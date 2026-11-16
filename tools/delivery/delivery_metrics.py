#!/usr/bin/env python3
"""AA-1108 — delivery metrics (CI/CD and DORA per app) from the GitHub data of the six repos.

The root workflow "Delivery metrics" (.github/workflows/delivery-metrics.yml) runs this every hour. It reads the public
repos with the run's GITHUB_TOKEN (no new secret), keeps a normalised event store between runs (an Actions cache on
master), computes one summary per app and publishes it next to the docs reader bundle, where the CIS admin page
Platform › Delivery and the reports DEV-01 / DEV-03 read it (AA-CIS-App api/services/delivery_metrics.py):

  s3://<bronze>/docs-reader/delivery/summary.json                 format 1, the summary below
  s3://<bronze>/docs-reader/delivery/events/<yyyy>/<mm>/<dd>.ndjson  the normalised raw events, one file per day

Design (tech lead approved S282, root .tmp-session audit "aa1108-delivery-design", docs/guides/delivery-metrics.md):

  * Raw events first, metrics after. The collector stores normalised events (workflow runs, jobs, merged pull
    requests, GitHub Deployments) and computes every metric from them, so a changed definition is recomputed on the
    stored history. Field names follow the OpenTelemetry semantic conventions for CI/CD and VCS (cicd.pipeline.*,
    cicd.pipeline.task.*, vcs.*, deployment.*); fields with no convention carry the prefix `aa.`.
  * A deploy is a run of an app's deploy workflow on its default branch whose deploy job ran; runs of one commit that
    follow each other (CIS api + worker and admin, CRM api and web) are ONE deploy of the app. It is green when the
    deploy jobs and the post-deploy verify passed. A deploy failed when the verify was red, a deploy job failed, it
    was rolled back (a later deploy of an older commit), its pull request was reverted, or a `fix` pull request
    naming its pull request merged within `rework_hours` (48). Recovery = from the failed deploy to the next green
    deploy that repairs it. Rework rate = deploys that are a rollback or ship a revert / hotfix pull request.
  * A change is a pull request squash-merged into the default branch. Lead time = opened -> first green CI ->
    entered the merge queue -> merged -> deployed -> verified, measured to the first green deploy that contains the
    merge commit. Bot pull requests (not the agent App) and pull requests that change only docs are left out of the
    lead time and counted apart.
  * Every number carries its sample size `n`; the numbers are Dev numbers (environment `dev`).

Budget: GITHUB_TOKEN allows 1,000 requests an hour; one run spends at most `request_budget` (apps.json) and stops
early when the rate limit runs low. A cold store fills over several runs (newest data first: recent runs, merged pull
requests, deployments, the jobs of deploy runs, then older days); `collection.repos[].complete_since` says from which
day the history is complete.

    python3 tools/delivery/delivery_metrics.py collect --store DIR --out DIR       # GITHUB_TOKEN in the environment
    python3 tools/delivery/delivery_metrics.py summarize --store DIR --out DIR     # recompute from the store, offline
    python3 tools/delivery/delivery_metrics.py expired --keys FILE [--today D]     # S3 event keys past retention

Stdlib only. Exit 0 = done (a budget stop is not an error), 1 = no repo could be read, 2 = bad usage or config.
"""

from __future__ import annotations

import argparse
import fnmatch
import gzip
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

CONFIG = Path(__file__).with_name("apps.json")
FORMAT = 1
DEFINITIONS_VERSION = "2026-11-16"
API = "https://api.github.com"
STORE_EVENTS = "events.ndjson.gz"
STORE_STATE = "state.json"

RESULTS = {
    "success": "success",
    "failure": "failure",
    "cancelled": "cancellation",
    "skipped": "skip",
    "timed_out": "timeout",
    "action_required": "error",
    "neutral": "success",
    "stale": "error",
    "startup_failure": "error",
}
STATES = {
    "queued": "pending",
    "waiting": "pending",
    "pending": "pending",
    "requested": "pending",
    "in_progress": "executing",
    "completed": "finalizing",
}
RED = ("failure", "timeout", "error")
QUEUE_BRANCH = re.compile(r"^gh-readonly-queue/[^/]+/pr-(\d+)-")
REVERTS = re.compile(r"\bReverts?\s+(?:[\w.-]+/[\w.-]+)?#(\d+)", re.I)
TITLE_REF = re.compile(r"\(#(\d+)\)")
ANY_REF = re.compile(r"(?<![\w/])#(\d+)\b")
CHANGE_TYPE = re.compile(r"^(?:revert|feat|fix|chore|refactor|docs|test|perf|build|ci|style)(?=[(:!])", re.I)


# ── time helpers ────────────────────────────────────────────────────────────────────────────────────────────────


def ts(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def hours(a: Optional[datetime], b: Optional[datetime]) -> Optional[float]:
    if a is None or b is None:
        return None
    return round(max((b - a).total_seconds(), 0.0) / 3600.0, 3)


def percentile(values: Iterable[float], q: float) -> Optional[float]:
    """Nearest-rank percentile (q in 0..100); None for no value."""
    xs = sorted(v for v in values if v is not None)
    if not xs:
        return None
    k = max(1, math.ceil(q / 100.0 * len(xs)))
    return round(xs[min(k, len(xs)) - 1], 3)


def iso_week(d: datetime) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


# ── config ──────────────────────────────────────────────────────────────────────────────────────────────────────


class ConfigError(ValueError):
    pass


def load_config(path: Path = CONFIG) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("format") != FORMAT or not isinstance(cfg.get("apps"), list) or not cfg["apps"]:
        raise ConfigError(f"{path}: format {FORMAT} with a non-empty apps list expected")
    for k in (
        "org",
        "environment",
        "headline_days",
        "trend_weeks",
        "trend_months",
        "store_days",
        "jobs_days",
        "runs_overlap_days",
        "rework_hours",
        "raw_retention_days",
        "request_budget",
        "rate_limit_floor",
        "list_cap",
    ):
        if k not in cfg:
            raise ConfigError(f"{path}: {k} missing")
    seen = set()
    for a in cfg["apps"]:
        for k in ("id", "name", "repo", "default_branch", "deploy_workflows", "deploy_job", "ci_workflows"):
            if not a.get(k):
                raise ConfigError(f"{path}: app {a.get('id')!r}: {k} missing")
        if a["id"] in seen:
            raise ConfigError(f"{path}: app {a['id']} twice")
        seen.add(a["id"])
        re.compile(a["deploy_job"])
        if a.get("verify_job"):
            re.compile(a["verify_job"])
    return cfg


# ── GitHub REST client with a request budget ────────────────────────────────────────────────────────────────────


class BudgetSpent(Exception):
    """The run's request budget (or the rate limit floor) is reached: stop fetching, keep what we have."""


class ReadError(Exception):
    """A GitHub read failed (HTTP error other than a budget stop)."""


Transport = Callable[[str], tuple[int, dict, bytes]]


def urllib_transport(token: str) -> Transport:
    def call(url: str) -> tuple[int, dict, bytes]:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "aa-delivery-metrics",
                **({"Authorization": f"Bearer {token}"} if token else {}),
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed https://api.github.com URL)
                return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read() or b""

    return call


class GitHub:
    def __init__(self, transport: Transport, budget: int, floor: int = 0, sleep: Callable[[float], None] = time.sleep):
        self.transport, self.budget, self.floor, self.sleep = transport, budget, floor, sleep
        self.used = 0
        self.remaining: Optional[int] = None

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        if self.used >= self.budget or (self.remaining is not None and self.remaining <= self.floor):
            raise BudgetSpent(f"used {self.used} of {self.budget}, rate limit remaining {self.remaining}")
        url = f"{API}/{path.lstrip('/')}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
        for attempt in (1, 2):
            self.used += 1
            status, headers, body = self.transport(url)
            rem = headers.get("x-ratelimit-remaining")
            if rem is not None and str(rem).isdigit():
                self.remaining = int(rem)
            if status == 200:
                return json.loads(body or b"null")
            if status in (403, 429) and self.remaining == 0:
                raise BudgetSpent(f"rate limit reached at {path}")
            if status >= 500 and attempt == 1:
                self.sleep(2.0)
                continue
            raise ReadError(f"GET {path}: HTTP {status}")
        raise ReadError(f"GET {path}: no answer")

    def pages(self, path: str, params: dict, key: Optional[str] = None, max_pages: int = 50) -> Iterable[dict]:
        """Items page by page (per_page 100) until a short page; `key` names the list inside an object answer."""
        for page in range(1, max_pages + 1):
            data = self.get(path, {**params, "per_page": 100, "page": page})
            items = (data or {}).get(key) or [] if key else (data or [])
            yield from items
            if len(items) < 100:
                return


# ── normalised events (OpenTelemetry CI/CD + VCS semantic convention names; `aa.` for the rest) ─────────────────


def _base(path: Any) -> str:
    return str(path or "").split("@", 1)[0].rsplit("/", 1)[-1]


def run_event(repo: str, r: dict) -> dict:
    start, end = ts(r.get("run_started_at") or r.get("created_at")), None
    if r.get("status") == "completed":
        end = ts(r.get("updated_at"))
    prs = [p.get("number") for p in r.get("pull_requests") or [] if isinstance(p, dict) and p.get("number")]
    return {
        "event": "cicd.pipeline.run",
        "id": f"{repo}/run/{r['id']}",
        "time": r.get("updated_at") or r.get("created_at"),
        "attributes": {
            "vcs.repository.name": repo,
            "cicd.pipeline.name": r.get("name") or _base(r.get("path")),
            "aa.workflow.file": _base(r.get("path")),
            "cicd.pipeline.run.id": r["id"],
            "cicd.pipeline.run.url.full": r.get("html_url"),
            "cicd.pipeline.run.state": STATES.get(r.get("status") or "", "pending"),
            "cicd.pipeline.result": RESULTS.get(r.get("conclusion") or "") if r.get("status") == "completed" else None,
            "vcs.ref.head.name": r.get("head_branch"),
            "vcs.ref.head.revision": r.get("head_sha"),
            "aa.trigger": r.get("event"),
            "aa.run_attempt": r.get("run_attempt") or 1,
            "vcs.change.id": prs[0] if prs else None,
            "aa.created_at": r.get("created_at"),
            "start_time": iso(start),
            "end_time": iso(end),
            "aa.duration_s": round((end - start).total_seconds()) if start and end and end >= start else None,
        },
    }


def job_event(repo: str, run: dict, j: dict) -> dict:
    start, end = ts(j.get("started_at")), ts(j.get("completed_at"))
    a = run["attributes"]
    return {
        "event": "cicd.pipeline.task.run",
        "id": f"{repo}/job/{j['id']}",
        "time": j.get("completed_at") or j.get("started_at"),
        "attributes": {
            "vcs.repository.name": repo,
            "cicd.pipeline.name": a["cicd.pipeline.name"],
            "aa.workflow.file": a["aa.workflow.file"],
            "cicd.pipeline.run.id": a["cicd.pipeline.run.id"],
            "cicd.pipeline.task.name": j.get("name"),
            "cicd.pipeline.task.run.id": j["id"],
            "cicd.pipeline.task.run.url.full": j.get("html_url"),
            "cicd.pipeline.task.run.result": RESULTS.get(j.get("conclusion") or "") if j.get("conclusion") else None,
            "vcs.ref.head.revision": j.get("head_sha") or a["vcs.ref.head.revision"],
            "aa.run_attempt": j.get("run_attempt") or 1,
            "start_time": iso(start),
            "end_time": iso(end),
            "aa.duration_s": round((end - start).total_seconds()) if start and end and end >= start else None,
        },
    }


def author_kind(user: Optional[dict], agent_logins: Iterable[str]) -> str:
    login = (user or {}).get("login") or ""
    if login in set(agent_logins):
        return "agent"
    if (user or {}).get("type") == "Bot" or login.endswith("[bot]"):
        return "bot"
    return "human"


def pr_event(repo: str, p: dict, agent_logins: Iterable[str]) -> dict:
    title, body = p.get("title") or "", p.get("body") or ""
    created, merged = ts(p.get("created_at")), ts(p.get("merged_at"))
    revert = REVERTS.search(body)
    revert_of = int(revert.group(1)) if revert else None
    if revert_of is None and title.lower().startswith("revert"):
        m = TITLE_REF.search(title)
        revert_of = int(m.group(1)) if m else None
    refs = sorted({int(n) for n in ANY_REF.findall(f"{title}\n{body}")} - {p.get("number")})
    kind = CHANGE_TYPE.match(title.strip())
    state = "merged" if merged else ("closed" if p.get("state") == "closed" else "open")
    return {
        "event": "vcs.change",
        "id": f"{repo}/pr/{p['number']}",
        "time": p.get("updated_at") or p.get("created_at"),
        "attributes": {
            "vcs.repository.name": repo,
            "vcs.change.id": p["number"],
            "vcs.change.title": title[:200],
            "vcs.change.state": state,
            "vcs.change.url.full": p.get("html_url"),
            "vcs.ref.head.name": (p.get("head") or {}).get("ref"),
            "vcs.ref.base.name": (p.get("base") or {}).get("ref"),
            "aa.author.kind": author_kind(p.get("user"), agent_logins),
            "aa.author.login": (p.get("user") or {}).get("login")
            if author_kind(p.get("user"), agent_logins) != "human"
            else None,
            "aa.created_at": p.get("created_at"),
            "aa.merged_at": p.get("merged_at"),
            "aa.merge_commit": p.get("merge_commit_sha") if merged else None,
            "aa.change_type": (kind.group(0).lower() if kind else ("revert" if revert_of else None)),
            "aa.revert_of": revert_of,
            "aa.references": refs[:20],
            "aa.docs_only": None,
            "vcs.change.time_to_merge": round((merged - created).total_seconds()) if merged and created else None,
        },
    }


def deployment_event(repo: str, d: dict) -> dict:
    return {
        "event": "deployment",
        "id": f"{repo}/deployment/{d['id']}",
        "time": d.get("created_at"),
        "attributes": {
            "vcs.repository.name": repo,
            "deployment.id": d["id"],
            "deployment.environment.name": d.get("environment"),
            "deployment.name": d.get("task"),
            "vcs.ref.head.revision": d.get("sha"),
            "aa.created_at": d.get("created_at"),
            "aa.creator.kind": author_kind(d.get("creator"), ()),
        },
    }


# ── the event store ─────────────────────────────────────────────────────────────────────────────────────────────


class Store:
    def __init__(self, events: Optional[dict] = None, state: Optional[dict] = None):
        self.events: dict[str, dict] = events or {}
        self.state: dict = state or {"repos": {}}
        self.touched_days: set[str] = set()

    @classmethod
    def load(cls, folder: Path) -> "Store":
        events: dict[str, dict] = {}
        p = folder / STORE_EVENTS
        if p.exists():
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        e = json.loads(line)
                        events[e["id"]] = e
        sp = folder / STORE_STATE
        state = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {"repos": {}}
        return cls(events, state)

    def save(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        with gzip.open(folder / STORE_EVENTS, "wt", encoding="utf-8") as fh:
            for e in sorted(self.events.values(), key=lambda e: (e["time"] or "", e["id"])):
                fh.write(json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n")
        (folder / STORE_STATE).write_text(json.dumps(self.state, indent=1, sort_keys=True), encoding="utf-8")

    def put(self, e: dict) -> bool:
        old = self.events.get(e["id"])
        if old is not None and e["event"] == "vcs.change" and old["attributes"].get("aa.docs_only") is not None:
            e["attributes"]["aa.docs_only"] = old["attributes"]["aa.docs_only"]
        if old == e:
            return False
        self.events[e["id"]] = e
        if e.get("time"):
            self.touched_days.add(e["time"][:10])
        return True

    def repo_state(self, repo: str) -> dict:
        return self.state.setdefault("repos", {}).setdefault(repo, {})

    def of(self, kind: str, repo: Optional[str] = None) -> list[dict]:
        return [
            e
            for e in self.events.values()
            if e["event"] == kind and (repo is None or e["attributes"]["vcs.repository.name"] == repo)
        ]

    def prune(self, keep_from: datetime) -> int:
        cut = iso(keep_from)
        old = [k for k, e in self.events.items() if (e.get("time") or "") < cut]
        for k in old:
            del self.events[k]
        return len(old)

    def day_files(self, days: Iterable[str]) -> dict[str, list[dict]]:
        want = set(days)
        out: dict[str, list[dict]] = defaultdict(list)
        for e in self.events.values():
            d = (e.get("time") or "")[:10]
            if d in want:
                out[d].append(e)
        return {d: sorted(v, key=lambda e: (e["time"], e["id"])) for d, v in out.items()}


# ── collection ──────────────────────────────────────────────────────────────────────────────────────────────────


def _days(first: date, last: date) -> list[date]:
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def fetch_run_day(gh: GitHub, cfg: dict, store: Store, repo: str, day: date) -> int:
    n = 0
    for r in gh.pages(
        f"repos/{cfg['org']}/{repo}/actions/runs", {"created": day.isoformat()}, key="workflow_runs", max_pages=10
    ):
        n += store.put(run_event(repo, r))
    return n


def collect(cfg: dict, store: Store, gh: GitHub, now: datetime) -> dict:
    """Fetch what changed since the last run (newest first), then backfill older days within the budget."""
    today = now.date()
    store_from = today - timedelta(days=cfg["store_days"])
    report: dict[str, Any] = {"repos": {}, "stopped": None, "errors": []}
    repos = [a["repo"] for a in cfg["apps"]]
    apps_by_repo = {a["repo"]: a for a in cfg["apps"]}
    env = cfg["environment"]

    def phase(name: str, fn: Callable[[], None]) -> bool:
        if report["stopped"]:
            return False
        try:
            fn()
        except BudgetSpent as e:
            report["stopped"] = f"{name}: {e}"
            return False
        return True

    for repo in repos:
        report["repos"][repo] = {"read": False}

    # 1. recent workflow runs (created in the last runs_overlap_days days: re-runs and late completions)
    def recent_runs():
        for repo in repos:
            st = store.repo_state(repo)
            last = date.fromisoformat(st["runs_forward_day"]) if st.get("runs_forward_day") else None
            first = max(store_from, (last or today) - timedelta(days=cfg["runs_overlap_days"]))
            try:
                for day in _days(first, today):
                    fetch_run_day(gh, cfg, store, repo, day)
                st["runs_forward_day"] = today.isoformat()
                st.setdefault("runs_complete_since", first.isoformat())
                report["repos"][repo]["read"] = True
            except ReadError as e:
                report["errors"].append(f"{repo}: {e}")

    # 2. pull requests closed since the cursor (sorted by update, newest first)
    def recent_prs():
        for repo in repos:
            st = store.repo_state(repo)
            cursor = ts(st.get("prs_cursor")) or datetime.combine(store_from, datetime.min.time(), timezone.utc)
            newest = cursor
            try:
                for p in gh.pages(
                    f"repos/{cfg['org']}/{repo}/pulls",
                    {"state": "closed", "sort": "updated", "direction": "desc"},
                    max_pages=20,
                ):
                    upd = ts(p.get("updated_at"))
                    if upd and upd < cursor - timedelta(hours=1):
                        break
                    newest = max(newest, upd or newest)
                    if p.get("merged_at"):
                        store.put(pr_event(repo, p, cfg.get("agent_logins", ())))
                st["prs_cursor"] = iso(newest)
                report["repos"][repo]["read"] = True
            except ReadError as e:
                report["errors"].append(f"{repo} pull requests: {e}")

    # 3. GitHub Deployments of the environment (newest first, until a known one)
    def recent_deployments():
        for repo in repos:
            st = store.repo_state(repo)
            known = st.get("deployments_max_id") or 0
            top = known
            try:
                for d in gh.pages(f"repos/{cfg['org']}/{repo}/deployments", {"environment": env}, max_pages=10):
                    if d["id"] <= known or (ts(d.get("created_at")) or now).date() < store_from:
                        break
                    top = max(top, d["id"])
                    store.put(deployment_event(repo, d))
                st["deployments_max_id"] = top
            except ReadError as e:
                report["errors"].append(f"{repo} deployments: {e}")

    # 4. jobs (all attempts) of completed runs not read yet: deploy runs first, then CI, then the rest (jobs_days)
    def spent(share: float) -> bool:
        """The soft limit of a phase: `share` of the run's budget is used (later phases still get the rest)."""
        return gh.used >= share * gh.budget

    def jobs(max_tier: int = 2, share: float = 1.0):
        have = {
            (
                e["attributes"]["vcs.repository.name"],
                e["attributes"]["cicd.pipeline.run.id"],
                e["attributes"]["aa.run_attempt"],
            )
            for e in store.of("aa.jobs.read")
        }
        jobs_from = iso(now - timedelta(days=cfg["jobs_days"]))

        def rank(e):
            a = e["attributes"]
            app = apps_by_repo[a["vcs.repository.name"]]
            tier = (
                0
                if a["aa.workflow.file"] in app["deploy_workflows"]
                else (1 if a["aa.workflow.file"] in app["ci_workflows"] else 2)
            )
            return (tier, -(ts(e["time"]) or now).timestamp())

        todo = [
            e
            for e in store.of("cicd.pipeline.run")
            if e["attributes"]["cicd.pipeline.run.state"] == "finalizing"
            and (
                e["attributes"]["vcs.repository.name"],
                e["attributes"]["cicd.pipeline.run.id"],
                e["attributes"]["aa.run_attempt"],
            )
            not in have
            and rank(e)[0] <= max_tier
            and (rank(e)[0] == 0 or (e["time"] or "") >= jobs_from)
        ]
        for e in sorted(todo, key=rank):
            if spent(share):
                return
            a = e["attributes"]
            try:
                for j in gh.pages(
                    f"repos/{cfg['org']}/{a['vcs.repository.name']}/actions/runs/{a['cicd.pipeline.run.id']}/jobs",
                    {"filter": "all"},
                    key="jobs",
                    max_pages=5,
                ):
                    store.put(job_event(a["vcs.repository.name"], e, j))
                # the jobs of this attempt are read (also when the run had none: a workflow skipped as a whole)
                store.put(
                    {
                        "event": "aa.jobs.read",
                        "id": f"{a['vcs.repository.name']}/jobsread/{a['cicd.pipeline.run.id']}",
                        "time": e["time"],
                        "attributes": {
                            "vcs.repository.name": a["vcs.repository.name"],
                            "cicd.pipeline.run.id": a["cicd.pipeline.run.id"],
                            "aa.run_attempt": a["aa.run_attempt"],
                        },
                    }
                )
            except ReadError as err:
                report["errors"].append(f"jobs of run {a['cicd.pipeline.run.id']}: {err}")

    # 5. files of merged pull requests (docs-only test) for apps that skip docs-only changes
    def pr_files(share: float = 1.0):
        todo = [
            e
            for e in store.of("vcs.change")
            if e["attributes"]["aa.docs_only"] is None
            and apps_by_repo[e["attributes"]["vcs.repository.name"]].get("no_deploy_paths")
        ]
        for e in sorted(todo, key=lambda e: e["attributes"]["aa.merged_at"] or "", reverse=True):
            if spent(share):
                return
            a = e["attributes"]
            app = apps_by_repo[a["vcs.repository.name"]]
            try:
                files = [
                    f.get("filename") or ""
                    for f in gh.pages(
                        f"repos/{cfg['org']}/{a['vcs.repository.name']}/pulls/{a['vcs.change.id']}/files",
                        {},
                        max_pages=3,
                    )
                ]
            except ReadError as err:
                report["errors"].append(f"files of PR {a['vcs.change.id']}: {err}")
                continue
            a["aa.docs_only"] = bool(files) and all(
                any(fnmatch.fnmatch(f, pat) for pat in app["no_deploy_paths"]) for f in files
            )
            store.touched_days.add((e["time"] or "")[:10])

    # 6. backfill older run days, newest missing day first, one day of each repo in turn (no repo starves)
    def backfill(share: float = 1.0):
        failed_repos: set[str] = set()
        while not spent(share):
            moved = False
            for repo in repos:
                st = store.repo_state(repo)
                since = date.fromisoformat(st.get("runs_complete_since") or today.isoformat())
                if repo in failed_repos or since <= store_from or spent(share):
                    continue
                day = since - timedelta(days=1)
                try:
                    fetch_run_day(gh, cfg, store, repo, day)
                except ReadError as e:
                    report["errors"].append(f"{repo} runs of {day}: {e}")
                    failed_repos.add(repo)
                    continue
                st["runs_complete_since"] = day.isoformat()
                moved = True
            if not moved:
                return

    # Newest first; the soft shares keep a cold store from spending a whole run on one phase.
    for name, fn in (
        ("runs", recent_runs),
        ("pull requests", recent_prs),
        ("deployments", recent_deployments),
        ("jobs of deploy runs", lambda: jobs(max_tier=0)),
        ("backfill", lambda: backfill(share=0.6)),
        ("pull request files", lambda: pr_files(share=0.8)),
        ("jobs", jobs),
    ):
        phase(name, fn)

    store.prune(datetime.combine(store_from, datetime.min.time(), timezone.utc))
    for repo in repos:
        st = store.repo_state(repo)
        report["repos"][repo]["complete_since"] = st.get("runs_complete_since")
    report["requests"] = gh.used
    report["rate_limit_remaining"] = gh.remaining
    return report


# ── metrics ─────────────────────────────────────────────────────────────────────────────────────────────────────


def _attr(e: dict, k: str) -> Any:
    return e["attributes"].get(k)


def latest_attempt(jobs: list[dict]) -> list[dict]:
    attempt = max([_attr(j, "aa.run_attempt") or 1 for j in jobs] or [1])
    return [j for j in jobs if (_attr(j, "aa.run_attempt") or 1) == attempt]


def run_outcome(app: dict, run: dict, jobs: Optional[list[dict]]) -> str:
    """success | verify_failed | deploy_failed | not_deployed | cancelled | running | unclassified.

    `jobs` None = not read yet (unclassified); [] = read, the run had no job."""
    result = _attr(run, "cicd.pipeline.result")
    if _attr(run, "cicd.pipeline.run.state") != "finalizing" or result is None:
        return "running"
    if result in ("cancellation", "skip") and not jobs:
        return "cancelled"
    if jobs is None:
        return "unclassified"
    latest = latest_attempt(jobs)
    dep = re.compile(app["deploy_job"])
    ver = re.compile(app["verify_job"]) if app.get("verify_job") else None
    deploy_jobs = [j for j in latest if dep.search(_attr(j, "cicd.pipeline.task.name") or "")]
    verify_jobs = [
        j
        for j in latest
        if ver
        and ver.search(_attr(j, "cicd.pipeline.task.name") or "")
        and _attr(j, "cicd.pipeline.task.run.result") not in (None, "skip")
    ]
    if any(_attr(j, "cicd.pipeline.task.run.result") in RED for j in deploy_jobs):
        return "deploy_failed"
    if not any(_attr(j, "cicd.pipeline.task.run.result") == "success" for j in deploy_jobs):
        return "cancelled" if result == "cancellation" else "not_deployed"
    if any(_attr(j, "cicd.pipeline.task.run.result") in RED for j in verify_jobs):
        return "verify_failed"
    return "success"


def group_outcome(outcomes: list[str]) -> str:
    """One app deploy from its runs: the worst run decides (a failed deploy job, then a red verify)."""
    return next((o for o in ("deploy_failed", "verify_failed", "unclassified") if o in outcomes), "success")


def deploy_groups(cfg: dict, app: dict, runs: list[dict], jobs_by_run: dict, deployments: list[dict]) -> list[dict]:
    """Deploy runs of the app -> app deploys (consecutive runs of one commit grouped), oldest first."""
    rows = []
    for r in runs:
        a = r["attributes"]
        if (
            a["aa.workflow.file"] not in app["deploy_workflows"]
            or a["vcs.ref.head.name"] != app["default_branch"]
            or a["aa.trigger"] not in cfg["deploy_triggers"]
        ):
            continue
        jobs = jobs_by_run.get(a["cicd.pipeline.run.id"])
        outcome = run_outcome(app, r, jobs)
        if outcome in ("running", "cancelled", "not_deployed"):
            continue
        dep = re.compile(app["deploy_job"])
        ver = re.compile(app["verify_job"]) if app.get("verify_job") else None
        latest = latest_attempt(jobs or [])
        dj = [
            ts(_attr(j, "end_time"))
            for j in latest
            if dep.search(_attr(j, "cicd.pipeline.task.name") or "") and _attr(j, "end_time")
        ]
        vj = [
            ts(_attr(j, "end_time"))
            for j in latest
            if ver
            and ver.search(_attr(j, "cicd.pipeline.task.name") or "")
            and _attr(j, "end_time")
            and _attr(j, "cicd.pipeline.task.run.result") not in (None, "skip")
        ]
        start, end = ts(a["start_time"]), ts(a["end_time"])
        deployed = max(dj) if dj else end
        rows.append(
            {
                "sha": a["vcs.ref.head.revision"],
                "start": start,
                "end": end,
                "deployed": deployed,
                "verified": (max(vj) if vj else deployed) if outcome == "success" else None,
                "verify_failed_at": max(vj) if vj and outcome == "verify_failed" else None,
                "outcome": outcome,
                "run": {
                    "id": a["cicd.pipeline.run.id"],
                    "url": a["cicd.pipeline.run.url.full"],
                    "workflow": a["cicd.pipeline.name"],
                    "outcome": outcome,
                    "attempt": a["aa.run_attempt"],
                },
            }
        )
    rows.sort(key=lambda x: x["start"] or datetime.min.replace(tzinfo=timezone.utc))
    groups: list[dict] = []
    for row in rows:
        g = groups[-1] if groups else None
        # runs of one commit that overlap (the services of one push) are one deploy; a later run of the same commit
        # (a retry, a manual redeploy) is its own deploy, marked `redeploy` below
        if g and g["sha"] == row["sha"] and row["start"] and g["end"] and row["start"] <= g["end"]:
            g["runs"].append(row["run"])
            g["start"] = min(g["start"], row["start"]) if g["start"] and row["start"] else g["start"] or row["start"]
            for k in ("end", "deployed"):
                g[k] = max(x for x in (g[k], row[k]) if x) if (g[k] or row[k]) else None
            g["verify_failed_at"] = g["verify_failed_at"] or row["verify_failed_at"]
            g["outcomes"].append(row["outcome"])
            g["verified_parts"].append(row["verified"])
        else:
            groups.append(
                {
                    "sha": row["sha"],
                    "start": row["start"],
                    "end": row["end"],
                    "deployed": row["deployed"],
                    "verify_failed_at": row["verify_failed_at"],
                    "runs": [row["run"]],
                    "outcomes": [row["outcome"]],
                    "verified_parts": [row["verified"]],
                }
            )
    for i, g in enumerate(groups):
        g["outcome"] = group_outcome(g["outcomes"])
        g["redeploy"] = i > 0 and groups[i - 1]["sha"] == g["sha"]
        g["verified"] = (
            max(v for v in g["verified_parts"] if v) if g["outcome"] == "success" and any(g["verified_parts"]) else None
        )
        g["deployments"] = sum(
            1
            for d in deployments
            if _attr(d, "vcs.ref.head.revision") == g["sha"]
            and g["start"]
            and g["end"]
            and g["start"] - timedelta(minutes=2) <= (ts(_attr(d, "aa.created_at")) or g["start"]) <= g["end"]
        )
        g["failed"], g["rework"] = [], []
        if g["outcome"] == "verify_failed":
            g["failed"].append("verify_red")
        if g["outcome"] == "deploy_failed":
            g["failed"].append("deploy_job_failed")
    return groups


def pr_of_branch(by_head: dict, branch: Optional[str], at: Optional[datetime]) -> Optional[int]:
    """The merged PR whose head branch is `branch` and that was open at `at`."""
    for opened, merged_at, number in by_head.get(branch or "", ()):
        if opened and merged_at and at and opened <= at <= merged_at:
            return number
    return None


def attach_changes(
    cfg: dict, app: dict, groups: list[dict], prs: list[dict], runs: list[dict], since: Optional[datetime] = None
) -> list[dict]:
    """Per merged pull request: its lead-time points, the deploy that first shipped it and the first green one.

    A pull request merged before `since` (the start of the complete run history) is not matched to a deploy: the
    deploys between its merge and `since` are not in the store, so the first stored deploy would claim it wrongly."""
    merged = [p for p in prs if _attr(p, "aa.merged_at") and _attr(p, "vcs.ref.base.name") == app["default_branch"]]
    merge_time = {
        _attr(p, "aa.merge_commit"): ts(_attr(p, "aa.merged_at")) for p in merged if _attr(p, "aa.merge_commit")
    }
    for g in groups:
        g["merge_time"] = merge_time.get(g["sha"]) or g["start"]
    # rollbacks: a deploy of a commit that was live earlier while another commit is live
    live, seen, live_group = None, set(), None
    for g in groups:
        if g["outcome"] == "unclassified":
            continue
        if live is not None and g["sha"] != live and g["sha"] in seen:
            g["rework"].append("rollback")
            g["rollback"] = True
            if live_group is not None and "rolled_back" not in live_group["failed"]:
                live_group["failed"].append("rolled_back")
                live_group.setdefault("repaired_by", []).append(g)
        if live is not None:
            seen.add(live)
        live, live_group = g["sha"], g
    ci = set(app["ci_workflows"])
    # GitHub empties a run's pull_requests list once the branch is gone: fall back to the head branch of a merged PR
    by_head: dict[str, list[tuple]] = defaultdict(list)
    for p in merged:
        by_head[_attr(p, "vcs.ref.head.name") or ""].append(
            (ts(_attr(p, "aa.created_at")), ts(_attr(p, "aa.merged_at")), _attr(p, "vcs.change.id"))
        )
    green: dict[int, datetime] = {}
    queued: dict[int, datetime] = {}
    queue_branches: dict[int, set] = defaultdict(set)
    for r in runs:
        a = r["attributes"]
        m = QUEUE_BRANCH.match(a["vcs.ref.head.name"] or "")
        if m and a["aa.trigger"] == "merge_group":
            n = int(m.group(1))
            t = ts(a["aa.created_at"])
            if t and (n not in queued or t < queued[n]):
                queued[n] = t
            queue_branches[n].add(a["vcs.ref.head.name"])
        if (
            a["aa.workflow.file"] in ci
            and a["aa.trigger"] in ("pull_request", "pull_request_target")
            and a["cicd.pipeline.result"] == "success"
        ):
            t = ts(a["end_time"])
            n = a["vcs.change.id"] or pr_of_branch(by_head, a["vcs.ref.head.name"], ts(a["aa.created_at"]))
            if n and t and (n not in green or t < green[n]):
                green[n] = t
    ordered = [g for g in groups if g["outcome"] != "unclassified" and not g.get("rollback")]
    changes = []
    for p in merged:
        a = p["attributes"]
        n, m_at = a["vcs.change.id"], ts(a["aa.merged_at"])
        known = since is None or m_at >= since
        shipped = next((g for g in ordered if g["merge_time"] and g["merge_time"] >= m_at), None) if known else None
        good = (
            next(
                (g for g in ordered if g["outcome"] == "success" and g["merge_time"] and g["merge_time"] >= m_at), None
            )
            if known
            else None
        )
        excluded = "bot" if a["aa.author.kind"] == "bot" else ("docs_only" if a["aa.docs_only"] else None)
        ch = {
            "number": n,
            "title": a["vcs.change.title"],
            "url": a["vcs.change.url.full"],
            "kind": a["aa.author.kind"],
            "login": a.get("aa.author.login"),
            "type": a["aa.change_type"],
            "revert_of": a["aa.revert_of"],
            "references": a["aa.references"] or [],
            "excluded": excluded,
            "opened": ts(a["aa.created_at"]),
            "first_green": green.get(n),
            "queued": queued.get(n),
            "merged": m_at,
            "deployed": good["deployed"] if good else None,
            "verified": good["verified"] if good else None,
            "shipped_in": shipped,
            "green_in": good,
            "queue_attempts": len(queue_branches.get(n, ())),
        }
        changes.append(ch)
        if shipped is not None:
            shipped.setdefault("changes", []).append(ch)
    by_number = {c["number"]: c for c in changes}
    window = timedelta(hours=cfg["rework_hours"])
    for c in changes:
        target = None
        reason = None
        if c["type"] == "revert" or c["revert_of"]:
            target, reason = by_number.get(c["revert_of"]), "reverted"
        elif c["type"] == "fix":
            cands = [
                by_number[r]
                for r in c["references"]
                if r in by_number
                and by_number[r]["merged"]
                and by_number[r]["merged"] < c["merged"]
                and by_number[r]["shipped_in"] is not None
            ]
            cands = [x for x in cands if c["merged"] - (x["shipped_in"]["deployed"] or x["merged"]) <= window]
            target, reason = (max(cands, key=lambda x: x["merged"]), "hotfix") if cands else (None, None)
        if target is None or target["shipped_in"] is None:
            continue
        g = target["shipped_in"]
        when = g["deployed"] or g["end"]
        if reason == "reverted" and when and c["merged"] - when > window:
            continue
        if reason not in g["failed"]:
            g["failed"].append(reason)
        g.setdefault("repaired_by", []).append(c)
        if c["shipped_in"] is not None and reason not in c["shipped_in"]["rework"]:
            c["shipped_in"]["rework"].append(reason)
    return changes


def recovery(groups: list[dict]) -> None:
    """Recovery time of each failed deploy: to the first green deploy that repairs it."""
    for i, g in enumerate(groups):
        if not g["failed"]:
            continue
        failed_at = g["verify_failed_at"] or g["end"] or g["deployed"]
        g["failed_at"] = failed_at
        cands = []
        if set(g["failed"]) & {"verify_red", "deploy_job_failed"}:
            nxt = next((x for x in groups[i + 1 :] if x["outcome"] == "success"), None)
            if nxt:
                cands.append(nxt["verified"] or nxt["end"])
        for rep in g.get("repaired_by", []):
            if isinstance(rep, dict) and "outcomes" in rep:  # a rollback deploy
                if rep["outcome"] == "success":
                    cands.append(rep["verified"] or rep["end"])
            elif isinstance(rep, dict) and rep.get("green_in") is not None:
                cands.append(rep["green_in"]["verified"] or rep["green_in"]["end"])
        cands = [c for c in cands if c and failed_at and c >= failed_at]
        g["recovered_at"] = min(cands) if cands else None
        g["recovery_h"] = hours(failed_at, g["recovered_at"]) if g["recovered_at"] else None


SEGMENTS = (
    ("to_first_green", "opened", "first_green"),
    ("to_queue", "first_green", "queued"),
    ("to_merge", "queued", "merged"),
    ("to_deploy", "merged", "deployed"),
    ("to_verify", "deployed", "verified"),
)
POINTS = ("opened", "first_green", "queued", "merged", "deployed", "verified")


def segments_of(c: dict) -> dict[str, float]:
    """Hours per segment; a missing point folds its segment into the next one that has both ends."""
    out: dict[str, float] = {}
    prev = c["opened"]
    for name, _a, b in SEGMENTS:
        end = c[b]
        if end is None or prev is None:
            continue
        out[name] = hours(prev, end) or 0.0
        prev = end
    return out


def in_range(t: Optional[datetime], a: datetime, b: datetime) -> bool:
    return t is not None and a <= t < b


def dora_block(groups: list[dict], changes: list[dict], a: datetime, b: datetime) -> dict:
    # a redeploy of the commit already live is not a change: left out of the counts (it can still be a recovery)
    reached = [g for g in groups if g["outcome"] != "unclassified" and not g["redeploy"] and in_range(g["start"], a, b)]
    green = [g for g in reached if g["outcome"] == "success"]
    failed = [g for g in reached if g["failed"]]
    rework = [g for g in reached if g["rework"]]
    recovered = [g["recovery_h"] for g in failed if g.get("recovery_h") is not None]
    lt = [c for c in changes if not c["excluded"] and c["verified"] and in_range(c["merged"], a, b)]
    weeks = max((b - a).total_seconds() / (7 * 86400), 1e-9)
    reasons: dict[str, int] = defaultdict(int)
    for g in failed:
        for r in g["failed"]:
            reasons[r] += 1
    return {
        "deployment_frequency": {
            "value": round(len(green) / weeks, 2),
            "unit": "per_week",
            "n": len(green),
            "attempts": len(reached),
        },
        "lead_time": {
            "p50_h": percentile([hours(c["opened"], c["verified"]) for c in lt], 50),
            "p90_h": percentile([hours(c["opened"], c["verified"]) for c in lt], 90),
            "n": len(lt),
        },
        "change_failure_rate": {
            "value": round(len(failed) / len(reached), 4) if reached else None,
            "n": len(reached),
            "failed": len(failed),
            "by_reason": dict(sorted(reasons.items())),
        },
        "recovery_time": {
            "p50_h": percentile(recovered, 50),
            "p90_h": percentile(recovered, 90),
            "n": len(recovered),
            "open": sum(1 for g in failed if g.get("recovery_h") is None),
        },
        "rework_rate": {
            "value": round(len(rework) / len(reached), 4) if reached else None,
            "n": len(reached),
            "rework": len(rework),
        },
    }


def lead_segments(changes: list[dict], a: datetime, b: datetime) -> list[dict]:
    lt = [c for c in changes if not c["excluded"] and c["verified"] and in_range(c["merged"], a, b)]
    out = []
    for name, _x, _y in SEGMENTS:
        vals = [s[name] for s in (segments_of(c) for c in lt) if name in s]
        out.append({"segment": name, "p50_h": percentile(vals, 50), "p90_h": percentile(vals, 90), "n": len(vals)})
    return out


def run_minutes(run: dict, jobs: Optional[list[dict]]) -> tuple[int, bool]:
    """Actions minutes of a run (each job rounded up to the minute, every attempt) and whether its jobs were read; a
    run whose jobs are not read yet (or that had none) counts its wall-clock time."""
    if jobs:
        return sum(math.ceil((_attr(j, "aa.duration_s") or 0) / 60) for j in jobs), True
    return math.ceil((_attr(run, "aa.duration_s") or 0) / 60), jobs is not None


def ci_block(
    cfg: dict, app: dict, runs: list[dict], jobs_by_run: dict, a: datetime, b: datetime, now: datetime
) -> dict:
    done = [r for r in runs if _attr(r, "cicd.pipeline.result") and in_range(ts(_attr(r, "end_time")), a, b)]
    by_wf: dict[str, list[dict]] = defaultdict(list)
    for r in done:
        by_wf[_attr(r, "cicd.pipeline.name")].append(r)
    workflows = []
    total_min, covered = 0, 0
    for name, rs in by_wf.items():
        judged = [r for r in rs if _attr(r, "cicd.pipeline.result") not in ("cancellation", "skip")]
        fails = [r for r in judged if _attr(r, "cicd.pipeline.result") in RED]
        durs = [_attr(r, "aa.duration_s") for r in judged if _attr(r, "aa.duration_s") is not None]
        mins = 0
        for r in rs:
            m, known = run_minutes(r, jobs_by_run.get(_attr(r, "cicd.pipeline.run.id")))
            mins += m
            covered += known
        total_min += mins
        last = max(rs, key=lambda r: _attr(r, "end_time") or "")
        workflows.append(
            {
                "name": name,
                "file": _attr(rs[0], "aa.workflow.file"),
                "runs": len(judged),
                "failures": len(fails),
                "failure_rate": round(len(fails) / len(judged), 4) if judged else None,
                "p50_s": percentile(durs, 50),
                "p95_s": percentile(durs, 95),
                "reruns": sum(1 for r in rs if (_attr(r, "aa.run_attempt") or 1) > 1),
                "minutes": mins,
                "kind": "deploy"
                if _attr(rs[0], "aa.workflow.file") in app["deploy_workflows"]
                else ("ci" if _attr(rs[0], "aa.workflow.file") in app["ci_workflows"] else "other"),
                "last_url": _attr(last, "cicd.pipeline.run.url.full"),
                "last_result": _attr(last, "cicd.pipeline.result"),
            }
        )
    workflows.sort(key=lambda w: (-w["runs"], w["name"]))
    slowest = max(
        (w for w in workflows if w["kind"] in ("ci", "deploy") and w["p95_s"] is not None),
        key=lambda w: w["p95_s"],
        default=None,
    )
    # main: the CI and deploy workflows on the default branch
    watch = set(app["ci_workflows"]) | set(app["deploy_workflows"])
    main_runs = sorted(
        [
            r
            for r in runs
            if _attr(r, "aa.workflow.file") in watch
            and _attr(r, "vcs.ref.head.name") == app["default_branch"]
            and _attr(r, "aa.trigger") in cfg["main_triggers"]
            and _attr(r, "cicd.pipeline.result") not in (None, "cancellation", "skip")
        ],
        key=lambda r: _attr(r, "end_time") or "",
    )
    state, red_since, red_url = "unknown", None, None
    per_wf: dict[str, list[dict]] = defaultdict(list)
    for r in main_runs:
        per_wf[_attr(r, "aa.workflow.file")].append(r)
    if per_wf:
        state = "green"
        for rs in per_wf.values():
            if _attr(rs[-1], "cicd.pipeline.result") in RED:
                state = "red"
                streak = rs[-1]
                for r in reversed(rs):
                    if _attr(r, "cicd.pipeline.result") not in RED:
                        break
                    streak = r
                t = ts(_attr(streak, "start_time"))
                if red_since is None or (t and t < red_since):
                    red_since, red_url = t, _attr(rs[-1], "cicd.pipeline.run.url.full")
    in_win = [r for r in main_runs if in_range(ts(_attr(r, "end_time")), a, b)]
    main_fail = [r for r in in_win if _attr(r, "cicd.pipeline.result") in RED]
    return {
        "workflows": workflows[: cfg["list_cap"]],
        "slowest": {"name": slowest["name"], "p95_s": slowest["p95_s"], "n": slowest["runs"]} if slowest else None,
        "main": {
            "state": state,
            "red_since": iso(red_since),
            "red_hours": hours(red_since, now) if red_since else None,
            "url": red_url,
            "failure_rate": round(len(main_fail) / len(in_win), 4) if in_win else None,
            "n": len(in_win),
        },
        "reruns": sum(w["reruns"] for w in workflows),
        "minutes": {"total": total_min, "coverage": round(covered / len(done), 4) if done else None, "n": len(done)},
    }


def flaky_block(cfg: dict, runs: list[dict], jobs_by_run: dict, a: datetime, b: datetime) -> list[dict]:
    """Jobs that failed and then passed on the same commit (a re-run attempt, or a later run of that workflow)."""
    flips: dict[tuple, dict] = {}
    seq: dict[tuple, list[tuple]] = defaultdict(list)
    for r in runs:
        for j in jobs_by_run.get(_attr(r, "cicd.pipeline.run.id")) or []:
            res = _attr(j, "cicd.pipeline.task.run.result")
            if res not in ("success",) + RED:
                continue
            key = (
                _attr(r, "cicd.pipeline.name"),
                _attr(j, "cicd.pipeline.task.name"),
                _attr(r, "vcs.ref.head.revision"),
            )
            seq[key].append((_attr(j, "end_time") or "", res, _attr(j, "cicd.pipeline.task.run.url.full")))
    for (wf, job, _sha), items in seq.items():
        items.sort()
        for (_t1, r1, _u1), (t2, r2, u2) in zip(items, items[1:], strict=False):
            if r1 in RED and r2 == "success" and in_range(ts(t2), a, b):
                f = flips.setdefault((wf, job), {"workflow": wf, "job": job, "flips": 0, "last_at": None, "url": None})
                f["flips"] += 1
                if (f["last_at"] or "") < t2:
                    f["last_at"], f["url"] = t2, u2
    return sorted(flips.values(), key=lambda f: (-f["flips"], f["workflow"], f["job"]))[: cfg["list_cap"]]


def queue_block(changes: list[dict], a: datetime, b: datetime) -> dict:
    qs = [c for c in changes if c["queued"] and in_range(c["merged"], a, b)]
    waits = [hours(c["queued"], c["merged"]) for c in qs]
    return {
        "wait_p50_h": percentile(waits, 50),
        "wait_p95_h": percentile(waits, 95),
        "n": len(qs),
        "ejections": sum(max(c["queue_attempts"] - 1, 0) for c in qs),
    }


def group_row(g: dict) -> dict:
    return {
        "sha": g["sha"],
        "started_at": iso(g["start"]),
        "deployed_at": iso(g["deployed"]),
        "finished_at": iso(g["end"]),
        "verified_at": iso(g["verified"]),
        "outcome": g["outcome"],
        "failed": list(g["failed"]),
        "rework": list(g["rework"]),
        "redeploy": g["redeploy"],
        "failed_at": iso(g.get("failed_at")),
        "recovered_at": iso(g.get("recovered_at")),
        "recovery_h": g.get("recovery_h"),
        "deployment_records": g["deployments"],
        "runs": g["runs"],
        "changes": [c["number"] for c in g.get("changes", [])][:50],
    }


def change_row(c: dict) -> dict:
    return {
        "number": c["number"],
        "title": c["title"],
        "url": c["url"],
        "kind": c["kind"],
        "login": c["login"],
        "excluded": c["excluded"],
        "merged_at": iso(c["merged"]),
        "lead_time_h": hours(c["opened"], c["verified"]) if c["verified"] else None,
        "segments": segments_of(c) if c["verified"] else {},
    }


def app_summary(cfg: dict, app: dict, store: Store, now: datetime) -> dict:
    repo = app["repo"]
    runs = store.of("cicd.pipeline.run", repo)
    jobs_by_run: dict[Any, list[dict]] = {}
    for m in store.of("aa.jobs.read", repo):
        jobs_by_run.setdefault(_attr(m, "cicd.pipeline.run.id"), [])
    for j in store.of("cicd.pipeline.task.run", repo):
        jobs_by_run.setdefault(_attr(j, "cicd.pipeline.run.id"), []).append(j)
    prs = store.of("vcs.change", repo)
    deps = [d for d in store.of("deployment", repo) if _attr(d, "deployment.environment.name") == cfg["environment"]]
    groups = deploy_groups(cfg, app, runs, jobs_by_run, deps)
    st = store.repo_state(repo)
    # the run history is complete from this day on; a window that starts earlier is measured from it (n says how much)
    cs = ts(f"{st['runs_complete_since']}T00:00:00Z") if st.get("runs_complete_since") else now
    changes = attach_changes(cfg, app, groups, prs, runs, since=cs)
    recovery(groups)

    def clip(x: datetime) -> datetime:
        return min(max(x, cs), now)

    req_a, b = now - timedelta(days=cfg["headline_days"]), now
    a = clip(req_a)
    trend_from = datetime.combine(
        week_start(now.date()) - timedelta(weeks=cfg["trend_weeks"] - 1), datetime.min.time(), timezone.utc
    )
    weeks = []
    for i in range(cfg["trend_weeks"]):
        ws = trend_from + timedelta(weeks=i)
        we = ws + timedelta(weeks=1)
        d = dora_block(groups, changes, clip(ws), min(we, now))
        c = ci_block(cfg, app, runs, jobs_by_run, clip(ws), min(we, now), now)
        weeks.append(
            {
                "week": iso_week(ws),
                "start": ws.date().isoformat(),
                "end": (we - timedelta(days=1)).date().isoformat(),
                "partial": we > now,
                "complete": ws >= cs,
                **_flat(d),
                "main_failure_rate": c["main"]["failure_rate"],
                "main_n": c["main"]["n"],
                "ci_p95_s": c["slowest"]["p95_s"] if c["slowest"] else None,
                "minutes": c["minutes"]["total"],
            }
        )
    months = []
    first = now.date().replace(day=1)
    for i in reversed(range(cfg["trend_months"])):
        y, m = first.year, first.month - i
        while m < 1:
            y, m = y - 1, m + 12
        ms = datetime(y, m, 1, tzinfo=timezone.utc)
        me = datetime(y + (m == 12), (m % 12) + 1, 1, tzinfo=timezone.utc)
        d = dora_block(groups, changes, clip(ms), min(me, now))
        c = ci_block(cfg, app, runs, jobs_by_run, clip(ms), min(me, now), now)
        months.append(
            {
                "month": f"{y:04d}-{m:02d}",
                "start": ms.date().isoformat(),
                "end": (me - timedelta(days=1)).date().isoformat(),
                "partial": me > now,
                "complete": ms >= cs,
                **_flat(d),
                "lead_time": d["lead_time"],
                "main_failure_rate": c["main"]["failure_rate"],
                "main_n": c["main"]["n"],
                "verify": verify_block(groups, clip(ms), min(me, now)),
                "failed_deploys": [group_row(g) for g in groups if g["failed"] and in_range(g["start"], ms, me)],
            }
        )
    in_trend = [g for g in groups if in_range(g["start"], trend_from, now)]
    recent_changes = [c for c in changes if in_range(c["merged"], a, b)]
    return {
        "id": app["id"],
        "name": app["name"],
        "repo": repo,
        "environment": cfg["environment"],
        "window": {
            "start": iso(a),
            "end": iso(b),
            "days": cfg["headline_days"],
            "requested_start": iso(req_a),
            "covered_days": round((b - a).total_seconds() / 86400, 1),
        },
        "complete_since": st.get("runs_complete_since"),
        "dora": dora_block(groups, changes, a, b),
        "lead_time_segments": lead_segments(changes, a, b),
        "ci": ci_block(cfg, app, runs, jobs_by_run, a, b, now),
        "merge_queue": queue_block(changes, a, b),
        "flaky": flaky_block(cfg, runs, jobs_by_run, a, b),
        "verify": verify_block(groups, a, b),
        "deploys": [group_row(g) for g in reversed(in_trend)][: cfg["list_cap"]],
        "failed_deploys": [group_row(g) for g in reversed(in_trend) if g["failed"]][: cfg["list_cap"]],
        "changes": {
            "merged": len(recent_changes),
            "by_kind": {k: sum(1 for c in recent_changes if c["kind"] == k) for k in ("agent", "human", "bot")},
            "docs_only": sum(1 for c in recent_changes if c["excluded"] == "docs_only"),
            "awaiting_deploy": sum(1 for c in recent_changes if not c["excluded"] and not c["verified"]),
            "bot": [
                change_row(c)
                for c in sorted(recent_changes, key=lambda c: c["merged"], reverse=True)
                if c["excluded"] == "bot"
            ][: cfg["list_cap"]],
            "slowest": [
                change_row(c)
                for c in sorted(
                    (c for c in recent_changes if not c["excluded"] and c["verified"]),
                    key=lambda c: -(hours(c["opened"], c["verified"]) or 0),
                )
            ][:10],
        },
        "trend": {"weeks": weeks, "months": months},
    }


def verify_block(groups: list[dict], a: datetime, b: datetime) -> dict:
    gs = [g for g in groups if g["outcome"] in ("success", "verify_failed") and in_range(g["start"], a, b)]
    red = [g for g in gs if g["outcome"] == "verify_failed"]
    last = max(red, key=lambda g: g["start"], default=None)
    return {
        "pass_rate": round(1 - len(red) / len(gs), 4) if gs else None,
        "n": len(gs),
        "red": len(red),
        "last_red_at": iso(last["verify_failed_at"] or last["end"]) if last else None,
        "last_red_url": last["runs"][-1]["url"] if last else None,
    }


def _flat(d: dict) -> dict:
    return {
        "deploys": d["deployment_frequency"]["n"],
        "deploy_attempts": d["deployment_frequency"]["attempts"],
        "lead_time_p50_h": d["lead_time"]["p50_h"],
        "lead_time_n": d["lead_time"]["n"],
        "cfr": d["change_failure_rate"]["value"],
        "failed": d["change_failure_rate"]["failed"],
        "recovery_p50_h": d["recovery_time"]["p50_h"],
        "recovery_n": d["recovery_time"]["n"],
        "rework_rate": d["rework_rate"]["value"],
        "rework": d["rework_rate"]["rework"],
    }


def summarize(
    cfg: dict, store: Store, now: datetime, source: Optional[dict] = None, collection: Optional[dict] = None
) -> dict:
    return {
        "format": FORMAT,
        "generated_at": iso(now),
        "environment": cfg["environment"],
        "source": source or {},
        "definitions": {
            "version": DEFINITIONS_VERSION,
            "headline_days": cfg["headline_days"],
            "trend_weeks": cfg["trend_weeks"],
            "trend_months": cfg["trend_months"],
            "rework_hours": cfg["rework_hours"],
            "segments": [s[0] for s in SEGMENTS],
            "guide": "docs/guides/delivery-metrics.md",
        },
        "collection": collection or {},
        "apps": [app_summary(cfg, app, store, now) for app in cfg["apps"]],
    }


# ── S3 retention of the raw event files ─────────────────────────────────────────────────────────────────────────

EVENT_KEY = re.compile(r"events/(\d{4})/(\d{2})/(\d{2})\.ndjson$")


def expired_keys(keys: Iterable[str], today: date, days: int) -> list[str]:
    cut = today - timedelta(days=days)
    out = []
    for k in keys:
        m = EVENT_KEY.search(k.strip())
        if m and date(int(m.group(1)), int(m.group(2)), int(m.group(3))) < cut:
            out.append(k.strip())
    return out


def write_outputs(out: Path, summary: dict, day_files: dict[str, list[dict]]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    for d, events in day_files.items():
        p = out / "events" / d[:4] / d[5:7] / f"{d[8:10]}.ndjson"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "".join(json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n" for e in events), encoding="utf-8"
        )


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("collect", "summarize"):
        p = sub.add_parser(name)
        p.add_argument("--store", type=Path, required=True)
        p.add_argument("--out", type=Path, required=True)
        p.add_argument("--config", type=Path, default=CONFIG)
        p.add_argument("--now", help="ISO time (tests); default the current UTC time")
        p.add_argument("--sha", default=os.environ.get("GITHUB_SHA", ""))
        p.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    e = sub.add_parser("expired")
    e.add_argument("--keys", type=Path, required=True)
    e.add_argument("--today")
    e.add_argument("--config", type=Path, default=CONFIG)
    args = ap.parse_args(argv)
    try:
        cfg = load_config(args.config)
    except (ConfigError, OSError, ValueError) as err:
        print(f"config: {err}", file=sys.stderr)
        return 2
    if args.cmd == "expired":
        today = date.fromisoformat(args.today) if args.today else datetime.now(timezone.utc).date()
        for k in expired_keys(args.keys.read_text(encoding="utf-8").splitlines(), today, cfg["raw_retention_days"]):
            print(k)
        return 0
    now = ts(args.now) if args.now else datetime.now(timezone.utc).replace(microsecond=0)
    store = Store.load(args.store)
    report: dict = {}
    if args.cmd == "collect":
        gh = GitHub(
            urllib_transport(os.environ.get("GITHUB_TOKEN", "")), cfg["request_budget"], cfg["rate_limit_floor"]
        )
        report = collect(cfg, store, gh, now)
        store.save(args.store)
    source = {"repo": "AA-Ecosys", "sha": args.sha or None, "run_id": args.run_id or None}
    summary = summarize(cfg, store, now, source, report)
    days = store.touched_days if args.cmd == "collect" else {(e.get("time") or "")[:10] for e in store.events.values()}
    write_outputs(args.out, summary, store.day_files(days))
    print(
        json.dumps(
            {
                "requests": report.get("requests"),
                "stopped": report.get("stopped"),
                "errors": report.get("errors", [])[:10],
                "events": len(store.events),
                "day_files": len(days),
                "apps": [
                    {
                        "id": s["id"],
                        "deploys": s["dora"]["deployment_frequency"]["n"],
                        "lead_time_n": s["dora"]["lead_time"]["n"],
                        "complete_since": s["complete_since"],
                    }
                    for s in summary["apps"]
                ],
            },
            indent=1,
        )
    )
    if (
        args.cmd == "collect"
        and not any(r.get("read") for r in report.get("repos", {}).values())
        and not report.get("stopped")
    ):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
