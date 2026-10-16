# `deepseek-v4-pro` 调用说明书

[English](README.en.md) · [模型目录](../../README.md) · [参数说明](parameters.md)

> 核对日期：**2026-10-15**。当前官方托管 API 入口是 `deepseek-flash` 与 `deepseek-v4-pro`。本页只讲 `deepseek-v4-pro`；旧名称 `deepseek-v4-flash` 和 `deepseek-v4-flash-vision-exp` 会路由到 Flash，不是 Pro 的别名。

## 模型身份

| 项目 | 值 |
|---|---|
| API 模型 ID | `deepseek-v4-pro` |
| 当前服务版本 | `DeepSeek-V4-Pro-0813` |
| API 地址 | `https://api.deepseek.com` |
| 密钥变量 | `DEEPSEEK_API_KEY` |
| 上下文 | 1M tokens |
| 最大输出 | 384K tokens |
| 账户并发上限 | 500 |
| 默认思考 | 开启，默认 `high` |
| 图片输入 | 不支持 |

型号、价格、上下文、视觉支持和并发限制分别以官方 [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) 与 [Rate Limit & Isolation](https://api-docs.deepseek.com/quick_start/rate_limit/) 为准。

## 安装与密钥

```powershell
py -m pip install openai
$env:DEEPSEEK_API_KEY = "你的密钥"
```

```bash
python3 -m pip install openai
export DEEPSEEK_API_KEY="你的密钥"
```

密钥只放环境变量或本地 `.env`，不要写入代码、提交记录、终端截图或帖子。

## 最小调用

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=120,
)

response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)
print(response.choices[0].message.content)
```

直接运行完整文件：

```powershell
.venv\Scripts\python.exe models/deepseek/deepseek-v4-pro/examples/01_basic.py
```

```bash
python models/deepseek/deepseek-v4-pro/examples/01_basic.py
```

## 已提供示例

| 文件 | 用途 |
|---|---|
| [`01_basic.py`](examples/01_basic.py) | 普通对话与完整性检查 |
| [`02_streaming.py`](examples/02_streaming.py) | 流式正文、思考内容和用量 |
| [`03_thinking.py`](examples/03_thinking.py) | 开关思考并读取 `reasoning_content` |
| [`04_json_output.py`](examples/04_json_output.py) | JSON 输出及业务字段校验 |
| [`05_tool_calling.py`](examples/05_tool_calling.py) | 非思考工具调用闭环 |
| [`07_typescript.ts`](examples/07_typescript.ts) | TypeScript 普通对话 |
| [`08_curl.sh`](examples/08_curl.sh) | cURL 普通对话 |

示例来源与核验状态见 [`examples/sources.json`](examples/sources.json)。维护者使用 `deepseek-v4-pro` 准确 ID，将本页七份完整文件分别向官方 API 真实运行，包含文档所列 `npx tsx` 与 Bash 命令；均通过文件内的完成性检查。这只覆盖所用输入、参数与账户，不代表模型效果、长期可用性或并发能力。密钥、模型回复、原始记录和测试时间不随仓库发布。

## 关键能力

- Chat Completions、流式输出、思考、JSON Object、工具调用均有官方文档和本仓库示例。
- Responses API、Anthropic 兼容 API、前缀续写、FIM 和自动上下文缓存由官方列为支持能力，本批次没有为 Pro 重复增加示例。
- `strict` 工具调用、对话前缀续写属于 Beta 接口；接入生产前应单独验证。
- Pro 不支持图片输入，因此不要复制 Flash 的视觉、Files 图片或 Responses 图片示例后只改模型名。
- 思考模式会忽略 `temperature`、`presence_penalty`、`frequency_penalty`；需要稳定结构时仍要在应用侧解析和校验。

完整字段解释见[参数说明](parameters.md)。跨厂商和生产环境的失败处理见[真实踩雷与生产检查](../../../docs/06-真实踩雷与生产检查.md)。

## 官方资料

- [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/)
- [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)
- [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)
- [JSON Output](https://api-docs.deepseek.com/guides/json_mode/)
- [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)
- [Rate Limit & Isolation](https://api-docs.deepseek.com/quick_start/rate_limit/)
