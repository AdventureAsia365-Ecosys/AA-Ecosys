# Panel rubric v1.1 — diagnosis of v1 and calibration (S248, M2a S1-first, Refs AA-645)

*Agent: Claude Code (subagent). $0: no LLM calls, no DB. Inputs: `pass-a.json`, `pass-b.json`, `repeatability.txt`
(v1 run on 12 golden pages), `docs/eval/aa729/fixture-1.1.0.json` (50 golden S1 pages, labels approved by Nghiệp),
`docs/audits/2026-10-21-S246-content-quality-advisory/README.md` (what "pass" means). Output: `rubric-v1.1.md`.*

## 0. Short answer

- **Why v1 never says pass.** The v1 verdict rule made a page `heavy_edit` as soon as *any* fact had to change, and
  every real S1 page has a few small fact slips (v1 found 3–11 per pass page). The labeller's "pass" is S246's
  "publish verbatim or light edit" = *one-phrase fixes that add no tour service and do not break the structure*, so it
  tolerates exactly those slips. v1's severity field was not used by the verdict at all.
- **Why the serious counts swing 9 vs 16.** 4 of the 7 extra serious errors in pass B are one claim ("Class III–IV
  rapids") counted once per field; the other 3 are severity calls the v1 wording left open.
- **v1.1** = a class→severity table with a magnitude floor, four hard-fail kinds, one error per claim, a verdict
  computed from the error list, and a sentence-count denominator counted by code.
- **Train fit (30 pages, my own non-blind v1.1 judgement): 29/30 agree with the label** (pass 4/4, fail 25/26),
  threshold plateau τ = 0.016–0.018 (chosen 0.017). The held-out 20 are untouched; the packet is
  `packet-holdout.json`.

## 1. Diagnosis of v1

### 1.1 What fired on the four pass pages (both passes)

| page | label reason (Nghiệp-approved, short) | v1 serious | v1 minor (A / B) |
|---|---|---|---|
| s1-015 | facts all in source; "vague seo_meta 'kora at 5,200m'", "'the world's highest'", "filler" → light | B only: `kora at 5,200m` | 4 / 2 |
| s1-035 | "word-level embellishments … 'Start before dawn', 'accessible for all cycling levels', 'wild boar', pillars-to-ahimsa … none changes a fact or the structure" → light | none | 5 / 11 |
| s1-040 | "each a one-phrase fix: '30-minute walk…', the unsupported 'moderate climbing difficulty' … should go … none invents a tour service" → light | both: `moderate climbing difficulty` | 2 / 4 |
| s1-049 | "small one-phrase fixes: 'as the day's light fades', Day 6 'descending 1,570 meters' (that figure is elevation gain), the seo_meta superlative" → light | both: `descending 1,570 meters` | 2 / 3 |

Every item v1 flagged on these pages, serious or minor, is named in the label as a tolerated light fix. So the panel
did see the right things; the verdict rule ("heavy_edit = at least one fact … must change") turned them into fails.

### 1.2 What v1 called minor on fail pages that the labels treat as decisive

| page | v1 severity | label |
|---|---|---|
| s1-007, s1-019 | `cut_text` in seo_meta = minor (both passes) | cut meta is a stated fail reason |
| s1-010 | wrong overnight (Day 5 in Yuli, not Ruisui) and invented spa / thermal-pool amenities = minor | "the core fault"; fact change |
| s1-007 | invented compass bearings = minor | fail reason |
| s1-019 | "each revealing roughly 2,000" (total, not per pit) = minor | wrong fact, fail |
| s1-014 | Rome for Paris, K2 north face = minor | fail ("two wrong facts customers would read") |

v1 got these pages "right" only because every page was heavy_edit. Applying the v1.1 verdict rule to the v1 error
lists as they are gives 6/12 (A) and 7/12 (B); adding the hard-fail classes by class name gives 8/12 and 9/12
(s1-010 stays light because v1 filed its decisive errors as `wrong_place_or_direction` / `invented_fact` minor;
s1-035 turns heavy because pass B filed "accessible for all cycling levels" as `invented_promise`). A verdict rule
alone does not fix v1: the severity table and the hard-fail definitions are needed too.

### 1.3 Where the 9 vs 16 serious errors come from

| page | A | B | cause |
|---|---|---|---|
| s1-008 | 2 | 6 | B logged "Class III–IV" once per field (subtitle, summary, highlights, itinerary, meta) |
| s1-006 | 1 | 2 | "9 Days" vs Day 10: A `other`/minor, B `day_structure`/serious |
| s1-024 | 3 | 4 | invented "6 to 7 hours of active walking": A minor, B serious |
| s1-015 | 0 | 1 | "kora at 5,200m": A minor, B serious |

Fixes in v1.1: one error per claim (§4); day-count mismatch is always HF-1; invented durations ≥ 1 h are S2;
vague-but-not-contradicting figures are minor.

### 1.4 The denominator is noisy too

B counted 1.28–2.1× A's `checkable_claims` on the same pages. A's counts track the number of sentences of 4+ words
in the page closely (e.g. s1-006 75 vs 70 sentences, s1-014 92 vs 98, s1-040 20 vs 19, s1-050 65 vs 65). v1.1
therefore takes the denominator from code (`apply_v11.py`, sentences of 4+ words over the seven page fields) and
keeps the judge's `checkable_claims` for reference only.

## 2. What v1.1 changes, and the evidence for each

| change | evidence |
|---|---|
| Minor errors never fail a page | all four pass pages carry 2–11 minors the labeller tolerated (§1.1) |
| One serious error alone never fails a page | s1-040 (invented difficulty) and s1-049 (gain written as descent) are labelled pass with exactly one serious slip |
| HF-1 day structure, HF-2 invented promise, HF-3 scope drift, HF-4 cut text fail on their own | train fails s1-001, 006, 010, 012, 017, 019, 024, 026, 029, 031, 037, 045, 046, 047, 050: the label reason names one of these as sufficient ("the broken structure alone", "a false inclusion", "the cut-off text alone") |
| S1 magnitude floor (< 1 h, < 20 %) | s1-040 "30-minute walk" for ~1 hour and s1-006 "2 hours" for 2.5 hrs are tolerated / secondary in the labels, while s1-006 "6–7 hours" for 3–4 hrs is a fail reason |
| Conditional made certain = serious (S5) | s1-004 jeep safari "is included" for "we will try to join" |
| Accommodation amenity / standard = HF-2, accommodation location = S2 | s1-010 spa and thermal pools, s1-016 heritage hotels (fail reasons); s1-023 / s1-036 "within park boundaries" |
| Source contradicts itself → the day list wins | s1-023 names Corbett in its intro but no day visits it; the label fails the page for selling Corbett |
| Verdict computed, not chosen | v1 passes disagreed on severity but never on verdict, because the verdict ignored severity; v1.1 makes the verdict depend only on counted errors so a severity disagreement shows up and can be audited |

## 3. Split (seeded, stratified by label)

`split_v11.py` → `split-v1.1.json`, seed 2481. The 12 v1 repeatability pages are forced into TRAIN (their labels and
panel errors were read for the diagnosis). TRAIN is filled to 30 with the label mix of the 50 (6 pass / 44 fail →
4 pass / 26 fail); the 18 extra fail pages are drawn per fixture stratum (pick_reason prefix) in proportion.

- **TRAIN (30):** s1-001, 004, 005, 006, 007, 008, 010, 012, 014, 015, 016, 017, 018, 019, 023, 024, 026, 028, 029,
  031, 034, 035, 036, 037, 040, 045, 046, 047, 049, 050 (pass: 015, 035, 040, 049).
- **HELD-OUT (20):** s1-002, 003, 009, 011, 013, 020, 021, 022, 025, 027, 030, 032, 033, 038, 039, 041, 042, 043, 044,
  048 (pass: 011, 042).

## 4. Fit on TRAIN

I read the full source and page of the 18 train pages outside the v1 set and judged all 30 with v1.1
(`train-v1.1-self.json`, every quote checked verbatim against the page). `apply_v11.py` derives the verdicts:

```
python3 apply_v11.py train-v1.1-self.json --fixture <fixture> --labels <fixture> --sweep
```

| result | value |
|---|---|
| agreement with label (pass/fail) | **29/30 = 0.967**; pass 4/4, fail 25/26; balanced accuracy 0.981 |
| derived verdicts | heavy_edit 23, light_edit 5, reject 2 (s1-024, s1-045) |
| fails decided by a hard-fail | 19 of 26 |
| pages decided by the serious count / rate | 11: s1-004, 005, 014, 018, 028, 034, 036 (fail) and 015, 035, 040, 049 (pass) |
| τ sweep | 28/30 for τ 0.005–0.015, **29/30 for 0.016–0.018**, 28/30 for 0.019–0.033, then falling |
| alternative: pass iff no hard-fail and serious ≤ 1 (count only) | 28/30 (misses s1-015: 2 serious on a 131-sentence page) |
| alternative: rate only, τ 0.02, no one-error floor | 26/30 (misses s1-040 and s1-049: one serious on a short page) |

Per-page rates on the 11 pages the rate decides: pass 0, 0.0153 (s1-015, 2 serious), 0.0263 and 0.0526 (one
serious, under the floor); fail 0.0102 (s1-014, one serious), 0.0189 (s1-005), 0.0339–0.0732 (the rest).

**The one miss, s1-014 (label fail, v1.1 light_edit).** Under v1.1 it has one serious error (Rome for Paris, S7) and
minors (K2's "north face", six hours to Jhola instead of Askoli, two overclaims). The label fails it for "two wrong
facts customers would read" (Rome, north face), while s1-049 passes with a wrong elevation figure. Making "north
face" serious would also make similar background slips serious on the pass pages, so I left the miss in place: it is
the line between background trivia and a tour fact, and the label itself is not consistent on it.

## 5. Caveats (read before trusting the numbers)

1. **The train agreement is not blind.** I had read the labels (I listed all 50 label reasons once, before the split,
   to learn what pass means). The rules cite train pages only, but a fresh blind panel will agree less. The held-out
   passes are the real test.
2. **Few pass pages:** 4 in train, 2 in held-out. Pass recall on held-out is measured on n = 2.
3. **The threshold rests on two pages:** s1-015 (0.0153, pass) and s1-005 (0.0189, fail). Any τ between them gives the
   same train result. The one-error floor and the hard-fail kinds carry most of the decisions.
4. **The denominator changed:** v1.1 rates (serious / sentences) are not comparable with v1 rates (serious / judge's
   claims). `score_repeatability.py` still works on v1.1 files (same `severity`, `field`, `verdict` keys) but reports
   the judge's verdict and claim-based rate; use `apply_v11.py` for the v1.1 verdict.
5. Labels are panel labels approved by Nghiệp (1/100 human-only label, S246 §0), not Ms. Thư's view.

## 6. Held-out check (for the orchestrator)

Packet: `packet-holdout.json` (20 pages, seeded order 11, same fields as v1 packets, no labels / pipeline verdicts /
code findings), built by `build_packet_holdout.py` (build_packet.py has no id-list option). Two fresh blind agents,
same packet, `rubric-v1.1.md` only → `pass-h1.json`, `pass-h2.json`. Then:

```
F=../../../../docs/eval/aa729/fixture-1.1.0.json
python3 apply_v11.py pass-h1.json pass-h2.json --packet packet-holdout.json --labels $F
```

It prints, per pass, the derived verdicts and label agreement, and between passes the pass/fail kappa, 4-level
agreement, serious totals and ratio, hard-fail page agreement and mean rate difference. Do not change τ or the
tables after seeing these numbers; a change is v1.2 and needs a new train fit.
