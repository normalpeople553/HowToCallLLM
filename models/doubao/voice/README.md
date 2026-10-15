# 豆包语音：已实际运行的调用

[English](README.en.md) · [豆包总览](../../../docs/豆包已验证调用.md)

本目录有两份**以仓库原文件发起真实请求并成功**的 Python 示例：语音合成 2.0 把文本写成 MP3；流式语音识别 2.0 再读取这段 MP3，转成 WAV 后按 WebSocket 协议发送并取得非空文字。测试音频只留在被 Git 忽略的 `.local/`，不上传音频、密钥、模型回复或测试时间。成功仅覆盖此 Key、此音色、此计费资源和这些参数，不等于该能力的所有接口都已验证。[TTS 官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [流式识别官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh)

在[豆包语音控制台](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh)开通对应能力并创建**豆包语音 API Key**，不是方舟 `ARK_API_KEY`。安装 `aiohttp`（仅识别脚本需要）及系统 `ffmpeg`，然后在仓库根目录运行：

```bash
python -m pip install aiohttp
export DOUBAO_VOICE_API_KEY='你的豆包语音 API Key'
python models/doubao/voice/tts_2_0.py
python models/doubao/voice/streaming_asr_2_0.py
```

第一步默认生成 `.local/voice-tests/doubao-tts-2.0.mp3`；第二步默认读取同一路径。可分别用 `--output` 和 `--audio` 修改；`--text` 修改要合成的文字，`--speaker` 修改官方音色库中与你开通的 TTS 2.0 兼容的音色。若不想把 Key 写入 shell 环境，也可给两个脚本加 `--key-stdin`，在终端无回显输入。脚本不删除原始音频。[TTS 音色/请求参数](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [流式识别音频参数](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh)

| 发送的字段 | 本示例里的作用 |
|---|---|
| TTS `X-Api-Resource-Id: seed-tts-2.0` | 指定语音合成 2.0 资源；不要用方舟模型 ID 替换。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| TTS `req_params.text`、`speaker` | 要朗读的文本和对应音色 ID；`speaker` 不是采样温度。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| TTS `audio_params.format=mp3`、`sample_rate=24000` | 输出编码格式与采样率；不是上下文长度。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| STT `X-Api-Resource-Id: volc.seedasr.sauc.duration` | 使用流式识别 2.0 的小时版资源；并发版是另一个资源，本文件未测试。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| STT `audio.format=wav`、`rate=16000`、`bits=16`、`channel=1` | 告诉接口发送的是 16 kHz、16-bit、单声道 WAV；脚本先用 FFmpeg 转码。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| STT `request.model_name=bigmodel`、`enable_itn=true`、`enable_punc=true` | 选择大模型识别，并启用逆文本规范化、标点处理；不是模型输出 token 上限。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |

两个脚本都带唯一请求 ID。TTS 会拼接服务端返回的 Base64 音频分片；其成功终止事件 `code=20000000` 不能误当失败。STT 使用官网的“一句话识别” WebSocket 路径，不是实时逐字上屏接口；最后收到非空识别文字才算成功。[TTS 响应协议](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [一句话识别协议](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh)

录音文件识别 2.0 要提交服务端可访问的音频 URL；本地 `.local/` 文件不能直接作为 URL。音频生成 1.0 在[官方 MediaKit 接入路线](https://docs.volcengine.com/docs/Intelligentprocessing/audio-generation?lang=zh)还需跨服务授权和 MediaKit API Key。声音复刻 2.0 需要有使用授权的样音及可用音色槽位/后付费音色服务。这三项尚无本仓库**跑通的代码**，因此不在本目录伪列示例。[录音文件识别接口](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh) · [声音复刻接口](https://docs.volcengine.com/docs/DoubaoVoice/SoundReplicaAPI-V3?lang=zh) · [音色订购说明](https://docs.volcengine.com/docs/DoubaoVoice/Soundreplicationorderingandusageguide?lang=zh)
