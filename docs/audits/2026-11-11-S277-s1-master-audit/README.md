# S1 Master audit (S277)

## Before and after (S277, 11/11/2026)

The same read-only audit ran twice on Dev: before the S277 rewrites (07:08 +07, after the 3-tour pilot) and after
them (14:00 +07). The tables below are the "after" run; this block compares the two.

| | Before | After |
|---|---|---|
| Active Masters | 892 | 844 (48 elephant-riding Masters held off sale for review) |
| Written by an older model (pre writer v2) | 72 | 0 |
| Contract verdict `publish` | 832 | 835 |
| `policy_hold` (elephant riding) still on sale | 46 | 0 |
| `source_hold` | 8 | 7 |
| `review` | 6 | 2 |
| Masters whose fixed fields would change if recomposed today | 735 | 708 |

What happened in between: 36 pre-v2 Masters were rewritten with writer v2 and the S1 train (waves `4ff41973`,
`9bf05a79`, and the batch-lane pilot `7bad0b8c`, which also rewrote one v2 Master; about 2.4 USD measured in the ledger), and the 48 Masters that offer elephant
riding were held off sale with a pending policy review each (CIS 398 + #1439, tech lead decision).

Generated 2026-11-11T07:00:38+00:00 by `apps/AA-CIS-App/scripts/quality/audit_s1_masters.py` (schema `aa1049-s1-master-audit/2`, contract `fc-w1-report-1`), read-only, no model call.
Every active Master of the AA master tenant, judged on its published version and its raw source with the code that is on CIS main today. Public-repo rules applied: ids, codes and counts only, no page or source text, no brand words; tours are named by the first 8 hex characters of their id (the full per-Master lines stay in the gitignored .tmp-session).

## How many Masters

- Active Masters (master tenant): **844**; other tenants: 0.
- Audited: **844** = S1 writer v2 **844** + older writers **0**.
- Brand rule: active True, 43 forbidden words.

### Writer of the published version

| writer | all | v2 | older |
|---|---:|---:|---:|
| `v2` | 844 | 844 | 0 |

## What happened to the other tours

The master tenant has **987** source rows (`raw_tours`, every version and state).

### Source state (deleted, or source status / lifecycle stage)

| state | tours |
|---|---:|
| `active/active` | 917 |
| `deleted` | 44 |
| `superseded/active` | 26 |

### Master state (master status / deleted / reason; none = never published)

| state | tours |
|---|---:|
| `active` | 844 |
| `none` | 95 |
| `inactive/policy_hold` | 48 |

### Live sources without an active Master: 73

### Their pipeline status

| pipeline_status | tours |
|---|---:|
| `published` | 48 |
| `ingested` | 25 |

### Their latest version status

| status | tours |
|---|---:|
| `approved` | 46 |
| `hitl` | 27 |

| tour_id | pipeline | lifecycle | master | reason | latest version |
|---|---|---|---|---|---|
| `0a832593` | ingested | active | none |  | hitl |
| `0ae89a30` | published | active | inactive | policy_hold | hitl |
| `0b887ba3` | published | active | inactive | policy_hold | approved |
| `117d2345` | ingested | active | none |  | hitl |
| `154b9f6c` | published | active | inactive | policy_hold | approved |
| `16350d17` | published | active | inactive | policy_hold | approved |
| `176c8edd` | ingested | active | none |  | hitl |
| `19fbcd6f` | published | active | inactive | policy_hold | approved |
| `1a0de887` | published | active | inactive | policy_hold | approved |
| `1e9a62fc` | published | active | inactive | policy_hold | approved |
| `1fdb0736` | published | active | inactive | policy_hold | approved |
| `23078315` | published | active | inactive | policy_hold | approved |
| `2361320e` | ingested | active | none |  | hitl |
| `282df69a` | ingested | active | none |  | hitl |
| `2c063258` | published | active | inactive | policy_hold | approved |
| `2f20cacd` | published | active | inactive | policy_hold | approved |
| `313ce808` | ingested | active | none |  | hitl |
| `3aea8bdc` | published | active | inactive | policy_hold | approved |
| `42564a4c` | ingested | active | none |  | hitl |
| `44e9daef` | ingested | active | none |  | hitl |
| `47b39b8a` | published | active | inactive | policy_hold | approved |
| `4b05dc29` | published | active | inactive | policy_hold | approved |
| `4d841fa9` | published | active | inactive | policy_hold | approved |
| `50566aaf` | published | active | inactive | policy_hold | approved |
| `527eb151` | published | active | inactive | policy_hold | approved |
| `5547aef2` | published | active | inactive | policy_hold | approved |
| `56b10bb6` | ingested | active | none |  | hitl |
| `5bafc8b2` | published | active | inactive | policy_hold | approved |
| `5f342e9a` | published | active | inactive | policy_hold | approved |
| `60fc0e46` | published | active | inactive | policy_hold | approved |
| `61ea0e8c` | published | active | inactive | policy_hold | approved |
| `6209622d` | published | active | inactive | policy_hold | approved |
| `687b7440` | published | active | inactive | policy_hold | approved |
| `6a5ecf78` | ingested | active | none |  | hitl |
| `71cacbb0` | ingested | active | none |  | hitl |
| `741542df` | published | active | inactive | policy_hold | approved |
| `86f4dc83` | ingested | active | none |  | hitl |
| `909e5f93` | ingested | active | none |  | hitl |
| `9183cc8a` | published | active | inactive | policy_hold | approved |
| `9202cc6b` | published | active | inactive | policy_hold | approved |
| `93b96525` | published | active | inactive | policy_hold | approved |
| `a1058b99` | published | active | inactive | policy_hold | approved |
| `a234faad` | published | active | inactive | policy_hold | approved |
| `a25ec5e8` | published | active | inactive | policy_hold | approved |
| `a2d48b0c` | published | active | inactive | policy_hold | hitl |
| `a31d9fad` | published | active | inactive | policy_hold | approved |
| `a6f6512e` | ingested | active | none |  | hitl |
| `a8e6904d` | published | active | inactive | policy_hold | approved |
| `abfb4275` | ingested | active | none |  | hitl |
| `ae082c7c` | published | active | inactive | policy_hold | approved |
| `af1b605c` | published | active | inactive | policy_hold | approved |
| `b0e5fb21` | published | active | inactive | policy_hold | approved |
| `b5273e8f` | ingested | active | none |  | hitl |
| `b7a6e4aa` | ingested | active | none |  | hitl |
| `b82908bf` | published | active | inactive | policy_hold | approved |
| `bc2cc994` | published | active | inactive | policy_hold | approved |
| `c165c88e` | ingested | active | none |  | hitl |
| `c2ca8967` | published | active | inactive | policy_hold | approved |
| `c69543e5` | published | active | inactive | policy_hold | approved |
| `c87812bd` | ingested | active | none |  | hitl |
| `d0468bcd` | ingested | active | none |  | hitl |
| `d1426c7b` | published | active | inactive | policy_hold | approved |
| `d3dbee4f` | published | active | inactive | policy_hold | approved |
| `d4897d02` | published | active | inactive | policy_hold | approved |
| `d8e02692` | ingested | active | none |  | hitl |
| `da3ca995` | ingested | active | none |  | hitl |
| `dfdb4017` | published | active | inactive | policy_hold | approved |
| `e2dfece0` | ingested | active | none |  | hitl |
| `e9003118` | published | active | inactive | policy_hold | approved |
| `f46b0297` | ingested | active | none |  | hitl |
| `f51616dd` | ingested | active | none |  | hitl |
| `fca0fedd` | published | active | inactive | policy_hold | approved |
| `ff98f9f4` | published | active | inactive | policy_hold | approved |

## Final contract verdict (recomputed today, brand words included)

Computed twice per Master. **Today** (the headline, and the not-publish list below): the hard codes come from today's validate run on the stored text, the input the live S1 exit gives the contract. **Stored codes**: the hard codes stored with the version when it was written (`quality_scores.failure_codes`). They differ when a rule changed since, or a stored code is stale.

### Verdict today

| verdict | all | v2 | older |
|---|---:|---:|---:|
| `publish` | 835 | 835 | 0 |
| `source_hold` | 7 | 7 | 0 |
| `review` | 2 | 2 | 0 |

### Verdict on the stored codes

| verdict | all | v2 | older |
|---|---:|---:|---:|
| `publish` | 835 | 835 | 0 |
| `source_hold` | 7 | 7 | 0 |
| `review` | 2 | 2 | 0 |

### Masters where the two differ (stored codes -> today)

none

### Basis of the headline verdict (stored_codes = today's validate could not run)

| basis | all | v2 | older |
|---|---:|---:|---:|
| `today_validate` | 844 | 844 | 0 |

### Stored verdict -> today

none

### Blocking findings (Masters per code)

| code | all | v2 | older |
|---|---:|---:|---:|
| `SOURCE_DAY_CONTRADICTION` | 7 | 7 | 0 |
| `DAY_COUNT_VS_DURATION` | 2 | 2 | 0 |

### Warnings (Masters per code)

| code | all | v2 | older |
|---|---:|---:|---:|
| `DAY_CHECK_SKIPPED` | 21 | 21 | 0 |
| `DAY_DEPARTURE_MIDTRIP` | 11 | 11 | 0 |

## S1 writing rules on the stored text (deterministic, today's code)

### validate codes

| code | all | v2 | older |
|---|---:|---:|---:|
| `HIGHLIGHTS_TOO_GENERIC` | 8 | 8 | 0 |
| `HIGHLIGHTS_TOO_FEW` | 1 | 1 | 0 |

### validate codes not in the stored failure codes (new since the version was written)

none

### Brand pre-audit codes

| code | all | v2 | older |
|---|---:|---:|---:|
| `ITINERARY_MEAL_TIME_INVENTED` | 357 | 357 | 0 |
| `HIGHLIGHTS_OPTIONAL_LANGUAGE` | 31 | 31 | 0 |

### Pre-audit codes that need Jev to confirm (not run)

| code | all | v2 | older |
|---|---:|---:|---:|
| `ITINERARY_MEAL_TIME_INVENTED` | 72 | 72 | 0 |

### S1 code checks (Masters per code)

| code | all | v2 | older |
|---|---:|---:|---:|
| `NAME_NOT_IN_SOURCE` | 97 | 97 | 0 |
| `DAY_PLACE_MISMATCH` | 39 | 39 | 0 |
| `NUMBER_NOUN_MISMATCH` | 22 | 22 | 0 |
| `DAY_DEPARTURE_MIDTRIP` | 11 | 11 | 0 |
| `META_CUT` | 8 | 8 | 0 |
| `NUMBER_NOT_IN_SOURCE` | 8 | 8 | 0 |
| `INCLUSION_CONTRADICTED` | 7 | 7 | 0 |
| `SOURCE_DAY_CONTRADICTION` | 7 | 7 | 0 |
| `DAY_COUNT_VS_DURATION` | 2 | 2 | 0 |

### Numeric grounding (sentences with a figure the source lacks)

| count | all | v2 | older |
|---|---:|---:|---:|
| `sentences` | 5 | 5 | 0 |
| `masters` | 4 | 4 | 0 |

### Forbidden words, brand list (Masters per field)

none

### Forbidden words, AA core list (Masters per field)

none

## S1 train compose diff (what code composition would change today)

Fields counted per Master that would differ: `day_headings`, `fact_lines` (verbatim meals / overnight lines), `day_prose`, `day_count`, `seo_title` (word-boundary fit), `seo_meta` (code template). `slug` is not applicable on S1 (no slug column). The train composes v2 pages only; older versions are measured for comparison.

### Masters with any composed field changed

| count | all | v2 | older |
|---|---:|---:|---:|
| `masters` | 708 | 708 | 0 |

### Masters per changed field

| field | all | v2 | older |
|---|---:|---:|---:|
| `day_prose` | 444 | 444 | 0 |
| `fact_lines` | 417 | 417 | 0 |
| `seo_meta` | 7 | 7 | 0 |

## Not run (need a model) and errors

- `jev_grounding`: Jev sentence grounding of the stored text (the contract reads the stored grounding instead)
- `jev_meal_claims`: Jev on a meal / clock claim the source day does not back (the code is listed as needs_model)
- `llm_brand_audit`: the LLM brand audit (the deterministic pre-audit runs; the stored audit status is read)
- `s1_judge`: the S1 judge score (the stored score is read)

### Not run (Masters)

| check | all | v2 | older |
|---|---:|---:|---:|
| `jev_grounding` | 844 | 844 | 0 |
| `llm_brand_audit` | 844 | 844 | 0 |
| `s1_judge` | 844 | 844 | 0 |
| `jev_meal_claims` | 72 | 72 | 0 |

### Section errors (Masters)

none

### Source state of the active Masters

| state | all | v2 | older |
|---|---:|---:|---:|
| `active/active` | 844 | 844 | 0 |

## Masters whose verdict today differs from the stored-codes verdict: 0

## Masters whose verdict today is not publish: 9

| tour_id | writer | verdict today | on stored codes | blocking codes today |
|---|---|---|---|---|
| `2b3a540f` | v2 | review | review | DAY_COUNT_VS_DURATION |
| `5a79ee69` | v2 | review | review | DAY_COUNT_VS_DURATION |
| `256f07bd` | v2 | source_hold | source_hold | SOURCE_DAY_CONTRADICTION |
| `3fa33633` | v2 | source_hold | source_hold | SOURCE_DAY_CONTRADICTION |
| `54137f3f` | v2 | source_hold | source_hold | SOURCE_DAY_CONTRADICTION |
| `69f731ca` | v2 | source_hold | source_hold | SOURCE_DAY_CONTRADICTION |
| `7aaa375d` | v2 | source_hold | source_hold | SOURCE_DAY_CONTRADICTION |
| `83e3b208` | v2 | source_hold | source_hold | SOURCE_DAY_CONTRADICTION |
| `c8905ad0` | v2 | source_hold | source_hold | SOURCE_DAY_CONTRADICTION |
