"""Paid GLM examples: retry/stream/tool boundaries with SDK-like offline fixtures."""

from contextlib import contextmanager, redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from test_examples import SDKStream, chunk, fake_sdk, response, tool_call


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "models/zhipu/glm-4.7/examples"
FILES = ("01_basic.py", "02_streaming.py", "03_thinking.py", "04_json_output.py", "05_tool_calling.py", "06_multi_turn.py", "07_thinking_tools.py")
PRIVATE = "offline-private-error-not-a-real-key"


class ProviderError(Exception):
    def __init__(self, status=429, code="1305", retry_after=None, nested=True):
        super().__init__(PRIVATE)
        self.status_code = status
        detail = {"code": code, "message": PRIVATE}
        self.body = {"error": detail} if nested else detail
        self.response = SimpleNamespace(headers={} if retry_after is None else {"retry-after": retry_after})


@contextmanager
def imported(filename, replies=()):
    with fake_sdk(replies) as sdk, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        namespace = runpy.run_path(str(DIRECTORY / filename), run_name="offline_glm_import")
        with patch.object(namespace["time"], "sleep") as sleep, patch.object(namespace["random"], "uniform", return_value=0):
            yield sdk, namespace, sleep


class PaidGLMExampleTests(unittest.TestCase):
    def test_imports_are_side_effect_free_and_client_disables_nested_sdk_retries(self):
        for filename in FILES:
            with self.subTest(file=filename), imported(filename) as (sdk, namespace, _):
                with patch.dict(os.environ, {}, clear=True):
                    runpy.run_path(str(DIRECTORY / filename), run_name="offline_no_credentials")
                self.assertEqual(sdk.initializations, [])
                self.assertEqual(sdk.calls, [])
                namespace["make_client"]()
                self.assertEqual(sdk.initializations[0]["max_retries"], 0)
                self.assertEqual(sdk.initializations[0]["base_url"], "https://open.bigmodel.cn/api/paas/v4/")

    def test_only_documented_rate_limit_codes_retry_with_three_attempt_bound(self):
        for filename in FILES:
            for code in ("1302", "1305"):
                for nested in (False, True):
                    with self.subTest(file=filename, code=code, nested=nested), imported(filename, [ProviderError(code=code, nested=nested), ProviderError(code=code, nested=nested), response()]) as (sdk, namespace, sleep):
                        result = namespace["create_with_backoff"](sdk.client, model="glm-4.7", messages=[])
                        self.assertEqual(result.choices[0].finish_reason, "stop")
                        self.assertEqual(len(sdk.calls), 3)
                        self.assertEqual(sleep.call_args_list, [call(1), call(2)])
                        self.assertTrue(all(request["model"] == "glm-4.7" for request in sdk.calls))
            with self.subTest(file=filename, case="exhausted"), imported(filename, [ProviderError()] * 3) as (sdk, namespace, sleep):
                with self.assertRaises(RuntimeError) as error:
                    namespace["create_with_backoff"](sdk.client, model="glm-4.7", messages=[])
                self.assertEqual(len(sdk.calls), 3)
                self.assertEqual(sleep.call_args_list, [call(1), call(2)])
                self.assertNotIn(PRIVATE, str(error.exception))

    def test_quota_auth_and_other_failures_are_not_retried_or_leaked(self):
        for filename in FILES:
            for status, code in ((429, "1113"), (429, "1308"), (429, "unknown"), (401, "1305"), (500, "1302")):
                with self.subTest(file=filename, status=status, code=code), imported(filename, [ProviderError(status=status, code=code)]) as (sdk, namespace, sleep):
                    with self.assertRaises(RuntimeError) as error:
                        namespace["create_with_backoff"](sdk.client, model="glm-4.7", messages=[])
                    self.assertEqual(len(sdk.calls), 1)
                    sleep.assert_not_called()
                    self.assertNotIn(PRIVATE, str(error.exception))

    def test_retry_after_is_respected_but_long_wait_stops_without_another_request(self):
        for filename in FILES:
            with self.subTest(file=filename, case="bounded"), imported(filename, [ProviderError(retry_after="5"), response()]) as (sdk, namespace, sleep):
                namespace["create_with_backoff"](sdk.client, model="glm-4.7", messages=[])
                self.assertEqual(len(sdk.calls), 2)
                sleep.assert_called_once_with(5)
            with self.subTest(file=filename, case="too-long"), imported(filename, [ProviderError(retry_after="31")]) as (sdk, namespace, sleep):
                with self.assertRaises(RuntimeError):
                    namespace["create_with_backoff"](sdk.client, model="glm-4.7", messages=[])
                self.assertEqual(len(sdk.calls), 1)
                sleep.assert_not_called()

    def test_stream_success_closes_and_failure_never_replays_consumed_data(self):
        stream = SDKStream([chunk("complete"), chunk(reason="stop")])
        with imported("02_streaming.py", [stream]) as (sdk, namespace, sleep):
            self.assertEqual(namespace["main"](), "complete")
            self.assertTrue(stream.closed)
            self.assertEqual(len(sdk.calls), 1)
            sleep.assert_not_called()

        def interrupted():
            yield chunk("partial")
            raise ConnectionError(PRIVATE)

        stream = SDKStream(interrupted())
        with imported("02_streaming.py", [stream]) as (sdk, namespace, sleep):
            with self.assertRaises(RuntimeError) as error:
                namespace["main"]()
            self.assertTrue(stream.closed)
            self.assertEqual(len(sdk.calls), 1)
            sleep.assert_not_called()
            self.assertNotIn(PRIVATE, str(error.exception))

    def test_stream_close_failure_cannot_return_a_success(self):
        stream = SDKStream([chunk("complete", "stop")])
        stream.close = Mock(side_effect=OSError(PRIVATE))
        with imported("02_streaming.py", [stream]) as (_, namespace, _):
            with self.assertRaises(RuntimeError) as error:
                namespace["main"]()
            stream.close.assert_called_once()
            self.assertNotIn(PRIVATE, str(error.exception))

    def test_model_http_retry_does_not_reexecute_local_tool_or_change_its_history(self):
        for filename, name, arguments in (("05_tool_calling.py", "get_weather", '{"city":"杭州"}'), ("07_thinking_tools.py", "get_inventory", '{"sku":"SKU-001"}')):
            first = response(None, "tool_calls", [tool_call(name=name, arguments=arguments)])
            with self.subTest(file=filename), imported(filename, [first, ProviderError(), response("simulated final answer")]) as (sdk, namespace, sleep):
                tool = Mock(wraps=namespace[name])
                with patch.dict(namespace["main"].__globals__, {name: tool}):
                    namespace["main"]()
                self.assertEqual(tool.call_count, 1)
                self.assertEqual(len(sdk.calls), 3)
                self.assertEqual(sdk.calls[1], sdk.calls[2])
                self.assertEqual(sdk.calls[1]["messages"][2], first.choices[0].message.model_dump(exclude_none=True))
                self.assertEqual(sdk.calls[1]["messages"][3]["tool_call_id"], "call_1")
                sleep.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
