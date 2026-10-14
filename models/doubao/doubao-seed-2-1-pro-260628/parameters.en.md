# `doubao-seed-2-1-pro-260628` parameter reference

[中文](parameters.md) · [Human guide](../../../human/README.en.md) · [Model manual](README.en.md)

English translation of the [Chinese reference](parameters.md), checked there on **2026-10-14**. Code, manifests and reports are shared; original official URLs are retained, including Chinese pages. Translation does not rerun API verification. This exact ID is listed as a past model, so its constraints are not transferred to newer versions. [Model list][models] Current execution evidence: [example status](../../../en/docs/example-status.md).

## Actual request fields by file

All ten files use model doubao-seed-2-1-pro-260628, messages, ARK_API_KEY, the same Base URL and SDK timeout 120. None explicitly sets temperature, top_p, max_tokens, max_completion_tokens or stream_options. The linked sources define these choices, not server defaults.

| Shared executable | Additional API parameters | Local behavior/response fields |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | thinking disabled | Check complete answer, print usage. |
| [02_streaming.py](examples/02_streaming.py) | stream true; thinking disabled | Accumulate delta.content, check finish reason, close stream. |
| [03_thinking.py](examples/03_thinking.py) | thinking enabled | Separate reasoning summary, final text and actual reasoning_tokens. |
| [04_json_output.py](examples/04_json_output.py) | response_format json_schema; json_schema.name result; strict true; schema; thinking off | Parse JSON and require only Boolean ok=true. |
| [05_tool_calling.py](examples/05_tool_calling.py) | tools get_weather(city); thinking off; no explicit tool_choice | Up to six turns, simulated weather and result return. |
| [06_vision.py](examples/06_vision.py) | text/image_url content parts; thinking off | Construct input from IMAGE_URL or IMAGE_PATH. |
| [07_multi_turn.py](examples/07_multi_turn.py) | Full messages history; thinking off | Two fixed rounds; commit only complete answers. |
| [08_thinking_tools.py](examples/08_thinking_tools.py) | tools; thinking enabled; tool_choice omitted | Up to six turns; return full thinking-related assistant fields and tool results. |
| [09_video.py](examples/09_video.py) | video_url.url and text parts; thinking off | VIDEO_URL input; no fps, audio or file-preprocessing setting. |
| [10_implicit_cache.py](examples/10_implicit_cache.py) | Two ordinary requests with identical prefix; thinking off; no cache switch | Inspect usage.prompt_tokens_details.cached_tokens. |

Fields follow the [Chat API][api], [context-management guide][context] and [function-calling guide][tools].

## Connection and SDK settings

| Setting | Purpose, actual value and boundary | Source |
|---|---|---|
| api_key / ARK_API_KEY | Client authentication from a local environment variable, not a prompt field. | [SDK setup][sdk] |
| base_url | `https://ark.cn-beijing.volces.com/api/v3`; the SDK's Chat method adds /chat/completions. Do not use the full endpoint as the service root again. | [SDK setup][sdk] |
| timeout=120 | SDK network timeout in seconds; a project choice, not a token limit or official response-time guarantee. | [01](examples/01_basic.py); [SDK docs][sdk-retries] |
| max_retries | None explicitly set; installed SDK behavior applies. SDK defaults retry certain connection errors and 408/409/429/5xx twice, so one call expression can make multiple HTTP attempts. | [Locked versions](../../../requirements-lock.txt); [SDK retries][sdk-retries] |
| extra_body | Python SDK extension container; thinking merges into HTTP JSON top-level thinking, not a nested extra_body server field. | [SDK extra fields][sdk] |

## Messages, history and sampling

| Field | Purpose, default/range and exact-model note | Source |
|---|---|---|
| model | Exact ID above. Recheck capabilities, context and lifecycle before changing IDs. | [Model list][models] |
| messages | Ordered input/history with role/content. Chat context is managed manually; 07 does not use previous_response_id. | [Manual context][context] |
| messages[].role | system behavior, user question, assistant model history, tool results. Tool messages require matching tool_call_id. | [Chat messages][api] |
| messages[].content | String for text; content-part array for mixed image/video. Do not json.dumps the array into ordinary text. | [Images][image]; [Video][video] |
| temperature | General Chat range `[0,2]`, default 1.0; higher usually more random, lower more focused. Omitted here. Fixed-value exceptions documented for certain older 2.0 models are not imported into this ID. | [Temperature][api] |
| top_p | Candidate cumulative-probability threshold, general range `[0,1]`, default 0.7. Lower more focused, higher more varied. Omitted here; official recommendation is to adjust it or temperature, not both heavily. | [top_p][api] |

Project advice: tune sampling for expression diversity; use response_format and application validation for fixed, processable structures. Sampling distribution is not a substitute for schema/business validation. [Sampling/format][api] · [Structured-output steps][json]

## Context, answer and reasoning budgets

| Concept/field | Meaning, default and restriction | Source |
|---|---|---|
| Context | 256K input plus generated-content capacity, not automatic generation of 256K answer tokens. | [Model list][models]; [Context-window finish reason][api] |
| max_tokens | Answer-length limit. Chat default 4096; ranges vary by model. This model's listed maximum answer is 256K. | [API][api]; [Answer length][context]; [Model list][models] |
| max_completion_tokens | Total reasoning plus answer limit. Setting it overrides the default max_tokens answer limit. The guide says language models dated 250528 and later support it by default, with separately listed exceptions. | [Combined output budget][context] |
| Relationship | Do not send max_tokens and max_completion_tokens together or treat them as interchangeable synonyms. | [API][api]; [Context management][context] |
| Accepted upper bound | General Chat docs currently specify max_completion_tokens `[1,65536]`, while the model list separately states 256K maximum answer. This reference does not infer a larger accepted request value for the historical model; its full model-specific upper bound remains **unknown**. | [API][api]; [Model list][models] |

None of the ten files sets either budget. length may indicate answer, combined-generation or context limits. Text presence alone is insufficient; inspect termination too. Too-small combined budgets can be spent on reasoning, leaving less room for the answer. [03](examples/03_thinking.py); [Finish reasons][api]

## Thinking summaries and tool history

thinking.type supports enabled (default) and disabled. It is the thinking switch; temperature is not. 03/08 enable; all other files disable. [Thinking controls][thinking]; [API][api]; [Manifest](examples/sources.json)

| Field | Interpretation and required handling | Source |
|---|---|---|
| reasoning_content | This ID is in the reasoning-summary support list. It is not the entire original reasoning; character count is not actual reasoning-token usage. | [Encrypted original reasoning][thinking] |
| encrypted_content | Returned encrypted original reasoning. 08 returns the complete original assistant message; do not truncate, regenerate it or retain only the visible summary. | [Thinking round trip][thinking]; [08](examples/08_thinking_tools.py) |
| usage.completion_tokens_details.reasoning_tokens | Actual reasoning-token statistic, based on original reasoning even in summary mode. Missing means unknown, not a value estimated from summary length. | [Usage fields][thinking]; [03](examples/03_thinking.py) |

tools[].type function declares a function; name identifies it, description explains purpose and parameters is JSON Schema with type/properties/required. 05/08 use additionalProperties false but still validate names, JSON, types and IDs locally before simulated execution. [Tools schema][api]; [05](examples/05_tool_calling.py); [08](examples/08_thinking_tools.py)

With tools, tool_choice defaults auto, permitting text or a tool call; without tools it defaults none. 05/08 omit it. Return role tool, matching tool_call_id and string content in history, then request the final answer. A proposed call is not execution. [Selection/messages][api]; [Execute/return flow][tools]

tools.function.strict constrains tool arguments; response_format.json_schema.strict constrains final output. They occupy different locations. 05/08 do not send tool strict, so a parameters schema alone does not mean strict tool mode is active. [Strict fields][api]; [05](examples/05_tool_calling.py)

## JSON, images, video and streaming options

04 sets response_format.type json_schema. json_schema.name identifies the format; schema defines the final JSON; strict true asks for the supported schema's strict conformance. Here ok is a required Boolean, extra keys are forbidden and the client checks ok is True. That is a project business condition, not a universal response field. Supported keywords remain subject to the [structured-output documentation][json]. [04](examples/04_json_output.py)

06 uses `{"type":"image_url","image_url":{"url":…}}`; URL can be server-accessible or a compliant base64 data URL. Local IMAGE_URL/IMAGE_PATH are alternatives. The file intentionally accepts only local PNG/JPEG, not a claim that the model supports only those formats. [Image inputs][image]; [06](examples/06_vision.py)

09 uses `{"type":"video_url","video_url":{"url":…}}` and only sends the URL. It does not set fps, audio or Files preprocessing. Support follows the vision-capability model table linked by the video guide; do not also import newer models' special preprocessing options. [Video models/URLs][video]; [Vision model list][models]; [09](examples/09_video.py)

stream defaults false; true changes transport only. 02 does not set stream_options. If include_usage is set true, the documented extra final chunk before `[DONE]` has choices empty and total usage; default false. chunk_include_usage true adds cumulative usage to chunks, also default false. Do not sum cumulative values again. [Streaming options][api]; [02](examples/02_streaming.py)

## Statistics and local variables

usage.prompt_tokens, completion_tokens, total_tokens and prompt_tokens_details.cached_tokens are returned statistics, not required inputs. In 10, cached_tokens above zero means a hit, zero a miss, and missing unknown. Implicit caching is automatic; matching prefixes do not guarantee a hit. [Usage][api]; [Implicit caching][cache]; [10](examples/10_implicit_cache.py)

MAX_MODEL_TURNS/max_model_turns 6, an 80-character city check, simulated true, the cache demo's 80 records and two iterations are local teaching logic. They are not API fields, official city limits or guaranteed cache-hit conditions. [05](examples/05_tool_calling.py); [08](examples/08_thinking_tools.py); [10](examples/10_implicit_cache.py)

See [general parameters](../../../en/docs/parameters.md), [verification](../../../en/docs/verification.md) and [evidence policy](../../../en/docs/evidence-policy.md).

[api]: https://docs.volcengine.com/docs/ark/chat-api?lang=zh
[models]: https://docs.volcengine.com/docs/ark/model-list?lang=zh
[sdk]: https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh
[context]: https://docs.volcengine.com/docs/ark/context-management?lang=zh
[thinking]: https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh
[tools]: https://docs.volcengine.com/docs/ark/function-calling?lang=zh
[json]: https://docs.volcengine.com/docs/ark/structured-output-beta?lang=zh
[image]: https://docs.volcengine.com/docs/ark/image-understanding?lang=zh
[video]: https://docs.volcengine.com/docs/ark/video-understanding?lang=zh
[cache]: https://docs.volcengine.com/docs/ark/context-cache?lang=zh
[sdk-retries]: https://developers.openai.com/api/reference/python#retries
