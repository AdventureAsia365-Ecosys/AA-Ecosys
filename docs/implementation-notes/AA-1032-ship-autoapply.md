# AA-1032 — Implementation notes (root repo, lane ship-autoapply: parts 1 and 5)

The code half is in AA-CIS-Infra (branch `feat/aa-1032-contract-auto-apply`, its own
`docs/implementation-notes/AA-1032-ship-autoapply.md`). This file covers the root docs, skills and the lane template.

## Decisions

- **Decision record:** an amendment `docs/adr/0017a-dev-auto-applies-contract-migrations.md`, not a new number:
  it narrows ADR 0017 decisions 1 and 5 and "What stays manual" for Dev only. ADR 0017 gets a pointer, the README
  index a row.
- **Data standards v1.12:** MIG-4 and DM-11.2 carry a one-sentence Dev exception pointing to ADR 0017a; the idle rule
  (C6.3b / DM-11.4) itself is unchanged, the pipeline now enforces it instead of a person.
- **MIG-4's order stays** (migration-only PR, then the code PR): only the manual DB Migrate step goes away on Dev.
  Skills and runbook now say: read the Migration Apply run summary; `dbmig.sh` only for a `manual` stop, destructive
  files and the tech lead's busy override.
- **Header-less DELETE (review fix pass):** ADR 0017a decision 2, the runbook, `aa-ship`, the handbook (EN + VI) and
  MIG-4's Dev exception now say a contract file with a `DELETE` but no `-- migrate: destructive` header stays manual
  (Infra stop kind `delete`). The lint only warns about it, and an automatic run has no reader for a warning.
- **Batching (part 5):** written as a lane rule (one migration-only PR with consecutive numbers per owner, or files
  listed in number order with a `batch:` line) and as an orchestrator rule in `aa-ship` and `merge-trains.md`.
- **Lane CI parity (part 5):** `lane.js` COMMON now asks for the app preflight, integration tests of touched modules
  and a gitleaks scan of the lane's commits with the CI pin (v8.30.1, checksum-verified download into the scratchpad;
  no Docker in WSL). Checked by this lane on its own commits.
- **Lesson cleanup:** the S258 lesson "bot reads the latest check run" is now a test in Infra
  (`LatestCheckRunTest`) and its line is removed; the S260 train lesson point (3) names the real cause.

## Changed

- `docs/adr/0017a-…` (new), `docs/adr/0017-…` (pointer), `docs/adr/README.md`.
- `docs/architecture/data-standards/01-engineering.md` (MIG-4), `02-data-management.md` (DM-11.2), `README.md` (v1.12).
- `docs/engineering-handbook.md` + `.vi.md` (D8 path), `docs/ops/runbooks/db-migrate.md` (when to use, precondition).
- `skill/aa-ship/SKILL.md`, `skill/aa-ship/references/merge-trains.md`, `skill/aa-cis-schema/SKILL.md`,
  `skill/aa-lessons/lessons.md`, `tools/workflows/lane.js`.

## Tradeoffs

- `tools/github/train-lib.sh` `waitcopy` is unchanged (still merges an open contract copy PR after a gate): harmless
  now that ci-bot merges it, and the ship-helpers part of AA-1032 (another lane) owns the train helpers.

## Should know

- Merge order: the Infra PR first (behaviour), then this root PR (the docs describe what is live). If this root PR
  merges first, the docs describe a Dev behaviour that is not on Infra `main` yet.
- The packaged skills (`aa-ship`, `aa-cis-schema`, `aa-lessons`) need a re-upload at session end (skill aa-session).
