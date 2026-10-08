#!/bin/bash
# usage: run_detached.sh <local_script.py> [ENV=VAL ...] -> starts the script in the background on the api task
NAME=$(basename $1); shift
aws s3 cp $NAME s3://aa-cis-bronze-005097885195/scripts/$NAME --profile aa365-admin --region us-west-1 --quiet
URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/$NAME --profile aa365-admin --region us-west-1 --expires-in 300)
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
timeout 120 aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/$NAME && cd /app && (env $* PYTHONPATH=/app setsid nohup python3 /tmp/$NAME > /tmp/${NAME%.py}.log 2>&1 &) ; sleep 3'" --profile aa365-admin --region us-west-1 >/dev/null 2>&1
echo "started $NAME on $TASK_ARN"
