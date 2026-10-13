"""一套代码切换五家厂商。对应 book/02。

只需在 VENDORS 里登记每家的地址、模型和读取哪个环境变量，
想调哪家就把名字传给 chat()，其余代码完全不变。

运行前（用到哪家就配哪家的 key）：
    export DEEPSEEK_API_KEY=...  MOONSHOT_API_KEY=...
    export ZHIPU_API_KEY=...     DASHSCOPE_API_KEY=...  ARK_API_KEY=...
运行：
    python3 02_one_for_all.py
"""

import os

from openai import OpenAI

# 每家只在这张表里登记差异：环境变量名 / 地址 / 模型 / 可选参数
VENDORS = {
    "deepseek": {
        "key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
    },
    "kimi": {
        "key_env": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "kimi-k2.6",                       # 注意：老的 moonshot-v1-* 已不可用
        "extra": {"thinking": {"type": "disabled"}},  # 简单问题关思考更省
    },
    "zhipu": {
        "key_env": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4.7-flash",                    # 长期免费的 Flash 模型
        "extra": {"thinking": {"type": "disabled"}},  # 免费模型默认也思考，练手关掉
    },
    "qwen": {
        "key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-flash",
    },
    "doubao": {
        "key_env": "ARK_API_KEY",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-seed-2-1-pro-260628",       # 前提：控制台已开通该模型
        "extra": {"thinking": {"type": "disabled"}},
    },
}


def chat(vendor: str, question: str) -> str:
    cfg = VENDORS[vendor]                                      # 取出该家配置
    client = OpenAI(
        api_key=os.environ[cfg["key_env"]],                    # 同一份逻辑
        base_url=cfg["base_url"],
    )
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": question}],
        extra_body=cfg.get("extra"),                           # 思考开关等差异参数
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    for name in VENDORS:                                       # 依次问五家同一个问题
        try:
            answer = chat(name, "用一句话证明你是你自己")
            print(f"[{name}] {answer}\n")
        except KeyError:
            print(f"[{name}] 未配置 {VENDORS[name]['key_env']}，跳过\n")
        except Exception as e:                                 # 其他错误先打印不中断
            print(f"[{name}] 调用失败：{e}\n")
