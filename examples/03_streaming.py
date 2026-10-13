"""流式输出（打字机效果）。对应 book/02。

运行前：
    export DEEPSEEK_API_KEY="sk-你的key"
运行：
    python3 03_streaming.py
"""

import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

stream = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "用30个字讲个冷笑话"}],
    stream=True,                                               # 关键：开启流式
)

for chunk in stream:
    delta = chunk.choices[0].delta.content or ""               # 每个片段可能为空
    print(delta, end="", flush=True)                           # 不换行立即刷出

print()                                                        # 结尾补个换行
