---
id: GUIDE-12-delivery
title: Delivery metrics guide
description: How to read the CIS admin page Platform › Delivery and the reports DEV-01 / DEV-03 - the five DORA keys, the lead-time segments and CI health per app, the merge queues and the git map, how each number is defined on this ecosystem, and what to do when one moves.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent, cto]
applies_to: [aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-18
review_every_days: 90
related: [GUIDE-12, GUIDE-12-cis-admin, GUIDE-14-metrics, AA-1108, AA-1125, AA-1135]
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
  requests and the GitHub Deployments of the environment `dev`; for the Merge queue and Git map tabs also the timeline
  of each pull request seen in the merge queue and the default branch's commits with their files.
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

## 7. Merge queue tab

AA-CIS-App, AA-Booking and AA-Partner merge through a GitHub merge queue. The tab shows each **entry**: one stay of a
pull request in the queue, read from its timeline (added to / removed from the merge queue, merged) and matched with the
merge_group runs on the queue's temporary branches.

| Number | Definition | What to do |
|---|---|---|
| Queue wait p50 / p95 | Time from entering the queue to the merge, entries that merged in the last 4 weeks. The p95 is coloured (settings `cis.delivery.queue_wait_*`) | Slow merge_group checks or many rebuilds behind ejected entries; speed up or cache the checks that run in the queue |
| To merge p50 / p95 | From the first time a pull request entered the queue to its merge, across all its entries | Far above the wait: entries keep getting ejected |
| Outcome | **merged** (the queue removed it and merged it), **ejected** (the queue removed it without a merge), **removed** (a person or the agent took it out, or the pull request was closed), **in queue** | - |
| Ejection rate | Ejected entries / entries that merged or were ejected (settings `cis.delivery.queue_ejection_*`) | Read the reasons table: something passes on the pull request but fails on the merged result |
| Ejection reason | checks failed, checks timed out, checks cancelled, no check ran (from the merge_group runs of that entry), with the red workflows | Fix the workflow that ejects most |
| Flaky rate | Entries with a flaky signal / entries that merged or were ejected (settings `cis.delivery.queue_flaky_*`). Signals: a merge_group run whose newest attempt passed after an earlier attempt failed, or an ejection on red checks followed by a merge with no new commit | Quarantine or fix the check; never re-queue silently |
| merge_group CI | Minutes (per job, every attempt), runs, failure rate, p95 and re-runs of the queue's runs | Every ejection costs a full round of these minutes |
| Throughput | Entries that left the queue per day, by outcome | - |

## 8. Git map tab

Commits on each repo's default branch over 90 days, with their files (additions + deletions from the squash commits).

| Number | Definition |
|---|---|
| Commit calendar | Commits a day; the bars add them up per week |
| Author kind | agent App (`aa-agent`), CI bot (`aa-ecosys-ci-bot`, the Infra migration copies), release-please (a `chore(...): release` commit), Dependabot, another bot, a person. A person's login is never stored |
| Churn | Lines added + deleted per top-level directory, then per sub-directory or file (drill-down), and the top 30 files, over 30 or 90 days. Lock files are left out (`churn_exclude` in `tools/delivery/apps.json`) |
| Merges by branch prefix | Merged pull requests per head-branch prefix (feat, fix, docs, chore, bot, release-please, ...) |
| Recent commits | The newest 50 commits on the default branch with their pull request (the last `(#n)` of the title) |
| Files read | Share of the commits whose file list is read; a cold history fills over a few hourly runs, newest first |

Use it to see where the code moves (a hotspot that changes every week is a candidate for a test or a split) and who
moves it. Like the rest of the page it describes the system, not a person.

## 9. How to use it

- **Every week**: DEV-03 shows the week per app. Pick one bottleneck to fix and note it in the session log.
- **Every month**: DEV-01 compares with the month before. Set one or two improvement targets.
- **Never** use these numbers to grade a person. Measuring people makes the numbers get "managed" (Goodhart's law).
  They describe the system and the process.
- **Small n**: with fewer events than the setting, do not draw a conclusion; wait for more data.

## 10. Limits today

- Dev only; no prod dimension yet, and no incidents in recovery.
- Hotfix detection relies on a `fix` pull request naming the pull request it repairs (`#123`); an unnamed fix is not
  counted.
- Flaky jobs come from re-runs and repeated runs on one commit; per-test flakiness from JUnit reports is a later step.
- The Refresh button re-reads the published summary; it does not start a new GitHub collection (the CIS API has no
  GitHub token).
- A custom range reaches back only as far as the event store (`store_days`, 98 days); a longer or older range is
  refused, never estimated.
- Alerts (main red too long, failed deploy, red verify) and the split agent / person / bot lead time are a later
  step.

## 11. Time range and charts

**Range picker.** One picker above the tabs sets the window of every tab (Overview, each app, Merge queue, Git map);
it lives in the URL (`?range=7d|28d|90d`, or `?range=custom&from=YYYY-MM-DD&to=YYYY-MM-DD`), so a link opens the same
view.

- **Presets 7 / 28 / 90 days** are computed by the collector every hour (`ranges.d7`, `d28`, `d90` per app in the same
  summary; `range_presets` in `tools/delivery/apps.json`). The 28-day preset is the headline the page always showed.
- **Custom range** (from, to, whole UTC days): the CIS API recomputes it from the collector's daily event files with
  a byte copy of the collector's computation (`tools/delivery/delivery_engine.py`), so a custom range and a preset of
  the same window cannot differ. The summary carries the engine's sha256; while the CIS copy differs (a collector
  change not yet synced with `tools/delivery/sync_engine.py`), custom ranges are paused with a message and the presets
  still work. The longest range is the setting `cis.delivery.custom_range_max_days`; a range before the event store
  (`definitions.store_from`) or after the newest collection is refused. Results are cached per range until the next
  collection (`cis.delivery.custom_range_cache_entries` ranges at most).
- A window that starts before an app's complete history is measured from it, as before ("covered days").

**Charts.**

| Chart | What it shows |
|---|---|
| DORA trend | Deploys, lead time p50, change failure rate and recovery p50 per ISO week over 12 weeks, one app or all apps compared |
| Delivery flow | Pull request opened → CI green → entered the queue → merged → deployed → verified: the median and p95 of each step for the range, n per step; the step with the longest median is highlighted. A text table under the diagram carries the same numbers |
| Queue wait histogram | Merged queue entries per wait bin (`queue_wait_bins_h` in `apps.json`) |
| Ejection reasons | Ejected and removed entries per reason, as bars |
| Weekly ejection rate | Ejected over merged + ejected entries per ISO week of the range |
| Churn treemap | Lines changed per top-level directory sized by churn; select a directory to drill into its sub-directories and files |
| Recent commits | The newest commits on the default branch with their pull request links |

**Sorting.** The repo cards on Overview and Merge queue sort by worst colour first (default), by name, or by the
metric shown (highest or slowest first); the choice lives in the URL (`?sort=`).
