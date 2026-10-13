# S234 final synthesis: T9 gates, T2 low scores, /admin/tenants

Scope: AA-CIS-App `main` @ 20a2387 (Dev api :568 / worker :123). Read-only throughout: SELECTs, admin API GETs, and Playwright. Nothing was written to the DB or the repo.

Evidence files are in `.tmp-session/s234/final/`:
- Gates: `g_pull.py`, `db_gates.json`, `build.py`, `joined.json`, `joined2.json`, `analyze.py`, `finals.py`
- T2: `t2_scores.py/.json`, `t2_content.py/.json`, `t2_judge.py`, `t2_judge2.py`
- Tenants: `t360_audit.py/.json`, `ui/*.png`, `ui_shots.js`

Ground truth for the gate analysis is the S234 panel: rounds r1–r4, 80 pieces (32 blog, 48 LinkedIn). It comes from §1.3 of reports 02/03/04/07, plus `panel/fidelity_r4.json` for claim-level truth on r4. All 80 final texts match the DB (md5).

**Caveat:** the panel is AI agents, not humans: 4 independent reviewers plus a fidelity auditor, with ties resolved to the stricter label. Treat ±1 piece as noise.

---

## 0. Short answers

1. **Can we judge the 26 gates?** Partly.
   - The data is enough to find gates that are clearly noisy and should be dropped or fixed:
     - F1 years: 22 of 22 violations are false positives.
     - `promises_an_option` fires on 32 of 32 blogs.
     - F8 fires on 20 of 24 light LinkedIn pieces.
     - F3 has no lift over the blog base rate.
   - It is also enough to find gates that work and should be kept or tightened: F9_cta_fact, F17, F18, F16, F14 under-length and F12.
   - It is **not** enough to measure precision or recall of the rare gates. Six gates fired 0 times on 80 pieces.
   - We also lack **human labels** and the **attempt-1 warn ledger**, which is known for only 45 of 80 pieces.
   - Result: 27 gate results become a recommended set of **15 gate results, plus 6 new checks** (§1.4).
2. **Why are T2 scores low?** Mostly the scoring, not the copy.
   - The writer prompt orders brand-neutral copy, and the judge then penalises neutral copy.
   - The T2 judge takes the minimum of 3 axes plus a mission cap of 6. A1 gates on brand fit alone.
   - The job saves the last draft, not the best one.
   - The grounding check counts well-known background years and altitudes as invented. It forced 12 of 14 versions into 2 full rewrites.
   - The copy has one real defect: 5 of 14 SEO metas end mid-sentence.
   - "T2 5.0 vs A1 8.0" is not a quality gap. They are two different measurements.
3. **/admin/tenants:** most numbers are wrong or meaningless for the 4 real tenants.
   - `plan_id` is NULL, so quotas and price show 0 or ∞.
   - The Billing LLM cost is a fabricated formula: $0.054, against $6.78 actual for Atlas.
   - Lifecycle counts only apply to aa_internal.
   - The Active toggle is a no-op.
   - Delete is a soft delete that never revokes the key.
   - Almost nothing can be changed from the page except Brand.
   - Proposal: a 6-tab Tenant 360 built on one server-side `/360` endpoint.

---

## 1. Gates

### 1.1 How the gates run

`run_quality_gates` is at `services/acp_content_writing/quality_gates.py:1611-1745`. It produces **27 distinct gate results**:
- A blog piece gets 26 of them (every gate except F14_first_line).
- A LinkedIn piece gets 22 (no F4_seo_surface, F5, F3, F7 or F16).

Only 3 results come from LLM calls:
- F8 is one gpt-5.6-luna call.
- F9_cta_fact and F9_brand_style share one call.

The rest are deterministic and cost about $0.

**Cost on 80 pieces ($4.231 in total):**

| Item | Spend | Share | Per piece |
|---|---|---|---|
| F9 judge | $0.403 | 9.5% | $0.0050 |
| F8 judge | $0.130 | 3.1% | $0.0016 |
| Retries (attempts 2–3) | $1.19 | 28% | – |

Retries are driven by blocking gates. Of the 97 sentence repairs, the first failing gate was:

| Gate | Repairs |
|---|---|
| F9 | 27 |
| F15 | 22 |
| F17 | 19 |
| F1 | 12 |
| Regression guard | 7 |
| F13_repeat | 5 |
| F18 | 4 |
| F4 | 1 |

Each repair costs about $0.012.

**Base rates:**
- The panel rated 29 of 32 blogs heavy (91%) and 7 of 48 LinkedIn pieces heavy (15%).
- Any gate that fires on blogs therefore shows about 90% "precision" for free. Gates are judged on lift over this channel base rate, and on whether the violation names a defect the panel actually raised.
- Outcome: 51 approved (36 light + 15 heavy false passes), 29 held (21 heavy or reject + 8 light).

### 1.2 Gate table

Columns:
- **A1 fire** = fails at attempt 1. For warn gates the denominator is 45, because only that many attempt-1 ledgers are known.
- **Final** = fails in the final ledger.
- **Precision** = the share of final violations that name a defect the panel actually raised.

| # | Gate | What it checks | Type | Blocking? | A1 fire | Final (heavy among) | Precision / FP notes | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | F6_cta_present | CTA exists | det | block, no repair | 0/80 | 0 | Invariant, untestable at n=80 | **KEEP** |
| 2 | F0_complete | Required parts present | det | block | 0 | 0 | Invariant | **KEEP** |
| 3 | F4_extreme_length | Absurd length | det | block | 0 | 0 | Invariant | **KEEP** |
| 4 | F11_brand_name | Brand name correct | det | block | 0 | 0 | Invariant | **KEEP** |
| 5 | F10_cannibalization | Too close to an existing piece (embedding) | det | block | 0 | 0 | Invariant | **KEEP** |
| 6 | F2_brand_forbidden | Tenant forbidden words | det | block | 0 | 0 | Invariant | **MERGE** into a single lexicon gate |
| 7 | F2_banned_patterns | Core banned patterns | det | block | 0 | 0 | Overlaps the F15 stock list | **MERGE** into the lexicon gate |
| 8 | F1_grounding | Numbers/years appear in the seed | det | block | 13/80 | 3 (1/3) | **0 of 22 unique violations are panel defects.** All are year formats: '38' from "1637–38" (×9 pieces), '1630' from "1630s", '1990'. Wrongly held 2 light pieces (r1#12, r2#13). Costs 12 sentence repairs. | **TUNE** (accept "YYYY–YY" and "YYYYs" when the seed has YYYY); **BLOCK→WARN** until tuned |
| 9 | F9_cta_fact | LLM fact/CTA check against the seed | LLM | block | 47/80 | 15 (11/12 blog, **0/3 LinkedIn**) | 9 of 15 name the panel's deciding defect exactly; 5 are real but minor; 1 is partly spurious. **Bug A:** the judge sees citation tags (`:796`, called at `:1717`) and complains about "visible citation markers". **Bug B:** notes-only fallback becomes a fact hold (`:875`); 4 pieces held, 0 repairable. **Flip-flop:** in 10 regression reverts, the judge flagged a sentence it had passed unchanged one attempt earlier. Repair success 34/69 (49%). Holds: 13 (9 heavy / 4 light). | **KEEP + TUNE** |
| 10 | F9_brand_style | LLM brand voice (same call) | LLM | warn | 0/45 | 6 (5/6) | Caught Trail Pulse false passes r1#7 and r3#9, and r4#16's superlatives | **WARN→BLOCK (repair once, never hold)**, then fold into the new voice gate |
| 11 | F8_framework | LLM structure framework ("Problem / CTA" criteria) | LLM | warn | 25/45 | 53 (blog 27/29, **LinkedIn 2/24**) | Fires on 20 of 24 *light* LinkedIn pieces; no lift on blogs | **DROP** (or fold 1–2 criteria into the F9 prompt) |
| 12 | promises_an_option | Sentences citing an optional segment (`:375-418`) | det | warn | 13/45 | **32 = every blog** | About 2.5 flags per blog on headings, CTA and geology lines; catches none of the "optional flipped" defects (F17 does) | **DROP** (needs an ADR 0023/0026 note) |
| 13 | F3_structural_variance | No section notably longer | det | warn (blog) | 7/13 | 14 (13/14 = base rate) | The panel never asked for this; the anchor-weight complaint points the other way | **DROP** |
| 14 | F5_atom_density | Atoms per section | det | warn (blog) | 0/13 | 2 (1/2) | Too rare to mean anything | **DROP** |
| 15 | F7_faq_dedup | FAQ restates the body | det | warn (blog) | 0 | 0 | The `drop_restated_faq` fixer does the work | **MERGE** into F16 (keep the fixer) |
| 16 | F16_faq | FAQ has ≥3 pairs | det | block (FAQ-regen step owns it) | 7/24 (r2) | 7 (7/7) | 7 of 8 panel "FAQ under 3 pairs" defects caught. Sentence repair 0/11; regeneration fixed it from r3 | **KEEP + extend** (each answer must address its question: r4 #5, #17, #19) |
| 17 | F12_scope | Content outside the tour scope (places, journey end) | det | **warn** (`F12_SCOPE_BLOCKING = False`, `quality_gates.py:1297`) | 5/45 | 13 (blog 10/12, LinkedIn 0/1) | 9 of 16 correct. The 7 false positives were Ulaanbaatar/Thimphu seed facts in r3; r4 is 1/1 correct after the whitelist fix | **WARN→BLOCK** |
| 18 | F13_hygiene | Format hygiene, weak repeat (`hygiene.py:2112-2120`) | det | warn | 5/45 | 11 (10/11) | Its "repeats an earlier sentence" matches panel hard-error repeats (r4#17, r4#19, plus 4 r1/r2 blogs) but never blocks | **MERGE** the repeat part into F13_repeat; keep the rest as warn |
| 19 | F13_repeat | Near-verbatim repeat | det | block | 3/40 | 1 (1/1) | Correct; repair 2/5. Misses paraphrased duplicates (r3#19 had 3 and was approved; r4#1) and orphan sentences (r4#16) | **MERGE + TUNE** (sentence-repairable; add paraphrase and orphan checks) |
| 20 | F13_leak | Prompt/brief text leaking into copy | det | block | 0/60 | 0 | Missed 3 leaks: "One ruined site, one date, one fact." (r2#19), the naming note (r3#14), angle wording (r3#7) | **TUNE** |
| 21 | F17_trip_fact | Optional shown as planned, times not in source, thin-moment coda | det | block | 17/40 | 4 (2/4) | Violations match the rule. 1 FP idiom ("worn out by midday", r4#11). 2 light holds (r3#8, r4#15) were correct flags that should have been repaired, not held. Repair 17/22 (77%) | **KEEP + TUNE** (reverse direction included→"optional" r4#18, pace/difficulty promises, "lunch at" vs "near", idiom stoplist) |
| 22 | F18_rarity | Quantifier drift ("most" vs seed "many") | det | block | 13/40 | 0 | Hits are correct; repair 13/15 (87%). Misses superlatives (r4#16 "unlike almost anything else on earth") | **KEEP + TUNE** (add superlative patterns) |
| 23 | F14_social_shape | LinkedIn word band | det | warn; blocks only above 1.3× band | 1/45 | 5 (3/5; under-length 3/3) | Under-length on r2#3 (119 words), r4#6 (105), r4#11 (113): all heavy, and the panel named it the deciding defect on r4#6 and r4#11 | **Under-length WARN→BLOCK** (regenerate with unused seed facts) |
| 24 | F14_first_line | LinkedIn hook line | det | block, no repair | 0/36 | 1 (1/1) | Correct | **KEEP** |
| 25 | F15_voice | Stock AI lines + contrast frames (`hygiene.py:1428`) | det | blocks on attempt 1 only (`:1545`), never holds | **44/80** | 9 warn (8/9) | 36 of 44 clean after repair. Stock list hits 9 pieces. The contrast-frame check flags only 3 pieces in r2–r4 against a panel count of 16–19 per 20-piece round. Only 7 of 85 runs are seed paraphrases | **KEEP + TUNE** (widen the `not X, it is Y` family) |
| 26 | F15_voice_warn | Softer voice signals | det | warn | 2/45 | 3 (1/3) | Too rare | **MERGE** into F15 |
| 27 | F4_seo_surface | Title/meta/slug surface (blog) | det | block | 3/32 | 1 (1/1) | Correct; repair 2/4. r3 had meta fact errors in 11 of 20 pieces that nothing checks | **KEEP + extend** (title/meta fact check against seed dates and spans) |

The task said "26 gates". There are 27 distinct results, and a single blog carries 26 of them.

**Concrete F9_cta_fact tune list:**
1. Strip citation tags before the judge sees the text.
2. Replace the notes-only fallback with a `TEXT_INTEGRITY` code that quotes the sentence, so sentence repair can act. Three of the 4 fallback holds were real defects: a doubled CTA, a broken repair sentence, a garbled line.
3. Pass the title and meta to the judge.
4. Move toward deterministic typed claims (F9 v2).
5. On LinkedIn, repair instead of hold. LinkedIn holds were 0 of 3 heavy.

### 1.3 Defect classes the gates do not catch (r4 unless noted)

| Defect class | Panel count | Caught at final | Gap |
|---|---|---|---|
| Contrast frames / stock AI lines | 17 of 20 pieces | F15 contrast check flags 3 pieces (r2–r4) | Regex too narrow |
| Claim-level unsupported (fidelity audit) | 90 non-CTA claims | about 9 (~10%) via F9/F17 | F9 is CTA-centric; no claim-level check |
| Tenant voice (Trail Pulse energy, Terra child's-eye, WildKind habitat) | 9 | 1 (F9_brand_style) | **6 of the 15 false passes are Trail Pulse** |
| Repair and FAQ integrity (orphans, split paragraphs, broken grammar) | 8 | 3 | No post-repair integrity check |
| Overclaims / superlatives | 6 | 1 | F18 lacks superlatives |
| Invented siting intent ("deliberate", "never an accident", "narrow" vs seed "long") | 5 | 2 (F9) | No interpretation guard |
| "Optional" flipped / invented trip details | 9 | 7 (missed #16, #7) | F17 lacks the reverse direction |
| FAQ answer does not answer its question | 3 (#5, #17, #19) | 0 | New check |
| Hashtag near-miss of seed place names ("#PaaTaktsang") | seen | 0 | New check |
| Digits vs words when the seed has digits | seen | 0 | New normaliser |

### 1.4 Recommended gate set after the changes

**Blocking, with repair (sentence or regeneration):**

| Gate | Change |
|---|---|
| F9_cta_fact v2 | Tuned as above |
| F17_trip_fact | + reverse direction, pace, idiom stoplist |
| F18_rarity | + superlatives |
| F13_repeat | Absorbs the F13_hygiene repeat check, paraphrases and orphans |
| F15_voice | Absorbs F15_voice_warn; wider contrast frames; attempt-1 block stays |
| F16_faq | Absorbs F7; ≥3 pairs plus answers address their questions |
| F12_scope | Now blocking |
| F14_social_shape | Under-length now blocks, via regeneration |
| F4_seo_surface | + title/meta facts |
| **NEW** voice rubric | Tenant voice; replaces F9_brand_style |
| **NEW** post-repair integrity | Orphan, split paragraph, grammar |

**Blocking, no repair (invariants):**
- F0_complete, F4_extreme_length, F6_cta_present, F10_cannibalization, F11_brand_name, F14_first_line
- F13_leak (tuned)
- **NEW** lexicon gate (F2_banned_patterns + F2_brand_forbidden + the F15 stock list, with severity per source)

**Warn:**
- F1_grounding, until the year tune lands; then back to blocking
- F13_hygiene, format checks only

**Dropped:** F8_framework, promises_an_option, F3_structural_variance, F5_atom_density.

**New, lower priority:** siting-intent guard, hashtag near-miss check, digit normaliser.

**Effect:**
- About 18 gate results instead of 27, including the 3 new ones.
- F8 saves 1 LLM call per attempt (3.1% of cost).
- F1 alone stops 12 wasted repairs and 2 wrong holds per 80 pieces.
- The two main recall holes (voice, claim level) become explicit gates instead of warn noise.

### 1.5 Data we still lack and how to get it

1. **Human labels.** All ground truth today is AI-panel output.
   - Ask: Nghiệp, and ideally chị Thư for 20 of them, label **40 pieces**. Stratify as 20 blog + 20 LinkedIn and 50% approved + 50% held, with the 4 tenants balanced.
   - Use a fixed checklist: verdict (publish / light edit / heavy / reject), plus the 8 defect classes in §1.3 as checkboxes, plus a quoted sentence for each defect.
   - Effort: about 2–3 h of labelling.
   - Output: inter-rater agreement between the AI panel and the humans (κ). This tells us whether the panel can stand in for humans going forward.
   - Tooling: a "Label" action on `/admin/content-quality` (AA-769) that writes to a small `content_piece_label` table, so the labels persist and gates can be re-scored automatically.
2. **The full per-attempt gate ledger.** Warn results at attempt 1 are known for only 45 of 80 pieces, because only the final and discarded attempts keep a ledger.
   - Fix: persist `gate_ledger` for every attempt (in `repair_log` or `discarded_attempts`).
   - Without it, we cannot measure what a warn gate would catch before repair masks it.
3. **Volume for the rare gates.** Six gates fired 0 times.
   - Fix: a seeded fault-injection test set, for example 30 synthetic pieces with a planted leak, wrong brand name, missing CTA, duplicate FAQ or cannibal copy. This gives deterministic recall checks in CI for free, with no LLM cost.
4. **F9 judge stability.** The 10 flip-flops suggest variance.
   - Fix: re-judge 20 fixed texts 3 times each (about $0.30) and report the agreement rate. That is the prerequisite for deciding between F9 v2 deterministic claims and an ensemble.
5. **The F1 year fix replayed** against the 80 stored texts, offline at $0. This confirms the 22 false positives go to 0 without losing real number errors.

---

## 2. T2: why tenant rewrite scores are low

### 2.1 Data (Dev, 14 T2 versions, all written 2026-10-12)

The admin `/tenants` view shows 13 versions, because one row was written later. This analysis uses all 14.

**Scores (all whole numbers, none ≥ 7.5):**

| Tenant | Average | n |
|---|---|---|
| Atlas & Hearth | 5.0 | 3 |
| Trail Pulse | 4.0 | 3 |
| WildKind | 5.75 (5/7/7/5) | 4 |
| Terra Family | 7.0 | 4 |

**Status and repair:**
- 6 versions are `ai_generated` and 8 are `needs_review`.
- 12 of 14 have `qa_status='escalated'` with `qa_repair_count=2`. Every escalation is `grounding:novel_numeric_claim`, plus 1 FORBIDDEN_WORD.

**A1 comparison:** the same tours' A1 `published_tours.quality_score` is **8.0** for all of them. Their sub-scores are brand/seo/structure 10 and quality 9.5–10.

**Judge calls (104 in these jobs):**
- Mean score 5.08 against a pass line of 7.0. Only **21 passed**.
- In **72 of 104** calls the judge found `mission_present=false`. 0 of those 72 passed. Mean score was 4.43 with the mission missing and 6.53 with it present.
- The "would this differ for another brand" axis was below brand fit in 60 calls and above it in 4, so it is almost always the binding number.
- On brand fit alone (A1's rule), **32 of 104** calls would pass instead of 21.

**Cost:**
- $5.21 in total, $0.37 per version.
- Each job made 6–9 `t2_generate` calls (Sonnet 4.6). A version with no repair round cost $0.19 (453c0a24).
- The judge is `t2_judge` = gpt-5.6-luna, with fallback to gpt-6-luna and a 10% shadow.

**Judge reasons are not persisted.** The version row has no judge field, and `llm_call_log.quality_signal` holds only numbers.

### 2.2 Root causes

| # | Cause | Evidence | Effect |
|---|---|---|---|
| 1 | **The writer is told to be brand-neutral; the judge punishes neutrality** | T2 reuses A1's system prompt: "master content catalog used by many different travel brands", "Calm, factual, editorial", "never adopt a persona" (`services/content_generation/prompts.py:112-130`). The tenant prompt is "append only — do not override" (`batch_prompt.py:105`). Itinerary days must be "NEUTRAL third-person editorial… factual catalogue record" (`prompts.py:374-383`). The judge says "generic travel copy that would fit any brand must score low" and checks a "mission-hook" per day (`brand_fit.py:51,158`); a missing mission caps the score at 6 (`judge_node.py:33`). The brand profile has **no mission field**. | First drafts score 3–5. Scores reach 7 only when the judge's feedback leaks into a retry (c5df11d3: 4→7→5→7). |
| 2 | **A different, stricter rubric shown as the same number** | A1 gates on brand fit only (`judge_node.py:41-48,134`). T2 takes min(validate, brand_fit, cross_brand_distinct, mission cap 6) (`brand_fit.py:249,304`; `judge_node.py:134,141`). The cross-brand question (`brand_fit.py:156`) cannot be answered, because the judge never sees another brand's version. S204 measured Luna giving 2–6 on it where GPT-4.1 gave 8–9. | "5.0 vs 8.0" compares two different metrics. |
| 3 | **The last draft wins, not the best** | The rewrite check regenerates the whole tour up to 2 times (`tenant_pipeline.py:226-270`). Repair feedback holds only grounding/structure issues, not the judge's feedback (`:269`). The job saves the last draft (`t2_rewrite_job.py:208,223`). When retries run out, the graph stops (`graph.py:944,1102`) and the draft is still saved, as `needs_review`. | cbba9416 and 39d1e38c lost a 7.0 draft; 5b442cdf lost two 7.0 drafts; 453c0a24 was saved at 3.0. |
| 4 | **The grounding check rejects allowed background facts** | The writer may add "well-known background… its era" (`prompts.py:165`) and should "include altitude if trekking" (`prompts.py:368`). The check flags any number absent from the A1 text (`tenant_pipeline.py:74-89`): "1954 battle", "17th-century dzong", "3,120 m". Jev clears only master content. | 12 of 14 escalations, about 2.5× writer cost, and the trigger for cause 3. |
| 5 | **SEO metas are cut mid-sentence and nothing scores it** | 5 of 14 end in a fragment: "…with expert.", "…with active daily.", "…mountain farming and valley.", "…across fragile.", "…across distinct mountain." This comes from the last-resort word cut (`seo_meta_utils.py:222-232`). 2 of 14 append the wrong country ("Cuc Phuong National Park, in Laos.", `seo_meta_utils.py:254-255`) on a Laos→Vietnam tour. The complete-sentence check accepts both. | A real, visible defect that the tenant sees. |

**Reading of the 6 lowest versions** (cbba9416, 39d1e38c, 9a4b7959, 453c0a24, 7ef62541, 81102180):
- **Facts and structure: good.** Named places, distances, day structure, local dishes.
- **Brand voice: genuinely weak**, and the judge is right about that.
  - Trail Pulse ("Energetic, Fresh, Direct, Lightly playful") reads like a catalogue: "checks into the hotel for the night".
  - Atlas & Hearth gets only "private" and "expert guiding"; "luxury" is core-banned (`prompts.py:138`).
- **SEO meta** is broken in 3 of these 6.
- **Risk in the other direction:** passing versions add brand claims that are probably absent from the source. Examples: Terra "children aged seven to sixteen", WildKind "consent-based community visit". The judge may be rewarding claims the fidelity rule forbids. This is not yet verified against the source.

### 2.3 Fixes

| # | Fix | Where | Expected effect |
|---|---|---|---|
| F-a | T2 gets its own base prompt, or drops the neutral-voice and "append only" rules when `is_tenant_rewrite`. Rule 6 (no invented facts) stays. Day bodies use the brand voice. | `prompts.py:112-130,374-383`; `batch_prompt.py:105` | First-draft brand fit rises; fixes the Trail Pulse and A&H voice |
| F-b | Gate on brand fit only, as A1 does. Log cross-brand distinct and mission as diagnostics, with no cap, until a `core_idea`/mission field exists in T0 (AA-771). | `judge_node.py:33,134,141`; `brand_fit.py:156,249,304` | On today's data, passes go from 21 to 32 of 104 |
| F-c | Best draft wins: keep the highest-scoring draft that passes the grounding check. Repair rounds edit the previous draft with the judge's feedback instead of rewriting from scratch. When retries run out, return the best draft. | `tenant_pipeline.py:226-270`; `t2_rewrite_job.py:208,223`; `graph.py:944,1102` | Recovers the 3 lost 7.0 drafts; lowers cost |
| F-d | Grounding check: apply A1's background-fact allowance (years, centuries, well-known altitudes of named places), or route such sentences through Jev clearing | `tenant_pipeline.py:74-89` | Removes most of the 12/14 escalations and roughly 60% of T2 writer cost (estimate) |
| F-e | SEO meta: reject word cuts ending on a dangling adjective or noun; prefer the clause cut or a short re-ask; skip "in {country}" on multi-country tours; tighten the complete-sentence check | `seo_meta_utils.py:222-232,254-255` | 5/14 → 0 fragments; 2/14 → 0 wrong countries |
| F-f | Persist the judge result per version: brand_fit, cross_brand, mission, feedback text, and which axis set the score (JSON column on `tenant_tour_versions`, or `job.result`) | T2 job + migration | Admins can finally see *why* a version scored low |
| F-g | Brand-claim fidelity: run the F9-style fact check on T2 output against the A1 source for brand-flavoured claims (ages, "consent-based", etc.) | T2 graph | Stops the judge rewarding invented brand claims |
| F-h | AA-770 compliance: tenant status no longer derives from the score (every finished version becomes "Ready to review"; `needs_review` stays admin-only). Remove `quality`/`quality_score` from the tenant pool and detail APIs and replace the "Best quality first" sort. | `t2_rewrite_job.py:230-235`; `v1_tours.py:109,127,668-701`; portal `ui.tsx:91,100`, `DashboardTab.tsx:204`, `PlaceholderTabs.tsx:51` | The tenant sees content only |

**How to verify after the fixes:**
- Rerun the same 14 tour×tenant pairs, about $3–5 (≤ 50-tour rule respected).
- Targets:
  - mean judge brand fit ≥ 7
  - escalations ≤ 2 of 14
  - 0 broken metas
  - cost per version ≤ $0.20
- A human reads the 4 Trail Pulse and A&H versions for voice.

---

## 3. /admin/tenants (Tenant 360)

The page is `frontend/app/admin/tenants/page.tsx`: a single 1251-line file that uses no kit DataTable or Tabs.

There are 8 tenants in `shared.tenants`. The list shows 5 (`WHERE is_active = true`, `admin.py:296`): aa_internal plus atlas-hearth, terra-family, trail-pulse and wildkind-travel, all created 2026-10-12 on `growth`. Three offboarded tenants are hidden.

### 3.1 Root data defects

1. **`plan_id` is NULL** for all 4 test tenants and for test-1.
   - `create_tenant` never sets it (`admin.py:171`).
   - The `PATCH` plan change only sets `plan_tier` and `rate_limit_rpm` (`admin.py:423`).
   - So quotas, price and overage come back NULL and render as 0 or ∞.
2. **`v_tenant_monthly_usage.llm_cost_usd` is fabricated.** It is `pipeline_runs.cost_usd + 0.018 × count(ttv ai_generated)`.

   | Tenant | View says | `llm_call_log` says |
   |---|---|---|
   | Atlas | $0.054 | **$6.78** |
   | Terra | $0.072 | $6.83 |
   | WildKind | $0.072 | $1.92 |
   | Trail Pulse | $0.054 | $1.61 |
   | aa_internal | $0.1795 | $115.07 MTD (NULL-tenant rows) |
3. **Lifecycle and source counts cover aa_internal only.** `raw_tours` and `published_tours` hold only aa_internal rows (917 source, 892 master active), so every tenant shows 0/0/0.
4. **`this_month.tours_rewritten` is really the all-time active source count** (`admin.py:317`).
5. **API calls are mostly portal clicks.** `tenant_api_usage` logs the portal UI's own requests: Atlas 417, Terra 429, WildKind 117, Trail Pulse 93 in about 2 days. The 97,990 admin calls have NULL tenant_id.
6. **Three disagreeing sources for markets:** brand `target_markets`, `tenant_seo_config.target_market` (which has an `unsupported` list: Atlas AE,SA,SG,HK; Terra AE,SG,HK; Trail CA,SG; WildKind CA,NZ), and `acp_shared.tenant_config`, which falls back to US/blog for everyone.
   - The unmapped-market banner reads `shared.unmapped_market_requests`, which is empty. It only records a market when *no* country is supported (`seed_builder.py:348`).
7. **`GET /tenants/{id}/usage` returns 500 for all 8 tenants.** It selects columns that no longer exist in the view (`admin.py:362`).

### 3.2 Metric-by-metric audit

| Metric (location) | Source | Live value (Atlas unless noted) | Correct? | Meaningful? | Actionable? | Verdict |
|---|---|---|---|---|---|---|
| Header "5 active · 917 source · 892 published" (`page.tsx:1157-1210`) | aa_internal catalog | 917/892 | Yes | No (catalog, not tenants) | No | **DROP** (lives on Master Content) |
| Card Total Tenants / Active | `/tenants` (active only) | 5/5 | Misleading (equal by construction) | No | No | **REPLACE** with Active / Suspended / Offboarded counts |
| Cards Source (active) / Master (active) | aa_internal | 917/892 | Yes | No | No | **DROP** |
| Unmapped-market banner | `unmapped_market_requests` | empty | Per its rule | Blind to partly unsupported markets | No | **FIX**: surface `target_market.unsupported` |
| Row: Plan badge + posts/week | `plan_tier`, config | growth, 3 | Badge yes; no plan attached | Yes | No (`PUT /config` not wired) | **FIX** + "no plan attached" warning |
| Row: Country | `tenants.country` | null for all 8 | – | No | No | **DROP** (or derive from markets) |
| Row: Lifecycle pills | raw/published | 0/0/0 · 0/0/0 | Yes, but empty | No for tenants | No | **DROP** |
| Row: "Source Active" + calls | raw_tours + tenant_api_usage | "0 active", "417 calls" | Calls yes | Low (portal traffic) | No | **DROP**; replace with T2 versions + T9 pieces MTD |
| Row: % tour quota | view quota | 0% | **Wrong** (NULL plan; 3 rewrites actually exist) | Yes once fixed | No | **FIX** |
| Row: Active/Inactive toggle | `PATCH` (`page.tsx:921-924`) | – | **Broken**: UI sends a JSON body, API reads a query parameter (`admin.py:411-412`); returns 200 and changes nothing; UI flips local state (`page.tsx:930`). Confirmed by code, not clicked. | – | Looks actionable, isn't | **FIX** |
| Row: Delete | `DELETE` (`admin.py:457,467`) | – | Soft delete only; no key revoke, no audit; says "cannot be undone"; tenant becomes unrestorable from the UI | – | Misleading | **REPLACE** with wired `/offboard` (`admin.py:1065`) + reason |
| Row: Key rotate | `generate-key` (`admin.py:1024`) | – | Works; no audit row | Yes | Yes | **KEEP** + audit write |
| Panel: Total Rewrites | count of `tenant_tour_versions` (`admin.py:605`) | 3 (Terra 4 versions / 3 tours) | Counts versions, not tours | Partly | No | **RELABEL** "T2 versions (tours)" |
| Panel: LLM Cost (all time) | `llm_call_log` (`admin.py:615`) | $6.781 / $6.830 / $1.917 / $1.609 | **Correct**, but contradicts the Billing tab; aa_internal $155.71 includes NULL-tenant spend; window cost returns null (`admin.py:793`) | Yes | No | **KEEP**, split by stage group, show MTD vs plan price |
| Panel: API Calls (Mo) | `tenant_api_usage` | 417 / 429 / 117 / 93 | Yes | Low | No | **SPLIT** into portal vs integration (AA-766) |
| Panel: API Quota % | view | 0% | **Wrong** | Yes once fixed | No | **FIX** via plan_id |
| Panel: Rate Limit | `rate_limit_rpm` (enforced in `rate_limit.py:45`) | 300/min | Yes | Yes | No (shown 3×) | **KEEP once**, editable in Account & Plan |
| Panel: Plan / Member since | tenants | Growth / 2026-10-12 | Yes | Yes | No | **KEEP once** (duplicated in Settings and Billing) |
| Tab Tours + Tab Activity | `tenant_tour_versions` (`admin.py:600-620` vs `:977`) | 3 rows, scores 4/6/5, all needs_review | Score yes; name is A1's (`admin.py:712-720`); capped at 50 | Score not explained; green only at ≥ 9 (`page.tsx:275`), so always amber/red | No | **MERGE**; add qa_status, judge axes, T3 issue counts, tenant's own name, paging, 7.0 colour line, "not comparable to A1" label |
| Tab Pipeline (in Tours) | legacy `shared.pipeline_runs` (`admin.py:724-740`) | – | Stale source | No | No | **DROP** (use `shared.job`) |
| Tab API Usage | view | "417 / 0 (0%)" (`page.tsx:368`) | Wrong | Low | No | **MERGE** into Usage & Cost |
| Tab Brand | `tenant_brand_rules` + syncs `tenant_seo_config` (`admin.py:943-970`) | v3; CTA empty; system prompt empty | Yes | Yes | **Yes (only editable tab)** | **KEEP + completeness checklist** (CTA empty 4/4, system_prompt empty 4/4), show rewrite_language and the supported/unsupported market split |
| Tab Social Content | `a4/content-log` (`admin_a4.py:507`), `publish-log` | written 67/67/15/24; published 0 | "Written" is a list length capped at 500, not a count; publish_log is empty platform-wide | Low | No | **MERGE** into Content & Quality with a true `COUNT(*)` |
| Tab Usage & Billing | `/admin/billing` (`admin_pipeline.py:4948`) | $0.00, LLM $0.054, Tours 3/∞, API 417/∞ | **Wrong**; with no view row it returns **fabricated defaults: $299, 50 tours** (`admin_pipeline.py:4983-4992`) | Yes once fixed | No | **REBUILD** on `llm_call_log` + plan |
| Tab Quality | `a4/gate-telemetry` | blog 42 / 10 warn / 31 held; LinkedIn 25/7/14; Terra blog held 34/42 (81%) | Counts match SQL; fetches all platform data and filters in browser (`page.tsx:822-826`); warn = approved+flagged only (27 of 31 held also carry flags) | Partly (no reasons) | No | **REBUILD** server-side per tenant: top failing gates, retry_count, deep link to `/admin/content-quality?tenant=` |
| Tab Audit | `/audit` (`admin.py:519,540-547`) | 262 events, top 100 | Drops `details`; no filter; dominated by login (53) and content_piece created/finished (67+67) | Low | No | **FIX**: add details, action-type filter, admin-action writes |
| Tab Settings | tenants | Plan/rpm/since | Yes, duplicated | No | No (text says editors are "a follow-up") | **DROP**; fold into Account & Plan |
| Not shown: Jev spend / zones | `decision_log` | – | – | Yes | – | **ADD** |
| Not shown: T0 completeness | brand rules | – | – | Yes | – | **ADD** |

**UI (Playwright, live Dev):**
- 0 console errors; all `/api/admin/*` calls returned 200.
- Desktop at 1440px is fine.
- At 390px mobile:
  - The cards stay at 4 columns (`page.tsx:1199`), so the 4th card is clipped.
  - `main` has scrollWidth 488 against a 390 viewport.
  - The 10-tab bar overflows: the Settings tab sits at x=600.
- Dark mode is fine.
- No kit components are used, which violates aa-ui-verify.

### 3.3 Redesign proposal

**List view (one row per tenant):**
- Columns:
  - name
  - status (active / suspended / offboarded), with a filter
  - plan (+ "no plan attached" alert)
  - MTD LLM cost vs plan price (margin)
  - T2 versions MTD
  - T9 pieces MTD
  - held %
  - T0 completeness %
  - unsupported markets
  - alert badge
- Cards: Active / Suspended / Offboarded / Tenants with alerts.

**Panel, 6 tabs (kit Tabs + DataTable, server data from one endpoint):**

| Tab | Shows | Actions |
|---|---|---|
| 1. Account & Plan | Plan, price, quotas, overage; posts/week; rate limit; created; cancelled_at + reason; key last rotated | Change plan (sets `plan_tier` + `plan_id` + rpm together), override limits, suspend/resume, offboard with reason, rotate key (all audited) |
| 2. Brand (T0) | Current editor + completeness checklist (core idea/mission, segment, mindset, voice, style guide, good examples, forbidden words, CTA, system prompt, language); em-dash and length lint; version history (`tenant_brand_rule_versions`) | Edit, restore a version |
| 3. Markets | Declared → resolved countries, each DFS-supported or unsupported; `segment_research_log` coverage per market | Edit; one store replaces `tenant_config` (AA-766 scope 3) |
| 4. Content & Quality (admin-only) | **T2:** per version: tenant title, score labelled "T2 brand score", qa_status, judge axes (brand_fit / distinct / mission), judge feedback, T3 issue counts, repair count. **T9:** per channel: approved / held / warn / retry, top failing gates | Deep link per row to `/admin/content-quality?tenant=`; rerun T2 for a tour; tenant still always receives content (AA-770) |
| 5. Usage & Cost | `llm_call_log` cost by stage group (T2 / T9 / T10 judge / Jev / other), monthly; $/piece and $/tour; MTD vs plan price = margin; quota meters on real counts (T2 tours vs `tours_quota_monthly`, pieces vs posts_per_week × 4); API calls split portal vs integration | – |
| 6. Activity & Alerts | Audit with type filter (admin / content / login) and `details`. Alerts: no plan, missing T0 fields, unsupported markets, held rate above threshold, cost over budget, Jev 402s | Acknowledge alert |

**API changes:**
1. `PATCH /admin/tenants/{id}` (`admin.py:406`): take a JSON body (`plan_tier`, `is_active`, `rate_limit_rpm`, `posts_per_week`); resolve `plan_id`; write audit. `create_tenant` sets `plan_id`.
   - One-off data fix: backfill `plan_id` for 5 tenants (**needs Nghiệp's approval**).
2. Migration: `v_tenant_monthly_usage.llm_cost_usd` = sum of `llm_call_log` by tenant and month (or stop reading the column).
3. Delete or fix `GET /tenants/{id}/usage` (500 today).
4. **New `GET /admin/tenants/{id}/360`**: plan and billing, T0 completeness, markets plus research coverage, T2 summary with judge signals (needs F-f), tenant-scoped T9 gate summary, cost by stage group plus Jev (MTD and 30d), alerts.
5. `content-log` / `publish-log`: true `COUNT(*)`, or the counts move into `/360`.
6. `GET /tenants?include_inactive=`: return `cancelled_at`; drop the lifecycle block for non-internal tenants.
7. `/audit`: add `details` and an `action` filter. Add audit writes for key rotation, plan/status changes and offboard.
8. Markets: a single store; fold `/config` into it; expose `target_market.unsupported`.
9. Reporting label: the pre-AA-763 `s1_judge` rows with `source='debate'` (68 per tenant, 272 in total) become `t7_debate_judge`.

---

## 4. PROPOSED Linear issues for S235 (needs Nghiệp's approval; nothing has been created)

Estimates are in engineering days. P1 means do in S235.

| # | Title | Project | Parent / extends | Scope | Done when | Est |
|---|---|---|---|---|---|---|
| 1 | T9 gates: F1 year-format tolerance (BLOCK→WARN until fixed) | CIS Core | extends AA-768 | Accept "YYYY–YY" and "YYYYs" when the seed has YYYY; warn until merged | Offline replay on the 80 S234 texts: F1 false positives 22 → 0, no real number error lost; unit tests | 0.5 |
| 2 | T9 gates: F9_cta_fact v1.1 (strip citation tags, TEXT_INTEGRITY code, title/meta input, LinkedIn repair-not-hold) | CIS Core | extends AA-768 | `quality_gates.py:796,875,1717` | Replay on r4: 0 "citation marker" notes; the 4 fallback pieces get a quoted sentence; 3-run stability test reported | 1.5 |
| 3 | T9 gates: drop F8_framework, promises_an_option, F3, F5; merge F7→F16, F15_voice_warn→F15, F2 variants→lexicon | CIS Core | new, child of AA-741 | Remove or merge; ADR 0023/0026 note for promises_an_option | Gate count 27 → ~18 results; F8 LLM call removed (cost −3.1%); CI green | 1 |
| 4 | T9 gates: promote F12_scope, F14 under-length and F9_brand_style (repair-once) to blocking | CIS Core | child of AA-741 | Flip `:1297`; under-length → regenerate with unused seed facts | 20-piece pilot: Trail Pulse false passes ↓; no new light holds | 1 |
| 5 | T9 gates: recall tunes (F17 reverse + idioms, F18 superlatives, F15 contrast frames, F13 repeat/paraphrase/orphan, F13_leak patterns, F16 answer-addresses-question) | CIS Core | child of AA-741 | Deterministic patterns + tests built from the S234 panel examples | Each S234 example cited in §1.3 is caught by a test | 2 |
| 6 | T9 gates: new tenant-voice rubric + post-repair integrity check | CIS Core | child of AA-741 / AA-771 | Voice rubric per tenant (Trail Pulse, Terra, WildKind); orphan, split-paragraph and grammar check after repair | 20-piece pilot: ≥4 of 6 Trail Pulse-type false passes caught | 2 |
| 7 | Gate evaluation data: persist per-attempt gate ledger + human label action on Content Quality | CIS Core + Portal | extends AA-769 | Store `gate_ledger` for every attempt; "Label" action → `content_piece_label`; fault-injection test set (30 synthetic) | 40 pieces labelled by Nghiệp (chị Thư optional); κ panel vs human reported | 1.5 + 2–3 h labelling |
| 8 | T2: writer prompt for tenant voice + judge gates on brand fit only (mission/distinct logged, not capped) | CIS Core | new, relates AA-771 | `prompts.py:112-130,374-383`; `batch_prompt.py:105`; `judge_node.py:33,134,141`; `brand_fit.py` | Rerun of 14 pairs: mean brand fit ≥ 7, human voice check on Trail Pulse and A&H | 1.5 |
| 9 | T2: best-draft-wins + targeted repair + background-fact grounding allowance | CIS Core | new | `tenant_pipeline.py:74-89,226-270`; `t2_rewrite_job.py:208,223`; `graph.py:944,1102` | Rerun: escalations ≤ 2/14; cost per version ≤ $0.20; no saved draft scores below a passed one | 2 |
| 10 | T2: SEO meta truncation + wrong-country suffix | CIS Core | new (small) | `seo_meta_utils.py:222-232,254-255`; complete-sentence check | 0/14 fragment endings and 0 wrong countries on rerun; unit tests for the 7 cases found | 0.5 |
| 11 | T2: persist judge breakdown per version + brand-claim fidelity check | CIS Core | new | JSON column (migration) or `job.result`; F9-style claim check vs the A1 source | Every new version has brand_fit, distinct, mission, feedback and the binding axis; "children aged seven to sixteen"-type claims flagged | 1.5 |
| 12 | AA-770 compliance: decouple tenant status from score; remove quality fields from tenant APIs | CIS Portal | extends AA-770 | `t2_rewrite_job.py:230-235`; `v1_tours.py:109,127,668-701,740,781`; portal badges | Tenant API responses contain no score fields; portal shows "Ready to review" only | 1 |
| 13 | Tenant admin: fix status toggle, plan_id on create/patch, wire offboard, audit writes, remove /usage 500 | CIS Portal | new (bugs; or a comment on AA-766) | `admin.py:171,406-423,457,1024,1065,362`; plus a **plan_id backfill for 5 tenants (approval required)** | Toggling suspends for real (DB check); quota and price non-NULL; offboard revokes the key and writes audit | 1 |
| 14 | Billing: replace fabricated `llm_cost_usd` view column + starter defaults | CIS Portal (migration in CIS Core) | extends AA-766 | New view migration from `llm_call_log`; remove `admin_pipeline.py:4983-4992` defaults | Atlas Billing cost = `llm_call_log` ±$0.01 (AA-766 done-when) | 1 |
| 15 | Tenant 360 redesign: `/360` endpoint + 6-tab kit page | CIS Portal | **is** AA-766 (extend scope) | §3.3 sections, API changes 4–9, mobile fixes | aa-ui-verify passes (desktop/mobile/light/dark); every metric traced to a source in a test; no Total==Active, lifecycle or fake numbers | 4–5 |

**Suggested S235 order** (3–5 issues per session rule): #1, #2, #10, #13, then #8 or #3. #15 depends on #11, #13 and #14 and spans more than one session.

**Approval points for Nghiệp:**
- Creating these issues.
- The plan_id backfill in #13 (a DB write).
- Dropping `promises_an_option` (an ADR change).
- The labelling time in #7.
- The ≤ $5 T2 rerun to verify #8–#10.
