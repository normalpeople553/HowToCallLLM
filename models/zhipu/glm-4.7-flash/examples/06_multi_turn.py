"""glm-4.7-flash 非思考多轮对话：每轮携带完整的客户端历史。

官方来源：
- https://docs.bigmodel.cn/cn/guide/models/free/glm-4.7-flash
- https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
- https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8

使用仓库约定的 ZHIPU_API_KEY；官方 OpenAI 兼容示例也使用 ZAI_API_KEY。
本例是两轮固定对话，不依赖服务端保存上一轮历史。
"""

import json
import os
import sys

from openai import OpenAI


def completed_message(response):
    usage = getattr(response, "usage", None)
    usage = usage.model_dump(exclude_none=True) if hasattr(usage, "model_dump") else usage
    print("usage=" + json.dumps(usage, ensure_ascii=False, default=str), file=sys.stderr)
    choices = getattr(response, "choices", None) or []
    if not choices:
        raise RuntimeError("响应没有 choices，不能进入下一轮")
    choice = choices[0]
    message = choice.message
    if choice.finish_reason != "stop" or getattr(message, "tool_calls", None):
        raise RuntimeError(f"回答未完整结束：finish_reason={choice.finish_reason!r}")
    if not isinstance(message.content, str) or not message.content.strip():
        raise RuntimeError("回答没有最终正文，不能写入对话历史")
    return message


def main():
    client = OpenAI(
        api_key=os.environ["ZHIPU_API_KEY"],
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        timeout=120,
        max_retries=0,
    )
    messages = [{"role": "system", "content": "回答简洁，只根据本次传入的对话回答。"}]
    questions = ["我报名了周六上午的 Python 入门课，请记住这个信息。", "我报名的是什么课、什么时候上课？"]
    for question in questions:
        messages.append({"role": "user", "content": question})
        response = client.chat.completions.create(
            model="glm-4.7-flash", messages=messages,
            extra_body={"thinking": {"type": "disabled"}}, max_tokens=4096,
        )
        message = completed_message(response)
        messages.append(message.model_dump(exclude_none=True))
        print(message.content)
    return messages


if __name__ == "__main__":
    main()
