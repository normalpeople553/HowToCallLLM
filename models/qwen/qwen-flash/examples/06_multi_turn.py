"""qwen-flash 非思考多轮对话：由客户端回传历史正文。

官方来源：
- https://help.aliyun.com/zh/model-studio/multi-round-conversation
- https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions

基于官方 messages 示例改编。两次请求由同一份客户端历史串联；
本例关闭思考，不迁移新版型号的 preserve_thinking 参数。
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
        api_key=os.environ["DASHSCOPE_API_KEY"],
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=120,
        max_retries=0,
    )
    messages = [{"role": "system", "content": "回答简洁，只根据本次传入的对话回答。"}]
    questions = ["我报名了周六上午的 Python 入门课，请记住这个信息。", "我报名的是什么课、什么时候上课？"]
    for question in questions:
        messages.append({"role": "user", "content": question})
        response = client.chat.completions.create(
            model="qwen-flash", messages=messages,
            extra_body={"enable_thinking": False}, max_tokens=1024,
        )
        message = completed_message(response)
        # 官方非保留式多轮示例回传正文；不把 reasoning_content 拼入正文。
        messages.append({"role": "assistant", "content": message.content})
        print(message.content)
    return messages


if __name__ == "__main__":
    main()
