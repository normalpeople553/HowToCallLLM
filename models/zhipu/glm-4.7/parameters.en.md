# `glm-4.7` parameter reference

[中文](parameters.md) · [Human guide](../../../human/README.en.md) · [Model manual](README.en.md)

English translation of the [Chinese reference](parameters.md), source-checked **2026-10-14**. Calling code and official manifests are shared unchanged by translation; official URLs, including Chinese pages, are retained. Translation does not rerun API verification.

This page explains actual fields in [seven independent executables](examples/sources.json), not successful execution of arbitrary combinations. Find [calling files](../../../en/docs/example-status.md); private records are not published. This paid text model does not inherit free Flash defaults or evidence; current amounts are linked to [official pricing][pricing]. [GLM-4.7][model] · [Evidence policy](../../../en/docs/evidence-policy.md)

## 1. Actual parameters by file

All scripts use `model="glm-4.7"` and `messages`. SDK configuration is environment variable `ZHIPU_API_KEY`, Base URL `https://open.bigmodel.cn/api/paas/v4/`, `timeout=120` and `max_retries=0`. None sends `temperature`, `top_p`, `do_sample`, `reasoning_effort`, `stream_options`, `tool_stream` or `clear_thinking`. [Shared source catalog](examples/sources.json)

| Executable | Additional actual API fields | Explanation and local checks |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | thinking/max_tokens omitted, model defaults | Sections 3–5; normal finish, nonempty text |
| [02_streaming.py](examples/02_streaming.py) | stream true; thinking disabled | Sections 5–6; empty choices, termination and finally-close |
| [03_thinking.py](examples/03_thinking.py) | thinking enabled | Sections 4–5 and 8; show reasoning separately from final text |
| [04_json_output.py](examples/04_json_output.py) | response_format json_object; thinking disabled | Section 7; JSON prompt, Boolean ok=true validation |
| [05_tool_calling.py](examples/05_tool_calling.py) | tools get_weather(city); thinking disabled; tool_choice/max_tokens omitted | Sections 7 and 9; at most six logical model calls, simulated weather, batch validation |
| [06_multi_turn.py](examples/06_multi_turn.py) | Complete messages; thinking disabled; max_tokens 4096 | Sections 3–4; two fixed rounds, store only complete answers |
| [07_thinking_tools.py](examples/07_thinking_tools.py) | tools get_inventory(sku); tool_choice auto; thinking enabled; max_tokens 16384 | Sections 4–5, 7 and 9; at most four logical model calls, preserve reasoning, simulated inventory |

01–05 omit an explicit output budget. 4096 and 16384 in 06/07 are project settings, not model limits or defaults. Every file includes its own bounded retry function and does not import another example or test helper. [01](examples/01_basic.py) · [06](examples/06_multi_turn.py) · [07](examples/07_thinking_tools.py)

## 2. SDK configuration is not model generation control

| Setting | Purpose and current behavior | Source |
|---|---|---|
| api_key / ZHIPU_API_KEY | Client authentication; this repository's name differs from official ZAI_API_KEY examples without changing authentication. | [Compatibility][sdk]; [01](examples/01_basic.py) |
| base_url | Standard service root, not a generation field. Do not substitute a different product's Coding Plan endpoint. | [Compatibility][sdk]; [Rate/plan boundaries][rate] |
| timeout=120 | SDK network timeout in seconds; local choice, not a token budget, complete tool-task deadline or guarantee of completion within 120s. | [SDK timeout/retries][sdk-retries]; [01](examples/01_basic.py) |
| max_retries=0 | Disable SDK retries to avoid multiplication with local retries. The SDK default retries certain connection errors and 408/409/429/5xx twice. | [SDK][sdk-retries]; [01](examples/01_basic.py) |
| extra_body | SDK container merged into top-level HTTP JSON, e.g. thinking disabled. There is no outer generation field named extra_body. | [Compatible thinking example][sdk] |

### Local retry policy, not server parameters

`create_with_backoff` is a project function. It retries only HTTP 429 with business `error.code` 1302 or 1305, at most three HTTP attempts per logical call. Other errors, including unknown 429 codes, stop with fixed redacted messages rather than raw responses, errors or keys. [01](examples/01_basic.py) · [Official codes][errors]

1113 is also HTTP 429 but means unpaid balance; 1308 is a usage limit, and 1309 is an expired plan. These are not assumed to recover after a few seconds, and this code does not loop on them. [Error codes][errors] · [Rate limits][rate]

The local policy uses 1s/2s exponential delays with 0–0.25s jitter. A valid `Retry-After` (seconds or HTTP date) is a minimum wait; more than 30 seconds stops the example for a later rerun rather than shortening the header to 30s. These bounds do not promise service recovery. [Implementation](examples/01_basic.py) · [SDK retry guidance][sdk-rate]

Only the current model HTTP request is retried. A later 429 in 05/07 does not replay a completed local tool. 02 retries only stream creation, never after consumption begins. Logical model turns and HTTP attempts are different; six tool turns do not imply at most six network attempts. [02](examples/02_streaming.py) · [05](examples/05_tool_calling.py) · [07](examples/07_thinking_tools.py)

## 3. Identity, messages and sampling

| API field | Meaning, range/default and scope | Source |
|---|---|---|
| model | Required exact code glm-4.7, not Flash or automatic latest-model selection. | [API enum][api]; [Model][model] |
| messages | Current complete history in chronological order; cannot contain only system/assistant messages. | [messages][api] |
| messages[].role | system sets behavior; user is input; assistant is a model response; tool is a function result. | [Message roles][api] |
| messages[].content | Text here. Vision content parts in a shared API do not establish image/video input for this model. | [Text modalities][model]; [Request types][api] |
| temperature | Sampling randomness, range [0,1], at most two decimals, default 1.0. Higher is more varied, lower more focused; not a factual-accuracy dial. | [Text temperature][api]; [Concepts][params] |
| top_p | Sample from the smallest candidate set reaching cumulative probability threshold; range [0.01,1], at most two decimals, default 0.95. Unlike temperature, it narrows the candidate set. Adjust one, not both. | [Text top_p][api]; [Concepts][params] |
| do_sample | Default true; false selects greedy decoding and ignores temperature/top_p. Omitted here; not equivalent to prompting “be accurate.” | [do_sample][api]; [Core parameters][params] |

No executable sends these sampling fields. Its execution evidence does not verify a manually changed temperature or greedy-decoding request. Project recommendation: start with the exact request, modify one setting at a time and verify again. Temperature does not guarantee JSON structure or truth. [Actual fields](examples/sources.json) · [Evidence policy](../../../en/docs/evidence-policy.md)

## 4. Context, output ceiling and generation budget

| Concept/field | Confirmed model boundary | Source |
|---|---|---|
| Context | 200K, including input and generation; history/tool declarations also occupy input space. | [Model][model]; [Context concepts][params]; [messages/tools][api] |
| Maximum output | 128K capability ceiling, not automatic response length. | [Model][model] |
| max_tokens | Positive integer, text-schema range 1–131072. Limits generation, not input; reaching it may truncate output. | [API][api]; [Core parameters][params] |
| Omitted default | The exact glm-4.7 row states default 65536, maximum 131072. This is confirmed for the paid model, not inherited from Flash. | [Default table][params] |
| Local budgets | 06 sends 4096, 07 sends 16384; 01–05 omit. Neither context sizes nor guarantees of equal-length final text. | [06](examples/06_multi_turn.py); [07](examples/07_thinking_tools.py) |
| Reasoning/final split | The cited model parameters do not precisely specify their sharing of max_tokens; keep it **unknown**, not another provider's same-named semantics. | [max_tokens/thinking][api]; [Concepts][params] |

Regardless of budget, check finish_reason and final text. length is not complete success; a larger output budget cannot remove oversized input history. These are project checks based on separate constraints, not use of the output ceiling as an input window. [Context/output concepts][params] · [01](examples/01_basic.py)

## 5. Thinking, retained history and unconfirmed fields

thinking.type accepts enabled/disabled. GLM-4.7 defaults on and allows off. 01 omission is not off; 03/07 enable, 02/04/05/06 disable. Enabled mode performs reasoning for this model; do not import GLM-5.3's cannot-disable restriction. [Thinking mode][thinking] · [thinking concepts][params] · [ChatThinking][openapi]

reasoning_content is assistant reasoning text. Interleaved thinking/tool loops require the complete original field with tool_calls. 07 uses `message.model_dump(exclude_none=True)`, not a rewritten reasoning summary. [Interleaved thinking][thinking] · [07](examples/07_thinking_tools.py)

thinking.clear_thinking clears reasoning from earlier user turns, default true on the standard API. false requires complete, unchanged, ordered reasoning history for Preserved Thinking. It does not control whether the current turn thinks. 07 omits it and therefore does not claim cross-user-turn preservation. [Preserved thinking][thinking] · [ChatThinking.clear_thinking][openapi] · [07](examples/07_thinking_tools.py)

reasoning_effort is scoped to GLM-5.2 and later in the cited docs; no low/high/max levels are added to GLM-4.7. The exact model's encrypted_content input convention is also unverified and remains **unknown**, not copied from another provider. [Core parameters][params] · [Thinking rules][thinking]

## 6. Streaming and completion

stream defaults false. true returns SSE deltas with a final [DONE]. 02 disables thinking, accumulates delta.content and tolerates empty choices/usage-only chunks. It requires a normal stop with nonempty final text, rejecting missing termination, length, safety/network interruption, duplicate termination, post-finish text or unhandled tool deltas. [Stream/response fields][api] · [02](examples/02_streaming.py)

finish_reason tool_calls enters only an implemented tool handler; it is not final-answer success. Non-tool examples require normal completion, and unfinished tool arguments are never executed. These are local integrity checks, not SDK-provided validation. [Response schema][openapi] · [05](examples/05_tool_calling.py)

02 omits stream_options.include_usage; the cited text schema does not list that extension, so support remains **unknown**. The API lists tool_stream for streamed function calls, but 02 does not implement tool streaming and 05/07 use nonstreaming tool loops. A text stream pass does not establish tool-stream verification. [Text schema][openapi] · [tool_stream][api] · [Catalog](examples/sources.json)

Any stream-consumption exception stops without replay. finally attempts to close the response; displayed fragments remain partial and do not constitute success. [02](examples/02_streaming.py)

## 7. Function tools and JSON output

| Field | Meaning and actual use | Source |
|---|---|---|
| tools[].type | function declares a function tool. The text API permits up to 128 functions; each example declares one. | [Tool schema][openapi] |
| function.name | API name: letters/digits/underscore/hyphen, 1–64 chars. Local execution allows only the declared weather or inventory function. | [FunctionObject][openapi]; [05](examples/05_tool_calling.py); [07](examples/07_thinking_tools.py) |
| description | Explains purpose to the model; does not execute a function. | [FunctionObject][openapi] |
| parameters | JSON Schema with type/properties/required/additionalProperties. The client still validates JSON, types and business bounds. | [FunctionParameters][openapi]; [05](examples/05_tool_calling.py) |
| tool_choice | Text schema lists only auto, also default: the model decides whether to propose a call. 07 sets it, 05 omits. No required/none/forced named tools are invented. | [tool_choice][openapi] |
| role tool / tool_call_id / content | Match the original ID with a local function's string result, return it, then call the model again. | [Messages][api]; [Thinking tool example][thinking] |
| response_format | Default text. 04 sends json_object, requests JSON in the prompt, parses locally and requires only Boolean ok=true. | [API][api]; [Structured output][json]; [04](examples/04_json_output.py) |

additionalProperties false describes the expected argument object; the application also rejects extra fields. It is not tools.function.strict. The cited FunctionObject lacks strict and text response_format lists only text/json_object. Client-side jsonschema validation in a tutorial does not establish server json_schema/strict support; no such fields are sent. [Official schema][openapi] · [Schema validation][json] · [05](examples/05_tool_calling.py)

Validate the entire tool batch before execution, reject reused IDs across turns, and do not execute a tool on the last model turn when no response can be returned. At least one tool execution plus normal nonempty final text is required for this teaching loop. [05](examples/05_tool_calling.py) · [07](examples/07_thinking_tools.py)

## 8. Statistics, images and other endpoints

usage.prompt_tokens/completion_tokens/total_tokens are server response statistics, not generation input. Scripts print only integer values of these three fields; 03 additionally displays reasoning_content. Reasoning character counts cannot substitute for billed tokens. Keep private answers/reasoning out of public reports. [Usage response][api] · [01](examples/01_basic.py) · [03](examples/03_thinking.py) · [Evidence policy](../../../en/docs/evidence-policy.md)

If usage.prompt_tokens_details.cached_tokens appears, it is cached-input usage. Matching prefixes are recognized by the service, not a required cache-input field. This directory has no cache-specific example and does not promise that two short repeated prompts will hit cache. [Caching][cache] · [Not-integrated catalog](examples/sources.json)

The exact model declares text input/output. No image URL, file_id, detail, video or audio tutorial is provided. Shared APIs and other GLM vision models do not establish this model's modalities. Responses, FIM and Beta endpoints are likewise not integrated/verified here; do not transplant other vendors' fields. [Modalities][model] · [API request types][api] · [Scope](examples/sources.json)

## 9. Local teaching data and loop bounds

05's 1–80-character city validation and fixed sunny result, 07's SKU-001, stock 7, demand 5 and simulated true are project teaching data/protection, not platform city/SKU restrictions or live business information. [05](examples/05_tool_calling.py) · [07](examples/07_thinking_tools.py)

05 allows six logical model calls, 07 four; 06 has two rounds. ID sets, execution counts, JSON checks, three rate-limit attempts per request, the 30-second wait ceiling, main guards and stream.close are local controls, not model generation parameters or guarantees for arbitrary combinations. [05](examples/05_tool_calling.py) · [06](examples/06_multi_turn.py) · [07](examples/07_thinking_tools.py) · [02](examples/02_streaming.py)

Further reading: [general parameters](../../../en/docs/parameters.md) · [verification](../../../en/docs/verification.md) · [evidence policy](../../../en/docs/evidence-policy.md).

[model]: https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7
[pricing]: https://docs.bigmodel.cn/cn/guide/start/pricing
[api]: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
[openapi]: https://docs.bigmodel.cn/openapi/openapi.json
[sdk]: https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
[params]: https://docs.bigmodel.cn/cn/guide/start/concept-param
[thinking]: https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
[json]: https://docs.bigmodel.cn/cn/guide/capabilities/struct-output
[cache]: https://docs.bigmodel.cn/cn/guide/capabilities/cache
[errors]: https://docs.bigmodel.cn/cn/api/api-code
[rate]: https://docs.bigmodel.cn/cn/api/rate-limit
[sdk-retries]: https://developers.openai.com/api/reference/python#retries
[sdk-rate]: https://developers.openai.com/api/docs/guides/rate-limits
