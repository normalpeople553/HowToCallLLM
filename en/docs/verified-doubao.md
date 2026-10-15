# Doubao: verified minimal calls

[中文](../../docs/豆包已验证调用.md) · [Full Doubao model list](model-lists/doubao.md) · [Executed source file](../../models/doubao/verified_calls.py)

This page lists only exact Model IDs for which the maintainer ran the [same repository file](../../models/doubao/verified_calls.py) against the real API and received a complete, nonempty answer. Keys, replies, timestamps, and raw reports are not published. A different account, prompt, or parameter combination does not inherit this result. Check the [official model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh) for current availability; this page is not a service guarantee.

## Choose an exact model

| Purpose and lifecycle | Verified exact Model IDs | Tested endpoint |
|---|---|---|
| Current rolling model; underlying version changes automatically | `doubao-seed-evolving` | Minimal text through Chat Completions |
| Current recommended pinned versions | `doubao-seed-2-1-pro-260915` · `doubao-seed-2-1-lite-260915` · `doubao-seed-2-1-turbo-260628` | Minimal text through Chat Completions |
| Past versions still listed by the provider | `doubao-seed-2-1-pro-260628` · `doubao-seed-2-0-lite-260428` · `doubao-seed-2-0-mini-260428` · `doubao-seed-character-260628` · `doubao-seed-character-251128` | Minimal text through Chat Completions |
| Translation-specialized model | `doubao-seed-translation-250915` | Responses API with structured input and `translation_options` |
| Scheduled for retirement; maintain existing integrations only | `doubao-seed-2-0-lite-260215` · `doubao-seed-2-0-code-preview-260215` | Minimal text through Chat Completions |

Lifecycle labels come from the [official model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh) and [deprecation notice](https://docs.volcengine.com/docs/ark/model-deprecation-notice?lang=zh). The published EOS for `doubao-seed-2-0-lite-260215` is 2026-10-22 14:00 UTC+8; for `doubao-seed-2-0-code-preview-260215` it is 2026-11-24 14:00 UTC+8. A successful call now does not establish availability after EOS. [Deprecation notice](https://docs.volcengine.com/docs/ark/model-deprecation-notice?lang=zh)

`doubao-seed-evolving` requires manual activation in the Ark console; it is excluded from automatic activation of newly added models. [Activation management](https://docs.volcengine.com/docs/ark/activation-management?lang=zh)

## Run it

Set `ARK_API_KEY` as described in the [official API Key guide](https://docs.volcengine.com/docs/ark/api-key?lang=zh), install the `openai` Python package, and run from the repository root:

```bash
python models/doubao/verified_calls.py --model doubao-seed-2-1-pro-260915
python models/doubao/verified_calls.py --model doubao-seed-translation-250915
```

Replace `--model` with any exact ID in the table. The file rejects unlisted IDs. [Source](../../models/doubao/verified_calls.py). The `model` field and endpoints are documented in the [Chat API](https://docs.volcengine.com/docs/ark/chat-api?lang=zh) and [Responses API](https://docs.volcengine.com/docs/ark/create-model-responses-api?lang=zh).

## Parameters actually sent

| Field | Meaning in this file | Source |
|---|---|---|
| `model` | An exact ID, not a family name; no automatic fallback | [Model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [Source](../../models/doubao/verified_calls.py) |
| `messages` | One user text message for ordinary Chat models | [Chat API](https://docs.volcengine.com/docs/ark/chat-api?lang=zh) · [Source](../../models/doubao/verified_calls.py) |
| `thinking.type="disabled"` | Disables thinking for supported Chat models; it does not control temperature or context length. The non-thinking `character-251128` omits it | [Thinking](https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh) · [Model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh) |
| `input[].content[].translation_options` | In Responses API, translates from `zh` to `en`. Do not send this translation model through Chat Completions | [Responses API](https://docs.volcengine.com/docs/ark/create-model-responses-api?lang=zh) · [Source](../../models/doubao/verified_calls.py) |
| `timeout=120`, `max_retries=0` | Client-side wait and retry settings, not context, output-budget, or sampling controls | [Source](../../models/doubao/verified_calls.py) · [OpenAI Python SDK](https://github.com/openai/openai-python#timeouts) |

This file does **not** set `temperature`, `top_p`, `max_tokens`, or `max_completion_tokens`; those parameters are not verified per model by this file. [Source](../../models/doubao/verified_calls.py) · [Chat API parameters](https://docs.volcengine.com/docs/ark/chat-api?lang=zh)

## Verification boundary

“Verified” here means that this exact minimal text/translation file completed and checked the response status and nonempty final answer. It does not establish answer quality, all capabilities, throughput, or production reliability. Exploratory calls for images, audio understanding, video, streaming, tools, and structured output are not automatically file-level examples for every model. Standalone STT/TTS belong to [Doubao Voice](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh) and are not covered by an Ark text Model ID or this file. [Evidence policy](evidence-policy.md)

`doubao-seed-2-0-pro-260215` and `doubao-seed-2-0-mini-260215` remain in the [official catalog](https://docs.volcengine.com/docs/ark/model-list?lang=zh), but this account did not complete a call, so they are not in the table or executable choices. A 404 `InvalidEndpointOrModel.NotFound` can mean the model/endpoint is absent **or** that the account cannot access it; it does not prove retirement. [Official error codes](https://docs.volcengine.com/docs/ark/error-codes?lang=zh)
