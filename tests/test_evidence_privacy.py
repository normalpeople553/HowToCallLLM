"""Public artifacts must be usable without publishing private execution records."""

import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_KEYS = {
    "tested_at", "duration_seconds", "legacy_tested_at", "sort_time",
    "evidence_id", "source_sha256", "source_git_commit", "source_git_diff_sha256",
    "requests", "usage", "live_passed_files", "evidence_status",
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvidencePrivacyTests(unittest.TestCase):
    def assert_public(self, value):
        if isinstance(value, dict):
            self.assertFalse(PRIVATE_KEYS.intersection(value), "private execution material in public view")
            for nested in value.values():
                self.assert_public(nested)
        elif isinstance(value, list):
            for nested in value:
                self.assert_public(nested)

    def test_real_execution_reports_are_absent_from_public_directories(self):
        self.assertEqual(list((ROOT / "verification/examples").glob("*.json")), [])
        self.assertEqual(list((ROOT / "models").glob("*/*/verification/*.json")), [])
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for pattern in (".local/", "verification/**/*.json", "models/*/*/verification/*.json"):
            self.assertIn(pattern, ignore)

    def test_public_cards_and_manifests_do_not_publish_report_bindings(self):
        cards = list((ROOT / "skills/model-manual/references/models").glob("*.json"))
        self.assertTrue(cards)
        for path in cards:
            with self.subTest(card=path.name):
                card = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsNone(card["verification"])
                self.assertIn(card["verification_scope"], {"private", "not_run"})
                self.assertFalse(card.get("historical_verification"))
                self.assertNotIn("verified", {cap["status"] for cap in card["capabilities"].values()})
                self.assert_public(card)
        for path in (ROOT / "models").glob("*/*/examples/sources.json"):
            for example in json.loads(path.read_text(encoding="utf-8"))["examples"]:
                check = example["verification"]
                self.assertIn(check["live"], {"private", "not_run"})
                self.assertLessEqual(set(check), {"offline", "live", "note"})

    def test_public_queries_and_renderers_do_not_read_local_records_or_hash_execution_source(self):
        catalog = load_module("privacy_public_catalog", ROOT / "skills/model-manual/scripts/example_catalog.py")
        release = load_module("privacy_public_release", ROOT / "tests/check_example_release.py")
        renderer = load_module("privacy_public_human", ROOT / "scripts/render_human_examples.py")
        models = load_module("privacy_public_models", ROOT / "skills/model-manual/scripts/model_catalog.py")
        original_open = Path.open

        def public_open(path, *args, **kwargs):
            if ".local" in path.parts or path.name.startswith(".env"):
                raise AssertionError("private material must not be read")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", public_open), \
                patch("subprocess.Popen", side_effect=AssertionError("must not execute examples")), \
                patch("socket.socket.connect", side_effect=AssertionError("must not call APIs")), \
                patch.object(catalog, "file_identity", side_effect=AssertionError("must not hash execution source")):
            examples = catalog.select_examples(catalog.load_catalogs(ROOT))
            directory = release.collect_code_directory(ROOT)
            views = renderer.build_views(ROOT)
            model_pages = models.expected_pages(ROOT)
        self.assertTrue(examples)
        self.assertTrue(directory["rows"])
        self.assertTrue(model_pages)
        for value in (examples, directory, views):
            self.assert_public(value)

    def test_generated_pages_do_not_publish_private_records_or_execution_fingerprints(self):
        pages = [ROOT / "docs" / name for name in ("官方示例索引.md", "示例实测状态.md", "验证状态.md")]
        pages += [ROOT / "en/docs" / name for name in ("example-index.md", "example-status.md", "verification-status.md")]
        pages += list((ROOT / "human/examples").glob("*.md"))
        pages += list((ROOT / "docs/model-lists").glob("*.md"))
        pages += list((ROOT / "en/docs/model-lists").glob("*.md"))
        for path in pages:
            with self.subTest(page=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text))
                self.assertIsNone(re.search(r"\]\([^)]*verification/[^)]*\.json\)", text))
                self.assertIsNone(re.search(r"\b[0-9a-f]{64}\b", text))
                # 调用代码仍可处理 usage/requests；禁止的是实测产物，不是协议字段说明。
                for key in PRIVATE_KEYS - {"usage", "requests"}:
                    self.assertFalse(key in text, f"private field {key} in {path.name}")
                self.assertNotIn("完整 HTTP 通过", text)

    def test_official_document_check_dates_are_not_execution_dates(self):
        for path in (ROOT / "skills/model-manual/references/models").glob("*.json"):
            card = json.loads(path.read_text(encoding="utf-8"))
            self.assertRegex(card["last_checked_at"], r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
