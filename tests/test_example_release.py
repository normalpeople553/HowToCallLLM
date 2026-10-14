"""逐文件发布门槛的独立离线夹具；不依赖仓库现有报告是否通过。"""

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("example_release", ROOT / "tests/check_example_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ExampleReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.catalog, self.runner = release.dependencies(self.root)
        self.source = "models/deepseek/deepseek-flash/examples/01_basic.py"
        source = self.root / self.source
        source.parent.mkdir(parents=True)
        source.write_text("# synthetic example, never executed\n", encoding="utf-8")
        (source.parent / "_support.py").write_text("# synthetic support\n", encoding="utf-8")
        self.manifest_path = source.parent / "sources.json"
        self.manifest = {
            "schema_version": 1, "vendor": "deepseek", "model_id": "deepseek-flash", "checked_at": "2026-10-14",
            "examples": [{"id": "basic", "file": source.name, "title": "测试调用", "capability": "chat_completions",
                          "origin": "adapted_from_official", "sources": [{"url": "https://api-docs.deepseek.com/api/create-chat-completion", "title": "官方接口"}],
                          "required_env": ["DEEPSEEK_API_KEY"], "run_command": f"python {self.source}", "adaptations": ["合成离线夹具"],
                          "verification": {"offline": "mock_tested", "live": "not_run", "note": "合成夹具不声明实测"}}],
            "not_integrated": [],
        }
        self.save_manifest()
        references = self.root / "skills/model-manual/references"
        (references / "models").mkdir(parents=True)
        (references / "models/deepseek-flash.json").write_text(json.dumps({"vendor": "deepseek", "model_id": "deepseek-flash"}), encoding="utf-8")
        (references / "vendors.json").write_text(json.dumps({"vendors": {"deepseek": {"default_model": "deepseek-flash"}}}), encoding="utf-8")
        # 若误调用执行器或读凭据，测试立即失败。
        self.runner.credentials = mock.Mock(side_effect=AssertionError("credentials_must_not_be_read"))
        self.runner.execute_entry = mock.Mock(side_effect=AssertionError("example_must_not_be_executed"))
        self.dependency_patch = mock.patch.object(release, "dependencies", return_value=(self.catalog, self.runner))
        self.dependency_patch.start()
        self.addCleanup(self.dependency_patch.stop)

    def save_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def record(self, source=None, status="passed", hour=1, requests=None):
        source = source or self.source
        entry = next(entry for entry in self.runner.discover() if entry["path"] == source)
        return {
            **entry, "execution": "real_vendor_api", "status": status, "tested_at": f"2026-10-14T{hour:02}:00:00+00:00",
            "source_sha256": self.runner.file_identity(source), "exit_code": 0 if status == "passed" else 1,
            "requests": copy.deepcopy(requests if requests is not None else [self.http()]),
            "evidence_scope": self.catalog.HTTP_SCOPE,
        }

    def http(self, model="deepseek-flash", host="api.deepseek.com", suffix=".py"):
        return {"transport": self.catalog.TRANSPORTS[suffix], "method": "POST", "endpoint": f"https://{host}/chat/completions",
                "requested_model": model, "http_status": 200, "finish_reasons": ["stop"], "content_chars": 4,
                "parameters": {"stream": False}}

    def report(self, name, records):
        path = self.root / "verification/examples" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema_version": 1, "kind": "example_file_execution", "execution": "real_vendor_api",
                                    "privacy": {flag: False for flag in self.catalog.PRIVACY_FLAGS}, "results": records}), encoding="utf-8")
        return path

    def collect(self):
        return release.collect_release(self.root)

    def test_missing_evidence_is_explicit_and_inventory_includes_root_examples(self):
        for name in ("01_quickstart.py", "02_one_for_all.py", "03_streaming.py", "04_multi_turn.py"):
            path = self.root / "examples" / name
            path.parent.mkdir(exist_ok=True)
            path.write_text("# synthetic root example\n", encoding="utf-8")
        data = self.collect()
        self.assertEqual(data["total"], 5)
        self.assertEqual(data["counts"]["missing_evidence"], 5)
        self.assertFalse(data["ready"])
        page = release.render_page(data)
        self.assertIn("缺少报告", page)
        self.assertIn("examples/04_multi_turn.py", page)
        self.assertNotIn(str(self.root), page)
        self.runner.credentials.assert_not_called()
        self.runner.execute_entry.assert_not_called()

    def test_current_source_strict_http_passes_without_assuming_existing_reports(self):
        self.report("current.json", [self.record()])
        data = self.collect()
        self.assertTrue(data["ready"])
        self.assertEqual(data["counts"]["passed"], 1)

    def test_bilingual_pages_share_counts_paths_and_canonical_evidence(self):
        self.report("failure.json", [self.record(status="rate_limited", hour=1)])
        self.report("pass.json", [self.record(hour=2)])
        data = self.collect()
        before = copy.deepcopy(data)
        chinese, english = release.render_page(data), release.render_page(data, language="en")
        self.assertEqual(data, before)
        self.assertEqual(release.render_page(data, language="zh"), chinese)
        outputs = release.page_outputs(data)
        self.assertEqual(set(outputs), {release.PAGE, release.EN_PAGE})
        summary = f"**{data['counts']['passed']}/{data['total']}**"
        self.assertIn(summary, chinese)
        self.assertIn(summary, english)
        self.assertIn("../en/docs/example-status.md", chinese)
        self.assertIn("../../docs/示例实测状态.md", english)
        self.assertIn("../../models/README.en.md", english)
        for row in data["rows"]:
            self.assertIn(f"](../{row['path']})", chinese)
            self.assertIn(f"](../../{row['path']})", english)
            for attempt in row["attempts"]:
                self.assertIn(f"](../{attempt['report']})", chinese)
                self.assertIn(f"](../../{attempt['report']})", english)
                self.assertIn(attempt["tested_at"], english)
        with self.assertRaises(ValueError):
            release.render_page(data, language="unknown")

    def test_latest_valid_pass_is_selected_but_later_and_earlier_failures_survive(self):
        self.report("old-failure.json", [self.record(status="failed", hour=1)])
        self.report("effective-pass.json", [self.record(hour=2)])
        self.report("later-failure.json", [self.record(status="rate_limited", hour=3)])
        data = self.collect()
        row = data["rows"][0]
        self.assertEqual(row["status"], "passed")
        self.assertEqual(row["selected"]["report"], "verification/examples/effective-pass.json")
        self.assertEqual(len(row["attempts"]), 3)
        page = release.render_page(data)
        self.assertIn("old-failure.json", page)
        self.assertIn("later-failure.json", page)
        self.assertIn("历史失败", page)

    def test_http_200_without_finish_or_body_is_incomplete_not_capability_failure(self):
        http = self.http()
        http.pop("finish_reasons")
        http.pop("content_chars")
        self.report("old-observer.json", [self.record(requests=[http])])
        data = self.collect()
        self.assertEqual(data["rows"][0]["status"], "incomplete_evidence")
        self.assertIn("缺完整证据", release.render_page(data))

    def test_final_response_must_satisfy_all_completion_and_transport_guards(self):
        mutations = {
            "length": lambda r: r["requests"][0].update(finish_reasons=["length"]),
            "empty": lambda r: r["requests"][0].update(content_chars=0),
            "unfinished_stream": lambda r: r["requests"][0].update(parameters={"stream": True}),
            "parse_error": lambda r: r["requests"][0].update(telemetry_error=True),
            "overflow": lambda r: r["requests"][0].update(telemetry_overflow=True),
            "business_error": lambda r: r["requests"][0].update(business_status=1000),
            "tool_only": lambda r: r["requests"][0].update(has_tool_calls=True),
            "wrong_transport": lambda r: r["requests"][0].update(transport="real_fetch"),
            "wrong_host": lambda r: r["requests"][0].update(endpoint="https://api.moonshot.cn/chat/completions"),
            "wrong_model": lambda r: r["requests"][0].update(requested_model="qwen-flash"),
            "wrong_exit": lambda r: r.update(exit_code=1),
            "boolean_exit": lambda r: r.update(exit_code=False),
            "no_http": lambda r: r.update(requests=[], evidence_scope=self.catalog.PROCESS_SCOPE),
            "http_failure": lambda r: r["requests"][0].update(http_status=429),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                record = self.record()
                mutate(record)
                self.report("mutation.json", [record])
                data = self.collect()
                self.assertFalse(data["ready"])
                self.assertEqual(data["counts"]["passed"], 0)

    def test_finished_stream_and_responses_completed_are_accepted(self):
        for mode in ("stream", "responses"):
            with self.subTest(mode=mode):
                http = self.http()
                if mode == "stream":
                    http.update(parameters={"stream": True}, sse_done=True)
                else:
                    http.pop("finish_reasons")
                    http["response_status"] = "completed"
                self.report("completion.json", [self.record(requests=[http])])
                self.assertTrue(self.collect()["ready"])

    def test_last_request_per_model_not_any_earlier_success_decides_completion(self):
        failed = {**self.http(), "finish_reasons": ["length"]}
        self.report("last-failed.json", [self.record(requests=[self.http(), failed])])
        self.assertEqual(self.collect()["rows"][0]["status"], "incomplete_evidence")

    def test_tool_loop_needs_final_text_completion(self):
        tool = {**self.http(), "finish_reasons": ["tool_calls"], "has_tool_calls": True, "content_chars": 0}
        self.report("tool-loop.json", [self.record(requests=[tool, self.http()])])
        self.assertTrue(self.collect()["ready"])

    def test_changed_source_and_support_invalidate_old_pass(self):
        for filename in ("01_basic.py", "_support.py"):
            with self.subTest(filename=filename):
                self.report("before-edit.json", [self.record()])
                (self.manifest_path.parent / filename).write_text("# changed\n", encoding="utf-8")
                data = self.collect()
                self.assertEqual(data["rows"][0]["status"], "stale_source")
                self.assertFalse(data["ready"])

    def test_typescript_and_curl_observer_hashes_and_transport_are_required(self):
        for suffix, helper_name in self.catalog.TRACE_HELPERS.items():
            with self.subTest(suffix=suffix):
                source = self.manifest_path.parent / ("02_other" + suffix)
                source.write_text("# synthetic language example\n", encoding="utf-8")
                helper = self.root / helper_name
                helper.parent.mkdir(exist_ok=True)
                helper.write_text("# synthetic observer\n", encoding="utf-8")
                entry = copy.deepcopy(self.manifest["examples"][0])
                entry.update(id="other" + suffix, file=source.name)
                self.manifest["examples"].append(entry)
                self.save_manifest()
                relative = source.relative_to(self.root).as_posix()
                record = self.record(source=relative, requests=[self.http(suffix=suffix)])
                self.assertIn(helper_name, record["source_sha256"])
                self.report("language" + suffix + ".json", [record])
                row = next(row for row in self.collect()["rows"] if row["path"] == relative)
                self.assertEqual(row["status"], "passed")
                helper.write_text("# observer changed\n", encoding="utf-8")
                row = next(row for row in self.collect()["rows"] if row["path"] == relative)
                self.assertEqual(row["status"], "stale_source")

    def test_shared_root_requires_every_model_on_its_own_vendor_endpoint(self):
        source = self.root / "examples/02_one_for_all.py"
        source.parent.mkdir()
        source.write_text("# synthetic shared example\n", encoding="utf-8")
        (self.root / "skills/model-manual/references/models/qwen-flash.json").write_text(json.dumps({"vendor": "qwen", "model_id": "qwen-flash"}), encoding="utf-8")
        self.add_default_model("qwen", "qwen-flash")
        record = self.record(source="examples/02_one_for_all.py")
        self.report("shared.json", [record])
        row = next(row for row in self.collect()["rows"] if row["path"] == "examples/02_one_for_all.py")
        self.assertEqual(row["status"], "incomplete_evidence")
        record["requests"].append(self.http(model="qwen-flash", host="dashscope.aliyuncs.com"))
        self.report("shared.json", [record])
        row = next(row for row in self.collect()["rows"] if row["path"] == "examples/02_one_for_all.py")
        self.assertEqual(row["status"], "passed")
        record["requests"][-1]["endpoint"] = "https://api.deepseek.com/chat/completions"
        self.report("shared.json", [record])
        row = next(row for row in self.collect()["rows"] if row["path"] == "examples/02_one_for_all.py")
        self.assertEqual(row["status"], "invalid_evidence")
        (self.root / "skills/model-manual/references/models/glm-4.7.json").write_text(json.dumps({"vendor": "zhipu", "model_id": "glm-4.7"}), encoding="utf-8")
        self.add_default_model("zhipu", "glm-4.7")
        wrong_served = {**self.http(model="glm-4.7", host="open.bigmodel.cn"), "served_model": "glm-4.7-flash"}
        record = self.record(source="examples/02_one_for_all.py", requests=[self.http(), self.http(model="qwen-flash", host="dashscope.aliyuncs.com"), wrong_served])
        self.report("shared.json", [record])
        row = next(row for row in self.collect()["rows"] if row["path"] == "examples/02_one_for_all.py")
        self.assertEqual(row["status"], "invalid_evidence")

    def add_default_model(self, vendor, model):
        path = self.root / "skills/model-manual/references/vendors.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["vendors"][vendor] = {"default_model": model}
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_shared_routing_change_invalidates_earlier_pass_without_editing_report(self):
        relative = "examples/02_one_for_all.py"
        source = self.root / relative
        source.parent.mkdir()
        source.write_text("# synthetic shared example\n", encoding="utf-8")
        path = self.report("shared-before-migration.json", [self.record(source=relative)])
        original = path.read_bytes()
        row = next(row for row in self.collect()["rows"] if row["path"] == relative)
        self.assertEqual(row["status"], "passed")
        card = self.root / "skills/model-manual/references/models/glm-4.7.json"
        card.write_text(json.dumps({"vendor": "zhipu", "model_id": "glm-4.7"}), encoding="utf-8")
        self.add_default_model("zhipu", "glm-4.7")
        row = next(row for row in self.collect()["rows"] if row["path"] == relative)
        self.assertEqual(row["status"], "stale_source")
        self.assertFalse(row["attempts"][0]["current_source"])
        self.assertEqual(path.read_bytes(), original)

    def test_archived_nondefault_card_is_not_a_shared_execution_target(self):
        relative = "examples/02_one_for_all.py"
        source = self.root / relative
        source.parent.mkdir()
        source.write_text("# synthetic shared example\n", encoding="utf-8")
        archived = self.root / "skills/model-manual/references/models/glm-4.7-flash.json"
        archived.write_text(json.dumps({"vendor": "zhipu", "model_id": "glm-4.7-flash"}), encoding="utf-8")
        # Hash includes the archive conservatively, but the actual shared script loops vendor defaults only.
        self.report("shared-defaults-only.json", [self.record(source=relative)])
        row = next(row for row in self.collect()["rows"] if row["path"] == relative)
        self.assertEqual(row["status"], "passed")

    def test_paid_glm_example_never_inherits_flash_file_report_or_model_identity(self):
        relative = "models/zhipu/glm-4.7/examples/01_basic.py"
        source = self.root / relative
        source.parent.mkdir(parents=True)
        source.write_text("# synthetic paid-model example\n", encoding="utf-8")
        manifest = copy.deepcopy(self.manifest)
        manifest.update(vendor="zhipu", model_id="glm-4.7")
        manifest["examples"][0]["sources"] = [{"url": "https://docs.bigmodel.cn/cn/guide/models/llm/glm-4.7", "title": "Official model"}]
        manifest["examples"][0]["required_env"] = ["ZHIPU_API_KEY"]
        manifest["examples"][0]["run_command"] = "python " + relative
        (source.parent / "sources.json").write_text(json.dumps(manifest), encoding="utf-8")
        report = self.record(source=relative, requests=[self.http(model="glm-4.7", host="open.bigmodel.cn")])
        old = copy.deepcopy(report)
        old.update(path="models/zhipu/glm-4.7-flash/examples/01_basic.py", model_id="glm-4.7-flash")
        self.report("old-flash.json", [old])
        row = next(row for row in self.collect()["rows"] if row["path"] == relative)
        self.assertEqual(row["status"], "missing_evidence")
        old["path"] = relative
        self.report("misattributed-flash.json", [old])
        row = next(row for row in self.collect()["rows"] if row["path"] == relative)
        self.assertEqual(row["status"], "invalid_evidence")
        self.assertFalse(row["attempts"][0]["strict_passed"])
        report["requests"][0]["served_model"] = "glm-4.7-flash"
        report["tested_at"] = "2026-10-14T03:00:00+00:00"
        self.report("paid-request-free-served.json", [report])
        row = next(row for row in self.collect()["rows"] if row["path"] == relative)
        self.assertEqual(row["status"], "invalid_evidence")
        self.assertFalse(row["selected"]["strict_passed"])

    def test_report_header_wrong_model_duplicate_and_privacy_cannot_claim_pass(self):
        for mutation in ("kind", "privacy", "model", "duplicate"):
            with self.subTest(mutation=mutation):
                record = self.record()
                path = self.report("invalid.json", [record])
                report = json.loads(path.read_text(encoding="utf-8"))
                if mutation == "kind":
                    report["kind"] = "provider_verification"
                elif mutation == "privacy":
                    report["privacy"]["api_key_saved"] = True
                elif mutation == "model":
                    report["results"][0]["model_id"] = "other-model"
                else:
                    report["results"].append(dict(record))
                path.write_text(json.dumps(report), encoding="utf-8")
                self.assertFalse(self.collect()["ready"])

    def test_invalid_report_timestamp_is_not_rendered_as_untrusted_text(self):
        record = self.record()
        record["tested_at"] = "untrusted-field-not-a-date"
        self.report("bad-time.json", [record])
        data = self.collect()
        self.assertFalse(data["ready"])
        self.assertNotIn("untrusted-field-not-a-date", release.render_page(data))

    def test_catalog_is_validated_and_cannot_publish_incomplete_passed_reference(self):
        old = self.record()
        old["requests"][0].pop("finish_reasons")
        self.report("old.json", [old])
        self.report("new.json", [self.record(hour=2)])
        self.manifest["examples"][0]["verification"].update(live="passed", report="verification/examples/old.json")
        self.save_manifest()
        data = self.collect()
        self.assertEqual(data["counts"]["passed"], 1)
        self.assertFalse(data["ready"])
        self.assertEqual(data["catalog_issues"][0]["code"], "catalog_validation_failed")
        self.manifest["examples"][0]["verification"]["report"] = "verification/examples/new.json"
        self.save_manifest()
        self.assertTrue(self.collect()["ready"])
        self.manifest["examples"][0]["sources"][0]["url"] = "https://example.com/not-official"
        self.save_manifest()
        self.assertFalse(self.collect()["catalog_valid"])

    def test_cli_separates_page_freshness_from_complete_release_gate(self):
        def run(*args):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return release.main(["--root", str(self.root), *args])
        self.assertEqual(run("--write"), 0)
        self.assertTrue((self.root / release.EN_PAGE).is_file())
        self.assertEqual(run("--check"), 0)
        self.assertEqual(run("--check", "--require-passed"), 1)
        chinese_before = (self.root / release.PAGE).read_text(encoding="utf-8")
        (self.root / release.EN_PAGE).write_text("stale English only", encoding="utf-8")
        self.assertEqual(run("--check"), 2)
        self.assertEqual((self.root / release.PAGE).read_text(encoding="utf-8"), chinese_before)
        self.assertEqual(run("--write"), 0)
        self.assertEqual(run("--check"), 0)
        (self.root / release.PAGE).write_text("stale", encoding="utf-8")
        self.assertEqual(run("--check"), 2)
        self.report("current.json", [self.record()])
        self.assertEqual(run("--write", "--require-passed"), 0)
        self.assertEqual(run("--check", "--require-passed"), 0)


if __name__ == "__main__":
    unittest.main()
