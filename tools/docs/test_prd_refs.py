"""Unit tests for check_prd_refs.py (AA-894 scope 4). Run: python -m unittest discover -s tools/docs -p 'test_*.py'.

A good PRD passes; a broken reference, a missing PRD field, a bad issue key and a broken acceptance list fail.
Root repo only (not one of the files vendored into the app and Infra repos).
"""

from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import check_prd_refs

GOOD_PRD = """\
---
id: APP-10-demo
title: "PRD: demo"
type: reference
status: draft
owner: nghiep
last_reviewed: 2026-10-22
linear: [AA-821, AA-894]
adrs:
  - docs/adr/0010-demo.md
contracts: [docs/contracts/demo.v1.openapi.yaml]
erd: [docs/architecture/erd/design/demo.md]
migrations: []
---

# PRD: demo

## Acceptance criteria

- **AC-1** The demo works.
- **AC-2** The demo refuses a bad request.

## After the list

- **AC-1** text outside the section does not count as a duplicate
"""


class PrdRefsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        for rel in ("docs/adr/0010-demo.md", "docs/contracts/demo.v1.openapi.yaml",
                    "docs/architecture/erd/design/demo.md"):
            self.write(rel, "x\n")
        self.write("docs/product/README.md", "---\nid: APP-10\n---\n\n# Index, not a PRD\n")

    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def run_check(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_prd_refs.main(["--root", str(self.root)])
        return code, out.getvalue()

    def test_good_prd_passes(self):
        self.write("docs/product/demo/prd.md", GOOD_PRD)
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("1 PRD(s)", out)

    def test_broken_reference_fails(self):
        self.write("docs/product/demo/prd.md", GOOD_PRD.replace("0010-demo.md", "0010-gone.md"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("adrs: docs/adr/0010-gone.md does not exist", out)
        self.assertIn("file=docs/product/demo/prd.md,line=9", out)         # points at the adrs: line

    def test_path_outside_the_repo_fails(self):
        for bad in ("/etc/passwd", "../outside.md", "./docs/adr/0010-demo.md"):
            with self.subTest(bad=bad):
                self.write("docs/product/demo/prd.md", GOOD_PRD.replace("erd: [docs/architecture/erd/design/demo.md]",
                                                                         f"erd: [{bad}]"))
                code, out = self.run_check()
                self.assertEqual(code, 1, out)
                self.assertIn("must be a repo-relative path", out)

    def test_missing_field_and_bad_issue_key_fail(self):
        text = GOOD_PRD.replace("migrations: []\n", "").replace("linear: [AA-821, AA-894]", "linear: [AA-821, PR-19]")
        self.write("docs/product/demo/prd.md", text)
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("migrations: required on a PRD", out)
        self.assertIn("linear: not an issue key: PR-19", out)

    def test_acceptance_criteria_rules(self):
        for text, message in (
            (GOOD_PRD.split("## Acceptance criteria")[0], "missing section '## Acceptance criteria'"),
            (GOOD_PRD.replace("- **AC-1** The demo works.\n- **AC-2** The demo refuses a bad request.\n", "Soon.\n"),
             "no criterion"),
            (GOOD_PRD.replace("- **AC-2**", "- **AC-1**"), "duplicate IDs: AC-1"),
        ):
            with self.subTest(message=message):
                self.write("docs/product/demo/prd.md", text)
                code, out = self.run_check()
                self.assertEqual(code, 1, out)
                self.assertIn(message, out)

    def test_other_repo_path(self):
        text = GOOD_PRD.replace("migrations: []", "migrations: [infra/AA-CIS-Infra/db/migrations/crm/crm-001_base.sql]")
        self.write("docs/product/demo/prd.md", text)
        code, out = self.run_check()                                       # repo not checked out: warning only
        self.assertEqual(code, 0, out)
        self.assertIn("::warning", out)
        self.assertIn("not checked out here", out)
        (self.root / "infra/AA-CIS-Infra").mkdir(parents=True)             # checked out (workspace): checked
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("crm-001_base.sql does not exist", out)
        self.write("infra/AA-CIS-Infra/db/migrations/crm/crm-001_base.sql", "-- base\n")
        self.assertEqual(self.run_check()[0], 0)

    def test_references_checked_on_any_page_but_fields_only_required_on_prds(self):
        self.write("docs/ops/page.md", "---\nid: OPS-01\nerd: [docs/architecture/erd/design/none.md]\n---\n\n# Page\n")
        self.write("docs/ops/plain.md", "---\nid: OPS-03\n---\n\n# No PRD fields: fine\n")
        self.write("docs/sessions/journal.md", "---\nerd: [nowhere.md]\n---\n")   # journals are skipped
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("docs/ops/page.md", out)
        self.assertNotIn("plain.md", out)
        self.assertNotIn("journal.md", out)

    def test_prd_without_front_matter_fails(self):
        self.write("docs/product/demo/notes.md", "# Notes without front matter\n")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("a PRD needs front matter", out)


if __name__ == "__main__":
    unittest.main()
