# MiniMax calling code and human review

[All worked examples](README.en.md) · [中文](minimax.md)

`MiniMax-M2.7` · [Model manual](../../models/minimax/MiniMax-M2.7/README.en.md) · [Parameter reference](../../models/minimax/MiniMax-M2.7/parameters.en.md)

## Run the complete example

Set the following environment variable locally, after preparing the [locked environment](../../en/docs/verification.md): `MINIMAX_API_KEY`.

Standalone examples read exported environment variables, not .env automatically. Running the command makes a real request and may incur charges.

```bash
python models/minimax/MiniMax-M2.7/examples/01_basic.py
```

Complete source, copied unchanged from [the canonical file](../../models/minimax/MiniMax-M2.7/examples/01_basic.py):

```python
"""MiniMax-M2.7 基础调用；reasoning_split 只拆分输出，不关闭思考。

官方来源：
https://platform.minimax.cn/docs/api-reference/text-openai-api
https://platform.minimax.cn/docs/api-reference/text-chat-openai
本型号已公告服务调整计划，调用前请核对 sources.json 中的官方生命周期来源。
"""

import os

from openai import OpenAI


def check_business_status(response) -> None:
    """HTTP 200 不等于业务成功；只使用状态码，不输出原始错误内容。"""
    base = getattr(response, "base_resp", None)
    if base is None:
        return
    code = base.get("status_code") if isinstance(base, dict) else getattr(base, "status_code", None)
    if isinstance(code, bool) or not isinstance(code, int) or code != 0:
        raise RuntimeError("MiniMax 返回非零或缺失的业务状态码")


def final_text(content) -> str:
    if not isinstance(content, str):
        raise RuntimeError("没有最终正文")
    text = content.strip()
    # 兼容内联 <think> 形式；仅处理展示文本，历史消息必须原样保留。
    while text.startswith("<think>"):
        _, closing, text = text.partition("</think>")
        if not closing:
            raise RuntimeError("内联思考没有完整结束，不能当作最终答案")
        text = text.strip()
    if not text:
        raise RuntimeError("只有思考或空内容，没有最终正文")
    return text


def completed_text(response) -> str:
    check_business_status(response)
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"回答未完整完成：{choice.finish_reason!r}；请检查思考与正文预算")
    if getattr(choice.message, "tool_calls", None):
        raise RuntimeError("收到未处理的工具调用")
    return final_text(choice.message.content)

def main() -> None:
    client = OpenAI(
        api_key=os.environ["MINIMAX_API_KEY"],
        base_url="https://api.minimax.cn/v1",
        timeout=120,
    )
    response = client.chat.completions.create(
        model="MiniMax-M2.7",
        messages=[{"role": "user", "content": "用一句话介绍你自己。"}],
        extra_body={"reasoning_split": True},
        max_completion_tokens=16384,  # 项目演示预算，不是型号上限或官方默认。
    )
    print(completed_text(response))
    print("本次用量：", response.usage)


if __name__ == "__main__":
    main()
```

## Read the important lines

- [Line 59](../../models/minimax/MiniMax-M2.7/examples/01_basic.py#L59): reasoning_split separates thinking output; it does not disable thinking. Do not transplant another model's controls to M2.7. [Parameter evidence](../../models/minimax/MiniMax-M2.7/parameters.en.md)
- [Line 60](../../models/minimax/MiniMax-M2.7/examples/01_basic.py#L60): 16384 is this file's demonstration budget, not the model limit, official default or a guaranteed final-answer length. [Parameter evidence](../../models/minimax/MiniMax-M2.7/parameters.en.md)
- [Line 39](../../models/minimax/MiniMax-M2.7/examples/01_basic.py#L39): Check the business status when present, normal completion and final content; HTTP 200 alone is insufficient. [Parameter evidence](../../models/minimax/MiniMax-M2.7/parameters.en.md)
- [Line 24](../../models/minimax/MiniMax-M2.7/examples/01_basic.py#L24): Removing complete `<think>` spans is for display only. Unclosed or thinking-only content is not a final answer; tool history must retain original messages. [Parameter evidence](../../models/minimax/MiniMax-M2.7/parameters.en.md)

## What should count as success

The code prints final content and usage statistics. Wording is not fixed: the original reports intentionally omit answer text. Normal completion and nonempty final content are acceptance checks, not proof of factual answer accuracy. A thrown error is a failed check, not something to hide by removing the helper.

[Actual output/check logic](../../models/minimax/MiniMax-M2.7/examples/01_basic.py) · [Evidence boundaries](../../en/docs/evidence-policy.md)

## Original execution evidence

The current source has passed real HTTP evidence. [Original sanitized report](../../verification/examples/2026-10-14-minimax-attempt3.json) · [Current status](../../en/docs/example-status.md)

Source SHA-256: `a0c609a9242f357e6a0d51ce83745d80a1b883d794f31390bfe96305fc41cd9b`

This page is a reading view of that exact file, not another live run. It does not verify an Agent's changed code, arbitrary prompts or parameters, other model IDs, or present account availability.

## Official sources and advanced examples

- [Official source 1](https://platform.minimax.cn/docs/api-reference/text-openai-api)
- [Official source 2](https://platform.minimax.cn/docs/api-reference/text-chat-openai)
- [Official source 3](https://platform.minimax.cn/docs/guides/models-intro)

[Full parameter explanations and official citations](../../models/minimax/MiniMax-M2.7/parameters.en.md)

- [streaming · 02_streaming.py](../../models/minimax/MiniMax-M2.7/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/minimax/MiniMax-M2.7/examples/03_thinking.py)
- [tool_calling · 05_tool_calling.py](../../models/minimax/MiniMax-M2.7/examples/05_tool_calling.py)
- [multi_turn · 06_multi_turn.py](../../models/minimax/MiniMax-M2.7/examples/06_multi_turn.py)
- [native_chat_completions · 07_native_curl.sh](../../models/minimax/MiniMax-M2.7/examples/07_native_curl.sh)
