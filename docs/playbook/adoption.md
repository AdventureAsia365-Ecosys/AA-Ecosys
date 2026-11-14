---
id: GUIDE-14-adoption
title: Adopting the playbook
description: The day-1 checklist, the 30 / 60 / 90-day plan, the running cost of a new project and how the kit itself is accepted.
type: how-to
status: draft
owner: nghiep
audience: [owner, cto, pm, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-discovery, GUIDE-14-setup, GUIDE-14-metrics]
---

# Adopting the playbook

The checklist is a tracked list of issues with an owner and a date, not prose. Create one tracker issue per line.

## Day 1 (first two sessions)

| # | Step | Owner |
|---|---|---|
| 1 | Fill the [discovery brief](../templates/discovery-brief.md) and the [charter](../templates/project-charter.md); decide G1 | Business owner |
| 2 | Generate the repo or repos from the template repo; push; turn on branch protection and the merge queue | Tech lead |
| 3 | Create the tracker project, the plan file and the first backlog | Orchestrator agent |
| 4 | Fill `CONTEXT.md` on the arc42 canvas and the C4 context view | Orchestrator agent; tech lead accepts |
| 5 | Write the first ADRs: stack, data ownership, identity, environments | Orchestrator agent; tech lead accepts |
| 6 | Quote the Dev skeleton's monthly cost and get the business owner's yes; then create the cloud account and CI role through IaC, with tags and a budget alert at that figure | Tech lead |
| 7 | Apply migration `<prefix>-001` (schema, roles) from CI | Orchestrator agent |
| 8 | Deploy the skeleton to Dev; `/health` returns the commit SHA | Orchestrator agent |
| 9 | Fill the RAID log, the cost sheet and the secrets register (names only) | Orchestrator agent |
| 10 | Run the first session close: snapshot, log, lessons file created | Orchestrator agent |

## 30 / 60 / 90 days

| By day | Outcome | Checked by |
|---|---|---|
| 30 | First feature through the Definition of Ready and Done; ratchets and docs lint green; first lesson turned into a guard | Verified-live comment; CI history |
| 60 | Test strategy in use; ASVS level 1 checklist done for the touched areas; first runbook tested in a drill; DORA baseline taken | Drill evidence; first metrics report |
| 90 | First monthly cost and capacity review; first retro on the playbook itself; prune pass on instructions and ADRs; the G7 plan written (what switches on at first prod) | Review files; playbook issues raised |

## Running cost of a new project

Building the kit is free; running what it generates is not. Steps 6 to 8 deploy a skeleton with a database, a job
table and `/health` to Dev, and that bills every month. Quote it at G1 with the provider's pricing calculator for the
real region. Rough figures from list prices (November 2026):

| Shape | What runs on Dev | Rough monthly cost |
|---|---|---|
| Shared platform: the app joins an existing container cluster, database instance, private link and API gateway, with its own schema and roles | Two small containers (api, worker), logs, a few secrets | about 10 to 35 USD |
| Standalone: own account, database and load balancer | Two small containers, the smallest PostgreSQL instance in one zone, a load balancer, a NAT gateway, public IPv4, logs, secrets, image registry | about 80 to 120 USD; the load balancer and the NAT gateway are about half |

Prefer the shared shape when the project lives in the same organisation; use standalone when it must be isolated
(another owner, another legal entity).

## How the kit itself is accepted

| Measure | Target |
|---|---|
| Generate to green: template copy to all checks green on an empty PR | at most 1 session |
| Day-1 items that needed a manual fix the playbook does not describe | 0 blocking, at most 3 minor, each fixed in the kit |
| Template update from the previous tag to the latest on an untouched project | applies without conflict |
| Leak scans on the template repo | 0 findings |
| A fresh agent with no project context runs the day-1 checklist from the docs alone | no question the docs should have answered |
| Generate to live: template copy to `/health` returning the commit SHA on Dev | at most 2 sessions |
| Retirement of a test service with the phase 9 checklist | 0 resources and 0 USD left after one billing day |
| DORA baseline by day 60, playbook retro by day 90 | both done |
