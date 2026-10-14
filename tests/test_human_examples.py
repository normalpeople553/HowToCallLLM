"""Human-readable examples must mirror current, strictly evidenced source files.

Offline tests only: parse code, never execute it, read keys or contact providers.
All intentionally broken evidence/source fixtures live in temporary directories.
"""

import ast
import builtins
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/render_human_examples.py"
DEFAULTS = {
    "deepseek": "deepseek-flash",
    "kimi": "kimi-k2.6",
    "zhipu": "glm-4.7",
    "qwen": "qwen-flash",
    "doubao": "doubao-seed-2-1-pro-260628",
    "minimax": "MiniMax-M2.7",
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def offline_only():
    original_path_open, original_open = Path.open, builtins.open

    def check_path(value):
        if isinstance(value, (str, os.PathLike)) and Path(value).name.startswith(".env"):
            raise AssertionError("credential_file_must_not_be_read")

    def path_open(path, *args, **kwargs):
        check_path(path)
        return original_path_open(path, *args, **kwargs)

    def builtin_open(path, *args, **kwargs):
        check_path(path)
        return original_open(path, *args, **kwargs)

    def deny_execution(*_args, **_kwargs):
        raise AssertionError("network_or_example_execution_must_not_occur")

    with patch.object(os, "environ", {}), patch.object(Path, "open", path_open), \
            patch("builtins.open", builtin_open), \
            patch.object(socket, "create_connection", deny_execution), \
            patch.object(socket.socket, "connect", deny_execution), \
            patch.object(socket, "getaddrinfo", deny_execution), \
            patch("subprocess.Popen", deny_execution), \
            patch("runpy.run_path", deny_execution), patch("runpy.run_module", deny_execution):
        yield


def public_snapshot(root):
    """Hash public implementation/evidence targets only; never enumerate .env files."""
    paths = list((root / "models").glob("*/*/examples/*"))
    paths = [path for path in paths if path.is_file() and path.suffix in {".py", ".ts", ".sh", ".json"}]
    paths += list((root / "examples").glob("*.py"))
    paths += list((root / "verification/examples").glob("*.json"))
    paths += list((root / "skills/model-manual/references/models").glob("*.json"))
    paths += [root / "skills/model-manual/references/vendors.json"]
    paths += list((root / "human/examples").glob("*.md"))
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def python_blocks(text):
    return re.findall(r"^\x60\x60\x60python\n(.*?)^\x60\x60\x60[ \t]*$", text, re.M | re.S)


def local_targets(page, content):
    targets = set()
    for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
        if urlsplit(href).scheme or href.startswith("#"):
            continue
        target = unquote(href.split("#", 1)[0].strip("<>"))
        targets.add((ROOT / page.parent / target).resolve())
    return targets


class HumanExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with offline_only():
            cls.renderer = load_module("human_example_renderer_under_test", SCRIPT)
            cls.release = load_module("human_example_release_reference", ROOT / "tests/check_example_release.py")

    def views_and_pages(self):
        with offline_only():
            return self.renderer.build_views(ROOT), self.renderer.expected_pages(ROOT)

    def run_cli(self, *arguments, root=ROOT):
        output, errors = io.StringIO(), io.StringIO()
        with offline_only(), redirect_stdout(output), redirect_stderr(errors):
            try:
                code = self.renderer.main(["--root", str(root), *arguments])
            except SystemExit as error:
                code = error.code
        return code, output.getvalue(), errors.getvalue()

    def temporary_repository(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        # Copy only public code, source manifests and sanitized reports, never .env.
        for relative in (
            "models", "examples", "verification/examples",
            "skills/model-manual/references", "skills/model-manual/scripts",
        ):
            shutil.copytree(
                ROOT / relative, root / relative,
                ignore=shutil.ignore_patterns(".env*", "__pycache__"),
            )
        for relative in (
            "tests/check_example_release.py", "tests/run_example_files.py",
            "tests/live_fetch.mjs", "tests/live_curl.py", "requirements-lock.txt",
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return root

    def test_views_use_only_the_six_exact_paid_maintained_basic_files(self):
        views, _ = self.views_and_pages()
        self.assertEqual({view["vendor"]: view["model_id"] for view in views}, DEFAULTS)
        self.assertEqual(len(views), len(DEFAULTS))
        references = ROOT / "skills/model-manual/references"
        vendors = json.loads((references / "vendors.json").read_text(encoding="utf-8"))["vendors"]
        for view in views:
            with self.subTest(vendor=view["vendor"]):
                model = view["model_id"]
                self.assertEqual(vendors[view["vendor"]]["default_model"], model)
                expected = Path("models") / view["vendor"] / model / "examples/01_basic.py"
                self.assertEqual(Path(view["path"]), expected)
                card = json.loads((references / "models" / (model + ".json")).read_text(encoding="utf-8"))
                self.assertEqual(card["billing"]["type"]["value"], "paid")
                self.assertEqual(set(view["notes"]), {"zh", "en"})
                lines = view["source_text"].splitlines()
                for notes in view["notes"].values():
                    self.assertIsInstance(notes, list)
                    self.assertTrue(notes)
                    for note in notes:
                        self.assertEqual(set(note), {"line", "anchor", "description"})
                        self.assertIs(type(note["line"]), int)
                        self.assertGreaterEqual(note["line"], 1)
                        self.assertLessEqual(note["line"], len(lines))
                        self.assertIn(note["anchor"], lines[note["line"] - 1])
                        self.assertTrue(note["description"].strip())
                self.assertEqual(
                    [(note["line"], note["anchor"]) for note in view["notes"]["zh"]],
                    [(note["line"], note["anchor"]) for note in view["notes"]["en"]],
                )

    def test_view_metadata_matches_current_strict_release_and_real_file_reports(self):
        with offline_only():
            views = self.renderer.build_views(ROOT)
            release = self.release.collect_release(ROOT)
        released = {row["path"]: row for row in release["rows"]}
        for view in views:
            with self.subTest(vendor=view["vendor"]):
                path = Path(view["path"]).as_posix()
                row = released[path]
                self.assertEqual(row["status"], "passed")
                self.assertEqual((row["vendor"], row["model_id"]), (view["vendor"], view["model_id"]))
                self.assertTrue(row["selected"]["strict_passed"])
                self.assertTrue(row["selected"]["current_source"])
                self.assertEqual(view["report"], row["selected"]["report"])
                self.assertEqual(view["evidence_id"], row["selected"].get("evidence_id"))
                self.assertFalse({"tested_at", "duration_seconds", "legacy_tested_at"}.intersection(view))
                source = (ROOT / path).read_bytes()
                self.assertEqual(view["source_text"].encode("utf-8"), source)
                expected_hash = hashlib.sha256(source).hexdigest()
                self.assertEqual(view["source_sha256"], expected_hash)
                report = json.loads((ROOT / view["report"]).read_text(encoding="utf-8"))
                self.assertEqual(report["kind"], "example_file_execution")
                records = [record for record in report["results"] if record["path"] == path]
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0]["source_sha256"][path], expected_hash)
                self.assertEqual(view["support_sha256"], records[0]["source_sha256"])
                self.assertEqual(records[0]["status"], "passed")

    def test_views_preserve_opaque_ids_and_never_echo_legacy_execution_times(self):
        with offline_only():
            catalog, release_tool = self.renderer.dependencies(ROOT)
            baseline = release_tool.collect_release(ROOT)
        for version in (1, 2):
            with self.subTest(schema_version=version):
                synthetic = copy.deepcopy(baseline)
                identities = {}
                for row in synthetic["rows"]:
                    selected = row.get("selected")
                    if not selected:
                        continue
                    selected.pop("evidence_id", None)
                    if version == 2:
                        identities[row["path"]] = str(uuid4())
                        selected["evidence_id"] = identities[row["path"]]
                    # A legacy internal field must not escape into the public view.
                    selected["legacy_tested_at"] = "1999-12-31T23:59:59+00:00"
                    selected["tested_at"] = "1999-12-31T23:59:59+00:00"
                with offline_only(), patch.object(self.renderer, "dependencies", return_value=(catalog, release_tool)), \
                        patch.object(release_tool, "collect_release", return_value=synthetic):
                    views = self.renderer.build_views(ROOT)
                    pages = self.renderer.expected_pages(ROOT)
                for view in views:
                    self.assertEqual(view["evidence_id"], identities.get(view["path"]))
                    self.assertFalse({"tested_at", "duration_seconds", "legacy_tested_at"}.intersection(view))
                self.assertNotIn("1999-12-31T23:59:59", json.dumps(views))
                self.assertTrue(all("1999-12-31T23:59:59" not in page for page in pages.values()))

    def test_complete_python_fences_are_verbatim_and_identical_between_editions(self):
        views, pages = self.views_and_pages()
        for view in views:
            with self.subTest(vendor=view["vendor"]):
                chinese = pages[Path("human/examples") / (view["vendor"] + ".md")]
                english = pages[Path("human/examples") / (view["vendor"] + ".en.md")]
                expected = (ROOT / view["path"]).read_bytes()
                self.assertEqual([block.encode("utf-8") for block in python_blocks(chinese)], [expected])
                self.assertEqual([block.encode("utf-8") for block in python_blocks(english)], [expected])

    def test_embedded_code_is_parsed_not_executed_and_keeps_the_exact_api_model(self):
        views, pages = self.views_and_pages()
        with offline_only():
            for view in views:
                for suffix in (".md", ".en.md"):
                    path = Path("human/examples") / (view["vendor"] + suffix)
                    blocks = python_blocks(pages[path])
                    self.assertEqual(len(blocks), 1)
                    syntax = ast.parse(blocks[0], filename=Path(view["path"]).as_posix())
                    models = [
                        keyword.value.value
                        for node in ast.walk(syntax) if isinstance(node, ast.Call)
                        for keyword in node.keywords
                        if keyword.arg == "model" and isinstance(keyword.value, ast.Constant)
                    ]
                    self.assertEqual(models, [view["model_id"]])

    def test_pages_link_official_sources_parameters_original_code_report_and_hash(self):
        views, pages = self.views_and_pages()
        for view in views:
            source_manifest = ROOT / Path(view["path"]).parent / "sources.json"
            manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
            entry = next(item for item in manifest["examples"] if item["file"] == "01_basic.py")
            required_sources = {source["url"] for source in entry["sources"]}
            self.assertTrue(required_sources <= set(view["sources"]))
            source_hash = hashlib.sha256((ROOT / view["path"]).read_bytes()).hexdigest()
            for suffix in (".md", ".en.md"):
                page = Path("human/examples") / (view["vendor"] + suffix)
                text = pages[page]
                targets = local_targets(page, text)
                self.assertIn((ROOT / view["path"]).resolve(), targets)
                self.assertIn((ROOT / view["report"]).resolve(), targets)
                parameter_path = Path(view["parameters_path"])
                if suffix == ".en.md":
                    parameter_path = parameter_path.with_name("parameters.en.md")
                self.assertIn((ROOT / parameter_path).resolve(), targets)
                self.assertIn(source_hash, text)
                self.assertNotIn("tested_at", text)
                self.assertNotIn("duration_seconds", text)
                self.assertNotRegex(text, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
                for note in view["notes"]["en" if suffix == ".en.md" else "zh"]:
                    self.assertIn("#L" + str(note["line"]), text)
                    self.assertIn(note["description"], text)
                for url in view["sources"]:
                    self.assertIn(url, text)
                self.assertTrue(all(target.is_relative_to(ROOT) and target.exists() for target in targets))
            zh = pages[Path("human/examples") / (view["vendor"] + ".md")]
            en = pages[Path("human/examples") / (view["vendor"] + ".en.md")]
            links = lambda text: set(re.findall(r"https://[^\s)>\\]+", text))
            self.assertEqual(links(zh), links(en))

    def test_only_fourteen_pages_and_no_unverified_extra_python_are_generated(self):
        views, pages = self.views_and_pages()
        expected = {
            Path("human/examples") / (name + suffix)
            for name in ({"README"} | set(DEFAULTS))
            for suffix in (".md", ".en.md")
        }
        self.assertEqual(set(pages), expected)
        known_source = {view["source_text"] for view in views}
        for page, text in pages.items():
            blocks = python_blocks(text)
            if page.name.startswith("README"):
                self.assertEqual(blocks, [])
            else:
                self.assertEqual(len(blocks), 1)
                self.assertIn(blocks[0], known_source)
            self.assertEqual((ROOT / page).read_text(encoding="utf-8"), text)

    def test_generation_and_check_never_read_keys_connect_or_mutate_public_evidence(self):
        before = public_snapshot(ROOT)
        with offline_only():
            self.renderer.build_views(ROOT)
            self.renderer.expected_pages(ROOT)
        self.assertEqual(before, public_snapshot(ROOT))

    def test_default_cli_only_checks_and_write_check_are_mutually_exclusive(self):
        with offline_only():
            pages = self.renderer.expected_pages(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(self.renderer, "expected_pages", return_value=pages):
                self.assertEqual(self.run_cli("--write", root=root)[0], 0)
                before = {path: (root / path).read_bytes() for path in pages}
                self.assertEqual(self.run_cli(root=root)[0], 0)
                self.assertEqual(before, {path: (root / path).read_bytes() for path in pages})
                self.assertEqual(self.run_cli("--write", "--check", root=root)[0], 2)
                self.assertEqual(before, {path: (root / path).read_bytes() for path in pages})

    def test_write_check_only_touch_fourteen_fixture_pages_and_detect_stale_english(self):
        before = public_snapshot(ROOT)
        with offline_only():
            pages = self.renderer.expected_pages(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(self.renderer, "expected_pages", return_value=pages):
                self.assertEqual(self.run_cli("--check", root=root)[0], 2)
                self.assertFalse(any(root.iterdir()))
                self.assertEqual(self.run_cli("--write", root=root)[0], 0)
                files = {path.relative_to(root) for path in root.rglob("*") if path.is_file()}
                self.assertEqual(files, set(pages))
                self.assertEqual(self.run_cli("--check", root=root)[0], 0)
                stale = root / "human/examples/deepseek.en.md"
                stale.write_text("synthetic stale page\n", encoding="utf-8")
                self.assertEqual(self.run_cli("--check", root=root)[0], 2)
                self.assertEqual(self.run_cli("--write", root=root)[0], 0)
                self.assertEqual(self.run_cli(root=root)[0], 0)
        self.assertEqual(before, public_snapshot(ROOT))

    def test_missing_or_nonpassed_basic_evidence_fails_closed_in_public_fixtures(self):
        source = "models/deepseek/deepseek-flash/examples/01_basic.py"
        for mode in ("missing", "failed"):
            with self.subTest(mode=mode):
                root = self.temporary_repository()
                changes = 0
                for path in (root / "verification/examples").glob("*.json"):
                    report = json.loads(path.read_text(encoding="utf-8"))
                    results = []
                    for record in report.get("results", []):
                        if record.get("path") == source:
                            changes += 1
                            if mode == "missing":
                                continue
                            record.update(status="failed", exit_code=1)
                        results.append(record)
                    report["results"] = results
                    path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
                self.assertGreater(changes, 0)
                with offline_only(), self.assertRaises(ValueError):
                    self.renderer.build_views(root)

    def test_each_basic_requires_exact_identity_and_current_strict_pass_even_if_summary_is_green(self):
        source = "models/deepseek/deepseek-flash/examples/01_basic.py"
        with offline_only():
            catalog, release_tool = self.renderer.dependencies(ROOT)
            baseline = release_tool.collect_release(ROOT)
        for case in ("missing_row", "failed", "not_strict", "old_source", "wrong_vendor", "wrong_model"):
            with self.subTest(case=case):
                synthetic = copy.deepcopy(baseline)
                row = next(row for row in synthetic["rows"] if row["path"] == source)
                if case == "missing_row":
                    synthetic["rows"].remove(row)
                elif case == "failed":
                    row["status"] = "failed"
                elif case == "not_strict":
                    row["selected"]["strict_passed"] = False
                elif case == "old_source":
                    row["selected"]["current_source"] = False
                elif case == "wrong_vendor":
                    row["vendor"] = "kimi"
                else:
                    row["model_id"] = "synthetic-other-model"
                # Intentionally leave aggregate counts unchanged: a summary is not file evidence.
                with offline_only(), \
                        patch.object(self.renderer, "dependencies", return_value=(catalog, release_tool)), \
                        patch.object(release_tool, "collect_release", return_value=synthetic), \
                        self.assertRaises(ValueError):
                    self.renderer.build_views(ROOT)

    def test_source_change_cannot_reuse_a_passed_report_or_generate_a_verified_page(self):
        root = self.temporary_repository()
        source = root / "models/deepseek/deepseek-flash/examples/01_basic.py"
        source.write_bytes(source.read_bytes() + b"\n# synthetic offline source mutation\n")
        with offline_only():
            with self.assertRaises(ValueError):
                self.renderer.build_views(root)
            with self.assertRaises(ValueError):
                self.renderer.expected_pages(root)
        self.assertFalse((root / "human/examples").exists())


if __name__ == "__main__":
    unittest.main()
