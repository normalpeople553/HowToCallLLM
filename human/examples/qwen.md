# 通义千问 调用代码与人工核对

[全部代码阅读页](README.md) · [English](qwen.en.md)

`qwen-flash` · [型号说明书](../../models/qwen/qwen-flash/README.md) · [逐项参数说明](../../models/qwen/qwen-flash/parameters.md)

## 运行完整示例

按[锁定环境步骤](../../docs/验证与复现.md)准备环境，在本地设置：`DASHSCOPE_API_KEY`。

独立示例读取已导出的环境变量，不自动加载 .env；执行下列命令会真实调用并可能计费。

```bash
python models/qwen/qwen-flash/examples/01_basic.py
```

下面是完整源文件，逐字来自[规范文件](../../models/qwen/qwen-flash/examples/01_basic.py)：

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

## 关键行应该怎么看

- [第 28 行](../../models/qwen/qwen-flash/examples/01_basic.py#L28)：核对 DASHSCOPE_API_KEY 和本例兼容地址；区域或产品入口改变时另查对应配置。 [参数依据](../../models/qwen/qwen-flash/parameters.md)
- [第 35 行](../../models/qwen/qwen-flash/examples/01_basic.py#L35)：这是准确 ID qwen-flash，不是所有名称带 Flash 的新版。01 未显式设置思考、预算或采样字段。 [参数依据](../../models/qwen/qwen-flash/parameters.md)
- [第 11 行](../../models/qwen/qwen-flash/examples/01_basic.py#L11)：不要删掉结束状态和最终正文校验；同名参数在不同代际的适用性不能从本文件推导。 [参数依据](../../models/qwen/qwen-flash/parameters.md)

## 运行后应该检查什么

代码打印最终正文和用量统计。回答措辞不是固定值。正常结束、非空正文是验收条件，不证明答案事实准确。抛出异常表示相应检查未通过，不应通过删除校验函数掩盖。

[实际输出与校验逻辑](../../models/qwen/qwen-flash/examples/01_basic.py) · [证据边界](../../docs/来源与核验规则.md)

## 公开记录边界

维护者的实测记录仅在本地保存，不随仓库发布。本页只校验公开源码、准确请求型号、阅读行号与官方出处，不读取私有报告，也不声称公开可核验的通过结论。

本页是代码阅读视图，不是线上调用；它不验证 Agent 改写后的代码、任意提示词/参数组合、其他型号或当前账户可用性。

## 官方出处与进阶示例

- [官方出处 1](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)

[全部参数解释与官方引用](../../models/qwen/qwen-flash/parameters.md)

- [streaming · 02_streaming.py](../../models/qwen/qwen-flash/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/qwen/qwen-flash/examples/03_thinking.py)
- [json_object · 04_json_output.py](../../models/qwen/qwen-flash/examples/04_json_output.py)
- [tool_calling · 05_tool_calling.py](../../models/qwen/qwen-flash/examples/05_tool_calling.py)
- [multi_turn · 06_multi_turn.py](../../models/qwen/qwen-flash/examples/06_multi_turn.py)
- [thinking_tool_calling · 07_thinking_tools.py](../../models/qwen/qwen-flash/examples/07_thinking_tools.py)
