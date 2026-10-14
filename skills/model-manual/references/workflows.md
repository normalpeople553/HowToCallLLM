# Agent 任务流程

中文 · [English](workflows.en.md) · [Agent 篇](../../../agents/README.md)

本文件记录项目工作流，按任务读取；型号名、参数值与能力结论仍从 [models/](models/) 卡片读取。资料与证据的维护规则见[来源与核验规则](../../../docs/来源与核验规则.md)。

## 接入

适用于新增模型调用，以及 JSON、流式、工具或图片等具体任务。

1. 检查项目已有客户端、配置、依赖和调用入口，确定修改位置；从任务需求判断需要哪些能力，不默认开启思考或增加工具。
2. 读取准确型号卡片的 `identity`、`capabilities` 与 `generation`；需要解释/调整字段时再读下表对应的参数说明。核对接口、Key 环境变量、生命周期、思考开关、输出预算语义和任务约束；`documented` 是官方支持依据，不是实测通过。未知能力先核对官方资料。
3. 需要现成功能代码时，先用 [example_catalog.py](../scripts/example_catalog.py) 按准确型号/能力检索 `examples/sources.json`，读取官方出处、参数说明与验证范围；没有相应例子再查看 [generate_snippet.py](../scripts/generate_snippet.py) 的 `--help` 生成支持的组合。将请求和结果检查融入项目；Python 的厂商扩展字段按卡片放入 `extra_body`，其他 API 按命中示例核对，不套用 Chat 参数。改写后的新组合没有自动获得原文件的线上通过证据。
4. JSON 任务检查结束原因、解析结果并校验业务字段；工具任务使用允许的工具与参数、回传执行结果、保留完整消息并限制轮次。图片任务使用用户提供的输入，不将仅接受图片请求描述成识别准确率验证。
5. 运行与修改相关的离线检查，交付运行命令及未完成的线上验证项。已有项目遵循其依赖管理方式；独立运行本仓库示例使用锁定依赖，见[验证与复现](../../../docs/验证与复现.md)。

参数说明按示例文件映射字段、默认/范围、模式与副作用；只读当前任务对应的一份。厂商事实仍核对其中的官方出处，项目预算和业务校验不当作服务端上限。

| 准确型号 | 参数说明 |
|---|---|
| `deepseek-flash` | [逐项参数](../../../models/deepseek/deepseek-flash/parameters.md) |
| `kimi-k2.6` | [逐项参数](../../../models/kimi/kimi-k2.6/parameters.md) |
| `glm-4.7` | [逐项参数](../../../models/zhipu/glm-4.7/parameters.md) |
| `qwen-flash` | [逐项参数](../../../models/qwen/qwen-flash/parameters.md) |
| `doubao-seed-2-1-pro-260628` | [逐项参数](../../../models/doubao/doubao-seed-2-1-pro-260628/parameters.md) |
| `MiniMax-M2.7` | [逐项参数](../../../models/minimax/MiniMax-M2.7/parameters.md) |

以下命令在仓库根目录运行，只生成示例代码：

```bash
python skills/model-manual/scripts/generate_snippet.py --vendor qwen --model qwen-flash --task json --thinking off --max-tokens 2048
python skills/model-manual/scripts/generate_snippet.py --vendor kimi --model kimi-k2.6 --task tool --thinking off
```

生成器拒绝某个组合时，先区分“型号未声明能力”和“生成器尚无该语言模板”；后者不能直接推断为模型不支持。若需要手写实现，按官方资料与项目需求实现并明确其验证范围。

## 迁移

适用于更换厂商、型号或 SDK。先读取源和目标型号的卡片；源型号未收录时，从现有代码和官方资料建立源配置，不用目标型号反推。

按项目实际使用的功能逐项比较：

| 比较项 | 要确认的行为 |
|---|---|
| 接口与身份 | Key、Base URL、Model ID、地域、模型开通与生命周期 |
| 思考 | 默认行为、开关字段、SDK 扩展位置、历史思考是否需回传 |
| 输出预算 | 参数名称、范围，以及是否包含思考 token |
| 消息与流式 | 消息角色、内容结构、思考字段、空块、结束原因与 usage |
| 结构化输出 | JSON/Schema 支持范围、思考模式限制、解析与业务校验 |
| 工具调用 | tool_choice、参数约束、tool_call_id、完整 assistant 消息与循环上限 |
| 多模态与其他 API | 输入格式、具体型号能力、API 类型；未使用的功能无需扩展 |

区分可以保留的业务逻辑与需要替换的协议代码，再修改实现。不要只替换厂商地址和型号名后宣称迁移完成；也不要把工具流程静默降级成纯文本回答。

对改变的行为执行项目离线测试；交付差异说明、修改位置和未验证项。用户要求真实对比时再调用模型，并说明比较的是固定任务的结果，不能由一次运行推导通用质量排名。

## 排错

读取实际 Model ID、接口、SDK 版本、脱敏请求、原始状态码/业务码、结束原因与可用 usage；信息不足时只请求能区分原因的部分，不索取完整 Key。厂商 `notes` 可从 [vendors.json](vendors.json) 查找，但准确型号规则优先。

下表是排查分支，不是看到一个状态码就能确定根因；厂商错误含义和参数行为必须附对应官方来源。详细机制与代码见[真实踩雷](../../../docs/06-真实踩雷与生产检查.md)和[报错速查](../../../docs/05-新手必会与报错速查.md)。

| 现象 | 下一步 |
|---|---|
| 401 / 403 | 核对 Key 对应的平台、权限、地域或开通情况；保留厂商业务码 |
| 404 | 分别检查接口路径、型号名和部署/开通要求，不直接判定模型下线 |
| 400 | 对照型号卡片检查参数、思考模式、消息格式及工具历史 |
| 429 | 区分账户限制与服务繁忙，按官方规则做有限退避；不记为能力不支持 |
| 超时 / 5xx | 检查网络与服务响应，再按请求性质设置超时和有限重试 |
| HTTP 200 但空正文或截断 | 检查 finish_reason、思考与正文预算，不把重试当成预算修复 |
| JSON 不完整或字段错误 | 检查结束原因、JSON 指令、解析和业务校验，区分格式与语义错误 |
| 断流或 usage 块报错 | 检查空 choices、结束块与正文完整性，不只检查收到过文本 |
| 工具报错或无限循环 | 检查工具名、完整参数、tool_call_id、思考历史及循环上限 |

给出与证据对应的最小修复，并说明如何检查是否解决。日志未提供或无法复现时，把推测写成待检查原因，不伪装成已定位；外部写操作的重试还需按业务处理重复执行。

## 型号发现

用户问厂商还有哪些语言型号时，先查询 [model_catalog.py](../scripts/model_catalog.py) 或对应[语言模型清单](../../../docs/model-lists/README.md)，而不是只返回 `vendors.json` 的默认型号。在仓库根目录执行：

```bash
python skills/model-manual/scripts/model_catalog.py --vendor deepseek
python skills/model-manual/scripts/model_catalog.py --vendor deepseek --model deepseek-v4-pro
```

查询只读本地官方资料快照与已登记代码，不读取 Key、不发请求。按 `checked_at`、`status`、逐行说明和官方来源解释；`available` 是官方文档列出，不是当前账户调用成功。`billing=paid` 不能推断按量入口，预览可能仅限订阅。实时可用性仍需复核官方页面，真实调用另按授权。

`repository_coverage` 按准确厂商和 ID 关联：`manual_path` / `parameters_path` 为维护卡片对应页面，`example_files` 为该准确 ID 的调用文件；公开查询不返回私有实测统计。默认、别名、系列和实际服务版本之间不转移覆盖。无卡片的清单条目不会加入代码生成器；免费发现条目也不改变项目付费默认规则。未知 ID 返回未命中，不静默替换。

用户只要求增加型号清单时，维护 `data/model-lists/<vendor>.json` 的双语字段和官方来源，再生成页面即可；不因此创建详细卡片、宣称实测或更改默认型号。

## 未知型号

用户指定的型号没有机器卡片时，不能用默认卡片覆盖 Model ID 后继续生成。

1. 先查发现清单定位准确 ID 与来源，再从该厂商官方模型页和接口资料核对是否可调用、生命周期、所需任务能力与专属参数；保留官方链接和核对日期。清单未收录不等于官方不支持。
2. 用户只要求完成其项目接入时，可按官方资料手写实现，明确“尚未收录/尚未实测”，无需擅自扩展本知识库。关键行为无法确认时说明缺失项，不猜参数。
3. 用户要求补充本手册时，在 [models/](models/) 新建独立型号卡片，并在仓库 `models/<vendor>/<model-id>/` 增加说明书与必要示例；按相邻卡片的结构和生成器校验要求填写字段。每个 `value` 或 `status` 对应的 `source` 必须能解析，不能复制其他型号事实或报告。缺少文档的能力使用现有结构适用的未知状态；新增调用代码必须先真实运行，本地记录不得公开。
4. 厂商 `default_model` 只在用户要求更改默认型号时修改。当前验证器明确固定了测试型号，[同步脚本](../scripts/sync_verification.py)只生成厂商默认型号摘要；新增卡片不自动获得验证入口或成为默认型号。扩展目录时同步调整受影响的离线检查和验证脚本，避免把新型号测试成旧型号。

新增型号没有统一验证器报告时使用 `verification: null` 和 `verification_scope: "not_run"`，不填写虚构路径。已有统一记录不公开时使用 `verification:null` 与 `verification_scope:private`；公开同步器只展示官方依据与发布边界，不输出计数或报告，也不读取本地记录。新增型号仍需卡片、说明书、示例来源清单和离线检查。

## 证据与验证

先区分解释调用、离线检查和真实复测。普通接入不授权可能计费或上传输入的调用。

公开仓库提供官方出处、参数、规范代码和运行方式，不提供实测报告、模型回复、统计或执行哈希。`verification.live=private` 与 `verification_scope=private` 只表示记录未公开，不等于未执行，也不是可以公开审计的通过证明。缺少本地记录时明确说明，不能从型号卡、代码存在或离线 mock 推断线上成功。

- 查调用方式：按准确型号检索源码与官方出处，不要求读者提供维护者的私有记录。
- 查当前可用性：复核官方生命周期、账户和输入要求；历史维护结果不保证现在能用。
- 新生成或改写的代码：仅报告实际完成的编译、mock 或获授权的真实调用，不能继承原例结果。
- 维护者核验：只在明确需要时读 `.local/evidence/`；按源码/依赖指纹、真实 HTTP 与完整结束检查，不改旧哈希冒充复测。私有目录缺失、记录损坏或指纹变化都不能补成通过。

### 按授权复现真实示例

安装锁定依赖后，在仓库根目录查询清单；默认不读 Key、不发请求：

```bash
python tests/run_example_files.py --vendor kimi
```

仅在用户明确授权后执行；报告默认保存在被 Git 忽略的本地目录：

```bash
python tests/run_example_files.py --execute --file models/kimi/kimi-k2.6/examples/01_basic.py
```

Key 只从所需环境变量或忽略的 .env 读取，不回显或提交。不要无意上传私人媒体；素材、视频选项、超时/间隔和退出码见[验证与复现](../../../docs/验证与复现.md)。私有报告不保存执行时间、耗时或回复正文，任何报告均不得上传公开仓库。统一验证器只覆盖自己的固定测试项，不代表执行了所有示例。

维护者可显式运行 `python tests/check_example_release.py --check --require-passed` 核验本地完整证据；普通公开克隆只使用 `--check` 检查代码目录，没有私有记录时不宣称通过。公共页面和查询不得因本地记录有无而改变。

维护公开卡片、源码或资料后执行：

```bash
python -m unittest discover -s tests -p 'test_*.py'
python skills/model-manual/scripts/sync_verification.py --check
python skills/model-manual/scripts/example_catalog.py --check
python skills/model-manual/scripts/model_catalog.py --check
python scripts/render_human_examples.py --check
python tests/check_example_release.py --check
```

资料变更后先更新相应派生页再检查。交付采用的型号、官方来源、代码、环境变量、运行方法与实际完成的检查；排错说明依据与未确认项，迁移说明行为差异。不要把离线检查写成本次线上通过。
