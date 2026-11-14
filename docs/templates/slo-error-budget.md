---
id: OPS-00-slo-replace-me
title: SLO and error budget policy - <service>
description: <One sentence - the service level objective of the service and what the team does when the error budget runs out.>
type: reference
status: draft
owner: replace-me
audience: [owner, engineer, devops, cto]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 90
related: []
---

# SLO and error budget policy - <service>

<!-- New-project playbook, phase 8 Scale. Written early, switched ON at gate G7 (first prod or first paying tenant,
kit decision D10); on Dev it stays a draft. Built on the Google SRE workbook (implementing SLOs, error budget policy).
The business owner agrees the target; the tech lead owns the measurement. Delete this comment. -->

## 1. Service and users

<What the service does and for whom; the user journey the SLO protects.>

## 2. SLIs and SLOs

| SLI (what is measured) | Good event | Valid event | SLO (target over 28 days) | Source |
|---|---|---|---|---|
| Availability | <request answered with a non-5xx status> | <all requests except health checks> | <99.5 %> | <load balancer logs> |
| Latency | <request answered within 800 ms> | <all requests> | <95 %> | <...> |
| Freshness (jobs) | <job finished within its window> | <all scheduled jobs> | <99 %> | <job table> |

Error budget = 100 % minus the SLO. At 99.5 % over 28 days that is about 3 hours 22 minutes of bad minutes.

## 3. Policy

| Budget left in the window | What the team does |
|---|---|
| More than 50 % | Ship as normal |
| 25 % to 50 % | Releases continue; reliability issues move to the top of the queue |
| Less than 25 % | Only fixes and reliability work ship; risky changes wait |
| Spent | Feature freeze for the service until the budget recovers or the business owner accepts the risk in writing |

- A single incident that uses more than 20 % of the budget gets a postmortem.
- Exceptions are decided by the business owner and the tech lead together and recorded with a date.

## 4. Review

Monthly with the cost and capacity review; the target changes only by a recorded decision.
