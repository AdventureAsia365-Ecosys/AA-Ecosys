# AA-924 replay: the T10 gate fold on stored T9 pieces (S250)

AA-924 PR1 folds F2_banned_patterns + F2_brand_forbidden + the F15 stock list into one **F2_lexicon** ledger entry
and F15_voice + F15_voice_warn into one **F15_voice** entry, each finding with its own block / warn severity
(26 → 24 distinct results: 23 blog, 22 LinkedIn, 21 other channels). Routing reads the legacy view of the ledger,
so no passed / held decision should change. This replay checks that on stored pieces, at $0.

- **Harness:** AA-CIS-App `scripts/quality/replay_aa924.py` (branch `feat/aa-924-lexicon-gate-severity`).
- **Base tree:** `074676b2` (AA-926 S250 branch head, before AA-924). **Head:** `4d9f940e` (AA-924 PR1 after the
  review round). Both SHAs are pre-rebase: the CIS branch is rebased onto `origin/main` once AA-926 (#982) is
  merged, and the replay is re-run with base = that `origin/main` (the SHAs here are then updated).
- **Method:** `run_quality_gates` on each stored final text, with the gate inputs rebuilt the way the writer builds
  them (`scripts/aa729/score.py::t9_gate_replay`). The F9 judge is not called: it returns the F9 entries stored in
  the piece's own ledger (the real verdicts). A stored failing F10 entry is turned back into its similarity match.
  Each piece runs in four modes: attempt 1 (`stock_blocking=True`) and a later attempt (`stock_blocking=False`),
  each on the stored text and (`_dashfix`) on the stored text after `hygiene.fix_dashes`. Base and head get the
  same inputs, so any difference comes from the code change. No LLM call, no DB, no network.
- **Compared per piece and mode:** passed, status, first failure, hold, repair route, style-only stage, the
  blocking failures and flags of the legacy view, the held gate, and (review round) `plan_problems`: the gate,
  sentence and problem of every sentence-repair item, so a change in what the repair is told shows up.

## Status

| Set | Pieces | Routing differences | State |
|---|---|---|---|
| AA-729 golden T9 samples (15 t9_blog + 15 t9_linkedin) | 30 × 4 modes | **0** (plan problems included) | done (below) |
| S234 r1–r4 final pieces | expected 80 × 4 modes | not run | **needs the read-only export** (steps below) |

**What this evidence covers.** Until the S234 rows are in, the evidence is the golden set only. In the two
stored-text modes, 15 of 30 pieces fail first on `F2_banned_patterns` em-dashes in texts stored before AA-778 (290
findings over all rows), and 21 of 30 are held, so for most of them first failure, hold, route and status are
trivially equal. The writer now runs `hygiene.fix_dashes` before the gates, so the `_dashfix` modes are the
realistic input: there no piece fails first on F2, 15 of 30 are held, and the first failures spread over F9, F13,
F14, F15_voice, F16 and F17, which exercises the F15, waive and style-only paths. Both pairs give 0 differences.

## Golden set (root `docs/eval/aa729/fixture-1.1.0.json`)

Reading: 0 differences in passed, status, first failure, hold, repair route, stage and repair-plan problems, in all
four modes. The stored warn flags move as designed: F15_voice_warn → F15_voice, and F15_voice's stock lines →
F2_lexicon. Counts below are over all 120 rows (30 pieces × 4 modes).

### Decisions, base vs head

| source | mode | pieces | approved→approved | held→held | approved→held | held→approved | errors |
|---|---|---|---|---|---|---|---|
| golden | attempt1 | 30 | 9 | 21 | 0 | 0 | 0 |
| golden | later | 30 | 9 | 21 | 0 | 0 | 0 |
| golden | attempt1_dashfix | 30 | 15 | 15 | 0 | 0 | 0 |
| golden | later_dashfix | 30 | 15 | 15 | 0 | 0 | 0 |

### Differences in routing decisions (0)

None: passed / status / first failure / hold / repair route / stage are identical.

### Other differences (0)

Blocking failures of the legacy view, legacy-view flags, `plan_problems` and the held gate (base name mapped through
the fold). Expected: none, except a word that was judged in two gates before (now judged once). None.

### Head: first failure (legacy source) per mode

| mode | none | F2_banned_patterns | F9_cta_fact | F13_leak | F13_repeat | F14_first_line | F15_voice | F16_faq | F17_trip_fact |
|---|---|---|---|---|---|---|---|---|---|
| attempt1 | 9 | 15 | 3 | 0 | 0 | 1 | 0 | 1 | 1 |
| later | 9 | 15 | 3 | 0 | 0 | 1 | 0 | 1 | 1 |
| attempt1_dashfix | 14 | 0 | 5 | 1 | 2 | 2 | 2 | 1 | 3 |
| later_dashfix | 15 | 0 | 6 | 1 | 2 | 2 | 0 | 1 | 3 |

### Warn flags by stored name (all rows)

| flag | base | head |
|---|---|---|
| F12_scope | 12 | 12 |
| F13_hygiene | 8 | 8 |
| F14_social_shape | 4 | 4 |
| F15_voice | 4 | 12 |
| F15_voice_warn | 12 | 0 |
| F17_trip_fact | 4 | 4 |
| F2_lexicon | 0 | 4 |
| F2_style_warn | 4 | 4 |
| F9_brand_style | 12 | 12 |

### Head: findings of the merged entries (gate / source / severity)

| finding | count |
|---|---|
| F15_voice / F15_voice_warn / warn | 12 |
| F2_lexicon / F15_voice / block | 4 |
| F2_lexicon / F15_voice / warn | 4 |
| F2_lexicon / F2_banned_patterns / block | 290 |

### Results per ledger

| source | base: results (rows) | head: results (rows) |
|---|---|---|
| golden | 24 (60), 25 (60) | 22 (60), 23 (60) |

### Context: head (later-attempt mode) vs the stored status

This is not a test of AA-924: the stored status came from older code and the full repair loop. It shows how close the
replay inputs are to production.

| source | same | different |
|---|---|---|
| golden | 23 | 7 |

## S234 pieces: how to run (orchestrator, needs MFA)

The S234 texts are no longer on disk (S248 cleanup) and S3 has no copy. Export them read-only from
`acp_shared.content_piece` with `export_s234_pieces.py` in this folder:

- asyncpg, the container's `DATABASE_URL` (role `cis_app`), `ssl="require"`, one READ ONLY transaction, SELECT only.
  No LLM call.
- Selection: the angle requests of the 40 S234 panel pieces (embedded as `ANCHORS`), and every approved / held T9
  piece of those requests between the first and last anchor's `created_at` ± 3 h. Expected: 80 (32 blog, 48
  LinkedIn).
- Pieces without `writer_input` are counted in the notes and skipped by the replay.

Every AWS CLI command goes on one line (WSL2), profile `aa365-admin`, after
`aws sts get-caller-identity --profile aa365-admin`:

```bash
aws s3 cp docs/audits/2026-10-24-S250-aa924-replay/export_s234_pieces.py s3://aa-cis-bronze-005097885195/scripts/aa924_export.py --profile aa365-admin --region us-west-1
URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/aa924_export.py --profile aa365-admin --region us-west-1 --expires-in 300)
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/s.py && python3 /tmp/s.py --s3 s3://aa-cis-bronze-005097885195/scripts/out/aa924_s234.json.gz'" --profile aa365-admin --region us-west-1
aws s3 cp s3://aa-cis-bronze-005097885195/scripts/out/aa924_s234.json.gz .tmp-session/s250/aa924-replay/aa924_s234.json.gz --profile aa365-admin --region us-west-1
```

If the task role cannot write `scripts/out/`, run the same exec with `--gzip` instead of `--s3 …`. Copy the base64
block between `AA924-BEGIN` and `AA924-END` to a file and `base64 -d` it into `aa924_s234.json.gz`.

Then run the replay from the AA-924 CIS worktree. The base worktree is a detached checkout of `074676b2`, or of
`origin/main` once AA-926 is merged:

```bash
python -m scripts.quality.replay_aa924 all --base-tree <base-worktree> --golden <root>/docs/eval/aa729/fixture-1.1.0.json --s234 <root>/.tmp-session/s250/aa924-replay/aa924_s234.json.gz --out-dir <root>/.tmp-session/s250/aa924-replay --report <root>/.tmp-session/s250/aa924-replay/report-all.md
```

Then:

1. Paste the S234 rows of `report-all.md` into this README (the golden rows stay as above).
2. Copy the numbers into the PR and into `docs/implementation-notes/AA-924.md`.
3. List each passed / held difference with its reason.
4. Once the replay is done, delete the export: it holds tenant names and `writer_input`. Remove the S3 objects
   `scripts/out/aa924_s234.json.gz` and `scripts/aa924_export.py` in the bronze bucket (orchestrator step), and the
   local `.tmp-session/s250/aa924-replay/aa924_s234.json.gz`, `base.json` and `head.json`, which carry the same texts.

Expected: 0 routing differences. The only expected "other" difference is a word that was judged in two gates before:
a tenant-forbidden word that is also a platform-truth word, now judged once, by F2_lexicon.
