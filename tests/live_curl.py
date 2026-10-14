"""Observe the two checked-in non-streaming cURL examples without replacing responses.

The runner installs a PATH shim which executes this file with curl's original args.
The actual transport is always /usr/bin/curl (never a PATH lookup). It forwards the
original stdin/arguments, adding only --disable (ignore user curlrc) and a random
write-out marker. Stdout is the original response bytes after stripping that marker.
Only allowlisted numeric/enumerated metadata is written to MODEL_MANUAL_TELEMETRY.
"""

import json
import math
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys


CURL = "/usr/bin/curl"
OFFICIAL_ENDPOINTS = frozenset({
    "https://api.deepseek.com/chat/completions",
    "https://api.minimax.cn/v1/text/chatcompletion_v2",
})
MODELS = frozenset({
    "deepseek-flash", "DeepSeek-V4.1-Flash", "deepseek-v4.1-flash",
    "deepseek-v4-flash", "MiniMax-M2.7",
})
FINISH_REASONS = frozenset({
    "stop", "length", "tool_calls", "content_filter", "aborted",
    "insufficient_system_resource",
})
MAX_JSON_BYTES = 8 * 1024 * 1024


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 2**53 - 1


def safe_parameters(payload):
    result = {}
    for name in ("stream", "reasoning_split", "enable_thinking"):
        if isinstance(payload.get(name), bool):
            result[name] = payload[name]
    for name in ("max_tokens", "max_completion_tokens", "max_output_tokens"):
        if integer(payload.get(name)):
            result[name] = payload[name]
    for name in ("temperature", "top_p"):
        value = payload.get(name)
        if (integer(value) or isinstance(value, float) and math.isfinite(value)):
            result[name] = value
    effort = payload.get("reasoning_effort")
    if isinstance(effort, str) and effort in {"none", "low", "medium", "high", "max", "xhigh"}:
        result["reasoning_effort"] = effort
    choice = payload.get("tool_choice")
    if isinstance(choice, str) and choice in {"none", "auto", "required"}:
        result["tool_choice"] = choice
    elif isinstance(choice, dict):
        result["tool_choice"] = "named_function"
    thinking = payload.get("thinking")
    if isinstance(thinking, dict):
        result["thinking"] = {
            name: value for name, value in thinking.items()
            if name in {"type", "keep"} and isinstance(value, str)
            and value in {"enabled", "disabled", "adaptive", "all", "none"}
        }
    options = payload.get("stream_options")
    if isinstance(options, dict) and isinstance(options.get("include_usage"), bool):
        result["stream_options"] = {"include_usage": options["include_usage"]}
    reasoning = payload.get("reasoning")
    if isinstance(reasoning, dict) and isinstance(reasoning.get("effort"), str) and reasoning["effort"] in {"none", "low", "medium", "high", "max", "xhigh"}:
        result["reasoning"] = {"effort": reasoning["effort"]}
    output_format = payload.get("response_format")
    if isinstance(output_format, dict) and isinstance(output_format.get("type"), str) and output_format["type"] in {"text", "json_object", "json_schema"}:
        result["response_format"] = {"type": output_format["type"]}
    return result


def observe_json(record, data):
    if not isinstance(data, dict):
        return
    model = data.get("model")
    if isinstance(model, str) and model in MODELS:
        record["served_model"] = model
    base = data.get("base_resp")
    if isinstance(base, dict) and integer(base.get("status_code")):
        record["business_status"] = base["status_code"]
    usage = data.get("usage")
    if isinstance(usage, dict):
        result = {
            name: usage[name] for name in ("prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens")
            if integer(usage.get(name))
        }
        for name, field in (
            ("prompt_tokens_details", "cached_tokens"),
            ("completion_tokens_details", "reasoning_tokens"),
            ("input_tokens_details", "cached_tokens"),
            ("output_tokens_details", "reasoning_tokens"),
        ):
            detail = usage.get(name)
            if isinstance(detail, dict) and integer(detail.get(field)):
                result[name] = {field: detail[field]}
        record["usage"] = result
    choices = data.get("choices")
    for choice in choices if isinstance(choices, list) else []:
        if not isinstance(choice, dict):
            continue
        reason = choice.get("finish_reason")
        if isinstance(reason, str) and reason in FINISH_REASONS:
            record.setdefault("finish_reasons", []).append(reason)
        message = choice.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str):
            record["content_chars"] = record.get("content_chars", 0) + len(content)
        if isinstance(message.get("tool_calls"), list) and message["tool_calls"]:
            record["has_tool_calls"] = True


def validate_args(args, endpoints=OFFICIAL_ENDPOINTS):
    """Only existing shell flags are accepted; no config, redirection or extra URL."""
    endpoint = None
    has_stdin = False
    index = 0
    while index < len(args):
        argument = args[index]
        if argument in {"--silent", "--show-error", "--fail"}:
            index += 1
            continue
        if argument in {"-H", "--header", "--max-time", "--data-binary"}:
            if index + 1 >= len(args):
                raise ValueError("unsupported_curl_arguments")
            value = args[index + 1]
            if argument in {"-H", "--header"}:
                name, separator, content = value.partition(":")
                if not separator or name.lower() not in {"authorization", "content-type"} or "\r" in value or "\n" in value:
                    raise ValueError("unsupported_curl_arguments")
                if name.lower() == "content-type" and content.strip().lower() != "application/json":
                    raise ValueError("unsupported_curl_arguments")
            elif argument == "--max-time":
                if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value) or not 0 < float(value) <= 3600:
                    raise ValueError("unsupported_curl_arguments")
            else:
                if value != "@-" or has_stdin:
                    raise ValueError("unsupported_curl_arguments")
                has_stdin = True
            index += 2
            continue
        if argument in endpoints and endpoint is None:
            endpoint = argument
            index += 1
            continue
        raise ValueError("example_endpoint_or_curl_option_not_allowlisted")
    if not endpoint or not has_stdin:
        raise ValueError("unsupported_curl_arguments")
    return endpoint


def write_telemetry(path, outcome):
    if not path:
        return
    try:
        descriptor = os.open(Path(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(outcome, handle, ensure_ascii=False, allow_nan=False)
    except (OSError, ValueError, TypeError):
        # No raw filesystem error or user-provided path may escape this observer.
        pass


def run(args, stdin, telemetry_path=None, *, endpoints=OFFICIAL_ENDPOINTS):
    """Tests may explicitly allow a loopback server, but main always uses official URLs."""
    outcome = {"exit_code": 2, "requests": []}
    try:
        endpoint = validate_args(args, endpoints)
        if len(stdin) > MAX_JSON_BYTES:
            raise ValueError("unsupported_observation_request_body")
        payload = json.loads(stdin)
        if not isinstance(payload, dict) or payload.get("stream") is True:
            raise ValueError("observer_requires_nonstream_json")
    except (ValueError, TypeError, UnicodeError):
        write_telemetry(telemetry_path, outcome)
        sys.stderr.write("curl_observer_rejected_request\n")
        return 2
    record = {"method": "POST", "endpoint": endpoint, "transport": "real_curl", "parameters": safe_parameters(payload)}
    model = payload.get("model")
    if isinstance(model, str) and model in MODELS:
        record["requested_model"] = model
    outcome["requests"].append(record)
    marker = "\n__MODEL_MANUAL_CURL_" + secrets.token_hex(24) + "__"
    try:
        # --disable must be first: a user's curlrc must not add unseen URLs or outputs.
        completed = subprocess.run(
            [CURL, "--disable", *args, "--write-out", marker + "%{http_code}"],
            input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
    except OSError:
        outcome["exit_code"] = 127
        record["observation_status"] = "curl_unavailable"
        write_telemetry(telemetry_path, outcome)
        sys.stderr.write("curl_exit_code=127\n")
        return 127
    code = completed.returncode if completed.returncode >= 0 else 128 - completed.returncode
    outcome["exit_code"] = code
    body, found, status = completed.stdout.rpartition(marker.encode("ascii"))
    if not found or not re.fullmatch(rb"[0-9]{3}", status):
        body = completed.stdout
        record["observation_status"] = "missing_status_marker"
    else:
        http_status = int(status)
        if 100 <= http_status <= 599:
            record["http_status"] = http_status
        if len(body) <= MAX_JSON_BYTES:
            try:
                observe_json(record, json.loads(body))
                record["observation_status"] = "json_observed"
            except (ValueError, TypeError, UnicodeError):
                record["observation_status"] = "invalid_json"
        else:
            record["observation_status"] = "response_too_large"
    write_telemetry(telemetry_path, outcome)
    # Preserve exactly the bytes curl would have emitted; never print raw curl stderr.
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()
    if code:
        sys.stderr.write(f"curl_exit_code={code}\n")
    return code


def main():
    return run(sys.argv[1:], sys.stdin.buffer.read(), os.environ.get("MODEL_MANUAL_TELEMETRY"))


if __name__ == "__main__":
    raise SystemExit(main())
