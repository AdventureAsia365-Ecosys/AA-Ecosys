# AA-878 B1 — Secrets register (S243)

Root part of AA-878, branch `docs/aa878-secrets-register`. Companion branches:

- AA-TripPlanner-Web `fix/aa878-edge-key-from-secrets-manager` (T1): the Lambdas read the edge key
  from Secrets Manager by name, fail closed.
- AA-CIS-Infra `fix/aa878-tp-lambda-secrets-arn-only` (I2 + I3): drop the plaintext key and the
  dead Mapbox ARN from the TripPlanner Lambda env, forget the 4 orphan secrets' Terraform resources
  (removed blocks, no destroy), shrink `tf_plan_secret_arns`, and the drift checker
  `tools/secrets/register_check.py`.

## Decisions

- **YAML is the source, Markdown is its view.** `secrets-register.yaml` holds every row with the
  fields the plan listed (name, store, owner_app, owner, consumers file:line, managed_by, rotation,
  last_changed, status, notes); the Markdown tables were generated from it once. Later edits go to
  the YAML first.
- **Store vocabulary** the checker understands: `secretsmanager:acc2`, `github:<repo>`,
  `github:<repo>/<env>`, `github:org`, `vercel:<project>`, `lambda-env:<function>`. `vendor:*` rows
  are documentation only (not machine-checked).
- **Statuses beyond the plan's four** (keep / orphan-delete / pending-x1 / open-item): `planned`
  (the 5 credentials other S243 lanes add, as the task asked), `pending-removal` (a Lambda env key an
  open PR removes) and `deleted` / `removed` (kept for the deletion log). Each has a checker rule, so
  the register can reach `diff = 0` only when reality matches it.
- **Vercel and Lambda env: only secret-looking names need a row.** Both also hold plain config
  (`API_URL`, `NEXT_PUBLIC_*`, `BEDROCK_REGION`...). Registering all of them would bury the secrets.
  GitHub and Secrets Manager names are all secrets, so all need a row.
- **GitHub scopes from the S241 audit + workflow refs.** `gh secret list` is blocked for subagents,
  so the repo-vs-environment split comes from S241 (`README.md:119`: CIS env `dev` holds only
  `AWS_ROLE_ARN`) and `environment:` in the workflows on main. The main session's M0 listing
  confirms it; any mismatch shows up as `MISSING` + `UNREGISTERED` in the checker.
- **Vercel names from S241** (17/10) plus the `process.env.*` reads on main (the S242 Cognito client
  secrets). Same: M0 confirms.
- **Consumers exclude `apps/AA-CIS-App/.claude/worktrees/**` and docs**: `git grep` on `origin/main`
  of each repo with `:!docs :!**/*.md :!**/.claude/**`.
- **acc1 / acc3 not inventoried here**: the task allows read-only AWS calls with `aa365-admin` only.
  Listed as open item 9 for the main session (M0 d).

## Changed

- New `docs/security/secrets-register.yaml` (84 rows) and `docs/security/secrets-register.md`
  (summary, how to run the drift check, first run output, open items, deletion log, tables).
- No other root file. The session log, backlog row, access-review notes (M4) and the final
  `diff = 0` output come in the main session's final root PR.

## Tradeoffs

- Two files to keep in step (YAML + Markdown). Accepted: the YAML is what the checker reads; the
  Markdown is what people read. A generator script was not added to the repo to keep the root
  docs-only; regenerate the tables by hand or with a short one-off script.
- `last_changed` uses Secrets Manager `LastChangedDate`, which also moves on a tag-only update
  (`acp-*` show 15/10 from a Terraform tag re-apply). Noted on those rows.

## Should know

- **First checker run** (`--aws` + `--lambda-env`, 19/10): `diff = 7`, all expected: 4 Secrets
  Manager orphans still present (M2 deletes them), 3 Lambda env keys still present (I2 removes them).
- After M2: flip the 4 Secrets Manager rows and the 2 GitHub orphan rows to `deleted`, fill the
  deletion log. After I2 is applied: flip the 3 `pending-removal` rows to `removed`. After each
  planned credential is created: flip it to `keep`.
- **Candidate orphans found while building** (not in the M2 list): Vercel aa-cis-frontend
  `ADMIN_USERNAME`/`ADMIN_PASSWORD`/`ADMIN2_USERNAME`/`ADMIN2_PASSWORD` and `INTERNAL_API_KEY` (no
  reader in AA-CIS-App code on main), and possibly AA-CIS-App's repo-level `AWS_ROLE_ARN`. Open
  items 5 and 6.
- The root repo is **private** (`gh repo view`, 19/10; the S241 audit had listed it as public).
  The register holds names, owners and file references only, no values, but it maps where each
  credential lives: keep the repo private.
