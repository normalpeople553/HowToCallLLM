# Kimi · language-model list

[All vendors](README.md) · [中文](../../../docs/model-lists/kimi.md)

Official documentation checked: 2026-10-14. [Official catalog](https://platform.kimi.com/docs/models) · [Source data](../../../data/model-lists/kimi.json)

Covers the four hosted language models in the current Kimi API catalog, excluding retired API names. Kimi memberships, Kimi Code subscriptions, and third-party open-weight deployments are separate products.

Availability is a dated official-document snapshot, not an account-level or live-call guarantee. Billing links do not imply API access; read each row's restrictions. Coverage is joined by exact ID from maintained cards and current-source HTTP reports, not inherited through aliases or family names.

Text output is the scope; modality labels describe input understanding, not image/audio generation. No entry here expands the snippet generator's supported models.

## Documented / restricted / legacy entries

| Exact API ID / family | Lifecycle | Billing | Input | Repository coverage | Restrictions / official sources |
|---|---|---|---|---|---|
| `kimi-k3` / Kimi K3 | Officially listed | Paid | text, image, video | No maintained manual · No per-file live evidence | Metered standard Kimi API. A top-up is required to unlock K3; new-user registration/verification promotional credit cannot be used for K3. Check official access conditions. Kimi Code subscriptions are separate. [Model](https://platform.kimi.com/docs/guide/kimi-k3-quickstart) · [Pricing](https://platform.kimi.com/docs/pricing/chat) · [Source 3](https://platform.kimi.com/docs/models) |
| `kimi-k2.7-code` / Kimi K2.7 Code | Officially listed | Paid | text, image, video | No maintained manual · No per-file live evidence | Coding language model with explicitly documented image and video inputs. [Model](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) · [Pricing](https://platform.kimi.com/docs/pricing/chat) · [Source 3](https://platform.kimi.com/docs/models) |
| `kimi-k2.7-code-highspeed` / Kimi K2.7 Code | Officially listed | Paid | text, image, video | No maintained manual · No per-file live evidence | High-speed service entry for the same family; normal-entry test evidence is not inherited. [Model](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) · [Pricing](https://platform.kimi.com/docs/pricing/chat) · [Source 3](https://platform.kimi.com/docs/models) |
| `kimi-k2.6` / Kimi K2.6 | Officially listed | Paid | text, image, video | [Manual](../../../models/kimi/kimi-k2.6/README.en.md) · [Parameters](../../../models/kimi/kimi-k2.6/parameters.en.md) · [10/10 files passed](../example-status.md) · Project default | The Kimi model with a maintained detailed manual here; its parameters do not automatically apply to other models. [Model](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) · [Pricing](https://platform.kimi.com/docs/pricing/chat) · [Source 3](https://platform.kimi.com/docs/models) |

[Per-file live evidence and limits](../example-status.md)
