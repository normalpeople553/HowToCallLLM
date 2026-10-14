#!/usr/bin/env python3
"""公开调用代码目录生成器，以及显式启用的本地私有证据检查。

不执行示例、不读取 .env、不访问网络。仅调用 runner 的清单、哈希、响应判定函数。
默认 --write/--check 不读取本地证据；--require-passed 单独启用严格私有检查。
缺少有效私有证据时退出码 1；输入错误或公开目录页过期时退出码 2。
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
PRIVATE_EVIDENCE = Path(".local/evidence")
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
    """仅从本地私有镜像检查真实证据；公开页面不调用此函数。"""
    root = Path(root).resolve()
    catalog, runner = dependencies(root)
    catalog_valid, catalog_issues = True, []
    try:
        catalogs = catalog.load_catalogs(root, private_evidence=True)
        canonical = {
            (Path(item["catalog_path"]).parent / entry["file"]).as_posix(): entry["verification"]
            for item in catalogs for entry in item["examples"]
        }
    except (ValueError, TypeError, KeyError, OSError, AttributeError):
        # 仍核对全部文件，私有绑定或清单问题独立阻止通过，不伪造全绿。
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
    for path in sorted((root / PRIVATE_EVIDENCE / "verification/examples").glob("*.json")):
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


def collect_code_directory(root=ROOT):
    """Public inventory only: no evidence, file hashes, credentials, or requests."""
    root = Path(root).resolve()
    catalog, runner = dependencies(root)
    catalogs = catalog.load_catalogs(root)
    maintained = {row["path"]: row for row in catalog.select_examples(catalogs)}
    entries = runner.discover()
    if not entries or len({entry["path"] for entry in entries}) != len(entries):
        raise ValueError("empty_or_duplicate_example_inventory")
    rows = []
    for entry in entries:
        declared = maintained.get(entry["path"])
        command = declared["run_command"] if declared else f"python {entry['path']}"
        rows.append({
            "path": entry["path"], "vendor": entry["vendor"], "model_id": entry["model_id"],
            "capability": entry["capability"], "run_command": command,
        })
    return {"rows": rows}


def render_page(directory, language="zh"):
    if language not in {"zh", "en"}:
        raise ValueError("Unknown page language")
    english = language == "en"
    prefix = "../../" if english else "../"
    lines = [
        "# Calling code directory" if english else "# 调用代码目录", "",
        "[中文](../../docs/示例实测状态.md) | English" if english else "中文 | [English](../en/docs/example-status.md)", "",
        "> Generated by `tests/check_example_release.py --write`. This public directory reads registered source metadata only; it does not read local execution records, keys, or send API requests."
        if english else
        "> 本页由 `tests/check_example_release.py --write` 生成；公开目录仅读取已登记代码资料，不读取本地执行记录、Key，也不发送 API 请求。", "",
        "Use the files to understand calling patterns and review Agent-written code. The directory does not publish execution records or assert that a call currently works."
        if english else
        "这些文件用于学习调用方式和检查 Agent 写出的代码。目录不公开执行记录，也不声称当前调用一定成功。", "",
        "[Model manuals and parameters](../../models/README.en.md) · [Full code reading guide](../../human/examples/README.en.md) · [Official-documentation example index](example-index.md)"
        if english else
        "[型号说明书与参数](../models/README.md) · [完整代码阅读](../human/examples/README.md) · [官方功能示例索引](官方示例索引.md)", "",
        "Run from the repository root after installing the documented dependencies and setting the required environment variables. Running a file may send a billable request; only use authorized keys and input material."
        if english else
        "在仓库根目录安装说明中的依赖、配置所需环境变量后运行。执行文件可能发送计费请求，请仅使用获准的 Key 和输入素材。", "",
        "```bash", "python tests/check_example_release.py --write", "python tests/check_example_release.py --check", "```", "",
        "| File | Vendor / model | Purpose (capability key) | Run command |"
        if english else "| 文件 | 厂商 / 型号 | 用途（能力词） | 运行命令 |",
        "|---|---|---|---|",
    ]
    for row in directory["rows"]:
        command = row["run_command"].replace("|", "&#124;").replace("\n", " ")
        lines.append(
            f"| [{row['path']}]({prefix}{row['path']}) | {row['vendor']} / `{row['model_id']}` | "
            f"`{row['capability']}` | `{command}` |"
        )
    lines.append("")
    return "\n".join(lines)


def page_outputs(directory):
    return {PAGE: render_page(directory), EN_PAGE: render_page(directory, language="en")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="待检查仓库根目录，默认由脚本位置推导")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="检查公开调用代码目录是否一致")
    action.add_argument("--write", action="store_true", help="生成公开调用代码目录")
    parser.add_argument("--require-passed", action="store_true", help="额外严格检查本地私有证据，所有当前示例真实 HTTP 通过时才成功")
    args = parser.parse_args(argv)
    try:
        directory = collect_code_directory(args.root)
        for relative, content in page_outputs(directory).items():
            target = args.root / relative
            if args.write:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            if args.check and (not target.is_file() or target.read_text(encoding="utf-8") != content):
                print(f"调用代码目录过期：{relative.as_posix()}，请运行 --write", file=sys.stderr)
                return 2
        print(f"公开调用代码目录：{len(directory['rows'])} 个文件。")
        if not args.require_passed:
            return 0
        release = collect_release(args.root)
        print(f"当前示例 {release['total']}；完整 HTTP 通过 {release['counts']['passed']}；发布门槛 {'通过' if release['ready'] else '未满足'}")
        for row in release["rows"]:
            if row["status"] != "passed":
                print(f"{row['path']}: {row['status']}")
        if not release["catalog_valid"] or release["catalog_issues"] or release["report_issues"]:
            print("本地私有绑定、清单或报告校验存在问题。", file=sys.stderr)
            return 2
        return 0 if release["ready"] else 1
    except (ValueError, TypeError, KeyError, OSError, AttributeError):
        # 不打印可能来自不可信输入的原始异常/字段值。
        print("无法建立有效示例清单或源码身份，请检查仓库内资料。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
