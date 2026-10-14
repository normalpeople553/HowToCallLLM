"""付费 glm-4.7 流式输出；关闭思考，检查结束并始终关闭流。
官方型号：https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7
接口：https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
仅重试建立流前的限流；迭代中断后不重放，已展示的内容可能不完整。
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
    stream = create_with_backoff(
        client, model="glm-4.7",
        messages=[{"role": "user", "content": "用三句话解释上下文窗口"}],
        stream=True, extra_body={"thinking": {"type": "disabled"}},
    )
    parts = []
    finish_reason = None
    last_usage = None
    try:
        for chunk in stream:
            if getattr(chunk, "usage", None) is not None:
                last_usage = chunk.usage
            choices = getattr(chunk, "choices", None) or []
            if not choices:  # Tolerate empty choices / usage-only chunks.
                continue
            if len(choices) != 1:
                raise RuntimeError("流出现多个候选")
            choice = choices[0]
            delta = choice.delta
            if getattr(delta, "tool_calls", None):
                raise RuntimeError("本流式示例未实现工具delta")
            content = getattr(delta, "content", None)
            if content is not None and not isinstance(content, str):
                raise RuntimeError("流式正文不是文本")
            if finish_reason is not None and (content or choice.finish_reason is not None):
                raise RuntimeError("结束后出现正文或重复结束状态")
            if content:
                parts.append(content)
                print(content, end="", flush=True)
            if choice.finish_reason is not None:
                finish_reason = choice.finish_reason
        if finish_reason != "stop" or not "".join(parts).strip():
            raise RuntimeError("流未正常结束或没有最终正文")
    except Exception:
        raise RuntimeError("流式输出未完成；已显示的片段不可当作完整回答，且不会自动重放。") from None
    finally:
        # Both success and failure release the response; no retry after consuming data.
        try:
            stream.close()
        except Exception:
            raise RuntimeError("关闭流失败；本次结果不能标为完整通过。") from None
    print()
    if last_usage is not None:
        class UsageResult:
            usage = last_usage
        print_usage(UsageResult())
    return "".join(parts)


if __name__ == "__main__":
    main()
