#!/usr/bin/env bash
# AA-833 post-burst read-only check (S239). Run ~10 min after aa833-burst.py finishes.
# Usage: bash aa833-postcheck.sh <burst_start_utc e.g. 2026-10-16T03:40:00Z>
# Writes aa833-after-*.json next to this script and prints a one-line summary per metric.
set -euo pipefail
cd "$(dirname "$0")"
SINCE="${1:?burst start UTC}"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
P="--profile aa365-admin --region us-west-1"
for n in aa-tripplanner-dev-browse-throttles aa-tripplanner-dev-assembly-throttles; do
  aws cloudwatch describe-alarm-history --alarm-name "$n" --history-item-type StateUpdate --start-date 2026-10-15T12:35:00Z $P --output json > "aa833-after-history-$n.json"
  echo "$n state=$(aws cloudwatch describe-alarms --alarm-names "$n" $P --query 'MetricAlarms[0].StateValue' --output text) flips_since_15/10_12:35Z=$(python3 -c "import json;print(len(json.load(open('aa833-after-history-$n.json'))['AlarmHistoryItems']))")"
done
for f in aa-tripplanner-dev-browse aa-tripplanner-dev-assembly; do
  for m in Throttles Invocations Errors ConcurrentExecutions; do
    st=Sum; [ "$m" = ConcurrentExecutions ] && st=Maximum
    aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name "$m" --dimensions Name=FunctionName,Value="$f" --start-time "$SINCE" --end-time "$NOW" --period 60 --statistics "$st" $P --output json > "aa833-after-$f-$m.json"
    python3 -c "import json;v=[x['$st'] for x in json.load(open('aa833-after-$f-$m.json'))['Datapoints']];print('$f $m $st', sum(v) if '$st'=='Sum' else max(v or [0]))"
  done
done
