---
id: OPS-04-5xx-spike
title: 5xx spike on an API
description: Diagnose and stop a burst of 5xx answers from the CIS or Booking API, or errors from the TripPlanner Lambdas.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-booking-api, tripplanner-lambda]
last_reviewed: 2026-10-19
review_every_days: 90
related: [OPS-04, OPS-02-cis, OPS-02-booking, OPS-02-tp-lambda, OPS-04-queue-stuck, AA-870, AA-892]
---

# 5xx spike on an API

> [!WARNING]
> UNTESTED - written from the alarm definitions and logs as they are on 19/10/2026; not yet used in a real incident.

## Triggers

| Alarm | Fires when |
|---|---|
| `aa-cis-dev-api-5xx` | 5 or more 5XX from the CIS REST API in 5 minutes |
| `aa-cis-dev-api-latency-p95` | integration latency p95 above 5 s for 15 minutes |
| `aa-booking-dev-api-5xx` | 5 or more 5XX from the Booking REST API in 5 minutes |
| `aa-booking-dev-no-healthy-task`, `aa-booking-dev-unhealthy-hosts`, `aa-cis-dev-ecs-running-tasks-low` | no healthy task behind the API |
| `aa-tripplanner-dev-browse-errors`, `aa-tripplanner-dev-assembly-errors` | 3 or more Lambda errors in 5 minutes |
| `aa-cis-dev-rds-*` (connections, CPU, memory, storage, latency) | the shared database is the cause |

Also: a Sentry issue for the CIS api or worker (free plan), or a person reporting a broken page.

## First 5 minutes

1. Confirm and scope it (read-only).

   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" https://api-cis.lumiguides.it.com/health/ready
   curl -s https://api-booking.lumiguides.it.com/booking/health/ready
   curl -s -o /dev/null -w "%{http_code}\n" "https://tripplanner.lumiguides.it.com/api/browse?resource=countries"
   aws cloudwatch describe-alarms --state-value ALARM --profile aa365-admin --region us-west-1 --query "MetricAlarms[?!starts_with(AlarmName, 'TargetTracking')].[AlarmName,StateUpdatedTimestamp]" --output table
   ```

   `TargetTracking-…-AlarmLow-…` alarms in ALARM are autoscaling scale-in signals, not incidents.
   One app failing points at that app; all three failing points at RDS, the network (NAT alarm
   `aa-ecosys-dev-nat-status-check-failed`) or DNS.

2. Was there a deploy in the last hour? If yes, that is the first suspect.

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker aa-booking-dev-api --profile aa365-admin --region us-west-1 --query "services[].{n:serviceName,td:taskDefinition,r:deployments[0].rolloutState,since:deployments[0].createdAt}" --output table
   ```

   Also: `gh run list -R AdventureAsia365-Ecosys/<repo> -L 5` for app repos and for AA-CIS-Infra (a Terraform apply can
   break access as well).

3. Read the errors.

   ```bash
   aws logs tail /ecs/aa-cis-dev --since 15m --filter-pattern '?ERROR ?Traceback ?"status=5"' --profile aa365-admin --region us-west-1
   aws logs tail /ecs/aa-booking-dev --since 15m --filter-pattern '?ERROR ?Traceback' --profile aa365-admin --region us-west-1
   aws logs tail /aws/lambda/aa-tripplanner-dev-browse --since 15m --filter-pattern '?ERROR ?Task' --profile aa365-admin --region us-west-1
   ```

## Decide

| Pattern | Action |
|---|---|
| Started with a deploy | Roll back: [CIS](../runbooks/rollback-cis.md), [Booking](../runbooks/rollback-booking.md), [TP Lambdas](../runbooks/rollback-tp-lambda.md), [Terraform](../runbooks/rollback-terraform.md) |
| `AccessDenied` / `42501 permission denied` after an Infra apply or a migration | A grant or IAM change: roll back that change; for DB grants run the [isolation probe](../runbooks/isolation-probe.md) |
| `too many connections`, pool acquire timeouts, `aa-cis-dev-rds-connections-high` | Connection budget (C2.2): find the caller in the `aa-cis-dev-rds-role-connections-*` alarms; scale the noisy service down to its minimum, stop a runaway job ([queue stuck](queue-stuck.md)) |
| Tenant routes only (`/v1/...`), `aa817_tenant_pool_unavailable` in the log | Tenant pool or RLS: switch the route back to the admin pool ([feature flags](../feature-flags.md), break-glass C) |
| Slow, not failing (p95) | RDS CPU or a long query; a heavy job running - check the Jobs page |
| Only Bedrock/OpenAI-backed routes | Provider outage or quota: see [LLM cost spike](llm-cost-spike.md) for the routes, wait or switch the route |

## Close

- The alarm returns to `OK` (e-mail on OK, D-20); write the timeline in the incident issue
  ([incident response](../incident-response.md)). A missing alarm or log becomes an issue.
