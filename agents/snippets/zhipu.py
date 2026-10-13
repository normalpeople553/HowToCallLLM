"""智谱 GLM 最短调用片段（实测 2026-10-13）。export ZHIPU_API_KEY=...
glm-4.7-flash 长期免费；默认开思考，不开思考时 max_tokens 别太小。"""
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ZHIPU_API_KEY"],
                base_url="https://open.bigmodel.cn/api/paas/v4")

# ① 默认（免费模型也带思考；max_tokens 给足，否则思考链吃光额度 content 为空）
r = client.chat.completions.create(
    model="glm-4.7-flash",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=512,
)
print(r.choices[0].message.content)

# ② 关闭思考（实测有效，推荐免费练手时关掉）
r = client.chat.completions.create(
    model="glm-4.7-flash",
    messages=[{"role": "user", "content": "你好"}],
    extra_body={"thinking": {"type": "disabled"}},
)

# ③ 流式
stream = client.chat.completions.create(
    model="glm-4.7-flash",
    messages=[{"role": "user", "content": "讲个冷笑话"}],
    stream=True,
    extra_body={"thinking": {"type": "disabled"}},
)
for c in stream:
    print(c.choices[0].delta.content or "", end="", flush=True)
