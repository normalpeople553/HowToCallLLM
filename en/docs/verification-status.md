# Workflow record publication policy

[中文](../../docs/验证状态.md) | English

> Generated from public model cards and official references by `python skills/model-manual/scripts/sync_verification.py`. This command does not read local execution records, credentials or vendor APIs.

Execution records are local-only and are not published. This public page does not show results, statistics, runtime environments, fingerprints, record identifiers or report links. [Evidence policy](evidence-policy.md)

The vendor capability summary is derived solely from the exact model's official references as documented or unknown. Private execution results do not promote a public capability to verified.

| Model manual | Unified workflow record | Official references |
|---|---|---|
| [deepseek-flash](../../models/deepseek/deepseek-flash/README.en.md) | Local records are not published | [Official 1](https://api-docs.deepseek.com/api/create-chat-completion/) · [Official 2](https://api-docs.deepseek.com/guides/json_mode/) · [Official 3](https://api-docs.deepseek.com/guides/kv_cache/) · [Official 4](https://api-docs.deepseek.com/guides/responses_api/) · [Official 5](https://api-docs.deepseek.com/guides/thinking_mode/) · [Official 6](https://api-docs.deepseek.com/guides/tool_calls/) · [Official 7](https://api-docs.deepseek.com/guides/vision/) · [Official 8](https://api-docs.deepseek.com/quick_start/pricing/) |
| [kimi-k2.6](../../models/kimi/kimi-k2.6/README.en.md) | Local records are not published | [Official 1](https://platform.kimi.com/docs/api/chat) · [Official 2](https://platform.kimi.com/docs/guide/context-caching) · [Official 3](https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api) · [Official 4](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls) · [Official 5](https://platform.kimi.com/docs/guide/use-kimi-vision-model) · [Official 6](https://platform.kimi.com/docs/guide/use-thinking-models) · [Official 7](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api) |
| [glm-4.7](../../models/zhipu/glm-4.7/README.en.md) | Unified workflow not run | [Official 1](https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode) · [Official 2](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) |
| [qwen-flash](../../models/qwen/qwen-flash/README.en.md) | Local records are not published | [Official 1](https://help.aliyun.com/zh/model-studio/getting-started/models) · [Official 2](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) · [Official 3](https://help.aliyun.com/zh/model-studio/qwen-function-calling) · [Official 4](https://help.aliyun.com/zh/model-studio/qwen-structured-output) |
| [doubao-seed-2-1-pro-260628](../../models/doubao/doubao-seed-2-1-pro-260628/README.en.md) | Local records are not published | [Official 1](https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh) · [Official 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [Official 3](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) |
| [MiniMax-M2.7](../../models/minimax/MiniMax-M2.7/README.en.md) | Unified workflow not run | [Official 1](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [Official 2](https://platform.minimax.cn/docs/api-reference/text-openai-api) · [Official 3](https://platform.minimax.cn/docs/api-reference/text-post) |

## Interpretation

- private: execution records are not public. This does not assert success, failure or capability quality, and the public clone does not need those local files.
- not_run: no unified workflow run is registered for this model. This does not establish unsupported capabilities or describe every example's execution history.
- documented / unknown: these are official-document classifications only, not published execution results.

[Unified workflow source](../../tests/provider_verify.py) · [Per-file runner source](../../tests/run_example_files.py) · [Maintained manuals](../../models/README.en.md)

To perform your own local checks, see [verification](verification.md). The public generation/check commands remain reproducible without private records.
