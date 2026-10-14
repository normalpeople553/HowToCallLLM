# 模型级说明书

[English](README.en.md) · [人类篇](../human/README.md)

本目录为每个可调用模型提供独立说明书与示例；机器可读事实仍以 [`skills/model-manual/references/models/`](../skills/model-manual/references/models/)为唯一来源。[仓库来源规则](../docs/来源与核验规则.md)

当前已完成：

- [DeepSeek `deepseek-flash`](deepseek/deepseek-flash/README.md)
- [Kimi `kimi-k2.6`](kimi/kimi-k2.6/README.md)
- [智谱 `glm-4.7-flash`](zhipu/glm-4.7-flash/README.md)（历史统一验证器报告为超时、限流和跳过；当前文件状态另见[示例实测状态](../docs/示例实测状态.md)）
- [通义千问 `qwen-flash`](qwen/qwen-flash/README.md)
- [豆包 `doubao-seed-2-1-pro-260628`](doubao/doubao-seed-2-1-pro-260628/README.md)（[官方列为往期模型](https://docs.volcengine.com/docs/ark/model-list?lang=zh)）
- [MiniMax `MiniMax-M2.7`](minimax/MiniMax-M2.7/README.md)（逐文件执行证据见[示例实测状态](../docs/示例实测状态.md)；[官方已公告退役](https://platform.minimax.cn/docs/guides/models-intro)）

每份模型说明书应包含身份与生命周期、接口配置、能力矩阵、限制、价格官方入口、普通与流式调用、思考模式、结构化输出、工具调用、多模态、错误处理和生产检查清单；厂商未明确说明的能力必须标为未知。[仓库来源规则](../docs/来源与核验规则.md)

跨模型的输出截断、思考 token、JSON、工具循环、流式解析与限流问题统一收录在[真实踩雷与生产检查](../docs/06-真实踩雷与生产检查.md)。

当前文件级结果见[示例实测状态](../docs/示例实测状态.md)，旧统一验证器的能力检查见[验证状态页](../docs/验证状态.md)；复制完整工具、图片和流式示例后，按[验证与复现](../docs/验证与复现.md)中的锁定环境运行。

按功能浏览[官方示例索引](../docs/官方示例索引.md)，或读取每个型号的 `examples/sources.json` 获取准确文件、官方来源、输入变量、运行命令、改写说明及文件级验证状态。该清单与历史型号验证报告分开维护；新文件不会自动继承旧报告的通过结果。
