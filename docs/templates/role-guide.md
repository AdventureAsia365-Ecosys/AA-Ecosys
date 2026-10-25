---
id: GUIDE-00-role
title: <Role> guide
description: <One sentence - what this reader gets from the page.>
type: tutorial
status: draft
owner: nghiep
audience: [engineer]  # one or more of: owner, staff, engineer, devops, cto, cio, pm, agent
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 90
related: [CAT-00, GUIDE-03]
---

# <Role> guide

<!-- Role guides live in docs/guides/<role>.md (ceo, new-engineer, devops, cto, cio, pm); the agent index is
docs/agents.md. Link to the source page for every fact; do not restate rules (one home per fact).
Language: English. The CEO guide is bilingual - each section in English first, then "Tiếng Việt" with the same
content (or a two-column table); keep both in step in the same PR. Facts that must be stated the same way in
every guide: Dev holds test data only (D-01); prod will be a separate RDS instance on acc2 (ADR 0001, C7.2a,
D-17), dated when go-live is set; security logs are kept 365 days, app logs 30 days (D-09, AA-872).
Delete this comment. -->

## Who this is for

<The reader, what they already know, what they do not need to know.>

## What AA-Ecosys is (five lines)

<Four apps on one AWS account (acc2): AA-CIS (content and catalog), AA-TripPlanner-Web (traveller front door),
AA-Booking (customers, trip cases, pricing, payments), AA-Partner (partner agencies' CRM and the tenant portal). Link ecosystem-architecture.md.>

## Your first day

1. <Access to request, with who grants it.>
2. <First page to read.>

## Your first week

1. <Task that teaches the system, with the guide or runbook it uses.>

## What you own and what you approve

| Area | You own / approve | Source |
|---|---|---|

## Recurring duties

| Cadence | Duty | Page |
|---|---|---|
| Monthly | <...> | <link> |

## Where truth lives

| Question | Open |
|---|---|
| <...> | <link> |

## Escalation

<Who to call for what; severity per docs/ops/incident-response.md.>

## Related

- [Glossary](../glossary.md)
