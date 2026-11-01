#!/usr/bin/env python3
"""Merge gate of the Plan sync bot PR (S263, AA-896 lane plan-sync): are the named root checks green on the PR head?

The root repo's master has no branch protection and no ruleset, so `gh pr checks --required` has nothing to wait for
(it exits non-zero with "no required checks reported"). Like the DB Schema Dump root PR (AA-CIS-Infra
db/schema_dump_automerge.py `checks`), .github/workflows/plan-sync.yml names the checks itself and polls
GET /repos/{owner}/{repo}/commits/{head sha}/check-runs, feeding the JSON to this script:

    gh api "repos/$ROOT_REPO/commits/$HEAD/check-runs?per_page=100" > checks.json
    python3 tools/linear/bot_pr_checks.py --required "Docs lint,gitleaks" < checks.json

Exit 0 = every run complete, none red, each required check present with a success run; 1 = a red run, a required
check that only skipped, or no required name given; 2 = still running or a required check not reported yet (poll
again; the caller's time limit turns a lasting 2 into "stays open"). The last line printed is the verdict. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys

GREEN = {"success", "skipped", "neutral"}


def checks_verdict(runs: list[dict], required: list[str]) -> tuple[int, str]:
    if not required:
        return 1, "no required check named: refusing to merge on an empty set"
    pending = sorted(r["name"] for r in runs if r.get("status") != "completed")
    if pending:
        return 2, f"pending: {', '.join(pending)}"
    red = sorted(r["name"] for r in runs if (r.get("conclusion") or "") not in GREEN)
    if red:
        return 1, f"red check(s): {', '.join(red)}"
    names = {r["name"] for r in runs}
    missing = [n for n in required if n not in names]
    if missing:
        # A new head can take a few seconds to show its check runs: pending, not a failure.
        return 2, f"required check(s) not reported yet: {', '.join(missing)}"
    # A required check that only ran as "skipped" or "neutral" did not judge this head (e.g. a job `if:`): no merge.
    passed = {r["name"] for r in runs if r.get("conclusion") == "success"}
    not_passed = sorted(set(required) - passed)
    if not_passed:
        return 1, f"required check(s) did not pass (skipped/neutral only): {', '.join(not_passed)}"
    return 0, f"green: {', '.join(sorted(set(required)))}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--required", default="", help="comma-separated check run names that must be green")
    args = ap.parse_args(argv)
    runs = json.load(sys.stdin).get("check_runs", [])
    required = [n.strip() for n in args.required.split(",") if n.strip()]
    rc, verdict = checks_verdict(runs, required)
    print(verdict)
    return rc


if __name__ == "__main__":
    sys.exit(main())
