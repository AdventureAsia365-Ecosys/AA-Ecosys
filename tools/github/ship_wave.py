#!/usr/bin/env python3
"""Ship a whole wave of PRs: independent PRs in parallel, only declared chains in order (AA-1024 G1, skill aa-ship).

    tools/github/ship_wave.py cis#1350 cis#1352 booking#201 root#601 --wait-deploy
    tools/github/ship_wave.py 'cis#1349>apply:cis/383,cis/384' 'cis#1351@after=cis/384' cis#1350 --wait-deploy
    tools/github/ship_wave.py --dry-run 'crm#240>apply:crm/41' 'crm#241@after=crm/41' tp#230

Targets ('<Repo>#<pr>', repo aliases as ship_merge.py):
  <Repo>#<pr>                              independent: gated and merged at once, one worker per PR
  <Repo>#<pr>>apply:<owner>/<NNN>[,...]    a migration-only PR: merge, then its migrations go onto Dev through
                                           ship_copy_apply.py (Infra copy PR -> merge -> apply -> readiness)
  <Repo>#<pr>@after=<owner>/<NNN>[,...]    held until those migrations are applied (MIG-4 code PR)

Why (lessons S257, S271): a hand-written script that waits for one PR (and its deploy) before it queues the next ran a
7-PR wave in ~4 h instead of ~1 h. Here every PR that does not wait for a migration is gated and merged at the same
time (ship_merge.merge_one: EVERY check green, settle re-read, DIRTY / draft / base / deletion refusals; merge queue for
CIS, Booking, Partner; squash with --match-head-commit for the others, one PR at a time per non-queue repo). The
migrations of one owner are applied in number order, one after the other, as one batch (Migration Sync / Apply keep
owner order); a held PR starts the moment its migrations are registered. A failure stops only what depends on it.
--wait-deploy waits ONCE per deployed app (CIS, Booking, Partner) at the end, until its health endpoint reports a
git_sha that contains every merge of the wave in that repo; never once per PR.

Exit: 0 all merged (and applied / deployed) | 2 usage, or a hold on a migration nothing in the wave applies and Dev
has not registered | 3 a red check | 4 refused, merge failed, apply failed, or skipped because a dependency failed |
5 timed out (checks, queue or deploy). Orchestrator only: .claude/hooks/subagent-guardrails.sh refuses any subagent
command naming this tool (the merges run inside it). Holds no secrets.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import ship_copy_apply
import ship_merge
from ship_common import QUEUE_REPOS, Runner, ShipError, gh_json, log, parse_target, slug, warn_mfa

# Deployed apps: health endpoint that reports the running git_sha (as tools/github/train-lib.sh waitdeploy).
DEPLOY_URL = {
    "AA-CIS-App": "https://api-cis.lumiguides.it.com/health/ready",
    "AA-Booking": "https://api-booking.lumiguides.it.com/booking/health",
    "AA-Partner": "https://partner-dev.lumiguides.it.com/crm/health",
}

Key = tuple[str, str]  # (owner, NNN)


@dataclass
class Item:
    repo: str
    n: int
    applies: list[Key] = field(default_factory=list)
    after: list[Key] = field(default_factory=list)

    @property
    def tag(self) -> str:
        return f"{self.repo}#{self.n}"


def parse_key(text: str) -> Key:
    owner, _, num = text.strip().partition("/")
    if not num:
        raise ShipError(f"cannot read migration '{text}': use <owner>/<NNN> (cis/383, crm/041, booking/038)", 2)
    num = num.strip()
    if num.isdigit():
        num = num.zfill(3)  # crm/41 -> 041 (file names carry three digits)
    o, nnn, _ = ship_copy_apply.parse_target(owner, num)
    return o, nnn


def parse_item(text: str) -> Item:
    m = re.fullmatch(r"\s*(.+?)((?:\s*(?:>apply:|@after=)[^>@]+)*)\s*", text)
    if not m:
        raise ShipError(f"cannot read target '{text}'", 2)
    repo, n = parse_target(m.group(1))
    item = Item(repo, n)
    for kind, keys in re.findall(r"(>apply:|@after=)([^>@]+)", m.group(2)):
        parsed = [parse_key(k) for k in keys.split(",") if k.strip()]
        (item.applies if kind == ">apply:" else item.after).extend(parsed)
    return item


def parse_items(args: list[str]) -> list[Item]:
    items = [parse_item(a) for a in args]
    seen: dict[tuple[str, int], str] = {}
    produced: dict[Key, str] = {}
    for it in items:
        if (it.repo, it.n) in seen:
            raise ShipError(f"{it.tag} is listed twice", 2)
        seen[(it.repo, it.n)] = it.tag
        for k in it.applies:
            if k in produced:
                raise ShipError(f"{k[0]}/{k[1]} is applied by both {produced[k]} and {it.tag}", 2)
            produced[k] = it.tag
        if set(it.applies) & set(it.after):
            raise ShipError(f"{it.tag} cannot apply and wait for the same migration", 2)
    return items


def plan_lines(items: list[Item]) -> list[str]:
    now = [it.tag for it in items if not it.after]
    lines = [f"at once ({len(now)}, in parallel): {', '.join(now) or '-'}"]
    by_owner: dict[str, list[tuple[str, str]]] = {}
    for it in items:
        for o, nnn in it.applies:
            by_owner.setdefault(o, []).append((nnn, it.tag))
    for o, keys in sorted(by_owner.items()):
        chain = " -> ".join(f"{o}/{nnn} (after {tag} merges)" for nnn, tag in sorted(keys, key=lambda x: int(x[0])))
        lines.append(f"apply {o} in order: {chain}")
    for it in items:
        if it.after:
            lines.append(f"hold {it.tag} until applied: {', '.join(f'{o}/{n}' for o, n in it.after)}")
    return lines


class Wave:
    """Runs the items: merge workers, one apply worker per owner, held PRs released by their migrations."""

    def __init__(self, runner: Runner, items: list[Item], *, merge_kw: dict, apply_fn, fetch, check_only: bool):
        self.runner = runner
        self.items = items
        self.merge_kw = merge_kw
        self.apply_fn = apply_fn
        self.fetch = fetch
        self.check_only = check_only
        self.results: dict[str, tuple[int, str]] = {}
        self.merged_sha: dict[str, str] = {}
        self.merge_done = {it.tag: threading.Event() for it in items}
        keys = {k for it in items for k in it.applies + it.after}
        self.applied = {k: threading.Event() for k in keys}
        self.apply_ok: dict[Key, bool] = {}
        self.repo_locks = {r: threading.Lock() for r in {it.repo for it in items} if r not in QUEUE_REPOS}
        self.lock = threading.Lock()

    def _set(self, tag: str, code: int, msg: str) -> None:
        with self.lock:
            self.results[tag] = (code, msg)

    def merge(self, it: Item) -> None:
        try:
            if it.after and not self.check_only:  # --check-only gates a held PR at once (nothing gets applied)
                for k in it.after:
                    self.applied[k].wait()
                bad = [f"{o}/{n}" for o, n in it.after if not self.apply_ok.get((o, n))]
                if bad:
                    self._set(it.tag, 4, f"skipped: migration(s) {', '.join(bad)} not applied")
                    return
                log(f"{it.tag}: migrations {', '.join(f'{o}/{n}' for o, n in it.after)} applied, gating")
            lock = self.repo_locks.get(it.repo)
            if lock:
                with lock:
                    sha = ship_merge.merge_one(self.runner, it.repo, it.n, check_only=self.check_only,
                                               **self.merge_kw)
            else:
                sha = ship_merge.merge_one(self.runner, it.repo, it.n, check_only=self.check_only, **self.merge_kw)
            self.merged_sha[it.tag] = sha
            self._set(it.tag, 0, f"MERGED {sha[:8]}" if sha else "green (not merged)")
        except ShipError as e:
            log(f"ERROR {e}")
            self._set(it.tag, e.code, str(e))
        except Exception as e:  # noqa: BLE001 - one worker's crash must not hang the waiters
            log(f"ERROR {it.tag}: {type(e).__name__}: {e}")
            self._set(it.tag, 4, f"{type(e).__name__}: {e}")
        finally:
            self.merge_done[it.tag].set()

    def apply_owner(self, owner: str, keys: list[tuple[str, Item]]) -> None:
        """Apply one owner's migrations in number order; a failure fails every higher one (owner order)."""
        failed = None
        for nnn, it in sorted(keys, key=lambda x: int(x[0])):
            key = (owner, nnn)
            try:
                if failed:
                    log(f"apply {owner}/{nnn}: skipped ({failed})")
                    self.apply_ok[key] = False
                    continue
                self.merge_done[it.tag].wait()
                code = self.results.get(it.tag, (4, ""))[0]
                if code != 0 or self.check_only:
                    failed = f"{it.tag} not merged" if code else "--check-only"
                    log(f"apply {owner}/{nnn}: skipped ({failed})")
                    self.apply_ok[key] = False
                    continue
                log(f"apply {owner}/{nnn}: {it.tag} merged, copy + apply")
                rc = self.apply_fn(owner, nnn)
                self.apply_ok[key] = rc == 0
                if rc != 0:
                    failed = f"{owner}/{nnn} apply exit {rc}"
                    self._set(it.tag, 4, f"merged {self.merged_sha.get(it.tag, '')[:8]} but {failed}")
                    log(f"ERROR apply {owner}/{nnn}: exit {rc}")
            except Exception as e:  # noqa: BLE001 - a crash must release the held PRs
                failed = f"{owner}/{nnn}: {type(e).__name__}: {e}"
                self.apply_ok[key] = False
                self._set(it.tag, 4, failed)
            finally:
                self.applied[key].set()

    def run(self) -> None:
        by_owner: dict[str, list[tuple[str, Item]]] = {}
        for it in self.items:
            for o, nnn in it.applies:
                by_owner.setdefault(o, []).append((nnn, it))
        # Keys held on but applied by nothing in the wave were checked at start (already registered on Dev).
        for k, ev in self.applied.items():
            if not any(k in it.applies for it in self.items):
                self.apply_ok[k] = True
                ev.set()
        workers = len(self.items) + len(by_owner)
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = [pool.submit(self.merge, it) for it in self.items]
            futures += [pool.submit(self.apply_owner, o, keys) for o, keys in by_owner.items()]
            for f in futures:
                f.result()


def check_holds(items: list[Item], fetch) -> None:
    """A hold on a migration the wave does not apply must already be registered on Dev."""
    produced = {k for it in items for k in it.applies}
    for it in items:
        for o, nnn in it.after:
            if (o, nnn) in produced:
                continue
            if o not in ship_copy_apply.READY_URL or not ship_copy_apply.ready_now(o, nnn, fetch):
                raise ShipError(f"{it.tag} waits for {o}/{nnn}, which no PR in this wave applies and Dev has not "
                                f"registered: add its migration PR with '>apply:{o}/{nnn}'", 2)


def contains(runner: Runner, repo: str, base: str, head: str) -> bool:
    """Does commit `head` contain commit `base` (identical or ahead)?"""
    if head.startswith(base) or base.startswith(head):
        return True
    data = gh_json(runner, ["gh", "api", f"repos/{slug(repo)}/compare/{base}...{head}", "--jq", "{status: .status}"])
    return isinstance(data, dict) and data.get("status") in ("identical", "ahead")


def wait_deploys(runner: Runner, wave: Wave, fetch, *, timeout: float, interval: float = 30) -> int:
    """Once per deployed app: wait until its running git_sha contains every merge of the wave in that repo."""
    worst = 0
    by_repo: dict[str, list[str]] = {}
    for it in wave.items:
        sha = wave.merged_sha.get(it.tag)
        if sha and it.repo in DEPLOY_URL and wave.results.get(it.tag, (1,))[0] == 0:
            by_repo.setdefault(it.repo, []).append(sha)
    for repo, shas in sorted(by_repo.items()):
        url = DEPLOY_URL[repo]
        t0 = runner.now()
        while True:
            try:
                running = str((fetch(url) or {}).get("git_sha") or "")
            except Exception as e:  # noqa: BLE001 - report and retry until the timeout
                running = ""
                log(f"deploy {repo}: {url} unreachable ({type(e).__name__})")
            if running and all(contains(runner, repo, s, running) for s in shas):
                log(f"deploy {repo}: live {running[:8]} contains {len(shas)} merge(s) of the wave")
                break
            if runner.now() - t0 >= timeout:
                log(f"ERROR deploy {repo}: still {running[:8] or 'unknown'} after {int(timeout)}s, not "
                    f"{', '.join(s[:8] for s in shas)} (a docs-only merge does not deploy: check the Deploy Dev run)")
                worst = max(worst, 5)
                break
            runner.sleep(interval)
    return worst


def main(argv: list[str] | None = None, runner: Runner | None = None, apply_fn=None,
         fetch=ship_copy_apply.fetch_ready) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("targets", nargs="+", help="<Repo>#<pr>[>apply:<owner>/<NNN>,...][@after=<owner>/<NNN>,...]")
    ap.add_argument("--wait-deploy", action="store_true", help="at the end, wait once per deployed app")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, touch nothing")
    ap.add_argument("--check-only", action="store_true", help="gate every PR, merge and apply nothing")
    ap.add_argument("--allow-deletes", action="store_true", help="accept PRs that delete files")
    ap.add_argument("--timeout", type=float, default=2400, help="max seconds to wait for a PR's checks")
    ap.add_argument("--interval", type=float, default=60, help="seconds between check reads (min 30)")
    ap.add_argument("--queue-timeout", type=float, default=5400, help="max seconds in the merge queue")
    ap.add_argument("--deploy-timeout", type=float, default=1800, help="max seconds per app for --wait-deploy")
    a = ap.parse_args(argv)
    runner = runner or Runner()
    try:
        items = parse_items(a.targets)
    except ShipError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return e.code
    log("PLAN")
    for line in plan_lines(items):
        log(f"  {line}")
    if a.dry_run:
        return 0
    try:
        check_holds(items, fetch)
    except ShipError as e:
        log(f"ERROR {e}")
        return e.code
    if not a.check_only:
        warn_mfa(runner)
    if apply_fn is None:
        def apply_fn(owner: str, nnn: str) -> int:
            return ship_copy_apply.main([owner, nnn], runner=runner, fetch=fetch)
    wave = Wave(runner, items, apply_fn=apply_fn, fetch=fetch, check_only=a.check_only,
                merge_kw={"timeout": a.timeout, "interval": max(30.0, a.interval), "allow_deletes": a.allow_deletes,
                          "queue_timeout": a.queue_timeout})
    wave.run()
    worst = 0
    if a.wait_deploy and not a.check_only:
        worst = wait_deploys(runner, wave, fetch, timeout=a.deploy_timeout)
    log("SUMMARY")
    for it in items:
        code, msg = wave.results.get(it.tag, (4, "not run"))
        log(f"  {it.tag}: {'ok' if code == 0 else f'exit {code}'} - {msg}")
        worst = max(worst, code)
    for k in sorted(wave.apply_ok):
        if any(k in it.applies for it in items):
            log(f"  apply {k[0]}/{k[1]}: {'applied' if wave.apply_ok[k] else 'NOT applied'}")
    log(json.dumps({"exit": worst}))
    return worst


if __name__ == "__main__":
    sys.exit(main())
