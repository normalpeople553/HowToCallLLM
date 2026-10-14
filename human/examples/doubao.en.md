# Doubao calling code and human review

[All worked examples](README.en.md) · [中文](doubao.md)

`doubao-seed-2-1-pro-260628` · [Model manual](../../models/doubao/doubao-seed-2-1-pro-260628/README.en.md) · [Parameter reference](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.en.md)

## Run the complete example

Set the following environment variable locally, after preparing the [locked environment](../../en/docs/verification.md): `ARK_API_KEY`.

Standalone examples read exported environment variables, not .env automatically. Running the command makes a real request and may incur charges.

```bash
python models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py
```

Complete source, copied unchanged from [the canonical file](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py):

```python
"""豆包 最小调用，检查回答完整性。

官方来源：https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh
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

def main():
    client = OpenAI(
        api_key=os.environ["ARK_API_KEY"],
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        timeout=120,
    )
    response = client.chat.completions.create(
        model="doubao-seed-2-1-pro-260628",
        messages=[{"role": "user", "content": "用一句话介绍你自己"}],
        extra_body={"thinking": {"type": "disabled"}},
    )
    print(completed_text(response))
    print("本次用量：", response.usage)


if __name__ == "__main__":
    main()
```

## Read the important lines

- [Line 29](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py#L29): Match ARK_API_KEY, the Beijing /api/v3 URL and full dated model ID. Subscription shorthand is not the same metered API identity. [Parameter evidence](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.en.md)
- [Line 37](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py#L37): This file sends disabled thinking through Python SDK extra_body. It sets no explicit output budget; do not claim a coded total-output limit. [Parameter evidence](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.en.md)
- [Line 11](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py#L11): An HTTP response is not proof of complete content; check finish_reason, pending tools and final text. [Parameter evidence](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.en.md)

## What should count as success

The code prints final content and usage statistics. Wording is not fixed: the original reports intentionally omit answer text. Normal completion and nonempty final content are acceptance checks, not proof of factual answer accuracy. A thrown error is a failed check, not something to hide by removing the helper.

[Actual output/check logic](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py) · [Evidence boundaries](../../en/docs/evidence-policy.md)

## Original execution evidence

The current source has passed real HTTP evidence. [Original sanitized report](../../verification/examples/2026-10-14-doubao-attempt3.json) · [Current status](../../en/docs/example-status.md)

Source SHA-256: `5edb7519c41bd3dffb4e4026b2dd13b98ccf2ea91d13b94a9a0078a20f8754cd`

This page is a reading view of that exact file, not another live run. It does not verify an Agent's changed code, arbitrary prompts or parameters, other model IDs, or present account availability.

## Official sources and advanced examples

- [Official source 1](https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh)
- [Official source 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh)

[Full parameter explanations and official citations](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.en.md)

- [streaming · 02_streaming.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/03_thinking.py)
- [structured_output · 04_json_output.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/04_json_output.py)
- [tool_calling · 05_tool_calling.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/05_tool_calling.py)
- [vision · 06_vision.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/06_vision.py)
- [multi_turn · 07_multi_turn.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/07_multi_turn.py)
- [thinking_tool_calling · 08_thinking_tools.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/08_thinking_tools.py)
- [video_input · 09_video.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/09_video.py)
- [context_caching · 10_implicit_cache.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/10_implicit_cache.py)
