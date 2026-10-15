"""已实测的豆包流式语音识别 2.0 一句话识别示例。

依赖：python -m pip install aiohttp；系统需安装 ffmpeg。
运行：DOUBAO_VOICE_API_KEY=... python models/doubao/voice/streaming_asr_2_0.py
来源：https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-automatic-speech-recognition-websocket?lang=zh
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import struct
import subprocess
from pathlib import Path
from uuid import uuid4

try:
    import aiohttp
except ModuleNotFoundError:
    aiohttp = None

from _auth import read_key


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIO = ROOT / ".local" / "voice-tests" / "doubao-tts-2.0.mp3"
URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream"


def frame(message_type: int, flags: int, sequence: int, data: bytes, json_payload: bool) -> bytes:
    compressed = gzip.compress(data)
    header = bytes([0x11, (message_type << 4) | flags, (0x10 if json_payload else 0) | 0x01, 0])
    return header + struct.pack(">iI", sequence, len(compressed)) + compressed


def parse_frame(raw: bytes) -> tuple[int, bool, dict | None, int]:
    if len(raw) < 4:
        raise ValueError("服务端帧过短")
    header_len = (raw[0] & 0x0F) * 4
    message_type = raw[1] >> 4
    flags = raw[1] & 0x0F
    position = header_len
    is_last = bool(flags & 0x02)
    if flags & 0x01:
        position += 4  # sequence
    if flags & 0x04:
        position += 4  # event
    error_code = 0
    if message_type == 0x0F:
        error_code = struct.unpack(">i", raw[position : position + 4])[0]
        position += 4
    if message_type in (0x09, 0x0F):
        payload_len = struct.unpack(">I", raw[position : position + 4])[0]
        position += 4
        payload = raw[position : position + payload_len]
    else:
        payload = b""
    if payload and (raw[2] & 0x0F) == 1:
        payload = gzip.decompress(payload)
    data = json.loads(payload) if payload and (raw[2] >> 4) == 1 else None
    return message_type, is_last, data, error_code


async def recognize(audio_path: Path, key: str) -> str:
    if aiohttp is None:
        raise RuntimeError("缺少 aiohttp；请先运行：python -m pip install aiohttp")
    wav = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(audio_path), "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", "-f", "wav", "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    if not wav.startswith(b"RIFF"):
        raise RuntimeError("音频未能转为 WAV")
    headers = {
        "X-Api-Key": key,
        "X-Api-Resource-Id": "volc.seedasr.sauc.duration",
        "X-Api-Request-Id": str(uuid4()),
    }
    payload = {
        "user": {"uid": "model-manual-example"},
        "audio": {"format": "wav", "codec": "raw", "rate": 16000, "bits": 16, "channel": 1},
        "request": {"model_name": "bigmodel", "enable_itn": True, "enable_punc": True},
    }
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.ws_connect(URL, headers=headers) as websocket:
            await websocket.send_bytes(frame(1, 1, 1, json.dumps(payload).encode(), True))
            ack = await websocket.receive(timeout=10)
            if ack.type != aiohttp.WSMsgType.BINARY:
                raise RuntimeError(f"异常的识别确认帧：{ack.type}")
            _, _, _, ack_error = parse_frame(ack.data)
            if ack_error:
                raise RuntimeError(f"识别确认错误码：{ack_error}")
            chunk_bytes = 6400  # 16 kHz × 16-bit × 0.2 seconds
            chunks = [wav[i : i + chunk_bytes] for i in range(0, len(wav), chunk_bytes)]
            for index, chunk in enumerate(chunks, start=2):
                last = index == len(chunks) + 1
                await websocket.send_bytes(frame(2, 3 if last else 1, -index if last else index, chunk, False))
                await asyncio.sleep(0.2)
            final_text = None
            completed = False
            for _ in range(len(chunks) + 20):
                message = await websocket.receive(timeout=15)
                if message.type != aiohttp.WSMsgType.BINARY:
                    raise RuntimeError(f"异常的识别结果帧：{message.type}")
                _, last, data, error_code = parse_frame(message.data)
                if error_code:
                    raise RuntimeError(f"识别错误码：{error_code}")
                if isinstance(data, dict):
                    final_text = data.get("result", {}).get("text") or final_text
                if last:
                    completed = True
                    break
            if not completed or not final_text:
                raise RuntimeError("服务端未返回完整且非空的识别正文")
            return final_text


def main() -> None:
    parser = argparse.ArgumentParser(description="豆包流式语音识别 2.0")
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument("--key-stdin", action="store_true", help="从终端无回显读取 Key；不写入文件")
    args = parser.parse_args()
    print(asyncio.run(recognize(args.audio, read_key(args.key_stdin))))


if __name__ == "__main__":
    main()
