---
id: GUIDE-14-setup
title: "Phase 3: Setup"
description: Stand up a walking skeleton that builds, deploys to Dev and is observed, with every guard on - deliverables, gate G3 checklist and common mistakes.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-architecture, GUIDE-14-adoption, GUIDE-08]
---

# Phase 3: Setup

**Goal:** a walking skeleton: an empty product that builds, deploys to Dev and is observed, with every guard on from
the first commit. **Accountable:** the tech lead. **Follows:** Twelve-Factor App (deploy configuration in the
environment), trunk-based development, AGENTS.md (agent instructions), FinOps (tags and budgets from day 1).

This page also fills the catalog slot "Add a new app" (GUIDE-08). For a new app inside AA-Ecosys, the
[AA profile](aa-profile.md) adds the ADR 0008 twelve-step playbook.

## Deliverables

| Area | Deliverable |
|---|---|
| Repos | Generated from the template repo (planned, AA-1103); branch protection and the merge queue on |
| CI | Green on an empty PR: tests, lint, PR-title check, secret scan (PR and full history), docs lint, workflow lint |
| Local guards | Pre-push hook with the fast checks; code-health and coverage ratchets with an empty baseline |
| Agents | `AGENTS.md` as the instruction source, `CLAUDE.md` importing it, guardrail hooks with their tests |
| Tracker | Project, plan file and first backlog |
| Cloud | Account and roles through infrastructure as code; CI-to-cloud OIDC (no static keys); tags and a budget alert |
| Secrets | Secret store entries and a secrets register (names only) |
| Identity | An identity provider client per app |
| Database | Schema with owner and runtime roles; first migration `<prefix>-001` applied from CI ([migration template](../templates/migration-file.md)) |
| Platform services | Job table and worker; settings registry ([settings entry template](../templates/settings-entry.md)) |
| Observability | Structured logs, error tracking, `/health` (returns the commit SHA) and `/health/ready` |

## Gate G3: walking skeleton

| # | Question |
|---|---|
| 1 | Does `/health` on Dev return the commit SHA, deployed by CI (not by hand)? |
| 2 | Are all checks green on an empty PR? |
| 3 | Does a budget alert exist at the figure quoted at G1? |
| 4 | If multi-tenant: does the isolation probe pass (tenant A cannot see tenant B)? |
| 5 | Are no static cloud keys in CI or on a laptop profile used by CI? |
| 6 | Is every resource tagged with app and environment? |
| 7 | Does a fresh clone run locally from the `CONTEXT.md` "Run it locally" steps alone? |

## Common mistakes

- Building features before the skeleton deploys; every later step is then slower to prove.
- Turning guards on "later": a ratchet that starts empty is free, one added on a big codebase is a project.
- Long-lived cloud keys in CI instead of OIDC.
- A `/health` that answers 200 without saying which commit runs.
- Applying the first migration from a laptop.
