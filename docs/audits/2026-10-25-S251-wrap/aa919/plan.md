# AA-919 plan: WM-17, WM-18 and WM-20 in one AA-CIS-App PR series

The series needs **two new migrations, 282 and 283**, and **four CIS PRs** (A to D), plus one Infra copy PR and one root registers PR. No LLM call is made anywhere in the series, so the cost is $0, apart from one optional rollback drill on a T9 social piece that costs a few cents.

The Content quality gate freeze holds. The series adds no gate and changes no prompt bytes. Prompts that are pinned today must stay byte-identical, and that is enforced by sha256 pins captured on `main` before any refactor. Release-0 activation ships now. Activating a release that carries rules (any `content_class` other than `empty`) is refused by the API until WM-23, WM-24 and WM-25.

## 0. Facts checked in the repo (read-only, 2026-10-25)

**Repo state**
- The local CIS checkout is at `414e3236`, which equals `origin/main`. The map's `1e643cde` is stale.

**Migration numbers**
- The highest file is `281_schema_drift_reconcile.sql`. The live dump says 280 is applied.
- No CIS branch, Infra branch or `.tmp-session/wt/*` worktree holds a 282 or higher migration. Note that the CIS branch `fix/aa-853-drift-reconcile-282` holds 281.
- So **282 and 283 are free**. Following lesson 19, reserve them at once with empty Infra branches `feat/aa-919-cis-282-copy` and `feat/aa-919-cis-283-copy`.
- Readiness reads `max(version)` (`api/core/readiness.py:28`, `REQUIRED_CIS_SCHEMA = 280`). This makes **281 a hard precondition**: it must be applied on Dev before 282.

**ADR**
- The governing ADR is **app ADR 0010** (`docs/adr/0010-governed-writing-memory.md`), not "0009" as the S245 spec says.
- Decision 1: the double check (DB plus API).
- Decision 12: release 0 must be byte-identical to the prompt **with `PIPELINE_LESSONS_ENABLED` off**.
- Decision 11: tenant text lives only in deletable tables.

**`shared.prompt_eval_runs`**
- It has 0 rows, owner `cis_owner`, and `cis_app` holds SIUD.
- The only code writer is `services/eval/regression.py:_write_eval_run`, which uses pipeline `s1_old`. It must keep working.

**Fixture 1.1.0** (`AA-Ecosys/docs/eval/aa729/fixture-1.1.0.json`)
- 100 samples:

| Group | Samples |
|---|---|
| S1 | 50 |
| T2 | 10 |
| Blog | 15 |
| LinkedIn | 15 |
| `inj-s1-*` | 5 |
| `inj-t9-*` (3 blog, 2 LinkedIn, hosted on tenant `atlas-hearth`) | 5 |

- There is an extra tag that the map did not list: `prompt_injection` (10 samples).
- `shared_inputs.brand_rules` holds `s1:default` plus **four tenant brand packs**, which are tenant text.
- T9 inputs carry the full `context`.
- Every T2 sample has `days ≥ 9`.

**Expected split** (my computation: stratified by writer × label verdict, round-half-up at 30%)

| Writer | Tune | Holdout |
|---|---|---|
| a1 | 35 | 15 |
| t2 | 7 | 3 |
| t9_blog | 10 | 5 |
| t9_social | 10 | 5 |

The 10 injection samples are traps.

**Expected tier counts**
- `long_9d`: a1 25, t2 10.
- `fact_dense` (proposed rule, Q3): a1 15 (cut 10.42 facts per 100 words), t2 3 (cut 10.62).

**Tenant exposure**
- Tenants read only `SELECT id, status FROM shared.job` (`v1_tours.py:78`). A T2 stamp in `shared.job.result.diag` is therefore admin-only.

**Two baselines are already out of date**
- AA-729 baseline run `dab254c4` (S245) was written **before** S250 made writer v2 the default. The A1 control outputs and numbers are v1-writer output (Q8).
- WM-23's planned spot (`build_s1_system_prompt` / `s1_batch`) **misses the live v2 writer** (Q12).

## 1. Merge order

1. **PR-A, migrations.** CIS PR with `282_eval_golden_set.sql` and `283_writing_memory_release.sql`, plus:
   - integration tests
   - the conftest lists
   - the erasure inventory
   - the Infra copy PR (both files, byte-identical)
   - the root registers PR

   It needs an agent review (risk class: migration). After merge: DB Migrate `check` → `apply` for 281 if it is still missing, then 282, then 283. Then merge the bot PR `bot/db-schema-reference`.
2. **PR-B, WM-17 code.** The golden importer plus the run ledger helpers, and readiness → 282. Deploy, then import on Dev.
3. **PR-C, WM-18 code.** The release domain and DB mirror, the admin API, the kill switch and the resolver, and readiness → 283. Deploy.
4. **PR-D, WM-20.** It ships in this order:
   1. A first commit that only adds the prompt pins, green on `main`.
   2. Extraction of the state builders shared by live and replay code.
   3. The empty insertion hooks and the stamps.
   4. The `release0` replay module.

   Deploy, run the Dev replay, create release 0, get approval, activate, enable memory, run the rollback drill.

WM-18 "Done" waits for PR-D, because its rollback drill needs the stamps.

## 2. Migration 282: `api/migrations/282_eval_golden_set.sql` (WM-17)

The header follows the 280 template: Why / What, Guards, Preflight, Locks, Order with the code, Undo as a forward migration, X1, and the byte-copy note. The body is one `BEGIN; SET LOCAL lock_timeout='5s'; … COMMIT;`.

**Guard 1**
- The roles exist, and `aa_app_user` has no superuser or BYPASSRLS.
- `has_schema_privilege(current_user,'shared','CREATE')`.
- 280 is registered.
- `shared.prompt_eval_runs` has exactly the 089 columns, or the 282 columns on a re-run.
- On a re-run, the new tables' column strings match exactly.

**`shared.eval_golden_set`** (platform table, no tenant column, no RLS, `cis_app` only)
- `set_id uuid PK DEFAULT gen_random_uuid()`
- `name text NN CHECK (name ~ '^[a-z0-9_]{1,40}$')` (value `aa729`)
- `version text NN CHECK semver`
- `status text NN DEFAULT 'active' CHECK IN ('active','superseded')`
- `source_uri text NN`, ≤ 300 characters, with a CHECK refusing any 12-digit run, so it is an S3 key only and never an ARN or account
- `source_sha256 text NN CHECK ^[0-9a-f]{64}$`
- `seed int NN`
- `holdout_pct numeric(4,3) NN DEFAULT 0.300 CHECK (0,1)`
- `tier_rules jsonb NN DEFAULT '{}' CHECK object`: the derivation and thresholds, e.g. the `fact_dense` cut per writer
- `shared_inputs jsonb NN CHECK object`: **platform inputs only** (`s1:default`); the comment says tenant packs live on the items
- `label_history jsonb NN CHECK array`
- `item_count int NN ≥ 0`
- `imported_by text NN`
- `created_at`
- Constraints: `UNIQUE (name, version)` and a unique index `eval_golden_set_one_active (name) WHERE status='active'`

**`shared.eval_golden_item`** (RLS ENABLE + FORCE; `pii:free_text` on `input` and the output columns)
- `item_id uuid PK`
- `set_id uuid NN REFERENCES eval_golden_set ON DELETE CASCADE`
- `sample_id text NN CHECK ^[a-z0-9-]{1,40}$`
- `writer text NN CHECK IN ('a1','t2','t9_blog','t9_social')`
- `channel text`, with this CHECK:
  ```
  (writer IN ('a1','t2') AND channel IS NULL)
  OR (writer='t9_blog' AND channel='blog')
  OR (writer='t9_social' AND channel IS NOT NULL AND channel<>'blog')
  ```
- `scope` / `tenant_id` with the 280 pattern CHECK, plus `CHECK (writer<>'a1' OR scope='platform')` and `CHECK (writer='a1' OR scope='tenant')`
- `split text NN CHECK IN ('tune','holdout','trap')` and `trap bool NN`, with `CHECK (trap = (split='trap'))`
- `kind text NN CHECK IN ('real','synthetic')`
- `tiers text[] NN DEFAULT '{}'` with `CHECK (tiers <@ ARRAY['cycle_bike','trek_hike','water','wildlife','culinary','long_9d','long_18d','poor_raw','known_failure','held','fact_dense','prompt_injection','post_edit'] AND cardinality(tiers) <= 13)`
- `country text` (≤ 60 characters), `days int CHECK 1..60`
- `input jsonb NN CHECK object`
- `control_output jsonb`, `output_post_edit jsonb`, `pipeline_verdict jsonb` (each NULL or an object)
- `label jsonb NN CHECK object`
- `label_verdict text NN CHECK IN ('pass','fail')`
- `label_source text NN CHECK IN ('agent_panel','synthetic','admin_edit','tenant_edit','human_label')`
- `refs jsonb NN DEFAULT '{}'`: ids only
- `input_sha256 text NN hex64`
- Size caps: `pg_column_size(input) <= 262144`, and the same for the outputs
- `created_at`
- Constraints and indexes: `UNIQUE (set_id, sample_id)`; an index on `(set_id, writer, split)`; an index on `(tenant_id) WHERE scope='tenant'`

**`shared.eval_item_result`** (RLS ENABLE + FORCE; `pii:free_text` on `output`)
- `result_id uuid PK`
- `run_id uuid NN REFERENCES shared.prompt_eval_runs(id) ON DELETE CASCADE`
- `item_id uuid NN REFERENCES eval_golden_item ON DELETE CASCADE`
- `writer`, `scope`, `tenant_id`: copied from the item, same CHECKs, kept for RLS and erasure
- `arm text NN CHECK IN ('control','candidate')`
- `mode text NN CHECK IN ('score_only','regenerate','rejudge')`
- `output jsonb`, with `CHECK (mode='regenerate' OR output IS NULL)`
- `output_sha256`
- `verdict text NN CHECK IN ('pass','fail','error','skipped')`
- `score numeric`
- `failure_codes text[]` (cardinality ≤ 50)
- `hard_stop bool NN DEFAULT false`
- `judge_model text`, `judge_version text` (the rubric or prompt hash)
- `cost_usd numeric(10,6) NN DEFAULT 0 ≥ 0`
- `details jsonb CHECK object`: ids and counts only
- `created_at`
- `UNIQUE (run_id, item_id, arm)`

**Widening `shared.prompt_eval_runs`** (the table is empty, so the ACCESS EXCLUSIVE lock is brief)
- `DROP CONSTRAINT prompt_eval_runs_pipeline_check`, then add it back as `CHECK (pipeline IN ('s1_old','s1_from_atom','writing_memory'))`.
- New columns:
  - `run_kind text NN DEFAULT 'regression' CHECK IN ('regression','baseline_import','r0_replay','r2','shadow')`
  - `writer text CHECK (NULL OR IN 4)`
  - `release_id uuid` (its FK comes in 283)
  - `golden_set_id uuid REFERENCES eval_golden_set ON DELETE RESTRICT`
  - `tiers text[] NN DEFAULT '{}'`
  - `stop_reason text CHECK (NULL OR IN ('completed','hard_stop','futility','budget_cap','probe_fail','error'))`
  - `verdict text CHECK (NULL OR IN ('pass','fail','baseline','informative','invalid'))`
  - `fingerprint jsonb NN DEFAULT '{}' CHECK object`
  - `finished_at timestamptz`
- New CHECKs:
  - `prompt_eval_runs_wm_shape_check`: `pipeline<>'writing_memory' OR (writer IS NOT NULL AND run_kind<>'regression')`
  - `prompt_eval_runs_legacy_kind_check`: `pipeline='writing_memory' OR run_kind='regression'`
  - `prompt_eval_runs_finished_check`: `finished_at IS NULL OR (stop_reason IS NOT NULL AND verdict IS NOT NULL)`
- The existing `cost_usd` is reused.
- New index on `(writer, run_kind, created_at DESC) WHERE pipeline='writing_memory'`.

**RLS** on the item and result tables, following the 280 pattern:
- `<t>_cis_app_all` and `<t>_cis_owner_all`, both `USING (true) WITH CHECK (true)`.
- `tenant_isolation TO aa_app_user` with `scope='tenant' AND tenant_id = NULLIF(current_setting('app.tenant_id', true),'')::uuid`.

**Grants**
- First `REVOKE ALL` from PUBLIC, `cis_app`, `aa_app_user` and `catalog_owner`.
- Then:

| Table | `cis_app` gets |
|---|---|
| set | SELECT, INSERT, UPDATE |
| item | SELECT, INSERT, UPDATE, DELETE (DELETE for erasure) |
| result | SELECT, INSERT, DELETE (results are immutable) |
| `prompt_eval_runs` | unchanged |

- `aa_app_user` gets nothing.

**Guard 2**
- Every named constraint is `convalidated`.
- The indexes, checked through `pg_get_expr`.
- RLS is on and forced.
- An exact policy string and an exact privilege string.
- No column ACLs.
- The AA-859 invariant v3, inlined.

**Guard 3** (always rolls back, `ZZ282`). Every one of these must be refused with `check_violation`:
- an a1 item with a tenant
- a T9 item without a tenant
- a t9_blog item whose channel is `linkedin`
- an unknown tier
- `trap` not matching `split`
- a `writing_memory` run without a writer
- `regenerate` missing from a mode the CHECK expects, and `output` on `score_only`

Two inserts must still succeed: a legacy `s1_old` regression row (proving `regression.py` is unaffected), and a platform a1 item that reads back.

**Register:** `('282','AA-919: eval golden set tables, widened prompt_eval_runs (WM-17)')`.

**Undo** (a forward migration, marked `-- migrate: destructive (MIG-9)`): drop `eval_item_result`, then `eval_golden_item`, then `eval_golden_set`; drop the new columns and constraints; restore the old pipeline CHECK.

## 3. Migration 283: `api/migrations/283_writing_memory_release.sql` (WM-18)

Guard 1 additionally checks that 282 is registered.

**`shared.writing_memory_release`** (RLS ENABLE + FORCE). It holds no text: rules are referenced by id, and their text stays in `writing_rule`.

Columns:
- `release_id uuid PK`
- `writer`, `scope`, `tenant_id` (the 280 pattern)
- `release_no int NN ≥ 0`
- `train_kind text NN CHECK IN ('baseline','regular','emergency','lexicon')`
- `content_class text NN CHECK IN ('empty','lexicon_only','repair_hint_only','rules')`
- `rule_ids uuid[] NN DEFAULT '{}'` (cardinality ≤ 40)
- `items_sha256 text NN hex64`: a sha over the sorted (rule_id, rule_text, replacement); release 0 hashes an empty list
- `status text NN DEFAULT 'draft' CHECK IN ('draft','evaluated','approved','active','retired','rejected')`
- `eval_run_id`, `shadow_run_id`, `r0_run_id`: each `uuid REFERENCES shared.prompt_eval_runs ON DELETE RESTRICT`
- `previous_release_id uuid REFERENCES writing_memory_release ON DELETE SET NULL`: the rollback target
- `train_month date`
- `emergency_reason text` (≤ 500 characters)
- `reverify bool NN DEFAULT false`, `reverify_reasons text[] NN DEFAULT '{}'`, `reverify_at timestamptz`
- `fingerprint jsonb NN CHECK object`
- `approved_by`, `approved_at`, `approval_ref text` (≤ 300 characters)
- `activated_at`, `retired_at`, `retired_reason`
- `rejected_by`, `rejected_reason`
- `notes` (≤ 1000 characters)
- `created_by NN`, `created_at`, `updated_at`

Row CHECKs:
- `(content_class='empty') = (train_kind='baseline')`
- `(content_class='lexicon_only') = (train_kind='lexicon')`
- `(content_class='empty') = (cardinality(rule_ids)=0)`
- `release_no<>0 OR content_class='empty'`
- **`writing_memory_release_evidence_check`** (the WM-18 activate-requires-eval check):
  ```
  status NOT IN ('active','retired') OR (
       (content_class='empty'        AND r0_run_id IS NOT NULL AND eval_run_id IS NOT NULL)
    OR (content_class='lexicon_only' AND r0_run_id IS NOT NULL)
    OR (content_class IN ('repair_hint_only','rules') AND eval_run_id IS NOT NULL AND shadow_run_id IS NOT NULL))
  ```
- Approval: `status NOT IN ('approved','active','retired') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)`
- `status NOT IN ('active','retired') OR activated_at IS NOT NULL`
- `status<>'retired' OR retired_at IS NOT NULL`
- `status<>'rejected' OR (rejected_by AND rejected_reason)`
- `train_kind<>'emergency' OR emergency_reason IS NOT NULL`
- `reverify = (reverify_at IS NOT NULL)`
- `train_kind<>'regular' OR status NOT IN ('active','retired') OR train_month IS NOT NULL`

Indexes:
- **Active pointer:** unique index `(writer, scope, coalesce(tenant_id,'0…0'::uuid)) WHERE status='active'`.
- **Monthly train:** unique index `(writer, scope, coalesce(tenant_id,…), train_month) WHERE train_kind='regular' AND train_month IS NOT NULL`.
- Unique index `(writer, scope, coalesce(tenant_id,…), release_no)`.
- `(tenant_id, status) WHERE scope='tenant'`.
- `(writer, status)`.

**Trigger `shared.writing_memory_release_guard()`** (BEFORE INSERT OR UPDATE; plpgsql; `SET search_path = pg_catalog, pg_temp`; not SECURITY DEFINER; EXECUTE revoked from PUBLIC). It does the following:
1. An INSERT must have status `draft`.
2. Transitions are limited to:

   | From | Allowed to |
   |---|---|
   | draft | evaluated, rejected |
   | evaluated | approved, rejected, draft |
   | approved | active, rejected |
   | active | retired |
   | retired | active (rollback) |

   Anything else raises `restrict_violation`.
3. Once OLD.status is not `draft`, these fields are immutable (`restrict_violation`): writer, scope, tenant, `release_no`, `train_kind`, `content_class`, `rule_ids`, `items_sha256`. From `approved` on, the run refs are immutable too.
4. When NEW.status becomes `active` (`check_violation` on failure):
   - Every referenced run has `pipeline='writing_memory'`, the same writer, and `finished_at` set.
   - The eval run has kind `r2` with verdict `pass`, or kind `baseline_import` with verdict `baseline` (allowed only when the class is `empty`).
   - The shadow run has kind `shadow` and verdict `pass`.
   - The r0 run has kind `r0_replay` and verdict `pass`. For class `empty` it also needs `details->>'byte_diffs'='0'` and `(details->>'inputs')::int >= 20`.
   - **Isolation:** every `rule_id` exists in `shared.writing_rule` with the same writer. A platform release takes only platform rules; a tenant release takes only rules with `scope='tenant' AND tenant_id = NEW.tenant_id`.
   - On draft → active only (not on rollback): the rules' status is `approved` or `active`, and `content_class` matches the rule kinds (all lexicon, or all repair_hint).
   - On the first activation of a `regular` release, `train_month = date_trunc('month', now() AT TIME ZONE 'UTC')::date`.
   - `activated_at = now()`.

**`shared.writing_memory_shadow`** (RLS ENABLE + FORCE; `pii:free_text` on `output`)
- `shadow_id uuid PK`
- `release_id uuid NN REFERENCES writing_memory_release ON DELETE CASCADE`
- `run_id uuid NN REFERENCES prompt_eval_runs ON DELETE CASCADE`
- `writer`, `channel`
- `scope` / `tenant_id`: the **input's** owner, so a cross-tenant probe row belongs to tenant B and is erased with B
- `probe bool NN DEFAULT false`
- `input_source text NN CHECK IN ('content_piece','tenant_tour_version','generated_content','golden_item')`, `input_id uuid NN`
- `input_sha256`, `prompt_sha256`
- `output jsonb NN` (size cap), `output_sha256`
- `control_ref jsonb`, `isolation jsonb CHECK object`, `qa_artefacts text[]` (≤ 50)
- `verdict CHECK IN ('pass','fail','error')`
- `cost_usd NN DEFAULT 0`
- `created_at`
- `UNIQUE (run_id, input_source, input_id)`

**`shared.writing_memory_writer`** (the kill switch; platform table, no RLS)
- `writer text PK CHECK IN 4`, `memory_enabled bool NN DEFAULT false`, `updated_by text`, `updated_at`, with `CHECK (NOT memory_enabled OR updated_by IS NOT NULL)`.
- A BEFORE UPDATE trigger, `writing_memory_writer_guard`: setting `memory_enabled=true` requires an active platform release for that writer.
- Seeded with 4 rows, `ON CONFLICT DO NOTHING`.

**Foreign keys added to 282 tables**
- `prompt_eval_runs.release_id` → release, `ON DELETE SET NULL`.
- `eval_item_result ADD COLUMN release_id uuid REFERENCES writing_memory_release ON DELETE SET NULL`.

**RLS and grants**
- The release and shadow tables get the same three policies as above.

| Table | `cis_app` gets |
|---|---|
| release | SELECT, INSERT, UPDATE, DELETE |
| shadow | SELECT, INSERT, DELETE |
| writer | SELECT, UPDATE |

- `aa_app_user` gets nothing.

**Guard 2:** the same checks as 282, plus both triggers enabled.

**Guard 3** (`ZZ283`):
- Activating an empty release without r0 is refused.
- Activating with an r0 run whose `byte_diffs=1` is refused, and so is one with `inputs=19`.
- A `rules` release without shadow is refused.
- A release labelled `lexicon_only` that holds a `writer_instruction` rule is refused.
- A tenant-A release holding a tenant-B rule is refused.
- A second active release gives `unique_violation`.
- A second `regular` release in one month gives `unique_violation`.
- Changing items after draft gives `restrict_violation`.
- Setting `memory_enabled` with no active release is refused.
- One case must succeed: rollback (current → retired, then previous retired → active).

**Register:** 283.

**Undo:** drop the 3 tables, the 2 functions and the 2 foreign keys (destructive marker).

**Same PR (PR-A)**
- `tests/integration/conftest.py`: add `shared.eval_golden_item`, `shared.eval_item_result`, `shared.writing_memory_release` and `shared.writing_memory_shadow` to both `X1_POST_244_RLS` (:86) and `X1_POST_245_FORCE_RLS` (:96).
- `services/erasure/inventory.py`: add `_d` for the same four tables (golden items and results of the tenant, tenant releases, shadow outputs). `test_aa839` must stay green.
- No `rls_catalogue_rules.py` ALLOWLIST change: every tenant table has RLS.
- Root PR:
  - `docs/database/schema-ownership.md`: 6 rows (`prompt_eval_runs` as altered)
  - `02-data-management.md`: DM-7 rows, with retention as in Q16
  - ERD page `docs/architecture/erd/design/shared.md` (lesson 208)
  - an AI Use Register line for the new tenant-text stores
- Implementation notes: `docs/implementation-notes/AA-919-cis-282.md` and `AA-919-cis-283.md`.

## 4. Code

**PR-B (WM-17)**
- `services/eval/golden.py` (pure functions):
  - `writer_of(sample)`: s1 → a1, t2 → t2, t9_blog → t9_blog, t9_linkedin → t9_social; injection follows its host stratum.
  - `fact_density(tour)`: `len(numbers)+len(schedule)+len(places)` from `services.quality.s1_facts.build_fact_table`, per 100 source words.
  - `derive_tiers(sample, tier_rules)`: fixture tags, plus `long_9d` (days ≥ 9), `fact_dense` (top 30% per writer, a1 and t2 only), and `post_edit`.
  - `assign_splits(samples, seed=729, pct=0.30)`: stratified by (writer, `label_verdict`), ordered by `sha256(f"{seed}:{sample_id}")`, round-half-up; traps get `split='trap'`.
  - `item_rows(fixture)`: **inlines each tenant brand pack** (`shared_inputs.brand_rules[ref]`) into `item.input.brand_rules` and keeps only `s1:*` at set level. It refuses a tenant pack at set level.
  - `count_report(rows)`.
- `services/eval/golden_store.py`: SQL constants for insert set, items and run, and `import_baseline(conn, set_id, writer, score_json, run_meta)`. That function writes one `prompt_eval_runs` row per writer per mode (`pipeline='writing_memory'`, `run_kind='baseline_import'`, `verdict='baseline'`, `prompt_version` = the hash recorded in the run, `cost_usd`, details with the run id and report path) and one `eval_item_result` row per item (`arm='control'`, mode from the file).
  - Also: `active_set(conn, name)`, `counts(conn, set_id)`, `supersede(conn, name)`.
- `services/eval/golden_import.py`, CLI: `python -m services.eval.golden_import --fixture-key scripts/out/aa729/fixture-1.1.0.json [--baseline-key …score-only.json --baseline-key …score-regenerate.json] [--apply]`.
  - It is a dry run by default and prints counts.
  - It is idempotent on `(name, version)`.
  - It refuses a `source_sha256` that does not match an already-imported version.
  - It runs as `cis_app` through `DATABASE_URL`.
- `services/eval/regression.py`: no change. A compatibility unit test asserts its INSERT still satisfies the new CHECKs (it relies on the column defaults).

**PR-C (WM-18)**
- `services/writing_memory/releases.py`:
  - `create_draft` (computes `items_sha256`, the next `release_no`, `content_class` from the rule kinds) and `attach_evidence` (draft → evaluated once its refs are complete).
  - **`evidence_problem(release, runs, rules) -> Optional[(code, why)]`:** the API mirror of the CHECK and the trigger, with the same cases as Guard 3, as a readable 409. It is called on a `FOR UPDATE` row inside the write transaction.
  - `approve` needs a human id (`wm.admin_actor_id`, never a job) and accepts `approval_ref`.
  - `activate`: one transaction that locks the target and the current active row, retires the current one (`superseded`), and activates the target with `previous_release_id` set.
  - `rollback`: current → retired (`rollback: <reason>`), then previous → active. It returns 409 `no_previous` for release 0, where the kill switch is the answer instead.
  - `set_memory_enabled`.
  - `current_fingerprint(conn, writer)`: golden set name@version, the `llm_role_config` route of the writer stage (model_id plus fallbacks) and `registry.TAXONOMY_VERSION`.
  - `reverify_scan(conn)`: flags active releases whose fingerprint differs.
  - **This series' policy:** `activate` refuses any `content_class` other than `empty` with 409 `content_not_wired` until WM-23, WM-24 and WM-25.
  - `rules.expire_stale`: skips rule ids held by a release in draft, evaluated, approved or active.
- `services/writing_memory/insertion.py`:
  - A frozen `MemoryView` (writer, platform and tenant release ids and numbers, `rule_ids`, `memory_enabled`).
  - `resolve(pool, writer, tenant_id)`: one SQL query that reads the switch, the platform pointer and the tenant pointer (explicit `tenant_id = $n` filter). It **fails open**: on any error it logs `wm_release_unavailable` and returns `None`.
  - Renderers `a1_house_rules`, `t2_block`, `t9_platform_block` and `t9_tenant_lines` return `""` or `[]` for `None` or an empty view. A non-empty view returns `""` too, logs `wm_release_content_ignored` and sets `stamp.ignored=true`.
  - `stamp(view)`.
- Router, in `api/routers/admin_writing_memory.py` with the same prefix (the module docstring lists every route). Literal paths come before `/{release_id}`:
  - `GET /releases`, `GET /releases/active`, `GET /releases/{release_id}`: TENANT_READ
  - `POST /releases`, `POST /releases/reverify-scan`, `POST /releases/{release_id}/evidence`, `/approve`, `/activate`, `/rollback`, `/reject`: AI_ADMIN
  - `GET /writers`: TENANT_READ; `PATCH /writers/{writer}` (`memory_enabled`): AI_ADMIN
  - `GET /golden-sets`, `GET /golden-sets/{set_id}` (counts only, no text): TENANT_READ
  - Pydantic bodies use `extra="forbid"`.
  - Error mapping: `UndefinedTableError` → 503 `unavailable`; `CheckViolationError` / `RaiseError` from the trigger → 409 `db_refused` (proof that the second layer fired); `UniqueViolationError` → 409 `already_active` / `train_slot_taken`; 403 `no_actor` when there is no admin id.
  - POLICY entries go in `api/core/staff_authz.py` next to the 918 block. Then regenerate `tests/unit/snapshots/aa882_staff_route_policy.json` and `docs/api/openapi.json`.
- `REQUIRED_CIS_SCHEMA = 283`.

**PR-D (WM-20).** All the extractions are moves of existing code. They are proved by the pins committed first.

- Shared state builders, so replay and live code are the same functions:
  - `api/routers/v1_pipeline.py`: `build_initial_state(...)`, taken out of `_rewrite_tour` (169-216).
  - `api/routers/admin_pipeline.py`: `a1_tour_from_raw(row)`, taken out of 554-593 and 684.
  - `services/jobs/t2_rewrite_job.py`: `t2_inputs(pool, payload) -> (tour_dict, brand_rules, seo, market)`, taken out of `_prepare` and the SEO part of `_rewrite_and_save`.
  - `services/acp_content_writing/service.py`: `writer_kwargs(context)`, taken out of the `write_content` / `rewrite_with_feedback` calls (around 1851 and 1995).
- Empty insertion hooks:
  - A1 v2: `s1_writer_v2.w_system_prompt(forbidden, background="allow", house_rules="")` puts the block after `_forbidden_line` and before "Output ONLY valid JSON". `filter(None)` drops `""`, so the bytes are identical.
  - `s1_writer_v2_live.write` reads `state.get("writing_memory")`. `prompt_version_of(system)` stays at :118. Meta prompts are left alone (WM-23 decides).
  - T2: `batch_prompt.build_t2_system_prompt` appends `insertion.t2_block(state.get("writing_memory"))` before `t2_dashless`.
  - T9: `generate.write_content` / `rewrite_with_feedback(memory=None)` builds `system = SYSTEM_PROMPT + t9_platform_block(memory)`, and `build_user_prompt(memory_lines=None)` inserts after the words line (347) and before the CONTENT SEED.
- Resolve points:
  - A1: `admin_pipeline._execute_run_tour` (async, before the graph) passes the result into `initial_state["writing_memory"]`.
  - T2: `t2_rewrite_job.run` passes it into `_rewrite_tour`, so T3 re-calls reuse it.
  - T9: `service.start_write` puts it into `context["writing_release"]` once per piece, so every attempt uses the same release.
- Stamps (only when `memory_enabled` and a release resolved; otherwise the shape is unchanged, like the L0 pattern):
  - A1: `metadata.writing_release`, in `_build_generated_metadata` next to `writer_version` (373).
  - T2: `shared.job.result.diag.writing_release`, until `generation_meta` arrives in WM-25.
  - T9: `writer_input.writing_release`, in `writer_input_snapshot`.
- `services/writing_memory/release0.py`, CLI: `python -m services.writing_memory.release0 --writers a1,t2,t9_blog,t9_social --min 20 [--apply] [--create-release0]`. Per writer it loads ≥ 20 stored inputs, newest first, topped up from golden items of that writer:

  | Writer | Source |
  |---|---|
  | A1 | `generated_content` rows with `metadata->>'writer_version'='v2'`, then `raw_tours` through `a1_tour_from_raw` plus the A1 brand forbidden words |
  | T2 | `shared.job` kind `t2_rewrite` with status done, then `t2_inputs` |
  | T9 blog / social | `content_piece.writer_input` for that channel, with `atom_id` from `angle_gate_request` and `sibling_openers=[]` on both sides |

  - It builds (a) the system and user prompts with `memory=None` and (b) the same with the resolved view (release 0 from the DB, or a synthetic empty view before release 0 exists), and compares them byte for byte.
  - It also reports, as informative only and not the gate: for A1, `prompt_version_of(system)` against the stored `metadata.prompt_version`; for T9, `WRITER_PROMPT_VERSION` against `writer_input.writer_prompt_version`.
  - It writes `s3://<bronze>/scripts/out/wm20/<run_id>/report.json` (ids and hashes only) and one `prompt_eval_runs` row per writer: `run_kind='r0_replay'`, `verdict` `pass` or `fail`, `details{inputs, byte_diffs, sources, live_hash_match}`, `cost_usd=0`.
  - `--create-release0` adds a platform draft per writer: `release_no=0`, `train_kind='baseline'`, `content_class='empty'`, `r0_run_id` set, `eval_run_id` = that writer's baseline_import run. It also links `release_id` back onto the baseline runs and item results.

## 5. Tests

**PR-A**
- `tests/integration/test_aa919_migration_282.py` and `test_aa919_migration_283.py`:
  - asyncpg with a rolled-back transaction, `_as(conn, role)` and `_refused`.
  - The first test asserts the `schema_versions` row (lesson 67).
  - Run real SQL against each table.
  - Check RLS by behaviour: as `aa_app_user` with a foreign `app.tenant_id`, 0 rows and no privilege.
  - Run every Guard 3 case through `cis_app`.

**PR-B**
- `tests/unit/test_aa919_golden_derive.py`, using an invented fake fixture `tests/unit/fixtures/aa919_fake_fixture.json` with the same schema, 24 invented samples and no real text. It covers:
  - deterministic splits for a fixed seed, and the 30% rounding per stratum
  - the trap split
  - `long_9d` and `fact_dense`
  - tenant packs inlined onto items and never kept at set level
  - the writer and channel mapping
- `tests/unit/test_aa919_golden_import_cli.py`: dry run, S3 mocked, idempotent, sha mismatch refused.
- `tests/integration/test_aa919_golden_store.py`: import into Postgres, counts, re-run is a no-op, and baseline rows match the CHECKs.
- `tests/unit/test_aa919_regression_compat.py`: the `regression.py` INSERT still fits.
- **`tests/unit/test_aa919_no_golden_text.py`**, the CI "no real tenant text" guard (Q15):
  1. No tracked file contains the fixture markers (`"schema": "aa729-golden-set"`, `"label_history"` together with `"samples"`).
  2. A fingerprint check. `tests/unit/fixtures/aa919_golden_fingerprints.txt` holds 64-bit truncated sha256 values of 20 normalised 8-word shingles per golden item (about 2,000 lines, hashes only). It is generated by `python -m services.eval.golden --fingerprints <private fixture path>` from the root copy. The test shingles every tracked text file and fails on any hit.

**PR-C**
- `tests/unit/test_aa919_releases_api.py`, using the `aa977_fakes` pattern and `TestClient`:
  - per-route role checks (AI admin writes; viewer and content roles get 403; every staff role reads)
  - 422, 409, 404 and 503 mapping
  - `content_not_wired`, `no_previous` and `no_actor`
  - `test_policy_entries`
- `tests/unit/test_aa919_evidence_mirror.py`: a table-driven test with exactly the Guard 3 cases against `evidence_problem`. This is the API half of the double check.
- `tests/integration/test_aa919_releases_db.py`:
  - activate, supersede and rollback through `releases.py` on real Postgres
  - the trigger refuses even when the API check is bypassed (a direct UPDATE as `cis_app`)
  - tenant A rules never resolve for tenant B (`resolve`)
  - `expire_stale` skips rules held by a release
  - the kill-switch guard
- `tests/unit/test_aa919_resolver.py`: fails open on errors, the switch off gives `None`, the explicit tenant filter in the SQL string.

**PR-D**
- **`tests/unit/test_aa919_prompt_pins.py`**, committed first and green on `main` before any refactor. It pins sha256 of:
  - A1 v2 W system and user, and meta system and user
  - T2 system and user: branded, unbranded, en-GB, retry with feedback, `revise_block`
  - T9 `SYSTEM_PROMPT`, plus user prompts for blog single, blog route, LinkedIn and Facebook, each with and without an L0-applied pack and with revision feedback

  The aa792 A1 v1 pins stay as they are.
- **`tests/unit/test_aa919_release0_replay.py`**: 20 generated fake inputs per writer, run through the same `release0.compare` used on Dev (`memory=None` against an empty release-0 view). It asserts 0 byte differences on system and user, stamps present with `release_no=0`, and the A1 `prompt_version` unchanged.
- `tests/unit/test_aa919_stamps.py`: A1 metadata, T2 diag and T9 `writer_input` stamp shapes. With memory off, no key is present (shape unchanged).
- Also: `pytest tests/unit tests/integration -q`, flake8 at 120, the coverage ratchet, the regenerated aa882 snapshot and `openapi.json`, and `services.quality.lint` stays clean (no gate names added).

## 6. Dev steps (all single-line AWS CLI, profile `aa365-admin`, us-west-1)

1. **Preflight**, read-only as `cis_app` through the S3-mediated ECS exec:
   - Check that 281 is in `shared.schema_versions`, that `to_regclass` is NULL for the 5 new tables, and that `prompt_eval_runs` has `count(*)=0`.
   - `shared.job` and `booking.job` must be idle.
2. **Migrations.** Merge PR-A and the Infra copy PR. Then DB Migrate `check` → `apply` for `cis/281_…` if it is missing, then `cis/282_eval_golden_set.sql`, then `cis/283_writing_memory_release.sql`, with the job tables idle. Merge the bot PR, then the root registers PR.
3. **Import (PR-B deployed).**
   - Check that `s3://aa-cis-bronze-…/scripts/out/aa729/fixture-1.1.0.json` exists, and that the baseline files `…/<8f07b98f…>/score-score-only.json` and `…/<dab254c4…>/score-regenerate.json` exist.
   - If the fixture is missing, `aws s3 cp` the root copy (private bucket). If the baseline files are missing, see Q7.
   - Upload a launcher script that runs `runpy.run_module('services.eval.golden_import')`: dry run first, then `--apply`.
   - Post the counts JSON as a Linear comment.
4. **Releases (PR-C deployed).** Check that `GET /admin/writing-memory/writers` gives 4 rows with memory off and that `GET /releases` returns an empty list.
5. **Release 0 (PR-D deployed).**
   - ECS exec `release0 --writers all --min 20 --apply --create-release0`.
   - Confirm in `llm_call_log` that no row was added during the run window.
   - Nghiệp approves the 4 drafts (Q9). Then `POST /releases/{id}/approve`, then `/activate`.
   - `PATCH /writers/{w}` with `memory_enabled=true` for all 4 writers (Q14).
   - `POST /releases/{id}/activate` without evidence on a scratch draft must return 409 from the API. The integration test shows the DB refuses it too.
6. **Rollback drill on t9_social**, on a test tenant:
   - Create draft release 1 (empty `baseline`; reuses that writer's r0 and baseline runs), approve it, activate it.
   - Write one T9 LinkedIn piece. Its `writer_input.writing_release.platform.release_no` must be 1.
   - `POST /releases/{r1}/rollback`, then write the next piece. Its stamp must be `release_no` 0.
   - Cost is about one or two T9 writes, read from `llm_call_log`. A $0 resolver check through `GET /releases/active` is also recorded.
7. **Report.** Write `AA-Ecosys/docs/audits/<date>-S<nnn>-wm20-release0/README.md` (counts, diffs, sources, live-hash match, drill stamps) and include it in the root PR.

## 7. Done-when evidence

**WM-17**
- 282 is in `schema_versions`; the bot PR lists the 3 tables and the new `prompt_eval_runs` columns.
- A Linear comment with the importer counts:
  - Items by writer, split and tier, expected: a1 35/15, t2 7/3, t9_blog 10/5, t9_social 10/5, traps 10. `long_9d` a1 25, t2 10. `fact_dense` a1 15, t2 3.
  - The baseline_import runs and their per-writer `eval_item_result` counts.
- The CI guard `test_aa919_no_golden_text` is green on the PR.
- Cost: $0.

**WM-18**
- 283 is applied.
- Both layers refuse an activation without evidence: `test_aa919_releases_db` (DB, including a direct UPDATE) and `test_aa919_evidence_mirror` / API tests (API).
- On Dev, a 409 from the API on a scratch draft.
- Rollback drill: two consecutive t9_social pieces stamped release 1, then release 0, after `/rollback`.
- Agent review (kiro-reviewer or an independent subagent) on PR-A and PR-C.

**WM-20**
- CI `test_aa919_release0_replay`: 0 diffs on 4 × 20 fake inputs. The pins are unchanged between `main` and the PR.
- The Dev replay report: ≥ 20 inputs per writer, `byte_diffs=0` for every writer, $0.
- 4 `writing_memory_release` rows with `release_no=0` and `status='active'`, whose `eval_run_id` points at the AA-729 baseline_import run.
- `memory_enabled` is true for each writer, and stamps appear on new pieces.

## 8. Open questions, each with a proposed answer

1. **One migration or two?** Two (282 for WM-17, 283 for WM-18), with one Infra PR and applied in the same window. Each file stays reviewable at roughly the size of 280.
2. **281 is not applied yet.** Apply it first. Readiness compares `max(version)` and the keys must go in order. 281 is a no-op on Dev, per its header.
3. **"Fact-dense" has no source tag.** Use a deterministic $0 rule: fact entries (numbers, schedule, places from `build_fact_table`) per 100 source words, top 30% per writer, a1 and t2 only. Store the cut in `tier_rules`.
4. **Tier storage.** `tiers text[]` against a closed CHECK list (lesson 211: a new tier means a new migration, which is intended).
5. **Split for injection samples.** A separate `split='trap'`, outside tune and holdout. WM-19 runs them in its probe step.
6. **Tenant brand packs in `shared_inputs`.** Inline them on each tenant item, so erasure removes them. Only `s1:default` stays at set level.
7. **Are the per-item baseline score files on S3?** I could not check S3 read-only. If they are missing, import the aggregates from `report-*.md` into `details` and write `eval_item_result` from the fixture's frozen output (`mode='score_only'`, `arm='control'`).
8. **The A1 baseline is v1-writer output (taken before S250).** Release 0 for A1 starts with `reverify=true` (reason `prompt_version_mismatch`). Do the same for any writer whose baseline `prompt_version` differs from today's, which `release0` computes. A fresh A1 control run is a separately approved paid run in WM-19.
9. **The human approval click before WM-22's UI.** Nghiệp approves the 4 release-0 drafts on a clickable decision artifact. The API call then records his staff id in `approved_by`, the decision link in `approval_ref`, and the agent in `notes`. Alternative: move a one-button approve into WM-22 earlier.
10. **L0 lexicon rules that are active outside any release.** Leave them as they are in this series. Release-0 replay compares with the same L0-applied pack on both sides. WM-24 decides whether to fold them into `lexicon_only` releases.
11. **Where the T2 stamp goes.** `shared.job.result.diag.writing_release` now (tenants only read job id and status). Move it to `generation_meta` in WM-25.
12. **WM-23's planned spot misses v2.** Hook only the live A1 v2 writer here. Record a spec correction for WM-23: the HOUSE RULES slot is `w_system_prompt`, and the v1/batch append stays frozen.
13. **The T9 version stamp.** Keep `WRITER_PROMPT_VERSION` as it is now (identical under release 0). WM-24 switches to `prompt_version_of(actual system)` per call.
14. **Turn `memory_enabled` on after release 0?** Yes, for all 4 writers. It is a proven no-op, and the rollback drill needs the stamps.
15. **The CI "no tenant text" grep.** Use the marker scan plus the hashed-shingle fingerprint file. It contains no text, and the fingerprints are regenerated on each new golden version.
16. **Retention (DM-7).** Golden items and results: kept while their set is active plus 12 months. Tenant rows are deleted at offboarding. Shadow: 90 days after the release retires. Releases are kept, since they hold ids only.
17. **Capabilities.** Reads use TENANT_READ. Approve, activate, rollback, the switch and reverify-scan use AI_ADMIN, matching L0 activation.
18. **Rollback when a rule of the target release is now expired or rejected.** The trigger re-checks evidence and isolation only, never the rule status, because rollback must never be blocked. Flagging such a release is WM-26 scope.
19. **Monthly train.** Only `regular` releases count toward it, and `train_month` is fixed at first activation. Baseline (empty), lexicon and emergency releases, and rollbacks, never take the monthly slot.

## 9. Risks

- **The PR-D refactor of the shared builders** is the only change that could move bytes. Pins committed first, the aa792 pins and the replay test guard it.
- **The resolver** adds one DB read per write and fails open.
- **Deploy and DB Migrate** happen only with `shared.job` idle (DM-11.4).
- **No real text** goes into the public repo: fake fixtures only, plus the fingerprint guard.