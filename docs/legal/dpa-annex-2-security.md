---
id: SEC-04-dpa-annex2
title: "DPA Annex 2: technical and organisational measures (draft v0.2)"
description: "Annex 2 of the partner-agency DPA (and SCC Annex II): each security measure marked Live with its code, Terraform or audit evidence and the data-standard rule or ADR it implements, or Planned with the gate it must pass; no measure is claimed that does not run."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-crm-api, aa-crm-web, aa-partner-portal, aa-cis-api, aa-cis-worker, aa-booking-api, aa-cis-dev-db]
last_reviewed: 2026-11-05
review_every_days: 30
related: [SEC-04-dpa-agreement, SEC-04-dpa-annex1, SEC-04-dpa-annex3, ARCH-08-data-management, SEC-08-s268-crm-security-review, AA-820, AA-969, AA-970]
---

# DPA Annex 2: technical and organisational measures (draft v0.2)

> [!WARNING]
> Draft for counsel, not legal advice. Part of the [Data Processing Agreement](dpa.md); also Annex II of the SCCs
> ([Annex 4](dpa-annex-4-transfers.md)). This annex takes over the DPA technical annex of AA-970 (paused under ADR 0019
> d15).

**How to read it.** **Live** = runs on Dev on 2026-11-05, with the evidence named (repo and file on `main`, the live
schema dump, or an audit folder). **Planned** = not running; the gate says when it must exist. Rules are the data
standards ([Part B, data management](../architecture/data-standards/02-data-management.md)) cited as DM-n.n, and the
ADRs in [`docs/adr/`](../adr/). Repos: CIS = AA-CIS-App, BK = AA-Booking, CRM = AA-Partner, INF = AA-CIS-Infra.
AA promises the Live measures; the Planned ones are listed so the Agency knows what is not there yet.

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
| M-8 | Web application firewall rules (AWS WAF, regional) in front of the APIs, the load balancer and the sign-in pages; a request-body ceiling and fair per-agency request slots in the CRM | Live | INF `modules/waf/main.tf`, `accounts/aa365/identity_partner.tf`; CRM `app/bodylimit.py`, `app/tenant_gate.py` (S268 review F1, F2) | ADR 0019 d23 (a CloudFront-scope WAF for the Trip Planner is Planned) |

### Access control

| # | Measure | State | Evidence | Rule |
|---|---|---|---|---|
| M-9 | **Agency isolation in the database.** Every CRM table has row-level security forced on, with one tenant policy; request code reaches data only through a tenancy context that checks the user's membership on every request; a static test refuses any other database access | Live | CRM CONTEXT "Tenancy and data rules", `api/tests/unit/test_code_rules.py`, `test_every_crm_table_follows_the_base_template` | DM-8.4, DM-6.8 |
| M-10 | No other AA app can read the CRM: no AA app role holds a grant on schema `crm`, checked by the isolation probe (every AA app role gets a permission error on `crm`) | Live | `docs/database/schema-ownership.md` (`crm` row); DM-6.8 enforcement column | DM-6.8, DM-8.3 |
| M-11 | **Agency users** sign in through a dedicated Cognito pool: accounts are created by invitation only, **MFA is required**, password minimum 14 characters | Live | INF `accounts/aa365/identity_partner.tf` (`allow_admin_create_user_only = true`, `mfa_configuration = "ON"`, `minimum_length = 14`) | ADR 0010a, ADR 0019 settled item 4 |
| M-12 | **AA staff** sign in through the WORKFORCE pool: admin-created accounts only, one-time e-mail codes, password minimum 16 characters, recovery by an admin. **MFA is optional and not enforced** for staff today | Live (MFA: gap) | INF `accounts/aa365/identity.tf` (`allow_admin_create_user_only = true`, `mfa_configuration = "OPTIONAL"`, `minimum_length = 16`) | ADR 0006 / 0006a |
| M-13 | Least privilege for staff: each staff role has an explicit capability set, deny by default; tenant-scoped routes check the staff member's assigned agencies; reading tenant text is a separate capability; "view as tenant" is read-only, 5-60 minutes, needs a reason, audited | Live | CIS `api/core/staff_authz.py`, `api/core/tenant_scope.py`, `api/core/view_as.py`; CIS CONTEXT "R2 roles and tenant scope" | ADR 0019 d3, d5 |
| M-14 | AA access to CRM data in three levels: (1) console without personal data; (2) owner-granted read-only support, 1-7 days, names hidden by default, revocable at once; (3) emergency access, 15-60 minutes, a reason code and a ticket, never names, every Agency owner e-mailed. Each read is in the Agency's own access log | Live (the AWS-level emergency role is Planned) | CRM `app/support/`, crm-033; CONTEXT "AA support access L2 + break-glass L3" | DM-6.8 |
| M-15 | Database roles per app, migrations by a separate role, runtime roles without DDL rights, the administrator credential is break-glass only and the CIS runtime is denied it | Live | INF `db/migrations/roles/`, `modules/ecs/main.tf` (statement `DenyMasterAndOtherAppSecrets`) | DM-8.1, DM-8.2, DM-8.9 |
| M-16 | Secrets in AWS Secrets Manager, one prefix per app, each app reads only its own; secret scanning (gitleaks) in CI in every repo | Live | [Secrets register](../security/secrets-register.md); CI workflows | DM-8.6 |
| M-17 | Quarterly access review of database roles, grants, IAM readers of each secret and staff users | Live (first review 2026-10-20) | `docs/audits/2026-10-20-S245-access-review/` | DM-8.10 |

### Minimisation and AI

| # | Measure | State | Evidence | Rule |
|---|---|---|---|---|
| M-18 | **Personal data is scrubbed before any CRM model call**: three passes (the trip's known names and contacts, patterns such as e-mail, phone, passport, card, ID numbers, and Amazon Bedrock Guardrails); any error or timeout refuses the call. A corpus of 254 synthetic English and Vietnamese samples must show 0 leaks in CI | Live (CRM AI is off by default; Dev uses a stub provider) | CRM `app/privacy/`, CONTEXT "F3 PII scrubber", workflow "Scrub corpus" | DM-6.4; ADR 0008a §5 |
| M-19 | No identifying personal data in AI prompts of the Content studio and AA content stages; every such stage is classed `content`; a stage classed `pii` may only use AWS and a US deployment, enforced by a database check and the gateway | Live (rule by review; class enforced by CIS 373) | CIS migration 373 (`llm_role_config_pii_scope_check`), `shared/llm_client/vendor_route.py` | DM-6.4; ADR 0019 d12; ADR 0009 decision 10 |
| M-20 | AI call records keep the stage, model, provider, tokens, cost and time, never the prompt or output text; CRM drafts keep placeholders, and the placeholder map is sealed and expires after 24 hours | Live | `shared.llm_call_log`, `crm.llm_call` (dump); CRM `app/privacy/placeholder_store.py` | DM-6.4; ADR 0009 decision 8 |
| M-21 | Personal data stays out of job payloads, logs and error reports: job payloads hold ids only (checked at enqueue); log lines and error reports pass a scrubber; request paths with link tokens are logged redacted; error reporting sends no default personal data, no request bodies, no cookies and no local variables | Live | CRM `app/jobs/payload_guard.py`, `app/observability/scrub.py`, `request_id.py` (S268 F4); CIS `shared/sentry_init.py` (AA-870, AA-941); BK and TP same settings (AA-871) | DM-6.3, DM-6.4 |
| M-22 | Personal data is tagged per column in the database (`pii:` classes), so erasure and access reviews are mechanical; a generated inventory checks every tagged column against the records of processing | Live, partly (the CRM rows of the register are still to be written) | [Register](register.md) "Column inventory"; `tools/data/gen_pii_inventory.py` | DM-6.1 |

### Audit, monitoring and incidents

| # | Measure | State | Evidence | Rule |
|---|---|---|---|---|
| M-23 | **CRM audit trail**: append-only, codes and ids only; every reveal of an identity field and every list shown is recorded; hourly export per agency to write-once (S3 Object Lock) storage with a hash chain, verified before any partition is dropped; the Agency owner reads and downloads its own access log; an alert when one user reveals 60 records in an hour | Live (Dev: governance-mode lock only until go-live) | CRM CONTEXT "F5 audit", "F1 / F2 complete"; `crm.audit_event` (dump) | DM-6.8, DM-7.1 |
| M-24 | Audit trails in the other apps: CIS audit log append-only with a SHA-256 hash chain; Booking audit log of staff actions; AWS CloudTrail on every region with log file validation and KMS encryption | Live | `acp_shared.audit_log` triggers (dump; CIS migration 248); `booking.audit_logs`; INF `accounts/aa365/observability.tf` (`aws_cloudtrail.main`), `security_cloudtrail.tf` | DM-8.9 |
| M-25 | **Pilot safeguards before any real personal data** (ADR 0019 d16): (1) only the one pilot-marked agency may hold real data on Dev; (2) a hook stops agents and maintenance scripts from reading the pilot agency's personal data (counts only); (3) clean-up, test and batch jobs skip the pilot agency; (4) a nightly export of the pilot agency, so it can be restored alone; (5) a one-agency restore drill | **Planned: gate before pilot PII.** The pilot marker exists (`shared.tenants.is_pilot`, `pilot_ends_at`); items 1-5 are not built (S268 CRM security review §4); the portability export that item 4 reuses is Live | `docs/audits/2026-11-04-S268-crm-security-review/README.md` §4 | ADR 0019 d16 |
| M-26 | Incident process: severities, a SEV1 for any exposure or loss of data, containment first, the business owner within 30 minutes, affected agencies within 2 hours, a written review | Live (process; no real incident yet) | [Incident response](../ops/incident-response.md) | DPA clause 8 |
| M-27 | Independent security review of the CRM before real data: no blocking finding; four major findings fixed with tests; minor follow-ups listed | Live (2026-11-04) | `docs/audits/2026-11-04-S268-crm-security-review/` | AA-969 |
| M-28 | Penetration test before go-live | Planned: before the first paying agency | ADR 0019 b18 | |

### Availability, retention and deletion

| # | Measure | State | Evidence | Rule |
|---|---|---|---|---|
| M-29 | Automated database backups with point-in-time restore, 7 days; restore drills to a new instance; per-schema restore procedure | Live (drills 2026-10-17 and 2026-10-24) | INF `modules/rds/main.tf` (`backup_retention_period = 7`); `docs/audits/2026-10-17-S241-restore-drill/`, `docs/audits/2026-10-24-S249-restore-drill/` | DM-9.1, DM-9.3, DM-9.4 |
| M-30 | 14-day backups | Planned: cost approved, applied before the first pilot data (ADR 0019 settled item 3) | — | ADR 0019 d16 |
| M-31 | Retention windows per table, enforced by owner-run jobs in batches, first run of each kind under DRY RUN with the tech lead's approval | Live (CRM `crm_lifecycle`; CIS and Booking retention kinds) | DM-7.1 table; CRM `app/lifecycle/`; `docs/legal/retention-log.md` | DM-7.1, DM-7.2 |
| M-32 | Erasure and offboarding: one deletion path per app; dry run, verification and a receipt; legal holds enforced in the database | Live (CRM; CIS tenant erasure tested once on Dev on a synthetic agency) | CRM CONTEXT "Data lifecycle"; [DSAR and erasure runbook](dsar-erasure-runbook.md) §4; `docs/audits/2026-10-23-S248-aa839-erasure-drill/` | DM-6.7, DM-6.8 |
| M-33 | Personal data never in the repositories or on laptops; schema and policy details in the public repos hold no data or secrets | Live (rule; `.gitignore`; review) | DM-6.10; [docs style guide](../STYLE.md) "Where a page may live" | DM-6.10 |

### People and organisation

| # | Measure | State | Evidence |
|---|---|---|---|
| M-34 | Confidentiality undertakings for staff and contractors | **[●] To be confirmed by the business owner** | Not in this repository |
| M-35 | Named data-protection contact for the Agency | **[●]** (today AA's own privacy pages name one company contact address) | TP `frontend/lib/legal.ts` |
| M-36 | Security and privacy rules for agents and engineers (hooks that stop sub-agents from merging, deleting data or reading secrets; DRY RUN for destructive steps) | Live | Root `.claude/hooks/`; `skill/aa-cis-schema/references/destructive-ops.md` |

## 2. Known gaps (stated so the Agency is not surprised)

1. Staff MFA is optional (M-12). Agency users have MFA on (M-11).
2. The pilot safeguards of M-25 are not built: no real personal data may enter Dev until they are.
3. Database point-in-time restore resets every app at once; one agency can be restored only from its own export
   (M-25 item 4, Planned).
4. The Content studio has no self-serve whole-account export (DPA clause 11.2).
5. The Trip Planner prompt may carry traveller free text without an automated scrub (AI Use Register `tp_compose`);
   this matters only from pilot milestone 2.
6. No SOC 2 or ISO 27001 report (ADR 0019 b18).
