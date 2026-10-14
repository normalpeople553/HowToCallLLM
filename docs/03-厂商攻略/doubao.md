# 豆包（火山方舟）官方资料卡

[English](../../en/docs/vendors/doubao.md)

其他准确 ID、生命周期、输入模态及官方价格入口见[豆包语言模型清单](../model-lists/doubao.md)。请区分按量 API、订阅简称和已下线版本；清单不代表都有详细说明书或真实调用证据。

核对日期：**2026-10-13**。厂商事实以火山方舟官方文档为准；仓库实测口径见[来源与核验规则](../来源与核验规则.md)。

| 项目 | 值与官方来源 |
|---|---|
| Key | [`ARK_API_KEY`；管理页面](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) |
| 模型开通 | [官方开通管理说明](https://docs.volcengine.com/docs/ark/activation-management?lang=zh) |
| `base_url` | [`https://ark.cn-beijing.volces.com/api/v3`](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) |
| 项目默认模型 | [`doubao-seed-2-1-pro-260628`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| 模型 | [官方模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| 价格 | [官方价格页](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| 免费额度 | [官方免费推理额度](https://docs.volcengine.com/docs/ark/free-inference-quota?lang=zh) |

官方在线推理文档允许直接用 Model ID 调用；模型是否需要先开通、当前 ID 与可用地域分别以开通管理和模型列表为准。[在线推理](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) · [开通管理](https://docs.volcengine.com/docs/ark/activation-management?lang=zh) · [模型列表](https://docs.volcengine.com/docs/ark/model-list?lang=zh)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["ARK_API_KEY"],
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)
response = client.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "你好"}],
)
print(response.choices[0].message.content)
```

价格与免费额度不在本页抄录数字，分别以[官方价格页](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh)和[官方额度页](https://docs.volcengine.com/docs/ark/free-inference-quota?lang=zh)为准。

调用文件与官方出处见[型号说明书](../../models/doubao/doubao-seed-2-1-pro-260628/README.md)及[来源清单](../../models/doubao/doubao-seed-2-1-pro-260628/examples/sources.json)。测试记录只留维护者本地；安装与运行方式见[验证与复现](../验证与复现.md)。
