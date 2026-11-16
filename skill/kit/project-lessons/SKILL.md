---
name: project-lessons
description: The lesson log - write one principle the moment the root cause of a mistake is found, each line with a Guard field naming what stops it next time, read the area's lessons before editing, and turn checkable lessons into tests, hooks or CI checks, then delete the line. Use when something went wrong because of a wrong method or a wrong assumption, when a review finds a pattern error, and before editing an area that has lessons.
---

# project-lessons

Log: `docs/lessons.md`, one section per area. Each line is a **principle**, not an incident diary.

## 1. Read before you edit

Before editing an area, read its section. At session start, skim the sections of the chosen issues and the pending
lessons of the previous session. A lesson that contradicts the task is raised with the tech lead, not ignored.

## 2. When to write: at root-cause time

Write when a failure came from a wrong method or pattern, a wrong assumption (the issue's premise, memory, a guessed
name), a skipped verification that would have caught it, or a change that broke an earlier decision unseen. Do not
write plain typos, things a guard already catches, or session diary lines.

During a session, write into `.tmp-session/S<nnn>-lessons-pending.md`; move the lines into `docs/lessons.md` at
session close, so parallel lanes do not edit one file. Lanes report lessons in their result instead.

## 3. Line format

```text
- **<Principle, short imperative>** - <symptom -> root cause> (S<nnn>, <KEY>-<n>). Guard: <kind> <target>. Scope: <project|generic>.
```

| Guard form | When |
|---|---|
| `Guard: test\|hook\|tool\|ci\|lane <path>` | a machine check exists; the path must exist in the repo |
| `Guard: pending <KEY>-<n>` | the guard is planned; the issue is on the backlog or plan |
| `Guard: none: judgement\|external\|one-off <why>` | no machine can catch it; give a reason of three or more words |

`Scope: generic` marks a lesson another project would also need; it goes to the kit (the generic skills or the
playbook) at the next kit release.

## 4. Turn lessons into guards

A lesson a machine can check is the best kind: write the test, hook rule or CI check, name it in the Guard field, and
delete the line once the guard has caught the mistake for a while. A repeated mistake gets a guard in the same
session (or a planned guard issue), not a second line. A hook rule cites the lesson it replaces in its docstring and
ships with tests for the bad case and the near-misses.

## 5. Prune

At each 90-day review, delete lines whose guard exists and lines that no longer apply; merge duplicates.
