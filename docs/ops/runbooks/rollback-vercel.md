---
id: OPS-02-vercel
title: Roll back a Vercel deployment
description: Return the TripPlanner Vercel project to the previous production deployment, then promote the fix later. The CIS and Booking admins left Vercel (AA-911) and roll back on ECS.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-tripplanner]
last_reviewed: 2026-11-07
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-02-cis, OPS-02-terraform, OPS-02-ecs, OPS-02-staff-web-cutover, OPS-04, AA-869, AA-892, AA-911, AA-979]
---

# Roll back a Vercel deployment

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> Moved from `skill/aa-ship/SKILL.md` §5 (S241, AA-869). Instant Rollback has not been run on any project yet.

## When to use

- Trigger: a TripPlanner frontend production deploy broke a page and the API is fine.
- Not for: the CIS admin or the Booking admin. They left Vercel at the AA-911 retirement (07/11/2026, S272; root
  runbook [staff-web-ecs-cutover](staff-web-ecs-cutover.md) section 4) and run on ECS (`aa-cis-dev-admin`,
  `aa-booking-dev-admin`): roll them back with [rollback-ecs](rollback-ecs.md) on that service, or revert on the app
  repo's `main` (`Deploy Admin Dev` redeploys). Not for API problems ([rollback-cis](rollback-cis.md), [rollback-booking](rollback-booking.md)) or the
  TripPlanner Lambdas ([rollback-tp-lambda](rollback-tp-lambda.md)).

## Facts that shape this runbook

- Team plan: **Hobby** (D-18: Pro when the first tenant pays). Instant Rollback on Hobby returns only to the
  production deployment **immediately before** the current one.
- Project with live production traffic (2026-11-07): `aa-tripplanner` (tripplanner.lumiguides.it.com) only. The
  projects `aa-cis-frontend` and `aa-booking-admin` were deleted at the AA-911 Vercel retirement (S272); their
  rollback targets went with them.
- The tenant portal is **no longer served by Vercel**. Since the AA-979 P2b cutover, `portal.lumiguides.it.com`
  points at a CloudFront distribution in front of Fargate; since AA-1036 the studio is part of the agency web
  `aa-crm-dev-web` (AA-Partner `deploy-web-dev.yml`; the separate service `aa-crm-dev-portal` is retired). The
  Vercel project `aa-cis-portal`, its rollback target, was deleted at the P2b clean-up (S256): a bad studio deploy
  is rolled back on ECS ([rollback-ecs](rollback-ecs.md) on `aa-crm-dev-web`, or revert on AA-Partner `main`).
- Deployments are created by each repo's `vercel-deploy.yml` (S241), not by the Vercel Git integration
  (`git.deploymentEnabled: false`). A push to `main` that touches `frontend/**` makes the production deployment.
- After a rollback Vercel stops assigning the production domains to new deployments until one is promoted.
- Cost: 0 USD.

## Steps

1. Identify the bad and the previous production deployment.
   Dashboard: project, **Deployments**, filter Production. Or the Vercel MCP `list_deployments` with the project
   and `target: production`.
   Expected: the newest production deployment is the bad one; the one before it is `READY`.
   Verify: its commit SHA is the commit before the bad PR.
   Rollback: none - read-only.

2. Roll back. Dashboard: the previous production deployment, menu, **Instant Rollback**. CLI alternative (needs a
   Vercel token in the shell; never paste it in a doc or chat):

   ```bash
   vercel rollback <previous-deployment-url> --scope <team-slug>
   ```

   Expected: the production domain serves the previous deployment within seconds.
   Verify: open the page; `curl -s -o /dev/null -w "%{http_code}\n" https://tripplanner.lumiguides.it.com/` returns
   200.
   Rollback: promote the bad deployment again (step 4 on it), only if the rollback made things worse.

3. Fix on `main`: revert the bad PR. `vercel-deploy.yml` builds a new production deployment, but **it does not get
   the domain** while the project is in rolled-back state.

4. Promote the fixed deployment. Dashboard: the new deployment, **Promote**. CLI:

   ```bash
   vercel promote <fixed-deployment-url> --scope <team-slug>
   ```

   Expected: the domain serves the fixed deployment, and automatic domain assignment is back on.
   Verify: the page works and the deployment list shows it as Current.
   Rollback: Instant Rollback again.

## Verify the result

- The production domain answers 200 and the broken page works.
- The next merge to `main` updates production by itself (promotion re-enabled it).

## Roll back or abort

- A rollback is undone by promoting the deployment that was current before.

## Escalation

- [Incident response](../incident-response.md).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| - | - | - | - | not run yet |
