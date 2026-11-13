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
