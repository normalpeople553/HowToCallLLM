"""MiniMax-M2.7 流式正文：用量空块、完成状态和思考字段分开处理。

官方来源：
https://platform.minimax.cn/docs/api-reference/text-openai-api
https://platform.minimax.cn/docs/api-reference/text-chat-openai
本型号已公告服务调整计划，调用前请核对 sources.json 中的官方生命周期来源。
"""

import os
import sys

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

def consume_stream(stream) -> tuple[str, str, object]:
    answer_parts, reasoning_parts = [], []
    finish_reason = None
    usage = None
    try:
        for chunk in stream:
            check_business_status(chunk)
            usage = getattr(chunk, "usage", None) or usage
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = getattr(choice, "delta", None)
            content = getattr(delta, "content", None)
            reasoning = getattr(delta, "reasoning_content", None)
            if getattr(delta, "tool_calls", None):
                raise RuntimeError("本例未注册工具，却收到工具调用")
            if finish_reason is not None:
                if content or reasoning or choice.finish_reason is not None:
                    raise RuntimeError("已经结束的流又返回正文、思考或结束状态")
                continue
            if content:
                answer_parts.append(content)
                print(content, end="", flush=True)
            if reasoning:
                reasoning_parts.append(reasoning)
            if choice.finish_reason is not None:
                finish_reason = choice.finish_reason
    except Exception:
        print("\n[流式传输失败，已显示的文本可能不完整]", file=sys.stderr)
        raise
    if finish_reason != "stop":
        raise RuntimeError(f"流未正常结束：{finish_reason!r}，缺少结束状态或已经截断")
    answer = final_text("".join(answer_parts))
    return answer, "".join(reasoning_parts), usage


def main() -> None:
    client = OpenAI(
        api_key=os.environ["MINIMAX_API_KEY"],
        base_url="https://api.minimax.cn/v1",
        timeout=120,
    )
    stream = client.chat.completions.create(
        model="MiniMax-M2.7",
        messages=[{"role": "user", "content": "用三句话解释上下文窗口。"}],
        stream=True,
        stream_options={"include_usage": True},
        extra_body={"reasoning_split": True},
        max_completion_tokens=16384,
    )
    _, _, usage = consume_stream(stream)
    print()
    if usage is not None:
        print("本次用量：", usage)


if __name__ == "__main__":
    main()
