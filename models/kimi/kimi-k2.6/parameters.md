# `kimi-k2.6` 示例参数逐项说明

[English](parameters.en.md) · [人类篇](../../../human/README.md)

核对日期：2026-10-14。本页解释本目录示例实际发送的字段，不是其他 Kimi 型号的通用参数表。官方事实就近链接；“项目约定”只描述可查看的示例源码，不代表官方限制或性能保证。实际执行结果另查[示例实测状态](../../../docs/示例实测状态.md)，参数释义本身不是实测报告。

## 1. 按文件找参数

下表省略所有文件共有的 `model="kimi-k2.6"`、`messages` 和客户端连接选项；它们在后文解释。没有列出的参数就是该文件未显式设置，而不是值为零。具体请求以各文件链接为准。

| 文件 | 显式请求字段与本例取值 | 输入、历史和项目约定 |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | 无额外字段 | 单条文本 user 消息；未指定 `thinking`，因此使用 K2.6 默认思考模式。默认依据：[型号参数](https://platform.kimi.com/docs/api/models-overview)。 |
| [02_streaming.py](examples/02_streaming.py) | `stream=True`；`thinking.type="disabled"` | 文本增量；没有显式发送 `stream_options`。 |
| [03_thinking.py](examples/03_thinking.py) | `thinking.type="enabled"`；`max_tokens=16384` | 分别读取思考与最终正文；16384 是本例预算，不是型号上限。 |
| [04_json_output.py](examples/04_json_output.py) | `response_format.type="json_object"`；关闭思考 | 提示词要求 `{"ok":true}`；本地检查恰好一个 `ok` 字段且值为布尔真。 |
| [05_tool_calling.py](examples/05_tool_calling.py) | `tools` 定义 `get_weather(city)`；关闭思考 | 未显式设置 `tool_choice`；整批校验后执行模拟天气函数，最多六次模型调用，完整回传 assistant 与 tool 消息。 |
| [06_vision.py](examples/06_vision.py) | `content` 数组含 `text`、`image_url.url`；关闭思考 | `IMAGE_PATH` 本地 PNG/JPEG → base64 data URL；拒绝 `IMAGE_URL`。 |
| [07_multi_turn.py](examples/07_multi_turn.py) | 关闭思考 | 每轮重发历史 `messages`；成功后才追加 user 和完整 assistant，避免失败轮污染历史。 |
| [08_thinking_tools.py](examples/08_thinking_tools.py) | `tools` 定义 `get_order_status(order_id)`；`tool_choice="auto"`；`thinking={"type":"enabled","keep":"all"}`；`max_tokens=32768` | 模拟订单；完整思考历史；本地默认最多六次模型调用，不能把未调用工具的直接答案算作闭环。 |
| [09_video.py](examples/09_video.py) | `content` 数组含 `video_url.url`、`text`；关闭思考 | `VIDEO_PATH` 本地 MP4 → `data:video/mp4;base64,...`；没有发送 `fps`、远程视频地址或上传文件请求。 |
| [10_json_schema.py](examples/10_json_schema.py) | `response_format.type="json_schema"`；`json_schema.name="person"`、`strict=True`、对象 Schema；关闭思考 | Schema 要求 `name:string` 与 `age:integer`，两者必填，禁止额外字段；另做本地姓名/年龄校验。 |

“关闭思考”的 Python 写法均为 `extra_body={"thinking":{"type":"disabled"}}`；这是 K2.6 支持的配置，不适用于始终思考的其他型号。[型号参数](https://platform.kimi.com/docs/api/models-overview)

## 2. 连接选项不是生成参数

| 字段 | 本例取值、默认与作用 | 出处 |
|---|---|---|
| `api_key` | 从 `MOONSHOT_API_KEY` 读取；属于认证信息，不参与采样。没有该环境变量时脚本失败，不回退到写死的 Key。 | [官方快速开始](https://platform.kimi.com/docs/get-api-key)；各示例源码 |
| `base_url` | `https://api.moonshot.cn/v1`；OpenAI SDK 将 Chat Completions 请求发往 Kimi，而不是 OpenAI。 | [官方快速开始](https://platform.kimi.com/docs/get-api-key) |
| `timeout=120` | 所有示例显式设置的 SDK 超时，单位秒；不是服务端生成 token 预算，也不是“整个工具循环必在两分钟内完成”的承诺。 | [SDK：Timeouts](https://developers.openai.com/api/reference/python#timeouts)；各示例源码 |
| `max_retries` | 这些示例未覆盖 SDK 的默认重试设置；官方 SDK 默认对部分连接/状态错误重试两次，`0` 可关闭。重试和工具循环次数是两回事。 | [SDK：Retries](https://developers.openai.com/api/reference/python#retries) |
| `extra_body` | SDK 的扩展字段入口；其中 `thinking` 会合并到 HTTP JSON 请求体顶层，服务端并不需要名为 `extra_body` 的一层。直接 HTTP 应发送顶层 `thinking`。 | [型号参数及 curl 对照](https://platform.kimi.com/docs/api/models-overview)；[SDK：额外请求参数](https://developers.openai.com/api/reference/python#undocumented-request-params) |

SDK 文档解释的是客户端机制，不为 Kimi 提供 OpenAI 模型能力背书；安装版本以仓库 [requirements-lock.txt](../../../requirements-lock.txt) 为准。项目建议：生产应用同时设定自己的整段任务期限、重试预算和工具执行幂等策略；这些不是本型号的 API 参数。

## 3. 模型、消息与预算

| 字段/限制 | 作用、默认或边界 | 出处 |
|---|---|---|
| `model` | 本页固定 `kimi-k2.6`；不是 `kimi-k3` 或 K2.7 的别名，不能只替换名称后沿用不同型号的参数限制。 | [型号参数对比](https://platform.kimi.com/docs/api/models-overview) |
| `messages[].role` | 本例使用 `user`、`system`、`assistant`、`tool`；分别表达用户输入、系统要求、模型历史和工具结果。`content` 文本是字符串，多模态时为内容块数组。 | [Chat API：messages/content](https://platform.kimi.com/docs/api/chat) |
| 历史 `messages` | 多轮示例显式带回历史；不是靠同一个 Python client 自动记忆上轮。工具循环的 assistant 及对应 tool 结果必须一起保留。 | [多轮对话](https://platform.kimi.com/docs/guide/engage-in-multi-turn-conversations-using-kimi-api)；[工具调用](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls) |
| 上下文 | K2.6 为 256K tokens；这是上下文窗口，不是每次可输出 256K 的承诺。历史思考被保留时也占用上下文。 | [K2.6 型号页](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart)；[思考保留与消耗](https://platform.kimi.com/docs/guide/use-thinking-models) |
| `max_tokens` | 整数生成预算，K2.6 的思考 `reasoning_content` 和正文 `content` 共同消耗它；预算不足可能只有思考、没有正文。多步工具场景官方建议至少 16000，本例 03/08 分别选 16384/32768。 | [思考模型：输出预算](https://platform.kimi.com/docs/guide/use-thinking-models)；[03](examples/03_thinking.py)、[08](examples/08_thinking_tools.py) |
| 未设预算的文件 | 采用服务端默认；本次未确认当前官方针对 **K2.6** 的单次输出默认值及硬上限，标为未知。不能把 Chat API 页面其他型号的 `max_completion_tokens` 默认或范围搬来；示例预算也不是上限证据。 | [K2.6 参数说明](https://platform.kimi.com/docs/api/models-overview)与[思考指南](https://platform.kimi.com/docs/guide/use-thinking-models)的已确认范围 |

项目建议：增加预算不能替代结束检查，也不意味着必然生成那么多 token。所有截断都应单独处理，不要把 `reasoning_content` 当最终答案补位；可检查 [03 的完整性判断](examples/03_thinking.py)。

## 4. 思考与采样

| 参数 | K2.6 支持情况、默认与影响 | 出处 |
|---|---|---|
| `thinking.type` | `enabled`（默认）或 `disabled`；决定本次是否思考。示例 01 未设置，03/08 开启，其余明确关闭。 | [型号参数](https://platform.kimi.com/docs/api/models-overview) |
| `thinking.keep` | K2.6 默认不跨用户轮保留历史思考；`"all"` 开启保留。它不代替 `type` 开关；开启后要回传完整 `reasoning_content`，增加后续输入占用和计费。 | [思考模型：Preserved Thinking](https://platform.kimi.com/docs/guide/use-thinking-models) |
| 同一工具循环历史 | 无论如何配置跨轮保留，都不要删掉当前工具闭环所需的完整 assistant，包括 `reasoning_content`；08 直接保留 SDK message，避免手写字段漏传。 | [思考模型：工具调用](https://platform.kimi.com/docs/guide/use-thinking-models)；[08 源码](examples/08_thinking_tools.py) |
| `temperature` | 不可自由调：思考固定 1.0，非思考固定 0.6；其他值会报错，官方建议不显式传。本目录全部省略。 | [型号参数：temperature](https://platform.kimi.com/docs/api/models-overview) |
| `top_p`、`n`、两类 penalty | `top_p` 固定 0.95；`n` 固定 1；`presence_penalty`/`frequency_penalty` 固定 0。不要套其他厂商的范围。 | [型号参数对比](https://platform.kimi.com/docs/api/models-overview) |
| `reasoning_effort`、`preserve_thinking` | K2.6 不支持前者；本页官方 Kimi 接口用 `thinking.keep`，不把百炼的 `preserve_thinking` 拼到 Kimi 请求中。 | [型号参数](https://platform.kimi.com/docs/api/models-overview)；[官方保留写法](https://platform.kimi.com/docs/guide/use-thinking-models) |

项目建议：不要把“更确定”当成“事实更准确”，本仓库不提供温度与准确率的保证。K2.6 的采样值固定，没有可用的“设为 0 更准确”写法；应提供依据、明确任务与验收条件，再检查输出。固定值以[官方型号表](https://platform.kimi.com/docs/api/models-overview)为准。

## 5. 流式、usage 与结束状态

`stream` 默认关闭；02 设为 `True` 后，正文/思考从 `delta.content` / `delta.reasoning_content` 读取，不能继续按完整 `message` 解析。`stream_options.include_usage` 是流式用量选项：需要用量时可设 `True`，但当前 02 没有设置，不能承诺一定取得流式 usage；它只记录服务端实际返回的值。[流式输出](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api)；[Chat API：stream_options](https://platform.kimi.com/docs/api/chat)；[02 源码](examples/02_streaming.py)

`usage.prompt_tokens`、`completion_tokens`、`total_tokens` 是响应统计，不是请求参数；缓存等明细仅在实际返回时记录。`finish_reason="length"` 表示触及长度限制，不能当完整答案；工具阶段的 `tool_calls` 也不是最终文字成功。项目示例要求最终 `stop` 且非空正文，流式代码拒绝空 `choices` 误索引、未结束或互相矛盾的结束状态。[Chat API：响应字段](https://platform.kimi.com/docs/api/chat)；[02](examples/02_streaming.py)、[08](examples/08_thinking_tools.py)

## 6. 工具和 JSON 的嵌套字段

| 字段 | 用途、限制及本例取值 | 出处 |
|---|---|---|
| `tools[].type="function"` | 声明可调用函数；不是把 Python 函数上传让服务端执行。 | [工具调用基础](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls) |
| `function.name` / `description` | 告诉模型函数标识与用途；05 为模拟天气，08 为模拟订单。函数名与本地白名单必须匹配。 | [工具调用基础](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls)；[05](examples/05_tool_calling.py)、[08](examples/08_thinking_tools.py) |
| `function.parameters` | JSON Schema：`type="object"`、`properties` 中字段类型为 `string`、`required` 声明必填、`additionalProperties=False` 禁止额外键；本例没设置工具级 `strict`。应用仍须校验模型返回的参数。 | [工具调用基础](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls)；[05](examples/05_tool_calling.py)、[08](examples/08_thinking_tools.py) |
| `tool_choice` | 默认 `auto`，让模型自行决定；可用 `none` 或官方指定函数形式。K2.6 不支持 `required`，所以示例用本地“至少执行一次”的检查判定闭环完成，不假装 `auto` 保证调用。 | [工具调用约束](https://platform.kimi.com/docs/guide/use-tool-choice)；[08](examples/08_thinking_tools.py) |
| 返回的 `tool_calls[].id`、`function.arguments` | `arguments` 是待解析 JSON 字符串；应用整批校验名称、ID、参数后执行，再用 `role="tool"`、匹配 `tool_call_id` 和字符串 `content` 回传结果，不编造 ID。 | [工具调用流程](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls)；[05](examples/05_tool_calling.py)、[08](examples/08_thinking_tools.py) |
| `response_format.type="json_object"` | 04 要求 JSON 对象；提示词仍需说明 JSON 和目标字段，不等于业务 Schema 验证通过。 | [JSON Mode](https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api)；[04](examples/04_json_output.py) |
| `response_format.type="json_schema"` | 10 用 `json_schema.name` 标识结构、`schema` 定义字段、`strict=True` 请求严格遵循。K2.6 可用简单结构；复杂 `$ref`/`oneOf` 等不能照搬较新型号保证。 | [response_format：支持范围与配置](https://platform.kimi.com/docs/guide/response_format) |
| Schema 内 `required` / `additionalProperties` | 10 要求 `name`、`age` 都存在，且无其他键；`strict` 位于 `json_schema`，不是消息字段或独立顶层参数。 | [response_format](https://platform.kimi.com/docs/guide/response_format)；[10](examples/10_json_schema.py) |

城市 1–80 字、订单号 `DEMO-` 加四位数字、姓名长度、年龄 0–150、重复工具 ID 拒绝、六轮上限，都只是本项目的业务校验/安全边界，不是官方参数范围。它们可分别在 [05](examples/05_tool_calling.py)、[08](examples/08_thinking_tools.py)、[10](examples/10_json_schema.py) 查看；天气和订单数据均为本地模拟，不连接真实系统。

## 7. 图片与视频的字段不能互换

K2.6 的官方输入包含文本、图片、视频。06 的 `messages[].content` 是实际数组：文本块用 `type="text"`/`text`，图片块用 `type="image_url"`/`image_url.url`。09 则是 `type="video_url"`/`video_url.url`，不是把 MP4 填进图片字段。[K2.6：图片/视频示例](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart)

官方图片字段接受 base64 data URL 或 `ms://<file_id>`，不支持直接远程 HTTP(S) 图片地址；内容块不能先 `json.dumps` 成一个字符串。官方支持的图片格式比 06 的 PNG/JPEG 子集更广；09 只演示 MP4，不代表其他官方视频格式均不支持。`IMAGE_PATH`、`IMAGE_URL`、`VIDEO_PATH` 都是本地脚本变量，不是 API 字段；本例不实现上传、`ms://` 或抽帧 `fps` 参数。[视觉输入：格式与传输限制](https://platform.kimi.com/docs/guide/use-kimi-vision-model)；[06](examples/06_vision.py)、[09](examples/09_video.py)

项目建议：先使用短小、自己有权发送的文件；扩展上传/格式或更换接口前重新核对[官方视觉文档](https://platform.kimi.com/docs/guide/use-kimi-vision-model)，不要套用其他平台同名 `image_url` 的远程地址行为。
