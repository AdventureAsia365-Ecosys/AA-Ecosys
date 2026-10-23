---
id: PROD-01-aa645-writer-decision
title: "AA-645 S1 writer decision and rerun impact (S248)"
description: "Chọn writer W×Sonnet cho lần viết lại S1 (A/B gộp n=50, 2 lượt panel mù), đo brand-fit và tác động lên nền tảng."
type: report
status: active
owner: nghiep
audience: [engineer, cto, agent]
applies_to: [cis-core]
last_reviewed: 2026-10-23
review_every_days: 180
related: [AA-645]
---

# AA-645 — S1 writer decision and rerun impact (S248, 23/10/2026)

| File | What |
|---|---|
| [decision-memo.md](decision-memo.md) | A/B run 1: arms A+ Haiku vs W/E × Sonnet/Luna on 25 golden tours, panel + gates + cost |
| [pooled-n50.md](pooled-n50.md) | A/B run 1 + run 2 pooled (n = 50): W×Sonnet vs W×Luna by the pre-registered rule |
| [run2-score-summary.md](run2-score-summary.md) | Run 2 scorer output (per arm, A/A noise, pass agreement) |
| [brandfit-analysis.json](brandfit-analysis.json) | Offline measurement of the A1 brand-fit judge on the 125 run-1 pages ($0.25) |
| [platform-impact-memo.md](platform-impact-memo.md) | What a ~900-tour rerun touches (atoms, places, TripPlanner, tenants, SEO), cost, risks, run plan; §8 brand-fit result; §9 Nghiệp's decisions d01–d14 |

Decision: writer W×Sonnet; brand-fit report-only for A1 v2 until a source-bounded rubric is re-measured; pilot + ≤ 50
shadow first; step 0 prerequisites shipped in AA-CIS-App #963/#965 (AA-645, S248).
