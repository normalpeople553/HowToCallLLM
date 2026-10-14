"""MiniMax-M2.7 工具闭环：保留完整思考和消息，返回固定模拟天气。

官方来源：
https://platform.minimax.cn/docs/api-reference/text-openai-api
https://platform.minimax.cn/docs/api-reference/text-chat-openai
本例工具不访问天气网络服务；先验证整批调用，再执行模拟函数。
本型号已公告服务调整计划，调用前请核对 sources.json 中的官方生命周期来源。
"""

import json
import os

from openai import OpenAI


def check_business_status(response) -> None:
    """HTTP 200 不等于业务成功；只使用状态码，不输出原始错误内容。"""
    base = getattr(response, "base_resp", None)
    if base is None:
        return
    code = base.get("status_code") if isinstance(base, dict) else getattr(base, "status_code", None)
    if isinstance(code, bool) or not isinstance(code, int) or code != 0:
        raise RuntimeError("MiniMax 返回非零或缺失的业务状态码")


def final_text(content) -> str:
    if not isinstance(content, str):
        raise RuntimeError("没有最终正文")
    text = content.strip()
    # 兼容内联 <think> 形式；仅处理展示文本，历史消息必须原样保留。
    while text.startswith("<think>"):
        _, closing, text = text.partition("</think>")
        if not closing:
            raise RuntimeError("内联思考没有完整结束，不能当作最终答案")
        text = text.strip()
    if not text:
        raise RuntimeError("只有思考或空内容，没有最终正文")
    return text


def completed_text(response) -> str:
    check_business_status(response)
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"回答未完整完成：{choice.finish_reason!r}；请检查思考与正文预算")
    if getattr(choice.message, "tool_calls", None):
        raise RuntimeError("收到未处理的工具调用")
    return final_text(choice.message.content)

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "取得城市的教学用固定模拟天气，不提供实时天气",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}]


def get_weather(city: str) -> str:
    return json.dumps(
        {"city": city, "weather": "晴", "simulated": True, "notice": "教学模拟数据，不是实时天气"},
        ensure_ascii=False,
    )


def validate_call(call, used_ids: set[str]) -> tuple[str, str]:
    if getattr(call, "type", None) != "function" or call.function.name != "get_weather":
        raise ValueError("拒绝未注册的工具")
    if not isinstance(call.id, str) or not call.id or call.id in used_ids:
        raise ValueError("工具调用 ID 为空或重复")
    args = json.loads(call.function.arguments)
    if not isinstance(args, dict) or set(args) != {"city"}:
        raise ValueError("参数必须是仅包含 city 的 JSON 对象")
    city = args["city"]
    if not isinstance(city, str) or not city.strip() or len(city) > 80 or any(ord(c) < 32 for c in city):
        raise ValueError("city 必须为 1–80 字符的非空城市名，不能含控制字符")
    used_ids.add(call.id)
    return call.id, city.strip()


def run_agent(client, max_model_turns: int = 6) -> str:
    if isinstance(max_model_turns, bool) or not isinstance(max_model_turns, int) or not 2 <= max_model_turns <= 6:
        raise ValueError("本例模型调用次数必须在 2–6 之间")
    messages = [
        {"role": "system", "content": "查天气必须使用 get_weather，并告知用户结果是教学模拟数据。"},
        {"role": "user", "content": "杭州天气如何？"},
    ]
    used_ids: set[str] = set()
    executed = 0
    for turn in range(max_model_turns):
        response = client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=messages,
            tools=TOOLS,
            extra_body={"reasoning_split": True},
            max_completion_tokens=16384,
        )
        check_business_status(response)
        if not response.choices:
            raise RuntimeError("响应没有 choices")
        choice = response.choices[0]
        message = choice.message
        calls = message.tool_calls or []
        if not calls:
            answer = completed_text(response)
            if not executed:
                raise RuntimeError("模型未执行工具，未完成工具闭环")
            return answer
        if choice.finish_reason != "tool_calls":
            raise RuntimeError("工具调用未完整结束，未执行工具")
        if turn == max_model_turns - 1:
            raise RuntimeError("达到模型调用次数上限，停止执行后续工具")
        batch_ids = set(used_ids)
        planned = [validate_call(call, batch_ids) for call in calls]
        used_ids = batch_ids
        # 原始 content 中的 <think> 和扩展 reasoning_content 都必须保留，不能只传展示正文。
        messages.append(message)
        for call_id, city in planned:
            result = get_weather(city)
            executed += 1
            messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
    raise RuntimeError("达到模型调用次数上限")


def main() -> None:
    client = OpenAI(
        api_key=os.environ["MINIMAX_API_KEY"],
        base_url="https://api.minimax.cn/v1",
        timeout=120,
    )
    print(run_agent(client))


if __name__ == "__main__":
    main()
