"""通义千问 思考模式：验证最终回答，而不是只看是否产生思考。

官方来源：https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/
"""

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
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    timeout=120,
)

response = client.chat.completions.create(
    model="qwen-flash",
    messages=[{"role": "user", "content": "比较 9.11 和 9.8，只给结论和一句解释。"}],
    extra_body={"enable_thinking": True},
)
answer = completed_text(response)
print("思考内容：", getattr(response.choices[0].message, "reasoning_content", None))
print("最终回答：", answer)
print("本次用量：", response.usage)
