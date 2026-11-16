---
id: OPS-00-delivery-yyyy-ww
title: Delivery metrics <YYYY>-W<ww>
description: <One sentence - the DORA and flow metrics of the week against the baseline, and the one change they suggest.>
type: report
status: draft
owner: replace-me
audience: [engineer, cto, pm, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-16
related: []
---

# Delivery metrics <YYYY>-W<ww>

<!-- New-project playbook, phase 7 Operate (metrics page). Computed by a script from git, deploy runs, incident
records and the tracker; nobody types the numbers. Compare with the baseline taken by day 60. A metric is a question,
not a target: never reward a number. Delete this comment. -->

## 1. DORA

<!-- One table per app and environment (`dev` until go-live, then `prod` too): never mix environments in one number.
Write n (the events behind a number) next to each value; with n under the agreed minimum, write "too few events" and
do not read a trend. Definitions: section 4. -->

Environment: <dev / prod>

| Metric | Definition | This week (n) | 4-week median | Baseline | Trend |
|---|---|---|---|---|---|
| Deployment frequency | Green deploys a week (deploy job and post-deploy verify passed) | <...> (<n>) | <...> | <...> | <up / down / flat> |
| Change lead time | PR opened to the post-deploy verify of the first green deploy that contains it, median | <...> (<n>) | | | |
| Change fail rate | Failed deploys / deploys that reached the environment | <...> (<n>) | | | |
| Failed deployment recovery time | Failed deploy to the green deploy that repairs it, median | <...> (<n>) | | | |
| Deployment rework rate | Rollback, revert and hotfix deploys / deploys that reached the environment | <...> (<n>) | | | |

Lead-time segments (median hours, so the slow step is visible):

| Open to first green CI | Green CI to merge queue | Queue to merged | Merged to deployed | Deployed to verified |
|---|---|---|---|---|
| <...> | <...> | <...> | <...> | <...> |

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

## 4. Definitions

- **Deploy**: a run of the app's deploy workflow on the default branch whose deploy job ran. Runs of one commit that
  overlap (the services of one push) are one deploy. Green = deploy jobs and post-deploy verify passed. A later run of
  the commit already live is a redeploy: not counted, but it can be a recovery.
- **Change**: a pull request merged into the default branch. Bot pull requests and docs-only pull requests that cause
  no deploy are left out of lead time and counted apart.
- **Failed deploy**: post-deploy verify red, a deploy job failed, rolled back (a later deploy of an older commit),
  its pull request reverted within 48 hours, or a `fix` pull request naming its pull request merged within 48 hours.
  From prod on, an incident linked to the deploy also counts.
- **Recovery**: from the failed deploy to the green deploy that repairs it (the next green deploy, the rollback, or
  the deploy shipping the revert or hotfix).
- **Rework**: a deploy that is itself an unplanned repair (a rollback, or one that ships a revert or hotfix).
- **Environment**: a dimension of every number from the start; numbers of two environments are never summed.

## 5. Source

<Script name and version, the raw event files it read, the definitions version, when it ran. Keep the raw events
(workflow runs, jobs, pull requests, deployments) longer than the CI provider does, so a changed definition can be
recomputed.>
