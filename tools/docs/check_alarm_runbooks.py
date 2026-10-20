#!/usr/bin/env python3
"""Alarm runbook link check (AA-893). Stdlib only.

docs/generated/alarms.md (OPS-07) is written by AA-CIS-Infra `.github/workflows/docs-gen.yml` from the
Terraform state: one row per CloudWatch alarm and per EventBridge rule that notifies SNS, each with a
Runbook column. This check fails when a row:
  * has no runbook link (the generator writes **MISSING**, **BROKEN**, **NOT IN ROOT REPO** ...);
  * links to a file that does not exist in this repo, or to anything outside docs/.

It runs on every docs PR (docs-lint.yml), so renaming or deleting a runbook that an alarm e-mail
points to fails here, and on the bot PR that regenerates the page. Fix a bad row in the Terraform
(AA-CIS-Infra `accounts/aa365/alarm_runbooks.tf`), never in the generated page.

No alarms.md yet: nothing to check (exit 0).

Usage:
  python tools/docs/check_alarm_runbooks.py
  python tools/docs/check_alarm_runbooks.py --root <repo> --page docs/generated/alarms.md
"""

from __future__ import annotations

import argparse
import posixpath
import re
import sys
from pathlib import Path

from docslib import REPO_ROOT, Finding, emit

DEFAULT_PAGE = "docs/generated/alarms.md"
LINK = re.compile(r"^\[[^\]]+\]\(([^)\s]+)\)$")


def split_row(line: str) -> list[str]:
    """Cells of a Markdown table row; escaped pipes (\\|) stay inside a cell."""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", body)]


def check(root: Path, page: str) -> tuple[list[Finding], int]:
    """Return (findings, rows checked)."""
    path = root / page
    findings: list[Finding] = []
    rows = 0
    col = None
    page_dir = posixpath.dirname(page)
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|"):
            col = None  # a table ended
            continue
        cells = split_row(line)
        if col is None:
            col = cells.index("Runbook") if "Runbook" in cells else -1
            continue
        if col < 0 or set(line.replace("|", "").strip()) <= {"-", ":", " "}:
            continue  # not an alarm table, or the separator row
        rows += 1
        name = cells[0].strip("`")
        cell = cells[col] if col < len(cells) else ""
        m = LINK.match(cell)
        if not m:
            findings.append(Finding(page, n, "Alarm runbook", f"{name}: no runbook link ({cell or 'empty'}); fix the alarm description in AA-CIS-Infra"))
            continue
        target = m.group(1).split("#", 1)[0]
        resolved = posixpath.normpath(posixpath.join(page_dir, target))
        if not resolved.startswith("docs/") or not (root / resolved).is_file():
            findings.append(Finding(page, n, "Alarm runbook", f"{name}: runbook {resolved} does not exist in this repo"))
    return findings, rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--page", default=DEFAULT_PAGE)
    args = ap.parse_args(argv)
    if not (args.root / args.page).is_file():
        print(f"{args.page} not found: nothing to check")
        return 0
    findings, rows = check(args.root, args.page)
    if rows == 0:
        findings.append(Finding(args.page, 1, "Alarm runbook", "no alarm rows found: the page format changed or the page is empty"))
    emit(findings, "error")
    if not findings:
        print(f"{rows} alarm rows, every runbook link resolves")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
