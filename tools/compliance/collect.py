#!/usr/bin/env python3
"""AA-1170 (S287, phase 1) — the daily compliance evidence of the root repo, for CIS Platform › Compliance.

The root workflow "Compliance evidence" (.github/workflows/compliance-evidence.yml) runs this once a day on master. It
runs about ten checks that need no new permission (tech lead S287 Q5 / Q7: the read-only GitHub App and the evidence
role come in phase 2): reads of the six public repos with the run's GITHUB_TOKEN, and registers kept in this repo. It
writes ONE file, which the workflow uploads with the existing Docs sync role next to the Delivery summary (AA-1108):

  s3://<bronze>/docs-reader/compliance/evidence.json             CIS reads and ingests it (api/services/compliance.py)
  s3://<bronze>/docs-reader/compliance/history/<yyyy>/<mm>/<dd>.json   the same file, kept per day (readiness history)

Format 1: {"format": 1, "source": "root_daily", "collector", "collector_version" (git SHA of this run),
"run_ref" (workflow and run number), "generated_at", "checks": [{"check_id", "status", "summary", "detail",
"link"}]}. status is pass | fail | error | manual. The checks of the "fact" kind (last_restore_drill,
last_access_review, docs_review_overdue) publish a fact (a date or a count) with status pass when it was read, error
when not; ci_image_scan_sbom publishes its pass / fail and the date of its oldest scan (`last_date`). CIS grades every
fact against the admin settings (cis.compliance.*), so the thresholds are never literals here.

AA-1174 (S288, privacy obligations): six legal document checks (``legal_*``, the pages listed in checks.json
"legal_docs": records of processing, the processing agreement and its annexes, the sub-processor list, the Vietnam
transfer dossier, the data subject request runbook, the consent capture page) publish ``overdue`` = their pages past
their OWN review cycle (last_reviewed + review_every_days, the docs freshness rule), ``oldest_reviewed`` and
``doc_status`` (the pages' front-matter status, so a draft agreement is never mistaken for a signed one); a missing,
superseded or undated page is an error. ``last_erasure_drill`` publishes the date of the newest live erasure drill of
the retention and erasure run log. CIS grades them (cis.compliance.legal_docs_overdue_max,
cis.compliance.erasure_drill_max_age_days).

Public repo rules (root advisory section 4 C.5): the run prints counts only, never raw API output; detail holds counts,
dates, repo names and workflow names, never an account ID, an ARN, a bucket name or a person; :func:`assert_publishable`
refuses to write a file that carries one (the workflow then fails instead of publishing).

    python3 tools/compliance/collect.py --out _out/evidence.json      # GITHUB_TOKEN in the environment
    python3 tools/compliance/collect.py --out F --offline             # repo-local checks only (tests, a fork)

Stdlib only. Exit 0 = file written (failing checks are results, not errors), 2 = the file would carry forbidden text.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name("checks.json")
FORMAT = 1
SOURCE = "root_daily"
API = "https://api.github.com"
FORBIDDEN = (
    (re.compile(r"(?<![0-9A-Za-z])\d{12}(?![0-9A-Za-z])"), "an account ID"),
    (re.compile(r"arn:aws", re.I), "an ARN"),
    (re.compile(r"s3://", re.I), "an S3 URI (a bucket name)"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "an e-mail address"),
)
RED = frozenset({"failure", "timed_out", "startup_failure", "action_required"})

Fetch = Callable[[str], Any]


def load_config(path: Path = CONFIG) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def github_fetch(token: Optional[str]) -> Fetch:
    """GET a GitHub REST path; returns the parsed JSON, or None on 404. Raises on any other error."""
    def fetch(path: str) -> Any:
        req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json",
                                                          "X-GitHub-Api-Version": "2022-11-28",
                                                          "User-Agent": "aa-compliance-collector"})
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:   # noqa: S310 - fixed https host
                return json.loads(resp.read())
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            raise
    return fetch


def result(check_id: str, status: str, summary: str, detail: Optional[dict] = None, link: Optional[str] = None) -> dict:
    return {"check_id": check_id, "status": status, "summary": summary[:300], "detail": detail or {}, "link": link}


def _error(check_id: str, err: Exception) -> dict:
    return result(check_id, "error", f"the check could not run ({type(err).__name__})")


# ── GitHub checks (public reads with the run's token) ──────────────────────────────────────────────────────────────


def check_branch_protection(fetch: Fetch, cfg: dict) -> dict:
    """The default branch of every repo is protected (a ruleset or a branch protection rule)."""
    org, missing, protected = cfg["org"], [], 0
    for repo in cfg["repos"]:
        meta = fetch(f"/repos/{org}/{repo}") or {}
        branch = meta.get("default_branch") or "main"
        rules = fetch(f"/repos/{org}/{repo}/rules/branches/{branch}") or []
        kinds = {r.get("type") for r in rules if isinstance(r, dict)}
        info = fetch(f"/repos/{org}/{repo}/branches/{branch}") or {}
        if kinds & {"pull_request", "required_status_checks", "non_fast_forward"} or info.get("protected"):
            protected += 1
        else:
            missing.append(repo)
    status = "pass" if not missing else "fail"
    return result("repo_branch_protection", status, f"{protected}/{len(cfg['repos'])} default branches protected",
                  {"repos": len(cfg["repos"]), "protected": protected, "unprotected": missing},
                  f"https://github.com/{org}")


def check_codeql(fetch: Fetch, cfg: dict) -> dict:
    """Every repo runs CodeQL (default setup or a CodeQL workflow, active)."""
    org, missing = cfg["org"], []
    for repo in cfg["repos"]:
        flows = (fetch(f"/repos/{org}/{repo}/actions/workflows?per_page=100") or {}).get("workflows", [])
        if not any("codeql" in (w.get("path", "") + w.get("name", "")).lower() and w.get("state") == "active"
                   for w in flows):
            missing.append(repo)
    n = len(cfg["repos"])
    return result("codeql_enabled", "pass" if not missing else "fail", f"{n - len(missing)}/{n} repos run CodeQL",
                  {"repos": n, "with_codeql": n - len(missing), "without": missing})


def check_scheduled_guards(fetch: Fetch, cfg: dict, now: datetime) -> dict:
    """The latest scheduled run of every workflow that ran on a schedule in the window is not red (tools/github/
    guard_runs.py, the session-start block)."""
    org, since = cfg["org"], now - timedelta(days=cfg["guard_window_days"])
    total, red = 0, []
    for repo in cfg["repos"]:
        runs = (fetch(f"/repos/{org}/{repo}/actions/runs?event=schedule&per_page=100") or {}).get("workflow_runs", [])
        seen: set[str] = set()
        for run in runs:
            name = run.get("name") or run.get("path") or "?"
            try:
                when = datetime.fromisoformat(str(run.get("created_at", "")).replace("Z", "+00:00"))
            except ValueError:
                continue
            if when < since or name in seen or run.get("status") != "completed":
                continue
            seen.add(name)
            total += 1
            if run.get("conclusion") in RED:
                red.append(f"{repo}: {name}")
    return result("scheduled_guards_green", "pass" if total and not red else ("fail" if red else "error"),
                  f"{total - len(red)}/{total} scheduled guards green", {"workflows": total, "red": red})


_SKIP_RUN = frozenset({"cancelled", "skipped", "neutral", "stale"})


def _run_scan_result(fetch: Fetch, org: str, repo: str, run: dict) -> Optional[bool]:
    """Whether the image scan and the SBOM steps of one CI run both passed; None when the run did not scan (no such
    steps, or they were skipped: a path-filtered or cancelled run says nothing about the image)."""
    jobs = (fetch(f"/repos/{org}/{repo}/actions/runs/{run['id']}/jobs?per_page=100") or {}).get("jobs", [])
    steps = [s for j in jobs for s in j.get("steps", []) or []]
    scan = [s for s in steps if "trivy" in s.get("name", "").lower() and "scan" in s.get("name", "").lower()]
    sbom = [s for s in steps if "sbom" in s.get("name", "").lower() and "generate" in s.get("name", "").lower()]
    ran = [s for s in scan + sbom if s.get("conclusion") not in (None, "skipped", "cancelled")]
    if not scan or not sbom or len(ran) != len(scan + sbom):
        return None
    return all(s.get("conclusion") == "success" for s in ran)


def check_image_scan_sbom(fetch: Fetch, cfg: dict) -> dict:
    """The newest CI run that reached main in every image repo scanned the image (Trivy gate) and wrote an SBOM, both
    passed. "Reached main" = a merge-queue run (event merge_group, branch gh-readonly-queue/<main>/...: since the app
    CI dropped push on main this is the run that gates what lands) or a push run on main, whichever is newer. The
    result carries the fact `last_date`, the date of the OLDEST of those newest scans across the repos: CIS grades its
    age against cis.compliance.ci_scan_max_age_days, so a scan that stopped running fails instead of passing on an old
    run (Q3: only fresh evidence counts). The per-repo run dates are in `run_dates`."""
    org, flow, bad, ok = cfg["org"], cfg["ci_workflow"], [], 0
    inspect = int(cfg["ci_runs_inspected"])
    dates: dict[str, str] = {}
    for repo in cfg["image_repos"]:
        branch = (fetch(f"/repos/{org}/{repo}") or {}).get("default_branch") or "main"
        base = f"/repos/{org}/{repo}/actions/workflows/{flow}/runs"
        queue = (fetch(f"{base}?event=merge_group&status=completed&per_page={inspect}") or {}).get("workflow_runs", [])
        push = (fetch(f"{base}?event=push&branch={branch}&status=completed&per_page={inspect}")
                or {}).get("workflow_runs", [])
        runs = [r for r in queue if str(r.get("head_branch", "")).startswith(f"gh-readonly-queue/{branch}/")]
        runs += [r for r in push if r.get("head_branch") == branch]
        runs.sort(key=lambda r: str(r.get("created_at", "")), reverse=True)
        found = None
        for run in runs[:inspect]:
            if run.get("conclusion") in _SKIP_RUN:
                continue
            found = _run_scan_result(fetch, org, repo, run)
            if found is not None:
                dates[repo] = str(run.get("created_at", ""))[:10]
                break
        if found:
            ok += 1
        else:
            bad.append(repo)
    n = len(cfg["image_repos"])
    detail: dict[str, Any] = {"repos": n, "ok": ok, "missing_or_red": bad, "run_dates": dates}
    summary = f"{ok}/{n} image repos scan and write an SBOM"
    if dates:
        detail["last_date"] = min(dates.values())
        summary += f"; oldest newest scan {detail['last_date']}"
    return result("ci_image_scan_sbom", "pass" if not bad else "fail", summary, detail)


def check_secret_scan(fetch: Fetch, cfg: dict) -> dict:
    """The newest full-history secret scan of this repo passed."""
    org, flow = cfg["org"], cfg["secret_scan_workflow"]
    runs = (fetch(f"/repos/{org}/{cfg['root_repo']}/actions/workflows/{flow}/runs?status=completed&per_page=1")
            or {}).get("workflow_runs", [])
    if not runs:
        return result("secret_scan_history_green", "error", "no completed full-history secret scan found")
    run = runs[0]
    status = "pass" if run.get("conclusion") == "success" else "fail"
    return result("secret_scan_history_green", status, f"latest full-history scan: {run.get('conclusion')}",
                  {"conclusion": run.get("conclusion"), "run_date": str(run.get("created_at", ""))[:10]},
                  run.get("html_url") if str(run.get("html_url", "")).startswith("https://github.com/") else None)


# ── repo registers (this checkout) ─────────────────────────────────────────────────────────────────────────────────

_FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def _front(text: str) -> dict:
    m = _FRONT.match(text)
    out: dict[str, str] = {}
    for line in (m.group(1).splitlines() if m else []):
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def check_docs_overdue(root: Path, today: date, skip_status: tuple[str, ...]) -> dict:
    """Pages of docs/ past last_reviewed + review_every_days (fact `overdue`; CIS grades it)."""
    pages = overdue = 0
    for path in sorted((root / "docs").rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(("docs/archive/", "docs/audits/", "docs/sessions/", "docs/linear-export/")):
            continue
        fm = _front(path.read_text(encoding="utf-8", errors="replace"))
        if not fm.get("last_reviewed") or fm.get("status") in skip_status:
            continue
        try:
            reviewed = date.fromisoformat(fm["last_reviewed"][:10])
            every = int(fm.get("review_every_days") or 90)
        except ValueError:
            continue
        pages += 1
        overdue += (today - reviewed).days > every
    return result("docs_review_overdue", "pass", f"{overdue} of {pages} pages past their review date",
                  {"overdue": overdue, "pages": pages})


_DRILL_ROW = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|[^|]*\|[^|]*\|\s*pass\b", re.I | re.M)


def check_last_drill(root: Path) -> dict:
    """The newest passed drill of docs/ops/drills/README.md (fact `last_date`; CIS grades its age)."""
    path = root / "docs" / "ops" / "drills" / "README.md"
    dates = sorted(_DRILL_ROW.findall(path.read_text(encoding="utf-8"))) if path.exists() else []
    if not dates:
        return result("last_restore_drill", "error", "no passed drill in the drill index")
    return result("last_restore_drill", "pass", f"last passed drill {dates[-1]}",
                  {"last_date": dates[-1], "passed_drills": len(dates)})


_REVIEW = re.compile(r"\b(\d{4}-\d{2}-\d{2})-S\d+-access-review\b")


def check_last_access_review(root: Path) -> dict:
    """The newest access review listed in docs/security/README.md (fact `last_date`; CIS grades its age)."""
    path = root / "docs" / "security" / "README.md"
    dates = sorted(set(_REVIEW.findall(path.read_text(encoding="utf-8")))) if path.exists() else []
    if not dates:
        return result("last_access_review", "error", "no access review listed")
    return result("last_access_review", "pass", f"last access review {dates[-1]}",
                  {"last_date": dates[-1], "reviews": len(dates)})


GITHUB_BLOB = "https://github.com/{org}/{repo}/blob/master/{path}"


def check_legal_doc(root: Path, check_id: str, pages: list[str], today: date, skip_status: tuple[str, ...],
                    cfg: dict) -> dict:
    """AA-1174: the review state of the legal pages behind one check (fact `overdue`; CIS grades it)."""
    problems: list[str] = []
    overdue, reviewed, statuses = 0, [], set()
    for rel in pages:
        path = root / rel
        if not path.exists():
            problems.append(f"{rel}: missing")
            continue
        fm = _front(path.read_text(encoding="utf-8", errors="replace"))
        status = fm.get("status") or "unknown"
        statuses.add(status)
        if status in skip_status:
            problems.append(f"{rel}: {status}")
            continue
        try:
            day = date.fromisoformat(fm.get("last_reviewed", "")[:10])
            every = int(fm.get("review_every_days") or 90)
        except ValueError:
            problems.append(f"{rel}: no valid last_reviewed")
            continue
        reviewed.append(day.isoformat())
        overdue += (today - day).days > every
    link = GITHUB_BLOB.format(org=cfg["org"], repo=cfg["root_repo"], path=pages[0]) if pages else None
    detail: dict[str, Any] = {"pages": len(pages), "overdue": overdue, "doc_status": ", ".join(sorted(statuses))}
    if reviewed:
        detail["oldest_reviewed"] = min(reviewed)
    if problems:
        return result(check_id, "error", "; ".join(problems), {"pages": len(pages), "problems": len(problems)}, link)
    return result(check_id, "pass", f"{overdue} of {len(pages)} pages past their review cycle; "
                  f"oldest review {detail['oldest_reviewed']}; status {detail['doc_status']}", detail, link)


def check_last_erasure_drill(root: Path, rel: str, cfg: dict) -> dict:
    """AA-1174: the newest LIVE erasure drill row of the retention and erasure run log (fact `last_date`)."""
    path = root / rel
    dates = []
    for line in (path.read_text(encoding="utf-8").splitlines() if path.exists() else []):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[0]):
            continue
        if "erasure drill" in cells[1].lower() and cells[3].lower() == "live":
            dates.append(cells[0])
    link = GITHUB_BLOB.format(org=cfg["org"], repo=cfg["root_repo"], path=rel)
    if not dates:
        return result("last_erasure_drill", "error", "no live erasure drill in the run log", {}, link)
    return result("last_erasure_drill", "pass", f"last live erasure drill {max(dates)}",
                  {"last_date": max(dates), "drills": len(dates)}, link)


def check_vuln_exceptions(root: Path, today: date) -> dict:
    """Every row of the vulnerability exception register is still valid (expires today or later)."""
    path = root / "docs" / "security" / "vuln-exceptions.toml"
    try:
        rows = tomllib.loads(path.read_text(encoding="utf-8")).get("exception", [])
    except (OSError, tomllib.TOMLDecodeError) as err:
        return _error("vuln_exceptions_valid", err)
    expired = [f"{r.get('repo')}: {r.get('id')}" for r in rows
               if not isinstance(r.get("expires"), date) or r["expires"] < today]
    return result("vuln_exceptions_valid", "pass" if not expired else "fail",
                  f"{len(rows) - len(expired)}/{len(rows)} exceptions valid",
                  {"exceptions": len(rows), "expired": expired})


# ── the file ───────────────────────────────────────────────────────────────────────────────────────────────────────


def assert_publishable(bundle: dict) -> list[str]:
    """What forbidden text the bundle carries (empty = publishable)."""
    text = json.dumps(bundle)
    return [what for rx, what in FORBIDDEN if rx.search(text)]


def collect(fetch: Optional[Fetch], cfg: dict, root: Path, now: datetime, version: Optional[str],
            run_ref: Optional[str]) -> dict:
    today = now.date()
    checks: list[dict] = []
    remote = (("repo_branch_protection", lambda: check_branch_protection(fetch, cfg)),
              ("codeql_enabled", lambda: check_codeql(fetch, cfg)),
              ("scheduled_guards_green", lambda: check_scheduled_guards(fetch, cfg, now)),
              ("ci_image_scan_sbom", lambda: check_image_scan_sbom(fetch, cfg)),
              ("secret_scan_history_green", lambda: check_secret_scan(fetch, cfg)))
    local = (("docs_review_overdue", lambda: check_docs_overdue(root, today, tuple(cfg["docs_skip_status"]))),
             ("last_restore_drill", lambda: check_last_drill(root)),
             ("last_access_review", lambda: check_last_access_review(root)),
             ("vuln_exceptions_valid", lambda: check_vuln_exceptions(root, today)),
             ("last_erasure_drill", lambda: check_last_erasure_drill(root, cfg["retention_log"], cfg)))
    skip = tuple(cfg["docs_skip_status"])
    local += tuple((cid, (lambda c=cid, pages=pages: check_legal_doc(root, c, pages, today, skip, cfg)))
                   for cid, pages in cfg.get("legal_docs", {}).items())
    for check_id, run in (remote if fetch else ()) + local:
        try:
            checks.append(run())
        except Exception as err:   # one check failing never stops the others
            checks.append(_error(check_id, err))
    checks.append(result("collector_heartbeat", "pass", f"{len(checks)} checks ran",
                         {"checks": len(checks), "offline": fetch is None}))
    return {"format": FORMAT, "source": SOURCE, "collector": "root compliance-evidence",
            "collector_version": version if version and re.fullmatch(r"[0-9a-f]{7,40}", version) else None,
            "run_ref": run_ref, "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "checks": checks}


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--offline", action="store_true", help="repo-local checks only (no GitHub reads)")
    args = ap.parse_args(argv)
    cfg = load_config()
    fetch = None if args.offline else github_fetch(os.environ.get("GITHUB_TOKEN"))
    run_ref = None
    if os.environ.get("GITHUB_RUN_NUMBER"):
        run_ref = f"compliance-evidence #{os.environ['GITHUB_RUN_NUMBER']}"
    bundle = collect(fetch, cfg, ROOT, datetime.now(timezone.utc), os.environ.get("GITHUB_SHA"), run_ref)
    bad = assert_publishable(bundle)
    if bad:
        print(f"refused: the evidence file would carry {', '.join(bad)}", file=sys.stderr)
        return 2
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(bundle, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    counts: dict[str, int] = {}
    for c in bundle["checks"]:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    print(json.dumps({"checks": len(bundle["checks"]), "by_status": counts}))   # counts only (public log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
