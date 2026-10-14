"""思考 + 工具完整闭环：保留 reasoning_content 与 encrypted_content。

官方来源：
- https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh
  章节“回传思考内容加密原文”明确包含本型号：保留服务端完整消息，
  不裁剪或修改 encrypted_content，也不把思考摘要字数当作实际思考 token。
- https://docs.volcengine.com/docs/ark/function-calling?lang=zh
改编：最多 6 次模型调用；天气来自本地教学 fixture，没有外部天气副作用。
"""

import json
import os

from openai import OpenAI


MODEL = "doubao-seed-2-1-pro-260628"
MAX_MODEL_TURNS = 6
TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "教学用模拟天气查询，返回固定数据，不代表实时天气",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}]


def get_weather(city):
    return json.dumps({"city": city, "weather": "晴", "temperature_c": 23, "simulated": True}, ensure_ascii=False)


def validate_call(call, used_ids):
    if getattr(call, "type", None) != "function" or call.function.name != "get_weather":
        raise ValueError("拒绝未注册的工具")
    if not isinstance(call.id, str) or not call.id or call.id in used_ids:
        raise ValueError("工具调用 ID 为空或重复")
    arguments = json.loads(call.function.arguments)
    if not isinstance(arguments, dict) or set(arguments) != {"city"}:
        raise ValueError("参数必须是只包含 city 的 JSON 对象")
    city = arguments["city"]
    if not isinstance(city, str) or not city.strip() or len(city) > 80 or any(ord(char) < 32 for char in city):
        raise ValueError("city 必须是 1–80 字符的城市名，且不含控制字符")
    used_ids.add(call.id)
    return call.id, city.strip()


def main():
    client = OpenAI(
        api_key=os.environ["ARK_API_KEY"],
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        timeout=120,
    )
    messages = [
        {"role": "system", "content": "查询天气必须调用 get_weather。最终说明结果来自教学模拟数据。"},
        {"role": "user", "content": "查看杭州和北京的模拟天气，用两句话回答。"},
    ]
    used_ids = set()
    executed_call_count = 0
    for turn in range(MAX_MODEL_TURNS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            extra_body={"thinking": {"type": "enabled"}},
        )
        if not response.choices:
            raise RuntimeError("响应没有 choices")
        choice = response.choices[0]
        message = choice.message
        calls = getattr(message, "tool_calls", None) or []
        if calls:
            if choice.finish_reason != "tool_calls":
                raise RuntimeError("工具参数未正常完成，本批工具均不执行")
            if turn == MAX_MODEL_TURNS - 1:
                raise RuntimeError("达到模型调用上限，后续工具不执行")
            # 先整批校验，再执行；函数名称允许列表只包含 get_weather。
            planned = [validate_call(call, used_ids) for call in calls]
            # OpenAI SDK 会保留响应扩展字段。完整消息原样回传：
            # message.reasoning_content 是可能返回的摘要，
            # message.encrypted_content 是模型返回的加密原文，绝不重建或裁剪。
            messages.append(message)
            for call_id, city in planned:
                messages.append({"role": "tool", "tool_call_id": call_id, "content": get_weather(city)})
                executed_call_count += 1
            continue
        if choice.finish_reason != "stop":
            raise RuntimeError(f"最终回答未正常完成：{choice.finish_reason!r}")
        if not isinstance(message.content, str) or not message.content.strip():
            raise RuntimeError("工具闭环没有最终正文")
        if executed_call_count == 0:
            raise RuntimeError("模型未调用工具，未完成工具闭环")
        print(message.content)
        # 不打印 encrypted_content；实际思考 token 从服务端 usage 读取。
        details = getattr(getattr(response, "usage", None), "completion_tokens_details", None)
        print("末轮 reasoning_tokens：", getattr(details, "reasoning_tokens", None))
        return executed_call_count
    raise RuntimeError("达到模型调用上限")


if __name__ == "__main__":
    executed_call_count = main()
