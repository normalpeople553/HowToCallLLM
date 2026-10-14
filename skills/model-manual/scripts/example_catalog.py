#!/usr/bin/env python3
"""离线检索各型号官方改写示例，并生成唯一的人类阅读索引。"""

import argparse
from datetime import date
import json
from pathlib import Path
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[3]
INDEX = Path("docs/官方示例索引.md")
HOSTS = {
    "deepseek": {"api-docs.deepseek.com"},
    "kimi": {"platform.kimi.com"},
    "qwen": {"help.aliyun.com"},
    "zhipu": {"docs.bigmodel.cn"},
    "doubao": {"docs.volcengine.com", "www.volcengine.com"},
    "minimax": {"platform.minimax.io", "platform.minimax.cn", "platform.minimaxi.com"},
}
OFFLINE_STATES = {"not_run", "compile_checked", "mock_tested"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sources(sources, vendor):
    _require(isinstance(sources, list) and bool(sources), "每个示例/未集成项需要官方来源")
    for source in sources:
        parsed = urlparse(source.get("url", ""))
        _require(parsed.scheme == "https" and parsed.hostname in HOSTS[vendor], "来源必须是对应厂商官方 HTTPS 页面")
        _require(bool(source.get("title")), "来源缺少标题")


def load_catalogs(root=ROOT):
    catalogs = []
    for path in sorted((root / "models").glob("*/*/examples/sources.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        vendor, model = path.parts[-4], path.parts[-3]
        _require(data.get("schema_version") == 1, f"{path}: 不支持 schema_version")
        _require(data.get("vendor") == vendor and vendor in HOSTS, f"{path}: 厂商/路径不一致")
        _require(data.get("model_id") == model, f"{path}: 型号/路径不一致")
        date.fromisoformat(data["checked_at"])
        entries = data.get("examples", [])
        _require(isinstance(entries, list) and bool(entries), f"{path}: 缺少示例")
        ids, files = set(), set()
        for entry in entries:
            filename = entry.get("file", "")
            _require(Path(filename).name == filename and filename not in {"", ".", ".."}, "示例必须为当前目录中的文件")
            _require((path.parent / filename).is_file(), f"示例不存在：{filename}")
            _require(filename not in files and entry.get("id") not in ids, "示例文件/ID 重复")
            files.add(filename)
            ids.add(entry.get("id"))
            for key in ("id", "title", "capability", "run_command"):
                _require(isinstance(entry.get(key), str) and bool(entry[key].strip()), f"示例缺少 {key}")
            _require(entry.get("origin") == "adapted_from_official", "需要标明官方改写来源")
            _sources(entry.get("sources"), vendor)
            for key in ("required_env", "adaptations"):
                _require(isinstance(entry.get(key), list) and bool(entry[key]) and all(isinstance(v, str) and v for v in entry[key]), f"示例缺少 {key}")
            verification = entry.get("verification", {})
            _require(verification.get("offline") in OFFLINE_STATES, "未知离线验证状态")
            # 本版没有文件级真实调用报告；未来支持 passed 时须同时实现报告校验。
            _require(verification.get("live") == "not_run" and bool(verification.get("note")), "文件级线上验证必须标明本次未运行")
        runnable = {p.name for p in path.parent.iterdir() if p.suffix in {".py", ".ts", ".sh"} and not p.name.startswith("_")}
        _require(files == runnable, f"{path}: 清单与可运行文件不一致：{sorted(files ^ runnable)}")
        for item in data.get("not_integrated", []):
            _require(bool(item.get("capability")) and bool(item.get("reason")), "未集成项缺少能力/原因")
            _sources(item.get("sources"), vendor)
        data["catalog_path"] = path.relative_to(root).as_posix()
        catalogs.append(data)
    _require(bool(catalogs), "未找到示例清单")
    return catalogs


def select_examples(catalogs, vendor=None, model=None, capability=None):
    result = []
    for catalog in catalogs:
        if vendor and catalog["vendor"] != vendor or model and catalog["model_id"] != model:
            continue
        for entry in catalog["examples"]:
            if capability and entry["capability"] != capability:
                continue
            result.append({
                "vendor": catalog["vendor"], "model_id": catalog["model_id"],
                "checked_at": catalog["checked_at"], "catalog_path": catalog["catalog_path"],
                "path": str(Path(catalog["catalog_path"]).parent / entry["file"]).replace("\\", "/"),
                **entry,
            })
    return result


def selection_diagnostics(catalogs, vendor=None, model=None, capability=None):
    """无命中时给出当前型号的可用词与边界；不把缺示例写成不支持。"""
    result = []
    for catalog in catalogs:
        if vendor and catalog["vendor"] != vendor or model and catalog["model_id"] != model:
            continue
        result.append({
            "vendor": catalog["vendor"], "model_id": catalog["model_id"],
            "catalog_path": catalog["catalog_path"],
            "available_capabilities": sorted({entry["capability"] for entry in catalog["examples"]}),
            "not_integrated": [item for item in catalog.get("not_integrated", []) if not capability or item["capability"] == capability],
        })
    return result


def render_index(catalogs):
    lines = [
        "# 官方功能示例索引", "",
        "> 本页由各型号的 `examples/sources.json` 生成；修改清单后运行同步命令，不手改本页。", "",
        "这里的代码是**基于官方文档改写的项目示例**，不是厂商发布的 SDK，也不是官方示例原文镜像。"
        "每项清单记录官方链接、准确型号、所需环境变量、运行命令、改写说明和文件级验证范围。", "",
        "## 如何使用", "",
        "在仓库根目录安装 [requirements-lock.txt](../requirements-lock.txt)，设置对应 Key 和输入变量后运行文件。"
        "Python 示例共用锁定环境；TypeScript 另需 Node.js、`openai` 与 `tsx`，cURL 例子另需 curl/bash/Python。"
        "图片或视频会发送到对应厂商，请仅使用获准上传的内容。", "",
        "按功能给 Agent 查询（只读取清单，不发送请求）：", "",
        "```bash",
        "python skills/model-manual/scripts/example_catalog.py --vendor deepseek --capability vision",
        "python skills/model-manual/scripts/example_catalog.py --model kimi-k2.6 --capability video_input",
        "python skills/model-manual/scripts/example_catalog.py --write-index",
        "python skills/model-manual/scripts/example_catalog.py --check",
        "```", "",
        "输出 JSON 含完整命令与改写说明；能力词不确定时先仅传 `--model` 列出该型号的示例。"
        "找不到型号或功能时退出码为 2，已收录型号同时给出候选能力和匹配的未集成说明，不回退到别的型号。"
        "下表中环境变量的 `|` 表示二选一（Key 始终必需），可选变量见文件说明。", "",
        "## 验证标记", "",
        "- `mock_tested`：用假 SDK 执行代码检查请求/消息/失败分支，不代表服务端接受或识别质量。",
        "- `compile_checked`：仅语法编译检查；`not_run`：该类检查未执行。",
        "- 所有 `live=not_run` 表示本次未对该示例发起真实请求。型号历史报告见[验证状态](验证状态.md)，不能自动继承为新增文件的实测证据。", "",
    ]
    for catalog in catalogs:
        directory = Path(catalog["catalog_path"]).parent.as_posix()
        lines.extend([
            f"## {catalog['vendor']} · `{catalog['model_id']}`", "",
            f"资料核对：{catalog['checked_at']}；[来源、命令及改写清单](../{catalog['catalog_path']})。", "",
            "| 功能 / 文件 | 能力检索词 | 必需环境变量 | 官方来源 | 离线 / 本次线上 |",
            "|---|---|---|---|---|",
        ])
        for entry in catalog["examples"]:
            sources = " · ".join(f"[{s['title'].replace('|', '/')}]({s['url']})" for s in entry["sources"])
            env = "<br>".join(v.replace("|", "或") for v in entry["required_env"])
            check = entry["verification"]
            lines.append(f"| [{entry['title']}](../{directory}/{entry['file']}) | `{entry['capability']}` | {env} | {sources} | {check['offline']} / {check['live']} |")
        if catalog.get("not_integrated"):
            lines.extend(["", "尚未集成的官方功能或型号边界（不把“没有示例”直接解释为不支持）：", ""])
            for item in catalog["not_integrated"]:
                sources = " · ".join(f"[{s['title']}]({s['url']})" for s in item["sources"])
                lines.append(f"- `{item['capability']}`：{item['reason']} {sources}")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor", choices=sorted(HOSTS))
    parser.add_argument("--model")
    parser.add_argument("--capability", help="精确能力词；不确定时先仅用 --model 列出该型号示例")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write-index", action="store_true", help="从清单生成中文 Markdown 索引")
    action.add_argument("--check", action="store_true", help="检查清单与生成索引是否一致")
    args = parser.parse_args(argv)
    if (args.write_index or args.check) and (args.vendor or args.model or args.capability):
        parser.error("索引生成/检查不能使用筛选参数")
    try:
        catalogs = load_catalogs()
        if args.write_index or args.check:
            content = render_index(catalogs)
            if args.write_index:
                (ROOT / INDEX).write_text(content, encoding="utf-8")
                print(INDEX.as_posix())
            elif not (ROOT / INDEX).exists() or (ROOT / INDEX).read_text(encoding="utf-8") != content:
                raise ValueError("索引过期，请运行 --write-index")
            else:
                print("示例清单与索引一致")
        else:
            result = select_examples(catalogs, args.vendor, args.model, args.capability)
            if not result:
                diagnostics = selection_diagnostics(catalogs, args.vendor, args.model, args.capability)
                if diagnostics:
                    print(json.dumps({"selection_hints": diagnostics}, ensure_ascii=False, indent=2), file=sys.stderr)
                raise ValueError("未收录此型号/功能示例；请核对官方资料，不能套用别的型号")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError) as exc:
        print(f"示例清单错误：{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
