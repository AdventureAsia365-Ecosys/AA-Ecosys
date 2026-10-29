---
id: APP-13-yyyy-mm
title: Delivery and DORA report <YYYY-MM>
description: <One sentence - how often and how safely each app shipped this month, and the one improvement to make.>
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-partner, aa-cis-infra]
last_reviewed: 2026-10-29
review_every_days: 30
related: [APP-01, APP-02, APP-07, OPS-04]
---

# Delivery and DORA report <YYYY-MM>

<!-- Report family: release / DORA (DEV-01 monthly, with DEV-02 release notes and DEV-03 weekly flow). Register APP-13 in
docs/README.md before first use. Data: a root scheduled workflow collects GitHub Actions runs (deploy-dev, deploy-web-dev,
deploy-portal-dev, deploy-lambdas, vercel-deploy, post-deploy-verify, ci, release-please), PR timestamps and OPS-04 incident
times into JSON on business day 2; this page is generated from it. DORA bands are context for a small team, not targets;
read the trend. Save as docs/audits/<date>-S<nnn>-delivery/README.md with a root PR. Delete this comment. -->

Month: <YYYY-MM>. Generated: <UTC time>, run <id>. Repos: CIS, Booking, TripPlanner, Partner, Infra, root.

## 1. Summary

NARRATIVE: fastest and slowest app, change failures and their cause, the improvement to make next month.

## 2. How to read this report

- Lead time runs from the first commit of a PR to the successful deploy containing its merge commit.
- A change failure is a deploy followed within 24 h by a rollback, a fix on the same area, a failed post-deploy verify or an incident.
- Infra and root have no deploys in the app sense; they show apply runs and merged PRs.

## 3. DORA per app

| App | Deploys / week (K-DORA-DF@1) | Lead time median (K-DORA-LT@1) | Change failure rate (K-DORA-CFR@1) | Time to restore (K-DORA-MTTR@1) | Trend |
|---|---|---|---|---|---|
| CIS api + worker | | | | | |
| CIS admin (Vercel) | | | | | |
| Booking | | | | | |
| TripPlanner (Lambda + web) | | | | | |
| Partner (CRM api, web, portal) | | | | | |

Targets (context): deploys >= daily on active apps, lead time < 1 day, change failure < 15 %, restore < 1 day.

## 4. CI health

| Repo | CI runs | Failure rate on main (K-CI-MAINFAIL@1) | Median duration | Re-runs | Flaky tests | Actions minutes (private repos) |
|---|---|---|---|---|---|---|

## 5. Releases (DEV-02)

| App | Versions | User-visible highlights | Breaking changes |
|---|---|---|---|

## 6. Change failures

| Deploy | App | What failed | Detected by | Restore time | Postmortem |
|---|---|---|---|---|---|

## 7. Flow (from the weekly DEV-03 runs)

Issues shipped per week, In Progress older than 7 days, PRs open longer than 3 days, plan slot completion.

## 8. Decisions needed

| # | Decision | Context | Options | Recommendation | Owner role | Needed by |
|---|---|---|---|---|---|---|

## Sources

Workflow names per repo, collection JSON path, run ids.
