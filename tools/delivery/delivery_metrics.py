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
  * AA-1125 (S283) adds two sections per app, same store, same bundle (format 1 stays: new keys only):
      - `queue` (apps with `merge_queue: true`): one entry per stay of a pull request in the GitHub merge queue, from
        the pull request timeline (added_to_merge_queue / removed_from_merge_queue / merged, REST, one read per
        queued pull request) and the merge_group workflow runs already stored: wait, outcome merged / ejected /
        removed, the ejection reason from the red merge_group runs, merge_group CI minutes and re-runs, and flaky
        signals (a re-run that turned green, an ejection followed by a green re-entry with no new commit).
      - `git` (every app): the default branch's commits of the last `git_days` (90) days with their files (one read
        per commit, newest first, kept: commits never change): commits per day, author kind (agent App, ci-bot,
        release-please, dependabot, other bot, person; a person's login is never stored), churn by directory and the
        top files over 30 / 90 days, merges by branch prefix, and the last `graph_commits` commits for a graph.

Budget: GITHUB_TOKEN allows 1,000 requests an hour; one run spends at most `request_budget` (apps.json) and stops
early when the rate limit runs low. A cold store fills over several runs (newest data first: recent runs, merged pull
requests, deployments, the jobs of deploy runs, then older days); `collection.repos[].complete_since` says from which
day the history is complete.

    python3 tools/delivery/delivery_metrics.py collect --store DIR --out DIR       # GITHUB_TOKEN in the environment
    python3 tools/delivery/delivery_metrics.py summarize --store DIR --out DIR     # recompute from the store, offline
    python3 tools/delivery/delivery_metrics.py expired --keys FILE [--today D]     # S3 event keys past retention

The AA-1125 knobs (git_days, git_windows, graph_commits, top_files, top_children, commit_files_cap, author_kinds,
release_title, churn_exclude) live in apps.json like the AA-1108 ones; older configs get the defaults below.

Stdlib only. Exit 0 = done (a budget stop is not an error), 1 = no repo could be read, 2 = bad usage or config.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

# AA-1135: the computation lives in delivery_engine.py (byte-copied to AA-CIS-App for the custom date range); the names
# below are re-exported so the tests and older callers keep reading them from this module.
from delivery_engine import (  # noqa: F401
    COMMIT_KINDS,
    DEFINITIONS_VERSION,
    FORMAT,
    QUEUE_BRANCH,
    RED,
    STORE_EVENTS,
    STORE_STATE,
    Store,
    _attr,
    _days,
    app_summary,
    branch_prefix,
    classify_entries,
    hours,
    iso,
    open_entry,
    percentile,
    queue_entries,
    run_outcome,
    summarize,
    ts,
)

CONFIG = Path(__file__).with_name("apps.json")
ENGINE = Path(__file__).with_name("delivery_engine.py")
API = "https://api.github.com"
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
CONFIG_DEFAULTS: dict[str, Any] = {
    "git_days": 90,
    "git_windows": [30, 90],
    "graph_commits": 50,
    "top_files": 30,
    "top_children": 10,
    "commit_files_cap": 300,
    "queue_actor_prefix": "github-merge-queue",
    "author_kinds": {"agent": ["aa-agent[bot]"], "ci_bot": [], "dependabot": ["dependabot[bot]"]},
    "release_title": r"^chore(\([^)]*\))?: release ",
    "churn_exclude": [],
}
QUEUE_EVENTS = {
    "added_to_merge_queue": "added",
    "removed_from_merge_queue": "removed",
    "merged": "merged",
    "closed": "closed",
    "reopened": "reopened",
    "committed": "commit",
    "head_ref_force_pushed": "force_push",
}
REVERTS = re.compile(r"\bReverts?\s+(?:[\w.-]+/[\w.-]+)?#(\d+)", re.I)
TITLE_REF = re.compile(r"\(#(\d+)\)")
ANY_REF = re.compile(r"(?<![\w/])#(\d+)\b")
CHANGE_TYPE = re.compile(r"^(?:revert|feat|fix|chore|refactor|docs|test|perf|build|ci|style)(?=[(:!])", re.I)


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
    for k, v in CONFIG_DEFAULTS.items():
        cfg.setdefault(k, v)
    re.compile(cfg["release_title"])
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


def commit_author_kind(user: Optional[dict], title: str, cfg: dict) -> str:
    """agent | ci_bot | release_please | dependabot | bot | human for a commit on the default branch (AA-1125).

    A release-please release is told by its title (release-please opens it under the ci-bot App)."""
    if re.match(cfg["release_title"], title or "", re.I):
        return "release_please"
    login = (user or {}).get("login") or ""
    kinds = cfg.get("author_kinds") or {}
    for kind in ("agent", "ci_bot", "dependabot"):
        if login and login in set(kinds.get(kind) or ()):
            return kind
    if (user or {}).get("type") == "Bot" or login.endswith("[bot]"):
        return "bot"
    return "human"


def commit_event(repo: str, branch: str, c: dict, cfg: dict) -> dict:
    """One commit of the default branch (AA-1125). `aa.files` stays None until the commit's files are read."""
    commit = c.get("commit") or {}
    title = (commit.get("message") or "").split("\n", 1)[0].strip()[:200]
    when = (commit.get("committer") or {}).get("date") or (commit.get("author") or {}).get("date")
    kind = commit_author_kind(c.get("author"), title, cfg)
    refs = TITLE_REF.findall(title)
    return {
        "event": "aa.vcs.commit",
        "id": f"{repo}/commit/{c['sha']}",
        "time": when,
        "attributes": {
            "vcs.repository.name": repo,
            "vcs.ref.head.name": branch,
            "vcs.ref.head.revision": c["sha"],
            "aa.parents": [p.get("sha") for p in c.get("parents") or [] if isinstance(p, dict) and p.get("sha")],
            "aa.commit.title": title,
            "aa.author.kind": kind,
            "aa.author.login": ((c.get("author") or {}).get("login") or None) if kind != "human" else None,
            "vcs.change.id": int(refs[-1]) if refs else None,
            "aa.committed_at": when,
            "aa.files": None,
            "aa.files_truncated": None,
            "aa.additions": None,
            "aa.deletions": None,
        },
    }


def _queue_actor(user: Optional[dict], cfg: dict) -> str:
    login = (user or {}).get("login") or ""
    if login.startswith(cfg["queue_actor_prefix"]):
        return "queue"
    return author_kind(user, (cfg.get("author_kinds") or {}).get("agent") or cfg.get("agent_logins", ()))


def queue_event(repo: str, number: int, items: Iterable[dict], cfg: dict) -> Optional[dict]:
    """The merge-queue history of one pull request from its timeline (AA-1125): [kind, time, actor kind] in order.

    Kinds: added, removed, merged, closed, reopened, commit, force_push; actor kinds: queue (the merge queue itself),
    agent, bot, human (no login is kept). None when the timeline has no queue event."""
    rows = []
    for i, it in enumerate(items):
        kind = QUEUE_EVENTS.get(it.get("event") or "")
        if kind is None:
            continue
        when = it.get("created_at") if kind != "commit" else (it.get("committer") or {}).get("date")
        if not when:
            continue
        rows.append((when, i, kind, _queue_actor(it.get("actor"), cfg) if kind != "commit" else None))
    if not any(k in ("added", "removed") for _w, _i, k, _a in rows):
        return None
    rows.sort()
    events = [[k, w, a] for w, _i, k, a in rows]
    state = None
    for k, _w, _a in events:
        if k in ("merged", "closed"):
            state = "merged" if k == "merged" or state == "merged" else "closed"
        elif k == "reopened":
            state = None
    return {
        "event": "aa.merge_queue.timeline",
        "id": f"{repo}/queue/{number}",
        "time": events[-1][1],
        "attributes": {
            "vcs.repository.name": repo,
            "vcs.change.id": number,
            "aa.queue.events": events,
            "aa.queue.settled": state is not None,
        },
    }


# ── collection ──────────────────────────────────────────────────────────────────────────────────────────────────


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

    # 7. AA-1125: the merge-queue timeline of each pull request seen in a merge_group run (one read each). A timeline
    #    is read again while it is not settled (the pull request still open) and something moved: a new merge_group
    #    run of it, its merge, or an entry still open in the queue.
    #    S284: the reads take turns across the apps (newest first within each app). Reading one app to the end first
    #    let CIS's long backlog use the whole share of every run, so Booking and Partner never got a single timeline.
    def queue_timelines(share: float = 1.0):
        lanes: list[tuple[str, dict, list[int]]] = []
        for app in cfg["apps"]:
            if not app.get("merge_queue"):
                continue
            repo = app["repo"]
            st = store.repo_state(repo)
            read = st.setdefault("queue_read", {})
            seen: dict[int, str] = {}
            for r in store.of("cicd.pipeline.run", repo):
                a = r["attributes"]
                m = QUEUE_BRANCH.match(a["vcs.ref.head.name"] or "")
                if m and a["aa.trigger"] == "merge_group":
                    n = int(m.group(1))
                    seen[n] = max(seen.get(n, ""), a["aa.created_at"] or "")
            merged = {_attr(p, "vcs.change.id"): _attr(p, "aa.merged_at") or "" for p in store.of("vcs.change", repo)}
            have = {_attr(q, "vcs.change.id"): q for q in store.of("aa.merge_queue.timeline", repo)}
            todo = []
            for n, newest in seen.items():
                q, last = have.get(n), read.get(str(n)) or ""
                if q is None and not last:
                    todo.append((newest, n))
                elif q is not None and not _attr(q, "aa.queue.settled") and (
                    newest > last or merged.get(n, "") > last or open_entry(_attr(q, "aa.queue.events"))
                ):
                    todo.append((newest, n))
            for k in [k for k in read if int(k) not in seen]:
                del read[k]
            lanes.append((repo, read, [n for _newest, n in sorted(todo, reverse=True)]))
        for turn in range(max((len(t) for _r, _s, t in lanes), default=0)):
            for repo, read, todo in lanes:
                if turn >= len(todo):
                    continue
                n = todo[turn]
                if spent(share):
                    return
                try:
                    items = list(gh.pages(f"repos/{cfg['org']}/{repo}/issues/{n}/timeline", {}, max_pages=5))
                except ReadError as err:
                    report["errors"].append(f"{repo} queue timeline of #{n}: {err}")
                    continue
                ev = queue_event(repo, n, items, cfg)
                if ev is not None:
                    store.put(ev)
                read[str(n)] = iso(now)

    # 8. AA-1125: commits of each default branch since the cursor (90 days on a cold store), then their files.
    git_from = now - timedelta(days=cfg["git_days"])

    def recent_commits():
        for app in cfg["apps"]:
            repo = app["repo"]
            st = store.repo_state(repo)
            cursor = ts(st.get("commits_cursor"))
            since = max(git_from, cursor - timedelta(days=cfg["runs_overlap_days"])) if cursor else git_from
            newest = cursor
            try:
                for c in gh.pages(
                    f"repos/{cfg['org']}/{repo}/commits",
                    {"sha": app["default_branch"], "since": iso(since)},
                    max_pages=40,
                ):
                    if not c.get("sha"):
                        continue
                    e = commit_event(repo, app["default_branch"], c, cfg)
                    store.put(e)
                    t = ts(e["time"])
                    newest = max(newest, t) if newest and t else (newest or t)
            except ReadError as err:
                report["errors"].append(f"{repo} commits: {err}")
                continue
            st["commits_cursor"] = iso(newest or now)
            if not cursor:
                st["commits_complete_since"] = since.date().isoformat()

    def commit_files(share: float = 1.0):
        cut = iso(git_from)
        todo = [e for e in store.of("aa.vcs.commit") if _attr(e, "aa.files") is None and (e["time"] or "") >= cut]
        for e in sorted(todo, key=lambda e: e["time"] or "", reverse=True):
            if spent(share):
                return
            a = e["attributes"]
            try:
                d = gh.get(f"repos/{cfg['org']}/{a['vcs.repository.name']}/commits/{a['vcs.ref.head.revision']}")
            except ReadError as err:
                report["errors"].append(f"files of commit {a['vcs.ref.head.revision'][:12]}: {err}")
                continue
            files = [f for f in (d or {}).get("files") or [] if isinstance(f, dict) and f.get("filename")]
            cap = cfg["commit_files_cap"]
            a["aa.files"] = [[f["filename"], f.get("additions") or 0, f.get("deletions") or 0] for f in files[:cap]]
            a["aa.files_truncated"] = len(files) > cap or len(files) >= 300  # the API lists 300 files a page
            stats = (d or {}).get("stats") or {}
            a["aa.additions"] = stats.get("additions", sum(f[1] for f in a["aa.files"]))
            a["aa.deletions"] = stats.get("deletions", sum(f[2] for f in a["aa.files"]))
            store.touched_days.add((e["time"] or "")[:10])

    # Newest first; the soft shares keep a cold store from spending a whole run on one phase. The queue timelines come
    # after the backfill (it finds the older merge_group runs); the commit files of a cold store (a few thousand
    # commits over 90 days) fill over several runs, newest first, before the CI jobs.
    for name, fn in (
        ("runs", recent_runs),
        ("pull requests", recent_prs),
        ("deployments", recent_deployments),
        ("commits", recent_commits),
        ("jobs of deploy runs", lambda: jobs(max_tier=0)),
        ("backfill", lambda: backfill(share=0.6)),
        ("merge queue timelines", lambda: queue_timelines(share=0.7)),
        ("pull request files", lambda: pr_files(share=0.8)),
        ("commit files", lambda: commit_files(share=0.85)),
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
                        "queue_entries": (s.get("queue") or {}).get("entries"),
                        "commits": s["git"]["commits"],
                        "commit_files": s["git"]["files_coverage"],
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
