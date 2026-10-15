"""逐文件执行器的离线隐私/证据测试；不用真实 .env 或厂商 API。

SDK 集成测试仅替换 HTTPTransport 的网络返回，不替换 OpenAI SDK；缺少
锁定依赖时明确 skip。所有凭据/正文/ID 均为本文件生成的假 fixture。
"""

import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import RFC_4122, UUID
import zlib


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests/run_example_files.py"
spec = importlib.util.spec_from_file_location("live_example_runner_under_test", SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
SDK_AVAILABLE = all(importlib.util.find_spec(name) is not None for name in ("openai", "httpx"))
SECRET = "fixture-secret-NOT-A-REAL-KEY"
PRIVATE = "private-prompt-and-response-fixture"


def request(url="https://api.deepseek.com/chat/completions", payload=None):
    parsed = urlsplit(url)
    return types.SimpleNamespace(
        url=types.SimpleNamespace(path=parsed.path, host=parsed.hostname),
        method="POST",
        headers={"content-type": "application/json", "authorization": "Bearer " + SECRET},
        read=lambda: json.dumps(payload or {}).encode(),
    )


class LiveExampleRunnerTests(unittest.TestCase):
    def test_credentials_use_only_explicit_temporary_fixture_and_do_not_print_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "fixture.env"
            fixture.write_text(
                f'export DEEPSEEK_API_KEY="{SECRET}"\n'
                'MOONSHOT_API_KEY="file-value"\n'
                'DASHSCOPE_API_KEY="替换你的Key"\n'
                'UNRELATED_SECRET="must-not-load"\n', encoding="utf-8",
            )
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                env = runner.credentials(
                    {"MOONSHOT_API_KEY": "environment-value", "OPENAI_LOG": "debug"}, fixture,
                )
            self.assertEqual(env["DEEPSEEK_API_KEY"], SECRET)
            self.assertEqual(env["MOONSHOT_API_KEY"], "environment-value")
            self.assertNotIn("DASHSCOPE_API_KEY", env)
            self.assertNotIn("UNRELATED_SECRET", env)
            self.assertNotIn("OPENAI_LOG", env)
            self.assertEqual(stdout.getvalue() + stderr.getvalue(), "")

    def test_dry_run_only_lists_metadata_without_loading_credentials(self):
        output = io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT)]), patch.object(
            runner, "credentials", side_effect=AssertionError("dry run must not inspect credentials"),
        ), contextlib.redirect_stdout(output):
            self.assertEqual(runner.main(), 0)
        rows = json.loads(output.getvalue())
        self.assertNotIn(SECRET, output.getvalue())
        self.assertTrue(all(set(row) == {"path", "vendor", "model_id", "required_keys", "capability"} for row in rows))

    def test_discover_covers_all_registered_runnable_files_once(self):
        rows = runner.discover()
        actual = {row["path"] for row in rows}
        files = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "models").glob("*/*/examples/*")
            if path.suffix in {".py", ".sh", ".ts"} and not path.name.startswith("_")
        }
        files.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "examples").glob("*.py"))
        self.assertEqual(len(actual), len(rows))
        self.assertEqual(actual, files)
        self.assertEqual({row["vendor"] for row in rows}, {*runner.KEYS, "shared"})
        for row in rows:
            expected = list(runner.KEYS.values()) if row["vendor"] == "shared" else [runner.KEYS[row["vendor"]]]
            self.assertEqual(row["required_keys"], expected)

    def test_file_identity_includes_support_and_changes_when_support_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative = "models/deepseek/deepseek-flash/examples/01_basic.py"
            example = root / relative
            example.parent.mkdir(parents=True)
            example.write_bytes(b"pass\n")
            helper = example.with_name("_support.py")
            helper.write_text("SETTING = 1\n", encoding="utf-8")
            with patch.object(runner, "ROOT", root):
                first = runner.file_identity(relative)
                helper.write_text("SETTING = 2\n", encoding="utf-8")
                second = runner.file_identity(relative)
            helper_key = helper.relative_to(root).as_posix()
            self.assertEqual(set(first), {relative, helper_key})
            self.assertEqual(first[relative], hashlib.sha256(b"pass\n").hexdigest())
            self.assertEqual(first[relative], second[relative])
            self.assertNotEqual(first[helper_key], second[helper_key])

    def test_shared_identity_includes_model_cards_and_vendor_routing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            example = root / "examples/02_one_for_all.py"
            example.parent.mkdir()
            example.write_text("pass\n", encoding="utf-8")
            refs = root / "skills/model-manual/references"
            (refs / "models").mkdir(parents=True)
            card = refs / "models/fixture.json"
            vendors = refs / "vendors.json"
            card.write_text("{}", encoding="utf-8")
            vendors.write_text("{}", encoding="utf-8")
            with patch.object(runner, "ROOT", root):
                first = runner.file_identity("examples/02_one_for_all.py")
                card.write_text('{"changed":true}', encoding="utf-8")
                second = runner.file_identity("examples/02_one_for_all.py")
            self.assertEqual(set(first), {
                "examples/02_one_for_all.py", "skills/model-manual/references/models/fixture.json",
                "skills/model-manual/references/vendors.json",
            })
            self.assertNotEqual(first, second)

    def test_png_is_a_complete_crc_valid_256_pixel_red_image(self):
        data = runner.png_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        cursor, kinds, compressed = 8, [], bytearray()
        while cursor < len(data):
            size = struct.unpack(">I", data[cursor:cursor + 4])[0]
            kind = data[cursor + 4:cursor + 8]
            body = data[cursor + 8:cursor + 8 + size]
            crc = struct.unpack(">I", data[cursor + 8 + size:cursor + 12 + size])[0]
            self.assertEqual(crc, zlib.crc32(kind + body) & 0xffffffff)
            kinds.append(kind)
            if kind == b"IHDR":
                self.assertEqual(struct.unpack(">IIBBBBB", body), (256, 256, 8, 2, 0, 0, 0))
            if kind == b"IDAT":
                compressed.extend(body)
            cursor += 12 + size
        self.assertEqual(cursor, len(data))
        self.assertEqual(kinds, [b"IHDR", b"IDAT", b"IEND"])
        self.assertEqual(zlib.decompress(compressed), (b"\0" + b"\xff\0\0" * 256) * 256)

    def test_prepare_inputs_never_inherits_private_media_without_fixture(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(runner.shutil, "which", return_value=None):
            inputs = runner.prepare_inputs(Path(temporary), {
                "IMAGE_PATH": "/private/photo.png", "IMAGE_URL": "https://private.example/photo",
                "IMAGE_FILE_ID": "private-file-id", "VIDEO_PATH": "/private/video.mp4",
                "VIDEO_URL": "https://private.example/video", "DEEPSEEK_API_KEY": SECRET,
            })
            self.assertEqual(inputs["DEEPSEEK_API_KEY"], SECRET)
            self.assertEqual(Path(inputs["IMAGE_PATH"]).read_bytes(), runner.png_bytes())
            for name in ("IMAGE_URL", "IMAGE_FILE_ID", "VIDEO_PATH", "VIDEO_URL"):
                self.assertNotIn(name, inputs, name)

    def test_safe_parameters_drop_unexpected_private_nested_content(self):
        payload = {
            "messages": [{"role": "user", "content": PRIVATE}], "api_key": SECRET,
            "thinking": {"type": "enabled", "keep": "all", "unrecognized": PRIVATE},
            "stream_options": {"include_usage": True, "private_debug": SECRET},
            "reasoning": {"effort": "medium", "opaque": PRIVATE},
            "response_format": {"type": "json_schema", "json_schema": {"name": PRIVATE}},
            "tool_choice": {"type": "function", "function": {"name": PRIVATE}},
            "max_tokens": 2048, "temperature": 0.6,
        }
        safe = runner.safe_parameters(payload)
        serialized = json.dumps(safe)
        self.assertNotIn(PRIVATE, serialized)
        self.assertNotIn(SECRET, serialized)
        self.assertEqual(safe["max_tokens"], 2048)
        self.assertEqual(safe["temperature"], 0.6)
        self.assertEqual(safe["thinking"]["type"], "enabled")
        self.assertTrue(safe["stream_options"]["include_usage"])
        for name in ("reasoning_effort", "tool_choice", "max_tokens", "enable_thinking"):
            self.assertNotIn(SECRET, json.dumps(runner.safe_parameters({name: SECRET})))

    def test_request_record_never_saves_messages_headers_query_or_file_ids(self):
        record = runner.request_record(request(
            "https://api.deepseek.com/chat/completions?api_key=" + SECRET,
            {"model": "deepseek-flash", "messages": [{"content": PRIVATE}], "stream": True},
        ))
        self.assertEqual(record["requested_model"], "deepseek-flash")
        self.assertTrue(record["parameters"]["stream"])
        for value in (SECRET, PRIVATE, "authorization", "messages"):
            self.assertNotIn(value, json.dumps(record))
        for path in ("/files/private-file-id/content", "/v1/files/private-file-id/content", "/beta/files/private-file-id"):
            with self.subTest(path=path):
                redacted = runner.request_record(request("https://api.deepseek.com" + path))
                self.assertNotIn("private-file-id", json.dumps(redacted))

    def test_observe_json_only_records_counts_enums_and_numeric_usage(self):
        record = {}
        runner.observe_json(record, {
            "model": "deepseek-flash", "id": "private-response-id",
            "error": {"message": PRIVATE, "api_key": SECRET},
            "base_resp": {"status_code": 0, "status_msg": PRIVATE},
            "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10, "private": SECRET},
            "choices": [{"finish_reason": "tool_calls", "message": {
                "content": PRIVATE, "reasoning_content": SECRET,
                "tool_calls": [{"id": "private-tool-id", "function": {"arguments": PRIVATE}}],
            }}],
        })
        self.assertEqual(record["content_chars"], len(PRIVATE))
        self.assertEqual(record["finish_reasons"], ["tool_calls"])
        self.assertTrue(record["has_tool_calls"])
        self.assertEqual(record["usage"], {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10})
        self.assertEqual(record["business_status"], 0)
        for value in (SECRET, PRIVATE, "private-response-id", "private-tool-id", "status_msg", "arguments"):
            self.assertNotIn(value, json.dumps(record))

    def test_usage_rejects_boolean_negative_and_non_integer_counts(self):
        record = {}
        runner.observe_json(record, {"usage": {
            "prompt_tokens": True, "completion_tokens": -1, "total_tokens": "10",
            "input_tokens": 2.5, "output_tokens": 0,
        }})
        self.assertEqual(record["usage"], {"output_tokens": 0})

    def test_only_whitelisted_provider_error_codes_are_recorded(self):
        for code in (1302, "1305", 1308, "1113", 429, "rate_limit_exceeded", "insufficient_quota"):
            with self.subTest(code=code):
                record = {}
                runner.observe_json(record, {"error": {"code": code, "message": PRIVATE, "id": SECRET}})
                self.assertEqual(record, {"provider_error_code": str(code)})
        for code in (SECRET, PRIVATE, "unknown_error", True, [1302], {"private": SECRET}):
            with self.subTest(rejected=code):
                record = {}
                runner.observe_json(record, {"error": {"code": code, "message": PRIVATE}})
                self.assertEqual(record, {})

    def test_observer_does_not_change_execution_on_malformed_vendor_json(self):
        for data in (
            {"choices": [None]}, {"choices": ["not-a-choice"]}, {"choices": "bad"},
            {"choices": [{"message": "not-a-message"}]},
            {"object": "response", "status": "completed", "output": [{"content": [{"type": "output_text", "text": 123}]}]},
        ):
            for sse in (False, True):
                with self.subTest(data=data, sse=sse):
                    record = {}
                    observer = runner.BodyObserver(record, sse=sse)
                    raw = json.dumps(data).encode()
                    observer.feed(b"data: " + raw + b"\n\n" if sse else raw)
                    observer.finish()
                    self.assertEqual(observer.buffer, b"")

    def test_observer_reads_chunked_json_and_sse_without_retaining_body(self):
        payload = {"model": "deepseek-flash", "choices": [{"finish_reason": "stop", "message": {"content": "红色" + PRIVATE}}], "usage": {"total_tokens": 5}}
        for sse in (False, True):
            with self.subTest(sse=sse):
                body = json.dumps(payload, ensure_ascii=False).encode()
                wire = b": keepalive\r\ndata: " + body + b"\r\n\r\ndata: [DONE]\r\n\r\n" if sse else body
                record = {}
                observer = runner.BodyObserver(record, sse=sse)
                for offset in range(0, len(wire), 3):
                    observer.feed(wire[offset:offset + 3])
                observer.finish()
                self.assertEqual(record["content_chars"], len("红色" + PRIVATE))
                self.assertEqual(record["finish_reasons"], ["stop"])
                self.assertEqual(record["usage"], {"total_tokens": 5})
                self.assertNotIn(PRIVATE, json.dumps(record))
                self.assertEqual(observer.buffer, b"")
                if sse:
                    self.assertTrue(record["sse_done"])

    def test_sse_done_at_eof_without_final_newline_is_observed_once(self):
        record = {}
        observer = runner.BodyObserver(record, sse=True)
        observer.feed(b'data: {"choices":[{"finish_reason":"stop","delta":{"content":"ok"}}]}\n\n')
        observer.feed(b"data: [DO")
        observer.feed(b"NE]")
        self.assertNotIn("sse_done", record)
        observer.finish()
        observer.finish()
        self.assertTrue(record["sse_done"])
        self.assertEqual(record["content_chars"], 2)
        self.assertEqual(record["finish_reasons"], ["stop"])
        self.assertEqual(observer.buffer, b"")

    def test_stream_requires_terminal_event_or_actual_transport_eof_and_explicit_stop(self):
        record = {"http_status": 200, "parameters": {"stream": True}, "finish_reasons": ["stop"], "content_chars": 2}
        self.assertFalse(runner.completion_succeeded(record))
        self.assertTrue(runner.completion_succeeded({**record, "transport_eof": True}))
        self.assertFalse(runner.completion_succeeded({**record, "transport_eof": True, "finish_reasons": []}))
        self.assertFalse(runner.completion_succeeded({**record, "transport_eof": True, "finish_reasons": ["length"]}))

    def test_close_does_not_turn_an_unterminated_partial_line_into_done(self):
        record = {"http_status": 200, "parameters": {"stream": True}}
        observer = runner.BodyObserver(record, sse=True)
        observer.feed(b'data: {"choices":[{"finish_reason":"stop","delta":{"content":"ok"}}]}\n\ndata: [DONE]')
        observer.finish(eof=False)
        self.assertNotIn("sse_done", record)
        self.assertFalse(runner.completion_succeeded(record))
        self.assertEqual(observer.buffer, b"")

    def test_responses_metadata_never_contains_output_text_or_ids(self):
        record = {}
        runner.observe_json(record, {
            "object": "response", "status": "completed", "id": "private-response-id",
            "output": [{"id": "private-output-id", "content": [{"type": "output_text", "text": PRIVATE}]}],
            "usage": {"input_tokens": 2, "output_tokens": 3, "total_tokens": 5},
        })
        self.assertEqual(record["response_status"], "completed")
        self.assertEqual(record["content_chars"], len(PRIVATE))
        self.assertNotIn(PRIVATE, json.dumps(record))
        self.assertNotIn("private-response-id", json.dumps(record))
        self.assertNotIn("private-output-id", json.dumps(record))

    def execute_with_metadata(self, requests, exit_code=0, *, vendor="deepseek"):
        relative = "models/deepseek/deepseek-flash/examples/01_basic.py" if vendor != "shared" else "examples/02_one_for_all.py"
        entry = {"path": relative, "vendor": vendor, "model_id": "deepseek-flash" if vendor != "shared" else "multiple", "required_keys": ["DEEPSEEK_API_KEY"], "capability": "chat"}
        requests = [{
            "method": "POST", "endpoint": "https://api.deepseek.com/chat/completions",
            "transport": "real_httpx", **record,
        } for record in requests]
        if vendor != "shared":
            requests = [{"requested_model": "deepseek-flash", **record} for record in requests]
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)

            def subprocess_result(command, **kwargs):
                telemetry = Path(command[command.index("--telemetry") + 1])
                telemetry.write_text(json.dumps({"exit_code": exit_code, "requests": requests}), encoding="utf-8")
                return types.SimpleNamespace(returncode=exit_code, stdout=PRIVATE.encode(), stderr=SECRET.encode())

            with patch.object(runner.subprocess, "run", side_effect=subprocess_result):
                return runner.execute_entry(entry, {"DEEPSEEK_API_KEY": SECRET}, folder, 5)

    def test_zero_exit_without_observed_python_http_cannot_pass(self):
        result = self.execute_with_metadata([])
        self.assertNotEqual(result["status"], "passed")
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertNotIn(PRIVATE, json.dumps(result))

    def test_normal_final_completion_with_zero_exit_can_pass(self):
        result = self.execute_with_metadata([
            {"http_status": 200, "finish_reasons": ["stop"], "content_chars": 20},
        ])
        self.assertEqual(result["status"], "passed")
        self.assertNotIn("tested_at", result)
        self.assertNotIn("duration_seconds", result)

    def test_new_report_uses_random_evidence_identity_without_test_times_or_durations(self):
        result = self.execute_with_metadata([
            {"http_status": 200, "finish_reasons": ["stop"], "content_chars": 20},
        ])
        with patch.object(runner.importlib.metadata, "version", return_value="fixture-sdk"):
            report = runner.make_report([result])
            next_report = runner.make_report()
        self.assertEqual(report["schema_version"], 2)
        identity = UUID(report["evidence_id"])
        self.assertEqual(identity.version, 4)
        self.assertEqual(identity.variant, RFC_4122)
        self.assertEqual(str(identity), report["evidence_id"])
        self.assertNotEqual(report["evidence_id"], next_report["evidence_id"])
        self.assertEqual(report["results"], [result])
        self.assertEqual(report["runtime"]["openai"], "fixture-sdk")
        self.assertIs(report["privacy"]["test_timestamps_saved"], False)
        self.assertIs(report["privacy"]["duration_saved"], False)
        self.assertFalse(any(report["privacy"].values()))

        def check_private_fields(value):
            if isinstance(value, dict):
                self.assertFalse({"tested_at", "duration_seconds"} & set(value))
                for child in value.values():
                    check_private_fields(child)
            elif isinstance(value, list):
                for child in value:
                    check_private_fields(child)

        check_private_fields(report)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "fixture-report.json"
            runner.write_report(destination, report)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), report)

    def test_execution_cli_keeps_timeout_and_delay_controls_without_recording_elapsed_time(self):
        entries = runner.discover()[:2]
        results = [{**entry, "status": "passed", "requests": []} for entry in entries]
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "fixture-report.json"
            with patch.object(sys, "argv", [str(SCRIPT), "--execute", "--report", str(destination), "--timeout", "17", "--delay", "0.5"]), \
                    patch.object(runner, "discover", return_value=entries), \
                    patch.object(runner, "credentials", return_value={}), \
                    patch.object(runner, "prepare_inputs", side_effect=lambda _directory, env: env), \
                    patch.object(runner, "execute_entry", side_effect=results) as execute, \
                    patch.object(runner.time, "sleep") as sleep, \
                    patch.object(runner.importlib.metadata, "version", return_value="fixture-sdk"), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(), 0)
            self.assertEqual([call.args[-1] for call in execute.call_args_list], [17, 17])
            sleep.assert_called_once_with(0.5)
            report = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["summary"]["passed"], 2)
        self.assertNotIn("tested_at", report)
        self.assertNotIn("duration_seconds", report)
        self.assertEqual(report["results"], results)

    def test_execution_cli_defaults_to_local_only_uuid_report_without_printing_private_metadata(self):
        entry = runner.discover()[0]
        result = {**entry, "status": "passed", "requests": [{"http_status": 200, "finish_reasons": ["stop"], "content_chars": 5}], "source_sha256": {entry["path"]: "fixture-private-hash"}}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(runner, "ROOT", root), patch.object(sys, "argv", [str(SCRIPT), "--execute"]), \
                    patch.object(runner, "discover", return_value=[entry]), \
                    patch.object(runner, "credentials", return_value={}), \
                    patch.object(runner, "prepare_inputs", side_effect=lambda _directory, env: env), \
                    patch.object(runner, "execute_entry", return_value=result), \
                    patch.object(runner.importlib.metadata, "version", return_value="fixture-sdk"), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(runner.main(), 0)
            files = list((root / ".local/evidence/example-files").glob("*.json"))
            self.assertEqual(len(files), 1)
            report = json.loads(files[0].read_text(encoding="utf-8"))
            self.assertEqual(files[0].stem, report["evidence_id"])
            self.assertEqual(UUID(files[0].stem).version, 4)
            for private in (report["evidence_id"], "fixture-private-hash", "fixture-sdk", str(root), '"requests"', '"summary"'):
                self.assertNotIn(private, output.getvalue())
            self.assertEqual([path for path in root.iterdir()], [root / ".local"])

    def test_public_repository_report_destination_is_rejected_before_credentials_or_file_writes(self):
        entry = runner.discover()[0]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "verification/not-created.json"
            with patch.object(runner, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "report_destination_inside_public_repository"):
                    runner.write_report(destination, {"safe": True})
                with patch.object(sys, "argv", [str(SCRIPT), "--execute", "--report", str(destination)]), \
                        patch.object(runner, "discover", return_value=[entry]), \
                        patch.object(runner, "credentials") as load, contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        runner.main()
                    self.assertEqual(error.exception.code, 2)
                    load.assert_not_called()
            self.assertFalse(destination.parent.exists())

    def test_explicit_private_repository_destination_remains_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / ".local/evidence/custom.json"
            with patch.object(runner, "ROOT", root):
                runner.write_report(destination, {"safe": True})
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), {"safe": True})

    def test_private_directory_symlink_cannot_redirect_a_report_to_public_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            public = root / "docs"
            public.mkdir()
            try:
                (root / ".local").symlink_to(public, target_is_directory=True)
            except OSError as error:
                if getattr(error, "winerror", None) == 1314:
                    self.skipTest("Windows account cannot create symbolic links")
                raise
            destination = root / ".local/evidence/not-created.json"
            with patch.object(runner, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "report_destination_inside_public_repository"):
                    runner.write_report(destination, {"safe": True})
            self.assertFalse((public / "evidence").exists())

    def test_process_timeout_still_limits_execution_without_recording_duration(self):
        entry = runner.discover()[0]
        env = {key: SECRET for key in entry["required_keys"]}
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            runner.subprocess, "run", side_effect=runner.subprocess.TimeoutExpired("fixture", 7),
        ) as execute:
            result = runner.execute_entry(entry, env, Path(temporary), 7)
        self.assertEqual(execute.call_args.kwargs["timeout"], 7)
        self.assertEqual(result["status"], "timeout")
        self.assertNotIn("tested_at", result)
        self.assertNotIn("duration_seconds", result)

    def test_streaming_requires_protocol_done_not_just_stop_then_eof(self):
        complete = {
            "http_status": 200, "finish_reasons": ["stop"], "content_chars": 20,
            "parameters": {"stream": True}, "sse_done": True,
        }
        self.assertEqual(self.execute_with_metadata([complete])["status"], "passed")
        no_done = {key: value for key, value in complete.items() if key != "sse_done"}
        self.assertNotEqual(self.execute_with_metadata([no_done])["status"], "passed")

    def test_error_metadata_cannot_be_promoted_to_passed_by_zero_exit(self):
        for record in (
            {"http_status": 500},
            {"http_status": 429},
            {"http_status": 200, "finish_reasons": ["length"], "content_chars": 30},
            {"http_status": 200, "finish_reasons": ["stop"], "content_chars": 0},
            {"http_status": 200, "finish_reasons": ["stop"], "content_chars": 20, "telemetry_overflow": True},
            {"http_status": 200, "finish_reasons": ["stop"], "content_chars": 20, "telemetry_error": True},
            {"http_status": 200, "finish_reasons": ["length", "stop"], "content_chars": 20},
            {"http_status": 200, "finish_reasons": ["stop"], "content_chars": 20, "has_tool_calls": True},
            {"http_status": 200, "finish_reasons": ["stop"], "content_chars": 20, "business_status": 1004},
        ):
            with self.subTest(record=record):
                result = self.execute_with_metadata([record])
                self.assertNotEqual(result["status"], "passed")

    def test_shared_unknown_models_cannot_replace_expected_six_models(self):
        records = [{"http_status": 200, "content_chars": 10, "finish_reasons": ["stop"], "requested_model": "unregistered-" + str(i)} for i in range(6)]
        self.assertNotEqual(self.execute_with_metadata(records, vendor="shared")["status"], "passed")

    def test_shared_default_target_cannot_be_satisfied_by_an_archived_flash_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            references = root / "skills/model-manual/references"
            (references / "models").mkdir(parents=True)
            for model in ("glm-4.7", "glm-4.7-flash"):
                (references / "models" / f"{model}.json").write_text(json.dumps({"vendor": "zhipu", "model_id": model}), encoding="utf-8")
            (references / "vendors.json").write_text(json.dumps({"vendors": {"zhipu": {"default_model": "glm-4.7"}}}), encoding="utf-8")
            entry = {"vendor": "shared", "model_id": "multiple"}
            old = {"requested_model": "glm-4.7-flash", "http_status": 200, "finish_reasons": ["stop"], "content_chars": 5}
            new = {**old, "requested_model": "glm-4.7"}
            with patch.object(runner, "ROOT", root):
                self.assertEqual(runner.determine_status(entry, {"exit_code": 0, "requests": [old]}, 0), "failed")
                self.assertEqual(runner.determine_status(entry, {"exit_code": 0, "requests": [new]}, 0), "passed")
                mismatch = {**new, "served_model": "glm-4.7-flash"}
                self.assertEqual(runner.determine_status(entry, {"exit_code": 0, "requests": [mismatch]}, 0), "failed")
                self.assertEqual(runner.determine_status(entry, {"exit_code": 0, "requests": [mismatch, new]}, 0), "failed")

    def test_paid_glm_served_identity_conflict_is_rejected_without_breaking_other_aliases(self):
        record = {"requested_model": "glm-4.7", "served_model": "glm-4.7-flash", "http_status": 200, "finish_reasons": ["stop"], "content_chars": 5}
        self.assertFalse(runner.completion_succeeded(record))
        self.assertEqual(runner.determine_status({"vendor": "zhipu", "model_id": "glm-4.7"}, {"exit_code": 0, "requests": [record]}, 0), "failed")
        self.assertTrue(runner.completion_succeeded({**record, "served_model": "glm-4.7"}))
        self.assertTrue(runner.completion_succeeded({key: value for key, value in record.items() if key != "served_model"}))
        self.assertTrue(runner.completion_succeeded({**record, "requested_model": "deepseek-flash", "served_model": "deepseek-v4-flash"}))

    def test_http_429_and_nonzero_exit_are_classified_without_raw_error(self):
        result = self.execute_with_metadata([{"http_status": 429}], exit_code=1)
        self.assertEqual(result["status"], "rate_limited")
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertNotIn(PRIVATE, json.dumps(result))

    def test_missing_key_does_not_spawn_or_claim_passed(self):
        entry = runner.discover()[0]
        with tempfile.TemporaryDirectory() as temporary, patch.object(runner.subprocess, "run") as execute:
            result = runner.execute_entry(entry, {}, Path(temporary), 1)
        execute.assert_not_called()
        self.assertEqual(result["status"], "missing_key")
        self.assertEqual(result["missing_key_names"], entry["required_keys"])
        self.assertNotIn("tested_at", result)
        self.assertNotIn("duration_seconds", result)

    def test_write_report_does_not_overwrite_historical_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.json"
            runner.write_report(path, {"version": 1})
            with self.assertRaises(FileExistsError):
                runner.write_report(path, {"version": 2})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"version": 1})

    def test_write_report_rejects_flat_and_nested_time_fields_before_touching_destination(self):
        for field, value in (("tested_at", "fixture-time"), ("duration_seconds", 1.25)):
            for payload in ({field: value}, {"results": [{"requests": [{"response": {field: value}}]}]}):
                with self.subTest(field=field, payload=payload), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    destination = root / "not-created" / "report.json"
                    original = json.dumps(payload, sort_keys=True)
                    with self.assertRaisesRegex(ValueError, "report_contains_test_timestamp_or_duration"):
                        runner.write_report(destination, payload)
                    self.assertFalse(destination.parent.exists())
                    self.assertFalse(destination.exists())
                    self.assertEqual(json.dumps(payload, sort_keys=True), original)
                    existing = root / "existing.json"
                    runner.write_report(existing, {"original": True})
                    before = existing.read_bytes()
                    with self.assertRaises(ValueError):
                        runner.write_report(existing, payload)
                    self.assertEqual(existing.read_bytes(), before)

    def test_write_report_rejects_time_fields_carried_from_old_results_without_mutating_them(self):
        old_results = [{"status": "passed", "duration_seconds": 0.5, "requests": []}]
        with patch.object(runner.importlib.metadata, "version", return_value="fixture-sdk"):
            report = runner.make_report(old_results)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "not-created" / "report.json"
            with self.assertRaises(ValueError):
                runner.write_report(destination, report)
            self.assertFalse(destination.parent.exists())
        self.assertEqual(old_results[0]["duration_seconds"], 0.5)


@unittest.skipUnless(SDK_AVAILABLE, "requires installed real openai/httpx; no fake SDK fallback")
class ActualSDKObservationTests(unittest.TestCase):
    def run_real_sdk_fixture(self, source, handler, observer_failure=False):
        import httpx

        with tempfile.TemporaryDirectory() as temporary:
            path, telemetry = Path(temporary) / "sdk_fixture.py", Path(temporary) / "telemetry.json"
            path.write_text(source, encoding="utf-8")
            old_path, old_disable = list(sys.path), logging.root.manager.disable
            try:
                with contextlib.ExitStack() as stack:
                    stack.enter_context(patch.object(httpx.HTTPTransport, "handle_request", handler))
                    stack.enter_context(patch.dict(os.environ, {}, clear=True))
                    if observer_failure:
                        stack.enter_context(patch.object(runner, "observe_json", side_effect=RuntimeError(PRIVATE + SECRET)))
                    code = runner.child(path, telemetry)
            finally:
                sys.path[:] = old_path
                logging.disable(old_disable)
            return code, json.loads(telemetry.read_text(encoding="utf-8"))

    def test_normal_python_exit_does_not_fake_or_hide_request_success(self):
        def no_network(transport, request):
            raise AssertionError("fixture must not send any request")

        for statement, expected in (("raise SystemExit(0)", 0), ("raise SystemExit()", 0),
                                    ("raise SystemExit(1)", 1), (f"raise SystemExit({PRIVATE!r})", 1),
                                    ("raise SystemExit(0.0)", 1)):
            with self.subTest(statement=statement):
                code, report = self.run_real_sdk_fixture(statement, no_network)
                self.assertEqual(code, expected)
                self.assertEqual(report["exit_code"], expected)
                self.assertEqual(report["requests"], [])
                # Process success without actual HTTP evidence cannot become a pass.
                self.assertEqual(runner.determine_status({"vendor": "deepseek", "model_id": "deepseek-flash"}, report, code), "failed")
                self.assertNotIn(PRIVATE, json.dumps(report))

    def test_successful_main_exit_preserves_actual_sdk_http_observation(self):
        import httpx

        payload = {"model": "deepseek-flash", "choices": [{"index": 0, "finish_reason": "stop",
                   "message": {"role": "assistant", "content": PRIVATE}}]}

        def handler(transport, request):
            return httpx.Response(200, stream=httpx.ByteStream(json.dumps(payload).encode()),
                                  headers={"content-type": "application/json"}, request=request)

        source = ("from openai import OpenAI\n"
                  f"client = OpenAI(api_key={SECRET!r}, base_url='https://api.deepseek.com', max_retries=0)\n"
                  "client.chat.completions.create(model='deepseek-flash', messages=[{'role':'user','content':'fixture'}])\n"
                  "raise SystemExit(0)\n")
        code, report = self.run_real_sdk_fixture(source, handler)
        self.assertEqual(code, 0)
        self.assertEqual(runner.determine_status({"vendor": "deepseek", "model_id": "deepseek-flash"}, report, code), "passed")
        self.assertEqual(len(report["requests"]), 1)
        for value in (PRIVATE, SECRET):
            self.assertNotIn(value, json.dumps(report))

    def test_compressed_actual_sdk_chat_fim_and_sse_keep_independent_decoders(self):
        import httpx

        header = (
            "from openai import OpenAI\n"
            f"client = OpenAI(api_key={SECRET!r}, base_url='https://api.deepseek.com', max_retries=0)\n"
        )
        chat = {"id": "private-id", "object": "chat.completion", "model": "deepseek-flash", "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": PRIVATE}}], "usage": {"total_tokens": 5}}
        fim = {"id": "private-id", "object": "text_completion", "model": "deepseek-flash", "choices": [{"index": 0, "finish_reason": "stop", "text": PRIVATE}], "usage": {"total_tokens": 5}}
        event = {"id": "private-id", "object": "chat.completion.chunk", "model": "deepseek-flash", "choices": [{"index": 0, "delta": {"content": PRIVATE}, "finish_reason": "stop"}], "usage": {"total_tokens": 5}}
        bodies = {
            "chat": json.dumps(chat).encode(), "fim": json.dumps(fim).encode(),
            "sse": b"data: " + json.dumps(event).encode() + b"\n\ndata: [DONE]",
        }
        sources = {
            "chat": header + f"result = client.chat.completions.create(model='deepseek-flash', messages=[{{'role':'user','content':'fixture'}}])\nassert result.choices[0].message.content == {PRIVATE!r}\n",
            "fim": header + f"result = client.completions.create(model='deepseek-flash', prompt='fixture')\nassert result.choices[0].text == {PRIVATE!r}\n",
            "sse": header + "stream = client.chat.completions.create(model='deepseek-flash', messages=[{'role':'user','content':'fixture'}], stream=True)\nparts = [chunk.choices[0].delta.content or '' for chunk in stream if chunk.choices]\n" + f"assert ''.join(parts) == {PRIVATE!r}\n",
        }
        for kind in bodies:
            for coding, compress in (("gzip", gzip.compress), ("deflate", zlib.compress)):
                with self.subTest(kind=kind, coding=coding):
                    encoded = compress(bodies[kind])
                    emitted = []

                    class RawFixture(httpx.SyncByteStream):
                        def __iter__(self):
                            for index in range(0, len(encoded), 5):
                                chunk = encoded[index:index + 5]
                                emitted.append(chunk)
                                yield chunk

                    def handler(transport, request):
                        return httpx.Response(200, stream=RawFixture(), headers={
                            "content-type": "text/event-stream" if kind == "sse" else "application/json",
                            "content-encoding": coding,
                        }, request=request)

                    code, report = self.run_real_sdk_fixture(sources[kind], handler)
                    self.assertEqual(code, 0, report)
                    self.assertEqual(b"".join(emitted), encoded)
                    record = report["requests"][0]
                    self.assertEqual(record["content_encoding"], coding)
                    self.assertEqual(record["content_chars"], len(PRIVATE))
                    self.assertEqual(record["finish_reasons"], ["stop"])
                    self.assertEqual(record["usage"], {"total_tokens": 5})
                    self.assertNotIn("telemetry_error", record)
                    if kind == "sse":
                        self.assertTrue(record["sse_done"])
                    self.assertTrue(runner.completion_succeeded(record))
                    for value in (PRIVATE, SECRET, "private-id"):
                        self.assertNotIn(value, json.dumps(report))

    def test_observer_failure_does_not_change_real_sdk_response_or_raw_error(self):
        import httpx

        payload = {"id": "fixture-id", "object": "chat.completion", "model": "deepseek-flash", "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": PRIVATE}}]}

        def handler(transport, request):
            return httpx.Response(200, stream=httpx.ByteStream(json.dumps(payload).encode()), headers={"content-type": "application/json"}, request=request)

        source = (
            "from openai import OpenAI\n"
            f"client = OpenAI(api_key={SECRET!r}, base_url='https://api.deepseek.com', max_retries=0)\n"
            "result = client.chat.completions.create(model='deepseek-flash', messages=[{'role':'user','content':'fixture'}])\n"
            f"assert result.choices[0].message.content == {PRIVATE!r}\n"
        )
        code, report = self.run_real_sdk_fixture(source, handler, observer_failure=True)
        self.assertEqual(code, 0, "observer failure must not turn the original script into failure")
        record = report["requests"][0]
        self.assertTrue(record["telemetry_error"])
        self.assertFalse(runner.completion_succeeded(record))
        self.assertNotIn(SECRET, json.dumps(report))
        self.assertNotIn(PRIVATE, json.dumps(report))

    def test_child_observes_actual_openai_sdk_with_only_http_response_fixture(self):
        import httpx
        import openai

        self.assertIsNotNone(getattr(openai, "__file__", None))
        response = {
            "id": "private-response-id", "object": "chat.completion", "model": "deepseek-flash",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": PRIVATE, "reasoning_content": SECRET}}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
        }
        observed = []

        def only_http_fixture(transport, request):
            observed.append(json.loads(request.read()))
            # HTTPTransport returns an unread response stream, unlike json=...,
            # which httpx eagerly buffers before the runner can observe it.
            return httpx.Response(
                200, stream=httpx.ByteStream(json.dumps(response).encode()),
                headers={"content-type": "application/json"}, request=request,
            )

        with tempfile.TemporaryDirectory() as temporary:
            path, telemetry = Path(temporary) / "sdk_example.py", Path(temporary) / "telemetry.json"
            path.write_text(
                "from openai import OpenAI\n"
                f"client = OpenAI(api_key={SECRET!r}, base_url='https://api.deepseek.com', max_retries=0)\n"
                f"result = client.chat.completions.create(model='deepseek-flash', messages=[{{'role':'user','content':{PRIVATE!r}}}], extra_body={{'thinking':{{'type':'disabled'}}}})\n"
                f"assert result.choices[0].message.content == {PRIVATE!r}\n"
                "assert result.choices[0].finish_reason == 'stop'\n", encoding="utf-8",
            )
            old_path, old_disable = list(sys.path), logging.root.manager.disable
            try:
                with patch.object(httpx.HTTPTransport, "handle_request", only_http_fixture), patch.dict(os.environ, {}, clear=True):
                    code = runner.child(path, telemetry)
            finally:
                sys.path[:] = old_path
                logging.disable(old_disable)
            report = json.loads(telemetry.read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0]["thinking"], {"type": "disabled"})
        self.assertNotIn("extra_body", observed[0])
        self.assertEqual(len(report["requests"]), 1)
        metadata = report["requests"][0]
        self.assertEqual(metadata["transport"], "real_httpx")
        self.assertEqual(metadata["http_status"], 200)
        self.assertEqual(metadata["requested_model"], "deepseek-flash")
        self.assertEqual(metadata["content_chars"], len(PRIVATE))
        for value in (SECRET, PRIVATE, "private-response-id"):
            self.assertNotIn(value, json.dumps(report))

    def test_child_observes_real_sdk_sse_and_discards_raw_api_error(self):
        import httpx

        events = [
            {"id": "private-stream-id", "object": "chat.completion.chunk", "model": "deepseek-flash", "choices": [{"index": 0, "delta": {"content": PRIVATE, "reasoning_content": SECRET}, "finish_reason": None}]},
            {"id": "private-stream-id", "object": "chat.completion.chunk", "model": "deepseek-flash", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
            {"id": "private-stream-id", "object": "chat.completion.chunk", "model": "deepseek-flash", "choices": [], "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}},
        ]
        wire = b"".join(b"data: " + json.dumps(event).encode() + b"\n\n" for event in events) + b"data: [DONE]\n\n"

        class ChunkedResponse(httpx.SyncByteStream):
            def __iter__(self):
                for index in range(0, len(wire), 7):
                    yield wire[index:index + 7]

        def sse_fixture(transport, request):
            body = json.loads(request.read())
            self.assertTrue(body["stream"])
            return httpx.Response(200, stream=ChunkedResponse(), headers={"content-type": "text/event-stream"}, request=request)

        def error_fixture(transport, request):
            error = {"error": {"type": "invalid_request_error", "message": PRIVATE + SECRET, "request_id": "private-error-id"}}
            return httpx.Response(400, stream=httpx.ByteStream(json.dumps(error).encode()), headers={"content-type": "application/json"}, request=request)

        for failed in (False, True):
            with self.subTest(failed=failed), tempfile.TemporaryDirectory() as temporary:
                path, telemetry = Path(temporary) / "sdk_stream.py", Path(temporary) / "telemetry.json"
                path.write_text(
                    "from openai import OpenAI\n"
                    f"client = OpenAI(api_key={SECRET!r}, base_url='https://api.deepseek.com', max_retries=0)\n"
                    "stream = client.chat.completions.create(model='deepseek-flash', messages=[{'role':'user','content':'fixture'}], stream=True, stream_options={'include_usage':True})\n"
                    "parts = []\n"
                    "reason = None\n"
                    "for chunk in stream:\n"
                    "    if chunk.choices:\n"
                    "        choice = chunk.choices[0]\n"
                    "        parts.append(choice.delta.content or '')\n"
                    "        reason = choice.finish_reason or reason\n"
                    "assert reason == 'stop'\n"
                    f"assert ''.join(parts) == {PRIVATE!r}\n", encoding="utf-8",
                )
                old_path, old_disable = list(sys.path), logging.root.manager.disable
                stdout, stderr = io.StringIO(), io.StringIO()
                try:
                    with patch.object(httpx.HTTPTransport, "handle_request", error_fixture if failed else sse_fixture), patch.dict(
                        os.environ, {}, clear=True,
                    ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        code = runner.child(path, telemetry)
                finally:
                    sys.path[:] = old_path
                    logging.disable(old_disable)
                report = json.loads(telemetry.read_text(encoding="utf-8"))
                self.assertEqual(code, int(failed))
                self.assertEqual(len(report["requests"]), 1)
                metadata = report["requests"][0]
                self.assertTrue(metadata["parameters"]["stream"])
                self.assertEqual(metadata["http_status"], 400 if failed else 200)
                if failed:
                    self.assertEqual(report["error_type"], "BadRequestError")
                    self.assertEqual(report["http_status"], 400)
                else:
                    self.assertTrue(metadata["sse_done"])
                    self.assertEqual(metadata["finish_reasons"], ["stop"])
                    self.assertEqual(metadata["usage"]["total_tokens"], 5)
                    self.assertEqual(metadata["content_chars"], len(PRIVATE))
                serialized = json.dumps(report) + stdout.getvalue() + stderr.getvalue()
                for value in (SECRET, PRIVATE, "private-stream-id", "private-error-id"):
                    self.assertNotIn(value, serialized)


if __name__ == "__main__":
    unittest.main()
