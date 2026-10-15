# Booking staff admin: UI verify after the S237 Dev ship (AA-679, AA-810, regression)

- **Target:** https://aa-booking-admin.vercel.app. This is the production alias of Vercel project `aa-booking-admin`, deployment `dpl_77mttbRbUS1sAJoxskyezsK2654h` (READY, git `main` 51bb196, which includes Booking #7, #11, #12 and #13). The alias is public, so no share link or bypass was needed.
  - The project is in team `pqnghiep1354-5974s-projects` (Vercel CLI), not in `team_zHOmLxnHRN3EC6hXHbXgTG81`. The Vercel MCP `list_projects` on that team does not return it.
- **Backend:** Dev Booking API through the BFF `/api/booking/*`. `GET https://9z3xnalp59.execute-api.us-west-1.amazonaws.com/dev/booking/health/ready` returned `{"status":"ok","db":"ok","schema_version":"bk-010"}`, so bk-010 had already landed.
- **Account:** CIS E2E admin `e2e-claude-code` (Booking role `admin`; it has `trip_plan.write`, `trip_case.write`, `version.write`, `pricing.read` and `pricing.write`). The password was read from Secrets Manager `aa-cis/dev/e2e-test-admin` into the Playwright process only.
- **Run:** 2026-10-15, Claude Code sub-agent, Playwright/Chromium with one browser at a time. Scripts are in `.tmp-session/s237/uiv/booking/`.
- **Scope:** read-only. A route guard aborted every non-GET call to `/api/**` except:
  - `POST /api/auth/login`;
  - the stateless `POST /api/booking/pricing/quote-preview` that the calculator itself makes (nothing is saved).

  Blocked write attempts: **0**. No Save, Create, Add version or Approve button was clicked. Every drawer, modal and dialog was closed with Cancel.
- **Theme:** set the page's own way (`localStorage.bk_theme`, plus the matching `prefers-color-scheme`). `html[data-theme]` matched the requested theme on every capture. The admin is not pinned light; only /login is (by design, already verified in S236).

Matrix: 9 pages × {1440, 390} × {light, dark} = 36 captures (`<page>-<w>-<theme>.jpg`). There are also 40 interaction or scrolled captures. Raw data is in `results.json`, `results-supplement.json` (390 scrolled views, rules table widths) and `results-photos.json` (CIS photo loading).

## Matrix

| Page | 1440 L/D | 390 L/D | BFF calls | Data shown |
|---|---|---|---|---|
| / (dashboard) | PASS | PASS | trip-cases, summary, staff, notifications: all 200 | 2 new inquiries; recent cases TC-000003/2/1 |
| /cases | PASS | PASS | all 200 | 3 cases. Source filter has the new "CIS trip plan" option. `?source=cis` shows the 0-match empty state, which is correct because no case has been started from a plan yet |
| /cases/TC-000003 | PASS | PASS | trip-cases/TC-000003, countries: 200 | Confirmed custom trip, stepper, Proposals 2, people, trip details |
| /customers | PASS | PASS | customers ×N, all 200 | 3 customers |
| /pricing/calculator | PASS | PASS | none on load. `quote-preview` 200 (USD) and 422 (EUR, intended) | See AA-810 |
| /catalog/trip-plans | PASS | PASS | trip-plans, facets: 200 | KPIs: CIS tours **892** (facets total = list total = 892), Sellable 0, Countries 14. 25 rows per page, cards at 390 |
| /catalog/trip-plans/51b36891-… (Bhutan: Bumthang Drup Festival, 12 days) | PASS | PASS | trip-plans/{id}: 200 | Overview with cover photo, Day by day (12), Photos (42); all 42 loaded from `api-cis…/content/photos/{id}?size=small` (302 → 200) |
| /pricing/rules | PASS (defect 2) | PASS | rules, fx-rates: 200 | 3 seed rules In force, approved by "Migration seed" |
| /pricing/rules?tab=fx | PASS | PASS | rules, fx-rates: 200 | Empty state "No FX rates yet" (Dev has 0 FX rows) |

- **Console errors on page loads: 0 out of 36.** The only console errors in the whole run were in the calculator's EUR step: Chrome logs "Failed to load resource: 422" for the intended `quote-preview` 422 `{"detail":"no FX rate for EUR"}`.
- **Non-2xx BFF responses: 0**, apart from that intended 422.
- **`ERR_ABORTED` (11):** Next.js RSC prefetches (`?_rsc=`) were cancelled when the context closed or navigated. Benign.
- **Horizontal overflow at 390: none.** `scrollWidth == 390` on every page, drawer and modal, and no element extends past the viewport without being clipped.

## AA-679: sellable trip plans over the CIS catalog (Booking #11, #12)

**Verdict: PASS with defects.** The list and detail pages and the commercial drawer work on live data. The "Use for trip case" entry point is correctly disabled on Dev. Its dialog could only be opened with a browser-side mock (details below). Creating a case from a plan is NOT VERIFIABLE read-only.

- **List** (`trip-plans-*.jpg`, `trip-plans-bhutan-*.jpg`, `trip-plans-390-light-mid|bottom.jpg`):
  - It is a live read of `catalog.v_tour`: 892 tours, every one "Not for sale".
  - The Country / Status / Trip style / Sort filters are filled from the server (14 countries with counts, for example Bhutan (32)).
  - The `?country=Bhutan` filter shows 32 Bhutan rows with CIS thumbnails (23/23 visible loaded) and a "Reset filters" link.
  - `?sellable=yes` shows the empty state "No trip plans match" (`trip-plans-sellable-empty-1440-light.jpg`).
  - Clicking a row opens `/catalog/trip-plans/<source_id>`.
- **Detail** (`trip-plan-detail-*`, `trip-plan-days-1440-light.jpg`, `trip-plan-photos-1440-light-after8s.jpg`):
  - The header shows the "Not for sale" and "From CIS" badges, country, days and "Edit in CIS".
  - Tabs: Overview (cover photo, summary, facts), Day by day (12 CIS days with places) and Photos (42).
  - The Commercial side panel shows Status, Trip style, Default channel, Price hint, Notes, "Trip cases from this plan 0" and "Never edited in Booking".
- **Edit commercial:**
  - The drawer opens with Sellable, Trip style, Default channel, Price hint (amount, currency, basis) and Commercial notes. It closes on Cancel (`trip-plan-commercial-drawer-{1440,390}-{light,dark}.jpg`).
  - `/catalog/trip-plans/<id>/commercial` opens the page with the drawer already open (`trip-plan-commercial-route-1440-light.jpg`).
  - Save was not clicked.
- **"Use for trip case":**
  - The button is visible but **disabled**, with the title "Mark the plan sellable first". This is correct, because 0 plans are sellable on Dev.
  - Making a plan sellable is a write, so to see the dialog the GET of this one plan was answered **in the browser only** with `sellable: true` (Playwright route mock; no data changed).
  - The modal says "The proposal starts with the 12 day items of …, titled from CIS. It is not priced". It has two targets: "New trip case" (Existing customer / + New lead, start date, currency, adults, children) and "Add to an existing case" (trip case code).
  - It closed on Cancel (`use-for-trip-case-modal-*.jpg`, `use-for-trip-case-existing-1440-light.jpg`).
  - "Create trip case" and "Add version" were not clicked. The real POST flow and the V1 item count are **not verifiable** read-only.
- **Linear vs PR:** the AA-679 description in Linear still describes the old outbox/event-sync design (`trip_plans` drafts upserted by a job, "trashed tour unpublishes its template"). PR #12 implements S237 decision D4 (live read plus a commercial-only row). The UI matches the PR. The Linear Done-when text has not been reworded yet.

## AA-810: pricing rules and FX with maker-checker (Booking #7)

**Verdict: PASS with defects.** Every read-only part of the UI works. Creating and approving rows (the maker-checker itself) and a non-USD quote are NOT VERIFIABLE read-only on Dev.

- **`/pricing/rules`:**
  - Shows the title "Pricing rules & FX", the Maker-checker banner, tabs "Pricing rules" / "FX rates" (`?tab=fx`), and the "New FX rate" and "New rule" buttons (the account has `pricing.write`).
  - Rules table: channel, target, floor, peak uplift, card fee, valid from, status pill "In force", Entered by "—", Approved by "Migration seed".
  - At 390 the table becomes cards.
- **New rule / New FX rate drawers:**
  - Both open (`pricing-rules-new-{rule,fx}-drawer-*.jpg`).
  - The fields are entered as percentages: "Selling buffer 2 %", "As of" defaults to today, the source hint mentions "manual-dev", and the button is labelled "Save as pending".
  - Both closed on Cancel, and Save was not clicked.
- **FX tab:** the empty state "No FX rates yet …" appears, and the description says only USD prices work.
- **Approve dialog:** Dev has no pending rows (all 3 rules are approved; `can_approve=false`). The FX list was therefore mocked **in the browser** with one fake pending EUR row (`can_approve: true`, source "MOCK — UI verify only").
  - The tab shows the count badge "FX rates 1", the pill "Pending approval" and an "Approve" button.
  - The confirm dialog reads "Approve EUR at 0.92 per USD (buffer 2.5%), as of 15 Oct 2026 …" (`pricing-fx-approve-dialog-mock-*.jpg`). It was closed on Cancel.
- **Calculator** (`pricing-calculator-usd-*.jpg`, `pricing-calculator-eur-missing-fx-*.jpg`):
  - 1000 USD net, B2C, USD gives a total of **1,495.00 USD**: subtotal 1,492.54, margin 30%, **Card fee (included in the price) 3%**, effective margin 30.11% (floor 20%). This is unchanged from S236.
  - The FxNotice links to `/pricing/rules?tab=fx`.
  - Switching the selling currency to EUR shows "Missing FX rate: EUR. No approved row is in force for today…" with "Open Pricing rules & FX". The link goes to `/pricing/rules?tab=fx` (followed and checked).
- **Not verifiable read-only:**
  - creating a rule or FX rate (pending);
  - the 403 `own_row` for the maker;
  - a second person approving;
  - a quote priced in EUR (Done-when "USD and one other currency").
  
  Dev has **0 FX rows**, so the non-USD half of the Done-when is still open on Dev, whatever the UI does.

## Regression: dashboard, /cases, /cases/TC-000003, /customers, /pricing/calculator

**Verdict: PASS.** All 20 captures have 0 console errors, all BFF calls 2xx, no overflow at 390, and real Dev data.

## Defects / observations

| # | Severity | Page | Finding | Screenshot |
|---|---|---|---|---|
| 1 | Low | Trip plan detail, "Use for trip case" modal at 390 | The modal (max-height about 90vh) puts its footer inside the scroll area. At 390×844 "Cancel" / "Create trip case" sit below the fold (Cancel top 819 px > 802 px panel bottom) until the user scrolls inside the modal. A sticky footer would keep the primary action visible. | `use-for-trip-case-modal-390-light.jpg`, `…-390-light-scrolled.jpg` |
| 2 | Low | /pricing/rules at 1440 | The table (min width 1100, rendered 1207) is wider than its 1084 px container, so it scrolls sideways at 1440. The Note column gets 82 px, so "ADR 0005 seed — to confirm with Ms. Thư" wraps one word per line and each row is 164 px tall. The Actions column is empty when nothing is pending. | `pricing-rules-1440-light.jpg`, `pricing-rules-1440-light-table-scrolled-right.jpg` |
| 3 | Info | Trip plan Photos tab | Each CIS photo is a 302 redirect then 200. After 1.5 s only 1 of the 6 first tiles had painted (blank tiles); after 8 s all 42 were loaded, with 0 broken. The load is slow, not broken. | `trip-plan-photos-1440-light.jpg` vs `…-after8s.jpg` |
| 4 | Info | Trip plans list | Many tours (for example the first page, A–Z: Agra / Annapurna) have no CIS cover photo (`photo_count 0`) and show the placeholder icon. This is a data gap, not a UI fault. Bhutan rows all have photos. | `trip-plans-1440-light.jpg` |
| 5 | Info | Linear AA-679 | The description and Done-when still describe the outbox sync; the shipped design is D4 live read. Reword the Done-when before closing. | — |
| 6 | Info | Vercel | Project `aa-booking-admin` lives in team `pqnghiep1354-5974s-projects`, so it is not visible to the Vercel MCP for `team_zHOmLxnHRN3EC6hXHbXgTG81`. | — |
| 7 | Info | AA-810 Done-when on Dev | 0 FX rates on Dev. EUR pricing cannot be shown until two different staff enter and approve a rate. | `pricing-rules-fx-*.jpg` |

No blocker or major defect.

## Per-issue verdicts

| Issue | Verdict | Reason |
|---|---|---|
| AA-679 (Booking #11, #12) | **PASS with defects** | List, filters, detail, tabs, CIS photos and the commercial drawer work on live data (892 tours). "Use for trip case" is correctly disabled with 0 sellable plans. Its modal was seen only with a browser-side `sellable=true` mock. Creating a case from a plan was not verifiable read-only. Defect 1. |
| AA-810 (Booking #7) | **PASS with defects** | The rules/FX page, tabs, banner, status pills, both drawers, the FX empty state, the calculator card-fee row and the missing-FX link all work. The Approve dialog was seen only with a mocked pending row. Create, approve, `own_row` and EUR pricing were not verifiable read-only (0 FX rows on Dev). Defect 2. |
| Regression (dashboard, /cases, /cases/TC-000003, /customers, /pricing/calculator) | **PASS** | 0 console errors, all 2xx, no overflow, real data. |
