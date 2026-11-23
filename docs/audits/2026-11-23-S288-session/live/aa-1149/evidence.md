# AA-1149 live verification on Dev (S288, round 1)

Booking: a sold tour becomes one supplier booking per component, can-operate check, admin sale exception
(bk-065, AA-Booking #303 + #304).

- Date: 2026-11-23. Agent: Claude Code (verify subagent). Read-only on systems.
- Identity for the UI and API checks: the A10a read-only E2E Booking staff user (`booking-admin` group; every non-GET
  request is refused `403 e2e_read_only` before any DB access). No Dev-only E2E writer identity has the AA-1149 write
  routes on its allow-list (desk booking, quote, Generate, part waive, sale exception, no-hotel nights), so no write was
  made on any record.

## Deployed build

| Check | Result |
|---|---|
| `GET /booking/health` | 200, `git_sha` = `bd8ed4571a50c5ccaf3b66d45bd0416b85165d02` (the #304 merge commit) |
| `GET /booking/health/ready` | 200, `schema_version` = `bk-065`, `db` ok |
| ECS `aa-booking-dev-api` | one PRIMARY deployment, rollout COMPLETED |
| ECS `aa-booking-dev-admin` | one PRIMARY deployment, rollout COMPLETED, image tag = the same SHA |
| CI on the merge commit | CI, Visual, Change guard, Spec trace, Secret Scan, Docs lint, Deploy Dev, Deploy Admin Dev: all success |
| Booking admin `/login` | 200 |

## Done-when mapping

| # | Done-when line | Result | Evidence / reason |
|---|---|---|---|
| 1a | Confirming a 5-day tour (4 hotel nights, 5 transfers, 1 guide) and pressing Generate creates 10 service bookings from the snapshot | **not checked** | Needs writes no E2E identity may make (set components on a synthetic plan is allowed, but the desk booking / quote, the hold confirm and Generate are not on any allow-list). This is plan step 2 (orchestrator script through ECS exec, A10e staff actor, synthetic agency). Read-only evidence that the code path is live: the Suppliers tab shows the new "Tour components" card; 3 B2B cases sold before the deploy list their tour line with the skip reason `sold_before_split` ("Sold before tours were split: add by hand"); none of the 32 cases on Dev has quote parts yet (no tour sold since the deploy). |
| 1b | Editing the tour afterwards does not change them | **not checked** | Depends on 1a (plan step 2: replace the components, Generate again, compare). |
| 2a | A tour missing the night-2 hotel is blocked for B2B | **partial: pass for the check, not checked for the sale refusal** | `GET …/trip-plans/{id}/operability` on a live tour: `status: blocked`, finding `N1:night:2` "night 2 has no hotel" (level `block`, overridable). Price readiness shows the "Can operate" column with Blocked and the night findings; the `operable=blocked` filter returns only blocked rows. The quote refusal (422 naming N1) needs a quote write: not checked. |
| 2b | An admin exception with a reason unblocks it | **not checked** | Hand step for the tech lead (admin session). Read-only evidence: the "Allow sale…" drawer opens for an admin role, lists the N1 nights, offers only rule N1 for that tour, requires a reason of at least 20 characters, days default 14 and at most 30 (policy `operable_exception_default_days` = 14, `operable_exception_max_days` = 30 from the API), and says a trip sold under it gets a trip check. The drawer was closed without submitting. The same `POST …/sell-exception` from the read-only E2E admin is refused 403 `e2e_read_only`. |
| 2c | A missing transfer only warns | **not checked** | No N4 (destination change without a transfer) finding exists on Dev today: no tour has hotels in two places with components. Warning-level findings do render (an N5 "a guide on some days but not on day 2, 3, 4, 5", level `warn`, not overridable). Needs plan step 3 on the synthetic tour. |
| 3 | CI green, deployed, live check recorded here (Linear) | **partial** | CI green and deploy COMPLETED (table above). The Linear issue has no live-check comment yet (0 comments). |

## Other live facts

### Price readiness, can-operate (`GET /booking/catalog/price-readiness?format=json`)

- 892 trip plans, every row carries `operable`. `summary.by_operable` = ready 0, warnings 0, **blocked 892**, exception 0.
- Findings shown per row (the first 3 of each row): N1 4,794, N2 649, N5 1. No N3 and no N4 shown.
- Why everything is blocked: 890 of 892 plans have no components (readiness tile "No components"; their findings are
  N1 nights and N2 "the tour has no bookable components"); the 2 priced plans have room nights missing (N1). This is the expected Dev state (no real supply), not a defect, but it
  means the readiness page cannot show a Ready tour until the synthetic tour is completed in plan step 2.
- A tour marked "Sellable" still shows Blocked: by design the sellable gate reads price readiness only; the B2B quote
  is the hard block.

### Refused writes by the read-only E2E admin (all `403 {"detail":"e2e_read_only"}`)

| Request | Status |
|---|---|
| `POST /booking/catalog/trip-plans/{id}/sell-exception` (valid body, N1, 14 days) | 403 `e2e_read_only` |
| `POST /booking/catalog/trip-plans/{id}/sell-exception/revoke` | 403 `e2e_read_only` |
| `PUT /booking/catalog/trip-plans/{id}/no-hotel-nights` | 403 `e2e_read_only` |
| `POST /booking/trip-cases/{ref}/supplier-bookings/generate` | 403 `e2e_read_only` |
| `POST /booking/trip-cases/{ref}/supplier-bookings/parts/{part}/waive` | 403 `e2e_read_only` |

### Page health

Readiness, the drawer and both Suppliers tab pages: 0 console errors, 0 uncaught page errors, 0 same-origin HTTP
>= 400, no write sent by a read walk, `data-theme` applied, no horizontal page overflow at 1440 and 390 in light and
dark.

## Screenshots

| File | What |
|---|---|
| `aa1149-readiness__1440__light.png`, `__1440__dark.png`, `__390__light.png`, `__390__dark.png` | Price readiness with the "Can operate" column and filter |
| `aa1149-readiness-blocked__1440__light.png` | Filter "Can operate = Blocked" |
| `aa1149-sell-exception-drawer__1440__light.png`, `__dark.png` | The admin sale exception drawer (not submitted) |
| `aa1149-case-suppliers__1440__light.png`, `__390__dark.png` | Suppliers tab of a synthetic-agency B2B case (an extra-item booking; no tour parts) |
| `aa1149-case-sold-before-split__1440__light.png`, `__dark.png` | Suppliers tab "Tour components" card: a line sold before the split |

## Observations (not blockers)

1. The "Tour components" card labels a pre-split line as `Line <uuid>`; a tour title or line number would read better.
2. The sale exception drawer footer shows both "Cancel" and "Close" next to the in-body "Allow sale" button.
3. `GET /booking/trip-cases?channel=b2b` also returned B2C cases (the list endpoint seems to ignore `channel`); not
   part of AA-1149.
4. The `aa-booking-dev-admin` task definition also holds a `test-wp` container (a public WordPress image) next to
   `booking-admin`. Unrelated to AA-1149; worth checking that it is intended.

## What remains for Done (orchestrator)

1. Plan step 2 to 4 (`.tmp-session/S288/plans/AA-1149.md`, "Live verification"): synthetic tour 4 nights + 5 transfers
   + 1 guide, staff desk booking for the synthetic agency, Generate (expect `created` 10), replace the components and
   Generate again (expect 0, bookings unchanged), remove night 2 (operability blocked `N1:night:2`, quote 422 naming
   N1), remove a destination-change transfer (warning only), then the tech lead's "Allow sale" hand step and a re-quote.
2. DB aggregates: `.tmp-session/S288/live/aa1149_aggregates.py` (counts only).
3. A live-check comment on AA-1149, then cleanup per plan step 7.
