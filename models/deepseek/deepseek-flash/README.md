# `deepseek-flash` 调用说明书

按功能查找本型号的[官方改写示例与运行清单](examples/sources.json)，跨型号浏览[官方示例索引](../../../docs/官方示例索引.md)。清单单独标明文件的官方出处、改写与验证范围；本次新增示例未执行真实 API 调用，不继承历史报告的通过状态。

> 核对日期：**2026-10-13**。本页只记录 DeepSeek 官方文档可核验的事实和仓库明确标注的项目建议；机器可读事实见 [`deepseek-flash.json`](../../../skills/model-manual/references/models/deepseek-flash.json)。

## 1. 模型身份

| 项目 | 当前值 | 官方来源 |
|---|---|---|
| API Model ID | `deepseek-flash` | [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| 当前服务版本 | DeepSeek-V4.1-Flash | [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| OpenAI 格式地址 | `https://api.deepseek.com` | [Your First API Call](https://api-docs.deepseek.com/guides/codex) |
| 上下文长度 | 1M tokens | [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| 最大输出 | 384K tokens | [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) |
| 默认模式 | 开启思考，默认强度 `high` | [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/) |
| 视觉输入 | 支持 | [Vision](https://api-docs.deepseek.com/guides/vision/) |

旧名称 `deepseek-v4-flash` 和 `deepseek-v4-flash-vision-exp` 仍被接口接受，但原模型已经退役，请求会临时路由到 V4.1 Flash；新代码应使用 `deepseek-flash`。[Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) · [Change Log](https://api-docs.deepseek.com/updates/)

## 2. 开通与环境

在 [DeepSeek API Keys](https://platform.deepseek.com/api_keys) 创建密钥；官方示例使用 `DEEPSEEK_API_KEY` 环境变量和 `https://api.deepseek.com` 地址。[Your First API Call](https://api-docs.deepseek.com/guides/codex)

```bash
export DEEPSEEK_API_KEY="你的Key"
python3 -m pip install -r requirements-lock.txt
```

本项目规定密钥只能从环境变量或被 Git 忽略的 `.env` 读取，不能写进代码、日志或提交记录；这是仓库安全约定。[来源与核验规则](../../../docs/来源与核验规则.md) · [`.gitignore`](../../../.gitignore)

## 3. 最小调用

下面三种写法都调用官方 `POST /chat/completions` 接口；请求体字段以 [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)为准。

### Python

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=60,
)

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)
print(response.choices[0].message.content)
print(response.usage)
```

可运行文件：[`examples/01_basic.py`](examples/01_basic.py)。

### TypeScript

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.DEEPSEEK_API_KEY,
  baseURL: "https://api.deepseek.com",
});

const response = await client.chat.completions.create({
  model: "deepseek-flash",
  messages: [{ role: "user", content: "用一句话介绍你自己" }],
});
console.log(response.choices[0].message.content);
```

可运行文件：[`examples/07_typescript.ts`](examples/07_typescript.ts)。

### cURL

```bash
curl --fail-with-body https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-flash",
    "messages": [{"role": "user", "content": "用一句话介绍你自己"}]
  }'
```

可运行文件：[`examples/08_curl.sh`](examples/08_curl.sh)。

## 4. 常用请求参数

下表来自官方 [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)；完整字段、类型和限制应以该页面的当前版本为准。

| 参数 | 用途 | `deepseek-flash` 注意点 |
|---|---|---|
| `model` | 选择模型 | 使用 `deepseek-flash` |
| `messages` | 按顺序提交对话 | 至少一条；支持 system、user、assistant、tool |
| `stream` | 返回 SSE 流 | `true` 时逐块读取 `delta` |
| `max_tokens` | 限制生成长度 | 取值 1–384K；输入与输出总量不能超过上下文 |
| `thinking` | 开关思考 | OpenAI Python SDK 通过 `extra_body` 传入 |
| `reasoning_effort` | 控制思考强度 | `none`、`low`、`high`、`max` |
| `response_format` | JSON 输出 | `{"type":"json_object"}` |
| `tools` | 声明外部函数 | 模型只生成调用参数，应用负责执行 |
| `tool_choice` | 控制工具选择 | 思考模式不支持 `required` 和指定函数 |
| `stop` | 遇到指定文本停止 | 具体限制以接口页为准 |
| `user_id` | 业务侧用户隔离 | OpenAI SDK 通过 `extra_body` 传入 |

## 5. 流式输出

流式响应使用 `text/event-stream`，正文增量位于 `choices[0].delta.content`，思考增量位于 `choices[0].delta.reasoning_content`。[Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) · [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)

```python
stream = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": "用三句话解释缓存"}],
    stream=True,
)

for chunk in stream:
    reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
    content = chunk.choices[0].delta.content
    if reasoning:
        print(reasoning, end="", flush=True)
    if content:
        print(content, end="", flush=True)
```

完整示例：[`examples/02_streaming.py`](examples/02_streaming.py)。

官方并发文档说明，等待推理时非流式请求可能收到空行，流式请求可能收到 `: keep-alive` 注释；自行解析 HTTP 时应忽略这些保活内容。[Rate Limit & Isolation](https://api-docs.deepseek.com/quick_start/rate_limit/)

## 6. 思考模式

`deepseek-flash` 默认开启思考，默认强度为 `high`；`reasoning_effort="none"` 可关闭，`low`、`high`、`max` 可开启并调整强度。[Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)

```python
# 关闭思考
response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": "1+1 等于几？"}],
    extra_body={"thinking": {"type": "disabled"}},
)

# 开启并使用最高强度
response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": "证明这个结论……"}],
    reasoning_effort="max",
    extra_body={"thinking": {"type": "enabled"}},
)
```

完整示例：[`examples/03_thinking.py`](examples/03_thinking.py)。

思考模式会忽略 `temperature`、`presence_penalty` 和 `frequency_penalty`；`top_p` 只在思考模式生效，有效范围为 0.95–1.0，非思考模式固定为 1.0。[Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)

没有工具调用时，后续轮次无需回传旧的 `reasoning_content`，即使回传也不会进入上下文；请求带 `tools` 时，必须完整回传之前每轮的 `reasoning_content`，否则接口返回 400。[Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)

## 7. 多轮对话

Chat Completions 不在服务端替应用保存普通对话历史；官方多轮示例把之前的 user/assistant 消息追加到下一次 `messages` 请求中。[Thinking Mode：Multi-turn Conversation](https://api-docs.deepseek.com/guides/thinking_mode/)

```python
messages = [{"role": "user", "content": "我叫小明。"}]
first = client.chat.completions.create(model="deepseek-flash", messages=messages)
messages.append({"role": "assistant", "content": first.choices[0].message.content})
messages.append({"role": "user", "content": "我叫什么？"})
second = client.chat.completions.create(model="deepseek-flash", messages=messages)
print(second.choices[0].message.content)
```

## 8. JSON 输出

官方要求同时设置 `response_format={"type":"json_object"}`，并在 system 或 user 消息中明确包含“json”及期望格式；还应设置合理的 `max_tokens`，避免 JSON 被截断。[JSON Output](https://api-docs.deepseek.com/guides/json_mode/)

```python
response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {"role": "system", "content": "只返回 json，格式示例：{\"name\":\"张三\",\"age\":18}"},
        {"role": "user", "content": "人物：小明，26岁"},
    ],
    response_format={"type": "json_object"},
    max_tokens=512,
)
```

完整示例会检查 `finish_reason` 并调用 `json.loads`：[`examples/04_json_output.py`](examples/04_json_output.py)。官方提示 JSON Output 偶尔可能返回空内容，可尝试调整提示词。[JSON Output](https://api-docs.deepseek.com/guides/json_mode/)

## 9. Tool Calling

模型返回的是工具名与参数，工具函数本身必须由应用实现和执行；官方示例在执行后把 `tool_call_id` 与结果作为 `role="tool"` 消息交回模型。[Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市天气",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}]
```

完整的两段式调用与参数校验示例：[`examples/05_tool_calling.py`](examples/05_tool_calling.py)。

思考模式下使用工具时必须保留并回传所有历史 `reasoning_content`；思考模式不支持 `tool_choice="required"` 或指定函数，使用这些选项前需要关闭思考。[Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/) · [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)

严格工具模式属于 Beta，需要使用 `https://api.deepseek.com/beta`，所有函数设置 `strict: true`，并遵守官方支持的 JSON Schema 子集。[Tool Calls：strict Mode](https://api-docs.deepseek.com/guides/tool_calls/)

## 10. 图片输入

`deepseek-flash` 支持 JPEG、PNG、GIF 和 WebP，可通过公开 URL、base64 data URL 或 Files API 的 `file_id` 提交；Chat Completions 中图片只允许出现在 `user` 消息，放在 system 或 assistant 消息会返回 400。[Vision](https://api-docs.deepseek.com/guides/vision/)

```python
response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这张图片"},
            {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}},
        ],
    }],
)
```

完整示例：[`examples/06_vision.py`](examples/06_vision.py)。

官方限制包括：公开 URL 最长 8192 字符，内联或 URL 单图最大 32 MiB，`file_id` 单图最大 64 MiB，每次最多 600 张图片；完整尺寸、总量和像素限制见 [Vision：Limits](https://api-docs.deepseek.com/guides/vision/)。

## 11. 上下文缓存与用量

DeepSeek 上下文缓存默认开启，不需要修改代码；后续请求完整复用已经持久化的前缀单元时可能命中缓存，但官方明确说明缓存按 best-effort 工作，不保证命中。[Context Caching](https://api-docs.deepseek.com/guides/kv_cache/)

```python
usage = response.usage
print("缓存命中：", usage.prompt_cache_hit_tokens)
print("缓存未命中：", usage.prompt_cache_miss_tokens)
```

`usage.prompt_cache_hit_tokens` 和 `usage.prompt_cache_miss_tokens` 是官方提供的命中统计字段。[Context Caching：Checking Cache Hit Status](https://api-docs.deepseek.com/guides/kv_cache/)

## 12. 价格快照

以下是 **2026-10-13** 从官方页面核对的美元价格快照，单位为每 100 万 tokens；价格具有时效性，实际使用前必须点击[官方价格页](https://api-docs.deepseek.com/quick_start/pricing/)复核。

| 项目 | 非高峰 | 高峰 |
|---|---:|---:|
| 缓存命中输入 | $0.003 | $0.006 |
| 缓存未命中输入 | $0.15 | $0.30 |
| 输出 | $0.60 | $1.20 |

官方将工作日 01:00–04:00 与 06:00–10:00 UTC 定义为高峰时段，中国公共假期除外；其他时间包括周末和中国公共假期全天为非高峰。[Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/)

## 13. 并发、超时与重试

官方当前列出的 `deepseek-flash` 账户级并发上限为 2500，超过时返回 HTTP 429；该限制按账户计算，不按 API Key 分开。[Rate Limit & Isolation](https://api-docs.deepseek.com/quick_start/rate_limit/)

| 状态码 | 官方含义 | 首要动作 |
|---|---|---|
| 400 | 请求体格式错误 | 按错误文本检查 JSON 与消息结构 |
| 401 | API Key 错误 | 检查 Key |
| 402 | 余额不足 | 检查账户余额 |
| 422 | 参数无效 | 按错误文本检查参数 |
| 429 | 请求过快 | 降低并发或请求频率 |
| 500 | 服务端错误 | 短暂等待后重试 |
| 503 | 服务过载 | 短暂等待后重试 |

状态码含义与官方建议来自 [Error Codes](https://api-docs.deepseek.com/quick_start/error_codes/)。

项目建议只对 429、500、503 和网络超时做有上限的指数退避重试；不要自动重试 400、401、402、422，以免掩盖配置问题或重复计费。[项目规则](../../../docs/来源与核验规则.md)

## 14. 能力矩阵

下表只表达官方文档状态，不等同于仓库已经用真实 Key 验证；证据链接位于每一行。

| 能力 | 状态 | 官方证据 |
|---|---|---|
| Chat Completions | 已文档化 | [API](https://api-docs.deepseek.com/api/create-chat-completion/) |
| 流式输出 | 已文档化 | [API](https://api-docs.deepseek.com/api/create-chat-completion/) |
| 思考与强度控制 | 已文档化 | [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/) |
| JSON Object | 已文档化 | [JSON Output](https://api-docs.deepseek.com/guides/json_mode/) |
| Tool Calling | 已文档化 | [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/) |
| 严格工具 Schema | Beta | [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/) |
| 图片输入 | 已文档化 | [Vision](https://api-docs.deepseek.com/guides/vision/) |
| Responses API | 已文档化 | [Responses API](https://api-docs.deepseek.com/guides/responses_api/) |
| Anthropic API | 已文档化 | [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| 上下文缓存 | 自动开启 | [Context Caching](https://api-docs.deepseek.com/guides/kv_cache/) |
| Chat Prefix Completion | Beta | [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| FIM Completion | 仅非思考模式 | [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) |

## 15. 给 Agent 的执行规则

以下是本仓库对编程 Agent 的约定，规则依据是[来源与核验规则](../../../docs/来源与核验规则.md)和本模型的[机器卡片](../../../skills/model-manual/references/models/deepseek-flash.json)。

1. 使用 `deepseek-flash`，不要为新代码生成旧别名。
2. Key 只读取 `DEEPSEEK_API_KEY`，不得硬编码或打印。
3. 用户未要求思考模式时，说明其默认开启；需要低延迟时再明确关闭。
4. 使用 JSON Output 时同时写明 JSON 提示、`response_format`、解析和截断检查。
5. 执行工具前必须验证工具名与参数；模型返回值不能直接当可信指令执行。
6. 使用思考模式工具调用时必须保留 `reasoning_content`。
7. 报价时给出核对日期与官方价格链接，不把本页快照当永久价格。
8. 未在机器卡片或官方来源中声明的能力标记为未知，不自行推断。

## 16. 验证

**2026-10-13 历史基础验证**记录七项通过，范围为普通调用、流式、思考开关、JSON、首段工具调用和图片请求格式；旧报告没有记录完整结束原因，没有验证工具结果回传或图片内容识别。[历史脱敏记录](verification/2026-10-13.json) 最新的严格流程结果查[验证状态](../../../docs/验证状态.md)，复现环境和报告格式见[验证与复现](../../../docs/验证与复现.md)。

静态检查不会发送请求：

```bash
python -m unittest tests/test_models.py
```

在线检查会产生真实请求，并要求显式设置 Key；测试范围与脱敏规则见 [`tests/verify_deepseek_flash.py`](../../../tests/verify_deepseek_flash.py)。

```bash
DEEPSEEK_API_KEY="你的Key" python tests/verify_deepseek_flash.py --report /tmp/deepseek-flash-verification.json
```

## 17. 必看踩雷

不要只判断 HTTP 200：`finish_reason="length"` 表示生成达到限制，正文可能不完整；usage 还会在 `completion_tokens_details.reasoning_tokens` 中给出思考 token。[Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) JSON Mode 如果没有在提示词里明确要求 JSON，还可能持续生成空白直至达到 token 上限。[JSON Output](https://api-docs.deepseek.com/guides/json_mode/) 检测代码和工具、流式相关问题见[真实踩雷与生产检查](../../../docs/06-真实踩雷与生产检查.md)。

本仓库可运行示例已加入结束原因、空正文和流式终止检查；[工具示例](examples/05_tool_calling.py)使用有轮次上限的模拟天气闭环，先校验整批参数，再回传结果。它演示调用流程，不提供实时天气。[实现](examples/05_tool_calling.py)
