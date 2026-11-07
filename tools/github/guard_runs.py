#!/usr/bin/env python3
"""Scheduled guard runs status for the session-start block (AA-1024 G14, S272). Read-only, stdlib + the gh CLI.

Lesson S258-S266 (lessons.md, family 15): the full-history Secret Scan was red on main three times before anyone
looked, and the other non-blocking guards (CIS nightly random-order integration run, the weekly docs-lint lessons
sweep, the Infra drift and isolation probes) report only in their own run pages. This prints, for each of the 6 repos,
the latest SCHEDULED run of every workflow that ran on a schedule in the last --days days, red runs first, so the
opening status block (skill aa-session step "Trạng thái") shows them; any red run makes the opening checklist red.

    python3 tools/github/guard_runs.py                 # table; exit 1 when a latest scheduled run is red
    python3 tools/github/guard_runs.py --json

Reads use the local `gh` login (no App token; public repos). Exit: 0 all green | 1 a red run | 2 a repo unreadable.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ORG = "AdventureAsia365-Ecosys"
REPOS = ("AA-Ecosys", "AA-CIS-App", "AA-Booking", "AA-Partner", "AA-TripPlanner-Web", "AA-CIS-Infra")
RED = frozenset({"failure", "timed_out", "startup_failure", "action_required"})


def gh_runs(repo: str, run=subprocess.run) -> list[dict] | None:
    """The repo's scheduled runs (newest first), or None when gh fails."""
    r = run(["gh", "api", "-X", "GET", f"repos/{ORG}/{repo}/actions/runs", "-f", "event=schedule", "-f",
             "per_page=100", "--jq", ".workflow_runs"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        return None


def latest_per_workflow(runs: list[dict], since: datetime) -> list[dict]:
    seen: dict[str, dict] = {}
    for run in runs:
        name = run.get("name") or run.get("path") or "?"
        created = run.get("created_at") or ""
        try:
            when = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when < since:
            continue
        if name not in seen or created > seen[name]["created_at"]:
            seen[name] = {"workflow": name, "created_at": created, "status": run.get("status"),
                          "conclusion": run.get("conclusion"), "url": run.get("html_url")}
    return list(seen.values())


def collect(days: int, run=subprocess.run, now: datetime | None = None) -> tuple[list[dict], list[str]]:
    since = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    rows, unreadable = [], []
    for repo in REPOS:
        runs = gh_runs(repo, run)
        if runs is None:
            unreadable.append(repo)
            continue
        for row in latest_per_workflow(runs, since):
            rows.append({"repo": repo, **row})
    rows.sort(key=lambda r: (r["conclusion"] not in RED, r["status"] == "completed", r["repo"], r["workflow"]))
    return rows, unreadable


def label(row: dict) -> str:
    if row["status"] != "completed":
        return row["status"] or "?"
    return row["conclusion"] or "?"


def main(argv: list[str] | None = None, run=subprocess.run, now: datetime | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--days", type=int, default=8, help="only workflows with a scheduled run in this window (8)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows, unreadable = collect(a.days, run, now)
    red = [r for r in rows if r["conclusion"] in RED]
    if a.json:
        print(json.dumps({"rows": rows, "red": len(red), "unreadable": unreadable}, indent=1))
    else:
        print(f"Scheduled guard runs (latest per workflow, last {a.days} days): {len(red)} red of {len(rows)}")
        for r in rows:
            mark = "RED " if r["conclusion"] in RED else "    "
            print(f"{mark}{r['repo']:<20} {r['workflow'][:44]:<44} {label(r):<12} {r['created_at'][:16]}  {r['url']}")
        for repo in unreadable:
            print(f"??? {repo}: gh could not list its runs (login, rate limit)")
    if red:
        return 1
    return 2 if unreadable else 0


if __name__ == "__main__":
    sys.exit(main())
