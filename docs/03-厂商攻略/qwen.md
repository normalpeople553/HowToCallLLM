# 通义千问（阿里云百炼）官方资料卡

[English](../../en/docs/vendors/qwen.md)

其他准确 ID、生命周期、输入模态及官方价格入口见[通义千问语言模型清单](../model-lists/qwen.md)。请注意地域和快照限制；清单不代表都有详细说明书或真实调用证据。

核对日期：**2026-10-13**。厂商事实以阿里云百炼官方文档为准；仓库实测口径见[来源与核验规则](../来源与核验规则.md)。

| 项目 | 值与官方来源 |
|---|---|
| Key | [`DASHSCOPE_API_KEY`；管理页面](https://bailian.console.aliyun.com/?apiKey=1#/api-key) |
| `base_url` | [官方地域与 Workspace 地址表](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) |
| 项目默认模型 | [`qwen-flash`](https://help.aliyun.com/zh/model-studio/getting-started/models) |
| 模型 | [官方模型列表](https://help.aliyun.com/zh/model-studio/getting-started/models) |
| 价格 | [官方价格页](https://help.aliyun.com/zh/model-studio/model-pricing) |
| 免费额度 | [官方新人额度规则](https://help.aliyun.com/zh/model-studio/new-free-quota) |

项目示例暂用官方仍支持的旧兼容域名 `https://dashscope.aliyuncs.com/compatible-mode/v1`；官方当前推荐带 `WorkspaceId` 的地域域名，新项目应优先按官方表格选择。[官方兼容接口与迁移说明](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
response = client.chat.completions.create(
    model="qwen-flash",
    messages=[{"role": "user", "content": "你好"}],
)
print(response.choices[0].message.content)
```

Python SDK 关闭支持该能力模型的思考时，官方写法是 `extra_body={"enable_thinking": False}`；cURL 与 Node.js 的字段位置不同，应照官方语言示例使用。[官方 OpenAI 兼容文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

免费额度只适用于官方规则列出的地域、模型与期限；额度用完后的计费行为也以[官方新人额度规则](https://help.aliyun.com/zh/model-studio/new-free-quota)为准。

调用文件与官方出处见[型号说明书](../../models/qwen/qwen-flash/README.md)及[来源清单](../../models/qwen/qwen-flash/examples/sources.json)。测试记录只留维护者本地；安装与运行方式见[验证与复现](../验证与复现.md)。
