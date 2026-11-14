---
id: GUIDE-14-principles
title: Playbook principles and tolerances
description: The seven principles of the new-project kit and the tolerance table that tells agents what they may do without asking.
type: explanation
status: draft
owner: nghiep
audience: [owner, engineer, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, CAT-01, docs/research/new-project-playbook/README.md]
---

# Playbook principles and tolerances

## The seven principles

1. **Profile over standards.** Each kit page names the standard it follows and says what it kept or dropped. No new
   method is invented where a well-known one exists.
2. **One home per fact.** Templates live once, in [`docs/templates/`](../templates/README.md). Phase pages link them;
   the template repo copies them under a byte-copy guard, so a copy can never drift from its source.
3. **Handbook-first.** A rule changes in the kit page first, then in skills and copies. The learning site renders from
   the same pages.
4. **Generic core plus overlay.** The kit carries no project names. A project keeps an overlay (accounts, services,
   people, trackers) that points at the generic pages; AA's is the [AA profile](aa-profile.md).
5. **Tolerances, not approvals.** Agents act inside agreed limits and escalate only when a forecast says a limit will
   be broken (PRINCE2 "manage by exception").
6. **Switches by phase.** Prod-only controls (error budget, on-call, enforced code owners, a least-privilege agent role)
   are written now and switched on at gate G7, not before.
7. **Prune.** Every page has an owner and a review window. Superseded rules are deleted, not kept beside the new one.

## Tolerances

The charter sets the limits for each project. Inside them the agent acts without asking and reports what it did.
When a forecast says a limit will be broken, the agent stops that part and brings one decision page to the
accountable human: plain-words context, the options, and a proposed answer.

| Tolerance | What it limits | Kit default | Escalate when |
|---|---|---|---|
| Time | Work per session and in flight | 3 to 5 issues per session; at most 8 issues In Progress; an appetite per issue | An issue will pass its appetite |
| Cost | Money spent | Monthly cost quoted, and a yes for each new paid item on its own; paid batch runs: a trial of about 3, then at most about 50 | A new paid item, or a run above its cap |
| Scope | What an issue delivers | Done-when frozen once the issue is In Progress; new scope becomes a new linked issue | The Done-when cannot be met as written |
| Quality | What "done" means | Every check green, not only the required ones; Definition of Done verified live | A check cannot be made green inside the issue |
| Risk | Changes that can hurt | Risky classes (auth or permissions, migration or schema, CI or secrets, data deletion) get an independent agent review; destructive steps need the tech lead's yes after a dry run | Any destructive step; any risk the review rates high |
| Benefits | Business value | Business questions go to the business owner as options with a recommendation | A choice changes what users get or what it costs them |

### What does not count as a reason to stop

- An open question that has a reasonable answer: write the proposed answer, act on it, report it.
- A plan slot or a date that is only an order: pull the item forward when its technical prerequisites are met.
- A "nice to check with someone": checks that an agent can run itself (a live call, a test login, a dry run) are run.

Real blockers are few: a credential or MFA step only a person can do, money, a decision only the accountable human can
make, and an irreversible step.

## Two kinds of configuration

| Kind | Examples | Where it lives |
|---|---|---|
| Deploy configuration | Endpoints, secret references, per-environment switches | The environment (Twelve-Factor factor III) |
| Policy values | Thresholds, limits, caps, budgets, retention windows, prices | An admin-editable settings registry with history, seeded with the approved default ([settings entry template](../templates/settings-entry.md)) |

The two rules do not conflict once configuration is split this way: an operator changes a policy value on an admin page,
without a deploy.

## Gates are short and honest

- A gate is a checklist of at most about ten questions, rated red, amber or green.
- Amber needs a follow-up with an owner and a date in the tracker; red stops the phase.
- The accountable human signs the gate; the agent prepares the evidence for each line.
