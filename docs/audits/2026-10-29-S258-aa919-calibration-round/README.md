# AA-919: calibration labelling round (Facebook and the other thin strata) — prep, $0

Session S258, 29/10/2026. Agent: Claude Code (lane eval-prep). No model call was made; nothing ran on Dev yet.
CIS branch `feat/aa-919-calibration-labelling-round` holds the code; the operator scripts are in the private
`.tmp-session/S258/eval-prep/aa919/` (RUNBOOK.md there has the exact commands).

## Why

The R2 gate counts the judge only when kappa ≥ 0.6 on ≥ 10 labelled pairs with ≥ 3 of each label. The S257 picker
(`docs/audits/2026-10-29-S257-aa919-judge-compare/calibration-candidates-s257.json`, golden set `aa729@1.2.0`) found:

| Writer | Labelled pairs | Gaps (label class under 3 per stratum) |
|---|---|---|
| t9_social | 13 (8 pass / 5 fail), all LinkedIn | **Facebook: 0 pass, 0 fail** (needs 3 + 3); per tenant: 6 small gaps; held / known_failure pass +1 each |
| t9_blog | 13 | 2 tenant gaps, held / known_failure pass +1 each |
| t2 | 8 (below the 10-pair minimum) | overall pass +2, 7 tenant / tier gaps |
| a1 | 50 (6 pass / 44 fail) | tier gaps (culinary, water, wildlife, fact_dense, ... pass); the picker cannot target tour-type tiers yet |

**The data constraint:** the S257 pool held **one** freezable Facebook piece (`by_channel: linkedin 122, facebook 1`).
Six Facebook pairs (more with oversampling, because labels do not split evenly) cannot come from stored pieces unless
the census below finds more. If it does not, the stratum needs new Facebook pieces: a T8 + T9 run on Facebook for the
demo tenants, which calls the writer models (paid, and blocked while the LLM path is down). Labels are never invented
to fill a stratum.

## What was built (CIS branch, $0)

- `select_samples --ids <picker report | id list> --base-version 1.2.0`: freezes only the chosen ids, with the same
  freezers as the 1.0.0 selection, from every tenant channel (Facebook included). Facebook samples are `t9f-NNN`,
  stratum `t9_social`. Post-edit outputs are left out (they never calibrate). Existing labels the importer cannot take
  (reviews, audit verdicts) go to the panel with the old label kept as evidence.
- The label pack now shows the panel the full T9 source in the judge's layout (seed, scope, trip, angle brief, goal,
  brand pack, channel, writer asks, facts), uncut. Before, it showed only the seed, facts, CTA and brand name.
- `labels merge fixture-1.2.0.json addendum-labelled.json` makes fixture 1.3.0: it refuses duplicates, unlabelled
  samples, a wrong base; it continues the sample numbering and keeps old items on the brand pack they were written with.
- The importer accepts the `t9_social` stratum (needed in the deployed container before the 1.3.0 import).

## Labelling guide (for the agent that labels the addendum)

The round follows the S245 panel design (CIS `docs/implementation-notes/AA-729.md`, "Panel round 1") with the S256
rubric rules. Claude Code agents label; the business owner (or the tech lead under the session plan) approves.

1. **Input**: `pack.json` / `pack.md` from `labels export-pack` on the addendum. Each item has the sample id, stratum,
   channel, tags (without `held` / `known_failure`), the full source and the output. The pack never shows the
   pipeline's verdict, gate results or flags: do not look them up in the DB either.
2. **Rubric** (in the pack, `rubric`): pass = publishable as is or after a light edit; fail = needs a heavy edit or a
   rewrite. Grades: `as_is` / `light` = pass, `heavy` / `reject` = fail. The five rules decide the borderline cases:
   - every customer-facing field counts (body, title, SEO title, meta description, hashtags);
   - a claim the source does not support fails even when one phrase would fix it (wrong or invented fact, a fact the
     source contradicts, a promise about the trip the itinerary does not make);
   - a light edit changes wording only (typos, repetition, garbled but true phrasing, an imprecise but not false
     paraphrase, a brief point left out);
   - reflection that states no fact is voice, not a claim;
   - the brief and the brand pack are part of the source.
   Facebook adds nothing to the rubric: hashtags and the first line are customer-facing fields like any other.
3. **Panel per item**: three judges with different lenses (source fidelity; voice and structure; reader), each giving
   verdict + grade + one-sentence reason, then one **verifier** who reads the WHOLE source and checks every fact the
   judges or the output name. Agreed = the verifier matches the judges' majority. Disputed = the verifier overturns
   the majority: the item goes to the approver with the verifier's side proposed.
4. **Output** `panel.json`: `{"<sample_id>": {"verdict": "pass|fail", "grade": "as_is|light|heavy|reject",
   "reason": "<the deciding fact, quoting the output phrase>", "votes": [<4 votes>], "status": "agreed|disputed"}}`.
   Reasons quote output phrases and name the source section that supports or lacks them; no email or phone numbers.
5. **Approval**: the approver reads the disputed items (a click-to-approve page, as in S245) and the agreed counts;
   `labels apply ... --approved-by <approver>` writes agreed labels; disputed ones only with `--include-disputed`
   after a decision.
6. **Enough?** After `labels merge`, the local importer DRY RUN (`--no-db`) prints the counts per writer and split.
   Target per T9 social channel and per tenant: ≥ 3 pass and ≥ 3 fail. If a class is still short, pick more ids
   (picker `--stratum-target 3 --oversample 3`) and run a second addendum against 1.3.0 rather than relabelling.

## Do not

- Do not label from the pipeline verdict, the held reason or the judge's output.
- Do not relabel existing 1.2.0 items in this round (relabels go through `labels relabel` with a review file).
- Do not put the addendum, the pack or the fixture (tenant text) into a repo; keep them in `.tmp-session/` and bronze S3.

## Live order (orchestrator)

1. Census ($0): `fb_census.py` → how many freezable Facebook pieces exist, per tenant.
2. Picker ($0): `cc_run_s258.py` (fresh gaps and candidate ids, 2x oversampled).
3. Freeze ($0, read-only DB, writes one bronze object): `freeze_run_s258.py` built from the picker report.
4. Local: export-pack → panel → apply → merge → importer `--no-db` DRY RUN.
5. Merge + deploy the CIS PR; upload `fixture-1.3.0.json`; importer DRY RUN → `--apply`; regenerate the text-guard
   fingerprints with the key; R2 DRY RUN (expect Facebook in `calibration_strata`).
6. When the LLM path is back: R2 step D and the judge-model comparison on 1.3.0.
