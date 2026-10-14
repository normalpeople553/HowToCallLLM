# 04 · Pricing, quotas, and cost control

[中文](../../docs/04-免费额度与省钱攻略.md) · [Human guide](../../human/README.en.md)

Prices, free quotas, regions, and expiration dates change. The project therefore does not maintain a hand-copied total-price comparison that can quickly become stale. The following official pages are the source of truth when checking charges. [Evidence policy](evidence-policy.md)

| Vendor | Official pricing | Official free-quota or charging rules | Official model page |
|---|---|---|---|
| DeepSeek | [Models and pricing](https://api-docs.deepseek.com/quick_start/pricing/) | [Charging rules on the same page](https://api-docs.deepseek.com/quick_start/pricing/) | [Models and pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| Kimi | [Chat pricing](https://platform.kimi.com/docs/pricing/chat) | Refer to the pricing page and console. | [Model list](https://platform.kimi.com/docs/models) |
| Zhipu GLM | [Pricing and free-model status](https://docs.bigmodel.cn/cn/guide/start/pricing) | [Free labels on the same page](https://docs.bigmodel.cn/cn/guide/start/pricing) | [Model/pricing directory](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| Qwen | [Model pricing](https://help.aliyun.com/zh/model-studio/model-pricing) | [New-user free quota](https://help.aliyun.com/zh/model-studio/new-free-quota) | [Model list](https://help.aliyun.com/zh/model-studio/getting-started/models) |
| Doubao / Ark | [Model pricing](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) | [Free inference quota](https://docs.volcengine.com/docs/ark/free-inference-quota?lang=zh) | [Model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| MiniMax | [Pay-as-you-go pricing](https://platform.minimax.cn/docs/guides/pricing-paygo) | Refer to official billing and the relevant account; no free quota is promised here. | [Models and retirement notice](https://platform.minimax.cn/docs/guides/models-intro) |

## Project recommendations

These are project cost-control practices, not vendor promises. Their classification follows the [evidence policy](evidence-policy.md).

1. Before calling a model, open its official pricing page and check the model name, input/output rates, cache rates, region, and billing unit.
2. During development, select a reasonable output budget for the exact model and record `response.usage`. Do not universally hard-code the parameter name `max_tokens`; MiniMax recommends `max_completion_tokens` for new integrations. [DeepSeek Chat API](https://api-docs.deepseek.com/api/create-chat-completion/) · [MiniMax Chat API](https://platform.minimax.cn/docs/api-reference/text-chat-openai)
3. Choose thinking mode by task where the model supports a switch. For models that cannot disable thinking, plan the actual budget and output handling instead; M2.x ignores `disabled`. DeepSeek's switch is not a universal provider setting. [DeepSeek thinking](https://api-docs.deepseek.com/guides/thinking_mode/) · [MiniMax M2.x behavior](https://platform.minimax.cn/docs/api-reference/text-chat-openai)
4. Put application-side request caps, timeouts, and retry boundaries around batch work. These are engineering recommendations, not a claim that every vendor console offers equivalent controls. [Project policy](evidence-policy.md)
5. A free quota is not a promise of perpetual free service. Qwen's regions, expiration periods, and post-quota behavior follow its [official quota rules](https://help.aliyun.com/zh/model-studio/new-free-quota); Doubao's follow its [official quota rules](https://docs.volcengine.com/docs/ark/free-inference-quota?lang=zh).

Project defaults are simply defaults for runnable examples, not rankings of quality or value for money. Defaults and verification summaries are stored in [vendors.json](../../skills/model-manual/references/vendors.json).
