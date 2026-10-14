# `doubao-seed-2-1-pro-260628` 参数解释

[English](parameters.en.md) · [人类篇](../../../human/README.md)

核对日期：2026-10-14。本页按[本目录示例清单](examples/sources.json)解释实际字段；调用文件另查[调用代码目录](../../../docs/示例实测状态.md)。官方把本 ID 列在往期模型中，下面的型号说明不外推到新版本。[模型列表：往期模型][d-models]

## 先看每个文件实际发送什么

所有文件都发送 `model="doubao-seed-2-1-pro-260628"` 和 `messages`；都用 `ARK_API_KEY`、同一个 `base_url`、SDK `timeout=120`。当前十个文件均未显式发送 `temperature`、`top_p`、`max_tokens`、`max_completion_tokens` 或 `stream_options`，因此不能把下表的示例选择理解为这些参数已被设置。[01 源码](examples/01_basic.py) · [02 源码](examples/02_streaming.py) · [03 源码](examples/03_thinking.py) · [04 源码](examples/04_json_output.py) · [05 源码](examples/05_tool_calling.py) · [06 源码](examples/06_vision.py) · [07 源码](examples/07_multi_turn.py) · [08 源码](examples/08_thinking_tools.py) · [09 源码](examples/09_video.py) · [10 源码](examples/10_implicit_cache.py)

| 文件 | 公共字段以外的实际 API 参数 | 本地处理与返回值 |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | `thinking.type="disabled"` | 检查完整正文，打印 `usage` |
| [02_streaming.py](examples/02_streaming.py) | `stream=True`；`thinking.type="disabled"` | 拼接 `delta.content`，检查结束原因，关闭流 |
| [03_thinking.py](examples/03_thinking.py) | `thinking.type="enabled"` | 区分思考摘要、最终正文和实际 `reasoning_tokens` |
| [04_json_output.py](examples/04_json_output.py) | `response_format.type="json_schema"`；`json_schema.name="result"`、`strict=True`、`schema`；关闭思考 | 解析 JSON，并检查只有布尔字段 `ok=true` |
| [05_tool_calling.py](examples/05_tool_calling.py) | `tools` 定义 `get_weather(city)`；关闭思考；未设置 `tool_choice` | 最多六轮，执行固定模拟天气函数并回传工具结果 |
| [06_vision.py](examples/06_vision.py) | `messages[].content` 是 `text`、`image_url` 内容块数组；关闭思考 | 从 `IMAGE_URL` 或 `IMAGE_PATH` 构造图片输入 |
| [07_multi_turn.py](examples/07_multi_turn.py) | `messages` 包含完整历史；关闭思考 | 固定两轮，只把完整回答加入历史 |
| [08_thinking_tools.py](examples/08_thinking_tools.py) | `tools`；`thinking.type="enabled"`；未设置 `tool_choice` | 最多六轮，完整回传思考相关字段与工具结果 |
| [09_video.py](examples/09_video.py) | `content` 含 `video_url.url` 和文本；关闭思考 | 从 `VIDEO_URL` 读取地址；未设置 `fps`、音频或文件预处理选项 |
| [10_implicit_cache.py](examples/10_implicit_cache.py) | 两次相同前缀的普通 `messages`；关闭思考；没有缓存开关 | 读取返回的 `usage.prompt_tokens_details.cached_tokens` |

此表是对上述源文件的描述。API 中 `thinking`、`stream`、`response_format`、`tools`、多模态消息与 `usage` 的含义分别见 [Chat API][d-api]；多轮与工具流程见[上下文管理][d-context]和[函数调用][d-tools]。

## 连接和 SDK 参数

| 参数或变量 | 用途、当前值及边界 | 出处 |
|---|---|---|
| `api_key` / `ARK_API_KEY` | `api_key` 是客户端鉴权配置；示例从本地环境变量 `ARK_API_KEY` 读取，不是让模型理解的提示词字段 | [官方 OpenAI SDK 接入][d-sdk] |
| `base_url` | 当前为 `https://ark.cn-beijing.volces.com/api/v3`；SDK 的 Chat 方法请求其 `/chat/completions` 路径，不把整条路径再次当作 `base_url` | [官方 OpenAI SDK 接入][d-sdk] |
| `timeout=120` | SDK 的网络请求超时设置，单位秒；120 是本项目示例选择，不是模型输出 token 上限，也不是官方承诺的响应时间 | [01 源码](examples/01_basic.py) · [OpenAI 官方 SDK 超时说明][sdk-timeouts] |
| `max_retries` | SDK 自动重试配置；本目录当前没有显式设置，使用所安装 SDK 的行为。官方 SDK 默认对部分连接错误及 408、409、429、5xx 等重试两次；一次调用表达式不必然只产生一次 HTTP 尝试 | [锁定依赖](../../../requirements-lock.txt) · [OpenAI 官方 SDK 超时与重试说明][sdk-timeouts] |
| `extra_body` | OpenAI Python SDK 的额外请求字段容器。`extra_body={"thinking":{"type":"disabled"}}` 合并成 HTTP JSON 顶层的 `thinking`；原始 HTTP 请求不包一层 `extra_body` | [官方 OpenAI SDK：设置额外字段][d-sdk] |

## 请求正文、历史和采样

| API 字段 | 用途、默认值或范围 | 本型号注意事项与出处 |
|---|---|---|
| `model` | 指定模型 ID；本目录固定为 `doubao-seed-2-1-pro-260628` | 改成其他 ID 前重新查能力、上下文和生命周期；[模型列表][d-models] |
| `messages` | 按会话顺序提供输入与历史；每条包含 `role` 和相应内容 | Chat API 手动维护上下文；07 不使用 `previous_response_id`；[上下文管理：手动输入上下文][d-context] |
| `messages[].role` | `system` 设置行为，`user` 提问，`assistant` 保存模型消息，`tool` 回传函数结果 | 工具消息还需匹配 `tool_call_id`；[Chat API：messages][d-api] |
| `messages[].content` | 纯文本可用字符串；图片、视频混合输入使用内容块数组 | 数组包含对象，不能先 `json.dumps` 后当作普通文本发送；[图片理解][d-image] · [视频理解][d-video] |
| `temperature` | 调整 token 采样的随机性。通用 Chat 文档范围 `[0,2]`、默认 `1.0`；更高通常更随机，更低通常更集中 | 当前示例未设置。API 对部分旧 2.0 型号列有固定值例外，不能把那些型号的例外移植到本 ID；[Chat API：temperature][d-api] |
| `top_p` | 核采样阈值，限制参与采样的累计概率质量。通用文档范围 `[0,1]`、默认 `0.7`；较小更集中，较大更多样 | 当前示例未设置。官方建议与 `temperature` 二选一调整，而不是同时大改；[Chat API：top_p][d-api] |

本项目使用建议：需要换写法、增添表达变化时再调采样；需要固定字段和可处理的数据时优先定义输出格式并做校验。采样参数控制生成分布，结构约束由 `response_format` 和应用校验承担。[Chat API：采样、response_format][d-api] · [结构化输出：推荐使用步骤][d-json]

## 上下文窗口、回答预算和思考预算

| 概念或字段 | 含义、默认及限制 | 出处 |
|---|---|---|
| 型号上下文窗口 | 官方列为 `256K`；它是模型可处理的输入与生成内容边界，不是每次请求自动生成 `256K` 正文 | [模型列表][d-models] · [Chat API：finish_reason 的 context_window 限制][d-api] |
| `max_tokens` | 限制回答长度；Chat API 默认 `4096`，范围随型号变化。本型号列表列最大回答 `256K` | [Chat API：max_tokens][d-api] · [上下文管理：控制回答长度][d-context] · [模型列表][d-models] |
| `max_completion_tokens` | 限制“思维链 + 回答”的总生成长度；配置后 `max_tokens` 默认限制失效。官方说明 `250528` 及之后语言模型默认支持，特例另列 | [上下文管理：控制输出（回答+思维链）长度][d-context] |
| 两种预算的关系 | 不可同时发送 `max_tokens` 与 `max_completion_tokens`；二者不能当作同义字段随意替换 | [Chat API：max_completion_tokens][d-api] · [上下文管理][d-context] |
| 请求参数上界 | 当前通用 Chat API 对 `max_completion_tokens` 写 `[1,65536]`，而型号列表另列最大回答 `256K`；本页不据此推导该历史型号的更大可接受参数值，其单独完整上界保留未知 | [Chat API][d-api] · [模型列表][d-models] |

当前十个文件没有显式设置上述两种预算。`finish_reason="length"` 可能来自回答限制、总生成限制或上下文限制；只有“有正文”仍不足以说明完成，应同时检查结束原因。给总生成预算设得过小，思考也可能消耗它，留给正文的空间随之减少。[本目录代码](examples/03_thinking.py) · [Chat API：finish_reason][d-api]

## 思考、摘要和工具回传

本型号的 `thinking.type` 支持 `enabled`（默认）与 `disabled`。它是思考开关；`temperature` 不是思考开关。03、08 显式开启，其余文件显式关闭。[深度思考：控制深度思考][d-thinking] · [Chat API：temperature/thinking][d-api] · [示例清单](examples/sources.json)

| 字段 | 应怎样理解和处理 | 出处 |
|---|---|---|
| `reasoning_content` | 本型号属于默认输出思考摘要的支持列表；它不是原始思考全过程，字符数不能当作实际思考 token 数 | [深度思考：回传思考内容加密原文][d-thinking] |
| `encrypted_content` | 服务端返回的加密思考原文。08 将完整 assistant 消息原样回传，不能裁剪、重新生成或只保留可见摘要 | [深度思考：回传思考内容加密原文][d-thinking] · [08 源码](examples/08_thinking_tools.py) |
| `usage.completion_tokens_details.reasoning_tokens` | 实际思考 token 的返回统计；摘要模式仍按原始思考 token 统计。未返回时按未知处理，不从摘要字数估算 | [深度思考：字段说明][d-thinking] · [03 源码](examples/03_thinking.py) |

工具调用使用 `tools[].type="function"`；`function.name` 标识函数，`description` 告诉模型用途，`parameters` 用 JSON Schema 描述 `type`、`properties`、`required` 等参数约束。05、08 的 `additionalProperties=False` 声明不接受额外参数；代码仍在本地验证函数名、JSON、类型和 ID 后才执行模拟函数。[Chat API：tools][d-api] · [05 源码](examples/05_tool_calling.py) · [08 源码](examples/08_thinking_tools.py)

`tool_choice` 在有工具时默认 `auto`，允许返回正文或工具调用；无工具时默认 `none`。当前05、08未显式设置它。工具返回结果要以 `role="tool"`、匹配的 `tool_call_id` 和结果字符串加入历史，再次调用模型。模型提出调用本身不表示应用函数已经执行。[Chat API：tool_choice/messages][d-api] · [函数调用：执行函数、回传结果][d-tools]

`tools.function.strict` 是工具参数的严格模式；04 中 `response_format.json_schema.strict=True` 则约束最终输出，两者位置与用途不同。05、08 没有传工具 `strict`，不能因 `parameters` 写了 Schema 就说已开启工具严格模式。[Chat API：tools.function.strict、response_format.json_schema.strict][d-api] · [05 源码](examples/05_tool_calling.py)

## JSON、图片、视频与流式选项

04 使用 `response_format.type="json_schema"`；`json_schema.name` 是格式名，`schema` 定义最终 JSON 对象，`strict=True` 要求严格遵循支持的 Schema。示例只定义布尔 `ok`，要求它存在、禁止额外字段，再在客户端检查 `ok is True`。这是本例业务条件，不是所有请求的固定字段；服务端 Schema 支持范围以官方关键字列表为准。[结构化输出：json_schema、严格模式、语法支持][d-json] · [04 源码](examples/04_json_output.py)

06 的图片块是 `{"type":"image_url","image_url":{"url":...}}`，`url` 可为服务端可访问地址或合规的 Base64 data URL。`IMAGE_URL`、`IMAGE_PATH` 是本地二选一输入；当前文件主动把本地格式缩小到 PNG/JPEG，不代表模型只支持这两类格式。[图片理解：URL、Base64][d-image] · [06 源码](examples/06_vision.py)

09 的视频块是 `{"type":"video_url","video_url":{"url":...}}`。它只发送地址，不传 `fps`、音频配置或 Files 预处理参数；本型号支持依据视频教程链接到的视觉能力型号表，不能把最新型号的专属预处理参数一并套入。[视频理解：支持模型、视频 URL 传入][d-video] · [模型列表：视觉理解能力][d-models] · [09 源码](examples/09_video.py)

`stream=True` 只改变传输方式，默认 `False`。本目录02未设置 `stream_options`；若另行设置 `stream_options.include_usage=True`，官方规定在 `[DONE]` 前增加一个 `choices=[]`、带总 `usage` 的块，默认 `False`。`chunk_include_usage=True` 则在各块给累计用量，默认也为 `False`；不要把多块累计值再逐块相加。[Chat API：stream、stream_options][d-api] · [02 源码](examples/02_streaming.py)

## 返回统计与本地变量

`usage.prompt_tokens`、`completion_tokens`、`total_tokens`、`prompt_tokens_details.cached_tokens` 都是响应统计，不是调用时必须填写的参数。10 的 `cached_tokens>0` 表示命中，`0` 表示本次未命中，缺失则无法判断；隐式缓存自动处理，相同前缀也不保证命中。[Chat API：usage][d-api] · [上下文缓存：隐式缓存][d-cache] · [10 源码](examples/10_implicit_cache.py)

`MAX_MODEL_TURNS=6`、`max_model_turns=6`、城市名校验中的80字符、`simulated=True`、缓存演示的80条资料和两次循环，都是本地教学逻辑。它们不是方舟请求字段、官方城市名上限或缓存必然命中的条件。[05 源码](examples/05_tool_calling.py) · [08 源码](examples/08_thinking_tools.py) · [10 源码](examples/10_implicit_cache.py)

[d-api]: https://docs.volcengine.com/docs/ark/chat-api?lang=zh
[d-models]: https://docs.volcengine.com/docs/ark/model-list?lang=zh
[d-sdk]: https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh
[d-context]: https://docs.volcengine.com/docs/ark/context-management?lang=zh
[d-thinking]: https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh
[d-tools]: https://docs.volcengine.com/docs/ark/function-calling?lang=zh
[d-json]: https://docs.volcengine.com/docs/ark/structured-output-beta?lang=zh
[d-image]: https://docs.volcengine.com/docs/ark/image-understanding?lang=zh
[d-video]: https://docs.volcengine.com/docs/ark/video-understanding?lang=zh
[d-cache]: https://docs.volcengine.com/docs/ark/context-cache?lang=zh
[sdk-timeouts]: https://developers.openai.com/api/reference/python#retries
