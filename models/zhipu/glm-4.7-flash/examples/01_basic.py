import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ZHIPU_API_KEY"], base_url="https://open.bigmodel.cn/api/paas/v4/")
response = client.chat.completions.create(model="glm-4.7-flash", messages=[{"role": "user", "content": "用一句话介绍你自己"}])
print(response.choices[0].message.content)
