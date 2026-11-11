# Booking staff admin: signed-in UAT on Dev (S277, 11/11/2026)

Agent-run Playwright smoke of the deployed Booking staff admin (`booking.lumiguides.it.com`, admin build `2d70c96`),
signed in as the read-only E2E staff user (`booking-admin` group; the backend refuses every write with 403
`e2e_read_only`). Covers the departures operations and finance work shipped to Dev. Suite: AA-Booking
`frontend/e2e/signed-in/` (Playwright projects `signed-in-setup` + `signed-in`).

Command (from `frontend/`, with an MFA session on the admin profile so the mailbox can be read):

```
AWS_PROFILE=aa365-admin AWS_REGION=us-west-1 npm run test:signed-in
```

`BOOKING_E2E_REUSE_STATE=1` reuses a still-valid saved session (no new sign-in code). Output: `frontend/e2e/results/`
(gitignored).

## Run summary

Run 1 signed in with an emailed one-time code (about 20 s); runs 2 and 3 reused the session. The PNGs here are from
run 3: 6 passed, 1 skipped, 1.5 min. In every test: 0 console errors, 0 uncaught page errors, 0 same-origin HTTP >= 400,
no write request sent. In all 36 shots the theme was applied (`data-theme`) and nothing overflowed horizontally.

| Test | Result | Notes |
|---|---|---|
| Shell + `GET /api/booking/staff/me` | pass | role `admin`, active, not a preview session; profit / pricing / bill / ops / supply / B2B desk read permissions present |
| Costs & profit: Profit, Departure costs, Purchase orders tabs | pass | Profit: rows (period "Any date"); Departure costs: rows; Purchase orders: kit empty state |
| Trip case Suppliers tab: cost in USD | pass | a Dev case with 2 supplier bookings; the USD line (planned, billed, variance, FX difference, best cost) shows |
| Trip plan Departures tab + departure drawer | pass | 5 departures; a row click opens the drawer; rule fields (seats, minimum, sales cutoff, decision days) and Agency allotments load |
| B2B desk: Departures at risk tile + Departures & incidents tab | pass | tile shows 0 (no departure at risk on Dev), summary API carries `departures_at_risk` |
| Agency bookings tab + departure manifest | skipped | not deployed on Dev yet (no "Agency bookings" tab on /b2b-desk) |

## Screenshots

Each page at 1440 x 900 and 390 x 844, light and dark: `<page>__<width>__<theme>.png`. Staff pages scroll inside the
main column, so a shot shows the part named under "Focus".

| Page | Path | Focus | Result |
|---|---|---|---|
| `home` | `/` | top of the dashboard | pass |
| `finance-profit` | `/finance?period=all` | first profit row | pass |
| `finance-departures` | `/finance?tab=departures` | first departure row | pass, see finding 1 |
| `finance-orders` | `/finance?tab=orders` | empty state | pass |
| `case-costs-usd` | `/cases/<code>?tab=suppliers` | Cost vs billed, USD line | pass, see finding 2 |
| `trip-plan-departures` | `/catalog/trip-plans/<id>?tab=departures` | first departure row | pass |
| `departure-drawer` | the same, `&departure=<id>` | Agency allotments in the drawer | pass |
| `b2b-desk` | `/b2b-desk` | KPI tiles, Departures at risk | pass |
| `b2b-desk-departures` | `/b2b-desk?tab=departures` | first departure row | pass |

## Findings (UI, not blocking)

1. **Costs & profit → Departure costs: the Tour column shows the raw catalog id** (`000e3340-d9f5-…`), not the tour
   name. The B2B desk departures list shows the title through its tour-title lookup; the finance departures list does
   not. Fix: add the tour title to `GET /booking/finance/departures` (same lookup as the desk) and render
   `tour_title ?? "Tour <id prefix>"`. Not fixed in this lane, because another open change of the same wave edits the
   same backend file and tab.
2. **Case Cost vs billed: two USD summary lines** for a case costed in USD: the AA-1074 USD line (planned, billed,
   variance, FX difference, best cost) and the older per-currency totals line (`USD: net … · billed … · variance —`).
   The second line repeats the first when the only currency is USD. Cosmetic.
3. No departure is at risk on Dev, so the drawer's "Short of its minimum" banner was not seen live (the spec checks it
   when Dev has an at-risk departure).
