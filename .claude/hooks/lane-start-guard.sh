#!/bin/bash
# AA-1024 G12 (S271): a lane workflow (tools/workflows/lane.js) starts only when plan.json is on this session and the
# lane's issue is slotted in it. PreToolUse hook for the Workflow tool. Rules: lane_start_guard.py.
# Test: python3 .claude/hooks/test_lane_start_guard.py
exec python3 "$(dirname "$0")/lane_start_guard.py"
