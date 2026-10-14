---
name: model-manual
description: 为 DeepSeek、Kimi、智谱 GLM、通义千问、豆包和 MiniMax 接入、迁移或排查模型调用代码。用户需要国产模型接口配置、参数差异、流式/JSON/工具调用，或核对未收录型号时使用。
---

# 模型说明书 · Agent 入口

中文 · [English](SKILL.en.md) · [Agent 篇](../../agents/README.md) · [人类篇](../../human/README.md)

根据用户的项目完成模型调用任务。人类解释、学习路线与参数导航见人类篇；无需按顺序读取整套教程。中英文说明共用卡片、脚本、示例和报告，不将翻译当作新的实测。

## 先定位任务与型号

1. 从用户要求和现有项目确定厂商、型号、语言及调用方式；缺少会影响实现的信息时再问。没有现有项目且用户未指定语言时使用 Python，未指定型号时读取厂商的 `default_model`。本项目默认型号与维护示例全部使用付费型号，核对卡片 `billing.type.value=paid` 及其官方价格来源；遇到报错不得静默回退免费型号。用户明确指定的其他型号应按原 ID 核对，不擅自改名。[项目选型规则](../../docs/来源与核验规则.md)
2. 从 [references/vendors.json](references/vendors.json) 定位对应厂商，再读取指定型号的 [references/models/](references/models/) 卡片。目录中的 `model_card` 和 `model_manual` 只指默认型号，用户指定其他型号时必须按准确 Model ID 查找。若问“该厂商有哪些语言模型”或指定无卡片型号，先用 [model_catalog.py](scripts/model_catalog.py) 查询官方清单：`python skills/model-manual/scripts/model_catalog.py --vendor deepseek`，可加 `--model <准确ID>`。返回生命周期、官方型号/价格来源和独立派生的 `repository_coverage`；未命中不回退。官方列出不等于仓库已维护/实测，清单中的别名不继承默认卡片。只读命中厂商，不加载全部清单。
3. 型号参数读取卡片的 `generation`，能力读取 `capabilities`，事实的 `source` 在该卡片的 `sources` 中解析。先检查 `identity` 的生命周期与订阅路由；旧 Model ID 不保证实际服务版本。解释参数时按[任务流程的六型号参数入口](references/workflows.md#接入)读取对应 `parameters.md`，不把 SDK 选项、服务端参数和示例业务限制混为一谈。
4. 按下表读取[任务流程](references/workflows.md)中相关部分，完成实现和检查。

需要具体功能代码时先查询[官方示例目录](scripts/example_catalog.py)：`python skills/model-manual/scripts/example_catalog.py --model <准确型号> --capability <能力词>`。返回文件、参数说明路径、官方来源、环境变量、运行命令及验证范围；只读命中示例及其依赖。人类索引见[官方示例索引](../../docs/官方示例索引.md)，当前逐文件状态见[示例实测状态](../../docs/示例实测状态.md)。不存在的组合不会回退到其他型号；缺示例也不代表不支持。

| 用户任务 | 任务流程中的部分 | 重点 |
|---|---|---|
| 新增调用、JSON 提取、流式或工具调用 | 接入 | 检查任务与语言组合，用型号参数生成代码 |
| 换厂商、换型号、升级 SDK | 迁移 | 比较源与目标，保留业务行为，处理参数和消息差异 |
| 报错、空正文、断流或工具循环 | 排错 | 结合实际响应和具体型号定位原因 |
| 查询厂商的其他语言模型 | 型号发现 | 查官方清单、生命周期和仓库覆盖，不把默认卡片当完整目录 |
| 指定未收录型号 | 未知型号 | 核对官方资料，避免继承默认型号参数 |
| 查能力或要求真实复测 | 证据与验证 | 区分型号报告、逐文件证据与新生成代码；按授权运行 |

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
- 型号 `verification: null` / `verification_scope: not_run` 仅表示未完成该型号统一验证器，不能覆盖独立示例的真实 HTTP 报告；反向也不能由一个文件通过升级整张型号卡。按[证据与验证](references/workflows.md#证据与验证)核对原始报告、范围与当前文件哈希。
- 现成文件通过不代表任意新生成的参数/任务组合通过；文件或支持依赖哈希变更必须重新执行。`verified` 限于报告日期、型号和测试项，限流、缺 Key 或缺证据不等于能力不支持。
- 思考不能关闭的型号不生成假开关；`reasoning_split` 等输出格式参数不能当成关闭思考。请求默认字段、预算名称和允许的思考模式均从准确卡片读取。
- 以准确卡片和原始报告处理摘要冲突；[逐文件执行器](../../tests/run_example_files.py)默认只列清单，`--execute` 才会真实调用。授权、命令与报告同步见[证据与验证](references/workflows.md#证据与验证)；编译、mock 与历史实测不能写成“本次线上通过”。

生成器主要覆盖已收录型号的 Chat Completions；进阶示例另外提供按准确型号核对的 API/功能，依据其来源清单使用。不能将 Chat Completions 兼容扩大为全部 OpenAI API 兼容，也不能用单个示例推断所有参数都可用。
