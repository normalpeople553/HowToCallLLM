"""清单、官方来源、精确型号检索与生成索引的离线回归。"""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/model-manual/scripts/example_catalog.py"
spec = importlib.util.spec_from_file_location("example_catalog", SCRIPT)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)
EXPECTED_MODELS = {
    "deepseek-flash", "kimi-k2.6", "glm-4.7-flash", "qwen-flash",
    "doubao-seed-2-1-pro-260628", "MiniMax-M2.7",
}


class ExampleCatalogTests(unittest.TestCase):
    def test_every_model_and_runnable_file_is_cataloged(self):
        catalogs = catalog.load_catalogs()
        directories = {path.parent for path in (ROOT / "models").glob("*/*/README.md")}
        self.assertEqual({item["model_id"] for item in catalogs}, EXPECTED_MODELS)
        self.assertEqual({(ROOT / item["catalog_path"]).parent.parent for item in catalogs}, directories)
        rows = catalog.select_examples(catalogs)
        self.assertGreaterEqual(len(rows), 40)
        self.assertTrue(all(row["verification"]["live"] == "not_run" for row in rows))

    def test_exact_model_and_capability_filter_does_not_fallback(self):
        catalogs = catalog.load_catalogs()
        rows = catalog.select_examples(catalogs, "deepseek", "deepseek-flash", "vision_files")
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["path"].endswith("10_vision_files.py"))
        self.assertEqual(catalog.select_examples(catalogs, model="not-collected"), [])
        self.assertEqual(catalog.select_examples(catalogs, vendor="qwen", capability="vision"), [])
        minimax_rows = catalog.select_examples(catalogs, "minimax", "MiniMax-M2.7")
        self.assertTrue(minimax_rows)
        self.assertTrue(all(row["model_id"] == "MiniMax-M2.7" for row in minimax_rows))
        self.assertEqual(catalog.select_examples(catalogs, "minimax", "MiniMax-M2.8"), [])
        self.assertEqual(catalog.select_examples(catalogs, "deepseek", "MiniMax-M2.7"), [])

    def test_generated_index_is_current(self):
        expected = catalog.render_index(catalog.load_catalogs())
        self.assertEqual((ROOT / catalog.INDEX).read_text(encoding="utf-8"), expected)

    def test_missing_capability_exposes_exact_model_boundaries(self):
        catalogs = catalog.load_catalogs()
        hints = catalog.selection_diagnostics(catalogs, model="qwen-flash", capability="vision")
        self.assertEqual(len(hints), 1)
        self.assertIn("thinking_tool_calling", hints[0]["available_capabilities"])
        self.assertEqual(hints[0]["not_integrated"][0]["capability"], "vision")
        self.assertTrue(hints[0]["not_integrated"][0]["sources"])
        self.assertEqual(catalog.selection_diagnostics(catalogs, model="not-collected"), [])

    def test_cli_returns_json_or_fails_explicitly(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--model", "kimi-k2.6", "--capability", "video_input"], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)
        self.assertEqual(len(rows), 1)
        self.assertIn("VIDEO_PATH", rows[0]["required_env"])
        missing = subprocess.run([sys.executable, str(SCRIPT), "--model", "unknown"], capture_output=True, text=True, check=False)
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(missing.stdout, "")

    def test_invalid_catalog_rejected(self):
        for mutation in ("unofficial", "missing_file", "wrong_model", "orphan", "fake_live"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target = root / "models/deepseek/deepseek-flash/examples"
                shutil.copytree(ROOT / "models/deepseek/deepseek-flash/examples", target)
                path = target / "sources.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                if mutation == "unofficial":
                    data["examples"][0]["sources"][0]["url"] = "https://example.com/not-official"
                elif mutation == "missing_file":
                    data["examples"][0]["file"] = "does-not-exist.py"
                elif mutation == "wrong_model":
                    data["model_id"] = "deepseek-something-else"
                elif mutation == "orphan":
                    (target / "uncataloged.py").write_text("pass\n", encoding="utf-8")
                else:
                    data["examples"][0]["verification"]["live"] = "passed"
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
                    catalog.load_catalogs(root)

    def test_minimax_allows_only_its_official_source_host(self):
        for source in (
            "https://platform.minimax.io/docs/api-reference/text-chat",
            "https://platform.minimax.cn/docs/api-reference/text-chat",
            "https://platform.minimaxi.com/docs/api-reference/text-chat",
            "https://example.com/minimax/docs",
            "https://platform.minimax.io.example.com/docs",
            "https://docs.bigmodel.cn/minimax",
            "http://platform.minimax.io/docs",
        ):
            with self.subTest(source=source):
                if urlparse(source).scheme == "https" and urlparse(source).hostname in {"platform.minimax.io", "platform.minimax.cn", "platform.minimaxi.com"}:
                    catalog._sources([{"url": source, "title": "官方文本接口"}], "minimax")
                else:
                    with self.assertRaises(ValueError):
                        catalog._sources([{"url": source, "title": "非官方来源"}], "minimax")


if __name__ == "__main__":
    unittest.main()
