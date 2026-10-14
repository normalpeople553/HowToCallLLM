# DeepSeek · language-model list

[All vendors](README.md) · [中文](../../../docs/model-lists/deepseek.md)

Official documentation checked: 2026-10-14. [Official catalog](https://api-docs.deepseek.com/quick_start/pricing/) · [Source data](../../../data/model-lists/deepseek.json)

Covers the two current hosted language-model entry points and explicitly documented legacy aliases that still accept requests. Retired API names are excluded. Displayed model versions and open-weight names are not invented API IDs. Availability is a documentation state, not proof of current account access or service capacity.

Availability is a dated official-document snapshot, not an account-level or live-call guarantee. Billing links do not imply API access; read each row's restrictions. Coverage is joined by exact ID from maintained cards and current-source HTTP reports, not inherited through aliases or family names.

Text output is the scope; modality labels describe input understanding, not image/audio generation. No entry here expands the snippet generator's supported models.

## Documented / restricted / legacy entries

| Exact API ID / family | Lifecycle | Billing | Input | Repository coverage | Restrictions / official sources |
|---|---|---|---|---|---|
| `deepseek-flash` / DeepSeek V4.1 Flash | Officially listed | Paid | text, image | [Manual](../../../models/deepseek/deepseek-flash/README.en.md) · [Parameters](../../../models/deepseek/deepseek-flash/parameters.en.md) · [18/18 files passed](../example-status.md) · Project default | Current entry point, served as DeepSeek-V4.1-Flash. [Model](https://api-docs.deepseek.com/quick_start/pricing/) · [Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| `deepseek-v4-pro` / DeepSeek V4 Pro | Officially listed | Paid | text | No maintained manual · No per-file live evidence | The API ID remains deepseek-v4-pro; the served version is DeepSeek-V4-Pro-0813. The current table excludes vision input. [Model](https://api-docs.deepseek.com/quick_start/pricing/) · [Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| `deepseek-v4-flash` / DeepSeek V4 Flash | Alias / rerouted | Paid | text, image | No maintained manual · No per-file live evidence | The name is accepted, but its original model is retired. Requests route to V4.1 Flash, so the alias does not prove execution of old weights. [Model](https://api-docs.deepseek.com/quick_start/pricing/) · [Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| `deepseek-v4-flash-vision-exp` / DeepSeek V4 Flash Vision | Alias / rerouted | Paid | text, image | No maintained manual · No per-file live evidence | The old experimental name is accepted but its original model is retired and requests route to V4.1 Flash. [Model](https://api-docs.deepseek.com/quick_start/pricing/) · [Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |

[Per-file live evidence and limits](../example-status.md)
