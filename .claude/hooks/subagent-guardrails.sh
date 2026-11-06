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
  # AA-1026: scripts whose AWS / admin-API writes the command line does not show
  '(^|[ /])anthropic_key_plug_in\.sh'
  # AA-1032: the orchestrator ship tools push, merge and dispatch DB Migrate inside their own subprocesses (through
  # as-app.sh), where this hook never sees the command. Any mention is refused, so `cat`/`git add` of these files is
  # too: subagents editing them use the Read/Edit tools and `git add <dir>`. Their tests (test_ship_*.py) stay open.
  # AA-1024: ship_wave.py merges and applies migrations the same way.
  '(^|[ /"'"'"'=(`;&|])(ship_(merge|train|copy_apply|open_prs|wave)\.py|mergeq\.sh|dbmig\.sh|train-lib\.sh|as-app\.sh)'
  '(^|[ ;&|(])-m +ship_(merge|train|copy_apply|open_prs|wave)( |$|[;&|)])'
  # AA-1023: the ECS rollback helper runs update-service and the ECS exec wrapper runs execute-command (game-day seed
  # writes shared.job through it) inside the script, out of this hook's sight. Any mention is refused, as for the ship
  # tools above (dry runs too: they need the MFA session; lanes edit these files with Read/Edit and `git add <dir>`).
  # Their tests (test_ecs_rollback.py, test_ecsx.py, test_gameday_seed_job.py) stay open.
  '(^|[ /"'"'"'=(`;&|])(ecs_rollback|ecsx)\.sh'
  # Vercel CLI moves of the production domain (the MCP request_rollback / request_promote are in the MCP hook).
  '(^|[ ;&|(])(npx +)?vercel( +-[^ ]+( +[^- ][^ ]*)?)* +(rollback|promote|redeploy|deploy +.*--prod)( |$)'
)
for p in "${patterns[@]}"; do
  if echo "$cmd" | grep -Eq "$p"; then
    echo "BLOCKED for subagents ($p): only the orchestrator merges, pushes, deploys or deletes. Report what you need in your result instead." >&2
    exit 2
  fi
done
exit 0
