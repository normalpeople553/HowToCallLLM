"""模型级机器卡片和示例的离线检查，不发送 API 请求。"""

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
MODEL_CARDS = ROOT / "skills" / "model-manual" / "references" / "models"
DEEPSEEK_EXAMPLES = ROOT / "models" / "deepseek" / "deepseek-flash" / "examples"


class ModelCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = json.loads(
            (MODEL_CARDS / "deepseek-flash.json").read_text(encoding="utf-8")
        )
        cls.sources = cls.card["sources"]

    def test_deepseek_identity(self):
        self.assertEqual(self.card["model_id"], "deepseek-flash")
        self.assertEqual(self.card["vendor"], "deepseek")
        self.assertEqual(
            self.card["identity"]["api_model_id"]["value"], "deepseek-flash"
        )

    def test_sources_are_official_and_reachable_by_reference(self):
        self.assertGreaterEqual(len(self.sources), 10)
        for source_id, source in self.sources.items():
            with self.subTest(source_id=source_id):
                self.assertTrue(source["title"])
                parsed = urlparse(source["url"])
                self.assertEqual(parsed.scheme, "https")
                self.assertEqual(parsed.hostname, "api-docs.deepseek.com")

    def test_every_fact_references_a_known_source(self):
        def visit(node, path="root"):
            if isinstance(node, dict):
                if "value" in node:
                    self.assertIn("source", node, path)
                    self.assertIn(node["source"], self.sources, path)
                if "status" in node:
                    self.assertIn("source", node, path)
                    self.assertIn(node["source"], self.sources, path)
                for key, value in node.items():
                    visit(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    visit(value, f"{path}[{index}]")

        visit(self.card)

    def test_python_examples_compile(self):
        paths = sorted(DEEPSEEK_EXAMPLES.glob("*.py"))
        self.assertGreaterEqual(len(paths), 6)
        for path in paths:
            with self.subTest(path=path.name):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_verification_record_matches_card(self):
        verification_path = (MODEL_CARDS / self.card["verification"]).resolve()
        self.assertTrue(verification_path.is_file())
        result = json.loads(verification_path.read_text(encoding="utf-8"))
        self.assertEqual(result["model_id"], self.card["model_id"])
        self.assertEqual(result["summary"], {"passed": 7, "failed": 0})
        self.assertFalse(result["privacy"]["api_key_saved"])
        self.assertFalse(result["privacy"]["response_content_saved"])

    def test_shell_example_uses_environment_key(self):
        source = (DEEPSEEK_EXAMPLES / "08_curl.sh").read_text(encoding="utf-8")
        self.assertIn("${DEEPSEEK_API_KEY}", source)
        self.assertNotIn("sk-", source)


if __name__ == "__main__":
    unittest.main()
