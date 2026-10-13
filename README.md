# 模型说明书

> 给人和编程 Agent 共用的大模型 API 接入手册。

本项目帮助新手跑通第一次调用，也帮助老手和 Agent 快速查找 Key、`base_url`、模型名与厂商扩展参数；当前边界记录在 [`skills/model-manual/SKILL.md`](skills/model-manual/SKILL.md)。

## 三个入口

- 新手：从 [`docs/01-5分钟跑通第一次调用.md`](docs/01-5分钟跑通第一次调用.md) 开始。
- 老手：直接查下表或 [`skills/model-manual/references/vendors.json`](skills/model-manual/references/vendors.json)。
- Agent：先读取 [`skills/model-manual/SKILL.md`](skills/model-manual/SKILL.md)，再生成、迁移或排查代码。

## 模型级说明书

已收录五份型号说明书：[DeepSeek `deepseek-flash`](models/deepseek/deepseek-flash/README.md)、[Kimi `kimi-k2.6`](models/kimi/kimi-k2.6/README.md)、[智谱 `glm-4.7-flash`](models/zhipu/glm-4.7-flash/README.md)、[通义 `qwen-flash`](models/qwen/qwen-flash/README.md)和[豆包 `doubao-seed-2-1-pro-260628`](models/doubao/doubao-seed-2-1-pro-260628/README.md)。型号卡片保存官方事实，示例包含结果检查与工具闭环；实测范围和结果统一见[验证状态](docs/验证状态.md)。

## 快速参数表

下表的接口与模型链接均指向厂商官方文档；“仓库验证”指向可复现的在线体检脚本，结果只代表 **2026-10-13** 当日测试环境。[核验口径](docs/来源与核验规则.md)

| 厂商 | Key 环境变量 | 官方接口文档 | 默认模型 / 官方模型页 | 关闭思考 | 官方价格 |
|---|---|---|---|---|---|
| DeepSeek | `DEEPSEEK_API_KEY` | [`https://api.deepseek.com`](https://api-docs.deepseek.com/) | [`deepseek-flash`](https://api-docs.deepseek.com/quick_start/pricing/) | [`thinking.type=disabled`](https://api-docs.deepseek.com/guides/thinking_mode/) | [价格页](https://api-docs.deepseek.com/quick_start/pricing/) |
| Kimi | `MOONSHOT_API_KEY` | [`https://api.moonshot.cn/v1`](https://platform.kimi.com/docs/get-api-key) | [`kimi-k2.6`](https://platform.kimi.com/docs/models) | [`thinking.type=disabled`](https://platform.kimi.com/docs/guide/use-thinking-models) | [价格页](https://platform.kimi.com/docs/pricing/chat) |
| 智谱 GLM | `ZHIPU_API_KEY`（项目约定） | [`https://open.bigmodel.cn/api/paas/v4`](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) | [`glm-4.7-flash`](https://docs.bigmodel.cn/cn/guide/start/pricing) | [`thinking.type=disabled`](https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode) | [价格页](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| 通义千问 | `DASHSCOPE_API_KEY` | [OpenAI 兼容接口](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) | [`qwen-flash`](https://help.aliyun.com/zh/model-studio/getting-started/models) | [`enable_thinking=false`](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) | [价格页](https://help.aliyun.com/zh/model-studio/model-pricing) |
| 豆包方舟 | `ARK_API_KEY` | [`https://ark.cn-beijing.volces.com/api/v3`](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh) | [`doubao-seed-2-1-pro-260628`](https://docs.volcengine.com/docs/ark/model-list?lang=zh) | [`thinking.type=disabled`](https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh) | [价格页](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh) |

> 通义官方当前推荐带 `WorkspaceId` 的地域域名；旧 `dashscope.aliyuncs.com/compatible-mode/v1` 仍可使用。两种地址与迁移说明见[官方兼容接口文档](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)。

## 最小调用

DeepSeek 官方文档提供 OpenAI SDK 兼容调用方式；下面使用它当前推荐的 `deepseek-flash`。[官方接口与模型页](https://api-docs.deepseek.com/quick_start/pricing/)

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

五家厂商都在各自官方文档中提供 OpenAI-compatible Chat Completions 用法：[DeepSeek](https://api-docs.deepseek.com/)、[Kimi](https://platform.kimi.com/docs/api/chat)、[智谱](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction)、[通义](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)、[豆包](https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh)。本项目因此统一使用 `openai` 客户端，但不声称这些厂商兼容 OpenAI 的全部 API。

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

仓库要求 Python 3.10+，安装与离线校验见[验证与复现](docs/验证与复现.md)。在线体检会向已配置 Key 的厂商发送真实请求，报告自动记录安全元数据，具体结果见[验证状态](docs/验证状态.md)。

```bash
cp examples/.env.example .env
python -m pip install -r requirements-lock.txt
python tests/verify_calls.py kimi qwen --report /tmp/model-manual-verification.json
```

不发请求的检查覆盖目录、生成器、流式/截断和工具闭环，CI 使用相同命令：

```bash
python -m unittest discover -s tests -p 'test_*.py'
python skills/model-manual/scripts/sync_verification.py --check
```

## 文档

| 章节 | 内容与依据 |
|---|---|
| [00 前言](docs/00-前言.md) | 项目范围与标记 |
| [01 第一次调用](docs/01-5分钟跑通第一次调用.md) | 官方接口基础上的最短流程 |
| [02 统一调用套路](docs/02-一个套路调遍所有模型.md) | 五家兼容接口与差异 |
| [03 厂商资料卡](docs/03-厂商攻略/) | 每家官方链接、配置和仓库实测 |
| [04 价格与额度](docs/04-免费额度与省钱攻略.md) | 直达官方价格、额度页面 |
| [05 排错](docs/05-新手必会与报错速查.md) | 官方错误文档与项目排查流程 |
| [06 真实踩雷](docs/06-真实踩雷与生产检查.md) | 思考 token、截断、JSON、工具调用、流式与限流 |
| [验证与复现](docs/验证与复现.md) | 锁定环境、自动报告、退出码与验证范围 |
| [验证状态](docs/验证状态.md) | 从模型卡片与报告生成的当前能力状态 |
| [来源与核验规则](docs/来源与核验规则.md) | 每类结论如何引用与复核 |

## Key 安全

本仓库的项目规则是：Key 只从环境变量或被 `.gitignore` 排除的 `.env` 读取，不写入代码、不回显完整值；疑似泄露就去对应厂商控制台删除并重建。[规则说明](docs/来源与核验规则.md) · [仓库忽略配置](.gitignore)

## 致谢与协议

项目组织方式受开源项目[《高性价比人生指南》](https://github.com/eternity4719/HowToLiveBetter)启发；本项目与各模型厂商及该项目无隶属关系。仓库采用 [Unlicense](LICENSE)。
