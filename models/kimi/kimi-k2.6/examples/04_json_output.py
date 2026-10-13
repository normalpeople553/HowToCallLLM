import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["MOONSHOT_API_KEY"], base_url="https://api.moonshot.cn/v1")
response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": '只返回 json：{"name":"小明","age":26}'}],
    response_format={"type": "json_object"},
    extra_body={"thinking": {"type": "disabled"}},
)
print(json.loads(response.choices[0].message.content))
