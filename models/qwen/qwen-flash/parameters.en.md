# `qwen-flash` example parameter reference

[中文](parameters.md) · [Human guide](../../../human/README.en.md) · [Model manual](README.en.md)

English translation of the [Chinese reference](parameters.md), source-checked there on **2026-10-14**. This is the older qwen-flash, not Qwen3.5/3.8-Flash. Code, manifests and reports are shared; official URLs are unchanged, including Chinese pages. Translation does not rerun API verification. Project choices are not performance guarantees. Current execution evidence: [example status](../../../en/docs/example-status.md).

## 1. File-to-parameter map

All files share model qwen-flash, messages and the connection options below. Unlisted fields are not explicitly supplied; do not fill them with another model's defaults.

| Shared executable | Explicit fields/values | Input, history and local behavior |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | No extra field | One user text. Thinking omitted; older Qwen Flash defaults off. [Default][thinking] |
| [02_streaming.py](examples/02_streaming.py) | stream true; enable_thinking false | Text deltas. No stream_options.include_usage; record only usage actually returned. |
| [03_thinking.py](examples/03_thinking.py) | enable_thinking true | Non-streaming reasoning_content and final content; no explicit token budget. |
| [04_json_output.py](examples/04_json_output.py) | response_format.type json_object; thinking off | Prompt requests `{"ok":true}`; local exact-key/Boolean check. |
| [05_tool_calling.py](examples/05_tool_calling.py) | tools get_weather(city); thinking off | No explicit tool_choice; batch validation, simulated weather, six-call limit, full assistant/tool history. |
| [06_multi_turn.py](examples/06_multi_turn.py) | thinking off; max_tokens 1024 | Resends text history, retaining only assistant content; SDK max_retries 0. |
| [07_thinking_tools.py](examples/07_thinking_tools.py) | tools get_inventory(sku); tool_choice auto; thinking on; max_tokens 8192 | Complete assistant in the current loop, four model-call limit, at least one simulated inventory execution; max_retries 0. |

Python uses `extra_body={"enable_thinking":True/False}`, merged into the HTTP JSON top level. A string "false" is not Boolean false. Do not transplant Kimi's thinking.keep. [Extension placement][api]

## 2. Connection, SDK and region

| Option | Meaning and actual setting | Source |
|---|---|---|
| api_key | Reads DASHSCOPE_API_KEY for authentication, not generation. Do not put it in prompts/source. | [First call](https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen); linked files |
| base_url | `https://dashscope.aliyuncs.com/compatible-mode/v1` in these Beijing examples. The official recommendation is the console's Workspace-specific address; key/region must match. | [Compatible endpoint][api] |
| timeout=120 | Explicit SDK network timeout in seconds, not max_tokens or the complete multi-turn task deadline. | [SDK timeouts](https://developers.openai.com/api/reference/python#timeouts); files |
| max_retries | 06/07 explicitly use zero; 01–05 retain SDK defaults. The SDK defaults retry certain connection/status failures twice. | [SDK retries](https://developers.openai.com/api/reference/python#retries); [06](examples/06_multi_turn.py), [07](examples/07_thinking_tools.py) |
| extra_body | Python SDK extension mechanism, not a BaiLian model field. Raw HTTP/documented Node.js forms may place extensions at the JSON top level. | [enable_thinking][api]; [SDK extensions](https://developers.openai.com/api/reference/python#undocumented-request-params) |

The older model's regional table marks function calling supported in Beijing but not in Singapore, Frankfurt or the US. Merely changing region does not establish that 05/07 work there; these examples do not claim such coverage. [Regional capability table][model]

SDK mechanics are not model-capability evidence. Versions are locked in [requirements-lock.txt](../../../requirements-lock.txt). Project advice: side-effecting tools need application deadlines, retry budgets and idempotency controls; SDK retries are not tool-loop turns.

## 3. Exact model, context and budgets

| Field/limit | Meaning for the older qwen-flash | Source |
|---|---|---|
| model | Functionally equivalent to qwen-flash-2025-07-28, not a newer-generation Flash. | [Model page][model] |
| Input/output modalities | Text in/text out. Shared API image/video/audio fields do not establish support here. | [Modality table][model] |
| Context / maximum input / maximum output | Respectively 1000000 / 997952 / 32768 tokens. One-million context is not one-million output, nor are maximum input/output independent capacities to fill simultaneously. | [Model limits][model] |
| max_tokens | Limits **answer text, excluding reasoning**. The API's default/maximum for this branch is the model maximum output, confirmed here as 32768. 06's 1024 and 07's 8192 are project budgets, not recommendations or new limits. | [Other-model max_tokens branch][api]; [Output limit][model]; [06](examples/06_multi_turn.py), [07](examples/07_thinking_tools.py) |
| max_completion_tokens | Defined as reasoning + answer, but Flash support begins at Qwen3.5-Flash. Do not substitute it automatically for older qwen-flash because generic documentation recommends it for new code. | [Supported models][api] |
| thinking_budget | Limits reasoning length; Qwen3 support is documented, but none of the seven files sends it. The older qwen-flash's separate hard reasoning maximum was not explicitly confirmed here and remains **unknown**, not 32768 or a newer Flash limit. | [Reasoning limit][thinking]; [Published older-model specifications][model] |

Increasing max_tokens in 07 increases answer budget only; it does not establish a thinking-time/token limit. Still check finish_reason and nonempty final content. [07 checks](examples/07_thinking_tools.py)

## 4. Thinking, temperature and nucleus sampling

| Parameter | Default, range, mode and effects | Source |
|---|---|---|
| enable_thinking | Boolean, default false for this hybrid older model. True returns reasoning_content. 03/07 enable; other extended examples disable. Commercial Qwen Flash supports non-streaming thinking; do not copy open-model streaming-only restrictions. | [Qwen3 support/synchronous thinking][thinking] |
| temperature | `[0,2)`; non-thinking default 0.7, Qwen3 thinking default 0.6. Higher is more varied, lower more deterministic. All files omit it. | [Temperature][api]; [Qwen3 identity][model] |
| top_p | `(0,1]`; this model's non-thinking default 0.8, Qwen3 thinking default 0.95. Candidate cumulative-probability threshold; all files omit it. Official advice is to adjust it or temperature, not both. | [top_p][api] |
| preserve_thinking | Current support lists include newer Qwen3.6/3.7/3.8, not older qwen-flash. Not sent here; do not borrow a newer default. | [Preserve-thinking scope][api] |
| Cross-user-turn reasoning | 06 disables thinking and saves only answer content. 07 preserves the full assistant within its current tool loop, not a claim to enable older-model cross-turn preserved thinking. | [Multi-turn][multi]; [06](examples/06_multi_turn.py), [07](examples/07_thinking_tools.py) |

Project advice: evaluate creative variability with a one-variable sampling comparison; evaluate extraction/code through tests, schemas and source evidence. **More deterministic is not more factually accurate.** This repository does not guarantee that lower temperature improves correctness. Official sampling definitions concern diversity/determinism. [Sampling definitions][api]

## 5. Messages, streaming and response statistics

| Field | Meaning and example behavior | Source |
|---|---|---|
| messages[].role / content | system/user/assistant/tool; text content is a string. Send the required history each request; the SDK client does not manage the conversation. | [Multi-turn][multi]; [Tool message flow][tools] |
| stream | Default false. 02 enables deltas instead of complete messages; 03/07 are non-streaming thinking. | [Streaming](https://help.aliyun.com/zh/model-studio/stream); [Synchronous thinking][thinking] |
| stream_options.include_usage | Default false; when enabled, usage arrives in the final stream chunk. Streaming only; 02 omits it. Missing usage is not zero usage. | [Stream options][api]; [02](examples/02_streaming.py) |
| usage | Returned prompt/completion/total tokens, possibly reasoning/cache details. Record actual fields; not a request-side consumption limit. | [Thinking usage][thinking]; [API usage][api] |
| finish_reason | stop: normal; length: limit; tool_calls: tool stage. Reasoning or partial JSON is not final success. Project checks empty choices/text, unhandled calls and explicit streaming completion. | [Response fields][api]; [02](examples/02_streaming.py), [07](examples/07_thinking_tools.py) |

## 6. Nested tools and structured output

| Field | Meaning, limit or project choice | Source |
|---|---|---|
| tools[].type=function | Declares a function; application executes it. 05/07 use only simulated weather/inventory. | [Tools][tools]; [05](examples/05_tool_calling.py), [07](examples/07_thinking_tools.py) |
| function.name / description | Local allowlist routing and purpose; get_weather/get_inventory here. | [Definitions][tools]; files |
| function.parameters | JSON Schema object with string city/sku, required properties and additionalProperties false. No tool strict flag is sent; arguments still need local validation. | [Function arguments][tools]; files |
| tool_choice | With tools, default automatic; 07 explicitly auto. Documented disabling/named forms have model/mode constraints. Required is not a reliable supported forced-call contract here and is unsupported in thinking mode; do not use it to guarantee a call. | [Invocation policy][tools] |
| tool_calls[].function.arguments / id | JSON argument string. Validate the whole batch, execute, append the complete assistant, then return role tool, matching tool_call_id and string content. | [Full flow][tools]; [07](examples/07_thinking_tools.py) |
| response_format | Text by default. 04 selects json_object, explicitly requests JSON and disables thinking because this older model supports JSON Mode only in **non-thinking** mode. | [JSON Object support][json]; [04](examples/04_json_output.py) |
| JSON Schema / strict | Older qwen-flash is not in the cited JSON Schema support list. Do not transplant newer json_schema/strict requests. Object mode addresses format; the project's code checks exact keys and Boolean ok. | [Mode/model support][json]; [04](examples/04_json_output.py) |

City length 1–80, SKU-001 only, stock 7, four/six-call bounds, duplicate-ID rejection and an actual-tool-execution requirement are local business/security policies, not official defaults or ranges. additionalProperties false does not replace tool allowlisting, JSON/type checks or authorization in a real system. [05](examples/05_tool_calling.py); [07](examples/07_thinking_tools.py)

## 7. Compatible names do not imply capabilities

This exact model is text-only. Kimi-style video data URLs, other Qwen models' image_url/video, newer preserve_thinking/max_completion_tokens and strict JSON Schema all require model-specific confirmation, not merely successful SDK serialization. [Older model][model]; [Structured-output scope][json]; [Per-model parameter scope][api]

See [general parameter navigation](../../../en/docs/parameters.md), [verification](../../../en/docs/verification.md) and [evidence policy](../../../en/docs/evidence-policy.md). Explanations and documentation fragments do not extend a recorded file's tested scope.

[api]: https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions
[model]: https://help.aliyun.com/zh/model-studio/qwen-flash
[thinking]: https://help.aliyun.com/zh/model-studio/deep-thinking
[tools]: https://help.aliyun.com/zh/model-studio/qwen-function-calling
[json]: https://help.aliyun.com/zh/model-studio/qwen-structured-output
[multi]: https://help.aliyun.com/zh/model-studio/multi-round-conversation
