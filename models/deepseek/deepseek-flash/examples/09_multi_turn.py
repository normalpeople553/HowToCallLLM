"""多轮对话：应用显式保留历史；失败的回答不写入历史。

改写自 https://api-docs.deepseek.com/guides/multi_round_chat/
项目补充：环境变量、关闭思考、结束与空正文检查。
"""

from _support import completed_text, make_client


def ask(client, history, question):
    pending = history + [{"role": "user", "content": question}]
    response = client.chat.completions.create(
        model="deepseek-flash", messages=pending,
        extra_body={"thinking": {"type": "disabled"}},
    )
    text = completed_text(response)
    history.extend([pending[-1], {"role": "assistant", "content": text}])
    return text


def main():
    client = make_client()
    history = [{"role": "system", "content": "请简洁回答。"}]
    print(ask(client, history, "我叫小明。"))
    print(ask(client, history, "我叫什么名字？"))


if __name__ == "__main__":
    main()
