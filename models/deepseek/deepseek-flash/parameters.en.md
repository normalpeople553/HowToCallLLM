# `deepseek-flash` example parameters

[中文](parameters.md) · [Human guide](../../../human/README.en.md) · [Model manual](README.en.md)

English translation of the [Chinese parameter reference](parameters.md), checked there on **2026-10-14**. Code, source manifests and reports are shared; official URLs are unchanged, including Chinese sources. Translation does not rerun API verification. An SDK's ability to serialize a field is not evidence of DeepSeek support. Project settings below are attributed to the linked executable sources; current execution evidence is in [example status](../../../en/docs/example-status.md) and [sources.json](examples/sources.json).

Jump to [identity](#identity), [sampling](#sampling), [budget/thinking](#budget), [streaming](#streaming), [tools](#tools), [JSON](#json), [images/files](#vision-files), [Responses](#responses), [Beta/FIM](#beta), [SDK/local checks](#sdk), or the [file map](#example-map).

<a id="identity"></a>
## 1. Identity and messages

| Field/configuration | Meaning and actual use | Source |
|---|---|---|
| `model="deepseek-flash"` | API ID, currently serving DeepSeek-V4.1-Flash. An old alias does not imply old model weights. | [Models][pricing] |
| `base_url` | Ordinary examples use `https://api.deepseek.com`, not OpenAI's service; Beta has a separate path below. | [First call][first] |
| `api_key` / `Authorization: Bearer …` | Authentication, not a prompt/generation parameter. `DEEPSEEK_API_KEY` is this project's environment-variable choice. | [First call][first]; [01](examples/01_basic.py) |
| `messages` | Ordered Chat history, at least one message. Text content is a string; image input uses content-part arrays. | [Chat messages][chat] |

`system` supplies system requirements, `user` the input, `assistant` prior model messages and `tool` an application's tool result. A result's `tool_call_id` must match the model's call ID; do not invent a replacement. [Message definitions][chat]

Chat does not retain history for the client. Resend the required history each turn. [09](examples/09_multi_turn.py) appends an assistant message only after successful completion, so a failed/truncated round does not become completed history. [Official multi-turn guide](https://api-docs.deepseek.com/guides/multi_round_chat/)

<a id="sampling"></a>
## 2. Sampling is not an accuracy percentage

| Parameter | What it controls | This model's limits |
|---|---|---|
| `temperature` | Sampling randomness: higher is more varied, lower more focused; not a correctness score. | `[0,2]`, default `1`; ineffective in thinking mode. |
| `top_p` | Nucleus sampling: selects candidate tokens by cumulative probability, rather than scaling randomness as temperature does. | Input `(0,1]`, default `1`; only effective in thinking mode, where the effective range is `[0.95,1]` and lower inputs become `0.95`. Non-thinking fixes it at `1` and ignores the supplied value. |

These are DeepSeek-specific rules. The official recommendation is generally to change one of temperature/top_p, not both; none of these examples explicitly sets either. [Chat sampling][chat] · [Thinking restrictions][thinking]

Project interpretation: changing randomness does not establish factual correctness. Neither a higher temperature nor a lower one removes the need to verify an answer.

<a id="budget"></a>
## 3. Context, output budget and thinking

| Name | Meaning, range and distinction | Source |
|---|---|---|
| Model context `1M` | Input/output capacity, not a request to set `max_tokens=1000000`. | [Model table][pricing]; [Context definition](https://api-docs.deepseek.com/api/list-models/) |
| Chat `max_tokens` | Per-generation limit `1..393216`; input plus generation must still fit the context. Omitted defaults: non-thinking `8192`, thinking `65536`, effort `max` `131072`. | [Chat budget][chat] |
| `thinking.type` | `enabled` or `disabled`, enabled by default. Omission in 01/07/08 does not disable thinking. | [Thinking mode][thinking] |
| Chat `reasoning_effort` | `none` disables; `low`/`high`/`max` enable at that effort. Default `high`; 03 explicitly chooses high, without conflicting switches. | [Chat configuration][chat]; [03](examples/03_thinking.py) |
| `reasoning_content` | Returned reasoning, separate from final `content`; also returned in thinking/tool history. It is not an extra output-budget parameter. | [Thinking mode][thinking] |

Budget accounting must be distinguished by API. Chat's `usage.completion_tokens_details.reasoning_tokens` is a completion-usage breakdown; `completion_tokens` is not the final answer's character count. However, the cited Chat `max_tokens` wording does not explicitly state a “visible output + reasoning” budget equation as Responses does; its precise inclusion rule remains **not explicitly confirmed** here. Responses `max_output_tokens` explicitly includes both. [Chat usage][chat] · [Responses definition][response-api]

Project budgets, not defaults or model limits: thinking tools 12 use `16384`; non-thinking strict tools 13 use `2048`; prefix 14 uses `1024`; FIM 15 uses `128`; Responses 11 uses `2048`. Other Chat examples omit an explicit budget. No selected value guarantees enough output for every task. [Shared implementation](examples/_support.py); [11](examples/11_responses_vision.py); [14](examples/14_prefix_completion.py); [15](examples/15_fim_completion.py)

<a id="streaming"></a>
## 4. Streaming, usage and termination

`stream=True` returns SSE deltas; it does not select a different model or turn off thinking. Chat ends with `data: [DONE]`. `stream_options` may only be used with `stream=True`. [Chat streaming][chat]

DeepSeek specifies that the final chunk carries usage whether or not `stream_options.include_usage` is true. It contains one choice with no new content and a finish reason; **there is no additional usage-only chunk**. `include_usage=True` additionally makes prior chunks carry `usage:null`. [02](examples/02_streaming.py) does not set this option; defensive empty-choices handling does not assert that DeepSeek currently sends empty choices. [Chunk protocol][chat]

`finish_reason` is a response field. Ordinary examples require `stop`; `length` means a length limit, `tool_calls` a tool stage, and `aborted` is not completion. The project also rejects a disconnected stream, usage alone or empty final text even if HTTP succeeded. [Finish reasons][chat]; [02](examples/02_streaming.py); [Shared checks](examples/_support.py)

<a id="tools"></a>
## 5. Tool schemas, selection and strict mode

| Field | Meaning | Source |
|---|---|---|
| `tools[].type="function"` | Declare a function. The server does not execute local Python; the application validates, executes and returns the result. | [Tool flow][tools] |
| `function.name` / `description` | `get_weather` identifies the example function; its description guides selection, not execution permission. | [Chat tools][chat]; [05](examples/05_tool_calling.py) |
| `function.parameters` | JSON Schema: object, string city property, `required=["city"]`, `additionalProperties=false`. | [Tool schemas][tools] |
| `tool_choice` | `none`: no tool; `auto`: text or tool; `required`: at least one tool; a named function can be forced. Thinking mode rejects required/named choices. 12/13 explicitly use auto; 05 omits it, with the documented tools-present default auto. | [Chat selection][chat] |
| `function.strict=True` | Beta in 13: supported-schema conformance, not truthful cities/business correctness. Use Beta URL, strict on every function, all object properties required and `additionalProperties=false`. | [Strict mode][tools] |

Thinking/tool requests must preserve complete assistant messages, including `tool_calls` and `reasoning_content`. Missing required reasoning history can yield 400. The shared loop used by 12 preserves complete SDK messages. [Thinking/tool history][thinking]; [Implementation](examples/_support.py)

Project rules: weather is **simulated**, with no weather-network request. Validate the entire batch, allowlisted name, unique IDs, JSON/type and city length 1–80 before any execution. At most six model turns; a direct answer without any executed tool does not complete the tool demo. `max_model_turns`, city limits and execution counters are local, not DeepSeek parameters; strict does not replace them. [05](examples/05_tool_calling.py); [12](examples/12_thinking_tools.py); [13](examples/13_strict_tools.py); [Helper](examples/_support.py)

<a id="json"></a>
## 6. JSON output

04 requests `response_format={"type":"json_object"}` and explicitly asks for JSON in a system/user prompt. This is not arbitrary JSON Schema structured output or a guarantee about business values; the guide warns about empty/truncated output. [JSON mode][json]

The example disables thinking, checks finish reason and nonempty content, calls `json.loads` and asserts that `ok` is Boolean `True`. Parsing and the business assertion are local checks, not server parameters. [04](examples/04_json_output.py)

<a id="vision-files"></a>
## 7. Images, detail and Files

| Field | Explanation and restrictions | Source |
|---|---|---|
| Chat `content[].type="text"` / `text` | The text question, beside image parts in a user message. | [Vision shape][vision] |
| `image_url.url` | Public HTTP(S) URL or `data:image/…;base64,…`. JPEG/PNG/GIF/WebP are detected from actual bytes. | [Vision][vision] |
| `image_url.detail` | `low`: 512×512; high/original retain original; auto currently equals original. 06 omits detail; 11 uses the Responses top-level part field. | [Detail levels][vision] |
| `files.create(file=…,purpose="user_data")` | Multipart upload, not Chat JSON. Required purpose is user_data. | [Files][files] |
| `expires_after` | `anchor="created_at"`, `seconds=3600..2592000`; omission means permanent storage. 10's one-hour expiry is project policy, not the default. | [Expiry][files]; [10](examples/10_vision_files.py) |
| `{"type":"file","file_id":"file-api-…"}` | Chat reference to an uploaded image: file_id is top-level in the part, not `file.file_id`. Files are scoped by API key. | [Vision references][vision]; [File scope][files] |

Relevant byte limits: URL length 8192; remote/inline image 32 MiB; inline request body 48 MiB including base64 expansion; file-ID image 64 MiB. `max_tokens` does not change byte limits. [Vision limits][vision]

Local environment variables are not API fields. 06 converts `IMAGE_URL`/`IMAGE_PATH` to image_url.url; its local branch only accepts the JPEG/PNG suffixes listed in its source, not all supported model formats. 10 requires exactly one of IMAGE_PATH/IMAGE_FILE_ID; the latter reuses a file without reuploading. 11 uses IMAGE_DETAIL, default auto. Shared header/size/URL prechecks do not implement every official limit. HTTPS-only remote input is a project restriction; official input allows HTTP(S). [06](examples/06_vision.py); [10](examples/10_vision_files.py); [11](examples/11_responses_vision.py); [Helper](examples/_support.py)

<a id="responses"></a>
## 8. Responses uses a different shape

11 uses `/responses` on the ordinary Base URL, not `/chat/completions`. [Responses API][response-api]

| Actual field | Meaning |
|---|---|
| `input` | Replaces Chat messages; here user items with input_text/input_image parts. |
| `input_image.image_url` / `detail` | URL is a string, not Chat's `{url:…}` object; detail is its sibling. file_id is also supported, mutually exclusive with image_url; detail is ignored with file_id. 11 does not implement that file-ID branch. |
| `reasoning={"effort":"none"}` | Responses thinking-off configuration, not Chat's thinking field. Effort accepts none/low/high/max. |
| `max_output_tokens=2048` | Explicitly includes visible output **and reasoning tokens**; 2048 is a project budget, not the model maximum. |

Sources: [Responses request/response][response-api], [Responses images][vision]. The example requires `response.status="completed"` and nonempty output_text; incomplete/failed do not pass. [11](examples/11_responses_vision.py)

The API is stateless: do not assume OpenAI server-stored conversations or omit history using previous_response_id. 11 is not streaming; Responses events differ from Chat's `[DONE]`, so 02's parser cannot simply be reused. [Compatibility guide][responses]

<a id="beta"></a>
## 9. Beta prefix completion and FIM

| Example | Actual parameters and meaning | Source |
|---|---|---|
| 13 strict tools | Beta Base URL `https://api.deepseek.com/beta`, function.strict true; still Chat. | [Strict tools][tools] |
| 14 prefix | Last message is assistant with the supplied code prefix and `prefix=True` **inside that message**. Chat stop sequence `stop=["```"]` stops at the fence; max_tokens 1024 is the example budget. | [Prefix guide](https://api-docs.deepseek.com/guides/chat_prefix_completion/); [14](examples/14_prefix_completion.py) |
| 15 FIM | Beta `client.completions.create` calls `/completions`. prompt precedes the gap, optional suffix follows it; output fills the gap, not a Chat message. Example max_tokens 128; FIM maximum 4K and non-thinking only. | [FIM](https://api-docs.deepseek.com/guides/fim_completion/); [Model support][pricing] |

`make_client(beta=True)` is a local helper option selecting the URL, not a JSON model field. Reattaching a prefix/suffix for display is local formatting. [Helper](examples/_support.py); [14](examples/14_prefix_completion.py); [15](examples/15_fim_completion.py)

<a id="sdk"></a>
## 10. SDK configuration and local validation

| Configuration/check | What it controls |
|---|---|
| Python `timeout=120` | Network timeout in seconds, not 120 output tokens or a guaranteed 120-second complete tool task. |
| TypeScript `timeout:120_000` | Network timeout in milliseconds, corresponding to Python's 120 seconds. |
| Python max_retries / TypeScript maxRetries | Automatic SDK retries; zero disables them. Distinct from six model/tool turns. Current examples omit an explicit retry setting, so omission is not “no retries.” |
| `extra_body={"thinking":…}` | SDK extension mechanism merging top-level thinking into HTTP JSON; the server does not receive an outer extra_body model switch. |

SDK sources: [Python](https://developers.openai.com/api/reference/python), [TypeScript](https://developers.openai.com/api/reference/typescript). Actual settings: [01](examples/01_basic.py), [07](examples/07_typescript.ts), [helper](examples/_support.py). SDK mechanics do not establish DeepSeek support for an extra field.

`completed_text`, `image_bytes(max_bytes=…)`, max_model_turns, JSON business assertions, nonempty checks and not printing raw errors are project validation/security logic, not generation fields for API JSON. [Helper](examples/_support.py); [04](examples/04_json_output.py); [05](examples/05_tool_calling.py)

<a id="example-map"></a>
## 11. Every executable file

Public connection settings omitted below are explained in [identity](#identity)/[SDK](#sdk). Unset does not mean disabled. Each linked source is authoritative for the row's project configuration.

| File | Actual request fields beyond common identity | Explanation |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | model, user messages; thinking/budget omitted | [Identity](#identity), [defaults](#budget) |
| [02_streaming.py](examples/02_streaming.py) | model, user messages, stream true, thinking disabled; no stream_options | [Streaming](#streaming), [thinking](#budget) |
| [03_thinking.py](examples/03_thinking.py) | Same user question: disabled versus enabled + reasoning_effort high | [Thinking](#budget) |
| [04_json_output.py](examples/04_json_output.py) | model, JSON-requesting user message, response_format json_object, thinking disabled | [JSON](#json) |
| [05_tool_calling.py](examples/05_tool_calling.py) | model, system/user/full assistant/tool history, tools, thinking disabled; no explicit tool_choice | [Tools](#tools) |
| [06_vision.py](examples/06_vision.py) | model, user text/image_url.url parts, thinking disabled; detail omitted | [Vision](#vision-files) |
| [07_typescript.ts](examples/07_typescript.ts) | model, user messages; client apiKey/baseURL/timeout 120_000 | [Identity](#identity), [SDK](#sdk), [defaults](#budget) |
| [08_curl.sh](examples/08_curl.sh) | Chat POST, Bearer/JSON headers, model and user messages | [Identity](#identity), [defaults](#budget) |
| [09_multi_turn.py](examples/09_multi_turn.py) | model, accumulated system/user/assistant history, thinking disabled | [History](#identity) |
| [10_vision_files.py](examples/10_vision_files.py) | Upload file/purpose/expires_after; Chat model, user text/top-level file_id, thinking disabled | [Files](#vision-files) |
| [11_responses_vision.py](examples/11_responses_vision.py) | model/input/input_text/input_image/image_url/detail; reasoning.effort none; max_output_tokens 2048 | [Responses](#responses) |
| [12_thinking_tools.py](examples/12_thinking_tools.py) | Shared model/messages/tools/tool_choice auto; thinking enabled; max_tokens 16384 | [Tools](#tools), [budget](#budget) |
| [13_strict_tools.py](examples/13_strict_tools.py) | Beta client; shared tools strict true; tool_choice auto; thinking disabled; max_tokens 2048 | [Tools](#tools), [Beta](#beta) |
| [14_prefix_completion.py](examples/14_prefix_completion.py) | Beta Chat, model/messages with final-assistant prefix; stop; max_tokens 1024; thinking disabled | [Prefix](#beta) |
| [15_fim_completion.py](examples/15_fim_completion.py) | Beta Completions; model/prompt/suffix/max_tokens 128 | [FIM](#beta) |

[_support.py](examples/_support.py) supports 09–15; it is not a standalone API feature example. Its connection, image checks and tool loop are explained above. See [evidence policy](../../../en/docs/evidence-policy.md), [verification](../../../en/docs/verification.md) and [general parameter navigation](../../../en/docs/parameters.md).

[pricing]: https://api-docs.deepseek.com/quick_start/pricing/
[first]: https://api-docs.deepseek.com/quick_start/pricing-details-cny/
[chat]: https://api-docs.deepseek.com/api/create-chat-completion/
[thinking]: https://api-docs.deepseek.com/guides/thinking_mode/
[tools]: https://api-docs.deepseek.com/guides/tool_calls/
[json]: https://api-docs.deepseek.com/guides/json_mode/
[vision]: https://api-docs.deepseek.com/guides/vision/
[files]: https://api-docs.deepseek.com/guides/files_api/
[response-api]: https://api-docs.deepseek.com/api/create-response/
[responses]: https://api-docs.deepseek.com/guides/responses_api/
