# T-series social and blog content: F9 calibration, Jev integration, gate verdicts and next steps (S232 design)

**Scope.** This covers AA-768 (T9 fidelity), AA-701 (T10 gates and Jev), and the remaining T-axis work under AA-741.

**Code.** `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App`, `main` @ `80101bf` (#673). Paths are relative to that folder unless they start with `infra/`.

**Data.** All read-only, all times UTC. Files are in `/home/nghiep/projects/AA-Ecosys/.tmp-session/s232/`:
- `claims.json`: 127 unique flagged sentences from 22 pieces created 10:08–11:17.
- `pieces_text.json`: 49 final pieces.
- `jevinv_cmp.txt` and `rerun*.json`.
- Labels: the 3-labeler majority result under the S232 policy.

"Social" means LinkedIn, the only social channel that ran today. Round names are R0–R5:

| Round | R0 | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|---|
| Created at | 09:53 | 10:08 | 10:35 | 10:52 | 11:11 | 11:17 |

## Bottom line

1. **The F9 fact check is the binding constraint, and its errors follow a pattern.**
   - Of the 127 sentences F9 flagged, 48 are real violations (38%; 95% CI 30–47%), 46 are over-strict (36%) and 33 are borderline (26%).
   - All 46 over-strict flags fall into 4 categories that F9's own prompt says never to flag: place background (25), paraphrase of the SOURCE (14), the brand describing itself (4) and opinion (3).
   - Flags in the violation categories are 75% real and never over-strict.
2. **A perfect F9 alone does not reach 4 out of 5.**
   - If a judge that applies the policy perfectly re-checked today's final texts, R1–R5 would go from 8/25 approved to 12–13/25.
   - LinkedIn would go from 6/15 to 10–11/15. Blogs stay at 2/10.
   - Every LinkedIn piece that would still be held has exactly 1 real violation. Held blogs have about 2.
3. **Most real violations are asked for upstream.**
   - The T8 angles that every rerun reuses tell the writer to invent: "opens mid-moment — … the guide unrolling a map", "sound of prayer wheels, smell of incense", "why Bhutan is one of the only places this layer still exists intact".
   - The seed's sibling block feeds in other places (Ladakh, Mongolia, a Seoul city tour) as "the same moment".
4. **Blogs also have 3 mechanical blockers.**
   - The writer is capped at 2,048 tokens. 20/37 blog calls were cut off, and 5/20 final blogs end mid-text, one of them approved.
   - F3 fails 4/10 final blogs since 10:08 and forces full rewrites, which invent new facts.
   - F8's CTA item cannot pass on a blog that ends with a FAQ, and the blog format requires the FAQ to come last.
5. **Jev: yes, but only as a second opinion that can overrule F9's flags (and F1 hits), never add to them.**
   - It needs a new question, `t10_claim_supported`, worded with the S232 policy. It starts in shadow and is enforced only once calibration supports it.
   - `a1_claim_supported` cannot be reused. Its policy conflicts with S232 on both sides. Its enforce mode and 0.85 floor are stored once per question key, so it cannot run in shadow at T10.
   - Jev cannot replace F9: it cannot list claims, only the 4 test tenants may use it, and it has no calibrated reject side.
   - Cost is about $0.0008 or less per piece and about 0.5 s per attempt.
   - No existing T10 question can help F9. `t10_cta_clear` carries no signal (AUC 0.53) and should be switched off.
6. **The way we measure has to change.**
   - All 6 rounds today (9/30 approved, 95% CI 17–48%) are consistent with one unchanged rate.
   - Judge changes should be tested offline on frozen texts.
   - End-to-end changes need n=20 per checkpoint and n=40 to close AA-768.

## A. F9 judge precision

### A1. Precision by category (127 flagged sentences, 3-labeler majority, 25 disputed)

| Category | Flags | Real | Borderline | Over-strict | Precision (real / real + borderline) |
|---|---|---|---|---|---|
| scene_detail | 22 | 21 | 1 | 0 | 95% / 100% |
| contrast | 20 | 13 | 7 | 0 | 65% / 100% |
| trip_promise | 10 | 6 | 4 | 0 | 60% / 100% |
| other_fact | 7 | 4 | 3 | 0 | 57% / 100% |
| number | 3 | 2 | 1 | 0 | — |
| location | 2 | 2 | 0 | 0 | — |
| **Violation categories** | **64** | **48** | **16** | **0** | **75% / 100%** |
| place_background | 31 | 0 | 6 | 25 | 0% / 19% |
| paraphrase_supported | 15 | 0 | 1 | 14 | 0% / 7% |
| opinion_rhetoric | 6 | 0 | 3 | 3 | — |
| brand_self | 6 | 0 | 2 | 4 | — |
| **Exempt categories (the prompt already says never flag these)** | **58** | **0** | **12** | **46** | **0% / 21%** |
| hypothetical (not yet decided in the policy) | 5 | 0 | 5 | 0 | — |
| **Total** | **127** | **48** | **33** | **46** | **38% / 64%** |

The judge looks at the right kinds of sentences, but it applies the policy wrongly. It treats "not in the SOURCE" literally, even for the categories that `services/acp_content_writing/quality_gates.py:622–652` explicitly exempts. This is a structural problem: the fix is to make the judge put a category on each claim and apply the policy in code. Better prompt wording alone will not fix it.

### A2. Adding the policy to the judge prompt did not reduce over-flagging

| Rounds | Judge prompt | Flags | Real | Borderline | Over-strict |
|---|---|---|---|---|---|
| R1 (10:08) | before #671 | 17 | 10 (59%) | 2 (12%) | 5 (29%) |
| R2–R5 (10:35–11:17) | #671 and later (background allowed, scene detail forbidden) | 110 | 38 (35%) | 31 (28%) | 41 (37%) |

- #671 put the same background rule into both the writer prompt and the judge prompt. The writer started using place background; the judge kept flagging it. 28 of the 31 place-background flags come after #671.
- R2 may have started before #671 finished deploying. R3–R5 on their own give 32% real and 40% over-strict.

### A3. Effect at the piece level

F9_cta_fact failed on the final attempt of all 21 pieces held since 09:53.

For the counterfactual, I re-judged each R1–R5 final text with a policy-perfect judge, using the labels as ground truth:

| | Pieces | Approved now | With a perfect F9 on the final text | Still held by at least one real violation |
|---|---|---|---|---|
| LinkedIn | 15 | 6 | 10–11 | 4, each with exactly 1 real violation |
| Blog | 10 | 2 (1 of them cut off mid-text) | 2 | 7 (mean about 2.1 real violations; 5 of them also fail F3/F5), plus 1 "judge unavailable" from before #672 |
| Total | 25 | 8 (32%) | 12–13 (48–52%) | 11 |

**Pieces that flip to approved:**
- a4b4b4a6, 681fec6e and 1eb35ee7 have only over-strict flags.
- e2484582 has an over-strict fact flag plus a CTA flag. The CTA flag is wrong: the piece ends with the CTA lightly reworded ("…plan this trip for you").
- 7020f334 flips too if hypothetical scenes are allowed.

**LinkedIn pieces still held by a real violation:**
- dd0cca4f: places the monastery in Ladakh.
- dbc1f592: contrast claim "not by a religious order".
- ba26f8db: "worn thresholds".
- 32accbfd: "the monastery stays out of sight".

**Where the labels come from.**
- Of the 53 sentences flagged on final attempts, 26 have majority labels. I labeled the other 27 myself in a single pass under the same policy.
- My split was 11 real / 9 over-strict / 7 borderline. The majority's split on the pool I covered was 35% / 45% / 19%, so my labels are slightly stricter.
- The labelers saw the seed and the AUDIENCE line. The judge also saw the Facts block and the BRAND and TRIP lines. Claims about visas or trip names (for example #49 and #114) need a recheck before they are used as calibration truth.

### A4. What this means

- Fixing F9 precision is necessary but not sufficient. It gains about 4 LinkedIn pieces in 15. The rest has to come from:
  - fewer real violations (section D);
  - a repair loop that can fix the 1–2 violations that remain: sentence repair for blogs, plus a cheap third attempt.
- Approving more pieces makes judge misses more costly. Recall has not been measured, because the labels only cover flagged sentences. E4 adds an audit of approved pieces.
- **Correction to the scoreboard.** The 2 rounds after #673 (R4–R5) give 3/10 approved and 3/10 passing F1+F9, not 4/10 and 6/10.
  - `held_reason` only names the first blocking gate.
  - F3 and F5 run before F9 (`quality_gates.py:928–938`).
  - So 3 blog holds that were put down to F3/F5 also failed F9.

## B. Gate-by-gate verdicts

| Stage / gate | Where | Evidence (today) | Verdict | Change |
|---|---|---|---|---|
| T7 Bar + `_choose` | `services/acp_shared/slate.py:66, :121, :339` | Works. `seen_places` is shared across channels (`:478`), so later Segment channels get starved. | Keep | Make `seen_places` per channel before G7, if FB/IG/TikTok are in scope. |
| T7 Debate | `services/acp_shared/debate.py:187–194` | 82–90% of candidates flagged. `t7_topic_fits_brand` was grey 272/272 times, so Luna runs on every miss. | Change | Calibrate from labeled slates before G7. |
| T8 angles | `services/acp_angle_gate/service.py:89–92`, `services/acp_angle_gate/prompts.py:44–55` | The seed has been `atom_seed_text` since #669, so the gate map's "short label" note is out of date. But `best_final_style` still asks for sensory scenes and comparisons. The 5 measurement requests reuse angles from before #669. | Change | Add a style fidelity rule and regenerate the angles (D2). |
| T8 ranking | `services/acp_angle_gate/ranking.py:79, :118` | Deterministic, plus Jev in shadow. | Keep | — |
| T9 pre-flight | `services/acp_content_writing/service.py:245` | The CTA check returns 422 here, so F6 can never fail later. | Keep | Use a brand-default CTA (AA-668). |
| T9 facts | `services/acp_content_writing/facts.py:77` | Shadow, 15 asks. | Keep | — |
| T9 seed siblings | `services/acp_shared/atom_seed.py:19, :31–39, :68, :78` | Takes the first 4 of up to 20 Segment siblings in alphabetical order, from any place. Pawangka's 4 siblings are Alchi and Dat (Ladakh) and Gandan and Erdene Zuu (Mongolia). Ta Dzong's include a Seoul city tour. Traced violations: #0 and #3 (Ladakh), #10 ("gravel" from Vang Vieng). | Change | Same-place siblings only, labeled as other departures (D3). |
| T9 write | `services/acp_content_writing/generate.py:41` (2048); calls at `:152, :208, :242` | 20/37 blog calls stopped at `max_tokens`. 5/20 final blogs end mid-text, including b533c076, which was approved. json-repair silently salvages the cut-off envelope (`:45–70`). LinkedIn 0/55. | Change | Per-channel token cap, a `stop_reason` guard, and a complete-ending check (D1). |
| T9 SEO fit | `services/acp_content_writing/service.py:209` | F4_seo fails on 0/10 final blogs since #670. | Keep | Publish the fields (see T11 publish row). |
| T9 attempt 2 | `services/acp_content_writing/service.py:565–592`, `services/acp_content_writing/sentence_repair.py:57` | Sentence repair ran 5 times, LinkedIn only. Blogs got 17/17 full rewrites because F3/F5/F7 also failed. A repaired piece is re-judged in full, and the repair's own paraphrase gets flagged (#76, "ordered built"). | Change | Repair only real claims that carry a category. Make blogs eligible. On a repaired attempt, judge only the repaired sentences (C3). |
| T9 regression guard | `services/acp_content_writing/service.py:664–712` | Reverted 8 full rewrites. | Keep | — |
| T9 hold | `services/acp_content_writing/service.py:715–723`, `:1190`, `:1223`; `api/routers/v1_publish.py:281–284` | A held piece can never be published. The 422 says "edit it in My Content first", but an edit never re-runs the gates or changes the status, and there is no admin clear. The portal shows held as "ready". | Change | An edit triggers a re-check (G5; AA-668). |
| T9 buffer retry | `services/acp_content_writing/service.py:830–960` | Never fires on reruns. Skips F10, the embedding, Jev, sentence repair and the regression guard. Logged as attempt 1. Can leave a row stuck in `processing`. | Replace | In-loop attempt 3 as sentence repair; then delete (G4). |
| T10 Jev observer | `services/acp_content_writing/jev_observe.py:81` | 633 calls, $0.035, all grey. | Change | Switch `t10_cta_clear` off; add the claim check (C). |
| F6 cta_present | `services/acp_content_writing/quality_gates.py:223` | Can never fail today. | Keep | It becomes live once the CTA comes from brand defaults. |
| F1 grounding | `:237` | 0/25 final attempts since 10:08; 9 failed attempts today. | Keep | Add a Jev clear for unit conversions and sums (C). |
| F2, F10, promises_an_option | `:260`, `:277`, `:321` | 0 failures. | Keep | F10: fix the buffer retry's missing embedding. promises_an_option: scan the seed only, not the Facts (AA-765). |
| F4 length | `:432` (bands at `:417–419`) | 0 failures. The 13,000-char ceiling cannot be reached at 2,048 tokens, and cut-off bodies pass. | Change | Add a complete-ending sub-check (blocking, repairable). |
| F4_seo | `:453` | 0/10 final since #670. | Keep | — |
| F5 atom density | `:735` | 1/10 final blogs since 10:08; 5/37 attempts. Conflicts with the untagged background that AA-768 now allows. | Downgrade to warn | Decision G1 |
| F3 structural variance | `:765–822` | 4/10 final blogs since 10:08 (10/20 today). 20 of 22 violations come from the Segment rule, which measures something different from what the writer is told (see below). The one-sentence check misses one-liners that carry a tag, because the tag follows the period. Forces full rewrites. | Downgrade to warn and fix the measurement | Decision G1 |
| F7 FAQ dedup | `:832` | 0/20 final, but 6/37 attempts, and each one forced a full rewrite. | Keep, and make it fix itself | Drop the restating Q/A pair deterministically, with no LLM call. |
| F8 framework (warn) | `:530`, `:937`; `services/acp_content_writing/framework_rubrics.py:48` | 7 final blogs failed "CTA: ends with a soft … next step". 6 of them end with a FAQ, which the format requires (`services/acp_content_writing/prompts.py:44–47`), and 4 were cut off. Judge calls hit the 2,048-token default 5 times today. | Keep as warn | Let the CTA close the body before the FAQ. Raise the cap. Later, swap in `t10_rubric_met`. |
| F9 FACT half | `:584–732` | 38% precision; the errors are in exempt categories (A). | Change | Category on each claim, policy applied in code, Jev overrule (C). |
| F9 CTA half | same | 8 CTA_NOT_REFLECTED attempts. e2484582 was wrong (CTA present, reworded). e7b0d794 was right (cut off, no CTA). | Replace | Deterministic CTA-presence check (token overlap of 0.8 or more with the required CTA, inside the body). |
| F9_brand_style (warn) | same | 8/29 LinkedIn final. | Keep | — |
| T11 publish | `api/routers/v1_publish.py:63, :224` | Only blog and facebook can publish, so LinkedIn cannot. WordPress gets `seo_title` = the angle name and `seo_meta=""`. | Change (AA-765) | Publish T9's SEO fields; channel decision G6. |

How the F3 Segment rule differs from the writer instruction:

| | What it measures |
|---|---|
| Gate | Sums the words per Segment, keyed by the first tag in each section, with FAQ and intro sections included. Requires the top Segment to be at least 1.4× the runner-up. |
| Writer instruction | Make the richest section at least 1.5× any other section. |

## C. Jev integration design

### C1. Where Jev fits

| Option | Verdict | Why |
|---|---|---|
| Pre-filter (ask Jev about every sentence first) | No | Jev answers questions about a state; it cannot list claims. A blog has 60–90 sentences, about 66% of answers land grey (A1 live rate), and there is no calibrated reject side (A1 reject precision on non-numeric sentences is 90.5%, below 95%). |
| **Second opinion on the sentences F9 flags, plus F1 hits** | **Yes** | F9 already returns `unsupported_claims[{sentence, claim, why}]`. Jev re-rules each flagged sentence. A confident "allowed" drops the claim; Jev never adds one. This is the same pattern as `t3_jev_clear` (`services/acp_produce/tenant_pipeline.py:105–135`). Verdicts are cached per (source, sentence) for 180 days, so they stay stable across attempts and reruns. |
| Replace F9's fact half | No | It cannot list claims. `decide()` skips any tenant not in `shared.jev_tenant_allowlist`, which holds 4 test tenants while DPA/ZDR is pending. There is no reject floor. |

### C2. The question

**`t10_claim_supported`.** Kind Noul, stage `t10_gates`, mode `shadow`. Added by migration 220, following the shape of `api/migrations/194_t10_jev_questions.sql`.

- **Instructions:** "A travel brand wrote marketing copy from the SOURCE. Is everything this sentence asserts allowed by the SOURCE?"
- **True when the sentence is only made of:**
  - things stated or clearly implied by the SOURCE, in any words ("built by X" covers "X had it built");
  - widely known background about a place the SOURCE names (what it is, its history, its founder, its religious or cultural role, whether it is still in use), as long as nothing contradicts the SOURCE;
  - opinion, mood, the brand describing itself, or the CTA.
- **False when the sentence contains any of:**
  - a promise about this trip that the SOURCE does not state: activity, food, service, guide, transport or travel time, clock time, view or wildlife, accommodation, inclusion;
  - invented scene detail: how the place looks, sounds or smells, its paths, steps or roads, how it is reached, crowds, what most visitors do;
  - a town, region or country other than the SOURCE's Location;
  - a comparison the SOURCE does not make ("not X but Y", "unlike most", "older than");
  - a number that is not in the SOURCE.
- **Hypothetical scenes:** set by decision G2.
- **State:** `{source: _grounding_text(context)` (`services/acp_content_writing/service.py:191`)`, sentence: the flagged sentence with tags stripped}`. The subject key comes from `subject_key(source, sentence)` in `services/content_generation/grounding.py`.

**Why not reuse `a1_claim_supported`:**
- Its criteria conflict with S232 on both sides:
  - "mood/colour about something the source names" counts as supported, so it would clear scene violations such as worn steps;
  - "unsourced history" counts as unsupported, so it would keep the place-background flags.
- `decide.py:199–216` loads the mode and floors keyed by `question_key` only. Calling it at T10 would therefore act at its A1 enforce/0.85 setting from day one.
- Use it only as a comparison column in the offline replay.

### C3. Where it runs in each attempt

1. **`run_quality_gates`, order unchanged.**
   - F9 v2 returns a `category` for each claim.
   - Code drops the exempt categories before deciding FACT_CHECK: place background, paraphrase, opinion, brand self, and hypothetical if G2 allows it.
   - This extends round 4 at `quality_gates.py:675–684`.
2. **After a sentence repair: judge only the repaired sentences.**
   - Keep only the F9 claims whose sentence overlaps a repaired span; `sentence_repair.locate_sentence` finds the spans. The judge passed the other sentences on the previous attempt.
   - Log the dropped claims as `unchanged_sentence`.
   - Trade-off: a real violation the earlier judge missed stays missed. That is the same outcome as if the earlier attempt had passed.
3. **New async `claim_check`.**
   - Place it after `run_quality_gates` (`service.py:618–626`) and before `observe_t10` (`:629`).
   - It makes one `decide()` call per remaining flagged sentence and per F1 hit, 4 at a time.
   - When `accepted()` is true, the claim is dropped and recorded in that gate's ledger entry as `cleared_by_jev` with its p.
4. **Recompute `passed` and `first_failure`**, then hold or repair as today.

If Jev fails, the claim is kept, so a failure can only add holds, never remove them. For tenants not on the allow-list, Jev returns `skipped` and step 3 does nothing.

### C4. Mode and thresholds

| Phase | Setting | What happens |
|---|---|---|
| Live shadow | mode `shadow`, floors NULL | No outcome changes. The would-be effect is computed from `decision_log` by re-applying candidate floors, because floors are applied when the log is read. |
| Offline replay (E2) | Candidate floors 0.85 (the A1 v2 floor) and 0.90 | Pick the lowest floor that meets C7. |
| Enforce | `PUT /admin/decisions/questions/t10_claim_supported` (`api/routers/admin_decisions.py:395`) with the floor and `calibration_ref docs/calibration/t10_claim_supported.md` | No deploy needed. |
| Reject side | No reject ceiling | Jev never adds a violation. |

Expected yield: A1 v2 cleared 52% of the supported sentences at 0.85. Expect about half of the over-strict flags that survive step 1 to be cleared, mostly the 15 paraphrase cases. Place background is handled by step 1 even if Jev stays grey on it.

### C5. Cost and latency

- Each ask uses 0.5–1.8k input tokens at $0.042 per million (output is free), so about $0.00002–0.00008. Today's T3 average was $0.000081.
- F9 flags about 3.4 sentences per failing attempt (129 across 38 failing ledgers). That gives up to about 10 asks per piece, so $0.0008 or less per piece. That is under 1% of a blog's $0.097 and about 3% of a LinkedIn piece's $0.02–0.028.
- Latency: p50 is 110–180 ms with 4 asks at a time, so about 0.3–0.5 s per attempt, against jobs of 39–92 s.
- Sentences that do not change across reruns cost nothing (cache hit).

### C6. Code changes, by file

- **Migration:** `api/migrations/220_t10_claim_supported.sql`, plus an identical `infra/AA-CIS-Infra/db/migrations/cis/220_t10_claim_supported.sql` applied through the DB Migrate workflow.
- **`services/acp_content_writing/claim_check.py` (new):** splits F9 claims and F1 hits into kept and cleared, in the style of `t3_jev_clear`.
- **`services/acp_content_writing/quality_gates.py`:**
  - F9 contract gains `category`; the F9 result carries structured claims; exempt-category filter.
  - An optional `stage` argument, so replays log under `adhoc_aa701`.
  - Deterministic CTA check and complete-ending sub-check.
  - F3/F5 wrapped in `_downgrade_to_warn` (`:212`, applied around `:928–931`), per G1.
  - F3 measurement fix and F7 self-repair.
- **`services/acp_content_writing/service.py`:**
  - `claim_check` and the outcome recompute after `:626`.
  - The "judge only repaired sentences" filter after the sentence-repair branch (`:565–582`).
  - Attempt 3 and removal of the buffer retry, per G4.
- **`services/acp_content_writing/sentence_repair.py`:** read the structured claims instead of regex-parsing violation strings (`:22–24`, `:57–85`).
- **`t10_cta_clear`:** switch it off with an admin PUT (no deploy). Remove the ask in AA-765.
- **Docs and tests:** `docs/calibration/t10_claim_supported.md` plus its data file. Tests for the category filter, the repaired-sentence filter, `claim_check` with a fake `decide()`, the CTA check and the ending check. Update `docs/implementation-notes/AA-701.md` and `docs/implementation-notes/AA-768.md`.

### C7. Switching from shadow to enforce (all 4 required)

1. **Offline,** on the 127 labeled sentences (rechecked for Facts) at the chosen floor:
   - 5% or fewer of the cleared sentences are real violations;
   - at least 15 sentences are cleared;
   - no trip-promise, location or number violation is cleared.
2. **Live shadow,** in the n=40 run:
   - every would-be clear is reviewed by the 3 labelers, with a spot check by Nghiệp;
   - at most 1 wrong clear across at least 40 flagged sentences.
3. **Jev health:**
   - errors stay under 2% for allow-listed tenants;
   - the credit breaker does not trip. A1 logged 11,000 credit errors in 14 days, so check `/admin/decisions/jev-credit` before the run.
4. **Recording:** stamp the labels as outcomes with `record_outcome` (`decide.py:471`). `GET /admin/decisions/outcomes/summary` (`admin_decisions.py:297`) then keeps reporting precision after enforcement.

If no floor meets point 1, do not enforce. Instead, split the question into "stated in other words?" and "only background about a named place?", then re-run E2 (about $0.02).

### C8. Existing T-series Jev questions

| Question | Evidence | Verdict |
|---|---|---|
| `t10_cta_clear` | AUC 0.53. All 88 attempts scored p ≥ 0.8, including 0.96 on e7b0d794, which has no CTA because it was cut off. | Switch off. Replace with the deterministic CTA check. |
| `t10_rubric_met` | AUC 0.73 against F8; 77% agreement at 0.7. | Keep in shadow. Calibrate from G7 labels; it is the candidate to replace the F8 Luna call. |
| `t10_faq_restates` | AUC 0.72; all 6 F7 failures had p ≥ 0.86. | Keep in shadow until there are at least 20 F7 failures. |
| `t10_brand_voice` | AUC 0.60; p ranges 0.33–0.86. | Keep in shadow, low priority (the gate is a warn). |
| `t10_offer_as_certain`, `t10_same_piece` | Never asked. | No data; revisit in G7. |
| `t7_topic_fits_brand` | 272 asks, all grey, while Debate cuts 82–90%. | Calibrate from labeled slates before G7. |
| `t8_angle_answers`, `t9_fact_relevant` | 7 and 15 asks, all grey. | Leave in shadow. |

## D. Remaining writer-side changes

### D1. Blog token budget and cut-off output (mechanical, do first)

- In `generate.py:41`, set the cap per channel: blog 8,000, others stay at 2,048. The blog spec is 2,200 words, about 3,000 tokens, plus 25–35 citation tags, the JSON envelope and the summary.
- When `stop_reason == "max_tokens"`, count the attempt as failed instead of salvaging the cut-off JSON (`generate.py:45–70`). Add the complete-ending check.
- **Cost:** about +$0.015 per capped blog call (today a blog call costs about $0.039 at up to 2,048 output tokens), plus 15–25 s per blog attempt.
- **Removes:**
  - 4 of the 7 F8 blog CTA-item failures;
  - the CTA miss on e7b0d794;
  - approved pieces that end mid-text.

### D2. Angles must not ask for what the seed lacks (biggest lever on real violations)

At least 10 of the 48 majority-labeled real violations map directly onto an instruction in the chosen angle's `best_final_style`:

| Request | Angle instruction | Violations it produced |
|---|---|---|
| terra-family blog | "the guide unrolling a map" | #22; the same map appears again in #113 and #116 two rounds later |
| atlas-hearth blog | "one precise, unexpected detail … why Bhutan is one of the only places…" | #26 (contrast), #29 (silk detail) |
| atlas-hearth LinkedIn | "single specific sensory or physical detail…", "Refuses to Be Found Easily" | #1 (stone steps), #4, #36 ("most visitors") |
| terra-family LinkedIn | "sound of prayer wheels, smell of incense…", "…That Classrooms Can't" | #51 (worn thresholds), #52 ("older than…") |
| trail-pulse LinkedIn | "drop the reader onto the trail…", "The Climb That Earns the View" | #54 (pine forest), #56 (carved into the cliff) |

Changes:
- `services/acp_angle_gate/prompts.py:44–55`: `best_final_style` may only name details that are in the seed, with no sensory, scene or comparison asks.
- `services/acp_content_writing/prompts.py:147–149`: add "SOURCE FIDELITY overrides the angle: if the angle asks for a detail the seed lacks, use the seed's own detail or place background."
- Regenerate the angles of the measurement requests (5 × about $0.02). They were generated in the S231 pilot from the 26-character atom label, before #669.

### D3. Siblings from the same place only

- Filter `_SIBLING_EVIDENCE_QUERY` (`atom_seed.py:31–39`) to siblings whose `place` matches the atom's place; drop the rest.
- Replace the alphabetical pick (`:78`); today it favors sentences that start with "A".
- Label the block (`:68`): "Same place on other departures — background, not promises for this trip". The judge's SOURCE should show the same label.
- Evidence: #0 and #3 ("Ladakh" taken from the Alchi sibling) and #10 ("gravel" taken from a Vang Vieng sibling).
- Run a one-off SQL check: the share of sibling lines whose place differs from the atom's place.

### D4. Examples in the prompts, not more rules

- The contrast ban added in #672 did not stop contrast claims in R4–R5. Examples are #57, #93, #95, #96, #100 and #103; these are my single-pass labels.
- Add 4 bad-to-good pairs from the labeled set to SOURCE FIDELITY (`services/acp_content_writing/prompts.py:150–175`): worn steps; "not by a religious order but by a king"; "older than most cathedrals"; "most travellers never…".
- In the repair prompt (`generate.py:219–225`), say "when restating a SOURCE fact, keep the SOURCE's own words". #76, "ordered built", came from a repair and was then flagged.

### D5. Let blogs reach sentence repair

- This needs F3/F5 to become warns (G1) and F7 to fix itself.
- A blog with 1–3 real violations is then fixed in place instead of rewritten. Today it is 17/17 full rewrites, and the regression guard reverted 8 of them.

### D6. Attempt 3, sentence repair only (decision G4)

- Every LinkedIn piece that would still be held has exactly 1 real violation left on its final attempt.
- An attempt-3 repair costs under $0.01 and about 20 s per held piece. It replaces the buffer retry, and it is never a third full rewrite.

## E. Measurement plan

**Today's rounds:**

| Round | Latest merge before the round (deploy lags 5–10 min) | Approved | Blog | LinkedIn |
|---|---|---|---|---|
| R0 09:53 | #669 | 1/5 | 0/2 | 1/3 |
| R1 10:08 | #670 | 1/5 | 1/2 (cut off) | 0/3 |
| R2 10:35 | #671 | 3/5 | 1/2 | 2/3 |
| R3 10:52 | #672 | 1/5 | 0/2 | 1/3 |
| R4 11:11 | #673 | 1/5 | 0/2 | 1/3 |
| R5 11:17 | #673 | 2/5 | 0/2 | 2/3 |
| **Total** | | **9/30 (30%, 95% CI 17–48%)** | 2/12 | 7/18 |

At p ≈ 0.3, a single round of 5 lands between 1/5 and 3/5 about 80% of the time. That is exactly the 1, 1, 3, 1, 1, 2 we saw. **Do not compare rounds of 5.**

**E0. Scoreboard.**
- Build it from the final `gate_ledger` and `llm_call_log`, never from `held_reason`.
- Report: approved, F1+F9 pass, per-gate fail rate per channel, cut-off pieces (`stop_reason`), claims per attempt by category, and Jev would-be clears.
- Give a Wilson 95% CI for every rate.

**E1. Judge replay (offline, frozen text — removes writer variance).**
- Texts: every attempt of the 25 R1–R5 pieces (about 50), with the source rebuilt through `_grounding_text`.
- Runs: current F9 × 3 and F9 v2 × 3, stage `adhoc_aa701`.
- v2 passes if:
  - it keeps at least 90% of the real violations that the current F9 re-flags in the same repeats;
  - it flags at most 10% of the 46 over-strict sentences;
  - test-retest agreement on the piece-level FACT verdict is at least 85%.
- New sentences v2 flags get labeled before deciding.
- About 300 judge calls: about $0.7 at logged prices. Budget up to $3, because F9 input tokens look under-logged (average 2 per call).

**E2. Jev replay.**
- 127 sentences × {`t10_claim_supported`, `a1_claim_supported`}, about 254 asks, about $0.02, run with each piece's allow-listed tenant.
- Choose the floor by C7.

**E3. Live checkpoints.**
- **Request set:** 10 requests.
  - The 5 pilot requests, with regenerated angles.
  - 5 new ones: include wildkind-travel, both channels, a route blog, a family tour and a wildlife tour, and Facebook if G6 picks it.
- **Checkpoint A** (after the S233 PRs): n=20, about $1.5.
  - The baseline after #671 is 7/20 (35%).
  - 12/20 or more shows a real gain (one-sided p ≈ 0.02; about 89% power if the true rate is 70%).
  - 14/20 or more is on track for the target.
- **Close run** (with Jev in shadow, then the enforce decision): n=40, about $3.
- **AA-768 closes when all of these hold:**
  - at least 30/40 approved;
  - at least 14/20 per channel;
  - no cut-off pieces;
  - E4 passes.
- What this rule means:

| True approval rate | Chance of reaching 30/40 or more |
|---|---|
| 80% | about 0.84 |
| 65% | about 0.12 |

**E4. Recall audit.**
- Label every checkable sentence of 10 approved pieces from the close run (5 blog, 5 LinkedIn, about 400 sentences) with the 3-labeler workflow.
- It passes if there is no trip-promise, location or number violation, and at most 2 other real violations across the 10 pieces.

**E5. Statistics rules.**
- Compare arms on the same requests (McNemar).
- Judge judge changes at the claim level (more than 100 claims per run).
- Always report per channel.

**Budget before G7:** up to about $8 in total. Check Jev credit first.

## F. Prioritized T-axis plan

| # | Item | Issue | Depends on | Paid | When |
|---|---|---|---|---|---|
| 1 | Per-channel token cap, `stop_reason` guard, complete-ending check | AA-768 | — | — | S233 |
| 2 | Same-place siblings, T8 style fidelity rule, regenerate measurement angles | AA-768 | — | ~$0.2 | S233 |
| 3 | F9 v2: categories, policy applied in code, judge-only-repaired-sentences filter, deterministic CTA check | AA-701 / AA-768 | E1 | ≤ $3 | S233 |
| 4 | Apply G1 (F3/F5); F3 measurement fix; F7 self-repair; F8 FAQ/CTA rubric fix | AA-768 | G1 | — | S233 |
| 5 | Checkpoint A, n=20 | AA-768 | 1–4 | ~$1.5 | S233 |
| 6 | Migration 220, `claim_check` in shadow, F1 Jev clear, `t10_cta_clear` off | AA-701 | 3, E2 | ~$0.02 | S234 |
| 7 | Attempt-3 sentence repair; remove the buffer retry | AA-768 | G4 | — | S234 |
| 8 | Close run n=40 + E4 audit; enforce Jev if C7 is met; close AA-768 | AA-768 / AA-701 | 5–7 | ~$3 | S234 |
| 9 | Close AA-763 at the next natural S1 job | AA-763 | an S1 job | — | any |
| 10 | Debate calibration: 1 labeled slate per tenant, set the `t7_topic_fits_brand` floors | AA-696 or new issue (G7) | G7 | ~$0 | S235 |
| 11 | G7 prep: choose 12 tours; DE/FR/NL `segment_research` estimate, then Nghiệp triggers it ($5 cap); Jev credit; per-channel `seen_places` | AA-741 | 10 | ≤ $5 | S235 |
| 12 | G7 48-run with the label sheet, plus the AA-699 live check inside it | AA-741 / AA-699 | 8, 10, 11 | ≈ $24 | S236 |
| 13 | G8 report + portal UI/UX walk; follow-up issues after approval; close AA-741 | AA-741 | 12 | — | S237 |
| 14 | AA-765 (G6): one judge client; T11 dispatch into `acp_publish` including T9's SEO fields; LinkedIn adapter per G6; stale comments | AA-765 | 8 | — | after S234 |
| 15 | AA-766 (G9) Tenant 360: Cost and Markets tabs; Quality tab after G7 | AA-766 | cost-logging fixes; 12 for Quality | — | parallel from S235 |
| 16 | Portal chain: G10 AA-759 → G11 AA-760 → G12 AA-668 → G13 AA-761 → G14 AA-671 | AA-759 → AA-671 | G8's UI list | — | after S237 |
| 17 | G15: AA-762 + AA-703 (identity ADR, SES, build vs buy) | AA-762 / AA-703 | ADR | — | after G13 |
| 18 | Later: AA-729 golden set, AA-628 engagement loop, AA-704 | — | G7 labels; live T11 | — | later |

Notes on the plan:
- **G7 (item 12)** cost ≈ 48 T2 jobs × $0.37 + one blog and one LinkedIn piece per combination (≈ $5.6).
- **AA-766 (item 15):** the Cost tab needs 2 fixes first:
  - `shared.job.cost_usd` is 0 for every job;
  - F9 input tokens are under-logged (average 2 per call).
- **AA-668 (item 16, G12):** writer panel, brand-default CTA, job-based status, and the re-check of held pieces after an edit.
- **Stale comments for AA-765 (item 14):** `generate.py:36–40` mentions 4096 while the code is 2048. `tenant_pipeline.py:97` says 0.90 while the live floor is 0.85.
- **AA-703 identity ADR (item 17):** it goes in `AA-Ecosys/docs/adr/` because it spans 2 or more repos.
- **Corrections to the backlog:**
  - The T9 cap is 2,048, not 4,096. It is not a small cost item; it is what cuts off blogs.
  - T8 has used the full seed since #669.

## G. Decisions needed from the product owner

1. **F3 and F5 on blogs: warn or block?** I recommend warn. They are style heuristics; they block 4 of 10 final blogs and force full rewrites that invent new facts. F1 and F9 own fidelity.
2. **Policy edge cases:**
   - (a) Hypothetical or second-person scenes ("A child stands at the entrance… and takes it in"). I recommend allowing them only when they add no concrete scene detail.
   - (b) Country-level background (Bhutan's dress code, its tourism policy, visas). I recommend treating it like place background as long as it contains no number and makes no claim about this trip.
   - Together, these settle about 11–14 of the 33 borderline labels.
3. **Approve the F9 v2 + Jev path:**
   - judge replay (up to $3) and Jev replay (about $0.02) now;
   - Jev enforcement on the 4 allow-listed tenants only after C7 is met;
   - the new AA-768 done-when in E3.
   - Real tenants stay on the LLM-only path until DPA/ZDR clearance lets them onto the Jev allow-list. Is that clearance on the roadmap?
4. **Replace the AA-485 buffer retry with an in-loop attempt 3 that is sentence repair only?** It costs under $0.01 and about 20 s per held piece, and changes the 2-attempt cap.
5. **Held pieces before any real tenant:** should a tenant edit trigger an automatic re-check (recommended), and/or should there be an admin "release with note"?
6. **First live social channel:** LinkedIn, which we are tuning but `v1_publish.py:63` cannot publish, or Facebook, which can publish but has not been measured in T9?
7. **Housekeeping:** where Debate calibration is tracked (a new issue or a comment on AA-696), the G7 tour list, and the DE/FR/NL DFS run (estimate first, $5 cap).