# CRM review: how the progress slide is computed

The opening progress slide of the CRM review video (`crm-rev-00.cjs`, step 2) shows one headline and eight tiles.
This file records how each number was computed, so the next update uses the same method.

- **Method:** the S261 method in `docs/audits/2026-10-31-S261-crm-progress-video-plan/README.md` §1–§2, unchanged.
- **Recomputed:** S262, 01/11/2026. Linear was read for all 53 design cards (read only), and AA-Partner `origin/main`
  at `eeccc98`.
- **Previous values:** the S261 values (31/10/2026) are kept below for comparison.

## Sources

| Source | What it gives |
|---|---|
| `docs/audits/2026-10-21-S246-crm-design-v3/design-v3.md` §6.3 | The 53 cards (CRM-01a … CRM-38, CRM-B*, CRM-P*) and each card's size (S, M or L) |
| `docs/audits/2026-10-21-S246-crm-design-v3/design-v3.md` §6.4 | Size scale S = 0.25, M = 0.5, L = 1 session; 37.25 sessions nominal, W8 (CRM-38) excluded |
| `docs/audits/2026-10-21-S246-crm-design-v3/linear-issue-map.json` | Card id to Linear issue |
| Linear project "Partner CRM — AA-Partner" (read 01/11/2026) | State of each card |
| AA-Partner `origin/main` (`eeccc98`), PRs #156–#169 | Code that is merged: CRM-13b (#156, #157), CRM-26 (#160), CRM-24b (#161), CRM-27 (#165–#169) |
| AA-Partner `api/app/reports/service.py` | Report metrics still "not built": only the AI one (M14) |
| `docs/backlog/tracker/plan.json` | Cross-check only. Its last commit is 31/10/2026 19:34, so it is older than Linear here; Linear wins |

## Rules (same as S261)

1. A card counts as built when its code is on `main`. A Done card counts in full. A card that is merged and live but
   not yet closed on Linear also counts as built (S261 counted five such cards).
2. A Backlog card counts 0 %, even when some scaffolding exists.
3. Module %: a Done card counts 100 %, unless part of its scope was split into a later issue or is not live. Then
   the missing part is taken off. For example, S261 scored M5 email at 90 % because Microsoft 365 send-as was split out.
4. Issues outside the 53 cards are not in the denominator. These are the split-outs AA-1011 and AA-1012 and the
   follow-up AA-1019. They only lower the module they belong to.

## What changed since S261

| Issue | Card | Linear (01/11) | Counted as |
|---|---|---|---|
| AA-954 Offline PWA | CRM-24b | Done 31/10 | Built |
| AA-956 Module 8 ops release | CRM-26 | Done 31/10 | Built. The staff screen is in AA-1019, which is not live |
| AA-971 AA support L2 + break-glass L3 | CRM-13b | Done 31/10 | Built. Same staff screen gap (AA-1019) |
| AA-964 AI gateway + drafts + guardrails | CRM-33a | Done 31/10 | Built, **test mode only**: no real model is switched on until the contract clause is settled |
| AA-952 Module 7 invoices and payments | CRM-23 | Done 31/10 | Built. Card payments (Stripe) are still not live |
| AA-957 Commission + cancel trip | CRM-27 | In Progress (merged, live 01/11) | Built (rule 1), 95 % in the module table because live polish is still open |
| AA-962, AA-961, AA-953, AA-966, AA-967, AA-945, AA-955 | various | Done | Already counted as built in S261. They are now closed, so the module scores move up |
| AA-1019 Staff console | outside the 53 | In Review, built, not live (Infra apply pending) | Not counted. It holds back M8, F1 and F4 by 5–10 points |

## Headline: about 80 % (S261: about 70 %)

| Measure | S262 | S261 | How |
|---|---|---|---|
| By cards | **81.1 %** (43/53) | 69.8 % (37/53) | 42 Done on Linear, plus AA-957 merged and live. Ten cards are still Backlog: CRM-20, 28, 29a, 29b, 32, 33b, 36, 37a, 37b and 38. On Linear alone it is 42/53 = 79.2 % |
| By effort | **82.5 %** (30.725 / 37.25 sessions) | 71.3 % | Sum of card sizes. AA-957 counts at 0.95 of M. With W8 Go-real (≈ 2.5 sessions) added to the total: 77.3 % |
| Average of 23 modules | **84.3 %** | ≈ 70 % | Module table below, F1–F5 and M1–M18 |
| Average of 29 entries (pessimistic) | 73.7 % | ≈ 61 % | 23 modules plus the 6 entries outside them |

The three main measures give 81–84 %. The slide rounds down to **about 80 %**, as S261 rounded 69.8–71.3 % to 70 %.

**Work left:** 6.5 nominal sessions on the 53 cards (37.25 − 30.725). With about 15 % for review and MFA waits,
that is about 7.5 sessions. W8 Go-real adds 2–3 sessions and waits on outside steps (Stripe live, vendor checks, DPA).

## Module table

| Module | S262 % | S261 % | Note |
|---|---|---|---|
| F1 identity vault | 95 | 69 | AA-971 Done. The staff screen for support and break-glass is not live (AA-1019) |
| F2 pseudonymous profile | 100 | 100 | — |
| F3 PII scrubber | 100 | 80 | The AI gateway (AA-964) uses the scrubber; its design rule is "scrubber failure, no call" |
| F4 tenancy and roles | 95 | 78 | Support access L2/L3 built; staff screen not live (AA-1019) |
| F5 audit | 100 | 85 | Audit lines for L2/L3 and for ops release views shipped with AA-971 and AA-956 |
| M1 intake | 100 | 100 | — |
| M2 pipeline | 100 | 100 | — |
| M3 interactive proposal | 83 | 83 | Builder map still not built (AA-948, Backlog) |
| M4 written proposal | 100 | 100 | — |
| M5 email | 90 | 90 | Microsoft 365 send-as split out (AA-1011) |
| M6 booking ledger | 100 | 100 | — |
| M7 invoices and payments | 90 | 90 | AA-952 Done, reminders live. Card payments (Stripe) still not live |
| M8 AA ops release | 90 | 0 | AA-956 Done, staff API live. Staff board not live (AA-1019) |
| M9 WhatsApp/SMS | 0 | 0 | Backlog (CRM-28) |
| M10 workflows and tasks | 0 | 0 | Backlog (CRM-29a, 29b) |
| M11 traveller portal | 100 | 76 | AA-953 and AA-954 Done; the itinerary works offline |
| M12 contracts and waivers | 95 | 95 | PAdES signed PDF split out (AA-1012) |
| M13 commission and trip cancel | 95 | 0 | AA-957 merged and live 01/11; Linear still In Progress for live polish |
| M14 AI | 50 | 5 | CRM-33a (L) Done in test mode only, with no real model switched on until the contract clause is settled. CRM-33b (L) Backlog. 1 of 2 L-sized cards |
| M15 suppliers | 100 | 100 | — |
| M16 agency reports | 95 | 90 | The M8 and M13 cells are live. Only the AI cell still says "Coming later"; no `metric_daily` rollup yet |
| M17 AA insights | 70 | 70 | CIS page S-03 and `insight_aggregate` still missing |
| M18 data export and erasure | 90 | 90 | Re-import, deferred erasure and requests routed by AA still missing |
| Onboarding and import (CRM-31) | 100 | 80 | AA-962 Done |
| Duty of care and calendar (CRM-30) | 100 | 95 | AA-961 Done. S261 only missed the incident banner live check; calendar OAuth was already split out (AA-1011) |
| Search and library (CRM-32) | 0 | 0 | Backlog |
| Campaigns (CRM-36) | 0 | 0 | Backlog |
| Hardening and release (CRM-37a, 37b) | 0 | 0 | Backlog |
| Go-real (CRM-38) | 0 | 0 | Backlog |

## Slide tiles

The slide keeps at most eight tiles. S261 had eight. The new ships need a place, so two S261 tiles are merged and one
is added. A range shows the lowest and highest module in the tile.

| Tile | Modules | S262 | S261 tile |
|---|---|---|---|
| Intake and pipeline | M1, M2 | 100% | 100% (same) |
| Proposals (interactive and written) | M3, M4 | 83-100% | 83-100% (same) |
| Bookings, suppliers and commissions | M6, M15, M13 | 95-100% | "Bookings and suppliers" 100%; M13 added |
| Invoices and payments | M7 | 90%, note "card payments not yet" | 90% (same) |
| Traveller portal | M11 | 100%, note "now works offline" | 76%, "offline use not yet" |
| Email, reports and data export | M5, M16, M18 | 90-95% | "Email and reports" 90% + "Data export and erasure" 90%, merged |
| Trip hand-over to Adventure Asia, support access | M8, F1, F4 | 90-95%, note "staff screen not live yet" | new tile |
| Workflows, WhatsApp/SMS, AI | M10, M9, M14 | 0-50%, note "AI in test mode only; the rest not started" | 0%, "not started or blocked" |

The modules F2, F3, F5, M12, M17, the duty-of-care card and the onboarding card are not on a tile. This is the same
as S261. They count in the averages above.

## Next update

Read Linear for the 53 cards. Apply rules 1–4, update the module table, then the tiles, title and both captions. The
closing slide `crm-rev-20.cjs` repeats the headline. Keep the two slides in step.
