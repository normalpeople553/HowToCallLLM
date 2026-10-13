import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ARK_API_KEY"], base_url="https://ark.cn-beijing.volces.com/api/v3")
response = client.chat.completions.create(model="doubao-seed-2-1-pro-260628", messages=[{"role": "user", "content": "返回 ok 为 true"}], response_format={"type": "json_schema", "json_schema": {"name": "result", "strict": True, "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}}}, extra_body={"thinking": {"type": "disabled"}})
print(json.loads(response.choices[0].message.content))
