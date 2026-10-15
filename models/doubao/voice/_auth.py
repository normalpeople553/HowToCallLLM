"""Shared credential input for Doubao Voice examples."""

from __future__ import annotations

from getpass import getpass
import os
import sys


def read_key(from_stdin: bool) -> str:
    """Read the Voice API Key without adding platform-specific terminal code."""
    if not from_stdin:
        key = os.environ.get("DOUBAO_VOICE_API_KEY", "").strip()
        if not key:
            raise RuntimeError("请设置 DOUBAO_VOICE_API_KEY")
        return key
    if not sys.stdin.isatty():
        raise RuntimeError("--key-stdin 需要交互式终端")
    key = getpass("请输入豆包语音 API Key：").strip()
    if not key:
        raise RuntimeError("API Key 不能为空")
    return key
