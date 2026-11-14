---
id: TPL-01-session
title: Session checklist and session log template
description: The start, during and close steps of one agent working session, and the shape of the session log it leaves behind.
type: template
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01, skill/aa-session/SKILL.md]
---

# Session checklist and session log template

The generic session ritual (new-project playbook, agents page). AA's own version, with its memory store, live checks and
business updates, is the skill `skill/aa-session/SKILL.md`. Keep the live checklist as a scratch file during the
session; the log is written once, at the close, from the checked state.

## Start

- [ ] Read the latest session log, the live backlog and the plan file.
- [ ] Check live state: cloud identity, services and their commit, open job runs, open PRs, CI on the main branch.
- [ ] Propose 3 to 5 issues from the plan, in slot order, each with one to three plain lines; say why any is skipped.
- [ ] Start the live checklist with the approved list.

## During

- [ ] Each issue starts with its Definition of Ready checked and its implementation note opened.
- [ ] The checklist is updated after every finished step.
- [ ] A root cause found means a lesson line written now, with the guard that will stop it next time.
- [ ] Doable leftovers are done in the session, not listed as reminders.

## Close

1. Finish the work, then sync the tracker with evidence.
2. Snapshot the live state (services and commits, health, latest migration, job tables, open PRs).
3. Lessons: pending lines added to the lesson log, each with its guard field.
4. Business updates drafted, approved by the tech lead, then posted.
5. Then write the session log and the backlog, using the numbers from the snapshot.
6. Every repo back on the main branch with a clean tree.

## Session log shape

```markdown
# S<nnn> — <date> — <topic>

Agent: <tool and model>. Issues: <keys>.

## Done (verified)
- <issue>: <what, evidence link>

## In progress
- <issue>: <state, what is left, who unblocks it>

## Decisions
- <decision, by whom>

## Live state
<link to the snapshot>

## Lessons
- <lesson line, guard>

## Next
- <first issue of the next session and why>
```
