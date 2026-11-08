---
id: SEC-04-dpa-annex2
title: "DPA Annex 2: technical and organisational measures (draft v0.4)"
description: "Annex 2 of the partner-agency DPA (and SCC Annex II): each security measure marked Live with its code, Terraform or audit evidence and the data-standard rule or ADR it implements, or Planned with the gate it must pass; no measure is claimed that does not run."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-crm-api, aa-crm-web, aa-partner-portal, aa-cis-api, aa-cis-worker, aa-booking-api, aa-cis-dev-db]
last_reviewed: 2026-11-08
review_every_days: 30
related: [SEC-04-dpa-agreement, SEC-04-dpa-annex1, SEC-04-dpa-annex3, ARCH-08-data-management, SEC-08-s268-crm-security-review, OPS-03-pilot-tenant, AA-820, AA-969, AA-970, AA-1004, AA-1035, AA-1038]
---

# DPA Annex 2: technical and organisational measures (draft v0.4)

> [!WARNING]
> Draft for counsel, not legal advice. Part of the [Data Processing Agreement](dpa.md); also Annex II of the SCCs
> ([Annex 4](dpa-annex-4-transfers.md)). This annex takes over the DPA technical annex of AA-970 (paused under ADR 0019
> d15).

**How to read it.** **Live** = runs on Dev on 2026-11-06 (M-8, M-9b, M-9c and M-12 re-checked on 2026-11-08), with the evidence named (repo and file on `main`, a pull
request, the live schema dump, an audit folder or a session log in [`docs/sessions/`](../sessions/)). **Planned** = not running; the gate says when it must exist. Rules are the data
standards ([Part B, data management](../architecture/data-standards/02-data-management.md)) cited as DM-n.n, and the
ADRs in [`docs/adr/`](../adr/). Repos: CIS = AA-CIS-App, BK = AA-Booking, CRM = AA-Partner, INF = AA-CIS-Infra.
AA promises the Live measures; the Planned ones are listed so the Agency knows what is not there yet.

**What changed in v0.4 (2026-11-08).** M-8: the Trip Planner's web rules run in the regional WAF web ACL in front
of the load balancer since its move to AWS ECS (AA-1038, session S272), so the CloudFront-scope WAF listed as
Planned is no longer planned. New §0 maps the seven themes of the measures (hosting region, encryption, access control, tenant isolation, personal data before a model call, retention, incidents) to the rows below, and new §3 lists
every point that needs counsel or the business owner. New M-9b and M-9c state how the Content studio and Booking B2B
keep one agency's data apart from another's (v0.3 named only the CRM's database isolation): the Content studio is
isolated by row-level security for its tenant database role on the routes moved to it and by application code on the
rest, Booking B2B by application code only; both are new §2 item 8. M-12 re-read on AA-CIS-Infra `main`: staff MFA is
still optional. No other measure changed.

**What changed in v0.3 (2026-11-06).** The five pilot safeguards of ADR 0019 d16 (M-25) moved from Planned to Live
(AA-969, closed in session S269); automated backups are 14 days (M-29, M-30 merged into it); M-13 names the staff
roles and the tenant scope that went live with AA-1035 (closed in session S270); M-37 records the load test before
real data; §2 lists the gaps left. v0.2 was root PR #546 (2026-11-05).

## 0. At a glance

The seven themes of the technical and organisational measures, and the measures below that carry them. A theme is
only as strong as its weakest Live row; the gaps are in §2.

| Theme | What AA commits to | Measures |
|---|---|---|
| Hosting region | Agency Personal Data stored in one AWS region, us-west-1 (United States); the content AI stages may use cross-region inference, a stage that may carry personal data is held to US deployments | M-1, M-19 (and [Annex 3](dpa-annex-3-subprocessors.md) "Where") |
| Encryption | At rest (database, storage, per-agency CRM field keys in AWS KMS) and in transit (HTTPS everywhere, TLS required on every database connection) | M-2 to M-6 |
| Access control | Agency users: invitation-only partner sign-in pool with MFA required. AA staff: the Cognito WORKFORCE pool, admin-created accounts only, one-time e-mail codes, deny-by-default roles with a per-agency scope (staff MFA optional today, §2 item 1). No personal database logins; per-app database roles; secrets per app | M-7, M-11 to M-17 |
| Tenant isolation | CRM: row-level security forced on every CRM table with one tenant policy; no other AA app holds a grant on the CRM schema; a test refuses any other database access path. Content studio: the agency comes only from a session minted from an active membership; row-level security for the tenant database role on the routes moved to it, application-level scoping on the other routes and on the membership and account tables. Booking B2B: application-level scoping by the agency the CRM names, no row-level security (§2 item 8) | M-9, M-10 (CRM), M-9b (Content studio), M-9c (Booking B2B) |
| Personal data before a model call | CRM: personal data scrubbed in three passes before any model call, a failed scrub refuses the call. Content studio and AA content stages: no identifying personal data in prompts, by rule, with the `pii` stage class enforced by the database and the gateway. AI call records keep no prompt or output text | M-18 to M-21 (Trip Planner gap: §2 item 5) |
| Retention | Windows per table in the DM-7.1 retention table, enforced by owner jobs (first run of each kind under DRY RUN); a table whose window is still proposed keeps its rows until the window is approved (Annex 1 says which); erasure and offboarding with a receipt; backups 14 days | M-29, M-31, M-32 ([Annex 1](dpa-annex-1-processing.md) "Retention" per app) |
| Incident handling | Severities, a SEV1 for any exposure or loss of personal data, the business owner within 30 minutes, affected agencies within 2 hours, a written review; audit trails in every app and AWS CloudTrail | M-23, M-24, M-26 (DPA clause 8) |

## 1. Measures

### Hosting, network and encryption

| # | Measure | State | Evidence | Rule |
|---|---|---|---|---|
| M-1 | All Agency Personal Data is stored in one AWS region, us-west-1. Each agency account carries a data region field, `us` by default | Live | INF `modules/rds/main.tf`; `shared.tenants.data_region` (dump) | ADR 0019 d1, d12 |
| M-2 | Database encrypted at rest; deletion protection; a final snapshot if it is ever deleted | Live | INF `modules/rds/main.tf`: `storage_encrypted = true`, `deletion_protection = true`, `skip_final_snapshot = false` | DM-9.1 |
| M-3 | **CRM field encryption with a key per agency.** Every personal field is encrypted (AES-256-GCM) with a data key that belongs to one agency and one purpose; the keys are generated and wrapped by AWS KMS (key rotation on) and never stored in the clear; exact search uses blind indexes, not plaintext; a value of another agency does not open and the refusal is audited | Live | CRM `app/vault/`, CONTEXT "Field encryption"; `crm.tenant_key.wrapped_dek` (dump); INF `modules/environment/crm_data.tf` (`enable_key_rotation = true`) | DM-6.8; ADR 0008a |
| M-4 | CRM documents and exports are encrypted with the agency's key before they reach storage, and the bucket adds its own KMS encryption; the stored file's SHA-256 is checked before it is opened | Live | CRM `app/documents/`, `app/portability/exports.py` | DM-6.8 |
| M-5 | Crypto-shredding: offboarding destroys the agency's keys and checks that a sealed test value no longer opens | Live | CRM `app/lifecycle/offboarding.py`, `KeyProvider.destroy` | DM-6.8 |
| M-6 | Encryption in transit: HTTPS on every public endpoint; the database refuses non-TLS connections and every app connects with TLS required | Live | INF `modules/rds/main.tf` parameter `rds.force_ssl = 1` | DM-8.8 |
| M-7 | The database has no public endpoint; humans reach it only through audited AWS Systems Manager sessions, never SSH, and no person has a personal database login | Live | INF `modules/rds/main.tf` (`publicly_accessible = false`); runbook `docs/ops/runbooks/ecs-exec-s3-mediated.md` | DM-8.8 |
| M-8 | Web application firewall rules (AWS WAF, regional) in front of the APIs, the load balancer and the sign-in pages; a request-body ceiling and fair per-agency request slots in the CRM | Live | INF `modules/waf/main.tf` (since AA-1038, session S272, also the three Trip Planner web rules: a per-IP rate limit, a rate limit on the paths that call a model or send, and a browser challenge on the planner pages, each scoped to the Trip Planner host and to requests that came through AA's CloudFront), `accounts/aa365/identity_partner.tf`; CRM `app/bodylimit.py`, `app/tenant_gate.py` (S268 review F1, F2) | ADR 0019 d23 (the Trip Planner rules sit in this regional web ACL instead of a CloudFront-scope one: tech-lead decision on cost, S272) |

### Access control

| # | Measure | State | Evidence | Rule |
|---|---|---|---|---|
| M-9 | **Agency isolation in the CRM database.** Every CRM table has row-level security forced on, with one tenant policy; request code reaches data only through a tenancy context that checks the user's membership on every request; a static test refuses any other database access | Live | CRM CONTEXT "Tenancy and data rules", `api/tests/unit/test_code_rules.py`, `test_every_crm_table_follows_the_base_template` | DM-8.4, DM-6.8 |
| M-10 | No other AA app can read the CRM: no AA app role holds a grant on schema `crm`, checked by the isolation probe (every AA app role gets a permission error on `crm`) | Live | `docs/database/schema-ownership.md` (`crm` row); DM-6.8 enforcement column | DM-6.8, DM-8.3 |
| M-9b | **Agency isolation in the Content studio (CIS).** The agency never comes from the request: a Content studio session token is minted only from an active membership row (`shared.tenant_members`) of the signed-in partner identity on an active agency, carries that one agency id, lasts 15 minutes at most, and the Content studio role (owner, editor, viewer) is checked on every tenant path. In the database, two layers: (a) the content routes moved to the **tenant pool** sign in as the tenant role `aa_app_user`, set the agency for that transaction only, and the `tenant_isolation` row-level security policies on the tenant tables return and accept only that agency's rows; each such route can be switched back to the main pool by its own switch, and a missing or unreadable switch keeps the tenant pool (fail closed); CI refuses a table with a `tenant_id` column that has no row-level security and an `app.tenant_id` policy, unless it is on a reviewed allowlist that the tenant role cannot read, and refuses any privilege of the tenant role on a table without row-level security. (b) The other tenant routes, and the membership, account and billing tables (`shared.tenant_members`, `shared.tenant_membership_event`, `shared.tenants`, which have no row-level security), run as the CIS runtime role `cis_app`, whose policy on every row-level-security table is `USING (true)`: for them isolation is the application's own filter on the session's agency id, not the database | Live; layer (b) is application-level only (§2 item 8). Read on 2026-11-08 from AA-CIS-App `main` and the schema dump of 2026-11-07; which route switches are off on Dev was not re-read | CIS `api/routers/tenant_session.py`, `services/tenant_membership/session.py`, `api/middleware/tenant_role.py`, `api/core/aa544_tenant_pool.py` (the routes on the tenant pool and their switches); CIS CONTEXT "Tenant DB role (`aa_app_user`, AA-817 / AA-859)"; tests `tests/integration/test_aa817_rls_tenant_isolation.py`, `test_tenant_rls.py`, `test_rls_catalogue_guard.py` with `rls_catalogue_rules.py`; dump: `tenant_isolation` policies `TO aa_app_user` and `<table>_cis_app_all` policies `TO cis_app` (for example on `acp_shared.content_piece`, `shared.tenant_integrations`) | DM-8.4; ADR 0010a |
| M-9c | **Agency separation in Booking B2B.** Booking holds AA's own commercial records of the Agency's bookings and no traveller identity (Annex 1 §4). Its B2B API accepts only the CRM's machine client with the route's scope; the agency is the `X-AA-Tenant-Id` the CRM sends for its signed-in agency (M-9), checked against an active `booking.b2b_partners` row bound to that client; every read is filtered in SQL by that partner's agency id, never by another caller field, and another agency's hold, booking or invoice gets the same 404 as one that does not exist. The schema `booking` has no row-level security: the separation is Booking's application filter plus the CRM's choice of agency | Live; application-level only (§2 item 8). Read on 2026-11-08 from AA-Booking `main` and the schema dump of 2026-11-07 | BK `backend/app/b2b/access.py`, CONTEXT "B2B API"; tests `backend/tests/unit/test_b2b_hold_flow.py` (another partner's hold is a 404), `backend/tests/integration/test_aa1037_b2b_invoices.py` (nothing of another agency's invoices) | ADR 0005a; ADR 0006b decision 7 |
| M-11 | **Agency users** sign in through a dedicated Cognito pool: accounts are created by invitation only, **MFA is required**, password minimum 14 characters | Live | INF `accounts/aa365/identity_partner.tf` (`allow_admin_create_user_only = true`, `mfa_configuration = "ON"`, `minimum_length = 14`) | ADR 0010a, ADR 0019 settled item 4 |
| M-12 | **AA staff** sign in through the WORKFORCE pool: admin-created accounts only, one-time e-mail codes, password minimum 16 characters, recovery by an admin. **MFA is optional and not enforced** for staff today | Live (MFA: gap) | INF `accounts/aa365/identity.tf` (`allow_admin_create_user_only = true`, `mfa_configuration = "OPTIONAL"`, `minimum_length = 16`) | ADR 0006 / 0006a |
| M-13 | **Least privilege for staff.** Each staff role (admin, content, content lead, tenant QA, customer success, support, finance, AI operations, viewer) is one explicit capability set, deny by default. Every staff route that names an agency checks the staff member's **tenant scope**: customer success reaches only the agencies assigned to it, support those plus the unassigned pool, content and viewer only AA's own content; a refusal reads the same whether the agency exists or not, and a CI test fails any agency route without the check. Reading agency text is its own capability; support never sees prices, overage or AI cost. The CRM support desk asks CIS for the staff member's scope on every call and refuses when it cannot get an answer. "View as tenant" is read-only, 5-60 minutes, needs a reason, is audited and shows a banner | Live (checked live on 2026-11-05 with a customer-success test identity that can only read: 7 of 7 scope checks on the API, 403 on an agency not assigned to it, 28 screenshots of the real sign-in; the test identity writes nothing in CIS or the CRM) | CIS `api/core/staff_authz.py`, `api/core/tenant_scope.py`, `api/core/view_as.py`, `tests/unit/test_aa1035_tenant_scope_routes.py`; CIS CONTEXT "R2 roles and tenant scope"; CIS PRs #1315, #1316 (CRM desk scope), #1323-#1325, #1331, #1334; AA-Partner #226, #227, #234; `docs/audits/2026-11-05-S270-live-verify/aa1035/`; session log S270 | ADR 0019 d3, d4, d5; ADR 0006a A10d |
| M-14 | AA access to CRM data in three levels: (1) console without personal data; (2) owner-granted read-only support, 1-7 days, names hidden by default, revocable at once; (3) emergency access, 15-60 minutes, a reason code and a ticket, never names, every Agency owner e-mailed. Each read is in the Agency's own access log | Live (the AWS-level emergency role is Planned) | CRM `app/support/`, crm-033; CONTEXT "AA support access L2 + break-glass L3" | DM-6.8 |
| M-15 | Database roles per app, migrations by a separate role, runtime roles without DDL rights, the administrator credential is break-glass only and the CIS runtime is denied it | Live | INF `db/migrations/roles/`, `modules/ecs/main.tf` (statement `DenyMasterAndOtherAppSecrets`) | DM-8.1, DM-8.2, DM-8.9 |
| M-16 | Secrets in AWS Secrets Manager, one prefix per app, each app reads only its own; secret scanning (gitleaks) in CI in every repo | Live | [Secrets register](../security/secrets-register.md); CI workflows | DM-8.6 |
| M-17 | Quarterly access review of database roles, grants, IAM readers of each secret and staff users | Live (first review 2026-10-20) | `docs/audits/2026-10-20-S245-access-review/` | DM-8.10 |

### Minimisation and AI

| # | Measure | State | Evidence | Rule |
|---|---|---|---|---|
| M-18 | **Personal data is scrubbed before any CRM model call**: three passes (the trip's known names and contacts, patterns such as e-mail, phone, passport, card, ID numbers, and Amazon Bedrock Guardrails); any error or timeout refuses the call. A corpus of 254 synthetic English and Vietnamese samples must show 0 leaks in CI | Live (CRM AI is off by default per Agency; on Dev the drafts run on Amazon Nova Lite through a `us.` inference profile, always after the scrub) | CRM `app/privacy/`, CONTEXT "F3 PII scrubber", workflow "Scrub corpus"; INF `modules/environment/crm_llm.tf` | DM-6.4; ADR 0008a §5 |
| M-19 | No identifying personal data in AI prompts of the Content studio and AA content stages; every such stage is classed `content`; a stage classed `pii` may only use AWS and a US deployment, enforced by a database check and the gateway | Live (rule by review; class enforced by CIS 373) | CIS migration 373 (`llm_role_config_pii_scope_check`), `shared/llm_client/vendor_route.py` | DM-6.4; ADR 0019 d12; ADR 0009 decision 10 |
| M-20 | AI call records keep the stage, model, provider, tokens, cost and time, never the prompt or output text; CRM drafts keep placeholders, and the placeholder map is sealed and expires after 24 hours | Live | `shared.llm_call_log`, `crm.llm_call` (dump); CRM `app/privacy/placeholder_store.py` | DM-6.4; ADR 0009 decision 8 |
| M-21 | Personal data stays out of job payloads, logs and error reports: job payloads hold ids only (checked at enqueue); log lines and error reports pass a scrubber; request paths with link tokens are logged redacted; error reporting sends no default personal data, no request bodies, no cookies and no local variables | Live | CRM `app/jobs/payload_guard.py`, `app/observability/scrub.py`, `request_id.py` (S268 F4); CIS `shared/sentry_init.py` (AA-870, AA-941); BK and TP same settings (AA-871) | DM-6.3, DM-6.4 |
| M-22 | Personal data is tagged per column in the database (`pii:` classes), so erasure and access reviews are mechanical; a generated inventory checks every tagged column against the records of processing | Live, partly (the CRM rows of the register are still to be written) | [Register](register.md) "Column inventory"; `tools/data/gen_pii_inventory.py` | DM-6.1 |

### Audit, monitoring and incidents

| # | Measure | State | Evidence | Rule |
|---|---|---|---|---|
| M-23 | **CRM audit trail**: append-only, codes and ids only; every reveal of an identity field and every list shown is recorded; hourly export per agency to write-once (S3 Object Lock) storage with a hash chain, verified before any partition is dropped; the Agency owner reads and downloads its own access log; an alert when one user reveals 60 records in an hour | Live (Dev: governance-mode lock only until go-live) | CRM CONTEXT "F5 audit", "F1 / F2 complete"; `crm.audit_event` (dump) | DM-6.8, DM-7.1 |
| M-24 | Audit trails in the other apps: CIS audit log append-only with a SHA-256 hash chain; Booking audit log of staff actions; AWS CloudTrail on every region with log file validation and KMS encryption | Live | `acp_shared.audit_log` triggers (dump; CIS migration 248); `booking.audit_logs`; INF `accounts/aa365/observability.tf` (`aws_cloudtrail.main`), `security_cloudtrail.tf` | DM-8.9 |
| M-25 | **Pilot safeguards before any real personal data** (ADR 0019 d16): (1) only the one pilot-marked agency may hold real data on Dev; (2) agents and maintenance scripts cannot read the personal data of any agency, the pilot included (counts only); (3) clean-up, test and batch jobs skip the pilot agency; (4) a nightly export of the pilot agency, so it can be restored alone; (5) a one-agency restore drill. Details per item in the table below | **Live** (all five on Dev since 2026-11-05, AA-969 closed in session S269); one onboarding gap in §2 item 2 | Below; `docs/audits/2026-11-05-S269-aa969-loadtest/`; session log S269 | ADR 0019 d16 |
| M-26 | Incident process: severities, a SEV1 for any exposure or loss of data, containment first, the business owner within 30 minutes, affected agencies within 2 hours, a written review. A personal-data breach branch: where AA processes for the Agency, AA tells the Agency and the Agency notifies its authority; where AA is the controller of its own records, AA runs the 72-hour clock of Vietnam's law itself | Live (process; no real incident yet) | [Incident response](../ops/incident-response.md), "Personal data breach" | DPA clause 8 |
| M-27 | Independent security review of the CRM before real data: no blocking finding; four major findings fixed with tests; minor follow-ups listed | Live (2026-11-04) | `docs/audits/2026-11-04-S268-crm-security-review/` | AA-969 |
| M-28 | Penetration test before go-live | Planned: before the first paying agency | ADR 0019 b18 | |

### Availability, retention and deletion

| # | Measure | State | Evidence | Rule |
|---|---|---|---|---|
| M-29 | Automated database backups with point-in-time restore, **14 days**; restore drills to a new instance; per-schema restore procedure | Live (14 days since the apply of AA-CIS-Infra PR #694 on 2026-11-06, `describe-db-instances` BackupRetentionPeriod 14; 7 days before; drills 2026-10-17 and 2026-10-24) | INF `modules/rds/main.tf` (`backup_retention_period = 14`, AA-CIS-Infra #694); `docs/audits/2026-10-17-S241-restore-drill/`, `docs/audits/2026-10-24-S249-restore-drill/` | DM-9.1, DM-9.3, DM-9.4; ADR 0019 d16 |
| M-30 | 14-day backups (v0.2 listed them on their own as Planned) | Merged into M-29 in v0.3 | AA-CIS-Infra #694 | ADR 0019 d16 |
| M-31 | Retention windows per table, enforced by owner-run jobs in batches, first run of each kind under DRY RUN with the tech lead's approval | Live (CRM `crm_lifecycle`; CIS and Booking retention kinds) | DM-7.1 table; CRM `app/lifecycle/`; `docs/legal/retention-log.md` | DM-7.1, DM-7.2 |
| M-32 | Erasure and offboarding: one deletion path per app; dry run, verification and a receipt; legal holds enforced in the database | Live (CRM; CIS tenant erasure tested once on Dev on a synthetic agency) | CRM CONTEXT "Data lifecycle"; [DSAR and erasure runbook](dsar-erasure-runbook.md) §4; `docs/audits/2026-10-23-S248-aa839-erasure-drill/` | DM-6.7, DM-6.8 |
| M-33 | Personal data never in the repositories or on laptops; schema and policy details in the public repos hold no data or secrets | Live (rule; `.gitignore`; review) | DM-6.10; [docs style guide](../STYLE.md) "Where a page may live" | DM-6.10 |
| M-37 | Load test before real data: the CRM under 50 synthetic agencies at once, with fair per-agency request slots | Live (2026-11-05: 6,482 requests in about 8.6 minutes, 0 errors, 0 % refused for the well-behaved agencies, their p95 238 to 288 ms per request group) | `docs/audits/2026-11-05-S269-aa969-loadtest/k6-summary.json`; AA-Partner #222; session log S269 | AA-969 |

### People and organisation

| # | Measure | State | Evidence |
|---|---|---|---|
| M-34 | Confidentiality undertakings for staff and contractors | **[●] To be confirmed by the business owner** | Not in this repository |
| M-35 | Named data-protection contact for the Agency | **[●]** (today AA's own privacy pages name one company contact address) | TP `frontend/lib/legal.ts` |
| M-36 | Security and privacy rules for agents and engineers (hooks that stop sub-agents from merging, deleting data or reading secrets; DRY RUN for destructive steps) | Live | Root `.claude/hooks/`; `skill/aa-cis-schema/references/destructive-ops.md` |

### M-25 in detail: the pilot safeguards (Live)

| # | Safeguard | How it works | Evidence |
|---|---|---|---|
| 1 | Only the pilot agency holds real data on Dev | On Dev a new agency is refused unless it is created as the pilot, for 1 to 8 weeks; the database allows one pilot at a time; the marker reaches the CRM only through the CIS account feed | CIS `services/tenant_account/dev_guard.py` (AA-1028); `shared.tenants.is_pilot`, `pilot_ends_at` (CIS 354); `crm.tenant.is_pilot` (crm-044, AA-Partner #223) |
| 2 | Agents and maintenance scripts cannot read personal data | A hook reads every database command an AI agent is about to send (an uploaded script, an inline query, a maintenance-script run) and refuses one that would return a value of a column tagged as personal data; counting is allowed. The maintenance-script runner (DB Migrate run-script) plans each statement on the live database and refuses the same reads. Both are always on, for every agency, not only during the pilot | Root `.claude/hooks/pilot-pii-guard.sh` (root PR #548); AA-CIS-Infra run-script guard (AA-CIS-Infra #678); session log S269 |
| 3 | Clean-up, test and batch jobs skip the pilot agency | CIS retention of tenant rows and the end-to-end test identity; Booking case-lifecycle clearing and inbox redaction; the CRM data-lifecycle job and the test-agency delete | CIS #1314; AA-Booking #182; AA-Partner #224 |
| 4 | Nightly export of the pilot agency | One portability export of the pilot agency every night, sealed under the agency's own key, kept 7 days; a failed nightly backup raises an alert | AA-Partner `crm_pilot_backup` (#224, #230); DM-7.1 row `crm.export_job` |
| 5 | One-agency restore drill | Opens the newest nightly export, checks every checksum, restores every table into a throwaway schema of its own transaction and compares row counts; prints ids, table names and counts only | [Runbook](../ops/runbooks/pilot-tenant-restore-drill.md); run on Dev on 2026-11-05 on two synthetic agencies: 24 of 24 rows and 169 checksums (`docs/audits/2026-11-05-S269-aa969-loadtest/restore-drill.json`), and 5,206 of 5,206 rows after the fix below (session log S269) |

The drill found a real defect before any real data: the export opened two sealed columns with the wrong agency key, so
that agency's export failed. It was fixed with a test and a code guard, and a failed pilot backup now alerts
(AA-Partner #230).

## 2. Known gaps (stated so the Agency is not surprised)

1. Staff MFA is optional (M-12; AA-CIS-Infra `accounts/aa365/identity.tf`, re-read 2026-11-06). Agency users have
   MFA on (M-11).
2. The pilot agency's CRM account: on Dev the CRM's own agency creation accepts test agencies only
   (AA-Partner `app/agencies.py`), so the pilot agency cannot hold real data in the CRM until a pilot exception keyed
   on the CIS marker is built. This refuses rather than exposes, but it must be done before the pilot starts.
3. Database point-in-time restore resets every app at once; one agency is restored from its own nightly export
   (M-25 items 4-5). That export never holds vendor credentials, the agency's keys, the audit log (kept separately
   in write-once storage) or documents past 25 MiB per export ([runbook](../ops/runbooks/pilot-tenant-restore-drill.md),
   "What the nightly backup does not hold").
4. The Content studio has no self-serve whole-account export (DPA clause 11.2).
5. The Trip Planner prompt may carry traveller free text without an automated scrub (AI Use Register `tp_compose`);
   this matters only from pilot milestone 2.
6. No SOC 2 or ISO 27001 report (ADR 0019 b18).
7. The agent hook of M-25 item 2 reads the command text an agent sends: a script another program uploads, or SQL
   assembled at run time from parts it cannot read, is outside it (its known limits are listed in the hook). The
   run-script guard is exact for maintenance scripts. Only columns tagged as personal data are protected; the
   DM-6.1 census lists untagged candidate columns still to review.
8. Agency isolation outside the CRM is partly or wholly in application code, not in the database (DM-8.4 asks for
   row-level security on tenant tables). Content studio (M-9b): the routes not yet moved to the tenant pool, and the
   membership, account and billing tables, rely on the application's filter on the session's agency id; the CIS
   runtime role `cis_app` passes every row-level security policy. Booking B2B (M-9c): no row-level security on schema
   `booking`; the CRM names the agency and Booking filters by it. A missing filter in a new query would therefore not
   be stopped by the database. Moving the remaining Content studio routes to the tenant pool, and whether Booking B2B
   gets row-level security, is engineering work whose timing the tech lead sets.

## 3. Points for counsel and the business owner

Engineering can state what runs; it cannot decide these. **[COUNSEL]** = a lawyer's answer; **[BUSINESS OWNER]** =
the business owner's decision (whether and when counsel reviews the pack is also the business owner's call, ADR 0019
b20, b10).

| # | Point | Who | Where it is used |
|---|---|---|---|
| 1 | Confidentiality undertakings for staff and contractors exist and cover Agency Personal Data (M-34) | **[BUSINESS OWNER]** | DPA clause on personnel; SCC Annex II |
| 2 | The named data-protection contact for agencies (M-35) | **[BUSINESS OWNER]** | DPA clause 1.1 and the notices |
| 3 | Whether staff MFA must be required before real agency data (M-12, §2 item 1). Engineering's proposal: require it before the pilot agency's real data. How it fits the one-time e-mail-code sign-in (a second factor on top of it, or passkeys) is for the tech lead to design; it is an AA-CIS-Infra change to the WORKFORCE pool plus enrolling each staff member | **[BUSINESS OWNER]** (the tech lead implements) | M-12 |
| 4 | Whether "measures as listed, Live on Dev" is an acceptable standard for a pilot on Dev, or whether the pilot letter must say more (no SLA, test environment) | **[COUNSEL]** | Pilot letter, DPA clause 15.3 |
| 5 | Whether a penetration test (M-28) and a SOC 2 or ISO 27001 report (§2 item 6) must be promised with a date | **[BUSINESS OWNER]**, then **[COUNSEL]** for the wording | M-28 |
| 6 | Whether the AWS terms bind through the billing reseller, and whether the reseller is a sub-processor ([Annex 3](dpa-annex-3-subprocessors.md) §1.1) | **[COUNSEL]** | Annex 3, Annex 4 |
| 7 | Whether this annex can stand as SCC Annex II as written, or needs the SCC wording per measure | **[COUNSEL]** | [Annex 4](dpa-annex-4-transfers.md) |
