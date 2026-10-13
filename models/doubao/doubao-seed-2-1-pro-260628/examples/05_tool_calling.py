import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ARK_API_KEY"], base_url="https://ark.cn-beijing.volces.com/api/v3")
tools = [{"type": "function", "function": {"name": "get_weather", "description": "查询城市天气", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
response = client.chat.completions.create(model="doubao-seed-2-1-pro-260628", messages=[{"role": "user", "content": "杭州天气如何？"}], tools=tools, extra_body={"thinking": {"type": "disabled"}})
print(response.choices[0].message.tool_calls)
