"""Beta FIM 中间补全；/completions 不是 /chat/completions。

改写自：https://api-docs.deepseek.com/guides/fim_completion/
项目补充：环境变量、结束/空文本检查；只打印、不执行模型生成的代码。
"""

from _support import make_client


def main():
    prefix = "def celsius_to_fahrenheit(celsius):\n"
    suffix = "\n    return fahrenheit\n"
    response = make_client(beta=True).completions.create(
        model="deepseek-flash", prompt=prefix, suffix=suffix, max_tokens=128,
    )
    if not response.choices:
        raise RuntimeError("FIM 响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop" or not isinstance(choice.text, str) or not choice.text.strip():
        raise RuntimeError(f"FIM 补全不完整或为空：{choice.finish_reason!r}")
    print(prefix + choice.text + suffix)


if __name__ == "__main__":
    main()
