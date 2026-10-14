# 模型说明书

中文 · [English](README.en.md)

给人看的模型调用手册，给 Agent 执行的接入规范。学习调用、查找型号或交给 Agent 实现，从下面三个入口开始。

<a id="让说明书生成代码"></a>
<a id="快速参数表"></a>
## 从这里开始

| 入口 | 你能找到什么 |
|---|---|
| [人类篇](human/README.md) | 快速上手、完整代码讲解、检查 Agent 实现、通用参数与踩坑 |
| [模型目录](models/README.md) | 按厂商和准确型号查说明书、参数、示例、官方价格与实测记录 |
| [Agent 篇](agents/README.md) | 接入规范、资料查询、代码生成、迁移与排错 |

人类篇和 Agent 篇共用型号卡片、示例源码与原始报告；中英文也共用同一套代码与证据。

## 维护与证据

[实测状态](docs/示例实测状态.md) · [验证与复现](docs/验证与复现.md) · [来源规则](docs/来源与核验规则.md) · [翻译检查](scripts/check_translations.py)

项目默认调用和维护示例使用付费型号，不因报错静默回退免费型号。价格直接查模型目录中的官方页面；已有实测不代表 Agent 改写或任意参数组合已通过。详细边界见来源规则。

Key 只放环境变量或被 Git 忽略的 .env，不写入代码、聊天、报告或提交，不用模板覆盖已有 .env。[忽略配置](.gitignore) · [安全与来源规则](docs/来源与核验规则.md)

安装与检查命令统一见验证与复现；[CI 模板](ci/offline-checks.yml)尚未启用 GitHub Actions。

项目组织方式受[《高性价比人生指南》](https://github.com/eternity4719/HowToLiveBetter)启发；本项目与各模型厂商及该项目无隶属关系。采用 [Unlicense](LICENSE)。
