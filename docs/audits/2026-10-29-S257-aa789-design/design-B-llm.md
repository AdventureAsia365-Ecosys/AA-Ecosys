# AA-789 design B: LLM claim verifier for T10 ("the model proposes, the code decides")

Status: design only, no code. Written in S257 (29/10/2026). No paid LLM call was made for it.
Scope: the defect classes that CIS PR #1140 (AA-789 revision 4) left as pinned known misses in
`tests/unit/test_aa789_t10_recall.py`, plus the claim-level gap from Report 12 §1.3 ("90 non-CTA claims, ~10% caught").

## 0. Summary

- **What.** One cheap structured LLM pass reads the final candidate text and the numbered seed. For each atomic
  claim it returns: the piece span, the cited seed line, a verdict (`supported` / `contradicted` / `not_in_source`
  / `not_a_claim`), and a typed contradiction kind. It also returns a few structural marks: paraphrased repeat,
  orphan opener, and leaked writer instruction.
- **Who decides.** The model never holds a piece on its own. A finding can **hold** only when three things are
  true: the model says `contradicted` with a holdable kind; a deterministic confirmer for that kind passes on the
  two verbatim spans the model pinned; and an isolated re-check call agrees. Even then the finding first gets one
  sentence repair, and the piece is held only if the repair fails. Every other finding is **repair once, never
  hold**, or a warn flag.
- **Why this can reach precision ≥ 0.98 when F9 v2 could not.** The S234 F9 v2 replay (`05-f9v2-replay.md`) let the
  model decide "unsupported". It cleared only 33/46 over-strict flags (72%) and leaked 19 exempt-typed claims. Design
  B never blocks on "unsupported". It blocks only on a typed contradiction that code can check between two quoted
  spans. The regex rules that #1140 reverted fired on clean copy because they ran on every sentence. Here the same
  kind of literal check runs only on the sentence–seed pairs the model pinned, so the false-positive surface shrinks
  from every sentence to a handful of candidates.
- **Model.** Stage `t10_claims` already exists (role `validate`, migration 221, not yet wired). It routes
  `gpt-6-luna → gpt-5.6-luna`, and **both are refused on acc3 since 29/10** (OpenAI-on-Bedrock left with the
  reseller org). Proposed route: `haiku-5-5` on acc3 (Claude still works there; same price as GPT-6 Luna), with
  `gpt-6-luna-openai` as the fallback. Never Sonnet.
- **Cost.** About $0.004–0.005 per blog and $0.001 per LinkedIn post, about $0.003 per piece on the current mix.
  That is about $1 per month at Dev volume (~344 `t9_write` jobs in 30 days), about $13 per month at 5,000
  pieces/month, and about $80 per month at 30,000 pieces/month.
- **Latency.** Blogs are verified in parallel section chunks and run concurrently with the F9 judge, adding about
  0–5 s. In shadow mode the step has a 30 s timeout and fails open.
- **Effort.** 5 PRs, about 6 engineer-days. All of PR1 (pure module, confirmers, eval harness, error-injection eval)
  is $0 and can be done this week.

## 1. What exists today (read before building)

| Piece | Where | Relevance |
|---|---|---|
| Gate stack | `quality_gates.run_quality_gates` (`:2638`) | Already takes replayed LLM results (`f9_results`, AA-918). Design B adds `claim_results` the same way |
| F9 judge | `quality_gates._gate_brand_voice` (`:1063`), stage `t10_judge` | Whole-piece judge that already lists `unsupported_claims`. It flip-flopped in 10/15 reverts (S234) → sticky pass `F9PassMemory` (AA-777/865). Design B reuses that memory pattern |
| F9 v2 claim rules | `claim_rules.py` (`number_source_lines`, `split_piece`, `verify_quote`, `apply_rules`, `CLAIM_TYPES`) | The pure halves of an extraction call: numbered/typed seed lines (S/L/P/O/F/B/A/T) and verbatim-quote verification. **Design B reuses these and does not fork them** |
| Stage `t10_claims` | `shared/llm_client/role_config.py:130`, `docs/generated/llm-routes.md` | validate role, `gpt-6-luna → gpt-5.6-luna`, acc3. Both models are blocked today |
| Trip facts | `trip_facts.py`: `parse_moments`, `optional_activities`, `optional_as_fixed` (`:296`), `rarity_claims`, `_HEDGE_RE` | Deterministic halves the confirmers call, so they behave the same as F17/F18 |
| Offered status | `services/acp_shared/offered.py` (`decide`, `status_of_line`, `LOOSE_MARK_RE`) | Whether a seed line is optional or planned (ADR 0009) |
| Repair | `sentence_repair.plan` (`:314`) parses `"<problem>: '<sentence>'"`; `CHEAP_REPAIR_GATES` route to `t9_repair` (Haiku) | Findings use this shape, so the existing repair loop and the AA-528 regression guard work unchanged |
| Hold rule | `hold_failure` / `never_holds` (`:2374`) | Design B adds a kind-level hold rule (§4) |
| FAQ answer fit | `faq_answer_fit.py`, stage `t9_faq_answer_fit` (Sonnet), flag `T9_FAQ_LLM_FILTER` (off/shadow/on), drop-only | Already covers class 11. Design B does not duplicate it (§2, class 11) |
| Labels | `acp_shared.content_piece_label` (AA-769) | Where shadow adjudication can live |
| Held semantics | `service.py` AA-925 note | `held` is an admin-only label: the tenant still receives the piece. A false hold costs admin review time, not delivery |

## 2. Mechanism per missed class

The call returns one row per atomic claim:
`{c, s, q, k, v, r, rq, x}` = claim id, sentence id, piece quote (≤ 12 words, verbatim), claim kind, verdict, seed
line id, seed quote (≤ 15 words, verbatim), contradiction kind.

It also returns structural rows:
`{s, m, a}` = sentence id, mark (`repeat_of:<sid>` / `orphan` / `instruction_echo` / `naming_note`), and the anchor
quote.

There is no numeric confidence field. Model self-reported probabilities are badly calibrated. Confidence comes from
code confirmation plus agreement with a second call.

**Severity legend:** `HOLD` = may hold after one failed repair. `REPAIR` = blocks once for a sentence repair, never
holds (in `never_holds`). `WARN` = admin flag only.

| # | Missed class (pinned known miss) | Model output | Deterministic confirmer (runs only on the pinned pair) | Severity |
|---|---|---|---|---|
| 1 | "by boat" optional activity presented as planned (r4 #5, #14) | `v=contradicted, x=optional_as_planned`, `r` = the seed line listing the option | `rq` locates in `r`. `offered.status_of_line(r)` or `trip_facts.optional_activities` marks the activity optional, and its tokens overlap `q` (`_mentions_activity`). The clause holding `q` has no hedge (`_HEDGE_RE`), and neither does the paragraph lead (same logic as `optional_as_fixed`). Transport-of-goods sentences ("supplies arrive by boat") fail on the subject check: the claim kind must be `trip_activity` and the sentence subject a traveller noun or pronoun | **HOLD** |
| 2 | Reverse flip: planned moment called optional (r4 #18) | `x=planned_as_optional`, `r` = a `Source itinerary` / Day line | `r` is kind S, the activity is **not** in `optional_activities`, and its tokens overlap `q`. `q`'s clause carries an optional marker (`optional`, `if you wish`, `can be added`). Rejects "The Tsaatan day is part of the plan, not an optional extra" (marker is negated → the planned reading holds) | **HOLD** |
| 3 | "lunch/stop at X" when the source says near X (r3, r4 fix 2) | `x=near_as_at` | `rq` contains `near\|outside\|close to\|on the way to` + place P. `q` contains `at\|in` + the same P (`phrase_tokens` + `lev` ≤ 1) and no `near`. The claim kind is `trip_stop` (a trip promise, not background such as "buses stop in Mörön") | **REPAIR** first. Promote to HOLD only if shadow precision ≥ 0.98 (it is a minor defect) |
| 4 | "not a technical climb" difficulty promise (r4 #14) | `x=difficulty_understated` (seed says demanding) or `v=not_in_source, k=difficulty_promise` (seed silent) | Contradicted: `rq` has a difficulty marker (`strenuous\|steep\|significant elevation\|demanding\|multi-hour\|challenge`) **and** `q` has an easiness marker (`easy\|gentle\|not (a )?technical\|no effort\|suitable for all`), **and** the seed line does not itself contain the easiness term. The last check rejects Thorong La "non-technical … challenge is altitude" vs "not a technical trek" | contradicted **HOLD** (family safety). Not in source → **REPAIR** |
| 5 | "significant fraction/share of the world" unsupported (r4 #19, 0.4%) | `x=quantity_inflated`, `r` = the line with the figure | `rq` has a number with `%`/`percent`/a fraction; parse the value. `q` has a magnitude word (`significant\|considerable\|large\|major\|vast\|most\|majority`) on `share\|fraction\|portion\|part`. Confirm if value < 10% (magnitude words) or < 50% (`most`/`majority`). Rejects Baikal "20 percent … a significant share". No figure in the seed → `not_in_source` → REPAIR | figure present **HOLD**, else **REPAIR** |
| 6 | Scopeless superlative not in the source (r4 #16 "one of the most coherent … available"; r4 #4 "hard to overstate") | `v=not_in_source, k=superlative`, plus a `scoped` boolean | `q` contains a superlative or rank token, and no seed line has the same lemma about the same subject (`content_words` overlap). Cannot hold: "scoped vs scopeless" is a judgement, and the clean set has scoped superlatives ("among the most distinctive communities … in northern Mongolia") | **REPAIR** (F18 cheap repair) |
| 7 | The brief's "one X, one Y, one Z" recipe leaking (r2 #19) | structural `m=instruction_echo` | ≥ 3 content tokens of the sentence (or its "one … one … one" skeleton) occur in `brief_texts` / the angle text the writer got (`hygiene.brief_phrases`). Rejects "Each family gets one tent, one stove and one lantern" and "One driver, one guide, one pick-up point" when the brief does not hold those words | **REPAIR**. F13_leak stays the only no-repair leak invariant |
| 8 | Naming-note leakage (r3 #14 "one phonetic approximation … locals dislike") | structural `m=naming_note`, `r` = a `Naming:` line | `r` is a `Naming:` / Location-note line, and the sentence reuses its writer-guidance terms (`acceptable\|nickname\|approximation\|do not\|the itinerary calls it\|widely used`) **and** the model marks it as guidance, not a reader fact. The clean FAQ "Muren … only a phonetic approximation" is a reader fact, so the model has to tell them apart → never holds | **REPAIR** |
| 9 | Paraphrased repeats (r3 #19 ×3, r4 #1) | structural `m=repeat_of:<sid>` | Both sentences cite the same seed line `r` (or the same normalised claim), they are ≥ 2 sentences apart, neither is in the FAQ (F7 fixer owns that) or is the CTA, and content-word Jaccard ≥ 0.3. Across blog chunks, code pairs claims with the same `r`, then one isolated pair re-check asks "same claim twice? yes/no". Rejects the reviewer's "musical performance / musical instruments" pair (different `r`) | **REPAIR** (cut the later sentence, F13_repeat style) |
| 10 | Orphan section openers (r4 #16 "Access requires a multi-hour …") | structural `m=orphan`, `a` = the dangling referent | The sentence is the first in its section. It starts with a pronoun or demonstrative (`It\|This\|That\|They\|These\|Such`), or the model-quoted referent head noun is absent from the heading and the section but present in the previous section. Rejects "## Punakha Dzong / Admission tickets for the dzong …" (head noun is in the heading) | **REPAIR** |
| 11 | FAQ answer does not address its question (r4 #5, #17, #19) | **Not in this call.** | `faq_answer_fit.py` already does exactly this (isolated mode, drop-only, shadow-able). The S247 lesson was that batched context caused false flags, so folding it into a whole-piece call would bring that failure back | Unchanged: drop-only. Re-route `t9_faq_answer_fit` from Sonnet to `haiku-5-5` after a $0.01 replay on the S247 31 pairs |
| + | Claim-level unsupported, general (90 claims, ~10% caught) | `v=not_in_source` with `k ∈ {trip_activity, service_promise, time, scene_detail}` | `claim_rules.apply_rules` decides as today (type → allowed source kinds, quote check, tripwires) | **WARN** in this issue. Later it can replace F9's fact half once it meets the F9 v2 targets (real_kept ≥ 90%, over_strict_cleared ≥ 90%) |

**Holdable kinds (initial):** `optional_as_planned`, `planned_as_optional`, `difficulty_understated`,
`quantity_inflated` (only with a seed figure). Everything else starts as REPAIR or WARN.

## 3. Where it plugs into T10

### 3.1 New module: `services/acp_content_writing/claim_verify.py`

This module is pure apart from one call wrapper, and mirrors the `claim_rules` / `faq_answer_fit` split:

- `build_request(content_text, grounding_text, *, brief_texts, cta, seo_title, meta_description, channel) -> list[ChunkRequest]`
  - Numbers the seed with `claim_rules.number_source_lines` (SHOWN_KINDS only; O and A lines are dropped, as in
    F9 v2) and the piece with `claim_rules.split_piece`.
  - A blog is split by H2 into ≤ 4 chunks of about 15–20 sentences. Each chunk carries the heading outline and the
    previous section's last sentence (for orphan detection).
  - The system prompt and the numbered seed form an identical prefix, so the chunks share a prompt cache.
- `SCHEMA`: JSON schema with enums for `v`, `k`, `x`, `m`. Compact keys keep output tokens down (the main cost).
- `parse(reply, sentences, source_lines) -> list[ClaimRow | MarkRow]`: drops unknown ids, enums and duplicates
  (first one wins), same as `claim_rules.parse_rows`.
- `confirm(row, ctx) -> Finding | None`: one confirmer per kind (§2), built from `claim_rules.verify_quote`,
  `trip_facts.optional_activities` / `_HEDGE_RE` / `_mentions_activity`, `offered.status_of_line`, and the hygiene
  primitives. A row whose `q` is not in sentence `s`, or whose `rq` is not in line `r`, is dropped (a fabricated
  citation cannot pass).
- `recheck_request(finding) -> Request`: one isolated, kind-specific yes/no question. It contains only the sentence,
  its paragraph and the cited seed moment block (pattern from `faq_answer_fit` isolated mode). Example:
  "Does the sentence present boat rides as part of the plan, while the source lists them as optional? `planned` /
  `hedged` / `unclear`."
- `verify(...)`: the async wrapper. It calls `LLMClient.generate` on stage `t10_claims`, role `validate`, writes one
  `shared.llm_call_log` row per reply (AA-927 shape, `record_call_sync`), uses a 30 s timeout, and fails open: on
  error the result is `unavailable`, with no findings.
- `to_findings(confirmed) -> dict[gate, list[str]]`: each problem in the `"<problem>: '<sentence>'"` shape with the
  seed line snippet (`claim_rules._snippet`: no parentheses or semicolons, so `sentence_repair` can parse it).

### 3.2 Gate: `F20_claim_check`

- Added to `services/quality/registry.py`, as one merged-style entry with a severity per finding (AA-924 shape:
  `findings: [{text, severity, source}]`).
- **Why a new gate, not new findings on F17/F18/F13:** F17/F18/F13 stay deterministic and $0-replayable, and the LLM
  findings are attributable in the ledger and in `gate_eval.ledger_snapshot`, so shadow and blocking precision can be
  measured per source.
- `quality_gates.gate_claim_check(content_text, claim_results, *, mode, hold_kinds, calibrated) -> GateResultLite`.
- `run_quality_gates(..., claim_results=None)`, same as `f9_results`: `None` means the gate passes (off), and a
  replay passes stored results ($0).
- `CHEAP_REPAIR_GATES` += F20, so repairs run on `t9_repair` (Haiku).
- `never_holds(g)`: an F20 entry may hold only if a failed `block` finding has `kind ∈ hold_kinds`, `rechecked=True`,
  and the serving model is in `calibrated`.

### 3.3 service.py wiring (attempt loop, `service.py:~2203–2240`)

1. After `length_trim` (the last edit of the attempt), start the F9 judge and the claim verify concurrently:
   `asyncio.gather(to_thread(gate_brand_voice…), claim_verify.verify(…))`. Then pass both into `run_quality_gates`
   as `f9_results` / `claim_results`. Latency is the max of the two, not the sum. Skip the claim call on an attempt
   whose deterministic gates already failed with a non-repairable blocker (no point paying for it, same reasoning as
   the CTA short-circuit).
2. Sticky pass and carry: keep a `ClaimMemory` per job (the `F9PassMemory` pattern, AA-777/865). After a repair, only
   changed sentences (and their neighbours) are re-verified. A sentence passed earlier and unchanged cannot be flagged
   later. This stops flip-flops and cuts repeat cost to about 10–20% of a full call.
3. Shadow mode (`T10_CLAIMS_MODE=shadow`): one call on the **final** text, after `_apply_faq_answer_fit` and before
   `_final_integrity`. That is the real "post-repair integrity" point of Report 12 §1.4. Results go to
   `writer_input.claim_check` (admin-only) plus a non-blocking `F20_claim_check` flag, and never change status.
   Optionally (sampling flag) also on attempt 1, to measure what repairs mask (AA-791 gap).
4. Flag `T10_CLAIMS_MODE` = `off` (default) / `shadow` / `on`, read like `faq_filter.faq_filter_mode()`. Two more
   settings: `T10_CLAIMS_HOLD_KINDS` (comma list, empty = nothing holds) and the calibrated-model list. Each is a
   per-kind kill switch.

### 3.4 Admin and observability (CIS `frontend/`)

- The content-quality drawer shows F20 findings with both spans (piece quote + seed line) and the recheck result.
- A "Claim check (shadow)" tab on `/admin/content-quality` lists findings with agree / disagree buttons that write
  `content_piece_label.defects` (AA-769 table), so shadow precision is computed, not eyeballed.
- `llm_call_log` stage `t10_claims` shows up in existing cost pages unchanged.

### 3.5 Docs and governance

- Prompt register row (`docs/llm/prompt-register.md`, already lists `t10_claims`): update the source to
  `claim_verify.py · VERIFY_SYSTEM` with an eval run ID (handbook §5.7).
- CIS ADR `0012-t10-claim-verifier`: "LLM proposes typed claims, code confirms, hold only on rechecked
  contradictions". It cites ADR 0008 and ADR 0009.
- ADR 0008 caveat: a `validate` stage may use any vendor, but "a stage must not be labelled validate to dodge the
  rule". The verifier is a check whose output the judge never scores, so `validate` is legitimate. But a Haiku
  verifier reading Sonnet prose is same-vendor, so the ADR must state the mitigation (code decides; cross-vendor
  recheck when an OpenAI route is available) and Nghiệp approves it.

## 4. Precision safeguards: how clean copy is never held

1. **No hold on "unsupported".** `not_in_source` is never more than REPAIR. This removes the F9 v2 failure mode (model
   judgement on place background and opinion: 12 + 7 exempt-typed leaks, 72% over-strict cleared).
2. **Verbatim anchors.** `q` must locate in sentence `s` and `rq` in seed line `r` (`verify_quote`, fold-normalised,
   ≥ 4-char content word shared). A hallucinated citation is dropped silently.
3. **Kind confirmers (§2)** check a structural contrast between the two spans: optional vs. no hedge, near vs. at,
   figure < 10% vs. "significant". They are the literal rules #1140 had to revert, but they now run only on pinned
   pairs. Every verifier-round clean sentence in `test_aa789_t10_recall.py` (rounds 1–3, the 40 `ROUND3_CLEAN`, the
   near-miss lists) becomes a negative test for the confirmers. **In the test, each one is paired with a worst-case
   model row** (`contradicted`, every kind, best-matching seed line). This is the error-injection eval in §6 (P0) and §11.
4. **Isolated recheck.** A second, context-free call must agree (`planned` for kind 1, and so on). Disagreement or
   `unclear` demotes the finding to REPAIR. When an OpenAI route is available, the recheck runs on the other vendor
   (`gpt-6-luna-openai` vs. a Haiku primary), so a shared vendor blind spot needs two vendors to fail.
5. **Repair first.** A holdable finding still goes to one sentence repair. The piece is held only if the repaired
   sentence is re-verified and still confirmed (or the AA-528 guard reverts the repair). In the S234 data, F17 repair
   worked in 17/22 cases and F18 in 13/15, so most true positives never become holds.
6. **Sticky pass** (AA-777 pattern): a sentence passed in an earlier attempt and unchanged cannot be flagged later.
7. **Calibrated model only.** If the gateway serves a fallback model that has not passed the §6 eval, every F20
   finding is demoted to WARN.
8. **Fail open.** An unavailable or unusable reply means no findings plus a flag. This is unlike F9's AA-925 degraded
   hold, because the verifier is additive and its outage must never add holds.
9. **Kill switches.** `T10_CLAIMS_MODE`, plus per-kind `T10_CLAIMS_HOLD_KINDS`. Rollback is an env change on the
   worker task definition, with no deploy.
10. **Bounded blast radius.** `held` is an admin-only label, and the tenant still receives the piece (AA-925). The
    precision bar protects admin review time and trust in the gate, not delivery.

## 5. Expected precision and recall per class

These are priors, not measurements. §6 defines how each is measured. "Precision" counts findings at the stated
severity. Recall is on the pinned known misses plus the matching §1.3 panel examples.

| Class | Expected recall | Expected precision | Reasoning |
|---|---|---|---|
| 1 optional as planned | 0.75–0.85 | ≥ 0.98 after confirm + recheck | The seed lists options explicitly. The model handles "by boat" transport vs. activity. The hedge check is the same logic F17 already runs |
| 2 reverse flip | 0.80–0.90 | ≥ 0.98 | Strongest contrast: "optional" in the piece vs. a planned S line. The negation guard covers "not an optional extra" |
| 3 near vs. at | 0.60–0.75 | 0.90–0.97 (REPAIR) | The model must type the sentence as a trip stop and not background ("buses stop in Mörön"). Few examples, so it stays REPAIR until measured |
| 4 difficulty (contradicted) | 0.65–0.80 | ≥ 0.98 | Needs a seed difficulty marker. The "seed already says non-technical" guard removes the Thorong case |
| 4 difficulty (not in source) | 0.60–0.75 | 0.85–0.95 (REPAIR) | Judgement-heavy. A repair adds a caveat or cuts the line, which is cheap |
| 5 quantity inflated | 0.70–0.85 (with figure) | ≥ 0.98 | Numeric comparison in code. Without a figure it is a REPAIR with lower precision |
| 6 scopeless superlative | 0.60–0.75 | 0.85–0.92 (REPAIR) | "Scoped" is fuzzy. A repair costs $0.012 and can flatten good copy, so it never holds |
| 7 brief recipe | 0.50–0.65 | 0.90–0.97 (REPAIR) | Depends on the brief text being passed. The overlap confirmer stops "one tent, one stove" |
| 8 naming note | 0.55–0.70 | 0.85–0.92 (REPAIR) | Reader fact vs. writer guidance is a semantic call. The clean FAQ pronunciation example is the hard negative |
| 9 paraphrased repeat | 0.65–0.80 | 0.88–0.95 (REPAIR) | Same seed line + pair recheck. Summaries and FAQ are excluded |
| 10 orphan opener | 0.60–0.75 | 0.88–0.95 (REPAIR) | First-sentence check plus referent location |
| 11 FAQ fit | (existing step) | (existing step) | Unchanged. Measure the re-route on Haiku 5.5 |
| Claim-level unsupported | 0.40–0.60 | 0.70–0.80 (WARN) | Same ballpark as F9 v2. That is why it only warns |

Hold-level effect: on the 40-piece S234 set, Design B should hold only pieces with a confirmed flip, difficulty or
figure contradiction that one repair could not fix. Expect 0–2 pieces, against the current 14 held.

## 6. Rollout with measurable gates

| Phase | What | Cost | Exit gate (all must hold) |
|---|---|---|---|
| **P0: offline, $0** (this week) | PR1: pure module, confirmers, schema. **Eval set E1** (committed, synthetic): the AA-789 known misses as positives (≥ 5 per class, add synthetic ones where a class has fewer) plus every verifier clean sentence (≈ 100) plus ~150 new synthetic negatives (a reviewer agent writes them, no real tenant text). **E2** (scratch only, `.tmp-session/s249/aa783_export.json`): the 40 S234 pieces, labelled at sentence level by two independent agent labellers plus an adjudicator; Nghiệp spot-checks 10%. **Gold rows:** Claude Code (subscription, $0 marginal) writes the ideal model rows for E1 and E2. **Error injection:** worst-case rows for every clean sentence | $0 | Confirmers reject **100%** of injected worst-case rows on clean E1 and E2 sentences, or each leak is analysed and the kind is demoted to REPAIR. Confirmers accept ≥ 95% of gold contradiction rows. Replay with gold rows: 0 holds on the 26 panel-approved pieces. `test_aa789_t10_recall.py` known-miss tests flip to "found via F20 with gold rows" |
| **P1: model calibration** (paid, needs Nghiệp's explicit yes) | `scripts/aa789_claims_eval.py` via `LLMClient.generate`, stage `adhoc_aa789`, role `validate` (cost logging rule). E1 + E2, 3 runs each, on `haiku-5-5`. If an OpenAI route is back: also `gpt-6-luna(-openai)` | **≈ $1.6** est. (cap $3) | Holdable findings: **0 false** on E1 + E2 clean (≈ 1,500 sentences; 95% upper bound ≤ 0.2% per sentence) and precision ≥ 0.98 over all holdable findings. Test-retest agreement on holdable findings ≥ 95% (F9 v2 V2a reached 38/38 on pieces). Recall on holdable classes ≥ 0.6. Cost ≤ $0.006 per blog and p95 latency ≤ 15 s per chunk. Pick the model with the best precision first, then cost |
| **P2: shadow on Dev** | PR2 + PR5. `T10_CLAIMS_MODE=shadow` on the worker. Dev has no real traffic and no waiting is needed: run the shadow verifier once as a batch over the ~350 stored `content_piece` rows (final text plus stored seed), plus all new pieces. The agent panel adjudicates **every** HOLD/REPAIR finding and a random 10% of passes in the shadow tab | ≈ $1 batch (cap $2), then ≈ $1/month | ≥ 200 pieces verified. Holdable findings precision ≥ 0.98 with n ≥ 50 adjudicated (≤ 1 FP). **0 would-be false holds.** REPAIR findings precision ≥ 0.85 per kind (below that → WARN). Unavailable ≤ 2%. Added p95 latency ≤ 15 s |
| **P3: blocking** | PR4. `T10_CLAIMS_MODE=on`, `T10_CLAIMS_HOLD_KINDS` = the kinds that passed P2 one by one; REPAIR kinds go live at once | per §7 | Two weeks (or 200 pieces) in `on` with no adjudicated false hold. Any false hold → remove that kind from `HOLD_KINDS` (env change) and add the sentence as a negative test |
| **P4 (later, separate issue)** | Let F20's general `not_in_source` replace F9's fact half when it meets the F9 v2 targets | saves part of F9's $0.005/piece | real_kept ≥ 90%, over_strict_cleared ≥ 90%, 0 exempt-typed leaks |

Every paid run follows the house rules: state the USD before the run and after it, keep to a subset (the eval set,
not the catalogue), log cost through `llm_call_log`, and record an eval run ID in the PR.

## 7. Cost

### 7.1 Assumptions (from repo data)

- **Sizes** (S234 export, 40 pieces):
  - blog seed median ≈ 10.1k chars (≈ 2.5k tokens) and text ≈ 8.0k chars (≈ 2.0k tokens, ~70 sentences);
  - LinkedIn seed ≈ 2.4k chars (≈ 0.6k tokens) and text ≈ 1.2k chars (≈ 0.3k tokens, ~12 sentences).
- **Output** dominates. The F9 v2 V2a replay averaged ≈ 1.6k input / 2.4k output tokens per call ($0.0013/call on
  GPT-6 Luna). With compact keys a blog yields ≈ 100 claims × ~45 tokens ≈ 4.5–5k output tokens; LinkedIn ≈ 0.8–1k.
- **Prices** (`llm-routes.md`): `haiku-5-5` and `gpt-6-luna(-openai)` cost $0.10 in / $0.50 out per Mtok, cache read
  $0.01 (Haiku 5.5 cache write $0.125). `gpt-5.6-luna` costs $0.20 / $1.20. `sonnet` costs $3 / $15 and is excluded.

### 7.2 Per piece (primary route on `haiku-5-5` or `gpt-6-luna`)

| Item | Blog (4 chunks) | LinkedIn (1 call) |
|---|---|---|
| Input: system prompt + seed prefix (≈ 3.7k) cached once, read 3×; chunk text ≈ 2k uncached | ≈ $0.0008 | ≈ $0.0002 |
| Output ≈ 5k / 1k tokens | ≈ $0.0025 | ≈ $0.0005 |
| Isolated rechecks (0–3 × ~600 in / 50 out) | ≈ $0.0002 | ≈ $0.0001 |
| Re-verify after a repair (changed sentences only, ~15% of a call, on ~40% of blogs) | ≈ $0.0003 | ≈ $0.0001 |
| Extra sentence repairs the new findings cause (S234: $0.012 each; ~20% of blogs, ~5% of LinkedIn) | ≈ $0.0024 | ≈ $0.0006 |
| **Total** | **≈ $0.006** (verifier alone ≈ $0.0038) | **≈ $0.0015** (verifier alone ≈ $0.0009) |

On `gpt-5.6-luna` the verifier part is about 2.4× (blog ≈ $0.009). Against today's T10 cost of $0.01–0.03 per piece,
Design B adds about 10–30%. Against the whole T9 piece cost (S234: $4.231 / 80 = $0.053 per piece) it adds about
3–10%.

### 7.3 Monthly (blended ≈ $0.0033 per piece at 40% blog / 60% LinkedIn, including repairs)

| Volume | Pieces/month | Haiku 5.5 / GPT-6 Luna | GPT-5.6 Luna |
|---|---|---|---|
| Dev today (`t9_write` 344 jobs/30 d, probe W44) | ~344 | **≈ $1.1** | ≈ $2.3 |
| Early prod (10 tenants × 40) | 400 | ≈ $1.3 | ≈ $2.7 |
| Mid prod (50 × 100) | 5,000 | ≈ $17 | ≈ $35 |
| Large prod (200 × 150) | 30,000 | ≈ $100 | ≈ $210 |

The one-off costs are P1 at about $1.6 and the P2 batch at about $1. Both are cheap enough to fit inside the $249.94
AWS Lift credit on acc3 if the model is Claude on Bedrock. The Marketplace-sold OpenAI-on-Bedrock models may not be
covered by the promo credit.

### 7.4 The acc3 block and fallbacks

- **Today:** OpenAI-on-Bedrock (`gpt-6-luna`, `gpt-5.6-luna`) returns AccessDenied on acc3 since 29/10 06:50 UTC, so
  the existing `t10_claims` route is dead. Claude on acc3 still works.
- **Proposed route** (one migration on `shared.llm_role_config` plus `SAFE_DEFAULTS`):
  1. `haiku-5-5` (acc3 Bedrock, works now, same price as GPT-6 Luna, prompt caching);
  2. fallback `gpt-6-luna-openai` (OpenAI API; needs the OpenAI credit top-up that AA-999 already recommends).
  - No Sonnet fallback: it is 30× the cost, and a fallback that has not passed calibration is demoted to WARN anyway.
- **When the AWS case restores OpenAI-on-Bedrock:** rerun P1 for `gpt-6-luna` (≈ $0.8). Make it primary only if its
  precision is at least as good, because a cross-vendor primary matches the spirit of ADR 0008. Keep the other model
  as the recheck vendor.
- **If both routes are down,** the verifier fails open (WARN flag, no holds), so T10 behaves exactly as today.
  Design B adds no new dependency on the blocked account.

## 8. Latency

- **Throughput assumption:** about 100–200 output tokens per second plus 1–2 s to first token, for Haiku 5.5 and
  GPT-6 Luna class models.
- **Blog:** 4 chunks of about 1.2k output tokens run in parallel, so about 7–14 s wall time. Rechecks add 1–3 s.
- **LinkedIn:** one call of about 1k output tokens, about 5–8 s.
- **Added to the attempt:** the call runs concurrently with the F9 judge, which is a similar-sized call, so the
  attempt grows by about 0–5 s. A re-verify after a repair touches only the changed sentences, about 2–4 s. Compare
  `t9_write` today: p50 70.6 s, p95 180.9 s.
- **Shadow mode:** one call on the final text with a 30 s timeout that fails open. That is at most +30 s, typically
  about 10 s, on Dev only.
  - The alternative is a follow-up `shared.job` kind with zero added latency. It is not chosen because the result has
    to sit in the same `writer_input` record, and Dev latency does not matter.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Model flip-flops, as F9 did on 10/15 reverts | Sticky pass and carry memory; recheck agreement; test-retest ≥ 95% as a P1 gate |
| Same-vendor blind spot (Haiku verifying Sonnet prose) | Code decides holds; cross-vendor recheck when OpenAI returns; ADR line approved by Nghiệp |
| Truncated output on long blogs | Chunking by H2; `max_tokens` sized per chunk; a missing sentence id → one re-ask of that chunk (`parse_rows` pattern) or treat as unverified (no finding) |
| Confirmers drift back into regex whack-a-mole | They run only on pinned pairs. Every clean verifier sentence plus its worst-case row is a CI negative. A kind that leaks in the error-injection eval is demoted, not patched |
| Seed format drift breaks line numbering | `number_source_lines` already has a round-trip contract test with `compose_seed` (`atom_seed.py:229`). Design B reuses it |
| Real tenant copy leaking into the repo through eval fixtures | E2 stays in `.tmp-session` (gitignored). E1 is synthetic only. The CI golden-text guard stays on |
| Cost creep: repairs, re-verifies, prod growth | Re-verify only changed sentences; the stage is visible in `llm_call_log` and the wave cost report; per-piece cost is a P1 gate |
| acc3 vendor or billing changes again | Two routes on different providers; fail open; no holds without a calibrated model |
| Over-repair flattens good copy (REPAIR kinds) | Per-kind REPAIR precision gate ≥ 0.85 in P2, else WARN; the AA-528 regression guard reverts a repair that introduces new failures |
| Prompt injection via seed or brief text | All inputs are internal (catalogue seed, tenant brand pack); output is schema-validated enums plus verbatim quotes; nothing from the reply is executed |
| Small eval set: few true holdable contradictions (positives are mostly synthetic) | Precision is shown on the clean side (≈ 1,500 sentences + 200 shadow pieces, 0 false holds). Recall per class is reported with its n, not as one headline number |

## 10. Effort

| PR | Content | Days |
|---|---|---|
| PR1 (CIS) | `claim_verify.py` pure parts (request builder, schema, parser, confirmers); E1 fixtures; error-injection tests; `scripts/aa789_claims_eval.py` with a `--rows` replay mode ($0) and a `--live` mode (paid, adhoc stage); implementation notes `docs/implementation-notes/AA-789.md` updated | 1.5 |
| PR2 (CIS) | Call wrapper (gateway, call log, timeout, fail open); migration for the `t10_claims` route (`haiku-5-5` → `gpt-6-luna-openai`) plus a prompt version; `T10_CLAIMS_MODE` shadow wiring; `writer_input.claim_check`; prompt register row; ADR 0012 | 1.5 |
| (run) | P1 calibration plus report in `docs/audits/<date>-S<nnn>-aa789-claims/` (memory: save audits locally) | 0.5 + ≈ $1.6 |
| PR3 (CIS frontend) | Drawer display plus the "Claim check (shadow)" tab with agree/disagree labels (AA-769 table) | 1 |
| PR4 (CIS) | Blocking: `F20_claim_check` in the registry, `run_quality_gates(claim_results=)`, the `never_holds` kind rule, `CHEAP_REPAIR_GATES`, `ClaimMemory` carry, concurrent F9 + claims, replay of stored claim results | 1–1.5 |
| PR5 (Infra / worker env) | `T10_CLAIMS_MODE` / `T10_CLAIMS_HOLD_KINDS` on the worker task definition (shadow, then on) | 0.25 |

Total: about 6 engineer-days over 5 PRs. PR2 and PR4 touch the gate and hold logic, which counts as risky (DM-11.5),
so each gets an independent reviewer subagent.

## 11. This week at $0 vs. later with paid calls

**$0, buildable and measurable now:**
- PR1 completely: confirmers, schema and parser, unit tests.
- Eval set E1 (synthetic, committed) and the E2 sentence labels (scratch, agent panel, Nghiệp spot check).
- Gold rows for E1 and E2 written by Claude Code (subscription, no API spend). This gives the achievable recall
  ceiling per class with these confirmers.
- The error-injection eval: worst-case model rows on every clean sentence. It measures the precision floor that code
  guarantees **whatever the model does**, which is the core safety claim of this design.
- `--rows` replay through `run_quality_gates(claim_results=)` on the 40 pieces: count holds and repairs per piece,
  compare against panel verdicts and the current ledger.
- The ADR draft, the prompt draft and the route migration draft. The route stays unapplied until P1 is approved.

**Needs paid calls later** (each run stated in USD first and approved):
- P1 model calibration: ≈ $1.6 on Haiku 5.5, plus ≈ $0.8 per extra model once OpenAI access returns.
- The `t9_faq_answer_fit` re-route replay (S247 31 pairs): ≈ $0.01.
- P2 shadow batch over the ~350 stored Dev pieces: ≈ $1, then ≈ $1/month steady state.
- P3 blocking traffic: ≈ $0.003 per piece.
