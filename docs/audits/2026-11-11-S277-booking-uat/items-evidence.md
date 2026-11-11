# Booking AA-1073 / AA-1074 / AA-1075: per-item live evidence (S277, 11/11/2026)

Agent-run, read-only check of every scope item of the three Booking issues against Dev, so each issue can be closed
on evidence. Run by Claude Code on 11/11/2026, 10:20–10:45 UTC.

## What was checked, and how

- **Deployed versions.** API `GET /booking/health` → `git_sha` 5d712c8 (main); `GET /booking/health/ready` →
  `schema_version` bk-047, keys bk-001…bk-047 registered. Staff admin `GET /api/healthz` → `sha` e2e358c.
- **Staff reads.** The saved session of the read-only E2E staff user (`booking-admin`; the backend refuses every
  non-GET with 403 `e2e_read_only` before any DB access) was reused. A throwaway script outside the repo sent
  `GET /api/booking/...` through the admin BFF and opened each page in Playwright. It aborted every non-GET request
  to the BFF before it left the browser, and none was attempted. Pages: 0 uncaught page errors, 0 same-origin
  HTTP >= 400, 0 horizontal overflow at 1440 and 390, light and dark.
- **Dry runs.** `departures:generate` with `dry_run: true` writes nothing (the code only reads the existing dates).
  Called once as the E2E user, it answered **403 `e2e_read_only`**, refused before the DB as designed. All staff
  dry runs (generate, cancel, reduce, departure checks) are POSTs, so this user cannot run any of them. Their
  behaviour is covered by CI only.
- **B2B agency API (`/booking/b2b/v1/...`).** **Skipped.** No synthetic E2E agency M2M credential is documented
  in the Booking repo, its e2e folder, the root runbooks or the secrets register. The only Booking M2M client is
  the production AA-Partner CRM's own, which is not a test credential. The staff twins of the agency reads (vouchers,
  confirmation, cancellation, reductions, partner tariff) were read instead.
- **CI.** Merge-queue CI of every PR in the chain was green: #216 bk-045, #217 finance, #218 bk-046, #219
  departures, #223 bk-047, #224 agency ops, #225 finance titles. The latest merge-queue run, on top of all of
  them, is AA-Booking Actions run 43001114738 (PR #226, e2e358c). Its "Integration Tests" job ("no skips
  allowed") shows **636 passed**. Every test named below shows PASSED in that job's log. Integration tests run
  against a real PostgreSQL with the migrations applied.
- **Jobs.** `bk_departure_watch`, `bk_allotment_release`, `bk_departure_cost_recompute` and
  `bk_supplier_order_send` are registered in `app/jobs/kinds.py`. Only the first two have a live staff read,
  `GET /booking/b2b-desk/departure-checks/runs`. The two others have no run list. The ops deploy-gate read is not
  open to a staff session (401 through the BFF).

Verdicts: **LIVE**: the item's data and UI were seen on Dev, and its effect where Dev has data for it.
**CI-ONLY**: the read path or form is live but empty on Dev, or the effect needs a write or a scheduled run;
integration tests prove it. **NOT VERIFIED**: no live or CI proof. Here every such item is **not built**.
**BUG**: wrong behaviour seen.

Dev data at the time: one tour with fixed departures (5 weekly departures, 6 Nov – 4 Dec 2026). Every departure
has `min_to_operate` 0. No allotment, no shared departure cost, no purchase order, no staff-entered booking, no
supplier booking confirmed on an agency case, no tour terms, no b2b rule with `child_pct` / `infant_flat_usd`. Two
cancelled agency cases exist, TC-000027 (USD) and TC-000012 (VND).

## AA-1073: departures

| Item | Live check (route / page → status → key fields seen) | CI test evidence | Verdict |
|---|---|---|---|
| bk-01 Minimum to operate, sales cutoff, decision date | `GET b2b-desk/departures` 200 (5 rows) and `GET catalog/trip-plans/{tour}/departures` 200: each row has `min_to_operate` 0, `sales_cutoff_days` 0, `decision_days_before` 21, `sales_close_date` = start date, `decision_date` = start − 21, `seats_to_guarantee` null, `at_risk` false. `GET b2b-desk/summary` 200 `departures_at_risk` 0. Pages: trip plan Departures tab (Minimum / Sales close / Decision columns), departure drawer, B2B desk tile (earlier UAT shots) | `test_aa1073_departures::test_generator_minimum_cutoff_and_allotments`, `test_bk046_schema::test_departure_defaults_and_checks` | **LIVE** (fields, cutoff and decision dates). The at-risk path has no Dev data, see the watch row |
| bk-01 Daily `bk_departure_watch` (auto-guarantee, at-risk stamp, `departure.at_risk`, desk task) | `GET b2b-desk/departure-checks/runs` 200: `bk_departure_watch` succeeded today 06:53 UTC, `created_by` `scheduler:aa1073-departures`, `trigger` schedule, `checked` 0, `guaranteed_count` 0, `at_risk_count` 0, `schedule_utc_hour` 1. All Dev departures have minimum 0, so the watch has nothing to act on (by design: 0 = no minimum) | `test_aa1073_departures::test_watch_and_release`; `test_bk046_schema::test_at_risk_fans_out_once_to_the_agencies_on_the_departure`, `::test_at_risk_on_a_guaranteed_departure_emits_nothing` | **CI-ONLY** for the guarantee / at-risk effect. The scheduled job runs live |
| bk-02 Recurring departure generator | Trip plan → Departures → "Generate departures" drawer opens: From / To (≤ 400 days), weekly weekdays or monthly, seats, minimum, cutoff, decision, auto-confirm, "Preview dates" (shot `items/trip-plan-generate-drawer`). `POST .../departures:generate` with `dry_run: true` → 403 `e2e_read_only` (E2E user is read-only) | `test_aa1073_departures::test_generator_minimum_cutoff_and_allotments` | **CI-ONLY** (form live; dry run and create proven in CI) |
| bk-03 Per-agency allotments with release | `GET catalog/departures/{id}/allotments` 200: `items` [] and 13 `partner_options`. Desk rows `allotted` 0, `allotment_unused` 0. Drawer "Agency allotments" shows "No allotment on this departure." (earlier UAT). `bk_allotment_release` succeeded today 06:53 UTC (scheduled): `released` 0 | `test_aa1073_departures::test_generator_minimum_cutoff_and_allotments`, `::test_watch_and_release`; `test_bk046_schema::test_allotment_maker_checker_and_one_in_force`, `::test_allotment_facts_never_change_and_ending_is_final`, `::test_release_once_emits_to_the_one_agency`, `::test_cancelled_departure_takes_no_allotment` | **CI-ONLY** (no allotment on Dev; the release job runs live) |
| bk-04 Departure board (calendar, occupancy view, `/departures` page) | Not built: no `v_departure_occupancy` view, no staff `/departures` page or calendar in the code (grep on main 5d712c8). The implementation notes list it as a later slice. The B2B desk Departures tab (date window, held / sold / allotted / agencies count) covers part of it | none | **NOT VERIFIED (not built)** |
| bk-16 Ops sheet (guide, tour leader, meeting point and time) | Not built: no `meeting_point` / `meeting_time` / `ops_note` columns, no `departure_staff` table, no `departure.updated` event in the code | none | **NOT VERIFIED (not built)** |
| bk-09 Departure fees (minimum shortfall, unreleased allotment) | Not built: no `departure_fees` table, no `departure_fee` settlement role, no "Charge fee" action | none | **NOT VERIFIED (not built)** |
| bk-17 Departure price adjustments + early-booking rule | Not built: no `departure_price_adjustments` table. `GET pricing/rules` 200 has no `early_days` / `early_discount_pts` | none | **NOT VERIFIED (not built)** |

Update: bk-04, bk-16, bk-09 and bk-17 shipped later the same day (#228 / #229). See the section "AA-1073 remaining
items (after #229)" at the end. Bug 1 below was fixed by #227.

## AA-1074: finance

| Item | Live check (route / page → status → key fields seen) | CI test evidence | Verdict |
|---|---|---|---|
| bk-10 FX-normalised costs, realised FX difference | `GET trip-cases/TC-000015/supplier-costs` 200: `usd` {planned 480.00, billed 0, variance 0, fx_difference 0, cost 480.00, fx_missing false}. Each line carries `usd` {planned, billed null, variance null, fx_difference null}. `GET supplier-bookings` 200: `fx_rate_per_usd` / `fx_as_of` present (null: both bookings were confirmed 26/10, before bk-045). Profit `GET finance/profit/cases`: VND case TC-000012 revenue 1,982,000 VND → `revenue_usd` 79.28 at `fx_rate_per_usd` 25000. Page: case Suppliers tab, USD line (earlier UAT `case-costs-usd`) | `test_aa1074_finance::test_fx_snapshots_and_case_costs`; `test_bk045_schema::test_fx_plain_rate_reads_the_approved_rate_in_force`, `::test_booking_fx_snapshot_is_fixed_until_a_rerequest`, `::test_bill_fx_snapshot_is_set_once_with_the_approval` | **LIVE** (USD columns, revenue conversion). Every Dev supplier cost is USD, so the non-USD cost conversion and the snapshot at confirm / approve are **CI-ONLY** |
| bk-05 Departure shared costs priced by group size | `GET departures/{20 Nov dep}/costs` 200: `shared_costs` [], 3 cases with `shared_cost_usd` 0, `bills` [], `totals_usd` {revenue 347.59, cost 155.00, profit 192.59, profit_per_seat 64.20, margin 0.5541}. Drawer "Departure 2026-11-20": Shared costs empty state with "Add shared cost" and "Create purchase orders" (shot `items/finance-departure-costs-drawer`). `bk_departure_cost_recompute` has no live run list | `test_aa1074_finance::test_departure_cost_by_sold_seats_order_and_freeze`, `::test_recompute_watermark_moves_on_when_the_seats_go_back`, `::test_manual_cost_reprices_its_pending_booking`; `test_bk045_schema::test_a_booking_names_a_case_or_a_departure`, `::test_departure_cost_freezes_when_its_booking_is_requested` | **CI-ONLY** (no shared cost on Dev) |
| bk-06 Supplier purchase orders (e-mail send) | `GET supplier-orders` 200: `items` [], `total` 0. Costs & profit → Purchase orders: kit empty state (earlier UAT `finance-orders`). No order exists, so `GET supplier-orders/{ref}/document` could not be read | `test_aa1074_finance::test_purchase_order_create_send_and_answers`, `::test_send_refused_by_mail_goes_back_to_draft` (fake mailer); `test_bk045_schema::test_order_lines_and_life` | **CI-ONLY** |
| bk-07 Planned vs actual, per case and per departure | Case panel (above): planned per line, `billed` null, `unbilled` true, `variance` null until billed. Departure costs: `bills` [], `shared_planned` / `shared_billed` 0. No approved supplier bill on Dev | `test_aa1074_finance::test_fx_snapshots_and_case_costs`; `test_bk045_schema::test_departure_bill_takes_only_that_departures_bookings`, `::test_cost_variance_and_profit_views` | **LIVE** (planned side and "not billed yet" state). Variance on billed rows is **CI-ONLY** |
| bk-08 Profit per case / departure / agency | `GET finance/profit/cases` 200: 12 cases; totals revenue 2417.74 USD, cost 805.00, profit 1612.74, margin 0.6670. `GET finance/profit/departures` 200: 4 departures, totals revenue 783.58, cost 415.00, profit 368.58. `GET finance/profit/agencies` 200: 4 agency × month rows. Cross-check: the agency rows sum to the case totals (2417.74 revenue / 805.00 cost), and the departure rows sum to the departure totals. A cancelled case earns its fee: TC-000027 revenue 118.91 = the 75 % policy fee of 158.54 in `GET b2b-desk/bookings/TC-000027/cancellation`. `tour_title` is on every departure read. Pages: Profit tab, Departure costs list and drawer | `test_aa1074_finance::test_profit_reads`, `::test_departure_reads_name_the_tour_from_the_catalog`; `test_bk045_schema::test_cost_variance_and_profit_views`, `::test_cancelled_case_earns_the_fee` | **LIVE** |

## AA-1075: agency booking operations

| Item | Live check (route / page → status → key fields seen) | CI test evidence | Verdict |
|---|---|---|---|
| bk-11 Staff-entered agency bookings | `GET b2b-desk/entries` 200: `items` [], `total` 0, `awaiting_approval` 0. `GET b2b-desk/agencies` 200 (13). B2B desk → Agency bookings: tab and "New agency booking" drawer (agency, agency reference, currency, tour search, adults / children / infants, room mix, extra rooms and services, price override; shot `items/b2b-desk-new-agency-booking`). Manifest rows carry `entered_via` (all `api` on Dev) | `test_aa1075_booking_ops::test_staff_entry_vouchers_manifest_reduce_and_cancel` (booked at once, `entered_via` staff, `booking.created_by_aa` event, below-floor waits for a second approver); `test_bk047_schema::test_entered_via_defaults_and_checks`, `::test_desk_booking_maker_checker_and_created_by_aa_event`, `::test_api_confirm_emits_no_created_by_aa`, `::test_waiting_needs_an_override_below_the_floor` | **CI-ONLY** (form and list live; no staff entry on Dev) |
| bk-12 Service vouchers | `GET b2b-desk/bookings/TC-000033/vouchers?format=json` 200 and the same for TC-000011: `vouchers` [], `ops_contact` null, `agency_name` set. `?format=html` 200 prints "No voucher: the booking is cancelled or no service is confirmed by a supplier yet", "Traveller names are held by the agency", "Prices are not shown" (shot `items/vouchers-page`). No supplier booking is confirmed on an agency case on Dev. `b2b_ops_contact` is empty on Dev, as the notes say. `GET supplier-bookings` 200 rows carry `service_time`, `pickup_point`, `dropoff_point`, `voucher_note`. Case header "Vouchers" button (shot `items/case-agency-booking-panel`) | `test_aa1075_booking_ops::test_staff_entry_vouchers_manifest_reduce_and_cancel` (time, pick-up, confirmation ref, age bands, supplier name only, HTML "Lead traveller"); `test_bk047_schema::test_supplier_booking_voucher_fields_and_cancel_fee` | **CI-ONLY** (route live but empty on Dev; the B2B agency route was not called, no test credential) |
| bk-13 Manifest step 1 (counts only) | `GET b2b-desk/departures/{20 Nov dep}/manifest` 200: departure title, 3 of 4 seats; `totals` {adult 2, child 1, infant 0, seats 3, bookings 1}; `rooms` 1 × family; booking row: agency, agency ref, `entered_via` api, line confirmed; `supplier_bookings` []. `?format=html` 200 "Departure manifest … Counts only: traveller names stay with the agencies" (shot `items/manifest-print-html`). Page `/b2b-desk/manifest/{id}` (earlier UAT `after-fix/departure-manifest`). Step 2 (rooming names) is not built: it needs the DM-6.8 / ADR 0019 amendment, as the issue says | `test_aa1075_booking_ops::test_staff_entry_vouchers_manifest_reduce_and_cancel` | **LIVE** (step 1). Step 2: not built, by the issue's own dependency |
| bk-14 Cancellation: staff cancel + override / waive, supplier cancel cascade, supplier fee, partial cancel | `GET b2b-desk/bookings/TC-000027/cancellation` 200: `fee_pct` 75.00, `policy_fee` 118.91 USD, `fee` 118.91, `refundable` 39.63, `override` null, `can_approve_override` false. TC-000012 (VND): 50 %, fee 1,982,000, refundable 1,982,000. `GET .../TC-000011/reductions` 200 `items` []. `GET supplier-bookings` rows carry `supplier_cancel_fee` / `_currency`. Pages: case Agency booking card with "Fewer travellers" and "Cancel for the agency", the cancelled card (policy fee, fee charged, refundable), and both drawers open (shots `items/case-agency-booking-panel`, `case-cancellation-card`, `case-cancel-drawer`, `case-reduce-drawer`). Dry runs refused for this user (403 `e2e_read_only`) | `test_aa1075_booking_ops::test_staff_entry_vouchers_manifest_reduce_and_cancel` (reduce dry run, then a real reduce, `booking.line_reduced`; staff cancel with override asked and approved by a second person, `booking.fee_changed`; the confirmed supplier booking stays and its 12.50 USD fee becomes the cost in `v_cost_variance`); `test_bk047_schema::test_fee_override_needs_a_second_person_and_emits_fee_changed`, `::test_line_reduction_is_append_only_and_emits_line_reduced`, `::test_supplier_booking_voucher_fields_and_cancel_fee`. Cascade of pending / requested bookings: unit `test_aa682_supplier_bookings_flows` (`on_case_cancelled`) | **CI-ONLY** for every write path. The cancellation read and UI are live |
| bk-15 Child, infant, single-supplement net prices | `GET pricing/partner-tariffs/{agency}?source_id={tour}` 200: every band has `child_price_per_person`, `infant_price`, `single_supplement_per_person`. Child = adult price and infant 0.00, because no Dev rule sets `child_pct` / `infant_flat_usd` ("as adult"). Single supplement 0.00 / 48.78 / 32.52 / 39.02 / 41.81 / 44.34 USD for bands 1 / 2 / 3–4 / 5–6 / 7–10 / 11+. `GET pricing/rules` 200: `child_pct`, `infant_flat_usd` present (null). `GET catalog/trip-plans/{tour}` 200: `child_age_max` / `infant_age_max` null, so the defaults 11 / 1 apply ("Empty = 11", "Empty = 1" in the Agency terms panel). `GET .../prices` 200: the matrix has `child_amount`, `infant_amount`, `single_supplement_amount` (+ nets), all null, because the matrix was last priced 04/11, before bk-047 | `test_aa1075_booking_ops::test_tour_terms_and_child_price` (50 % child rule approved by a second person, infant flat, age bands); unit `test_single_supplement_is_the_single_rate_less_half_the_double`, `test_per_type_prices_follow_the_rule`; `test_bk047_schema::test_child_infant_single_columns_and_age_bands` | **LIVE** (engine on the tariff: single supplement, default child / infant). Non-default `child_pct` and the matrix columns filled on a recompute are **CI-ONLY** |
| bk-18 Per-product deposit and balance terms | `GET tour-terms/{tour}` 200 `items` []. `GET billing-terms` 200: default 30 % deposit, balance 30 days before. Trip plan → "Agency terms" panel: "No tour terms: the agency's terms or AA's default apply", For / Deposit % / Balance days form (shot `items/trip-plan-agency-terms`). `GET /b2b/v1/terms` (agency API) not called, no test credential | `test_aa1075_booking_ops::test_tour_terms_and_child_price` (`GET /terms` scope `tour`, then `agency_tour`, then back to `agency` / `default`); unit `test_plan_terms_pick_the_most_specific_row`; `test_bk047_schema::test_trip_plan_terms_one_row_per_scope` | **CI-ONLY** for the effect (no tour terms on Dev). Read and UI live, with **BUG 1** (layout) |

## Bugs

1. **UI (AA-1075 bk-15 / bk-18): the trip plan "Agency terms" panel sits outside the page column and shows under
   every tab.** In `frontend/app/(staff)/catalog/trip-plans/_parts/TripPlanDetailView.tsx`,
   `{p.has_commercial_row && <AgencyTermsPanel plan={p} />}` is rendered after the tab blocks, outside both the
   `tab === …` conditions and the padded content grid. Live, at 1440: the panel heading is at x = 269 on the
   Overview, Day by day, Photos and Departures tabs. The other cards' headings are at x = 301 on Departures. The
   panel spans from the sidebar edge to the window edge, with no side gutter (shots
   `items/trip-plan-agency-terms__1440__light.png`, `items/trip-plan-departures-tab-agency-terms__1440__light.png`;
   at 390 the panel is wider than the cards above it). Fix: move the panel into the Overview tab's column (or its
   own tab) inside the same container as the other sections.

No functional bug was found in the live reads. Every number cross-checked on Dev agreed: the profit totals per
agency and per departure, a cancelled case's revenue against its cancellation fee, and the manifest seats against
the departure's sold seats.

## Observations (not bugs of these issues)

- **Not built in AA-1073**: departure board (bk-04), ops sheet (bk-16), departure fees (bk-09), price adjustments
  and early booking (bk-17). `docs/implementation-notes/AA-1073.md` names them "later slices of the same issue".
  The issue's Done-when ("each item above is live on Dev") is therefore not met. Close it only after splitting
  these four into a follow-up, or keep it open.
- **Not built in AA-1075**: manifest step 2 (rooming names). Expected: the issue makes it depend on a data-standard
  amendment.
- **Changes against the issue text** are recorded in the notes: staff entry route `POST /b2b-desk/entries`; partial
  cancel stored as a reduction record, not a new version; tour terms in their own table, not a `trip_plan_id`
  column; no phone / e-mail on vouchers (contract field policy); purchase order confirmed / partly confirmed
  derived, not stored.
- `planned_profit_usd` (API only, `v_case_profit`) is `revenue_usd − planned_cost_usd`. On a case with no supplier
  booking it equals the revenue: TC-000011 has a planned profit of 158.54 USD, while `profit_usd` is 28.54 on the
  quoted cost. No page shows the field. Worth a note in the field description before a consumer reads it.
- The staff agency tariff page (`/pricing/agency-tiers/tariff`) does not show the child / infant / single columns
  that its API now returns. The issue asks only the CRM to read them, so this is optional.
- Stale code comment: `backend/app/b2b/cancellation.py` around line 440 says "requested / confirmed ones raise
  'cancel with supplier'". The code (`ops/supplier_bookings.on_case_cancelled`, AA-1075) cancels pending **and
  requested** bookings and raises the task for confirmed ones only.
- Older behaviour seen on these pages, outside the three issues: B2B departure cases read "Custom trip … no CIS
  tour linked yet". Their end date equals the start date (a 6-day tour shows "1 day"; `end_date` = `start_date`
  in the vouchers / confirmation JSON). The People card shows a raw partner tenant id. A cancelled case's banner
  prints the agency's M2M client id in the reason, masked in the shots here.
- The staff admin host answered 503 for a few seconds around 10:37 UTC (`staff/me` through the BFF). It was back
  at once: `/login` 200 six times in a row, `healthz` 200 on e2e358c. The API stayed healthy. Probably a task
  restart; not investigated.
- The `Deploy Admin Dev` run of 5d712c8 failed. The fix, #226 (e2e358c), deployed green, and that is the build
  checked here.

## Screenshots (`items/`)

Each at 1440 × 900 and 390 × 844, light and dark (`<page>__<width>__<theme>.png`), unless noted. All pages not
already in this folder or `after-fix/`:

| Shot | Page | Item |
|---|---|---|
| `trip-plan-generate-drawer` | `/catalog/trip-plans/<tour>?tab=departures`, "Generate departures" drawer | AA-1073 bk-02 |
| `finance-departure-costs-drawer` | `/finance?tab=departures&departure=<id>` | AA-1074 bk-05, bk-07, bk-08 |
| `b2b-desk-new-agency-booking` | `/b2b-desk?tab=agency-bookings`, "New agency booking" drawer | AA-1075 bk-11 |
| `case-agency-booking-panel` | `/cases/TC-000033` (Vouchers, Fewer travellers, Cancel for the agency) | AA-1075 bk-12, bk-14 |
| `case-cancel-drawer` | the same, "Cancel for the agency" drawer (not submitted) | AA-1075 bk-14 |
| `case-reduce-drawer` | the same, "Fewer travellers" drawer (not submitted) | AA-1075 bk-14 |
| `case-cancellation-card` | `/cases/TC-000027`, cancelled card (reason line masked) | AA-1075 bk-14 |
| `pricing-rules-child-infant` | `/pricing/rules` | AA-1075 bk-15 |
| `agency-tariff-child-infant-single` | `/pricing/agency-tiers/tariff?partner=<agency>` | AA-1075 bk-15 |
| `trip-plan-agency-terms` | `/catalog/trip-plans/<tour>`, Agency terms panel | AA-1075 bk-15, bk-18 (Bug 1) |
| `trip-plan-departures-tab-agency-terms` (1440 only) | the same panel under the Departures tab | Bug 1 |
| `vouchers-page` (1440 light only) | the staff vouchers HTML of TC-000033, rendered from the live response (served as a download) | AA-1075 bk-12 |
| `manifest-print-html` (1440 light only) | the printable manifest HTML of the 20 Nov departure | AA-1075 bk-13 |

## AA-1073 remaining items (after #229)

Re-checked on 11/11/2026 around 11:30 UTC, against API and staff admin both on main 69c4ffb (Booking #228 is the
bk-048 migration, #229 the code). `GET /booking/health` reports `git_sha` 69c4ffb, `/booking/health/ready` reports
`schema_version` bk-048, and the admin `healthz` reports `sha` 69c4ffb. Same method as above: the read-only E2E
staff session, GETs through the BFF, and every non-GET aborted in the browser (0 attempted). Pages: 0 page errors,
0 same-origin HTTP >= 400, 0 horizontal overflow.

**CI.** Merge-queue CI of #229 is AA-Booking Actions run 43024811924: all 8 jobs green. Its "Integration Tests"
job ("no skips allowed") shows **648 passed**. The 12 tests named below all show PASSED in that job's log, together
with the earlier `test_aa1073_departures` pair. Push runs of 69c4ffb: Deploy Dev and Deploy Admin Dev green.

**B2B agency API.** Still not called, because no synthetic agency credential is documented. Contract
`booking.b2b.v1` 1.8 (root #700) adds `Departure.meeting_point` / `meeting_time` and the events
`departure.updated` / `departure.fee_charged`. Its agency-facing side is covered by
`test_aa1073_rest::test_board_ops_and_fees`: "meeting point and time reach the agency; the note does not".

**Dev data.** November has 4 departures (6 / 13 / 20 / 27 Nov) with 8 of 12 seats sold, and December has 1.
None is at risk, and there is no allotment, no fee, no price adjustment, no ops sheet, no departure staff and no
rule with early booking.

| Item | Live check (route / page → status → key fields seen) | CI test evidence | Verdict |
|---|---|---|---|
| bk-04 Departure board (calendar, occupancy, filters, drawer with seats by agency, price column) | `GET b2b-desk/departure-board?from=2026-11-01&to=2026-11-30` 200: 4 items, `totals` {departures 4, capacity 12, sold 8, held 0, free 4, at_risk 0, incidents 0}, `countries` [Philippines], `plans` 1. Each item has `occupancy_pct` (100.0 / 0.0 / 75.0 / 75.0), `agencies_count`, `allotted`, `min_to_operate`, `open_incident` and `price`. Filters answer: December window → the 4 Dec departure only; `at_risk=true` → 0; `country=Philippines&status=scheduled` → 4. `GET b2b-desk/departure-board/{20 Nov}` 200: `agencies` [the agency with 3 sold, 0 held, case TC-000033, allotment null], plus the `ops`, `fees`, `fee_suggestions`, `price_adjustments` and `partner_options` sections. Page `/departures` (Operations → Departures): KPI tiles 4 / 8 of 12 / 0 / 0. The calendar shows each departure on its Friday with its occupancy bar (shot `items/departure-board-calendar`). Table with the Country + Status filters applied, and a Price column reading "from 400.00 USD" (`items/departure-board-table-filtered`). The drawer has Seats by agency, Ops, Departure fees and Price, with links "Open on the trip plan" and "Manifest" (`items/departure-board-drawer-fees-price`; smoke `after-1073/departure-board-drawer`) | `test_aa1073_rest::test_board_ops_and_fees` (window, view seats, filters, drill-down); `test_bk048_schema::test_occupancy_view_counts_like_the_app` | **LIVE**. See BUG 2 (smoke wait) |
| bk-16 Ops sheet (meeting point, time, ops note, departure staff) | Board detail `ops` {meeting_point null, meeting_time null, ops_note null, staff []}, with `staff_options` (Booking staff users) and `supplier_options` (one guide / transport supplier). Board list rows carry `meeting_point` / `meeting_time`. The drawer's Ops section renders: meeting point, meeting time ("Local time on the start date"), ops note ("Staff only, never sent to an agency"), "Save ops sheet", and Role (Guide …) + Who + Assign. No ops sheet is saved on Dev; writes are `PATCH .../ops`, `POST .../staff` and `DELETE departure-staff/{id}` | `test_aa1073_rest::test_board_ops_and_fees` (agency sees point and time, never the note; content role refused); `test_bk048_schema::test_ops_sheet_checks_and_departure_updated`, `::test_departure_staff_one_kind_of_person`, `::test_erasure_marks_staff_text_only` | **CI-ONLY** for the write and the `departure.updated` event. The read and UI are live |
| bk-09 Departure fees (minimum shortfall, unreleased allotment) | `GET b2b-desk/departure-fees` 200: `items` [], `total` 0, `pending` 0; by `departure_id` also empty. Board detail `fees` [] and `fee_suggestions` [] (nothing at risk, no allotment). The drawer shows "No fee on this departure." and the generic "Charge fee" button. The suggested "Charge minimum shortfall / allotted seats not released" buttons and the "Charge fee" action on at-risk desk rows and on allotments render only for an at-risk departure or an allotment in force or released (code: `B2BDeskView.tsx` `d.at_risk`, `DeparturesPanel.tsx` allotment state, `DepartureBoardDrawer.tsx` `fee_suggestions`). Dev has none, so they were not seen. Terms clause: `GET partner-terms-clauses` 200 lists `departure_fees` "Departure fees", status **draft**, `updated_by` `system:bk-048`, so `GET /terms` does not show it until the business owner approves the wording (by design). Settlement role: bk-048 widens the `agency_invoice_line` role CHECK to `departure_fee`, with `source_fee_id`. The migration is applied (readiness bk-048), but the role cannot be read from a staff session, and the root schema reference is still at bk-046 | `test_aa1073_rest::test_board_ops_and_fees` (maker sales, second person approves, the settlement draft bills the fee once); `test_bk048_schema::test_fee_maker_checker_final_and_event` (`departure.fee_charged`), `::test_settlement_line_bills_a_fee_once` | **CI-ONLY** (no fee on Dev; the at-risk / allotment actions are not reachable with Dev data) |
| bk-17 Price adjustments + early booking | Board detail `price_adjustments` []. Each board row has `price` {hint 400.00 USD per person, adjustment null, early_booking null}, shown in the table's Price column as "from 400.00 USD". `GET pricing/rules` 200: all 5 rules carry `early_days` / `early_discount_pts`, null on every rule. The "New pricing rule" drawer (B2B channel) shows "Early booking: days before start" and "Early booking: margin points off" (shot `items/pricing-rule-drawer-early-booking`). The drawer's Price section renders (no adjustment) | `test_aa1073_rest::test_price_adjustment_and_early_booking_on_quotes` (10 % off proposed by contracting, refused for sales and for the maker, approved by admin; sells under the floor with a note; withdrawn; then an early-booking rule lowers the next quote); `test_bk048_schema::test_price_adjustments_one_in_force_maker_checker`, `::test_early_booking_rule_columns`, `::test_quote_line_price_note_is_an_object` | **CI-ONLY** for the effect on quotes (nothing set on Dev). Fields, price column and form are live |

**BUG 2 (test wait, bk-04 signed-in smoke): the calendar screenshots are taken before the board query answers.**
The shots `after-1073/departure-board__*.png` show skeleton KPI tiles and an empty November grid. The page is not
at fault. Loading `/departures` and waiting for `GET /api/booking/b2b-desk/departure-board` to answer, the
calendar shows the 4 departures on 6 / 13 / 20 / 27 Nov and the tiles read 4 / 8 of 12 / 0 / 0 (shots
`items/departure-board-calendar__*`, 1440 and 390, light and dark). Measured in one run:

- The month header is visible 0.8–1.3 s after load, with no `main [aria-busy="true"]` element.
- The board response arrived up to 4.5 s after load (390 light).
- In 3 of the 4 viewport / theme runs, the header was up while no chip was rendered yet.

The cause is in `frontend/e2e/signed-in/departure-board.spec.ts`. The `ready` callback passed to
`capture(page, "departure-board", …)` waits only for `pageSettled` and `getByTestId("board-month")`:

- The month header is static: it renders before the query starts.
- `pageSettled` looks for `aria-busy`, but neither the kit KpiTile skeleton (`role="status"`, no `aria-busy`) nor
  the desktop calendar marks its loading state.

The `bffGet` call just before is the test's own request; it does not wait for the page's query. Fix: in that
`ready`, wait for the board response (`page.waitForResponse` on `b2b-desk/departure-board`, armed before the
reload in `capture`), or for the KPI "Departures" value / the first `board-chip` / the empty-month text. The table
and drawer captures are unaffected: they wait for `tableSettled` and for the drawer. A side note on the page: the
desktop calendar draws no loading state (only the phone list says "Loading…"), so a slow board looks like an
empty month until it answers. This is cosmetic, not a defect.

**Bug 1 (Agency terms panel) re-checked after #227 (18bd127): fixed.**

- Departures tab: no "Agency terms" heading (shots `items/trip-plan-departures-after-227__*`).
- Overview at 1440: the panel sits in the right-hand column (heading x = 1060, the same column as the price card).
- Overview at 390: the panel is inside the page gutter (x = 53, like the other cards; shots
  `items/trip-plan-overview-after-227__*`).

**Observations.**

- **Price column "from" is not the agency price.** The board's "from" price is the trip plan's commercial price
  hint (400.00 USD per person on Dev). That is not the B2B price agencies are quoted (79.27–128.05 USD per person
  on the agency tariff of the same tour). The notes say this is on purpose ("a hint + the adjustment", the quote
  is the price of record), but a label such as "price hint" would avoid staff reading it as the agency price.
- **The E2E user is assignable as departure staff.** The Ops "Who" list (`staff_options`) includes the E2E staff
  user, like the trip case StaffPicker; SIGNED-IN-SMOKE.md already flags this.
- **Root schema reference is behind.** `docs/architecture/db-schema-reference.md` still reads Booking bk-046 (dump
  of 05:58 UTC). The bk-048 objects appear after the next DB Schema Dump run.

Shots added to `items/` (1440 and 390, light and dark):

- `departure-board-calendar`
- `departure-board-table-filtered`
- `departure-board-drawer-fees-price`
- `pricing-rule-drawer-early-booking`
- `trip-plan-departures-after-227`
- `trip-plan-overview-after-227`
