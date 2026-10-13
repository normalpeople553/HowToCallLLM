# 智谱 GLM 官方资料卡

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

仓库于 2026-10-13 验证了 `glm-4.7-flash` 的普通、流式和 `thinking.type=disabled` 调用，见 [`tests/verify_calls.py`](../../tests/verify_calls.py)。这项实测不能外推到 GLM-5.3；官方 GLM-5.3 Flash 文档说明该代模型不能关闭思考。[GLM-5.3 Flash 文档](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash)
