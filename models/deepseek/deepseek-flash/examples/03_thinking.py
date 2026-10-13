"""DeepSeek 思考开关与强度控制。

官方来源：https://api-docs.deepseek.com/guides/thinking_mode/
"""

import os

from openai import OpenAI


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=120,
)

question = "9.11 和 9.8 哪个更大？只给结论和一句解释。"

without_thinking = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": question}],
    extra_body={"thinking": {"type": "disabled"}},
)
print("关闭思考：", without_thinking.choices[0].message.content)

with_thinking = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": question}],
    reasoning_effort="high",
    extra_body={"thinking": {"type": "enabled"}},
)
message = with_thinking.choices[0].message
print("思考内容：", getattr(message, "reasoning_content", None))
print("最终回答：", message.content)
