# `deepseek-flash` API manual

[中文](README.md) · [Human guide](../../../human/README.en.md) · [Parameter reference](parameters.en.md)

English translation of the [Chinese manual](README.md). Executable code and official source manifests are shared. Official URLs are retained, even when their pages are in Chinese. This translation does not rerun or newly validate any API.

Source-check date in the original manual: **2026-10-13**. Machine-readable facts: [`deepseek-flash.json`](../../../skills/model-manual/references/models/deepseek-flash.json). Find source attribution and commands in [examples/sources.json](examples/sources.json), and browse the [example index](../../../en/docs/example-index.md).

Find calling files and attribution in [sources.json](examples/sources.json) and the [complete code directory](../../../en/docs/example-status.md). Reports, replies, statistics and execution fingerprints stay local. Recheck changed parameters or inputs. [Publishing policy](../../../en/docs/evidence-policy.md)

## 1. Identity

| Item | Recorded value | Official source |
|---|---|---|
| API model ID | `deepseek-flash` | [Models and pricing][pricing] |
| Serving version | DeepSeek-V4.1-Flash | [Models and pricing][pricing] |
| OpenAI-format Base URL | `https://api.deepseek.com` | [First call][first] |
| Context window | 1M tokens | [Models and pricing][pricing] |
| Maximum output | 384K tokens | [Chat API][chat] |
| Default mode | Thinking enabled, effort `high` | [Thinking mode][thinking] |
| Image input | Supported | [Vision][vision] |

Legacy names `deepseek-v4-flash` and `deepseek-v4-flash-vision-exp` remain accepted, but their models have retired and requests are routed to V4.1 Flash. Use `deepseek-flash` for new code. [Models and pricing][pricing] · [Change log](https://api-docs.deepseek.com/updates/)

## 2. Account and environment

Create a key at [DeepSeek API Keys](https://platform.deepseek.com/api_keys). The official example uses `DEEPSEEK_API_KEY` and the Base URL above. [First call][first]

From the repository root, after setting that environment variable:

```bash
python3 -m pip install -r requirements-lock.txt
python models/deepseek/deepseek-flash/examples/01_basic.py
```

Running examples sends real requests and may incur charges. Project policy allows keys only in environment variables or a Git-ignored `.env`, never in source, logs or commits. [Evidence/security policy](../../../en/docs/evidence-policy.md) · [Ignore rules](../../../.gitignore)

## 3. Basic Python, TypeScript and cURL calls

All three canonical files call `POST /chat/completions`. Use them rather than an abbreviated fragment without response checks. Fields are defined by the [Chat API][chat].

| Language | Shared executable file |
|---|---|
| Python | [01_basic.py](examples/01_basic.py) |
| TypeScript | [07_typescript.ts](examples/07_typescript.ts) |
| cURL with Python response validation | [08_curl.sh](examples/08_curl.sh) |

Installation, runtime requirements and real-execution commands are in [verification and reproduction](../../../en/docs/verification.md). These are the same files used by the Chinese documentation, not newly translated scripts.

## 4. Common request fields

| Field | Purpose and model-specific note |
|---|---|
| `model` | Select `deepseek-flash`. |
| `messages` | Ordered conversation; at least one message; system/user/assistant/tool roles. |
| `stream` | `true` returns SSE deltas. |
| `max_tokens` | Generation limit, 1–384K; input plus generated content must fit the context. |
| `thinking` | Thinking switch; pass through Python SDK `extra_body`. |
| `reasoning_effort` | `none`, `low`, `high`, `max`. |
| `response_format` | `{"type":"json_object"}` requests JSON output. |
| `tools` | Declare external functions; the application executes them. |
| `tool_choice` | Thinking mode does not support `required` or a forced named function. |
| `stop` | Stop on specified text; consult the API for limits. |
| `user_id` | Business-side user isolation; supplied through SDK `extra_body`. |

Source: [Chat API][chat]. See the [full parameter reference](parameters.en.md) for defaults, exact ranges and distinctions between SDK and server fields.

## 5. Streaming

Streaming uses `text/event-stream`. Text arrives in `choices[0].delta.content`; thinking arrives in `delta.reasoning_content`. [Chat API][chat] · [Thinking mode][thinking]

The checked [02_streaming.py](examples/02_streaming.py) handles termination and empty content safely. During inference, non-streaming responses may contain blank lines and streaming responses may contain `: keep-alive` comments; a raw HTTP parser should ignore these keep-alives. [Rate limits and isolation][rate]

DeepSeek's final-chunk usage behavior is not identical to every OpenAI-compatible service. Consult [streaming parameters](parameters.en.md#streaming) before changing the parser.

## 6. Thinking

Thinking is enabled by default with effort `high`. `reasoning_effort="none"` disables it; `low`, `high` and `max` enable it at the selected effort. Python examples use `extra_body={"thinking":{"type":"enabled"}}` or `disabled` for the explicit switch. [Thinking mode][thinking]

Thinking mode ignores `temperature`, `presence_penalty` and `frequency_penalty`. `top_p` works only in thinking mode, with an effective range of 0.95–1.0; non-thinking fixes it at 1.0. [Thinking mode][thinking]

Without tools, old `reasoning_content` need not be returned in later turns and is ignored even if supplied. Requests with `tools` must return every previous round's complete `reasoning_content`; otherwise the API returns 400. [Thinking mode][thinking]

Run [03_thinking.py](examples/03_thinking.py) for a checked on/off comparison, or [12_thinking_tools.py](examples/12_thinking_tools.py) for a complete thinking/tool loop. Their budgets and history handling are explained in [parameters](parameters.en.md#budget).

## 7. Multi-turn conversations

Chat Completions does not store ordinary conversation history for the application. Append prior user/assistant messages and send the required history in each `messages` request. [Multi-turn thinking guidance][thinking]

The shared [09_multi_turn.py](examples/09_multi_turn.py) adds only a successfully completed assistant response to history. It is not relying on a client object to remember the conversation.

## 8. JSON output

Set `response_format={"type":"json_object"}` and explicitly include “json” and the desired structure in a system or user message. Use an appropriate `max_tokens` budget to avoid truncating JSON. The official guide also warns that JSON output can occasionally be empty. [JSON output][json]

[04_json_output.py](examples/04_json_output.py) checks `finish_reason`, nonempty text, `json.loads` and a local business assertion. JSON format alone is not proof that field values are correct.

## 9. Tool calling

Declare a function's `name`, `description` and JSON Schema `parameters` inside `tools`. The model returns a function name and argument string; the application validates and executes it, then returns a `role="tool"` message with the matching `tool_call_id`. [Tool calls][tools]

[05_tool_calling.py](examples/05_tool_calling.py) implements a bounded, complete round trip with simulated weather. Validate all calls in a batch before executing any. This does not provide real-time weather.

Thinking/tool requests must retain historical `reasoning_content`. Disable thinking before using `tool_choice="required"` or a named forced function. [Thinking mode][thinking] · [Chat API][chat]

Strict tool mode is Beta: use `https://api.deepseek.com/beta`, set `strict: true` on every function, and follow the supported JSON Schema subset. See [13_strict_tools.py](examples/13_strict_tools.py) and [strict-mode documentation][tools].

## 10. Images

The model accepts JPEG, PNG, GIF and WebP through a public URL, base64 data URL or uploaded Files API `file_id`. In the documented Chat vision path, images belong in user messages; system/assistant images return 400. [Vision][vision]

Use [06_vision.py](examples/06_vision.py) for URL/local images, [10_vision_files.py](examples/10_vision_files.py) to upload or reuse a file ID, and [11_responses_vision.py](examples/11_responses_vision.py) for the Responses shape. Exact variables and field placement are covered in [image/file parameters](parameters.en.md#vision-files).

Documented limits include URLs up to 8192 characters, 32 MiB per inline/URL image, 64 MiB per `file_id` image and up to 600 images per request. See the original [Vision limits][vision] for pixel, aggregate-size and other restrictions.

## 11. Context cache and usage

Context caching is automatic. Reusing an already persisted prefix unit may hit the cache, but caching is best-effort and a hit is not guaranteed. Inspect `usage.prompt_cache_hit_tokens` and `usage.prompt_cache_miss_tokens`, the documented cache statistics. [Context caching][cache]

## 12. Dated price snapshot

The Chinese manual recorded these USD prices on **2026-10-13**, per one million tokens. They are a historical snapshot, not a quote for today; always reopen [official pricing][pricing].

| Item | Off-peak | Peak |
|---|---:|---:|
| Cached input | $0.003 | $0.006 |
| Uncached input | $0.15 | $0.30 |
| Output | $0.60 | $1.20 |

The cited page defines peak periods as weekdays 01:00–04:00 and 06:00–10:00 UTC, excluding Chinese public holidays. Other periods, including weekends and Chinese public holidays, are off-peak. [Models and pricing][pricing]

## 13. Concurrency, errors and retries

The recorded account-level concurrency limit is 2500; exceeding it returns HTTP 429. It is per account, not per API key. [Rate limits and isolation][rate]

| HTTP status | Official meaning | First action |
|---|---|---|
| 400 | Malformed request | Check JSON and messages. |
| 401 | Invalid API key | Check credentials. |
| 402 | Insufficient balance | Check the account balance. |
| 422 | Invalid parameter | Correct parameters. |
| 429 | Requests too fast | Reduce concurrency/request rate. |
| 500 | Server error | Wait briefly and retry. |
| 503 | Server overload | Wait briefly and retry. |

Source: [Error codes](https://api-docs.deepseek.com/quick_start/error_codes/). Project recommendation: bounded exponential backoff for 429/500/503 and network timeouts; do not blindly retry 400/401/402/422, masking configuration errors or repeating costs. [Project policy](../../../en/docs/evidence-policy.md)

## 14. Documented capability matrix

This table records official support, not a claim that every capability was live-tested. Read [historical results](../../../en/docs/verification-status.md) and [per-file results](../../../en/docs/example-status.md) separately.

| Capability | Recorded status | Official source |
|---|---|---|
| Chat Completions / streaming | Documented | [API][chat] |
| Thinking and effort | Documented | [Thinking mode][thinking] |
| JSON Object | Documented | [JSON output][json] |
| Tool calling | Documented | [Tool calls][tools] |
| Strict tool schema | Beta | [Tool calls][tools] |
| Images | Documented | [Vision][vision] |
| Responses API | Documented | [Responses guide][responses] |
| Anthropic API | Documented | [Model table][pricing] |
| Context cache | Automatic | [Caching][cache] |
| Chat Prefix Completion | Beta | [Model table][pricing] |
| FIM Completion | Non-thinking only | [Model table][pricing] |

## 15. Project rules for agents

Use the exact current ID, read keys only from `DEEPSEEK_API_KEY`, and never hardcode or print them. Explain the default thinking mode before explicitly disabling it for a low-latency task. JSON implementations need a JSON prompt, format setting, parser and truncation checks. Validate tool names/arguments before execution and preserve thinking history when using thinking/tools. Price claims need a check date and an official link. Leave undocumented capabilities unknown. These are project rules grounded in the [model card](../../../skills/model-manual/references/models/deepseek-flash.json) and [evidence policy](../../../en/docs/evidence-policy.md).

## 16. Verification and reproduction

Calling code and official attribution are in [sources.json](examples/sources.json). Execution records stay local; see [reproduction](../../../en/docs/verification.md) for setup and checks.

The later strict unified-workflow results are listed in [historical verification status](../../../en/docs/verification-status.md). Current original-file execution is listed in [example status](../../../en/docs/example-status.md); neither automatically proves arbitrary changed requests.

Offline checks send no requests. The shared [tests/verify_deepseek_flash.py](../../../tests/verify_deepseek_flash.py) is a real-request unified-verifier entry point, not an executor of every example. Setup, per-file commands, report fields and exit codes are in [verification](../../../en/docs/verification.md).

## 17. Common pitfalls

HTTP 200 alone is insufficient. `finish_reason="length"` can mean an incomplete answer, and `usage.completion_tokens_details.reasoning_tokens` reports reasoning usage. JSON mode without an explicit JSON instruction may generate whitespace until its token limit. [Chat API][chat] · [JSON output][json]

The executable files check completion, nonempty final text and streaming termination. Their bounded simulated tools demonstrate protocol flow, not real business data. See [production pitfalls](../../../en/docs/production-pitfalls.md) and the [parameter reference](parameters.en.md).

[pricing]: https://api-docs.deepseek.com/quick_start/pricing/
[first]: https://api-docs.deepseek.com/guides/codex
[chat]: https://api-docs.deepseek.com/api/create-chat-completion/
[thinking]: https://api-docs.deepseek.com/guides/thinking_mode/
[vision]: https://api-docs.deepseek.com/guides/vision/
[rate]: https://api-docs.deepseek.com/quick_start/rate_limit/
[json]: https://api-docs.deepseek.com/guides/json_mode/
[tools]: https://api-docs.deepseek.com/guides/tool_calls/
[cache]: https://api-docs.deepseek.com/guides/kv_cache/
[responses]: https://api-docs.deepseek.com/guides/responses_api/
