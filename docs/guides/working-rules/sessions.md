---
id: GUIDE-15-sessions
title: Working rules - sessions
description: The canonical English rules for running a working session of the agent team - what to read and check at the start, how work runs during the session, and the fixed order of the session close.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-15, GUIDE-15-planning, GUIDE-15-stakeholders, CAT-01, GUIDE-02, AA-1104]
lang: en
---

# Working rules - sessions

A session is one sitting of the agent team: the orchestrator (the main Claude Code session) and the lanes it starts.
This page holds the **rules**. The step-by-step procedure, with its commands, is the session skill
[`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md), which agents load. If the two disagree, the
stricter rule applies until one PR fixes both.

The rules W1 to W7 of the [engineering handbook](../../engineering-handbook.md#24-two-working-rules-decide-dont-ask-no-agent-made-gates)
hold in every session; this page does not repeat them.

## Sources of state

| Rule | Why |
|---|---|
| Read the recorded state first: the session memory, the latest session log, the [live backlog](../../backlog/README.md) and the master plan | The next session starts where the last one stopped, not from memory |
| When sources disagree, repo beats the canonical Notion page, which beats memory, which beats a skill. Report the disagreement; never pick silently | One order for every reader ([handbook §2.2](../../engineering-handbook.md#22-sources-of-truth-for-process-state)) |
| Check the real state before acting: the caller identity of the AWS profile, the ECS services, the job tables, the AI gateway, the scheduled guard runs | A status that can change is checked live or reported as "not checked" (W5) |
| Record when the MFA session expires and act before it does | A long merge train dies half way when the session expires |

## Session start

1. **Propose the issue list from the master plan.** Issues planned for this session first, then the next slot, then
   milestone order. A slot is an order, not a gate (W2): pull an item forward when its prerequisites are met. Say why
   any item is skipped or pulled ahead.
2. **Size.** 3 to 5 issues in a normal session; 8 to 10 when parallel lanes run.
3. **Converge first.** List every issue In Progress. Close what meets its Done-when, finish what is nearly done,
   and name what blocks the rest. The whole team holds at most 8 issues In Progress (cap set by the tech lead); above
   it, the session converges before it starts anything new.
4. **Recurring reviews.** When due, the weekly query review, the monthly capacity and cost review and the quarterly
   access review join the session list (data standards C4.3, C8, DM-8.10).
5. **Update the master plan before any lane starts.** Once the tech lead confirms the list, the tracker shows this
   session's issues, then lanes open.

## During the session

| Rule | Detail |
|---|---|
| Keep a live checklist | One file per session, updated after each step; it is the source of the session log |
| Capture a lesson at root-cause time | One line in the pending lessons file the moment the cause is found, moved to the lessons log at close ([lessons](../../../skill/aa-lessons/SKILL.md)) |
| Explain each issue as it starts | Three to six plain lines: the problem, what will be done, who does it, how it is verified |
| The orchestrator holds the live rights | Only the orchestrator pushes, opens and merges PRs, runs workflows, Terraform apply, DB Migrate and ECS exec. A lane writes code, tests and runbooks in its own worktree and scratch folder and hands live steps back (a hook enforces this) |
| Questions carry a proposed answer | Plain-words context plus the answer you would pick; several questions become one decision page. An open question is not a reason to stop (W1) |
| Dev does not wait | Dev holds test data only and has no real traffic: create the evidence now instead of waiting for a time window |
| Save what the session produces | Audits, reports and decision pages go into `docs/audits/<date>-S<nnn>-<slug>/` and the session's root PR |
| Finish before closing | Doable work (an issue In Progress, a side finding, a live check) is done in the session, not listed back as a reminder |
| Never toggle infrastructure | Agents do not start, stop or scale ECS, RDS or NAT. A stopped service is reported to the tech lead |

## Session close

The order is fixed: **close the work, check the real state, lessons, approved Jira posts, then write the logs**.
Logs come last so that every number in them was checked, not remembered.

1. **Close the work in Linear.** A verified issue goes to Done with an evidence comment; an unfinished one stays
   In Progress with what is left and what blocks it. Then audit every issue that moved to Done for its evidence.
2. **Snapshot the real state** before writing any log: task definitions and image versions per service, health
   endpoints, the latest migration per owner, the job tables and open waves, the head and open PRs of each repo,
   and anything left switched on deliberately for the next session. Names and numbers only, never an account ID or
   a secret value.
3. **Lessons** move from the pending file into the lessons log.
4. **Jira drafts** are shown to the tech lead once, verbatim, approved, then posted
   ([stakeholder rules](stakeholder-communication.md)).
5. **Then write**, from the snapshot and the Jira result: the session log, the memory block (prepend only, never
   delete an old block), the live backlog and the master plan.
6. **Package the changed skills**, export and archive the closed Linear issues, and merge the session's root PR
   once docs lint is green.
7. **Leave every repo clean** on its default branch, and leave the environment running.
8. **Summarise in three lines:** done, left (and what blocks it), where the next session starts.

## Related

- [Planning and issue rules](planning-and-issues.md) and [stakeholder communication rules](stakeholder-communication.md)
- [Agent instruction index](../../agents.md)
- [Engineering handbook, operating model](../../engineering-handbook.md#2-operating-model)
