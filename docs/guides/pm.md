---
id: GUIDE-07
title: PM guide
description: How work is planned and tracked in AA-Ecosys - Linear projects and limits, Definition of Ready and Done, the live backlog, session rhythm, Jira with the business owner, releases and UAT, feature flags, and how to write an issue an agent can execute.
type: how-to
status: draft
owner: nghiep
audience: [pm]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
related: [TPL-01-dor, PLAT-01, APP-07, OPS-06, GUIDE-04, AA-897]
---

# PM guide

How the whole delivery system works: [engineering handbook](../engineering-handbook.md).

## Who this is for

You plan and track work: you turn requests into issues, keep the queue in order and report progress to the
business. Most code is written by AI agents (Kiro, Claude Code subagents) and gated by Claude Code and the tech lead, so
the quality of an issue decides the quality of the result. After this page you can write an issue an agent can
execute, keep Linear and the backlog in step, and close the loop with the business owner.

## Where work lives

| Tool | Holds | Rule |
|---|---|---|
| **Linear**, workspace and team `AA_Ecosys` | Every engineering work item | English. Ask the tech lead before creating an issue (D-24) |
| [Live backlog](../backlog/README.md) | The ordered queue, time-gated checks, decisions waiting on the tech lead | Updated by hand at the end of each session (D-22) |
| **Jira** (projects PR, KAN, CON) | Requests from the business owner and the business side | Vietnamese, drafts approved before posting |
| Notion → Program Brain → memory.md | Short pointers between sessions | Vietnamese, newest first |
| `docs/sessions/` | What each session did | Vietnamese |

Linear projects (2026-10-28): **CIS Core — Pipeline, LLM & Platform**, **Data Platform — Schema, Ops & Scale**,
**CIS Portal — Admin & Tenant UI**, **TripPlanner & AA-Booking**, **Partner CRM — AA-Partner**. Every issue belongs to
one project. A project holds at most **100 unarchived issues**, and the Free plan at most 250 in the workspace, so one
issue is one deliverable slice (about one PR) and the detail lives in a local plan or checklist. At the end of each
session, export closed issues to `docs/linear-export/` and archive them through the API
(`python3 tools/linear/linear_export.py --archive --apply`); never delete an issue to make room.

## Writing an issue an agent can execute

Use the house template from `skill/aa-linear-issue/SKILL.md` (Problem / Scope / Done when / Related) plus the
[Definition of Ready](../templates/definition-of-ready.md) sections. An issue is ready when it has:

1. **Problem** with evidence (session, PR, numbers), not "might".
2. **Goal**: the business outcome in one or two sentences.
3. **Scope**: repo, schema, files, endpoints or pages in and out.
4. **Done when**: 3 to 6 checks on the real environment ("`GET /x` returns field `y`", "page Z shows ...").
5. **Verify**: the exact curl, page, query or workflow run that proves it.
6. **Risk class**: none, auth, migration, IAM/secret, delete, cost or LLM. Anything but "none" gets the
   `kiro-reviewer` review before merge.
7. **Dependencies** and **docs impact** (CONTEXT.md, ADR, runbook, contract).

Check for duplicates first; check the issue number before you write it anywhere. A good test: could someone who has
never seen the codebase verify "Done when" with no questions?

## Definition of Done

An issue is Done only when it is merged, CI is green, the deploy finished (rollout COMPLETED) and the change was
**verified live**, with the evidence in a Linear comment (`skill/aa-ship/SKILL.md`). Merge alone is not Done.

- Commits and PRs say `Refs AA-123`. Never `Fixes` / `Closes` (Linear would auto-close) and never `[AA-123]` in the
  subject.
- Status changes only with real progress and evidence; In Progress issues should converge every session.

## Session rhythm

1. **Start**: read memory and the live backlog §1-§3, check the real state, propose issues from the queue (3-5, or
   8-10 in an Ultracode session); the tech lead picks (`skill/aa-session`). No full re-audit of Linear unless the backlog file is older than about two weeks.
2. **During**: carry each picked issue end to end. Explain each issue (what, who does it, how it is verified)
   before starting it.
3. **End**: update the backlog (status, closed items to §5, new items), session log, Notion memory, Linear; prepare
   Jira drafts for the business owner in one batch.

## Jira and the business owner

- Every Jira comment is a draft first; the tech lead approves it before it is posted (`skill/aa-jira-update`).
- Write in Vietnamese, short, under the tech lead's name, no internal Linear keys, and tag the business owner with a
  real mention.
- Do not create Jira issues or change their status on your own.
- Report a feature request on Jira only after it has shipped; note it in Linear meanwhile.
- Every claim of "works" needs live evidence per channel tested, with screenshots; say what was not tested.
- Business and legal questions go to the business owner as calm proposals with options (the [CEO guide](ceo.md)
  lists the decisions that are the owner's).

## Releases and UAT

- Every merge to `main` deploys to Dev. A "release" for the business is a short note of what users can now do:
  template [`templates/release-note.md`](../templates/release-note.md), posted as a Jira draft.
- Each app repo tags its versions and writes its `CHANGELOG.md` with release-please (AA-891).
- **UAT** is recorded as short videos for all apps, once the technical work is done or when the tech lead says (AA-855);
  template [`templates/uat-report.md`](../templates/uat-report.md).

## Feature flags

A deploy is not a release: a flag can keep finished code dark until the business is ready. The flag register is
`docs/ops/feature-flags.md` (AA-892), a document, not a table. Each flag has an owner and a remove-by date, except
tenant-pool flags, which are a security control and stay.

## Paid work and cost

Paid AI or data runs start with a trial of about 3 items, then at most about 50 tours; never the whole catalog
without the tech lead's approval. Any new paid service needs a monthly price and approval before it is switched on.

## Where truth lives

| Question | Open |
|---|---|
| What is next? | [Live backlog](../backlog/README.md) §3 |
| What waits on the tech lead? | Live backlog §2 |
| Platform roadmap items (U-xx) | [Handbook §9](../engineering-handbook.md#9-roadmap); keys in [backlog §3a](../backlog/README.md#3a-platform-roadmap-keys-plat-01) |
| Who approves what? | Data standards [Part B §11](../architecture/data-standards/02-data-management.md#11-change-management) (merge rights per D-13, DM-11.5 in v1.1) |
| What does this term mean? | [Glossary](../glossary.md) |

## Related

- [CEO guide](ceo.md), [CTO guide](cto.md), [new engineer guide](new-engineer.md)
- `skill/aa-linear-issue/SKILL.md`, `skill/aa-ship/SKILL.md`, `skill/aa-session/SKILL.md`, `skill/aa-jira-update/SKILL.md`
