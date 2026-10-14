# `kimi-k2.6` 调用说明书

[English](README.en.md) · [人类篇](../../../human/README.md)

逐项理解示例中的参数、默认值与副作用：见[参数详解与逐文件映射](parameters.md)。

按功能查找[官方改写来源与运行清单](examples/sources.json)，跨型号浏览[官方示例索引](../../../docs/官方示例索引.md)。验证分为[历史统一流程](../../../docs/验证状态.md)与[当前逐文件实测](../../../docs/示例实测状态.md)，以对应报告的源码、参数、输入和环境为准，不互相继承通过状态。[证据规则](../../../docs/来源与核验规则.md)

本页代码块是说明性片段；运行与验证以链接的完整文件为准。片段、自改参数及生成器任意新组合不继承文件的实测结果。[参数与文件映射](parameters.md)；[证据边界](../../../docs/来源与核验规则.md)

> 官方资料核对日期：**2026-10-13**。事实均附原始链接；两层实测以各自报告的证据编号和范围为准，不用资料核对日期代替执行证据。机器卡片见 [`kimi-k2.6.json`](../../../skills/model-manual/references/models/kimi-k2.6.json)。

## 1. 一眼看懂

| 项目 | 当前值 | 官方来源 |
|---|---|---|
| Model ID | `kimi-k2.6` | [Kimi K2.6](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) |
| Base URL | `https://api.moonshot.cn/v1` | [快速开始](https://platform.kimi.com/docs/get-api-key) |
| 上下文 | 256K tokens | [Kimi K2.6](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) |
| 输入 | 文本、图片、视频 | [Kimi K2.6](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) |
| 关键能力 | 思考、流式输出、JSON、Tool Calling | [模型参数](https://platform.kimi.com/docs/api/models-overview) · [Chat API](https://platform.kimi.com/docs/api/chat) |

## 2. 最小调用

在[控制台](https://platform.kimi.com/console/api-keys)创建 Key；官方快速开始使用 `MOONSHOT_API_KEY`。[快速开始](https://platform.kimi.com/docs/get-api-key)

```bash
export MOONSHOT_API_KEY="你的Key"
python3 -m pip install -r requirements-lock.txt
python models/kimi/kimi-k2.6/examples/01_basic.py
```

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["MOONSHOT_API_KEY"],
    base_url="https://api.moonshot.cn/v1",
)
response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)
print(response.choices[0].message.content)
```

接口路径、消息结构和返回字段以 [Chat Completions API](https://platform.kimi.com/docs/api/chat) 为准；完整文件见 [`examples/01_basic.py`](examples/01_basic.py)。

## 3. 思考模式

K2.6 默认开启思考；可传 `thinking.type=enabled` 或 `disabled`。OpenAI Python SDK 未建模的字段放进 `extra_body`；思考内容位于 `reasoning_content`。[思考模型](https://platform.kimi.com/docs/guide/use-thinking-models) · [模型参数](https://platform.kimi.com/docs/api/models-overview)

```python
response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "分析这个问题"}],
    extra_body={"thinking": {"type": "disabled"}},
)
```

K2.6 不支持 `reasoning_effort`；温度在思考模式固定为 1.0、非思考模式固定为 0.6，`top_p` 固定为 0.95，`n` 固定为 1，不应传入冲突值。[模型参数](https://platform.kimi.com/docs/api/models-overview)

完整示例：[`examples/03_thinking.py`](examples/03_thinking.py)。

## 4. 流式输出

设置 `stream=True` 后逐块读取 `choices[0].delta.content`；思考增量在 `delta.reasoning_content`。[流式输出](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api) · [思考模型](https://platform.kimi.com/docs/guide/use-thinking-models)

完整示例：[`examples/02_streaming.py`](examples/02_streaming.py)。

## 5. JSON 与结构化输出

JSON Mode 使用 `response_format={"type":"json_object"}`，提示词仍应明确要求 JSON 并说明字段；收到内容后仍要做 `json.loads` 和业务校验。[JSON Mode](https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api)

需要 Schema 约束时查看 [response_format](https://platform.kimi.com/docs/guide/response_format) 的 Structured Output 支持范围，不要假设任意 JSON Schema 关键字都可用。完整 JSON Mode 示例：[`examples/04_json_output.py`](examples/04_json_output.py)。

## 6. Tool Calling

把函数的名称、描述和参数 Schema 放入 `tools`；模型返回 `tool_calls`，应用执行函数后再用 `role="tool"` 与对应 `tool_call_id` 回传结果。[工具调用](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls)

K2.6 不支持 `tool_choice="required"`；可让模型自动选择、禁止调用或按官方支持形式指定工具。[工具调用约束](https://platform.kimi.com/docs/guide/use-tool-choice) 仓库的 [`examples/05_tool_calling.py`](examples/05_tool_calling.py)包含工具参数校验、模拟天气执行、`tool_call_id` 回传和最终答复；循环有上限，完整 assistant 消息会保留。

## 7. 图片、视频与缓存

图片支持 JPEG、PNG、GIF、WebP、BMP、HEIC、HEIF；视频支持 MP4、MPEG、MOV、AVI、FLV、MPG、WebM、WMV、3GPP。内容必须传数组，不能把数组序列化成字符串；SVG 不作为图片格式接受。[视觉模型](https://platform.kimi.com/docs/guide/use-kimi-vision-model)

可运行图片示例：[examples/06_vision.py](examples/06_vision.py)；输入方式和运行命令见文件说明。

当前官方图片字段接受 base64 data URL 或 `ms://<file_id>`，不直接接受远程 HTTP(S) 图片地址；本仓库图片脚本使用 `IMAGE_PATH` 编码本地文件，拒绝 `IMAGE_URL`。不要将其他厂商的远程图片写法直接复制到 Kimi。[Chat Completions：Content 字段](https://platform.kimi.com/docs/api/chat)

上下文缓存支持 5 分钟或 1 小时 TTL，命中条件、用量字段和价格以[上下文缓存](https://platform.kimi.com/docs/guide/context-caching)为准。

## 8. 价格与错误处理

2026-10-13 价格快照（人民币/百万 tokens）：缓存命中输入 ¥1.10、未命中输入 ¥6.50、输出 ¥27.00。价格会变，使用前直接复核[官方价格页](https://platform.kimi.com/docs/pricing/chat)。

对 429 做指数退避，对 5xx 做有限次数重试，对 400 先修请求而不是盲目重试；状态码含义以[官方错误码](https://platform.kimi.com/docs/api/errors)为准。

## 9. 给 Agent 的固定配置

```yaml
provider: kimi
model: kimi-k2.6
base_url: https://api.moonshot.cn/v1
api_key_env: MOONSHOT_API_KEY
thinking_off_extra_body:
  thinking: {type: disabled}
```

这些字段分别来自[快速开始](https://platform.kimi.com/docs/get-api-key)、[K2.6 页面](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart)和[思考模型](https://platform.kimi.com/docs/guide/use-thinking-models)。[历史基础报告](verification/2026-10-13.json)保留当时结果；统一验证器结果查[历史流程状态](../../../docs/验证状态.md)，原始示例的独立执行结果查[逐文件实测状态](../../../docs/示例实测状态.md)。统一验证器复测：`python tests/verify_kimi_k2_6.py --report /tmp/kimi-k2.6-verification.json`；逐文件命令、环境、范围与退出码见[验证与复现](../../../docs/验证与复现.md)。

## 10. 必看踩雷

K2.6 的思考 token 与正文 token 共同受 `max_tokens` 限制；预算太小可能先输出大量 `reasoning_content`，却没有足够空间生成最终答案。多步工具调用时官方建议 `max_tokens >= 16000`。[Kimi 思考模型](https://platform.kimi.com/docs/guide/use-thinking-models) 通用检测代码与更多问题见[真实踩雷与生产检查](../../../docs/06-真实踩雷与生产检查.md)。
