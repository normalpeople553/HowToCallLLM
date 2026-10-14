#!/usr/bin/env python3
"""从公开型号卡片与官方来源生成能力摘要和记录公开策略；不读取本地实测。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[3]
REFERENCES = ROOT / "skills/model-manual/references"
CATALOG = REFERENCES / "vendors.json"
STATUS_PAGE = ROOT / "docs/验证状态.md"
PUBLIC_SCOPES = {"private", "not_run"}
DOCUMENTED_STATUSES = {"documented", "verified", "beta_documented", "automatic", "non_thinking_only"}
OFFICIAL_HOSTS = {
    "deepseek": {"api-docs.deepseek.com"},
    "kimi": {"platform.kimi.com", "platform.moonshot.cn"},
    "zhipu": {"docs.bigmodel.cn", "open.bigmodel.cn", "bigmodel.cn"},
    "qwen": {"help.aliyun.com", "www.alibabacloud.com"},
    "doubao": {"docs.volcengine.com", "www.volcengine.com"},
    "minimax": {"platform.minimax.cn", "platform.minimaxi.com", "platform.minimax.io", "www.minimax.cn", "www.minimaxi.com", "www.minimax.io"},
}


def _read_json(path, snapshot):
    if snapshot is None:
        return json.loads(path.read_text(encoding="utf-8"))
    identity = path.resolve()
    if identity not in snapshot:
        snapshot[identity] = path.read_text(encoding="utf-8")
    # Separate mutable objects, identical public source bytes for both languages.
    return json.loads(snapshot[identity])


def _official_url(card, reference):
    if not isinstance(reference, dict):
        return None
    key, sources = reference.get("source"), card.get("sources", {})
    if not isinstance(key, str) or not isinstance(sources, dict):
        return None
    source = sources.get(key)
    value = source.get("url") if isinstance(source, dict) else None
    if not isinstance(value, str) or any(char.isspace() for char in value):
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme == "https" and parsed.hostname in OFFICIAL_HOSTS.get(card["vendor"], set())
                and parsed.username is None and parsed.password is None and parsed.port in (None, 443)):
            return value
    except ValueError:
        pass
    return None


def documented_capabilities(card):
    """官方依据只能派生 documented；私有或旧 passed 永不派生 verified。"""
    result = {}
    for name, capability in card["capabilities"].items():
        declared = capability.get("status") if isinstance(capability, dict) else None
        result[name] = (
            "documented" if declared in DOCUMENTED_STATUSES and _official_url(card, capability)
            else "unknown"
        )
    if "thinking" in result and "thinking_off" not in result:
        off = card.get("generation", {}).get("thinking", {}).get("off", {})
        result["thinking_off"] = (
            "documented" if isinstance(off, dict) and off.get("value") is not None and _official_url(card, off)
            else "unknown"
        )
    return result


def _source_links(card, english):
    urls = sorted({
        url for capability in card["capabilities"].values()
        if (url := _official_url(card, capability)) is not None
    })
    if not urls:
        return "Official support unconfirmed" if english else "官方支持未确认"
    label = "Official" if english else "官方"
    return " · ".join(f"[{label} {index}]({url})" for index, url in enumerate(urls, 1))


def expected_outputs(language="zh", *, _snapshot=None) -> dict[Path, str]:
    if language not in {"zh", "en"}:
        raise ValueError("Unknown page language")
    english = language == "en"
    catalog = _read_json(CATALOG, _snapshot)
    catalog.pop("verified_at", None)
    lines = [
        "# Workflow record publication policy", "",
        "[中文](../../docs/验证状态.md) | English", "",
        "> Generated from public model cards and official references by `python skills/model-manual/scripts/sync_verification.py`. This command does not read local execution records, credentials or vendor APIs.", "",
        "Execution records are local-only and are not published. This public page does not show results, statistics, runtime environments, fingerprints, record identifiers or report links. [Evidence policy](evidence-policy.md)", "",
        "The vendor capability summary is derived solely from the exact model's official references as documented or unknown. Private execution results do not promote a public capability to verified.", "",
        "| Model manual | Unified workflow record | Official references |",
        "|---|---|---|",
    ] if english else [
        "# 统一流程记录公开策略", "",
        "中文 | [English](../en/docs/verification-status.md)", "",
        "> 本页由 `python skills/model-manual/scripts/sync_verification.py` 从公开型号卡片和官方来源生成。本命令不读取本地实测记录、密钥或厂商接口。", "",
        "实测记录仅保留在本地，不对外发布。本页不公开结果、统计、运行环境、源码指纹、记录标识或报告链接。[来源规则](来源与核验规则.md)", "",
        "厂商能力摘要只按准确型号的官方依据派生为 documented 或 unknown；不会因私有实测结果把公开能力升级为 verified。", "",
        "| 型号说明书 | 统一流程记录 | 官方依据 |",
        "|---|---|---|",
    ]
    for vendor, cfg in catalog["vendors"].items():
        card_path = REFERENCES / "models" / f'{cfg["default_model"]}.json'
        card = _read_json(card_path, _snapshot)
        if card["vendor"] != vendor or card["model_id"] != cfg["default_model"]:
            raise ValueError(f"型号归属不一致：{cfg['default_model']}")
        # Even a malformed public binding must never cause a private report read.
        if card.get("verification") is not None:
            raise ValueError("Public model cards must not bind execution reports")
        scope = card.get("verification_scope", "not_run")
        if scope not in PUBLIC_SCOPES:
            raise ValueError("Public verification scope must be private or not_run")
        cfg["model_card"] = f"models/{card_path.name}"
        cfg["verification"] = None
        cfg["verification_scope"] = scope
        cfg["capabilities"] = documented_capabilities(card)
        manual_link = f'../../models/{vendor}/{card["model_id"]}/README.en.md' if english else f'../models/{vendor}/{card["model_id"]}/README.md'
        state = ("Local records are not published" if scope == "private" else "Unified workflow not run") if english else ("本地记录不公开" if scope == "private" else "统一流程未运行")
        lines.append(f'| [{card["model_id"]}]({manual_link}) | {state} | {_source_links(card, english)} |')
    lines += [
        "", "## Interpretation", "",
        "- private: execution records are not public. This does not assert success, failure or capability quality, and the public clone does not need those local files.",
        "- not_run: no unified workflow run is registered for this model. This does not establish unsupported capabilities or describe every example's execution history.",
        "- documented / unknown: these are official-document classifications only, not published execution results.", "",
        "[Unified workflow source](../../tests/provider_verify.py) · [Per-file runner source](../../tests/run_example_files.py) · [Maintained manuals](../../models/README.en.md)", "",
        "To perform your own local checks, see [verification](verification.md). The public generation/check commands remain reproducible without private records.", "",
    ] if english else [
        "", "## 如何解读", "",
        "- private：记录不公开，不声称通过、失败或能力质量；公开克隆不需要这些本地文件。",
        "- not_run：此型号未登记统一流程运行，不等于能力不支持，也不代表每个示例的全部运行历史。",
        "- documented / unknown：仅表示官方资料依据，不是公开的实测结论。", "",
        "[统一流程验证器源码](../tests/provider_verify.py) · [逐文件执行器源码](../tests/run_example_files.py) · [维护中的说明书](../models/README.md)", "",
        "自行进行本地检查见[验证与复现](验证与复现.md)。公开生成与检查命令不依赖私有记录。", "",
    ]
    return {
        CATALOG: json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        (ROOT / "en/docs/verification-status.md" if english else STATUS_PAGE): "\n".join(lines),
    }


def all_expected_outputs() -> dict[Path, str]:
    snapshot = {}
    chinese, english = expected_outputs(_snapshot=snapshot), expected_outputs(language="en", _snapshot=snapshot)
    if chinese[CATALOG] != english[CATALOG]:
        raise ValueError("Canonical public sources changed during bilingual generation")
    return {**chinese, **english}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只检查公开生成内容是否同步")
    args = parser.parse_args(argv)
    changed = []
    for path, expected in all_expected_outputs().items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == expected:
            continue
        changed.append(path)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    if args.check and changed:
        print("需要重新生成：" + ", ".join(str(p.relative_to(ROOT)) for p in changed))
        return 1
    print("公开摘要已同步。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
