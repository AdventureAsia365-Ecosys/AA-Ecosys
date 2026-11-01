---
id: OPS-08-s262-aa804-c4-ui-verify
title: "AI providers follow-ups (C4): live UI verification (S262)"
description: "Live check of CIS #1208 on the Production Vercel host with Dev data: the 10 earlier findings, the new views, and 4 new low findings."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [cis]
last_reviewed: 2026-11-01
review_every_days: 30
related: [AA-804, AA-1016, AA-1017, AA-1018]
---

# AI providers follow-ups (C4): live UI verification (S262, 01/11/2026)

Host: Production Vercel, CIS `cc034731` (#1208), Dev-only E2E CIS admin (read-only). 43 PNG (1440 light/dark, 390 light).

| Item | Result |
|---|---|
| Providers: access state, last probe, failure domain, warm-path labels | PASS |
| Re-queue refused jobs (dry-run dialog) | Partial: the dry run is a POST, the read-only E2E session gets 403, no dialog |
| Routing: failure-domain badge per stage; F7 tab strip at 390; F8 wording | PASS |
| Models & trials: F3 scroll hint; F4 plain reason/source; Experiments | PASS |
| Budgets: F5 names + one-line badge; F6 "no cap set"; tenant tier | PASS |
| Calls tab, refused rows, 7 days | PASS (11 rows, 0 USD) |
| Trace drawer Table at 1440 (F2) | PASS (all columns, all rows) |
| Cost Operations at 390 (F1) | PASS |
| Tenant 360 › Cost: AI budget tile + editor (Cancel) | PASS |
| S1 rewrite without the per-run model select | PASS |

Console / network: 0 errors except the expected 403 on the re-queue POST; no page-level sideways scroll at 390.

## New findings

| ID | Where | Severity | Finding |
|---|---|---|---|
| N1 | Cost Operations › AI & data spend at 390, group-by tree | Low | Row content 12–33 px wider than the card; right-hand cost cut. |
| N2 | AI providers › Calls at 1440 | Low | Table box height-capped at 9 rows with empty page below (F2 pattern). |
| N3 | Tenants detail tab strip at 390 (not kit Tabs) | Low | `?tab=cost` opens Cost but the tab is off-screen with no fade. |
| N4 | Providers / Budgets text | Info | Internal key in a failure domain of a disabled connection; raw error codes; actor shown as a raw login key. |

> Screenshots of this check are kept off the public repo because the admin AI providers pages show cloud account IDs. They are stored in Drive: `02 Báo cáo/S262-evidence-private/AA-804-c4/` (rclone).
