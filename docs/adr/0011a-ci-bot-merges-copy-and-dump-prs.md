# ADR 0011 — Amendment: ci-bot opens and merges migration-copy PRs in AA-CIS-Infra and schema-dump PRs in the root repo

- **Status:** Proposed (28/10/2026, S255). Written with AA-993 Phase E slice I1, as [ADR 0017](0017-migrations-in-app-pr-expand-auto-apply.md)
  requires ("Needs: ADR 0011a"). Becomes Accepted with ADR 0017 in slice M5, after the first copy PR and the first
  schema-dump PR are merged by ci-bot on Dev.
- **Scope:** AA-CIS-Infra (`db-schema-dump.yml` publish job, the coming `migration-sync.yml`), the root repo
  (`bot/db-schema-reference` PRs), the GitHub App `aa-ci-bot` (live name `aa-ecosys-ci-bot`). The app repos are
  **not** affected: none of their workflows gets a token for AA-CIS-Infra or the root repo (the one cross-repo app
  token, the CIS kit sync of [ADR 0016](0016-one-design-system-guarded-kit-copies.md) decision 6, reaches only the
  three consumer app repos; decision 3).
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
   | Schema dump | root | `bot/db-schema-reference` | `db-schema-dump.yml` (existing) | ADR 0017 decision 9: dispatched after an apply, opened by this run, drift fingerprint computed in this run and unchanged, design ERD drift green, only the generated files, every root check green (`db/schema_dump_automerge.py`) |

   Any other PR ci-bot opens (release PRs, Docs Gen PRs) is still merged by a person or the orchestrating agent, as in
   ADR 0011 decision 4.
2. **The token is minted inside the Infra workflow that needs it, on `main` only, narrowed to one repo and to Contents +
   Pull requests write** (`actions/create-github-app-token` with `repositories` and `permission-*`). The copy job's
   token covers AA-CIS-Infra only; the dump job's token covers the root repo only. No token gets Workflows, Actions,
   Administration or Secrets.
3. **No app workflow mints a token for AA-CIS-Infra or the root repo.** The copy is pulled: Infra reads the public
   owner repos' `main` anonymously (set difference of migration files) and never trusts a payload from an app. There
   is no `repository_dispatch` from the apps.
   The one cross-repo token an app workflow mints is AA-CIS-App `kit-sync.yml` (ADR 0016 decision 6, AA-994 S3s):
   per run, one token per consumer app repo (AA-Partner, AA-Booking, AA-TripPlanner-Web), Contents + Pull requests
   write, in the main-only `release` environment, used to push branch `bot/kit-sync` and open its PR, which a person
   or the orchestrating agent merges. It cannot reach AA-CIS-Infra or the root repo, so the database-rights concern
   of critic point 1 does not apply; the same key can already mint any installation token, so the narrowing in the
   workflow is the control. *(Clarified 2026-10-29, S257: the earlier wording "for another repo" contradicted ADR
   0016 decision 6, accepted the day before.)*
   **Exception, the migration-sync doorbell** *(amended 2026-10-29, S258)*: each owner repo's
   `migration-sync-wake.yml` (push to `main` touching its migrations folder, main-only `release` environment) mints a
   token for AA-CIS-Infra with **Issues write only** and posts one comment on the open Infra issue labelled
   `migration-sync-wake`. Infra's `migration-sync.yml` runs on a comment by exactly `aa-ecosys-ci-bot[bot]` on that
   issue, never reads its text, and still pulls the owners' `main` anonymously, so the no-payload rule above holds.
   Why: GitHub runs the sync's `*/10` cron best effort (once in ~6 h on 2026-10-29), which hid a hand step in the
   "no human step" path. Issues write cannot change Infra code, open or merge a PR, or dispatch a workflow, and the
   App already holds it; `repository_dispatch` (Contents write) and `workflow_dispatch` (Actions write, which would also
   let the key dispatch DB Migrate or Terraform Apply) stay out. The cron stays as the backstop.

4. **ci-bot cannot push to AA-CIS-Infra `main`.** The ruleset on `main` (AA-CIS-Infra
   `tools/github/infra-main-ruleset.json`, applied with the tech lead's login by `tools/github/db_auto_apply_gate.sh`)
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
- **Negative:** the merge conditions of decision 1 live in the workflows, not in GitHub. A leaked ci-bot key (repo
  secret `AA_CI_BOT_PRIVATE_KEY`) could open and merge **any** AA-CIS-Infra PR whose required checks are green (the
  ruleset needs 0 approvals in the dev phase), e.g. a change to `db/run_migration.py` or a `.tf` file, and the next
  auto-apply would run that runner with the migrator's rights; the byte re-check against the owner repo covers the
  SQL file, not the runner. It still cannot push to Infra `main` directly, change a file under `.github/workflows/`
  (no Workflows permission), read a secret or dispatch a workflow (no Actions permission). Open point for M3 (before
  `DB_AUTO_APPLY=true`): close this with code-owner review on every path outside `db/migrations/<owner>/` (ruleset
  `require_code_owner_review` + a CODEOWNERS file that leaves `db/migrations/` unowned), which also changes how the
  orchestrating agent merges its own Infra PRs (the tech lead's bypass, or an approval), so the tech lead decides it.
- **Cost:** 0 USD (GitHub Free, public repos).

## Alternatives considered

- **App workflows push the copy PR with a minted ci-bot token:** that token could write to Infra `main` or to the
  runner; rejected (critic point 1).
- **The agent keeps merging both PRs:** keeps two waits on every schema change (ADR 0017 Context).
- **A third App only for these merges:** a separate key with the same blast radius inside Infra and root; not worth
  the extra key while both stay within one App's narrowed tokens.
