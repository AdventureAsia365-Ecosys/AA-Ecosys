# AA-790: a fixed blog sample and a calibrated panel before any new writer round — plan, $0

Session S258, 29/10/2026. Agent: Claude Code (lane eval-prep). No model call, nothing run on Dev yet.
Selector: CIS `scripts/aa790/fixed_sample.py` (branch `feat/aa-919-calibration-labelling-round`, tests
`tests/unit/test_aa790_fixed_sample.py`). Run steps: private `.tmp-session/S258/eval-prep/aa790/RUNBOOK.md`.

## Why (numbers from the S257 round-10 panel, `../2026-10-29-S257-aa790-r10-panel/panel-scores.json`)

Round 10 wrote the control twice (`r10c`, `r10c2`) and the same blind panel scored both. The per-piece difference of
two identical arms is pure noise (writer re-generation + one judge vote):

| Lens | SD of the noise difference, 8 pieces | 5 blogs only | Smallest effect a 24-blog sample detects (80 % power) |
|---|---|---|---|
| ai_tells | 1.29 | 1.60 | ~0.9 |
| brand_voice | 1.07 | 1.27 | ~0.7 |
| source_fidelity | 1.10 | 1.39 | ~0.8 |
| reader_value | 0.52 | 0.55 | ~0.3 |

(Smallest detectable effect ≈ 2.8 × SD / √n for a paired mean; the SDs come from 8 and 5 pieces, so they are rough.)
The round bars were ±0.15. With 8 pieces the noise of a mean is ~0.4, which is why two identical controls differed as
much as the effects. **More pieces alone do not reach a 0.15 bar on any lens**: 24 blogs bring the noise of a mean to
~0.22-0.33. Two things must change together: a larger fixed sample, and less noise per piece (several judge votes per
lens, measured first). The bars then follow from the measured noise instead of a fixed 0.15.

## The fixed sample

- **What**: ≥ 20 T9 blog pieces (default 24; 8 per demo tenant), the same pieces in every round until the sample is
  versioned again. Blog only: the reader-value failures of rounds 9-10 are blog failures, and blogs carry the longest
  prompts. LinkedIn stays on the golden set (AA-919).
- **Eligible**: `acp_shared.content_piece` blog pieces, status approved or held, with a stored `writer_input` that has a
  seed and a brand pack and an angle request (what the repanel harness rewrites from).
- **One piece per distinct input**: attempts and reruns of one request write from the same seed; the selector keeps
  the newest piece per seed hash. **Risk:** the schema dump estimates only ~21 rows in `acp_shared.angle_gate_request`, so the number of
  distinct blog inputs may be under 24. The selector reports `pool.distinct_inputs` and `short_by`; if short, the
  sample is whatever exists (stated in the manifest), and growing it needs new T8 requests on new atoms (paid model
  calls, blocked now). No piece is counted twice to reach a number.
- **Stratification**: equal share per tenant (a tenant with fewer inputs gives all it has; the rest goes to the
  others); inside a tenant up to half the share are **labelled anchors** (the golden set's t9_blog label, else the
  majority of `acp_shared.content_piece_label`), then unlabelled pieces; each part round-robin over destination, held
  pieces first. Optional `FORCE_IDS` puts the round 1-10 harness blogs first, for the link to old rounds.
  Deterministic: `sha256("790:<piece_id>")`.
- **Where it is stored**: the manifest JSON (ids, tenant, destination, status, route size, anchor label, and the sha256
  of the stored writer_input, seed and text; no text) goes into this folder as `fixed-sample-v1.json`. Every later
  round names the version it ran on. Before a round, the operator re-runs the selector with `FORCE_IDS` = the manifest's ids and compares the hashes (not automated yet): a piece whose
  input changed, or that was deleted, is reported and dropped for that round, never replaced silently; a replacement
  makes `v2`. The texts the panel scores stay in the private `.tmp-session/` (tenant text).

## Panel calibration (before any paid writer round)

The panel is Claude Code agents (no API cost). Four lenses, 0-10, the S251 rubric, blind items, all arms in one run
(lesson S252: judges drift between runs).

1. **Judge test-retest ($0)**: score the stored texts of the 24 pieces twice, in two separate panel runs, with the
   same rubric. Per lens: the SD of (run 2 − run 1) gives the judge's own noise. With `k` votes averaged per lens, the
   judge part of a pair's noise falls by √k; measure k = 1 and k = 3 (three judges per lens per item).
2. **Anchor check ($0)**: on the labelled anchors, the stored text's scores must separate the labels: source_fidelity
   AUC ≥ 0.75 between golden pass and fail, and the mean of the four lenses ordered as_is > light > heavy > reject on
   `content_piece_label` grades. A lens that cannot separate the anchors is reported and does not gate a round.
3. **Drift anchors in every run**: 4 anchor texts (2 pass, 2 fail) ride along in every later panel run; if their mean
   moves by more than the test-retest SD, the run is repeated before anyone reads the arms.
4. **Writer noise (first paid step, later)**: the control written twice on the fixed sample, scored with the
   calibrated panel (k votes). Writer SD = √(pair variance − judge variance). This sets the bars.
5. **Bars from noise**: a round passes a lens only when the paired mean beats ±2 × the measured standard error, and
   "no loss" means the lower bound stays above −2 SE. The minimum detectable effect is printed before the run; if
   it is larger than the effect the round aims at, the round does not run.

## Cost when the LLM path is back (estimate, not approved)

One blog rewrite ≈ $0.04-0.08 (round 10: 8 calls, $0.33; harness reserve $0.12 a blog). Writer-noise step: 24 × 2 =
48 calls ≈ $2-4. A round with control + treatment on 24 blogs ≈ $2-4, plus the panel at $0. The panel calibration
(steps 1-3) is $0.

## Decisions for the tech lead

1. Accept "no new writer prompt round until the fixed sample exists and the panel test-retest is measured" (S257
   proposal, now with numbers).
2. Size: 24 (default) or as many distinct inputs as exist if fewer; revisit after step 4 shows the writer noise.
3. Bars: replace the fixed ±0.15 with ±2 SE from the measured noise (step 5).
