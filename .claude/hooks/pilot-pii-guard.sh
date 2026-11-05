#!/bin/bash
# AA-969 part 2 (root ADR 0019 d16): agents never read row-level personal data of tenant tables (counts only).
# PreToolUse hook for Bash (orchestrator and subagents alike). The rules and how it decides: pilot_pii_guard.py.
# Test: python3 -m unittest .claude/hooks/test_pilot_pii_guard.py
exec python3 "$(dirname "$0")/pilot_pii_guard.py"
