import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
tools = [{"type": "function", "function": {"name": "get_weather", "description": "查询城市天气", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
response = client.chat.completions.create(model="qwen-flash", messages=[{"role": "user", "content": "杭州天气如何？"}], tools=tools, extra_body={"enable_thinking": False})
print(response.choices[0].message.tool_calls)
