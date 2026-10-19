# Pooled F9_cta_fact re-flag rate after sentence repair (S245, 20/10/2026)

Status: **skeleton.** The pooling script is ready, but it has not run yet. The sections marked _pending_ are
filled from the run output.

Agent: Claude Code. Cost: $0 (read-only DB, no LLM call). Issue: the AA-777 residual, pooled over the r5–r7 retries.

## 1. Question

After the AA-777 fixes (sticky pass #761, r6 fixes 1–3 in CIS #767), how often does a retry *add* a blocking
fail? The issue asks for this over enough retries (n ≥ 60) to beat the noise of a single round (n ≈ 25). The target is
≤ 8%. The title names F9_cta_fact. The Done-when names any blocking fail. Both are reported.

Done-when (from the issue):

1. The pooled rate over n ≥ 60 retries, with a 95% interval.
2. Every retry-added fail is classified as one of:
   - **C1**: a real new fault (the repair writer added an unsupported claim);
   - **C2**: F9 re-judging a sentence that was repaired, or one that was left unchanged;
   - **C3**: a judge quote that spans two sentences.
3. Either the pooled rate is ≤ 8%, or one fix ships and a re-measure (≤ $1.5) shows ≤ 8% on the pooled set.

## 2. Inputs

| Set | Pieces | Retries | Source |
|---|---|---|---|
| S235_r5 | 20 | 26 | `BASE_SETS` in `.tmp-session/s239/aa777_r7_readout.py` |
| S239_r6 | 20 | 26 | `../2026-10-16-S239-in-progress-audit/aa777-r6/readout_stdout.json` |
| S239_r7 | 20 | 23 | `../2026-10-16-S239-in-progress-audit/aa777-r7/readout_stdout.json` |
| S239_aa768_pre761 / r6_aa768 / r7_aa768 | 5 / 5 / 5 | 9 / 8 / 8 | same readouts |
| natural_post_r7 | _pending_ | _pending_ | T9 pieces created after 2026-10-16T08:12Z that are in no set above |
| S234_r4 (reference only, before the sticky pass) | 20 | 32 | `BASE_SETS` |

The r6 cases have already been classified in `../2026-10-16-S239-in-progress-audit/aa777-r6/diagnosis.md`. That
classification is reused here and cross-checked against the dump.

## 3. Method

- **Script:** `script/s245_f9_pool.py`. It is a copy of `.tmp-session/s245_f9_pool.py` as handed to the run.
  It runs in the CIS api container through the S3-presigned ECS exec. It connects with the container's
  `DATABASE_URL` (role `cis_app`), with `ssl="require"`, inside one read-only transaction. The full output goes to
  `s3://…/scripts/out/s245_aa865_pool.json` and is saved here as `pool.json`.
- **Metric:** `reconstruct()` and the "retry added a blocking fail" rule are copied from the S239 r7 readout, which
  is itself a port of S234 `fr_analyze.py`. The script first checks that it reproduces every committed per-round
  number (`reproduction_check`). A mismatch is reported and never silently absorbed.
- **Interval:** Wilson score interval, 95%.
- **Case dump:** one record per retry that added a blocking fail. Each record holds:
  - the piece and attempt;
  - the repair targets of the base attempt (gate plus the quoted sentence);
  - for each F9 claim: the claim, the judge's reason, the located sentence, and the number of sentences the quote
    spans;
  - whether that sentence was unchanged since the base attempt, whether the sentence before it changed, and the
    content words the repair added;
  - a heuristic `suggested_class`.

  The class in §5 is set by reading each case. The hint is not used as the class.

## 4. Pooled rate

Preliminary figures, computed at $0 from the committed readouts before the run:

| Pool | Retries | Any blocking fail added | F9_cta_fact added |
|---|---|---|---|
| primary r5 + r6 + r7 | 75 | 8 = 10.7% [5.5%, 19.7%] | 6 = 8.0% [3.7%, 16.4%] |
| + AA-768 sets | 100 | 10 = 10.0% [5.5%, 17.4%] | 6 = 6.0% [2.8%, 12.5%] |
| current code (r7 + r7 AA-768) | 31 | 4 = 12.9% [5.1%, 28.9%] | 3 = 9.7% [3.4%, 24.9%] |

Run output: _pending_. This includes the sentence-family rate, the variant that ignores F17 (the r6 F17 adds were
fixed by #767) and natural_post_r7.

## 5. Classification

_pending_. Table columns: set · piece · k · mode · gate added · sentence · judge reason · location
(repaired / unchanged / two-sentence) · class (C1/C2/C3) · note.

Known before the run: none of the 3 r7 F9 adds was a repair target. The repairs touched only F15, F14, F17 and F18
items. F9 passed at attempt 1 and flagged again at attempt 2. The dump decides whether each flagged sentence was
style-repaired or left unchanged and missed by the sticky pass.

## 6. Decision

_pending_. The options, in order of preference:

- (a) Extend the sticky pass. A sentence whose only change is the repair edit stays sticky: deletion-only edits,
  and style edits that add no new content word.
- (b) Make F9 on a repaired sentence a warning instead of a block. This weakens the writer source-fidelity policy,
  so it is used only if the data rules out (a).
- If C1 dominates, neither option fits. A deterministic post-check on the replacement is needed, in the style of
  r6 fix 1.

## 7. Re-measure

_pending, only if a fix ships._ The re-measure has two parts, within a $1.5 cap:

1. A $0 counterfactual replay of the new rule on the pooled retries' stored ledgers and quotes.
2. One live round of 20 + 5 pieces, costing about $1.0, using the r7 enqueue, driver and readout scripts.
