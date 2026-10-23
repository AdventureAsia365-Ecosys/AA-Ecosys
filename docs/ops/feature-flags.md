---
id: OPS-06
title: Feature-flag register
description: Every runtime flag and kill switch in the ecosystem, by name only - where it lives, its default, who owns it and when it is removed.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, aa-cis-frontend, aa-booking-api, tripplanner-lambda]
last_reviewed: 2026-10-19
review_every_days: 90
related: [OPS-06-legacy-login, OPS-10, APP-09, APP-03, docs/architecture/data-standards/02-data-management.md, AA-544, AA-816, AA-892]
---

# Feature-flag register

This register is a document, not a database table: data standard DM-1.5 rules out a `shared.feature_flag` table for
now. Add a row in the same PR that adds a flag, and move it to "Removed" in the PR that deletes it.

Names only. Values that are secrets never appear here. Environment variable names contain underscores: Nghiệp edits
their values by hand (Terraform in VSCode, the Vercel dashboard); agents describe the change and do not generate it.

**Checked against code on `main` and live configuration on 19/10/2026** (CIS `api/core/aa544_tenant_pool.py`,
`api/core/staff_identity.py`, `frontend/lib/staffSession.ts`, `shared/jobs/worker.py`; Booking `backend/app/settings.py`;
TripPlanner `backend/config.py`; the live CIS and Booking task definitions; Infra `modules/ecs/main.tf`,
`accounts/aa365/tripplanner.tf`).

## Columns

- **Kind:** `release` (temporary, removed after rollout), `ops` (kill switch or operational setting, permanent),
  `security` (a security control; never removed by date).
- **remove_by:** the event or date after which the flag is deleted. Security controls have none.

## CIS

| Flag | Kind | Where it is set | Default (code) | Live value 19/10 | Owner | remove_by | Notes |
|---|---|---|---|---|---|---|---|
| `LEGACY_ADMIN_LOGIN_ENABLED` | release | API: ECS task env (not set); BFF: Vercel `aa-cis-frontend` env per target (Production `false`) | **off** since AA-816 S2, 22/10 (only `1`/`true`/`yes`/`on` turn it on; ADR 0006a A12) | off (API unset; checked 23/10) | nghiep | with the bridge retirement (AA-911 P6b, end of project): delete the flag and the HS256 staff path | [Runbook](runbooks/legacy-login-flag.md) (rollback). Gates the password form, BFF `/api/auth/login` and the HS256 path of `/auth/verify-admin`, not `/auth/admin-login` or `/auth/booking-token` |
| Tenant-pool route flags (11 Redis keys, below) | security | Redis (ElastiCache, single node, no persistence) | on = tenant pool with RLS; a missing key or a read error is on (fail closed, D-12) | all on since 16/10/2026 (AA-859 flip report) | nghiep | none (C2.3g, DM-8.4, D-12) | Only an explicit `false` (also `0`/`off`/`no`) sends one route back to the admin pool. A Redis restart drops every key, so every route is back on |
| `TENANT_POOL_FORCE_ADMIN_FLAGS` | security (emergency) | API ECS task env (comma-separated flag keys) | empty | not set | nghiep | none; must stay empty except during an incident | Durable per-route switch back to the admin pool, read at process start, survives Redis restarts. An unknown key is logged as an error. [Break-glass C](runbooks/break-glass.md#c-tenant-pool-emergency-switch) |
| `JOB_WORKER_IN_API` | ops | API ECS task env (Terraform `modules/ecs`) | off | `false` | nghiep | none | Jobs run on `aa-cis-dev-worker` (AA-735, ADR 0003). On only for local development |
| Workforce sign-in domain override | ops | BFF env (Vercel) | the custom domain `staff-auth.lumiguides.it.com` (code constant) | not set | nghiep | none | Points sign-in back at the pool's prefix domain (ADR 0006a A5) |
| Cost guard limits | ops | `shared.spend_budget` rows, admin **Budgets** page | migration seed values | see the Budgets page | nghiep | none | Per provider and scope; `hard_stop` stops paid calls. [LLM cost spike](playbooks/llm-cost-spike.md) |
| Per-stage LLM route | ops | `shared.llm_role_config` via admin LLM config | per stage | see the LLM config page | nghiep | none | Model switch per stage (APP-06, AA-900) |

### Tenant-pool route keys (CIS `ALL_TENANT_POOL_FLAGS`)

| Redis key | Route(s) | Needs migration 241 |
|---|---|---|
| `aa544:stage1:publish_pending_pool` | GET `/v1/publish-log/pending` | no |
| `aa544:stage5:get_piece_pool` | GET `/v1/content-writing/pieces/{id}` and `/export` | no |
| `aa544:publish_log_list_pool` | GET `/v1/publish-log` | no |
| `aa544:integration_disconnect_pool` | DELETE `/v1/integrations/{wordpress,facebook}` | no (needs 237) |
| `aa817:content_piece_reads_pool` | GET `/v1/content-writing/requests/{id}/latest-piece` | no |
| `aa859:piece_edit_pool` | PATCH `/v1/content-writing/pieces/{id}` | no |
| `aa859:t2_version_write_pool` | PATCH `/v1/tours/versions/{id}` | no |
| `aa859:angle_gate_decide_pool` | POST `/v1/angle-gate/requests/{id}/choose` and `/reopen` | yes |
| `aa859:unpublish_pool` | DELETE `/v1/publish-log/{id}` | no |
| `aa859:t2_version_reads_pool` | GET `/v1/tours/pool`, `/my-versions`, `/versions/{id}` | no |
| `aa859:integration_connect_pool` | GET/POST `/v1/integrations/{wordpress,facebook}` and `/test` | yes |

A new route flag is added to `ALL_TENANT_POOL_FLAGS` (a unit test checks it), to the flag tool's allow-list and to this
table. To ship a route dark, set its key to `false` on Dev **before** the deploy (a missing key is on).

## Booking

| Flag | Kind | Where | Default | Live value 19/10 | Owner | remove_by | Notes |
|---|---|---|---|---|---|---|---|
| `WORKER_ENABLED` | ops | ECS task env | on in `dev` when a database URL is set | not set (on) | nghiep | none | Off makes `aa-booking-dev-jobs-sampling-stopped` fire by design |
| Deploy-gate exempt kinds | ops | code (`backend/app/jobs/kinds.py`) | `bk_inquiry_pull` | same | nghiep | none | Not counted by the deploy gate |

## TripPlanner

| Flag | Kind | Where | Default | Live value 19/10 | Owner | remove_by | Notes |
|---|---|---|---|---|---|---|---|
| `REQUIRE_REGISTRATION_BEFORE_HANDOFF` | release | assembly Lambda env (Terraform `tripplanner.tf`) | `true` | `true` | nghiep | TBD (Nghiệp): no removal date recorded | Registration required before send-to-advisor |
| `TP_DAILY_SPEND_CAP_USD` | ops | Lambda env (both functions) | `5.0` (placeholder; business cap open for Nghiệp) | not set (5.0) | nghiep | none | Daily cap on customer-facing model spend; over it, narration falls back and free-text search answers 503 |
| `GUEST_LEGACY_GRACE_UNTIL` | release | code constant (a reviewed deploy changes it) | an instant already past (closed S239) | closed | nghiep | proposed: delete the dormant grace path in the next guest-session change | Not an env var on purpose |

## Removed

| Flag | Removed | Why |
|---|---|---|
| `deploy_gate_exempt` on `ops_rds_role_connections` (CIS) | AA-751 | The RDS sample left the job runner; the kind is retired and auto-cancelled |
