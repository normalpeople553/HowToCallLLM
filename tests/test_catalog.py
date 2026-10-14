"""不发送网络请求的目录与代码生成器检查。"""

import importlib.util
import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "skills" / "model-manual" / "references" / "vendors.json"
GENERATOR = ROOT / "skills" / "model-manual" / "scripts" / "generate_snippet.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_snippet", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.vendors = cls.data["vendors"]
        cls.generator = load_generator()

    def test_expected_vendors_exist(self):
        self.assertEqual(
            set(self.vendors),
            {"deepseek", "kimi", "zhipu", "qwen", "doubao", "minimax"},
        )

    def test_required_fields_and_capability_states(self):
        allowed_states = {"verified", "documented", "unknown"}
        for vendor, cfg in self.vendors.items():
            with self.subTest(vendor=vendor):
                for field in ("name", "key_env", "key_url", "base_url", "default_model"):
                    self.assertTrue(cfg.get(field), f"{vendor} 缺少 {field}")
                self.assertTrue(cfg["base_url"].startswith("https://"))
                self.assertTrue(cfg["key_env"].endswith("API_KEY"))
                self.assertTrue(set(cfg["capabilities"].values()) <= allowed_states)

    def test_every_vendor_fact_has_official_sources(self):
        official_hosts = {
            "api-docs.deepseek.com",
            "platform.kimi.com",
            "docs.bigmodel.cn",
            "help.aliyun.com",
            "docs.volcengine.com",
            "platform.minimax.cn",
            "platform.minimax.io",
            "platform.minimaxi.com",
        }
        for vendor, cfg in self.vendors.items():
            with self.subTest(vendor=vendor):
                self.assertGreaterEqual(len(cfg.get("sources", {})), 3)
                for label, url in cfg["sources"].items():
                    self.assertEqual(urlparse(url).scheme, "https", label)
                    self.assertIn(urlparse(url).hostname, official_hosts, url)
                for note in cfg.get("notes", []):
                    self.assertIsInstance(note, dict)
                    self.assertTrue(note.get("text"))
                    self.assertIn(urlparse(note.get("source", "")).hostname, official_hosts)

    def test_generated_python_compiles(self):
        for vendor, cfg in self.vendors.items():
            with self.subTest(vendor=vendor):
                source = self.generator.python_snippet(
                    cfg,
                    cfg["default_model"],
                    "你好",
                    stream=True,
                    thinking="off" if "off" in self.generator.load_model(cfg["default_model"])["generation"]["thinking"] else "default",
                )
                compile(source, f"<{vendor}>", "exec")

    def test_vendor_default_resolves_to_its_model_card(self):
        for vendor, cfg in self.vendors.items():
            with self.subTest(vendor=vendor):
                card = self.generator.load_model(cfg["default_model"], vendor)
                self.assertEqual(card["vendor"], vendor)
                self.assertEqual(card["generation"]["key_env"]["value"], cfg["key_env"])
                self.assertEqual(card["generation"]["base_url"]["value"].rstrip("/"), cfg["base_url"].rstrip("/"))


if __name__ == "__main__":
    unittest.main()
