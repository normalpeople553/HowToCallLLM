# Doubao Voice: live-tested calls

[中文](README.md) · [Doubao overview](../../../en/docs/verified-doubao.md)

These two Python files were **run from this repository against the real API**. TTS 2.0 saved an MP3; streaming ASR 2.0 read that MP3, converted it to WAV, sent it over WebSocket, and received nonempty text. The generated audio remains under Git-ignored `.local/`. Credentials, audio, replies, and test times are not published. This verifies only the exact resource IDs, speaker, and parameters used here, not every route for these capabilities. [Official TTS API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [Official streaming ASR API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh)

Activate the corresponding capabilities and obtain a **Doubao Voice API Key** in the [Voice console](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh); the Ark `ARK_API_KEY` is a different credential. Install `aiohttp` for ASR and system `ffmpeg`, then run from the repository root:

```bash
python -m pip install aiohttp
export DOUBAO_VOICE_API_KEY='your Doubao Voice API Key'
python models/doubao/voice/tts_2_0.py
python models/doubao/voice/streaming_asr_2_0.py
```

The first script writes `.local/voice-tests/doubao-tts-2.0.mp3`; the second reads the same path. Override them with `--output` and `--audio`. Use `--text` for synthesis input and `--speaker` for a compatible 2.0 speaker ID from the official voice catalog. `--key-stdin` reads a key from the terminal without echo instead of from an environment variable. The scripts do not delete the original audio. [TTS parameters](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [ASR parameters](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh)

| Sent field | Meaning here |
|---|---|
| TTS `X-Api-Resource-Id: seed-tts-2.0` | Selects the TTS 2.0 resource, not an Ark Model ID. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| TTS `req_params.text`, `speaker` | Text to speak and the compatible speaker ID; this is not sampling temperature. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| TTS `audio_params.format=mp3`, `sample_rate=24000` | Output encoding and sample rate, not context length. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| ASR `X-Api-Resource-Id: volc.seedasr.sauc.duration` | Uses the duration-billed ASR 2.0 resource. The concurrency-billed variant is a separate, untested resource. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| ASR `audio.format=wav`, `rate=16000`, `bits=16`, `channel=1` | Declares 16-kHz, 16-bit mono WAV, produced by FFmpeg before sending. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| ASR `request.model_name=bigmodel`, `enable_itn=true`, `enable_punc=true` | Selects large-model ASR and enables inverse text normalization and punctuation; not an output-token limit. [Official API](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |

Both files send unique request IDs. TTS concatenates Base64 audio chunks; its successful terminal event `code=20000000` must not be mistaken for an error. The ASR file uses the official **one-sentence** WebSocket route, not the live character-by-character display route; it requires a nonempty transcription to report success. [TTS protocol](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [ASR protocol](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh)

Recorded-file ASR 2.0 requires an audio URL accessible to the service; the local `.local/` file is not such a URL. The [official MediaKit route](https://docs.volcengine.com/docs/Intelligentprocessing/audio-generation?lang=zh) for audio generation 1.0 also requires cross-service authorization and a MediaKit API Key. Voice cloning 2.0 requires an authorized voice sample and a usable voice slot or postpaid speaker service. There is **no live-tested repository code** for these three yet. [Recorded-file ASR](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh) · [Voice clone API](https://docs.volcengine.com/docs/DoubaoVoice/SoundReplicaAPI-V3?lang=zh) · [Speaker-service guide](https://docs.volcengine.com/docs/DoubaoVoice/Soundreplicationorderingandusageguide?lang=zh)
