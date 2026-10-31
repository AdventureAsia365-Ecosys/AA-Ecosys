---
id: GUIDE-10
title: New engineer guide
description: Learning path for an engineer joining AA-Ecosys - repos, first local run per repo, first PR to Dev, where truth lives, day-1 and week-1 checklists.
type: tutorial
status: draft
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
related: [GUIDE-01, GUIDE-02, GUIDE-05, ARCH-01, TPL-02, AA-897]
---

# New engineer guide

How the whole delivery system works: [engineering handbook](../engineering-handbook.md).

## Who this is for

You write code for AA-Ecosys: Python (FastAPI, asyncpg), Next.js, PostgreSQL, Terraform on AWS. You do not need
to know our business or our history. After this page you can run each repo locally, ship a small change to Dev the
way we do it, and find the source of any fact without asking.

Accounts and the AWS account map are in [Onboarding: accounts and access](../onboarding.md). Do that page first.

## What AA-Ecosys is

Four apps on one AWS account (acc2, us-west-1), plus a Terraform repo. The AI models run on Amazon Bedrock in a
second account, acc3:

- **AA-CIS-App** - content system of record: tour ingest and rewrite (A-series), atoms, tenant content (T-series),
  admin console, and the API behind the tenant portal.
- **AA-TripPlanner-Web** - the traveller front door: browse places, assemble a trip, send an inquiry.
- **AA-Booking** - customers, trip cases, proposals, pricing and suppliers for Adventure Asia staff.
- **AA-Partner** - the CRM for partner travel agencies (ADR 0010) and, since AA-979 (2026-10-25), the tenant portal
  (Content studio) UI, moved from AA-CIS-App with its history. The portal runs on ECS Fargate behind
  `portal.lumiguides.it.com`.
- **AA-CIS-Infra** - Terraform for every AWS resource, and the DB Migrate workflow for the shared RDS.

There is only a **Dev** environment today, holding **test data only** (D-01). Prod will be a separate RDS instance
in its own AWS account, `aa-prod` (ADR 0018, C7.2a, D-17), dated when go-live is set. Read the
[ecosystem architecture](../ecosystem-architecture.md) once end to end.

## Repos map

| Local folder | Repo (org `AdventureAsia365-Ecosys`) | Visibility | Default branch | Read first | Deploys to |
|---|---|---|---|---|---|
| `.` (root) | `AA-Ecosys` | public (since 2026-10-22) | `master` | [docs catalog](../README.md), [ADRs](../adr/README.md) | nothing (docs, skills, audits) |
| `apps/AA-CIS-App` | `AA-CIS-App` | public | `main` | `CONTEXT.md` | ECS `aa-cis-dev-api` + `aa-cis-dev-worker`; Vercel `aa-cis-frontend` (admin) |
| `apps/AA-Booking` | `AA-Booking` | public | `main` | `CONTEXT.md`, ADR 0004 | ECS `aa-booking-dev-api`; Vercel `aa-booking-admin` |
| `apps/AA-Partner` | `AA-Partner` | public | `main` | `CONTEXT.md`, ADR 0010 | ECS `aa-crm-dev-api`, `aa-crm-dev-web` and `aa-crm-dev-portal` (tenant portal), all on `portal.lumiguides.it.com` |
| `apps/AA-TripPlanner-Web` | `AA-TripPlanner-Web` | public | `main` | `CONTEXT.md` | Lambdas `aa-tripplanner-dev-browse` / `-assembly`; Vercel |
| `infra/AA-CIS-Infra` | `AA-CIS-Infra` | public (since 2026-10-22) | `main` | `CONTEXT.md`, `README.md` | AWS acc2 (root `accounts/aa365/`) |

The app repos are **public**. Never put account IDs, ARNs, security group IDs, secret lists or security
findings in them ([where a page may live](../STYLE.md#where-a-page-may-live-sec-06)).

## First local run per repo

Each repo README has the exact commands; these are the shortest paths that work without AWS access.

| Repo | Run | Test |
|---|---|---|
| AA-CIS-App | README "Local setup": venv, `uvicorn api.main:app --reload --port 8000`, `python -m worker`, `cd frontend && npm ci && npm run dev` | README "Tests": unit tests need no DB; integration tests need a local PostgreSQL 15/16 |
| AA-Booking | README "Local development": `cd backend`, venv, `ENVIRONMENT=local .venv/bin/uvicorn app.main:app --port 8000`, then `curl -s localhost:8000/booking/health` | `ruff check`, `pytest tests/unit`; integration needs a throwaway `*_test` DB prepared by `tests.integration.bootstrap_roles` |
| AA-Partner | README "Run the tests": `cd api`, venv, `pip install -r requirements-dev.txt`; `cd web && npm ci` (in a worktree, never in the main checkout) | `ENVIRONMENT=test .venv/bin/pytest tests/unit -q`; integration needs a throwaway `*_test` DB prepared by `tests.integration.bootstrap_roles`; `npm test` in `web/` |
| AA-TripPlanner-Web | README "Local setup": `cd frontend && npm ci && npm run dev`; backend fixtures server `python -m backend.tests.dev_browse_server` run from the repo root, not `backend/` (no DB) | `cd backend && PYTHONPATH=.. pytest` (offline) |
| AA-CIS-Infra | No local apply. `terraform fmt -check` and `terraform validate` locally; `plan` needs MFA credentials (onboarding) | CI "Terraform Plan" on the PR |

Environment variable names with underscores are set by the tech lead by hand (Vercel, GitHub, AWS). Copy `.env.example`
files as they are and ask for values; do not generate or rename those variables.

## Your first PR to Dev

The full gate list is `skill/aa-ship/SKILL.md`; this is the shape.

1. Pick a small issue that meets the [Definition of Ready](../templates/definition-of-ready.md). Read the repo's
   `CONTEXT.md` and the section of `skill/aa-lessons/lessons.md` for the area you touch.
2. Branch from fresh `main` (`master` in root): `git checkout main && git pull origin main && git checkout -b fix/<slug>`.
3. Keep `docs/implementation-notes/<ISSUE>.md` while you work: Decisions, Changed, Tradeoffs, Should know.
4. Commit with Conventional Commits: subject `feat|fix|chore|refactor|docs|ci|test|perf: <english>`, body
   `Refs AA-123`. Never `[AA-123]` in the subject and never `Fixes` / `Closes` (Linear would close the issue too
   early). The PR title becomes the squash commit, so it follows the same rule
   ([handbook §5.1](../engineering-handbook.md#51-commits)).
5. Push and open the PR (`git push -u origin <branch>`, then `gh pr create`); every repo has a PR template, fill it
   in. CI must be green: CIS has 9 required checks, Booking 7, TripPlanner 5 and Partner 10; root and Infra have
   none, so read their CI by hand. In root that CI is **Docs lint**. Run it before you push with
   the commands in `tools/docs/README.md` "Run locally", inside a venv (`python3 -m venv .tmp-session/docs-venv`):
   Ubuntu 24.04 refuses a system-wide `pip install` (PEP 668).
6. Migration? It goes first, alone: migration-only PR in the owner repo → byte copy in Infra
   `db/migrations/<owner>/` → **DB Migrate** `check` then `apply` → then the code PR
   ([schema ownership](../database/schema-ownership.md), Infra `README.md` "DB Migrate").
7. Merge (squash). During the dev phase the author merges after green CI (decision D-13, data standards DM-11.5
   v1.1). CIS, Booking and Partner use the GitHub merge queue: a green PR joins it (`tools/github/mergeq.sh`), and the
   queue re-runs CI on the newest `main` before it squashes. A risky change (auth, migration, IAM or secret, data delete, CI workflow) gets an agent review first
   (`kiro-reviewer` or an independent reviewer subagent).
8. Deploy happens on merge: CIS, Booking and Partner `Deploy Dev` (blocked only while a rerun wave is open or a
   deploy-blocking job runs or is due, AA-993 G5), Partner web and portal `Deploy Web Dev` / `Deploy Portal Dev`,
   TripPlanner `deploy-lambdas.yml`, the Vercel frontends through `vercel-deploy*.yml`.
9. **Verify live** before you call it done: rollout COMPLETED, `/health` shows your commit, the endpoint or page
   returns what the issue asked. Post the evidence on the Linear issue. Done = merged + CI green + deployed +
   verified live.

## Where truth lives

| Question | Open |
|---|---|
| How does the system fit together? | [Ecosystem architecture](../ecosystem-architecture.md), then each repo's `CONTEXT.md` |
| Which table or column? | [DB schema reference](../architecture/db-schema-reference.md) (generated nightly). Never guess names |
| Who may migrate which schema? | [Schema ownership](../database/schema-ownership.md) |
| Data rules (PII, retention, access, cost) | [Data standards](../architecture/data-standards/README.md) |
| Why was it built this way? | [ADR index](../adr/README.md), app and Infra `docs/adr/` |
| Contracts between apps | [Contracts](../contracts/README.md) |
| What do we work on next? | [Live backlog](../backlog/README.md), Linear |
| What happened last session? | `docs/sessions/` (Vietnamese) and Notion Program Brain → memory.md |
| Which instruction file does an agent follow? | [Agent index](../agents.md) |
| What does this word mean? | [Glossary](../glossary.md) |

Order of trust when two sources disagree: the repo (code, CONTEXT.md, ADRs) > the canonical Notion page > session
memory > a skill. Report the mismatch; do not fix it silently.

## WSL notes

- Work under `/home/<you>/projects/AA-Ecosys`, never `\\wsl.localhost\...`.
- **AWS CLI: one line per command**, always with `--profile aa365-admin --region us-west-1`. A `\` continuation
  hangs WSL2.
- Waiting for CI or a deploy: wait a sensible time (CI 3-5 min, ECS 2-5 min, Vercel 1-2 min), then check once;
  prefer `gh pr checks <n> --watch`.
- Scratch files go in `.tmp-session/` inside the workspace.

## Day 1 checklist

- [ ] All accounts in [onboarding](../onboarding.md#accounts-you-need) work; `aws sts get-caller-identity --profile aa365-admin` shows acc2.
- [ ] The root repo cloned as `~/projects/AA-Ecosys`, with the five app and Infra repos cloned inside it.
- [ ] Read: ecosystem architecture §1-§4, [STYLE](../STYLE.md), [glossary](../glossary.md).
- [ ] Signed in to the CIS admin with your company e-mail code.
- [ ] Booking backend health answers locally (`curl -s localhost:8000/booking/health`).

## Week 1 checklist

- [ ] CIS unit tests and TripPlanner backend tests pass locally.
- [ ] Read `CONTEXT.md` of CIS, Booking, TripPlanner, Partner and Infra; read ADR 0001, 0002, 0006/0006a and 0008.
- [ ] Read [data standards Part B](../architecture/data-standards/02-data-management.md) §6-§11 (PII, retention,
      access, backup, cost, change).
- [ ] Ran one read-only query through the S3-mediated ECS exec pattern (`skill/aa-cis-schema`), with the tech lead.
- [ ] Shipped one small PR end to end (merge → deploy → verified live) with evidence on Linear.
- [ ] Read the [incident response](../ops/incident-response.md) page and the [DevOps guide](devops.md).

## Escalation

The tech lead is on call for everything during the dev phase. Severity and who to tell: [incident response](../ops/incident-response.md).

## Related

- [Onboarding: accounts and access](../onboarding.md)
- [DevOps guide](devops.md), [CTO guide](cto.md), [PM guide](pm.md)
- [Glossary](../glossary.md)
