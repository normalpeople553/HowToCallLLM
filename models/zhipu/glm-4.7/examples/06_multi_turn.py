"""付费 glm-4.7 两轮文本对话；客户端逐轮发送完整、已验证的历史。
官方型号：https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7
接口：https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
max_tokens=4096是本地示例选择，不是上下文大小。
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


def main():
    client = make_client()
    messages = [{"role": "system", "content": "回答简洁，只根据本次传入的对话回答。"}]
    questions = ["我报名了周六上午的 Python 入门课，请记住这个信息。", "我报名的是什么课、什么时候上课？"]
    for question in questions:
        messages.append({"role": "user", "content": question})
        response = create_with_backoff(
            client, model="glm-4.7", messages=messages,
            extra_body={"thinking": {"type": "disabled"}}, max_tokens=4096,
        )
        message = completed_message(response)
        print_usage(response)
        messages.append(message.model_dump(exclude_none=True))
        print(message.content)
    return messages


if __name__ == "__main__":
    main()
