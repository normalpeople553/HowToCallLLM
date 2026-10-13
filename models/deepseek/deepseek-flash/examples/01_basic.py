"""DeepSeek Chat Completions 最小调用。

官方来源：https://api-docs.deepseek.com/guides/codex
"""

import os

from openai import OpenAI


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=60,
)

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)

print(response.choices[0].message.content)
print(response.usage)
