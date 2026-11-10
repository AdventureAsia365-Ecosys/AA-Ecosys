"""Unit tests for check_images.py (AA-1064): image links on docs pages.

Run: python -m unittest discover -s tools/docs -p 'test_*.py'  (needs PyYAML, tools/docs/requirements.txt)
Fixture pages and images are invented; the PNG / WebP files are built in code.
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_docs_reader as b  # noqa: E402
import check_images as ci  # noqa: E402
from test_docs_reader import FAKE_ACCOUNT, png_bytes, webp_bytes  # noqa: E402


class ImageLint(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def put(self, rel: str, data: bytes | str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            p.write_text(data, encoding="utf-8")
        else:
            p.write_bytes(data)

    def messages(self, page: str, body: str) -> list[str]:
        self.put(page, "# Page\n\n" + body)
        return [f.message for f in ci.check_page(self.root, page)]

    def test_good_links_pass(self):
        self.put("docs/guides/images/list-page.png", png_bytes())
        self.put("docs/guides/images/list-page.webp", webp_bytes())
        self.put("docs/architecture/diagrams/a.svg",
                 '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"><g/></svg>\n')
        body = ("![The list page](images/list-page.png)\n![Same, WebP](images/list-page.webp \"title\")\n"
                "![A diagram](../architecture/diagrams/a.svg)\n")
        self.assertEqual(self.messages("docs/guides/run.md", body), [])

    def test_missing_image(self):
        (msg,) = self.messages("docs/guides/run.md", "![Gone](images/gone.png)\n")
        self.assertIn("does not exist", msg)

    def test_no_alt_text(self):
        self.put("docs/guides/images/a.png", png_bytes())
        (msg,) = self.messages("docs/guides/run.md", "![](images/a.png)\n")
        self.assertIn("no alt text", msg)

    def test_oversize_screenshot(self):
        self.put("docs/guides/images/big.png", png_bytes(pad=b.MAX_RASTER_BYTES))
        (msg,) = self.messages("docs/guides/run.md", "![Big](images/big.png)\n")
        self.assertIn("over the 300 KB cap", msg)

    def test_id_in_metadata(self):
        self.put("docs/guides/images/meta.png", png_bytes(text=f"account {FAKE_ACCOUNT}".encode()))
        msgs = self.messages("docs/guides/run.md", "![Meta](images/meta.png)\n")
        self.assertTrue(msgs)
        self.assertTrue(all("in the image metadata" in m for m in msgs), msgs)

    def test_remote_and_inline_images(self):
        msgs = self.messages("docs/guides/run.md",
                             "![Remote](https://example.com/a.png)\n![Inline](data:image/png;base64,AAAA)\n")
        self.assertEqual(len(msgs), 2)
        self.assertTrue(all("never loads" in m for m in msgs))

    def test_never_published_folder(self):
        self.put("docs/audits/2026-x/shot.png", png_bytes())
        (msg,) = self.messages("docs/guides/run.md", "![Evidence](../audits/2026-x/shot.png)\n")
        self.assertIn("never published", msg)

    def test_unsupported_type_and_bad_name(self):
        self.put("docs/guides/images/photo.jpg", b"\xff\xd8\xff")
        self.put("docs/guides/images/my shot.png", png_bytes())
        msgs = self.messages("docs/guides/run.md", "![Photo](images/photo.jpg)\n![Shot](<images/my shot.png>)\n")
        self.assertEqual(len(msgs), 2)
        self.assertIn("use SVG for diagrams, PNG or WebP", msgs[0])
        self.assertIn("letters, digits", msgs[1])

    def test_climbing_out_of_the_repo(self):
        (msg,) = self.messages("docs/a.md", "![Up](../../x.png)\n")
        self.assertIn("does not point at a file", msg)

    def test_code_and_ignore_marker_are_skipped(self):
        body = ("```markdown\n![](gone.png)\n```\n`![](gone.png)` in a sentence\n"
                "![](gone.png) <!-- docs-lint: ignore -->\n")
        self.assertEqual(self.messages("docs/STYLE.md", body), [])

    def test_main_scope_and_exit_code(self):
        self.put("docs/guides/run.md", "# Run\n\n![Gone](images/gone.png)\n")
        self.put("docs/audits/2026-x/README.md", "# Evidence\n\n![](missing.png)\n")   # journal: out of scope
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ci.main(["--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("1 errors", out.getvalue())
        self.assertNotIn("docs/audits/", out.getvalue())
        (self.root / "docs/guides/run.md").write_text("# Run\n\nNo image.\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ci.main(["--root", str(self.root)]), 0)


if __name__ == "__main__":
    unittest.main()
