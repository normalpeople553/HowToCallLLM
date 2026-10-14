# Qwen calling code and human review

[All worked examples](README.en.md) · [中文](qwen.md)

`qwen-flash` · [Model manual](../../models/qwen/qwen-flash/README.en.md) · [Parameter reference](../../models/qwen/qwen-flash/parameters.en.md)

## Run the complete example

Set the following environment variable locally, after preparing the [locked environment](../../en/docs/verification.md): `DASHSCOPE_API_KEY`.

Standalone examples read exported environment variables, not .env automatically. Running the command makes a real request and may incur charges.

```bash
python models/qwen/qwen-flash/examples/01_basic.py
```

Complete source, copied unchanged from [the canonical file](../../models/qwen/qwen-flash/examples/01_basic.py):

```python
"""通义千问 最小调用，检查回答完整性。

官方来源：https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/
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
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    timeout=120,
)

response = client.chat.completions.create(
    model="qwen-flash",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)
print(completed_text(response))
print("本次用量：", response.usage)
```

## Read the important lines

- [Line 28](../../models/qwen/qwen-flash/examples/01_basic.py#L28): Match DASHSCOPE_API_KEY and this compatible URL. A region or product change needs its own configuration check. [Parameter evidence](../../models/qwen/qwen-flash/parameters.en.md)
- [Line 35](../../models/qwen/qwen-flash/examples/01_basic.py#L35): The exact ID is qwen-flash, not every newer model named Flash. This basic file sets no explicit thinking, budget or sampling fields. [Parameter evidence](../../models/qwen/qwen-flash/parameters.en.md)
- [Line 11](../../models/qwen/qwen-flash/examples/01_basic.py#L11): Keep finish-state and final-content checks. This file does not establish same-named parameter support in other generations. [Parameter evidence](../../models/qwen/qwen-flash/parameters.en.md)

## What should count as success

The code prints final content and usage statistics. Wording is not fixed. Normal completion and nonempty final content are acceptance checks, not proof of factual answer accuracy. A thrown error is a failed check, not something to hide by removing the helper.

[Actual output/check logic](../../models/qwen/qwen-flash/examples/01_basic.py) · [Evidence boundaries](../../en/docs/evidence-policy.md)

## Public record boundaries

The maintainer's execution records are local and not published with this repository. This page only checks the public source, exact request identity, reading anchors and official-source links; it does not consult private reports or claim a publicly verifiable pass.

This is a reading view, not a live run. It does not verify an Agent's changed code, arbitrary prompts or parameters, other model IDs, or current account availability.

## Official sources and advanced examples

- [Official source 1](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)

[Full parameter explanations and official citations](../../models/qwen/qwen-flash/parameters.en.md)

- [streaming · 02_streaming.py](../../models/qwen/qwen-flash/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/qwen/qwen-flash/examples/03_thinking.py)
- [json_object · 04_json_output.py](../../models/qwen/qwen-flash/examples/04_json_output.py)
- [tool_calling · 05_tool_calling.py](../../models/qwen/qwen-flash/examples/05_tool_calling.py)
- [multi_turn · 06_multi_turn.py](../../models/qwen/qwen-flash/examples/06_multi_turn.py)
- [thinking_tool_calling · 07_thinking_tools.py](../../models/qwen/qwen-flash/examples/07_thinking_tools.py)
