# Doubao / Volcengine Ark: official-source reference

[中文](../../../docs/03-厂商攻略/doubao.md) · [Human guide](../../../human/README.en.md)

See the [Doubao language-model list](../model-lists/doubao.md) for other exact IDs, lifecycle, input modalities and official pricing. Distinguish metered APIs, subscription shorthand and retired versions; a listing does not imply a detailed manual or live-call evidence.

Source verification date: **2026-10-13**. Vendor facts follow the official Ark documentation; repository testing terminology follows the [evidence policy](../evidence-policy.md).

| Item | Value and official source |
|---|---|
| Key | [`ARK_API_KEY`; management page](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) |
| Model activation | [Official activation management](https://docs.volcengine.com/docs/ark/activation-management?lang=zh) |
| `base_url` | [`https://ark.cn-beijing.volces.com/api/v3`](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) |
| Project default | [`doubao-seed-2-1-pro-260628`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| Models | [Official model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| Pricing | [Official pricing](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| Free quota | [Official free inference quota](https://docs.volcengine.com/docs/ark/free-inference-quota?lang=zh) |

The online-inference documentation permits direct Model ID calls. Activation requirements, current IDs, and available regions must still be checked in activation management and the model list. [Online inference](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) · [Activation](https://docs.volcengine.com/docs/ark/activation-management?lang=zh) · [Models](https://docs.volcengine.com/docs/ark/model-list?lang=zh)

Use the shared executable [01_basic.py](../../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py) for the environment key, endpoint, exact model above, and text-`messages` pattern. This translation does not modify the underlying prompt or add another API script.

```bash
python models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py
```

This page does not copy price or free-quota numbers. Check the [official pricing](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) and [quota rules](https://docs.volcengine.com/docs/ark/free-inference-quota?lang=zh).

The historical basic verification for `doubao-seed-2-1-pro-260628` covered ordinary requests, streaming, thinking switches, JSON Schema, initial tool calls, and image-request shape. It did not verify image-content recognition or tool-result return. [Historical redacted report](../../../models/doubao/doubao-seed-2-1-pro-260628/verification/2026-10-13.json) Consult [unified verification status](../verification-status.md) for results and the [model manual](../../../models/doubao/doubao-seed-2-1-pro-260628/README.en.md) for complete examples. Do not generalize these results to other models.
