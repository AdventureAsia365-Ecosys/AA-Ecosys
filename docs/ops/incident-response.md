---
id: OPS-04
title: Incident response
description: Severity levels, who to tell and when, and the first steps for an incident during the dev phase.
type: how-to
status: active
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-17
review_every_days: 90
related: [OPS-02, OPS-10, skill/aa-ship/SKILL.md, AA-869, AA-892]
---

# Incident response

Owner: Nghiệp (on call for everything during the dev phase). Created S241 (AA-869). Rollback commands:
`skill/aa-ship/SKILL.md` §5. Alarms e-mail on ALARM and on OK (D-20).

## Severity

| SEV | Meaning | Examples | Response |
|---|---|---|---|
| SEV1 | Customers or tenants cannot use a product, or data is exposed or lost | API 5xx for everyone, tenant sees another tenant's data, secret leaked, DB down | Start now, any hour. Tell Ms. Thư within 30 min. Tenants told within 2 h if they are affected. |
| SEV2 | A feature is broken or degraded, with a workaround | One page 500s, pipeline jobs stuck, e-mail codes delayed, one alarm firing for > 30 min | Same working day. Ms. Thư told if a tenant noticed or a deadline is at risk. |
| SEV3 | Internal only, no customer impact | Dev-only error, flapping alarm, CI broken | Backlog item. |

When unsure, pick the higher severity and lower it later.

## First 15 minutes

1. **Confirm.** Reproduce it on the live URL (curl or browser). Read the alarm e-mail and the app log
   (`/ecs/aa-cis-dev`, `/ecs/aa-booking-dev`, Lambda logs). Note the start time.
2. **Stop the bleeding.**
   - Bad deploy: roll back (aa-ship §5).
   - Leaked secret: rotate it first and investigate second.
   - Runaway job or cost: cancel the job, or set its kind's feature flag off.
   - Data exposure: close the route (flag, WAF rule or rollback) before looking for the cause.
3. **Freeze.** No merges to the affected repo until it is stable. Pipeline waves are paused.
4. **Write it down.** Open a Linear issue `[Incident] <short title>` with a timeline as you go (times in
   ICT). Commands and outputs go in the issue, never secret values.
5. **Tell people** (below) once the severity is clear.

## Who is told

| Who | SEV1 | SEV2 | Channel |
|---|---|---|---|
| Ms. Thư | within 30 min | if a tenant noticed or a deadline is at risk | Zalo (plain text, short) |
| Affected tenants | within 2 h, then on each change and on resolution | only if they reported it | E-mail from Nghiệp (no agent names, no internal issue keys) |
| Customers (Booking/TripPlanner) | if personal data is involved: Ms. Thư decides with the lawyer (PDPD notice duties) | no | — |

## Notice template (tenant e-mail)

```
Subject: [Adventure Asia] Service issue — <product>, <date>

Hello <name>,

From <start time ICT> <product> <what the tenant sees, one sentence>.
We are <what we are doing now, one sentence>. Your data <is / is not> affected.
Next update by <time ICT>, or sooner when it is resolved.

<Nghiệp>, Adventure Asia
```

Resolution notice: what happened (one sentence), when it ended, what the tenant needs to do (usually
nothing), and what changes so it does not happen again.

## After the incident

- SEV1 and SEV2: a short write-up in the Linear issue within 2 working days. Cover the timeline, the
  cause, what detected it (an alarm or a person), and the follow-up issues.
- A missing alarm or log becomes an issue. A wrong assumption becomes a line in `skill/aa-lessons/lessons.md`.
