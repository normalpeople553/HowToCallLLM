"""Kimi 图片输入：IMAGE_PATH 指向本地 PNG/JPEG，编码为 base64 data URL。

官方视觉文档明确不支持直接传远程图片 URL，本例拒绝 IMAGE_URL。
官方来源：
- https://platform.kimi.com/docs/guide/use-kimi-vision-model
- https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart
来源清单、改编内容和验证范围见同目录 sources.json。
"""

import base64
import os
from pathlib import Path

from openai import OpenAI


def completed_text(response) -> str:
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"回答未完整结束：{choice.finish_reason!r}，请检查输出和思考预算")
    if getattr(choice.message, "tool_calls", None):
        raise RuntimeError("收到未处理的工具调用")
    content = choice.message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("没有最终正文")
    return content

def image_content(image_path: str) -> list[dict]:
    path = Path(image_path)
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(path.suffix.lower())
    if mime is None:
        raise ValueError("本例的本地文件请选择 PNG 或 JPEG")
    payload = path.read_bytes()
    if not payload:
        raise ValueError("图片文件为空")
    image_url = f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}"
    return [
        {"type": "text", "text": "请客观描述这张图片。"},
        {"type": "image_url", "image_url": {"url": image_url}},
    ]


def main() -> None:
    if os.environ.get("IMAGE_URL"):
        raise ValueError("Kimi 官方文档不支持远程图片 URL；请清除 IMAGE_URL 并设置 IMAGE_PATH")
    image_path = os.environ.get("IMAGE_PATH")
    if not image_path:
        raise ValueError("请设置 IMAGE_PATH 为本地 PNG 或 JPEG 文件")
    content = image_content(image_path)
    client = OpenAI(
        api_key=os.environ["MOONSHOT_API_KEY"],
        base_url="https://api.moonshot.cn/v1",
        timeout=120,
    )
    response = client.chat.completions.create(
        model="kimi-k2.6",
        messages=[{"role": "user", "content": content}],
        extra_body={"thinking": {"type": "disabled"}},
    )
    print(completed_text(response))


if __name__ == "__main__":
    main()
