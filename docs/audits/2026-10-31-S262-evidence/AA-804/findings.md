---
id: OPS-08-s262-aa804-ui-verify
title: "AI providers admin page: live UI verification (S262)"
description: "Live screenshot pass of the AI providers page (5 tabs, trace drawer, old-link redirects) on the Production Vercel host with Dev data; results per page and 10 findings."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [cis]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-804, AA-1017]
---

# AA-804 — AI providers admin page, live UI verification (S262, 31/10/2026)

- Host: Production Vercel (Dev data). Frontend deployed: AA-CIS-App 7f6e3c2a (PR #1199); `main` head 18d0941c (#1201) has no `frontend/` change since, so production serves the newest frontend.
- Identity: Dev-only E2E CIS admin (aa-ui-verify §3a), read-only session, signed out afterwards.
- Method: navigate + screenshot only (no Save / Test / toggle / PATCH). Per page: 1440 light, 1440 dark, 390 light; console errors, failed requests, 4xx/5xx and sideways overflow recorded.

## Results per page

| # | Page | Console errors | 4xx/5xx | Overflow @390 | Real data | Verdict |
|---|---|---|---|---|---|---|
| 1 | Providers › Overview | 0 | 0 | none | month spend = sum of rows, 8 provider rows | PASS |
| 1b | Providers › Connections | 0 | 0 | none | 5 connections, health, budget | PASS |
| 1c | Providers › Jev credit | 0 | 0 | none | top-ups, spend, balance, ledger rows | PASS |
| 2 | Routing | 0 | 0 | none | availability, stage routes, Jev per stage | PASS |
| 3 | Models & trials | 0 | 0 | none | 14 models, 7 shadow rows | PASS (F3, F4) |
| 4 | Budgets | 0 | 0 | none | provider/job/connection caps; tenant tier = designed empty state | PASS (F5, F6) |
| 5 | Guide | 0 | 0 | none | 11 sections | PASS |
| 6 | Trace drawer (job t7_slate) | 0 | 0 | none | 10 calls, LLM 5 / Jev 5 | PASS with F2 |
| 7a–7c | settings?tab=models, settings?tab=jev-credit, cost-ops?tab=budgets | 0 | 0 | none | land on the new tab, one `tab` value | PASS |
| 7d | /admin/llm-usage → cost-ops?tab=llm | 0 | 0 | main scrolls sideways | redirect correct | redirect PASS, page F1 |

## Findings

| ID | Page / element | Severity | Finding |
|---|---|---|---|
| F1 | Cost Operations › LLM, account filter chips | Medium | At 390 px the chip row does not wrap; main scrolls sideways (747 vs 390). Pre-existing. |
| F2 | Trace drawer, calls table | Medium | At 1440 Cost / Latency / Tokens are hidden to the right with no scroll hint; table height-capped (rows 9–10 cut) while the drawer has empty space. 390 card layout is fine. |
| F3 | Models & trials tables | Low | Sideways scroll inside the card at 1440 with no hint ("Updated", "Repeat" cut); model names wrap over 3–4 lines. |
| F4 | Models & trials, Blocked badge + Source | Low | All-caps blocked reason with an internal session tag; Source shows internal file / migration names. |
| F5 | Budgets › Job caps | Low | Raw UUID as "Last changed"; "NO DAILY CAP" badge wraps into a round blob. |
| F6 | Budgets › connection budgets | Low | "no cap" rows still say "Stops at the cap · 80 %". |
| F7 | Tab strip at 390 | Low | No scroll hint; the active Budgets tab is not scrolled into view. |
| F8 | Providers vs Routing wording | Info | Circuit-open connection shows "Available" on Routing (any answered call in 24 h counts); "No recent calls" vs "Unknown" for the same row. |
| F9 | Trace drawer note | Info | "Calls a provider refused are not logged yet" is out of date since ledger v2 (#1200/#1201). |
| F10 | Jev credit subtitle | Info | Shows an internal table name. |

## Not covered

Write actions (not clicked; the E2E admin session is read-only), dark at 390, the VI locale, a DB match of the on-screen totals.

## Files

36 PNGs `NN-<page>-{1440-light,1440-dark,390-light}.png` (01–03 Providers, 04 Routing, 05 Models, 06 Budgets, 07 Guide, 08 Trace, 09–12 redirects). The admin UI shows AWS account IDs by design; none are transcribed here.

> Screenshots of this check are kept off the public repo because the admin AI providers pages show cloud account IDs. They are stored in Drive: `02 Báo cáo/S262-evidence-private/AA-804/` (rclone).
