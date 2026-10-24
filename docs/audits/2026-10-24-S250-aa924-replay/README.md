# AA-924 replay: the T10 gate fold on stored T9 pieces (S250)

AA-924 PR1 folds F2_banned_patterns + F2_brand_forbidden + the F15 stock list into one **F2_lexicon** ledger entry
and F15_voice + F15_voice_warn into one **F15_voice** entry, each finding with its own block / warn severity
(26 → 24 distinct results: 23 blog, 22 LinkedIn, 21 other channels). Routing reads the legacy view of the ledger,
so no passed / held decision should change. This replay checks that on stored pieces, at $0.

- **Harness:** AA-CIS-App `scripts/quality/replay_aa924.py` (branch `feat/aa-924-lexicon-gate-severity`).
- **Base tree:** `074676b2` (AA-926 S250 branch head, before AA-924). **Head:** `f584d811` (AA-924 PR1).
- **Method:** `run_quality_gates` on each stored final text, with the gate inputs rebuilt the way the writer builds
  them (`scripts/aa729/score.py::t9_gate_replay`). The F9 judge is not called: it returns the F9 entries stored in
  the piece's own ledger (the real verdicts). A stored failing F10 entry is turned back into its similarity match.
  Each piece runs twice: as attempt 1 (`stock_blocking=True`) and as a later attempt (`stock_blocking=False`).
  Base and head get the same inputs, so any difference comes from the code change. No LLM call, no DB, no network.

## Status

| Set | Pieces | Routing differences | State |
|---|---|---|---|
| AA-729 golden T9 samples (15 t9_blog + 15 t9_linkedin) | 30 × 2 modes | **0** | done (below) |
| S234 r1–r4 final pieces | expected 80 × 2 modes | not run | **needs the read-only export** (steps below) |

## Golden set (root `docs/eval/aa729/fixture-1.1.0.json`)

Reading: there are 0 differences in passed, status, first failure, hold, repair route and stage, in both modes. The
stored warn flags move as designed: F15_voice_warn → F15_voice, and F15_voice's stock lines → F2_lexicon. The 290
`F2_lexicon / F2_banned_patterns / block` findings are em-dashes in texts stored before AA-778 (145 per mode). Base
and head both block on them, so the held count (21 of 30) reflects old stored texts, not AA-924.

### Decisions, base vs head

| source | mode | pieces | approved→approved | held→held | approved→held | held→approved | errors |
|---|---|---|---|---|---|---|---|
| golden | attempt1 | 30 | 9 | 21 | 0 | 0 | 0 |
| golden | later | 30 | 9 | 21 | 0 | 0 | 0 |

### Differences in routing decisions (0)

None: passed / status / first failure / hold / repair route / stage are identical.

### Other differences (0)

Blocking failures of the legacy view, legacy-view flags and the held gate (base name mapped through the fold).
Expected: none, except a word that was judged in two gates before (now judged once). None.

### Warn flags by stored name (all rows)

| flag | base | head |
|---|---|---|
| F12_scope | 6 | 6 |
| F13_hygiene | 4 | 4 |
| F14_social_shape | 2 | 2 |
| F15_voice | 2 | 6 |
| F15_voice_warn | 6 | 0 |
| F17_trip_fact | 2 | 2 |
| F2_lexicon | 0 | 2 |
| F2_style_warn | 2 | 2 |
| F9_brand_style | 6 | 6 |

### Head: findings of the merged entries (gate / source / severity)

| finding | count |
|---|---|
| F15_voice / F15_voice_warn / warn | 6 |
| F2_lexicon / F15_voice / block | 2 |
| F2_lexicon / F15_voice / warn | 2 |
| F2_lexicon / F2_banned_patterns / block | 290 |

### Results per ledger

| source | base: results (rows) | head: results (rows) |
|---|---|---|
| golden | 24 (30), 25 (30) | 22 (30), 23 (30) |

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

Expected: 0 routing differences. The only expected "other" difference is a word that was judged in two gates before:
a tenant-forbidden word that is also a platform-truth word, now judged once, by F2_lexicon.
