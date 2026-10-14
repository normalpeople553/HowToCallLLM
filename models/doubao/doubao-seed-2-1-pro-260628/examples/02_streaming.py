"""豆包 流式输出：处理空 choices，并检查流是否完整结束。

官方来源：https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh
"""

import os
import sys

from openai import OpenAI


def main():
    client = OpenAI(
        api_key=os.environ["ARK_API_KEY"],
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        timeout=120,
    )
    stream = client.chat.completions.create(
        model="doubao-seed-2-1-pro-260628",
        messages=[{"role": "user", "content": "用三句话解释上下文窗口"}],
        stream=True,
        extra_body={"thinking": {"type": "disabled"}},
    )
    answer_parts = []
    finish_reason = None
    usage = None
    try:
        for chunk in stream:
            usage = getattr(chunk, "usage", None) or usage
            if not chunk.choices:  # 统计用量的末块可能只有 usage。
                continue
            choice = chunk.choices[0]
            if getattr(choice.delta, "tool_calls", None):
                raise RuntimeError("收到本示例未处理的工具调用")
            if choice.delta.content:
                if finish_reason is not None:
                    raise RuntimeError("收到结束标记之后仍出现正文")
                answer_parts.append(choice.delta.content)
                print(choice.delta.content, end="", flush=True)
            if choice.finish_reason is not None:
                if finish_reason is not None and finish_reason != choice.finish_reason:
                    raise RuntimeError("流中出现互相矛盾的结束原因")
                finish_reason = choice.finish_reason
    except Exception:
        print("\n[流式传输失败，以上内容可能不完整]", file=sys.stderr)
        raise
    finally:
        close = getattr(stream, "close", None)
        if callable(close):
            close()
    print()
    if finish_reason != "stop":
        raise RuntimeError(
            f"流未正常完成：finish_reason={finish_reason!r}；"
            "length 表示截断，None 表示没有收到结束状态"
        )
    if not "".join(answer_parts).strip():
        raise RuntimeError("流已结束，但没有最终正文")
    if usage is not None:
        print("本次用量：", usage)
    return answer_parts, finish_reason, usage


if __name__ == "__main__":
    answer_parts, finish_reason, usage = main()
