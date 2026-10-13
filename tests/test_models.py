"""全部模型级机器卡片和示例的离线检查，不发送 API 请求。"""

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
MODEL_CARDS = ROOT / "skills" / "model-manual" / "references" / "models"
OFFICIAL_HOSTS = {
    "deepseek": {"api-docs.deepseek.com"},
    "kimi": {"platform.kimi.com"},
    "zhipu": {"docs.bigmodel.cn"},
    "qwen": {"help.aliyun.com"},
    "doubao": {"docs.volcengine.com"},
}


class ModelCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(MODEL_CARDS.glob("*.json"))]

    def test_expected_models_exist(self):
        self.assertEqual({c["model_id"] for c in self.cards}, {"deepseek-flash", "kimi-k2.6", "glm-4.7-flash", "qwen-flash", "doubao-seed-2-1-pro-260628"})

    def test_sources_are_official_and_reachable_by_reference(self):
        for card in self.cards:
            for source_id, source in card["sources"].items():
                with self.subTest(model=card["model_id"], source_id=source_id):
                    self.assertTrue(source["title"])
                    if source["url"].startswith("http"):
                        parsed = urlparse(source["url"])
                        self.assertEqual(parsed.scheme, "https")
                        self.assertIn(parsed.hostname, OFFICIAL_HOSTS[card["vendor"]])

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

        for card in self.cards:
            self.card = card
            self.sources = card["sources"]
            visit(card)

    def test_python_examples_compile(self):
        paths = sorted((ROOT / "models").glob("*/*/examples/*.py"))
        self.assertGreaterEqual(len(paths), 26)
        for path in paths:
            with self.subTest(path=path.name):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_verification_record_matches_card(self):
        for card in self.cards:
            verification_path = (MODEL_CARDS / card["verification"]).resolve()
            with self.subTest(model=card["model_id"]):
                self.assertTrue(verification_path.is_file())
                result = json.loads(verification_path.read_text(encoding="utf-8"))
                self.assertEqual(result["model_id"], card["model_id"])
                self.assertFalse(result["privacy"]["api_key_saved"])
                self.assertFalse(result["privacy"]["response_content_saved"])

    def test_shell_example_uses_environment_key(self):
        source = (ROOT / "models/deepseek/deepseek-flash/examples/08_curl.sh").read_text(encoding="utf-8")
        self.assertIn("${DEEPSEEK_API_KEY}", source)
        self.assertNotIn("sk-", source)

    def test_every_model_manual_links_the_pitfall_guide(self):
        manuals = sorted((ROOT / "models").glob("*/*/README.md"))
        self.assertEqual(len(manuals), 5)
        for manual in manuals:
            with self.subTest(manual=str(manual)):
                self.assertIn("06-真实踩雷与生产检查.md", manual.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
