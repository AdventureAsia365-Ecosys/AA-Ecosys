"""Which Dev services a merged PR deploys, and the ECS exec guard before a CIS backend merge (AA-1048, S281).

Read-only helpers for the ship tools; stdlib only, every external command through a ship_common.Runner.

1. Deployed services per repo. Each app repo deploys one or more services from its own workflow, filtered by the
   workflow's `on.push.paths` (GitHub semantics: patterns in order, a later `!pattern` drops what an earlier one took).
   `SERVICES` mirrors those filters and the health endpoint that reports the running commit (`git_sha`, or `sha` for
   the admin frontends). ship_wave.py --wait-deploy waits on the services a merged PR touches, not on the repo's API
   alone: S281 Partner #323 (web only) was reported "still <old sha> after 1800s" (exit 5) because only the CRM API
   health was read, while the CRM web /healthz already served the merge. A PR that touches no deploy path (docs, tests)
   expects no deploy. test_ship_deploy.py compares `paths` with the workflows of the local app clones (skipped when a
   clone is missing), so a changed filter shows up as a red test, not as a wrong wait.

2. ECS exec guard. tools/ecs/ecsx.sh in S3 mode (the CIS api and worker containers) keeps a heartbeat object
   `scripts/out/<run id>.txt.running` on the scripts bucket while the script runs (rewritten every 30 s,
   tools/ecs/ecsx_runner.py) and removes it with the result. A merge that deploys aa-cis-dev-api / -worker replaces the
   task under the script and kills it (lesson S234). Before ship_merge.merge_one merges a CIS PR that touches the
   api/worker deploy paths, `exec_guard` lists the heartbeats and refuses while one is fresh (younger than FRESH_S, no
   `.done` next to it), naming the run id, unless the tech lead passes --allow-running-exec (logged). The CI deploy
   guard of AA-CIS-App (deploy_job_guard.sh, shared/jobs/exec_heartbeat.py) reads the same heartbeats and still blocks
   the roll itself; this guard keeps main from getting ahead of what can deploy. Booking and CRM runs use the local
   mode (their task roles cannot write the bucket): their output stays in the container's /tmp and nothing is recorded
   outside, so they are not guarded (gap documented in tools/github/README.md).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ship_common import ROOT, Runner, ShipError, log, slug

HERE = Path(__file__).resolve().parent
ECSX_SH = HERE.parent / "ecs" / "ecsx.sh"


@dataclass(frozen=True)
class Service:
    repo: str
    name: str  # short label: api, web, admin
    label: str  # what deploys (ECS services)
    url: str  # health endpoint that reports the running commit
    workflow: str  # the deploy workflow whose push paths `paths` mirrors
    paths: tuple[str, ...]  # on.push.paths of that workflow, in order


# Hosts: docs/ecosystem-architecture.md (CIS api-cis., CIS admin aa-cis., Booking api-booking., Booking admin
# booking., CRM API on partner-dev. /crm, CRM web on the agency host portal.). Paths: each workflow's on.push.paths.
SERVICES: tuple[Service, ...] = (
    Service("AA-CIS-App", "api", "aa-cis-dev-api + aa-cis-dev-worker",
            "https://api-cis.lumiguides.it.com/health/ready", ".github/workflows/deploy-dev.yml",
            ("api/**", "shared/**", "services/**", "worker/**", "Dockerfile", "requirements.txt", "!api/version.py",
             "!api/migrations/**")),
    Service("AA-CIS-App", "admin", "aa-cis-dev-admin",
            "https://aa-cis.lumiguides.it.com/api/healthz", ".github/workflows/deploy-admin-dev.yml",
            ("frontend/**", "!frontend/**/*.test.mjs", ".github/workflows/deploy-admin-dev.yml")),
    Service("AA-Booking", "api", "aa-booking-dev-api",
            "https://api-booking.lumiguides.it.com/booking/health", ".github/workflows/deploy-dev.yml",
            ("backend/**", "!backend/tests/**", "!backend/pyproject.toml", ".github/workflows/deploy-dev.yml",
             ".github/scripts/booking-deploy-preflight.sh", ".github/scripts/schema_gate.py")),
    Service("AA-Booking", "admin", "aa-booking-dev-admin",
            "https://booking.lumiguides.it.com/api/healthz", ".github/workflows/deploy-admin-dev.yml",
            ("frontend/**", "!frontend/**/*.test.mjs", "!frontend/e2e/**", ".github/workflows/deploy-admin-dev.yml")),
    Service("AA-Partner", "api", "aa-crm-dev-api",
            "https://partner-dev.lumiguides.it.com/crm/health", ".github/workflows/deploy-dev.yml",
            ("api/**", "!api/tests/**", "!api/pyproject.toml", "!api/migrations/**",
             ".github/workflows/deploy-dev.yml", ".github/scripts/partner-deploy-preflight.sh",
             ".github/scripts/schema_gate.py")),
    Service("AA-Partner", "web", "aa-crm-dev-web",
            "https://portal.lumiguides.it.com/healthz", ".github/workflows/deploy-web-dev.yml",
            ("web/**", "!web/tests/**", ".github/workflows/deploy-web-dev.yml")),
)
DEPLOYED_REPOS = frozenset(s.repo for s in SERVICES)
# The CIS service whose deploy replaces the containers ecsx runs in (S3 mode: api and worker).
EXEC_SERVICE = next(s for s in SERVICES if s.repo == "AA-CIS-App" and s.name == "api")


def services_of(repo: str) -> list[Service]:
    return [s for s in SERVICES if s.repo == repo]


def service(repo: str, name: str) -> Service:
    for s in SERVICES:
        if s.repo == repo and s.name == name:
            return s
    raise KeyError(f"{repo}/{name}")


def _glob_re(pattern: str) -> re.Pattern:
    """A workflow path glob as a regex: '**/' any directories (or none), '**' anything, '*' one segment, '?' a char."""
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def path_matches(paths: tuple[str, ...] | list[str], file: str) -> bool:
    """GitHub `on.push.paths`: patterns in order; a match sets it, a later matching '!pattern' clears it."""
    hit = False
    for p in paths:
        neg = p.startswith("!")
        if _glob_re(p[1:] if neg else p).match(file):
            hit = not neg
    return hit


def touched_services(repo: str, files: list[str]) -> list[Service]:
    """The services of `repo` whose deploy workflow a merge changing `files` starts ([] = no deploy expected)."""
    return [s for s in services_of(repo) if any(path_matches(s.paths, f) for f in files)]


def changed_files(runner: Runner, repo: str, n: int) -> list[str]:
    """Every file the PR changes (added, modified, removed, renamed: both names). ShipError when unreadable."""
    r = runner.run(["gh", "api", "--paginate", f"repos/{slug(repo)}/pulls/{n}/files?per_page=100",
                    "--jq", "[.[] | .filename, (.previous_filename // empty)]"], timeout=60)
    if not r.ok:
        raise ShipError(f"{repo}#{n}: cannot list the PR files: {r.last_line()}", 2)
    out: list[str] = []
    try:
        for line in r.out.splitlines():
            if line.strip():
                v = json.loads(line)
                out.extend(str(x) for x in (v if isinstance(v, list) else [v]))
    except json.JSONDecodeError as e:
        raise ShipError(f"{repo}#{n}: the PR file list is not JSON ({e})", 2) from e
    return out


def running_sha(body: object) -> str:
    """The commit a health body reports: `git_sha` (APIs, CRM web) or `sha` (CIS / Booking admin /api/healthz)."""
    if not isinstance(body, dict):
        return ""
    return str(body.get("git_sha") or body.get("sha") or "")


# --- ECS exec guard ----------------------------------------------------------------------------------------------

OUT_PREFIX = "scripts/out/"
RUNNING_SUFFIX = ".running"
DONE_SUFFIX = ".done"
# Same rule as the CIS deploy gate (shared/jobs/exec_heartbeat.py FRESH_S): four missed beats of the runner's 30 s
# heartbeat (ecsx_runner.HEARTBEAT_MAX_S caps the beat at 30 s, so a live run is never older than this).
FRESH_S = 120
ALLOW_FLAG = "--allow-running-exec"
# Every override is appended here (one JSON line) besides the WARN line in the run output.
OVERRIDE_LOG = ROOT / ".tmp-session" / "ship-overrides.jsonl"


def exec_bucket() -> str:
    """The scripts bucket ecsx uses: ECSX_BUCKET, else the default written in tools/ecs/ecsx.sh (one source)."""
    env = os.environ.get("ECSX_BUCKET", "").strip()
    if env:
        return env
    try:
        text = ECSX_SH.read_text(encoding="utf-8")
    except OSError as e:
        raise ShipError(f"cannot read {ECSX_SH} for the scripts bucket ({e}); set ECSX_BUCKET", 2) from e
    m = re.search(r"\$\{ECSX_BUCKET:-([A-Za-z0-9.\-]+)\}", text)
    if not m:
        raise ShipError(f"no ECSX_BUCKET default in {ECSX_SH}; set ECSX_BUCKET", 2)
    return m.group(1)


def exec_profile() -> str:
    return os.environ.get("ECSX_PROFILE", "aa365-admin")


def _parse_time(text: str) -> datetime | None:
    try:
        t = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def running_from_listing(objects: list[dict], now: float, fresh_s: int = FRESH_S) -> list[dict]:
    """Fresh heartbeats with no `.done` next to them, oldest first: [{run_id, age_s}]."""
    keys = {str(o.get("Key") or "") for o in objects}
    out = []
    for o in objects:
        key = str(o.get("Key") or "")
        if not key.startswith(OUT_PREFIX) or not key.endswith(RUNNING_SUFFIX):
            continue
        base = key[: -len(RUNNING_SUFFIX)]
        if base + DONE_SUFFIX in keys:
            continue
        t = _parse_time(str(o.get("LastModified") or ""))
        if t is None:
            continue
        age = now - t.timestamp()
        if age <= fresh_s:
            run_id = base[len(OUT_PREFIX):].rsplit(".", 1)[0]
            out.append({"run_id": run_id, "age_s": max(0, int(age))})
    return sorted(out, key=lambda r: (-r["age_s"], r["run_id"]))


def running_exec_runs(runner: Runner) -> list[dict]:
    """ecsx S3-mode runs alive now (read-only list of the top level of scripts/out/). ShipError when unreadable."""
    r = runner.run(["aws", "s3api", "list-objects-v2", "--bucket", exec_bucket(), "--prefix", OUT_PREFIX,
                    "--delimiter", "/", "--query", "Contents[].{Key: Key, LastModified: LastModified}",
                    "--output", "json", "--profile", exec_profile(), "--region", "us-west-1"], timeout=60)
    if not r.ok:
        raise ShipError(f"cannot read the ECS exec heartbeats ({r.last_line()[:200]})", 4)
    try:
        objects = json.loads(r.out or "null") or []
    except json.JSONDecodeError as e:
        raise ShipError(f"the ECS exec heartbeat listing is not JSON ({e})", 4) from e
    return running_from_listing(list(objects), runner.now())


def _record_override(repo: str, n: int, what: str, now: float) -> None:
    try:
        OVERRIDE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(OVERRIDE_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"t": int(now), "flag": ALLOW_FLAG, "pr": f"{repo}#{n}", "what": what}) + "\n")
    except OSError as e:
        log(f"WARN cannot append the override to {OVERRIDE_LOG}: {e}")


def exec_guard(runner: Runner, repo: str, n: int, *, allow: bool = False) -> None:
    """Refuse (ShipError exit 4) to merge a CIS PR that deploys api/worker while an ecsx script runs there.

    Only AA-CIS-App PRs that touch the api/worker deploy paths are checked; an unreadable file list counts as
    touching them, an unreadable heartbeat listing refuses (fail closed). `allow` (--allow-running-exec) turns a
    refusal into a logged warning."""
    if repo != EXEC_SERVICE.repo:
        return
    tag = f"{repo}#{n}"
    try:
        files = changed_files(runner, repo, n)
        if EXEC_SERVICE not in touched_services(repo, files):
            return
    except ShipError as e:
        log(f"{tag}: {e}; treating it as a backend PR for the ECS exec guard")
    try:
        runs = running_exec_runs(runner)
    except ShipError as e:
        what = f"{e}: cannot tell whether an ECS exec script runs in {EXEC_SERVICE.label}"
        if allow:
            log(f"WARN {tag}: {ALLOW_FLAG} (tech lead's call): merging although {what}")
            _record_override(repo, n, what, runner.now())
            return
        raise ShipError(f"{tag} REFUSED: {what} (renew the MFA session: aws sts get-caller-identity --profile "
                        f"{exec_profile()}; or {ALLOW_FLAG}, the tech lead's call)", 4) from e
    if not runs:
        return
    names = ", ".join(f"{x['run_id']} (heartbeat {x['age_s']}s ago)" for x in runs)
    what = f"ECS exec script running in {EXEC_SERVICE.label}: {names}"
    if allow:
        log(f"WARN {tag}: {ALLOW_FLAG} (tech lead's call): merging while an {what}; the CIS deploy guard still "
            f"blocks the roll until the script ends or that guard is overridden")
        _record_override(repo, n, what, runner.now())
        return
    raise ShipError(f"{tag} REFUSED: an {what}. This merge deploys a new task and would kill it: wait until "
                    f"tools/ecs/ecsx.sh prints the result, then ship again (or {ALLOW_FLAG}, the tech lead's call)", 4)
