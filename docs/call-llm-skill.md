# 可选安装的 call-llm Skill

[English](../en/docs/call-llm-skill.md) · [Skill 源码](../skills/call-llm/SKILL.md) · [Agent 接入规范](../agents/README.md)

`call-llm` 是本知识库的可安装入口。用户决定是否安装；安装后，在自己的项目里要求 Agent 接入大模型，Agent 会从固定的 [HowToCallLLM 仓库](https://github.com/normalpeople553/HowToCallLLM) 获取接入规范、准确型号卡和示例，再修改当前项目。Skill 自身不内置另一份型号清单。

## 安装

在支持 Codex Skill 的环境中，向 Agent 提出：

> 请使用 skill-installer，从 https://github.com/normalpeople553/HowToCallLLM/tree/main/skills/call-llm 安装 `call-llm`。

安装的是仓库中的 `skills/call-llm` 子目录，不会自动安装到其他用户机器，也不会在安装时创建或填写 Key。Skill 内部名称为 `call-llm`，调用时写 `$call-llm`；界面显示名是 `call_llm`。不安装时仍可直接阅读本仓库的 [Agent 接入规范](../agents/README.md)。

## 共用的 keyenv

首次使用 Skill 时，它会运行 [`keyenv.py`](../skills/call-llm/scripts/keyenv.py) 的 `init`，在用户主目录创建 `~/.call-llm/keyenv`。Windows 对应 `$HOME\.call-llm\keyenv`。文件只含空的变量名；用户只填需要的厂商 Key。已有文件不会被覆盖。

| 变量名 | 用途 |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek |
| `MOONSHOT_API_KEY` | Kimi |
| `ZHIPU_API_KEY` | 智谱 GLM |
| `DASHSCOPE_API_KEY` | 通义千问 |
| `ARK_API_KEY` | 豆包方舟 |
| `DOUBAO_VOICE_API_KEY` | 豆包语音 |
| `MINIMAX_API_KEY` | MiniMax |

编辑文件时一行一个 `NAME=value`，只填写已申请的 Key。可用 `python <已安装 Skill 的路径>/scripts/keyenv.py status` 只查看哪些变量已填写；它不会显示值。文件位于项目和 Git 仓库之外；本仓库的 [`.gitignore`](../.gitignore) 也排除误放进仓库的 `keyenv`。

`keyenv` 是本机明文文件，不是系统密钥库；只适合放在可信的个人开发环境。远程 Agent、容器与线上服务不会自动取得这份本地文件，应在各自环境另行配置凭据。

## 在项目中使用

在当前项目向 Agent 说：

> 使用 `$call-llm`，给这个项目接入 DeepSeek 的普通文本调用。沿用现有语言和依赖，先做离线检查，并告诉我如何启动。

项目代码读取标准环境变量，不依赖用户主目录的固定路径。需要用本地 `keyenv` 启动项目时，运行：

```powershell
python "$HOME\.codex\skills\call-llm\scripts\keyenv.py" run --key DEEPSEEK_API_KEY -- python app.py
```

```bash
python ~/.codex/skills/call-llm/scripts/keyenv.py run --key DEEPSEEK_API_KEY -- python app.py
```

把 `app.py` 换成当前项目的启动命令。仅指定的 Key 会从 `keyenv` 注入该子进程；当前进程已设置同名环境变量时，以当前环境为准。生产部署需要在部署环境另行配置变量。直接运行本仓库的独立示例不会自动加载 `keyenv`，也应使用上述包装命令。

Skill 不读取或回显完整 Key 给 Agent。它会按 [model-manual 规则](../skills/model-manual/SKILL.md)确认准确型号、参数和示例；真实 API 调用按用户授权执行，离线检查与历史示例的实测状态分开报告。
