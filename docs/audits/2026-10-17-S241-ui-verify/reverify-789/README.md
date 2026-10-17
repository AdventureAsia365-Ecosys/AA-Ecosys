# S241 re-verify: CIS PR #789 on Dev (17/10/2026)

This is a read-only re-check, on https://aa-cis.lumiguides.it.com, of the defects that `../README.md` reported against PR #787 (A7 and
observations 2–4), plus the critic notes (Slate tab at 390, Jobs drawer close X, legend pills, drawer titles, My Catalog drawer
title). The build under test is CIS `main` cafd13a8 (PR #789).

- **Build identification.** The build was identified by behaviour; the Vercel deployment was not read. Every change below is new in
  cafd13a8: the StickyBar has `top: -28px`, the portal Badge has a separate icon flex item, the Recent Activity grid at 390 is
  `36px 266px` with no badge column, the kit Drawer title box is `flex: 1; min-width: 0; overflow-wrap: anywhere`, and the My
  Catalog drawer title shows the tour name.
- **Tooling.** Playwright Chromium, headless, with a fresh context for each width and theme. The scripts are in the session scratchpad
  (`uiv/reverify.mjs`, `reverify2.mjs`, `reverify3.mjs`), which reuse the login, write-blocking and leak-scan code from the earlier
  `admin.mjs` and `portal.mjs`. Raw measurements are in `results.json`.
- **Accounts.** The admin is `e2e-claude-code` (`aa-cis/dev/e2e-test-admin`). The tenant is `atlas-hearth`
  (`aa-cis/dev/e2e-tenant/atlas-hearth`). Both secrets are read into process memory only.
- **Writes.** The only writes were the login POSTs: 2 tenant logins and 3 admin logins. A route handler aborted every other non-GET request, and
  `blocked_writes` is empty in all runs. Nothing was published, picked, retried, cancelled or edited. The only control clicked
  in a drawer was the Jobs drawer close X. The sort and the column filter are client-side only.
- **Leak scan.** Before every screenshot, the page text was checked for the tenant key, the admin password, `pk.eyJ…` and JWTs. There were
  0 hits, and `results.json` has none.
- **Themes.** The admin pages were checked at 1440 and 390, in light and dark. The tenant portal is pinned light (`data-theme="light"` was read
  on the portal subtree), so it was checked at 1440 and 390 in light only.

## Results

| # | Item | Result | Measurement (DOM) | Screenshots |
|---|---|---|---|---|
| 1 | ROUTE pill on `/portal/t11-publish`: one line (≤ 24 px), with the icon and text on one line | **PASS** | All 3 ROUTE pills, at 1440 and 390: height **22.5 px** (was 33.5). Inside the pill, the svg (11 px, top 5.8) and the text box (16.5 px, top 3) share a vertical centre of **11.3 px**, and the svg sits left of the text. At 390 the pill is 278 px wide and ends in an ellipsis (`text-overflow: ellipsis`, truncated). At 1440 it is not truncated (626 / 745 px). | `t11-1440-light.png`, `t11-390-light.png`, `t11-rest-*-light.png` |
| 2 | T11 StickyBar when stuck: nothing but the band or bar between the topbar and the bar; at rest, no overlap with the previous card | **PASS** | **Stuck** (band `top: 0px`, bar `top: -28px`). At 1440 the bar box starts at y **56**, which is the topbar bottom and `<main>` top; bar content starts at 106. At 390 the bar box starts at y 48, clipped by `<main>` at 56; content starts at 98. `elementFromPoint` was sampled every 10 px × 2 px across the scrollport, from y 56.5 to the bar content top. At 1440 that was **3,025 samples with 0 hits outside the bar and its ancestors**, and at 390 it was 819 samples with 0 hits, so no card content shows in the strip. **At rest**, the painted band overlaps the previous card and its children by **0 / 0 / 0 px²** at both widths. The band starts 1 px below the card top. The transparent bar box still has `pointer-events: none`. | `t11-stuck-1440-light.png`, `t11-stuck-390-light.png`, `t11-rest-*-light.png` |
| 3 | T11 previews: no raw `##`/`**`, and the heading does not run into the body | **PASS** | There are 3 pending pieces, and each raw `content_preview` starts with `## …`. **Piece A:** the heading equals the card title ("Where Two Worlds Meet: …"), so it is **dropped**, and the preview starts "There is a line in northern Mongolia…". **Pieces B and C:** the heading differs from the card title (the angle name), so it is kept and followed by **" · "**: "What a Bolt of Cloth Can Tell You About a Country · In the National Textile Museum…" and "The Weight of 1937 · 1937. For a moment…". All 3 have 0 `##` and 0 `**`, and none starts with its card title. The result is the same at 1440 and 390. | `t11-1440-light.png`, `t11-stuck-390-light.png` |
| 4 | Dashboard Recent Activity at 390: title ≥ 200 px, one line, ellipsis; badge on the meta line | **PASS** | At 390, all 5 rows: title **245 px** wide in a 266 px row (was 99 px), height 16.9 px = 1 line, `nowrap` + `ellipsis`, truncated. The grid is `36px 266px`. The "READY TO REVIEW" badge is inside the text column, **below the title**, on the date line. At 1440 nothing changed: the title is 240 px and the badge has its own column. | `dashboard-recent-390-light.png`, `dashboard-recent-1440-light.png` |
| 5 | `/admin/atom-curation` Slate tab at 390 (Atlas & Hearth): no sideways scroll; header indent; scrollLeft 0 after sort and filter | **PASS** (see observations O2 and O3) | At 390, light and dark, before sorting, after the Seed sort, after the `mismatch` filter and after scrolling to the result row: `.aa-admin-main` scrollWidth **390 = clientWidth 390**, scrollLeft **0**, the document 390/390 with scrollLeft 0, and **no ancestor of the table** (table → … → html) has scrollWidth > clientWidth or a non-zero scrollLeft. The table's own `overflow-x: auto` wrapper scrolls (849–1,110 / 356 px). Two elements outside the table also report scrollWidth > clientWidth. The sub-nav tab strip `.a527-inner-sidebar` (1157/357) is horizontal by design (`overflow-x: auto`, not an ancestor of the table). The BottomNav Review count badge "25" is 28/20 px. **Header indent:** the "Social Content" h1 left is **16 px**, the same as Jobs (16) and Content Quality (16); it was 48. The filter leaves **1 row**: "Seed: Pawangka Monastery · China", with a PLACE ≠ SUBJECT badge. At 1440 there are no offenders and main is 1204/1204. | `slate-390-*.png`, `slate-sorted-filtered-mismatch-390-*.png`, `slate-mismatch-row-390-*.png` (result row with its Seed cell), `slate-*-1440-*.png` |
| 6 | `/admin/jobs` drawer at 390, long kind (`ops_rds_role_connections`): close X inside the viewport and clickable | **PASS** | All 4 combos. At 390 the X is at x **352–370** (viewport 390), and `elementFromPoint` at its centre hits the X. The kind is one line with an ellipsis ("ops_rds_role_conne…", 210 px, `title` attribute holds the full kind). The SUCCEEDED badge keeps its size. Clicking the X closes the drawer: the dialog count is 0 and `job=` is gone from the URL. At 1440 the X is at 1402–1420 and the kind is not truncated. | `jobs-drawer-390-light.png`, `jobs-drawer-390-dark.png`, `jobs-drawer-1440-*.png` |
| 7 | Content Quality piece drawer at 390: BLOCKING/WARNING legend pills ≤ 24 px | **PASS** | BLOCKING **22.5 px** (82 px wide) and WARNING **22.5 px** (76 px), radius 999, while the helper text beside them is 52 px tall (3 lines). They were about 50 px. The result is the same in dark and at 1440. | `cq-piece-drawer-legend-390-*.png`, `cq-piece-drawer-legend-1440-*.png` |
| 8 | Long string titles in other kit drawers still wrap fully | **PASS** for string titles; **FAIL** for pills inside titles (see R1) | The Content Quality tour-version drawer title "Laos to Vietnam by Bicycle: Nam Ou River to Hanoi — 12 Days — Terra Family Expeditions v6" **wraps to 3 lines at 390** (319 × 77 px) and 2 lines at 1440. There is no horizontal overflow, no clipped child and no ellipsis, and the X stays in view (352–370). The piece drawer title ("Built Into the Cliff, Restored From Ash") also wraps fully. | `cq-version-drawer-*.png`, `cq-piece-drawer-header-*.png` |
| 9 | T4 My Catalog drawer: the Drawer title shows the tour name | **PASS** | The kit Drawer title reads "**Mongolia: Khövsgöl Lake and Gobi Desert — 15 Days**" (1 line at 1440, 2 lines at 390, not clipped, X in view). The body header now shows only `en-US`, so the name is not repeated. | `t4-drawer-1440-light.png`, `t4-drawer-390-light.png` |

### Console and network, per page

| Page | Console errors | Page errors | Non-2xx |
|---|---|---|---|
| `/portal/t11-publish` (1440, 390) | 0 | 0 | 0 |
| `/portal/dashboard` (1440, 390) | 0 | 0 | 0 |
| `/portal/t4-pool` + drawer (1440, 390) | 0 | 0 | 0 |
| `/portal/t10-review` + drawer (1440, 390) | 0 | 0 | 0 |
| `/admin/atom-curation?section=slate` (4 combos, + 2 row probes) | 0 | 0 | 0 |
| `/admin/jobs?kind=ops_rds_role_connections&status=succeeded` + drawer (4 combos) | 0 | 0 | 0 |
| `/admin/content-quality?piece=…` (4 combos × 2 runs) | 0 | 0 | 0 |
| `/admin/content-quality?tab=versions` + drawer (4 combos) | 0 | 0 | 0 |
| `/admin/jobs`, `/admin/content-quality`, `/admin/review-queue` (header-indent probe) | 0 | 0 | One **307** on `/admin/review-queue`: my probe opened a URL that the app redirects. This is not a page defect. |

## New defect found in this re-check

**R1 (regression from #789, Low–Medium, tenant-facing): pills inside kit Drawer titles break letter by letter.** The new
`overflow-wrap: anywhere` on the kit Drawer title box (`frontend/app/_kit/Drawer.tsx`) is inherited by every title node. In
a flex row, that lowers the min-content width of a pill, so the pill shrinks and its text breaks between letters.

- **T10 My Content drawer (portal, tenant-facing).** The channel pill "BLOG" stacks as **B / L / O / G**: 38 × **72 px** at 390, and
  51 × 39 px ("BL / OG") at 1440. In the PR #787 screenshot (`../portal/t10-drawer-390-light.png`) it was a one-line pill.
  See `t10-drawer-header-390-light.png` and `t10-drawer-header-1440-light.png`.
- **Content Quality piece drawer (admin).** The status pill "APPROVED" becomes a 59 × **55.5 px** circle ("APPR / OVE / D") at 390,
  in light and dark. It was one line before #789 (`../admin-seed/content-quality-piece-drawer-390-light.png`). At 1440 it is fine
  (22.5 px). See `cq-piece-drawer-header-390-*.png`.
- **Not affected.** The Jobs drawer wraps its StatusBadge in `flexShrink: 0` and is fine.
- **Possible fixes** (not applied, this was read-only): give pills `flex-shrink: 0` / `white-space: nowrap` where they sit in a
  title (ReviewList.tsx T10 title, PieceDrawer.tsx header), or set `overflow-wrap: normal` on the kit `Badge` and the portal
  `Badge`, so that only the free text in a title breaks anywhere.

## Observations (not regressions of #789)

- **O1: T4 drawer has two close X buttons.** One is in the kit Drawer header. The other is in CatalogDrawer's own body header, next to
  `en-US`. This was already true before #789 (the kit title was empty and the X was there), but it is more visible now that the title
  row holds the tour name. In the same drawer at 390, the Highlights chips are cut on the right ("…(founded 1727): one o").
- **O2: Slate tab at 390, small scroller and a covering sticky strip.** The page header (title, description, Tour/Market filters,
  6 stat cards) sits outside the body scroller, so on an 844 px phone the body scroller is only **201 px tall** (y 559–760). Inside
  it, the sticky "PROPOSED / PICKED / USED / CUT" strip is 80 px tall and covers the table header and the top of the result row
  (`elementFromPoint` on the row hits the strip). The row itself is 241 px tall. The filtered row is still readable after scrolling
  (see `slate-mismatch-row-390-*.png`), but the view is cramped. #789 did not touch this layout.
- **O3: Header indent at 1440 differs between admin pages.** The h1 left is 268 (Social Content), 272 (Jobs) and 260 (Content Quality).
  This is not from #789 (`padX` stays 32 at 1440); at 390 all three are 16.
- **O4: The `aria-sort` attribute is still missing** on the sortable Slate `<th>` headers (carried over from the first report).

## Not checked

- Safari and real touch devices (only Chromium was used). The portal in dark mode was not checked (the portal is pinned light).
- T10: only the "Where Two Worlds Meet" blog drawer was opened. T4: only the first "Open →" tour. The Writer panel was not rendered (opening it needs a pick, which is a write).
- Other drawers that may hold pills in their titles (`admin/review/page.tsx`, `PlaceCardFactsDrawer`, `SettingsKitTab`) were not opened. By
  code reading, review/page.tsx and SettingsKitTab pass plain strings.
- The StickyBar on other portal pages (ReviewList, the Slate tab in `/portal/t7-planning`) was not measured; only T11 was.
- The deploy SHA was inferred from behaviour (see above), not read from Vercel.
