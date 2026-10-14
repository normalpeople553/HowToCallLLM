# Zhipu GLM: official-source reference

[中文](../../../docs/03-厂商攻略/zhipu.md) · [Human guide](../../../human/README.en.md)

See the [Zhipu language-model list](../model-lists/zhipu.md) for other exact IDs, lifecycle, input modalities and official pricing. Free entries are discovery only and do not change paid defaults; a listing does not imply a detailed manual or live-call evidence.

Source verification date: **2026-10-14**. Vendor facts follow the [Zhipu documentation](https://docs.bigmodel.cn/llms.txt); repository testing terminology follows the [evidence policy](../evidence-policy.md).

| Item | Value and official source |
|---|---|
| Key | [`ZHIPU_API_KEY`; management page](https://bigmodel.cn/usercenter/apikeys) |
| `base_url` | [`https://open.bigmodel.cn/api/paas/v4`](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| Project default | [Paid `glm-4.7`](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| Models and pricing | [Official pricing](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| OpenAI SDK | [Official compatibility guide](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| Thinking | [Official thinking-mode guide](https://docs.bigmodel.cn/cn/guide/capabilities/thinking) |

Use the canonical runnable [01_basic.py](../../../models/zhipu/glm-4.7/examples/01_basic.py) and the [paid model's parameter reference](../../../models/zhipu/glm-4.7/parameters.en.md). Install locked dependencies and configure `ZHIPU_API_KEY`, then run from the repository root:

```bash
python models/zhipu/glm-4.7/examples/01_basic.py
```

Project rule: free `glm-4.7-flash` is no longer the Zhipu default, and failed paid-model calls do not fall back to it. Follow the [official pricing page](https://docs.bigmodel.cn/cn/guide/start/pricing) for `glm-4.7`; do not copy fixed prices. [Selection policy](../evidence-policy.md)

Balance is not concurrency allowance. Zhipu code `1302` means an account rate limit, `1305` platform overload, and `1113` account arrears; paid models are not guaranteed to avoid rate limits. [Official rate limits](https://docs.bigmodel.cn/cn/api/rate-limit) · [Official error codes](https://docs.bigmodel.cn/cn/api/api-code)

Use the exact paid model's [manual](../../../models/zhipu/glm-4.7/README.en.md) and [calling files](../../../models/zhipu/glm-4.7/examples/sources.json), not free-model results. Execution records stay local. Check thinking restrictions independently across generations. [GLM-5.3 Flash documentation](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash)
