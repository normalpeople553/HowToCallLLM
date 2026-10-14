# `MiniMax-M2.7` example parameters

[中文](parameters.md) · [Human guide](../../../human/README.en.md) · [Model manual](README.en.md)

English translation of the [Chinese reference](parameters.md), checked there on **2026-10-14**. This covers the **M2.7 hosted API** and existing files, not M3/M3.1 vision, reasoning-depth or other newer parameters. Shared code, sources and reports are unchanged; original official URLs are retained, including Chinese pages. Translation does not rerun API verification. Parameter attribution is not execution evidence: see [sources.json](examples/sources.json) and [example status](../../../en/docs/example-status.md).

Check lifecycle before calling: M2.7 new-user access ends **2026-10-19**, pay-as-you-go API service ends **2026-11-18**, and M Plan/Token Plan old-name requests route to M3.1 Flash Preview from **2026-10-19**. An old ID does not prove original-model execution. This reference does not silently replace the requested model. [Official notice][lifecycle]

Jump to [identity](#identity), [sampling](#sampling), [budget](#budget), [thinking](#thinking), [streaming](#streaming), [tools](#tools), [unconfirmed combinations](#boundaries), [native API](#native), [SDK/local checks](#sdk), or [file map](#example-map).

<a id="identity"></a>
## 1. Identity and messages

| Field/configuration | Meaning | Official/source evidence |
|---|---|---|
| model MiniMax-M2.7 | Exact ID, not highspeed or M3; fixed in every file here. | [Chat model list][chat] |
| base_url `https://api.minimax.cn/v1` | Mainland-China SDK service root; Chat endpoint /v1/chat/completions. Not the full native endpoint. | [SDK setup][sdk] |
| api_key / Bearer header | Authentication, not message text. MINIMAX_API_KEY is the project's environment-variable name. | [Authentication][chat]; [01](examples/01_basic.py) |
| messages | Ordered history; only text and tools are sent by this directory. | [Chat messages][chat] |

Project roles: system requirements, user question, full assistant model response, tool result paired by tool_call_id. 06 accumulates history and 05 retains complete assistant objects, not just content. The official full-history requirement explicitly covers M2.7. [05](examples/05_tool_calling.py); [06](examples/06_multi_turn.py); [SDK history][sdk]

International documentation also gives `https://api.minimax.io/v1`. These files use mainland China; they do not claim keys work across regions or that historical api.minimaxi.com currently remains compatible. [International SDK documentation](https://platform.minimax.io/docs/api-reference/text-openai-api)

<a id="sampling"></a>
## 2. Sampling is not an accuracy control

| Parameter | M2.7 compatible-Chat meaning | Source |
|---|---|---|
| temperature | Randomness coefficient, `[0,2]`, default 1. Higher more random, lower more deterministic. | [Chat temperature][chat] |
| top_p | Nucleus threshold, `[0,1]`. M2.x default 0.9, not the M3-family 0.95 on the same page. | [Chat top_p][chat] |

Temperature scales randomness; nucleus sampling selects candidate tokens by cumulative probability. The [DeepSeek official sampling definition](https://api-docs.deepseek.com/api/create-chat-completion/) is cited **only for that concept**, not to borrow DeepSeek values/mode restrictions. MiniMax ranges remain those above.

Project interpretation: randomness does not imply correctness or protection from hallucinations. These files omit both fields, and no cited official basis says M2.7 ignores them in thinking mode; do not import DeepSeek's behavior. Native ranges also differ; see [section 8](#native).

<a id="budget"></a>
## 3. Context and generation budget

M2.7's **204800-token** context is a model capacity, not another name for max_completion_tokens. Do not assume maximum input and maximum output can both be filled independently. [Model window][sdk]

| Field | Confirmed definition | What remains unconfirmed |
|---|---|---|
| max_completion_tokens | Compatible-Chat generation upper limit: integer at least 1, M2.x maximum 204800, recommended 65536. A limit can produce length; inspect termination after adjusting budget. | Maximum is not default or promised final-answer length. The new M2.7 field's precise reasoning/final-text inclusion equation is **unknown** here. |
| max_tokens | Deprecated old field. SDK docs explicitly include reasoning tokens in this old budget; too small can yield length with empty content. | Do not treat that old-field wording as confirmation of the new field, or fill M2.7 gaps using M3. |

Sources: [Chat budget/range][chat], [SDK old-field accounting][sdk]. The current cited pages do not explicitly confirm M2.7's new-field default; this reference does not guess.

All six runnable files set max_completion_tokens 16384: a **project demonstration budget**, not an official default or sufficient-for-all-tasks guarantee. Short README fragments may use smaller values; the executed source is authoritative. [01](examples/01_basic.py); [02](examples/02_streaming.py); [03](examples/03_thinking.py); [05](examples/05_tool_calling.py); [06](examples/06_multi_turn.py); [07](examples/07_native_curl.sh)

<a id="thinking"></a>
## 4. Thinking switch, depth and output format

| Field | M2.7 boundary |
|---|---|
| thinking.type | M2.x thinking cannot be disabled. Adaptive is default; disabled is accepted but ineffective. The files do not present it as successful thinking-off configuration. |
| reasoning_effort | Current documentation restricts effective depth adjustment to M3.1 Flash Preview; others ignore it. Not set for M2.7, with no invented low/high levels. |
| reasoning_split true | **Output-format** switch, separating reasoning_content, not turning thinking off. False can retain thinking inside content's `<think>…</think>`. Python sends true through extra_body; native example omits it. |

Source: [Chat thinking/reasoning fields][chat]. Do not change only model in an M3.1 sample and claim M2.7 supports every field.

For display, files may strip leading complete think blocks and then verify remaining final text. Tool history must retain the original assistant with thinking/tool_calls; display-only text must not overwrite it. 03 displays reasoning_content only if actually returned; its absence is not proof thinking was disabled. [Complete return requirements][sdk]; [03](examples/03_thinking.py); [05](examples/05_tool_calling.py)

<a id="streaming"></a>
## 5. Streaming, usage and success

stream true sends chunks. 02 also requests stream_options.include_usage true. These concern transport/statistics, not output budget or thinking mode. [Streaming][chat]; [Usage option][sdk]

usage, finish_reason and base_resp are **response fields**, not generation inputs. Business status, usage and sensitive-content flags are documented; HTTP 200 does not replace checking complete final content. [Response fields][chat]

Project acceptance: 02 tolerates empty-choices usage chunks and collects actual usage, but requires stop and nonempty final text. Missing termination, length, unexpected tool deltas, duplicate/conflicting finishes and post-finish generation error. Ordinary files check available business status; native 07 requires base_resp.status_code zero. These are safeguards, not assertions that every defensive branch is a documented server behavior. [02](examples/02_streaming.py); [01](examples/01_basic.py); [07](examples/07_native_curl.sh)

<a id="tools"></a>
## 6. Tool parameters and complete round trips

Compatible Chat supports function tools, and the complete-assistant history rule includes M2.7. [Chat tools][chat]; [SDK function-call requirements][sdk]

The following is [05's](examples/05_tool_calling.py) project-defined tool, not a built-in MiniMax weather service:

| Field | Meaning in this example |
|---|---|
| tools[].type function | Declare a function; actual execution is local. |
| function.name get_weather / description | Local allowlist routing and purpose; no arbitrary code-execution authority. |
| function.parameters.type object | JSON arguments; properties.city.type string. |
| required city / additionalProperties false | Declare city required and no extra keys. Local code still validates; this does not assert server strict-schema enforcement. |
| Returned function.arguments | Model-generated JSON string to parse/validate, never execute as code. |
| role tool / tool_call_id / content | Return simulated output, paired to the original call, then obtain the final answer. |

05 **does not set tool_choice or strict**. Current compatible-Chat documentation is insufficient to promise forced/named selection or strict guarantees for M2.7. Native separately lists none/auto; that does not establish additional compatible-Chat values. [Chat parameter table][chat]; [Native selection][native]

Project policy: fixed simulated weather, no live weather request. Validate the full batch before execution: allowlisted name, unique IDs, JSON object, city string and 1–80-character bound. At most six model turns, and at least one executed tool is required for the demo to complete. max_model_turns, execution counters and city limits are local, not MiniMax fields. Real model traffic with a simulated tool is not real weather evidence. [05](examples/05_tool_calling.py)

<a id="boundaries"></a>
## 7. Unconfirmed combinations

| Feature/field | Current M2.7 integration boundary | Official evidence |
|---|---|---|
| response_format / JSON Schema | No 04 JSON file. Asking for JSON in a prompt is not a protocol guarantee. | [Native docs][native] restrict the field to MiniMax-Text-01; [compatible Chat][chat] does not confirm M2.7 JSON mode. |
| image_url, video, detail, Files multimodal references | Not added to M2.7. | [SDK multimodal section][sdk] specifies M3/M3.1; do not use their detail/size rules as M2.7 specifications. |
| Responses, FIM, DeepSeek prefix/Beta strict | Not integrated for this model; do not copy DeepSeek endpoint/Base URL. | [Compatible Chat][chat] and [legacy native Chat][native] do not establish these combinations. |

<a id="native"></a>
## 8. Native cURL differs from compatible Chat

07 calls `https://api.minimax.cn/v1/text/chatcompletion_v2`. The native page still lists M2.7/max_completion_tokens while marking the API deprecated. Being listed does not prove every account can call it now. This is not /v1/chat/completions. [Native endpoint][native]

Its headers are Bearer authentication and Content-Type application/json. JSON contains only model, user messages and max_completion_tokens 16384; no reasoning_split. [Native request definition][native]; [07](examples/07_native_curl.sh)

Native temperature/top_p ranges are both `(0,1]`, differing from compatible Chat. The old default table does not explicitly list M2.7; do not substitute M2 defaults. Native max_completion_tokens explicitly states at least 1, but this reference does not import an otherwise unstated native M2.7 upper bound from another endpoint. 07 does not set sampling fields. [Native sampling/budget][native]

<a id="sdk"></a>
## 9. SDK and local safety settings

| Setting | Layer and meaning |
|---|---|
| timeout 120 | Python SDK network timeout in seconds, not a generation maximum or a whole-loop 120-second guarantee. |
| max_retries | SDK automatic retries; zero disables. Not explicitly set here; distinct from model turns and not sent to the model. |
| extra_body reasoning_split true | SDK merges top-level reasoning_split into JSON; not an outer server extra_body switch. |
| cURL --max-time 180 | Local transport limit in seconds, not tokens. --fail detects HTTP errors; business status still needs validation. |
| max_model_turns / city validation / display_text | Project loop/input/display logic, not server generation parameters. |

Sources: [OpenAI Python SDK](https://developers.openai.com/api/reference/python), [curl manual](https://curl.se/docs/manpage.html), and the actual [01](examples/01_basic.py), [05](examples/05_tool_calling.py), [07](examples/07_native_curl.sh) files. SDK extensibility does not imply vendor support for arbitrary fields.

<a id="example-map"></a>
## 10. Every runnable file

Python files share environment-key authentication, mainland-China Base URL and timeout 120. All six share model MiniMax-M2.7 and max_completion_tokens 16384. Linked files are the source for actual project settings.

| File | Additional actual fields/behavior | Explanation |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | user messages, extra_body reasoning_split true; final-text checks | [Messages](#identity), [budget](#budget), [thinking](#thinking), [SDK](#sdk) |
| [02_streaming.py](examples/02_streaming.py) | user messages, reasoning_split true, stream true, stream_options.include_usage true | [Streaming](#streaming), [budget](#budget), [thinking](#thinking) |
| [03_thinking.py](examples/03_thinking.py) | user messages, reasoning_split true; no thinking/reasoning_effort | [Thinking boundary](#thinking), [budget](#budget) |
| [05_tool_calling.py](examples/05_tool_calling.py) | system/user/full assistant/tool messages, tools, reasoning_split true; no tool_choice/strict | [Tools](#tools), [thinking format](#thinking) |
| [06_multi_turn.py](examples/06_multi_turn.py) | Accumulated system/user/full assistant history, reasoning_split true | [History](#identity), [thinking history](#thinking) |
| [07_native_curl.sh](examples/07_native_curl.sh) | Native POST, Bearer/JSON headers, user messages; no reasoning_split; max-time 180 | [Native interface](#native), [transport](#sdk) |

Missing 04 is intentional, not an overlooked file. Confirm **exact model + endpoint** support before adding new features/files/evidence. See [boundaries](#boundaries), [general parameters](../../../en/docs/parameters.md), [verification](../../../en/docs/verification.md) and [evidence policy](../../../en/docs/evidence-policy.md).

[lifecycle]: https://platform.minimax.cn/docs/guides/models-intro
[chat]: https://platform.minimax.cn/docs/api-reference/text-chat-openai
[sdk]: https://platform.minimax.cn/docs/api-reference/text-openai-api
[native]: https://platform.minimax.cn/docs/api-reference/text-post
