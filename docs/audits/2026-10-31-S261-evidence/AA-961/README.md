---
id: OPS-08-s261-aa961-incident-live-check
title: "S261 AA-961 live check: AA incident on a departure (Booking flag -> CRM banner + task)"
description: "Agent-run Playwright check on Dev of the AA incident path (Booking staff flag -> booking.b2b.v1 event -> CRM banner, task, Travelling-now panel), the target trip prepared for it, and the optional overlapping-traveller check."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-961, AA-975, AA-952]
---

# AA-961 live check: AA incident on a departure (S261, 31/10/2026, 09:20–09:45 +07)

Headless Chromium (Playwright, one browser at a time) against the live Dev hosts: Booking staff admin `booking.`
(AA-910 E2E staff, read-only session), CRM web + API on the agency host `portal.` (e2e **owner** of the synthetic
agency "Lữ hành Sen Vàng", partner pool, password + authenticator). Codes and secrets were read at run time and never
written down. Raw records: [`data/`](data/) (no names, no contact data; ids are Dev synthetic ids).

## Result in one line

The CRM side is ready and its baseline is proven, the Booking flag was **refused for the E2E staff (403
`e2e_read_only`, as designed)**, so **the incident itself was not raised, and the banner, the task and the clear were
not seen live**. Raising it needs a write-capable Booking staff session or a Dev seed (steps below). The optional
overlap check **passed**.

## Why a new target trip was needed

The triage example (the C-M3 trip `9ea4f816`, Booking booking `963177e5`) **cannot receive an incident**: its AA line
is a trip-plan item **on request with no departure** (`departure_id` null on the CRM line; service date 30 Nov 2026,
and the tour's Booking departures are 6, 13, 20, 27 Nov and 4 Dec). The bk-022 fan-out only addresses partners with
seats on the flagged departure, and the CRM only links an incident to trips with a line on that departure. The same is
true of Sen Vàng's other AA trip `947ec89c`. No Sen Vàng trip had an AA line on a departure.

So a target was built through the normal product flow on the synthetic agency (no DB or ECS access):

| Step | Result |
|---|---|
| `GET aa/products/<seed tour>?currency=USD` (live from Booking) | 200; departure **13 Nov 2026** (`9f7d807d…`), 2 seats free, auto-confirm |
| Inquiry form on the client host -> card -> owner takes it, dates 12–15 Nov, Qualifying, Proposal (Stage 2 by phone) | 202, then 200 each |
| Builder: booking terms in force set on the version, agency lodging night 1, AA item on day 2 **with that departure**, publish, send | 200 / 201 each; AA option `availability instant` |
| Client: Check availability (hold), accept | hold `active`, accept 200 |
| Deposit marked paid (bank transfer) | 200, trip Proposal -> **Booked** |
| Booking sync confirms the line | AA line **confirmed** on departure `9f7d807d` (Booking trip case TC-000027), trip `bb658382` |
| Booking desk, same departure | `sold 2`, `partners 1` |

A first attempt (trip `313f62c3`) was moved to **Lost** and its hold **released** (line `cancelled/released`, the
13 Nov seats back to 2 free): its builder version had no booking terms attached, so the deposit answered 409
(`terms_reaccept_required` path) and its client link had not been kept to re-accept.

## Results per Done-when line

| Done-when (triage §4 item 4 / Linear AA-961) | Result |
|---|---|
| Flag a synthetic incident on the departure of a Sen Vàng trip with an AA line via Booking staff admin "Flag incident on departure" | **Not done: refused.** The modal opens (type "Other", "1 agency is on it"); `POST /booking/b2b-desk/departures/9f7d807d…/incidents` -> **403 `e2e_read_only`**, the modal shows "You do not have access to this."; `GET …/incidents` after -> 0 incidents (nothing written). Screens `02`–`04`. |
| Banner on the Sen Vàng trip | **Baseline only.** Before any incident: `GET trips/bb658382/incidents` 200 `[]`, no `trip-incident-banner` on the trip page (1440 light/dark, 390). The banner with an open incident was **not seen**. |
| Task on the Sen Vàng trip | **Baseline only.** Trip tasks: `reply_inquiry`, `get_planning_info`, `collect_deposit:done`; no `aa_incident` task. The task after a flag was **not seen**. |
| Travelling now shows the incident | **Baseline only.** `/travelling?days=14` lists the trip (12–15 Nov, Booked, Mine), no `duty-incidents` panel; API `incidents: []`, `incident_flag_id` null; `duty/reach` on 13 Nov `incidents: []`. |
| Atlas & Hearth sees nothing | **Structural evidence only.** Booking's B2B partner registry has two rows ("Synthetic Agency 972" and "SYNTHETIC CRM sen-vang"); Atlas & Hearth is **not a partner**, so the bk-022 fan-out (one outbox row per partner with seats on the departure) cannot address it, and the departure's `partners` count is 1. No CRM e2e user is a member of Atlas & Hearth, so its CRM screens were **not opened**. |
| Clear the incident | **Not done** (nothing was raised). |
| Optional: lead traveller on a second overlapping trip -> duty list shows the traveller once with both trip ids | **PASS.** The lead of `947ec89c` was added to `9ea4f816` (both 29 Nov – 2 Dec): `GET duty/travelling?from=2026-11-29&days=7` -> that traveller **1 row**, `trip_ids [947ec89c, 9ea4f816]`, keys `traveler_id, trip_ids, regions, has_phone, has_email, has_emergency_contact, has_health_info` (no name, no contact), total travellers unchanged (4). Undone right after (DELETE 200; back to `trip_ids [947ec89c]`, total 4). API only: the page's windows stop at 14 days. |

## Not tested, and why

- **The incident itself** (Booking flag -> `departure.incident` event -> `crm.incident_flag` + urgent `aa_incident`
  task -> trip banner + Travelling panel), and **its clear** (`departure.incident_cleared` -> flag cleared, banner
  shows "cleared"). The only Booking staff identity an agent can sign in with is read-only by design (AA-910), and a
  Dev seed needs DB Migrate `run-script`, which this lane may not run. The steps are below; the check script is ready.
- **Atlas & Hearth's CRM screens**: no e2e CRM member of that agency exists; only the Booking-side structural proof
  above.
- Dark mode and 390 px of the Booking desk (staff-only page, unchanged by AA-961).

## For the orchestrator: finish the check

Target: departure `9f7d807d-1b10-4477-9136-02a7911f4875` (13 Nov 2026), Sen Vàng trip
`bb658382-cc68-4d24-91cb-7b7cdbaca598`. Scripts in `.tmp-session/S261/aa961/` (local only; MFA profile for the
secrets and the e2e mailbox).

1. Raise the incident, one of:
   - Booking admin `https://booking.lumiguides.it.com/b2b-desk?tab=departures`, row **13 Nov 2026** -> Flag incident ->
     Type **Other** -> Flag incident, as a write-capable staff user (not the E2E user). Expect "Incident flagged; 1
     agency told".
   - API with that user's WORKFORCE access token: `POST https://api-booking.lumiguides.it.com/booking/b2b-desk/departures/9f7d807d-1b10-4477-9136-02a7911f4875/incidents`
     body `{"incident_code":"other"}` -> 201, `partners_notified: 1`.
   - Dev seed, DB Migrate `mode=run-script` (master):
     `INSERT INTO booking.departure_incidents (departure_id, incident_code, flagged_by) VALUES ('9f7d807d-1b10-4477-9136-02a7911f4875', 'other', 'seed:S261-AA-961') RETURNING id;`
     (the `departure_incidents_outbox` trigger fans it out; no Booking audit row on this path).
2. Read who was told (run-script, read only):
   `SELECT p.agency_name, o.event_type, o.feed_seq IS NOT NULL AS sequenced FROM booking.outbox o JOIN booking.b2b_partners p ON p.id = o.partner_id WHERE o.departure_id = '9f7d807d-1b10-4477-9136-02a7911f4875' AND o.event_type LIKE 'departure.incident%';`
   Expect one row, the Sen Vàng partner.
3. Wait at least 60 s (`crm_booking_sync` runs every minute), then
   `cd .tmp-session/S261/aa961 && MODE=after npx playwright test -c pw.config.ts check.spec.ts`
   Expect: trip incidents 1 open (`other`), banner `role=alert`, one `aa_incident` task, the Travelling (14 days) panel
   listing the departure with trip `bb658382`; Booking `open_incident` set; screens `06-after-*`.
4. Clear: the row's **Clear incident** button, or `POST https://api-booking.lumiguides.it.com/booking/b2b-desk/incidents/<incident id>/clear`,
   or run-script `UPDATE booking.departure_incidents SET cleared_at = now(), cleared_by = 'seed:S261-AA-961' WHERE departure_id = '9f7d807d-1b10-4477-9136-02a7911f4875' AND cleared_at IS NULL;`
5. Wait 60 s, then `MODE=cleared …check.spec.ts`: no open flag, the trip banner shows it cleared (`role=status`), no
   Travelling panel; screens `07-cleared-*`.

## Findings (not blocking)

- **F1. Hydration warning on the CRM trip page:** `Minified React error #418` (text mismatch) as a page error on
  `/pipeline/<trip>` in every load of this run (S260 did not list it). The page renders and works.
- **F2. Copy:** Travelling now says "1 travellers" for one traveller (`05-baseline-travelling-14d-*`), the same kind
  of plural as S260 F4 ("1 signature pending").
- **F3. Builder proposals without booking terms:** a builder version published with no `terms_doc_id` is accepted
  without any terms acceptance, and its deposit then answers 409 until the client re-accepts; the agent cannot
  re-issue the link of an accepted version (409 `proposal_not_sent`). Worth a guard on publish (or defaulting the
  terms in force), so an agency cannot reach this state from the builder.

## Test data left on Dev (synthetic agency only)

- Trip `bb658382` (Booked, 12–15 Nov 2026) with a confirmed AA line on departure 13 Nov (Booking TC-000027, 2 seats
  sold on that departure). Kept as the incident target for steps 1–5.
- Trip `313f62c3` moved to Lost (its AA hold released).
- The overlap check was undone.

## Screenshots

| File | What |
|---|---|
| `01-trip-before-incident-1440-light.png` | New Sen Vàng trip right after the confirm: AA line confirmed on 13 Nov, no banner |
| `02-booking-desk-departures-1440-light.png` | Booking B2B desk, Departures & incidents: 13 Nov `2 sold`, 1 agency, no incident |
| `03-booking-flag-modal-1440-light.png` | "Flag incident on departure" modal, type Other, "1 agency is on it" |
| `04-booking-flag-refused-1440-light.png` | After Flag: "You do not have access to this." (403 `e2e_read_only`) |
| `05-baseline-trip-1440-{light,dark}.png`, `05-baseline-trip-390-light.png` | Trip page before any incident (party, answers, history masked) |
| `05-baseline-travelling-14d-1440-{light,dark}.png`, `05-baseline-travelling-14d-390-light.png` | Travelling now, Next 14 days: the trip listed, no incident panel |

No sideways scroll on any shot (document and `main` scrollWidth = clientWidth, 1440 and 390).

## Finished by the orchestrator (S261, 31/10/2026, 13:31–13:50 +07)

The incident was raised and cleared through two reviewed AA-CIS-Infra DB Migrate `run-script` runs of
`db/scripts/aa961_incident_seed.py` (#544, #545 fix: `flagged_by` references `booking.staff_users`, so the row is
attributed to the synthetic E2E staff user; #546 clear mode). Rows written as the app role `booking`, so the
`departure_incidents_outbox` trigger fanned the events out exactly as in production.

| Step | Result | Evidence |
|---|---|---|
| Flag (run 41177461668) | incident `a33a5d8a` `other` on departure 13 Nov; outbox 1 row `departure.incident` to **one** partner (Sen Vàng) | job log `SCRIPT` lines |
| After (`MODE=after`, 1 passed) | trip banner `role=alert` "AA reported an incident on a departure in this trip"; **one** urgent `aa_incident` task; Travelling (14 days) panel "AA reported 1 incidents" with the trip; Booking `open_incident` set; Atlas & Hearth not a partner | `06-after-*` (1440 light/dark, 390) |
| Clear (run 41177912654) | `cleared_at` set; outbox `departure.incident_cleared` to the same partner | job log |
| Cleared (`MODE=cleared`, 1 passed) | trip incidents 200 `status cleared`; banner `role=status` "… Cleared 31 Oct 2026"; Travelling panel gone, `duty/reach` 13 Nov `incidents: []`; Booking `open_incident` null. The `aa_incident` task stays open by design (CONTEXT.md: the clear closes the flag and leaves the tasks to the agent) | `07-cleared-*` |

Finding F4 (copy, not blocking): "AA reported 1 incidents" (plural for one), same kind as F2.

