---
id: OPS-08-s261-aa990-readers
title: "S261 AA-990 live evidence: Booking, CRM and Content studio readers on S1 v2 text"
description: "Agent-run Playwright checks on the Dev hosts (31/10/2026): Booking proposal and trip-plan read-back compared with the public CIS text, an AA line quote on a rewritten tour in the CRM, and the master_newer badge in the Content studio."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-990, AA-947, AA-986, AA-645]
---

# AA-990: S1 v2 text in the Booking, CRM and tenant readers (S261, 31/10/2026)

This run covers triage lane 3 item 1 (the $0 part that does not depend on AA-997). Three checks, one comment each.

## How it ran

- Headless Chromium (Playwright 1.59 library), one browser at a time, against the live Dev hosts:
  - Booking admin `booking.lumiguides.it.com`;
  - CRM web and Content studio `portal.lumiguides.it.com`;
  - the public client host `go-dev.lumiguides.it.com`;
  - the public CIS API `api-cis.lumiguides.it.com`, read only (`GET /v1/trip/{tour_id}`, no auth).
- Egress checked first: VN, not the VPN.
- Identities. Codes and secrets were read at run time and never written down. No screenshot was taken on the managed-login host.
  - **Booking:** the AA-910 E2E staff (`booking-admin`), with a read-only session, signed in by email code from the E2E mailbox.
  - **CRM:** the e2e **owner** of the synthetic agency "Lữ hành Sen Vàng" (partner pool, password and authenticator).
  - **Content studio:** the e2e **studio-viewer** of the tenant "Atlas & Hearth (E2E)" (partner pool, password and authenticator).
- Console errors means `console.error` and uncaught page errors on the app origin. Failing requests means responses ≥ 400 on the app origin.
- The S1 v2 status of the tours used:
  - All 892 active tours were rewritten by S1 v2 on 25/10 (AA-645).
  - The two tours used here are also in the S252 parity sample, which recorded "v2 text OK" (`docs/audits/2026-10-26-S252-aa990-parity/`).
  - The Bhutan tour's Master was published again on 30/10 (`v_tour.updated_at`).
- Raw records are in [`data/`](data/). Tour ids and source ids are catalog keys. CRM trip and line ids are cut to 8 characters.

## Results

| # | Done-when line (AA-990 scope 3, 4, 5) | Result |
|---|---|---|
| 1 | Booking: the proposal read-back shows the new published text | **PASS for the catalog read-back, with finding F1 on stored proposal items.** Each trip-plan page matches the public CIS text exactly, field by field. A proposal version made before the rewrite still shows the day titles copied when it was made. |
| 2 | CRM: `crm_catalog_sync` picked up the new text, and an AA line quote on a rewritten tour works | **PASS.** The CRM catalog cache title equals the CIS name. A new AA line went from "AA pending" to "AA quoted" with a Booking quote. |
| 3 | Tenant versions older than Master: the tenant is informed and nothing is silently overwritten | **PASS.** The "Updated by Adventure Asia" badge shows on 2 of 2 `master_newer` versions. The drawer notice says the text was not changed and offers Rewrite. |

### 1. Booking: proposal trip case and trip-plan read-back

Tour **"Bumdra Trek, Bhutan — 7 Days"** (source `4a2411b2…`, tour `2e1fd11d…`). The case is **TC-000008**: source `cis`, proposal V2 (draft), made 16/10/2026, before the S1 v2 rewrite.

| Check | Result | Screenshot |
|---|---|---|
| Trip-plan page, Day by day tab (reads `catalog.v_tour_day` live) compared with the public CIS `GET /v1/trip/2e1fd11d…` | Title equal. Summary equal. **7/7 day titles and 7/7 day bodies equal** (whitespace normalised). | `01a-booking-trip-plan-bumdra-days-{1440,390}.png`, `01a-…-overview-1440.png` |
| Second tour, the CRM seed tour "Tropical Jewels: Bohol, Dumaguete and Siquijor — 6 Days" (source `000e3340…`) | Title and summary equal. **6/6 day titles and 6/6 bodies equal.** | `01e-booking-trip-plan-bohol-days-1440.png` |
| Proposal TC-000008 V2: builder and customer-style preview | 7 items tagged "FROM CIS". **Only 1/7 item titles equal today's CIS day title.** Example: "Arrival in Paro and Drive to Thimphu" against CIS "Paro arrival and drive to Thimphu". The version title is also the old tour name, "Bhutan: Bumdra Trek & Valley Monasteries — 7 Days". See F1. | `01b-booking-case-tc8-1440.png`, `01c-booking-proposal-tc8-v2-1440.png`, `01d-booking-proposal-tc8-v2-preview-{1440,390}.png` |
| B2B proposal TC-000026 V1, made by the CRM's AA confirm on 30/10 | Approved, 158.54 USD. The item title is technical: "trip_plan tp:<id> · line <id>" (F3). | `01f-booking-proposal-tc26-v1-crm-1440.png` |
| Console and network | 0 console errors and 0 failing requests on every Booking page. No sideways scroll, except the preview at 390 (F2). | — |

Data: [`data/01-booking-vs-cis.json`](data/01-booking-vs-cis.json) has the per-day comparison and the proposal items against current CIS titles.

### 2. CRM: an AA line quote on a rewritten tour (Sen Vàng, owner)

Trip "Nepal, 6 đêm" (`4d6ec6d0…`, stage Inquiry, no lines before) → Bookings → **Add AA item**.

| Step | Result | Screenshot |
|---|---|---|
| Search "Tropical Jewels" in the AA catalog (the CRM's CIS cache) | One option: "Tropical Jewels: Bohol, Dumaguete and Siquijor — 6 Days · 6 days · PH". The cache title **equals** the CIS public name. `served_state: served`. | `02a-crm-add-aa-item-form-1440.png` |
| Product look-up `GET aa/products/000e3340…?currency=USD` (live from Booking) | **200**. Components: trip_plan, activity, hotel_room. "From" price 400.00 USD per person. | — |
| The whole tour, our own date 21 Nov 2026, 2 adults, sell 900.00 USD, then "Ask AA for a price" | `POST trips/{id}/aa-lines` → **201**, `supplier_kind aa`, `read_only true`, `sub_status pending`, pending `quote`. The line title is the CIS tour name. | — |
| Booking's quote | Within the poll: `sub_status quoted`. Cost 158.54 USD and sell 900.00 USD, both with fx source `aa_quote_lock`. `below_from_price false`. Actions: hold, release, requote. The row reads "AA quoted". | `02b-crm-trip-aa-quoted-{1440,390}.png` |
| The client-facing trip page of the same tour on `go-dev.` (`/trip/0c8bdf9e…`, reads CIS `/v1/trip`) | **200** at 1440 and 390. Name, summary and **12/12 itinerary lines** of the CIS text are on the page. 0 console errors, no sideways scroll. | `02c-client-trip-page-bohol-{1440,390}.png` |
| Console | The trip page logged one React #418 (hydration text mismatch) at 1440 (F4). 0 failing requests. | — |

Data: [`data/02-crm-aa-line.json`](data/02-crm-aa-line.json).

**Test data written:** one AA line on the synthetic Sen Vàng trip `4d6ec6d0…`, left at "AA quoted". It has no hold and no booking, so nothing is committed. Booking holds the matching B2B quote.

### 3. Content studio: the `master_newer` badge (Atlas & Hearth, studio-viewer)

| Check | Result | Screenshot |
|---|---|---|
| `GET /api/tenant/v1/tours/my-versions` (all pages) | **200**. 19 version rows, and every one carries `master_newer`. **Exactly 2 are true**: "Goa Honeymoon Tour — 6 Days" (version 21/10, Master 25/10) and "Golden Triangle with Ranthambore Wildlife — 8 Days" (version 20/10, Master 25/10). Both are `served`. No QA, score, gate or flag keys in the rows. | — |
| My Tours list (9 tours) | The "UPDATED BY ADVENTURE ASIA" badge appears on exactly those 2 rows, at 1440 and at 390. The tooltip reads: "Adventure Asia updated this tour on 25 Oct 2026, after your version. Your text was not changed. Rewrite it if you want the new details." | `03a-portal-tours-mine-{1440,390}.png`, `03b-portal-badge-closeup-1440.png` |
| Drawer of "Goa Honeymoon Tour" | The notice (`role=note`) shows the same sentence with a **Rewrite** button. The tenant's summary, highlights and itinerary are still their own text. | `03c-portal-drawer-master-newer-1440.png` |
| Console and network | 0 console errors and 0 failing requests. No sideways scroll at 390. | — |

Data: [`data/03-portal-master-newer.json`](data/03-portal-master-newer.json).

This closes the "portal screenshot pending" item from S252 and S253. The badge now shows on `portal.lumiguides.it.com`, which since AA-979 is served by the Fargate studio.

## Findings

- **F1 (Booking, medium): stored proposal items keep pre-rewrite text under a "FROM CIS" tag.**
  - What happens:
    - V1 and Vn items copy the CIS day titles when the version is made (`items_from_days` and the Vn copy). They never refresh.
    - TC-000008 V2 (16/10) therefore shows 6 of 7 titles that CIS no longer publishes, still tagged "FROM CIS".
    - The preview footer says CIS descriptions will join "once the catalog endpoint (GET /booking/catalog/tours) is on the Booking API". A live read already exists: `GET /booking/catalog/trip-plans/{source_id}` is what the trip-plan page uses.
  - This is a snapshot by design: a sent version is locked. But nothing tells staff that the CIS text has moved on.
  - Proposal: follow the portal's `master_newer` pattern. When `v_tour.updated_at` is later than the version's `created_at` on a draft, show "CIS updated this tour after this version" with "Refresh from CIS" (a new version). The preview could also read day bodies live by `source_tour_id`.
  - Not fixed here (read-only lane).
- **F2 (Booking, low): the proposal preview at 390 scrolls sideways.**
  - On `/cases/TC-000008/proposals/2/preview`, `main.scrollWidth − clientWidth = 257 px`. Day cards and the Overview panel are clipped on the right (`01d-…-390.png`).
  - The trip-plan page at 390 is fine (0).
- **F3 (Booking, low): B2B proposals made from a CRM AA confirm have a technical item title.**
  - On TC-000025 and TC-000026 the title reads "trip_plan tp:<uuid> · line <uuid>" and the version title "B2B crm-proposal:<uuid> v1".
  - Staff cannot see which tour was sold without opening the trip plan. The tour name is in the catalog and could be used.
- **F4 (CRM web, low): React error #418 on the trip page.**
  - A hydration text mismatch appeared on the first load at 1440 (`/pipeline/{tripId}`) and not on the 390 reload.
  - It is probably a date or time text rendered differently on the server and in the browser. The page worked.

## What was NOT tested, and why

- **A new Booking proposal made from a rewritten tour.** Making one ("Use for trip case" on the trip plan, or a new version) is a write. The only agent Booking identity is the read-only E2E staff (writes answer 403 `e2e_read_only`). By code, V1 items come from `catalog.v_tour_day` at creation time (`app/catalog/trip_plans.py` `items_from_days`), so a version made today would carry today's titles. This was not observed live. The step is in orchestrator steps.
- **Hold, confirm or release of the new AA line, and the CRM proposal builder with the AA item.** These are not needed for "an AA line quote works". Hold and confirm were covered by the AA-947 E2E spec.
- **CRM on Atlas & Hearth.** No CRM e2e user is a member of that agency, so the CRM check ran on Sen Vàng, the agency the E2E Dev workflow uses.
- **Rewrite from the master_newer notice.** It starts a paid LLM rewrite (no LLM path right now), and the identity is a studio viewer.
- **Other AA-990 items.**
  - Not in this lane: the TripPlanner parity sample (done S252), saved-trip mapping (done S252), SEO contexts (done S252).
  - Lane 1 after AA-997: the 16-tour place fixes and `recheck_14`.
  - Deferred until an LLM path exists: narrate/compose parity.
- **Light/dark variants.** Taken in the default theme only. This is a data read-back check, not a UI change.

## Screenshots

| File | What |
|---|---|
| `01a-booking-trip-plan-bumdra-overview-1440.png` | Booking trip plan Bumdra: overview (CIS summary and highlights) |
| `01a-booking-trip-plan-bumdra-days-1440.png`, `…-390.png` | Booking trip plan Bumdra: Day by day (live `v_tour_day`) |
| `01b-booking-case-tc8-1440.png` | Case TC-000008 (source cis) |
| `01c-booking-proposal-tc8-v2-1440.png` | Proposal V2 builder: stored items |
| `01d-booking-proposal-tc8-v2-preview-1440.png`, `…-390.png` | Proposal V2 customer-style preview (F1, F2) |
| `01e-booking-trip-plan-bohol-days-1440.png` | Booking trip plan of the CRM seed tour: Day by day |
| `01f-booking-proposal-tc26-v1-crm-1440.png` | B2B proposal from the CRM AA confirm (F3) |
| `02a-crm-add-aa-item-form-1440.png` | CRM "Add AA item" form on the rewritten tour |
| `02b-crm-trip-aa-quoted-1440.png`, `…-390.png` | CRM trip with the line "AA quoted" |
| `02c-client-trip-page-bohol-1440.png`, `…-390.png` | Client-facing trip page (go-dev) with the CIS v2 text |
| `03a-portal-tours-mine-1440.png`, `…-390.png` | Content studio My Tours with 2 badges |
| `03b-portal-badge-closeup-1440.png` | Badge close-up |
| `03c-portal-drawer-master-newer-1440.png` | Drawer notice with Rewrite |
