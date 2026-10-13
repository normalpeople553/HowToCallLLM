import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
response = client.chat.completions.create(model="qwen-flash", messages=[{"role": "user", "content": '只返回 json：{"ok":true}'}], response_format={"type": "json_object"}, extra_body={"enable_thinking": False})
print(json.loads(response.choices[0].message.content))
