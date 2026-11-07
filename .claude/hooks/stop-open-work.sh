#!/bin/bash
# AA-1024 G19 (S272): a Stop hook. When the last message offers to stop or asks to go on while the session checklist
# has open, unblocked items, it blocks the stop once and lists them. How it decides: stop_open_work.py.
# Test: python3 .claude/hooks/test_stop_open_work.py
exec python3 "$(dirname "$0")/stop_open_work.py"
