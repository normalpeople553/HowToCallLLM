# 豆包 · 语言模型清单

[模型目录](../../models/README.md) · [English](../../en/docs/model-lists/doubao.md)

官方文档核对日期：2026-10-14。[官方目录](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [来源数据](../../data/model-lists/doubao.json)

范围为中国内地火山方舟按量 API：收录核对日官方模型列表文本生成栏的豆包自研 Model ID，含角色、翻译及多模态理解语言模型；已下线版本不列入，也不作为历史档案。排除转售型号、图像/视频/3D 生成、独立语音服务、向量、重排、纯 OCR 和单一意图分类器。Coding/Agent Plan 的入口、短名称和生命周期须另查订阅文档，不与按量 API 混用。往期、EOM 与 EOS 分开判断，价目中出现不等于可用；实际权限以地域、账户及控制台为准。本表是官方资料核对而非 API 实测，不包含固定价格或调用参数上限。

可用性是有日期的官方文档快照，不保证你账户具备权限，也不表示本次实际调用。定价入口不等于接入权限，限制见逐行说明。仓库覆盖只按准确 ID 关联公开说明书、参数和代码，不读取私有实测记录，也不按别名或系列继承。

本清单以语言输出为范围；模态表示输入理解，不是图像/音频生成能力。出现在这里不自动扩展代码生成器支持的型号。

## 官方列出 / 受限 / 旧版入口

| 准确 API ID / 系列 | 生命周期 | 付费类型 | 输入 | 仓库覆盖 | 限制 / 官方出处 |
|---|---|---|---|---|---|
| [`doubao-seed-evolving`](https://docs.volcengine.com/docs/ark/latest-model?lang=zh) / Doubao Seed Evolving | 别名 / 重路由 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 统一 Model ID 指向持续更新的模型服务，不是固定快照；当前官方列为推荐型号。支持视觉理解，不支持音频理解；本表不把 Coding Plan 的短名称当作按量 API 别名。 [型号](https://docs.volcengine.com/docs/ark/latest-model?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) · [出处 1](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| [`doubao-seed-2-1-pro-260915`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed 2.1 | 官方列为可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 官方推荐的固定版本 Model ID；此处状态针对方舟按量 API，不代表订阅套餐的模型范围。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| [`doubao-seed-2-1-lite-260915`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed 2.1 | 官方列为可用 | 付费 | 文本, 图片, 视频, 音频 | 未维护详细说明书 · 无维护示例 | 官方推荐型号；模型表分别列出视觉理解与音频理解。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| [`doubao-seed-2-1-turbo-260628`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed 2.1 | 官方列为可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 按量 API 模型表仍列为推荐型号；不要套用 Coding Plan 同名短名称的下线公告。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| [`doubao-seed-2-1-pro-260628`](../../models/doubao/doubao-seed-2-1-pro-260628/README.md) / Doubao Seed 2.1 | 旧版仍列可用 | 付费 | 文本, 图片, 视频 | [说明书](../../models/doubao/doubao-seed-2-1-pro-260628/README.md) · [参数](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.md) · [代码](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py) · 项目默认 | 官方归入往期模型，仍列于可调用模型表；不是 260915 版本，也不是本次新增实测。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| [`doubao-seed-2-0-lite-260428`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed 2.0 | 旧版仍列可用 | 付费 | 文本, 图片, 视频, 音频 | 未维护详细说明书 · 无维护示例 | 官方归入往期模型；音频理解表仍明确列出此版本。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| [`doubao-seed-2-0-mini-260428`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed 2.0 | 旧版仍列可用 | 付费 | 文本, 图片, 视频, 音频 | 未维护详细说明书 · 无维护示例 | 官方归入往期模型；音频理解表仍明确列出此版本。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| [`doubao-seed-2-0-pro-260215`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed 2.0 | 旧版仍列可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 已于 2026-09-24 EOM，不能新建旧版服务；EOS 为 2026-11-24 14:00（UTC+8）。核对日尚未到 EOS，不标为已下线。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) · [出处 3](https://docs.volcengine.com/docs/ark/model-deprecation-notice?lang=zh) |
| [`doubao-seed-2-0-lite-260215`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed 2.0 | 旧版仍列可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 已于 2026-09-24 EOM；该版本适用提前的 EOS：2026-10-22 14:00（UTC+8），不是同批公告的通用 11 月日期。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) · [出处 3](https://docs.volcengine.com/docs/ark/model-deprecation-notice?lang=zh) |
| [`doubao-seed-2-0-mini-260215`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed 2.0 | 旧版仍列可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 已于 2026-09-24 EOM；该版本适用提前的 EOS：2026-10-22 14:00（UTC+8），不是同批公告的通用 11 月日期。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) · [出处 3](https://docs.volcengine.com/docs/ark/model-deprecation-notice?lang=zh) |
| [`doubao-seed-2-0-code-preview-260215`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed 2.0 Code | 预览 / 受限入口 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 预览版本，官方仍列于往期模型；已于 2026-09-24 EOM，EOS 为 2026-11-24 14:00（UTC+8）。preview 标签不表示可向新用户开放。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) · [出处 3](https://docs.volcengine.com/docs/ark/model-deprecation-notice?lang=zh) |
| [`doubao-seed-character-260628`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed Character | 旧版仍列可用 | 付费 | 文本, 图片, 视频 | 未维护详细说明书 · 无维护示例 | 角色模型；官方文本与视觉能力表列出此准确 ID，不与不支持思考的 251128 文本版本合并。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| [`doubao-seed-character-251128`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed Character | 旧版仍列可用 | 付费 | 文本 | 未维护详细说明书 · 无维护示例 | 往期文本角色模型；官方明确该版本不支持深度思考。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| [`doubao-seed-translation-250915`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) / Doubao Seed Translation | 旧版仍列可用 | 付费 | 文本 | 未维护详细说明书 · 无维护示例 | 官方文本生成栏中的翻译增强语言模型，不是独立语音、OCR 或向量接口。 [型号](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |

[来源与核验边界](../来源与核验规则.md)
