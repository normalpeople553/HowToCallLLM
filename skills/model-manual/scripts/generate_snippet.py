#!/usr/bin/env python3
"""Generate a minimal model call from the model-manual catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from pprint import pformat
from typing import Any


CATALOG = Path(__file__).resolve().parent.parent / "references" / "vendors.json"


def load_vendors() -> dict[str, dict[str, Any]]:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    return data["vendors"]


def python_snippet(cfg: dict[str, Any], model: str, question: str, stream: bool, thinking: str) -> str:
    args = [
        f'    model={model!r},',
        f'    messages=[{{"role": "user", "content": {question!r}}}],',
    ]
    if cfg.get("default_max_tokens"):
        args.append(f'    max_tokens={cfg["default_max_tokens"]},')
    if thinking == "off":
        args.append(f'    extra_body={pformat(cfg["thinking_off_body"], width=88)},')
    if stream:
        args.append("    stream=True,")

    request = "\n".join(args)
    if stream:
        result = '''for chunk in response:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
print()'''
    else:
        result = "print(response.choices[0].message.content)"

    return f'''import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ[{cfg["key_env"]!r}],
    base_url={cfg["base_url"]!r},
    timeout=40,
)

response = client.chat.completions.create(
{request}
)
{result}
'''


def typescript_snippet(
    cfg: dict[str, Any], model: str, question: str, stream: bool, thinking: str
) -> str:
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
    }
    if cfg.get("default_max_tokens"):
        body["max_tokens"] = cfg["default_max_tokens"]
    if thinking == "off":
        body.update(cfg["thinking_off_body"])
    if stream:
        body["stream"] = True

    body_json = json.dumps(body, ensure_ascii=False, indent=2)
    env_name = cfg["key_env"]
    if stream:
        call = '''const stream = await client.chat.completions.create(request as any);
for await (const chunk of stream as any) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}
process.stdout.write("\\n");'''
    else:
        call = '''const response = await client.chat.completions.create(request as any);
console.log((response as any).choices[0].message.content);'''

    return f'''import OpenAI from "openai";

const apiKey = process.env.{env_name};
if (!apiKey) throw new Error("请先设置 {env_name}");

const client = new OpenAI({{
  apiKey,
  baseURL: {json.dumps(cfg["base_url"], ensure_ascii=False)},
  timeout: 40_000,
}});

const request: Record<string, unknown> = {body_json};
{call}
'''


def curl_snippet(cfg: dict[str, Any], model: str, question: str, stream: bool, thinking: str) -> str:
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
    }
    if cfg.get("default_max_tokens"):
        body["max_tokens"] = cfg["default_max_tokens"]
    if thinking == "off":
        body.update(cfg["thinking_off_body"])
    if stream:
        body["stream"] = True

    payload = json.dumps(body, ensure_ascii=False, indent=2)
    return f'''curl --fail-with-body {cfg["base_url"]}/chat/completions \\
  -H "Authorization: Bearer ${{{cfg["key_env"]}}}" \\
  -H "Content-Type: application/json" \\
  --data-binary @- <<'JSON'
{payload}
JSON
'''


def main() -> None:
    vendors = load_vendors()
    parser = argparse.ArgumentParser(description="从《模型说明书》生成最小可运行调用代码")
    parser.add_argument("--vendor", choices=sorted(vendors), required=True)
    parser.add_argument("--language", choices=("python", "typescript", "curl"), default="python")
    parser.add_argument("--model", help="覆盖厂商默认模型")
    parser.add_argument("--question", default="你好，请用一句话介绍你自己")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--thinking", choices=("default", "off"), default="default")
    args = parser.parse_args()

    cfg = vendors[args.vendor]
    model = args.model or cfg["default_model"]
    if args.thinking == "off" and not cfg.get("thinking_off_body"):
        parser.error(f"{args.vendor} 没有登记关闭思考的参数")

    generators = {
        "python": python_snippet,
        "typescript": typescript_snippet,
        "curl": curl_snippet,
    }
    print(generators[args.language](cfg, model, args.question, args.stream, args.thinking), end="")


if __name__ == "__main__":
    main()
