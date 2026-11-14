---
id: GUIDE-14-aa-profile
title: AA profile of the playbook
description: How AA-Ecosys maps onto the generic new-project kit - where each phase's AA rules, tools and examples live, and which rules are AA-only.
type: reference
status: draft
owner: nghiep
audience: [engineer, cto, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, CAT-01, GUIDE-02, GUIDE-08]
---

# AA profile of the playbook

AA-Ecosys is the reference application of the kit (kit decision D12): new repos start from the template repo, and the
existing AA repos align by hand when they are touched. This page is the overlay: it points from each generic page to
the AA source that holds the rule. When the two disagree, the AA source wins for AA work and the playbook gets an issue.

## Phase by phase

| Phase | AA sources |
|---|---|
| 1 Discovery | [ADR 0008](../adr/0008-new-app-integration-and-data-platform-rules.md) decision gate (new app, module or API client); research notes in [`docs/research/`](../research/new-project-playbook/README.md); the business model [ADR 0019](../adr/0019-b2b-only-ecosystem-model.md) |
| 2 Architecture | [Ecosystem architecture](../ecosystem-architecture.md); [ADR index and placement rule](../adr/README.md); [contracts](../contracts/README.md); [data standards](../architecture/data-standards/README.md); [schema ownership](../database/schema-ownership.md); [AI use register](../architecture/ai-use-register.md); [environment model](../adr/0012-environment-model.md) |
| 3 Setup | ADR 0008 section 3, the twelve-step playbook for a new app (design, owner registration, roles, first migration, tenancy, contract reads, events, identity, platform services, personal data, ops, isolation probe); [onboarding](../onboarding.md); [tagging standard](../architecture/tagging-standard.md); [secrets register](../security/secrets-register.md) |
| 4 Build | [Definition of Ready](../templates/definition-of-ready.md); skill `aa-linear-issue`; the root PR template; migration rules MIG-1 to MIG-14 in [data standards Part A](../architecture/data-standards/01-engineering.md); parallel lanes in skill `aa-session` |
| 5 Test | Each app's CI workflows (UI smoke, eval regression); skill `aa-ui-verify`; [UAT report](../templates/uat-report.md); [isolation probe](../ops/runbooks/isolation-probe.md) |
| 6 Release | Skill `aa-ship` (the Definition of Done, merge tools, deploy gate, verify live); [release note](../templates/release-note.md); [feature flags](../ops/feature-flags.md); skill `aa-jira-update` for the business update |
| 7 Operate | [Operations index](../ops/README.md); [incident response](../ops/incident-response.md); [postmortems](../ops/postmortems/README.md); [drills](../ops/drills/README.md); [FinOps](../ops/finops.md) |
| 8 Scale | [Scaling standard](../architecture/data-standards/03-scaling.md); [lean account model](../adr/0018-lean-aws-account-model.md); merge rights by phase (DM-11.5, handbook section 6.5) |
| 9 Retire | Account removal in [ADR 0001a](../adr/0001a-retire-acc1-llm-on-acc3-only.md); tour retirement in [ADR 0015](../adr/0015-tour-liveness-and-retirement-propagation.md); [dead table registry](../architecture/dead-table-registry.md); the DRY RUN procedure for destructive work in skill `aa-cis-schema` |

## Tolerances: AA values

| Tolerance | AA value | Source |
|---|---|---|
| Time | 3 to 5 issues per session (8 to 10 in a long session); at most 8 In Progress | Skill `aa-session` |
| Cost | Every new paid item quoted and approved on its own; paid runs: about 3, then at most about 50 | [Handbook](../engineering-handbook.md) working rules W3 and W4; [FinOps](../ops/finops.md); DM-10.6 |
| Scope | Done-when frozen at In Progress; one issue is one deliverable slice | Skill `aa-linear-issue` |
| Quality | Every check green; Done = verified live | Skill `aa-ship` |
| Risk | Risky classes reviewed by an independent agent; destructive steps after a DRY RUN and the tech lead's yes | DM-11.5; skill `aa-cis-schema` |
| Benefits | Business questions to the business owner as calm options with a recommendation | Skill `ai-nghiep` |

The working rules W1 to W7 (decide, don't ask; no agent-made gates; paid-run subset; quote before any paid item; verify
live before claiming; one report page for the business owner; every threshold an admin-editable setting) are in
[handbook section 2.4](../engineering-handbook.md#24-working-rules-for-agents).

## What AA does differently from the generic kit today

| Generic kit | AA today | Why |
|---|---|---|
| `AGENTS.md` as the instruction source | `.kiro/steering/` plus `.claude/CLAUDE.md` | Kept for now (kit decision D7); aligns when touched |
| Generic skills in English | AA skills in Vietnamese with AA paths | The AA overlay may stay Vietnamese (kit decision D8); generic skills come with AA-1103 |
| One repo from the template | A root repo plus five app and Infra repos, hand-built | Built before the kit existed; aligns by hand (D12) |
| Linear or another tracker | Linear on the Free plan, with export and archive at session end | Quota rule, skill `aa-linear-issue` |
| Business update channel | Jira comments drafted, then approved by the tech lead | Skill `aa-jira-update` |

## AA-only rules (not in the kit)

Product and operations specifics that the learning site teaches but the kit does not carry: the CIS content pipeline,
the Booking and Partner domains, the LLM account routing, the database migrate and exec runbooks, and the admin spend
page.
