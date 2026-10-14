#!/usr/bin/env python3
"""Check reviewed translation pairs without network access or API credentials.

The source hash detects an unreviewed source revision, not semantic correctness.
Generated pages are checked by their own bilingual generators, never executed here.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("en/translations.json")


def document(root, value, suffix=".md"):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid_repository_path")
    relative = Path(value)
    target = (root / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(root):
        raise ValueError("path_outside_repository")
    if target.suffix != suffix or not target.is_file():
        raise ValueError("missing_document_or_generator")
    return target


def external_sources(text):
    """Only cited Markdown URLs, not example endpoints inside code fences."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    links = re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", text)
    links += re.findall(r"^\[[^\]\n]+\]:\s*(\S+)", text, flags=re.M)
    return {url.strip("<>") for url in links if urlsplit(url.strip("<>")).scheme in {"http", "https"}}


def example_targets(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    links = re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", text)
    return {Path(urlsplit(link).path).name for link in links if not urlsplit(link).scheme and Path(urlsplit(link).path).suffix in {".py", ".ts", ".sh"}}


def check(root=ROOT):
    root = Path(root).resolve()
    manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("languages") != ["zh-CN", "en"]:
        raise ValueError("invalid_translation_manifest")
    static, generated = manifest.get("translations"), manifest.get("generated")
    if not isinstance(static, list) or not isinstance(generated, list) or not static:
        raise ValueError("missing_translation_inventory")
    issues, seen_sources, seen_targets = [], set(), set()
    for kind, entries in (("static", static), ("generated", generated)):
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("invalid_translation_entry")
            source, target = entry.get("source"), entry.get("target")
            source_path, target_path = document(root, source), document(root, target)
            if source in seen_sources or target in seen_targets or source == target:
                raise ValueError("duplicate_translation_pair")
            seen_sources.add(source)
            seen_targets.add(target)
            source_text, target_text = source_path.read_text(encoding="utf-8"), target_path.read_text(encoding="utf-8")
            if not source_text.strip() or not target_text.strip():
                issues.append({"source": source, "code": "empty_translation"})
            if kind == "generated":
                document(root, entry.get("generator"), suffix=".py")
                continue
            digest = entry.get("source_sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("invalid_source_fingerprint")
            if digest != hashlib.sha256(source_path.read_bytes()).hexdigest():
                issues.append({"source": source, "code": "source_changed_review_translation"})
            if external_sources(source_text) != external_sources(target_text):
                issues.append({"source": source, "code": "official_or_external_citation_mismatch"})
            # Preserve actual file mappings in detailed parameter explanations.
            if source_path.name == "parameters.md" and example_targets(source_text) != example_targets(target_text):
                issues.append({"source": source, "code": "executable_reference_mismatch"})
    return {"static_pairs": len(static), "generated_pairs": len(generated), "issues": issues}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="read-only consistency check (also the default)")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository to inspect; useful for offline fixtures")
    parser.add_argument("--fingerprint", help="print a Markdown source hash after manually reviewing its translation")
    args = parser.parse_args(argv)
    try:
        if args.fingerprint:
            source = document(args.root.resolve(), args.fingerprint)
            print(hashlib.sha256(source.read_bytes()).hexdigest())
            return 0
        result = check(args.root)
        print(f"Translations: {result['static_pairs']} reviewed pairs, {result['generated_pairs']} generated pairs")
        for issue in result["issues"]:
            print(f"{issue['source']}: {issue['code']}")
        return 1 if result["issues"] else 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        # No arbitrary file contents or exception strings are printed.
        print("Invalid translation inventory or repository path.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
