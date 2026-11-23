---
id: OPS-08-s288-aa1158-live-evidence
title: "S288 live evidence: AA-1158 part 1, approval rules for a three-person team (Booking bk-064, #300)"
description: "Agent-run live checks on Dev for AA-1158 part 1 with the Dev-only E2E identities, 23/11/2026; owner-only and payout paths listed for CI, the DB probe or the tech lead."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-23
review_every_days: 30
related: [AA-1158, AA-1155]
---

# S288 live evidence: AA-1158 part 1 (23/11/2026, about 13:30 +07)

## What is deployed

| Check | Result | Record |
|---|---|---|
| Booking API `/booking/health` | 200, `git_sha` `19f2fcf1` = squash merge of Booking #300 (top of `main`; #299 bk-064 `cf13013d` is under it) | curl |
| Booking API `/booking/health/ready` | 200, `schema_version` `bk-064`, `bk-064` in `registered_keys`, db ok | curl |
| ECS `aa-booking-dev-api` | one PRIMARY deployment, rollout COMPLETED, 1/1 running | `aws ecs describe-services` |
| ECS `aa-booking-dev-admin` (staff web) | one PRIMARY deployment, rollout COMPLETED, 1/1 running | same |
| CI on `19f2fcf1` | CI, Visual, Deploy Dev, Deploy Admin Dev, Secret Scan, Spec trace: success | `gh run list --commit` |
| Schema reference | root `db-schema-reference.md` on `master` says "Booking **bk-064**" (bot PRs #949 / #951 merged); `booking.suppliers` has `activated_by`, `activated_at`, `owner_self_approved`, `writers`; `booking.billing_entity_change` exists | root `master` |

## How the live checks ran

Headless Chromium (Playwright), one browser, against `https://booking.lumiguides.it.com` (staff web, BFF `/api/booking/*`
to the Booking API). Spec: `.tmp-session/S288/live/aa1158/aa1158-live.spec.ts` (scratch, not committed). Sign-in codes
were read from the e2e mailbox at run time and never written down; no screenshot of the managed-login host; every
screenshot masks @-addresses and the account chip. Raw answers: `results.json` (no keys, no e-mail addresses).

Identities (root ADR 0006a, Dev only):
- **A10a** read-only Booking admin (`booking-admin`, every write 403 `e2e_read_only`);
- **A10g** custom-role maker (`booking-custom`, role "Product, ops & accounting", the content+ops custom role);
- **A10e-2** pricing maker (A10d CIS address) and pricing checker (`booking-contracting`).

Writes made, all on records the run created (names start with `SYNTHETIC`), all cleaned up: the custom maker created
one synthetic supplier and deactivated it (audit `supplier.created` then `supplier.withdrawn`). An earlier attempt of the
same spec stopped at a sign-in and ran this create + deactivate twice more, also cleaned up (3 withdrawn synthetic
suppliers in total, status `inactive`). The pricing checker sent one activate that the E2E guard refused before the
route (no change). No price, contract, payout or billing write went through.

## Done-when of AA-1158, line by line

| # | Done-when | Result | Evidence |
|---|---|---|---|
| 1a | bk- migration of part 1 applied on Dev, schema-reference PR merged | **PASS** | `/health/ready` bk-064; schema reference bk-064 on `master` |
| 1b | Second bk- migration (part 2) applied; Terraform KMS key, policy only the Booking task role | **NOT CHECKED** | Part 2 is S289 by scope; nothing to check yet |
| 2a | A supplier created by the content+ops role stays `pending` | **PASS** | Custom maker `POST /suppliers` → 201, `status: pending`, `writers` = [creator], `activated_by` null, `owner_self_approved` false; `GET` detail same; `actions.activate = {allowed: false, blockers: [needs_supplier_activate]}`. UI: list filter "Pending approval" with the badge, detail banner "This supplier waits for approval: a second person activates it before contracts can be added." (`suppliers-pending-*.png`, `supplier-detail-pending-*.png`) |
| 2b | Activation by its creator is refused | **PASS (live, 403 `forbidden`)** | Custom maker `POST /suppliers/{id}/activate` → 403 `forbidden` (its role holds no `supplier.activate`; the A10g probe answers from the session's capabilities, log `booking_e2e_probe_refused needs=supplier.activate`). The `maker_checker` 403 for a creator who *does* hold `supplier.activate` was not reachable live: the only E2E identity allowed to activate (pricing checker) may touch only the pricing maker's suppliers, and the pricing maker cannot sign in (F1). That branch is proven in CI (`test_aa1158_approval_rules_api.py`) |
| 2c | Activation by the business owner works | **NOT CHECKED** | Needs the real business owner's session (hand step H1). E2E identities never self-approve by design (`GET /staff/me/self-approval` as the E2E admin → `{is_business_owner: false, approve: false, payout: false}`) |
| 2d | A second person activates (checker can activate a synthetic supplier) | **NOT CHECKED (blocked by F1)** | The pricing checker signs in (role `contracting`, holds `supplier.activate`, `contract.publish`). Its activate of the custom maker's supplier → 403 `e2e_synthetic_only`, the supplier stayed `pending`: the guard works, but the allowed path needs a supplier created by the pricing maker, who is refused at sign-in (F1) |
| 3 | The business owner creates and activates a supplier: `owner_self_approved = true` | **NOT CHECKED** | Hand step H1 |
| 4 | The tech lead approving his own supplier, contract or bill is refused at the API (4xx) and the DB | **NOT CHECKED live** | E2E identities cannot act as the tech lead. CI: `test_aa1158_approval_rules_api.py`, `test_bk064_schema.py`. DB: the rolled-back probe of live step 4 (orchestrator, DB Migrate `run-script`); catalog objects are counted by the aggregate script below |
| 4b | Contract publish follows the writer list (maker publishing its own draft → 403 `maker_checker`, checker publishes) | **NOT CHECKED (blocked by F1)** | Needs the pricing maker's synthetic supplier, hotel and rate sheet. CI only |
| 5 | The bill approver recording the payout is refused, except the business owner (flagged) | **NOT CHECKED live** | No E2E identity holds `payout.write`. CI only; aggregate script counts `same_approver_payer` rows |
| 6 | A `payment_instructions` change stays pending until approved; invoices keep the old details | **NOT CHECKED (write); read side PASS** | `GET /billing-entities` → 200, each entity carries `pending_change` (none pending). UI Settings tab shows "Change payment details" on the entity row (`agency-billing-settings-*.png`). A change request as the E2E admin → 403 `e2e_read_only` (expected). The pending → approve flow needs a real finance/admin session (hand step H2) or CI |
| 7 | Setting `sellable = true` on a tour with no approved price is refused | **NOT CHECKED (blocked by F1)** | The planned live probe (pricing maker, workbench `make_sellable` on an unpriced synthetic plan → `skipped no_approved_price`) needs the pricing maker. CI only |
| 8 | Bank account pending + 24 h payout lock + ciphertext + masking | **NOT CHECKED** | Part 2 (S289) |
| 9 | The owner's dashboard shows the self-approval filter | **PASS** | `GET /audit-logs?owner_self_approved=true` → 200, 0 items (none yet). Audit log tab "Business-owner self-approvals" selected by the URL (`audit-log-self-approvals-*.png`, 4 variants). Dashboard My work tile "Business-owner self-approvals — None this month" (filter `owner_self_approved=true`, `from` 1st of the month), plus "Suppliers to activate" and "Billing changes to approve" tiles (`home-my-work-*.png`). Seen as the E2E admin, an `audit.read` holder: the tile is shown to every `audit.read` holder by design |
| 10 | Deploys reach rollout COMPLETED, `/booking/health` 200 | **PASS** | See "What is deployed" |

Other checks from the lane's live steps:

| Check | Result | Evidence |
|---|---|---|
| Policy switches `owner_self_approval_allowed`, `owner_payout_after_approval_allowed` | **PASS** | `GET /pricing/policy`: both in group `security`, version 1 in force, value `true` |
| `GET /staff/me/self-approval` (E2E admin) | **PASS** | `{is_business_owner: false, approve: false, payout: false}` |
| UI pages: console errors / failing requests / sideways scroll | **PASS** | 0 console errors, 0 failing requests, no horizontal overflow (document and `main`) on every page and width captured |
| Booking `post-deploy-verify.yml` | **NOT CHECKED** | Manual workflow, last run 01/11; dispatch is the orchestrator's step |
| Pricing E2E A10e-2/3 green with the reordered steps | **NOT CHECKED (blocked by F1)** | |

## Findings

- **F1 (blocks the pricing E2E, not a code defect of #300):** the A10e-2 pricing maker (A10d CIS address) is refused at
  Booking sign-in: API log `booking_e2e_writer_refused identity=pricing_maker reason=groups`, staff web
  `Booking refused the sign-in (e2e_scope)`. Its WORKFORCE groups are now only `cis-customer_success`; the Booking guard
  requires exactly `cis-customer_success` + `booking-contracting`. Booking groups are mirrored from the CIS staff grant,
  so its Booking grant (contracting) is gone. Effect: the A10e-2/3 pricing E2E cannot run, and with it the live proof
  of checker activation, the contract writers rule and the sellable gate. Fix: restore the Booking `contracting` grant of
  that E2E user (CIS Staff page, or the A10e runbook grant step), then re-run this spec.
- **Observation:** the custom maker's `/staff/me` lists no `supplier.*` permission names in `permissions`, yet its
  supplier create is allowed (the role's capabilities may be answered under another field). Display only; not checked
  further.

## Needs the tech lead (hand steps)

- **H1 — business-owner self-approval (Done-when 2c, 3).** Precondition: the business-owner marker is set on the
  business owner's account (CIS → Platform → Staff, owner session; the aggregate script reports how many accounts carry
  it). Then, signed in as the business owner on `https://booking.lumiguides.it.com/suppliers`: Add supplier, name
  `SYNTHETIC owner check`, category Hotel → the row shows "Pending approval" → open it → Activate. Expect: status Active,
  and on `https://booking.lumiguides.it.com/audit-log?owner_self_approved=true` one row "supplier activated" by her.
  Screenshot: the supplier header after activation and that audit row. Then Deactivate the supplier.
  Same session, tech lead variant: the tech lead creates `SYNTHETIC lead check` and presses Activate → expect a refusal
  "a supplier is activated by a second person" (403 `maker_checker`); screenshot the message; then deactivate it.
- **H2 — payment details change (Done-when 6).** On `https://booking.lumiguides.it.com/agency-billing?tab=settings`, the
  `DEVCHECK1037` row → "Change payment details", any test text, reason "S288 live check of the pending change flow" →
  expect a "Change pending" pill and the invoices still printing the old text; a second person (or the business owner,
  flagged) approves or the requester withdraws it. Screenshot the pending pill and the decision.

## DB aggregates (orchestrator)

Script `.tmp-session/S288/live/aa1158_db_aggregates.py` (read-only transaction, counts and catalog names only; passes
`pilot_pii_guard.py --check`). Run in the Booking container (role `booking`):

```
ECSX_SERVICE=aa-booking-dev-api tools/ecs/ecsx.sh .tmp-session/S288/live/aa1158_db_aggregates.py
```

It reports: business-owner / owner marker counts in `shared.v_staff_booking_grant`; suppliers by status with
`activated_by`, `owner_self_approved`, `writers`, synthetic counts; the two policy switches; contracts by status with
writers / flag; `same_approver_payer` payouts; `billing_entity_change` by status; audit rows flagged
`owner_self_approved` / `same_approver_payer` and supplier actions of the last 2 days; sellable plans without a valid
price row; the bk-064 constraints (7 names) and triggers (`%owner_self_approval` expected 10, `suppliers_writers`,
`suppliers_activation_guard`, `billing_entity_change_guard`). Expected now: 0 business-owner self-approval rows,
suppliers `pending` 0 (the run's synthetic ones are `inactive`), switches version 1 = true.

The rolled-back DB probe of the lane's live step 4 (CHECK / trigger refusals with the tech lead's and the owner's keys)
is a DB Migrate `run-script` as master, not part of this read-only script.
