# `qwen-flash` API manual

[中文](README.md) · [Human guide](../../../human/README.en.md) · [Parameter reference](parameters.en.md)

English translation of the [Chinese manual](README.md), source-checked there on **2026-10-13**. Calling code and official source manifests are shared; original official URLs are retained, including Chinese pages. Translation does not rerun API verification. Machine facts: [`qwen-flash.json`](../../../skills/model-manual/references/models/qwen-flash.json).

Find files and attribution in [sources.json](examples/sources.json) or the [example index](../../../en/docs/example-index.md). Keep [historical unified tests](../../../en/docs/verification-status.md) separate from [per-file execution](../../../en/docs/example-status.md). Evidence covers only recorded source, parameters, input and environment; fragments, modified requests and generated combinations do not inherit passes. [Evidence policy](../../../en/docs/evidence-policy.md)

## 1. At a glance

| Item | Recorded value | Official source |
|---|---|---|
| Model ID | `qwen-flash` | [Model list][models] |
| Alias version | `qwen-flash-2025-07-28` | [Model pricing][pricing] |
| Context | 1M tokens | [Model list][models] |
| Interface | OpenAI-compatible Chat Completions | [API][api] |
| Input | Text | [Model list][models] |

This is the older exact Qwen Flash model, not a newer-generation Flash. Its detailed limits and unsupported/not-confirmed combinations are in [parameters](parameters.en.md).

## 2. Endpoint and first call

The official recommendation is a Workspace-specific endpoint, `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`. The older `https://dashscope.aliyuncs.com/compatible-mode/v1` remains documented; production projects should prefer the address supplied by their console. [API][api]

Key creation and `DASHSCOPE_API_KEY` follow the [first-call guide](https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen). Endpoint execution records stay local and are not published.

Run the shared [01_basic.py](examples/01_basic.py), rather than a new English variant. From the repository root, after setting DASHSCOPE_API_KEY:

```bash
python -m pip install -r requirements-lock.txt
python models/qwen/qwen-flash/examples/01_basic.py
```

This sends a real request and may incur charges. Runtime and evidence details: [verification](../../../en/docs/verification.md).

## 3. Thinking and streaming

Python uses `extra_body={"enable_thinking": True/False}`. Raw HTTP and the documented Node.js form put enable_thinking at the JSON top level. Reasoning is returned as reasoning_content. [API][api]

stream true returns delta.content. Use [02_streaming.py](examples/02_streaming.py) for termination checks and [03_thinking.py](examples/03_thinking.py) for separately checked reasoning and final output. [API][api]

## 4. JSON and tools

JSON Object mode uses `response_format={"type":"json_object"}` and requires an explicit JSON instruction. Model/mode support and schema forms are documented under [structured output][json]. Shared executable: [04_json_output.py](examples/04_json_output.py).

Qwen Flash supports function calling: tools describes the function, the model proposes arguments, and the application executes and returns results. Qwen does not support tool_choice required as a reliable forced-call contract; use automatic selection or documented named-function forms within the model/mode restrictions. [Function calling][tools]

[05_tool_calling.py](examples/05_tool_calling.py) batch-validates calls, executes simulated weather, returns matching tool_call_id results and obtains a final answer. [07_thinking_tools.py](examples/07_thinking_tools.py) covers thinking with simulated inventory. Neither fixture is live weather or stock data; completion requires an actual local tool execution.

## 5. Dated pricing snapshot

The Chinese manual recorded the following global-deployment CNY prices on **2026-10-13**, per million tokens:

| Input length tier | Input | Output |
|---|---:|---:|
| Up to 128K | ¥0.15 | ¥1.50 |
| 128K–256K | ¥0.60 | ¥6.00 |
| 256K–1M | ¥1.20 | ¥12.00 |

Region, deployment and tier affect pricing. This translation is not a fresh quote: reopen [official pricing][pricing].

## 6. Configuration and evidence

The shared example configuration is provider qwen, exact model qwen-flash, key variable DASHSCOPE_API_KEY, the older Beijing compatible Base URL above and text input. Explicit thinking-off Python configuration is `extra_body={"enable_thinking":False}`. [Model list][models] · [API][api]

Calling code and official attribution are in [sources.json](examples/sources.json). Execution records stay local; see [reproduction](../../../en/docs/verification.md) for setup and checks.

## 7. Budget pitfalls

BaiLian's max_tokens meaning varies by model. max_completion_tokens is defined as reasoning plus answer, but its Flash support starts at Qwen3.5-Flash; do not automatically substitute it for the older qwen-flash. For this older model, max_tokens limits the answer body only. Python extension fields such as enable_thinking belong in extra_body. [API][api]

See [parameters](parameters.en.md) for exact budgets/defaults and [production pitfalls](../../../en/docs/production-pitfalls.md) for validation. A common compatible field name does not establish support for images, preserved thinking or strict schemas on this exact model.

[models]: https://help.aliyun.com/zh/model-studio/getting-started/models
[pricing]: https://help.aliyun.com/zh/model-studio/model-pricing
[api]: https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/
[json]: https://help.aliyun.com/zh/model-studio/qwen-structured-output
[tools]: https://help.aliyun.com/zh/model-studio/qwen-function-calling
