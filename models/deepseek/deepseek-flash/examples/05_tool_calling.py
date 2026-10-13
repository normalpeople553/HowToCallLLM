"""DeepSeek 非思考模式 Tool Calling 完整闭环。

官方来源：https://api-docs.deepseek.com/guides/tool_calls/
模型只提出工具调用；应用必须验证参数并负责实际执行。
"""

import json
import os

from openai import OpenAI


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=60,
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]


def get_weather(city: str) -> str:
    if not isinstance(city, str) or not city.strip() or len(city) > 80:
        raise ValueError("city 参数无效")
    return json.dumps({"city": city, "weather": "晴（示例数据）"}, ensure_ascii=False)


messages = [{"role": "user", "content": "杭州天气怎么样？"}]
first = client.chat.completions.create(
    model="deepseek-flash",
    messages=messages,
    tools=tools,
    extra_body={"thinking": {"type": "disabled"}},
)

assistant_message = first.choices[0].message
messages.append(assistant_message)

for call in assistant_message.tool_calls or []:
    if call.function.name != "get_weather":
        raise ValueError(f"拒绝未注册工具：{call.function.name}")
    arguments = json.loads(call.function.arguments)
    result = get_weather(arguments.get("city"))
    messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

final = client.chat.completions.create(
    model="deepseek-flash",
    messages=messages,
    tools=tools,
    extra_body={"thinking": {"type": "disabled"}},
)
print(final.choices[0].message.content)
