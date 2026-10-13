"""不发请求的证据、派生摘要和报告统计一致性检查。"""

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC_PATH = ROOT / "skills/model-manual/scripts/sync_verification.py"
spec = importlib.util.spec_from_file_location("sync_verification", SYNC_PATH)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class CatalogSyncTests(unittest.TestCase):
    def test_generated_catalog_and_status_page_are_current(self):
        for path, expected in sync.expected_outputs().items():
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
            report = json.loads((ROOT / cfg["verification"]).read_text(encoding="utf-8"))
            self.assertEqual(card["vendor"], vendor)
            self.assertEqual(card["model_id"], cfg["default_model"])
            observations = sync.report_tests(report)
            for capability, state in cfg["capabilities"].items():
                if state != "verified":
                    continue
                with self.subTest(vendor=vendor, capability=capability):
                    self.assertIn(capability, sync.TEST_IDS)
                    self.assertEqual(observations[sync.TEST_IDS[capability]]["status"], "passed")


if __name__ == "__main__":
    unittest.main()
