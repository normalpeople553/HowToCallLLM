"""逐文件运行真实示例；不替换模型响应，不保存密钥、正文或原始错误。

默认只列清单；--execute 才发送真实请求。Python 使用原 SDK 的真实 HTTPTransport，
记录器只旁观传输，不改请求/响应。Shell/TS 同样旁观真实网络元数据。
"""

import argparse
import base64
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import logging
import os
from pathlib import Path
import re
import runpy
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib


ROOT = Path(__file__).resolve().parents[1]
KEYS = {
    "deepseek": "DEEPSEEK_API_KEY", "kimi": "MOONSHOT_API_KEY",
    "qwen": "DASHSCOPE_API_KEY", "zhipu": "ZHIPU_API_KEY",
    "doubao": "ARK_API_KEY", "minimax": "MINIMAX_API_KEY",
}
HOSTS = {"api.deepseek.com", "api.moonshot.cn", "dashscope.aliyuncs.com", "open.bigmodel.cn", "ark.cn-beijing.volces.com", "api.minimax.cn"}
SAFE_PARAMETERS = {"stream", "max_tokens", "max_completion_tokens", "max_output_tokens", "temperature", "top_p", "reasoning_effort", "reasoning_split", "thinking", "enable_thinking", "tool_choice", "stream_options", "reasoning", "response_format"}
LIVE_STATUSES = {"passed", "failed", "rate_limited", "missing_key", "missing_input", "missing_runtime", "timeout"}


def credentials(env=None, env_path=None):
    result = dict(os.environ if env is None else env)
    path = env_path or ROOT / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.strip().removeprefix("export ").partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if sep and key in KEYS.values() and value and "替换" not in value and "你的" not in value:
                result.setdefault(key, value)
    # 不继承调试日志开关，避免原 SDK 将请求/响应正文写到 stderr。
    result.pop("OPENAI_LOG", None)
    return result


def discover():
    rows = []
    for manifest in sorted((ROOT / "models").glob("*/*/examples/sources.json")):
        catalog = json.loads(manifest.read_text(encoding="utf-8"))
        for entry in catalog["examples"]:
            rows.append({"path": (manifest.parent / entry["file"]).relative_to(ROOT).as_posix(), "vendor": catalog["vendor"], "model_id": catalog["model_id"], "required_keys": [KEYS[catalog["vendor"]]], "capability": entry["capability"]})
    for path in sorted((ROOT / "examples").glob("*.py")):
        all_vendors = path.name == "02_one_for_all.py"
        rows.append({"path": path.relative_to(ROOT).as_posix(), "vendor": "shared" if all_vendors else "deepseek", "model_id": "multiple" if all_vendors else "deepseek-flash", "required_keys": list(KEYS.values()) if all_vendors else [KEYS["deepseek"]], "capability": "shared_example"})
    return rows


def file_identity(path):
    path = ROOT / path
    files = [path]
    if path.parent != ROOT / "examples":
        files += sorted(path.parent.glob("_*.py"))
    if path.name == "02_one_for_all.py":
        files += sorted((ROOT / "skills/model-manual/references/models").glob("*.json"))
        files += [ROOT / "skills/model-manual/references/vendors.json"]
    if path.suffix == ".ts":
        files.append(ROOT / "tests/live_fetch.mjs")
    if path.suffix == ".sh":
        files.append(ROOT / "tests/live_curl.py")
    return {item.relative_to(ROOT).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest() for item in files}


def png_bytes():
    def block(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    scanlines = (b"\x00" + b"\xff\x00\x00" * 256) * 256
    return b"\x89PNG\r\n\x1a\n" + block(b"IHDR", struct.pack(">IIBBBBB", 256, 256, 8, 2, 0, 0, 0)) + block(b"IDAT", zlib.compress(scanlines)) + block(b"IEND", b"")


def prepare_inputs(directory, env):
    result = dict(env)
    image = directory / "synthetic-red.png"
    image.write_bytes(png_bytes())
    # 只上传本工具生成的公开教学素材，不读取用户照片。
    result.pop("IMAGE_URL", None)
    result.pop("IMAGE_FILE_ID", None)
    result.pop("VIDEO_PATH", None)
    result.pop("VIDEO_URL", None)
    result["IMAGE_PATH"] = str(image)
    if shutil.which("ffmpeg"):
        video = directory / "synthetic-red.mp4"
        command = ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=red:s=128x128:r=1:d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", str(video)]
        completed = subprocess.run(command, capture_output=True, timeout=30)
        if completed.returncode == 0:
            result["VIDEO_PATH"] = str(video)
    return result


def safe_parameters(payload):
    result = {}
    for name in SAFE_PARAMETERS & payload.keys():
        value = payload[name]
        if name in {"max_tokens", "max_completion_tokens", "max_output_tokens", "temperature", "top_p"}:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
        elif name in {"stream", "reasoning_split", "enable_thinking"}:
            if not isinstance(value, bool):
                continue
        elif name in {"reasoning_effort", "tool_choice"}:
            if name == "tool_choice" and isinstance(value, dict):
                value = "named_function"
            elif not isinstance(value, str) or value not in {"none", "auto", "required", "low", "medium", "high", "max", "xhigh"}:
                continue
        elif name == "response_format":
            if not isinstance(value, dict) or value.get("type") not in {"json_object", "json_schema", "text"}:
                continue
            value = {"type": value["type"]}
        elif name == "thinking":
            if not isinstance(value, dict):
                continue
            value = {key: item for key, item in value.items() if key in {"type", "keep"} and isinstance(item, str) and item in {"enabled", "disabled", "adaptive", "all", "none"}}
        elif name == "stream_options":
            if not isinstance(value, dict):
                continue
            value = {key: item for key, item in value.items() if key == "include_usage" and isinstance(item, bool)}
        elif name == "reasoning":
            if not isinstance(value, dict):
                continue
            value = {key: item for key, item in value.items() if key == "effort" and isinstance(item, str) and item in {"none", "low", "medium", "high", "max", "xhigh"}}
        if isinstance(value, (bool, int, float, str, dict)):
            result[name] = value
    return result


def observe_json(record, data):
    if not isinstance(data, dict):
        return
    error = data.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        allowed_codes = {"1302", "1305", "1308", "1113", "429", "rate_limit_exceeded", "insufficient_quota"}
        if not isinstance(code, bool) and isinstance(code, (int, str)) and str(code) in allowed_codes:
            record["provider_error_code"] = str(code)
    model = data.get("model")
    if isinstance(model, str) and re.fullmatch(r"(?:deepseek|kimi|glm|qwen|doubao|MiniMax|ep)[A-Za-z0-9_.:-]{0,100}", model, re.I):
        record["served_model"] = model
    if isinstance(data.get("base_resp"), dict):
        code = data["base_resp"].get("status_code")
        if isinstance(code, int) and not isinstance(code, bool):
            record["business_status"] = code
    usage = data.get("usage")
    if isinstance(usage, dict):
        record["usage"] = {key: value for key, value in usage.items() if key in {"prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens"} and isinstance(value, int) and not isinstance(value, bool) and value >= 0}
    choices = data.get("choices")
    for choice in choices if isinstance(choices, list) else []:
        if not isinstance(choice, dict):
            continue
        fim_text = choice.get("text")
        if isinstance(fim_text, str):
            record["content_chars"] = record.get("content_chars", 0) + len(fim_text)
        reason = choice.get("finish_reason")
        if isinstance(reason, str) and reason in {"stop", "length", "tool_calls", "content_filter", "aborted", "insufficient_system_resource"}:
            record.setdefault("finish_reasons", []).append(reason)
        message = choice.get("message") or choice.get("delta") or {}
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str):
            record["content_chars"] = record.get("content_chars", 0) + len(content)
        calls = message.get("tool_calls") or []
        if calls:
            record["has_tool_calls"] = True
    if data.get("object") == "response" or "output" in data and "status" in data:
        status = data.get("status")
        if isinstance(status, str) and status in {"completed", "incomplete", "failed"}:
            record["response_status"] = status
        outputs = data.get("output")
        for output in outputs if isinstance(outputs, list) else []:
            if isinstance(output, dict):
                parts = output.get("content")
                for part in parts if isinstance(parts, list) else []:
                    if isinstance(part, dict) and part.get("type") == "output_text":
                        text = part.get("text")
                        if isinstance(text, str):
                            record["content_chars"] = record.get("content_chars", 0) + len(text)


class BodyObserver:
    def __init__(self, record, sse=False, decoder=None):
        self.record, self.sse, self.decoder = record, sse, decoder
        self.buffer = b""
        self.failed = False
        self.finished = False

    def fail(self):
        # 只记录固定标志，绝不记录异常字符串或原始响应内容。
        self.record["telemetry_error"] = True
        self.failed = True
        self.buffer = b""

    def _sse_line(self, line):
        if not line.startswith(b"data:"):
            return
        value = line[5:].strip()
        if not value:
            return
        if value == b"[DONE]":
            self.record["sse_done"] = True
        else:
            observe_json(self.record, json.loads(value))

    def _feed_decoded(self, chunk):
        if len(self.buffer) + len(chunk) > 8 * 1024 * 1024:
            self.record["telemetry_overflow"] = True
            self.failed = True
            self.buffer = b""
            return
        self.buffer += chunk
        if self.sse:
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                self._sse_line(line)

    def feed(self, chunk):
        if self.failed or self.finished:
            return
        try:
            self._feed_decoded(self.decoder.decode(chunk) if self.decoder is not None else chunk)
        except Exception:
            # 旁观解析失败不能改变 SDK 自己收到的字节或异常行为。
            self.fail()

    def finish(self, eof=True):
        if self.finished:
            return
        self.finished = True
        try:
            if self.failed or not eof:
                return
            if self.decoder is not None:
                self._feed_decoded(self.decoder.flush())
            if self.failed:
                return
            if self.sse:
                # 部分服务在 EOF 前发送 data: [DONE]，但没有最后的换行。
                # 只处理已收到的尾行，不凭空补写 DONE 或补齐 JSON。
                if self.buffer:
                    self._sse_line(self.buffer)
            else:
                observe_json(self.record, json.loads(self.buffer))
        except Exception:
            self.fail()
        finally:
            self.buffer = b""


def request_record(request):
    path = request.url.path
    path = re.sub(r"(/files/)[^/]+", r"\1<redacted-id>", path)
    record = {"method": request.method, "endpoint": f"https://{request.url.host}{path}", "transport": "real_httpx"}
    if "application/json" in request.headers.get("content-type", ""):
        try:
            payload = json.loads(request.read())
            if not isinstance(payload, dict):
                return record
            record["parameters"] = safe_parameters(payload)
            model = payload.get("model")
            if isinstance(model, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", model):
                record["requested_model"] = model
        except (ValueError, TypeError):
            pass
    return record


def completion_succeeded(record):
    if type(record.get("http_status")) is not int or not 200 <= record["http_status"] < 300:
        return False
    if record.get("business_status", 0) != 0 or record.get("telemetry_overflow") or record.get("telemetry_error"):
        return False
    parameters = record.get("parameters", {})
    if not isinstance(parameters, dict):
        return False
    if parameters.get("stream") is True and not (
        record.get("sse_done") is True or record.get("transport_eof") is True
    ):
        return False
    if record.get("has_tool_calls"):
        return False
    normal = record.get("response_status") == "completed" or record.get("finish_reasons", []) == ["stop"]
    return normal and type(record.get("content_chars")) is int and record["content_chars"] > 0


def determine_status(entry, outcome, process_exit):
    requests = outcome.get("requests", [])
    if process_exit != 0 or outcome.get("exit_code") != 0:
        return "rate_limited" if any(item.get("http_status") == 429 for item in requests) else "failed"
    if not requests:
        return "failed"
    final_by_model = {}
    for record in requests:
        if record.get("requested_model"):
            final_by_model[record["requested_model"]] = record
    if entry["vendor"] == "shared":
        expected = {json.loads(path.read_text(encoding="utf-8"))["model_id"] for path in (ROOT / "skills/model-manual/references/models").glob("*.json")}
    else:
        expected = {entry["model_id"]}
    if expected <= set(final_by_model) and all(completion_succeeded(final_by_model[model]) for model in expected):
        return "passed"
    return "failed"


def child(path, telemetry):
    """不改模型参数、不替换 SDK 返回值；只旁观真正的 HTTPTransport。"""
    import httpx
    records = []
    original = httpx.HTTPTransport.handle_request

    class RecordingStream(httpx.SyncByteStream):
        def __init__(self, stream, observer):
            self.stream, self.observer = stream, observer

        def __iter__(self):
            try:
                for data in self.stream:
                    # feed 只解码供统计使用的副本；原字节原样交回 SDK。
                    self.observer.feed(data)
                    yield data
                # 某些兼容端点没有 [DONE]；只有实际读尽传输且显式 stop 才可通过。
                self.observer.record["transport_eof"] = True
            finally:
                self.observer.finish(eof=self.observer.record.get("transport_eof") is True)

        def close(self):
            try:
                self.stream.close()
            finally:
                self.observer.finish(eof=False)

    def handle(transport, request):
        if request.url.scheme != "https" or request.url.host not in HOSTS:
            raise RuntimeError("example_endpoint_not_allowlisted")
        record = request_record(request)
        records.append(record)
        response = original(transport, request)
        record["http_status"] = response.status_code
        observer = BodyObserver(record, "text/event-stream" in response.headers.get("content-type", ""))
        try:
            # httpx 0.28.1（requirements-lock.txt）在 iter_bytes 内解压响应。
            # 为旁观器创建独立 Response/decoder，绝不能取真实 response 的
            # _get_content_decoder()，否则会和 SDK 共享有状态的解码器。
            shadow = httpx.Response(response.status_code, headers=response.headers, stream=httpx.ByteStream(b""))
            observer.decoder = shadow._get_content_decoder()
            codings = response.headers.get_list("content-encoding", split_commas=True)
            safe_codings = [item.strip().lower() for item in codings if item.strip().lower() in {"identity", "gzip", "deflate", "br", "zstd"}]
            if safe_codings:
                record["content_encoding"] = ",".join(safe_codings)
        except Exception:
            observer.fail()
        response.stream = RecordingStream(response.stream, observer)
        return response

    httpx.HTTPTransport.handle_request = handle
    logging.disable(logging.CRITICAL)
    outcome = {"exit_code": 0, "requests": records}
    try:
        sys.path.insert(0, str(path.parent))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            runpy.run_path(str(path), run_name="__main__")
    except BaseException as exc:
        outcome["exit_code"] = 1
        outcome["error_type"] = type(exc).__name__
        # 固定分类，不保存厂商异常字符串（它可能包含原始请求/密钥）。
        status = getattr(exc, "status_code", None)
        if isinstance(status, int):
            outcome["http_status"] = status
    finally:
        httpx.HTTPTransport.handle_request = original
        Path(telemetry).write_text(json.dumps(outcome, ensure_ascii=False), encoding="utf-8")
    return outcome["exit_code"]


def execute_entry(entry, env, temporary, timeout):
    started = time.monotonic()
    path = ROOT / entry["path"]
    result = {**entry, "tested_at": datetime.now(timezone.utc).isoformat(), "source_sha256": file_identity(entry["path"]), "status": "failed", "execution": "real_vendor_api", "input_fixture": "synthetic_local_image_or_video_or_official_public_url"}
    missing = [name for name in entry["required_keys"] if not env.get(name)]
    if missing:
        return {**result, "status": "missing_key", "missing_key_names": missing}
    if entry["capability"] == "video_input" and entry["vendor"] == "doubao" and not env.get("VIDEO_URL"):
        return {**result, "status": "missing_input", "missing_input_names": ["VIDEO_URL"]}
    if entry["capability"] == "video_input" and entry["vendor"] == "kimi" and not env.get("VIDEO_PATH"):
        return {**result, "status": "missing_input", "missing_input_names": ["VIDEO_PATH"]}
    telemetry = temporary / (hashlib.sha256(entry["path"].encode()).hexdigest() + ".json")
    child_env = {**env, "MODEL_MANUAL_TELEMETRY": str(telemetry)}
    if path.suffix == ".py":
        command = [sys.executable, str(Path(__file__).resolve()), "--child", str(path), "--telemetry", str(telemetry)]
    elif path.suffix == ".sh":
        shim = temporary / "bin"
        shim.mkdir(exist_ok=True)
        curl = shim / "curl"
        curl.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + " " + shlex.quote(str(ROOT / "tests/live_curl.py")) + ' "$@"\n', encoding="utf-8")
        curl.chmod(0o700)
        python = shim / "python3"
        if not python.exists():
            python.symlink_to(sys.executable)
        child_env["PATH"] = str(shim) + os.pathsep + env.get("PATH", "")
        command = [shutil.which("bash") or "bash", str(path)]
    elif path.suffix == ".ts":
        if not shutil.which("node") or not (ROOT / "node_modules/openai").is_dir():
            return {**result, "status": "missing_runtime"}
        command = ["node", "--import", str(ROOT / "tests/live_fetch.mjs"), str(path)]
    else:
        return {**result, "status": "missing_runtime"}
    try:
        completed = subprocess.run(command, cwd=ROOT, env=child_env, capture_output=True, timeout=timeout)
        outcome = json.loads(telemetry.read_text()) if telemetry.is_file() else {"exit_code": completed.returncode, "requests": []}
        result.update(outcome)
        requests = outcome["requests"]
        result["status"] = determine_status(entry, outcome, completed.returncode)
        # raw subprocess stdout/stderr 永不落盘；只报告程序自身验证通过与否。
        result["evidence_scope"] = "original_file_and_real_http_metadata" if requests else "original_file_process_exit_and_its_response_checks"
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
    result["duration_seconds"] = round(time.monotonic() - started, 3)
    return result


def write_report(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 每次报告独立路径；拒绝覆盖既有证据。
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--vendor", choices=[*KEYS, "shared"])
    parser.add_argument("--file", action="append", help="精确仓库相对路径，可重复；只允许已登记的真实文件")
    parser.add_argument("--report")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--delay", type=float, default=0, help="文件间隔秒数（0–60），用于低并发/RPM账户")
    parser.add_argument("--video-url", help="Doubao 视频示例使用的获准公开 HTTPS 测试素材")
    parser.add_argument("--child", help=argparse.SUPPRESS)
    parser.add_argument("--telemetry", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        return child(Path(args.child), args.telemetry)
    if not 0 <= args.delay <= 60:
        parser.error("--delay 需在 0–60 秒之间")
    entries = [row for row in discover() if (not args.vendor or row["vendor"] == args.vendor) and (not args.file or row["path"] in args.file)]
    if not entries or args.file and set(args.file) != {row["path"] for row in entries}:
        parser.error("未收录此示例文件或厂商组合")
    if not args.execute:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return 0
    if not args.report:
        parser.error("真实执行必须指定新的 --report 路径")
    if Path(args.report).exists():
        parser.error("报告路径已存在，请使用新路径保留历史")
    env = credentials()
    report = {"schema_version": 1, "kind": "example_file_execution", "execution": "real_vendor_api", "tested_at": datetime.now(timezone.utc).isoformat(), "runtime": {"python": sys.version.split()[0], "openai": importlib.metadata.version("openai")}, "privacy": {"api_key_saved": False, "response_content_saved": False, "reasoning_content_saved": False, "raw_error_saved": False, "request_messages_saved": False}, "results": []}
    with tempfile.TemporaryDirectory(prefix="model-manual-live-") as temporary:
        directory = Path(temporary)
        env = prepare_inputs(directory, env)
        if args.video_url:
            env["VIDEO_URL"] = args.video_url
        for index, entry in enumerate(entries):
            if index and args.delay:
                time.sleep(args.delay)
            result = execute_entry(entry, env, directory, args.timeout)
            report["results"].append(result)
            print(json.dumps({"file": entry["path"], "status": result["status"], "requests": len(result.get("requests", [])), "error_type": result.get("error_type")}, ensure_ascii=False), flush=True)
    report["summary"] = {state: sum(item["status"] == state for item in report["results"]) for state in sorted(LIVE_STATUSES)}
    write_report(args.report, report)
    return 0 if all(item["status"] == "passed" for item in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
