#!/usr/bin/env python3
"""Scheduled guard runs status for the session-start block (AA-1024 G14, S272). Read-only, stdlib + the gh CLI.

Lesson S258-S266 (lessons.md, family 15): the full-history Secret Scan was red on main three times before anyone
looked, and the other non-blocking guards (CIS nightly random-order integration run, the weekly docs-lint lessons
sweep, the Infra drift and isolation probes) report only in their own run pages. This prints, for each of the 6 repos,
the latest SCHEDULED run of every workflow that ran on a schedule in the last --days days, red runs first, so the
opening status block (skill aa-session step "Trạng thái") shows them; any red run makes the opening checklist red.

A red scheduled run is superseded when a LATER green workflow_dispatch or push run of the same workflow ran on the
repo's default branch (S294: Catalogue and Image Scan were reported red after a green hand dispatch had fixed them):
the row reads "superseded (green <event> <time>)" and does not count red. A failed lookup leaves the row red.

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
# Runs that can supersede a red scheduled run: a hand dispatch or a push to the default branch, finished green.
SUPERSEDE_EVENTS = frozenset({"workflow_dispatch", "push"})


def default_branch(repo: str) -> str:
    return "master" if repo == "AA-Ecosys" else "main"


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
                          "conclusion": run.get("conclusion"), "url": run.get("html_url"),
                          "workflow_id": run.get("workflow_id")}
    return list(seen.values())


def later_green(repo: str, row: dict, run=subprocess.run) -> dict | None:
    """The newest green workflow_dispatch / push run of the row's workflow on the default branch created after the
    row's scheduled run, or None (also when the lookup fails: the row then stays red)."""
    wid = row.get("workflow_id")
    if not wid:
        return None
    branch = default_branch(repo)
    r = run(["gh", "api", "-X", "GET", f"repos/{ORG}/{repo}/actions/workflows/{wid}/runs", "-f", f"branch={branch}",
             "-f", "per_page=50", "--jq", ".workflow_runs"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    try:
        runs = json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        return None
    best = None
    for x in runs or []:
        if (x.get("event") in SUPERSEDE_EVENTS and x.get("status") == "completed" and x.get("conclusion") == "success"
                and (x.get("head_branch") or branch) == branch and (x.get("created_at") or "") > row["created_at"]
                and (best is None or x["created_at"] > best["created_at"])):
            best = {"event": x.get("event"), "created_at": x.get("created_at"), "url": x.get("html_url")}
    return best


def is_red(row: dict) -> bool:
    return row.get("conclusion") in RED and not row.get("superseded")


def collect(days: int, run=subprocess.run, now: datetime | None = None) -> tuple[list[dict], list[str]]:
    since = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    rows, unreadable = [], []
    for repo in REPOS:
        runs = gh_runs(repo, run)
        if runs is None:
            unreadable.append(repo)
            continue
        for row in latest_per_workflow(runs, since):
            if row["conclusion"] in RED:
                newer = later_green(repo, row, run)
                if newer:
                    row["superseded"] = newer
            rows.append({"repo": repo, **row})
    rows.sort(key=lambda r: (not is_red(r), r["status"] == "completed", r["repo"], r["workflow"]))
    return rows, unreadable


def label(row: dict) -> str:
    sup = row.get("superseded")
    if sup:
        return f"superseded (green {sup['event']} {(sup.get('created_at') or '')[:16]})"
    if row["status"] != "completed":
        return row["status"] or "?"
    return row["conclusion"] or "?"


def main(argv: list[str] | None = None, run=subprocess.run, now: datetime | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--days", type=int, default=8, help="only workflows with a scheduled run in this window (8)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows, unreadable = collect(a.days, run, now)
    red = [r for r in rows if is_red(r)]
    if a.json:
        print(json.dumps({"rows": rows, "red": len(red), "unreadable": unreadable}, indent=1))
    else:
        print(f"Scheduled guard runs (latest per workflow, last {a.days} days): {len(red)} red of {len(rows)}")
        for r in rows:
            mark = "RED " if is_red(r) else "    "
            print(f"{mark}{r['repo']:<20} {r['workflow'][:44]:<44} {label(r):<12} {r['created_at'][:16]}  {r['url']}")
        for repo in unreadable:
            print(f"??? {repo}: gh could not list its runs (login, rate limit)")
    if red:
        return 1
    return 2 if unreadable else 0


if __name__ == "__main__":
    sys.exit(main())
