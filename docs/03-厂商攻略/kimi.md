# Kimi 官方资料卡

[English](../../en/docs/vendors/kimi.md)

核对日期：**2026-10-13**。厂商事实以 [Kimi 开放平台文档](https://platform.kimi.com/docs/llms.txt)为准；仓库实测口径见[来源与核验规则](../来源与核验规则.md)。

| 项目 | 值与官方来源 |
|---|---|
| Key | [`MOONSHOT_API_KEY`；管理页面](https://platform.moonshot.cn/console/api-keys) |
| `base_url` | [`https://api.moonshot.cn/v1`](https://platform.kimi.com/docs/get-api-key) |
| 项目默认模型 | [`kimi-k2.6`](https://platform.kimi.com/docs/models) |
| 模型 | [官方模型列表](https://platform.kimi.com/docs/models) |
| 价格 | [官方 Chat 价格页](https://platform.kimi.com/docs/pricing/chat) |
| 思考 | [官方思考模型指南](https://platform.kimi.com/docs/guide/use-thinking-models) |
| 流式 | [官方流式输出指南](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api) |

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["MOONSHOT_API_KEY"],
    base_url="https://api.moonshot.cn/v1",
)
response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "你好"}],
)
print(response.choices[0].message.content)
```

官方思考指南给出的关闭写法是 `extra_body={"thinking": {"type": "disabled"}}`；不要把这一参数自动套用到未在官方模型页确认的模型。[官方思考指南](https://platform.kimi.com/docs/guide/use-thinking-models)

模型名、上下文长度和价格都直接从[官方模型页](https://platform.kimi.com/docs/models)与[官方价格页](https://platform.kimi.com/docs/pricing/chat)核对，本项目不维护二手数字表。

`kimi-k2.6` 在 2026-10-13 的历史基础验证覆盖普通、流式、思考开关、JSON 对象、首段工具调用和图片请求格式；报告没有记录最终结束原因、工具结果回传或图片内容识别，因此这些项目不算完整闭环验证。[历史脱敏报告](../../models/kimi/kimi-k2.6/verification/2026-10-13.json) 最新结果统一查[验证状态](../验证状态.md)，完整代码查[型号说明书](../../models/kimi/kimi-k2.6/README.md)。
