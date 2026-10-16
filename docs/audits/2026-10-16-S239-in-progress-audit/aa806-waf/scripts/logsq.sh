#!/usr/bin/env bash
# usage: logsq.sh <start-iso> <end-iso> <query> <outfile>
set -euo pipefail
S=$(date -d "$1" +%s); E=$(date -d "$2" +%s)
QID=$(aws logs start-query --log-group-name aws-waf-logs-aa-cis-dev --start-time "$S" --end-time "$E" --query-string "$3" --profile aa365-admin --region us-west-1 --query queryId --output text)
until st=$(aws logs get-query-results --query-id "$QID" --profile aa365-admin --region us-west-1 --query status --output text) && [ "$st" != "Running" ] && [ "$st" != "Scheduled" ]; do sleep 2; done
aws logs get-query-results --query-id "$QID" --profile aa365-admin --region us-west-1 --output json > "$4"
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(d['status'],len(d['results']),d.get('statistics'))" "$4"
