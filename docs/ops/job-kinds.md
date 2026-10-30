---
id: APP-09
title: Job-kind register and kill switches
description: Every background job kind in CIS and Booking with its limits, the kinds that block a deploy, and how to stop one; hand-written from the code on main.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-worker, aa-booking-api, aa-crm-api]
last_reviewed: 2026-10-28
review_every_days: 90
related: [OPS-04-queue-stuck, OPS-04-llm-cost-spike, OPS-10-deploy-gate, OPS-06, docs/adr/0003-one-durable-job-model.md, docs/adr/0003a-per-owner-job-tables.md, AA-650, AA-892]
---

# Job-kind register and kill switches

Hand-written from the code on `main` (2026-10-28); a generated version is planned once the hand table goes wrong. The
live list of registered kinds is `GET /admin/job-runner/summary` (CIS); trust it over this page.

## How to stop work

There is **no general per-kind pause switch** today. Two kinds have their own environment switch on the worker:
`SUPPLY_CONTENT_LLM` = `off` makes `supply_content_draft` skip, and unattended `writing_memory_mine` runs only when
`WRITING_MEMORY_AUTO_MINE` is on (default off). See the [feature-flag register](feature-flags.md). The other controls:

| Control | Scope | How |
|---|---|---|
| Cancel a job | one row | admin Jobs page **Cancel**, or `POST /admin/job-runner/jobs/{id}/cancel` (queued or running; the handler stops at its next check) |
| Retry | one row | **Retry**, or `POST …/jobs/{id}/retry` (failed, stopped_budget, cancelled) |
| Cost guard | one provider and scope | `shared.spend_budget` (admin **Cost Operations → Budgets**); a hard stop ends the job `stopped_budget` |
| Stop all CIS jobs | every kind | scale `aa-cis-dev-worker` to 0 (command below); the worker drains on SIGTERM and releases running rows back to the queue (see the next section), queued rows wait; queue-age alarms fire, as expected |
| Retired kind | a kind with no handler | listed in `RETIRED_KINDS`; the api sampler cancels its rows |

```bash
aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-worker --desired-count 0 --profile aa365-admin --region us-west-1 --query "service.desiredCount" --output text # WRITE
```

Undo: the same command with `--desired-count 1`, then look for `job_worker_started` in `/ecs/aa-cis-dev`. Scaling the
worker to 0 stops all CIS job work; the tech lead decides it.

The worker's autoscaling target has minimum 1 (maximum 3), so the next scaling activity can start a task again. For a
stop that must last, also lower the minimum, and put it back afterwards (until then Terraform shows drift):

```bash
aws application-autoscaling register-scalable-target --service-namespace ecs --resource-id service/aa-cis-dev-cluster/aa-cis-dev-worker --scalable-dimension ecs:service:DesiredCount --min-capacity 0 --profile aa365-admin --region us-west-1 # WRITE
```

Undo: the same command with `--min-capacity 1`.

A per-kind pause (for example a column in a kind registry table) would be a new feature: open an issue if an incident
shows the need.

## Deploys and running jobs (AA-993 G5)

Deploys no longer wait for idle job tables. On SIGTERM the worker drains: it releases a running job back to the queue,
and the new task claims it again. A queued row is claimed by whichever image is live.

A deploy gate still blocks while a job of a **deploy-blocking** kind is running, or is queued and due within 15
minutes. These kinds keep no checkpoint, or use up a single-use approval, so a release would lose work. The CIS gate
also blocks while a rerun wave is open (`shared.rerun_wave.status = 'open'`). Override: the deploy workflow input
`override_running_jobs` (tech lead only, [deploy gate override](runbooks/deploy-gate-override.md)).

DB Migrate `apply` is different: it still waits until every owner job table is idle (DM-11.4), except the idle-exempt
kinds in AA-CIS-Infra `db/owners.yaml`.

## CIS (`shared.job`, worker service `aa-cis-dev-worker`)

`concurrency` = parallel rows of the kind per worker; `expected` = seconds after which a running row is "overdue" on the
Jobs page and in `aa-cis-dev-jobs-overdue-running` (twice this value); `background` kinds never take the worker's last
free slots; **blocks** = `deploy_blocking` in the registry.

| Kind | Code | Concurrency | Max attempts | Expected (s) | Background | Blocks deploys | Paid calls (from the code; check before relying on it) |
|---|---|---|---|---|---|---|---|
| `s1_batch_ingest` | `services/jobs/s1_batch_ingest_job.py` | 1 | 1 | 7200 | no | **yes** (no checkpoint) | Bedrock Batch (poll + ingest; blocked on acc3, AA-624) |
| `s1_rewrite` | `services/jobs/s1_rewrite_job.py` | 6 | 1 | 600 | no | no | LLM |
| `s1_seo_prefetch` | `services/jobs/s1_seo_prefetch_job.py` | 1 | 2 | 900 | no | no | DataForSEO |
| `segment_research` | `services/jobs/segment_research_job.py` | 1 | 2 | 3600 | no | no | DataForSEO + LLM |
| `recompute` | `services/jobs/recompute_job.py` | 1 | 2 | 1800 | no | no | Jev decide + embeddings (Cohere) |
| `revalidate` | `services/jobs/revalidate_job.py` | 2 | 2 | 600 | no | no | LLM (validate + judge) |
| `a3_atomize` | `services/jobs/a3_atomize_job.py` | 1 | 2 | 1800 | no | no | LLM |
| `t2_rewrite` | `services/jobs/t2_rewrite_job.py` | 4 | 2 | 300 | no | no | LLM (tenant) |
| `t7_slate` | `services/jobs/t7_slate_job.py` | 2 | 2 | 600 | no | no | LLM (tenant) |
| `t8_angles` | `services/jobs/t8_angles_job.py` | 4 | 2 | 120 | no | no | LLM + Jev (tenant) |
| `t9_write` | `services/jobs/t9_write_job.py` | 4 | 2 | 600 | no | no | LLM (tenant) |
| `photo_sync` | `services/jobs/photo_sync_job.py` | 1 | 2 | 1800 | no | no | Google Drive API (free quota) |
| `place_cards_build` | `services/jobs/place_cards_job.py` | 1 | 2 | 600 | no | no | - |
| `place_extract` | `services/jobs/place_extract_job.py` | 1 | 3 | 300 | yes | no | LLM + geocoder |
| `place_geocode` | `services/jobs/place_geocode_job.py` | 1 | 3 | 1800 | yes | no | geocoder (cost guard `geocoder`), LLM |
| `place_shape` | `services/jobs/place_shape_job.py` | 1 | 3 | 1800 | yes | no | geocoder (Geoapify details) + Overpass |
| `place_dedupe` | `services/jobs/place_dedupe_job.py` | 1 | 2 | 900 | yes | no | - |
| `place_relocate` | `services/jobs/place_relocate_job.py` | 1 | 3 | 1800 | yes | no | geocoder (budgeted); DRY RUN by default (AA-997) |
| `tour_graph_build` | `services/jobs/tour_graph_job.py` | 1 | 3 | 600 | yes | no | geocoder (lookups) |
| `tripplanner_purge` | `services/jobs/tripplanner_purge_job.py` | 1 | 4 | 60 | no | no | - (calls the TripPlanner cache revalidate URL, AA-987) |
| `supply_content_draft` | `services/jobs/supply_content_draft_job.py` | 1 | 2 | 300 | yes | no | LLM (at most 20 drafts a day; cost guard `job:supply_content_draft`; kill switch `SUPPLY_CONTENT_LLM`) |
| `supply_media_purge` | `services/jobs/supply_media_purge_job.py` | 1 | 3 | 60 | yes | no | - (S3 + CDN invalidation) |
| `writing_signal_backfill`, `writing_signal_fact_filter` | `services/jobs/writing_memory_job.py` | 1 | 2, 3 | 900, 600 | yes | no | - |
| `writing_memory_mine` | same | 1 | 1 | 1800 | yes | no | LLM judge route (at most 50 calls, 1 USD a run) |
| `writing_memory_r0`, `writing_memory_post_activation` | same | 1 | 2 | 1800, 300 | yes | no | - |
| `writing_memory_r2`, `writing_memory_shadow` | same | 1 | 1 | 5400 | yes | **yes** (a re-claimed run would start over and pay again) | LLM (R2 at most 10 USD, shadow at most 7 USD a run) |
| `retention_llm_call_log`, `retention_tenant_api_usage`, `retention_job`, `retention_decision_log`, `retention_cost_explorer_snapshot` | `services/jobs/retention_job.py` (policy `services/retention/policy.py`) | 1 | 2 | 1800 | yes | no | - (DRY RUN by default when run by hand) |
| `staff_directory_reconcile` | `services/jobs/staff_reconcile_job.py` | 1 | 2 | 120 | yes | no | - (daily, scheduled by the ops probe) |
| `data_erasure` | `services/jobs/erasure_job.py` (inventory `services/erasure/inventory.py`) | 1 | 1 | 900 | yes | **yes** (an apply uses up its single-use DRY RUN approval) | - (manual only, DRY RUN by default; apply off unless `ERASURE_APPLY_ENABLED=true`; an apply is never retried (409), AA-839, [runbook](../legal/dsar-erasure-runbook.md)) |
| `staff_invite_email` | `services/jobs/staff_invite_email_job.py` | 2 | 5 | 60 | no | no | SES |
| `ops_alert_email` | `services/jobs/ops_alert_email_job.py` | 1 | 5 | 60 | no | no | SES |
| `llm_cost_reconcile` | `services/jobs/llm_cost_reconcile_job.py` (logic `services/llm_cost/reconcile.py`) | 1 | 2 | 300 | yes | no | - (nightly from 02:00 UTC by the ops metrics sampler, last 3 days, switch `LLM_COST_RECONCILE`; reads the stored Cost Explorer snapshot, never a live CE call; the Anthropic / OpenAI usage APIs only for a connection that names a read-only usage key, not billed; AA-1002 S10) |
| `noop_sleep` | `services/jobs/noop_sleep_job.py` | - | - | - | - | no (gate-exempt) | - (test-only, registered only when `JOB_TEST_KINDS=1`, Dev; AA-993 G1) |

Kinds with `max_attempts = 1` are not retried after a failure. A deploy drain is not a failure: the released attempt is
not counted (`shared/jobs/queue.py` `release`).

## Booking (`booking.job`, worker inside `aa-booking-dev-api`)

| Kind | Expected (s) | Deploy gate | Notes |
|---|---|---|---|
| `bk_inquiry_pull` | 60 | exempt from the counts (always queued) | pulls inquiries |
| `bk_inquiry_process` | 60 | released on a deploy | |
| `bk_notify_email` | 60 | released on a deploy | SES staff notification (also the TripPlanner advisor e-mail) |
| `bk_b2b_hold_expire` | 120 | released on a deploy | expires due B2B holds (AA-973) |
| `bk_tour_lifecycle_pull` | 120 | released on a deploy | reads the CIS tour lifecycle outbox (AA-986) |
| `bk_case_lifecycle` | 300 | released on a deploy | daily case lifecycle (AA-682) |
| `bk_ops_reminders` | 120 | released on a deploy | ops reminders (AA-682) |
| `bk_retention_job` | 900 | **blocks** (no checkpoint) | retention |
| `bk_retention_inbox_redact` | 900 | **blocks** (no checkpoint) | retention |
| `bk_noop_sleep` | 3660 | exempt | test-only, `JOB_TEST_KINDS` on Dev (AA-993 G4) |

Source: `backend/app/jobs/kinds.py` (`EXPECTED_SECONDS`, `DEPLOY_BLOCKING_KINDS`, `DEPLOY_GATE_EXEMPT`).

## CRM (`crm.job`, worker inside `aa-crm-dev-api`)

The CRM kinds (`crm_*`) and their schedules are listed in AA-Partner `CONTEXT.md`, section "Job runner (`crm.job`, ADR 0003a)". None blocks a deploy
since AA-993 G4b (`DEPLOY_BLOCKING_KINDS` is empty in `api/app/jobs/kinds.py`). Stop all CRM jobs only by scaling
`aa-crm-dev-api`, which also stops the CRM API.

## TripPlanner

`tripplanner.job` is planned (AA-861); today TripPlanner work runs inside the Lambda requests.
