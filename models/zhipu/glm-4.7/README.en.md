# `glm-4.7` API manual

[中文](README.md) · [Human guide](../../../human/README.en.md) · [Parameter reference](parameters.en.md)

English translation of the [Chinese manual](README.md), source-checked on **2026-10-14**. Calling code and official source manifests are shared; official URLs are retained, including Chinese pages. Translation does not rerun API verification.

This directory maintains the same-generation **paid** model `glm-4.7`, not `glm-4.7-flash`, and does not silently upgrade to the newest GLM. The exact ID remains in the official model guide and API enum, and official pricing lists nonzero charges. Follow the pricing page for current tiers and terms; this repository does not freeze a numerical price. [Model][model] · [API][api] · [Pricing][pricing]

## 1. Identity and connection boundaries

| Item | Confirmed configuration | Source |
|---|---|---|
| Exact Model ID | `glm-4.7` | [Model][model]; [API enum][api] |
| Standard API Base URL | `https://open.bigmodel.cn/api/paas/v4/` | [Compatibility][sdk] |
| Repository key variable | `ZHIPU_API_KEY`; official examples also use `ZAI_API_KEY`. Variable names are local conventions. | [Compatibility][sdk]; [01](examples/01_basic.py) |
| Input / output | Text / text; generic API vision fields do not imply vision for this model. | [Modalities][model] |
| Context / maximum output | 200K / 128K tokens, not the actual length of every response. | [Model][model]; [Concepts][params] |
| Billing | Paid; current amounts, caching prices and tiers are linked, not copied. | [Official pricing][pricing] |

This uses the standard pay-as-you-go API endpoint, not a Coding Plan-specific connection. Do not mix product endpoints or subscription entitlements into this fixed configuration. [Compatibility][sdk] · [Rate limits and plan boundaries][rate]

Machine card: [glm-4.7.json](../../../skills/model-manual/references/models/glm-4.7.json). Capability status comes from documentation. Card `verification=null` / `not_run` means no unified-verifier report is registered for this model; it does not replace file-level results. [Card](../../../skills/model-manual/references/models/glm-4.7.json) · [Evidence policy](../../../en/docs/evidence-policy.md)

## 2. Run a complete source file, then modify it

Install locked dependencies from the repository root, set `ZHIPU_API_KEY`, then run the following. These commands send paid real requests; no key is included here. [Dependency lock](../../../requirements-lock.txt) · [01](examples/01_basic.py)

```bash
python -m pip install -r requirements-lock.txt
python models/zhipu/glm-4.7/examples/01_basic.py
```

All seven scripts run independently without repository test helpers and have a main guard: import does not construct a client. They check normal completion, nonempty final text and bounded retries. Modified fragments and parameter combinations do not inherit a file's verified result. [Manifest and source](examples/sources.json) · [Evidence policy](../../../en/docs/evidence-policy.md)

| Executable | Purpose | Local safeguards |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | Basic chat, model-default thinking | Normal finish and nonempty text |
| [02_streaming.py](examples/02_streaming.py) | Streaming with thinking off | Empty choices, truncation/disconnection and post-finish checks; always close in finally |
| [03_thinking.py](examples/03_thinking.py) | Explicit thinking, separate reasoning/final text | Reasoning alone is not a complete answer |
| [04_json_output.py](examples/04_json_output.py) | JSON Object mode | Parse and require only Boolean `ok=true` |
| [05_tool_calling.py](examples/05_tool_calling.py) | Simulated weather tool, thinking off | At most six logical model calls; validate the whole tool batch first |
| [06_multi_turn.py](examples/06_multi_turn.py) | Two rounds with full client-sent history | Store only complete answers; budget 4096 |
| [07_thinking_tools.py](examples/07_thinking_tools.py) | Interleaved thinking with simulated inventory | Preserve complete assistant; at most four logical model calls; budget 16384 |

The [parameter reference](parameters.en.md) maps each file's actual fields. [sources.json](examples/sources.json) is the shared source/adaptation/command/verification catalog. The [cross-model example index](../../../en/docs/example-index.md) is navigation, not an expansion of this model's capabilities.

## 3. Thinking, JSON and tools

`glm-4.7` defaults to thinking; `thinking.type=disabled` turns it off. Python `extra_body` merges the object into the HTTP top level; it does not send an outer API property named extra_body. [Thinking mode][thinking] · [Compatible examples][sdk]

For thinking/tool loops, return complete, unmodified `reasoning_content` along with the original assistant `tool_calls` and matching tool results. 07 serializes the full assistant. It does not explicitly set `clear_thinking=false`, so it does not claim to enable cross-user-turn Preserved Thinking. [Official thinking rules][thinking] · [07](examples/07_thinking_tools.py)

JSON mode is `response_format={"type":"json_object"}` and still needs application validation. JSON Schema in tool parameters is not server-side `strict`. The text-request schema lists only `tool_choice="auto"`; these examples do not invent required/named forced tools or server `json_schema` output. [Structured output][json] · [Official OpenAPI][openapi] · [Parameter boundaries](parameters.en.md)

Weather and inventory are fixed **teaching simulations**, not real systems. Validate all names, arguments and IDs before execution, return the matching `tool_call_id`, then obtain final text. An answer without an executed tool does not complete this demonstration. [05](examples/05_tool_calling.py) · [07](examples/07_thinking_tools.py)

## 4. Rate limits, safety and reproducibility

Every script disables SDK retries. Only HTTP 429 with business code `1302` (account rate limit) or `1305` (overload) gets at most three attempts. Exponential 1s/2s delays plus up to 0.25s jitter and a 30-second per-wait ceiling are project policy. A valid `Retry-After` is not shortened; a value beyond the ceiling stops the example for later rerun. [Implementation](examples/01_basic.py) · [Official error codes][errors] · [SDK retries][sdk-retries]

429 can instead mean unpaid balance (`1113`), quota (`1308`), expired subscription or missing access. It is not automatically retryable or evidence of an unsupported capability. Tool loops retry only the current model HTTP request, never replay a completed local tool. Once stream consumption begins, a disconnect is not replayed, and the response is always closed. [Error classification][errors] · [05](examples/05_tool_calling.py) · [02](examples/02_streaming.py)

Scripts display answers locally; 03 also displays reasoning. Do not commit private text, keys or raw errors to public reports. API exceptions use fixed redacted messages; usage printing includes only known numeric token fields. [03](examples/03_thinking.py) · [Usage/error handling](examples/01_basic.py) · [Evidence policy](../../../en/docs/evidence-policy.md)

## 5. No cross-model evidence inheritance

For this paid model, find calling files and official attribution in the [code directory](../../../en/docs/example-status.md) and [sources.json](examples/sources.json). Execution records stay local and are not displayed publicly. Offline mocks establish local protocol/safeguards, not real hosted API success or semantic accuracy for arbitrary prompts. [Evidence policy](../../../en/docs/evidence-policy.md)

Use this model's own [calling code](examples/sources.json), not free-model results. See [reproduction](../../../en/docs/verification.md) and [production pitfalls](../../../en/docs/production-pitfalls.md).

[model]: https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7
[api]: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
[sdk]: https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
[pricing]: https://docs.bigmodel.cn/cn/guide/start/pricing
[params]: https://docs.bigmodel.cn/cn/guide/start/concept-param
[thinking]: https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
[json]: https://docs.bigmodel.cn/cn/guide/capabilities/struct-output
[openapi]: https://docs.bigmodel.cn/openapi/openapi.json
[errors]: https://docs.bigmodel.cn/cn/api/api-code
[rate]: https://docs.bigmodel.cn/cn/api/rate-limit
[sdk-retries]: https://developers.openai.com/api/reference/python#retries
