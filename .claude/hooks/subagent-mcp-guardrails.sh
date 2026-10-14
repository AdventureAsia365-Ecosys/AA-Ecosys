#!/bin/bash
# S235 (architect R6): the Bash guardrail does not cover MCP tools. Block MCP write tools for SUBAGENTS only
# (hook input has agent_id); the orchestrator (no agent_id) keeps full access. Subagents may still read.
input=$(cat)
read -r agent tool < <(python3 -c '
import json, sys
d = json.loads(sys.argv[1])
print(d.get("agent_id") or "-", d.get("tool_name") or "")
' "$input")
[ "$agent" = "-" ] && exit 0
# GitHub: anything that changes remote state
if echo "$tool" | grep -Eq '^mcp__plugin_github_github__(merge_|create_|delete_|push_|fork_|update_|add_|issue_write|sub_issue_write|pull_request_review_write|request_copilot_review|run_secret_scanning)'; then blocked=1; fi
# Linear / Notion / Vercel / Atlassian / Canva / Figma / Claude Docs writes
if echo "$tool" | grep -Eq '^mcp__claude_ai_Linear__(save_|create_|delete_|merge_|update_|submit_|resolve_|mark_|share_|unshare_|retire_|restore_|prepare_)'; then blocked=1; fi
if echo "$tool" | grep -Eq '^mcp__claude_ai_Notion__notion-(create|update|delete|move|duplicate|restore|upload|set|send|spawn|stop|convert)'; then blocked=1; fi
if echo "$tool" | grep -Eq '^mcp__claude_ai_Vercel__(create_|update_|delete_|add_|edit_|assign_|buy_|cancel_|pause_|unpause_|put_|patch_|request_|restore_|approve_|complete_|start_|revoke_|activate_|accept_|invalidate_|stage_|upload_|write_|run_session|kill_|stop_|upsert_|replace_|verify_|issue_cert|test_drain|retry_|rerequest_|record_events)'; then blocked=1; fi
if echo "$tool" | grep -Eq '^mcp__claude_ai_Atlassian__(addOrEdit|create|edit|transition|update|executeWrite|executeDestructive)'; then blocked=1; fi
if [ -n "$blocked" ]; then
  echo "BLOCKED for subagents ($tool): only the orchestrator writes to GitHub/Linear/Notion/Vercel/Jira. Report what you need in your result instead." >&2
  exit 2
fi
exit 0
