# Language-model lists

[Model directory](../../../models/README.en.md) · [中文](../../../docs/model-lists/README.md)

Discovery only: these are official API IDs, not a claim that this repository has a detailed manual or live-tested code for every model.

Scope: chat, reasoning and coding language models, including multimodal understanding where officially documented. Excludes image/video generation, standalone speech, embeddings, rerankers and third-party hosted models. See each vendor's scope and account/region/access restrictions; this is not an account-specific /models response or an exhaustive historical archive.

Prices are linked to official pages, not frozen here. Free entries are discovery records only: maintained examples and generated defaults remain paid, with no silent fallback. Retired models are excluded from these lists and Agent queries. Unconfirmed availability appears separately and is not a recommendation to call.

Official lifecycle and input labels are dated documentation snapshots, not live API tests. A paid label is not proof of pay-as-you-go access; previews may require subscriptions. An alias does not inherit another ID's manual, parameters or code. Maintainer execution records remain local and are not published.

| Vendor | Checked | Listed IDs (retired excluded; includes uncertain) | Detailed manuals | Official catalog |
|---|---|---|---|---|
| [DeepSeek](deepseek.md) | 2026-10-15 | 4 | 2 | [Official](https://api-docs.deepseek.com/quick_start/pricing/) |
| [Kimi](kimi.md) | 2026-10-14 | 4 | 1 | [Official](https://platform.kimi.com/docs/models) |
| [Zhipu GLM](zhipu.md) | 2026-10-14 | 32 | 1 | [Official](https://docs.bigmodel.cn/cn/guide/start/model-overview) |
| [Qwen](qwen.md) | 2026-10-14 | 81 | 1 | [Official](https://help.aliyun.com/zh/model-studio/models) |
| [Doubao](doubao.md) | 2026-10-14 | 14 | 1 | [Official](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| [MiniMax](minimax.md) | 2026-10-14 | 6 | 1 | [Official](https://platform.minimax.cn/docs/faq/models) |

## Agent lookup

```bash
python skills/model-manual/scripts/model_catalog.py --vendor deepseek
python skills/model-manual/scripts/model_catalog.py --vendor deepseek --model deepseek-v4-pro
python skills/model-manual/scripts/model_catalog.py --billing paid --status available
```

Read-only, offline JSON; unknown exact IDs return an error, never another model. Results include official URLs, lifecycle, billing, input modalities, and separately derived exact-ID repository coverage. No credentials are read.

If no maintained card exists, verify that exact model's official API and parameters before implementation; the snippet generator does not automatically support it. Listed input modalities do not establish a common API format or guarantee semantic quality.

[Shared source data](../../../data/model-lists) · [Query / page generator](../../../skills/model-manual/scripts/model_catalog.py) · [Model directory](../../../models/README.en.md)
