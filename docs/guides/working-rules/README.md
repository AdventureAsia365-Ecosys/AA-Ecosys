---
id: GUIDE-15
title: Working rules
description: Index of the canonical English working rules of the agent team - sessions, planning and issues, stakeholder communication - and where the rules W1 to W7 live.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-15-sessions, GUIDE-15-planning, GUIDE-15-stakeholders, CAT-01, GUIDE-02, GUIDE-13-lms, AA-1104]
lang: en
---

# Working rules

The rules agents follow lived in Vietnamese skills tied to repo paths. These pages are their canonical English text,
so that people and agents, and the AA Academy lessons, read the same rule (AA Academy gap G6,
[research §6.6](../../research/lms/README.md#66-one-source-for-humans-and-agents)).

**A rule page holds the rule; the skill holds the procedure.** An agent still loads the skill to do the work. When a
rule changes, change the page and the skill in one PR; if they disagree meanwhile, the stricter one applies.

| Page | Rules about | Procedure (skill) |
|---|---|---|
| [Sessions](sessions.md) | Sources of state, session start, the work during a session, the order of the session close | [`aa-session`](../../../skill/aa-session/SKILL.md) |
| [Planning and issues](planning-and-issues.md) | Backlog order, creating an issue, Definition of Ready, the Linear quota, updates, Done | [`aa-linear-issue`](../../../skill/aa-linear-issue/SKILL.md), [`aa-ship`](../../../skill/aa-ship/SKILL.md) |
| [Stakeholder communication](stakeholder-communication.md) | Progress posts for the business owner, business questions, decision pages, vendor messages | [`aa-jira-update`](../../../skill/aa-jira-update/SKILL.md), [`ai-nghiep`](../../../skill/ai-nghiep/SKILL.md) |

The seven numbered rules W1 to W7 apply across all three pages. They live in the
[engineering handbook](../../engineering-handbook.md): W1 "decide, don't ask" and W2 "no agent-made gates" in
[§2.4](../../engineering-handbook.md#24-two-working-rules-decide-dont-ask-no-agent-made-gates), W3 to W7 in
[§2.5](../../engineering-handbook.md#25-more-working-rules-for-agents).

Other rule homes, not repeated here: the docs style and the command rules (single-line AWS CLI, underscore variable
names) in the [style guide](../../STYLE.md); spend and quotes in [FinOps](../../ops/finops.md); merge rights in
[handbook §6.5](../../engineering-handbook.md#65-merge-rights-by-phase); the agent instruction stack in the
[agent index](../../agents.md).
