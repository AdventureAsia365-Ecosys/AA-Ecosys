#!/bin/bash
# Red-team table for subagent-mcp-guardrails.sh: MCP write tools are refused for subagents, reads pass, and the main
# session (no agent_id) is never refused. Invented arguments only: the kit's template repo copies this file.
# Run: bash .claude/hooks/test_subagent_mcp_guardrails.sh
H="$(dirname "$0")/subagent-mcp-guardrails.sh"; pass=0; fail=0
t(){ want=$1; tool=$2; got=$(python3 -c 'import json,sys;print(json.dumps({"agent_id":"a1","tool_name":sys.argv[1],"tool_input":{}}))' "$tool" | "$H" >/dev/null 2>&1; echo $?); if [ "$got" = "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "MISS want=$want got=$got :: $tool"; fi; }
main(){ got=$(python3 -c 'import json,sys;print(json.dumps({"tool_name":sys.argv[1],"tool_input":{}}))' "$1" | "$H" >/dev/null 2>&1; echo $?); if [ "$got" = 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "MISS main session refused :: $1"; fi; }
# a subagent must be refused (2)
t 2 mcp__plugin_github_github__merge_pull_request; t 2 mcp__plugin_github_github__create_pull_request
t 2 mcp__plugin_github_github__push_files; t 2 mcp__plugin_github_github__issue_write
t 2 mcp__claude_ai_Linear__save_issue; t 2 mcp__claude_ai_Linear__save_comment; t 2 mcp__claude_ai_Linear__delete_comment
t 2 mcp__claude_ai_Notion__notion-update-page; t 2 mcp__claude_ai_Notion__notion-create-pages
t 2 mcp__claude_ai_Vercel__create_deployment; t 2 mcp__claude_ai_Vercel__request_promote; t 2 mcp__claude_ai_Vercel__edit_project_env
t 2 mcp__claude_ai_Atlassian__addOrEditJiraIssueComment; t 2 mcp__claude_ai_Atlassian__transitionJiraIssue
# a subagent may read (0)
t 0 mcp__plugin_github_github__get_pull_request; t 0 mcp__claude_ai_Linear__get_issue; t 0 mcp__claude_ai_Linear__list_comments
t 0 mcp__claude_ai_Notion__notion-fetch; t 0 mcp__claude_ai_Vercel__get_deployment; t 0 mcp__claude_ai_Atlassian__getJiraIssue
# the main session is never refused by this hook
main mcp__claude_ai_Linear__save_issue; main mcp__plugin_github_github__merge_pull_request
echo "pass=$pass fail=$fail"; [ "$fail" = 0 ]
