# F9 v2 replay — 2026-10-13 07:26:10

Mode: PAID. Stage `adhoc_aa768_f9v2`. Cost cap $0.60; charged $0.4017 over 172 calls.

DB enrichment: {'set_a_claims_moved_to_discarded_attempts': 73, 'set_b_grounding_from_writer_input': 20, 'pieces_read': 42}

## Set A (127 S232 labelled claims)

| arm | run | real_kept | hard subset | over_strict_cleared | borderline failed | hypothetical failed |
|---|---|---|---|---|---|---|
| DET | 1 | 17/48 [0.234, 0.496] | 8/10 | 40/46 [0.743, 0.939] | 6/33 | 2/5 |
| CUR | 1 | 31/48 [0.504, 0.766] | 7/10 | 25/46 [0.402, 0.678] | 24/33 | 4/5 |
| CUR | 2 | 37/48 [0.635, 0.867] | 10/10 | 26/46 [0.422, 0.698] | 21/33 | 3/5 |
| V2a | 1 | 34/48 [0.568, 0.818] | 8/10 | 33/46 [0.575, 0.827] | 15/33 | 3/5 |
| V2a | 2 | 36/48 [0.612, 0.851] | 9/10 | 33/46 [0.575, 0.827] | 17/33 | 4/5 |

Targets (V2a): real_kept ≥90% with 10/10 trip_promise+location+number; over_strict_cleared ≥90%; 0 exempt-typed leaks; piece test-retest ≥85%.

- V2a leaks (real violation typed exempt and passed): {'place_background': 12, 'opinion': 7}
- Test-retest piece agreement: CUR 35/38, V2a 38/38
- Held texts by run: CUR {'1': 35, '2': 38}, V2a {'1': 38, '2': 38}
- False holds: {'CUR': {'held_on_unlabelled_only': 10, 'held_with_real_or_borderline': 54, 'held_over_strict_plus_unlabelled': 7, 'false_hold': 2}, 'V2a': {'held_with_real_or_borderline': 52, 'held_over_strict_plus_unlabelled': 5, 'held_on_unlabelled_only': 19}}
- New V2 flags to label: 565 (f9v2_new_flags.json)

### V2a confusion (majority category → model type, all runs)

- brand_self: {'service_promise': 6, 'trip_fact': 2, 'opinion': 2, 'number': 1, 'comparison': 1}
- contrast: {'comparison': 12, 'place_background': 16, 'number': 4, 'social_proof': 2, 'service_promise': 2, 'opinion': 3, 'trip_fact': 1}
- hypothetical: {'scene_detail': 6, 'hypothetical': 2, 'trip_fact': 1, 'place_background': 1}
- location: {'social_proof': 4}
- number: {'cta': 2, 'number': 2, 'place_background': 1, 'comparison': 1}
- opinion_rhetoric: {'place_background': 6, 'opinion': 4, 'scene_detail': 2}
- other_fact: {'social_proof': 5, 'hypothetical': 1, 'place_background': 5, 'scene_detail': 2, 'opinion': 1}
- paraphrase_supported: {'scene_detail': 3, 'place_background': 7, 'trip_fact': 14, 'opinion': 5, 'comparison': 1}
- place_background: {'place_background': 48, 'scene_detail': 7, 'hypothetical': 3, 'opinion': 3, 'trip_fact': 1}
- scene_detail: {'scene_detail': 24, 'trip_fact': 7, 'service_promise': 2, 'social_proof': 2, 'opinion': 6, 'comparison': 2, 'number': 1}
- trip_promise: {'service_promise': 9, 'trip_fact': 8, 'comparison': 2, 'social_proof': 1}

## Set B (S233 r1) — panel known-violation checklist

| item | rule | occurrences | caught (DET/F12) | caught (any incl. V2) |
|---|---|---|---|---|
| gobi_title_meta | F12_scope | 16 | 0 | 0 |
| price_title_meta | F12_scope / keyword | 16 | 0 | 0 |
| tends_to_stay | F9v2 | 1 | 1 | 1 |
| permit_logistics | F9v2 | 1 | 1 | 1 |
| nomadic_families | F9v2 | 1 | 1 | 1 |
| never_rebuilt | F9v2 | 1 | 0 | 1 |
| erdene_zuu_borrowed | F12_scope / hygiene | 8 | 8 | 8 |
| access_takes_time | F9v2 | 1 | 1 | 1 |

## Cost by arm

| arm | calls | logged $ | charged $ | est $ | tokens_in logged | tokens_in est (chars/4) | tokens_out |
|---|---|---|---|---|---|---|---|
| V2a | 76 | 0.1014 | 0.1055 | 0.1046 | 123894 | 126332 | 183874 |
| CUR | 76 | 0.2309 | 0.2551 | 0.2518 | 236664 | 261872 | 166197 |
| SETB | 20 | 0.0411 | 0.0411 | 0.0397 | 71041 | 74440 | 64508 |
