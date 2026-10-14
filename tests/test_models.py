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
    "minimax": {"platform.minimax.io", "platform.minimax.cn", "platform.minimaxi.com"},
}
EXPECTED_MODELS = {
    "deepseek-flash", "kimi-k2.6", "glm-4.7", "qwen-flash",
    "doubao-seed-2-1-pro-260628", "MiniMax-M2.7",
}


class ModelCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        vendors = json.loads((MODEL_CARDS.parent / "vendors.json").read_text(encoding="utf-8"))["vendors"]
        cls.cards = [json.loads((MODEL_CARDS / f"{cfg['default_model']}.json").read_text(encoding="utf-8")) for cfg in vendors.values()]

    def test_expected_models_exist(self):
        self.assertEqual({c["model_id"] for c in self.cards}, EXPECTED_MODELS)

    def test_all_maintained_default_models_have_official_paid_billing_evidence(self):
        self.assertEqual(len(self.cards), 6)
        for card in self.cards:
            with self.subTest(model=card["model_id"]):
                billing = card["billing"]["type"]
                self.assertEqual(billing["value"], "paid")
                source = card["sources"][billing["source"]]
                parsed = urlparse(source["url"])
                self.assertEqual(parsed.scheme, "https")
                self.assertIn(parsed.hostname, OFFICIAL_HOSTS[card["vendor"]])

    def test_paid_glm_4_7_does_not_inherit_flash_verification(self):
        card = next(card for card in self.cards if card["model_id"] == "glm-4.7")
        self.assertEqual(card["vendor"], "zhipu")
        self.assertNotIn("glm-4.7-flash", json.dumps(card.get("historical_verification", [])))
        if card.get("verification") is not None:
            report = json.loads((MODEL_CARDS / card["verification"]).resolve().read_text(encoding="utf-8"))
            self.assertEqual(report["model_id"], "glm-4.7")
            self.assertNotIn("glm-4.7-flash", card["verification"])
        else:
            self.assertEqual(card.get("verification_scope"), "not_run")
            self.assertNotIn("verified", [capability["status"] for capability in card["capabilities"].values()])
        manifest = json.loads((ROOT / "models/zhipu/glm-4.7/examples/sources.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["model_id"], "glm-4.7")
        for example in manifest["examples"]:
            check = example["verification"]
            self.assertIn(check["live"], {"private", "not_run"})
            self.assertFalse(check.get("report"))
            self.assertLessEqual(set(check), {"offline", "live", "note"})

    def test_sources_are_official_and_reachable_by_reference(self):
        for card in self.cards:
            for source_id, source in card["sources"].items():
                with self.subTest(model=card["model_id"], source_id=source_id):
                    self.assertTrue(source["title"])
                    if source["url"].startswith("http"):
                        parsed = urlparse(source["url"])
                        self.assertEqual(parsed.scheme, "https")
                        self.assertIn(parsed.hostname, OFFICIAL_HOSTS[card["vendor"]])
                    else:
                        self.assertTrue((MODEL_CARDS / source["url"]).resolve().is_file())

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
            with self.subTest(model=card["model_id"]):
                self.assertIsNone(card.get("verification"))
                self.assertIn(self.card_scope(card), {"private", "not_run"})
                self.assertFalse(card.get("historical_verification"))
                self.assertFalse(any(capability["status"] == "verified" for capability in card["capabilities"].values()))

    @staticmethod
    def card_scope(card):
        return card.get("verification_scope")

    def test_shell_example_uses_environment_key(self):
        source = (ROOT / "models/deepseek/deepseek-flash/examples/08_curl.sh").read_text(encoding="utf-8")
        self.assertIn("${DEEPSEEK_API_KEY}", source)
        self.assertNotIn("sk-", source)

    def test_every_model_manual_links_the_pitfall_guide(self):
        manuals = [ROOT / "models" / card["vendor"] / card["model_id"] / "README.md" for card in self.cards]
        self.assertEqual({manual.parent.name for manual in manuals}, EXPECTED_MODELS)
        for manual in manuals:
            with self.subTest(manual=str(manual)):
                self.assertIn("06-真实踩雷与生产检查.md", manual.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
