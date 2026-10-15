"""豆包音频生成 1.0 直连接口，已用仓库原文件真实执行。

运行：DOUBAO_VOICE_API_KEY=... python models/doubao/voice/audio_generation_1_0.py
来源：https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from tts_2_0 import read_key


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIO = ROOT / ".local" / "voice-tests" / "doubao-audio-generation-1.0.mp3"
DEFAULT_URL_FILE = ROOT / ".local" / "voice-tests" / "doubao-audio-generation-1.0.url"
ENDPOINT = "https://openspeech.bytedance.com/api/v3/tts/create"


def main() -> None:
    parser = argparse.ArgumentParser(description="豆包音频生成 1.0：文本生成音频")
    parser.add_argument(
        "--prompt",
        default="请生成一段约五秒的清晰普通话女声，只说：你好，欢迎使用豆包语音识别。这是一段测试录音。不要背景音乐。",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument("--url-file", type=Path, default=DEFAULT_URL_FILE)
    parser.add_argument("--key-stdin", action="store_true", help="从终端无回显读取 Key")
    args = parser.parse_args()
    payload = {
        "model": "seed-audio-1.0",
        "text_prompt": args.prompt,
        "audio_config": {"format": "mp3", "sample_rate": 24000},
    }
    request = Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "X-Api-Key": read_key(args.key_stdin),
            "X-Api-Request-Id": str(uuid4()),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=300) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"音频生成 HTTP {error.code}；未保存音频") from None
    if result.get("code") not in (None, 0, 20000000):
        raise RuntimeError(f"音频生成业务码 {result['code']}；未保存音频")
    audio_base64, audio_url = result.get("audio"), result.get("url")
    if not audio_base64 or not audio_url:
        raise RuntimeError("接口未同时返回音频和临时 URL")
    audio = base64.b64decode(audio_base64, validate=True)
    if not audio:
        raise RuntimeError("接口返回了空音频")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.url_file.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(audio)
    args.url_file.write_text(audio_url + "\n", encoding="utf-8")
    print(f"音频生成成功：{len(audio)} 字节，保存到 {args.output}")
    print(f"服务端可读取的临时音频 URL 保存到 {args.url_file}，用于录音文件识别示例")


if __name__ == "__main__":
    main()
