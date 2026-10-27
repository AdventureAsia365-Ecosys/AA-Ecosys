# AA-993 design — critic pass (S252)

1. **Blocking: the push-triggered auto-apply runs with the Terraform-apply role, and nothing protects Infra `main`.**
   - Problem: D2.2 and D2.4 mean that any push to Infra `main` touching `db/migrations/**` applies SQL to Dev. Infra `main` has no protection, no rulesets, and the `prod` environment has no rules (live `gh api`: 404, `[]`, `protection_rules: []`). The app `migration-sync.yml` mints a ci-bot token with Contents write on AA-CIS-Infra. That token can push straight to `main`, and so can anyone holding a ci-bot key. It can also edit `.github/scripts/migrator-task.sh` or `db/run_migration.py`, because files outside `.github/workflows/` need no Workflows permission. The next auto-apply then runs that code as `aa-cis-infra-tf-apply`. That role has the "same grants as aa-cis-dev-role", and its only gate is `ref == refs/heads/main`. Today a person dispatches the apply. Q7's "dev-db-auto restricted to main" adds nothing while `main` is unprotected.
   - Evidence:
     - Infra `accounts/aa365/cicd_split.tf:14, 565-592`
     - `db-migrate.yml:97`
     - ADR 0011 `:37, :43-45`
     - `docs/security/github-apps.md:199-200`
   - Fix:
     - Add a slice before M3. Infra gets a ruleset: PRs required, Copy Guard and migration-files checks required, no direct pushes (ci-bot included), bypass for Nghiệp only.
     - The auto-apply gets its own narrow IAM role: RunTask on the migrator family plus S3 presign. Trust `environment:dev-db-auto` + `ref:main`. This is a Terraform/IAM slice that the plan lacks today.
     - `migration-apply` re-checks byte identity against the owner's `main` and runs the classifier itself. It never trusts the merge.
     - Prefer an Infra schedule (about every 5 min) that polls the public owner repos over app-minted Contents-write tokens. If dispatch stays, Infra ignores the payload's `owner`/`sha` and reads the owner's `main` itself.

2. **Blocking: expand files are applied out of order, and the CIS check uses the highest number, so `schema-gate` can pass while a contract file is still missing.**
   - Problem: `apply-pending` applies "every unregistered copy classified expand", skipping contract files. `run_migration.py` applies one file whenever its version is unregistered and has no gap or order check (`:35`). CIS readiness compares `max(version::int) >= REQUIRED_CIS_SCHEMA` (`api/core/readiness.py:30-35, 55`). Example: expand 291 is applied while contract 290 is pending. The max is 291, the gate passes, and code that needs 290 deploys.
   - Two more problems:
     - Infra sync copies only files "above the Infra head" (D2.2). A lower-numbered file merged later, which is common with parallel lanes, is never copied.
     - Replay treats unregistered files below the latest registered one as legacy (`db/replay_migrations.py:26-27`), so the drift report goes wrong too.
   - Fix:
     - `apply-pending` stops at the first unregistered non-expand file of each owner (strict prefix order).
     - Sync by set difference (files missing in Infra), not by number.
     - CIS readiness checks an explicit set of required keys, like Booking (`backend/app/db.py`), or "no unregistered owner file ≤ required".
     - `schema-gate` checks that every key ≤ required is registered.

3. **Blocking: the expand post-check is not specified tightly enough, and it can approve changes that widen access.**
   - Problem 1: "Definition hash of every pre-existing object" conflicts with the normal expand cases. ADD COLUMN and CREATE INDEX on an existing table change that table's column and index sets.
   - Problem 2: if policies, triggers and constraints are hashed per object, a new `CREATE POLICY … USING (true)` on an existing RLS table is a "new object" and passes. So do a new trigger, a CHECK constraint or a UNIQUE index on an existing table. Each one changes how existing data is accessed, or breaks writes from the old code.
   - Problem 3: a new FK from a new table adds internal RI triggers on the existing referenced table, which gives false positives.
   - Problem 4: `ALTER DEFAULT PRIVILEGES`, function overloads and INSERT/UPSERT of config rows into existing tables (for example routing rows that change paid LLM calls) are not covered. `n_tup_ins` is not read, and an UPSERT shows up as `n_tup_upd`.
   - Problem 5: "extending `object_snapshot`" does not work as written. `OBJECTS_SQL` keys only on (kind, id, owner) and drops every row owned by the role the file runs as (`run_migration.py:255-258, 337-340`). Those are exactly the owner objects an expand file must not change.
   - Fix:
     - Define allowed changes per existing table: a new nullable column or one with a non-volatile default; a new non-unique index (CONCURRENTLY above the size threshold); internal FK triggers on the referenced table.
     - Anything else on an existing relation is contract: a new policy, trigger, constraint or unique index; any change to `relacl`, RLS flags or `pg_default_acl`; any INSERT, UPDATE or DELETE.
     - A new table in a schema that requires RLS must have ENABLE + FORCE.
     - Write a separate catalog query that includes objects owned by the owner role.
     - Re-estimate M2 above L.

4. **Major: the Isolation Probe does not block after an auto-apply, and the runner has no RLS lint.**
   - Problem: today the probe is only dispatched, with `continue-on-error` (`db-migrate.yml:367-379`). `git grep` finds no RLS check in `run_migration.py`, `check_migration_files.py` or `check_migration_ownership.py`. With no human between merge and apply, a new tenant table without FORCE RLS goes live, and the code that uses it deploys.
   - Fix: `migration-apply` runs the probe as a blocking job, and `schema-gate` waits for it to pass. Add the RLS rule for new tables to the post-check in item 3.

5. **Major: the lock-risk control acts after the lock is taken, and the no-transaction path cannot roll back.**
   - Problem 1: the runtime post-check runs after the statements, so an ACCESS EXCLUSIVE lock has already been held. `lock_timeout 5s` only limits the wait to get the lock. `statement_timeout` is 15 min (`run_migration.py:143`).
   - Problem 2: these are missing from the lock-risk list: a volatile or GENERATED STORED column (table rewrite), and an FK validated on a big table.
   - Problem 3: the Q5 "ALTERs a hot table" test misses CREATE INDEX, CREATE TRIGGER and REFERENCES on `shared.job`, `booking.job`, `crm.job` or `catalog.*`.
   - Problem 4: for `no-transaction` files, only the registration runs in the runner's transaction (`:1177-1180`), so exit 14 cannot undo a CIC. `CREATE INDEX CONCURRENTLY IF NOT EXISTS` after a failed build finds the INVALID index, skips it, and registers the file. A UNIQUE CIC breaks old-code inserts.
   - Fix:
     - Run a static pre-check against sizes from the latest dump before executing.
     - Expand files get `statement_timeout` ≤ 30 s, except CIC.
     - After a CIC, check `pg_index.indisvalid`.
     - No UNIQUE and no FK validation in expand files.
     - A "hot table" is any table named by any statement in the file.

6. **Major: running old code can break during an expand.**
   - Problem: asyncpg raises `InvalidCachedStatementError` when a prepared statement's result type changes inside a transaction; it cannot re-prepare there. The CIS claim uses `RETURNING *` inside `conn.transaction()` (`shared/jobs/queue.py:90-110`). CIS has 52 non-test `SELECT *` / `RETURNING *` sites; Booking has 3 and Partner 6. An expand ADD COLUMN on `shared.job` or a ledger fails these calls on every pooled connection. This is the "breaks the running old code during expand" case, and the design does not mention it.
   - Fix: classify ADD COLUMN on tables that are always busy (job tables, ledgers) as contract, or require the star queries on them to be replaced with explicit column lists first. Add a test or lint for this.

7. **Major: a contract migration inside an app PR blocks every later deploy of that app.**
   - Problem: under D2.1 and D2.5, code that needs a contract or destructive file reaches `main`, and from then on every Deploy Dev of that app fails at `schema-gate` until someone applies the file by hand. MIG-4 avoided this by putting the migration first and the code in a later PR (`01-engineering.md:268-271`).
   - Fix: the app CI job "Migration preflight" fails a PR that both adds a non-expand file and raises the readiness key to it. Contract files keep the migration-only PR → apply → code PR order.

8. **Major: `crm_dispatch` can still send a second e-mail when G5 empties the Partner blocking set.**
   - Problem: the provider call runs inside `system_tx`, before the decision commits (`api/app/dispatch/worker.py:94-123`). The providers are SMTP and OAuth mail (`mail/providers/smtp.py:140`, `oauth_mail.py:137`). Neither `send` signature takes an idempotency key, so the Q9 key protects nothing today. `asyncio.shield` does not survive the process ending: lifespan waits 20 s (`main.py:80, 177`), then the event loop cancels the remaining tasks.
   - Fix: keep `crm_dispatch` in `DEPLOY_BLOCKING_KINDS` until a committed "send started" marker exists. That marker can ship as an expand change (a new `crm.dispatch_attempt` row committed before the send, skip when it exists) instead of the CHECK change at `010_crm_data_lifecycle.sql:313`.

9. **Major: the `s1_rewrite` checkpoint makes a resumed job skip its remaining persist steps.**
   - Problem: the existing read-before-write returns early on any `progress.version_id` (`services/jobs/s1_rewrite_job.py:49-54`). If `version_id` is written right after the `generated_content` INSERT (`admin_pipeline.py:795`), a release before the remaining persist steps (quality_scores `:849`, review_queue `~:880-900`, fix_pass update `:894-898`) ends "succeeded". The version then has no score and no review entry.
   - Fix: store a `persist_stage` marker, resume each remaining step idempotently (`_enqueue_review` already guards double enqueue, `:224-273`), and return early only when `phase=done`.

10. **Major: the `a3_atomize` lock as designed does not stop two runs overlapping.**
    - Problem: `pg_advisory_xact_lock` is released at the end of each transaction. `_run_a3_atomize_background` opens a pool and runs many transactions (`services/export/handler.py:184-245`). READ1's "two platform-wide recomputes" is out of date: Score/Route now go to a debounced `recompute` job (`:213-244`). The real overlap is atomize, segment matching and cache clearing on the same tour.
    - Fix: hold a session-level `pg_advisory_lock(tour key)` on one dedicated connection for the whole run, or a lease row. Keep `release_delay_seconds`.

11. **Major: auto-apply runs can cancel a DB Migrate run that a person dispatched.**
    - Problem: GitHub keeps only one pending run per concurrency group. If `migration-apply` reuses the `db-migrate` group through `workflow_call`, an auto-apply run can replace a pending manual contract apply, `set-password` or `run-script` run. `db-schema-dump.yml:71-72` already records this hazard. Using a separate group instead lets two migrator tasks run at once, and the runner takes no advisory lock (no hit in `git grep`).
    - Fix: give auto-apply its own group, and add a session advisory lock in `run_migration.py` for every apply mode.

12. **Major: a `verify_only` dispatch can drop a real deploy.**
    - Problem: the concurrency is workflow-level, group `deploy-dev-cis`, `cancel-in-progress: false` (`deploy-dev.yml:29-31`). A `verify_only` dispatch takes the single pending slot and cancels a pending push deploy. The 20-minute `schema-gate` poll also holds the group.
    - Fix: put verify in its own `post-deploy-verify.yml` with its own group. Deploy Dev calls it through `workflow_call`, and it can also be dispatched.

13. **Major: the verify job can be green when nothing was verified.**
    - Problem:
      - `if: needs.deploy.result == 'success'` skips verify when deploy is skipped. Booking's `config` job skips the whole run when `AWS_ROLE_ARN` is unset (READ2, `deploy-dev.yml:70-87`).
      - `ui-smoke-portal.yml` skips its logged-in tests when `E2E_TENANT_API_KEY` is missing (`:8`).
      - `target` exists only as a `workflow_dispatch` input (`:37`), not under `workflow_call` (`:10-24`), so V3's `uses: … target=fargate` will not work.
      - TripPlanner sets `GIT_SHA` from `steps.plan.outputs.sha` (`vercel-deploy.yml:144, 150`), not `GITHUB_SHA`.
    - Fix:
      - For push events, a skipped deploy is red.
      - Add `target` and `resolve_via` to the `workflow_call` inputs.
      - In verify, a missing smoke key is red.
      - TripPlanner compares against the plan sha.

14. **Minor: the "released-on-shutdown count" in verify needs data CI cannot reach.**
    - Problem: CI cannot reach RDS (`deploy-dev.yml:41-42`), and no endpoint returns this count.
    - Fix: add an admin endpoint as part of G1.

15. **Minor: the G1–G3 live proofs need the override that only Nghiệp may use.**
    - Problem: the proofs rely on `override_running_jobs` before G5, and the 100 s drain adds up to about 100 s to every CIS deploy.
    - Fix: register the probe kind `noop_sleep` with `deploy_gate_exempt=True` (`shared/jobs/registry.py:40-43`), so the proof needs no override.

16. **Minor: raising Booking and Partner `MAX_RELEASES` to 10 also prolongs outages from a bad job.**
    - Problem: their worker runs inside the API process. A job that starves the event loop fails health checks, ECS sends SIGTERM, the job is released without counting an attempt, and the cycle repeats: 10 API restarts instead of 3 (S201 precedent, `a3_atomize_job.py:20-25`).
    - Fix: count releases unless a newer task revision is alive, using the ECS task metadata the way CIS does (`ecs_task_revision`). Keep the cap at 3.

17. **Minor: there is no rule for reverting an app PR whose migration was already applied.**
    - Problem: the revert deletes the file from the owner's `main`. The Copy Guard nightly then fails (`check_migration_copies.py:163-176`), and the number can be reused.
    - Fix: app CI refuses to delete or edit a migration file already registered on Dev; aa-ship explains a code-only revert.

18. **Minor: CI that calls `scripts/pre-push.sh` can be weakened without the CI review.**
    - Problem: once CI Lint and Unit run the script, a PR can weaken required checks by editing `scripts/`, which is outside the CI/workflow risk class and outside CODEOWNERS. CIS `text_guard` needs `GOLDEN_GUARD_KEY` in CI (`ci.yml:56-60`).
    - Fix:
      - Add `scripts/pre-push.sh` and `.githooks/` to CODEOWNERS and to the risk class.
      - `--ci` never uses diff-based skipping.
      - In `--ci` mode on `main` or `merge_group`, a missing `GOLDEN_GUARD_KEY` is red.

19. **Minor: the copy-PR classify step cannot run "without AWS".**
    - Problem: the replay takes its file order from the live `schema_versions` dump (`replay_migrations.py:9-10`, `db-schema-dump.yml:301`).
    - Fix: the copy-PR job downloads the latest dump artifact, or the replay falls back to number order.

20. **Minor: scaling Booking and Partner to 1 in Deploy Dev (Q6) breaks a stated rule.**
    - Problem: the current step says "scale to 1 is a separate approved step" (Booking `deploy-dev.yml:206`), and the cost rule applies.
    - Fix: get Nghiệp's yes before turning on an automatic scale-up, or make desired 0 red without scaling.

21. **Minor: changing what `deploy_gate_status` means also changes other pages.**
    - Problem: the Platform Apps page reads it (`api/services/platform_apps.py:80, 109`), and so does the post-deploy smoke (`api/core/staff_authz.py:455`).
    - Fix: G5 updates the Apps-page text and adds an `open_waves` field.

22. **Minor: D1.3 leaves out Booking `bk_notify_email`.**
    - Problem: this kind is documented as at-least-once (`backend/app/notifications/staff_email.py:14-15`), so a deploy can send the staff a duplicate e-mail.
    - Fix: list it as an accepted duplicate.

23. **Minor: the first deploy after M4 can fail at `schema-gate`.**
    - Problem: `schema-gate` polls `registered_keys` from the old task, which does not have that field yet.
    - Fix: ship the readiness field in its own PR first, or let the gate fall back to `missing_schema_versions`.

24. **Minor: the cited line numbers I checked are correct.**
    - CIS `worker.py:94` (`grace_seconds=20`), `:291-303`, `:365-372`
    - `deploy_job_guard.sh:33-38`
    - `main.tf:793-795`, `booking.tf:387`, `crm_app.tf:447`
    - Booking and Partner `Dockerfile:32`
    - Partner `kinds.py:68`, `queue.py:31`
    - Booking `kinds.py:25`
    - ADR "Next free root numbers: **0016**"

All of the above was read on Infra cee70f3, CIS d0ff7e08, Booking f47a750, Partner 86082f4, TripPlanner 3f6228a and root b2e3626, after `git fetch`. I used read-only `gh api` calls. Nothing was edited or pushed.