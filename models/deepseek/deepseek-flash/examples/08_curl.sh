#!/usr/bin/env bash
# DeepSeek Chat Completions cURL 最小调用。
# 官方来源：https://api-docs.deepseek.com/api_samples/chat_curl/

set -euo pipefail
: "${DEEPSEEK_API_KEY:?请先设置 DEEPSEEK_API_KEY}"

curl --fail-with-body https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
  -H "Content-Type: application/json" \
  --data-binary @- <<'JSON'
{
  "model": "deepseek-flash",
  "messages": [
    {"role": "user", "content": "用一句话介绍你自己"}
  ]
}
JSON
