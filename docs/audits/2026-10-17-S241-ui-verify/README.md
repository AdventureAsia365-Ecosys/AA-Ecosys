# S241 UI verify: CIS PR #787 on Dev (17/10/2026)

This was a read-only check of `main` 748c12c (CIS PR #787) on https://aa-cis.lumiguides.it.com. It covers AA-836
(tenant portal), AA-863 (admin seed view) and the S241 admin pollers and Jobs page.

- **Tooling.** Playwright Chromium, headless, one browser at a time, a fresh context for each width and theme. Scripts are in the
  session scratchpad (`uiv/portal.mjs`, `uiv/admin.mjs`), not in the repo. Raw measurements are in `results.json`.
- **Accounts.** The admin is `e2e-claude-code`, from `aa-cis/dev/e2e-test-admin`. The tenant is `atlas-hearth`, using the API key in
  `aa-cis/dev/e2e-tenant/atlas-hearth`. Both are read at run time into process memory only, never printed or saved,
  and no storage state was written to disk.
- **Writes.** The only writes were the login POSTs: 4 tenant logins and 7 admin logins. A route handler aborted every other non-GET
  request, and `blocked_writes` is empty in every run. Nothing was published, picked, cut, cancelled, retried or edited.
  The Jobs drawer "Retry" button was never clicked.
- **Leak scan.** Before each screenshot, the page text was checked for the tenant key, the admin password, Mapbox `pk.eyJ…`
  tokens and JWTs. No hits were found, and `results.json` has none either.
- **Build.** The build is identified by behaviour, not by reading the Vercel deployment. The list XHR carries `fields=summary`, the Jobs header
  reads "Queue idle — auto-refresh paused", the new StickyBar sentinel and band DOM is present, and the catalog drawer no longer calls
  `/v1/tours/pool/{id}`. All four are new in 748c12c.
- **Themes.** Light and dark come from `colorScheme` emulation plus `localStorage.cis_theme`. The admin theme toggle was also
  clicked: Light → Dark (body `rgb(15,20,27)`) → System → Light. The tenant portal is **pinned light by design**
  (`portal/layout.tsx`: `data-theme="light"` on the portal subtree), so the portal "dark" screenshots match the light ones.

## Results

### A) AA-836 tenant portal (atlas-hearth), 1440 and 390, light and dark

| # | Item | Result | Evidence (DOM measurements) | Screenshots |
|---|---|---|---|---|
| A1 | No horizontal overflow at 390 | **PASS** | `scrollingElement.scrollWidth` 390 = `innerWidth` 390 on T11, T10, T4 and Dashboard, in both themes, and also with the T10 and T4 drawers open. At 1440 it is 1440/1440. | `portal/t11-publish-390-*`, `t10-review-390-*`, `t4-pool-390-*`, `dashboard-390-*` |
| A2 | T11 card content ≥ 200 px at 390, button below content | **PASS** | All 3 Ready-to-Publish cards: content column **278 px**, row `flex-wrap: wrap`. Button top is below content bottom: 1573 ≥ 1561, 1777 ≥ 1765, 2022 ≥ 2010. At 1440 the button stays beside an 826 px column, as designed. | `portal/t11-boundary-390-*`, `t11-publish-390-*` |
| A3 | StickyBar does not intersect the previous card at rest | **PASS** | The painted band (aria-hidden layer) overlaps the previous cards (WordPress and Facebook connect cards) by **0 px²** at 1440 and 390, both on load and with the boundary scrolled to the centre (bar still at rest, offset −50). Band top = card top + 1 px. Note: the bar's own layout box is transparent at rest and has `pointer-events: none`. It still starts 28 px above the card and overlaps the Facebook card's bottom 7 px (box only, not painted). When stuck, the band is drawn from the bar top (`top: 0px`). | `portal/t11-boundary-*`, `t11-stuck-*` |
| A4 | My Catalog drawer + "See original content" | **PASS** | All 4 combos: 0 console errors, 0 page errors, 0 non-2xx, **0 requests to `/v1/tours/pool/<id>`**. The drawer's only API call is `GET /api/tenant/v1/tours/versions/9122ca5f-…` 200. After the click, "Hide original content from Adventure Asia" is shown with the original text (11,066 chars). | `portal/t4-drawer-original-*` |
| A5 | No raw `##` / `**` in T11 previews and the T10 drawer | **PASS** (Writer: not checked) | The source data does carry markdown. The 3 `publish-log/pending` previews have 1 `##` each, and the blog item opened in T10 has 7 `##` and 8 `**` in `content_text`. The rendered `innerText` has **0 `##` and 0 `**`** in the Ready-to-Publish card and in the T10 drawer ("Where Two Worlds Meet", blog), which has 4 `<strong>` and 17 `<p>`. | `portal/t11-boundary-*`, `t10-drawer-*` |
| A6 | Dashboard Recent Activity titles: one line with an ellipsis at 390 | **PASS** | 5 of 5 titles: height 16.9 px = 1 line-height, `white-space: nowrap`, `text-overflow: ellipsis`, truncated (`scrollWidth > clientWidth`). Titles are 99 px wide at 390 and 240 px at 1440, and the short-date column is dropped on the phone. Observation: at 390 only about 10 characters show ("Mongolia: K…") because the "READY TO REVIEW" badge takes about 140 px. | `portal/dashboard-recent-*` |
| A7 | ROUTE pill keeps a one-line pill shape | **FAIL** | `border-radius: 999px`, `nowrap`, ellipsis active at 390, **but height 33.5 px against 22.5 px for one line**, at both widths and in both themes. Cause: the badge text now sits in an inner `<span>` that is blockified as a flex item. The `Milestone` icon is a `<svg>` with `display: block` (global CSS) inside that span, so it renders on its own line above the text (svg top 3 px, text below). The pill is a 2-line rounded box, not the old oval but still not one line. Possible fix: keep the icon outside the ellipsis span, or give the inner span `display: inline-flex; align-items: center` (or svg `display: inline`). | `portal/t11-boundary-1440-light.png`, `t11-boundary-390-light.png` |

### B) AA-863 admin seed view (e2e admin), 1440 and 390, light and dark

| # | Item | Result | Evidence | Screenshots |
|---|---|---|---|---|
| B1 | Pieces table Title cell shows the Segment label and "Seed: place · country", with a warning badge on mismatch rows | **PASS** | Header "Title / angle · seed". With filter Terra Family Expeditions + "Built Into the Cliff, Restored", all 9 rows read "Segment: Paro — stroll", "Seed: Tiger's Nest Monastery · Bhutan" and a **PLACE ≠ SUBJECT** badge, in all 4 combos. Tooltip: "Seed atom 01e04f10e1019971 · frozen when the Subject was picked · Subject place: Paro · Segment countries: Bhutan". At 390 the seed line is cut ("…Monastery · B…"); the full text is in the tooltip and the drawer. 0 console errors, 0 non-2xx. | `admin-seed/content-quality-pieces-*`, `content-quality-row-390-*` |
| B2 | Piece drawer "Slate seed" section | **PASS** | Section "Slate seed — the atom this piece was written from": "Segment: Paro — stroll · Seed: Tiger's Nest Monastery · Bhutan · PLACE ≠ SUBJECT". Seen in all 4 combos. | `admin-seed/content-quality-piece-drawer-*` |
| B3 | atom-curation Slate tab (Atlas & Hearth): Seed column; mismatch rows sortable and filterable | **PASS** | Column "Seed (place · country)" is present. 89 rows, **1 mismatch** (Pawangka Monastery · China, PLACE ≠ SUBJECT), which is not first by default. One click on the Seed sort moves it to row 1. Typing `mismatch` in the Seed filter leaves 1 row. No page overflow at 390 (the table scrolls inside its box). 0 console errors, 0 non-2xx. Minor: the sorted `<th>` has no `aria-sort`. | `admin-seed/slate-*`, `slate-sorted-seed-*`, `slate-filter-mismatch-*` |

The "Paro — stroll / Tiger's Nest Monastery" mismatch exists for **Terra Family Expeditions** and **Trail Pulse**, not
for Atlas & Hearth, so B1 and B2 used a Terra Family piece (`21697065-…`). Atlas & Hearth's single Slate mismatch is the
Pawangka Monastery (China) row.

### C) Jobs page and admin shell pollers

| # | Item | Result | Evidence | Screenshots |
|---|---|---|---|---|
| C1 | Default page size 25 | **PASS** | 25 rows. The page-size select value is `25` (options 25/50/100/200). Pager "1–25 of 2,705". The same holds at 1440 and 390, light and dark. | `admin-jobs/jobs-*` |
| C2 | List XHR uses `fields=summary` and returns payload null | **PASS** | `GET /api/admin/job-runner/jobs?page=1&page_size=25&sort=created_at&sort_dir=desc&fields=summary` 200. All 25 rows have `payload: null` and `result: null`; the keys are still present. | `admin-jobs/jobs-1440-light.png` |
| C3 | Idle queue: the header says auto-refresh is paused and no further list request fires for 70 s | **PASS** | Queue: queued 0, running 0. Header: "Queue idle — auto-refresh paused; use Refresh." The only list request is at t = 1.6 s. **Zero `/api/*` requests of any kind** in the 72 s window from t = 4 s to t = 76 s (tab `visible`), and the header is unchanged afterwards. | `admin-jobs/jobs-1440-light.png` |
| C4 | Job drawer shows payload/result from `/jobs/{id}` | **PASS** | On click: `GET /api/admin/job-runner/jobs/{id}` and `…/llm-calls?limit=200`. Cancelled `x6_probe` shows Payload `{"probe":"AA-751"}` and no result. A succeeded `ops_rds_role_connections` job (390) shows Payload `{"trigger":"schedule"}` and Result `{"roles":{"booking":{"pct":6.67,…}}}`. | `admin-jobs/jobs-drawer-1440-light.png`, `jobs-drawer-succeeded-390-light.png` |
| C5 | Over 130 s: `notifications/count` about 1–2 times, `review-queue` about once | **PASS** | On `/admin/content-quality` at 1440: notifications/count at t = 0.9 s and 121.7 s (2), review-queue once at 0.9 s. At 390: 1.1 s and 122.1 s (2), review-queue once at 1.1 s. | `admin-jobs/shell-1440-light.png`, `shell-390-light.png` |
| C6 | One review-queue count request although the Sidebar and BottomNav both show it | **PASS** | At 390 the BottomNav is visible with the Review badge "25", and the Sidebar is mounted (`data-hydrated="true"`). There is a single `GET /api/admin/review-queue?status=pending&page=1&page_size=1` per load. | `admin-jobs/shell-390-light.png` |

## Defects and observations

1. **A7 FAIL (Low, tenant-facing, AA-836): the ROUTE pill renders on 2 lines** (icon above the text, 33.5 px). See the fix
   options in A7.
2. Observation (likely pre-existing, outside A3's at-rest scope): when the T11 "Ready to Publish" bar is **stuck**, a
   strip of scrolled content shows between the topbar and the bar. The strip is 28 px at 1440 (y 56–84) and about 20 px at 390. The stuck bar's
   top sits at the scroll container's padding edge, so the 28 px bleed band lies inside the bar instead of above it.
   The stuck geometry is the same as before PR #787 by code reading, but it was not compared against an older build.
   See `portal/t11-stuck-*`.
3. Observation: Dashboard Recent Activity at 390 shows only about 10 characters of each title. The checked requirement is met; the
   status badge takes the width.
4. Observation: the seed country is truncated in the 390 Pieces card (tooltip and drawer show it in full). Also, `aria-sort` is missing
   on the sortable Slate headers.

## Not checked

- **Social Content Writer panel, finished piece (A5).** It only opens after "Pick to write" in this visit (a write plus a paid
  T8/T9 run). The drawer uses the same `MarkdownBody` as the T10 drawer, which passed, but the Writer panel itself was not rendered.
- The StickyBar on the Slate page (`/portal/t7-planning`, SlateTab) was not measured; only T11 was.
- T10: one drawer was opened (blog "Where Two Worlds Meet"). T4: only the first "Open →" tour was opened.
- Jobs **active-queue polling** (30 s while queued/running) was not checked, because the queue was idle and enqueuing would be a write.
  The 70 s idle window ran at 1440 light only.
- Pollers: tested only in a visible headless tab. Not checked: hidden-tab pause, refetch on focus, the 180 s review-queue
  interval (the window was 130 s, shorter than 180 s), and badge refresh after a review action (a write).
- Server-side parts of PR #787 (verify-admin 5 min cache, BFF body streaming, seed audit SQL) were not checked beyond the
  pages working with 0 non-2xx.
- The deploy SHA was not read from Vercel or ECS (inferred from behaviour, see above). Only Chromium was used; Safari and real
  touch devices were not tested.
