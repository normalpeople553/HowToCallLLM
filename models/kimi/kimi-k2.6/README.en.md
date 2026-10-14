# `kimi-k2.6` API manual

[中文](README.md) · [Human guide](../../../human/README.en.md) · [Parameter reference](parameters.en.md)

English translation of the [Chinese manual](README.md), whose official-source check date is **2026-10-13**. Code, manifests and reports are shared; original official URLs are retained, including Chinese pages. Translation does not rerun API verification. Machine facts: [`kimi-k2.6.json`](../../../skills/model-manual/references/models/kimi-k2.6.json).

Use [sources.json](examples/sources.json) and the [example index](../../../en/docs/example-index.md) to find code. Read [historical unified verification](../../../en/docs/verification-status.md) separately from [per-file execution](../../../en/docs/example-status.md). Results apply only to recorded source, parameters, input and environment. Fragments, modified requests and arbitrary generated combinations do not inherit passes. [Evidence policy](../../../en/docs/evidence-policy.md)

## 1. At a glance

| Item | Recorded value | Official source |
|---|---|---|
| Model ID | `kimi-k2.6` | [K2.6][model] |
| Base URL | `https://api.moonshot.cn/v1` | [Quick start][start] |
| Context | 256K tokens | [K2.6][model] |
| Inputs | Text, images, video | [K2.6][model] |
| Key capabilities | Thinking, streaming, JSON, tool calling | [Model parameters][params]; [Chat API][chat] |

## 2. First call

Create a key in the [console](https://platform.kimi.com/console/api-keys) and set `MOONSHOT_API_KEY`, the environment variable used in the official quick start. [Quick start][start]

From the repository root:

```bash
python3 -m pip install -r requirements-lock.txt
python models/kimi/kimi-k2.6/examples/01_basic.py
```

This sends a real request and may incur charges. [01_basic.py](examples/01_basic.py) is the shared executable with response checks, not a new English variant. Endpoint, messages and response fields follow the [Chat API][chat]. Runtime and report details are in [verification](../../../en/docs/verification.md).

## 3. Thinking mode

K2.6 enables thinking by default. Use `thinking.type=enabled` or `disabled`; the Python SDK supplies unmodeled fields through `extra_body`. Returned thinking is `reasoning_content`. [Thinking models][thinking] · [Model parameters][params]

K2.6 does not support `reasoning_effort`. Temperature is fixed at `1.0` while thinking and `0.6` otherwise; top_p is `0.95` and n is `1`. Do not supply conflicting values. [Model parameters][params]

The checked example is [03_thinking.py](examples/03_thinking.py). Thinking tokens and final-answer tokens share `max_tokens`; too small a budget can leave reasoning but no final answer. The official multi-step-tool recommendation is `max_tokens >= 16000`. [Thinking budget][thinking] · [Parameter explanation](parameters.en.md)

## 4. Streaming

With `stream=True`, read text from `choices[0].delta.content` and thinking from `delta.reasoning_content`. [Streaming guide](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api) · [Thinking models][thinking]

Use [02_streaming.py](examples/02_streaming.py), including its termination checks; do not treat a disconnected stream as a complete answer.

## 5. JSON and structured output

JSON Mode uses `response_format={"type":"json_object"}`. Explicitly request JSON and the required fields in the prompt, then parse and validate the business result locally. [JSON Mode](https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api) · [04_json_output.py](examples/04_json_output.py)

For schema constraints, consult the documented [response_format support](https://platform.kimi.com/docs/guide/response_format); not every JSON Schema keyword is guaranteed. [10_json_schema.py](examples/10_json_schema.py) demonstrates the simple structure and local checks explained in [parameters](parameters.en.md).

## 6. Tool calling

Put the function name, description and argument schema in `tools`. The model returns tool_calls; the application executes a validated function and returns a `role="tool"` message with the matching tool_call_id. [Tool-calling guide][tools]

K2.6 does not support `tool_choice="required"`. Use automatic selection, no tools, or a documented named-function form. [Tool-choice restrictions](https://platform.kimi.com/docs/guide/use-tool-choice)

[05_tool_calling.py](examples/05_tool_calling.py) validates parameters, executes simulated weather, returns tool results and obtains a final answer, with a loop bound and full assistant history. [08_thinking_tools.py](examples/08_thinking_tools.py) demonstrates a thinking loop with a simulated order. Neither tool returns live business data.

## 7. Images, video and caching

The official visual formats include JPEG, PNG, GIF, WebP, BMP, HEIC and HEIF; video includes MP4, MPEG, MOV, AVI, FLV, MPG, WebM, WMV and 3GPP. Content must be an array, not a JSON-serialized string; SVG is not accepted as an image format. [Vision guide][vision]

The documented image field accepts a base64 data URL or `ms://<file_id>`, not a direct remote HTTP(S) image URL. [06_vision.py](examples/06_vision.py) encodes `IMAGE_PATH` and rejects `IMAGE_URL`; do not copy another provider's remote-image shape into Kimi. [Chat content][chat]

[09_video.py](examples/09_video.py) demonstrates local MP4 input. Read its input requirements and the [parameter reference](parameters.en.md) rather than assuming all transport/format combinations are implemented.

Context-cache TTLs include five minutes or one hour. Hit requirements, usage fields and pricing remain subject to the [official cache documentation](https://platform.kimi.com/docs/guide/context-caching).

## 8. Prices and errors

The Chinese manual's **2026-10-13** CNY-per-million-token snapshot is cached input ¥1.10, uncached input ¥6.50 and output ¥27.00. Prices change; reopen the [official price page](https://platform.kimi.com/docs/pricing/chat) before use.

Use exponential backoff for 429, bounded retries for 5xx, and correct a 400 request rather than retrying it blindly. Meanings are defined by the [official error codes](https://platform.kimi.com/docs/api/errors).

## 9. Fixed connection configuration and evidence

The shared configuration is provider kimi, exact model kimi-k2.6, Base URL `https://api.moonshot.cn/v1`, and key variable MOONSHOT_API_KEY. Explicit thinking-off Python configuration is `extra_body={"thinking":{"type":"disabled"}}`; it is not the model's default. [Quick start][start] · [K2.6][model] · [Thinking][thinking]

The [Legacy smoke report](verification/2026-10-13.json) retains its original scope. Read strict unified-verifier results in [historical status](../../../en/docs/verification-status.md), and original-file runs in [example status](../../../en/docs/example-status.md). The shared unified entry point is `python tests/verify_kimi_k2_6.py --report /tmp/kimi-k2.6-verification.json`; it sends real requests, and does not automatically execute every advanced file. Commands, environment and exit codes: [verification](../../../en/docs/verification.md).

## 10. Production checks

Always distinguish thinking from final text and validate completion before consuming JSON or tool output. Too-small thinking budgets can truncate the final answer. Additional checks and reusable patterns are in [production pitfalls](../../../en/docs/production-pitfalls.md) and the [full parameter reference](parameters.en.md).

[model]: https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart
[start]: https://platform.kimi.com/docs/get-api-key
[params]: https://platform.kimi.com/docs/api/models-overview
[chat]: https://platform.kimi.com/docs/api/chat
[thinking]: https://platform.kimi.com/docs/guide/use-thinking-models
[tools]: https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls
[vision]: https://platform.kimi.com/docs/guide/use-kimi-vision-model
