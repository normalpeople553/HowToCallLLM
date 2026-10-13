"""DeepSeek 工具调用完整闭环；天气工具返回固定模拟数据。

官方来源：
- https://api-docs.deepseek.com/guides/tool_calls/
- https://api-docs.deepseek.com/guides/thinking_mode/

调用最多 6 次模型，整批校验工具参数后才执行本地函数。
"""

import json
import os

from openai import OpenAI


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=120,
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "取得指定城市的教学用模拟天气，不提供实时天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    }
]


def get_weather(city: str) -> str:
    """固定模拟结果；接入真实天气 API 时替换此函数。"""
    return json.dumps(
        {"city": city, "weather": "晴", "simulated": True, "notice": "教学模拟数据，不是实时天气"},
        ensure_ascii=False,
    )


def validate_call(call, used_ids: set[str]) -> tuple[str, str]:
    if getattr(call, "type", None) != "function" or call.function.name != "get_weather":
        raise ValueError("拒绝未注册的工具")
    if not isinstance(call.id, str) or not call.id or call.id in used_ids:
        raise ValueError("工具调用 ID 为空或重复")
    arguments = json.loads(call.function.arguments)
    if not isinstance(arguments, dict) or set(arguments) != {"city"}:
        raise ValueError("工具参数必须是只包含 city 的 JSON 对象")
    city = arguments["city"]
    if (
        not isinstance(city, str)
        or not city.strip()
        or len(city) > 80
        or any(ord(char) < 32 for char in city)
    ):
        raise ValueError("city 必须是 1–80 字符的非空城市名，且不含控制字符")
    used_ids.add(call.id)
    return call.id, city.strip()


messages = [
    {"role": "system", "content": "天气查询必须使用 get_weather；明确告知用户结果是教学模拟数据。"},
    {"role": "user", "content": "杭州天气如何？"},
]
used_ids: set[str] = set()
executed_call_count = 0
max_model_turns = 6
for turn in range(max_model_turns):
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=messages,
        tools=tools,
        extra_body={"thinking": {"type": "disabled"}},
    )
    if not response.choices:
        raise RuntimeError("模型响应没有 choices")
    choice = response.choices[0]
    message = choice.message
    calls = message.tool_calls or []
    if calls:
        if choice.finish_reason != "tool_calls":
            raise RuntimeError(f"工具调用未完整结束：{choice.finish_reason!r}，未执行任何工具")
        if turn == max_model_turns - 1:
            raise RuntimeError("已达到模型调用次数上限，停止执行后续工具")
        # 校验全部调用；任何一个失败，本批次都不执行。
        planned = [validate_call(call, used_ids) for call in calls]
        # 保留完整 assistant 消息，包含 tool_calls 及可能的 reasoning_content 扩展字段。
        messages.append(message)
        for call_id, city in planned:
            result = get_weather(city)
            executed_call_count += 1
            messages.append(
                {"role": "tool", "tool_call_id": call_id, "content": result}
            )
        continue
    if choice.finish_reason != "stop":
        raise RuntimeError(f"最终回答未正常完成：{choice.finish_reason!r}")
    if not isinstance(message.content, str) or not message.content.strip():
        raise RuntimeError("工具闭环没有最终正文")
    if executed_call_count == 0:
        raise RuntimeError("模型没有调用示例工具，未完成工具闭环")
    print(message.content)
    break
else:
    raise RuntimeError("已达到模型调用次数上限")
