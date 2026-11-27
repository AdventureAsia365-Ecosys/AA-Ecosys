---
id: SEC-01
title: Security baseline
description: Every security control of the ecosystem on acc2 and GitHub, with its live status, the evidence and the open issue; read before a security review or a go-live check.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-cis-infra]
last_reviewed: 2026-11-01
review_every_days: 90
related: [SEC-02, SEC-03, SEC-05, SEC-06, OPS-04, OPS-10, AA-873, AA-874, AA-875, AA-876, AA-878, AA-879, AA-895, AA-829, AA-1022, AA-1162]
---

# Security baseline

One row per control. **Status** is what runs on Dev today, read live on 2026-10-19 and re-read on 2026-11-01 for the
rows that changed since; the code and supply chain rows and the merge rights row were re-read on 2026-11-21 (AA-1162,
GitHub API read-only: rulesets, branch protection, code scanning default setup; workflows on each default branch) (AWS read-only with `--profile aa365-admin --region us-west-1`, GitHub API read-only). The row
links the evidence or the issue that closes the gap. This page does not repeat the work of those issues; it points at
them.

What this page is not: it is the list of controls that exist, not a Statement of Applicability. It maps to no
ISO/IEC 27001 Annex A control and no SOC 2 criterion, and no certification is claimed. That mapping is made only when
the first customer security questionnaire arrives (trigger T-QUESTIONNAIRE in the backlog trigger table, S261
architecture review N17).

Status values: **in place** (works today), **partial** (works, with a named gap), **gap** (missing, issue
open), **by decision** (not done because the tech lead decided so, with the trigger that reopens it).

> [!NOTE]
> Dev holds test data only (S241 D-01). Controls marked "before prod" are blockers for the go-live checklist
> (G-12, AA-880), not for Dev work.

## Summary

| Area | In place | Partial | Gap |
|---|---|---|---|
| Edge and network | WAF on the ALB, SG per caller, private DB, SSRF-safe outbound client, S3 gateway endpoint | API Gateway edge hardening (AA-876) | — |
| Identity and access | Human MFA, GitHub org 2FA, CI OIDC main-only (subject + `ref`), CI role split | Cognito cutover (AA-816), agent role optional | — |
| Data stores | RDS encryption, TLS, no public endpoint, Redis AUTH/TLS/at-rest | DB role split and RLS FORCE for CIS (X1) | — |
| Detection and logs | Multi-region CloudTrail with KMS, REJECT-only flow logs, WAF logs of acted-on requests, 365/30-day retention (Dev logs 30 days since S263), alarms, Access Analyzer, S3 account BPA, security alert rules incl. Identity Center admin sessions | — | — (GuardDuty off by decision) |
| Code and supply chain | Secret scanning + push protection on all six repos, gitleaks PR and full-history scans on all six, no deletion and no force-push on all six default branches, Dependabot alerts everywhere, CodeQL on all six repos, failing Trivy image gate in CIS, Booking and Partner, Infra actions pinned to commit SHAs | Human review of risky PRs (agent reviews only until the pilot, AA-1162), TripPlanner has no image gate | — |
| Secrets | Secrets Manager per app, register with drift check (`diff = 0`, AA-878) | Rotation is manual by decision (D-02/D-03) | — |

## Edge and network

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| WAF | Regional web ACL `aa-cis-dev-waf` on the shared ALB and, since AA-1092, on the CIS and Booking REST API stages (2 stage associations, read 2026-11-25). Rules: AWS managed common rule set, VPC-link internal allow, rate limit, geo block. WAF logs on Dev: 30 days, only requests a rule blocked, challenged or counted (logging filter; allowed requests are dropped). Prod: 365 days. Every block, the managed common rule set included, answers a custom response with the security headers (HSTS, nosniff, a deny-all CSP, Permissions-Policy) and a static text body (AA-1111). Accepted: the ALB's own `Server: awselb/2.0` header on a response it builds from a WAF block cannot be removed (no ALB option; ZAP Low, no version disclosed). | partial | INF `docs/waf-count-review.md`, `modules/waf` (S263 alert diet, AA-1025; block responses AA-1111, guard INF `tools/terraform/tests/test_aa1111_security_headers.py`). Login rate limit, API throttling, CORS and security headers: AA-876 |
| Outbound requests | Server-side fetches of tenant-supplied URLs go through the SSRF-safe client `safe_http`. | in place | AA-875 (Done) |
| S3 from private subnets | S3 gateway endpoint on the private route table: same-region S3 (ECR layers included) stays on the AWS network instead of the NAT instance; default endpoint policy, bucket policies unchanged. The db route table has no route out of the VPC. | in place (after the AA-1022 apply) | AA-1022; INF `modules/vpc/main.tf` |
| One security group per caller | RDS admits only `cis-api`, `cis-worker`, `booking-api`, `crm-api`, `tp-lambda`, `db-migrate`; Redis only the two CIS groups (EFS was removed in S257). The shared app group is gone (X1 S14). | in place | Root ADR [0004b](../adr/0004b-per-app-security-groups.md); INF `accounts/aa365/app_security_groups.tf` |
| Egress | Every app group still allows all outbound traffic (17 of 20 groups, read 2026-11-27); the narrowing to TCP 443 + the data-store ports (and SMTP for `crm-api`) and a domain allow-list on the NAT instance are approved and open. | gap (approved, 0 USD) | AA-1185 scope 8 |
| NAT instance patching | State Manager association runs `AWS-RunPatchBaseline` (Install, reboot only if needed) on the NAT instance every Sunday 21:00 UTC; the root volume is encrypted at its next deliberate replacement. | in place after the AA-1185 apply | AA-1185; INF `accounts/aa365/security_account_defaults.tf` |
| Load balancers | ALB and VPC-link NLB have deletion protection; the ALB drops header fields with invalid names (`drop_invalid_header_fields`). The default execute-api endpoints of the CIS and Booking REST APIs and the TripPlanner HTTP API are switched off (Infra root variable `api_default_endpoints_disabled`, S296): they answer 403 (REST) or 404 (HTTP API), so the WAF, geo rules and logs in front of the custom domains cannot be bypassed; every caller uses `api-cis.`, `api-booking.` or `api-tripplanner.<zone>`. | in place after the AA-1185 applies | AA-1185; INF `modules/alb/`, `modules/api_gateway/`, guard INF `tools/terraform/tests/test_aa1185_execute_api_off.py` |
| Mail domain and certificates | DMARC `p=none` with aggregate reports (`rua`) to the watched ops inbox (tighten after 2–4 weeks of reports); CAA at the apex allows only the Amazon CAs (every certificate is ACM). | in place after the AA-1185 apply | AA-1185; INF `accounts/aa365/ses.tf`, `dns.tf` |
| Vulnerability contact | `/.well-known/security.txt` (RFC 9116, expiry under a year, a test fails when it is due) on the CIS admin, Booking admin, CRM web (all its hosts) and TripPlanner hosts; TripPlanner's AI label links to "Report AI content". | in place after the AA-1185 deploys | AA-1185 |
| Private data stores | RDS `publicly_accessible = false`; humans reach the DB only through ECS exec over SSM (S3-mediated script runner), never SSH. | in place | DM-8.8; `skill/aa-cis-schema` (ECS exec pattern) |
| VPC flow logs | Four flow logs, REJECT records only, to CloudWatch Logs, 30 days on Dev (S263 alert diet); prod 365 days. Accepted traffic is not recorded on Dev: rejected connection attempts stay visible, a full traffic trace for an investigation means switching the flow logs back to ALL for the time of it. | in place | AA-872 (D-09); AA-1025 (INF `accounts/aa365/diagnostics.tf`) |

## Identity and access

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| Human AWS access with MFA | `aa365-admin` and `default` assume one Terraform-managed admin role with an MFA device (12-hour session, AA-1004). `default` points at acc2 since AA-517. Profiles: account map in `docs/onboarding.md` (AA-897). | in place | AA-517. IAM users and access keys are listed in the quarterly access review (SEC-05), not here |
| GitHub organisation 2FA | Required for every member (organisation setting read 2026-10-19). | in place | AA-867 |
| CI trust: main only | Every GitHub OIDC role pins the audience and an exact immutable subject of one repo. Every role whose subject is a GitHub environment (CIS deploy, Terraform apply, DB auto-apply, e2e mail reader, Booking deploy, CRM deploy, CRM scrub corpus) also requires `ref = refs/heads/main`, so "main only" does not rest on the environment's branch policy alone; TripPlanner's subject is the main ref itself; the read-only plan roles accept `pull_request` and the main ref. The Terraform apply environment is named `prod` but applies Dev; ADR 0012 (accepted S257) decision 6 renames it to `dev` before any prod role exists (AA-880, D-16). Guard: INF `tools/terraform/tests/test_aa1022_hardening.py`. | in place | AA-866, AA-1022; INF `accounts/aa365/cicd_split.tf`, `booking.tf`, `crm_app.tf`, `crm_scrub.tf` |
| CI least privilege | Three roles: plan (read only + state lock + named secrets), apply, CIS app deploy. Bootstrap objects (the roles' own policies, OIDC provider) are applied locally with MFA. The apply role still carries ten broad AWS managed policies (one is `SecretsManagerReadWrite`: it reads every secret, the RDS master included; access review F-7), and its inline policy is at 9,559 of 10,240 characters. | partial | AA-806; INF `docs/ci-role-split.md` |
| IAM policy validation | The required Infra plan check runs IAM Access Analyzer `ValidatePolicy` on every policy document the plan creates or changes; ERROR and SECURITY_WARNING fail unless an allow row gives a reason. | in place | AA-1185; INF `tools/terraform/iam_policy_validate.py` |
| Staff and customer identity | Cognito on acc2 (ADR 0006): staff pool with e-mail code sign-in, self sign-up refused, no-group deny; break-glass account with TOTP and a token-issued alarm; alarm on `AdminCreateUser` with a caller-set password (ADR 0006a A8). The legacy admin login is still on until the cutover. | partial | Root ADR [0006](../adr/0006-ecosystem-identity.md), [0006a](../adr/0006a-identity-phase1-amendments.md); AA-854 (done), AA-816 (cutover), AA-703 |
| Agent guardrails | Subagents cannot push, merge, deploy, apply Terraform, write secrets or call IAM (`.claude/hooks/subagent-guardrails.sh`, with its test script); an MCP guard hook blocks their GitHub, Linear, Notion, Vercel and Jira writes. Agents treat files, Jira and web content as data. The committed `.claude/settings.json` denies Claude Code reads of `~/.aws/**` and `~/.config/gh/**`, `gh auth token` and `aws configure get` (root #120, U-04 step 1; deny-only by the tech lead's choice, no ask rules in the dev phase). A narrow agent role (`aa-cis-dev-agent-session`, AA-730) exists but is not mandatory yet. | partial (by decision) | D-15: the mandatory agent role is a prod trigger (U-53), with the GitHub App for agents (U-25) |
| Merge rights | Dev phase: the orchestrating agent merges its own PRs after every check is green (risky PRs after an independent agent review, which the aa-agent App posts on the PR as a comment review: `tools/github/post_agent_review.py`); subagents never merge (hook). An agent review is not a human review. From the first pilot with real data (tech lead decision D4, S286; at the latest the first prod environment or paying tenant) the tech lead approves every risky PR (Terraform/IAM, migration, auth/permission, CI/workflow/secret, data deletion) before merge: the merge gate refuses such a PR without a human APPROVED review of its head once the switch in `tools/github/change_control.json` is on (off today, built and tested). | partial (human approval switched off until the pilot) | D-13; D4 (S286); DM-11.5 (data standards v1.1); AA-1162; `skill/aa-ship/SKILL.md` §1 |
| Quarterly access review | Roles, grants, IAM roles that can read each DB secret, Cognito staff users, GitHub and Vercel members. Record in `docs/audits/<date>-S<nnn>-access-review/`. First review done 2026-10-20; live IAM user/key check still to add (F-15). | in place | DM-8.10; [2026-Q4 record](../audits/2026-10-20-S245-access-review/README.md) (AA-878); cadence AA-838 |

## Data stores

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| RDS at rest and in transit | Storage encrypted; parameter `rds.force_ssl = 1`; deletion protection on; 14-day automated backups (root ADR 0019 d16); slow-query log at 500 ms; `postgresql` log export kept 365 days. | in place | C4.2a; AA-872 |
| DB roles per app | Booking and TripPlanner objects owned by NOLOGIN owner roles; migrations run as `db_migrator` from their own task definition. CIS runtime split (`cis_owner` / `cis_app`) is X1 wave 4. | partial | DM-8.1, DM-8.2; AA-852, AA-860 |
| Tenant isolation (RLS) | RLS template on tenant tables, scoped to the runtime role; new apps use FORCE from day one; CIS tables get FORCE after the role split. The isolation probe (INF `db-isolation-probe.yml`) runs on a schedule and after each apply. | partial | DM-8.4; AA-817 D2; U-16 |
| Tenant pool flags | Unreadable flag means tenant pool; `"false"` means admin pool; an emergency environment switch exists. This is a security control with no remove-by date. | in place | D-12; `docs/ops/feature-flags.md` (AA-892) |
| Redis | `aa-cis-dev-cache`: AUTH token, in-transit encryption and at-rest encryption all on (read 2026-11-01). Reachable only from the CIS api and worker groups. | in place | AA-874 |
| Real data on laptops | The 2026-09-16 real-data dumps were moved off the laptop; `docs/backups/` is empty (checked 2026-11-01) and ignored by git. | in place | DM-6.10; AA-829 (Done) |
| EBS defaults | EBS encryption by default on (us-west-1) and snapshot Block Public Access `block-all-sharing`. | in place after the AA-1185 apply | AA-1185; INF `accounts/aa365/security_account_defaults.tf` |

## Detection and logs

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| CloudTrail | Trail `aa-cis-dev-trail`: multi-region, management events read and write, global service events, log file validation, KMS key; trail bucket versioned with Object Lock (read 2026-11-01). | in place | AA-286, AA-873 (S255) |
| GuardDuty | Detector code ready behind a switch, off (about 15-20 USD/month). Trigger: before prod or the first paying tenant. | by decision | AA-873 |
| IAM Access Analyzer | External-access analyzer `aa-sec-dev-external-access` active; intended findings archived by rule; a new ACTIVE finding e-mails the alerts topic. | in place | AA-873 (S255, S256) |
| AWS Health events | Issues, scheduled changes and account notifications (us-west-1, and us-east-1 through the forwarder) mail the alerts topic, ticket severity. | in place after the AA-1185 apply | AA-1185 |
| Admin group changes | Adding a WORKFORCE user to `cis-admin`, `booking-admin` or `crm-platform-admin` mails the alerts and page topics (page severity); enabling a staff user mails the alerts topic only (ticket severity: the CIS Staff page also sends it on routine Reset and Sync). Check each against the access register. | in place after the AA-1185 apply | AA-1185 |
| S3 Block Public Access | Account-level setting with all four flags on (read 2026-11-01), plus bucket-level settings. | in place | AA-873 (S255) |
| Security alert rules | EventBridge rules on CloudTrail to the alerts topic: trail tampering, security-group changes and IAM changes outside the Terraform apply role, any root activity, and every Identity Center session on an administrator permission set (`AssumeRoleWithSAML`, read-only events included; Identity Center records it in us-east-1, forwarded to us-west-1). The e-mails carry no role ARN or account ID for the Identity Center rule. Live pattern check: INF `tools/terraform/sec_alert_check.py`. | in place (Identity Center rule after the AA-1022 apply) | AA-873, AA-1022; INF `security_baseline.tf`, `security_sso_signin.tf` |
| Admin session digest | After each Identity Center administrator session, a second e-mail lists what the session did: counts per service, every delete and write call (resource names only), read-only calls by count; session name cut to the user's local part, no account ID, ARN or full e-mail address. Hourly Lambda reading CloudTrail Event history in the region SCP allow-list (us-east-1, us-west-1, us-west-2; calls to SCP-exempt services in other regions are not covered), oldest calls first, sent once the session expired or was idle 60 min; later calls, or the rest of a run that ran short, send a continued digest. Live check: INF `tools/terraform/sec_alert_check.py --digest --digest-preview`. | after the apply | AA-873; INF `security_sso_session_digest.tf` |
| Security Hub | Not enabled (paid per check). | by decision | Revisit with the prod checklist (AA-880) |
| Log retention | Security logs 365 days (ECS exec sessions, `postgresql`, identity Lambdas; VPC flow and WAF logs 30 days on Dev since the S263 alert diet, AA-1025, 365 days on prod); application logs 30 days (`/ecs/aa-cis-dev`, `/ecs/aa-booking-dev`, TripPlanner Lambdas, API Gateway execution logs). | in place | D-09, AA-872. Data standards C4.2b still says 14 days: fixed in v1.1 (N-1) |
| Alarms | Since the S263 alert diet (AA-1025) CloudWatch keeps only what the apps cannot see; state alarms (no healthy task, RDS, NAT, SES rates, backup copy age) e-mail on ALARM and OK, event alarms (Lambda errors, break-glass token, KMS decrypt anomaly) on ALARM only, through the alerts topic; the RDS instance events rule mails when the shared database is down, stopped or failing; the in-app checks of CIS, Booking and AA-Partner mail the same topic. Each description carries its runbook link (AA-893). Break-glass secret reads and `AdminCreateUser` with a password alert too. Cost anomalies go to the same topic (AA-896). | in place | INF `accounts/aa365/observability*.tf`, `identity_alerts.tf`, `cost_anomaly.tf`; OPS-07 |
| Error tracking | Sentry on the CIS backend. Booking and TripPlanner: JSON logs only. | partial | AA-870 (done); AA-871 |

## Code and supply chain

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| Branch rules, app repos | AA-CIS-App, AA-Booking, AA-TripPlanner-Web: ruleset "main: no force-push, no deletion (AA-867)"; AA-Partner: ruleset "default branch: no force-push, no deletion (AA-1162)". CIS, Booking and Partner also merge through a merge queue (ruleset "main: merge queue (AA-993)"). Required checks come from branch protection on `main` (read 2026-11-21): CIS 10, Booking 9, Partner 11, TripPlanner 6; no required approving review (Dev phase, see Merge rights). | in place | AA-867; AA-993; AA-1162 |
| Branch rules, root and Infra | Both repos are public since 2026-10-22 (ADR 0014 amendment). AA-CIS-Infra: ruleset "main: PR and required checks (AA-993 I1)" (no deletion, no force-push, PR required, 5 required checks, 0 approving reviews). AA-Ecosys (root): ruleset "default branch: no force-push, no deletion (AA-1162)" and ruleset "master: Catalogue guard required (AA-1106)" (one required check); other checks are read by the merge tool, which refuses any red one (DM-11.5). | in place | ADR 0014 amendment; AA-993; AA-1106; AA-1162; D-14 |
| Public-repo identifiers | The docs lint fails account IDs, ARNs with an account, VPC ids, API Gateway hosts, user-pool IDs and e-mail addresses outside the company and test domains in the docs pages of the root and Infra repos, load balancer ids too (error mode in both since S296; the app repos already fail them). Not covered: the journals (sessions, audits), the agent files and the account IDs inside Infra Terraform (`terraform.tfvars`, cross-account ARNs). | partial | AA-1185 |
| Secret scanning | All six repos are public and have GitHub secret scanning and push protection on (`security_and_analysis` read 23/10/2026, S248; re-read 2026-11-01, AA-Partner included). AA-CIS-Infra and AA-Ecosys (root): `secret-scan.yml` runs gitleaks on every PR (lines the PR adds, plus a squash preview of the PR; `pull_request_target`, so GitHub always runs the base branch's copy and a PR cannot change the check that judges it) and `secret-scan-history.yml` a **full-history** job (every commit of every branch, tag and PR head, nightly + on push to the default branch) with a baseline of pinned fingerprints, so it is green today and red on any new finding. Both use the same `.gitleaks.toml` rules (the gitleaks v8.30.1 default rules copied without gitleaks' global path allowlist, which skipped text files such as `.svg` or `node_modules/`, plus the repo rules), incl. `credential-key-literal`: a `*password` / `*secret` / `*api_key` / `*_token` key with a literal value in tfvars, `.env*`, JSON or YAML (the shape an external scanner caught in old Infra history on 22/10). The PR scan reads its rules and baseline from the base commit; changing them, or adding an inline allow comment for the scanner, needs the label `secret-scan-baseline-reviewed`, added after the last push (any later push, reopen or label change removes it; a change to either secret scan workflow, `.github/CODEOWNERS` or any `.gitattributes` needs the label too); both jobs read merge commits as remerge diffs, renamed files whole and every file as text, and fail on an octopus merge or a git error; a red result means the value is public, so it is rotated even if force-pushed away; the history job also scans every PR head (`refs/pull/*/head`). AA-Booking CI: gitleaks (PR only). The four app repos run their own `secret-scan.yml` (PR) and `secret-scan-history.yml` (full history) too (read 2026-11-21). | in place | AA-981 (S248); AA-867; precondition before any private→public switch: [ADR 0014](../adr/0014-repo-visibility-and-github-plan.md) amendment 2 |
| Dependency alerts | Dependabot alerts and security updates on in all six repos; `dependabot.yml` in CIS, Infra, Booking, TripPlanner and Partner (AA-895), each with a weekly github-actions entry (CIS since AA-1022). Process and open alerts: [vulnerability management](vulnerability-management.md). | in place | AA-867, AA-895, AA-1022 |
| Action pinning | AA-CIS-Infra: every `uses:` in its workflows names a full commit SHA with the release tag in a comment; guard INF `tools/terraform/tests/test_workflow_action_pins.py`. App repos: mostly release tags, updated by Dependabot. | partial | AA-1022 |
| CI security gates | CIS, Booking and Partner: `pip-audit` failing gate, Trivy image scan **failing** on fixable CRITICAL/HIGH (`exit-code: 1`, `ignore-unfixed`; an accepted finding needs a `.trivyignore` line with an expiry and a reason, checked by `check_trivyignore.py`) and a CycloneDX SBOM (syft) per image; Partner scans both its images (api and web) and runs `npm audit` on the web app. TripPlanner: `pip-audit` failing gate on the Lambda requirements, no Trivy image scan. Read on each default branch 2026-11-21. | partial (TripPlanner) | AA-868; AA-879 |
| Code scanning (CodeQL) | GitHub CodeQL default setup, weekly and on PRs, analyses all six repos (Python, JavaScript/TypeScript, Actions). Root and AA-CIS-Infra were first analysed on 2026-11-21 (completed analyses of all three languages on the default branch, read the same day); free while the repos stay public. | in place | AA-1162; S287 compliance advisory |
| Public repos content | Rule: no account IDs, ARNs, network IDs, inventories or security reports in public repos (SEC-06, D-25). **Scrubbed and enforced (AA-902, S244, 19/10/2026):** HEAD of all three public repos holds 0 real account IDs (`git grep` on `origin/main` after CIS #854, Booking #45, TP #105; only obviously fake 12-digit test values remain). Code that needs a satellite account reads `BEDROCK_ACCT_PRIMARY` from the task / Lambda environment (AA-CIS-Infra #221; the fallback variable `BEDROCK_ACCT_FALLBACK` was removed by AA-998); bucket names come from `BRONZE_BUCKET` or STS; the TripPlanner deploy role ARN is a repo secret. A blocking resource-ID check (`.github/scripts/check_resource_ids.py`) runs in CI: CIS Lint, Booking Security Audit, TripPlanner Backend (pytest); AA-Partner, created after AA-902, runs the same blocking check in its CI Security Audit job (step "No literal AWS resource IDs", `ci.yml` on `main` `923e206`, read 25/10/2026). Proven on 19/10 with throwaway PRs that add an ARN with a 12-digit account: CIS #857, Booking #47, TripPlanner #108 each failed with 1 finding (closed). Git history keeps the old IDs; account IDs are not credentials, so no history rewrite (S244). | in place | SEC-06 in [`STYLE.md`](../STYLE.md#where-a-page-may-live-sec-06); D-25; AA-902 |

## Secrets

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| Storage | Secrets Manager, one secret per role and purpose, named `<app>/<env>/<purpose>` (legacy CIS names kept). DM-8.6 requires each execution role to read only its own secrets; the register checks it. TripPlanner Lambdas read their secrets by name, not from Lambda environment values (INF #207). | in place | DM-8.6 |
| Register | Owner, readers, rotation class per secret; orphan cleanup (4 Secrets Manager orphans deleted 19/10 with the 30-day window, 2 GitHub orphans deleted 17/10). Drift check with AWS, Lambda env, GitHub and Vercel inventories: `diff = 0` on 2026-10-20. Org-level GitHub secrets not listable with the current token. | in place | AA-878; [`secrets-register.md`](secrets-register.md) |
| Rotation | Rotate when exposure is suspected, at go-live and after any break-glass use. No fixed 90-day cycle on Dev. | in place (by decision) | D-02, D-03, DM-8.9 |
| Before any write | `aws sts get-caller-identity --profile aa365-admin` first (two wrong-account writes happened). | in place | DM-8.7, AA-517 |

## How to re-check

Run these read-only commands when you review this page. Each costs nothing.

```bash
aws guardduty list-detectors --profile aa365-admin --region us-west-1 --output text
aws accessanalyzer list-analyzers --profile aa365-admin --region us-west-1 --query "analyzers[].name" --output text
aws s3control get-public-access-block --account-id <acc2-account-id> --profile aa365-admin --region us-west-1
aws cloudtrail describe-trails --profile aa365-admin --region us-west-1 --query "trailList[].{name:Name,multi:IsMultiRegionTrail,validation:LogFileValidationEnabled,kms:KmsKeyId}"
aws events list-rules --name-prefix aa-sec-dev --profile aa365-admin --region us-west-1 --query "Rules[].[Name,State]" --output text
aws ec2 describe-vpc-endpoints --profile aa365-admin --region us-west-1 --query "VpcEndpoints[].[VpcEndpointType,ServiceName,State]" --output text
aws elasticache describe-cache-clusters --profile aa365-admin --region us-west-1 --query "CacheClusters[].{id:CacheClusterId,transit:TransitEncryptionEnabled,rest:AtRestEncryptionEnabled,auth:AuthTokenEnabled}"
aws wafv2 list-web-acls --scope REGIONAL --profile aa365-admin --region us-west-1 --query "WebACLs[].Name" --output text
aws logs describe-log-groups --profile aa365-admin --region us-west-1 --query "logGroups[].[logGroupName,retentionInDays]" --output text
```

Public repo content (run in each public repo after `git fetch origin main`; prints the files that hold an account ID):

```bash
git grep -l -E '<acc1-account-id>|<acc2-account-id>|<acc3-account-id>' origin/main
```

The account IDs are in the account map (`docs/onboarding.md`). acc1 (a personal account) was removed from the
ecosystem on 2026-10-28 (AA-998) and serves only Bedrock since S278 (AA-1095); its ID stays in the pattern so it never comes back into a public repo. GitHub settings: repository Settings →
Code security, and Settings → Rules; or the read-only API calls listed in
[vulnerability management](vulnerability-management.md#monthly-triage).

Update a row when its issue ships, set `last_reviewed` to the day you re-ran the checks, and say so in the PR.
