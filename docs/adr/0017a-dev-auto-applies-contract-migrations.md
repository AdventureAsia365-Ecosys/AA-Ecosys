# ADR 0017 — Amendment A1: Dev auto-applies contract migrations when every job table is idle; prod unchanged

- **Status:** Accepted (01/11/2026, S263, AA-1032: the tech lead asked for the ship-loop optimisations to be done now).
  Separate file, following the `0003a` pattern; ADR 0017 itself only gets a pointer.
- **Amends:** ADR 0017 decision 1 ("Contract and destructive files keep MIG-4"), decision 5 ("stop at the first
  unregistered file that is not expand"; "Contract and destructive files are listed … manual DB Migrate apply needed")
  and the section "What stays manual", **on Dev only**. Data standards Part A **MIG-4** and Part B **DM-11.2** get the
  same Dev exception (standards v1.12).
- **Implements:** ADR 0003a decision 5 and data standards **DM-11.4** / **C6.3b** (a contract apply waits for every
  owner job table to be idle and no rerun wave to be open) without a person; ADR 0011a (ci-bot merges copy PRs).
- **Related Linear:** AA-1032 (parts 1 and 5), AA-993 (the pipeline this extends).
- **Built in:** AA-CIS-Infra `db/run_migration.py` (apply-pending contract mode), `db/apply_pending.py`,
  `db/migration_sync.py`, `.github/workflows/migration-apply.yml`, `db/owners.yaml`
  `contract_auto_apply_environments`; implementation notes `docs/implementation-notes/AA-1032-ship-autoapply.md`.

## Context

In S263 a contract migration took about 40-50 minutes of wall time from the owner's migration-only PR to a code PR
that could merge: CI, the merge queue, the bot copy PR (often merged by hand, because a cancelled duplicate
`gitleaks` run made ci-bot refuse it), then a person dispatching DB Migrate `check` and `apply`, then the schema-dump
PR. Seven CIS files (325-331) and three CRM files (crm-036 to crm-038) went through this one by one. The manual step
adds no control that the pipeline lacks on Dev: DB Migrate `apply` of a contract file is a click whose only guard is
the idle check, and the reviewed file is already on the owner's `main` and byte-checked.

Dev has no real users or traffic (dev phase, DM-11.5). Prod does not exist yet; from the first prod or paying tenant
the tech lead approves every migration before it is applied (DM-11.5, ADR 0017 decision 8, Q7).

## Decision

1. **On Dev, Migration Apply applies contract files too.** A contract file (no `-- migrate: expand` header, not
   destructive) is applied in its turn, in key order per owner, by the same `apply-pending` task as expand files, when:
   - its bytes equal the owner repo's `main` (re-checked by the runner, never trusted from the copy PR);
   - the classify replay of Dev applied it cleanly (role switch and ownership post-check included) and its lint is
     clean;
   - every owner job table (`shared.job`, `booking.job`, `crm.job`, any `<schema>.job`) is idle and no rerun wave is
     open: the same wait as DB Migrate `apply` (three checks 20 s apart, non-exempt kinds, no override ever). Still
     busy = **deferred**: the owner stops there, the run stays green, the hourly run (or the next copy merge) retries.

   It runs like a DB Migrate `apply` of that file: default `lock_timeout` 5 s and `statement_timeout` 15 min, the role
   switch to the live owner, the ownership post-check, then the blocking Isolation Probe and DB Schema Dump of the
   run.
2. **Strict order and stops are unchanged.** Per owner in key order; the first failure stops that owner (the other
   owners still run, ADR 0017 decision 5); never past a gap, a copy PR not merged yet, or an out-of-order file.
   **Destructive files** (`-- migrate: destructive`) are always a stop with their own note: DRY RUN counts to the tech
   lead, then DB Migrate (RDS snapshot), as before. A **contract file with a `DELETE`** statement but no destructive
   header is a stop too (kind `delete`, its own note): the lint only warns about it (MIG-12) and nobody reads a
   warning on an automatic run, so a person adds the header (snapshot, DRY RUN) or applies it with DB Migrate.
   Out-of-order files, `roles/`, `catalog.*` recipes that need a
   person, `set-password` and `run-script` stay manual.
3. **Dev only; prod unchanged.** The environment is checked three times: the workflow's `TARGET_ENV` (the
   workflow targets the Dev cluster and database), the runner (`apply_pending.py --environment … --contract`) and the
   task, which refuses (exit 10) a bundle that asks for contract files outside `db/owners.yaml`
   `contract_auto_apply_environments` (`[dev]`). A prod copy of the workflow keeps contract files manual; changing that
   needs a new ADR.
4. **Kill switch.** The AA-CIS-Infra repo variable `DB_AUTO_APPLY_CONTRACT=false` turns contract mode off: contract
   files are listed and noted on their copy PR "manual DB Migrate apply needed", as before this amendment.
   `DB_AUTO_APPLY` and the public repo + ruleset gate (ADR 0017 decision 8) still gate the whole apply.
5. **ci-bot merges every green copy PR, judged on the latest run of each check.** Migration Sync already merged every
   class; it refused PRs whose head commit carried a cancelled duplicate check run next to a green one. It now reads
   the latest run per check name and app, as GitHub does, so contract copies merge without a person.
6. **MIG-4's order stays.** A contract file still ships in a migration-only PR before the code PR (the app "Migration
   preflight" still refuses a readiness raise to a non-expand file). On Dev the step "a person runs DB Migrate" becomes
   "Migration Apply applies it when idle". The orchestrator batches the migration-only PRs of one owner in a wave (one
   PR with consecutive numbers, or merged back to back) so one copy-and-apply cycle covers them.

## Consequences

- (+) A contract migration on Dev goes owner merge → bot copy → applied with no hand step; the code PR waits only for
  the schema gate. Target: the S263 40-50 min loop drops to the copy + apply time (about 10-15 min when idle).
- (+) Copy PRs no longer need a person because of a cancelled duplicate check run.
- (−) A contract file can now change a policy, constraint, grant or config row on Dev without a person pressing a
  button. Accepted for Dev: the file is reviewed on the owner's `main`, replayed on a copy of Dev first, applied only
  when the job tables are idle, and the Isolation Probe after it is blocking.
- (−) A long wave or a busy job table delays a contract file and every later file of its owner until the next idle
  run. A person can still run DB Migrate with `override_busy_jobs` (tech lead only).
- (−) One more Dev-only behaviour to remember when prod comes: the prod workflow must not set its environment to one in
  `contract_auto_apply_environments`.

## Alternatives considered

- **Keep the manual DB Migrate step for contract files (ADR 0017 as accepted):** the S263 cost above, for no added
  control on Dev.
- **A second workflow for contract files:** two apply paths would need their own ordering against each other; the
  existing task already holds the apply lock and the strict per-owner order.
- **Apply contract files without the idle wait (like expand files):** a constraint or policy change under a running
  job can block or break it; DM-11.4 keeps the idle rule for contract changes.
- **Auto-apply destructive files after a snapshot:** destructive changes need the DRY RUN counts and a person's
  decision (MIG-12, destructive-ops); not worth automating on Dev.
