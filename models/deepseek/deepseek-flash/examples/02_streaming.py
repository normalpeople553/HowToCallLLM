"""同时处理 DeepSeek 流式思考与正文。

官方来源：
- https://api-docs.deepseek.com/api/create-chat-completion/
- https://api-docs.deepseek.com/guides/thinking_mode/
"""

import os

from openai import OpenAI


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=120,
)

stream = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": "用三句话解释上下文缓存"}],
    stream=True,
)

in_answer = False
for chunk in stream:
    delta = chunk.choices[0].delta
    reasoning = getattr(delta, "reasoning_content", None)
    if reasoning:
        print(reasoning, end="", flush=True)
    if delta.content:
        if not in_answer:
            print("\n\n--- 正文 ---\n", end="")
            in_answer = True
        print(delta.content, end="", flush=True)
print()
