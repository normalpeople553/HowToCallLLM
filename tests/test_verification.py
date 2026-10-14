"""验证器的离线边界/脱敏测试；不读取密钥或发送模型请求。"""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import provider_verify as verify


SECRET = "sentinel-sensitive-content-never-persist"


def completion(content="收到", finish="stop", reasoning=None, calls=None, reasoning_tokens=None):
    return {
        "id": SECRET,
        "choices": [{"finish_reason": finish, "message": {"role": "assistant", "content": content, "reasoning_content": reasoning, "tool_calls": calls}}],
        "usage": {"prompt_tokens": 8, "completion_tokens": 15, "total_tokens": 23, "completion_tokens_details": {"reasoning_tokens": reasoning_tokens}},
    }


def tool_call(arguments='{"city":"杭州"}', name="get_weather"):
    return {"id": SECRET, "type": "function", "function": {"name": name, "arguments": arguments}}


def stream_chunk(content=None, finish=None, usage=None, choices=True):
    return {"choices": [{"delta": {"content": content}, "finish_reason": finish}] if choices else [], "usage": usage}


class MockStream:
    def __init__(self, chunks):
        self.chunks, self.closed = chunks, False

    def __iter__(self):
        return iter(self.chunks)

    def close(self):
        self.closed = True


class ProviderError(Exception):
    def __init__(self, status):
        self.status_code = status
        self.body = {"error": {"code": "1305" if status == 429 else SECRET, "message": SECRET}}
        super().__init__(SECRET)


class CompletionTests(unittest.TestCase):
    def test_nonempty_truncated_answer_is_rejected(self):
        with self.assertRaisesRegex(verify.VerificationFailure, "output_truncated"):
            verify.require_content(completion(content="有正文也不完整", finish="length"))

    def test_text_requires_stop_and_nonempty_content(self):
        for reason in (None, "tool_calls", "content_filter", "function_call", SECRET):
            with self.subTest(reason=reason):
                with self.assertRaises(verify.VerificationFailure):
                    verify.require_content(completion(finish=reason))
        with self.assertRaisesRegex(verify.VerificationFailure, "empty_content"):
            verify.require_content(completion(content=" "))
        with self.assertRaisesRegex(verify.VerificationFailure, "unexpected_choice_count"):
            verify.require_content({"choices": []})
        self.assertEqual(verify.require_content(completion()), "收到")

    def test_tools_require_matching_reason_and_calls(self):
        calls = [tool_call()]
        self.assertEqual(verify.require_tools(completion(None, "tool_calls", calls=calls)), calls)
        for response in (completion(None, "stop", calls=calls), completion(None, "tool_calls", calls=[]), completion(None, "length", calls=calls)):
            with self.assertRaises(verify.VerificationFailure):
                verify.require_tools(response)

    def test_reasoning_characters_are_not_reported_as_tokens(self):
        data = verify.usage_metadata(completion(reasoning=SECRET))
        self.assertIsNone(data["reasoning_tokens"])
        self.assertEqual(verify.usage_metadata(completion(reasoning=SECRET, reasoning_tokens=9))["reasoning_tokens"], 9)
        self.assertNotIn("reasoning_chars", verify.completion_metadata(completion(reasoning=SECRET)))
        self.assertNotIn(SECRET, json.dumps(verify.completion_metadata(completion(content=SECRET, reasoning=SECRET))))


class StreamingTests(unittest.TestCase):
    def test_usage_only_chunk_after_stop_is_supported(self):
        usage = completion()["usage"]
        stream = MockStream([stream_chunk("收到"), stream_chunk(finish="stop"), stream_chunk(usage=usage, choices=False)])
        observation = {}
        self.assertEqual(verify.consume_stream(stream, observation), "收到")
        self.assertTrue(stream.closed)
        self.assertTrue(observation["stream_completed"])
        self.assertEqual(observation["finish_reason"], "stop")
        self.assertEqual(observation["output_tokens"], 15)

    def test_partial_stream_without_end_is_not_passed(self):
        stream = MockStream([stream_chunk("半句话")])
        observation = {}
        with self.assertRaisesRegex(verify.VerificationFailure, "missing_finish_reason"):
            verify.consume_stream(stream, observation)
        self.assertTrue(stream.closed)
        self.assertFalse(observation["stream_completed"])

    def test_length_end_is_recorded_but_rejected(self):
        observation = {}
        with self.assertRaisesRegex(verify.VerificationFailure, "output_truncated"):
            verify.consume_stream(MockStream([stream_chunk("半句话", "length")]), observation)
        self.assertEqual(observation["finish_reason"], "length")
        self.assertFalse(observation["stream_completed"])

    def test_usage_only_or_empty_body_is_not_passed(self):
        for chunks in ([stream_chunk(usage=completion()["usage"], choices=False)], [stream_chunk(finish="stop")]):
            with self.assertRaises(verify.VerificationFailure):
                verify.consume_stream(MockStream(chunks))

    def test_content_after_end_is_not_passed(self):
        with self.assertRaisesRegex(verify.VerificationFailure, "content_after_finish"):
            verify.consume_stream(MockStream([stream_chunk("收到", "stop"), stream_chunk("更多")]))


class WorkflowTests(unittest.TestCase):
    def make_runner(self, vendor="kimi", replies=()):
        client = Mock()
        client.chat.completions.create.side_effect = list(replies)
        return verify.VerificationRunner(verify.SPECS[vendor], client), client

    def run_silently(self, runner, name, test):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            runner.run(name, test)
        return runner.results[-1], output.getvalue()

    def test_zhipu_profile_targets_paid_glm_not_free_flash(self):
        self.assertEqual(verify.SPECS["zhipu"].model, "glm-4.7")
        runner, client = self.make_runner("zhipu", [completion()])
        result, _ = self.run_silently(runner, "chat_completions", runner.basic)
        self.assertEqual(client.chat.completions.create.call_args.kwargs["model"], "glm-4.7")
        self.assertEqual(result["model_id"], "glm-4.7")
        self.assertNotIn("glm-4.7-flash", json.dumps(result))

    def test_tool_arguments_are_validated_and_result_used(self):
        first = completion(None, "tool_calls", reasoning=SECRET, calls=[tool_call()])
        runner, client = self.make_runner(replies=[first, completion("杭州晴，23摄氏度")])
        result, output = self.run_silently(runner, "tool_calling", runner.tool_calling)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(client.chat.completions.create.call_count, 2)
        second = client.chat.completions.create.call_args_list[1].kwargs
        self.assertEqual(second["messages"][1]["reasoning_content"], SECRET)
        self.assertEqual(second["messages"][2]["tool_call_id"], SECRET)
        self.assertEqual(json.loads(second["messages"][2]["content"])["temperature_c"], 23)
        self.assertTrue(result["requests"][0]["response"]["tool_arguments_validated"])
        self.assertNotIn(SECRET, json.dumps(result) + output)

    def test_invalid_tool_never_reaches_execution_or_second_call(self):
        invalid = [tool_call(name="delete_all"), tool_call(arguments="[]"), tool_call(arguments='{"city":3}'), tool_call(arguments='{"city":"杭州","extra":true}'), tool_call(arguments='{"city":"北京"}'), tool_call(arguments="not json")]
        for call in invalid:
            runner, client = self.make_runner(replies=[completion(None, "tool_calls", calls=[call])])
            with self.subTest(call=call):
                result, _ = self.run_silently(runner, "tool_calling", runner.tool_calling)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(client.chat.completions.create.call_count, 1)

    def test_tool_final_truncation_or_ignored_result_fails(self):
        for final in (completion("晴23", "length"), completion("没有使用工具结果")):
            runner, _ = self.make_runner(replies=[completion(None, "tool_calls", calls=[tool_call()]), final])
            result, _ = self.run_silently(runner, "tool_calling", runner.tool_calling)
            self.assertEqual(result["status"], "failed")

    def test_vision_validates_color_without_disclosing_color_in_question(self):
        runner, client = self.make_runner(replies=[completion("red")])
        result, _ = self.run_silently(runner, "vision", runner.vision)
        self.assertEqual(result["status"], "passed")
        question = client.chat.completions.create.call_args.kwargs["messages"][0]["content"][0]["text"]
        self.assertNotIn("red", question)
        self.assertNotIn("红", question)
        runner, _ = self.make_runner(replies=[completion("收到图片")])
        result, _ = self.run_silently(runner, "vision", runner.vision)
        self.assertEqual(result["error"]["code"], "wrong_image_color")

    def test_all_five_profiles_execute_complete_mock_workflows(self):
        for vendor, spec in verify.SPECS.items():
            responses = [completion(), MockStream([stream_chunk("收到", "stop")]), completion(), completion("9.8", reasoning=SECRET, reasoning_tokens=8), completion('{"ok":true}'), completion(None, "tool_calls", calls=[tool_call()]), completion("晴，23摄氏度")]
            if spec.vision:
                responses.append(completion("red"))
            runner, client = self.make_runner(vendor, responses)
            with self.subTest(vendor=vendor), contextlib.redirect_stdout(io.StringIO()):
                results = runner.execute()
                self.assertEqual(verify.count_results(results)["failed"], 0)
                self.assertEqual(len(results), 7 if spec.vision else 6)
                self.assertGreaterEqual(client.chat.completions.create.call_count, 7)
                on = next(row for row in results if row["id"] == "thinking_enabled")
                self.assertGreaterEqual(on["requests"][0]["parameters"]["max_tokens"], 16384)

    def test_429_is_bounded_and_remaining_tests_are_skipped(self):
        runner, client = self.make_runner("zhipu", [ProviderError(429), ProviderError(429)])
        with patch.object(verify.time, "sleep") as sleep, contextlib.redirect_stdout(io.StringIO()) as output:
            results = runner.execute()
        counts = verify.count_results(results)
        self.assertEqual(client.chat.completions.create.call_count, 2)
        sleep.assert_called_once_with(1)
        self.assertEqual(counts, {"passed": 0, "failed": 0, "rate_limited": 1, "skipped": 5})
        self.assertEqual(verify.result_exit_code(counts), 2)
        self.assertEqual(results[0]["error"]["provider_code"], "1305")
        self.assertFalse(results[0]["requests"][0]["response_received"])
        self.assertNotIn(SECRET, json.dumps(results) + output.getvalue())

    def test_failure_metadata_retains_length_without_raw_data(self):
        runner, _ = self.make_runner(replies=[completion(SECRET, "length", reasoning=SECRET)])
        result, output = self.run_silently(runner, "basic", runner.basic)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["requests"][0]["response"]["finish_reason"], "length")
        self.assertNotIn(SECRET, json.dumps(result) + output)


class ReportingTests(unittest.TestCase):
    def test_default_cli_selects_all_vendors_without_reading_keys(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(verify, "load_env"), patch.object(verify, "source_metadata", return_value={}), contextlib.redirect_stdout(io.StringIO()) as output:
            status = verify.main([])
        self.assertEqual(status, 2)
        for vendor in verify.SPECS:
            self.assertIn(f"SKIPPED {vendor}/", output.getvalue())

    def test_unknown_or_duplicate_vendors_are_rejected_before_env_loading(self):
        for args in (["unknown"], ["kimi", "kimi"]):
            with self.subTest(args=args), patch.object(verify, "load_env") as load_env, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    verify.main(args)
                self.assertEqual(error.exception.code, 2)
                load_env.assert_not_called()

    def test_error_body_and_message_are_never_printed(self):
        self.assertEqual(verify.safe_error(ProviderError(401)), {"code": "authentication_failed", "http_status": 401})
        self.assertNotIn(SECRET, json.dumps(verify.safe_error(RuntimeError(SECRET))))

    def test_auth_rate_limit_server_and_timeout_are_distinct(self):
        self.assertEqual(verify.safe_error(ProviderError(429))["code"], "rate_limited")
        self.assertEqual(verify.safe_error(ProviderError(503))["code"], "server_error")
        self.assertEqual(verify.safe_error(TimeoutError(SECRET))["code"], "request_timeout")
        self.assertNotIn(SECRET, json.dumps(verify.safe_error(TimeoutError(SECRET))))

    def test_request_metadata_is_whitelisted(self):
        parameters = verify.safe_request_parameters({"messages": SECRET, "api_key": SECRET, "extra_body": {"thinking": {"type": "enabled", "secret": SECRET}, "token": SECRET}, "tools": SECRET, "tool_choice": {"type": "function", "function": {"name": SECRET}}, "max_tokens": 16384, "response_format": {"type": "json_schema", "json_schema": SECRET}})
        self.assertNotIn(SECRET, json.dumps(parameters))
        self.assertEqual(parameters["thinking"], {"type": "enabled"})
        self.assertEqual(parameters["response_format_type"], "json_schema")

    def test_existing_report_requires_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "report.json"
            verify.write_report(destination, {"original": True})
            with self.assertRaises(FileExistsError):
                verify.write_report(destination, {"replacement": True})
            self.assertEqual(json.loads(destination.read_text()), {"original": True})
            verify.write_report(destination, {"replacement": True}, overwrite=True)
            self.assertEqual(json.loads(destination.read_text()), {"replacement": True})

    def test_exit_code_is_zero_only_when_every_selected_test_passes(self):
        for statuses, expected in ((["passed"], 0), (["passed", "skipped"], 2), (["rate_limited"], 2), (["failed", "rate_limited"], 1), ([], 2)):
            self.assertEqual(verify.result_exit_code(verify.count_results([{"status": value} for value in statuses])), expected)

    def test_endpoint_does_not_allow_embedded_credentials_or_query(self):
        for endpoint in ("http://example.com", "https://user:secret@example.com", "https://example.com?api_key=secret", "https://example.com#secret"):
            with self.assertRaises(ValueError):
                verify.validate_endpoint(endpoint)

    def test_missing_keys_generates_skipped_report_without_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "report.json"
            with patch.dict(os.environ, {}, clear=True), patch.object(verify, "load_env"), patch.object(verify, "source_metadata", return_value={"source_git_commit": "test", "source_git_dirty": False, "source_git_diff_sha256": "test"}), contextlib.redirect_stdout(io.StringIO()):
                status = verify.main(["--report", str(destination)], single_vendor="kimi")
            report = json.loads(destination.read_text())
            self.assertEqual(status, 2)
            self.assertEqual(report["model_id"], "kimi-k2.6")
            self.assertEqual(report["counts"]["skipped"], 1)
            self.assertFalse(any(report["privacy"].values()))
            self.assertIn("python", report["runtime"])
            self.assertIn("openai", report["runtime"])


if __name__ == "__main__":
    unittest.main()
