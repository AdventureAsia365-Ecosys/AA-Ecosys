---
id: APP-06-re-embed
title: Re-embed a vector column into another embedding space
description: How to move CIS vector columns to another embedding model (a planned change, or the Cohere Embed v4 vendor lost) without ever mixing two vector spaces - dry run, fallback switch and probe, shadow column, resumable capped fill, swap, rollback, cleanup - and the T-15 test on the smallest table.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, aa-cis-dev-db, aa-tripplanner-browse]
last_reviewed: 2026-11-01
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [APP-06, OPS-05-db-migrate, OPS-05-ecs-exec, APP-06-anthropic-key, AA-1026]
---

# Re-embed a vector column into another embedding space

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step. The T-15 test below is the first run.

Source of truth: AA-CIS-App migrations `340_embedding_space_registry.sql` and
`341_embedding_reembed_tools_titan_fallback.sql`, `shared/llm_client/embedding_space.py`, `shared/llm_client/embed.py`,
`services/embeddings/reembed.py`, `services/jobs/embedding_reembed_job.py`, `docs/implementation-notes/AA-1026-gw-embed.md`;
AA-CIS-Infra `db/scripts/aa1026_embedding_shadow.py`; AA-TripPlanner-Web `backend/shared/embedding_space.py`.

## The idea in five lines

- A **space** is one embedding model at one dimension: `cohere-embed-v4/1536/v1` today (served by `cohere-embed-v4`
  on acc2 and `cohere-embed-v4-acc3`, the same vector). Vectors of two spaces are never stored in one column or
  compared in one query.
- `shared.embedding_column` gives every vector column its space and its **swap group**: columns compared with each
  other or written by one stage move together (`f10_embed` = atom, question and content piece vectors; `tour_place`;
  `published_tours`).
- The **fallback space** is `titan-embed-text-v2/1024/v1`: Amazon Titan Text Embeddings V2, another vendor, on acc2 in
  us-west-2 (connection `acc2-usw2`, **off** until this runbook switches it on). Different dimension, so it is only
  reached by a re-embed, never by a route fallback.
- A move is: new vectors into `<column>__shadow` (resumable, capped job) → **swap** the whole group in one transaction
  (old vectors kept as `<column>__prev`, dependent views rebuilt, registry updated) → writers and searches embed in the
  new space within 60 s, no code change.
- Rollback while `__prev` is kept: `shared.embedding_rollback`. Cleanup after a week: drop `__prev`.

## When to use

| Situation | What to do |
|---|---|
| Planned model change (cheaper, better, a new version) | The whole procedure, group by group, on a tech lead yes with a cost cap per run. |
| **Incident: the embedding model or vendor is gone** (Cohere refused on acc2 and acc3, the model retired, the account blocked) | See [Incident: Cohere Embed v4 lost](#incident-cohere-embed-v4-lost) first, then this procedure for `f10_embed` and `tour_place`. |
| One account down, the other still answers (for example acc2 throttled, acc3 fine) | Nothing: the route already falls back to `cohere-embed-v4-acc3`, the same space. |
| T-15: prove the machinery before AA-1004 changes acc2 billing / organization | [The T-15 test](#the-t-15-test-question_embedding-under-1-usd) (shadow fill on `question_embedding`, no swap). |

## Incident: Cohere Embed v4 lost

What degrades while no embedding model answers (all of it soft, nothing is corrupted):

- T9 writing: `content_embedding` stays NULL (cannibalization gate sees no near-duplicates; the piece still saves).
- A3 atom ranking: question landing falls back to claim-by-name for atoms or questions without a vector.
- `place_extract`: new place texts cannot be embedded; the job fails and retries (places already embedded are fine).
- TripPlanner search: keyword ranking (reason `embed_error`), map and browse unaffected.

Decide in this order:

1. **Is it really the model, not one account?** `GET /admin/llm-connections` and the ledger: refusals on both `acc2`
   and `acc3` for `cohere-embed-v4*` (error class `access_denied` / `quota_exhausted`). One account refused = no action.
2. **Will it come back within a day?** (an AWS case, a billing fix) Then wait: nothing above loses data, and a
   re-embed of everything costs time, not much money. Write the decision in the incident note.
3. **Otherwise move to the fallback space.** Order: `f10_embed` group first (T9 and A3 depend on it; about 12,000
   short texts), then `tour_place` (13,500 place texts; TripPlanner needs its own change first, see
   [TripPlanner](#tripplanner-and-the-tour_place-group)), `published_tours` last (no writer, see below).
   Cost at Titan V2 prices (0.02 USD per 1M tokens): well under 0.10 USD for everything; the dry run gives the number.
4. **Other way out**: OpenAI `text-embedding-3-small` (1536 dims, vendor API, tech lead decision T-3 allows a vendor
   API when the AWS paths are blocked) is not catalogued for embeddings yet: adding it is a code change in
   `shared/llm_client/embed.py` (an OpenAI request shape) plus a catalog / space row. Titan is ready today.

## Before you start

- CIS migrations 340 and 341 applied on Dev (`shared.schema_versions` has both), the CIS code deployed (api and worker
  on the same SHA), Infra `db/scripts/aa1026_embedding_shadow.py` on Infra `main`.
- A tech lead yes for the paid part with a cap (`cost_cap_usd`), per run.
- For a **swap**: job tables idle (DB Migrate checks it) and no open wave.

## 1. Confirm the account

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account of the [account map](../../onboarding.md#account-map). Abort on any other account.

## 2. Read the registry ($0)

```bash
ADMIN_SECRET=$(aws secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --query SecretString --output text --profile aa365-admin --region us-west-1)
curl -s https://api-cis.lumiguides.it.com/admin/job-runner/embedding-spaces -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" | python3 -m json.tool
```

Expected: `"source": "registry"` (not `builtin`), two spaces (`cohere-embed-v4/1536/v1` active,
`titan-embed-text-v2/1024/v1` standby), five columns, every `space_key` = `cohere-embed-v4/1536/v1`, no
`shadow_column` / `previous_column` unless a move is under way.

## 3. Dry run per column ($0, no provider call)

```bash
curl -s -X POST https://api-cis.lumiguides.it.com/admin/job-runner/embedding-reembed/run -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" -H "content-type: application/json" -d '{"mode": "dry_run", "column": "acp_contract.question_embedding.embedding", "space_key": "titan-embed-text-v2/1024/v1"}'
curl -s https://api-cis.lumiguides.it.com/admin/job-runner/jobs/<job_id> -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" | python3 -m json.tool
```

Expected result: `rows`, `blank_rows`, `chars`, `estimated_tokens`, `estimated_usd`, `requests`, `prepared: false`
and `next_steps` (the exact owner calls). Repeat for every column of the group. `published_tours.content_embedding`
answers 422/failed "no re-embed text source": it has no writer, see [published_tours](#published_tours).

## 4. Switch the fallback connection on and probe it (< 0.0001 USD)

Switching `acc2-usw2` on moves no stage route: nothing routes to Titan unless a column's space says so.

```bash
curl -s -X PATCH https://api-cis.lumiguides.it.com/admin/llm-connections/acc2-usw2 -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" -H "content-type: application/json" -d '{"enabled": true}'
curl -s -X POST https://api-cis.lumiguides.it.com/admin/job-runner/embedding-reembed/run -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" -H "content-type: application/json" -d '{"mode": "probe", "space_key": "titan-embed-text-v2/1024/v1"}'
```

Expected probe result: `"ok": true`, `"model_used": "titan-embed-text-v2"`, `"account": "acc2-usw2"`,
`"dimension": 1024`, and one `shared.llm_call_log` row, stage `adhoc_conn_test`, role `embed`,
`quality_signal.embedding_space = titan-embed-text-v2/1024/v1`. Abort on `"ok": false`: the error names the cause
(AccessDenied = IAM or the region SCP; ValidationException = model access not granted in us-west-2). The registry
cache is 5 minutes: if the probe says "no usable deployment" right after the PATCH, wait and retry.

## 5. Prepare the shadow column (owner, DB Migrate run-script)

In a one-line Infra PR set, in `db/scripts/aa1026_embedding_shadow.py`: `ACTION = "prepare"`,
`COLUMN = "<schema.table.column>"`, `SPACE = "titan-embed-text-v2/1024/v1"`; first with `MODE = "dry_run"` (as
merged), then `MODE = "apply"`. Dispatch:

```bash
gh workflow run db-migrate.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f environment=dev -f mode=run-script -f script=db/scripts/aa1026_embedding_shadow.py
```

Expected: `SCRIPT done action=prepare result=<column>__shadow`, then a `SCRIPT column` line with `shadow_space` set.
It adds a nullable `vector(1024)` column (a catalog-only change, no rewrite). Once per column of the group.

## 6. Fill the shadow (paid, capped, resumable)

```bash
curl -s -X POST https://api-cis.lumiguides.it.com/admin/job-runner/embedding-reembed/run -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" -H "content-type: application/json" -d '{"mode": "fill", "column": "acp_contract.question_embedding.embedding", "cost_cap_usd": 1}'
```

Watch the job on the Jobs page (progress: `written`, `blank`, `calls`, `spent_usd`, `last_key`). Result:
`complete: true` when every row with a vector has a shadow vector (`remaining_rows` = `remaining_blank_rows`).
`stopped: cost_cap` or a failure: queue the same payload again; it continues where it stopped (it only reads rows
whose shadow is still empty). Each call writes one ledger row (stage = the column's writer stage, role `embed`,
`quality_signal.op = reembed`, `embedding_space`). Writers keep writing the serving column in the old space during
the fill; re-run the fill right before the swap to catch the rows they added.

## 7. Index the shadow (only for a column that has a vector index)

`atom_embedding` (`idx_atom_embedding_vector`, ivfflat lists 10), `tour_place` (`tour_place_embedding_hnsw`, hnsw),
`content_piece` (`idx_content_piece_embedding`, ivfflat lists 10), `published_tours` (`idx_pt_embedding`). Name the
new index `<old index name>__shadow` so the swap renames it into place; build it after the fill (ivfflat learns its
lists from the data), with `CREATE INDEX CONCURRENTLY IF NOT EXISTS ... ON ... USING <same method> (<column>__shadow
vector_cosine_ops) [WITH (lists = 10)]` in its own no-transaction cis/ file (DB Migrate). `question_embedding` has no
vector index: skip.

## 8. Swap the group

- Job tables idle, no wave. Fill re-run last (step 6) so `remaining_rows` = `remaining_blank_rows` for every column.
- `f10_embed` group (no catalog view reads these columns): the Infra script with `ACTION = "swap"` (dry run, then
  apply). Expected `SCRIPT done action=swap result=3`.
- `tour_place` group: its dependent views (`catalog.v_component_embedding`, `catalog.v_tour_component`) belong to
  `catalog_owner`, which the master login may not act as. Swap it with a one-line **cis/ migration** applied by DB
  Migrate (db_migrator may), guarded so it replays as a no-op elsewhere:

  ```sql
  BEGIN;
  DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM shared.embedding_column WHERE swap_group = 'tour_place' AND shadow_column IS NOT NULL) THEN
          PERFORM shared.embedding_swap('tour_place');
      ELSE
          RAISE NOTICE 'tour_place has no prepared shadow here: nothing to swap';
      END IF;
  END $$;
  INSERT INTO shared.schema_versions (version, applied_at, description) VALUES ('<NNN>', now(), 'AA-1026 swap tour_place') ON CONFLICT (version) DO NOTHING;
  COMMIT;
  ```

What the swap does: refuses while a row has a vector but no shadow vector; drops the dependent views (deepest first),
renames `<column>` → `<column>__prev` and `<column>__shadow` → `<column>` (NOT NULL and single-column indexes follow),
recreates the views from their own definition as their owners with their options, grants and comments, marks the
registry (`space_key` = the new space, `previous_*` = the old one) in the same transaction.

After the swap: redeploy api and worker with no code change (`aws ecs update-service ... --force-new-deployment`, one
line each) so no process keeps a cached registry (60 s) or a prepared statement over the renamed column.

Verify: step 2 shows the group's columns in the new space with `previous_column` set; one new T9 piece / A3 run /
place extract writes ledger rows with `embedding_space = titan-embed-text-v2/1024/v1`; the CIS daily data coverage
counts are unchanged.

## 9. Rollback (while `__prev` is kept)

The Infra script with `ACTION = "rollback"` (or the guarded migration form for `tour_place`). Rows written after the
swap have no old vector: the rollback refuses with their count. For the f10 caches delete those rows (they are
re-embedded on demand: `atom_embedding` / `question_embedding` rows created after the swap time) or set
`ALLOW_MISSING = True` (the column then stays nullable). After a rollback the new vectors sit in the shadow again: a
later swap needs only a fill catch-up.

## 10. Cleanup (destructive, after 7 days without a rollback)

`shared.embedding_drop_previous('<group>')` drops the kept old vectors: no rollback after it. It follows the DRY RUN
procedure (`skill/aa-cis-schema/references/destructive-ops.md`) as its own reviewed script; switch the old space to
`retired` in a migration if it will not come back. To abandon a fill instead: `ACTION = "drop_shadow"`.

## TripPlanner and the tour_place group

TripPlanner search reads the space of `geo.tour_place.embedding` from `catalog.v_embedding_space_v1` and embeds the
query only in it. Its client builds only the Cohere request at 1536 dims today: after a swap of `tour_place` to Titan
it answers with keyword ranking (reason `embedding_space_mismatch`) until a TripPlanner change adds the Titan request
shape. Ship that change before swapping `tour_place` when the outage is long.

## published_tours

`gold_aa_internal.published_tours.content_embedding` has had no writer since migration 041 and no text source: it
cannot be re-embedded. Swap its group with `ALLOW_MISSING = True` only if a reader needs it in the new space (the
column is then empty); otherwise leave it in the old space (nothing compares it with the other groups).

## The T-15 test (question_embedding, under 1 USD)

Tech lead decision T-15 (S263): prove the machinery on the smallest table before AA-1004 changes acc2 billing or
organization. No swap: the serving column is untouched.

1. Step 2 (registry), step 3 dry run for `acp_contract.question_embedding.embedding` into
   `titan-embed-text-v2/1024/v1`. Expected about 1,000 rows and `estimated_usd` well under 0.01. Stop if over 1 USD.
2. Step 4: connection `acc2-usw2` on, probe `"ok": true`.
3. Step 5: Infra script `ACTION = "prepare"`, `COLUMN = "acp_contract.question_embedding.embedding"` (dry run, apply).
4. Step 6: fill with `"cost_cap_usd": 1`. Expected `complete: true`, `spent_usd` < 0.01, `calls` about the row count
   divided by 16 (Titan pages), ledger rows with `quality_signal.op = reembed`.
5. Verify (as `cis_app`, [ECS exec](ecs-exec-s3-mediated.md)):
   `SELECT count(*) AS n, count(embedding__shadow) AS shadow, min(vector_dims(embedding__shadow)) AS dims FROM acp_contract.question_embedding;`
   expected `shadow = n` (minus blank questions), `dims = 1024`; and
   `SELECT count(*), sum(cost_usd) FROM shared.llm_call_log WHERE quality_signal->>'op' = 'reembed' AND created_at > now() - interval '1 hour';`
6. Clean up: Infra script `ACTION = "drop_shadow"` (apply), connection `acc2-usw2` off (PATCH `{"enabled": false}`),
   step 2 shows no shadow. Record the run below.

## Test log

| Date | Where | Who | Evidence | Result |
|---|---|---|---|---|
| - | - | - | - | not run yet (T-15 pending) |
