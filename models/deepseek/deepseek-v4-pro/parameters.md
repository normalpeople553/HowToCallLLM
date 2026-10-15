# `deepseek-v4-pro` 参数说明

[返回说明书](README.md) · [English](parameters.en.md)

下表针对仓库中的 OpenAI 兼容 Chat Completions 示例。字段上限以官方 [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) 为准。

| 字段 | 类型 | 作用与注意点 | 对应示例 |
|---|---|---|---|
| `model` | string | 固定为 `deepseek-v4-pro` | 全部 |
| `messages` | array | 按顺序传入 system、user、assistant、tool 消息 | `01_basic.py`、`05_tool_calling.py` |
| `stream` | boolean | `true` 返回 SSE；空 `choices` 块可能只含用量 | `02_streaming.py` |
| `stream_options.include_usage` | boolean | 请求流末尾的用量块 | `02_streaming.py` |
| `max_tokens` | integer | 1–393216；输入与输出仍受 1M 上下文约束 | 按需添加 |
| `thinking.type` | object | `enabled` 或 `disabled`；Python SDK 放在 `extra_body` | `03_thinking.py`、`05_tool_calling.py` |
| `reasoning_effort` | string | `none`、`low`、`high`、`max` | `03_thinking.py` |
| `response_format` | object | `{"type":"json_object"}`；提示词也要明确要求 JSON | `04_json_output.py` |
| `tools` | array | 声明函数名、说明和 JSON Schema；函数由应用执行 | `05_tool_calling.py` |
| `tool_choice` | string/object | 可控制工具选择；思考模式对部分选择方式有限制 | `05_tool_calling.py` |
| `stop` | string/array | 命中停止文本时结束生成 | 按需添加 |
| `user_id` | string | 业务侧用户标识，Python SDK 可通过 `extra_body` 传入 | 按需添加 |

## 响应读取

- 普通正文：`response.choices[0].message.content`
- 思考内容：`response.choices[0].message.reasoning_content`
- 工具请求：`response.choices[0].message.tool_calls`
- 结束原因：`response.choices[0].finish_reason`
- 用量：`response.usage`
- 流式正文：`chunk.choices[0].delta.content`
- 流式思考：`chunk.choices[0].delta.reasoning_content`

应用至少应检查 `choices` 非空、`finish_reason` 符合当前阶段，并确认正文或工具调用确实存在。`length` 表示输出或上下文预算不足，不能把截断结果当完整回答。

## 思考模式

Pro 默认开启思考，默认强度为 `high`。关闭方式：

```python
extra_body={"thinking": {"type": "disabled"}}
```

开启并指定强度：

```python
reasoning_effort="high",
extra_body={"thinking": {"type": "enabled"}},
```

思考模式下，`temperature`、`presence_penalty` 和 `frequency_penalty` 会被忽略。最终答案与思考内容是不同字段；不要只看到 `reasoning_content` 就认为请求已完成。

## JSON 输出

```python
response_format={"type": "json_object"}
```

同时在提示词中写明“只输出 JSON”。收到正文后仍需 `json.loads`，再检查对象类型、必填字段、字段类型和业务取值。示例见 [`04_json_output.py`](examples/04_json_output.py)。

## 工具调用

模型只返回工具名和参数。应用需要：

1. 校验工具名、调用 ID、JSON 参数和业务约束。
2. 执行允许的本地函数或服务。
3. 把完整 assistant 消息和每个 tool 结果写回 `messages`。
4. 设置轮次与调用次数上限，继续请求最终正文。

示例 [`05_tool_calling.py`](examples/05_tool_calling.py) 使用固定模拟天气，不代表实时数据。

## Pro 特有限制

官方价格与模型表把 Pro 的 Vision 标为不支持。因此本目录没有 `06_vision.py`，也不要给 `messages[].content` 加 `image_url` 后期待 Pro 处理图片。需要图片输入时使用 `deepseek-flash`，并重新核对其说明书和成本。

本页是字段解释，不构成线上实测。每个文件的来源和状态见 [`examples/sources.json`](examples/sources.json)。
