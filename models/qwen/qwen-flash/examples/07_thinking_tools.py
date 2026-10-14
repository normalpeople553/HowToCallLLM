"""qwen-flash 思考与工具闭环：查询固定模拟库存，再回答用户。

官方来源：
- https://help.aliyun.com/zh/model-studio/qwen-function-calling
- https://help.aliyun.com/zh/model-studio/deep-thinking
- https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions

基于官方 Function Calling 流程改编；工具只返回本地固定教学数据。
qwen-flash 的 max_tokens 限制正文。本例不传仅登记于新版型号的
max_completion_tokens / preserve_thinking；完整回传同一工具循环的 assistant。
四次模型调用、整批参数校验和库存数据均为项目示例约定。
"""

import json
import os
import sys

from openai import OpenAI


TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_inventory", "description": "查询教学用固定模拟库存，不连接真实库存系统",
        "parameters": {
            "type": "object", "properties": {"sku": {"type": "string"}},
            "required": ["sku"], "additionalProperties": False,
        },
    },
}]


def validate_call(call, seen_ids):
    if getattr(call, "type", None) != "function" or call.function.name != "get_inventory":
        raise ValueError("模型请求了未登记的工具")
    call_id = getattr(call, "id", None)
    if not isinstance(call_id, str) or not call_id or call_id in seen_ids:
        raise ValueError("工具调用 id 缺失或重复")
    arguments = json.loads(call.function.arguments)
    if not isinstance(arguments, dict) or set(arguments) != {"sku"}:
        raise ValueError("参数必须且只能包含 sku")
    if arguments["sku"] != "SKU-001":
        raise ValueError("本教学工具只接受 SKU-001")
    seen_ids.add(call_id)
    return call_id, arguments["sku"]


def get_inventory(sku):
    return json.dumps({"sku": sku, "available": 7, "simulated": True}, ensure_ascii=False)


def main():
    client = OpenAI(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=120, max_retries=0,
    )
    messages = [
        {"role": "system", "content": "查询库存必须使用 get_inventory，答案说明结果是教学模拟数据。"},
        {"role": "user", "content": "请查询 SKU-001 的模拟库存，再判断够不够满足 5 件的需求。"},
    ]
    seen_ids = set()
    executed = 0
    for turn in range(4):
        response = client.chat.completions.create(
            model="qwen-flash", messages=messages, tools=TOOLS, tool_choice="auto",
            extra_body={"enable_thinking": True}, max_tokens=8192,
        )
        usage = getattr(response, "usage", None)
        usage = usage.model_dump(exclude_none=True) if hasattr(usage, "model_dump") else usage
        print("usage=" + json.dumps(usage, ensure_ascii=False, default=str), file=sys.stderr)
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise RuntimeError("模型响应没有 choices")
        choice = choices[0]
        message = choice.message
        calls = getattr(message, "tool_calls", None) or []
        if calls:
            if choice.finish_reason != "tool_calls":
                raise RuntimeError(f"工具参数未完整结束：{choice.finish_reason!r}，未执行工具")
            if turn == 3:
                raise RuntimeError("已到模型调用上限，不执行无法回传的工具")
            batch_ids = set(seen_ids)
            planned = [validate_call(call, batch_ids) for call in calls]
            results = [(call_id, get_inventory(sku)) for call_id, sku in planned]
            seen_ids = batch_ids
            # 原样保留 tool_calls、reasoning_content 等字段，不拼接或改写思考。
            messages.append(message.model_dump(exclude_none=True))
            for call_id, result in results:
                messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
                executed += 1
            continue
        if choice.finish_reason != "stop":
            raise RuntimeError(f"最终回答未完整结束：{choice.finish_reason!r}")
        if not isinstance(message.content, str) or not message.content.strip():
            raise RuntimeError("最终回答没有正文；检查思考与回答预算")
        if executed == 0:
            raise RuntimeError("模型直接回答，未完成工具闭环示例")
        print(message.content)
        return messages
    raise RuntimeError("尚未得到最终答案，模型调用次数已达上限")


if __name__ == "__main__":
    main()
