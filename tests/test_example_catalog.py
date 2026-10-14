"""清单、官方来源、精确型号检索与生成索引的离线回归。"""

import importlib.util
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/model-manual/scripts/example_catalog.py"
spec = importlib.util.spec_from_file_location("example_catalog", SCRIPT)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)
EXPECTED_MODELS = {
    "deepseek-flash", "kimi-k2.6", "glm-4.7", "qwen-flash",
    "doubao-seed-2-1-pro-260628", "MiniMax-M2.7",
}


class ExampleCatalogTests(unittest.TestCase):
    def test_every_model_and_runnable_file_is_cataloged(self):
        catalogs = catalog.load_catalogs()
        directories = {path.parent.parent for path in (ROOT / "models").glob("*/*/examples/sources.json")}
        self.assertEqual({item["model_id"] for item in catalogs}, EXPECTED_MODELS)
        self.assertEqual({(ROOT / item["catalog_path"]).parent.parent for item in catalogs}, directories)
        rows = catalog.select_examples(catalogs)
        self.assertGreaterEqual(len(rows), 40)
        self.assertTrue(all(row["verification"]["live"] in catalog.PUBLIC_LIVE_STATES for row in rows))
        for row in rows:
            self.assertEqual(set(row["verification"]), {"offline", "live", "note"})

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
        for relative, expected in catalog.index_outputs(catalog.load_catalogs()).items():
            with self.subTest(path=relative.as_posix()):
                self.assertEqual((ROOT / relative).read_text(encoding="utf-8"), expected)

    def test_bilingual_indices_share_canonical_data_sources_and_file_links(self):
        catalogs = catalog.load_catalogs()
        before = json.dumps(catalogs, sort_keys=True)
        chinese, english = catalog.render_index(catalogs), catalog.render_index(catalogs, language="en")
        self.assertEqual(catalog.render_index(catalogs, language="zh"), chinese)
        self.assertEqual(before, json.dumps(catalogs, sort_keys=True))
        self.assertIn("../en/docs/example-index.md", chinese)
        self.assertIn("../../docs/官方示例索引.md", english)
        for row in catalog.select_examples(catalogs):
            with self.subTest(path=row["path"]):
                self.assertIn(f"](../{row['path']})", chinese)
                self.assertIn(f"](../../{row['path']})", english)
                state = f"{row['verification']['offline']} / {row['verification']['live']}"
                self.assertIn(state, chinese)
                self.assertIn(state, english)
                for source in row["sources"]:
                    self.assertIn(f"]({source['url']})", english)
        for model in catalogs:
            directory = Path(model["catalog_path"]).parent.parent
            self.assertIn(f"](../../{directory.as_posix()}/README.en.md)", english)
            if "parameters_path" in model:
                parameters = Path(model["parameters_path"]).with_name("parameters.en.md")
                self.assertIn(f"](../../{parameters.as_posix()})", english)
            for item in model.get("not_integrated", []):
                # 所有当前译文均与canonical理由指纹匹配；资料变化后不能沿用旧译文。
                record = catalog.GAP_TRANSLATIONS[f"{model['vendor']}:{item['capability']}"]
                self.assertEqual(catalog._gap_reason_en(model["vendor"], item), record[1])
                for source in item["sources"]:
                    self.assertIn(f"]({source['url']})", english)
        with self.assertRaises(ValueError):
            catalog.render_index(catalogs, language="unknown")
        for page in (chinese, english):
            self.assertNotIn("verification/", page)
            self.assertNotIn(".local/", page)
            self.assertNotIn("evidence_id", page)

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
                # 此测试只测指定破坏项，不依赖主仓库是否已新增真实报告。
                for entry in data["examples"]:
                    entry["verification"]["live"] = "not_run"
                    entry["verification"].pop("report", None)
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


class FileExecutionEvidenceTests(unittest.TestCase):
    """临时目录内合成报告只用于校验逻辑；不执行文件、不连接厂商。"""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self, suffix=".py", live="passed", vendor="deepseek", model="deepseek-flash"):
        directory = self.root / "models" / vendor / model / "examples"
        directory.mkdir(parents=True, exist_ok=True)
        source = directory / f"01_basic{suffix}"
        source.write_text("# synthetic fixture; never executed\n", encoding="utf-8")
        (directory / "_support.py").write_text("# synthetic helper\n", encoding="utf-8")
        (directory.parent / "parameters.md").write_text("# Synthetic parameter page\n", encoding="utf-8")
        self.source_path = source.relative_to(self.root).as_posix()
        self.manifest_path = directory / "sources.json"
        self.report_path = self.root / "verification/examples/synthetic.json"
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        verification = {"offline": "mock_tested", "live": live, "note": "仅合成离线校验夹具，不是实测声明"}
        if live != "not_run":
            verification["report"] = self.report_path.relative_to(self.root).as_posix()
        manifest = {
            "schema_version": 1, "vendor": vendor, "model_id": model, "checked_at": "2026-10-14",
            "examples": [{
                "id": "basic", "file": source.name, "title": "基础调用", "capability": "chat_completions",
                "origin": "adapted_from_official", "sources": [{"url": "https://" + sorted(catalog.HOSTS[vendor])[0] + "/fixture-api", "title": "官方接口"}],
                "required_env": ["ZHIPU_API_KEY" if vendor == "zhipu" else "DEEPSEEK_API_KEY"], "run_command": f"python {self.source_path}",
                "adaptations": ["离线测试夹具"], "verification": verification,
            }], "not_integrated": [],
        }
        result = {
            "path": self.source_path, "vendor": vendor, "model_id": model,
            "tested_at": "2026-10-14T03:04:05+00:00", "source_sha256": catalog.file_identity(self.root, self.source_path),
            "status": live, "execution": "real_vendor_api", "exit_code": 0,
            "requests": [{"transport": catalog.TRANSPORTS[suffix], "http_status": 200, "requested_model": model, "endpoint": "https://" + sorted(catalog.API_HOSTS[vendor])[0] + "/chat/completions", "finish_reasons": ["stop"], "content_chars": 5, "parameters": {"stream": False}}],
            "evidence_scope": catalog.HTTP_SCOPE,
        }
        report = {
            "schema_version": 1, "kind": "example_file_execution", "execution": "real_vendor_api",
            "privacy": {name: False for name in catalog.PRIVACY_FLAGS}, "results": [result],
        }
        self.save(manifest, report if live != "not_run" else None)
        return manifest, report

    def save(self, manifest, report=None):
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        if report is not None:
            self.report_path.write_text(json.dumps(report), encoding="utf-8")

    def test_not_run_needs_no_report_and_parameter_page_is_required_reading(self):
        self.fixture(live="not_run")
        self.assertFalse(self.report_path.exists())
        catalogs = catalog.load_catalogs(self.root, private_evidence=True)
        rows = catalog.select_examples(catalogs)
        self.assertEqual(rows[0]["verification"]["live"], "not_run")
        self.assertEqual(rows[0]["parameters_path"], "models/deepseek/deepseek-flash/parameters.md")
        rendered = catalog.render_index(catalogs)
        self.assertIn("调用前必读：[逐参数说明与文件映射](../models/deepseek/deepseek-flash/parameters.md)", rendered)
        self.assertIn("不保证任意参数组合、语义正确率", rendered)

    def test_bilingual_cli_writes_only_fixture_pages_and_detects_english_staleness(self):
        self.fixture(live="not_run")
        def run(*args):
            output = io.StringIO()
            with patch.object(catalog, "ROOT", self.root), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                code = catalog.main(list(args))
            return code, output.getvalue()
        self.assertEqual(run("--write-index")[0], 0)
        chinese, english = self.root / catalog.INDEX, self.root / catalog.EN_INDEX
        self.assertTrue(chinese.is_file())
        self.assertTrue(english.is_file())
        original_chinese = chinese.read_text(encoding="utf-8")
        self.assertEqual(run("--check")[0], 0)
        english.write_text("stale English only", encoding="utf-8")
        self.assertEqual(run("--check")[0], 2)
        self.assertEqual(chinese.read_text(encoding="utf-8"), original_chinese)
        self.assertEqual(run("--write-index")[0], 0)
        code, output = run("--model", "deepseek-flash")
        self.assertEqual(code, 0)
        # 查询JSON仍返回源标题和结构，不把面向机器的内容替换成页面译文。
        row = json.loads(output)[0]
        self.assertEqual(row["title"], "基础调用")
        self.assertEqual(row["capability"], "chat_completions")
        self.assertEqual(row["verification"]["live"], "not_run")

    def test_new_or_changed_gap_reason_cannot_reuse_an_old_translation(self):
        item = {"capability": "vision", "reason": "new canonical reason"}
        translated = catalog._gap_reason_en("zhipu", item)
        self.assertNotIn(item["reason"], translated)
        self.assertNotEqual(translated, catalog.GAP_TRANSLATIONS["zhipu:vision"][1])

    def test_legacy_report_validates_time_but_exposes_only_legacy_identity_and_http_scope(self):
        _, report = self.fixture()
        catalogs = catalog.load_catalogs(self.root, private_evidence=True)
        verification = catalogs[0]["examples"][0]["verification"]
        self.assertIs(verification["legacy_evidence"], True)
        self.assertFalse({"tested_at", "duration_seconds", "legacy_tested_at"}.intersection(verification))
        self.assertEqual(catalog.evidence_metadata(report, report["results"][0]),
                         {"legacy_tested_at": "2026-10-14T03:04:05+00:00"})
        self.assertEqual(verification["evidence_scope"], catalog.HTTP_SCOPE)
        rendered = catalog.render_index(catalogs)
        self.assertIn("mock_tested / private", rendered)
        self.assertNotIn("verification/examples/synthetic.json", rendered)
        self.assertEqual(set(catalog.select_examples(catalogs)[0]["verification"]), {"offline", "live", "note"})
        for language in ("zh", "en"):
            rendered = catalog.render_index(catalogs, language=language)
            self.assertNotIn(report["results"][0]["tested_at"], rendered)
            self.assertNotIn("tested_at", rendered)

    def version_two(self, report):
        report["schema_version"] = 2
        report["evidence_id"] = str(uuid4())
        report["privacy"].update(test_timestamps_saved=False, duration_saved=False)
        for result in report["results"]:
            result.pop("tested_at", None)
            result.pop("duration_seconds", None)
        return report

    def test_v2_opaque_identity_replaces_times_without_weakening_http_scope(self):
        manifest, report = self.fixture()
        self.version_two(report)
        self.save(manifest, report)
        self.assertEqual(catalog.evidence_metadata(report, report["results"][0]), {"evidence_id": report["evidence_id"]})
        catalogs = catalog.load_catalogs(self.root, private_evidence=True)
        verification = catalogs[0]["examples"][0]["verification"]
        self.assertEqual(verification["evidence_id"], report["evidence_id"])
        self.assertEqual(verification["evidence_scope"], catalog.HTTP_SCOPE)
        self.assertFalse({"tested_at", "duration_seconds", "legacy_tested_at", "legacy_evidence"}.intersection(verification))
        for language, title in (("zh", "线上记录"), ("en", "online records")):
            page = catalog.render_index(catalogs, language=language)
            self.assertIn(title, page)
            self.assertNotIn("2026-10-14T03:04:05", page)
        for mutation in (
            lambda r: r["results"][0]["requests"][0].update(finish_reasons=["length"]),
            lambda r: r["results"][0].update(source_sha256={}),
            lambda r: r["results"][0].update(exit_code=1),
            lambda r: r["results"][0]["requests"][0].update(http_status=429),
        ):
            broken = copy.deepcopy(report)
            mutation(broken)
            self.save(manifest, broken)
            with self.assertRaises(ValueError):
                catalog.load_catalogs(self.root, private_evidence=True)

    def test_v2_requires_a_canonical_uuid4_and_explicit_false_time_privacy_flags(self):
        _, report = self.fixture()
        self.version_two(report)
        mutations = {
            "missing_id": lambda r: r.pop("evidence_id"),
            "nonstring_id": lambda r: r.update(evidence_id=4),
            "invalid_id": lambda r: r.update(evidence_id="not-a-uuid"),
            "uuid1": lambda r: r.update(evidence_id="00000000-0000-1000-8000-000000000001"),
            "uuid5": lambda r: r.update(evidence_id="00000000-0000-5000-8000-000000000001"),
            "noncanonical_id": lambda r: r.update(evidence_id=r["evidence_id"].replace("-", "")),
            "missing_timestamp_privacy": lambda r: r["privacy"].pop("test_timestamps_saved"),
            "missing_duration_privacy": lambda r: r["privacy"].pop("duration_saved"),
            "timestamp_saved": lambda r: r["privacy"].update(test_timestamps_saved=True),
            "duration_saved": lambda r: r["privacy"].update(duration_saved=True),
            "numeric_false": lambda r: r["privacy"].update(duration_saved=0),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                broken = copy.deepcopy(report)
                mutation(broken)
                with self.assertRaises(ValueError):
                    catalog.evidence_metadata(broken, broken["results"][0])

    def test_v2_rejects_time_keys_anywhere_including_unselected_nested_records(self):
        _, report = self.fixture()
        self.version_two(report)
        for key in ("tested_at", "duration_seconds"):
            for location in ("top", "result", "request", "unselected_nested"):
                with self.subTest(key=key, location=location):
                    broken = copy.deepcopy(report)
                    value = "2026-10-14T03:04:05+00:00" if key == "tested_at" else 1.5
                    target = {"top": broken, "result": broken["results"][0],
                              "request": broken["results"][0]["requests"][0]}.get(location)
                    if target is not None:
                        target[key] = value
                    else:
                        broken["extra"] = [{"nested": [{key: value}]}]
                    with self.assertRaises(ValueError):
                        catalog.evidence_metadata(broken, broken["results"][0])

    def test_public_selection_cannot_echo_legacy_time_metadata_from_a_manifest(self):
        manifest, _ = self.fixture(live="not_run")
        verification = manifest["examples"][0]["verification"]
        verification.update(tested_at="private-legacy-time", duration_seconds=1, legacy_tested_at="private-legacy-time")
        self.save(manifest)
        with self.assertRaises(ValueError):
            catalog.load_catalogs(self.root)
        # Even direct selection of an internal in-memory catalog strips private fields.
        manifest["catalog_path"] = self.manifest_path.relative_to(self.root).as_posix()
        self.assertNotIn("private-legacy-time", json.dumps(catalog.select_examples([manifest])))

    def private_fixture(self):
        manifest, report = self.fixture()
        self.version_two(report)
        original = dict(manifest["examples"][0]["verification"])
        manifest["examples"][0]["verification"] = {"offline": "mock_tested", "live": "private", "note": "实测记录仅在本地保存，不作公开通过声明"}
        self.save(manifest)
        bindings = self.root / ".local/evidence/bindings.json"
        bindings.parent.mkdir(parents=True, exist_ok=True)
        data = {"schema_version": 1, "examples": {self.source_path: original}}
        bindings.write_text(json.dumps(data), encoding="utf-8")
        mirror = self.root / ".local/evidence" / original["report"]
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(json.dumps(report), encoding="utf-8")
        return manifest, report, data, bindings, mirror

    def test_public_mode_never_reads_local_bindings_reports_or_computes_evidence_hashes(self):
        self.private_fixture()
        original_open = Path.open
        def public_open(path, *args, **kwargs):
            self.assertNotIn(".local", path.parts)
            self.assertNotIn("verification", path.parts)
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", public_open), patch.object(catalog, "file_identity", side_effect=AssertionError("public lookup cannot hash evidence")):
            loaded = catalog.load_catalogs(self.root)
            row = catalog.select_examples(loaded)[0]
            self.assertEqual(row["verification"]["live"], "private")
            self.assertEqual(set(row["verification"]), {"offline", "live", "note"})
            self.assertNotIn("verification/", catalog.render_index(loaded))

    def test_explicit_private_mode_resolves_local_binding_and_still_fails_changed_sources(self):
        _, report, _, _, _ = self.private_fixture()
        loaded = catalog.load_catalogs(self.root, private_evidence=True)
        private = loaded[0]["examples"][0]["verification"]
        self.assertEqual(private["live"], "passed")
        self.assertEqual(private["evidence_id"], report["evidence_id"])
        self.assertEqual(private["report"], ".local/evidence/verification/examples/synthetic.json")
        self.assertEqual(catalog.select_examples(loaded)[0]["verification"]["live"], "private")
        self.assertNotIn(report["evidence_id"], json.dumps(catalog.select_examples(loaded)))
        (self.root / self.source_path).write_text("# changed synthetic source\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            catalog.load_catalogs(self.root, private_evidence=True)
        self.assertEqual(catalog.load_catalogs(self.root)[0]["examples"][0]["verification"]["live"], "private")

    def test_missing_private_records_remain_private_not_passed_or_not_run(self):
        _, _, _, bindings, _ = self.private_fixture()
        bindings.unlink()
        checked = catalog.load_catalogs(self.root, private_evidence=True)[0]["examples"][0]["verification"]
        self.assertEqual(checked["live"], "private")
        self.assertEqual(set(checked), {"offline", "live", "note"})

    def test_invalid_private_binding_is_rejected_only_in_explicit_private_mode(self):
        for case in ("schema", "examples", "source", "verification", "escape", "missing_report"):
            with self.subTest(case=case):
                _, _, data, bindings, _ = self.private_fixture()
                if case == "schema":
                    data["schema_version"] = True
                elif case == "examples":
                    data["examples"] = []
                elif case == "source":
                    data["examples"]["../synthetic.py"] = data["examples"].pop(self.source_path)
                elif case == "verification":
                    data["examples"][self.source_path]["live"] = "forged"
                elif case == "escape":
                    data["examples"][self.source_path]["report"] = "../synthetic.json"
                else:
                    data["examples"][self.source_path]["report"] = "verification/examples/missing.json"
                bindings.write_text(json.dumps(data), encoding="utf-8")
                self.assertEqual(catalog.load_catalogs(self.root)[0]["examples"][0]["verification"]["live"], "private")
                with self.assertRaises(ValueError):
                    catalog.load_catalogs(self.root, private_evidence=True)

    def test_public_private_states_reject_extra_evidence_fields_and_public_pass_claims(self):
        for case in ("report", "evidence_id", "source_sha256", "requests", "passed"):
            with self.subTest(case=case):
                manifest, _ = self.fixture(live="not_run")
                check = manifest["examples"][0]["verification"]
                check["live"] = "private"
                if case == "passed":
                    check["live"] = "passed"
                else:
                    check[case] = "synthetic-private-value"
                self.save(manifest)
                with self.assertRaises(ValueError):
                    catalog.load_catalogs(self.root)

    def test_all_observed_failure_and_missing_condition_statuses_are_allowed(self):
        manifest, report = self.fixture()
        for status in sorted(catalog.LIVE_STATES - catalog.PUBLIC_LIVE_STATES - {"passed"}):
            with self.subTest(status=status):
                manifest["examples"][0]["verification"]["live"] = status
                result = report["results"][0]
                result["status"] = status
                result.pop("requests", None)
                result.pop("exit_code", None)
                result.pop("evidence_scope", None)
                self.save(manifest, report)
                loaded = catalog.load_catalogs(self.root, private_evidence=True)
                self.assertEqual(loaded[0]["examples"][0]["verification"]["live"], status)

    def test_report_identity_privacy_and_status_must_match(self):
        mutations = {
            "schema": lambda r: r.update(schema_version=True),
            "historical_capability_report": lambda r: r.update(kind="provider_verification"),
            "mock_execution": lambda r: r.update(execution="mock"),
            "saved_content": lambda r: r["privacy"].update(response_content_saved=True),
            "missing_privacy": lambda r: r.pop("privacy"),
            "missing_privacy_flag": lambda r: r["privacy"].pop("raw_error_saved"),
            "missing_result": lambda r: r.update(results=[]),
            "duplicate_result": lambda r: r["results"].append(dict(r["results"][0])),
            "path": lambda r: r["results"][0].update(path="models/deepseek/other/examples/01_basic.py"),
            "vendor": lambda r: r["results"][0].update(vendor="kimi"),
            "model": lambda r: r["results"][0].update(model_id="deepseek-other"),
            "status": lambda r: r["results"][0].update(status="failed"),
            "result_mock": lambda r: r["results"][0].update(execution="mock"),
            "missing_hashes": lambda r: r["results"][0].pop("source_sha256"),
            "missing_time": lambda r: r["results"][0].pop("tested_at"),
            "time_without_zone": lambda r: r["results"][0].update(tested_at="2026-10-14T03:04:05"),
            "invalid_legacy_time": lambda r: r["results"][0].update(tested_at="not-a-date"),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                manifest, report = self.fixture()
                mutation(report)
                self.save(manifest, report)
                with self.assertRaises(ValueError):
                    catalog.load_catalogs(self.root, private_evidence=True)

    def test_unavailable_nonrelative_and_escaping_reports_are_rejected(self):
        manifest, report = self.fixture()
        verification = manifest["examples"][0]["verification"]
        for path in ("verification/examples/missing.json", "../synthetic.json", str(self.report_path), "verification/../examples/synthetic.json", "verification\\examples\\synthetic.json"):
            with self.subTest(path=path):
                verification["report"] = path
                self.save(manifest, report)
                with self.assertRaises(ValueError):
                    catalog.load_catalogs(self.root, private_evidence=True)
        with tempfile.TemporaryDirectory() as directory:
            external = Path(directory) / "external.json"
            external.write_text(json.dumps(report), encoding="utf-8")
            (self.root / "escaped.json").symlink_to(external)
            verification["report"] = "escaped.json"
            self.save(manifest, report)
            with self.assertRaises(ValueError):
                catalog.load_catalogs(self.root, private_evidence=True)

    def test_changed_source_or_support_or_new_helper_invalidates_report(self):
        for filename in ("01_basic.py", "_support.py", "_new_helper.py"):
            with self.subTest(filename=filename):
                self.fixture()
                target = self.manifest_path.parent / filename
                target.write_text("# changed after execution\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "支持文件已变更"):
                    catalog.load_catalogs(self.root, private_evidence=True)
                if filename == "_new_helper.py":
                    target.unlink()

    def test_python_passed_requires_successful_current_model_real_http_and_exit_zero(self):
        mutations = {
            "failed_exit": lambda r: r.update(exit_code=1),
            "bool_exit": lambda r: r.update(exit_code=False),
            "missing_exit": lambda r: r.pop("exit_code"),
            "no_trace": lambda r: r.update(requests=[], evidence_scope=catalog.PROCESS_SCOPE),
            "mock_transport": lambda r: r["requests"][0].update(transport="mock"),
            "unofficial_endpoint": lambda r: r["requests"][0].update(endpoint="https://example.com/chat/completions"),
            "other_vendor_endpoint": lambda r: r["requests"][0].update(endpoint="https://api.moonshot.cn/chat/completions"),
            "endpoint_credentials": lambda r: r["requests"][0].update(endpoint="https://secret@api.deepseek.com/chat/completions"),
            "endpoint_query": lambda r: r["requests"][0].update(endpoint="https://api.deepseek.com/chat/completions?key=secret"),
            "failed_http": lambda r: r["requests"][0].update(http_status=429),
            "wrong_model_http": lambda r: r["requests"][0].update(requested_model="another-model"),
            "upload_only_http": lambda r: r["requests"][0].pop("requested_model"),
            "wrong_scope": lambda r: r.update(evidence_scope=catalog.PROCESS_SCOPE),
            "missing_scope": lambda r: r.pop("evidence_scope"),
            "missing_finish": lambda r: r["requests"][0].pop("finish_reasons"),
            "missing_body": lambda r: r["requests"][0].pop("content_chars"),
            "empty_body": lambda r: r["requests"][0].update(content_chars=0),
            "length": lambda r: r["requests"][0].update(finish_reasons=["length"]),
            "unhandled_tools": lambda r: r["requests"][0].update(has_tool_calls=True),
            "business_failure": lambda r: r["requests"][0].update(business_status=1000),
            "telemetry_failure": lambda r: r["requests"][0].update(telemetry_error=True),
            "telemetry_overflow": lambda r: r["requests"][0].update(telemetry_overflow=True),
            "unfinished_stream": lambda r: r["requests"][0].update(parameters={"stream": True}),
            "final_429": lambda r: r["requests"].append({**r["requests"][0], "http_status": 429}),
            "final_length": lambda r: r["requests"].append({**r["requests"][0], "finish_reasons": ["length"]}),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                manifest, report = self.fixture()
                mutation(report["results"][0])
                self.save(manifest, report)
                with self.assertRaises(ValueError):
                    catalog.load_catalogs(self.root, private_evidence=True)

    def test_success_after_a_failed_http_attempt_is_not_rejected(self):
        manifest, report = self.fixture()
        requests = report["results"][0]["requests"]
        requests.insert(0, {**requests[0], "http_status": 429})
        self.save(manifest, report)
        self.assertEqual(catalog.load_catalogs(self.root, private_evidence=True)[0]["examples"][0]["verification"]["live"], "passed")

    def test_paid_glm_rejects_explicit_served_conflict_even_before_a_later_normal_reply(self):
        for early_conflict in (False, True):
            with self.subTest(early_conflict=early_conflict), tempfile.TemporaryDirectory() as directory:
                previous = self.root
                self.root = Path(directory)
                try:
                    manifest, report = self.fixture(vendor="zhipu", model="glm-4.7")
                    requests = report["results"][0]["requests"]
                    requests[0]["served_model"] = "glm-4.7-flash"
                    if early_conflict:
                        requests.append({**requests[0], "served_model": "glm-4.7"})
                    self.save(manifest, report)
                    with self.assertRaises(ValueError):
                        catalog.load_catalogs(self.root, private_evidence=True)
                    requests[0]["served_model"] = "glm-4.7"
                    self.save(manifest, report)
                    catalog.load_catalogs(self.root, private_evidence=True)
                finally:
                    self.root = previous

    def test_other_vendor_served_alias_is_not_rejected_by_paid_glm_identity_rule(self):
        manifest, report = self.fixture()
        report["results"][0]["requests"][0]["served_model"] = "deepseek-v4-flash"
        self.save(manifest, report)
        catalog.load_catalogs(self.root, private_evidence=True)

    def test_all_languages_require_complete_matching_real_http_evidence(self):
        for suffix in (".py", ".sh", ".ts"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                # 不同后缀各自只有一个可运行文件，避免清单孤儿文件干扰校验。
                previous = self.root
                self.root = Path(directory)
                try:
                    manifest, report = self.fixture(suffix=suffix)
                    rendered = catalog.render_index(catalog.load_catalogs(self.root, private_evidence=True))
                    self.assertIn("mock_tested / private", rendered)
                    self.assertNotIn("verification/examples/synthetic.json", rendered)
                    result = report["results"][0]
                    request = result["requests"][0]
                    result.update(evidence_scope=catalog.PROCESS_SCOPE, requests=[])
                    self.save(manifest, report)
                    with self.assertRaises(ValueError):
                        catalog.load_catalogs(self.root, private_evidence=True)
                    result.update(evidence_scope=catalog.HTTP_SCOPE, requests=[{**request, "transport": "mock"}])
                    self.save(manifest, report)
                    with self.assertRaises(ValueError):
                        catalog.load_catalogs(self.root, private_evidence=True)
                finally:
                    self.root = previous

    def test_stream_done_or_real_transport_eof_and_responses_completed_are_valid(self):
        for suffix in (".py", ".sh", ".ts"):
            for mode in ("done", "eof", "responses"):
                with self.subTest(suffix=suffix, mode=mode), tempfile.TemporaryDirectory() as directory:
                    previous = self.root
                    self.root = Path(directory)
                    try:
                        manifest, report = self.fixture(suffix=suffix)
                        request = report["results"][0]["requests"][0]
                        if mode == "responses":
                            request.pop("finish_reasons")
                            request["response_status"] = "completed"
                        else:
                            request["parameters"]["stream"] = True
                            request["sse_done" if mode == "done" else "transport_eof"] = True
                        self.save(manifest, report)
                        catalog.load_catalogs(self.root, private_evidence=True)
                    finally:
                        self.root = previous

    def test_tool_requests_must_return_to_final_text_before_canonical_passed(self):
        manifest, report = self.fixture()
        requests = report["results"][0]["requests"]
        requests.insert(0, {**requests[0], "finish_reasons": ["tool_calls"], "has_tool_calls": True, "content_chars": 0})
        self.save(manifest, report)
        catalog.load_catalogs(self.root, private_evidence=True)
        requests.reverse()
        self.save(manifest, report)
        with self.assertRaises(ValueError):
            catalog.load_catalogs(self.root, private_evidence=True)

    def test_failed_process_only_record_remains_transparent_but_not_passed(self):
        manifest, report = self.fixture(live="failed")
        report["results"][0].update(exit_code=1, requests=[], evidence_scope=catalog.PROCESS_SCOPE)
        self.save(manifest, report)
        rendered = catalog.render_index(catalog.load_catalogs(self.root, private_evidence=True))
        self.assertIn("mock_tested / private", rendered)
        self.assertNotIn("verification/examples/synthetic.json", rendered)

    def test_transport_helpers_are_part_of_source_identity_when_present(self):
        for suffix, helper_path in catalog.TRACE_HELPERS.items():
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                previous = self.root
                self.root = Path(directory)
                try:
                    self.fixture(suffix=suffix)
                    # 加入旁观代码后，旧报告哈希也必须失效，不能沿用进程模式身份。
                    helper = self.root / helper_path
                    helper.parent.mkdir(parents=True, exist_ok=True)
                    helper.write_text("# synthetic transport observer\n", encoding="utf-8")
                    self.assertIn(helper_path, catalog.file_identity(self.root, self.source_path))
                    with self.assertRaisesRegex(ValueError, "支持文件已变更"):
                        catalog.load_catalogs(self.root, private_evidence=True)
                    self.fixture(suffix=suffix)
                    catalog.load_catalogs(self.root, private_evidence=True)
                    helper.write_text("# changed observer\n", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "支持文件已变更"):
                        catalog.load_catalogs(self.root, private_evidence=True)
                finally:
                    self.root = previous

    def test_not_run_with_report_and_unknown_live_status_are_rejected(self):
        manifest, report = self.fixture()
        for live in ("not_run", "private", "unverified"):
            with self.subTest(live=live):
                manifest["examples"][0]["verification"]["live"] = live
                self.save(manifest, report)
                with self.assertRaises(ValueError):
                    catalog.load_catalogs(self.root, private_evidence=True)

    def test_hash_identity_matches_the_real_runner_without_running_it(self):
        runner_spec = importlib.util.spec_from_file_location("example_file_runner_identity", ROOT / "tests/run_example_files.py")
        runner = importlib.util.module_from_spec(runner_spec)
        runner_spec.loader.exec_module(runner)
        # 单纯导入不读取凭据、不执行 main；临时根目录替换仅用于纯哈希函数。
        self.fixture()
        runner.ROOT = self.root
        self.assertEqual(catalog.file_identity(self.root, self.source_path), runner.file_identity(self.source_path))
        base = {"http_status": 200, "content_chars": 4, "finish_reasons": ["stop"], "parameters": {"stream": False}}
        variants = [base, {**base, "content_chars": 0}, {**base, "finish_reasons": []},
                    {**base, "http_status": 429}, {**base, "telemetry_error": True},
                    {**base, "telemetry_overflow": True}, {**base, "business_status": 1},
                    {**base, "has_tool_calls": True}, {**base, "response_status": "completed", "finish_reasons": []},
                    {**base, "parameters": {"stream": True}},
                    {**base, "parameters": {"stream": True}, "sse_done": True},
                    {**base, "parameters": {"stream": True}, "transport_eof": True}]
        for request in variants:
            with self.subTest(request=request):
                self.assertEqual(catalog._completion_succeeded(request), runner.completion_succeeded(request))


if __name__ == "__main__":
    unittest.main()
