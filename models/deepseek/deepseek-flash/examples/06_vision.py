"""通过公开图片 URL 调用 deepseek-flash 视觉能力。

官方来源：https://api-docs.deepseek.com/guides/vision/
"""

import os

from openai import OpenAI


image_url = os.environ["IMAGE_URL"]
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=120,
)

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请客观描述这张图片。"},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url, "detail": "low"},
                },
            ],
        }
    ],
)
print(response.choices[0].message.content)
