"""Tests for check_alarm_runbooks.py (AA-893). Run: python -m unittest discover -s tools/docs -p 'test_*.py'."""

from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

import check_alarm_runbooks as car

PAGE = """\
---
id: OPS-07
---

# Monitoring and alarm catalog

Severity: [incident response](../ops/incident-response.md).

### cis

| Alarm | Condition | Notifies | Runbook | What it means |
|---|---|---|---|---|
| `aa-cis-dev-api-5xx` | a \\| b >= 5 | alerts (ALARM + OK) | [ops/playbooks/5xx-spike.md](../ops/playbooks/5xx-spike.md) | 5xx. |
| `aa-cis-dev-db` | x | alerts | [ops/database-operations.md](../ops/database-operations.md) | db. |

## EventBridge alarm rules

| Rule | App | Event | Notifies | Runbook | What it means |
|---|---|---|---|---|---|
| `aa-identity-dev-breakglass` | identity | e | alerts | [ops/runbooks/break-glass.md](../ops/runbooks/break-glass.md) | bg. |
"""


class AlarmRunbookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        for f in ("docs/ops/playbooks/5xx-spike.md", "docs/ops/database-operations.md", "docs/ops/runbooks/break-glass.md"):
            self.write(f, "# x\n")

    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(text), encoding="utf-8")

    def run_main(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = car.main(["--root", str(self.root)])
        return rc, out.getvalue()

    def test_valid_page_passes(self) -> None:
        self.write(car.DEFAULT_PAGE, PAGE)
        rc, out = self.run_main()
        self.assertEqual(rc, 0, out)
        self.assertIn("3 alarm rows", out)

    def test_missing_page_is_not_an_error(self) -> None:
        rc, out = self.run_main()
        self.assertEqual(rc, 0)
        self.assertIn("nothing to check", out)

    def test_deleted_runbook_fails(self) -> None:
        self.write(car.DEFAULT_PAGE, PAGE)
        (self.root / "docs/ops/runbooks/break-glass.md").unlink()
        rc, out = self.run_main()
        self.assertEqual(rc, 1)
        self.assertIn("aa-identity-dev-breakglass: runbook docs/ops/runbooks/break-glass.md does not exist", out)

    def test_missing_link_and_outside_docs_fail(self) -> None:
        page = PAGE.replace("[ops/playbooks/5xx-spike.md](../ops/playbooks/5xx-spike.md)", "**MISSING**")
        page = page.replace("[ops/database-operations.md](../ops/database-operations.md)", "[x](../../README.md)")
        self.write("README.md", "# r\n")
        self.write(car.DEFAULT_PAGE, page)
        rc, out = self.run_main()
        self.assertEqual(rc, 1)
        self.assertIn("aa-cis-dev-api-5xx: no runbook link (**MISSING**)", out)
        self.assertIn("aa-cis-dev-db: runbook README.md does not exist", out)

    def test_page_without_rows_fails(self) -> None:
        self.write(car.DEFAULT_PAGE, "# Monitoring and alarm catalog\n\nNone.\n")
        rc, out = self.run_main()
        self.assertEqual(rc, 1)
        self.assertIn("no alarm rows found", out)


if __name__ == "__main__":
    unittest.main()
