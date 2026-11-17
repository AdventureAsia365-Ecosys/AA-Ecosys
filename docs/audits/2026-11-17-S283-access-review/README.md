---
id: SEC-05-2026q4b
title: Access review 2026-Q4 (pre-pilot re-run)
description: Who and what can reach each app (GitHub, Vercel, AWS IAM, Cognito, DB roles, secrets) on 17/11/2026, the findings, and what changed since the first review of 20/10/2026.
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-partner, aa-cis-infra]
last_reviewed: 2026-11-17
review_every_days: 90
related: [SEC-01, SEC-02, SEC-05, AA-1111, AA-1109, AA-878, AA-838]
---

# Access review 2026-Q4 (pre-pilot re-run)

Date: 17/11/2026 (S283). Agent: Claude Code (lane S283-l6), read-only. Cost: 0 USD.
Previous review: [2026-10-20-S245-access-review](../2026-10-20-S245-access-review/README.md). Next: first session of
2027-Q1 (DM-8.10, 90 days).

Why a second Q4 record: the S282 ecosystem audit (AA-1109) found the first review out of date before a pilot with real
personal data (R25: 4 WORKFORCE users then, 12 now; F-15 never recorded), and AA-1111 asks for it to be recorded again
together with R08 (admin sign-in without a second factor) and R34 (agents on the human admin role).

No secret value, e-mail address, account ID, ARN, pool ID, access key ID or personal name is on this page. People are
named by role; test identities by a stable label (W1..W12 WORKFORCE, X1..X10 external, P1..P14 partner, in creation
order) with their groups and e-mail domain.

Status column in the findings: **new** (not in S245), **changed** (S245 finding, state moved), **unchanged**,
**closed** (listed again in section 8).

## 1. Sources

| Part | Source (read-only, 17/11/2026) | Note |
|---|---|---|
| GitHub org + repos | `gh api` GET: org settings, members, `members?role=admin`, teams, outside collaborators, invitations, installations, Actions permissions, fork-PR approval; per repo collaborators, keys, hooks, environments (+ protection rules) | Repo list per App installation needs an App token: not readable with the user token |
| GitHub secrets | Names per repo / environment / org through `gh api …/actions/secrets` (names and dates only) | `gh secret` is blocked for subagents; the REST read gives the same names |
| Vercel | Vercel MCP `list_teams`, `list_team_members`, `list_projects` | 0 projects left |
| AWS IAM | Terraform on AA-CIS-Infra `origin/main` (39b2d353, 16/11) + IAM Access Analyzer findings | Live `aws iam` reads are blocked for subagents by the guardrail hook: section 4.3 lists the commands for the orchestrator. The S282 orchestrator run gave partial numbers (used below) |
| Cognito | `cognito-idp list-user-pools / describe-user-pool / get-user-pool-mfa-config / list-identity-providers / list-users / list-groups / list-users-in-group / admin-get-user / admin-list-groups-for-user` | Counts, groups, enabled flag, MFA setting, e-mail domain |
| DB roles | `docs/architecture/db-schema-reference.md` sections Roles and Default privileges (live dump 16/11/2026 12:33 UTC) | Effective reach per login role, credential columns and staff rows: run-script `s283_access_review_db.py` (section 6.2), run 17/11 |
| Secrets | acc2 `secretsmanager list-secrets` + `get-resource-policy`; drift check `tools/secrets/register_check.py` against `docs/security/secrets-register.yaml` with the AWS, GitHub and Lambda env inventories | Vercel inventory empty (no project) |

## 2. GitHub (org AdventureAsia365-Ecosys, Free plan)

| Item | State on 17/11 | Change since S245 |
|---|---|---|
| Org members / admins | 2 members, both org admins: the tech lead's account and the GitHub break-glass account | Unchanged |
| Teams, outside collaborators, pending invitations | 0 / 0 / 0 | Unchanged |
| 2FA required; default member permission; members can create repos | 2FA required; default `read`; members can create repositories (public and private): **yes**; private forks off | Unchanged |
| Repositories | 7, all public: AA-CIS-App, AA-Booking, AA-TripPlanner-Web, AA-Partner, AA-CIS-Infra, AA-Ecosys (root), project-template | +AA-Partner, +project-template; AA-CIS-Infra now public |
| Collaborators per repo | The 2 org admins, `admin`, on all 7 | Unchanged |
| Deploy keys / webhooks | 0 / 0 on all 7 | Unchanged |
| GitHub Apps installed | 5, all "selected repositories": `vercel`, `linear-code`, `claude`, `aa-agent` (agent PR author, ADR 0011), `aa-ecosys-ci-bot` (CI bot) | Was 4 on "all repositories"; `notion-workspace` removed; the 2 own Apps added (S245 F-8 part 1 closed) |
| Actions policy | Selected actions only, SHA pinning required, default workflow token `read`, workflows cannot approve PRs | Not recorded in S245 |
| Fork-PR approval | `all_external_contributors` on the org and on all 7 repos | AA-1111 item: done |
| Environments with rules | AA-CIS-Infra `prod` and `org`: required reviewers + branch policy; `dev-db-auto`: branch policy. AA-CIS-App `dev`, `e2e`, `release`: branch policy; `prod`: protected branches. AA-Booking `dev`, `release`; AA-Partner `dev`, `e2e`, `release`, `scrub-corpus`; AA-TripPlanner-Web `release`; root `ci-hygiene`: branch policy | AA-CIS-Infra `prod` now has a reviewer + branch policy (S245 F-7 part 2), but the Dev apply moved to env `dev` (AA-1023 rename), which has **no rule** (F-03) |
| Environments without rules | AA-CIS-Infra `dev` (holds the apply role's `AWS_ROLE_ARN`), `staging`; AA-CIS-App `Preview`, `Production`, `staging`; AA-Booking `Preview`, `Production`; AA-TripPlanner-Web `Preview`, `Production` | Vercel-era leftovers (F-13) |
| Secrets | Org: 0. Repo + environment names: 31 inventories read; drift check result in section 7 (F-11) | S245 org listing was 403; now readable |

Repo-level secrets (readable by a workflow on any branch, so only behind the "who can push" gate): AA-CIS-Infra
`TF_VAR_DB_PASSWORD` and `AA_CI_BOT_PRIVATE_KEY`; AA-CIS-App `E2E_ADMIN_USERNAME` / `E2E_ADMIN_PASSWORD` (no workflow on
`main` reads them) and `GOLDEN_GUARD_KEY`; AA-Partner `E2EPORTALEMAIL` / `E2EPORTALPASSWORD` / `E2EPORTALTOTP`. The
other credentials sit in environments with a branch policy. `VERCEL_TOKEN` is gone from every repo.

## 3. Vercel (Hobby team)

| Item | State | Change |
|---|---|---|
| Team members / access groups | 1 owner (the tech lead); 0 access groups | Unchanged |
| Projects | **0**: `aa-cis-portal` deleted (S256), `aa-cis-frontend` and `aa-booking-admin` retired (S272, AA-911, staff admins on ECS), `aa-tripplanner` retired (S272, AA-1038, TripPlanner web on ECS behind CloudFront) | Was 3 |
| Secret-bearing env vars | None left (no project). The register still lists `vendor:vercel` account tokens as orphan-delete | S245 F-5, F-6, F-11 closed by the retirement |

## 4. AWS IAM (acc2; acc1 and acc3 not read in this lane)

### 4.1 People

- Humans reach acc2 through the profile `aa365-admin` (= `default`), which assumes the Terraform-managed admin role with
  MFA, 12-hour session (AA-1004, S273). Since S273 the hand-made 8-hour role is retired.
- Agents run in the same shell, so on the same human admin role: this review ran as that role (STS check 17/11). The
  narrow agent role `aa-cis-dev-agent-session` (AA-730, profile `aa365-agent`) exists in Terraform but is not the
  default. Compensating control: the Claude Code subagent hook blocks `aws iam`, `gh secret`, pushes, merges and
  deletes in subagents (this lane hit it). R34 / F-02.
- IAM users (S282 orchestrator read, 16/11): 1 IAM user (the human's base user that the admin role is assumed from),
  root MFA on, no root access key. Access key age, last use and MFA device of that user: not read yet (F-15, 4.3).
- acc1: only `AA1-Bedrock-Invoker` (assumed by the CIS task role with an ExternalId) and the break-glass role
  `AA-BreakGlass-Admin` (root ADR 0001a note S278). acc3: SSO permission set `AA-Admin` from acc1 Identity Center.
  Not re-read here (profile scope of this lane).

### 4.2 Machine roles and the secrets each can read (Terraform `origin/main`)

| Role (name) | Used by | Secrets it can read | Change since S245 |
|---|---|---|---|
| `aa-cis-dev-ecs-task-role` | CIS api + worker | `GetSecretValue` on `*` minus a Deny on the RDS master, `db-migrator`, `booking/*`, `tripplanner/*`, `crm/*`, `aa-crm/*`, `aa-ecosys/*`, `aa-identity/*` | Deny list grew by 4 prefixes; the Allow is still `*` (F-04) |
| `aa-cis-dev-ecs-execution-role` | Inject CIS task secrets | `aa-cis/dev/*` pattern | Unchanged |
| Booking execution / task roles | Booking api + worker | Named ARNs only: Booking DSN, Booking Sentry DSN | +Sentry DSN |
| TripPlanner Lambda role + `aa-tripplanner-dev-web` execution role | 3 Lambdas, web on ECS | `tripplanner/dev/*` named secrets (API key, DSN, Cognito BFF / sign-up proof keys, tenant assertion key) | +web service, +tenant assertion key |
| CRM api / web roles (AA-Partner) | CRM api, web | Named ARNs only: CRM DSN, CRM Sentry DSN, the CRM M2M client, the mail OAuth clients (no wildcard); web: `crm/dev/web` | New since S245 |
| `aa-cis-dev-db-migrate-*` | DB Migrate, schema dump, probes | `db-migrator` (inject), DSN list + master in the task | Unchanged |
| `aa-cis-infra-tf-plan` | Terraform plan (any branch) | Named list `tf_plan_secret_arns` | Unchanged |
| `aa-cis-infra-tf-apply` | Terraform apply, DB Migrate, schema dump, probes (env `dev` + `ref main`) | Still `SecretsManagerReadWrite`, but the boundary now **denies `GetSecretValue` on every secret outside `tf_plan_secret_arns`** and denies resource-policy edits on the guarded secrets (AA-873, S261) | S245 F-7 value-read closed |
| `aa-cis-infra-db-auto-apply` | migration-apply (env `dev-db-auto` + `ref main`) | Migrator path only | New since S245 |
| App deploy roles (CIS, Booking, TripPlanner, CRM) | GitHub OIDC deploys | None | +CRM |
| `aa-cis-dev-agent-session` | Agent shells (not default) | None: `DenyDangerous` covers secret values; no exception for E2E secrets | Unchanged (F-12 of S245) |
| Cognito trigger Lambdas, ops Lambdas, scheduler, flow logs, snapshot expiry, e2e mail reader, admin-session digest | Infrastructure | None, except the DFS balance probe (`aa-cis/dev/admin-secret`) | +admin-session digest Lambda |

Secrets with a resource policy (3): the WORKFORCE break-glass login, the `aa-agent` App key and the Linear API key.
Each denies `GetSecretValue` / `PutSecretValue` (and for the last two also update, rotate, replicate) to every
principal except the human MFA admin role. IAM Access Analyzer (account analyzer, external access): 0 active
findings (11 role + 1 bucket archived as intended trust, 1 role + 1 bucket resolved).

### 4.3 Live cross-check still open (orchestrator, read-only, single-line)

```bash
aws iam get-account-summary --profile aa365-admin --region us-west-1 --query 'SummaryMap.{Users:Users,Roles:Roles,MFA:AccountMFAEnabled,RootKeys:AccountAccessKeysPresent}' --output json
aws iam list-users --profile aa365-admin --region us-west-1 --query 'Users[].[UserName,CreateDate,PasswordLastUsed]' --output text
for u in $(aws iam list-users --profile aa365-admin --region us-west-1 --query 'Users[].UserName' --output text); do echo "== user"; aws iam list-access-keys --user-name "$u" --profile aa365-admin --region us-west-1 --query 'AccessKeyMetadata[].[Status,CreateDate]' --output text; aws iam list-mfa-devices --user-name "$u" --profile aa365-admin --region us-west-1 --query 'length(MFADevices)' --output text; aws iam list-attached-user-policies --user-name "$u" --profile aa365-admin --region us-west-1 --query 'AttachedPolicies[].PolicyName' --output text; aws iam list-user-policies --user-name "$u" --profile aa365-admin --region us-west-1 --query 'PolicyNames' --output text; done
for k in $(aws iam list-users --profile aa365-admin --region us-west-1 --query 'Users[].UserName' --output text | xargs -n1 -I{} aws iam list-access-keys --user-name {} --profile aa365-admin --region us-west-1 --query 'AccessKeyMetadata[].AccessKeyId' --output text); do aws iam get-access-key-last-used --access-key-id "$k" --profile aa365-admin --region us-west-1 --query 'AccessKeyLastUsed.[LastUsedDate,ServiceName]' --output text; done
for r in $(aws iam list-roles --profile aa365-admin --region us-west-1 --query 'Roles[?!starts_with(Path, `/aws-service-role/`)].RoleName' --output text); do echo "$r $(aws iam get-role --role-name "$r" --profile aa365-admin --region us-west-1 --query 'Role.RoleLastUsed.LastUsedDate' --output text)"; done
```

Record here only counts, key ages in days, last-used dates and role names (no user names, key IDs or ARNs). Questions:
any IAM user besides the base user; any access key older than 90 days or unused for 90 days; any role unused for 90
days (removal candidate); does the base user hold anything beyond "assume the admin role with MFA".

Result (orchestrator, 17/11/2026, read-only, counts and ages only):

- Account summary: 1 IAM user, 62 roles (20 service-linked), root has MFA, root has no access key.
- The one IAM user (U1, the base user the CLI profiles start from): 1 MFA device; console password last used 131 days
  ago; **one active access key, 132 days old**, used today (STS only: it only assumes roles). Policies: five AWS
  read-only managed policies (EC2, CloudWatch, RDS, S3, Billing) plus two inline policies that let it assume the admin
  session role and the agent session role. No group.
- Roles (42 non service-linked): every one was used in the last 30 days except `aa-cis-dev-agent-session` (36 days).
  No role unused for 90 days, so no removal candidate.

Answers: no IAM user besides the base user; **the base user's key is past 90 days (132 d)** → rotate it (F-15, a hand
step with MFA: create the new key, update the local profile, deactivate then delete the old one); no role unused for 90
days; the base user holds read-only policies beyond "assume the admin role with MFA" (the five managed read-only
policies): keep or trim is the tech lead's call (F-15).

**Update 17/11/2026 ~05:00Z (S283):** the base user's key is rotated. A new access key was created by the tech lead and written to the local base profile by the agent from the downloaded file (the secret was never printed); `sts get-caller-identity` works with it. The old key (created 07/07/2026, 132 days) is now **Inactive**; delete it from 18/11 after one quiet day. A first new key that was pasted into a chat by mistake was deleted at once and never used. F-15 key part: done.

## 5. Cognito (acc2)

| Pool | Users | Groups (members / enabled) | MFA and sign-in |
|---|---|---|---|
| `aa-workforce-dev` (staff) | 12 (11 enabled, 12 confirmed) | `cis-admin` 4/3, `booking-admin` 3/2, `crm-platform-admin` 1/1, `crm-ops` 1/1, `crm-support` 1/1, `cis-content` 1/1, `cis-customer_success` 1/1, `booking-sales` 1/1, `booking-finance` 2/2, `booking-contracting` 1/1; empty: `cis-finance`, `cis-content_lead`, `cis-tenant_qa`, `cis-ai_ops`, `cis-support`, `booking-content_creator` | MFA **OPTIONAL** (TOTP available); first factors e-mail code or password; no external IdP; admin-only user creation; threat protection off. 1 of 12 users has TOTP (the break-glass) |
| `aa-external-dev` (travellers) | 10 (10 enabled) | none | MFA **OFF**; e-mail code or password; self sign-up allowed |
| `aa-partner-dev` (agency members, CRM) | 14 (14 enabled) | none | MFA **ON** (TOTP); password first factor; admin-only creation. Cognito reports no MFA preference on any user (the E2E runs use TOTP seeds held as GitHub environment secrets) |
| `aa-m2m-dev` (machine clients) | 0 | none | 1 app client (client credentials); MFA n/a |

WORKFORCE users (S245 had 4):

| Label | Role of the person | E-mail domain | Groups | Enabled | MFA | Remark |
|---|---|---|---|---|---|---|
| W1 | Break-glass staff login (AA-854) | adventure.asia | cis-admin, booking-admin | **No** (off at rest, by design) | TOTP | Keep. Unchanged |
| W2 | Tech lead | adventure.asia | cis-admin, booking-admin, crm-platform-admin | Yes | none | Keep; needs a second factor (F-01). +crm-platform-admin since S245 |
| W3 | Business owner | adventure.asia | cis-admin | Yes | none | S245 Q-1 still open: admin or a narrower group? Needs a second factor (F-01, F-06) |
| W4 | E2E identity (AA-816 E1) | E2E test mail domain | cis-content | Yes | none | Keep. S245 group `cis-reviewer` became `cis-content` |
| W5 | E2E identity A10a, Booking admin (reads audit log) | E2E test mail domain | booking-admin | Yes | none | New. Admin group on a test identity (F-05) |
| W6 | E2E identity A10b, CIS admin (rehearsal) | E2E test mail domain | cis-admin | Yes | none | New. Admin group on a test identity (F-05) |
| W7 | E2E identity A10c, CRM staff | E2E test mail domain | crm-support, crm-ops | Yes | none | New. Keep |
| W8 | E2E identity, customer success | E2E test mail domain | cis-customer_success | Yes | none | New. Keep |
| W9 | E2E identity A10e, Booking staff | E2E test mail domain | booking-sales | Yes | none | New. Keep |
| W10, W11 | E2E identities A10e, maker / checker | E2E test mail domain | booking-finance | Yes | none | New. Keep |
| W12 | E2E identity, Booking contracting | E2E test mail domain | booking-contracting | Yes | none | New. Keep |

The E2E identities sign in with an e-mail code. Codes for the admin, CRM staff and Booking staff identities (A10b,
A10c, A10e) land under a mailbox prefix that only the MFA admin role reads, so those identities are agent-only, never
CI (runbook `docs/ops/runbooks/pilot-rehearsal.md`, section Identities).

External pool: X1..X9 E2E travellers (E2E test mail domain, created 24–25/10), X10 a tech-lead test account on a
personal mail domain (created 01/11). Partner pool: P1..P9, P12..P14 E2E agency members (E2E test mail domain;
rehearsal agencies), P10 and P11 tech-lead test accounts on a personal mail domain (created 01–02/11). No real agency
member or traveller is in any pool yet.

Legacy sign-in rows and staff app grants: counted in section 6.2 (`shared.admin_users` 12 rows, 7 active;
`booking.staff_users` 17 rows, 8 active and all Cognito-linked). The legacy E2E admin logins of S245 F-1 / F-2 are
inactive; their Secrets Manager logins (`aa-cis/dev/e2e-test-admin`, `-admin-2`, `-viewer`) were last read on 27/10.

## 6. DB roles (shared RDS)

### 6.1 From the live dump (16/11/2026 12:33 UTC)

| Role | Login / attributes | Member of | Conn. limit | Uses | Change since S245 |
|---|---|---|---|---|---|
| `aa_cis_admin` | login; not superuser, no BYPASSRLS | `rds_superuser`, `cis_owner`, `cis_app`, `bk_owner`, `tp_owner`, `crm_owner` | none | Master: break-glass, migrator task (`roles/`, `set-password`, `run-script`) | +`crm_owner` |
| `db_migrator` | login | `cis_owner`, `cis_app`, `bk_owner`, `tp_owner`, `catalog_owner`, `crm_owner`, `pg_read_all_stats` | 5 | DB Migrate, schema dump, probes | +`crm_owner` |
| `cis_app` | login | — | 90 | CIS api + worker | Unchanged |
| `aa_app_user` | login | — | 15 | CIS tenant pool (RLS) | Unchanged |
| `booking` | login | — | 15 | Booking api + worker | Unchanged |
| `tripplanner` | login | — | 30 | TripPlanner Lambdas + web | Unchanged |
| `crm_app` | login | `crm_ai_reader`, `crm_eraser`, `crm_insights`, `crm_support_reader` | 6 | CRM api (+ `crm.job` worker in process) | New |
| `cis_owner`, `bk_owner`, `tp_owner`, `crm_owner`, `catalog_owner` | NOLOGIN | — | — | Table owners | +`crm_owner` |
| `crm_ai_reader`, `crm_eraser`, `crm_insights`, `crm_support_reader` | NOLOGIN | — | — | CRM capability roles granted to `crm_app` | New |

No role is superuser or BYPASSRLS except what the master inherits from `rds_superuser`. Default privileges: each owner
grants DML only to its own app's runtime role (`cis_owner` → `cis_app` in 7 CIS schemas, `bk_owner` → `booking`,
`tp_owner` → `tripplanner`, `crm_owner` → `crm_app`); `crm_owner` also keeps EXECUTE on its future functions to itself
(no PUBLIC default). No default ACL grants across apps. `catalog_owner` has no default ACL. RLS: 325 policies in the
dump; RLS catalogue guard reports 0 unallowlisted violations.

### 6.2 Effective reach (run-script, 17/11/2026)

Source: `s283_access_review_db.py` (the lane's `.tmp-session/S283/access_review_db.py`), DB Migrate `mode=run-script`,
`READ_ONLY = True`, run by the orchestrator on 17/11/2026 00:26 UTC as the master on PostgreSQL 15.17 (run 43987418006,
success, 399 `SCRIPT` lines). Catalog reads and aggregate counts only: no row value, username or e-mail was printed.

**Roles and membership.** 23 roles outside `pg_*` (7 login roles: `aa_cis_admin`, `db_migrator`, `cis_app`,
`aa_app_user`, `booking`, `tripplanner`, `crm_app`). No role is SUPERUSER, BYPASSRLS or REPLICATION. Only the master
has CREATEDB / CREATEROLE (from RDS) and a password `VALID UNTIL`. 24 memberships, none granted WITH ADMIN OPTION
except the RDS-managed grants of `rds_superuser` (`pg_read_all_data`, `pg_write_all_data`, `pg_monitor`, …), which only
the master holds. `aa_app_user` and `crm_app` are NOINHERIT: `crm_app` must `SET ROLE` to use its four capability roles.
Sessions at the time: master 1 (the script), `cis_app` 2, `booking` 1, `tripplanner` 1, `crm_app` 1; `aa_app_user` and
`db_migrator` 0. Same as the dump (6.1).

**Database and schema ACLs.** Database: PUBLIC keeps `CONNECT` and `TEMPORARY` (the PostgreSQL default), `cis_owner`
has `CREATE`. Schemas: `CREATE` only for each schema's owner; `public` grants PUBLIC `USAGE` only (no PUBLIC `CREATE`
anywhere). PUBLIC `SELECT` on 2 relations, both in `public` (extension views).

**Effective reach per login role** (direct grants and through membership; relations = tables, views, materialized and
foreign tables; no runtime role can TRUNCATE, own a relation or create in a schema):

| Login role | Own schemas: SELECT / write | Outside its own schemas (all marked `cross_app`, read-only unless stated) |
|---|---|---|
| `cis_app` | `shared` 113/99, `acp_contract` 17/17, `acp_shared` 23/23, `acp_deliver` 1/1, `geo` 18/18, `gold_aa_internal` 9/7, `silver_aa_internal` 8/8, `learn` 9/9 | `booking` 12 views (`v_ops_*`, `v_supply_*`, `v_from_prices`, `v_tenant_billing_status`, `v_tenant_erasure_report_v1`); `tripplanner` 6 views (`v_ops_*`, `v_tenant_erasure_report_v1`) |
| `aa_app_user` (tenant pool, RLS) | `shared` 6/3, `acp_shared` 11/4, `acp_contract` 5/0, `acp_deliver` 1/0, `gold_aa_internal` 5/1, `silver_aa_internal` 4/0, `catalog` 15/0 (column grants on 4 schemas) | none |
| `booking` | `booking` 117/85 (column-level UPDATE on 27 tables) | `catalog` 24 relations |
| `tripplanner` | `tripplanner` 19/14 | `catalog` 29 relations; `booking.v_from_prices` (1 view); INSERT on `shared.llm_call_log` (cost ledger, workspace LLM rule) |
| `crm_app` | `crm` 152/136 (column-level grants on 6 tables) | none |

All 6 `cross_app` rows are published read contracts the owner granted on purpose: the `catalog` schema (the shared
catalogue contract), owner-made `v_*` views of Booking and TripPlanner for the CIS admin ops / supply / erasure pages and
the TripPlanner "from price", and the one ledger INSERT. No runtime role reads or writes another app's **base table**,
and nothing reaches the `crm` schema except `crm_app` (and master / migrator). Compared with S245 ("no cross-app
grant"): the S245 statement covered default ACLs only; these view grants are explicit per-object grants in owner
migrations, not drift. They are the edges to watch (F-22).

**Credential columns** (DM-6.1 tag `conf:credential`, 17 columns on 13 tables): each is readable only by its own app's
runtime role plus the master and `db_migrator`:

| Schema | Columns | Login roles that can SELECT them |
|---|---|---|
| `booking` | 2 (customer OTP hash, customer refresh-token hash) | `booking`, master, migrator |
| `crm` | 12 (OTP / link / session / calendar-feed hashes, encrypted integration secret, wrapped tenant data key, …) | `crm_app`, master, migrator |
| `shared` | 1 (`admin_users.password_hash`) | `cis_app`, master, migrator |
| `tripplanner` | 2 (guest token and its hash on `sessions`) | `tripplanner`, master, migrator |

`aa_app_user` reads none of them. Note: `tripplanner.sessions` keeps the guest token in clear next to its hash (F-23).

**Functions.** SECURITY DEFINER: 20, all in `crm`, owned by `crm_owner`, none executable by PUBLIC (the `crm_owner`
default ACL removes the PUBLIC default). PUBLIC may execute 81 non-definer (SECURITY INVOKER) functions: `booking` 67,
`shared` 9, `gold_aa_internal` 3, `geo` 2. An invoker function runs with the caller's rights, so this opens no table;
it is hygiene only (F-21).

**Default ACLs** (32 rows): unchanged from S245 plus `crm_owner` → `crm_app` (tables DML, sequences) and `crm_owner`
EXECUTE on its own future functions. `cis_owner` → `cis_app` in 7 CIS schemas, `bk_owner` → `booking`, `tp_owner` →
`tripplanner`. No default grant to another app's role or to PUBLIC.

**RLS coverage** (tables with RLS on / forced / total): `crm` 131 / 130 / 147, `shared` 22 / 18 / 106, `acp_shared`
14 / 5 / 23, `learn` 8 / 8 / 9, `tripplanner` 5 / 5 / 13, `gold_aa_internal` 4 / 3 / 7, `silver_aa_internal` 4 / 4 / 8,
`booking` 2 / 2 / 91, `acp_contract` 1 / 0 / 15, `acp_deliver` 1 / 0 / 1, `retired` 1 / 0 / 2, `geo` 0 / 0 / 18,
`public` 0 / 0 / 1. Tenant isolation rests on RLS in `crm` and the tenant-scoped `shared` / `acp_*` tables; Booking relies on its own
role and API, not RLS (2 of 91).

**Staff access rows** (aggregate counts):

| Table | Result |
|---|---|
| `shared.admin_users` (legacy CIS sign-in rows) | 12 rows. **Active 7**: 1 owner admin (Cognito-linked, **still has a password hash**), 3 admin (2 Cognito-linked; 1 E2E not yet linked, never signed in), 1 content (E2E), 1 customer success (E2E), 1 viewer (E2E CI smoke, **password**, never signed in, not linked). **Inactive 5**: 3 admin E2E rows with a password (the legacy full-admin E2E logins of S245 F-1 / F-2) and 2 content rows with a password, never signed in. No row idle over 90 days |
| `shared.staff_app_grant` | 1 grant: Booking `admin`, active user |
| `shared.staff_crm_grant` | 1 grant: CRM `platform_admin`, active user |
| `shared.staff_tenant_assignment` | 1 `backup` assignment (1 staff, 1 tenant) |
| `shared.staff_view_as_session` | 2 sessions, both in the last 90 days, **0 open** |
| `booking.staff_users` | 17 rows. **Active 8**, all Cognito-linked (admin 3, contracting 2, finance 2, sales 1): **0 active unlinked** (AA-911 met). **Inactive 9** bridge-era rows (admin 5, contracting 4; never seen, not linked) |
| `crm.support_grant` | 4 grants, all `revoked`; 0 active, 0 past expiry, 0 with identity shown (RLS FORCE: a lower bound as seen by the master) |

| Check | Expected | Result |
|---|---|---|
| `cross_app` rows | 0 on base tables | 6, all owner-published views / catalogue contract / ledger INSERT; 0 on base tables. **Pass** (watch, F-22) |
| Credential columns readable by a login role | only the owning app's runtime role | **Pass**: 17 / 17 own app only (+ master, migrator) |
| PUBLIC EXECUTE on SECURITY DEFINER functions in app schemas | 0 or each justified | **Pass**: 0 (81 invoker functions open to PUBLIC, F-21) |
| PUBLIC CREATE on any schema | 0 | **Pass**: 0 |
| `shared.admin_users` active rows with a password | 0 E2E full-admin rows (S245 F-1, F-2) | **Pass** for F-1 / F-2 (the 3 legacy E2E admin rows are inactive). 2 active rows still hold a password hash: the owner and the E2E viewer (F-20) |
| `booking.staff_users` active rows without a Cognito link | 0 (AA-911) | **Pass**: 0 |
| Open view-as sessions / active CRM support grants past expiry | 0 / 0 | **Pass**: 0 / 0 |

## 7. Findings

| # | Finding | Severity | Proposed action (approval) | Status | Issue |
|---|---|---|---|---|---|
| F-01 | WORKFORCE pool MFA is OPTIONAL with e-mail code or password as first factor: 11 of 12 users have no second factor, among them all enabled `cis-admin` / `booking-admin` / `crm-platform-admin` members (tech lead, business owner, 2 E2E identities). Admins see every tenant's data | High | **Change** (tech lead): require TOTP for the admin groups (pool `ON`, or a pre-token check that refuses an admin group without MFA) with the ADR 0006 amendment; enrol the tech lead and business owner first | new (R08) | AA-1111 |
| F-02 | Agent shells run on the human 12-hour admin role while reading untrusted content; the narrow `aa-cis-dev-agent-session` role exists but is not the default; only the subagent hook narrows subagents | Medium | **Decide** (tech lead): make `aa365-agent` the default for agent shells and add a read-only audit variant (view-only + security-audit managed policies) for reviews like this one; keep the hook | new (R34) | AA-1111 |
| F-03 | AA-CIS-Infra env `dev` (holds the Terraform apply role ARN; terraform-apply, DB Migrate, schema dump, probes) has no deployment branch policy or reviewer; the only "main only" gate is the IAM `ref` condition | Low | **Change** (tech lead, free): add deployment branch policy `main` to env `dev` so the gate is two layers again | changed (S245 F-7 part 2 moved from `prod` to `dev`) | AA-866 |
| F-04 | CIS task role: `GetSecretValue` Allow on `*` with a Deny list (now 8 prefixes); any new secret prefix is readable by CIS until someone adds a Deny | Medium | **Change** (IAM, tech lead): replace the Allow with an allow-list (`aa-cis/dev/*`, `aa-llm/*`, `acp/*` tenant connector secrets) and keep the Deny as a second layer | changed (Deny widened, Allow unchanged) | AA-878 |
| F-05 | Two E2E identities sit in admin groups (W5 `booking-admin`, W6 `cis-admin`), enabled at all times, no second factor; their codes go to the admin-only mailbox prefix | Low | **Keep** while the pilot rehearsals run (ADR 0006a A10a/A10b limit their writes); propose to disable them between rehearsals and include them in F-01's MFA rule | new | AA-816 |
| F-06 | Business owner holds `cis-admin` (S245 Q-1 unanswered) | Low | **Decide** (tech lead with the business owner): keep admin with MFA (F-01) or move to a narrower group (`cis-content_lead` / reviewer view) | unchanged | — |
| F-07 | Test accounts on a personal mail domain in the customer-facing pools: 1 in external, 2 in partner | Low | **Remove** before the first real agency or traveller signs in, or move them to the E2E test mail domain (tech lead) | new | AA-1111 |
| F-08 | Repo-level GitHub secrets readable by a workflow on any branch: AA-CIS-Infra `TF_VAR_DB_PASSWORD`, `AA_CI_BOT_PRIVATE_KEY`; AA-Partner `E2EPORTAL*` (3); AA-CIS-App `GOLDEN_GUARD_KEY` | Medium | **Change**: move `AA_CI_BOT_PRIVATE_KEY` and the `E2EPORTAL*` set into environments with branch policy `main` (the repos are public now, so environment rules are free; the old "private repo" reason in the Infra workflow comments no longer holds); for `TF_VAR_DB_PASSWORD`, check whether Terraform still needs the master password (plan on branches reads it) or can drop it | changed (S245 F-10: `VERCEL_TOKEN` gone, rest still open, 2 more) | AA-878 |
| F-09 | AA-CIS-App repo secrets `E2E_ADMIN_USERNAME` / `E2E_ADMIN_PASSWORD`: no workflow on `main` reads them (legacy password E2E login) | Low | **Remove** (tech lead OK, then orchestrator deletes; register row to `deleted`) | new | AA-816 |
| F-10 | Secrets Manager grew from 29 live (S245) to 56; 0 of 56 rotate automatically | Low (Dev) | **Keep** for Dev (D-02/D-03); rotate before prod or on suspicion | unchanged (S245 F-4) | AA-880 |
| F-11 | Register drift `diff = 25`: 17 names unregistered, 7 Secrets Manager (3 tenant connector secrets, 2 rehearsal agency logins, studio viewer, TripPlanner tenant assertion key) and 10 GitHub (Infra `AWS_ACCOUNT_ALIASES`, `BEDROCK_ACCT_PAYER_ID`, `dev` / `dev-db-auto` `AWS_ROLE_ARN`, root `DOCS_SYNC_*` + `ci-hygiene` CI bot key, AA-Partner `e2e` assistant password + TOTP, AA-CIS-App `GOLDEN_GUARD_KEY`), 6 planned rows now present, 1 missing (`AA-CIS-Infra/prod AWS_ROLE_ARN`: moved to env `dev` by the AA-1023 rename), 1 Lambda env false positive (`STATE_KEY` of the admin-session digest is an S3 object key) | Low | **Keep** the secrets; update the register YAML + tables (no AWS change); add `STATE_KEY` to the checker's allow-list | new | AA-878 |
| F-12 | Secrets never read since creation or idle: one tenant CMS secret (created 20/10), one rehearsal agency login, `tripplanner/dev/lead-webhook-key` (08/11); the 3 legacy E2E admin logins last read 27/10 | Low | **Check consumer**, then remove the unused ones (DRY RUN → tech lead OK → delete); the legacy E2E logins go with S245 F-1/F-2 | new | AA-878 |
| F-13 | Vercel-era GitHub environments with no rule and nothing to deploy: `Preview` / `Production` in AA-CIS-App, AA-Booking, AA-TripPlanner-Web; `staging` in AA-CIS-App and AA-CIS-Infra | Low | **Remove** (tech lead OK; check each holds no secret first) | new | — |
| F-14 | DB effective reach, credential-column readers and staff rows measured (section 6.2): all 7 checks pass; findings F-20 to F-23 | — | None (closed by the 17/11 run-script) | closed | AA-1111 |
| F-15 | IAM live cross-check done (section 4.3): 1 IAM user (the base user) with MFA; its one access key is **132 days old** (past 90); it also holds five read-only managed policies; no role unused for 90 days | Medium | **Rotate** the base user's key (hand step with MFA); **decide** keep or trim the five read-only policies (tech lead) | changed (read live; key past 90 days) | AA-1111 |
| F-16 | GitHub: both members are org admins; members can create public and private repositories | Low | **Change** (tech lead, org owner setting): turn off repository creation for members; keep 2 admins (break-glass) | unchanged (S245 F-8 part 2) | — |
| F-17 | Terraform roots `accounts/aa365` and the acc3 root do not pin `allowed_account_ids` (acc1-bedrock and management do) | Medium | **Change** (AA-1111 scope, Infra PR, plan must show no change) | new (R44) | AA-1111 |
| F-18 | Agent role `DenyDangerous` has no NotResource exception for the E2E viewer secret | Low | Do it together with F-02 | unchanged (S245 F-12) | — |
| F-19 | Secrets of acc1 / acc3 not inventoried in this lane (acc1 should hold none since S278) | Low | Orchestrator lists names with the acc1 / acc3 profiles | unchanged (S245 F-14) | AA-878 |
| F-20 | `shared.admin_users`: 2 active rows still hold a password hash (the owner admin, Cognito-linked; the E2E viewer, never signed in), 5 inactive rows too (3 legacy E2E admins, 2 content). The CIS API takes Cognito sessions only (S247), so these hashes are dead credentials | Low | **Remove** the hashes (a reviewed DB Migrate run-script, DRY RUN count first, tech lead OK); disable the E2E viewer row and retire its secret `aa-cis/dev/e2e-test-viewer` if no workflow uses it; delete or keep the 5 inactive rows (tech lead) | new | AA-816 |
| F-21 | 81 SECURITY INVOKER functions are executable by PUBLIC (`booking` 67, `shared` 9, `gold_aa_internal` 3, `geo` 2); `crm` already revokes the PUBLIC default | Low | **Keep** (no table opens: invoker rights); optional hygiene: owners add `ALTER DEFAULT PRIVILEGES … REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC` like `crm_owner` | new | — |
| F-22 | Cross-app reads exist only through published objects: `cis_app` reads 12 Booking and 6 TripPlanner views, `booking` / `tripplanner` read the `catalog` contract, `tripplanner` reads `booking.v_from_prices` and inserts into `shared.llm_call_log` | Low | **Keep** (owner-granted contracts); list them as the allowed edges in a scheduled check so a new cross-app grant fails it | new (measured for the first time) | — |
| F-23 | `tripplanner.sessions` stores the guest token in clear next to its hash (both tagged `conf:credential`); anyone with `tripplanner`, master or migrator access can replay a guest session | Low | **Change** (TripPlanner owner migration): keep only the hash once the code reads the hash; check the code path first | new | — |
| F-24 | 9 inactive bridge-era `booking.staff_users` rows (never seen, never linked) | Low | **Remove** after a DRY RUN count (tech lead OK), or keep as history | new | AA-911 |

Questions for the tech lead: **Q-1** (again) business owner `cis-admin` or narrower (F-06)? **Q-2** IdP choice for
F-01: Cognito TOTP for admin groups, or Google IdP with 2-Step Verification (the company mail is not on Google
Workspace, so TOTP is the simpler path)? **Q-3** default agent role (F-02)?

## 8. Closed since the last review

| Finding (S245) | How it was closed | Evidence |
|---|---|---|
| F-5 Vercel readable secrets | All Vercel projects retired; no env var left | Vercel team 0 projects (17/11); S247 had already made `SENTRY_AUTH_TOKEN` / `TRIPPLANNER_API_KEY` sensitive |
| F-6 No `aa-cis-portal` project | Project and workflow deleted (AA-979, S256) | Session log S256; register row orphan-delete |
| F-7 Apply role reads every secret | Boundary Deny on `GetSecretValue` outside the Terraform refresh list + Deny on resource-policy edits of guarded secrets (AA-873, S261); `prod` env now has reviewer + branch policy | AA-CIS-Infra `accounts/aa365/cicd_split.tf` (`DenySecretValuesTerraformDoesNotRefresh`); env rules read 17/11. GitHub-side gap moved to env `dev`: F-03 |
| F-8 part 1 Apps on all repositories | All 5 installations on "selected repositories"; `notion-workspace` removed | `gh api orgs/<org>/installations` 17/11 |
| F-9 Org secrets not listable | Org Actions secrets: 0 | `gh api orgs/<org>/actions/secrets` 17/11 |
| F-10 part `VERCEL_TOKEN` ×3 at repo level | Removed with the Vercel retirement | Repo secret lists 17/11 |
| F-11 Vercel `ADMIN_*` / `INTERNAL_API_KEY` | Deleted (S247) and projects retired | Session log S247; no project |
| F-13 Real-data dump on the laptop | The local `docs/backups/2026-09-16` folder is gone (the folder now holds only AA-1004 / AA-1113 notes); the S3 copy was not re-verified in this lane | Local listing 17/11 |
| F-1, F-2 Legacy full-admin E2E password accounts | The 3 legacy E2E admin rows in `shared.admin_users` are inactive (their password hashes remain: F-20) | Run-script 17/11 (section 6.2) |
| AA-1111 fork-PR approval | Found already on: `all_external_contributors` on the org and on all 7 repos, so this AA-1111 item is done (no change made) | `gh api …/fork-pr-contributor-approval` 17/11 |


## 9. Next time

1. Run the drift check first with every inventory (`gh api` lists work where `gh secret` is blocked for subagents);
   aim for `diff = 0` before the review.
2. Let the orchestrator run section 4.3 and the DB run-script at the start, so the subagent lane only writes up.
3. Turn the stable checks into scheduled guards: WORKFORCE admins without MFA (after F-01), E2E identities in admin
   groups, repo-level secrets outside the allow-list, GitHub environments without rules that hold a secret.
4. Add the users of the partner and external pools by label once real agencies and travellers arrive (the pilot).
5. Update the SEC-05 table in `docs/security/README.md` with this record.
