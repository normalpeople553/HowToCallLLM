"""豆包（火山方舟）最短调用片段（实测 2026-10-13）。export ARK_API_KEY=...
前提：模型已在控制台『开通管理』开通，否则 404。"""
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ARK_API_KEY"],
                base_url="https://ark.cn-beijing.volces.com/api/v3")

# ① 默认（seed-2-1-pro 默认开思考）
r = client.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=512,
)
print(r.choices[0].message.content)

# ② 关闭思考
r = client.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "你好"}],
    extra_body={"thinking": {"type": "disabled"}},
)

# ③ 流式
stream = client.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "讲个冷笑话"}],
    stream=True,
    extra_body={"thinking": {"type": "disabled"}},
)
for c in stream:
    print(c.choices[0].delta.content or "", end="", flush=True)
