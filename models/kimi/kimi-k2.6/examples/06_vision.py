"""Kimi 图片输入：IMAGE_URL（公开 HTTPS URL）或 IMAGE_PATH（二选一）。

本例本地文件使用 PNG/JPEG；保留 content 数组，不把数组序列化成字符串。
官方来源：https://platform.kimi.com/docs/guide/use-kimi-vision-model
"""

import base64
import os
from pathlib import Path
from urllib.parse import urlparse

from openai import OpenAI


def completed_text(response) -> str:
    """应用检查：只有正常结束且非空的正文才能当作完整结果。"""
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(
            f"回答未正常完成：finish_reason={choice.finish_reason!r}；"
            "length 表示达到生成或上下文限制，请检查思考与回答预算"
        )
    content = choice.message.content
    if getattr(choice.message, "tool_calls", None):
        raise RuntimeError("收到未处理的工具调用")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("模型没有返回最终正文；请检查思考预算和提示词")
    return content

image_url = os.getenv("IMAGE_URL")
image_path = os.getenv("IMAGE_PATH")
if bool(image_url) == bool(image_path):
    raise ValueError("请只设置 IMAGE_URL 或 IMAGE_PATH 中的一个")
if image_path:
    path = Path(image_path)
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(path.suffix.lower())
    if mime is None:
        raise ValueError("本例的本地文件请选择 PNG 或 JPEG")
    image_url = f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
else:
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("IMAGE_URL 请使用模型服务能访问的公开 HTTPS 地址")

client = OpenAI(
    api_key=os.environ["MOONSHOT_API_KEY"],
    base_url="https://api.moonshot.cn/v1",
    timeout=120,
)

response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请客观描述这张图片。"},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ],
    extra_body={"thinking": {"type": "disabled"}},
)
print(completed_text(response))

