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
            if check["live"] == "not_run":
                self.assertFalse(check.get("report"))
                continue
            report = json.loads((ROOT / check["report"]).read_text(encoding="utf-8"))
            matching = [result for result in report["results"] if result["path"] == f"models/zhipu/glm-4.7/examples/{example['file']}"]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0]["model_id"], "glm-4.7")

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
                if card.get("verification") is None:
                    self.assertEqual(self.card_scope(card), "not_run")
                    self.assertFalse(any(capability["status"] == "verified" for capability in card["capabilities"].values()))
                    self.assertFalse(card.get("historical_verification"), "未实测型号不能继承其他型号的旧报告")
                    continue
                verification_path = (MODEL_CARDS / card["verification"]).resolve()
                self.assertTrue(verification_path.is_file())
                result = json.loads(verification_path.read_text(encoding="utf-8"))
                self.assertEqual(result["model_id"], card["model_id"])
                self.assertFalse(result["privacy"]["api_key_saved"])
                self.assertFalse(result["privacy"]["response_content_saved"])
                if result["schema_version"] >= 2:
                    self.assertEqual(self.card_scope(card), "strict_workflow")
                    self.assertFalse(any(result["privacy"].values()))
                    self.assertFalse(result["source_git_dirty"])
                    self.assertRegex(result["source_git_commit"], r"^[0-9a-f]{40}$")
                    self.assertRegex(result["source_git_diff_sha256"], r"^[0-9a-f]{64}$")
                    for test in result["results"]:
                        self.assertIn(test["status"], {"passed", "failed", "rate_limited", "skipped"})
                        if test["status"] != "passed":
                            continue
                        self.assertTrue(test["requests"])
                        for request in test["requests"]:
                            self.assertTrue(request["response_received"])
                            self.assertIn(request["response"]["finish_reason"], {"stop", "tool_calls"})
                        final = test["requests"][-1]["response"]
                        self.assertEqual(final["finish_reason"], "stop")
                        self.assertGreater(final["content_chars"], 0)
                        if test["id"] == "streaming":
                            self.assertTrue(final["stream_completed"])
                        if test["id"] == "tool_calling":
                            self.assertGreaterEqual(len(test["requests"]), 2)
                            self.assertTrue(test["requests"][0]["response"]["tool_arguments_validated"])

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
