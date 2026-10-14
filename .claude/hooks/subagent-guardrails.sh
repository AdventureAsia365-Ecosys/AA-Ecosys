#!/bin/bash
# S234 (Nghiệp approved): block release / destructive commands for SUBAGENTS only.
# The orchestrator (main session: no agent_id in the hook input) merges, pushes and deploys;
# workflow / Agent subagents (agent_id present) only code, test and commit locally.
input=$(cat)
read -r agent cmd < <(python3 -c '
import json, sys
d = json.loads(sys.argv[1])
print(d.get("agent_id") or "-", (d.get("tool_input") or {}).get("command", "").replace("\n", " "))
' "$input")
[ "$agent" = "-" ] && exit 0
patterns=(
  'git push' 'gh pr merge' 'gh pr close' 'gh pr create' 'gh pr ready' 'gh workflow run' 'gh run rerun' 'gh secret'
  'gh api -X (PUT|POST|PATCH|DELETE)' 'gh api --method (PUT|POST|PATCH|DELETE)' 'gh repo (create|delete)'
  'terraform (apply|destroy|import|state)' 'aws ecs (update-service|run-task|stop-task|register-task-definition)'
  'aws rds (stop|start|delete|modify)' 'aws secretsmanager (put|create|delete|update)' 'aws s3 rm'
  'git reset --hard' 'git clean -[a-z]*f' 'git branch -D' 'git checkout \.( |$)' 'git restore \.( |$)'
  'git rebase .*(main|master)$' 'git commit .*--no-verify'
  'gh api .* -(f|F) ' 'gh api .*--(field|raw-field|input)' 'aws ecs execute-command' 'aws iam ' 'aws lambda (invoke|update|create|delete)'
  'aws ssm (put|delete|send-command)' 'aws ecr (put|delete|batch-delete)'
)
for p in "${patterns[@]}"; do
  if echo "$cmd" | grep -Eq "$p"; then
    echo "BLOCKED for subagents ($p): only the orchestrator merges, pushes, deploys or deletes. Report what you need in your result instead." >&2
    exit 2
  fi
done
exit 0
