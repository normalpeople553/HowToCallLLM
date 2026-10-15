"""Cross-platform startup and credential checks for Doubao Voice examples."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
VOICE = ROOT / "models/doubao/voice"
AUTH_SOURCE = VOICE / "_auth.py"
spec = importlib.util.spec_from_file_location("doubao_voice_auth", AUTH_SOURCE)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class DoubaoVoiceExamplesTests(unittest.TestCase):
    def test_all_scripts_start_and_show_help_without_optional_dependencies(self):
        for name in (
            "tts_2_0.py",
            "streaming_asr_2_0.py",
            "audio_generation_1_0.py",
            "recorded_asr_2_0.py",
        ):
            with self.subTest(script=name):
                completed = subprocess.run(
                    [sys.executable, str(VOICE / name), "--help"],
                    cwd=ROOT,
                    capture_output=True,
                    timeout=10,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr.decode(errors="replace"))
                self.assertIn(b"usage:", completed.stdout)

    def test_environment_key_is_trimmed(self):
        with patch.dict(os.environ, {"DOUBAO_VOICE_API_KEY": "  fixture-key  "}, clear=True):
            self.assertEqual(auth.read_key(False), "fixture-key")

    def test_missing_environment_key_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DOUBAO_VOICE_API_KEY"):
                auth.read_key(False)

    def test_interactive_key_uses_cross_platform_getpass(self):
        with patch.object(auth.sys.stdin, "isatty", return_value=True), \
                patch.object(auth, "getpass", return_value="  fixture-key  ") as hidden_input:
            self.assertEqual(auth.read_key(True), "fixture-key")
        hidden_input.assert_called_once()

    def test_noninteractive_stdin_is_rejected(self):
        with patch.object(auth.sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "交互式终端"):
                auth.read_key(True)


if __name__ == "__main__":
    unittest.main()
