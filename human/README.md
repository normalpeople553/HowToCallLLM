# 人类篇：找到用法，理解参数，读懂证据

[项目首页](../README.md) · [English](README.en.md) · [Agent 篇](../agents/README.md)

这里面向需要做判断、运行示例或给 Agent 下任务的人，不按新手/老手分组。人类篇与 Agent 篇共享[型号卡片](../skills/model-manual/references/models/)、示例源码和报告，不各自维护一套模型事实。[来源规则](../docs/来源与核验规则.md)

<a id="reading-path"></a>
## 按你现在的问题阅读

| 你想做什么 | 从这里开始 | 读完要能确认什么 |
|---|---|---|
| 第一次调模型 | [第一次调用](../docs/01-5分钟跑通第一次调用.md) | 环境、Key、地址、型号与可运行文件 |
| 用熟悉的 SDK 接另一家 | [兼容接口套路](../docs/02-一个套路调遍所有模型.md) | 哪些结构共用，哪些字段必须按型号处理 |
| 找准确型号的用法 | [型号目录](../models/README.md)及下表 | API ID、接口、生命周期和官方来源 |
| 理解或调整参数 | [参数说明与调参](../docs/参数说明与调参.md) | 字段作用、默认/未知、预算与模式副作用 |
| 查价格与额度 | [官方费用入口](../docs/04-免费额度与省钱攻略.md) | 当前账户/地域适用规则，不依赖手抄价格 |
| 请求报错 | [排错与 Key 安全](../docs/05-新手必会与报错速查.md) | 脱敏后保留哪些信息、先检查哪一层 |
| 避免截断、空答与工具雷区 | [生产踩雷](../docs/06-真实踩雷与生产检查.md) | 结束原因、思考预算、完整历史和业务校验 |
| 想知道到底测过没有 | [逐文件实测状态](../docs/示例实测状态.md)与[验证复现](../docs/验证与复现.md) | 当前源码、输入、参数、环境和报告范围 |
| 让 Agent 帮你接入/迁移/排错 | [Agent 篇](../agents/README.md) | 给出业务目标和约束，按任务读取准确资料 |

这些章节按需查阅即可；阅读方式见[前言](../docs/00-前言.md)，无需先通读整本。

## 六个已收录型号

下表是资料导航，不是质量排名。“特色示例”仅指仓库已收录的代码，不是完整能力清单，也不表示所有例子或组合已通过。来源、改写与当前验证范围查[官方示例索引](../docs/官方示例索引.md)。

| 准确型号 | 说明书 | 参数与逐文件映射 | 可重点看的特色示例 |
|---|---|---|---|
| `deepseek-flash` | [DeepSeek](../models/deepseek/deepseek-flash/README.md) | [参数](../models/deepseek/deepseek-flash/parameters.md) | [图片/File ID](../models/deepseek/deepseek-flash/examples/10_vision_files.py)、[Responses 图片](../models/deepseek/deepseek-flash/examples/11_responses_vision.py)、[FIM](../models/deepseek/deepseek-flash/examples/15_fim_completion.py) |
| `kimi-k2.6` | [Kimi](../models/kimi/kimi-k2.6/README.md) | [参数](../models/kimi/kimi-k2.6/parameters.md) | [保留思考的工具闭环](../models/kimi/kimi-k2.6/examples/08_thinking_tools.py)、[本地视频](../models/kimi/kimi-k2.6/examples/09_video.py) |
| `glm-4.7-flash` | [智谱](../models/zhipu/glm-4.7-flash/README.md) | [参数](../models/zhipu/glm-4.7-flash/parameters.md) | [多轮历史](../models/zhipu/glm-4.7-flash/examples/06_multi_turn.py)、[思考工具闭环](../models/zhipu/glm-4.7-flash/examples/07_thinking_tools.py) |
| `qwen-flash` | [通义千问](../models/qwen/qwen-flash/README.md) | [参数](../models/qwen/qwen-flash/parameters.md) | [JSON 对象](../models/qwen/qwen-flash/examples/04_json_output.py)、[思考工具闭环](../models/qwen/qwen-flash/examples/07_thinking_tools.py) |
| `doubao-seed-2-1-pro-260628` | [豆包](../models/doubao/doubao-seed-2-1-pro-260628/README.md) | [参数](../models/doubao/doubao-seed-2-1-pro-260628/parameters.md) | [思考工具历史](../models/doubao/doubao-seed-2-1-pro-260628/examples/08_thinking_tools.py)、[隐式缓存观测](../models/doubao/doubao-seed-2-1-pro-260628/examples/10_implicit_cache.py) |
| `MiniMax-M2.7` | [MiniMax](../models/minimax/MiniMax-M2.7/README.md) | [参数](../models/minimax/MiniMax-M2.7/parameters.md) | [模拟工具闭环](../models/minimax/MiniMax-M2.7/examples/05_tool_calling.py)、[旧原生 cURL](../models/minimax/MiniMax-M2.7/examples/07_native_curl.sh) |

调用前同时读型号身份与生命周期，不把旧名仍能请求理解为固定服务版本保证。MiniMax M2.7 已有退役/订阅路由公告；具体日期与平台区别见[型号说明书](../models/minimax/MiniMax-M2.7/README.md)和[官方公告](https://platform.minimax.cn/docs/guides/models-intro)。

## 建议的动手顺序

以下是项目流程建议，不是厂商对模型正确性的承诺。[规则与边界](../docs/来源与核验规则.md)

1. 在仓库根目录准备 Python 3.10+ 独立环境，安装锁定依赖；不要靠“我电脑上能 import”判断环境一致。[完整步骤](../docs/验证与复现.md)

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements-lock.txt
   ```

2. 按准确型号配置对应环境变量。若使用 `.env`，先确认被 Git 忽略，只增补需要的字段；不要用模板覆盖已有 `.env`，也不要打印它来检查 Key。[Key 安全](../docs/05-新手必会与报错速查.md#key-安全)

3. 从[示例索引](../docs/官方示例索引.md)选择规范可执行文件，读取其环境变量、输入要求与模拟数据说明。上传文件前确认自己有权发送；直接运行原例可能计费。[执行与输入规则](../docs/验证与复现.md)

4. 先读该文件的参数映射，分清以下三层；未知项保持未知，不拿新型号或别家的同名字段补齐。[调参导航](../docs/参数说明与调参.md)

   | 层次 | 例子 | 应从哪里确认 |
   |---|---|---|
   | SDK / 传输 | `timeout`、`max_retries`、`extra_body` | 型号参数页的 SDK 说明与锁定版本 |
   | 模型请求 | `model`、`messages`、预算、思考、`tools` | 准确型号官方出处及实际端点 |
   | 本地验收 | 循环轮数、城市/订单/SKU、JSON 业务检查 | 规范示例源码与项目约定 |

5. 检查结束原因、非空最终正文和服务端业务状态；JSON 还要解析与业务验证，工具还要核对参数、ID 和完整消息闭环。HTTP 200 或进程退出 0 不是全部检查。[生产检查](../docs/06-真实踩雷与生产检查.md)

6. 修改提示词、预算、思考、输入或协议后，重新检查更改后的路径。原例的通过不覆盖任意新组合；需要真实证据时按[复现流程](../docs/验证与复现.md)保存新的脱敏报告，不覆盖历史。

Windows 激活命令、Node/cURL 依赖、视频输入和真实执行开关统一见[验证与复现](../docs/验证与复现.md)。这里的安装片段不发送模型请求，也不另造一份 API 示例。

## “测过”要看哪一层

| 证据 | 能证明什么 | 不能据此推断什么 |
|---|---|---|
| 官方文档/型号卡片 | 该准确型号已找到的官方参数与能力依据 | 你的账户、代码或所有任务都已成功 |
| [历史统一流程验证](../docs/验证状态.md) | 固定能力脚本当时的测试项与结果 | 全部进阶示例或当前源码都通过 |
| [逐文件实测](../docs/示例实测状态.md) | 指定源码/依赖指纹、参数、输入与环境下的真实执行证据 | 任意改写、新生成组合或通用准确率 |
| 编译/离线 mock | 对应语法与模拟边界的检查 | 真实 API 接受请求或实时业务数据正确 |

型号卡片 `verification=null/not_run` 可与独立示例的真实执行记录同时存在；两层报告不能互相冒充。限流、缺输入和旁观证据不足也不等于能力不支持。具体定义与当前结果以[证据规则](../docs/来源与核验规则.md)及动态状态页为准，不在这里写死通过数量。

## 交给 Agent 时说清目标

可以把下面的任务描述交给编程 Agent；这是工作指令，不是新增的模型 API 请求样例：

> 请从本仓库 Agent 篇开始，使用我指定的准确型号完成接入。沿用现有项目语言与依赖；先说明需要的能力、输入和参数，再修改代码并做离线检查。真实调用仅在我授权的范围内执行，交付时区分官方支持、已有证据、本次验证和未知项。

迁移时补充源/目标型号与必须保留的业务行为；排错时提供脱敏状态码、结束原因和最小复现，不提供完整 Key。[Agent 篇](../agents/README.md) · [排错路线](../docs/05-新手必会与报错速查.md)
