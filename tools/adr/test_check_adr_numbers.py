"""Tests for check_adr_numbers.py (AA-928). Run: python -m unittest discover -s tools/adr -p 'test_*.py'."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import check_adr_numbers as can

README = """# Ecosystem ADRs

| ADR | Title | Status |
|---|---|---|

## Numbering

| Number | Status | For |
|---|---|---|
{rows}

Next free root numbers: {next_free}.
"""


def write_tree(root: Path, files: list[str], rows: list[tuple[str, str]], next_free: str,
               headers: dict[str, str] | None = None) -> Path:
    adr = root / "docs" / "adr"
    adr.mkdir(parents=True, exist_ok=True)
    for old in adr.glob("*.md"):
        old.unlink()
    for name in files:
        head = (headers or {}).get(name, "- **Status:** Proposed")
        (adr / name).write_text(f"# ADR {name[:5]}\n\n{head}\n\n## Context\n\nText.\n", encoding="utf-8")
    table = "\n".join(f"| {n} | Reserved | {what} |" for n, what in rows)
    (adr / "README.md").write_text(README.format(rows=table, next_free=next_free), encoding="utf-8")
    return adr


BASE_FILES = ["0001-a.md", "0002-b.md", "0003-c.md", "0003a-c-amend.md", "0004-d.md"]
BASE_ROWS = [("0005", "AI platform (AA-804)")]


class StaticRules(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def errors(self, files, rows=BASE_ROWS, next_free="**0006**"):
        adr = write_tree(self.tmp, files, rows, next_free)
        return can.check_static(can.load_dir(adr))

    def test_clean_tree_passes(self) -> None:
        self.assertEqual(self.errors(BASE_FILES), [])

    def test_duplicate_base_number_fails(self) -> None:
        errs = self.errors(BASE_FILES + ["0004-other.md"])
        self.assertTrue(any(e.startswith("S1 ") for e in errs), errs)

    def test_duplicate_amendment_fails(self) -> None:
        errs = self.errors(BASE_FILES + ["0003a-again.md"])
        self.assertTrue(any(e.startswith("S1 ") for e in errs), errs)

    def test_amendment_without_base_fails(self) -> None:
        errs = self.errors(BASE_FILES + ["0007a-orphan.md"], next_free="**0006**, **0008**")
        self.assertTrue(any(e.startswith("S2 ") for e in errs), errs)

    def test_file_with_reserved_number_fails(self) -> None:
        errs = self.errors(BASE_FILES + ["0005-ai.md"])
        self.assertTrue(any(e.startswith("S3 ") for e in errs), errs)

    def test_reservation_without_issue_fails(self) -> None:
        errs = self.errors(BASE_FILES, rows=[("0005", "AI platform")])
        self.assertTrue(any(e.startswith("S4 ") for e in errs), errs)

    def test_wrong_next_free_line_fails(self) -> None:
        errs = self.errors(BASE_FILES, next_free="**0005**")
        self.assertTrue(any(e.startswith("S5 ") for e in errs), errs)

    def test_next_free_lists_gaps_then_top(self) -> None:
        self.assertEqual(can.compute_next_free({1, 2, 3, 4, 6}, {5, 9}), [7, 8, 10])
        self.assertEqual(self.errors(BASE_FILES, rows=[("0005", "x (AA-1)"), ("0008", "y (AA-2)")],
                                     next_free="**0006**, **0007**, **0009**"), [])

    def test_legacy_reserved_line_is_read(self) -> None:
        text = "# ADRs\n\nReserved: **0009** AI platform (AA-804).\n"
        self.assertEqual(can.parse_reservations(text), {9: "AI platform (AA-804)"})


class PrRules(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        write_tree(self.root, BASE_FILES, BASE_ROWS, "**0006**")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def pr_errors(self, files, rows=BASE_ROWS, next_free="**0006**", headers=None):
        adr = write_tree(self.root, files, rows, next_free, headers)
        base = can.load_git(self.root, "HEAD", "docs/adr")
        return can.check_pr(base, can.load_dir(adr))

    def test_next_free_number_passes(self) -> None:
        self.assertEqual(self.pr_errors(BASE_FILES + ["0006-new.md"], next_free="**0007**"), [])

    def test_used_number_fails(self) -> None:
        errs = self.pr_errors(BASE_FILES + ["0004-clash.md"])
        self.assertTrue(any(e.startswith("D1 ") for e in errs), errs)

    def test_reserved_number_fails_for_another_issue(self) -> None:
        errs = self.pr_errors(BASE_FILES + ["0005-grab.md"], rows=[], next_free="**0006**",
                              headers={"0005-grab.md": "- **Status:** Proposed\n- **Related Linear:** AA-999"})
        self.assertTrue(any(e.startswith("D2 ") for e in errs), errs)

    def test_reserved_number_passes_for_its_issue(self) -> None:
        errs = self.pr_errors(BASE_FILES + ["0005-ai.md"], rows=[], next_free="**0006**",
                              headers={"0005-ai.md": "- **Status:** Proposed\n- **Related Linear:** AA-804"})
        self.assertEqual(errs, [])

    def test_reserved_number_kept_reserved_fails(self) -> None:
        errs = self.pr_errors(BASE_FILES + ["0005-ai.md"],
                              headers={"0005-ai.md": "- **Status:** Proposed\n- **Related Linear:** AA-804"})
        self.assertTrue(any(e.startswith("D2 ") for e in errs), errs)

    def test_skipping_ahead_fails(self) -> None:
        errs = self.pr_errors(BASE_FILES + ["0007-jump.md"], next_free="**0006**, **0008**")
        self.assertTrue(any(e.startswith("D3 ") for e in errs), errs)

    def test_amendment_letter_skip_fails(self) -> None:
        errs = self.pr_errors(BASE_FILES + ["0003c-skip.md"])
        self.assertTrue(any(e.startswith("D4 ") for e in errs), errs)

    def test_next_amendment_letter_passes(self) -> None:
        self.assertEqual(self.pr_errors(BASE_FILES + ["0003b-next.md", "0004a-first.md"]), [])

    def test_rename_passes(self) -> None:
        files = [f for f in BASE_FILES if f != "0004-d.md"] + ["0004-d-renamed.md"]
        self.assertEqual(self.pr_errors(files), [])


class Propose(unittest.TestCase):
    def test_propose(self) -> None:
        adr = write_tree(Path(tempfile.mkdtemp()), BASE_FILES, BASE_ROWS, "**0006**")
        head = can.load_dir(adr)
        self.assertEqual(can.check_propose(head, "0006"), [])
        self.assertTrue(can.check_propose(head, "0005"))  # reserved
        self.assertTrue(can.check_propose(head, "0004"))  # used
        self.assertTrue(can.check_propose(head, "0008"))  # not next free
        self.assertEqual(can.check_propose(head, "0003b"), [])
        self.assertTrue(can.check_propose(head, "0003c"))


class RepoIndex(unittest.TestCase):
    def test_this_repo_passes(self) -> None:
        head = can.load_dir(can.REPO_ROOT / "docs" / "adr")
        self.assertEqual(can.check_static(head), [])


if __name__ == "__main__":
    unittest.main()
