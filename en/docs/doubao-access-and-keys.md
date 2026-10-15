# Doubao: per-model activation and API Key map

[中文](../../docs/豆包开通与密钥.md) · [Verified calls](verified-doubao.md) · [Language-model catalog](model-lists/doubao.md)

Choose the **service** before the model: Volcano Ark, Doubao Voice, and AI MediaKit use distinct API Key types. The links below lead to official console pages and require sign-in. `projectName=default` in the Voice URLs means the default project; switch projects in the console if necessary. **Having a Key does not activate every model**: project, activation status, billing resource, and any Model ID / IP restrictions on the Key still matter. [Ark activation](https://docs.volcengine.com/docs/ark/activation-management?lang=zh) · [Ark API Keys](https://docs.volcengine.com/docs/ark/api-key?lang=zh) · [Voice console guide](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh)

## Ark language models: one Ark Key type

For each exact Model ID below, check or activate it in [Ark activation management][ark-open], then create a Key in [Ark API Key management][ark-key] under the same project. Code commonly stores this as `ARK_API_KEY`. **You do not need a separate Key per model.** Whether one Ark Key can call a particular model also depends on the model's availability, project access, Model ID / IP restrictions, region, and usage state. `doubao-seed-evolving` requires manual activation; older models past EOM may not be open to new accounts. [Official model list](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [Activation](https://docs.volcengine.com/docs/ark/activation-management?lang=zh) · [Deprecation](https://docs.volcengine.com/docs/ark/model-deprecation-notice?lang=zh) · [Key restrictions](https://docs.volcengine.com/docs/ark/api-key?lang=zh)

| Exact Model ID | Activation | Obtain Key | Repository verification |
|---|---|---|---|
| `doubao-seed-evolving` | [Ark activation][ark-open] (manual) | [Ark Key][ark-key] | Minimal Chat call passed |
| `doubao-seed-2-1-pro-260915` | [Ark activation][ark-open] | [Ark Key][ark-key] | Minimal Chat call passed |
| `doubao-seed-2-1-lite-260915` | [Ark activation][ark-open] | [Ark Key][ark-key] | Minimal Chat call passed |
| `doubao-seed-2-1-turbo-260628` | [Ark activation][ark-open] | [Ark Key][ark-key] | Minimal Chat call passed |
| `doubao-seed-2-1-pro-260628` | [Ark activation][ark-open] | [Ark Key][ark-key] | Minimal Chat call passed |
| `doubao-seed-2-0-lite-260428` | [Ark activation][ark-open] | [Ark Key][ark-key] | Minimal Chat call passed |
| `doubao-seed-2-0-mini-260428` | [Ark activation][ark-open] | [Ark Key][ark-key] | Minimal Chat call passed |
| `doubao-seed-2-0-pro-260215` | [Ark activation][ark-open] (past EOM; check existing access) | [Ark Key][ark-key] | Did not pass on this account; not verified |
| `doubao-seed-2-0-mini-260215` | [Ark activation][ark-open] (past EOM; check existing access) | [Ark Key][ark-key] | Did not pass on this account; not verified |
| `doubao-seed-character-260628` | [Ark activation][ark-open] | [Ark Key][ark-key] | Minimal Chat call passed |
| `doubao-seed-character-251128` | [Ark activation][ark-open] | [Ark Key][ark-key] | Minimal Chat call passed |
| `doubao-seed-translation-250915` | [Ark activation][ark-open] | [Ark Key][ark-key] | Responses translation passed; not a Chat call |
| `doubao-seed-2-0-lite-260215` | [Ark activation][ark-open] (existing integrations) | [Ark Key][ark-key] | Minimal Chat call passed; EOS announced |
| `doubao-seed-2-0-code-preview-260215` | [Ark activation][ark-open] (existing integrations) | [Ark Key][ark-key] | Minimal Chat call passed; EOS announced |

“Passed” refers only to the [repository's exact-ID minimal calls](../../models/doubao/verified_calls.py), not general availability for all accounts. The two older IDs marked “did not pass” still appear in the official catalog but are **not** presented as verified. [Official catalog](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [Verification boundary](verified-doubao.md)

## Doubao Voice models: one Voice Key per project

Activate the **specific capability** in [Voice activation management][voice-open], then obtain a Key under the same project from [Doubao Voice API Key management][voice-key]. Code stores it as `DOUBAO_VOICE_API_KEY`; APIs generally send it in `X-Api-Key`. **One Voice Key can serve multiple activated and compatible Voice models in its project**; activating one capability does not automatically activate the others. Speaker IDs, model IDs, and resource IDs are not API Keys. [Official console guide](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh) · [API Key usage](https://docs.volcengine.com/docs/DoubaoVoice/APIKeyUsage?lang=zh)

| Console model / capability | Activation | Obtain Key | Additional request selector | Repository verification |
|---|---|---|---|---|
| TTS 2.0 | [Voice activation][voice-open] | [Voice Key][voice-key] | `X-Api-Resource-Id: seed-tts-2.0` and a compatible Speaker ID. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) | [Passed](../../models/doubao/voice/tts_2_0.py) |
| Streaming ASR 2.0 | [Voice activation][voice-open] | [Voice Key][voice-key] | Duration-based `volc.seedasr.sauc.duration` or concurrency-based `volc.seedasr.sauc.concurrent`; only the former was tested. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) | [Duration-based route passed](../../models/doubao/voice/streaming_asr_2_0.py) |
| Recorded-file ASR 2.0 | [Voice activation][voice-open] | [Voice Key][voice-key] | Standard route `volc.seedasr.auc` plus a server-accessible audio URL. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh) | [Standard route passed](../../models/doubao/voice/recorded_asr_2_0.py) |
| Audio generation 1.0 | [Voice activation][voice-open] | [Voice Key][voice-key] | The direct API sends `model: seed-audio-1.0`, **not** `X-Api-Resource-Id`; it returns audio and a temporary URL. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) | [Direct API passed](../../models/doubao/voice/audio_generation_1_0.py) |
| Voice clone 2.0 | [Voice activation][voice-open] | [Voice Key][voice-key] | Training requires an authorized sample and a usable Speaker ID/slot or postpaid speaker service; synthesis of a cloned voice uses `seed-icl-2.0`. [Training API](https://docs.volcengine.com/docs/DoubaoVoice/SoundReplicaAPI-V3?lang=zh) · [Speaker-service guide](https://docs.volcengine.com/docs/DoubaoVoice/Soundreplicationorderingandusageguide?lang=zh) | Not live-tested; no success claim |

The activation link opens the project list, not necessarily a specific model row; search by the model's Chinese console name. If access is denied or “开通管理” is missing, check sign-in, project, and subaccount permissions. [New-console guide](https://docs.volcengine.com/docs/DoubaoVoice/QuickStartNewConsole?lang=zh) · [Console FAQ](https://docs.volcengine.com/docs/DoubaoVoice/ConsoleUsageFAQ?lang=zh)

## Audio generation 1.0 also has a MediaKit proxy route

The [Doubao Voice direct API](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) uses a **Doubao Voice Key** to call an activated `seed-audio-1.0`; this is the route tested in this repository. The alternative [AI MediaKit proxy guide](https://docs.volcengine.com/docs/Intelligentprocessing/audio-generation?lang=zh) additionally requires cross-service authorization in [MediaKit authorization management][mediakit-auth] and a **MediaKit Key** created in [MediaKit API Key management][mediakit-key]. On that route, the MediaKit Key authenticates the proxy endpoint; it does not replace a Voice Key for the direct API or an Ark Key. A previous attempt to send the Voice Key to the MediaKit proxy returned 403; that did not establish a problem with the Voice direct API. [Official MediaKit guide](https://docs.volcengine.com/docs/Intelligentprocessing/audio-generation?lang=zh)

[ark-open]: https://ark.volcengine.com/region:cn-beijing/openManagement
[ark-key]: https://ark.volcengine.com/region:cn-beijing/apikey
[voice-open]: https://console.volcengine.com/speech/new/setting/activate?projectName=default
[voice-key]: https://console.volcengine.com/speech/new/setting/apikeys?projectName=default
[mediakit-auth]: https://console.volcengine.com/imp/ai-mediakit/settings?projectName=default&tab=authorization
[mediakit-key]: https://console.volcengine.com/imp/ai-mediakit/settings
