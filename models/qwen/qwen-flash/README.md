# `qwen-flash` 调用说明书

按功能查找本型号的[官方改写示例与运行清单](examples/sources.json)，跨型号浏览[官方示例索引](../../../docs/官方示例索引.md)。清单单独标明文件的官方出处、改写与验证范围；本次新增示例未执行真实 API 调用，不继承历史报告的通过状态。

> 核对日期：**2026-10-13**。官方事实均附原始链接；机器卡片见 [`qwen-flash.json`](../../../skills/model-manual/references/models/qwen-flash.json)。

## 1. 一眼看懂

| 项目 | 当前值 | 官方来源 |
|---|---|---|
| Model ID | `qwen-flash` | [模型列表](https://help.aliyun.com/zh/model-studio/getting-started/models) |
| 当前别名版本 | `qwen-flash-2025-07-28` | [模型价格](https://help.aliyun.com/zh/model-studio/model-pricing) |
| 上下文 | 1M tokens | [模型列表](https://help.aliyun.com/zh/model-studio/getting-started/models) |
| 接口 | OpenAI Chat Completions 兼容 | [接口文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) |
| 输入 | 文本 | [模型列表](https://help.aliyun.com/zh/model-studio/getting-started/models) |

## 2. 地址选择与最小调用

官方当前推荐 Workspace 专属地址 `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`；旧的 `https://dashscope.aliyuncs.com/compatible-mode/v1` 仍在兼容文档中，本仓库实测后者可用。生产项目应优先采用控制台给出的 Workspace 地址。[接口文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
response = client.chat.completions.create(
    model="qwen-flash",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)
print(response.choices[0].message.content)
```

密钥创建与环境变量名称见[首次调用](https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen)。完整示例：[`examples/01_basic.py`](examples/01_basic.py)。

## 3. 思考与流式输出

OpenAI Python SDK 通过 `extra_body={"enable_thinking": true|false}` 传思考开关；直接 HTTP 与 Node.js 示例按接口文档把该字段放在请求体顶层。思考内容字段为 `reasoning_content`。[接口文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

```python
response = client.chat.completions.create(
    model="qwen-flash",
    messages=[{"role": "user", "content": "分析这个问题"}],
    extra_body={"enable_thinking": False},
)
```

设置 `stream=True` 后逐块读取 `delta.content`。[接口文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) 示例：[`examples/02_streaming.py`](examples/02_streaming.py) · [`examples/03_thinking.py`](examples/03_thinking.py)。

## 4. JSON 与 Tool Calling

JSON 对象模式使用 `response_format={"type":"json_object"}`，提示词必须明确要求 JSON；支持范围和 JSON Schema 写法以[结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)为准。示例：[`examples/04_json_output.py`](examples/04_json_output.py)。

Qwen Flash 系列支持 Function Calling；`tools` 定义函数，模型返回参数，应用负责执行并回传结果。Qwen 系列不支持 `tool_choice="required"`，可使用自动选择或文档支持的指定函数形式。[Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling) 仓库的完整闭环示例包含整批参数校验、模拟天气执行、`tool_call_id` 回传和最终答复；天气数据仅供演示。[examples/05_tool_calling.py](examples/05_tool_calling.py)

## 5. 价格

2026-10-13 全球部署价格快照（人民币/百万 tokens）：输入不超过 128K 时输入 ¥0.15、输出 ¥1.50；128K–256K 时 ¥0.60/¥6.00；256K–1M 时 ¥1.20/¥12.00。区域、部署方式和阶梯会影响价格，使用前必须复核[官方价格页](https://help.aliyun.com/zh/model-studio/model-pricing)。

## 6. 给 Agent 的固定配置

```yaml
provider: qwen
model: qwen-flash
base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
api_key_env: DASHSCOPE_API_KEY
thinking_off_extra_body:
  enable_thinking: false
modalities: [text]
```

模型、地址和参数来自[模型列表](https://help.aliyun.com/zh/model-studio/getting-started/models)与[接口文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)；[2026-10-13 历史基础报告](verification/2026-10-13.json)保留当时结果，最新严格流程结果查[验证状态](../../../docs/验证状态.md)。使用锁定依赖复测：`python tests/verify_qwen_flash.py --report /tmp/qwen-flash-verification.json`，环境变量与退出码见[验证与复现](../../../docs/验证与复现.md)。

## 7. 必看踩雷

百炼的 `max_tokens` 语义会随模型变化，而 `max_completion_tokens` 明确限制“思维链 + 回答”；新代码不能假定所有模型都按同一种方式计算思考预算。[OpenAI Chat Completions 兼容文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) Python SDK 的 `enable_thinking` 等扩展参数必须放进 `extra_body`。对照表和检测代码见[真实踩雷与生产检查](../../../docs/06-真实踩雷与生产检查.md)。

具体到旧 `qwen-flash` 型号，官方当前把 `max_tokens` 归为只限制正文的范围；`max_completion_tokens` 的千问 Flash 支持列表从 Qwen3.5-Flash 起，因此生成器不会给 `qwen-flash` 自动替换这个参数。[OpenAI Chat Completions 兼容文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)
