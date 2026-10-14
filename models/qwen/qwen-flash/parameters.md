# `qwen-flash` 示例参数逐项说明

核对日期：2026-10-14。本页只对应旧型号 `qwen-flash`，不是 Qwen3.5/3.8-Flash。官方事实就近链接，项目取值直接链接源码；“项目建议”不代表官方性能保证。实际调用结果另查[示例实测状态](../../../docs/示例实测状态.md)，参数释义本身不是实测报告。

## 1. 按文件找参数

所有文件共有 `model="qwen-flash"`、`messages` 及后文所述连接选项；下表列额外请求字段。未出现的字段表示未显式发送，不应擅自补成其他型号的默认值。

| 文件 | 显式请求字段与本例取值 | 输入、历史和项目约定 |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | 无额外字段 | 单条 user 文本；未指定思考开关，旧 Qwen-Flash 默认不开启。默认依据：[深度思考支持表](https://help.aliyun.com/zh/model-studio/deep-thinking)。 |
| [02_streaming.py](examples/02_streaming.py) | `stream=True`；`enable_thinking=False` | 普通文本增量；没有发送 `stream_options.include_usage`，只记录实际收到的 usage。 |
| [03_thinking.py](examples/03_thinking.py) | `enable_thinking=True` | 非流式返回；分别读取 `reasoning_content` 和最终 `content`，未设显式 token 预算。 |
| [04_json_output.py](examples/04_json_output.py) | `response_format.type="json_object"`；关闭思考 | 提示词要求 `{"ok":true}`；本地检查对象恰好一个字段且 `ok is True`。 |
| [05_tool_calling.py](examples/05_tool_calling.py) | `tools` 定义 `get_weather(city)`；关闭思考 | 没有显式 `tool_choice`；整批参数校验后执行模拟天气，最多六次模型调用，完整回传 assistant/tool。 |
| [06_multi_turn.py](examples/06_multi_turn.py) | 关闭思考；`max_tokens=1024` | 每次发送文本历史；历史 assistant 只保留正文；客户端另设 `max_retries=0`。 |
| [07_thinking_tools.py](examples/07_thinking_tools.py) | `tools` 定义 `get_inventory(sku)`；`tool_choice="auto"`；开启思考；`max_tokens=8192` | 完整保留当前工具循环的 assistant；本地最多四次模型调用，至少执行一次模拟库存工具才算闭环；客户端 `max_retries=0`。 |

“开启/关闭思考”的 Python 写法为 `extra_body={"enable_thinking": True/False}`。它合并成 HTTP JSON 顶层 `enable_thinking`；不要把字符串 `"false"` 当布尔值，也不要把 Kimi 的 `thinking.keep` 换个名字直接套入。[OpenAI 兼容接口：扩展字段放置](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)

## 2. 连接配置与地域

| 字段 | 本例取值、默认与作用 | 出处 |
|---|---|---|
| `api_key` | 从 `DASHSCOPE_API_KEY` 读取，供鉴权而非模型生成使用。不要把 Key 写进提示词或源码。 | [官方首次调用](https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen)；各示例源码 |
| `base_url` | 示例为北京兼容地址 `https://dashscope.aliyuncs.com/compatible-mode/v1`；官方目前推荐控制台提供的 Workspace 专属地址。Key 与地域应对应。 | [OpenAI 兼容接口：地址](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) |
| `timeout=120` | 所有文件显式设置的 SDK 超时秒数，不是 `max_tokens`，也不是完整多轮任务的总时限。 | [SDK：Timeouts](https://developers.openai.com/api/reference/python#timeouts)；各示例源码 |
| `max_retries` | 06/07 显式为 `0`，便于暴露本次请求失败；01–05 未覆盖 SDK 默认设置。官方 SDK 默认对特定连接/状态错误重试两次。 | [SDK：Retries](https://developers.openai.com/api/reference/python#retries)；[06](examples/06_multi_turn.py)、[07](examples/07_thinking_tools.py) |
| `extra_body` | Python SDK 扩展参数入口，不是百炼服务端模型字段；直接 HTTP 或接口文档中的 Node.js 写法可把扩展字段放在请求体顶层。 | [兼容接口：enable_thinking](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)；[SDK：额外请求参数](https://developers.openai.com/api/reference/python#undocumented-request-params) |

官方旧型号专页把北京的 Function Calling 标为支持，而新加坡、法兰克福和美国对应表为不支持；不能只改地域地址就认定 05/07 仍具备相同工具能力。本目录示例没有声称覆盖这些部署。[qwen-flash：分地域能力表](https://help.aliyun.com/zh/model-studio/qwen-flash)

SDK 文档只用于解释客户端机制，不代表 OpenAI 支持本型号能力；实际依赖版本见 [requirements-lock.txt](../../../requirements-lock.txt)。项目建议：对有真实副作用的工具，另设应用总时限、重试预算和幂等边界；SDK 重试次数不等于模型工具循环次数。

## 3. 型号、上下文与 token 预算

| 字段/限制 | 旧 `qwen-flash` 的具体含义 | 出处 |
|---|---|---|
| `model` | 当前 `qwen-flash` 功能等同 `qwen-flash-2025-07-28`，不是较新一代 Flash。 | [旧型号专页](https://help.aliyun.com/zh/model-studio/qwen-flash) |
| 输入/输出模态 | 文本输入、文本输出；本目录没有 `image_url`、视频或音频示例。兼容 API 中存在这些字段，不等于这个型号支持。 | [旧型号专页：模态表](https://help.aliyun.com/zh/model-studio/qwen-flash) |
| 上下文/输入/输出上限 | 官方分别列 1000000 / 997952 / 32768 tokens。上下文不是“可输出一百万 token”，输入和输出也不是可以同时各自任意占满的独立容量。 | [旧型号专页：上下文限制](https://help.aliyun.com/zh/model-studio/qwen-flash) |
| `max_tokens` | 对本型号限制**回答正文，不包含思维链**；接口说明其默认值和最大值为型号最大输出长度，即本页已确认的 32768。06 用 1024，07 用 8192，是项目预算，不是推荐值或新上限。 | [兼容接口：max_tokens 的“其他模型”分支](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)；[型号输出上限](https://help.aliyun.com/zh/model-studio/qwen-flash)；[06](examples/06_multi_turn.py)、[07](examples/07_thinking_tools.py) |
| `max_completion_tokens` | 官方定义为思考+回答总预算，但 Flash 的支持列表从 Qwen3.5-Flash 开始；**不能**因文档建议新代码使用它，就给旧 `qwen-flash` 自动替换。 | [兼容接口：支持型号](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) |
| `thinking_budget` | 用于限制思考长度，接口列出 Qwen3 支持；当前七个文件都没传。旧 `qwen-flash` 的独立思考硬上限本次未在型号专页明确确认，记为未知，不能用正文 32768 或新版 Flash 数字代替。 | [深度思考：限制思考长度](https://help.aliyun.com/zh/model-studio/deep-thinking)；[旧型号规格的已列范围](https://help.aliyun.com/zh/model-studio/qwen-flash) |

项目建议：对 07 增大 `max_tokens` 只是在增加正文预算，不能据此声称限制了思考耗时或思考 token；仍须校验 `finish_reason` 与最终非空正文。[07 的结束检查](examples/07_thinking_tools.py)

## 4. 思考、温度和核采样

| 参数 | 默认、范围、模式及副作用 | 出处 |
|---|---|---|
| `enable_thinking` | 布尔值；旧 Qwen-Flash 是混合思考型号，默认 `False`。`True` 时思考内容返回在 `reasoning_content`；03/07 开启，其他扩展示例显式关闭。商业版 Qwen-Flash 可非流式思考，不能套用某些开源型号“只能流式”的限制。 | [深度思考：Qwen3 支持与同步调用](https://help.aliyun.com/zh/model-studio/deep-thinking) |
| `temperature` | 范围 `[0,2)`；非思考默认 0.7，Qwen3 思考模式默认 0.6。较大更发散、较小更确定，当前示例全部省略。 | [兼容接口：temperature](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)；旧型号属于 Qwen3 的依据：[型号页](https://help.aliyun.com/zh/model-studio/qwen-flash) |
| `top_p` | 范围 `(0,1]`；本型号非思考默认 0.8，Qwen3 思考默认 0.95；控制核采样候选概率范围，当前示例全部省略。官方建议与 `temperature` 只调一个。 | [兼容接口：top_p](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) |
| `preserve_thinking` | 当前官方支持列表包括较新 Qwen3.6/3.7/3.8 等型号，未列旧 `qwen-flash`；本目录不发送，不用新版默认补到旧型号。 | [兼容接口：preserve_thinking](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) |
| 跨用户轮的历史思考 | 06 关闭思考、历史只存正文；官方普通多轮思考示例也区分 `content` 与 `reasoning_content`。07 完整回传当前工具闭环的 assistant，不声称为旧型号开启了“跨轮保留思考”功能。 | [多轮对话](https://help.aliyun.com/zh/model-studio/multi-round-conversation)；[06](examples/06_multi_turn.py)、[07](examples/07_thinking_tools.py) |

项目建议：写作/创意任务可以做单变量温度对照；提取/代码任务可先保持默认，并以可执行测试/Schema/原文核验评价结果。**更确定不等于更准确**，本仓库不提供“温度越低事实正确率越高”的保证。采样的官方定义只描述多样性与确定性，见[temperature/top_p](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)。

## 5. 消息、流式和返回字段

| 字段 | 用途及示例注意点 | 出处 |
|---|---|---|
| `messages[].role` / `content` | 本例使用 system/user/assistant/tool；文本 `content` 是字符串。每次请求带上需要的历史，SDK client 本身不代管会话。 | [多轮对话](https://help.aliyun.com/zh/model-studio/multi-round-conversation)；[Function Calling 消息流程](https://help.aliyun.com/zh/model-studio/qwen-function-calling) |
| `stream` | 默认 `False`；02 为 `True`，读取增量 `delta` 而不是完整 `message`。03/07 是非流式思考，返回完整正文/思考。 | [流式输出](https://help.aliyun.com/zh/model-studio/stream)；[深度思考同步调用](https://help.aliyun.com/zh/model-studio/deep-thinking) |
| `stream_options.include_usage` | 默认 `False`；开启后在流末块返回统计。仅流式时使用；当前 02 未发送，不能把缺失 usage 解释成零消耗。 | [兼容接口：stream_options](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)；[02](examples/02_streaming.py) |
| `usage` | 响应中的 prompt/completion/total token 统计，可能有思考/缓存明细；按服务端实际字段记录，不是请求的“用量上限”。 | [深度思考：用量统计](https://help.aliyun.com/zh/model-studio/deep-thinking)；[兼容接口：usage](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) |
| `finish_reason` | `stop` 为正常停止，`length` 为达到长度限制，`tool_calls` 表示工具阶段；返回思考或部分 JSON 不等于最终成功。项目代码还检查空 choices、空正文和未处理工具；02 检查终止标记而不把自然断流当成功。 | [兼容接口：响应格式](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)；[02](examples/02_streaming.py)、[07](examples/07_thinking_tools.py) |

## 6. 工具与结构化输出的每层字段

| 字段 | 用途、限制及本例约定 | 出处 |
|---|---|---|
| `tools[].type="function"` | 声明函数工具；模型给出调用请求，真正执行的是应用。05/07 只调用本地模拟函数，不查真实天气/库存。 | [Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling)；[05](examples/05_tool_calling.py)、[07](examples/07_thinking_tools.py) |
| `function.name` / `description` | 名称用于路由到本地白名单，描述告诉模型何时使用；本例是 `get_weather` 与 `get_inventory`。 | [Function Calling：工具定义](https://help.aliyun.com/zh/model-studio/qwen-function-calling)；[05](examples/05_tool_calling.py)、[07](examples/07_thinking_tools.py) |
| `function.parameters` | JSON Schema 对象：`type="object"`、`properties` 声明 city/sku 的 `string` 类型、`required` 必填、`additionalProperties=False` 禁额外字段。本例未发送工具级 `strict`，返回参数必须再做本地验证。 | [Function Calling：工具参数](https://help.aliyun.com/zh/model-studio/qwen-function-calling)；[05](examples/05_tool_calling.py)、[07](examples/07_thinking_tools.py) |
| `tool_choice` | 有工具时默认自动选择；07 显式 `auto`，也可按官方形式禁用或指定函数。Qwen 当前不支持可靠的 `required` 语义，思考模式不支持该值；不能靠它保证旧型号执行工具。 | [Function Calling：控制调用策略](https://help.aliyun.com/zh/model-studio/qwen-function-calling) |
| `tool_calls[].function.arguments` / `id` | 参数是待解析 JSON 字符串；先整批校验，再执行。把完整 assistant 追加到历史，并通过 `role="tool"`、对应 `tool_call_id` 与字符串 `content` 回传结果。 | [Function Calling：完整流程](https://help.aliyun.com/zh/model-studio/qwen-function-calling)；[07](examples/07_thinking_tools.py) |
| `response_format` | 默认文本；04 设置 `{"type":"json_object"}`，且提示词包含 JSON 要求。旧 Qwen-Flash 的 JSON Mode 仅支持**非思考**，所以同时关闭思考。 | [结构化输出：JSON Object 支持表](https://help.aliyun.com/zh/model-studio/qwen-structured-output)；[04](examples/04_json_output.py) |
| JSON Schema / `strict` | 当前 JSON Schema 支持表未列旧 `qwen-flash`；不把新版 `json_schema`/`strict=True` 请求搬到 04。JSON 对象模式只解决格式，`ok` 的字段/布尔值约束由项目代码验证。 | [结构化输出：分模式支持范围](https://help.aliyun.com/zh/model-studio/qwen-structured-output)；[04](examples/04_json_output.py) |

城市 1–80 字、只接受 `SKU-001`、固定库存 7、四/六次调用上限、拒绝重复工具 ID、必须实际执行过工具，是[05](examples/05_tool_calling.py)/[07](examples/07_thinking_tools.py) 的业务/安全约定，不是官方参数默认或范围。`additionalProperties=False` 不能代替工具白名单、JSON 类型检查和真实系统的授权校验。

## 7. 不从同名兼容字段推导能力

本型号只用文本。Kimi 的 `data:video/mp4;base64`、其他 Qwen 视觉型号的 `image_url`/`video`、新版 `preserve_thinking`、`max_completion_tokens` 和严格 JSON Schema 都需要分别核对具体型号支持，不能因为 SDK 能序列化就认为服务器支持。[旧 Qwen-Flash 规格](https://help.aliyun.com/zh/model-studio/qwen-flash)；[结构化输出范围](https://help.aliyun.com/zh/model-studio/qwen-structured-output)；[兼容接口的逐型号参数范围](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)
