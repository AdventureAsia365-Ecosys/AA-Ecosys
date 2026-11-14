---
id: GUIDE-14-metrics
title: Playbook metrics
description: How a project measures delivery (DORA), flow (Kanban) and AI readiness (DORA AI capabilities), and how often.
type: reference
status: draft
owner: nghiep
audience: [cto, pm, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-operate, GUIDE-14-adoption]
---

# Playbook metrics

Metrics are questions, not targets. They are computed by a script from records the team already keeps; nobody types
them, and no paid tool is bought before there is prod traffic. Report template:
[delivery metrics report](../templates/delivery-metrics-report.md).

## Delivery: the five DORA metrics

| Metric | Definition | Source | Cadence |
|---|---|---|---|
| Change lead time | Commit to running on the live environment, median | Git and deploy runs | weekly |
| Deployment frequency | Deploys to the live environment per day | Deploy runs | weekly |
| Failed deployment recovery time | A failed deploy to restored service, median | Deploy runs and incident records | weekly |
| Change fail rate | Deploys that caused a rollback, hotfix or incident, over all deploys | Deploy runs and incident records | weekly |
| Deployment rework rate | Unplanned deploys made to fix a user-facing problem, over all deploys | Deploy runs and the tracker | weekly |

## Flow: the four Kanban metrics

| Metric | Definition |
|---|---|
| Work in progress | Issues In Progress now (limit 8 by default) |
| Throughput | Issues Done per week |
| Work item age | Days an In Progress issue has been open; the oldest is the one to look at |
| Cycle time | In Progress to Done, median |

## AI readiness: the seven DORA AI capabilities

Score each 0 to 3 once per project and at each 90-day review.

| Capability | What good looks like in the kit |
|---|---|
| Clear and communicated AI stance | `AGENTS.md` plus the project rules: what agents may do, what they never do |
| Healthy data ecosystems | Data standards, one writer per entity, contracts |
| AI-accessible internal data | A generated schema reference, a docs catalog and an `llms.txt` index |
| Strong version control | Trunk-based flow, merge queue, immutable images |
| Working in small batches | One deliverable per issue; 3 to 5 issues per session |
| User-centric focus | A success metric in the charter; UAT for visible features |
| Quality internal platform | The template repo, generic skills, hooks and ship tools |

## Reading the numbers

- Compare with the project's own baseline (taken by day 60), not with another team.
- A rising change fail rate with a rising deploy frequency means the tests and checks are not keeping up.
- A rising work item age means too much is started; finish before starting.
