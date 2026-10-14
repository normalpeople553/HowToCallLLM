"""Responses API 图片输入；IMAGE_URL / IMAGE_PATH 二选一。

官方来源：https://api-docs.deepseek.com/guides/responses_api/
https://api-docs.deepseek.com/guides/vision/
https://api-docs.deepseek.com/guides/thinking_mode/
与 Chat Completions 的消息结构不同；此 API 不保存服务端会话历史。
项目补充：检查 completed 状态和正文；IMAGE_DETAIL 可选。
"""

from _support import image_detail, image_url_from_env, make_client


def main():
    url, detail = image_url_from_env(), image_detail()
    response = make_client().responses.create(
        model="deepseek-flash",
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": "请客观描述这张图片。"},
            {"type": "input_image", "image_url": url, "detail": detail},
        ]}],
        reasoning={"effort": "none"},
        max_output_tokens=2048,
    )
    if response.status != "completed":
        raise RuntimeError(f"Responses 未完整完成：{response.status!r}")
    if not isinstance(response.output_text, str) or not response.output_text.strip():
        raise RuntimeError("Responses 没有最终正文")
    print(response.output_text)


if __name__ == "__main__":
    main()
