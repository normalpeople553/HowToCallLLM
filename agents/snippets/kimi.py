"""Kimi 最短调用片段（实测 2026-10-13）。export MOONSHOT_API_KEY=...
注意：moonshot-v1-* 老模型名新账号已 404，当前用 kimi-k2.6 / kimi-k3。"""
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["MOONSHOT_API_KEY"], base_url="https://api.moonshot.cn/v1")

# ① 默认（k2.6 默认开思考）
r = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=512,
)
print(r.choices[0].message.content)

# ② 关闭思考
r = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "你好"}],
    extra_body={"thinking": {"type": "disabled"}},
)

# ③ 流式
stream = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "讲个冷笑话"}],
    stream=True,
    extra_body={"thinking": {"type": "disabled"}},
)
for c in stream:
    print(c.choices[0].delta.content or "", end="", flush=True)
