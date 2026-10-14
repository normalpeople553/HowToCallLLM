"""Kimi K2.6 视频理解：本地 MP4 编码成 data:video/mp4;base64。

设置 VIDEO_PATH 为短小的本地 MP4 文件；本例不处理远程视频 URL 或文件上传。
官方来源：
- https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart （视频理解代码示例）
- https://platform.kimi.com/docs/guide/use-kimi-vision-model （base64 与文件上传）
来源、改编内容和验证范围见同目录 sources.json。
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

def video_content(video_path: str) -> list[dict]:
    path = Path(video_path)
    if path.suffix.lower() != ".mp4":
        raise ValueError("本例仅演示本地 MP4，请配置 VIDEO_PATH")
    payload = path.read_bytes()
    if not payload:
        raise ValueError("视频文件为空")
    video_url = "data:video/mp4;base64," + base64.b64encode(payload).decode("ascii")
    return [
        {"type": "video_url", "video_url": {"url": video_url}},
        {"type": "text", "text": "按时间顺序概括这个视频中可见的事件，不要编造画面外的信息。"},
    ]


def main() -> None:
    video_path = os.environ.get("VIDEO_PATH")
    if not video_path:
        raise ValueError("请配置 VIDEO_PATH；本例只演示本地 MP4 -> base64 的官方流程")
    content = video_content(video_path)
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
