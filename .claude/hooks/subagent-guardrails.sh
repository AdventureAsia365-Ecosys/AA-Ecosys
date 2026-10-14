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
  # git: allow any global options before the subcommand (e.g. git -C <dir> push)
  'git( +-[cC] +[^ ]+| +--[a-z-]+(=[^ ]+)?)* +push' 'git( +-[cC] +[^ ]+| +--[a-z-]+(=[^ ]+)?)* +reset +--hard'
  'git( +-[cC] +[^ ]+| +--[a-z-]+(=[^ ]+)?)* +clean +-[a-z]*f' 'git( +-[cC] +[^ ]+| +--[a-z-]+(=[^ ]+)?)* +branch +-D'
  'git( +-[cC] +[^ ]+)* +checkout +\.( |$)' 'git( +-[cC] +[^ ]+)* +restore +\.( |$)'
  'git( +-[cC] +[^ ]+)* +rebase .*(main|master)$' 'git( +-[cC] +[^ ]+)* +commit .*--no-verify'
  'gh +pr +(merge|close|create|ready)' 'gh +workflow +run' 'gh +run +rerun' 'gh +secret' 'gh +repo +(create|delete|edit)'
  'gh +api .*(-X *|--method[ =]+)(PUT|POST|PATCH|DELETE)' 'gh +api .* -(f|F) ' 'gh +api .*--(field|raw-field|input)'
  # terraform / aws: allow global options (--profile X --region Y …) before the service
  'terraform( +-[a-z-]+(=[^ ]+)?)* +(apply|destroy|import|state)'
  'aws( +--[a-z-]+( +[^- ][^ ]*)?)* +ecs +(update-service|run-task|stop-task|register-task-definition|execute-command)'
  'aws( +--[a-z-]+( +[^- ][^ ]*)?)* +rds +(stop|start|delete|modify)'
  'aws( +--[a-z-]+( +[^- ][^ ]*)?)* +secretsmanager +(put|create|delete|update)'
  'aws( +--[a-z-]+( +[^- ][^ ]*)?)* +s3 +rm' 'aws( +--[a-z-]+( +[^- ][^ ]*)?)* +iam '
  'aws( +--[a-z-]+( +[^- ][^ ]*)?)* +lambda +(invoke|update|create|delete)'
  'aws( +--[a-z-]+( +[^- ][^ ]*)?)* +ssm +(put|delete|send-command)'
  'aws( +--[a-z-]+( +[^- ][^ ]*)?)* +ecr +(put|delete|batch-delete)'
)
for p in "${patterns[@]}"; do
  if echo "$cmd" | grep -Eq "$p"; then
    echo "BLOCKED for subagents ($p): only the orchestrator merges, pushes, deploys or deletes. Report what you need in your result instead." >&2
    exit 2
  fi
done
exit 0
