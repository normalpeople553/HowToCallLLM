---
name: call-llm
description: Add or update LLM API calls in the user's current software project using normalpeople553/HowToCallLLM. Use when the user wants an Agent to select an exact model, configure local API keys, integrate chat/streaming/JSON/tools or troubleshoot an existing integration. Also use when asked to create or inspect the shared local keyenv file. Do not activate for general LLM discussion without a project or key setup request.
---

# Call LLM

把 [HowToCallLLM](https://github.com/normalpeople553/HowToCallLLM) 用作接入资料源，修改用户当前项目。这个 Skill 是可选安装的入口；型号事实、示例与接入规则以资料仓库的当前版本为准，不复制一份容易过期的模型表。

## 本机 Key

首次使用时用本 Skill 的实际安装路径运行 `python <Skill目录>/scripts/keyenv.py init`，不要相对于当前项目寻找 `scripts/`。它在用户主目录创建 `~/.call-llm/keyenv`，只写空字段；已存在时原样保留。告诉用户路径及所需变量名，由用户自行填写。不要读取、回显、复制或上传完整 Key。`python <Skill目录>/scripts/keyenv.py status` 只显示哪些变量已填写。文件名是 `keyenv`，不是仓库内的 `.env`。

用户若要求本机运行，可用 `python <Skill目录>/scripts/keyenv.py run --key <所需变量名> -- <命令及参数>`；脚本仅从 `keyenv` 加载指定 Key，且会移除子进程环境中其他已知厂商的 Key。已存在的同名进程环境变量优先。普通项目代码只从对应环境变量读取，不硬编码用户主目录路径，也不把 `keyenv` 复制到项目。部署环境的 Key 由该环境单独配置。直接运行 HowToCallLLM 的独立示例不会自动加载 `keyenv`；用上述 `run` 包装命令。

`keyenv` 是本机明文文件，不是系统密钥库；仅在可信的本机环境使用。远程 Agent、容器和线上部署无法自动读取用户电脑上的文件，需在各自运行环境配置凭据。

## 取得最新接入资料

固定官方资料仓库为 `https://github.com/normalpeople553/HowToCallLLM.git`。先查当前环境是否已有该仓库的可用 checkout；否则克隆到用户缓存目录，并在使用前从 `origin/main` 更新。核对 remote URL，拒绝把同名的其他仓库当资料源。更新失败时可使用已核对的本地版本，但要说明其提交号和未能确认的新旧状态。只读资料，不把用户项目或 `keyenv` 提交到该仓库。

在资料仓库根目录阅读 `skills/model-manual/SKILL.md`，然后按任务读取其 `references/workflows.md`、准确型号卡、参数页和对应完整示例。需要查其他型号时先运行 `skills/model-manual/scripts/model_catalog.py`，需要具体能力代码时运行 `skills/model-manual/scripts/example_catalog.py`；不要仅凭模型系列名改写示例的 `model` 字段。资料仓库中 `verification.live=private` 是维护者记录，不代表本次项目代码已实测。

## 接入当前项目

1. 检查用户项目已有语言、依赖、调用入口、部署方式和测试方式，确定所需能力。尊重用户指定的厂商与准确型号；未指定时按 `model-manual` 的厂商默认规则选择，并说明选择结果。
2. 从准确型号卡和示例确认 API 地址、环境变量、请求字段、思考/预算限制、输入模态和响应检查。只把所需代码与依赖加到当前项目；沿用项目现有结构。
3. 让应用读取标准环境变量。需要本地验证时通过 `keyenv.py run --key ...` 启动；缺少 Key 时先完成无需 Key 的实现与离线检查，告诉用户应填写哪一项。
4. 做与修改相称的编译、离线测试或项目检查。真实 API 调用会计费或发送输入，只在用户已授权时执行。报告准确型号、来源提交、修改位置、运行命令和实际完成的验证；不要把其他文件的历史实测写成本次结果。

若用户只要求创建或检查 `keyenv`，完成那件事即可，不克隆资料仓库或修改项目。
