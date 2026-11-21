#!/usr/bin/env python3
"""Post the independent agent review of a lane onto its PR as a GitHub PR review (AA-1162, skill aa-ship §1).

    tools/github/as-app.sh --repos AA-Booking -- python3 tools/github/post_agent_review.py booking#240 \
        --review wf_324cb059-50b --lenses "correctness + spec fit,security + data safety,settings"
    python3 tools/github/post_agent_review.py root#930 --review reviews.json --dry-run   # print the body only

The review is evidence on the PR (ISO 27001 A.8.32, SOC 2 CC8.1): who reviewed, which lenses, what they found and
which reviewer run it was. It is posted by the aa-agent App, which authored the PR, and GitHub refuses APPROVE or
REQUEST_CHANGES from a PR's own author, so the event is always COMMENT and the verdict is the body's first line:

    Agent review: approve | request changes | blocking

blocking = at least one blocking finding; request changes = a major finding or a reviewer verdict "changes";
approve otherwise. An agent review is not a human approval: from the trigger in aa-ship §1 the merge gate asks for an
APPROVED review by a human (tools/github/change_control.json), and this comment never counts as one.

--review takes what the lane workflow (tools/workflows/lane.js) returns, in any of these shapes:
  - a workflow run id (wf_...) or its journal.jsonl: the results of the agents labelled review:<lane>:<i>, in lens
    order, plus whether a fix pass ran after them;
  - a JSON file holding the lane result {"lane", "impl", "reviews": [...], "fix"}, {"reviews": [...]}, a list of
    reviews or one review; a review is {"verdict": "approve"|"changes", "findings": [{severity, file, line, issue,
    fix}]} and may carry "lens".
Lens names come from each review's "lens", else from --lenses (comma-separated, in the lane's lens order), else
"lens <i>". The reviewer run id comes from --run-id, else the wf_ id, else the JSON's "run_id".

Idempotent per head SHA: the body ends with a hidden marker <!-- aa-agent-review head=<sha> -->. A re-run on the same
head updates that review (PUT .../reviews/<id>) instead of adding a second one; a new head gets a new review, so the
history of reviewed heads stays on the PR. --head <sha> refuses when the PR head moved on (the review was of another
commit).

Posting needs GH_TOKEN (as-app.sh sets it): without it gh would post as the person logged in, and an agent review must
never look like a human one. --dry-run prints the body and posts nothing. Exit: 0 posted / updated / dry run |
2 usage, input or gh error | 4 refused (PR not open, head moved, no GH_TOKEN). Orchestrator only. No secrets.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

from ship_common import Runner, ShipError, gh_json, log, parse_target, slug

MARKER_PREFIX = "<!-- aa-agent-review head="
MARKER_RE = re.compile(r"<!-- aa-agent-review head=([0-9a-f]{7,40})(?: [^>]*)? -->")
VERDICTS = ("approve", "request changes", "blocking")
SEVERITIES = ("blocking", "major", "minor")
MAX_ROWS = 40  # findings listed in the table; the counts line always covers all of them
MAX_CELL = 300  # characters per table cell
JOURNAL_GLOBS = (
    "~/.claude/projects/*/*/subagents/workflows/{id}/journal.jsonl",
    "~/.claude/projects/*/subagents/workflows/{id}/journal.jsonl",
)


# --- input ---------------------------------------------------------------------------------------------------------


def _find_journal(arg: str) -> Path | None:
    p = Path(arg).expanduser()
    if p.is_file() and p.suffix == ".jsonl":
        return p
    if re.fullmatch(r"wf_[A-Za-z0-9_-]+", arg):
        hits: list[str] = []
        for g in JOURNAL_GLOBS:
            hits.extend(glob.glob(os.path.expanduser(g.format(id=arg))))
        if hits:
            return Path(max(hits, key=os.path.getmtime))
        raise ShipError(f"no journal for '{arg}' (a journal.jsonl path or a workflow run id wf_...)", 2)
    return None


def _is_review(obj: object) -> bool:
    return isinstance(obj, dict) and "verdict" in obj and isinstance(obj.get("findings", []), list)


def load_journal(path: Path) -> dict:
    """Reviews of a lane journal in lens order, the lane key and whether a fix pass ran after the reviews."""
    labels: dict[str, str] = {}
    reviews: list[tuple[int, dict]] = []
    fix_ran = False
    lane = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        agent = str(rec.get("agentId") or "")
        if rec.get("type") == "started" and agent:
            labels[agent] = str(rec.get("label") or "")
        elif rec.get("type") == "result":
            label = labels.get(agent, "")
            res = rec.get("result")
            m = re.fullmatch(r"review:(.+):(\d+)", label)
            if m and _is_review(res):
                lane = lane or m.group(1)
                reviews.append((int(m.group(2)), res))
            elif label.startswith("fix:") and isinstance(res, dict):
                fix_ran = True
            elif label.startswith("impl:"):
                lane = lane or label[len("impl:"):]
    if not reviews:
        raise ShipError(f"{path}: no review result (agents labelled review:<lane>:<i>)", 2)
    reviews.sort(key=lambda t: t[0])
    run_id = path.parent.name if path.parent.name.startswith("wf_") else ""
    return {"reviews": [r for _, r in reviews], "lane": lane, "fix_ran": fix_ran, "run_id": run_id}


def load_input(arg: str) -> dict:
    """{"reviews": [...], "lane": str, "fix_ran": bool, "run_id": str} from a journal, wf_ id or JSON file."""
    journal = _find_journal(arg)
    if journal is not None:
        return load_journal(journal)
    p = Path(arg).expanduser()
    if not p.is_file():
        raise ShipError(f"no review input at '{arg}' (a JSON file, a journal.jsonl or a workflow run id wf_...)", 2)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ShipError(f"{p}: not JSON ({e})", 2) from e
    out = {"reviews": [], "lane": "", "fix_ran": False, "run_id": ""}
    if _is_review(data):
        out["reviews"] = [data]
    elif isinstance(data, list):
        out["reviews"] = [r for r in data if _is_review(r)]
    elif isinstance(data, dict):
        out["reviews"] = [r for r in (data.get("reviews") or []) if _is_review(r)]
        out["lane"] = str(data.get("lane") or "")
        out["fix_ran"] = bool(data.get("fix"))
        out["run_id"] = str(data.get("run_id") or data.get("runId") or "")
    if not out["reviews"]:
        raise ShipError(f"{p}: no review in it (expected the lane result, its reviews[] or one review)", 2)
    return out


# --- body ----------------------------------------------------------------------------------------------------------


def verdict_of(reviews: list[dict]) -> str:
    findings = [f for r in reviews for f in (r.get("findings") or []) if isinstance(f, dict)]
    sev = {str(f.get("severity") or "").lower() for f in findings}
    if "blocking" in sev:
        return "blocking"
    if "major" in sev or any(str(r.get("verdict") or "").lower() != "approve" for r in reviews):
        return "request changes"
    return "approve"


def _cell(text: object) -> str:
    s = " ".join(str(text if text is not None else "").split())
    s = s.replace("|", "\\|").replace("<!--", "&lt;!--")
    return s if len(s) <= MAX_CELL else s[: MAX_CELL - 1] + "…"


def lens_names(reviews: list[dict], given: list[str]) -> list[str]:
    names = []
    for i, r in enumerate(reviews):
        lens = str(r.get("lens") or "").strip()
        if not lens and i < len(given):
            lens = given[i]
        names.append(lens or f"lens {i + 1}")
    return names


def build_body(reviews: list[dict], *, head: str, lenses: list[str], run_id: str, lane: str = "",
               fix_ran: bool = False) -> str:
    verdict = verdict_of(reviews)
    names = lens_names(reviews, lenses)
    rows: list[tuple[int, str, dict]] = []
    for name, r in zip(names, reviews):
        for f in r.get("findings") or []:
            if isinstance(f, dict):
                sev = str(f.get("severity") or "minor").lower()
                rows.append((SEVERITIES.index(sev) if sev in SEVERITIES else len(SEVERITIES), name, f))
    rows.sort(key=lambda t: t[0])
    counts = {s: sum(1 for _, _, f in rows if str(f.get("severity") or "").lower() == s) for s in SEVERITIES}
    votes = [str(r.get("verdict") or "?").lower() for r in reviews]
    lines = [
        f"Agent review: {verdict}",
        "",
        f"Lenses: {'; '.join(_cell(n) for n in names)}",
        f"Findings: {counts['blocking']} blocking, {counts['major']} major, {counts['minor']} minor "
        f"({len(reviews)} reviewer(s): {', '.join(f'{votes.count(v)} {v}' for v in sorted(set(votes)))})",
        f"Reviewer run: {_cell(run_id) or 'not given'}" + (f" (lane {_cell(lane)})" if lane else ""),
        f"Reviewed head: {head[:12]}",
    ]
    if fix_ran:
        lines.append("Fix pass: ran after this review on the blocking/major findings; the head above includes it. "
                     "A risky PR gets a second review of the fixed head.")
    if rows:
        lines += ["", "| Severity | Lens | File | Finding | Fix |", "|---|---|---|---|---|"]
        for _, name, f in rows[:MAX_ROWS]:
            where = _cell(f.get("file"))
            if f.get("line"):
                where += f":{_cell(f.get('line'))}"
            lines.append(f"| {_cell(f.get('severity'))} | {_cell(name)} | {where} | {_cell(f.get('issue'))} | "
                         f"{_cell(f.get('fix'))} |")
        if len(rows) > MAX_ROWS:
            lines.append(f"\n{len(rows) - MAX_ROWS} more finding(s) in the reviewer run.")
    lines += [
        "",
        "Independent agent review posted by the aa-agent App as a comment review (GitHub refuses approve or request "
        "changes from the PR's author). It is not a human approval.",
        f"{MARKER_PREFIX}{head} -->",
    ]
    return "\n".join(lines)


# --- GitHub --------------------------------------------------------------------------------------------------------


def existing_review(runner: Runner, repo: str, n: int, head: str) -> int | None:
    """Id of this tool's review for this head (marker + a bot author), or None."""
    r = runner.run(["gh", "api", "--paginate", f"repos/{slug(repo)}/pulls/{n}/reviews?per_page=100",
                    "--jq", ".[] | {id, type: .user.type, body} | @json"], timeout=60)
    if not r.ok:
        raise ShipError(f"{repo}#{n}: cannot list reviews: {r.last_line()}", 2)
    for line in r.out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rev = json.loads(line)
        except json.JSONDecodeError:
            continue
        m = MARKER_RE.search(str(rev.get("body") or ""))
        if m and m.group(1) == head and rev.get("type") == "Bot":
            return int(rev["id"])
    return None


def post(runner: Runner, repo: str, n: int, body: str, head: str) -> tuple[str, int]:
    """Create the review, or update the one this tool posted for the same head. Returns (action, review id)."""
    rid = existing_review(runner, repo, n, head)
    if rid is not None:
        argv = ["gh", "api", "-X", "PUT", f"repos/{slug(repo)}/pulls/{n}/reviews/{rid}", "--input", "-"]
        payload = {"body": body}
        action = "updated"
    else:
        argv = ["gh", "api", "-X", "POST", f"repos/{slug(repo)}/pulls/{n}/reviews", "--input", "-"]
        payload = {"body": body, "event": "COMMENT", "commit_id": head}
        action = "posted"
    r = runner.run(argv, timeout=60, input_text=json.dumps(payload))
    if not r.ok:
        raise ShipError(f"{repo}#{n}: review not {action}: {r.last_line()}", 2)
    try:
        rid = int(json.loads(r.out or "{}").get("id") or rid or 0)
    except (json.JSONDecodeError, AttributeError, TypeError, ValueError):
        rid = rid or 0
    return action, rid


def main(argv: list[str] | None = None, runner: Runner | None = None, env: dict | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("target", help="'<Repo>#<pr>' (aliases root, cis, booking, partner/crm, tp, infra)")
    ap.add_argument("--review", required=True, help="wf_ run id, journal.jsonl, or a JSON file of the lane review")
    ap.add_argument("--lenses", default="", help="lens names in the lane's order, comma-separated")
    ap.add_argument("--run-id", default="", help="reviewer run id (default: the wf_ id or the JSON's run_id)")
    ap.add_argument("--head", default="", help="the reviewed head SHA; refuse when the PR head differs")
    ap.add_argument("--dry-run", action="store_true", help="print the review body, post nothing")
    a = ap.parse_args(argv)
    runner = runner or Runner()
    env = os.environ if env is None else env
    try:
        repo, n = parse_target(a.target)
        data = load_input(a.review)
        pr = gh_json(runner, ["gh", "pr", "view", str(n), "-R", slug(repo), "--json", "state,headRefOid"])
        if not isinstance(pr, dict):
            raise ShipError(f"{repo}#{n}: unexpected gh output", 2)
        head = str(pr.get("headRefOid") or "")
        if pr.get("state") != "OPEN":
            raise ShipError(f"{repo}#{n} REFUSED: the PR is {str(pr.get('state')).lower()}, not open", 4)
        if a.head and not head.startswith(a.head.lower()):
            raise ShipError(f"{repo}#{n} REFUSED: the PR head is {head[:8]}, not the reviewed {a.head[:8]}", 4)
        lenses = [x.strip() for x in a.lenses.split(",") if x.strip()]
        body = build_body(data["reviews"], head=head, lenses=lenses, run_id=a.run_id or data["run_id"],
                          lane=data["lane"], fix_ran=data["fix_ran"])
        if a.dry_run:
            print(body)
            log(f"{repo}#{n}: dry run, nothing posted ({body.splitlines()[0]})")
            return 0
        if not env.get("GH_TOKEN"):
            raise ShipError("REFUSED: no GH_TOKEN; run under tools/github/as-app.sh so the review is the App's, "
                            "never the logged-in person's", 4)
        action, rid = post(runner, repo, n, body, head)
        log(f"{repo}#{n}: review {action} (id {rid}, head {head[:8]}): {body.splitlines()[0]}")
        return 0
    except ShipError as e:
        print(f"ERROR {e}", file=sys.stderr, flush=True)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
