# DeepSeek · 语言模型清单

[全部厂商](README.md) · [English](../../en/docs/model-lists/deepseek.md)

官方文档核对日期：2026-10-14。[官方目录](https://api-docs.deepseek.com/quick_start/pricing/) · [来源数据](../../data/model-lists/deepseek.json)

范围为官方托管语言模型目录中的两个当前主入口，以及官方明确的旧别名和已退役接入名；不把展示的模型版本号或开源权重名猜成可调用API ID。目录可用性是官方文档状态，不保证任意账户当前有权限或服务容量。

可用性是有日期的官方文档快照，不保证你账户具备权限，也不表示本次实际调用。定价入口不等于接入权限，限制见逐行说明。仓库覆盖按准确 ID 关联维护卡片和当前源码 HTTP 报告，不按别名或系列继承。

本清单以语言输出为范围；模态表示输入理解，不是图像/音频生成能力。出现在这里不自动扩展代码生成器支持的型号。

## 官方列出 / 受限 / 旧版入口

| 准确 API ID / 系列 | 生命周期 | 付费类型 | 输入 | 仓库覆盖 | 限制 / 官方出处 |
|---|---|---|---|---|---|
| `deepseek-flash` / DeepSeek V4.1 Flash | 官方列为可用 | 付费 | 文本, 图片 | [说明书](../../models/deepseek/deepseek-flash/README.md) · [参数](../../models/deepseek/deepseek-flash/parameters.md) · [18/18 文件实测通过](../示例实测状态.md) · 项目默认 | 当前主入口；服务版本为DeepSeek-V4.1-Flash。 [型号](https://api-docs.deepseek.com/quick_start/pricing/) · [价格](https://api-docs.deepseek.com/quick_start/pricing/) |
| `deepseek-v4-pro` / DeepSeek V4 Pro | 官方列为可用 | 付费 | 文本 | 未维护详细说明书 · 无逐文件实测证据 | 官方API名称仍为deepseek-v4-pro；服务版本为DeepSeek-V4-Pro-0813，当前价格表标明不支持视觉输入。 [型号](https://api-docs.deepseek.com/quick_start/pricing/) · [价格](https://api-docs.deepseek.com/quick_start/pricing/) |
| `deepseek-v4-flash` / DeepSeek V4 Flash | 别名 / 重路由 | 付费 | 文本, 图片 | 未维护详细说明书 · 无逐文件实测证据 | 名称仍被接受，但原模型已退役；请求转由V4.1 Flash处理，不能把旧名称当成旧权重的验证。 [型号](https://api-docs.deepseek.com/quick_start/pricing/) · [价格](https://api-docs.deepseek.com/quick_start/pricing/) |
| `deepseek-v4-flash-vision-exp` / DeepSeek V4 Flash Vision | 别名 / 重路由 | 付费 | 文本, 图片 | 未维护详细说明书 · 无逐文件实测证据 | 旧实验名称仍被接受，但原模型已退役并转由V4.1 Flash处理。 [型号](https://api-docs.deepseek.com/quick_start/pricing/) · [价格](https://api-docs.deepseek.com/quick_start/pricing/) |

## 已下线或可用性未确认——不可据此认为能调用

| 准确 API ID / 系列 | 生命周期 | 付费类型 | 输入 | 仓库覆盖 | 限制 / 官方出处 |
|---|---|---|---|---|---|
| `deepseek-chat` / DeepSeek legacy API | 已下线 | 未确认 | 未确认 | 未维护详细说明书 · 无逐文件实测证据 | 官方公告：2026-07-24 15:59 UTC后退役且不可访问。历史教程中的名称不表示当前仍可调用。 [型号](https://api-docs.deepseek.com/news/news260424/) · [价格](https://api-docs.deepseek.com/quick_start/pricing/) |
| `deepseek-reasoner` / DeepSeek legacy API | 已下线 | 未确认 | 未确认 | 未维护详细说明书 · 无逐文件实测证据 | 官方公告：2026-07-24 15:59 UTC后退役且不可访问；不把旧思考模型名当成当前独立型号。 [型号](https://api-docs.deepseek.com/news/news260424/) · [价格](https://api-docs.deepseek.com/quick_start/pricing/) |

[逐文件实测及证据边界](../示例实测状态.md)
