---
id: APP-09
title: Job-kind register and kill switches
description: Every background job kind in CIS and Booking with its limits, and how to stop one; hand-written from the code on main.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-worker, aa-booking-api]
last_reviewed: 2026-10-19
review_every_days: 90
related: [OPS-04-queue-stuck, OPS-04-llm-cost-spike, OPS-10-deploy-gate, OPS-06, docs/adr/0003-one-durable-job-model.md, docs/adr/0003a-per-owner-job-tables.md, AA-650, AA-892]
---

# Job-kind register and kill switches

Hand-written from the code on `main` (19/10/2026); a generated version is planned once the hand table goes wrong. The
live list of registered kinds is `GET /admin/job-runner/summary` (CIS); trust it over this page.

## How to stop work

There is **no per-kind pause switch** today. The controls are:

| Control | Scope | How |
|---|---|---|
| Cancel a job | one row | admin Jobs page **Cancel**, or `POST /admin/job-runner/jobs/{id}/cancel` (queued or running; the handler stops at its next check) |
| Retry | one row | **Retry**, or `POST …/jobs/{id}/retry` (failed, stopped_budget, cancelled) |
| Cost guard | one provider and scope | `shared.spend_budget` (admin Budgets page); a hard stop ends the job `stopped_budget` |
| Stop all CIS jobs | every kind | scale `aa-cis-dev-worker` to 0 (command below); running rows are interrupted, queued rows wait; queue-age alarms fire, as expected |
| Retired kind | a kind with no handler | listed in `RETIRED_KINDS`; the api sampler cancels its rows |

```bash
aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-worker --desired-count 0 --profile aa365-admin --region us-west-1 --query "service.desiredCount" --output text # WRITE
```

Undo: the same command with `--desired-count 1`, then look for `job_worker_started` in `/ecs/aa-cis-dev`. Scaling the
worker interrupts running jobs like a deploy does; Nghiệp decides it.

The worker's autoscaling target has minimum 1 (maximum 3), so the next scaling activity can start a task again. For a
stop that must last, also lower the minimum, and put it back afterwards (until then Terraform shows drift):

```bash
aws application-autoscaling register-scalable-target --service-namespace ecs --resource-id service/aa-cis-dev-cluster/aa-cis-dev-worker --scalable-dimension ecs:service:DesiredCount --min-capacity 0 --profile aa365-admin --region us-west-1 # WRITE
```

Undo: the same command with `--min-capacity 1`.

A per-kind pause (for example a column in a kind registry table) would be a new feature: open an issue if an incident
shows the need.

## CIS (`shared.job`, worker service `aa-cis-dev-worker`)

`concurrency` = parallel rows of the kind per worker; `expected` = seconds after which a running row is "overdue" on the
Jobs page and in `aa-cis-dev-jobs-overdue-running` (twice this value); `background` kinds never take the worker's last
free slots.

| Kind | Code | Concurrency | Max attempts | Expected (s) | Background | Paid calls (from the imports; check before relying on it) |
|---|---|---|---|---|---|---|
| `s1_batch_ingest` | `services/jobs/s1_batch_ingest_job.py` | 1 | 1 | 7200 | no | Bedrock Batch (poll + ingest; blocked on acc3, AA-624) |
| `s1_rewrite` | `services/jobs/s1_rewrite_job.py` | 6 | 1 | 600 | no | LLM |
| `s1_seo_prefetch` | `services/jobs/s1_seo_prefetch_job.py` | 1 | 2 | 900 | no | DataForSEO |
| `segment_research` | `services/jobs/segment_research_job.py` | 1 | 2 | 3600 | no | DataForSEO + LLM |
| `recompute` | `services/jobs/recompute_job.py` | 1 | 2 | 1800 | no | Jev decide + embeddings (Cohere) |
| `revalidate` | `services/jobs/revalidate_job.py` | 2 | 2 | 600 | no | LLM (validate + judge) |
| `a3_atomize` | `services/jobs/a3_atomize_job.py` | 1 | 2 | 1800 | no | LLM |
| `t2_rewrite` | `services/jobs/t2_rewrite_job.py` | 4 | 2 | 300 | no | LLM (tenant) |
| `t7_slate` | `services/jobs/t7_slate_job.py` | 2 | 2 | 600 | no | LLM (tenant) |
| `t8_angles` | `services/jobs/t8_angles_job.py` | 4 | 2 | 120 | no | LLM + Jev (tenant) |
| `t9_write` | `services/jobs/t9_write_job.py` | 4 | 2 | 600 | no | LLM (tenant) |
| `photo_sync` | `services/jobs/photo_sync_job.py` | 1 | 2 | 1800 | no | Google Drive API (free quota) |
| `place_cards_build` | `services/jobs/place_cards_job.py` | 1 | 2 | 600 | no | - |
| `place_extract` | `services/jobs/place_extract_job.py` | 1 | 3 | 300 | yes | LLM + geocoder |
| `place_geocode` | `services/jobs/place_geocode_job.py` | 1 | 3 | 1800 | yes | geocoder (cost guard `geocoder`), LLM |
| `tour_graph_build` | `services/jobs/tour_graph_job.py` | 1 | 3 | 600 | yes | geocoder (lookups) |
| `retention_llm_call_log`, `retention_tenant_api_usage`, `retention_job`, `retention_decision_log`, `retention_cost_explorer_snapshot` | `services/jobs/retention_job.py` (policy `services/retention/policy.py`) | 1 | 2 | 1800 | yes | - (DRY RUN by default when run by hand) |
| `staff_directory_reconcile` | `services/jobs/staff_reconcile_job.py` | 1 | 2 | 120 | yes | - (daily, scheduled by the ops probe) |
| `staff_invite_email` | `services/jobs/staff_invite_email_job.py` | 2 | per `api/services/staff_invite.py` | 60 | no | SES |
| `ops_alert_email` | `services/jobs/ops_alert_email_job.py` | 1 | per `shared/ops_alerts.py` | 60 | no | SES |

Kinds with `max_attempts = 1` are not retried after an interruption (a deploy or an override ends them `failed`).

## Booking (`booking.job`, worker inside `aa-booking-dev-api`)

| Kind | Expected (s) | Deploy gate | Notes |
|---|---|---|---|
| `bk_inquiry_pull` | 60 | exempt (always queued) | pulls inquiries |
| `bk_inquiry_process` | 60 | counted | |
| `bk_notify_email` | 60 | counted | SES staff notification (also the TripPlanner advisor e-mail) |
| `bk_retention_job` | 900 | counted | retention |
| `bk_retention_inbox_redact` | 900 | counted | retention |

Source: `backend/app/jobs/kinds.py` and the modules it names.

## TripPlanner

`tripplanner.job` is planned (AA-861); today TripPlanner work runs inside the Lambda requests.
