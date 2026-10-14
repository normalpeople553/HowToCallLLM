"""豆包官方文档改编示例的离线回归；SDK 全部替换，不读 Key、不发请求。"""

import contextlib
import copy
import io
import json
import os
import runpy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
from unittest.mock import patch

from test_examples import chunk, fake_sdk, response, run_example, tool_call


ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "models/doubao/doubao-seed-2-1-pro-260628/examples"
MODEL = "doubao-seed-2-1-pro-260628"


def thought_tool_response(calls=None):
    result = response(None, "tool_calls", calls or [tool_call()])
    message = result.choices[0].message
    message.reasoning_content = "这是供后续请求回传的模拟思考摘要。"
    message.encrypted_content = "opaque-offline-ciphertext-do-not-modify"
    return result


class TrackingStream:
    def __init__(self, chunks):
        self.chunks, self.closed = chunks, False

    def __iter__(self):
        return iter(self.chunks)

    def close(self):
        self.closed = True


class DoubaoOfficialExamplesTests(unittest.TestCase):
    def test_manifest_covers_all_examples_and_live_status_requires_strict_evidence(self):
        catalog = json.loads((EXAMPLES / "sources.json").read_text(encoding="utf-8"))
        # 只读验证器会核对真实报告身份、当前源码/支持文件哈希和最终 HTTP 响应。
        validator = runpy.run_path(str(ROOT / "skills/model-manual/scripts/example_catalog.py"), run_name="offline_catalog_validation")
        validated = next(item for item in validator["load_catalogs"](ROOT) if item["vendor"] == "doubao" and item["model_id"] == MODEL)
        verified_entries = {entry["file"]: entry for entry in validated["examples"]}
        self.assertEqual(catalog["schema_version"], 1)
        self.assertEqual(catalog["vendor"], "doubao")
        self.assertEqual(catalog["model_id"], MODEL)
        self.assertEqual(catalog["checked_at"], "2026-10-14")
        entries = catalog["examples"]
        self.assertEqual({entry["file"] for entry in entries}, {item.name for item in EXAMPLES.glob("*.py")})
        self.assertEqual(len({entry["id"] for entry in entries}), len(entries))
        for entry in entries:
            with self.subTest(example=entry["file"]):
                self.assertEqual(entry["origin"], "adapted_from_official")
                verification = entry["verification"]
                checked = verified_entries[entry["file"]]["verification"]
                self.assertEqual(verification["live"], checked["live"])
                if verification["live"] == "not_run":
                    self.assertFalse(verification.get("report"))
                else:
                    self.assertTrue((ROOT / verification["report"]).is_file())
                    self.assertEqual(verification["report"], checked["report"])
                    self.assertIn("tested_at", checked)
                self.assertEqual(entry["verification"]["offline"], "mock_tested")
                self.assertIn("ARK_API_KEY", entry["required_env"])
                self.assertIn(entry["file"], entry["run_command"])
                self.assertTrue(entry["adaptations"])
                self.assertTrue(entry["sources"])
                for source in entry["sources"]:
                    self.assertEqual(urlparse(source["url"]).hostname, "docs.volcengine.com")
                    self.assertTrue(source["title"])
        self.assertTrue(catalog["not_integrated"])
        for gap in catalog["not_integrated"]:
            self.assertTrue(gap["reason"])
            self.assertTrue(gap["sources"])

    def test_every_example_imports_without_api_client_or_key_access(self):
        # fake_sdk 使用纯测试环境；若模块初始化发请求，此处立即因无回复失败。
        for example in EXAMPLES.glob("*.py"):
            with self.subTest(example=example.name), fake_sdk([]) as sdk, contextlib.redirect_stdout(io.StringIO()):
                namespace = runpy.run_path(str(example), run_name="offline_import")
                self.assertTrue(callable(namespace.get("main")))
                self.assertEqual(sdk.initializations, [])
                self.assertEqual(sdk.calls, [])

    def test_each_manifest_example_runs_with_mocked_target_model(self):
        fixtures = {
            "01_basic.py": [response()],
            "02_streaming.py": [iter([chunk("完整回答", "stop")])],
            "03_thinking.py": [response()],
            "04_json_output.py": [response('{"ok":true}')],
            "05_tool_calling.py": [thought_tool_response(), response("教学模拟晴天")],
            "06_vision.py": [response()],
            "07_multi_turn.py": [response("核心功能"), response("产品介绍")],
            "08_thinking_tools.py": [thought_tool_response(), response("教学模拟天气")],
            "09_video.py": [response("视频场景描述")],
            "10_implicit_cache.py": [response(), response()],
        }
        for filename, replies in fixtures.items():
            with self.subTest(example=filename):
                sdk, _ = run_example(EXAMPLES / filename, replies, {"VIDEO_URL": "https://example.com/demo.mp4"})
                self.assertTrue(sdk.calls)
                self.assertTrue(all(call["model"] == MODEL for call in sdk.calls))
                self.assertEqual(sdk.initializations[0]["base_url"], "https://ark.cn-beijing.volces.com/api/v3")

    def test_multi_turn_preserves_complete_history(self):
        first, final = response("第一轮完整回答"), response("第二轮完整回答")
        first.choices[0].message.encrypted_content = "opaque-first-turn"
        sdk, namespace = run_example(EXAMPLES / "07_multi_turn.py", [first, final])
        self.assertEqual(len(sdk.calls), 2)
        self.assertEqual(len(sdk.calls[0]["messages"]), 2)
        self.assertEqual(len(sdk.calls[1]["messages"]), 4)
        assistant = sdk.calls[1]["messages"][2]
        self.assertEqual(assistant.content, first.choices[0].message.content)
        self.assertEqual(assistant.encrypted_content, "opaque-first-turn")
        self.assertEqual(len(namespace["history"]), 5)

    def test_multi_turn_failed_answer_does_not_change_history(self):
        for bad in (response("半句", "length"), response(""), response(None), SimpleNamespace(choices=[])):
            with self.subTest(response=bad), fake_sdk([bad]) as sdk, contextlib.redirect_stdout(io.StringIO()):
                namespace = runpy.run_path(str(EXAMPLES / "07_multi_turn.py"), run_name="offline_import")
                history = [{"role": "system", "content": "系统消息"}]
                original = copy.deepcopy(history)
                with self.assertRaises(RuntimeError):
                    namespace["ask"](sdk.client, history, "这个提问将失败")
                self.assertEqual(history, original)

    def test_thinking_tools_preserve_opaque_encryption_and_tool_ids(self):
        first = thought_tool_response([tool_call(), tool_call("北京", call_id="call_2")])
        sdk, namespace = run_example(EXAMPLES / "08_thinking_tools.py", [first, response("杭州和北京均为教学模拟晴天")])
        self.assertEqual(namespace["executed_call_count"], 2)
        self.assertEqual(len(sdk.calls), 2)
        for request in sdk.calls:
            self.assertEqual(request["extra_body"], {"thinking": {"type": "enabled"}})
        messages = sdk.calls[1]["messages"]
        assistant = messages[2]
        original = first.choices[0].message
        self.assertEqual(assistant.reasoning_content, original.reasoning_content)
        self.assertEqual(assistant.encrypted_content, original.encrypted_content)
        self.assertEqual(assistant.provider_extension, original.provider_extension)
        self.assertEqual([item["tool_call_id"] for item in messages[3:]], ["call_1", "call_2"])
        self.assertTrue(all(json.loads(item["content"])["simulated"] for item in messages[3:]))

    def test_pinned_sdk_serializes_encrypted_field_without_network(self):
        try:
            import httpx
            from openai import OpenAI
        except ImportError:
            self.skipTest("安装 requirements-lock.txt 后可运行 SDK 序列化检查")
        requests = []

        def handle(request):
            requests.append(json.loads(request.content))
            if len(requests) == 1:
                message = {
                    "role": "assistant", "content": None,
                    "reasoning_content": "供回传的摘要", "encrypted_content": "opaque-unmodified-ciphertext",
                    "tool_calls": [{"id": "offline-call", "type": "function", "function": {"name": "get_weather", "arguments": '{"city":"杭州"}'}}],
                }
                reason = "tool_calls"
            else:
                message, reason = {"role": "assistant", "content": "教学模拟天气是晴天。"}, "stop"
            return httpx.Response(200, json={
                "id": "offline-response", "object": "chat.completion", "created": 1, "model": MODEL,
                "choices": [{"index": 0, "finish_reason": reason, "message": message}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            })

        # MockTransport 在本进程直接构造响应，始终不会走网络。
        client = OpenAI(api_key="offline-test-only", base_url="https://example.invalid/v3", http_client=httpx.Client(transport=httpx.MockTransport(handle)))
        try:
            with patch("openai.OpenAI", return_value=client), patch.dict(os.environ, {"ARK_API_KEY": "offline-test-only"}, clear=True), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(EXAMPLES / "08_thinking_tools.py"), run_name="__main__")
        finally:
            client.close()
        self.assertEqual(len(requests), 2)
        assistant = requests[1]["messages"][2]
        self.assertEqual(assistant["encrypted_content"], "opaque-unmodified-ciphertext")
        self.assertEqual(assistant["reasoning_content"], "供回传的摘要")

    def test_thinking_tools_validate_entire_batch_before_execution(self):
        bad_calls = [
            tool_call(name="delete_something", call_id="bad"),
            tool_call(arguments="[]", call_id="bad"),
            tool_call(arguments="{", call_id="bad"),
            tool_call(city=4, call_id="bad"),
            tool_call(city="", call_id="bad"),
            tool_call(city="杭\n州", call_id="bad"),
            tool_call(arguments='{"city":"杭州","extra":true}', call_id="bad"),
            tool_call(call_id="call_1"),
        ]
        example = EXAMPLES / "08_thinking_tools.py"
        for bad in bad_calls:
            executed = []
            previous_profile = sys.getprofile()

            def profile(frame, event, arg):
                if event == "call" and frame.f_code.co_filename == str(example) and frame.f_code.co_name == "get_weather":
                    executed.append(frame.f_locals["city"])

            with self.subTest(call=bad):
                try:
                    sys.setprofile(profile)
                    with self.assertRaises(ValueError):
                        run_example(example, [thought_tool_response([tool_call(), bad])])
                finally:
                    sys.setprofile(previous_profile)
                self.assertEqual(executed, [])

    def test_thinking_tools_reject_incomplete_or_empty_final_response(self):
        example = EXAMPLES / "08_thinking_tools.py"
        for final in (response("半句话", "length"), response("", "stop"), response(None, "stop"), response("拒绝", "content_filter"), SimpleNamespace(choices=[])):
            with self.subTest(final=final), self.assertRaises(RuntimeError):
                run_example(example, [thought_tool_response(), final])
        with self.assertRaisesRegex(RuntimeError, "未完成工具闭环"):
            run_example(example, [response("没有执行工具的回答")])

    def test_thinking_tools_do_not_execute_truncated_or_unbounded_calls(self):
        example = EXAMPLES / "08_thinking_tools.py"
        for reason in ("length", None, "stop", "aborted"):
            with self.subTest(reason=reason), self.assertRaises(RuntimeError):
                run_example(example, [response(None, reason, [tool_call()])])
        replies = [thought_tool_response([tool_call(call_id=f"round_{index}")]) for index in range(6)]
        with fake_sdk(replies) as sdk, contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            runpy.run_path(str(example), run_name="__main__")
        self.assertEqual(len(sdk.calls), 6)

    def test_video_uses_url_part_without_new_model_specific_options(self):
        sdk, _ = run_example(EXAMPLES / "09_video.py", [response("视频描述")], {"VIDEO_URL": "https://example.com/demo.mp4?signature=offline"})
        request = sdk.calls[0]
        self.assertEqual(request["messages"][0]["content"][0], {"type": "video_url", "video_url": {"url": "https://example.com/demo.mp4?signature=offline"}})
        self.assertNotIn("preprocess_configs", request)
        self.assertNotIn("fps", request["messages"][0]["content"][0]["video_url"])

    def test_video_rejects_missing_invalid_url_and_incomplete_answer(self):
        for url in ("", "http://example.com/video.mp4", "file:///tmp/demo.mp4", "https://username:password@example.com/video.mp4"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                run_example(EXAMPLES / "09_video.py", [], {"VIDEO_URL": url})
        for bad in (response("半句", "length"), response(""), response(None), SimpleNamespace(choices=[])):
            with self.subTest(response=bad), self.assertRaises(RuntimeError):
                run_example(EXAMPLES / "09_video.py", [bad], {"VIDEO_URL": "https://example.com/demo.mp4"})

    def test_cache_keeps_prefix_fixed_and_reports_hit_miss_or_unknown(self):
        example = EXAMPLES / "10_implicit_cache.py"
        for cached_tokens, expected in ((0, "本次未命中缓存"), (1024, "本次命中缓存"), (None, "无法判断是否命中")):
            replies = [response(), response()]
            for reply in replies:
                reply.usage.prompt_tokens_details = SimpleNamespace(cached_tokens=cached_tokens)
            with self.subTest(cached_tokens=cached_tokens), fake_sdk(replies) as sdk, contextlib.redirect_stdout(io.StringIO()) as output:
                runpy.run_path(str(example), run_name="__main__")
                self.assertIn(expected, output.getvalue())
                self.assertEqual(sdk.calls[0]["messages"], sdk.calls[1]["messages"])
                self.assertNotIn("caching", sdk.calls[0])

    def test_cache_stops_if_any_response_is_incomplete(self):
        for bad in (response("半句", "length"), response(""), response(None), SimpleNamespace(choices=[])):
            with self.subTest(response=bad), self.assertRaises(RuntimeError):
                run_example(EXAMPLES / "10_implicit_cache.py", [bad])

    def test_stream_closes_and_rejects_content_after_finish(self):
        stream = TrackingStream([chunk("完成", "stop"), chunk("结束后的错误内容")])
        with self.assertRaises(RuntimeError):
            run_example(EXAMPLES / "02_streaming.py", [stream])
        self.assertTrue(stream.closed)


if __name__ == "__main__":
    unittest.main()
