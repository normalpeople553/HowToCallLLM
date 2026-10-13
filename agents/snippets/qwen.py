"""通义千问（百炼）最短调用片段（实测 2026-10-13）。export DASHSCOPE_API_KEY=...
百炼思考开关是 enable_thinking，和其他四家的 thinking.type 不同。"""
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"],
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

# ① qwen-flash 别名：快、便宜，本身不思考
r = client.chat.completions.create(
    model="qwen-flash",
    messages=[{"role": "user", "content": "你好"}],
)
print(r.choices[0].message.content)

# ② 用带思考的 qwen3.6-flash，并演示关闭思考（enable_thinking 百炼独一份）
r = client.chat.completions.create(
    model="qwen3.6-flash",
    messages=[{"role": "user", "content": "13*29 等于几"}],
    extra_body={"enable_thinking": False},
)

# ③ 流式
stream = client.chat.completions.create(
    model="qwen-flash",
    messages=[{"role": "user", "content": "讲个冷笑话"}],
    stream=True,
)
for c in stream:
    print(c.choices[0].delta.content or "", end="", flush=True)
