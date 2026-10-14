# Kimi: official-source reference

[中文](../../../docs/03-厂商攻略/kimi.md) · [Human guide](../../../human/README.en.md)

See the [Kimi language-model list](../model-lists/kimi.md) for other exact IDs, lifecycle, input modalities and official pricing. A listing does not imply a detailed manual or live-call evidence.

Source verification date: **2026-10-13**. Vendor facts follow the [Kimi platform documentation](https://platform.kimi.com/docs/llms.txt); repository testing terminology follows the [evidence policy](../evidence-policy.md).

| Item | Value and official source |
|---|---|
| Key | [`MOONSHOT_API_KEY`; management page](https://platform.moonshot.cn/console/api-keys) |
| `base_url` | [`https://api.moonshot.cn/v1`](https://platform.kimi.com/docs/get-api-key) |
| Project default | [`kimi-k2.6`](https://platform.kimi.com/docs/models) |
| Models | [Official model list](https://platform.kimi.com/docs/models) |
| Pricing | [Official Chat pricing](https://platform.kimi.com/docs/pricing/chat) |
| Thinking | [Official thinking-model guide](https://platform.kimi.com/docs/guide/use-thinking-models) |
| Streaming | [Official streaming guide](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api) |

The executable [01_basic.py](../../../models/kimi/kimi-k2.6/examples/01_basic.py) uses the environment key, Base URL, and exact model above with the common Chat Completions `messages` structure. Run it from the repository root; this translation does not change the shared file's prompt.

```bash
python models/kimi/kimi-k2.6/examples/01_basic.py
```

The official thinking guide uses `extra_body={"thinking": {"type": "disabled"}}` to disable supported thinking behavior. Do not automatically apply that field to a model whose behavior has not been confirmed in its official model documentation. [Official thinking guide](https://platform.kimi.com/docs/guide/use-thinking-models)

Check model IDs, context lengths, and prices directly in the [official model list](https://platform.kimi.com/docs/models) and [pricing page](https://platform.kimi.com/docs/pricing/chat); this project does not maintain a secondhand numeric table here.

The 2026-10-13 historical basic verification for `kimi-k2.6` covered ordinary requests, streaming, thinking switches, JSON objects, initial tool calls, and image-request shape. It did not record final termination, tool-result return, or image-content recognition, so those items are not complete-loop verification. [Historical redacted report](../../../models/kimi/kimi-k2.6/verification/2026-10-13.json) Read [unified verification status](../verification-status.md) for results and the [model manual](../../../models/kimi/kimi-k2.6/README.en.md) for complete code.
