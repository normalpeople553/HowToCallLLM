# DeepSeek 调用代码与人工核对

[全部代码阅读页](README.md) · [English](deepseek.en.md)

`deepseek-flash` · [型号说明书](../../models/deepseek/deepseek-flash/README.md) · [逐项参数说明](../../models/deepseek/deepseek-flash/parameters.md)

## 运行完整示例

按[锁定环境步骤](../../docs/验证与复现.md)准备环境，在本地设置：`DEEPSEEK_API_KEY`。

独立示例读取已导出的环境变量，不自动加载 .env；执行下列命令会真实调用并可能计费。

```bash
python models/deepseek/deepseek-flash/examples/01_basic.py
```

下面是完整源文件，逐字来自[规范文件](../../models/deepseek/deepseek-flash/examples/01_basic.py)：

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

## 关键行应该怎么看

- [第 28 行](../../models/deepseek/deepseek-flash/examples/01_basic.py#L28)：先核对环境变量、服务地址和网络超时；不要把 timeout 当成 token 预算。 [参数依据](../../models/deepseek/deepseek-flash/parameters.md)
- [第 35 行](../../models/deepseek/deepseek-flash/examples/01_basic.py#L35)：准确请求 Flash；本例没有显式设置思考开关、输出预算或采样参数，不能读成已经关闭思考或限制输出长度。 [参数依据](../../models/deepseek/deepseek-flash/parameters.md)
- [第 11 行](../../models/deepseek/deepseek-flash/examples/01_basic.py#L11)：Agent 代码也应检查结束原因、待处理工具调用和非空最终正文，不能只打印 choices[0] 就算完整成功。 [参数依据](../../models/deepseek/deepseek-flash/parameters.md)

## 运行后应该检查什么

代码打印最终正文和用量统计。回答措辞不是固定值，原始报告也刻意不保存回答正文。正常结束、非空正文是验收条件，不证明答案事实准确。抛出异常表示相应检查未通过，不应通过删除校验函数掩盖。

[实际输出与校验逻辑](../../models/deepseek/deepseek-flash/examples/01_basic.py) · [证据边界](../../docs/来源与核验规则.md)

## 对应的原始实测证据

当前源码的真实 HTTP 证据通过时间：2026-10-14T02:56:26.472152+00:00。[原始脱敏报告](../../verification/examples/2026-10-14-deepseek-attempt3.json) · [当前状态](../../docs/示例实测状态.md)

源文件 SHA-256：`bcd589398bfc2ed984cd9bddff6d2268b08bd5f3600a2dddb91852df63e4e767`

本页是该准确文件的阅读视图，不是又一次线上实测；它不验证 Agent 改写后的代码、任意提示词/参数组合、其他型号或当前账户可用性。

## 官方出处与进阶示例

- [官方出处 1](https://api-docs.deepseek.com/api/create-chat-completion/)

[全部参数解释与官方引用](../../models/deepseek/deepseek-flash/parameters.md)

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
