# MiniMax

[English](../../en/docs/vendors/minimax.md)

已收录 [`MiniMax-M2.7` 调用说明书](../../models/minimax/MiniMax-M2.7/README.md)：国区 Chat Completions、用户原生 cURL、思考输出、流式、多轮和工具闭环；示例与官方出处见[功能索引](../官方示例索引.md)。

官方已公告 M2.7 系列于 2026-10-19 停止向新用户开放、2026-11-18 按量 API 下线；M Plan/Token Plan 从 10-19 起旧名请求路由到 M3.1 Flash Preview。[生命周期公告](https://platform.minimax.cn/docs/guides/models-intro)

| 用途 | 官方入口 |
|---|---|
| 国区兼容接口与模型参数 | [Chat Completions](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| SDK、型号、完整工具消息历史 | [OpenAI SDK](https://platform.minimax.cn/docs/api-reference/text-openai-api) |
| 旧原生 `/text/chatcompletion_v2` | [文本合成（deprecated）](https://platform.minimax.cn/docs/api-reference/text-post) |
| 密钥 | [官方密钥管理](https://platform.minimax.cn/console/access?tab=api-keys) |
| 费用 | [官方按量计费](https://platform.minimax.cn/docs/guides/pricing-paygo) |

参数逐项解释及每个实际文件的字段映射见[M2.7 参数说明](../../models/minimax/MiniMax-M2.7/parameters.md)。实测按两层查阅：[历史统一流程状态](../验证状态.md)目前没有此型号的统一验证器报告，[逐文件示例实测状态](../示例实测状态.md)单独记录原始示例的真实执行，不能用前者的空缺推断从未调用，也不能继承其他厂商或任意参数组合的结果。[证据规则](../来源与核验规则.md)
