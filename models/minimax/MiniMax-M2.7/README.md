# `MiniMax-M2.7` 调用说明书

> 资料核对：2026-10-14。仅官方文档收录，**尚未真实调用验证**。机器事实见[型号卡片](../../../skills/model-manual/references/models/MiniMax-M2.7.json)，示例出处与运行方式见[来源清单](examples/sources.json)，跨型号查找见[官方示例索引](../../../docs/官方示例索引.md)。

## 先看生命周期

官方已公告 M2.7 系列退役：**2026-10-19 停止向新用户开放；按量付费 API 于 2026-11-18 正式下线**。M Plan / Token Plan 的 M2.7 请求则从 2026-10-19 起统一路由到 M3.1 Flash Preview，旧名称保留为兼容入口。旧 Model ID 不一定意味着实际服务仍是 M2.7。[官方下线与路由通知](https://platform.minimax.cn/docs/guides/models-intro)

项目约定：按用户指定的准确型号收录，不自动替换成 M3；接入前先核对自己的账户类型与官方通知。生成器会在 stderr 输出生命周期提醒，生成的代码仍使用 `MiniMax-M2.7`。本手册不会用未收录的新型号参数绕过这些限制。[代码生成器](../../../skills/model-manual/scripts/generate_snippet.py)

## 身份与接口

| 项目 | 值 | 官方依据 |
|---|---|---|
| 准确 Model ID | `MiniMax-M2.7`，不是 `MiniMax-M2.7-highspeed` | [Chat API](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| 上下文窗口 | 204,800 tokens | [OpenAI SDK 支持型号](https://platform.minimax.cn/docs/api-reference/text-openai-api) |
| Chat 生成上限参数 | `max_completion_tokens`，至少 1，M2.x 上限 204,800；输入仍受上下文约束，不代表能与最大输入同时用满 | [Chat API 参数](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| OpenAI SDK Base URL | `https://api.minimax.cn/v1` | [官方 SDK 配置](https://platform.minimax.cn/docs/api-reference/text-openai-api) |
| Chat Completions | `POST /v1/chat/completions` | [Chat API](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| 旧原生接口 | `POST /v1/text/chatcompletion_v2`，当前标为 deprecated，但型号列表仍含 M2.7 | [原生文本合成](https://platform.minimax.cn/docs/api-reference/text-post) |

两个路径是不同接口。项目为便于复用现有客户端，使用 Chat Completions 作为默认代码路径；用户提供的旧原生 cURL 单独保留为兼容示例，不把 SDK 的 Base URL 设置成完整的 `/text/chatcompletion_v2`。[官方 SDK](https://platform.minimax.cn/docs/api-reference/text-openai-api) · [旧原生接口](https://platform.minimax.cn/docs/api-reference/text-post)

## 准备环境

在[官方密钥管理](https://platform.minimax.cn/console/access?tab=api-keys)获取对应账户的密钥；Bearer 鉴权定义见[Chat API](https://platform.minimax.cn/docs/api-reference/text-chat-openai)。本仓库约定使用 `MINIMAX_API_KEY`，不将真实 Key 写进示例或报告。[项目来源与安全规则](../../../docs/来源与核验规则.md)

```bash
export MINIMAX_API_KEY='你的新密钥'
python -m pip install -r requirements-lock.txt
python models/minimax/MiniMax-M2.7/examples/01_basic.py
```

Python 示例使用仓库[锁定依赖](../../../requirements-lock.txt)；这不是厂商最低 SDK 版本承诺。运行示例会发送真实请求，离线测试则使用假响应。[验证与复现](../../../docs/验证与复现.md)

## 普通调用与原生 cURL

以下请求使用官方 Chat 格式与输出字段；项目补充了环境变量、超时、思考输出分离和结果检查。完整版本见[01_basic.py](examples/01_basic.py)。[Chat API](https://platform.minimax.cn/docs/api-reference/text-chat-openai)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["MINIMAX_API_KEY"],
    base_url="https://api.minimax.cn/v1",
    timeout=120,
)
response = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[{"role": "user", "content": "你好"}],
    max_completion_tokens=4096,
    extra_body={"reasoning_split": True},
)
base = getattr(response, "base_resp", None)
if base is not None and base.get("status_code") != 0:
    raise RuntimeError("服务端业务状态未成功")
if not response.choices or response.choices[0].finish_reason != "stop":
    raise RuntimeError("没有完整结束的回答")
text = response.choices[0].message.content
if not isinstance(text, str) or not text.strip():
    raise RuntimeError("最终正文为空")
print(text)
```

用户原有的请求地址与预算字段可以在当前官方原生接口文档中核对。下面保留其 `1024` 预算作为对照，不把它当成够用保证；可运行且带响应检查的版本见[原生 cURL](examples/07_native_curl.sh)。[原生参数与弃用标记](https://platform.minimax.cn/docs/api-reference/text-post)

```bash
curl --fail-with-body https://api.minimax.cn/v1/text/chatcompletion_v2 \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-M2.7",
    "messages": [{"role": "user", "content": "你好"}],
    "max_completion_tokens": 1024
  }'
```

原生接口可能同时返回 HTTP 状态和 `base_resp` 业务状态；只拿到 HTTP 200 不代表应用检查已经通过。项目示例还检查 `finish_reason`、空正文和未处理的工具调用。[原生响应字段](https://platform.minimax.cn/docs/api-reference/text-post) · [项目完整性规则](../../../docs/06-真实踩雷与生产检查.md)

## 思考、流式与预算

M2.x 的思考**无法关闭**，传 `thinking.type=disabled` 会被接收但不生效；`reasoning_effort` 对该型号不生效。`reasoning_split=true` 只是把思考分离到 `reasoning_content`，`false` 时思考通过 `<think>` 留在 `content`，两者均不关闭思考。[Chat API 的 M2.x 规则](https://platform.minimax.cn/docs/api-reference/text-chat-openai)

因此项目生成器对 M2.7 的 `--thinking off` 明确报错，不生成“看似关闭”的代码；默认设置 `reasoning_split=true` 便于只发布最终正文。示例预算是项目选择，可按任务调整，不是模型输出长度承诺。[生成参数卡片](../../../skills/model-manual/references/models/MiniMax-M2.7.json)

官方将 `max_tokens` 标为旧参数，建议新接入使用 `max_completion_tokens`；前者在 SDK 页明确包含思考 token，后者目前的字段说明没有同样明确的归属措辞。本项目对 **M2.7 的 `max_completion_tokens` 思考计入语义标为待确认**，不按旧字段或其他厂商外推。[Chat 参数](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [SDK 参数说明](https://platform.minimax.cn/docs/api-reference/text-openai-api)

项目检查：`finish_reason=length`、空最终正文或缺少正常结束信号均不当成成功结果。流式请求的 `stream=true` 与思考分离是两回事；实现需分别处理正文增量、思考增量及无 choices 的用量块。[Chat 流式参数](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [项目踩雷与生产检查](../../../docs/06-真实踩雷与生产检查.md)

## 多轮与工具

工具调用后应回传完整 assistant 消息，包含工具调用和思考字段；不要只复制最终正文或删掉 `<think>` 内容，否则可能破坏连续性。[SDK 的 Function Call 注意事项](https://platform.minimax.cn/docs/api-reference/text-openai-api)

本仓库提供普通多轮与完整工具闭环。工具只返回固定教学模拟天气，不连接真实天气系统；工具名允许列表、整批参数校验、调用 ID 去重和轮次上限属于项目约定。可运行文件及其来源见[示例清单](examples/sources.json)。

## 不套用的能力

| 能力 | 当前收录边界 | 官方依据 |
|---|---|---|
| JSON Mode / JSON Schema | 原生 `response_format` 标为仅 MiniMax-Text-01 支持；当前兼容 Chat 页未登记 M2.7 的该参数，因此不提供声称有格式保证的 JSON 示例 | [原生 API](https://platform.minimax.cn/docs/api-reference/text-post) · [Chat API](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| 原生图片、视频输入 | SDK 多模态段明确列 M3/M3.1，不把这些示例直接套给 M2.7；这里“未收录”不等于所有外部视觉工具都不可用 | [SDK 多模态型号范围](https://platform.minimax.cn/docs/api-reference/text-openai-api) |
| Anthropic / 缓存等进阶路径 | 本批专注 Chat 与用户原生入口；未新增相应依赖和完整流程，不代表厂商不提供 | [官方模型调用入口](https://platform.minimax.cn/docs/guides/text-generation) |

## 价格与排错

费用直接查[官方按量计费](https://platform.minimax.cn/docs/guides/pricing-paygo)，不在本页复制单价；订阅和按量调用的密钥、额度与路由规则分别核对，不能用某类套餐推断另一类 API 可用性。[官方账户与计费规则](https://platform.minimax.cn/docs/guides/pricing-paygo) · [退役通知](https://platform.minimax.cn/docs/guides/models-intro)

项目排查顺序：先核对域名、账户类型、准确 Model ID 与生命周期，再查 HTTP/业务状态、输出预算、完整结束状态及工具历史。通用检查见[真实踩雷](../../../docs/06-真实踩雷与生产检查.md)和[报错速查](../../../docs/05-新手必会与报错速查.md)。

当前没有 M2.7 的真实验证报告，也没有保存任何真实密钥。`verification=null` 与 `verification_scope=not_run` 表示只有官方资料和离线检查，不会借用其他型号的实测通过状态；文件级状态另见[示例来源清单](examples/sources.json)。[证据规则](../../../docs/来源与核验规则.md)
