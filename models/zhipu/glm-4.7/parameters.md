# `glm-4.7` 参数解释

[English](parameters.en.md) · [人类篇](../../../human/README.md) · [型号说明书](README.md)

核对日期：2026-10-14。此页解释[七个独立可运行源文件](examples/sources.json)的实际字段及未使用字段的边界；不是任意参数组合均通过的承诺。调用文件见[代码目录](../../../docs/示例实测状态.md)。本型号为付费文本模型；金额直接查[官方价格][pricing]，不继承免费Flash的配置默认或验证结果。[GLM-4.7][model] · [证据规则](../../../docs/来源与核验规则.md)

## 1. 文件与实际参数映射

所有脚本均使用 `model="glm-4.7"`、`messages`；SDK配置为环境变量 `ZHIPU_API_KEY`、Base URL `https://open.bigmodel.cn/api/paas/v4/`、`timeout=120`、`max_retries=0`。所有脚本均未发送 `temperature`、`top_p`、`do_sample`、`reasoning_effort`、`stream_options`、`tool_stream` 或 `clear_thinking`。[七个源文件与运行清单](examples/sources.json)

| 可运行文件 | 公共字段以外的实际API参数 | 对应解释与本地校验 |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | 未传 `thinking` / `max_tokens`，采用型号默认 | 第3、4、5节；正常结束且有最终正文 |
| [02_streaming.py](examples/02_streaming.py) | `stream=True`；`thinking.type="disabled"` | 第5、6节；空choices处理、结束状态和finally关闭 |
| [03_thinking.py](examples/03_thinking.py) | `thinking.type="enabled"` | 第4、5、8节；分别展示思考与最终正文 |
| [04_json_output.py](examples/04_json_output.py) | `response_format={"type":"json_object"}`；关闭思考 | 第7节；提示词要求JSON，并验证布尔 `ok=true` |
| [05_tool_calling.py](examples/05_tool_calling.py) | `tools` 声明 `get_weather(city)`；关闭思考；未传 `tool_choice` / `max_tokens` | 第7、9节；最多六次逻辑模型调用、模拟天气、整批校验后执行 |
| [06_multi_turn.py](examples/06_multi_turn.py) | 完整历史 `messages`；关闭思考；`max_tokens=4096` | 第3、4节；两轮固定问题，只保留完整回答 |
| [07_thinking_tools.py](examples/07_thinking_tools.py) | `tools` 声明 `get_inventory(sku)`；`tool_choice="auto"`；开启思考；`max_tokens=16384` | 第4、5、7、9节；最多四次逻辑模型调用、完整回传思考与模拟库存 |

01–05未显式设置输出预算；06的4096和07的16384是项目选择，不是型号上限或默认。每个文件都包含自身的有限退避函数，无需导入测试或其它示例文件。[01](examples/01_basic.py) · [06](examples/06_multi_turn.py) · [07](examples/07_thinking_tools.py)

## 2. SDK设置与模型生成参数分开理解

| 字段 | 用途和当前设置 | 出处 |
|---|---|---|
| `api_key` / `ZHIPU_API_KEY` | 客户端鉴权；仓库变量名与官方示例的 `ZAI_API_KEY` 不同，但变量名不改变认证协议 | [兼容文档][sdk]、[01源码](examples/01_basic.py) |
| `base_url` | 标准服务根地址，不是模型生成字段；不要替换成另一产品的Coding Plan端点 | [兼容文档][sdk]、[速率/套餐边界][rate] |
| `timeout=120` | SDK网络超时，单位秒；本地选择，不是token预算、整个工具任务的总截止时间或保证120秒内生成完 | [SDK超时与重试][sdk-retries]、[01源码](examples/01_basic.py) |
| `max_retries=0` | 禁用SDK自动重试，避免和本地退避相乘；SDK默认对部分连接错误、408/409/429/5xx重试两次 | [官方SDK说明][sdk-retries]、[01源码](examples/01_basic.py) |
| `extra_body` | SDK额外JSON字段容器；例如 `extra_body={"thinking":{"type":"disabled"}}` 合并为HTTP顶层 `thinking`，不是名为extra_body的服务端模型参数 | [兼容文档：思考示例][sdk] |

### 本地重试，不是服务端参数

`create_with_backoff` 是本项目函数名。仅HTTP 429且 `error.code` 为 `1302` 或 `1305` 时重试；一次逻辑调用最多三次HTTP尝试。其余错误（含未知429）停止并给固定脱敏提示，不输出原响应、原始错误或密钥。[01源码](examples/01_basic.py) · [官方错误码][errors]

`1113` 也是429，但表示欠费；`1308` 表示使用上限，`1309` 表示套餐到期，不能当成几秒后必然恢复的速率限制。脚本未为它们循环请求。[官方错误码][errors] · [速率限制][rate]

等待使用1秒、2秒指数退避，加 `[0,0.25]` 秒随机抖动；有效 `Retry-After`（秒数或HTTP日期）作为最小等待，超过30秒则立即退出，稍后另行运行，不把它截短到30秒继续请求。这些次数和等待上限是本地策略，不是平台承诺的恢复时间。[01源码](examples/01_basic.py) · [SDK服务端重试指引][sdk-rate]

重试只围绕当前模型HTTP请求。05/07已执行的模拟工具不会因后续模型429而重执行；02只在建立流之前重试，消费流后异常不自动重放。逻辑模型轮数与HTTP尝试数不同，不能把六轮工具循环理解为总共最多六次网络请求。[02](examples/02_streaming.py) · [05](examples/05_tool_calling.py) · [07](examples/07_thinking_tools.py)

## 3. 身份、消息与采样

| API字段 | 含义、范围和默认 | 出处 |
|---|---|---|
| `model` | 必填的精确模型代码，本目录固定 `glm-4.7`；不是Flash、不是自动选择最新型号 | [API枚举][api]、[型号][model] |
| `messages` | 按时间顺序传入当前请求的完整历史；不能仅有system/assistant消息 | [API：messages][api] |
| `messages[].role` | `system`设定行为；`user`为输入；`assistant`为模型回复；`tool`为工具执行结果 | [API：消息角色][api] |
| `messages[].content` | 此型号使用文本。共享API中的视觉内容块不构成本型号图片/视频输入支持证据 | [文本模态][model]、[请求分类][api] |
| `temperature` | 采样随机性，范围 `[0,1]`、最多两位小数；本型号默认 `1.0`。高值更发散，低值更集中，不等于事实准确率控制器 | [API文本temperature][api]、[核心概念][params] |
| `top_p` | 从累计概率达到阈值的候选集合采样；范围 `[0.01,1]`、最多两位小数；默认 `0.95`。与温度不同，它缩小候选集合；官方建议二选一调整 | [API文本top_p][api]、[核心概念][params] |
| `do_sample` | 默认 `true`；`false` 采用贪心策略，此时temperature/top_p被忽略。示例未传，不是提示词中的“请准确回答” | [API：do_sample][api]、[核心参数][params] |

这些采样字段没有被本目录脚本发送，因此原文件的运行结果不能作为手动加温度或关闭采样后同一请求的通过证明。本项目建议先保留原请求，再逐项更改并重新核验；温度不是JSON结构或事实正确性的保证。[实际字段清单](examples/sources.json) · [证据规则](../../../docs/来源与核验规则.md)

## 4. 上下文、输出上限与生成预算

| 概念或字段 | 本型号的确认值和边界 | 出处 |
|---|---|---|
| 上下文窗口 | 200K，包含输入与生成内容；历史消息、工具说明也占输入空间 | [型号页][model]、[上下文概念][params]、[messages/tools][api] |
| 最大输出 | 128K，是型号能力上限，不是每次自动输出长度 | [型号页][model] |
| `max_tokens` | 正整数，文本schema范围 `1–131072`；限制生成而不包括输入。达到限制可能截断 | [API：max_tokens][api]、[核心参数][params] |
| 省略时默认 | `glm-4.7` 的官方默认表明确为 `65536`，最大 `131072`。此结论针对付费精确型号，不是继承Flash默认 | [核心参数：默认值表][params] |
| 本地预算 | 06传4096，07传16384；01–05省略。不是上下文窗口，也不保证得到同长度最终正文 | [06](examples/06_multi_turn.py)、[07](examples/07_thinking_tools.py) |
| 思考与正文的细分 | 所读型号参数未明确精确说明二者如何共享 `max_tokens`；保留**未知**，不套用另一厂商同名字段语义 | [max_tokens/thinking][api]、[核心参数][params] |

无论预算大小都检查 `finish_reason` 和最终正文；`length` 不是完整成功，增加生成预算也不能消除已超上下文的历史。此处是项目根据两个独立限制设置的校验，不把最大输出当作可用输入窗口。[上下文与输出概念][params] · [01](examples/01_basic.py)

## 5. 思考、历史保留与未确认字段

`thinking.type` 为 `enabled/disabled`，GLM-4.7默认开启，允许关闭。01省略开关不代表关闭；03、07显式开启，02、04、05、06关闭。开启后本型号执行思考；不能把GLM-5.3“不能关闭”的规则搬来。[思考模式][thinking] · [核心参数：thinking][params] · [官方OpenAPI：ChatThinking][openapi]

`reasoning_content` 是assistant返回的思考文本。交错思考工具循环要求完整、原样回传该字段，和原 `tool_calls` 一起发送；07使用 `message.model_dump(exclude_none=True)`，不是把思考改写或总结成另一段文字。[思考模式：交错思考][thinking] · [07](examples/07_thinking_tools.py)

`thinking.clear_thinking` 控制是否清除前面用户轮的思考，标准API默认 `true`；`false` 要求完整、未修改、按原顺序携带历史reasoning以启用Preserved Thinking。它不改变当前轮是否思考。07未发送此字段，因此不宣称已开启跨用户轮的思考保留。[思考模式：保留式思考][thinking] · [ChatThinking.clear_thinking][openapi] · [07](examples/07_thinking_tools.py)

`reasoning_effort` 当前文档仅适用于GLM-5.2及以上，不给GLM-4.7增加 `low/high/max` 档位；`encrypted_content` 的本型号输入约定也未核实，保留未知，不复制其它厂商的加密思考字段。[核心参数][params] · [思考规则][thinking]

## 6. 流式与完成判定

`stream` 默认 `false`，为 `true` 时通过SSE返回delta，并在结束时发送 `[DONE]`。02关闭思考、累积 `delta.content`，允许空choices/usage-only块；接受一个正常 `stop` 且有最终正文，不接受缺失结束状态、`length`、安全中断、网络异常、重复结束、结束后正文或未处理的工具delta。[API：stream和返回结构][api] · [02](examples/02_streaming.py)

`finish_reason="tool_calls"` 只允许进入已实现的工具处理路径，不是最终正文成功。所有非工具示例必须正常结束；工具参数未正常结束时不执行本地函数。这是本地完整性策略，不是SDK自动替用户校验。[官方返回schema][openapi] · [05](examples/05_tool_calling.py)

02不发送 `stream_options.include_usage`；所读文本请求schema未列该扩展，本型号支持范围保留未知。API列出 `tool_stream` 可控制工具调用流式输出，但当前02不演示工具流，05/07则使用非流式工具循环；不从普通文本流推断工具流已经实测。[文本请求schema][openapi] · [API：tool_stream][api] · [实际清单](examples/sources.json)

流消费阶段任何异常均不重放，`finally` 尝试关闭响应；已展示的片段只作为部分结果，不能因进程曾输出文字就标为成功。[02源码](examples/02_streaming.py)

## 7. 函数工具与JSON输出

| 字段 | 含义和本目录用法 | 出处 |
|---|---|---|
| `tools[].type` | `function` 表示函数工具；文本API最多128个函数，本例只注册一个 | [API/OpenAPI工具schema][openapi] |
| `function.name` | 函数名；API允许字母、数字、下划线/短横线，1–64字符。本地只允许声明的天气或库存函数 | [FunctionObject][openapi]、[05](examples/05_tool_calling.py)、[07](examples/07_thinking_tools.py) |
| `description` | 告知模型用途，不会自己执行函数 | [FunctionObject][openapi] |
| `parameters` | JSON Schema参数说明；本例使用 `type/properties/required/additionalProperties`，客户端仍检查JSON、字段与业务边界 | [FunctionParameters][openapi]、[05](examples/05_tool_calling.py) |
| `tool_choice` | 文本schema仅列 `auto`，默认也是auto；模型自行决定是否提调用。07显式传，05省略；不添加required/none/强制命名调用 | [ChatCompletionTextRequest.tool_choice][openapi] |
| `role="tool"` / `tool_call_id` / `content` | 把本地函数的字符串结果与原调用ID匹配回传，然后再次请求模型 | [消息协议][api]、[思考工具示例][thinking] |
| `response_format` | 默认text；04传 `{"type":"json_object"}` 并在提示词要求JSON。客户端解析后检查只有布尔 `ok=true` | [API][api]、[结构化输出][json]、[04](examples/04_json_output.py) |

工具schema中的 `additionalProperties=False` 是对预期参数对象的描述，示例本地也明确拒绝额外字段。它不等于服务端 `tools.function.strict`。当前FunctionObject未列strict，文本response_format只列text/json_object；教程中的客户端jsonschema验证不证明服务端json_schema或strict支持，本目录均不发送。[官方schema][openapi] · [结构化输出：Schema验证][json] · [05](examples/05_tool_calling.py)

工具参数批次全部验证成功才执行函数；跨轮ID去重，达到最后模型轮时不再执行无法回传的工具。必须至少执行一次示例工具并获得正常非空最终正文才算完成教学闭环。[05](examples/05_tool_calling.py) · [07](examples/07_thinking_tools.py)

## 8. 返回统计、图片与其它端点边界

`usage.prompt_tokens/completion_tokens/total_tokens` 是服务端返回统计，不是请求生成参数。示例仅打印这三项中的整数，03另显示 `reasoning_content`；思考字符数不能换算成实际计费token。不要把私有回答或思考放进公开报告。[API返回usage][api] · [01](examples/01_basic.py) · [03](examples/03_thinking.py) · [证据规则](../../../docs/来源与核验规则.md)

若响应包含 `usage.prompt_tokens_details.cached_tokens`，它是缓存命中统计；相同前缀由平台识别，不是必填缓存输入。本目录没有缓存专门示例，不承诺短提示重复两次必然命中。[上下文缓存][cache] · [未集成功能](examples/sources.json)

官方精确型号页声明文本输入/输出，所以这里不提供图片URL、`file_id`、`detail`、视频或音频输入教程。通用API、其它GLM视觉型号的字段不是本型号能力证据。Responses、FIM及Beta端点也不是本目录已集成或实测的接口，不移植别家字段。[型号模态][model] · [API请求分类][api] · [范围清单](examples/sources.json)

## 9. 本地教学数据与循环上限

05的城市名1–80字符检查、固定“晴”、07的 `SKU-001`、库存7件和需求5件、`simulated=True` 都是项目教学数据与保护，不是平台的城市/SKU限制或真实业务信息。[05](examples/05_tool_calling.py) · [07](examples/07_thinking_tools.py)

05最多六次、07最多四次逻辑模型调用；06恰好两轮。工具调用ID集合、执行计数、JSON字段校验、每请求最多三次限流尝试、等待30秒上限、`main` 守卫和 `stream.close()` 都是本地逻辑，不是模型生成参数或任何组合的成功保证。[05](examples/05_tool_calling.py) · [06](examples/06_multi_turn.py) · [07](examples/07_thinking_tools.py) · [02](examples/02_streaming.py)

继续阅读：[通用参数导航](../../../docs/参数说明与调参.md) · [验证与复现](../../../docs/验证与复现.md) · [证据规则](../../../docs/来源与核验规则.md)。

[model]: https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7
[pricing]: https://docs.bigmodel.cn/cn/guide/start/pricing
[api]: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
[openapi]: https://docs.bigmodel.cn/openapi/openapi.json
[sdk]: https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
[params]: https://docs.bigmodel.cn/cn/guide/start/concept-param
[thinking]: https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
[json]: https://docs.bigmodel.cn/cn/guide/capabilities/struct-output
[cache]: https://docs.bigmodel.cn/cn/guide/capabilities/cache
[errors]: https://docs.bigmodel.cn/cn/api/api-code
[rate]: https://docs.bigmodel.cn/cn/api/rate-limit
[sdk-retries]: https://developers.openai.com/api/reference/python#retries
[sdk-rate]: https://developers.openai.com/api/docs/guides/rate-limits
