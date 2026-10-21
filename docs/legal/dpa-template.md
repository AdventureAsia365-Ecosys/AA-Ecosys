---
id: SEC-04-dpa
title: Data processing agreement template (draft)
description: Draft DPA between Adventure Asia and a tenant, with roles, processor obligations and annexes for processing, security measures and sub-processors; for counsel to rewrite, not legal advice.
type: template
status: draft
owner: nghiep
audience: [owner, cio]
applies_to: [ecosystem]
last_reviewed: 2026-10-21
review_every_days: 90
related: [SEC-04, SEC-04-packet, AA-886, AA-820, AA-839, AA-877]
---

# Data processing agreement template (draft)

> **DRAFT FOR LAWYER REVIEW. THIS IS NOT LEGAL ADVICE AND IS NOT APPROVED.**
> Engineering (Claude Code, for Pham Quoc Nghiep) prepared this outline from the product facts in the
> [compliance and privacy register](register.md). Counsel has not reviewed it and no tenant has seen it. Counsel
> should rewrite it to fit the tenant agreement (defined terms, numbering, liability, governing law) and choose the
> regimes that apply (Vietnam PDPL and its decree, GDPR with the SCCs, Australia APP 8). Every product fact in the
> annexes cites code or the live schema dump.

| | |
|---|---|
| Status | Draft v0.1, 21/10/2026 |
| Placeholders | `[●]` = a value counsel or the business fills in. *Drafting notes* (italics) are for the reviewer and are not part of the agreement. |
| Companion | AI acceptable-use clause: [`tenant-terms-ai-clause-draft.md`](tenant-terms-ai-clause-draft.md) |

## 1. Parties and roles

**1.1** This Data Processing Agreement ("DPA") is between [●] (the Adventure Asia legal entity, "AA") and the tenant
named in the [partner agreement] ("Tenant"). It forms part of that agreement.

**1.2 Tenant data.** For personal data the Tenant puts into the Services (for example names in brand settings, content
or channel connections), and for any tenant CRM data if that service is provided, the Tenant is the **controller** and
AA is the **processor**.

**1.3 AA's own data.** For travellers who use the Adventure Asia Trip Planner and send a trip to an AA advisor, and for
the customer records in AA's booking system, AA is the **controller**. This DPA does not cover that data; the
TripPlanner privacy notice does.

*Drafting note: today a tenant signs in with one shared tenant key, and tenant user accounts are not built. The tenant
record holds the business name, slug, country and a key hash, but no individual contact details (register row 5).*

## 2. Processor obligations

AA shall:

1. **Instructions.** Process Tenant personal data only on the Tenant's documented instructions, including those given
   through the Services (for example a publish action), unless the law requires otherwise; AA tells the Tenant of
   such a legal requirement unless the law forbids it.
2. **Confidentiality.** Ensure that people authorised to process the data are bound by confidentiality.
3. **Security.** Apply the technical and organisational measures in Annex 2, and keep them at a level appropriate to
   the risk.
4. **Breach notice.** Notify the Tenant without undue delay, and within [●] hours, after becoming aware of a personal
   data breach affecting Tenant data, with the information the Tenant needs for its own notifications.
   *Drafting note: AA's internal incident process tells affected tenants within 2 hours of a SEV1 incident ("data is
   exposed or lost") being identified ([incident response](../ops/incident-response.md), Severity table). Counsel
   decides the contractual figure; the PDPL controller deadline to the authority is reported as 72 hours (CRM research
   `04-economics-compliance-security.md` §4.1).*
5. **Sub-processors.** Use only the sub-processors in Annex 3. The Tenant gives general authorisation; AA notifies the
   Tenant at least [●] days before adding or replacing one, and the Tenant may object on reasonable grounds [●]. AA
   imposes the same data-protection obligations on each sub-processor.
6. **Data-subject requests.** Help the Tenant answer requests from individuals (access, correction, deletion,
   objection) by appropriate technical and organisational measures, within [●] days of a request.
7. **Assistance.** Help the Tenant with security, breach notifications, impact assessments and consultations with
   authorities, taking into account the information available to AA.
8. **Deletion or return.** At the end of the Services, at the Tenant's choice, delete or return Tenant personal data
   within [●] days, and delete existing copies unless the law requires storage. AA confirms deletion in writing.
   *Drafting note: offboarding a tenant today is soft (revokes the key, cancels queued jobs) and reversible by AA. A
   tested tenant erasure procedure does not exist yet (see the [DSAR and erasure runbook](dsar-erasure-runbook.md));
   it is needed before AA can commit to a deletion deadline. Two facts bound any "delete existing copies" wording. The
   7-day automated database backups (`backup_retention_period = 7`, `modules/rds/main.tf:143`) cannot be edited, so
   erased data leaves them only when they age out, within 7 days; the manual snapshot taken before an erasure is
   deleted once the erasure is verified (runbook section 3, step 8). And the runbook finds a person's records by a
   one-way hash of their e-mail address and erases by record id, so the address itself is never written into code,
   logs or the repository.*
9. **Audit.** Make available the information needed to show compliance with this DPA, and allow audits by the Tenant
   or an auditor it mandates, [●] (frequency, notice, cost).
10. **Transfers.** Process Tenant data in the United States (AWS us-west-1) and with the sub-processors in Annex 3,
    under the transfer safeguards in [●] (for example SCC Module 2, the UK Addendum, a Vietnamese transfer impact
    assessment). *Drafting note: counsel chooses the instruments per regime. Two facts limit "United States": the AI
    accounts call Amazon Bedrock through `global.` cross-region inference profiles, which can process a prompt outside
    the US, and the Vercel functions run in Vercel's default region, which is not pinned (register section (b)).*

## 3. Tenant obligations

The Tenant shall have a lawful basis for the personal data it puts into the Services, give individuals the notices the
law requires, and not put special-category data into brand settings or content [●].

## 4. Liability, term and precedence

[●] *Drafting note: aligned with the partner agreement by counsel.*

## Annex 1: Description of the processing

| Item | Description |
|---|---|
| Subject matter | Providing the Services: tour rewrites in the Tenant's brand voice, social and blog content, publishing to the Tenant's channels on instruction |
| Duration | The term of the partner agreement, plus the deletion period in clause 2.8 |
| Nature and purpose | Storage, AI generation and review, publication on instruction, support and moderation, security |
| Categories of data subjects | People the Tenant names in brand settings, content or channel connections `[to be confirmed with the Tenant]`; Tenant staff only through the shared tenant key |
| Categories of personal data | Whatever the Tenant enters; channel credentials (`conf:credential`, stored in Secrets Manager `acp/cms/*`, `acp/social/*` and `shared.tenant_integrations`); activity records (publish log, admin audit log). AA's policy is that no personal data goes to AI models (DM-6.4) |
| Special categories | None intended |
| Retention | AI call records 180 days; security logs 365 days; publish records and the audit log: a period set before production; account data while the account is active, then [●]. Source: [§7 retention table](../architecture/data-standards/02-data-management.md#7-retention-and-archival) |

Register rows 5 and 6 of [register.md](register.md) hold the table-level detail.

## Annex 2: Technical and organisational measures

**Live** = runs on Dev today, with the evidence cited. **Planned** = not running yet; the work item is named.

| Measure | State | Evidence |
|---|---|---|
| Database encrypted at rest | Live | AA-CIS-Infra `modules/rds/main.tf:115` (`storage_encrypted = true`) |
| Database backups and deletion protection | Live | 7-day automated backups (`backup_retention_period = 7`, `modules/rds/main.tf:143`); `deletion_protection = true` (`:140`) and a final snapshot on delete (`:133`) |
| Database not reachable from the internet | Live | AA-CIS-Infra `modules/rds/main.tf:132` (`publicly_accessible = false`); DM-8.8 |
| Encryption in transit (TLS) | Live | HTTPS at API Gateway and on the Vercel sites; RDS `rds.force_ssl` set (AA-CIS-Infra `modules/rds/main.tf:78`) and every app connects with SSL required |
| Tenant isolation by row-level security; per-app database roles | Live | DM-8.4; X1 role split: the CIS runtime signs in as `cis_app`, and its task role is denied the master secret (AA-CIS-Infra `modules/ecs/main.tf:262-280`; DM-8.9) |
| Credentials stored hashed or in Secrets Manager | Live | `shared.tenants.api_key_hash`; `booking.customer_otps.otp_hash`, `customer_sessions.refresh_token_hash`; channel credentials in Secrets Manager (dump; DM-6.9) |
| TripPlanner guest token stored only as a hash | Live (AA-827) | Dump: `tripplanner.sessions.guest_token_hash bytea`, CHECK `sessions_guest_token_retired_chk (guest_token IS NULL)` ([`db-schema-reference.md`](../architecture/db-schema-reference.md) lines 3739, 3745) |
| Error tracking without personal data | Live (AA-870) | AA-CIS-App `shared/sentry_init.py:96-108` (`send_default_pii=False`, no request bodies), `:66-79` (cookies dropped, header allowlist, key redaction). Open point: frame local variables (register note 1) |
| Staff sign-in | Live | Cognito WORKFORCE pool: accounts are created by an admin only (no self sign-up), staff sign in with an e-mail one-time code, recovery is admin-only, the password policy is 16 characters with all four character classes. MFA is **optional**: TOTP is set up for the break-glass account only; it is not enforced for staff (AA-CIS-Infra `accounts/aa365/identity.tf:22-25`, `:344-375`) |
| Audit trail of staff and tenant actions | Live | `booking.audit_logs` (actor, action, before/after); `acp_shared.audit_log` append-only with a sha256 hash chain (dump lines 500-530: triggers `audit_log_chain`, `audit_log_no_update`, `audit_log_no_delete`; CIS migration 248) |
| Security log retention 365 days | Live | [§7 retention table](../architecture/data-standards/02-data-management.md#7-retention-and-archival) (CloudWatch security/audit class, AA-872) |
| No personal data in AI prompts or AI call records | Live as a rule, checked by review | DM-6.4; no automated PII check exists |
| Retention jobs for event payload PII | Planned | Booking job built, DRY RUN only; TripPlanner not built (DM-6.6; AA-825, AA-861). See the [retention log](retention-log.md) |
| Tested erasure job for a traveller and a tenant | Planned | AA-839; [DSAR and erasure runbook](dsar-erasure-runbook.md) (untested; finds a traveller's records by a one-way hash of the e-mail address and erases by record id) |
| Machine-readable PII inventory (`pii:` column tags) | Planned | AA-877 (DM-6.1) |
| Individual tenant user accounts and key rotation | Planned | AA-813 |

## Annex 3: Sub-processors

The list of record is section (b) of the [compliance and privacy register](register.md#b-sub-processors). Changes are
notified as in clause 2.5. *Drafting note: counsel decides whether the AWS resellers (TrueIDC for the hosting account,
eCloudvalley for the AI account) and the model makers behind Amazon Bedrock are listed.*

## Annex 4: Tenant CRM (placeholder)

Reserved for the CRM legal track (DM-6.8): CRM data categories, per-tenant retention and hard delete, CRM
sub-processors and the transfer annexes. Written by that track when the CRM design is approved; not part of this draft.
