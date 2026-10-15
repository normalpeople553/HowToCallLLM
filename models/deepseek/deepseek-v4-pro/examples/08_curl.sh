#!/usr/bin/env bash
# DeepSeek Chat Completions cURL 示例；使用 Python 3 标准库检查回答。
# 官方来源：https://api-docs.deepseek.com/api/create-chat-completion/

set -euo pipefail
: "${DEEPSEEK_API_KEY:?请先设置 DEEPSEEK_API_KEY}"

curl --silent --show-error --fail https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
  -H "Content-Type: application/json" \
  --data-binary @- <<'JSON' | python3 -c '
import json
import sys

response = json.load(sys.stdin)
choices = response.get("choices") or []
if not choices:
    raise SystemExit("响应没有 choices")
choice = choices[0]
if choice.get("finish_reason") != "stop":
    raise SystemExit("回答未正常完成，请检查 finish_reason 和思考、回答预算")
message = choice.get("message") or {}
answer = message.get("content")
if message.get("tool_calls") or not isinstance(answer, str) or not answer.strip():
    raise SystemExit("响应没有可用的最终正文")
print(answer)
print("本次用量：", response.get("usage"))
'
{
  "model": "deepseek-v4-pro",
  "messages": [
    {"role": "user", "content": "用一句话介绍你自己"}
  ]
}
JSON
