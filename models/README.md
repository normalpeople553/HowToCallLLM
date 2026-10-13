# 模型级说明书

本目录为每个可调用模型提供独立说明书与示例；机器可读事实仍以 [`skills/model-manual/references/models/`](../skills/model-manual/references/models/)为唯一来源。[仓库来源规则](../docs/来源与核验规则.md)

当前已完成：

- [DeepSeek `deepseek-flash`](deepseek/deepseek-flash/README.md)
- [Kimi `kimi-k2.6`](kimi/kimi-k2.6/README.md)
- [智谱 `glm-4.7-flash`](zhipu/glm-4.7-flash/README.md)（本次实测受 429 限流，文档能力与实测状态分开标注）
- [通义千问 `qwen-flash`](qwen/qwen-flash/README.md)
- [豆包 `doubao-seed-2-1-pro-260628`](doubao/doubao-seed-2-1-pro-260628/README.md)（官方列为往期模型）

每份模型说明书应包含身份与生命周期、接口配置、能力矩阵、限制、价格官方入口、普通与流式调用、思考模式、结构化输出、工具调用、多模态、错误处理和生产检查清单；厂商未明确说明的能力必须标为未知。[仓库来源规则](../docs/来源与核验规则.md)

跨模型的输出截断、思考 token、JSON、工具循环、流式解析与限流问题统一收录在[真实踩雷与生产检查](../docs/06-真实踩雷与生产检查.md)。
