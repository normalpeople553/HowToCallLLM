"""DeepSeek 最短调用片段（实测 2026-10-13）。export DEEPSEEK_API_KEY=..."""
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

# ① 默认（v4 模型默认开思考，思考链在 message.reasoning_content）
r = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=512,
)
print(r.choices[0].message.content)

# ② 关闭思考（省钱省时）
r = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "你好"}],
    extra_body={"thinking": {"type": "disabled"}},
)

# ③ 流式
stream = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "讲个冷笑话"}],
    stream=True,
    extra_body={"thinking": {"type": "disabled"}},
)
for c in stream:
    print(c.choices[0].delta.content or "", end="", flush=True)
