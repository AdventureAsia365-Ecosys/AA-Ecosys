#!/usr/bin/env python3
"""PreToolUse guard for the Workflow tool (AA-1024 G12, S271): a lane starts only on an up-to-date master plan.

Lessons S264 and S271: lanes were opened while docs/backlog/tracker/plan.json (and the tracker's session tab) still
showed the previous session, so the tech lead's plan view was wrong for the whole wave; and lanes got a placeholder
string ("__FROM_FILE__") as args instead of an object (S252: the script read every field as undefined).

For a launch of tools/workflows/lane.js (by scriptPath, any checkout, or by the name `aa-lane`) it refuses (exit 2):
  1. args that are not an object (a JSON-encoded object string is fine: the harness parses it), or that lack
     key / goal / session / date;
  2. a plan.json `session` other than args.session (aa-session step 7: update plan.json and republish the tracker
     right after the session list is agreed, BEFORE the first lane);
  3. a goal whose first AA-<n> issue is in plan.json with a `session` slot that does not name args.session (a pulled-
     ahead issue gets its slot moved to this session first; an issue not in plan.json passes);
  4. (G4) MemAvailable under 4 GiB: a lane builds and tests, and the WSL VM ran out of memory with 3 lanes plus the
     orchestrator's own Playwright (S237 ... S270). The message names the heavy processes running.
     `ram_gate: "skip: <reason>"` in args passes, logged.
  5. (G20) a lane whose worktree already exists (`.tmp-session/wt/<session>-<key>-*`, lowercase session) without
     `resume: true`: a lane relaunched after a usage limit or a crash redid or overwrote half-done work (10 events,
     S243 ... S270). With `resume: true`, lane.js makes the agent report `resumed_state` (dirty files, commits ahead,
     a decision per file) before it changes anything. Remove a stale worktree (git worktree remove) to start over.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aa_shell_guard  # noqa: E402  (the /proc readers of RAM-1)

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
PLAN = Path("docs/backlog/tracker/plan.json")
HITS_LOG = Path(".tmp-session/guard-hits.log")
REQUIRED = ("key", "goal", "session", "date")
LANE_MEM_FLOOR_MIB = 4096
FIX = ("Update docs/backlog/tracker/plan.json first (session, next_session, and the session slot of every agreed "
       "issue, pulled-ahead ones too), run tools/linear/plan_sync.py --validate, republish the tracker (skill "
       "aa-session step 7), then launch the lane. Hotfix only: add plan_gate: \"skip: <reason>\" to args.")


def is_lane(tool_input: dict) -> bool:
    sp = str(tool_input.get("scriptPath") or "")
    return sp.replace("\\", "/").endswith("tools/workflows/lane.js") or tool_input.get("name") == "aa-lane"


def lane_worktrees(root: Path, session: str, key: str) -> list[str]:
    """Worktree directories this lane already made: .tmp-session/wt/<session>-<key>-* (lane.js names them so)."""
    wt = root / ".tmp-session" / "wt"
    prefix = f"{session.lower()}-{key}-"
    try:
        return sorted(str(p) for p in wt.iterdir() if p.is_dir() and p.name.startswith(prefix))
    except OSError:
        return []


def _log(root: Path, what: str) -> None:
    try:
        p = root / HITS_LOG
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"rule": "LANE-1", "what": what[:300]}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def check(tool_input: dict, root: Path = ROOT, proc: Path = Path("/proc")) -> str | None:
    """None when the launch may go ahead, else the refusal message."""
    if not is_lane(tool_input):
        return None
    args = tool_input.get("args")
    if isinstance(args, str):
        # The harness parses a JSON-encoded object (replay S271: 191 lane launches passed args that way and ran); a
        # placeholder such as "__FROM_FILE__" stays one string and the lane breaks (lesson S252).
        try:
            parsed = json.loads(args)
        except json.JSONDecodeError:
            parsed = None
        if not isinstance(parsed, dict):
            return (f"lane.js args is a string that is not a JSON object ({args[:40]!r}): write the args object "
                    f"inline, never a placeholder string.")
        args = parsed
    if not isinstance(args, dict):
        kind = type(args).__name__ if args is not None else "missing"
        return f"lane.js args must be a JSON object, got {kind}."
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
    existing = lane_worktrees(root, session, str(args["key"]))
    if existing and args.get("resume") is not True:
        return (f"the worktree(s) of lane {args['key']} already exist: {', '.join(existing)}. Relaunch it with "
                f"resume: true in args (the lane then reports resumed_state and continues from git status/log), or "
                f"remove the stale worktree(s) first (git -C <repo> worktree remove <path>) to start over.")
    avail = aa_shell_guard.mem_available_mib(proc)
    if avail is not None and avail < LANE_MEM_FLOOR_MIB:
        ram_gate = str(args.get("ram_gate") or "")
        if re.match(r"skip:\s*\S", ram_gate):
            _log(root, f"ram skip {args.get('key')} at {avail} MiB: {ram_gate}")
            return None
        heavy = [f"pid {p[0]} {p[1]} MiB {p[2]}" for p in aa_shell_guard.processes(proc) if p[2]][:6]
        return (f"MemAvailable is {avail} MiB, under {LANE_MEM_FLOOR_MIB} MiB for a new lane (a lane builds and "
                f"tests; the WSL VM ran out of memory with 3 lanes). Heavy processes: {'; '.join(heavy) or 'none'}. "
                f"Wait for a lane to finish, or add ram_gate: \"skip: <reason>\" to args.")
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
