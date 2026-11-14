---
id: PROD-00-raci-replace-me
title: Stakeholder map and RACI - <project>
description: <One sentence - who is affected by the project, who decides, and who is accountable for each phase.>
type: reference
status: draft
owner: replace-me
audience: [owner, cto, pm, engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 90
related: []
---

# Stakeholder map and RACI - <project>

<!-- New-project playbook, phase 1 Discovery. One Accountable per phase (common RACI rule). Agents may be Responsible,
never Accountable (AA's own rule). Name roles, not people, in company docs. Delete this comment. -->

## 1. Stakeholders

| Stakeholder (role or group) | Interest | Influence | What they need from us | Channel and cadence |
|---|---|---|---|---|
| Business owner | <...> | high | <decisions, cost summary> | <weekly report> |
| <users> | <...> | <...> | <...> | <...> |
| <vendors, partners, regulators> | <...> | <...> | <...> | <...> |

## 2. Team shape

<tech lead plus agents | several engineers plus agents | engineers only> (playbook index, "Other team shapes").

## 3. RACI per phase

A = accountable (one per row), R = responsible, C = consulted, I = informed.

| Phase | Business owner | Tech lead | Orchestrator agent | Subagents / second agent | CI | Vendors |
|---|---|---|---|---|---|---|
| 1 Discovery | A | R | R | C | - | C |
| 2 Architecture | C | A | R | C | - | C |
| 3 Setup | I | A | R | R | R | C |
| 4 Build | I | A | R | R | R | - |
| 5 Test | C | A | R | R | R | - |
| 6 Release | I | A | R | - | R | - |
| 7 Operate | I | A | R | C | R | C |
| 8 Scale | A | R | R | C | - | C |
| 9 Retire | A | R | R | C | R | C |

Change the defaults above only with a reason in the last column of a decision record.

## 4. Decision rights

| Decision | Who decides | Who is consulted |
|---|---|---|
| Go / no-go, scope, new spend | Business owner | Tech lead |
| Architecture, ADRs, merge of risky classes after first prod | Tech lead | Orchestrator agent |
| Routine merges and deploys in the dev phase | Orchestrator agent | CI |
