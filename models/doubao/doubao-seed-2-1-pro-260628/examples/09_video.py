"""豆包视频理解：通过 VIDEO_URL 传入服务端可访问的视频 HTTPS URL。

官方来源：
- https://docs.volcengine.com/docs/ark/video-understanding?lang=zh
  “支持模型”指向视觉理解能力表；“视频 URL 传入”给出 Chat API 格式。
- https://docs.volcengine.com/docs/ark/model-list?lang=zh
  “视觉理解能力→往期模型”明确列出 doubao-seed-2-1-pro-260628。
仅使用 video_url.url；不套用新版本文件预处理、音频或抽帧参数。
运行前设置 ARK_API_KEY 与 VIDEO_URL；本例不下载或上传视频文件。
"""

import os
from urllib.parse import urlparse

from openai import OpenAI


def completed_text(response):
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"视频回答未正常完成：{choice.finish_reason!r}")
    message = choice.message
    if getattr(message, "tool_calls", None):
        raise RuntimeError("视频示例没有工具执行器")
    if not isinstance(message.content, str) or not message.content.strip():
        raise RuntimeError("模型没有返回视频描述正文")
    return message.content


def main():
    video_url = os.environ.get("VIDEO_URL", "")
    parsed = urlparse(video_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("请设置方舟服务能访问的 HTTPS VIDEO_URL；不要在 URL 中放用户名或密码")
    client = OpenAI(
        api_key=os.environ["ARK_API_KEY"],
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        timeout=120,
    )
    response = client.chat.completions.create(
        model="doubao-seed-2-1-pro-260628",
        messages=[{
            "role": "user",
            "content": [
                {"type": "video_url", "video_url": {"url": video_url}},
                {"type": "text", "text": "描述视频中的主要场景和动作；看不清的信息请说明。"},
            ],
        }],
        extra_body={"thinking": {"type": "disabled"}},
    )
    print(completed_text(response))


if __name__ == "__main__":
    main()
