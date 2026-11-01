---
id: OPS-08-s262-aa804-n1n4-ui-verify
title: "AI providers polish N1-N4: live UI verification (S262)"
description: "Live check of CIS #1211 on the Production Vercel host with Dev data: cost tree at 390, Calls table uncapped, kit tabs on Tenants, plain words for codes and actors."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [cis]
last_reviewed: 2026-11-01
review_every_days: 30
related: [AA-804]
---

# AI providers polish N1-N4: live UI verification (S262, 01/11/2026)

- **Host:** the Production Vercel deployment of the CIS admin, on CIS `67668f85` (#1211). The Vercel Deploy run for that SHA finished green.
- **Session:** the Dev-only E2E CIS admin (read-only), using the saved storage state of the UAT dry-run harness (`tools/uat/lib/signin.cjs`).
- **Browser:** headless Chromium; the theme was set through `cis_theme` + `colorScheme`.
- **Screenshots:** 18 PNG files. For the files named `*-full.png`, the viewport was grown to the height of the scrolling `<main>`.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | N1: Cost Operations › AI & data spend, group-by tree at 390 light | PASS | Both groupings (26 and 35 costs, first sub node opened): 0 costs cut, every card scrollWidth == clientWidth (356/356), page 390/390. |
| 2 | N2 + N4: Calls, 7 days, refused, 1440 light | PASS | 13 rows, all in the table; no height-capped scroll box (only `<main>` scrolls). The Outcome column reads "stopped by a spending cap", "other error", "access denied", "key or sign-in problem"; no raw code. |
| 3 | N3: Tenants `?tenant=<id>&tab=cost` at 390 light | PASS | Kit underline tabs: Cost selected (2px underline), inside the strip and the viewport, gradient edge fade present, page 390/390. |
| 4 | N4: Providers at 1440 light | PASS | The "last error" lines read words; failure domains carry no connection key. "Re-queue refused jobs" gives the expected POST 403 and a muted "This is a read-only session: …" line; no `e2e_read_only`, no red alert. |
| 5 | N4: Budgets "Last changed" at 1440 light | PASS | The DataForSEO cap reads a staff name; the rest read "Migration NNN" / "Break-glass"; no `name:ref` string on the page. |
| 6 | Console errors | PASS | 0 console and page errors on every page, apart from the expected 403 on `POST /api/admin/job-runner/jobs/retry-llm-denied`. No other HTTP 4xx/5xx. |

Dark at 1440: Calls and Providers render correctly, with the same counts and wording as light.

## Notes (no new defect)

| ID | Where | Severity | Note |
|---|---|---|---|
| I1 | Providers › LLM connections | Info | A connection with no account ID still shows its key as the mono line under its label (by design); the failure-domain line uses the label. |
| I2 | Providers › failure domain | Info | The assume-role LLM account's domain shows its account ID; the main account's shows its name. Allowed, but the two rows read differently. |
| I3 | Budgets › Job caps | Info | One "Last changed" value is an old free-text test tag, not a `user:sub` value; old data. |
| I4 | Calls at 1440 | Info | The Outcome column is narrow; "stopped by a spending cap" wraps over four lines. Cosmetic. |

> Screenshots of this check are kept off the public repo because the admin AI providers pages show cloud account IDs. They are stored in Drive: `02 Báo cáo/S262-evidence-private/AA-804-n1n4/` (rclone).
