"""Offline checks for the optional skill's local credential boundary."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/call-llm/scripts/keyenv.py"
spec = importlib.util.spec_from_file_location("call_llm_keyenv", SCRIPT)
keyenv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(keyenv)


class KeyenvTests(unittest.TestCase):
    def test_init_creates_blank_file_once_without_overwriting_user_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / ".call-llm" / "keyenv"
            self.assertTrue(keyenv.initialize(path))
            self.assertEqual(set(keyenv.read_keys(path)), set(keyenv.KEY_NAMES))
            self.assertTrue(all(not value for value in keyenv.read_keys(path).values()))
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            content = path.read_text(encoding="utf-8").replace(
                "DEEPSEEK_API_KEY=", "DEEPSEEK_API_KEY=fixture-secret"
            )
            path.write_text(content, encoding="utf-8")
            self.assertFalse(keyenv.initialize(path))
            self.assertEqual(keyenv.read_keys(path)["DEEPSEEK_API_KEY"], "fixture-secret")

    def test_keyenv_is_plain_data_and_rejects_ambiguous_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "keyenv"
            for invalid in (
                "export DEEPSEEK_API_KEY=fixture-secret\n",
                "DEEPSEEK_API_KEY=one\nDEEPSEEK_API_KEY=two\n",
                "OTHER_SECRET=fixture-secret\n",
            ):
                with self.subTest(invalid=invalid.split("=")[0]):
                    path.write_text(invalid, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        keyenv.read_keys(path)

    def test_run_passes_only_selected_known_key_and_never_prints_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "keyenv"
            path.write_text(
                "DEEPSEEK_API_KEY=fixture-deepseek\n"
                "MOONSHOT_API_KEY=fixture-moonshot\n",
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch.dict(os.environ, {"MOONSHOT_API_KEY": "ambient-moonshot"}), \
                    patch.object(keyenv.subprocess, "run") as child, \
                    contextlib.redirect_stdout(output):
                child.return_value.returncode = 0
                self.assertEqual(keyenv.run(["python", "app.py"], ["DEEPSEEK_API_KEY"], path), 0)
            passed = child.call_args.kwargs["env"]
            self.assertEqual(passed["DEEPSEEK_API_KEY"], "fixture-deepseek")
            self.assertNotIn("MOONSHOT_API_KEY", passed)
            self.assertEqual(child.call_args.args[0], ["python", "app.py"])
            self.assertEqual(output.getvalue(), "")

    def test_existing_selected_environment_key_wins(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "keyenv"
            path.write_text("DEEPSEEK_API_KEY=stored\n", encoding="utf-8")
            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "ambient"}), \
                    patch.object(keyenv.subprocess, "run") as child:
                child.return_value.returncode = 0
                keyenv.run(["python", "app.py"], ["DEEPSEEK_API_KEY"], path)
            self.assertEqual(child.call_args.kwargs["env"]["DEEPSEEK_API_KEY"], "ambient")


if __name__ == "__main__":
    unittest.main()
