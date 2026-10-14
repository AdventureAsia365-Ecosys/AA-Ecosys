# AA-683 Booking staff admin: Vercel deployment UI verify (S236)

- **PR:** AdventureAsia365-Ecosys/AA-Booking#5, head `e91788cbc15723d30ec42c0066b40596f1b9534d` (`feat/aa-683-staff-admin-frontend`)
- **Deployment:** `dpl_67DsH8gaBKwVThGz6mKNkHmscy2j`, https://aa-booking-admin-gbq1xbbrv-pqnghiep1354-5974s-projects.vercel.app (Vercel Authentication on; reached with the project's existing automation-bypass header, scoped to the deployment origin only; protection left unchanged)
- **Backend:** real Dev Booking API through the BFF `/api/booking/*`; signed in as the CIS E2E admin `e2e-claude-code` (secret `aa-cis/dev/e2e-test-admin`)
- **Date:** 2026-10-14. **Agent:** Claude Code (sub-agent), Playwright/Chromium, profile kept in the session scratchpad
- **Scope:** read-only. The only POST calls were `/api/auth/login` and the stateless `/api/booking/pricing/quote-preview`. No versions created, nothing sent or approved, no status changes.

Matrix: 9 signed-in pages × {1440, 390} × {light, dark} = 36 captures, plus /login (light/dark × 1440/390, wrong password, empty fields) and a scrolled-to-bottom capture of every page at 390 (`*-390-light-bottom.jpg`). Raw data: `results.json`.

## Results

| Page | 1440 L/D | 390 L/D | BFF calls | Notes |
|---|---|---|---|---|
| /login | PASS | PASS | `POST /api/auth/login` 401 (wrong pw) → 200 | Wrong password shows "That username and password do not match a CIS staff account."; empty fields show "Enter your CIS username and password.". Pinned light in dark mode by design (`app/login/page.tsx`). |
| / (dashboard) | PASS | PASS | trip-cases, summary, staff, notifications: all 200 | TC-000001 in Recent trip cases |
| /cases | PASS | PASS | all 200 | TC-000001 listed (S235 E2E Test, Haa valley +3 legs, New inquiry, Unassigned) |
| /cases/TC-000001 | PASS | PASS | trip-cases/TC-000001, countries: 200 | Header, stepper, tabs, inquiry days, trip legs, people, trip details rendered |
| /customers | PASS | PASS | customers ×6, all 200 | 1 lead (S235 E2E Test) |
| /staff | PASS | PASS | staff 200 | 1 active admin |
| /settings | PASS | PASS | settings 200 | Profile fields read-only, link to CIS |
| /notifications | PASS | PASS | notifications 200 | 1 unread "New inquiry TC-000001" |
| /pricing/calculator | PASS | PASS | `POST quote-preview` 200 | 1000 USD net → subtotal 1,492.54 → **total 1,495.00 USD** (rule B2C target 30%, card fee 3%, round up to 5, effective margin 30.11%, floor 20%). Matches the API response. |
| /proposals | PASS | PASS | versions 200 | Empty state "No proposals match" (no versions on Dev yet) |

- Console errors on signed-in pages: **0**. Only console error in the run: the browser logging the expected 401 from the wrong-password attempt.
- Non-200 BFF responses: **0** (besides the intended 401).
- Horizontal overflow at 390: **none** (document `scrollWidth == 390` on every page; no unclipped element past the viewport). At 390 the last content clears the bottom nav (content bottom 760 px, nav top 784 px).
- The first dashboard load after sign-in logs a few `ERR_ABORTED` chunk/BFF requests: `router.replace` + `router.refresh` cancels in-flight requests; the same calls then complete 200. Benign.

## Defects / observations

| # | Severity | Page | Finding | Screenshot |
|---|---|---|---|---|
| 1 | Low | Dashboard | KPI "In progress **0**" sits over the subline "1 open · +1 vs last month", which reads as a contradiction (the open case is the new inquiry). | `dashboard-1440-dark.jpg` |
| 2 | Low | Pricing calculator | Summary says "Margin applied 30%" but the subtotal (1,492.54) also includes the 3% card fee; the fee only appears inside the collapsed "Rule, FX and lines". A "Card fee 3%" row in the summary would make the arithmetic readable. | `pricing-calculator-1440-light.jpg`, `pricing-calculator-1440-light-details.jpg` |
| 3 | Info | Vercel | This PR-branch deployment has `target: production` and holds the alias `aa-booking-admin.vercel.app` (the PR comment's "Preview" link), although the project's production branch is `main`. Check the project's git/production-branch setup before `main` deploys. | — |
| 4 | Info | Pricing calculator | Selling currency lists EUR/GBP/AUD/SGD while Dev has no FX rates; the on-page notice explains it. Non-USD was not exercised (USD only as briefed). | — |

No blocker or major defect found.

## Verdict

**Fit to merge** from a UI/integration standpoint: every page renders real Dev data through the BFF with no errors, at both widths and in both themes. Defects 1–2 can be follow-ups; item 3 is a Vercel project setting to check, not a code issue.
