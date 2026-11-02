#!/bin/bash
# Red-team table for subagent-guardrails.sh (S235). Run: bash .claude/hooks/test_subagent_guardrails.sh
H="$(dirname "$0")/subagent-guardrails.sh"; pass=0; fail=0
t(){ want=$1; shift; got=$(python3 -c 'import json,sys;print(json.dumps({"agent_id":"a1","tool_input":{"command":sys.argv[1]}}))' "$*" | "$H" >/dev/null 2>&1; echo $?); if [ "$got" = "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "MISS want=$want got=$got :: $*"; fi; }
# must block (2)
t 2 git push origin main; t 2 git -C /x push -u origin b; t 2 git -c user.name=x push; t 2 git -C /x reset --hard; t 2 git branch -D foo
t 2 gh pr merge 1; t 2 gh pr create --title x; t 2 gh api -XPOST repos/x; t 2 gh api -X PATCH repos/x; t 2 gh api --method PUT x; t 2 gh api repos/x -f a=b; t 2 gh repo create x
t 2 terraform apply; t 2 terraform -chdir=x apply; t 2 aws ecs update-service --cluster c; t 2 aws --profile p --region r ecs update-service --cluster c
t 2 aws --profile aa365-admin ecs execute-command --task t; t 2 aws --region us-west-1 secretsmanager put-secret-value --secret-id x
t 2 aws iam get-role --role-name x; t 2 aws --profile p iam list-roles; t 2 aws --profile p s3 rm s3://x
t 2 tools/llm/anthropic_key_plug_in.sh --apply; t 2 bash tools/llm/anthropic_key_plug_in.sh --check; t 2 cat k \| tools/llm/anthropic_key_plug_in.sh --apply
t 2 python3 tools/github/ship_merge.py cis#1230; t 2 tools/github/ship_merge.py --check-only cis#1230; t 2 ./ship_train.py cis /x feat/a:1
t 2 tools/github/ship_copy_apply.py cis 330; t 2 python3 -u /home/x/tools/github/ship_open_prs.py wf_1; t 2 tools/github/dbmig.sh cis/330 apply
t 2 tools/github/mergeq.sh AA-CIS-App 1; t 2 tools/github/as-app.sh --repos AA-Ecosys -- gh api repos/x; t 2 . tools/github/train-lib.sh
t 2 bash -c "tools/github/ship_merge.py root#1"; t 2 cd tools/github \&\& python3 -m ship_merge root#1; t 2 X=1 ship_copy_apply.py cis 330
t 2 bash tools/ops/ecs_rollback.sh aa-booking-dev-api --previous --apply; t 2 tools/ops/ecs_rollback.sh aa-crm-dev-api --to 118 --apply
t 2 ./ecs_rollback.sh aa-crm-dev-api --list; t 2 bash -c "tools/ops/ecs_rollback.sh x --to 1 --apply"
t 2 tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=seed; t 2 ECSX_SERVICE=aa-booking-dev-api tools/ecs/ecsx.sh x.py
t 2 bash /home/x/tools/ecs/ecsx.sh --resume r1 0; t 2 cd tools/ecs \&\& ./ecsx.sh s.py
t 2 vercel rollback https://x.vercel.app --scope t; t 2 npx vercel promote https://x.vercel.app; t 2 vercel --scope t redeploy u
t 2 vercel deploy --prod
# must allow (0)
t 0 python3 -m unittest discover -s tools/ops -p 'test_*.py'; t 0 python3 tools/ops/test_ecs_rollback.py
t 0 python3 tools/ecs/test_ecsx.py; t 0 python3 -m unittest tools/ops/test_gameday_seed_job.py; t 0 vercel ls; t 0 vercel inspect u
t 0 python -m unittest discover -s tools/github -p 'test_*.py'; t 0 python3 tools/github/test_ship_merge.py; t 0 python3 -m unittest test_ship_copy_apply
t 0 python3 tools/github/ship_common.py mfa; t 0 bash tools/llm/test_anthropic_key_plug_in.sh
t 0 git status; t 0 git -C /x log --oneline; t 0 git commit -m msg; t 0 gh pr view 1; t 0 gh api repos/x; t 0 gh pr checks 1
t 0 aws --profile p ecs describe-services --cluster c; t 0 aws s3 cp a s3://b; t 0 terraform plan; t 0 aws --profile p secretsmanager get-secret-value --secret-id x
echo "pass=$pass fail=$fail"; [ "$fail" = 0 ]
