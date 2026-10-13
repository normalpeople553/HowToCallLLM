import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ARK_API_KEY"], base_url="https://ark.cn-beijing.volces.com/api/v3")
response = client.chat.completions.create(model="doubao-seed-2-1-pro-260628", messages=[{"role": "user", "content": "用一句话介绍你自己"}])
print(response.choices[0].message.content)
