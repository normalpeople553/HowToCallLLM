# Zhipu GLM calling code and human review

[All worked examples](README.en.md) · [中文](zhipu.md)

`glm-4.7` · [Model manual](../../models/zhipu/glm-4.7/README.en.md) · [Parameter reference](../../models/zhipu/glm-4.7/parameters.en.md)

## Run the complete example

Set the following environment variable locally, after preparing the [locked environment](../../en/docs/verification.md): `ZHIPU_API_KEY`.

Standalone examples read exported environment variables, not .env automatically. Running the command makes a real request and may incur charges.

```bash
python models/zhipu/glm-4.7/examples/01_basic.py
```

Complete source, copied unchanged from [the canonical file](../../models/zhipu/glm-4.7/examples/01_basic.py):

```python
"""付费 glm-4.7 基础对话；资料核对2026-10-14，不继承Flash历史实测。
官方型号：https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7
兼容接口：https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
用法：设置 ZHIPU_API_KEY 后从仓库根运行本文件。参数解释见 ../parameters.md。
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
    response = create_with_backoff(
        client, model="glm-4.7",
        messages=[{"role": "user", "content": "用一句话介绍你自己"}],
    )
    print(completed_message(response).content)
    print_usage(response)


if __name__ == "__main__":
    main()
```

## Read the important lines

- [Line 24](../../models/zhipu/glm-4.7/examples/01_basic.py#L24): SDK retries are disabled; the local helper owns bounded retries. Do not multiply two retry layers. [Parameter evidence](../../models/zhipu/glm-4.7/parameters.en.md)
- [Line 28](../../models/zhipu/glm-4.7/examples/01_basic.py#L28): Only HTTP 429 with business code 1302/1305 enters this retry path, with at most three attempts; not every 429 is transient. [Parameter evidence](../../models/zhipu/glm-4.7/parameters.en.md)
- [Line 97](../../models/zhipu/glm-4.7/examples/01_basic.py#L97): Check the exact paid glm-4.7 ID, not free Flash with inherited evidence. This basic file also omits thinking and output-budget controls. [Parameter evidence](../../models/zhipu/glm-4.7/parameters.en.md)
- [Line 70](../../models/zhipu/glm-4.7/examples/01_basic.py#L70): Check one candidate, normal completion, no unhandled tools and nonempty content. Do not replace sanitized errors with public raw responses. [Parameter evidence](../../models/zhipu/glm-4.7/parameters.en.md)

## What should count as success

The code writes final content to stdout and usage statistics to stderr. Wording is not fixed: the original reports intentionally omit answer text. Normal completion and nonempty final content are acceptance checks, not proof of factual answer accuracy. A thrown error is a failed check, not something to hide by removing the helper.

[Actual output/check logic](../../models/zhipu/glm-4.7/examples/01_basic.py) · [Evidence boundaries](../../en/docs/evidence-policy.md)

## Original execution evidence

Current-source HTTP evidence passed at 2026-10-14T04:12:36.474074+00:00. [Original sanitized report](../../verification/examples/2026-10-14-zhipu-paid-attempt2.json) · [Current status](../../en/docs/example-status.md)

Source SHA-256: `ad0906242fa2c9590a4885b4a35fca59fbc40c97baef2e4ce8880a3062664469`

This page is a reading view of that exact file, not another live run. It does not verify an Agent's changed code, arbitrary prompts or parameters, other model IDs, or present account availability.

## Official sources and advanced examples

- [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7)
- [Official source 2](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8)
- [Official source 3](https://docs.bigmodel.cn/cn/api/api-code)

[Full parameter explanations and official citations](../../models/zhipu/glm-4.7/parameters.en.md)

- [streaming · 02_streaming.py](../../models/zhipu/glm-4.7/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/zhipu/glm-4.7/examples/03_thinking.py)
- [json_object · 04_json_output.py](../../models/zhipu/glm-4.7/examples/04_json_output.py)
- [tool_calling · 05_tool_calling.py](../../models/zhipu/glm-4.7/examples/05_tool_calling.py)
- [multi_turn · 06_multi_turn.py](../../models/zhipu/glm-4.7/examples/06_multi_turn.py)
- [thinking_tool_calling · 07_thinking_tools.py](../../models/zhipu/glm-4.7/examples/07_thinking_tools.py)
