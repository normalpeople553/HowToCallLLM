"""五家大模型一键体检脚本。

用途：换电脑 / 隔一段时间后，验证本指南里的调用方式是否仍然可用。
用法：
    1. 在仓库根目录的 .env 填入 key（参考 examples/.env.example）
    2. pip install openai
    3. python tests/verify_calls.py              # 体检全部
       python tests/verify_calls.py kimi doubao  # 只体检指定厂商
安全：只打印成功/失败和 token 用量，绝不打印 key。
"""

import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_env():  # 极简 .env 解析，无需第三方依赖
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        if v and "粘贴" not in v:
            os.environ.setdefault(k.strip(), v)


load_env()
from openai import OpenAI

# 每家：默认调用 + 关思考 + 流式，模型与参数均为 2026-10-13 实测通过的组合
VENDORS = {
    "deepseek": {
        "key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
        "thinking_off": {"thinking": {"type": "disabled"}},
    },
    "kimi": {
        "key_env": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "kimi-k2.6",
        "thinking_off": {"thinking": {"type": "disabled"}},
    },
    "zhipu": {
        "key_env": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4.7-flash",
        "thinking_off": {"thinking": {"type": "disabled"}},
        "max_tokens": 512,  # 免费模型默认思考，给足额度
    },
    "qwen": {
        "key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-flash",
        "thinking_off": None,  # qwen-flash 本身不思考；思考款用 qwen3.x + enable_thinking
    },
    "doubao": {
        "key_env": "ARK_API_KEY",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-seed-2-1-pro-260628",  # 前提：控制台已开通该模型
        "thinking_off": {"thinking": {"type": "disabled"}},
    },
}

QUESTION = "只回复两个字：在的"


def run_one(name, cfg):
    key = os.environ.get(cfg["key_env"], "")
    if not key:
        return [("配置", "SKIP", f"未设置 {cfg['key_env']}")]
    client = OpenAI(api_key=key, base_url=cfg["base_url"], timeout=40)
    common = {"model": cfg["model"], "messages": [{"role": "user", "content": QUESTION}]}
    if "max_tokens" in cfg:
        common["max_tokens"] = cfg["max_tokens"]
    results = []

    # 1. 默认调用
    try:
        r = client.chat.completions.create(**common)
        results.append(("默认调用", "PASS", f"{r.usage.prompt_tokens}/{r.usage.completion_tokens} tokens"))
    except Exception as e:
        results.append(("默认调用", "FAIL", f"{type(e).__name__}: {str(e)[:120]}"))
        return results  # 默认都不通，后面不用试

    # 2. 关思考
    if cfg["thinking_off"]:
        try:
            r = client.chat.completions.create(
                **common, extra_body=cfg["thinking_off"])
            has_reasoning = bool(getattr(r.choices[0].message, "reasoning_content", None))
            tag = "PASS" if not has_reasoning else "WARN(仍有思考链)"
            results.append(("关闭思考", tag, f"{r.usage.completion_tokens} output tokens"))
        except Exception as e:
            results.append(("关闭思考", "FAIL", f"{type(e).__name__}: {str(e)[:120]}"))
    else:
        results.append(("关闭思考", "SKIP", "该模型本身不思考"))

    # 3. 流式
    try:
        stream = client.chat.completions.create(**common, stream=True)
        text = "".join((c.choices[0].delta.content or "") for c in stream)
        results.append(("流式输出", "PASS" if text else "WARN(空)", f"收到 {len(text)} 字"))
    except Exception as e:
        results.append(("流式输出", "FAIL", f"{type(e).__name__}: {str(e)[:120]}"))

    return results


def main():
    names = sys.argv[1:] or list(VENDORS)
    total_fail = 0
    for name in names:
        if name not in VENDORS:
            print(f"[{name}] 未知厂商，可选：{', '.join(VENDORS)}")
            continue
        print(f"\n===== {name} ({VENDORS[name]['model']}) =====")
        for item, status, detail in run_one(name, VENDORS[name]):
            mark = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️ ", "WARN(空)": "⚠️ ", "WARN(仍有思考链)": "⚠️ "}.get(status, "•")
            print(f"  {mark} {item:<4} {status:<6} {detail}")
            if status == "FAIL":
                total_fail += 1
        time.sleep(0.5)
    print()
    if total_fail:
        print(f"体检结束：{total_fail} 项失败，看上面 FAIL 详情（404 多为模型改名/未开通）。")
        sys.exit(1)
    print("体检结束：全部通过 ✅")


if __name__ == "__main__":
    main()
