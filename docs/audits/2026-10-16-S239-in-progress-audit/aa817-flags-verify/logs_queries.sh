#!/usr/bin/env bash
# AA-817 S239 — the read-only log/metadata commands behind logs/ (single-line AWS CLI, acc2).
# Window of the verify run: 2026-10-16T05:15:13Z .. 05:15:50Z (raw/summary.json).
set -euo pipefail
cd "$(dirname "$0")/logs"
S=$(date -d 2026-10-16T05:15:00Z +%s); E=$(date -d 2026-10-16T05:16:30Z +%s); D0=$(date -d 2026-10-16T00:00:00Z +%s); NOW=$(date +%s)

# 1. every api/ log line in the window (one api task: api/api/b931286ceb9d445183d068d5669d3b30)
aws logs filter-log-events --log-group-name /ecs/aa-cis-dev --log-stream-name-prefix api/ --start-time ${S}000 --end-time ${E}000 --profile aa365-admin --region us-west-1 --output json > api_window_raw.json

# 2. Logs Insights (start-query, then get-query-results --query-id <id> > insights_qN.json)
# q1 window: errors / warnings / 5xx / tenant-pool failures
aws logs start-query --log-group-name /ecs/aa-cis-dev --start-time $S --end-time $E --query-string 'fields @timestamp, @logStream, @message | filter @logStream like /^api\// | filter @message like /Traceback|Exception|\[error|\[warning|503|aa817_tenant_context_unavailable|aa817_tenant_guc_not_applied|aa544_flag_read_failed|aa544_tenant_pool_create_failed|tenant pool unavailable|Tenant data path unavailable/ | sort @timestamp asc | limit 200' --profile aa365-admin --region us-west-1 --query queryId --output text
# q2 whole day: tenant-pool failure / privilege errors
aws logs start-query --log-group-name /ecs/aa-cis-dev --start-time $D0 --end-time $NOW --query-string 'fields @timestamp, @logStream, @message | filter @logStream like /^api\// | filter @message like /aa817_tenant_context_unavailable|aa817_tenant_guc_not_applied|aa544_flag_read_failed|aa544_tenant_pool_create_failed|Tenant data path unavailable|integration_secret_tombstone_failed|InsufficientPrivilege|permission denied/ | sort @timestamp asc | limit 200' --profile aa365-admin --region us-west-1 --query queryId --output text
# q3 whole day: pool used per event
aws logs start-query --log-group-name /ecs/aa-cis-dev --start-time $D0 --end-time $NOW --query-string 'fields @timestamp, @message | filter @logStream like /^api\// | filter @message like /aa817_latest_piece|aa544_stage5_fetch_piece|integration_disconnected|DELETE \/v1\/integrations/ | parse @message /(?<evt>aa817_latest_piece|aa544_stage5_fetch_piece|integration_disconnected|DELETE \/v1\/integrations\/\w+ HTTP\/1.1" \d+)/ | parse @message /used_tenant_pool=(?<pool>\w+)/ | stats count() by evt, pool' --profile aa365-admin --region us-west-1 --query queryId --output text
# q4 whole day: pool per api task
aws logs start-query --log-group-name /ecs/aa-cis-dev --start-time $D0 --end-time $NOW --query-string 'fields @timestamp, @logStream, @message | filter @logStream like /^api\// | filter @message like /aa817_latest_piece|aa544_stage5_fetch_piece/ | parse @message /used_tenant_pool=(?<pool>\w+)/ | stats count(), min(@timestamp), max(@timestamp) by @logStream, pool' --profile aa365-admin --region us-west-1 --query queryId --output text
# q5 whole day: latest-piece pool per tenant (False rows all before 03:33:18Z, i.e. before the flag went on)
aws logs start-query --log-group-name /ecs/aa-cis-dev --start-time $D0 --end-time $NOW --query-string 'fields @timestamp, @message | filter @logStream like /^api\// | filter @message like /aa817_latest_piece/ | parse @message /used_tenant_pool=(?<pool>\w+)/ | parse @message /tenant_id=(?<tid>[0-9a-f-]+)/ | stats count(), min(@timestamp), max(@timestamp) by pool, tid' --profile aa365-admin --region us-west-1 --query queryId --output text

# 3. tenant CMS secret metadata only (no value): connect write 05:15:45Z, tombstone 05:15:48Z
aws secretsmanager describe-secret --secret-id acp/cms/20d07d32-ed98-405f-81d5-0c2399c9fcdf --profile aa365-admin --region us-west-1 --query '{Name:Name,LastChangedDate:LastChangedDate,LastAccessedDate:LastAccessedDate,Versions:VersionIdsToStages}' --output json > tenant_cms_secret_describe.json
