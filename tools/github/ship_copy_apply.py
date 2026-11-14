#!/usr/bin/env python3
"""Get one migration onto Dev: its Infra bot copy PR, then DB Migrate on THAT file (AA-1032, skill aa-ship).

    tools/github/ship_copy_apply.py cis 330                     # copy PR -> merge -> DB Migrate apply -> readiness
    tools/github/ship_copy_apply.py crm crm-038 --mode check     # report only
    tools/github/ship_copy_apply.py booking 035_x.sql --no-copy  # file already on Infra main: dispatch only

Owners: cis, booking (bk), crm, tripplanner (tp); roles (Infra-native, no copy PR) with --no-copy.
Target: NNN, <prefix>-NNN or the file name.

1. Copy: find bot/migration-copy/<owner>-<NNN> in ANY state. An OPEN PR is gated like ship_merge (every check green)
   and squash-merged through the aa-agent App; a MERGED one is fine; CLOSED ones are ignored. No PR yet -> wait
   (--copy-timeout); the file already on Infra main without a PR is fine too.
2. Class from the file header on Infra main: `-- migrate: expand` -> Migration Apply applies it after the copy merges,
   so no dispatch (unless --dispatch-expand); `-- migrate: destructive` -> refused unless --allow-destructive
   (DRY RUN process first, aa-cis-schema references/destructive-ops.md); anything else is contract -> dispatch.
3. Dispatch DB Migrate and follow ITS OWN run: under a local lock, remember the dispatch runs that exist, dispatch,
   then take the one new run whose title is "DB Migrate <mode> <owner>/<file>" (Infra run-name). Before Infra has the
   run-name, the one new run since the dispatch is taken; two new runs -> refuse to guess (S263: reading "the latest
   run" reported another file's run).
4. Wait for that run (status polls, no `gh run watch`, which can hang: lesson S252), print its conclusion and the key
   log lines (job log API: lesson S243/S254).
5. Read the owner app's /health/ready: status, schema_version and whether the key is in registered_keys.
Dev Migration Apply can apply the file itself (expand, and contract when every job table is idle: AA-1032 part 1):
an apply whose key is already registered is not dispatched. A red run passes only when ITS OWN log says the apply
lock was held (exit code 17: nothing ran) and the key shows up within 5 minutes; any other red run is exit 1 even
when the key is registered (exit 9 registers the file and still needs hand cleanup).

Owner order (what Migration Sync and Migration Apply keep): before it merges a copy PR, and before an apply dispatch,
the tool refuses (exit 4) while an OPEN bot/migration-copy/<owner>-<lower NNN> PR exists, or while the owner's
/health/ready lacks the key of a lower file on Infra main (above keys_baseline) or cannot be read. Applying 331 while
330 waits makes 330 out-of-order for auto-apply (AA-920: 297 applied after 299). --allow-out-of-order bypasses it.

An apply refused because a job table is busy or a rerun wave is open (the run's log: `exit code: 7`, "apply refused: a
job table is busy", "MIGRATE ERROR: refusing apply — busy") prints "apply held: job tables busy (<table: kinds>)" and
exits 7: nothing ran, the file goes on once idle (S281: a tour trash/restore queued a platform recompute of 16-52 min).

Exit: 0 applied / checked and (apply) the key is registered | 1 run not green or key not registered |
2 usage, dispatch failed or run not found | 3 copy PR red | 4 refused (destructive, closed, out of order) |
5 timed out | 7 apply held: a job table busy or a rerun wave open (nothing ran; re-dispatch once idle). dbmig.sh calls this with --no-copy. Orchestrator only: .claude/hooks/subagent-guardrails.sh refuses any
subagent command that names this tool or dbmig.sh (the merge and the dispatch run inside, out of the hook's sight).
Holds no secrets.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import json
import re
import sys
import urllib.request
from contextlib import contextmanager
from datetime import datetime

import ship_merge
from ship_common import AS_APP, ROOT, Runner, ShipError, gh_json, log, warn_mfa

INFRA = "AA-CIS-Infra"
INFRA_SLUG = f"AdventureAsia365-Ecosys/{INFRA}"
WORKFLOW = "db-migrate.yml"
OWNERS = {"cis": "cis", "booking": "booking", "bk": "booking", "crm": "crm", "tripplanner": "tripplanner",
          "tp": "tripplanner", "roles": "roles"}
KEY_PREFIX = {"cis": "", "booking": "bk-", "crm": "crm-", "tripplanner": "tp-", "roles": "rl-"}
READY_URL = {
    "cis": "https://api-cis.lumiguides.it.com/health/ready",
    "booking": "https://api-booking.lumiguides.it.com/booking/health/ready",
    "crm": "https://partner-dev.lumiguides.it.com/crm/health/ready",
}
LOG_PATTERN = re.compile(r"ran as|master login|busy|idle|wave|applied|already|refus|NOTICE|error|exit \d+|"
                         r"^MIGRATE|^SCRIPT|registered", re.IGNORECASE)
LOCK_FILE = ROOT / ".tmp-session" / ".db-migrate-dispatch.lock"
# Unregistered files at or below this number are legacy (ran by hand before self-registration; Infra
# db/run_migration.py AUTO_APPLY_FLOOR). The readiness body's keys_baseline wins when present.
LEGACY_FLOOR = {"cis": 263}
# The db-migrate.yml lines that say the apply lock was held and nothing ran (exit 17). Anchored at the line start:
# the job log also prints the step's script, where the same words follow `echo "` or `if [`.
LOCK_HELD = re.compile(r"^(exit code: 17\b|(##\[error\]|::error::)the apply lock is held)")
EXIT_LINE = re.compile(r"^exit code: \S+")
# S281: the apply was refused because a job table is busy or a rerun wave is open (Infra db/run_migration.py exit 7,
# DM-11.4): nothing ran, the file can be applied once every job table is idle. Anchored like LOCK_HELD (the job log
# also prints the step script, where the same words follow `echo "` or `if [`).
BUSY_REFUSED = re.compile(r"^(exit code: 7\b|(##\[error\]|::error::)apply refused: a job table is busy|"
                          r"(MIGRATE )?ERROR: (refusing apply|idle-gate refused)\b.*\bbusy:)")
# "MIGRATE busy: shared.job running=1 queued=0 due=0 kinds=[recompute:running=1]" (BusyState.line()), also the
# unreadable / open-wave forms.
BUSY_LINE = re.compile(r"^(?:MIGRATE )?busy: (\S+) (.*)$")
BUSY_KINDS = re.compile(r"kinds=\[([^\]]*)\]")
# Exit code of an apply held by busy job tables (nothing ran; re-dispatch once idle). Distinct from 1 (a real
# failure) so a wave can stay resumable; same number as DB Migrate's own refusal.
EXIT_HELD = 7


def parse_target(owner: str, target: str) -> tuple[str, str, str | None]:
    o = OWNERS.get(owner.lower())
    if not o:
        raise ShipError(f"unknown owner '{owner}' (cis, booking, crm, tripplanner; roles with --no-copy)", 2)
    t = target.strip().split("/")[-1]
    m = re.fullmatch(r"(?:(?:bk|crm|tp|rl)-)?(\d{3,4})(_[A-Za-z0-9_]+\.sql)?", t)
    if not m:
        raise ShipError(f"cannot read migration '{target}': use NNN, <prefix>-NNN or NNN_name.sql", 2)
    return o, m.group(1), (t if m.group(2) else None)


def ready_key(owner: str, num: str) -> str:
    return f"{KEY_PREFIX[owner]}{num}"


def run_title(mode: str, path: str) -> str:
    """The Infra db-migrate.yml run-name for one migration (keep in sync with that workflow)."""
    return f"DB Migrate {mode} {path}"


# --- copy PR -----------------------------------------------------------------------------------------------------


def find_copy_pr(runner: Runner, owner: str, num: str) -> dict | None:
    head = f"bot/migration-copy/{owner}-{num}"
    prs = gh_json(runner, ["gh", "pr", "list", "-R", INFRA_SLUG, "--head", head, "--state", "all", "--limit", "20",
                           "--json", "number,state,labels,mergedAt,createdAt,headRefName"])
    prs = [p for p in (prs or []) if p.get("headRefName") == head]
    open_ = [p for p in prs if p.get("state") == "OPEN"]
    if open_:
        return max(open_, key=lambda p: p.get("createdAt") or "")
    merged = [p for p in prs if p.get("state") == "MERGED"]
    if merged:
        return max(merged, key=lambda p: p.get("mergedAt") or "")
    return None


def main_files(runner: Runner, owner: str) -> list[str]:
    r = runner.run(["gh", "api", f"repos/{INFRA_SLUG}/contents/db/migrations/{owner}?ref=main",
                    "--jq", ".[].name"], timeout=60)
    if not r.ok:
        raise ShipError(f"cannot list db/migrations/{owner} on Infra main: {r.last_line()}", 2)
    return [x.strip() for x in r.out.splitlines() if x.strip()]


def file_on_main(runner: Runner, owner: str, num: str, name: str | None) -> str | None:
    names = main_files(runner, owner)
    hits = [x for x in names if x.startswith(f"{num}_") and x.endswith(".sql")]
    if name:
        return name if name in hits else None
    if len(hits) > 1:
        raise ShipError(f"several files {owner}/{num}_*.sql on Infra main: {', '.join(hits)}", 2)
    return hits[0] if hits else None


def open_lower_copy_prs(runner: Runner, owner: str, num: str) -> list[str]:
    """Open copy PRs of the same owner with a lower number (Migration Sync merges them in owner order)."""
    prefix = f"bot/migration-copy/{owner}-"
    prs = gh_json(runner, ["gh", "pr", "list", "-R", INFRA_SLUG, "--state", "open", "--limit", "100",
                           "--json", "number,state,headRefName"])
    out = []
    for p in prs or []:
        m = re.fullmatch(re.escape(prefix) + r"(\d{3,4})", str(p.get("headRefName") or ""))
        if m and p.get("state", "OPEN") == "OPEN" and int(m.group(1)) < int(num):
            out.append(f"#{p['number']} ({owner}-{m.group(1)})")
    return sorted(out)


def unapplied_below(runner: Runner, owner: str, num: str, fetch) -> list[str]:
    """Keys of the owner's files on Infra main below NNN (above the legacy baseline) that Dev has not registered.
    Raises (exit 4) when the readiness body cannot tell; [] for an owner without a readiness endpoint."""
    url = READY_URL.get(owner)
    if not url:
        return []
    try:
        d = fetch(url)
    except Exception as e:  # noqa: BLE001 - fail closed: the order cannot be checked
        raise ShipError(f"cannot read {url} ({type(e).__name__}) to check that every {owner} file below {num} is "
                        f"applied; --allow-out-of-order to go on anyway", 4) from e
    keys = d.get("registered_keys")
    if not isinstance(keys, list):
        raise ShipError(f"{url} has no registered_keys (status={d.get('status')}): cannot check that every {owner} "
                        f"file below {num} is applied; --allow-out-of-order to go on anyway", 4)
    floor = int(d.get("keys_baseline") or LEGACY_FLOOR.get(owner, 0))
    lower = set()
    for x in main_files(runner, owner):
        m = re.fullmatch(r"(\d{3,4})_[A-Za-z0-9_]+\.sql", x)
        if m and floor < int(m.group(1)) < int(num):
            lower.add(m.group(1))
    return [ready_key(owner, n) for n in sorted(lower, key=int) if ready_key(owner, n) not in keys]


def check_order(runner: Runner, owner: str, num: str, *, fetch=None, applied: bool) -> None:
    """Refuse (exit 4) while a lower copy PR is open, or (applied=True) a lower file is not registered on Dev."""
    opened = open_lower_copy_prs(runner, owner, num)
    missing = unapplied_below(runner, owner, num, fetch or fetch_ready) if applied else []
    why = []
    if opened:
        why.append(f"lower copy PRs still open: {', '.join(opened)}")
    if missing:
        why.append(f"lower files not registered on Dev: {', '.join(missing)}")
    if why:
        raise ShipError(f"{owner}-{num} out of order: {'; '.join(why)}. Land them first (Migration Sync/Apply keep "
                        f"owner order; applying past a gap leaves the lower file out-of-order), or rerun with "
                        f"--allow-out-of-order", 4)


def ensure_copy(runner: Runner, owner: str, num: str, name: str | None, *, timeout: float, interval: float,
                gate_timeout: float, in_order: bool = True) -> str:
    """Wait for / merge the copy PR; return the file name on Infra main."""
    t0 = runner.now()
    while True:
        pr = find_copy_pr(runner, owner, num)
        if pr and pr.get("state") == "OPEN":
            if in_order:
                check_order(runner, owner, num, applied=False)
            labels = ",".join(x.get("name", "") for x in pr.get("labels") or [])
            log(f"copy {owner}-{num}: PR #{pr['number']} open [{labels}], gating")
            ship_merge.merge_one(runner, INFRA, int(pr["number"]), timeout=gate_timeout, interval=interval)
        elif pr:
            log(f"copy {owner}-{num}: PR #{pr['number']} already merged")
        found = file_on_main(runner, owner, num, name)
        if found:
            return found
        if runner.now() - t0 >= timeout:
            what = f"PR #{pr['number']} merged but" if pr else "no copy PR and"
            raise ShipError(f"copy {owner}-{num}: {what} no file on Infra main after {int(timeout)}s", 5)
        runner.sleep(interval)


def file_class(runner: Runner, path: str) -> str:
    """expand | destructive | contract, from the leading comment block of the file on Infra main."""
    data = gh_json(runner, ["gh", "api", f"repos/{INFRA_SLUG}/contents/db/migrations/{path}?ref=main"])
    text = base64.b64decode((data or {}).get("content", "")).decode("utf-8", "replace")
    directives: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if not s.startswith("--"):
            break
        m = re.match(r"--\s*migrate:\s*(.+)", s)
        if m:
            directives.append(m.group(1).strip().lower())
    if any(d.startswith("destructive") for d in directives):
        return "destructive"
    if any(d.startswith("expand") for d in directives):
        return "expand"
    return "contract"


# --- dispatch + own run ------------------------------------------------------------------------------------------


@contextmanager
def dispatch_lock():
    """One identification at a time from this machine, so two parallel calls never take each other's run."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_FILE, "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _runs(runner: Runner) -> list[dict]:
    data = gh_json(runner, ["gh", "run", "list", "-R", INFRA_SLUG, "-w", WORKFLOW, "-e", "workflow_dispatch",
                            "-L", "30", "--json", "databaseId,createdAt,displayTitle,status,url"])
    return list(data or [])


def _ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def pick_own_run(before: set[int], runs: list[dict], since: float, title: str) -> dict | None:
    """The run this dispatch created, or None while it has not appeared. Raises when it cannot tell."""
    new = [r for r in runs if int(r["databaseId"]) not in before and _ts(r.get("createdAt") or "1970-01-01T00:00:00Z")
           >= since]
    titled = [r for r in new if r.get("displayTitle") == title]
    if len(titled) == 1:
        return titled[0]
    if len(titled) > 1:
        raise ShipError(f"{len(titled)} new runs titled '{title}': {[r['databaseId'] for r in titled]}; "
                        f"read them by hand", 2)
    generic = [r for r in new if not str(r.get("displayTitle", "")).startswith("DB Migrate ")
               or r.get("displayTitle") == "DB Migrate (shared RDS)"]
    if len(generic) == 1:
        return generic[0]
    if len(generic) > 1:
        raise ShipError(f"{len(generic)} new untitled DB Migrate runs {[r['databaseId'] for r in generic]}: "
                        f"cannot tell which one is ours; read them by hand", 2)
    return None


def dispatch(runner: Runner, path: str, mode: str, *, appear_timeout: float = 150) -> dict:
    title = run_title(mode, path)
    with dispatch_lock():
        before = {int(r["databaseId"]) for r in _runs(runner)}
        since = runner.now() - 300  # slack for a skewed WSL clock; the 'before' set is what tells runs apart
        r = runner.run([AS_APP, "--repos", INFRA, "--", "gh", "workflow", "run", WORKFLOW, "-R", INFRA_SLUG, "--ref",
                        "main", "-f", f"migration={path}", "-f", "environment=dev", "-f", f"mode={mode}"],
                       timeout=120)
        if not r.ok:
            raise ShipError(f"dispatch failed: {r.last_line()}", 2)
        t0 = runner.now()
        while True:
            runner.sleep(5)
            run = pick_own_run(before, _runs(runner), since, title)
            if run:
                log(f"DB Migrate {mode} {path}: run {run['databaseId']} {run.get('url', '')}")
                return run
            if runner.now() - t0 >= appear_timeout:
                raise ShipError(f"the dispatched run did not appear within {int(appear_timeout)}s", 2)


def wait_run(runner: Runner, run_id: int, *, timeout: float, interval: float = 30) -> str:
    t0 = runner.now()
    while True:
        v = gh_json(runner, ["gh", "run", "view", str(run_id), "-R", INFRA_SLUG, "--json", "status,conclusion"])
        if (v or {}).get("status") == "completed":
            return str(v.get("conclusion") or "")
        if runner.now() - t0 >= timeout:
            raise ShipError(f"run {run_id} still {(v or {}).get('status')} after {int(timeout)}s", 5)
        runner.sleep(interval)


def run_log(runner: Runner, run_id: int) -> list[str]:
    """Every log line of the run's jobs, timestamp column dropped and stripped (job log API: lesson S243/S254)."""
    v = gh_json(runner, ["gh", "run", "view", str(run_id), "-R", INFRA_SLUG, "--json", "jobs"])
    out: list[str] = []
    for job in (v or {}).get("jobs") or []:
        r = runner.run(["gh", "api", f"repos/{INFRA_SLUG}/actions/jobs/{job.get('databaseId')}/logs"], timeout=120)
        if r.ok:
            out.extend(re.sub(r"^\S+Z\s", "", line).strip() for line in r.out.splitlines())
    return out


def key_log_lines(lines: list[str], limit: int = 25) -> list[str]:
    out = [x[:260] for x in lines if not x.startswith("##[group") and LOG_PATTERN.search(x)]
    return out[:limit]


def lock_held(lines: list[str]) -> bool:
    """The run's own log says the apply lock was held by another run and nothing ran (exit 17)."""
    return any(LOCK_HELD.match(x) for x in lines)


def busy_refusal(lines: list[str]) -> str | None:
    """None, or what kept the apply out when the run's own log says it was refused for busy job tables (exit 7):
    "shared.job: recompute:running=1; shared.rerun_wave open=1" from the MIGRATE busy lines (the last report wins,
    a re-check repeats them), "busy" when the log names no table."""
    if not any(BUSY_REFUSED.match(x) for x in lines):
        return None
    busy: dict[str, str] = {}
    for x in lines:
        m = BUSY_LINE.match(x)
        if not m:
            continue
        name, rest = m.group(1), m.group(2)
        k = BUSY_KINDS.search(rest)
        busy[name] = k.group(1).strip() if k and k.group(1).strip() else rest.strip()
    return "; ".join(f"{n}: {v}" if v else n for n, v in busy.items()) or "busy"


def exit_line(lines: list[str]) -> str:
    hits = [x for x in lines if EXIT_LINE.match(x)]
    return hits[-1] if hits else "no 'exit code:' line in the run log"


# --- readiness ---------------------------------------------------------------------------------------------------


def fetch_ready(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "aa-ship-tools"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - fixed https URLs
        return json.loads(resp.read().decode("utf-8"))


def ready_now(owner: str, num: str, fetch=None) -> bool:
    """One read, no wait: is the key already in the app's registered_keys?"""
    try:
        d = (fetch or fetch_ready)(READY_URL[owner])
    except Exception:  # noqa: BLE001 - unreachable means "not known", the dispatch goes ahead
        return False
    return ready_key(owner, num) in (d.get("registered_keys") or [])


def check_ready(runner: Runner, owner: str, num: str, *, timeout: float, interval: float = 30,
                fetch=fetch_ready) -> bool | None:
    """True/False = key registered or not after waiting; None = the owner has no readiness endpoint."""
    url = READY_URL.get(owner)
    if not url:
        log(f"ready: {owner} has no readiness endpoint; check docs/architecture/db-schema-reference.md after the "
            f"schema dump PR")
        return None
    key = ready_key(owner, num)
    t0 = runner.now()
    while True:
        try:
            d = fetch(url)
        except Exception as e:  # noqa: BLE001 - report and retry
            d = {"status": f"unreachable ({type(e).__name__})"}
        keys = d.get("registered_keys") or []
        ok = key in keys
        if ok or runner.now() - t0 >= timeout:
            req = f" required_schema={d['required_schema']}" if "required_schema" in d else ""
            log(f"ready {url}: status={d.get('status')} schema_version={d.get('schema_version')}{req} "
                f"key {key} registered={'yes' if ok else 'no'}")
            return ok
        runner.sleep(interval)


# --- main --------------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None, runner: Runner | None = None, fetch=fetch_ready,
         report: dict | None = None) -> int:
    """`report` (optional, the wave passes one): gets "held" = the busy job tables when the exit is EXIT_HELD."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("owner", help="cis | booking | crm | tripplanner")
    ap.add_argument("migration", help="NNN, <prefix>-NNN or the file name")
    ap.add_argument("--mode", choices=("apply", "check"), default="apply")
    ap.add_argument("--no-copy", action="store_true", help="the file is already on Infra main: skip the copy PR")
    ap.add_argument("--no-dispatch", action="store_true", help="stop after the copy PR")
    ap.add_argument("--dispatch-expand", action="store_true", help="dispatch even for an expand file")
    ap.add_argument("--allow-destructive", action="store_true", help="dispatch a destructive file (after DRY RUN)")
    ap.add_argument("--allow-out-of-order", action="store_true",
                    help="merge/apply although a lower file of the owner is not copied or not applied (bypasses the "
                         "Migration Sync / Apply owner order)")
    ap.add_argument("--copy-timeout", type=float, default=1200)
    ap.add_argument("--run-timeout", type=float, default=1500)
    ap.add_argument("--interval", type=float, default=30)
    a = ap.parse_args(argv)
    runner = runner or Runner()
    try:
        owner, num, name = parse_target(a.owner, a.migration)
        warn_mfa(runner)
        if a.no_copy:
            fname = file_on_main(runner, owner, num, name)
            if not fname:
                raise ShipError(f"no file {owner}/{name or num + '_*.sql'} on Infra main", 2)
        else:
            fname = ensure_copy(runner, owner, num, name, timeout=a.copy_timeout, interval=a.interval,
                                gate_timeout=a.run_timeout, in_order=not a.allow_out_of_order)
        path = f"{owner}/{fname}"
        kind = file_class(runner, path)
        log(f"copy {owner}-{num}: {path} on Infra main ({kind})")
        if a.no_dispatch:
            return 0
        explicit = a.no_copy  # dbmig.sh: an explicit dispatch of one file
        if a.mode == "apply" and kind == "destructive" and not (a.allow_destructive or explicit):
            raise ShipError(f"{path} is destructive: follow the DRY RUN process, then rerun with "
                            f"--allow-destructive", 4)
        if a.mode == "apply" and kind == "expand" and not (a.dispatch_expand or explicit):
            log(f"{path}: expand file, Migration Apply applies it after the copy merge; not dispatching")
            ok = check_ready(runner, owner, num, timeout=a.run_timeout, interval=a.interval, fetch=fetch)
            return 0 if ok in (True, None) else 1
        if a.mode == "apply" and READY_URL.get(owner) and ready_now(owner, num, fetch):
            # Dev Migration Apply may have applied it already (expand, or contract when idle: AA-1032 part 1).
            log(f"{path}: key {ready_key(owner, num)} already registered; not dispatching")
            check_ready(runner, owner, num, timeout=0, fetch=fetch)
            return 0
        if a.mode == "apply" and not a.allow_out_of_order:
            check_order(runner, owner, num, fetch=fetch, applied=True)
        elif a.mode == "apply":
            log(f"WARN {path}: --allow-out-of-order, owner order not checked")
        run = dispatch(runner, path, a.mode)
        rid = int(run["databaseId"])
        conclusion = wait_run(runner, rid, timeout=a.run_timeout, interval=a.interval)
        log(f"DBMIG {a.mode} {path} run={rid} conclusion={conclusion}")
        lines = run_log(runner, rid)
        for line in key_log_lines(lines):
            log(f"  {line}")
        if conclusion != "success":
            log(f"run {rid} {conclusion}: {exit_line(lines)}")
            if a.mode == "apply" and READY_URL.get(owner) and lock_held(lines):
                # Exit 17: another run (Migration Apply) held the apply lock, nothing ran here; it may be applying
                # this very file.
                if check_ready(runner, owner, num, timeout=300, interval=a.interval, fetch=fetch):
                    log(f"WARN run {rid} found the apply lock held (exit 17, nothing ran), and the key is "
                        f"registered: applied by the run that held the lock")
                    return 0
            held = busy_refusal(lines) if a.mode == "apply" else None
            if held:
                # S281: a tour state change queued a platform recompute (16-52 min) and the apply refused (DM-11.4).
                # Nothing ran: the file goes on once every job table is idle (Migration Apply, or a re-dispatch).
                log(f"apply held: job tables busy ({held}); nothing ran, {path} is not applied. Re-dispatch once "
                    f"idle (ship_wave --wait-idle N does it), or let Migration Apply take it (exit {EXIT_HELD})")
                if report is not None:
                    report["held"] = held
                return EXIT_HELD
            return 1
        if a.mode == "check":
            return 0
        ok = check_ready(runner, owner, num, timeout=120, interval=a.interval, fetch=fetch)
        return 0 if ok in (True, None) else 1
    except ShipError as e:
        log(f"ERROR {e}")
        return e.code


if __name__ == "__main__":
    sys.exit(main())
