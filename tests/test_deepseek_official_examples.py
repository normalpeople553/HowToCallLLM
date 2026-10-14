"""执行 DeepSeek 官方改写示例的离线测试；无网络、无真实密钥。"""

import copy
import io
import json
import os
import runpy
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_examples import fake_sdk, response, tool_call


DIRECTORY = Path(__file__).resolve().parent.parent / "models/deepseek/deepseek-flash/examples"


def execute(name, results=(), env=None, *, configure=None, run_name="__main__"):
    with fake_sdk(results, env) as sdk, patch.dict(sys.modules), patch.object(sys, "path", [str(DIRECTORY)] + sys.path), redirect_stdout(io.StringIO()):
        sys.modules.pop("_support", None)
        if configure:
            configure(sdk)
        namespace = runpy.run_path(str(DIRECTORY / name), run_name=run_name)
        return sdk, namespace


class DeepSeekOfficialExampleTests(unittest.TestCase):
    def test_multi_turn_sends_complete_history(self):
        sdk, _ = execute("09_multi_turn.py", [response("你好小明"), response("小明")])
        history = sdk.calls[1]["messages"]
        self.assertEqual(len(history), 4)
        self.assertEqual(history[-2], {"role": "assistant", "content": "你好小明"})

    def test_multi_turn_failure_does_not_pollute_history(self):
        with fake_sdk([response("半句", "length")]) as sdk, patch.dict(sys.modules), patch.object(sys, "path", [str(DIRECTORY)] + sys.path):
            sys.modules.pop("_support", None)
            namespace = runpy.run_path(str(DIRECTORY / "09_multi_turn.py"), run_name="offline")
            history = [{"role": "system", "content": "助手"}]
            before = copy.deepcopy(history)
            with self.assertRaises(RuntimeError):
                namespace["ask"](sdk.client, history, "问题")
            self.assertEqual(history, before)

    def test_file_reference_has_top_level_file_id_and_no_upload(self):
        def configure(sdk):
            sdk.client.files = SimpleNamespace(create=lambda **_: self.fail("不得上传已有 ID"))
        sdk, _ = execute("10_vision_files.py", [response()], {"IMAGE_PATH": "", "IMAGE_FILE_ID": "file-api-offline"}, configure=configure)
        self.assertEqual(sdk.calls[0]["messages"][0]["content"][1], {"type": "file", "file_id": "file-api-offline"})

    def test_file_upload_sets_purpose_expiration_and_keeps_handle_open(self):
        uploads = []
        def configure(sdk):
            def upload(**kwargs):
                self.assertFalse(kwargs["file"].closed)
                self.assertTrue(kwargs["file"].read().startswith(b"\x89PNG"))
                uploads.append(kwargs)
                return SimpleNamespace(id="file-api-new")
            sdk.client.files = SimpleNamespace(create=upload)
        sdk, _ = execute("10_vision_files.py", [response()], configure=configure)
        self.assertEqual(uploads[0]["purpose"], "user_data")
        self.assertEqual(uploads[0]["expires_after"], {"anchor": "created_at", "seconds": 3600})
        self.assertTrue(uploads[0]["file"].closed)
        self.assertEqual(sdk.calls[0]["messages"][0]["content"][1]["file_id"], "file-api-new")

    def test_responses_vision_uses_different_content_and_reasoning_shape(self):
        def configure(sdk):
            sdk.client.responses = SimpleNamespace(create=sdk.create)
        sdk, _ = execute("11_responses_vision.py", [SimpleNamespace(status="completed", output_text="图片描述")], {"IMAGE_DETAIL": "low"}, configure=configure)
        self.assertEqual(sdk.calls[0]["reasoning"], {"effort": "none"})
        self.assertNotIn("messages", sdk.calls[0])
        part = sdk.calls[0]["input"][0]["content"][1]
        self.assertEqual(part["type"], "input_image")
        self.assertEqual(part["detail"], "low")
        self.assertTrue(part["image_url"].startswith("data:image/png;base64,"))

    def test_responses_rejects_incomplete_failed_and_empty(self):
        for status, text in (("incomplete", "半句"), ("failed", ""), ("completed", " ")):
            with self.subTest(status=status, text=text), self.assertRaises(RuntimeError):
                execute("11_responses_vision.py", [SimpleNamespace(status=status, output_text=text)], configure=lambda sdk: setattr(sdk.client, "responses", SimpleNamespace(create=sdk.create)))

    def test_tools_preserve_thinking_and_beta_schema(self):
        for name in ("12_thinking_tools.py", "13_strict_tools.py"):
            first = response(None, "tool_calls", [tool_call()])
            with self.subTest(example=name):
                sdk, _ = execute(name, [first, response("模拟天气")])
                assistant = sdk.calls[1]["messages"][2]
                self.assertEqual(assistant.reasoning_content, first.choices[0].message.reasoning_content)
                self.assertEqual(assistant.provider_extension, {"preserved": True})
                function = sdk.calls[0]["tools"][0]["function"]
                if "strict" in name:
                    self.assertTrue(sdk.initializations[0]["base_url"].endswith("/beta"))
                    self.assertTrue(function["strict"])
                    self.assertFalse(function["parameters"]["additionalProperties"])
                else:
                    self.assertEqual(sdk.calls[0]["extra_body"], {"thinking": {"type": "enabled"}})

    def test_tools_reject_bad_batch_and_bound_turns(self):
        for name in ("12_thinking_tools.py", "13_strict_tools.py"):
            with self.subTest(example=name), self.assertRaises(ValueError):
                execute(name, [response(None, "tool_calls", [tool_call(), tool_call(name="unknown", call_id="bad")])])
            with self.subTest(example=name), self.assertRaises(RuntimeError):
                execute(name, [response(None, "tool_calls", [tool_call(call_id=f"call_{i}")]) for i in range(6)])
            with self.assertRaises(RuntimeError):
                execute(name, [response("未经工具直接回答")])

    def test_prefix_uses_last_assistant_and_beta(self):
        sdk, _ = execute("14_prefix_completion.py", [response("def convert(c): return c * 1.8 + 32")])
        self.assertEqual(sdk.calls[0]["messages"][-1]["role"], "assistant")
        self.assertTrue(sdk.calls[0]["messages"][-1]["prefix"])
        self.assertTrue(sdk.initializations[0]["base_url"].endswith("/beta"))

    def test_fim_uses_completions_and_rejects_truncation(self):
        def configure(sdk):
            sdk.client.completions = SimpleNamespace(create=sdk.create)
        sdk, _ = execute("15_fim_completion.py", [SimpleNamespace(choices=[SimpleNamespace(text="    fahrenheit = celsius * 1.8 + 32", finish_reason="stop")])], configure=configure)
        self.assertIn("suffix", sdk.calls[0])
        self.assertNotIn("messages", sdk.calls[0])
        for reason, text in (("length", "半句"), ("stop", "")):
            with self.assertRaises(RuntimeError):
                execute("15_fim_completion.py", [SimpleNamespace(choices=[SimpleNamespace(text=text, finish_reason=reason)])], configure=configure)

    def test_helper_detects_four_image_formats_from_bytes(self):
        _, namespace = execute("09_multi_turn.py", run_name="offline")
        support = namespace["make_client"].__globals__
        for data, mime in ((b"GIF89a-pixels", "image/gif"), (b"RIFF1234WEBPpixels", "image/webp"), (b"\xff\xd8\xff-pixels", "image/jpeg"), (b"\x89PNG\r\n\x1a\n-pixels", "image/png")):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "not-an-image-extension.bin"
                path.write_bytes(data)
                self.assertEqual(support["image_bytes"](path), (data, mime))

    def test_helper_input_validation_and_tool_argument_edges(self):
        _, namespace = execute("09_multi_turn.py", run_name="offline")
        support = namespace["make_client"].__globals__
        for env in ({}, {"IMAGE_URL": "https://example.com/x.png", "IMAGE_PATH": "also-set"}, {"IMAGE_URL": "file:///etc/hosts"}, {"IMAGE_URL": "https://example.com/" + "x" * 8192}):
            with self.subTest(env_keys=list(env)), patch.dict(os.environ, env, clear=True), self.assertRaises(ValueError):
                support["image_url_from_env"]()
        with patch.dict(os.environ, {"IMAGE_DETAIL": "unknown"}, clear=True), self.assertRaises(ValueError):
            support["image_detail"]()
        for arguments in ("{", "[]", '{"city":1}', '{"city":""}', '{"city":"杭州","extra":true}'):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                execute("12_thinking_tools.py", [response(None, "tool_calls", [tool_call(arguments=arguments)])])
        with self.assertRaises(ValueError):
            execute("12_thinking_tools.py", [response(None, "tool_calls", [tool_call(), tool_call()])])
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.png"
            image.write_bytes(b"not-image")
            with self.assertRaises(ValueError):
                support["image_bytes"](image)
            with self.assertRaises(ValueError):
                support["image_bytes"](image, max_bytes=1)

    def test_locked_sdk_serializes_examples_without_network(self):
        """使用真实 SDK + HTTP MockTransport，补上假 SDK 不覆盖的序列化层。"""
        import httpx
        import openai

        original_openai = openai.OpenAI
        for name in ("09_multi_turn.py", "10_vision_files.py", "11_responses_vision.py", "12_thinking_tools.py", "13_strict_tools.py", "14_prefix_completion.py", "15_fim_completion.py"):
            requests = []
            def handler(request):
                requests.append(request)
                if request.url.path == "/files":
                    return httpx.Response(200, json={"id": "file-api-sdk-test", "object": "file", "bytes": 20, "created_at": 0, "filename": "offline.png", "purpose": "user_data"})
                payload = json.loads(request.content)
                if request.url.path == "/responses":
                    result = {"id": "resp_offline", "object": "response", "created_at": 0, "status": "completed", "model": "deepseek-flash", "output": [{"id": "msg_offline", "type": "message", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "text": "离线响应", "annotations": []}]}]}
                elif request.url.path.endswith("/completions") and "prompt" in payload:
                    result = {"id": "fim_offline", "object": "text_completion", "created": 0, "model": "deepseek-flash", "choices": [{"index": 0, "text": "    fahrenheit = celsius * 1.8 + 32", "finish_reason": "stop"}]}
                else:
                    message = {"role": "assistant", "content": "离线响应"}
                    finish = "stop"
                    if "tools" in payload and len(requests) == 1:
                        message.update(content=None, reasoning_content="offline-reasoning", tool_calls=[{"id": "offline_call", "type": "function", "function": {"name": "get_weather", "arguments": '{"city":"杭州"}'}}])
                        finish = "tool_calls"
                    if "tools" in payload and len(requests) == 2:
                        self.assertEqual(payload["messages"][2]["reasoning_content"], "offline-reasoning")
                        self.assertEqual(payload["messages"][3]["tool_call_id"], "offline_call")
                    result = {"id": "chat_offline", "object": "chat.completion", "created": 0, "model": "deepseek-flash", "choices": [{"index": 0, "message": message, "finish_reason": finish}]}
                return httpx.Response(200, json=result)

            clients = []
            def factory(**kwargs):
                client = original_openai(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(handler)))
                clients.append(client)
                return client

            with self.subTest(example=name), tempfile.TemporaryDirectory() as directory:
                image = Path(directory) / "offline.png"
                image.write_bytes(b"\x89PNG\r\n\x1a\noffline-pixels")
                env = {"DEEPSEEK_API_KEY": "offline-test-only", "IMAGE_PATH": str(image)}
                try:
                    with patch.object(openai, "OpenAI", factory), patch.dict(os.environ, env, clear=True), patch.dict(sys.modules), patch.object(sys, "path", [str(DIRECTORY)] + sys.path), redirect_stdout(io.StringIO()):
                        sys.modules.pop("_support", None)
                        runpy.run_path(str(DIRECTORY / name), run_name="__main__")
                finally:
                    for client in clients:
                        client.close()
                self.assertTrue(requests)
                if name == "10_vision_files.py":
                    self.assertIn(b"user_data", requests[0].content)
                    self.assertIn(b"expires_after[seconds]", requests[0].content)
                    self.assertEqual(json.loads(requests[1].content)["messages"][0]["content"][1], {"type": "file", "file_id": "file-api-sdk-test"})


if __name__ == "__main__":
    unittest.main()
