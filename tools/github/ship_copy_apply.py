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

Exit: 0 applied / checked and (apply) the key is registered | 1 run not green or key not registered |
2 usage, dispatch failed or run not found | 3 copy PR red | 4 refused (destructive, closed) | 5 timed out.
dbmig.sh calls this with --no-copy. Orchestrator only (merge + gh workflow run). Holds no secrets.
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
from datetime import datetime, timezone

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


def file_on_main(runner: Runner, owner: str, num: str, name: str | None) -> str | None:
    r = runner.run(["gh", "api", f"repos/{INFRA_SLUG}/contents/db/migrations/{owner}?ref=main",
                    "--jq", ".[].name"], timeout=60)
    if not r.ok:
        raise ShipError(f"cannot list db/migrations/{owner} on Infra main: {r.last_line()}", 2)
    names = [x.strip() for x in r.out.splitlines() if x.strip()]
    hits = [x for x in names if x.startswith(f"{num}_") and x.endswith(".sql")]
    if name:
        return name if name in hits else None
    if len(hits) > 1:
        raise ShipError(f"several files {owner}/{num}_*.sql on Infra main: {', '.join(hits)}", 2)
    return hits[0] if hits else None


def ensure_copy(runner: Runner, owner: str, num: str, name: str | None, *, timeout: float, interval: float,
                gate_timeout: float) -> str:
    """Wait for / merge the copy PR; return the file name on Infra main."""
    t0 = runner.now()
    while True:
        pr = find_copy_pr(runner, owner, num)
        if pr and pr.get("state") == "OPEN":
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


def key_log_lines(runner: Runner, run_id: int, limit: int = 25) -> list[str]:
    v = gh_json(runner, ["gh", "run", "view", str(run_id), "-R", INFRA_SLUG, "--json", "jobs"])
    out: list[str] = []
    for job in (v or {}).get("jobs") or []:
        r = runner.run(["gh", "api", f"repos/{INFRA_SLUG}/actions/jobs/{job.get('databaseId')}/logs"], timeout=120)
        if not r.ok:
            continue
        for line in r.out.splitlines():
            text = re.sub(r"^\S+Z\s", "", line).strip()  # drop the timestamp column
            if text.startswith("##[group") or not LOG_PATTERN.search(text):
                continue
            out.append(text[:260])
            if len(out) >= limit:
                return out
    return out


# --- readiness ---------------------------------------------------------------------------------------------------


def fetch_ready(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "aa-ship-tools"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - fixed https URLs
        return json.loads(resp.read().decode("utf-8"))


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


def main(argv: list[str] | None = None, runner: Runner | None = None, fetch=fetch_ready) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("owner", help="cis | booking | crm | tripplanner")
    ap.add_argument("migration", help="NNN, <prefix>-NNN or the file name")
    ap.add_argument("--mode", choices=("apply", "check"), default="apply")
    ap.add_argument("--no-copy", action="store_true", help="the file is already on Infra main: skip the copy PR")
    ap.add_argument("--no-dispatch", action="store_true", help="stop after the copy PR")
    ap.add_argument("--dispatch-expand", action="store_true", help="dispatch even for an expand file")
    ap.add_argument("--allow-destructive", action="store_true", help="dispatch a destructive file (after DRY RUN)")
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
                                gate_timeout=a.run_timeout)
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
        run = dispatch(runner, path, a.mode)
        rid = int(run["databaseId"])
        conclusion = wait_run(runner, rid, timeout=a.run_timeout, interval=a.interval)
        log(f"DBMIG {a.mode} {path} run={rid} conclusion={conclusion}")
        for line in key_log_lines(runner, rid):
            log(f"  {line}")
        if conclusion != "success":
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
