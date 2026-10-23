Merged the run-2 chunks and ran the scorer. The pick is `w|sonnet-5-5`. It's the only arm with no gate codes, and it has the lowest serious-error rate (0.0011 per claim, Wilcoxon p=0.0001 vs A+).

**Merge:** `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645ab/run2/pass-a.json` and `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645ab/run2/pass-b.json` each hold 100 pages (p001–p100, no duplicates) and 25 rank groups (g01–g25). The `pass`/`rubric` fields were missing from all pass-a chunks and from `pass-b-10.json`. I set them to `a`/`b` and `s1-panel-v1.1`, the same values as run 1. 125 units in all: 25 tours × 5 arms. The stored arm has gates only and no panel pages.

**Per arm** (25 tours each; serious = serious errors per checkable claim; rank: lower is better)

| arm | gate pages (codes) | serious/claim a | b | pooled | serious/page | mean rank | coverage | $/tour | calls/tour |
|---|---|---|---|---|---|---|---|---|---|
| aplus\|haiku (baseline) | 14 (NUMBER_NOT_IN_SOURCE 10, META_LENGTH 5, DAY_* 2) | 0.0431 | 0.0397 | 0.0414 | 2.62 | 0.760 | 0.398 | 0.0174 | 2.64 |
| aplus2\|haiku (A/A copy) | 17 (NUMBER_NOT_IN_SOURCE 12, META_LENGTH 8, DAY_* 1) | 0.0458 | 0.0444 | 0.0451 | 2.84 | 0.863 | 0.432 | 0.0174 | 2.64 |
| w\|sonnet-5-5 | 0 | 0.0007 | 0.0014 | 0.0011 | 0.06 | 0.060 | 0.696 | 0.0571 | 2.24 |
| w\|gpt-6-luna | 1 (META_LENGTH 1) | 0.0059 | 0.0050 | 0.0054 | 0.22 | 0.317 | 0.530 | 0.0024 | 2.44 |
| stored\|live (gates only) | 9 (META_CUT 5, META_LENGTH 2, DAY_* 1, NUMBER_NOT_IN_SOURCE 1, TEXT_TRUNCATED 1) | – | – | – | – | – | 0.500 | 0 | 0 |

Verdicts and agency use, both passes pooled (50 per arm):
- **sonnet:** 25 publish_verbatim and 25 light_edit; agency use is 25 yes and 25 with edits.
- **luna:** 31 publish_verbatim, 13 light_edit, 6 heavy_edit; agency use is 31 yes, 13 with edits, 6 no.
- **aplus:** 33 heavy_edit, 2 reject, 1 publish_verbatim.
- **aplus2:** 33 heavy_edit, 2 reject, 0 publish_verbatim.

**A/A noise (aplus vs aplus2, same setup):**
- Pooled serious/claim: 0.0414 vs 0.0451, a gap of +0.0037 (about 9% relative). Pass a: 0.0431 vs 0.0458; pass b: 0.0397 vs 0.0444.
- Paired median per-tour gap: -0.0014. Wilcoxon p=0.367 (n_nonzero=25), so the gap is noise.
- Gate pages: 14 vs 17. Mean rank: 0.760 vs 0.863.
- Both writer arms are about 10× below this noise band.

**Wilcoxon W vs A+** (paired per-tour serious rate, 25 tours)

| arm | median diff | n_nonzero | p pooled | p pass a | p pass b |
|---|---|---|---|---|---|
| w\|sonnet-5-5 | -0.0333 | 20 | 0.0001 | 0.0001 | 0.0001 |
| w\|gpt-6-luna | -0.0333 | 20 | 0.0003 | 0.0002 | 0.0005 |
| aplus2\|haiku | -0.0014 | 25 | 0.367 | 0.348 | 0.307 |

**Pick:** `w|sonnet-5-5`. luna is ruled out by its one META_LENGTH gate page; no other arm was within the tie band. Caveat from the scorer: "12 tours choose a writer, they do not prove one; confirm in A/B run 1."

**Pass a/b agreement** (does the page have at least one serious error):

| scope | n | pages flagged a / b | raw agreement | kappa |
|---|---|---|---|---|
| all pages | 100 | 48 / 47 | 0.97 | 0.94 |
| aplus\|haiku | 25 | 20 / 19 | 0.96 | 0.88 |
| aplus2\|haiku | 25 | 23 / 23 | 1.00 | 1.00 |
| w\|gpt-6-luna | 25 | 4 / 3 | 0.96 | 0.83 |
| w\|sonnet-5-5 | 25 | 1 / 2 | 0.96 | 0.65 |

Sonnet's kappa is lower only because it has very few flagged pages: one disagreement moves it a lot. The Pearson correlation of per-page serious-error counts between passes is 0.98.

Files are in `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645ab/run2/`:
- score.json
- score-pass-a.json
- score-pass-b.json