# AA-1048 — claim instrument prompt v2: gated evaluation (S279, 13/11/2026)

Run on Dev through ECS exec (`python -m services.ground_truth.instrument_eval run`, CIS a94ddec7), pool = the 286 claims
R1 fired on (scratch only, removed from S3 after the run). Instrument `gpt-6-luna-openai@openai-direct:entailment#v2`,
prompt version `aa1048-r1-v2@ddaab8c279ef`, 3 votes per claim, majority decides.

| Run | run_id | Claims | Calls | Spent (ledger) | Verdict |
|---|---|---|---|---|---|
| Trial | eaa18a85 | 3 | 9 | 0.001471 USD | trial (no verdict) |
| Full | 3018008d | 50 | 150 | 0.031648 USD | **no_go** |

Ledger (`shared.llm_call_log`, stage `adhoc_aa1048`, by run_id): 9/9 and 150/150 rows, 0 not ok, prompt_version as above.
Plan estimate was 0.51 USD; actual 0.032 USD (cap 1.5 USD from setting `cis.spend.instrument_eval_cap_usd`).

## Score (bars from settings: FP dropped >= 60 %, TP kept >= 90 % on out-of-sample stored violations)

| Measure | Result | Bar |
|---|---|---|
| False positives dropped | 12 / 25 = 48 % | 60 % — fails |
| Stored violations kept (out of sample) | 18 / 20 = 90 % | 90 % — passes |
| Relabelled violations kept (in sample, not gated) | 5 / 5 | — |
| Precision / recall | 0.58 / 0.90 | — |

By false-positive group: verbatim 4/4 dropped, paraphrase 7/17, place background 1/4.

## Reading

- v2 fixes the verbatim misses completely and half the paraphrase misses, without losing stored violations beyond the bar.
- It is not enough to replace v1: paraphrase (10 still firing) and place-background (3 still firing) carry the remaining
  false positives. This matches the B3 check in the v2 notes (place background was not the main driver).
- Next: a v3 that targets paraphrase entailment (accept a sentence when the source states the same fact in other words,
  with the sentence-level context v2 already sends), measured on the same subset first at $0 against the stored votes,
  then one gated run (~0.03 USD). v1 stays the live instrument until a version passes both bars.

Full report (counts, groups and hash prefixes only): `instrument-v2-eval.json`.
