"""从型号机器卡读取配置，用同一入口调用五家默认型号。

配置与官方来源见 skills/model-manual/references/models/*.json。
本文件需要保留在仓库 examples/ 中；单独复制时请一并携带机器卡目录。
运行前给需要调用的厂商配置环境变量，安装 openai 后执行本文件。
"""

import copy
import json
import os
from pathlib import Path

from openai import OpenAI


ROOT = Path(__file__).resolve().parent.parent
REFERENCES = ROOT / "skills" / "model-manual" / "references"
VENDORS = json.loads((REFERENCES / "vendors.json").read_text(encoding="utf-8"))["vendors"]


def completed_text(response) -> str:
    """应用检查：只有正常结束且非空的正文才能当作完整结果。"""
    if not response.choices:
        raise RuntimeError("响应没有 choices")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        raise RuntimeError(
            f"回答未正常完成：finish_reason={choice.finish_reason!r}；"
            "length 表示达到生成或上下文限制，请检查思考与回答预算"
        )
    content = choice.message.content
    if getattr(choice.message, "tool_calls", None):
        raise RuntimeError("收到未处理的工具调用")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("模型没有返回最终正文；请检查思考预算和提示词")
    return content

def model_card(vendor: str) -> dict:
    """只调用仓库中有独立机器卡的型号。"""
    model = VENDORS[vendor]["default_model"]
    path = REFERENCES / "models" / f"{model}.json"
    card = json.loads(path.read_text(encoding="utf-8"))
    if card["vendor"] != vendor or card["model_id"] != model:
        raise ValueError("厂商目录与型号机器卡不一致")
    return card


def chat(vendor: str, question: str) -> str:
    card = model_card(vendor)
    generation = card["generation"]
    client = OpenAI(
        api_key=os.environ[generation["key_env"]["value"]],
        base_url=generation["base_url"]["value"],
        timeout=120,
    )
    params = {
        "model": card["identity"]["api_model_id"]["value"],
        "messages": [{"role": "user", "content": question}],
    }
    # 开关值与 Python 扩展字段位置均来自该型号的卡片，避免套用厂商级默认参数。
    thinking_off = copy.deepcopy(generation["thinking"]["off"]["value"])
    extra_fields = set(generation["python_extra_body_fields"]["value"])
    extra_body = {key: value for key, value in thinking_off.items() if key in extra_fields}
    params.update({key: value for key, value in thinking_off.items() if key not in extra_fields})
    if extra_body:
        params["extra_body"] = extra_body
    response = client.chat.completions.create(**params)
    return completed_text(response)


if __name__ == "__main__":
    for vendor in VENDORS:
        key_env = model_card(vendor)["generation"]["key_env"]["value"]
        if not os.environ.get(key_env):
            print(f"[{vendor}] 未配置 {key_env}，跳过")
            continue
        try:
            print(f"[{vendor}] {chat(vendor, '用一句话介绍你自己')}\n")
        except Exception as exc:
            # 仅显示错误类型和状态，避免原始请求/响应或异常文本泄露密钥。
            status = getattr(exc, "status_code", None)
            status = status if isinstance(status, int) else "未知"
            print(f"[{vendor}] 调用失败：{type(exc).__name__}，HTTP 状态 {status}")
