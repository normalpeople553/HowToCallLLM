# `glm-4.7-flash` parameter reference

[中文](parameters.md) · [Human guide](../../../human/README.en.md) · [Model manual](README.en.md)

English translation of the [Chinese reference](parameters.md), checked there on **2026-10-14**. Shared code, manifests and reports are unchanged; official URLs are retained, including Chinese pages. Translation does not rerun API verification. This page explains the seven files in [sources.json](examples/sources.json), not a claim that all passed live. See [example status](../../../en/docs/example-status.md). This exact model's documented modalities are text input/output, context 200K and maximum output 128K. [Model page][model]

## Actual fields by file

All files use model glm-4.7-flash, messages, SDK Base URL `https://open.bigmodel.cn/api/paas/v4/`, timeout 120 and environment key ZHIPU_API_KEY. 01–05 omit max_tokens; all files omit temperature, top_p, stream_options and reasoning_effort. The linked files define these project choices.

| Shared executable | Additional API parameters | SDK/local behavior |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | thinking omitted, model default | Check finish_reason/nonempty text. |
| [02_streaming.py](examples/02_streaming.py) | stream true; thinking disabled | Accumulate text and check termination. |
| [03_thinking.py](examples/03_thinking.py) | thinking enabled | Separate reasoning_content and final text. |
| [04_json_output.py](examples/04_json_output.py) | response_format json_object; thinking off | JSON prompt and local Boolean ok check. |
| [05_tool_calling.py](examples/05_tool_calling.py) | tools get_weather(city); thinking off; tool_choice omitted | Six-turn maximum, simulated weather/result return. |
| [06_multi_turn.py](examples/06_multi_turn.py) | Complete history; thinking off; max_tokens 4096 | Two fixed rounds; SDK max_retries 0. |
| [07_thinking_tools.py](examples/07_thinking_tools.py) | tools get_inventory(sku); tool_choice auto; thinking on; max_tokens 16384 | Four-turn maximum, full reasoning/simulated inventory return; max_retries 0. |

HTTP thinking is top-level JSON; Python passes it through extra_body. API fields follow [Chat API][api] and [compatible SDK examples][sdk].

## SDK settings versus generation fields

| Setting | Meaning and current configuration | Source |
|---|---|---|
| api_key / ZHIPU_API_KEY | Client authentication. The repository variable differs from the official ZAI_API_KEY example without changing the protocol. | [Compatibility][sdk]; [01](examples/01_basic.py) |
| base_url | Service root above, not a model generation field. | [Compatibility][sdk] |
| timeout=120 | Network timeout in seconds; project choice, not a token budget or guaranteed completion time. | [01](examples/01_basic.py); [SDK timeout/retry docs][sdk-retries] |
| max_retries | 06/07 set zero; others omit it. SDK defaults retry some connection errors and 408/409/429/5xx twice. Outer loop counts are not HTTP attempt counts. | [06](examples/06_multi_turn.py); [07](examples/07_thinking_tools.py); [SDK][sdk-retries] |
| extra_body | SDK extension container. `{"thinking":{"type":"disabled"}}` is merged into HTTP top-level thinking, not an outer extra_body field. | [Compatibility][sdk] |

## Text, sampling and defaults

| API field | Purpose, range/default and model-specific scope | Source |
|---|---|---|
| model | Required exact model code glm-4.7-flash, not a display name or automatic selection of another GLM. | [model field][api] |
| messages | Ordered question/history with system/user/assistant/tool roles, not just the last question. Cannot consist only of system/assistant messages. | [messages][api] |
| messages[].content | Text string here. Other vision models' content parts in the shared API do not imply image/video input for this model. | [Text model][model]; [Request types][api] |
| temperature | Randomness, `[0,1]`, at most two decimal places; GLM-4.7 family default 1.0. Higher more varied, lower more focused. Omitted here; no separate Flash-specific default is invented. | [Text temperature][api] |
| top_p | Cumulative-probability threshold, `[0.01,1]`, at most two decimals; GLM-4.7 family default 0.95. Lower narrows candidates; adjust it or temperature rather than both. | [Text top_p][api] |
| do_sample | Sampling on by default; false uses greedy decoding. Not set here, and not equivalent to asking “be accurate” in the prompt. | [Core parameters][params] |

Project recommendation: keep defaults first, change sampling for expression diversity, and use output formats/local validation for machine-readable results. Temperature is not a structure or accuracy guarantee. [Sampling][params] · [Structured output][json]

## Context and single-generation budget

| Concept/field | Confirmed meaning and boundary | Source |
|---|---|---|
| Context | 200K input plus generated content; account for history and tool declarations in input planning. | [Model][model]; [Context concepts][params]; [messages/tools][api] |
| Maximum output | 128K capability ceiling, not automatic output length per request. | [Model][model] |
| max_tokens | Positive integer, text schema maximum 131072. Limits generated tokens, not input; hitting it can truncate output. | [API][api]; [Core parameters][params] |
| Exact default | The default table lists glm-4.7, not separately glm-4.7-flash. The model page's 65536 is an example setting, not confirmed Flash default. Omitted-budget default remains **unknown**. | [Defaults][params]; [Model example][model] |
| Example budgets | 06 uses 4096, 07 uses 16384; others omit. These are not context sizes or guarantees of equal-length final text. | [06](examples/06_multi_turn.py); [07](examples/07_thinking_tools.py) |
| Reasoning accounting | The sources did not separately make the precise reasoning/final-answer sharing of max_tokens explicit for this exact model; keep it **unknown**, not another provider's same-named rule. | [max_tokens/thinking][api]; [Core parameters][params] |

Check finish_reason, final content and usage. A larger generation budget cannot fix history already exceeding the context; this project treats the constraints separately. [Core concepts][params]; [07](examples/07_thinking_tools.py)

## Thinking, history retention and streaming

thinking.type accepts enabled/disabled; the GLM-4.7 family defaults on and this model permits off. 01 omission is not off; 03/07 enable, 02/04/05/06 disable. Do not import GLM-5.3's always-thinking restrictions. [Thinking behavior][thinking]; [ChatThinking][api]; [Manifest](examples/sources.json)

Thinking/tool loops return historical reasoning_content with complete assistant messages. 07's `message.model_dump(exclude_none=True)` serializes the original reasoning/tool fields, not a rewritten reasoning summary. [Interleaved thinking][thinking]; [07](examples/07_thinking_tools.py)

The confirmed retained field here is reasoning_content. This model's encrypted_content input convention was not verified and remains **unknown**; do not import Doubao's encrypted-reasoning rules. [Thinking][thinking]; [Messages][api]

thinking.clear_thinking controls clearing earlier user-turn thinking, default true in the standard API. false enables preservation only with complete ordered reasoning history returned. It is not the current thinking switch. 07 omits clear_thinking, so it does not claim to enable cross-user-round Preserved Thinking. [Retention][thinking]; [ChatThinking.clear_thinking][api]; [07](examples/07_thinking_tools.py)

reasoning_effort is not sent. The cited core documentation scopes it to GLM-5.2 and later; no low/high/max levels are added for glm-4.7-flash. [Core parameters][params]

stream defaults false; true sends SSE deltas without changing the model/budget. 02 omits stream_options, and the cited text-request schema does not list stream_options.include_usage. Its support for this model remains **unknown**, not copied from another service. [Text stream][api]; [Official OpenAPI][openapi]; [02](examples/02_streaming.py)

## Tools and JSON output

tools describes functions: get_weather(city) in 05 and get_inventory(sku) in 07. type function, function.name/description and JSON Schema parameters use type/properties/required/additionalProperties. The text API supports up to 128 functions; each example declares one. [Tool schema][api]; [05](examples/05_tool_calling.py); [07](examples/07_thinking_tools.py)

The cited text-request schema lists only tool_choice auto, also its default: the model decides whether to propose a call. 07 sets it, 05 omits it. This reference does not recommend forced named calls, required or none as confirmed values for this exact model. [tool_choice][api]; [OpenAPI][openapi]

Return results as role tool, matching tool_call_id and string content, then call the model again for the final answer. Validate names, JSON/types and business bounds locally before execution. A model tool_calls response does not mean execution already occurred. [Tool messages][api]; [Thinking tools][thinking]; [05](examples/05_tool_calling.py)

04 requests response_format json_object and specifies JSON in the prompt; locally ok must be Boolean true. The cited schema lists text/json_object. A tutorial's client-side jsonschema validation is not confirmation of server response_format json_schema or strict true for this model. [response_format][api]; [Schema validation][json]; [04](examples/04_json_output.py)

Similarly, JSON Schema in function.parameters does not activate tools.function.strict. The cited function schema does not list it and these files do not send it. Do not transplant Doubao strict-mode settings. [FunctionObject OpenAPI][openapi]; [07](examples/07_thinking_tools.py)

## Statistics and local variables

usage is a response statistic; reasoning_content is reasoning text. Neither is a required generation input. Text character count is not server token usage. 03 displays text, 06/07 print actual usage rather than estimating reasoning tokens from characters. [Response/usage fields][api]; [03](examples/03_thinking.py); [06](examples/06_multi_turn.py); [07](examples/07_thinking_tools.py)

If usage.prompt_tokens_details.cached_tokens is returned, it is cached-input usage, not a required cache-setting input. The service recognizes matching prefixes; this directory has no dedicated cache example and does not promise a short repeated prompt will hit. [Caching][cache]; [Manifest](examples/sources.json)

The six-turn 05 limit, four-turn 07 limit, SKU-001, stock 7, demand 5, simulated true and 80-character city check are local teaching data/protection, not API parameters or official inventory/city limits. [05](examples/05_tool_calling.py); [07](examples/07_thinking_tools.py)

See [general parameters](../../../en/docs/parameters.md), [verification](../../../en/docs/verification.md) and [evidence policy](../../../en/docs/evidence-policy.md).

[model]: https://docs.bigmodel.cn/cn/guide/models/free/glm-4.7-flash
[api]: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
[openapi]: https://docs.bigmodel.cn/openapi/openapi.json
[sdk]: https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
[params]: https://docs.bigmodel.cn/cn/guide/start/concept-param
[thinking]: https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
[json]: https://docs.bigmodel.cn/cn/guide/capabilities/struct-output
[cache]: https://docs.bigmodel.cn/cn/guide/capabilities/cache
[sdk-retries]: https://developers.openai.com/api/reference/python#retries
