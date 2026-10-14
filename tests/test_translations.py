"""Bilingual routing, source revisions and shared executable evidence; no API calls."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("translation_checks", ROOT / "scripts/check_translations.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class TranslationChecksTests(unittest.TestCase):
    def fixture(self, root):
        (root / "en").mkdir()
        source, target = root / "parameters.md", root / "parameters.en.md"
        text = "# Parameters\n[Official](https://example.org/api)\n[Example](examples/01_basic.py)\n"
        source.write_text(text, encoding="utf-8")
        target.write_text(text, encoding="utf-8")
        data = {"schema_version": 1, "languages": ["zh-CN", "en"], "translations": [{
            "source": source.name, "target": target.name,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }], "generated": []}
        (root / checker.MANIFEST).write_text(json.dumps(data), encoding="utf-8")
        return source, target, data

    def test_matching_reviewed_pair_is_valid_without_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            self.assertEqual(checker.check(root), {"static_pairs": 1, "generated_pairs": 0, "issues": []})

    def test_source_change_requires_review_not_silent_hash_refresh(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, _, _ = self.fixture(root)
            source.write_text(source.read_text() + "Changed official limit.\n", encoding="utf-8")
            self.assertEqual(checker.check(root)["issues"][0]["code"], "source_changed_review_translation")

    def test_translation_cannot_drop_official_citations_or_executable_mapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, target, _ = self.fixture(root)
            target.write_text("# Translation with omitted details\n", encoding="utf-8")
            self.assertEqual({item["code"] for item in checker.check(root)["issues"]}, {
                "official_or_external_citation_mismatch", "executable_reference_mismatch",
            })

    def test_duplicate_and_outside_repository_paths_are_rejected(self):
        for case in ("duplicate", "outside"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                _, _, data = self.fixture(root)
                if case == "duplicate":
                    data["translations"].append(data["translations"][0])
                else:
                    data["translations"][0]["target"] = "../private.md"
                (root / checker.MANIFEST).write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
                    checker.check(root)

    def test_generated_pairs_use_shared_generators_not_translation_fingerprints(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, _, data = self.fixture(root)
            for name in ("status.md", "status.en.md", "generate.py"):
                (root / name).write_text("generated\n", encoding="utf-8")
            data["generated"] = [{"source": "status.md", "target": "status.en.md", "generator": "generate.py"}]
            (root / checker.MANIFEST).write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(checker.check(root)["generated_pairs"], 1)


class RepositoryEditionTests(unittest.TestCase):
    def test_all_maintained_reading_pages_have_a_translation_pair(self):
        data = json.loads((ROOT / checker.MANIFEST).read_text(encoding="utf-8"))
        actual = {entry["source"] for kind in ("translations", "generated") for entry in data[kind]}
        expected = {
            "README.md", "human/README.md", "agents/README.md", "models/README.md",
            "skills/model-manual/SKILL.md", "skills/model-manual/references/workflows.md",
            "verification/README.md",
        }
        expected.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "docs").rglob("*.md"))
        expected.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "human").rglob("*.md")
                        if not path.name.endswith(".en.md"))
        for pattern in ("*/*/README.md", "*/*/parameters.md"):
            expected.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "models").glob(pattern))
        self.assertEqual(actual, expected)
        self.assertEqual(checker.check(ROOT)["issues"], [])

    def test_both_books_route_to_canonical_model_cards_and_shared_code(self):
        for relative in ("human/README.md", "human/README.en.md", "agents/README.md", "agents/README.en.md"):
            self.assertTrue((ROOT / relative).is_file(), relative)
        # No translated executable tree, model-card copy or report copy is created.
        self.assertFalse((ROOT / "en/models").exists())
        self.assertFalse((ROOT / "en/verification").exists())
        self.assertEqual(list((ROOT / "en").rglob("*.py")), [])
        self.assertEqual(list((ROOT / "en").rglob("*.ts")), [])
        self.assertEqual(list((ROOT / "en").rglob("*.sh")), [])
        refs = ROOT / "skills/model-manual/references"
        vendors = json.loads((refs / "vendors.json").read_text(encoding="utf-8"))["vendors"]
        for vendor, config in vendors.items():
            card_path = refs / "models" / f"{config['default_model']}.json"
            card = json.loads(card_path.read_text(encoding="utf-8"))
            self.assertEqual(card["vendor"], vendor)
            self.assertEqual(card["model_id"], config["default_model"])
            folder = ROOT / "models" / card["vendor"] / card["model_id"]
            for name in ("README.md", "README.en.md", "parameters.md", "parameters.en.md"):
                self.assertTrue((folder / name).is_file())


if __name__ == "__main__":
    unittest.main()
