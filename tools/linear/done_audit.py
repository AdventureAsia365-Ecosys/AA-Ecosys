#!/usr/bin/env python3
"""Done-evidence audit (AA-1024 G11, S272): issues moved to Done without the evidence aa-ship asks for. Read-only.

Lessons S243-S246 and S262: issues went to Done by themselves (Linear's Git automation on a merge, an id linked from a
root docs PR body, a DB Migrate run) or were set Done before every "Done when" bullet was met. The PR-text rules
(pr-title.yml, tools/github/ship_open_prs.py) stop the automatic flips at the source; this audit finds what still
slipped through, at session close (skill aa-session, step "Linear"), so each hit is reopened or gets its comment.

For every issue completed since --since (state type "completed"; canceled issues are not audited) it checks:
  1. an evidence comment exists: the aa-ship template ("Verified live ..."), "Done-with-scope:" or a hand-closed
     issue's "Done-evidence: <why>" line (skill/aa-ship/SKILL.md section 4);
  2. every bullet of the description's "Done when" section is covered by the evidence comments: at least half of the
     bullet's significant words (4+ letters, not a stop word) appear in them. A heuristic: it flags, the reviewer
     decides.

    python3 tools/linear/done_audit.py --since 2026-11-07T00:00:00Z        # exit 1 when an issue has a finding
    python3 tools/linear/done_audit.py --since 2026-11-07 --json

The Linear key: tools/linear/linear_api.py (Secrets Manager or LINEAR_API_KEY). Exit: 0 clean | 1 findings | 2 usage.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone

QUERY = """
query($since: DateTimeOrDuration!, $after: String) {
  issues(first: 50, after: $after, includeArchived: true,
         filter: { completedAt: { gte: $since }, state: { type: { eq: "completed" } } }) {
    pageInfo { hasNextPage endCursor }
    nodes {
      identifier title description completedAt url
      comments(first: 100) { nodes { body createdAt } }
    }
  }
}
"""

EVIDENCE_RE = re.compile(r"(?im)^\s*(?:\*\*)?(?:verified live\b|done-with-scope:|done-evidence:)")
DONE_WHEN_HEAD = re.compile(r"(?im)^\s*(?:#{1,6}\s*|\*\*)?done[ -]when\b.*$")
NEXT_HEAD = re.compile(r"(?m)^\s*(?:#{1,6}\s+\S|\*\*[^*]+\*\*\s*:?\s*$|\+\+\+)")
BULLET = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(?:\[[ xX]\]\s+)?(.+?)\s*$")
WORD = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]{3,}")
STOP = frozenset("""
with that this from have when then than into onto each every must only also does done more less some none they them
their there where which while what will would should could about after before under over just same such very been
being were your ours page shows show issue issues returns return work works using used uses make made
""".split())


def done_when_bullets(description: str) -> list[str]:
    """The bullets of the description's "Done when" section (empty when there is none)."""
    text = description or ""
    m = DONE_WHEN_HEAD.search(text)
    if not m:
        return []
    rest = text[m.end():]
    nxt = NEXT_HEAD.search(rest)
    section = rest[: nxt.start()] if nxt else rest
    out = []
    for line in section.splitlines():
        b = BULLET.match(line)
        if b:
            out.append(b.group(1))
    return out


def significant(text: str) -> set[str]:
    return {w.lower().strip("./-") for w in WORD.findall(text) if w.lower() not in STOP}


def covered(bullet: str, evidence: str) -> bool:
    words = significant(bullet)
    if not words:
        return True
    ev = evidence.lower()
    return sum(1 for w in words if w in ev) * 2 >= len(words)


def audit_issue(issue: dict) -> list[str]:
    comments = [c.get("body") or "" for c in ((issue.get("comments") or {}).get("nodes") or [])]
    evidence = [c for c in comments if EVIDENCE_RE.search(c)]
    if not evidence:
        return ["no evidence comment (aa-ship template 'Verified live', 'Done-with-scope:' or 'Done-evidence:')"]
    joined = "\n".join(evidence)
    missing = [b for b in done_when_bullets(issue.get("description") or "") if not covered(b, joined)]
    return [f"Done-when bullet not shown in the evidence: {b[:120]}" for b in missing]


def audit(issues: list[dict]) -> list[dict]:
    out = []
    for i in issues:
        findings = audit_issue(i)
        if findings:
            out.append({"id": i.get("identifier"), "title": i.get("title"), "completed_at": i.get("completedAt"),
                        "url": i.get("url"), "findings": findings})
    return out


def since_value(text: str) -> str:
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat()
        return datetime.fromisoformat(text.replace("Z", "+00:00")).isoformat()
    except ValueError as e:
        raise SystemExit(f"done_audit: --since must be a date or an ISO time ({e})") from None


def fetch(since: str) -> list[dict]:
    from linear_api import api_key, gql
    key = api_key()
    issues, after = [], None
    while True:
        page = gql(key, QUERY, {"since": since, "after": after})["issues"]
        issues += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return issues
        after = page["pageInfo"]["endCursor"]


def main(argv: list[str] | None = None, issues: list[dict] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--since", required=True, help="date (YYYY-MM-DD, UTC) or ISO time: usually the session start")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    since = since_value(a.since)
    if issues is None:
        issues = fetch(since)
    hits = audit(issues)
    if a.json:
        print(json.dumps({"since": since, "audited": len(issues), "hits": hits}, ensure_ascii=False, indent=1))
    else:
        print(f"done_audit: {len(issues)} issue(s) completed since {since}, {len(hits)} with a finding")
        for h in hits:
            print(f"- {h['id']} {h['title']!r} (Done {h['completed_at']})")
            for f in h["findings"]:
                print(f"    {f}")
        if hits:
            print("Reopen each hit (Linear state back to In Review) or add the evidence comment (skill/aa-ship "
                  "section 4).")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
