# Kimi calling code and human review

[All worked examples](README.en.md) · [中文](kimi.md)

`kimi-k2.6` · [Model manual](../../models/kimi/kimi-k2.6/README.en.md) · [Parameter reference](../../models/kimi/kimi-k2.6/parameters.en.md)

## Run the complete example

Set the following environment variable locally, after preparing the [locked environment](../../en/docs/verification.md): `MOONSHOT_API_KEY`.

Standalone examples read exported environment variables, not .env automatically. Running the command makes a real request and may incur charges.

```bash
python models/kimi/kimi-k2.6/examples/01_basic.py
```

Complete source, copied unchanged from [the canonical file](../../models/kimi/kimi-k2.6/examples/01_basic.py):

```python
"""Kimi 最小调用，检查回答完整性。

官方来源：https://platform.kimi.com/docs/api/chat
"""

import os

from openai import OpenAI


def completed_text(response) -> str:
    """应用检查：只有正常结束且非空的正文才能当作完整结果。"""
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(
            f"回答未正常完成：finish_reason={choice.finish_reason!r}；"
            "length 表示达到生成或上下文限制，请检查思考与回答预算"
        )
    content = choice.message.content
    if getattr(choice.message, "tool_calls", None):
        raise RuntimeError("收到未处理的工具调用")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("模型没有返回最终正文；请检查思考预算和提示词")
    return content

client = OpenAI(
    api_key=os.environ["MOONSHOT_API_KEY"],
    base_url="https://api.moonshot.cn/v1",
    timeout=120,
)

response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)
print(completed_text(response))
print("本次用量：", response.usage)
```

## Read the important lines

- [Line 28](../../models/kimi/kimi-k2.6/examples/01_basic.py#L28): Match MOONSHOT_API_KEY to this Moonshot /v1 URL, not another product endpoint. [Parameter evidence](../../models/kimi/kimi-k2.6/parameters.en.md)
- [Line 35](../../models/kimi/kimi-k2.6/examples/01_basic.py#L35): This file fixes K2.6 and omits a thinking switch. A different model or added thinking/budget fields need their own parameter evidence. [Parameter evidence](../../models/kimi/kimi-k2.6/parameters.en.md)
- [Line 11](../../models/kimi/kimi-k2.6/examples/01_basic.py#L11): Distinguish thinking from the final answer; this helper accepts only normally completed, nonempty final content. [Parameter evidence](../../models/kimi/kimi-k2.6/parameters.en.md)

## What should count as success

The code prints final content and usage statistics. Wording is not fixed. Normal completion and nonempty final content are acceptance checks, not proof of factual answer accuracy. A thrown error is a failed check, not something to hide by removing the helper.

[Actual output/check logic](../../models/kimi/kimi-k2.6/examples/01_basic.py) · [Evidence boundaries](../../en/docs/evidence-policy.md)

## Public record boundaries

The maintainer's execution records are local and not published with this repository. This page only checks the public source, exact request identity, reading anchors and official-source links; it does not consult private reports or claim a publicly verifiable pass.

This is a reading view, not a live run. It does not verify an Agent's changed code, arbitrary prompts or parameters, other model IDs, or current account availability.

## Official sources and advanced examples

- [Official source 1](https://platform.kimi.com/docs/api/chat)
- [Official source 2](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart)

[Full parameter explanations and official citations](../../models/kimi/kimi-k2.6/parameters.en.md)

- [streaming · 02_streaming.py](../../models/kimi/kimi-k2.6/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/kimi/kimi-k2.6/examples/03_thinking.py)
- [json_object · 04_json_output.py](../../models/kimi/kimi-k2.6/examples/04_json_output.py)
- [tool_calling · 05_tool_calling.py](../../models/kimi/kimi-k2.6/examples/05_tool_calling.py)
- [vision · 06_vision.py](../../models/kimi/kimi-k2.6/examples/06_vision.py)
- [multi_turn · 07_multi_turn.py](../../models/kimi/kimi-k2.6/examples/07_multi_turn.py)
- [thinking_tool_calling · 08_thinking_tools.py](../../models/kimi/kimi-k2.6/examples/08_thinking_tools.py)
- [video_input · 09_video.py](../../models/kimi/kimi-k2.6/examples/09_video.py)
- [json_schema · 10_json_schema.py](../../models/kimi/kimi-k2.6/examples/10_json_schema.py)
