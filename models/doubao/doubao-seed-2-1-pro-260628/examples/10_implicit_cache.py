"""观察隐式缓存：固定长前缀，连续请求两次，读取服务端 cached_tokens。

官方来源：
- https://docs.volcengine.com/docs/ark/context-cache?lang=zh
  “隐式缓存→提升缓存命中率、工作原理”：无需开关；命中由服务端决定。
- https://docs.volcengine.com/docs/ark/model-list?lang=zh
  “上下文缓存能力→往期模型”：本型号支持 Chat API 隐式缓存。
缓存命中为 0 也是正常观测结果，本例不会把两次请求相同视作命中保证。
"""

import os

from openai import OpenAI


def completed_text(response):
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"回答未正常完成：{choice.finish_reason!r}")
    message = choice.message
    if getattr(message, "tool_calls", None):
        raise RuntimeError("缓存示例没有工具执行器")
    if not isinstance(message.content, str) or not message.content.strip():
        raise RuntimeError("模型没有返回最终正文")
    return message.content


def main():
    client = OpenAI(
        api_key=os.environ["ARK_API_KEY"],
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        timeout=120,
    )
    # 教学资料由本例生成，非用户数据；不通过字符数猜测实际 token 数。
    background = "\n".join(
        f"条目 {index:03d}：读书笔记包含书名、作者、页码、原文摘录与读者自己的理解，导出时保留出处。"
        for index in range(80)
    )
    messages = [
        {"role": "system", "content": "按给定资料回答，保持简短。\n" + background},
        {"role": "user", "content": "用一句话概括这些笔记条目的共同原则。"},
    ]
    for index in range(2):
        response = client.chat.completions.create(
            model="doubao-seed-2-1-pro-260628",
            messages=messages,
            extra_body={"thinking": {"type": "disabled"}},
        )
        print(completed_text(response))
        usage = getattr(response, "usage", None)
        details = getattr(usage, "prompt_tokens_details", None)
        cached_tokens = getattr(details, "cached_tokens", None)
        if cached_tokens is None:
            print(f"第 {index + 1} 次：服务端没有返回 cached_tokens，无法判断是否命中。")
        elif cached_tokens == 0:
            print(f"第 {index + 1} 次：cached_tokens=0，本次未命中缓存。")
        else:
            print(f"第 {index + 1} 次：cached_tokens={cached_tokens}，本次命中缓存。")
        print("本次输入 tokens：", getattr(usage, "prompt_tokens", None))


if __name__ == "__main__":
    main()
