#!/usr/bin/env bash
# MiniMax-M2.7 原生旧入口示例；新接入优先使用 /v1/chat/completions。
# 官方：https://platform.minimax.cn/docs/api-reference/text-post （已标 deprecated）
# max_completion_tokens 是该原生文档正式列出的字段，max_tokens 已弃用。
# 本例固定使用当前国区官方域名 api.minimax.cn；旧 api.minimaxi.com 本轮未实测。
# 国际平台使用 api.minimax.io 和对应平台凭据，不能据此推断跨平台 Key 通用。
# 模型服务已有调整公告，调用前核对 sources.json 的生命周期来源。
# 需要 bash、curl 和 Python 3 标准库。不会执行模型返回的代码。

set -euo pipefail
: "${MINIMAX_API_KEY:?请先设置 MINIMAX_API_KEY}"

curl --silent --show-error --fail --max-time 180 \
  https://api.minimax.cn/v1/text/chatcompletion_v2 \
  -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
  -H "Content-Type: application/json" \
  --data-binary @- <<'JSON' | python3 -c '
import json
import sys

response = json.load(sys.stdin)
base = response.get("base_resp")
code = base.get("status_code") if isinstance(base, dict) else None
if isinstance(code, bool) or not isinstance(code, int) or code != 0:
    raise SystemExit("MiniMax 原生接口返回非零或缺失的业务状态码")
choices = response.get("choices") or []
if not choices:
    raise SystemExit("原生响应没有 choices")
choice = choices[0]
if choice.get("finish_reason") != "stop":
    raise SystemExit("回答未完整结束，请检查思考与正文预算")
message = choice.get("message") or {}
if message.get("tool_calls"):
    raise SystemExit("收到未处理的工具调用")
text = message.get("content")
if not isinstance(text, str):
    raise SystemExit("没有最终正文")
text = text.strip()
while text.startswith("<think>"):
    _, closing, text = text.partition("</think>")
    if not closing:
        raise SystemExit("内联思考未完整结束")
    text = text.strip()
if not text:
    raise SystemExit("只有思考或空内容，没有最终正文")
print(text)
print("本次用量：", response.get("usage"))
'
{
  "model": "MiniMax-M2.7",
  "messages": [
    {"role": "user", "content": "用一句话介绍你自己。"}
  ],
  "max_completion_tokens": 16384
}
JSON
