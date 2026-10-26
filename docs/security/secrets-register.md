# Secrets register

AA-878 (S241 finding P1-2). One row per credential the ecosystem holds: where it is stored, who owns
it, who reads it, how it is managed and rotated, and what should happen to it. **Names and metadata
only — never a value.** The machine-readable twin is [`secrets-register.yaml`](secrets-register.yaml)
(same rows); edit the YAML first, then the tables here to match.

- Updated: 25/10/2026 (S250: acc2 `list-secrets` re-read, 53 names (49 live + 4 in the deletion window); new
  rows for the S250 secrets `aa-cis/dev/redis-auth` (AA-874), `tripplanner/dev/cognito-bff-key` and
  `tripplanner/dev/cognito-signup-proof-key` (AA-908), `crm/dev/mail-oauth` (AA-945), and for the S248–S249 names
  that were never registered (CRM web, CRM M2M client, six CRM e2e users, a second tenant CMS secret); AA-Partner
  GitHub rows (the portal deploy moved from AA-CIS-App, AA-979 P2a; the CIS copies deleted); TripPlanner traveller
  Vercel env names (AA-908). No `booking/dev/e2e-test-staff` secret: the second WORKFORCE E2E staff (Infra #361) signs
  in by email code only. Drift check with the AWS inventory: `diff = 0`; GitHub and Vercel listings not re-run).
  Earlier: 22/10/2026 (S247: `ROOT_REPO_DOCS_TOKEN` deleted, the Infra docs workflows use the
  `aa-ecosys-ci-bot` App token (AA-CIS-Infra #281); the three unused GitHub PATs flagged for revoke
  (pending Nghiệp); DataForSEO exposure in the now-public AA-CIS-Infra history recorded, see
  [ADR 0014](../adr/0014-repo-visibility-and-github-plan.md) amendment; no live drift check this update).
  Earlier: 20/10/2026 (S245: first drift check with all four inventories (AWS, Lambda env, GitHub per
  repo/env, Vercel names): `diff = 8` → `diff = 0`; rows flipped below; first access review
  [2026-10-20-S245](../audits/2026-10-20-S245-access-review/README.md)). Earlier: 19/10/2026 (S244: AA-816 Stage S — S1 on Production, C9 Preview credential, I6 rotation, break-glass
  rotation, AA-878 N1; X1 S20/S22 — `db_migrator` in use. acc2 `list-secrets` re-read: 33 names, 29 live + 4 deleted in
  the recovery window, 0 with rotation enabled). Earlier: S243 (X1 S18/S19, 4 orphans deleted, viewer created). Inventory: acc2 `list-secrets` (31 secrets, 0 with rotation enabled,
  0 scheduled for deletion), Lambda env keys, ECS task-definition secret refs, the `secrets.*`
  references in workflows on `main` of the four app/infra repos, and the S241 audit's GitHub +
  Vercel name lists (17/10).
- GitHub scopes (repo vs environment) and the Vercel names are confirmed by the main session's
  M0 listing (`gh secret list` per repo/env/org, Vercel env names without values); subagents cannot
  run `gh secret`.
- **DSN host (AA-829, S248):** since the AA-829 DSN switch (23/10/2026, applied and verified) every database DSN
  secret in this register (`aa-cis/dev/rds`, `aa-cis/dev/db-migrator`, `aa-cis/dev/rds-cis-app`,
  `aa-cis/dev/rds-app-user`, `booking/dev/database-url`, `tripplanner/dev/database-url`, `crm/dev/database-url`)
  names the private host **`db.dev.internal`** (Route 53 private zone `dev.internal`, CNAME to the RDS endpoint, TTL
  60 s, resolvable only inside the VPC; AA-CIS-Infra `accounts/aa365/db_dns.tf`), not the RDS endpoint. A new DSN uses
  `db.dev.internal`. `sslmode` stays `require` (the RDS certificate does not name
  `db.dev.internal`, so `verify-full` would fail). DB Migrate `set-password` refuses a role secret whose host differs
  from the master's, so the secrets move together; a restore or replacement of the instance changes the CNAME, not the
  secrets ([restore runbook](../ops/runbooks/restore-rds-pitr.md#repoint-dbdevinternal-after-a-restore)).
- Status legend: **keep** (in use) · **open-item** (in use, open finding) · **pending-x1** (consumer
  arrives with X1) · **planned** (added this session, not created yet) · **orphan-delete** (no
  consumer; DRY RUN → Nghiệp OK → delete) · **pending-removal** (plaintext/dead Lambda env key an
  open PR removes) · **deleted / removed** (kept for the log).

## Summary (25/10/2026)

| | Count |
|---|---|
| Rows | 126: 53 Secrets Manager (49 live + 0 planned + 4 deleted, in the recovery window), 41 GitHub (32 live + 9 deleted/removed), 14 Vercel (13 live + 1 planned + 0 removed), 4 Lambda env (all removed), 14 vendor |
| Changed 25/10/2026 (S250) | Secrets Manager: new `aa-cis/dev/redis-auth`, `tripplanner/dev/cognito-bff-key`, `tripplanner/dev/cognito-signup-proof-key`, `crm/dev/mail-oauth` (shell, no value until the OAuth clients exist); 10 S248–S249 names registered; `crm/dev/database-url`, `crm/dev/sentry-dsn`, `aa-cis/dev/tripplanner-revalidate-hmac`, `aa-ecosys/ops/linear-api-key` planned → keep. GitHub: AA-Partner rows (`VERCEL_TOKEN` team token `aa-partner-ci`, expires 23/04/2027; `VERCEL_PORTAL_BYPASS_SECRET` and `E2E_TENANT_API_KEY` moved from AA-CIS-App, deleted there). Vercel aa-tripplanner: `TP_SESSION_SECRET`, `TP_COGNITO_BFF_KEY`, `TP_COGNITO_SIGNUP_PROOF_KEY` |
| Drift check (S250, AWS inventory only) | **`diff = 0`** for Secrets Manager acc2 (was 17 before the update: 14 unregistered names + 3 rows still planned in the YAML although the secrets exist). GitHub and Vercel not re-listed this update (AA-Partner scopes taken from the workflows' environments) |
| Changed 22/10/2026 (S247) | GitHub AA-CIS-Infra `ROOT_REPO_DOCS_TOKEN` **deleted** (Infra docs workflows on the `aa-ecosys-ci-bot` App token, AA-CIS-Infra #281); vendor rows: three unused GitHub PATs, revoke recommended (pending Nghiệp); DataForSEO password exposed in public AA-CIS-Infra history, rotation declined for now (Nghiệp, ADR 0014 amendment). Drift check not re-run (no fresh inventories) |
| Drift check (S245, all four inventories) | **`diff = 0`** (was 8 before this update). Not checked: GitHub org secrets (the listing answers 403, no org-admin scope; no `github:org` row) |
| Orphans | 4 Secrets Manager — **deleted 19/10/2026**, recovery until 18/11 (`aa-cis/dev/api-keys`, `aa-cis/dev/acp-webhook-secret`, `aa-cis/dev/acp-partner-api`, `tripplanner/dev/mapbox-geocoding-token`); 2 GitHub — **deleted 17/10/2026** (AA-866: `VERCEL_DEPLOY_HOOK`, `ACPCORE_READ_TOKEN`), absent on 20/10; the repo-level `ADMIN_SECRET` and `AWS_ROLE_ARN` on AA-CIS-App are absent too |
| Plaintext secret in a Lambda env | none: `TRIPPLANNER_API_KEY` and the dead `MAPBOX_GEOCODING_TOKEN_ARN` left both TripPlanner Lambdas with I2 (19/10); the ops-probe `ADMIN_SECRET` left with I1 (Infra #195) |
| Planned rows | 0: the 4 planned in S243 exist now (GitHub `VERCEL_PORTAL_BYPASS_SECRET`, `E2E_TENANT_API_KEY`, env `e2e` `E2E_MAIL_ROLE_ARN`; Vercel aa-booking-admin `COGNITO_BOOKING_STAFF_CLIENT_SECRET`) and are `keep` |
| Added S245 | GitHub AA-TripPlanner-Web `AWS_DEPLOY_ROLE_ARN` (role ARN, AA-902); Secrets Manager `aa-ecosys/ops/linear-api-key` (Linear export + archive tool) |
| Rotated / revoked 20/10/2026 (S245) | local gh / MCP OAuth token (`gho_`, Nghiệp); old Mapbox geocoding token revoked in the Mapbox account (geocoding API now 401) |
| Rotated 19/10/2026 (S244) | `aa-cis/dev/admin-secret` (I6), `aa-identity/dev/breakglass` (password + TOTP), `aa-cis/dev/db-migrator` (value first written by script, X1 S20) |
| Rotation enabled in Secrets Manager | 0 of 30 live |

## How to run the drift check

The checker lives in AA-CIS-Infra: `tools/secrets/register_check.py` (stdlib + PyYAML). It reads
only inventories you collected (names and dates), never calls `GetSecretValue`, prints names only,
and exits 0 when `diff = 0`, 1 on any difference, 2 on bad input. Collect the inventories into the
session scratch folder (single-line commands):

```bash
D=/home/nghiep/projects/AA-Ecosys/.tmp-session/<session>/secrets-inventory; mkdir -p $D/gh
aws secretsmanager list-secrets --include-planned-deletion --profile aa365-admin --region us-west-1 --output json > $D/list-secrets.json
for f in $(aws lambda list-functions --profile aa365-admin --region us-west-1 --query 'Functions[].FunctionName' --output text); do echo "\"$f\": $(aws lambda get-function-configuration --function-name $f --profile aa365-admin --region us-west-1 --query 'keys(Environment.Variables || `{}`)' --output json),"; done | sed '$ s/,$//' | { echo '{'; cat; echo '}'; } > $D/lambda-env.json
for r in AA-CIS-App AA-Booking AA-TripPlanner-Web AA-CIS-Infra AA-Ecosys; do gh secret list -R AdventureAsia365-Ecosys/$r --json name,updatedAt > $D/gh/$r.json; done
gh secret list -R AdventureAsia365-Ecosys/AA-CIS-App --env dev --json name,updatedAt > $D/gh/AA-CIS-App@dev.json
gh secret list -R AdventureAsia365-Ecosys/AA-CIS-Infra --env prod --json name,updatedAt > $D/gh/AA-CIS-Infra@prod.json
gh secret list --org AdventureAsia365-Ecosys --json name,updatedAt > $D/gh/org.json
```

Add one `<repo>@<env>.json` per environment that
`gh api repos/AdventureAsia365-Ecosys/<repo>/environments` lists (e.g. `AA-CIS-App@e2e.json` once
AA-816 creates it). For Vercel, save the env names of each project (Vercel MCP `filter_project_envs`,
no decrypt) as `{"aa-cis-frontend": [{"key": "...", "target": ["..."]}], ...}` in `$D/vercel.json`.
Then, from the AA-CIS-Infra checkout:

```bash
python3 tools/secrets/register_check.py --register /home/nghiep/projects/AA-Ecosys/docs/security/secrets-register.yaml --aws $D/list-secrets.json --gh $D/gh --vercel $D/vercel.json --lambda-env $D/lambda-env.json
```

Rules it applies:

- Every Secrets Manager and GitHub secret name must have a row (`UNREGISTERED` otherwise).
- Vercel and Lambda env also hold plain config, so only secret-looking names (SECRET, KEY, TOKEN,
  PASSWORD, CREDENTIAL; not `*_ARN`/`*_NAME`/`*_HEADER`/`*_ID`; for Vercel not `NEXT_PUBLIC_*`)
  need a row (`UNREGISTERED` / `LAMBDA-ENV-SECRET`).
- `keep` / `open-item` / `pending-x1` rows must exist (`MISSING`, or `SCHEDULED-FOR-DELETION`).
  `planned` rows must not exist yet (`PLANNED-NOW-PRESENT`: flip them to `keep`).
  `orphan-delete` / `pending-removal` / `deleted` / `removed` rows must be gone or scheduled for
  deletion (`STILL-PRESENT`).
- Stores without an inventory, and `vendor:*` rows, are listed as "not checked".

First run (19/10/2026, `--aws` + `--lambda-env` only; GitHub and Vercel wait for M0): `diff = 7`,
exactly the work AA-878 I2 and M2 still have to do.

```text
STILL-PRESENT lambda-env:aa-tripplanner-dev-assembly MAPBOX_GEOCODING_TOKEN_ARN (register: pending-removal)
STILL-PRESENT lambda-env:aa-tripplanner-dev-assembly TRIPPLANNER_API_KEY (register: pending-removal)
STILL-PRESENT lambda-env:aa-tripplanner-dev-browse TRIPPLANNER_API_KEY (register: pending-removal)
STILL-PRESENT secretsmanager:acc2 aa-cis/dev/acp-partner-api (register: orphan-delete)
STILL-PRESENT secretsmanager:acc2 aa-cis/dev/acp-webhook-secret (register: orphan-delete)
STILL-PRESENT secretsmanager:acc2 aa-cis/dev/api-keys (register: orphan-delete)
STILL-PRESENT secretsmanager:acc2 tripplanner/dev/mapbox-geocoding-token (register: orphan-delete)
diff = 7
```

S244 run (19/10/2026, evening; `--aws` + `--lambda-env`, 8 Lambda functions; GitHub and Vercel still need the main
session's listing): before this update `UNREGISTERED secretsmanager:acc2 aa-cis/dev/admin-secret-preview`
(`diff = 1`); after it `diff = 0`. The TripPlanner Lambda env keys (`pending-removal` rows) are already gone, so those
rows can flip to `removed`.

The "register matches" bullet of AA-878 is met when a fresh run with all four inventories prints
`diff = 0`: I2 applied, M2 deletions done and those rows flipped to `deleted`/`removed`, the
planned rows created and flipped to `keep`. Run it again at every quarterly access review.

**S245 run (20/10/2026), all four inventories.** Inputs, names only: AWS `list-secrets` (33 names) and Lambda env
keys (8 functions) collected read-only on 20/10; GitHub secret names per repo, per environment (AA-CIS-App
`dev`/`e2e`/`Preview`/`prod`/`Production`/`staging`, AA-Booking `dev`/`Preview`/`Production`, AA-TripPlanner-Web
`Preview`/`Production`, AA-CIS-Infra `dev`/`prod`/`staging`; AA-Ecosys has none) listed by the main session on
20/10; Vercel env names of `aa-cis-frontend`, `aa-tripplanner` and `aa-booking-admin` (Vercel MCP, no decrypt; the
team has no other project). The org-level listing answered 403 (the `gho_` token has no org-admin scope), so
`github:org` is not checked; the register has no org row. Dependabot secret lists are empty in all five repos.

Before the S245 update:

```text
MISSING github:AA-Booking VERCEL_AUTOMATION_BYPASS_SECRET (register: keep)
MISSING github:AA-CIS-App AWS_ROLE_ARN (register: open-item)
MISSING github:AA-TripPlanner-Web VERCEL_AUTOMATION_BYPASS_SECRET (register: keep)
PLANNED-NOW-PRESENT github:AA-CIS-App E2E_TENANT_API_KEY (set status: keep)
PLANNED-NOW-PRESENT github:AA-CIS-App VERCEL_PORTAL_BYPASS_SECRET (set status: keep)
PLANNED-NOW-PRESENT github:AA-CIS-App/e2e E2E_MAIL_ROLE_ARN (set status: keep)
PLANNED-NOW-PRESENT vercel:aa-booking-admin COGNITO_BOOKING_STAFF_CLIENT_SECRET (set status: keep)
UNREGISTERED github:AA-TripPlanner-Web AWS_DEPLOY_ROLE_ARN
diff = 8
```

After it (31 stores checked: `secretsmanager:acc2`, 19 GitHub repo/env scopes, 3 Vercel projects, 8 Lambda functions):

```text
not checked (no inventory or documentation only): 12 stores
diff = 0
```

Row changes: the 4 planned rows → `keep`; AA-CIS-App repo-level `AWS_ROLE_ARN` → `removed` (open item 6 closed);
Booking and TripPlanner `VERCEL_AUTOMATION_BYPASS_SECRET` → `removed` (absent; their workflows treat it as optional);
`VERCEL_DEPLOY_HOOK` and `ACPCORE_READ_TOKEN` `orphan-delete` → `deleted` (17/10, AA-866: absent, so the checker had
nothing to flag, but the rows were stale); the three TripPlanner Lambda `pending-removal` rows → `removed`; new
`AWS_DEPLOY_ROLE_ARN` row; `last_changed` filled from the GitHub `updatedAt` where it was `TBD-M0`.

## Open items

1. ~~**Vercel Preview `ADMIN_SECRET`** (the god-key on every preview) → a low-privilege credential.~~
   **Closed 19/10/2026 (S244, AA-816 C9 + I6).** CIS #858: the API admin-secret guards accept a verified Cognito
   principal; the new `aa-cis/dev/admin-secret-preview` (read by the API by the code-constant name in
   `api/core/staff_credential.py`) gives a principal capped at viewer, never the machine. Vercel Preview
   `ADMIN_SECRET` holds that value; preview smoke in viewer mode 59 passed / 7 skipped (CIS #859). The main
   `aa-cis/dev/admin-secret` was rotated the same day (new → 200, old → 403); its copies are now only GitHub
   AA-CIS-App env `dev` and Vercel Production.
2. **CIS task role `secretsmanager:GetSecretValue` on `*`** (AA-CIS-Infra `modules/ecs/main.tf:171-181`):
   partly closed by X1 S19 (Infra #204, 19/10/2026): an explicit Deny now covers the RDS master,
   `aa-cis/dev/db-migrator`, `booking/*` and `tripplanner/*`. The Allow is still `*`, so the CIS containers can
   still read every other secret (E2E secrets included). The break-glass secret is protected by its
   resource-policy Deny. Narrowing the Allow to a list stays a follow-up (ask Nghiệp first).
3. **0 rotations configured** (29 live Secrets Manager secrets, `RotationEnabled` null on all). Manual
   rotation dates are the `last_changed` column; vendor rotation dates are `TBD-Nghiep`.
4. **Full-admin E2E accounts** (narrowed S244): AA-878 N1 is done — GitHub `E2E_ADMIN_*` hold the viewer
   account, so `e2e-claude-code` is no longer on every PR preview; with the Preview credential a legacy admin
   login on a Preview reaches only viewer rights. Still open: disable `e2e-claude-code-2` (decision D4 / cutover
   N-F, needs an owner Cognito session on the Staff page, Nghiệp); disable `e2e-claude-code` at S2 (the API
   `/auth/admin-login` answers until then).
5. **Vercel aa-cis-frontend `ADMIN_PASSWORD` / `ADMIN2_PASSWORD` (and their usernames) and
   `INTERNAL_API_KEY`**: no reader in AA-CIS-App code on `main`. Confirm and delete by hand (not in
   the M2 list yet). All still present on 20/10 (S245). Also on 20/10: Vercel flags `SENTRY_AUTH_TOKEN`,
   `ADMIN2_PASSWORD` and aa-tripplanner `TRIPPLANNER_API_KEY` (Development + Preview) as `readable-secret`
   (type Encrypted, not Sensitive); re-create them as Sensitive by hand (access review F-5).
6. ~~**AA-CIS-App repo-level `AWS_ROLE_ARN`**~~ **Closed 20/10/2026 (S245):** absent in the GitHub listing; the
   env `dev` copy is the only one.
7. **Repo-level secrets readable from any branch** (S241 P0-1): `VERCEL_TOKEN` on AA-CIS-App, AA-Booking and
   AA-TripPlanner-Web; `TF_VAR_DB_PASSWORD` on AA-CIS-Infra. The repo-level `ADMIN_SECRET` is gone (S244); the
   rotated copy lives only in env `dev`. `E2E_ADMIN_*` stay repo-level but hold only the viewer account now.
   ~~`ROOT_REPO_DOCS_TOKEN` is a personal access token~~ deleted 22/10/2026 (S247): the Infra docs workflows
   use the `aa-ecosys-ci-bot` App token (AA-CIS-Infra #281).
8. **Terraform state still holds values**: `random_password.tripplanner_api_key` (by design: the
   secret is the source of truth) and the Cognito app client secrets. The ops-probe admin secret
   left state with I1.
9. **acc1 / acc3 secrets** (`pqnghiep-admin`, `nghiep_aa365`): not inventoried yet. The main session
   lists their names (M0 d) and adds rows; AA-517 cleaned 20 strays from acc1 on 02/09.
10. **CI apply role reads every secret** (S245 access review F-7): `aa-cis-infra-tf-apply` carries the AWS
    managed policy `SecretsManagerReadWrite` and its boundary does not limit `secretsmanager`, so any AA-CIS-Infra
    workflow on `main` in env `prod` can read (and write) the RDS master, `aa-cis/dev/db-migrator`, `booking/*`,
    `tripplanner/*` and every other secret. It also holds `PutResourcePolicy` / `DeleteResourcePolicy`, so it can
    lift the break-glass resource-policy Deny (that call is alerted). Follow-up under AA-806: replace the managed
    policy with a named-ARN grant (as `tf_plan_secret_arns` does for the plan role) or add a `GetSecretValue` Deny
    on the master / `booking/*` / `tripplanner/*` to the boundary (bootstrap object: applied locally with MFA, ask
    Nghiệp first, IAM); add a `main` branch policy on env `prod` (AA-866).
11. **Infra main lost the S250 Terraform for four secrets (S250 close):** AA-CIS-Infra `main` af8ac53 (#380, schema
    drift report) was squashed from a stale branch and dropped `accounts/aa365/crm_mail.tf` (`crm/dev/mail-oauth`),
    the traveller BFF secrets in `identity.tf` (`tripplanner/dev/cognito-bff-key`, `cognito-signup-proof-key`) and the
    Redis AUTH wiring in `modules/ecs` (`aa-cis/dev/redis-auth` stays in `modules/elasticache`), among other files.
    The secrets exist live and in state. Restore the files from 5bdde4d before any `terraform-apply` from `main`;
    a plan must then show no changes.

## Who can read the RDS master (X1 S19)

Since 19/10/2026 (S243, Infra #203 + #204, AA-860; migrator rows updated for X1 S22, Infra #225, S244):

| Principal | Reads `aa-cis/dev/rds`? | Why |
|---|---|---|
| CIS api + worker containers (task role) | **No** — explicit Deny, verified 20/20 AccessDenied after IAM propagation (~8 min) | X1 S19 Deny on `aa-cis/<env>/rds-??????` (master only; `rds-app-user` / `rds-cis-app` stay readable) |
| CIS api + worker `DATABASE_URL` | No — now `aa-cis/dev/rds-cis-app` (`cis_app`) | X1 S18 |
| ECS execution role | No longer for the migrator `DATABASE_URL`: it injects `aa-cis/dev/db-migrator` since X1 S22 | Infra #225 |
| DB Migrate / Schema Dump / isolation probe / Tour Liveness Gate (migrator task) | Only inside the task (`MASTER_SECRET`, migrator task role) for `roles/` files, `set-password` and `run-script` (the nightly DB Tour Liveness Gate is one READ_ONLY run-script, AA-986); every other file runs with the `db_migrator` login | X1 S22; probe 58/58 after S22, `sessions.master_break_glass_only` pass |
| Humans with the MFA admin profile (`aa365-admin`) | Yes | Break-glass only (DM-8.9); prefer DB Migrate `mode=run-script` |
| Agent ECS exec scripts | **No** | They use the container `DATABASE_URL` (`cis_app`); see `docs/ops/runbooks/ecs-exec-s3-mediated.md` |
| CI role `aa-cis-infra-tf-apply` (any AA-CIS-Infra workflow on `main` in env `prod`: terraform-apply, db-migrate, db-schema-dump, db-isolation-probe) | **Yes** — and every other secret, `booking/*` and `tripplanner/*` included | AWS managed policy `SecretsManagerReadWrite` (one of the ten on the apply role, AA-806); the `tf_apply_boundary` boundary starts with Allow `*` and none of its Deny statements cover `secretsmanager`. Env `prod` has no GitHub protection rule; the only gate is the OIDC `ref = refs/heads/main` claim (AA-866). Open item 10, access review F-7 |

The same Deny covers `aa-cis/dev/db-migrator`, `booking/*` and `tripplanner/*` for the CIS task role. It does
not apply to the apply role above.

## Deletion log

Filled in by AA-878 step M2: DRY RUN list → Nghiệp OK → `delete-secret --recovery-window-in-days 30`
→ independent re-list. Restore within 30 days:
`aws secretsmanager restore-secret --secret-id <name> --profile aa365-admin --region us-west-1`.

| Date | Store | Name | Evidence of no consumer | Command / who | Recovery until |
|---|---|---|---|---|---|
| 2026-10-19 | Secrets Manager acc2 | `aa-cis/dev/api-keys` | No reader on main of any repo (register row, M2 DRY RUN); Terraform-managed ones forgotten from state first (Infra #207) | `delete-secret --recovery-window-in-days 30` (main session, Nghiệp OK S243) | 2026-11-18 |
| 2026-10-19 | Secrets Manager acc2 | `aa-cis/dev/acp-webhook-secret` | No reader on main of any repo (register row, M2 DRY RUN); Terraform-managed ones forgotten from state first (Infra #207) | `delete-secret --recovery-window-in-days 30` (main session, Nghiệp OK S243) | 2026-11-18 |
| 2026-10-19 | Secrets Manager acc2 | `aa-cis/dev/acp-partner-api` | No reader on main of any repo (register row, M2 DRY RUN); Terraform-managed ones forgotten from state first (Infra #207) | `delete-secret --recovery-window-in-days 30` (main session, Nghiệp OK S243) | 2026-11-18 |
| 2026-10-19 | Secrets Manager acc2 | `tripplanner/dev/mapbox-geocoding-token` | No reader on main of any repo (register row, M2 DRY RUN); Terraform-managed ones forgotten from state first (Infra #207) | `delete-secret --recovery-window-in-days 30` (main session, Nghiệp OK S243) | 2026-11-18 (the token itself revoked at Mapbox 20/10, so a restore gives a dead value) |
| 2026-10-17 | GitHub AA-CIS-App (repo) | `VERCEL_DEPLOY_HOOK` | No workflow on main references it (AA-866) | deleted under AA-866 (main session); absent in the S245 listing 20/10 | none (GitHub secrets have no recovery) |
| 2026-10-17 | GitHub AA-CIS-App (repo) | `ACPCORE_READ_TOKEN` | No workflow on main references it; AA-ACP-Core archived | deleted under AA-866 (main session); absent in the S245 listing 20/10. The PAT behind it still needs revoking (Nghiệp) | none |
| 2026-10-25 | GitHub AA-CIS-App (repo) | `VERCEL_PORTAL_BYPASS_SECRET` | No workflow on CIS main references it after the portal moved to AA-Partner (AA-979 P2a-3, CIS #997) | deleted by the main session (S250); the value now lives in AA-Partner | none (GitHub secrets have no recovery) |
| 2026-10-25 | GitHub AA-CIS-App (repo) | `E2E_TENANT_API_KEY` | Same: the portal smoke runs from AA-Partner (AA-979 P2a-3) | deleted by the main session (S250); copy kept in AA-Partner | none (GitHub secrets have no recovery) |

## Register

### Secrets Manager, acc2 (005097885195, us-west-1) (53)

| Name | Owner app | Consumers (main) | Managed by | Rotation | Last changed | Status | Notes |
|---|---|---|---|---|---|---|---|
| `aa-cis/dev/rds` | cis | migrator task, read in the task as MASTER_SECRET for roles/ files, set-password, run-script only, incl. the nightly DB Tour Liveness Gate run-script (AA-986) (AA-CIS-Infra db/run_migration.py:204; not injected since X1 S22, Infra #225); AA-CIS-App scripts/link_staff_identity.py:65, services/acp_produce/sweeper_lambda.py:37 (default; Lambda not deployed); humans with the MFA admin profile (break-glass, DM-8.9) | cli (read by data source module.secrets.data.aws_secretsmanager_secret.rds) | none | 2026-07-07 | **keep** | Master DSN (aa_cis_admin). No longer the CIS runtime login since X1 S18 (19/10/2026); the CIS task role is denied it since X1 S19; DB Migrate logs in as db_migrator since X1 S22. Also readable by the CI apply role aa-cis-infra-tf-apply (SecretsManagerReadWrite; open item 10). See "Who can read the RDS master (X1 S19)". |
| `aa-ecosys/ops/linear-api-key` | ecosystem | AA-Ecosys `tools/linear/linear_export.py` (orchestrating session, MFA admin profile) | cli (by hand, Nghiệp) | TBD-Nghiep | 2026-10-20 | **keep** | Linear personal API key (S245): export closed issues to `docs/linear-export/`, then archive via the GraphQL API (Free plan, no manual archive in the UI). Created 20/10/2026 (S245). |
| `aa-cis/dev/dataforseo` | cis | ECS api + worker DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD (modules/ecs/main.tf:509-510, :708-709) | cli (data source module.secrets.data.aws_secretsmanager_secret.dataforseo) | none | 2026-07-07 | **keep** | Vendor DataForSEO login/password (JSON). |
| `aa-cis/dev/acp-partner-api` | cis | — | terraform module.secrets.aws_secretsmanager_secret.acp_partner_api (forgotten by AA-878 I2, removed block) | none | 2026-10-15 | **deleted** | Placeholder of the retired ACP v1 partner path. No reader on main of any repo; CloudTrail since 18/10: only the plan role (refresh). LastChangedDate 15/10 is a Terraform tag re-apply, not a value change. Deleted 19/10/2026 (S243), recovery until 18/11/2026. |
| `aa-cis/dev/acp-webhook-secret` | cis | — | terraform module.secrets.aws_secretsmanager_secret.acp_webhook_secret (forgotten by AA-878 I2, removed block) | none | 2026-10-15 | **deleted** | Placeholder of the retired ACP v1 webhook HMAC. No reader on main; CloudTrail since 18/10: only the plan role. Deleted 19/10/2026 (S243), recovery until 18/11/2026. |
| `aa-cis/dev/admin-secret` | cis | ECS api + worker ADMIN_SECRET (modules/ecs/main.tf:502, :706); ops-probe Lambda aa-cis-dev-dfs-balance-check, read by ARN from the event secret_id (AA-CIS-Infra accounts/aa365/dfs_balance.tf:236, :270); copies: GitHub AA-CIS-App env dev ADMIN_SECRET, Vercel aa-cis-frontend ADMIN_SECRET Production only | cli (var.secret_admin_arn, terraform.tfvars) | manual (2026-10-19, AA-816 I6) | 2026-10-19 | **keep** | Main admin secret (machine callers; legacy sessions until S2). Rotated 19/10/2026 (S244, I6): new → 200, old → 403; GitHub env dev + Vercel Production copies updated; api + worker restarted. Preview holds `aa-cis/dev/admin-secret-preview` (C9). Header trust remains for it until S2. |
| `aa-cis/dev/openai-key` | cis | ECS api + worker OPENAI_API_KEY (modules/ecs/main.tf:500, :705); AA-CIS-App shared/llm_client/client.py:134 | cli (var.secret_openai_arn, terraform.tfvars) | none | 2026-08-21 | **keep** | Vendor OpenAI. |
| `aa-cis/dev/api-keys` | cis | — | cli | none | 2026-07-07 | **deleted** | APIFY_API_TOKEN placeholder; api/main.py no longer reads it (no reader on main of any repo). LastAccessedDate 2026-09-07. Deleted 19/10/2026 (S243), recovery until 18/11/2026. |
| `aa-cis/dev/e2e-test-admin` | cis | agent Booking UI checks (Booking BFF → CIS /auth/admin-login) and legacy sign-in on CIS PR previews (skill/aa-ui-verify/SKILL.md), user e2e-claude-code | cli | none | 2026-10-08 | **open-item** | Full CIS admin + Booking admin, legacy password login. Not in GitHub any more (N1 done S244). No password form on Production since S1; on a Preview it reaches only viewer rights (C9). Disable at S2. |
| `aa-cis/dev/jwt-secret` | cis | ECS api + worker JWT_SECRET (modules/ecs/main.tf:503, :707); AA-CIS-App api/routers/auth.py:34 | cli (var.secret_jwt_arn, terraform.tfvars) | none | 2026-09-01 | **keep** | HS256, one key for staff + tenant JWT (S241 P1-3). |
| `aa-cis/dev/tripplanner-revalidate-hmac` | cis | ECS api + worker, read by name aa-cis/<ENVIRONMENT>/tripplanner-revalidate-hmac at run time (AA-CIS-App services/jobs/tripplanner_purge_job.py, job `tripplanner_purge`, 10-min cache); copy: Vercel aa-tripplanner CATALOG_REVALIDATE_SECRET (AA-TripPlanner-Web frontend/app/api/revalidate/catalog/route.ts) | cli (by hand, orchestrating session) | manual (rotate both copies together) | 2026-10-24 | **keep** | AA-987: HMAC key of the signed cache purge notice `catalog.tour.lifecycle.v1` (root ADR 0015 A1). Bare string (JSON `{"secret": "..."}` also read by CIS), 32+ random bytes. Not under `tripplanner/*` (the CIS task role is denied that prefix); the task role's existing GetSecretValue covers it, no IAM change. Unset = the CIS job succeeds with `skipped: not_configured`. ~$0.40/month. Exists; flipped to keep at S250 close (AA-987 verified live). |
| `aa-cis/dev/rds-app-user` | cis | AA-CIS-App api/core/aa544_tenant_pool.py:128 (tenant pool, aa_app_user); AA-CIS-Infra db/isolation_probe.py:116, db/owners.yaml:64 | cli | none | 2026-09-10 | **keep** | DSN of the non-BYPASSRLS tenant role (AA-544). |
| `tripplanner/dev/database-url` | tripplanner | TP Lambdas browse + assembly by ARN TRIPPLANNER_DATABASE_URL_ARN (AA-CIS-Infra accounts/aa365/tripplanner.tf env; AA-TripPlanner-Web backend/shared/db.py:33); AA-CIS-Infra db/isolation_probe.py:127, db/owners.yaml:161 | terraform aws_secretsmanager_secret.tripplanner_db (value out-of-band, ignore_changes) | none | 2026-10-14 | **keep** | Read by the plan role on refresh (tf_plan_secret_arns). |
| `tripplanner/dev/api-key` | tripplanner | TP Lambdas browse + assembly, by name tripplanner/<ENVIRONMENT>/api-key (AA-TripPlanner-Web backend/shared/auth.py, AA-878 T1); copy: Vercel aa-tripplanner TRIPPLANNER_API_KEY (BFF frontend/app/api/browse/route.ts:9, trip/route.ts:15, lib/catalog.ts:46) | terraform aws_secretsmanager_secret.tripplanner_api_key + random_password.tripplanner_api_key | none | 2026-10-14 | **keep** | Edge shared secret X-TripPlanner-Key. Until AA-878 I2 is applied the value is also a plaintext Lambda env (see lambda-env rows). Still in Terraform state (random_password) by design. |
| `tripplanner/dev/mapbox-geocoding-token` | tripplanner | — | terraform aws_secretsmanager_secret.tripplanner_mapbox (forgotten by AA-878 I2, removed block) | none | 2026-10-14 | **deleted** | AA-675 extraction token; no reader since AA-712 slice 6a. A real Mapbox token (PutSecretValue 29/09). Deleted 19/10/2026 (S243), recovery until 18/11/2026. **Revoked in the Mapbox account 20/10/2026 (S245)**: the geocoding API answers 401 with it. |
| `aa-cis/dev/typesafe` | cis | AA-CIS-App shared/secrets.py:78 (Jev decide() seam, worker) | cli | none | 2026-09-29 | **keep** | Vendor Typesafe / Jev. |
| `aa-cis/dev/gdrive-photo-reader` | cis | AA-CIS-App services/photos/drive.py:83 | cli | none (decision 02/10/2026: no rotation needed) | 2026-10-01 | **keep** | Google API key (Drive API, public CON photo folders). |
| `aa-cis/dev/e2e-tenant/atlas-hearth` | cis | AA-CIS-App services/acp_shared/e2e_tenant_key_sync.py:28 (writes after key issue), task role grant AA-CIS-Infra modules/ecs/main.tf:250; agent UI verify / paid E2E runs (tenant portal API key) | cli (value kept in sync by app-runtime) | app-runtime (key re-issue) | 2026-10-15 | **keep** | Test tenant Atlas & Hearth portal API key. |
| `aa-cis/dev/e2e-tenant/terra-family` | cis | AA-CIS-App services/acp_shared/e2e_tenant_key_sync.py:28 (writes after key issue), task role grant AA-CIS-Infra modules/ecs/main.tf:250; agent UI verify / paid E2E runs (tenant portal API key) | cli (value kept in sync by app-runtime) | app-runtime (key re-issue) | 2026-10-12 | **keep** | Test tenant Terra Family Expeditions portal API key. |
| `aa-cis/dev/e2e-tenant/trail-pulse` | cis | AA-CIS-App services/acp_shared/e2e_tenant_key_sync.py:28 (writes after key issue), task role grant AA-CIS-Infra modules/ecs/main.tf:250; agent UI verify / paid E2E runs (tenant portal API key) | cli (value kept in sync by app-runtime) | app-runtime (key re-issue) | 2026-10-12 | **keep** | Test tenant Trail Pulse portal API key. |
| `aa-cis/dev/e2e-tenant/wildkind-travel` | cis | AA-CIS-App services/acp_shared/e2e_tenant_key_sync.py:28 (writes after key issue), task role grant AA-CIS-Infra modules/ecs/main.tf:250; agent UI verify / paid E2E runs (tenant portal API key) | cli (value kept in sync by app-runtime) | app-runtime (key re-issue) | 2026-10-12 | **keep** | Test tenant WildKind Travel portal API key. |
| `booking/dev/database-url` | booking | ECS aa-booking-dev-api DATABASE_URL (AA-CIS-Infra accounts/aa365/booking.tf:304); AA-CIS-Infra db/isolation_probe.py:122, db/owners.yaml:131 | terraform aws_secretsmanager_secret.booking_db (container only, value out-of-band) | none | 2026-10-14 | **keep** |  |
| `crm/dev/database-url` | crm | AA-Partner api + crm.job worker DATABASE_URL (AA-933; execution role only); AA-CIS-Infra db/isolation_probe.py (login crm_app), db/run_migration.py set-password crm_app, db/owners.yaml crm | terraform aws_secretsmanager_secret.crm_db (accounts/aa365/crm_data.tf, shell only, value out-of-band) | none | 2026-10-23 | **keep** | AA-932. DSN of crm_app (LOGIN, limit 6, schema crm). Nghiệp writes it in the Console after the apply, then DB Migrate set-password role=crm_app. CIS task role denied crm/* (DenyMasterAndOtherAppSecrets). |
| `crm/dev/sentry-dsn` | crm | ECS aa-crm-dev-api SENTRY_DSN via the task-definition `secrets` block, only while AA-CIS-Infra `crm_sentry_enabled` is true (accounts/aa365/crm_app.tf, AA-933); AA-Partner api/app/observability/sentry.py | terraform aws_secretsmanager_secret.crm_sentry_dsn (accounts/aa365/crm_app.tf, shell only, value out-of-band) | none | 2026-10-23 | **keep** | AA-933. Sentry DSN of project aa-partner-api (low sensitivity: ingest-only). Readers: the CRM execution role only; CIS task role denied crm/*. |
| `crm/dev/portal-sentry-dsn` | crm | ECS aa-crm-dev-portal SENTRY_DSN via the task-definition `secrets` block, only while AA-CIS-Infra `crm_portal_sentry_enabled` is true (accounts/aa365/crm_portal.tf, AA-979); AA-Partner portal/instrumentation.ts | terraform aws_secretsmanager_secret.crm_portal_sentry_dsn (accounts/aa365/crm_portal.tf, shell only, value out-of-band) | none | 2026-10-26 | **planned** | AA-979 P2b (S252). Sentry DSN of the Content studio (aa-partner-portal; ingest-only). Created by Infra PR-1; flip to keep after the apply. Reader: the portal execution role only. |
| `booking/dev/sentry-dsn` | booking | ECS aa-booking-dev-api SENTRY_DSN via the task-definition `secrets` block, only while AA-CIS-Infra `booking_sentry_enabled` is true (accounts/aa365/booking.tf, AA-871); AA-Booking backend/app/observability/sentry.py | terraform aws_secretsmanager_secret.booking_sentry_dsn (shell only, value out-of-band) | none | TBD-M0 | **keep** | AA-871. Sentry DSN of project aa-booking-api (low sensitivity: ingest-only). Created and wired S247 (22/10/2026); test events verified in Sentry. |
| `tripplanner/dev/sentry-dsn` | tripplanner | TP Lambdas browse + assembly, by name tripplanner/<ENVIRONMENT>/sentry-dsn at cold start (AA-TripPlanner-Web backend/shared/observability.py resolve_dsn, AA-871); grant ReadSentryDsnSecret (AA-CIS-Infra accounts/aa365/tripplanner.tf) | terraform aws_secretsmanager_secret.tripplanner_sentry_dsn (shell only, value out-of-band) | none | TBD-M0 | **keep** | AA-871. Sentry DSN of project aa-tripplanner-lambdas (low sensitivity: ingest-only). No DSN in the Lambda env. Created and wired S247 (22/10/2026); test events verified in Sentry. |
| `aa-ecosys/github/aa-agent-app-key` | ecosystem | AA-Ecosys `tools/github/as-app.sh` (orchestrating session, MFA admin profile; mints 1-hour installation tokens) | cli | manual (2026-10-22); on leak / go-live / reader leaving (ADR 0011) | 2026-10-22 | **keep** | AA-901. Private key of the GitHub App `aa-agent` (app id 5421824). The `.pem` was shredded after storing. |
| `aa-cis/dev/booking-jwt-signing-key` | cis | AA-CIS-App api/core/booking_jwt.py:49 (RS256 private key, signs Booking staff tokens; Booking verifies via the public JWKS) | cli | manual (kid + previous[] supported) | 2026-10-14 | **keep** | AA-680 Phase 2 retires this bridge (Booking accepts Cognito tokens); keep until then. |
| `aa-cis/dev/geoapify` | cis | AA-CIS-App shared/secrets.py:98 (geocoder, worker) | cli | none | 2026-10-14 | **keep** | Vendor Geoapify. |
| `acp/cms/20d07d32-ed98-405f-81d5-0c2399c9fcdf` | cis | AA-CIS-App api/routers/v1_integrations.py:261 (tenant WordPress credentials, acp/cms/{tenant_id}); task role grant modules/ecs/main.tf:220 | app-runtime | tenant (reconnect) | 2026-10-16 | **keep** | Test tenant Terra Family. Per-tenant secrets appear here as tenants connect a CMS. |
| `acp/social/20d07d32-ed98-405f-81d5-0c2399c9fcdf` | cis | AA-CIS-App api/routers/v1_integrations.py:421 (tenant Facebook Page token, acp/social/{tenant_id}); task role grant modules/ecs/main.tf:238 | app-runtime | tenant (reconnect) | 2026-10-15 | **keep** | Test tenant Terra Family. |
| `aa-cis/dev/e2e-wordpress-test` | cis | agent E2E channel tests (WordPress test site) | cli | none | 2026-10-15 | **keep** | Test-only credentials (S238). Kept on purpose at cleanup. |
| `aa-cis/dev/e2e-facebook-test` | cis | agent E2E channel tests (Facebook test Page) | cli | none | 2026-10-15 | **keep** | Test-only credentials (S238). Kept on purpose at cleanup. |
| `aa-cis/dev/e2e-test-admin-2` | cis | agent Booking maker-checker verify (user e2e-claude-code-2) | cli | none | 2026-10-16 | **open-item** | Full CIS admin + Booking checker. Decision D4 / cutover N-F (proposed: disable on the Staff page; needs an owner Cognito session, Nghiệp). Still active 19/10. |
| `aa-identity/dev/breakglass` | identity | humans only (break-glass sign-in); written by AA-CIS-Infra tools/identity/workforce_bootstrap.py breakglass-init | terraform aws_secretsmanager_secret.identity_breakglass (identity.tf:932) + resource policy identity_alerts.tf:63 (value out-of-band) | manual (2026-10-19, breakglass-init) | 2026-10-19 | **keep** | Password + TOTP seed. Resource-policy Deny for every other principal and access alarms (AA-854). Rotated 19/10/2026 (S244) after the managed-login break-glass test; breakglass-verify OK. Old TOTP seed void: Nghiệp re-adds the new one to an authenticator if wanted. |
| `aa-cis/dev/sentry-dsn-api` | cis | AA-CIS-App shared/sentry_init.py:20 | cli (tag ManagedBy=manual-AA-870) | none | 2026-10-17 | **keep** | Sentry DSN (low sensitivity: ingest-only). |
| `aa-cis/dev/rds-cis-app` | cis | ECS aa-cis-dev-api + aa-cis-dev-worker DATABASE_URL (X1 S18, Infra #203); AA-CIS-Infra db/run_migration.py:191 (set-password), db/owners.yaml:48, db/isolation_probe.py:116 | terraform aws_secretsmanager_secret.rds_cis_app (db_migrator.tf:71) | none | 2026-10-19 | **keep** | LOGIN role cis_app DSN; value generated by script at X1 S17 (S243). CIS runtime login since 19/10/2026 (api:703 / worker:260). |
| `aa-cis/dev/db-migrator` | infra | ECS aa-cis-dev-db-migrate DATABASE_URL: DB Migrate, DB Schema Dump, isolation probe (X1 S22, Infra #225; .github/scripts/migrator-task.sh:44); db/run_migration.py:207 (set-password target) | terraform aws_secretsmanager_secret.db_migrator (db_migrator.tf:78) | manual (2026-10-19, set-password) | 2026-10-19 | **keep** | LOGIN role db_migrator DSN. Value generated and written by script at X1 S20 (DB Migrate set-password run 39247263215; never shown). In use since X1 S22 (probe 58/58, run 39256408600). Denied to the CIS task role since X1 S19. |
| `aa-cis/dev/e2e-test-viewer` | cis | value mirrored in GitHub AA-CIS-App E2E_ADMIN_USERNAME / E2E_ADMIN_PASSWORD: the ui-smoke account on every PR preview, viewer mode (ui-smoke.yml:58-59; N1, S244); agent read-only checks on CIS PR previews (skill/aa-ui-verify/SKILL.md) | cli | none | 2026-10-19 | **keep** | AA-878 C1/M3: read-only viewer staff account e2e-claude-code-viewer (CIS 249 viewer role, legacy login, Preview only), no Booking access. Created S243 (password generated by script, never shown). Not a real user. CI smoke account since S244 (59 passed / 7 skipped). |
| `aa-cis/dev/admin-secret-preview` | cis | CIS API by the code-constant name PREVIEW_SECRET_NAME (AA-CIS-App api/core/staff_credential.py:48; only when AWS_EXECUTION_ENV is set, 5 min cache); copy: Vercel aa-cis-frontend ADMIN_SECRET, Preview target only | cli | none | 2026-10-19 | **keep** | AA-816 C9 (CIS #858) Preview BFF credential, created 19/10/2026 (S244, about 0.40 USD a month). A match gives a principal capped at viewer, never the machine. Separate from the main secret. Closes open item 1. |
| `aa-cis/dev/redis-auth` | cis | ECS aa-cis-dev-api + aa-cis-dev-worker REDIS_AUTH_TOKEN via the task-definition secrets block (AA-CIS-Infra modules/ecs/main.tf redis_secrets, #372; AA-CIS-App shared/cache/redis_conn.py, CIS #983) | terraform module.elasticache aws_secretsmanager_secret.redis_auth + write-only version (secret_string_wo from an ephemeral random_password; never in state) | manual (bump auth_token_version: ROTATE, redeploy, SET; Infra docs/implementation-notes/AA-874.md) | 2026-10-25 | **keep** | AA-874 (S250). AUTH token of the TLS + at-rest encrypted Valkey group aa-cis-dev-cache (Infra #354); the old plain node was destroyed (Infra #373). Read by the CIS execution role only. Note (S250 close): AA-CIS-Infra main af8ac53 (#380) dropped this Terraform from main by mistake (stale squash); the resource exists live and in state. Restore the file before any apply from main. |
| `tripplanner/dev/cognito-bff-key` | tripplanner | WAF web ACL of the EXTERNAL pool: per-traveller rate rule keyed on header x-aa-traveller-bff (AA-CIS-Infra accounts/aa365/identity.tf, #374); copy: Vercel aa-tripplanner TP_COGNITO_BFF_KEY (AA-TripPlanner-Web frontend/lib/authRequest.ts) | terraform aws_secretsmanager_secret.identity_traveller_bff[0] + version from random_password.identity_traveller_bff[0] (value in state) | manual (-replace=random_password.identity_traveller_bff[0], then update the Vercel env) | 2026-10-25 | **keep** | AA-908 (S250). Marks the TripPlanner BFF's Cognito API calls so the WAF counts them per traveller, not per Vercel egress IP. Note (S250 close): AA-CIS-Infra main af8ac53 (#380) dropped this Terraform from main by mistake (stale squash); the resource exists live and in state. Restore the file before any apply from main. |
| `tripplanner/dev/cognito-signup-proof-key` | tripplanner | EXTERNAL pre sign-up trigger, SIGNUP_PROOF_SECRET_ID (AA-CIS-Infra lambda_src/identity_triggers/external.py, #374); copy: Vercel aa-tripplanner TP_COGNITO_SIGNUP_PROOF_KEY (signs ValidationData bff_proof on each SignUp) | terraform aws_secretsmanager_secret.identity_traveller_signup_proof[0] + version (value in state) | manual (replace the random_password, then update the Vercel env) | 2026-10-25 | **keep** | AA-908 (S250). HMAC key of the BFF sign-up proof: only the TripPlanner BFF may sign travellers up natively (email code, no traveller passwords; ADR 0006 decisions 1 and 4). Note (S250 close): AA-CIS-Infra main af8ac53 (#380) dropped this Terraform from main by mistake (stale squash); the resource exists live and in state. Restore the file before any apply from main. |
| `crm/dev/mail-oauth` | crm | ECS aa-crm-dev-api MAIL_OAUTH, mapped only while crm_mail_oauth_enabled is true (AA-CIS-Infra accounts/aa365/crm_mail.tf + crm_app.tf, #375; AA-Partner api/app/settings.py) | terraform aws_secretsmanager_secret.crm_mail_oauth (accounts/aa365/crm_mail.tf, shell only, value out-of-band) | TBD-Nghiep | 2026-10-25 | **keep** | AA-945 (S250). JSON google_client_id, google_client_secret, ms_client_id, ms_client_secret: AA's own OAuth clients for the agencies' Gmail / Microsoft 365 send-as. Shell without a value until Nghiep creates the two OAuth clients (human step; AA-945 stays In Progress); crm_mail_oauth_enabled stays false until then (a task whose valueFrom secret has no value fails to start). Note (S250 close): AA-CIS-Infra main af8ac53 (#380) dropped this Terraform from main by mistake (stale squash); the resource exists live and in state. Restore the file before any apply from main. |
| `aa-crm/dev/m2m-booking-client` | crm | ECS aa-crm-dev-api M2M_CLIENT (AA-CIS-Infra accounts/aa365/crm_app.tf; AA-Partner api/app/cis/m2m.py); crm_membership_pull asks for scope cis.tenant/read with it (AA-978) | terraform aws_secretsmanager_secret.m2m_crm_client (accounts/aa365/identity_m2m.tf, container only, value out-of-band) | manual (re-issue the M2M app client secret) | 2026-10-25 | **keep** | AA-972/AA-976 (S248-S249): JSON client_id, client_secret, token_url, scopes of the CRM's M2M app client. S250 (AA-978) added cis.tenant/read to its scopes (value rewritten by the orchestrator, not printed). |
| `crm/dev/web` | crm | ECS aa-crm-dev-web (CRM web BFF), execution role aa-crm-dev-web-ecs-execution-role (AA-CIS-Infra accounts/aa365/crm_web.tf); written by AA-CIS-Infra tools/identity/crm_dev_identity.py; AA-979: ECS aa-crm-dev-portal execution role, `session_secret` only, to read the CRM web session on the agency host (IAM cannot scope a JSON key) | terraform aws_secretsmanager_secret.crm_web (accounts/aa365/crm_web.tf, shell only, value out-of-band) | manual (crm_dev_identity.py re-writes it) | 2026-10-24 | **keep** | AA-935 (S249): JSON cognito_client_secret, session_secret of the CRM web on the partner pool. |
| `crm/dev/e2e-test-crm/harbour-lights-owner` | crm | AA-Partner e2e/helpers/signin.ts (E2E Dev, Playwright); written by AA-CIS-Infra tools/identity/crm_dev_identity.py | cli (tools/identity/crm_dev_identity.py) | manual (crm_dev_identity.py) | 2026-10-24 | **keep** | AA-939 (S249): sign-in material of the synthetic partner-pool e2e user e2e-test-crm-harbour-lights-owner (synthetic agency, MFA). Test-only. |
| `crm/dev/e2e-test-crm/sen-vang-agent` | crm | AA-Partner e2e/helpers/signin.ts (E2E Dev, Playwright); written by AA-CIS-Infra tools/identity/crm_dev_identity.py | cli (tools/identity/crm_dev_identity.py) | manual (crm_dev_identity.py) | 2026-10-24 | **keep** | AA-939 (S249): sign-in material of the synthetic partner-pool e2e user e2e-test-crm-sen-vang-agent (synthetic agency, MFA). Test-only. |
| `crm/dev/e2e-test-crm/sen-vang-assistant` | crm | AA-Partner e2e/helpers/signin.ts (E2E Dev, Playwright); written by AA-CIS-Infra tools/identity/crm_dev_identity.py | cli (tools/identity/crm_dev_identity.py) | manual (crm_dev_identity.py) | 2026-10-24 | **keep** | AA-939 (S249): sign-in material of the synthetic partner-pool e2e user e2e-test-crm-sen-vang-assistant (synthetic agency, MFA). Test-only. |
| `crm/dev/e2e-test-crm/sen-vang-owner` | crm | AA-Partner e2e/helpers/signin.ts (E2E Dev, Playwright); written by AA-CIS-Infra tools/identity/crm_dev_identity.py | cli (tools/identity/crm_dev_identity.py) | manual (crm_dev_identity.py) | 2026-10-24 | **keep** | AA-939 (S249): sign-in material of the synthetic partner-pool e2e user e2e-test-crm-sen-vang-owner (synthetic agency, MFA). Test-only. |
| `crm/dev/e2e-test-crm/southern-cross-agent` | crm | AA-Partner e2e/helpers/signin.ts (E2E Dev, Playwright); written by AA-CIS-Infra tools/identity/crm_dev_identity.py | cli (tools/identity/crm_dev_identity.py) | manual (crm_dev_identity.py) | 2026-10-24 | **keep** | AA-939 (S249): sign-in material of the synthetic partner-pool e2e user e2e-test-crm-southern-cross-agent (synthetic agency, MFA). Test-only. |
| `crm/dev/e2e-test-crm/southern-cross-owner` | crm | AA-Partner e2e/helpers/signin.ts (E2E Dev, Playwright); written by AA-CIS-Infra tools/identity/crm_dev_identity.py | cli (tools/identity/crm_dev_identity.py) | manual (crm_dev_identity.py) | 2026-10-24 | **keep** | AA-939 (S249): sign-in material of the synthetic partner-pool e2e user e2e-test-crm-southern-cross-owner (synthetic agency, MFA). Test-only. |
| `acp/cms/692a3214-5cc2-46c6-a5ca-265389747269` | cis | AA-CIS-App api/routers/v1_integrations.py (tenant CMS credentials, acp/cms/{tenant_id}); task role grant modules/ecs/main.tf | app-runtime | tenant (reconnect) | 2026-10-20 | **keep** | Second test tenant CMS connection (created 20/10/2026 by the app). Per-tenant secrets appear here as tenants connect a CMS; first registered at S250 close. |

### GitHub Actions secrets (41)

| Name | Store | Owner app | Consumers (main) | Rotation | Status | Notes |
|---|---|---|---|---|---|---|
| `ADMIN_SECRET` | `github:AA-CIS-App` | cis | — | none | **removed** | Repo-level copy of the main admin secret (S241 P0-1). Confirmed absent on 19/10/2026 (S244, `gh secret list`); the only GitHub copy is environment `dev` (next row). |
| `ADMIN_SECRET` | `github:AA-CIS-App/dev` | cis | AA-CIS-App .github/workflows/deploy-dev.yml:51, :234 (jobs with environment: dev) | manual (copy of aa-cis/dev/admin-secret, 2026-10-19) | **keep** | Deploy Dev pre-deploy gate + post-deploy smoke. Updated with AA-816 I6 (S244). |
| `AWS_REGION` | `github:AA-CIS-App` | cis | deploy-dev.yml:28, :73, :109; eval-regression.yml:31 | none | **keep** | Not a secret (S241 E12: move to a variable). |
| `AWS_ROLE_ARN` | `github:AA-CIS-App` | cis | — | none | **removed** | Repo-level legacy value for the retired aa-cis-dev-role. Absent in the S245 listing (20/10/2026); the env `dev` copy is the only one. Open item 6 closed. |
| `AWS_ROLE_ARN` | `github:AA-CIS-App/dev` | cis | deploy-dev.yml:72, :108; eval-regression.yml:43 (jobs with environment: dev) | none | **keep** | aa-cis-dev-app-deploy role ARN (not a secret). |
| `ECR_REGISTRY` | `github:AA-CIS-App` | cis | deploy-dev.yml:29 | none | **keep** | Not a secret (move to a variable). |
| `ECR_REPOSITORY` | `github:AA-CIS-App` | cis | deploy-dev.yml:30 | none | **keep** | Not a secret (move to a variable). |
| `ECS_CLUSTER` | `github:AA-CIS-App` | cis | deploy-dev.yml:31; eval-regression.yml:32 | none | **keep** | Not a secret (move to a variable). |
| `ECS_SERVICE` | `github:AA-CIS-App` | cis | deploy-dev.yml:32, :118; eval-regression.yml:33 | none | **keep** | Not a secret (move to a variable). |
| `E2E_ADMIN_USERNAME` | `github:AA-CIS-App` | cis | ui-smoke.yml:58 | none | **keep** | Since S244 (AA-878 N1) the viewer account e2e-claude-code-viewer; was e2e-claude-code (full admin). Preview smoke in viewer mode 59 passed / 7 skipped. Still repo-level (item 7), viewer-only. |
| `E2E_ADMIN_PASSWORD` | `github:AA-CIS-App` | cis | ui-smoke.yml:59 | none | **keep** | See E2E_ADMIN_USERNAME (N1 done S244: value from aa-cis/dev/e2e-test-viewer). |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | `github:AA-CIS-App` | cis | ui-smoke.yml:57; vercel-deploy.yml:161 | none | **keep** | Vercel deployment-protection bypass for aa-cis-frontend previews. |
| `VERCEL_TOKEN` | `github:AA-CIS-App` | cis | vercel-deploy.yml:83, :132 | TBD-Nghiep | **keep** | Vendor Vercel token, preview + production in one job (S241 P0-1). |
| `VERCEL_DEPLOY_HOOK` | `github:AA-CIS-App` | cis | — | none | **deleted** | Deleted 17/10/2026 (AA-866); absent in the S245 listing. Stale aa-296/299/300 branches still name it in ci.yml but can no longer use it. |
| `ACPCORE_READ_TOKEN` | `github:AA-CIS-App` | cis | — | none | **deleted** | PAT for the archived AA-ACP-Core repo. Secret deleted 17/10/2026 (AA-866); absent in the S245 listing. The PAT itself still needs revoking in GitHub settings (Nghiệp; not the `gho_` token rotated in S245). |
| `VERCEL_PORTAL_BYPASS_SECRET` | `github:AA-CIS-App` | cis | ui-smoke-portal.yml:58; vercel-deploy-portal.yml:171 | none | **deleted** | AA-885: bypass secret of the Vercel project aa-cis-portal, set 19/10. The S245 Vercel listing shows no aa-cis-portal project in the team (access review F-6). Deleted 25/10/2026 (S250, AA-979 P2a-3, CIS #997): the portal deploys from AA-Partner (row below). |
| `E2E_TENANT_API_KEY` | `github:AA-CIS-App` | cis | ui-smoke-portal.yml:61 (portal smoke) | manual (copy of an aa-cis/dev/e2e-tenant/* key) | **deleted** | AA-885: test tenant portal API key for the portal smoke, set 19/10. Deleted 25/10/2026 (S250, AA-979 P2a-3, CIS #997): the portal deploys from AA-Partner (row below). |
| `E2E_MAIL_ROLE_ARN` | `github:AA-CIS-App/e2e` | cis | e2e-cognito.yml:48 (environment e2e) | none | **keep** | AA-816 E1: role ARN (not a secret value) of the SES e2e mailbox reader, set 19/10 in env `e2e` (branch policy). |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | `github:AA-Booking` | booking | AA-Booking .github/workflows/vercel-deploy.yml:161 (optional) | none | **removed** | Absent in the S245 listing (repo + envs). The workflow only logs the status code without it; re-add and flip to keep if wanted. AWS deploy settings are vars.*, not secrets. |
| `VERCEL_TOKEN` | `github:AA-Booking` | booking | AA-Booking vercel-deploy.yml:83, :132 | TBD-Nghiep | **keep** | Vendor Vercel token. |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | `github:AA-TripPlanner-Web` | tripplanner | AA-TripPlanner-Web .github/workflows/vercel-deploy.yml:161 (optional) | none | **removed** | Absent in the S245 listing (repo + envs). Optional in the workflow; re-add and flip to keep if wanted. |
| `VERCEL_TOKEN` | `github:AA-TripPlanner-Web` | tripplanner | AA-TripPlanner-Web vercel-deploy.yml:83, :132 | TBD-Nghiep | **keep** | Vendor Vercel token. |
| `AWS_DEPLOY_ROLE_ARN` | `github:AA-TripPlanner-Web` | tripplanner | AA-TripPlanner-Web deploy-lambdas.yml:59, :69 | none | **keep** | Lambda deploy role ARN (AA-902), a repo secret so the public repo holds no ARN; not a secret value. Added S245 (was UNREGISTERED). |
| `AWS_ROLE_ARN` | `github:AA-CIS-Infra` | infra | AA-CIS-Infra .github/workflows/terraform-plan.yml:27 (no environment) | none | **keep** | aa-cis-infra-tf-plan role ARN (not a secret). |
| `AWS_ROLE_ARN` | `github:AA-CIS-Infra/prod` | infra | terraform-apply.yml:37; db-migrate.yml:206; db-schema-dump.yml:90; db-isolation-probe.yml:79 (environment: prod) | none | **keep** | aa-cis-infra-tf-apply role ARN (not a secret). Env `prod` has no GitHub protection rule; the OIDC trust requires `refs/heads/main` (access review F-7). The role reads every Secrets Manager secret (open item 10). |
| `AWS_REGION` | `github:AA-CIS-Infra` | infra | terraform-apply.yml:38, :53 | none | **keep** | Not a secret. |
| `TF_STATE_BUCKET` | `github:AA-CIS-Infra` | infra | terraform-apply.yml:51; terraform-plan.yml:41 | none | **keep** | Not a secret. |
| `TF_VAR_DB_PASSWORD` | `github:AA-CIS-Infra` | infra | terraform-apply.yml:29; terraform-plan.yml:50 | none | **open-item** | RDS master password, repo-level (S241 E12: move into a protected env or drop once RDS manages it). S240: printed once in a local transcript; decision: rotate before prod. |
| `AA_CI_BOT_PRIVATE_KEY` | `github:AA-CIS-App/release` | ecosystem | not yet on main (release-please AA-891; Infra docs workflows) | manual (2026-10-22) | **keep** | AA-901. Key of the GitHub App `aa-ecosys-ci-bot` (app id 5421877, variable `AA_CI_BOT_APP_ID`). |
| `AA_CI_BOT_PRIVATE_KEY` | `github:AA-Booking/release` | ecosystem | not yet on main (release-please AA-891; Infra docs workflows) | manual (2026-10-22) | **keep** | AA-901. Key of the GitHub App `aa-ecosys-ci-bot` (app id 5421877, variable `AA_CI_BOT_APP_ID`). |
| `AA_CI_BOT_PRIVATE_KEY` | `github:AA-TripPlanner-Web/release` | ecosystem | not yet on main (release-please AA-891; Infra docs workflows) | manual (2026-10-22) | **keep** | AA-901. Key of the GitHub App `aa-ecosys-ci-bot` (app id 5421877, variable `AA_CI_BOT_APP_ID`). |
| `AA_CI_BOT_PRIVATE_KEY` | `github:AA-CIS-Infra` | ecosystem | db-schema-dump.yml:233; docs-gen.yml:102, :199; migration-copy-guard.yml:172 (retention-rows job, Contents read; AA-929) — replaced `ROOT_REPO_DOCS_TOKEN` (AA-CIS-Infra #281, S247) | manual (2026-10-22) | **keep** | AA-901. Key of the GitHub App `aa-ecosys-ci-bot` (app id 5421877, variable `AA_CI_BOT_APP_ID`). |
| `ROOT_REPO_DOCS_TOKEN` | `github:AA-CIS-Infra` | infra | — | none | **deleted** | Personal access token with write to the root repo (S241 P1-2). Its three Infra docs workflows moved to the `aa-ecosys-ci-bot` App token (AA-CIS-Infra #281); GitHub secret deleted 22/10/2026 (S247). The PAT behind it (most likely `aa-cis-infra-schema-dump`) is still unrevoked: see the GitHub tokens vendor row. |
| `VERCEL_TOKEN` | `github:AA-Partner` | crm | AA-Partner .github/workflows/vercel-deploy-portal.yml:94, :149 | manual (team token aa-partner-ci, expires 2027-04-23) | **keep** | AA-979 P2a-2 (S250): Vercel token scoped to the team (name aa-partner-ci), expires 23/04/2027; deploys the portal (Vercel project aa-cis-portal) from AA-Partner. Repo-level, like the other VERCEL_TOKEN rows (open item 7). |
| `VERCEL_PORTAL_BYPASS_SECRET` | `github:AA-Partner` | crm | AA-Partner .github/workflows/ui-smoke-portal.yml:85; vercel-deploy-portal.yml:170, :269 | none | **keep** | AA-979 P2a-2 (S250): deployment-protection bypass of the Vercel project aa-cis-portal, moved from AA-CIS-App (deleted there). |
| `E2E_TENANT_API_KEY` | `github:AA-Partner` | crm | AA-Partner .github/workflows/ui-smoke-portal.yml:88; vercel-deploy-portal.yml:270 | manual (copy of an aa-cis/dev/e2e-tenant/* key) | **keep** | AA-979 P2a-2 (S250): test tenant portal API key for the portal smoke, moved from AA-CIS-App (deleted there). VERCEL_PORTAL_PROJECT_ID is a repo variable, not a secret. |
| `E2E_MAIL_ROLE_ARN` | `github:AA-Partner/e2e` | crm | AA-Partner .github/workflows/e2e-dev.yml:70 (environment e2e) | none | **keep** | AA-936/AA-939 (S249): role ARN (not a secret value) of the read-only SES e2e mailbox reader. Scope taken from the workflow's environment; not yet confirmed by a GitHub listing (subagents cannot list GitHub secrets). |
| `E2ECRMPASSWORD` | `github:AA-Partner/e2e` | crm | AA-Partner .github/workflows/e2e-dev.yml:76 | manual (crm_dev_identity.py) | **keep** | AA-939 (S249): password of the synthetic MFA partner-pool e2e owner (copy of a crm/dev/e2e-test-crm/* secret). Scope taken from the workflow's environment; not yet confirmed by a GitHub listing (subagents cannot list GitHub secrets). |
| `E2ECRMTOTP` | `github:AA-Partner/e2e` | crm | AA-Partner .github/workflows/e2e-dev.yml:77 | manual (crm_dev_identity.py) | **keep** | AA-939 (S249): TOTP seed of the same synthetic e2e owner (partner pool MFA). Scope taken from the workflow's environment; not yet confirmed by a GitHub listing (subagents cannot list GitHub secrets). |
| `SCRUB_CORPUS_ROLE_ARN` | `github:AA-Partner/scrub-corpus` | crm | AA-Partner .github/workflows/scrub-corpus.yml:65, :97 (environment scrub-corpus) | none | **keep** | AA-938 (S249): role ARN (not a secret value) of the nightly Scrub corpus job. Scope taken from the workflow's environment; not yet confirmed by a GitHub listing (subagents cannot list GitHub secrets). |
| `AA_CI_BOT_PRIVATE_KEY` | `github:AA-Partner/release` | ecosystem | AA-Partner .github/workflows/release-please.yml:42 (environment release) | manual (key generated 2026-10-22) | **keep** | AA-901: key of the GitHub App aa-ecosys-ci-bot for release-please in AA-Partner. Scope taken from the workflow's environment; not yet confirmed by a GitHub listing (subagents cannot list GitHub secrets). |

### Vercel environment variables (secret-bearing) (14)

| Name | Store | Owner app | Consumers (main) | Rotation | Status | Notes |
|---|---|---|---|---|---|---|
| `ADMIN_SECRET` | `vercel:aa-cis-frontend` | cis | AA-CIS-App frontend BFF (server-side admin proxy; since C9 sent only for legacy sessions and non-staff paths, lib/auth-server.ts staffCredentialHeaders) | manual (Production: copy of aa-cis/dev/admin-secret; Preview: copy of aa-cis/dev/admin-secret-preview; both 2026-10-19) | **keep** | One name, two values (S244): Production = main secret (I6); Preview = Preview credential capped at viewer (C9). Open item 1 closed. |
| `ADMIN_PASSWORD` | `vercel:aa-cis-frontend` | cis | — | none | **open-item** | S241 inventory; no reader in AA-CIS-App code on main (nor ADMIN_USERNAME). Candidate orphan: confirm in Vercel and delete by hand (not in the M2 list yet). |
| `ADMIN2_PASSWORD` | `vercel:aa-cis-frontend` | cis | — | none | **open-item** | Same as ADMIN_PASSWORD (with ADMIN2_USERNAME): no reader on main, candidate orphan. Still present 20/10, type Encrypted (`readable-secret`). |
| `INTERNAL_API_KEY` | `vercel:aa-cis-frontend` | cis | AA-CIS-App frontend/app/api/tenant/pipeline/brand-identity/route.ts:12, frontend/app/api/tour-full/[id]/route.ts:11 (sent as X-API-Key) | none | **open-item** | No backend reader of INTERNAL_API_KEY on main (the s4_trigger Lambda is gone); verify what the X-API-Key value is, then drop or document. |
| `SENTRY_AUTH_TOKEN` | `vercel:aa-cis-frontend` | cis | AA-CIS-App frontend/next.config.ts (withSentryConfig, build-time source-map upload) | TBD-Nghiep | **keep** | Vendor Sentry. Type Encrypted: Vercel flags `readable-secret` (S245); re-create as Sensitive (F-5). |
| `COGNITO_CIS_ADMIN_CLIENT_SECRET` | `vercel:aa-cis-frontend` | identity | AA-CIS-App frontend (staff sign-in BFF, process.env.COGNITO_CIS_ADMIN_CLIENT_SECRET) | none | **keep** | AA-816 / ADR 0006a. The secret also sits in Terraform state (client resource). |
| `COGNITO_BREAKGLASS_CLIENT_SECRET` | `vercel:aa-cis-frontend` | identity | AA-CIS-App frontend (break-glass sign-in, process.env.COGNITO_BREAKGLASS_CLIENT_SECRET) | none | **keep** | AA-816. |
| `TRIPPLANNER_API_KEY` | `vercel:aa-tripplanner` | tripplanner | AA-TripPlanner-Web frontend/app/api/browse/route.ts:9, trip/route.ts:15, lib/catalog.ts:46 | with tripplanner/dev/api-key | **keep** | Must be set on Production, Preview and Development (S237 lesson). S245: Production Sensitive; Development + Preview Encrypted (`readable-secret`, F-5). |
| `CATALOG_REVALIDATE_SECRET` | `vercel:aa-tripplanner` | tripplanner | AA-TripPlanner-Web frontend/app/api/revalidate/catalog/route.ts (lib/catalogPurge.ts verifies X-AA-Signature; trimmed) | with aa-cis/dev/tripplanner-revalidate-hmac | **keep** | AA-987. Same value as the CIS secret; Production + Preview, Sensitive. Set with printf, not echo (both sides trim, but a newline elsewhere refuses every notice with 401). Unset = the route answers 503. Set (AA-987 verified live); flipped to keep at S250 close. |
| `SENTRY_DSN` | `vercel:aa-tripplanner` | tripplanner | AA-TripPlanner-Web frontend/instrumentation.ts -> lib/sentryLite.ts (server-side onRequestError reporter, env.SENTRY_DSN) | none | **planned** | AA-871. DSN of Sentry project aa-tripplanner-web; server-only (never NEXT_PUBLIC_). Production + Preview. Flip to keep once set. |
| `COGNITO_BOOKING_STAFF_CLIENT_SECRET` | `vercel:aa-booking-admin` | booking | AA-Booking frontend staff sign-in (AA-680 S3) | none | **keep** | AA-680. Sensitive, Production only; created 18/10/2026. |
| `TP_SESSION_SECRET` | `vercel:aa-tripplanner` | tripplanner | AA-TripPlanner-Web frontend/lib/authRequest.ts (seals the traveller session cookies, at least 32 characters) | manual | **keep** | AA-908 (S250): set on Production + Preview by the orchestrator (value generated, never shown). Rotating it signs every traveller out. |
| `TP_COGNITO_BFF_KEY` | `vercel:aa-tripplanner` | tripplanner | AA-TripPlanner-Web frontend/lib/authRequest.ts (header x-aa-traveller-bff on the Cognito API calls) | with tripplanner/dev/cognito-bff-key | **keep** | AA-908 (S250): copy of tripplanner/dev/cognito-bff-key; Production + Preview. |
| `TP_COGNITO_SIGNUP_PROOF_KEY` | `vercel:aa-tripplanner` | tripplanner | AA-TripPlanner-Web frontend/lib/authRequest.ts (signs ValidationData bff_proof on SignUp) | with tripplanner/dev/cognito-signup-proof-key | **keep** | AA-908 (S250): copy of tripplanner/dev/cognito-signup-proof-key; Production + Preview. |

### Lambda environment keys (acc2) (4)

| Name | Store | Owner app | Consumers (main) | Rotation | Status | Notes |
|---|---|---|---|---|---|---|
| `TRIPPLANNER_API_KEY` | `lambda-env:aa-tripplanner-dev-browse` | tripplanner | — | none | **removed** | Removed by AA-878 I2 (Infra #207 + TP #99, 19/10): the Lambda reads the secret by name. Absent 19/10 and 20/10. |
| `TRIPPLANNER_API_KEY` | `lambda-env:aa-tripplanner-dev-assembly` | tripplanner | — | none | **removed** | Removed by AA-878 I2 (Infra #207 + TP #99, 19/10). Absent 19/10 and 20/10. |
| `MAPBOX_GEOCODING_TOKEN_ARN` | `lambda-env:aa-tripplanner-dev-assembly` | tripplanner | — | none | **removed** | ARN only, dead since AA-712 slice 6a. Removed by AA-878 I2 (19/10); the token was revoked at Mapbox 20/10. |
| `ADMIN_SECRET` | `lambda-env:aa-cis-dev-dfs-balance-check` | cis | — | none | **removed** | Removed by AA-878 I1 (Infra #195, applied 19/10): the env now holds only API_BASE_URL. |

### Vendors and accounts (not machine-checked) (14)

| Credential | Store | Owner | Consumers | Rotation | Notes |
|---|---|---|---|---|---|
| AWS payer / billing console (TrueIDC) | `vendor:trueidc` | TBD-Nghiep | acc2 billing (TrueIDC is the AWS payer vendor) | TBD-Nghiep | Console access via TrueIDC; record who holds it. |
| Namecheap account (lumiguides.it.com) | `vendor:namecheap` | TBD-Nghiep | DNS / domain registration | TBD-Nghiep |  |
| Zoho account | `vendor:zoho` | TBD-Nghiep | mail / business tooling | TBD-Nghiep |  |
| Mapbox public token (NEXT_PUBLIC_MAPBOX_TOKEN) + account | `vendor:mapbox` | TBD-Nghiep | Vercel aa-tripplanner NEXT_PUBLIC_MAPBOX_TOKEN (URL-restricted, S239) | TBD-Nghiep | Old secret geocoding token revoked 20/10/2026 (S245, geocoding API now 401); the TripPlanner docs PR removed its last mention. |
| DataForSEO account | `vendor:dataforseo` | TBD-Nghiep | aa-cis/dev/dataforseo | TBD-Nghiep | **Open (S247, 22/10/2026):** AA-CIS-Infra history holds a DataForSEO API credential from an old committed variables file, and that repo is public since 22/10/2026 ([ADR 0014](../adr/0014-repo-visibility-and-github-plan.md) amendment). Rotation recommended; Nghiệp accepted the risk and chose not to rotate now. Rotate before the repos go back to private or before prod, then update `aa-cis/dev/dataforseo`. Rotation path (AA-981): vendor dashboard → `aa-cis/dev/dataforseo` → force a new deployment of api + worker → `/admin/dfs-balance` 200 → resolve the external scanner alert. |
| OpenAI API key (account) | `vendor:openai` | TBD-Nghiep | aa-cis/dev/openai-key | TBD-Nghiep |  |
| Typesafe / Jev API key (account) | `vendor:typesafe` | TBD-Nghiep | aa-cis/dev/typesafe | TBD-Nghiep |  |
| Geoapify API key (account) | `vendor:geoapify` | TBD-Nghiep | aa-cis/dev/geoapify | TBD-Nghiep |  |
| Sentry org dk-0ql (DSNs + auth token) | `vendor:sentry` | TBD-Nghiep | aa-cis/dev/sentry-dsn-api; booking/dev/sentry-dsn; crm/dev/sentry-dsn; tripplanner/dev/sentry-dsn; Vercel SENTRY_AUTH_TOKEN; Vercel aa-tripplanner SENTRY_DSN | TBD-Nghiep |  |
| Google Cloud API key (gdrive-photo-reader) | `vendor:google` | TBD-Nghiep | aa-cis/dev/gdrive-photo-reader | none (decision 02/10/2026) | Leak closed in CIS PR #535; Nghiep decided no rotation. |
| GitHub tokens (pqnghiep1354) | `vendor:github` | TBD-Nghiep | local gh / MCP OAuth token (`gho_`); three fine-grained PATs with no consumer: `aa-cis-infra-schema-dump` (most likely the former `ROOT_REPO_DOCS_TOKEN` value, secret deleted 22/10), `ACPCORE_READ_TOKEN` (secret deleted 17/10), `aa-cis-acpcore-read` (expired) | manual: `gho_` rotated 2026-10-20 (S245, Nghiệp); PATs: revoke recommended (S247), pending Nghiệp | The `gho_` rotation closes the S240 transcript exposure. **Open (S247):** with `ROOT_REPO_DOCS_TOKEN` gone (AA-CIS-Infra #281) the three PATs are unused; revoking all three in GitHub Settings > Developer settings is recommended to Nghiệp, pending. |
| GitHub App `aa-agent` | `vendor:github` | nghiep | agent sessions via `tools/github/as-app.sh` | on leak / go-live (ADR 0011) | AA-901. App id 5421824, 5 selected repos; actions/contents/PR/workflows write, checks/statuses/issues read; no webhook, no org permissions. Key: `aa-ecosys/github/aa-agent-app-key`. |
| GitHub App `aa-ecosys-ci-bot` | `vendor:github` | nghiep | release-please (AA-891); Infra docs workflows | on leak / go-live (ADR 0011) | AA-901. Created as `aa-ecosys-ci-bot` (`aa-ci-bot` was taken). App id 5421877, 5 selected repos; contents/issues/PR write only. Key: `AA_CI_BOT_PRIVATE_KEY`. |
| Vercel account tokens | `vendor:vercel` | TBD-Nghiep | GitHub VERCEL_TOKEN in AA-CIS-App, AA-Booking, AA-TripPlanner-Web | TBD-Nghiep | Hobby team; one token or three? Record it. |
