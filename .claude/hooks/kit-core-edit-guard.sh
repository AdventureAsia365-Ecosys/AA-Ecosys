#!/bin/bash
# AA-994 / root ADR 0016 decision 8: agents never edit a vendored copy of the UI kit core.
# PreToolUse hook for Edit, Write, MultiEdit and NotebookEdit (orchestrator and subagents alike).
#
# Blocks a file path that has a `_kit/core/` or `ui/core/` folder in it (globs `**/_kit/core/**`, `**/ui/core/**`)
# unless the file is the canonical copy: AA-CIS-App `frontend/app/_kit/core/`. The canonical copy is recognised
#   - by git: the file's repo has an `origin` ending in `AA-CIS-App` and the path inside it starts with
#     `frontend/app/_kit/core/` (works in CIS worktrees under .tmp-session/wt/ too), or
#   - by path: it contains `apps/AA-CIS-App/frontend/app/_kit/core/`.
# The path is normalised first (`..`, symlinks), and a relative path is read against the hook input's `cwd`.
# Any other tool, or input it cannot parse, passes (exit 0): the integrity check in each app's CI is the real gate,
# this hook only saves wasted work. Test: bash .claude/hooks/test_kit_core_edit_guard.sh
input=$(cat)
msg=$(python3 - "$input" <<'PY'
import json, os, re, subprocess, sys

try:
    data = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)
if data.get("tool_name") not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
    sys.exit(0)
ti = data.get("tool_input") or {}
raw = ti.get("file_path") or ti.get("notebook_path") or ""
if not isinstance(raw, str) or not raw:
    sys.exit(0)
cwd = data.get("cwd") or os.getcwd()
path = os.path.realpath(os.path.join(cwd, os.path.expanduser(raw)))

COPY = re.compile(r"(^|/)(_kit|ui)/core/")
if not COPY.search(path):
    sys.exit(0)
CANON_REL = "frontend/app/_kit/core/"
if "/apps/AA-CIS-App/" + CANON_REL in path:
    sys.exit(0)


def git(d, *args):
    try:
        r = subprocess.run(["git", "-C", d, *args], capture_output=True, text=True, timeout=5)
    except Exception:
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


d = os.path.dirname(path)
while d and d != "/" and not os.path.isdir(d):
    d = os.path.dirname(d)
top = git(d, "rev-parse", "--show-toplevel") if d else ""
if top:
    rel = os.path.relpath(path, os.path.realpath(top))
    origin = git(d, "remote", "get-url", "origin")
    if re.search(r"[/:]AA-CIS-App(\.git)?/?$", origin) and rel.startswith(CANON_REL):
        sys.exit(0)

print(
    f"BLOCKED: {raw} is a vendored copy of the UI kit core (root ADR 0016). "
    "Edit the CIS canonical copy (AA-CIS-App frontend/app/_kit/core), then sync: "
    "tools/kit/kit-sync.sh <portal|crm-web|booking|tripplanner>. Never edit the copy; "
    "CI integrity (core/check-kit-copy.mjs) rejects it anyway. App-only parts go in the app's local/ folder or barrel."
)
PY
)
if [ -n "$msg" ]; then
  echo "$msg" >&2
  exit 2
fi
exit 0
