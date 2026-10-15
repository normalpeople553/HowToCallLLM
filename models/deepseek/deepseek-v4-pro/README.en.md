# `deepseek-v4-pro` API guide

[中文](README.md) · [Model index](../../README.md) · [Parameter reference](parameters.en.md)

> Checked on **2026-10-15**. The current hosted API entry points are `deepseek-flash` and `deepseek-v4-pro`. The legacy names `deepseek-v4-flash` and `deepseek-v4-flash-vision-exp` route to Flash; they are not Pro aliases.

## Model identity

| Item | Value |
|---|---|
| API model ID | `deepseek-v4-pro` |
| Served version | `DeepSeek-V4-Pro-0813` |
| API base URL | `https://api.deepseek.com` |
| Key variable | `DEEPSEEK_API_KEY` |
| Context window | 1M tokens |
| Maximum output | 384K tokens |
| Account concurrency | 500 |
| Default reasoning | Enabled at `high` |
| Image input | Unsupported |

See the official [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) and [Rate Limit & Isolation](https://api-docs.deepseek.com/quick_start/rate_limit/) pages for the current model, pricing, context, vision, and concurrency data.

## Install and configure

```powershell
py -m pip install openai
$env:DEEPSEEK_API_KEY = "your-key"
```

```bash
python3 -m pip install openai
export DEEPSEEK_API_KEY="your-key"
```

Keep the key in an environment variable or a local `.env` file. Do not place it in source code, commits, screenshots, or posts.

## Minimal request

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=120,
)

response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": "Introduce yourself in one sentence."}],
)
print(response.choices[0].message.content)
```

Run the complete file on Windows:

```powershell
.venv\Scripts\python.exe models/deepseek/deepseek-v4-pro/examples/01_basic.py
```

Or on macOS/Linux:

```bash
python models/deepseek/deepseek-v4-pro/examples/01_basic.py
```

## Included examples

| File | Purpose |
|---|---|
| [`01_basic.py`](examples/01_basic.py) | Basic chat and completion checks |
| [`02_streaming.py`](examples/02_streaming.py) | Streaming text, reasoning, and usage |
| [`03_thinking.py`](examples/03_thinking.py) | Toggle reasoning and read `reasoning_content` |
| [`04_json_output.py`](examples/04_json_output.py) | JSON output plus application validation |
| [`05_tool_calling.py`](examples/05_tool_calling.py) | Non-reasoning tool loop |
| [`07_typescript.ts`](examples/07_typescript.ts) | TypeScript basic chat |
| [`08_curl.sh`](examples/08_curl.sh) | cURL basic chat |

See [`examples/sources.json`](examples/sources.json) for provenance and verification states. No `DEEPSEEK_API_KEY` is configured on this machine, so this update did not send live requests. The core Python examples use synthetic offline responses; that does not verify account access, quota, or live behavior.

## Capability notes

- Chat Completions, streaming, reasoning, JSON Object, and tool calls have official documentation and local examples.
- The official table also lists Responses API, the Anthropic-compatible API, prefix completion, FIM, and automatic context caching. This update does not duplicate examples for those features.
- Strict tool calls and chat prefix completion use Beta endpoints and should be verified separately before production use.
- Pro does not support image input. Do not copy Flash vision, image Files API, or Responses vision examples and only change the model name.
- Reasoning mode ignores `temperature`, `presence_penalty`, and `frequency_penalty`. Parse and validate structured output in the application.

See the [parameter reference](parameters.en.md) for field-level details and [production checks](../../../en/docs/production-pitfalls.md) for cross-provider failure handling.

## Official references

- [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/)
- [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)
- [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)
- [JSON Output](https://api-docs.deepseek.com/guides/json_mode/)
- [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)
- [Rate Limit & Isolation](https://api-docs.deepseek.com/quick_start/rate_limit/)
