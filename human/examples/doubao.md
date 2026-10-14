# 豆包 调用代码与人工核对

[全部代码阅读页](README.md) · [English](doubao.en.md)

`doubao-seed-2-1-pro-260628` · [型号说明书](../../models/doubao/doubao-seed-2-1-pro-260628/README.md) · [逐项参数说明](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.md)

## 运行完整示例

按[锁定环境步骤](../../docs/验证与复现.md)准备环境，在本地设置：`ARK_API_KEY`。

独立示例读取已导出的环境变量，不自动加载 .env；执行下列命令会真实调用并可能计费。

```bash
python models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py
```

下面是完整源文件，逐字来自[规范文件](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py)：

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

## 关键行应该怎么看

- [第 29 行](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py#L29)：核对 ARK_API_KEY、北京 /api/v3 地址和完整日期版 Model ID；订阅简称不能直接当成同一个按量 API 型号。 [参数依据](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.md)
- [第 37 行](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py#L37)：本例通过 Python SDK 的 extra_body 发送关闭思考配置；没有显式发送输出预算，不表示代码已限制总输出。 [参数依据](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.md)
- [第 11 行](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py#L11)：有 HTTP 响应不等于正文完整，仍需核对 finish_reason、工具状态和最终文本。 [参数依据](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.md)

## 运行后应该检查什么

代码打印最终正文和用量统计。回答措辞不是固定值，原始报告也刻意不保存回答正文。正常结束、非空正文是验收条件，不证明答案事实准确。抛出异常表示相应检查未通过，不应通过删除校验函数掩盖。

[实际输出与校验逻辑](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py) · [证据边界](../../docs/来源与核验规则.md)

## 对应的原始实测证据

当前源码已有通过的真实 HTTP 证据。[原始脱敏报告](../../verification/examples/2026-10-14-doubao-attempt3.json) · [当前状态](../../docs/示例实测状态.md)

源文件 SHA-256：`5edb7519c41bd3dffb4e4026b2dd13b98ccf2ea91d13b94a9a0078a20f8754cd`

本页是该准确文件的阅读视图，不是又一次线上实测；它不验证 Agent 改写后的代码、任意提示词/参数组合、其他型号或当前账户可用性。

## 官方出处与进阶示例

- [官方出处 1](https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh)
- [官方出处 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh)

[全部参数解释与官方引用](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.md)

- [streaming · 02_streaming.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/03_thinking.py)
- [structured_output · 04_json_output.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/04_json_output.py)
- [tool_calling · 05_tool_calling.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/05_tool_calling.py)
- [vision · 06_vision.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/06_vision.py)
- [multi_turn · 07_multi_turn.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/07_multi_turn.py)
- [thinking_tool_calling · 08_thinking_tools.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/08_thinking_tools.py)
- [video_input · 09_video.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/09_video.py)
- [context_caching · 10_implicit_cache.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/10_implicit_cache.py)
