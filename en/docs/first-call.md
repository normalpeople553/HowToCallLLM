# 01 · Make your first call in five minutes

[中文](../../docs/01-5分钟跑通第一次调用.md) · [Human guide](../../human/README.en.md)

This chapter uses DeepSeek's officially documented OpenAI-compatible interface for a first text request. Model names, addresses, and parameters follow the [official documentation](https://api-docs.deepseek.com/).

## 1. Prepare Python

This repository requires Python 3.10 or later as its own runtime convention. Download Python from [python.org](https://www.python.org/downloads/). Create an isolated environment at the repository root and install the locked dependencies; the full procedure is in [verification and reproduction](verification.md).

```bash
python3 --version
python3 -m venv .venv
# macOS / Linux
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. [requirements-lock.txt](../../requirements-lock.txt) pins the SDK and dependencies; historical reports retain the environments originally recorded. For client usage, see the [official OpenAI Python SDK repository](https://github.com/openai/openai-python).

## 2. Create an API key

Create a key at [DeepSeek API Keys](https://platform.deepseek.com/api_keys). Balance rules, billing, and current prices are defined by the [official pricing page](https://api-docs.deepseek.com/quick_start/pricing/).

Project rule: never embed a key in code or commit it to Git. Examples read it from an environment variable. [Evidence and safety policy](evidence-policy.md)

The [basic file](../../examples/01_quickstart.py) reads the process environment directly; it does not automatically load `.env`. Saving a key in `.env` alone is not enough to run that file. Use the environment-variable method below, or follow [local live verification](verification.md#local-live-verification) to let the executor load an ignored `.env`. Do not print keys to check configuration.

```bash
# macOS / Linux
export DEEPSEEK_API_KEY="YOUR_KEY"
```

```powershell
# Windows PowerShell
$env:DEEPSEEK_API_KEY="YOUR_KEY"
```

## 3. Run the minimal example

The official endpoint is `https://api.deepseek.com`, and the recommended model entry in the source guide is `deepseek-flash`. [Official interface and model page](https://api-docs.deepseek.com/quick_start/pricing/)

Run the shared [examples/01_quickstart.py](../../examples/01_quickstart.py):

```bash
python3 examples/01_quickstart.py
```

The important fields are:

| Location | Purpose in the example |
|---|---|
| `OpenAI(api_key=...)` | Reads `DEEPSEEK_API_KEY` for authentication. |
| `OpenAI(base_url=...)` | Routes the SDK to `https://api.deepseek.com`. |
| `client.chat.completions.create(model=...)` | Selects `deepseek-flash`. |
| `messages` | Carries the conversation, including the user message. |
| `choices[0].message.content` | Contains the response text. |
| `usage` | Contains the returned token usage. |

The message, response, and usage structures are documented in the [DeepSeek Chat API](https://api-docs.deepseek.com/api/create-chat-completion/). Unlike a short illustrative `print(response.choices[0].message.content)` fragment, the executable file also checks empty content and `finish_reason`, so a truncated answer is not accepted as complete. The shared file's actual prompt is not changed by this translation.

If the request fails, retain the full status code and error text for private diagnosis, redact secrets before sharing, and follow [troubleshooting](troubleshooting.md). The project does not present an unverified cause as a confirmed explanation. [Evidence policy](evidence-policy.md)

Next: [02 · One compatible-API pattern, with model-specific rules](compatible-api.md).
