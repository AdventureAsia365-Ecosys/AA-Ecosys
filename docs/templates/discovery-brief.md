---
id: PROD-00-discovery-replace-me
title: Discovery brief - <product or feature>
description: <One sentence - the problem, who has it, and the go / no-go asked for at gate G1.>
type: report
status: draft
owner: replace-me
audience: [owner, cto, pm, engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
related: []
---

# Discovery brief - <product or feature>

<!-- New-project playbook, phase 1 Discovery (docs/playbook/01-discovery.md). Built on the UK GDS discovery phase
(restate the solution as a problem, size the cost of the problem, stopping is not failure) and the 18F buy-versus-build
guide. Fill it with the business owner; the tech lead and agents add the research. Keep it to two pages. Store it in the
project's docs (for AA: docs/product/<slug>/). Delete this comment. -->

## 1. Problem

- **Who has it:** <user group, how many, how often>.
- **What happens today:** <the current way, its workarounds>.
- **Evidence:** <interviews, tickets, numbers, research notes; each with its source>.
- **Cost of the problem:** <time, money or risk per month if nothing changes>.

## 2. What success looks like

One measurable outcome, with today's value and the target: <metric, baseline, target, by when>.

## 3. Options

| Option | What it is | Rough cost (build and run per month) | Time to first value | Risks |
|---|---|---|---|---|
| Do nothing | Keep today's way | 0 | now | <...> |
| Buy or reuse | <product, module of an existing app, API client> | <...> | <...> | <lock-in, data residency> |
| Build | <new app or module> | <...> | <...> | <...> |

Buy-versus-build questions: is this a core differentiator? Does a product cover at least 80 % of the need? Who runs
it after launch? Can the data leave if the vendor fails?

## 4. Data and privacy screening

| Question | Answer |
|---|---|
| Personal data handled? | <yes / no> |
| Data classes | <contact, booking, payment, identity document, health, free text> |
| Countries of the data subjects and where the data will live | <...> |
| Lawful basis per purpose | <contract, consent, legitimate interest> |
| High risk (a full impact assessment needed)? | <yes / no, with the reason> |

## 5. Constraints and assumptions

- <Deadline, budget, team, technology, contracts.>
- <Assumption to test, and how.>

## 6. Recommendation for gate G1

- **Recommendation:** <go with option X / no-go / more discovery for N sessions>.
- **Appetite:** <sessions and USD the business owner accepts for the next phase>.
- **Running cost quoted:** <monthly cost of the Dev skeleton, from the cost sheet>.
- **Next:** if go, fill the project charter.
