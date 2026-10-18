# Agent 接入规范（给编程 Agent 看）

中文 · [English](README.en.md) · [项目首页](../README.md) · [模型目录](../models/README.md) · [人类篇](../human/README.md) · [Agent 开发教程](https://github.com/normalpeople553/HowToBuildAgent)

本页集中提供接入规范、查询与代码工具、迁移、排错和验证任务的入口，面向执行这些任务的编程 Agent，也供人复制任务指令。查厂商有哪些型号、阅读型号说明书和示例，统一从[模型目录](../models/README.md)进入；概念学习走[人类篇](../human/README.md)。不要求先读完整套教程。

需要 Agent 执行任务时，按需进入 [model-manual Skill](../skills/model-manual/SKILL.md)；只查型号或浏览说明书，不必先读 Skill。本页不重复维护六家的型号表。

跨项目复用时可选装 [call-llm Skill](../docs/call-llm-skill.md)：它在用户主目录创建 `keyenv`，从本仓库更新资料后让 Agent 按下述规范修改当前项目。安装是用户选择，不是阅读本仓库的前提。

## 开始一个任务

项目默认型号与维护示例全部采用付费型号，读取卡片 `billing.type` 和官方价格来源；遇到失败不静默回退免费型号。[选型规则](../docs/来源与核验规则.md)

执行接入、迁移、排错或验证任务时，先完整读取 [SKILL.md](../skills/model-manual/SKILL.md)，再按用户任务读取[任务流程](../skills/model-manual/references/workflows.md)的相关部分，不默认加载所有型号。仅做查询时，可直接使用下方工具；查询结果不替代接入与验证规则。

| 用户要做什么 | 读取与执行重点 |
|---|---|
| 接入或增加 JSON、流式、工具、图片等功能 | 项目现状 → 准确型号卡 → 能力/参数 → 对应完整示例或生成器 |
| 换厂商、型号或 SDK | 源与目标卡片、消息/思考/预算/工具差异、业务逻辑保留与回归 |
| 空回复、截断、断流、错误码或工具循环 | 脱敏请求、真实状态、结束原因、用量与官方依据；不索要完整 Key |
| 用户指定未收录型号 | 先核对该型号的官方身份和能力，不用默认卡片换名冒充 |
| 询问实测或要求复测 | 准确源码、检查范围与用户授权，不把 mock 写成线上成功 |

这些是项目工作流，不是厂商保证；详细步骤和交付规则见[任务流程](../skills/model-manual/references/workflows.md)。

## 查询与代码工具

### 资料地图

人查型号走[模型目录](../models/README.md)，机器按准确 ID 查询下面的共享资料；清单、官方型号卡与可执行代码分别表达不同的资料覆盖；测试记录只留本地。

| 资料 | 规范入口 | 怎么用 |
|---|---|---|
| 厂商路由 | [vendors.json](../skills/model-manual/references/vendors.json) | 定位默认型号，不把默认型号规则推广至同厂所有型号 |
| 厂商还有哪些语言型号 | [model_catalog.py](../skills/model-manual/scripts/model_catalog.py) · [模型目录](../models/README.md) | 人读目录、机器查准确 ID 和官方来源/生命周期；覆盖独立关联，清单不等于有卡片或实测 |
| 准确型号事实 | [references/models](../skills/model-manual/references/models/) | 读取 identity、capabilities、generation，并解析每条 source |
| 参数解释 | [参数导航](../docs/参数说明与调参.md) | 按任务只读对应型号；区分 SDK 配置、模型参数与本地安全限制 |
| 现成功能代码 | [example_catalog.py](../skills/model-manual/scripts/example_catalog.py) | 按准确型号/能力查来源清单、输入变量、运行命令与官方出处 |
| 生成新组合 | [generate_snippet.py](../skills/model-manual/scripts/generate_snippet.py) | 根据支持的语言/任务组合生成，不自动继承现成文件通过状态 |
| 调用文件目录 | [完整代码目录](../docs/示例实测状态.md) | 查看文件、准确型号、功能与命令，不读取私有记录 |
| 本地验证规则 | [验证说明](../docs/验证状态.md) | 真实调用按授权；测试记录不发布 |

查询和生成命令在仓库根目录运行，以下命令不发请求：

### 型号查询

按厂商列出清单，或核对一个准确 ID；查询命中不代表已经有调用卡片、完整示例或实测通过。

```bash
python skills/model-manual/scripts/model_catalog.py --vendor deepseek
python skills/model-manual/scripts/model_catalog.py --vendor deepseek --model deepseek-v4-pro
```

### 示例检索

先按准确型号和能力查现成文件，再读取该文件的输入变量、官方来源和运行要求。

```bash
python skills/model-manual/scripts/example_catalog.py --model deepseek-flash --capability text
python skills/model-manual/scripts/example_catalog.py --model deepseek-flash --capability vision
```

普通文本可用 `text`、`chat` 或 `basic`，它们仅是 `chat_completions` 的检索别名；返回的准确型号、能力和验证状态不变。其他能力词不确定时，先只传 `--model` 查看该型号的候选，不猜词反复查询，不换型号回退。[检索实现](../skills/model-manual/scripts/example_catalog.py)

### 代码生成

先查看支持的参数；生成新任务组合后，仍需按接入规范检查和验证，不继承其他文件的通过状态。

```bash
python skills/model-manual/scripts/generate_snippet.py --help
python skills/model-manual/scripts/generate_snippet.py --vendor kimi --task tool --thinking off
```

## 给 Agent 的任务指令

**接入：** 阅读本仓库的 skills/model-manual/SKILL.md，根据我的项目接入 Kimi。先检查现有语言、依赖和调用入口；读取准确型号资料，给出实现、运行方式和验证范围。不要回显密钥。

**迁移：** 按本仓库的 Skill，把项目里的 Kimi 调用迁移到通义。逐项比较思考、输出预算、JSON、流式和完整工具消息，保留业务行为，不只替换地址与模型名。

**排错：** 按本仓库的 Skill，排查我提供的脱敏错误和最小调用。先依据实际响应区分鉴权、限流、预算和协议问题，再给出最小修复和检查方法；没有证据的原因标为待核实。

## 输出与证据约定

交付采用的准确型号与官方来源、代码或项目修改、依赖与变量名、运行命令，以及实际完成/尚未完成的检查；迁移补充行为差异，排错补充依据。[规范](../skills/model-manual/SKILL.md)

- Key 只从规定环境变量或本地忽略文件读取，不写入示例或输出。普通代码任务不默认发起可能计费或上传素材的真实请求。
- 生成器和离线测试不是在线验证；原例结果不保证其他输入或组合。文件或依赖变更后重新验证；报告、回复、统计与执行哈希不上传。
- 工具数据是模拟时必须明说。不要删掉结束检查、工具回传或思考历史来让测试“通过”。
- 公开的 private 标记只是说明记录未发布，不等于未执行，也不是公开可审计的通过证明。

以上边界及授权后的真实执行方式见[证据流程](../skills/model-manual/references/workflows.md#证据与验证)与[验证与复现](../docs/验证与复现.md)。机器 JSON、脚本参数和例子路径是中英文共享契约，不翻译字段名或静默替换 API 区域。

## 英文与兼容入口

[English integration instructions](README.en.md)使用 [SKILL.en.md](../skills/model-manual/SKILL.en.md)和[英文任务流程](../skills/model-manual/references/workflows.en.md)，仍读取同一套官方卡片与调用源码。

旧的 [agents/SKILL.md](SKILL.md)只作兼容跳转；本目录旧 vendors/snippets 子目录也只是迁移提示，不是另一份事实或代码源。[旧厂商卡说明](vendors/README.md) · [旧片段说明](snippets/README.md)
