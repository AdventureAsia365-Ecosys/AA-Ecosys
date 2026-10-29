---
id: OPS-06
title: Feature-flag register
description: Every runtime flag and kill switch in the ecosystem, by name only - where it lives, its default, who owns it and when it is removed.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, aa-cis-frontend, aa-booking-api, tripplanner-lambda]
last_reviewed: 2026-10-28
review_every_days: 90
related: [OPS-06-legacy-login, OPS-10, APP-09, APP-03, docs/architecture/data-standards/02-data-management.md, AA-544, AA-816, AA-892]
---

# Feature-flag register

This register is a document, not a database table: data standard DM-1.5 rules out a `shared.feature_flag` table for
now. Add a row in the same PR that adds a flag, and move it to "Removed" in the PR that deletes it.

Names only. Values that are secrets never appear here. Environment variable names contain underscores: the tech lead edits
their values by hand (Terraform in VSCode, the Vercel dashboard); agents describe the change and do not generate it.

**Checked against code on `main` on 2026-10-28** (CIS `api/core/aa544_tenant_pool.py`, `api/core/staff_identity.py`,
`frontend/lib/staffSession.ts`, `services/acp_angle_gate/prompts.py`, `services/jobs/erasure_job.py`; Booking
`backend/app/settings.py`, `backend/app/jobs/kinds.py`; TripPlanner `backend/config.py`; Infra `modules/ecs/main.tf`,
`accounts/aa365/booking.tf`, `accounts/aa365/tripplanner.tf`). **Live values:** the CIS and Booking ECS task
definitions were read on 2026-10-28; Redis keys, Vercel and Lambda values are from the date in their cell.

## Columns

- **Kind:** `release` (temporary, removed after rollout), `ops` (kill switch or operational setting, permanent),
  `security` (a security control; never removed by date).
- **remove_by:** the event or date after which the flag is deleted. Security controls have none.

## CIS

| Flag | Kind | Where it is set | Default (code) | Live value | Owner | remove_by | Notes |
|---|---|---|---|---|---|---|---|
| `LEGACY_ADMIN_LOGIN_ENABLED` | release | API: ECS task env (not set); BFF: Vercel `aa-cis-frontend` env per target (Production `false`) | **off** since AA-816 S2, 2026-10-22 (only `1`/`true`/`yes`/`on` turn it on; ADR 0006a A12) | off (API unset, 2026-10-28; BFF checked 2026-10-23) | tech lead | with the bridge retirement (AA-911 P6b, end of project): delete the flag and the HS256 staff path | [Runbook](runbooks/legacy-login-flag.md) (rollback). Gates the password form, BFF `/api/auth/login` and the HS256 path of `/auth/verify-admin`, not `/auth/admin-login` or `/auth/booking-token` |
| Tenant-pool route flags (21 Redis keys, below) | security | Redis (ElastiCache, single node, no persistence) | on = tenant pool with RLS; a missing key or a read error is on (fail closed, D-12) | the first 11 keys all on since 2026-10-16 (AA-859 flip report); the 10 later keys not read here | tech lead | none (C2.3g, DM-8.4, D-12) | Only an explicit `false` (also `0`/`off`/`no`) sends one route back to the admin pool. A Redis restart drops every key, so every route is back on |
| `TENANT_POOL_FORCE_ADMIN_FLAGS` | security (emergency) | API ECS task env (comma-separated flag keys) | empty | not set (2026-10-28) | tech lead | none; must stay empty except during an incident | Durable per-route switch back to the admin pool, read at process start, survives Redis restarts. An unknown key is logged as an error. [Break-glass C](runbooks/break-glass.md#c-tenant-pool-emergency-switch) |
| `JOB_WORKER_IN_API` | ops | API ECS task env (Terraform `modules/ecs`) | off | `false` (2026-10-28) | tech lead | none | Jobs run on `aa-cis-dev-worker` (AA-735, ADR 0003). On only for local development |
| `ERASURE_APPLY_ENABLED` | security | API and worker ECS task env (Terraform `modules/ecs`, `var.erasure_apply_enabled`) | off (DRY RUN only) | `false` (2026-10-28) | tech lead | none | Lets an approved `data_erasure` apply run (AA-839, [DSAR and erasure runbook](../legal/dsar-erasure-runbook.md)) |
| `JOB_TEST_KINDS` | ops | API and worker ECS task env (Terraform `modules/ecs`) | off | `1` on Dev (2026-10-28) | tech lead | none | Registers the test-only kind `noop_sleep` for the worker-drain proof (AA-993 G1); `0` on any other environment |
| `T8_ANGLE_BRIEF_MODE` | release | API and worker ECS task env | unset = `off` (the old T8 prompt, byte for byte); `r8` turns on the round-8 angle brief | not set (2026-10-28) | tech lead | after the AA-790 round-8 A/B: keep one brief and delete the switch | Lets the paid A/B run both briefs on one image |
| `SUPPLY_CONTENT_LLM` | ops (kill switch) | worker ECS task env | on (only `off`/`0`/`false`/`no` turn it off) | not set, so on (2026-10-28) | tech lead | none | `off` makes `supply_content_draft` skip its paid draft (AA-835); `SUPPLY_CONTENT_MAX_DRAFTS_PER_DAY` caps drafts (default 20) |
| `INQUIRY_HANDOFF_ALERTS` | ops (kill switch) | worker ECS task env | on (only `off`/`0`/`false`/`no` turn it off) | not set, so on (from the AA-1003 R2 deploy) | tech lead | none | `off` stops the TP-03 handoff gap bell and its ops alert e-mail (one a UTC day); the hourly `inquiry_handoff_check` still runs and records the gap (AA-1003 R2) |
| `WRITING_MEMORY_AUTO_MINE` | ops | worker ECS task env | off | not set, so off (2026-10-28) | tech lead | none | On lets the fact filter queue a paid `writing_memory_mine` run by itself (AA-917) |
| Workforce sign-in domain override | ops | BFF env (Vercel) | the custom domain `staff-auth.lumiguides.it.com` (code constant) | not set (2026-10-19) | tech lead | none | Points sign-in back at the pool's prefix domain (ADR 0006a A5) |
| Cost guard limits | ops | `shared.spend_budget` rows, admin **Cost Operations → Budgets** (`/admin/cost-ops?tab=budgets`) | migration seed values | see the Budgets page | tech lead | none | Per provider and scope; `hard_stop` stops paid calls. [LLM cost spike](playbooks/llm-cost-spike.md) |
| Per-stage LLM route | ops | `shared.llm_role_config` via admin LLM config | per stage | see the LLM config page | tech lead | none | Model switch per stage (APP-06, AA-900) |

### Tenant-pool route keys (CIS `ALL_TENANT_POOL_FLAGS`)

| Redis key | Route(s) | Needs migration |
|---|---|---|
| `aa544:stage1:publish_pending_pool` | GET `/v1/publish-log/pending` | - |
| `aa544:stage5:get_piece_pool` | GET `/v1/content-writing/pieces/{id}` and `/export` | - |
| `aa544:publish_log_list_pool` | GET `/v1/publish-log` | - |
| `aa544:integration_disconnect_pool` | DELETE `/v1/integrations/{wordpress,facebook}` | 237 |
| `aa817:content_piece_reads_pool` | GET `/v1/content-writing/requests/{id}/latest-piece` | - |
| `aa859:piece_edit_pool` | PATCH `/v1/content-writing/pieces/{id}` | - |
| `aa859:t2_version_write_pool` | PATCH `/v1/tours/versions/{id}` | - |
| `aa859:angle_gate_decide_pool` | POST `/v1/angle-gate/requests/{id}/choose` and `/reopen` | 241 |
| `aa859:unpublish_pool` | DELETE `/v1/publish-log/{id}` | - |
| `aa859:t2_version_reads_pool` | GET `/v1/tours/pool`, `/my-versions`, `/versions/{id}` | - |
| `aa859:integration_connect_pool` | GET/POST `/v1/integrations/{wordpress,facebook}` and `/test` | 241 |
| `aa859:t2_version_detail_reads_pool` | T2 version detail reads: `/{id}/full`, `/{id}`, DOCX export | - |
| `aa859:brand_identity_pool` | GET/POST `/admin/brand-identity` (tenant) | 262 |
| `aa859:publish_pool` | POST `/v1/publish-log/{piece_id}/publish` | - |
| `aa859:angle_gate_read_pool` | GET the angle-gate request, and the re-read after choose / reopen | 265 |
| `aa859:slate_reads_pool` | GET `/v1/slate` (subject list) | 265 |
| `aa859:subject_decide_pool` | POST `/v1/subjects/{id}/pick` and `/cut` | 265, 266 |
| `aa859:trip_reallocation_pool` | trip-reallocation suggest and confirm | 265, 266 |
| `aa859:marketplace_pool` | GET `/v1/marketplace` | 266 |
| `aa859:reviews_pool` | GET the content-writing reviews and one review | 265, 266 |
| `aa986:tenant_notifications_pool` | GET `/v1/notifications`, POST `.../read` | 274 |
| `aa814:facts_pool` | GET / POST `/v1/facts`, PATCH / DELETE `/v1/facts/{id}` (tenant Facts Entries) | 302 |

"Needs migration" names the CIS migration whose RLS and grants the route relies on: before rolling that migration back,
turn the flag off. A new route flag is added to `ALL_TENANT_POOL_FLAGS` (a unit test checks it), to the flag tool's
allow-list and to this table. To ship a route dark, set its key to `false` on Dev **before** the deploy (a missing key is on).

## Booking

| Flag | Kind | Where | Default | Live value | Owner | remove_by | Notes |
|---|---|---|---|---|---|---|---|
| `WORKER_ENABLED` | ops | ECS task env | on in `dev` when a database URL is set | not set, so on (2026-10-28) | tech lead | none | Off makes `aa-booking-dev-jobs-sampling-stopped` fire by design |
| `JOB_TEST_KINDS` | ops | ECS task env (Terraform `booking.tf`) | off | `1` on Dev (2026-10-28) | tech lead | none | Registers the test-only kind `bk_noop_sleep` (AA-993 G4) |
| Deploy-blocking kinds | ops | code (`backend/app/jobs/kinds.py` `DEPLOY_BLOCKING_KINDS`) | `bk_retention_job`, `bk_retention_inbox_redact` | same | tech lead | none | The deploy gate blocks only while one of them runs or is due within 15 minutes (AA-993 G5) |
| Deploy-gate exempt kinds | ops | code (`DEPLOY_GATE_EXEMPT`) | `bk_inquiry_pull`, `bk_noop_sleep` | same | tech lead | none | Left out of the gate's counts, which are information only since AA-993 G5 |

## TripPlanner

| Flag | Kind | Where | Default | Live value | Owner | remove_by | Notes |
|---|---|---|---|---|---|---|---|
| `REQUIRE_REGISTRATION_BEFORE_HANDOFF` | release | assembly Lambda env (Terraform `tripplanner.tf`) | `true` | `true` (2026-10-19) | tech lead | TBD (tech lead): no removal date recorded | Registration required before send-to-advisor |
| `TP_DAILY_SPEND_CAP_USD` | ops | Lambda env (both functions) | `5.0` (placeholder; the business cap is open for the tech lead) | not set, so 5.0 (2026-10-19) | tech lead | none | Daily cap on customer-facing model spend; over it, narration falls back and free-text search answers 503 |
| `GUEST_LEGACY_GRACE_UNTIL` | release | code constant (a reviewed deploy changes it) | 2026-10-16 00:00 UTC, already past (closed S239) | closed | tech lead | proposed: delete the dormant grace path in the next guest-session change | Not an env var on purpose |

## Removed

| Flag | Removed | Why |
|---|---|---|
| `deploy_gate_exempt` on `ops_rds_role_connections` (CIS) | AA-751 | The RDS sample left the job runner; the kind is retired and auto-cancelled |
