"""MiniMax-M2.7 独立示例的离线协议与边界测试，不读取真实 Key 或访问网络。"""

import copy
import io
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parent.parent
DIRECTORY = ROOT / "models/minimax/MiniMax-M2.7/examples"
PYTHON_FILES = ("01_basic.py", "02_streaming.py", "03_thinking.py", "05_tool_calling.py", "06_multi_turn.py")


def response(content="最终正文", reason="stop", calls=None, code=0):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            finish_reason=reason,
            message=SimpleNamespace(
                role="assistant", content=content, tool_calls=calls,
                reasoning_content="拆分的模拟思考", provider_extension={"retained": True},
            ),
        )],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20),
        base_resp={"status_code": code, "status_msg": "DO-NOT-PRINT-RAW-ERROR"},
    )


def tool_call(city="杭州", call_id="call_1", name="get_weather", arguments=None):
    return SimpleNamespace(
        id=call_id, type="function",
        function=SimpleNamespace(name=name, arguments=arguments if arguments is not None else json.dumps({"city": city})),
    )


def chunk(content=None, reason=None, reasoning=None, calls=None):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            delta=SimpleNamespace(content=content, reasoning_content=reasoning, tool_calls=calls),
            finish_reason=reason,
        )],
        usage=None,
        base_resp={"status_code": 0},
    )


class FakeSDK:
    def __init__(self, responses=()):
        self.responses = iter(responses)
        self.initializations = []
        self.calls = []
        self.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=self.create)))

    def initialize(self, **kwargs):
        self.initializations.append(kwargs)
        return self.client

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        return next(self.responses)


@contextmanager
def fake_sdk(responses=()):
    sdk = FakeSDK(responses)
    module = types.ModuleType("openai")
    module.OpenAI = sdk.initialize
    with patch.dict(sys.modules, {"openai": module}), patch.dict(os.environ, {"MINIMAX_API_KEY": "offline-test-only"}, clear=True), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        yield sdk


def load(name):
    return runpy.run_path(str(DIRECTORY / name), run_name="offline_example_import")


class MiniMaxExampleTests(unittest.TestCase):
    def test_locked_sdk_serializes_budget_and_complete_tool_history_offline(self):
        import httpx
        import openai

        original_openai = openai.OpenAI
        for filename in ("01_basic.py", "05_tool_calling.py"):
            requests = []
            def handler(request):
                self.assertEqual(str(request.url), "https://api.minimax.cn/v1/chat/completions")
                body = json.loads(request.content)
                requests.append(body)
                self.assertTrue(body["reasoning_split"])
                self.assertEqual(body["max_completion_tokens"], 16384)
                self.assertNotIn("max_tokens", body)
                self.assertNotIn("tool_choice", body)
                message = {"role": "assistant", "content": "离线最终回答"}
                reason = "stop"
                if "tools" in body and len(requests) == 1:
                    message = {"role": "assistant", "content": "<think>原始内联思考</think>", "reasoning_content": "原始拆分思考", "provider_extension": {"retained": True}, "tool_calls": [{"id": "call_offline", "type": "function", "function": {"name": "get_weather", "arguments": '{"city":"杭州"}'}}]}
                    reason = "tool_calls"
                if "tools" in body and len(requests) == 2:
                    assistant = body["messages"][2]
                    self.assertEqual(assistant["content"], "<think>原始内联思考</think>")
                    self.assertEqual(assistant["reasoning_content"], "原始拆分思考")
                    self.assertEqual(assistant["provider_extension"], {"retained": True})
                    self.assertEqual(body["messages"][3]["tool_call_id"], "call_offline")
                return httpx.Response(200, json={"id": "offline", "object": "chat.completion", "model": "MiniMax-M2.7", "created": 0, "base_resp": {"status_code": 0}, "choices": [{"index": 0, "message": message, "finish_reason": reason}], "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}})

            clients = []
            def factory(**kwargs):
                client = original_openai(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(handler)))
                clients.append(client)
                return client

            try:
                with self.subTest(filename=filename), patch.object(openai, "OpenAI", factory), patch.dict(os.environ, {"MINIMAX_API_KEY": "offline-test-only"}, clear=True), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    runpy.run_path(str(DIRECTORY / filename), run_name="__main__")
                self.assertEqual(len(requests), 2 if "tool" in filename else 1)
            finally:
                for client in clients:
                    client.close()

    def test_imports_do_not_read_credentials_or_create_clients(self):
        for name in PYTHON_FILES:
            with self.subTest(file=name), fake_sdk() as sdk, patch.dict(os.environ, {}, clear=True):
                load(name)
                self.assertEqual(sdk.initializations, [])
                self.assertEqual(sdk.calls, [])

    def test_basic_and_thinking_use_cn_host_and_format_only_switch(self):
        for name in ("01_basic.py", "03_thinking.py"):
            with self.subTest(file=name), fake_sdk([response()]) as sdk:
                runpy.run_path(str(DIRECTORY / name), run_name="__main__")
                self.assertEqual(sdk.initializations[0]["base_url"], "https://api.minimax.cn/v1")
                request = sdk.calls[0]
                self.assertEqual(request["model"], "MiniMax-M2.7")
                self.assertEqual(request["extra_body"], {"reasoning_split": True})
                self.assertGreater(request["max_completion_tokens"], 0)
                for parameter in ("thinking", "reasoning_effort", "response_format", "max_tokens"):
                    self.assertNotIn(parameter, request)

    def test_complete_text_rejects_truncation_empty_thinking_only_and_business_failure(self):
        cases = [
            response("半句", "length"), response("内容", "content_filter"), response("内容", "aborted"),
            response("内容", None), response(None), response("\n"), response("<think>只有思考</think>"),
            response("<think>思考没有结束"), response(code=1004), SimpleNamespace(choices=[]),
        ]
        for name in ("01_basic.py", "03_thinking.py", "06_multi_turn.py"):
            for index, returned in enumerate(cases):
                with self.subTest(file=name, case=index), fake_sdk([returned]):
                    with self.assertRaises(RuntimeError):
                        runpy.run_path(str(DIRECTORY / name), run_name="__main__")

    def test_display_may_strip_think_but_history_keeps_original_message(self):
        first = response("<think>原始内联思考</think>记住了")
        with fake_sdk([first, response("小明，26岁"), response("半句", "length")]) as sdk:
            namespace = load("06_multi_turn.py")
            history = [{"role": "system", "content": "测试"}]
            self.assertEqual(namespace["ask"](sdk.client, history, "我叫小明"), "记住了")
            self.assertEqual(namespace["ask"](sdk.client, history, "我是谁"), "小明，26岁")
            assistant = sdk.calls[1]["messages"][2]
            self.assertEqual(assistant.content, first.choices[0].message.content)
            self.assertEqual(assistant.reasoning_content, "拆分的模拟思考")
            self.assertEqual(assistant.provider_extension, {"retained": True})
            self.assertEqual(len(history), 5)
            with self.assertRaises(RuntimeError):
                namespace["ask"](sdk.client, history, "这轮截断")
            self.assertEqual(len(history), 5)

    def test_stream_accepts_usage_only_and_keeps_thinking_separate(self):
        chunks = [
            chunk(reasoning="模拟思考"), chunk("最终"), chunk("正文"), chunk(reason="stop"),
            SimpleNamespace(choices=[], usage=SimpleNamespace(completion_tokens=20)),
        ]
        with fake_sdk([iter(chunks)]) as sdk:
            runpy.run_path(str(DIRECTORY / "02_streaming.py"), run_name="__main__")
            self.assertEqual(sdk.calls[0]["stream_options"], {"include_usage": True})
            self.assertEqual(sdk.calls[0]["extra_body"], {"reasoning_split": True})
        with fake_sdk():
            namespace = load("02_streaming.py")
            text, reasoning, usage = namespace["consume_stream"](iter(chunks))
            self.assertEqual((text, reasoning, usage.completion_tokens), ("最终正文", "模拟思考", 20))

    def test_stream_rejects_missing_finish_bad_finish_or_post_finish_output(self):
        cases = [
            [chunk("半句", "length")], [chunk("半句", "aborted")], [chunk("没有结束")],
            [chunk(reason="stop")], [chunk("<think>只有思考</think>", "stop")],
            [chunk("正文", "stop"), chunk("额外正文")],
            [chunk("正文", "stop"), chunk(reason="stop")],
            [chunk("正文", "stop"), chunk(reasoning="结束后思考")],
            [chunk(calls=[tool_call()], reason="tool_calls")],
        ]
        for index, chunks in enumerate(cases):
            with self.subTest(case=index), fake_sdk():
                namespace = load("02_streaming.py")
                with self.assertRaises(RuntimeError):
                    namespace["consume_stream"](iter(chunks))

    def test_stream_propagates_transport_and_business_failure(self):
        def interrupted():
            yield chunk("半句")
            raise ConnectionError("offline disconnect")

        with fake_sdk():
            namespace = load("02_streaming.py")
            with self.assertRaises(ConnectionError):
                namespace["consume_stream"](interrupted())
            failed = chunk("半句")
            failed.base_resp["status_code"] = 1004
            with self.assertRaises(RuntimeError):
                namespace["consume_stream"](iter([failed]))

    def test_tools_keep_all_thinking_and_match_every_call(self):
        first = response("<think>制定计划</think>查询天气", "tool_calls", [tool_call(), tool_call("北京", "call_2")])
        with fake_sdk([first, response("<think>汇总</think>两地均为教学模拟晴天")]) as sdk:
            namespace = load("05_tool_calling.py")
            self.assertEqual(namespace["run_agent"](sdk.client), "两地均为教学模拟晴天")
            self.assertEqual(len(sdk.calls), 2)
            messages = sdk.calls[1]["messages"]
            self.assertEqual(messages[2].content, first.choices[0].message.content)
            self.assertEqual(messages[2].reasoning_content, first.choices[0].message.reasoning_content)
            self.assertEqual(messages[2].provider_extension, {"retained": True})
            self.assertEqual([message["tool_call_id"] for message in messages[3:]], ["call_1", "call_2"])
            self.assertTrue(all(json.loads(message["content"])["simulated"] for message in messages[3:]))
            self.assertTrue(all(request["extra_body"] == {"reasoning_split": True} for request in sdk.calls))

    def test_tools_validate_entire_batch_before_execution(self):
        invalid_calls = [
            tool_call(arguments="{", call_id="bad"), tool_call(arguments="[]", call_id="bad"),
            tool_call(city=True, call_id="bad"), tool_call(city="", call_id="bad"),
            tool_call(city="杭\n州", call_id="bad"), tool_call(city="x" * 81, call_id="bad"),
            tool_call(name="unknown", call_id="bad"), tool_call(call_id=""), tool_call(call_id="call_1"),
            tool_call(arguments='{"city":"杭州","extra":true}', call_id="bad"),
        ]
        for invalid in invalid_calls:
            with self.subTest(call=invalid), fake_sdk([response(None, "tool_calls", [tool_call(), invalid])]) as sdk:
                function = load("05_tool_calling.py")["run_agent"]
                handler = Mock(return_value='{"simulated":true}')
                with patch.dict(function.__globals__, {"get_weather": handler}):
                    with self.assertRaises(ValueError):
                        function(sdk.client)
                handler.assert_not_called()

    def test_tools_reject_direct_answer_bad_finish_and_missing_final_body(self):
        cases = [
            [response("未调用工具")], [response(None, "length", [tool_call()])],
            [response(None, "stop", [tool_call()])], [response(None, "tool_calls", [tool_call()], code=1004)],
            [response(None, "tool_calls", [tool_call()]), response("半句", "length")],
            [response(None, "tool_calls", [tool_call()]), response("<think>只有思考</think>")],
            [response(None, "tool_calls", [tool_call()]), response(None, "tool_calls", [tool_call()])],
        ]
        for index, responses in enumerate(cases):
            with self.subTest(case=index), fake_sdk(responses) as sdk:
                namespace = load("05_tool_calling.py")
                with self.assertRaises((RuntimeError, ValueError)):
                    namespace["run_agent"](sdk.client)

    def test_tools_stop_before_executing_last_round(self):
        with fake_sdk([response(None, "tool_calls", [tool_call(call_id=f"call_{index}")]) for index in range(2)]) as sdk:
            function = load("05_tool_calling.py")["run_agent"]
            handler = Mock(return_value='{"simulated":true}')
            with patch.dict(function.__globals__, {"get_weather": handler}):
                with self.assertRaises(RuntimeError):
                    function(sdk.client, max_model_turns=2)
            self.assertEqual(len(sdk.calls), 2)
            self.assertEqual(handler.call_count, 1)

    def test_manifest_omits_unsupported_json_and_requires_evidence_for_live_status(self):
        manifest = json.loads((DIRECTORY / "sources.json").read_text(encoding="utf-8"))
        validator = runpy.run_path(str(ROOT / "skills/model-manual/scripts/example_catalog.py"), run_name="offline_catalog_validation")
        validated = next(item for item in validator["load_catalogs"](ROOT) if item["vendor"] == "minimax" and item["model_id"] == "MiniMax-M2.7")
        verified_entries = {entry["file"]: entry for entry in validated["examples"]}
        self.assertFalse((DIRECTORY / "04_json_output.py").exists())
        self.assertEqual(manifest["model_id"], "MiniMax-M2.7")
        for entry in manifest["examples"]:
            verification = entry["verification"]
            checked = verified_entries[entry["file"]]["verification"]
            self.assertEqual(verification["live"], checked["live"])
            if verification["live"] == "not_run":
                self.assertFalse(verification.get("report"))
            else:
                self.assertTrue((ROOT / verification["report"]).is_file())
                self.assertEqual(verification["report"], checked["report"])
                self.assertIn("tested_at", checked)
            self.assertNotIn(entry["capability"], {"json_object", "json_schema"})
        not_integrated = {entry["capability"] for entry in manifest["not_integrated"]}
        self.assertTrue({"json_object", "json_schema", "thinking_off", "vision"} <= not_integrated)

    @unittest.skipUnless(os.name == "posix", "原生 cURL 脚本替身测试需要 POSIX Shell")
    def test_native_curl_uses_documented_host_field_and_checks_business_status(self):
        bash = shutil.which("bash")
        self.assertIsNotNone(bash)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "python3").symlink_to(sys.executable)
            fake_curl = directory / "curl"
            fake_curl.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "body = json.load(sys.stdin)\n"
                "if body.get('model') != 'MiniMax-M2.7' or 'max_tokens' in body or body.get('max_completion_tokens') != 16384: sys.exit(91)\n"
                "if 'https://api.minimax.cn/v1/text/chatcompletion_v2' not in sys.argv: sys.exit(92)\n"
                "sys.stdout.write(os.environ['OFFLINE_NATIVE_RESPONSE'])\n",
                encoding="utf-8",
            )
            fake_curl.chmod(0o755)
            cases = [
                (0, "stop", "<think>模拟思考</think>最终正文", 0),
                (1004, "stop", "正文", 1), (0, "length", "半句", 1),
                (0, "stop", "<think>只有思考</think>", 1),
                (0, "stop", "<think>思考没有结束", 1), (0, "stop", " ", 1),
            ]
            for code, reason, content, expected in cases:
                with self.subTest(code=code, finish_reason=reason, content=content):
                    payload = {
                        "base_resp": {"status_code": code, "status_msg": "DO-NOT-PRINT-RAW-ERROR"},
                        "choices": [{"finish_reason": reason, "message": {"content": content}}],
                    }
                    result = subprocess.run(
                        [bash, str(DIRECTORY / "07_native_curl.sh")],
                        env={
                            "PATH": temporary + os.pathsep + os.defpath,
                            "MINIMAX_API_KEY": "offline-test-only",
                            "OFFLINE_NATIVE_RESPONSE": json.dumps(payload, ensure_ascii=False),
                        },
                        text=True, capture_output=True, check=False,
                    )
                    self.assertEqual(result.returncode, expected, result.stderr)
                    self.assertNotIn("DO-NOT-PRINT-RAW-ERROR", result.stdout + result.stderr)
                    if expected == 0:
                        self.assertIn("最终正文", result.stdout)
                        self.assertNotIn("模拟思考", result.stdout)


if __name__ == "__main__":
    unittest.main()
