# MiniMax 调用代码与人工核对

[全部代码阅读页](README.md) · [English](minimax.en.md)

`MiniMax-M2.7` · [型号说明书](../../models/minimax/MiniMax-M2.7/README.md) · [逐项参数说明](../../models/minimax/MiniMax-M2.7/parameters.md)

## 运行完整示例

按[锁定环境步骤](../../docs/验证与复现.md)准备环境，在本地设置：`MINIMAX_API_KEY`。

独立示例读取已导出的环境变量，不自动加载 .env；执行下列命令会真实调用并可能计费。

```bash
python models/minimax/MiniMax-M2.7/examples/01_basic.py
```

下面是完整源文件，逐字来自[规范文件](../../models/minimax/MiniMax-M2.7/examples/01_basic.py)：

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

## 关键行应该怎么看

- [第 59 行](../../models/minimax/MiniMax-M2.7/examples/01_basic.py#L59)：reasoning_split 用于拆分思考输出，不是关闭思考；不要把其他型号的开关移植到 M2.7。 [参数依据](../../models/minimax/MiniMax-M2.7/parameters.md)
- [第 60 行](../../models/minimax/MiniMax-M2.7/examples/01_basic.py#L60)：16384 是这个源文件的项目演示预算，不是型号上限、官方默认或保证得到同样长的正文。 [参数依据](../../models/minimax/MiniMax-M2.7/parameters.md)
- [第 39 行](../../models/minimax/MiniMax-M2.7/examples/01_basic.py#L39)：检查可用业务状态、正常结束和最终正文；HTTP 200 本身不足以证明成功。 [参数依据](../../models/minimax/MiniMax-M2.7/parameters.md)
- [第 24 行](../../models/minimax/MiniMax-M2.7/examples/01_basic.py#L24)：去除完整 `<think>` 段只用于展示；缺少闭合标签或只有思考时不能冒充最终答案，工具历史仍须保留原消息。 [参数依据](../../models/minimax/MiniMax-M2.7/parameters.md)

## 运行后应该检查什么

代码打印最终正文和用量统计。回答措辞不是固定值，原始报告也刻意不保存回答正文。正常结束、非空正文是验收条件，不证明答案事实准确。抛出异常表示相应检查未通过，不应通过删除校验函数掩盖。

[实际输出与校验逻辑](../../models/minimax/MiniMax-M2.7/examples/01_basic.py) · [证据边界](../../docs/来源与核验规则.md)

## 对应的原始实测证据

当前源码的真实 HTTP 证据通过时间：2026-10-14T02:56:31.070798+00:00。[原始脱敏报告](../../verification/examples/2026-10-14-minimax-attempt3.json) · [当前状态](../../docs/示例实测状态.md)

源文件 SHA-256：`a0c609a9242f357e6a0d51ce83745d80a1b883d794f31390bfe96305fc41cd9b`

本页是该准确文件的阅读视图，不是又一次线上实测；它不验证 Agent 改写后的代码、任意提示词/参数组合、其他型号或当前账户可用性。

## 官方出处与进阶示例

- [官方出处 1](https://platform.minimax.cn/docs/api-reference/text-openai-api)
- [官方出处 2](https://platform.minimax.cn/docs/api-reference/text-chat-openai)
- [官方出处 3](https://platform.minimax.cn/docs/guides/models-intro)

[全部参数解释与官方引用](../../models/minimax/MiniMax-M2.7/parameters.md)

- [streaming · 02_streaming.py](../../models/minimax/MiniMax-M2.7/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/minimax/MiniMax-M2.7/examples/03_thinking.py)
- [tool_calling · 05_tool_calling.py](../../models/minimax/MiniMax-M2.7/examples/05_tool_calling.py)
- [multi_turn · 06_multi_turn.py](../../models/minimax/MiniMax-M2.7/examples/06_multi_turn.py)
- [native_chat_completions · 07_native_curl.sh](../../models/minimax/MiniMax-M2.7/examples/07_native_curl.sh)
