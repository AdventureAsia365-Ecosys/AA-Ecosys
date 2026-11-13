---
id: OPS-12-pilot-onboarding
title: Onboard a pilot agency
description: Onboard the Dev pilot agency - provision, owner invitation, brand, modules and add-ons, AI budget, entering and leaving pilot mode, exit - with the page, route, script or job kind that does each step today, and the gaps.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [aa-cis-api, aa-crm-dev-api, aa-crm-dev-web, aa-booking-dev-api, tripplanner, ecosystem]
last_reviewed: 2026-11-13
review_every_days: 90
related: [OPS-12-pilot-rehearsal, OPS-03-pilot-tenant, OPS-05-ecs-exec, AA-1086, AA-1093, AA-1082, docs/adr/0019-b2b-only-ecosystem-model.md, docs/adr/0006a-identity-phase1-amendments.md]
---

# Onboard a pilot agency

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.

Root [ADR 0019](../../adr/0019-b2b-only-ecosystem-model.md) d16 lets Dev hold exactly one real agency, the pilot, for
at most eight weeks. Every other Dev tenant is synthetic. This runbook takes one agency from "agreement signed" to
"working in all four apps", then out of pilot mode again. The synthetic dress rehearsal of the same chain is the
[pilot rehearsal plan](pilot-rehearsal.md).

Each step names the tool that does it today. The code was read on `origin/main` of each repo on 2026-11-13 (AA-CIS-App
`995241bc4`, AA-Partner `5d302757`, AA-Booking `a73b031`, AA-TripPlanner-Web `9c3c213`, AA-CIS-Infra `c937d4c`).
Where no tool exists, the step says **Gap** and names the issue that owns it. The full gap list is at the
[end of this page](#gaps).

## Roles

| Role | Does |
|---|---|
| Tech lead | Every staff write below: the CIS admin role (`tenant.write`, `spend.write`) and the CRM `crm-platform-admin` group. No Dev-only E2E identity may create a tenant, create a CRM agency, invite an owner or touch the pilot (root ADR 0006a A10b-1: E2E writes are for synthetic tenants only, and the pilot is never synthetic) |
| Engineer on duty or the orchestrating agent | Reads, checks and evidence. It may run the admin-secret scripts the tech lead approved (the system audit's option b) |
| Agency owner | Accepts the invitation, enrols MFA, imports the brand, switches on CRM features and sets the CRM AI budget |

## What pilot mode changes

A pilot tenant is `shared.tenants.kind = agency` with `is_pilot` true and a `pilot_ends_at` date (CIS migration 354:
one pilot at most, unique index `tenants_one_pilot_key`; a CHECK makes it `kind` agency).

| Rule | Where it is enforced |
|---|---|
| On Dev a new `agency` is refused unless it is the pilot | AA-CIS-App `services/tenant_account/dev_guard.py` (`dev_real_tenant_refused`, `pilot_taken`, `pilot_dev_only`) |
| No Dev-only E2E identity may write on it | AA-CIS-App `api/core/e2e_staff.py` (`is_canary IS TRUE AND is_pilot IS NOT TRUE`); AA-Booking `app/auth/e2e_staff.py` (`catalog.v_tenant_account_v1.is_synthetic`) |
| CIS clean-up jobs skip it | AA-CIS-App `services/retention/policy.py` (`NOT_PILOT`) |
| The CRM backs it up every night and its clean-up skips it | AA-Partner job kind `crm_pilot_backup`; `app/lifecycle/pilot.py` (marker `crm.tenant.is_pilot`, projected by `crm_entitlement_pull`) |
| Agents never read its personal data | root `.claude/hooks/pilot_pii_guard.py` |
| Its end date is reported, never acted on | AA-CIS-App job kind `tenant_account_tick` (hourly), log line `tenant_pilot_ended` |

> [!NOTE]
> On Dev the CRM creates synthetic agencies only (AA-Partner `app/agencies.py`, `SYNTHETIC_ONLY_ENVIRONMENTS`), so the
> pilot's CRM agency carries `crm.tenant.is_synthetic` true like every other Dev agency. The CRM's Dev-only E2E staff
> check (AA-Partner `api/app/tenancy.py`, `E2E_SYNTHETIC_SQL`) therefore also reads the pilot marker
> (`crm.tenant.is_pilot`, crm-044): the A10c identity never reaches the pilot agency (gap G9, closed by AA-1086 in
> S279). Step 5 of [Before you start](#before-you-start) checks it.

## Before you start

1. Confirm the account.

   ```bash
   aws sts get-caller-identity --profile aa365-admin
   ```

   Expected: account `aa365-admin` resolves to acc2 (see the account map in [onboarding](../../onboarding.md)).
   Abort if it is any other account.

2. Confirm the pilot slot is free. In the CIS admin, open **Platform › Tenants** and look for a "Pilot until ..."
   badge on Tenant 360 › Subscription. For a query, follow
   [Query the database through ECS exec and S3](ecs-exec-s3-mediated.md) with:

   ```sql
   SELECT slug, pilot_ends_at FROM shared.tenants WHERE is_pilot;
   ```

   Expected: no row. Abort if a row is there: Dev holds one pilot only. End the old pilot first ([Step 8](#step-8-leave-pilot-mode)).

3. Have the business inputs ready: the signed agreement and DPA, the legal name and billing details, the owner's work
   e-mail address, the markets, the content tier (`starter`, `growth` or `business`) and the posts per week.
4. Confirm the agency web can carry a real agency. The CRM web and the studio run as one Fargate Spot task today, and
   a second task needs the tech lead's cost approval (AA-1082). Abort if AA-1082 is not done and the tech lead has not
   accepted the risk in writing.
5. Confirm the Dev-only CRM staff identity (A10c, `e2e-crm-staff@`) cannot reach the pilot. **Abort unless** the CRM E2E
   staff check excludes `crm.tenant.is_pilot` (gap G9, closed by AA-1086: `E2E_SYNTHETIC_SQL` on `origin/main` of
   AA-Partner reads `is_synthetic IS TRUE AND is_pilot IS NOT TRUE`, and the deployed `aa-crm-dev-api` image carries
   that commit) **or** A10c is switched off on the CRM. Otherwise that identity can open S-02 views and S-04 support sessions on the real
   agency, which breaks root ADR 0006a A10b-1 (E2E writes on synthetic tenants only) and the pilot personal-data rule.
   There is no waiver for this check.

## Step 1: provision the tenant

The `tenant_provision` saga (AA-CIS-App `services/tenant_account/provision.py`, job kind `tenant_provision` on
`shared.job`) creates the tenant, its content subscription and its add-ons in one job, idempotent per request key.

1. As the tech lead, call `POST /admin/tenants/provision` (AA-CIS-App `api/routers/admin_tenant_provision.py`) from
   the signed-in CIS admin session (admin BFF path `/api/admin/tenants/provision`) or with the approved admin-secret
   script. Body:

   ```json
   {
     "request_key": "pilot-<agency-slug>-001",
     "name": "<agency legal or trading name>",
     "slug": "<agency-slug>",
     "plan_tier": "growth",
     "posts_per_week": 3,
     "kind": "agency",
     "pilot_weeks": 6,
     "add_ons": [
       {"product": "crm", "plan_key": "crm.core", "seats": 3},
       {"product": "tripplanner", "plan_key": "tripplanner.hosted"}
     ]
   }
   ```

   `<agency-slug>` is the lower-case slug the agency's TripPlanner path will use. `pilot_weeks` is 1 to 8. Add
   `trial_days` only if the agreement starts with a trial.
2. Poll `GET /admin/tenants/provision/<job-id>` until `status` is `succeeded` (the `shared.job` status). `<job-id>` is
   the `job_id` of the 202 answer. `failed` (read its `error`), `cancelled` or `stopped_budget` means abort.

- **Expected:** steps `tenant_created`, `pilot_marked`, `content_active` (or `content_trialing`), `crm_subscribed`,
  `tripplanner_subscribed`. Tenant 360 › Subscription shows the "Pilot until ..." badge.
- **Verify:** within about five minutes `bk_tenant_pull` (AA-Booking) has the agency's partner row; Booking lists it
  under agencies.
- **Abort:** `pilot_taken` means another pilot exists (stop; see Before you start, step 2). `slug_taken` means the slug
  exists: pick another one. Nothing was written in either case.
- **Rollback:** soft offboard, `POST /admin/tenants/<tenant-id>/offboard` (**Offboard** on the tenant list, `/admin/tenants`, reason required). It keeps
  `is_pilot`, so the slot stays taken until the pilot is ended ([Step 8](#step-8-leave-pilot-mode)).

> [!NOTE]
> **Gap G2a.** The **New tenant** modal on `/admin/tenants` calls the synchronous `POST /admin/tenants`. It has no
> pilot field and no add-ons, and on Dev it refuses `kind` agency. The pilot is API-only today. Owner: AA-1086.

## Step 2: create the CRM agency

The CRM does not create an agency from the CIS feed: `crm_entitlement_pull` leaves an unknown agency alone. Create it
under the CIS tenant id.

1. As the tech lead (group `crm-platform-admin`), open **Platform › Tenants › Agencies (CRM)**
   (`/admin/tenants/agencies`) and use **Create an agency** with the tenant id from step 1, the agency name and its
   default locale. The page calls `POST /admin/platform/crm/agencies`, which relays to `crm.ops.v1 POST /tenants`.
2. Wait for the next `crm_entitlement_pull` run (every slot, plus an hourly reconcile).

- **Expected:** 201 with the agency summary. An existing id is 409 `tenant_exists` and nothing is written.
- **Verify:** the agency drawer shows plan core, the allowed features of `crm.core` and the seat limit. Its pilot marker
  follows the CIS snapshot (`crm.tenant.is_pilot`).
- **Abort:** 403 means the caller lacks `crm-platform-admin`.

## Step 3: invite the owner

The owner signs in once (the partner pool, MFA required) and holds two memberships: the Content studio owner (a CIS
membership) and the CRM agency owner. Both mails are AA system mails that the CRM delivers.

1. **Content studio owner.** Tenant 360 › Members › **Invite** with role `owner` (`POST
   /admin/tenants/<tenant-id>/members/invitations`, AA-CIS-App `api/routers/admin_tenant360.py`). Only the admin role
   may grant `owner`. The Dev-only E2E admin (A10b) may invite `viewer` or `editor` on synthetic tenants only.
2. **CRM first owner.** In the agency drawer of step 2, use **Invite owner** (`POST
   /admin/platform/crm/agencies/<tenant-id>/owner-invite`).
3. The owner opens each mail, claims the account (`/crm/public/v1/invitations/claim`), sets a password, enrols an
   authenticator and accepts. The studio acceptance queues `crm_studio_activation`, which activates the CIS membership.

- **Expected:** the owner lands on `portal.lumiguides.it.com` with the Content studio, the CRM and the TripPlanner
  module in the app switcher.
- **Verify:** Tenant 360 › Members lists the owner as `active`; the CRM agency drawer lists one active owner.
- **Abort:** an invitation mail that never arrives: check the SES alarms with [SES bounce](ses-bounce.md). Send it
  again with **Send again** (`POST /admin/tenants/<tenant-id>/members/<membership-id>/invitation/send`).

## Step 4: import the brand

1. The owner opens **Brand** in the studio (`/portal/brand`) and uploads the brand guide as `.docx`. The page calls
   the CIS routes `POST /admin/brand-identity/upload`, then `/admin/brand-identity/parse`, then saves with
   `POST /admin/brand-identity` (through the studio BFF `/api/tenant/admin/brand-identity*`, tenant-scoped).
2. The owner checks the parsed voice, the words to use and the words to avoid, and saves.

- **Expected:** the Getting started checklist ticks the brand step.
- **Verify:** Tenant 360 › Voice memory and the brand rules show the new brand.
- **Staff alternative:** `PUT /admin/tenants/<tenant-id>/brand-identity` (admin).

> [!NOTE]
> **Gap G13.** The TripPlanner site colours do not come from the brand: there is no editor for the TripPlanner theme
> (it was written by hand on Dev in S275), so the brand is set more than once (system audit M32). No issue holds it yet.

## Step 5: modules and add-ons

| Need | Tool today |
|---|---|
| Content tier | `plan_tier` at step 1; later Tenant 360 › Settings (plan) |
| CRM, TripPlanner | `add_ons` at step 1; later Tenant 360 › Subscription › **Add an add-on** / **Change** / **Cancel** (`POST /admin/tenants/<tenant-id>/provision`, `.../provision/cancel`, the same saga) |
| Owner asks for an add-on | Studio `/portal/account/add-ons` (`POST /v1/account/add-on-requests`); staff approve or decline on Tenant 360 (`POST /admin/tenants/<tenant-id>/addon-requests/<request-id>/approve` or `/decline`) |
| One feature on or off, or a limit | Tenant 360 › Subscription › overrides (`PUT /admin/tenants/<tenant-id>/entitlement-overrides/<feature-key>`, reason required, optional expiry) |
| CRM features the plan allows | The owner switches them on in CRM **Settings** (the plan decides what is allowed) |
| TripPlanner leads | With `crm.core` and `tp.hosted` both entitled, leads go to the CRM (`crm_tp_lead_pull`). Without the CRM add-on: Tenant 360 lead route (`PUT /admin/tenants/<tenant-id>/tripplanner-site/lead-route`: webhook or e-mail) |
| Book with AA | Booking partner row from `bk_tenant_pull` (the content plan's `trade.book`); AA lines in the CRM go through `booking.b2b.v1` |

- **Verify:** the agency snapshot `GET /tenant/v1/tenants/<tenant-id>/account` (M2M) and Tenant 360 › Subscription
  agree; the CRM drawer shows the projected features within one pull slot.

## Step 6: set the AI budget

The AI budget lives in two pots today.

| Pot | Covers | Set by | Ledger |
|---|---|---|---|
| CIS `ai.budget_usd_monthly` (resolved: an override on Tenant 360 › Subscription, else the tenant row on Tenant 360 › Cost › AI budget, else the plan's included spend) | Content studio stages and TripPlanner (TripPlanner reads `catalog.v_tenant_ai_budget_v1`, CIS 390) | Tech lead: `PUT /admin/ai-gateway/tenant-budgets/<tenant-id>` (`spend.write`) or the override route of step 5 | `shared.llm_call_log` |
| CRM `crm.tenant_settings.ai_budget_usd` (default 2 USD, at most the plan cap) | CRM AI drafts (`ai_assist` entitlement, AI off by default) | Agency owner: CRM **Settings › AI** (`PUT /crm/v1/settings/ai`) | `crm.llm_call` |

1. Set the CIS budget the agreement names. A budget of 0 stops every T-stage and ad-hoc AI call of the tenant.
2. Ask the owner to set the CRM budget and switch AI on if the plan includes it.

- **Expected:** Tenant 360 › Cost shows the effective budget and its source.
- **Verify:** TripPlanner fails closed per tenant (AA-TripPlanner-Web `backend/shared/tenant_budget.py`): a tenant
  with no resolved budget gets no AI with reason `tenant_budget_none`, a budget that cannot be read gives
  `tenant_budget_unreadable`, and a spent or 0 USD budget gives `tenant_budget_cap` (narration says
  `ai_budget_exhausted`). `cap_reached` and `spend_unreadable` are the app-wide gateway caps (`backend/aa_llm/budget.py`),
  not the tenant budget. Read Tenant 360 › Cost after the owner's first session.

> [!NOTE]
> **Gap G12.** A CIS override does not reach CRM drafts: the CRM has its own pot and ledger. Whether one budget should
> cap all apps is a tech lead decision. No issue holds it yet.

## Step 7: during the pilot

- The nightly CRM export of the pilot (`crm_pilot_backup`) and its restore drill: [Restore one tenant's CRM data from
  its nightly export](pilot-tenant-restore-drill.md). Run the drill once before the pilot holds real data.
- Agents read the pilot's data only as counts and ids (`pilot_pii_guard`).
- `tenant_account_tick` logs `tenant_pilot_ended` once `pilot_ends_at` has passed. It changes nothing: ending a real
  agency's service is the tech lead's call, with notice.
- CIS and TripPlanner have no one-tenant restore yet (AA-1093 part 3).

## Step 8: leave pilot mode

Gap G2 is closed (AA-1086, S279): the CIS administrator ends the pilot.

1. Tenant 360 › Subscription › **End pilot** (shown to the administrator only, next to the "Pilot until ..." badge),
   with a reason, or `POST /admin/tenants/<tenant-id>/pilot/end` with `{"reason": "..."}` (`tenant.write`, BFF
   `/api/admin/...`). It clears `is_pilot` and `pilot_ends_at` together in one transaction, writes one
   `tenant.pilot_ended` audit row (reason, the end date it had, whether it ended early) and one
   `account.status_changed` event with the status unchanged, so the CRM marker follows at the next
   `crm_entitlement_pull` (about 2 minutes).
2. A tenant that is not the pilot answers 200 with `changed` false and nothing is written; a second click is harmless.
   Any account status is accepted, an offboarded pilot included.
3. The route does not change `kind`: on Dev a non-pilot `agency` is then offboarded (root ADR 0019 d16).

- **Expected:** `SELECT slug FROM shared.tenants WHERE is_pilot` returns no row.
- **Verify:** the CRM agency's pilot marker is false after one pull; `crm_pilot_backup` stops queuing its export.

## Step 9: exit (offboarding)

An agency that leaves is offboarded in every app. Only parts exist today; the cross-app saga is AA-1093.

| App | Today |
|---|---|
| CIS | Soft offboard `POST /admin/tenants/<tenant-id>/offboard` (**Offboard** on `/admin/tenants`; `/restore` reverses it). Erasure: the `data_erasure` job, DRY RUN fingerprint first, then apply with the tech lead's approval |
| CRM | Owner-driven: CRM **Settings › Data**, "leave AA Partner": export, then erase (job kinds `crm_offboard`, `crm_data_export`), 72 h cool-off. When CIS stops serving the tenant the CRM only locks the agency |
| Booking | No tenant erasure. `bk_tenant_pull` suspends the partner row |
| TripPlanner | No tenant erasure |

Follow AA-1093 for the saga that erases or anonymises the tenant in every app on the agreed schedule. Until it lands,
an exit is a manual, per-app job with the destructive-ops procedure (`skill/aa-cis-schema/references/destructive-ops.md`).

## Gaps

| ID | Gap | Repo | Owner |
|---|---|---|---|
| G2 | Closed (S279): `POST /admin/tenants/<tenant-id>/pilot/end` and Tenant 360 › Subscription › **End pilot** ([Step 8](#step-8-leave-pilot-mode)) | AA-CIS-App | AA-1086 |
| G2a | The New tenant modal cannot create the pilot or add add-ons (API only). Still open: it needs the async saga call, job polling and three new fields; add-ons can be added on Tenant 360 › Subscription after the create | AA-CIS-App | follow-up of AA-1086 |
| G9 | Closed (S279): the CRM's Dev-only E2E staff check and the studio relay's synthetic check also exclude the pilot agency (`crm.tenant.is_pilot`), because Dev agencies are all synthetic. Still a stop check of Before you start, step 5 (the deployed image) | AA-Partner | AA-1086 |
| G12 | Two AI budget pots (CIS + TripPlanner, CRM) | AA-Partner, AA-CIS-App | none yet |
| G13 | No TripPlanner theme editor; the brand is set by hand | AA-CIS-App, AA-TripPlanner-Web | none yet (system audit M32) |
| - | Agency web on one Spot task | AA-CIS-Infra | AA-1082 |
| - | Offboarding erase in every app, per-tenant restore for CIS and TripPlanner | all | AA-1093 |

The synthetic rehearsal's own gaps (specs and scripts) are listed in the [pilot rehearsal plan](pilot-rehearsal.md#gaps).
