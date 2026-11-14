---
id: OPS-00-delivery-yyyy-ww
title: Delivery metrics <YYYY>-W<ww>
description: <One sentence - the DORA and flow metrics of the week against the baseline, and the one change they suggest.>
type: report
status: draft
owner: replace-me
audience: [engineer, cto, pm, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
related: []
---

# Delivery metrics <YYYY>-W<ww>

<!-- New-project playbook, phase 7 Operate (metrics page). Computed by a script from git, deploy runs, incident
records and the tracker; nobody types the numbers. Compare with the baseline taken by day 60. A metric is a question,
not a target: never reward a number. Delete this comment. -->

## 1. DORA

| Metric | Definition | This week | 4-week median | Baseline | Trend |
|---|---|---|---|---|---|
| Change lead time | Commit to running on the live environment, median | <...> | <...> | <...> | <up / down / flat> |
| Deployment frequency | Deploys to the live environment per day | <...> | | | |
| Failed deployment recovery time | Failed deploy to restored, median | <...> | | | |
| Change fail rate | Deploys that caused a rollback, hotfix or incident / all deploys | <...> | | | |
| Deployment rework rate | Unplanned deploys to fix a user-facing problem / all deploys | <...> | | | |

## 2. Flow

| Metric | This week | 4-week median |
|---|---|---|
| Work in progress (In Progress issues) | <...> | <...> |
| Throughput (issues Done) | <...> | |
| Work item age, oldest In Progress | <days> | |
| Cycle time (In Progress to Done), median | <days> | |

## 3. Reading

- <What moved and the likely cause.>
- <One change to try next week, or "none".>

## 4. Source

<Script name and version, the queries or files it read, when it ran.>
