# ADR 0017 — Migrations ship in the app PR; expand files are auto-applied on Dev by an Infra pipeline before deploy

- **Status:** Proposed (2026-10-28, S254). Drafted from the AA-993 design (S252); nothing of it is built yet. The
  answers to the design's open questions that this ADR depends on (Q5, Q7, Q8, Q11, Q14–Q17) take their proposed
  answer; Q7 and Q16 were approved by the tech lead on 2026-10-26 (S252).
- **Scope:** AA-CIS-App, AA-Booking, AA-Partner (app CI "Migration preflight", the readiness keys, a `schema-gate` job
  in Deploy Dev; AA-TripPlanner-Web optional, Q14), AA-CIS-Infra (`db/run_migration.py` classifier and locks, the
  migration-sync and migration-apply workflows, a narrow IAM role, an environment and a ruleset on `main`, schema-dump
  auto-merge), root (data standards MIG-4 / DM-11.2 / DM-11.4 / C6.3b, skills `aa-ship` and `aa-cis-schema`,
  steering `db-schema.md`).
- **Amends:** data standards DM-11.2 (`02-data-management.md`), C6.3b (`03-scaling.md`) and Part A MIG-4
  (`01-engineering.md`, the order "migration-only PR → copy → apply → code PR") — for **expand** files only. Contract
  and destructive files keep MIG-4 unchanged.
- **Implements:** ADR 0003 / 0003a (per-owner job tables; the idle check stays for contract files); ADR 0008
  decision on one migration path through AA-CIS-Infra DB Migrate; ADR 0011 §4 (merge rights per tier).
- **Needs:** **ADR 0011a** (to write with slice I1): ci-bot may open and merge migration-copy PRs and schema-dump PRs
  **inside AA-CIS-Infra and the root repo only**; no app workflow mints a cross-repo write token.
- **Depends on:** ADR 0014 (repo visibility). The auto-apply gate is a ruleset plus environment rules on AA-CIS-Infra,
  which exist on GitHub Free only while the repo is public; going private switches auto-apply off (decision 8).
- **Design and evidence:** [`docs/audits/2026-10-26-S252-aa993-delivery-pipeline/design.md`](../audits/2026-10-26-S252-aa993-delivery-pipeline/design.md)
  (§1 D2, §2 Phase E slices I1, M1, M2a, M2b, M3, M4a, M4b, M5; §3 baseline; §4 questions) and its
  [`critic.md`](../audits/2026-10-26-S252-aa993-delivery-pipeline/critic.md) (points 1–7, 11, 17, 19, 23).
- **Related Linear:** AA-993.
- **Numbering note:** the AA-993 design draft called its whole decision set "ADR 0016" (D1 drain + deploy guard,
  D2 migrations, D3 post-deploy verify, D4 merge queue, D5 pre-push hooks). Number 0016 went to the UI kit ADR. Code
  and notes that cite "ADR 0016 D1 / D3" mean that design draft. D1, D3, D4 and D5 are being built as slices of
  AA-993 under the data standards (C6.2, C6.3a, DM-11.4) and need no ADR of their own; D2 is this ADR.

## Context

A schema change costs four hand steps and two waits today (design §3, last 15 PRs per repo, 24–2026-10-26):

1. the owner repo merges a **migration-only PR** (MIG-4);
2. a person makes a **byte copy PR** in AA-CIS-Infra `db/migrations/<owner>/` (8 of the last 15 Infra PRs; median
   19 min; #380 lost #372–#378 on a squash);
3. a person dispatches **DB Migrate** `check` then `apply` (1.5 min, but it waits for every job table to be idle);
4. the **schema-dump PR** on the root repo is merged by hand (median 154 min open → merge, range 15–1172 min);
5. only then the **code PR** that reads the new column merges.

The runner applies any unregistered file with no order check and no cross-run lock (`db/run_migration.py`: no
advisory lock), and the post-apply Isolation Probe is only dispatched, `continue-on-error`. AA-CIS-Infra `main` has no
branch protection and no ruleset; DB Migrate assumes the wide `aa-cis-infra-tf-apply` role whose only gate is
`ref == refs/heads/main`. A person dispatching every apply is the only control.

Most changes are additive (a new table, a nullable column, an index). They do not need the two-PR order: code that
reads them can ship with them **if** the schema is applied before the code rolls and old code keeps working on the new
schema. The risky changes (constraints, policies, grants, data rewrites, drops) still need a person.

## Decision

1. **One PR for expand files.** An app PR carries the migration file, the code that needs it and the readiness bump
   (CIS `api/core/readiness.py` `REQUIRED_CIS_KEYS`, Booking `backend/app/db.py`, Partner `api/app/db.py`). **Contract
   and destructive files keep MIG-4**: migration-only PR → manual DB Migrate apply → code PR. App CI "Migration
   preflight" fails a PR that:
   - adds a non-expand file **and** raises the readiness requirement to it (critic 7);
   - edits or deletes a migration file already present in the Infra copy (copied = immutable; a revert is code-only,
     explained in `aa-ship`, critic 17);
   - adds a file whose number is not the owner `main` max + 1 (the merge queue re-runs it on the latest `main`).
   CODEOWNERS on the migrations folders stays the approval point from the first prod / paying tenant (DM-11.5).
2. **The copy is pulled by Infra, never pushed by the apps.** AA-CIS-Infra `migration-sync.yml` (every 10 min while
   Infra is public, plus manual) reads each public owner repo's `main` and copies the **set difference** (files in the
   owner repo missing from `db/migrations/<owner>/`), raw bytes, one file per branch `bot/migration-copy/<owner>-<NNN>`.
   It runs the copy checks and the classifier (decision 3), labels the PR `migration:expand|contract|destructive`, or
   `out-of-order` when the number is below the owner's highest registered key (never auto-applied), and ci-bot
   squash-merges it after the required checks. Every class is copied; only the apply differs.
   *(Amended 2026-10-29, S258.)* The sync does not wait for the cron, which GitHub runs best effort: it also starts on
   an owner repo's doorbell comment (`migration-sync-wake.yml` after a push to `main` touching its migrations, ci-bot
   token with Issues write on Infra only, comment text never read; ADR 0011a decision 3) and when a copy PR's
   `Terraform Plan` / `Migration Copy Guard` run completes (`workflow_run`), so the merge pass follows the checks. The
   cron stays as the backstop.
3. **Classification: header, static lint, authoritative runtime post-check.**
   - Header `-- migrate: expand` (new runner flag). No header = contract. `expand` with `destructive` is a lint error;
     `expand` with `no-transaction` only for a non-unique `CREATE INDEX CONCURRENTLY IF NOT EXISTS`.
   - **Allowed in an expand file**, on a pre-existing relation, and nothing else: a new nullable column or one with a
     non-volatile, non-generated default; a new **non-unique** index (CONCURRENTLY above the size threshold); the
     internal RI triggers that a new table's FK adds on the referenced table. New objects (tables, views, functions,
     types, sequences) are allowed, except: an overload of an existing function name is contract; a new table in a
     schema whose tables require RLS must `ENABLE` **and** `FORCE` RLS; an FK from a new table is allowed, an FK added
     to an existing table is not.
   - **Contract** on any pre-existing object: a new policy, trigger, constraint or unique index; any other column
     change; `relacl`, RLS flags, `pg_default_acl`; view or function definitions; any INSERT / UPDATE / DELETE / UPSERT
     on an existing table (config and routing rows included); ADD COLUMN on a **hot table** (`shared.job`,
     `booking.job`, `crm.job`, `shared.job_worker`, the ledgers, `catalog.*` base tables; list in `owners.yaml`),
     because running code uses `SELECT *` / `RETURNING *` on them inside transactions and a changed row type breaks
     prepared statements (critic 6; about 50 star sites in CIS, 3 in Booking, 6 in Partner).
   - The static lint refuses the text-visible cases early. The **runtime post-check is the authority**: inside the
     apply transaction a dedicated catalog snapshot of every pre-existing object in the owner's schemas (including
     objects the owner role owns, which today's object snapshot drops) is diffed before / after, together with
     `pg_stat_xact_user_tables` insert / update / delete counts. A diff outside the allowed set rolls back with
     **exit 14** "expand file changed an existing object: `<object>`". The same function runs as `--classify` in app CI
     and on the copy PR, replaying against a CI Postgres in the order of the latest DB Schema Dump artifact (number
     order as the fallback, critic 19).
4. **Lock risk is checked before the statements run.** Before an expand file executes, the runner reads the size of
   every table the file names and refuses (**exit 15**, "lock risk → contract") a non-concurrent `CREATE INDEX`, a
   volatile or generated column, or any ACCESS EXCLUSIVE statement on a table above 100k rows (MIG-10). Expand files
   run with `statement_timeout = 30s` (CIC excepted) and the existing `lock_timeout = 5s`. After a CIC the runner
   checks `pg_index.indisvalid`; an INVALID index is **exit 16**, not registered, and the summary names the index to
   drop.
5. **Apply before deploy, in strict order.** AA-CIS-Infra `migration-apply.yml` (on push to `main` touching
   `db/migrations/(cis|booking|tripplanner|crm)/**`, on a schedule and by hand; environment `dev-db-auto`; its own
   concurrency group `db-auto-apply`) runs `db/apply_pending.py`:
   - per owner, in **number order**, apply each unregistered expand file and **stop at the first unregistered file
     that is not expand** (or is `out-of-order`); never skip past a gap (critic 2);
   - re-check each file's bytes against the owner repo's `main` and re-classify it before applying (never trust the
     merge or the label);
   - retry lock timeouts (55P03) with backoff;
   - run the **Isolation Probe as a blocking job**, then dispatch DB Schema Dump.
   The runner takes a session `pg_advisory_lock` (one key for apply, set-password, run-script and roles), so an
   auto-apply and a person's DB Migrate run never overlap; DB Migrate keeps its own concurrency group, so an
   auto-apply never replaces a pending manual run (critic 11). Expand files skip the all-job-tables-idle wait; an
   expand file that names a hot table waits for an open wave to close (Q5). Contract and destructive files are listed
   in the run summary and commented on their copy PR: "manual DB Migrate apply needed".
6. **A narrow role for the auto-apply.** `migration-apply` assumes a new role `aa-cis-infra-db-auto-apply`, trusted
   only for `environment:dev-db-auto` + `ref:refs/heads/main`: RunTask / RegisterTaskDefinition /
   DeregisterTaskDefinition on the migrator task family, `iam:PassRole` on the migrator task and execution roles only,
   `ecs:Describe*`, S3 put / presign on the scripts prefix, logs read; same permissions-boundary style as the
   Terraform roles. Not `aa-cis-infra-tf-apply`. Cost $0 (IAM).
7. **The deploy waits for its schema.** App Deploy Dev gets a `schema-gate` job between `preflight` and `deploy`: it
   reads the keys the deployed code requires and polls Dev readiness until every key up to the required one is
   registered (`registered_keys` on `/health/ready`, shipped first in its own PR, M4a; falls back to
   `missing_schema_versions` on an older task, critic 23), and requires the `migration-apply` run that registered
   them to be green, probe included. Timeout 20 min, then red **before** rollout: "required X not applied
   (contract/destructive → manual apply)". CIS and Partner Deploy Dev path filters add `!api/migrations/**`.
8. **Infra `main` is protected, or auto-apply is off.** A ruleset on AA-CIS-Infra `main`: PR required; required checks
   Copy Guard, `check_migration_files`, classify, `terraform-plan`; no direct pushes, ci-bot included; bypass the tech lead
   only. On GitHub Free a ruleset and environment rules exist only on a public repo (ADR 0014): when Infra goes
   private, repo variable `DB_AUTO_APPLY=false` turns the apply into "list only" (expand files go back to a one-click
   manual DB Migrate) until a paid plan or another gate exists (Q16). From the first prod, the tech lead is the required
   reviewer of the prod-DB equivalent (Q7).
9. **The schema-dump PR merges itself** (`db-schema-dump.yml` `publish` job) when the dump was triggered by an apply,
   `DRIFT_CHANGED != true`, the design-ERD drift step (moved before the merge) is green and the root `docs-lint` /
   `contracts` checks are green; merged by polling (`allow_auto_merge` is off on root and Infra). A nightly
   structural change that no apply explains stays manual.

## Consequences

- (+) One PR per additive schema change; copy, apply and dump leave the critical path. Target: ≤ 25 min from app
  merge to verified live with no human step (the 10-min sync poll included), schema-dump PR ≤ 10 min after an apply.
- (+) Code never rolls onto a schema it needs but does not have (`schema-gate` before rollout), and never past a
  missing lower-numbered file (strict prefix apply).
- (+) The apply path is narrower and better locked than today: a dedicated role, an advisory lock, a blocking
  Isolation Probe, and a ruleset where there is none.
- (−) Expand is deliberately narrow: hot-table ADD COLUMN, new policies / constraints / unique indexes and config-row
  inserts are contract and stay manual. The `SELECT *` follow-up (Q17) is what lets the hot-table list shrink.
- (−) New Terraform/IAM, an Infra ruleset, two workflows and ci-bot uses inside Infra (ADR 0011a). The Dev DB gate is
  CI checks + the ruleset, not a person, and it lapses if Infra goes private (auto-apply then off).
- (−) The runtime post-check adds a catalog scan per expand file (seconds). A contract file merged in an app PR's
  number sequence blocks later expand files of that owner until a person applies it (by design: no gaps).
- (−) A revert of an app PR whose migration was applied is code-only; the file stays (copied = immutable).

## What stays manual

- Contract files: migration-only PR → agent review → manual DB Migrate `apply` → code PR (MIG-4); from the first prod,
  the tech lead approves (DM-11.5). Destructive files: RDS snapshot, DRY RUN counts to the tech lead, dead-table registry.
- Out-of-order copies and INVALID-index clean-ups (exit 16).
- `catalog.*` view changes, cross-owner grants (`owners.yaml` `consumer_grants` + the isolation probe), `roles/`
  files, `set-password`, `run-script`.
- New `crm` tables still need their DM-7 retention row in root first (Copy Guard retention check).
- Nightly schema-dump PRs that no apply explains, and any dump with `DRIFT_CHANGED=true`.

## Rollout (design Phase E, in this order)

I1 (Infra role, environment, ruleset; ADR 0011a) → M1 (schema-dump auto-merge) → M2a (runner order, lock, lock-risk)
→ M2b (runtime post-check and `--classify`) → M4a (readiness `registered_keys` per app) → M3 (`migration-sync` +
`migration-apply`) → M4b (app `schema-gate` + Migration preflight; closes AA-993 with one Booking PR going merge →
copied → applied → probe green → deploy → verify, no human step) → M5 (root rules: MIG-4, DM-11.2, DM-11.4, C6.3b,
`aa-ship`, `aa-cis-schema`; this ADR → Accepted, ADR 0011a → Accepted). Each slice is in the risk class that gets an
independent review before merge (migration, CI/workflow, IAM).

## Alternatives considered

- **Keep MIG-4 for every file and only automate the copy:** removes one hand step, keeps the two-PR order and the
  waits for the additive majority.
- **App workflows push the copy PR (or `repository_dispatch`) with a minted ci-bot token:** that token can write to
  Infra `main`, runner script included, and the next auto-apply would run it with Dev DB rights. Pulling from the
  public owner repos needs no cross-repo write (critic 1).
- **Reuse `aa-cis-infra-tf-apply` for the apply:** far wider than RunTask on one task family.
- **Reuse the `db-migrate` concurrency group:** an auto-apply could replace a person's pending run (critic 11).
- **Apply every expand file and skip contract ones:** leaves gaps that a max-version readiness check cannot see
  (critic 2).
- **Header-only classification:** a statement-head allowlist would pass 4 of 131 owner files; `DO $$` guards and
  `CREATE OR REPLACE` make text rules unreliable. The catalog post-check is the authority.
- **Per-object definition hashing:** blocks a normal ADD COLUMN / CREATE INDEX and passes a new policy or trigger;
  replaced by an allowed-change list per existing relation (critic 3).
- **Reusable workflows in Infra or root called by the apps:** break when those repos go private on GitHub Free
  (ADR 0014).
