"""Tests of the project-kit tools (AA-1103): the kit transform and the generic-source check.

Invented text only. Run: python3 -m unittest discover -s tools/project-kit -p 'test_*.py'
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_kit_sources as cks  # noqa: E402
from kit_transform import MarkerError, transform, transform_bytes  # noqa: E402


class TransformTest(unittest.TestCase):
    def test_no_marker_is_a_byte_copy(self):
        data = "line one\n\nline two\n".encode()
        self.assertIs(transform_bytes(data), data)

    def test_binary_is_copied_unchanged(self):
        data = b"\xff\xfe kit:skip \x00"
        self.assertEqual(transform_bytes(data), data)

    def test_markdown_skip_block_and_blank_lines(self):
        src = "a\n\n<!-- kit:skip -->\nlocal only\n<!-- /kit:skip -->\n\nb\n"
        self.assertEqual(transform(src), "a\n\nb\n")

    def test_hash_skip_block(self):
        src = "x = 1\n# kit:skip\ny = 2\n# /kit:skip\nz = 3\n"
        self.assertEqual(transform(src), "x = 1\nz = 3\n")

    def test_drop_line_markdown_table_and_hash(self):
        src = "| a | b |\n| c | d <!-- kit:drop --> |\nkey: v # kit:drop\nend\n"
        self.assertEqual(transform(src), "| a | b |\nend\n")

    def test_only_line_markdown_and_hash(self):
        src = "<!-- kit:only Generic line. -->\n# kit:only key: value\n"
        self.assertEqual(transform(src), "Generic line.\nkey: value\n")

    def test_only_block(self):
        src = "a\n<!-- kit:only\n| x | y |\nkit:only -->\nb\n"
        self.assertEqual(transform(src), "a\n| x | y |\nb\n")

    def test_drop_then_only_keeps_single_blank(self):
        src = "a\n\n- local <!-- kit:drop -->\n\n<!-- kit:only - generic -->\n\nb\n"
        self.assertEqual(transform(src), "a\n\n- generic\n\nb\n")

    def test_unbalanced_markers_raise(self):
        for bad in (
            "<!-- kit:skip -->\nno close\n",
            "<!-- /kit:skip -->\n",
            "<!-- kit:skip -->\n<!-- kit:only\nkit:only -->\n<!-- /kit:skip -->\n",
            "<!-- kit:only\nx\n<!-- /kit:skip -->\n",
        ):
            with self.assertRaises(MarkerError, msg=bad):
                transform(bad)


class CheckSourcesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        self.deny = self.root / "deny.txt"
        self.deny.write_text("# invented terms\n(?i)\\bacme\\b\n\\bZX-[0-9]+\n", encoding="utf-8")
        self.sources = self.root / "sources.txt"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel: str, text: str) -> None:
        (self.root / rel).write_text(text, encoding="utf-8")

    def check(self, lines: str) -> list[str]:
        self.sources.write_text(lines, encoding="utf-8")
        return cks.check_sources(self.root, self.sources, self.deny)

    def test_clean_source_passes(self):
        self.write("docs/a.md", "Generic text.\n<!-- kit:skip -->\nAcme only, see ZX-12.\n<!-- /kit:skip -->\n")
        self.assertEqual(self.check("docs/a.md template/docs/a.md\n"), [])

    def test_unmarked_term_fails_with_line_not_text(self):
        self.write("docs/a.md", "ok\nTalk to Acme.\n")
        errors = self.check("docs/a.md template/docs/a.md\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("docs/a.md:2:", errors[0])
        self.assertNotIn("Talk to", errors[0])

    def test_drop_marked_term_passes(self):
        self.write("docs/a.md", "ok\n- see ZX-7 <!-- kit:drop -->\n")
        self.assertEqual(self.check("docs/a.md template/docs/a.md\n"), [])

    def test_bad_rows(self):
        self.write("docs/a.md", "ok\n")
        errors = self.check(
            "docs/a.md template/docs/a.md\n"
            "docs/a.md template/docs/a.md\n"
            "docs/missing.md template/docs/m.md\n"
            "docs/a.md ../outside.md\n"
            "only-one-field\n"
        )
        text = "\n".join(errors)
        self.assertIn("listed twice", text)
        self.assertIn("does not exist", text)
        self.assertIn("inside the template repo", text)
        self.assertIn("expected `<source> <dest>`", text)

    def test_marker_error_is_reported(self):
        self.write("docs/a.md", "<!-- kit:skip -->\nnever closed\n")
        errors = self.check("docs/a.md template/docs/a.md\n")
        self.assertTrue(any("never closed" in e for e in errors))

    def test_scan_tree_checks_paths_and_text(self):
        tree = self.root / "tree"
        (tree / "acme-notes").mkdir(parents=True)
        (tree / "acme-notes" / "x.md").write_text("fine\n", encoding="utf-8")
        (tree / "y.md").write_text("ZX-3 left here\n", encoding="utf-8")
        errors = cks.scan_tree(tree, self.deny)
        self.assertEqual(len(errors), 2)


class RealKitSourcesTest(unittest.TestCase):
    """The repo's own kit sources stay generic (the same check docs-lint runs)."""

    def test_repo_kit_sources_are_generic(self):
        self.assertEqual(cks.check_sources(cks.ROOT, cks.SOURCES, cks.DENYLIST), [])


if __name__ == "__main__":
    unittest.main()
