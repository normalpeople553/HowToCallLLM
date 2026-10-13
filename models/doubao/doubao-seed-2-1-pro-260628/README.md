# `doubao-seed-2-1-pro-260628` 调用说明书

> 核对日期：**2026-10-13**。该 ID 已在官方列表的“往期模型”区域，但本仓库当天仍调用成功；新项目选型前应先查看当前模型列表。机器卡片见 [`doubao-seed-2-1-pro-260628.json`](../../../skills/model-manual/references/models/doubao-seed-2-1-pro-260628.json)。

## 1. 一眼看懂

| 项目 | 当前值 | 官方来源 |
|---|---|---|
| Model ID | `doubao-seed-2-1-pro-260628` | [模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| 生命周期 | 往期模型，2026-10-13 实测仍可调用 | [模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [实测记录](verification/2026-10-13.json) |
| Base URL | `https://ark.cn-beijing.volces.com/api/v3` | [在线推理 API](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) |
| 上下文 | 256K tokens | [模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| 默认/最大输出 | 4K / 256K tokens | [模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| 能力 | 深度思考、多模态、工具调用、结构化输出 | [模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |

## 2. 开通与最小调用

调用前需要在方舟控制台开通对应模型；开通方式以[模型开通管理](https://docs.volcengine.com/docs/ark/activation-management?lang=zh)为准。

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["ARK_API_KEY"],
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)
response = client.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)
print(response.choices[0].message.content)
```

鉴权、Model ID 直调和 OpenAI 兼容字段见[在线推理 API](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh)。完整示例：[`examples/01_basic.py`](examples/01_basic.py)。

## 3. 思考与流式输出

该模型默认开启思考，可用 `thinking.type=enabled|disabled` 切换；思考文本位于 `reasoning_content`。[深度思考](https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh)

```python
response = client.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "直接回答 1+1"}],
    extra_body={"thinking": {"type": "disabled"}},
)
```

流式请求使用 `stream=True` 并逐块读取 `delta.content`；接口结构以[在线推理 API](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh)为准。示例：[`examples/02_streaming.py`](examples/02_streaming.py) · [`examples/03_thinking.py`](examples/03_thinking.py)。

## 4. 结构化输出与 Tool Calling

官方模型列表标注该模型支持结构化输出，并推荐 `json_schema`；Schema 仍应保持精简，客户端必须再次解析和校验。[模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh) 示例：[`examples/04_json_output.py`](examples/04_json_output.py)。

官方模型列表标注该模型支持工具调用；应用应把函数声明放在 `tools`，校验返回参数，自行执行工具并回传结果。[模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh) 示例：[`examples/05_tool_calling.py`](examples/05_tool_calling.py)。

## 5. 图片输入与价格

该模型支持多模态理解；Chat Completions 的图片消息格式与限制以[在线推理 API](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh)和[模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh)为准。本仓库用本地生成的 32×32 PNG data URL 完成验证，不依赖外部图片。

价格容易随区域、缓存和活动变化，本页不抄录可能失效的数字；直接查看[官方价格页](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh)。

## 6. 生命周期建议

“往期模型”不等于接口立即不可用；本仓库当天实测成功，但它也不适合默认为长期新项目的唯一依赖。上线前应从[当前模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh)选择替代型号，并为 Model ID 做配置化切换。

## 7. 给 Agent 的固定配置

```yaml
provider: doubao
model: doubao-seed-2-1-pro-260628
base_url: https://ark.cn-beijing.volces.com/api/v3
api_key_env: ARK_API_KEY
thinking_off_extra_body:
  thinking: {type: disabled}
lifecycle: past_but_callable
```

连接信息来自[在线推理 API](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh)，生命周期来自[模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh)并由当天实测补充。实时能力结果见 [`verification/2026-10-13.json`](verification/2026-10-13.json)，复测命令为 `ARK_API_KEY=... python tests/verify_doubao_seed_2_1_pro.py`。
