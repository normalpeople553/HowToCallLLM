"""Beta 对话前缀续写；仅打印文本，不执行生成的代码。

改写自：https://api-docs.deepseek.com/guides/chat_prefix_completion/
项目补充：环境变量、关闭思考、结束检查；保留前缀后打印完整代码块。
"""

from _support import completed_text, make_client


def main():
    prefix = "```python\n"
    response = make_client(beta=True).chat.completions.create(
        model="deepseek-flash",
        messages=[
            {"role": "user", "content": "编写一个把摄氏温度转换为华氏温度的纯函数。"},
            {"role": "assistant", "content": prefix, "prefix": True},
        ],
        stop=["```"],
        max_tokens=1024,
        extra_body={"thinking": {"type": "disabled"}},
    )
    print(prefix + completed_text(response) + "\n```")


if __name__ == "__main__":
    main()
