"""DeepSeek JSON Output，并检查截断与解析错误。

官方来源：https://api-docs.deepseek.com/guides/json_mode/
"""

import json
import os

from openai import OpenAI


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=60,
)

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {
            "role": "system",
            "content": '只返回 json，格式示例：{"name":"张三","age":18}',
        },
        {"role": "user", "content": "人物：小明，26岁"},
    ],
    response_format={"type": "json_object"},
    max_tokens=512,
)

choice = response.choices[0]
if choice.finish_reason == "length":
    raise RuntimeError("输出被 max_tokens 或上下文上限截断")
if not choice.message.content:
    raise RuntimeError("JSON Output 返回空内容，请按官方建议调整提示词后重试")

data = json.loads(choice.message.content)
print(data)
