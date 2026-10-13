import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ZHIPU_API_KEY"], base_url="https://open.bigmodel.cn/api/paas/v4/")
stream = client.chat.completions.create(model="glm-4.7-flash", messages=[{"role": "user", "content": "解释上下文窗口"}], stream=True, extra_body={"thinking": {"type": "disabled"}})
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
