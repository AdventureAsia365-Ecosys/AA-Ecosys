---
id: GUIDE-09
title: CIO guide
description: Security, compliance, data and IT cost for AA-Ecosys - baseline, access reviews, secrets, data classification and PII, retention, disaster recovery, vendors, budgets and the legal items that go to Ms. Thư.
type: explanation
status: draft
owner: nghiep
audience: [cio]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 90
related: [SEC-01, SEC-02, SEC-04, SEC-05, ARCH-08, FIN-01, GUIDE-06, AA-897, AA-895, AA-886]
---

# CIO guide

How the whole delivery system works: [engineering handbook](../engineering-handbook.md).

## Who this is for

You are accountable for information security, data protection, compliance and IT spend. After this page you know
which controls exist, which are open, where the evidence is kept, how personal data is classified and retained, what
the recovery targets are, which vendors process data and which decisions go to Ms. Thư. The rules themselves live in
the [data standards](../architecture/data-standards/README.md); this page points to them.

## Where we stand today

- Only a Dev environment exists. It holds **test data only** (D-01: on 2026-10-17 the 8 Booking and 6 TripPlanner
  customer rows were all test or internal addresses). Data standards C7.1a forbid copying prod personal data to Dev.
- Prod will be a separate RDS instance on acc2 (ADR 0001, C7.2a, D-17), started when Ms. Thư sets a go-live date.
  Several controls are deliberately scheduled for that date (see the readiness list below).
- Repos: all six repos are public: the four app repos (D-14, D-25), and root and Infra since 22/10/2026 until the
  coding phase ends ([ADR 0014](../adr/0014-repo-visibility-and-github-plan.md) amendment; a switch back is gated by
  amendment 2). Security findings and infrastructure detail are written only in root and Infra, never in an app repo.

## Security baseline

The control checklist is `docs/security/baseline.md` (AA-895); each control links its own issue. Current state:

| Control | State |
|---|---|
| CI to AWS through OIDC, trust limited to `main` | Done (AA-866) |
| Org 2FA (no SMS), CodeQL, secret scanning and push protection on public repos, gitleaks PR + full-history scans on Infra and root | Done (AA-867, AA-841, AA-981) |
| Server-side staff role checks; staff sign-in by company e-mail code on Cognito; owner-only access changes | Done (AA-882, AA-816; legacy password login retired at cutover) |
| ECS exec session logs and PostgreSQL connection logs | Done (D-07, D-08) |
| One security group per caller; DB owner/runtime role split (X1) | Network done (ADR 0004b); roles in progress (AA-852, AA-860) |
| Tenant isolation: RLS + fail-closed tenant pool | In progress (D-12, AA-859) |
| Redis AUTH/TLS/at-rest | Open (AA-874, cost quote first) |
| API edge: rate limits, WAF/throttle, CORS, security headers; SSRF-safe outbound client | Open (AA-876, AA-875) |
| GuardDuty, IAM Access Analyzer, S3 Block Public Access, CloudTrail review | Open (AA-873, cost quote first) |
| JSON logs with request ids, Sentry for Booking and TripPlanner | Open (AA-871) |
| Audit log for staff actions with hash chain | Live in CIS (AA-884); the RDS master can still bypass it until X1 ends |

## Access management

- Humans reach the database only through logged ECS exec sessions over SSM, never SSH or a public endpoint
  (DM-8.8). Every DB login role is defined in git; passwords live only in Secrets Manager (DM-8.1, DM-8.6).
- Staff access is managed only by owners (Nghiệp and the locked break-glass account) on CIS admin → Platform →
  Staff; disabling keeps history.
- **Quarterly access review** (DM-8.10), first session of each quarter: DB roles, memberships and grants, IAM roles
  that can read each DB secret, Cognito staff users, GitHub collaborators and apps. Record:
  `docs/audits/<date>-S<nnn>-access-review/`, indexed from `docs/security/README.md`. The first review comes with
  AA-878; the cadence with AA-838.
- AI agents run with Nghiệp's admin role today (D-15). A separate agent identity and least-privilege role are
  trigger items (U-25, U-53), revisited if Nghiệp reopens D-15 (N-8).

## Secrets

- Register: `docs/security/secrets-register.md` (AA-878, in review): every secret by name, owner, consumers and
  rotation trigger, with a monthly drift check. Orphaned secrets are removed with a 30-day recovery window.
- Rotation happens when exposure is suspected, at go-live and after any break-glass use (D-02, D-03, DM-8.9).
  There is no fixed 90-day cycle on Dev. A GitHub token and the RDS master password printed into a local
  transcript are on the go-live list.

## Data classification and personal data

- Every personal-data column carries a `pii:<class>` comment (`contact`, `name`, `address`, `profile`,
  `online_id`, `free_text`, `travel`, `payment`, and for the partner CRM `government_id`, `health`,
  `emergency_contact`); commercial secrets use `conf:commercial`, credentials `conf:credential` (DM-6.1, data
  standards v1.3). A migration copy with an unknown class fails CI. Tagging Booking and TripPlanner columns is
  AA-877.
- `booking.customers` is the single customer master (DM-6.2). Payloads and logs carry ids, not personal details
  (DM-6.3).
- No identifying personal data is sent to LLMs or to Jev, and none is written to the LLM and decision ledgers or
  app logs (DM-6.4).
- Data subject requests (access, erasure): handled by hand with a DRY RUN runbook until a self-service button exists
  with customer accounts (D-11, DM-6.7, runbook OPS-09 in AA-839).
- Real-data dumps must not live on laptops or in repo trees (DM-6.10). The 2026-09-16 dumps still wait for
  Nghiệp's approval to be secured or deleted (AA-829).

## Retention

The only retention registry is the DM-7 table in
[data standards Part B](../architecture/data-standards/02-data-management.md#7-retention-and-archival). Today:

| What | Kept |
|---|---|
| Security logs: VPC flow, WAF, ECS exec sessions, PostgreSQL, Cognito triggers | 365 days (D-09, AA-872; checked on acc2 2026-10-19) |
| Application logs (ECS, Lambda, API Gateway) | 30 days |
| LLM call ledger | 180 days, then daily rollup |
| Job rows | succeeded 30 days, failed 90 days |
| Outbox and inbox payload personal data | redacted after 90 days (to build) |
| Staff and Booking audit logs | kept; a window is set before prod |
| RDS automated backups / manual snapshots | 7 days on Dev (14 in prod) / 30 days |

A retention change needs Nghiệp's approval and lands as an amendment to that table (DM-7.5).

## Disaster recovery

| | Dev today | Prod target (DM-9.6, proposed) |
|---|---|---|
| Backups | Automated, 7-day point-in-time recovery, single-AZ | Multi-AZ, 14-day PITR, AWS Backup with a cross-region copy |
| RPO (data loss) | Minutes within the PITR window | ≤ 15 min (instance loss), ≤ 24 h (region loss) |
| RTO (downtime) | Full restore drill took about 22 min (2026-10-17) | ≤ 1 h (AZ or instance), ≤ 4 h (region) |
| Drills | When the procedure changes and once before prod (DM-9.3) | Quarterly |

Evidence: `docs/audits/2026-10-17-S241-restore-drill/`. Open: single-schema restore runbook and DSN behind a
private CNAME (AA-829).

## Vendors and sub-processors

The register of record is the [compliance and privacy register](../legal/register.md) (SEC-04, draft), section (b),
with evidence per vendor; it is regenerated in part from the `pii:` tags later. Short working list:

| Vendor | Use | Personal data |
|---|---|---|
| Amazon Web Services (acc2 via a reseller; acc3 and acc1 for Bedrock) | All hosting, database, e-mail (SES), identity (Cognito), AI models (Bedrock) | Yes (customers, staff) |
| Vercel (Hobby plan) | Frontend hosting: CIS admin, TripPlanner, Booking admin and the tenant portal (AA-Partner) | In transit only |
| GitHub (Free plan) | Code, CI | No customer data |
| Sentry (free plan) | Error reports for CIS | Must not contain personal data (DM-6.4) |
| Jev | Content decisions | Tenant content needs a DPA / zero-retention agreement first (ADR 0001) |
| OpenAI | Last-resort fallback model for some judges | No personal data (DM-6.4) |
| DataForSEO, Geoapify, Mapbox | Search demand, geocoding, maps | No |
| Google Drive | Photo originals, files for Ms. Thư | No customer data |
| Atlassian Jira, Linear, Notion | Work tracking and notes | Staff names only |

## IT cost

- Budgets on acc2 with e-mail alerts: 250 USD per month total; per `App` tag CIS 150, shared 50, Booking 25,
  TripPlanner 25 (read 2026-10-19). Rules: data standards DM-10.
- Every paid model or data call is recorded in a ledger; per-app cost is visible on CIS admin → Platform → Cost per
  app (AA-884).
- Process and the monthly cost and capacity review: `docs/ops/finops.md` and FIN-02 (AA-896, AA-838). Cost Anomaly
  Detection (free) is part of AA-896. Nghiệp activates the `App` and `Environment` cost allocation tags in Billing.
- Spend decisions: every new paid service is quoted and approved first (D-19). Vercel Pro waits for the first paying
  tenant (D-18). GitHub stays on the Free plan (D-14).

## Legal items for Ms. Thư

Raised as calm proposals with options; whether a lawyer is needed is her call.

| Item | Status |
|---|---|
| Tenant terms: clause on AI-written content | Draft in `docs/legal/tenant-terms-ai-clause-draft.md`; her answer wanted by 2026-11-11 (AA-820) |
| Privacy policy, terms of use, sub-processor list, records of processing | Draft pages live (TripPlanner and portal `/privacy`, `/terms`); [register](../legal/register.md) and bilingual [readiness packet](../legal/readiness-packet.md) (AA-886) |
| DPA template for tenants (before any tenant CRM data) | Draft [DPA template](../legal/dpa-template.md); required before the first tenant uses a CRM (DM-6.8) |
| Access and deletion requests | [DSAR and erasure runbook](../legal/dsar-erasure-runbook.md) (CIS erasure job built, DRY RUN only; Dev drill pending); runs logged in the [retention log](../legal/retention-log.md) |
| Breach notification duties under Vietnamese data protection law | Decided case by case with the lawyer ([incident response](../ops/incident-response.md)) |

## Readiness list for prod (security and compliance part)

Rotate the GitHub token and RDS master password; pgaudit; second alert channel; restore drill; Multi-AZ and
cross-region backup; WAF before customer self sign-up; legal pack published. Owner: AA-880 with ADR 0012.

## Recurring duties

| Cadence | Duty | Page |
|---|---|---|
| Monthly | Read the cost and capacity review; secrets register drift | `docs/audits/<date>-S<nnn>-capacity-review/`, AA-878 |
| Quarterly | Access review | `docs/audits/<date>-S<nnn>-access-review/` |
| When a vendor is added | Update the vendor register and DPA status | AA-886 |
| Before prod | Security readiness list above | AA-880 |

## Related

- [CTO guide](cto.md), [DevOps guide](devops.md), [CEO guide](ceo.md)
- [Data standards](../architecture/data-standards/README.md), [glossary](../glossary.md)
