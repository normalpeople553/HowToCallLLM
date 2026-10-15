"""Offline integrity checks; real API execution is kept private."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models/doubao/verified_calls.py"
spec = importlib.util.spec_from_file_location("doubao_verified_calls", SOURCE)
calls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calls)


class DoubaoVerifiedCallsTests(unittest.TestCase):
    def test_exact_choices_are_in_official_inventory_and_bilingual_pages(self):
        listed = {row["model_id"] for row in json.loads((ROOT / "data/model-lists/doubao.json").read_text(encoding="utf-8"))["models"]}
        tested = {*calls.CHAT_MODELS, calls.TRANSLATION_MODEL}
        self.assertEqual(len(tested), 12)
        self.assertTrue(tested <= listed)
        self.assertFalse({"doubao-seed-2-0-pro-260215", "doubao-seed-2-0-mini-260215"} & tested)
        for page in (ROOT / "docs/豆包已验证调用.md", ROOT / "en/docs/verified-doubao.md"):
            content = page.read_text(encoding="utf-8")
            for model in tested:
                self.assertIn(f"`{model}`", content)

    def test_chat_checks_completion_and_omits_thinking_for_old_character(self):
        response = SimpleNamespace(choices=[SimpleNamespace(
            finish_reason="stop", message=SimpleNamespace(content="收到。", tool_calls=None)
        )])
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=Mock(return_value=response))))
        self.assertEqual(calls.complete_chat(client, "doubao-seed-character-251128"), "收到。")
        self.assertNotIn("extra_body", client.chat.completions.create.call_args.kwargs)
        calls.complete_chat(client, "doubao-seed-2-1-pro-260915")
        self.assertEqual(client.chat.completions.create.call_args.kwargs["extra_body"], {"thinking": {"type": "disabled"}})
        response.choices[0].finish_reason = "length"
        with self.assertRaises(RuntimeError):
            calls.complete_chat(client, "doubao-seed-2-1-pro-260915")

    def test_translation_uses_responses_with_target_language(self):
        response = SimpleNamespace(status="completed", output_text="Hello")
        client = SimpleNamespace(responses=SimpleNamespace(create=Mock(return_value=response)))
        self.assertEqual(calls.complete_translation(client), "Hello")
        request = client.responses.create.call_args.kwargs
        self.assertEqual(request["model"], calls.TRANSLATION_MODEL)
        item = request["input"][0]["content"][0]
        self.assertEqual(item["type"], "input_text")
        self.assertEqual(item["translation_options"], {"source_language": "zh", "target_language": "en"})
        response.status = "incomplete"
        with self.assertRaises(RuntimeError):
            calls.complete_translation(client)


if __name__ == "__main__":
    unittest.main()
