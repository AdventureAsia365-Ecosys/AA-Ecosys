---
id: ARCH-10
title: Testing strategy
description: How AA-Ecosys tests a change, layer by layer, from static checks to the live verify after deploy, which workflow runs each layer in which repo, and where the binding test rules live.
type: explanation
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [ARCH-08-engineering, CAT-01, GUIDE-05, GUIDE-06, GUIDE-13-lms, AA-1104]
---

# Testing strategy

This page explains how a change is tested in AA-Ecosys and why the layers are split the way they are. It names the
workflow that runs each layer; the binding rules stay where they are: the test rules TST-1 to TST-7 in
[data standards Part A §7](data-standards/01-engineering.md#7-testing), the Definition of Done in the
[engineering handbook §6.4](../engineering-handbook.md#64-definition-of-ready-and-done) and the live verify in
`skill/aa-ship/SKILL.md`. Workflow facts were read from the `main` branch of each repo on 2026-11-14.

## The idea in one paragraph

Cheap checks run first and on every pull request; expensive checks run only when the diff needs them; nothing counts
as done until the change runs on Dev and a live check proves it. Most code is written by agents, so the checks carry
more weight than in a human-only team: a gap in a check is a gap an agent will walk through. Every layer below fails
closed, and a lesson that a check could catch becomes a check (the lesson log rule in
[handbook §3](../engineering-handbook.md#3-lifecycle-stages), stage 10).

## The layers

| # | Layer | What it catches | When it runs | Where |
|---|---|---|---|---|
| 1 | Static checks | Style and lint errors, type errors, new complexity or file-size debt (code-health ratchets, AA-1097), literal AWS resource IDs in public repos, known vulnerable dependencies, secrets | Every pull request | The `Lint` and `Security Audit` jobs of each app's `ci.yml`; `secret-scan.yml` in all six repos; `workflow-lint.yml` |
| 2 | Unit tests | Logic errors in one module, with no database or network | Every pull request that touches code | `Unit Tests` in each app's `ci.yml` (parallel workers; a coverage gate or a coverage ratchet that may not drop) |
| 3 | Integration tests | SQL, migrations, row-level security, grants and the job runner on a real PostgreSQL 15 | Pull requests that touch migrations, SQL or integration tests; always in the merge queue | `Integration Tests` (CIS, Booking, Partner) and `Migrations (lint, PG 15 replay)` (TripPlanner); rules TST-1 to TST-4 |
| 4 | Contract tests | A change that breaks another app's reader | Pull requests that touch an API or a contract | `api-contract.yml` (OpenAPI diff, CIS and Booking), root `contracts.yml` (OpenAPI schemas, samples and field policy; TST-6) |
| 5 | Image checks | An image that does not start, or fixable critical vulnerabilities | Pull requests that touch the Dockerfile or requirements | `Docker Build Check` (health answer without a database, Trivy, SBOM) |
| 6 | UI checks | Broken pages, console errors, overflow, theme and kit drift | Pull requests that touch a frontend; after each frontend deploy | `visual.yml` (changed pages, desktop and phone, light and dark), `ui-smoke.yml` and `ui-smoke-portal.yml` (Playwright against the deployed host), `e2e-cognito.yml` (real staff sign-in) |
| 7 | Post-deploy verify | Dev does not run the commit that was merged, a health check fails, a worker kind has no live worker | After every deploy | `post-deploy-verify.yml` in each app repo |
| 8 | Live verify (Done) | The feature does not do what the issue asked on the real system | Before an issue is marked Done | The orchestrating session, by `skill/aa-ship/SKILL.md`: curl with status and shape, the UI page, a query |
| 9 | Scheduled guards | Problems no single pull request causes: order-dependent tests, tenant isolation, drift, old secrets in history | Nightly or weekly | `nightly-integration.yml` (CIS, random module order), AA-CIS-Infra `db-isolation-probe.yml`, `db-freshness-probe.yml`, `terraform-drift.yml`, `secret-scan-history.yml` |
| 10 | LLM quality | A prompt or model change that makes the writing or judging worse | By hand, because each run costs money | The golden set of about 100 samples (AA-729) and `eval-regression.yml` in CIS (`workflow_dispatch` only) |

The root repo and AA-CIS-Infra have no app code. The root repo runs the docs lint (`docs-lint.yml`: front-matter,
links, Markdown style, the unit tests of its tools), `contracts.yml`, `pr-title.yml` and the secret scans.
AA-CIS-Infra runs `terraform-plan.yml` on every pull request, plus unit tests for its guard scripts and Lambda code.

## Why the layers are split this way

- **Speed where it is cheap.** Layers 1 and 2 run in minutes and need no database. A scope step in each `ci.yml`
  skips the heavy jobs (layers 3, 5 and 6) when the diff does not touch their area; the merge queue runs everything
  again on the latest `main` before the squash.
- **A real database, as a non-superuser.** A superuser skips row-level security, so tests that depend on it also run
  as an RDS-like role (TST-3), and every tenant table has isolation cases (TST-4). Skipped integration tests fail the
  job: a skip would hide a missing table.
- **The same checks before the push.** The pre-push hook (`scripts/install-hooks.sh`, AA-993) runs the subset of
  layers 1 and 2 that the diff needs, so most failures never reach CI.
- **Merged is not done.** Layers 7 and 8 exist because a green pull request can still deploy the wrong image, miss a
  migration or fail on real data.

## How to read the required checks of a repo

Branch protection on each app repo names the checks a pull request must pass. Read the current list rather than a copy:

```bash
gh api repos/AdventureAsia365-Ecosys/AA-Booking/branches/main/protection/required_status_checks --jq '.contexts'
```

Change the repo name for the other apps. The root repo and AA-CIS-Infra have no required checks; the merging session
checks that every check is green before it merges.

## Known gaps

| Gap | Tracked in |
|---|---|
| The catalogue guard of TST-5 is still "to build"; until then the review checklist of Part A §8 applies | Data standards Part A §7, roadmap X2 |
| No accessibility check in the UI layer | AA Academy gap G4 ([research](../research/lms/README.md#23-gaps-that-block-courses)) |
| LLM evals are manual, with no per-pull-request trigger (decision N-4) | [Handbook §5.7](../engineering-handbook.md#57-llm-prompts-and-models) |

## Related

- [Data standards Part A §7 Testing](data-standards/01-engineering.md#7-testing)
- [Engineering handbook §6.4](../engineering-handbook.md#64-definition-of-ready-and-done), [§3](../engineering-handbook.md#3-lifecycle-stages)
- [Operations index, CI/CD matrix](../ops/README.md#cicd-matrix-app-02)
- [Run it locally](../guides/new-engineer.md#first-local-run-per-repo), for the local commands of each repo
