# Kimi 调用代码与人工核对

[全部代码阅读页](README.md) · [English](kimi.en.md)

`kimi-k2.6` · [型号说明书](../../models/kimi/kimi-k2.6/README.md) · [逐项参数说明](../../models/kimi/kimi-k2.6/parameters.md)

## 运行完整示例

按[锁定环境步骤](../../docs/验证与复现.md)准备环境，在本地设置：`MOONSHOT_API_KEY`。

独立示例读取已导出的环境变量，不自动加载 .env；执行下列命令会真实调用并可能计费。

```bash
python models/kimi/kimi-k2.6/examples/01_basic.py
```

下面是完整源文件，逐字来自[规范文件](../../models/kimi/kimi-k2.6/examples/01_basic.py)：

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

## 关键行应该怎么看

- [第 28 行](../../models/kimi/kimi-k2.6/examples/01_basic.py#L28)：核对 MOONSHOT_API_KEY 与本例 Moonshot /v1 地址；不要因名称叫 Kimi 就改用别的产品入口。 [参数依据](../../models/kimi/kimi-k2.6/parameters.md)
- [第 35 行](../../models/kimi/kimi-k2.6/examples/01_basic.py#L35)：本例固定 K2.6 且省略思考开关；Agent 若改型号或增加思考、预算字段，需要读新组合的参数依据。 [参数依据](../../models/kimi/kimi-k2.6/parameters.md)
- [第 11 行](../../models/kimi/kimi-k2.6/examples/01_basic.py#L11)：区分思考与最终答案；这里只接受正常结束且非空的最终正文。 [参数依据](../../models/kimi/kimi-k2.6/parameters.md)

## 运行后应该检查什么

代码打印最终正文和用量统计。回答措辞不是固定值。正常结束、非空正文是验收条件，不证明答案事实准确。抛出异常表示相应检查未通过，不应通过删除校验函数掩盖。

[实际输出与校验逻辑](../../models/kimi/kimi-k2.6/examples/01_basic.py) · [证据边界](../../docs/来源与核验规则.md)

## 公开记录边界

维护者的实测记录仅在本地保存，不随仓库发布。本页只校验公开源码、准确请求型号、阅读行号与官方出处，不读取私有报告，也不声称公开可核验的通过结论。

本页是代码阅读视图，不是线上调用；它不验证 Agent 改写后的代码、任意提示词/参数组合、其他型号或当前账户可用性。

## 官方出处与进阶示例

- [官方出处 1](https://platform.kimi.com/docs/api/chat)
- [官方出处 2](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart)

[全部参数解释与官方引用](../../models/kimi/kimi-k2.6/parameters.md)

- [streaming · 02_streaming.py](../../models/kimi/kimi-k2.6/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/kimi/kimi-k2.6/examples/03_thinking.py)
- [json_object · 04_json_output.py](../../models/kimi/kimi-k2.6/examples/04_json_output.py)
- [tool_calling · 05_tool_calling.py](../../models/kimi/kimi-k2.6/examples/05_tool_calling.py)
- [vision · 06_vision.py](../../models/kimi/kimi-k2.6/examples/06_vision.py)
- [multi_turn · 07_multi_turn.py](../../models/kimi/kimi-k2.6/examples/07_multi_turn.py)
- [thinking_tool_calling · 08_thinking_tools.py](../../models/kimi/kimi-k2.6/examples/08_thinking_tools.py)
- [video_input · 09_video.py](../../models/kimi/kimi-k2.6/examples/09_video.py)
- [json_schema · 10_json_schema.py](../../models/kimi/kimi-k2.6/examples/10_json_schema.py)
