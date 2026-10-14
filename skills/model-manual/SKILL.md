---
name: model-manual
description: 为 DeepSeek、Kimi、智谱 GLM、通义千问和豆包接入、迁移或排查 OpenAI-compatible 模型调用代码。用户需要国产模型的接口配置、参数差异、流式/JSON/工具调用，或核对未收录型号时使用。
---

# 模型说明书 · Agent 入口

根据用户的项目完成模型调用任务。人类阅读入口是[仓库 README](../../README.md)；无需按顺序读取整套教程。

## 先定位任务与型号

1. 从用户要求和现有项目确定厂商、型号、语言及调用方式；缺少会影响实现的信息时再问。没有现有项目且用户未指定语言时使用 Python，未指定型号时读取厂商的 `default_model`。
2. 从 [references/vendors.json](references/vendors.json) 定位对应厂商，再读取指定型号的 [references/models/](references/models/) 卡片。目录中的 `model_card` 和 `model_manual` 只指默认型号，用户指定其他型号时必须按准确 Model ID 查找。
3. 型号参数读取卡片的 `generation`，能力读取 `capabilities`，每个事实的 `source` 在该卡片的 `sources` 中解析。需要解释限制或查看示例时读取 [models/](../../models/) 中对应说明书；需要声称“已实测”时继续读该卡片 `verification` 指向的原始报告。
4. 按下表读取[任务流程](references/workflows.md)中相关部分，完成实现和检查。

需要具体功能代码时先查询[官方示例目录](scripts/example_catalog.py)：`python skills/model-manual/scripts/example_catalog.py --model <准确型号> --capability <能力词>`。返回文件、官方来源、环境变量、运行命令及改写/验证范围；只读取命中的示例及其本目录依赖。人类索引见[官方示例索引](../../docs/官方示例索引.md)。不存在的组合不会回退到其他型号；示例缺失也不代表不支持。

| 用户任务 | 任务流程中的部分 | 重点 |
|---|---|---|
| 新增调用、JSON 提取、流式或工具调用 | 接入 | 检查任务与语言组合，用型号参数生成代码 |
| 换厂商、换型号、升级 SDK | 迁移 | 比较源与目标，保留业务行为，处理参数和消息差异 |
| 报错、空正文、断流或工具循环 | 排错 | 结合实际响应和具体型号定位原因 |
| 指定未收录型号 | 未知型号 | 核对官方资料，避免继承默认型号参数 |
| 查能力或要求真实复测 | 证据与验证 | 分开说明官方声明、历史结果和本次检查 |

## 生成调用代码

在仓库根目录运行；脚本只生成代码，不发送模型请求：

```bash
python skills/model-manual/scripts/generate_snippet.py --help
python skills/model-manual/scripts/generate_snippet.py --vendor kimi --language python --thinking off
python skills/model-manual/scripts/generate_snippet.py --vendor qwen --language typescript --stream
python skills/model-manual/scripts/generate_snippet.py --vendor kimi --task tool --thinking off
python skills/model-manual/scripts/generate_snippet.py --vendor qwen --task json --thinking off --max-tokens 2048
```

语言支持 `python`、`typescript` 和 `curl`，任务组合以脚本帮助和型号卡片为准。未知型号、未支持组合和生命周期限制必须先处理；不能通过换名、删除校验或沿用其他型号参数绕过。融入现有项目时保留其语言、依赖和代码风格。

## 交付与边界

- 交付可运行代码或项目修改、必要的环境变量与运行命令，说明实际完成的检查。用户只要代码时保持简洁。
- 参数与能力的厂商结论附卡片中的官方来源；价格和额度直接链接官方页面。项目判断按[来源规则](../../docs/来源与核验规则.md)标为“项目建议”。
- Key 从型号规定的环境变量读取，不硬编码、不回显。除非用户明确要求真实调用，否则只生成、修改代码或执行离线检查。
- 保留输出完整性检查：普通/JSON 检查结束原因和空正文；流式处理空 `choices` 与结束状态；工具验证名称和参数、回传 `tool_call_id`、保留完整 assistant 消息并限制轮次。示例中的工具数据为模拟数据。
- `verified` 仅代表报告中的日期、型号和测试范围；官方支持与本次失败分别说明。历史基础验证不证明完整工具闭环或图片内容识别，限流不代表不支持。
- 以准确型号卡片和原始报告处理摘要冲突；维护或复测后按[验证与复现](../../docs/验证与复现.md)检查同步。源码编译、模拟测试和历史实测不能写成“本次线上通过”。

生成器主要覆盖已收录型号的 Chat Completions；进阶示例另外提供按准确型号核对的 API/功能，依据其来源清单使用。不能将 Chat Completions 兼容扩大为全部 OpenAI API 兼容，也不能用单个示例推断所有参数都可用。
