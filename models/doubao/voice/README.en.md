# Doubao Voice: live-tested calls

[中文](README.md) · [Doubao overview](../../../en/docs/verified-doubao.md) · [Per-model activation and Key map](../../../en/docs/doubao-access-and-keys.md)

These four Python files were **run from this repository against the real API**. TTS 2.0 saved an MP3, which streaming ASR 2.0 read and transcribed. The direct audio-generation 1.0 API generated another MP3 and a temporary URL, which recorded-file ASR 2.0 transcribed. Audio and the URL remain under Git-ignored `.local/`. Credentials, audio, replies, and test times are not published. This verifies only the resources and parameters used, not every route for these capabilities. [Official TTS API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [Streaming ASR API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) · [Direct audio-generation API](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) · [Recorded-file ASR API](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh)

Activate the corresponding capabilities and obtain a **Doubao Voice API Key** in the [Voice console](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh); the Ark `ARK_API_KEY` is a different credential. Install `aiohttp` for ASR and system `ffmpeg`, then run from the repository root:

```bash
python -m pip install aiohttp
export DOUBAO_VOICE_API_KEY='your Doubao Voice API Key'
python models/doubao/voice/tts_2_0.py
python models/doubao/voice/streaming_asr_2_0.py
python models/doubao/voice/audio_generation_1_0.py
python models/doubao/voice/recorded_asr_2_0.py
```

The first script writes `.local/voice-tests/doubao-tts-2.0.mp3`; the second reads it. The third writes `.local/voice-tests/doubao-audio-generation-1.0.mp3` and a local `.url` file; the fourth submits that temporary URL to recorded-file ASR. The official direct audio-generation URL expires after **two hours**, so run the fourth promptly; alternatively provide your own `--audio-url`. TTS `--text` and `--speaker` select text and a compatible voice; audio-generation `--prompt` selects the generated content. `--key-stdin` reads a key from the terminal without echo. The scripts do not delete the original audio. [TTS parameters](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [Audio-generation response](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) · [Recorded-file API](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh)

| Sent field | Meaning here |
|---|---|
| TTS `X-Api-Resource-Id: seed-tts-2.0` | Selects the TTS 2.0 resource, not an Ark Model ID. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| TTS `req_params.text`, `speaker` | Text to speak and the compatible speaker ID; this is not sampling temperature. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| TTS `audio_params.format=mp3`, `sample_rate=24000` | Output encoding and sample rate, not context length. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| ASR `X-Api-Resource-Id: volc.seedasr.sauc.duration` | Uses the duration-billed ASR 2.0 resource. The concurrency-billed variant is a separate, untested resource. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| ASR `audio.format=wav`, `rate=16000`, `bits=16`, `channel=1` | Declares 16-kHz, 16-bit mono WAV, produced by FFmpeg before sending. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| ASR `request.model_name=bigmodel`, `enable_itn=true`, `enable_punc=true` | Selects large-model ASR and enables inverse text normalization and punctuation; not an output-token limit. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| Audio generation `model=seed-audio-1.0`, `text_prompt` | Selects the audio-generation model and prompt. The direct route uses a Voice Key but no `X-Api-Resource-Id`. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) |
| Audio generation `audio_config.format=mp3`, `sample_rate=24000` | Selects output format and sample rate, not a duration limit. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) |
| Recorded-file ASR `X-Api-Resource-Id: volc.seedasr.auc`, `audio.url` | Selects the standard 2.0 route and a server-accessible audio URL; a local path will not work. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh) |
| Recorded-file ASR `request.model_name=bigmodel`, `enable_itn=true` | Selects the ASR model and inverse text normalization. After submission, query the result with the same task ID. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh) |

Both files send unique request IDs. TTS concatenates Base64 audio chunks; its successful terminal event `code=20000000` must not be mistaken for an error. The ASR file uses the official **one-sentence** WebSocket route, not the live character-by-character display route; it requires a nonempty transcription to report success. [TTS protocol](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [ASR protocol](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh)

Audio generation also has a [MediaKit proxy route](https://docs.volcengine.com/docs/Intelligentprocessing/audio-generation?lang=zh), which requires cross-service authorization and a **separate MediaKit Key**. This directory uses the live-tested **Doubao Voice direct API**; do not mix their credentials. Voice cloning 2.0 still requires an authorized sample and a usable voice slot or postpaid speaker service; no repository code has passed a clone call. [Voice clone API](https://docs.volcengine.com/docs/DoubaoVoice/SoundReplicaAPI-V3?lang=zh) · [Speaker-service guide](https://docs.volcengine.com/docs/DoubaoVoice/Soundreplicationorderingandusageguide?lang=zh)
