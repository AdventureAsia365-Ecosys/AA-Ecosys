# S237 UI verify: summary

Read-only verification of the UI shipped in S237 (15/10/2026), workflow `wf_dd57cfa2-340`: one Playwright agent per
area (1440/390 x light/dark, console, network, data, the issue's feature), then an independent reviewer that tried to
refute each verdict from the screenshots and raw results. The verdicts below are **after** that review. Per-area
details: `cis-admin/`, `cis-portal/`, `booking/`, `tripplanner/` (README + results.json + screenshots).
`portal-668/` and `tp-812/` are earlier build-time screenshots from the lane agents.

Accounts: E2E admin `e2e-claude-code`, E2E tenant `atlas-hearth`; credentials read from Secrets Manager at run time,
never written. Writes: the login POST only. A scan of this folder for tokens (Mapbox, Vercel share, bearer, API keys)
found none.

## Verdicts

| Area | Issue | Verdict | Note |
|---|---|---|---|
| CIS admin | AA-819 daily publish limit override (Tenant 360 > Settings) | **PASS** | "20/day (default)", validation 1..1000, Save disabled until valid; 0 console errors |
| CIS admin | AA-791 per-attempt gate ledger + Label | **NOT VERIFIABLE** | Label section + LABEL column/filter render; the per-attempt ledger needs a T9 write with 2+ attempts after the deploy (none yet) |
| CIS admin | AA-802 silent correction + "older copy" | **NOT VERIFIABLE** | Version drawer edit note, flagged sentences with Cut/Rewrite/Edit render; "older copy" needs an admin edit on a published/exported item (a write) |
| CIS admin | AA-668 writer panel | **NOT VERIFIABLE** here | Tenant-portal feature; needs a tenant session + Subject pick + paid T8/T9 run. Build-time screenshots in `portal-668/` |
| Tenant portal | AA-815 Facebook connect option, per-channel gating | **PASS with defects** | Connect Facebook Page card renders; the permission name reads `pages_manage_post spermission` (D5, wrong name shown to tenants) |
| Tenant portal | AA-815 connected state, Disconnect, Unpublish | **NOT VERIFIABLE** | All 4 E2E tenants have no connected channel and 0 published posts |
| Tenant portal | AA-819 AI notice at review / publish / export | **PASS** | |
| Tenant portal | AA-819 daily publish limit notice | **NOT VERIFIABLE** | No up-front quota line in the portal; only the 429 message on the 21st publish (not built as a visible counter) |
| Tenant portal | Product rule "tenant sees content only" | **PASS** | No gate/flag/held/QA wording on the pages opened |
| Booking | AA-679 trip plans (list, detail, use for trip case) | **PASS with defects** | 892 plans, 0 sellable on Dev; 390 modal footer below the fold; disabled button contrast (light) |
| Booking | AA-810 pricing rules + FX rates (maker-checker) | **PASS with defects** | /pricing/rules table scrolls sideways at 1440; approval flow not exercised (write) |
| Booking | Regression (dashboard, cases, customers, calculator) | **PASS** | 0 console errors on 36 page loads |
| TripPlanner | Preview env (S237 fix) | **PASS with defects** | Data renders on preview; **Mapbox token refuses the preview host** (URL-restricted) → no base map on previews (D7) |
| TripPlanner | AA-812 WCAG AA contrast | **PASS** | 0 axe contrast violations on home/destination/tour (light + dark); /plan still has 7 (AA-674) |
| TripPlanner | AA-812 destination-photo fallback | **NOT VERIFIABLE** | 731 of 892 tours still show a placeholder; data depends on AA-708 |
| TripPlanner | AA-812 month filter in /plan List | **PASS with defects** | Filter works; burst 503s (D9) **fixed after the run** (pool max 1 + browse concurrency 15, 40 parallel uncached calls → 40 x 200); "1 DAYS" label (D12) |
| TripPlanner | Prod pages after #77/#78 | **PASS with defects** | Render + dark mode OK; content defects: Vietnam tour "14 days" with 12 day entries, duplicate Kuang Si places, "Ho Chi Minh Trail" as a point, repeated cover photos |
| TripPlanner | AA-712 6b default legacy | **NOT VERIFIABLE** in the browser | Default `legacy` confirmed by the code and the Dev parity run (`../aa712-6b/`), not by a response header |
| TripPlanner | S236 D1 tile storm | **PASS** (fixed) | |
| TripPlanner | S236 D2 "Customise this trip" | **NOT VERIFIABLE** | The final apply needs `POST /api/trip`; tours without planner places still 404 (D11) |

## Defects to track (new or confirmed)

- **D7 (Medium)** Mapbox token URL restriction blocks `*.vercel.app` previews: add the preview host pattern in the Mapbox
  account (Nghiệp).
- **D5 (Low, tenant-facing)** wrong Meta permission name on the Facebook card.
- Portal layout at 390: Ready-to-Publish card column ~90 px, filter row overflow on My Content, Recent Activity titles
  1–2 words per line, oval ROUTE pill; StickyBar overlaps the card above.
- Portal data: Ready to Publish lists 46 pieces with 3 unique titles for atlas-hearth (duplicate cards, S236 finding).
- Admin: Content Quality versions toolbar overflows 69 px at 390 (since AA-769); LABEL column off-screen at 1440 (needs
  horizontal scroll); the Label form shows "As-is" pre-selected on an unlabelled piece.
- Booking: /cases?source=cis empty-state copy; trip-plans KPIs fill the first viewport at 390.
- TripPlanner content: day-count mismatch, duplicate places, route-as-point, repeated photos (catalog data quality).

## Verifier quality notes (from the refute pass)

- Some evidence was mis-cited or duplicated (7 byte-identical screenshot pairs in `cis-admin/`); verdicts were
  downgraded where the cited screenshot did not show the claim.
- The tenant portal dark-mode claim was wrong in one admin-session capture (`portal-t7-planning-as-admin-1440-dark`).
