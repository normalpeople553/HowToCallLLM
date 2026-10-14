# `glm-4.7-flash` 参数解释

核对日期：2026-10-14。本页解释[本目录七个示例](examples/sources.json)的实际字段，不代表所有文件已经真实调用成功；运行状态另查[示例实测状态](../../../docs/示例实测状态.md)。本型号官方输入、输出模态均为文本，上下文为200K，最大输出128K。[GLM-4.7-Flash 型号页][z-model]

## 文件与实际参数映射

所有文件都用 `model="glm-4.7-flash"`、`messages`、SDK `base_url="https://open.bigmodel.cn/api/paas/v4/"`、`timeout=120`，从环境变量 `ZHIPU_API_KEY` 读取密钥。01–05未显式设置 `max_tokens`；所有文件均未设置 `temperature`、`top_p`、`stream_options` 或 `reasoning_effort`。[01 源码](examples/01_basic.py) · [02 源码](examples/02_streaming.py) · [03 源码](examples/03_thinking.py) · [04 源码](examples/04_json_output.py) · [05 源码](examples/05_tool_calling.py) · [06 源码](examples/06_multi_turn.py) · [07 源码](examples/07_thinking_tools.py)

| 文件 | 公共字段以外的实际 API 参数 | SDK 或本地逻辑 |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | 未传 `thinking`，采用型号默认 | 检查 `finish_reason` 和非空正文 |
| [02_streaming.py](examples/02_streaming.py) | `stream=True`；`thinking.type="disabled"` | 拼接流式正文，检查结束状态 |
| [03_thinking.py](examples/03_thinking.py) | `thinking.type="enabled"` | 区分 `reasoning_content` 和最终正文 |
| [04_json_output.py](examples/04_json_output.py) | `response_format.type="json_object"`；关闭思考 | 提示词要求 JSON，客户端检查布尔 `ok=true` |
| [05_tool_calling.py](examples/05_tool_calling.py) | `tools` 定义 `get_weather(city)`；关闭思考；未传 `tool_choice` | 六轮上限，执行模拟天气函数并回传结果 |
| [06_multi_turn.py](examples/06_multi_turn.py) | `messages` 含完整历史；关闭思考；`max_tokens=4096` | 两轮固定对话；SDK `max_retries=0` |
| [07_thinking_tools.py](examples/07_thinking_tools.py) | `tools` 定义 `get_inventory(sku)`；`tool_choice="auto"`；开启思考；`max_tokens=16384` | 四轮上限，完整回传思考和模拟库存；SDK `max_retries=0` |

此表的数值、函数名与校验条件来自对应源文件，是项目示例约定。接口字段以[对话补全 API][z-api]为准；原始 HTTP 的思考字段位于顶层 `thinking`，Python 示例则通过 SDK 的 `extra_body` 传入。[官方 OpenAI 兼容示例][z-sdk]

## SDK 设置与模型参数分开理解

| 字段或变量 | 用途、当前值与默认处理 | 出处 |
|---|---|---|
| `api_key` / `ZHIPU_API_KEY` | 客户端鉴权配置；`ZHIPU_API_KEY` 是本仓库变量名，官方兼容示例也使用 `ZAI_API_KEY`，变量名本身不改变服务协议 | [OpenAI 兼容说明][z-sdk] · [01 源码](examples/01_basic.py) |
| `base_url` | 服务根地址，示例使用 `https://open.bigmodel.cn/api/paas/v4/`；不是语言模型生成参数 | [OpenAI 兼容说明][z-sdk] |
| `timeout=120` | SDK 网络请求超时设置，单位秒；120是本地选择，不是token预算或服务端承诺的完成时间 | [01 源码](examples/01_basic.py) · [OpenAI 官方 SDK 超时说明][sdk-timeouts] |
| `max_retries` | SDK 自动重试配置；06、07显式设置0，其余未显式设置。官方 SDK 默认对部分连接错误及 408、409、429、5xx 等重试两次；不要把外层循环次数当作实际HTTP尝试次数 | [06 源码](examples/06_multi_turn.py) · [07 源码](examples/07_thinking_tools.py) · [OpenAI 官方超时与重试说明][sdk-timeouts] |
| `extra_body` | OpenAI Python SDK合并额外JSON字段的容器；`extra_body={"thinking":{"type":"disabled"}}` 的实际API字段是顶层 `thinking` | [OpenAI 兼容说明：深度思考示例][z-sdk] |

## 文本、采样和默认值

| API字段 | 用途、范围及默认 | 本型号的解释与出处 |
|---|---|---|
| `model` | 必填模型代码；本目录固定 `glm-4.7-flash` | 不是网页展示名称，也不自动选择其它GLM；[对话补全API：model][z-api] |
| `messages` | 按顺序传入当前问题和历史；角色为 `system/user/assistant/tool` | 不仅是最后一句问题；不能只包含系统或助手消息；[对话补全API：messages][z-api] |
| `messages[].content` | 本型号使用文本字符串 | API总接口存在其它视觉模型的内容块，不代表 `glm-4.7-flash` 支持图片或视频；[型号页：文本输入][z-model] · [对话补全API：文本/视觉请求区分][z-api] |
| `temperature` | 控制采样随机性；范围 `[0,1]`、最多两位小数。GLM-4.7系列文档默认 `1.0` | 高一些更发散，低一些更集中；当前示例不传，本页不另设Flash专属默认；[API文本请求：temperature][z-api] |
| `top_p` | 控制候选token累计概率阈值；范围 `[0.01,1]`、最多两位小数。GLM-4.7系列文档默认 `0.95` | 低一些缩小候选范围，高一些增加多样性；建议与 `temperature` 二选一调整；[API文本请求：top_p][z-api] |
| `do_sample` | 是否采样，默认 `true`；若设 `false` 使用贪心策略 | 当前示例未设置；它和提示词中的“请准确回答”不是同一层控制；[核心参数：do_sample][z-params] |

本项目使用建议：先保留示例默认；需要更多表达变化时再调整采样，需要机器可处理结果时定义JSON格式并做字段校验，不把温度当作输出结构约束。[核心参数：采样][z-params] · [结构化输出][z-json]

## 型号窗口与单次生成预算

| 概念或字段 | 已核对含义与边界 | 出处 |
|---|---|---|
| 上下文窗口 | 本型号200K，包含一次请求处理的输入和生成内容；历史消息、工具说明都需要纳入输入规划 | [型号页][z-model] · [核心参数：上下文窗口][z-params] · [API：messages/tools][z-api] |
| 型号最大输出 | 本型号128K；这是能力上限，不是每次自动生成长度 | [型号页：最大输出Tokens][z-model] |
| `max_tokens` | 正整数，文本请求schema最大 `131072`；限制单次生成token，不包括输入，达到限制时可能截断 | [API文本请求：max_tokens][z-api] · [核心参数：max_tokens][z-params] |
| 本型号默认预算 | 官方默认值表列了 `glm-4.7`，未单列 `glm-4.7-flash`；型号页例子里的65536是示例参数。本页不把它写成Flash独立默认值，省略时的精确默认保留未知 | [核心参数：各型号默认值表][z-params] · [型号页：调用示例][z-model] |
| 本例请求值 | 06设置4096，07设置16384，其余未设置；这些数不是上下文窗口，也不保证得到同长度正文 | [06 源码](examples/06_multi_turn.py) · [07 源码](examples/07_thinking_tools.py) |
| 思考与预算细分 | 本次读取的本型号参数说明没有单独明确“思考与正文如何共享 `max_tokens`”的精确规则，保留未知；不要把别家同名字段语义套来 | [API：max_tokens/thinking][z-api] · [核心参数][z-params] |

因此，程序仍要检查 `finish_reason`、最终正文和返回用量；增加生成预算也不能解决已经超出上下文窗口的历史输入。这是本项目根据两个独立限制采用的处理方式。[核心参数：max_tokens、上下文窗口][z-params] · [07 源码](examples/07_thinking_tools.py)

## 思考、保留历史和流式

`thinking.type` 取 `enabled/disabled`，GLM-4.7系列默认开启；该型号可以在请求中关闭。01省略开关不代表不思考；03、07显式开启，02、04、05、06显式关闭。不能把GLM-5.3系列“强制思考不可关闭”的限制套在本型号上。[思考模式：默认思考行为][z-thinking] · [API：ChatThinking][z-api] · [示例清单](examples/sources.json)

在“思考 + 工具”循环中，应把历史 `reasoning_content` 连同完整assistant消息回传；07的 `message.model_dump(exclude_none=True)` 用于序列化消息，保留原有思考及工具调用，没有把思考重新总结成自己的文字。[思考模式：交错式思考][z-thinking] · [07 源码](examples/07_thinking_tools.py)

本次该型号官方示例要求保留的是 `reasoning_content`；未核实该型号的 `encrypted_content` 输入约定，标记未知，不把豆包的加密思考字段要求直接套在这里。[思考模式][z-thinking] · [API：思考消息][z-api]

`thinking.clear_thinking` 控制是否清除先前用户回合的思考，标准API默认 `true`；要启用保留式思考可设 `false` 并完整、按原顺序回传思考。它不等于当前轮的思考开关。当前07没有显式传 `clear_thinking`，不能宣称已经开启跨回合的Preserved Thinking。[思考模式：保留式思考][z-thinking] · [API：ChatThinking.clear_thinking][z-api] · [07 源码](examples/07_thinking_tools.py)

`reasoning_effort` 不是本目录使用的参数；当前核心参数文档把它的适用范围写为GLM-5.2及以上，本页不为 `glm-4.7-flash` 增添 `low/high/max` 档位。[核心参数：reasoning_effort][z-params]

`stream` 默认 `false`，设为 `true` 后通过SSE逐块返回 `delta`，不改变所选模型与预算。02未发送 `stream_options`；当前官方文本请求schema也未列出 `stream_options.include_usage`，本型号该扩展的支持范围保留未知，不直接复制其它厂商配置。[API：ChatCompletionTextRequest.stream][z-api] · [官方OpenAPI文本请求schema][z-openapi] · [02 源码](examples/02_streaming.py)

## 工具参数和JSON输出

`tools` 是函数说明，当前05使用 `get_weather(city)`，07使用 `get_inventory(sku)`。`type="function"` 声明函数工具；`function.name` 是函数名，`description` 供模型判断用途，`parameters` 以JSON Schema描述参数，使用 `type/properties/required/additionalProperties`。API文本请求最多支持128个函数，示例各只注册一个。[API：tools、FunctionObject、FunctionParameters][z-api] · [05 源码](examples/05_tool_calling.py) · [07 源码](examples/07_thinking_tools.py)

当前官方文本请求 `tool_choice` 仅列 `auto`，含义是模型自行决定是否提出函数调用，默认也是 `auto`。07显式传它，05省略；本页不推荐把命名强制调用、`required` 或 `none` 当成本型号已确认取值。[API：ChatCompletionTextRequest.tool_choice][z-api] · [官方OpenAPI][z-openapi]

工具调用结果需用 `role="tool"`、匹配的 `tool_call_id`、字符串 `content` 回传；随后再次请求模型，才有机会得到完整最终正文。函数名、工具参数JSON、字段类型和业务允许范围由本地执行器验证，模型返回 `tool_calls` 不表示函数已经执行。[API：工具消息][z-api] · [思考模式：工具示例][z-thinking] · [05 源码](examples/05_tool_calling.py)

04的 `response_format={"type":"json_object"}` 要求JSON格式，提示词再说明期望结构，客户端仍检查 `ok` 必须为布尔 `true`。当前官方文本schema列的是 `text/json_object`；文档中“JSON Schema验证”示例使用客户端 `jsonschema` 校验，不代表本型号已支持服务端 `response_format.type="json_schema"` 或 `strict=True`。[API：response_format][z-api] · [结构化输出：Schema验证][z-json] · [04 源码](examples/04_json_output.py)

同理，工具的 `parameters` 使用JSON Schema不等于开启服务端 `tools.function.strict`。当前函数schema未列该参数，本目录也没有发送它；不能把豆包示例里的严格模式直接移植到这里。[官方OpenAPI：FunctionObject][z-openapi] · [07 源码](examples/07_thinking_tools.py)

## 返回统计与本地变量

`usage` 是响应统计，`reasoning_content` 是返回的思考内容；它们不是用户必须填写的请求参数，思考文本的字符数也不是服务端token统计。本目录03显示文本，06、07打印原始 `usage`，不会从字符数换算思考token。[API：响应消息、usage][z-api] · [03 源码](examples/03_thinking.py) · [06 源码](examples/06_multi_turn.py) · [07 源码](examples/07_thinking_tools.py)

若响应包含 `usage.prompt_tokens_details.cached_tokens`，它是缓存命中的返回统计，不是必填缓存输入；具体命中由平台识别相同前缀。本目录没有缓存专门示例，也不承诺重复一条短提示就一定命中。[上下文缓存][z-cache] · [示例清单](examples/sources.json)

05的六轮循环、07的四轮循环、`SKU-001`、库存7件、需求5件、`simulated=True`、城市名80字符校验都是本地教学数据或执行保护，不是API字段，也不是官方库存或城市限制。[05 源码](examples/05_tool_calling.py) · [07 源码](examples/07_thinking_tools.py)

[z-model]: https://docs.bigmodel.cn/cn/guide/models/free/glm-4.7-flash
[z-api]: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
[z-openapi]: https://docs.bigmodel.cn/openapi/openapi.json
[z-sdk]: https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
[z-params]: https://docs.bigmodel.cn/cn/guide/start/concept-param
[z-thinking]: https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
[z-json]: https://docs.bigmodel.cn/cn/guide/capabilities/struct-output
[z-cache]: https://docs.bigmodel.cn/cn/guide/capabilities/cache
[sdk-timeouts]: https://developers.openai.com/api/reference/python#retries
