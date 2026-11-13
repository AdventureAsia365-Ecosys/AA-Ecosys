---
id: OPS-12-pilot-rehearsal
title: Rehearse a pilot with a synthetic agency
description: The synthetic pilot rehearsal on Dev - one synthetic agency and one AA tour through every app in 13 steps (0-12), with the cross-app checks, the LLM spend cap, the automation each step has today and the gaps.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [aa-cis-api, aa-crm-dev-api, aa-crm-dev-web, aa-booking-dev-api, tripplanner, ecosystem]
last_reviewed: 2026-11-13
review_every_days: 90
related: [OPS-12-pilot-onboarding, OPS-03-pilot-tenant, OPS-05-ecs-exec, AA-1086, AA-1093, AA-1079, AA-1082, docs/adr/0006a-identity-phase1-amendments.md, docs/adr/0019-b2b-only-ecosystem-model.md]
---

# Rehearse a pilot with a synthetic agency

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.

Every link of the agency chain works on Dev, but no one has taken one newly provisioned agency through all of it on
the real UI (system audit S278, section 4: readiness about 70 %). This plan does that once, on a synthetic agency,
before a real agency joins. The real onboarding is the [pilot agency onboarding runbook](pilot-agency-onboarding.md).

**Done when** (AA-1086):

- The rehearsal README in `docs/audits/<date>-S<nnn>-pilot-rehearsal/` shows PASS for steps 0-12, or lists each FAIL
  with the issue that fixes it.
- The marker tenant leaves pilot mode at the end and the Dev pilot slot is free again.
- Real LLM spend is at most 10 USD (estimate 2-4 USD), reported per stage from the ledger.

The automation named below was read on `origin/main` of each repo on 2026-11-13 (AA-CIS-App `995241bc4`, AA-Partner
`5d302757`, AA-Booking `a73b031`, AA-TripPlanner-Web `9c3c213`, AA-CIS-Infra `c937d4c`).

## Two tenants, not one

The system audit proposed one tenant created as the pilot (`kind` agency with `pilot_weeks`). That tenant could not be
rehearsed with the Dev-only E2E write identities: CIS and Booking treat a tenant as synthetic only when `is_canary` is
true **and** it is not the pilot (root [ADR 0006a](../../adr/0006a-identity-phase1-amendments.md) A10b-1, A10e), and a
pilot's `is_canary` is false. Every staff write would then fall back to the tech lead's own sessions, and Dev's one
pilot slot would hold a fake agency for the whole run. So the rehearsal uses two tenants:

| Tenant | Kind | Used for |
|---|---|---|
| `pilot-rehearsal-01` ("E2E Pilot Rehearsal Travel") | `demo` (synthetic, `is_canary` true) | Steps 1-12: the whole agency chain |
| `pilot-rehearsal-01-marker` | `agency` with `pilot_weeks` 1, no add-ons | Steps 1b and 12b only: entering and leaving pilot mode, and the second-pilot refusal |

This split is the plan's recommendation; the tech lead confirms it before step 1. If the tech lead keeps the audit's
single pilot tenant instead, every row marked "E2E identity" below becomes a tech lead step.

## Fixtures

### The synthetic agency `pilot-rehearsal-01`

Created through the CIS provisioning path, the `tenant_provision` saga (AA-CIS-App
`services/tenant_account/provision.py`, job kind `tenant_provision`), by the tech lead, because no E2E identity may
create a tenant (ADR 0006a A10b-4):

- AA-CIS-App fixture (gap G1, closed by AA-1086): `python -m services.tenant_account.e2e_fixtures rehearsal-tenant --run
  <run>` through ECS Exec on `aa-cis-dev-api`, DRY RUN first, then `--apply`. It enqueues the same saga as
  `POST /admin/tenants/provision` with `name` "E2E Pilot Rehearsal Travel", `slug` `pilot-rehearsal-01`, `plan_tier`
  `growth`, `posts_per_week` 2, `kind` `demo`, `add_ons` `crm` (`crm.core`, 3 seats) and `tripplanner`
  (`tripplanner.hosted`), request key `aa1086-pilot-rehearsal-01-<run>`, under the id AA-Partner's seed catalogue
  gives the agency key `pilot-rehearsal-01` (`41ea21ee-77ee-5474-bd6d-aa738d2da990`). It prints the tenant id and the
  job to poll; a tenant that already exists is reported with its subscriptions, never created twice.
- Its E2E owner and agent: AA-CIS-Infra `tools/identity/crm_e2e_users.json` lists
  `e2e-test-crm-pilot-rehearsal-01-owner` and `-agent`; `crm_dev_identity.py --pool partner e2e-users --apply
  --write-secrets` creates them (credentials in `crm/dev/e2e-test-crm/pilot-rehearsal-01-<role>`) and prints their
  subjects.
- Its CRM agency and members: AA-Partner `python -m app.seed --apply --agency pilot-rehearsal-01 --member
  pilot-rehearsal-01:owner:<sub> --member pilot-rehearsal-01:agent:<sub>` through ECS Exec on `aa-crm-dev-api`. The
  CRM and portal specs then run on it with `E2ECRMPARTNER` = the tenant id and the owner's `E2ECRMEMAIL`,
  `E2ECRMPASSWORD` and `E2ECRMTOTP`.

The `pilot-rehearsal-01-marker` tenant uses the same route with `kind` `agency`, `pilot_weeks` 1 and no add-ons.

### Tour X

One AA tour whose Booking trip plan is sellable: a price and at least one open departure inside the rehearsal window
(`GET /booking/catalog/trip-plans?sellable=true`; readiness on Booking **Pricing › Workbench**, `GET
/booking/catalog/price-workbench`). The S278 audit counted two such plans on Dev (2 of 892). Pick one as X and keep the
other as the fallback X' (the "two trip plans" of AA-1086). If fewer than two are sellable on the day, the
customer-service team prices one more before the run; that is not code.

At every stage the evidence checks the same tour: source id, name, number of days (`end = start + days - 1`) and price.

### Identities

| Identity (ADR 0006a) | Address | Writes it may make | Steps |
|---|---|---|---|
| A10b CIS admin | `e2e-cis-admin@e2e-mail.lumiguides.it.com` | Studio invitations (viewer or editor), view-as, release of a held piece, TripPlanner add-on: synthetic tenants only | 1, 4, evidence views |
| A10e Booking staff | `e2e-booking-staff@` | Supplier booking request and confirm; cancel a seeded synthetic departure (A10e-1) | 8, 9, X3 |
| A10e maker / checker | `e2e-booking-maker@`, `e2e-booking-checker@` | Record a payment / approve or reject it | 11 |
| A10a Booking admin | `e2e-booking@` | None (reads the audit log) | 8-11 reads |
| A10c CRM staff | `e2e-crm-staff@` | S-02 views and S-04 support sessions on synthetic agencies | 10 |
| Tech lead | own Cognito session | Create tenants and the CRM agency, owner invitations, the AI budget override, retire and restore a tour | 1, 1b, 2, 12, X2 |
| Agency owner / agent | members of `pilot-rehearsal-01` (partner pool, MFA) | Agency steps | 2-4b, 7, 8 |
| Traveller | invented name, address on `example.invalid` | Public pages | 5, 6, 8, 10 |

Every E2E identity signs in with an e-mail code from the E2E mailbox. Codes for A10b, A10c and A10e land under
`inbound-admin/`, which only the MFA admin role reads, so these runs are agent-only and never CI.

## Step 0: baseline (read only)

1. `aws sts get-caller-identity --profile aa365-admin` (expected: acc2, see [onboarding](../../onboarding.md)).
2. Every ECS service of `aa-cis-dev-cluster` runs the image of its repo's `main`:

   ```bash
   aws ecs list-services --cluster aa-cis-dev-cluster --profile aa365-admin --region us-west-1 --output text
   ```

3. The job tables are idle and no wave is open: CIS `/admin/job-runner/summary` and `/admin/waves`; the Booking,
   CRM and TripPlanner job tables are quiet (`booking.job`, `crm.job`, `tripplanner.job`).
4. Spend baseline: the CIS admin **AI gateway** page (month spend per connection and the caps). If the OpenAI month
   cap is nearly used, settle the judge route first (AA-1079): the judges have no live fallback.
5. The pilot slot is free (`SELECT slug FROM shared.tenants WHERE is_pilot` returns no row).
6. The WordPress test site answers JSON on `https://test-wp.lumiguides.it.com/wp-json/` (a free test site expires
   after about two weeks and then answers HTML), and the Facebook test Page is reachable from its integration.
7. SES: read whether the account is in the sandbox and that the mail domain verifies, before any invitation step.

Evidence: `baseline.json` (service, image, job counts, spend, slot, test-wp status). Status: manual.

## The 13 steps

Status: **automated** = a committed spec or script does it and ran live at least once; **manual** = a person or the
orchestrator does it in the UI or through the API, no spec; **gap** = it cannot pass today without new code or config
(gap IDs at the [end](#gaps)).

| Step | Actor | Surface | Automation today | Expected evidence | Status |
|---|---|---|---|---|---|
| 1. Provision `pilot-rehearsal-01` and its CRM agency; set its AI budget; try a second real agency | Tech lead | CIS admin, `POST /admin/tenants/provision`; `/admin/tenants/agencies` | None for the create. TripPlanner add-on alone: AA-CIS-App `tests/e2e/admin-evidence/tp-addon.spec.ts`, project `admin-evidence`, `E2EADMIN=1`, `TENANT_SYNTHETIC`, `TP_PLAN`, `E2E_DRY_RUN`, `E2E_CANCEL` (A10b). The fixture `e2e_fixtures rehearsal-tenant` and the CRM seed (see [Fixtures](#fixtures)) | Job `status` `succeeded` (`failed` with `error` = abort) with `tenant_created`, `content_active`, `crm_subscribed`, `tripplanner_subscribed`; `GET /tenant/v1/tenants/<tenant-id>/account` 200; CRM agency projected within one `crm_entitlement_pull` slot; Booking partner within about 5 minutes (`bk_tenant_pull`); `kind` agency without `pilot_weeks` refused 422 `dev_real_tenant_refused`, nothing written | fixture (G1 closed); the second-agency refusal manual |
| 1b. Enter pilot mode on the marker tenant; try a second pilot. Step 12b ends it with the end-pilot route (G2 closed) | Tech lead | `POST /admin/tenants/provision` (`kind` agency, `pilot_weeks` 1) | None | Steps `tenant_created`, `pilot_marked`; Tenant 360 › Subscription badge "Pilot until ..."; a second pilot refused `pilot_taken` | manual |
| 2. Invite the owner; owner signs in with MFA | Tech lead, then agency owner | Tenant 360 › Members › Invite (`owner`); agency drawer › Invite owner; `portal.lumiguides.it.com` | AA-Partner `e2e/phase2/phase2.spec.ts` (`e2e/playwright.phase2.config.ts`, `E2EP2=1`, `E2EP2STAFF`, `E2EP2SINCE`, `E2EP2OUT`) claims a viewer or editor invitation only; CRM `e2e/tests/invite.spec.ts` (`E2ECRMINVITE=1`, `E2ECRMINVITEE`) an assistant | Owner sees Content studio, CRM and TripPlanner in the app switcher; no "no active owner" banner; Tenant 360 › Members lists the owner `active` | manual (G1, G10) |
| 3. Import a brand guide (.docx), adopt tour X and two more tours, Rewrite, export DOCX | Agency owner | Studio `/portal/brand`, `/portal/tours`, `/portal/tours/mine` | AA-Partner `e2e/playwright.portal.config.ts` projects `portal-setup` + `portal` (`BASE_URL`, `PORTAL_TARGET=fargate`, `E2EPORTALEMAIL`, `E2EPORTALPASSWORD`, `E2EPORTALTOTP`): `aa1040-export-marks.spec.ts` (AI mark on exports), `s268-studio-price-vi.spec.ts` (marketplace price). No spec for brand import or Rewrite | Brand rules +1; tour cards with photo and price; usage meter +1; DOCX carries `X-AI-Generated` and the AI mark in its properties | manual (G3) |
| 4. Refresh topics (time it), pick an angle, write one blog and one LinkedIn post, edit in the viewer; release a held piece | Agency owner; A10b for the release | Studio `/portal/create`, `/portal/content`; CIS **Tenant content QA › Compliance** | Release: AA-CIS-App `tests/e2e/admin-evidence/compliance-release.spec.ts` (`E2EADMIN=1`, `FLAG_SYNTHETIC`, `FLAG_REAL`, `E2E_DRY_RUN`) and the flag seeder `python -m services.tenant_account.e2e_fixtures subject-gate-flag --tenant <tenant-id> --run <run>` (ECS exec on `aa-cis-dev-api`, DRY RUN first). No spec for topics, angle or writing | Every adopted tour has a topic or a stated reason; slate time recorded; the viewer shows no writer brief and no search context; the held piece released by A10b with a `content_compliance.released` audit row | manual (G3); release automated |
| 4b. Publish the blog to WordPress (with a link to `/pilot-rehearsal-01/plan?tour=<X>`), take it down, publish again; post and remove on the Facebook test Page | Agency owner | Studio `/portal/account/integrations`, `/portal/content/publish` (`POST /v1/publish-log/<piece-id>/publish`, put-back, move-to-draft) | None committed (the S276 drill used API calls) | Live post with the AI mark; publishing again makes no duplicate; Facebook post and removal both logged in the publish log | manual (G4) |
| 5. Open the agency's planner, search "Laos", add tour X, reorder at 390 px, chat three turns | Traveller | `tripplanner.lumiguides.it.com/pilot-rehearsal-01/plan` | AA-TripPlanner-Web `e2e/visual/planner.spec.ts` (`-c planner.config.ts`, every API call mocked) and `visual.spec.ts` (projects `1440`, `390`): not a live tenant run | Tenant colours; the list holds only the tenant's adopted tours (needs this wave's TripPlanner change: the AA catalogue keyed on the AA-hosted tenant, not on `kind` demo); search by embedding; `shared.llm_call_log` rows carry the tenant id | manual (G5, G13) |
| 6. Send to the agency (consent ticked), click twice | Traveller, then agency owner | TripPlanner `POST /trip/<trip-id>/send-to-advisor`; CRM `/pipeline` | None | 200 once; one lead in the CRM pipeline within about a minute (`crm_tp_lead_pull`); not visible to the audit tenants; the TripPlanner outbox row redacted (`tripplanner.outbox.redacted_at`); one hand-off for the double click | manual (G5) |
| 6b. The other lead channels: webhook and e-mail | Orchestrator | Tenant 360 lead route (`PUT /admin/tenants/<tenant-id>/tripplanner-site/lead-route`), only for a tenant without the CRM add-on | None | Signature valid; Reply-To is the traveller | gap (G14) |
| 7. Quote: an AA line for tour X, own services, inclusions and exclusions; a discount above the limit | Agency owner / agent | CRM `/pipeline/<trip-id>`, proposal builder | AA-Partner `e2e/tests/aa-lines.spec.ts`, `proposal-builder.spec.ts` (`e2e/playwright.config.ts`, `E2ECRM=1`, `E2ECRMCLIENT`, `E2ECRMPARTNER`, `E2ECRMFORMKEY`, `E2ECRMEMAIL`, `E2ECRMPASSWORD`, `E2ECRMTOTP`, `E2ECRMAATOUR`), on the CRM E2E agencies today | The AA price equals the Booking quote for the agency's tier; the discount opens an approval task for the owner | automated on the CRM E2E agencies (G1); discount manual (G15) |
| 8. The client accepts, pays the deposit ("I've paid"), AA confirms | Traveller; agency owner; A10e staff | `go-dev.lumiguides.it.com/c/p`; CRM `/aa-bookings`; Booking B2B desk | AA-Partner `client-proposal.spec.ts`, `lifecycle-thin.spec.ts` (same env); AA-Booking `frontend/e2e/e2e-writers/writes.spec.ts` test 1, project `e2e-writers` (`BOOKING_E2E_WRITERS=1`, `BOOKING_E2E_FIXTURES`, `SYNTHETIC_SUPPLIER_BOOKING`); reads: project `signed-in` (`departure-board.spec.ts`, `agency-ops.spec.ts`) | Trip booked; a B2B case; seats +N on the departure; manifest matches; CRM `/aa-bookings` shows confirmed. VNPay runs as the stub only | automated (G1 for this tenant) |
| 9. Supplier booking, confirmation, voucher, purchase order, supplier bill | A10e staff | Booking `/cases/<code>`, `/finance` | `writes.spec.ts` test 1 (request and confirm) | Voucher without client name or price and with the right end date; a cost line against the revenue in USD | supplier booking automated; voucher, PO, bill gap (G6) |
| 10. Traveller portal: code sign-in, passport and flight, e-sign, itinerary and voucher; send to AA ops | Traveller; A10c reads the ops view | `go-dev.lumiguides.it.com/c/t`; CRM staff console `/staff` | `lifecycle-thin.spec.ts` (portal link, code sign-in, stage 3 lock, e-sign envelope) | The itinerary matches tour X; the ops view shows the departure | automated (G1 for this tenant) |
| 11. AA agency invoice (AAT), payment by maker, approval by checker, overdue blocks a hold (409) until paid | A10e maker and checker | Booking `/agency-billing`; CIS Tenant 360 › Booking billing (read) | `writes.spec.ts` tests 2-3 (`SYNTHETIC_AGENCY_INVOICE`, `PAYMENT_AMOUNT`); invoice from the seeder `python -m app.e2e_fixtures --apply --run <run> --agency-tenant <tenant-id>` (ECS exec on `aa-booking-dev-api`, DRY RUN first) | Payment recorded and approved by two identities, each the actor of its audit row; 409 on a hold while overdue, then open again | maker-checker automated; overdue gap (G7) |
| 12. Budget fail-closed in three apps (X1); then reset the budgets | Tech lead; agency owner; traveller | Tenant 360 › Subscription override; CRM **Settings › AI**; studio and planner | None live (`planner.spec.ts` mocks the paused chat) | See [X1](#x1-ai-budget-fails-closed-in-three-apps) | manual (G8) |
| 12b. Leave pilot mode on the marker tenant | Tech lead | Tenant 360 › Subscription › **End pilot** or `POST /admin/tenants/<tenant-id>/pilot/end` (reason required), as in [onboarding Step 8](pilot-agency-onboarding.md#step-8-leave-pilot-mode); then [Teardown](#teardown) | None | `changed` true and one `tenant.pilot_ended` audit row; `SELECT slug FROM shared.tenants WHERE is_pilot` returns no row; Dev pilot slot free; the CRM marker false after one `crm_entitlement_pull` | manual (G2 closed) |

The tour retirement (X2) and the AA-cancelled departure (X3) run after step 12, so they cannot break the main chain.

## Cross-app checks

### X1: AI budget fails closed in three apps

1. Tech lead: on Tenant 360 › Subscription, override `ai.budget_usd_monthly` for `pilot-rehearsal-01` to 0.05 USD
   with a reason and an expiry (`PUT /admin/tenants/<tenant-id>/entitlement-overrides/ai.budget_usd_monthly`). A10b
   may not do this.
2. Content studio: Rewrite a tour. Expected: refused before any model call (`shared.cost_guard`), one refused row
   in `shared.llm_call_log`.
3. TripPlanner: send one chat turn on `/pilot-rehearsal-01/plan`. Expected: the per-tenant refusal
   `tenant_budget_cap` (AA-TripPlanner-Web `backend/shared/tenant_budget.py`; the narration answer carries
   `ai_budget_exhausted`); search falls back to keyword ranking. `cap_reached` or `spend_unreadable` is the app-wide
   gateway cap (`backend/aa_llm/budget.py`), not the tenant budget: record it as a **FAIL** of X1, not a PASS.
4. CRM: the owner sets **Settings › AI** budget to 0 and asks for a draft. Expected: `budget_exhausted`, no model
   call. The CRM has its own pot (`crm.tenant_settings.ai_budget_usd`, ledger `crm.llm_call`); the CIS override does
   not reach it (onboarding gap G12).
5. Remove the override and restore the CRM budget. Expected: the three surfaces work again.

### X2: tour retirement

Retiring a tour on Dev hides it for every Dev tenant, so X2 runs last and restores at once. It changes shared Dev
state: `tour_retirement_fanout` (AA-CIS-App `services/tour_lifecycle/fanout.py`) flags every live post about the tour
for every tenant, sends `tour_notice_email` mails to every tenant holding a derivative, and schedules
`retired_page_draft` for agencies that opted into the automatic move to draft; Booking notifies staff on every open
trip case; the restore then mails a "back on sale" notice. So it starts with a read-only blast-radius check.

0. **Pre-check (read only, abort on any doubt):**
   - CIS dry run: `GET /admin/tours/<tour-id>/lifecycle-preview?action=trash_master` (the confirm dialog's dry run,
     rolled back). Expected `allowed` true; note `derivatives` (tenants, live posts) and `notifies_tenants`.
   - The tenants behind those counts, through [ECS exec and S3](ecs-exec-s3-mediated.md) on `aa-cis-dev-api`
     (container role `cis_app`, which reads these RLS tables): run `services.tour_lifecycle.derivatives.tenant_derivatives`
     with the key's tour ids, then for those ids:

     ```sql
     SELECT t.slug, t.kind, t.is_canary, t.is_pilot, coalesce(p.auto_draft, false) AS auto_draft
       FROM shared.tenants t
       LEFT JOIN acp_shared.tour_retirement_policy p ON p.tenant_id = t.tenant_id
      WHERE t.tenant_id = ANY($1::uuid[]);
     ```

   - Booking: the open trip cases and active holds on X, read-only through ECS exec (local mode) on
     `aa-booking-dev-api` with the queries the pull itself uses (AA-Booking `backend/app/catalog/lifecycle.py`,
     `AFFECTED_CASES_SQL` and `PLAN_SQL`, with X's source id).
   - **Abort unless** every tenant listed is synthetic (`is_canary` true, `is_pilot` false), none is the pilot or the
     marker tenant, and every open Booking case and hold on X is a synthetic fixture. Pick X' instead if X fails.
   - The restore (step 4) must finish before the earliest `draft_due_at` (event time + the notice period, default
     7 days), so no opted-in WordPress page is moved to draft. Plan X2 for one sitting.
1. Tech lead: trash tour X's Master in the CIS admin (`PATCH /admin/master/<tour-id>/trash`), then wait for
   `tour_retirement_fanout`.
2. Expected: the agency gets the `tour.discontinued` notice; Booking (`bk_tour_lifecycle_pull`) notifies staff per
   open trip case and refuses new quotes and holds (409 `tour_not_served`); the TripPlanner trip lists the stop as
   unavailable.
3. The CRM has no handler yet (AA-1093): record that the trip with tour X is **not** flagged.
4. Restore, in two calls. `PATCH /admin/master/<tour-id>/restore` takes the Master out of the trash but leaves it
   `inactive` (paused): the tour is still not served. Then `PATCH /admin/master/<tour-id>/activate`. A 409
   `source_not_live` means restore the source tour first; a 409 for the elephant-riding policy means the Review Queue
   approve. Expected only **after the activate**: `tour.reinstated` notices, `gold_aa_internal.v_tour_liveness` shows
   the key served (Master `active`), Booking quotes and holds on X answer again and the planner lists the stop.

Status: manual; CRM part is a gap owned by AA-1093.

### X3: AA cancels a departure the agency holds (crm-13)

Proven live on 2026-11-13 on the CRM's E2E agency (evidence in the S279 session folder, `verify/aa1087-crm13/`):

1. AA-Booking seeder `python -m app.e2e_fixtures --apply --run <run>` (ECS exec, DRY RUN first): a synthetic
   departure, the agency's booking on it, a pending supplier booking and an issued invoice. Save its JSON output.
2. AA-Partner `e2e/tests/aa-cancel.spec.ts` with `E2ECRM=1`, `E2ECRMAACANCEL=prepare` and `E2ECRMAACANCELFIXTURES`
   set to that file: a CRM trip with the seeded tour as an AA item on the seeded departure.
3. AA-Booking `writes.spec.ts` test 4 (A10e-1, `SYNTHETIC_DEPARTURE`): the staff address cancels the departure.
4. `aa-cancel.spec.ts` with `E2ECRMAACANCEL=verify`: within one `crm_booking_sync` minute the trip shows one active
   `crm.aa_cancel_case` and the board filter "AA cancelled" lists it.

Status: automated on the CRM E2E agency. On `pilot-rehearsal-01` it needs G1 and G11 (the spec accepts the CRM E2E
agency only).

## LLM spend cap

Cap 10 USD, estimate 2-4 USD (system audit S278, section 4). The infrastructure cost does not change.

| Stage | Calls | Estimate (USD) |
|---|---|---|
| T2 rewrite | 3 tours | 0.3-0.9 |
| T7 topic slate | 1-2 refreshes | 0.5-1.5 |
| T9 blog + LinkedIn + Facebook | 3 pieces | 1.0-1.5 |
| TripPlanner chat | 3 turns | 0.03-0.07 |
| Narration and embeddings | a few | < 0.05 |
| CRM AI draft | 1 | < 0.01 (0 on the stub model) |
| Budget probes (X1) | refused | <= 0.05 |

- **Stop rule:** read the running total after steps 3, 4 and 5: every CIS ledger row of the window, shadow rows
  included, plus the CRM's `crm.llm_call` of the tenant. Above 6 USD, stop and ask the tech lead; never pass 10 USD.
- **Report per stage** from the CIS ledger (read through [ECS exec and S3](ecs-exec-s3-mediated.md), container
  role `cis_app`):

  ```sql
  SELECT coalesce(app, quality_signal->>'app', 'cis') AS app, stage, status,
         coalesce(is_shadow, quality_signal @> '{"shadow": true}') AS shadow,
         count(*) AS calls, round(sum(coalesce(cost_usd, 0)), 4) AS usd
    FROM shared.llm_call_log
   WHERE tenant_id = '<tenant-id>'::uuid AND created_at >= '<run-start>'::timestamptz
   GROUP BY 1, 2, 3, 4 ORDER BY usd DESC;
  ```

  `<tenant-id>` is the id of `pilot-rehearsal-01`; `<run-start>` is the time step 1 began. Report the rows of the same
  window without a tenant id as one "untagged" line (step 0 made sure no other paid run shares the window). Shadow
  rows are billed A/B calls (CIS migration 319): they count toward the cap and the stop rule. Rows written before 319
  have `app` and `is_shadow` NULL, hence the `coalesce` from `quality_signal`. The CRM's draft spend is on
  **Settings › AI** (ledger `crm.llm_call`, `cost_usd_est`) and is added to the total.

## Teardown

Run after X3, in this order. Each write below is the tech lead's; the evidence folder records each result.

1. **Marker tenant out of pilot mode (step 12b).** Tenant 360 › Subscription › **End pilot** (or the route) as in
   [onboarding Step 8](pilot-agency-onboarding.md#step-8-leave-pilot-mode). Then step 12b's check.
2. **Marker tenant removed.** `pilot-rehearsal-01-marker` is `kind` agency with `is_canary` false: a non-synthetic
   tenant that root ADR 0019 d16 does not allow on Dev once it is no longer the pilot. Soft offboard it (`POST
   /admin/tenants/<tenant-id>/offboard`, reason "pilot rehearsal teardown"), then erase it with the `data_erasure` job:
   `POST /admin/job-runner/erasure/run` with `subject` tenant (DRY RUN by default), the tech lead approves the DRY RUN
   fingerprint, then the apply ([DSAR erasure runbook](../../legal/dsar-erasure-runbook.md)). The apply refuses a tenant
   offboarded less than `ERASURE_TENANT_RETENTION_DAYS` ago; until then the offboarded marker stays, and the README
   names the date of the apply.
3. **`pilot-rehearsal-01` is kept** as a synthetic fixture (`kind` demo, `is_canary` true) for the next rehearsal and
   for G1, with its CRM agency and E2E members. Its budget override (X1) is removed and its CRM AI budget restored. If
   the tech lead decides otherwise, offboard it like the marker (CIS offboard, CRM **Settings › Data** leave) and list
   it in the README.
4. **Channel posts taken down.** Every WordPress post of step 4b is removed by the agency owner in the studio (**Remove
   post**, `DELETE /v1/publish-log/<publish-id>`), and the Facebook test Page post likewise; the publish log shows each
   as unpublished. If the free WordPress test site has expired, write that in the README.
5. **Booking fixtures.** The seeder rows of steps 8-11 and X3 are synthetic and stay, tagged by their run id; cancel any
   still-open synthetic hold so it does not block the next run.
6. **Final read:** step 0 checks 3 and 5 again (job tables idle, pilot slot free) and the spend total.

## Evidence

One folder, `docs/audits/<date>-S<nnn>-pilot-rehearsal/`, with a README table: step, PASS or FAIL, evidence file, and
for each FAIL the issue that fixes it. Screenshots at 1440 and 390 px, light and dark, with assertions and zero console
errors. The root repo is public: no account ID, e-mail address, tenant personal data, tour or piece text; name records
by the first 8 hex characters of their id.

## Gaps

Each gap below is a step that needs a new spec, script or rule. G2, G2a, G9, G12 and G13 are in the
[onboarding runbook](pilot-agency-onboarding.md#gaps).

| ID | Step | Repo | Proposal |
|---|---|---|---|
| G1 | 1, 2, 7-11 | AA-CIS-App, AA-Partner, AA-CIS-Infra | **Closed (AA-1086, S279)**, see [Fixtures](#fixtures). A rehearsal fixture: CIS `e2e_fixtures rehearsal-tenant` enqueues the saga (`demo`, both add-ons, DRY RUN first) and the CRM seed gets a `pilot-rehearsal-01` agency under that id with owner and agent members whose E2E users (`crm_e2e_users.json`, `crm_dev_identity.py e2e-users --write-secrets`) let every CRM and portal spec run on it |
| G3 | 3, 4 | AA-Partner | A studio rehearsal spec (portal project, opt-in): brand import from an invented .docx, adopt, Rewrite, DOCX export, topic refresh timing, angle, blog and LinkedIn, viewer edit; paid steps behind an explicit switch |
| G4 | 4b | AA-Partner | A publish spec: connect, publish, put back, move to draft on the WordPress test site (checks `/wp-json/` first) and post and remove on the Facebook test Page |
| G5 | 5, 6 | AA-TripPlanner-Web | A live tenant spec, headed (bot and WAF checks): theme, search, add tour X, reorder at 390 px, three chat turns, send to the agency with a double click, then the CRM pipeline read |
| G6 | 9 | AA-Booking (+ ADR 0006a amendment) | Widen A10e staff to voucher issue, purchase order send and supplier bill on synthetic agencies, with a `writes.spec.ts` test each |
| G7 | 11 | AA-Booking | A seeder option for an overdue synthetic invoice and a test that a hold is 409 until the payment is approved |
| G8 | 12 | AA-CIS-App (+ ADR 0006a amendment), AA-TripPlanner-Web, AA-Partner | One opt-in script or spec for X1: either an A10b amendment for the `ai.budget_usd_monthly` override on synthetic tenants, or the tech lead's step, then the three refusals read back from both ledgers |
| G10 | 2 | AA-CIS-Infra, AA-Partner | Only if G1 is not taken: an owner recipient in `studio_invitees` and a phase 2 owner mode that stores the new password and authenticator secret in Secrets Manager |
| G11 | X3 | AA-Partner | Let `aa-cancel.spec.ts` accept a seeder run for another synthetic agency (today it requires the CRM E2E agency) |
| G14 | 6b | AA-TripPlanner-Web | A script that sends one lead through the webhook and the e-mail channel of a tenant without the CRM add-on and checks the signature and Reply-To |
| G15 | 7 | AA-Partner | A test that a discount above the agent's limit opens the owner's approval task |
| - | X2 | AA-Partner, all | The CRM handler for `tour.discontinued`: AA-1093 |
