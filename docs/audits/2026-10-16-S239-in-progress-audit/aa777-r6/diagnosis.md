# AA-777 r6 diagnosis: retry-added fails and holds (S239, 16/10/2026)

Inputs: `readout_stdout.json` (this folder) and `.tmp-session/s239/aa777_focus_dump.json` (8 pieces: `gate_ledger`, `repair_log`, `discarded_attempts`, `content_text`, `writer_input`). Code read: CIS `main` 4646b6f7, which contains the r6 code 90387fb4 (#761).

I ran local probes at $0 and made no AWS/DB calls:
- `sentence_repair.plan()` on the attempt-2 ledgers;
- `trip_facts.timing_claims()` on the sentences before and after repair;
- `trip_facts._thin_extra()` / `_trim_thin()` on the a2133050 coda.

Limits:
- Attempt-1 text is not stored. Only attempt 2 is in `discarded_attempts`, plus the final text. Before-repair sentences are therefore taken from the repair_log feedback quotes.
- The `flags` column (F7_faq_autofix, F13_autofix lines) was not dumped. So the outcome of the F16 FAQ regeneration is not known (see §2.3).

## 1. Summary

| # | Piece | Set | What | Class |
|---|---|---|---|---|
| R1 | a3d82ff1 LinkedIn (trail-pulse) | r6 | k=2 added **F17** ('the afternoon') | **(a)** |
| R2 | 263e5a5a LinkedIn (trail-pulse) | r6 | k=2 added **F17** ('The afternoon') | **(a)** |
| R3 | 17125e0c LinkedIn (trail-pulse) | r6 | k=2 added **F9**, then the guard reverted it | **(b)** |
| R4 | a2133050 blog (atlas-hearth, Mongolia) | r6 | k=2 added **F9**; also held on F17 | **(b)**, plus an F17 thin-coda defect (e) |
| H1 | a2133050 blog | r6 | held **F17_trip_fact** (thin coda) | **(e)** gate/plan defect, with (b) |
| H2 | 89d60686 blog (AA-768 atlas-hearth) | aa768 | held **F17** pace; F9 still failing | **(a)**, plus (e) pronoun lock, plus (b) |
| H3 | 35ee6a3d blog (AA-768 terra-family) | aa768 | held **F9_cta_fact** | **(b)**, plus (e) plan dedupe dropped the F9 item |
| H4 | 1a8dec5d blog (terra-family, Mongolia) | r6 | held **F16_faq** (2 pairs) | **(d)** |
| H5 | 3532ecdd blog (terra-family, Mongolia) | r6 | held **F16_faq** (2 pairs) | **(d)** |

There is no case of (c). Every sentence that carries a new fail is either a sentence the repair was asked to fix or a sentence left unchanged. The repair edited only the items it was given. This is checked against the feedback quotes, because the attempt-1 text is not stored.

Three root causes cover 6 of the 8 cases:

1. **The repair writer adds a time or pace word, and nothing checks the replacement for F17** (R1, R2, H2). F17 is deterministic, yet `splice_checked` only runs the integrity checks (repeat, orphan pronoun, misplaced moment) on a replacement.
2. **The F9 sticky pass misses sentences that did not change** (R3, R4, H2, H3). There are three ways it misses:
   - the key includes the previous sentence;
   - a multi-sentence judge quote never matches a single-sentence key;
   - an edit that only deletes words gets a new key.
3. **`sentence_repair.plan()` drops an F9 item that overlaps an F17 item** (H1, H3). Two things follow. The repair is never told the F9 problem. And because the dropped item is the only truth item, the attempt-3 blog truth cut, which only looks at items whose `gate` is F1/F9, never sees it. This is one reason `blog_truth_cut_entries = 0`.

## 2. Case details

### 2.1 Retries that added a blocking fail (4/26)

**R1 — a3d82ff1, k=2, F17 added (class a).**
- Before (attempt 1, flagged by F9 as an unsupported outcome claim): "Building swim and rest time in before lunch means you **arrive at the afternoon** with energy, not just photos."
- After the repair (t9_write sentence repair; problem = F9): "Building swim and rest time in before lunch means **the afternoon starts** with space to keep going, not just a camera roll to show for the morning."
- F17 at attempt 2: "gives a time the source does not ('the afternoon')". The source only has "before lunch", which anchors *morning*.
- Probe: `timing_claims` returns [] on the old sentence. `_TIME_RE` deliberately skips "at the afternoon" (the S234 'energy, not schedule' carve-out). On the new sentence it flags. The time word was inherited from the flagged sentence, but the repair turned it into a schedule claim, which is a new specific claim.
- The F9 issue was fixed. Attempt 3 dropped "before lunch … afternoon" and the piece was approved.

**R2 — 263e5a5a, k=2, F17 added (class a).**
- Before (attempt 1, F15 sibling repeat; the item was a style problem): "Time to swim and rest is built into the plan before lunch."
- After (t9_write repair, because an F9 item in the same call routed it to Sonnet): "**The afternoon** has room for swimming and resting at the pools before lunch." This is a new time, and it contradicts "before lunch".
- F17: "gives a time the source does not ('The afternoon')". Attempt 3 wrote "Time is left for swimming and resting at the pools before lunch." (the source wording), and the piece was approved.

**R3 — 17125e0c, k=2, F9 added, guard revert (class b).**
- Sentence (unchanged from attempt 1 to attempt 2, and still in the final): "After a short trek through forested hills, Day 2 brings you to the tiered limestone pools of Kuang Si Falls near Luang Prabang."
- F9 passed it at attempt 1 (attempt-1 F9 = passed). At attempt 2 the judge flagged it: "does not state that the trek itself passes through forested hills". At attempt 3 it passed again with the same sentence.
- Why sticky did not drop it: the attempt 1 → 2 repair (Haiku, F15 only) rewrote the **previous** sentence, the hook ("Swim time … isn't a gap in the schedule. It's the schedule." → "Swim time at Kuang Si Falls on Day 2 is the centerpiece of the day."). `_f9_key` = (prev, sentence), so the key changed and the sentence was judged again.
- The guard reverted attempt 2, and attempt 3 fixed the F15 items.

**R4 — a2133050, k=2, F9 added (class b, plus an F17 defect).**
- Before (attempt 1, F17 thin coda): "Before leaving this part of northern Mongolia, the route also passes the ruins of an ancient monastery destroyed during the political purges of 1937: a single, spare reminder that the region's layers of cultural memory extend well beyond its landscape." At attempt 1 F9 passed with this sentence present.
- After (the repair did what the F17 message asked, "cut the added clause"): "Before leaving this part of northern Mongolia, the route passes the ruins of an ancient monastery destroyed during the political purges of 1937."
- F9 at attempt 2: "does not specify their position in the route relative to leaving northern Mongolia". The "Before leaving …" frame was already in the attempt-1 sentence, which F9 passed. Removing words cannot add a claim, but the sentence changed, so sticky does not apply.
- Same sentence, F17 at attempt 2: still "closes on a thin moment … with an interpretation". Probe: `_thin_extra` = `['leaving', 'part', 'northern', 'mongolia']`, which is 4 against the limit of 2. All four extras are in the **leading** clause. `_trim_thin` only cuts a **trailing** appositive, so it returns None. The message ("cut the added clause") gives no hint about the leading frame. Without the frame the sentence has 0 extras (probe).

### 2.2 Held pieces

**H1 — a2133050 (held F17, F9 also failing).** The attempt-2 → 3 repair got one item only. Probe: `plan()` returned one F17 item for "Before leaving … 1937." The F9 item for the same sentence was skipped as "same sentence flagged twice" (`sentence_repair.py:226`), because F17 comes before F9 in the ledger. Three things followed:
- The repair saw only the F17 text, which had already been followed, and the sentence came back unchanged.
- The attempt-3 truth cut found no F1/F9 item, so `_cut_blog_truth_items` returned None and logged no entry.
- The sentence is the last one before "## Plan This Journey…". `delete_flagged` would accept it (not the hook, no pronoun follower), and the blog is 8241 chars, so a cut would have cleared F9 and F17 together.

**H2 — 89d60686 (AA-768 atlas-hearth; held F17 pace, F9 failing).** The causes:
- **(a)** Attempt 1 → 2: the F15 item "For travellers who have moved through markets across Asia, the temptation is to pass through these quickly." was rewritten as "These markets reward a **slower pace** than their size might suggest." The following unchanged "That would be a misjudgement." now makes no sense, and the new sentence is a pace claim. The readout counts this retry as `added: []`, because F17 was already failing at attempt 1 (on 'the morning'). The gate-level metric does not see a new violation inside a gate that is already failing.
- **(e) Pronoun lock.** At attempt 2 → 3 both items were deleted by the repair and then reverted by the integrity check: "opens on a pronoun with no referent: 'That would be a misjudgement.'" and "'They are simply what is made and grown here.'". The truth cut was refused for the same reason (`truth_cut_refused`: "no flagged sentence is safe to cut"). The flagged F9 sentence "The craft objects …: these are not performances of heritage put on for visitors." has failed at every attempt since attempt 1. Its pronoun-led follower ("They are simply …") blocks every deletion and every rewrite.
- **(b)** The final F9 also carries a new claim on "The monastery's meaning is not in any one view of it. It is in the fact that … for over twelve centuries." That text was unchanged since attempt 2 and was not flagged at attempts 1–2. The judge quote spans **two sentences**, so `_f9_located_key` builds a two-sentence key that can never be in the passed set.

**H3 — 35ee6a3d (AA-768 terra-family; held F9).**
- Final F9: "The sunset ride around Luang Prabang is done, **bicycles are leaned against a wall**, and your family is seated at Khaiphaen Restaurant …" The judge calls it invented scene detail, which is a real but low-harm embellishment.
- At attempt 1 this sentence was not flagged. At attempt 1 → 2 the hook repair ('It is the end of your first day in Laos.') was integrity-reverted, so the hook and this sentence stayed the same.
- At attempt 2 the judge flagged a **two-sentence** quote, "Picture the end of your first evening in Laos. The sunset ride … days ahead.", so sticky could not match it.
- `plan()` (probe) kept only the F17 item "Picture the end of your first evening in Laos." and dropped the overlapping F9 item. The repair therefore never saw the bicycles problem. It deleted 'Picture…' through a repeat-guard delete.
- With 'Picture…' gone, the bicycles sentence became the hook with a new previous sentence (the heading). It was judged again and flagged, and the piece was held.
- The truth cut never ran, because there was no F9 item. It would have refused anyway, because the sentence is now the hook.

### 2.3 F16_faq holds (class d)

**H4 — 1a8dec5d and H5 — 3532ecdd.** Both are Terra Mongolia route blogs of the same request, 3bf7a5f7. Each holds at attempt 2 with "ends with 2 FAQ pair(s) … needs at least 3". Both are otherwise clean (`pass_f1_f9` true; only warn gates are left). Here is how they end up held:
- Attempt 1 already had F16 failing. The single FAQ regeneration ran (one `t9_repair/faq_regen` call each), and the FAQ at attempt 2 is the same 2 pairs as at attempt 1. So the regeneration was either not kept (pair count not above `before`, or integrity problems) or dropped back to 2 pairs.
- At attempt 2 no second regeneration is allowed. `faq_fell` (service.py:1596) needs the previous FAQ to have ≥ 3 pairs.
- F16 is not repairable, so with F16 the only blocking fail left, the piece holds.

To find out which branch was taken: read the `flags` column (F7_faq_autofix: "FAQ regeneration not kept (…)" or "dropped FAQ the source cannot answer …") and `quality_signal.unused_facts` of the two `faq_regen` llm_call_log rows. Both are read-only and cost $0. One possible cause, not confirmed: these are the 3rd and 4th blogs of one request, so `unused_source_facts` may be close to empty and the new pairs restate the body.

## 3. Code paths read

- **Repair prompt** (`generate.py:275 _REPAIR_SYSTEM`) forbids new claims, numbers, places, scene detail and promises. It says "when [the PROBLEM] gives a time … drop that part", but nothing stops it from **adding** a time of day or a pace word when the problem is F9 or F15. R1, R2 and H2 are exactly that.
- **Post-checks** (`sentence_repair.splice_checked`, :339) only run `_integrity`: new repeat, orphan pronoun, misplaced moment. There is no F1/F17/F18 check on the replacement inside the pipeline. `check_replacement` (:516) exists but is used only on the admin path.
- **F17** (`trip_facts.timing_claims` :391, `pace_claims` :1348 (pace on blogs only), `thin_coda` :1082 / `_trim_thin` :1096) is deterministic and cheap to run on one sentence.
- **F9 sticky pass** (`quality_gates._f9_key` :842, `_f9_located_key`, `_drop_sticky_claims` :930): the key is (previous sentence, sentence). A quote spanning several sentences produces a key that never matches.
- **Attempt-3 blog truth cut** (`service.py:391 TRUTH_CUT_GATES = {F1, F9}`, `_cut_blog_truth_items`): it works on the `gate` of `plan()` items, so it is blind to F9 items that the overlap dedupe dropped. It also excludes F17 items whose own instruction is "cut it". `delete_flagged` refuses any deletion that would orphan a pronoun-led follower.
- **Regression guard** (`service.py:1680`) works per gate and reverts the whole attempt only when the attempt is not net-better. It caught R3. R1, R2 and R4 were net-better attempts, so it kept them; the metric still counts them as added.
- **F16** (`gate_faq_contract` :1611, `_enforce_faq_contract`): one regeneration per writer text, plus one more only when a repair pushed the FAQ from ≥ 3 pairs to under 3.

## 4. Proposed fixes, ranked

The metrics: retry-added is 4/26 = 15.4% against a target of ≤ 8%, which allows at most 2 of 26. AA-768 is 3/5 against a target of ≥ 4/5. All fixes are in CIS `services/acp_content_writing/`.

| Rank | Fix | Size | Retry-added | AA-768 | Other |
|---|---|---|---|---|---|
| 1 | **F17 post-check on repair replacements.** After `splice_checked`, run `timing_claims` (plus `pace_claims` on blogs) on each replaced sentence. If the replacement has a finding the original sentence did not have, either revert that item or, for an F1/F9 item, delete it when `delete_flagged` allows. Also add one prompt line: "Never add a time of day, day part, ordinal night/day, or pace/rest word the SOURCE does not give; drop one the sentence already had if the PROBLEM is about what it claims." | ~30 lines + 1 prompt line, $0 runtime | **−2** (R1, R2): 4→2/26 = **7.7%, met**. Certain, because the check is the gate's own function; probe-verified on both pairs. | Prevents H2's pace insertion | Also closes the metric blind spot in H2 |
| 2 | **`plan()` merges overlapping items instead of skipping them.** Use the union span and join the problems; keep `gates` as a set (truth gate wins). `_cut_blog_truth_items` reads `gates`. | ~15 lines | 0 | **+1 expected (H3)**: the repair finally sees "bicycles … invented scene detail" for the 2-sentence span. Medium confidence, because it relies on one LLM repair plus a judge pass. | H1: the attempt-3 truth cut fires and cuts the coda, clearing F9 and F17. Likely approved, which makes `blog_truth_cut_entries` > 0. |
| 3 | **Sticky key relaxation.** (i) Put the previous sentence in `_f9_key` only when the sentence opens with a referent-dependent word (pronoun/demonstrative: `this/that/these/those/it/they…`, cf. `trip_facts._PRONOUN_OPEN_RE` plus `that`). (ii) Split a multi-sentence judge quote into sentences, and drop the claim when every sentence of it is sticky. | ~20 lines | **−1** (R3): 1/26 = 3.8% with fix 1. High confidence: F9 passed at attempt 1, and the sentence is unchanged with a non-pronoun opener. | Supports H3 (the attempt-2 two-sentence quote and the attempt-3 changed previous sentence would both be sticky) and H2 (the Taktsang quote) | The trade-off is accepted by #761's design: a scene detail the attempt-1 judge passed stays. It is not a tour promise, so writer source-fidelity policy is unaffected. |
| 4 | **Thin coda: trim the leading frame and name the extras.** `_trim_thin` also tries the tail after a leading adverbial clause ("Before leaving …, " / "After …, " / "As …, ") and capitalises it. The F17 thin-coda message lists the extra words ("words the source does not give: leaving, part, northern, mongolia"). Optional: count a deletion-only edit (new sentence an in-order word subset of a passed one) as sticky. | ~15 lines | **−1** (R4): 0/26 with fixes 1+3. `fix_thin_moments` makes the coda plain at attempt 1, so F17 never sends it to a repair. Probe: 0 extras after the trim. | — | H1 is approved without depending on fix 2 |
| 5 | **Pronoun-follower cut.** In `delete_flagged`, and in the integrity fallback when a repair returns "", also delete the following sentence(s) of the same paragraph that open on a pronoun/demonstrative and are ≤ ~12 words, bounded by the blog minimum length. | ~20 lines | 0 | H2 becomes reachable: the "craft objects / They are simply…" pair and the "pace / That would be a misjudgement" pair can be cut. With fixes 1 and 3, H2 likely passes, giving 5/5. | Unlocks the attempt-3 truth cut where the writer chains sentences with pronouns |
| 6 | **Add F17 'cut it' items to the blog attempt-3 cut scope.** Time, pace and thin-coda findings are deterministic, and their instruction is already "cut it". | ~5 lines | 0 | Helps H2 and H1 | Policy-safe: a cut never adds a claim, and it is guarded by `_blog_cut_refusal` |
| 7 | **F16: one more FAQ regeneration at attempt 2** when F16 is still failing and the attempt-1 regeneration was not kept. About $0.005 each. Before building it, read the `flags` column to confirm which branch was taken. | ~5 lines | 0 | 0 | approved 17→19/20 if the regeneration succeeds. The alternative is a policy call for Nghiệp: F16 as a warn when ≥ 2 pairs. |
| 8 | **Readout: violation-level adds.** Count a new flagged sentence inside a gate that was already failing (H2's pace sentence is invisible today). | readout only | Makes the metric honest. It may *raise* r6's number. | — | — |

**Minimum set for both unmet metrics: fixes 1 + 2 + 3** (about 65 lines, no new LLM calls):
- **Retry-added:** R1 and R2 are removed deterministically and R3 by sticky → **1/26 ≈ 4%**. Fix 1 alone already gives 2/26 = 7.7%, which is borderline at n=26.
- **AA-768:** fix 2, with fix 3 as backup, makes H3 pass → **4/5**.

Adding fix 4 also clears R4/H1 (r6 retry-added 0/26, one fewer F17 hold). Fix 5 makes H2 possible, which would give 5/5.

Re-measure: an r7 at the same n=20 + 5 (about $1.2). Report both the gate-level rate and the violation-level rate (fix 8), because the 8% target is about 2 retries and is noisy at this n.
