"""检查仓库维护的 Markdown 本地文件链接；不访问网络。"""

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


def document_paths():
    paths = [ROOT / "README.md", ROOT / "README.en.md", ROOT / "verification/README.md", ROOT / "verification/README.en.md"]
    for directory in ("docs", "models", "skills", "agents", "human", "en"):
        paths.extend((ROOT / directory).rglob("*.md"))
    return paths


def anchors(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    found = set(re.findall(r'\bid=["\x27]([^"\x27]+)["\x27]', text))
    occurrences = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", text, flags=re.M):
        heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
        heading = re.sub(r"<[^>]*>", "", heading)
        slug = "".join(character for character in heading.lower() if character.isalnum() or character in " _-").replace(" ", "-")
        count = occurrences.get(slug, 0)
        occurrences[slug] = count + 1
        found.add(slug if not count else f"{slug}-{count}")
    return found


class LocalLinkTests(unittest.TestCase):
    def test_document_links_resolve(self):
        for path in document_paths():
            text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
            for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", text):
                parsed = urlsplit(target.strip("<>"))
                if parsed.scheme or not parsed.path:
                    continue
                with self.subTest(document=str(path.relative_to(ROOT)), target=target):
                    self.assertTrue((path.parent / unquote(parsed.path)).resolve().exists())

    def test_local_markdown_anchors_resolve_in_both_editions(self):
        for path in document_paths():
            text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
            for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", text):
                parsed = urlsplit(target.strip("<>"))
                if parsed.scheme or not parsed.fragment:
                    continue
                destination = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                if destination.suffix != ".md" or not destination.is_file():
                    continue
                with self.subTest(document=str(path.relative_to(ROOT)), target=target):
                    self.assertIn(unquote(parsed.fragment), anchors(destination.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
