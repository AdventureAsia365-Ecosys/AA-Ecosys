---
id: APP-04-erd-design
title: "Design ERDs (planned schemas)"
description: "Index and rules of the hand-written design ERDs: one Mermaid page per planned schema, reviewed before its migrations and compared with the live dump by the drift check."
type: reference
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-cis-dev-db, ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
generated: false
related: [APP-04, APP-04-erd, AA-894]
---

# Design ERDs (planned schemas)

A design ERD is the diagram of a schema, first drawn **before** its migrations exist. It is reviewed in a PR together with the
ADRs and the PRD, and the migration PRs are reviewed against it. The generated pages one level up
([live ERDs](../README.md)) show what is live; this folder shows what is planned. The DB Schema Dump workflow never
writes here.

| Schema | Owner | Page | Live? | Drift check |
|---|---|---|---|---|
| `crm` | AA-Partner | [crm.md](crm.md) | yes, since `crm-001` (78 tables and 6 views at `crm-023`); the page is not in sync yet | report only (`enforce=false`) |
| `tripplanner` | AA-TripPlanner-Web | [tripplanner.md](tripplanner.md) | yes | enforced (`enforce=true`) |

## Drift check

After every DB Migrate apply and every night, the DB Schema Dump workflow runs AA-CIS-Infra
`db/check_erd_drift.py` on each page here against the live model (`erd.json`) and writes a report to its run
summary:

- tables in the design but not live, and live but not in the design;
- primary keys that differ, where the design gives one;
- FK edges missing or extra, compared as child table, FK columns and parent table.

A schema with no tables yet is reported as "not live yet" and passes. Drift fails the run only when the page says
`enforce=true`. Set it in the root PR that follows the first in-sync dump of that schema.

## Rules for a design page

1. One file per schema, named `<schema>.md`, with catalog front matter (`APP-04-erd-design-<schema>`,
   `status: draft` until the first migration, `generated: false`).
2. One marker comment under the title:
   `<!-- erd-design schema=<schema> enforce=false implied-fk=<column>:<table> -->`. `implied-fk` is optional: every
   box whose `<column>` is marked `FK` and has no drawn edge gets an FK to `<table>` (the tenant edge).
3. Mermaid `erDiagram` blocks, one per module, at most about 15 boxes each (docs style guide). The conventions of
   the generated pages apply: quoted names for Mermaid keywords and for `"schema.table"` of another schema, `PK`,
   `FK`, `UK` after the column, DM-6.1 tags as attribute comments.
4. Each table has its attribute block once on the page; a bare name in another diagram is a reference.
5. Relationship lines put the parent on the left and the child on the right, and the label is the child's FK
   column list (`"trip_id"`). The checker compares those columns with the live `FOREIGN KEY`.
6. Show keys and the state column only; full columns belong in the design document the page cites.
7. A migration that changes the design changes the page in the same PR; a decision the page made alone goes into its
   "Open points" table.
