"""运行真实示例代码的离线回归测试：用假 SDK，完全不读真实 Key 或发请求。"""

import base64
import copy
import io
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
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
# 本模块保留原五家的固定“关闭思考 + 模拟天气/JSON”fixture。
# MiniMax M2.7 不支持关闭思考或已确认的 JSON Mode，使用独立专项行为测试。
MODEL_DIRS = sorted(path for path in (ROOT / "models").glob("*/*/examples") if path.parent.parent.name != "minimax")
TOOLS = [directory / "05_tool_calling.py" for directory in MODEL_DIRS]
STREAMS = [directory / "02_streaming.py" for directory in MODEL_DIRS] + [ROOT / "examples/03_streaming.py"]
TEXT_EXAMPLES = [
    path
    for directory in MODEL_DIRS
    for name in ("01_basic.py", "03_thinking.py", "04_json_output.py", "06_vision.py")
    if (path := directory / name).exists()
] + [ROOT / "examples/01_quickstart.py"]


def tool_call(city="杭州", *, name="get_weather", call_id="call_1", arguments=None):
    import json

    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments if arguments is not None else json.dumps({"city": city})),
    )


def response(content="完整回答", reason="stop", calls=None):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason=reason,
                message=SimpleNamespace(
                    role="assistant",
                    content=content,
                    tool_calls=calls,
                    reasoning_content="供回传的模拟思考字段",
                    provider_extension={"preserved": True},
                ),
            )
        ],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )


def chunk(content=None, reason=None):
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=content), finish_reason=reason)],
        usage=None,
    )


class FakeSDK:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
        self.initializations = []
        self.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=self.create)))

    def initialize(self, **kwargs):
        self.initializations.append(kwargs)
        return self.client

    def create(self, **kwargs):
        # 冻结每次调用的 messages，防止后续 append 掩盖第一次请求的内容。
        self.calls.append(copy.deepcopy(kwargs))
        return next(self.responses)


@contextmanager
def fake_sdk(responses, env=None):
    sdk = FakeSDK(responses)
    module = types.ModuleType("openai")
    module.OpenAI = sdk.initialize
    dummy_env = {
        name: "offline-test-only"
        for name in ("DEEPSEEK_API_KEY", "MOONSHOT_API_KEY", "ZHIPU_API_KEY", "DASHSCOPE_API_KEY", "ARK_API_KEY", "MINIMAX_API_KEY")
    }
    # 本地输入适用于三家的图片示例；不能把 DeepSeek/Doubao 的 URL 能力套给 Kimi。
    with tempfile.TemporaryDirectory() as directory:
        image = Path(directory) / "offline.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\noffline-pixels")
        dummy_env["IMAGE_PATH"] = str(image)
        dummy_env.update(env or {})
        with patch.dict(sys.modules, {"openai": module}), patch.dict(os.environ, dummy_env, clear=True):
            yield sdk


def run_example(path, responses, env=None, *, run_name="__main__"):
    with fake_sdk(responses, env) as sdk, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        namespace = runpy.run_path(str(path), run_name=run_name)
    return sdk, namespace


class ExampleTests(unittest.TestCase):
    def test_text_examples_require_normal_finish(self):
        for path in TEXT_EXAMPLES:
            for reason in ("length", "content_filter", "aborted", None, "tool_calls"):
                with self.subTest(example=str(path.relative_to(ROOT)), finish_reason=reason):
                    with self.assertRaises(RuntimeError):
                        run_example(path, [response(reason=reason)] * 2)

    def test_text_examples_reject_empty_final_content_and_missing_choices(self):
        for path in TEXT_EXAMPLES:
            for content in (None, "", "  \n"):
                with self.subTest(example=str(path.relative_to(ROOT)), content=content):
                    with self.assertRaises(RuntimeError):
                        run_example(path, [response(content=content)] * 2)
            with self.subTest(example=str(path.relative_to(ROOT)), choices="missing"):
                with self.assertRaises(RuntimeError):
                    run_example(path, [SimpleNamespace(choices=[])])

    def test_text_and_json_success(self):
        for path in TEXT_EXAMPLES:
            with self.subTest(example=str(path.relative_to(ROOT))):
                content = '{"ok":true}' if path.name == "04_json_output.py" else "完整回答"
                run_example(path, [response(content)] * 2)

    def test_json_rejects_invalid_business_payload(self):
        for directory in MODEL_DIRS:
            for content in ('{"ok":false}', '{"ok":1}', '[]', '{"ok":true,"extra":1}', '{"ok":'):
                with self.subTest(example=str(directory.relative_to(ROOT)), content=content):
                    with self.assertRaises(ValueError):
                        run_example(directory / "04_json_output.py", [response(content)])

    def test_stream_accepts_usage_only_chunks_and_tracks_finish(self):
        for path in STREAMS:
            with self.subTest(example=str(path.relative_to(ROOT))):
                usage_only = SimpleNamespace(choices=[], usage=SimpleNamespace(completion_tokens=5))
                stream = iter([chunk(), chunk("完整"), chunk("回答"), chunk(reason="stop"), usage_only])
                _, namespace = run_example(path, [stream])
                self.assertEqual(namespace["finish_reason"], "stop")
                self.assertEqual("".join(namespace["answer_parts"]), "完整回答")
                self.assertEqual(namespace["usage"].completion_tokens, 5)

    def test_stream_rejects_truncation_missing_finish_and_empty_answer(self):
        cases = [
            [chunk("半句话", "length")],
            [chunk("半句话", "aborted")],
            [chunk("半句话", "content_filter")],
            [chunk("没有结束块")],
            [chunk(reason="stop")],
            [chunk("回答", "stop"), chunk(reason="length")],
            [SimpleNamespace(choices=[], usage=None)],
        ]
        for path in STREAMS:
            for index, chunks in enumerate(cases):
                with self.subTest(example=str(path.relative_to(ROOT)), case=index):
                    with self.assertRaises(RuntimeError):
                        run_example(path, [iter(chunks)])

    def test_stream_propagates_transport_failure(self):
        def broken_stream():
            yield chunk("半句话")
            raise ConnectionError("offline disconnect")

        for path in STREAMS:
            with self.subTest(example=str(path.relative_to(ROOT))):
                with self.assertRaises(ConnectionError):
                    run_example(path, [broken_stream()])

    def test_tools_round_trip_preserves_assistant_and_matches_call_ids(self):
        import json

        for path in TOOLS:
            with self.subTest(example=str(path.relative_to(ROOT))):
                first = response(None, "tool_calls", [tool_call(), tool_call("北京", call_id="call_2")])
                sdk, namespace = run_example(path, [first, response("杭州和北京均为模拟晴天")])
                self.assertEqual(len(sdk.calls), 2)
                self.assertEqual(namespace["executed_call_count"], 2)
                self.assertEqual(len(sdk.calls[0]["messages"]), 2)
                messages = sdk.calls[1]["messages"]
                assistant = messages[2]
                self.assertEqual(assistant.reasoning_content, first.choices[0].message.reasoning_content)
                self.assertEqual(assistant.provider_extension, {"preserved": True})
                tool_messages = messages[3:]
                self.assertEqual([message["tool_call_id"] for message in tool_messages], ["call_1", "call_2"])
                self.assertTrue(all(message["role"] == "tool" for message in tool_messages))
                self.assertTrue(all(json.loads(message["content"])["simulated"] for message in tool_messages))

    def test_tools_validate_entire_batch_before_execution(self):
        bad_calls = [
            tool_call(arguments="[]", call_id="bad"),
            tool_call(arguments="{", call_id="bad"),
            tool_call(city=1, call_id="bad"),
            tool_call(city="", call_id="bad"),
            tool_call(city="x" * 81, call_id="bad"),
            tool_call(city="杭\n州", call_id="bad"),
            tool_call(arguments='{"city":"杭州","extra":true}', call_id="bad"),
            tool_call(name="unknown_tool", call_id="bad"),
            tool_call(call_id=""),
            tool_call(call_id="call_1"),
        ]
        for path in TOOLS:
            for bad_call in bad_calls:
                with self.subTest(example=str(path.relative_to(ROOT)), bad_call=bad_call):
                    executed = []
                    previous_profile = sys.getprofile()

                    def profile(frame, event, arg):
                        if event == "call" and frame.f_code.co_filename == str(path) and frame.f_code.co_name == "get_weather":
                            executed.append(frame.f_locals["city"])

                    try:
                        sys.setprofile(profile)
                        with self.assertRaises(ValueError):
                            run_example(path, [response(None, "tool_calls", [tool_call(), bad_call])])
                    finally:
                        sys.setprofile(previous_profile)
                    self.assertEqual(executed, [], "首个调用合规也不能在后续调用校验失败前执行")

    def test_tools_reject_bad_finish_and_empty_final(self):
        for path in TOOLS:
            for reason in ("length", "aborted", "stop", None):
                with self.subTest(example=str(path.relative_to(ROOT)), tool_finish=reason):
                    with self.assertRaises(RuntimeError):
                        run_example(path, [response(None, reason, [tool_call()])])
            for final in (response("半句", "length"), response(None), response("\n")):
                with self.subTest(example=str(path.relative_to(ROOT)), final=final):
                    with self.assertRaises(RuntimeError):
                        run_example(path, [response(None, "tool_calls", [tool_call()]), final])

    def test_tools_require_an_executed_tool_before_final_answer(self):
        for path in TOOLS:
            with self.subTest(example=str(path.relative_to(ROOT))):
                with self.assertRaisesRegex(RuntimeError, "未完成工具闭环"):
                    run_example(path, [response("杭州天气晴，模型直接生成的正文")])

    def test_tools_bound_model_turns(self):
        for path in TOOLS:
            with self.subTest(example=str(path.relative_to(ROOT))):
                rounds = [response(None, "tool_calls", [tool_call(call_id=f"call_{index}")]) for index in range(6)]
                with fake_sdk(rounds) as sdk, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    with self.assertRaises(RuntimeError):
                        runpy.run_path(str(path), run_name="__main__")
                self.assertEqual(len(sdk.calls), 6)

    def test_vision_encodes_local_file_as_data_url(self):
        paths = [directory / "06_vision.py" for directory in MODEL_DIRS if (directory / "06_vision.py").exists()]
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "test.png"
            payload = b"\x89PNG\r\n\x1a\nmock-pixels"
            image.write_bytes(payload)
            for path in paths:
                with self.subTest(example=str(path.relative_to(ROOT))):
                    sdk, _ = run_example(path, [response()], {"IMAGE_URL": "", "IMAGE_PATH": str(image)})
                    content = sdk.calls[0]["messages"][0]["content"]
                    self.assertIsInstance(content, list)
                    self.assertEqual(content[1]["image_url"]["url"], "data:image/png;base64," + base64.b64encode(payload).decode("ascii"))

    def test_multi_turn_records_only_complete_answer(self):
        path = ROOT / "examples/04_multi_turn.py"
        with fake_sdk([response("半句", "length"), response("完整回答")]) as sdk, redirect_stdout(io.StringIO()):
            namespace = runpy.run_path(str(path), run_name="example_test")
            with self.assertRaises(RuntimeError):
                namespace["ask"]("失败的提问")
            self.assertEqual(len(namespace["messages"]), 1)
            self.assertEqual(namespace["ask"]("成功的提问"), "完整回答")
            self.assertEqual(len(namespace["messages"]), 3)
            self.assertEqual(sdk.calls[1]["messages"][-1]["content"], "成功的提问")

    def test_one_for_all_uses_model_generation_cards(self):
        import json

        path = ROOT / "examples/02_one_for_all.py"
        vendors = json.loads((ROOT / "skills/model-manual/references/vendors.json").read_text(encoding="utf-8"))["vendors"]
        with fake_sdk([response()] * len(vendors)) as sdk, redirect_stdout(io.StringIO()):
            namespace = runpy.run_path(str(path), run_name="example_test")
            for index, (vendor, cfg) in enumerate(vendors.items()):
                with self.subTest(vendor=vendor):
                    self.assertEqual(namespace["chat"](vendor, "你好"), "完整回答")
                    card = namespace["model_card"](vendor)
                    generation = card["generation"]
                    self.assertEqual(sdk.initializations[index]["base_url"], generation["base_url"]["value"])
                    self.assertEqual(sdk.calls[index]["model"], card["identity"]["api_model_id"]["value"])
                    defaults = generation.get("request_defaults", {}).get("value", {})
                    toggle = generation["thinking"].get("off", {}).get("value", {})
                    self.assertEqual(sdk.calls[index].get("extra_body", {}), {**defaults, **toggle})

    def test_one_for_all_rejects_truncated_answer(self):
        path = ROOT / "examples/02_one_for_all.py"
        with fake_sdk([response("半句", "length")]), redirect_stdout(io.StringIO()):
            namespace = runpy.run_path(str(path), run_name="example_test")
            with self.assertRaises(RuntimeError):
                namespace["chat"]("deepseek", "你好")

    @unittest.skipUnless(os.name == "posix", "假 curl 和符号链接测试需要 POSIX Shell")
    def test_curl_example_checks_complete_response(self):
        import json

        script = ROOT / "models/deepseek/deepseek-flash/examples/08_curl.sh"
        bash = shutil.which("bash")
        self.assertIsNotNone(bash)
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            # 用离线 curl 替身执行真实 shell 示例；PATH 前置且环境不含任何真实 Key。
            fake_curl = directory_path / "curl"
            (directory_path / "python3").symlink_to(sys.executable)
            for reason, expected_code in (("stop", 0), ("length", 1), ("aborted", 1)):
                with self.subTest(finish_reason=reason):
                    payload = json.dumps({"choices": [{"finish_reason": reason, "message": {"content": "回答"}}]})
                    fake_curl.write_text("#!/bin/sh\nprintf '%s' '" + payload + "'\n", encoding="utf-8")
                    fake_curl.chmod(0o755)
                    result = subprocess.run(
                        [bash, str(script)],
                        env={"PATH": directory + os.pathsep + os.defpath, "DEEPSEEK_API_KEY": "offline-test-only"},
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, expected_code, result.stderr)


if __name__ == "__main__":
    unittest.main()
