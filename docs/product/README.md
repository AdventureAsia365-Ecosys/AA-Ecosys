---
id: APP-10
title: "Product requirements (PRD as code)"
description: "What a PRD is in this repo, its front matter (linear, adrs, contracts, erd, migrations), the acceptance-criteria rule that Linear Done-when points to, and the list of PRDs."
type: reference
status: draft
owner: nghiep
audience: [owner, engineer, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
related: [APP-04-erd-design, ARCH-05, ARCH-07, AA-894]
---

# Product requirements (PRD as code)

A PRD (product requirements document) says **what** a feature must do for its users and **how we know it is done**.
It lives here, in Git, next to the ADRs, contracts and ERDs it points to, and is reviewed in a PR like code. Linear is
on the Free plan (S245), so the detail is here and a Linear issue only points to it.

A PRD is short. It summarises and links: the design document, ADRs, contracts and ERD hold the detail, and a PRD
never copies them. When a source changes a requirement, the PRD changes in the same PR.

## Where the parts live

| Question | Answered by |
|---|---|
| What must the feature do, for whom, and when is it done? | The PRD (`docs/product/<app>/<feature>.md` or `docs/product/<feature>/prd.md`) |
| Why this architecture, and what did we give up? | ADRs (`docs/adr/`, linked in `adrs`) |
| What crosses an app boundary? | Contracts (`docs/contracts/`, linked in `contracts`) |
| What does the data look like? | Design ERD before the migration, generated ERD after (`docs/architecture/erd/`, linked in `erd`) |
| What changed in the database? | Migrations (linked in `migrations` once they exist) |
| Who builds which slice? | Linear issues (keys in `linear`) |

## Front matter

A PRD carries the catalog front matter of the [style guide](../STYLE.md) (`docs/templates/frontmatter.schema.json`)
plus five PRD fields. The docs lint (`tools/docs/check_prd_refs.py`) requires them on every page under
`docs/product/` except this index, and fails when a listed path does not exist.

| Field | Content | Rule |
|---|---|---|
| `id` | Catalog ID `APP-10-<feature>` | Unique (front-matter check) |
| `status` | `draft` until the tech lead has read it; `active` while the feature is built or live | Schema enum |
| `owner` | Person accountable | Schema pattern |
| `linear` | Issue keys that deliver the PRD, e.g. `[AA-821, AA-928]` | At least one; `AA-<n>` |
| `adrs` | Repo-relative paths of the ADRs, e.g. `docs/adr/0010-aa-partner-app.md` | Each path exists |
| `contracts` | Repo-relative paths of the contracts the feature produces or consumes | Each path exists |
| `erd` | Repo-relative paths of the ERD pages | Each path exists |
| `migrations` | Migration files; a file in another workspace repo starts with its folder (`infra/AA-CIS-Infra/db/migrations/crm/...`) | Each path exists; other-repo paths are checked where that repo is checked out (locally), warned about in root CI. Empty `[]` until the first migration |

## Acceptance criteria and Linear

Each PRD ends with a section `## Acceptance criteria`. Every criterion is a list item that starts with a bold ID,
`**AC-<n>**`, unique in the page, and states something a test, a probe or a live check can show. IDs are never
reused or renumbered; a dropped criterion keeps its ID with "(dropped, reason)".

A Linear issue's **Done when** points to the criteria it closes instead of restating them, for example
"Done when: PRD partner-crm AC-1 and AC-2 pass on Dev (links)". The evidence goes into the Linear comment, as the
aa-ship rule requires; the PRD does not hold evidence.

## PRDs

| ID | Feature | App | Status |
|---|---|---|---|
| APP-10-partner-crm | [Partner CRM](partner-crm/prd.md) | AA-Partner (+ Booking, CIS) | draft |
