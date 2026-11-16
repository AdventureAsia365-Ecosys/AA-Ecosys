#!/bin/bash
# Subagent guardrail (PreToolUse hook for Bash): block release and destructive commands for SUBAGENTS only.
# The orchestrator (main session: no agent_id in the hook input) merges, pushes and deploys; workflow / Agent
# subagents (agent_id present) only code, test and commit locally.
# The patterns live in subagent-guardrails.d/*.txt (one extended regex per line, # comments): 00-generic.txt is the
# kit's generic block, other files are the project's own block. Test: bash .claude/hooks/test_subagent_guardrails.sh
input=$(cat)
read -r agent cmd < <(python3 -c '
import json, sys
d = json.loads(sys.argv[1])
print(d.get("agent_id") or "-", (d.get("tool_input") or {}).get("command", "").replace("\n", " "))
' "$input")
[ "$agent" = "-" ] && exit 0
dir="$(dirname "$0")/subagent-guardrails.d"
found=0
for f in "$dir"/*.txt; do
  [ -f "$f" ] || continue
  found=1
  while IFS= read -r p || [ -n "$p" ]; do
    case "$p" in '' | '#'*) continue ;; esac
    if echo "$cmd" | grep -Eq -- "$p"; then
      echo "BLOCKED for subagents ($p): only the orchestrator merges, pushes, deploys or deletes. Report what you need in your result instead." >&2
      exit 2
    fi
  done < "$f"
done
# No pattern file: refuse rather than let a subagent push through a broken install.
if [ "$found" = 0 ]; then
  echo "BLOCKED for subagents: no pattern file in $dir (the guardrail is not installed correctly)." >&2
  exit 2
fi
exit 0
