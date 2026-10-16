# S239 live verify: AA-Booking AA-822, AA-823, AA-679, AA-683 (Dev, 16/10/2026)

Agent: Claude Code (S239 workflow subagent). Nghiệp approved writing clearly labelled test data on Dev (S239).

## Environment

- API: `https://api-booking.lumiguides.it.com/booking`. `/health` git_sha `dda5521`. `/health/ready` returns `{"status":"ok","db":"ok","schema_version":"bk-011"}`.
- Staff admin: `https://aa-booking-admin.vercel.app`, the Vercel production alias. The production deployment for `cd4b962` (Booking #20, the AA-683 table fix) has status success (deployment 7108145523).
- Staff: `e2e-claude-code` (CIS user `2d8e5a2f-…`) and `e2e-claude-code-2` (`58a130c7-…`). Both are active Booking `admin`, with every permission including `supply.write`, `pricing.write` and `trip_plan.write`.
- Login: the real `/login` UI (CIS `/auth/admin-login`, then `/auth/booking-token`). Credentials are read from Secrets Manager at run time. Nothing was printed or saved, and no screenshot shows a password or token.
- Browser: Playwright Chromium, `ignoreDefaultArgs:['--hide-scrollbars']` (real scrollbars). Theme is set through `localStorage.bk_theme`, and `data-theme` on `<html>` is checked in every shot. Viewports are 1440×900 and 390×844.
- Overflow check: `documentElement.scrollWidth <= clientWidth`, plus every table's scrolling wrapper `scrollWidth <= clientWidth`. The `matrix-*.json` files per folder hold the raw numbers.
- Console and network: 0 console errors and 0 HTTP ≥400 on every page in every run. The only network noise is 3–4 `ERR_ABORTED` dashboard prefetches cancelled by the post-login navigation, which is benign.
- Scripts are in `.tmp-session/s239/bkv/` (`lib.mjs`, `matrix.mjs`, `s822*.mjs`, `s823*.mjs`, `s679*.mjs`, `s683*.mjs`, `bk.py`).

## AA-822: suppliers and supplier contracts (folder `aa822/`)

Steps, all in the UI as e2e-claude-code unless marked API:

| # | Step | Result |
|---|---|---|
| 1 | `/suppliers/new`: name, categories Hotel and Activity, website, notes, contact, country BT → Save supplier | POST 201 → **SUP-000001** `d54ae2c7-f161-4971-9dff-4aff7bbb09d7`, lands on the detail page (`ui-01`) |
| 2 | Edit profile → Job title → Save changes | PATCH 200, `contact_title` updated (`ui-02`) |
| 3 | Contracts tab → New contract: title, ref, 2026-10-01..2027-12-31, USD, payment terms → Save as draft | POST 201 → contract `16d66dfa-51d6-4aad-9703-88ab29688beb`, status `draft` (`ui-04`) |
| 4 | Row menu as the maker | "Edit draft" enabled; "Publish (needs a second person)" **disabled** (`ui-05`) |
| 5 | Edit draft → Cancellation policy → Save draft | PATCH 200 (`ui-06`) |
| 6 | List with search `ZZ S239` and category Hotel | 1 row (`suppliers-filtered-*`, `ui-07`) |
| 7 | API: `GET /suppliers?q=ZZ S239`, `/suppliers/SUP-000001`, `/contracts`, `/audit-logs?entity_id=…` | 200s. Audit rows: `supplier.created`, `supplier.updated` (contact_title), `supplier_contract.created`, `supplier_contract.updated` (cancellation_policy) (`api-evidence.json`) |

Screenshot matrix (1440/390 × light/dark): suppliers list, filtered list, new form, profile, contracts tab. 20 shots, `data-theme` correct, no page overflow at either width.

Verdict per Done-when:
- bk-008 applied: **MET** (`schema_version` bk-011 includes it).
- Supplier and contract created, edited and listed through the staff admin, with desktop and mobile screenshots: **MET**.
- Rows and audit-log entries visible through the API: **MET**.
- CI green, deployed, live check recorded: **MET for the live check** (this folder). The Linear comment is still to be posted by the orchestrator.

## AA-823: hotels, room types, services, supplier net rates (folder `aa823/`)

| # | Step | Result |
|---|---|---|
| 1 | UI `/hotels` → Add hotel under SUP-000001, "ZZ S239 test Hotel Thimphu", 4★, Boutique, BT | POST 201 → **HTL-000001** `e8dfea00-4781-4ce9-ab43-f45778066a64` |
| 2 | Hotel drawer → Add room type ×2 | 201 "ZZ S239 Deluxe Double" `209a97cc-…`, 201 "ZZ S239 Family Suite" `649b555a-…` (`ui-03`) |
| 3 | UI `/services` → Add service: activity, per person, "ZZ S239 test Thimphu valley guided day walk" | 201 → **SVC-000001** `fabe33de-5293-48ae-b68d-16f753886531` |
| 4 | UI supplier contracts → second draft contract in **EUR** (rates take the contract currency, so a non-USD rate needs a non-USD contract) | 201 → `f0241f6b-6f85-4367-8359-043c29cd26c5` |
| 5 | UI supplier Rates tab → Add rate ×3 | Deluxe 120.00 USD/room-night BB `54b937e1-…`; Suite 210.00 USD/room-night BB `aba2f124-…`; service **45.00 EUR/person** `074c7f37-…` (`ui-06`, `ui-07-*`) |
| 6 | API before publish: `rate-in-force` (room and service) | `{"rate": null}`: drafts are not in force |
| 7 | API: self-publish by e2e-claude-code, `PATCH /contracts/{id} {"status":"published"}` on both | **403 `maker_checker`** ×2 (`api-01-before-publish.json`). The UI already disables Publish for the maker. |
| 8 | UI as **e2e-claude-code-2**: row menu → Publish → confirm, both contracts | PATCH 200 ×2, status `published`, `published_by_name` e2e-claude-code-2 (`ui-08-*`, `ui-09`) |
| 9 | API `rate-in-force` after publish | Room 1 → 120.00 USD (rate `54b937e1`), room 2 → 210.00 USD, service (pax 2) → 45.00 EUR (`api-02-after-publish.json`) |
| 10 | API: test case **TC-000007** (new lead "ZZ S239 test Customer AA-823", 2 pax, start 2026-12-01, discovery) + V1 | 201 / 201 |
| 11 | UI proposal builder `/cases/TC-000007/proposals/1`: Add item "…Deluxe Double, 2 nights" days 1–3 with the supply typeahead (`ui-10`), Add item "…valley walk" day 3 with the service, no costs entered → Save | PUT items 200, `rate_defaults`: pos 1 on 2026-12-01 rate `54b937e1` **240.00 USD** (120 × 2 nights); pos 2 on 2026-12-03 rate `074c7f37` **90.00 EUR** (45 × 2 pax). Cost lines carry `supplier_rate_id` and notes like "120.00 USD x 2 night" (`api-04`) |
| 12 | UI "Apply price to this version" (b2c_tailor_made, USD) | POST price 200. AA-810 engine: EUR line net_usd 97.83 (90 / 0.92, no buffer on cost, as designed), net 337.83 USD, margin 30 %, card fee 3 %, subtotal 504.22 → **final 505.00 USD**, effective margin 30.1 %. Per-line sell 358.21 + 146.01. The UI shows the same values (`ui-12`). Audit: `trip_case_version.created/items_replaced/priced` |

Audit (`api-05-audit.json`): `hotel.created`, `service.created`, `supplier_contract.created` + `.published` for both contracts, rate writes under the contracts.

Screenshot matrix (1440/390 × light/dark): `/hotels`, hotel drawer, `/services`, `/services/SVC-000001`, supplier Rates tab, proposal V1 builder. 24 shots, 0 console/network errors, no page overflow.

Verdict per Done-when:
- bk-010 applied: **MET**.
- Hotel with 2 room types and a service under a supplier, used as items on a trip case version, net rate pulled in, sell price from the AA-810 engine (live): **MET**. Maker-checker was proven both ways: 403 for the maker, publish by the second person.
- Staff admin pages (/hotels, /services, supplier Rates tab) verified desktop and mobile: **MET** on the production alias, not a per-PR preview. Evidence still needs to go on the issue.
- CI green, deployed: **MET** (earlier evidence).

## AA-679: catalog trip plans, commercial row, "Use for trip case" (folder `aa679/`)

Plan: CIS source_id `4a2411b2-6966-4ec0-a27e-84f9fad186ea`, "Bhutan: Bumdra Trek & Valley Monasteries — 7 Days".

| # | Step | Result |
|---|---|---|
| 1 | API `PUT /catalog/trip-plans/{sid}/commercial` (sellable, Trekking, b2c_tailor_made, hint 2,450 USD pp, notes "ZZ S239 test …") | 200, `plan_id 75b1bdfe-ed69-4459-a22e-e96cf2e68805`, `changed` = 7 fields |
| 2 | Same PUT again | 200, **same plan_id**, `changed: []` |
| 3 | `GET /audit-logs?entity_id=<plan_id>` | **1 row** `trip_plan.created` ("Marked sellable"). The second PUT wrote nothing. |
| 4 | `GET /catalog/trip-plans?sellable=true&country=Bhutan` | total **1**, with trip_style, default_channel, price_hint, has_commercial_row filled. `/facets`: sellable 1, Bhutan 32/1, trip_styles ["Trekking"] |
| 5 | UI `/catalog/trip-plans?sellable=yes&country=Bhutan` | 1 row, "Sellable" pill, Trekking, "from 2,450.00 USD per person" (`trip-plans-sellable-*`) |
| 6 | UI plan detail → Use for trip case → New trip case, "+ New lead" "ZZ S239 test Customer AA-679", start 2027-04-05, 2 adults → Create trip case | POST 201 `mode` new case → **TC-000008** V1, lands on `/cases/TC-000008?tab=proposals` (`ui-03`, `ui-04`) |
| 7 | V1 items | **7 items = the 7 days of the plan** (`days` = 7), one per day, each with `source_tour_id` = the plan |
| 8 | UI Use for trip case → "Add to an existing case" TC-000008 → Add version | POST 201 `mode: new_version`, **V2** with 7 items (`ui-06`, `api-05-case-items.json`) |
| 9 | 390 px modal (S237 defect 1) | The "Create trip case" button is inside the first viewport (y 799 + 37 ≤ 844) in light and dark (`use-modal-390-*`): fixed |

The DB count query was not run (no ECS exec). One row is shown instead by the same `plan_id` on both PUTs, a single audit row, list total 1, and the bk-009 unique key.

Verdict per Done-when:
- (D4) Staff list sellable trip plans with commercial fields: **MET** (API + UI).
- (D4) A trip case or version can start from a trip plan: **MET** (new case, and new version on an existing case, both through the UI).
- Idempotent commercial PUT: **MET**.
- S237 low UI defects: 390 dialog footer **fixed**. The light-mode disabled-button contrast and the mobile KPI cards were not re-checked.

## AA-683: /pricing/rules and /proposals table fit (folder `aa683/`)

Pending rows created as e2e-claude-code (API):
- FX `2a255cca-bfaa-4d3d-96aa-b8bb3e2f795a`: BTN 84.10 per USD, buffer 2 %, as_of 2026-10-16, source "ZZ S239 test FX row …". Self-approve returned **403 `own_row`**.
- Rule `e4cd95e1-6ebe-481c-a8e1-6d1155a37f96`: b2b, values identical to the seed (15 / 10 / +3 pts / 3 %), valid_from **2027-01-01**, note "ZZ S239 test rule row …". Self-approve returned **403 `own_row`**.

Screenshots as the maker with both rows pending: `/pricing/rules`, `/pricing/rules?tab=fx` and `/proposals` at 1440/390 × light/dark, with scrollbars enabled:

| Page | 1440 table wrapper sw/cw | 1440 doc | 390 doc | Note lines (1440) |
|---|---|---|---|---|
| /pricing/rules (pending row) | 1078/1078 | 1440/1440 | 390/390 | 2,2,2,2 (long note truncated with an ellipsis) |
| /pricing/rules?tab=fx (pending row) | 1084/1084 | 1440/1440 | 390/390 | Source column: 3,2 (see D4) |
| /proposals | 1084/1084 | 1440/1440 | 390/390 | n/a |

Same results in light and dark, as maker and as checker. Then, as **e2e-claude-code-2** in the UI: the Approve button is visible (`pricing-*-checker-u2-*`), and approving gives 200. The rule became `scheduled` (from 2027-01-01) and the BTN FX row `in_force`, both `approved_by` e2e-claude-code-2 (`pricing-*-approved-u2-*`, `approve-u2.json`).

Verdict on the folded Done-when bullet ("/pricing/rules and /proposals at 1440 no horizontal scroll, Note ≤ 2 lines, no overflow at 390, light + dark screenshots"): **MET** on production `cd4b962`. The other AA-683 bullets (Ms. Thư review waived, customer-app spec moved to AA-680) are Nghiệp decisions recorded on Linear 16/10. The `ui-spec.md` line-3 update was not checked here.

## Defects / observations (none blocking)

| # | Sev | Where | What |
|---|---|---|---|
| D1 | Low | `/suppliers` list (1195/1084), supplier Contracts tab (1150/1092), `/hotels` (1245/1084), hotel drawer rates table (1126/631), `/services` (1379/1084) at 1440 | These tables still scroll sideways at 1440, the same class as the AA-683 fix (`tableMinWidth`). On the Contracts tab the **Actions "⋯" column is completely off-screen** at 1440 with 2 contracts (trigger right edge 1476 > wrapper 1391), so the publish and edit menu is reached only by scrolling the table sideways. |
| D2 | Low | `RowMenu` | A Playwright `locator.click()` on the partly clipped "⋯" (it scrolls the wrapper first) opens the menu and it closes at once. A coordinate click works. This is probably the `scroll` (capture) close listener reacting to the scroll-into-view. A real user who scrolls first is not affected. Worth a check together with D1. |
| D3 | Low (UX) | Case created from a trip plan (TC-000008) | The Overview shows the title "Custom trip" and Trip legs "A custom trip: no CIS tour is linked yet". `/proposals` shows Trip "Custom", although every V1/V2 item carries `source_tour_id` of the plan and the plan detail counts "Trip cases from this plan: 1". The case has `legs: []` and `title: null`. The audit remaining-step expected "the new case Overview linking the plan". |
| D4 | Low | `/pricing/rules?tab=fx` at 1440 | The Source column wraps to 3 lines for a long source. It is not truncated like Note on the rules tab. Not in the AA-683 Done-when. |
| D5 | Cosmetic | Tab strip on `/pricing/rules` (also seen on other tab bars) | The `[role=tablist]` has `overflow:auto` and scrollHeight 32 > clientHeight 31, so with visible scrollbars (Windows) a small scrollbar shows at its right end. |
| D6 | Info | `/catalog/trip-plans?sellable=true` | The URL param is `sellable=yes|no`. `sellable=true` is ignored (shows all 892). Not a bug, just remember it for deep links. |

## Test records created (nothing deleted; clean up later)

| Kind | Id / code | Name / note |
|---|---|---|
| Supplier | SUP-000001 `d54ae2c7-f161-4971-9dff-4aff7bbb09d7` | ZZ S239 test Supplier AA-822 (active) |
| Contract (published) | `16d66dfa-51d6-4aad-9703-88ab29688beb` | ZZ S239 test contract 2026-27 USD |
| Contract (published) | `f0241f6b-6f85-4367-8359-043c29cd26c5` | ZZ S239 test contract 2026-27 EUR (services) |
| Hotel | HTL-000001 `e8dfea00-4781-4ce9-ab43-f45778066a64` | ZZ S239 test Hotel Thimphu |
| Room types | `209a97cc-e5fe-4f1d-bf4e-a87d4257c685`, `649b555a-e5fb-4d6e-8091-d8aba6753be7` | ZZ S239 Deluxe Double, ZZ S239 Family Suite |
| Service | SVC-000001 `fabe33de-5293-48ae-b68d-16f753886531` | ZZ S239 test Thimphu valley guided day walk |
| Supplier rates | `54b937e1-f263-4b0f-8602-5f60830ed76c`, `aba2f124-a34e-4f06-83dc-a83f67449823`, `074c7f37-464c-4839-b51a-12c63e183e13` | 120 USD, 210 USD, 45 EUR (published, fixed) |
| Customer (lead) | `c7eeafa0-8ff5-4e63-a695-f4ccf08eecfe` | ZZ S239 test Customer AA-823 |
| Trip case | TC-000007 `3f6f9fd1-43c7-40b3-956e-ca61f595f0e1`, V1 `c08b67d5-e57e-44ec-9edd-e784a9308b07` (draft, priced 505.00 USD) | discovery |
| Customer (lead) | `1376fac5-1f04-4ea9-b4bb-633b95e4f550` | ZZ S239 test Customer AA-679 |
| Trip case | TC-000008 `509c154f-fdd6-40f3-ad65-108fd4f67fd9`, V1 `119361b2-2b6e-417b-812c-1d75573f9674`, V2 `58d5adbf-92fa-4c32-90d8-8ac62f567811` (drafts, 7 items each) | new_inquiry |
| Trip plan commercial row | plan `75b1bdfe-ed69-4459-a22e-e96cf2e68805` on CIS `4a2411b2-…` | **sellable = true** on a real Bhutan tour, notes "ZZ S239 test …". Revert with PUT sellable=false. |
| Pricing rule | `e4cd95e1-6ebe-481c-a8e1-6d1155a37f96` | b2b, same values as the seed, **scheduled from 2027-01-01** (approved; append-only, cannot be deleted; harmless because the values are identical, but its note replaces the seed note from 2027) |
| FX rate | `2a255cca-bfaa-4d3d-96aa-b8bb3e2f795a` | **BTN 84.10 in force** (approved; append-only) |

Suggested cleanup: deactivate SUP-000001, HTL-000001 and SVC-000001. Expire the 2 contracts. Cancel TC-000007 and TC-000008 with a reason. PUT the commercial row of `4a2411b2-…` with `sellable:false`. Pricing rows are append-only: if wanted, supersede the b2b row with a later row that carries the seed note.
