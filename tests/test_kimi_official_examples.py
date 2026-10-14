"""Kimi 官方功能示例的离线请求形状/边界检查；不读取真实密钥或调用 API。"""

import base64
import copy
import io
import json
import os
import runpy
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "models/kimi/kimi-k2.6/examples"


def completion(content="完整回答", reason="stop", calls=None):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            finish_reason=reason,
            message=SimpleNamespace(
                role="assistant", content=content, tool_calls=calls,
                reasoning_content="模拟思考内容", provider_extension={"retained": True},
            ),
        )],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=10),
    )


def call(arguments=None, name="get_order_status", call_id="call_1"):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments if arguments is not None else {"order_id": "DEMO-1001"}),
        ),
    )


class FakeSDK:
    def __init__(self, responses=()):
        self.responses = iter(responses)
        self.calls = []
        self.initializations = []
        self.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=self.create)))

    def initialize(self, **kwargs):
        self.initializations.append(kwargs)
        return self.client

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        return next(self.responses)


@contextmanager
def mocked_sdk(responses=(), env=None):
    sdk = FakeSDK(responses)
    module = types.ModuleType("openai")
    module.OpenAI = sdk.initialize
    dummy_env = {"MOONSHOT_API_KEY": "offline-test-only"}
    dummy_env.update(env or {})
    with patch.dict(sys.modules, {"openai": module}), patch.dict(os.environ, dummy_env, clear=True), redirect_stdout(io.StringIO()):
        yield sdk


def load(name):
    return runpy.run_path(str(EXAMPLES / name), run_name="offline_example_import")


class KimiOfficialExampleTests(unittest.TestCase):
    def test_new_examples_import_without_key_or_client_creation(self):
        for filename in ("06_vision.py", "07_multi_turn.py", "08_thinking_tools.py", "09_video.py", "10_json_schema.py"):
            with self.subTest(file=filename), mocked_sdk() as sdk:
                with patch.dict(os.environ, {}, clear=True):
                    load(filename)
                self.assertEqual(sdk.initializations, [])
                self.assertEqual(sdk.calls, [])

    def test_existing_examples_remain_covered_by_mock(self):
        stream = [
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="完整回答"), finish_reason="stop")], usage=None),
            SimpleNamespace(choices=[], usage=SimpleNamespace(completion_tokens=10)),
        ]
        responses = {
            "01_basic.py": [completion()],
            "02_streaming.py": [iter(stream)],
            "03_thinking.py": [completion()],
            "04_json_output.py": [completion('{"ok":true}')],
            "05_tool_calling.py": [
                completion(None, "tool_calls", [call({"city": "杭州"}, "get_weather")]),
                completion("杭州为模拟晴天"),
            ],
        }
        for filename, returned in responses.items():
            with self.subTest(file=filename), mocked_sdk(returned) as sdk:
                runpy.run_path(str(EXAMPLES / filename), run_name="__main__")
                self.assertEqual(sdk.calls[0]["model"], "kimi-k2.6")

    def test_image_request_is_base64_and_refuses_remote_url(self):
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "image.png"
            payload = b"\x89PNG\r\n\x1a\nmock-pixels"
            image.write_bytes(payload)
            with mocked_sdk([completion()], {"IMAGE_PATH": str(image)}) as sdk:
                runpy.run_path(str(EXAMPLES / "06_vision.py"), run_name="__main__")
                content = sdk.calls[0]["messages"][0]["content"]
                self.assertIsInstance(content, list)
                self.assertEqual(content[1]["image_url"]["url"], "data:image/png;base64," + base64.b64encode(payload).decode("ascii"))
            with mocked_sdk(env={"IMAGE_URL": "https://example.com/image.png"}) as sdk:
                with self.assertRaisesRegex(ValueError, "不支持远程图片 URL"):
                    runpy.run_path(str(EXAMPLES / "06_vision.py"), run_name="__main__")
                self.assertEqual(sdk.calls, [])

    def test_multi_turn_preserves_whole_message_and_commits_only_success(self):
        first = completion("记住了")
        with mocked_sdk([first, completion("小明，26岁"), completion("半句", "length")]) as sdk:
            namespace = load("07_multi_turn.py")
            messages = [{"role": "system", "content": "测试"}]
            self.assertEqual(namespace["ask"](sdk.client, messages, "我叫小明，今年26岁"), "记住了")
            self.assertEqual(namespace["ask"](sdk.client, messages, "我是谁"), "小明，26岁")
            assistant = sdk.calls[1]["messages"][2]
            self.assertEqual(assistant.reasoning_content, first.choices[0].message.reasoning_content)
            self.assertEqual(assistant.provider_extension, {"retained": True})
            self.assertEqual(len(messages), 5)
            with self.assertRaises(RuntimeError):
                namespace["ask"](sdk.client, messages, "这轮截断")
            self.assertEqual(len(messages), 5)

    def test_thinking_tools_keep_reasoning_and_match_all_ids(self):
        first = completion(None, "tool_calls", [call(), call({"order_id": "DEMO-1002"}, call_id="call_2")])
        with mocked_sdk([first, completion("两个订单都为教学模拟待发货")]) as sdk:
            namespace = load("08_thinking_tools.py")
            self.assertIn("模拟", namespace["run_agent"](sdk.client, "查询模拟订单"))
            self.assertEqual(len(sdk.calls), 2)
            for request in sdk.calls:
                self.assertEqual(request["extra_body"], {"thinking": {"type": "enabled", "keep": "all"}})
                self.assertGreaterEqual(request["max_tokens"], 16000)
                self.assertEqual(request["tool_choice"], "auto")
                self.assertNotIn("reasoning_effort", request)
                self.assertNotIn("temperature", request)
            messages = sdk.calls[1]["messages"]
            self.assertEqual(messages[2].reasoning_content, "模拟思考内容")
            self.assertEqual(messages[2].provider_extension, {"retained": True})
            self.assertEqual([message["tool_call_id"] for message in messages[3:]], ["call_1", "call_2"])
            self.assertTrue(all(json.loads(message["content"])["simulated"] for message in messages[3:]))

    def test_thinking_tools_validate_batch_before_any_execution(self):
        invalid_calls = [
            call({"order_id": "REAL-1001"}, call_id="bad"),
            call({"order_id": 1001}, call_id="bad"),
            call({"order_id": "DEMO-1001", "extra": True}, call_id="bad"),
            call(["DEMO-1001"], call_id="bad"),
            call(name="unregistered", call_id="bad"),
            call(call_id="call_1"),
        ]
        for invalid in invalid_calls:
            with self.subTest(call=invalid), mocked_sdk([completion(None, "tool_calls", [call(), invalid])]) as sdk:
                namespace = load("08_thinking_tools.py")
                function = namespace["run_agent"]
                handler = Mock(return_value='{"simulated":true}')
                with patch.dict(function.__globals__, {"get_order_status": handler}):
                    with self.assertRaises(ValueError):
                        function(sdk.client, "查询模拟订单")
                handler.assert_not_called()

    def test_thinking_tools_require_complete_calls_and_final_answer(self):
        cases = [
            [completion("直接回答，未用工具")],
            [completion(None, "length", [call()])],
            [completion(None, "aborted", [call()])],
            [completion(None, "tool_calls", [call()]), completion("半句", "length")],
            [completion(None, "tool_calls", [call()]), completion(None)],
        ]
        for index, responses in enumerate(cases):
            with self.subTest(case=index), mocked_sdk(responses) as sdk:
                namespace = load("08_thinking_tools.py")
                with self.assertRaises(RuntimeError):
                    namespace["run_agent"](sdk.client, "查询模拟订单")

    def test_thinking_tools_stop_before_executing_last_budget_round(self):
        responses = [completion(None, "tool_calls", [call(call_id=f"call_{index}")]) for index in range(2)]
        with mocked_sdk(responses) as sdk:
            namespace = load("08_thinking_tools.py")
            function = namespace["run_agent"]
            handler = Mock(return_value='{"simulated":true}')
            with patch.dict(function.__globals__, {"get_order_status": handler}):
                with self.assertRaises(RuntimeError):
                    function(sdk.client, "查询模拟订单", max_model_turns=2)
            self.assertEqual(handler.call_count, 1)
            self.assertEqual(len(sdk.calls), 2)

    def test_video_uses_official_video_url_content_type(self):
        with tempfile.TemporaryDirectory() as temporary:
            video = Path(temporary) / "clip.mp4"
            payload = b"mock-mp4-payload"
            video.write_bytes(payload)
            with mocked_sdk([completion()], {"VIDEO_PATH": str(video)}) as sdk:
                runpy.run_path(str(EXAMPLES / "09_video.py"), run_name="__main__")
                content = sdk.calls[0]["messages"][0]["content"]
                self.assertIsInstance(content, list)
                self.assertEqual(content[0], {"type": "video_url", "video_url": {"url": "data:video/mp4;base64," + base64.b64encode(payload).decode("ascii")}})
                self.assertEqual(sdk.calls[0]["extra_body"], {"thinking": {"type": "disabled"}})

    def test_video_example_rejects_unsupported_inputs_before_api(self):
        with mocked_sdk(env={"VIDEO_URL": "https://example.com/clip.mp4"}) as sdk:
            with self.assertRaisesRegex(ValueError, "VIDEO_PATH"):
                runpy.run_path(str(EXAMPLES / "09_video.py"), run_name="__main__")
            self.assertEqual(sdk.initializations, [])
        with tempfile.TemporaryDirectory() as temporary, mocked_sdk():
            namespace = load("09_video.py")
            empty = Path(temporary) / "empty.mp4"
            empty.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "为空"):
                namespace["video_content"](str(empty))
            with self.assertRaisesRegex(ValueError, "MP4"):
                namespace["video_content"](str(Path(temporary) / "clip.avi"))

    def test_schema_is_simple_strict_and_checks_business_fields(self):
        with mocked_sdk([completion('{"name":"小明","age":26}')]) as sdk:
            namespace = runpy.run_path(str(EXAMPLES / "10_json_schema.py"), run_name="__main__")
            output = sdk.calls[0]["response_format"]
            self.assertEqual(output["type"], "json_schema")
            self.assertIs(output["json_schema"]["strict"], True)
            schema = output["json_schema"]["schema"]
            self.assertEqual(schema["required"], ["name", "age"])
            self.assertIs(schema["additionalProperties"], False)
            self.assertNotIn("$ref", json.dumps(schema))
            for data in ({"name": "小明", "age": True}, {"name": "", "age": 26}, {"name": "小明", "age": -1}, {"name": "小明", "age": 26, "extra": True}, []):
                with self.subTest(data=data), self.assertRaises(ValueError):
                    namespace["validate_person"](data)

    def test_new_text_paths_reject_incomplete_or_empty_answer(self):
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "image.png"
            video = Path(temporary) / "clip.mp4"
            image.write_bytes(b"mock-png-payload")
            video.write_bytes(b"mock-mp4-payload")
            env = {"IMAGE_PATH": str(image), "VIDEO_PATH": str(video)}
            for filename in ("06_vision.py", "07_multi_turn.py", "09_video.py", "10_json_schema.py"):
                for returned in (completion("半句", "length"), completion("拒绝", "content_filter"), completion(None), SimpleNamespace(choices=[])):
                    with self.subTest(file=filename, response=returned), mocked_sdk([returned], env):
                        with self.assertRaises(RuntimeError):
                            runpy.run_path(str(EXAMPLES / filename), run_name="__main__")


if __name__ == "__main__":
    unittest.main()
