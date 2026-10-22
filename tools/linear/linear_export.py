#!/usr/bin/env python3
"""Export closed Linear issues (with comments) into the repo, then optionally archive them.

Why (S245, 20/10/2026): Linear stays on the Free plan (250 unarchived issues per workspace). The UI has no
manual archive and auto-archive waits at least a month, so closed issues filled the quota. The export in
docs/linear-export/ is the long-term record; archiving through the API frees the quota without losing it.

Usage (from the AA-Ecosys root, MFA profile already unlocked):
    python3 tools/linear/linear_export.py                  # export every closed issue, archive nothing
    python3 tools/linear/linear_export.py --archive        # DRY RUN: list what would be archived
    python3 tools/linear/linear_export.py --archive --apply  # archive exported, closed, unarchived issues
    python3 tools/linear/linear_export.py --only AA-913    # one issue (repeatable)

Rules:
- Only issues whose state type is completed or canceled are exported or archived. Open work is never touched.
- An issue is archived only after its export file exists and matches the issue's current updatedAt.
- Deleted issues still in Linear's 30-day trash are exported too (marked trashed) so their comments survive.
- The API key is read from Secrets Manager (aa-ecosys/ops/linear-api-key, acc2) into memory only; it is
  never printed or written. LINEAR_API_KEY in the environment overrides it (CI / testing).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.linear.app/graphql"
SECRET_ID = "aa-ecosys/ops/linear-api-key"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "linear-export"
CLOSED = ("completed", "canceled")

ISSUE_FIELDS = """
  id identifier title description url priority
  createdAt updatedAt startedAt completedAt canceledAt archivedAt trashed
  state { name type }
  team { key }
  project { name }
  parent { identifier }
  children(first: 100) { nodes { identifier state { type } } }
  labels { nodes { name } }
  assignee { name }
  creator { name }
  attachments { nodes { title url } }
  comments(first: 100) { nodes { body createdAt user { name } } }
"""

LIST_QUERY = """
query($after: String) {
  issues(first: 50, after: $after, includeArchived: true) {
    pageInfo { hasNextPage endCursor }
    nodes { %s }
  }
}
""" % ISSUE_FIELDS

ONE_QUERY = "query($id: String!) { issue(id: $id) { %s } }" % ISSUE_FIELDS

ARCHIVE_MUTATION = "mutation($id: String!) { issueArchive(id: $id, trash: false) { success } }"
UNARCHIVE_MUTATION = "mutation($id: String!) { issueUnarchive(id: $id) { success } }"
STATE_QUERY = "query($id: String!) { issue(id: $id) { identifier trashed archivedAt } }"
DETACH_MUTATION = "mutation($id: String!) { issueUpdate(id: $id, input: { parentId: null }) { success } }"
OPEN = ("triage", "backlog", "unstarted", "started")


def open_children(issue: dict) -> list[str]:
    """Sub-issues still open. Linear archives every sub-issue together with its parent (S247: archiving AA-821
    took its 53 open CRM sub-issues with it), so a parent with open children must not be archived."""
    return [c["identifier"] for c in ((issue.get("children") or {}).get("nodes") or [])
            if c["state"]["type"] in OPEN]


def keep(issue: dict) -> bool:
    """Exported: every closed issue, and every archived or trashed issue whatever its state."""
    return issue["state"]["type"] in CLOSED or bool(issue.get("archivedAt")) or bool(issue.get("trashed"))


def api_key() -> str:
    key = os.environ.get("LINEAR_API_KEY", "").strip()
    if key:
        return key
    r = subprocess.run(
        ["aws", "secretsmanager", "get-secret-value", "--secret-id", SECRET_ID, "--query", "SecretString",
         "--output", "text", "--profile", os.environ.get("AWS_PROFILE_LINEAR", "aa365-admin"), "--region", "us-west-1"],
        capture_output=True, text=True, stdin=subprocess.DEVNULL,
    )
    key = r.stdout.strip()
    if r.returncode != 0 or not key:
        sys.exit(f"cannot read {SECRET_ID} (aws exit {r.returncode}); unlock MFA or set LINEAR_API_KEY")
    return key


def gql(key: str, query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        API, data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "Authorization": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Linear API HTTP {e.code}: {e.read()[:300]!r}")
    if body.get("errors"):
        sys.exit(f"Linear API error: {json.dumps(body['errors'])[:500]}")
    return body["data"]


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "no-project").lower()).strip("-")
    return s[:60] or "no-project"


def path_for(issue: dict) -> Path:
    return OUT / slug((issue.get("project") or {}).get("name")) / f"{issue['identifier']}.md"


def render(issue: dict) -> str:
    meta = {
        "identifier": issue["identifier"],
        "title": issue["title"],
        "state": issue["state"]["name"],
        "state_type": issue["state"]["type"],
        "project": (issue.get("project") or {}).get("name"),
        "parent": (issue.get("parent") or {}).get("identifier"),
        "labels": [n["name"] for n in issue["labels"]["nodes"]],
        "priority": issue.get("priority"),
        "assignee": (issue.get("assignee") or {}).get("name"),
        "creator": (issue.get("creator") or {}).get("name"),
        "created_at": issue["createdAt"],
        "started_at": issue.get("startedAt"),
        "completed_at": issue.get("completedAt"),
        "canceled_at": issue.get("canceledAt"),
        "updated_at": issue["updatedAt"],
        "trashed": bool(issue.get("trashed")),
        "url": issue["url"],
    }
    # Metadata as a fenced yaml block, not front-matter: docs lint validates every docs/**/*.md front-matter
    # against the catalog schema, and these generated pages are not catalog pages.
    lines = [f"# {issue['identifier']} — {issue['title']}", "", "```yaml"]
    lines += [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items()] + ["```", ""]
    lines += [issue.get("description") or "_(no description)_", ""]
    atts = issue["attachments"]["nodes"]
    if atts:
        lines += ["## Links", ""] + [f"- [{a['title']}]({a['url']})" for a in atts] + [""]
    comments = sorted(issue["comments"]["nodes"], key=lambda c: c["createdAt"])
    if comments:
        lines += ["## Comments", ""]
        for c in comments:
            who = (c.get("user") or {}).get("name") or "unknown"
            lines += [f"### {c['createdAt'][:16].replace('T', ' ')} — {who}", "", c["body"], ""]
    return "\n".join(lines).rstrip() + "\n"


def exported_matches(issue: dict) -> bool:
    p = path_for(issue)
    if not p.exists():
        return False
    head = p.read_text(encoding="utf-8").split("\n```\n", 1)[0]
    return f'updated_at: "{issue["updatedAt"]}"' in head


def fetch(key: str, only: list[str]) -> list[dict]:
    if only:
        out = []
        for ident in only:
            issue = gql(key, ONE_QUERY, {"id": ident})["issue"]
            if issue and keep(issue):
                out.append(issue)
            else:
                print(f"skip {ident}: not found or not closed")
        return out
    issues, after = [], None
    while True:
        page = gql(key, LIST_QUERY, {"after": after})["issues"]
        issues += [i for i in page["nodes"] if keep(i)]
        if not page["pageInfo"]["hasNextPage"]:
            return issues
        after = page["pageInfo"]["endCursor"]


def move_from_trash(key: str, issue_id: str) -> str:
    """Trash -> archive. issueArchive(trash: false) first; if the issue is still trashed, restore it and archive."""
    gql(key, ARCHIVE_MUTATION, {"id": issue_id})
    st = gql(key, STATE_QUERY, {"id": issue_id})["issue"]
    if st["archivedAt"] and not st["trashed"]:
        return "archived (direct)"
    gql(key, UNARCHIVE_MUTATION, {"id": issue_id})
    gql(key, ARCHIVE_MUTATION, {"id": issue_id})
    st = gql(key, STATE_QUERY, {"id": issue_id})["issue"]
    return "archived (restore + archive)" if st["archivedAt"] and not st["trashed"] else f"NOT moved: {st}"


def write_index(issues: list[dict]) -> None:
    rows = sorted(issues, key=lambda i: (slug((i.get("project") or {}).get("name")), i["identifier"]))
    lines = ["# Linear export", "",
             "Closed Linear issues (Done / Canceled), plus every archived or trashed issue, with their comments, exported by "
             "`tools/linear/linear_export.py` before they are archived (Linear Free plan, S245). "
             "Generated — do not edit by hand; re-run the script.", "",
             "| Issue | Title | State | Closed | Project |", "|---|---|---|---|---|"]
    for i in rows:
        rel = path_for(i).relative_to(OUT).as_posix()
        closed = (i.get("completedAt") or i.get("canceledAt") or "")[:10]
        title = i["title"].replace("|", "\\|")
        state = i["state"]["name"] + (" (trashed)" if i.get("trashed") else "")
        lines.append(f"| [{i['identifier']}]({rel}) | {title} | {state} | {closed} | "
                     f"{(i.get('project') or {}).get('name') or '—'} |")
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--archive", action="store_true", help="archive exported closed issues (dry run unless --apply)")
    ap.add_argument("--apply", action="store_true", help="with --archive: really archive")
    ap.add_argument("--only", action="append", default=[], help="issue identifier, e.g. AA-913 (repeatable)")
    ap.add_argument("--rescue-trash", action="store_true",
                    help="move exported issues from Linear's 30-day trash to the archive (dry run unless --apply)")
    ap.add_argument("--rescue-open-archived", action="store_true",
                    help="unarchive open issues archived with their parent and detach them (dry run unless --apply)")
    args = ap.parse_args()

    key = api_key()
    issues = fetch(key, args.only)
    written = 0
    for issue in issues:
        p = path_for(issue)
        text = render(issue)
        if not p.exists() or p.read_text(encoding="utf-8") != text:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            written += 1
    if not args.only:
        # A file is stale when its issue was reopened (no longer closed/archived/trashed) or now lives under another
        # project folder. Stale files are removed so the export stays one file per issue (history keeps the rest).
        wanted = {path_for(i).resolve() for i in issues}
        stale = sorted(f for f in OUT.glob("*/AA-*.md") if f.resolve() not in wanted)
        for f in stale:
            f.unlink()
        if stale:
            print(f"removed {len(stale)} stale files: {', '.join(f.stem for f in stale[:10])}")
        write_index(issues)
    print(f"closed issues: {len(issues)} | files written/updated: {written} | "
          f"trashed: {sum(1 for i in issues if i.get('trashed'))} | archived: {sum(1 for i in issues if i.get('archivedAt'))}")

    if args.rescue_trash:
        # Only closed issues go to the archive. A trashed open issue (Backlog / In Progress) is reported, never
        # archived: an archived open issue disappears from every Linear view (AA-779 / AA-800, S245).
        open_trashed = [i for i in issues if i.get("trashed") and i["state"]["type"] not in CLOSED]
        for i in open_trashed:
            print(f"  skip (open, restore by hand or --only + unarchive): {i['identifier']} {i['state']['name']}")
        rescue = [i for i in issues if i.get("trashed") and i["state"]["type"] in CLOSED and exported_matches(i)]
        print(f"{'RESCUE' if args.apply else 'DRY RUN, would move trash -> archive'}: {len(rescue)} issue(s)")
        for i in rescue:
            if not args.apply:
                print(f"  {i['identifier']}  {i['state']['name']}  {i['title'][:80]}")
                continue
            print(f"  {i['identifier']}: {move_from_trash(key, i['id'])}")
        return
    if args.rescue_open_archived:
        # An archived open issue disappears from every Linear view. Unarchive it and detach it from its closed
        # parent, so archiving the parent again cannot take it along.
        hit = [i for i in issues if i.get("archivedAt") and not i.get("trashed") and i["state"]["type"] in OPEN]
        print(f"{'RESCUE' if args.apply else 'DRY RUN, would unarchive + detach'}: {len(hit)} open issue(s)")
        for i in hit:
            parent = (i.get("parent") or {}).get("identifier")
            if not args.apply:
                print(f"  {i['identifier']}  {i['state']['name']}  parent={parent}  {i['title'][:70]}")
                continue
            gql(key, UNARCHIVE_MUTATION, {"id": i["id"]})
            if parent:
                gql(key, DETACH_MUTATION, {"id": i["id"]})
            st = gql(key, STATE_QUERY, {"id": i["id"]})["issue"]
            print(f"  {i['identifier']}: {'unarchived' if not st['archivedAt'] else 'STILL ARCHIVED'}"
                  f"{f', detached from {parent}' if parent else ''}")
        return
    if not args.archive:
        return
    todo = [i for i in issues if not i.get("archivedAt") and not i.get("trashed") and exported_matches(i)]
    held = [i for i in todo if open_children(i)]
    for i in held:
        print(f"  skip (open sub-issues would be archived with it): {i['identifier']} -> "
              f"{', '.join(open_children(i)[:8])}{' …' if len(open_children(i)) > 8 else ''}")
    todo = [i for i in todo if not open_children(i)]
    print(f"{'ARCHIVE' if args.apply else 'DRY RUN, would archive'}: {len(todo)} issue(s)")
    for i in todo:
        if not args.apply:
            print(f"  {i['identifier']}  {i['state']['name']}  {i['title'][:80]}")
            continue
        ok = gql(key, ARCHIVE_MUTATION, {"id": i["id"]})["issueArchive"]["success"]
        print(f"  {i['identifier']}: {'archived' if ok else 'NOT archived'}")


if __name__ == "__main__":
    main()
