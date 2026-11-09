#!/usr/bin/env python3
"""Merge one or more PRs, refusing any PR with a red check (AA-1032, skill aa-ship).

    tools/github/ship_merge.py 'AA-CIS-App 1230' AA-CIS-Infra#585 root#438 tp#208
    tools/github/ship_merge.py --check-only cis#1230          # gate only: report, merge nothing
    tools/github/ship_merge.py --serial booking#140 booking#141   # one after the other, stop at the first failure

Targets: '<Repo> <pr>' (quoted), '<Repo>#<pr>', or loose '<Repo> <pr>' argv pairs; repo aliases root, cis, booking,
partner/crm, tp, infra.

Gate (every target): wait for the PR's checks, then merge only when EVERY check is green (SUCCESS, NEUTRAL or
SKIPPED), required or not — S263 #1225 merged through the queue with a red non-required "Migration preflight". A
green read is not final: a job with `needs:` gets its check only when it is queued and a workflow_run workflow starts
later, so the gate reads again after SETTLE_SECONDS, requires the same set of checks still green, and requires every
workflow run on the head commit (`gh run list --commit`) to be finished and green. It also
refuses a draft PR, a PR that does not target the default branch (a stacked PR still based on its parent), a DIRTY PR,
and a PR that deletes files unless --allow-deletes (a squash from a stale base shows up as deletions, lessons
S250/S253). The gate does not see job tables or waves: aa-ship §2 still applies before backend merges.

Merge: AA-CIS-App, AA-Booking, AA-Partner through the merge queue (mergeq.sh). When mergeq.sh exits 4 "not in the
queue" and the PR is not merged, the merge-queue entries and the PR's merge_group runs are read before failing: while
either still holds the PR, the tool waits (S273: exit 4 while the PR's own group CI ran). TripPlanner, Infra and the
root repo squash through the aa-agent App with --match-head-commit (the head that was gated). Queue repos run in
parallel (one worker per PR, lesson S257); PRs of one non-queue repo run one after the other. --serial keeps the given
order for all.

Exit: 0 all merged (or green with --check-only) | 2 usage / gh error | 3 a check or workflow run red, or none
reported | 4 refused (draft, base, DIRTY, deletions, closed) or merge failed | 5 checks still pending at --timeout.
Orchestrator only: .claude/hooks/subagent-guardrails.sh refuses any subagent command that names this tool (the merge
runs inside it, out of the hook's sight). Holds no secrets.
"""

from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from ship_common import (
    AS_APP,
    GATE_ENV,
    MERGEQ,
    QUEUE_REPOS,
    Runner,
    ShipError,
    classify_checks,
    classify_runs,
    default_branch,
    fmt_list,
    gh_json,
    log,
    parse_targets,
    pr_view,
    removed_files,
    runs_on_commit,
    slug,
    warn_mfa,
)

NO_CHECKS_GRACE = 180  # seconds to wait for a first check to register on a fresh head
# A green read is confirmed by a second one this much later: checks of `needs:` jobs and workflow_run workflows are
# created late (the failure mode of S263 #1225: a red non-required check after the merge).
SETTLE_SECONDS = 25


def gate(runner: Runner, repo: str, n: int, *, timeout: float = 2400, interval: float = 60,
         allow_deletes: bool = False, expect_head: str | None = None) -> dict:
    """Wait for the PR's checks; return the PR (state MERGED is returned as is) or raise ShipError."""
    t0 = runner.now()
    tag = f"{repo}#{n}"
    seen_green: frozenset | None = None  # the green set of the previous read, confirmed by the next one
    while True:
        pr = pr_view(runner, repo, n)
        elapsed = runner.now() - t0
        if pr.get("state") == "MERGED":
            return pr
        if pr.get("state") == "CLOSED":
            raise ShipError(f"{tag} REFUSED: the PR is closed", 4)
        if expect_head and pr.get("headRefOid") != expect_head:
            if elapsed >= timeout:
                raise ShipError(f"{tag} GitHub still shows head {str(pr.get('headRefOid'))[:8]}, "
                                f"not the pushed {expect_head[:8]}", 5)
            runner.sleep(min(interval, 30))
            continue
        s = classify_checks(pr.get("statusCheckRollup"))
        if s.red:
            raise ShipError(f"{tag} REFUSED: red checks: {fmt_list(s.red)}", 3)
        if s.total == 0:
            if elapsed >= NO_CHECKS_GRACE:
                raise ShipError(f"{tag} REFUSED: no check reported on head {str(pr.get('headRefOid'))[:8]}", 3)
            runner.sleep(min(interval, 30))
            continue
        if s.pending:
            if elapsed >= timeout:
                raise ShipError(f"{tag} checks still pending after {int(timeout)}s: {fmt_list(s.pending)}", 5)
            seen_green = None
            runner.sleep(interval)
            continue
        green = frozenset(s.green)
        if green != seen_green:
            # First all-green read, or the set changed since the last one: read again before trusting it.
            seen_green = green
            runner.sleep(SETTLE_SECONDS)
            continue
        head = str(pr.get("headRefOid") or "")
        rs = classify_runs(runs_on_commit(runner, repo, head))
        if rs.red:
            raise ShipError(f"{tag} REFUSED: red workflow runs on head {head[:8]}: {fmt_list(rs.red)}", 3)
        if rs.pending:
            if elapsed >= timeout:
                raise ShipError(f"{tag} workflow runs still pending after {int(timeout)}s: {fmt_list(rs.pending)}", 5)
            seen_green = None
            runner.sleep(interval)
            continue
        break
    if pr.get("isDraft"):
        raise ShipError(f"{tag} REFUSED: draft PR (gh pr ready first)", 4)
    base = default_branch(repo)
    if pr.get("baseRefName") != base:
        raise ShipError(f"{tag} REFUSED: base is '{pr.get('baseRefName')}', not {base} "
                        f"(stacked PR: retarget or use ship_train.py)", 4)
    if pr.get("mergeStateStatus") == "DIRTY":
        raise ShipError(f"{tag} REFUSED: DIRTY (conflicts with {base})", 4)
    if not allow_deletes:
        gone = removed_files(runner, repo, n)
        if gone:
            raise ShipError(f"{tag} REFUSED: the PR deletes {len(gone)} file(s): {fmt_list(gone, 8)} "
                            f"(check the base; --allow-deletes when intended)", 4)
    log(f"{tag}: all {len(s.green)} checks green, head {str(pr.get('headRefOid'))[:8]}")
    return pr


def _merged_sha(runner: Runner, repo: str, n: int, tries: int = 4) -> str | None:
    """GitHub can report OPEN for a few seconds after the queue merged (lesson S255): read again before failing."""
    for i in range(tries):
        pr = pr_view(runner, repo, n)
        if pr.get("state") == "MERGED":
            return ((pr.get("mergeCommit") or {}).get("oid")) or ""
        if i < tries - 1:
            runner.sleep(10)
    return None


# mergeq.sh's "left the queue" line (exit 4). S273: printed while the PR's own merge_group CI was still running with
# several CIS PRs queued at once; isInMergeQueue read false for a moment while the queue rebuilt its groups.
LEFT_QUEUE = "not in the queue"
QUEUE_ENTRIES = ("query($o:String!,$r:String!,$b:String!){repository(owner:$o,name:$r){mergeQueue(branch:$b)"
                 "{entries(first:100){nodes{state position pullRequest{number}}}}}}")


def queue_hold(runner: Runner, repo: str, n: int) -> str:
    """What still holds the PR in the merge queue: its queue entry, or a merge_group run of its group branch
    (gh-readonly-queue/<base>/pr-<n>-<sha>) that has not finished. '' when neither (it has really left). A read that
    fails counts as nothing found (the caller then reports the failure as before)."""
    base = default_branch(repo)
    owner, name = slug(repo).split("/", 1)
    try:
        data = gh_json(runner, ["gh", "api", "graphql", "-f", f"query={QUEUE_ENTRIES}", "-f", f"o={owner}",
                                "-f", f"r={name}", "-f", f"b={base}"])
    except ShipError as e:
        log(f"{repo}#{n}: merge queue entries unreadable ({e})")
        data = None
    queue = (((data or {}).get("data") or {}).get("repository") or {}).get("mergeQueue") if isinstance(data, dict) \
        else None
    for node in (((queue or {}).get("entries") or {}).get("nodes") or []):
        if ((node or {}).get("pullRequest") or {}).get("number") == n:
            return f"queue entry {node.get('state') or '?'} at position {node.get('position')}"
    try:
        runs = gh_json(runner, ["gh", "run", "list", "-R", slug(repo), "--event", "merge_group", "-L", "50",
                                "--json", "databaseId,name,headBranch,status,conclusion"])
    except ShipError as e:
        log(f"{repo}#{n}: merge_group runs unreadable ({e})")
        runs = []
    prefix = f"gh-readonly-queue/{base}/pr-{n}-"
    live = [r for r in (runs if isinstance(runs, list) else [])
            if str(r.get("headBranch") or "").startswith(prefix) and (r.get("status") or "").lower() != "completed"]
    if live:
        return "merge_group run " + ", ".join(f"{r.get('name')} {r.get('status')}" for r in live[:3])
    return ""


def _wait_out_queue(runner: Runner, repo: str, n: int, *, timeout: float, interval: float) -> str | None:
    """mergeq.sh said the PR left the queue: trust that only once queue_hold() finds nothing, then read the PR state
    again. Return the merge SHA, or None when it really left (or is still held at the timeout)."""
    tag = f"{repo}#{n}"
    t0 = runner.now()
    while True:
        hold = queue_hold(runner, repo, n)
        if not hold:
            return _merged_sha(runner, repo, n)
        if runner.now() - t0 >= timeout:
            log(f"{tag}: still held in the merge queue after {int(timeout)}s ({hold})")
            return None
        log(f"{tag}: mergeq.sh reported '{LEFT_QUEUE}', but {hold}: waiting")
        runner.sleep(interval)
        pr = pr_view(runner, repo, n)
        if pr.get("state") == "MERGED":
            return ((pr.get("mergeCommit") or {}).get("oid")) or ""


def merge_one(runner: Runner, repo: str, n: int, *, check_only: bool = False, timeout: float = 2400,
              interval: float = 60, allow_deletes: bool = False, expect_head: str | None = None,
              queue_timeout: float = 5400) -> str:
    """Gate and merge one PR. Return the merge SHA ('' with --check-only); raise ShipError on refusal/failure."""
    tag = f"{repo}#{n}"
    pr = gate(runner, repo, n, timeout=timeout, interval=interval, allow_deletes=allow_deletes,
              expect_head=expect_head)
    if pr.get("state") == "MERGED":
        sha = ((pr.get("mergeCommit") or {}).get("oid")) or ""
        log(f"{tag}: already merged {sha[:8]}")
        return sha
    if check_only:
        log(f"{tag}: green, not merged (--check-only)")
        return ""
    os.environ[GATE_ENV] = "ship_merge"  # as-app.sh lets a gated `gh pr merge` through (AA-1024); inherited below
    if repo in QUEUE_REPOS:
        r = runner.stream([MERGEQ, repo, str(n)], prefix=f"{tag}: ", timeout=queue_timeout)
        why = f"mergeq.sh exit {r.rc}: {r.last_line()}"
    else:
        head = str(pr.get("headRefOid") or "")
        r = runner.run([AS_APP, "--repos", repo, "--", "gh", "pr", "merge", str(n), "-R", slug(repo), "--squash",
                        "--match-head-commit", head], timeout=180)
        why = f"gh pr merge exit {r.rc}: {r.last_line()}"
    sha = _merged_sha(runner, repo, n)
    if sha is None and repo in QUEUE_REPOS and r.rc == 4 and LEFT_QUEUE in r.out:
        sha = _wait_out_queue(runner, repo, n, timeout=queue_timeout, interval=interval)
    if sha is None:
        raise ShipError(f"{tag} NOT MERGED ({why})", 4)
    log(f"{tag}: MERGED {sha[:8]}")
    return sha


def run_targets(runner: Runner, targets: list[tuple[str, int]], *, serial: bool = False, **kw) -> int:
    """Merge every target; return the worst exit code (0 when all merged)."""
    if serial:
        groups = [targets]
    else:
        groups = []
        by_repo: dict[str, list] = {}
        for t in targets:
            if t[0] in QUEUE_REPOS:
                groups.append([t])
            else:
                by_repo.setdefault(t[0], []).append(t)
        groups.extend(by_repo.values())

    results: dict[tuple[str, int], tuple[int, str]] = {}

    def work(group: list[tuple[str, int]]) -> None:
        for i, (repo, n) in enumerate(group):
            try:
                sha = merge_one(runner, repo, n, **kw)
                results[(repo, n)] = (0, f"MERGED {sha[:8]}" if sha else "green (not merged)")
            except ShipError as e:
                log(f"ERROR {e}")
                results[(repo, n)] = (e.code, str(e))
                for rest in group[i + 1:]:
                    results[rest] = (4, f"{rest[0]}#{rest[1]} skipped: an earlier PR in the same run failed")
                return

    if len(groups) == 1:
        work(groups[0])
    else:
        with ThreadPoolExecutor(max_workers=len(groups)) as pool:
            list(pool.map(work, groups))

    log("SUMMARY")
    worst = 0
    for t in targets:
        code, msg = results.get(t, (4, "not run"))
        log(f"  {t[0]}#{t[1]}: {'ok' if code == 0 else f'exit {code}'} - {msg}")
        worst = max(worst, code)
    return worst


def main(argv: list[str] | None = None, runner: Runner | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("targets", nargs="+", help="'<Repo> <pr>' or '<Repo>#<pr>'")
    ap.add_argument("--check-only", action="store_true", help="gate and report, merge nothing")
    ap.add_argument("--serial", action="store_true", help="one PR after the other in the given order")
    ap.add_argument("--allow-deletes", action="store_true", help="accept a PR that deletes files")
    ap.add_argument("--timeout", type=float, default=2400, help="max seconds to wait for checks (default 2400)")
    ap.add_argument("--interval", type=float, default=60, help="seconds between check reads (min 30)")
    ap.add_argument("--queue-timeout", type=float, default=5400, help="max seconds for mergeq.sh (default 5400)")
    a = ap.parse_args(argv)
    runner = runner or Runner()
    try:
        targets = parse_targets(a.targets)
    except ShipError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return e.code
    if not a.check_only:
        warn_mfa(runner)
    return run_targets(runner, targets, serial=a.serial, check_only=a.check_only, timeout=a.timeout,
                       interval=max(30.0, a.interval), allow_deletes=a.allow_deletes, queue_timeout=a.queue_timeout)


if __name__ == "__main__":
    sys.exit(main())
