import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
response = client.chat.completions.create(model="qwen-flash", messages=[{"role": "user", "content": "比较 9.11 和 9.8"}], extra_body={"enable_thinking": True})
print(response.choices[0].message.content)
