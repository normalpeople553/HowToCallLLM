#!/usr/bin/env python3
"""离线检索各型号官方改写示例，并生成唯一的人类阅读索引。"""

import argparse
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[3]
INDEX = Path("docs/官方示例索引.md")
HOSTS = {
    "deepseek": {"api-docs.deepseek.com"},
    "kimi": {"platform.kimi.com"},
    "qwen": {"help.aliyun.com"},
    "zhipu": {"docs.bigmodel.cn"},
    "doubao": {"docs.volcengine.com", "www.volcengine.com"},
    "minimax": {"platform.minimax.io", "platform.minimax.cn", "platform.minimaxi.com"},
}
API_HOSTS = {
    "deepseek": {"api.deepseek.com"}, "kimi": {"api.moonshot.cn"},
    "qwen": {"dashscope.aliyuncs.com"}, "zhipu": {"open.bigmodel.cn"},
    "doubao": {"ark.cn-beijing.volces.com"}, "minimax": {"api.minimax.cn"},
}
OFFLINE_STATES = {"not_run", "compile_checked", "mock_tested"}
LIVE_STATES = {"not_run", "passed", "failed", "rate_limited", "missing_key", "missing_input", "missing_runtime", "timeout"}
PRIVACY_FLAGS = {"api_key_saved", "response_content_saved", "reasoning_content_saved", "raw_error_saved", "request_messages_saved"}
HTTP_SCOPE = "original_file_and_real_http_metadata"
PROCESS_SCOPE = "original_file_process_exit_and_its_response_checks"
TRANSPORTS = {".py": "real_httpx", ".ts": "real_fetch", ".sh": "real_curl"}
TRACE_HELPERS = {".ts": "tests/live_fetch.mjs", ".sh": "tests/live_curl.py"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sources(sources, vendor):
    _require(isinstance(sources, list) and bool(sources), "每个示例/未集成项需要官方来源")
    for source in sources:
        parsed = urlparse(source.get("url", ""))
        _require(parsed.scheme == "https" and parsed.hostname in HOSTS[vendor], "来源必须是对应厂商官方 HTTPS 页面")
        _require(bool(source.get("title")), "来源缺少标题")


def file_identity(root, path):
    """与 tests/run_example_files.py 的规则一致；不加载执行器或读取凭据。"""
    root, path = Path(root), Path(root) / path
    files = [path]
    if path.parent != root / "examples":
        files += sorted(path.parent.glob("_*.py"))
    if path.suffix in TRACE_HELPERS:
        helper = root / TRACE_HELPERS[path.suffix]
        if helper.is_file():
            files.append(helper)
    if path.name == "02_one_for_all.py":
        files += sorted((root / "skills/model-manual/references/models").glob("*.json"))
        files += [root / "skills/model-manual/references/vendors.json"]
    return {item.relative_to(root).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest() for item in files}


def _report_path(root, value):
    _require(isinstance(value, str) and bool(value), "线上状态必须提供仓库相对 report 路径")
    path = Path(value)
    _require(not path.is_absolute() and "\\" not in value and all(part not in {"", ".", ".."} for part in value.split("/")), "report 必须是无路径跳转的仓库相对路径")
    target = root / path
    _require(target.resolve().is_relative_to(root.resolve()), "report 不能指向仓库之外")
    _require(target.is_file(), f"文件级线上报告不存在：{value}")
    return target


def _completion_succeeded(request):
    """与 runner.completion_succeeded 保持同一门槛；只读安全元数据。"""
    status, chars = request.get("http_status"), request.get("content_chars")
    if type(status) is not int or not 200 <= status < 300:
        return False
    if request.get("business_status", 0) != 0 or request.get("telemetry_overflow") or request.get("telemetry_error"):
        return False
    parameters = request.get("parameters", {})
    if not isinstance(parameters, dict):
        return False
    if parameters.get("stream") is True and not (request.get("sse_done") is True or request.get("transport_eof") is True):
        return False
    if request.get("has_tool_calls"):
        return False
    normal = request.get("response_status") == "completed" or request.get("finish_reasons", []) == ["stop"]
    return normal and type(chars) is int and chars > 0


def _verify_live(root, source_path, vendor, model, verification, reports):
    """只验证已保存的文件级证据；此过程从不执行示例或访问网络。"""
    live = verification.get("live")
    _require(isinstance(live, str) and live in LIVE_STATES, "未知文件级线上验证状态")
    _require(isinstance(verification.get("note"), str) and bool(verification["note"].strip()), "文件级验证缺少范围说明")
    if live == "not_run":
        _require(not verification.get("report"), "not_run 不能引用线上验证报告")
        return
    report_path = _report_path(root, verification.get("report"))
    if report_path not in reports:
        reports[report_path] = json.loads(report_path.read_text(encoding="utf-8"))
    report = reports[report_path]
    _require(isinstance(report, dict) and type(report.get("schema_version")) is int and report["schema_version"] == 1, "文件级线上报告 schema_version 无效")
    _require(report.get("kind") == "example_file_execution" and report.get("execution") == "real_vendor_api", "必须使用真实逐文件执行报告，不能复用型号能力报告")
    privacy = report.get("privacy")
    _require(isinstance(privacy, dict) and PRIVACY_FLAGS <= privacy.keys() and all(value is False for value in privacy.values()), "真实报告必须声明未保存密钥、正文、思考、原始错误和请求消息")
    results = report.get("results")
    _require(isinstance(results, list) and all(isinstance(item, dict) for item in results), "文件级线上报告缺少 results 列表")
    matching = [item for item in results if item.get("path") == source_path]
    _require(len(matching) == 1, f"报告必须唯一记录当前示例：{source_path}")
    result = matching[0]
    _require(result.get("vendor") == vendor and result.get("model_id") == model, "报告厂商/型号与示例不一致")
    _require(result.get("execution") == "real_vendor_api" and result.get("status") == live, "报告执行方式/状态与清单不一致")
    _require(result.get("source_sha256") == file_identity(root, source_path), "示例或支持文件已变更，不能沿用旧文件级报告")
    tested_at = result.get("tested_at")
    _require(isinstance(tested_at, str), "文件级报告缺少 tested_at")
    recorded_time = datetime.fromisoformat(tested_at)
    _require(recorded_time.tzinfo is not None, "文件级报告时间必须包含时区")
    requests = result.get("requests", [])
    _require(isinstance(requests, list) and all(isinstance(item, dict) for item in requests), "文件级请求记录必须为列表")
    suffix = Path(source_path).suffix
    for request in requests:
        _require(isinstance(request.get("endpoint"), str), "HTTP 记录缺少有效 endpoint")
        endpoint = urlparse(request["endpoint"])
        _require(request.get("transport") == TRANSPORTS.get(suffix) and endpoint.scheme == "https" and endpoint.hostname in API_HOSTS[vendor] and endpoint.username is None and endpoint.password is None and not endpoint.query and not endpoint.fragment, "HTTP 记录必须使用与文件扩展名对应的真实传输、对应厂商 HTTPS 地址且不能含凭据/查询串")
    scope = result.get("evidence_scope")
    if scope is not None:
        _require(scope == (HTTP_SCOPE if requests else PROCESS_SCOPE), "报告证据范围与 HTTP 记录不一致")
    if live == "passed":
        _require(type(result.get("exit_code")) is int and result["exit_code"] == 0, "passed 必须有 exit_code=0")
        _require(bool(requests) and scope == HTTP_SCOPE, "所有语言的 passed 必须有真实 HTTP 元数据，不能只凭进程退出")
        target_requests = [request for request in requests if request.get("requested_model") == model]
        _require(bool(target_requests) and _completion_succeeded(target_requests[-1]), "passed 必须有当前型号最后一次请求的正常结束、非空最终正文及完整传输/业务状态证据")
    # 日期与范围来自通过身份/哈希校验的报告，而不是清单的自填声明。
    verification["tested_at"] = tested_at
    verification["evidence_scope"] = scope


def load_catalogs(root=ROOT):
    root = Path(root)
    catalogs, reports = [], {}
    for path in sorted((root / "models").glob("*/*/examples/sources.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        vendor, model = path.parts[-4], path.parts[-3]
        _require(data.get("schema_version") == 1, f"{path}: 不支持 schema_version")
        _require(data.get("vendor") == vendor and vendor in HOSTS, f"{path}: 厂商/路径不一致")
        _require(data.get("model_id") == model, f"{path}: 型号/路径不一致")
        date.fromisoformat(data["checked_at"])
        entries = data.get("examples", [])
        _require(isinstance(entries, list) and bool(entries), f"{path}: 缺少示例")
        ids, files = set(), set()
        for entry in entries:
            filename = entry.get("file", "")
            _require(Path(filename).name == filename and filename not in {"", ".", ".."}, "示例必须为当前目录中的文件")
            _require((path.parent / filename).is_file(), f"示例不存在：{filename}")
            _require(filename not in files and entry.get("id") not in ids, "示例文件/ID 重复")
            files.add(filename)
            ids.add(entry.get("id"))
            for key in ("id", "title", "capability", "run_command"):
                _require(isinstance(entry.get(key), str) and bool(entry[key].strip()), f"示例缺少 {key}")
            _require(entry.get("origin") == "adapted_from_official", "需要标明官方改写来源")
            _sources(entry.get("sources"), vendor)
            for key in ("required_env", "adaptations"):
                _require(isinstance(entry.get(key), list) and bool(entry[key]) and all(isinstance(v, str) and v for v in entry[key]), f"示例缺少 {key}")
            verification = entry.get("verification", {})
            _require(isinstance(verification, dict), "示例 verification 必须为对象")
            _require(verification.get("offline") in OFFLINE_STATES, "未知离线验证状态")
            _verify_live(root, (path.parent / filename).relative_to(root).as_posix(), vendor, model, verification, reports)
        runnable = {p.name for p in path.parent.iterdir() if p.suffix in {".py", ".ts", ".sh"} and not p.name.startswith("_")}
        _require(files == runnable, f"{path}: 清单与可运行文件不一致：{sorted(files ^ runnable)}")
        for item in data.get("not_integrated", []):
            _require(bool(item.get("capability")) and bool(item.get("reason")), "未集成项缺少能力/原因")
            _sources(item.get("sources"), vendor)
        data["catalog_path"] = path.relative_to(root).as_posix()
        parameters = path.parent.parent / "parameters.md"
        if parameters.is_file():
            data["parameters_path"] = parameters.relative_to(root).as_posix()
        catalogs.append(data)
    _require(bool(catalogs), "未找到示例清单")
    return catalogs


def select_examples(catalogs, vendor=None, model=None, capability=None):
    result = []
    for catalog in catalogs:
        if vendor and catalog["vendor"] != vendor or model and catalog["model_id"] != model:
            continue
        for entry in catalog["examples"]:
            if capability and entry["capability"] != capability:
                continue
            result.append({
                "vendor": catalog["vendor"], "model_id": catalog["model_id"],
                "checked_at": catalog["checked_at"], "catalog_path": catalog["catalog_path"],
                **({"parameters_path": catalog["parameters_path"]} if "parameters_path" in catalog else {}),
                "path": str(Path(catalog["catalog_path"]).parent / entry["file"]).replace("\\", "/"),
                **entry,
            })
    return result


def selection_diagnostics(catalogs, vendor=None, model=None, capability=None):
    """无命中时给出当前型号的可用词与边界；不把缺示例写成不支持。"""
    result = []
    for catalog in catalogs:
        if vendor and catalog["vendor"] != vendor or model and catalog["model_id"] != model:
            continue
        result.append({
            "vendor": catalog["vendor"], "model_id": catalog["model_id"],
            "catalog_path": catalog["catalog_path"],
            "available_capabilities": sorted({entry["capability"] for entry in catalog["examples"]}),
            "not_integrated": [item for item in catalog.get("not_integrated", []) if not capability or item["capability"] == capability],
        })
    return result


def render_index(catalogs):
    lines = [
        "# 官方功能示例索引", "",
        "> 本页由各型号的 `examples/sources.json` 生成；修改清单后运行同步命令，不手改本页。", "",
        "这里的代码是**基于官方文档改写的项目示例**，不是厂商发布的 SDK，也不是官方示例原文镜像。"
        "每项清单记录官方链接、准确型号、所需环境变量、运行命令、改写说明和文件级验证范围。", "",
        "## 如何使用", "",
        "在仓库根目录安装 [requirements-lock.txt](../requirements-lock.txt)，设置对应 Key 和输入变量后运行文件。"
        "Python 示例共用锁定环境；TypeScript 另需 Node.js、`openai` 与 `tsx`，cURL 例子另需 curl/bash/Python。"
        "图片或视频会发送到对应厂商，请仅使用获准上传的内容。", "",
        "按功能给 Agent 查询（只读取清单，不发送请求）：", "",
        "```bash",
        "python skills/model-manual/scripts/example_catalog.py --vendor deepseek --capability vision",
        "python skills/model-manual/scripts/example_catalog.py --model kimi-k2.6 --capability video_input",
        "python skills/model-manual/scripts/example_catalog.py --write-index",
        "python skills/model-manual/scripts/example_catalog.py --check",
        "```", "",
        "输出 JSON 含完整命令与改写说明；能力词不确定时先仅传 `--model` 列出该型号的示例。"
        "找不到型号或功能时退出码为 2，已收录型号同时给出候选能力和匹配的未集成说明，不回退到别的型号。"
        "下表中环境变量的 `|` 表示二选一（Key 始终必需），可选变量见文件说明。", "",
        "## 验证标记", "",
        "- `mock_tested`：用假 SDK 执行代码检查请求/消息/失败分支，不代表服务端接受或识别质量。",
        "- `compile_checked`：仅语法编译检查；`not_run`：该类检查未执行。",
        "- `live=passed`：当前文件及支持文件哈希匹配真实逐文件报告，进程退出及示例自身响应检查通过。Python / TypeScript / cURL 分别须有 `real_httpx` / `real_fetch` / `real_curl` HTTP 证据；当前型号最后一次请求须成功、正常结束、最终正文非空、无未处理工具调用和业务/旁观错误，流式请求还须有 `[DONE]` 或真实传输结束标志。旧进程模式报告保留，但不能作为清单的 `passed` 证据。",
        "- `passed` 不等于所有参数组合都受支持，不代表语义正确率、图片/视频识别质量或未来仍可调用；参数含义请先读对应型号的参数页。",
        "- `failed` / `rate_limited` / `timeout` 是未通过；`missing_key` / `missing_input` / `missing_runtime` 是缺少运行条件，不能当作真实调用成功。",
        "- `live=not_run` 表示没有该文件的线上执行证据。非 `not_run` 项须链接真实逐文件报告，并核对型号、状态、源码和支持文件哈希；日期取自报告。型号历史报告见[验证状态](验证状态.md)，不能继承为示例文件的实测证据。", "",
    ]
    for catalog in catalogs:
        directory = Path(catalog["catalog_path"]).parent.as_posix()
        lines.extend([
            f"## {catalog['vendor']} · `{catalog['model_id']}`", "",
            f"资料核对：{catalog['checked_at']}；[来源、命令及改写清单](../{catalog['catalog_path']})。", "",
        ])
        if "parameters_path" in catalog:
            lines.extend([f"调用前必读：[逐参数说明与文件映射](../{catalog['parameters_path']})。", ""])
        lines.extend([
            "| 功能 / 文件 | 能力检索词 | 必需环境变量 | 官方来源 | 离线 / 逐文件线上 | 时间 / 报告 / 证据 |",
            "|---|---|---|---|---|---|",
        ])
        for entry in catalog["examples"]:
            sources = " · ".join(f"[{s['title'].replace('|', '/')}]({s['url']})" for s in entry["sources"])
            env = "<br>".join(v.replace("|", "或") for v in entry["required_env"])
            check = entry["verification"]
            evidence = "—"
            if check["live"] != "not_run":
                scope = {HTTP_SCOPE: "HTTP 元数据", PROCESS_SCOPE: "进程及自身检查"}.get(check.get("evidence_scope"), "未取得执行证据")
                evidence = f"{check['tested_at']}<br>[报告](../{check['report']})<br>{scope}"
            lines.append(f"| [{entry['title']}](../{directory}/{entry['file']}) | `{entry['capability']}` | {env} | {sources} | {check['offline']} / {check['live']} | {evidence} |")
        if catalog.get("not_integrated"):
            lines.extend(["", "尚未集成的官方功能或型号边界（不把“没有示例”直接解释为不支持）：", ""])
            for item in catalog["not_integrated"]:
                sources = " · ".join(f"[{s['title']}]({s['url']})" for s in item["sources"])
                lines.append(f"- `{item['capability']}`：{item['reason']} {sources}")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor", choices=sorted(HOSTS))
    parser.add_argument("--model")
    parser.add_argument("--capability", help="精确能力词；不确定时先仅用 --model 列出该型号示例")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write-index", action="store_true", help="从清单生成中文 Markdown 索引")
    action.add_argument("--check", action="store_true", help="检查清单与生成索引是否一致")
    args = parser.parse_args(argv)
    if (args.write_index or args.check) and (args.vendor or args.model or args.capability):
        parser.error("索引生成/检查不能使用筛选参数")
    try:
        catalogs = load_catalogs()
        if args.write_index or args.check:
            content = render_index(catalogs)
            if args.write_index:
                (ROOT / INDEX).write_text(content, encoding="utf-8")
                print(INDEX.as_posix())
            elif not (ROOT / INDEX).exists() or (ROOT / INDEX).read_text(encoding="utf-8") != content:
                raise ValueError("索引过期，请运行 --write-index")
            else:
                print("示例清单与索引一致")
        else:
            result = select_examples(catalogs, args.vendor, args.model, args.capability)
            if not result:
                diagnostics = selection_diagnostics(catalogs, args.vendor, args.model, args.capability)
                if diagnostics:
                    print(json.dumps({"selection_hints": diagnostics}, ensure_ascii=False, indent=2), file=sys.stderr)
                raise ValueError("未收录此型号/功能示例；请核对官方资料，不能套用别的型号")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"示例清单错误：{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
