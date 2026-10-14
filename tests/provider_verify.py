"""五家模型共享的真实验证器；报告和终端只保留白名单元数据。

依赖由 requirements-lock.txt 固定。离线单元测试使用 mock，不发送请求。
每次真实调用的结束原因、参数和 token 用量由同一套规则检查并记录。
"""

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import platform
import struct
import subprocess
import time
import zlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
STATUSES = ("passed", "failed", "rate_limited", "skipped")
FINISH_REASONS = {"stop", "tool_calls", "length", "content_filter", "function_call", "insufficient_system_resource", "aborted"}


@dataclass(frozen=True)
class ProviderSpec:
    vendor: str
    model: str
    key_env: str
    base_url: str
    vision: bool = False
    thinking_style: str = "thinking"
    json_type: str = "json_object"
    named_tool_choice: bool = True
    retry_attempts: int = 1


def load_specs():
    """测试目标保持明确；接口与扩展参数读取同一份型号卡片。"""
    models = {
        "deepseek": "deepseek-flash",
        "kimi": "kimi-k2.6",
        "zhipu": "glm-4.7",
        "qwen": "qwen-flash",
        "doubao": "doubao-seed-2-1-pro-260628",
    }
    specs = {}
    for vendor, model in models.items():
        card = json.loads((ROOT / f"skills/model-manual/references/models/{model}.json").read_text(encoding="utf-8"))
        if card["vendor"] != vendor or card["model_id"] != model:
            raise ValueError("测试目标与型号卡片不一致")
        generation = card["generation"]
        on = generation["thinking"]["on"]["value"]
        off = generation["thinking"]["off"]["value"]
        style = "enable_thinking" if "enable_thinking" in on else "thinking"
        if style == "enable_thinking":
            expected = ({"enable_thinking": True}, {"enable_thinking": False})
        else:
            expected = ({"thinking": {"type": "enabled"}}, {"thinking": {"type": "disabled"}})
        if (on, off) != expected or generation["token_budget"]["parameter"]["value"] != "max_tokens":
            raise ValueError("测试配置发生变化，需要更新固定样例")
        vision = card["capabilities"].get("vision", {}).get("status")
        specs[vendor] = ProviderSpec(
            vendor, model,
            generation["key_env"]["value"],
            generation["base_url"]["value"],
            vision=vision in {"verified", "documented"},
            thinking_style=style,
            json_type=generation["json_output"]["response_format"]["value"]["type"],
            named_tool_choice=False,
            retry_attempts=2 if vendor == "zhipu" else 1,
        )
    return specs


SPECS = load_specs()


class VerificationFailure(Exception):
    """错误码固定于程序，不使用供应商正文或异常消息。"""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def field(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def safe_int(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def usage_metadata(response):
    usage = field(response, "usage")
    details = field(usage, "completion_tokens_details")
    return {
        "input_tokens": safe_int(field(usage, "prompt_tokens")),
        "output_tokens": safe_int(field(usage, "completion_tokens")),
        "total_tokens": safe_int(field(usage, "total_tokens")),
        "reasoning_tokens": safe_int(field(details, "reasoning_tokens")),
    }


def usage_summary(response) -> str:
    return ", ".join(f"{key}={value}" for key, value in usage_metadata(response).items())


def require_finish_reason(reason, mode="text"):
    if reason == "length":
        raise VerificationFailure("output_truncated")
    expected = "tool_calls" if mode == "tools" else "stop"
    if reason != expected:
        raise VerificationFailure("missing_finish_reason" if reason is None else "unexpected_finish_reason")


def completion_choice(response):
    choices = field(response, "choices", []) or []
    if len(choices) != 1:
        raise VerificationFailure("unexpected_choice_count")
    return choices[0]


def require_content(response) -> str:
    choice = completion_choice(response)
    require_finish_reason(field(choice, "finish_reason"))
    message = field(choice, "message")
    if field(message, "tool_calls"):
        raise VerificationFailure("unexpected_tool_calls")
    content = field(message, "content") or ""
    if not isinstance(content, str) or not content.strip():
        raise VerificationFailure("empty_content")
    return content


def require_tools(response):
    choice = completion_choice(response)
    require_finish_reason(field(choice, "finish_reason"), "tools")
    calls = field(field(choice, "message"), "tool_calls") or []
    if not calls:
        raise VerificationFailure("empty_tool_calls")
    return calls


def completion_metadata(response):
    result = usage_metadata(response)
    choices = field(response, "choices", []) or []
    if len(choices) == 1:
        choice = choices[0]
        reason = field(choice, "finish_reason")
        result["finish_reason"] = reason if reason in FINISH_REASONS else None
        message = field(choice, "message")
        content = field(message, "content")
        result["content_chars"] = len(content) if isinstance(content, str) else 0
        result["reasoning_present"] = bool(field(message, "reasoning_content"))
        result["tool_call_count"] = len(field(message, "tool_calls", []) or [])
    return result


def consume_stream(stream, observation=None):
    """usage-only 空 choices 块合法；有正文但没有正常结束块仍失败。"""
    observation = observation if observation is not None else {}
    observation["stream_completed"] = False
    parts, finish = [], None
    seen_choice = False
    try:
        for chunk in stream:
            if field(chunk, "usage") is not None:
                observation.update(usage_metadata(chunk))
            choices = field(chunk, "choices", []) or []
            if not choices:
                continue
            if len(choices) != 1:
                raise VerificationFailure("unexpected_choice_count")
            choice = choices[0]
            delta = field(choice, "delta")
            text = field(delta, "content") or ""
            if not isinstance(text, str):
                raise VerificationFailure("invalid_content_type")
            if finish is not None and (text or field(delta, "tool_calls")):
                raise VerificationFailure("content_after_finish")
            if field(delta, "tool_calls"):
                raise VerificationFailure("unexpected_tool_calls")
            seen_choice = True
            parts.append(text)
            reason = field(choice, "finish_reason")
            if reason is not None:
                if finish is not None and reason != finish:
                    raise VerificationFailure("conflicting_finish_reason")
                finish = reason
                observation["finish_reason"] = reason if reason in FINISH_REASONS else None
    finally:
        close = getattr(stream, "close", None)
        if callable(close):
            close()
        observation["content_chars"] = sum(len(part) for part in parts)
    if not seen_choice:
        raise VerificationFailure("empty_stream")
    require_finish_reason(finish)
    content = "".join(parts)
    if not content.strip():
        raise VerificationFailure("empty_content")
    observation["stream_completed"] = True
    return content


def make_test_png(width: int = 32, height: int = 32) -> str:
    """生成纯红 PNG data URL；色值只在图片中，测试问题不透露答案。"""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    scanlines = b"".join(b"\x00" + b"\xff\x00\x00" * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b"")
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def safe_request_parameters(kwargs):
    """白名单序列化：不记录 messages、工具定义或任意扩展。"""
    result = {}
    for key in ("max_tokens", "max_completion_tokens"):
        if safe_int(kwargs.get(key)) is not None:
            result[key] = kwargs[key]
    if isinstance(kwargs.get("stream"), bool):
        result["stream"] = kwargs["stream"]
    stream_options = kwargs.get("stream_options")
    if isinstance(stream_options, dict) and isinstance(stream_options.get("include_usage"), bool):
        result["include_usage"] = stream_options["include_usage"]
    if kwargs.get("reasoning_effort") in {"none", "minimal", "low", "medium", "high", "xhigh", "max"}:
        result["reasoning_effort"] = kwargs["reasoning_effort"]
    extra = kwargs.get("extra_body") or {}
    if isinstance(extra, dict):
        thinking = extra.get("thinking")
        if isinstance(thinking, dict) and thinking.get("type") in {"enabled", "disabled"}:
            result["thinking"] = {"type": thinking["type"]}
        if isinstance(extra.get("enable_thinking"), bool):
            result["enable_thinking"] = extra["enable_thinking"]
    fmt = kwargs.get("response_format") or {}
    if isinstance(fmt, dict) and fmt.get("type") in {"text", "json_object", "json_schema"}:
        result["response_format_type"] = fmt["type"]
    choice = kwargs.get("tool_choice")
    if isinstance(choice, str) and choice in {"auto", "none", "required"}:
        result["tool_choice_mode"] = choice
    elif isinstance(choice, dict):
        result["tool_choice_mode"] = "named_function"
    if "tools" in kwargs:
        result["tools_supplied"] = True
    return result


def safe_error(exc):
    if isinstance(exc, VerificationFailure):
        return {"code": exc.code}
    status = safe_int(getattr(exc, "status_code", None))
    categories = {400: "invalid_request", 401: "authentication_failed", 403: "permission_denied", 404: "model_or_endpoint_unavailable", 429: "rate_limited"}
    code = categories.get(status, "server_error" if status is not None and status >= 500 else "http_error")
    if status is None:
        name = type(exc).__name__
        code = "request_timeout" if name in {"APITimeoutError", "ReadTimeout", "ConnectTimeout", "WriteTimeout", "PoolTimeout", "TimeoutError"} else "request_or_validation_error"
    error = {"code": code}
    if status is not None:
        error["http_status"] = status
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        detail = body.get("error", body)
        code = detail.get("code") if isinstance(detail, dict) else None
        if str(code) in {"1302", "1305", "429"}:
            error["provider_code"] = str(code)
    return error


def validate_endpoint(value):
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("base URL must be HTTPS without credentials, query or fragment")
    return value.rstrip("/")


def source_metadata():
    """源码身份含未提交改动摘要，不输出 Git 路径或文件正文。"""
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout
    try:
        commit = git("rev-parse", "HEAD").decode().strip()
        dirty = bool(git("status", "--porcelain"))
        digest = hashlib.sha256(git("diff", "HEAD", "--binary"))
        for filename in sorted(git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0")):
            if filename:
                digest.update(filename)
                candidate = ROOT / os.fsdecode(filename)
                if candidate.is_file():
                    digest.update(candidate.read_bytes())
        return {"source_git_commit": commit, "source_git_dirty": dirty, "source_git_diff_sha256": digest.hexdigest()}
    except (OSError, subprocess.CalledProcessError):
        return {"source_git_commit": None, "source_git_dirty": None, "source_git_diff_sha256": None}


def runtime_metadata():
    try:
        sdk = importlib.metadata.version("openai")
    except importlib.metadata.PackageNotFoundError:
        sdk = None
    return {"python": platform.python_version(), "openai": sdk}


def thinking_body(spec, enabled):
    if spec.thinking_style == "enable_thinking":
        return {"enable_thinking": enabled}
    return {"thinking": {"type": "enabled" if enabled else "disabled"}}


def validate_tool_call(call):
    if field(call, "type") != "function" or field(field(call, "function"), "name") != "get_weather":
        raise VerificationFailure("tool_not_allowlisted")
    call_id = field(call, "id")
    if not isinstance(call_id, str) or not call_id:
        raise VerificationFailure("missing_tool_call_id")
    try:
        arguments = json.loads(field(field(call, "function"), "arguments"))
    except (TypeError, json.JSONDecodeError):
        raise VerificationFailure("invalid_tool_json") from None
    if not isinstance(arguments, dict) or set(arguments) != {"city"}:
        raise VerificationFailure("invalid_tool_argument_keys")
    if not isinstance(arguments["city"], str) or arguments["city"] not in {"杭州", "Hangzhou"}:
        raise VerificationFailure("invalid_tool_city")
    return arguments


class VerificationRunner:
    def __init__(self, spec, client, endpoint=None):
        self.spec, self.client = spec, client
        self.base_url = validate_endpoint(endpoint or spec.base_url)
        self.endpoint = self.base_url + "/chat/completions"
        self.results, self.current = [], None

    def call(self, **kwargs):
        request = {"parameters": safe_request_parameters(kwargs), "attempts": 0, "response_received": False}
        self.current["requests"].append(request)
        for attempt in range(self.spec.retry_attempts):
            request["attempts"] = attempt + 1
            try:
                response = self.client.chat.completions.create(model=self.spec.model, **kwargs)
                request["response_received"] = True
                if not kwargs.get("stream"):
                    request["response"] = completion_metadata(response)
                return response
            except Exception as exc:
                if getattr(exc, "status_code", None) != 429 or attempt + 1 == self.spec.retry_attempts:
                    raise
                time.sleep(2 ** attempt)

    def run(self, test_id, test):
        self.current = {"id": test_id, "vendor": self.spec.vendor, "model_id": self.spec.model, "base_url": self.base_url, "endpoint": self.endpoint, "requests": []}
        try:
            test()
            self.current["status"] = "passed"
        except Exception as exc:
            self.current["status"] = "rate_limited" if getattr(exc, "status_code", None) == 429 else "failed"
            self.current["error"] = safe_error(exc)
        self.results.append(self.current)
        print_result(self.current)

    def basic(self):
        require_content(self.call(messages=[{"role": "user", "content": "只回复：收到"}], max_tokens=512, extra_body=thinking_body(self.spec, False)))

    def streaming(self):
        stream = self.call(messages=[{"role": "user", "content": "只回复：流式正常"}], stream=True, stream_options={"include_usage": True}, max_tokens=512, extra_body=thinking_body(self.spec, False))
        observation = {}
        self.current["requests"][-1]["response"] = observation
        consume_stream(stream, observation)

    def thinking_on(self):
        response = self.call(messages=[{"role": "user", "content": "9.11 和 9.8 哪个更大？请给出简短答案。"}], max_tokens=16384, extra_body=thinking_body(self.spec, True))
        require_content(response)
        reasoning = field(field(completion_choice(response), "message"), "reasoning_content")
        if not isinstance(reasoning, str) or not reasoning.strip():
            raise VerificationFailure("missing_reasoning")

    def thinking_off(self):
        response = self.call(messages=[{"role": "user", "content": "1+1 等于几？"}], max_tokens=512, extra_body=thinking_body(self.spec, False))
        require_content(response)
        if field(field(completion_choice(response), "message"), "reasoning_content"):
            raise VerificationFailure("unexpected_reasoning")

    def json_output(self):
        fmt = {"type": "json_object"}
        if self.spec.json_type == "json_schema":
            fmt = {"type": "json_schema", "json_schema": {"name": "result", "strict": True, "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}}}
        response = self.call(messages=[{"role": "system", "content": '只返回 JSON 对象：{"ok":true}。'}, {"role": "user", "content": "返回 ok 为 true 的 JSON"}], response_format=fmt, max_tokens=512, extra_body=thinking_body(self.spec, False))
        try:
            result = json.loads(require_content(response))
        except json.JSONDecodeError:
            raise VerificationFailure("invalid_json_output") from None
        if result != {"ok": True} or type(result.get("ok")) is not bool:
            raise VerificationFailure("unexpected_json_output")

    def tool_calling(self):
        tools = [{"type": "function", "function": {"name": "get_weather", "description": "查询城市天气", "parameters": {"type": "object", "properties": {"city": {"type": "string", "enum": ["杭州", "Hangzhou"]}}, "required": ["city"], "additionalProperties": False}}}]
        messages = [{"role": "user", "content": "调用天气工具查询杭州，并在收到结果后用中文回复天气和摄氏温度。"}]
        choice = {"type": "function", "function": {"name": "get_weather"}} if self.spec.named_tool_choice else "auto"
        first = self.call(messages=messages, tools=tools, tool_choice=choice, max_tokens=1024, extra_body=thinking_body(self.spec, False))
        calls = require_tools(first)
        if len(calls) != 1:
            raise VerificationFailure("unexpected_tool_call_count")
        call = calls[0]
        arguments = validate_tool_call(call)
        self.current["requests"][-1]["response"]["tool_arguments_validated"] = True
        message = field(completion_choice(first), "message")
        # 提供方思考字段用于续轮，报告不保存消息、调用 ID 或参数。
        assistant = {"role": "assistant", "content": field(message, "content"), "tool_calls": [{"id": field(call, "id"), "type": "function", "function": {"name": "get_weather", "arguments": json.dumps(arguments, ensure_ascii=False)}}]}
        reasoning = field(message, "reasoning_content")
        if reasoning is not None:
            assistant["reasoning_content"] = reasoning
        messages.append(assistant)
        # 本地固定 fixture；先完成 allowlist 和参数验证再回传结果。
        result = {"city": arguments["city"], "weather": "晴", "temperature_c": 23}
        messages.append({"role": "tool", "tool_call_id": field(call, "id"), "content": json.dumps(result, ensure_ascii=False)})
        final = self.call(messages=messages, tools=tools, tool_choice="none", max_tokens=1024, extra_body=thinking_body(self.spec, False))
        content = require_content(final)
        if "23" not in content or not any(word in content.lower() for word in ("晴", "sunny", "clear")):
            raise VerificationFailure("tool_result_not_used")

    def vision(self):
        response = self.call(messages=[{"role": "user", "content": [{"type": "text", "text": "图片的主要颜色是什么？只回复一个英文小写颜色词。"}, {"type": "image_url", "image_url": {"url": make_test_png()}}]}], max_tokens=512, extra_body=thinking_body(self.spec, False))
        content = require_content(response).strip().lower().strip(".。!！\"'` ")
        if content != "red":
            raise VerificationFailure("wrong_image_color")

    def execute(self, basic_only=False):
        tests = [("chat_completions", self.basic), ("streaming", self.streaming), ("thinking_disabled", self.thinking_off)]
        if not basic_only:
            json_id = "structured_output" if self.spec.json_type == "json_schema" else "json_object"
            tests += [("thinking_enabled", self.thinking_on), (json_id, self.json_output), ("tool_calling", self.tool_calling)]
            if self.spec.vision:
                tests.append(("vision", self.vision))
        rate_limited = False
        for name, test in tests:
            if rate_limited:
                result = {"id": name, "vendor": self.spec.vendor, "model_id": self.spec.model, "base_url": self.base_url, "endpoint": self.endpoint, "status": "skipped", "error": {"code": "not_run_after_rate_limit"}, "requests": []}
                self.results.append(result)
                print_result(result)
                continue
            self.run(name, test)
            rate_limited = self.results[-1]["status"] == "rate_limited"
        return self.results


def print_result(result):
    suffix = " ".join(f"{key}={value}" for key, value in result.get("error", {}).items())
    print(f"{result['status'].upper()} {result['vendor']}/{result['model_id']} {result['id']} {suffix}".rstrip())


def count_results(results):
    return {status: sum(result["status"] == status for result in results) for status in STATUSES}


def result_exit_code(counts):
    if counts["failed"]:
        return 1
    if counts["rate_limited"] or counts["skipped"] or not counts["passed"]:
        return 2
    return 0


def make_report(results, source=None, single_vendor=None):
    report = {
        "schema_version": 2,
        "tested_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "runtime": runtime_metadata(),
        **(source if source is not None else source_metadata()),
        "counts": count_results(results),
        "results": results,
        "privacy": {"api_key_saved": False, "response_content_saved": False, "reasoning_content_saved": False, "tool_arguments_saved": False, "request_id_saved": False, "request_messages_saved": False, "raw_error_saved": False},
    }
    if single_vendor:
        spec = SPECS[single_vendor]
        report.update({"vendor": spec.vendor, "model_id": spec.model})
    return report


def write_report(destination, report, overwrite=False):
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w" if overwrite else "x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_env():
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.removeprefix("export ").strip(), value.strip().strip('"').strip("'")
        if key in {spec.key_env for spec in SPECS.values()} and value and "粘贴" not in value:
            os.environ.setdefault(key, value)


def main(argv=None, single_vendor=None):
    parser = argparse.ArgumentParser(description="真实 API 验证；仅正常完成的回答或工具闭环会通过。")
    if not single_vendor:
        parser.add_argument("vendors", nargs="*", metavar="VENDOR")
    parser.add_argument("--report", type=Path, help="生成脱敏 JSON 报告；目标已存在则拒绝。")
    parser.add_argument("--overwrite", action="store_true", help="明确允许覆盖 --report 目标。")
    parser.add_argument("--base-url", help="覆盖单一厂商 HTTPS base URL；不允许凭据/query/fragment。")
    parser.add_argument("--timeout", type=float, default=60, help="单次请求超时秒数，默认 60。")
    args = parser.parse_args(argv)
    vendors = [single_vendor] if single_vendor else (args.vendors or list(SPECS))
    if any(vendor not in SPECS for vendor in vendors):
        parser.error("未知厂商，可选：" + ", ".join(SPECS))
    if len(vendors) != len(set(vendors)):
        parser.error("厂商参数不能重复")
    if args.overwrite and not args.report:
        parser.error("--overwrite 必须同时提供 --report")
    if args.report and args.report.exists() and not args.overwrite:
        parser.error("报告目标已存在；请选择新路径或明确使用 --overwrite")
    if args.base_url and len(vendors) != 1:
        parser.error("--base-url 只支持一次选择一个厂商")
    if not 0 < args.timeout <= 180:
        parser.error("--timeout 必须大于 0 且不超过 180 秒")
    try:
        endpoint_override = validate_endpoint(args.base_url) if args.base_url else None
    except ValueError:
        parser.error("base URL 必须是无凭据、query、fragment 的 HTTPS 地址")
    source = source_metadata()
    load_env()
    results = []
    for vendor in vendors:
        spec = SPECS[vendor]
        key = os.environ.get(spec.key_env)
        if not key:
            result = {"id": "configuration", "vendor": vendor, "model_id": spec.model, "status": "skipped", "error": {"code": "missing_api_key"}, "requests": []}
            results.append(result)
            print_result(result)
            continue
        try:
            from openai import OpenAI
            endpoint = endpoint_override or spec.base_url
            client = OpenAI(api_key=key, base_url=endpoint, timeout=args.timeout, max_retries=0)
            try:
                results += VerificationRunner(spec, client, endpoint).execute(basic_only=not single_vendor)
            finally:
                client.close()
        except Exception as exc:
            result = {"id": "client_setup", "vendor": vendor, "model_id": spec.model, "status": "failed", "error": safe_error(exc), "requests": []}
            results.append(result)
            print_result(result)
    report = make_report(results, source=source, single_vendor=single_vendor)
    if args.report:
        try:
            write_report(args.report, report, overwrite=args.overwrite)
        except OSError:
            print("FAILED report_write code=report_not_written")
            return 1
        print("脱敏 JSON 报告已生成。")
    print("结果：" + ", ".join(f"{status}={report['counts'][status]}" for status in STATUSES))
    return result_exit_code(report["counts"])
