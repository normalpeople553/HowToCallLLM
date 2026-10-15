# 豆包语音：已实际运行的调用

[English](README.en.md) · [豆包总览](../../../docs/豆包已验证调用.md) · [逐模型开通与 Key 对照](../../../docs/豆包开通与密钥.md)

本目录有四份**以仓库原文件发起真实请求并成功**的 Python 示例：语音合成 2.0 生成 MP3，流式识别 2.0 读取它并取得文字；音频生成 1.0 直连接口生成另一段 MP3 与临时 URL，录音文件识别 2.0 用该 URL 取得文字。测试音频和 URL 只留在被 Git 忽略的 `.local/`，不上传音频、密钥、模型回复或测试时间。成功仅覆盖所用 Key、资源及参数，不等于这些能力的所有接口都已验证。[TTS 官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [流式识别接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) · [音频生成直连接口](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) · [录音文件识别接口](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh)

在[豆包语音控制台](https://docs.volcengine.com/docs/DoubaoVoice/console-guidance?lang=zh)开通对应能力并创建**豆包语音 API Key**，不是方舟 `ARK_API_KEY`。安装 `aiohttp`（仅识别脚本需要）及系统 `ffmpeg`，然后在仓库根目录运行：

```bash
python -m pip install aiohttp
export DOUBAO_VOICE_API_KEY='你的豆包语音 API Key'
python models/doubao/voice/tts_2_0.py
python models/doubao/voice/streaming_asr_2_0.py
python models/doubao/voice/audio_generation_1_0.py
python models/doubao/voice/recorded_asr_2_0.py
```

Windows PowerShell 使用同一组 Python 文件，只需改用 PowerShell 的环境变量语法：

```powershell
python -m pip install aiohttp
$env:DOUBAO_VOICE_API_KEY="你的豆包语音 API Key"
python models/doubao/voice/tts_2_0.py
python models/doubao/voice/streaming_asr_2_0.py
python models/doubao/voice/audio_generation_1_0.py
python models/doubao/voice/recorded_asr_2_0.py
```

第一步默认生成 `.local/voice-tests/doubao-tts-2.0.mp3`；第二步默认读取同一路径。第三步生成 `.local/voice-tests/doubao-audio-generation-1.0.mp3` 和仅供本地使用的 `.url` 文件；第四步读取此临时 URL 提交录音识别任务。官方音频生成直连响应的 URL 有效期为 **2 小时**，请及时运行第四步；也可为录音识别脚本传入自己的 `--audio-url`。TTS 的 `--text` 和 `--speaker` 分别选择文本与兼容音色；音频生成的 `--prompt` 决定生成内容。若不想把 Key 写入 shell 环境，可给各脚本加 `--key-stdin`，它通过 Python 跨平台的 `getpass` 在终端无回显输入。脚本不删除原始音频。[TTS 音色/请求参数](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [音频生成响应](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) · [录音文件接口](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh)

| 发送的字段 | 本示例里的作用 |
|---|---|
| TTS `X-Api-Resource-Id: seed-tts-2.0` | 指定语音合成 2.0 资源；不要用方舟模型 ID 替换。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| TTS `req_params.text`、`speaker` | 要朗读的文本和对应音色 ID；`speaker` 不是采样温度。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| TTS `audio_params.format=mp3`、`sample_rate=24000` | 输出编码格式与采样率；不是上下文长度。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) |
| STT `X-Api-Resource-Id: volc.seedasr.sauc.duration` | 使用流式识别 2.0 的小时版资源；并发版是另一个资源，本文件未测试。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| STT `audio.format=wav`、`rate=16000`、`bits=16`、`channel=1` | 告诉接口发送的是 16 kHz、16-bit、单声道 WAV；脚本先用 FFmpeg 转码。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| STT `request.model_name=bigmodel`、`enable_itn=true`、`enable_punc=true` | 选择大模型识别，并启用逆文本规范化、标点处理；不是模型输出 token 上限。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh) |
| 音频生成 `model=seed-audio-1.0`、`text_prompt` | 选择音频生成模型与生成提示词；直连接口用语音 Key，但没有 `X-Api-Resource-Id`。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) |
| 音频生成 `audio_config.format=mp3`、`sample_rate=24000` | 选择返回音频格式和采样率；不是生成时长上限。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh) |
| 录音识别 `X-Api-Resource-Id: volc.seedasr.auc`、`audio.url` | 选择 2.0 标准版并提供服务端可读取的音频 URL；本地文件路径不行。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh) |
| 录音识别 `request.model_name=bigmodel`、`enable_itn=true` | 选择识别模型并启用逆文本规范化；提交成功后还须以同一任务 ID 查询结果。[官方接口](https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh) |

两个脚本都带唯一请求 ID。TTS 会拼接服务端返回的 Base64 音频分片；其成功终止事件 `code=20000000` 不能误当失败。STT 使用官网的“一句话识别” WebSocket 路径，不是实时逐字上屏接口；最后收到非空识别文字才算成功。[TTS 响应协议](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh) · [一句话识别协议](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh)

音频生成另有[MediaKit 代理路线](https://docs.volcengine.com/docs/Intelligentprocessing/audio-generation?lang=zh)，它需要跨服务授权与**单独的 MediaKit Key**；本目录使用已实测的**豆包语音直连接口**，不能混用 Key。声音复刻 2.0 仍需要有使用授权的样音及可用音色槽位/后付费音色服务；没有本仓库跑通的代码。[声音复刻接口](https://docs.volcengine.com/docs/DoubaoVoice/SoundReplicaAPI-V3?lang=zh) · [音色订购说明](https://docs.volcengine.com/docs/DoubaoVoice/Soundreplicationorderingandusageguide?lang=zh)
