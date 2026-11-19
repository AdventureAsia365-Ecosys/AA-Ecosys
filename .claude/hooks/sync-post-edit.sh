#!/bin/bash
# AA-1136 slice 1 (S285): PostToolUse Edit|Write|MultiEdit. Lints the one edited file and points at its docs pages;
# silent in the default log mode (AA_SYNC_HOOKS). How it decides: sync_post_edit.py.
# Never fails the tool call: whatever the script does, this wrapper exits 0 (stdout, the reminder JSON, passes through).
# Test: python3 .claude/hooks/test_sync_post_edit.py
python3 "$(dirname "$0")/sync_post_edit.py"
exit 0
