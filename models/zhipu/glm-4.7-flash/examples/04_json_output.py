import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ZHIPU_API_KEY"], base_url="https://open.bigmodel.cn/api/paas/v4/")
response = client.chat.completions.create(model="glm-4.7-flash", messages=[{"role": "user", "content": '只返回 json：{"ok":true}'}], response_format={"type": "json_object"}, extra_body={"thinking": {"type": "disabled"}})
print(json.loads(response.choices[0].message.content))
