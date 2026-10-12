# Jev (decide()) on the T-series: inventory, live check on today's pieces, and whether it can back the F9 fact check

Everything below was read-only: three SELECT scripts on Dev and code reading. I made no Jev or LLM calls and wrote nothing to the DB.

**Recommendation: partially.** Jev can back the F9 fact check per flagged claim and clear the false flags. It cannot replace F9 today. Reasons are in section 5.

## 1. T-series Jev questions (`shared.decision_question`, 25 rows)

| Stage | Question | Call site | Mode | Floors (accept / reject) | Used for |
|---|---|---|---|---|---|
| t2_judge_tiebreak | a1_brand_fit | content_generation/judge_node.py:103 | shadow | none / none | tie-break of the T2 rewrite judge score |
| t3_grounding | a1_claim_supported | acp_produce/tenant_pipeline.py:115 (`t3_jev_clear`) | **enforce** | **0.85** / none | clears a T3 numeric hit when Jev is confident; never adds a violation |
| t7_debate | t7_topic_fits_brand | acp_shared/debate.py:190 | shadow | none / none | prefilter before the Luna brand-fit call |
| t8_angle_rank | t8_angle_answers | acp_angle_gate/ranking.py:137 | shadow | none / none | does the angle answer the PAA question |
| t9_facts | t9_fact_relevant | acp_content_writing/facts.py:95 | shadow | none / none | Facts entry relevance before the writer |
| t10_gates | t10_rubric_met | jev_observe.py (per F8 item) | shadow | none / none | partner of F8 |
| t10_gates | t10_brand_voice | jev_observe.py | shadow | none / none | partner of F9_brand_style |
| t10_gates | t10_cta_clear | jev_observe.py | shadow | none / none | partner of the CTA half of F9_cta_fact |
| t10_gates | t10_offer_as_certain | jev_observe.py | shadow | none / none | partner of promises_an_option; **never asked** (0 rows ever) |
| t10_gates | t10_faq_restates | jev_observe.py | shadow | none / none | partner of F7_faq_dedup |
| t10_gates | t10_same_piece | jev_observe.py | shadow | none / none | partner of F10 cannibalization; **never asked** (no pair at cosine ≥ 0.85) |

Three things matter for the rest of the report:

- **No T0 Jev question exists.**
- **Every T-native question is shadow with NULL floors (threshold_version 0, no calibration_ref).** By construction they can only return `grey`. Today 100% of their rows are grey. They are uncalibrated, not failing.
- **No T10 question asks "is this claim supported by the source".** F9's fact half and F1 have no Jev partner.

The Jev allow-list holds 4 test tenants (atlas-hearth, terra-family, trail-pulse, wildkind-travel), added 12/10 at 03:46 UTC. Every other tenant gets `skipped`.

## 2. decision_log since 2026-10-12T00:00Z (T stages)

| Stage / question | n | Zones | Cost | p50 latency |
|---|---|---|---|---|
| t10 rubric_met | 352 | all grey | $0.0167 | 136 ms |
| t10 faq_restates | 105 | all grey | $0.0068 | 121 ms |
| t10 brand_voice | 88 | all grey | $0.0074 | 131 ms |
| t10 cta_clear | 88 | all grey | $0.0042 | 109 ms |
| t7 topic_fits_brand | 272 | all grey | $0.0069 | 174 ms (max 4.0 s) |
| t3 a1_claim_supported | 98 | 97 grey, 1 accept | $0.0078 | 149 ms |
| t9 fact_relevant | 15 | all grey | $0.0005 | 132 ms |
| t8 angle_answers | 7 | all grey | $0.0001 | 182 ms |
| t2 a1_brand_fit | 4 | all grey | $0.0002 | 131 ms |

- **Per call:** about $0.00002–0.00008. The price is $0.042/Mtok input and output is free.
- **Input size today:** t10_gates averages 1,319 input tokens (max 2,879). t3 averages 1,919 (max 3,011).
- **Errors:** 0 today.
- **Cache:** hits today on t9 (22), t2 (14) and t3 (1). The cache is keyed on (subject_key, wording hash, tenant) and lasts 180 days.

## 3. T10 Jev vs gate outcome, same attempt (today's pieces)

**Join method.** `attempt_key` is only logged, not stored. I matched on the hash in `subject_key`: the md5 of `strip_citation_tags(content)[:14000]` for each attempt's text. Attempt texts came from `content_piece` (final attempt) and `discarded_attempts`.

- 49 pieces, 92 attempts. 88 attempts have Jev rows; the 4 without are attempt 1 of the first runs, before the allow-list existed.
- All 633 t10 log rows matched an attempt.
- These 49 pieces include the earlier pilot rounds, not only the final AA-768 n=10.

**What blocked attempts today.** F9_cta_fact failed on 82 attempts:

| Reason | Attempts |
|---|---|
| FACT_CHECK_MANUAL_CHECK | 76–80 |
| CTA_NOT_REFLECTED | 8 |
| Judge unavailable (Luna max_tokens) | 1 |

F1 failed on 9 attempts.

**Agreement.** "Gate pass/fail" is the gate result on the same attempt. AUC is the chance that a passing attempt gets a higher Jev p than a failing one: 0.5 means no signal.

| Jev question | Gate | Pass / fail | Jev p when gate passes | Jev p when gate fails | AUC | Reading |
|---|---|---|---|---|---|---|
| t10_cta_clear | CTA half of F9_cta_fact | 80 / 8 | 0.88–0.97 | 0.94–0.96 | **0.53** | No signal. Jev says the CTA is clear on all 88 attempts, including the 8 where the LLM said CTA_NOT_REFLECTED. |
| t10_cta_clear | whole F9_cta_fact | 10 / 78 | mean 0.952 | mean 0.956 | — | Expected: 76 of the failures are fact flags, which this question does not cover. |
| t10_brand_voice | F9_brand_style (warn) | 68 / 20 | mean 0.66 | mean 0.62 | 0.60 | Weak. Values sit between 0.33 and 0.86, so no confident zone. |
| t10_rubric_met (min over items) | F8_framework | 59 / 29 | 0.67–0.89 | 0.09–0.89 | **0.73** | Best signal. At cut 0.7: 58 agree on pass, 10 agree on fail, 19 Jev-pass where F8 failed, 1 the other way (77% agree). Only 3 confident lows (≤ 0.13), all F8 fails. |
| t10_faq_restates (max over answers) | F7_faq_dedup | 25 / 6 | mean 0.71 | 0.86–0.93 | 0.72 | Right direction: every F7 fail has p ≥ 0.86. Too few fails (6) to set a floor. |

Overall p distribution:

- cta_clear: 88/88 at ≥ 0.8.
- rubric_met: 318/352 at ≥ 0.8.
- brand_voice: mostly 0.4–0.8.
- faq_restates: bimodal (25 below 0.2, 41 above 0.8).

**F9 fact half and F1:** no Jev question, so no comparison is possible. This is the gap.

## 4. How A1 and T3 already use Jev for claim support

**s1_grounding** (content_generation/grounding.py `_judge_all`):

- Asks one Noul per sentence unit (subtitle, summary, highlights, itineraries; at least 4 words).
- State is `{source, sentence}`, using the per-unit source from AA-756 (header + that day ± 1 day + inclusions/exclusions).
- It asks `a1_claim_supported` and the shadow `a1_promise_unsupported` in the same call.
- 4 calls run at once on a 2-connection pool. It fails open.
- `classify()`: a deterministic novel number is a violation unless Jev's enforced accept clears it. An enforced reject would raise UNSUPPORTED_CLAIM, but no reject floor is set, so it never fires. A low p only adds a reviewer note.

**Wording of `a1_claim_supported`:**

- Question: "Is every fact in this sentence stated or clearly implied by the source?"
- Criteria for true: "Mood and colour about something the source names count as supported." Unsourced historical facts count as false.

**Calibration** (docs/calibration/a1_claim_supported.md):

- Accept side: p ≥ 0.90 was 50/50 correct; p ≥ 0.85 is 60/62 (97%), now enforced at threshold v2.
- Reject side: ≤ 0.30 gives 90.5% precision on non-numeric sentences, so no reject floor. The misses were table-shaped sources.
- Nghiệp overturned 5 of 59 labels, all in Jev's favour.

**Live A1 volume (14 days):** 87,323 rows.

- Non-error rows: 26,042 accept (34%), 49,538 grey. 16,105 rows (about 21% of non-error) have p ≤ 0.30.
- Errors: 11,743. 11,000 are 402 credit-exhausted and 730 are breaker-open.

**t3_grounding:** same question and state, but the whole master text is the source. Today's 98 numeric hits had median p ≈ 0.10: 77 at ≤ 0.30 and 1 at ≥ 0.85. Jev agrees most of those numbers are novel.

**a1_promise_unsupported** (shadow, never calibrated, 13,425 rows, all grey) has exactly the AA-768 policy wording: "General background about a place the source names … does not count as a promise."

## 5. Can Jev replace or back the LLM F9 fact check?

| Criterion | Evidence | Verdict |
|---|---|---|
| Question available | `a1_claim_supported` is the closest but its policy conflicts with AA-768: its criteria allow mood and colour and reject unsourced history, while AA-768 allows well-known place background and rejects invented scene detail. `a1_promise_unsupported` matches the "no unsourced tour promise" half. | A new T10 question is needed (e.g. `t10_claim_supported`, stage t10_gates) carrying the AA-768 wording: background about a named place OK; invented scene detail, other location or tour promise = unsupported; illustrative or hypothetical narration explicitly in scope. |
| Who finds the claims | Jev only answers a question about a given state; it cannot list claims. F9 already returns `unsupported_claims[{sentence, claim, why}]`. | **Back, don't replace**: F9 stays the claim finder, and Jev rules on each claim. |
| Input size | T10 sources are 0.85–5.9k chars (5 requests in claims.json); state is about 0.5–2k tokens. A1 ran sources up to 29k chars without errors. No hard limit in code; the risk is the 3 s timeout (3 tries, then fail open). | OK |
| Cost | Per claim about $0.00005–0.0001 (t3 average $0.000081). 4–8 claims per piece ≈ $0.0005. One F9 Luna call today ≈ $0.0024; the judge stays either way. | Negligible |
| Latency | p50 110–150 ms, p90 about 200–300 ms, 4 at a time. Cost of 8 claims ≈ 0.3 s per attempt. | OK |
| Determinism / caching | Same (source+sentence hash, wording, tenant) returns the cached verdict for 180 days at zero cost. Floors are re-applied on read, so moving a threshold needs no new calls. The LLM judge is temperature-0 but not stable: today's runs swung 1/5 to 3/5 on the same code. | **Strong argument for Jev**: stable verdicts per claim across attempts and reruns |
| Grey-zone rate | A1 live: about 66% of non-error verdicts are grey at accept 0.85. T3 today: 97/98 grey, but those are mostly truly novel numbers. T10 marketing prose is unmeasured. | Expect Jev to clear roughly 30–50% of F9 flags confidently; the rest stay with F9 |
| Tenant guard | `decide()` skips any tenant not on the allow-list (DPA/ZDR, design C2). Only 4 test tenants are allowed. | **Blocks replacement**: real tenants must keep the LLM path |
| Calibration data | claims.json (in the s232 scratch folder) holds 127 F9-flagged claims (87 blog, 40 LinkedIn, 22 pieces), each with sentence, claim, judge reason and the source per request. | A ready labelled-set candidate |

**Proposed design** (same pattern as `t3_jev_clear`):

1. F9 lists `unsupported_claims`.
2. Each claim is sent to the new question with state `{source: grounding_text, sentence}`.
3. If Jev's enforced verdict is accept (p ≥ the floor), the claim is dropped. Otherwise it stays.
4. If every claim is dropped, FACT_CHECK_MANUAL_CHECK is removed, the same way round 4 already drops claims the judge cannot justify.
5. Jev never adds a violation. A reject floor comes only after calibration, as on A1.

The same hook can clear T10 F1 numeric hits (9 attempts today), as T3 already does; this needs no new question.

**Gating steps:**

1. Label the 127 claims as truly invented vs over-flagged. This is the AA-701 calibration work.
2. Shadow-run the new question on them. This is a paid call: about 127 × $0.0001 ≈ $0.013, and it needs Nghiệp's approval.
3. Pick the accept floor at ≥ 95% precision.
4. Enforce.

## Other findings

- **t10_cta_clear has no power** (AUC 0.53, all p ≥ 0.88). Either the LLM over-flags CTA_NOT_REFLECTED on the 8 attempts or the question is too lenient. Those 8 need labelling before the question can be calibrated or dropped.
- **t10_rubric_met is the most promising swap** (AUC 0.73 vs F8): it could replace the GPT F8 call (F8 is non-blocking; $0.00067 per call today) after floors are set.
- **t10_offer_as_certain and t10_same_piece have never been asked**, so there is no data to calibrate them.
- **Possible cost-logging gap:** `llm_call_log` rows for the t10_judge F9 calls show average tokens_in = 2 (F8 shows 328). Input tokens for F9 look under-recorded, so F9 cost may be understated.

## Files

- Scripts (in /home/nghiep/projects/AA-Ecosys/.tmp-session/s232/):
  - s232_jevinv_q.py
  - s232_jevinv_cmp.py
  - s232_jevinv_cost.py
- Per-attempt join output: jevinv_cmp.txt (same folder)
- Code read (in /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/):
  - shared/llm_client/decide.py
  - services/acp_content_writing/jev_observe.py
  - services/acp_content_writing/quality_gates.py (F9 at about lines 584–732)
  - services/content_generation/grounding.py
  - services/acp_produce/tenant_pipeline.py (lines 96–135)
  - docs/calibration/a1_claim_supported.md