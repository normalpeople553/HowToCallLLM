# DeepSeek: official-source reference

[中文](../../../docs/03-厂商攻略/deepseek.md) · [Human guide](../../../human/README.en.md)

Beyond the maintained Flash model, see the [DeepSeek language-model list](../model-lists/deepseek.md) for exact IDs, aliases, retirements and official pricing. A listing does not imply a detailed manual or live-call evidence.

Source verification date: **2026-10-13**. Vendor facts follow the [DeepSeek API documentation](https://api-docs.deepseek.com/); repository testing terminology follows the [evidence policy](../evidence-policy.md).

Parameters, capabilities, price snapshots, and eight complete examples for `deepseek-flash` are organized in its [model-specific manual](../../../models/deepseek/deepseek-flash/README.en.md).

| Item | Value and official source |
|---|---|
| Key | [`DEEPSEEK_API_KEY`; management page](https://platform.deepseek.com/api_keys) |
| `base_url` | [`https://api.deepseek.com`](https://api-docs.deepseek.com/) |
| Project default | [`deepseek-flash`](https://api-docs.deepseek.com/quick_start/pricing/) |
| Models and pricing | [Official models/pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| Thinking | [Official thinking-mode guide](https://api-docs.deepseek.com/guides/thinking_mode/) |
| Errors | [Official error codes](https://api-docs.deepseek.com/quick_start/error_codes/) |
| Changes | [Official updates](https://api-docs.deepseek.com/updates/) |

The official pricing page states that `deepseek-flash` is served by DeepSeek-V4.1-Flash. The old `deepseek-v4-flash` name remains callable, but the old V4 Flash model has retired and that name temporarily routes to the newer version. [Official models/pricing](https://api-docs.deepseek.com/quick_start/pricing/)

Use the shared executable [01_basic.py](../../../models/deepseek/deepseek-flash/examples/01_basic.py) rather than maintaining another independent copy of the introductory client fragment. It uses the key, endpoint, model, and `messages` pattern described above; the shared source retains its actual prompt.

```bash
python models/deepseek/deepseek-flash/examples/01_basic.py
```

The documented Python disabling syntax is `extra_body={"thinking": {"type": "disabled"}}`. Thinking appears in `reasoning_content`, and thinking mode ignores some sampling parameters. [Official thinking guide](https://api-docs.deepseek.com/guides/thinking_mode/)

Use the currency and peak/off-peak rules currently displayed by the official pricing page. This page does not copy numbers that could continue circulating after a price change. [Official pricing](https://api-docs.deepseek.com/quick_start/pricing/)

The 2026-10-13 historical basic verification covered ordinary requests, streaming, thinking switches, JSON, initial tool calls, and image-request shape. It did not record final termination, verify tool-result return, or verify image-content recognition. [Historical redacted report](../../../models/deepseek/deepseek-flash/verification/2026-10-13.json) Consult [unified verification status](../verification-status.md) for the recorded results and [verification and reproduction](../verification.md) to rerun tests.
