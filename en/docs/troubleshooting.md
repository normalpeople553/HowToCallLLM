# 05 · Troubleshooting and safety rules

[中文](../../docs/05-新手必会与报错速查.md) · [Human guide](../../human/README.en.md)

Interpret errors using the vendor's response and official documentation. This page gives the project's investigation order; it does not assume that the same HTTP status always has the same cause. [Evidence policy](evidence-policy.md)

## Start with four steps

1. For diagnosis, retain the complete status code, error type, request ID, and error text, but remove API keys and sensitive business content before sharing. This is a project troubleshooting rule. [Policy](evidence-policy.md)
2. Reproduce with [examples/01_quickstart.py](../../examples/01_quickstart.py) or a minimal call produced by the [generator](../../skills/model-manual/scripts/generate_snippet.py), to separate account/model issues from application-code issues.
3. Check `base_url`, the current model ID, activation, and account balance against the vendor's official interface, model, and pricing pages. Start with the configuration links in the [English repository entry](../../README.en.md).
4. Run [tests/verify_calls.py](../../tests/verify_calls.py) only after configuring real credentials and accepting possible charges. The script source defines its actual request scope.

## Common symptoms

| Symptom | Project investigation order | Official basis |
|---|---|---|
| `401` / authentication failure | Check whether the environment variable is set and whether the key belongs to the correct platform and region; never print its value. | [DeepSeek errors](https://api-docs.deepseek.com/quick_start/error_codes/) · [Kimi errors](https://platform.kimi.com/docs/api/errors) |
| `402` / insufficient balance | Check the vendor console, balance, and billing status against its official pricing page. | [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/) · [Kimi pricing](https://platform.kimi.com/docs/pricing/chat) |
| `404` / model not found | Copy the current exact Model ID from the official model page and check activation requirements. | [Kimi models](https://platform.kimi.com/docs/models) · [Doubao models](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [Doubao activation](https://docs.volcengine.com/docs/ark/activation-management?lang=zh) |
| `429` / rate limit | Read the limit information in the error body, reduce concurrency, and retry according to the service rules. | [DeepSeek errors](https://api-docs.deepseek.com/quick_start/error_codes/) · [Kimi errors](https://platform.kimi.com/docs/api/errors) |
| Context limit exceeded | Shorten the history or select a model whose officially documented context fits the task. | [Kimi models](https://platform.kimi.com/docs/models) · [Qwen models](https://help.aliyun.com/zh/model-studio/getting-started/models) |
| Empty streaming fragment | Use `delta.content or ""`; retain the full event for private diagnosis where appropriate. | [Kimi streaming](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api) |
| Empty answer with reasoning present | Inspect `reasoning_content`, the output limit, and that exact model's thinking behavior. | [DeepSeek thinking](https://api-docs.deepseek.com/guides/thinking_mode/) · [Zhipu thinking](https://docs.bigmodel.cn/cn/guide/capabilities/thinking) |

## API key safety

Project rule: read keys only from environment variables, a project `.env` excluded by [.gitignore](../../.gitignore), or the optional [call-llm skill's](call-llm-skill.md) `keyenv` in the user's home directory. Never retain complete keys in code, Issues, chat, screenshots, or logs. [Project policy](evidence-policy.md)

```bash
# Check presence only; never print the value.
test -n "$DEEPSEEK_API_KEY" && echo "set" || echo "not set"
```

If a key may have leaked, delete and recreate it in the relevant vendor's key-management page: [DeepSeek](https://platform.deepseek.com/api_keys), [Kimi](https://platform.moonshot.cn/console/api-keys), [Zhipu](https://bigmodel.cn/usercenter/apikeys), [Qwen](https://bailian.console.aliyun.com/?apiKey=1#/api-key), or [Doubao](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey).

Persisting a key in shell configuration makes it available to processes running as the same user. Whether that is acceptable depends on your security boundary. This project supports a Git-ignored project `.env`; for use across projects, the optional `keyenv` wrapper loads only the provider keys requested for a run. [Project policy](evidence-policy.md) · [Skill usage](call-llm-skill.md)
