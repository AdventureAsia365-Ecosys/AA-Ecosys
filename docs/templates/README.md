---
id: TPL-01
title: Templates
description: Every doc template of AA-Ecosys and the new-project kit, by lifecycle phase, with what each one is for.
type: reference
status: draft
owner: nghiep
audience: [engineer, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [CAT-00, TPL-02, TPL-03, GUIDE-14]
---

# Templates

One home per template (playbook principle 2). Copy a template, fill it, and delete its guidance comment. Templates
carry placeholder IDs and are never published to the docs reader. The front-matter schema is
[`frontmatter.schema.json`](frontmatter.schema.json); the style rules are in the [style guide](../STYLE.md).

## By lifecycle phase

| Phase | Template | Use it for |
|---|---|---|
| 1 Discovery | [Discovery brief](discovery-brief.md) | The problem, its cost, options and the go / no-go asked at G1 |
| 1 Discovery | [Project charter](project-charter.md) | Product goal, success metric, appetite and tolerances |
| 1 Discovery | [Stakeholder map and RACI](stakeholder-raci.md) | Who is affected, who decides, one Accountable per phase |
| 1, then all | [RAID log](risk-register.md) | Risks, assumptions, issues and dependencies with owners |
| 1, then 7 | [Cost sheet](cost-sheet.md) | Monthly forecast, unit cost, paid items with their approval |
| 1, 2 | [Vendor selection](vendor-selection.md) | Options side by side before a contract |
| 2 Architecture | [`CONTEXT.md` on the arc42 canvas](context-arc42.md) | Repo boundaries, C4 views, decisions, run it locally |
| 2, then all | [ADR](adr.md) | A hard-to-reverse decision (full and MADR-minimal shapes, prune step) |
| 2 | [HTTP API conventions ADR](adr-http-api-conventions.md) | URLs, versions, errors, lists, idempotency for a new API |
| 2 | [Threat model](threat-model.md) | Assets, trust boundaries, STRIDE per container |
| 2, 4 | [Contract](contract.md) | A cross-app view, API or event with schema and samples |
| 3, 4 | [Migration file](migration-file.md) | Header, transaction, self-registration, expand / contract |
| 3, 4 | [Settings registry entry](settings-entry.md) | A threshold or policy value as an admin-editable setting |
| 4 Build | [Definition of Ready](definition-of-ready.md) | What an issue needs before work starts, with path and appetite |
| 4 Build | [Implementation note](implementation-note.md) | Plan, decisions, changes and tradeoffs, written while working |
| 5 Test | [Test strategy](test-strategy.md) | What is tested at which layer and what blocks a merge |
| 5, 6 | [Security checklist](security-checklist.md) | ASVS 5.0 level 1 (level 2 for auth, payment, personal data) |
| 5 Test | [UAT report](uat-report.md) | Business sign-off of a visible feature |
| 6 Release | [Release checklist](release-checklist.md) | Merge to verified live, by quality area |
| 6 Release | [Release note](release-note.md) | The business view of a release |
| 7 Operate | [Runbook](runbook.md) | Exact steps for one task, with the tested rule |
| 7 Operate | [Incident record](incident-record.md) | A light record opened when an incident starts |
| 7 Operate | [Postmortem](postmortem.md) | Blameless review, with the list of when one is required |
| 7 Operate | [Capacity and cost review](cost-report.md), [capacity review](capacity-review.md) | Monthly cost and capacity |
| 7 Operate | [Access review](access-review.md) | Quarterly: who can reach what |
| 7 Operate | [Delivery metrics report](delivery-metrics-report.md) | Weekly DORA and flow metrics |
| 8 Scale | [SLO and error budget policy](slo-error-budget.md) | Written early, switched on at first prod |
| 9 Retire | [Retirement checklist](retirement-checklist.md) | Nothing left running, stored or billed |
| All | [Session checklist and session log](session-checklist.md) | Start, during and close of an agent session |

## Page shapes

| Template | Use it for |
|---|---|
| [How-to](how-to.md) | Steps to reach one goal |
| [Reference](reference.md) | Facts to look up |
| [Explanation](explanation.md) | Why something is the way it is |
| [Role guide](role-guide.md) | One reader role's entry page |
