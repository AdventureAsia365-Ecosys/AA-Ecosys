# AA-645: S1 writer, pooled n = 50 decision (run 1 + run 2)

S248 · 2026-10-23 · Agent: Claude Code

**Data:**
- Run 1 covers golden tours s1-001..025 (`run/`, `pass-a.json`, `pass-b.json`).
- Run 2 covers s1-026..050 (`run2/`, `run2/pass-a.json`, `run2/pass-b.json`).
- Pages are mapped to (tour, arm) with each run's `panel/key.json`. The E arms of run 1 are ignored.
- Labels come from `fixture-1.1.0.json` (drafted by the agent panel, approved by Nghiệp). These 50 tours have 44 fail labels and 6 pass labels.

**Script:** `/tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/a440f877-5210-4a43-9af3-b1852feb20d9/scratchpad/pooled.py`. It is pure Python. The Wilcoxon test uses the same normal approximation as `score_screen.py` and also reports an exact conditional p. The bootstrap uses 20,000 resamples of tours with seed 645.

## 1. Verdict

**Case 1 of the pre-registered rule applies: W×Sonnet is significantly better than W×Luna, so the choice is W×Sonnet.**

The pre-registered primary metric is serious errors per checkable claim for each tour, pooled over both panel passes and paired over the 50 tours. W×Sonnet is lower on it:
- Mean difference −0.0037 (bootstrap 95% CI −0.0078 to −0.0003).
- Wilcoxon p = 0.041 (exact 0.043).
- Sign test: Sonnet wins 10, loses 2, ties 38, p = 0.039.

The result is only just significant:
- Only 12 of the 50 tours differ. In 3 of Sonnet's 10 wins (s1-005, 006, 016), both arms have the same number of serious errors and only the claim count differs.
- If you count serious errors without dividing by claims, Sonnet wins 7, Luna wins 2, and 41 tie. Wilcoxon p = 0.13, sign test p = 0.18.
- Pages with any serious error: Sonnet 7/50, Luna 10/50 (McNemar p = 0.45).
- Pass a alone is significant (p = 0.028); pass b alone is not (p = 0.066).

All the secondary measures point the same way, and the rank result is strong:
- The blind panel ranks Sonnet higher in 37 tours and Luna higher in 7 (p < 0.0001).
- Sonnet has 0 gate pages; Luna has 2.
- Sonnet's figure coverage is higher (p = 0.001).
- Sonnet fixes 37 of 44 fail-labelled tours; Luna fixes 33.
- Sonnet keeps all 6 pass-labelled tours clean; Luna breaks 1.

Nothing favours Luna except cost: its writer is about 24× cheaper.

In run 2, both W arms again beat A+ by far more than the A/A noise, in both passes, so the run-2 confirmation criterion is met. The only open question is Sonnet versus Luna, and by the pre-registered rule the answer is Sonnet.

If Nghiệp reads the count-only check as a tie, the memo's tie branch would apply instead. That branch recommends Sonnet because these pages are the data foundation; the "cheaper wins" rule would pick Luna. The rule as written names the primary metric, and that metric is significant.

## 2. W×Sonnet vs W×Luna (n = 50 tours)

| Measure | W×Sonnet | W×Luna | Paired test (Sonnet − Luna) |
|---|---:|---:|---|
| Serious / claim, pooled | **0.0022** | 0.0055 | — |
| Serious / claim, run 1 · run 2 | 0.0033 · 0.0011 | 0.0056 · 0.0054 | run 1 p = 0.13 (6–1); run 2 p = 0.14 (4–1) |
| Per-tour rate, mean diff | — | — | **−0.0037, CI −0.0078 to −0.0003, Wilcoxon p = 0.041 (exact 0.043)** |
| Per-tour wins / losses / ties (rate) | 10 | 2 | 38 ties, sign p = 0.039 |
| Serious errors / page / pass | 0.12 | 0.23 | count-only: 7–2–41, Wilcoxon p = 0.13 |
| Pages with 0 serious in both passes | 43/50 | 40/50 | McNemar p = 0.45 |
| Checkable claims / page | 55.1 | 41.9 | Sonnet writes ~30% more checkable content |
| Rank (0 = first, 1 = last; E removed, renormalised over 4 arms) | **0.090** | 0.298 | −0.208, CI −0.292 to −0.118, p < 0.0001; 37 / 7 / 6 ties, sign p < 0.0001 |
| Head-to-head in each pass (100 tour-passes) | above Luna 75 | above Sonnet 19 | 6 ties |
| Rank per run | — | — | run 1 p = 0.059 (18–5); run 2 p = 0.0001 (19–2) |
| Gate pages | **0** | 2 (s1-015 META_CUT, run 1 before the fix; s1-034 META_LENGTH, run 2 after the fix) | — |
| Figure coverage (mean) | **0.678** | 0.566 | +0.104, CI +0.043 to +0.172, p = 0.001; 21 / 2 / 27 ties |
| Fail-labelled tours fixed (0 serious in both passes, no gate) | **37/44** (r1 18/23, r2 19/21) | 33/44 (r1 17/23, r2 16/21) | — |
| Pass-labelled tours kept clean | **6/6** | 5/6 (s1-015 gate) | — |
| Panel verdicts (100 page-passes) | 47 publish_verbatim · 46 light · 7 heavy | 52 · 32 · 16 | — |
| Writer errors / retries / max_tokens stops | 0 / 0 / 0 | 0 / 0 / 0 | — |
| Writer+meta cost / tour | $0.0581 ($2.90 for 50) | $0.0024 ($0.12 for 50) | ~24× |
| Calls / tour | 2.36 | 2.48 | — |

The 12 tours where the per-tour rate differs (serious errors in pass a, pass b):

| Tour | Sonnet | Luna | Note |
|---|---|---|---|
| s1-005 | 1, 1 | 1, 1 | same count; only claims differ, so Sonnet "wins" |
| s1-006 | 1, 1 | 1, 1 | same count; Sonnet "wins" |
| s1-016 | 1, 0 | 1, 0 | same count; Sonnet "wins" |
| s1-007 | 0, 0 | 1, 1 | Sonnet |
| s1-012 | 0, 0 | 1, 0 | Sonnet |
| s1-021 | 1, 1 | 2, 2 | Sonnet |
| s1-030 | 0, 0 | 2, 2 | Sonnet |
| s1-031 | 0, 0 | 1, 1 | Sonnet |
| s1-032 | 0, 0 | 1, 0 | Sonnet |
| s1-038 | 0, 1 | 2, 2 | Sonnet |
| s1-010 | 1, 1 | 0, 0 | Luna |
| s1-033 | 1, 1 | 0, 0 | Luna |

Fail-labelled tours still not fixed:
- **Sonnet:** s1-005, 006, 010, 016, 021, 033, 038.
- **Luna:** s1-005, 006, 007, 012, 016, 021, 030, 031, 032, 034, 038.

## 3. W arms vs A+ (Haiku, today) and the A/A noise, pooled n = 50

| Comparison (per-tour serious / claim) | Mean diff | Bootstrap 95% CI | Wilcoxon p | Better / worse / tie |
|---|---:|---|---:|---|
| W×Sonnet − A+ | −0.0385 | −0.0482 to −0.0293 | < 0.0001 | 40 / 1 / 9 |
| W×Luna − A+ | −0.0348 | −0.0445 to −0.0254 | < 0.0001 | 37 / 4 / 9 |
| W×Sonnet − A+2 | −0.0428 | −0.0540 to −0.0326 | < 0.0001 | 43 / 1 / 6 |
| W×Luna − A+2 | −0.0391 | −0.0505 to −0.0284 | < 0.0001 | 39 / 4 / 7 |
| **A/A noise: A+2 − A+** | +0.0043 | −0.0065 to +0.0157 | 0.53 | 23 / 25 / 2; per-tour \|diff\| median 0.0198 |

| Arm | Serious / claim pooled | Rank | Gate pages | Figure coverage | Fail tours fixed | $/tour |
|---|---:|---:|---:|---:|---:|---:|
| A+ Haiku | 0.0399 | 0.787 | 30/50 (NUMBER_NOT_IN_SOURCE 22, META_LENGTH 13, DAY_* 2) | 0.420 | 6/44 | $0.0172 |
| A+2 Haiku (A/A) | 0.0429 | 0.825 | 33/50 (NUMBER 25, META_LENGTH 15, DAY_* 3) | 0.454 | 3/44 | $0.0173 |
| W×Sonnet | 0.0022 | 0.090 | 0 | 0.678 | 37/44 | $0.0581 |
| W×Luna | 0.0055 | 0.298 | 2 | 0.566 | 33/44 | $0.0024 |

Rank, W vs A+:
- Sonnet −0.697 (49 / 0 / 1), p < 0.0001.
- Luna −0.488 (45 / 4 / 1), p < 0.0001.
- A/A rank difference +0.038 (CI −0.053 to +0.130, p = 0.39).

Run-2 confirmation criterion ("W must again beat A+ outside A/A noise in both passes"), using run 2 only (n = 25):

| Pass | W×Sonnet − A+ | W×Luna − A+ | A+2 − A+ (noise) |
|---|---|---|---|
| a | −0.0414 (CI −0.056 to −0.028), p = 0.0001, 20–0 | −0.0364 (−0.051 to −0.023), p = 0.0002, 19–1 | +0.0075 (−0.006 to +0.021), p = 0.35 |
| b | −0.0376 (−0.052 to −0.024), p = 0.0001, 19–0 | −0.0338 (−0.050 to −0.019), p = 0.0005, 17–2 | +0.0070 (−0.006 to +0.019), p = 0.31 |

The criterion is met for both W arms: in neither pass does a W confidence interval overlap the A/A interval.

## 4. Cost

| | Writer+meta / tour (this A/B) | Full A1 chain, ~900 tours (memo §2.2 model) | With a fact judge from a different model family (memo §3) |
|---|---:|---:|---:|
| A+ Haiku (today) | $0.0172 | $42 | — |
| W×Sonnet | $0.0581 (run 1 $0.0591, run 2 $0.0571) | $72 ($61–105) | ~$75 (Luna judge ~$3) |
| W×Luna | $0.0024 (both runs) | $11 ($9–15) | ~$36 (Sonnet judge ~$25) |

Once the fact judge is included, Sonnet costs about $40 more per full rewrite. In a normal month that is about $1.6 more (memo §2.3). The measured cost was the same in both runs.

## 5. Caveats

1. **The gap is small.** Sonnet − Luna is −0.0037 per claim, which is about one extra serious error per ~9 pages per pass for Luna. It is also smaller than the A/A per-tour noise measured on Haiku pages (median |diff| 0.0198). Haiku pages carry about 10× more errors, so that noise is not directly comparable, but it shows the scale.
2. **The primary result is borderline.** p = 0.041 does not survive the count-only view, the any-serious view, or pass b on its own. The rank, gate, coverage and fix-count results agree with it and carry most of the weight.
3. **Rank values differ from `score.json`.** Rank here is recomputed without the E pages (run 1 ranked 6 pages per tour, run 2 ranked 4). `score.json` included E, so its run-1 rank values are different.
4. **Luna's META_CUT fix.** Luna's run-1 pages were written before the fix. Run 2, after the fix, still produced one META_LENGTH gate page (s1-034).
5. **The panel is not independent human grading.** It is two blind agent passes using rubric v1.1. The golden labels were drafted by the agent panel and approved by Nghiệp. Treat the numbers as relative signals between arms.
6. **Only writer + meta were run.** The live validator, judge and Jev were not. The main cost risk is retries under the brand judge (memo §4.7); the step-4 shadow run measures that.

## 6. Next step (memo §5)

Put W×Sonnet behind a flag (off by default) and run the step-4 shadow measurement. Then run waves of 3, then up to 50, then about 900 tours, with approval between waves. The $0.26 offline brand-fit judge measurement on the run 1 + run 2 pages has not been done yet.

The report is saved at `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645ab/pooled-n50.md`.