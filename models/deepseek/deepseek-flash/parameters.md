# `deepseek-flash` 示例参数说明

资料核对：2026-10-14。本页解释本目录实际示例，不把“SDK 能传这个字段”当成“DeepSeek 支持这个功能”。官方事实逐项附链接；标为“项目约定”的内容来自链接的示例代码。文件级运行证据另见[来源与验证清单](examples/sources.json)，参数释义本身不是实测报告。

快速定位：[身份与消息](#identity) · [采样](#sampling) · [预算与思考](#budget) · [流式](#streaming) · [工具](#tools) · [JSON](#json) · [图片与文件](#vision-files) · [Responses](#responses) · [Beta / FIM](#beta) · [SDK 与本地检查](#sdk) · [逐文件对照](#example-map)。

<a id="identity"></a>
## 1. 接口身份与消息

| 字段或配置 | 含义与本目录用法 | 官方依据 |
|---|---|---|
| `model="deepseek-flash"` | 请求的模型 ID；当前对应 DeepSeek-V4.1-Flash，不应把旧名称等同于旧权重版本。 | [模型与版本](https://api-docs.deepseek.com/quick_start/pricing/) |
| `base_url` | 普通示例使用 `https://api.deepseek.com`，不是 OpenAI 自家的服务地址；Beta 示例另见后文。 | [首次调用](https://api-docs.deepseek.com/quick_start/pricing-details-cny/) |
| `api_key` / `Authorization: Bearer …` | 鉴权配置，不是提示词或模型参数。本目录从 `DEEPSEEK_API_KEY` 读取，是项目的环境变量命名约定。 | [首次调用](https://api-docs.deepseek.com/quick_start/pricing-details-cny/)；[01 源码](examples/01_basic.py) |
| `messages` | Chat 接口的有序对话历史，至少一条；`content` 是文本，图片场景则是内容块数组。 | [Chat 请求结构](https://api-docs.deepseek.com/api/create-chat-completion/) |

`role` 不只是展示标签：`system` 放系统要求，`user` 放用户输入，`assistant` 放模型先前返回，`tool` 放程序执行工具后的结果。工具结果用 `tool_call_id` 对应模型返回的调用 ID，而不是重新编一个 ID。对应字段见 [Chat 消息定义](https://api-docs.deepseek.com/api/create-chat-completion/)。

Chat 接口不替客户端保存历史；多轮时每次重新发送已有消息。09 示例只在回答完整后追加 assistant，避免把失败或截断结果当成已完成历史。这是官方多轮模式加上项目的校验策略。[官方多轮说明](https://api-docs.deepseek.com/guides/multi_round_chat/)；[09 源码](examples/09_multi_turn.py)

<a id="sampling"></a>
## 2. `temperature` 与 `top_p`：多样性不等于准确率

| 参数 | 调节什么 | 本型号限制 |
|---|---|---|
| `temperature` | 改变采样随机性；较高更发散，较低更集中，不是“正确率百分比”。 | 范围 `[0, 2]`、默认 `1`；思考模式下不生效。 |
| `top_p` | 核采样：按累计概率保留候选 token，而不是像温度那样调节随机性的尺度。 | 传入范围 `(0, 1]`、默认 `1`；仅思考模式生效，实际范围 `[0.95, 1]`，更低值按 `0.95`；非思考模式固定 `1`、忽略传值。 |

这些是 DeepSeek 当前协议，不能推成所有厂商的通用规则。官方建议通常只调整两者之一；本目录示例都没有显式设置它们。[Chat 采样参数](https://api-docs.deepseek.com/api/create-chat-completion/)；[思考模式参数限制](https://api-docs.deepseek.com/guides/thinking_mode/)

项目阅读建议：由“随机性”定义只能推得答案的多样程度变化，不能推得提高温度就更准确、降低温度就不会编造。需要确定答案时仍应验证结果，而非把采样参数当成事实校验器。

<a id="budget"></a>
## 3. 上下文、输出预算与思考

| 名称 | 意义、范围与区别 | 官方依据 |
|---|---|---|
| 型号上下文 `1M` | 型号容纳输入与输出的窗口，不是一个应写成 `max_tokens=1000000` 的请求参数。 | [型号规格](https://api-docs.deepseek.com/quick_start/pricing/)；[上下文字段定义](https://api-docs.deepseek.com/api/list-models/) |
| Chat `max_tokens` | 本次生成 token 上限，`1..393216`；输入与生成总长仍受上下文限制。省略时，非思考默认 `8192`，思考默认 `65536`，`reasoning_effort="max"` 时默认 `131072`。 | [Chat 输出预算](https://api-docs.deepseek.com/api/create-chat-completion/) |
| `thinking.type` | `enabled` 开启、`disabled` 关闭；默认开启。因此 01、07、08 没传开关不等于关闭思考。 | [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/) |
| Chat `reasoning_effort` | `none` 关闭；`low` / `high` / `max` 开启并选择思考强度，默认 `high`。03 明确使用 `high`，不同时传互相冲突的开关。 | [Chat 思考配置](https://api-docs.deepseek.com/api/create-chat-completion/)；[03 源码](examples/03_thinking.py) |
| `reasoning_content` | 返回的思考文本，与最终 `content` 分开；它是响应字段，思考工具历史中也需要回传，并非另一个输出预算参数。 | [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/) |

预算是否包含思考必须按接口区分：Chat 的 `usage.completion_tokens_details.reasoning_tokens` 是生成用量的细分，不能把 `completion_tokens` 当成最终正文长度；但当前 Chat `max_tokens` 字段没有像 Responses 那样明确写出“可见输出 + 思考”的预算等式，本页将其精确计入语义记为**未明确确认**。Responses 的 `max_output_tokens` 则明确包含两者，见[第 8 节](#responses)。[Chat 用量与字段定义](https://api-docs.deepseek.com/api/create-chat-completion/)；[Responses 预算定义](https://api-docs.deepseek.com/api/create-response/)

项目示例预算不是服务端默认或型号极限：12 思考工具使用 `16384`；13 非思考严格工具使用 `2048`；14 前缀续写使用 `1024`；15 FIM 使用 `128`；11 Responses 使用 `2048`。其余 Chat 示例没有显式设置预算。调整时需结合任务长度，并检查结束状态，不保证“设成某个值就一定够”。[共享工具实现](examples/_support.py)；[11](examples/11_responses_vision.py)；[14](examples/14_prefix_completion.py)；[15](examples/15_fim_completion.py)

<a id="streaming"></a>
## 4. 流式传输、用量与结束状态

`stream=True` 改为 SSE 增量返回，不是另一种模型，也不等于关闭思考。Chat 流以 `data: [DONE]` 结束；`stream_options` 只能与 `stream=True` 同用。[Chat 流式协议](https://api-docs.deepseek.com/api/create-chat-completion/)

DeepSeek 当前规定：无论是否设置 `stream_options.include_usage`，最后一个 chunk 都带本次 `usage`，其中有一个不带新正文、但有 `finish_reason` 的 choice；**不另发独立 usage-only chunk**。`include_usage=True` 主要让先前 chunk 也带 `usage: null`。02 没有设置此选项；对空 `choices` 的防御性处理不是宣称官方一定会发空 choices。[官方分块说明](https://api-docs.deepseek.com/api/create-chat-completion/)；[02 源码](examples/02_streaming.py)

`finish_reason` 是响应状态，不是请求参数：`stop` 才是本目录普通回答接受的完整结束；`length` 表示到达长度限制，`tool_calls` 表示要进入工具步骤，`aborted` 等不算完整答案。流断开、只收到 usage 或正文为空都不能仅凭 HTTP 成功判定通过。后一句是项目验收规则。[官方结束原因](https://api-docs.deepseek.com/api/create-chat-completion/)；[02](examples/02_streaming.py)；[共享检查](examples/_support.py)

<a id="tools"></a>
## 5. 工具定义、选择与严格模式

| 参数 | 说明 | 官方依据 |
|---|---|---|
| `tools[].type="function"` | 声明可调用的函数，不会让服务端自动执行本机 Python。模型返回调用，程序验证并执行后再回传结果。 | [工具调用流程](https://api-docs.deepseek.com/guides/tool_calls/) |
| `function.name` / `description` | 本例名称为 `get_weather`；描述帮助模型判断用途，不是授予执行权限。 | [工具参数](https://api-docs.deepseek.com/api/create-chat-completion/)；[05 源码](examples/05_tool_calling.py) |
| `function.parameters` | JSON Schema：`type=object`、`properties.city.type=string`、`required=["city"]`、`additionalProperties=false`，描述参数对象的结构。 | [工具 Schema 说明](https://api-docs.deepseek.com/guides/tool_calls/) |
| `tool_choice` | `none` 不调用、`auto` 可回答或调用、`required` 必须调用，也可指定函数；思考模式不支持 `required` 或指定函数。12、13 显式用 `auto`；05 省略，有 tools 时官方默认 `auto`。 | [Chat 工具选择](https://api-docs.deepseek.com/api/create-chat-completion/) |
| `function.strict=True` | 13 的 Beta 能力：保证调用参数符合支持的 Schema 结构，不保证城市真实或业务正确。须使用 Beta 地址、所有 function 都设 strict；每个 object 的属性均 required，并设 `additionalProperties=false`。 | [Strict Mode](https://api-docs.deepseek.com/guides/tool_calls/) |

思考工具调用必须保留并回传完整 assistant，包括 `tool_calls` 和 `reasoning_content`，不能只留最终正文；缺少必要思考历史可能导致 400。12 依赖的共享循环直接保留完整 SDK 消息。[思考工具历史要求](https://api-docs.deepseek.com/guides/thinking_mode/)；[共享循环](examples/_support.py)

项目约定：天气结果是**模拟数据**，不会联网查询；调用前先校验整批参数、工具白名单、唯一 ID、`city` 类型及 1–80 字符长度，最多 6 次模型轮次。只有确实执行过工具且收到最终完整回答才算工具闭环。`max_model_turns`、城市长度和执行计数都不是 DeepSeek 请求参数，strict 也不替代这些检查。[05](examples/05_tool_calling.py)；[12](examples/12_thinking_tools.py)；[13](examples/13_strict_tools.py)；[共享实现](examples/_support.py)

<a id="json"></a>
## 6. JSON 输出

04 的 `response_format={"type":"json_object"}` 请求合法 JSON；还必须在 system / user 提示词里要求 JSON。它不是任意 JSON Schema 的结构化输出模式，也不保证字段的业务含义；官方另提醒可能有空正文或因预算截断。[官方 JSON 模式](https://api-docs.deepseek.com/guides/json_mode/)

本例关闭思考，先查 `finish_reason` 和非空正文，再 `json.loads`，最后检查 `ok` 是否确为布尔值 `True`。最后两步是项目的格式解析与业务断言，不是发给服务端的参数。[04 源码](examples/04_json_output.py)

<a id="vision-files"></a>
## 7. 图片、`detail` 与 Files API

| 字段 | 解释与限制 | 官方依据 |
|---|---|---|
| Chat `content[].type="text"` / `text` | 图片问题的文字部分；与图片块一起放在 user 消息中。 | [视觉输入形状](https://api-docs.deepseek.com/guides/vision/) |
| `image_url.url` | 可公开访问的 HTTP(S) URL，或 `data:image/…;base64,…`。支持 JPEG、PNG、GIF、WebP，官方按实际内容识别。 | [视觉输入](https://api-docs.deepseek.com/guides/vision/) |
| `image_url.detail` | `low` 缩至 512×512；`high` / `original` 保留原图，`auto` 当前等同 original。06 没显式传；11 的 detail 放在 Responses 图片块顶层。 | [Detail Level](https://api-docs.deepseek.com/guides/vision/) |
| `files.create(file=…, purpose="user_data")` | multipart 上传，不是 Chat JSON；`purpose` 必填且固定为 `user_data`。 | [Files API](https://api-docs.deepseek.com/guides/files_api/) |
| `expires_after` | `anchor="created_at"`，`seconds` 范围 `3600..2592000`；省略过期配置为永久保存。10 选一小时是项目存储策略，不是官方默认。 | [文件过期配置](https://api-docs.deepseek.com/guides/files_api/)；[10 源码](examples/10_vision_files.py) |
| `{"type":"file","file_id":"file-api-…"}` | Chat 引用已上传图片；`file_id` 是块的顶层字段，不能改成 `file.file_id`。已上传文件按 API Key 隔离。 | [图片文件引用](https://api-docs.deepseek.com/guides/vision/)；[文件作用域](https://api-docs.deepseek.com/guides/files_api/) |

与示例直接相关的官方大小边界：URL 最长 8192 字符，远程图片或 inline 图片最多 32 MiB，inline 请求体最多 48 MiB（包含 base64 膨胀），通过 `file_id` 引用的单张图片最多 64 MiB。`max_tokens` 不会改变这些字节限制。[视觉限制](https://api-docs.deepseek.com/guides/vision/)

项目输入变量不属于 API：06 的 `IMAGE_URL` / `IMAGE_PATH` 转成 `image_url.url`，本地分支只接受示例代码列出的 JPEG / PNG 后缀；这不等于型号只支持两种格式。10 的 `IMAGE_PATH` 与 `IMAGE_FILE_ID` 二选一，后者复用已有文件、不再次上传。11 的 `IMAGE_DETAIL` 默认 `auto`；共享帮助函数检查文件头、部分大小和 URL 条件，但不是全部官方限制的替代。示例对远程输入额外要求 HTTPS 是项目约定，官方同时接受 HTTP(S)。[06](examples/06_vision.py)；[10](examples/10_vision_files.py)；[11](examples/11_responses_vision.py)；[共享输入检查](examples/_support.py)

<a id="responses"></a>
## 8. Responses：不要照搬 Chat 字段形状

11 使用同一普通 Base URL 下的 `/responses`，不是 `/chat/completions`。实际参数区别如下。[Responses API](https://api-docs.deepseek.com/api/create-response/)

| 本例字段 | 含义 |
|---|---|
| `input` | 代替 Chat 的 messages；这里是 user 消息数组，内容为 `input_text` 和 `input_image`。 |
| `input_image.image_url` / `detail` | URL 是字符串，不是 Chat 的 `{url:…}` 对象；detail 与 image_url 同级。也支持 `file_id`，二者互斥，file_id 时忽略 detail；11 本身未走 file_id 分支。 |
| `reasoning={"effort":"none"}` | Responses 的关闭思考写法，不是 Chat 的 `thinking` 字段；可选强度为 `none` / `low` / `high` / `max`。 |
| `max_output_tokens=2048` | 输出上限，官方明确包含**可见正文与思考 token**；2048 是本例选择，不是型号上限。 |

以上字段与预算定义见 [Responses 请求](https://api-docs.deepseek.com/api/create-response/)，图片细节见 [Responses 图片输入](https://api-docs.deepseek.com/guides/vision/)。本例要求 `response.status="completed"` 且 `output_text` 非空；`incomplete` / `failed` 不算完成。[响应状态](https://api-docs.deepseek.com/api/create-response/)；[11 源码](examples/11_responses_vision.py)

此接口仍是无状态的；不要套用 OpenAI 的服务端会话保存假设，也不要靠 `previous_response_id` 省略历史。本例没有使用 Responses 流式；其事件协议与 Chat 的 `[DONE]` 不同，不能复用 02 的解析器。[DeepSeek Responses 兼容范围](https://api-docs.deepseek.com/guides/responses_api/)

<a id="beta"></a>
## 9. Beta 前缀续写与 FIM

| 示例 | 实际参数与意义 | 官方依据 |
|---|---|---|
| 13 严格工具 | `base_url="https://api.deepseek.com/beta"` + `function.strict=True`，其余仍走 Chat。 | [严格工具 Beta](https://api-docs.deepseek.com/guides/tool_calls/) |
| 14 前缀续写 | 最后一条为 assistant，`content` 给出代码开头，**该消息内** `prefix=True` 强制续写；Chat 请求的 `stop=["```"]` 到代码围栏时停止；`max_tokens=1024` 是本例预算。 | [Chat Prefix Completion](https://api-docs.deepseek.com/guides/chat_prefix_completion/)；[14 源码](examples/14_prefix_completion.py) |
| 15 FIM | Beta 地址下调用 `client.completions.create`（`/completions`）；`prompt` 是空缺前文本，`suffix` 是空缺后文本，返回中间补全，而不是 Chat messages。`max_tokens=128` 是本例小预算；FIM 最大输出为 4K，且仅非思考模式。 | [FIM 参数与上限](https://api-docs.deepseek.com/guides/fim_completion/)；[功能限制](https://api-docs.deepseek.com/quick_start/pricing/) |

`beta=True` 是本仓库 `make_client` 的本地参数，用来选择 Beta Base URL，不是发给模型的 JSON 字段。14 输出时拼回既有前缀、15 拼接前后文，也都是本地展示逻辑。[共享客户端](examples/_support.py)；[14](examples/14_prefix_completion.py)；[15](examples/15_fim_completion.py)

<a id="sdk"></a>
## 10. SDK 配置与本地校验，不是模型参数

| 配置或检查 | 它实际控制什么 |
|---|---|
| Python `timeout=120` | SDK 的网络超时配置，单位秒；不是“最多生成 120 token”，也不是端到端整条工具链必定 120 秒结束。 |
| TypeScript `timeout:120_000` | SDK 的网络超时配置，单位毫秒，与 Python 120 秒对应。 |
| Python `max_retries` / TypeScript `maxRetries` | SDK 自动重试配置，`0` 可禁用；与项目 6 轮工具循环是两回事。现有示例未显式设置，不能据此宣称不会自动重试。 |
| Python `extra_body={"thinking":…}` | SDK 扩展请求体的入口；发往 DeepSeek 的 JSON 顶层字段是 `thinking`，不是服务端有一个名为 extra_body 的开关。 |

SDK 语义依据 [OpenAI Python：超时、重试、扩展参数](https://developers.openai.com/api/reference/python) 与 [TypeScript：超时和重试](https://developers.openai.com/api/reference/typescript)；实际配置见[01](examples/01_basic.py)、[07](examples/07_typescript.ts)、[共享客户端](examples/_support.py)。SDK 文档不能证明 DeepSeek 支持某个额外字段，厂商支持范围仍以前述 DeepSeek 官方文档为准。

`completed_text`、`image_bytes(max_bytes=…)`、`max_model_turns`、JSON 业务断言、空正文检查、异常时不打印原始响应，均是示例程序自己的校验或安全策略；它们不是可复制进 API JSON 的生成参数。[共享实现](examples/_support.py)；[04](examples/04_json_output.py)；[05](examples/05_tool_calling.py)

<a id="example-map"></a>
## 11. 每个可运行文件的实际请求对照

表中省略公共的 `api_key` / `base_url` / `timeout` 时，仍使用[身份配置](#identity)与[SDK 配置](#sdk)；“未设置”不是默认关闭。每行文件链接即该行项目配置的来源。

| 可运行文件 | 实际发送的主要输入参数 | 参数解释 |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | `model`、user `messages`；未显式设置思考或预算 | [消息](#identity)、[默认思考与预算](#budget) |
| [02_streaming.py](examples/02_streaming.py) | `model`、user `messages`、`stream=True`、`thinking.type=disabled`；不传 stream_options | [流式与 usage](#streaming)、[思考](#budget) |
| [03_thinking.py](examples/03_thinking.py) | 同一 user 问题分别传 thinking disabled，以及 thinking enabled + `reasoning_effort=high` | [思考与预算](#budget) |
| [04_json_output.py](examples/04_json_output.py) | `model`、要求 JSON 的 user `messages`、`response_format.type=json_object`、thinking disabled | [JSON](#json)、[思考](#budget) |
| [05_tool_calling.py](examples/05_tool_calling.py) | `model`、system/user/完整 assistant/tool 历史、`tools`、thinking disabled；不显式传 tool_choice | [工具 Schema、历史与本地限制](#tools) |
| [06_vision.py](examples/06_vision.py) | `model`、user text + `image_url.url` 内容块、thinking disabled；不传 detail | [图片与本地变量](#vision-files) |
| [07_typescript.ts](examples/07_typescript.ts) | `model`、user `messages`；客户端 `apiKey` / `baseURL` / `timeout:120_000` | [身份](#identity)、[默认思考](#budget)、[SDK](#sdk) |
| [08_curl.sh](examples/08_curl.sh) | POST Chat，Bearer/JSON 请求头；body 为 `model`、user `messages` | [身份](#identity)、[默认思考与预算](#budget) |
| [09_multi_turn.py](examples/09_multi_turn.py) | `model`、累积 system/user/assistant `messages`、thinking disabled | [多轮历史](#identity) |
| [10_vision_files.py](examples/10_vision_files.py) | 上传时 `file` / `purpose` / `expires_after`；Chat `model`、user text + 顶层 file_id、thinking disabled | [Files 与图片](#vision-files) |
| [11_responses_vision.py](examples/11_responses_vision.py) | `model`、`input`、input_text/input_image、`image_url` / `detail`、`reasoning.effort=none`、`max_output_tokens=2048` | [Responses](#responses)、[图片](#vision-files) |
| [12_thinking_tools.py](examples/12_thinking_tools.py) | 共享循环的 `model` / `messages` / `tools` / `tool_choice=auto` / thinking enabled / `max_tokens=16384` | [工具](#tools)、[预算](#budget) |
| [13_strict_tools.py](examples/13_strict_tools.py) | Beta 客户端；共享循环 tools 内 `strict=True`、tool_choice auto、thinking disabled、`max_tokens=2048` | [严格工具](#tools)、[Beta](#beta) |
| [14_prefix_completion.py](examples/14_prefix_completion.py) | Beta Chat；`model` / `messages`，最后 assistant 内 prefix；`stop`、`max_tokens=1024`、thinking disabled | [前缀续写](#beta) |
| [15_fim_completion.py](examples/15_fim_completion.py) | Beta Completions；`model` / `prompt` / `suffix` / `max_tokens=128` | [FIM](#beta) |

[_support.py](examples/_support.py) 是 09–15 使用的本地帮助文件，不是单独的 API 功能示例；它的客户端、图片校验与工具循环分别已列于以上各节。
