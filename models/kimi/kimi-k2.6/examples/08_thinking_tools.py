"""Kimi 思考模式工具闭环：保留完整 reasoning_content，查询模拟订单。

官方来源：
- https://platform.kimi.com/docs/guide/use-thinking-models
- https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart
本例使用非流式请求，便于展示每轮完整 assistant 消息原样回传。
订单结果是固定模拟数据，不查询真实订单；来源与验证范围见 sources.json。
"""

import json
import os
import re

from openai import OpenAI


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "查询 DEMO- 开头的教学模拟订单，返回固定模拟状态，不访问真实订单系统",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    }
]


def get_order_status(order_id: str) -> str:
    return json.dumps(
        {"order_id": order_id, "status": "待发货", "simulated": True, "notice": "教学模拟数据"},
        ensure_ascii=False,
    )


def validate_call(call, used_ids: set[str]) -> tuple[str, str]:
    if getattr(call, "type", None) != "function" or call.function.name != "get_order_status":
        raise ValueError("拒绝未注册工具")
    if not isinstance(call.id, str) or not call.id or call.id in used_ids:
        raise ValueError("工具调用 ID 为空或重复")
    arguments = json.loads(call.function.arguments)
    if not isinstance(arguments, dict) or set(arguments) != {"order_id"}:
        raise ValueError("工具参数必须是仅包含 order_id 的 JSON 对象")
    order_id = arguments["order_id"]
    if not isinstance(order_id, str) or re.fullmatch(r"DEMO-[0-9]{4}", order_id) is None:
        raise ValueError("本例只接受 DEMO- 加 4 位数字的模拟订单号")
    used_ids.add(call.id)
    return call.id, order_id


def run_agent(client, question: str, max_model_turns: int = 6) -> str:
    if isinstance(max_model_turns, bool) or not isinstance(max_model_turns, int) or max_model_turns < 2:
        raise ValueError("工具闭环至少需要预留 2 次模型调用")
    messages = [
        {"role": "system", "content": "订单状态必须调用 get_order_status；明确告知用户结果是教学模拟数据。"},
        {"role": "user", "content": question},
    ]
    used_ids: set[str] = set()
    executed_call_count = 0
    for turn in range(max_model_turns):
        response = client.chat.completions.create(
            model="kimi-k2.6",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            # K2.6 支持开启保留式思考；不传其他型号才支持的 reasoning_effort。
            extra_body={"thinking": {"type": "enabled", "keep": "all"}},
            max_tokens=32768,  # 官方多步工具建议 >=16000；思考与正文共享预算。
        )
        if not response.choices:
            raise RuntimeError("响应没有 choices")
        choice = response.choices[0]
        message = choice.message
        calls = message.tool_calls or []
        if calls:
            if choice.finish_reason != "tool_calls":
                raise RuntimeError(f"工具调用未完整结束：{choice.finish_reason!r}，未执行工具")
            if turn == max_model_turns - 1:
                raise RuntimeError("已达到模型调用上限，停止执行后续工具")
            batch_ids = set(used_ids)
            planned = [validate_call(call, batch_ids) for call in calls]
            used_ids = batch_ids
            # 原样保留完整 SDK 对象，不能仅重建 role/content/tool_calls 而丢掉思考字段。
            messages.append(message)
            for call_id, order_id in planned:
                result = get_order_status(order_id)
                executed_call_count += 1
                messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
            continue
        if choice.finish_reason != "stop":
            raise RuntimeError(f"最终回答未完整结束：{choice.finish_reason!r}")
        if not isinstance(message.content, str) or not message.content.strip():
            raise RuntimeError("没有最终正文")
        if executed_call_count == 0:
            raise RuntimeError("模型没有调用工具，未完成工具闭环")
        return message.content
    raise RuntimeError("已达到模型调用上限")


def main() -> None:
    client = OpenAI(
        api_key=os.environ["MOONSHOT_API_KEY"],
        base_url="https://api.moonshot.cn/v1",
        timeout=120,
    )
    print(run_agent(client, "帮我查询模拟订单 DEMO-1001 的发货状态，并告诉我是否是真实数据。"))


if __name__ == "__main__":
    main()
