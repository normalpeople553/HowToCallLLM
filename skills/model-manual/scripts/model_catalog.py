#!/usr/bin/env python3
"""Official language-model discovery, distinct from maintained cards and live evidence.

Default: read-only JSON query; no network, credentials or model requests.
--write-pages regenerates both editions; --check detects stale generated pages.
"""

import argparse
from datetime import date
import importlib.util
import json
from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[3]
VENDORS = ("deepseek", "kimi", "zhipu", "qwen", "doubao", "minimax")
NAMES = {"deepseek": "DeepSeek", "kimi": "Kimi", "zhipu": "智谱 GLM",
         "qwen": "通义千问", "doubao": "豆包", "minimax": "MiniMax"}
NAMES_EN = {**NAMES, "zhipu": "Zhipu GLM", "qwen": "Qwen", "doubao": "Doubao"}
OFFICIAL_HOSTS = {
    "deepseek": {"api-docs.deepseek.com"},
    "kimi": {"platform.kimi.com", "platform.moonshot.cn"},
    "zhipu": {"docs.bigmodel.cn", "open.bigmodel.cn", "bigmodel.cn"},
    "qwen": {"help.aliyun.com", "www.alibabacloud.com", "modelstudio.console.aliyun.com"},
    "doubao": {"docs.volcengine.com", "www.volcengine.com"},
    "minimax": {"platform.minimax.cn", "www.minimax.cn", "platform.minimax.io"},
}
STATUSES = {"available", "preview", "legacy_available", "alias", "retired", "unknown"}
PUBLIC_STATUSES = STATUSES - {"retired"}
BILLING = {"paid", "free", "unknown"}
MODALITIES = {"text", "image", "video", "audio", "unknown"}
STATUS_ZH = {"available": "官方列为可用", "preview": "预览 / 受限入口",
             "legacy_available": "旧版仍列可用", "alias": "别名 / 重路由",
             "retired": "已下线", "unknown": "可用性未确认"}
STATUS_EN = {"available": "Officially listed", "preview": "Preview / restricted access",
             "legacy_available": "Legacy, still listed", "alias": "Alias / rerouted",
             "retired": "Retired", "unknown": "Availability unconfirmed"}
BILLING_ZH = {"paid": "付费", "free": "免费（以官方条件为准）", "unknown": "未确认"}
BILLING_EN = {"paid": "Paid", "free": "Free (official conditions apply)", "unknown": "Unconfirmed"}
MODALITY_ZH = {"text": "文本", "image": "图片", "video": "视频", "audio": "音频", "unknown": "未确认"}


def _official_url(value, vendor):
    if not isinstance(value, str) or any(char.isspace() for char in value):
        raise ValueError("invalid_official_url")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS[vendor]
            or parsed.username is not None or parsed.password is not None
            or parsed.port not in (None, 443)):
        raise ValueError("non_official_vendor_url")


def _bilingual(value):
    return (isinstance(value, dict) and set(value) == {"zh", "en"}
            and all(isinstance(text, str) for text in value.values()))


def load_catalogs(root=ROOT):
    root = Path(root).resolve()
    catalogs = []
    expected = {f"{vendor}.json" for vendor in VENDORS}
    directory = root / "data/model-lists"
    if {path.name for path in directory.glob("*.json")} != expected:
        raise ValueError("expected_six_vendor_catalogs")
    for vendor in VENDORS:
        path = directory / f"{vendor}.json"
        if not path.resolve().is_relative_to(root):
            raise ValueError("catalog_outside_repository")
        catalog = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(catalog, dict) or set(catalog) != {
            "schema_version", "vendor", "checked_at", "official_catalog_url", "scope_note", "models"
        }:
            raise ValueError("invalid_catalog_fields")
        if type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1 or catalog["vendor"] != vendor:
            raise ValueError("invalid_catalog_identity")
        checked = catalog["checked_at"]
        if not isinstance(checked, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked):
            raise ValueError("invalid_checked_at")
        date.fromisoformat(checked)
        if not _bilingual(catalog["scope_note"]) or not all(catalog["scope_note"].values()):
            raise ValueError("missing_bilingual_scope")
        _official_url(catalog["official_catalog_url"], vendor)
        models = catalog["models"]
        if not isinstance(models, list) or not models:
            raise ValueError("empty_model_catalog")
        seen = set()
        for model in models:
            if not isinstance(model, dict) or set(model) != {
                "model_id", "family", "status", "billing", "input_modalities",
                "model_url", "pricing_url", "notes", "sources"
            }:
                raise ValueError("invalid_model_fields_no_embedded_verification")
            identity = model["model_id"]
            if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}", identity):
                raise ValueError("invalid_model_id")
            if identity in seen:
                raise ValueError("duplicate_model_id")
            seen.add(identity)
            if not isinstance(model["family"], str) or not model["family"].strip():
                raise ValueError("missing_model_family")
            if model["status"] not in STATUSES or model["billing"] not in BILLING:
                raise ValueError("invalid_status_or_billing")
            modes = model["input_modalities"]
            if (not isinstance(modes, list) or not modes or any(not isinstance(item, str) for item in modes)
                    or len(set(modes)) != len(modes) or not set(modes) <= MODALITIES
                    or ("unknown" in modes and len(modes) != 1)):
                raise ValueError("invalid_input_modalities")
            if not _bilingual(model["notes"]):
                raise ValueError("missing_bilingual_notes")
            sources = model["sources"]
            if (not isinstance(sources, list) or not sources or any(not isinstance(item, str) for item in sources)
                    or len(set(sources)) != len(sources)):
                raise ValueError("missing_or_duplicate_sources")
            for url in [model["model_url"], model["pricing_url"], *sources]:
                _official_url(url, vendor)
            if not {model["model_url"], model["pricing_url"]} <= set(sources):
                raise ValueError("model_and_pricing_sources_required")
        catalogs.append(catalog)
    return catalogs


def _empty_coverage():
    return {"manual_path": None, "parameters_path": None, "example_files": [],
            "live_passed_files": [], "generation_registered": False,
            "default_for_vendor": False, "evidence_status": "no_examples"}


def project_coverage(root=ROOT):
    """Join by exact vendor + API ID, never by family, alias or served version."""
    root = Path(root).resolve()
    references = root / "skills/model-manual/references"
    vendors = json.loads((references / "vendors.json").read_text(encoding="utf-8"))["vendors"]
    result = {}
    for path in sorted((references / "models").glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        vendor, identity = card["vendor"], card["model_id"]
        key = (vendor, identity)
        if key in result or vendor not in vendors:
            raise ValueError("invalid_maintained_card_identity")
        value = _empty_coverage()
        for name, field in (("README.md", "manual_path"), ("parameters.md", "parameters_path")):
            relative = Path("models") / vendor / identity / name
            target = root / relative
            if not target.resolve().is_relative_to(root):
                raise ValueError("manual_outside_repository")
            if target.is_file():
                value[field] = relative.as_posix()
        value["generation_registered"] = isinstance(card.get("generation"), dict)
        value["default_for_vendor"] = vendors[vendor]["default_model"] == identity
        result[key] = value
    spec = importlib.util.spec_from_file_location("model_inventory_release", ROOT / "tests/check_example_release.py")
    release_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release_module)
    release = release_module.collect_release(root)
    if not release["catalog_valid"] or release["catalog_issues"] or release["report_issues"]:
        raise ValueError("invalid_repository_example_evidence")
    for row in release["rows"]:
        if row["vendor"] == "shared":
            continue  # Multi-vendor demos are not exact-model manuals or alias tests.
        value = result.setdefault((row["vendor"], row["model_id"]), _empty_coverage())
        value["example_files"].append(row["path"])
        if row["status"] == "passed":
            value["live_passed_files"].append(row["path"])
    for value in result.values():
        value["example_files"].sort()
        value["live_passed_files"].sort()
        if value["example_files"]:
            value["evidence_status"] = ("all_registered_examples_passed" if
                len(value["example_files"]) == len(value["live_passed_files"]) else "incomplete_evidence")
    return result


def select_models(catalogs, vendor=None, model=None, billing=None, status=None, coverage=None):
    coverage = coverage or {}
    rows = []
    for catalog in catalogs:
        if vendor is not None and catalog["vendor"] != vendor:
            continue
        for entry in catalog["models"]:
            if (entry["status"] == "retired"
                    or model is not None and entry["model_id"] != model
                    or billing is not None and entry["billing"] != billing
                    or status is not None and entry["status"] != status):
                continue
            rows.append({**entry, "vendor": catalog["vendor"], "checked_at": catalog["checked_at"],
                         "official_catalog_url": catalog["official_catalog_url"], "scope_note": catalog["scope_note"],
                         "repository_coverage": coverage.get((catalog["vendor"], entry["model_id"]), _empty_coverage())})
    return rows


def _link(page, target, label):
    relative = posixpath.relpath(Path(target).as_posix(), page.parent.as_posix())
    return f"[{label}]({relative})"


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _coverage_text(page, value, english):
    parts = []
    for field, zh, en in (("manual_path", "说明书", "Manual"), ("parameters_path", "参数", "Parameters")):
        if value[field]:
            target = value[field].replace(".md", ".en.md") if english else value[field]
            parts.append(_link(page, target, en if english else zh))
    if not value["manual_path"]:
        parts.append("No maintained manual" if english else "未维护详细说明书")
    if value["example_files"]:
        primary = next((path for path in value["example_files"] if path.endswith("/examples/01_basic.py")),
                       value["example_files"][0])
        parts.append(_link(page, primary, "Code" if english else "代码"))
    count, passed = len(value["example_files"]), len(value["live_passed_files"])
    if count:
        status_path = "en/docs/example-status.md" if english else "docs/示例实测状态.md"
        parts.append(_link(page, status_path, f"{passed}/{count} files passed" if english else f"{passed}/{count} 文件实测通过"))
    else:
        parts.append("No per-file live evidence" if english else "无逐文件实测证据")
    if value["default_for_vendor"]:
        parts.append("Project default" if english else "项目默认")
    return " · ".join(parts)


def expected_pages(root=ROOT):
    catalogs = [{**catalog, "models": [entry for entry in catalog["models"] if entry["status"] != "retired"]}
                for catalog in load_catalogs(root)]
    coverage = project_coverage(root)
    pages = {}
    for english in (False, True):
        lang = "en" if english else "zh"
        directory = Path("en/docs/model-lists" if english else "docs/model-lists")
        other = Path("docs/model-lists" if english else "en/docs/model-lists")
        index = directory / "README.md"
        lines = ["# Language-model lists" if english else "# 语言模型清单", "",
                 _link(index, "models/README.en.md" if english else "models/README.md", "Model directory" if english else "模型目录") + " · " +
                 _link(index, other / "README.md", "中文" if english else "English"), "",
                 ("Discovery only: these are official API IDs, not a claim that this repository has a detailed manual or live-tested code for every model."
                  if english else "这是官方 API 型号的发现清单，不表示仓库已为每个型号维护详细说明书或完成真实调用。"), "",
                 ("Scope: chat, reasoning and coding language models, including multimodal understanding where officially documented. Excludes image/video generation, standalone speech, embeddings, rerankers and third-party hosted models. See each vendor's scope and account/region/access restrictions; this is not an account-specific /models response or an exhaustive historical archive."
                  if english else "范围：对话、推理、编程语言模型，包含有官方依据的多模态理解；不含图片/视频生成、独立语音、Embedding、Rerank 和第三方托管型号。各厂商的完整性、账户、地域和接入限制见各页；不是你账户的 /models 返回，也不是所有历史版本的档案。"), "",
                 ("Prices are linked to official pages, not frozen here. Free entries are discovery records only: maintained examples and generated defaults remain paid, with no silent fallback. Retired models are excluded from these lists and Agent queries. Unconfirmed availability appears separately and is not a recommendation to call."
                  if english else "价格只链接官方页面，不在这里固化数字。免费条目仅用于发现：维护示例和生成器默认仍全部采用付费型号，不静默回退。已下线型号不出现在清单和 Agent 查询中；可用性未确认的条目单列，不作为调用建议。"), "",
                 ("Official lifecycle and input labels are dated documentation snapshots, not live API tests. A paid label is not proof of pay-as-you-go access; previews may require subscriptions. An alias does not inherit another ID's manual, parameters or passed tests."
                  if english else "官方生命周期和输入标签是核对日的文档快照，不是在线调用测试。“付费”不等于可以按量接入，预览可能仅限订阅。别名不继承另一个 ID 的说明书、参数或实测。"), "",
                 "| Vendor | Checked | Listed IDs (retired excluded; includes uncertain) | Detailed manuals | Official catalog |" if english else "| 厂商 | 核对日期 | 收录 ID（不含已下线；含待确认） | 详细说明书 | 官方目录 |",
                 "|---|---|---|---|---|"]
        for catalog in catalogs:
            vendor = catalog["vendor"]
            maintained = sum(bool(coverage.get((vendor, entry["model_id"]), {}).get("manual_path")) for entry in catalog["models"])
            label = (NAMES_EN if english else NAMES)[vendor]
            lines.append(f"| {_link(index, directory / (vendor + '.md'), label)} | {catalog['checked_at']} | {len(catalog['models'])} | {maintained} | [Official]({catalog['official_catalog_url']}) |")
        lines += ["", "## Agent lookup" if english else "## Agent 查询", "",
                  "```bash", "python skills/model-manual/scripts/model_catalog.py --vendor deepseek",
                  "python skills/model-manual/scripts/model_catalog.py --vendor deepseek --model deepseek-v4-pro",
                  "python skills/model-manual/scripts/model_catalog.py --billing paid --status available", "```", "",
                  ("Read-only, offline JSON; unknown exact IDs return an error, never another model. Results include official URLs, lifecycle, billing, input modalities, and separately derived exact-ID repository coverage. No credentials are read."
                   if english else "只读、离线输出 JSON；准确 ID 未命中时返回错误，不替换成其他型号。结果含官方来源、生命周期、付费类型、输入模态，以及按准确 ID 独立派生的仓库覆盖。不读取密钥。"), "",
                  ("If no maintained card exists, verify that exact model's official API and parameters before implementation; the snippet generator does not automatically support it. Listed input modalities do not establish a common API format or guarantee semantic quality."
                   if english else "没有维护卡片的型号，需要先查该准确型号的官方 API 和参数再实现；代码生成器不会自动支持它。输入模态不代表各厂商格式相同，也不保证语义效果。"), "",
                  _link(index, "data/model-lists", "Shared source data" if english else "共享来源数据") + " · " +
                  _link(index, "skills/model-manual/scripts/model_catalog.py", "Query / page generator" if english else "查询 / 页面生成器") + " · " +
                  _link(index, "models/README.en.md" if english else "models/README.md", "Model directory" if english else "模型目录"), ""]
        pages[index] = "\n".join(lines)
        for catalog in catalogs:
            vendor = catalog["vendor"]
            page = directory / (vendor + ".md")
            title = (NAMES_EN if english else NAMES)[vendor]
            lines = [f"# {title} · " + ("language-model list" if english else "语言模型清单"), "",
                     _link(page, "models/README.en.md" if english else "models/README.md", "Model directory" if english else "模型目录") + " · " +
                     _link(page, other / page.name, "中文" if english else "English"), "",
                     (f"Official documentation checked: {catalog['checked_at']}. " if english else f"官方文档核对日期：{catalog['checked_at']}。") +
                     f"[{'Official catalog' if english else '官方目录'}]({catalog['official_catalog_url']}) · " +
                     _link(page, f"data/model-lists/{vendor}.json", "Source data" if english else "来源数据"), "",
                     catalog["scope_note"][lang], "",
                     ("Availability is a dated official-document snapshot, not an account-level or live-call guarantee. Billing links do not imply API access; read each row's restrictions. Coverage is joined by exact ID from maintained cards and current-source HTTP reports, not inherited through aliases or family names."
                      if english else "可用性是有日期的官方文档快照，不保证你账户具备权限，也不表示本次实际调用。定价入口不等于接入权限，限制见逐行说明。仓库覆盖按准确 ID 关联维护卡片和当前源码 HTTP 报告，不按别名或系列继承。"), "",
                     ("Text output is the scope; modality labels describe input understanding, not image/audio generation. No entry here expands the snippet generator's supported models."
                      if english else "本清单以语言输出为范围；模态表示输入理解，不是图像/音频生成能力。出现在这里不自动扩展代码生成器支持的型号。"), ""]
            groups = [(False, "Documented / restricted / legacy entries" if english else "官方列出 / 受限 / 旧版入口"),
                      (True, "Availability unconfirmed — do not assume callable" if english else "可用性待确认——不可据此认为能调用")]
            for uncertain, heading in groups:
                entries = [entry for entry in catalog["models"] if (entry["status"] == "unknown") == uncertain]
                if not entries:
                    continue
                lines += [f"## {heading}", "",
                          "| Exact API ID / family | Lifecycle | Billing | Input | Repository coverage | Restrictions / official sources |" if english else "| 准确 API ID / 系列 | 生命周期 | 付费类型 | 输入 | 仓库覆盖 | 限制 / 官方出处 |",
                          "|---|---|---|---|---|---|"]
                for entry in entries:
                    value = coverage.get((vendor, entry["model_id"]), _empty_coverage())
                    source_links = [f"[{'Model' if english else '型号'}]({entry['model_url']})",
                                    f"[{'Pricing' if english else '价格'}]({entry['pricing_url']})"]
                    source_links.extend(f"[{'Source' if english else '出处'} {i}]({url})" for i, url in enumerate(entry["sources"], 1)
                                        if url not in {entry["model_url"], entry["pricing_url"]})
                    note = entry["notes"][lang]
                    if value["manual_path"]:
                        target = value["manual_path"].replace(".md", ".en.md") if english else value["manual_path"]
                        model_link = _link(page, target, f"`{entry['model_id']}`")
                    else:
                        model_link = f"[`{entry['model_id']}`]({entry['model_url']})"
                    fields = [f"{model_link} / {entry['family']}",
                              (STATUS_EN if english else STATUS_ZH)[entry["status"]],
                              (BILLING_EN if english else BILLING_ZH)[entry["billing"]],
                              ", ".join(entry["input_modalities"] if english else [MODALITY_ZH[mode] for mode in entry["input_modalities"]]),
                              _coverage_text(page, value, english),
                              (note + " " if note else "") + " · ".join(source_links)]
                    lines.append("| " + " | ".join(_cell(field) for field in fields) + " |")
                lines.append("")
            lines += [(_link(page, "en/docs/example-status.md" if english else "docs/示例实测状态.md",
                             "Per-file live evidence and limits" if english else "逐文件实测及证据边界")), ""]
            pages[page] = "\n".join(lines)
    return pages


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--vendor", choices=VENDORS)
    parser.add_argument("--model", help="Exact API ID; no family/alias fallback")
    parser.add_argument("--billing", choices=sorted(BILLING))
    parser.add_argument("--status", choices=sorted(PUBLIC_STATUSES))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write-pages", action="store_true")
    args = parser.parse_args(argv)
    if (args.check or args.write_pages) and any((args.vendor, args.model, args.billing, args.status)):
        parser.error("page operations cannot be combined with query filters")
    try:
        root = args.root.resolve()
        if args.check or args.write_pages:
            pages = expected_pages(root)
            if args.write_pages:
                for path, content in pages.items():
                    target = root / path
                    if not target.resolve().is_relative_to(root):
                        raise ValueError("generated_page_outside_repository")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
                print(json.dumps({"written_pages": len(pages)}))
            else:
                stale = [str(path) for path, content in pages.items()
                         if not (root / path).is_file() or (root / path).read_text(encoding="utf-8") != content]
                print(json.dumps({"checked_pages": len(pages), "stale_pages": stale}))
                return 2 if stale else 0
        else:
            rows = select_models(load_catalogs(root), args.vendor, args.model, args.billing,
                                 args.status, project_coverage(root))
            if not rows:
                print(json.dumps({"error": "no_exact_model_match", "models": []}))
                return 2
            print(json.dumps({"schema_version": 1, "kind": "official_language_model_discovery",
                              "live_api_calls": False, "models": rows}, ensure_ascii=False, indent=2))
    except (ValueError, TypeError, KeyError, AttributeError, OSError):
        print(json.dumps({"error": "invalid_catalog_or_repository_evidence"}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
