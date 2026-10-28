# Lệnh đã chạy (S255, 28/10/2026, chỉ đọc)

Mỗi lệnh một dòng (WSL2). Cost Explorer tính 0,01 USD mỗi request; Budgets, Pricing, GuardDuty/Access Analyzer/S3/CloudTrail describe miễn phí.

## acc2 (`aa365-admin`) — 9 request CE = 0,09 USD

```
aws ce get-cost-and-usage --time-period Start=2026-08-01,End=2026-10-28 --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=DIMENSION,Key=SERVICE --profile aa365-admin --region us-east-1 --output json
aws ce get-cost-and-usage --time-period Start=2026-08-01,End=2026-10-28 --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=TAG,Key=App --profile aa365-admin --region us-east-1 --output json
aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-28 --granularity MONTHLY --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE Type=DIMENSION,Key=USAGE_TYPE --profile aa365-admin --region us-east-1 --output json
aws ce get-cost-and-usage --time-period Start=2026-10-01,End=2026-10-28 --granularity DAILY --metrics UnblendedCost --group-by Type=TAG,Key=App --profile aa365-admin --region us-east-1 --output json
aws ce get-cost-and-usage --time-period Start=2026-10-01,End=2026-10-28 --granularity MONTHLY --metrics UnblendedCost --group-by Type=TAG,Key=App Type=DIMENSION,Key=SERVICE --profile aa365-admin --region us-east-1 --output json
aws ce get-cost-and-usage --time-period Start=2026-10-20,End=2026-10-28 --granularity MONTHLY --metrics UnblendedCost --group-by Type=TAG,Key=App Type=DIMENSION,Key=SERVICE --profile aa365-admin --region us-east-1 --output json
aws ce get-cost-and-usage --time-period Start=2026-10-01,End=2026-10-28 --granularity MONTHLY --metrics UsageQuantity UnblendedCost --group-by Type=DIMENSION,Key=USAGE_TYPE --profile aa365-admin --region us-east-1 --output json
aws ce get-anomaly-monitors --profile aa365-admin --region us-east-1 --output json
aws ce get-anomaly-subscriptions --profile aa365-admin --region us-east-1 --output json
```

## acc3 (`nghiep_aa365`) — 4 request CE = 0,04 USD

```
aws ce get-cost-and-usage --time-period Start=2026-08-01,End=2026-10-28 --granularity MONTHLY --metrics UnblendedCost NetUnblendedCost --group-by Type=DIMENSION,Key=RECORD_TYPE --profile nghiep_aa365 --region us-east-1 --output json
aws ce get-cost-and-usage --time-period Start=2026-08-01,End=2026-10-28 --granularity MONTHLY --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE --filter '{"Dimensions":{"Key":"RECORD_TYPE","Values":["Usage"]}}' --profile nghiep_aa365 --region us-east-1 --output json
aws ce get-cost-and-usage --time-period Start=2026-10-01,End=2026-10-28 --granularity DAILY --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE --profile nghiep_aa365 --region us-east-1 --output json
aws ce get-anomaly-subscriptions --profile nghiep_aa365 --region us-east-1 --query 'AnomalySubscriptions[].[SubscriptionName,Frequency]' --output text
```

## Miễn phí (acc2, us-west-1 trừ khi ghi khác)

```
aws budgets describe-budgets --account-id <acc2> --profile aa365-admin --region us-east-1
aws pricing get-products --service-code AmazonGuardDuty --filters Type=TERM_MATCH,Field=location,Value="US West (N. California)" --region us-east-1 --profile aa365-admin
aws guardduty list-detectors --profile aa365-admin --region us-west-1
aws accessanalyzer list-analyzers --profile aa365-admin --region us-west-1
aws s3control get-public-access-block --account-id <acc2> --profile aa365-admin --region us-west-1
aws cloudtrail describe-trails --profile aa365-admin --region us-west-1
aws cloudtrail get-event-selectors --trail-name aa-cis-dev-trail --profile aa365-admin --region us-west-1
aws securityhub describe-hub --profile aa365-admin --region us-west-1
aws configservice describe-configuration-recorders --profile aa365-admin --region us-west-1
aws s3api get-public-access-block --bucket <each bucket> --profile aa365-admin --region us-west-1
aws s3api get-bucket-policy-status --bucket <each bucket> --profile aa365-admin --region us-west-1
aws s3 cp s3://aa-cis-dev-cloudtrail-logs-<acc2>/AWSLogs/<acc2>/CloudTrail/us-west-1/2026/10/26/ <tmp>/ --recursive --profile aa365-admin --region us-west-1
```

Một ngày log CloudTrail (26/10) được tải về thư mục tạm, đếm bằng `python3 -I` (gzip + json), rồi xoá.
