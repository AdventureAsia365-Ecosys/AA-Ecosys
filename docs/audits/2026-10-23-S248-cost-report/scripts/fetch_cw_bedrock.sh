#!/usr/bin/env bash
# AA-896 (S248) — Bedrock usage per model (CloudWatch AWS/Bedrock, daily sums) for the unit-cost table.
# Usage: bash fetch_cw_bedrock.sh <END, exclusive, YYYY-MM-DD> <out dir>
#   23/10/2026 run (from the report folder): bash scripts/fetch_cw_bedrock.sh 2026-10-23 data
#   refresh after 01/11:                     bash scripts/fetch_cw_bedrock.sh 2026-11-01 data-final
# Read only. Cost: GetMetricData is 0.01 USD per 1,000 metrics requested; this asks for 48 metrics per account
# (12 model IDs x 4 metrics), so about 0.001 USD per run. CloudWatch keeps daily-aggregatable data for 15 months.
# Model IDs: the ones `aws cloudwatch list-metrics --namespace AWS/Bedrock` showed on acc3/acc1 (us-west-1) in
# October plus the regional/in-Region IDs used in August/September. Add new IDs here when the model mix changes.
set -euo pipefail
END="${1:?END date (exclusive) required}"; OUT="${2:?out dir required}"; mkdir -p "$OUT"
START=2026-08-01
Q="$(mktemp)"; trap 'rm -f "$Q"' EXIT
python3 -I - "$Q" <<'PY'
import json, sys
models = [
    "global.anthropic.claude-haiku-4-5-20251001-v1:0", "global.anthropic.claude-haiku-5-5",
    "global.anthropic.claude-sonnet-4-6", "global.anthropic.claude-sonnet-5", "global.anthropic.claude-sonnet-5-5",
    "global.cohere.embed-v4:0", "global.openai.gpt-5.6-luna", "global.openai.gpt-6-luna",
    "us.anthropic.claude-sonnet-4-6", "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "anthropic.claude-sonnet-4-6", "anthropic.claude-haiku-4-5-20251001-v1:0",
]
metrics = ["Invocations", "InputTokenCount", "OutputTokenCount", "InvocationClientErrors"]
q = [{"Id": f"m{i}_{k}", "Label": f"{m}|{met}", "ReturnData": True,
      "MetricStat": {"Metric": {"Namespace": "AWS/Bedrock", "MetricName": met,
                                "Dimensions": [{"Name": "ModelId", "Value": m}]},
                     "Period": 86400, "Stat": "Sum"}}
     for i, m in enumerate(models) for k, met in enumerate(metrics)]
json.dump(q, open(sys.argv[1], "w"))
PY
for pair in nghiep_aa365:acc3 pqnghiep-admin:acc1; do
  p="${pair%%:*}"; a="${pair##*:}"
  aws cloudwatch get-metric-data --metric-data-queries "file://$Q" --start-time "${START}T00:00:00Z" --end-time "${END}T00:00:00Z" --profile "$p" --region us-west-1 --output json </dev/null > "$OUT/$a-bedrock-metrics.json"
  grep -q '"NextToken"' "$OUT/$a-bedrock-metrics.json" && echo "WARN: $a has more pages" || true
done
echo "done: $OUT"
