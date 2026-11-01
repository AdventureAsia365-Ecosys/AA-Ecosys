#!/usr/bin/env python3
"""Merge a stack of branches from one worktree, bottom first (AA-1032, skill aa-ship references/merge-trains.md).

    tools/github/ship_train.py AA-Partner /home/nghiep/projects/AA-Ecosys/.tmp-session/wt/s263-crm-w6 \\
        feat/aa-958-migration:175 feat/aa-958-code:176
    tools/github/ship_train.py --dry-run cis <worktree> feat/a:1230:1 feat/b:1231   # print the plan only

Each item is '<branch>:<pr>[:<own>]' ('<branch> <pr> [<own>]' quoted also works). <own> = how many commits on top of
the branch below are the branch's own. When left out it is counted ONCE, before anything moves:
`git rev-list --count <branch below>..<branch>` (the first branch: `origin/<default>..<branch>`).

For every branch, in order, stopping at the first failure:
 1. fetch; refuse when a rebase is in progress, tracked files are modified, or origin/<branch> has commits the local
    branch lacks (a bot push would be lost);
 2. `git rebase --onto origin/<default> <branch>~<own> <branch>`: only the branch's own commits move, so the commits of
    the branch below, already squash-merged, are not replayed (lesson S243); conflict -> abort and stop;
 3. retarget the PR to the default branch and mark it ready when needed, then push through the aa-agent App with
    --force-with-lease=<branch>:<the remote SHA read at step 1>;
 4. ship_merge gate on the pushed head (EVERY check green, not only required ones) and merge: merge queue for CIS,
    Booking, Partner; squash for the others.

Exit: 0 every branch merged | 1 rebase conflict / git refusal | 2 usage | 3 red check | 4 refused or merge failed |
5 checks pending at --timeout. Orchestrator only (push and merge). Holds no secrets.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass

import ship_merge
from ship_common import (
    AS_APP,
    Runner,
    ShipError,
    default_branch,
    log,
    normalize_repo,
    pr_view,
    slug,
    warn_mfa,
)


@dataclass
class Item:
    branch: str
    pr: int
    own: int | None = None


def parse_item(text: str) -> Item:
    parts = [p for p in re.split(r"[:\s]+", text.strip()) if p]
    if len(parts) not in (2, 3) or not parts[1].isdigit() or (len(parts) == 3 and not parts[2].isdigit()):
        raise ShipError(f"cannot read '{text}': use '<branch>:<pr>[:<own commits>]'", 2)
    return Item(parts[0], int(parts[1]), int(parts[2]) if len(parts) == 3 else None)


class Git:
    def __init__(self, runner: Runner, wt: str):
        self.runner, self.wt = runner, wt

    def __call__(self, *args: str, timeout: float = 120):
        return self.runner.run(["git", "-C", self.wt, *args], timeout=timeout)

    def out(self, *args: str) -> str:
        r = self(*args)
        if not r.ok:
            raise ShipError(f"git {' '.join(args)} failed: {r.last_line()}", 1)
        return r.out.strip()

    def rev(self, ref: str) -> str | None:
        r = self("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        return r.out.strip() if r.ok and r.out.strip() else None

    def is_ancestor(self, a: str, b: str) -> bool:
        return self("merge-base", "--is-ancestor", a, b).rc == 0

    def count(self, rng: str) -> int:
        return int(self.out("rev-list", "--count", rng))


def preflight_worktree(git: Git) -> None:
    """Refuse while a rebase is in progress or tracked files are modified (lesson S254: a push mid-rebase ships the
    old branch)."""
    for name in ("rebase-merge", "rebase-apply"):
        p = git.out("rev-parse", "--git-path", name)
        if not os.path.isabs(p):
            p = os.path.join(git.wt, p)
        if os.path.exists(p):
            raise ShipError(f"{git.wt}: a rebase is in progress ({name}); finish or abort it first", 1)
    dirty = git.out("status", "--porcelain", "--untracked-files=no")
    if dirty:
        raise ShipError(f"{git.wt}: tracked files are modified:\n{dirty}", 1)


def plan(git: Git, base: str, items: list[Item]) -> list[Item]:
    """Fill in <own> for every item from the stack as it is now, before any rebase."""
    out: list[Item] = []
    below = f"origin/{base}"
    for it in items:
        if git.rev(it.branch) is None:
            raise ShipError(f"no local branch '{it.branch}' in {git.wt}", 1)
        own = it.own
        if own is None:
            if below != f"origin/{base}" and not git.is_ancestor(below, it.branch):
                raise ShipError(f"'{it.branch}' is not stacked on '{below}': give its own commit count "
                                f"('{it.branch}:{it.pr}:<n>')", 2)
            own = git.count(f"{below}..{it.branch}")
        if own < 1:
            raise ShipError(f"'{it.branch}' has no commit of its own on top of '{below}'", 2)
        out.append(Item(it.branch, it.pr, own))
        below = it.branch
    return out


def ship_branch(runner: Runner, git: Git, repo: str, it: Item, **merge_kw) -> str:
    base = default_branch(repo)
    tag = f"{repo}#{it.pr}"
    git.out("fetch", "-q", "origin")
    preflight_worktree(git)
    remote = git.rev(f"origin/{it.branch}")
    if remote is None:
        raise ShipError(f"{tag}: origin/{it.branch} does not exist (open the PR first)", 1)
    if not git.is_ancestor(remote, it.branch):
        raise ShipError(f"{tag}: origin/{it.branch} has commits the local branch lacks (a bot or a reviewer "
                        f"pushed?): merge them locally first", 1)
    git.out("checkout", "-q", it.branch)
    r = git("rebase", "--onto", f"origin/{base}", f"{it.branch}~{it.own}", it.branch, timeout=300)
    if not r.ok:
        git("rebase", "--abort")
        raise ShipError(f"{tag}: rebase conflict on origin/{base}; resolve by hand (skill resolving-merge-conflicts)"
                        f"\n{r.last_line()}", 1)
    n = git.count(f"origin/{base}..{it.branch}")
    if n != it.own:
        raise ShipError(f"{tag}: after the rebase {n} commits sit on origin/{base}, expected {it.own}", 1)
    head = git.out("rev-parse", it.branch)
    log(f"{tag}: {it.branch} = {it.own} commit(s) on origin/{base}, head {head[:8]}")

    pr = pr_view(runner, repo, it.pr)
    if pr.get("state") != "OPEN":
        raise ShipError(f"{tag}: PR is {pr.get('state')}", 4)
    if pr.get("baseRefName") != base:
        r = runner.run([AS_APP, "--repos", repo, "--", "gh", "pr", "edit", str(it.pr), "-R", slug(repo),
                        "--base", base], timeout=120)
        if not r.ok:
            raise ShipError(f"{tag}: cannot retarget to {base}: {r.last_line()}", 4)
        log(f"{tag}: retargeted {pr.get('baseRefName')} -> {base}")
    if pr.get("isDraft"):
        r = runner.run([AS_APP, "--repos", repo, "--", "gh", "pr", "ready", str(it.pr), "-R", slug(repo)],
                       timeout=120)
        if not r.ok:
            raise ShipError(f"{tag}: cannot mark ready: {r.last_line()}", 4)
    if head != remote:
        r = runner.run([AS_APP, "--repos", repo, "--", "git", "-C", git.wt, "push", "-q",
                        f"--force-with-lease={it.branch}:{remote}", "origin", it.branch], timeout=300)
        if not r.ok:
            raise ShipError(f"{tag}: push refused: {r.last_line()}", 1)
        log(f"{tag}: pushed {remote[:8]} -> {head[:8]}")
    else:
        log(f"{tag}: already on origin/{base}, nothing to push")
    return ship_merge.merge_one(runner, repo, it.pr, expect_head=head, **merge_kw)


def main(argv: list[str] | None = None, runner: Runner | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo")
    ap.add_argument("worktree")
    ap.add_argument("items", nargs="+", help="<branch>:<pr>[:<own commits>], bottom of the stack first")
    ap.add_argument("--dry-run", action="store_true", help="print the plan (own commit counts), change nothing")
    ap.add_argument("--allow-deletes", action="store_true")
    ap.add_argument("--timeout", type=float, default=2400)
    ap.add_argument("--interval", type=float, default=60)
    ap.add_argument("--queue-timeout", type=float, default=5400)
    a = ap.parse_args(argv)
    runner = runner or Runner()
    try:
        repo = normalize_repo(a.repo)
        if not os.path.isdir(a.worktree):
            raise ShipError(f"no worktree at {a.worktree}", 2)
        git = Git(runner, a.worktree)
        git.out("fetch", "-q", "origin")
        preflight_worktree(git)
        items = plan(git, default_branch(repo), [parse_item(x) for x in a.items])
        for it in items:
            log(f"plan {repo}#{it.pr}: rebase --onto origin/{default_branch(repo)} {it.branch}~{it.own} {it.branch}")
        if a.dry_run:
            return 0
        warn_mfa(runner, need_minutes=60)
        for it in items:
            sha = ship_branch(runner, git, repo, it, timeout=a.timeout, interval=max(30.0, a.interval),
                              allow_deletes=a.allow_deletes, queue_timeout=a.queue_timeout)
            log(f"TRAIN {repo}#{it.pr} merged {sha[:8]}")
        log(f"TRAIN done: {len(items)} PR(s) merged")
        return 0
    except ShipError as e:
        log(f"TRAIN STOPPED: {e}")
        return e.code


if __name__ == "__main__":
    sys.exit(main())
