"""检查仓库维护的 Markdown 本地文件链接；不访问网络。"""

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class LocalLinkTests(unittest.TestCase):
    def test_document_links_resolve(self):
        paths = [ROOT / "README.md"]
        for directory in ("docs", "models", "skills", "agents"):
            paths.extend((ROOT / directory).rglob("*.md"))
        for path in paths:
            text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
            for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", text):
                parsed = urlsplit(target.strip("<>"))
                if parsed.scheme or not parsed.path:
                    continue
                with self.subTest(document=str(path.relative_to(ROOT)), target=target):
                    self.assertTrue((path.parent / unquote(parsed.path)).resolve().exists())


if __name__ == "__main__":
    unittest.main()
