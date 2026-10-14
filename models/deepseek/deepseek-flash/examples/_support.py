"""本目录进阶示例的项目校验；不是官方 SDK，也不覆盖所有服务端限制。

协议来源：
https://api-docs.deepseek.com/guides/vision/
https://api-docs.deepseek.com/guides/tool_calls/
https://api-docs.deepseek.com/guides/thinking_mode/
轮次上限、模拟天气及输入预检查是本项目的示例约定。
"""

import base64
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from openai import OpenAI


def make_client(*, beta=False):
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com/beta" if beta else "https://api.deepseek.com",
        timeout=120,
    )


def completed_text(response):
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop" or getattr(choice.message, "tool_calls", None):
        raise RuntimeError(f"正文未完整完成：{choice.finish_reason!r}")
    text = choice.message.content
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("没有最终正文；请检查思考与回答预算")
    return text


def image_bytes(path, *, max_bytes=32 * 1024 * 1024):
    path = Path(path)
    if path.stat().st_size > max_bytes:
        raise ValueError("图片超过本例所用输入方式的单文件大小限制")
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif data.startswith((b"GIF87a", b"GIF89a")):
        mime = "image/gif"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        raise ValueError("请选择实际内容为 PNG、JPEG、GIF 或 WebP 的图片")
    return data, mime


def image_url_from_env():
    url, path = os.getenv("IMAGE_URL"), os.getenv("IMAGE_PATH")
    if bool(url) == bool(path):
        raise ValueError("请只设置 IMAGE_URL 或 IMAGE_PATH 中的一个")
    if path:
        data, mime = image_bytes(path)
        return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
    parsed = urlparse(url)
    # 官方支持 HTTP(S)；本例对用户提供的远程地址采用更窄的 HTTPS 约定。
    if parsed.scheme != "https" or not parsed.hostname or len(url) > 8192:
        raise ValueError("本例 IMAGE_URL 需为不超过 8192 字符的公开 HTTPS 图片地址")
    return url


def image_detail():
    detail = os.getenv("IMAGE_DETAIL", "auto")
    if detail not in {"low", "high", "original", "auto"}:
        raise ValueError("IMAGE_DETAIL 必须是 low/high/original/auto")
    return detail


def weather_loop(client, *, thinking, strict=False):
    """完整 assistant 原样回传，保留 reasoning_content；不执行模型生成的代码。"""
    function = {
        "name": "get_weather",
        "description": "返回城市的教学模拟天气，不是实时天气",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    }
    if strict:
        function["strict"] = True
    messages = [
        {"role": "system", "content": "天气查询必须使用 get_weather，并说明结果为教学模拟数据。"},
        {"role": "user", "content": "杭州天气如何？"},
    ]
    used_ids = set()
    executed = 0
    for turn in range(6):
        result = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            tools=[{"type": "function", "function": function}],
            tool_choice="auto",
            max_tokens=16384 if thinking else 2048,
            extra_body={"thinking": {"type": "enabled" if thinking else "disabled"}},
        )
        if not result.choices:
            raise RuntimeError("响应没有 choices")
        choice = result.choices[0]
        calls = choice.message.tool_calls or []
        if not calls:
            answer = completed_text(result)
            if not executed:
                raise RuntimeError("模型未执行工具，未完成示例闭环")
            return answer
        if choice.finish_reason != "tool_calls" or turn == 5:
            raise RuntimeError("工具调用未完整结束或已达到轮次上限")
        planned = []
        for call in calls:
            if getattr(call, "type", None) != "function" or call.function.name != "get_weather":
                raise ValueError("拒绝未注册的工具")
            if not isinstance(call.id, str) or not call.id or call.id in used_ids:
                raise ValueError("工具调用 ID 为空或重复")
            args = json.loads(call.function.arguments)
            if not isinstance(args, dict) or set(args) != {"city"}:
                raise ValueError("工具参数只能包含 city")
            city = args["city"]
            if not isinstance(city, str) or not city.strip() or len(city) > 80 or any(ord(c) < 32 for c in city):
                raise ValueError("city 必须为 1–80 字符的非空城市名，不能含控制字符")
            used_ids.add(call.id)
            planned.append((call.id, city.strip()))
        # 先校验整批参数，再执行本地函数；strict 也不能替代应用侧验证。
        messages.append(choice.message)
        for call_id, city in planned:
            messages.append({
                "role": "tool", "tool_call_id": call_id,
                "content": json.dumps({"city": city, "weather": "晴", "simulated": True}, ensure_ascii=False),
            })
            executed += 1
    raise RuntimeError("达到模型调用次数上限")
