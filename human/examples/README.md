# 阅读模型调用代码并检查 Agent 实现

[人类篇](../README.md) · [English](README.en.md)

选择下面的型号，直接阅读完整可运行的 Python 代码、关键行解释、参数说明、运行方式和原始实测证据。既可以照着学习调用，也可以用来人工检查 Agent 的实现。

代码块逐字来自 models/ 下的规范文件，不是删掉校验的教学短片段；中英文展示同一份执行过的代码，保留原注释和提示词。核对的是型号身份、请求语义和结果验收，不要求变量名或封装完全一样。型号、参数、输入或协议改变后，需要验证改变后的路径。

## 按型号看完整代码

| 准确型号 | 代码与人工核对 |
|---|---|
| `deepseek-flash` | [DeepSeek](deepseek.md) |
| `kimi-k2.6` | [Kimi](kimi.md) |
| `glm-4.7` | [智谱 GLM](zhipu.md) |
| `qwen-flash` | [通义千问](qwen.md) |
| `doubao-seed-2-1-pro-260628` | [豆包](doubao.md) |
| `MiniMax-M2.7` | [MiniMax](minimax.md) |

## 运行前确认

按[验证与复现](../../docs/验证与复现.md)准备锁定环境，并在本地设置所列 Key 环境变量。阅读页面或运行生成器不会发请求；运行 Python 示例会真实调用并可能计费。独立示例不会自动加载根目录 .env。不要公开密钥，也不要用模板覆盖已有 .env。

## 检查 Agent 代码的清单

以下为项目人工验收建议：对照准确型号的参数页、官方来源和实际代码检查这些行为。人工看过代码不等于生产验收通过。

1. 身份与安全：准确型号、API 产品/地域、Key 变量对应；不硬编码或打印密钥，不静默回退免费型号。
2. 参数：分清 SDK 配置、模型请求和本地业务校验；输出预算不是上下文窗口设置，省略字段不是显式开关。思考和预算语义按准确型号查证。
3. 结果：检查正常结束、最终正文及适用的厂商业务状态；仅有思考、截断或待处理工具调用，都不是完整最终答案。
4. 证据：索要实际修改文件、运行命令与测试范围；离线 mock、HTTP 请求被接受、旧文件报告和 Agent 自称成功不是同一层证据。

[参数定义与官方出处](../../docs/参数说明与调参.md) · [证据与安全规则](../../docs/来源与核验规则.md)

## 继续检查进阶调用

- [流式](../../models/zhipu/glm-4.7/examples/02_streaming.py)：处理空 choices，检查正常结束和非空正文；finally 关闭流，消费中断后不自动重放。 [参数依据](../../models/zhipu/glm-4.7/parameters.md)
- [JSON](../../models/kimi/kimi-k2.6/examples/04_json_output.py)：检查该型号的 response_format 与提示词，先验收结束状态再解析 JSON，还要校验字段、类型及业务值。 [参数依据](../../models/kimi/kimi-k2.6/parameters.md)
- [工具闭环](../../models/zhipu/glm-4.7/examples/07_thinking_tools.py)：先整批校验名称、ID 与参数，再执行允许的工具；完整回传 assistant 和匹配 tool_call_id 的结果，限制轮数并取得最终答复。示例库存为模拟数据。 [参数依据](../../models/zhipu/glm-4.7/parameters.md)
- [图片](../../models/kimi/kimi-k2.6/examples/06_vision.py)：先确认准确型号与输入格式；本例读本地 PNG/JPEG 并构造 content 数组，不能把别家远程 URL 写法直接搬来。请求被接受不代表识别准确率已验证。 [参数依据](../../models/kimi/kimi-k2.6/parameters.md)

上述链接打开已有完整源文件，不是跨型号通用模板。运行前核对各自的逐文件状态和输入要求；基础示例的报告不覆盖任意进阶组合。

[逐文件实测状态](../../docs/示例实测状态.md) · [全部功能示例](../../docs/官方示例索引.md) · [页面生成器](../../scripts/render_human_examples.py)
