# Pooled F9_cta_fact re-flag rate after sentence repair (S245, 20/10/2026)

Status: **run done, cases classified, fix (a) written** (CIS branch `fix/f9-sticky-carry-over-repaired-sentences`,
not merged yet). The $0 counterfactual replay is done; the optional live r8 waits for the shared paid round.

Agent: Claude Code. Cost so far: $0 (read-only DB, no LLM call). Issue: the AA-777 residual, pooled over the r5–r7
retries.

## 1. Question

After the AA-777 fixes (sticky pass #761, r6 fixes 1–3 in CIS #767), how often does a retry *add* a blocking
fail? The issue asks for this over enough retries (n ≥ 60) to beat the noise of a single round (n ≈ 25). The target is
≤ 8%. The title names F9_cta_fact; the problem statement names the "retry added a blocking fail" metric. Both are
reported.

Done when (quoted from the issue):

> * The pooled rate over n ≥ 60 retries is reported, with a 95% interval.
> * Either the pooled rate is ≤ 8%, or one fix ships and a re-measure (≤ $1.5) shows ≤ 8% on the pooled set.

The classification is the issue's **Scope 2**, not a Done-when line: "Classify each retry-added fail: real new fault,
F9 re-judging the repaired sentence, or a judge quote spanning two sentences." This audit uses:

- **C1**: a real new fault (the repair writer, or a full rewrite, added an unsupported claim);
- **C2**: F9 judging again a sentence it had passed, either one the repair edited or one it left unchanged;
- **C3**: a judge quote that spans two sentences.

## 2. Inputs

| Set | Pieces | Retries | Source |
|---|---|---|---|
| S235_r5 | 20 | 26 | `BASE_SETS` in `.tmp-session/s239/aa777_r7_readout.py` |
| S239_r6 | 20 | 26 | `../2026-10-16-S239-in-progress-audit/aa777-r6/readout_stdout.json` |
| S239_r7 | 20 | 23 | `../2026-10-16-S239-in-progress-audit/aa777-r7/readout_stdout.json` |
| S239_aa768_pre761 / r6_aa768 / r7_aa768 | 5 / 5 / 5 | 9 / 8 / 8 | same readouts |
| natural_post_r7 | 1 | 1 | T9 pieces created after 2026-10-16T08:12Z that are in no set above (one tenant job) |
| S234_r4 (reference only, before the sticky pass) | 20 | 32 | `BASE_SETS` |

The r6 cases were classified before in `../2026-10-16-S239-in-progress-audit/aa777-r6/diagnosis.md`. That reading is
reused here and agrees with the dump.

## 3. Method

- **Script:** `script/s245_f9_pool.py`, a copy of `.tmp-session/s245_f9_pool.py` as handed to the run. It ran in the
  CIS api container through the S3-presigned ECS exec on 2026-10-19T23:50Z. It connects with the container's
  `DATABASE_URL` (role `cis_app`), with `ssl="require"`, inside one read-only transaction. The full output went to
  `s3://…/scripts/out/s245_aa865_pool.json` and is saved here, unchanged, as `pool.json`.
- **Metric:** `reconstruct()` and the "retry added a blocking fail" rule are copied from the S239 r7 readout, which
  is itself a port of S234 `fr_analyze.py`. The run reproduced every committed per-round number
  (`reproduction_all_match: true`: r4 4/32, r5 1/26, pre761 1/9, r6 4/26, r6_aa768 0/8, r7 3/23, r7_aa768 1/8).
  No piece was missing or excluded, and the AA-791 ledger snapshots never disagreed with the feedback lines.
- **Interval:** Wilson score interval, 95%.
- **Case dump:** one record per retry that added a blocking fail (14 in all sets). Each record holds:
  - the piece, the tenant slug (the field is called `slug` in `pool.json`; it is the `tenant_slug`), the channel
    and the attempt;
  - the repair targets of the base attempt (gate plus the quoted sentence);
  - for each F9 claim: the claim, the judge's reason, the located sentence, the sentence before it, and the number
    of sentences the quote spans;
  - whether that sentence was unchanged since the base attempt, and a heuristic `suggested_class`.
- **Limit that matters for §5.** `content_piece` keeps the final text and one discarded attempt. For a 3-attempt
  piece the attempt-1 text is gone, so for every k = 2 case "unchanged" was guessed from the repair targets (Jaccard
  < 0.5 with every target). That guess is wrong three times (see §5): a target the repair rewrote heavily scores
  under 0.5. The classes below are set by reading each case, not by the hint.

## 4. Pooled rate

From the run (`pool.json` → `pools`). "Any" is the issue's headline metric, "F9" the title's.

| Pool | Pieces | Retries | Any blocking fail added | F9_cta_fact added | Any, ignoring F17 adds |
|---|---|---|---|---|---|
| **primary r5 + r6 + r7** | 60 | 75 | **8 = 10.7% [5.5%, 19.7%]** | 6 = 8.0% [3.7%, 16.4%] | 6 = 8.0% [3.7%, 16.4%] |
| + the three AA-768 sets | 75 | 100 | 10 = 10.0% [5.5%, 17.4%] | 6 = 6.0% [2.8%, 12.5%] | 7 = 7.0% [3.4%, 13.8%] |
| + natural_post_r7 | 76 | 101 | 10 = 9.9% [5.5%, 17.3%] | 6 = 5.9% [2.8%, 12.4%] | 7 = 6.9% [3.4%, 13.6%] |
| current code (r7 + r7 AA-768) | 25 | 31 | 4 = 12.9% [5.1%, 28.9%] | 3 = 9.7% [3.4%, 24.9%] | 4 = 12.9% [5.1%, 28.9%] |
| reference S234_r4 (before the sticky pass) | 20 | 32 | 4 = 12.5% [5.0%, 28.1%] | 4 = 12.5% [5.0%, 28.1%] | 4 = 12.5% [5.0%, 28.1%] |

By repair mode, primary pool: 73 sentence repairs (8 adds, 6 F9), 1 truth cut and 1 truth cut + sentences (0 adds).
Natural traffic since r7 is a single retry, so it adds nothing to the evidence.

**Verdict on the first Done-when line: met** (n = 75 ≥ 60, Wilson 95% reported). **Second line: not met by
pooling alone.** The headline rate is 10.7% > 8%. F9 alone is exactly at 8.0%, but its upper bound is 16.4%.

## 5. Classification of every retry-added fail

All 14 cases in the dump. Read from `pool.json` (claims, judge reasons, repair targets, F9 judge calls per attempt)
and the r6 diagnosis. "Hint" is the script's `suggested_class`; where it is wrong, the evidence says why.

| # | Set | Piece | Ch. | k | Gate added | Flagged sentence (short) | Location | Class | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| 1 | r4 (ref) | bb776a54 | blog | 3 | F9 | "…the camps are where they are because the forest requires it…" | unchanged (base text stored) | C2 | Same sentence passed at attempt 2; r4 had no sticky pass. |
| 2 | r4 (ref) | 71ad6b1f | LinkedIn | 2 | F17 + F9 | "…like the swim and lunch break at Kuang Si before the afternoon's next move." | **repaired** (hint: unchanged) | C1 | F17 is deterministic and flags this sentence at k but not at k−1, so the sentence changed: the F15 repair added "before the afternoon's next move". |
| 3 | r4 (ref) | 9594430b | blog | 3 | F9 | "…meet at a visible, crossable boundary." | unchanged (base stored) | C2 | Passed at attempt 2, no sticky pass in r4. |
| 4 | r4 (ref) | 5939df86 | blog | 3 | F9 ×3 | "…over the decades…", "…within the national park…", "The journey through the lake region passes the ruins…" | unchanged (base stored) | C2 | All three passed at attempt 2. |
| 5 | r5 | ccb0843c | blog | 2 | F9 ×2 | (a) "The reason is ecological: …the quality of light…"; (b) "The ruins of an ancient monastery… stand within this region." | (a) unchanged; (b) **repaired** (hint: unchanged) | C2 | (a) not a target, neighbour not a target. (b) the F17 thin-coda target "The journey through this part of northern Mongolia closes with… the ruins… which stand as a quiet register of what this region has also lost." rewritten: the location claim was in the passed sentence, now explicit with "within". r5 ran before the sticky pass. |
| 6 | pre761 | dde74641 | blog | 3 | F17 | "At Khaiphaen Restaurant, the first evening brings…" | repaired | C1 | The F9 repair added "the first evening". |
| 7 | r6 | a3d82ff1 | LinkedIn | 2 | F17 | "…means the afternoon starts with space…" | repaired | C1 | r6 diagnosis R1: the F9 repair added a time. Fixed by #767 fix 1 (F17 post-check). |
| 8 | r6 | 17125e0c | LinkedIn | 2 | F9 | "After a short trek through forested hills, Day 2 brings you…" | unchanged, neighbour repaired | C2 | r6 diagnosis R3. Fixed by #767 fix 3 (no referent opener → key on the sentence alone). |
| 9 | r6 | a2133050 | blog | 2 | F9 | "Before leaving this part of northern Mongolia, the route passes the ruins…" | repaired, **deletion only** | C2 | r6 diagnosis R4: the F17 repair cut the clause "a single, spare reminder…" and the word "also". |
| 10 | r6 | 263e5a5a | LinkedIn | 2 | F17 | "The afternoon has room for swimming…" | repaired | C1 | r6 diagnosis R2. Fixed by #767 fix 1. |
| 11 | r7 | 31b91e79 | blog | 2 | F9 | "A lake this large… shapes everything around it… communities sustained by its shores…" | repaired, style edit | C2 (borderline C1) | The F15 target "…exerts a gravitational pull on everything around it: the climate, the soil, the species, and the human communities who have organised their lives around its shores…" passed F9 at attempt 1. The repair made the figure literal ("shapes", "sustained"); the judge flagged the causal claim the old sentence already made. |
| 12 | r7 | 3aa22704 | LinkedIn | 2 | F9 | "The sacred cave at the heart of the site draws Bhutanese Buddhist pilgrims who consider a visit here a spiritual obligation." | unchanged, neighbour repaired | C2 | Not a target. It opens on "The", so its key carried the hook before it, and the F14/F15 repair rewrote that hook ("Guru Rinpoche is said to have flown…" → "In the 8th century, Guru Rinpoche meditated in a sacred cave here…"). New key, judged again, flagged. |
| 13 | r7 | 4dd0e729 | blog | 2 | F9 | "It is a practical stop for lunch before the group continues north toward the lakeshore." | **repaired** (hint: unchanged) | C1 | The F17 target "It is a practical overnight stop that also gives families time to rest before the longer drive north on day four." follows the same Sod Camp sentence and has the same frame. The repair turned the overnight stop into a lunch stop; the source says overnight. A real new fault, rightly flagged. |
| 14 | r7 AA-768 | ebfff6f3 | blog | 2 | F18 | "Most travellers who have moved through markets across Asia…" | full rewrite | C1 | The full rewrite added a rarity generalisation. |

Totals:

| Pool | C1 real new fault | C2 F9 re-judging | C3 two-sentence quote |
|---|---|---|---|
| primary r5–r7 (8 cases) | 3 (#7, #10, #13) | **5** (#5, #8, #9, #11, #12) | 0 |
| all 14 cases | 6 | 8 | 0 |

C2 splits into: unchanged sentence whose key changed (#8, #12, plus #5a), repaired by deletion only (#9), repaired
with new words (#5b, #11). No C3 case is left after #767 fix 3 split multi-sentence quotes. Two of the three C1 cases
in the primary pool (#7, #10) are already fixed on main by #767 fix 1.

## 6. Decision: fix (a), extend the sticky pass

C2 dominates (5 of 8), so the issue's Scope 3 applies. Fix (a) is chosen over (b):

- (b) "F9 on a repaired sentence warns instead of blocks" would also wave through #13, a real new fault (overnight →
  lunch stop). That breaks the writer source-fidelity policy: never promise what the source lacks.
- (a) only stops F9 from judging again what an earlier verdict of the same piece passed and the repair did not change.

What fix (a) does (CIS `services/acp_content_writing/quality_gates.py`, `F9PassMemory` + `_f9_carry_keys`): the job
memory also keeps the text the last F9 verdict judged. Before the sticky filter, each new sentence takes over the
pass of the old sentence it came from when:

1. the old sentence passed F9, and
2. the new one is the old one or a **deletion-only** edit of it: the old words in the same order with some removed;
   a removed run sits at the start or end, between two punctuation breaks, or is only filler adverbs ("also",
   "very"…); no negation, hedge or option word is removed ("not", "optional", "about", "can", "if", "said"…); no new
   symbol; and
3. a referent opener keeps its antecedent: the sentence before it is the same, a deletion-only edit of the old one,
   or, for a definite noun phrase opener ("The sacred cave…"), still holds every content word the sentence shared with
   its old neighbour. A pronoun after a rewritten neighbour ("It was founded in 1692.") is still judged again.

Covered: #9 (deletion only) and #12 (unchanged, definite-noun-phrase opener). Not covered, on purpose: #5b and #11
add words, and accepting synonyms would need a judgement the code cannot make safely; #13 and #14 are real faults. A
plain set (any other caller) and attempt 1 behave exactly as before. 30 unit tests, including these before/after
pairs; the full CIS unit suite passes (8693 passed, 1 skipped).

## 7. Re-measure

### 7.1 $0 counterfactual replay (done)

`script/s245_f9_counterfactual.py` replays the rules on every F9 item of `pool.json`, importing `_f9_key`,
`_f9_deletion_only` and `_f9_antecedent_kept` from the CIS fix branch. For k = 2 cases the attempt-1 sentence and
its neighbour come from the §5 reading (table `REVIEWED` in the script). Output: `counterfactual_stdout.json`.

Check: replaying the **current** main rule on the current-code pool removes nothing (4/31 stays 4/31), which is
what the live r7 run showed. On the primary pool it removes only #8, which #767 fix 3 fixed.

| Pool (retries) | Observed | Current main rule | **With fix (a)** | Fix (a) + #767 F17 post-check credited (#7, #10) |
|---|---|---|---|---|
| primary r5–r7 (75), any | 8 = 10.7% [5.5, 19.7] | 7 = 9.3% [4.6, 18.0] | **5 = 6.7% [2.9, 14.7]** | 3 = 4.0% [1.4, 11.1] |
| primary r5–r7 (75), F9 | 6 = 8.0% [3.7, 16.4] | 5 = 6.7% [2.9, 14.7] | **3 = 4.0% [1.4, 11.1]** | 3 = 4.0% [1.4, 11.1] |
| + AA-768 sets (100), any | 10 = 10.0% [5.5, 17.4] | 9 = 9.0% [4.8, 16.2] | 7 = 7.0% [3.4, 13.8] | 5 = 5.0% [2.2, 11.2] |
| + natural (101), any | 10 = 9.9% [5.5, 17.3] | 9 = 8.9% [4.8, 16.1] | 7 = 6.9% [3.4, 13.6] | 5 = 5.0% [2.1, 11.1] |
| current code r7 (31), any | 4 = 12.9% [5.1, 28.9] | 4 = 12.9% | 3 = 9.7% [3.4, 24.9] | 3 = 9.7% |
| reference S234_r4 (32), any | 4 = 12.5% | 1 = 3.1% | 1 = 3.1% | 1 = 3.1% |

Remaining primary adds with fix (a): #5 (r5, "within"), #7 and #10 (r6 F17, already fixed by #767), #11 (r7 style
rephrase), #13 (r7 real new fault).

**Reading.** On the pooled set the re-measured rate with the fix is 6.7% (any) and 4.0% (F9), both ≤ 8% as point
estimates; the 95% upper bounds (14.7%, 11.1%) are still above 8%, which no n ≈ 75 sample can avoid at these rates.
The fix moves the current-code pool by one case only (4 → 3 of 31). The rest of the r7 residual is one real fault
(#13) and one style rephrase (#11), plus one full-rewrite F18 (#14). A live round of about 25 pieces is therefore
expected near 2–3 adds in 30 retries, so it cannot by itself show ≤ 8% with confidence; its value is pooling it with
this set and confirming no regression.

Limits of the replay:
- It assumes a dropped claim changes nothing else in the attempt (the judge's other verdicts and the next repair are
  taken as they were).
- The attempt-1 sentences for k = 2 cases are inferred from the repair targets and the deterministic F17 evidence
  (§5), not read from stored text. #12's old neighbour (the hook) is inferred from the F14 target.

### 7.2 Optional live r8 (orchestrator, shared paid round)

20 + 5 pieces (the r7 piece mix: 20 main + 5 AA-768 requests) on Dev after the CIS fix is deployed, cap $1.5
(r7 cost $0.95), trial 3 pieces first. Re-use `.tmp-session/s239/aa777_r7_enqueue_apply.py`,
`aa777_r7_driver.sh` and `aa777_r7_readout.py` (readout adapted to `DATABASE_URL`/`cis_app`, as the pooling script
does). Report r8 alone and pooled with r5–r7 (n ≈ 105), plus the count of `F9_sticky_carry` log lines (how often the
carry fired) from CloudWatch `/ecs/aa-cis-dev`.
