"""Offline model-list schema, exact-identity coverage and bilingual CLI checks.

These tests never execute an example, read credentials or contact a vendor.
Temporary JSON mutations are synthetic validation fixtures, not API evidence.
"""

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


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/model-manual/scripts/model_catalog.py"
VENDORS = {"deepseek", "kimi", "zhipu", "qwen", "doubao", "minimax"}
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
    """Reject credential files/network before opening or connecting to anything."""
    original_path_open = Path.open
    original_open = builtins.open

    def check_path(value):
        if isinstance(value, (str, os.PathLike)) and Path(value).name.startswith(".env"):
            raise AssertionError("credential_file_must_not_be_read")

    def path_open(path, *args, **kwargs):
        check_path(path)
        return original_path_open(path, *args, **kwargs)

    def builtin_open(path, *args, **kwargs):
        check_path(path)
        return original_open(path, *args, **kwargs)

    def deny_network(*_args, **_kwargs):
        raise AssertionError("network_must_not_be_used")

    # No inherited credentials are visible, even if implementation calls getenv.
    with patch.object(os, "environ", {}), patch.object(Path, "open", path_open), \
            patch("builtins.open", builtin_open), \
            patch.object(socket, "create_connection", deny_network), \
            patch.object(socket.socket, "connect", deny_network), \
            patch.object(socket, "getaddrinfo", deny_network), \
            patch("subprocess.Popen", deny_network):
        yield


def source_snapshot(root):
    """Only public source/card/report files: no glob over private credential files."""
    paths = list((root / "data/model-lists").glob("*.json"))
    paths += list((root / "skills/model-manual/references/models").glob("*.json"))
    paths += [root / "skills/model-manual/references/vendors.json"]
    paths += list((root / "verification/examples").glob("*.json"))
    paths += [
        path for path in (root / "models").glob("*/*/examples/*")
        if path.is_file() and path.suffix in {".py", ".ts", ".sh"}
    ]
    paths += list((root / "examples").glob("*.py"))
    for relative in ("docs/model-lists", "en/docs/model-lists"):
        paths += list((root / relative).glob("*.md"))
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


class ModelCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with offline_only():
            cls.catalog = load_module("model_catalog_under_test", SCRIPT)
            cls.release = load_module("model_catalog_release_reference", ROOT / "tests/check_example_release.py")

    def temporary_catalogs(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        target = root / "data/model-lists"
        shutil.copytree(ROOT / "data/model-lists", target)
        return root, target / "zhipu.json"

    def mutate_fixture(self, mutate):
        root, path = self.temporary_catalogs()
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return root

    def run_cli(self, *args, root=ROOT):
        output, errors = io.StringIO(), io.StringIO()
        with offline_only(), patch.object(self.catalog, "ROOT", root), \
                redirect_stdout(output), redirect_stderr(errors):
            try:
                code = self.catalog.main(list(args))
            except SystemExit as error:
                code = error.code  # argparse rejects incompatible CLI modes.
        return code, output.getvalue(), errors.getvalue()

    def test_six_vendor_lists_have_exact_schema_and_no_claimed_repository_evidence(self):
        with offline_only():
            catalogs = self.catalog.load_catalogs(ROOT)
        self.assertEqual({item["vendor"] for item in catalogs}, VENDORS)
        model_fields = {
            "model_id", "family", "status", "billing", "input_modalities",
            "model_url", "pricing_url", "notes", "sources",
        }
        for item in catalogs:
            raw = json.loads(
                (ROOT / "data/model-lists" / (item["vendor"] + ".json")).read_text(encoding="utf-8")
            )
            self.assertFalse(
                any(row["status"] == "retired" for row in raw["models"]),
                "Current source JSON must not retain retired entries behind a filtered loader",
            )
            self.assertEqual(item["checked_at"], "2026-10-14")
            self.assertEqual(set(item["scope_note"]), {"zh", "en"})
            self.assertTrue(all(item["scope_note"].values()))
            ids = [row["model_id"] for row in item["models"]]
            self.assertTrue(ids)
            self.assertEqual(len(ids), len(set(ids)))
            for row in item["models"]:
                with self.subTest(vendor=item["vendor"], model=row["model_id"]):
                    self.assertEqual(set(row), model_fields)
                    self.assertIn(row["model_url"], row["sources"])
                    self.assertIn(row["pricing_url"], row["sources"])
                    self.assertEqual(set(row["notes"]), {"zh", "en"})
                    self.assertNotEqual(row["status"], "verified")
                    self.assertNotEqual(row["status"], "retired")

    def test_invalid_or_noncanonical_check_dates_are_rejected(self):
        for value in ("not-a-date", "2026-02-30", "20261014", 20261014, None):
            with self.subTest(value=value):
                root = self.mutate_fixture(lambda data: data.update(checked_at=value))
                with offline_only(), self.assertRaises(ValueError):
                    self.catalog.load_catalogs(root)

    def test_unofficial_cross_vendor_and_credential_bearing_urls_are_rejected(self):
        cases = [
            ("official_catalog_url", "https://platform.minimax.cn/docs/overview"),
            ("model_url", "https://api-docs.deepseek.com/quick_start/pricing"),
            ("pricing_url", "https://docs.bigmodel.cn.example.invalid/pricing"),
            ("source", "http://docs.bigmodel.cn/cn/guide/start/pricing"),
            ("source", "https://fixture-user@docs.bigmodel.cn/cn/guide/start/pricing"),
        ]
        for field, url in cases:
            with self.subTest(field=field, url=url):
                def mutate(data):
                    if field == "official_catalog_url":
                        data[field] = url
                    elif field == "source":
                        data["models"][0]["sources"].append(url)
                    else:
                        data["models"][0][field] = url
                        data["models"][0]["sources"].append(url)
                root = self.mutate_fixture(mutate)
                with offline_only(), self.assertRaises(ValueError):
                    self.catalog.load_catalogs(root)

    def test_duplicate_ids_and_filename_vendor_mismatch_are_rejected(self):
        def duplicate(data):
            data["models"].append(copy.deepcopy(data["models"][0]))
        for mutate in (duplicate, lambda data: data.update(vendor="kimi")):
            with self.subTest(mutation=mutate.__name__):
                root = self.mutate_fixture(mutate)
                with offline_only(), self.assertRaises(ValueError):
                    self.catalog.load_catalogs(root)

    def test_missing_model_or_pricing_attribution_is_rejected(self):
        for case in ("empty", "model", "pricing"):
            with self.subTest(case=case):
                def mutate(data):
                    row = data["models"][0]
                    if case == "empty":
                        row["sources"] = []
                    else:
                        row["sources"].remove(row[case + "_url"])
                root = self.mutate_fixture(mutate)
                with offline_only(), self.assertRaises(ValueError):
                    self.catalog.load_catalogs(root)

    def test_data_cannot_forge_verified_live_or_manual_coverage(self):
        cases = [
            ("model", "status", "verified"),
            ("model", "verification", {"live": "passed"}),
            ("model", "live", "passed"),
            ("model", "manual_path", "models/zhipu/glm-4.7/README.md"),
            ("model", "repository_coverage", {"live_passed_files": ["fictional.py"]}),
            ("catalog", "verification", {"live": "passed"}),
        ]
        for target, field, value in cases:
            with self.subTest(target=target, field=field):
                def mutate(data):
                    destination = data if target == "catalog" else data["models"][0]
                    destination[field] = value
                root = self.mutate_fixture(mutate)
                with offline_only(), self.assertRaises(ValueError):
                    self.catalog.load_catalogs(root)

    def test_catalog_additions_do_not_change_the_six_paid_defaults_or_create_cards(self):
        references = ROOT / "skills/model-manual/references"
        before = source_snapshot(ROOT)
        with offline_only():
            rows = self.catalog.select_models(self.catalog.load_catalogs(ROOT))
        vendors = json.loads((references / "vendors.json").read_text(encoding="utf-8"))["vendors"]
        self.assertEqual({vendor: cfg["default_model"] for vendor, cfg in vendors.items()}, DEFAULTS)
        self.assertEqual({path.stem for path in (references / "models").glob("*.json")}, set(DEFAULTS.values()))
        for vendor, model in DEFAULTS.items():
            selected = [row for row in rows if row["vendor"] == vendor and row["model_id"] == model]
            self.assertEqual(len(selected), 1)
            self.assertEqual(selected[0]["billing"], "paid")
            card = json.loads((references / "models" / (model + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(card["billing"]["type"]["value"], "paid")
        self.assertEqual(before, source_snapshot(ROOT))

    def test_exact_vendor_model_billing_and_status_filters_have_no_fallback(self):
        with offline_only():
            catalogs = self.catalog.load_catalogs(ROOT)
            original = json.dumps(catalogs, sort_keys=True)
            all_rows = self.catalog.select_models(catalogs)
            selected = self.catalog.select_models(catalogs, vendor="zhipu", model="glm-4.7")
            self.assertEqual([(row["vendor"], row["model_id"]) for row in selected], [("zhipu", "glm-4.7")])
            self.assertEqual(self.catalog.select_models(catalogs, model="definitely-not-a-model"), [])
            self.assertEqual(self.catalog.select_models(catalogs, vendor="deepseek", model="glm-4.7"), [])
            self.assertEqual(self.catalog.select_models(catalogs, model="minimax-m2.7"), [])
            for field, value in (("billing", "free"), ("status", "alias"), ("status", "unknown")):
                expected = {(r["vendor"], r["model_id"]) for r in all_rows if r[field] == value}
                actual = self.catalog.select_models(catalogs, **{field: value})
                self.assertTrue(expected)
                self.assertEqual({(r["vendor"], r["model_id"]) for r in actual}, expected)
            self.assertEqual(original, json.dumps(catalogs, sort_keys=True))
            # A data-only selection never implicitly loads cards or inherits evidence.
            self.assertTrue(all(not row["repository_coverage"]["example_files"] for row in all_rows))

    def test_injected_retired_ids_never_leak_through_queries_pages_or_index_counts(self):
        with offline_only():
            catalogs = self.catalog.load_catalogs(ROOT)
            baseline_rows = self.catalog.select_models(catalogs)
            baseline_pages = self.catalog.expected_pages(ROOT)
            injected = copy.deepcopy(catalogs)
            zhipu = next(item for item in injected if item["vendor"] == "zhipu")
            retired = copy.deepcopy(zhipu["models"][0])
            retired_id = "offline-retired-id-must-not-be-published"
            retired.update(model_id=retired_id, status="retired")
            zhipu["models"].append(retired)
            original = json.dumps(injected, sort_keys=True)
            self.assertEqual(self.catalog.PUBLIC_STATUSES, self.catalog.STATUSES - {"retired"})
            for filters in (
                {},
                {"vendor": "zhipu"},
                {"status": "retired"},
                {"model": retired_id},
                {"vendor": "zhipu", "model": retired_id, "status": "retired"},
            ):
                with self.subTest(filters=filters):
                    rows = self.catalog.select_models(injected, **filters)
                    self.assertFalse(any(row["status"] == "retired" for row in rows))
                    self.assertFalse(any(row["model_id"] == retired_id for row in rows))
                    if filters.get("status") == "retired" or filters.get("model") == retired_id:
                        self.assertEqual(rows, [])
            self.assertEqual(self.catalog.select_models(injected), baseline_rows)
            with patch.object(self.catalog, "load_catalogs", return_value=injected):
                pages = self.catalog.expected_pages(ROOT)
            # Equality checks both vendor rows and aggregate counts without fixing inventory size.
            self.assertEqual(pages, baseline_pages)
            for path, content in pages.items():
                with self.subTest(page=path.as_posix()):
                    self.assertNotIn(retired_id, content)
            self.assertEqual(original, json.dumps(injected, sort_keys=True))

    def test_new_and_alias_ids_do_not_inherit_manuals_generation_or_live_results(self):
        with offline_only():
            catalogs = self.catalog.load_catalogs(ROOT)
            coverage = self.catalog.project_coverage(ROOT)
            rows = self.catalog.select_models(catalogs, coverage=coverage)
        candidates = [row for row in rows if row["model_id"] not in DEFAULTS.values()]
        self.assertTrue(candidates)
        self.assertTrue(any(row["status"] == "alias" for row in candidates))
        for row in candidates:
            with self.subTest(vendor=row["vendor"], model=row["model_id"]):
                coverage = row["repository_coverage"]
                self.assertFalse(coverage["manual_path"])
                self.assertFalse(coverage["parameters_path"])
                self.assertFalse(coverage["example_files"])
                self.assertFalse(coverage["live_passed_files"])
                self.assertFalse(coverage["generation_registered"])
                self.assertFalse(coverage["default_for_vendor"])
                self.assertEqual(coverage["evidence_status"], "no_examples")

    def test_repository_coverage_is_derived_from_exact_release_rows_not_family_names(self):
        with offline_only():
            coverage = self.catalog.project_coverage(ROOT)
            release = self.release.collect_release(ROOT)
        self.assertEqual(release["total"], 59, "The existing 59-file release must not be expanded by catalog-only rows")
        for vendor, model in DEFAULTS.items():
            with self.subTest(model=model):
                current = coverage[(vendor, model)]
                expected = [row for row in release["rows"] if row["vendor"] == vendor and row["model_id"] == model]
                self.assertEqual(set(current["example_files"]), {row["path"] for row in expected})
                self.assertEqual(set(current["live_passed_files"]), {row["path"] for row in expected if row["status"] == "passed"})
                self.assertTrue(current["generation_registered"])
                self.assertTrue(current["default_for_vendor"])
                self.assertTrue((ROOT / current["manual_path"]).is_file())
                self.assertTrue((ROOT / current["parameters_path"]).is_file())
                self.assertEqual(
                    current["evidence_status"],
                    "all_registered_examples_passed"
                    if expected and all(row["status"] == "passed" for row in expected)
                    else "incomplete_evidence",
                )

    def test_read_only_catalog_paths_never_read_env_or_connect_to_network(self):
        before = source_snapshot(ROOT)
        with offline_only():
            catalogs = self.catalog.load_catalogs(ROOT)
            self.catalog.select_models(catalogs, vendor="deepseek")
            self.catalog.project_coverage(ROOT)
            self.catalog.expected_pages(ROOT)
        self.assertEqual(before, source_snapshot(ROOT))

    def test_bilingual_pages_share_model_ids_official_links_and_dynamic_coverage(self):
        with offline_only():
            catalogs = self.catalog.load_catalogs(ROOT)
            outputs = self.catalog.expected_pages(ROOT)
        expected_paths = {
            Path(prefix) / (name + ".md")
            for prefix in ("docs/model-lists", "en/docs/model-lists")
            for name in ({"README"} | VENDORS)
        }
        self.assertEqual(set(outputs), expected_paths)
        for vendor in VENDORS:
            chinese = outputs[Path("docs/model-lists") / (vendor + ".md")]
            english = outputs[Path("en/docs/model-lists") / (vendor + ".md")]
            official_links = lambda text: set(re.findall(r"https://[^\s)>\\]+", text))
            self.assertEqual(official_links(chinese), official_links(english))
            raw = next(item for item in catalogs if item["vendor"] == vendor)
            for row in raw["models"]:
                self.assertIn(row["model_id"], chinese)
                self.assertIn(row["model_id"], english)
                for source in row["sources"]:
                    self.assertIn(source, chinese)
                    self.assertIn(source, english)
                if row["status"] == "unknown":
                    # Unknown is still public, but must remain in its own caution group.
                    exact_id = "`" + row["model_id"] + "`"
                    zh_heading = re.findall(r"^## (.+)$", chinese[:chinese.index(exact_id)], re.M)[-1]
                    en_heading = re.findall(r"^## (.+)$", english[:english.index(exact_id)], re.M)[-1]
                    self.assertRegex(zh_heading, r"(未确认|待确认)")
                    self.assertIn("unconfirmed", en_heading.lower())
            self.assertIn("示例实测状态.md", chinese)
            self.assertIn("example-status.md", english)
        for path, expected in outputs.items():
            self.assertEqual((ROOT / path).read_text(encoding="utf-8"), expected, path.as_posix())

    def test_default_cli_is_read_only_json_and_unknown_model_does_not_select_a_default(self):
        before = source_snapshot(ROOT)
        code, output, _ = self.run_cli()
        self.assertEqual(code, 0)
        result = json.loads(output)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["kind"], "official_language_model_discovery")
        self.assertIs(result["live_api_calls"], False)
        rows = result["models"]
        self.assertEqual({row["vendor"] for row in rows}, VENDORS)
        self.assertTrue(all("repository_coverage" in row for row in rows))
        code, output, _ = self.run_cli("--model", "definitely-not-a-model")
        self.assertEqual(code, 2)
        missing = json.loads(output)
        self.assertEqual(missing["error"], "no_exact_model_match")
        self.assertEqual(missing["models"], [])
        code, output, _ = self.run_cli("--vendor", "zhipu", "--model", "glm-4.7")
        self.assertEqual(code, 0)
        self.assertEqual([row["model_id"] for row in json.loads(output)["models"]], ["glm-4.7"])
        code, output, errors = self.run_cli("--status", "retired")
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertIn("retired", errors)
        self.assertEqual(before, source_snapshot(ROOT))

    def test_write_and_check_modes_cannot_silently_render_a_filtered_subset(self):
        before = source_snapshot(ROOT)
        for mode in ("--write-pages", "--check"):
            for arguments in (("--vendor", "zhipu"), ("--model", "glm-4.7"), ("--billing", "paid"), ("--status", "available")):
                with self.subTest(mode=mode, arguments=arguments):
                    code, _, _ = self.run_cli(mode, *arguments)
                    self.assertEqual(code, 2)
        self.assertEqual(before, source_snapshot(ROOT))

    def test_page_writer_and_check_detect_english_staleness_in_an_isolated_fixture(self):
        with offline_only():
            outputs = self.catalog.expected_pages(ROOT)
        root, _ = self.temporary_catalogs()
        initial = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*") if path.is_file()
        }
        # Generator contents are checked above against real canonical data.
        # Here only the CLI writer/checker is exercised, never in the real repo.
        with patch.object(self.catalog, "expected_pages", return_value=outputs):
            code, _, _ = self.run_cli("--write-pages", root=root)
            self.assertEqual(code, 0)
            for relative, content in outputs.items():
                self.assertEqual((root / relative).read_text(encoding="utf-8"), content)
            created = {
                path.relative_to(root).as_posix()
                for path in root.rglob("*") if path.is_file()
            }
            self.assertEqual(created, initial | {path.as_posix() for path in outputs})
            self.assertEqual(self.run_cli("--check", root=root)[0], 0)
            english = root / "en/docs/model-lists/zhipu.md"
            english.write_text("stale synthetic translation\n", encoding="utf-8")
            self.assertEqual(self.run_cli("--check", root=root)[0], 2)
            self.assertEqual(self.run_cli("--write-pages", root=root)[0], 0)
            self.assertEqual(self.run_cli("--check", root=root)[0], 0)


if __name__ == "__main__":
    unittest.main()
