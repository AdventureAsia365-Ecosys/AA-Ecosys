#!/usr/bin/env bash
# AA-1004 (S294) — export 13 months of acc2 Cost Explorer history before the account changes payer
# (Billing Transfer into the company organization). Read only, 4 requests x 0.01 USD = 0.04 USD.
# Usage (from the audit folder): bash scripts/fetch_ce.sh <END exclusive, YYYY-MM-DD> <raw json dir>
#   25/11/2026 run: bash scripts/fetch_ce.sh 2026-11-25 /some/scratch/dir
# Then: python3 scripts/to_csv.py /some/scratch/dir data
# The raw JSON stays outside the repo; only the CSVs (no account number in them) are committed.
set -euo pipefail
END="${1:?END date (exclusive) required}"; OUT="${2:?raw json dir required}"; mkdir -p "$OUT"
START=2025-11-01
aws sts get-caller-identity --profile aa365-admin --query Arn --output text </dev/null >/dev/null
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=DIMENSION,Key=SERVICE --profile aa365-admin --region us-east-1 </dev/null > "$OUT/service.json"
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=TAG,Key=App --profile aa365-admin --region us-east-1 </dev/null > "$OUT/app.json"
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=TAG,Key=Component --profile aa365-admin --region us-east-1 </dev/null > "$OUT/component.json"
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=DIMENSION,Key=RECORD_TYPE --profile aa365-admin --region us-east-1 </dev/null > "$OUT/rectype.json"
for f in "$OUT"/*.json; do grep -q NextPageToken "$f" && echo "WARN: $f has more pages" || true; done
echo "done: $OUT"
