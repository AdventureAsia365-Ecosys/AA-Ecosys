# S290 close-outs, section 4: AA-1149 and AA-1176 live check on Dev (plus AA-1158 probes on the way)

- When: 2026-11-24, 06:19–06:33 UTC (13:19–13:33 +07). The run was made by an agent with headless Playwright (Node,
  `tools/uat`) through the Booking admin BFF `https://booking.lumiguides.it.com/api/booking/*`. The plan and scripts are
  `.tmp-session/S290/closeouts/` (README §4), files `40_supply.cjs` and `50_tour.cjs`.
- Sessions: the orchestrator signed each identity in (Cognito e-mail code from S3 `inbound-admin/`, MFA admin profile)
  and saved the state files. This run reused them, so no code, secret or sign-in host was seen. Identities (root ADR
  0006a):
  - pricing maker `e2e-cis-cs@` (A10e-2..5; tech lead decision D1, group `booking-contracting` added 13:18, removed at
    cleanup);
  - pricing checker (A10e-2/3);
  - E2E owner (A10h, Booking `admin`, never the business owner).
- Tech lead decisions (24/11):
  - D0: the "synthetic tour" is an untouched catalogue key that no real agency ever used (the A10e-2 rule), with
    SYNTHETIC commercial rows and a full restore.
  - D1: yes.
- The plan: CIS key `cbfc127e-28bb-413a-9eca-1e39015aa275`, "Chiang Mai to Chiang Rai Mountain Cycling — 5 Days"
  (Thailand). Booking plan `9aa0edf9-…`. The CIS route has nights 2 and 3 in two places (Chiang Dao, Ban Thaton).
  `10_bk_facts.py MODE=pick` chose it. Before the run it was not sellable, with no component, price, version,
  departure, exception or note. Vietnam has only one catalogue tour (14 days).
- Synthetic agency: "E2E Pilot Rehearsal Travel" (`pilot-rehearsal-01`, synthetic in CIS).
- Masking: no e-mail address appears in any file here. The nets on screen (30 / 50 / 80 USD) are the invented rates of
  the SYNTHETIC S290 rate sheets, not a real supplier's.

## Synthetic records created

| Kind | Code / id | State now |
|---|---|---|
| Hotel DMC | `SUP-000018` "SYNTHETIC S290 AA-1149 hotel DMC (live check, not real)", TH | active |
| Ground DMC | `SUP-000019` "SYNTHETIC S290 AA-1149 ground DMC (live check, not real)", TH | active |
| Hotels | `HTL-000008` hotel A (Chiang Dao) and `HTL-000009` hotel B (Ban Thaton), each with room type Double/2 | active |
| Services | `SVC-000018` private transfer, `SVC-000019` English guide (unit group) | active |
| Contracts | one per DMC: USD, 2026-11-24 → 2027-06-30. Room BB 80 per night, transfer 30, guide 50 | published |
| Plan | commercial note "SYNTHETIC S290 live check plan …", sellable, 10 components | restored to full, priced |
| Desk booking A | `SYNTHETIC-S290-1149-A`, 2 adults, 2027-01-23 → trip case **TC-000040** (confirmed; tour line accepted by the desk) | 10 supplier bookings `To request` |
| Desk booking B | `SYNTHETIC-S290-1149-B` (sold under the exception) → trip case **TC-000041** | confirmed |
| Sale exception | N1 `N1:night:2`, 14 days (until 2026-12-08) | revoked |

The 4 new hotels and services each queued one CIS supply-content draft (about 0.003 USD each, the S289 measure).

## Steps and results (`.tmp-session/S290/closeouts/work/results.log`: 108 PASS, 1 FAIL, explained in step 15)

| # | Step (identity) | Request → status | Result | Evidence |
|---|---|---|---|---|
| 4.2 | Two suppliers (maker) | 2 × `POST /suppliers` → 201 | `SUP-000018`, `SUP-000019`, both **pending** (AA-1158 R5) | `40-suppliers.json` |
| 4.3 | Activate (checker) | 2 × `POST /suppliers/{code}/activate` → 200 | active (second person) | log |
| 4.4 | Hotels, room types, services (maker) | 2 × `POST /hotels`, 2 × room types, 2 × `POST /services` → 201 | HTL-000008/9, SVC-000018/19 | `41-records.json` |
| 4.6 | Rate sheets (maker) | DRY RUN 200 (2 rates, no check), import 200 → draft. Then the maker's own `PATCH /contracts/{id} {status: published}` → **403 `maker_checker`** "a contract is published by someone who wrote none of its terms" | **AA-1158: a contract writer cannot publish**: pass ×2 | `42-ratesheet-hotel.json`, `42-ratesheet-ground.json` |
| 4.7 | Publish (checker) | `PATCH /contracts/{id}` → 200 ×2 | published, second person | `43-contract-*.json`, `43-contract-*-published__1440__light.png` |
| 4.8 | Sellable probe (owner) | `PUT /catalog/trip-plans/{key}/commercial {sellable:true}` on the untouched plan → **409 `no_approved_price`** "approve a price version or let the cost sheet price the tour before selling it". Then `{sellable:false, note}` → 200 | **AA-1158 Q9: pass** | `50-sellable-probe.json` |
| 4.9 | Components (owner) | `PUT …/components` (10 items) → 200 | rooms days 1–4 (A, A, B, B), transfers days 1–5, guide day 1 | log |
| 4.10 | Price + can-operate (owner) | `POST …/prices/recompute` → 200 changed; `GET …/prices` | computed b2b and fixed-departure rows on the v2 bands 1, 2, 3, 4, 5–7, 8–10, 11+; operability **warnings** (only `N5:guide`) | `50-price-bands.json`, `50-operability-full.json` |
| 4.11 | Sellable (owner) | `PUT …/commercial {sellable:true}` → 200 | price-ready plan is sellable | log |
| 4.12 | Desk booking A (owner) | `POST /b2b-desk/entries` → 201 | **booked, TC-000040** | `50-desk-A.json` |
| 4.13 | Desk accepts the on-request tour line (owner) | `POST /b2b-desk/on-request/{hold}/lines/tour/accept` → 200 | line confirmed (Generate books only confirmed lines) | log |
| 4.14 | Generate (owner) | `POST /trip-cases/TC-000040/supplier-bookings/generate` → 200 | **created 10**: SUP-000018 ×4 (hotel nights), SUP-000019 ×6 (5 transfers + 1 guide); supply `items_to_book 10`, `live 10` | `50-generate-A.json`, `50-case-A-suppliers-*` |
| 4.15 | Edit the tour, Generate again (owner) | `PUT …/components` without the day-2 room → 200; Generate → 200 | **created 0; the 10 bookings unchanged** (same ids, suppliers, dates, parts); operability **blocked `N1:night:2`** | `50-operability-edited.json` |
| 4.16 | Sale to an agency while blocked (owner) | `POST /b2b-desk/entries` (B) → **422 `invalid`** "line tour: this tour cannot be sold to agencies yet: night 2 has no hotel (N1)" | **the B2B sale is blocked: pass** | `results.log` (the 422 file was overwritten by step 4.17's 201) |
| 4.17 | **AA-1176:** sale exception (owner) | `POST …/sell-exception {rules:[N1], reason (≥ 20 chars), days:14}` → 200 | status **exception** (N1 covered, until 2026-12-08). Desk booking B → **201 booked, TC-000041** | `50-operability-exception.json`, `50-desk-B.json`, `50-readiness-exception__{1440,390}__{light,dark}.png` |
| 4.18 | **AA-1176:** revoke (owner) | `POST …/sell-exception/revoke` → 200 | status **blocked** again, no live exception | `50-operability-revoked.json` |
| 15 | Missing transfer only warns (owner) | `PUT …/components` with all 4 nights but no day-3 transfer → 200 | status **warnings**, `N4:day:3` warn (+ `N5:guide`) | `50-operability-no-transfer3.json` |
| 4.19 | Restore + screenshots (owner) | `PUT …/components` full → 200; recompute 200 | status warnings (N5 only) | `50-operability-restored.json`, `50-readiness-final__*`, `50-case-A-suppliers-final__*` |

**The one FAIL, a test design error, not a product defect.** The first edit removed the day-2 room and the day-3
transfer together. N4 compares two consecutive hotel nights (`operability._n4`: the hotel's destination on night n
and night n + 1), so with no hotel on night 2 it has nothing to compare. Step 15 then removed only the day-3 transfer,
with every night hotelled. The result was `N4:day:3` at level warn and status `warnings`, not `blocked`. The script now
keeps the two checks apart (`edit` = no day-2 room; `transfer` = no day-3 transfer).

## Result per Done-when

| Issue | Line | Result |
|---|---|---|
| AA-1149 | A 5-day tour (4 hotel nights, 5 transfers, 1 guide), confirmed, and Generate creates 10 bookings from the snapshot | **pass** (4.12–4.14) |
| AA-1149 | Editing the tour afterwards does not change them | **pass** (4.15) |
| AA-1149 | A tour missing the night-2 hotel is blocked for B2B; an admin exception with a reason unblocks it | **pass** (4.15–4.17) |
| AA-1149 | A missing transfer only warns | **pass** (step 15) |
| AA-1176 | The E2E owner creates a sale exception on a synthetic tour (reason, 14 days) and revokes it | **pass** (4.17, 4.18) |
| AA-1158 | A contract writer cannot publish its contract | **pass** (4.6) |
| AA-1158 | `sellable = true` with no approved price → 409 | **pass** (4.8) |
| — | DB aggregates (parts 10, bookings from parts 10, covered quote line on TC-000041) | **orchestrator ECS exec pending** (README 4.20) |

## Observations

1. **The Suppliers tab lists the 10 generated bookings as "extra item".** For example "SB-000021 · extra item",
   although they come from the sold tour's parts. The S288 note asked for a better label on the "Tour components"
   card. This looks like the same family: worth a UI follow-up.
2. **The desk entry left the tour line "on request".** Generate created nothing until the desk accepted the line.
   That matches the AA-1149 decision "an on-request line only after the desk accepted it". S289 saw the same for a room
   line.
3. Price readiness now counts 3 priced plans (the synthetic plan plus the 2 real ones). Cleanup puts it back to 2.

## Cleanup state (not done yet: README §9 after the remaining checks)

The plan is sellable and priced, with 10 components and the SYNTHETIC note. TC-000040 and TC-000041 are live. Both
contracts are published and the supply is active. The maker still holds `booking-contracting`. Sections 5 (AA-1175)
and 6 (AA-1158 payout) reuse this plan, case A and the ground DMC, so cleanup waits for them.

# Section 5: AA-1175 group-size bands (after the A10e-6 deploy, AA-Booking #319 `32a49292`)

- When: 2026-11-24, about 06:58–07:05 UTC. The E2E owner (A10h) proposed the changes; the pricing checker (A10e-6:
  policy decisions on `price_pax_bands` versions the E2E owner made) approved them. Script `60_policy.cjs`.

| # | Step (identity) | Request → status | Result | Evidence |
|---|---|---|---|---|
| 5.1 | Read (owner) | `GET /pricing/policy` → 200 | v2 in force: 1, 2, 3, 4, 5–7, 8–10, 11+ | `60-policy-read.json` |
| 5.2 | Propose v3 (owner) | `POST /pricing/policy {key price_pax_bands, value, effective_from today, reason, submit}` → 201 pending. The maker's own approve → **403 `own_row`** | pass | `60-propose-v3.json` |
| 5.3 | Approve v3 (checker) | `POST /pricing/policy/{id}/approve` → 200 | **v3 in force** (1, 2, 3, 4, 5–6, 7–10, 11+) | log |
| 5.4 | History + audit + bands (owner) | audit rows `pricing_policy.submitted` + `pricing_policy.approved`, maker ≠ approver; recompute of the synthetic plan → matrix b2b bands 1, 2, 3, 4, 5–6, 7–10, 11+; agency tariff (E2E Pilot Rehearsal Travel): **4 → 4–4, 6 → 5–6, 9 → 7–10** | pass | `60-policy-history.json`, `60-bands-v3.json`, `60-policy-v3__1440__light.png` |
| 5.5 | Propose the v2 values back (owner) | → 201 pending; own approve → 403 `own_row` | pass | `60-propose-restore.json` |
| 5.6 | Approve (checker) | → 200 | **v4 (= v2 values) in force** | log |
| 5.7 | History + bands on v2 (owner) | history v4 in force, v3/v2/v1 superseded, no version approved by its maker; both changes audited | pass (history); bands read: see below | `60-policy-history.json`, `60-policy-after-restore__1440__light.png` |
| 5.7 | Bands on v2 (owner) | recompute 200; matrix b2b 1, 2, 3, 4, 5–7, 8–10, 11+; tariff **4 → 4–4 (priced for 4), 6 → 5–7 (priced for 5), 9 → 8–10 (priced for 8)** | **AA-1175 Done-when: pass** | `60-bands-v2.json` |

# Section 7a: AA-1152 day add-ons reach the agency lead and the CRM quote

- When: 2026-11-24, 06:5x–07:43 UTC.
- Identities:
  - the pilot rehearsal agency's Content studio owner and CRM owner (partner pool; signed in by the orchestrator);
  - an anonymous traveller.
- Tech lead decision D4: one paid T2 rewrite, cap 0.50 USD. **Cost (shared.llm_call_log, read by the orchestrator): job `0a2d5f33` = 0.1481 USD** (t2_generate 2 calls 0.1471, judge 0.0006, flag_fix 0.0004), job succeeded.

| # | Step | Result | Evidence |
|---|---|---|---|
| 7.1 | The agency adopts "Ho Chi Minh Trail Cycling — Vietnam and Laos" (CIS `POST /v1/tours/pool/{id}/rewrite` through the studio BFF) | 200, one rewrite queued (version `72bcf3ef-…`, job `0a2d5f33-…`) | `80-adopt.json` |
| 7.2 | The rewrite finished `ai_generated`; the agency owner approved its own version (`PATCH …/versions/{id} {action: approve}` → 200) | pass (the first poll ran on an expired studio session: re-signed, re-run) | `80-adopt-wait.json` |
| 7.3 | Agency planner `/pilot-rehearsal-01/plan?tour=3fa33633…` | the HCMC day card lists the **5 SYNTHETIC S289 add-ons with the agency's rounded "From $X per person"** (45 / 50 / 60 / 65 / 75). The traveller ticks "street food walk" (`POST /api/trip/addons` 200). The lead is sent with a SYNTHETIC name and an example.invalid address → **200 `sent`, channel `crm`** | `80-agency-planner-addon-ticked__1440__light.webp`, `80-agency-planner-day-addons__{1440,390}__light.png`, `80-planner.json` |
| 7.4 | CRM (pilot owner) | The lead is a trip at stage Inquiry on the **Pipeline** ("Vietnam, 6 nights"). Its note reads **"Day 7 AA add-on: SYNTHETIC S289 Saigon street food walk (sv:7e2d6d62-7ed2-49b1-aee1-fe9c9d21d890)"**. In the proposal builder, the AA add-on is added on day 7 → **`POST /bff/proposals/:id/blocks/:id/aa-addons` 201**, on request, sell 90.00 USD for 2 (the agency's suggestion) | `80-crm-pipeline-lead__1440__light.png`, `80-crm-lead-sv-note__1440__light.png`, `80-crm-aa-addon-quoted__1440__light.png`, `80-crm.json` |

Notes:

- **An AA add-on needs an AA tour on the proposal** (CRM `aa_addon_needs_tour`).
  - The HCMC catalogue tour is not sellable in Booking, so it is not in the "AA inventory" picker.
  - The proposal therefore took the SYNTHETIC S290 Thai plan as its AA tour (day 1, `aa-options` 201, a live B2B quote with no hold).
  - The add-on is attached to that AA trip.
  - In the CRM, an add-on belongs to "the AA tour of the same day, else the proposal's first AA tour". So a Vietnamese add-on sits on a Thai trip here: a test artefact.
  - Follow-up idea: the add-on drawer could require the tour that the add-on's place is on.
- The add-on list needs the proposal's day-1 date. It was set to 20/12/2026, so day 7 = 26/12, inside the add-on contract.
- The CRM screen shows "AA price 32.47 USD per traveller" (the B2B price) to the agency owner. This is the designed "role that sees margins".
- The first CRM check looked in `/inbox` (unmatched mail only), and the script was fixed to read the Pipeline. That accounts for the logged FAIL.

# Section 7b: AA-1160 lead fallback (in progress)

Tech lead yes (24/11) for steps 1–4. The tenant is **E2E Lead Proof Travel** (`e2e-lead-proof`, synthetic, TripPlanner only
until now, no members).

| # | Step (identity) | Result | Evidence |
|---|---|---|---|
| 1 | Attach crm.core (E2E owner, CIS `POST /admin/tenants/{id}/provision`, mode attach) | 202, job queued. CRM onboarding **failed: `agency_create` 403 `missing_group`** (the E2E owner holds no `crm-platform-admin`). So the tenant holds crm.core with **no CRM agency**: lead route `crm_agency false` | `85-attach-crm-core.json` |
| 2 | Fallback route (E2E owner, `PUT …/tripplanner-site/lead-route`) | e-mail to an existing E2E mailbox recipient → 200 | `85-route.json`, `85-tenant360-lead-route__1440__light.png` |
| 3 | Traveller lead (anonymous, planner BFF: one free day, then send) | **200 `sent`, channel `email`**: the fallback route, not the CRM | `85-planner-lead-sent__1440__light.webp` |
| 4 | Studio invitation (E2E owner, `POST /admin/tenants/{id}/members/invitations`, owner) to the pilot rehearsal owner's E2E address | 201, delivery **sent** | `85-invite.json` |
| 5 | Accept the invitation (orchestrator, `tools/uat/accept-owner-invite.cjs --tenant-name "E2E Lead Proof Travel"`) | `owner_invite_accepted` (activated), `owner_membership_listed` | orchestrator log |
| 6 | Agency app (Content studio, that owner on E2E Lead Proof Travel) › Account › Trip planner | The studio opens on E2E Lead Proof Travel. `GET /api/studio/trip-planner/leads` → 200: **the lead is listed with channel `email`, status `delivered`**. The page shows "Where leads go · NOW: E-MAIL" and "Your CRM is not taking planner leads right now (not set up yet, or no longer active), so leads go to the route below" | `85-leads.json`, `85-agency-app-planner-leads__{1440,390}__light.png` |
| 7 | CRM pull reports no `skipped_agency` | **orchestrator** (CloudWatch) | — |

# Planner on locale vi (AA-1160)

The pilot owner set `pilot-rehearsal-01`'s planner locale to vi (studio BFF `PUT /api/studio/trip-planner/appearance`
→ 200), and back to en afterwards (200).

| Width | Result | Evidence |
|---|---|---|
| 1440 | `html lang="vi"`, Vietnamese chrome ("Chuyến đi của bạn", "Bắt đầu xây dựng chuyến đi", filters, tabs) | `85-planner-vi__1440__light.webp` |
| 390 | `html lang="vi"`, Vietnamese chrome ("Khám phá", "Chuyến đi", "Trò chuyện", "Bộ lọc") | `85-planner-vi__390__light.png` |

Observation, **follow-up (not changed here)**: on the vi planner, the box "**Plan from a tour route**" keeps its English
title while its body text is Vietnamese. TripPlanner i18n: the heading needs a VI string in the planner message
catalogue.

# Section 6: AA-1158 payout lock and rule probes (in progress)

The A10e-6 allow-list fix is live (AA-Booking #319). The ground DMC is `SUP-000019` and the case is TC-000040.

| # | Step (identity) | Result | Evidence |
|---|---|---|---|
| 6.1 | SYNTHETIC bank account (E2E owner; number made in memory, never printed) | 201 **pending**, masked "•••• 4920". The full number is not in any response. The owner's approve → **403 `bank_approver_not_allowed`** | `70-bank.json` |
| 6.2 | Request + confirm SB-000017, SB-000019, SB-000021 (E2E owner) | 200 ×6 | log |
| 6.3 | Bill 1 entered by the pricing maker (A10e-6) | 201, `SYNTHETIC-S290-BILL-1` | log |
| 6.4 | Bill 1 approved by the pricing checker (A10e-6) | 200, BIL-000002 approved (second person) | `70-approve-bill1-checker.json` |
| 6.7a | Bill 2 entered by the pricing maker | 201, `SYNTHETIC-S290-BILL-2` | log |
| 6.5 | Payout on BIL-000002 while the account is pending (E2E owner: neither creator nor approver) | **409 `bank_account_pending`** "this supplier's bank account change waits for approval: no payout until it is decided" | `70-payout-bill1-pending.json` |
| 6.6 | Bill 3 entered by the E2E owner, then its own approve | 201; **403 `maker_checker`** "you entered BIL-000004: another person approves it" (the stand-in for "the tech lead never self-approves") | `70-approve-bill3-owner.json` |
| 6.7b | BIL-000003 (bill 2, the maker's) approved by the E2E owner → 200; its payout by the same E2E owner | **403 `maker_checker`** "you approved BIL-000003: another admin records its payout" | `70-approve-bill2-owner.json`, `70-payout-bill2-approver.json` |
| 6.10 | SYNTHETIC billing entity `SYN-S290` created with payment text (E2E owner) | 201. The text is **a pending change, not applied**. The requester's approve → **403 `maker_checker`**; withdraw → 200; entity deactivated. The real AA entity was never touched | `70-billing-entity.json` |
| 6.11 | SYNTHETIC probe supplier created by the E2E owner, then its own activate | **403 `maker_checker`** "a supplier is activated by someone other than the people who created or edited it"; probe deactivated | `70-self-activate.json` |
| 6.8 / 6.9 | Business owner approves the SUP-000019 account; then a payout within 24 h → 409 `bank_payout_locked` | **waiting for the business owner** | — |
| 6.12 | Ciphertext at rest (Infra run-script) | **orchestrator** | — |

# AA-1153 part 2 (AA-Booking #321 `0182e15c`, bk-072), live check S290

| # | Step (identity) | Result | Evidence |
|---|---|---|---|
| 1 | B2B desk on-request list (E2E owner): TC-000039's hotel line | `component.supplier` = **"SYNTHETIC S289 AA-1153 Lantern DMC B" (SUP-000017)**, the DMC whose rate priced the line (was the hotel's first DMC, SUP-000016, in S289). The page's Item column shows "Hotel room · SYNTHETIC S289 AA-1…" (truncated at 1440) | `90-desk-label.json`, `90-desk-on-request-dmc-label__1440__light.png` |
| 2a | Pricing policy (E2E owner) | **`allotment_release_days_default` = 7, `rate_sheet_max_rows` = 2000** | `90-policy.json` |
| 2b | Export the S290 hotel contract (maker, `GET /contracts/{id}/rate-sheet`, the Rates tab's Excel button) and add an **Inventory** row: HTL-000008 Double, `allotment`, 2 rooms, release 7, 24 Nov 2026 → 30 Jun 2027 | DRY RUN 200: 2 rates, diff 0 added / 0 changed / 0 removed against the exported contract, inventory `allotment` 2 rooms, release 7 (`release_days_default false`). Import → draft `eeab19b1-…` (c2). The **checker published it** (second person) | `90-dryrun-c2.json` |
| 2c | Desk entry (E2E owner, synthetic agency) **3 double rooms** on 24 Dec 2026 (> 7 days ahead) | booked TC-000042, **room line `on_request`** (2 rooms of allotment for 3 asked) | `90-quote-q3rooms.json` |
| 2d | Desk entry **2 double rooms**, same date | booked TC-000043, **room line `confirmed`** (available from the allotment) | `90-quote-q2rooms.json` |
| 2e | Desk entry 2 rooms on **27 Nov 2026** (inside the 7 release days) | booked TC-000044, **room line `on_request`** (released) | `90-quote-qrelease.json` |
| 3a | Baseline: 1 room on 5 Jan 2027, under c2 (net 80) | TC-000045 confirmed, quoted total **103.90** USD (floor 94.12) | `90-quote-qnet80.json` |
| 3b | Export c2 again, change HTL-000008 net **80 → 84**, DRY RUN | the diff is against the exported contract c2: **changed HTL-000008 Double BB, old 80.00, new 84, +5.0 %**; inventory row carried over (allotment 2, release 7); no check warning. Import → draft `99f5bf4b-…` (c3); **checker published** | `90-dryrun-c3.json` |
| 3c | Same request as 3a after c3 | TC-000046, quoted total **109.10** USD (floor 98.83) = ×1.05: **the newest published contract's net (84) prices the date** | `90-quote-qnet84.json` |
| 3d | 1 more room on 24 Dec 2026 (2 already held by TC-000043) | TC-000047 room line **`on_request`**: c2 and c3 both carry allotment 2, and the engine counts only the newest contract's terms, so **the allotment is not doubled (2, not 4)** | `90-quote-qnotdoubled.json` |
| 4 | Cleanup | the six desk bookings TC-000042…047 cancelled through the desk (each a dry run first, then 200). **c3 and c2 expired** by the checker (200), so the original S290 contract (net 80, no allotment) is again the only one in force | `90-supplier-rates-inventory__1440__light.png` (after cleanup: the Excel button and the "Room and service inventory" section) |

The `price_note.supply` reason of each on-request line (`allotment_full` for 2c / 3d, `released` for 2e) is stored
on the quote line, which no staff API returns. The orchestrator reads it with `10_bk_facts.py MODE=check
CASES=TC-000042,TC-000043,TC-000044,TC-000047` (counts and codes only).

Side note: TC-000041 (section 4 case B, sold under the sale exception) shows on the desk as an on-request tour line. It
is cancelled at cleanup.

# AA-1148 content workspace (AA-CIS-App #1664 `161deddd`, CIS 478; Booking bk-073), live check S290

- When: 2026-11-24, about 09:20–09:35 UTC.
- Identity: the E2E owner on the CIS admin (A10h, administrator), as the maker only.
- Script: `.tmp-session/S290/closeouts/95_aa1148.cjs`. It never runs the draft checks, so no SYNTHETIC tour can go live.

| # | Step | Result | Evidence |
|---|---|---|---|
| 1 | Workspace options and the list | **PASS.** `GET /admin/content-workspace/options` 200 returned these values (see the note below the table on the two-person switch): limits max_days 21, min_inclusions 3, min_exclusions 1, bulk_max 100; tour types private / join-in (EN + VI labels); quick chips: included "Private transport, English-speaking guide, Entrance fees, Meals as listed, Accommodation as listed, Drinking water", not included "International flights, Travel insurance, Drinks, Tips, Personal expenses, Visa fees"; `suppliers_available true`; **`two_person_publish false`**. The list is empty (0 hand-made tours) | `95-options.json`, `95-list__{1440,390}__{light,dark}.png` |
| 2 | Supplier picker (Booking view `v_supply_suppliers`) | **PASS.** The search "SYNTHETIC S290" lists SUP-000019 (ground DMC, transport + guide, TH, active) and SUP-000018 (hotel DMC). The New page shows "AA supplier (from Booking)" with search and list | `95-picker.json`, `95-new__{1440,390}__light.png` |
| 3 | Create a SYNTHETIC hand-made tour (`POST /admin/content-workspace/tours`) | **FAIL: HTTP 500 Internal Server Error**, 4 times between 09:2x and 09:30 UTC: 3 days + country "Thailand" + SUP-000019; 1 day + "TH" + SUP-000019; 1 day + "TH" with no supplier. **No tour was left behind** (the list still shows 0). The server error happens with or without a supplier, so it is not the supplier path. Cause needs the CIS API log | `results.log` |
| 3 (re-run after AA-CIS-App #1666 `dc8bbf15`) | Create, about 10:0x UTC: 3 days, Thailand, SUP-000019, deliberately incomplete (1 inclusion, no exclusion) | **PASS: 201** `{tour_id, wording_version_id}` | `95-create.json` |
| 4 | Editor and preview (E2E owner) | **PASS.** State `draft` ("Customers do not see it"), **completeness 85 %**. The required list shows ✓ for name, country, AA supplier from Booking, day cards, nights, titles, places, descriptions, no overlap, wording, "Day N —" blocks, and ✗ for "At least 3 included items" and "At least 1 item not included". The supplier is shown as SUP-000019. The Preview tab renders the facts and the wording at desktop and phone width | `95-view-a.json`, `95-editor-a__{1440,390}__{light,dark}.png`, `95-preview-a__{1440,390}__light.png` |
| 5 | Publish by the same person while incomplete (`POST /admin/tours/{id}/draft/publish`) | **PASS: refused, 409 `required_missing`** | `95-publish-a.json` |
| 6 | Facts completed with the quick chips (4 included, 2 not included), `PUT …/facts` with `expected_saved_at` | **PASS: 200**; completeness **100 %**, every item ✓ | `95-view-b.json`, `95-editor-b__{1440,390}__{light,dark}.png`, `95-preview-b__{1440,390}__light.png` |
| 6b | Publish by the same person, complete, checks not run | **PASS: refused, 409 `revalidate_required`**. The checks were deliberately never run, so nothing could publish | `95-publish-b.json` |
| 7 | Drawer `PATCH /admin/tours/{id}/raw {inclusions, reason}` | **PASS: 409 `manual_tour_use_workspace`** | `95-drawer.json` |
| 9 | Cleanup: `PATCH /admin/tours/{id}/trash` | **PASS: 200, `source_status trashed`**. The workspace now reads state `retired`, editable false. The tour was never published (no Master row) | `95-trash.json` |
| — | Where the batch shows | **Not confirmed.** `/admin/upload` has no batch list, so the "Content workspace" run row (`shared.pipeline_runs`, status completed, by #1666) was not seen in any page opened; a counts-only DB read would confirm it. No stuck ingest was visible. Before the trash, the tour was listed in **"Tours Ready for Rewrite"** with source file "—" and a Rewrite action | `95-upload-runs__1440__light.png` |
| 8 | Supplier links report and suggestions | **PASS.** `GET …/supplier-links` 200: **917 live tours not linked**, 0 with a suggestion. `POST …/apply-suggestions {dry_run: true}` 200: `matches 0, would_link 0` (nothing linked; DRY RUN only) | `95-links.json`, `95-supplier-links__{1440,390}__{light,dark}.png` |

**The two-person refusal is not demonstrated**: the switch stays off until the tech lead and the business owner turn it on
(Thursday). The refusals recorded are `required_missing` (incomplete) and `revalidate_required` (complete, checks not
run).

**Observation (for the CIS owner):** before the trash, a never-published hand-made tour shows in Upload › "Tours Ready
for Rewrite". A person could run S1 (paid) on it. The AA-1148 export guard then files the result in the Review Queue
instead of publishing it, so nothing goes live, but the list may confuse. Consider hiding `entry_origin = manual` tours
there, or labelling them "Content workspace".

**Two-person publishing is OFF on Dev** (`cis.content.publish_two_person` false). So once a tour exists, a same-person
publish attempt is not refused by the two-person rule. It is refused by the required list (409 `required_missing` while
incomplete), then by the unrun checks (409 `revalidate_required`). Showing "refused under the two-person rule" needs the
switch turned on in Platform › Settings (an administrator's audited change).

A two-person publish end to end needs a second real person. The A10f content_lead E2E identity is read-only in CIS
(no synthetic-tour marker), and the E2E owner may never be the checker (A10h D6).

Observation: the Supplier links report's "Supplier text in the sheet" column shows "—" on every row shown. If the sheet
text is empty for most live tours, that would explain 0 suggestions. Worth a look when the 500 is fixed.

# AA-1177 contract expiry reminders (AA-Booking #325 `29407508`, bk-074), live check S290

- When: 2026-11-24, about 11:35–11:50 UTC.
- Identities:
  - E2E owner (A10h): read, and the maker of the draft;
  - pricing checker (A10e-3): the second person who published it.

| # | Step | Result | Evidence |
|---|---|---|---|
| 1 | Pricing › Policy | **PASS.** `contract_expiry_alert_days` = 60, `contract_expiry_mail_roles` = `["admin", "contracting"]` | `98-policy.json`, `98-policy__1440__light.png` |
| 2 | SYNTHETIC hotel contract ending inside the window | **PASS.** The E2E owner imported "SYNTHETIC S290 AA-1177 expiring contract (live check, not real)" on SUP-000018: HTL-000008 Double BB, 25 Nov → **24 Dec 2026**. DRY RUN, then draft `b5d593eb-…`. The **pricing checker published it** | `90-dryrun-x1177.json` |
| 3a | `GET /booking/contracts/expiring` | **PASS.** 3 contracts. Ours: SUP-000018, kind **`["hotel"]`**, valid_to 2026-12-24, **30 days left**, announced false, mailed false (before any job run). `?supplier=SUP-000018` lists it alone | `98-expiring.json` |
| 3b | Dashboard My work tile "Contracts ending soon" | **PASS.** "3 · Within 60 days, first due 24 Dec 2026" | `98-mywork-tile__{1440,390}__{light,dark}.png` |
| 3c | Suppliers list | **PASS.** The KPI reads "Contracts ending within 60 days: 3". The "Contracts ending soon" panel lists the three contracts with days left, kind (Hotel / Activity) and state (ours "Pending", the S248 one "Notified") | `98-suppliers-expiring__{1440,390}__{light,dark}.png` |
| 3d | Supplier SUP-000018 › Contracts | **PASS.** The "Contracts ending soon" panel shows our contract (30 days left, ends 24 Dec 2026, Pending). The contract row shows "Upcoming" (it starts 25 Nov) | `98-supplier-contracts-tab__{1440,390}__light.png` |
| 4a | Job run r1 (orchestrator, ECS exec `99_contract_expiry_job.py APPLY=1 RUN=r1`: `bk_contract_expiry_watch:s290-r1`, payload `trigger manual`; today's scheduled run had already happened before the contract existed, and no staff route runs the job on demand). The tech lead approved the real run (it mails the real staff of the roles on Dev) | **PASS.** Succeeded 11:53:06Z: expiring 3, announced 2 (the S248 contract was announced before), mail outcome done, **sent 21, refused 0**. All three contracts are announced_rows 1 and mailed_rows 1. **One in-app notification `contract.expiring` for our contract** | orchestrator ecsx output |
| 4b | E2E mailbox (orchestrator, S3, since 11:52Z) | **PASS.** `inbound-admin/` 12 messages + `inbound/` 3 = **15 = 5 E2E addresses × 3 contracts**, one per person per contract, subject "[Dev] Supplier contract ends … / Hợp đồng nhà cung cấp hết hạn …" (MIME-encoded). The other 6 of the 21 went to 2 real staff | orchestrator mailbox read |
| 4c | Pages after the run (E2E owner) | **PASS.** `GET /booking/contracts/expiring`: all three announced true, mailed true. The Suppliers panel and the My work tile refreshed | `98-expiring-after-run.json`, `98-suppliers-expiring-after-run__1440__light.png`, `98-mywork-tile-after-run__1440__light.png` |
| 4d | Second run r2 (orchestrator) | **PASS.** Announced 0, **sent 0**; notifications for our contract still 1; the mailbox still holds 15: no repeat | orchestrator ecsx output |
| 5 | Cleanup: the pricing checker expired the SYNTHETIC contract `b5d593eb-…` | **PASS.** `PATCH /contracts/{id} {status: expired}` 200. It **left `/contracts/expiring`** (2 left, both earlier SYNTHETIC contracts) | `98-expiring-after-expire.json`, `98-suppliers-expiring-after-expire__1440__light.png` |

Not run here: "The window stays the Pricing › Policy value; changing it changes what is listed". Changing the window
is a two-person Pricing › Policy change, and the list and KPI already read 60 from the policy.
