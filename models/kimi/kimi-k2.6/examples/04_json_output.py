"""Kimi JSON 输出：检查完成状态、解析和业务字段。

官方来源：https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api
"""

import json
import os

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

client = OpenAI(
    api_key=os.environ["MOONSHOT_API_KEY"],
    base_url="https://api.moonshot.cn/v1",
    timeout=120,
)

response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": '只返回 json 对象：{"ok":true}'}],
    response_format={"type": "json_object"},
    extra_body={"thinking": {"type": "disabled"}},
)
data = json.loads(completed_text(response))
if not isinstance(data, dict) or set(data) != {"ok"} or data["ok"] is not True:
    raise ValueError("JSON 可解析，但不符合本例业务要求：ok 必须是 true")
print(data)
