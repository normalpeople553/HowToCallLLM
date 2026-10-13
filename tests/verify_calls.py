"""五家大模型一键体检脚本。

用途：换电脑 / 隔一段时间后，验证本指南里的调用方式是否仍然可用。
用法：
    1. 在仓库根目录的 .env 填入 key（参考 examples/.env.example）
    2. pip install openai
    3. python tests/verify_calls.py              # 体检全部
       python tests/verify_calls.py kimi doubao  # 只体检指定厂商
安全：只打印成功/失败和 token 用量，绝不打印 key。
"""

import json
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
        k = k.removeprefix("export ").strip()
        v = v.strip().strip('"').strip("'")
        if v and "粘贴" not in v:
            os.environ.setdefault(k, v)


load_env()

CATALOG = REPO_ROOT / "skills" / "model-manual" / "references" / "vendors.json"
VENDORS = json.loads(CATALOG.read_text(encoding="utf-8"))["vendors"]

QUESTION = "只回复两个字：在的"


def run_one(name, cfg):
    key = os.environ.get(cfg["key_env"], "")
    if not key:
        return [("配置", "SKIP", f"未设置 {cfg['key_env']}")]
    try:
        from openai import OpenAI
    except ImportError:
        return [("依赖", "FAIL", "未安装 openai，请先运行 pip install -r requirements.txt")]
    client = OpenAI(api_key=key, base_url=cfg["base_url"], timeout=40)
    common = {
        "model": cfg["default_model"],
        "messages": [{"role": "user", "content": QUESTION}],
    }
    if "default_max_tokens" in cfg:
        common["max_tokens"] = cfg["default_max_tokens"]
    results = []

    # 1. 默认调用
    try:
        r = client.chat.completions.create(**common)
        content = r.choices[0].message.content or ""
        status = "PASS" if content.strip() else "FAIL"
        detail = f"{r.usage.prompt_tokens}/{r.usage.completion_tokens} tokens"
        if not content.strip():
            detail += "，正文为空"
        results.append(("默认调用", status, detail))
    except Exception as e:
        results.append(("默认调用", "FAIL", f"{type(e).__name__}: {str(e)[:120]}"))
        return results  # 默认都不通，后面不用试

    # 2. 关思考
    if cfg.get("thinking_off_body"):
        try:
            thinking_common = dict(common)
            thinking_common["model"] = cfg.get("thinking_model", cfg["default_model"])
            r = client.chat.completions.create(
                **thinking_common, extra_body=cfg["thinking_off_body"])
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
    total_run = 0
    total_skip = 0
    for name in names:
        if name not in VENDORS:
            print(f"[{name}] 未知厂商，可选：{', '.join(VENDORS)}")
            total_fail += 1
            continue
        print(f"\n===== {name} ({VENDORS[name]['default_model']}) =====")
        for item, status, detail in run_one(name, VENDORS[name]):
            mark = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️ ", "WARN(空)": "⚠️ ", "WARN(仍有思考链)": "⚠️ "}.get(status, "•")
            print(f"  {mark} {item:<4} {status:<6} {detail}")
            if status == "FAIL":
                total_fail += 1
            if status == "SKIP":
                total_skip += 1
            else:
                total_run += 1
        time.sleep(0.5)
    print()
    if total_fail:
        print(f"体检结束：执行 {total_run} 项，跳过 {total_skip} 项，失败 {total_fail} 项。")
        sys.exit(1)
    if total_run == 0:
        print(f"体检未执行：跳过 {total_skip} 项，请至少配置一家厂商的 API Key。")
        sys.exit(2)
    print(f"体检结束：执行 {total_run} 项，跳过 {total_skip} 项，全部通过 ✅")


if __name__ == "__main__":
    main()
