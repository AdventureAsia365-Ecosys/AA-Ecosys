# AA-853 live verification (S250, 25/10/2026)

Issue: AA-853 "Schema drift diff against a replayed DB + migration ownership lint". Linear status at check time: In Progress.
Merged: Infra #379 (`b1d2e92`, ownership lint, 04:16 UTC) and Infra #380 (`af8ac53`, drift report, 04:17 UTC).
Infra `main` = `af8ac53` at check time.

Verdict: **partial**. The ownership lint is proven on the code now on `main`, by a local run. The nightly drift report
has **not run on `main` yet**, so neither Done-when item has a GitHub run link on `main`.

## 1. Ownership lint (Done-when 2: red on a test migration that touches another owner's schema, green otherwise)

| Evidence | Result |
|---|---|
| PR #379 CI, Migration Copy Guard run 40156473742 (branch `feat/aa-853-migration-ownership-lint`), job "Migration lint and unique numbers" | pass (every copy listed `ok`) |
| PR #380 CI, run 40161322783 | pass, but its head (`6f50bfb`) does **not** contain #379, so this run does not exercise the lint |
| Copy Guard runs on `main` since #379 merged | **none**. Last scheduled run 40073555018 (24/10 07:17 UTC) predates #379. The Copy Guard runs on `main` only on the nightly schedule (02:17 UTC) or a manual dispatch |
| Local, exact export of `origin/main` `af8ac53`: `python3 db/check_migration_files.py` | exit 0, `116 file(s) linted, unique numbers checked, 0 problem(s)` |
| Local, same tree: `python3 -m unittest discover -s db/tests` | `Ran 633 tests`, `OK (skipped=1)`; `test_check_migration_ownership.py` 21 tests OK |
| Local red probe: `db/migrations/tripplanner/099_aa853_red_probe.sql` with `CREATE TABLE booking.aa853_probe (id int);` + its own `shared.schema_versions` row | exit 1: `line 2: CREATE TABLE booking.aa853_probe: schema booking belongs to owner booking; a tripplanner/ migration touches only tripplanner (db/owners.yaml schemas, AA-853)` |
| Local green probe: same file with `CREATE TABLE tripplanner.aa853_probe` | exit 0, `117 file(s) linted ... 0 problem(s)` |

The probe file was created only in a scratch export and deleted; nothing was pushed.

## 2. Schema drift report (Done-when 1: a nightly run reports 0 unmanaged objects, or each remaining one has an owner decision)

| Evidence | Result |
|---|---|
| DB Schema Dump runs on `main` at or after `af8ac53` | **none**. Latest run 40157565576 (03:15 UTC, `8af6e11`) predates #380 and has no drift job |
| Root `docs/architecture/db-schema-reference.md` on master | no `drift-fingerprint` marker, no "Schema drift" section yet (bot PR #244, merged 04:34 UTC, came from the pre-#380 run) |
| Next scheduled run | 03:43 UTC 26/10 (schedules on this repo have fired late, e.g. 24/10 at 08:25 UTC) |
| Expected first numbers (PR #380 body, local end-to-end run against the 24/10 20:23 UTC live dump, before the job split) | replay 330 files: 174 ok, 20 partly, 136 failed; drift 188 unmanaged, 22 missing, 30 changed, 233 explained by a replay gap. `db/schema_drift_decisions.json` starts empty, so these are open |

Unmanaged / missing / changed counts **from a run on `main`: not available** (no run yet).

### Known side issue that will make the next run red (not AA-853)

Every DB Schema Dump run since 24/10 19:12 UTC ended `failure` at the step "Design ERD drift (report)" (AA-894 scope 3):
run 40157565576 shows `tripplanner.md` enforce=yes with 2 findings (fails) and `crm.md` 136 findings (report only).
In the new three-job layout this step is the last step of the `publish` job, after the root PR step, so the root PR
(with the drift section) is still opened. The run conclusion will still be `failure` until the tripplanner design
page is updated or its enforce flag is turned off. Do not read that red as an AA-853 failure.

## Done-when mapping

| Done-when | Status | What closes it |
|---|---|---|
| Nightly run reports 0 unmanaged, or each remaining one listed with an owner decision (run link) | **Open.** No run on `main` yet; the first run is expected to show ~188 unmanaged, all without a decision | (a) a DB Schema Dump run on `main` (dispatch or tonight's schedule) with the step summary "Schema drift (AA-853)" and the drift section in the root PR; (b) owner decisions in `db/schema_drift_decisions.json` and/or the AA-ACP-Core `db/replay_baseline/` file until open unmanaged = 0 |
| Lint red on a test migration touching another owner's schema, green otherwise (run links) | **Met in substance, locally**; red/green proven on `main`'s code (above) plus unit tests `OtherOwnersFail` / `WiredIntoTheCopyGuardLint`. GitHub run link on `main` still missing | a Migration Copy Guard run on `main` (dispatch, or tonight's 02:17 UTC schedule) green |

## Not done by this check (blocked for a subagent)

`gh workflow run` is blocked by `.claude/hooks/subagent-guardrails.sh`. The orchestrator can run:

- `gh workflow run "Migration Copy Guard" -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main`
- `gh workflow run "DB Schema Dump (shared RDS)" -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f reason="AA-853 live verify (S250)" -f publish=false`
  (read-only against the DB; a changed drift fingerprint opens or updates the root PR `bot/db-schema-reference` anyway, by design;
  PR #380's own test plan suggests `publish=true`)

After the dump run, check: all three jobs ran, `drift` is green (or `publish` stayed green past a red `drift`), the step summary
"Schema drift (AA-853)" counts, the `db-schema-drift-<run id>` artifact, and the drift section in the root PR.
