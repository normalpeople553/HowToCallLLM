# 智谱 GLM 官方资料卡

[English](../../en/docs/vendors/zhipu.md)

核对日期：**2026-10-13**。厂商事实以 [智谱开放文档](https://docs.bigmodel.cn/llms.txt)为准；仓库实测口径见[来源与核验规则](../来源与核验规则.md)。

| 项目 | 值与官方来源 |
|---|---|
| Key | [`ZHIPU_API_KEY`；管理页面](https://bigmodel.cn/usercenter/apikeys) |
| `base_url` | [`https://open.bigmodel.cn/api/paas/v4`](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| 项目默认模型 | [`glm-4.7-flash`](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| 模型与价格 | [官方定价页](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| OpenAI SDK | [官方兼容说明](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| 思考 | [官方思考模式文档](https://docs.bigmodel.cn/cn/guide/capabilities/thinking) |

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["ZHIPU_API_KEY"],
    base_url="https://open.bigmodel.cn/api/paas/v4",
)
response = client.chat.completions.create(
    model="glm-4.7-flash",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=512,
)
print(response.choices[0].message.content)
```

`glm-4.7-flash` 的价格状态必须从[官方定价页](https://docs.bigmodel.cn/cn/guide/start/pricing)复核；本项目不把“Flash”名称本身等同于免费承诺。

2026-10-13 的历史验证中，`glm-4.7-flash` 六项请求均遭遇 429（账户速率限制 `1302` 或模型访问量过大 `1305`），没有记录为通过。[历史脱敏报告](../../models/zhipu/glm-4.7-flash/verification/2026-10-13.json) 最新结果统一查[验证状态](../验证状态.md)，完整代码查[型号说明书](../../models/zhipu/glm-4.7-flash/README.md)。GLM-5.3 的思考限制必须单独核对，不继承 GLM-4.7 配置。[GLM-5.3 Flash 文档](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash)
