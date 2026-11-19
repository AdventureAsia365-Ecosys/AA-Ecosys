#!/bin/bash
# AA-1136 slice 1 (S285): the ONE Stop / SubagentStop hook. Runs stop_open_work.py (AA-1024 G19, unchanged) first,
# then the change guard (tools/sync/change_guard.py) on the checkouts the agent wrote. How it decides: stop_dispatch.py.
# Only exit 2 (refuse the stop once, reason on stderr) passes through; any other failure lets the stop go on.
# /usr/bin/python3 first: the PATH python3 is a mise shim that costs ~0.5 s per start (S285 measure); stdlib only.
# AA_SYNC_T0 = wrapper start, so the log's wall_ms includes the interpreter start.
# Test: python3 .claude/hooks/test_stop_dispatch.py
export AA_SYNC_T0="${EPOCHREALTIME:-}"
PY=/usr/bin/python3
[ -x "$PY" ] || PY=python3
"$PY" "$(dirname "$0")/stop_dispatch.py"
rc=$?
[ "$rc" -eq 2 ] && exit 2
exit 0
