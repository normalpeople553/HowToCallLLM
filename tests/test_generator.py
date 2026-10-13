"""Offline behavior checks for standalone generated calls; no API keys or network."""

import ast
import contextlib
import copy
import importlib.util
import io
import json
import math
import os
import shutil
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


GENERATOR = Path(__file__).resolve().parent.parent / "skills/model-manual/scripts/generate_snippet.py"
spec = importlib.util.spec_from_file_location("model_generator", GENERATOR)
generator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(generator)


def request_from_python(source):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "request" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("generated request missing")


def reply(text="OK", reason="stop", calls=None, reasoning=None):
    data = {"role": "assistant", "content": text}
    if calls:
        data["tool_calls"] = [{"id": c.id, "type": c.type, "function": vars(c.function)} for c in calls]
    if reasoning:
        data["reasoning_content"] = reasoning
    message = types.SimpleNamespace(content=text, tool_calls=calls, model_dump=lambda **_: copy.deepcopy(data))
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message, finish_reason=reason)], usage={"completion_tokens": 3})


def chunk(text=None, reason=None, usage=None, no_choices=False):
    choices = [] if no_choices else [types.SimpleNamespace(delta=types.SimpleNamespace(content=text), finish_reason=reason)]
    return types.SimpleNamespace(choices=choices, usage=usage)


def tool_call(arguments='{"a":19,"b":23}', name="sum_numbers", call_id="call_1"):
    return types.SimpleNamespace(id=call_id, type="function", function=types.SimpleNamespace(name=name, arguments=arguments))


class ModelSelectionTests(unittest.TestCase):
    def setUp(self):
        self.cards = generator.load_models()

    def test_unknown_and_vendor_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "未收录型号"):
            generator.load_model("glm-5.3", "zhipu")
        with self.assertRaisesRegex(ValueError, "不能与厂商"):
            generator.load_model("kimi-k2.6", "deepseek")
        cli = subprocess.run([sys.executable, str(GENERATOR), "--vendor", "zhipu", "--model", "glm-5.3"], capture_output=True, text=True)
        self.assertEqual(cli.returncode, 2)
        self.assertEqual(cli.stdout, "")
        self.assertIn("未收录型号", cli.stderr)

    def test_legacy_function_arguments_cannot_override_model(self):
        cfg = {"default_model": "kimi-k2.6", "key_env": "OTHER_KEY", "base_url": "https://invalid.example", "thinking_off_body": {"incorrect": True}}
        source = generator.python_snippet(cfg, "kimi-k2.6", "hi", False, "off")
        request = request_from_python(source)
        self.assertEqual(request["extra_body"], {"thinking": {"type": "disabled"}})
        self.assertNotIn("OTHER_KEY", source)
        self.assertNotIn("invalid.example", source)
        with self.assertRaisesRegex(ValueError, "不能与厂商"):
            generator.python_snippet(cfg, "qwen-flash", "hi", False, "off")

    def test_card_budget_and_thinking_fields_drive_request(self):
        for model, card in self.cards.items():
            for mode in ("default", "on", "off"):
                with self.subTest(model=model, thinking=mode):
                    original = copy.deepcopy(card)
                    body = generator.build_request(card, "hi", thinking=mode, max_tokens=4096)
                    parameter = card["generation"]["token_budget"]["parameter"]["value"]
                    self.assertEqual(body[parameter], 4096)
                    if mode == "default":
                        self.assertNotIn("thinking", body)
                        self.assertNotIn("enable_thinking", body)
                    else:
                        toggle = card["generation"]["thinking"][mode]["value"]
                        self.assertTrue(toggle.items() <= body.items())
                    self.assertEqual(card, original)
        qwen = generator.build_request(self.cards["qwen-flash"], "hi", max_tokens=100)
        self.assertIn("max_tokens", qwen)
        self.assertNotIn("max_completion_tokens", qwen)
        default = generator.build_request(self.cards["glm-4.7-flash"], "hi")
        self.assertNotIn("max_tokens", default)
        for invalid in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                generator.build_request(self.cards["deepseek-flash"], "hi", max_tokens=invalid)
        with self.assertRaisesRegex(ValueError, "不能超过"):
            generator.build_request(self.cards["deepseek-flash"], "hi", max_tokens=393217)

    def test_capability_and_language_combinations_fail_explicitly(self):
        for model in ("qwen-flash", "glm-4.7-flash"):
            with self.assertRaisesRegex(ValueError, "未登记图片输入"):
                generator.build_request(self.cards[model], "describe", task="vision", image_url="https://example.com/image.png")
        with self.assertRaisesRegex(ValueError, "image-url"):
            generator.build_request(self.cards["kimi-k2.6"], "describe", task="vision")
        with self.assertRaisesRegex(ValueError, "thinking off"):
            generator.build_request(self.cards["qwen-flash"], "extract", task="json")
        with self.assertRaisesRegex(ValueError, "暂不支持 --stream"):
            generator.build_request(self.cards["kimi-k2.6"], "sum", task="tool", stream=True)
        for func in (generator.typescript_snippet, generator.curl_snippet):
            for task in ("tool", "vision"):
                with self.assertRaisesRegex(ValueError, "仅支持 Python"):
                    func(self.cards["kimi-k2.6"], "kimi-k2.6", "hi", False, "off", task=task)

    def test_generated_python_and_shell_are_valid_with_adversarial_question(self):
        question = "引号 '\"、换行\nMODEL_MANUAL_JSON\n$(not_a_command) `not_a_command`"
        for model, card in self.cards.items():
            tasks = ["chat", "json", "tool"]
            if generator._supported(card, "vision"):
                tasks.append("vision")
            for task in tasks:
                for stream in (False, True):
                    if task == "tool" and stream:
                        continue
                    with self.subTest(model=model, task=task, stream=stream):
                        image_url = "https://example.com/image.png" if task == "vision" else None
                        source = generator.python_snippet(card, model, question, stream, "off", 4096, task, image_url)
                        compile(source, f"<{model}/{task}>", "exec")
                        body = request_from_python(source)
                        if task == "json":
                            self.assertIn("JSON", body["messages"][0]["content"])
                        if task == "tool":
                            self.assertEqual(body["tool_choice"], "auto")
            for stream in (False, True):
                source = generator.curl_snippet(card, model, question, stream, "off")
                check = subprocess.run(["bash", "--noprofile", "--norc", "-n"], input=source, text=True, capture_output=True)
                self.assertEqual(check.returncode, 0, check.stderr)

    def test_past_model_warning_is_stderr_only(self):
        cli = subprocess.run([sys.executable, str(GENERATOR), "--vendor", "doubao", "--max-tokens", "4096"], capture_output=True, text=True)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        compile(cli.stdout, "<doubao-cli>", "exec")
        self.assertIn("往期模型", cli.stderr)
        self.assertIn("尚未确认", cli.stderr)


class GeneratedPythonBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.namespace = {"json": json, "sys": sys, "math": math}
        exec(generator.PYTHON_RESULT_HELPERS, self.namespace)

    def test_complete_answer_requires_stop_and_nonempty_text(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.namespace["checked_message"](reply()).content, "OK")
            for response in (reply("partial", "length"), reply("", "stop"), reply("partial", "aborted"), reply("partial", None), types.SimpleNamespace(choices=[], usage=None)):
                with self.assertRaises(RuntimeError):
                    self.namespace["checked_message"](response)

    def test_stream_usage_only_chunk_is_recorded_and_not_indexed(self):
        output, diagnostics = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostics):
            text = self.namespace["checked_stream"]([
                chunk(no_choices=True), chunk("O"), chunk("K"), chunk(reason="stop"),
                chunk(no_choices=True, usage={"completion_tokens": 2}),
            ])
        self.assertEqual(text, "OK")
        self.assertIn('"completion_tokens": 2', diagnostics.getvalue())

    def test_stream_truncated_missing_terminal_and_empty_answer_rejected(self):
        for stream in ([chunk("partial", "length")], [chunk("partial")], [chunk(reason="stop")], [chunk("partial", "content_filter")]):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    self.namespace["checked_stream"](stream)

    def test_stream_rejects_tool_delta_and_data_after_terminal(self):
        tool_delta = chunk("answer")
        tool_delta.choices[0].delta.tool_calls = [{"index": 0}]
        streams = [
            [tool_delta, chunk(reason="stop")],
            [chunk("OK", "stop"), chunk("new")],
            [chunk("OK", "stop"), chunk(reason="stop")],
            [chunk("OK", "length"), chunk(reason="stop")],
        ]
        for stream in streams:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    self.namespace["checked_stream"](stream)

    def test_interrupted_stream_still_records_usage_and_closes(self):
        class InterruptedStream:
            closed = False

            def __iter__(self):
                yield chunk("partial", usage={"completion_tokens": 7})
                raise ConnectionError("interrupted")

            def close(self):
                self.closed = True

        stream, diagnostics = InterruptedStream(), io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(diagnostics):
            with self.assertRaises(ConnectionError):
                self.namespace["checked_stream"](stream)
        self.assertTrue(stream.closed)
        self.assertIn('"completion_tokens": 7', diagnostics.getvalue())

    def test_full_generated_tool_loop_preserves_reasoning_and_tool_id(self):
        requests = []
        replies = iter([reply(None, "tool_calls", [tool_call()], "prior reasoning"), reply("42")])

        def create(**kwargs):
            requests.append(copy.deepcopy(kwargs))
            return next(replies)

        client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create)))
        fake_sdk = types.ModuleType("openai")
        fake_sdk.OpenAI = lambda **_: client
        card = generator.load_model("kimi-k2.6")
        source = generator.python_snippet(card, card["model_id"], "sum", False, "on", task="tool")
        with patch.dict(sys.modules, {"openai": fake_sdk}), patch.dict(os.environ, {"MOONSHOT_API_KEY": "test-placeholder"}), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(source, {})
        self.assertEqual(len(requests), 2)
        messages = requests[1]["messages"]
        self.assertEqual(messages[1]["reasoning_content"], "prior reasoning")
        self.assertEqual(messages[2]["tool_call_id"], "call_1")
        self.assertEqual(json.loads(messages[2]["content"]), {"result": 42})

    def test_tool_task_requires_actual_execution_but_chat_allows_direct_answer(self):
        client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda **_: reply("42"))))
        fake_sdk = types.ModuleType("openai")
        fake_sdk.OpenAI = lambda **_: client
        card = generator.load_model("kimi-k2.6")
        for task in ("tool", "chat"):
            source = generator.python_snippet(card, "kimi-k2.6", "sum", False, "off", task=task)
            output = io.StringIO()
            with patch.dict(sys.modules, {"openai": fake_sdk}), patch.dict(os.environ, {"MOONSHOT_API_KEY": "test-placeholder"}), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                if task == "tool":
                    with self.assertRaisesRegex(RuntimeError, "尚未实际执行工具"):
                        exec(source, {})
                else:
                    exec(source, {})
            self.assertEqual(output.getvalue(), "" if task == "tool" else "42\n")

    def test_generated_json_stream_publishes_only_one_validated_object(self):
        for text, expected_error in (('{"answer":"OK"}', None), ('{"wrong":1}', ValueError)):
            response = [chunk(text), chunk(reason="stop"), chunk(no_choices=True, usage={"completion_tokens": 5})]
            client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda **_: response)))
            fake_sdk = types.ModuleType("openai")
            fake_sdk.OpenAI = lambda **_: client
            card = generator.load_model("qwen-flash")
            source = generator.python_snippet(card, card["model_id"], "json", True, "off", task="json")
            output = io.StringIO()
            with patch.dict(sys.modules, {"openai": fake_sdk}), patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-placeholder"}), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                if expected_error:
                    with self.assertRaises(expected_error):
                        exec(source, {})
                else:
                    exec(source, {})
            if expected_error:
                self.assertEqual(output.getvalue(), "")
            else:
                self.assertEqual(json.loads(output.getvalue()), {"answer": "OK"})

    def test_generated_tool_validator_rejects_unknown_and_invalid_arguments(self):
        functions = generator.PYTHON_TOOL_LOOP.split("for _ in range(4):")[0]
        exec(functions, self.namespace)
        self.assertEqual(json.loads(self.namespace["execute_tool"](tool_call())), {"result": 42})
        for call in (tool_call(name="shell"), tool_call('{"a":true,"b":1}'), tool_call('{"a":1,"b":2,"extra":3}'), tool_call('{"a":NaN,"b":2}'), tool_call('{"a":1e309,"b":2}'), tool_call('[]')):
            with self.assertRaises(ValueError):
                self.namespace["execute_tool"](call)

    def test_tool_loop_rejects_reused_ids_and_validates_whole_batch(self):
        for replies in (
            [reply(None, "tool_calls", [tool_call()]), reply(None, "tool_calls", [tool_call()])],
            [reply(None, "tool_calls", [tool_call(), tool_call('{"a":true,"b":2}', call_id="call_2")])],
        ):
            responses = iter(replies)
            requests = []

            def create(**kwargs):
                requests.append(copy.deepcopy(kwargs))
                return next(responses)

            namespace = dict(self.namespace)
            namespace["client"] = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create)))
            namespace["request"] = {"messages": []}
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(ValueError):
                    exec(generator.PYTHON_TOOL_LOOP, namespace)
            if len(requests) == 1:
                self.assertEqual(namespace["request"]["messages"], [])


@unittest.skipUnless(shutil.which("node"), "Node.js absent; Python behavior tests still run")
class GeneratedTypeScriptBehaviorTests(unittest.TestCase):
    def run_typescript(self, body, include_helpers=True):
        version = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if int(version.stdout.strip().lstrip("v").split(".")[0]) < 24:
            self.skipTest("Node.js 24+ required for inline TypeScript stripping")
        script = (generator.TYPESCRIPT_RESULT_HELPERS + "\n" if include_helpers else "") + body
        result = subprocess.run(["node", "--input-type=module-typescript"], input=script, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_typescript_safely_consumes_usage_only_and_reports_errors(self):
        result = self.run_typescript('''
const chunks = [
  {choices: []},
  {choices: [{delta: {content: "OK"}, finish_reason: null}]},
  {choices: [{delta: {}, finish_reason: "stop"}]},
  {choices: [], usage: {completion_tokens: 2}},
];
const stream = {async *[Symbol.asyncIterator]() {yield* chunks;}};
if (await checkedStream(stream) !== "OK") throw new Error("unexpected text");
for (const reason of ["length", "aborted", null]) {
  const bad = {async *[Symbol.asyncIterator]() {yield {choices: [{delta: {content: "partial"}, finish_reason: reason}]};}};
  let rejected = false;
  try {await checkedStream(bad);} catch {rejected = true;}
  if (!rejected) throw new Error("incomplete stream accepted");
}
for (const response of [{choices: []}, {choices: [{message: {content: ""}, finish_reason: "stop"}]}, {choices: [{message: {content: "partial"}, finish_reason: "length"}]}]) {
  let rejected = false;
  try {checkedMessage(response);} catch {rejected = true;}
  if (!rejected) throw new Error("bad completion accepted");
}
for (const chunks of [
  [{choices: [{delta: {tool_calls: [{index: 0}]}, finish_reason: "stop"}]}],
  [{choices: [{delta: {content: "OK"}, finish_reason: "stop"}]}, {choices: [{delta: {content: "late"}, finish_reason: null}]}],
  [{choices: [{delta: {content: "OK"}, finish_reason: "stop"}]}, {choices: [{delta: {}, finish_reason: "stop"}]}],
]) {
  const bad = {async *[Symbol.asyncIterator]() {yield* chunks;}};
  let rejected = false;
  try {await checkedStream(bad);} catch {rejected = true;}
  if (!rejected) throw new Error("inconsistent stream accepted");
}
''')
        self.assertIn('"completion_tokens":2', result.stderr)

    def test_complete_typescript_json_stream_emits_one_object(self):
        card = generator.load_model("qwen-flash")
        source = generator.typescript_snippet(card, "qwen-flash", "json", True, "off", task="json")
        stub = '''const chunks = [
  {choices: [{delta: {content: '{"answer":"OK"}'}, finish_reason: null}]},
  {choices: [{delta: {}, finish_reason: "stop"}]},
  {choices: [], usage: {completion_tokens: 5}},
];
class OpenAI {
  constructor(_args: unknown) {}
  chat = {completions: {create: async (_request: unknown) => ({
    async *[Symbol.asyncIterator]() {yield* chunks;}
  })}};
}
process.env.DASHSCOPE_API_KEY = "test-placeholder";
'''
        source = source.replace('import OpenAI from "openai";\n', stub, 1)
        result = self.run_typescript(source, include_helpers=False)
        self.assertEqual(json.loads(result.stdout), {"answer": "OK"})


if __name__ == "__main__":
    unittest.main()
