"""付费 glm-4.7 非思考工具闭环；天气是本地固定模拟，非实时数据。
官方型号：https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7
消息协议：https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
最多六次逻辑模型调用；每个HTTP请求最多三次限流尝试。
只重试模型请求，不包裹本地工具执行；整批参数验证后才执行模拟工具。
"""

import json
import math
import os
import random
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from openai import OpenAI


def make_client():
    """SDK settings, not model parameters; disable nested SDK retries."""
    return OpenAI(
        api_key=os.environ["ZHIPU_API_KEY"],
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        timeout=120, max_retries=0,
    )


def create_with_backoff(client, **request):
    """Retry only a model HTTP request, never a local tool or consumed stream.

    Official codes: 1302 = rate limit, 1305 = overload. Other 429 codes
    can mean billing, entitlement or quota errors and are not retried here.
    https://docs.bigmodel.cn/cn/api/api-code
    SDK max_retries=0: https://developers.openai.com/api/reference/python#retries
    Three attempts, 1s/2s exponential delays plus <=0.25s jitter are local policy.
    """
    for attempt in range(3):
        try:
            return client.chat.completions.create(**request)
        except Exception as error:
            body = getattr(error, "body", None)
            payload = body.get("error", body) if isinstance(body, dict) else {}
            code = str(payload.get("code", "")) if isinstance(payload, dict) else ""
            if getattr(error, "status_code", None) != 429 or code not in {"1302", "1305"}:
                raise RuntimeError("API 请求失败；请在安全环境检查状态、权限、余额和参数，勿公开原始错误。") from None
            if attempt == 2:
                raise RuntimeError("1302/1305 限流在三次请求后仍未恢复；停止调用。") from None
            delay = 2 ** attempt + random.uniform(0, 0.25)
            headers = getattr(getattr(error, "response", None), "headers", {}) or {}
            retry_after = headers.get("retry-after")
            if retry_after is not None:
                try:
                    wait = float(retry_after)
                except (TypeError, ValueError):
                    try:
                        date = parsedate_to_datetime(retry_after)
                        if date.tzinfo is None:
                            date = date.replace(tzinfo=timezone.utc)
                        wait = (date - datetime.now(timezone.utc)).total_seconds()
                    except (TypeError, ValueError, OverflowError):
                        wait = 0
                if math.isfinite(wait) and wait >= 0:
                    if wait > 30:
                        raise RuntimeError("Retry-After 超过本例30秒等待上限；请稍后重新运行。") from None
                    delay = max(delay, wait)
            time.sleep(delay)
    raise RuntimeError("已达到请求尝试上限")


def completed_message(response):
    choices = getattr(response, "choices", None) or []
    if len(choices) != 1:
        raise RuntimeError("需要且只能有一个候选回答")
    choice = choices[0]
    message = choice.message
    if choice.finish_reason != "stop" or getattr(message, "tool_calls", None):
        raise RuntimeError("回答未正常结束或含未处理工具调用；不要当作完整结果。")
    if not isinstance(message.content, str) or not message.content.strip():
        raise RuntimeError("没有最终正文；请检查思考、生成预算与提示词。")
    return message


def print_usage(response):
    """Print only documented numeric token counts, not arbitrary provider fields."""
    usage = getattr(response, "usage", None)
    stats = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
        if isinstance(value, int) and not isinstance(value, bool):
            stats[name] = value
    print("usage=" + json.dumps(stats, ensure_ascii=False), file=sys.stderr)


TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "取得城市的固定教学模拟天气，不提供实时天气",
        "parameters": {
            "type": "object", "properties": {"city": {"type": "string"}},
            "required": ["city"], "additionalProperties": False,
        },
    },
}]


def get_weather(city):
    return json.dumps(
        {"city": city, "weather": "晴", "simulated": True, "notice": "教学模拟，不是实时天气"},
        ensure_ascii=False,
    )


def validate_call(call, seen_ids):
    function = getattr(call, "function", None)
    if getattr(call, "type", None) != "function" or getattr(function, "name", None) != "get_weather":
        raise ValueError("未登记的工具")
    call_id = getattr(call, "id", None)
    if not isinstance(call_id, str) or not call_id or call_id in seen_ids:
        raise ValueError("工具调用ID缺失或重复")
    args = json.loads(function.arguments)
    if not isinstance(args, dict) or set(args) != {"city"}:
        raise ValueError("参数必须且只能包含city")
    city = args["city"]
    if not isinstance(city, str) or not city.strip() or len(city) > 80 or any(ord(x) < 32 for x in city):
        raise ValueError("city需要1至80字符的非空文本且不能含控制字符")
    seen_ids.add(call_id)
    return call_id, city.strip()


def main():
    client = make_client()
    messages = [
        {"role": "system", "content": "天气必须使用get_weather查询；明确说明结果是教学模拟数据。"},
        {"role": "user", "content": "杭州天气如何？"},
    ]
    seen_ids = set()
    executed_call_count = 0
    for turn in range(6):
        # Only this request is retried; already-completed local tools are never replayed.
        response = create_with_backoff(
            client, model="glm-4.7", messages=messages, tools=TOOLS,
            extra_body={"thinking": {"type": "disabled"}},
        )
        print_usage(response)
        choices = getattr(response, "choices", None) or []
        if len(choices) != 1:
            raise RuntimeError("需要且只能有一个候选")
        choice = choices[0]
        message = choice.message
        calls = getattr(message, "tool_calls", None) or []
        if calls:
            if choice.finish_reason != "tool_calls":
                raise RuntimeError("工具参数未正常结束；未执行工具")
            if turn == 5:
                raise RuntimeError("已到模型调用上限，不执行无法回传的工具")
            batch_ids = set(seen_ids)
            planned = [validate_call(call, batch_ids) for call in calls]
            # Full assistant preserves any reasoning/provider extension fields.
            messages.append(message.model_dump(exclude_none=True))
            seen_ids = batch_ids
            for call_id, city in planned:
                result = get_weather(city)
                executed_call_count += 1
                messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
            continue
        message = completed_message(response)
        if executed_call_count == 0:
            raise RuntimeError("模型未实际调用工具，未完成工具闭环")
        print(message.content)
        return messages
    raise RuntimeError("已达到模型调用次数上限")


if __name__ == "__main__":
    main()
