---
id: GUIDE-14-architecture
title: "Phase 2: Architecture"
description: Choose and record the boundaries that are hard to reverse before code - deliverables, gate G2 checklist, templates and common mistakes.
type: how-to
status: draft
owner: nghiep
audience: [cto, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-discovery, GUIDE-14-setup]
---

# Phase 2: Architecture

**Goal:** choose the boundaries that are hard to reverse, and write them down before code. **Accountable:** the tech
lead. **Follows:** arc42 (the one-page canvas, not all twelve sections on day 1), C4 (context, container and deployment
views as code), MADR (minimal ADRs), ISO/IEC 25010:2023 (quality names), OWASP ASVS 5.0 (security level per area).

## Deliverables

| Deliverable | Template |
|---|---|
| `CONTEXT.md` on the arc42 canvas, with C4 context and container views | [`CONTEXT.md` template](../templates/context-arc42.md) |
| First ADRs: stack, data ownership, identity, tenancy, environments | [ADR](../templates/adr.md) |
| HTTP API conventions | [HTTP API conventions ADR](../templates/adr-http-api-conventions.md) |
| Quality requirements under the nine ISO 25010 names | Section 11 of `CONTEXT.md` |
| Contract list and one contract folder per cross-app read | [Contract](../templates/contract.md) |
| Schema ownership row: which repo writes which schema, with its key space | Project's schema ownership page |
| Light threat model | [Threat model](../templates/threat-model.md) |
| Privacy register rows for every personal-data entity, with retention | Project's privacy register |
| AI use register rows, if the product uses AI | Project's AI use register |

## Gate G2: design accepted

| # | Question |
|---|---|
| 1 | Does every entity have exactly one writer? |
| 2 | Does every cross-app read go through a named, versioned contract? |
| 3 | Is the security level chosen per area: ASVS level 1, level 2 for auth, payment and personal data? |
| 4 | Does every personal-data entity have a privacy register row with its retention? Is the impact assessment done when G1 said high risk? |
| 5 | Are the running costs estimated per environment and added to the cost sheet? |
| 6 | Is the environment model chosen (how many, what each holds, how a change moves)? |
| 7 | Are the first ADRs written and accepted by the tech lead? |
| 8 | Does `CONTEXT.md` stay under its size cap, with module detail in linked pages? |

## Common mistakes

- Two services writing the same table "just for now".
- Reading another app's tables directly instead of through a contract view or API.
- A threat model that lists the six STRIDE letters but no real threat.
- Writing every arc42 section on day 1; fill the canvas, grow the rest with the code.
- Decisions made in chat and never written as an ADR.

## How AA does it

The [ecosystem architecture](../ecosystem-architecture.md), the [ADR index](../adr/README.md), the
[contracts](../contracts/README.md), the [data standards](../architecture/data-standards/README.md) and
[schema ownership](../database/schema-ownership.md); see the [AA profile](aa-profile.md).
