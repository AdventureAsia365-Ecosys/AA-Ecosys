#!/bin/bash
# AA-1024 (S271): repeated shell and ship mistakes as refusals (pkill -f, zsh word splitting, export $(...), raw or
# serial merges, heavy commands on low memory). PreToolUse hook for Bash, orchestrator and subagents alike.
# The rules and how it decides: aa_shell_guard.py. Test: python3 .claude/hooks/test_aa_shell_guard.py
exec python3 "$(dirname "$0")/aa_shell_guard.py"
