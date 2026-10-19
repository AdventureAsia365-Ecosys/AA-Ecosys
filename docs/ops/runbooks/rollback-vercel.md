---
id: OPS-02-vercel
title: Roll back a Vercel deployment
description: Return a Vercel project (CIS admin, Booking admin, TripPlanner) to the previous production deployment, then promote the fix later.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-frontend, aa-booking-admin, aa-tripplanner]
last_reviewed: 2026-10-19
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-02-cis, OPS-04, AA-869, AA-892]
---

# Roll back a Vercel deployment

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> Moved from `skill/aa-ship/SKILL.md` §5 (S241, AA-869). Instant Rollback has not been run on any of the three
> projects yet.

## When to use

- Trigger: a frontend production deploy broke a page (admin, Booking admin or TripPlanner) and the API is fine.
- Not for: API problems ([rollback-cis](rollback-cis.md), [rollback-booking](rollback-booking.md)) or the
  TripPlanner Lambdas ([rollback-tp-lambda](rollback-tp-lambda.md)).

## Facts that shape this runbook

- Team plan: **Hobby** (D-18: Pro when the first tenant pays). Instant Rollback on Hobby returns only to the
  production deployment **immediately before** the current one.
- Projects (19/10/2026): `aa-cis-frontend` (aa-cis.lumiguides.it.com), `aa-booking-admin`, `aa-tripplanner`
  (tripplanner.lumiguides.it.com). The tenant portal project from AA-885 is planned.
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
   Verify: open the page; `curl -s -o /dev/null -w "%{http_code}\n" https://aa-cis.lumiguides.it.com/login`
   (or the TripPlanner home page) returns 200.
   Rollback: promote the bad deployment again (step 4 on it), only if the rollback made things worse.

3. Fix on `main`: revert the bad PR. `vercel-deploy.yml` builds a new production deployment, but **it does not
   get the domain** while the project is in rolled-back state.

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
