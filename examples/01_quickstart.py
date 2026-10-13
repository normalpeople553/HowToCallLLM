"""最小可运行示例：调用 DeepSeek 说一句话。对应 book/01。

运行前：
    export DEEPSEEK_API_KEY="sk-你的key"
    pip3 install openai
运行：
    python3 01_quickstart.py
"""

import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],          # key 从环境变量读，别写死
    base_url="https://api.deepseek.com",             # DeepSeek 接入地址
)

resp = client.chat.completions.create(
    model="deepseek-v4-flash",                       # 模型名
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)

print(resp.choices[0].message.content)               # 取出回答正文
print("本次用量：", resp.usage)                      # 花了多少 token
