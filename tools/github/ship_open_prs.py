#!/usr/bin/env python3
"""Push lane branches and open their PRs from a lane workflow journal (AA-1032, skill aa-session parallel-lanes).

    tools/github/ship_open_prs.py wf_85982363-f71                  # a run id: its journal.jsonl is looked up
    tools/github/ship_open_prs.py <path>/journal.jsonl --only Infra --extra-refs AA-1032
    tools/github/ship_open_prs.py wf_85982363-f71 --dry-run        # validate and print, push nothing

The journal of a tools/workflows/lane.js run holds one {"type": "result", "result": {...}} line per agent. The PRs
are the prs[] of the LAST result that carries prs[] (the fix pass replaces the implement pass), in merge order, with
the lane's title and body as given. A final result with ready=false is refused unless --allow-not-ready.

Every PR is checked before anything is pushed (all or nothing): the worktree exists, the branch exists locally and is
ahead of origin/<base>, no rebase in progress and no modified tracked file (lesson S254), the title is a conventional
one without an issue id (Linear reads "fix: AA-123" as a closing phrase, lesson S246), the body has "Refs AA-<n>" and
no Fixes/Closes phrase, and the repo's pre-push hook is installed when it ships one (core.hooksPath=.githooks, so the
push runs the repo's checks; AA-1024 l22). Files the branch deletes are listed as a warning (merge gate refuses them).

Then for each PR: push through the aa-agent App (no force), open the PR (or reuse an open PR of that branch), check
the author is the App, print the URL and the lane's live_steps. --extra-refs adds issue ids to the Refs line; the
Claude Code attribution line is appended when the body lacks it.

Exit: 0 all opened | 2 usage / journal | 4 a PR failed validation, push or create. Orchestrator only. No secrets.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from ship_common import (
    AS_APP,
    ROOT,
    Runner,
    ShipError,
    default_branch,
    log,
    normalize_repo,
    slug,
)

ATTRIBUTION = "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
TITLE_RE = re.compile(r"^(feat|fix|chore|refactor|docs|test|perf|ci|build)(\([^)]+\))?!?: \S.*$")
ISSUE_RE = re.compile(r"\bAA-\d+\b")
CLOSING_RE = re.compile(r"\b(fix(es|ed)?|close[sd]?|resolve[sd]?)\b[:\s]+AA-\d+", re.IGNORECASE)
REFS_RE = re.compile(r"^Refs\s+AA-\d+.*$", re.MULTILINE)
JOURNAL_GLOBS = (
    "~/.claude/projects/*/*/subagents/workflows/{id}/journal.jsonl",
    "~/.claude/projects/*/subagents/workflows/{id}/journal.jsonl",
)


def find_journal(arg: str) -> Path:
    p = Path(arg).expanduser()
    if p.is_file():
        return p
    if re.fullmatch(r"wf_[A-Za-z0-9_-]+", arg):
        hits: list[str] = []
        for g in JOURNAL_GLOBS:
            hits.extend(glob.glob(os.path.expanduser(g.format(id=arg))))
        if hits:
            return Path(max(hits, key=os.path.getmtime))
    raise ShipError(f"no journal at '{arg}' (a journal.jsonl path or a workflow run id wf_...)", 2)


def load_prs(path: Path) -> tuple[list[dict], dict]:
    """prs[] of the last result that carries prs[], plus that result (for ready / blocked_reason)."""
    last: dict | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        res = rec.get("result") if rec.get("type") == "result" else None
        if isinstance(res, dict) and isinstance(res.get("prs"), list) and res["prs"]:
            last = res
    if last is None:
        raise ShipError(f"{path}: no result with prs[]", 2)
    return last["prs"], last


def add_refs(body: str, extra: list[str]) -> str:
    if not extra:
        return body
    m = REFS_RE.search(body)
    if not m:
        return body.rstrip() + "\n\nRefs " + ", ".join(extra) + "\n"
    have = set(ISSUE_RE.findall(m.group(0)))
    add = [x for x in extra if x not in have]
    if not add:
        return body
    return body[: m.end()] + ", " + ", ".join(add) + body[m.end():]


def with_attribution(body: str) -> str:
    if "Generated with [Claude Code]" in body:
        return body
    return body.rstrip() + "\n\n" + ATTRIBUTION + "\n"


def validate(runner: Runner, p: dict, stacked_on: frozenset[str] = frozenset()) -> tuple[list[str], list[str]]:
    """Return (problems, warnings) for one prs[] entry. `stacked_on`: branches of earlier PRs in the same list; a PR
    based on one of them is compared with the local branch (it reaches origin when the earlier PR is pushed)."""
    problems: list[str] = []
    warnings: list[str] = []
    try:
        repo = normalize_repo(str(p.get("repo", "")))
    except ShipError as e:
        return [str(e)], []
    wt, br = str(p.get("worktree", "")), str(p.get("branch", ""))
    base = str(p.get("base") or default_branch(repo))
    title, body = str(p.get("pr_title", "")), str(p.get("pr_body", ""))
    if not TITLE_RE.match(title):
        problems.append(f"title is not 'feat|fix|chore|refactor|docs|...: description': {title!r}")
    if ISSUE_RE.search(title):
        problems.append(f"title carries an issue id (Linear may close it on merge): {title!r}")
    if not REFS_RE.search(body):
        problems.append("body has no 'Refs AA-<n>' line")
    if CLOSING_RE.search(body):
        problems.append("body has a closing phrase (Fixes/Closes/Resolves AA-<n>): use Refs")
    if not os.path.isdir(wt):
        problems.append(f"no worktree at {wt}")
        return problems, warnings

    def git(*args: str):
        return runner.run(["git", "-C", wt, *args], timeout=120)

    if not git("rev-parse", "--verify", "--quiet", f"refs/heads/{br}").ok:
        problems.append(f"no local branch {br} in {wt}")
        return problems, warnings
    for name in ("rebase-merge", "rebase-apply"):
        r = git("rev-parse", "--git-path", name)
        gp = r.out.strip()
        if gp and not os.path.isabs(gp):
            gp = os.path.join(wt, gp)
        if gp and os.path.exists(gp):
            problems.append(f"{wt}: a rebase is in progress")
    if git("status", "--porcelain", "--untracked-files=no").out.strip():
        problems.append(f"{wt}: tracked files are modified (commit or stash first)")
    # AA-1024 l22 (G6): the repo's pre-push hook (CI checks of the diff, rebase refusal, CIS integration stamp) runs
    # inside the push only when the clone points git at .githooks; one install covers every worktree of the clone.
    hooks = git("config", "--get", "core.hooksPath").out.strip()
    if os.path.isfile(os.path.join(wt, ".githooks", "pre-push")) and hooks != ".githooks":
        problems.append(f"{wt}: the pre-push hook is not installed (core.hooksPath={hooks or 'unset'}): run "
                        f"scripts/install-hooks.sh in that repo once (shared by every worktree of the clone)")
    git("fetch", "-q", "origin")
    ref = f"origin/{base}"
    if base in stacked_on and not git("rev-parse", "--verify", "--quiet", f"refs/remotes/{ref}").ok:
        ref = base
    r = git("rev-list", "--count", f"{ref}..{br}")
    if not r.ok:
        problems.append(f"cannot compare {br} with {ref}: {r.last_line()}")
    elif int(r.out.strip() or "0") < 1:
        problems.append(f"{br} has no commit ahead of {ref}")
    d = git("diff", "--name-only", "--diff-filter=D", f"{ref}...{br}")
    gone = [x for x in d.out.splitlines() if x.strip()]
    if gone:
        warnings.append(f"{br} deletes {len(gone)} file(s): {', '.join(gone[:8])}")
    return problems, warnings


def open_one(runner: Runner, p: dict, extra_refs: list[str], draft: bool) -> str:
    repo = normalize_repo(str(p["repo"]))
    wt, br = str(p["worktree"]), str(p["branch"])
    base = str(p.get("base") or default_branch(repo))
    tag = f"{repo} {br}"
    r = runner.run([AS_APP, "--repos", repo, "--", "git", "-C", wt, "push", "-q", "-u", "origin", br], timeout=300)
    if not r.ok:
        raise ShipError(f"{tag}: push failed (no force push here): {r.last_line()}", 4)
    existing = runner.run(["gh", "pr", "list", "-R", slug(repo), "--head", br, "--state", "open", "--json",
                           "number,url", "--jq", ".[0].url // empty"], timeout=60)
    url = existing.out.strip() if existing.ok else ""
    if url:
        log(f"{tag}: pushed to the open PR {url}")
    else:
        body = with_attribution(add_refs(str(p.get("pr_body", "")), extra_refs))
        tmpdir = ROOT / ".tmp-session"
        tmpdir.mkdir(parents=True, exist_ok=True)
        fd, fname = tempfile.mkstemp(prefix="pr-body-", suffix=".md", dir=str(tmpdir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(body)
            argv = [AS_APP, "--repos", repo, "--", "gh", "pr", "create", "--repo", slug(repo), "--base", base,
                    "--head", br, "--title", str(p["pr_title"]), "--body-file", fname]
            if draft:
                argv.append("--draft")
            r = runner.run(argv, timeout=120)
        finally:
            os.unlink(fname)
        m = re.search(r"https://github\.com/\S+/pull/\d+", r.out + "\n" + r.err)
        if not r.ok or not m:
            raise ShipError(f"{tag}: gh pr create failed: {r.last_line()}", 4)
        url = m.group(0)
        log(f"{tag}: opened {url}")
    a = runner.run(["gh", "pr", "view", url, "--json", "author", "--jq", ".author.login"], timeout=60)
    who = a.out.strip()
    if a.ok and "aa-agent" not in who:
        log(f"WARN {url}: author is '{who}', expected the aa-agent App")
    for step in p.get("live_steps") or []:
        log(f"    live: {step}")
    return url


def main(argv: list[str] | None = None, runner: Runner | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("journal", help="journal.jsonl path or workflow run id (wf_...)")
    ap.add_argument("--only", default="", help="open only the PRs whose repo name contains this text")
    ap.add_argument("--extra-refs", default="", help="comma-separated issue ids to add to the Refs line")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="validate and print, push nothing")
    ap.add_argument("--allow-not-ready", action="store_true", help="open PRs of a result with ready=false")
    a = ap.parse_args(argv)
    runner = runner or Runner()
    try:
        path = find_journal(a.journal)
        prs, res = load_prs(path)
        log(f"journal {path}: {len(prs)} PR(s), ready={res.get('ready')}")
        if res.get("ready") is False and not a.allow_not_ready:
            raise ShipError(f"the lane result is not ready: {res.get('blocked_reason') or 'no reason given'} "
                            f"(--allow-not-ready to open anyway)", 4)
        extra = [x.strip() for x in a.extra_refs.split(",") if x.strip()]
        for x in extra:
            if not re.fullmatch(r"AA-\d+", x):
                raise ShipError(f"--extra-refs: '{x}' is not AA-<n>", 2)
        chosen = [p for p in prs if a.only.lower() in str(p.get("repo", "")).lower()]
        if not chosen:
            raise ShipError(f"no PR matches --only '{a.only}'", 2)
        bad = False
        earlier: set[str] = set()
        for p in chosen:
            problems, warnings = validate(runner, p, frozenset(earlier))
            earlier.add(str(p.get("branch", "")))
            tag = f"{p.get('repo')} {p.get('branch')}"
            for w in warnings:
                log(f"WARN {tag}: {w}")
            for x in problems:
                log(f"REFUSED {tag}: {x}")
            bad = bad or bool(problems)
            log(f"{'ok' if not problems else 'bad'} {tag}: {p.get('pr_title')}")
        if bad:
            return 4
        if a.dry_run:
            return 0
        for p in chosen:
            open_one(runner, p, extra, a.draft)
        return 0
    except ShipError as e:
        log(f"ERROR {e}")
        return e.code


if __name__ == "__main__":
    sys.exit(main())
