---
id: OPS-02-vercel
title: Roll back a Vercel deployment
description: "Superseded: no ecosystem frontend runs on Vercel any more (the staff admins left with AA-911, the TripPlanner frontend with AA-1038). Every frontend rolls back on ECS; this page only says where."
type: how-to
status: superseded
superseded_by: OPS-02-ecs
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-tripplanner]
last_reviewed: 2026-11-08
review_every_days: 90
last_tested: 2026-11-02
tested_where: drill
tested_evidence: "docs/audits/2026-11-02-S264-rollback-game-day/README.md (D3 production alias of aa-booking-admin back and forward, before the Vercel retirement)"
related: [OPS-02-ecs, OPS-02-cis, OPS-02-tp-lambda, OPS-02-staff-web-cutover, OPS-02-tripplanner-web-cutover, AA-869, AA-911, AA-979, AA-1038]
---

# Roll back a Vercel deployment

> [!WARNING]
> Superseded by [rollback-ecs](rollback-ecs.md). No ecosystem project is left on Vercel: there is nothing to roll back
> there. Kept so the old links land on the right procedure.

## Where each frontend rolls back now

| Frontend | Left Vercel | Serves | Roll back with |
|---|---|---|---|
| TripPlanner (`tripplanner.lumiguides.it.com`) | AA-1038, project `aa-tripplanner` retired 08/11/2026 (S272; [cut-over runbook](tripplanner-web-ecs-cutover.md) section 4) | ECS `aa-tripplanner-dev-web` behind CloudFront | [rollback-ecs](rollback-ecs.md) on `aa-tripplanner-dev-web`, or revert on AA-TripPlanner-Web `main` (`Deploy Web Dev` redeploys) |
| CIS admin (`aa-cis.`) | AA-911, 07/11/2026 (S272; [staff-web-ecs-cutover](staff-web-ecs-cutover.md) section 4) | ECS `aa-cis-dev-admin` | [rollback-ecs](rollback-ecs.md) on that service, or revert on AA-CIS-App `main` (`Deploy Admin Dev`) |
| Booking admin (`booking.`) | AA-911, 07/11/2026 (S272) | ECS `aa-booking-dev-admin` | [rollback-ecs](rollback-ecs.md) on that service, or revert on AA-Booking `main` (`Deploy Admin Dev`) |
| Tenant portal / Content studio (`portal.`) | AA-979 P2b (S256), studio in the agency web since AA-1036 | ECS `aa-crm-dev-web` behind CloudFront | [rollback-ecs](rollback-ecs.md) on `aa-crm-dev-web`, or revert on AA-Partner `main` |

Not for API problems ([rollback-cis](rollback-cis.md), [rollback-booking](rollback-booking.md)) or the TripPlanner
Lambdas ([rollback-tp-lambda](rollback-tp-lambda.md)).

## What changed

- There is no Instant Rollback any more: an ECS rollback points the service at an earlier task-definition revision
  (its image is immutable in ECR, the newest 10 kept for the TripPlanner web) and the next deploy from `main` moves it
  forward again.
- The DNS of every former Vercel host points at AWS (CloudFront or the shared ALB); a Vercel CNAME with no project
  claiming the host would be a takeover risk, so no Vercel target is kept anywhere (AA-CIS-Infra
  `tripplanner_web_edge.tf`, `staff_web_edge.tf`, `crm_agency_edge.tf`).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-11-02 | drill (rollback game day D3), agent-run, `aa-booking-admin` | Claude Code, tech lead watching | [`audits/2026-11-02-S264-rollback-game-day/`](../../audits/2026-11-02-S264-rollback-game-day/README.md) | pass: production alias back and forward in under a minute each; superseded five days later (AA-911) |
