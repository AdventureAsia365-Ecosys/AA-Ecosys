#!/bin/bash
# usage: run_script.sh <local_script.py> [ENV=VAL ...]  -> runs on api task, prints output via S3
NAME=$(basename $1); OUT=${NAME%.py}.txt; shift
aws s3 cp $NAME s3://aa-cis-bronze-005097885195/scripts/$NAME --profile aa365-admin --region us-west-1 --quiet
URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/$NAME --profile aa365-admin --region us-west-1 --expires-in 300)
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
timeout 300 aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/s.py && cd /app && $* PYTHONPATH=/app python3 /tmp/s.py > /tmp/r.txt 2>&1; python3 -c \"import boto3;boto3.client(\\\"s3\\\",region_name=\\\"us-west-1\\\").upload_file(\\\"/tmp/r.txt\\\",\\\"aa-cis-bronze-005097885195\\\",\\\"scripts/$OUT\\\")\"'" --profile aa365-admin --region us-west-1 >/dev/null 2>&1
aws s3 cp s3://aa-cis-bronze-005097885195/scripts/$OUT - --profile aa365-admin --region us-west-1
