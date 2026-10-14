# Real-world pitfalls and production checks

[中文](../../docs/06-真实踩雷与生产检查.md) · [Human guide](../../human/README.en.md)

> Source verification date: **2026-10-13**. This page includes only issues supported by official vendor documentation or redacted repository reports. Cross-provider claims state their scope; “OpenAI-compatible” does not mean identical parameter semantics. Translating the page does not renew its verification date. [Evidence policy](evidence-policy.md)

## 1. Thinking can consume the answer's output budget

### Symptoms

- A long `reasoning_content` is followed by a very short, empty, or unfinished `content`.
- HTTP status is still 200, so code that checks only request success passes an incomplete result downstream.
- `finish_reason` is `length`, not the normal `stop`.

### The cause differs by provider

Kimi explicitly limits the combined token count of `reasoning_content` and final `content` with `max_tokens`. For multi-step tool calls with K2.6/K2.7 Code, its guide recommends `max_tokens >= 16000` to avoid incomplete thinking or answers. [Kimi thinking models](https://platform.kimi.com/docs/guide/use-thinking-models)

Alibaba Cloud Model Studio offers both `max_tokens` and `max_completion_tokens`. The latter limits the complete output—thinking plus answer—while the former's meaning varies: some models use it for both, others for the answer alone. A shared wrapper must not assume universal `max_tokens` semantics. [Model Studio Chat Completions parameters](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

For the collected **old `qwen-flash`**, the current documentation puts it in the answer-only `max_tokens` category. Flash support for `max_completion_tokens` starts with Qwen3.5-Flash; do not substitute that parameter into old `qwen-flash`. The generator uses only the exact model card's registered parameter. [Official parameter scope](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) · [Shared model card](../../skills/model-manual/references/models/qwen-flash.json)

DeepSeek exposes reasoning tokens as `usage.completion_tokens_details.reasoning_tokens` and uses `finish_reason="length"` when a generation limit is reached. Monitor both. [DeepSeek Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)

MiniMax M2.7—additional source check dated 2026-10-14—cannot disable thinking. `reasoning_split` only changes where reasoning appears in the output; requesting `disabled` does not stop it. Its official SDK guidance explicitly includes thinking in legacy `max_tokens`, but the current M2.7 field description for `max_completion_tokens` does not explicitly establish the same accounting. This project leaves that point unconfirmed rather than inferring it from another model. [MiniMax Chat parameters](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [SDK thinking and parameters](https://platform.minimax.cn/docs/api-reference/text-openai-api)

### What to change

Project recommendation: always check `finish_reason`, nonempty final content, and usage. Do not reuse a tiny non-thinking allowance such as 128/256 tokens for a thinking task. Read the correct budget name and semantics from the exact model manual, not from a vendor-wide or SDK-wide assumption. [Evidence policy](evidence-policy.md)

```python
choice = response.choices[0]
content = choice.message.content or ""

if choice.finish_reason == "length":
    raise RuntimeError("Generation limit reached; the answer may be truncated")
if not content.strip():
    raise RuntimeError("Empty answer; check whether thinking consumed the budget")

usage = response.usage
details = getattr(usage, "completion_tokens_details", None)
reasoning_tokens = getattr(details, "reasoning_tokens", None)
print({
    "completion_tokens": getattr(usage, "completion_tokens", None),
    "reasoning_tokens": reasoning_tokens,
    "finish_reason": choice.finish_reason,
})
```

This is an explanatory fragment, not an independently verified executable example. Retrying is not the only fix: the same insufficient budget can repeatedly produce truncation. First check the budget parameter and value; reduce reasoning effort or disable thinking only where the exact model supports it, then use bounded retries. [Project policy](evidence-policy.md)

## 2. HTTP 200 is not a completion check

DeepSeek documents `stop`, `length`, `content_filter`, `tool_calls`, `insufficient_system_resource`, and `aborted`. `stop` means a natural stop or a matched stop sequence; `tool_calls` means the model requested a tool. [DeepSeek Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)

MiniMax's native interface also returns a business status in `base_resp.status_code`. Project examples check that status, termination, and a nonempty final answer. HTTP success alone is insufficient, and text containing only `<think>` is not a final answer. [Native response fields](https://platform.minimax.cn/docs/api-reference/text-post) · [M2.7 example catalog](../../models/minimax/MiniMax-M2.7/examples/sources.json)

Project recommendation: branch on termination before parsing JSON, writing a database, executing code, or displaying a final answer. [Policy](evidence-policy.md)

```python
reason = response.choices[0].finish_reason
if reason == "tool_calls":
    handle_tool_calls(response.choices[0].message.tool_calls)
elif reason == "length":
    raise RuntimeError("Truncated result; do not treat it as a complete answer")
elif reason != "stop":
    raise RuntimeError(f"Model did not finish normally: {reason}")
```

## 3. JSON Mode does not guarantee correct business data

DeepSeek requires an explicit JSON instruction in the prompt when using `response_format={"type":"json_object"}`. Otherwise the model may continue producing whitespace until the token budget is exhausted, making the request appear stuck. JSON Mode can still produce truncated content when `finish_reason="length"`. [Chat API](https://api-docs.deepseek.com/api/create-chat-completion/) · [JSON Output](https://api-docs.deepseek.com/guides/json_mode/)

Model Studio also requires an explicit JSON instruction for `json_object`. Its `json_schema` and `json_object` modes have different model-support lists. [Chat parameters](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) · [Structured output](https://help.aliyun.com/zh/model-studio/qwen-structured-output)

Project recommendation: use three layers—completion check → `json.loads` → Schema/business validation. Valid JSON can still contain invalid enum values, missing business relationships, or fabricated values. [Policy](evidence-policy.md)

## 4. JSON tool arguments are not permission to execute

DeepSeek warns that generated tool arguments may not be valid JSON and may include parameters absent from the function Schema. Validate them before calling a real function. [Chat API](https://api-docs.deepseek.com/api/create-chat-completion/)

Project recommendation: allowlist tool names; parse arguments, then validate their Schema and business permissions. Add idempotency keys and human confirmation to write operations, and bound the tool loop. These are project safeguards, not vendor guarantees of model correctness. [Policy](evidence-policy.md)

```python
allowed_tools = {"get_weather": get_weather}
call = message.tool_calls[0]

if call.function.name not in allowed_tools:
    raise PermissionError("Model requested an unauthorized tool")

arguments = json.loads(call.function.arguments)
validate_weather_arguments(arguments)  # Types, enums, lengths, and permissions.
result = allowed_tools[call.function.name](**arguments)
```

## 5. Dropping thinking fields can break the next tool turn

Kimi requires all `reasoning_content` to be retained and returned within a multi-step K2.6/K2.7 Code tool call. With K2.6 `thinking.keep="all"`, also preserve complete historical assistant messages. [Kimi thinking models](https://platform.kimi.com/docs/guide/use-thinking-models)

DeepSeek requires complete preceding `reasoning_content` in thinking mode with `tools`; missing it causes HTTP 400. [DeepSeek Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)

Do not rebuild history as only `{"role":"assistant","content": message.content}`. The project recommends retaining the complete SDK assistant message, then appending tool results. Before persisting reasoning—which may contain sensitive information—apply your business data policy. [Project policy](evidence-policy.md)

## 6. Not every streaming chunk contains answer text

DeepSeek puts streaming usage in the last chunk before termination; that chunk contains no new answer text and has a nonempty `finish_reason`. With thinking enabled, `delta.reasoning_content` arrives before `delta.content`. [Chat API](https://api-docs.deepseek.com/api/create-chat-completion/) · [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)

Kimi likewise describes reasoning before the answer. Some OpenAI SDK types do not statically declare this extension field; use `getattr`/`hasattr` where needed. [Kimi thinking models](https://platform.kimi.com/docs/guide/use-thinking-models)

Project recommendation: do not concatenate `chunk.choices[0].delta.content` blindly. Check `choices`, then independently collect reasoning, answer content, termination, and usage. [Policy](evidence-policy.md)

```python
reasoning_parts = []
content_parts = []
finish_reason = None
final_usage = None

for chunk in stream:
    if getattr(chunk, "usage", None):
        final_usage = chunk.usage
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta
    reasoning_parts.append(getattr(delta, "reasoning_content", None) or "")
    content_parts.append(delta.content or "")
    if chunk.choices[0].finish_reason:
        finish_reason = chunk.choices[0].finish_reason

if finish_reason != "stop":
    raise RuntimeError(f"Incomplete streaming result: {finish_reason}")
if not "".join(content_parts).strip():
    raise RuntimeError("Empty streaming answer")
```

The complete executable protection code is in the shared [streaming example](../../models/kimi/kimi-k2.6/examples/02_streaming.py). Offline tests use simulated truncation, empty usage chunks, and tool responses to exercise code paths; live reports separately record real requests. [Verification and reproduction](verification.md)

## 7. An incorrectly placed `extra_body` can leave a parameter ineffective

Model Studio documents `extra_body` for nonstandard fields such as `enable_thinking` and `thinking_budget` when using the OpenAI Python SDK. In direct HTTP requests, those fields belong at the top level of the JSON body. [Chat parameters](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

Kimi and DeepSeek thinking switches are vendor extensions too; the project's Python examples pass them through `extra_body`. [Kimi](https://platform.kimi.com/docs/guide/use-thinking-models) · [DeepSeek](https://api-docs.deepseek.com/guides/thinking_mode/)

Project recommendation: a request accepted without error does not prove that a parameter took effect. Inspect reasoning and separately test supported on/off paths. [Kimi thinking example](../../models/kimi/kimi-k2.6/examples/03_thinking.py) · [DeepSeek thinking example](../../models/deepseek/deepseek-flash/examples/03_thinking.py)

## 8. HTTP 429 does not mean the key is wrong or the model is permanently unavailable

Zhipu error code `1302` means account rate restriction; `1305` means high current model traffic. HTTP 429 alone cannot distinguish them or establish authentication failure or unsupported capability. [Official error codes](https://docs.bigmodel.cn/cn/api/api-code)

Project recommendation: classify by both HTTP and business code. Apply capped exponential backoff with jitter for 429, inspect credentials/permissions for 401/403, and fix the request body for 400. Do not retry every error indiscriminately. [Policy](evidence-policy.md)

## 9. Still callable does not mean a good permanent dependency for a new project

Ark lists `doubao-seed-2-1-pro-260628` among past models. Recheck current lifecycle and availability before choosing a long-term dependency; a past successful call would not guarantee future access. [Ark model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh)

Project recommendation: make Model IDs configurable, and check both official lifecycle notices and real liveness before release. One successful call does not remove migration risk; the word “past” alone does not prove the endpoint is already offline. [Policy](evidence-policy.md)

## 10. Thinking history consumes context and can increase cost

Kimi states that `reasoning_content` counts toward token consumption. Preserved thinking continues to occupy context and incur charges in subsequent history. [Kimi thinking models](https://platform.kimi.com/docs/guide/use-thinking-models)

Project recommendation: retain thinking only when a multi-turn task genuinely needs continued reasoning. For ordinary chat, retrieval Q&A, and simple extraction, prefer disabling it where supported or not preserving historical reasoning. Use actual response usage for cost calculations, and recheck [official pricing](pricing.md) before use.

## Minimum pre-production checklist

These are project recommendations based on the documented behavior above, not vendor promises. [Policy](evidence-policy.md)

- Read keys from environment variables; never log complete keys.
- Pin and record the Model ID, Base URL, SDK version, and verification date.
- Separately test ordinary requests, streaming, supported thinking on/off paths, JSON, and tools; test images for multimodal models.
- Check `finish_reason`; reject `length` as a complete result.
- Record input, output, and reasoning tokens; alert on unusual growth.
- Parse and validate JSON; check tool allowlists, permissions, and idempotency.
- Set bounded retries for 429, 5xx, and timeouts; never blindly replay writes.
- Keep official pricing/model links rather than treating copied prices as a permanent truth source.
