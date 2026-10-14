"""Kimi 多轮对话：完整成功后才把本轮 user/assistant 写入历史。

官方来源：
- https://platform.kimi.com/docs/guide/engage-in-multi-turn-conversations-using-kimi-api
- https://platform.kimi.com/docs/guide/use-thinking-models
来源清单、改编内容和验证范围见同目录 sources.json。
"""

import os

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

def ask(client, messages: list, question: str) -> str:
    user_message = {"role": "user", "content": question}
    response = client.chat.completions.create(
        model="kimi-k2.6",
        messages=[*messages, user_message],
        extra_body={"thinking": {"type": "disabled"}},
    )
    answer = completed_text(response)
    # 保留完整 assistant 对象；失败或截断时不污染本地历史。
    messages.extend([user_message, response.choices[0].message])
    return answer


def main() -> None:
    client = OpenAI(
        api_key=os.environ["MOONSHOT_API_KEY"],
        base_url="https://api.moonshot.cn/v1",
        timeout=120,
    )
    messages = [{"role": "system", "content": "你是简洁的助手，结合已有对话回答。"}]
    print(ask(client, messages, "我叫小明，今年26岁。"))
    print(ask(client, messages, "我叫什么名字？今年多少岁？"))


if __name__ == "__main__":
    main()
