# `kimi-k2.6` example parameter reference

[中文](parameters.md) · [Human guide](../../../human/README.en.md) · [Model manual](README.en.md)

English translation of the [Chinese reference](parameters.md), source-checked there on **2026-10-14**. Code, source manifests and reports are shared; original official URLs, including Chinese pages, are preserved. Translation does not rerun API verification. This page describes actual K2.6 example fields, not all Kimi models. Project settings are not official limits or performance guarantees. Execution results: [example status](../../../en/docs/example-status.md).

## 1. File-to-parameter map

Every file also uses `model="kimi-k2.6"`, messages and the connection options below. An unlisted field is not explicitly set, not implicitly zero.

| Shared executable | Explicit fields/values | Input, history and local policy |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | No extra request field | One user text; thinking omitted, so K2.6 default thinking applies. [Default][params] |
| [02_streaming.py](examples/02_streaming.py) | stream true; thinking.type disabled | Text deltas; no explicit stream_options. |
| [03_thinking.py](examples/03_thinking.py) | thinking.type enabled; max_tokens 16384 | Separate reasoning/final text; project budget, not maximum. |
| [04_json_output.py](examples/04_json_output.py) | response_format.type json_object; thinking disabled | Prompt asks for `{"ok":true}`; local check requires exactly that Boolean field. |
| [05_tool_calling.py](examples/05_tool_calling.py) | tools get_weather(city); thinking disabled | No explicit tool_choice; batch validation, simulated weather, at most six model calls, full assistant/tool history. |
| [06_vision.py](examples/06_vision.py) | content array with text/image_url.url; thinking disabled | IMAGE_PATH PNG/JPEG encoded as a data URL; IMAGE_URL rejected. |
| [07_multi_turn.py](examples/07_multi_turn.py) | thinking disabled | Resends history; commits user/full assistant only after success. |
| [08_thinking_tools.py](examples/08_thinking_tools.py) | tools get_order_status(order_id); tool_choice auto; `thinking={"type":"enabled","keep":"all"}`; max_tokens 32768 | Simulated order; complete reasoning history; default six model calls; a no-tool answer is not a completed tool demo. |
| [09_video.py](examples/09_video.py) | video_url.url/text content parts; thinking disabled | VIDEO_PATH MP4 to `data:video/mp4;base64,…`; no fps, remote-video URL or upload request. |
| [10_json_schema.py](examples/10_json_schema.py) | response_format.type json_schema; json_schema.name person; strict true; object schema; thinking disabled | Required name:string/age:integer, no extra fields; local name/age validation. |

Python thinking-off fields use `extra_body={"thinking":{"type":"disabled"}}`. This is a K2.6 option, not an option to assume for always-thinking models. [Model parameters][params]

## 2. Connection options are not generation parameters

| Option | Actual use, default handling and meaning | Source |
|---|---|---|
| api_key | Reads MOONSHOT_API_KEY for authentication, not sampling. Missing environment configuration fails rather than falling back to a hardcoded key. | [Quick start][start]; linked files |
| base_url | `https://api.moonshot.cn/v1`, routing the OpenAI SDK to Kimi, not OpenAI. | [Quick start][start] |
| timeout=120 | Explicit in every example; network timeout in seconds, not a server token budget or a two-minute whole-tool-task guarantee. | [SDK timeouts](https://developers.openai.com/api/reference/python#timeouts); linked files |
| max_retries | Not overridden in these files. SDK defaults retry certain connection/status failures twice; zero disables retries. Distinct from tool-loop turns. | [SDK retries](https://developers.openai.com/api/reference/python#retries) |
| extra_body | SDK extension entry point; thinking is merged into top-level HTTP JSON. Raw HTTP does not wrap it in extra_body. | [Model/cURL comparison][params]; [SDK extensions](https://developers.openai.com/api/reference/python#undocumented-request-params) |

SDK documentation explains client mechanics, not Kimi's support for OpenAI model capabilities. Installed versions follow [requirements-lock.txt](../../../requirements-lock.txt). Project recommendation: impose application-wide deadlines, retry budgets and tool idempotency rules separately; they are not K2.6 request fields.

## 3. Model, messages and budgets

| Field/limit | Meaning, default or boundary | Source |
|---|---|---|
| model | Exact kimi-k2.6, not an alias for kimi-k3 or K2.7; changing the name does not transfer another model's limits. | [Model comparison][params] |
| messages[].role | user input, system requirements, assistant history, tool results. Text content is a string; multimodal content is an array. | [Chat messages/content][chat] |
| History messages | Explicitly resent, not remembered by the Python client. Preserve assistant and associated tool results together. | [Multi-turn](https://platform.kimi.com/docs/guide/engage-in-multi-turn-conversations-using-kimi-api); [Tools][tools] |
| Context | 256K tokens; not a promise to output 256K. Preserved historical reasoning also consumes context. | [K2.6][model]; [Thinking retention][thinking] |
| max_tokens | Integer generation budget shared by reasoning_content and final content. Insufficient budget can leave reasoning only. Official multi-step-tool recommendation: at least 16000; 03/08 choose 16384/32768. | [Thinking budget][thinking]; [03](examples/03_thinking.py), [08](examples/08_thinking_tools.py) |
| Omitted budgets | Server default applies. K2.6's exact single-generation default and hard maximum were not explicitly confirmed in the cited sources and remain **unknown**. Do not import another model's max_completion_tokens range or treat an example budget as a maximum. | [Confirmed model parameters][params]; [Thinking guide][thinking] |

Project recommendation: a larger budget does not replace termination checks or require the model to spend all tokens. Handle truncation separately; do not substitute reasoning_content for a missing final answer. [03 checks](examples/03_thinking.py)

## 4. Thinking and sampling

| Field | K2.6 defaults, support and effects | Source |
|---|---|---|
| thinking.type | enabled by default, or disabled. 01 omits; 03/08 enable; other examples explicitly disable. | [Model parameters][params] |
| thinking.keep | Historical thinking is not retained across user rounds by default; all enables retention. Does not replace type. Return complete reasoning_content, increasing subsequent input/context and billing. | [Preserved thinking][thinking] |
| Current tool-loop history | Regardless of cross-user-round retention, retain the full assistant reasoning needed by the current tool loop. 08 retains SDK messages directly. | [Thinking/tools][thinking]; [08](examples/08_thinking_tools.py) |
| temperature | Not freely adjustable: thinking 1.0, non-thinking 0.6. Other values error; the official advice is to omit it, as every file does. | [Temperature][params] |
| top_p / n / penalties | Fixed top_p 0.95, n 1, presence_penalty/frequency_penalty 0. Do not copy other providers' ranges. | [Model comparison][params] |
| reasoning_effort / preserve_thinking | K2.6 does not support reasoning_effort. Its documented retention field is thinking.keep, not BaiLian's preserve_thinking. | [Parameters][params]; [Retention][thinking] |

Project advice: determinism is not factual accuracy. Fixed K2.6 sampling does not offer a “temperature 0 is more accurate” recipe. Provide evidence, a task and acceptance criteria, then validate output. [Official fixed values][params]

## 5. Streaming, usage and completion

stream defaults off. 02 enables it and reads delta.content/delta.reasoning_content rather than a complete message. stream_options.include_usage can request usage, but 02 does not set it and cannot promise streaming usage will be present; it records only returned values. [Streaming guide](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api); [Chat stream_options][chat]; [02](examples/02_streaming.py)

usage.prompt_tokens/completion_tokens/total_tokens and optional cache details are response statistics, not request budgets. length means a length limit; tool_calls is a tool stage, not final text success. Project examples require a final stop and nonempty text; streaming avoids unsafe empty-choices indexing and rejects missing/conflicting termination. [Chat response fields][chat]; [02](examples/02_streaming.py); [08](examples/08_thinking_tools.py)

## 6. Nested tool and JSON fields

| Field | Meaning, limits and example choice | Source |
|---|---|---|
| tools[].type=function | Declares a callable function, not an uploaded Python function executed by the server. | [Tools][tools] |
| function.name / description | Identifier and purpose; simulated weather in 05, simulated orders in 08. Name must match the local allowlist. | [Tools][tools]; [05](examples/05_tool_calling.py), [08](examples/08_thinking_tools.py) |
| function.parameters | Object JSON Schema, string properties, required fields and additionalProperties false. No tool-level strict is set; validate returned arguments locally. | [Tools][tools]; [05](examples/05_tool_calling.py), [08](examples/08_thinking_tools.py) |
| tool_choice | Default auto; none or a documented named form are available. Required is not supported by K2.6. Auto does not guarantee execution, so the demo checks at least one real local execution. | [Tool choice](https://platform.kimi.com/docs/guide/use-tool-choice); [08](examples/08_thinking_tools.py) |
| tool_calls[].id / function.arguments | Arguments are a JSON string. Batch-validate names/IDs/arguments before execution, then return role tool, matching tool_call_id and string content. Never invent an ID. | [Tools][tools]; [05](examples/05_tool_calling.py), [08](examples/08_thinking_tools.py) |
| response_format.type=json_object | 04 requests a JSON object; prompt still specifies JSON/fields. This is not business-schema validation. | [JSON Mode](https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api); [04](examples/04_json_output.py) |
| response_format.type=json_schema | 10 uses json_schema.name, schema and strict true. Simple K2.6 structures are covered; do not import newer models' guarantees for complex $ref/oneOf. | [Structured-output scope](https://platform.kimi.com/docs/guide/response_format) |
| Schema required / additionalProperties | 10 requires name and age and forbids extra keys. strict is inside json_schema, not a message/top-level field. | [response_format](https://platform.kimi.com/docs/guide/response_format); [10](examples/10_json_schema.py) |

City length 1–80, order IDs DEMO- plus four digits, name length, age 0–150, duplicate-ID rejection and a six-call limit are project safety/business rules, not official parameter ranges. Weather and orders are simulated locally, with no live backend. [05](examples/05_tool_calling.py); [08](examples/08_thinking_tools.py); [10](examples/10_json_schema.py)

## 7. Image and video shapes are not interchangeable

K2.6 inputs include text/images/video. 06 sends a real content array: text parts use type text/text, images use type image_url/image_url.url. 09 uses type video_url/video_url.url; do not place MP4 data in an image field. [K2.6 examples][model]

Image input accepts data URLs or ms:// file references, not direct HTTP(S) images. Do not serialize content parts into a JSON string. Official image formats exceed 06's PNG/JPEG subset; 09's MP4 example does not rule out other documented video formats. IMAGE_PATH, IMAGE_URL and VIDEO_PATH are local variables, not API fields. These files do not implement uploads, ms:// references or fps sampling. [Vision restrictions][vision]; [06](examples/06_vision.py), [09](examples/09_video.py)

Project recommendation: start with small media you are authorized to send. Recheck [official vision documentation][vision] before adding transports/formats or changing APIs; the same image_url name on another platform does not establish remote-URL support here. See [general parameters](../../../en/docs/parameters.md), [verification](../../../en/docs/verification.md) and [evidence policy](../../../en/docs/evidence-policy.md).

[start]: https://platform.kimi.com/docs/get-api-key
[params]: https://platform.kimi.com/docs/api/models-overview
[chat]: https://platform.kimi.com/docs/api/chat
[model]: https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart
[thinking]: https://platform.kimi.com/docs/guide/use-thinking-models
[tools]: https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls
[vision]: https://platform.kimi.com/docs/guide/use-kimi-vision-model
