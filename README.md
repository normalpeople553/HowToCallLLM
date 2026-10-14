# 模型说明书

中文 · [English](README.en.md)

给人看的模型调用手册，给 Agent 执行的接入规范。人类篇讲清概念、参数与踩坑；Agent 篇按任务读取资料、生成代码、迁移和排错。两篇共用型号卡片、可执行示例和真实报告。[来源规则](docs/来源与核验规则.md)

## 选择篇章

| 你要做什么 | 中文 | English |
|---|---|---|
| 自己理解、调用和排查模型 | [人类篇](human/README.md) | [Human guide](human/README.en.md) |
| 让编程 Agent 接入、迁移或排错 | [Agent 篇](agents/README.md) | [Agent guide](agents/README.en.md) |

给 Agent 直接读取 [SKILL.md](skills/model-manual/SKILL.md)；英文任务读取 [SKILL.en.md](skills/model-manual/SKILL.en.md)。不要求 Agent 先通读人类教程。

<a id="让说明书生成代码"></a>
## 目前包括什么

| 内容 | 入口 |
|---|---|
| 第一次调用、兼容接口、环境变量、费用入口和常见报错 | [人类篇阅读路线](human/README.md#reading-path) |
| 六家语言模型的准确 API ID、生命周期、输入模态、官方价格和仓库覆盖 | [语言模型清单](docs/model-lists/README.md) |
| 六家具体型号的身份、接口、能力、限制、生命周期和官方出处 | [型号说明书](models/README.md) |
| 上下文与输出预算、温度/核采样、思考、流式、JSON、工具和多模态字段的逐项解释 | [参数说明与调参](docs/参数说明与调参.md) |
| 普通/流式/思考、多轮、JSON/Schema、工具闭环、图片/视频等按型号收录的完整文件 | [官方功能示例索引](docs/官方示例索引.md) |
| 思考 token、截断、空正文、工具回传、断流、限流和生产检查 | [真实踩雷](docs/06-真实踩雷与生产检查.md) |
| 接入、迁移、排错、未知型号与证据核对的 Agent 工作流 | [Agent 篇](agents/README.md) |
| 按型号生成 Python / TypeScript / cURL，按能力检索现成示例 | [代码生成器](skills/model-manual/scripts/generate_snippet.py) · [示例目录工具](skills/model-manual/scripts/example_catalog.py) |
| 锁定依赖、离线回归、真实逐文件执行、脱敏报告与源码哈希检查 | [验证与复现](docs/验证与复现.md) |
| 英文通用指南、六家说明书、参数页和自动生成的状态页 | [English edition](README.en.md) |

这张表是内容清单，不表示每个型号支持所有功能。当前文件数、通过数和未通过项，以[逐文件实测状态](docs/示例实测状态.md)为准；旧型号能力检查另见[历史统一流程状态](docs/验证状态.md)。

<a id="快速参数表"></a>
## 已维护详细说明书的型号

下表不是厂商的全部型号。[六家语言模型清单](docs/model-lists/README.md)另外收录官方型号与旧名，并区分“官方列出”“有详细说明书”“有逐文件实测证据”。清单新增不等于生成器已支持，也不继承同厂默认型号的参数或测试。

项目规则：默认调用与维护示例全部采用付费型号，不因报错自动回退免费型号；价格直接查各说明书的官方入口，赠送额度不改变型号的付费性质。[选型规则](docs/来源与核验规则.md)

| 厂商 | 准确型号 / 中文说明书 | English manual |
|---|---|---|
| DeepSeek | [deepseek-flash](models/deepseek/deepseek-flash/README.md) | [English](models/deepseek/deepseek-flash/README.en.md) |
| Kimi | [kimi-k2.6](models/kimi/kimi-k2.6/README.md) | [English](models/kimi/kimi-k2.6/README.en.md) |
| 智谱 | [glm-4.7](models/zhipu/glm-4.7/README.md) | [English](models/zhipu/glm-4.7/README.en.md) |
| 通义千问 | [qwen-flash](models/qwen/qwen-flash/README.md) | [English](models/qwen/qwen-flash/README.en.md) |
| 豆包 | [doubao-seed-2-1-pro-260628](models/doubao/doubao-seed-2-1-pro-260628/README.md) | [English](models/doubao/doubao-seed-2-1-pro-260628/README.en.md) |
| MiniMax | [MiniMax-M2.7](models/minimax/MiniMax-M2.7/README.md) | [English](models/minimax/MiniMax-M2.7/README.en.md) |

型号名称不保证永久可用。旧型号下线、订阅路由和地域限制，要核对各说明书链接的官方页面；不自动用同厂其他型号替换。[收录规则](docs/来源与核验规则.md)

## 一份事实，两种读法，两种语言

型号事实保留在[机器卡片](skills/model-manual/references/models/)，厂商路由保留在 [vendors.json](skills/model-manual/references/vendors.json)。中英文链接同一批[示例源码](models/)和[原始报告](verification/examples/)，不会把翻译当成新实测，也不会因语言不同切换 API 区域或密钥。

价格和额度直接链接官方页面；未知保持未知，限流不改写成不支持。中英文派生页从同一数据生成；静态译文的对应关系与已核对的源文件版本由[翻译检查](scripts/check_translations.py)维护。翻译检查不是语义准确率证明。[完整规则](docs/来源与核验规则.md)

## 维护、安全与协议

安装、离线检查、双语同步和显式真实调用见[验证与复现](docs/验证与复现.md)。状态页同步不等于所有文件通过；严格门槛由[发布检查](tests/check_example_release.py)的 --require-passed 区分。已有的 [CI 模板](ci/offline-checks.yml)仍未启用 GitHub Actions。

Key 只放环境变量或被 Git 忽略的 .env，不写进代码、聊天、报告或提交；已有 .env 不要被模板覆盖。[安全规则](docs/来源与核验规则.md) · [忽略配置](.gitignore)

项目组织方式受[《高性价比人生指南》](https://github.com/eternity4719/HowToLiveBetter)启发；本项目与各模型厂商及该项目无隶属关系。采用 [Unlicense](LICENSE)。
