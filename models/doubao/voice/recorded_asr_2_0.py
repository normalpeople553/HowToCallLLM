"""豆包录音文件识别 2.0 标准版，已用仓库原文件真实执行。

先运行 audio_generation_1_0.py 获取临时 URL，再运行本文件。
来源：https://docs.volcengine.com/docs/DoubaoVoice/LargemodelrecordingfilerecognitionstandardversionAPI?lang=zh
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from tts_2_0 import read_key


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_URL_FILE = ROOT / ".local" / "voice-tests" / "doubao-audio-generation-1.0.url"
BASE = "https://openspeech.bytedance.com/api/v3/auc/bigmodel"


def post(path: str, payload: dict, headers: dict) -> tuple[str | None, bytes]:
    request = Request(
        BASE + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            return response.headers.get("X-Api-Status-Code"), response.read()
    except HTTPError as error:
        raise RuntimeError(f"录音识别 HTTP {error.code}") from None


def main() -> None:
    parser = argparse.ArgumentParser(description="豆包录音文件识别 2.0 标准版")
    parser.add_argument("--audio-url", help="服务端可访问的 MP3 URL；优先于 --url-file")
    parser.add_argument("--url-file", type=Path, default=DEFAULT_URL_FILE)
    parser.add_argument("--key-stdin", action="store_true", help="从终端无回显读取 Key")
    args = parser.parse_args()
    audio_url = args.audio_url or args.url_file.read_text(encoding="utf-8").strip()
    if not audio_url.startswith("https://"):
        raise ValueError("请提供服务端可访问的 HTTPS 音频 URL，不是本地文件路径")
    task_id = str(uuid4())
    headers = {
        "X-Api-Key": read_key(args.key_stdin),
        "X-Api-Resource-Id": "volc.seedasr.auc",
        "X-Api-Request-Id": task_id,
        "X-Api-Sequence": "-1",
    }
    code, _ = post(
        "/submit",
        {
            "user": {"uid": "model-manual-example"},
            "audio": {"format": "mp3", "url": audio_url},
            "request": {"model_name": "bigmodel", "enable_itn": True},
        },
        headers,
    )
    if code != "20000000":
        raise RuntimeError(f"任务提交未成功：{code}")
    for _ in range(30):
        time.sleep(2)
        code, body = post("/query", {}, headers)
        if code in ("20000001", "20000002"):
            continue
        if code != "20000000":
            raise RuntimeError(f"任务查询失败：{code}")
        result = json.loads(body)
        text = result.get("result", {}).get("text")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("任务完成，但无非空识别正文")
        print(text)
        return
    raise TimeoutError("录音识别任务未在 60 秒内完成；请用任务 ID 排查")


if __name__ == "__main__":
    main()
