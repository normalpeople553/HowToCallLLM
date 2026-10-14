# Kimi · 语言模型清单

[模型目录](../../models/README.md) · [English](../../en/docs/model-lists/kimi.md)

官方文档核对日期：2026-10-14。[官方目录](https://platform.kimi.com/docs/models) · [来源数据](../../data/model-lists/kimi.json)

范围为Kimi API开放平台当前目录的四个托管语言模型，不列已下线接入名；不混入Kimi会员、Kimi Code订阅或其他服务商的开源部署。

可用性是有日期的官方文档快照，不保证你账户具备权限，也不表示本次实际调用。定价入口不等于接入权限，限制见逐行说明。仓库覆盖按准确 ID 关联维护卡片和当前源码 HTTP 报告，不按别名或系列继承。

本清单以语言输出为范围；模态表示输入理解，不是图像/音频生成能力。出现在这里不自动扩展代码生成器支持的型号。

## 官方列出 / 受限 / 旧版入口

| 准确 API ID / 系列 | 生命周期 | 付费类型 | 输入 | 仓库覆盖 | 限制 / 官方出处 |
|---|---|---|---|---|---|
| [`kimi-k3`](https://platform.kimi.com/docs/guide/kimi-k3-quickstart) / Kimi K3 | 官方列为可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无逐文件实测证据 | 标准Kimi API按量计费；需充值解锁，新用户注册认证赠金不可用于K3，具体条件见官方访问说明；与Kimi Code订阅区分。 [型号](https://platform.kimi.com/docs/guide/kimi-k3-quickstart) · [价格](https://platform.kimi.com/docs/pricing/chat) · [出处 3](https://platform.kimi.com/docs/models) |
| [`kimi-k2.7-code`](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) / Kimi K2.7 Code | 官方列为可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无逐文件实测证据 | 编程语言模型，官方同时声明图片与视频理解输入。 [型号](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) · [价格](https://platform.kimi.com/docs/pricing/chat) · [出处 3](https://platform.kimi.com/docs/models) |
| [`kimi-k2.7-code-highspeed`](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) / Kimi K2.7 Code | 官方列为可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无逐文件实测证据 | 同一系列的高速服务入口；不把普通版实测继承为高速版实测。 [型号](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) · [价格](https://platform.kimi.com/docs/pricing/chat) · [出处 3](https://platform.kimi.com/docs/models) |
| [`kimi-k2.6`](../../models/kimi/kimi-k2.6/README.md) / Kimi K2.6 | 官方列为可用 | 付费 | 文本, 图片, 视频 | [说明书](../../models/kimi/kimi-k2.6/README.md) · [参数](../../models/kimi/kimi-k2.6/parameters.md) · [代码](../../models/kimi/kimi-k2.6/examples/01_basic.py) · [10/10 文件实测通过](../示例实测状态.md) · 项目默认 | 当前仓库维护的Kimi详细说明书目标；不代表其他Kimi型号沿用相同参数。 [型号](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) · [价格](https://platform.kimi.com/docs/pricing/chat) · [出处 3](https://platform.kimi.com/docs/models) |

[逐文件实测及证据边界](../示例实测状态.md)
