# DeepSeek 官方资料卡

核对日期：**2026-10-13**。厂商事实以 [DeepSeek API 文档](https://api-docs.deepseek.com/)为准；仓库实测口径见[来源与核验规则](../来源与核验规则.md)。

`deepseek-flash` 的参数、能力、价格快照与八个完整示例已经整理为独立的[模型级调用说明书](../../models/deepseek/deepseek-flash/README.md)。

| 项目 | 值与官方来源 |
|---|---|
| Key | [`DEEPSEEK_API_KEY`；管理页面](https://platform.deepseek.com/api_keys) |
| `base_url` | [`https://api.deepseek.com`](https://api-docs.deepseek.com/) |
| 项目默认模型 | [`deepseek-flash`](https://api-docs.deepseek.com/quick_start/pricing/) |
| 模型与价格 | [官方模型与价格页](https://api-docs.deepseek.com/quick_start/pricing/) |
| 思考模式 | [官方思考模式文档](https://api-docs.deepseek.com/guides/thinking_mode/) |
| 错误码 | [官方错误码](https://api-docs.deepseek.com/quick_start/error_codes/) |
| 版本变更 | [官方更新日志](https://api-docs.deepseek.com/updates/) |

官方价格页说明 `deepseek-flash` 当前由 DeepSeek-V4.1-Flash 提供服务；旧 `deepseek-v4-flash` 名称仍可调用，但旧 V4 Flash 已退役并临时路由到新版本。[官方模型与价格页](https://api-docs.deepseek.com/quick_start/pricing/)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)
response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": "你好"}],
)
print(response.choices[0].message.content)
```

关闭思考的官方写法是 `extra_body={"thinking": {"type": "disabled"}}`；思考内容在 `reasoning_content`，且思考模式会忽略部分采样参数。[官方思考文档](https://api-docs.deepseek.com/guides/thinking_mode/)

价格采用官方页面当前展示的币种与峰谷规则，本项目不复制数字，避免文档在价格调整后继续传播旧值。[官方模型与价格页](https://api-docs.deepseek.com/quick_start/pricing/)

仓库于 2026-10-13 验证了目录中记录的普通、流式和关闭思考调用；测试实现与限制见 [`tests/verify_calls.py`](../../tests/verify_calls.py)。
