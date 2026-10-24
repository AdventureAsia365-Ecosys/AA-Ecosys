---
id: PROD-01-aa783-agreement
title: "AA-783 agreement report: 40 labels vs the S234 T9 panel and gates"
description: Human-vs-panel and human-vs-gate agreement on the 40 pieces of the S234 label pack, computed in S248 with agree.py; labels AI-drafted and owner-approved.
type: reference
status: active
owner: nghiep
audience: [engineer, agent]
last_reviewed: 2026-10-24
related: [AA-783, AA-787, AA-791, AA-924]
---

# AA-783 agreement report (S248 run, committed S249)

**Label provenance:** the 40 labels were drafted by Claude (`labeller = claude-draft`, reasons prefixed `[Claude]`,
one batch write 2026-10-23T02:29:59Z) and approved by Nghiệp in S248. They are "AI-drafted, owner-approved", not an
independent human pass, so they are a weaker reference for calibrating an AI panel (S248 decision d17: no independent
human pass for now; the panel is only used to compare writers, never to decide publishing).

**Data:** export `aa783_export.py --set s234` (read-only; re-run S249 on Dev: 40 pieces, 26 approved / 14 held, no
label stored in `content_piece_label`), labels in the S248 label-desk artifact (`labels/<piece_id>`, db-backed; that
artifact belongs to the claude.ai account used in S248 and is not readable from the S249 account, so the full
per-piece `labels.json` is not reproduced here). Tool: `agree.py report` (this folder), seed 783, 2,000 bootstrap
resamples. The tables below are the report the S248 run printed; the gate sections are summarised from the same run
(Linear AA-783 comment of 23/10/2026).

Labelled 40 of 40. Thresholds: stand-in kappa 0.6, light bar 0.6.

## Light share

| Slice | n | Human as-is | Human light+ | Panel light+ | Gate approved |
|---|---|---|---|---|---|
| all | 40 | 0.025 | 0.7 | 0.55 | 0.65 |
| blog | 16 | 0.0 | 0.375 | 0.125 | 0.5 |
| linkedin | 24 | 0.042 | 0.917 | 0.833 | 0.75 |
| atlas-hearth/blog | 8 | 0.0 | 0.5 | 0.125 | 0.5 |
| atlas-hearth/linkedin | 6 | 0.0 | 0.833 | 1.0 | 0.5 |
| terra-family/blog | 8 | 0.0 | 0.25 | 0.125 | 0.5 |
| terra-family/linkedin | 6 | 0.0 | 1.0 | 0.833 | 0.667 |
| trail-pulse/linkedin | 6 | 0.0 | 0.833 | 0.5 | 1.0 |
| wildkind-travel/linkedin | 6 | 0.167 | 1.0 | 1.0 | 0.833 |

Panel minus human light share: -0.15; a panel bar of 0.45 matches a human bar of 0.6.

## Verdict agreement (human vs panel)

| Against | n | Exact | kappa (CI) | Quadratic kappa (CI) | Binary kappa (CI) | Panel stricter / more lenient |
|---|---|---|---|---|---|---|
| panel majority | 40 | 0.7 | 0.401 [0.135, 0.652] | 0.49 [0.24, 0.689] | 0.479 [0.205, 0.725] | 10 / 2 |
| editor | 40 | 0.7 | 0.425 [0.19, 0.659] | 0.465 [0.244, 0.682] | 0.461 [0.225, 0.7] | 11 / 1 |
| brand_lead | 40 | 0.775 | 0.524 [0.257, 0.767] | 0.595 [0.35, 0.786] | 0.611 [0.329, 0.842] | 7 / 2 |
| channel | 40 | 0.725 | 0.456 [0.204, 0.693] | 0.565 [0.35, 0.736] | 0.611 [0.333, 0.843] | 7 / 4 |
| client | 40 | 0.75 | 0.441 [0.135, 0.7] | 0.469 [0.179, 0.714] | 0.477 [0.167, 0.744] | 6 / 4 |


Panel-internal Fleiss kappa: 0.537 (verdict), 0.601 (binary). **The panel cannot stand in for the human verdict**
(stand-in needs quadratic and binary kappa ≥ 0.60 against the panel majority; got 0.49 and 0.479).

## Gate approve/hold vs the labels

"Should approve" = light or better. Gate: precision 0.808, recall 0.75, accuracy 0.70, kappa 0.318
(TP 21, FP 5, FN 7, TN 7).

## Gates worth a look (final ledger and any attempt)

| Gate | Fires | Precision | Recall | Note |
|---|---|---|---|---|
| F8_framework | final on 25/40 | 0.69 | – | fires on 17 pieces labelled light or better: over-strict, mostly blogs |
| F9_cta_fact | ever 29 | 0.83 | 0.80 | works |
| promises_an_option | 16 | 1.00 | – | precise |
| F12_scope | – | – | 0.30 | misses most scope defects |

## Decisions recorded (Done-when: "thresholds/gate decisions updated with the human numbers")

1. **No panel threshold change.** The labels are AI-drafted (d17 "skip"), the panel stays a relative writer
   comparison (AA-645 uses it that way), and no gate is promoted or demoted from these numbers alone. If the panel ever
   decides publishing, an independent human pass (10–40 pieces, Nghiệp or Ms. Thư, no AI draft) comes first, with the
   label desk pattern in the S248 calibration-loop memo (`docs/audits/2026-10-23-S248-calibration-loop/memo.md`, C2).
2. **Panel bar:** a panel light-or-better bar of **0.45** matches the human 0.60 bar on this set (panel stricter by
   0.15, blog much stricter than LinkedIn). Use 0.45 when reading old S233/S234 panel shares.
3. **F8_framework over-strict on blogs → input to AA-924** (severity per violation, F15/F2 merge, lexicon gate) and
   AA-787 (gate drop/merge), not changed here (no new gates / gate changes during the S1-first freeze).
4. **F12_scope recall 0.30 → input to AA-788** (promote F12 after AA-924): promotion would block little until recall
   improves.

The issue closes on this report (S249). Follow-ups live in AA-924, AA-787, AA-788 and the calibration-loop memo.
