# MiniMax · 语言模型清单

[模型目录](../../models/README.md) · [English](../../en/docs/model-lists/minimax.md)

官方文档核对日期：2026-10-14。[官方目录](https://platform.minimax.cn/docs/faq/models) · [来源数据](../../data/model-lists/minimax.json)

核对中国国内 MiniMax 官方托管语言 API 的当前模型列表、调用指南、计费及下线通知，覆盖其列出的 M 系列对话、推理、编程与多模态理解型号；已下线语言型号不列入。不宣称穷尽此前已从目录移除的 abab/Text-01 等历史档案，也不把本地开源权重当作托管 API 可用证据。按量 API、M Plan 与 Token Plan 的密钥、计费及路由必须分开看；仅订阅可用的预览型号已逐项注明，不推断国际站账户或其他区域权限。排除转售、图像/视频/音乐生成、独立语音、向量、重排及纯 OCR。本表无固定价格、参数上限或新增调用实测，模型状态以生命周期通知而非价目残留为依据。

可用性是有日期的官方文档快照，不保证你账户具备权限，也不表示本次实际调用。定价入口不等于接入权限，限制见逐行说明。仓库覆盖只按准确 ID 关联公开说明书、参数和代码，不读取私有实测记录，也不按别名或系列继承。

本清单以语言输出为范围；模态表示输入理解，不是图像/音频生成能力。出现在这里不自动扩展代码生成器支持的型号。

## 官方列出 / 受限 / 旧版入口

| 准确 API ID / 系列 | 生命周期 | 付费类型 | 输入 | 仓库覆盖 | 限制 / 官方出处 |
|---|---|---|---|---|---|
| [`MiniMax-M3.1-Flash-Preview`](https://platform.minimax.cn/docs/guides/text-generation) / MiniMax M3.1 | 预览 / 受限入口 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 目前仅通过 M Plan 和 MiniMax Code 提供，不是普通按量 API 可用型号；M Plan 订阅 Key 与普通按量 API Key 不通用。Token Plan 老用户安排另见订阅公告；其他型号名称重路由到此模型也不代表执行了原型号。 [型号](https://platform.minimax.cn/docs/guides/text-generation) · [价格](https://www.minimax.cn/m-plan) · [出处 3](https://platform.minimax.cn/docs/faq/models) · [出处 4](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [出处 5](https://platform.minimax.cn/docs/m-plan/intro) · [出处 6](https://platform.minimax.cn/docs/m-plan/quickstart) · [出处 7](https://platform.minimax.cn/docs/m-plan/token-plan-notice) |
| [`MiniMax-M3`](https://platform.minimax.cn/docs/guides/text-generation) / MiniMax M3 | 官方列为可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 官方可用语言模型及按量计费页均列出此准确 ID；图片和视频输入由 Chat Completions API 明确支持，不从其他模态生成产品推断。 [型号](https://platform.minimax.cn/docs/guides/text-generation) · [价格](https://platform.minimax.cn/docs/guides/pricing-paygo) · [出处 3](https://platform.minimax.cn/docs/faq/models) · [出处 4](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| [`MiniMax-M2.7`](../../models/minimax/MiniMax-M2.7/README.md) / MiniMax M2.7 | 官方列为可用 | 付费 | 文本 | [说明书](../../models/minimax/MiniMax-M2.7/README.md) · [参数](../../models/minimax/MiniMax-M2.7/parameters.md) · [代码](../../models/minimax/MiniMax-M2.7/examples/01_basic.py) · 项目默认 | 官方仍列为可用语言模型；按量付费 API：2026-10-19 起停止向新用户开放，存量用户可继续调用至 2026-11-18 正式下线，核对日尚未下线。M Plan/Token Plan：2026-10-19 起该名称的请求统一路由至 MiniMax-M3.1-Flash-Preview，名称仅保留为兼容入口；不能把订阅重路由提前算作按量 API 下线。 [型号](https://platform.minimax.cn/docs/guides/text-generation) · [价格](https://platform.minimax.cn/docs/guides/pricing-paygo) · [出处 3](https://platform.minimax.cn/docs/faq/models) · [出处 4](https://platform.minimax.cn/docs/guides/models-intro) · [出处 5](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| [`MiniMax-M2.7-highspeed`](https://platform.minimax.cn/docs/guides/text-generation) / MiniMax M2.7 | 官方列为可用 | 付费 | 文本 | 未维护详细说明书 · 无维护示例 | 官方仍列为可用语言模型；按量付费 API：2026-10-19 起停止向新用户开放，存量用户可继续调用至 2026-11-18 正式下线，核对日尚未下线。M Plan/Token Plan：2026-10-19 起该名称的请求统一路由至 MiniMax-M3.1-Flash-Preview，名称仅保留为兼容入口；不能把订阅重路由提前算作按量 API 下线。 [型号](https://platform.minimax.cn/docs/guides/text-generation) · [价格](https://platform.minimax.cn/docs/guides/pricing-paygo) · [出处 3](https://platform.minimax.cn/docs/faq/models) · [出处 4](https://platform.minimax.cn/docs/guides/models-intro) · [出处 5](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| [`MiniMax-M2.5`](https://platform.minimax.cn/docs/guides/text-generation) / MiniMax M2.5 | 旧版仍列可用 | 付费 | 文本 | 未维护详细说明书 · 无维护示例 | 官方模型调用页列为历史版本，但可用模型 FAQ 仍列为可用；按量付费 API：2026-10-19 起停止向新用户开放，存量用户可继续调用至 2026-11-18 正式下线，核对日尚未下线。M Plan/Token Plan：2026-10-19 起该名称的请求统一路由至 MiniMax-M3.1-Flash-Preview，名称仅保留为兼容入口；不能把订阅重路由提前算作按量 API 下线。 [型号](https://platform.minimax.cn/docs/guides/text-generation) · [价格](https://platform.minimax.cn/docs/guides/pricing-paygo) · [出处 3](https://platform.minimax.cn/docs/faq/models) · [出处 4](https://platform.minimax.cn/docs/guides/models-intro) · [出处 5](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| [`MiniMax-M2.5-highspeed`](https://platform.minimax.cn/docs/guides/text-generation) / MiniMax M2.5 | 旧版仍列可用 | 付费 | 文本 | 未维护详细说明书 · 无维护示例 | 官方模型调用页列为历史版本，但可用模型 FAQ 仍列为可用；按量付费 API：2026-10-19 起停止向新用户开放，存量用户可继续调用至 2026-11-18 正式下线，核对日尚未下线。M Plan/Token Plan：2026-10-19 起该名称的请求统一路由至 MiniMax-M3.1-Flash-Preview，名称仅保留为兼容入口；不能把订阅重路由提前算作按量 API 下线。 [型号](https://platform.minimax.cn/docs/guides/text-generation) · [价格](https://platform.minimax.cn/docs/guides/pricing-paygo) · [出处 3](https://platform.minimax.cn/docs/faq/models) · [出处 4](https://platform.minimax.cn/docs/guides/models-intro) · [出处 5](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |

[来源与核验边界](../来源与核验规则.md)
