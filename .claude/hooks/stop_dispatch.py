#!/usr/bin/env python3
"""Stop / SubagentStop dispatcher (AA-1136 slice 1): the one hook that runs when an agent is about to stop.

Claude Code runs the hooks of one event in parallel, and each one may take the single "block the stop" turn, so the
Stop checks live in ONE script (S284 hooks advisory, section 7):

  1. Stop only: stop_open_work.check() (AA-1024 G19), exactly as before and in every AA_SYNC_HOOKS mode, off included.
     When it blocks, its text goes to stderr with exit 2 and nothing else runs.
  2. Stop and SubagentStop, when AA_SYNC_HOOKS is not off: tools/sync/change_guard.py on every checkout this agent
     wrote (recorded by sync_post_edit.py in .tmp-session/hookstate/<session>-<agent>.json). An agent that wrote
     nothing is not checked. log (default): one line in the hook log, silent. warn / block: refuse the stop once with
     the reminder (each finding once per session + agent; `stop_hook_active` lets the next stop through).

Failure: an error in part 2 is logged and the stop goes through; an error in part 1 is reported on stderr and the
stop goes through (as stop_open_work.py does on its own). Test: python3 .claude/hooks/test_stop_dispatch.py
"""

from __future__ import annotations

import time

_T0 = time.perf_counter()

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "tools" / "sync"))  # the library next to this script, whatever the cwd
import change_guard  # noqa: E402
import hookio  # noqa: E402
import stop_open_work  # noqa: E402


def open_work_reason(data: dict) -> str | None:
    if data.get("hook_event_name", "Stop") != "Stop":
        return None
    try:
        return stop_open_work.check(data)
    except Exception as e:  # noqa: BLE001 - same contract as stop_open_work.main(): a hook bug never traps the session
        print(f"stop_open_work: internal error {type(e).__name__}: {e} (stop allowed)", file=sys.stderr)
        return None


def sync_check(data: dict, m: str) -> tuple[dict, str]:
    """(log record, reminder or '') for the checkouts this agent wrote."""
    event = str(data.get("hook_event_name") or "Stop")
    rec: dict = {"event": event, "hook": "stop_dispatch", "mode": m, "session": hookio.session_key(data),
                 "agent": hookio.agent_key(data),
                 "agent_type": str(data.get("agent_type") or ""),
                 "stop_hook_active": bool(data.get("stop_hook_active"))}
    state = hookio.load_state(data)
    repos = [r for r in state["repos"] if Path(r).is_dir()]
    if not repos:
        rec["outcome"] = "no-writes"
        return rec, ""
    reports = [change_guard.check(Path(r)) for r in repos]
    kinds = {found.kind for r in repos if (found := hookio.find_repo(r))}
    rec["repo_kind"] = "worktree" if "worktree" in kinds else "main"
    rec["checks"] = [r.summary() for r in reports]
    found = [r for r in reports if r.findings]
    rec["would"] = "remind" if found else "none"
    if not found or not hookio.speaks(m) or data.get("stop_hook_active"):
        return rec, ""
    # every finding is marked as said (a list, not any(): any() would stop at the first new one)
    new = [r for r in found if any([hookio.first_time(state, f"stop:{r.top}:{f}") for f in r.findings])]
    if not new:
        return rec, ""
    hookio.save_state(data, state)
    rec["said"] = True
    return rec, "\n\n".join(r.message() for r in new)


def main() -> int:
    data = hookio.read_event()
    reason = open_work_reason(data)
    if reason:
        print(reason, file=sys.stderr)
        return 2
    m = hookio.mode(event=str(data.get("hook_event_name") or "Stop"))
    if m == "off":
        return 0
    text = ""
    try:
        rec, text = sync_check(data, m)
    except Exception as e:  # noqa: BLE001 - a hook bug must never trap the agent
        rec = {"event": str(data.get("hook_event_name") or "Stop"), "hook": "stop_dispatch", "mode": m,
               "agent": hookio.agent_key(data), "error": f"{type(e).__name__}: {e}"[:300]}
    rec["latency_ms"] = round((time.perf_counter() - _T0) * 1000, 1)
    rec["wall_ms"] = hookio.wall_ms()
    hookio.log_event(rec)
    if text:
        print(hookio.clip(text), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
