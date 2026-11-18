---
id: APP-09
title: Job-kind register and kill switches
description: Every background job kind in CIS, Booking, TripPlanner and the CRM with its limits, the kinds that block a deploy, and how to stop one; hand-written from the code on main.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-worker, aa-booking-api, aa-crm-api, tripplanner-lambda]
last_reviewed: 2026-11-13
review_every_days: 90
related: [OPS-04-queue-stuck, OPS-04-llm-cost-spike, OPS-10-deploy-gate, OPS-06, docs/adr/0003-one-durable-job-model.md, docs/adr/0003a-per-owner-job-tables.md, AA-650, AA-892, AA-1093]
---

# Job-kind register and kill switches

The kind lists under each owner are generated from the code on `main` (`<!-- gen:job-kinds-* -->` blocks,
`tools/docs/gen_sections.py`, read statically by `tools/docs/repo_facts.py`); the notes and the controls are
hand-written. The live list of registered kinds is `GET /admin/job-runner/summary` (CIS); trust it over this page.

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

The worker's scalable target has minimum 1 (maximum 3). Since S263 it has no target-tracking policy on Dev (a heavy
wave raises the desired count by hand, at most 3); lowering the minimum still keeps a registration from starting a task
again. For a stop that must last, lower the minimum and put it back afterwards (until then Terraform shows drift):

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
Jobs page and in the CIS ops check `jobs_overdue` (twice this value); `background` kinds never take the worker's last
free slots; **blocks** = `deploy_blocking` in the registry.

### Registered kinds (generated)

<!-- gen:job-kinds-cis -->

65 kinds registered with `@job_kind` (`shared/jobs/registry.py`); a kind registered only when `JOB_TEST_KINDS` is on is not listed.

| Kind | Code | Concurrency | Max attempts | Expected (s) | Background | Blocks deploys | Gate exempt |
|---|---|---|---|---|---|---|---|
| `a3_atomize` | `services/jobs/a3_atomize_job.py` | 1 | 2 | 1800 | no | no | no |
| `ai_usage_rollup` | `services/jobs/ai_usage_rollup_job.py` | 1 | 2 | 1200 | **yes** | no | **yes** |
| `data_erasure` | `services/jobs/erasure_job.py` | 1 | 1 | 900 | **yes** | **yes** | no |
| `embedding_reembed` | `services/jobs/embedding_reembed_job.py` | 1 | 3 | 1800 | **yes** | no | no |
| `inquiry_handoff_check` | `services/jobs/report_ops_jobs.py` | 1 | 1 | 5 | **yes** | no | no |
| `kpi_snapshot_daily` | `services/jobs/report_jobs.py` | 1 | 3 | 300 | **yes** | no | no |
| `llm_batch` | `services/jobs/llm_batch_job.py` | 2 | 3 | 900 | no | no | no |
| `llm_connection_probe` | `services/jobs/llm_probe_job.py` | 1 | 1 | 600 | **yes** | no | **yes** |
| `llm_contract_smoke` | `services/jobs/llm_contract_smoke_job.py` | 1 | 1 | 300 | **yes** | no | no |
| `llm_cost_reconcile` | `services/jobs/llm_cost_reconcile_job.py` | 1 | 2 | 300 | **yes** | no | no |
| `llm_model_lifecycle_sync` | `services/jobs/llm_model_lifecycle_job.py` | 1 | 2 | 120 | **yes** | no | **yes** |
| `llm_route_watch` | `services/jobs/llm_route_watch_job.py` | 1 | 2 | 60 | **yes** | no | **yes** |
| `ops_alert_email` | `services/jobs/ops_alert_email_job.py` | 1 | 5 | 60 | no | no | no |
| `photo_destination_match` | `services/jobs/photo_destination_match_job.py` | 1 | 2 | 300 | **yes** | no | no |
| `photo_medium_backfill` | `services/jobs/photo_medium_backfill_job.py` | 1 | 2 | 1800 | **yes** | no | no |
| `photo_sync` | `services/jobs/photo_sync_job.py` | 1 | 2 | 1800 | no | no | no |
| `place_cards_build` | `services/jobs/place_cards_job.py` | 1 | 2 | 600 | no | no | no |
| `place_dedupe` | `services/jobs/place_dedupe_job.py` | 1 | 2 | 900 | **yes** | no | no |
| `place_extract` | `services/jobs/place_extract_job.py` | 1 | 3 | 300 | **yes** | no | no |
| `place_geocode` | `services/jobs/place_geocode_job.py` | 1 | 3 | 1800 | **yes** | no | no |
| `place_relocate` | `services/jobs/place_relocate_job.py` | 1 | 3 | 1800 | **yes** | no | no |
| `place_shape` | `services/jobs/place_shape_job.py` | 1 | 3 | 1800 | **yes** | no | no |
| `quality_funnel_watch` | `services/jobs/quality_funnel_watch_job.py` | 1 | 3 | 60 | **yes** | no | **yes** |
| `recompute` | `services/jobs/recompute_job.py` | 1 | 2 | 1800 | no | no | no |
| `report_email` | `services/jobs/report_ops_jobs.py` | 1 | 5 | 60 | **yes** | no | no |
| `report_generate` | `services/jobs/report_jobs.py` | 2 | 2 | 120 | **yes** | no | no |
| `retention_cost_explorer_snapshot` | `services/jobs/retention_job.py` | 1 | 2 | 1800 | **yes** | no | no |
| `retention_decision_log` | `services/jobs/retention_job.py` | 1 | 2 | 1800 | **yes** | no | no |
| `retention_job` | `services/jobs/retention_job.py` | 1 | 2 | 1800 | **yes** | no | no |
| `retention_llm_call_log` | `services/jobs/retention_job.py` | 1 | 2 | 1800 | **yes** | no | no |
| `retention_tenant_api_usage` | `services/jobs/retention_job.py` | 1 | 2 | 1800 | **yes** | no | no |
| `retired_page_draft` | `services/jobs/tour_retirement_jobs.py` | 2 | 4 | 120 | no | no | no |
| `revalidate` | `services/jobs/revalidate_job.py` | 2 | 2 | 600 | no | no | no |
| `s1_batch_ingest` | `services/jobs/s1_batch_ingest_job.py` | 1 | 1 | 7200 | no | **yes** | no |
| `s1_rewrite` | `services/jobs/s1_rewrite_job.py` | 6 | 1 | 600 | no | no | no |
| `s1_seo_prefetch` | `services/jobs/s1_seo_prefetch_job.py` | 1 | 2 | 900 | no | no | no |
| `segment_research` | `services/jobs/segment_research_job.py` | 1 | 2 | 3600 | no | no | no |
| `source_fanout` | `services/jobs/source_fanout_job.py` | 1 | 3 | 60 | no | no | no |
| `staff_directory_reconcile` | `services/jobs/staff_reconcile_job.py` | 1 | 2 | 120 | **yes** | no | no |
| `staff_invite_email` | `services/jobs/staff_invite_email_job.py` | 2 | 5 | 60 | no | no | no |
| `supply_content_draft` | `services/jobs/supply_content_draft_job.py` | 1 | 2 | 300 | **yes** | no | no |
| `supply_media_purge` | `services/jobs/supply_media_purge_job.py` | 1 | 3 | 60 | **yes** | no | no |
| `t2_rewrite` | `services/jobs/t2_rewrite_job.py` | 4 | 2 | 300 | no | no | no |
| `t7_slate` | `services/jobs/t7_slate_job.py` | 2 | 2 | 600 | no | no | no |
| `t8_angles` | `services/jobs/t8_angles_job.py` | 4 | 2 | 120 | no | no | no |
| `t9_write` | `services/jobs/t9_write_job.py` | 4 | 2 | 600 | no | no | no |
| `tenant_account_tick` | `services/jobs/tenant_account_tick_job.py` | 1 | 2 | 60 | no | no | no |
| `tenant_backup` | `services/jobs/tenant_backup_job.py` | 1 | 2 | 900 | **yes** | no | no |
| `tenant_billing_tick` | `services/jobs/tenant_billing_tick_job.py` | 1 | 2 | 60 | no | no | no |
| `tenant_erasure_saga` | `services/jobs/tenant_erasure_saga_job.py` | 1 | 3 | 120 | **yes** | no | no |
| `tenant_provision` | `services/jobs/tenant_provision_job.py` | 1 | 3 | 60 | no | no | no |
| `tour_graph_build` | `services/jobs/tour_graph_job.py` | 1 | 3 | 600 | **yes** | no | no |
| `tour_notice_email` | `services/jobs/tour_retirement_jobs.py` | 1 | 4 | 120 | no | no | no |
| `tour_paa_backfill` | `services/jobs/tour_paa_job.py` | 1 | 2 | 1800 | no | no | no |
| `tour_retirement_fanout` | `services/jobs/tour_retirement_jobs.py` | 2 | 5 | 120 | no | no | no |
| `tripplanner_custom_domain` | `services/jobs/tripplanner_custom_domain_job.py` | 1 | 3 | 120 | **yes** | no | no |
| `tripplanner_purge` | `services/jobs/tripplanner_purge_job.py` | 1 | 4 | 60 | no | no | no |
| `writing_memory_kpi_weekly` | `services/jobs/writing_memory_job.py` | 1 | 2 | 900 | **yes** | no | no |
| `writing_memory_mine` | `services/jobs/writing_memory_job.py` | 1 | 1 | 1800 | **yes** | no | no |
| `writing_memory_post_activation` | `services/jobs/writing_memory_job.py` | 1 | 2 | 300 | **yes** | no | no |
| `writing_memory_r0` | `services/jobs/writing_memory_job.py` | 1 | 2 | 1800 | **yes** | no | no |
| `writing_memory_r2` | `services/jobs/writing_memory_job.py` | 1 | 1 | 5400 | **yes** | **yes** | no |
| `writing_memory_shadow` | `services/jobs/writing_memory_job.py` | 1 | 1 | 5400 | **yes** | **yes** | no |
| `writing_signal_backfill` | `services/jobs/writing_memory_job.py` | 1 | 2 | 900 | **yes** | no | no |
| `writing_signal_fact_filter` | `services/jobs/writing_memory_job.py` | 1 | 3 | 600 | **yes** | no | no |

Read statically from AA-CIS-App main at `2ff8c53d` (tools/docs/repo_facts.py).

<!-- /gen -->

### Notes per kind (hand-written)

Paid calls and switches, from the code; check before relying on them. A kind missing here has no note.

| Kind | Paid calls and notes |
|---|---|
| `s1_batch_ingest` | Bedrock Batch (poll + ingest; blocked on acc3, AA-624) |
| `s1_rewrite` | LLM |
| `s1_seo_prefetch` | DataForSEO |
| `segment_research` | DataForSEO + LLM |
| `recompute` | Jev decide + embeddings (Cohere) |
| `revalidate` | LLM (validate + judge) |
| `a3_atomize` | LLM |
| `t2_rewrite` | LLM (tenant) |
| `t7_slate` | LLM (tenant) |
| `t8_angles` | LLM + Jev (tenant) |
| `t9_write` | LLM (tenant) |
| `photo_sync` | Google Drive API (free quota) |
| `place_cards_build` | - |
| `place_extract` | LLM + geocoder |
| `place_geocode` | geocoder (cost guard `geocoder`), LLM |
| `place_shape` | geocoder (Geoapify details) + Overpass |
| `place_dedupe` | - |
| `place_relocate` | geocoder (budgeted); DRY RUN by default (AA-997) |
| `tour_graph_build` | geocoder (lookups) |
| `tripplanner_purge` | - (calls the TripPlanner cache revalidate URL, AA-987) |
| `supply_content_draft` | LLM (at most 20 drafts a day; cost guard `job:supply_content_draft`; kill switch `SUPPLY_CONTENT_LLM`) |
| `supply_media_purge` | - (S3 + CDN invalidation) |
| `writing_signal_backfill`, `writing_signal_fact_filter` | - |
| `writing_memory_mine` | LLM judge route (at most 50 calls, 1 USD a run) |
| `writing_memory_r0`, `writing_memory_post_activation` | - |
| `writing_memory_r2`, `writing_memory_shadow` | LLM (R2 at most 10 USD, shadow at most 7 USD a run) |
| `retention_llm_call_log`, `retention_tenant_api_usage`, `retention_job`, `retention_decision_log`, `retention_cost_explorer_snapshot` | - (DRY RUN by default when run by hand) |
| `staff_directory_reconcile` | - (daily, scheduled by the ops probe) |
| `data_erasure` | - (manual only, DRY RUN by default; apply off unless `ERASURE_APPLY_ENABLED=true`; an apply is never retried (409), AA-839, [runbook](../legal/dsar-erasure-runbook.md)) |
| `tenant_erasure_saga` | - (drives the offboarding erasure across the apps, contract `tenant.erasure.v1`; DRY RUN first, apply only with the approved combined fingerprint, refuses the pilot tenant and, on Dev, a non-synthetic one; [runbook](../legal/dsar-erasure-runbook.md) section 4) |
| `tenant_backup` | - (database and S3 only: one tenant's rows to the gold bucket `exports/tenants/<t>/cis/`, kept 7 days; on demand, and nightly for the pilot tenant only when `TENANT_BACKUP_PILOT=on`, default off; AA-1093, [restore drill](runbooks/tenant-restore-drill.md)) |
| `staff_invite_email` | SES |
| `ops_alert_email` | SES |
| `llm_cost_reconcile` | - (nightly from 02:00 UTC by the ops metrics sampler, last 3 days, switch `LLM_COST_RECONCILE`; reads the stored Cost Explorer snapshot, never a live CE call; the Anthropic / OpenAI usage APIs only for a connection that names a read-only usage key, not billed; AA-1002 S10) |
| `embedding_reembed` | Embedding model of the target space: `dry_run` none, `probe` one call of a few words, `fill` one call per page (stopped before a page that would cross `cost_cap_usd`, at most 25 USD, for the whole job: retries and releases share it; resumable). Manual only, DRY RUN by default (`POST /admin/job-runner/embedding-reembed/run`, AA-1026; runbook [embedding re-embed](runbooks/embedding-re-embed.md)) |
| `noop_sleep` | - (test-only, registered only when `JOB_TEST_KINDS=1`, Dev; AA-993 G1; gate-exempt) |

Kinds with `max_attempts = 1` are not retried after a failure. A deploy drain is not a failure: the released attempt is
not counted (`shared/jobs/queue.py` `release`).

## Booking (`booking.job`, worker inside `aa-booking-dev-api`)

<!-- gen:job-kinds-booking -->

18 kinds in `backend/app/jobs/kinds.py` (`EXPECTED_SECONDS`, `DEPLOY_BLOCKING_KINDS`, `DEPLOY_GATE_EXEMPT`, `TEST_KINDS`).

| Kind | Expected (s) | Blocks deploys | Gate exempt | Test only |
|---|---|---|---|---|
| `bk_agency_invoice_reminders` | 300 | no | no | no |
| `bk_allotment_release` | 120 | no | no | no |
| `bk_b2b_hold_expire` | 120 | no | no | no |
| `bk_case_lifecycle` | 300 | no | no | no |
| `bk_departure_cost_recompute` | 300 | no | no | no |
| `bk_departure_watch` | 300 | no | no | no |
| `bk_noop_sleep` | 3660 | no | **yes** | **yes** |
| `bk_ops_reminders` | 120 | no | no | no |
| `bk_price_recompute` | 600 | no | no | no |
| `bk_retention_inbox_redact` | 900 | **yes** | no | no |
| `bk_retention_job` | 900 | **yes** | no | no |
| `bk_saas_invoice_draft` | 300 | no | no | no |
| `bk_settlement_draft` | 300 | no | no | no |
| `bk_supplier_order_send` | 120 | no | no | no |
| `bk_tenant_erase` | 300 | no | no | no |
| `bk_tenant_pull` | 120 | no | no | no |
| `bk_tour_lifecycle_pull` | 120 | no | no | no |
| `bk_trip_plan_sync` | 120 | no | no | no |

Read statically from AA-Booking main at `4b777358` (tools/docs/repo_facts.py).

<!-- /gen -->

Notes (hand-written; a kind missing here has no note):

| Kind | Notes |
|---|---|
| `bk_b2b_hold_expire` | expires due B2B holds (AA-973) |
| `bk_tour_lifecycle_pull` | reads the CIS tour lifecycle outbox (AA-986) |
| `bk_case_lifecycle` | daily case lifecycle (AA-682) |
| `bk_ops_reminders` | ops reminders (AA-682) |
| `bk_retention_job` | retention |
| `bk_retention_inbox_redact` | retention |
| `bk_tenant_erase` | AA-1093, bk-057: the Booking step of the offboarding erasure saga; reads `catalog.v_tenant_erasure_v1`, DRY RUN plan hash, apply anonymises the agency (money rows and the bill-to snapshot kept) only with the approved hash, writes `booking.tenant_erasure_log` (report view `booking.v_tenant_erasure_report_v1`); blocks a deploy while an apply runs |

The retired B2C kinds (`bk_inquiry_pull`, `bk_inquiry_process`, `bk_notify_email`) have no handler any more; `bk_inquiry_pull` stays in `DEPLOY_GATE_EXEMPT` so the deploy-gate answer keeps its shape, and a leftover row is cancelled by the worker.

Source: `backend/app/jobs/kinds.py` (`EXPECTED_SECONDS`, `DEPLOY_BLOCKING_KINDS`, `DEPLOY_GATE_EXEMPT`).

## CRM (`crm.job`, worker inside `aa-crm-dev-api`)

<!-- gen:job-kinds-crm -->

34 kinds in `api/app/jobs/kinds.py` (`EXPECTED_SECONDS`, `DEPLOY_BLOCKING_KINDS`, `DEPLOY_GATE_EXEMPT`, `TEST_KINDS`).

| Kind | Expected (s) | Blocks deploys | Gate exempt | Test only |
|---|---|---|---|---|
| `crm_audit_export` | 300 | no | no | no |
| `crm_audit_retention` | 900 | no | no | no |
| `crm_booking_sync` | 60 | no | **yes** | no |
| `crm_campaign_tick` | 300 | no | no | no |
| `crm_catalog_sync` | 300 | no | no | no |
| `crm_client_import` | 120 | no | no | no |
| `crm_data_export` | 600 | no | no | no |
| `crm_dispatch` | 30 | no | no | no |
| `crm_entitlement_pull` | 60 | no | no | no |
| `crm_fx_fetch` | 120 | no | no | no |
| `crm_heartbeat` | 30 | no | **yes** | no |
| `crm_intake_process` | 30 | no | no | no |
| `crm_job_retention` | 900 | no | no | no |
| `crm_lifecycle` | 900 | no | no | no |
| `crm_mail_health` | 300 | no | no | no |
| `crm_mail_history_import` | 120 | no | no | no |
| `crm_mail_ingest` | 120 | no | no | no |
| `crm_membership_pull` | 30 | no | **yes** | no |
| `crm_messaging_health` | 300 | no | no | no |
| `crm_messaging_templates` | 60 | no | no | no |
| `crm_offboard` | 600 | no | no | no |
| `crm_ops_release_sync` | 300 | no | no | no |
| `crm_partner_accounts` | 300 | no | no | no |
| `crm_pdf_render` | 60 | no | no | no |
| `crm_pilot_backup` | 60 | no | no | no |
| `crm_placeholder_purge` | 60 | no | no | no |
| `crm_stage_date_rule` | 120 | no | no | no |
| `crm_studio_activation` | 30 | no | no | no |
| `crm_task_digest` | 120 | no | no | no |
| `crm_tenant_erase` | 600 | no | no | no |
| `crm_tour_retired_fanout` | 120 | no | no | no |
| `crm_tp_lead_pull` | 120 | no | no | no |
| `crm_workflow_run` | 60 | no | no | no |
| `crm_workflow_tick` | 300 | no | no | no |

Read statically from AA-Partner main at `6592cf50` (tools/docs/repo_facts.py).

<!-- /gen -->

The schedules are in AA-Partner `CONTEXT.md`, section "Job runner (`crm.job`, ADR 0003a)". None blocks a deploy
since AA-993 G4b (`DEPLOY_BLOCKING_KINDS` is empty in `api/app/jobs/kinds.py`). Stop all CRM jobs only by scaling
`aa-crm-dev-api`, which also stops the CRM API. Notes on the kinds added by AA-1093 (hand-written):

| Kind | Notes |
|---|---|
| `crm_tour_retired_fanout` | crm-063: one job per served → retired or retired → served transition the hourly `crm_catalog_sync` sees (idempotency key per AA tour, transition and change time). Per agency, in its own transaction: raises or clears `crm.tour_retired_flag` rows (open option, held, quoted or confirmed AA booking line) and one task per affected trip to the trip owner; never writes a booking line or an option. `paused` is ignored (ADR 0015 decision 5) |
| `crm_tenant_erase` | reads `GET /tenant/v1/erasure-requests` (scope `cis.tenant/erasure`) and, at the CRM's `not_before` (T0 + 90 days), runs the agency erasure with crypto-shredding without the owner's click, reporting through `POST /tenant/v1/erasure-requests/{id}/reports` (`tenant.erasure.v1`) |

## TripPlanner (`tripplanner.job`, jobs Lambda `aa-tripplanner-<env>-jobs`)

Worker: the jobs Lambda (AA-TripPlanner-Web `backend/jobs/handler.py`), woken daily by the EventBridge Scheduler
(AA-CIS-Infra `accounts/aa365/tripplanner_jobs.tf`) or invoked by an operator through IAM (`op` `tick`, `enqueue`,
`run`, `status`). Every kind matches `^tp_[a-z0-9_]+$` (tp-021). Source: `HANDLERS`, `DAILY` and `MAX_ATTEMPTS` in
`backend/jobs/handler.py`.

<!-- gen:job-kinds-tripplanner -->

6 kinds in `HANDLERS` of `backend/jobs/handler.py`; `DAILY` = queued by the daily tick.

| Kind | Daily | Max attempts |
|---|---|---|
| `tp_lead_deliver` | **yes** | 3 |
| `tp_retention_ai_rate_counter` | **yes** | 1 |
| `tp_retention_outbox_redact` | **yes** | 1 |
| `tp_tenant_backup` | **yes** | 2 |
| `tp_tenant_erase` | **yes** | 1 |
| `tp_tenant_restore_drill` | no | 1 |

Read statically from AA-TripPlanner-Web main at `44aa203b` (tools/docs/repo_facts.py).

<!-- /gen -->

Notes (hand-written):

| Kind | Notes |
|---|---|
| `tp_retention_outbox_redact` | redacts `tripplanner.outbox` payloads past their window (AA-861; DRY RUN when run by hand) |
| `tp_retention_ai_rate_counter` | deletes AI limiter windows older than 2 days (AA-1015) |
| `tp_lead_deliver` | daily + on demand: delivers and redacts `lead.submitted` rows, retries (AA-1038) |
| `tp_tenant_erase` | AA-1093, tp-030: the TripPlanner step of the offboarding erasure saga; reads `catalog.v_tenant_erasure_v1`, DRY RUN plan hash, apply deletes the tenant's rows and merges its spend rows only with the approved hash, writes `tripplanner.tenant_erasure_log` (report view `tripplanner.v_tenant_erasure_report_v1`) |
| `tp_tenant_backup` | AA-1093 L4: one tenant's TripPlanner rows to its own backup prefix; drilled by the jobs Lambda `restore_drill` op ([restore drill](runbooks/tenant-restore-drill.md), TripPlanner section) |
