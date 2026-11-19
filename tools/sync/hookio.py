#!/usr/bin/env python3
"""Hook I/O for the sync hooks (AA-1136 slice 1): event input, mode switch, repo lookup, state, log, output.

Shared by the Claude Code hooks (`.claude/hooks/sync_post_edit.py`, `.claude/hooks/stop_dispatch.py`), and later by
Kiro hooks, pre-push and CI callers of `change_guard.py`. Python stdlib only, no subprocess: a hook must stay well
under its latency budget (p95 <= 300 ms, docs/implementation-notes/AA-1136.md).

Mode switch `AA_SYNC_HOOKS` (read first by every hook):
  off    the sync hooks do nothing (the Stop dispatcher still runs stop_open_work.py, unchanged)
  log    default: compute everything, append one JSON line per event to the hook log, say nothing, never block
  warn   log + remind the agent (PostToolUse additionalContext; Stop / SubagentStop refuse the stop once)
  block  inside a session the same as warn (the advisory blocks only at push / PR); `change_guard.py check` exits 1

Files (all under <project>/.tmp-session/, gitignored, never in the public repo):
  hooklog.jsonl                       one JSON object per hook event, with latency_ms (AA_SYNC_HOOKLOG overrides)
  hookstate/<session>-<agent>.json    repos the agent wrote + what was already said (AA_SYNC_STATE_DIR overrides)

Failure: every helper here swallows its own I/O errors; a hook never fails closed because of them.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
MODES = ("off", "log", "warn", "block")
DEFAULT_MODE = "log"
MAX_MESSAGE = 1500  # advisory 4.1 rule 4: a reminder is at most ~1,500 characters
_SAFE = re.compile(r"[^A-Za-z0-9_-]+")


def mode(env: dict | None = None) -> str:
    value = ((env if env is not None else os.environ).get("AA_SYNC_HOOKS") or DEFAULT_MODE).strip().lower()
    return value if value in MODES else DEFAULT_MODE


def speaks(m: str) -> bool:
    """True when the mode lets a hook say something to the agent."""
    return m in ("warn", "block")


def log_path() -> Path:
    return Path(os.environ.get("AA_SYNC_HOOKLOG") or ROOT / ".tmp-session" / "hooklog.jsonl")


def state_dir() -> Path:
    return Path(os.environ.get("AA_SYNC_STATE_DIR") or ROOT / ".tmp-session" / "hookstate")


class Timer:
    def __init__(self) -> None:
        self.start = time.perf_counter()

    def ms(self) -> float:
        return round((time.perf_counter() - self.start) * 1000, 1)


def wall_ms(env: dict | None = None, now: float | None = None) -> float | None:
    """Milliseconds since the shell wrapper started (AA_SYNC_T0 = bash $EPOCHREALTIME), interpreter start included.
    None when the wrapper did not set it (a direct `python3 <hook>.py` run)."""
    raw = ((env if env is not None else os.environ).get("AA_SYNC_T0") or "").replace(",", ".")
    try:
        start = float(raw)
    except ValueError:
        return None
    return round(((now if now is not None else time.time()) - start) * 1000, 1)


def read_event(stream=None) -> dict:
    """The hook JSON from stdin; {} when it is missing or not an object."""
    try:
        data = json.loads((stream or sys.stdin).read() or "{}")
    except (ValueError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def agent_key(data: dict) -> str:
    """`main` for the main session, else the subagent id Claude Code passes (agent_id)."""
    return _SAFE.sub("_", str(data.get("agent_id") or "main"))[:64] or "main"


def session_key(data: dict) -> str:
    return _SAFE.sub("_", str(data.get("session_id") or "nosession"))[:64] or "nosession"


def edited_path(data: dict) -> str:
    """The file an Edit / Write / MultiEdit / NotebookEdit call wrote ('' when none)."""
    ti = data.get("tool_input") or {}
    if not isinstance(ti, dict):
        return ""
    return str(ti.get("file_path") or ti.get("notebook_path") or "")


# --- repo lookup --------------------------------------------------------------------------------------------------


@dataclass
class Repo:
    top: Path  # the checkout or worktree that holds the file
    name: str  # repo name (basename of the main checkout: AA-CIS-App, AA-Ecosys, ...)
    kind: str  # "main" (a .git directory) or "worktree" (a .git file)
    rel: str = ""  # the file's path inside `top`, '/'-separated
    main: Path | None = None  # the main checkout (== top for kind "main"; from the worktree's gitdir otherwise)


def _main_of_worktree(git_file: Path) -> Path | None:
    try:
        first = git_file.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return None
    if not first.startswith("gitdir:"):
        return None
    gitdir = Path(first.split(":", 1)[1].strip())
    if not gitdir.is_absolute():
        gitdir = (git_file.parent / gitdir).resolve()
    # <main>/.git/worktrees/<name>  ->  <main>
    parts = gitdir.parts
    if len(parts) >= 3 and parts[-2] == "worktrees" and parts[-3] == ".git":
        return Path(*parts[:-3])
    return None


def find_repo(path: str | Path) -> Repo | None:
    """The git checkout holding `path` (walks up to the nearest .git; no subprocess). None outside any repo."""
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        return None
    start = p if p.is_dir() else p.parent
    for d in (start, *start.parents):
        git = d / ".git"
        try:
            if git.is_dir():
                return Repo(top=d, name=d.name, kind="main", rel=_rel(p, d), main=d)
            if git.is_file():
                main = _main_of_worktree(git)
                return Repo(top=d, name=(main.name if main else d.name), kind="worktree", rel=_rel(p, d), main=main)
        except OSError:
            return None
    return None


def _rel(p: Path, top: Path) -> str:
    try:
        return p.relative_to(top).as_posix()
    except ValueError:
        return ""


# --- state per session + agent ------------------------------------------------------------------------------------


def state_file(data: dict) -> Path:
    return state_dir() / f"{session_key(data)}-{agent_key(data)}.json"


def load_state(data: dict) -> dict:
    try:
        state = json.loads(state_file(data).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    state.setdefault("repos", [])
    state.setdefault("said", [])
    return state


def save_state(data: dict, state: dict) -> None:
    path = state_file(data)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        state["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


def first_time(state: dict, key: str) -> bool:
    """True the first time `key` is said for this session + agent (and records it)."""
    if key in state["said"]:
        return False
    state["said"].append(key)
    return True


# --- log and output -----------------------------------------------------------------------------------------------


def log_event(record: dict) -> None:
    """Append one JSON line to the hook log; never raises."""
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
    try:
        path = log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        pass


def clip(text: str, limit: int = MAX_MESSAGE) -> str:
    return text if len(text) <= limit else text[: limit - 15].rstrip() + "\n  (... cut)"


def context_output(event: str, text: str) -> str:
    """The stdout JSON that adds `text` to the agent's context after a tool call (exit 0)."""
    return json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": clip(text)}})
