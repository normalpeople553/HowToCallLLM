"""多轮对话：应用把历史消息随每次请求重新发送。对应 docs/02。

运行前：
    export DEEPSEEK_API_KEY="sk-你的key"
运行：
    python3 04_multi_turn.py
"""

import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

# messages 就是“聊天记录本”，每轮往里追加
messages = [
    {"role": "system", "content": "你是一个简洁的助手。"},
]


def ask(question: str) -> str:
    messages.append({"role": "user", "content": question})    # 先记下用户这句
    resp = client.chat.completions.create(
        model="deepseek-flash",
        messages=messages,                                    # 把整本记录发过去
    )
    answer = resp.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})  # 再记下模型回答
    return answer


print(ask("我叫小明，今年26岁。"))
print(ask("我叫什么名字？多少岁？"))
