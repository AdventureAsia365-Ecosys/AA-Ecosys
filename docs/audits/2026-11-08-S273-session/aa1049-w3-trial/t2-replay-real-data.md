# AA-1049 T2 replay (33 versions)

- flags: `{"T2_ORCHESTRATOR": "linear"}`, --opt-in: True
- status base -> branch: {'ai_generated': 32, 'needs_review': 1} -> {'ai_generated': 23, 'needs_review': 10}
- declared: 0
- undeclared: 0
- missing: 0
- MISS (a difference on a version with an outcome-moving cassette miss; re-record, never a pass): 20
- cassette hits base / branch: 48 / 49
- cassette misses base: {'t2_brand_audit': 18, 't2_flag_fix': 11, 't2_judge': 18, 't2_itinerary_nudge': 3}; branch: {'t2_judge': 18, 't2_flag_fix': 11}; judge misses (no stored verdict): 18

- MISS 12bfa06c-db9e-438f-a8a4-778dbf829a49 status,llm_stages: base {'t2_brand_audit': 1, 't2_flag_fix': 1}, branch {'t2_flag_fix': 1}
- MISS 2dc60f30-9f6d-4db5-974b-292e3f83b511 llm_stages: base {'t2_brand_audit': 1}, branch {}
- MISS 39d1e38c-d8c4-4bb6-accb-a6e38cdadbb3 status,quality_score,llm_stages: base {'t2_brand_audit': 1, 't2_flag_fix': 1}, branch {'t2_flag_fix': 1}
- MISS 4e86f1ea-aaef-4b5f-b202-b9c9d4276837 status,quality_score,llm_stages: base {'t2_brand_audit': 1, 't2_flag_fix': 1}, branch {'t2_flag_fix': 1}
- MISS 541874d9-d73a-446c-bf99-c03c18f91745 status,llm_stages: base {'t2_brand_audit': 1, 't2_flag_fix': 1}, branch {'t2_flag_fix': 1}
- MISS 588aa1f8-3fcb-487b-8f9e-c6773bf3a9da llm_stages: base {'t2_brand_audit': 1, 't2_itinerary_nudge': 1}, branch {}
- MISS 5b39474a-e06e-445d-a20a-87fbcf55cd9b quality_score,llm_stages: base {'t2_brand_audit': 1}, branch {}
- MISS 640a8eff-1729-4237-b203-f61084b48ea3 status,quality_score,llm_stages: base {'t2_brand_audit': 1, 't2_flag_fix': 1}, branch {'t2_flag_fix': 1}
- MISS 6ca1121a-548f-4758-a18c-85b54aee5328 status,quality_score,llm_stages: base {'t2_brand_audit': 1, 't2_flag_fix': 1}, branch {'t2_flag_fix': 1}
- MISS 75116f75-588b-49d8-acf8-78dd326cba35 status,quality_score,llm_stages: base {'t2_brand_audit': 1, 't2_flag_fix': 1}, branch {'t2_flag_fix': 1}
- MISS 88f2ef94-79c6-493e-b7f4-42a185e4be3e llm_stages: base {'t2_brand_audit': 1}, branch {}
- MISS 9122ca5f-0bc0-4792-b4fc-bf5a46c1730e status,llm_stages: base {'t2_brand_audit': 1, 't2_flag_fix': 1}, branch {'t2_flag_fix': 1}
- MISS aa452b6d-cd22-4238-b07b-eea742b29e8a llm_stages: base {'t2_brand_audit': 1, 't2_itinerary_nudge': 1}, branch {}
- MISS b25e4411-f939-41fd-9e8a-f857d600342b qa_repair_count,quality_score,llm_stages: base {'t2_brand_audit': 1}, branch {'t2_flag_fix': 2}
- MISS b716c7f6-105a-4b4b-960b-d8def3abf74d llm_stages: base {'t2_flag_fix': 1}, branch {}
- MISS be79395a-7d7e-4e80-8399-5b9428485ae0 llm_stages: base {'t2_flag_fix': 1}, branch {}
- MISS cbba9416-c308-40b0-8051-e1eddaf0b53c llm_stages: base {'t2_brand_audit': 1, 't2_itinerary_nudge': 1}, branch {}
- MISS d5a48151-db11-44b4-9312-b876164ceeb8 quality_score,llm_stages: base {'t2_brand_audit': 1}, branch {}
- MISS ee5fa669-c169-407a-8fb5-e84df69fd9b7 llm_stages: base {'t2_brand_audit': 1}, branch {}
- MISS f4185e7e-f95d-469e-81bb-cd2f123b01b2 status,llm_stages: base {'t2_brand_audit': 1, 't2_flag_fix': 1}, branch {'t2_flag_fix': 1}

Declared ids:
- D-t2-status: opt-in T2_ORCHESTRATOR=linear (L1): ai_generated -> needs_review when an enforce finding is left on the selected draft (T3 hard code, T3 grounding, a Master day-slot break) or a held fallback writer; never the other way
- D-t2-calls: opt-in linear (L2/L3/L4): at most 2 writer calls, one report-only judge call, no brand-audit flag_fix / itinerary nudge call
- D-t2-select: opt-in linear (L5): the selected draft / stored text, its score (never above main's for the same lineage) and the qa repair count differ
- D-t2-review: opt-in linear: the review row lists the enforce findings left (a day-slot code may be added)
- D-t2-contract: opt-in linear: the REPORT-mode final-contract verdict of the different stored text / status
