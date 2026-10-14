# DeepSeek · language-model list

[Model directory](../../../models/README.en.md) · [中文](../../../docs/model-lists/deepseek.md)

Official documentation checked: 2026-10-14. [Official catalog](https://api-docs.deepseek.com/quick_start/pricing/) · [Source data](../../../data/model-lists/deepseek.json)

Covers the two current hosted language-model entry points and explicitly documented legacy aliases that still accept requests. Retired API names are excluded. Displayed model versions and open-weight names are not invented API IDs. Availability is a documentation state, not proof of current account access or service capacity.

Availability is a dated official-document snapshot, not an account-level or live-call guarantee. Billing links do not imply API access; read each row's restrictions. Coverage joins exact IDs to public manuals, parameters and code, never private execution records or another alias/family's coverage.

Text output is the scope; modality labels describe input understanding, not image/audio generation. No entry here expands the snippet generator's supported models.

## Documented / restricted / legacy entries

| Exact API ID / family | Lifecycle | Billing | Input | Repository coverage | Restrictions / official sources |
|---|---|---|---|---|---|
| [`deepseek-flash`](../../../models/deepseek/deepseek-flash/README.en.md) / DeepSeek V4.1 Flash | Officially listed | Paid | text, image | [Manual](../../../models/deepseek/deepseek-flash/README.en.md) · [Parameters](../../../models/deepseek/deepseek-flash/parameters.en.md) · [Code](../../../models/deepseek/deepseek-flash/examples/01_basic.py) · Project default | Current entry point, served as DeepSeek-V4.1-Flash. [Model](https://api-docs.deepseek.com/quick_start/pricing/) · [Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| [`deepseek-v4-pro`](https://api-docs.deepseek.com/quick_start/pricing/) / DeepSeek V4 Pro | Officially listed | Paid | text | No maintained manual · No maintained example | The API ID remains deepseek-v4-pro; the served version is DeepSeek-V4-Pro-0813. The current table excludes vision input. [Model](https://api-docs.deepseek.com/quick_start/pricing/) · [Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| [`deepseek-v4-flash`](https://api-docs.deepseek.com/quick_start/pricing/) / DeepSeek V4 Flash | Alias / rerouted | Paid | text, image | No maintained manual · No maintained example | The name is accepted, but its original model is retired. Requests route to V4.1 Flash, so the alias does not prove execution of old weights. [Model](https://api-docs.deepseek.com/quick_start/pricing/) · [Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| [`deepseek-v4-flash-vision-exp`](https://api-docs.deepseek.com/quick_start/pricing/) / DeepSeek V4 Flash Vision | Alias / rerouted | Paid | text, image | No maintained manual · No maintained example | The old experimental name is accepted but its original model is retired and requests route to V4.1 Flash. [Model](https://api-docs.deepseek.com/quick_start/pricing/) · [Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |

[Source and verification boundaries](../evidence-policy.md)
