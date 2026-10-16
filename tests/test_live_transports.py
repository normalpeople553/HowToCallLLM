"""真实 Node fetch / /usr/bin/curl 的 loopback 测试；无厂商 API 或真实 Key。"""

import contextlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Thread
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("live_curl_transport_tests", ROOT / "tests/live_curl.py")
curl_observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(curl_observer)
SECRET = "offline-private-key-fixture"
PROMPT = "offline-private-prompt-fixture"
ANSWER = "offline-private-answer-fixture"
REASONING = "offline-private-reasoning-fixture"
RAW_ERROR = "offline-private-error-fixture"
RESPONSE_ID = "offline-private-response-id-fixture"
NODE = shutil.which("node")


def node_major_version():
    if not NODE:
        return None
    try:
        completed = subprocess.run(
            [NODE, "--version"], capture_output=True, text=True, timeout=5,
        )
        if completed.returncode == 0:
            return int(completed.stdout.strip().lstrip("v").split(".", 1)[0])
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return None


NODE_MAJOR = node_major_version()


def native_process_env():
    """Return a credential-free environment that still supports Windows processes."""
    environment = {"PATH": os.defpath}
    for name in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    return environment


@unittest.skipUnless(NODE_MAJOR is not None and NODE_MAJOR >= 24, "requires Node.js >=24/native fetch; no mock fallback")
class NativeFetchObserverTests(unittest.TestCase):
    def test_native_fetch_original_response_privacy_429_and_redirect_isolation(self):
        # A minimal environment prevents inherited observer preload/configuration
        # or credentials from affecting this entirely local test.
        completed = subprocess.run(
            [NODE, str(ROOT / "tests/live_fetch_checks.mjs")], cwd=ROOT,
            env=native_process_env(), capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["origin_requests"], 3)
        self.assertEqual(result["redirected_requests"], 0)
        self.assertEqual(set(result["checks"]), {
            "original_response", "original_body_and_headers", "privacy", "http_429",
            "redirect_307_rejected", "unallowlisted_url_rejected",
        })
        for value in (SECRET, PROMPT, ANSWER, REASONING, RAW_ERROR, RESPONSE_ID):
            self.assertNotIn(value, completed.stdout + completed.stderr)


@unittest.skipUnless(Path(curl_observer.CURL).is_file(), "requires actual /usr/bin/curl; no mock fallback")
class NativeCurlObserverTests(unittest.TestCase):
    def test_actual_curl_forwards_original_bytes_and_records_only_safe_metadata(self):
        self.assertIn("deepseek-v4-pro", curl_observer.MODELS)
        request_body = json.dumps({"model": "deepseek-flash", "messages": [{"role": "user", "content": PROMPT}]}).encode()
        response_body = json.dumps({
            "id": RESPONSE_ID, "model": "deepseek-flash",
            "choices": [{"finish_reason": "stop", "message": {"content": ANSWER, "reasoning_content": REASONING}}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5, "private": SECRET},
        }).encode()
        received, errors = [], []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append((self.rfile.read(int(self.headers["content-length"])), self.headers.get("authorization")))
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)

            def log_message(self, *_args):
                pass

            def handle(self):
                try:
                    super().handle()
                except Exception as error:
                    errors.append(type(error).__name__)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_address[1]}/chat/completions"
            stdout, stderr = types.SimpleNamespace(buffer=io.BytesIO()), io.StringIO()
            with tempfile.TemporaryDirectory() as temporary:
                telemetry = Path(temporary) / "telemetry.json"
                with patch.dict(os.environ, {"PATH": os.defpath}, clear=True), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code = curl_observer.run([
                        "--silent", "--show-error", "--fail", "--max-time", "3", endpoint,
                        "-H", "Authorization: Bearer " + SECRET,
                        "-H", "Content-Type: application/json", "--data-binary", "@-",
                    ], request_body, str(telemetry), endpoints={endpoint})
                saved = telemetry.read_text(encoding="utf-8")
            self.assertEqual(code, 0)
            self.assertEqual(stdout.buffer.getvalue(), response_body)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(received, [(request_body, "Bearer " + SECRET)])
            self.assertEqual(errors, [])
            report = json.loads(saved)
            self.assertEqual(report["exit_code"], 0)
            self.assertEqual(len(report["requests"]), 1)
            record = report["requests"][0]
            self.assertEqual(record["transport"], "real_curl")
            self.assertEqual(record["requested_model"], "deepseek-flash")
            self.assertEqual(record["http_status"], 200)
            self.assertEqual(record["finish_reasons"], ["stop"])
            self.assertEqual(record["content_chars"], len(ANSWER))
            self.assertEqual(record["observation_status"], "json_observed")
            self.assertEqual(record["usage"], {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5})
            for value in (SECRET, PROMPT, ANSWER, REASONING, RAW_ERROR, RESPONSE_ID):
                self.assertNotIn(value, saved + stderr.getvalue())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
