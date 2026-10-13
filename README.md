# 高性价比大模型指南

> 学会一套写法，调遍国产大模型。
> 一份给新手的、按「性价比」组织的大模型 API 调用攻略。**每条调用方式都用真实 key 实测过。**

[![version](https://img.shields.io/badge/version-0.3-orange)]()
[![vendors](https://img.shields.io/badge/厂商-5家-blue)]()
[![tested](https://img.shields.io/badge/调用实测-2026--10--13%2015项全过-brightgreen)]()
[![license](https://img.shields.io/badge/license-Unlicense-lightgrey)]()

---

## 两条阅读路径

这个仓库有两个版本，**按你是谁选入口**：

### 🤖 你是 AI 编程助手（Codex / Claude Code / Trae…），或你只想抄答案

直接读 **[`agents/SKILL.md`](agents/SKILL.md)**——那是给机器读的速查卡：五家的领 key 地址、base_url、模型名、思考开关、注意点一页全有；每家的 YAML 卡片在 [`agents/vendors/`](agents/vendors/)，可直接复制的代码在 [`agents/snippets/`](agents/snippets/)。

> 给 Agent 主人的用法：把本仓库地址丢给你的 AI，说"读这个仓库里的 agents/SKILL.md，帮我调 Kimi"，它就能返回领密钥方法和全部调用技巧。

### 👤 你是新手小白，想搞懂自己在干嘛

从 **[docs/00-前言.md](docs/00-前言.md)** 开始，按顺序读科普线：

| 章节 | 内容 |
|---|---|
| [00 前言](docs/00-前言.md) | 这份指南怎么用、标记是什么意思 |
| [01 5 分钟跑通第一次调用](docs/01-5分钟跑通第一次调用.md) | 从装环境到看到模型回你一句话 |
| [02 一个套路调遍所有模型](docs/02-一个套路调遍所有模型.md) | 万能模板 + 四件套 + **五家思考开关实测对照** |
| 03 厂商攻略 | DeepSeek · Kimi · 智谱 · 通义 · **豆包** |
| [04 免费额度与省钱攻略](docs/04-免费额度与省钱攻略.md) | 五家价格对照、决策树、防翻车 |
| [05 新手必会与报错速查](docs/05-新手必会与报错速查.md) | 多轮/流式/JSON + 常见报错自救 |

## 这是什么

国内能叫得上名字的大模型厂商有十几家，每家都有自己的平台、文档、模型名和计费规则。新手一上来就懵：**到底用哪家？key 去哪领？代码怎么写？会不会一不小心扣很多钱？**

更麻烦的是，网上教程容易过期：模型名会换代、旧参数会失效、免费政策各家有各自的规则。

这份指南不做官方文档的搬运工。它的做法是：**每条调用方式都用真实 key 实测，每条免费政策都附官方出处，把"此刻正确的答案"固化下来。**

- 🔰 新手：从零跑通第一次调用，5 分钟看到模型回你一句话；
- 🎯 老手/AI：打开速查卡，3 秒抄走此刻可用的模型名和参数；
- 💰 免费额度怎么薅、各家多少钱、新手第一家选谁；
- 🧯 报错了怎么自救、有哪些注意点。

## 一个最重要的事实

**国产大模型几乎全都兼容 OpenAI 的接口格式。**

所以下面这段代码，改两行就能换成 DeepSeek、Kimi、智谱、通义、豆包……：

```python
from openai import OpenAI

client = OpenAI(
    api_key="你的key",
    base_url="https://api.deepseek.com",   # ① 改这一行：换厂商
)
resp = client.chat.completions.create(
    model="deepseek-v4-flash",             # ② 改这一行：换模型
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.choices[0].message.content)
```

详见 [docs/02-一个套路调遍所有模型.md](docs/02-一个套路调遍所有模型.md)。

## 五家速览（实测 2026-10-13）

| 厂商 | base_url | 推荐模型 | 免费政策（📄 官方可查） | 实测 |
|---|---|---|---|---|
| DeepSeek | `https://api.deepseek.com` | `deepseek-v4-flash` | [赠送余额，优先扣减](https://api-docs.deepseek.com/zh-cn/quick_start/pricing) | ✅ |
| Kimi | `https://api.moonshot.cn/v1` | `kimi-k2.6` / `kimi-k3` | —（官方无免费额度说明） | ✅ |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4.7-flash` | [定价页标注免费](https://docs.bigmodel.cn/cn/guide/start/pricing) | ✅ |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-flash` / `qwen3.6-flash` | [新人免费额度](https://help.aliyun.com/zh/model-studio/new-free-quota) | ✅ |
| 豆包（方舟） | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-seed-2-1-pro-260628` | [新用户免费推理额度](https://docs.volcengine.com/docs/ark/free-inference-quota?lang=zh) | ✅ |

## 一键体检

换电脑、过段时间想确认本指南是否还能用？填好根目录 `.env`（模板见 `examples/.env.example`），跑：

```bash
pip install openai
python tests/verify_calls.py
```

脚本会对五家各测「默认调用 / 关闭思考 / 流式」共 15 项，全程不打印 key。这也是本仓库"敢标实测"的底气——**不是我说它对，是脚本刚跑过。**

## 当前覆盖范围（v0.3）

- ✅ 只讲**文本大模型的对话调用**（embedding、生图、语音、视频、Agent 留待后续）
- ✅ 5 家厂商：DeepSeek、Kimi、智谱 GLM、通义千问、豆包
- ✅ Python + 官方 `openai` 库一种写法；普通/思考开关/流式/多轮全部实测
- ⏳ 计划中：文心、星火、MiniMax、混元；Function Calling 专题

## 信息可信度与时效

模型名、价格、免费额度变得非常快。本指南：

- 每条调用方式标注 ✅ **已实测**（附日期）/ 📄 **官方文档** / 💬 **社区经验**；
- 实测脚本就是 [`tests/verify_calls.py`](tests/verify_calls.py)，你可以自己复现；
- 价格等易变信息标 ⚠️ 并附官方链接，用前请复核。

> 最近一次实测：**2026-10-13，五家 15 项全部通过**。发现过期欢迎提 Issue。

## 密钥安全

`.env` 已在 `.gitignore` 中，永远不会被提交。真实 key 不要写进代码、不要发群、不要截图；泄露了立刻去平台删除重建。

## 免责声明

个人学习整理的第三方攻略，与上述厂商无关联，不代表官方立场。商标、模型名称归各自所有者。请以官方文档为准，并留意账户计费设置。

## 致谢与声明

组织方式受开源电子书《高性价比人生指南》（HowToLiveBetter）启发，内容为针对大模型 API 主题独立撰写。

## 开源协议

[Unlicense](LICENSE)——公有领域，随意使用、修改、分发，包括商用，无需署名。
