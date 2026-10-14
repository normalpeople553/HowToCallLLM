"""豆包多轮对话：手动携带历史，只将完整回答写入会话。

官方来源：
- https://docs.volcengine.com/docs/ark/context-management?lang=zh
- https://docs.volcengine.com/docs/ark/text-generation?lang=zh
运行：python models/doubao/doubao-seed-2-1-pro-260628/examples/07_multi_turn.py
"""

import os

from openai import OpenAI


MODEL = "doubao-seed-2-1-pro-260628"


def completed_text(response):
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"回答未正常完成：{choice.finish_reason!r}；本轮不写入历史")
    message = choice.message
    if getattr(message, "tool_calls", None):
        raise RuntimeError("多轮文本示例不执行工具调用")
    if not isinstance(message.content, str) or not message.content.strip():
        raise RuntimeError("模型没有返回最终正文；本轮不写入历史")
    return message.content


def ask(client, history, question):
    candidate = history + [{"role": "user", "content": question}]
    response = client.chat.completions.create(
        model=MODEL,
        messages=candidate,
        extra_body={"thinking": {"type": "disabled"}},
    )
    text = completed_text(response)
    # 保留完整 assistant 对象，包括服务端可能返回的扩展字段。
    history.extend([candidate[-1], response.choices[0].message])
    return text


def main():
    client = OpenAI(
        api_key=os.environ["ARK_API_KEY"],
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        timeout=120,
    )
    history = [{"role": "system", "content": "你是简洁的项目助手。"}]
    # 固定两轮演示；交互应用应另设会话长度和上下文预算。
    for question in ("我的项目叫海棠，是一个读书笔记工具。先建议一个核心功能。", "基于刚才的项目和功能，再写一句产品介绍。"):
        print(ask(client, history, question))
    return history


if __name__ == "__main__":
    history = main()
