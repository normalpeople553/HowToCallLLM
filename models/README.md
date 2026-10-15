# 模型目录

[项目首页](../README.md) · [English](README.en.md) · [人类篇](../human/README.md) · [Agent 篇](../agents/README.md)

先选厂商，再选准确型号。厂商页把型号清单、官方价格和仓库已有的调用资料放在同一行，不需要分别寻找“模型清单”和“型号说明书”。

## 按厂商找型号

| 厂商（点击查看型号） | 已维护详细说明书的型号 | 读代码与检查 Agent |
|---|---|---|
| [DeepSeek](../docs/model-lists/deepseek.md) | [deepseek-flash](deepseek/deepseek-flash/README.md) · [deepseek-v4-pro](deepseek/deepseek-v4-pro/README.md) | [完整代码与核对](../human/examples/deepseek.md) |
| [Kimi](../docs/model-lists/kimi.md) | [kimi-k2.6](kimi/kimi-k2.6/README.md) | [完整代码与核对](../human/examples/kimi.md) |
| [智谱 GLM](../docs/model-lists/zhipu.md) | [glm-4.7](zhipu/glm-4.7/README.md) | [完整代码与核对](../human/examples/zhipu.md) |
| [通义千问](../docs/model-lists/qwen.md) | [qwen-flash](qwen/qwen-flash/README.md) | [完整代码与核对](../human/examples/qwen.md) |
| [豆包](../docs/model-lists/doubao.md) | [doubao-seed-2-1-pro-260628](doubao/doubao-seed-2-1-pro-260628/README.md) | [完整代码与核对](../human/examples/doubao.md) |
| [MiniMax](../docs/model-lists/minimax.md) | [MiniMax-M2.7](minimax/MiniMax-M2.7/README.md) | [完整代码与核对](../human/examples/minimax.md) |

上表中列出的维护型号不是厂商的全部型号。点击厂商可查看其他准确 API ID、输入模态、生命周期和官方价格入口；已有完整说明书的型号可直接点击进入。尚无说明书或示例的型号会明确标注，不继承同系列证据。

已下线型号不列出；可用性待确认的条目单独分组。预览、兼容别名、订阅/地域限制及未来下线安排，以型号行的官方来源和核对日期为准。清单是资料快照，不保证当前账户权限或服务容量。[收录与证据规则](../docs/来源与核验规则.md)

## 按功能找代码

[全部功能示例](../docs/官方示例索引.md) · [代码阅读与人工核对](../human/examples/README.md) · [调用代码目录](../docs/示例实测状态.md)

先确认准确型号，再找普通对话、流式、思考、JSON、工具、图片/视频等对应文件。逐项字段解释放在各型号的参数页；不把同厂其他型号的示例直接换名套用。

## 使用与验证

项目默认调用和维护示例仍全部采用付费型号；发现清单中的免费条目不改变这项规则，也不触发自动回退。具体价格只查官方页面。[选型规则](../docs/来源与核验规则.md)

运行环境、输入要求和真实调用方式见[验证与复现](../docs/验证与复现.md)；调用文件见代码目录；测试记录与哈希只留本地，不对外展示，规则见[验证说明](../docs/验证状态.md)。翻译、代码阅读页和新生成的组合不构成新的线上执行记录。
