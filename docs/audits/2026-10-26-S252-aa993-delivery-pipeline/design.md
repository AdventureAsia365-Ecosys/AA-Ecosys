# AA-993 design: deploy any time, ship migrations in the app PR, verify every deploy

Basis: code read on `origin/main` (root `origin/master`) after `git fetch` on 26/10/2026. All reads were read-only: `git show`, `git grep` and `gh api` GETs. The critic's citations below were re-checked today and match:

- **Infra.** `accounts/aa365/cicd_split.tf:14-16, 565-592` and `db-migrate.yml:84-86, 97-98, 367-379`. `db/run_migration.py` at `:35`, `:143-145`, `:252-258`, `:337-340` and `:1170-1180`; it has no advisory lock (`git grep advisory` returns nothing). Also `db/replay_migrations.py:9-10, 26-27`.
- **CIS.** `api/core/readiness.py:30-50` and `shared/jobs/queue.py:90-110` (`RETURNING *` inside `conn.transaction()`). Also `queue.py:500-512`, `registry.py:28-46`, `services/jobs/s1_rewrite_job.py:49-54, 86-88` and `api/routers/admin_pipeline.py:795, 849, 894-898`. Also `services/export/handler.py:184-245`, `deploy-dev.yml:29-31`, `platform_apps.py:80, 109` and `staff_authz.py:455`.
- **Partner.** `api/app/dispatch/worker.py:94-123`, `api/app/main.py:80, 177`, the provider `send(raw, secret, recipients)` signatures (`mail/providers/__init__.py:49`, `smtp.py:140`, `oauth_mail.py:137`) and `ui-smoke-portal.yml:8-24, 37-49`.
- **Booking.** `deploy-dev.yml` lines 70-87 (the `config` job skip) and 205-208 ("scale to 1 is a separate approved step").
- **TripPlanner.** `vercel-deploy.yml:144, 150` (`GIT_SHA=$SHA` from `steps.plan.outputs.sha`).
- **Live GitHub state.** Infra `main` is unprotected (`branches/main/protection` returns 404) and has no rulesets (`[]`). Infra and root are **public** now. ADR 0014 says they go private again (`0014-…md:4, 43-44`), and on GitHub Free, rulesets and environment rules exist only on public repos (`:21, :24-27`). The org plan is `free`. `allow_auto_merge` is false on Infra and root and true on the four app repos.

| Repo | Head read in READs | Head today | What changed |
|---|---|---|---|
| CIS | c53ab119 | 83eed0e1 | #1041 (gitleaks on `merge_group`), #1042 (`master_newer`: `_tenant_projection.py`, `v1_tours.py`). No cited path touched |
| Booking | 8c8ad68 | f47a750 | Cited lines re-checked |
| Partner | acbe9f4 | 7bd2bb0 | #90 (`web/components/mail/MailImport.tsx` only) |
| TripPlanner | — | 3f6228a | — |
| Infra | — | cee70f3 | — |

Other cited lines come from the READs. Re-check them when each slice starts.

---

## 1. ADR draft

File: `docs/adr/0016-deploy-any-time-and-migrations-in-app-pr.md`. 0016 is the next free root number (`docs/adr/README.md`). Add a row to the README table, which `tools/adr/check_adr_numbers.py` checks. The ADR also needs `0011a` (new ci-bot uses, all inside Infra). It is drafted in slice I1.

```markdown
# ADR 0016 — Deploy any time: graceful worker drain, migrations in the app PR, automatic post-deploy verify, local gates

- **Status:** Proposed (26/10/2026, S252)
- **Scope:** AA-CIS-App, AA-Booking, AA-Partner, AA-TripPlanner-Web (deploy workflows, job runners, readiness, hooks),
  AA-CIS-Infra (DB Migrate, runner, migration copy/apply/dump workflows, a new narrow apply role, ECS stopTimeout,
  a ruleset on `main`), root (data standards, skills aa-ship / aa-cis-schema, steering db-schema.md).
- **Amends:** data standards DM-11.2, DM-11.4 (`02-data-management.md:376, 378`), C6.3a/b (`03-scaling.md:343-344`),
  MIG-4 (`01-engineering.md:268-279`, checklist `:697, :717`) — for **expand** files only; contract files keep MIG-4.
  Needs **ADR 0011a** (ci-bot inside AA-CIS-Infra: open and merge copy PRs, merge schema-dump PRs; no cross-repo
  write token is minted by any app workflow).
- **Implements:** ADR 0003 / 0003a (one durable job model, per-owner job tables); ADR 0011 §4 (merge rights per tier).
- **Depends on:** ADR 0014 visibility. The auto-apply relies on the Infra ruleset and environment rules, which exist
  only while Infra is public on GitHub Free (`0014:21, 24-27`); if Infra goes private, auto-apply is switched off
  (repo variable `DB_AUTO_APPLY=false`) until an equivalent gate exists (D2.8).
- **Related Linear:** AA-993.

## Context

Lead time is driven by manual waits, not by coding (baseline in §3 of the design):
- Backend deploys block on **any queued or running row** (CIS `shared/jobs/worker.py:365-372` →
  `deploy_job_guard.sh:33-38`; Booking `booking-deploy-preflight.sh:64-82`; Partner `partner-deploy-preflight.sh`),
  although all three runners already release a running job on SIGTERM (CIS `worker.py:254-264`, `queue.py:195-230`;
  Booking `worker.py:145-159`; Partner `worker.py:163-177`). Queued rows are blocked too, though a deploy never
  touches them. The wave rule is not checked by any deploy gate (only `run_migration.py:197-198` and a manual step in
  `skill/aa-ship/SKILL.md`).
- The CIS drain uses 20 s (`worker.py:94`) of a 120 s stopTimeout (`modules/ecs/main.tf:795`); Booking/Partner have
  30 s stopTimeout (`booking.tf:387`, `crm_app.tf:447`), a 20 s worker wait (Partner `main.py:80, 177`), and uvicorn
  waits for in-flight HTTP before lifespan shutdown (`Dockerfile:32`, no `--timeout-graceful-shutdown`).
- Some kinds are not safe to re-run: CIS `s1_rewrite` (only `phase=done` + `version_id` is checkpointed, at the very
  end, `s1_rewrite_job.py:86-88`; the persist steps after the `generated_content` INSERT — `quality_scores`
  `admin_pipeline.py:849`, review queue `~:880-900`, fix-pass update `:894-898` — are not); CIS `a3_atomize` (thread
  outlives the release, `a3_atomize_job.py:20-25, 87-94`; the run spans many transactions on a pool,
  `services/export/handler.py:184-245`); Partner `crm_dispatch` (provider send inside the row-lock transaction,
  `dispatch/worker.py:94-123`, providers take no idempotency key, `mail/providers/__init__.py:49`); Booking retention
  (`no_release`, `retention/jobs.py:72-74`); Booking `bk_notify_email` is at-least-once
  (`notifications/staff_email.py:14-15`).
- Migrations need hand steps per change: owner migration-only PR → hand-made byte-copy PR in Infra (8 of 15
  Infra PRs, median 19 min; #380 lost #372-#378 on squash) → DB Migrate dispatch → hand merge of the schema-dump PR
  (median 154 min open→merge) → a later code PR (MIG-4).
- The DB Migrate runner applies a file whenever its version is unregistered (`run_migration.py:35`), with no order
  check and no cross-run lock; the post-apply Isolation Probe is only dispatched, `continue-on-error`
  (`db-migrate.yml:367-379`). Infra `main` has no protection or ruleset, and DB Migrate assumes
  `aa-cis-infra-tf-apply` ("same grants as aa-cis-dev-role", `cicd_split.tf:14-16`) whose only gate is
  `ref == refs/heads/main` (`:565-592`). Today a person dispatches every apply.
- Post-deploy checks exist inline but are partial: Booking/Partner smoke is **skipped green at desired 0**
  (Booking `deploy-dev.yml:205-208`, Partner `:196-199`), and the whole Booking run is skipped green when
  `AWS_ROLE_ARN` is unset (`:70-87`); CIS admin checks are a **warning** without `ADMIN_SECRET`
  (`deploy-dev.yml:331-332`); TripPlanner production never reads `/api/health` (`vercel-deploy.yml:164-216`);
  Booking admin has no live UI smoke; the portal smoke skips logged-in tests without `E2E_TENANT_API_KEY`
  (`ui-smoke-portal.yml:8`). aa-ship §3 steps 1-4 are done by hand.
- All 7 red PR CI runs in the sample (CIS #1037 ×2, #1029; Booking #100, #94; TripPlanner #143) failed on checks
  a local hook can run. No repo has hooks.

## Decision

### D1 — Graceful worker shutdown; the deploy guard checks only an open wave and blocking kinds
1. **Drain window.** CIS `Worker.grace_seconds` default 20 → env `JOB_WORKER_GRACE_SECONDS` (default 100, validated
   `< stopTimeout − 15`). Booking and Partner add `--timeout-graceful-shutdown 5` to the uvicorn CMD so 5 s + 20 s
   worker wait + release fit inside stopTimeout 30.
2. **Releases caused by a deploy do not burn retries — CIS only.** CIS `queue.release` skips the `MAX_RELEASES` count
   when a newer task revision is alive (`newer_worker_alive`, `queue.py:503-512`). Booking/Partner **keep
   `MAX_RELEASES` = 3**: their worker runs in the API process, so a job that starves the loop causes health-check
   restarts, and a higher cap multiplies outages. Revision-aware counting there is a follow-up (needs a worker
   heartbeat like `shared.job_worker`).
3. **Non-idempotent kinds are made re-run safe, or stay blocking:**
   - CIS `s1_rewrite`: `ctx.progress` records `persist_stage` (`writer_done` with `writer_text`/`writer_model`,
     `content_inserted` with `version_id`, `scored`, `queued_for_review`, `fix_pass_saved`) after each step of
     `admin_pipeline.py:795-900`. A resumed job skips the paid writer via the `batch_text` / `batch_model_used` seam
     (`admin_pipeline.py:530-536`), and resumes each remaining step idempotently (`_enqueue_review` already guards a
     double enqueue, `:224-273`; the score insert checks for an existing row for `generated_content_id`). The early
     return at `s1_rewrite_job.py:49-54` fires **only when `phase == 'done'`**.
   - CIS `a3_atomize`: a `threading.Event` checked between days and set on `CancelledError`; a **session-level**
     `pg_advisory_lock(<tour key>)` held on one dedicated connection for the whole
     `_run_a3_atomize_background` run (atomize + segment matching + cache clear, `handler.py:184-245`) and released
     in `finally`; and a per-kind `release_delay_seconds` on `JobKind` (`registry.py:28-46`) = stopTimeout for
     thread-run kinds.
   - Partner `crm_dispatch`: **stays in `DEPLOY_BLOCKING_KINDS`** until a committed "send started" marker exists:
     tx1 locks the row, gates, inserts a `crm.dispatch_attempt(dispatch_id, attempt, started_at)` row, commits;
     the provider send runs outside any transaction; tx2 writes the decision. A re-run that finds an attempt with no
     decision sets `held` / `send_uncertain` (an existing status, `DECIDE_SQL`) instead of sending again. The new table
     is an expand migration (needs its DM-7 retention row first). No `asyncio.shield` (it does not survive the
     process ending after the 20 s wait, `main.py:80, 177`); no provider idempotency key (the `send` signatures take
     none).
   - Booking retention: in `DEPLOY_BLOCKING_KINDS` (replaces `DEPLOY_GATE_EXEMPT`, `kinds.py:25`); checkpointing is a
     follow-up. Booking `bk_notify_email`: accepted duplicate (documented at-least-once).
4. **Guard change** (only after 1-3 are live):
   - CIS `deploy_gate_status`: `safe_to_deploy = NOT EXISTS (SELECT 1 FROM shared.rerun_wave WHERE status='open')`
     AND no running row of a kind flagged `deploy_blocking`. New field `open_waves`; `active`/`by_status` stay as
     information. `deploy_job_guard.sh` keeps reading only `safe_to_deploy`; its message changes. The Platform Apps
     card (`api/services/platform_apps.py:80, 109`) and the post-deploy smoke (`staff_authz.py:455`) are updated
     to the new meaning.
   - Booking / Partner `deploy-gate`: safe unless a `DEPLOY_BLOCKING_KINDS` row is running. They do not read CIS
     waves (waves only drive `shared.job`).
   - Override input and Nghiệp-only rule unchanged.
5. **DB Migrate** keeps the all-job-tables-idle guard for files that are not `expand` (D2.3); expand files skip it.
6. **Visibility:** each worker logs `job_released_on_shutdown{kind, job_id}`; a new admin endpoint per app
   (`/admin/job-runner/released?since=<ts>`, M2M-allowlisted like `staff_authz.py:455`) returns the count, which the
   D3 verify prints (CI cannot reach RDS, `deploy-dev.yml:41-42`). Double spend stays visible in
   `shared.llm_call_log` per job id.

### D2 — The migration ships in the app PR; expand files are applied by an Infra pipeline before deploy
1. **One PR for expand files:** migration file + code + readiness bump (CIS `api/core/readiness.py:30`, Booking
   `backend/app/db.py:22-46`, Partner `api/app/db.py:31-54`) in the same app PR. **Contract and destructive files keep
   MIG-4 order** (migration-only PR → manual apply → code PR): app CI "Migration preflight" fails a PR that adds a
   non-expand file **and** raises the readiness requirement to it. App CI also refuses a PR that edits or deletes a
   migration file already present in the Infra copy (copied = immutable; a revert is code-only, explained in aa-ship),
   and requires a new file's number = owner `main` max + 1 (the merge queue re-runs this on the latest `main`).
   CODEOWNERS on the migrations folders stays the prod-phase approval point.
2. **Copy pulled by Infra, never pushed by the apps.** Infra `migration-sync.yml` (schedule every 10 min while Infra is
   public, plus manual) reads each public owner repo's `main` itself and computes the **set difference** of migration
   files (in the owner repo, missing from `db/migrations/<owner>/`), not "numbers above the head". It writes raw bytes,
   one file per branch `bot/migration-copy/<owner>-<NNN>` rebased on main, runs `check_migration_copies.py` +
   `check_migration_files.py` + `--classify` (D2.3), opens the PR as ci-bot with label
   `migration:expand|contract|destructive` (or `out-of-order` when the number is below the owner's highest
   registered key — never auto-applied), waits for required checks, squash-merges (dev phase). No app workflow
   mints a cross-repo token; there is no `repository_dispatch` payload to trust. Copy ≠ apply: every class is
   merged; only the apply differs.
3. **Classifier — header, static lint, authoritative runtime post-check:**
   - Header `-- migrate: expand` (new flag in `run_migration.py` `FLAGS` `:145`, parser `:465-474`). No header = contract
     (manual). `expand` + `destructive` = lint error; `expand` + `no-transaction` only for a non-UNIQUE
     `CREATE INDEX CONCURRENTLY IF NOT EXISTS`.
   - **Allowed in an expand file**, per pre-existing relation, and nothing else: a new column that is nullable or has a
     non-volatile, non-generated default; a new **non-unique** index (CONCURRENTLY when the table is above the size
     threshold); the internal RI triggers a new table's FK adds on the referenced table. New objects (tables, views,
     functions, types, sequences) are allowed, with: a new function whose name already exists in the schema (an
     overload) = contract; a new table in a schema whose tables require RLS must `ENABLE` **and** `FORCE` RLS; an FK
     from a new table is allowed (validation on an empty table), an FK added to an existing table is not.
   - **Contract**, on any pre-existing relation/object: a new policy, trigger, constraint or unique index; any change
     to columns other than the allowed ADD, `relacl`, RLS enable/force, `pg_default_acl`
     (`ALTER DEFAULT PRIVILEGES`), view/function definitions; any INSERT, UPDATE, DELETE or UPSERT on a pre-existing
     table (config/routing rows included); ADD COLUMN on a **hot table** (job tables `shared.job`, `booking.job`,
     `crm.job`, `shared.job_worker`, the ledgers, `catalog.*` base tables), because running code uses
     `SELECT *`/`RETURNING *` on them inside transactions (CIS `queue.py:90-110`; ~50 star sites in CIS non-test
     code, Booking 3, Partner 6) and a changed row type invalidates prepared statements there.
   - Static lint in `lint()` (`:840-891`) refuses the text-visible cases early (any `DESTRUCTIVE_RES`, `DELETE`,
     `UPDATE`, `INSERT … INTO` an object not created in the file, `ALTER … TYPE` / `SET NOT NULL` / `RENAME` /
     `VALIDATE` / `REVOKE` / `ALTER DEFAULT PRIVILEGES` / `CREATE UNIQUE INDEX`, `SET LOCAL ROLE catalog_owner`,
     `GRANT … TO` a role outside the owner's `runtime_roles` / `nologin_roles` in `owners.yaml`, any statement naming a
     hot table except a non-unique CIC).
   - Runtime post-check (authoritative), inside the apply transaction: a **new catalog query** (not `OBJECTS_SQL`,
     which keys on (kind, id, owner) and drops rows owned by the run-as role, `:252-258, 337-340`) that snapshots,
     for every pre-existing object in the owner's schemas **including objects owned by the owner role**: columns
     (type/null/default/generated), `relacl`, `relrowsecurity`/`relforcerowsecurity`, policies, non-internal triggers,
     constraints, indexes (with `indisunique`), `pg_get_viewdef`, `pg_get_functiondef` per signature, plus
     `pg_default_acl`, and `pg_stat_xact_user_tables.n_tup_ins/n_tup_upd/n_tup_del` on pre-existing tables. A diff
     outside the allowed set → ROLLBACK, **exit 14** "expand file changed an existing object: <object>". The same
     function runs in "classify" mode in app CI and on the Infra copy PR (replay against a CI Postgres, using the
     latest DB Schema Dump artifact for order (`replay_migrations.py:9-10`), falling back to number order), which
     sets the PR label from evidence.
4. **Lock risk is checked before the statements, not after.** Before executing an expand file the runner reads
   `pg_class.reltuples`/size for every table the file names (any statement), and refuses (exit 15, "lock risk →
   contract") a non-concurrent `CREATE INDEX`, a volatile/GENERATED STORED column, or any ACCESS EXCLUSIVE-taking
   statement on a table above 100k rows (MIG-10). Expand files run with `statement_timeout = 30s` (CIC excepted) and
   the existing `lock_timeout = 5s` (`:143`). After a CIC the runner checks `pg_index.indisvalid`; an INVALID index →
   exit 16, registration skipped (the `no-transaction` path cannot roll back the CIC itself, `:1170-1180`), and the
   summary names the index to drop.
5. **Apply.** Infra `migration-apply.yml` (push to main on `db/migrations/(cis|booking|tripplanner|crm)/**`, schedule,
   manual; environment `dev-db-auto`; own concurrency group `db-auto-apply`) runs `db/apply_pending.py`:
   - per owner, in **strict number order**: apply each unregistered expand file and **stop at the first unregistered
     file that is not expand** (or is `out-of-order`). Never skip past a gap;
   - before applying, re-check byte identity of each file against the owner repo's `main` and re-run `--classify`
     itself (never trust the merge or the label);
   - retry 55P03 with backoff;
   - then run the **Isolation Probe as a blocking job** and dispatch DB Schema Dump.
   The runner takes a session `pg_advisory_lock` (one key for all modes: apply, set-password, run-script, roles) so
   an auto-apply and a person's DB Migrate run never overlap; DB Migrate keeps its own group `db-migrate`
   (`db-migrate.yml:84-86`), so an auto-apply never replaces a pending manual run. Contract/destructive files are
   listed in the summary and commented on the copy PR "manual DB Migrate apply needed".
6. **Narrow role.** `migration-apply` assumes a new role `aa-cis-infra-db-auto-apply` (trust:
   `environment:dev-db-auto` + `ref:refs/heads/main`): `ecs:RunTask`/`RegisterTaskDefinition`/`DeregisterTaskDefinition`
   on the migrator family, `iam:PassRole` on the migrator task/execution roles only, `ecs:Describe*`, the S3 put/presign
   on the scripts prefix, logs read. Not `aa-cis-infra-tf-apply` (`cicd_split.tf:14-16, 565-592`).
7. **Order — gate before rollout.** App Deploy Dev gains a `schema-gate` job between `preflight` and `deploy`:
   - read the required keys from the code being deployed and poll Dev readiness until every key ≤ required is
     registered (CIS: readiness gains `registered_keys` above the legacy baseline and a `REQUIRED_CIS_KEYS` set, like
     Booking `db.py:22-46`; strict-prefix apply makes `max ≥ required` imply no gap, `readiness.py:39-41`);
   - require the `migration-apply` run that registered them to have concluded green, probe job included (`gh api`
     read on Infra);
   - fall back to `missing_schema_versions` when the running task predates `registered_keys`;
   - timeout 20 min, then fail **before** rollout with "required X not applied (contract/destructive → manual
     apply)". CIS/Partner Deploy Dev path filters add `!api/migrations/**`.
8. **Infra `main` protection.** A ruleset on Infra `main`: PR required; required checks Copy Guard,
   `check_migration_files`, classify, `terraform-plan`; no direct pushes, ci-bot included; bypass Nghiệp only.
   Valid only while Infra is public (ADR 0014 `:24-27`): going private sets `DB_AUTO_APPLY=false` (apply-pending then
   lists, never applies) until a paid plan or another gate exists.
9. **Schema-dump PR auto-merge** (`db-schema-dump.yml` `publish` job, `:417-486`) when: reason is after-apply or
   apply-pending; `DRIFT_CHANGED != true`; design-ERD drift step (moved before merge, today `:493-511`) green; root
   `docs-lint`/`contracts` checks green. `gh pr merge --squash` by polling (no `allow_auto_merge` on root/Infra).
   Nightly unexplained structural change stays manual.

### D3 — Automatic post-deploy verify in every deploy workflow
- A separate workflow `post-deploy-verify.yml` per repo (`workflow_call` + `workflow_dispatch` with `expected_sha`),
  job-level concurrency group `post-deploy-verify-<app>`, so a verify dispatch never takes the pending slot of
  `deploy-dev-*` (`deploy-dev.yml:29-31`). Called with `needs: deploy` from CIS `deploy-dev.yml`; Booking
  `deploy-dev.yml`; Partner `deploy-dev.yml`, `deploy-web-dev.yml`, `deploy-portal-dev.yml`; TripPlanner
  `deploy-lambdas.yml` and the production path of `vercel-deploy.yml`. The existing inline "Verify image" and
  "Smoke test" steps move into it.
- A final job `result` (`if: always()`) in each deploy workflow: on a `push` event, a skipped or failed `config`,
  `deploy` or `verify` is **red** (Booking's `config` skip at `:70-87` included).
- One script per repo `.github/scripts/post_deploy_verify.sh <app>` driven by `.github/verify/<app>.rows`
  (`name|method url|expected http|jq assertion`); a PR that changes an endpoint adds a row. Per repo, not a root
  reusable workflow; root `tools/verify/` holds the canonical copy with a byte check.
- Fixed rows: ECS `deployments[0].rolloutState == COMPLETED` and image = the built tag (CIS api **and** worker);
  `/health` `git_sha == expected` + `version` = manifest; `/health/ready` 200 + schema keys; CIS worker alive with
  `git_sha` = SHA and caps = registered kinds (hard fail, today `:298-329`); D1 released-on-shutdown count (info).
- Red rules: rollout not COMPLETED or rolled back; sha/image mismatch; ready ≠ 200; any row fails after 3 tries;
  a required secret/variable missing (CIS `ADMIN_SECRET`; `E2E_TENANT_API_KEY` for the portal smoke; Booking
  `AWS_ROLE_ARN`); **desired count 0 is red** (no automatic scale-up; Q6).
- New coverage: TripPlanner production `GET /api/health` compares `git_sha` with `steps.plan.outputs.sha`
  (what the deploy sets, `vercel-deploy.yml:144, 150`), plus `version`; Partner portal Fargate calls
  `ui-smoke-portal.yml` with `target=fargate` after `target` and `resolve_via` are added to its `workflow_call` inputs
  (today only under `workflow_dispatch`, `:10-24` vs `:37-49`); Booking admin gets a public Playwright smoke
  (`/login` renders, headers) on the production host.

### D4 — Merge queue on CIS, Booking, Partner (already being enabled)
- Rulesets: SQUASH, ALLGREEN, ≤5 per group, timeout 45/30/30 min; `ci.yml` runs on `merge_group` (CIS `:10`, Booking
  `:16`, Partner `:25`); merge through `tools/github/mergeq.sh`, never `update-branch`. Deploy Dev runs once per queue
  group, so verify (D3) checks the last `git_sha` of the group (aa-ship `:73-75`).
- After 5 green queued merges per repo, turn off "require branches to be up to date" (strict) in the classic branch
  protection of those three repos.
- TripPlanner (not strict, low traffic) and root: no queue. Infra: no queue, but the D2.8 ruleset.

### D5 — Pre-push hooks that run the CI commands
- Per repo `scripts/pre-push.sh` (bash), installed by `scripts/install-hooks.sh` → `git config core.hooksPath .githooks`
  (`.githooks/pre-push` calls the script; worktrees share it). No husky/pre-commit.
- Fast mode (default, target ≤ 90 s) on `git diff --name-only origin/main...HEAD`: `check_resource_ids.py` always;
  Python changed → Booking/Partner `ruff check .` + `ruff format --check .` (version from `requirements-dev.txt`),
  CIS the exact flake8 line (`ci.yml:38-41`) + `services.quality.lint --report` + `text_guard scan` (markers only),
  TripPlanner full backend pytest + `.github/scripts` unittests; unit tests for changed modules + `--lf`; frontend
  changed → `npm run lint` + `tsc --noEmit` (+ `npm test` where present), never `next build`; Infra →
  `terraform fmt -check -recursive`, `check_migration_files.py`, `terraform init -backend=false && validate` on
  touched roots, tests of changed `tools/`/`db/`.
- Full mode (`--full` or `AA_PREPUSH=full`) = the exact CI unit command with coverage (Booking/Partner
  `--cov-fail-under=90`; CIS `--cov=services --cov=shared` + `coverage_ratchet.py --base origin/main`).
- **One source of truth:** CI Lint and Unit steps call `scripts/pre-push.sh --full --ci`. `--ci` never skips by diff;
  in `--ci` on `main` or `merge_group`, a missing `GOLDEN_GUARD_KEY` (CIS `ci.yml:56-60`) is red.
  `scripts/pre-push.sh` and `.githooks/` go into CODEOWNERS and into the CI/workflow risk class.
- Close CI gaps in the same slices: pin flake8 in CIS (`ci.yml:34`), add `terraform fmt -check` to Infra CI, add ruff
  to TripPlanner backend.
- Bypass: `git push --no-verify`, documented in aa-ship.

## Consequences
- (+) Backend deploys stop waiting for idle job tables; only an open CIS wave or a running blocking kind blocks.
- (+) One PR per expand schema change; copy, apply and dump merge leave the critical path; code never goes live on a
  schema it needs but does not have (gate before rollout), and never past a missing lower-numbered file.
- (+) aa-ship §3 steps 1-4 become a CI job with a red/green result per deploy; a skipped deploy on push is red.
- (+) Lint/format/unit failures caught before push; CI runs per PR → ~1 with the queue.
- (−) A deploy during a paid `s1_rewrite` writer call pays that one call twice (per tour, per interruption); a
  LangGraph sync node mid-Bedrock completes and bills after cancel (`worker.py:383-387`). Accepted, visible in
  `llm_call_log`. Booking `bk_notify_email` may send one duplicate staff mail per interruption.
- (−) A `crm_dispatch` interrupted mid-send ends `held/send_uncertain` and needs a person to resend or close.
- (−) New Terraform/IAM (narrow role), an Infra ruleset, and ci-bot uses inside Infra (ADR 0011a). The DB gate on Dev
  is CI checks + the ruleset, not a person; it lapses if Infra goes private (auto-apply then off).
- (−) Expand is deliberately narrow: hot-table ADD COLUMN, new policies/constraints/unique indexes and config-row
  inserts are contract and stay manual.
- (−) The runtime post-check adds a catalog scan per expand file (seconds); CIS deploys get up to ~100 s longer drain.
- (−) More workflow code in five repos; the verify script is copied per repo.

## What stays manual
- Contract files (anything outside the D2.3 allowed set): migration-only PR → agent review → manual DB Migrate `apply`
  → code PR (MIG-4); from the first prod, Nghiệp approves (DM-11.5).
- Destructive files: RDS snapshot, DRY RUN counts to Nghiệp, dead-table registry (MIG-12, schema-ownership rule 6).
- Out-of-order copies and INVALID-index clean-ups (exit 16).
- `catalog.*` view changes, cross-owner grants (`owners.yaml` `consumer_grants` + `isolation_probe.py`), `roles/`
  files, `set-password`, `run-script`.
- New `crm` tables still need the DM-7 retention row in root first (Copy Guard retention job).
- Deploy override during an open wave or a running blocking kind: Nghiệp only, written reason.
- Nightly schema-dump PRs that no apply explains, and any dump with `DRIFT_CHANGED=true`.
- Scaling a stopped Dev service up for verify (cost rule).
- Terraform apply, and UI checks per aa-ui-verify beyond the smoke rows.

## Alternatives considered
- Keep "job tables idle" and shorten jobs: does not remove queued-row blocking or the wave/manual coupling.
- Reusable workflows in Infra/root called by the apps: break when Infra/root go private on GitHub Free (ADR 0014).
- App workflows push copy PRs or `repository_dispatch` to Infra with a minted ci-bot Contents-write token: that token
  can push to Infra `main` (runner and migrator script included) and the next auto-apply runs it with Dev DB
  rights; Infra pulling from the public owner repos needs no cross-repo write.
- Reuse `aa-cis-infra-tf-apply` for auto-apply: far wider than RunTask on one family.
- Reuse the `db-migrate` concurrency group: an auto-apply can replace a person's pending run.
- "Apply every expand file, skip contract": leaves gaps that a max-version readiness check cannot see.
- Header-only classification: the corpus scan shows a statement-head allowlist would pass 4 of 131 owner files, and
  `DO $$` guards (283) / `CREATE OR REPLACE` (316) make text rules unreliable; the catalog post-check is the authority.
- Per-object definition hashing: blocks normal ADD COLUMN/CREATE INDEX and passes new policies/triggers; replaced by
  an allowed-change list per existing relation.
- husky / pre-commit framework: extra version pins next to CI's; only CIS has a root `package.json`.
```

---

## 2. Slice plan

The risk class follows aa-ship and DM-11.5. A slice gets an independent review before merge (`kiro-reviewer` or an independent subagent) when it falls in any of these classes:

- auth
- migration or schema
- CI, workflow or secret
- IAM or Terraform
- data deletion

Every slice merges on its own and has a revert path.

Effort is rough agent time:

| Size | Agent time |
|---|---|
| S | ≤ 0.5 day |
| M | ≈ 1 day |
| L | ≈ 2–3 days |
| XL | ≈ 4–5 days |

### Phase A: post-deploy verify (D3)

**V1. CIS verify workflow** (AA-CIS-App)
- **Files:**
  - New `.github/workflows/post-deploy-verify.yml`: `workflow_call` + `workflow_dispatch(expected_sha)`, with job-level concurrency `post-deploy-verify-cis`.
  - `deploy-dev.yml`: move the steps at `:198-335` into the verify workflow, call it after `deploy`, and add the final `result` job (a skip on push is red).
  - New `.github/scripts/post_deploy_verify.sh` and `.github/verify/cis.rows`. These hold the admin rows `:256-260` and the worker rows `:298-329`, plus `rolloutState` checks on api and worker.
  - A missing `ADMIN_SECRET` becomes red.
- **Tests:** `tests/unit/test_post_deploy_verify.py` runs the script against fixture JSON. Each of these must exit non-zero: a sha mismatch, rolloutState FAILED, ready 503, a missing secret.
- **Risk:** CI/workflow, so it gets a review.
- **Live proof:**
  1. The next push-triggered Deploy Dev shows verify green, with the rows printed.
  2. A `post-deploy-verify` dispatch with `expected_sha=<previous sha>` goes red on the sha row.
  3. The dispatch does not cancel or replace a pending Deploy Dev run (check the run list).
- **Revert:** revert the PR.
- **Effort:** M.

**V2. Booking + Partner api verify** (AA-Booking, AA-Partner)
- **Files:**
  - The same verify-workflow pattern, with `booking.rows` and `crm.rows`.
  - Red at desired 0: today the smoke is skipped green (Booking `:205-208`, Partner `:196-199`).
  - Red on a `config` skip during a push (Booking `:70-87`).
- **Tests:** fixture tests in `backend/tests/unit/` and `api/tests/unit/`.
- **Risk:** CI/workflow, so it gets a review.
- **Live proof:**
  1. Deploy Dev is green with the rows printed.
  2. A wrong-sha dispatch goes red.
- **Effort:** S per repo.

**V3. Partner web + portal verify** (AA-Partner)
- **Files:**
  - `deploy-web-dev.yml`: rows `:150-168` move into verify.
  - `deploy-portal-dev.yml`: rows `:153-182`.
  - `ui-smoke-portal.yml`: add `target` and `resolve_via` to the `workflow_call` inputs, then call it with `target=fargate`.
  - A missing `E2E_TENANT_API_KEY` is red in this caller.
- **Risk:** CI/workflow, so it gets a review.
- **Live proof:** a portal deploy run with the UI smoke green. The logged-in tests must have executed, not been skipped (check the Playwright report).
- **Effort:** S.

**V4. TripPlanner verify** (AA-TripPlanner-Web)
- **Files:**
  - `vercel-deploy.yml` production path: `GET /api/health`, with `git_sha == steps.plan.outputs.sha` and `version` equal to the manifest.
  - `deploy-lambdas.yml`: rows `:128-153` move into verify.
- **Risk:** CI/workflow, so it gets a review.
- **Live proof:**
  1. A production deploy's verify shows the matching sha.
  2. A stale-sha dispatch goes red.
- **Effort:** S.

**V5. Booking admin public smoke** (AA-Booking)
- **Files:**
  - Playwright project `smoke-public` in `frontend/playwright.config.ts`: `/login` renders, no console errors, security headers present.
  - `vercel-deploy.yml` production calls it.
- **Risk:** CI/workflow, so it gets a review.
- **Live proof:** a production run with the smoke green and a screenshot artifact.
- **Effort:** M.

### Phase B: pre-push hooks (D5)

**H1. Hook scripts, local only** (all 5 repos plus root; root runs `check_adr_numbers` and docs-lint)
- **Files:**
  - `scripts/pre-push.sh`, `scripts/install-hooks.sh` and `.githooks/pre-push`.
  - An aa-ship note.
  - Root `tools/metrics/lead.py` and `ci_times.py`, persisted from the scratchpad.
- **Tests:** shellcheck, plus `--self-test` on a fixture diff.
- **Risk:** no CI change, so no review class applies.
- **Live proof:**
  1. Push a planted error: flake8 E501 in CIS, `ruff format` drift in Booking, `terraform fmt` drift in Infra.
  2. The hook blocks the push and prints the CI command.
  3. Fast mode finishes in under 90 s.
- **Revert:** `git config --unset core.hooksPath`.
- **Effort:** M.

**H2. CI calls the same script; close the gaps** (CIS, Booking, Partner, TripPlanner, Infra)
- **Changes:**
  - CI Lint and Unit steps run `scripts/pre-push.sh --full --ci`. `--ci` never skips by diff.
  - In `--ci` on main or `merge_group`, a missing `GOLDEN_GUARD_KEY` is red.
  - Add `scripts/pre-push.sh` and `.githooks/` to CODEOWNERS.
  - Pin flake8 in CIS (`ci.yml:34`).
  - Add `terraform fmt -check` to Infra `terraform-plan.yml`.
  - Add ruff to the TripPlanner backend, with a `pyproject.toml`.
  - Optionally add CIS `pytest-xdist` (Q13).
- **Risk:** CI/workflow, so it gets a review.
- **Live proof:**
  1. The required check names are unchanged.
  2. One PR per repo goes green through the script.
  3. Record the CIS Unit wall time before and after xdist.
- **Effort:** M.

### Phase C: graceful shutdown, then the guard change (D1)

**G1. CIS drain hardening** (AA-CIS-App, AA-CIS-Infra)
- **Files:**
  - `shared/jobs/worker.py:94`: grace from env, with an assertion.
  - `shared/jobs/queue.py:195-230`: a release does not count when `newer_worker_alive`; add `release_delay_seconds`.
  - `registry.py:28-46`: new fields `release_delay_seconds` and `deploy_blocking`.
  - A test-only kind `noop_sleep`, registered only when `JOB_TEST_KINDS=1`, with `deploy_gate_exempt=True` (`registry.py:40-43`).
  - New endpoint `/admin/job-runner/released`, M2M-allowlisted.
  - Infra `modules/ecs/main.tf:793-795`: update the comment and add worker env `JOB_WORKER_GRACE_SECONDS=100`.
- **Tests:**
  - `tests/unit/jobs/test_shutdown.py`: a job within the grace window completes; a longer one is released; when a newer revision is alive the release counter is unchanged.
  - An integration test on the CI Postgres: claim → SIGTERM → release → re-claim.
- **Risk:**
  - The job runner affects every job, so it gets a review.
  - The Infra env change is Terraform, so it gets a review.
- **Live proof:**
  1. Enqueue `noop_sleep(300 s)` on Dev.
  2. A normal Deploy Dev passes the guard without override, because the kind is exempt.
  3. The logs show `job_worker_draining`, then `job_released_on_shutdown`.
  4. The new revision re-claims the job, `attempt` is unchanged, and the job ends `succeeded`.
  5. The `released` endpoint shows 1.
- **Effort:** M.

**G2. CIS `s1_rewrite` persist stages** (AA-CIS-App)
- **Files:**
  - `services/jobs/s1_rewrite_job.py:49-54, 86-88`: the early return only on `phase=done`; resume by `persist_stage`.
  - `api/routers/admin_pipeline.py:795-900`: a stage checkpoint after each persist step, with idempotent resume for the score insert, `_enqueue_review` (`:224-273`) and the fix-pass update.
  - `:530-536`: reuse `batch_text`.
- **Tests:** cancel at each stage:
  - after the writer, no new LLM call;
  - after the INSERT, exactly one `generated_content` row, one `quality_scores` row and one review entry;
  - after scoring, no duplicate score.
- **Risk:** a paid path, so it gets a review.
- **Live proof:** a paid 3-tour trial with a deploy mid-run. Check:
  - one version per tour, each with a score and a review entry;
  - `llm_call_log` shows at most one writer call per tour, except one cut mid-writer;
  - the cost is reported.
- **Effort:** M.

**G3. CIS `a3_atomize` overlap** (AA-CIS-App)
- **Files:**
  - `services/jobs/a3_atomize_job.py:20-25, 87-94`: a `threading.Event`.
  - `services/export/handler.py:184-245`: a session `pg_advisory_lock(tour key)` on one dedicated connection for the whole run, released in `finally`.
  - Set `release_delay_seconds=120` on the kind.
- **Tests:**
  - A cancel stops the thread at the next day boundary.
  - A second run on the same tour blocks until the first releases the lock, across several transactions.
- **Live proof:**
  1. Atomize one tour and deploy mid-run.
  2. Old and new task logs show no overlap for that tour.
  3. The released row's `run_after` is at least 120 s after the release.
- **Effort:** S–M.

**G4. Booking + Partner drain** (AA-Booking, AA-Partner)
- **Files:**
  - `backend/Dockerfile:32` and `api/Dockerfile:32`: add `--timeout-graceful-shutdown 5`.
  - `MAX_RELEASES` stays at 3.
  - Booking `kinds.py:25`: `DEPLOY_BLOCKING_KINDS` = the retention kinds. Partner `kinds.py:68`: `{crm_dispatch}`.
- **Risk:** no formal review class.
- **Live proof:**
  1. Deploy Dev with `bk_x6_probe` running (C6.3a).
  2. The job is released and re-claimed.
  3. Task stop time stays under 30 s, read from the ECS events.
- **Effort:** S.

**G4b. Partner `crm_dispatch` send marker** (AA-Partner, root)
- **Order:** after M4, as an expand migration through the new flow. Until then, `crm_dispatch` stays blocking.
- **Files:**
  - Root: a DM-7 retention row for `crm.dispatch_attempt`.
  - Partner: a migration `crm-NNN` with `-- migrate: expand` (new table, ENABLE + FORCE RLS).
  - `api/app/dispatch/worker.py:94-123`: tx1 (lock, gate, insert attempt, commit) → send → tx2 (decide). A re-run with an attempt and no decision → `held`/`send_uncertain`.
  - After that, remove `crm_dispatch` from `DEPLOY_BLOCKING_KINDS`.
- **Tests:**
  - A fake sender cancelled after `send` returns → one send, and the row ends `held/send_uncertain`.
  - Cancelled before `send` → resend allowed.
- **Risk:** migration, so it gets a review.
- **Live proof:**
  1. Run a test dispatch to the E2E mail target with a deploy mid-run.
  2. Exactly one message arrives.
- **Effort:** M.

**G5. Guard change** (AA-CIS-App, AA-Booking, AA-Partner, root)
- **Order:** only after G1–G4 are live.
- **Files:**
  - CIS `shared/jobs/worker.py:365-372`: the wave and `deploy_blocking` logic, and the `open_waves` field.
  - `deploy_job_guard.sh:35-38`: the message.
  - `api/services/platform_apps.py:80, 109`: the Apps card text.
  - `staff_authz.py:455`: the route description.
  - Booking `routers/ops.py:39-44`.
  - The Partner `/crm/ci/deploy-gate` router.
  - Root: C6.3a (`03-scaling.md:343`), DM-11.4 (`02-data-management.md:378`) and aa-ship §2.
- **Tests:**
  - queued and running rows with no wave → safe;
  - an open wave → unsafe;
  - a running blocking kind → unsafe.
- **Risk:** the deploy gate (CI/workflow), so it gets a review.
- **Live proof:**
  1. With CIS jobs queued and running and no wave open, the preflight passes.
  2. Open a 0-tour test wave → the preflight blocks. Close it.
  3. A seeded Booking retention row blocks.
  4. A running Partner `crm_dispatch` blocks.
- **Revert:** revert the PR.
- **Effort:** S.

### Phase D: merge queue finish (D4)

**Q1. Queue proven, strict off** (CIS, Booking, Partner; GitHub settings)
- **Changes:**
  - After 5 green `merge_group` merges each, turn off strict.
  - Update aa-ship §1.
- **Risk:** CI settings, so it gets a review. Record the before and after `gh api` JSON.
- **Live proof:**
  - The protection JSON shows `strict: false`.
  - The next 15 PRs show no "Merge branch" commits and a median of 1 CI run.
- **Effort:** S.

### Phase E: migration flow (D2), last

**I1. Infra gate and narrow role** (AA-CIS-Infra, root). This must merge before M3.
- **Files:**
  - Terraform `accounts/aa365/cicd_split.tf`: new role `aa-cis-infra-db-auto-apply`. Trust: `environment:dev-db-auto` and `ref:refs/heads/main`. Grants: RunTask, Register and Deregister on the migrator family only, PassRole on the migrator roles, the S3 scripts prefix and logs read. It gets the same permissions boundary style as `tf_apply`.
  - The Infra environment `dev-db-auto` with a deployment-branch rule of `main`.
  - The Infra ruleset on `main`: PR required, required checks, no direct push (ci-bot included), Nghiệp bypass.
  - Root: draft ADR 0011a, and update `docs/security/github-apps.md`.
- **Risk:** IAM/Terraform, CI settings and secret, so it gets a review. The monthly cost is $0, since IAM costs nothing.
- **Live proof:**
  1. `gh api …/rulesets` lists the ruleset.
  2. A test direct push to Infra main with the ci-bot token is refused.
  3. The new role cannot `iam:PassRole` a non-migrator role, checked with `iam simulate-principal-policy` (read-only).
  4. A `workflow_dispatch` from a non-main ref fails to assume the role.
- **Effort:** M.

**M1. Schema-dump auto-merge** (AA-CIS-Infra, root)
- **Files:**
  - `db-schema-dump.yml`: move the ERD drift step (`:493-511`) before the merge, add the merge-condition block, and add the `crm` latest key (`:200, :460`).
  - `db/README.md:107` and steering `db-schema.md:25`.
- **Risk:** CI/workflow and secret, so it gets a review.
- **Live proof:**
  - The dump PR from the next apply is merged by ci-bot within minutes.
  - A nightly run with `DRIFT_CHANGED=true` stays open.
- **Effort:** S.

**M2a. Runner order, lock and lock-risk** (AA-CIS-Infra)
- **Files:** `db/run_migration.py`:
  - a session `pg_advisory_lock` for every applying mode;
  - the `expand` flag (`:145`, `:465-474`);
  - static lint additions (`:840-891`);
  - the pre-execution size check (exit 15);
  - `statement_timeout` 30 s for expand files;
  - the CIC `indisvalid` check (exit 16);
  - expand files skip the idle wait (`:1765-1790`);
  - refuse an expand file during an open wave if it names a hot table.
- **Tests (`db/tests/`):**
  - two concurrent apply processes serialize;
  - expand + REVOKE fails lint;
  - expand CREATE INDEX (non-concurrent) on a seeded 200k-row table → exit 15 before any lock;
  - an INVALID CIC → exit 16, not registered;
  - every Infra copy's `--inspect` on `origin/main` still passes.
- **Risk:** migration and CI, so it gets a review.
- **Effort:** L.

**M2b. Runtime post-check and classify** (AA-CIS-Infra)
- **Files:** `db/run_migration.py` and a new `db/expand_check.py`:
  - a new catalog query covering objects owned by the owner role (separate from `OBJECTS_SQL` at `:252-340`);
  - the allowed-change diff;
  - `n_tup_ins/upd/del`;
  - `pg_default_acl`;
  - function overloads;
  - RLS on new tables;
  - exit 14;
  - `--classify`;
  - replay with the dump artifact, falling back to number order.
- **Tests:** these must exit 14 on the CI Postgres:
  - expand + `CREATE POLICY … USING (true)` on an existing RLS table;
  - expand + a new trigger or CHECK on an existing table;
  - expand + INSERT into an existing config table;
  - a new table with no FORCE RLS in an RLS schema;
  - expand + `CREATE OR REPLACE VIEW` on an existing view;
  - an object owned by the owner role being altered;
  - expand + ADD COLUMN on `shared.job` (hot table).

  These must pass:
  - a new nullable column;
  - a non-unique CIC;
  - a new table with an FK to an existing table.

  An asyncpg test confirms that `RETURNING *` inside a transaction fails after ADD COLUMN on the same table. It proves the hot-table rule.
- **Risk:** migration and CI, so it gets a review.
- **Live proof:**
  1. DB Migrate `check` on Dev with an expand probe file (`CREATE TABLE IF NOT EXISTS booking.aa993_probe(...)` with RLS) → exit 0.
  2. The contract variant → exit 14 with the object named.
- **Effort:** XL.

**M3. Infra `migration-sync` + `migration-apply`** (AA-CIS-Infra). Merge only after I1, M2a and M2b.
- **Files:**
  - `migration-sync.yml`: schedule every 10 min plus manual; pulls from the public owner repos by set difference; adds the `out-of-order` label.
  - `tools/migration_sync.py`: raw bytes, using the `OWNERS` map from `check_migration_copies.py:56-62`.
  - `migration-apply.yml`: environment `dev-db-auto`, the narrow role, group `db-auto-apply`, the `DB_AUTO_APPLY` variable, and the blocking Isolation Probe job.
  - `db/apply_pending.py`: strict prefix order; stops at the first non-expand file; re-checks bytes against the owner's main and re-classifies.
  - The DB Migrate apply step moved into a shared script that both workflows use. `db-migrate.yml` keeps its own group.
- **Tests:**
  - `migration_sync`: byte identity; set difference finds a lower-numbered late file; one file per branch.
  - `apply_pending`: with expand 291 and contract 290 pending, nothing is applied; with expand 290 and 291, both are applied in order; a byte mismatch against the owner's main refuses.
- **Risk:** CI/workflow, secret and migration, so it gets a review.
- **Live proof:**
  1. A sync dispatch with nothing new does nothing.
  2. The M2b probe is copied, merged, applied, registered and probe-green, and the dump PR auto-merges.
  3. A manual DB Migrate `check` dispatched during an auto-apply waits on the advisory lock, and neither run is cancelled.
- **Effort:** L.

**M4a. Readiness keys first** (CIS, Booking, Partner)
- **Files:**
  - Booking and Partner `/health/ready` gain `registered_keys`.
  - CIS readiness gains `REQUIRED_CIS_KEYS` and `registered_keys` above the legacy baseline (`readiness.py:30-50`).
  - Each ships in its own PR, before M4b, so the first `schema-gate` reads a task that has the field.
- **Risk:** low. Readiness is part of the deploy contract, so it gets a review.
- **Live proof:** each `/health/ready` lists the keys.
- **Effort:** S per app.

**M4b. App side** (CIS, Booking, Partner; TripPlanner optional, Q14)
- **Files:**
  - Deploy Dev `schema-gate`: keys ≤ required are registered; the `migration-apply` run is green, probe included; falls back to `missing_schema_versions`.
  - The `!api/migrations/**` path for CIS and Partner.
  - The CI job "Migration preflight":
    - Infra `--inspect` and `check_migration_ownership.py` from a pinned Infra SHA;
    - number = owner main max + 1;
    - `--classify` on the CI DB;
    - a readiness-bump test;
    - refuse a non-expand file together with a readiness raise to it;
    - refuse editing or deleting a file already in the Infra copy.
  - CIS: a strict per-file apply in `tests/integration/conftest.py:519-534`.
  - No app `migration-sync.yml` and no cross-repo token.
- **Risk:** CI/workflow, so it gets a review.
- **Live proof (closes AA-993):**
  1. One Booking PR with an expand migration plus code that reads it.
  2. Merge → copied → applied → probe green → `schema-gate` passes → deploy → verify green with the new key, with no human step. Record the times.
  3. Negative 1: a PR with a contract file and a readiness raise is refused by the preflight.
  4. Negative 2: a contract-only PR is copied with the label `contract`, apply stops there, and a later deploy of code that does not need it still passes.
- **Effort:** M per app.

**M5. Root rules and ADRs** (root repo)
- **Changes:**
  - MIG-4 (`01-engineering.md:268-279`) for expand files, plus the checklist at `:697, :717`;
  - DM-11.2 and DM-11.4;
  - C6.3b;
  - ADR 0016 → Accepted;
  - ADR 0011a → Accepted;
  - `skill/aa-ship` §2–3, including the code-only revert rule;
  - `skill/aa-cis-schema` `:73-75, :101-102`;
  - the TripPlanner CI comment (`ci.yml:89-91`);
  - workflow headers, via M3.
- **Risk:** it changes the merge and migration rules, so it gets a review.
- **Proof:** root `contracts` and `docs-lint` are green.
- **Effort:** S.

**Suggested order:**

V1 → V2 → V3 → V4 → H1 → H2 → V5 → G1 → G2 → G3 → G4 → G5 → Q1 → I1 → M1 → M2a → M2b → M4a → M3 → M4b → G4b → M5

- Q1 can run in parallel at any point.
- M5 ships ADR 0016 as Proposed together with V1.
- The total is about 22 PRs across 6 repos, tracked under one Linear issue (AA-993) with the slices in the session checklist.

---

## 3. Measurement

### Baseline (READ 4, last 15 merged PRs per repo, 24–26/10/2026)

| Measure (median) | CIS | Booking | Partner | TripPlanner | Infra |
|---|---|---|---|---|---|
| PR lead time, created → merged | 59 min | 39 min (without release PRs; 50 with) | 8 min | ≈6.5 min (without release PRs; 24 with) | 9 min |
| CI runs per PR (mean, max) | 2 (1.8, 3) | 2 (2.1, 6) | 2 (1.7, 4) | 1 (1.3, 3) | 1 |
| Red CI runs / total | 3/27 | 3/31 | 0/25 | 1/20 | 0/15 |
| PRs with an update-branch commit | 10/15 | 4/15 | 7/15 | 0 | 0 |
| CI wall time, median / max | 10.8 / 11.7 min | 3.1 / 4.6 | 3.6 / 5.5 | 1.8 / 3.4 | plan 1.2, copy guard 0.5 |
| Deploy Dev | 5.7 min | 4.1 | 3.9 | — | DB Migrate 1.5 |

Migration chain medians:

- Infra copy PR: 19 min.
- Schema-dump PR: 154 min open → merge (range 15–1172).
- 8 of 15 Infra PRs were copy or run-script PRs.

### New metrics to add (no baseline yet; take them from Actions history before G5 and M4b)

1. **Deploy blocked by the guard.** Deploy Dev runs red at `preflight`, plus runs with `override_running_jobs`, per repo per week.
2. **Merge → verified live.** From `mergedAt` to the end of a green verify.
3. **Migration chain.** App PR `mergedAt` → copy PR merged → `migration-apply` run end (probe green) → `schema-gate` pass → verify green.
   - Old-flow baseline: owner migration PR → hand copy PR → DB Migrate apply → dump PR merged → code PR merged.
   - Source: the last 5 migrations per app.
4. **Released-on-shutdown count per deploy.** Read from the G1 endpoint. Also track duplicate LLM spend on released jobs: `shared.llm_call_log` grouped by job id where attempts > 1.
5. **Expand vs contract share and the contract wait.** The share of copy PRs labelled expand vs contract, and the median time a contract file waits for its manual apply. This checks that the narrow expand definition still removes most of the waiting.

### How to re-measure

- The scripts are committed in H1 to root `tools/metrics/` (`lead.py`, `ci_times.py`, with `--since <date>` and metrics 1–5).
- Re-run after each phase, counting only PRs created after that phase's last merge:

  | After | Measure |
  |---|---|
  | Phase A+B | red runs, CI runs per PR |
  | Q1 | update-branch count |
  | G5 | deploy-blocked count |
  | M4b | migration chain, dump time |

- Use the same 15-PR window per repo, read-only `gh api`.

### Targets

| Metric | Target |
|---|---|
| Red PR runs caused by lint, format or unit tests | 0 |
| CI runs per PR | ≤ 1.2 median, update-branch 0 |
| CIS lead time | ≤ 30 min median (needs xdist and the queue) |
| Guard blocks outside a wave or blocking kind | 0 |
| Expand migration chain | ≤ 25 min from app merge to verified live (10-min sync poll included), no human step |
| Schema-dump PR | ≤ 10 min after an apply |
| Push-triggered deploys ending "skipped green" | 0 |

---

## 4. Open questions, each with a proposed answer (Nghiệp decides)

> **Decided by Nghiệp, 26/10/2026 (S252):** Q6, Q7 and Q16 approved as proposed. The other questions follow the proposed answer.


| # | Question | Proposed answer |
|---|---|---|
| Q1 | How long should the CIS drain window be? | 100 s (`JOB_WORKER_GRACE_SECONDS`). That leaves 20 s of the 120 s stopTimeout. |
| Q2 | Do deploy releases count toward `MAX_RELEASES`? | **CIS:** no, when a newer revision is alive (`queue.py:503`). **Booking/Partner:** yes, and the cap stays at 3. A higher cap would prolong restart loops in the in-process worker. Revision-aware counting comes later. |
| Q3 | Booking retention during a deploy: block or checkpoint? | Block now (`DEPLOY_BLOCKING_KINDS`). A checkpoint per 1,000-row batch comes later. |
| Q4 | Should Booking and Partner deploys wait for an open CIS wave? | No. DM-11.4 is reworded to say so. |
| Q5 | Can an expand migration run during an open wave? | Yes, unless any statement names a hot table. Those files wait for the wave to close. |
| Q6 | Deploy Dev at desired count 0: skip or red? | **Red, with no automatic scale-up.** The current rule says scaling to 1 is a separate approved step (Booking `deploy-dev.yml:206`), and the cost rule applies. Nghiệp can choose to allow an automatic scale-to-1 for verify. |
| Q7 | How is auto-apply gated on Dev? | Through four controls: <ul><li>the Infra ruleset (I1);</li><li>environment `dev-db-auto` limited to `main`;</li><li>the narrow role trusting `environment:dev-db-auto` + `ref:main`;</li><li>re-classification inside the apply.</li></ul> No reviewer in the dev phase. From the first prod, Nghiệp is the required reviewer on the prod-DB equivalent. |
| Q8 | Should ci-bot merge copy PRs and schema-dump PRs? | Yes, inside Infra only, recorded in ADR 0011a. Apps mint no cross-repo token. |
| Q9 | `crm_dispatch`: idempotency key, or a send marker? | **The marker:** a `crm.dispatch_attempt` row committed before the send (an expand migration, G4b). A re-run that finds an attempt with no decision is `held/send_uncertain`. The provider `send` signatures take no key (`__init__.py:49`, `smtp.py:140`, `oauth_mail.py:137`), and `asyncio.shield` does not survive the process ending. Until G4b ships, the kind stays deploy-blocking. |
| Q10 | Verify script: per repo or shared? | Per repo, as `post-deploy-verify.yml` in each repo. A root canonical copy is kept with a byte check. |
| Q11 | Where does app CI get the Infra runner? | Sparse checkout at a pinned Infra SHA while Infra is public. After that, a byte-vendored copy with a vendored-copy check (AA-981). |
| Q12 | Turn off strict "up to date" once the queue runs? | Yes, on CIS, Booking and Partner after 5 green queued merges each. |
| Q13 | Use `pytest-xdist` for CIS? | Yes in H2, kept only if coverage stays within ±0.5 pp, the ratchet does not change and no new flaky test appears. |
| Q14 | Are TripPlanner `tp-NNN` migrations in scope for `schema-gate`? | Not in the first pass; that is optional slice M4-TP. Until then, TripPlanner expand files still auto-apply in strict order, and its code PRs keep the old order. |
| Q15 | Probe table on Dev: keep or drop it? | Use one `booking.aa993_probe` with RLS, then drop it through the destructive path (snapshot plus DRY RUN). |
| Q16 | What happens to auto-apply when Infra goes private again (ADR 0014)? | Rulesets and environment rules then disappear on Free (`0014:24-27`). Proposal: `DB_AUTO_APPLY=false` at the switch. Apply-pending then only lists files, copy and dump auto-merge continue, and expand files go back to a one-click manual DB Migrate. Revisit if the plan changes. |
| Q17 | The hot-table list for the "ADD COLUMN = contract" rule? | `shared.job`, `shared.job_worker`, `booking.job`, `crm.job`, the ledgers, and `catalog.*` base tables, kept in `owners.yaml`. A follow-up replaces `SELECT *` / `RETURNING *` on them (about 50 CIS sites, 3 in Booking, 6 in Partner) so the list can shrink. |

---

## Critic points applied / not applied (why)

**Applied (blocking)**

1. **Auto-apply security.** Applied in four ways:
   - New slice I1: an Infra ruleset (no direct push, ci-bot included), environment `dev-db-auto`, and a narrow role `aa-cis-infra-db-auto-apply` in place of `aa-cis-infra-tf-apply` (`cicd_split.tf:14-16, 565-592`).
   - Apps mint no token. Infra pulls from the public owner repos on a schedule. The dispatch and its payload are removed.
   - The apply re-checks bytes against the owner's `main` and re-classifies.
   - Added beyond the critic: the ruleset and environment rules only exist while Infra is public (ADR 0014 `:24-27`). Q16 turns auto-apply off when Infra goes private.
2. **Order and gaps.** Applied:
   - strict prefix apply, which stops at the first non-expand file;
   - set-difference sync, with an `out-of-order` label;
   - CI requires number = owner main max + 1;
   - CIS readiness gets an explicit `REQUIRED_CIS_KEYS` and `registered_keys` (`readiness.py:30-50`);
   - `schema-gate` checks every key ≤ required.
3. **Post-check spec.** Applied:
   - an allowed-change list per existing relation (new policy, trigger, constraint or unique index = contract; internal RI triggers allowed);
   - `n_tup_ins`, `pg_default_acl` and overloads are covered;
   - RLS ENABLE + FORCE on new tables;
   - a separate catalog query that covers owner-owned objects (`OBJECTS_SQL` drops them, `:252-258, 337-340`);
   - M2 is split into M2a (L) and M2b (XL).

**Applied (major)**

4. The Isolation Probe becomes a blocking job in `migration-apply` (today `continue-on-error`, `db-migrate.yml:367-379`), and `schema-gate` requires that run to be green. The RLS rule is in the post-check.
5. Lock risk:
   - a size check runs before execution (exit 15);
   - expand files run with `statement_timeout` 30 s;
   - after a CIC, `indisvalid` is checked (exit 16, not registered; the no-transaction path cannot roll back, `:1170-1180`);
   - no UNIQUE indexes and no FK validation on existing tables;
   - "hot table" means any table that any statement names.
6. ADD COLUMN on a hot table is classified as contract. A star-query replacement follow-up is listed (Q17), and an asyncpg test proves the failure (CIS `queue.py:90-110`). The star-site count I got is about 50 by line count; the critic said 52.
7. Contract files keep MIG-4 order. The preflight refuses a non-expand file together with a readiness raise to it.
8. `crm_dispatch` stays deploy-blocking until G4b ships the committed `dispatch_attempt` marker as an expand migration. The idempotency-key and `asyncio.shield` claims are dropped.
9. `s1_rewrite` uses a `persist_stage` marker. The early return fires only on `phase=done` (`s1_rewrite_job.py:49-54`).
10. `a3_atomize` uses a session-level advisory lock on one dedicated connection for the whole run (`handler.py:184-245`). The context line about "two platform-wide recomputes" is replaced; Score/Route now go to the debounced `recompute` job.
11. Auto-apply gets its own `db-auto-apply` group, and `run_migration.py` gets a session advisory lock for all applying modes. `git grep` confirms there is no advisory lock today.
12. Verify moves to `post-deploy-verify.yml` with job-level concurrency, so it no longer competes with `deploy-dev-cis` (`deploy-dev.yml:29-31`).
13. Silent green paths are closed:
    - a skipped deploy on push is red (final `result` job; Booking `:70-87`);
    - `target` and `resolve_via` are added to the `ui-smoke-portal.yml` `workflow_call` inputs (`:10-24` vs `:37-49`);
    - a missing smoke key is red;
    - TripPlanner compares against `steps.plan.outputs.sha` (`vercel-deploy.yml:144, 150`).

**Minor points (all applied)**

- **14:** a released-count admin endpoint, added in G1.
- **15:** `noop_sleep` with `deploy_gate_exempt=True`, so the G1 proof needs no override.
- **16:** Booking and Partner keep `MAX_RELEASES` = 3, so restart loops are not prolonged.
- **17:** copied migration files are immutable in app CI, and aa-ship gets a code-only revert rule.
- **18:** CODEOWNERS and the risk class cover the hook script; `--ci` never skips by diff; a missing `GOLDEN_GUARD_KEY` is red.
- **19:** classify replay uses the dump artifact and falls back to number order.
- **20:** desired count 0 is red with no automatic scale-up; Nghiệp decides on scale-up (Q6).
- **21:** G5 updates the Apps card, `staff_authz` and the new `open_waves` field.
- **22:** `bk_notify_email` is listed as an accepted duplicate.
- **23:** M4a ships `registered_keys` first, and `schema-gate` falls back to `missing_schema_versions`.
- **24:** the line checks are confirmed. Two heads have moved since the critic's read:
  - CIS is at 83eed0e1 (#1042);
  - Partner is at 7bd2bb0 (#90).

  Neither touches a cited file.

**Not applied or changed from the critic's fix**

- **The ruleset as the lasting gate (point 1).** It holds only while Infra is public; Q16 covers the private case. The critic's schedule of about 5 min is set to 10 min to bound Actions minutes when Infra becomes private (2,000 min/month, ADR 0014 `:29-30`). This adds about 5 min to the chain target, which rises from 20 to 25 min.
- **`asyncio.shield` and the idempotency key for `crm_dispatch` (Q9).** Removed rather than kept "where supported", because no current provider supports a key.

No files were edited, nothing was pushed, and no workflow or AWS call was run.