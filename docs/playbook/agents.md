---
id: GUIDE-14-agents
title: Running a project with agents
description: How one human and several AI agents run a project - roles, tolerances, guardrails, the session ritual, lanes, decision pages and instruction layering.
type: explanation
status: draft
owner: nghiep
audience: [cto, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-principles, TPL-01-session, GUIDE-02]
---

# Running a project with agents

What AA learned about running a team of one tech lead and several AI agents, written so another project can apply it.
**Follows:** AGENTS.md (open instruction format), the Thoughtworks Technology Radar techniques on agents (progressive
context disclosure, sandboxing, feedback flywheel; cautions on instruction bloat and documentation sprawl), PRINCE2
tolerances.

## Roles

| Role | Does | Never |
|---|---|---|
| Tech lead (human) | Approves the Definition of Ready, ADRs and spend; holds credentials, MFA and prod decisions | - |
| Business owner (human) | Business, legal and commercial decisions; reviews releases, cost and UAT | Technical approvals |
| Orchestrator agent (main session) | Picks work, writes or delegates code, gates, merges and deploys in the dev phase, verifies live, updates the tracker | Posts business updates without approval; touches prod without the tech lead |
| Subagents and a second coding agent (lanes) | Code, tests and commits in their own worktree | Push, merge, apply infrastructure, write secrets or cloud resources |
| Reviewer agent | Reviews risky classes through its lens | Merge |
| CI | Runs every check; is the final gate | - |

Agents may be Responsible for a phase, never Accountable.

## Tolerances

Agents act without asking inside the limits of the [tolerance table](principles.md#tolerances) and escalate only on a
forecast breach. "Decide, don't ask" and "no agent-made gates" are the same rule seen from two sides: carry an approved
direction through, and never invent a hold that the tolerances do not require.

## Decision pages

When something does need a human, bring one page, not a string of questions in chat:

- Plain-words context for each question: what it is about and why it matters now.
- Two to five options per question, plus "Other" with room to write.
- The proposed answer marked, with one line of why.
- Who answers each question (tech lead or business owner).
- Answers saved where the agent can read them back, so work resumes without retyping.

## Guardrails

Rules that matter are enforced by machines, not by memory:

| Guardrail | What it blocks |
|---|---|
| Subagent hook | Push, merge, infrastructure apply, cloud writes and secret writes from a lane |
| MCP write guard | Writes to trackers or docs from tools that should only read |
| Shell guard rules | Commands that caused a real mistake before (each rule cites its lesson) |
| Stop hook | Ending a session while unblocked work remains |
| Personal-data guard | Personal data in prompts, logs or commits |

Each hook ships with red-team tests that prove it blocks the bad case and lets the good case through.

## Session ritual

- **Start:** read the latest log, the backlog and the plan; check live state; propose 3 to 5 issues in plan order.
- **During:** keep a live checklist; write a lesson at root-cause time, with the guard that will stop it next time.
- **Close:** snapshot live state, add lessons, get business drafts approved, then write the log; every repo back on a
  clean main branch.

Template: [session checklist and session log](../templates/session-checklist.md).

## Lanes

- One worktree per lane, created from the latest main; lanes never edit the main checkouts.
- Each lane reads the repo's `CONTEXT.md` and the lessons of the area before it edits.
- Reviewers by lens: correctness for every change; security and data for risky classes; one fix pass.
- A lane returns a structured result: branches and commits, tests run, the live steps it could not do (with a ready
  script), and what is left.
- The orchestrator pushes, opens PRs, merges, deploys and runs the live steps.

## Instruction layering

| Layer | Holds | Loaded |
|---|---|---|
| `AGENTS.md` (source), `CLAUDE.md` importing it | Hard rules and pointers, kept short | Always |
| Skills | Procedures for one kind of task | On demand |
| Docs (`CONTEXT.md`, playbook, handbook) | The facts and the rules in full | Linked, read when needed |
| Lessons | Recent root causes, each with a guard field and a scope tag (project only, or generic for the kit) | Per area, before editing |

Keep the always-loaded layer small and measure it; move procedures into skills; turn checkable lessons into guards and
delete the line; prune at every 90-day review.
