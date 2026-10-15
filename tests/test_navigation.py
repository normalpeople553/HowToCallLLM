"""Offline checks for the three-entry home and provider-first navigation.

Only public Markdown/JSON is read. No examples, generators or model APIs run.
General link resolution and generated-content equality have their own suites.
"""

import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
VENDORS = {"deepseek", "kimi", "zhipu", "qwen", "doubao", "minimax"}


def read(relative):
    path = ROOT / relative
    if path.name.startswith(".env"):
        raise AssertionError("navigation_tests_must_not_read_credentials")
    return path.read_text(encoding="utf-8")


def prose(text):
    return re.sub(r"\x60\x60\x60.*?\x60\x60\x60", "", text, flags=re.S)


def links(text):
    return re.findall(r"\[([^\]\n]*)\]\(([^)\n]+)\)", prose(text))


def local_target(page, href):
    parsed = urlsplit(href.strip("<>"))
    if parsed.scheme or parsed.netloc:
        return None
    path = (ROOT / page.parent / unquote(parsed.path)).resolve() if parsed.path else ROOT / page
    return path.relative_to(ROOT)


def local_targets(page, text):
    return {
        target for _, href in links(text)
        if (target := local_target(page, href)) is not None
    }


def tables(text):
    groups, current = [], []
    for line in prose(text).splitlines() + [""]:
        if line.lstrip().startswith("|"):
            current.append(line.strip())
        elif current:
            if len(current) >= 2 and re.fullmatch(r"[\s|:-]+", current[1]):
                groups.append(current)
            current = []
    return groups


def explicit_ids(text):
    return set(re.findall(r"\bid=[\"']([^\"']+)[\"']", prose(text)))


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.providers = json.loads(read("skills/model-manual/references/vendors.json"))["vendors"]

    def test_home_has_one_three_entry_table_not_parallel_feature_or_language_directories(self):
        for suffix in (".md", ".en.md"):
            with self.subTest(edition=suffix):
                page = Path("README" + suffix)
                text = read(page)
                primary = tables(text)
                self.assertEqual(len(primary), 1, "Home must not repeat feature/model inventories")
                rows = primary[0][2:]
                self.assertEqual(len(rows), 3)
                expected = {Path(folder) / ("README" + suffix) for folder in ("human", "models", "agents")}
                actual = []
                for row in rows:
                    row_links = links(row)
                    self.assertEqual(len(row_links), 1, "Language switching is not a parallel directory column")
                    target = local_target(page, row_links[0][1])
                    self.assertIn(target, expected)
                    actual.append(target)
                self.assertEqual(set(actual), expected)
                self.assertEqual(len(set(actual)), len(actual))
                destinations = local_targets(page, text)
                opposite = Path("README.md" if suffix == ".en.md" else "README.en.md")
                self.assertIn(opposite, destinations)
                self.assertIn("https://github.com/normalpeople553/HowToBuildAgent", text)
                forbidden = {
                    Path("docs/model-lists/README.md"), Path("en/docs/model-lists/README.md"),
                    Path("docs/参数说明与调参.md"), Path("en/docs/parameters.md"),
                    Path("docs/官方示例索引.md"), Path("en/docs/example-index.md"),
                    Path("skills/model-manual/SKILL.md"), Path("skills/model-manual/SKILL.en.md"),
                    *(Path("skills/model-manual/scripts") / filename for filename in
                      ("model_catalog.py", "example_catalog.py", "generate_snippet.py")),
                }
                self.assertFalse(destinations & forbidden, "Detailed tools and topics belong behind the three entries")
                self.assertFalse(any(
                    target.parts[:1] == ("models",) and len(target.parts) > 2 for target in destinations
                ), "The home must not repeat the six-model table")

    def test_home_retains_maintenance_evidence_license_and_ignore_safety_links(self):
        for suffix in (".md", ".en.md"):
            with self.subTest(edition=suffix):
                page = Path("README" + suffix)
                text = read(page)
                destinations = local_targets(page, text)
                verification = Path("en/docs/verification.md" if suffix == ".en.md" else "docs/验证与复现.md")
                policy = Path("en/docs/evidence-policy.md" if suffix == ".en.md" else "docs/来源与核验规则.md")
                self.assertTrue({verification, policy, Path("LICENSE"), Path(".gitignore")} <= destinations)
                self.assertIn(".env", prose(text))

    def test_model_directory_has_six_provider_rows_with_exact_manual_and_human_code_routes(self):
        self.assertEqual(set(self.providers), VENDORS)
        for suffix in (".md", ".en.md"):
            page = Path("models") / ("README" + suffix)
            text = read(page)
            prefix = Path("en/docs/model-lists" if suffix == ".en.md" else "docs/model-lists")
            expected_lists = {prefix / (vendor + ".md") for vendor in VENDORS}
            candidates = [
                table for table in tables(text)
                if expected_lists <= local_targets(page, "\n".join(table))
            ]
            self.assertEqual(len(candidates), 1)
            rows = candidates[0][2:]
            self.assertEqual(len(rows), len(VENDORS))
            for vendor, config in self.providers.items():
                with self.subTest(edition=suffix, vendor=vendor):
                    listing = prefix / (vendor + ".md")
                    matched = [row for row in rows if listing in local_targets(page, row)]
                    self.assertEqual(len(matched), 1)
                    destinations = local_targets(page, matched[0])
                    manual = Path("models") / vendor / config["default_model"] / ("README" + suffix)
                    human = Path("human/examples") / (vendor + suffix)
                    self.assertTrue({listing, manual, human} <= destinations)

    def test_human_guide_keeps_reading_anchor_code_parameters_and_pitfalls(self):
        for suffix in (".md", ".en.md"):
            with self.subTest(edition=suffix):
                page = Path("human") / ("README" + suffix)
                text = read(page)
                self.assertIn("reading-path", explicit_ids(text))
                destinations = local_targets(page, text)
                parameters = Path("en/docs/parameters.md" if suffix == ".en.md" else "docs/参数说明与调参.md")
                pitfalls = Path("en/docs/production-pitfalls.md" if suffix == ".en.md" else "docs/06-真实踩雷与生产检查.md")
                self.assertTrue({
                    Path("human/examples") / ("README" + suffix), parameters, pitfalls,
                    Path("models") / ("README" + suffix),
                } <= destinations)
                self.assertIn("https://github.com/normalpeople553/HowToBuildAgent", text)

    def test_agent_entry_still_reaches_canonical_skill_lookup_and_generation_tools(self):
        for suffix in (".md", ".en.md"):
            with self.subTest(edition=suffix):
                page = Path("agents") / ("README" + suffix)
                destinations = local_targets(page, read(page))
                skill = Path("skills/model-manual") / ("SKILL" + suffix)
                self.assertIn(skill, destinations)
                reachable = destinations | local_targets(skill, read(skill))
                required = {
                    Path("skills/model-manual/references/vendors.json"),
                    Path("skills/model-manual/references/models"),
                    Path("skills/model-manual/references") / ("workflows" + suffix),
                    *(Path("skills/model-manual/scripts") / filename for filename in
                      ("model_catalog.py", "example_catalog.py", "generate_snippet.py")),
                }
                self.assertTrue(required <= reachable)
                self.assertIn(Path("models") / ("README" + suffix), destinations)

    def test_chinese_home_legacy_explicit_anchors_remain_compatible(self):
        self.assertTrue({"让说明书生成代码", "快速参数表"} <= explicit_ids(read("README.md")))

    def test_clickable_model_ids_use_exact_manual_or_official_page_and_code_never_falls_back(self):
        maintained = {(vendor, config["default_model"]) for vendor, config in self.providers.items()}
        for vendor in VENDORS:
            data = json.loads(read(Path("data/model-lists") / (vendor + ".json")))
            for english in (False, True):
                suffix = ".en.md" if english else ".md"
                page = Path("en/docs/model-lists" if english else "docs/model-lists") / (vendor + ".md")
                text = read(page)
                rows = [row for table in tables(text) for row in table[2:]]
                for entry in data["models"]:
                    if entry["status"] == "retired":
                        continue
                    identity = entry["model_id"]
                    with self.subTest(vendor=vendor, model=identity, english=english):
                        matches = [
                            (row, href)
                            for row in rows for label, href in links(row)
                            if label.strip("\x60*") == identity
                        ]
                        self.assertEqual(len(matches), 1, "Every exact ID must be a direct clickable route")
                        row, href = matches[0]
                        destinations = local_targets(page, row)
                        if (vendor, identity) in maintained:
                            folder = Path("models") / vendor / identity
                            self.assertEqual(local_target(page, href), folder / ("README" + suffix))
                            self.assertIn(folder / "examples/01_basic.py", destinations)
                        else:
                            self.assertEqual(href, entry["model_url"])
                            self.assertFalse(any(
                                target.parts[:1] == ("models",) and "examples" in target.parts
                                for target in destinations
                            ), "An unmaintained ID or alias must not inherit another model's raw code")


if __name__ == "__main__":
    unittest.main()
