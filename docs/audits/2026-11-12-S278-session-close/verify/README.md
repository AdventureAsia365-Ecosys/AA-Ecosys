# S278 live verification: AA-1069, AA-1070, AA-1080, AA-1079

Date: 12/11/2026 (S278), Dev only. CRM API `/crm/health` reported `git_sha 066560e711126e0eade58134d80691b0082a5444`
(the expected `066560e7…`) before the run.

How it ran: local Playwright scripts (`scripts/`, Playwright from `apps/AA-Partner/e2e/node_modules`), one browser at a
time.

- **CRM:** signed in on `portal.lumiguides.it.com` as the synthetic E2E agency owner (`sen-vang-owner`, agency "Lữ hành Sen
  Vàng", partner pool, password + authenticator). The identity was read into memory from Secrets Manager. The scripts
  called the CRM BFF (`/bff/...`) from the signed-in page and also drove the web UI.
- **Content studio:** used the E2E `harbour-lights-owner`. It has editor membership on the audit tenants since S270. The
  run chose the studio **"Atlas & Hearth (Audit)"** (`audit-atlas-hearth`) in the chooser.
- **CIS admin:** used the Dev-only E2E CIS admin (`e2e-cis-admin@e2e-mail…`, root ADR 0006a A10b). It signed in with an
  e-mail code read from the e2e mailbox `inbound-admin/`. The role is read-only on Route control.

No password, authenticator secret, sign-in code, cookie, token or portal link appears in this folder. No storage state
was saved.

Every record written used names with "E2E" and `.invalid` e-mail addresses. The agency mailbox of the synthetic agency
is **disconnected**, so outgoing mail is held, and nothing was delivered.

Folders: `shots/` (screenshots), `raw/` (JSON responses and state, with secrets and links redacted), `scripts/` (the
runs).

## AA-1069: agency service catalogue (crm-23) and supplier booking requests (crm-24)

Synthetic trip: a new inquiry from the public form (`go-dev`, lead "E2E s278sbnml Catalogue",
`e2e.catalogue.s278sbnml@example.invalid`, Vietnam, 4 nights, 2 adults), trip `851ce184`.

| Item | Steps | Result | Evidence |
|---|---|---|---|
| Create E2E own supplier with a `.invalid` contact | `POST /bff/suppliers` (flight, "E2E s278sbnml Air Desk", `e2e.airdesk.s278sbnml@example.invalid`) | PASS: 201, `has_contact_email: true` | `raw/aa1069-setup-log.json` |
| Service 1: flight, per_person, net 80 / sell 100 USD, linked to the supplier | `POST /bff/services` | PASS: 201, `qty_basis per_person`, `unit_net 80.00`, `unit_sell 100.00`, `supplier_name` set | `raw/aa1069-setup-log.json`, `shots/aa1069-services-{1440,390}-{light,dark}.png` |
| Service 2: fee, per_booking (no supplier, agency's own fee, sell 25) | `POST /bff/services` | PASS: 201 | same |
| Services page | `/services` | PASS: both rows (Price, Cost, Counted, Offered); cards at 390; no sideways scroll; no console errors | `shots/aa1069-services-*.png` |
| Builder draft on the trip | `POST /bff/trips/{id}/builder {currency: USD}` | PASS: 201, Stage 2 skeleton, `room_config [double, 2 adults]` | `raw/aa1069-setup-log.json` |
| Add from catalogue (UI): flight into a "Flights" block | builder → "+ Add" → Catalogue → pick the flight → "Add to this block" | PASS: preview "2 x 100.00 USD = 200.00 USD · Supplier cost per unit: 80.00 USD"; `POST …/catalogue-options` 201; the option is `sell_amount 200.00` (= 100 × qty 2 = party travellers), `net_amount 160.00`, title "… Flight HAN-SGN x 2", supplier kept | `shots/aa1069-builder-catalogue-tab-1440-light.png`, `shots/aa1069-builder-after-add-1440-light.png`, `shots/aa1069-builder-{1440-light,390-dark}.png`, `raw/aa1069-state.json` |
| Add from catalogue: per_booking fee | `POST /bff/proposals/{id}/blocks/{block}/catalogue-options` | PASS: 201, `sell_amount 25.00` (qty 1), `net 0.00` | `raw/aa1069-flow-log.json` |
| Planning agency line for the E2E supplier | `POST /bff/trips/{id}/lines` | PASS: 201, status `planning` | `raw/aa1069-flow-log.json` |
| Per-supplier drafts (UI) | trip page → "Request from suppliers" → "Prepare e-mails" | PASS: `POST …/supplier-requests` 200, exactly 1 draft, for "E2E s278sbnml Air Desk" (dates, 2 adults, 1 room, traveller name; text in the agency language, Vietnamese) | `shots/aa1069-supplier-requests-drafts-1440-light.png` |
| Send one draft | "Send to E2E … Air Desk" | PASS: `POST …/supplier-requests/send` 202; line → `requested` (`requested_at`, `request_ref` = message id). The message sits in Messages as held (`held_count 1`, mailbox disconnected), and nothing was delivered | `shots/aa1069-supplier-request-sent-1440-light.png`, `shots/aa1069-line-requested-1440-light.png`, `raw/aa1069-confirm-log.json` |
| Type a confirmation number → confirmed | "Record confirmation" with `E2E-S278SBNML` | PASS after the line money was set: the first try answered **409** because the agency's Booking validation is "Basic" ("Fill these in before confirming: cost, sell price"). After `PUT /bff/lines/{id}/money` (cost 160 / sell 200 USD) the UI confirm answered 200: status `confirmed`, `confirmation_no E2E-S278SBNML`. This is expected behaviour under the validation setting, not a fault | `shots/aa1069-line-confirmed-1440-light.png` |
| `GET /bookings?status=requested` | BFF call + the Bookings page "Requested" filter | **FAIL (still open from S277).** API 422 `literal_error`: "Input should be 'planning', 'confirmed' or 'cancelled'" (`app/routers/ledger.py get_bookings`, the `status` Literal lacks `requested`). The web Bookings page offers a "Requested" filter (`STATUSES` includes it), and `/bookings?status=requested` renders "The CRM service is not answering right now. Try again in a minute." | `shots/aa1069-bookings-requested-filter-1440-light.png`, `raw/aa1069-flow-log.json` |
| Bookings page (all) | `/bookings` | PASS: renders; no sideways scroll at 390; no console errors | `shots/aa1069-bookings-{1440,390}-{light,dark}.png` |

AA-1069 summary: **12 PASS / 1 FAIL**. The FAIL is the `requested` status filter on `GET /bookings`, in both the API and
the Bookings page.

### AA-1069 clean-up

| Record | Action | State at the end |
|---|---|---|
| Services (flight, fee) | `DELETE /services/{id}` | deleted; `GET /services` → `[]` (as at the start) |
| Trip `851ce184` (with its builder draft) | `DELETE /trips/{id}` | in Trash (purge 19/11) |
| Lead traveller "E2E s278sbnml Catalogue" | `DELETE /travelers/{id}` | in Trash (purge 19/11) |
| Booking line `cb1f47ed` | cancel 200; trash → 409 `line_not_editable` (only a planning line is deleted) | **cancelled** (stays with the trashed trip) |
| Supplier "E2E s278sbnml Air Desk" `2be5cbbe` | trash → 409 `supplier_in_use` (the cancelled line names it); moving the line to another supplier → 422 | **left in place, still active**: it is E2E-named with a `.invalid` contact. It can be trashed once the trip purge removes the line. The 422 message says "the supplier of a confirmed line does not change" for a *cancelled* line (wording) |
| Held supplier e-mail (conversation `c6b05da6`) | the 10 s Undo window had passed | held in the disconnected mailbox, addressed to `.invalid` |

The board went back to 38 inquiry cards, and the services catalogue went back to empty. The only additions left are one
cancelled line and one E2E supplier, as listed above.

## AA-1070: CRM travel ops (six shipped items)

Trips used:

- **T:** the S277 Book now trip `9f0976dc` (booked, 2 adults + 1 child, departure `824ac043` 20–25 Nov, room config 1
  × family). Only the lead has a traveller record.
- **R:** booked E2E trip `18c61c49` ("E2E S261 Lead vwye3w", 3 traveller records). It was needed because T has a single
  traveller, so T cannot exceed a room's capacity.

| Item | Steps | Result | Evidence |
|---|---|---|---|
| crm-22 departure list | `GET /bff/departures?scope=upcoming`, `/departures` page | PASS: 200, 4 AA departures with trips/pax/feed state | `shots/aa1070-departures-{1440,390}-{light,dark}.png` |
| crm-22 roster | `GET /bff/departures/824ac043…/roster`, `/departures/{ref}` page | PASS (API): 200, 1 trip, pax 2+1, state `scheduled`, the traveller with passport/room checks. **UI FAIL (minor): sideways scroll at 390** (light and dark). The roster card's "Trip" row (long tour title) pushes the page to 458 px wide | `shots/aa1070-roster-{1440,390}-{light,dark}.png` (the 390 images are 458 px wide) |
| crm-22 manifest CSV | `POST /bff/departures/{ref}/manifest {}`; then with `fields [name, dietary]` and no reason | PASS: 200 `{filename departure-…-AADEP-….csv, watermark, row_count, fields, reason, csv}`, header `watermark,no,name,trip_ref,age_band,room`, 1 row. A health field without a reason → 422 `reason_required` (threshold 5, reasons listed) | `raw/aa1070-run-log.json` (header and row count only) |
| crm-20 vouchers (agency) | `GET /trips/T/vouchers`; added an own-supplier agency line "E2E S278 airport transfer (voucher check)" (visible to travellers), money 10/15 USD, confirm (`E2E-S278-V1`), `PUT /lines/{id}/voucher` (pick-up, drop-off, 08:30, note) | PASS: AA line voucher `released: false` (`line_hidden`); the new line's voucher `released: true` with the details; `GET /lines/{id}/voucher` 200 | `shots/aa1070-trip-travel-panel-{1440,390}-{light,dark}.png` |
| crm-20 vouchers (client portal) | `POST /bff/trips/T/portal-access` 201 → the traveller link on `go-dev` → dev-echo sign-in code → portal | PASS: `GET /crm/public/v1/traveller/travel` 200 `{vouchers, voucher_header, rooming, visas}`; the "Vouchers" section shows the transfer voucher (pick-up, drop-off, time, confirmation no., "Print or save as PDF"), Rooms and Visa documents; no sideways scroll at 390; no console errors | `shots/aa1070-portal-travel-{390-light,390-dark,1440-light}.png` |
| crm-21 server PDFs | `POST /bff/trips/T/pdfs {kind: confirmation}` and `{kind: voucher, booking_line_id}` | PASS: both 202 `{queued: true, document_kind}`; within one 5 s poll both documents were in `GET /trips/T/documents` (`confirmation-9f0976dc.pdf` 214,517 B `confirmation_pdf`; `voucher-0FEE253C.pdf` 214,387 B `voucher`); `POST /documents/{id}/download` 200 | `raw/aa1070-run-log.json`, `raw/aa1070-cleanup-log.json`; the PDF buttons are in the travel panel shots |
| crm-17 rooming list | R: `PUT /trips/R/rooming` with 3 travellers in a double; then a triple. T: a single room (config says family); then a family room | PASS: double → **422 `room_over_capacity`** "a double room takes 2"; triple → 200. T single → 422 `rooms_not_in_proposal`; family → 200. Portal shows the room | `raw/aa1070-run-log.json`, travel panel + portal shots |
| crm-15 passport check | `GET /trips/{T,R}/passports` | PASS: 200; each traveller is `{traveler_id, role, status}` only (`missing` here: no expiry on file); body has `valid_months`, `valid_until_needed`, `issues`; **no expiry date, passport number or nationality** in either body | `raw/aa1070-state.json` (`passport_T`, `passport_R`) |
| crm-16 visa templates | `POST /bff/visa-templates` (PH e-visa, 2 E2E documents, official URL `example.invalid`) as owner; `/settings/travel` page | PASS: 201; listed; Settings > Travel renders (passport months 6, visa guidance) with no sideways scroll | `shots/aa1070-settings-travel-{1440,390}-{light,dark}.png` |
| crm-16 visa tracker | suggestions T and R; `POST /trips/T/visas` (lead, PH, template, deadline 18 Nov); add checklist item; tick; status `collecting` | PASS: 201 (checklist seeded from the template + 1 added), tick 200, PATCH 200; the panel shows "PH · E-visa · Collecting documents · Ready by 18 Nov 2026 · 1/3 documents"; the portal shows the visa checklist. Suggestions: T → `[]` (the Book now trip has no destinations and no nationality on file); R → `VN` per traveller with `nationality_known: false` | travel panel + portal shots, `raw/aa1070-run-log.json` |

AA-1070 summary: **10 PASS / 1 FAIL**. The FAIL is minor: the roster page at 390 px scrolls sideways.

Observation (not judged): the departure page's money card shows revenue 90.00 USD and costs 229.03 USD (profit
-139.03). Revenue counts only the invoiced deposit, while costs include AA's net and the partner commission from S277.

### AA-1070 restore / clean-up

All restored except one cancelled synthetic line on T:

- the visa application and the visa template were deleted (`GET /visa-templates` → `[]` as at the start);
- both rooming lists were set back to `[]`;
- both PDFs were trashed;
- the voucher line `0fee253c` was **cancelled**. Confirmed lines cannot be deleted, so it stays on T as cancelled;
- the new portal access `5691c14f` was revoked. Issuing it had already revoked the earlier S277 link, which was used;
- Settings > Travel was untouched (`passport_valid_months 6`).

The portal invite queued a transactional e-mail to the lead's synthetic address, held by the disconnected mailbox.

## AA-1080: Content studio Brand Identity of audit-atlas-hearth

Studio: "Atlas & Hearth (Audit)", Brand Identity version 3 (updated 11 Nov 2026). Read only, nothing saved.

| Item | Result | Evidence |
|---|---|---|
| Target Markets market note | PASS: the field shows "US, UK, UAE, Saudi Arabia, Singapore, Hong Kong". Below it, the amber note "Search data for your markets" reads: "Tour page keywords use United States search data (the first market you listed that we cover)", then one line each for UAE, Saudi Arabia, Singapore and Hong Kong: "no search data for this market yet. Your content uses United States search data until it is added; we have recorded the request." API: `markets.unsupported [AE, SA, SG, HK]`, each `reason no_search_data, uses US`; `seo_market US`; `defaulted false` | `shots/aa1080-brand-{1440,390}-{light,dark}.png`, `shots/aa1080-brand-marketnote-{1440,390}-{light,dark}.png`, `raw/aa1080-brand.json` |
| Partly-unsupported banner | PASS: the market note switches to the amber "warning" style when some markets are unsupported (the same box as above). The post-save line "… research not available yet for AE, SA, SG, HK" shows only after a save, so it was not triggered (no write) | same |
| Brand context filled | PASS: 747 / 2000 characters ("Write as Atlas & Hearth, luxury cultural travel brand. Core idea: …"), also in "How we use this" | `shots/aa1080-brand-context-{1440,390}-{light,dark}.png` |
| Default CTA filled | PASS: "Get in touch with Atlas & Hearth to plan this trip." | `shots/aa1080-brand-cta-{1440,390}-{light,dark}.png` |
| Layout | PASS: no sideways scroll at 390, light and dark; no console or network errors | `raw/aa1080-brand.json` |

AA-1080 summary: **5 PASS / 0 FAIL**. The studio page scrolls inside its own main area, so the full-page shots show the
top of the page. The Brand context and CTA shots are viewport shots after scrolling to each field.

## AA-1079: CIS admin, AI gateway, Route control

| Item | Result | Evidence |
|---|---|---|
| Route version 8 | PASS: the header shows "VERSION 8" and `GET /api/admin/ai-gateway/route-control` returns `version 8`, `order_mode model_first`, `updated_by admin:claude-code-s277` | `shots/aa1079-route-control-top-1440-{light,dark}.png`, `shots/aa1079-route-control-{1440,390}-{light,dark}.png` |
| Preset serving_first | PASS: version 8 is "In force", action "Preset", 3 changes, with the note "AA-1079 S277: serving model first on t2_judge / t7_debate_judge / t10_judge while the acc3 rungs refuse". The versions API gives `preset: "serving_first"`; the table shows the action "Preset" and not the preset key | `shots/aa1079-route-versions-1440-{light,dark}.png`, `raw/aa1079-route-versions.json` |
| Judge chains, serving model first | PASS: t2_judge, t7_debate_judge and t10_judge each list Primary "GPT-6 Luna (OpenAI API)", then GPT-5.6 Luna (Bedrock, acc3), then GPT-6 Luna (Bedrock, acc3) | `shots/aa1079-stage-{t2_judge,t7_debate_judge,t10_judge}-1440-{light,dark}.png`, `raw/aa1079-route-control.json` |
| Layout / errors | PASS: no sideways scroll at 1440 or 390, light or dark; no console or network errors; the role is read only ("your role can see the routes but not change them") | `raw/aa1079-route-control.json` |

AA-1079 summary: **4 PASS / 0 FAIL**.

## Console and network errors seen

- **CRM:** the only 4xx were ones the checks provoked on purpose:
  - `GET /bff/bookings?status=requested` 422 (the finding above);
  - the first confirm 409 (Booking validation);
  - `GET /bff/lines/{id}/confirm-check` 404 and `GET /bff/trips/{id}/conversations` 404. Both are routes my probe called
    that are not on the BFF allow-list or do not exist; the UI does not call them;
  - the deliberate 422s for rooming capacity, the rooming config and the manifest reason.
- **CRM UI page loads, Content studio, client portal, CIS admin:** none.
- **The one visible page error:** the Bookings page "Requested" filter, which renders the "CRM service is not answering"
  state.

## Not tested, and why

- **Real supplier delivery and threaded supplier replies:** the synthetic agency's mailbox is disconnected, and the
  address is `.invalid` on purpose. The request was queued and held, so no reply could arrive.
- **Supplier tiers (per-party-size unit net) and currency conversion of a service:** not in the brief, not exercised.
- **Visa suggestions with a template match:** the trips have no traveller nationality on file (`nationality_known:
  false`), and T has no destinations.
- **The roster with more than one trip, and a manifest with a reason (more than 5 travellers):** the chosen departure
  has 1 trip and 1 traveller record. The reason rule was checked through the health-field path.
- **The PDF bytes:** each document's existence, kind, file name and size (~214 KB) were checked, and the download
  answered 200. The file was not opened.
- **The post-save Brand Identity line "research not available yet for …":** it needs a save, and this run was read only.

## Re-verify after #285

AA-Partner #285 deployed: `/crm/health` reported `git_sha d63ad21174cc4b06f3b94893974bb7b79f66cc8b`. The run used the
same E2E agency owner sign-in (`scripts/reverify285.mjs`, output `raw/reverify285.json`). It made no writes, apart from
one refused PATCH.

| Check | Result | Evidence |
|---|---|---|
| `GET /bff/bookings?status=requested` | PASS: 200, 0 lines (empty list). The only S278 requested line was confirmed and then cancelled earlier, so none is in `requested` now | `raw/reverify285.json` |
| `GET /bff/bookings?status=booked` | PASS: 422 `literal_error` "Input should be 'planning', 'requested', 'confirmed' or 'cancelled'" | `raw/reverify285.json` |
| Web `/bookings?status=requested`, 1440 + 390, light + dark | PASS: the page renders totals, the filter links and the empty state "No booking lines yet." It no longer shows "The CRM service is not answering right now". No console or network errors; scrollWidth 1440 / 390 | `shots/aa1069-requested-{1440,390}-{light,dark}.png` |
| PATCH the cancelled S278 line `cb1f47ed` to another own supplier (`5e1eace4`) | PASS: 422 `line_not_editable`, message "this line is cancelled; its supplier does not change" (no "confirmed") | `raw/reverify285.json` |
| Roster `/departures/824ac043…` at 390×844, light + dark | PASS: document scrollWidth 390, equal to the viewport (was 458). The Trip value "Tropical Jewels: Bohol, Dumaguete and Siquijor — 6 Days" wraps to 2 lines (height 40 px, right edge 342 px). No console errors | `shots/aa1070-roster-fixed-390-{light,dark}.png` |
| Roster at 1440, light + dark | PASS: unchanged desktop table (Traveller / Trip / Details / Passport / Room); scrollWidth 1440 | `shots/aa1070-roster-fixed-1440-{light,dark}.png` |

Re-verify summary: **6 PASS / 0 FAIL**.

The E2E supplier "E2E s278sbnml Air Desk" is left as it is; it purges with the trashed trip on 19/11.

Observation: with a status filter and no matching lines, the empty state says "No booking lines yet." A filter-aware
wording such as "No requested lines" would be clearer. This is copy only, not a failure.

## AA-1081: Blog topics note on Create > Articles (four audit studios)

The check was read only. The account was `harbour-lights-owner` (editor on the four "(Audit)" studios), and the page
was `/portal/create/article` with the Blog tab, which is the default. No refresh, "Update topics", pick, cut or generate
control was pressed. The only clicks were the studio chooser and the note's client-side "Show all" toggle.

`GET /v1/slate` enqueues a `t7_slate` job only when the last successful proposal is more than 24 h old. All four
tenants had a successful run from 12/11 00:14–00:56Z, so the call only read. Every `GET /api/tenant/v1/slate` answer
during the run had `refresh {status: "succeeded", refreshing: false}`, with the same `finished_at` before and after the
reloads. **No job was started.** Script: `scripts/a1081_topics.mjs`; output: `raw/aa1081-topics.json`.

| Studio | Slate run (`refresh.finished_at`) | Note title | Tours without a topic and their reason (as shown) | Evidence |
|---|---|---|---|---|
| Terra Family Expeditions (Audit) | 00:28:19Z | "2 of your 12 tours have no article topic yet" | Khovsgol and Gobi Tour, Mongolia — 15 Days: **low_search_interest**, shown as "Too few people search for this tour's places yet to carry an article. It still gets social post topics." Rajasthan Palaces, Forts & Tiger Reserves — 15 Days: **not_ready**, shown as "Topics for this tour are still being prepared. Check again after the next update." | `shots/aa1081-blog-topics-terra-{1440,390}-{light,dark}.png` (the note), `shots/aa1081-blog-topics-terra-page-{1440,390}-{light,dark}.png` (page) |
| Atlas & Hearth (Audit) | 00:14:08Z | "1 of your 13 tours has no article topic yet" | Rajasthan Palaces…: **not_ready** | `shots/aa1081-blog-topics-atlas-1440-light.png`, `…-atlas-page-1440-light.png` |
| Trail Pulse (Audit) | 00:42:42Z | "1 of your 12 tours has no article topic yet" | Rajasthan Palaces…: **not_ready** | `shots/aa1081-blog-topics-trail-1440-light.png`, `…-trail-page-1440-light.png` |
| WildKind Travel (Audit) | 00:56:17Z | "1 of your 12 tours has no article topic yet" | Rajasthan Palaces…: **not_ready** | `shots/aa1081-blog-topics-wildkind-1440-light.png`, `…-wildkind-page-1440-light.png` |

| Check | Result |
|---|---|
| Typed reasons shown | PASS: `not_ready` on each of the four tenants and `low_search_interest` on Terra Family, 5 in total (not_ready 4, low_search_interest 1), as expected. Each reason is shown in plain words, never as the code |
| No score / bar / "Debate" wording | PASS: the note text has no "score", "bar", "debate", "threshold" or "Jev", and the Articles page has no "Debate". The Slate rows show search volume ("~2,400 searches a month"), which is the existing Slate design and not part of the note |
| Console / network errors | PASS: none on any of the four studios |
| Sideways scroll | PASS: none at 1440 or 390, light or dark (Terra Family in all four modes; the others at 1440 light) |

AA-1081 summary: **4 PASS / 0 FAIL**. Only Terra Family was shot in all four modes, because it is the one with both
reasons. The other three studios carry the same single `not_ready` row and were shot at 1440 light.

## AA-1070 crm-35 / crm-13 (after 9b52cf06)

CRM API and web both run image `9b52cf061c68beed97316eea87395ebed88f0491` (`/crm/health`; ECS `aa-crm-dev-web:139`,
`aa-crm-dev-api:159`, rollout COMPLETED; read-only describe calls). `/crm/health/ready` → `schema_version crm-060`.
The agency was the same synthetic one (Sen Vàng owner). Scripts: `scripts/c35_run.mjs`, `scripts/c35_send.mjs`,
`scripts/c35_cleanup.mjs`, `scripts/c13_check.mjs`; outputs `raw/c35-*.json`, `raw/c13-check.json`.

### crm-35: included / not included lists

Synthetic trip: a new inquiry "E2E s278i52rv Inclusions" (`.invalid` e-mail), trip `e519c16e`, builder v1 `0c37b213`
with the AA seed tour (Tropical Jewels, trip_plan, sell 1500 USD, day 1 = 11 Dec 2026).

| Check | Result | Evidence |
|---|---|---|
| Settings > Proposal lines page `/settings/inclusions` | **FAIL**: the page answers HTTP 500 "This page couldn't load", at 1440 and 390, light and dark. Web log (`/ecs/aa-crm-dev`, digest 7797940): `Error: not on the BFF allow-list: GET inclusion-items?archived=true`. The page calls `crmCall(..., "GET", "inclusion-items?archived=true")` server-side. The allow-list entry in `web/lib/bff.ts` is `/^inclusion-items$/`, and the server-side check matches the path with the query string, so it throws. (The browser BFF path strips the query and works.) Console: 500 + React error #441 | `shots/aa1070-crm35-settings-{1440,390}-{light,dark}.png` (the error page) |
| Library writes (through the BFF, since the page is down) | PASS: 2 Included (one with VI) + 1 Not included → 201 ×3; archive one → PATCH 200 `archived: true`; the list with `archived=true` shows all 3 | `raw/c35-run-log.json` |
| Archived line cannot be picked | PASS: `PUT /proposals/{id}/inclusions` with the archived id → 409 `inclusion_item_archived`; the panel's "From your library" offers only the live included line | same |
| Builder panel (UI): pick, type, reorder, save | PASS: picked the library Included and Not included lines; typed an Included line (EN + VI) → "Typed for this proposal" badge; moved the typed line up (order before: library, typed → after: typed, library); "Save lines" → PUT 200. The saved lines are `custom` / `library` with the EN + VI texts | `shots/aa1070-crm35-panel-draft-{1440,390}-{light,dark}.png`, `raw/c35-state.json` (`reorder`, `draft_lines`) |
| AA tour block is read-only | PASS: "From the tour Tropical Jewels…" under each list (4 included and 1 not-included line from the CIS content), with no buttons in the block | same shots (`aa_block_buttons: 0`) |
| Publish → frozen | PASS: publish 200 → `published`; the AA lines are copied as `aa_tour`; `PUT …/inclusions` → **409 `proposal_not_draft`**; `PATCH …/builder` → 409 `proposal_not_draft`; the panel shows "This version is published: its lists no longer change." read-only | `shots/aa1070-crm35-panel-published-{1440,390}-{light,dark}.png` |
| E-mail / WhatsApp text | PASS: 200. The text follows the agency locale (vi): "Đã bao gồm" (typed VI line, library VI line, then the AA tour's lines under its title), "Chưa bao gồm" (library line in EN, which has no VI, then the AA tour's line), after the days and before "Giá" | `raw/c35-state.json` (`text_email.excerpt`) |
| Proposal PDF | PASS: `POST /trips/{id}/pdfs {kind: proposal}` 202 → `proposal-e519c16e-v1.pdf` (215,420 B, `proposal_pdf`) appeared; download 200, `application/pdf`, starts `%PDF-`. The PDF renders the e-mail text above, so the lists are in it. Its text was not extracted (embedded CID font) | `raw/c35-state.json` |
| Client page `/c/p` (EN) | PASS: send 200 (after moving the trip to Proposal with override reason `other`); the link was exchanged and removed from the address bar (`/c/p`). "What's included": typed line, library line, AA tour block; "Not included": library line, AA tour block. No console errors; no sideways scroll | `shots/aa1070-crm35-client-en-{1440,390}-{light,dark}.png` (the section), `shots/aa1070-crm35-client-en-page-*.png` (full page) |
| Client page (VI, cookie `aa_crm_locale=vi-VN`) | PASS: "Đã bao gồm" / "Chưa bao gồm" with the VI texts where they exist (EN otherwise); no sideways scroll | `shots/aa1070-crm35-client-vi-{1440,390}-light.png` |

crm-35 summary: **8 PASS / 1 FAIL** (the Settings page). Observations, not judged:

- **The AA tour's lines are broken at hard line breaks.** The CIS content splits one sentence into several bullets ("Accommodations as indicated / Meal as indicated / Transfer and" | "Sightseeing tours / Boat rides / …"). The panel, the client page and the text all show these fragments. This is a source-data issue in `crm.aa_catalog_tour.body.inclusions`.
- **The e-mail text shows a due date in the past:** "Đợt thanh toán 1 … hạn 12/10/2026", from the default schedule of 60 days before an 11 Dec start.

**Clean-up:**

- the proposal was withdrawn (200), so the client link is dead;
- the PDF was trashed;
- all 3 library lines were deleted, so `GET /inclusion-items?archived=true` → `[]`, as at the start;
- the trip and its lead traveller are in Trash (purge 19/11);
- the board is back to 38 inquiries.

The send queued an e-mail to the `.invalid` lead, held by the disconnected mailbox.

### crm-13: AA cancelled a departure

| Check | Result | Evidence |
|---|---|---|
| `GET /bff/pipeline?issue=aa_cancelled` | PASS: 200, 0 cards (no open case on this agency). An unknown `issue=nonsense` → 422 | `raw/c13-check.json` |
| Board with the filter (`/pipeline?issue=aa_cancelled`) | PASS: the "AA cancelled" chip is active and every column says "No trips in this stage."; no sideways scroll; no console errors | `shots/aa1070-crm13-pipeline-filter-{1440,390}-{light,dark}.png` |
| Trip page without a case | PASS: the S277 booked trip (AA line on departure 824ac043) and the crm-35 trip render `crm-trip` with no `aa-cancel-case` card and no "AA cancelled" text | `shots/aa1070-crm13-trip-no-case-1440-light.png` |
| `POST /trips/{id}/aa-cancel/{unknown case}/requote` | PASS: **404 `aa_cancel_case_not_found`** on both trips (not 500). A malformed body → 422 (`string_pattern_mismatch`, `date_from_datetime_parsing`) | `raw/c13-check.json` |

crm-13 summary: **4 PASS / 0 FAIL** for what can be reached.

**Not tested, and why:** the flow starts from a Booking `departure.cancelled` feed event. The Booking E2E staff
identity is read-only and cannot cancel a departure, and forging a feed event was ruled out. These parts were therefore
not exercised:

- opening a case, the owner task `aa_departure_cancelled` and the workflow event;
- the card and its two actions: re-quote onto another departure (new version, or new trip for an accepted one), and
  cancel at no charge (charge waived, refunds prefilled);
- the board badge on a flagged trip;
- the idempotence on a replayed event.

## Batch after CRM 96e1fd9d / CIS 13e024d0 (AA-1070 #288, AA-1088, AA-960)

Versions checked first:

- CRM web `/healthz` → `git_sha 96e1fd9d7374e15385a283137ee4a27b9c12f615`;
- CRM API `/crm/health` → `96e1fd9d…`;
- CIS API `/health` → `13e024d090a9de7fae28f9fec64731409ae3e3aa`.

### AA-1070 #288: Settings > Proposal lines

| Check | Result | Evidence |
|---|---|---|
| `/settings/inclusions` loads | PASS: document 200, `crm-inclusion-settings` rendered, no "This page couldn't load", at 1440 and 390, light and dark; no sideways scroll; no console or network errors | `shots/aa1070-r288-settings-inclusions-{1440,390}-{light,dark}.png` |
| Add one line in the UI, delete it again | PASS: "Add line" (Not included, "E2E s278r288 Travel insurance (settings check)") → POST 201, the row shows; "Delete" → DELETE 200; the library is back to 0 lines (0 before) | `shots/aa1070-r288-settings-after-delete-1440-light.png`, `raw/r288.json` |

### AA-1088: studio pre-pilot fixes (`harbour-lights-owner`)

| Check | Result | Evidence |
|---|---|---|
| (a) My Content drawer, "Atlas & Hearth (Audit)" | PASS: the drawer shows the title, BLOG and AI-assisted badges, the piece text, the AI notice and the edit/export actions. None of "Where this came from", writer brief, source fact, search context, CTA, formula, angle or style appear. No sideways scroll | `shots/aa1088-drawer-{1440,390}-{light,dark}.png`, `raw/aa1088-studio-readonly.json` |
| (b1) A held blog piece, editor on an audit studio | PASS (API): the held pieces were found read-only through the CIS admin (`GET /api/admin/content-quality/pieces?status=held&channel=blog`, E2E CIS admin). On "Atlas & Hearth (Audit)", 9 of 13 pending pieces are held blog pieces. A publish POST through the studio proxy on one of them (`7b80e4ca`) → **409 `content_needs_final_check`, `can_publish_anyway: false`**, detail "Before this piece goes live, please read it through once more: we could not confirm every detail in it against the trip (dates, places, what is included). An account owner can then publish it." It contains no score, gate or held words. The held check runs before any write, so nothing was published | `raw/aa1088-publish.json` |
| (b2) The refusal shown on the Publish page + the owner's "Publish anyway" | **NOT TESTED (blocked by test data).** On all four "(Audit)" studios WordPress and Facebook are **not connected**, so the Publish page shows no Publish button. harbour-lights is also only an *editor* there, so no owner path exists. The only studio where harbour-lights is owner and test-wp is connected ("Atlas & Hearth", not an audit tenant) has 4 pending pieces, **none held**. I did not connect test-wp to an audit tenant, publish an approved piece, or press "Publish anyway" | `shots/aa1088-audit-publish-page-1440-light.png` |
| (c) Partner terms and privacy pages | PASS: both 200, "v0.7 · last updated 12 November 2026". No "API key" anywhere. The remaining "API" words are only "the Anthropic API" / "the OpenAI API" (model providers). Both describe sign-in. No sideways scroll | `shots/aa1088-legal-{partner-terms,privacy}-{1440-light,390-light,390-dark}.png` |

AA-1088 summary: **3 PASS (a, b1, c) / 0 FAIL / 1 not testable (b2)**.

To test b2, either:

- a held blog piece is needed on a studio that has test-wp connected and an owner identity, or
- test-wp connected plus an owner identity on one audit studio.

Observation: the My Content page subtitle still reads "See everything you've written — where it came from and whether
it's…". That is the page description, not the drawer.

### AA-960: tags (synthetic E2E agency owner)

Synthetic trip "E2E s278txdd0 Tags" (`827e8be4`, from the public form, `.invalid` e-mail), moved to Qualifying.
Qualifying had 0 trips at the start, so a Qualifying column bulk touches only this trip.

| Check | Result | Evidence |
|---|---|---|
| Create a trip tag and apply it (trip page tag bar, "+ New tag" → "Create and add") | PASS: `POST /bff/tags` 201 + `PUT /bff/trips/{id}/tags/{tag}` 200; the chip "E2E S278TXDD0 TRIP TAG" shows | `shots/aa960-trip-tagbar-{1440,390}-{light,dark}.png` |
| Create a client tag and apply it (client page tag bar) | PASS: POST 201 + `PUT /bff/travelers/{id}/tags/{tag}` 200; chip shown | `shots/aa960-client-tagbar-{1440,390}-{light,dark}.png` |
| Client directory `?tag=<code>` | PASS: `/clients?tag=e2e_s278txdd0_client_tag` lists only "E2E s278txdd0 Tags" with its tag. The tag filter chips also offer the system tag "Ready to travel again" | `shots/aa960-clients-tag-filter-{1440,390}-{light,dark}.png` |
| Board card tags | PASS: the Qualifying card shows the agency tag. The Booked cards show system tags (AA multi-day tour, Culture and heritage, Local life, Water activities, +1) | `shots/aa960-board-{1440,390}-{light,dark}.png` (Qualifying column), `shots/aa960-bulk-preview-1440-light.png` (full board behind the dialog) |
| Bulk apply with preview | PASS: the single tag was first removed from the chip (DELETE 200). Then the column "Tags" → "Add the tag" → tag → **Preview**: the preview shows "1 trips will get the tag …" and the button reads "Apply to 1" before apply (`dry_run` 200, `count 1, already 0, held 0, archived_suppressed 0`). Apply 200 (`count 1, workflows_started 0`); the trip carries the tag again. A stale apply (`expected: 5`) → 409 `count_changed` | `shots/aa960-bulk-preview-{1440-light,390-dark}.png`, `shots/aa960-bulk-applied-1440-light.png` |
| `/marketing` "Ready to travel again" | PASS (empty): `GET /marketing/ready-to-travel` 200 `{items: [], total: 0, ready_after_months: 9}`. The panel explains the rule and consent ("Sending needs their marketing consent") and shows "No client is ready to travel again yet". Per-client reasons and the consent state could not be seen: no synthetic client came home ≥ 9 months ago with no open trip. `sys_ready_to_travel` uses = 0 | `shots/aa960-marketing-{1440,390}-{light,dark}.png` |
| System tags cannot be changed | PASS: all **409 `system_tag`** "the app keeps its own tags": put a system trip tag on a trip, PATCH and DELETE a system tag, bulk with a system tag, put the system client tag on a client, and remove the system link `sys_aa_multi_day` from the S277 booked trip. The trip page lists them under "Set by the app" with the reason and no remove button | `shots/aa960-system-tags-1440-light.png`, `raw/t960-cleanup.json` |
| Settings > Tags | PASS: 15 tag rows (system + agency); no sideways scroll | `shots/aa960-settings-tags-{1440,390}-{light,dark}.png` |

AA-960 summary: **8 PASS / 0 FAIL** (Ready to travel again only in its empty state). Console and network errors: only
the 409s the checks caused on purpose. No sideways scroll in any shot.

Observations, not judged:

- **The system tag reason shows a raw AA tour id.** It reads "From the AA tour 000e3340-d9f5-…" instead of the tour
  title, which is not readable for an agency.
- **The bulk preview has a plural slip:** "1 trips will get the tag".

Clean-up:

- both agency tags were deleted from Settings > Tags (confirm dialog, DELETE 200, `removed_links 1` each);
- the trip and its lead are in Trash (purge 19/11);
- no agency tag is left, Qualifying is 0 and Inquiry 38, as at the start.

## AA-1087 / crm-13 (live)

Date 12/11/2026 (S278), Dev only, run by a verify subagent (no push, merge, workflow, Terraform, DB Migrate, ECS exec;
no AWS/Cognito change). Deployed: Booking API `24d2dab` (includes #232 E2E writers and #231 M13), CIS API `22c250a8`
(includes #1456), CRM API `1321cc3a`. The specs ran from temporary detached worktrees of `origin/main` (removed after
the run); the verify-only specs are kept in `aa1087-crm13/scripts/`. Every sign-in used the managed login with an
e-mail code from `inbound-admin/` (no password, no code or cookie written anywhere, no storage state saved).

Folder: `aa1087-crm13/` (`raw/`, `shots/`, `scripts/`).

### Fixtures found on Dev (read-only discovery)

- Supplier bookings: only `SB-000004/5` (B2C case TC-000015, confirmed). **No pending / requested supplier booking of
  any agency's B2B case** (summary: requested 0, pending 0). The CRM synthetic agency's cases (TC-000025…35) have none.
- Agency invoices: none `issued` (7 USD + 1 VND drafts, 2 paid). Payments: 2, both approved.
- CIS Compliance: **0 subject_gate flags** (open or resolved).
- Synthetic per the guard (`catalog.v_tenant_account_v1.is_synthetic`): "Atlas & Hearth" (`9149d3c6`) and "Invented
  Ledger Lane" (`1d3e25e0`) pass; **"SYNTHETIC CRM sen-vang (AA-947 E2E)" (`bab16039`) does NOT** (403
  `e2e_synthetic_only`; the tenant is also absent from CIS `/admin/tenants`). So the CRM's E2E agency is outside the
  writers' scope.

### AA-1087 results

| Check | Result | Evidence |
|---|---|---|
| Official spec `--project=e2e-writers`, dry run (`BOOKING_E2E_WRITERS=1 BOOKING_E2E_WRITERS_DRY_RUN=1`, SB = `SB-000004`, invoice = sen-vang draft, read-only stand-ins) | PASS: staff and maker sign in, `staff/me` 200, records read; checker test skipped by design in dry run | `raw/aa1087-official-dry-run.log` |
| Runbook note | The documented command needs `BOOKING_E2E_BASE_URL=https://booking.lumiguides.it.com` too, else Playwright tries to start a local `next start` and fails ("no production build") | — |
| Sign-in of each Booking identity | PASS: staff → role `sales`, maker → `finance`, checker → `finance` | `raw/aa1087-probes.json`, `shots/aa1087-{staff,maker,checker}-signed-in-1440-light.png` |
| Staff: confirm (allow-listed) on a B2C supplier booking | PASS (refused): 403 `e2e_synthetic_only` | `raw/aa1087-probes.json` |
| Staff: cancel supplier booking / record payment / **approve payment (checker action)** / **PATCH departure** | PASS (refused): 403 `e2e_read_only` on all four | same; `raw/aa1088-m13-docs.json` (`departure_patch_empty`) |
| Maker: record on sen-vang draft | 403 `e2e_synthetic_only` (sen-vang not synthetic in CIS, see above) | `raw/aa1087-probes.json` |
| Maker: record on Atlas & Hearth draft / Ledger Lane paid | guard passed (synthetic), route 409 `invoice_not_issued`: **no row** | same |
| Maker: approve | PASS (refused): 403 `e2e_read_only` | same |
| Checker: record / confirm supplier booking | PASS (refused): 403 `e2e_read_only` | same |
| Checker: approve (already-approved Ledger Lane payment) | guard passed, route 409 `payment_decided`: **no change** | same |
| Server logs name the identity and reason | PASS: `booking_e2e_writer_refused identity=… reason=not_allowlisted / not_synthetic`, `booking_e2e_write_allowed identity=…` | `raw/aa1087-booking-refusal-logs.txt` |
| Staff write: send + confirm a synthetic agency's supplier booking | **NOT TESTED**: no pending/requested supplier booking of a synthetic agency exists, and the identities cannot create one | — |
| Maker records → checker approves (maker-checker happy path) | **NOT TESTED**: no issued invoice of a synthetic agency; issuing is outside the allow-lists | — |
| Audit log shows the actor | **NOT TESTED**: no allowed write reached a commit | — |
| CIS A10b: sign in, Compliance page 1440/390 | PASS: renders, no sideways scroll; 0 flags | `shots/aa1087-cis-compliance-{1440,390}-light.png`, `raw/aa1087-cis-probe.json` |
| CIS A10b: release passes the middleware allow-list | PASS: release on an unknown flag → 404 "Flag not found" (route reached) | same |
| CIS A10b: non-allow-listed write | PASS (refused): `POST /admin/tenants {}` → 403 `e2e_read_only` | same |
| CIS A10b: release a synthetic tenant's held piece; refused on a real tenant | **NOT TESTED**: no subject_gate flag exists on Dev; the official `compliance-release` spec needs `FLAG_SYNTHETIC` even for its dry run | — |
| Refused outside Dev | **NOT TESTED live**: there is no non-dev Booking/CIS environment; covered only by unit tests | — |

### crm-13 (full flow)

**NOT TESTED.** The Booking staff writer cannot cancel a departure: `PATCH /booking/catalog/departures/9f7d807d…`
answered 403 `e2e_read_only` (departure still `scheduled`). Departure cancel is not on any A10e allow-list. Candidate
for a later run (all bookings from the CRM E2E agency only): `2d3f3d0c` (27 Nov, 3 seats sold, sen-vang TC-000031 +
TC-000035); `824ac043` (20 Nov, sen-vang TC-000033). The empty `9f7d807d` (13 Nov, sold 0) would open no CRM case.
Note: sen-vang is not CIS-synthetic, so even a cancel route added to the A10e list would refuse it as written.

### AA-1088 M13 voucher end date

| Case | Result | Evidence |
|---|---|---|
| TC-000035 (sen-vang, Tropical Jewels 6 days, start 27 Nov) | PASS for the documents: confirmation "27 Nov 2026 to 02 Dec 2026" (start + 6 − 1), vouchers JSON end 2026-12-02; case title = tour name (not "Custom trip"). Vouchers HTML is "No voucher: … no service is confirmed by a supplier yet" (no supplier booking), so it shows no dates. **Observation:** the case page header and Trip details still show "27 Nov 2026 – 27 Nov 2026 (1 day)": the stored end of a case confirmed before #231 is not rewritten (by design per the PR, but staff still see 1 day) | `raw/aa1088-m13-TC-000035-{confirmation,vouchers}.{pdf,html}`, `shots/aa1088-m13-TC-000035-*-1440-light.png`, `shots/aa1088-m13-case-TC-000035-{1440,390}-light.png` |
| TC-000033 (start 20 Nov) | PASS (documents): end 2026-11-25; title = tour name | `raw/aa1088-m13-and-departure-probe.json`, `shots/aa1088-m13-case-TC-000033-*.png` |
| TC-000028 (older sen-vang case, start 1 Dec) | Dates PASS (end 06 Dec). Title **FAIL**: the case shows "B2B crm-proposal:f24632b5… v1" and the confirmation line reads "trip_plan tp:77740b45… · line 5a83f927…", not the tour name | `raw/aa1088-m13-TC-000028-*.{pdf,html}`, `shots/aa1088-m13-case-TC-000028-*.png` |
| New case confirmed after #231 | NOT TESTED: none exists on Dev | — |

### Clean-up

Nothing to clean: **no row was created or changed** by this run (every write probe was refused 403 or ended in a 409
before any insert/update). Side effects only: sign-in code mails under `inbound-admin/` (1-day expiry) and the normal
`booking.staff_users` last-seen sync of the three identities on sign-in.

## AA-1092 / AA-1094 (live)

Run 12/11/2026 ~14:15–14:50 ICT, Dev only, acc2 (STS <acc2>). Folder: `aa1092-1094/` (`scripts/`, `shots/`, `raw/`).
Deployed: TripPlanner Lambdas updated 06:08Z, web task def `aa-tripplanner-dev-web:14` (COMPLETED 13:14 ICT) maps
`TP_TENANT_ASSERTION_KEY` from the secret's `current`; CIS api `git_sha 22c250a8` (#1460); CRM api `aa-crm-dev-api:161`.
The TripPlanner edge key was read from Secrets Manager on stdin only (never printed or written); from the assertion secret
only its shape and timestamps were read (`raw/aa1092-tp-keyset-shape.json`, no key material). Booking RLS (bk-049) was not
checked here (orchestrator). Nothing was created: every CRM request was a validation failure or used fake values.

### AA-1092

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Forged assertion (random 32-byte key), browse + assembly Lambdas, right edge key | PASS: 401 `tenant_assertion_invalid` on both | `raw/aa1092-tp-assertion-probe.json` |
| 1b | Old-way assertion (key derived from the edge key) | **FAIL (time-gated by design)**: accepted (browse 200, assembly 404 for a random trip id). The secret holds `edge_derived_until` = 2026-11-13T05:55:33Z (12:55 ICT 13/11), the 24 h cut-over grace of the first fill. Refused only after that time, or after a re-fill without `edge_derived_until` | `raw/aa1092-tp-assertion-probe.json`, `raw/aa1092-tp-keyset-shape.json`, `raw/aa1092-tp-lambda-assertion-log-events.txt` (the only `edge_derived` uses are this probe) |
| 1c | Malformed assertion; forged assertion without the edge key | PASS: 401 `tenant_assertion_invalid`; 401 `unauthorized` (edge gate first) | same |
| 1d | Normal tenant page through the BFF | PASS: `/audit-terra-family/plan` loads with the agency bar; a search on it (BFF signs with the dedicated key) answers 200, "60 places match"; 0 `tenant_assertion` refusal / `key_used` events in either Lambda since 07:20Z | `shots/aa1092-tenant-search-1440-light.png`, `raw/aa1092-tenant-search-lambda-log.txt` |
| 2a | VNPay IPN `GET /crm/public/v1/hooks/vnpay/ipn` (go-dev and portal): unsigned, garbled hash, hash + newline | PASS (protocol): HTTP **200** `{"RspCode":"97","Message":"Invalid signature"}`, `no-store`. Not 4xx: VNPay expects HTTP 200 + RspCode (the root review summary expects `97` too), so the Done-when wording "4xx" does not apply literally | `raw/aa1092-crm-ipn-probe.json` |
| 2b | Forged 128-hex hash, unknown reference; same request replayed; 600-char field; SQL-like reference | PASS: `01 Order not found` (twice), `01`, `99 Unknow error`; body is only `{RspCode, Message}`, no ids, no stack | same |
| 2c | Rate limit on bad notices | PASS: 160 unsigned notices in 15 s → 429 `rate_limited` from #98 on, `Retry-After: 60`. 16 KiB URL → 414 at the edge | same (`flood_unsigned`, `url_16k`) |
| 2d | Bad signature on a KNOWN reference → 97 then 429 per (address, reference); replay of a genuinely signed notice → 02 | NOT TESTED: needs an open payment session reference and the agency's VNPay secret (unit tests only) | — |
| 3a | Book now (synthetic agency Sen Vàng form, key masked) | PASS: widget 404 `booking_not_offered` (Book now off); unknown key 404 `form_not_found`; foreign Origin 403; bad body 422 `consent_required`; 40 KiB 413 `body_too_large`; per-address 429 after the 5/min intake limit, `Retry-After: 60` | `raw/aa1092-crm-booknow-intake-probe.json` |
| 3b | Book now per-agency hourly cap (429 `form_rate_limited`, 200/h, bucket `book:<key>`) | NOT TESTED live: reaching it needs valid bookings (real rows); covered by unit tests | — |
| 3c | Sales-partner intake link `/crm/public/v1/r/{token}` with a fake 43-char token | PASS: GET 404 `link_not_found`; POST 404 `link_not_found`; shares the per-address intake limiter (429 inside the same minute) | `raw/aa1092-crm-booknow-intake-probe.json`, `raw/aa1092-crm-partner-link-post.txt` |
| 4 | WAF coverage | PASS: `aa-cis-dev-waf` on the ALB + REST stages `aa-cis-dev-api/dev` and `aa-booking-dev-api/dev`; `aa-identity-dev-pools` on all 4 pools incl. `aa-m2m-dev`. Not covered, by design (Infra `docs/implementation-notes/AA-1092-waf.md`): TripPlanner HTTP API (AWS: no web ACL on HTTP APIs; edge key + assertion + 500 rps stage throttle + app limits), the photo CDN (static). The 4 CloudFront hosts (go-dev, portal, partner-dev, tripplanner) have no CloudFront ACL but reach the ALB ACL via VPC origin → NLB → ALB (`CloudFrontOriginAllow` skips RateLimit1000/Geo; CRM relies on its own per-viewer limits). Today: RateLimit1000 blocked 0 (NAT exemption works), GeoBlock 89; all API hosts healthy | `raw/aa1092-waf-acls.txt`, `raw/aa1092-waf-resources.txt`, `raw/aa1092-waf-rules.json`, `raw/aa1092-waf-blocked-today.txt`, `raw/health.txt` |
| 5 | Review notes | PASS with a gap: root `docs/audits/2026-11-12-S278-prepii-security/README.md` (#719) and Partner `docs/implementation-notes/AA-1092.md` (R1–R16, "No high finding is open"). Both say residual risks are "tracked in Linear AA-1092", but AA-1092 has no comments. `docs/security/secrets-register.md` still marks the key **planned** although it is filled | git `origin/master` c228372d |

AA-1092 summary: **9 PASS / 1 FAIL (1b, time-gated) / 3 NOT TESTED**. Done when not met yet: the old-key refusal can only be shown after
12:55 ICT 13/11 (or after a re-fill that drops `edge_derived_until`; the web already signs with `current`). "IPN 4xx" is HTTP 200 + RspCode 97 by protocol.

### AA-1094

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Synthetic tenant path lists only its adopted tours with its own text | **FAIL / not demonstrable**: the only served synthetic tenant is `audit-terra-family`, and it is kind `demo`, so it gets the AA catalogue: `source "aa"`, total 844, the same first tours and AA text as `/aa-tripplanner/plan`. `/audit-terra-family/tours/{slug}` → 404 (demo kind has no tenant tour page). The other audit tenants (atlas-hearth, trail-pulse, wildkind-travel, harbour-lights, sen-vang) are not served (`tenant not found`). The `source "tenant"` path (`catalog.v_tenant_tour_v1`) was never reached live | `raw/aa1094-tenant-lookup.json`, `raw/aa1094-tourlist.json`, `shots/aa1094-tourlist-{tenant,aa_demo}-{1440,390}-{light,dark}.png`, `shots/aa1094-tenant-tour-route-1440-light.png` |
| 2 | AA tour page: no agency branding, no Sign in | PASS: direct `/tours/{slug}` and the tour opened from the agency planner in the same tab show the AA bar, no agency name, no Sign in, no sideways scroll (1440/390, light/dark). The agency planner shows the agency bar and no Sign in | `shots/aa1094-aa-tour-page-*.png`, `shots/aa1094-aa-tour-from-tenant-*.png`, `shots/aa1094-planner-*.png`, `raw/aa1094-pages.json`, `raw/aa1094-dark.json` |
| 3a | CIS tour page JSON carries `source_id` | PASS: `GET api-cis /v1/trip/a26bdf3f…` → `source_id 28e22489…` (= the catalogue row) | `raw/aa1094-cis-trip-page.json` |
| 3b | Book now targets the page's own key | PASS (payload): go-dev `/trip/a26bdf3f…?f=<key>&p=80477347…` (another tour in `p=`) → widget request `tour=28e22489…&page=a26bdf3f…` at 1440/390 light+dark | `raw/aa1094-pages.json`, `raw/aa1094-dark.json`, `shots/aa1094-crm-trip-booknow-*.png` |
| 3c | Book now creates the line for that `source_id` | NOT TESTED: Book now is off for the synthetic agency (`booking_not_offered`); no line created | — |

AA-1094 summary: **4 PASS / 1 FAIL (no served agency-kind tenant) / 1 NOT TESTED**. Done when not met: item 1 needs a served
synthetic tenant of kind `agency` with adopted, publishable tours; item 3 "creates the line" needs Book now switched on for the
synthetic agency for one booking.

Clean-up: none needed (no rows created; the IPN and intake limiters reset after 60 s).
