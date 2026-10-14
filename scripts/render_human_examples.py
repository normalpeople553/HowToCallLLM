#!/usr/bin/env python3
"""Render human-readable code and review guides from current live-tested files.

Never imports or executes an example, reads a key, or calls a model.
The Python blocks are exact source copies, not newly generated API requests.
"""

import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import posixpath
import sys


ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "deepseek": "deepseek-flash", "kimi": "kimi-k2.6", "zhipu": "glm-4.7",
    "qwen": "qwen-flash", "doubao": "doubao-seed-2-1-pro-260628", "minimax": "MiniMax-M2.7",
}
NAMES = {"deepseek": "DeepSeek", "kimi": "Kimi", "zhipu": "智谱 GLM",
         "qwen": "通义千问", "doubao": "豆包", "minimax": "MiniMax"}
NAMES_EN = {**NAMES, "zhipu": "Zhipu GLM", "qwen": "Qwen", "doubao": "Doubao"}
# Reading prompts refer to actual code, not additional vendor capability claims.
# A missing anchor blocks regeneration so source changes require editorial review.
READING = {
    "deepseek": [
        ('client = OpenAI(', '先核对环境变量、服务地址和网络超时；不要把 timeout 当成 token 预算。',
         'Check the key environment variable, service URL and network timeout; timeout is not a token budget.'),
        ('model="deepseek-flash"', '准确请求 Flash；本例没有显式设置思考开关、输出预算或采样参数，不能读成已经关闭思考或限制输出长度。',
         'The request targets this exact Flash ID. It sets no thinking switch, output budget or sampling control; do not read omission as disabled thinking or an explicit output limit.'),
        ('def completed_text(', 'Agent 代码也应检查结束原因、待处理工具调用和非空最终正文，不能只打印 choices[0] 就算完整成功。',
         'Review finish reason, unhandled tool calls and nonempty final content; printing choices[0] alone is not complete success.'),
    ],
    "kimi": [
        ('client = OpenAI(', '核对 MOONSHOT_API_KEY 与本例 Moonshot /v1 地址；不要因名称叫 Kimi 就改用别的产品入口。',
         'Match MOONSHOT_API_KEY to this Moonshot /v1 URL, not another product endpoint.'),
        ('model="kimi-k2.6"', '本例固定 K2.6 且省略思考开关；Agent 若改型号或增加思考、预算字段，需要读新组合的参数依据。',
         'This file fixes K2.6 and omits a thinking switch. A different model or added thinking/budget fields need their own parameter evidence.'),
        ('def completed_text(', '区分思考与最终答案；这里只接受正常结束且非空的最终正文。',
         'Distinguish thinking from the final answer; this helper accepts only normally completed, nonempty final content.'),
    ],
    "zhipu": [
        ('timeout=120, max_retries=0', 'SDK 自动重试已关闭，本地退避函数负责有限重试；不要叠加两层重试。',
         'SDK retries are disabled; the local helper owns bounded retries. Do not multiply two retry layers.'),
        ('def create_with_backoff(', '只有 HTTP 429 且业务码为 1302/1305 才进入本例重试，最多三次；不是所有 429 都会稍等即恢复。',
         'Only HTTP 429 with business code 1302/1305 enters this retry path, with at most three attempts; not every 429 is transient.'),
        ('client, model="glm-4.7"', '核对付费准确型号 glm-4.7；不能换成免费 Flash 后继承本文件的实测。01 也未显式设置思考开关或输出预算。',
         'Check the exact paid glm-4.7 ID, not free Flash with inherited evidence. This basic file also omits thinking and output-budget controls.'),
        ('def completed_message(', '唯一候选、正常结束、无待处理工具、非空正文都要检查；固定脱敏错误不应被改成公开输出完整原始响应。',
         'Check one candidate, normal completion, no unhandled tools and nonempty content. Do not replace sanitized errors with public raw responses.'),
    ],
    "qwen": [
        ('client = OpenAI(', '核对 DASHSCOPE_API_KEY 和本例兼容地址；区域或产品入口改变时另查对应配置。',
         'Match DASHSCOPE_API_KEY and this compatible URL. A region or product change needs its own configuration check.'),
        ('model="qwen-flash"', '这是准确 ID qwen-flash，不是所有名称带 Flash 的新版。01 未显式设置思考、预算或采样字段。',
         'The exact ID is qwen-flash, not every newer model named Flash. This basic file sets no explicit thinking, budget or sampling fields.'),
        ('def completed_text(', '不要删掉结束状态和最终正文校验；同名参数在不同代际的适用性不能从本文件推导。',
         'Keep finish-state and final-content checks. This file does not establish same-named parameter support in other generations.'),
    ],
    "doubao": [
        ('client = OpenAI(', '核对 ARK_API_KEY、北京 /api/v3 地址和完整日期版 Model ID；订阅简称不能直接当成同一个按量 API 型号。',
         'Match ARK_API_KEY, the Beijing /api/v3 URL and full dated model ID. Subscription shorthand is not the same metered API identity.'),
        ('extra_body={"thinking": {"type": "disabled"}}', '本例通过 Python SDK 的 extra_body 发送关闭思考配置；没有显式发送输出预算，不表示代码已限制总输出。',
         'This file sends disabled thinking through Python SDK extra_body. It sets no explicit output budget; do not claim a coded total-output limit.'),
        ('def completed_text(', '有 HTTP 响应不等于正文完整，仍需核对 finish_reason、工具状态和最终文本。',
         'An HTTP response is not proof of complete content; check finish_reason, pending tools and final text.'),
    ],
    "minimax": [
        ('extra_body={"reasoning_split": True}', 'reasoning_split 用于拆分思考输出，不是关闭思考；不要把其他型号的开关移植到 M2.7。',
         'reasoning_split separates thinking output; it does not disable thinking. Do not transplant another model\'s controls to M2.7.'),
        ('max_completion_tokens=16384', '16384 是这个源文件的项目演示预算，不是型号上限、官方默认或保证得到同样长的正文。',
         '16384 is this file\'s demonstration budget, not the model limit, official default or a guaranteed final-answer length.'),
        ('def completed_text(', '检查可用业务状态、正常结束和最终正文；HTTP 200 本身不足以证明成功。',
         'Check the business status when present, normal completion and final content; HTTP 200 alone is insufficient.'),
        ('def final_text(', '去除完整 `<think>` 段只用于展示；缺少闭合标签或只有思考时不能冒充最终答案，工具历史仍须保留原消息。',
         'Removing complete `<think>` spans is for display only. Unclosed or thinking-only content is not a final answer; tool history must retain original messages.'),
    ],
}
REVIEW_CASES = [
    ("zhipu", "02_streaming.py", "流式", "Streaming",
     "处理空 choices，检查正常结束和非空正文；finally 关闭流，消费中断后不自动重放。",
     "Handle empty choices, require normal completion and nonempty content, close in finally, and do not replay after interrupted consumption."),
    ("kimi", "04_json_output.py", "JSON", "JSON",
     "检查该型号的 response_format 与提示词，先验收结束状态再解析 JSON，还要校验字段、类型及业务值。",
     "Check model-specific response_format and prompting; validate completion before parsing JSON, then check fields, types and application values."),
    ("zhipu", "07_thinking_tools.py", "工具闭环", "Tool loop",
     "先整批校验名称、ID 与参数，再执行允许的工具；完整回传 assistant 和匹配 tool_call_id 的结果，限制轮数并取得最终答复。示例库存为模拟数据。",
     "Validate the entire batch of names, IDs and arguments before allowlisted execution. Return complete assistant history and matching tool_call_id results, bound rounds and obtain a final answer. Inventory data is simulated."),
    ("kimi", "06_vision.py", "图片", "Images",
     "先确认准确型号与输入格式；本例读本地 PNG/JPEG 并构造 content 数组，不能把别家远程 URL 写法直接搬来。请求被接受不代表识别准确率已验证。",
     "Check the exact model and input format. This example reads local PNG/JPEG into a content array; do not transplant another provider's remote-URL format. Request acceptance does not establish recognition accuracy."),
]


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependencies(root):
    # Code comes from this tool's checkout, fixture data from the supplied root.
    return (_module("human_example_catalog", ROOT / "skills/model-manual/scripts/example_catalog.py"),
            _module("human_example_release", ROOT / "tests/check_example_release.py"))


def build_views(root=ROOT):
    root = Path(root).resolve()
    catalog, release_tool = dependencies(root)
    release = release_tool.collect_release(root)
    if not release["catalog_valid"] or release["catalog_issues"] or release["report_issues"]:
        raise ValueError("invalid_example_evidence")
    evidence = {row["path"]: row for row in release["rows"]}
    entries = catalog.select_examples(catalog.load_catalogs(root))
    references = root / "skills/model-manual/references"
    defaults = json.loads((references / "vendors.json").read_text(encoding="utf-8"))["vendors"]
    views = []
    for vendor, model in MODELS.items():
        card = json.loads((references / "models" / (model + ".json")).read_text(encoding="utf-8"))
        if (card["model_id"] != model or card["vendor"] != vendor
                or defaults[vendor]["default_model"] != model or card["billing"]["type"]["value"] != "paid"):
            raise ValueError("reading_guide_model_needs_review")
        matching = [entry for entry in entries if entry["vendor"] == vendor and entry["model_id"] == model]
        basic = [entry for entry in matching if entry["file"] == "01_basic.py"]
        if len(basic) != 1:
            raise ValueError("missing_exact_basic_example")
        entry = basic[0]
        row = evidence.get(entry["path"], {})
        selected = row.get("selected") or {}
        if (row.get("status") != "passed" or row.get("model_id") != model or row.get("vendor") != vendor
                or not selected.get("strict_passed") or not selected.get("current_source")):
            raise ValueError("basic_example_lacks_current_http_evidence")
        source_path = root / entry["path"]
        if not source_path.resolve().is_relative_to(root):
            raise ValueError("example_outside_repository")
        source = source_path.read_bytes().decode("utf-8")
        if "```" in source or not source.endswith("\n"):
            raise ValueError("source_cannot_be_embedded_as_python_fence")
        ast.parse(source)  # Syntax only; importing this source would make API calls.
        notes = {"zh": [], "en": []}
        for anchor, chinese, english in READING[vendor]:
            locations = [i for i, line in enumerate(source.splitlines(), 1) if anchor in line]
            if len(locations) != 1:
                raise ValueError("reading_anchor_needs_editorial_review")
            for lang, description in (("zh", chinese), ("en", english)):
                notes[lang].append({"line": locations[0], "anchor": anchor, "description": description})
        identities = catalog.file_identity(root, entry["path"])
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if identities.get(entry["path"]) != digest:
            raise ValueError("example_source_identity_mismatch")
        views.append({"vendor": vendor, "model_id": model, "path": entry["path"],
                      "source_text": source, "source_sha256": digest, "support_sha256": identities,
                      "evidence_id": selected.get("evidence_id"), "report": selected["report"],
                      "parameters_path": entry["parameters_path"],
                      "sources": [source["url"] for source in entry["sources"]],
                      "notes": notes, "required_env": entry["required_env"], "run_command": entry["run_command"],
                      "related_examples": [{"path": item["path"], "capability": item["capability"]}
                                           for item in matching if item["path"] != entry["path"]]})
    return views


def _link(page, target, label):
    return f"[{label}]({posixpath.relpath(Path(target).as_posix(), page.parent.as_posix())})"


def expected_pages(root=ROOT):
    views = build_views(root)
    pages = {}
    for english in (False, True):
        lang, suffix = ("en", ".en.md") if english else ("zh", ".md")
        index = Path("human/examples") / ("README" + suffix)
        lines = ["# Read model calls and review Agent code" if english else "# 阅读模型调用代码并检查 Agent 实现", "",
                 _link(index, "human/README" + suffix, "Human guide" if english else "人类篇") + " · " +
                 _link(index, "human/examples/README" + (".md" if english else ".en.md"), "中文" if english else "English"), "",
                 ("Choose a model below to read complete, executable Python code with line-linked explanations, parameter references, run commands and original execution evidence. Use it to learn the call and review an Agent's implementation."
                  if english else "选择下面的型号，直接阅读完整可运行的 Python 代码、关键行解释、参数说明、运行方式和原始实测证据。既可以照着学习调用，也可以用来人工检查 Agent 的实现。"), "",
                 ("Code blocks are copied unchanged from the canonical files in models/, not shortened teaching fragments. Both languages show the same executed code, including its original comments and prompts. Review identity, request semantics and completion checks; variable names and wrappers need not look identical. Changes to model, parameters, inputs or protocol require their own verification."
                  if english else "代码块逐字来自 models/ 下的规范文件，不是删掉校验的教学短片段；中英文展示同一份执行过的代码，保留原注释和提示词。核对的是型号身份、请求语义和结果验收，不要求变量名或封装完全一样。型号、参数、输入或协议改变后，需要验证改变后的路径。"), "",
                 "## Choose a worked example" if english else "## 按型号看完整代码", "",
                 "| Model | Code and review notes |" if english else "| 准确型号 | 代码与人工核对 |", "|---|---|"]
        for view in views:
            name = (NAMES_EN if english else NAMES)[view["vendor"]]
            lines.append(f"| `{view['model_id']}` | {_link(index, 'human/examples/' + view['vendor'] + suffix, name)} |")
        lines += ["", "## Before running" if english else "## 运行前确认", "",
                  ("Use the locked environment in " if english else "按") +
                  _link(index, "en/docs/verification.md" if english else "docs/验证与复现.md", "verification" if english else "验证与复现") +
                  (" and set the listed key environment variable locally. Reading these pages or running the renderer makes no API request; running a Python example calls the provider and may incur charges. A root .env is not automatically loaded by standalone examples. Never publish a key or overwrite an existing .env with a template."
                   if english else "准备锁定环境，并在本地设置所列 Key 环境变量。阅读页面或运行生成器不会发请求；运行 Python 示例会真实调用并可能计费。独立示例不会自动加载根目录 .env。不要公开密钥，也不要用模板覆盖已有 .env。"), "",
                  "## Human review checklist" if english else "## 检查 Agent 代码的清单", "",
                  ("Project review criteria: compare these behaviors with the exact model's parameter guide and official sources. No single visual inspection proves production readiness."
                   if english else "以下为项目人工验收建议：对照准确型号的参数页、官方来源和实际代码检查这些行为。人工看过代码不等于生产验收通过。"), "",
                  ("1. Identity and safety: verify exact model, API product/region and key variable. No hard-coded or logged secrets, and no silent free-model fallback."
                   if english else "1. 身份与安全：准确型号、API 产品/地域、Key 变量对应；不硬编码或打印密钥，不静默回退免费型号。"),
                  ("2. Parameters: separate SDK options, model request fields and local application checks. An output budget is not a setting for the context window; omission is not an explicit switch. Verify thinking and budget semantics for that exact model."
                   if english else "2. 参数：分清 SDK 配置、模型请求和本地业务校验；输出预算不是上下文窗口设置，省略字段不是显式开关。思考和预算语义按准确型号查证。"),
                  ("3. Results: check normal completion, final content and any provider business status. Thinking-only content, truncation and a pending tool call are not a complete final answer."
                   if english else "3. 结果：检查正常结束、最终正文及适用的厂商业务状态；仅有思考、截断或待处理工具调用，都不是完整最终答案。"),
                  ("4. Evidence: request exact changed files, commands and test scope. Offline mocks, accepted HTTP requests, old-file reports and the Agent's own assertion are different evidence."
                   if english else "4. 证据：索要实际修改文件、运行命令与测试范围；离线 mock、HTTP 请求被接受、旧文件报告和 Agent 自称成功不是同一层证据。"), "",
                  _link(index, "docs/参数说明与调参.md" if not english else "en/docs/parameters.md", "Parameter definitions" if english else "参数定义与官方出处") + " · " +
                  _link(index, "docs/来源与核验规则.md" if not english else "en/docs/evidence-policy.md", "Evidence and safety rules" if english else "证据与安全规则"), "",
                  "## Review advanced behavior" if english else "## 继续检查进阶调用", ""]
        for vendor, filename, zh, en, chinese, translated in REVIEW_CASES:
            folder = Path("models") / vendor / MODELS[vendor]
            lines += ["- " + _link(index, folder / "examples" / filename, en if english else zh) + "：" +
                      (translated if english else chinese) + " " + _link(index, folder / ("parameters" + suffix), "Parameters" if english else "参数依据")]
        lines += ["", ("These links open the existing full files, not generic cross-model templates. Check their current per-file status and input requirements before running; the basic examples' reports do not cover every advanced combination."
                       if english else "上述链接打开已有完整源文件，不是跨型号通用模板。运行前核对各自的逐文件状态和输入要求；基础示例的报告不覆盖任意进阶组合。"), "",
                  _link(index, "en/docs/example-status.md" if english else "docs/示例实测状态.md", "Per-file status" if english else "逐文件实测状态") + " · " +
                  _link(index, "en/docs/example-index.md" if english else "docs/官方示例索引.md", "All feature examples" if english else "全部功能示例") + " · " +
                  _link(index, "scripts/render_human_examples.py", "Page renderer" if english else "页面生成器"), ""]
        pages[index] = "\n".join(lines)
        for view in views:
            page = Path("human/examples") / (view["vendor"] + suffix)
            model_folder = Path(view["path"]).parent.parent
            parameters = Path(view["parameters_path"]).with_name("parameters" + suffix)
            name = (NAMES_EN if english else NAMES)[view["vendor"]]
            lines = [f"# {name} " + ("calling code and human review" if english else "调用代码与人工核对"), "",
                     _link(page, index, "All worked examples" if english else "全部代码阅读页") + " · " +
                     _link(page, Path("human/examples") / (view["vendor"] + (".md" if english else ".en.md")), "中文" if english else "English"), "",
                     f"`{view['model_id']}` · " + _link(page, model_folder / ("README" + suffix), "Model manual" if english else "型号说明书") + " · " +
                     _link(page, parameters, "Parameter reference" if english else "逐项参数说明"), "",
                     "## Run the complete example" if english else "## 运行完整示例", "",
                     ("Set the following environment variable locally, after preparing the " if english else "按") +
                     _link(page, "en/docs/verification.md" if english else "docs/验证与复现.md", "locked environment" if english else "锁定环境步骤") +
                     (": " if english else "准备环境，在本地设置：") + ", ".join(f"`{key}`" for key in view["required_env"]) + ("." if english else "。"), "",
                     ("Standalone examples read exported environment variables, not .env automatically. Running the command makes a real request and may incur charges."
                      if english else "独立示例读取已导出的环境变量，不自动加载 .env；执行下列命令会真实调用并可能计费。"), "",
                     "```bash", view["run_command"], "```", "",
                     ("Complete source, copied unchanged from " if english else "下面是完整源文件，逐字来自") +
                     _link(page, view["path"], "the canonical file" if english else "规范文件") + (":" if english else "："), "",
                     "```python\n" + view["source_text"] + "```", "",
                     "## Read the important lines" if english else "## 关键行应该怎么看", ""]
            for note in view["notes"][lang]:
                lines.append("- " + _link(page, view["path"] + f"#L{note['line']}",
                                          ("Line " if english else "第 ") + str(note["line"]) + ("" if english else " 行")) +
                             (": " if english else "：") + note["description"] + " " + _link(page, parameters, "Parameter evidence" if english else "参数依据"))
            lines += ["", "## What should count as success" if english else "## 运行后应该检查什么", "",
                      (("The code writes final content to stdout and usage statistics to stderr. " if english else "代码把最终正文写到标准输出，把用量写到标准错误流。")
                       if view["vendor"] == "zhipu" else ("The code prints final content and usage statistics. " if english else "代码打印最终正文和用量统计。")) +
                      ("Wording is not fixed: the original reports intentionally omit answer text. Normal completion and nonempty final content are acceptance checks, not proof of factual answer accuracy. A thrown error is a failed check, not something to hide by removing the helper."
                       if english else "回答措辞不是固定值，原始报告也刻意不保存回答正文。正常结束、非空正文是验收条件，不证明答案事实准确。抛出异常表示相应检查未通过，不应通过删除校验函数掩盖。"), "",
                      _link(page, view["path"], "Actual output/check logic" if english else "实际输出与校验逻辑") + " · " +
                      _link(page, "en/docs/evidence-policy.md" if english else "docs/来源与核验规则.md", "Evidence boundaries" if english else "证据边界"), "",
                      "## Original execution evidence" if english else "## 对应的原始实测证据", "",
                      ("The current source has passed real HTTP evidence. " if english else "当前源码已有通过的真实 HTTP 证据。") +
                      _link(page, view["report"], "Original sanitized report" if english else "原始脱敏报告") + " · " +
                      _link(page, "en/docs/example-status.md" if english else "docs/示例实测状态.md", "Current status" if english else "当前状态"), "",
                      ("Source SHA-256: " if english else "源文件 SHA-256：") + f"`{view['source_sha256']}`", "",
                      ("This page is a reading view of that exact file, not another live run. It does not verify an Agent's changed code, arbitrary prompts or parameters, other model IDs, or present account availability."
                       if english else "本页是该准确文件的阅读视图，不是又一次线上实测；它不验证 Agent 改写后的代码、任意提示词/参数组合、其他型号或当前账户可用性。"), "",
                      "## Official sources and advanced examples" if english else "## 官方出处与进阶示例", ""]
            lines.extend(f"- [Official source {i}]({url})" if english else f"- [官方出处 {i}]({url})"
                         for i, url in enumerate(view["sources"], 1))
            lines += ["", _link(page, parameters, "Full parameter explanations and official citations" if english else "全部参数解释与官方引用"), ""]
            for entry in view["related_examples"]:
                lines.append("- " + _link(page, entry["path"], entry["capability"] + " · " + Path(entry["path"]).name))
            lines.append("")
            pages[page] = "\n".join(lines)
    return pages


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true", help="read-only default")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        pages = expected_pages(root)
        stale = []
        for relative, content in pages.items():
            target = root / relative
            if not target.resolve().is_relative_to(root):
                raise ValueError("page_outside_repository")
            if args.write:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            elif not target.is_file() or target.read_text(encoding="utf-8") != content:
                stale.append(relative.as_posix())
        print(json.dumps({"written_pages" if args.write else "checked_pages": len(pages), "stale_pages": stale}))
        return 2 if stale else 0
    except (ValueError, SyntaxError, OSError, KeyError, TypeError, AttributeError):
        print(json.dumps({"error": "invalid_source_or_current_http_evidence"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
