#!/usr/bin/env python3
"""Generate standalone calls from registered model cards, not vendor parameters."""

from __future__ import annotations

import argparse
import copy
import json
import shlex
import sys
from pathlib import Path
from pprint import pformat
from typing import Any
from urllib.parse import urlparse

CATALOG = Path(__file__).resolve().parent.parent / "references" / "vendors.json"
MODEL_CARDS = CATALOG.parent / "models"
TASK_QUESTIONS = {
    "chat": "你好，请用一句话介绍你自己",
    "json": "请用一句话解释什么是 API。",
    "tool": "请调用 sum_numbers 计算 19 加 23，再告诉我结果。",
    "vision": "请描述图片中能直接看到的内容。",
}
ANSWER_SCHEMA = {
    "type": "object", "properties": {"answer": {"type": "string"}},
    "required": ["answer"], "additionalProperties": False,
}
SUM_TOOL = {
    "type": "function",
    "function": {
        "name": "sum_numbers", "description": "计算两个有限实数的和",
        "parameters": {
            "type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"], "additionalProperties": False,
        },
    },
}


def load_vendors() -> dict[str, dict[str, Any]]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))["vendors"]


def load_models() -> dict[str, dict[str, Any]]:
    cards = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(MODEL_CARDS.glob("*.json"))]
    return {card["model_id"]: card for card in cards}


def load_model(model: str, vendor: str | None = None) -> dict[str, Any]:
    cards = load_models()
    if model not in cards:
        raise ValueError(f"未收录型号 {model!r}；可用型号：{', '.join(sorted(cards))}")
    card = cards[model]
    if vendor is not None and card["vendor"] != vendor:
        raise ValueError(f"型号 {model} 属于 {card['vendor']}，不能与厂商 {vendor} 混用")
    if "generation" not in card:
        raise ValueError(f"型号 {model} 尚未登记代码生成参数")
    return card


def validate_paid_default(card: dict[str, Any]) -> None:
    """Fail closed on default selection; explicit model lookup stays separate."""
    billing = card.get("billing")
    fact = billing.get("type") if isinstance(billing, dict) else None
    sources = card.get("sources")
    source_key = fact.get("source") if isinstance(fact, dict) else None
    source = sources.get(source_key) if isinstance(sources, dict) and isinstance(source_key, str) else None
    url = source.get("url") if isinstance(source, dict) else None
    parsed = urlparse(url) if isinstance(url, str) else None
    if (
        not isinstance(fact, dict) or fact.get("value") != "paid"
        or parsed is None or parsed.scheme != "https" or not parsed.netloc
    ):
        raise ValueError(
            f"默认型号 {card.get('model_id', '<unknown>')} 必须明确登记为付费"
            "（billing.type.value=paid）并关联有效的官方计费来源；拒绝生成，不会自动换型号"
        )


def _resolve_card(cfg: dict[str, Any], model: str) -> dict[str, Any]:
    # Compatibility: existing callers may pass a vendor cfg. It selects identity
    # only; it cannot override the model card's connection or request parameters.
    vendor = cfg.get("vendor")
    if vendor is None and cfg.get("default_model"):
        vendor = load_model(cfg["default_model"])["vendor"]
    return load_model(model, vendor)


def _fact(config: dict[str, Any], field: str) -> Any:
    return config[field]["value"]


def _supported(card: dict[str, Any], capability: str) -> bool:
    state = card.get("capabilities", {}).get(capability, {}).get("status", "unknown")
    return state in {"verified", "documented", "rate_limited_during_verification"}


def build_request(
    card: dict[str, Any], question: str, stream: bool = False,
    thinking: str = "default", max_tokens: int | None = None,
    task: str = "chat", image_url: str | None = None,
) -> dict[str, Any]:
    """Build an HTTP body; Python-specific extra_body placement comes later."""
    if task not in TASK_QUESTIONS:
        raise ValueError(f"不支持的任务 {task}")
    if thinking not in {"default", "on", "off"}:
        raise ValueError(f"不支持的思考模式 {thinking}")
    if image_url is not None and task != "vision":
        raise ValueError("--image-url 仅用于 --task vision")
    if not _supported(card, "chat_completions"):
        raise ValueError(f"{card['model_id']} 未登记 Chat Completions 能力")
    generation = card["generation"]
    body: dict[str, Any] = {
        **copy.deepcopy(generation.get("request_defaults", {}).get("value", {})),
        "model": card["model_id"], "messages": [{"role": "user", "content": question}],
    }
    if thinking != "default":
        toggle = generation.get("thinking", {}).get(thinking)
        if not toggle or not _supported(card, "thinking"):
            raise ValueError(f"{card['model_id']} 未登记思考 {thinking} 的参数")
        body.update(copy.deepcopy(toggle["value"]))
    if max_tokens is not None:
        budget = generation.get("token_budget")
        if not budget:
            raise ValueError(f"{card['model_id']} 未登记输出预算参数")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < _fact(budget, "min"):
            raise ValueError("--max-tokens 必须是正整数")
        if "max" in budget and max_tokens > _fact(budget, "max"):
            raise ValueError(f"{card['model_id']} 的 {_fact(budget, 'parameter')} 不能超过 {_fact(budget, 'max')}")
        body[_fact(budget, "parameter")] = max_tokens
    if stream:
        if not _supported(card, "streaming"):
            raise ValueError(f"{card['model_id']} 未登记流式能力")
        if task == "tool":
            raise ValueError("工具闭环示例暂不支持 --stream；工具参数需完整接收后再校验")
        body["stream"] = True
        if "stream_options" in generation:
            body["stream_options"] = copy.deepcopy(_fact(generation, "stream_options"))
    if task == "json":
        config = generation.get("json_output")
        if not config or not _supported(card, config["capability"]):
            raise ValueError(f"{card['model_id']} 未登记 JSON 输出能力")
        if config.get("requires_thinking_off", {}).get("value") and thinking != "off":
            raise ValueError(f"{card['model_id']} 的 JSON 任务需显式设置 --thinking off，参见模型卡片官方来源")
        response_format = copy.deepcopy(_fact(config, "response_format"))
        if response_format["type"] == "json_schema":
            response_format["json_schema"] = {"name": "answer", "strict": True, "schema": ANSWER_SCHEMA}
        body["response_format"] = response_format
        body["messages"].insert(0, {"role": "system", "content": "只输出 JSON 对象，包含且仅包含字符串字段 answer。"})
    elif task == "tool":
        if not _supported(card, "tool_calling"):
            raise ValueError(f"{card['model_id']} 未登记工具调用能力")
        body["tools"] = [copy.deepcopy(SUM_TOOL)]
        if "tool_choice" in generation:
            body["tool_choice"] = _fact(generation, "tool_choice")
    elif task == "vision":
        if not _supported(card, "vision"):
            raise ValueError(f"{card['model_id']} 未登记图片输入能力，请选择已收录的视觉型号")
        parsed = urlparse(image_url or "")
        input_kind = None
        if image_url:
            if parsed.scheme in {"https", "http"} and parsed.netloc:
                input_kind = "http_url"
            elif image_url.startswith("data:image/") and ";base64," in image_url:
                input_kind = "base64_data_url"
            elif parsed.scheme == "ms" and parsed.netloc:
                input_kind = "ms_file_id"
        allowed_inputs = generation.get("image_input", {}).get("value", ["http_url", "base64_data_url"])
        if input_kind not in allowed_inputs:
            descriptions = {
                "http_url": "HTTP(S) 图片地址",
                "base64_data_url": "data:image/...;base64,...",
                "ms_file_id": "ms://<file_id>",
            }
            allowed_description = "、".join(descriptions[item] for item in allowed_inputs)
            raise ValueError(f"{card['model_id']} 的 --image-url 只接受：{allowed_description}；请遵循该型号图片输入限制")
        body["messages"][0]["content"] = [
            {"type": "text", "text": question}, {"type": "image_url", "image_url": {"url": image_url}},
        ]
    return body


def _python_body(card: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(body)
    extra = {}
    for key in _fact(card["generation"], "python_extra_body_fields"):
        if key in result:
            extra[key] = result.pop(key)
    if extra:
        result["extra_body"] = extra
    return result


PYTHON_RESULT_HELPERS = '''def check_provider_status(response):
    base = getattr(response, "base_resp", None)
    if base is not None:
        code = base.get("status_code") if isinstance(base, dict) else getattr(base, "status_code", None)
        if isinstance(code, bool) or not isinstance(code, int) or code != 0:
            raise RuntimeError("服务端 base_resp 未报告成功；不要将 HTTP 200 当成业务成功")


def report_usage(usage):
    data = usage.model_dump(exclude_none=True) if hasattr(usage, "model_dump") else usage
    print("usage=" + json.dumps(data, ensure_ascii=False, default=str), file=sys.stderr)


def checked_message(response, allow_tools=False):
    check_provider_status(response)
    report_usage(getattr(response, "usage", None))
    choices = getattr(response, "choices", None) or []
    if not choices:
        raise RuntimeError("响应没有 choices，不能作为成功答案")
    choice = choices[0]
    reason = getattr(choice, "finish_reason", None)
    if reason == "length":
        raise RuntimeError("输出被截断（finish_reason=length）；调整预算并重新生成完整答案")
    message = getattr(choice, "message", None)
    calls = getattr(message, "tool_calls", None) or []
    if allow_tools and reason == "tool_calls" and calls:
        return message
    if reason != "stop" or calls:
        raise RuntimeError(f"响应未正常结束：finish_reason={reason!r}")
    text = getattr(message, "content", None)
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("最终答案为空；检查思考预算和响应状态")
    return message


def checked_stream(response, echo=True):
    parts = []
    finish_reason = None
    usage = None
    try:
        for chunk in response:
            check_provider_status(chunk)
            if getattr(chunk, "usage", None) is not None:
                usage = chunk.usage
            choices = getattr(chunk, "choices", None) or []
            if not choices:  # usage-only 块也必须先记录 usage
                continue
            choice = choices[0]
            reason = getattr(choice, "finish_reason", None)
            delta = getattr(choice, "delta", None)
            text = getattr(delta, "content", None)
            if getattr(delta, "tool_calls", None) or getattr(delta, "function_call", None):
                raise RuntimeError("收到未处理的工具 delta；不能作为正文答案")
            if finish_reason is not None and (reason is not None or text):
                raise RuntimeError("结束后又收到正文或结束信号；流式响应不一致")
            if reason is not None:
                finish_reason = reason
            if text:
                if not isinstance(text, str):
                    raise RuntimeError("非文本 delta.content")
                parts.append(text)
                if echo:
                    print(text, end="", flush=True)
    finally:
        if echo:
            print()
        report_usage(usage)  # 中断时可能没有 usage，不能把 None 当零消耗
        close = getattr(response, "close", None)
        if callable(close):
            close()
    if finish_reason == "length":
        raise RuntimeError("输出被截断（finish_reason=length）；已打印内容只是未完成的片段")
    if finish_reason != "stop":
        raise RuntimeError(f"流式响应未正常结束：finish_reason={finish_reason!r}")
    text = "".join(parts)
    if not text.strip():
        raise RuntimeError("流式最终答案为空；检查思考预算和响应状态")
    return text
'''

PYTHON_TOOL_LOOP = '''def validate_tool(call):
    if call.type != "function" or call.function.name != "sum_numbers":
        raise ValueError("模型请求了未允许的工具")
    args = json.loads(call.function.arguments)
    if not isinstance(args, dict) or set(args) != {"a", "b"}:
        raise ValueError("工具参数必须且只能包含 a、b")
    for number in args.values():
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise ValueError("a、b 必须是有限实数")
    return args


def execute_tool(call, args=None):
    args = validate_tool(call) if args is None else args
    result = args["a"] + args["b"]
    if not math.isfinite(result):
        raise ValueError("相加结果溢出")
    return json.dumps({"result": result}, ensure_ascii=False, allow_nan=False)


seen_tool_ids = set()
executed_tool_count = 0
for _ in range(4):  # 项目示例上限：防止无限工具循环
    response = client.chat.completions.create(**request)
    message = checked_message(response, allow_tools=True)
    calls = getattr(message, "tool_calls", None) or []
    if not calls:
        if executed_tool_count == 0:
            raise RuntimeError("模型直接回答，尚未实际执行工具；本次未完成工具闭环示例")
        print(message.content)
        break
    ids = [call.id for call in calls]
    if (any(not isinstance(call_id, str) or not call_id for call_id in ids)
            or len(set(ids)) != len(ids) or seen_tool_ids.intersection(ids)):
        raise ValueError("工具调用 id 缺失或重复")
    arguments = [validate_tool(call) for call in calls]  # 先校验整批，再执行
    results = [execute_tool(call, args) for call, args in zip(calls, arguments)]
    executed_tool_count += len(results)
    seen_tool_ids.update(ids)
    # 保留 reasoning_content 等模型扩展字段，回传完整 assistant 消息。
    request["messages"].append(message.model_dump(exclude_none=True))
    for call, result in zip(calls, results):
        request["messages"].append({"role": "tool", "tool_call_id": call.id, "content": result})
else:
    raise RuntimeError("工具调用达到 4 轮，尚未得到最终答案")
'''


def _budget_comment(card: dict[str, Any], max_tokens: int | None, language: str) -> str:
    prefix = "#" if language in {"python", "curl"} else "//"
    budget = card["generation"].get("token_budget")
    semantics = _fact(budget, "semantics") if budget else "unknown"
    labels = {
        "thinking_and_answer": "包含思考与正文；小预算可能只有思考而没有最终答案",
        "answer_only": "只限制正文，思考 token 不计入此参数",
        "unknown": "思考是否计入预算尚未在该型号来源中确认；不要视为正文长度保证",
    }
    note = labels[semantics]
    if max_tokens is None:
        note += "；未显式设置，使用服务端默认值"
    return f"{prefix} 输出预算：{note}。\n"


def python_snippet(
    cfg: dict[str, Any], model: str, question: str, stream: bool, thinking: str,
    max_tokens: int | None = None, task: str = "chat", image_url: str | None = None,
) -> str:
    card = _resolve_card(cfg, model)
    generation = card["generation"]
    body = _python_body(card, build_request(card, question, stream, thinking, max_tokens, task, image_url))
    if task == "tool":
        result = PYTHON_TOOL_LOOP
    elif stream:
        result = "response = client.chat.completions.create(**request)\n" + (
            "text = checked_stream(response, echo=False)  # JSON 收完整并校验后再发布\n" if task == "json"
            else "text = checked_stream(response)\n"
        )
    else:
        result = "response = client.chat.completions.create(**request)\ntext = checked_message(response).content\n"
    if task == "json":
        result += '''data = json.loads(text)
if not isinstance(data, dict) or set(data) != {"answer"} or not isinstance(data["answer"], str):
    raise ValueError("JSON 不符合业务要求：仅接受字符串字段 answer")
print(json.dumps(data, ensure_ascii=False))
'''
    elif task != "tool" and not stream:
        result += "print(text)\n"
    return f'''import json
import math
import os
import sys
from openai import OpenAI

{_budget_comment(card, max_tokens, "python")}client = OpenAI(
    api_key=os.environ[{_fact(generation, "key_env")!r}],
    base_url={_fact(generation, "base_url")!r},
    timeout=120,
    max_retries=0,  # 项目约定：由调用方决定是否重试及重试次数
)

{PYTHON_RESULT_HELPERS}
request = {pformat(body, width=88, sort_dicts=False)}

{result}'''


TYPESCRIPT_RESULT_HELPERS = '''function reportUsage(usage: unknown) {
  console.error("usage=" + JSON.stringify(usage ?? null));
}

function checkProviderStatus(response: any) {
  if (response.base_resp != null && response.base_resp.status_code !== 0) {
    throw new Error("服务端 base_resp 未报告成功；不要将 HTTP 200 当成业务成功");
  }
}

function checkedMessage(response: any): string {
  checkProviderStatus(response);
  reportUsage(response.usage);
  const choice = response.choices?.[0];
  if (!choice) throw new Error("响应没有 choices，不能作为成功答案");
  if (choice.finish_reason === "length") throw new Error("输出被截断（finish_reason=length）");
  if (choice.finish_reason !== "stop" || choice.message?.tool_calls?.length) {
    throw new Error(`响应未正常结束：finish_reason=${choice.finish_reason}`);
  }
  const text = choice.message?.content;
  if (typeof text !== "string" || !text.trim()) throw new Error("最终答案为空；检查思考预算");
  return text;
}

async function checkedStream(response: any, echo = true): Promise<string> {
  const parts: string[] = [];
  let finishReason: string | null = null;
  let usage: unknown = null;
  try {
    for await (const chunk of response) {
      checkProviderStatus(chunk);
      if (chunk.usage != null) usage = chunk.usage;
      const choice = chunk.choices?.[0];
      if (!choice) continue;
      const text = choice.delta?.content;
      if (choice.delta?.tool_calls?.length || choice.delta?.function_call) {
        throw new Error("收到未处理的工具 delta；不能作为正文答案");
      }
      if (finishReason !== null && (choice.finish_reason != null || text)) {
        throw new Error("结束后又收到正文或结束信号；流式响应不一致");
      }
      if (choice.finish_reason != null) finishReason = choice.finish_reason;
      if (text) {
        if (typeof text !== "string") throw new Error("非文本 delta.content");
        parts.push(text);
        if (echo) process.stdout.write(text);
      }
    }
  } finally {
    if (echo) process.stdout.write("\\n");
    reportUsage(usage); // 中断时 usage 可能缺失；不能当作零消耗
    response.controller?.abort();
  }
  if (finishReason === "length") throw new Error("输出被截断；已打印内容只是未完成的片段");
  if (finishReason !== "stop") throw new Error(`流式响应未正常结束：finish_reason=${finishReason}`);
  const text = parts.join("");
  if (!text.trim()) throw new Error("流式最终答案为空；检查思考预算");
  return text;
}
'''


def _check_language_task(language: str, task: str) -> None:
    if language != "python" and task in {"tool", "vision"}:
        raise ValueError(f"{task} 的完整任务示例暂仅支持 Python；请选择 --language python")


def typescript_snippet(
    cfg: dict[str, Any], model: str, question: str, stream: bool, thinking: str,
    max_tokens: int | None = None, task: str = "chat", image_url: str | None = None,
) -> str:
    _check_language_task("typescript", task)
    card = _resolve_card(cfg, model)
    generation = card["generation"]
    body = build_request(card, question, stream, thinking, max_tokens, task, image_url)
    if stream:
        call = "const response = await client.chat.completions.create(request as any);\n" + (
            "const text = await checkedStream(response, false); // JSON 校验后再发布\n" if task == "json"
            else "const text = await checkedStream(response);\n"
        )
    else:
        call = "const response = await client.chat.completions.create(request as any);\nconst text = checkedMessage(response);\n"
    if task == "json":
        call += '''const data: unknown = JSON.parse(text);
if (typeof data !== "object" || data === null || Array.isArray(data) ||
    Object.keys(data).length !== 1 || typeof (data as any).answer !== "string") {
  throw new Error("JSON 不符合业务要求：仅接受字符串字段 answer");
}
console.log(JSON.stringify(data));
'''
    elif not stream:
        call += "console.log(text);\n"
    env_name = _fact(generation, "key_env")
    return f'''import OpenAI from "openai";

{_budget_comment(card, max_tokens, "typescript")}const apiKey = process.env.{env_name};
if (!apiKey) throw new Error("请先设置 {env_name}");
const client = new OpenAI({{
  apiKey,
  baseURL: {json.dumps(_fact(generation, "base_url"), ensure_ascii=False)},
  timeout: 120_000,
  maxRetries: 0, // 项目约定：由调用方决定是否重试
}});

{TYPESCRIPT_RESULT_HELPERS}
const request: Record<string, unknown> = {json.dumps(body, ensure_ascii=False, indent=2)};
{call}'''


def curl_snippet(
    cfg: dict[str, Any], model: str, question: str, stream: bool, thinking: str,
    max_tokens: int | None = None, task: str = "chat", image_url: str | None = None,
) -> str:
    _check_language_task("curl", task)
    card = _resolve_card(cfg, model)
    generation = card["generation"]
    body = build_request(card, question, stream, thinking, max_tokens, task, image_url)
    payload = json.dumps(body, ensure_ascii=False, indent=2)
    delimiter = "MODEL_MANUAL_JSON"
    while delimiter in payload.splitlines():
        delimiter += "_END"
    endpoint = _fact(generation, "base_url").rstrip("/") + "/chat/completions"
    buffering = " --no-buffer" if stream else ""
    return f'''{_budget_comment(card, max_tokens, "curl")}# curl 展示原始响应；使用结果前检查 finish_reason、正文完整性及 usage。
: "${{{_fact(generation, "key_env")}:?请先设置 {_fact(generation, "key_env")}}}"
curl --fail-with-body{buffering} {shlex.quote(endpoint)} \\
  -H "Authorization: Bearer ${{{_fact(generation, "key_env")}}}" \\
  -H "Content-Type: application/json" \\
  --data-binary @- <<'{delimiter}'
{payload}
{delimiter}
'''


def main() -> None:
    vendors = load_vendors()
    parser = argparse.ArgumentParser(description="按已收录型号生成独立可运行的调用代码")
    parser.add_argument("--vendor", choices=sorted(vendors), required=True)
    parser.add_argument("--language", choices=("python", "typescript", "curl"), default="python")
    parser.add_argument("--model", help="已收录的模型 ID；默认使用厂商目录指定的型号")
    parser.add_argument("--task", choices=tuple(TASK_QUESTIONS), default="chat")
    parser.add_argument("--question", help="任务问题；不填时使用对应任务示例")
    parser.add_argument("--image-url", help="vision 图片输入，按型号限制；Kimi 只接受 base64 data URL 或 ms:// 文件引用")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--thinking", choices=("default", "on", "off"), default="default")
    parser.add_argument("--max-tokens", type=int, help="按型号卡片语义设置输出预算；未指定时使用服务端默认值")
    args = parser.parse_args()
    model = args.model if args.model is not None else vendors[args.vendor]["default_model"]
    generators = {"python": python_snippet, "typescript": typescript_snippet, "curl": curl_snippet}
    try:
        card = load_model(model, args.vendor)
        if args.model is None:
            validate_paid_default(card)
        source = generators[args.language](card, model, args.question or TASK_QUESTIONS[args.task], args.stream,
                                           args.thinking, args.max_tokens, args.task, args.image_url)
    except ValueError as exc:
        parser.error(str(exc))
    lifecycle = card.get("identity", {}).get("lifecycle", {}).get("value")
    if "lifecycle_warning" in card["generation"]:
        print("提醒：" + _fact(card["generation"], "lifecycle_warning"), file=sys.stderr)
    if lifecycle == "past_but_callable":
        print(f"提醒：{model} 属于官方往期模型；调用前复核模型列表与可用状态。", file=sys.stderr)
    if args.max_tokens is not None and _fact(card["generation"]["token_budget"], "semantics") == "unknown":
        print(f"提醒：{model} 尚未确认思考是否计入输出预算；请同时监控 finish_reason 和 usage。", file=sys.stderr)
    print(source, end="")


if __name__ == "__main__":
    main()
