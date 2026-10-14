# Model manuals

[中文](README.md) · [Human guide](../human/README.en.md)

English translation of the [Chinese model index](README.md). Both languages share the same executable code, model cards, source manifests and reports. Official source URLs are retained, including Chinese-language pages; translating this index does not rerun or revalidate an API.

Each exact model has its own manual and examples. Machine-readable facts remain in [`skills/model-manual/references/models/`](../skills/model-manual/references/models/), under the [evidence policy](../en/docs/evidence-policy.md).

| Exact model | Manual | Parameter reference |
|---|---|---|
| DeepSeek `deepseek-flash` | [Manual](deepseek/deepseek-flash/README.en.md) | [Parameters](deepseek/deepseek-flash/parameters.en.md) |
| Kimi `kimi-k2.6` | [Manual](kimi/kimi-k2.6/README.en.md) | [Parameters](kimi/kimi-k2.6/parameters.en.md) |
| Zhipu `glm-4.7` | [Manual](zhipu/glm-4.7/README.en.md) | [Parameters](zhipu/glm-4.7/parameters.en.md) |
| Qwen `qwen-flash` | [Manual](qwen/qwen-flash/README.en.md) | [Parameters](qwen/qwen-flash/parameters.en.md) |
| Doubao `doubao-seed-2-1-pro-260628` | [Manual](doubao/doubao-seed-2-1-pro-260628/README.en.md) | [Parameters](doubao/doubao-seed-2-1-pro-260628/parameters.en.md) |
| MiniMax `MiniMax-M2.7` | [Manual](minimax/MiniMax-M2.7/README.en.md) | [Parameters](minimax/MiniMax-M2.7/parameters.en.md) |

Zhipu now targets the same-generation paid `glm-4.7`; it does not inherit evidence from the old free Flash model. Check [per-file results](../en/docs/example-status.md). Doubao's ID is listed as a past model in its [official model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh). MiniMax has an [official retirement notice](https://platform.minimax.cn/docs/guides/models-intro); its per-file execution evidence is separate from the historical unified verifier.

Project rule: all maintained models above are paid, with no default free-model fallback. Official pricing links and selection evidence are in the cards and [evidence policy](../en/docs/evidence-policy.md). Each manual covers identity and lifecycle, connection configuration, capabilities and limitations, official pricing links, basic/streaming requests, thinking, structured output, tools, multimodal inputs, errors and production checks where documented. Undocumented capabilities remain unknown, not automatically supported or unsupported.

For output truncation, thinking tokens, JSON validation, tool loops, streaming and rate limits across models, see [production pitfalls](../en/docs/production-pitfalls.md). Use the locked environment in [verification and reproduction](../en/docs/verification.md).

Read [per-file execution status](../en/docs/example-status.md) for current source-specific evidence and [historical verification status](../en/docs/verification-status.md) for the older unified capability checks. A file, a documentation fragment and a generated parameter combination do not inherit one another's successful result.

Browse the [official example index](../en/docs/example-index.md), or read each model's shared `examples/sources.json` for exact files, official sources, input variables, commands, adaptations and verification scope. Source manifests and historical reports are maintained separately; new files do not inherit old passes. Parameter explanations are indexed in the [parameter guide](../en/docs/parameters.md).
