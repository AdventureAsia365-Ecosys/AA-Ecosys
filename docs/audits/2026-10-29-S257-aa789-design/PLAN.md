# AA-789 final plan: close the T10 recall gap for the 11 missed classes

Status: plan (S257, 29/10/2026). No code written, no paid call made.
Inputs: `design-A-nlp.md`, `design-B-llm.md`, `design-C-hybrid.md`, the eval set in `eval/` (405 items: 149 defect,
246 clean, 10 contested), two judge panels (both picked A as the base, with grafts from B and C), root
`docs/generated/llm-routes.md` (29/10 snapshot).
Direction from the tech lead (S257): keep AA-789 open and solve it fully; look for more solutions, not only gates.

---

## 0. Decision in one paragraph

Build a **three-tier stack** in which only the deterministic tier can ever hold a piece.

- **Tier 0, prevention ($0 code):** stop the writer from producing the two leak classes at all. Render the seed's
  `Naming:` note as a one-line "use this name" instruction instead of explanatory prose, and remove copyable
  "one X, one Y, one Z" templates from the writer brief. This is the extra solution the S257 direction asked for: a leak
  that is never written needs no gate.
- **Tier 1, seed alignment (design A, $0 LLM):** spaCy dependency parse + a typed `SeedGraph` + a closed lexical
  trigger. A finding needs all three keys; any missing key means abstain. Findings go under the **existing** gate names
  (F17_trip_fact, F18_rarity, F13_leak, F13_repeat, FAQ step) with a `sa:<class>` prefix, never a new gate (S246 freeze).
  Each class has its own mode: `off / shadow / repair / hold`.
- **Tier 2, residual verifier (B + C, small paid LLM, later):** for the forms Tier 1 cannot reach (paraphrased naming
  notes and recipes, implicit-subject repeats, open WHAT/WHY/HOW FAQ answers, cleft "X is where you break for lunch",
  "hard to overstate", scoped-vs-scopeless superlatives). Candidates are Tier 1's triggered-but-abstained sentences plus
  a few broad patterns for these classes only. Verbatim anchors on both sides, fail open, sticky verdicts.
  **Tier 2 never holds.** Its strongest action is one sentence repair or cut.

Everything that can hold must first clear **0 false positives on the 246 clean eval items** (Wilson 95% upper bound
1.54%), then **≥ 50 labelled shadow fires with ≤ 1 false**, then fail one sentence repair before any hold.

---

## 1. Why this shape (judge synthesis)

| | A (deterministic NLP) | B (LLM claim verifier) | C (candidates + LLM adjudicator) |
|---|---|---|---|
| Judge totals | 8.0 / 36 (winner both panels) | 7.2 / 31 | 6.0 / 32 |
| Precision | Built in (three keys or abstain) | Error-injection floor, but confirmers = reverted regexes | ~1–2% clean blogs falsely held on its own priors |
| Recall | ~0.5 average, narrow literal forms | 0.5–0.9 priors, depends on ~100-claim extraction | Highest on paper (0.55–0.80 end recall) |
| Cost | $0 LLM (+$3.6/mo memory if needed) | ~$0.003/piece | ~$0.008–0.015/blog |
| Buildable and measurable now | **Yes, fully, for $0** | Module yes, model no (acc3 blocked) | Generator yes, adjudicator no |

What we take from each:

- **A:** the whole Tier 1, the severity ladder, the parse-stability abstain, determinism and version pins.
- **C:** routing under existing gate names (I6), the invariants as CI tests (I1 candidate tier cannot fail a gate, I2
  byte-identical ledger when off or erroring), the per-class mode enum, the deterministic pre-clear rules as extra
  abstain conditions, and the Writing memory feedback loop with an automatic per-class demotion.
- **B:** the error-injection eval (worst-case inputs on every clean sentence prove a floor), the verbatim-anchor rule,
  "never hold on not_in_source", repairs first, sticky `ClaimMemory`, and the same-seed-line pairing for repeats.

---

## 2. Coverage per missed class

"Max" is the strongest mode the class may ever reach. Recall figures are design priors (±20 points); Phase 0 replaces
them with measured numbers from `score.py`. Eval counts are defect / clean hard negatives (excluding contested).

| # | Class (eval key, n) | Tier 0 prevention | Tier 1 mechanism (deterministic) | Tier 1 max | Tier 2 residual (LLM) | Tier 2 max | Gate it lives under |
|---|---|---|---|---|---|---|---|
| 1 | 'by boat' optional activity told as planned (`optional_as_planned`, 13/25) | Seed already marks OFFERED; no change | Instrument noun of an optional activity of moment M (boat, horse, kayak, raft, bike, reindeer) as pobj of by/on/in, dobj of a ride verb or compound head; governing verb has a **traveller subject**, no modal, no negation, no hedge whose syntactic scope covers the instrument; instrument absent from M's planned lines and planned transport. **Not** the two-word `_mentions_activity` rule. A failed parse confirmer demotes to repair, never drops | **hold** (after G3; starts repair) | Passives and generic recommendations ("best seen by boat") that Tier 1 abstains on | repair | F17_trip_fact |
| 2 | Reverse flip: planned moment called optional (`planned_as_optional`, 12/18) | – | Hedge predicate ('optional', 'if you wish', 'on request', 'at extra cost') whose **target** NP (copula subject, gerund object, amod head) is a moment-level NP of planned M; a place in a locative modifier ("At the Tsaatan settlements, …") is not the target; target holds no lemma of M's optional sub-activities; negated hedge ("not an optional extra") is clean | **hold** (first wave) | Paraphrased hedges ("for those who want to") | repair | F17_trip_fact |
| 3 | 'Lunch/stop at X' when the seed says near X (`near_as_at`, 15/18) | – | Seed event (lunch, stop, break, overnight, camp…) with prep path → NEAR(event, X); copy event linked to X through at/in (own prep child or copula); not in a temporal prep ("After lunch, … the airport in Mörön"); alias-resolved; no seed AT for any event of the scope | **hold** (first wave) | Cleft forms ("Mörön is where you break for lunch") | repair | F17_trip_fact |
| 4 | 'Not a technical climb' difficulty promise (`difficulty_promise`, 14/18) | – | Ease lexicon or negated difficulty word predicated of an **activity noun** of M (polarity = reassurance); caveats ("strenuous in places") and equipment subjects ("no technical gear is needed") never fire; pre-clear when the seed has the stem; seed hazard raises the text to "contradicts" | repair | Judgement cases ("full without being relentless", "never rushed") | repair | F17_trip_fact |
| 5 | 'Significant share of the world' unsupported (`world_share_unsupported`, 11/16) | – | Proportion head + magnitude/number; `of → pobj → poss` chain reaches a global scope noun; the NP is an argument about a seed place; pre-clear when a seed figure backs it with the same scope (Baikal 20%); a wrong figure vs the seed ("two percent" vs 0.4%) fires | **hold** (first wave) | "Great reservoir of the planet" style forms with no proportion head | repair | F18_rarity |
| 6 | Scopeless superlative not in the source (`scopeless_superlative`, 22/15, 7 contested) | – | JJS/RBS or 'one of the most' on a class noun or seed entity; scope missing or global; evaluative adjective (practical list never fires: best time, nearest, easiest way); no seed superlative with the same lemma after a derivation map | repair, then warn (style-only, like F2) | "Hard to overstate", "few places can offer", scope-widening (Central Asia → Asia) | repair | F18_rarity |
| 7 | Brief 'one X, one Y, one Z' recipe leak (`brief_recipe_leak`, 13/15) | **Rewrite the thin-moment brief so it has no copyable template** (describe the intent, not the shape); also covers "A Single Sentence on…", audience range wording | Triad/pair of 'one N' that is a verbless fragment or appositive list, with ≥ 2 head lemmas that are recipe nouns of the actual brief/prompt text or meta nouns (fact, year, moment, detail) | repair (cut), never hold | Paraphrased recipes, angle and voice instruction echoes | repair (cut) | F13_leak (repair-first, see §3) |
| 8 | Naming-note leak (`naming_note_leak`, 11/17) | **Render `Naming:` as "Use the name Mörön (not Moron)." with no rationale text** in the seed builder, so the leakable words (phonetic approximation, connotation, international audiences) never reach the writer | Sentence names M or an alias **and** has ≥ 2 note-only lemmas (or 1 strong: romanise, transliterate, connotation, phonetic, spelling); abstain if those lemmas are also background facts ("also known as") | repair (cut), never hold | Paraphrased notes ("a name locals find unfortunate") | repair | F13_leak (repair-first) |
| 9 | Paraphrased repeat (`paraphrased_repeat`, 13/17) | – | Candidate pair = two body sentences **citing the same seed line or seed fact** (B), within the section or 6 sentences; key 2 local bge-small cosine ≥ τ (τ set so ≤ 1 clean pair per 2,000 passes); key 3 the later sentence adds no seed fact; pre-clear for parallel `## Day N` sections; replaces C's Jaccard | autofix-delete (existing dedupe guards) or warn, never hold | Implicit or generic subjects, hook restated in paragraph 1 | repair (cut) | F13_repeat |
| 10 | Orphan section opener (`orphan_opener`, 11/15) | – | First sentence of a section whose subject is a pronoun/demonstrative with no agreeing antecedent in the heading, **plus** (graft from B) a bare-NP opener whose head noun is absent from the heading and section but present in the previous section ("Access requires…"); definite bridging NPs ("The approach road") never fire | repair, never hold | Misplaced sentences, "What they find…" style openers | repair | F13_repeat |
| 11 | FAQ answer does not address its question (`faq_non_answer`, 14/18) | – | New `type_mismatch` reason: measurable question types only (yes/no, how-ADJ, when, where, who); answer's first two sentences match none of the expected forms; drop the pair above `FAQ_MIN_PAIRS`, else flag | drop, never hold | Open WHAT/WHY/HOW: the existing `faq_answer_fit` module, pre-filtered by Tier 1 so only unclassifiable pairs are sent; re-routed off Sonnet (§5) | drop | FAQ step (unchanged semantics) |

Classes 1–5 are fact defects (the panel's deciding defects); only 1, 2, 3 and 5 may reach hold. Classes 6–11 are style
or integrity defects: repair, cut or drop, then warn. This matches C's invariant I5 and keeps the hold surface small.

---

## 3. Safety rules (apply to every tier)

1. **Holds only from Tier 1, only for classes 1, 2, 3, 5, only in mode `hold`.** Tier 2 and Tier 0 cannot hold.
2. **Hold bar per class, in order:**
   - **G1 offline:** 0 false positives on the 246 clean eval items and 0 on the class's own hard negatives (`score.py`,
     Wilson bound reported); ≥ 1 true positive on each reachable panel example; error-injection pass (below).
   - **G2 shadow → repair:** ≥ 30 labelled fires, precision ≥ 0.95, no wrong-direction fire, still 0 on clean eval.
   - **G3 repair → hold:** ≥ 50 labelled fires cumulative with ≤ 1 false (point precision ≥ 0.98, Wilson lower bound
     reported), a second rater on the labels, repair-guard test green, and the date is after the S246 freeze (~18/11).
   - Below 50 fires a class stays in repair, whatever its point estimate. On Dev volume that may be months for rare
     classes; that is accepted.
3. **Repair before hold.** A hold-mode finding first gets one `t9_repair` sentence repair; the piece is held only if
   the repaired sentence still fails. `sa:`-prefixed findings under F13_leak follow this too (they never use F13_leak's
   direct no-repair hold).
4. **Abstain by construction.** Missing seed relation, unresolved alias, unstable parse (full vs split parse differ),
   sentence over 40 tokens without a stable split, heading/quote/CTA → no finding. Plus C's pre-clear rules (seed-backed
   figure, seed lexeme stem, same-clause hedge, cross-day-section pair).
5. **Error-injection eval (from B):** for hold-capable checks, perturb the inputs on every clean sentence (force the
   wrong PP attachment, drop an alias, swap the moment attribution) and assert the check abstains instead of firing.
   For Tier 2, a worst-case model row (VIOLATION, best-matching seed line) on every clean sentence must be rejected by
   the anchor checks or stay at repair.
6. **Invariants as CI tests (from C):** I1 `seed_align` and the Tier 2 candidate list cannot import gate result
   builders (import lint); I2 with every mode `off`, or Tier 2 erroring/unavailable, the gate ledger is byte-identical
   to `main` on the 40 stored pieces and all verifier clean sentences; repair-guard test (a repair cannot introduce a
   new `sa:` finding).
7. **Demotion is automatic, promotion is a PR.** Weekly job: any labelled wrong hold, or hold precision < 0.98 over
   the last 50 labelled fires, sets that class to `repair`. Promotion to `hold` is a small PR with the evidence table.
8. **Determinism:** pinned spaCy 3.8.x + `en_core_web_sm` wheel by hash, bge-small ONNX by SHA-256; `nlp_version` in
   the ledger so a replay reports version drift.
9. **No real copy in repos:** eval and labels stay in `.tmp-session`; repo fixtures are synthetic; replay prints
   kinds and counts only (CI golden-text guard).

---

## 4. Rollout with gates

| Phase | What | Cost | Exit gate |
|---|---|---|---|
| **P0 offline (next session)** | Install spaCy + bge in a `.tmp-session` venv. Run **main's baseline** over `eval_set.jsonl` (first row of the table). Build Tier 1 per class with an eval adapter that wraps `seed_excerpt` into the seed-builder labels; score each class with `score.py --strict-class`. Measure worker RSS and latency in a 0.5 vCPU / 1 GiB container. Second-rater pass (independent agent) on the eval labels of classes 1, 2, 3, 5; tech lead spot-checks 20 items | **$0** | G1 per class; RSS number decides the memory question |
| **P1 shadow on Dev** | Merge Tier 1 with all modes `shadow` (findings are flags only). Read-only replay of **every stored Dev `content_piece` and its discarded attempts** via ECS exec (container `DATABASE_URL`; count first). Two-agent label panel on every fire; tech lead spot-checks 20% | **$0** (running ECS/RDS only) | G2 per class |
| **P2 repair mode** | Classes past G2 go to `repair` (one cheap repair on attempt 1, never hold). Measure repair success on true positives: ≥ 90% fixed in one repair, 0 repairs that add a new F17/F18 finding | ~$0.0045 per repair, ≤ $0.50 per 100 findings. **Blocked today:** `t9_repair` runs on Haiku/Sonnet on acc3 | Repair success bar |
| **P3 Tier 2 shadow** | Fix the `t10_claims` route (both acc3 models blocked; add `gpt-6-luna-openai`). Calibrate on the eval set + 40-piece export, 3 repeats. Then shadow on stored pieces | P1-style calibration ≈ $1.5 (cap $3); shadow batch ≈ $1 (cap $2). Needs OpenAI credit or the acc3 unblock | Tier 2 per class: precision ≥ 0.90 on its candidates, ≥ 95% of VIOLATIONs pass quote checks, test-retest ≥ 0.90, worst-case rows never reach above repair |
| **P4 Tier 2 repair** | Tier 2 findings may trigger one repair or cut | ≈ $0.003–0.008 per blog, ≈ $0.001 per LinkedIn | Repair success ≥ 70%, AA-528 guard reverts ≤ 10% |
| **P5 hold (after ~18/11)** | One promotion PR per class past G3, order: 2 reverse flip, 3 near→at, 5 world share, then 1 'by boat' | $0 extra | G3; hold-rate jump > 2 points on the next T-round triggers review |

**Tier 0 prevention** ships in P1 (code is $0). Its effect is measured on the next paid T-round we choose to run, by
counting `sa:` class 7 and 8 fires before vs after (the detector is the measuring stick).

**"Done" for AA-789:** every class has a live mechanism at ≥ repair severity with its measured recall and precision
recorded; classes 1, 2, 3, 5 promoted to hold or explicitly kept at repair with the evidence; all known-miss tests in
`test_aa789_t10_recall.py` flipped to positives; weekly demotion job running; Tier 2 live in repair for the residual
forms (or the issue split, see decision D4).

---

## 5. Cost

| Item | Per piece | Dev per month (~100–350 pieces) | Early tenants (~3,000 pieces/month) |
|---|---|---|---|
| Tier 0 prevention | $0 | $0 | $0 |
| Tier 1 seed alignment | $0 LLM; ~0.6 s CPU p50 | $0 | $0 |
| Worker memory 1 → 2 GiB (only if P0 RSS needs it) | – | **≈ $3.6 fixed** | ≈ $3.6 per always-on task |
| Fallback if memory refused: Cohere Embed v4 on acc2 for repeats | ≈ $0.0002 blog | < $0.10 | ≈ $0.30–0.60 |
| Extra repairs from true Tier 1 findings (~0.5 per piece × $0.0045) | ≈ $0.002 | ≈ $0.2–0.8 | ≈ $7 |
| Tier 2 residual verifier (gpt-6-luna class, few candidates per blog) | ≈ $0.003–0.008 blog, ≈ $0.001 LinkedIn | ≈ $1–2 | ≈ $10–25 |
| FAQ fit re-routed from Sonnet ($0.012/blog) to gpt-6-luna after a $0.01 replay on the S247 31 pairs | ≈ $0.001 blog | saves money when FAQ fit is on | saves ≈ $30 vs Sonnet |
| One-off: Tier 2 calibration + shadow batch | – | ≈ $2.5 once (cap $5) | – |

Total: **$0 now; ≈ $5–7 per month on Dev once everything is live** (memory bump included); ≈ $20–35 per month at early
tenant volume. Each paid run is stated in USD before and after, logged in `shared.llm_call_log` (`stage=adhoc_aa789`),
and kept to the eval set and stored pieces, never the catalogue.

---

## 6. PR slices

All CIS PRs touch gate or hold logic, so each gets an independent reviewer subagent before merge (DM-11.5). Default
mode for every new class is `off` on merge, then `shadow` by worker env.

**Next session ($0, P0 + P1):**

| Slice | Repo | Content | Size |
|---|---|---|---|
| S1 foundation | CIS | `nlp_parse.py`, `seed_graph.py`, `seed_align.py` skeleton; pins + Dockerfile (lazy load in worker only); per-class mode config (`T10_SA_MODE_<CLASS>` = off/shadow/repair/hold); `sa:` prefix routing into F17/F18/F13 results before `merge_ledger`; `never_holds` clause (hold only if class mode = hold and repair already failed); I1 import lint, I2 byte-identity test, seed-builder contract test | 2 d |
| S2 eval harness | CIS | `scripts/aa789_seed_align_eval.py`: reads an eval file path (outside the repo), wraps seed excerpts, writes predictions for `score.py`; baseline row for `main`; replay extension (kinds only) | 1 d |
| S3 fact checks | CIS | Classes 1–5 + repair guard + error-injection tests + synthetic positives/negatives (every verifier clean sentence as a negative) | 2.5 d |
| S4 style/integrity checks | CIS | Classes 6, 7, 8, 10 (with the bare-NP orphan extension) | 1.5 d |
| S5 prevention | CIS | `Naming:` rendered as a use-this-name line in the seed builder; thin-moment brief rewritten without a template; prompt register rows updated; snapshot tests | 0.5 d |
| Root | root | This plan into `docs/research/`, P0 numbers into `docs/audits/<date>-S<nnn>-aa789-seed-align/` (counts only) | 0.25 d |

**Session after (still $0 unless noted):**

| Slice | Repo | Content | Size |
|---|---|---|---|
| S6 repeats | CIS | `sentence_embed.py` (bge-small ONNX int8) + class 9 (same-seed-line pairing, autofix-delete or warn) | 1.5–2 d |
| S7 FAQ | CIS | Class 11 `type_mismatch` + Tier 1 pre-filter in front of `faq_answer_fit` | 1 d |
| I1 memory (conditional) | Infra | Worker 1024 → 2048 MiB, only after decision D1 | 0.25 d |
| S8 feedback loop | CIS | `writing_signal` join on sentence sha (false alarm / miss), Signals filter, weekly per-class precision row + automatic demotion job | 1.5 d |
| S9 Tier 2 module ($0 part) | CIS | `claim_verify.py` pure parts: candidate list from Tier 1 abstentions + residual patterns, schema, verbatim-anchor checks, `ClaimMemory`, stub client, worst-case-row tests; route migration drafted, not applied | 1.5 d |

**When a route exists (paid, after decision D2):** S10 route migration + Tier 2 shadow wiring + admin agree/disagree
tab (aa-ui-verify), P3 calibration run with report; then promotion PRs P* (0.25 d each, after ~18/11).

Effort: ≈ 10 d for Tier 0 + Tier 1 + harness + feedback, ≈ 4 d for Tier 2. S3, S4, S5 are independent after S1 and
can run in parallel lanes.

---

## 7. Decisions needed from the tech lead

Each has a proposed answer; nothing else blocks the $0 phases.

| # | Decision | Proposed answer |
|---|---|---|
| D1 | Worker memory 1 → 2 GiB (≈ $3.6/month) if P0 shows spaCy + bge do not fit in 1 GiB | Yes, only if measured RSS needs it; otherwise Cohere Embed v4 on acc2 for repeats (pennies per month) |
| D2 | Route for Tier 2 and the FAQ fit re-route while acc3 Bedrock is blocked: top up OpenAI API credit (`gpt-6-luna-openai`, data leaves AWS on the same terms as today's `t10_judge` fallback) or wait for the AWS case | Use OpenAI credit when it is loaded for the luna judges anyway (AA-999 step 2); cap Tier 2 one-off spend at $5 |
| D3 | Reading of the S246 freeze: repair-only `sa:` findings under existing gates before ~18/11, holds only after | Yes: no new gate and no new hold path before 18/11; repair mode is allowed earlier |
| D4 | Linear shape (Free-plan quota): keep AA-789 for Tier 0 + Tier 1, and open one new issue for Tier 2 (it depends on a paid route) | Yes, one new issue, created only after this approval |
| D5 | Label evidence for holds: agent two-rater panel + tech lead spot-check of 20 items per hold-capable class | Yes; promotion PRs after G3 are agent-merged in the dev phase, with the evidence table in the PR |
| D6 | Tier 0 changes the writer's inputs (naming line, brief wording) for all future pieces | Yes; measured on the next paid T-round we run anyway |
