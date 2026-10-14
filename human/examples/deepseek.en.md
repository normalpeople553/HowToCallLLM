# DeepSeek calling code and human review

[All worked examples](README.en.md) · [中文](deepseek.md)

`deepseek-flash` · [Model manual](../../models/deepseek/deepseek-flash/README.en.md) · [Parameter reference](../../models/deepseek/deepseek-flash/parameters.en.md)

## Run the complete example

Set the following environment variable locally, after preparing the [locked environment](../../en/docs/verification.md): `DEEPSEEK_API_KEY`.

Standalone examples read exported environment variables, not .env automatically. Running the command makes a real request and may incur charges.

```bash
python models/deepseek/deepseek-flash/examples/01_basic.py
```

Complete source, copied unchanged from [the canonical file](../../models/deepseek/deepseek-flash/examples/01_basic.py):

```python
"""DeepSeek 最小调用，检查回答完整性。

官方来源：https://api-docs.deepseek.com/api/create-chat-completion/
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
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=120,
)

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)
print(completed_text(response))
print("本次用量：", response.usage)
```

## Read the important lines

- [Line 28](../../models/deepseek/deepseek-flash/examples/01_basic.py#L28): Check the key environment variable, service URL and network timeout; timeout is not a token budget. [Parameter evidence](../../models/deepseek/deepseek-flash/parameters.en.md)
- [Line 35](../../models/deepseek/deepseek-flash/examples/01_basic.py#L35): The request targets this exact Flash ID. It sets no thinking switch, output budget or sampling control; do not read omission as disabled thinking or an explicit output limit. [Parameter evidence](../../models/deepseek/deepseek-flash/parameters.en.md)
- [Line 11](../../models/deepseek/deepseek-flash/examples/01_basic.py#L11): Review finish reason, unhandled tool calls and nonempty final content; printing choices[0] alone is not complete success. [Parameter evidence](../../models/deepseek/deepseek-flash/parameters.en.md)

## What should count as success

The code prints final content and usage statistics. Wording is not fixed: the original reports intentionally omit answer text. Normal completion and nonempty final content are acceptance checks, not proof of factual answer accuracy. A thrown error is a failed check, not something to hide by removing the helper.

[Actual output/check logic](../../models/deepseek/deepseek-flash/examples/01_basic.py) · [Evidence boundaries](../../en/docs/evidence-policy.md)

## Original execution evidence

The current source has passed real HTTP evidence. [Original sanitized report](../../verification/examples/2026-10-14-deepseek-attempt3.json) · [Current status](../../en/docs/example-status.md)

Source SHA-256: `bcd589398bfc2ed984cd9bddff6d2268b08bd5f3600a2dddb91852df63e4e767`

This page is a reading view of that exact file, not another live run. It does not verify an Agent's changed code, arbitrary prompts or parameters, other model IDs, or present account availability.

## Official sources and advanced examples

- [Official source 1](https://api-docs.deepseek.com/api/create-chat-completion/)

[Full parameter explanations and official citations](../../models/deepseek/deepseek-flash/parameters.en.md)

- [streaming · 02_streaming.py](../../models/deepseek/deepseek-flash/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/deepseek/deepseek-flash/examples/03_thinking.py)
- [json_object · 04_json_output.py](../../models/deepseek/deepseek-flash/examples/04_json_output.py)
- [tool_calling · 05_tool_calling.py](../../models/deepseek/deepseek-flash/examples/05_tool_calling.py)
- [vision · 06_vision.py](../../models/deepseek/deepseek-flash/examples/06_vision.py)
- [chat_completions · 07_typescript.ts](../../models/deepseek/deepseek-flash/examples/07_typescript.ts)
- [chat_completions · 08_curl.sh](../../models/deepseek/deepseek-flash/examples/08_curl.sh)
- [multi_turn · 09_multi_turn.py](../../models/deepseek/deepseek-flash/examples/09_multi_turn.py)
- [vision_files · 10_vision_files.py](../../models/deepseek/deepseek-flash/examples/10_vision_files.py)
- [responses_vision · 11_responses_vision.py](../../models/deepseek/deepseek-flash/examples/11_responses_vision.py)
- [thinking_tool_calling · 12_thinking_tools.py](../../models/deepseek/deepseek-flash/examples/12_thinking_tools.py)
- [strict_tool_calling · 13_strict_tools.py](../../models/deepseek/deepseek-flash/examples/13_strict_tools.py)
- [chat_prefix_completion · 14_prefix_completion.py](../../models/deepseek/deepseek-flash/examples/14_prefix_completion.py)
- [fim_completion · 15_fim_completion.py](../../models/deepseek/deepseek-flash/examples/15_fim_completion.py)
