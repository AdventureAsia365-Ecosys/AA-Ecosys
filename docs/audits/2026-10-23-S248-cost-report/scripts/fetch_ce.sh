#!/usr/bin/env bash
# AA-896 (S248) — raw Cost Explorer pulls for the Aug/Sep/Oct 2026 cost report.
# Usage: bash fetch_ce.sh <END, exclusive, YYYY-MM-DD> <out dir>
#   23/10/2026 run (from the report folder): bash scripts/fetch_ce.sh 2026-10-23 data
#   refresh after 01/11 (wait to 03/11, CE revises ~48 h): bash scripts/fetch_ce.sh 2026-11-01 data-final
#   (the two forecast calls are only meaningful while the month is open; they fail harmlessly after it.)
# Cost: each get-cost-and-usage / get-cost-forecast request is 0.01 USD, billed to the account queried.
# This script makes 11 requests (acc2 6, acc3 4, acc1 1) = 0.11 USD. Read only. One-off audit pull, not a
# production client (DM-10.4: the admin page /admin/platform/cost is the standing source).
set -euo pipefail
END="${1:?END date (exclusive) required}"; OUT="${2:?out dir required}"; mkdir -p "$OUT"
START=2026-08-01
for p in aa365-admin nghiep_aa365 pqnghiep-admin; do aws sts get-caller-identity --profile "$p" --query Account --output text </dev/null >/dev/null; done
# acc2: by service, by record type, by App tag, App x service since tags went live (16/10), forecast to month end
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=DIMENSION,Key=SERVICE --profile aa365-admin --region us-east-1 </dev/null > "$OUT/acc2-service.json"
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=DIMENSION,Key=RECORD_TYPE --profile aa365-admin --region us-east-1 </dev/null > "$OUT/acc2-rectype.json"
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost --group-by Type=TAG,Key=App --profile aa365-admin --region us-east-1 </dev/null > "$OUT/acc2-app.json"
aws ce get-cost-and-usage --time-period Start=2026-10-16,End=$END --granularity MONTHLY --metrics UnblendedCost --group-by Type=TAG,Key=App Type=DIMENSION,Key=SERVICE --profile aa365-admin --region us-east-1 </dev/null > "$OUT/acc2-app-service-since-1016.json"
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost --group-by Type=DIMENSION,Key=USAGE_TYPE --profile aa365-admin --region us-east-1 </dev/null > "$OUT/acc2-usage-type.json"
aws ce get-cost-forecast --time-period Start=$END,End=2026-11-01 --granularity MONTHLY --metric UNBLENDED_COST --profile aa365-admin --region us-east-1 </dev/null > "$OUT/acc2-forecast-oct.json" || true
# acc3 (LLM main): by service, by record type (credits), daily by service from 15/09
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=DIMENSION,Key=SERVICE --profile nghiep_aa365 --region us-east-1 </dev/null > "$OUT/acc3-service.json"
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost --group-by Type=DIMENSION,Key=RECORD_TYPE --profile nghiep_aa365 --region us-east-1 </dev/null > "$OUT/acc3-rectype.json"
aws ce get-cost-and-usage --time-period Start=2026-09-15,End=$END --granularity DAILY --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE --profile nghiep_aa365 --region us-east-1 </dev/null > "$OUT/acc3-daily.json"
aws ce get-cost-forecast --time-period Start=$END,End=2026-11-01 --granularity MONTHLY --metric UNBLENDED_COST --profile nghiep_aa365 --region us-east-1 </dev/null > "$OUT/acc3-forecast-oct.json" || true
# acc1 (LLM fallback): by service
aws ce get-cost-and-usage --time-period Start=$START,End=$END --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=DIMENSION,Key=SERVICE --profile pqnghiep-admin --region us-east-1 </dev/null > "$OUT/acc1-service.json"
for f in "$OUT"/*.json; do grep -q NextPageToken "$f" && echo "WARN: $f has more pages" || true; done
echo "done: $OUT"
