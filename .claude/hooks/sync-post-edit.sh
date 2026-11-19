#!/bin/bash
# AA-1136 slice 1 (S285): PostToolUse Edit|Write|MultiEdit. Lints the one edited file and points at its docs pages;
# silent in the default log mode (AA_SYNC_HOOKS). How it decides: sync_post_edit.py.
# Test: python3 .claude/hooks/test_sync_post_edit.py
# Never fails the tool call: whatever the script does, this wrapper exits 0 (stdout, the reminder JSON, passes through).
# /usr/bin/python3 first: the PATH python3 is a mise shim that costs ~0.5 s per start (S285 measure); the script needs
# only the stdlib (PyYAML only when the doc-map cache is rebuilt, and that failure is logged, not raised).
# AA_SYNC_T0 = wrapper start, so the log's wall_ms includes the interpreter start.
export AA_SYNC_T0="${EPOCHREALTIME:-}"
PY=/usr/bin/python3
[ -x "$PY" ] || PY=python3
"$PY" "$(dirname "$0")/sync_post_edit.py"
exit 0
