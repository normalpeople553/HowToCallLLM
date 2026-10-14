"""不发请求的证据、派生摘要和报告统计一致性检查。"""

import importlib.util
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SYNC_PATH = ROOT / "skills/model-manual/scripts/sync_verification.py"
spec = importlib.util.spec_from_file_location("sync_verification", SYNC_PATH)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class CatalogSyncTests(unittest.TestCase):
    def test_generated_catalog_and_status_page_are_current(self):
        for path, expected in sync.all_expected_outputs().items():
            with self.subTest(path=str(path)):
                self.assertEqual(path.read_text(encoding="utf-8"), expected)

    def test_rate_limited_and_skipped_are_not_passed_or_failed(self):
        report = {"tests": {
            "first": {"status": "passed"},
            "second": {"status": "rate_limited"},
            "third": {"status": "skipped"},
        }}
        self.assertEqual(sync.counts(report), {"passed": 1, "failed": 0, "rate_limited": 1, "skipped": 1})

    def test_report_summary_agrees_with_test_results(self):
        for path in (ROOT / "models").glob("*/*/verification/*.json"):
            with self.subTest(path=str(path)):
                report = json.loads(path.read_text(encoding="utf-8"))
                actual = sync.counts(report)
                for status, count in report.get("summary", report.get("counts", {})).items():
                    if status in actual:
                        self.assertEqual(count, actual[status])

    def test_verified_capability_has_matching_runtime_evidence(self):
        catalog = json.loads(sync.CATALOG.read_text(encoding="utf-8"))
        for vendor, cfg in catalog["vendors"].items():
            card = json.loads((sync.REFERENCES / cfg["model_card"]).read_text(encoding="utf-8"))
            self.assertEqual(card["vendor"], vendor)
            self.assertEqual(card["model_id"], cfg["default_model"])
            if cfg.get("verification") is None:
                self.assertIsNone(card.get("verification"))
                self.assertEqual(cfg["verification_scope"], "not_run")
                self.assertNotIn("verified", cfg["capabilities"].values())
                continue
            report = json.loads((ROOT / cfg["verification"]).read_text(encoding="utf-8"))
            observations = sync.report_tests(report)
            for capability, state in cfg["capabilities"].items():
                if state != "verified":
                    continue
                with self.subTest(vendor=vendor, capability=capability):
                    self.assertIn(capability, sync.TEST_IDS)
                    self.assertEqual(observations[sync.TEST_IDS[capability]]["status"], "passed")

    def fixture_without_verification(self, directory, *, omit_reference=False):
        root = Path(directory)
        references = root / "skills/model-manual/references"
        cards = references / "models"
        cards.mkdir(parents=True)
        catalog_path = references / "vendors.json"
        catalog_path.write_text(json.dumps({"vendors": {"minimax": {
            "default_model": "MiniMax-M2.7",
            "verification": "models/other/old-model/verification/old.json",
            "verification_scope": "strict_workflow",
            "capabilities": {"chat_completions": "verified", "thinking_off": "verified", "vision": "verified"},
        }}}), encoding="utf-8")
        card_path = cards / "MiniMax-M2.7.json"
        card = {
            "model_id": "MiniMax-M2.7", "vendor": "minimax",
            "verification": None, "verification_scope": "not_run",
            "generation": {"thinking": {"on": {"value": {"reasoning_split": True}}}},
            "capabilities": {
                "chat_completions": {"status": "documented"},
                "thinking": {"status": "documented"},
                "vision": {"status": "unsupported"},
                "not_confirmed": {"status": "unknown"},
            },
        }
        if omit_reference:
            del card["verification"]
        card_path.write_text(json.dumps(card), encoding="utf-8")
        return root, references, catalog_path, card_path

    def test_missing_and_null_report_are_not_run_without_reading_a_report(self):
        for omit_reference in (False, True):
            with self.subTest(omit_reference=omit_reference), tempfile.TemporaryDirectory() as directory:
                root, references, catalog_path, card_path = self.fixture_without_verification(directory, omit_reference=omit_reference)
                status_page = root / "docs/验证状态.md"
                reads = []
                original_read = Path.read_text

                def record_read(path, *args, **kwargs):
                    reads.append(path)
                    return original_read(path, *args, **kwargs)

                with patch.multiple(sync, ROOT=root, REFERENCES=references, CATALOG=catalog_path, STATUS_PAGE=status_page), patch.object(Path, "read_text", record_read):
                    outputs = sync.expected_outputs()
                self.assertEqual(set(reads), {catalog_path, card_path})
                cfg = json.loads(outputs[catalog_path])["vendors"]["minimax"]
                self.assertIsNone(cfg["verification"])
                self.assertEqual(cfg["verification_scope"], "not_run")
                self.assertNotIn("verified", cfg["capabilities"].values())
                self.assertEqual(cfg["capabilities"]["chat_completions"], "documented")
                self.assertEqual(cfg["capabilities"]["vision"], "unknown")
                self.assertEqual(cfg["capabilities"]["thinking_off"], "unknown")
                row = next(line for line in outputs[status_page].splitlines() if line.startswith("| [MiniMax-M2.7]"))
                columns = [column.strip() for column in row.strip("|").split("|")]
                self.assertEqual(columns[1:], ["—", "统一验证器未运行", "—", "—", "—", "—", "—", "报告空缺"])

    def test_explicit_broken_or_other_model_report_is_not_treated_as_not_run(self):
        for case in ("broken_path", "other_model", "unfounded_scope"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root, references, catalog_path, card_path = self.fixture_without_verification(directory)
                card = json.loads(card_path.read_text(encoding="utf-8"))
                if case == "unfounded_scope":
                    card["verification_scope"] = "strict_workflow"
                else:
                    card["verification"] = "unexpected-report.json"
                    if case == "other_model":
                        (card_path.parent / "unexpected-report.json").write_text(json.dumps({"model_id": "old-model", "tests": {}}), encoding="utf-8")
                card_path.write_text(json.dumps(card), encoding="utf-8")
                with patch.multiple(sync, ROOT=root, REFERENCES=references, CATALOG=catalog_path, STATUS_PAGE=root / "status.md"):
                    with self.assertRaises(ValueError):
                        sync.expected_outputs()

    def test_bilingual_outputs_use_one_catalog_and_relative_report_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root, references, catalog_path, card_path = self.fixture_without_verification(directory)
            card = json.loads(card_path.read_text(encoding="utf-8"))
            card.update(verification="fixture-report.json", verification_scope="strict_workflow")
            card_path.write_text(json.dumps(card), encoding="utf-8")
            report_path = card_path.parent / "fixture-report.json"
            report_path.write_text(json.dumps({
                "schema_version": 2, "model_id": "MiniMax-M2.7", "tested_at": "2026-10-14T01:00:00+00:00",
                "runtime": {"openai": "2.54.0"}, "results": [
                    {"id": "chat_completions", "status": "passed"},
                    {"id": "streaming", "status": "rate_limited"},
                    {"id": "thinking_enabled", "status": "skipped"},
                ],
            }), encoding="utf-8")
            status_page = root / "docs/验证状态.md"
            with patch.multiple(sync, ROOT=root, REFERENCES=references, CATALOG=catalog_path, STATUS_PAGE=status_page):
                chinese, english = sync.expected_outputs(), sync.expected_outputs(language="en")
                reads = []
                original_read = Path.read_text
                def record_read(path, *args, **kwargs):
                    reads.append(path.resolve())
                    return original_read(path, *args, **kwargs)
                with patch.object(Path, "read_text", record_read):
                    both = sync.all_expected_outputs()
                self.assertEqual(len(reads), len(set(reads)))
            english_page = root / "en/docs/verification-status.md"
            self.assertEqual(json.loads(chinese[catalog_path]), json.loads(english[catalog_path]))
            self.assertEqual(set(both), {catalog_path, status_page, english_page})
            self.assertTrue(all(path.is_relative_to(root) for path in both))
            zh_row = next(line for line in chinese[status_page].splitlines() if line.startswith("| [MiniMax-M2.7]"))
            en_row = next(line for line in english[english_page].splitlines() if line.startswith("| [MiniMax-M2.7]"))
            zh_columns = [value.strip() for value in zh_row.strip("|").split("|")]
            en_columns = [value.strip() for value in en_row.strip("|").split("|")]
            self.assertEqual(zh_columns[3:8], en_columns[3:8])
            self.assertEqual(en_columns[3:7], ["1", "0", "1", "1"])
            self.assertIn("../../" + report_path.relative_to(root).as_posix(), en_row)
            self.assertIn("README.en.md", en_row)
            self.assertIn("../en/docs/verification-status.md", chinese[status_page])
            self.assertIn("../../docs/验证状态.md", english[english_page])

    def test_bilingual_cli_is_fixture_isolated_and_detects_english_staleness(self):
        with tempfile.TemporaryDirectory() as directory:
            root, references, catalog_path, _ = self.fixture_without_verification(directory)
            status_page = root / "docs/验证状态.md"
            english_page = root / "en/docs/verification-status.md"
            with patch.multiple(sync, ROOT=root, REFERENCES=references, CATALOG=catalog_path, STATUS_PAGE=status_page), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sync.main([]), 0)
                self.assertTrue(status_page.is_file())
                self.assertTrue(english_page.is_file())
                original_chinese = status_page.read_text(encoding="utf-8")
                self.assertEqual(sync.main(["--check"]), 0)
                english_page.write_text("stale English", encoding="utf-8")
                self.assertEqual(sync.main(["--check"]), 1)
                self.assertEqual(status_page.read_text(encoding="utf-8"), original_chinese)
                self.assertEqual(sync.main([]), 0)
                self.assertEqual(sync.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
