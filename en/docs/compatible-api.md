# 02 · One compatible-API pattern, with model-specific rules

[中文](../../docs/02-一个套路调遍所有模型.md) · [Human guide](../../human/README.en.md)

Every collected vendor documents an OpenAI-compatible Chat Completions interface: [DeepSeek](https://api-docs.deepseek.com/), [Kimi](https://platform.kimi.com/docs/api/chat), [Zhipu](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction), [Qwen](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/), [Doubao](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh), and [MiniMax](https://platform.minimax.cn/docs/api-reference/text-openai-api). “Compatible” describes the chat interface used here, not compatibility with every OpenAI API. [Project boundaries](../../skills/model-manual/SKILL.en.md)

## The common pattern

The [OpenAI Python SDK example](https://github.com/openai/openai-python) supplies the common shape: create `OpenAI(api_key=..., base_url=...)`, then call `client.chat.completions.create(model=..., messages=...)` and read `response.choices[0].message.content`. The provider-specific values come from the official sources below, not from the SDK's defaults.

| Vendor | `base_url` | Model | Model-specific parameter source |
|---|---|---|---|
| DeepSeek | [`https://api.deepseek.com`](https://api-docs.deepseek.com/) | [`deepseek-flash`](https://api-docs.deepseek.com/quick_start/pricing/) | [Thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/) |
| Kimi | [`https://api.moonshot.cn/v1`](https://platform.kimi.com/docs/get-api-key) | [`kimi-k2.6`](https://platform.kimi.com/docs/models) | [Thinking mode](https://platform.kimi.com/docs/guide/use-thinking-models) |
| Zhipu | [`https://open.bigmodel.cn/api/paas/v4`](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) | [`glm-4.7`](https://docs.bigmodel.cn/cn/guide/start/pricing) | [Thinking mode](https://docs.bigmodel.cn/cn/guide/capabilities/thinking) |
| Qwen | [Official region and Workspace addresses](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) | [`qwen-flash`](https://help.aliyun.com/zh/model-studio/getting-started/models) | [`enable_thinking`](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) |
| Doubao | [`https://ark.cn-beijing.volces.com/api/v3`](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) | [Official model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh) | [Online inference](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) |
| MiniMax | [`https://api.minimax.cn/v1`](https://platform.minimax.cn/docs/api-reference/text-openai-api) | [`MiniMax-M2.7`—retirement announced](https://platform.minimax.cn/docs/guides/models-intro) | [`max_completion_tokens`; M2.x thinking cannot be disabled; `reasoning_split` changes format only](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |

Qwen currently recommends regional addresses containing `WorkspaceId`; the legacy compatible domain remains supported and is retained by the project for existing examples. [Official migration guidance](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

For executable code that reads exact model-card settings rather than copying a generic configuration, see [examples/02_one_for_all.py](../../examples/02_one_for_all.py).

## Conversation, streaming, and thinking

For multi-turn conversation, send the required historical `messages` again with the next request. Role definitions such as `system`, `user`, and `assistant` are specified in each vendor's chat API, for example [Kimi Chat](https://platform.kimi.com/docs/api/chat). The complete shared example is [examples/04_multi_turn.py](../../examples/04_multi_turn.py).

`stream=True` enables streaming. Read chunks rather than a single final message; check `choices` before accessing `choices[0]`, and collect `delta.content` while separately tracking termination and usage. Kimi documents the data-event format in its [streaming guide](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api). Use the executable [examples/03_streaming.py](../../examples/03_streaming.py), not a text-printing fragment alone, to check completion. [Production pitfalls](production-pitfalls.md)

Thinking controls are not uniform. DeepSeek and Kimi use `thinking.type`: [DeepSeek](https://api-docs.deepseek.com/guides/thinking_mode/) · [Kimi](https://platform.kimi.com/docs/guide/use-thinking-models/). Qwen's Python SDK examples use `extra_body={"enable_thinking": False}`. [Qwen](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

```python
# DeepSeek / Kimi; check the exact model for Zhipu and Doubao.
extra_body={"thinking": {"type": "disabled"}}

# Qwen
extra_body={"enable_thinking": False}
```

GLM-4.7 and Doubao behavior must be checked separately in [Zhipu thinking mode](https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode) and [Ark deep thinking](https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh). Zhipu's historical verification on 2026-10-13 was rate-limited; consult [verification status](verification-status.md) for the recorded results. Do not transfer GLM-4.7's disabling configuration to GLM-5.3. [GLM-5.3 documentation](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash)

The disabling examples above do **not** apply to MiniMax M2.7. It accepts `thinking.type=disabled` without disabling thinking; `reasoning_split=true` only separates reasoning from the answer. The generator rejects `--thinking off` for this model. The native `/text/chatcompletion_v2` endpoint is also not the OpenAI SDK Base URL. See the [M2.7 manual](../../models/minimax/MiniMax-M2.7/README.en.md) and [official behavior](https://platform.minimax.cn/docs/api-reference/text-chat-openai).

To generate a model-specific call, use [generate_snippet.py](../../skills/model-manual/scripts/generate_snippet.py). It reads the vendor directory and [model cards](../../skills/model-manual/references/models/) and checks vendor/model identity, capabilities, thinking settings, and output budgets. Instructions are in the [English repository entry](../../README.en.md). Full streaming examples track termination and usage; printing received text alone does not prove success. [Production pitfalls](production-pitfalls.md)
