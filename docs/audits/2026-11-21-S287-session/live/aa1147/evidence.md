---
id: OPS-08-s287-aa1147-live-evidence
title: 'S287 live evidence: AA-1147 agency services follow the trip'
description: "Agent-run Playwright and BFF evidence on the Dev hosts for AA-1147 (AA-Partner #374 crm-083, #375 bf663b9e with crm-084), 21/11/2026, synthetic agency only."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-21
review_every_days: 30
related: [AA-1147]
---

# S287 live evidence: AA-1147 agency services follow the trip (21/11/2026, 06:27–07:01 UTC)

Under test: AA-Partner #374 `7b4d9e3b` (crm-083 contract migration) and #375 `bf663b9e` (code, crm-084 settings rows).
CRM web `https://portal.lumiguides.it.com/healthz`: `git_sha bf663b9e8936…`, version 0.13.0, environment dev.

- Identity: the E2E owner of the synthetic agency "Lữ hành Sen Vàng" (saved UAT state, `tools/uat/lib/crm-signin.cjs`
  identity A, password + authenticator; no code was written down). CIS side: the Dev-only E2E CIS admin
  (`tools/uat/lib/signin.cjs cis-admin`, read-only session; the e-mail code was read from the e2e mailbox and never stored).
- Data made (synthetic agency only): one trip from the agency's public inquiry form for an invented prospect
  `E2E v11470zbai Agency Extras` (`@example.invalid` address), trip `d4dc902a-e01b-4e4a-857c-bad7d05307a0`; builder
  version `deee01eb-2461-46ef-a71b-e7064c15b716` (USD); one deposit invoice draft `8872f023-ec5b-4da5-be7b-9e1871e93bc0`
  (not issued). No real tenant was opened. Cost: 0 USD, no model call.
- All agency-side calls went through the CRM web's own BFF (`/bff/*`) from the signed-in page; the client accepted on
  the client host through the link (the link token was kept in a chmod-600 scratch file and deleted after the run).
  Nothing touched AWS or the database directly (AWS use: Secrets Manager read of the E2E credentials and the e2e
  mailbox read, both by the sign-in helpers).
- The CRM web was opened with the `aa_crm_locale=en-AU` cookie in the test browser (the saved state carries vi-VN);
  the member's own language setting was not changed.

| # | Done-when item | Result |
|---|---|---|
| 1 | Accept a builder version with 1 flight + 1 visa agency item through the client link; the Bookings tab shows exactly 2 planning agency lines "Handled by the agency", no deadline | **PASS** |
| 2 | "Deadline and supplier" on the flight line: set a deadline within 3 days, Save → lines API shows `due_at`; Clear deadline → `due_at` null; set again | **PASS** |
| 3 | The hourly CRM workflow tick opens an `agency_flight_due` task | **PASS** (07:00 UTC tick) |
| 4 | Invoice printable page and client page show "Services provided by Lữ hành Sen Vàng" with the visa priced and the disclaimer | **PASS** |
| 5 | CIS Platform › Settings (CRM tab) shows `crm.agency_lines.due_lead_days` = 3 and `crm.agency_lines.disclaimer` en/vi, read only | **PASS** |

## 1. Accept writes two planning agency lines: PASS

Setup through the BFF (all answered as listed):

- `POST /crm/public/v1/forms/<key>/submissions` (client host, the agency's inquiry form) → **202**; the trip card
  appeared on `GET /bff/pipeline`.
- `POST /bff/trips/{trip}/owner` → 200; `PATCH /bff/trips/{trip}` (dates +30..+33 days) → 200;
  `POST /bff/trips/{trip}/stage` qualifying → 200, proposal (`override_reason: info_by_phone`) → 200.
- `POST /bff/trips/{trip}/builder {currency: USD}` → **201**; `PATCH /bff/proposals/{id}/builder` (day 1 date, balance
  date) → 200.
- Day 1: `POST …/days/{day}/blocks {title: Flights, type: other}` → 201; `POST …/blocks/{block}/options
  {title: "Return flight Ho Chi Minh City - Hanoi", category: flight, sell 270.00, net 240.00}` → **201**.
- Day 2: `POST …/days/{day}/blocks {title: Visa, type: other}` → 201; `POST …/blocks/{block}/options
  {title: "E-visa (2 travellers)", category: visa, sell 50.00, net 30.00}` → **201**.
- Side check: an agency item on the day 1 Lodging block was refused **422** `agency_item_not_allowed` ("a lodging block
  takes Adventure Asia items only; add your flight, visa, travel insurance or the agency fee on an Other block"), as
  designed.
- `POST /bff/proposals/{id}/publish` → 200 (`status: published`, `sell_total 320.00`);
  `POST /bff/proposals/{id}/send` → **200** (`link_path` returned once, not recorded here).

Client (desktop Chromium, no sign-in): the link landed on `/c/p`; the hold box read `data-status="none"` (no AA item),
Continue, rooms + terms + full name, `POST /crm/public/v1/proposal/accept` → **200**, "accepted" panel shown.

Agency side after the accept, `GET /bff/trips/{trip}/lines` → **200**, agency lines (`supplier_kind = agency`):

| line | category | status | handled_by_agency | agency_supplier_id | due_at | bundled | option_id set | sell / cost |
|---|---|---|---|---|---|---|---|---|
| `23aefcdc…` | flight | planning | true | null | null | false | yes | 270.00 / 240.00 USD |
| `5880425e…` | visa | planning | true | null | null | false | yes | 50.00 / 30.00 USD |

Exactly 2 lines, both carrying the accepted proposal item (`option_id`). The Bookings panel (`trip-bookings`) text holds
"Handled by the agency" exactly twice, both PLANNING, Collect "By the agency", "Hidden from travellers", and a
"Deadline and supplier" button on each.

- `01a-bookings-two-agency-lines-light.png`, `01b-bookings-two-agency-lines-dark.png`

## 2. Deadline set, cleared, set again: PASS

Done in the UI ("Deadline and supplier" → the date field in the agency's DD/MM/YYYY order → Save / Clear deadline); the
browser's own PATCH and the lines API after each step:

| Step | Request (UI) | Status | `GET /bff/trips/{trip}/lines` flight `due_at` |
|---|---|---|---|
| Set (today + 2 days) | `PATCH /bff/lines/{flight}` body `{"due_at":"2026-11-23"}` | **200** | `2026-11-23T00:00:00+00:00` (GET 200) |
| Clear deadline | `PATCH /bff/lines/{flight}` body `{"due_at":null}` | **200** | `null` (GET 200) |
| Set again | `PATCH /bff/lines/{flight}` body `{"due_at":"2026-11-23"}` | **200** | `2026-11-23T00:00:00+00:00` (GET 200) |

Only the changed field was sent (no supplier or bundled key). The visa line stayed without a deadline. The flight row
now reads "Handled by the agency / Due 23 Nov 2026". Final set at 06:32:45Z.

- `02-bookings-flight-deadline-set-light.png`

## 3. Deadline task from the hourly tick: PASS

There is no manual trigger that is a normal app action (the tick is a `crm_workflow_tick` job queued once per UTC
hour), so the trip's open tasks were polled read-only, `GET /bff/tasks?scope=trip&trip_id={trip}&status=open` → **200**
every ~3.5 minutes from 06:36Z. The deadline was last set at 06:32:45Z.

- 06:36Z–06:57Z: open kinds `reply_inquiry, get_planning_info, collect_deposit` (no agency task before the tick).
- 07:01:08Z: `agency_flight_due` present. Task `c3586e04-51ae-44f2-b317-24844a970a4b`, `created_at
  2026-11-21T07:00:20Z` (the 07:00 tick), `priority urgent`, `status open`, `source system`,
  `due_at 2026-11-23T00:00:00+00:00` (= the line's deadline), `booking_line_id 23aefcdc…` (the flight line),
  `line_title "Return flight Ho Chi Minh City - Hanoi"`, assigned to the trip owner (the E2E owner).
- Only the flight line had a deadline, so no `agency_visa_due` task was opened (as designed).
- The trip's Tasks panel shows "URGENT Issue the flight ticket before its time limit · due 23 Nov 2026, 7:00 am GMT+7".

- `03-trip-task-agency-flight-due-light.png`

## 4. Invoice printable page and client page: PASS

Client page (before the accept, desktop light and dark), section `client-agency-services`:
"Services provided by Lữ hành Sen Vàng — Return flight Ho Chi Minh City - Hanoi 270.00 USD — E-visa (2 travellers)
50.00 USD", then the disclaimer "These services are arranged and provided by the agency named above, which is
responsible for them. Airline, visa and insurance terms are those of the airline, the issuing authority and the
insurer." The section is still on the page after the accept (count 1).

Invoice: on the trip's Invoices card, the deposit schedule row's invoice button sent
`POST /bff/trips/{trip}/invoices {schedule_id}` → **201** (deposit, total 96.00 USD, draft). `GET /bff/invoices/{id}` → 200
with lines:

| source | kind | description | amount |
|---|---|---|---|
| schedule | charge | Deposit (proposal version 1) | 96.00 |
| agency_line | included | Return flight Ho Chi Minh City - Hanoi | 270.00 |
| agency_line | included | E-visa (2 travellers) | 50.00 |

The agency services are listed but not summed (total = the one charge). `GET /bff/invoices/{id}/document` → **200**; the
HTML holds "Services provided by Lữ hành Sen Vàng", both rows with USD 270.00 / USD 50.00 and the disclaimer under them.
The "Printable invoice" button opened that page as a `blob:` window. The invoice has no separate PDF route (the BFF
allows only `invoices/{id}` and `invoices/{id}/document`); the printable page is the browser-printable form. It is a
print document with no dark theme, so only the light capture is kept.

- `04a-client-page-agency-services-light.png`, `04b-client-page-agency-services-dark.png`
- `04c-invoice-printable-agency-services-light.png`

Observation (not a failure): on the client page each single-option block shows "Included" on the flight and the visa
card (the item is in the total), while the group below prices them (270.00 / 50.00 USD). The total 320.00 USD is right;
the two labels may read as contradictory to a traveller.

## 5. CIS Platform › Settings, CRM tab: PASS

`https://aa-cis.lumiguides.it.com/admin/platform/settings?app=crm&area=agency_lines` as the E2E CIS admin;
`GET /api/admin/settings/registry?app=crm` → **200**, `can_write: false`, `reader_error: null`. Area "Agency lines 2":

| key | value in force | default | type / allowed | scope |
|---|---|---|---|---|
| `crm.agency_lines.due_lead_days` | 3 (days) | 3 | int, 0–60 | platform+tenant, 0 agency values |
| `crm.agency_lines.disclaimer` | `{"en": "These services are arranged and provided by the agency named above, …", "vi": "Các dịch vụ này do đại lý nêu trên sắp xếp, cung cấp và chịu trách nhiệm. …"}` | same | json | platform+tenant, 0 agency values |

The page shows "You can read the CRM settings. Changing or approving them needs the CRM platform administrator group
(crm-platform-admin)" (`settings-crm-read-only`). Both rows read "Never changed" with the value marked "default".

- `05a-cis-settings-crm-agency-lines-light.png`, `05b-cis-settings-crm-agency-lines-dark.png`,
  `05c-cis-settings-crm-disclaimer-light.png`

## Left on Dev

The synthetic trip, its version (accepted) and the draft deposit invoice and the open `agency_flight_due` task stay on the
synthetic agency as reference; nothing was issued or paid. Screenshots were compressed with `tools/docs/compress_images.py`; they show
only invented names (prospect, agency) and the E2E admin's display name, no e-mail address, link token or code.
