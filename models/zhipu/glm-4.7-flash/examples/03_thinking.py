import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ZHIPU_API_KEY"], base_url="https://open.bigmodel.cn/api/paas/v4/")
response = client.chat.completions.create(model="glm-4.7-flash", messages=[{"role": "user", "content": "比较 9.11 和 9.8"}], extra_body={"thinking": {"type": "enabled"}})
print(response.choices[0].message.content)
