---
name: model-manual
description: 为 DeepSeek、Kimi、智谱 GLM、通义千问和豆包生成、迁移或排查 OpenAI-compatible 文本模型调用代码。用户询问国产大模型的 API 地址、模型名、思考开关、流式调用或接入报错时使用。
---

# 模型说明书

帮助用户用尽可能少的步骤接入本 Skill 已收录的文本大模型。

## 工作流

1. 确认用户指定的厂商、语言和调用方式；能从现有项目判断时，不重复提问。
2. 读取 [references/vendors.json](references/vendors.json) 中对应厂商的记录。不要凭记忆补写模型名、地址或专属参数。
   - 如果记录含 `model_manual`，继续读取对应模型说明书和 `references/models/` 下的机器卡片；模型级事实优先于厂商级摘要。
3. 普通示例优先运行 `scripts/generate_snippet.py` 生成。需要融入现有项目时，遵循项目已有语言、依赖和代码风格。
4. 用户未指定语言时默认 Python；未指定模型时使用 `default_model`。
5. 返回完整可运行代码，并给出依赖安装命令、所需环境变量和运行命令。
6. 遇到错误时，保留原始状态码并结合厂商的 `notes` 排查；每条 note 自带来源，不要把所有 404 都归因于同一原因。
7. 遇到正文为空、输出截断、JSON 卡住、工具循环、流式解析或 429 时，读取 [`../../docs/06-真实踩雷与生产检查.md`](../../docs/06-真实踩雷与生产检查.md)；先按具体模型确认参数语义，再给修复方案。

## 生成示例

在本 Skill 目录运行：

```bash
python scripts/generate_snippet.py --vendor kimi --language python
python scripts/generate_snippet.py --vendor qwen --language typescript --thinking off
python scripts/generate_snippet.py --vendor doubao --language curl --stream
```

支持的语言是 `python`、`typescript` 和 `curl`。`--thinking off` 只在厂商卡片声明了关闭方法时添加对应请求字段。

## 输出要求

- API Key 必须从厂商卡片规定的环境变量读取，禁止硬编码或在输出中回显完整 Key。
- 明确区分“已实测”“官方文档说明”和“尚未验证”；缺少资料时直接说明未知。
- 每个厂商事实都附上 `sources` 或 `notes.source` 中的官方链接；提到价格、免费额度时直接链接官方价格或额度页，不引用二手汇总。
- 经验性选型或排查建议标注为“项目建议”，并链接仓库的 `docs/来源与核验规则.md`。
- 不把 Chat Completions 兼容表述成完整 OpenAI API 兼容。
- 用户只要代码时保持简洁；用户是新手时补充 Key 申请、安装和运行步骤。
- 除非用户明确要求实际验证，否则只生成或修改代码，不主动发送可能计费的请求。
- 若 `verified_at` 已明显过时，提醒用户先运行仓库中的体检脚本或复核官方文档。

## 当前边界

默认只覆盖文本对话、思考开关和流式输出。模型级机器卡片可以声明 JSON、Tool Calling、图片或 Responses API；未在数据中声明的能力不要推断其兼容性。
