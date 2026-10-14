# 模型说明书

> Agent 优先，人类可读的大模型 API 接入手册。

本项目把模型资料、调用代码和验证证据组织成编程 Agent 可以按任务使用的说明书：接入模型、迁移厂商、排查错误，以及核对尚未收录的型号。人类通过本页了解怎么使用、模型有什么差异、实测结果能证明什么。两种入口共用模型卡片与原始报告，维护规则见[来源与核验规则](docs/来源与核验规则.md)。

## 两个入口

| 读者 | 入口 | 怎么使用 |
|---|---|---|
| Agent | [`skills/model-manual/SKILL.md`](skills/model-manual/SKILL.md) | 按任务读取对应型号卡片、示例和报告，完成接入、迁移或排错 |
| 人类 | 本页 | 给 Agent 一条具体指令；需要判断能力、费用或失败原因时查下面的资料 |

需要具体功能代码时，从[官方功能示例索引](docs/官方示例索引.md)按准确型号查找图片、视频、多轮、思考工具、结构化输出等示例；实际执行结果另查[逐文件示例实测状态](docs/示例实测状态.md)。来源清单记录出处、运行命令与改写，不把历史报告或清单录入时的验证标记自动当成当前文件的实测结论。[证据边界](docs/来源与核验规则.md)

## 让 Agent 使用

把仓库地址和你的项目需求一起交给编程 Agent；本地已克隆时，直接提供 `skills/model-manual/SKILL.md` 的路径。以下指令可以复制后修改：

**接入模型**

> 阅读 https://github.com/normalpeople553/HowToCallLLM 的 skills/model-manual/SKILL.md，根据我的项目接入 Kimi。先检查现有语言、依赖和调用代码，再读取对应型号资料；给出可运行实现、运行命令和验证范围。

**迁移厂商**

> 按这个仓库的 Skill，把项目中的 Kimi 调用迁移到通义。逐项核对思考开关、输出预算、JSON、流式和工具消息，不要只替换 base_url 和模型名。说明哪些行为能保留、哪些需要修改，以及哪些尚未验证。

**排查错误**

> 按这个仓库的 Skill，排查我提供的错误和最小调用代码。先区分鉴权、限流、输出截断和参数问题，再给出有依据的修复与检查方法；不要回显 Key。

Agent 的任务分支、未知型号处理和交付要求见[任务流程](skills/model-manual/references/workflows.md)。代码生成与离线检查不会调用模型；真实 API 验证需要单独明确要求。[验证与复现](docs/验证与复现.md)

## 人类按问题查阅

| 想了解什么 | 阅读位置 |
|---|---|
| 某个具体型号的能力、限制与示例 | [模型说明书](models/README.md) |
| 某个可运行示例当前是否真实执行、是否通过 | [逐文件示例实测状态](docs/示例实测状态.md)及其原始报告 |
| 历史统一验证器检查过哪些能力 | [历史统一流程验证状态](docs/验证状态.md)及其原始报告 |
| 每个参数是什么、怎么调、有哪些型号差异 | [参数说明与调参导航](docs/参数说明与调参.md) |
| 为什么同一套接口仍有参数差异 | [统一调用套路](docs/02-一个套路调遍所有模型.md) |
| 空回复、JSON、工具循环和限流怎么处理 | [真实踩雷](docs/06-真实踩雷与生产检查.md) |
| 怎么核对价格、额度和成本 | [价格与额度](docs/04-免费额度与省钱攻略.md) |
| 自己手动运行一次调用 | [第一次调用](docs/01-5分钟跑通第一次调用.md)（辅助教程） |

能力声明、实测结果和项目建议分别记录；`unknown` 表示没有足够结论，不能据此认定不支持。[来源规则](docs/来源与核验规则.md)

## 模型级说明书

已收录的准确型号、调用说明和参数解释如下；每份参数页按实际可运行文件映射字段，并分别标明官方语义与项目配置。

| 准确型号 | 调用说明书 | 参数详解 |
|---|---|---|
| DeepSeek `deepseek-flash` | [说明书](models/deepseek/deepseek-flash/README.md) | [参数与逐文件对照](models/deepseek/deepseek-flash/parameters.md) |
| Kimi `kimi-k2.6` | [说明书](models/kimi/kimi-k2.6/README.md) | [参数与逐文件对照](models/kimi/kimi-k2.6/parameters.md) |
| 智谱 `glm-4.7-flash` | [说明书](models/zhipu/glm-4.7-flash/README.md) | [参数与逐文件对照](models/zhipu/glm-4.7-flash/parameters.md) |
| 通义 `qwen-flash` | [说明书](models/qwen/qwen-flash/README.md) | [参数与逐文件对照](models/qwen/qwen-flash/parameters.md) |
| 豆包 `doubao-seed-2-1-pro-260628` | [说明书](models/doubao/doubao-seed-2-1-pro-260628/README.md) | [参数与逐文件对照](models/doubao/doubao-seed-2-1-pro-260628/parameters.md) |
| MiniMax `MiniMax-M2.7` | [说明书](models/minimax/MiniMax-M2.7/README.md) | [参数与逐文件对照](models/minimax/MiniMax-M2.7/parameters.md) |

参数入门与调节顺序见[参数说明与调参](docs/参数说明与调参.md)。实测分两层：[历史统一验证器](docs/验证状态.md)检查固定能力项，[逐文件运行](docs/示例实测状态.md)检查具体文件与当次输入；两者不能相互替代，也不证明任意参数组合都成功。[来源规则](docs/来源与核验规则.md)

MiniMax M2.7 的逐文件执行情况同样见[示例实测状态](docs/示例实测状态.md)，不以历史统一验证器报告空缺推断从未真实调用。其生命周期需单独注意：2026-10-19 停止向新用户开放，2026-11-18 按量 API 下线；订阅请求的旧名称将从 10-19 起路由到新模型。使用前先查[官方通知](https://platform.minimax.cn/docs/guides/models-intro)。

## 快速参数表

下表的接口、型号与参数行为链接均指向厂商官方文档；环境变量名也可在上面的各型号示例中核对。它是配置速查，不是实测通过表；实际参数解释见[调参导航](docs/参数说明与调参.md)，运行证据见[核验口径](docs/来源与核验规则.md)。

| 厂商 | Key 环境变量 | 官方接口文档 | 默认模型 / 官方模型页 | 关闭思考 | 官方价格 |
|---|---|---|---|---|---|
| DeepSeek | `DEEPSEEK_API_KEY` | [`https://api.deepseek.com`](https://api-docs.deepseek.com/) | [`deepseek-flash`](https://api-docs.deepseek.com/quick_start/pricing/) | [`thinking.type=disabled`](https://api-docs.deepseek.com/guides/thinking_mode/) | [价格页](https://api-docs.deepseek.com/quick_start/pricing/) |
| Kimi | `MOONSHOT_API_KEY` | [`https://api.moonshot.cn/v1`](https://platform.kimi.com/docs/get-api-key) | [`kimi-k2.6`](https://platform.kimi.com/docs/models) | [`thinking.type=disabled`](https://platform.kimi.com/docs/guide/use-thinking-models) | [价格页](https://platform.kimi.com/docs/pricing/chat) |
| 智谱 GLM | `ZHIPU_API_KEY`（项目约定） | [`https://open.bigmodel.cn/api/paas/v4`](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) | [`glm-4.7-flash`](https://docs.bigmodel.cn/cn/guide/start/pricing) | [`thinking.type=disabled`](https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode) | [价格页](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| 通义千问 | `DASHSCOPE_API_KEY` | [OpenAI 兼容接口](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) | [`qwen-flash`](https://help.aliyun.com/zh/model-studio/getting-started/models) | [`enable_thinking=false`](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) | [价格页](https://help.aliyun.com/zh/model-studio/model-pricing) |
| 豆包方舟 | `ARK_API_KEY` | [`https://ark.cn-beijing.volces.com/api/v3`](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) | [`doubao-seed-2-1-pro-260628`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) | [`thinking.type=disabled`](https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh) | [价格页](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |
| MiniMax | `MINIMAX_API_KEY`（项目约定） | [`https://api.minimax.cn/v1`](https://platform.minimax.cn/docs/api-reference/text-openai-api) | [`MiniMax-M2.7`（已公告退役）](https://platform.minimax.cn/docs/guides/models-intro) | [M2.x 无法关闭；reasoning_split 只改输出格式](https://platform.minimax.cn/docs/api-reference/text-chat-openai) | [价格页](https://platform.minimax.cn/docs/guides/pricing-paygo) |

> 通义官方当前推荐带 `WorkspaceId` 的地域域名；旧 `dashscope.aliyuncs.com/compatible-mode/v1` 仍可使用。两种地址与迁移说明见[官方兼容接口文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)。

## 最小调用

DeepSeek 官方文档提供 OpenAI SDK 兼容调用方式；下面使用它当前推荐的 `deepseek-flash`。[官方接口与模型页](https://api-docs.deepseek.com/quick_start/pricing/)

以下代码块是说明性片段，不在逐文件执行清单内；需要完整校验时运行[对应示例文件](models/deepseek/deepseek-flash/examples/01_basic.py)，并核对该文件的[实测记录](docs/示例实测状态.md)。片段或自改参数不继承文件结果。[项目证据规则](docs/来源与核验规则.md)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[{"role": "user", "content": "你好"}],
)
print(response.choices[0].message.content)
```

已收录厂商都在各自官方文档中提供 OpenAI-compatible Chat Completions 用法：[DeepSeek](https://api-docs.deepseek.com/)、[Kimi](https://platform.kimi.com/docs/api/chat)、[智谱](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction)、[通义](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)、[豆包](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh)、[MiniMax](https://platform.minimax.cn/docs/api-reference/text-openai-api)。本项目因此统一使用 `openai` 客户端，但不声称这些厂商兼容 OpenAI 的全部 API。

## 让说明书生成代码

生成器读取厂商路由和具体型号卡片，检查型号归属、思考开关、任务能力和输出参数；支持范围由[脚本参数](skills/model-manual/scripts/generate_snippet.py)定义。未知型号会提示先补卡片，避免继续套用默认型号参数。

```bash
python skills/model-manual/scripts/generate_snippet.py \
  --vendor kimi --language python --thinking off

python skills/model-manual/scripts/generate_snippet.py \
  --vendor qwen --language typescript --stream

python skills/model-manual/scripts/generate_snippet.py \
  --vendor doubao --language curl

# 生成完整 Python 工具闭环
python skills/model-manual/scripts/generate_snippet.py \
  --vendor kimi --model kimi-k2.6 --task tool --thinking off

# JSON 提取；输出上限按当前型号卡片的字段语义处理
python skills/model-manual/scripts/generate_snippet.py \
  --vendor qwen --task json --thinking off --max-tokens 2048
```

## 验证

仓库要求 Python 3.10+，安装与离线校验见[验证与复现](docs/验证与复现.md)。真实验证分为下面的统一验证器，以及直接执行已登记文件的[逐文件执行器](tests/run_example_files.py)；两者都会发送真实请求、分别保存报告。结果分别见[历史统一流程状态](docs/验证状态.md)与[逐文件示例状态](docs/示例实测状态.md)，不把“进程退出 0”直接扩展成所有能力都通过。[证据规则](docs/来源与核验规则.md)

```bash
cp examples/.env.example .env
python -m pip install -r requirements-lock.txt
python tests/verify_calls.py kimi qwen --report /tmp/model-manual-verification.json
```

逐文件执行器默认只列清单、不读取密钥；只有显式加 `--execute` 才发请求。运行命令、输入素材与报告字段见[验证与复现](docs/验证与复现.md)。生成器输出的任意新参数组合也不自动继承现有示例的通过状态。[执行器](tests/run_example_files.py)

不发请求的检查覆盖目录、生成器、流式/截断和工具闭环；可复用的 [CI 模板](ci/offline-checks.yml)使用相同命令，当前尚未启用 GitHub Actions：

```bash
python -m unittest discover -s tests -p 'test_*.py'
python skills/model-manual/scripts/sync_verification.py --check
```

## 完整资料索引

| 章节 | 内容与依据 |
|---|---|
| [Agent Skill](skills/model-manual/SKILL.md) | 任务路由、必读资料与交付边界 |
| [Agent 任务流程](skills/model-manual/references/workflows.md) | 接入、迁移、排错、未知型号和证据核对 |
| [00 阅读说明](docs/00-前言.md) | 双入口、项目范围与可信度标记 |
| [01 第一次调用](docs/01-5分钟跑通第一次调用.md) | 手动运行的辅助教程 |
| [02 统一调用套路](docs/02-一个套路调遍所有模型.md) | 已收录厂商兼容接口与差异 |
| [03 厂商资料卡](docs/03-厂商攻略/) | 每家官方链接、配置和仓库实测 |
| [04 价格与额度](docs/04-免费额度与省钱攻略.md) | 直达官方价格、额度页面 |
| [05 排错](docs/05-新手必会与报错速查.md) | 官方错误文档与项目排查流程 |
| [06 真实踩雷](docs/06-真实踩雷与生产检查.md) | 思考 token、截断、JSON、工具调用、流式与限流 |
| [参数说明与调参](docs/参数说明与调参.md) | 六家逐参数解释、文件映射、调节顺序与证据边界 |
| [验证与复现](docs/验证与复现.md) | 锁定环境、自动报告、退出码与验证范围 |
| [历史统一流程状态](docs/验证状态.md) | 从模型卡片登记的统一验证器报告生成的历史能力摘要 |
| [逐文件示例实测状态](docs/示例实测状态.md) | 当前文件对应的真实执行、参数、源码指纹与报告 |
| [来源与核验规则](docs/来源与核验规则.md) | 每类结论如何引用与复核 |

## Key 安全

本仓库的项目规则是：Key 只从环境变量或被 `.gitignore` 排除的 `.env` 读取，不写入代码、不回显完整值；疑似泄露就去对应厂商控制台删除并重建。[规则说明](docs/来源与核验规则.md) · [仓库忽略配置](.gitignore)

## 致谢与协议

项目组织方式受开源项目[《高性价比人生指南》](https://github.com/eternity4719/HowToLiveBetter)启发；本项目与各模型厂商及该项目无隶属关系。仓库采用 [Unlicense](LICENSE)。
