import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["ZHIPU_API_KEY"], base_url="https://open.bigmodel.cn/api/paas/v4/")
tools = [{"type": "function", "function": {"name": "get_weather", "description": "查询城市天气", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
response = client.chat.completions.create(model="glm-4.7-flash", messages=[{"role": "user", "content": "杭州天气如何？"}], tools=tools, extra_body={"thinking": {"type": "disabled"}})
print(response.choices[0].message.tool_calls)
