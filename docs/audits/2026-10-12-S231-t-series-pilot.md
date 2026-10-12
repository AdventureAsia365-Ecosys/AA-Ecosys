# S231 — T-series pilot (G3) + G1/G2 — AA-741

Date: 12/10/2026 · Agent: Claude Code · Env: Dev (acc2) · Plan: `docs/architecture/t-series-audit-and-plan.md` §7

## Scope
- **G1** tenant_id on every LLM call — shipped first so the pilot's cost numbers are real.
- **G2** `segment_research` DE/FR/NL, scoped to the 3 pilot tours (73 places).
- **G3** pilot: 3 Master tours × 4 brand tenants (T2), then one slate → angle → write per tenant
  for blog and LinkedIn (the social channel the slate offered).

Pilot tours (chosen for best existing US/UK research coverage, three countries):

| tour | published_tour_id | places |
|---|---|---|
| Culinary Gems of Bhutan | `84e392c3` | 25 |
| Khövsgöl & Gobi (Mongolia) | `caf4bf16` | 24 |
| Laos→Vietnam by bicycle | `2cf487be` | 24 |

## Results

### G1 — verified live
- 12 T2 jobs: **359/359** `llm_call_log` rows carry the tenant (before: s1_judge 3/8,393).
- 5 T9 jobs: every row (t9_write, t10_gates, t10_judge, f10_embed) carries the tenant.
- Gap found and fixed: shadow-model rows (10% judge shadow) ran on a plain thread → no job_id /
  tenant (29 rows in the pilot). PR #663. HTTP-path rows (T7/T8) still rely on explicit
  tenant_id until G5 (AA-764).

### G2 — DE/FR/NL research
- Places researched DE/FR/NL: 26 → **99** each; `search_demand` keywords 96 → **263** each.
- Cost **$0.70** (estimate was $1.07 DFS + $0.10 LLM). Job 402 s.

### T2 (tenant rewrite of Master) — 12 runs
| tenant | market | scores (Bhutan / Mongolia / Laos-VN) |
|---|---|---|
| atlas-hearth | US | 5 / 6 / 4 |
| terra-family | UK | 7 / 7 / 7 |
| trail-pulse | US | 4 / 3 / 5 |
| wildkind-travel | US | 5 / 7 / 7 |

- 5/12 reach 7 (`ai_generated`), 7/12 `needs_review`. All `brand_loaded=true`.
- **All 12 `seo_source = admin_us_fallback`** — the tenant-market keywords were never used (see
  finding 1). Fixed in PR #664.
- Cost **$4.59 total ≈ $0.38/tour**; `t2_generate` = 95% ($4.34, ~7 generate calls per tour).
  Job time avg 281 s.

### T7 / T8 / T9 (slate → angle → write)
| step | where it runs | latency | cost |
|---|---|---|---|
| T7 slate (propose + Debate) | HTTP `GET /v1/slate` | **2 min 48 s – 4 min+ → 504 at the gateway (all 4 tenants)** | ~$0.02/tenant |
| T8 angles | HTTP `POST …/goal` | **15–19 s** | ~$0.02/request |
| T9 write + T10 gates | job | 38–106 s | blog ~$0.12, LinkedIn ~$0.037 per final piece (incl. 1 repair attempt) |

- Per piece incl. T8: **blog ≈ $0.14, LinkedIn ≈ $0.057.**
- **5/5 final pieces held** — none publishable:
  - F1_grounding — the writer invents numbers absent from the seed ("900-metre drop",
    "3,120 metres", "since the 1970s", Laos e-visa fee/processing days).
  - F9_cta_fact — audit `manual_check`.
- Debate flagged **49–54 of 60** candidates per tenant (safety rail caps cuts at 30).
- Jev on T-series: t3_grounding 92/93 grey, t7_debate 222/222 grey (uncalibrated shadow — as
  expected before AA-696/699 calibration).

### Pilot spend
G2 $0.70 + T2 $4.59 + T7 ~$0.08 + T8 ~$0.10 + T9 ~$0.33 ≈ **$5.8**.

## Findings → action
| # | finding | action |
|---|---|---|
| 1 | T2 market keywords matched on title words only ("CULINARY GEMS OF BHUTAN" → `culinary`) → 0 matches, US fallback for every tenant | **Fixed PR #664**: match on the tour's atom places too. Verified live: terra-family × Bhutan → `seo_source = tenant_market` (UK), score 7, $0.31 |
| 2 | Intermittent ALB 502 (uvicorn keep-alive 5 s < ALB idle 100 s); 39 on 07/10 | **Fixed PR #662** |
| 3 | Shadow LLM rows lost job_id + tenant | **Fixed PR #663** |
| 4 | Integration DB lacked role `aa_app_user` → migration 203 (`v_active_tour_atoms`) never applied in tests | **Fixed PR #664** (conftest) |
| 5 | `GET /v1/slate` re-runs propose + Debate on every page load: 3–4 min, 504, paid each time | AA-764 (G5): move to a job; GET must only read |
| 6 | T9: 100% held — writer invents numeric facts; F9 manual_check | Writer source-fidelity rule for T9 (same A/B policy as S1) — next session |
| 7 | Debate flags 82–90% of candidates | Calibrate with AA-696/699 before the full run |
| 8 | T2 quality: 5/12 reach 7; ~7 generate calls/tour drive cost | Analyse in G7 with tenant-market keywords on (after #664) |

Linear: the workspace hit the free-plan issue limit in S231 — findings 2–4 and 6 are tracked
on AA-741 instead of their own issues.

## Scripts
`.tmp-session/s231/` (gitignored): `s231_pilot.py` (tenant API runner), `s231_measure.py`,
`s231_t9.py`, `s231_slate.py`, `s231_mktseo*.py` (market-SEO diagnosis), `pilot.json` (raw).
