# Kimi · language-model list

[Model directory](../../../models/README.en.md) · [中文](../../../docs/model-lists/kimi.md)

Official documentation checked: 2026-10-14. [Official catalog](https://platform.kimi.com/docs/models) · [Source data](../../../data/model-lists/kimi.json)

Covers the four hosted language models in the current Kimi API catalog, excluding retired API names. Kimi memberships, Kimi Code subscriptions, and third-party open-weight deployments are separate products.

Availability is a dated official-document snapshot, not an account-level or live-call guarantee. Billing links do not imply API access; read each row's restrictions. Coverage joins exact IDs to public manuals, parameters and code, never private execution records or another alias/family's coverage.

Text output is the scope; modality labels describe input understanding, not image/audio generation. No entry here expands the snippet generator's supported models.

## Documented / restricted / legacy entries

| Exact API ID / family | Lifecycle | Billing | Input | Repository coverage | Restrictions / official sources |
|---|---|---|---|---|---|
| [`kimi-k3`](https://platform.kimi.com/docs/guide/kimi-k3-quickstart) / Kimi K3 | Officially listed | Paid | text, image, video | No maintained manual · No maintained example | Metered standard Kimi API. A top-up is required to unlock K3; new-user registration/verification promotional credit cannot be used for K3. Check official access conditions. Kimi Code subscriptions are separate. [Model](https://platform.kimi.com/docs/guide/kimi-k3-quickstart) · [Pricing](https://platform.kimi.com/docs/pricing/chat) · [Source 3](https://platform.kimi.com/docs/models) |
| [`kimi-k2.7-code`](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) / Kimi K2.7 Code | Officially listed | Paid | text, image, video | No maintained manual · No maintained example | Coding language model with explicitly documented image and video inputs. [Model](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) · [Pricing](https://platform.kimi.com/docs/pricing/chat) · [Source 3](https://platform.kimi.com/docs/models) |
| [`kimi-k2.7-code-highspeed`](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) / Kimi K2.7 Code | Officially listed | Paid | text, image, video | No maintained manual · No maintained example | High-speed service entry for the same family; normal-entry test evidence is not inherited. [Model](https://platform.kimi.com/docs/guide/kimi-k2-7-code-quickstart) · [Pricing](https://platform.kimi.com/docs/pricing/chat) · [Source 3](https://platform.kimi.com/docs/models) |
| [`kimi-k2.6`](../../../models/kimi/kimi-k2.6/README.en.md) / Kimi K2.6 | Officially listed | Paid | text, image, video | [Manual](../../../models/kimi/kimi-k2.6/README.en.md) · [Parameters](../../../models/kimi/kimi-k2.6/parameters.en.md) · [Code](../../../models/kimi/kimi-k2.6/examples/01_basic.py) · Project default | The Kimi model with a maintained detailed manual here; its parameters do not automatically apply to other models. [Model](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) · [Pricing](https://platform.kimi.com/docs/pricing/chat) · [Source 3](https://platform.kimi.com/docs/models) |

[Source and verification boundaries](../evidence-policy.md)
