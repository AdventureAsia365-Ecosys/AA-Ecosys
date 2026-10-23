# AA-910 — Booking staff admin tables at 1440 px (S249, 24/10/2026)

Repeatable layout check, committed in AA-Booking (branch `feat/aa-910-layout-check`): Playwright project
`layout-mock`, `npm run build && npm run test:layout` in `frontend/`.

- **How**: the production build (`next start`) with the Booking API mocked. Browser calls to the BFF
  (`/api/booking/*`) are answered by route interception from typed worst-case fixtures (`e2e/layout/fixtures.ts`:
  25-row pages, long names and e-mails, every status, seven FX rows); the one server-side call (`staff/me`) goes to a
  local stub. The session is an unsigned token that `proxy.ts` only decodes; the real API verifies signatures, and no
  app code reads a test flag (a signed-in check is not possible: the E2E staff account has no Booking role on
  purpose).
- **Viewports**: 1440 x 900 light and dark, a 1280 x 800 squeeze (light, measured only) and 390 x 844 phone (light).
  Chromium (Playwright 1.59) with scrollbars on (`<main>` scrollbar 6 px), Poppins loaded from Google Fonts.
- **Result: 88 / 88 tests pass** (22 page entries). On every page and viewport: horizontal page scroll 0 (document and `<main>`),
  console errors 0, unmocked API calls 0, tab strips 0 px overflow (no 1 px scrollbar). At 1440 every table fits its
  frame with at least 20 px to spare (min-content vs frame); FX currency / rate / buffer / as-of / source cells
  35 / 35 on one line. At 1280 wide tables scroll inside their own box and the row-menu column stays pinned and in
  view.

| Page | Path | 1440 light: table min-content / frame px | Slack px | 1440 dark | 1280 light | 390 light | Screenshots |
|---|---|---|---|---|---|---|---|
| dashboard | `/` | 764 / 1078 | 314 | page 0, fits | page 0 | page 0 | [1440 light](dashboard-1440-light.png) · [1440 dark](dashboard-1440-dark.png) · [390](dashboard-390-light.png) |
| cases | `/cases` | 1039 / 1078 | 39 | page 0, fits | page 0, table scrolls in its box | page 0 | [1440 light](cases-1440-light.png) · [1440 dark](cases-1440-dark.png) · [390](cases-390-light.png) |
| case-proposals | `/cases/TC-000001?tab=proposals` | 703 / 1078 | 375 | page 0, fits | page 0 | page 0 | [1440 light](case-proposals-1440-light.png) · [1440 dark](case-proposals-1440-dark.png) · [390](case-proposals-390-light.png) |
| proposals | `/proposals` | 1004 / 1078 | 74 | page 0, fits | page 0, table scrolls in its box | page 0 | [1440 light](proposals-1440-light.png) · [1440 dark](proposals-1440-dark.png) · [390](proposals-390-light.png) |
| customers | `/customers` | 1044 / 1078 | 34 | page 0, fits | page 0, table scrolls in its box | page 0 | [1440 light](customers-1440-light.png) · [1440 dark](customers-1440-dark.png) · [390](customers-390-light.png) |
| customer-cases | `/customers/CUS-000001?tab=cases` | 476 / 1086 | 610 | page 0, fits | page 0 | page 0 | [1440 light](customer-cases-1440-light.png) · [1440 dark](customer-cases-1440-dark.png) · [390](customer-cases-390-light.png) |
| trip-plans | `/catalog/trip-plans` | 944 / 1078 | 134 | page 0, fits | page 0, table scrolls in its box | page 0 | [1440 light](trip-plans-1440-light.png) · [1440 dark](trip-plans-1440-dark.png) · [390](trip-plans-390-light.png) |
| trip-plans-orphaned | `/catalog/trip-plans?show=orphaned` | 602 / 1078 | 476 | page 0, fits | page 0 | page 0 | [1440 light](trip-plans-orphaned-1440-light.png) · [1440 dark](trip-plans-orphaned-1440-dark.png) · [390](trip-plans-orphaned-390-light.png) |
| suppliers | `/suppliers` | 1055 / 1078, pinned ⋯ | 23 | page 0, fits | page 0, table scrolls in its box, ⋯ pinned | page 0 | [1440 light](suppliers-1440-light.png) · [1440 dark](suppliers-1440-dark.png) · [390](suppliers-390-light.png) |
| supplier-contracts | `/suppliers/SUP-000001?tab=contracts` | 1053 / 1086, pinned ⋯ | 33 | page 0, fits | page 0, table scrolls in its box, ⋯ pinned | page 0 | [1440 light](supplier-contracts-1440-light.png) · [1440 dark](supplier-contracts-1440-dark.png) · [390](supplier-contracts-390-light.png) |
| supplier-rates | `/suppliers/SUP-000001?tab=rates` | 948 / 1086, pinned ⋯ | 138 | page 0, fits | page 0, table scrolls in its box, ⋯ pinned | page 0 | [1440 light](supplier-rates-1440-light.png) · [1440 dark](supplier-rates-1440-dark.png) · [390](supplier-rates-390-light.png) |
| hotels | `/hotels` | 1056 / 1078, pinned ⋯ | 22 | page 0, fits | page 0, table scrolls in its box, ⋯ pinned | page 0 | [1440 light](hotels-1440-light.png) · [1440 dark](hotels-1440-dark.png) · [390](hotels-390-light.png) |
| hotel-drawer | `/hotels?hotel=HTL-000001` | 1056 / 1078, pinned ⋯; 803 / 831, drawer | 22 | page 0, fits | page 0, table scrolls in its box, ⋯ pinned | page 0 | [1440 light](hotel-drawer-1440-light.png) · [1440 dark](hotel-drawer-1440-dark.png) · [390](hotel-drawer-390-light.png) |
| services | `/services` | 1058 / 1078, pinned ⋯ | 20 | page 0, fits | page 0, table scrolls in its box, ⋯ pinned | page 0 | [1440 light](services-1440-light.png) · [1440 dark](services-1440-dark.png) · [390](services-390-light.png) |
| service-rates | `/services/SVC-000001?tab=rates` | 755 / 1086 | 331 | page 0, fits | page 0 | page 0 | [1440 light](service-rates-1440-light.png) · [1440 dark](service-rates-1440-dark.png) · [390](service-rates-390-light.png) |
| pricing-rules | `/pricing/rules` | 1017 / 1078 | 61 | page 0, fits | page 0, table scrolls in its box | page 0 | [1440 light](pricing-rules-1440-light.png) · [1440 dark](pricing-rules-1440-dark.png) · [390](pricing-rules-390-light.png) |
| pricing-fx | `/pricing/rules?tab=fx` | 1045 / 1078 (FX cells one line: 35 / 35) | 33 | page 0, fits | page 0, table scrolls in its box | page 0 | [1440 light](pricing-fx-1440-light.png) · [1440 dark](pricing-fx-1440-dark.png) · [390](pricing-fx-390-light.png) |
| b2b-desk-on-request | `/b2b-desk` | 1024 / 1078 | 54 | page 0, fits | page 0, table scrolls in its box | page 0 | [1440 light](b2b-desk-on-request-1440-light.png) · [1440 dark](b2b-desk-on-request-1440-dark.png) · [390](b2b-desk-on-request-390-light.png) |
| b2b-desk-departures | `/b2b-desk?tab=departures` | 926 / 1078 | 152 | page 0, fits | page 0, table scrolls in its box | page 0 | [1440 light](b2b-desk-departures-1440-light.png) · [1440 dark](b2b-desk-departures-1440-dark.png) · [390](b2b-desk-departures-390-light.png) |
| staff | `/staff` | 870 / 1078 | 208 | page 0, fits | page 0 | page 0 | [1440 light](staff-1440-light.png) · [1440 dark](staff-1440-dark.png) · [390](staff-390-light.png) |
| staff-cases | `/staff/u-001?tab=cases` | 741 / 1078 | 337 | page 0, fits | page 0 | page 0 | [1440 light](staff-cases-1440-light.png) · [1440 dark](staff-cases-1440-dark.png) · [390](staff-cases-390-light.png) |
| audit-log | `/audit-log` | no kit table (entry feed) | – | page 0, fits | page 0 | page 0 | [1440 light](audit-log-1440-light.png) · [1440 dark](audit-log-1440-dark.png) · [390](audit-log-390-light.png) |

Full per-test numbers (all viewports, column widths, FX cells, tab strips): [measurements.md](measurements.md),
[measurements.json](measurements.json).

## Before the fix (origin/main `9e7b774`, same check)

| Page | Measured | Cause |
|---|---|---|
| `/cases` | table 1526 / 1078 at 1440 (scrolls) | person cell without max width (570 px e-mail), 8 columns |
| `/customers` | table 1362 / 1078 | same person cell |
| `/staff` | table 1166 / 1078 | same person cell |
| hotel drawer rates | 837 / 831 | the drawer's own 6 px scrollbar (S248 measured with hidden scrollbars) |
| `/audit-log` at 1280 | `<main>` 1099 / 1026 (page scrolls sideways) | long entity label in a no-wrap `Code` |
| dashboard, supplier contracts, FX tab | 3 / 13 / 13 px to spare | under the 20 px margin |
| `/b2b-desk` on-request (AA-975, merged to main during S249) | 1124 / 1078 | supplier name sub-line without a cap next to two action buttons |

Fixes in the same Booking branch (details: AA-Booking `docs/implementation-notes/AA-910.md`, section S249).

## Not covered

- Real Dev data and a real staff session (by design: mocked API, no sign-in). The fixtures are longer than typical
  rows, so this is the stricter case.
- Firefox / Safari, and 390 px in dark (geometry does not depend on the theme).
- Not wired into Booking CI (run ~4.7 min plus build and browser download); the command is in
  `frontend/README.md`.
