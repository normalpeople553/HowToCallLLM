"""MiniMax-M2.7 的思考不可关闭；reasoning_split 是输出格式开关。

官方来源：https://platform.minimax.cn/docs/api-reference/text-chat-openai
https://platform.minimax.cn/docs/api-reference/text-openai-api
不传其他型号专用的 reasoning_effort，也不把 thinking disabled 当作关闭成功。
本型号已公告服务调整计划，调用前请核对 sources.json 中的官方生命周期来源。
"""

import os

from openai import OpenAI


def check_business_status(response) -> None:
    """HTTP 200 不等于业务成功；只使用状态码，不输出原始错误内容。"""
    base = getattr(response, "base_resp", None)
    if base is None:
        return
    code = base.get("status_code") if isinstance(base, dict) else getattr(base, "status_code", None)
    if isinstance(code, bool) or not isinstance(code, int) or code != 0:
        raise RuntimeError("MiniMax 返回非零或缺失的业务状态码")


def final_text(content) -> str:
    if not isinstance(content, str):
        raise RuntimeError("没有最终正文")
    text = content.strip()
    # 兼容内联 <think> 形式；仅处理展示文本，历史消息必须原样保留。
    while text.startswith("<think>"):
        _, closing, text = text.partition("</think>")
        if not closing:
            raise RuntimeError("内联思考没有完整结束，不能当作最终答案")
        text = text.strip()
    if not text:
        raise RuntimeError("只有思考或空内容，没有最终正文")
    return text


def completed_text(response) -> str:
    check_business_status(response)
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"回答未完整完成：{choice.finish_reason!r}；请检查思考与正文预算")
    if getattr(choice.message, "tool_calls", None):
        raise RuntimeError("收到未处理的工具调用")
    return final_text(choice.message.content)

def main() -> None:
    client = OpenAI(
        api_key=os.environ["MINIMAX_API_KEY"],
        base_url="https://api.minimax.cn/v1",
        timeout=120,
    )
    response = client.chat.completions.create(
        model="MiniMax-M2.7",
        messages=[{"role": "user", "content": "9.11 和 9.8 哪个更大？给结论和一句解释。"}],
        extra_body={"reasoning_split": True},
        max_completion_tokens=16384,
    )
    answer = completed_text(response)
    reasoning = getattr(response.choices[0].message, "reasoning_content", None)
    print("思考字段：", reasoning if isinstance(reasoning, str) and reasoning else "本次响应未返回拆分的思考文本")
    print("最终回答：", answer)
    print("本次用量：", response.usage)


if __name__ == "__main__":
    main()
