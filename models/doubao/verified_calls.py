"""已实际运行的豆包最小调用；只选择本文件列出的准确 Model ID。

安装：python -m pip install openai
运行：python models/doubao/verified_calls.py --model doubao-seed-2-1-pro-260915
凭据：环境变量 ARK_API_KEY。不得把密钥写进本文件。

官方来源：
https://docs.volcengine.com/docs/ark/model-list?lang=zh
https://docs.volcengine.com/docs/ark/chat-api?lang=zh
https://docs.volcengine.com/docs/ark/create-model-responses-api?lang=zh
https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh
"""

import argparse
import os

from openai import OpenAI


CHAT_MODELS = (
    "doubao-seed-evolving",
    "doubao-seed-2-1-pro-260915",
    "doubao-seed-2-1-lite-260915",
    "doubao-seed-2-1-turbo-260628",
    "doubao-seed-2-1-pro-260628",
    "doubao-seed-2-0-lite-260428",
    "doubao-seed-2-0-mini-260428",
    "doubao-seed-2-0-lite-260215",
    "doubao-seed-2-0-code-preview-260215",
    "doubao-seed-character-260628",
    "doubao-seed-character-251128",
)
TRANSLATION_MODEL = "doubao-seed-translation-250915"
NON_THINKING_MODELS = {"doubao-seed-character-251128"}


def complete_chat(client: OpenAI, model: str) -> str:
    request = {
        "model": model,
        "messages": [{"role": "user", "content": "请只回复：收到。"}],
    }
    if model not in NON_THINKING_MODELS:
        request["extra_body"] = {"thinking": {"type": "disabled"}}
    response = client.chat.completions.create(**request)
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(f"回答未正常结束：{choice.finish_reason!r}")
    if choice.message.tool_calls:
        raise RuntimeError("收到未处理的工具调用")
    content = choice.message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("模型未返回最终正文")
    return content


def complete_translation(client: OpenAI) -> str:
    # 翻译型号不支持 Chat Completions，也不接受 Responses 的裸字符串 input。
    response = client.responses.create(
        model=TRANSLATION_MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "你好",
                        "translation_options": {
                            "source_language": "zh",
                            "target_language": "en",
                        },
                    }
                ],
            }
        ],
    )
    if response.status != "completed" or not response.output_text.strip():
        raise RuntimeError(f"翻译未完整完成：{response.status!r}")
    return response.output_text


def main() -> None:
    parser = argparse.ArgumentParser(description="调用已验证的豆包准确型号")
    parser.add_argument("--model", choices=(*CHAT_MODELS, TRANSLATION_MODEL), required=True)
    args = parser.parse_args()
    client = OpenAI(
        api_key=os.environ["ARK_API_KEY"],
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        timeout=120,
        max_retries=0,
    )
    result = complete_translation(client) if args.model == TRANSLATION_MODEL else complete_chat(client, args.model)
    print(result)


if __name__ == "__main__":
    main()
