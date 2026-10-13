import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["MOONSHOT_API_KEY"], base_url="https://api.moonshot.cn/v1")
stream = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "用三句话解释上下文窗口"}],
    stream=True,
    extra_body={"thinking": {"type": "disabled"}},
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
