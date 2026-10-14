"""Execute Qwen/GLM official-adapted examples with a fake SDK, never real keys."""

import copy
import io
import json
import os
import runpy
import sys
import types
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
PROVIDERS = {
    "qwen": {"model": "qwen-flash", "key": "DASHSCOPE_API_KEY", "host": "help.aliyun.com", "off": {"enable_thinking": False}, "on": {"enable_thinking": True}},
    "zhipu": {"model": "glm-4.7", "key": "ZHIPU_API_KEY", "host": "docs.bigmodel.cn", "off": {"thinking": {"type": "disabled"}}, "on": {"thinking": {"type": "enabled"}}},
}


def examples_dir(vendor):
    return ROOT / "models" / vendor / PROVIDERS[vendor]["model"] / "examples"


def to_dict(value):
    if isinstance(value, SimpleNamespace):
        return {key: to_dict(item) for key, item in vars(value).items()}
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value


class Message(SimpleNamespace):
    def model_dump(self, **_kwargs):
        return copy.deepcopy(to_dict(self))


def response(text="完整答案", reason="stop", calls=None):
    return SimpleNamespace(
        choices=[SimpleNamespace(finish_reason=reason, message=Message(
            role="assistant", content=text, tool_calls=calls,
            reasoning_content="保留这段模拟思考", provider_extension={"preserved": True},
        ))],
        usage={"prompt_tokens": 10, "completion_tokens": 5, "completion_tokens_details": {"reasoning_tokens": 2}},
    )


def call(call_id="call_1", name="get_inventory", args='{"sku":"SKU-001"}'):
    return SimpleNamespace(id=call_id, type="function", function=SimpleNamespace(name=name, arguments=args))


class FakeSDK:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
        self.initializations = []

    def initialize(self, **kwargs):
        self.initializations.append(kwargs)
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=self.create)))

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        return next(self.responses)


@contextmanager
def fake_sdk(responses):
    sdk = FakeSDK(responses)
    module = types.ModuleType("openai")
    module.OpenAI = sdk.initialize
    # clear=True prevents tests from reading a real key inherited from the shell.
    env = {provider["key"]: "offline-test-only" for provider in PROVIDERS.values()}
    with patch.dict(sys.modules, {"openai": module}), patch.dict(os.environ, env, clear=True):
        yield sdk


class TextOfficialExampleTests(unittest.TestCase):
    def run_script(self, path, responses):
        with fake_sdk(responses) as sdk, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            runpy.run_path(str(path), run_name="__main__")
        return sdk

    def test_new_examples_import_without_reading_key_or_constructing_client(self):
        for vendor in PROVIDERS:
            for filename in ("06_multi_turn.py", "07_thinking_tools.py"):
                with self.subTest(vendor=vendor, file=filename), fake_sdk([]) as sdk:
                    runpy.run_path(str(examples_dir(vendor) / filename), run_name="imported_example")
                    self.assertEqual(sdk.initializations, [])

    def test_multiturn_passes_validated_history_and_keeps_exact_model(self):
        for vendor, config in PROVIDERS.items():
            with self.subTest(vendor=vendor):
                sdk = self.run_script(examples_dir(vendor) / "06_multi_turn.py", [response("已记住报名信息"), response("周六上午的 Python 入门课")])
                self.assertEqual(len(sdk.calls), 2)
                self.assertEqual(len(sdk.calls[0]["messages"]), 2)
                history = sdk.calls[1]["messages"]
                self.assertEqual(len(history), 4)
                self.assertEqual(history[2]["role"], "assistant")
                self.assertEqual(history[2]["content"], "已记住报名信息")
                self.assertEqual(history[3]["role"], "user")
                for request in sdk.calls:
                    self.assertEqual(request["model"], config["model"])
                    self.assertEqual(request["extra_body"], config["off"])
                if vendor == "qwen":
                    self.assertNotIn("reasoning_content", history[2])

    def test_multiturn_stops_before_next_request_on_incomplete_answer(self):
        bad = [response("半句", "length"), response("半句", "aborted"), response("回答", None), response(""), response(None), SimpleNamespace(choices=[], usage=None), response("文本", calls=[call()])]
        for vendor in PROVIDERS:
            for index, incomplete in enumerate(bad):
                with self.subTest(vendor=vendor, case=index), fake_sdk([incomplete, response()]) as sdk, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    with self.assertRaises(RuntimeError):
                        runpy.run_path(str(examples_dir(vendor) / "06_multi_turn.py"), run_name="__main__")
                    self.assertEqual(len(sdk.calls), 1)

    def test_thinking_tools_returns_full_assistant_and_matching_results(self):
        for vendor, config in PROVIDERS.items():
            with self.subTest(vendor=vendor):
                first = response(None, "tool_calls", [call(), call("call_2")])
                sdk = self.run_script(examples_dir(vendor) / "07_thinking_tools.py", [first, response("模拟库存7件，足够5件需求")])
                self.assertEqual(len(sdk.calls), 2)
                history = sdk.calls[1]["messages"]
                self.assertEqual(history[2], first.choices[0].message.model_dump(exclude_none=True))
                self.assertEqual(history[2]["reasoning_content"], "保留这段模拟思考")
                self.assertEqual(history[2]["provider_extension"], {"preserved": True})
                self.assertEqual([item["tool_call_id"] for item in history[3:]], ["call_1", "call_2"])
                for tool_message in history[3:]:
                    data = json.loads(tool_message["content"])
                    self.assertTrue(data["simulated"])
                    self.assertEqual(data["available"], 7)
                for request in sdk.calls:
                    self.assertEqual(request["model"], config["model"])
                    self.assertEqual(request["extra_body"], config["on"])
                    self.assertEqual(request["tool_choice"], "auto")
                    self.assertNotIn("max_completion_tokens", request)
                    self.assertNotIn("preserve_thinking", request["extra_body"])

    def test_thinking_tools_validates_whole_batch_before_running_tool(self):
        bad_calls = [call("call_2", name="shell"), call("call_2", args="[]"), call("call_2", args="{"), call("call_2", args='{"sku":true}'), call("call_2", args='{"sku":"SKU-001","extra":1}'), call(), call("")]
        for vendor in PROVIDERS:
            path = examples_dir(vendor) / "07_thinking_tools.py"
            for bad_call in bad_calls:
                with self.subTest(vendor=vendor, bad=bad_call), fake_sdk([response(None, "tool_calls", [call(), bad_call])]), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    namespace = runpy.run_path(str(path), run_name="imported_example")
                    executed = []
                    globals_ = namespace["main"].__globals__
                    with patch.dict(globals_, {"get_inventory": lambda sku: executed.append(sku)}):
                        with self.assertRaises(ValueError):
                            namespace["main"]()
                    self.assertEqual(executed, [])

    def test_thinking_tools_rejects_bad_finish_direct_answer_and_empty_final(self):
        cases = [
            [response("未调用工具的回答")],
            [response(None, "length", [call()])],
            [response(None, "stop", [call()])],
            [SimpleNamespace(choices=[], usage=None)],
            [response(None, "tool_calls", [call()]), response("半句话", "length")],
            [response(None, "tool_calls", [call()]), response("")],
            [response(None, "tool_calls", [call()]), response("半句话", None)],
        ]
        for vendor in PROVIDERS:
            for index, responses in enumerate(cases):
                with self.subTest(vendor=vendor, case=index), self.assertRaises(RuntimeError):
                    self.run_script(examples_dir(vendor) / "07_thinking_tools.py", responses)

    def test_thinking_tools_rejects_reused_ids_and_has_turn_bound(self):
        for vendor in PROVIDERS:
            path = examples_dir(vendor) / "07_thinking_tools.py"
            with self.subTest(vendor=vendor, scenario="reused id"), self.assertRaises(ValueError):
                self.run_script(path, [response(None, "tool_calls", [call()]), response(None, "tool_calls", [call()])])
            rounds = [response(None, "tool_calls", [call(f"call_{index}")]) for index in range(4)]
            with self.subTest(vendor=vendor, scenario="bound"), fake_sdk(rounds) as sdk, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    runpy.run_path(str(path), run_name="__main__")
                self.assertEqual(len(sdk.calls), 4)

    def test_source_manifests_cover_files_and_sources_without_public_execution_data(self):
        validator = runpy.run_path(str(ROOT / "skills/model-manual/scripts/example_catalog.py"), run_name="offline_catalog_validation")
        validated = {(item["vendor"], item["model_id"]): item for item in validator["load_catalogs"](ROOT)}
        for vendor, config in PROVIDERS.items():
            directory = examples_dir(vendor)
            manifest = json.loads((directory / "sources.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["vendor"], vendor)
            self.assertEqual(manifest["model_id"], config["model"])
            self.assertEqual(manifest["checked_at"], "2026-10-14")
            entries = manifest["examples"]
            verified_entries = {entry["file"]: entry for entry in validated[(vendor, config["model"])]["examples"]}
            self.assertEqual({entry["file"] for entry in entries}, {path.name for path in directory.glob("*.py")})
            self.assertEqual(len({entry["id"] for entry in entries}), len(entries))
            for entry in entries:
                self.assertEqual(entry["required_env"], [config["key"]])
                relative = (directory / entry["file"]).relative_to(ROOT).as_posix()
                self.assertEqual(entry["run_command"], "python " + relative)
                self.assertEqual(entry["origin"], "adapted_from_official")
                verification = entry["verification"]
                checked = verified_entries[entry["file"]]["verification"]
                self.assertEqual(verification["live"], checked["live"])
                self.assertEqual(set(checked), {"offline", "live", "note"})
                self.assertEqual(set(verification), {"offline", "live", "note"})
                self.assertIn(checked["live"], {"private", "not_run"})
                self.assertIn(entry["verification"]["offline"], {"mock_tested", "compile_checked"})
                compile((directory / entry["file"]).read_text(encoding="utf-8"), entry["file"], "exec")
            for item in entries + manifest["not_integrated"]:
                self.assertTrue(item["sources"])
                for source in item["sources"]:
                    self.assertEqual(urlparse(source["url"]).scheme, "https")
                    self.assertEqual(urlparse(source["url"]).hostname, config["host"])
                    self.assertTrue(source["title"])


if __name__ == "__main__":
    unittest.main()
