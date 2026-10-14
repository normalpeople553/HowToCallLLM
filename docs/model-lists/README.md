# 语言模型清单

[English](../../en/docs/model-lists/README.md)

这是官方 API 型号的发现清单，不表示仓库已为每个型号维护详细说明书或完成真实调用。

范围：对话、推理、编程语言模型，包含有官方依据的多模态理解；不含图片/视频生成、独立语音、Embedding、Rerank 和第三方托管型号。各厂商的完整性、账户、地域和接入限制见各页；不是你账户的 /models 返回，也不是所有历史版本的档案。

价格只链接官方页面，不在这里固化数字。免费条目仅用于发现：维护示例和生成器默认仍全部采用付费型号，不静默回退。已下线型号不出现在清单和 Agent 查询中；可用性未确认的条目单列，不作为调用建议。

官方生命周期和输入标签是核对日的文档快照，不是在线调用测试。“付费”不等于可以按量接入，预览可能仅限订阅。别名不继承另一个 ID 的说明书、参数或实测。

| 厂商 | 核对日期 | 收录 ID（不含已下线；含待确认） | 详细说明书 | 官方目录 |
|---|---|---|---|---|
| [DeepSeek](deepseek.md) | 2026-10-14 | 4 | 1 | [Official](https://api-docs.deepseek.com/quick_start/pricing/) |
| [Kimi](kimi.md) | 2026-10-14 | 4 | 1 | [Official](https://platform.kimi.com/docs/models) |
| [智谱 GLM](zhipu.md) | 2026-10-14 | 32 | 1 | [Official](https://docs.bigmodel.cn/cn/guide/start/model-overview) |
| [通义千问](qwen.md) | 2026-10-14 | 81 | 1 | [Official](https://help.aliyun.com/zh/model-studio/models) |
| [豆包](doubao.md) | 2026-10-14 | 14 | 1 | [Official](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| [MiniMax](minimax.md) | 2026-10-14 | 6 | 1 | [Official](https://platform.minimax.cn/docs/faq/models) |

## Agent 查询

```bash
python skills/model-manual/scripts/model_catalog.py --vendor deepseek
python skills/model-manual/scripts/model_catalog.py --vendor deepseek --model deepseek-v4-pro
python skills/model-manual/scripts/model_catalog.py --billing paid --status available
```

只读、离线输出 JSON；准确 ID 未命中时返回错误，不替换成其他型号。结果含官方来源、生命周期、付费类型、输入模态，以及按准确 ID 独立派生的仓库覆盖。不读取密钥。

没有维护卡片的型号，需要先查该准确型号的官方 API 和参数再实现；代码生成器不会自动支持它。输入模态不代表各厂商格式相同，也不保证语义效果。

[共享来源数据](../../data/model-lists) · [查询 / 页面生成器](../../skills/model-manual/scripts/model_catalog.py) · [维护中的说明书](../../models/README.md)
