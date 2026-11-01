---
id: OPS-08-s263-alert-diet
title: "Alerting diet: keep, remove and move-in-app table for every CloudWatch alarm (S263)"
description: "The decision table the S263 alert diet follows: every one of the 101 acc2 alarms, the custom metrics, the dashboard and the log groups, with keep / remove / move-in-app, the replacement check and its test, and the expected monthly cost after the change."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-01
review_every_days: 30
related: [OPS-08-s263-alerting-cost, AA-1025]
---

# Alerting diet (S263, AA-1025)

The tech lead approved the savings proposals of the [cost audit](README.md) and asked to keep only what is truly
necessary. This page is the table the change follows; it was written before the code.

## 1. Principle

CloudWatch keeps only the signals an app cannot see itself:

- **a service is down** (no healthy target behind the ALB, one alarm per service, CIS api included);
- **shared infrastructure health** the apps cannot measure: RDS CPU, free storage and instance connections; the NAT
  recover action; the Lambda functions with no app behind them (Cognito triggers, TripPlanner, the snapshot-expiry
  and TripPlanner jobs functions);
- **what AWS requires or only AWS sees**: SES bounce and complaint rates, the break-glass token, CRM KMS decrypts;
- the security EventBridge rules (free) and the budgets (free) stay as they are.

Everything an app can read from its own database or its own process (job queues, connection limits, audit export
lag, membership feed, log events such as a failed cost-log write) becomes an **in-app check** evaluated by the
loop that already exists in each app (CIS `api/core/ops_metrics_sampler.py`, Booking and AA-Partner
`JobMetricsSampler`), at $0. The CloudWatch alarm, its metric filter and the custom metric it fed are removed.

### 1.1 How an in-app check alerts

| | CIS | Booking | AA-Partner (CRM) |
|---|---|---|---|
| Evaluated by | api ops sampler tick (5 min); log events also flushed by the worker loop | `JobMetricsSampler` tick (5 min) | `JobMetricsSampler` tick (5 min) |
| Admin bell | yes: `shared.notifications`, event `platform.ops_check.<check>`, roles `admin` | no (staff bell is case-level) | no (no AA-staff bell in the CRM) |
| E-mail | SNS publish to the alerts topic (`ALERTS_TOPIC_ARN`) | same topic | same topic |
| Dedupe | advisory-locked bell: one bell per check per 6 h, one e-mail per check per UTC day | ledger row `bk_ops_alert` in `booking.job` (idempotency key per check per UTC day) | ledger row `crm_ops_alert` in `crm.job` (key per check and day, or per event id) |
| Needs | `sns:Publish` on the topic (task role) | `sns:Publish` + env `ALERTS_TOPIC_ARN` | `sns:Publish` + env `ALERTS_TOPIC_ARN` |

Why the SNS topic and not the CIS SES `ops_alert_email` job: the topic **is** the path the removed alarms used, so
the recipients do not change (the bootstrap subscription plus the addresses managed on Platform › Alert recipients,
AA-913), and a stuck or dead job worker cannot delay the e-mail that says the worker is stuck. SNS e-mail is inside
the free tier (1,000 e-mails a month; ~375 a month today, fewer after the diet).

Dedupe through the job table (Booking, CRM): the sampler inserts one `succeeded` row with the alert's idempotency key
before it publishes (`INSERT ... ON CONFLICT DO NOTHING`); only the process whose insert wins publishes, so two API
tasks or a restart never send twice; a failed publish deletes the row so the next tick retries. The rows are the
history of sent alerts and age out with the normal job retention.

## 2. Alarms (101 on 01/11/2026, plus 1 new and 1 added the same day by Infra #581)

Legend: **Keep** (stays in CloudWatch), **Remove** (no replacement needed, reason given), **Move** (becomes an in-app
check), **Replace**. "OK mail" = whether the alarm still e-mails on recovery: kept for state alarms, dropped for
event alarms (one e-mail per incident instead of two).

### 2.1 CIS (`aa-cis-dev-*`, 38)

| Alarm | Decision | Why / replacement | OK mail |
|---|---|---|---|
| `rds-cpu-high` | Keep | RDS health, not visible to the apps | yes |
| `rds-free-storage-low` | Keep | RDS health | yes |
| `rds-connections-high` | Keep | the one instance-level connections alarm (60 % of `max_connections`) | yes |
| `rds-freeable-memory-low` | Remove | never fired (live floor ~520 MB); CPU + connections catch the usual causes on Dev | — |
| `rds-cpu-surplus-credits-charged` | Remove | a cost symptom; the account budget and Cost Explorer show it | — |
| `rds-read-latency-high`, `rds-write-latency-high`, `rds-disk-queue-depth-high` | Remove | never fired; weekly `pg_stat_statements` review (C4.3) covers slow I/O on Dev | — |
| `rds-max-used-xid-high` | Move (CIS) | check `rds_xid_age`: `max(age(datfrozenxid))` > 1,000,000,000 | — |
| `rds-role-connections-{tripplanner,booking,aa_app_user,cis_app,db_migrator,crm_app}` (6) | Move (CIS) | check `rds_role_connections`: any LOGIN role with a CONNECTION LIMIT above 80 % (same query as before) | — |
| `rds-role-connections-sampling-stopped` | Remove | the sampler runs in the api; the api being down is the new `api-no-healthy-task` alarm | — |
| `rds-cis-app-too-many-connections` (log filter) | Move (CIS) | log event `cis_app_too_many_connections` (a line containing `too many connections for role "cis_app"`) | — |
| `jobs-queue-age` | Move (CIS) | check `jobs_starved`: capacity-aware oldest starved queued age > 900 s (same `shared/jobs/backlog.py` sample) | — |
| `jobs-overdue-running` | Move (CIS) | check `jobs_overdue`: running past 2 x expected seconds | — |
| `jobs-sampling-stopped` | Remove | see `rds-role-connections-sampling-stopped` | — |
| `api-5xx`, `api-latency-p95` | Remove | an outage is `api-no-healthy-task`; an app error that answers 5xx is a Sentry event (all three apps report to Sentry) | — |
| `ecs-running-tasks-low` | **Replace** | blind (Container Insights is off): replaced by `aa-cis-dev-api-no-healthy-task` (ALB `HealthyHostCount` < 1 for 5 min) | yes |
| `{llm_call_log,decision_log,llm_shadow_log,dfs_call_log}-write-failed` (4, log filters) | Move (CIS) | log events of the same names (and their `_sync` variants), captured in the api and worker processes | — |
| `tenant-flag-read-failed`, `tenant-flag-unrecognized`, `tenant-pool-unavailable`, `tenant-guc-not-applied` (log filters) | Move (CIS) | log events `aa817_tenant_*` of the same names | — |
| `tenant-route-admin-pool` (log filter) | Move (CIS) | a line with `used_tenant_pool = false` whose event is not a known deliberate rollback (`publish_log_listed`) | — |
| `acp-piece-held-rate-high`, `acp-grounding-score-floor`, `acp-repair-count-high` | Remove | their only emitter (`services/acp_produce/metrics.py`) has no caller in production: the alarms could never fire. Held pieces are reviewed in `/admin/atom-curation`. The dead emitter is deleted | — |
| `acp-dlq-depth` | Remove | the `aa-cis-dev-acp-events` bus has no rule left, so nothing can reach the DLQ (the queue itself stays) | — |
| `rds-snapshot-expiry-errors` | Keep | Lambda with no app behind it | no |
| `rds-snapshot-expiry-copy-age-aa-cis-dev-db` | Keep | CRM-14 promise (erased data leaves every backup within 30 days); only AWS sees snapshots | yes |

### 2.2 AA-Partner (`aa-crm-dev-*`, 22)

| Alarm | Decision | Why / replacement | OK mail |
|---|---|---|---|
| `no-healthy-task`, `portal-no-healthy-task`, `web-no-healthy-task` | Keep | service down | yes |
| `unhealthy-hosts`, `portal-unhealthy-hosts`, `web-unhealthy-hosts` | Remove | one task per service: the same event as `*-no-healthy-task` (two e-mails per incident) | — |
| `portal-target-5xx`, `cpu-high` | Remove | Sentry / no autoscaling on Dev | — |
| `kms-decrypt-anomaly` | Keep | someone decrypting outside the app is invisible to the app (design v3 §4.1) | no (already alarm-only) |
| `jobs-queue-age`, `jobs-overdue-running` | Move (CRM) | checks `jobs_stuck`, `jobs_overdue` from `crm.job` (same SQL as the sampler) | — |
| `jobs-sampling-stopped` | Remove | the worker runs in the API process: the API down is `no-healthy-task`; the minute heartbeat job shows a dead worker loop as `jobs_stuck` | — |
| `audit-export-lag`, `audit-partitions`, `audit-verify-lag` | Move (CRM) | checks of the same names and thresholds (180 min, < 1 month ahead, 50 h) from `crm.audit_export_agencies()` / `crm.audit_partition_bounds()` | — |
| `bulk-reveal` | Move (CRM) | event `bulk_reveal` raised where `crm_bulk_reveal` is logged (60 reveals per member per hour); one e-mail per member and hour | — |
| `breakglass-opened`, `breakglass-owner-not-mailed` | Move (CRM) | events raised next to the log lines; one e-mail per break-glass session (design v3 §4.8 L3 "alert every time") | — |
| `membership-feed-stuck` | Move (CRM) | event raised where `crm_membership_feed_stuck` is logged; one e-mail per UTC day | — |
| `membership-apply-refused` | Move (CRM) | event per refused CIS event id | — |
| `ops-release-incomplete-t21`, `ops-release-withdrawn` | Move (CRM) | events per ops release id, raised where the lines are emitted | — |

### 2.3 Identity (`aa-identity-dev-*`, 15)

| Alarm | Decision | Why | OK mail |
|---|---|---|---|
| `{workforce,external}-{pre-sign-up,pre-token}-errors` (4) | Keep | Cognito triggers have no app behind them | no |
| `*-throttles` (4), `*-duration-p99` (4) | Remove | a throttled or timed-out trigger fails the sign-in, which shows as `Errors` (Cognito kills a trigger at 5 s) | — |
| `trigger-unexpected-error` (log filter, default value 0 = always billed) | Remove | an unexpected exception refuses the sign-in: it is an `Errors` datapoint too | — |
| `waf-blocked` | Remove | the WAF does its job; blocked requests stay in the WAF log | — |
| `breakglass-token-issued` | Keep | only the trigger log sees the break-glass account; the metric filter loses `default_value` so the metric is billed only in hours with a token | no |

### 2.4 Booking (`aa-booking-dev-*`, 8)

| Alarm | Decision | Why / replacement | OK mail |
|---|---|---|---|
| `no-healthy-task` | Keep | service down | yes |
| `unhealthy-hosts`, `uptime` (ops-probe GET of `/booking/health`) | Remove | the same event as `no-healthy-task`; the 5-minute uptime schedule is removed with it | — |
| `api-5xx`, `cpu-high` | Remove | Sentry / no autoscaling on Dev | — |
| `jobs-queue-age`, `jobs-overdue-running` | Move (Booking) | checks `jobs_stuck`, `jobs_overdue` from `booking.job` | — |
| `jobs-sampling-stopped` | Remove | worker in the API process; API down = `no-healthy-task` | — |

### 2.5 TripPlanner, shared, e-mail, autoscaling, security digest (18 + 1)

| Alarm | Decision | Why | OK mail |
|---|---|---|---|
| `aa-tripplanner-dev-browse-errors`, `-assembly-errors` | Keep | Lambda, no other observer | no |
| `aa-tripplanner-dev-browse-throttles` | Keep | fired 8 times in 30 days: a real signal | no |
| `aa-tripplanner-dev-assembly-throttles` | Remove | never fired; errors alarm stays | — |
| `aa-tripplanner-dev-jobs-errors` | Keep | daily retention / redaction jobs (DM-6.6) | no |
| `aa-tripplanner-dev-jobs-not-run` | Keep | the only signal that the redaction schedule stopped | yes |
| `aa-ecosys-dev-nat-system-check-recover` | Keep | the recover action itself | yes |
| `aa-ecosys-dev-nat-status-check-failed` | Remove | duplicate e-mail of the recover alarm for the system part; an instance-level failure stops all egress, which every app's no-healthy-task / job checks show | — |
| `aa-email-dev-bounce-rate`, `aa-email-dev-complaint-rate` | Keep | SES requires them | yes |
| `aa-sec-dev-admin-session-digest-errors` (Infra #581, 01/11) | Keep | Lambda with no app behind it | no |
| `TargetTracking-*` (8, api + worker x CPU + memory x High + Low) | Remove | the four target-tracking policies are removed on Dev (1 api + 1 worker task; a wave scales the worker by hand, `docs/ops/job-kinds.md`). The scalable targets (1..3) stay, so the documented scale commands still work | — |

## 3. Other CloudWatch items

| Item | Decision |
|---|---|
| Dashboard `aa-cis-dev-pipeline` | Remove (module `monitoring`); the admin overview shows the same ECS numbers |
| Custom metrics `AA/RDS` RoleConnections / RoleConnectionLimitPct, `AA/Jobs/CIS`, `AA/Jobs/Booking`, `AA/Jobs/Crm` (7 incl. `MailIngestDropped`, `RevealsPerMemberPeakHour`, 3 audit) | Stop publishing (the samplers no longer call PutMetricData; the IAM grants go) |
| Custom metrics `aa-cis/ops`, `AA/Crm/*`, `AA/RDS CisAppTooManyConnections`, `AA/Identity TriggerUnexpectedError` | Their 20 metric filters are removed |
| Custom metrics kept | `AA/Crm/Kms DecryptCalls` (anomaly band), `AA/RDS BackupCopyMaxAgeDays` + retention (copy age), `AA/Identity BreakglassTokenIssued` (only when used) |
| Log group `/aa-cis-dev/diagnostic/vpc-flow-logs` | 365 -> 30 days; flow logs record `REJECT` traffic only (security signal kept, ~95 % less ingest) |
| Log group `aws-waf-logs-aa-cis-dev` | 365 -> 30 days on Dev; logging filter keeps `BLOCK` and `COUNT` requests only (allowed requests are dropped) |
| Log group `/aws/apigateway/welcome` | imported into Terraform with 30 days |
| Security EventBridge rules, budgets, cost anomaly monitor, SES configuration sets | Unchanged (free) |

## 4. Controls that moved from CloudWatch to the apps

| Control | Old alarm | New in-app check | Test |
|---|---|---|---|
| CIS job queue starved | `aa-cis-dev-jobs-queue-age` | `shared/ops_checks.py` `jobs_starved` (api sampler) | `tests/unit/test_s263_ops_checks.py` |
| CIS job overdue | `aa-cis-dev-jobs-overdue-running` | `jobs_overdue` | same |
| Per-role CONNECTION LIMIT | `aa-cis-dev-rds-role-connections-*` (6) | `rds_role_connections` | same |
| XID wraparound | `aa-cis-dev-rds-max-used-xid-high` | `rds_xid_age` | same |
| cis_app refused connection | `aa-cis-dev-rds-cis-app-too-many-connections` | log event `cis_app_too_many_connections` | same |
| Cost / decision log write lost | `aa-cis-dev-*-write-failed` (4) | log events `*_write_failed` | same |
| Tenant pool fail-closed states | `aa-cis-dev-tenant-*` (5) | log events `aa817_tenant_*`, admin-pool route | same |
| Booking job queue stuck / overdue | `aa-booking-dev-jobs-queue-age`, `-overdue-running` | `app/jobs/ops_checks.py` `jobs_stuck`, `jobs_overdue` | `backend/tests/unit/test_ops_checks.py` |
| CRM job queue stuck / overdue | `aa-crm-dev-jobs-queue-age`, `-overdue-running` | `app/observability/ops_alerts.py` `jobs_stuck`, `jobs_overdue` | `api/tests/unit/test_ops_alerts.py` |
| CRM audit export lag / partitions / verify lag | `aa-crm-dev-audit-*` (3) | `audit_export_lag`, `audit_partitions`, `audit_verify_lag` | same |
| CRM bulk reveal | `aa-crm-dev-bulk-reveal` | event `bulk_reveal` | same + `test_reveal_meter.py` |
| CRM break-glass | `aa-crm-dev-breakglass-opened`, `-owner-not-mailed` | events `breakglass_opened`, `breakglass_owner_not_mailed` | same |
| CRM membership feed | `aa-crm-dev-membership-feed-stuck`, `-apply-refused` | events `membership_feed_stuck`, `membership_apply_refused` | same |
| CRM ops release | `aa-crm-dev-ops-release-incomplete-t21`, `-withdrawn` | events `ops_release_incomplete_t21`, `ops_release_withdrawn` | same |

## 5. Expected cost (acc2, list prices, no free tier)

| | Before (Nov forecast) | After |
|---|---:|---:|
| Alarms (alarm-metric units x 0.10 USD) | 105 -> ~10.5 USD | 28 -> 2.80 USD (25 alarms incl. the new CIS one and the #581 digest one; copy-age 2 metrics, KMS anomaly 3) |
| Custom metrics (x 0.30 USD) | ~28 -> ~8.1-9 USD | ~3 -> ~0.90 USD |
| Dashboard | ~2.3-3 USD | 0 |
| API requests, SNS, SES, EventBridge, Lambda | ~0.1 USD | ~0.05 USD |
| **Alerting total** | **~21 USD/month** | **~3.8 USD/month** |
| Logs (vended VPC flow + WAF, ingest) | ~3.0 USD (Oct) | ~0.3 USD (REJECT-only flow logs, BLOCK/COUNT-only WAF log) |

E-mail: 92 alarms sent OK mails too; after the diet 12 state alarms do. Event checks in the apps send one e-mail per
check per UTC day (or per break-glass session / ops release / refused event).

## 6. What is not covered any more (accepted)

- RDS memory, latency and disk queue on Dev (no alarm; C4.3 weekly review and the admin overview).
- API 5xx bursts while the service is healthy: Sentry (all apps), not e-mail from CloudWatch.
- Automatic scale-out of the CIS api / worker on Dev: a heavy wave sets the worker desired count by hand.
- Prod (ADR 0018, own account) re-decides this list; this diet is for Dev.
