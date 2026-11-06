#!/usr/bin/env python3
"""PreToolUse guard for the Workflow tool (AA-1024 G12, S271): a lane starts only on an up-to-date master plan.

Lessons S264 and S271: lanes were opened while docs/backlog/tracker/plan.json (and the tracker's session tab) still
showed the previous session, so the tech lead's plan view was wrong for the whole wave; and a lane once got its args
as a JSON-encoded string instead of an object (lane.js then read `args.session` as undefined).

For a launch of tools/workflows/lane.js (by scriptPath, any checkout, or by the name `aa-lane`) it refuses (exit 2):
  1. args that are not an object, or that lack key / goal / session / date;
  2. a plan.json `session` other than args.session (aa-session step 7: update plan.json and republish the tracker
     right after the session list is agreed, BEFORE the first lane);
  3. a goal whose first AA-<n> issue is in plan.json with a `session` slot that does not name args.session (a pulled-
     ahead issue gets its slot moved to this session first; an issue not in plan.json passes).
`plan_gate: "skip: <reason>"` in args passes (a hotfix lane), logged to .tmp-session/guard-hits.log. Every other
Workflow launch (research, review, audits) is not gated. plan.json is read from the main checkout
($CLAUDE_PROJECT_DIR), where the orchestrator edits it. Unreadable hook input passes; an unreadable plan.json refuses
a lane launch (the gate cannot tell).

Test: python3 .claude/hooks/test_lane_start_guard.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
PLAN = Path("docs/backlog/tracker/plan.json")
HITS_LOG = Path(".tmp-session/guard-hits.log")
REQUIRED = ("key", "goal", "session", "date")
FIX = ("Update docs/backlog/tracker/plan.json first (session, next_session, and the session slot of every agreed "
       "issue, pulled-ahead ones too), run tools/linear/plan_sync.py --validate, republish the tracker (skill "
       "aa-session step 7), then launch the lane. Hotfix only: add plan_gate: \"skip: <reason>\" to args.")


def is_lane(tool_input: dict) -> bool:
    sp = str(tool_input.get("scriptPath") or "")
    return sp.replace("\\", "/").endswith("tools/workflows/lane.js") or tool_input.get("name") == "aa-lane"


def _log(root: Path, what: str) -> None:
    try:
        p = root / HITS_LOG
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"rule": "LANE-1", "what": what[:300]}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def check(tool_input: dict, root: Path = ROOT) -> str | None:
    """None when the launch may go ahead, else the refusal message."""
    if not is_lane(tool_input):
        return None
    args = tool_input.get("args")
    if not isinstance(args, dict):
        kind = type(args).__name__ if args is not None else "missing"
        return (f"lane.js args must be a JSON object, got {kind}" + (" (a JSON-encoded string: pass the object "
                "itself, never a quoted or placeholder string)" if isinstance(args, str) else "") + ".")
    gate = str(args.get("plan_gate") or "")
    if re.match(r"skip:\s*\S", gate):
        _log(root, f"skip {args.get('key')}: {gate}")
        return None
    missing = [k for k in REQUIRED if not str(args.get(k) or "").strip()]
    if missing:
        return f"lane.js args lack {', '.join(missing)} (required: {', '.join(REQUIRED)})."
    session = str(args["session"]).strip()
    try:
        plan = json.loads((root / PLAN).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return f"cannot read {PLAN} ({type(e).__name__}) to check the master plan before the lane. {FIX}"
    if str(plan.get("session")) != session:
        return (f"the master plan is not on this session: {PLAN} has session={plan.get('session')!r}, the lane says "
                f"{session!r}. {FIX}")
    m = re.search(r"\bAA-\d+\b", str(args["goal"]))
    if m:
        issue = next((i for i in plan.get("issues") or [] if i.get("id") == m.group(0)), None)
        if issue is not None:
            slot = str(issue.get("session") or "")
            if session not in re.findall(r"S\d+", slot):
                return (f"{m.group(0)} is slotted for {slot!r} in {PLAN}, not {session}: move its session slot "
                        f"(and `next`) to {session} if it was pulled ahead. {FIX}")
    return None


def main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return 0
    if not isinstance(data, dict):
        return 0
    msg = check(data.get("tool_input") or {})
    if msg:
        _log(ROOT, msg)
        print(f"BLOCKED by lane_start_guard: {msg}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
