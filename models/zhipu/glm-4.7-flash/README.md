# `glm-4.7-flash` 调用说明书

> 核对日期：**2026-10-13**。官方事实均附原始链接；本次真实请求遇到官方服务 429，未把文档能力冒充成实测通过。机器卡片见 [`glm-4.7-flash.json`](../../../skills/model-manual/references/models/glm-4.7-flash.json)。

## 1. 一眼看懂

| 项目 | 当前值 | 官方来源 |
|---|---|---|
| Model ID | `glm-4.7-flash` | [对话补全 API](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8) |
| Base URL | `https://open.bigmodel.cn/api/paas/v4/` | [OpenAI SDK 兼容](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| 上下文 | 200K tokens | [模型价格](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| 最大输出 | 128K tokens | [对话补全 API](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8) |
| 价格 | 输入、输出均为免费 | [模型价格](https://docs.bigmodel.cn/cn/guide/start/pricing) |

## 2. 最小调用

官方 OpenAI 兼容示例使用 `ZAI_API_KEY`；本仓库为兼容已有总览统一读取 `ZHIPU_API_KEY`，两者只是本地变量名，不会改变认证协议。[OpenAI SDK 兼容](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["ZHIPU_API_KEY"],
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)
response = client.chat.completions.create(
    model="glm-4.7-flash",
    messages=[{"role": "user", "content": "用一句话介绍你自己"}],
)
print(response.choices[0].message.content)
```

可运行文件：[`examples/01_basic.py`](examples/01_basic.py)。请求与响应字段以[对话补全 API](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8)为准。

## 3. 思考与流式输出

GLM-4.7 系列默认开启思考，可用 `thinking.type=disabled` 关闭；思考文本位于 `reasoning_content`。[思考模式](https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode) · [深度思考](https://docs.bigmodel.cn/cn/guide/capabilities/thinking)

```python
response = client.chat.completions.create(
    model="glm-4.7-flash",
    messages=[{"role": "user", "content": "直接回答 1+1"}],
    extra_body={"thinking": {"type": "disabled"}},
)
```

设置 `stream=True` 后逐块读取 `delta.content`；接口字段由[对话补全 API](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8)定义。示例：[`examples/02_streaming.py`](examples/02_streaming.py) · [`examples/03_thinking.py`](examples/03_thinking.py)。

## 4. JSON 与 Tool Calling

JSON 对象模式使用 `response_format={"type":"json_object"}`；工具通过 `tools` 声明，并可使用 `tool_choice` 控制选择。[对话补全 API](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8)

示例：[`examples/04_json_output.py`](examples/04_json_output.py) · [`examples/05_tool_calling.py`](examples/05_tool_calling.py)。应用必须自行校验 JSON 和工具参数，再执行实际函数；这是本仓库安全约定。[来源与核验规则](../../../docs/来源与核验规则.md)

## 5. 当前实测状态

2026-10-13 的验证请求返回 HTTP 429，包括账户速率限制业务码 `1302` 和模型访问量过大业务码 `1305`；这说明请求已到达服务，但不足以证明各能力可用。仓库因此把能力保留为“官方已记录”，不标成“本次实测通过”。详见 [`verification/2026-10-13.json`](verification/2026-10-13.json)。

遇到 429 应使用带抖动的指数退避并限制重试次数；持续限流的结果单独记录，不能判为模型能力不支持。[项目建议与规则](../../../docs/来源与核验规则.md) 使用锁定依赖复测：`python tests/verify_glm_4_7_flash.py --report /tmp/glm-4.7-flash-verification.json`，环境变量和退出码见[验证与复现](../../../docs/验证与复现.md)。最新结果统一查[验证状态](../../../docs/验证状态.md)。

## 6. 给 Agent 的固定配置

```yaml
provider: zhipu
model: glm-4.7-flash
base_url: https://open.bigmodel.cn/api/paas/v4/
api_key_env: ZHIPU_API_KEY
thinking_off_extra_body:
  thinking: {type: disabled}
```

Base URL 与模型参数来自[官方 OpenAI 兼容文档](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction)和[对话补全 API](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8)；运行状态统一查[验证状态](../../../docs/验证状态.md)，不写进固定连接配置。

[工具调用示例](examples/05_tool_calling.py)已经包含校验、模拟执行、结果回传和最终回答的完整有限循环；此处是可运行模板，真实成功状态以[验证状态](../../../docs/验证状态.md)引用的报告为准。

## 7. 必看踩雷

429 不能自动解释成 Key 无效或模型不支持；必须结合 HTTP 状态、业务码和有限重试后的结果分类。本模型的当天证据见[脱敏验证报告](verification/2026-10-13.json)，通用退避与错误分类见[真实踩雷与生产检查](../../../docs/06-真实踩雷与生产检查.md)。
