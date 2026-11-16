#!/bin/bash
# Red-team table for the generic block of subagent-guardrails.sh (subagent-guardrails.d/00-generic.txt).
# Invented names only: the kit's template repo copies this file. Run: bash .claude/hooks/test_subagent_guardrails_generic.sh
H="$(dirname "$0")/subagent-guardrails.sh"; pass=0; fail=0
t(){ want=$1; shift; got=$(python3 -c 'import json,sys;print(json.dumps({"agent_id":"a1","tool_input":{"command":sys.argv[1]}}))' "$*" | "$H" >/dev/null 2>&1; echo $?); if [ "$got" = "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "MISS want=$want got=$got :: $*"; fi; }
main(){ got=$(python3 -c 'import json,sys;print(json.dumps({"tool_input":{"command":sys.argv[1]}}))' "$*" | "$H" >/dev/null 2>&1; echo $?); if [ "$got" = 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "MISS main session refused :: $*"; fi; }
# a subagent must be refused (2)
t 2 git push origin main; t 2 git -C /x push -u origin b; t 2 git -c user.name=x push; t 2 git -C /x reset --hard; t 2 git branch -D foo
t 2 git clean -fd; t 2 git checkout .; t 2 git restore .; t 2 git rebase origin/main; t 2 git commit -m x --no-verify
t 2 gh pr merge 1; t 2 gh pr create --title x; t 2 gh pr ready 1; t 2 gh workflow run ci.yml; t 2 gh run rerun 1; t 2 gh secret set X
t 2 gh api -XPOST repos/x; t 2 gh api -X PATCH repos/x; t 2 gh api --method PUT x; t 2 gh api repos/x -f a=b; t 2 gh repo create x
t 2 terraform apply; t 2 terraform -chdir=x apply; t 2 terraform state rm x
t 2 aws ecs update-service --cluster c; t 2 aws --profile p --region r ecs update-service --cluster c
t 2 aws --profile p ecs execute-command --task t; t 2 aws --region r secretsmanager put-secret-value --secret-id x
t 2 aws iam get-role --role-name x; t 2 aws --profile p s3 rm s3://x; t 2 aws lambda invoke --function-name f out
t 2 aws ssm send-command --document-name d; t 2 aws ecr batch-delete-image --repository-name r
t 2 vercel rollback https://x.example.app; t 2 npx vercel promote https://x.example.app; t 2 vercel deploy --prod
# a subagent may (0)
t 0 git status; t 0 git -C /x log --oneline; t 0 git commit -m msg; t 0 gh pr view 1; t 0 gh api repos/x; t 0 gh pr checks 1
t 0 aws --profile p ecs describe-services --cluster c; t 0 aws s3 cp a s3://b; t 0 terraform plan; t 0 vercel ls
t 0 python3 -m unittest discover -s tests
# the main session (no agent_id) is never refused by this hook
main git push origin main; main terraform apply
echo "pass=$pass fail=$fail"; [ "$fail" = 0 ]
