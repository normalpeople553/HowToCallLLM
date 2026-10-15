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

## How to activate the models

The language models on this page and standalone STT/TTS use **two separate services: Ark and Doubao Voice**. Activate the model and create the API Key in the target project of each service. An existing `ARK_API_KEY` does not activate Doubao Voice and is not its `X-Api-Key`. [Ark API Key](https://docs.volcengine.com/docs/ark/api-key?lang=zh) · [Doubao Voice console guide](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh)

### Language models on this page: Ark

1. Sign in to [Ark activation management](https://docs.volcengine.com/docs/ark/activation-management?lang=zh), select the project you will call from, find the **exact Model ID**, and choose “开通服务” (activate service). Follow the confirmation dialog. A model marked “邀测中” (invitation only) cannot be activated through self-service; the official guide says to submit a support ticket. Check the console for the current status. [Activation management](https://docs.volcengine.com/docs/ark/activation-management?lang=zh)
2. Even if automatic activation of new models is enabled, activate `doubao-seed-evolving` manually. Check its status and billing terms; neither free quota nor activation means permanently free use. [Activation management](https://docs.volcengine.com/docs/ark/activation-management?lang=zh)
3. Create or retrieve a Key in [Ark API Key management](https://docs.volcengine.com/docs/ark/api-key?lang=zh) under the **same project** and set `ARK_API_KEY` as shown below. If the Key has Model ID or IP restrictions, ensure this call is allowed. [Ark API Key](https://docs.volcengine.com/docs/ark/api-key?lang=zh)

### Standalone STT/TTS: Doubao Voice

STT turns audio into text; TTS turns text into audio. Neither is in the Ark model table above, but TTS 2.0 and streaming ASR 2.0 now have [separately live-tested examples](../../models/doubao/voice/README.en.md). These are the official activation steps. [Doubao Voice console guide](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh)

1. Open the Doubao Voice console described in the [new-console quick start](https://docs.volcengine.com/docs/DoubaoVoice/QuickStartNewConsole?lang=zh) and select the target project in the upper-left corner. First-time users should follow the official registration and identity-verification steps. An initial one-click activation may be offered; follow what your console shows. [New-console quick start](https://docs.volcengine.com/docs/DoubaoVoice/QuickStartNewConsole?lang=zh)
2. Under “开通管理” (activation management), activate the **recorded-file recognition** or **streaming recognition** model needed for STT, and **Doubao TTS model 2.0** for TTS. Select “开通”, accept the service terms, then select “开通模型”. Activating one speech model does **not** establish access to every other speech model; check each status in the same project. [Console guide](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh) · [New-console quick start](https://docs.volcengine.com/docs/DoubaoVoice/QuickStartNewConsole?lang=zh)
3. Create or retrieve a **Doubao Voice API Key** under “API管理”/“API Key管理” in that project. Speech requests use `X-Api-Key` plus the `X-Api-Resource-Id` of the activated capability. Do not substitute the Ark `ARK_API_KEY`. Keys and resources are isolated by project. [Console guide](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh) · [Recorded-file STT HTTP](https://docs.volcengine.com/docs/DoubaoVoice/recording-file-recognition-lite-http?lang=zh) · [TTS HTTP](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh)
4. Match the resource ID to the selected API: [standard recorded-file recognition 2.0](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh) uses `volc.seedasr.auc`, while [TTS 2.0](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) uses `seed-tts-2.0`. For TTS, obtain a compatible Speaker ID from the [official voice library](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh). The separate [fast recorded-file API](https://docs.volcengine.com/docs/DoubaoVoice/recording-file-recognition-lite-http?lang=zh) shows `volc.bigasr.auc_turbo`; do not mix its resource ID with the standard or streaming API.

Before activation, use the [Doubao Voice console guide](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh) to find billing and resource-purchase controls. Actual prices, balance, free quota, and service status are specific to **your project's console**. If “开通管理” is missing for a subaccount, check the speech-service permission guidance in the [console FAQ](https://docs.volcengine.com/docs/DoubaoVoice/ConsoleUsageFAQ?lang=zh).

### Mapping of activated speech capabilities to APIs

The following **integration routes** are based on a user-provided Doubao Voice console screenshot and official API documentation. TTS 2.0 and streaming ASR 2.0 have [live-tested repository code](../../models/doubao/voice/README.en.md); the other three are official routes, not verified calls in this repository. Check the service status, Voice API Key, speaker, and billing mode in the same project before use. [Console guide](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh)

| Console capability | Official API and identifier | Essential flow |
|---|---|---|
| TTS 2.0 — tested | [Unidirectional TTS HTTP](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh); `X-Api-Resource-Id: seed-tts-2.0` | [Executed code](../../models/doubao/voice/tts_2_0.py): supplies `text`, compatible `speaker`, and `audio_params`; joins chunks into a local MP3. Copy the speaker ID from the [voice library](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh). |
| Recorded-file STT 2.0 | [Standard HTTP API](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh); `X-Api-Resource-Id: volc.seedasr.auc` | Submit an accessible audio URL, obtain a task ID, then poll the [result-query API](https://docs.volcengine.com/docs/DoubaoVoice/result-query-http-1?lang=zh). The final text is not returned in one request. |
| Streaming STT 2.0 — duration-based tested | [One-sentence WebSocket API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh); duration-based `volc.seedasr.sauc.duration` or concurrency-based `volc.seedasr.sauc.concurrent` | [Executed code](../../models/doubao/voice/streaming_asr_2_0.py): converts MP3 to WAV, sends binary audio packets, and checks for nonempty text. The concurrency-based variant was not tested. |
| Voice clone 2.0 | [Voice Clone V3 training API](https://docs.volcengine.com/docs/DoubaoVoice/SoundReplicaAPI-V3?lang=zh); the TTS resource ID for cloned speech is [`seed-icl-2.0`](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) | Obtain a valid clone Speaker ID, train through V3, check its state, then synthesize using that speaker. If the voice-slot service is not activated, follow the [official purchase guide](https://docs.volcengine.com/docs/DoubaoVoice/Soundreplicationorderingandusageguide?lang=zh) for a prepaid slot or separately activate postpaid speaker service. Activating the clone model alone is insufficient for a finished clone call. |
| Audio generation 1.0 | The official [AI MediaKit integration guide](https://docs.volcengine.com/docs/Intelligentprocessing/audio-generation?lang=zh) uses `model: seed-audio-1.0` | Prompt-based audio-scene generation is **not** TTS 2.0. The documented MediaKit route additionally requires cross-service authorization and a separate MediaKit API Key; submit an asynchronous task and query its result. Do not reuse the TTS endpoint. |

This page publishes only the [TTS and streaming STT files that passed live calls](../../models/doubao/voice/README.en.md). It does not treat console activation as proof that the remaining three APIs work. [Evidence policy](evidence-policy.md)

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
