#!/bin/bash
# Run a Python script inside a running CIS container over ECS exec and get ALL of its output back, via S3.
#
#   tools/ecs/ecsx.sh <script.py> [VAR=value ...]          # api task (default)
#   ECSX_SERVICE=aa-cis-dev-worker ECSX_CONTAINER=worker tools/ecs/ecsx.sh <script.py>
#
# Why: the SSM terminal of ECS exec drops long stdout and can end the process with it (lesson log, S237 → S253).
# Here the session only starts tools/ecs/ecsx_runner.py, which detaches, runs the script with cwd /app, and puts
# the output on the bronze bucket (scripts/out/); this side waits for the .done marker, prints the output, removes
# the objects and exits with the script's exit code. The script reads DATABASE_URL (cis_app) like any ECS exec
# script; VAR=value pairs become its environment. Orchestrator only (the subagent hook blocks ECS exec).
# CIS containers only: the CRM task role cannot write the bronze bucket.
set -euo pipefail
script=${1:?usage: ecsx.sh <script.py> [VAR=value ...]}; shift
P="--profile ${ECSX_PROFILE:-aa365-admin} --region us-west-1"
B=${ECSX_BUCKET:-aa-cis-bronze-005097885195}
SVC=${ECSX_SERVICE:-aa-cis-dev-api}; CTR=${ECSX_CONTAINER:-api}; WAIT=${ECSX_TIMEOUT:-900}
for kv in "$@"; do [[ $kv =~ ^[A-Za-z_][A-Za-z0-9_]*=[A-Za-z0-9_.:,/@+-]*$ ]] || { echo "ecsx: bad VAR=value: $kv" >&2; exit 2; }; done
id=$(date -u +%Y%m%dT%H%M%S)-$$-$(basename "$script" .py)
here=$(cd "$(dirname "$0")" && pwd)
aws s3 cp "$script" s3://$B/scripts/ecsx/$id.py $P --quiet
aws s3 cp "$here/ecsx_runner.py" s3://$B/scripts/ecsx/$id.runner.py $P --quiet
U1=$(aws s3 presign s3://$B/scripts/ecsx/$id.py $P --expires-in 600)
U2=$(aws s3 presign s3://$B/scripts/ecsx/$id.runner.py $P --expires-in 600)
TASK=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name "$SVC" $P --query 'taskArns[0]' --output text)
OUT=scripts/out/$id.txt
# The exec call itself can hang (the SSM session never closes): bound it; the runner is detached, so a cut session
# after the start is harmless.
timeout 90 aws ecs execute-command --cluster aa-cis-dev-cluster --task "$TASK" --container "$CTR" --interactive \
  --command "sh -c 'curl -sf \"$U1\" -o /tmp/$id.py && curl -sf \"$U2\" -o /tmp/$id.runner.py && $* python3 /tmp/$id.runner.py /tmp/$id.py $B $OUT'" \
  $P 2>&1 | grep -q "ECSX_STARTED" || echo "ecsx: started (session output not seen, normal when SSM drops it); waiting for the result" >&2
aws s3 rm s3://$B/scripts/ecsx/$id.py $P --quiet; aws s3 rm s3://$B/scripts/ecsx/$id.runner.py $P --quiet
t=0; until aws s3api head-object --bucket $B --key $OUT.done $P >/dev/null 2>&1; do
  sleep 3; t=$((t+3)); [ $t -ge $WAIT ] && { echo "ecsx: no result after ${WAIT}s (s3://$B/$OUT)" >&2; exit 3; }; done
done_line=$(aws s3 cp s3://$B/$OUT.done - $P)
aws s3 cp s3://$B/$OUT - $P
aws s3 rm s3://$B/$OUT $P --quiet; aws s3 rm s3://$B/$OUT.done $P --quiet
echo "ecsx: $done_line" >&2
rc=${done_line#rc=}; exit ${rc%% *}
