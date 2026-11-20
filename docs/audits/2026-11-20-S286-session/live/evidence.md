---
id: OPS-08-s286-live-evidence
title: "S286 live evidence: My work, lean staff roles (Staff page, Booking finance reads, one sign-in)"
description: "Agent-run Playwright evidence on the Dev hosts for AA-1156 (CIS #1615) and AA-1150 (CIS #1617, Booking #288), 20/11/2026."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-20
review_every_days: 30
related: [AA-1156, AA-1150]
---

# S286 live evidence (20/11/2026, 07:30–07:55 +07)

Headless Chromium (Playwright, one browser at a time). Hosts, after their deploys were green:
CIS admin `https://aa-cis.lumiguides.it.com` (API `/health/ready` git_sha `dd679a32`, schema `461`),
Booking staff admin `https://booking.lumiguides.it.com` (API `/booking/health` git_sha `f8c89580`, schema `bk-061`).

Identities (by role; codes read at run time from the e2e mailbox, never written down; no screenshot on the managed-login
host):

- **CIS content:** the E2E content reviewer (CIS role `content`), codes from `inbound/`.
- **CIS admin:** the Dev-only E2E CIS admin (read-only session, not an owner).
- **Booking finance:** the E2E Booking maker (WORKFORCE group `booking-finance`), via `tools/uat/lib/signin.cjs booking-maker`.
- **One sign-in:** the Dev-only non-admin E2E account `e2e-cis-cs@` (CIS customer success).

Console errors = `console.error` / uncaught page errors on the app origin. Failing requests = responses >= 400 on the
app origin. Raw records in `data/` (ids removed).

## Results

| # | Item (issue + PR) | Result |
|---|---|---|
| A | AA-1156 My work (CIS #1615) | **PASS with finding** (5 of 6 tiles equal their target page through the tile link; Place cards only on a direct load, F1) |
| B | AA-1150 Staff page (CIS #1617) | **Partly not tested**: the presets, "Show all roles" and Add staff render only for a platform owner; the E2E admin is not one |
| C | AA-1150 Booking finance reads (Booking #288) | **PASS** |
| D | AA-1150 one sign-in (spec `one-sign-in.spec.ts`) | **FAIL**: the spec as written stops at `/admin` (F2); a patched copy proves no second prompt, but Booking refuses the account (`reason=forbidden`, F3) |

### A. AA-1156 My work

- Content role lands on `/admin/my-work` after sign-in: **PASS**. The nav shows only My work, AA Catalogue and Platform
  (`data/01-my-work-content.json` `landing`).
- Tiles shown (content: review.act + content.write): Review Queue waiting 73, Supply copy drafts 8, Hotels and services
  with no description 0, AA content drafts 1. Total line "82 items waiting in all": **PASS**
  (`01a-my-work-content-1440-light.png`, `01b-my-work-content-1440-dark.png`).
- Mobile 390 light + dark, no horizontal scroll (document 390/390, `.aa-admin-main` 390/390): **PASS**
  (`01c-my-work-content-390-light.png`, `01d-my-work-content-390-dark.png`).
- Console errors 0, failing requests 0 on My work (content and admin runs): **PASS**.
- Admin lands on `/admin/overview` with "My work" in the Home nav group: **PASS** (`01e-admin-overview-nav-1440-light.png`,
  `data/01-admin-followup-place-cards.json`). The admin sees all 6 tiles.
- Tile count = target page total, by clicking each tile (data `pairs` in `data/01-my-work-content.json` and
  `data/01-my-work-admin.json`):

  | Tile | Tile | Target page (list API `total`, page "of N") | Result |
  |---|---|---|---|
  | Review Queue: waiting | 73 | `/admin/review` → 73, "of 73" | **PASS** |
  | Supply copy: drafts to review | 8 | `/admin/supply-content?has_draft=1` → 8, "of 8" | **PASS** |
  | Hotels and services with no description | 0 | `/admin/supply-content?status=draft` → 0 | **PASS** |
  | AA content: drafts | 1 | `/admin/aa-content?status=draft` → 1, "of 1" | **PASS** |
  | Place cards to review (admin) | 4,859 | via the tile link: list called without `status`, page "of 4,860", status filter empty; direct load of the same URL: `status=auto_checked`, "of 4,859" | **FAIL via tile, PASS direct** (F1) |
  | Compliance holds (admin) | 0 | `/admin/tenant-qa/compliance` (Open tab) → 0 | **PASS** |

### B. AA-1150 Staff page

- Page loads, console errors 0, failing requests 0 (`data/01-my-work-admin.json` `staff`).
- The deployed JS of `/admin/platform/staff` contains "Business owner", "Content + Product & operations",
  "Show all roles", "Custom (show all roles)" and the Booking label "Product & operations" (bundle string scan, run
  output in the lane report). Not a rendering check.
- Three presets shown, other roles behind "Show all roles", Add staff opening on Custom with CIS content: **not tested**.
  The list answers `viewer.is_owner=false, can_write=false` for the E2E admin, so the page shows the read-only line
  and no Add staff button, and the drawer shows "Only a platform owner ... can change roles or access"
  (`02a-staff-e2e-cs-drawer-readonly.png`).
- Booking role label "Product & operations" on screen: **not tested**. No account on Dev holds the Booking
  `contracting` role (Booking roles in the list: none or admin).

### C. AA-1150 Booking finance reads

- `GET /api/booking/staff/me` as the E2E finance maker: role `finance`; permissions include `bill.read`, `pricing.read`,
  `supply.read`, `ops.read`, `trip_case.read`, `catalog.read`, and not `payout.write`, `supplier.activate`,
  `contract.publish`, `stop_sale.approve`: **PASS** (`data/03-booking-finance.json`).
- `GET` supplier-bills, pricing/rules, suppliers, trip-cases through the BFF: 200 each: **PASS**.
- `/suppliers` as finance: list renders (6 suppliers), no Activate or Publish control: **PASS**
  (`03a-booking-suppliers-finance-1440-light.png`).
- An inactive supplier's detail as finance: no Activate button, no Publish: **PASS**
  (`03b-booking-supplier-inactive-detail-finance-1440-light.png`).
- Console errors 0, failing requests 0.

### D. AA-1150 one sign-in

- As the header says (`AWS_PROFILE=aa365-admin E2ECS=1 npx playwright test --project=admin-evidence one-sign-in`):
  **FAIL** at step 2: `page.goto('/admin')` lands on `/login` (F2), timeout 30 s. No trace saved (it stops only at the end).
- Patched local copy (step 2 stays on the sign-in landing page, `/admin/tenants` for customer success): the Booking
  hand-off goes `booking /login` → `/api/auth/signin/cognito` → `staff-auth /oauth2/authorize` → straight back to
  `/api/auth/callback/cognito` with a code, no e-mail field shown: **PASS** for "no second prompt"
  (`data/04-one-sign-in-hops.json`).
- Booking then refuses the account: `/login?reason=forbidden`, "Booking refused this account": **FAIL**, the spec expects
  a `contracting` session (F3) (`04a-one-sign-in-booking-refused-forbidden.png`).
- Trace (holds E2E session cookies, kept local only, not in this folder): worktree
  `.tmp-session/wt/s286-verify-cis/tests/e2e/results/admin-evidence/s286-one-sign-in-trace.zip`.

## Findings

- **F1: Place cards ignores the tile's filter after a client-side navigation.** `frontend/app/admin/places/cards/page.tsx`
  `view = edited ?? (hydrated ? readView() : EMPTY)` reads `window.location.search` during render; on a Next `<Link>`
  navigation from My work the URL is not updated yet, so the list loads unfiltered (4,860) under
  `?status=auto_checked` and the filter select is empty, and nothing re-reads it. Repro: as admin open `/admin/my-work`,
  click "Place cards to review". Proposed fix: read the view from `useSearchParams()` (as Supply copy and AA content do
  since #1615), or render the tile link as a plain `<a>` for this page. Not fixed in this lane.
- **F2: `one-sign-in.spec.ts` step 2 opens bare `/admin`, which has no page rule.** `frontend/proxy.ts` fails closed to
  `/login` (no `PAGE_RULES` entry for `/admin`), and `/login` does not forward a signed-in person. Proposed fix: open
  `landingPage(role)` or just stay on the page the sign-in landed on. Not fixed in this lane.
- **F3: `e2e-cis-cs@` has lost its Booking `contracting` grant.** WORKFORCE groups now: `cis-customer_success` only
  (read-only check). Booking's A10e-2 writer rule (`backend/app/auth/e2e_staff.py`, pricing maker) needs exactly
  `{cis-customer_success, booking-contracting}`, so `check_session` refuses 403 and the callback maps it to
  `reason=forbidden`. The CIS directory also shows Booking role "None". The account still acted in Booking on 14/11
  (supplier activity log), so the group was removed after that.

## Not covered

- Staff presets / "Show all roles" / Add staff default (B): needs a platform owner session.
- Applying a preset: out of scope by instruction.

## Test data written

- None (every call was a read; the E2E sessions are read-only).

## S286 second pass

Run 20/11/2026 09:20–09:27 +07, headless Chromium (Playwright from `tools/uat`, saved E2E sessions from
`tools/uat/lib/signin.cjs`; codes read at run time, never written). Read-only: every call was a GET.

Hosts and builds, checked before the run:

- Booking API `/booking/health` git_sha `b71fca9c` (= Booking #291 merge commit). Booking admin ECS
  `aa-booking-dev-admin:48`, image tag `b71fca9c…`, rollout COMPLETED.
- CIS admin ECS `aa-cis-dev-admin:77`, image `dev-87cbdb2b…` (= CIS #1620 merge commit), rollout COMPLETED. CIS API
  `/health/ready` git_sha `daec5413`, schema `462`.

Identities: **Booking admin (read-only E2E)** `booking` (role `admin`, 10 tile capabilities), **Booking finance maker**
`booking-maker` (role `finance`), **CIS admin (read-only E2E)** `cis-admin`.

| # | Item (issue + PR) | Result |
|---|---|---|
| A | AA-1159 Booking My work (Booking #291) | **PASS with findings** (every tile = its list total for both roles; F4 console 403 on `/cases` as finance, pre-existing; F5 cosmetic) |
| B | AA-1156 Place cards tile after CIS #1620 (F1 fix) | **PASS** (tile 4,859 = list 4,859 via the tile click; F1 closed) |

### A. AA-1159 Booking My work

- `GET /api/booking/my-work/summary`: **200** for both roles. Admin: 10 tiles (6 "work" + 4 "approve"). Finance: 6 tiles
  (`my_open_cases`, `trip_checks_overdue`, `supplier_bills_overdue`, `supplier_bills_due_soon`,
  `agency_invoices_overdue` + `agency_payments_to_approve`), which is exactly its capabilities (no `b2b_desk.read`,
  `bill.approve`, `payout.write`, `stop_sale.approve`): **PASS**.
- The dashboard shows the band with "To do" and "To approve or pay" for both roles: **PASS**
  (`06-booking-my-work-admin-1440-light.png`, `06-booking-my-work-admin-1440-dark.png`,
  `07-booking-my-work-finance-1440-light.png`).
- Tile = filtered total of its target list, by clicking each tile from `/` (list API `total` through the BFF; data
  `data/06-booking-my-work-admin.json`, `data/07-booking-my-work-finance.json` `pairs`):

  | Tile | Tile | Landed on | List call → total | Result |
  |---|---|---|---|---|
  | My open cases | 0 | `/cases?tab=mine&status=<11 open statuses>` | `trip-cases?status=…&assignee=me` → 0, tab "Mine" | **PASS** |
  | Trip checks overdue | 18 | `/trip-checks?due=overdue` | `trip-checks?status=open&due_before=2026-11-19` → 18, tab "Overdue 18", "of 18" | **PASS** |
  | On-request lines (admin) | 3 | `/b2b-desk` | `b2b-desk/on-request?state=open` → 3, tab "On request 3" | **PASS** |
  | Supplier bills overdue | 0 | `/billing?bill_status=open&bill_due=overdue` | `supplier-bills?status=open&overdue=true` → 0 | **PASS** |
  | Supplier bills due soon (3 days) | 0 | `/billing?bill_status=open&bill_due=soon` | `supplier-bills?status=open&due_soon=true` → 0 | **PASS** |
  | Agency invoices overdue | 0 | `/agency-billing?status=overdue` | `agency-invoices?status=overdue` → 0 | **PASS** |
  | Supplier bills to approve (admin) | 0 | `/billing?bill_status=received&approvable=me` | `supplier-bills?status=received&approvable=me` → 0 | **PASS** |
  | Supplier bills to pay (admin) | 0 | `/billing?bill_status=approved&approvable=me` | `supplier-bills?status=approved&approvable=me` → 0 | **PASS** |
  | Agency payments to approve | 0 | `/agency-billing?tab=payments&approvable=me` | `agency-payments?state=recorded&approvable=me` → 0, tab "Payments to approve" | **PASS** |
  | Stop-sales to review (admin) | 0 | `/stop-sales?review=me` | `supply/restrictions?kind=stop_sale&review=me` → 0, "Nothing waits for review" | **PASS** |

  The filter controls on each target page show the tile's filter (for example Billing status `received` + "approvable
  `me`"), so the list is the filtered view, not a default view. Finance gets the same numbers for its 6 tiles.
- Only two queues have items on Dev today (trip checks 18, on-request 3); the other 8 equalities are 0 = 0, so the
  maker-checker subset (`approvable=me`, `review=me`) was not exercised with a non-zero count.
- 1440 + 390, light + dark (`data-theme` follows the scheme), both roles: horizontal scroll none at 390 (document
  390/390, `main` 390/390): **PASS** (`06-booking-my-work-admin-390-light.png`, `06-booking-my-work-admin-390-dark.png`;
  one column of tiles on the phone).
- Console errors and failing requests on the dashboard: 0 for both roles, all 4 viewport/scheme runs. On the target
  pages: 0 for admin; finance gets one (F4): **PASS with finding**.

### B. AA-1156 re-check after CIS #1620

- `/admin/my-work` as the E2E CIS admin: summary 200, 6 tiles; "Place cards to review" **4,859**.
- Click the tile → `/admin/places/cards?status=auto_checked`: one list call
  `content-quality/place-cards?limit=50&offset=0&status=auto_checked` → total **4,859**, page "of 4,859", Card status
  select `auto_checked`: **PASS** (before #1620 the same click gave an unfiltered call, "of 4,860", empty select).
  A direct load of the same URL gives the same call and 4,859 (`08-cis-place-cards-after-tile-click-1440-light.png`,
  `data/08-cis-my-work-recheck.json`).
- Other tiles re-confirmed by click: Review Queue waiting 73 → `/admin/review` "of 73" (Review status `pending`);
  Supply copy drafts 8 → `supply-content?has_draft=1` total 8, "of 8"; AA content drafts 1 → `aa-content?status=draft`
  total 1, "of 1": **PASS**.
- Console errors 0, failing requests 0.

### Findings (second pass)

- **F1 closed** by CIS #1620 (see B).
- **F4: `/cases` calls `GET /booking/staff/directory` for a role without `staff.directory`.** As finance, the "My open
  cases" tile lands on `/cases`, whose assignee picker (`frontend/app/(staff)/cases/_parts/StaffSelect.tsx`, AA-683)
  fetches the directory unconditionally; the API answers 403 and the browser logs a console error. The list itself
  loads (200, total 0). Pre-existing, not from #291. Proposed fix: enable the query only when
  `staff.permissions` holds `staff.directory` (hide or disable the picker otherwise).
- **F5 (cosmetic): "Agency payments to approve" is cut to "Agency payments to appro…"** at 1440 in the 4-column tile
  grid (both roles, both schemes). The aria label is whole. Proposed fix: let the KpiTile label wrap to two lines, or
  shorten it to "Payments to approve".

### Test data written (second pass)

- None. All reads; both E2E sessions are read-only, the finance maker made no write.
