"""Kimi 简单 JSON Schema：结构化抽取，并做业务层二次校验。

官方提醒 K2.6 对复杂 schema 可能不稳定，本例不使用 $ref、oneOf 或 Partial Mode。
官方来源：https://platform.kimi.com/docs/guide/response_format
来源、改编内容和验证范围见同目录 sources.json。
"""

import json
import os

from openai import OpenAI


def completed_text(response) -> str:
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"回答未完整结束：{choice.finish_reason!r}，请检查输出和思考预算")
    if getattr(choice.message, "tool_calls", None):
        raise RuntimeError("收到未处理的工具调用")
    content = choice.message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("没有最终正文")
    return content

def validate_person(data) -> dict:
    if not isinstance(data, dict) or set(data) != {"name", "age"}:
        raise ValueError("期望只包含 name 和 age 的 JSON 对象")
    if not isinstance(data["name"], str) or not data["name"].strip() or len(data["name"]) > 80:
        raise ValueError("name 必须是 1–80 字符的非空字符串")
    # bool 在 Python 中是 int 的子类，因此这里单独排除。
    if isinstance(data["age"], bool) or not isinstance(data["age"], int) or not 0 <= data["age"] <= 150:
        raise ValueError("age 必须是 0–150 的整数")
    return data


def main() -> None:
    client = OpenAI(
        api_key=os.environ["MOONSHOT_API_KEY"],
        base_url="https://api.moonshot.cn/v1",
        timeout=120,
    )
    response = client.chat.completions.create(
        model="kimi-k2.6",
        messages=[
            {"role": "system", "content": "从给定文本抽取人物姓名和年龄，只基于原文回答。"},
            {"role": "user", "content": "小明今年26岁。"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "person",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                    "required": ["name", "age"],
                    "additionalProperties": False,
                },
            },
        },
        extra_body={"thinking": {"type": "disabled"}},
    )
    data = validate_person(json.loads(completed_text(response)))
    print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    main()
