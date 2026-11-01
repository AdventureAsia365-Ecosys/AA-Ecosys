---
id: OPS-04
title: Incident response
description: Severity levels, who to tell and when, and the first steps for an incident during the dev phase.
type: how-to
status: active
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-01
review_every_days: 90
related: [OPS-01, OPS-02-cis, OPS-04-5xx-spike, OPS-10, SEC-01, skill/aa-ship/SKILL.md, AA-869, AA-892, AA-873]
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
     [Vercel](runbooks/rollback-vercel.md), [TripPlanner Lambdas](runbooks/rollback-tp-lambda.md),
     [Terraform](runbooks/rollback-terraform.md)). The CRM API, CRM web and portal services on ECS have no rollback
     runbook yet; until 2026-11-03 the portal can also fall back to its Vercel project ([Vercel](runbooks/rollback-vercel.md)).
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
  sign-in was yours. A digest marked `(continued)` covers calls made after an earlier digest of the same session.
  `WARNING: the lookup hit its page cap` means the counts are a lower bound: read the rest in CloudTrail Event history.
  No digest after a sign-in alert: check the function's `-errors` alarm and its log group
  (`/aws/lambda/aa-sec-dev-admin-session-digest`).
- Other `[aa-sec]` rules (IAM, security-group, trail, root, Access Analyzer): expected only from Terraform or a
  planned change; otherwise follow the first 15 minutes above.

## Who is told

| Who | SEV1 | SEV2 | Channel |
|---|---|---|---|
| Business owner | within 30 min | if a tenant noticed or a deadline is at risk | Zalo (plain text, short) |
| Affected tenants | within 2 h, then on each change and on resolution | only if they reported it | E-mail from the tech lead (no agent names, no internal issue keys) |
| Customers (Booking/TripPlanner) | if personal data is involved: the business owner decides with the lawyer (PDPD notice duties) | no | — |

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
