"""Public code reading pages never consult keys, APIs or private evidence."""

import ast
import builtins
from contextlib import contextmanager, redirect_stderr, redirect_stdout
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

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/render_human_examples.py"
DEFAULTS = {"deepseek": "deepseek-flash", "kimi": "kimi-k2.6", "zhipu": "glm-4.7",
            "qwen": "qwen-flash", "doubao": "doubao-seed-2-1-pro-260628", "minimax": "MiniMax-M2.7"}
PRIVATE_FIELDS = {"report", "evidence_id", "source_sha256", "support_sha256", "tested_at",
                  "duration_seconds", "live_passed_files", "strict_passed", "requests"}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def offline_only():
    original_path_open, original_open = Path.open, builtins.open
    def check(value):
        if isinstance(value, (str, os.PathLike)):
            path = Path(value)
            if path.name.startswith(".env") or ".local" in path.parts or "verification" in path.parts:
                raise AssertionError("credentials_or_private_evidence_must_not_be_read")
    def path_open(path, *args, **kwargs):
        check(path)
        return original_path_open(path, *args, **kwargs)
    def builtin_open(path, *args, **kwargs):
        check(path)
        return original_open(path, *args, **kwargs)
    def deny(*args, **kwargs):
        raise AssertionError("network_or_example_execution_must_not_occur")
    with patch.object(os, "environ", {}), patch.object(Path, "open", path_open), patch("builtins.open", builtin_open), \
            patch.object(socket, "create_connection", deny), patch.object(socket.socket, "connect", deny), \
            patch.object(socket, "getaddrinfo", deny), patch("subprocess.Popen", deny), \
            patch("runpy.run_path", deny), patch("runpy.run_module", deny):
        yield


def public_snapshot(root):
    paths = [p for p in (root / "models").glob("*/*/examples/*") if p.is_file() and p.suffix in {".py", ".ts", ".sh", ".json"}]
    paths += list((root / "examples").glob("*.py")) + list((root / "skills/model-manual/references/models").glob("*.json"))
    paths += [root / "skills/model-manual/references/vendors.json"] + list((root / "human/examples").glob("*.md"))
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def python_blocks(text):
    return re.findall(r"^\x60\x60\x60python\n(.*?)^\x60\x60\x60[ \t]*$", text, re.M | re.S)


def local_targets(page, text):
    return {(ROOT / page.parent / unquote(href.split("#", 1)[0].strip("<>"))).resolve()
            for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text) if not urlsplit(href).scheme and not href.startswith("#")}


class HumanExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with offline_only():
            cls.renderer = load_module("human_renderer_under_test", SCRIPT)

    def views_and_pages(self):
        with offline_only():
            return self.renderer.build_views(ROOT), self.renderer.expected_pages(ROOT)

    def run_cli(self, *args, root=ROOT):
        output, errors = io.StringIO(), io.StringIO()
        with offline_only(), redirect_stdout(output), redirect_stderr(errors):
            try:
                code = self.renderer.main(["--root", str(root), *args])
            except SystemExit as error:
                code = error.code
        return code, output.getvalue(), errors.getvalue()

    def temporary_repository(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative in ("models", "examples", "skills/model-manual/references", "skills/model-manual/scripts"):
            shutil.copytree(ROOT / relative, root / relative, ignore=shutil.ignore_patterns(".env*", "__pycache__"))
        return root

    def test_views_use_exact_paid_models_and_current_line_anchors(self):
        views, _ = self.views_and_pages()
        self.assertEqual({v["vendor"]: v["model_id"] for v in views}, DEFAULTS)
        references = ROOT / "skills/model-manual/references"
        vendors = json.loads((references / "vendors.json").read_text(encoding="utf-8"))["vendors"]
        for view in views:
            model, vendor = view["model_id"], view["vendor"]
            self.assertEqual(vendors[vendor]["default_model"], model)
            self.assertEqual(Path(view["path"]), Path("models") / vendor / model / "examples/01_basic.py")
            card = json.loads((references / "models" / (model + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(card["billing"]["type"]["value"], "paid")
            self.assertEqual(set(view["notes"]), {"zh", "en"})
            for notes in view["notes"].values():
                self.assertTrue(notes)
                for note in notes:
                    self.assertEqual(set(note), {"line", "anchor", "description"})
                    self.assertIs(type(note["line"]), int)
                    self.assertIn(note["anchor"], view["source_text"].splitlines()[note["line"] - 1])
                    self.assertTrue(note["description"].strip())
            self.assertEqual([(n["line"], n["anchor"]) for n in view["notes"]["zh"]], [(n["line"], n["anchor"]) for n in view["notes"]["en"]])

    def test_views_contain_public_source_metadata_not_execution_records(self):
        views, _ = self.views_and_pages()
        for view in views:
            self.assertFalse(PRIVATE_FIELDS.intersection(view))
            self.assertEqual(view["source_text"].encode("utf-8"), (ROOT / view["path"]).read_bytes())
            self.assertTrue((ROOT / view["parameters_path"]).is_file())
            self.assertTrue(view["sources"])

    def test_invalid_local_records_are_never_consulted(self):
        root = self.temporary_repository()
        with offline_only():
            baseline = self.renderer.expected_pages(root)
        for relative in (".local/evidence/bindings.json", "verification/examples/synthetic.json"):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("invalid synthetic evidence; must not be opened", encoding="utf-8")
        with offline_only():
            self.assertEqual(self.renderer.expected_pages(root), baseline)

    def test_python_fences_are_verbatim_and_identical_between_editions(self):
        views, pages = self.views_and_pages()
        for view in views:
            for suffix in (".md", ".en.md"):
                page = Path("human/examples") / (view["vendor"] + suffix)
                self.assertEqual([b.encode("utf-8") for b in python_blocks(pages[page])], [(ROOT / view["path"]).read_bytes()])

    def test_code_is_parsed_not_executed_and_requests_exact_model(self):
        views, pages = self.views_and_pages()
        with offline_only():
            for view in views:
                syntax = ast.parse(python_blocks(pages[Path("human/examples") / (view["vendor"] + ".md")])[0])
                models = [k.value.value for node in ast.walk(syntax) if isinstance(node, ast.Call) for k in node.keywords
                          if k.arg == "model" and isinstance(k.value, ast.Constant)]
                self.assertEqual(models, [view["model_id"]])

    def test_pages_link_sources_parameters_code_not_private_reports_or_fingerprints(self):
        views, pages = self.views_and_pages()
        for view in views:
            manifest = json.loads((ROOT / Path(view["path"]).parent / "sources.json").read_text(encoding="utf-8"))
            entry = next(e for e in manifest["examples"] if e["file"] == "01_basic.py")
            self.assertEqual(set(view["sources"]), {s["url"] for s in entry["sources"]})
            for suffix in (".md", ".en.md"):
                page = Path("human/examples") / (view["vendor"] + suffix)
                text, targets = pages[page], local_targets(page, pages[page])
                self.assertIn((ROOT / view["path"]).resolve(), targets)
                parameters = Path(view["parameters_path"])
                if suffix == ".en.md":
                    parameters = parameters.with_name("parameters.en.md")
                self.assertIn((ROOT / parameters).resolve(), targets)
                self.assertTrue(all(t.is_relative_to(ROOT) and t.exists() for t in targets))
                self.assertNotIn("verification/", text)
                self.assertNotIn(".local/", text)
                self.assertNotRegex(text, r"\b[0-9a-f]{64}\b")
                self.assertNotRegex(text, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
                for field in PRIVATE_FIELDS - {"report", "requests"}:
                    self.assertNotIn(field, text)
                for note in view["notes"]["en" if suffix == ".en.md" else "zh"]:
                    self.assertIn("#L" + str(note["line"]), text)
                for url in view["sources"]:
                    self.assertIn(url, text)
            self.assertIn("not published", pages[Path("human/examples") / (view["vendor"] + ".en.md")])
        self.assertIn("不保证当前账户可用", pages[Path("human/examples/README.md")])

    def test_only_fourteen_public_pages_and_no_new_python_are_generated(self):
        views, pages = self.views_and_pages()
        expected = {Path("human/examples") / (name + suffix) for name in ({"README"} | set(DEFAULTS)) for suffix in (".md", ".en.md")}
        self.assertEqual(set(pages), expected)
        for page, text in pages.items():
            blocks = python_blocks(text)
            self.assertEqual(len(blocks), 0 if page.name.startswith("README") else 1)
            self.assertTrue(all(b in {v["source_text"] for v in views} for b in blocks))
            self.assertEqual((ROOT / page).read_text(encoding="utf-8"), text)

    def test_rendering_never_reads_private_evidence_or_mutates_public_source(self):
        before = public_snapshot(ROOT)
        self.views_and_pages()
        self.assertEqual(before, public_snapshot(ROOT))

    def test_default_cli_checks_and_actions_are_mutually_exclusive(self):
        _, pages = self.views_and_pages()
        with tempfile.TemporaryDirectory() as directory, patch.object(self.renderer, "expected_pages", return_value=pages):
            root = Path(directory)
            self.assertEqual(self.run_cli("--write", root=root)[0], 0)
            before = {p: (root / p).read_bytes() for p in pages}
            self.assertEqual(self.run_cli(root=root)[0], 0)
            self.assertEqual(self.run_cli("--write", "--check", root=root)[0], 2)
            self.assertEqual(before, {p: (root / p).read_bytes() for p in pages})

    def test_writer_only_touches_fourteen_fixture_pages_and_detects_stale_english(self):
        _, pages = self.views_and_pages()
        with tempfile.TemporaryDirectory() as directory, patch.object(self.renderer, "expected_pages", return_value=pages):
            root = Path(directory)
            self.assertEqual(self.run_cli("--check", root=root)[0], 2)
            self.assertFalse(any(root.iterdir()))
            self.assertEqual(self.run_cli("--write", root=root)[0], 0)
            self.assertEqual({p.relative_to(root) for p in root.rglob("*") if p.is_file()}, set(pages))
            self.assertEqual(self.run_cli("--check", root=root)[0], 0)
            (root / "human/examples/deepseek.en.md").write_text("synthetic stale page\n", encoding="utf-8")
            self.assertEqual(self.run_cli("--check", root=root)[0], 2)

    def test_public_manifest_and_paid_identity_errors_fail_closed_without_reports(self):
        for case in ("public_passed", "unofficial_source", "free_card", "changed_default", "missing_parameters"):
            root = self.temporary_repository()
            folder = root / "models/deepseek/deepseek-flash"
            path = folder / "examples/sources.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            if case in {"public_passed", "unofficial_source"}:
                if case == "public_passed":
                    data["examples"][0]["verification"]["live"] = "passed"
                else:
                    data["examples"][0]["sources"][0]["url"] = "https://example.invalid/synthetic"
                path.write_text(json.dumps(data), encoding="utf-8")
            elif case == "missing_parameters":
                (folder / "parameters.md").unlink()
            else:
                path = root / "skills/model-manual/references" / ("models/deepseek-flash.json" if case == "free_card" else "vendors.json")
                data = json.loads(path.read_text(encoding="utf-8"))
                if case == "free_card":
                    data["billing"]["type"]["value"] = "free"
                else:
                    data["vendors"]["deepseek"]["default_model"] = "synthetic-other-model"
                path.write_text(json.dumps(data), encoding="utf-8")
            with self.subTest(case=case), offline_only(), self.assertRaises(ValueError):
                self.renderer.build_views(root)

    def test_bad_syntax_model_anchor_or_fence_requires_source_review(self):
        for case in ("syntax", "model", "anchor", "fence", "newline"):
            root = self.temporary_repository()
            source = root / "models/deepseek/deepseek-flash/examples/01_basic.py"
            text = source.read_text(encoding="utf-8")
            if case == "syntax":
                text += "\ninvalid(\n"
            elif case == "model":
                text = text.replace('model="deepseek-flash"', 'model="synthetic-other-model"')
            elif case == "anchor":
                text = text.replace("client = OpenAI(", "client=OpenAI(")
            elif case == "fence":
                text += "\n# ```\n"
            else:
                text = text.rstrip("\n")
            source.write_text(text, encoding="utf-8")
            with self.subTest(case=case), offline_only(), self.assertRaises((ValueError, SyntaxError)):
                self.renderer.build_views(root)

    def test_valid_source_change_updates_public_code_without_claiming_private_pass(self):
        root = self.temporary_repository()
        source = root / "models/deepseek/deepseek-flash/examples/01_basic.py"
        source.write_bytes(source.read_bytes() + b"\n# synthetic public source review\n")
        with offline_only():
            pages = self.renderer.expected_pages(root)
        self.assertEqual(python_blocks(pages[Path("human/examples/deepseek.md")])[0].encode("utf-8"), source.read_bytes())
        self.assertNotIn("passed real HTTP", pages[Path("human/examples/deepseek.en.md")])


if __name__ == "__main__":
    unittest.main()
