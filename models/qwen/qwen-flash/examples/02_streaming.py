import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
stream = client.chat.completions.create(model="qwen-flash", messages=[{"role": "user", "content": "解释上下文窗口"}], stream=True, extra_body={"enable_thinking": False})
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
