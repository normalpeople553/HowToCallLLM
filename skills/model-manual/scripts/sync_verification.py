#!/usr/bin/env python3
"""从型号卡片和原始报告生成厂商能力摘要、验证状态页；不发送请求。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REFERENCES = ROOT / "skills/model-manual/references"
CATALOG = REFERENCES / "vendors.json"
STATUS_PAGE = ROOT / "docs/验证状态.md"
TEST_IDS = {
    "chat_completions": "chat_completions",
    "streaming": "streaming",
    "thinking": "thinking_enabled",
    "thinking_off": "thinking_disabled",
    "json_object": "json_object",
    "structured_output": "structured_output",
    "tool_calling": "tool_calling",
    "vision": "vision",
}


def report_tests(report: dict) -> dict:
    if isinstance(report.get("tests"), dict):
        return report["tests"]
    results = report.get("results", [])
    if isinstance(results, dict):
        return results
    return {item.get("id", item.get("name")): item for item in results}


def counts(report: dict) -> dict:
    return {
        state: sum(item.get("status") == state for item in report_tests(report).values())
        for state in ("passed", "failed", "rate_limited", "skipped")
    }


def expected_outputs() -> dict[Path, str]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    lines = [
        "# 历史统一流程验证状态",
        "",
        "> 本页由 `python skills/model-manual/scripts/sync_verification.py` 从型号卡片与脱敏报告生成；请更新报告后重新生成。本命令不发送 API 请求。",
        "",
        "厂商能力摘要只指项目默认型号；具体日期、环境、参数、测试范围和结果以每行的报告为准。官方文档声明与一次运行结果分别记录。[来源规则](来源与核验规则.md)",
        "",
        "本页只汇总旧统一验证器的能力检查，不代表当前每个示例文件的执行状态。逐文件源码哈希、真实 HTTP 元数据与运行日期见[示例实测状态](示例实测状态.md)；两层报告不能互相替代。",
        "",
        "| 型号 | 报告日期 | 验证范围 | 通过 | 失败 | 限流 | 跳过 | SDK | 原始报告 |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for vendor, cfg in catalog["vendors"].items():
        card_path = REFERENCES / "models" / f'{cfg["default_model"]}.json'
        card = json.loads(card_path.read_text(encoding="utf-8"))
        if card["vendor"] != vendor or card["model_id"] != cfg["default_model"]:
            raise ValueError(f"型号归属不一致：{cfg['default_model']}")
        cfg["model_card"] = f'models/{card_path.name}'
        reference = card.get("verification")
        report = None
        report_path = None
        if reference is None:
            # 已有官方资料但尚未实测是正式状态，不能猜测报告名或继承厂商旧结果。
            if card.get("verification_scope", "not_run") != "not_run":
                raise ValueError(f"缺少报告时验证范围必须是 not_run：{card['model_id']}")
            cfg["verification"] = None
            cfg["verification_scope"] = "not_run"
        else:
            if not isinstance(reference, str) or not reference.strip():
                raise ValueError(f"报告引用须为非空路径或 null：{card['model_id']}")
            report_path = (card_path.parent / reference).resolve()
            if not report_path.is_file():
                raise ValueError(f"已登记的报告文件不存在：{card['model_id']}")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if report["model_id"] != card["model_id"]:
                raise ValueError(f"型号与报告不一致：{card['model_id']}")
            cfg["verification"] = report_path.relative_to(ROOT).as_posix()
            cfg["verification_scope"] = "strict_workflow" if report.get("schema_version", 1) >= 2 else "legacy_smoke"
        observations = report_tests(report) if report is not None else {}
        capability_states = {}
        for name, capability in card["capabilities"].items():
            if name in TEST_IDS:
                status = observations.get(TEST_IDS[name], {}).get("status")
                if status == "passed":
                    capability_states[name] = "verified"
                elif capability["status"] in {"not_documented_for_this_model", "unknown", "unsupported"}:
                    capability_states[name] = "unknown"
                else:
                    capability_states[name] = "documented"
            else:
                capability_states[name] = "unknown" if capability["status"] in {"not_documented_for_this_model", "unknown", "unsupported"} else "documented"
        if "thinking" in card["capabilities"]:
            off_body = card.get("generation", {}).get("thinking", {}).get("off", {}).get("value")
            capability_states["thinking_off"] = (
                "verified" if observations.get("thinking_disabled", {}).get("status") == "passed"
                else "documented" if off_body is not None else "unknown"
            )
        cfg["capabilities"] = capability_states
        manual_link = f'../models/{vendor}/{card["model_id"]}/README.md'
        if report is None:
            lines.append(f'| [{card["model_id"]}]({manual_link}) | — | 统一验证器未运行 | — | — | — | — | — | 报告空缺 |')
            continue
        result_counts = counts(report)
        report_link = "../" + report_path.relative_to(ROOT).as_posix()
        scope = "严格流程验证" if cfg["verification_scope"] == "strict_workflow" else "历史基础验证"
        sdk = report.get("runtime", {}).get("openai", "未记录")
        lines.append(
            f'| [{card["model_id"]}]({manual_link}) | {report.get("tested_at", "未记录").split("T", 1)[0]} | {scope} | '
            f'{result_counts["passed"]} | {result_counts["failed"]} | {result_counts["rate_limited"]} | '
            f'{result_counts["skipped"]} | {sdk} | [JSON]({report_link}) |'
        )
    lines.extend([
        "",
        "## 如何解读",
        "",
        "- 统一验证器未运行：型号卡片没有登记此类报告；计数、日期与 SDK 显示为 —。这不代表没有逐文件实测，也不等于能力不支持；文件级记录请看示例实测状态页。",
        "- 历史基础验证：只证明脚本当时检查过的条件；旧报告没有记录完整结束原因、工具回传闭环或图片内容识别，不自动补写这些结论。",
        "- 严格流程验证：脚本检查结束原因和正文；工具项包含参数验证、结果回传和最终答复；图片项包含测试图内容断言。具体选中了哪些测试仍以报告为准。",
        "- 限流与跳过：没有获得能力验证结论；HTTP 429 不等于鉴权失败或模型不支持。",
        "- SDK 版本：历史报告保留原环境；本项目当前可复现安装使用 [requirements-lock.txt](../requirements-lock.txt)。",
        "",
        "安装、复测、报告保存与退出码见[验证与复现](验证与复现.md)。",
        "",
    ])
    return {
        CATALOG: json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        STATUS_PAGE: "\n".join(lines),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只检查生成内容是否同步")
    args = parser.parse_args()
    changed = []
    for path, expected in expected_outputs().items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == expected:
            continue
        changed.append(path)
        if not args.check:
            path.write_text(expected, encoding="utf-8")
    if args.check and changed:
        print("需要重新生成：" + ", ".join(str(p.relative_to(ROOT)) for p in changed))
        return 1
    print("验证摘要已同步。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
