import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
response = client.chat.completions.create(model="qwen-flash", messages=[{"role": "user", "content": "用一句话介绍你自己"}])
print(response.choices[0].message.content)
