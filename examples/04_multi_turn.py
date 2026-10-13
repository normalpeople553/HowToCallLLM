"""多轮对话：每次发送历史消息，完整成功后再记入对话。

运行前配置 DEEPSEEK_API_KEY，安装 openai 后执行本文件。
官方来源：https://api-docs.deepseek.com/guides/thinking_mode/
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
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=120,
)
messages = [{"role": "system", "content": "你是一个简洁的助手。"}]


def ask(question: str) -> str:
    user_message = {"role": "user", "content": question}
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[*messages, user_message],
        extra_body={"thinking": {"type": "disabled"}},
    )
    answer = completed_text(response)
    messages.extend([user_message, {"role": "assistant", "content": answer}])
    return answer


if __name__ == "__main__":
    print(ask("我叫小明，今年26岁。"))
    print(ask("我叫什么名字？多少岁？"))
