"""Unit tests for the page history and the "What changed in docs" page (AA-1132 A1): build_docs_reader.py rules 13-14.

Run: python -m unittest tools/docs/test_docs_history.py  (needs PyYAML, tools/docs/requirements.txt)
Fixtures use invented pages only; git runs in a temporary repository.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_docs_reader as b  # noqa: E402

# git runs in a temporary repo: drop git's repo-local variables for this whole test process (as test_docs_reader_v2).
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)

ACCOUNT_LIKE = "1234" * 3   # a 12-digit run, built so the source holds no literal account-shaped number


def _page(page_id: str, title: str, extra: str = "", body: str = "Body.\n") -> str:
    return (f"---\nid: {page_id}\ntitle: {title}\ntype: how-to\nstatus: active\nowner: nghiep\naudience: [staff]\n"
            f"last_reviewed: 2026-11-01\n{extra}---\n\n# {title}\n\n{body}")


class SubjectTest(unittest.TestCase):
    def test_pr_suffix_becomes_the_number(self):
        self.assertEqual(b.clean_subject("docs: tidy the river guide (#42)"), ("docs: tidy the river guide", 42))

    def test_issue_keys_are_removed(self):
        text, pr = b.clean_subject("[AA-12] fix: lantern page, KAN-3 and PR-7 notes (AA-1, AA-2) (#9)")
        self.assertEqual(pr, 9)
        for key in ("AA-12", "KAN-3", "PR-7", "AA-1", "AA-2", "[", "()"):
            self.assertNotIn(key, text)
        self.assertTrue(text.startswith("fix: lantern page"))

    def test_ids_are_redacted_and_long_subjects_trimmed(self):
        text, pr = b.clean_subject(f"docs: bucket of {ACCOUNT_LIKE} moved")
        self.assertIsNone(pr)
        self.assertIn("[redacted-account-id]", text)
        long, _ = b.clean_subject("docs: " + "word " * 80)
        self.assertLessEqual(len(long), b.SUBJECT_MAX)
        self.assertTrue(long.endswith("…"))

    def test_other_dash_numbers_stay(self):
        self.assertEqual(b.clean_subject("chore: UTF-8 and S3-1 notes")[0], "chore: UTF-8 and S3-1 notes")


class HistoryBuild(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "repo"
        self.out = Path(self._tmp.name) / "out"
        self.root.mkdir()
        self.git("init", "-q")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                               *args], check=True, capture_output=True, text=True).stdout.strip()

    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self, message: str) -> str:
        self.git("add", ".")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def seed(self) -> list[str]:
        self.write("docs/guides/harbour.md", _page("GUIDE-91", "Harbour guide"))
        self.write("docs/legal/quiet-cove.md", _page("SEC-91", "Quiet cove policy"))
        self.write("docs/generated/tide-table.md", _page("CAT-91", "Tide table", extra="generated: true\n"))
        shas = [self.commit("docs: first pages (#1)")]
        self.write("docs/guides/harbour.md", _page("GUIDE-91", "Harbour guide", body="Second.\n"))
        self.write("docs/legal/quiet-cove.md", _page("SEC-91", "Quiet cove policy", body="Second.\n"))
        shas.append(self.commit("docs: harbour and cove notes (#2)"))
        self.write("docs/generated/tide-table.md", _page("CAT-91", "Tide table", extra="generated: true\n",
                                                         body="Regenerated.\n"))
        shas.append(self.commit("docs: regenerate the tide table (#3)"))
        return shas

    def build(self) -> dict:
        return b.build(self.out, root=self.root, sha="abc123", ref="master")

    def entry(self, manifest: dict, path: str) -> dict:
        return next(p for p in manifest["pages"] if p["path"] == path)

    def test_history_newest_first_with_subjects_and_pr(self):
        shas = self.seed()
        m = self.build()
        hist = self.entry(m, "docs/guides/harbour.md")["history"]
        self.assertEqual([h["sha"] for h in hist], [shas[1], shas[0]])
        self.assertEqual(hist[0]["subject"], "docs: harbour and cove notes")
        self.assertEqual(hist[0]["pr"], 2)
        self.assertEqual(self.entry(m, "docs/guides/harbour.md")["last_changed"],
                         {"sha": hist[0]["sha"], "date": hist[0]["date"]})
        self.assertEqual(m["counts"]["with_history"], 3)

    def test_history_is_capped(self):
        self.write("docs/guides/harbour.md", _page("GUIDE-91", "Harbour guide"))
        self.commit("docs: v0")
        for n in range(b.HISTORY_MAX + 2):
            self.write("docs/guides/harbour.md", _page("GUIDE-91", "Harbour guide", body=f"Edit {n}.\n"))
            self.commit(f"docs: edit {n}")
        hist = self.entry(self.build(), "docs/guides/harbour.md")["history"]
        self.assertEqual(len(hist), b.HISTORY_MAX)
        self.assertEqual(hist[0]["subject"], f"docs: edit {b.HISTORY_MAX + 1}")

    def test_changes_page_lists_written_staff_pages_and_counts_owner_pages(self):
        self.seed()
        m = self.build()
        e = self.entry(m, b.CHANGES_PATH)
        self.assertEqual((e["id"], e["access"], e["nav"], e["generated"], e["history"]),
                         (b.CHANGES_ID, "staff", "reference", True, []))
        body = (self.out / e["key"]).read_text(encoding="utf-8")
        self.assertIn("[Harbour guide](../guides/harbour.md)", body)
        self.assertNotIn("Quiet cove", body)
        self.assertIn("1 page with restricted access", body)
        self.assertNotIn("tide table", body.lower())     # generated pages and their commits are left out
        self.assertIn("PR #2", body)
        self.assertEqual(m["counts"]["changes_commits"], 2)

    def test_changes_page_is_not_searchable(self):
        self.seed()
        m = self.build()
        con = sqlite3.connect(self.out / m["search"]["key"])
        try:
            paths = {row[0] for row in con.execute("SELECT DISTINCT path FROM sections")}
        finally:
            con.close()
        self.assertNotIn(b.CHANGES_PATH, paths)
        self.assertIn("docs/guides/harbour.md", paths)

    def test_no_changes_page_outside_git(self):
        self.write("docs/guides/harbour.md", _page("GUIDE-91", "Harbour guide"))
        (self.root / ".git").rename(self.root / "not-git")
        m = self.build()
        self.assertNotIn(b.CHANGES_PATH, [p["path"] for p in m["pages"]])
        self.assertEqual(self.entry(m, "docs/guides/harbour.md")["history"], [])

    def test_tracked_file_at_the_generated_path_fails(self):
        self.write(b.CHANGES_PATH, _page("CAT-92", "Hand page"))
        self.commit("docs: a hand page")
        with self.assertRaises(SystemExit):
            self.build()

    def test_manifest_json_round_trip(self):
        self.seed()
        self.build()
        m = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(p["history"], list) for p in m["pages"]))


if __name__ == "__main__":
    unittest.main()
