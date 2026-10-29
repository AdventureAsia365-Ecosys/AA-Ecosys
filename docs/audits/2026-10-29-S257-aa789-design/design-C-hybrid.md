# AA-789 design, Approach C: deterministic candidates + LLM adjudicator

S257, 29/10/2026. Design only. No code was changed. The one measurement in this document (§9.1) was a $0 offline run on the stored S234 pieces, and it printed counts only.

Inputs read for this design:
- CIS `main` @ `4feb3cb3`: `services/acp_content_writing/{quality_gates.py, hygiene.py, trip_facts.py, faq_answer_fit.py, sentence_repair.py}`, `services/acp_shared/channel_spec.py`, `shared/llm_client/role_config.py`, `services/writing_memory/{signals.py, fact_filter.py, reason_codes.py, calibration.py}`, `tests/unit/test_aa789_t10_recall.py`, `scripts/aa789_recall_replay.py`, `docs/implementation-notes/AA-789.md`.
- The AA-789 revisions in git: `05b175e3` (rev 1, broad), `e76c3fcf` (rev 2), `83291bbf` (rev 3) and `79a429aa` (rev 4, merged as #1140).
- Root: `docs/audits/2026-10-13-S234-t-series-rounds/12-gates-t2-tenants.md` §1.1–1.5, `05-f9v2-replay.md`, `docs/generated/llm-routes.md`.

---

## 0. The design in one paragraph

Bring back the broad patterns from revisions 1–3 and widen them further, but as **candidates, not findings**. A candidate is a `(class, sentence, seed anchor)` triple. It is not a gate result and cannot be one. It can block or hold a piece only if an **adjudicator call** says it is a violation (one LLM call per piece, or per moment group on long blogs). That call reads the candidate sentence, its neighbouring sentences and the piece's own seed. Then three more conditions must hold:
1. The verdict's evidence passes a deterministic check: the quoted seed line really is in the seed, and the quoted claim really is in the sentence.
2. For a hold, a second model confirms the verdict.
3. The finding has already had its one sentence repair and failed it.

Every candidate the adjudicator clears is logged with its verdict. Disagreements from human review (Writing memory signals) feed calibration and drive the per-class kill switch. With the adjudicator off, failing, or unreachable (Bedrock on acc3 today), the ledger is **byte-identical to `main`**. The deterministic tier has no code path that adds a failed result.

---

## 1. Invariants (written as tests, not as conventions)

| # | Invariant | How it is enforced |
|---|---|---|
| I1 | The candidate tier never adds a failed gate result. | `t10_candidates.py` returns `list[Candidate]` and imports nothing from `quality_gates`, so it has no `_result`, no gate names and no `Finding`. An import-lint test (same style as the AA-926 gate-name lint) fails the build if it does. |
| I2 | Adjudicator off, error, timeout, unusable reply, or no route means the ledger equals `main` byte for byte. | A replay test on the 40 stored pieces plus the round-1/2/3 clean sentences. It runs `run_quality_gates` with `adjudication=None`, with a raising stub, and with a stub that returns UNSURE, and asserts that `gate_ledger` equals the `main` output. Fail open, as `faq_answer_fit` does. |
| I3 | A finding from an adjudicated class may block only if (a) the verdict is VIOLATION, (b) its evidence passes `verify_evidence()`, and (c) the class mode is `repair` or `hold`. | Each class has its own mode flag (`T10X_MODE_<CLASS>` ∈ off / shadow / repair / hold). The default is `shadow`. |
| I4 | A finding may hold only if, on top of I3, the class mode is `hold`, a second model returned VIOLATION on the same evidence, and the sentence still fails after its one sentence repair. | `never_holds()` gets one new clause: an adjudicated finding (marked by a `t10x:` violation prefix) returns `True` unless its stored record carries `hold_eligible=True`. That flag is set only by the confirm step. |
| I5 | No class whose defect is about style or integrity (repeat, opener, leak, FAQ fit) ever holds. | These classes have no `hold` mode in the enum. Like F15 today, they block once for a repair or a cut, then warn. |
| I6 | Adjudicated findings sit under existing gate names (F17, F18, F13_leak, F13_repeat). | No new gate is added, which respects the S246 rule (no new blocking gates for 4 weeks). The registry gets no new gate entry, only a new finding prefix. |

---

## 2. Where it plugs into T10

```
service.py attempt loop
  └─ quality_gates.run_quality_gates(..., adjudication=AdjudicationMemory|None, adjudication_results=None)
       ├─ existing deterministic gates (unchanged)                         ← main behaviour
       ├─ NEW t10_candidates.generate(content_text, trip_ctx, hygiene_ctx, brief_texts, cta)  ($0)
       │     → list[Candidate(class, span, sentence, neighbours, anchors, det_support)]
       │     minus every candidate whose sentence already has a blocking finding from the deterministic gates
       ├─ NEW t10_adjudicate.adjudicate(candidates, seed=own_seed+Facts, memory)   (LLM, fail-open)
       │     → list[Verdict(class, sentence_sha, verdict, evidence, verified, model, prompt_v)]
       └─ NEW t10_adjudicate.to_findings(verdicts, modes) → violations appended to the F17/F18/F13 legacy results
             (prefix "t10x:<class>: …", always quoting the sentence so sentence_repair.plan can locate it)
service.py
  ├─ sentence_repair.plan()  ← unchanged; adjudicated findings route like any F17/F18/F13 finding
  ├─ after repair: re-adjudicate ONLY candidates whose sentence_sha changed (AdjudicationMemory, like F9PassMemory)
  ├─ confirm step (hold classes only): isolated call on a different model for each still-failing VIOLATION
  └─ hold_failure() ← never_holds() reads hold_eligible (I4)
writer_input.t10_adjudication  ← every candidate + verdict, per attempt (shadow and live)
```

Concrete touch points:

| File | Change |
|---|---|
| `services/acp_content_writing/t10_candidates.py` (new) | The high-recall generator (§3). It reuses `trip_facts.parse_moments`, `optional_activities`, `_mentions_activity`, `Moment.statuses` (OFFERED / INCLUDED), `Moment.naming`, `hygiene.sentence_spans`, `content_words`, `dangling_opener`, `orphan_lines`, and the rev 1–3 regexes from git (`_MODE_RE`, `_COLLECTIVE_HEDGE_RE`, `included_as_optional`, `_NEAR_NAME_RE`/`near_as_at`, `PACE_RE` 'technical', `_SUPERLATIVE_RE`, `BRIEF_WORDING_RE`, `NAMING_NOTE_TERMS_RE`, `paraphrased_repeats`, `subjectless_section_openers`). |
| `services/acp_content_writing/t10_adjudicate.py` (new) | Builds the prompt, defines the JSON schema, batches calls, runs `verify_evidence()`, holds `AdjudicationMemory` (cache key `sha(sentence)+sha(own seed)+prompt_version`), runs the confirm call, and converts verdicts to findings. Every call goes through `LLMClient.generate()` with one `shared.llm_call_log` row, in the AA-927 shape the `faq_answer_fit` stage uses. |
| `quality_gates.run_quality_gates` | Two keyword arguments. `adjudication` is the memory object (None means off). `adjudication_results` holds stored verdicts for a $0 replay, mirroring `f9_results` (AA-918 R0 replay stays $0). Adjudicated violations are appended to the legacy results `gate_trip_facts` / `gate_leak` / `gate_repeat` return, **before** `merge_ledger`. The ledger shape does not change. |
| `quality_gates.never_holds` | The I4 clause. |
| `services/acp_content_writing/service.py` | Creates `AdjudicationMemory` per job (next to `F9PassMemory`), runs the confirm step before `hold_failure`, and persists `writer_input.t10_adjudication`. |
| `shared/llm_client/role_config.py` + a CIS migration | Two stage rows: `t10_adjudicate` (role `judge`, primary `gpt-6-luna` acc3, fallback `gpt-6-luna-openai`) and `t10_adjudicate_confirm` (role `judge`, primary `gpt-5.6-luna`, fallback `gpt-6-luna-openai`). Role `judge` is the right one because the verdict decides a block or hold (ADR 0008: a judge stage must be non-Anthropic). Using `t10_claims` instead is possible: it exists, is unwired, and is a `validate` stage. A separate stage keeps cost attribution clean. |
| `services/quality/registry.py` | Finding prefixes and the class list (gate-name literals stay in the registry, AA-926). |
| `frontend/app/admin/atom-curation` (tab) + BFF route | A read-only "T10 adjudication" tab: each candidate's class, verdict, evidence and mode. QA lives only in admin, never in the tenant view (tenant-sees-content-only rule). |
| `scripts/aa789_candidates_replay.py` (new) | A $0 replay of the generator (counts only, no copy), plus `--fixture` to replay stored verdicts. |

The FAQ class is **not** added to the adjudicator. `faq_answer_fit.py` (stage `t9_faq_answer_fit`, flag `T9_FAQ_LLM_FILTER` off/shadow/on, drop-only, never holds) already does exactly this check. The design moves it to `shadow` together with the adjudicator (§10) and adds its verdicts to the same calibration export.

---

## 3. Mechanism per missed class

Some definitions used in the table:
- "Cand." means the candidate rule. It is deliberately broader than any revision.
- "Q" is the closed question the adjudicator answers.
- "Det. evidence" is what `verify_evidence()` checks deterministically.
- "Max mode" is the strongest mode the class may ever reach.

| # | Class (panel example) | Cand. (high recall, $0) | Adjudicator Q | Det. evidence required for VIOLATION | Routed under | Max mode |
|---|---|---|---|---|---|---|
| 1 | Optional activity stated as planned ('…by boat', r4 #5, #14) | Every sentence that `_mentions_activity` an `OptionalActivity` (seed `Status: OFFERED` / hedge lines), **with or without a hedge**. Also every `_MODE_RE` hit ('by boat / on horseback / by kayak'). | "Does this sentence tell the reader that the optional activity is part of the plan? Hedges may sit anywhere in the sentence or the next one." | `seed_quote` must be a substring of the seed and must contain an OFFERED status or optional hedge for the same activity token. The sentence must contain the activity token. | F17_trip_fact | hold |
| 2 | Reverse flip: a planned moment called optional (r4 #18) | Every sentence with an optional or choice marker ('optional', 'if you like', 'for those who', 'can choose', 'add-on', 'extra cost', 'on request'). Rev 3 `included_as_optional` shape, unbound. | "Does this sentence call something optional or extra that the seed lists as included or planned?" | `seed_quote` is in the seed and is an INCLUDED status line or a plain itinerary line for the same token. The sentence contains the marker. | F17_trip_fact | hold |
| 3 | 'Lunch/stop at X' when the seed says near X (r4 fix 2, r3 Mörön) | Every sentence with a stop verb ('lunch, stop, stay, overnight, camp, picnic, break') + 'at / in' + a capitalised place, where the seed has 'near / outside / on the way to' + the same place token. Rev 3 `_NEAR_NAME_RE` plus a seed-side join. | "Does the copy put the trip *at / in* X where the seed only says near / outside / en route?" | `seed_quote` contains 'near / outside / on the way / en route' and the place token. The sentence contains the same token after 'at / in'. | F17_trip_fact | repair (hold only after §10 phase 4 data) |
| 4 | Difficulty promise ('not a technical climb', r4 #14) | Every sentence with a difficulty lexeme ('technical, easy, gentle, moderate, strenuous, challenging, demanding, accessible, suitable for, no experience, beginner, any fitness, manageable, effortless, steep'). Rev 3 `PACE_RE` + 'technical'. Blog and LinkedIn. | "Does the sentence promise a difficulty or fitness level the seed does not state or that contradicts it?" | The claim span (the lexeme) is in the sentence, and the lexeme's stem is **absent** from the seed. Same rule as `_pace_supported`. If the seed has the stem, the candidate is cleared deterministically without a call. | F17_trip_fact | repair |
| 5 | Unsupported share of the world ('significant fraction', r4 #19) | Every sentence with a share or scope noun ('fraction, share, proportion, percent, the world, on earth, the planet, anywhere else, few places'). Rev 1 F18 extension. | "Does the sentence claim a quantity or share relative to the world (or a region) that no seed line supports?" | The claim span is in the sentence. No seed sentence shares its number or quantifier and scope noun (deterministic support test, the inverse of `rarity_claims`' support check). A seed-backed figure (the Baikal 20% false positive) is cleared before any call. | F18_rarity | hold |
| 6 | Scopeless superlative not in the source ('one of the most coherent', r4 #16) | Every superlative: 'one of the most / best …', 'most + ADJ', '-est' from a closed list, 'the only', 'unique', 'unrivalled'. Rev 3 `_SUPERLATIVE_RE`. | "Is this superlative (with its scope) supported by a seed line with the same or a wider scope? 'Most distinct in Mongolia' does **not** support an unscoped 'most coherent'." | The claim span is in the sentence. If VIOLATION cites a seed line as the near miss, that line must be in the seed. | F18_rarity | repair (hold only after phase 4 data) |
| 7 | Brief recipe leak ('One ruined site, one date, one fact.', r2 #19) | Every 'one X, one Y(, one Z)' or 'a single X … a single Y' sentence, plus any sentence whose content-word 4-gram overlap with `brief_texts` lines is ≥ 2. Rev 1 `BRIEF_WORDING_RE` + `_brief_violations`. | "Is this sentence an instruction to the writer from the brief rather than copy for the reader?" Gets the brief line as the anchor. | `brief_quote` is a substring of `brief_texts`. It shares ≥ 2 content words with the sentence. | F13_leak | repair (cut) |
| 8 | Naming-note leak (r3 #14) | Every sentence with a naming lexeme ('spelled, pronounced, transliterated, phonetic, also called, also known as, formally known, romanised') **or** two names from the same moment's `Naming:` line. Rev 3 `NAMING_NOTE_TERMS_RE`, unbound. | "Does this sentence repeat the seed's internal naming note (meta-guidance about names) rather than give the reader useful name information, such as a pronunciation FAQ answer?" | `seed_quote` is the moment's `Naming:` line (substring check). | F13_leak | repair (rewrite or cut) |
| 9 | Paraphrased repeat (r4 #1, r3 #19 ×3) | Every pair of non-adjacent body sentences with content-word Jaccard ≥ 0.35 (both ≥ 5 content words). Also rev 3 `paraphrased_repeats` pairs. FAQ answers are excluded (F7 fixer). | "Does sentence B tell the reader anything that sentence A does not?" Both sentences and their headings are shown. Answer options: NEW_INFO / SAME_CLAIM. | Both sentences are in the text. The cut target is the later one, and `sentence_repair.delete_flagged` safety applies (never the hook or CTA, no orphaned pronoun). | F13_repeat | repair (cut) |
| 10 | Orphan section opener (r4 #16) | The first sentence after every `##` heading, if it opens on a pronoun, demonstrative or bare relational noun ('This, That, These, It, They, Here, Such, The same'). Also `dangling_opener` / rev 1 `subjectless_section_openers`. | "Read the heading and this sentence alone: is it clear what the sentence is about?" | The sentence is the first sentence after the heading. | F13_repeat | repair |
| 11 | FAQ answer does not answer its question (r4 #5, #17, #19) | All FAQ pairs (`faq_pairs`). | Existing `faq_answer_fit` prompt (NON_ANSWER / WRONG_SUBJECT). | Existing. | `faq_answer_fit` step | drop (never holds; unchanged module) |

Candidate ordering and cap: at most 24 candidates per piece. When there are more, take classes in hold-class-first order, then by sentence position. The overflow is logged as `t10x_overflow`, so recall loss from the cap is visible. In the §9.1 measurement, the largest blog produced about 25 raw hits before de-duplication.

Deterministic pre-clear, which costs $0 and reduces calls:
- class 4 when the seed has the lexeme stem;
- class 5 when a seed sentence backs the figure;
- class 1 when the hedge is inside the same clause as the activity token (rev 3 `_item_hedged` true, which is the case `main` already treats as clean);
- class 9 when the two sentences sit in different `## Day N` sections and differ in day-specific tokens (the round-3 false positive).

Pre-clear can only *remove* candidates, never add findings.

---

## 4. The adjudicator call

**Batching.**
- LinkedIn: one call per piece, and only if there is ≥ 1 candidate after pre-clear. About half of LinkedIn pieces make no call (§9.1: only 8–13 of 24 had any candidate hit).
- Blog: one call per group of ≤ 8 candidates, grouped by moment. That is 1–3 calls, run in parallel (concurrency 3, the pattern `FIT_CONCURRENCY` uses).

Isolated mode (one call per candidate) is kept as a configuration option, as in `faq_answer_fit`. It is used for the confirm step.

**Context in each call.**
- The **full own-seed half** (`split_seed(seed)[0]`) plus the Facts block, not an excerpt. Blog seeds average 10.6k characters (about 2.7k tokens; max 11.6k), and LinkedIn seeds 2.4k characters. Sending the whole seed costs about $0.0003 more per call on gpt-6-luna. It removes the main false-positive source of claim-level LLM checks, which is support that sits in another moment or in Facts. F9 v2 (05-f9v2-replay) lost 12 real violations to "place_background" typing and cleared only 72% of over-strict flags when it judged whole pieces.
- For each candidate: its id, its class, the sentence, the sentence before and after, the section heading, and the deterministic anchor (the activity token, the place token, the claim span or the brief line).
- Class definitions, plus 2 positive and 2 negative synthetic few-shots per class in the batch. The negatives are the verifier round 1–3 clean shapes. Synthetic text only, which keeps the golden-text guard happy.

**Output schema** (JSON, enforced and validated; an invalid item is treated as UNSURE):

```json
{"items":[{"id":"c3","verdict":"VIOLATION|OK|UNSURE",
  "claim_quote":"<exact words from the sentence>",
  "seed_quote":"<exact line fragment from the seed, or empty when the claim is unsupported>",
  "reason_code":"optional_as_planned|included_as_optional|near_as_at|difficulty_unsupported|share_unsupported|superlative_unscoped|brief_leak|naming_leak|same_claim|orphan_opener",
  "repair_hint":"<≤ 20 words>"}]}
```

No numeric confidence. Self-reported confidence from these models is not calibrated, and F9 flip-flopped 10 times in S234. "Confident" means the following, all of which are deterministic or cross-model:
1. The verdict is VIOLATION, not UNSURE.
2. `claim_quote` is in the sentence and `seed_quote` (where the class requires one) is in the seed, both checked after accent folding and whitespace normalisation (`hygiene.fold`).
3. `reason_code` matches the candidate's class.
4. For holds, the confirm model agrees.

UNSURE and OK never produce a finding.

**`repair_hint`** goes into the sentence-repair PROBLEM text, as F17 problems do today. The repair therefore knows *which* fact to keep, for example "keep the boat ride, mark it optional".

**Prompt-injection surface.** Tenant brief text and seed text are data. The only thing the model's output can do is name candidate ids that already exist and quote substrings. It cannot create a finding on a sentence that is not a candidate, and it cannot hold anything by itself (I3, I4).

---

## 5. Precision safeguards: why clean copy is not held

For a clean sentence to end up holding a piece, **all** of these must go wrong together:

1. The broad candidate generator picks it. This happens often by design, and is harmless.
2. Deterministic pre-clear does not remove it.
3. gpt-6-luna returns VIOLATION with the matching `reason_code`.
4. Both quotes verify. A false VIOLATION on a contradiction class (1, 2, 3, 8) usually cites a seed line that does not contradict, or paraphrases one that does not exist. The substring plus token check rejects both.
5. The class is in `hold` mode, which only classes 1, 2 and 5 reach in the first release.
6. The sentence repair runs, and the re-adjudication of the *repaired* sentence is still VIOLATION.
7. An isolated call on a different model (gpt-5.6-luna) returns VIOLATION with verified quotes.

Illustrative compound rate for a clean candidate:
- Stage 1 false VIOLATION: ≤ 5%.
- Quote verification passes a false VIOLATION: ~50% for contradiction classes, ~100% for absence classes. For absence classes the deterministic "no support" test in step 2 is the counterweight.
- Still flagged after repair: ~30%.
- Confirm model agrees with a wrong stage 1: ~30%, assuming correlated errors.

That gives 0.05 × 0.5 × 0.3 × 0.3 ≈ **0.2% per clean hold-class candidate**, or ≈ 0.45% for absence classes. A blog has about 7 hold-class candidates (§9.1), so the prior is about 1–2% of clean blogs held wrongly. That is **not good enough on priors alone**, which is why classes reach `hold` only after phase 4 measures a real rate (§10). Two levers lower it further:
- A held piece goes to admin review. It is not lost, but it is still a false hold.
- The per-class kill switch (§8) demotes a class to `repair` on the first labelled wrong hold.

By contrast, `repair` mode for a clean sentence costs one sentence repair (about $0.012, Report 12 §1.1) under the existing AA-528 regression guard. A clean sentence is rewritten, never held.

---

## 6. Expected precision and recall per class

These numbers are **priors, not measurements**. The panel gives only 1–3 positives per class (the known misses pinned in `test_aa789_t10_recall.py`), so any recall figure from them alone has a 95% CI wider than ±40 points. Phase 1 (§10) replaces these priors with numbers from the labelled set plus fault-injected positives.

| # | Class | Candidate recall | Adjudicator recall | End recall (≈) | Precision of VIOLATION + verified (stage 1) | Precision of a hold (stage 1 + confirm + post-repair) | Reasoning |
|---|---|---|---|---|---|---|---|
| 1 | Optional as planned | 0.95 | 0.85 | **0.80** | 0.93–0.97 | ≥ 0.98 (target) | The seed carries explicit OFFERED / INCLUDED status lines (`Moment.statuses`), which makes this local reading comprehension with a citable anchor. Misses come from activities named by a synonym the token match does not know. |
| 2 | Reverse flip | 0.95 | 0.85 | **0.80** | 0.95–0.98 | ≥ 0.98 | The same structured anchor. The marker lexicon is small and closed. |
| 3 | Near vs at | 0.70 | 0.80 | **0.55** | 0.85–0.93 | n/a (repair) | The phrasing varies ('lunch in the village outside X'), and some 'at X' is fine when X is a district. That is judgment, so repair only. |
| 4 | Difficulty promise | 0.85 | 0.75 | **0.65** | 0.80–0.90 | n/a (repair) | 'Easy' or 'gentle' can be a fair reading of 'short walk'. The panel's bar is subjective, so repair only. |
| 5 | Share of the world | 0.90 | 0.85 | **0.75** | 0.92–0.97 | ≥ 0.98 | Deterministic pre-clear removes seed-backed figures. What remains is mostly truly unsupported. |
| 6 | Scopeless superlative | 0.90 | 0.70 | **0.60** | 0.80–0.90 | n/a (repair) | Scope comparison ('in Mongolia' vs unscoped) is subtle, and the round-3 false positive was exactly this kind. |
| 7 | Brief recipe leak | 0.90 when brief text is available, 0.6 when not | 0.85 | **0.75** | 0.90–0.95 | n/a (cut) | With `brief_texts`, the anchor is a real substring. 'One driver, one guide, one pick-up point.' is copy, and the adjudicator sees there is no brief line behind it. |
| 8 | Naming-note leak | 0.90 | 0.80 | **0.70** | 0.85–0.93 | n/a (repair) | A pronunciation FAQ answer is legitimate. The `Naming:` line anchor helps tell the two apart. |
| 9 | Paraphrased repeat | 0.80 | 0.75 | **0.60** | 0.80–0.90 | n/a (cut) | "Adds nothing" is graded, and day-section repeats are legitimate. Pre-clear removes the round-3 day-section pair. |
| 10 | Orphan opener | 0.85 | 0.80 | **0.70** | 0.85–0.92 | n/a (repair) | Local and easy to judge with the heading. |
| 11 | FAQ answer fit | 1.0 (all pairs) | S247 trial: 3/3 found | 0.8 (prior) | S247: 0 false drops in 31 pairs | n/a (drop) | Existing module, measured only on n = 31. |

At the piece level, against the §1.3 gap list: about 9 of the 11 classes go from 0% caught to roughly 55–80% caught (end recall).

What holds:
- **Today**, a stage-1 false positive in a repair class costs a sentence rewrite, not a hold.
- **Hold-capable classes in the first release:** 1, 2 and 5. All three have a deterministic anchor on both sides, and they are the fact defects the panel treats as deciding (an "optional flipped" or invented trip detail decides 9 pieces).

---

## 7. Cost

Unit prices come from `docs/generated/llm-routes.md` (`shared.llm_model_catalog` snapshot 29/10):
- gpt-6-luna: $0.10 per 1M tokens in, $0.50 per 1M out.
- gpt-5.6-luna: $0.20 in, $1.20 out.
- Sonnet (FAQ fit): $3 in, $15 out.

These models are reasoning models, so most output is reasoning tokens. Empirical anchor: the F9 v2 arm V2a on gpt-6-luna logged 76 calls, 124k tokens in and 184k out, for $0.1014. That is **$0.0013 per call at about 1.6k in and 2.4k out** (05-f9v2-replay).

| Call | Tokens in (est.) | Tokens out incl. reasoning (est.) | $ per call |
|---|---|---|---|
| Stage 1 batch, blog (prompt 1.5k + seed 2.8k + ≤ 8 candidates with context 1.0k) | 5.3k | 3.0k | **$0.0020** |
| Stage 1, LinkedIn (prompt 1.5k + seed 0.6k + 1–2 candidates 0.3k) | 2.4k | 1.5k | **$0.0010** |
| Confirm, isolated, gpt-5.6-luna (seed + 1 candidate) | 4.5k | 1.5k | **$0.0027** |
| FAQ fit, batched, Sonnet (existing; 3 pairs) | 2.5k | 0.3k | $0.012 |

**Per piece**, using the §9.1 volumes and assuming attempt-1 text has about 1.3× the candidates of the final text:

| Component | Blog | LinkedIn |
|---|---|---|
| Stage 1 on attempt 1 | 2.5 calls × $0.0020 = $0.0050 | 0.5 calls × $0.0010 = $0.0005 |
| Re-adjudication of repaired sentences (changed shas only) | 1 call = $0.0020 | 0.1 call = $0.0001 |
| Confirm (hold classes, still-failing VIOLATIONs only) | 0.5 × $0.0027 = $0.0014 | 0.05 × $0.0027 = $0.0001 |
| **Adjudicator subtotal** | **≈ $0.008** | **≈ $0.0006** |
| Extra sentence repairs from new true findings (≈ 0.6 per blog, 0.1 per LinkedIn, × $0.012) | $0.007 | $0.0012 |
| FAQ fit (existing module, once switched on) | $0.012 | n/a |
| **All-in, blog / LinkedIn** | **≈ $0.027** (≈ $0.015 without FAQ fit) | **≈ $0.002** |

For scale: today's F9 judge costs $0.005 per piece, and a full S234 piece cost about $0.053 ($4.231 / 80). If both stage rows fall back to gpt-5.6-luna, the adjudicator subtotal is about 2.3× higher: $0.018 per blog.

**Monthly** (mix 40% blog / 60% LinkedIn, all-in including FAQ fit):

| Volume | Pieces per month | $ per month |
|---|---|---|
| Dev today (eval and regeneration runs only, no tenants) | ~100 | **≈ $1.2** |
| 10 tenants × 30 pieces | 300 | **≈ $3.6** |
| 50 tenants × 40 pieces | 2,000 | **≈ $24** |

Shadow costs the same calls as live mode, so phase 2 on Dev is about $1–2 in total. Every call is a `shared.llm_call_log` row under stages `t10_adjudicate` and `t10_adjudicate_confirm`, so the wave or report cost-per-stage rule applies without extra work.

---

## 8. Feedback loop (calibration and the Writing memory disagreement queue)

1. **Every candidate is stored**, whether VIOLATION, OK, UNSURE, pre-cleared or overflow. It goes in `writer_input.t10_adjudication`, per attempt: class, sentence sha256, char offsets, verdict, quotes, `verified`, model, prompt version, latency, and the mode in effect. The text stays on the piece row (tenant erasure covers it). Exports carry shas and offsets only.

2. **The disagreement queue** reuses Writing memory signals (`shared.writing_signal`, ADR 0010). There are two disagreement types:
   - **False alarm.** An admin dismisses an adjudicated finding (`action='dismiss'`, `gate` F17/F18/F13, the finding's class in `locator`).
   - **Miss.** An admin or tenant cuts or rewrites a sentence (`sentence_cut`, `sentence_rewrite`, `tenant_edit`) whose sha matches a candidate the adjudicator **cleared** (OK, UNSURE or pre-cleared), or a sentence that was never a candidate. The second case is a generator recall gap.

   A new "T10 adjudication" filter on the Signals tab lists both types. The filter is a join on sentence sha. No new table is needed if the dismiss path writes the class into `locator`. If the existing actions cannot carry it, one migration adds a `t10x_dismiss` action, following the reason-code-first rule (CHECK before code).

3. **Sampling for labels.** The labelling pass covers:
   - every VIOLATION in a hold class;
   - 10% of OK verdicts per class per week, minimum 5;
   - every UNSURE.

   Claude Code runs the labelling with an agent panel, and the tech lead approves (standing practice). Labels are pass/fail per `(piece, sentence_sha, class)`. They are stored in the S234 label-pack format (Report 12 §1.5 #1, `content_piece_label`) or as `fact_status` on the signal.

4. **What the labels drive.**
   - **Per-class rolling precision and miss rate**, on a weekly report row next to the R2 calibration (`writing_memory/calibration.py` already computes confusion and κ per stratum and can take these verdicts).
   - **Automatic kill switch.** A hold class whose labelled hold precision drops below 0.98 over the last 50 confirmed verdicts, or that has *any* labelled wrong hold, is demoted to `repair` in config by the weekly job. Promotion is always by hand.
   - **Few-shot and prompt updates**, only through the ADR 0010 release flow. A disagreement becomes a candidate exemplar. R0 replays the stored verdicts at $0 (`adjudication_results`), R2 re-judges the labelled set (paid, small), and only then does the prompt version change. Labels never change the prompt directly. That avoids Goodhart: the adjudicator does not learn from its own verdicts.
   - **Generator recall gaps** (misses on non-candidates) become new candidate patterns plus unit tests. Recall can widen safely because the generator cannot hold anything (I1).

---

## 9. Latency

9.1 **Measured candidate volume** ($0, offline, revision-free prototype regexes over the 40 S234 stored final texts; script at `/tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/e18d5b85-2701-4bbf-9145-f2678da5693b/scratchpad/cand_count.py`; counts only):

| Per piece (mean / max) | Blog (n = 16, 49.6 sentences) | LinkedIn (n = 24, 9.7 sentences) |
|---|---|---|
| optional_planned (activity token of an OFFERED line) | 2.1 / 6 | 0 |
| optional_flip marker | 1.2 / 3 | 0.04 / 1 |
| near_at | 0.1 / 1 | 0.2 / 1 |
| difficulty | 1.4 / 4 | 0 |
| world_share | 4.0 / 7 | 0 |
| superlative | 3.0 / 6 | 0.3 / 1 |
| recipe | 0.1 / 1 | 0 |
| naming | 0.9 / 2 | 0 |
| orphan opener | 0.6 / 2 | n/a (no headings) |
| paraphrase pairs (J ≥ 0.35) | 1.9 / 4 | 0 |
| **Total candidate hits** | **≈ 15.3 (≈ 12 unique sentences)** | **≈ 0.5** |
| FAQ pairs (existing module) | 3.0 / 5 | 0 |

For comparison, the *findings* each revision adds on the same texts:
- **Rev 1 (`05b175e3`, the broadest)** adds 13 findings over 40 pieces relative to `main`: F18 +3, F17 +2, F13_leak +3, F13_repeat +2, F15 +1 (`aa789_recall_replay.py compare`). Each of those would have been a hold-capable or blocking finding with no adjudication, and three verifier rounds showed that kind fires on clean copy.
- **Approach C** turns about 12 sentences per blog into *questions* instead.

9.2 **Latency estimates** (to be measured in shadow from `llm_call_log.latency_ms`):
- One gpt-6-luna reasoning call with about 5k in and 3k out: 6–15 s.
- Blog: 1–3 parallel calls, so **+8–18 s per attempt**, plus up to one confirm call (+5–10 s) only on the hold path.
- LinkedIn: **+0 s for about half of pieces** (no candidate after pre-clear), +5–10 s otherwise.

T9 blog generation already takes minutes per attempt, so this is acceptable. Shadow gate: p95 ≤ 30 s added per attempt. Step timeout: 45 s, then fail open (I2).

---

## 10. Rollout with measurable gates

| Phase | What runs | Cost | Gate to advance (all must hold) |
|---|---|---|---|
| **P0: build and offline eval at $0 (this week)** | Generator + pre-clear, adjudicator module with a stub/fixture client, `verify_evidence`, `to_findings`, mode flags, the I1–I6 tests, replay script, labelled eval set. | $0 | (a) Generator recall ≥ 0.95 on all positives (the 1–3 panel examples per class + **≥ 15 fault-injected positives per class**). (b) Mean candidates ≤ 20 per blog and ≤ 3 per LinkedIn. (c) I2: ledger byte-identical to `main` on the 40 pieces and all round 1–3 clean sentences with the adjudicator off, stubbed or raising. (d) `verify_evidence` rejects 100% of a hand-built set of fabricated quotes. (e) Prompt token count per call within ±20% of §7 (counted, not called). |
| **P1: offline paid eval** (needs acc3 Bedrock unblocked, or OpenAI credit for `gpt-6-luna-openai`) | Stage 1 + confirm on the labelled set, 3 repeats. | **≈ $1.5**: about 260 candidates in ≈ 90 batched calls × 3 repeats × $0.002, plus confirm ≈ 60 × $0.0027, plus margin. Cap $3. | Per class: (a) **clean FP rate**: VIOLATION + verified on clean candidates ≤ 1% for repair classes, and **0 in ≥ 300 clean candidates** for hold classes (one-sided 95% upper bound ≤ 1%). Implied precision ≥ 0.98 at the observed prevalence. (b) Recall on positives ≥ 0.70 for hold classes, ≥ 0.55 for others. (c) Test-retest verdict agreement ≥ 0.90 across 3 runs. (d) ≥ 95% of VIOLATIONs pass quote verification; a lower rate means the prompt is wrong. (e) $/piece within ±30% of §7. |
| **P2: shadow on Dev** (`T10X_MODE_*=shadow`, `T9_FAQ_LLM_FILTER=shadow`) | Live writer path. Verdicts are recorded, and pieces are delivered unchanged. Pieces come from eval and regeneration runs (Dev has no tenants, so we generate the evidence now rather than wait). | ≈ $1–2 for 100–150 pieces | (a) ≥ 100 pieces, ≥ 40 of them blogs. (b) Agent-panel labels on every VIOLATION plus 10% of cleared: hold-class precision ≥ 0.98, repair-class precision ≥ 0.90. (c) Miss rate in the cleared sample ≤ 15%. (d) Fail-open rate ≤ 2%. (e) p95 added latency ≤ 30 s. (f) 0 regressions on the existing ledger (I2 in production: compare the stored ledger with and without the adjudicated findings). |
| **P3: repair mode** (classes 1–10 in `repair`) | Adjudicated findings block attempt 1 and get a sentence repair or cut. Never a hold. | +$0.007 per blog for repairs | (a) Repair success ≥ 70% (F17 today: 77%). (b) AA-528 regression-guard reverts ≤ 10% of adjudicated repairs. (c) Repair-class precision stays ≥ 0.90 on the weekly sample. (d) No rise in F9 flip-flop holds. |
| **P4: hold mode, classes 1, 2, 5 only** | I4 chain live. | +$0.0014 per blog (confirm) | (a) After the S246 4-week freeze on new blocking behaviour (≈ 18/11) **and** the tech lead's approval. This is a new hold path, even though no new gate is added. (b) ≥ 200 pieces in P3 with 0 labelled wrong confirmations in the hold classes. (c) Kill switch tested: a forced wrong label demotes the class in the next weekly run. Classes 3 and 6 can be proposed for hold only with their own P3 evidence at the same bar. |

---

## 11. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Bedrock on acc3 stays blocked | No adjudication at all, so no recall gain. Nothing breaks (fail open). | The fallback route `gpt-6-luna-openai` (OpenAI API, already the fallback for `t10_judge`) once credit is loaded. Data leaves AWS on the same terms as today's `t10_judge` fallback. |
| Verdict instability (F9 had 10 flip-flops in S234) | The same sentence flips between attempts and causes repair loops. | `AdjudicationMemory` makes verdicts sticky per (sentence sha, seed sha, prompt version). Only changed sentences are re-judged. Holds need cross-model agreement. P1 gate (c) checks test-retest. |
| Correlated errors between the two OpenAI-vendor models | The confirm step adds less independence than assumed (§5). | Measure confirm-given-wrong in P1. If it is > 50%, move confirm to a different vendor. Haiku on acc3 as a `validate` confirm is not possible as a `judge` (ADR 0008), so the alternative is deterministic-only confirm for hold classes, which is already required for classes 1, 2 and 5. |
| Support for a claim lives in another moment or in Facts | False "unsupported". | The full own seed plus Facts go in every call (§4). Pre-clear runs the deterministic support test on the whole source. |
| Candidate explosion on long blogs | Cost and latency grow. | Cap of 24 with logged overflow, grouping by moment, pre-clear. |
| Few real positives (1–3 per class) | Recall numbers mean little. | ≥ 15 fault-injected positives per class (deterministic string edits on light pieces, plus Claude-written synthetic paraphrases, $0). Recall is reported per source (panel vs injected). |
| Golden-text guard | Labels or fixtures leak real copy into the repo. | The labelled set stores `(piece_id, sentence_sha, offsets, class, label)` only, and text is rebuilt from the gitignored export at run time. Few-shots and tests are synthetic and marked as such (the AA-789 test convention). |
| Goodhart / feedback poisoning | The prompt drifts towards what the adjudicator already believes. | Only human or panel labels feed changes, and only through the ADR 0010 release flow (R0 at $0, then R2). |
| Prompt injection via brief or seed text | A forged verdict. | The output can only reference existing candidate ids and quote substrings. Quotes are verified. No hold without I4. |
| Scope creep into F9 territory (claim-level unsupported, 90 claims in r4) | Duplicate checks, double repairs. | This design covers only the 11 listed classes. Generic unsupported claims stay with F9 / F9 v2. A sentence that already has a deterministic blocking finding is skipped (§2). |

---

## 12. Effort

| PR | Repo | Content | Days |
|---|---|---|---|
| PR1 | CIS | `t10_candidates.py` (generator + pre-clear; rev 1–3 regexes resurrected from git plus the structured `Moment.statuses` / `Naming:` joins), I1 lint test, `scripts/aa789_candidates_replay.py` (counts only), unit tests with synthetic positives and all round 1–3 clean negatives | 1.0 |
| PR2 | CIS + migration via DB Migrate | `t10_adjudicate.py` (prompt v1, schema, batching, `verify_evidence`, `AdjudicationMemory`, confirm, fail open, `llm_call_log` rows), two stage rows + `SAFE_DEFAULTS`, registry prefixes, fixture replay (`adjudication_results`), I2 and I3 tests. Migration and CI routing count as risky, so an agent review comes first. | 1.5 |
| PR3 | CIS | Wiring in `run_quality_gates` / `service.py` behind per-class mode flags (default `off`, then `shadow`), the `never_holds` I4 clause, `writer_input.t10_adjudication` persistence, admin read-only tab in `/admin/atom-curation` + BFF route (aa-ui-verify) | 1.5 |
| PR4 | CIS (+ maybe 1 migration) | Disagreement join and Signals filter, weekly calibration row + kill-switch job, label import | 1.5 |
| PR5 | CIS | Switch P3 (repair) on, then later P4 (hold, classes 1, 2, 5). Flags and config only, plus evidence in the implementation notes. | 0.5 |
| Root PR | root | Design doc into `docs/research/`, P1/P2 audit reports into `docs/audits/<date>-S<nnn>-aa789-adjudicator/` | 0.5 |
| **Total** | | 5 CIS PRs, 1–2 migrations, 1 root PR | **≈ 6.5 dev days**, plus P2 shadow runtime (hours of generation on Dev, not days of waiting) |

---

## 13. What can be built this week at $0, and what needs paid calls later

**$0 this week (no LLM API calls, no DB writes):**
- PR1 complete, with candidate recall and volume measured on the 40-piece export and the injected positives (P0 gates a and b).
- The labelled candidate set:
  - generator output on the 40 pieces, about 200 blog candidates plus about 12 LinkedIn;
  - the round 1–3 clean sentences;
  - ≥ 15 injected positives per class.

  Claude Code labels it with an agent panel at no metered cost, and the tech lead approves. Only shas, offsets and labels go in the repo.
- PR2's module with a stub client. `verify_evidence` is tested against fabricated quotes. Prompt token counts give a counted (not guessed) cost per piece.
- Prompt debugging as a dry run: Claude Code subagents play the adjudicator on 20 candidates to find unclear class definitions. This is **prompt QA only**. Its verdicts are not evidence for gpt-6-luna precision.
- PR3 wiring with every mode at `off`/`shadow` and the stub in place. I2 is proved byte-identical on all stored pieces.
- PR4's join, report and kill-switch logic on synthetic signals.

**Needs paid calls later** (after the acc3 Bedrock unblock or OpenAI credit, each with an explicit cap):
- P1 offline eval: about $1.5 (cap $3). It is the only way to measure the adjudicator's precision and recall.
- P2 shadow on Dev: about $1–2 for 100–150 pieces.
- P3 and P4 ongoing: about $0.015 per blog and $0.002 per LinkedIn (adjudicator plus extra repairs), plus $0.012 per blog if FAQ fit is on. That is ≈ $1–4 per month at Dev or early-tenant volume and ≈ $24 per month at 2,000 pieces.
