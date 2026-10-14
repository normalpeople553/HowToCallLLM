"""公开摘要只依赖官方来源；测试不读本地真实证据、密钥或厂商接口。"""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SYNC_PATH = ROOT / "skills/model-manual/scripts/sync_verification.py"
spec = importlib.util.spec_from_file_location("sync_verification", SYNC_PATH)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
OFFICIAL = "https://platform.minimax.cn/docs/api-reference/text-chat-openai"
PRIVATE_SENTINEL = "fixture-private-evidence-never-published"


class CatalogSyncTests(unittest.TestCase):
    def test_generated_catalog_and_status_page_are_current(self):
        for path, expected in sync.all_expected_outputs().items():
            with self.subTest(path=str(path)):
                self.assertEqual(path.read_text(encoding="utf-8"), expected)

    def fixture(self, directory, scope="private", *, omit_reference=False):
        root = Path(directory)
        references = root / "skills/model-manual/references"
        cards = references / "models"
        cards.mkdir(parents=True)
        catalog_path = references / "vendors.json"
        catalog_path.write_text(json.dumps({
            "selection_policy": {"default_billing": "paid"},
            "verified_at": PRIVATE_SENTINEL,
            "vendors": {"minimax": {
                "default_model": "MiniMax-M2.7",
                "verification": ".local/evidence/old-private.json",
                "verification_scope": "strict_workflow",
                "capabilities": {"chat_completions": "verified", "old_report_only": "verified"},
                "base_url": "https://api.minimax.cn/v1",
            }},
        }), encoding="utf-8")
        card_path = cards / "MiniMax-M2.7.json"
        card = {
            "model_id": "MiniMax-M2.7", "vendor": "minimax",
            "verification": None, "verification_scope": scope,
            "generation": {"thinking": {"on": {"value": {"reasoning_split": True}, "source": "api"}}},
            "capabilities": {
                "chat_completions": {"status": "verified", "source": "api"},
                "thinking": {"status": "documented", "source": "api"},
                "vision": {"status": "unsupported", "source": "api"},
                "not_confirmed": {"status": "unknown", "source": "api"},
                "local_only": {"status": "documented", "source": "local"},
            },
            "sources": {"api": {"url": OFFICIAL}, "local": {"url": "../../../../docs/policy.md"}},
        }
        if omit_reference:
            del card["verification"]
        card_path.write_text(json.dumps(card), encoding="utf-8")
        return root, references, catalog_path, card_path

    def settings(self, root, references, catalog_path):
        return patch.multiple(sync, ROOT=root, REFERENCES=references, CATALOG=catalog_path,
                              STATUS_PAGE=root / "docs/验证状态.md")

    def test_public_capabilities_use_only_official_sources_and_never_private_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root, references, catalog_path, _ = self.fixture(directory)
            with self.settings(root, references, catalog_path):
                outputs = sync.all_expected_outputs()
            catalog = json.loads(outputs[catalog_path])
            self.assertNotIn("verified_at", catalog)
            self.assertEqual(catalog["selection_policy"], {"default_billing": "paid"})
            cfg = catalog["vendors"]["minimax"]
            self.assertIsNone(cfg["verification"])
            self.assertEqual(cfg["verification_scope"], "private")
            self.assertEqual(cfg["capabilities"], {
                "chat_completions": "documented", "thinking": "documented",
                "vision": "unknown", "not_confirmed": "unknown",
                "local_only": "unknown", "thinking_off": "unknown",
            })
            self.assertNotIn("verified", cfg["capabilities"].values())
            self.assertEqual(cfg["base_url"], "https://api.minimax.cn/v1")

    def test_private_and_not_run_remain_distinct_without_reading_any_report(self):
        for scope in ("private", "not_run"):
            for omit_reference in (False, True):
                with self.subTest(scope=scope, omit_reference=omit_reference), tempfile.TemporaryDirectory() as directory:
                    root, references, catalog_path, card_path = self.fixture(directory, scope, omit_reference=omit_reference)
                    reads = []
                    original_read = Path.read_text

                    def public_only(path, *args, **kwargs):
                        self.assertIn(path, {catalog_path, card_path})
                        reads.append(path)
                        return original_read(path, *args, **kwargs)

                    with self.settings(root, references, catalog_path), patch.object(Path, "read_text", public_only):
                        outputs = sync.all_expected_outputs()
                    self.assertEqual(set(reads), {catalog_path, card_path})
                    self.assertEqual(len(reads), 2)
                    cfg = json.loads(outputs[catalog_path])["vendors"]["minimax"]
                    self.assertIsNone(cfg["verification"])
                    self.assertEqual(cfg["verification_scope"], scope)
                    page = outputs[root / "docs/验证状态.md"]
                    expected = "本地记录不公开" if scope == "private" else "统一流程未运行"
                    self.assertIn(expected, page)
                    rows = [line for line in page.splitlines() if line.startswith("|")]
                    self.assertTrue(all(len(line.strip("|").split("|")) == 3 for line in rows))

    def test_public_bindings_or_old_workflow_scopes_fail_before_reading_a_report(self):
        for case in ("report_binding", "legacy_scope", "strict_scope", "unknown_scope"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root, references, catalog_path, card_path = self.fixture(directory)
                card = json.loads(card_path.read_text(encoding="utf-8"))
                if case == "report_binding":
                    card["verification"] = ".local/evidence/private.json"
                else:
                    card["verification_scope"] = {"legacy_scope": "legacy_smoke", "strict_scope": "strict_workflow", "unknown_scope": "made_up"}[case]
                card_path.write_text(json.dumps(card), encoding="utf-8")
                original_read = Path.read_text

                def public_only(path, *args, **kwargs):
                    self.assertIn(path, {catalog_path, card_path})
                    return original_read(path, *args, **kwargs)

                with self.settings(root, references, catalog_path), patch.object(Path, "read_text", public_only):
                    with self.assertRaises(ValueError):
                        sync.all_expected_outputs()

    def test_local_records_do_not_affect_public_generation_and_clone_needs_no_evidence(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as cloned:
            root, references, catalog_path, _ = self.fixture(directory)
            with self.settings(root, references, catalog_path):
                before = sync.all_expected_outputs()
            private_file = root / ".local/evidence/fixture.json"
            private_file.parent.mkdir(parents=True)
            private_file.write_text(json.dumps({
                "evidence_id": PRIVATE_SENTINEL, "runtime": {"openai": PRIVATE_SENTINEL},
                "counts": {"passed": 999}, "source_sha256": PRIVATE_SENTINEL,
                "results": [{"status": "passed", "model_id": "MiniMax-M2.7"}],
            }), encoding="utf-8")
            original_read = Path.read_text

            def no_private_reads(path, *args, **kwargs):
                self.assertNotIn(".local", path.parts)
                return original_read(path, *args, **kwargs)

            with self.settings(root, references, catalog_path), patch.object(Path, "read_text", no_private_reads):
                self.assertEqual(before, sync.all_expected_outputs())
            clone = Path(cloned)
            clone_references = clone / "skills/model-manual/references"
            shutil.copytree(references, clone_references)
            clone_catalog = clone_references / "vendors.json"
            self.assertFalse((clone / ".local").exists())
            with self.settings(clone, clone_references, clone_catalog), patch.object(Path, "read_text", no_private_reads), contextlib.redirect_stdout(io.StringIO()):
                after = sync.all_expected_outputs()
                self.assertEqual({path.relative_to(root): value for path, value in before.items()},
                                 {path.relative_to(clone): value for path, value in after.items()})
                self.assertEqual(sync.main([]), 0)
                self.assertEqual(sync.main(["--check"]), 0)
            self.assertFalse((clone / ".local").exists())

    def test_bilingual_pages_only_publish_public_navigation_and_official_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root, references, catalog_path, _ = self.fixture(directory)
            with self.settings(root, references, catalog_path):
                outputs = sync.all_expected_outputs()
            chinese = outputs[root / "docs/验证状态.md"]
            english = outputs[root / "en/docs/verification-status.md"]
            self.assertEqual(set(outputs), {catalog_path, root / "docs/验证状态.md", root / "en/docs/verification-status.md"})
            for page in (chinese, english):
                self.assertIn(OFFICIAL, page)
                self.assertNotIn(PRIVATE_SENTINEL, page)
                for private_field in ("evidence_id", "source_sha256", "tested_at", "duration_seconds", "2.54.0", "999", ".local/"):
                    self.assertNotIn(private_field, page)
                self.assertNotIn("[JSON]", page)
                self.assertNotIn("| SDK |", page)
                self.assertNotIn("| Passed |", page)
            self.assertIn("README.en.md", english)
            self.assertIn("../../tests/provider_verify.py", english)
            self.assertIn("../tests/provider_verify.py", chinese)
            self.assertIn("../en/docs/verification-status.md", chinese)
            self.assertIn("../../docs/验证状态.md", english)

    def test_official_source_missing_cross_vendor_or_untrusted_does_not_become_documented(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, _, card_path = self.fixture(directory)
            card = json.loads(card_path.read_text(encoding="utf-8"))
            for url in ("../../../../.local/evidence/private.json", "https://api-docs.deepseek.com/", "http://platform.minimax.cn/docs", "https://user:secret@platform.minimax.cn/docs"):
                with self.subTest(url=url):
                    card["sources"]["api"]["url"] = url
                    self.assertEqual(sync.documented_capabilities(card)["chat_completions"], "unknown")
            card["sources"].pop("api")
            self.assertEqual(sync.documented_capabilities(card)["chat_completions"], "unknown")

    def test_official_qualified_support_states_remain_documented_not_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, _, card_path = self.fixture(directory)
            card = json.loads(card_path.read_text(encoding="utf-8"))
            for state in ("beta_documented", "automatic", "non_thinking_only"):
                with self.subTest(state=state):
                    card["capabilities"]["chat_completions"]["status"] = state
                    self.assertEqual(sync.documented_capabilities(card)["chat_completions"], "documented")
            card["capabilities"]["chat_completions"]["status"] = "made_up_passed"
            self.assertEqual(sync.documented_capabilities(card)["chat_completions"], "unknown")

    def test_bilingual_cli_is_fixture_isolated_and_detects_english_staleness(self):
        with tempfile.TemporaryDirectory() as directory:
            root, references, catalog_path, _ = self.fixture(directory)
            status_page = root / "docs/验证状态.md"
            english_page = root / "en/docs/verification-status.md"
            with self.settings(root, references, catalog_path), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sync.main([]), 0)
                self.assertEqual(sync.main(["--check"]), 0)
                original_chinese = status_page.read_text(encoding="utf-8")
                english_page.write_text("stale English", encoding="utf-8")
                self.assertEqual(sync.main(["--check"]), 1)
                self.assertEqual(status_page.read_text(encoding="utf-8"), original_chinese)
                self.assertEqual(sync.main([]), 0)
                self.assertEqual(sync.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
