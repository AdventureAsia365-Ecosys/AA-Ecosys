# AA-1151 add-on offers and AA-1152 day add-ons / agency prices: live check on Dev (S289, rerun)

- When: 2026-11-24, 02:19–02:39 UTC (09:19–09:39 +07). Run by an agent, headless Playwright (Node, the Booking
  `frontend/node_modules`). Rerun of `../aa-1151-1153/evidence.md`. That run was blocked (B1) because the pricing
  maker had no Booking group. The tech lead approved giving the group back on 24/11 at about 09:20.
- Deployed: Booking `/booking/health` `git_sha 1c32a10d…`, `/booking/health/ready` `schema_version bk-070`.
  TripPlanner 12b6a4d2 and Partner 28b1c4f6 are as stated by the coordinator; their SHAs were not re-read here.
- Booking and CIS sign-in: Cognito managed login with an e-mail code. The code was read from the S3 prefix
  `inbound-admin/` with the MFA admin profile. It was never printed, logged or screenshotted.
  - The CIS admin session reused the E2E owner's staff sign-in, so no second code was needed.
  - CRM sign-in: the pilot-rehearsal-01 E2E owner (`crm/dev/e2e-test-crm/pilot-rehearsal-01-owner`), with a password
    and an authenticator code. The secret was read with the AWS CLI inside the runner and never printed.
  - No screenshot was taken on `staff-auth.` or `partner-auth.`. All local browser state files were deleted at the
    end.
- Identities (root ADR 0006a):
  - pricing maker (A10e-2/3/4): `staff/me` 200, role `contracting`, cis_role `customer_success`;
  - pricing checker (A10e-2/3);
  - E2E owner (A10h);
  - CRM E2E owner of the synthetic agency `pilot-rehearsal-01`.

## AA-1151

| # | Step | Time (UTC) | Request → status | Result |
|---|---|---|---|---|
| 1a | Maker creates a SYNTHETIC supplier | 02:20:11 | `POST /suppliers` → 201 | `SUP-000015` "SYNTHETIC S289 AA-1151 activities DMC (live check, not real)", category activity, VN, Ho Chi Minh City, status **pending** |
| 1b | Maker DRY RUN before activation | 02:20:11 | `POST /suppliers/SUP-000015/activity-sheets?dry_run=true` → 422 | `supplier_inactive`, as designed (AA-1158 R5: a second person activates) |
| 1c | Checker activates the supplier | 02:20:34 | `POST /suppliers/SUP-000015/activate` → 200 | active |
| 1d | Maker DRY RUN | 02:20:45 | same → 200 | `dry_run: true`, 5 activities, contract "SYNTHETIC S289 AA-1151 activity catalogue (live check, not real)", USD, 2026-11-24 → 2027-01-15. Rules: Cu Chi `operating_weekdays [1,3,5]`; cooking class `start_times 09:00`; cruise 18:00; nets 25/30/45/35/40 |
| 1e | Maker import | 02:21:05 | `POST /suppliers/SUP-000015/activity-sheets` → 200 | `imported: 5`: services `SVC-000013`…`SVC-000017`, 5 offers, **1 draft contract** `ac3f989c-…` |
| 2 | Checker publishes the contract | 02:21:16 | `PATCH /contracts/ac3f989c-…` `{status: published}` → 200 | `status published`, `phase in_force`, `created_by` = maker, `published_by` = checker |
| 3 | E2E owner publishes the 5 offers | 02:21:41–43 | `GET /add-ons?status=draft` (5 SYNTHETIC S289 drafts), then 5 × `POST /add-ons/{id}/publish` → 200 | Each offer: `created_by` maker, `published_by` E2E owner, `owner_self_approved false` |
| 4 | Place add-on view (staff API) | 02:21:43 | `GET /add-ons/place-days?destination_id=<HCMC>&date_from=2026-11-24&date_to=2027-01-31` → 200 | `days_ahead 365`, 192 rows. See the table below |
| 5 | Add-ons page | 02:22 | UI | "5 add-ons", all Published. "Contracts ending soon" now lists the new contract ("52 days left … ends 15 Jan 2027"). `a1151-addons-published__1440__light.png`, `__390__` |

Rows returned by the place add-on view, per offer (asked up to 2027-01-31):

| Offer | Rule in the file | Days returned | First → last | Weekdays seen |
|---|---|---|---|---|
| SVC-000013 street food walk | daily | 53 | 2026-11-24 → 2027-01-15 | all 7 |
| SVC-000014 Cu Chi tunnels | Mon, Wed, Fri | 23 | 2026-11-25 → 2027-01-15 | Mon, Wed, Fri only |
| SVC-000015 Mekong delta | valid 2026-12-01 → 2026-12-10 | 10 | 2026-12-01 → 2026-12-10 | — |
| SVC-000016 cooking class | daily, 09:00 | 53 | 2026-11-24 → 2027-01-15 | all 7 |
| SVC-000017 dinner cruise | daily, 18:00 | 53 | 2026-11-24 → 2027-01-15 | all 7 |

The view returns no day after the contract end (2027-01-15), though the request asked up to 2027-01-31. It returns no
non-operating weekday and no Mekong day outside its own window: **only in-force days**. Booking has no staff page for
this view, so the evidence is the API answer.

**Kept:** the supplier, the contract and the 5 published offers stay in place (AA-1152 uses them). Nothing was retired.

**LLM cost:** the import queued 5 CIS supply-content draft jobs. CIS `GET /admin/supply-content/status` (E2E owner,
read): `draft_jobs_7d {"succeeded": 5}`, `llm_cost_today_usd 0.014286`. That covers every supply-content call today,
so these 5 drafts account for at most 0.014 USD. The 5 SYNTHETIC S289 services are `in_review` in CIS. Nobody
published their content, so Booking still shows "No customer text".

## AA-1152

| # | Step | Time (UTC) | Result | Evidence |
|---|---|---|---|---|
| A | AA's planner (`/plan`, demo tenant): start from "Ho Chi Minh Trail Cycling" (`/plan?tour=3fa33633…&source=ca1d7500…`). This created one anonymous guest trip | 02:23 | `GET /api/trip/addons` 200, `prices_shown false`. Day 7 "Cu Chi" (overnight Ho Chi Minh City) shows "Optional activities this day" with all 5 SYNTHETIC S289 add-ons, tagged "Where you stay", with runs and start times, and no price (AA's own planner) | `a1152-aa-planner-hcmc-day-card__1440__light.webp`, `__390__` |
| B | Tick "SYNTHETIC S289 Saigon street food walk", then reload | 02:30:21 | `POST /api/trip/addons` 200 `{day 7, component_id "sv:7e2d6d62-7ed2-49b1-aee1-fe9c9d21d890"}`. After the reload the GET still shows it `selected`: it is stored as a trip event with its `sv:` code | `a1152-aa-planner-addon-ticked-after-reload__1440__light.webp` |
| C | Lead with the pick | — | **Not run.** On AA's planner "Send to an advisor" is a demo notice and sends no lead. The two agency planners on Dev do not sell a tour through Ho Chi Minh City: `pilot-rehearsal-01` sells China / Philippines / Sri Lanka and `audit-atlas-hearth` 11 tours, none at HCMC. An agency planner removes out-of-scope stops from the trip: the trip GET with the tenant header returned an empty itinerary after a Cu Chi stop was added. So no agency day card can list an HCMC add-on, and no lead was submitted. Unblock: an agency adopts the HCMC tour, or offers are imported at a place an agency sells (a CIS tenant write, outside this lane) | — |
| D | CRM Settings › Payments › "Prices on my planner and rounding" (pilot-rehearsal-01 owner) | 02:29 | Panel present. "Show prices on my planner" was **on**. USD step AA default (1), choices 1/5/10. VND default 10000 | `a1152-crm-planner-prices-initial-on__1440__light.png`, `__390__` |
| E | Save (switch on) and check the agency tour page | 02:30:00 save, 02:31 page | Before the save, every pilot tour page read `{"price": null}`, probably an old list (stale window 6 h). After the save (`PUT settings/planner-prices` 200), "Bohol, Dumaguete and Siquijor" `/pilot-rehearsal-01/tours/…-000e3340` read `{"from_per_person": "110", "currency": "USD"}` and the page shows "From **$110** per person · Indicative price; your final price is in E2E Pilot Rehearsal Travel's quote" | `a1152-agency-tour-page-price-on__1440__light.png`, `__390__` |
| F | Switch off, save, reload the page | 02:36:42 save, 02:36:54 page | `show_planner_prices false`. The route answers `{"price": null}` within about 12 s and the page shows no price line | `a1152-crm-planner-prices-saved-off__1440__light.png`, `a1152-agency-tour-page-price-off__1440__light.png`, `__390__` |
| G | Switch back on (restores the starting state) | 02:37:12 save, 02:37:14 page | price `110 USD` again | `a1152-crm-planner-prices-saved-on__1440__light.png` |

Rounding: $110 is a whole number at the USD step of 1. Booking's own price for this plan is already 110.00, so the
round-up is not visibly exercised. The step was not changed and no markup was set (no extra writes).

## Writes made on Dev by this run

- Booking: supplier `SUP-000015` (active), 5 services `SVC-000013`…`017`, 1 published contract `ac3f989c-…`, 5
  published offers. All are marked SYNTHETIC S289 and kept.
- CIS: 5 supply-content LLM drafts (`in_review`), queued by the import.
- TripPlanner: 3 anonymous guest trips:
  - on AA's planner, `d8767425-…`: the Ho Chi Minh Trail tour and one pick (`sv:7e2d6d62-…`), day 7;
  - on `pilot-rehearsal-01`, `973776db-…`: one Cu Chi stop. Its guest cookie was overwritten by mistake, so the stop
    could not be removed. The agency view filters it out;
  - on `pilot-rehearsal-01`, `7189a27f-…`: the Cu Chi stop was added and removed again (empty).

  No lead, no name, no e-mail.
- CRM (pilot-rehearsal-01): `PUT settings/planner-prices` three times (on, off, on). The final state equals the
  starting state (on, default steps).

## Observation for the TripPlanner owner (not verified as a bug)

The planner sends `x-tp-tenant-slug` on its calls. A `POST /api/trip {op: add}` and a `GET /api/trip?trip_id=` sent
**without** that header worked on a trip created on `/pilot-rehearsal-01/plan`: the GET returned the out-of-scope Cu
Chi stop that the tenant-scoped GET hides. Both calls need the trip's own guest cookie, so this is no cross-traveller
access. Still, a trip of an agency can be read and changed through the demo-tenant path. The owner should check that
this is intended.

## Result per Done-when

| Item | Result |
|---|---|
| AA-1151: a file of 5 activities creates 5 drafts | **pass** (DRY RUN 200 then import 200: 5 draft offers + 1 draft contract) |
| AA-1151: a second person publishes | **pass** (checker published the contract; E2E owner published the 5 offers; maker ≠ publisher) |
| AA-1151: the place add-on view returns only in-force days | **pass** (contract end, weekdays and the row window all respected) |
| AA-1152: the HCMC day card shows ≥ 1 add-on | **pass** on AA's planner (5 add-ons, 1440 and 390); **not run** on an agency planner (no agency sells HCMC) |
| AA-1152: a ticked add-on reaches the lead with its `sv:` code | **not run**. The pick is stored with its `sv:` code and survives a reload (pass), but no lead can be sent: demo planner, and no agency sells HCMC |
| AA-1152: the agency page shows a rounded "from" price and hides it when switched off | **pass** ($110 per person on, hidden within seconds off, back on). The round-up is not visibly exercised (value already whole) |

## Correction (S289, after a code review of the tenant isolation)

The note above that "an agency trip can be read and changed without the agency (tenant) header" is wrong. The trip in
question was created by this lane's own header-less POST, so it belongs to the default (demo) tenant from the start.
Under the agency's header the same trip answered 404, which the BFF shows as an empty trip; agency planners do not
filter stops. Tenant isolation holds: the Lambda binds `app.tenant_id` per connection and `tripplanner.sessions`,
`trip_drafts` and `trip_events` have FORCE row-level security (role `tripplanner`, no BYPASSRLS); another tenant's read
is 404 and its write is 401 with nothing written (`backend/tests/test_tenant_rls_pg.py`, `test_aa1038_tenant_site_pg.py`).
Three independent reviews agreed (not real, severity none). Minor hardening noted: a fresh session under tenant B with a
trip id of tenant A ends in a 500 with rollback instead of a 403 (no data read or written). Future live checks of an agency
planner must always send `x-tp-tenant-slug`.
