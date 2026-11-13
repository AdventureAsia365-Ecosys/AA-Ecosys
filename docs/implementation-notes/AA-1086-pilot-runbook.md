# AA-1086 part 1: pilot onboarding runbook and synthetic rehearsal plan (S279 lane l4-pilot-runbook)

Docs only, root repo. Two pages: `docs/ops/runbooks/pilot-agency-onboarding.md` (OPS-12-pilot-onboarding) and
`docs/ops/runbooks/pilot-rehearsal.md` (OPS-12-pilot-rehearsal), listed in `docs/ops/README.md` and the catalog
(`docs/README.md`, new row OPS-12). Every tool named was read on `origin/main` of the child repos on 2026-11-13.

## Decisions

- **Two tenants for the rehearsal, not one.** The S278 audit planned `pilot-rehearsal-01` as the pilot (`kind` agency,
  `pilot_weeks` 1). On `origin/main` every E2E write path treats a tenant as synthetic only when `is_canary` is true
  and it is not the pilot (CIS `api/core/e2e_staff.py` `SYNTHETIC_TENANT_SQL`; Booking via
  `catalog.v_tenant_account_v1.is_synthetic`), and the saga sets `is_canary = (kind == "demo")`. A pilot rehearsal
  tenant would refuse every A10b / A10e write, and would hold Dev's one pilot slot all run. So `pilot-rehearsal-01` is
  `demo` (the whole chain) and a separate `pilot-rehearsal-01-marker` (`agency`, `pilot_weeks` 1, no add-ons) carries
  steps 1b / 12b. Marked in the page as the plan's recommendation for the tech lead to confirm.
- **"Sellable in two trip plans"** read as: tour X is one of the sellable Booking trip plans (one plan per CIS tour;
  plan components are hotels and services, not tours) and the second sellable plan is the fallback X'. The audit's
  "2/892 trip plans have price and departure" is where the "two" comes from.
- **Status vocabulary:** automated (a committed spec or script ran live at least once), manual (UI or API, no spec),
  gap (cannot pass without new code or config).
- **Catalog ID OPS-12** (unused) with suffixes, like OPS-03-pilot-tenant.
- **Env names of the specs** are written exactly as in each spec header, in code spans, so they copy cleanly; no
  shell command with underscore variables is generated (the spec headers carry the full commands).

## Changed

- Nothing in code. The issue's "runbook merged" Done-when item is this PR; the rehearsal itself (README PASS/FAIL,
  pilot slot free, spend) is AA-1086 part 2.

## Tradeoffs

- The pages name tools by repo path and route rather than linking into child repos (lychee checks root links offline;
  child repos are not checked out in the root CI).
- The S278 system audit and the S279 verify evidence are referred to by path in prose, not linked, because they are
  copied into `docs/audits/` only at session close.

## Should know

- **Leaving pilot mode has no tool** (gap G2): no route clears `shared.tenants.is_pilot`, offboarding keeps it, and the
  unique index `tenants_one_pilot_key` keeps the slot taken. Step 12b cannot PASS until G2 lands or the tech lead
  approves a DB Migrate run-script write.
- **CRM A10c and the pilot** (gap G9): AA-Partner `api/app/tenancy.py` `E2E_SYNTHETIC_SQL` reads only
  `crm.tenant.is_synthetic`, and `app/agencies.py` makes every Dev CRM agency synthetic, the pilot's included. Before a
  real pilot holds data, the E2E CRM staff check should also exclude `is_pilot`.
- **Two AI budget pots** (gap G12): CIS `ai.budget_usd_monthly` covers the studio and TripPlanner; CRM drafts use
  `crm.tenant_settings.ai_budget_usd` and `crm.llm_call`. X1 tests both.
- **CRM agency is not created from the CIS feed**: `crm_entitlement_pull` leaves an unknown agency alone; the agency is
  created on Platform › Tenants › Agencies (CRM) under the CIS tenant id.
- **Owner invitations:** A10b may invite viewer or editor only, so the owner invitation is a tech lead step until G1.
- The New tenant modal calls the synchronous `POST /admin/tenants` (no pilot, no add-ons): the pilot is API-only (G2a).
- Step 5 depends on this wave's TripPlanner change (the AA catalogue keyed on the AA-hosted tenant): before it, a
  `demo` agency's planner lists the AA catalogue instead of its adopted tours.

## Review fix pass (S279)

Seven reviewer findings, all confirmed against `origin/main` of the child repos and fixed:

- **X2 restore is two calls.** `restore_master` (AA-CIS-App `services/tour_lifecycle/service.py`) brings the Master back
  `inactive`; only `PATCH /admin/master/<tour-id>/activate` serves it again (409 `source_not_live` or the
  elephant-riding policy refusal are named).
- **Job status.** `GET /admin/tenants/provision/<job-id>` returns the `shared.job.status` column: `succeeded`, never
  `done` (`job_status_check`).
- **G9 is a stop check.** Onboarding "Before you start" step 5 aborts unless the CRM E2E staff check excludes the pilot
  or A10c is off on the CRM. G9 is held by AA-1086 as a pre-pilot gate until the tech lead approves an AA-Partner issue.
- **Teardown section** in the rehearsal: the 12b hand write (DB Migrate run-script, DRY RUN), soft offboard and
  `data_erasure` of the marker tenant (DRY RUN fingerprint; the apply waits for the retention window),
  `pilot-rehearsal-01` kept as a synthetic fixture, channel posts removed. Step 1b now waits for G2 or the tech lead's
  written acceptance of the hand write.
- **X2 blast radius.** A read-only pre-check first: the CIS `lifecycle-preview` dry run, the tenants behind the
  derivative counts with their `is_canary` / `is_pilot` / `auto_draft`, and the Booking open cases and holds (the
  pull's own `AFFECTED_CASES_SQL` / `PLAN_SQL`); abort unless all are synthetic; restore before any `draft_due_at`.
- **Spend report.** Shadow rows are billed A/B calls (CIS 319), so the query keeps them and groups by
  `coalesce(is_shadow, quality_signal @> '{"shadow": true}')`, with `coalesce(app, quality_signal->>'app', 'cis')`; the
  stop rule counts shadow rows and `crm.llm_call`.
- **TripPlanner reason codes.** The tenant cap is `tenant_budget_cap` (narration `ai_budget_exhausted`), no budget
  `tenant_budget_none`, unreadable `tenant_budget_unreadable` (`backend/shared/tenant_budget.py`); `cap_reached` /
  `spend_unreadable` are the app-wide caps (`backend/aa_llm/budget.py`) and count as a FAIL of X1.

## S279 lane l16: G1, G2 and G9 closed

- **G1** (rehearsal fixture): AA-CIS-App `e2e_fixtures rehearsal-tenant --run <run> [--apply]` enqueues the saga for
  `pilot-rehearsal-01` (`demo`, both add-ons) under the AA-Partner seed id of the same key; the CRM seed catalogue holds
  the agency (owner + agent); AA-CIS-Infra `crm_e2e_users.json` lists the two E2E users. The rehearsal Fixtures section
  now names the three commands in order.
- **G2** (leave pilot mode): AA-CIS-App `POST /admin/tenants/{tenant_id}/pilot/end` (administrator, reason required,
  audited `tenant.pilot_ended`, idempotent) and the Tenant 360 › Subscription "End pilot" button. Onboarding Step 8,
  rehearsal step 12b and Teardown 1 use it; the DB Migrate hand write is gone.
- **G2a** stays open as a follow-up (the New tenant modal still calls the synchronous create).
- **G9** (E2E staff vs pilot): AA-Partner `E2E_SYNTHETIC_SQL` and `SYNTHETIC_AGENCY_SQL` read
  `is_synthetic IS TRUE AND is_pilot IS NOT TRUE` (crm-044 marker, no migration). Before-you-start step 5 stays a stop
  check on the deployed image.
