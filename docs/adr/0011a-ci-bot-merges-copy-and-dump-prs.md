# ADR 0011 — Amendment: ci-bot opens and merges migration-copy PRs in AA-CIS-Infra and schema-dump PRs in the root repo

- **Status:** Proposed (28/10/2026, S255). Written with AA-993 Phase E slice I1, as [ADR 0017](0017-migrations-in-app-pr-expand-auto-apply.md)
  requires ("Needs: ADR 0011a"). Becomes Accepted with ADR 0017 in slice M5, after the first copy PR and the first
  schema-dump PR are merged by ci-bot on Dev.
- **Scope:** AA-CIS-Infra (`db-schema-dump.yml` publish job, the coming `migration-sync.yml`), the root repo
  (`bot/db-schema-reference` PRs), the GitHub App `aa-ci-bot` (live name `aa-ecosys-ci-bot`). The app repos are
  **not** affected: none of their workflows gets a token for another repo.
- **Amends:** [ADR 0011](0011-github-app-identity-and-merge-rights.md) decision 1 (what `aa-ci-bot` is used for) and
  decision 3 (who acts as which identity: the row "release-please release PR, Infra root docs PRs"). Decision 4 (merge
  rights per risk tier) is unchanged for every PR a person or an agent opens.
- **Implements:** ADR 0017 decisions 2 (the copy is pulled by Infra, never pushed by the apps) and 9 (the schema-dump
  PR merges itself); AA-993 design Q8 (ci-bot merges copy and dump PRs inside Infra and the root repo only) and critic
  point 1 (no cross-repo write token minted by an app workflow).
- **Design and evidence:** [`docs/audits/2026-10-26-S252-aa993-delivery-pipeline/design.md`](../audits/2026-10-26-S252-aa993-delivery-pipeline/design.md)
  §1 D2, §2 I1 / M1 / M3, §4 Q8; [`critic.md`](../audits/2026-10-26-S252-aa993-delivery-pipeline/critic.md) point 1.
- **Related Linear:** AA-993.

## Context

ADR 0011 gave `aa-ci-bot` two jobs: release-please release PRs in the app repos, and the AA-CIS-Infra workflows that
open root docs PRs (DB Schema Dump, Docs Gen). In both, a person (or the orchestrating agent) merges the PR.

ADR 0017 removes two hand steps from every additive schema change:

1. the byte copy of an app's migration file into AA-CIS-Infra `db/migrations/<owner>/` (8 of the last 15 Infra PRs);
2. the merge of the root `bot/db-schema-reference` PR after each apply (median 154 min open).

Both are generated, checked content. Having a bot merge them is only safe if the bot cannot also write anything else
that later runs with database rights, and if no app workflow holds a token that can write to AA-CIS-Infra (critic
point 1: such a token could push `db/run_migration.py`, and the next auto-apply would run it).

## Decisions

1. **ci-bot may open and squash-merge two kinds of PR, and only these:**

   | PR | Repo | Branch | Opened by | Merged when |
   |---|---|---|---|---|
   | Migration copy | AA-CIS-Infra | `bot/migration-copy/<owner>-<NNN>`, one file per branch | `migration-sync.yml` (slice M3) | the required checks of the Infra ruleset on `main` are green (Copy Guard, migration lint, classify, Terraform Plan, gitleaks) and the diff is exactly one new file under `db/migrations/<owner>/`, byte-identical to the owner repo's `main` |
   | Schema dump | root | `bot/db-schema-reference` | `db-schema-dump.yml` (existing) | ADR 0017 decision 9: dispatched after an apply, opened by this run, drift fingerprint unchanged, design ERD drift green, only the generated files, every root check green (`db/schema_dump_automerge.py`) |

   Any other PR ci-bot opens (release PRs, Docs Gen PRs) is still merged by a person or the orchestrating agent, as in
   ADR 0011 decision 4.
2. **The token is minted inside the Infra workflow that needs it, on `main` only, narrowed to one repo and to Contents +
   Pull requests write** (`actions/create-github-app-token` with `repositories` and `permission-*`). The copy job's
   token covers AA-CIS-Infra only; the dump job's token covers the root repo only. No token gets Workflows, Actions,
   Administration or Secrets.
3. **No app workflow mints a token for another repo.** The copy is pulled: Infra reads the public owner repos'
   `main` anonymously (set difference of migration files) and never trusts a payload from an app. There is no
   `repository_dispatch` from the apps.
4. **ci-bot cannot push to AA-CIS-Infra `main`.** The ruleset on `main` (AA-CIS-Infra
   `tools/github/infra-main-ruleset.json`, applied with Nghiệp's login by `tools/github/db_auto_apply_gate.sh`)
   requires a PR and green checks for every actor; ci-bot is not a bypass actor. Its merge of a copy PR is the only way
   its write reaches `main`, and the auto-apply re-checks the bytes against the owner repo and re-classifies the file
   before it runs it (ADR 0017 decision 5).
5. **The root repo has no ruleset today** (no required checks on GitHub for root, ADR 0014 decision 3). The dump job
   therefore checks the PR itself before it merges: only `docs/architecture/db-schema-reference.md` and top-level
   generated ERD pages, every check run on the head commit green, `Docs lint` and `gitleaks` present, merge pinned to
   the head commit it checked.
6. **When AA-CIS-Infra goes private** (ADR 0014), the ruleset stops being enforced on GitHub Free. ADR 0017 decision 8
   then switches the auto-apply off (`DB_AUTO_APPLY=false`); copy PRs may still be opened by ci-bot, but are merged by
   a person or the agent until a gate exists again.

## Consequences

- **Positive:** the copy and the dump leave the critical path of a schema change; every bot merge is limited to
  generated or byte-copied content and leaves a `aa-ecosys-ci-bot[bot]` entry on the PR timeline.
- **Negative:** a leaked ci-bot key could open and merge a copy PR in Infra or a dump PR in root, within the checks
  above. It still cannot push to Infra `main`, change a workflow, read a secret or dispatch the apply (no Actions
  permission), and the apply re-verifies the copied file against the owner repo.
- **Cost:** 0 USD (GitHub Free, public repos).

## Alternatives considered

- **App workflows push the copy PR with a minted ci-bot token:** that token could write to Infra `main` or to the
  runner; rejected (critic point 1).
- **The agent keeps merging both PRs:** keeps two waits on every schema change (ADR 0017 Context).
- **A third App only for these merges:** a separate key with the same blast radius inside Infra and root; not worth
  the extra key while both stay within one App's narrowed tokens.
