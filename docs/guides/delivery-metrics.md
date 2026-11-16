---
id: GUIDE-12-delivery
title: Delivery metrics guide
description: How to read the CIS admin page Platform › Delivery and the reports DEV-01 / DEV-03 - the five DORA keys, the lead-time segments and CI health per app, how each number is defined on this ecosystem, and what to do when one moves.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent, cto]
applies_to: [aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-16
review_every_days: 90
related: [GUIDE-12, GUIDE-12-cis-admin, GUIDE-14-metrics, AA-1108]
---

# Delivery metrics guide

Part of [app access and operations](app-access-and-operations.md). A Vietnamese version of this page is
[delivery-metrics.vi.md](delivery-metrics.vi.md). The project-kit report template that uses the same definitions is
[delivery metrics report](../templates/delivery-metrics-report.md).

## 1. What the page answers

Every number on Platform › Delivery is tied to a decision. If a number does not change a decision, it is not on the
page.

| Question | Decision it supports |
|---|---|
| How fast does each app ship, and how steadily? | Which app needs attention; whether pull requests should be smaller |
| How long does one change take from pull request to Dev, and where does it wait? | Speed up CI, the merge queue or review |
| How many deploys fail, and how long until they are repaired? | Where to add a test or a guard; whether rollback must get faster |
| Is CI stable, and does it waste time? | Fix flaky tests, split slow jobs, add caches |
| Do the agent ship tools slow delivery down or break it? | Fix the `ship_*` tools, the train or a guard |

## 2. Where the numbers come from

- The root workflow **Delivery metrics** (`.github/workflows/delivery-metrics.yml`) runs every hour. It reads the six
  public repos with its own `GITHUB_TOKEN` (no extra secret): workflow runs, their jobs (every attempt), merged pull
  requests and the GitHub Deployments of the environment `dev`.
- It stores **raw events first** (one NDJSON file per day, kept 400 days) and computes the metrics from them, so a
  changed definition can be recomputed on the stored history. Field names follow the OpenTelemetry semantic
  conventions for CI/CD and VCS (`cicd.pipeline.*`, `vcs.change.*`, `deployment.*`).
- It publishes one summary next to the docs reader bundle. The CIS API reads it (cached 5 minutes), colours each
  number with the settings of area **delivery** on Platform › Settings, and serves the page. The reports **DEV-01**
  (monthly) and **DEV-03** (weekly) read the same summary, so the page and the reports always show the same numbers.
- **Refresh** on the page re-reads the newest published summary. A new collection runs on the hour.
- Every number is a **Dev number**. Dev has few events, so every metric shows its sample size **n**; a metric with n
  under the setting "fewest events before a colour" stays grey. Industry DORA bands are measured on production: do
  not compare these numbers with them as if they were production numbers.
- A new repo history fills over a few hourly runs (the request budget is shared). "History complete from" on each
  app says from which day the numbers cover everything.

## 3. Definitions on this ecosystem

These are the approved definitions (tech lead, S282). They are the part that matters most: a well-coloured number
with a wrong definition means nothing.

- **Deploy.** A run of one of the app's deploy workflows on its default branch (push or manual run) whose deploy job
  ran. The workflows per app are listed in `tools/delivery/apps.json`. Runs of one commit that overlap in time are
  **one deploy of the app** (CIS api + worker and admin, CRM api and web). A deploy is **green** when its deploy jobs
  and its post-deploy verify passed. A later run of the commit that is already live is a **redeploy**: it can be the
  recovery of a failed deploy, but it is not counted as a new deploy.
- **Change.** A pull request squash-merged into the default branch.
- **Failed deploy.** One of:
  - the post-deploy verify was red;
  - a deploy job failed;
  - it was **rolled back** (a later deploy of an older commit);
  - its pull request was **reverted**, within 48 hours;
  - a pull request whose title starts with `fix` names its pull request and merged within 48 hours (a **hotfix**).
- **Recovery.** From the failed deploy to the green deploy that repairs it: the next green deploy for a red verify or
  a failed deploy job, the rollback deploy, or the deploy that ships the revert or the hotfix.
- **Rework.** A deploy that is itself an unplanned repair: a rollback, or a deploy that ships a revert or hotfix pull
  request.
- **Environment.** A separate dimension from the start: `dev` now, `prod` after go-live. Prod adds incidents to
  recovery.
- **Left out of lead time, counted apart.** Pull requests by a bot (release-please, the schema and docs bots, not the
  agent App) and pull requests that change only docs (`docs/**` or Markdown) and cause no deploy.

## 4. The five DORA keys

DORA grew from four keys to five: three for throughput, two for instability. The starting thresholds are the DORA
"high" band (tech lead S282); each is a setting on Platform › Settings › CIS › Delivery metrics, changed by an
administrator with a reason.

| Key | Definition | Green at start | Amber at start | If it gets worse |
|---|---|---|---|---|
| Deployment frequency | Green deploys a week over the last 4 weeks | at least 1 a week | at least 0.25 a week | Changes pile up: ship smaller pull requests, look at what blocks the deploy |
| Lead time for changes | Median, pull request opened to the post-deploy verify of the first green deploy that contains it | 24 hours or less | 168 hours or less | Read the segment chart (section 5) and fix the longest segment |
| Change failure rate | Failed deploys / deploys that reached Dev | 15 % or less | 30 % or less | Look at the reasons in "Failed deploys": add the test or guard that would have caught them |
| Failed deployment recovery time | Median, failed deploy to the green deploy that repairs it | 24 hours or less | 168 hours or less | Make rollback faster, or fix forward sooner |
| Rework rate | Rollback, revert and hotfix deploys / deploys that reached Dev | 10 % or less | 20 % or less | More time goes into repairs than into new work: slow down and stabilise |

Two more colours on each app:

- **Slowest CI p95**: the p95 wall time of the app's slowest CI or deploy workflow; green at 15 minutes or less,
  amber at 30.
- **Main branch**: green when the newest CI and deploy runs on the default branch passed; amber when one is red for
  less than 2 hours; red after that. A red main blocks every merge: fix it first.

## 5. Lead-time segments

The lead time is split at the points where a change waits, so the chart shows where to act.

| Segment | From → to | A long segment usually means |
|---|---|---|
| Open to first green CI | pull request opened → the first green CI run on it | slow or flaky CI, or a pull request opened before it was ready |
| Green CI to merge queue | first green CI → the pull request enters the merge queue | waiting for review or for the session to ship it |
| Queue to merged | enters the queue → merged | the queue re-runs CI on the newest main; ejections (a red run in the queue) add a full CI round |
| Merged to deployed | merged → the deploy job of the first green deploy that contains it finished | the deploy is gated (a busy job table, a migration waiting for Migration Apply) or slow to build |
| Deployed to verified | deploy job finished → post-deploy verify passed | a slow verify, or a red verify that needed a second deploy |

A repo without a merge queue (root) has no queue point: its "Queue to merged" covers green CI to merged.

## 6. CI health

| Number | What it shows | What to do |
|---|---|---|
| p50 / p95 per workflow | Typical and slow wall time of the last 4 weeks (cancelled and skipped runs left out) | Split or cache the slowest job; check the job list in the GitHub run |
| Failure rate per workflow | Red runs / runs | A high rate on pull requests is normal while coding; on main or in the queue it is not |
| Failure rate on main | Red CI and deploy runs on the default branch / runs | Above a few percent: something breaks main often; find the common cause |
| Re-runs | Runs with more than one attempt | Many re-runs usually mean flaky tests |
| Flaky jobs | Jobs that failed and then passed on the same commit | Fix the top one first; never re-run silently |
| Merge-queue wait and ejections | Time in the queue, and how often a pull request was pushed out | Ejections cost a full CI round each |
| Actions minutes | Job minutes per workflow (public repos run free, but waste still shows) | Remove jobs that run when nothing they test changed |

## 7. How to use it

- **Every week**: DEV-03 shows the week per app. Pick one bottleneck to fix and note it in the session log.
- **Every month**: DEV-01 compares with the month before. Set one or two improvement targets.
- **Never** use these numbers to grade a person. Measuring people makes the numbers get "managed" (Goodhart's law).
  They describe the system and the process.
- **Small n**: with fewer events than the setting, do not draw a conclusion; wait for more data.

## 8. Limits today

- Dev only; no prod dimension yet, and no incidents in recovery.
- Hotfix detection relies on a `fix` pull request naming the pull request it repairs (`#123`); an unnamed fix is not
  counted.
- Flaky jobs come from re-runs and repeated runs on one commit; per-test flakiness from JUnit reports is a later step.
- The Refresh button re-reads the published summary; it does not start a new GitHub collection (the CIS API has no
  GitHub token).
- Alerts (main red too long, failed deploy, red verify) and the split agent / person / bot lead time are a later
  step.
