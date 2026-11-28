---
id: OPS-08-s297-ui-evidence
title: "S297 UI evidence: Compliance Calendar tab, USD-only billing (CIS admin, Booking staff admin, Partner CRM web)"
description: "Agent-run read-only Playwright evidence on the Dev hosts, 28/11/2026: the CIS Compliance readiness Calendar tab and the USD-only billing surfaces of CIS, Booking and the Partner CRM web (Content studio billing and dashboard, CRM home, one proposal); one VND leftover on the Booking Agency billing KPI tiles."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-28
review_every_days: 30
related: [AA-1184, AA-1191]
---

# S297 UI evidence (28/11/2026, about 15:50–16:05 +07)

Headless Chromium (Playwright 1.x from `tools/uat`), one browser at a time, after both deploys were live:
CIS API `/health/ready` git_sha `fb4d3077` (schema `498`), Booking API `/booking/health` git_sha `e609351d`.
Hosts: CIS admin `https://aa-cis.lumiguides.it.com`, Booking staff admin `https://booking.lumiguides.it.com`.
Item 4 (Partner CRM web) ran in a second lane once its deploy was live: see "Second lane" below.

Identities (by role; codes read at run time from the e2e mailbox by `tools/uat/lib/signin.cjs`, never written down;
no screenshot of the managed-login host): the Dev-only E2E CIS admin (read-only) and the E2E Booking admin
(`booking-admin`, read-only). After sign-in only GETs and page views were sent: the browser context aborted every other
method except the session refresh. The only request it aborted was the browser error-reporting beacon (one per page);
the matching `net::ERR_FAILED` console line is left out of the counts. No setting or data was changed; the plan drawer
was opened and closed without saving.

Each page was captured at 1440 px light and 390 px dark (the CIS Tenant 360 Billing tab at 1440 light only).
Console errors = `console.error` / uncaught page errors. Failing requests = responses >= 400 on the app origin.
Screenshots mask the account chip and replace every @-address, E2E user handle, 12-digit number and issue reference
in the page text (`[ref]`) before the shot. Raw records: `data/results.json` (ids -> `<uuid>`).

## Results

| Item | Issue | Check | Result | File |
|---|---|---|---|---|
| 1 | AA-1184 | Platform › Compliance readiness › Calendar tab (`?tab=calendar`) renders: check `ops_calendar_overdue` state **fail**, sealed, reason "2 overdue: OC-010, OC-999; 8 due soon" | **PASS** | `01-cis-compliance-calendar-1440-light.png`, `01-cis-compliance-calendar-390-dark.png` |
| 1 | AA-1184 | KPI tiles Overdue 2 / Due soon 8 / Open 5 / Lines 62; table "Needs attention" 15 rows | **PASS** | same |
| 1 | AA-1184 | OC-010 (secrets register rows, due 27/11) shows **overdue**, "1 day ago", "3 past due … of 94 dated rows" | **PASS** | same |
| 1 | AA-1184 | Drill line OC-999 visible (overdue, "Drill: a deliberately past-due test line") and the drill note under the check | **PASS** (observation: still listed, see O1) | same |
| 2 | AA-1191 | Tenants › Plans & add-ons list: prices in USD only, no VND column or input | **PASS** | `02a-cis-plans-1440-light.png`, `02a-cis-plans-390-dark.png` |
| 2 | AA-1191 | Plan drawer opened read-only (content.growth at 1440, content.starter at 390): USD price, USD extra seat, USD agreed price, no VND field, no currency picker | **PASS** | `02b-cis-plan-drawer-1440-light.png`, `02b-cis-plan-drawer-390-dark.png` |
| 2 | AA-1191 | Tenant 360 (synthetic agency) › Subscription: Billing details "Billing currency USD", quote in USD, no VND anywhere; Billing tab no VND | **PASS** (finding F2) | `02c-cis-tenant360-subscription-1440-light.png`, `02c-cis-tenant360-subscription-390-dark.png`, `02d-cis-tenant360-billing-1440-light.png` |
| 2 | AA-1191 | Platform › Settings, `cis.billing.enabled_currencies`: value in force `["USD"]`, default `["USD"]`, never changed | **PASS** (observation O2) | `02e-cis-settings-enabled-currencies-1440-light.png`, `02e-cis-settings-enabled-currencies-390-dark.png` |
| 3 | AA-1191 | Booking Settings › General: commercial defaults (quote validity, deposit) read-only, no currency shown, no VND | **PASS** | `03a-booking-settings-1440-light.png`, `03a-booking-settings-390-dark.png` |
| 3 | AA-1191 | Booking Agency billing › Settings › Payment terms: "Software fee currency" field hidden (API `enabled_currencies` = `["USD"]`) | **PASS** | `03b-booking-billing-terms-1440-light.png`, `03b-booking-billing-terms-390-dark.png` |
| 3 | AA-1191 | Agency billing › Invoices, kind Software fee: 8 SaaS invoices (7 drafts + 1 paid), every total in USD | **PASS** | `03c-booking-saas-invoices-1440-light.png`, `03c-booking-saas-invoices-390-dark.png` |
| 3 | AA-1191 | Agency billing page has no VND | **FAIL** (F1: the Open / Overdue / Waiting for approval tiles each show a "0 VND" line) | `03b-…`, `03c-…` (all four shots) |
| 4 | AA-1191 | Content studio › Account › Billing (Partner CRM web, E2E studio viewer): plan, monthly bill, usage and compare plans all in USD (`$`), no VND, no currency picker | **PASS** | `04a-crm-studio-billing-1440-light.png`, `04a-crm-studio-billing-390-dark.png` |
| 4 | AA-1191 | Content studio › Dashboard: membership and "This month" amount due in USD, no VND | **PASS** | `04b-crm-studio-dashboard-1440-light.png`, `04b-crm-studio-dashboard-390-dark.png` |
| 4 | AA-1191 | CRM › Home dashboard (synthetic agency owner): money tiles (Sold, Margin) in USD, no VND | **PASS** | `04c-crm-home-dashboard-1440-light.png`, `04c-crm-home-dashboard-390-dark.png` |
| 4 | AA-1191 | One proposal opened in the builder (working copy v1, nothing saved): every amount in USD, no currency select on the page, no VND | **PASS** | `04d-crm-proposal-1440-light.png`, `04d-crm-proposal-390-dark.png` |
| 4 | AA-1191 | The proposal's trip page: proposal and Money sections in USD, no currency select, no VND | **PASS** | `04e-crm-trip-proposals-1440-light.png`, `04e-crm-trip-proposals-390-dark.png` |
| all | — | Console errors 0 and failing requests 0 on all 27 shots (17 first lane + 10 second lane); no horizontal overflow at 390 (document and `main`) | **PASS** | `data/results.json` |

## Findings

- **F1 — VND still shown on the Booking Agency billing KPI tiles.** The tiles above the tabs list one line per currency
  from `GET /booking/agency-invoices/summary` (`by_currency`), which returns a `VND` bucket (1 draft, all amounts 0)
  because an old synthetic tour-settlement draft for October 2026 is in VND. The tiles read "0.00 USD / 0 VND" on every
  tab. The SaaS drafts themselves are all USD, so the USD-only rule for software fee drafts holds; the leak is the tile
  rendering (`AgencyBillingView.tsx` `perCurrency`, which does not filter by `enabled_currencies`) and the settlement
  draft row, which also shows VND in the Invoices list with "All kinds". Proposed fix: hide currencies that are not
  enabled from the tiles (or fold them into the USD view), and decide whether old VND settlement drafts are voided or
  shown with a "currency not enabled" note. Not fixed in this lane.
- **F2 — Issue references in page text (data, not code).** Tenant 360 › Subscription shows two issue references: an
  add-on request's agency note ("S269 live check (…)") and a plan feature description of `crm.ai_budget_usd_monthly`
  (it names a repo job, an issue reference and a migration number). Booking Agency billing › Settings shows one in the
  synthetic billing entity's legal name. They come from stored rows (the feature catalogue description is platform
  copy; the other two are test data). They are replaced with `[ref]` in the screenshots. Proposed fix: rewrite the
  feature description in plain words; the test rows can stay.

## Observations

- **O1** — The drill line OC-999 ("injected for one collector run") is still in the published calendar and counted in
  "2 overdue", so the check stays red for a reason that is not a real duty. Expected to drop on the next collector run
  once the drill line is removed from the calendar file; worth confirming tomorrow's run shows only OC-010.
- **O2** — The settings row shows "Allowed —" for this list setting, although its allowed values are USD and VND. Not
  wrong for USD-only, but the column does not show list choices.
- The CIS `Deploy Dev` run of the commit after `fb4d3077` (a CI-only change) ended in failure during this lane; the
  live API stayed on `fb4d3077`. The Booking `Deploy Dev` of the commit after `e609351d` also failed; the live API
  stayed on `e609351d`. Neither changes what was checked here.

## Not covered

- The CRM "new proposal" and AA prices currency pickers with VND enabled (the setting stays USD only; a read-only lane does not change it).
- Any write path (changing the enabled currencies, saving a plan, running drafts): read-only lane.

## Second lane (28/11/2026, about 16:05–16:20 +07): item 4, Partner CRM web

Host `https://portal.lumiguides.it.com` (CRM web and the Content studio, one host), CRM `/crm/health` and web
`/healthz` git_sha `1e49ce19` (the merge of the CRM USD-only pull request). Same browser rules, masks and counts as the
first lane.

Identities: the Content studio viewer of the E2E tenant (partner pool, password + authenticator read at run time) for
the studio pages, and the owner of the synthetic CRM agency (identity A of `tools/uat/lib/crm-signin.cjs`) for the CRM
pages. That CRM account can write; this lane sent only GETs (other methods aborted, the only one aborted was the
error-reporting beacon). Opening the proposal builder records one "view" audit event on the CRM side (a GET).

Results are in the table above (item 4 rows). Console errors 0 and failing requests 0 on all 10 shots; no horizontal
overflow at 390. Notes:

- The studio sidebar shows a grey bar where the "Account" group header is: the account-chip mask matched that header's
  name. It hides a nav label only; the Billing page itself is not masked.
- The proposal's booking terms code and the traveller handles are replaced with `•••` by the E2E-handle scrub.
- The CRM agency on this account has no VND proposal, so the check shows the USD-only display, not how a stored VND
  proposal is shown (the pull request starts a new version of such a proposal in USD; not exercised here).
