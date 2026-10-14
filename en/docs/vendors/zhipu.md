# Zhipu GLM: official-source reference

[中文](../../../docs/03-厂商攻略/zhipu.md) · [Human guide](../../../human/README.en.md)

Source verification date: **2026-10-13**. Vendor facts follow the [Zhipu documentation](https://docs.bigmodel.cn/llms.txt); repository testing terminology follows the [evidence policy](../evidence-policy.md).

| Item | Value and official source |
|---|---|
| Key | [`ZHIPU_API_KEY`; management page](https://bigmodel.cn/usercenter/apikeys) |
| `base_url` | [`https://open.bigmodel.cn/api/paas/v4`](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| Project default | [`glm-4.7-flash`](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| Models and pricing | [Official pricing](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| OpenAI SDK | [Official compatibility guide](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| Thinking | [Official thinking-mode guide](https://docs.bigmodel.cn/cn/guide/capabilities/thinking) |

The Chinese reference's illustrative client fragment reads `ZHIPU_API_KEY`, uses the Base URL and `glm-4.7-flash` above, sends a user text message, and sets `max_tokens=512` before printing `choices[0].message.content`. That illustrative budget is not a documented model default or a passing test for every configuration. For the maintained runnable path and its own current parameters, use [01_basic.py](../../../models/zhipu/glm-4.7-flash/examples/01_basic.py).

```bash
python models/zhipu/glm-4.7-flash/examples/01_basic.py
```

Recheck `glm-4.7-flash` pricing status on the [official pricing page](https://docs.bigmodel.cn/cn/guide/start/pricing). The word “Flash” is not itself a promise of free service.

All six requests in the 2026-10-13 historical verification received 429, with account rate restriction `1302` or high model traffic `1305`; none was recorded as passed. [Historical redacted report](../../../models/zhipu/glm-4.7-flash/verification/2026-10-13.json) Consult [unified verification status](../verification-status.md) for results and the [model manual](../../../models/zhipu/glm-4.7-flash/README.en.md) for complete code. GLM-5.3's thinking restrictions require a separate check and must not inherit GLM-4.7 configuration. [GLM-5.3 Flash documentation](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash)
