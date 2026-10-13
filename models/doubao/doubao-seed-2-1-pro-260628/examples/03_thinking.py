import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ARK_API_KEY"], base_url="https://ark.cn-beijing.volces.com/api/v3")
response = client.chat.completions.create(model="doubao-seed-2-1-pro-260628", messages=[{"role": "user", "content": "比较 9.11 和 9.8"}], extra_body={"thinking": {"type": "enabled"}})
print(response.choices[0].message.content)
