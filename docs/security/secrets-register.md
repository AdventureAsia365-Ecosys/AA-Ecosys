# Secrets register

AA-878 (S241 finding P1-2). One row per credential the ecosystem holds: where it is stored, who owns
it, who reads it, how it is managed and rotated, and what should happen to it. **Names and metadata
only — never a value.** The machine-readable twin is [`secrets-register.yaml`](secrets-register.yaml)
(same rows); edit the YAML first, then the tables here to match.

- Updated: 20/10/2026 (S245: first drift check with all four inventories (AWS, Lambda env, GitHub per
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
- Status legend: **keep** (in use) · **open-item** (in use, open finding) · **pending-x1** (consumer
  arrives with X1) · **planned** (added this session, not created yet) · **orphan-delete** (no
  consumer; DRY RUN → Nghiệp OK → delete) · **pending-removal** (plaintext/dead Lambda env key an
  open PR removes) · **deleted / removed** (kept for the log).

## Summary (20/10/2026)

| | Count |
|---|---|
| Rows | 87: 33 Secrets Manager (29 live + 4 deleted 19/10, in the recovery window), 29 GitHub (23 live + 6 deleted/removed), 9 Vercel, 4 Lambda env (all removed), 12 vendor |
| Drift check (S245, all four inventories) | **`diff = 0`** (was 8 before this update). Not checked: GitHub org secrets (the listing answers 403, no org-admin scope; no `github:org` row) |
| Orphans | 4 Secrets Manager — **deleted 19/10/2026**, recovery until 18/11 (`aa-cis/dev/api-keys`, `aa-cis/dev/acp-webhook-secret`, `aa-cis/dev/acp-partner-api`, `tripplanner/dev/mapbox-geocoding-token`); 2 GitHub — **deleted 17/10/2026** (AA-866: `VERCEL_DEPLOY_HOOK`, `ACPCORE_READ_TOKEN`), absent on 20/10; the repo-level `ADMIN_SECRET` and `AWS_ROLE_ARN` on AA-CIS-App are absent too |
| Plaintext secret in a Lambda env | none: `TRIPPLANNER_API_KEY` and the dead `MAPBOX_GEOCODING_TOKEN_ARN` left both TripPlanner Lambdas with I2 (19/10); the ops-probe `ADMIN_SECRET` left with I1 (Infra #195) |
| Planned rows | 0: the 4 planned in S243 exist now (GitHub `VERCEL_PORTAL_BYPASS_SECRET`, `E2E_TENANT_API_KEY`, env `e2e` `E2E_MAIL_ROLE_ARN`; Vercel aa-booking-admin `COGNITO_BOOKING_STAFF_CLIENT_SECRET`) and are `keep` |
| Added S245 | GitHub AA-TripPlanner-Web `AWS_DEPLOY_ROLE_ARN` (role ARN, AA-902) |
| Rotated / revoked 20/10/2026 (S245) | local gh / MCP OAuth token (`gho_`, Nghiệp); old Mapbox geocoding token revoked in the Mapbox account (geocoding API now 401) |
| Rotated 19/10/2026 (S244) | `aa-cis/dev/admin-secret` (I6), `aa-identity/dev/breakglass` (password + TOTP), `aa-cis/dev/db-migrator` (value first written by script, X1 S20) |
| Rotation enabled in Secrets Manager | 0 of 29 live |

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
   `ROOT_REPO_DOCS_TOKEN` is a personal access token (U-25: GitHub App token, out of AA-878 scope).
8. **Terraform state still holds values**: `random_password.tripplanner_api_key` (by design: the
   secret is the source of truth) and the Cognito app client secrets. The ops-probe admin secret
   left state with I1.
9. **acc1 / acc3 secrets** (`pqnghiep-admin`, `nghiep_aa365`): not inventoried yet. The main session
   lists their names (M0 d) and adds rows; AA-517 cleaned 20 strays from acc1 on 02/09.

## Who can read the RDS master (X1 S19)

Since 19/10/2026 (S243, Infra #203 + #204, AA-860; migrator rows updated for X1 S22, Infra #225, S244):

| Principal | Reads `aa-cis/dev/rds`? | Why |
|---|---|---|
| CIS api + worker containers (task role) | **No** — explicit Deny, verified 20/20 AccessDenied after IAM propagation (~8 min) | X1 S19 Deny on `aa-cis/<env>/rds-??????` (master only; `rds-app-user` / `rds-cis-app` stay readable) |
| CIS api + worker `DATABASE_URL` | No — now `aa-cis/dev/rds-cis-app` (`cis_app`) | X1 S18 |
| ECS execution role | No longer for the migrator `DATABASE_URL`: it injects `aa-cis/dev/db-migrator` since X1 S22 | Infra #225 |
| DB Migrate / Schema Dump / isolation probe (migrator task) | Only inside the task (`MASTER_SECRET`, migrator task role) for `roles/` files, `set-password` and `run-script`; every other file runs with the `db_migrator` login | X1 S22; probe 58/58 after S22, `sessions.master_break_glass_only` pass |
| Humans with the MFA admin profile (`aa365-admin`) | Yes | Break-glass only (DM-8.9); prefer DB Migrate `mode=run-script` |
| Agent ECS exec scripts | **No** | They use the container `DATABASE_URL` (`cis_app`); see `docs/ops/runbooks/ecs-exec-s3-mediated.md` |

The same Deny covers `aa-cis/dev/db-migrator`, `booking/*` and `tripplanner/*` for the CIS task role.

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

## Register

### Secrets Manager, acc2 (005097885195, us-west-1) (33)

| Name | Owner app | Consumers (main) | Managed by | Rotation | Last changed | Status | Notes |
|---|---|---|---|---|---|---|---|
| `aa-cis/dev/rds` | cis | migrator task, read in the task as MASTER_SECRET for roles/ files, set-password, run-script only (AA-CIS-Infra db/run_migration.py:204; not injected since X1 S22, Infra #225); AA-CIS-App scripts/link_staff_identity.py:65, services/acp_produce/sweeper_lambda.py:37 (default; Lambda not deployed); humans with the MFA admin profile (break-glass, DM-8.9) | cli (read by data source module.secrets.data.aws_secretsmanager_secret.rds) | none | 2026-07-07 | **keep** | Master DSN (aa_cis_admin). No longer the CIS runtime login since X1 S18 (19/10/2026); the CIS task role is denied it since X1 S19; DB Migrate logs in as db_migrator since X1 S22. See "Who can read the RDS master (X1 S19)". |
| `aa-cis/dev/dataforseo` | cis | ECS api + worker DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD (modules/ecs/main.tf:409-410, :605-606) | cli (data source module.secrets.data.aws_secretsmanager_secret.dataforseo) | none | 2026-07-07 | **keep** | Vendor DataForSEO login/password (JSON). |
| `aa-cis/dev/acp-partner-api` | cis | — | terraform module.secrets.aws_secretsmanager_secret.acp_partner_api (forgotten by AA-878 I2, removed block) | none | 2026-10-15 | **deleted** | Placeholder of the retired ACP v1 partner path. No reader on main of any repo; CloudTrail since 18/10: only the plan role (refresh). LastChangedDate 15/10 is a Terraform tag re-apply, not a value change. Deleted 19/10/2026 (S243), recovery until 18/11/2026. |
| `aa-cis/dev/acp-webhook-secret` | cis | — | terraform module.secrets.aws_secretsmanager_secret.acp_webhook_secret (forgotten by AA-878 I2, removed block) | none | 2026-10-15 | **deleted** | Placeholder of the retired ACP v1 webhook HMAC. No reader on main; CloudTrail since 18/10: only the plan role. Deleted 19/10/2026 (S243), recovery until 18/11/2026. |
| `aa-cis/dev/admin-secret` | cis | ECS api + worker ADMIN_SECRET (modules/ecs/main.tf:402, :603); ops-probe Lambda aa-cis-dev-dfs-balance-check, read by ARN from the event secret_id (AA-CIS-Infra accounts/aa365/dfs_balance.tf:236, :270); copies: GitHub AA-CIS-App env dev ADMIN_SECRET, Vercel aa-cis-frontend ADMIN_SECRET Production only | cli (var.secret_admin_arn, terraform.tfvars) | manual (2026-10-19, AA-816 I6) | 2026-10-19 | **keep** | Main admin secret (machine callers; legacy sessions until S2). Rotated 19/10/2026 (S244, I6): new → 200, old → 403; GitHub env dev + Vercel Production copies updated; api + worker restarted. Preview holds `aa-cis/dev/admin-secret-preview` (C9). Header trust remains for it until S2. |
| `aa-cis/dev/openai-key` | cis | ECS api + worker OPENAI_API_KEY (modules/ecs/main.tf:400, :602); AA-CIS-App shared/llm_client/client.py:134 | cli (var.secret_openai_arn, terraform.tfvars) | none | 2026-08-21 | **keep** | Vendor OpenAI. |
| `aa-cis/dev/api-keys` | cis | — | cli | none | 2026-07-07 | **deleted** | APIFY_API_TOKEN placeholder; api/main.py no longer reads it (no reader on main of any repo). LastAccessedDate 2026-09-07. Deleted 19/10/2026 (S243), recovery until 18/11/2026. |
| `aa-cis/dev/e2e-test-admin` | cis | agent Booking UI checks (Booking BFF → CIS /auth/admin-login) and legacy sign-in on CIS PR previews (skill/aa-ui-verify/SKILL.md), user e2e-claude-code | cli | none | 2026-10-08 | **open-item** | Full CIS admin + Booking admin, legacy password login. Not in GitHub any more (N1 done S244). No password form on Production since S1; on a Preview it reaches only viewer rights (C9). Disable at S2. |
| `aa-cis/dev/jwt-secret` | cis | ECS api + worker JWT_SECRET (modules/ecs/main.tf:403, :604); AA-CIS-App api/routers/auth.py:34 | cli (var.secret_jwt_arn, terraform.tfvars) | none | 2026-09-01 | **keep** | HS256, one key for staff + tenant JWT (S241 P1-3). |
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

### GitHub Actions secrets (29)

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
| `VERCEL_PORTAL_BYPASS_SECRET` | `github:AA-CIS-App` | cis | ui-smoke-portal.yml:58; vercel-deploy-portal.yml:171 | none | **keep** | AA-885: bypass secret of the Vercel project aa-cis-portal, set 19/10. The S245 Vercel listing shows no aa-cis-portal project in the team (access review F-6). |
| `E2E_TENANT_API_KEY` | `github:AA-CIS-App` | cis | ui-smoke-portal.yml:61 (portal smoke) | manual (copy of an aa-cis/dev/e2e-tenant/* key) | **keep** | AA-885: test tenant portal API key for the portal smoke, set 19/10. |
| `E2E_MAIL_ROLE_ARN` | `github:AA-CIS-App/e2e` | cis | e2e-cognito.yml:48 (environment e2e) | none | **keep** | AA-816 E1: role ARN (not a secret value) of the SES e2e mailbox reader, set 19/10 in env `e2e` (branch policy). |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | `github:AA-Booking` | booking | AA-Booking .github/workflows/vercel-deploy.yml:161 (optional) | none | **removed** | Absent in the S245 listing (repo + envs). The workflow only logs the status code without it; re-add and flip to keep if wanted. AWS deploy settings are vars.*, not secrets. |
| `VERCEL_TOKEN` | `github:AA-Booking` | booking | AA-Booking vercel-deploy.yml:83, :132 | TBD-Nghiep | **keep** | Vendor Vercel token. |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | `github:AA-TripPlanner-Web` | tripplanner | AA-TripPlanner-Web .github/workflows/vercel-deploy.yml:161 (optional) | none | **removed** | Absent in the S245 listing (repo + envs). Optional in the workflow; re-add and flip to keep if wanted. |
| `VERCEL_TOKEN` | `github:AA-TripPlanner-Web` | tripplanner | AA-TripPlanner-Web vercel-deploy.yml:83, :132 | TBD-Nghiep | **keep** | Vendor Vercel token. |
| `AWS_DEPLOY_ROLE_ARN` | `github:AA-TripPlanner-Web` | tripplanner | AA-TripPlanner-Web deploy-lambdas.yml:59, :69 | none | **keep** | Lambda deploy role ARN (AA-902), a repo secret so the public repo holds no ARN; not a secret value. Added S245 (was UNREGISTERED). |
| `AWS_ROLE_ARN` | `github:AA-CIS-Infra` | infra | AA-CIS-Infra .github/workflows/terraform-plan.yml:27 (no environment) | none | **keep** | aa-cis-infra-tf-plan role ARN (not a secret). |
| `AWS_ROLE_ARN` | `github:AA-CIS-Infra/prod` | infra | terraform-apply.yml:37; db-migrate.yml:206; db-schema-dump.yml:90; db-isolation-probe.yml:79 (environment: prod) | none | **keep** | aa-cis-infra-tf-apply role ARN (not a secret). Env `prod` has no GitHub protection rule; the OIDC trust requires `refs/heads/main` (access review F-7). |
| `AWS_REGION` | `github:AA-CIS-Infra` | infra | terraform-apply.yml:38, :53 | none | **keep** | Not a secret. |
| `TF_STATE_BUCKET` | `github:AA-CIS-Infra` | infra | terraform-apply.yml:51; terraform-plan.yml:41 | none | **keep** | Not a secret. |
| `TF_VAR_DB_PASSWORD` | `github:AA-CIS-Infra` | infra | terraform-apply.yml:29; terraform-plan.yml:50 | none | **open-item** | RDS master password, repo-level (S241 E12: move into a protected env or drop once RDS manages it). S240: printed once in a local transcript; decision: rotate before prod. |
| `ROOT_REPO_DOCS_TOKEN` | `github:AA-CIS-Infra` | infra | db-schema-dump.yml:71, :177, :183 | TBD-Nghiep | **open-item** | Personal access token with write to the root repo (S241 P1-2; PAT -> GitHub App token is U-25, out of AA-878 scope). |

### Vercel environment variables (secret-bearing) (9)

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
| `COGNITO_BOOKING_STAFF_CLIENT_SECRET` | `vercel:aa-booking-admin` | booking | AA-Booking frontend staff sign-in (AA-680 S3) | none | **keep** | AA-680. Sensitive, Production only; created 18/10/2026. |

### Lambda environment keys (acc2) (4)

| Name | Store | Owner app | Consumers (main) | Rotation | Status | Notes |
|---|---|---|---|---|---|---|
| `TRIPPLANNER_API_KEY` | `lambda-env:aa-tripplanner-dev-browse` | tripplanner | — | none | **removed** | Removed by AA-878 I2 (Infra #207 + TP #99, 19/10): the Lambda reads the secret by name. Absent 19/10 and 20/10. |
| `TRIPPLANNER_API_KEY` | `lambda-env:aa-tripplanner-dev-assembly` | tripplanner | — | none | **removed** | Removed by AA-878 I2 (Infra #207 + TP #99, 19/10). Absent 19/10 and 20/10. |
| `MAPBOX_GEOCODING_TOKEN_ARN` | `lambda-env:aa-tripplanner-dev-assembly` | tripplanner | — | none | **removed** | ARN only, dead since AA-712 slice 6a. Removed by AA-878 I2 (19/10); the token was revoked at Mapbox 20/10. |
| `ADMIN_SECRET` | `lambda-env:aa-cis-dev-dfs-balance-check` | cis | — | none | **removed** | Removed by AA-878 I1 (Infra #195, applied 19/10): the env now holds only API_BASE_URL. |

### Vendors and accounts (not machine-checked) (12)

| Credential | Store | Owner | Consumers | Rotation | Notes |
|---|---|---|---|---|---|
| AWS payer / billing console (TrueIDC) | `vendor:trueidc` | TBD-Nghiep | acc2 billing (TrueIDC is the AWS payer vendor) | TBD-Nghiep | Console access via TrueIDC; record who holds it. |
| Namecheap account (lumiguides.it.com) | `vendor:namecheap` | TBD-Nghiep | DNS / domain registration | TBD-Nghiep |  |
| Zoho account | `vendor:zoho` | TBD-Nghiep | mail / business tooling | TBD-Nghiep |  |
| Mapbox public token (NEXT_PUBLIC_MAPBOX_TOKEN) + account | `vendor:mapbox` | TBD-Nghiep | Vercel aa-tripplanner NEXT_PUBLIC_MAPBOX_TOKEN (URL-restricted, S239) | TBD-Nghiep | Old secret geocoding token revoked 20/10/2026 (S245, geocoding API now 401); the TripPlanner docs PR removed its last mention. |
| DataForSEO account | `vendor:dataforseo` | TBD-Nghiep | aa-cis/dev/dataforseo | TBD-Nghiep |  |
| OpenAI API key (account) | `vendor:openai` | TBD-Nghiep | aa-cis/dev/openai-key | TBD-Nghiep |  |
| Typesafe / Jev API key (account) | `vendor:typesafe` | TBD-Nghiep | aa-cis/dev/typesafe | TBD-Nghiep |  |
| Geoapify API key (account) | `vendor:geoapify` | TBD-Nghiep | aa-cis/dev/geoapify | TBD-Nghiep |  |
| Sentry org dk-0ql (DSNs + auth token) | `vendor:sentry` | TBD-Nghiep | aa-cis/dev/sentry-dsn-api; Vercel SENTRY_AUTH_TOKEN | TBD-Nghiep |  |
| Google Cloud API key (gdrive-photo-reader) | `vendor:google` | TBD-Nghiep | aa-cis/dev/gdrive-photo-reader | none (decision 02/10/2026) | Leak closed in CIS PR #535; Nghiep decided no rotation. |
| GitHub tokens (pqnghiep1354) | `vendor:github` | TBD-Nghiep | ROOT_REPO_DOCS_TOKEN (PAT); old ACPCORE_READ_TOKEN PAT (secret deleted 17/10); local gh / MCP OAuth token (`gho_`) | manual: `gho_` rotated 2026-10-20 (S245, Nghiệp); PATs TBD-Nghiep | The `gho_` rotation closes the S240 transcript exposure. Still open: revoke the old ACPCORE PAT; ROOT_REPO_DOCS_TOKEN stays a PAT until U-25 (GitHub App). |
| Vercel account tokens | `vendor:vercel` | TBD-Nghiep | GitHub VERCEL_TOKEN in AA-CIS-App, AA-Booking, AA-TripPlanner-Web | TBD-Nghiep | Hobby team; one token or three? Record it. |
