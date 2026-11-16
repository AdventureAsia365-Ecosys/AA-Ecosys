---
name: project-issue
description: Tracker issues from creation to Done - ask before creating, check for duplicates, the Definition of Ready (problem, scope, checkable Done-when, path, appetite), one issue per deliverable slice, the In Progress cap, status changes only with real progress, and Done only with verified-live evidence. Use when creating, updating, commenting on, assigning or closing an issue.
---

# project-issue

Template: `docs/templates/definition-of-ready.md`. Parameters (in `AGENTS.md`): the tracker, the issue key prefix,
the projects, the priority scale, any plan-quota rule.

## 1. Before creating

- Ask the tech lead before creating a new issue (during an approved list, follow-ups of that work are fine; say so).
- Search for a matching open issue first; comment there instead of creating a duplicate.
- One issue = one deliverable slice (about one PR or a small group of PRs). Detail lives in the issue's plan or the
  implementation note, not in sub-issues.
- Every issue belongs to one project.

## 2. Definition of Ready

```markdown
## Problem
<who is hurt, how, and the evidence>

## Scope
1. <what will be built or changed>
Out of scope: <what will not>

## Done when
* <checkable line: a command, a page, a number>

Path: small | standard | risky (risky = auth, migration, CI/secrets, data deletion: independent review)
Appetite: <how much effort it is worth; past it, stop and re-plan>
```

Done-when lines are frozen when the issue goes In Progress; new scope becomes a new linked issue.

## 3. While working

- At most 8 issues In Progress across the project; finish before starting.
- Change status only on real progress with evidence (a PR link, a run, a live check), never ahead of it.
- Keep `docs/implementation-notes/<KEY>-<n>.md` (Decisions, Changed, Tradeoffs, Should know) as you go.
- Comments are short and factual; link PRs and runs.

## 4. PRs and commits

- Subject `<type>: <description>`, no issue key in the subject.
- Body: one `Refs <KEY>-<n>, <KEY>-<m>` line naming every issue the PR mentions; describe other issues in words.
- Never `Fixes` / `Closes` / `Resolves`: the tracker would close the issue on merge, before it is verified live.

## 5. Done

Set Done by hand after `project-ship` section 6, with the evidence in a comment: what was checked, where, the result.
An issue that cannot be verified yet stays In Progress with a note of what is left and who or what it waits for.

## 6. Quota

On a plan with an issue cap, export closed issues to the repo (`docs/tracker-export/`) and archive them at session
close; never delete an issue to make room (its comments are evidence).
