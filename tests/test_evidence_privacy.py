"""Offline privacy checks for public evidence; never read credentials or call APIs."""

import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch
from uuid import RFC_4122, UUID


ROOT = Path(__file__).resolve().parents[1]
TIME_KEYS = {"tested_at", "duration_seconds", "legacy_tested_at", "sort_time"}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvidencePrivacyTests(unittest.TestCase):
    def assert_untimed(self, value):
        if isinstance(value, dict):
            self.assertFalse(TIME_KEYS.intersection(value), "execution time leaked into public evidence")
            for nested in value.values():
                self.assert_untimed(nested)
        elif isinstance(value, list):
            for nested in value:
                self.assert_untimed(nested)

    def test_all_public_reports_have_unique_opaque_ids_and_no_execution_time(self):
        files = list((ROOT / "verification/examples").glob("*.json"))
        files += list((ROOT / "models").glob("*/*/verification/*.json"))
        self.assertTrue(files)
        identities = set()
        for path in files:
            with self.subTest(report=path.relative_to(ROOT).as_posix()):
                report = json.loads(path.read_text(encoding="utf-8"))
                self.assert_untimed(report)
                identity = UUID(report["evidence_id"])
                self.assertEqual(identity.version, 4)
                self.assertEqual(identity.variant, RFC_4122)
                self.assertEqual(str(identity), report["evidence_id"])
                self.assertNotIn(str(identity), identities)
                identities.add(str(identity))
                self.assertIs(report["privacy"]["test_timestamps_saved"], False)
                self.assertIs(report["privacy"]["duration_saved"], False)
                if report.get("kind") == "example_file_execution":
                    self.assertEqual(report["schema_version"], 2)
                else:
                    self.assertIn(report["schema_version"], {1, 3})

    def test_legacy_unified_evidence_is_not_promoted_by_privacy_redaction(self):
        legacy = list((ROOT / "models").glob("*/*/verification/2026-10-13.json"))
        self.assertTrue(legacy)
        for path in legacy:
            with self.subTest(report=path.relative_to(ROOT).as_posix()):
                report = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(report["schema_version"], 1)
                self.assert_untimed(report)

    def test_public_catalog_and_release_views_are_untimed_and_read_only(self):
        catalog = load_module("privacy_example_catalog", ROOT / "skills/model-manual/scripts/example_catalog.py")
        release = load_module("privacy_example_release", ROOT / "tests/check_example_release.py")
        renderer = load_module("privacy_human_renderer", ROOT / "scripts/render_human_examples.py")
        with patch("subprocess.Popen", side_effect=AssertionError("must not execute examples")), \
                patch("socket.socket.connect", side_effect=AssertionError("must not call APIs")), \
                patch("os.environ", {}):
            examples = catalog.select_examples(catalog.load_catalogs(ROOT))
            state = release.collect_release(ROOT)
            views = renderer.build_views(ROOT)
        self.assertTrue(examples)
        self.assertTrue(state["ready"])
        self.assertEqual(state["counts"]["passed"], state["total"])
        for value in (examples, state, views):
            self.assert_untimed(value)

    def test_generated_evidence_pages_do_not_show_execution_timestamps_or_durations(self):
        pages = [ROOT / "docs" / name for name in ("官方示例索引.md", "示例实测状态.md", "验证状态.md")]
        pages += [ROOT / "en/docs" / name for name in ("example-index.md", "example-status.md", "verification-status.md")]
        pages += list((ROOT / "human/examples").glob("*.md"))
        for path in pages:
            with self.subTest(page=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text))
                self.assertNotIn("tested_at", text)
                self.assertNotIn("duration_seconds", text)
                self.assertNotIn("| 时间 / 报告 / 证据 |", text)
                self.assertNotIn("| Time / report / evidence |", text)

    def test_official_source_check_dates_remain_separate_from_execution_evidence(self):
        cards = list((ROOT / "skills/model-manual/references/models").glob("*.json"))
        self.assertTrue(cards)
        for path in cards:
            with self.subTest(card=path.name):
                card = json.loads(path.read_text(encoding="utf-8"))
                self.assertRegex(card["last_checked_at"], r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
