"""Shared helpers for the orchestrator ship tools (tools/github/ship_*.py, AA-1032).

The tools merge, restack, copy-and-apply and open PRs for the AA_Ecosys repos. Every write to GitHub goes through
the aa-agent App (as-app.sh next to this file); reads use the local `gh` login. No token, key or credential is
printed: MFA expiry is read from `aws configure export-credentials` and only its Expiration field is kept.

Orchestrator only: the subagent guardrail hook blocks push, merge and `gh workflow run`, and these tools do exactly
that. Python stdlib only. Every external command goes through a Runner so the tests can replace it with a stub.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
AS_APP = str(HERE / "as-app.sh")
MERGEQ = str(HERE / "mergeq.sh")
# The main workspace checkout (the tools may run from a worktree copy of the root repo).
ROOT = Path(os.environ.get("AA_ECOSYS_ROOT", "/home/nghiep/projects/AA-Ecosys"))
ORG = "AdventureAsia365-Ecosys"

REPOS = ("AA-Ecosys", "AA-CIS-App", "AA-Booking", "AA-Partner", "AA-TripPlanner-Web", "AA-CIS-Infra")
# Repos whose main is protected by the GitHub merge queue (AA-889): merge through mergeq.sh.
QUEUE_REPOS = frozenset({"AA-CIS-App", "AA-Booking", "AA-Partner"})
ALIASES = {
    "root": "AA-Ecosys",
    "aa-ecosys": "AA-Ecosys",
    "cis": "AA-CIS-App",
    "booking": "AA-Booking",
    "bk": "AA-Booking",
    "partner": "AA-Partner",
    "crm": "AA-Partner",
    "tp": "AA-TripPlanner-Web",
    "tripplanner": "AA-TripPlanner-Web",
    "infra": "AA-CIS-Infra",
}
LOCAL_DIRS = {
    "AA-Ecosys": "",
    "AA-CIS-App": "apps/AA-CIS-App",
    "AA-Booking": "apps/AA-Booking",
    "AA-Partner": "apps/AA-Partner",
    "AA-TripPlanner-Web": "apps/AA-TripPlanner-Web",
    "AA-CIS-Infra": "infra/AA-CIS-Infra",
}

# CheckRun conclusions that count as green. Anything else that is COMPLETED (FAILURE, CANCELLED, TIMED_OUT,
# ACTION_REQUIRED, STARTUP_FAILURE, STALE) is red: S263 #1225 merged with a red non-required "Migration preflight".
GREEN_CONCLUSIONS = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})


class ShipError(Exception):
    """A refusal or failure with the exit code the CLI should return."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


@dataclass
class Result:
    rc: int
    out: str = ""
    err: str = ""

    @property
    def ok(self) -> bool:
        return self.rc == 0

    def last_line(self) -> str:
        lines = [x for x in (self.out + "\n" + self.err).splitlines() if x.strip()]
        return lines[-1].strip() if lines else ""


class Runner:
    """Runs external commands. The tests replace it with a scripted fake (test_ship_tools.FakeRunner)."""

    def run(self, argv: list[str], timeout: float | None = None, input_text: str | None = None) -> Result:
        kw: dict = {"capture_output": True, "text": True, "timeout": timeout}
        if input_text is None:
            kw["stdin"] = subprocess.DEVNULL
        else:
            kw["input"] = input_text
        try:
            p = subprocess.run(argv, **kw)
        except subprocess.TimeoutExpired:
            return Result(124, "", f"timed out after {timeout}s")
        except FileNotFoundError as e:
            return Result(127, "", str(e))
        return Result(p.returncode, p.stdout or "", p.stderr or "")

    def stream(self, argv: list[str], prefix: str, timeout: float | None = None) -> Result:
        """Run a long command (mergeq.sh) and print its lines as they come, prefixed; return the collected output."""
        lines: list[str] = []
        try:
            p = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True)
        except FileNotFoundError as e:
            return Result(127, "", str(e))
        timer = threading.Timer(timeout, p.kill) if timeout else None
        if timer:
            timer.start()
        try:
            assert p.stdout is not None
            for line in p.stdout:
                lines.append(line.rstrip("\n"))
                log(f"{prefix}{line.rstrip()}")
            rc = p.wait()
        finally:
            if timer:
                timer.cancel()
        return Result(rc, "\n".join(lines), "")

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def now(self) -> float:
        return time.time()


_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


# --- names -------------------------------------------------------------------------------------------------------


def normalize_repo(name: str) -> str:
    """Map 'AA-Ecosys (root)', 'apps/AA-CIS-App', 'AdventureAsia365-Ecosys/AA-Booking', 'cis' ... to a repo name."""
    s = name.strip()
    s = re.sub(r"\s*\(.*\)\s*$", "", s)  # "AA-Ecosys (root)"
    s = s.rstrip("/").split("/")[-1]  # org/ or apps/ or infra/ prefix
    if s.lower() in ALIASES:
        return ALIASES[s.lower()]
    for r in REPOS:
        if r.lower() == s.lower():
            return r
    raise ShipError(f"unknown repo '{name}' (known: {', '.join(REPOS)} or {', '.join(sorted(ALIASES))})", 2)


def parse_target(text: str) -> tuple[str, int]:
    """'AA-CIS-App 1225', 'AA-CIS-App#1225', 'cis#1225' or 'cis 1225' -> ('AA-CIS-App', 1225)."""
    m = re.fullmatch(r"\s*([A-Za-z0-9_./() -]+?)\s*[#\s]\s*(\d+)\s*", text)
    if not m:
        raise ShipError(f"cannot read '{text}': use '<Repo> <pr>' or '<Repo>#<pr>'", 2)
    return normalize_repo(m.group(1)), int(m.group(2))


def parse_targets(args: list[str]) -> list[tuple[str, int]]:
    """Accept quoted pairs ('AA-CIS-App 1225'), Repo#n, or loose argv (AA-CIS-App 1225 AA-Booking 7)."""
    out: list[tuple[str, int]] = []
    i = 0
    while i < len(args):
        a = args[i]
        if re.search(r"[#\s]\d+\s*$", a):
            out.append(parse_target(a))
            i += 1
        elif i + 1 < len(args) and args[i + 1].isdigit():
            out.append((normalize_repo(a), int(args[i + 1])))
            i += 2
        else:
            raise ShipError(f"cannot read target '{a}': use '<Repo> <pr>' or '<Repo>#<pr>'", 2)
    return out


def default_branch(repo: str) -> str:
    return "master" if repo == "AA-Ecosys" else "main"


def slug(repo: str) -> str:
    return f"{ORG}/{repo}"


def local_checkout(repo: str) -> Path:
    return ROOT / LOCAL_DIRS[repo] if LOCAL_DIRS[repo] else ROOT


# --- GitHub reads ------------------------------------------------------------------------------------------------


PR_FIELDS = "number,state,isDraft,mergeStateStatus,baseRefName,headRefName,headRefOid,mergeCommit,statusCheckRollup"


def gh_json(runner: Runner, argv: list[str], timeout: float = 60) -> object:
    r = runner.run(argv, timeout=timeout)
    if not r.ok:
        raise ShipError(f"{' '.join(argv[:4])} failed: {r.last_line()}", 2)
    try:
        return json.loads(r.out or "null")
    except json.JSONDecodeError as e:
        raise ShipError(f"{' '.join(argv[:4])}: not JSON ({e})", 2) from e


def pr_view(runner: Runner, repo: str, n: int) -> dict:
    data = gh_json(runner, ["gh", "pr", "view", str(n), "-R", slug(repo), "--json", PR_FIELDS])
    if not isinstance(data, dict):
        raise ShipError(f"{repo}#{n}: unexpected gh output", 2)
    return data


@dataclass
class CheckSummary:
    green: list[str] = field(default_factory=list)
    red: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.green) + len(self.red) + len(self.pending)


def classify_checks(rollup: list[dict] | None) -> CheckSummary:
    """Every check counts, required or not. A re-run of the same check (same workflow + name) replaces the older
    run; a run superseded by concurrency (CANCELLED, then run again) is therefore not red, but a latest run that is
    CANCELLED is."""
    latest: dict[tuple, dict] = {}
    for item in rollup or []:
        kind = item.get("__typename", "CheckRun")
        name = item.get("context") if kind == "StatusContext" else item.get("name")
        key = (kind, item.get("workflowName", ""), name)
        stamp = item.get("startedAt") or item.get("completedAt") or ""
        if key not in latest or stamp >= (latest[key].get("startedAt") or latest[key].get("completedAt") or ""):
            latest[key] = item
    s = CheckSummary()
    for (kind, wf, name), item in sorted(latest.items(), key=lambda kv: (kv[0][1] or "", kv[0][2] or "")):
        label = f"{wf} / {name}" if wf else str(name)
        if kind == "StatusContext":
            state = (item.get("state") or "").upper()
            if state in ("PENDING", "EXPECTED", ""):
                s.pending.append(label)
            elif state == "SUCCESS":
                s.green.append(label)
            else:
                s.red.append(f"{label} ({state.lower()})")
        else:
            if (item.get("status") or "").upper() != "COMPLETED":
                s.pending.append(label)
            elif (item.get("conclusion") or "").upper() in GREEN_CONCLUSIONS:
                s.green.append(label)
            else:
                s.red.append(f"{label} ({(item.get('conclusion') or 'no conclusion').lower()})")
    return s


def _parse_paged_arrays(text: str) -> list:
    out: list = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            v = json.loads(line)
            out.extend(v if isinstance(v, list) else [v])
    return out


def removed_files(runner: Runner, repo: str, n: int) -> list[str]:
    """Files the PR deletes (a squash from a stale base shows up as deletions: lessons S250/S253)."""
    r = runner.run(["gh", "api", "--paginate", f"repos/{slug(repo)}/pulls/{n}/files?per_page=100",
                    "--jq", '[.[] | select(.status=="removed") | .filename]'], timeout=60)
    if not r.ok:
        raise ShipError(f"{repo}#{n}: cannot list PR files: {r.last_line()}", 2)
    return [str(x) for x in _parse_paged_arrays(r.out)]


# --- AWS MFA session ---------------------------------------------------------------------------------------------


def mfa_expiry(runner: Runner, profile: str = "aa365-admin") -> datetime | None:
    """Expiry of the cached MFA session (8 h). Only the Expiration field is read; nothing else is kept or printed."""
    r = runner.run(["aws", "configure", "export-credentials", "--profile", profile, "--format", "process"],
                   timeout=30)
    if not r.ok:
        return None
    try:
        exp = json.loads(r.out).get("Expiration")
    except (json.JSONDecodeError, AttributeError):
        return None
    if not exp:
        return None
    try:
        return datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
    except ValueError:
        return None


def warn_mfa(runner: Runner, need_minutes: int = 30) -> None:
    """as-app.sh reads the App key with the MFA session: warn before a long run that would outlive it."""
    exp = mfa_expiry(runner)
    if exp is None:
        log("WARN MFA session: expired or unreadable (as-app.sh will fail). "
            "Tech lead: run aws sts get-caller-identity --profile aa365-admin and enter the code.")
        return
    left = (exp - datetime.fromtimestamp(runner.now(), tz=timezone.utc)).total_seconds() / 60
    if left < need_minutes:
        log(f"WARN MFA session ends in {int(left)} min ({exp.astimezone().strftime('%H:%M')} local): "
            "renew before the run needs as-app.sh again.")


def fmt_list(items: list[str], limit: int = 12) -> str:
    more = f" (+{len(items) - limit} more)" if len(items) > limit else ""
    return "; ".join(items[:limit]) + more


def die(e: ShipError) -> int:
    print(f"ERROR {e}", file=sys.stderr, flush=True)
    return e.code
