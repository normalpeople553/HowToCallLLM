#!/usr/bin/env python3
"""只读核对全部示例的当前源码与真实 HTTP 证据，可重生成中文状态页。

不执行示例、不读取 .env、不访问网络。仅调用 runner 的清单、哈希、响应判定函数。
默认退出码不要求全部通过；--require-passed 将缺少有效证据视为退出码 1。
输入/清单错误或 --check 发现页面过期时退出码 2。
"""

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PAGE = Path("docs/示例实测状态.md")
EN_PAGE = Path("en/docs/example-status.md")
LABELS = {
    "passed": "通过", "failed": "执行未通过", "rate_limited": "限流",
    "missing_key": "缺少 Key", "missing_input": "缺少输入", "missing_runtime": "缺少运行环境",
    "timeout": "超时", "missing_evidence": "缺少报告", "stale_source": "仅有旧源码证据",
    "incomplete_evidence": "缺完整证据", "invalid_evidence": "证据无效",
}
LABELS_EN = {
    "passed": "Passed", "failed": "Execution failed", "rate_limited": "Rate-limited",
    "missing_key": "Missing key", "missing_input": "Missing input", "missing_runtime": "Missing runtime",
    "timeout": "Timed out", "missing_evidence": "No report", "stale_source": "Old-source evidence only",
    "incomplete_evidence": "Incomplete evidence", "invalid_evidence": "Invalid evidence",
}


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependencies(root):
    # 从工具所在仓库加载代码；--root 只替换待核查资料，便于无 API 的独立夹具测试。
    catalog = _module("release_example_catalog", ROOT / "skills/model-manual/scripts/example_catalog.py")
    runner = _module("release_example_runner", ROOT / "tests/run_example_files.py")
    runner.ROOT = root
    return catalog, runner


def _targets(root, entry, catalog):
    if entry["vendor"] != "shared":
        return {entry["model_id"]: catalog.API_HOSTS[entry["vendor"]]}
    result = {}
    references = root / "skills/model-manual/references"
    vendors = json.loads((references / "vendors.json").read_text(encoding="utf-8"))["vendors"]
    for vendor, config in vendors.items():
        card = json.loads((references / "models" / f"{config['default_model']}.json").read_text(encoding="utf-8"))
        if card["vendor"] != vendor or card["model_id"] != config["default_model"]:
            raise ValueError("shared_default_model_card_mismatch")
        result[card["model_id"]] = catalog.API_HOSTS[card["vendor"]]
    if not result:
        raise ValueError("shared_example_has_no_model_cards")
    return result


def _header_valid(report, catalog):
    privacy = report.get("privacy") if isinstance(report, dict) else None
    if not (
        isinstance(report, dict) and type(report.get("schema_version")) is int
        and report["schema_version"] in {1, 2} and report.get("kind") == "example_file_execution"
        and report.get("execution") == "real_vendor_api" and isinstance(privacy, dict)
        and catalog.PRIVACY_FLAGS <= privacy.keys() and all(value is False for value in privacy.values())
        and isinstance(report.get("results"), list) and all(isinstance(item, dict) for item in report["results"])
    ):
        return False
    # v2 的整份报告隐私约束也覆盖不属于当前示例清单的记录和空结果集。
    if report["schema_version"] == 2:
        try:
            catalog.evidence_metadata(report, {})
        except (ValueError, TypeError, KeyError, AttributeError):
            return False
    return True


def _attempt(root, entry, report, result, report_path, identity, targets, catalog, runner):
    """报告自称 passed 只是输入；必须以当前规则重新验证。"""
    attempt = {
        "report": report_path, "reported_status": result.get("status"),
        "evidence_id": None, "current_source": result.get("source_sha256") == identity,
        "strict_passed": False, "issue": None, "request_count": 0,
    }
    try:
        metadata = catalog.evidence_metadata(report, result)
        attempt["evidence_id"] = metadata.get("evidence_id")
        if result.get("vendor") != entry["vendor"] or result.get("model_id") != entry["model_id"]:
            raise ValueError("model_or_vendor_mismatch")
        if result.get("execution") != "real_vendor_api" or result.get("status") not in runner.LIVE_STATUSES:
            raise ValueError("invalid_result_identity")
        requests = result.get("requests", [])
        if not isinstance(requests, list) or not all(isinstance(item, dict) for item in requests):
            raise ValueError("invalid_request_list")
        attempt["request_count"] = len(requests)
        hosts = set().union(*targets.values())
        for request in requests:
            endpoint = urlparse(request.get("endpoint", ""))
            if (
                request.get("transport") != catalog.TRANSPORTS.get(Path(entry["path"]).suffix)
                or endpoint.scheme != "https" or endpoint.hostname not in hosts
                or endpoint.username is not None or endpoint.password is not None or endpoint.query or endpoint.fragment
            ):
                raise ValueError("invalid_http_identity")
            model = request.get("requested_model")
            if model in targets and endpoint.hostname not in targets[model]:
                raise ValueError("model_endpoint_mismatch")
            if runner.model_identity_conflicts(request):
                raise ValueError("served_model_identity_mismatch")
        scope = result.get("evidence_scope")
        if scope is not None and scope != (catalog.HTTP_SCOPE if requests else catalog.PROCESS_SCOPE):
            raise ValueError("invalid_evidence_scope")
        if result["status"] == "passed":
            if type(result.get("exit_code")) is not int or result["exit_code"] != 0:
                raise ValueError("invalid_passed_exit_code")
            # 旧进程模式和旧 gzip 旁观缺失不能升级为完整 HTTP 证据。
            if not requests or scope != catalog.HTTP_SCOPE:
                attempt["issue"] = "incomplete_http_metadata"
            elif runner.determine_status(entry, result, result["exit_code"]) != "passed":
                attempt["issue"] = "incomplete_completion_metadata"
            else:
                attempt["strict_passed"] = attempt["current_source"]
    except (ValueError, TypeError, KeyError, AttributeError):
        attempt["issue"] = "invalid_evidence"
    return attempt


def collect_release(root=ROOT):
    root = Path(root).resolve()
    catalog, runner = dependencies(root)
    catalog_valid, catalog_issues = True, []
    try:
        catalogs = catalog.load_catalogs(root)
        canonical = {row["path"]: row["verification"] for row in catalog.select_examples(catalogs)}
    except (ValueError, TypeError, KeyError, OSError, AttributeError):
        # 仍展示全部文件的证据状态，清单问题独立阻止发布，不伪造全绿。
        catalog_valid, canonical = False, {}
        catalog_issues.append({"code": "catalog_validation_failed"})
    entries = runner.discover()
    if not entries or len({entry["path"] for entry in entries}) != len(entries):
        raise ValueError("empty_or_duplicate_example_inventory")
    rows = {}
    for entry in entries:
        identity = runner.file_identity(entry["path"])
        if identity != catalog.file_identity(root, entry["path"]):
            raise ValueError("runner_catalog_source_identity_rules_differ")
        rows[entry["path"]] = {**entry, "identity": identity, "targets": _targets(root, entry, catalog), "attempts": []}
    report_issues = []
    for path in sorted((root / "verification/examples").glob("*.json")):
        relative = path.relative_to(root).as_posix()
        if not path.resolve().is_relative_to(root):
            report_issues.append({"report": relative, "code": "report_outside_repository"})
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            if not _header_valid(report, catalog):
                raise ValueError("invalid_file_execution_report")
        except (ValueError, TypeError, OSError):
            report_issues.append({"report": relative, "code": "invalid_file_execution_report"})
            continue
        counts = {}
        for result in report["results"]:
            source = result.get("path")
            if isinstance(source, str):
                counts[source] = counts.get(source, 0) + 1
        for result in report["results"]:
            source = result.get("path")
            if not isinstance(source, str) or source not in rows:
                continue
            row = rows[source]
            attempt = _attempt(root, row, report, result, relative, row["identity"], row["targets"], catalog, runner)
            if counts[source] != 1:
                attempt.update(strict_passed=False, issue="invalid_evidence")
            row["attempts"].append(attempt)
    final = []
    for row in rows.values():
        attempts = sorted(row["attempts"], key=lambda item: item["report"])
        valid = [item for item in attempts if item["strict_passed"]]
        current = [item for item in attempts if item["current_source"]]
        source_verification = canonical.get(row["path"], {})
        registered = [item for item in valid if item["report"] == source_verification.get("report")]
        selected = (registered or valid or current or attempts or [None])[0]
        if valid:
            status = "passed"
        elif not attempts:
            status = "missing_evidence"
        elif not current:
            status = "stale_source"
        elif selected["issue"] == "invalid_evidence":
            status = "invalid_evidence"
        elif selected["reported_status"] == "passed":
            status = "incomplete_evidence"
        else:
            status = selected["reported_status"]
        if source_verification.get("live") == "passed" and not any(item["strict_passed"] and item["report"] == source_verification.get("report") for item in attempts):
            catalog_issues.append({"path": row["path"], "code": "catalog_passed_reference_lacks_strict_evidence"})
        final.append({
            "path": row["path"], "vendor": row["vendor"], "model_id": row["model_id"],
            "status": status, "selected": selected, "attempts": attempts,
            "catalog_report": source_verification.get("report"),
        })
    counts = {state: sum(row["status"] == state for row in final) for state in sorted(LABELS)}
    ready = counts["passed"] == len(final) and catalog_valid and not catalog_issues and not report_issues
    return {"rows": final, "counts": counts, "total": len(final), "catalog_valid": catalog_valid,
            "catalog_issues": catalog_issues, "report_issues": report_issues, "ready": ready}


def _link(path, label="报告"):
    return f"[{label}](../{path})"


def render_page(release, language="zh"):
    if language == "en":
        return _render_page_en(release)
    if language != "zh":
        raise ValueError("Unknown page language")
    passed, total = release["counts"]["passed"], release["total"]
    lines = [
        "# 示例实测状态", "",
        "中文 | [English](../en/docs/example-status.md)", "",
        "> 本页由 `tests/check_example_release.py --write` 生成；核查过程不读取 `.env`、不执行示例、不发送 API 请求。", "",
        f"当前可执行示例 **{total}** 个；当前源码完整 HTTP 证据通过 **{passed}/{total}**。"
        f"发布门槛：**{'通过' if release['ready'] else '未满足'}**。", "",
        "这里核对逐文件报告，不把型号能力报告、旧源码通过、仅进程退出或缺失 finish/content 的旧记录算作完整实测。"
        "Python / TypeScript / cURL 的传输分别须为 `real_httpx` / `real_fetch` / `real_curl`；"
        "还核对源码与支持文件（含对应旁观辅助代码）哈希、厂商/型号、HTTP 成功、最终正常结束、非空正文、流结束标志及服务端业务状态。"
        "工具调用须最终回到正文，多厂商入口须各目标型号均完成。", "",
        "同一当前源码若有多次执行，优先选择示例清单登记且严格通过的报告；其余记录按报告路径稳定选择，不按测试时间排序。历史失败仍在下表保留。"
        "“缺完整证据”表示观测不足，不是断言接口不支持该能力。`passed` 也不代表所有参数组合或语义正确率均已验证。", "",
        "```bash", "python tests/check_example_release.py --write", "python tests/check_example_release.py --check",
        "python tests/check_example_release.py --check --require-passed", "```", "",
        "默认检查/生成允许状态页呈现未通过；`--require-passed` 在未全通过时退出 1。"
        "输入/清单错误或生成页不一致退出 2；不需要主机私密路径。", "",
        f"型号示例清单校验：{'通过' if release['catalog_valid'] and not release['catalog_issues'] else '未通过'}；"
        f"报告结构问题：{len(release['report_issues'])}。", "",
        "## 当前源码逐文件证据", "",
        "| 文件 | 厂商 / 型号 | 当前状态 | 有效证据 / 报告 | HTTP 请求数 |",
        "|---|---|---|---|---|",
    ]
    for row in release["rows"]:
        selected = row["selected"]
        evidence = _link(selected["report"]) if selected else "—"
        lines.append(f"| {_link(row['path'], row['path'])} | {row['vendor']} / `{row['model_id']}` | {LABELS.get(row['status'], '证据无效')} | {evidence} | {selected['request_count'] if selected else 0} |")
    missing = [row for row in release["rows"] if row["status"] != "passed"]
    lines.extend(["", "## 尚未取得有效通过证据", ""])
    if missing:
        lines.extend(f"- `{row['path']}`：{LABELS.get(row['status'], '证据无效')}。" for row in missing)
    else:
        lines.append("无；所有当前文件均有严格通过证据。")
    lines.extend(["", "## 历史失败、旧通过与观测不足", "", "历史报告不覆盖、不删除；旧记录不会因重试成功而消失。", "",
                  "| 文件 | 记录状态 | 源码身份 | 报告 |", "|---|---|---|---|"])
    history_count = 0
    for row in release["rows"]:
        for attempt in row["attempts"]:
            if attempt["strict_passed"]:
                continue
            history_count += 1
            state = LABELS.get(attempt["reported_status"], "证据无效")
            if attempt["reported_status"] == "passed":
                state = "旧记录自报通过（不计入当前）" if not attempt["current_source"] else "自报通过，但缺完整/有效证据"
                if attempt["issue"] in {"incomplete_http_metadata", "incomplete_completion_metadata"}:
                    state = "自报通过，但缺完整 HTTP 证据"
            if attempt["issue"] == "invalid_evidence":
                state = "记录身份/元数据无效"
            lines.append(f"| `{row['path']}` | {state} | {'当前' if attempt['current_source'] else '不匹配当前源码'} | {_link(attempt['report'])} |")
    if not history_count:
        lines.append("| — | 无历史失败或观测不足记录 | — | — |")
    if release["catalog_issues"] or release["report_issues"]:
        lines.extend(["", "## 输入与清单问题", ""])
        for issue in release["catalog_issues"]:
            lines.append(f"- `{issue.get('path', 'models/*/*/examples/sources.json')}`：`{issue['code']}`。")
        for issue in release["report_issues"]:
            lines.append(f"- {_link(issue['report'])}：`{issue['code']}`。")
    lines.append("")
    return "\n".join(lines)


def _render_page_en(release):
    def link(path, label="Report"):
        return f"[{label}](../../{path})"

    passed, total = release["counts"]["passed"], release["total"]
    lines = [
        "# Example execution status", "",
        "[中文](../../docs/示例实测状态.md) | English", "",
        "> Generated by `tests/check_example_release.py --write`. Checking does not read `.env`, execute examples, or send API requests.", "",
        f"Current executable examples: **{total}**. Complete HTTP evidence for current source: **{passed}/{total}**. "
        f"Release gate: **{'passed' if release['ready'] else 'not satisfied'}**.", "",
        "This page checks file-execution reports. Model-capability reports, old-source passes, process exit alone, and old records without finish/content observations do not count as complete evidence. "
        "Python / TypeScript / cURL require `real_httpx` / `real_fetch` / `real_curl`, respectively. "
        "Checks cover source and support-file hashes (including transport observers), vendor/model identity, HTTP success, normal final completion, nonempty text, stream termination, and server business status. "
        "Tool workflows must return to final text; the multi-vendor entry point must complete for every target model.", "",
        "For repeated executions of identical current source, prefer the catalog-registered report when it strictly passes. Otherwise select deterministically by report path, not by test time. Historical failures remain below. "
        "Incomplete evidence means insufficient observation, not a conclusion that the API lacks the capability. "
        "A pass does not validate every parameter combination or semantic accuracy. Read the [English model manuals and parameter notes](../../models/README.en.md).", "",
        "```bash", "python tests/check_example_release.py --write", "python tests/check_example_release.py --check",
        "python tests/check_example_release.py --check --require-passed", "```", "",
        "Default generation/checking may succeed while the page honestly reports incomplete execution. `--require-passed` exits 1 unless the release gate is satisfied. "
        "Invalid inputs/catalogs or a stale generated page exit 2. No host-private paths are required.", "",
        f"Model example catalogs: {'valid' if release['catalog_valid'] and not release['catalog_issues'] else 'invalid'}. "
        f"Report-structure issues: {len(release['report_issues'])}.", "",
        "Related evidence: [official-documentation example index](example-index.md) and [historical workflow status](verification-status.md).", "",
        "## Current-source evidence by file", "",
        "| File | Vendor / model | Current status | Effective evidence / report | HTTP requests |",
        "|---|---|---|---|---|",
    ]
    for row in release["rows"]:
        selected = row["selected"]
        evidence = link(selected["report"]) if selected else "—"
        lines.append(f"| {link(row['path'], row['path'])} | {row['vendor']} / `{row['model_id']}` | {LABELS_EN.get(row['status'], 'Invalid evidence')} | {evidence} | {selected['request_count'] if selected else 0} |")
    missing = [row for row in release["rows"] if row["status"] != "passed"]
    lines.extend(["", "## Files without an effective pass", ""])
    if missing:
        lines.extend(f"- `{row['path']}`: {LABELS_EN.get(row['status'], 'Invalid evidence')}." for row in missing)
    else:
        lines.append("None. Every current file has strict passing evidence.")
    lines.extend(["", "## Historical failures, old passes, and incomplete observations", "",
                  "Historical reports are neither overwritten nor deleted; a successful retry does not erase earlier records.", "",
                  "| File | Recorded outcome | Source identity | Report |", "|---|---|---|---|"])
    history_count = 0
    for row in release["rows"]:
        for attempt in row["attempts"]:
            if attempt["strict_passed"]:
                continue
            history_count += 1
            state = LABELS_EN.get(attempt["reported_status"], "Invalid evidence")
            if attempt["reported_status"] == "passed":
                state = "Old record reports a pass (not current evidence)" if not attempt["current_source"] else "Reports a pass, but complete/valid evidence is missing"
                if attempt["issue"] in {"incomplete_http_metadata", "incomplete_completion_metadata"}:
                    state = "Reports a pass, but complete HTTP evidence is missing"
            if attempt["issue"] == "invalid_evidence":
                state = "Invalid record identity/metadata"
            source = "Current" if attempt["current_source"] else "Does not match current source"
            lines.append(f"| `{row['path']}` | {state} | {source} | {link(attempt['report'])} |")
    if not history_count:
        lines.append("| — | No historical failure or incomplete observation | — | — |")
    if release["catalog_issues"] or release["report_issues"]:
        lines.extend(["", "## Input and catalog issues", ""])
        for issue in release["catalog_issues"]:
            lines.append(f"- `{issue.get('path', 'models/*/*/examples/sources.json')}`: `{issue['code']}`.")
        for issue in release["report_issues"]:
            lines.append(f"- {link(issue['report'])}: `{issue['code']}`.")
    lines.append("")
    return "\n".join(lines)


def page_outputs(release):
    return {PAGE: render_page(release), EN_PAGE: render_page(release, language="en")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="待检查仓库根目录，默认由脚本位置推导")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="检查已生成状态页是否一致")
    action.add_argument("--write", action="store_true", help="生成状态页")
    parser.add_argument("--require-passed", action="store_true", help="所有当前示例均有完整真实 HTTP 通过证据时才成功")
    args = parser.parse_args(argv)
    try:
        release = collect_release(args.root)
        for relative, content in page_outputs(release).items():
            target = args.root / relative
            if args.write:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            if args.check and (not target.is_file() or target.read_text(encoding="utf-8") != content):
                print(f"示例状态页过期：{relative.as_posix()}，请运行 --write", file=sys.stderr)
                return 2
        print(f"当前示例 {release['total']}；完整 HTTP 通过 {release['counts']['passed']}；发布门槛 {'通过' if release['ready'] else '未满足'}")
        for row in release["rows"]:
            if row["status"] != "passed":
                print(f"{row['path']}: {row['status']}")
        if not release["catalog_valid"] or release["catalog_issues"] or release["report_issues"]:
            print("清单或报告校验存在问题，详见生成页。", file=sys.stderr)
            return 2
        return 1 if args.require_passed and not release["ready"] else 0
    except (ValueError, TypeError, KeyError, OSError, AttributeError):
        # 不打印可能来自不可信输入的原始异常/字段值。
        print("无法建立有效示例清单或源码身份，请检查仓库内资料。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
