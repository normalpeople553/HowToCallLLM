import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ARK_API_KEY"], base_url="https://ark.cn-beijing.volces.com/api/v3")
stream = client.chat.completions.create(model="doubao-seed-2-1-pro-260628", messages=[{"role": "user", "content": "解释上下文窗口"}], stream=True, extra_body={"thinking": {"type": "disabled"}})
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
