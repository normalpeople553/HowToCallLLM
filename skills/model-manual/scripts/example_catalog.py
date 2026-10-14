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
EN_INDEX = Path("en/docs/example-index.md")
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
# Human translations only; evidence, statuses, and source URLs always come from the manifests.
GAP_TRANSLATIONS = {
    "deepseek:anthropic_api": ("9fdfd08558ba05252de04736ee5f31c15e56690202d5d7e12cb9c38f87396843", "An official compatible endpoint exists. This batch adds neither the anthropic dependency nor an example; that is not a claim of unsupported functionality."),
    "deepseek:context_caching": ("56982493939e92c5263989b7091d93e24e813814af0053d03b4abcb22563799e", "No dedicated cache-observation example was added in this batch. The official cache rules remain authoritative."),
    "doubao:explicit_cache": ("c85c85568c368f88a5c398f187afea0643a11e50460640340bf4c599b0d7da3a", "The official matrix lists Responses API prefix and session caching for this model. This batch uses Chat API and only observes implicit caching without creating resources; explicit cache creation, reuse, expiration, and storage billing are not covered."),
    "doubao:files_video_preprocessing": ("719e2701c6b951c8d05a92a852a786cd2f789474fdbde011e0b1e1d9b75b151d", "The current Files video tutorial uses version 260915 and model-specific preprocessing settings. Their applicability to 260628 has not been checked individually, so the example only uses video_url.url without an upload."),
    "doubao:video_embedded_audio": ("3b1c7a0aac1901e8ab3c10e0fb368166eed6226ae772d8a69cda09062d3eaa08", "This batch covers visual video understanding only. Embedded-audio limits and parameters for this historical model have not been independently verified; a visual-input pass is not an audio-understanding pass."),
    "doubao:responses_builtin_tools": ("dabb27e13d1fceebf3f7280d6250fe17765162307e865ad225eb7cd8862ff8db", "The official matrix lists Responses tools such as web access and MCP for this model. These complete tool examples use local simulated functions through Chat API and do not mix tool schemas from different APIs."),
    "kimi:remote_image_url": ("e845925736654d4657fd7fce5ab1a69178e751a1c69f8a1b1a0a2ec9370e2bfa", "The current vision and Chat API documentation lists base64 or ms:// file references and explicitly excludes remote image URLs. Example 06 no longer forwards those URLs directly."),
    "kimi:complex_json_schema_and_partial_mode": ("d633072f6e1cdcdc2a6be4f39b84020a9c3ac4b02b2d1c4fe720504ad9e665fd", "The K2.6 documentation warns that complex $ref/oneOf and Partial Mode combinations may be unstable. This batch includes simple schemas plus application validation, not complex combinations."),
    "kimi:builtin_web_search": ("c01372589823f0e234249c76a1ed26d49f7b5f50a70549038dc6a986810d2b49", "The K2.6 page says web-search documentation is being upgraded and discourages current use. Built-in $web_search also has thinking-mode compatibility restrictions, so it is not integrated here."),
    "kimi:uploaded_video_file_reference": ("017640f2f88d96a02dfe2c4ef47131fd75437ac76d6c377025cebb36e982b3db", "Official vision documentation describes uploads and ms:// references. This batch only includes local short MP4/base64 input; file lifecycle and upload-polling workflows are not integrated."),
    "minimax:json_object": ("6e1c7c9309efa8364a88bf334b2732b6aea01a4a7492e104217e74d5bede427c", "The hosted native API limits response_format to MiniMax-Text-01; a hosted M2.7 JSON-guarantee parameter is unconfirmed in the OpenAI-compatible API. Self-hosted documentation or a JSON prompt is not treated as hosted JSON Mode support; no 04_json_output.py is created."),
    "minimax:json_schema": ("b937aa02e8fe1cd2b8fc8eafe88fef4542e705c85537e00b08822a98267415e7", "Hosted MiniMax-M2.7 response_format/json_schema support is unconfirmed. Native documentation names MiniMax-Text-01 only; support is not inherited from other models or self-hosted APIs."),
    "minimax:thinking_off": ("697f7dc8b3e7f6b42eecf84fa2cb7db1a37cb984051267cc4c8f154dc55947de", "Official documentation says M2.x thinking cannot be disabled: disabled is accepted but ignored. reasoning_split only changes output formatting."),
    "minimax:reasoning_effort_control": ("a775c5cf052549ebfa6129762ff02f55bd739f2a6e76362572eeffc2bd72be6e", "Current documentation only declares reasoning_effort effective for MiniMax-M3.1-Flash-Preview. M2.7 examples do not add an ineffective thinking-effort control."),
    "minimax:vision": ("157e53c0796c85be9ec58d93c629d3e6027040d4146c686707602b646125a2b5", "Current official OpenAI-compatible image input covers MiniMax-M3.1-Flash-Preview and MiniMax-M3. Image input for M2.7 is unconfirmed here; examples from other models are not reused."),
    "minimax:video_input": ("af0036c5db32f52324d65fb8d044e9cc1132ab1d80d7f63af3c862c76fa48bab", "Current official multimodal-input instructions target the M3 family. This batch does not transplant its video_url protocol to M2.7."),
    "minimax:legacy_minimaxi_domain_verification": ("78c3a83093dbf195795f1f408f3a561e1eac1437501c9b4f80e6d53f8449c24f", "Current mainland documentation lists api.minimax.cn and international documentation lists api.minimax.io. The old api.minimaxi.com domain was not live-tested in this batch; no alias-compatibility promise is made."),
    "minimax:subscription_alias_identity_after_migration": ("a173fcf9ddf977ac3150ee1217044f9e6d277f36f51cc27c6c81d033b02e88fa", "The official notice stops new-user M2.7 access on 2026-10-19 and retires its pay-as-you-go API on 2026-11-18. M Plan/Token Plan requests using old names reroute to M3.1 Flash Preview from 2026-10-19. These examples retain the exact model name; rerouted subscription responses are not original-M2.7 test evidence."),
    "qwen:vision": ("fca87e8f4ce01c01f8eefa4626be2454b18a318cd97820eb597ff7c25ee83e8e", "The official Function Calling matrix lists Qwen-Flash as a text-generation model. Its image input was not verified here; Qwen-VL or newer multimodal examples must not be transplanted."),
    "qwen:preserved_thinking": ("70d7e93456d909047468302b2d25077d0a21f931adda10401be30b46ad4ec2f8", "The current preserve_thinking support list does not include the older qwen-flash. Thinking-tool examples return complete messages without adding that parameter."),
    "qwen:max_completion_tokens": ("38120c4d69188d1056282f1a83c630d3850e4746dd6168976dfc0c7306c773f7", "The documented parameter support list starts at Qwen3.5-Flash. It is not directly applied to the older qwen-flash; the examples retain the documented max_tokens answer budget."),
    "zhipu:vision": ("9079d62c7901b72a0c62cebf34e2a38bf4f8d4bef0b9b8e85d80d92ce1e398e7", "The official model page lists text for both input and output modalities. Image examples for GLM vision models must not be transplanted."),
    "zhipu:context_caching": ("1461f4b8c1a4cca1f22f5dc7a3607e6dab19488ad5f7509646dc6347253850eb", "The official page lists context caching, but this batch adds no cache-hit observation example. Model-specific usage fields still need checking; two requests do not guarantee a cache hit."),
    "zhipu:server_json_schema_and_strict_tools": ("74459c4e81baff08f52d520d57b768d76bcc9654343a969ab0a7772e3f039c25", "The current text-request schema lists text/json_object only, and FunctionObject does not list strict. Client-side JSON Schema validation and other vendors' strict-tool capabilities are not transplanted to this model."),
}


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


def _model_identity_conflicts(request):
    # Paid GLM must not inherit a response from the old free Flash model.
    # Do not impose exact matching on other vendors' documented aliases.
    return request.get("requested_model") == "glm-4.7" and request.get("served_model") is not None and request["served_model"] != "glm-4.7"


def _completion_succeeded(request):
    """与 runner.completion_succeeded 保持同一门槛；只读安全元数据。"""
    status, chars = request.get("http_status"), request.get("content_chars")
    if _model_identity_conflicts(request):
        return False
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
        _require(not any(_model_identity_conflicts(request) for request in requests), "付费 GLM 请求的实际返回型号冲突，不能标记通过")
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


def render_index(catalogs, language="zh"):
    if language == "en":
        return _render_index_en(catalogs)
    _require(language == "zh", "未知页面语言")
    lines = [
        "# 官方功能示例索引", "",
        "中文 | [English](../en/docs/example-index.md)", "",
        "> 本页由各型号的 `examples/sources.json` 生成；修改清单后运行同步命令，不手改本页。", "",
        "这里的代码是**基于官方文档改写的项目示例**，不是厂商发布的 SDK，也不是官方示例原文镜像。"
        "每项清单记录官方链接、准确型号、所需环境变量、运行命令、改写说明和文件级验证范围。", "",
        "## 如何使用", "",
        "在仓库根目录安装 [requirements-lock.txt](../requirements-lock.txt)，设置对应 Key 和输入变量后运行文件。"
        "Python 示例共用锁定环境；TypeScript 的 Node.js 与 SDK 要求见 [package.json](../package.json)，可用 `npm ci` 安装锁定 SDK。"
        "清单里的 `npx tsx` 命令另需 tsx，逐文件执行器则直接使用 Node；具体方式见[验证与复现](验证与复现.md)。cURL 例子另需 curl/bash/Python。"
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


def _render_index_en(catalogs):
    lines = [
        "# Official-documentation example index", "",
        "[中文](../../docs/官方示例索引.md) | English", "",
        "> Generated from each model's `examples/sources.json`. Update the manifests and regenerate; do not edit this page by hand.", "",
        "These are project examples adapted from official documentation, not a vendor SDK or a verbatim mirror of official samples. "
        "Each manifest records the exact model, official sources, required environment variables, commands, adaptations, and file-level evidence.", "",
        "## Usage", "",
        "Install [requirements-lock.txt](../../requirements-lock.txt) from the repository root, then set the required key and inputs. "
        "Python examples share the locked environment. TypeScript runtime/SDK requirements are in [package.json](../../package.json); `npm ci` installs the locked SDK. "
        "The catalog's `npx tsx` command additionally uses tsx, while the file executor invokes Node directly; see [reproduction](verification.md). cURL examples need curl, bash, and Python. "
        "Images and videos are sent to the relevant vendor: use only material you are authorized to upload.", "",
        "Read the [English model manuals](../../models/README.en.md) and parameter notes before calling a model. "
        "Query by capability without sending requests:", "", "```bash",
        "python skills/model-manual/scripts/example_catalog.py --vendor deepseek --capability vision",
        "python skills/model-manual/scripts/example_catalog.py --model kimi-k2.6 --capability video_input",
        "python skills/model-manual/scripts/example_catalog.py --write-index",
        "python skills/model-manual/scripts/example_catalog.py --check", "```", "",
        "The machine-readable JSON remains in its canonical schema, including the original source metadata. "
        "Use `--model` alone to list capability keys. An unknown model or capability exits with code 2 and never falls back to another model; "
        "known models include available keys and relevant integration boundaries in the diagnostics. "
        "`or` in the environment column means either input is sufficient; the API key is always required. Optional variables are documented in the files.", "",
        "## Evidence labels", "",
        "- `mock_tested`: a fake SDK checks request construction, message history, and failure handling; it does not prove server acceptance or answer quality.",
        "- `compile_checked`: syntax compilation only. `not_run`: that class of check has not run.",
        "- `live=passed`: the example and support-file hashes match a real file-execution report, the process and the example's own checks succeeded, "
        "and Python / TypeScript / cURL recorded `real_httpx` / `real_fetch` / `real_curl`. The last request for the target model must succeed, finish normally, "
        "and return nonempty final text with no unresolved tools, business error, or telemetry failure. Streaming also needs `[DONE]` or a real transport EOF marker. "
        "Old process-only reports remain available but cannot establish canonical `passed` status.",
        "- `passed` does not establish support for every parameter combination, semantic accuracy, visual recognition quality, or future availability. Read the model-specific parameter page.",
        "- `failed`, `rate_limited`, and `timeout` are not passes. `missing_key`, `missing_input`, and `missing_runtime` mean execution prerequisites were missing.",
        "- `live=not_run` has no online execution evidence for that file. Other states require a report with matching model, status, and current source/support hashes; "
        "the time is read from that report. [Historical workflow checks](verification-status.md) cannot substitute for file-level evidence. "
        "The complete repository release view is [example execution status](example-status.md).", "",
    ]
    for catalog in catalogs:
        directory = Path(catalog["catalog_path"]).parent.as_posix()
        model_directory = Path(directory).parent.as_posix()
        lines.extend([
            f"## {catalog['vendor']} · `{catalog['model_id']}`", "",
            f"Sources checked: {catalog['checked_at']}. [Canonical sources, commands, and adaptations](../../{catalog['catalog_path']}). "
            f"[English model manual](../../{model_directory}/README.en.md).", "",
        ])
        if "parameters_path" in catalog:
            parameters = Path(catalog["parameters_path"]).with_name("parameters.en.md").as_posix()
            lines.extend([f"Required reading: [parameter reference and file mapping](../../{parameters}).", ""])
        lines.extend([
            "| Capability / file | Search key | Required environment | Official sources | Offline / file execution | Time / report / evidence |",
            "|---|---|---|---|---|---|",
        ])
        for entry in catalog["examples"]:
            sources = " · ".join(f"[Official source {index}]({source['url']})" for index, source in enumerate(entry["sources"], 1))
            env = "<br>".join(value.replace("|", " or ") for value in entry["required_env"])
            check = entry["verification"]
            evidence = "—"
            if check["live"] != "not_run":
                scope = {HTTP_SCOPE: "HTTP metadata", PROCESS_SCOPE: "Process and internal checks"}.get(check.get("evidence_scope"), "No execution evidence obtained")
                evidence = f"{check['tested_at']}<br>[Report](../../{check['report']})<br>{scope}"
            lines.append(f"| [{entry['capability']} · {entry['file']}](../../{directory}/{entry['file']}) | `{entry['capability']}` | {env} | {sources} | {check['offline']} / {check['live']} | {evidence} |")
        if catalog.get("not_integrated"):
            lines.extend(["", "### Integration gaps and model-specific boundaries", "",
                          "A missing example does not establish that the model lacks the capability. These entries are taken from the same source manifest.", ""])
            for item in catalog["not_integrated"]:
                sources = " · ".join(f"[Official source {index}]({source['url']})" for index, source in enumerate(item["sources"], 1))
                reason = _gap_reason_en(catalog["vendor"], item)
                lines.append(f"- `{item['capability']}`: {reason} {sources}")
        lines.append("")
    return "\n".join(lines)


def _gap_reason_en(vendor, item):
    """Translations are fingerprinted to the canonical reason; changed facts never reuse stale wording."""
    record = GAP_TRANSLATIONS.get(f"{vendor}:{item['capability']}")
    if record and hashlib.sha256(item["reason"].encode("utf-8")).hexdigest() == record[0]:
        return record[1]
    return "Not integrated in this example collection. The model-specific reason is new or changed; consult the English model manual, canonical source manifest, and linked official documentation before use."


def index_outputs(catalogs):
    return {INDEX: render_index(catalogs), EN_INDEX: render_index(catalogs, language="en")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor", choices=sorted(HOSTS))
    parser.add_argument("--model")
    parser.add_argument("--capability", help="精确能力词；不确定时先仅用 --model 列出该型号示例")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write-index", action="store_true", help="从清单生成中英文 Markdown 索引")
    action.add_argument("--check", action="store_true", help="检查清单与中英文生成索引是否一致")
    args = parser.parse_args(argv)
    if (args.write_index or args.check) and (args.vendor or args.model or args.capability):
        parser.error("索引生成/检查不能使用筛选参数")
    try:
        catalogs = load_catalogs(ROOT)
        if args.write_index or args.check:
            for relative, content in index_outputs(catalogs).items():
                target = ROOT / relative
                if args.write_index:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
                    print(relative.as_posix())
                elif not target.is_file() or target.read_text(encoding="utf-8") != content:
                    raise ValueError(f"索引过期：{relative.as_posix()}，请运行 --write-index")
            if args.check:
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
