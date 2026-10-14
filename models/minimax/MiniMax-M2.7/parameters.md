# `MiniMax-M2.7` 示例参数说明

[English](parameters.en.md) · [人类篇](../../../human/README.md)

资料核对：2026-10-14。本页只解释 **M2.7 托管 API** 与本目录现有文件，不将 M3 / M3.1 的视觉、思考深度或其他新参数移植到 M2.7。参数出处不等于调用成功证据；文件级验证范围另查[来源清单](examples/sources.json)。

调用前先核对生命周期：官方已公告 M2.7 系列于 2026-10-19 停止向新用户开放，按量 API 于 2026-11-18 下线；M Plan / Token Plan 的旧名称从 2026-10-19 起路由至 M3.1 Flash Preview。因此，旧 Model ID 不能证明实际仍运行旧型号。本页不自动替换用户指定的 M2.7。[官方生命周期通知](https://platform.minimax.cn/docs/guides/models-intro)

快速定位：[身份与消息](#identity) · [采样](#sampling) · [预算](#budget) · [思考](#thinking) · [流式](#streaming) · [工具](#tools) · [未确认功能](#boundaries) · [原生接口](#native) · [SDK 与本地检查](#sdk) · [逐文件对照](#example-map)。

<a id="identity"></a>
## 1. 接口身份与消息

| 字段或配置 | 说明 | 官方依据 |
|---|---|---|
| `model="MiniMax-M2.7"` | 准确型号 ID，不是 highspeed，也不是 M3；本目录全部示例固定此值。 | [兼容 Chat 型号列表](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| `base_url="https://api.minimax.cn/v1"` | 国区 OpenAI SDK 根地址；Chat 路径为 `/v1/chat/completions`。不能把完整原生路径塞进 SDK Base URL。 | [官方 SDK 配置](https://platform.minimax.cn/docs/api-reference/text-openai-api) |
| `api_key` / Bearer 请求头 | 鉴权，不是消息内容。本仓库环境变量名 `MINIMAX_API_KEY` 是项目约定。 | [Chat 鉴权](https://platform.minimax.cn/docs/api-reference/text-chat-openai)；[01 源码](examples/01_basic.py) |
| `messages` | 有序对话历史，本目录只发送文本和工具消息。 | [Chat messages](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |

本例角色分工：`system` 放要求，`user` 放问题，`assistant` 保留模型返回，`tool` 回传函数结果并用 `tool_call_id` 配对。06 发送累积历史，05 保留完整 assistant 对象，不仅仅回传 `content`。这是项目的请求实现，完整回传要求也明确覆盖官方 SDK 列出的 M2.7。[05](examples/05_tool_calling.py)；[06](examples/06_multi_turn.py)；[官方完整历史要求](https://platform.minimax.cn/docs/api-reference/text-openai-api)

国际站另有 `https://api.minimax.io/v1` 配置；本目录选择国区，不声称同一密钥跨区可用，也不声称历史 `api.minimaxi.com` 域名的当前兼容性。[国际站官方配置](https://platform.minimax.io/docs/api-reference/text-openai-api)

<a id="sampling"></a>
## 2. 采样：发散程度，不是准确率旋钮

| 参数 | 兼容 Chat 的 M2.7 语义 | 官方依据 |
|---|---|---|
| `temperature` | 随机性系数，范围 `[0, 2]`、默认 `1`；高一些更随机，低一些更确定。 | [Chat temperature](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |
| `top_p` | 核采样阈值，范围 `[0, 1]`；M2.x 默认 `0.9`，不是该页 M3 系列的 `0.95`。 | [Chat top_p](https://platform.minimax.cn/docs/api-reference/text-chat-openai) |

概念区别：温度调节采样的随机性尺度，核采样用累计概率筛选候选 token；核采样的具体概念可参阅[官方采样定义](https://api-docs.deepseek.com/api/create-chat-completion/)，此链接**仅解释概念，不借用 DeepSeek 的取值或开关规则**。上述 MiniMax 范围仍以 MiniMax 官方定义为准。

项目阅读建议：由“随机性”不能推导“温度越高事实越正确”或“越低越不会编造”。本目录不显式设置这两个参数；也没有官方依据宣称 M2.7 开启思考时会忽略它们，不能照搬 DeepSeek 的限制。原生接口的范围还不同，见[第 8 节](#native)。

<a id="budget"></a>
## 3. 上下文窗口与生成预算

M2.7 上下文窗口是 **204,800 tokens**，是型号规格，不是 `max_completion_tokens` 的别名；不要据此认为最大输入与最大输出可以同时用满。[官方型号窗口](https://platform.minimax.cn/docs/api-reference/text-openai-api)

| 参数 | 已确认的定义 | 不应推断的内容 |
|---|---|---|
| `max_completion_tokens` | 兼容 Chat 生成长度上限，整数至少 `1`；M2.x 上限 `204800`、推荐值 `65536`。达到限制可能 `length`，应调整预算并重新核对结束状态。 | 上限不是默认值，不保证等长正文；当前说明没有明确 M2.7 新字段中思考与正文的精确计入等式，记为**未知**。 |
| `max_tokens` | 旧字段，已弃用；官方 SDK 文档明确旧字段的预算包含思考 token，过小可能 length 且正文为空。 | 不将旧字段的明确表述直接当成新字段 `max_completion_tokens` 的已确认事实，也不拿 M3 的说明补齐 M2.7。 |

字段范围见 [Chat 预算参数](https://platform.minimax.cn/docs/api-reference/text-chat-openai)，旧字段的思考预算说明见 [SDK 参数表](https://platform.minimax.cn/docs/api-reference/text-openai-api)。官方未在当前页面明确 M2.7 新字段默认值，本页不填猜测值。

本目录六个可运行文件都主动使用 `max_completion_tokens=16384`，这是**项目演示预算**，不是官方默认或“任何任务都够”的承诺；README 里的短片段也可能选更小预算，应以所运行文件为准。[01](examples/01_basic.py)；[02](examples/02_streaming.py)；[03](examples/03_thinking.py)；[05](examples/05_tool_calling.py)；[06](examples/06_multi_turn.py)；[07](examples/07_native_curl.sh)

<a id="thinking"></a>
## 4. 思考开关、深度与返回格式

| 字段 | M2.7 的适用边界 |
|---|---|
| `thinking.type` | M2.x 思考无法关闭；`adaptive` 是默认行为，传 `disabled` 被接收但不生效。本目录没有发送伪“关闭”配置。 |
| `reasoning_effort` | 当前只有 M3.1 Flash Preview 真正支持深度调节，其他型号忽略。因此 M2.7 示例不设置它，不提供伪“low / high 档位”教程。 |
| `reasoning_split=True` | **输出格式**开关，把思考拆到 `reasoning_content`；不是关闭思考。false 时思考可能在 `content` 的 `<think>…</think>` 中。Python 示例通过 extra_body 发送 true；原生示例未发送。 |

以上边界来自 [Chat thinking / reasoning_effort / reasoning_split](https://platform.minimax.cn/docs/api-reference/text-chat-openai)。不要把页面开头的 M3.1 示例直接改个 model 就宣称 M2.7 支持所有参数。

显示答案时，示例可以去掉开头完整 `<think>` 段，检查是否还有正文；但工具历史里必须保留原始 assistant（含思考和 tool_calls），不能把“显示用正文”覆盖历史。03 仅在响应确实包含 `reasoning_content` 时展示它；没有该字段不等于没有思考。[官方完整回传说明](https://platform.minimax.cn/docs/api-reference/text-openai-api)；[03 源码](examples/03_thinking.py)；[05 源码](examples/05_tool_calling.py)

<a id="streaming"></a>
## 5. 流式、用量与成功判断

`stream=True` 让响应分批返回；02 还设置 `stream_options={"include_usage":True}` 请求流式 token 用量。它们控制传输和统计，不替代输出预算或思考开关。[官方 stream 定义](https://platform.minimax.cn/docs/api-reference/text-chat-openai)；[include_usage 说明](https://platform.minimax.cn/docs/api-reference/text-openai-api)

`usage`、`finish_reason`、`base_resp` 是**响应字段**，不是向模型发送的参数。官方返回业务状态、用量及敏感状态；HTTP 200 本身不能代替对正文和结束状态的检查。[官方响应字段](https://platform.minimax.cn/docs/api-reference/text-chat-openai)

项目验收策略：02 容忍没有 choice 的统计块并收集 usage，但必须看到 `stop`、存在非空最终正文；无结束标记、length、异常工具 delta、重复或结束后继续生成等都报错。普通示例还检查可用的业务状态，原生 07 要求 `base_resp.status_code=0`。这些是本地防护，不宣称厂商一定会产生每一种防御性分支。[02](examples/02_streaming.py)；[01](examples/01_basic.py)；[07](examples/07_native_curl.sh)

<a id="tools"></a>
## 6. 工具调用参数与完整闭环

官方兼容 Chat 支持 `tools` 的 function 工具；完整 assistant 历史需要保留，此要求包含 M2.7。[Chat tools](https://platform.minimax.cn/docs/api-reference/text-chat-openai)；[SDK 的多轮工具注意事项](https://platform.minimax.cn/docs/api-reference/text-openai-api)

05 中的以下结构是项目具体工具定义，不是 MiniMax 预置天气接口：[05 源码](examples/05_tool_calling.py)

| 字段 | 本例作用 |
|---|---|
| `tools[].type="function"` | 声明函数型工具；实际执行由本地程序完成。 |
| `function.name="get_weather"` / `description` | 名称用于本地白名单路由，描述帮助模型选择；没有授予任意代码执行能力。 |
| `function.parameters.type="object"` | 参数是 JSON 对象；`properties.city.type="string"` 定义城市字符串。 |
| `required=["city"]` / `additionalProperties=False` | 声明 city 必填、不要额外键；本地仍自行检查，不声称服务端已按 strict 保证 Schema。 |
| 返回 `function.arguments` | 由模型产生的 JSON 字符串，先解析与验证，不能当成代码执行。 |
| `role="tool"` / `tool_call_id` / `content` | 把模拟执行结果送回模型，ID 必须对应原始调用，之后取得最终答案。 |

05 **未显式传 `tool_choice`，也未传 `strict`**。当前兼容 Chat 文档不足以在这里承诺 M2.7 的 forced/named tool choice 或 strict 服务端约束；原生接口单独列出 `none` / `auto`，不据此推导兼容接口支持其他取值。[兼容 Chat 参数表](https://platform.minimax.cn/docs/api-reference/text-chat-openai)；[原生 tool_choice](https://platform.minimax.cn/docs/api-reference/text-post)

项目约定：天气为模拟固定数据，无真实天气网络请求；每轮先校验整批调用，限制名称、唯一 ID、JSON 对象、city 类型与 1–80 字符长度；最多 6 次模型轮次，且必须实际执行过工具才能算完成闭环。`max_model_turns`、执行计数、城市限制是本地控制，不发送给 MiniMax。真实模型调用加模拟工具，不等于工具数据也是真实天气。[05 源码](examples/05_tool_calling.py)

<a id="boundaries"></a>
## 7. 未确认的组合：不要靠字段名猜支持

| 功能或字段 | 当前 M2.7 收录结论 | 官方边界 |
|---|---|---|
| `response_format` / JSON Schema | 不提供 04 JSON 示例；提示词要求 JSON 不等于协议保证。 | [旧原生文档](https://platform.minimax.cn/docs/api-reference/text-post)明确该参数只支持 MiniMax-Text-01；[当前兼容 Chat 参数](https://platform.minimax.cn/docs/api-reference/text-chat-openai)未确认 M2.7 JSON 模式。 |
| 图片 `image_url`、视频、`detail`、Files 多模态引用 | 不向 M2.7 添加这些字段。 | [官方 SDK 多模态章节](https://platform.minimax.cn/docs/api-reference/text-openai-api)明确限定 M3 / M3.1，不能用其 detail 或文件大小参数描述 M2.7。 |
| Responses、FIM、DeepSeek 的 `prefix` / Beta strict | 本型号未收录，不能直接复用 DeepSeek 的接口或 Base URL。 | 当前收录依据为 [MiniMax 兼容 Chat](https://platform.minimax.cn/docs/api-reference/text-chat-openai)与[旧原生 Chat](https://platform.minimax.cn/docs/api-reference/text-post)，均不足以确认这些组合。 |

<a id="native"></a>
## 8. 原生 cURL 与兼容 Chat 不能混成一套参数

07 请求的是 `https://api.minimax.cn/v1/text/chatcompletion_v2`。官方当前仍列出 M2.7 与 `max_completion_tokens`，同时将接口标为 deprecated；文档列出不构成所有账户此刻均可用的实测证明。它不是 SDK 的 `/v1/chat/completions`。[官方原生端点](https://platform.minimax.cn/docs/api-reference/text-post)

07 的 HTTP 请求头为 Bearer 鉴权及 `Content-Type: application/json`，JSON 只发送 `model`、user `messages`、`max_completion_tokens=16384`；不发送兼容示例的 reasoning_split。本例参数来源见[原生请求定义](https://platform.minimax.cn/docs/api-reference/text-post)，实际值见[07 源码](examples/07_native_curl.sh)。

原生文档的采样范围是 `temperature ∈ (0,1]`、`top_p ∈ (0,1]`，与兼容 Chat 的范围不同；其旧默认值表没有明确 M2.7，不拿 M2 的旧默认值补齐。原生 max_completion_tokens 当前仅明确至少 1，本页不从另一端点补出它未明写的 M2.7 范围。07 不设置采样参数。[原生采样与预算字段](https://platform.minimax.cn/docs/api-reference/text-post)

<a id="sdk"></a>
## 9. SDK 配置与本地安全参数

| 名称 | 所属层与解释 |
|---|---|
| `timeout=120` | Python SDK 网络超时配置，单位秒；不是生成上限，也不保证整个多轮工具任务 120 秒内完成。 |
| `max_retries` | SDK 自动重试配置，`0` 可禁用；现有 Python 示例未显式设置。它与工具循环次数不同，不发送到模型。 |
| `extra_body={"reasoning_split":True}` | SDK 扩展 JSON 请求体的方法；实际服务端收到顶层 reasoning_split，不会收到名为 extra_body 的模型开关。 |
| cURL `--max-time 180` | 本地传输限时，单位秒；与 token 预算不同。`--fail` 检查 HTTP 错误，仍需后续检查业务状态。 |
| `max_model_turns` / city 校验 / display_text | 项目本地循环、输入和展示控制；不是可复制进 HTTP JSON 的服务端参数。 |

SDK 配置依据 [OpenAI Python：超时、重试与扩展字段](https://developers.openai.com/api/reference/python)，cURL 依据 [curl 官方手册](https://curl.se/docs/manpage.html)。本例值与检查逻辑见[01](examples/01_basic.py)、[05](examples/05_tool_calling.py)、[07](examples/07_native_curl.sh)。SDK 允许扩展字段不代表厂商支持它，厂商能力须回到 MiniMax 官方文档确认。

<a id="example-map"></a>
## 10. 每个可运行文件的实际请求对照

Python 文件公共配置均为环境变量 Key、国区 Base URL、`timeout=120`；公共参数均为 `model="MiniMax-M2.7"` 与 `max_completion_tokens=16384`。每行文件链接是具体项目配置的来源，官方含义见对应章节。

| 可运行文件 | 额外实际输入与行为 | 参数解释 |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | user `messages`、`extra_body.reasoning_split=True`；最终正文检查 | [消息](#identity)、[预算](#budget)、[思考格式](#thinking)、[SDK](#sdk) |
| [02_streaming.py](examples/02_streaming.py) | user `messages`、reasoning_split true、`stream=True`、`stream_options.include_usage=True` | [流式与用量](#streaming)、[预算](#budget)、[思考](#thinking) |
| [03_thinking.py](examples/03_thinking.py) | user `messages`、reasoning_split true；未传 thinking 或 reasoning_effort | [M2.7 思考限制](#thinking)、[预算](#budget) |
| [05_tool_calling.py](examples/05_tool_calling.py) | system/user/完整 assistant/tool `messages`、`tools`、reasoning_split true；未传 tool_choice / strict | [工具定义、回传与本地限制](#tools)、[思考格式](#thinking) |
| [06_multi_turn.py](examples/06_multi_turn.py) | 累积 system/user/完整 assistant 历史、reasoning_split true | [消息历史](#identity)、[思考历史](#thinking) |
| [07_native_curl.sh](examples/07_native_curl.sh) | 原生 POST 路径，Bearer/JSON 请求头；user messages；不传 reasoning_split；`--max-time 180` | [原生端点与差异](#native)、[本地传输参数](#sdk) |

缺失的 04 不是漏写，见[未确认功能](#boundaries)；新增功能前应先确认**此型号 + 此端点**的官方支持，再添加文件与验证证据。
