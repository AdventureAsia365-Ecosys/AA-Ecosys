#!/usr/bin/env python3
"""Sync the master plan tracker (docs/backlog/tracker/plan.json) from Linear, one way: Linear -> plan.json.

Design: docs/audits/2026-11-01-S262-assessment-followup/README.md section 6 (approved S263, $0).

Field ownership (6.2):
- Linear owns, and this script always overwrites in issues[]: the set of open issues (state type triage, backlog,
  unstarted, started; open issues archived with a parent are kept), id, title, status, priority, project, due.
- People own, and this script never touches: per issue milestone, session, size, next, needs; the blocks milestones,
  checks, waiting, log, projects, next_session (except --session).
Conflict rules (6.4): closed issues leave issues[] and are listed in the diff; a new open issue enters with
milestone "later", session "unscheduled", needs "cần xếp slot"; a due date only the plan has is kept with a warning;
unknown project / session / milestone values warn. Only the public-safety guard (12-digit account ID, "arn:") fails.

Usage (from the AA-Ecosys root; key from Secrets Manager with an unlocked MFA profile, or LINEAR_API_KEY):
    python3 tools/linear/plan_sync.py                        # dry run: print the diff, write nothing
    python3 tools/linear/plan_sync.py --check                # exit 1 when plan.json differs from Linear
    python3 tools/linear/plan_sync.py --write                # write plan.json (sets updated + synced_at)
    python3 tools/linear/plan_sync.py --write --session S263 # session close: also session / next_session
    python3 tools/linear/plan_sync.py --log-draft            # print a log[0] draft (closed / canceled / created)
    python3 tools/linear/plan_sync.py --validate             # offline: shape, due/risks, public safety (no Linear)
    python3 tools/linear/plan_sync.py --check-scope BASE     # offline: only Linear-owned fields differ from BASE

Stdlib only. Never writes to Linear.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs" / "backlog" / "tracker" / "plan.json"
INDEX = ROOT / "docs" / "backlog" / "tracker" / "index.html"
PLAN_REL = "docs/backlog/tracker/plan.json"

TEAM_KEY = "AA"
OPEN = ("triage", "backlog", "unstarted", "started")
CLOSED = ("completed", "canceled")
PRIORITY = {0: "No priority", 1: "Urgent", 2: "High", 3: "Medium", 4: "Low"}
# Linear project name prefix -> plan.json project key (6.2). An unknown name warns and maps to "other".
PROJECT_PREFIX = (
    ("Data Platform", "data"),
    ("CIS Core", "core"),
    ("CIS Portal", "portal"),
    ("TripPlanner", "tpbk"),
    ("AA-Booking", "tpbk"),
    ("Partner CRM", "crm"),
)
LINEAR_FIELDS = ("id", "title", "status", "priority", "project", "due")
HAND_FIELDS = ("milestone", "session", "size", "next", "needs")
KEY_ORDER = ("id", "title", "status", "priority", "project", "milestone", "session", "size", "next", "needs", "due")
NEW_DEFAULTS = {"milestone": "later", "session": "unscheduled", "size": "", "next": "", "needs": "cần xếp slot"}
# Top-level keys a sync may change; every other block is hand-owned (6.2).
SYNC_TOP_KEYS = ("issues", "updated", "synced_at")

ACCOUNT_ID = re.compile(r"(?<!\d)\d{12}(?!\d)")
ARN = re.compile(r"(?<![A-Za-z0-9])arn:")  # "arn:aws:..."; not the tail of a word such as "Learn:"
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

OPEN_QUERY = """
query($after: String, $team: String!, $types: [String!]!) {
  issues(first: 100, after: $after, includeArchived: true,
         filter: { team: { key: { eq: $team } }, state: { type: { in: $types } } }) {
    pageInfo { hasNextPage endCursor }
    nodes { identifier title priority dueDate archivedAt trashed createdAt state { name type } project { name } }
  }
}
"""

CHANGED_SINCE_QUERY = """
query($after: String, $team: String!, $since: DateTimeOrDuration!) {
  issues(first: 100, after: $after, includeArchived: true,
         filter: { team: { key: { eq: $team } }, updatedAt: { gte: $since } }) {
    pageInfo { hasNextPage endCursor }
    nodes { identifier title createdAt completedAt canceledAt trashed state { name type } }
  }
}
"""


class SafetyError(Exception):
    """plan.json would carry an account ID or an ARN (the tracker page can be shared; the repo is public)."""


# ---------------------------------------------------------------------------------------------------------------
# Pure part: normalise, merge, validate. No I/O; covered by tools/linear/test_plan_sync.py.
# ---------------------------------------------------------------------------------------------------------------

def issue_num(ident: str) -> int:
    m = re.search(r"(\d+)$", ident or "")
    return int(m.group(1)) if m else 0


def project_key(name: str | None) -> str | None:
    """Plan project key for a Linear project name; None when no prefix matches (caller warns, uses "other")."""
    for prefix, key in PROJECT_PREFIX:
        if name and name.startswith(prefix):
            return key
    return None


def normalize(node: dict) -> dict:
    """One Linear GraphQL issue node -> the Linear-owned plan fields plus a few flags for the diff."""
    pname = (node.get("project") or {}).get("name")
    return {
        "id": node["identifier"],
        "title": node["title"],
        "status": node["state"]["name"],
        "state_type": node["state"]["type"],
        "priority": PRIORITY.get(node.get("priority") or 0, "No priority"),
        "project": project_key(pname) or "other",
        "project_name": pname,
        "due": node.get("dueDate") or None,
        "archived": bool(node.get("archivedAt")),
        "trashed": bool(node.get("trashed")),
    }


def ordered(issue: dict) -> dict:
    """Keys in the order plan.json uses, so a rewrite does not churn; unknown keys keep their place at the end."""
    out = {k: issue[k] for k in KEY_ORDER if k in issue}
    out.update({k: v for k, v in issue.items() if k not in out})
    return out


def merge(plan: dict, linear: list[dict], closed: dict[str, str] | None = None) -> tuple[dict, dict]:
    """Apply Linear-owned fields to plan["issues"]. Pure: returns (new_plan, diff); `plan` is not modified.

    linear: normalized open issues (normalize()); a trashed or closed node passed in is treated as gone.
    closed: optional {identifier: state name} of issues known to be closed, to say why an issue left the plan.
    diff: {"removed": [(id, reason)], "added": [id], "changed": [(id, field, old, new)], "warnings": [str]}.
    """
    closed = closed or {}
    new = copy.deepcopy(plan)
    diff: dict = {"removed": [], "added": [], "changed": [], "warnings": []}
    live = {i["id"]: i for i in linear if i.get("state_type", "started") in OPEN and not i.get("trashed")}

    issues = []
    for old in plan.get("issues", []):
        ident = old["id"]
        src = live.pop(ident, None)
        if src is None:
            diff["removed"].append((ident, closed.get(ident, "not open in Linear (closed, deleted or another team)")))
            continue
        cur = dict(old)
        for field in ("title", "status", "priority", "project"):
            if field == "title" and cur.get("private"):
                continue  # private work: the plan keeps its public-safe label, the Linear title never reaches the repo
            if cur.get(field) != src[field]:
                diff["changed"].append((ident, field, cur.get(field), src[field]))
                cur[field] = src[field]
        if src["due"]:
            if cur.get("due") != src["due"]:
                diff["changed"].append((ident, "due", cur.get("due"), src["due"]))
                cur["due"] = src["due"]
        elif cur.get("due"):
            diff["warnings"].append(f"{ident}: due {cur['due']} is only in plan.json; set it in Linear")
        _flag(src, diff)
        issues.append(ordered(cur))

    for ident in sorted(live, key=issue_num):
        src = live[ident]
        item = {k: src[k] for k in ("id", "title", "status", "priority", "project")}
        item.update(NEW_DEFAULTS)
        if src["due"]:
            item["due"] = src["due"]
        diff["added"].append(ident)
        _flag(src, diff)
        issues.append(ordered(item))

    new["issues"] = issues
    return new, diff


def _flag(src: dict, diff: dict) -> None:
    if src.get("archived"):
        diff["warnings"].append(f"{src['id']}: open but archived in Linear (kept; unarchive it)")
    if src["project"] == "other":
        diff["warnings"].append(f"{src['id']}: project {src.get('project_name')!r} has no plan key (mapped to 'other')")


def has_changes(diff: dict) -> bool:
    return bool(diff["removed"] or diff["added"] or diff["changed"])


def stamp(plan: dict, today: str, synced_at: str, session: str | None = None) -> dict:
    """Set updated / synced_at (and session + next_session when given). Returns a new dict, keys in file order."""
    rest = {k: v for k, v in plan.items() if k not in ("updated", "synced_at")}
    out = {"updated": today, "synced_at": synced_at, **rest}
    if session:
        out["session"] = session
        m = re.fullmatch(r"S(\d+)", session)
        if m:
            out["next_session"] = f"S{int(m.group(1)) + 1}"
    return out


def dumps(plan: dict) -> str:
    """The exact file format of plan.json (indent 1, UTF-8 kept, final newline) so a rewrite does not churn."""
    return json.dumps(plan, indent=1, ensure_ascii=False) + "\n"


def safety_problems(text: str) -> list[str]:
    hits = [f"12-digit number (account ID?) {m.group(0)[:4]}…" for m in ACCOUNT_ID.finditer(text)]
    if ARN.search(text):
        hits.append("'arn:' found")
    return hits


def validate(plan: dict, ses_order: list[str] | None = None, ms_order: list[str] | None = None) -> tuple[list, list]:
    """(errors, warnings). Errors: shape, due/risks rules, public safety. Warnings: unknown session / milestone."""
    errors: list[str] = []
    warnings: list[str] = []
    for key in ("updated", "session", "next_session", "projects", "milestones", "checks", "waiting", "log", "issues"):
        if key not in plan:
            errors.append(f"missing top-level key {key!r}")
    seen = set()
    for i in plan.get("issues", []):
        ident = i.get("id", "?")
        for k in LINEAR_FIELDS[:-1] + HAND_FIELDS:
            if k not in i:
                errors.append(f"{ident}: missing {k!r}")
        if ident in seen:
            errors.append(f"{ident}: listed twice")
        seen.add(ident)
        if i.get("priority") not in PRIORITY.values():
            errors.append(f"{ident}: priority {i.get('priority')!r} is not a Linear priority label")
        if ses_order is not None and i.get("session") not in ses_order:
            warnings.append(f"{ident}: session {i.get('session')!r} not in SES_ORDER (index.html)")
        if ms_order is not None and i.get("milestone") not in ms_order:
            warnings.append(f"{ident}: milestone {i.get('milestone')!r} not in MS_ORDER (index.html)")
        if i.get("project") not in plan.get("projects", {}):
            warnings.append(f"{ident}: project {i.get('project')!r} not in projects")
    for x in plan.get("milestones", []) + plan.get("issues", []):
        if "due" in x and not ISO_DATE.fullmatch(str(x["due"])):
            errors.append(f"{x.get('id', '?')}: due {x['due']!r} is not YYYY-MM-DD")
    for m in plan.get("milestones", []):
        for r in m.get("risks", []):
            if set(r) != {"text", "owner_role", "trigger"}:
                errors.append(f"{m.get('id', '?')}: risk keys must be text, owner_role, trigger")
    errors += [f"public safety: {p}" for p in safety_problems(dumps(plan))]
    return errors, warnings


def scope_violations(base: dict, new: dict) -> list[str]:
    """What changed between base and new outside the Linear-owned fields (6.5: the bot merges only when empty)."""
    out = []
    for k in sorted(set(base) | set(new)):
        if k not in SYNC_TOP_KEYS and base.get(k) != new.get(k):
            out.append(f"top-level {k!r} changed")
    old_by_id = {i["id"]: i for i in base.get("issues", [])}
    for i in new.get("issues", []):
        old = old_by_id.get(i["id"])
        ref = old if old is not None else NEW_DEFAULTS
        for k in HAND_FIELDS:
            if i.get(k) != ref.get(k):
                out.append(f"{i['id']}: hand-owned {k!r} changed")
        extra = set(i) - set(LINEAR_FIELDS) - set(HAND_FIELDS)
        if old is None and extra:
            out.append(f"{i['id']}: new issue with extra keys {sorted(extra)}")
        elif old is not None:
            for k in extra:
                if i.get(k) != old.get(k):
                    out.append(f"{i['id']}: hand-owned {k!r} changed")
    return out


def log_draft(changed: list[dict], since: str, session: str | None, date: str) -> dict:
    """A log[0] draft from issues updated since `since` (YYYY-MM-DD): closed, canceled, created. Notes stay by hand."""
    def on_or_after(ts: str | None) -> bool:
        return bool(ts) and ts[:10] >= since

    closed, canceled, created = [], [], []
    for n in sorted(changed, key=lambda x: issue_num(x["identifier"])):
        st = n["state"]["type"]
        if st == "completed" and on_or_after(n.get("completedAt")) and not n.get("trashed"):
            closed.append(n["identifier"])
        elif st == "canceled" and on_or_after(n.get("canceledAt")):
            canceled.append(n["identifier"])
        if on_or_after(n.get("createdAt")):
            created.append(n["identifier"])
    return {"session": session or "S?", "date": date, "closed": closed, "canceled": canceled, "created": created,
            "reopened": [], "notes": []}


def js_array(html: str, name: str) -> list[str] | None:
    """Read `var NAME = [...]` from index.html (SES_ORDER, MS_ORDER); None when absent."""
    m = re.search(r"var\s+" + re.escape(name) + r"\s*=\s*(\[[^\]]*\])", html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def format_diff(diff: dict) -> str:
    lines = []
    for ident, reason in diff["removed"]:
        lines.append(f"REMOVED  {ident}: {reason}")
    for ident in diff["added"]:
        lines.append(f"NEW      {ident}: slot needed (milestone later, session unscheduled)")
    for ident, field, old, new in diff["changed"]:
        lines.append(f"CHANGED  {ident} {field}: {old!r} -> {new!r}")
    for w in diff["warnings"]:
        lines.append(f"WARN     {w}")
    head = (f"plan_sync: {len(diff['removed'])} removed, {len(diff['added'])} new, "
            f"{len(diff['changed'])} field changes, {len(diff['warnings'])} warnings")
    return "\n".join([head] + lines)


# ---------------------------------------------------------------------------------------------------------------
# I/O part: Linear reads, files, CLI.
# ---------------------------------------------------------------------------------------------------------------

def _paged(key: str, query: str, variables: dict) -> list[dict]:
    from linear_api import gql  # local import: the offline modes and the tests never need it

    nodes, after = [], None
    while True:
        page = gql(key, query, {**variables, "after": after})["issues"]
        nodes += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return nodes
        after = page["pageInfo"]["endCursor"]


def fetch_open(key: str) -> list[dict]:
    return [normalize(n) for n in _paged(key, OPEN_QUERY, {"team": TEAM_KEY, "types": list(OPEN)})]


def fetch_changed_since(key: str, since: str) -> list[dict]:
    return _paged(key, CHANGED_SINCE_QUERY, {"team": TEAM_KEY, "since": f"{since}T00:00:00.000Z"})


def iso_day(value: str | None) -> str | None:
    """`updated` as YYYY-MM-DD; a hand-written DD/MM/YYYY (S273 close) is converted instead of breaking the Linear query."""
    if not value:
        return None
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", value.strip())
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else value.strip()[:10]


def committed_updated(path: Path) -> str | None:
    """`updated` of plan.json as committed at HEAD (a local session-start --write must not move the log window)."""
    if path.resolve() != PLAN.resolve():
        return None
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{PLAN_REL}"], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout).get("updated")
    except json.JSONDecodeError:
        return None


def now_local() -> dt.datetime:
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    except Exception:  # noqa: BLE001 - no tz database: fall back to UTC
        return dt.datetime.now(dt.timezone.utc)


def orders(index: Path) -> tuple[list[str] | None, list[str] | None]:
    if not index.exists():
        return None, None
    html = index.read_text(encoding="utf-8")
    return js_array(html, "SES_ORDER"), js_array(html, "MS_ORDER")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="exit 1 when plan.json differs from Linear")
    mode.add_argument("--write", action="store_true", help="write plan.json (default: dry run)")
    mode.add_argument("--validate", action="store_true", help="offline checks of plan.json only")
    mode.add_argument("--check-scope", metavar="BASE", help="offline: fail when fields other than Linear-owned differ")
    ap.add_argument("--session", help="with --write: set session (and next_session = the next S number)")
    ap.add_argument("--log-draft", action="store_true", help="also print a log[0] draft as JSON")
    ap.add_argument("--since", help="log draft window start YYYY-MM-DD (default: committed plan.json updated)")
    ap.add_argument("--plan", default=str(PLAN), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    path = Path(args.plan)
    plan = json.loads(path.read_text(encoding="utf-8"))
    ses_order, ms_order = orders(INDEX)

    if args.validate or args.check_scope:
        errors, warnings = validate(plan, ses_order, ms_order)
        if args.check_scope:
            base = json.loads(Path(args.check_scope).read_text(encoding="utf-8"))
            errors += [f"scope: {v}" for v in scope_violations(base, plan)]
        for w in warnings:
            print(f"WARN  {w}")
        for e in errors:
            print(f"ERROR {e}")
        print(f"{path.name}: {len(errors)} errors, {len(warnings)} warnings")
        return 1 if errors else 0

    from linear_api import api_key

    key = api_key()
    linear = fetch_open(key)
    since = iso_day(args.since or committed_updated(path) or plan.get("updated"))
    changed = fetch_changed_since(key, since) if since else []
    closed = {n["identifier"]: f"{n['state']['name']} in Linear" for n in changed if n["state"]["type"] in CLOSED}
    closed.update({n["identifier"]: "deleted in Linear" for n in changed if n.get("trashed")})
    new_plan, diff = merge(plan, linear, closed)

    now = now_local()
    if args.write:
        new_plan = stamp(new_plan, now.date().isoformat(),
                         dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), args.session)
    report = format_diff(diff)
    draft = log_draft(changed, since or now.date().isoformat(), args.session, now.strftime("%d/%m/%Y")) \
        if args.log_draft else None
    # Public-safety gate BEFORE anything is printed: the Plan sync workflow puts this output in the Actions log and in
    # the bot PR body, both public (the root repo is public). On a hit print only the redacted hits, nothing else.
    hits = safety_problems("\n".join([report, dumps(new_plan), json.dumps(draft, ensure_ascii=False)]))
    if hits:
        for h in hits:
            print(f"ERROR    public safety: {h}")
        print("refusing to continue: Linear data would put an account ID or an ARN into plan.json or this output")
        return 2
    print(report)

    errors, warnings = validate(new_plan, ses_order, ms_order)
    for w in warnings:
        print(f"WARN     {w}")
    for e in errors:
        print(f"ERROR    {e}")

    if draft is not None:
        print("log draft (since " + str(since) + "):")
        print(json.dumps(draft, ensure_ascii=False, indent=1))

    if args.check:
        return 1 if has_changes(diff) else 0
    if args.write:
        if errors:
            print("not written: fix the errors above")
            return 1
        path.write_text(dumps(new_plan), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    print("dry run: nothing written (use --write)")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
