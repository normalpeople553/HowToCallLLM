# `deepseek-v4-pro` parameter reference

[Back to the guide](README.en.md) · [中文](parameters.md)

This page covers the OpenAI-compatible Chat Completions examples in this repository. Use the official [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) as the source of truth for current field limits.

| Field | Type | Purpose and constraints | Example |
|---|---|---|---|
| `model` | string | Always `deepseek-v4-pro` | All |
| `messages` | array | Ordered system, user, assistant, and tool messages | `01_basic.py`, `05_tool_calling.py` |
| `stream` | boolean | `true` returns SSE; a usage-only block may have empty `choices` | `02_streaming.py` |
| `stream_options.include_usage` | boolean | Requests a usage block at the end of the stream | `02_streaming.py` |
| `max_tokens` | integer | 1–393216; input plus output remains constrained by the 1M context | Add when needed |
| `thinking.type` | object | `enabled` or `disabled`; pass through `extra_body` in the Python SDK | `03_thinking.py`, `05_tool_calling.py` |
| `reasoning_effort` | string | `none`, `low`, `high`, or `max` | `03_thinking.py` |
| `response_format` | object | `{"type":"json_object"}`; the prompt must also request JSON | `04_json_output.py` |
| `tools` | array | Function name, description, and JSON Schema; the application executes it | `05_tool_calling.py` |
| `tool_choice` | string/object | Controls tool selection; some modes are restricted during reasoning | `05_tool_calling.py` |
| `stop` | string/array | Stops generation when matching text is reached | Add when needed |
| `user_id` | string | Application user identifier; pass through `extra_body` in Python | Add when needed |

## Reading responses

- Final text: `response.choices[0].message.content`
- Reasoning: `response.choices[0].message.reasoning_content`
- Tool requests: `response.choices[0].message.tool_calls`
- Finish reason: `response.choices[0].finish_reason`
- Usage: `response.usage`
- Streaming text: `chunk.choices[0].delta.content`
- Streaming reasoning: `chunk.choices[0].delta.reasoning_content`

At minimum, check that `choices` is not empty, the finish reason matches the current stage, and the expected text or tool calls exist. A `length` finish reason means the output or context budget was exhausted; the result is incomplete.

## Reasoning mode

Pro enables reasoning by default at `high`. Disable it with:

```python
extra_body={"thinking": {"type": "disabled"}}
```

Enable it with an explicit effort:

```python
reasoning_effort="high",
extra_body={"thinking": {"type": "enabled"}},
```

Reasoning mode ignores `temperature`, `presence_penalty`, and `frequency_penalty`. Final text and reasoning use separate fields. The presence of `reasoning_content` alone does not mean the request completed.

## JSON output

```python
response_format={"type": "json_object"}
```

Also tell the model to return JSON only. Parse the returned text with `json.loads`, then validate the object type, required fields, field types, and business constraints. See [`04_json_output.py`](examples/04_json_output.py).

## Tool calls

The model only returns a tool name and arguments. The application must:

1. Validate the tool name, call ID, JSON arguments, and business rules.
2. Run an allowed local function or service.
3. Append the complete assistant message and each tool result to `messages`.
4. Enforce turn and call limits, then request the final answer.

[`05_tool_calling.py`](examples/05_tool_calling.py) uses fixed simulated weather and does not provide live data.

## Pro-specific limitation

The official model table marks Vision as unsupported for Pro. This directory therefore has no `06_vision.py`. Do not add an `image_url` to `messages[].content` and expect Pro to process it. Use `deepseek-flash` for image input and review its guide and pricing separately.

This reference explains fields; it is not a live verification record. See [`examples/sources.json`](examples/sources.json) for file-level provenance and status.
