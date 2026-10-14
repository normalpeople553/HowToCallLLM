# `glm-4.7` 调用说明书

[English](README.en.md) · [人类篇](../../../human/README.md) · [参数解释](parameters.md)

资料核对：2026-10-14。本目录维护智谱同代**付费**型号 `glm-4.7`，不是 `glm-4.7-flash`，也不自动换成最新一代。官方型号页与API枚举均列出该型号；定价页有非零计费条目，实际价格、阶梯及服务条款请直接查官方页面，不在仓库固定报价。[GLM-4.7][model] · [对话补全][api] · [官方价格][pricing]

## 1. 型号与接入边界

| 项目 | 已确认配置 | 出处 |
|---|---|---|
| 精确 Model ID | `glm-4.7` | [型号页][model]、[API枚举][api] |
| 标准API Base URL | `https://open.bigmodel.cn/api/paas/v4/` | [OpenAI兼容文档][sdk] |
| 本仓库密钥环境变量 | `ZHIPU_API_KEY`；官方示例也使用 `ZAI_API_KEY`，变量名是本地约定 | [官方兼容示例][sdk]、[01源码](examples/01_basic.py) |
| 输入 / 输出 | 文本 / 文本；不把通用API的视觉请求字段当成本型号图片能力 | [型号模态][model] |
| 上下文 / 最大输出 | 200K / 128K tokens；不是每次请求的实际生成量 | [型号页][model]、[参数概念][params] |
| 计费 | 付费；当前金额、缓存价和分档只链接官方 | [官方价格][pricing] |

此处使用标准按量API端点，不是Coding Plan专用接入地址。不要把另一产品端点或套餐权限混进固定配置。[OpenAI兼容文档][sdk] · [速率与套餐边界][rate]

机器卡片：[`glm-4.7.json`](../../../skills/model-manual/references/models/glm-4.7.json)。能力来源是官方文档；卡片的 `verification=null` / `not_run` 表示未登记该型号统一验证器报告，不替代逐文件实测状态。[机器卡片](../../../skills/model-manual/references/models/glm-4.7.json) · [证据规则](../../../docs/来源与核验规则.md)

## 2. 先运行原文件，再按参数页修改

从仓库根安装锁定依赖，设置 `ZHIPU_API_KEY` 后运行以下命令。命令会发送付费真实请求；本页只提供运行入口，不包含密钥。[依赖锁](../../../requirements-lock.txt) · [01源码](examples/01_basic.py)

```bash
python -m pip install -r requirements-lock.txt
python models/zhipu/glm-4.7/examples/01_basic.py
```

七个脚本都可独立运行，不依赖仓库测试辅助模块；每个都有 `main` 保护，导入时不创建客户端。源文件包含正常结束、非空正文及受限重试检查；自改片段或参数组合不自动继承原文件的实测结论。[源码与来源清单](examples/sources.json) · [证据规则](../../../docs/来源与核验规则.md)

| 示例 | 做什么 | 本地保护 |
|---|---|---|
| [01_basic.py](examples/01_basic.py) | 普通文本调用，思考开关采用型号默认 | 正常结束、非空正文 |
| [02_streaming.py](examples/02_streaming.py) | 关闭思考的流式输出 | 空choices、截断/断流、结束后正文检查；finally关闭流 |
| [03_thinking.py](examples/03_thinking.py) | 显式开启思考，区分思考与最终正文 | 不能只因产生思考就算完整回答 |
| [04_json_output.py](examples/04_json_output.py) | JSON Object模式 | 解析JSON，并验证只有布尔 `ok=true` |
| [05_tool_calling.py](examples/05_tool_calling.py) | 关闭思考的模拟天气工具闭环 | 最多六次逻辑模型调用；工具参数整批验证 |
| [06_multi_turn.py](examples/06_multi_turn.py) | 客户端携带完整历史的两轮对话 | 只将完整回答写入后续历史；预算4096 |
| [07_thinking_tools.py](examples/07_thinking_tools.py) | 交错思考与模拟库存工具闭环 | 完整保留assistant；最多四次逻辑模型调用；预算16384 |

功能与实际字段逐一对应见[参数解释与文件映射](parameters.md)，官方出处、改写点、运行命令和文件级验证见[唯一来源清单](examples/sources.json)。[跨型号示例索引](../../../docs/官方示例索引.md)只用于导航，不额外扩大本型号能力。

## 3. 思考、JSON与工具的重点

`glm-4.7` 默认开启思考；可用 `thinking.type=disabled` 关闭。Python SDK通过 `extra_body` 将该对象送入HTTP顶层，不发送名为extra_body的外层API字段。[思考模式][thinking] · [兼容示例][sdk]

开启“思考 + 工具”时，必须回传完整、未修改的 `reasoning_content`，连同原assistant的 `tool_calls`、匹配的工具结果一起继续调用。07保留完整序列化消息；它没有显式设置 `clear_thinking=false`，因此不宣称开启跨用户轮的Preserved Thinking。[官方思考规则][thinking] · [07源码](examples/07_thinking_tools.py)

JSON模式是 `response_format={"type":"json_object"}`，仍需客户端校验。工具 `parameters` 用JSON Schema描述参数，不等于已开启服务端 `strict`；当前文本请求schema只列 `tool_choice="auto"`，不擅自添加 `required`、强制命名工具或 `json_schema` 输出。[结构化输出][json] · [官方OpenAPI][openapi] · [参数边界](parameters.md)

天气和库存函数都是固定**教学模拟数据**，不会访问真实天气/库存系统。先验证全批函数名、参数与调用ID，再执行本地函数、回传 `tool_call_id`，最后必须得到正文；直接回答而未执行工具不算闭环。[05源码](examples/05_tool_calling.py) · [07源码](examples/07_thinking_tools.py)

## 4. 限流、安全与复现

所有脚本关闭SDK自动重试，只对HTTP 429且业务码 `1302`（账户速率）或 `1305`（服务过载）最多尝试三次。1秒/2秒指数延时加不超过0.25秒抖动、单次等待30秒上限是项目策略；有有效 `Retry-After` 时不提前重试，超出上限则停止，稍后再运行。[本地实现](examples/01_basic.py) · [官方错误码][errors] · [SDK重试说明][sdk-retries]

429也可能是欠费 `1113`、额度 `1308`、套餐到期或权限等问题，不能一律重试或解释成能力不支持。工具循环只重试当前模型HTTP请求，不重执行已完成的本地工具；流一旦开始消费，断流后不自动重放，且始终关闭响应。[官方错误分类][errors] · [05源码](examples/05_tool_calling.py) · [02源码](examples/02_streaming.py)

示例会在终端展示答案，03也会展示思考；不要把这些私文、密钥或原始错误提交到公开报告。请求异常使用固定脱敏提示，用量只输出已知的数字token计数。[03源码](examples/03_thinking.py) · [本地用量与错误处理](examples/01_basic.py) · [证据规则](../../../docs/来源与核验规则.md)

## 5. 证据不跨型号继承

当前付费型号的逐文件执行状态只看[示例实测状态](../../../docs/示例实测状态.md)和[本目录sources.json](examples/sources.json)指向的、匹配当前源码/输入/参数/环境的报告。离线mock只证明本地协议与保护逻辑，不证明真实托管API成功，也不证明任意提示词的语义正确率。[来源与核验规则](../../../docs/来源与核验规则.md)

免费Flash的[旧报告](../glm-4.7-flash/verification/2026-10-13.json)和[旧严格报告](../glm-4.7-flash/verification/2026-10-13-strict.json)原地保留，仅解释旧型号历史，不是 `glm-4.7` 的验证。历史统一流程与当前逐文件结果分别查[统一状态](../../../docs/验证状态.md)及[逐文件状态](../../../docs/示例实测状态.md)。复现环境见[验证与复现](../../../docs/验证与复现.md)，生产检查见[真实踩雷](../../../docs/06-真实踩雷与生产检查.md)。

[model]: https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7
[api]: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
[sdk]: https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
[pricing]: https://docs.bigmodel.cn/cn/guide/start/pricing
[params]: https://docs.bigmodel.cn/cn/guide/start/concept-param
[thinking]: https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
[json]: https://docs.bigmodel.cn/cn/guide/capabilities/struct-output
[openapi]: https://docs.bigmodel.cn/openapi/openapi.json
[errors]: https://docs.bigmodel.cn/cn/api/api-code
[rate]: https://docs.bigmodel.cn/cn/api/rate-limit
[sdk-retries]: https://developers.openai.com/api/reference/python#retries
