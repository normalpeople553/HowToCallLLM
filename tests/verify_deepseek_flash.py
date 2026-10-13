"""对 deepseek-flash 做真实、脱敏的能力验证。

本脚本会产生真实 API 请求和费用，只输出测试状态、token 数和内容长度；
不会输出 API Key、模型回答、思考内容、工具参数或请求 ID。

官方能力来源：skills/model-manual/references/models/deepseek-flash.json
"""

import base64
import json
import os
import struct
import sys
import zlib
from collections.abc import Callable

from openai import OpenAI


MODEL = "deepseek-flash"


def make_test_png(width: int = 64, height: int = 64) -> bytes:
    """只用标准库生成有效的 8-bit RGB PNG，避免测试依赖外部图片。"""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    scanlines = b"".join(b"\x00" + b"\xff\x00\x00" * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(scanlines))
        + chunk(b"IEND", b"")
    )


def require_content(response) -> str:
    content = response.choices[0].message.content or ""
    if not content.strip():
        raise AssertionError("正文为空")
    return content


def usage_summary(response) -> str:
    usage = response.usage
    if not usage:
        return "usage unavailable"
    return f"input={usage.prompt_tokens}, output={usage.completion_tokens}"


def main() -> int:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        print("未设置 DEEPSEEK_API_KEY；未发送任何请求。")
        return 2

    client = OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=180)

    tests: list[tuple[str, Callable[[], str]]] = []

    def basic() -> str:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "只回复：收到"}],
            max_tokens=128,
        )
        content = require_content(response)
        return f"{usage_summary(response)}, chars={len(content)}"

    tests.append(("普通调用", basic))

    def streaming() -> str:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "只回复：流式正常"}],
            extra_body={"thinking": {"type": "disabled"}},
            max_tokens=128,
            stream=True,
        )
        parts = [chunk.choices[0].delta.content or "" for chunk in stream]
        content = "".join(parts)
        if not content.strip():
            raise AssertionError("流式正文为空")
        return f"chars={len(content)}"

    tests.append(("流式输出", streaming))

    def thinking_on() -> str:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "9.11 和 9.8 哪个更大？"}],
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
            max_tokens=1024,
        )
        content = require_content(response)
        reasoning = getattr(response.choices[0].message, "reasoning_content", None) or ""
        if not reasoning.strip():
            raise AssertionError("未收到 reasoning_content")
        return f"{usage_summary(response)}, reasoning_chars={len(reasoning)}, answer_chars={len(content)}"

    tests.append(("开启思考", thinking_on))

    def thinking_off() -> str:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "1+1 等于几？"}],
            extra_body={"thinking": {"type": "disabled"}},
            max_tokens=128,
        )
        require_content(response)
        reasoning = getattr(response.choices[0].message, "reasoning_content", None)
        if reasoning:
            raise AssertionError("关闭思考后仍收到 reasoning_content")
        return usage_summary(response)

    tests.append(("关闭思考", thinking_off))

    def json_output() -> str:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": '只返回 json，例如：{"ok":true}'},
                {"role": "user", "content": "返回 ok 为 true 的 json"},
            ],
            response_format={"type": "json_object"},
            extra_body={"thinking": {"type": "disabled"}},
            max_tokens=128,
        )
        data = json.loads(require_content(response))
        if data.get("ok") is not True:
            raise AssertionError("JSON 内容不符合要求")
        return usage_summary(response)

    tests.append(("JSON Output", json_output))

    def tool_calling() -> str:
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询城市天气",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }]
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "查询杭州天气"}],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "get_weather"}},
            extra_body={"thinking": {"type": "disabled"}},
            max_tokens=256,
        )
        calls = response.choices[0].message.tool_calls or []
        if not calls or calls[0].function.name != "get_weather":
            raise AssertionError("未收到预期工具调用")
        arguments = json.loads(calls[0].function.arguments)
        if not isinstance(arguments.get("city"), str):
            raise AssertionError("工具参数无效")
        return f"{usage_summary(response)}, calls={len(calls)}"

    tests.append(("Tool Calling", tool_calling))

    def vision() -> str:
        encoded = base64.b64encode(make_test_png()).decode("ascii")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "确认你收到了一张图片，只需简短回答。"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{encoded}", "detail": "low"},
                    },
                ],
            }],
            extra_body={"thinking": {"type": "disabled"}},
            max_tokens=128,
        )
        content = require_content(response)
        return f"{usage_summary(response)}, chars={len(content)}"

    tests.append(("图片输入", vision))

    failed = 0
    for name, test in tests:
        try:
            detail = test()
            print(f"PASS {name}: {detail}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {str(exc)[:160]}")

    print(f"完成：{len(tests) - failed}/{len(tests)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
