"""已实测的豆包语音合成 2.0 最小示例；音频仅保存到本地。

运行：DOUBAO_VOICE_API_KEY=... python models/doubao/voice/tts_2_0.py
来源：https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from _auth import read_key


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / ".local" / "voice-tests" / "doubao-tts-2.0.mp3"
URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"


def json_events(body: str):
    decoder = json.JSONDecoder()
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if not line or line == "[DONE]":
            continue
        position = 0
        while position < len(line):
            event, consumed = decoder.raw_decode(line[position:])
            yield event
            position += consumed
            while position < len(line) and line[position].isspace():
                position += 1


def main() -> None:
    parser = argparse.ArgumentParser(description="豆包语音合成 2.0")
    parser.add_argument("--text", default="你好，我是豆包语音合成模型。请把这段语音用于识别测试。")
    parser.add_argument("--speaker", default="zh_female_vv_uranus_bigtts")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--key-stdin", action="store_true", help="从终端无回显读取 Key；不写入文件")
    args = parser.parse_args()
    payload = {
        "req_params": {
            "text": args.text,
            "speaker": args.speaker,
            "audio_params": {"format": "mp3", "sample_rate": 24000},
        }
    }
    request = Request(
        URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "X-Api-Key": read_key(args.key_stdin),
            "X-Api-Resource-Id": "seed-tts-2.0",
            "X-Api-Request-Id": str(uuid4()),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            body = response.read().decode("utf-8")
    except HTTPError as error:
        raise RuntimeError(f"TTS HTTP {error.code}；未保存音频") from None

    audio = bytearray()
    finished = False
    for event in json_events(body):
        if event.get("code") not in (None, 0, 20000000):
            raise RuntimeError(f"TTS 业务码 {event['code']}；未保存音频")
        if event.get("code") == 20000000:
            finished = True
        if event.get("data"):
            audio.extend(base64.b64decode(event["data"], validate=True))
    if not audio or not finished:
        raise RuntimeError("TTS 未收到完整音频及成功终止事件；未保存文件")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(audio)
    print(f"TTS 成功，已保存 {len(audio)} 字节：{args.output}")


if __name__ == "__main__":
    main()
