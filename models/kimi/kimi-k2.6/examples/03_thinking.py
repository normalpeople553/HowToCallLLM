import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["MOONSHOT_API_KEY"], base_url="https://api.moonshot.cn/v1")
response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "比较 9.11 和 9.8"}],
    extra_body={"thinking": {"type": "enabled"}},
)
print(response.choices[0].message.content)
