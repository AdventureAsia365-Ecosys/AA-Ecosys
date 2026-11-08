---
id: OPS-04
title: Incident response
description: Severity levels, who to tell and when, the first steps for an incident during the dev phase, and the personal-data breach branch (agency as controller, AA as controller with the 72-hour path of Vietnam's law).
type: how-to
status: active
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-06
review_every_days: 90
related: [OPS-01, OPS-02-cis, OPS-04-5xx-spike, OPS-10, SEC-01, SEC-04, SEC-04-dpa-agreement, SEC-04-vn-transfer-dossier, skill/aa-ship/SKILL.md, AA-869, AA-892, AA-873, AA-820]
---

# Incident response

Owner: the tech lead (on call for everything during the dev phase). Created S241 (AA-869). Runbooks and playbooks:
[operations index](README.md) (rollback runbooks moved there from `skill/aa-ship/SKILL.md` §5, AA-892). Alarms e-mail
on ALARM and on OK (D-20).

## Severity

| SEV | Meaning | Examples | Response |
|---|---|---|---|
| SEV1 | Customers or tenants cannot use a product, or data is exposed or lost | API 5xx for everyone, tenant sees another tenant's data, secret leaked, DB down | Start now, any hour. Tell the business owner within 30 min. Tenants told within 2 h if they are affected. |
| SEV2 | A feature is broken or degraded, with a workaround | One page 500s, pipeline jobs stuck, e-mail codes delayed, one alarm firing for > 30 min | Same working day. The business owner is told if a tenant noticed or a deadline is at risk. |
| SEV3 | Internal only, no customer impact | Dev-only error, flapping alarm, CI broken | Backlog item. |

When unsure, pick the higher severity and lower it later.

## First 15 minutes

1. **Confirm.** Reproduce it on the live URL (curl or browser). Read the alarm e-mail and the app log
   (`/ecs/aa-cis-dev`, `/ecs/aa-booking-dev`, `/ecs/aa-crm-dev` for the CRM API, CRM web and portal, Lambda logs).
   Note the start time.
2. **Stop the bleeding.**
   - Bad deploy: roll back ([CIS](runbooks/rollback-cis.md), [Booking](runbooks/rollback-booking.md),
     [any ECS service](runbooks/rollback-ecs.md): the staff admins, the CRM API and web, the TripPlanner web,
     [TripPlanner Lambdas](runbooks/rollback-tp-lambda.md), [Terraform](runbooks/rollback-terraform.md)). No frontend
     runs on Vercel any more (AA-911, AA-1038).
   - Leaked secret: rotate it first and investigate second ([secret rotation](runbooks/secret-rotation.md)).
   - Runaway job or cost: cancel the job or lower its cost-guard budget ([queue stuck](playbooks/queue-stuck.md),
     [cost spike](playbooks/llm-cost-spike.md)). There is no per-kind pause switch ([job kinds](job-kinds.md)).
   - Data exposure: close the route (tenant-pool flag, WAF rule or rollback) before looking for the cause
     ([feature flags](feature-flags.md)).
3. **Freeze.** No merges to the affected repo until it is stable. Pipeline waves are paused.
4. **Write it down.** Open a Linear issue `[Incident] <short title>` with a timeline as you go (times in
   ICT). Commands and outputs go in the issue, never secret values.
5. **Tell people** (below) once the severity is clear.

## Security alert e-mails

Subjects start with `[aa-sec]`; the rules and the live check are listed in [the security baseline](../security/baseline.md).

- **`sso_admin_signin`**: an Identity Center session on an administrator permission set started. Expected only when the
  tech lead signs in. If it was not you, treat it as SEV1: sign out every session and reset the user in Identity
  Center, then read what the session did (next item, or CloudTrail Event history by user name).
- **`admin session digest`**: the follow-up for the same session, sent within about two hours of its last call (or when
  its credentials expire): calls per service, every DELETE then every other WRITE call with its resource name and
  error code, read-only calls by count. Read the delete and write lists first; an unknown call is SEV1 even if the
  sign-in was yours. A digest marked `(continued)` covers calls made after an earlier digest of the same session; one
  marked `(partial)` covers calls up to the time it states only (the run ran short of time), and a continued digest
  follows within the hour. `WARNING: the lookup hit its page cap` means the counts are a lower bound: read the rest
  in CloudTrail Event history. The digest reads the regions the organization region policy allows (us-east-1,
  us-west-1, us-west-2). Calls to services that policy exempts from the region rule (global services, Bedrock, KMS,
  ACM and the like), made in any other region, are not in the digest: for a session you did not start, also read
  CloudTrail Event history in those regions.
  No digest after a sign-in alert: check the function's `-errors` alarm and its log group
  (`/aws/lambda/aa-sec-dev-admin-session-digest`).
- Other `[aa-sec]` rules (IAM, security-group, trail, root, Access Analyzer): expected only from Terraform or a
  planned change; otherwise follow the first 15 minutes above.

## Who is told

| Who | SEV1 | SEV2 | Channel |
|---|---|---|---|
| Business owner | within 30 min | if a tenant noticed or a deadline is at risk | Zalo (plain text, short) |
| Affected tenants | within 2 h, then on each change and on resolution | only if they reported it | E-mail from the tech lead (no agent names, no internal issue keys) |
| Agency (as controller of its clients' data) | if the agency's personal data is involved: the [processor path](#personal-data-breach) below | no | E-mail to the agency owner |
| Authority and data subjects | if personal data AA controls is involved: the [controller path](#personal-data-breach) below (Vietnam's personal data protection law, Law 91/2025/QH15, and Decree 356/2025/ND-CP) | no | Business owner, with counsel |

## Personal data breach

Any SEV1 where personal data may have been exposed, lost, changed or read by someone who should not have it also
follows this branch. The timings come from the [DPA](../legal/dpa.md) clause 8 and from Vietnam's personal data
protection law (PDPL: Law 91/2025/QH15 and Decree 356/2025/ND-CP, in force since 2026-01-01) as the S261 architecture
review read Article 23; **counsel confirms the triggers, the form and the channel before the first real personal
data** (DPA C5; [Vietnam transfer dossier](../legal/vn-cross-border-transfer-dossier.md) §7).

**1. Whose data is it?** Decide in the first hour; count rows, never read them (the agent hook refuses row reads).

| Data | AA's role | Path |
|---|---|---|
| An agency's data: CRM clients, leads, trips and messages (schema `crm`); its Content studio inputs; Trip Planner leads sent to it | Processor (DPA clause 1.2) | Processor path |
| AA's own records: staff, agency account and billing contacts, AA's own Booking and Trip Planner customers held today, AI and usage ledgers, security logs | Controller (DPA clause 1.4) | Controller path |

Both paths can apply to one incident. Which tables and personal-data classes are involved: the
[compliance register](../legal/register.md) (records of processing and the `pii:` column inventory).

**2. Processor path (the agency is the controller).**

| When | Do |
|---|---|
| T0 + 2 hours (target) | E-mail the agency owner with the template below: what is known, from when, what the agency sees |
| T0 + [24] hours (DPA clause 8.3, counsel) | The breach notice of DPA clause 8.2: nature, categories and approximate numbers of people and records, likely consequences, measures taken, a contact |
| On each change, at least every 24 hours | An update to the agency |
| Resolution + [5] business days | A written summary to the agency: timeline, cause, data, fix, prevention |

AA does not notify an authority or the agency's clients itself unless the agency asks in writing or the law requires
it (DPA 8.4). The agency carries its own deadline: under the PDPL the controller notifies the authority within 72
hours (Article 23(1)); an EU agency, within 72 hours under GDPR Article 33. Give it the facts it needs for that.

**3. Controller path (AA is the controller).**

| When | Who | Do |
|---|---|---|
| T0 + 30 minutes | Tech lead | Tell the business owner (the SEV1 rule above), saying that personal data AA controls is involved |
| As soon as the facts allow | Tech lead | Prepare the facts: what happened and when, which data categories and how many people and records, likely consequences, the measures taken, the AA contact |
| **T0 + 72 hours at the latest** | Business owner | When the breach may harm national defence, security or public order, or the life, health, honour, dignity or property of the people concerned: notify the personal data protection authority (the Ministry of Public Security's department; the S245 research names A05) under PDPL Article 23(1), on the form and channel counsel confirms |
| With counsel | Business owner | Whether to tell the people concerned, and the duties of other laws by their country (for example GDPR Articles 33 and 34, Australia's notifiable data breaches scheme) |

The small-business exemption of PDPL Article 38 does not cover Article 23, so this path applies to AA whatever its
size. Keep in the incident issue: the times, who decided, what was sent to whom (copies without personal data).

## Notice template (tenant e-mail)

```text
Subject: [Adventure Asia] Service issue — <product>, <date>

Hello <name>,

From <start time ICT> <product> <what the tenant sees, one sentence>.
We are <what we are doing now, one sentence>. Your data <is / is not> affected.
Next update by <time ICT>, or sooner when it is resolved.

<tech lead name>, Adventure Asia
```

Resolution notice: what happened (one sentence), when it ended, what the tenant needs to do (usually
nothing), and what changes so it does not happen again.

## After the incident

- SEV1 and SEV2: a short write-up in the Linear issue within 2 working days. Cover the timeline, the
  cause, what detected it (an alarm or a person), and the follow-up issues.
- A missing alarm or log becomes an issue. A wrong assumption becomes a line in `skill/aa-lessons/lessons.md`.
