---
id: GUIDE-15-planning
title: Working rules - planning and issues
description: The canonical English rules for the backlog order, Linear issues (creation, Definition of Ready, quota, updates) and when an issue is Done.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-15, GUIDE-15-sessions, GUIDE-15-stakeholders, CAT-01, AA-1104]
lang: en
---

# Working rules - planning and issues

This page holds the **rules** for planning and for Linear issues. The procedures, with their commands and templates,
are the skills [`skill/aa-linear-issue/SKILL.md`](../../../skill/aa-linear-issue/SKILL.md) (issues) and
[`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) (merge, deploy, Done). If a skill and this page disagree,
the stricter rule applies until one PR fixes both.

## Order of work

- **One ordered queue.** The [live backlog](../../backlog/README.md) holds the order and the master plan tracker
  holds the session slots. Linear holds the state of each issue. Kanban, not sprints
  ([handbook §2.1](../../engineering-handbook.md#21-the-model)).
- **A slot is an order, not a gate.** Pull a later item forward when its technical prerequisites are met (W2).
  Only real dependencies block: a migration that must be applied first, a busy job table or an open wave, an MFA
  session, money, or a decision only the tech lead or the business owner can make.
- **Work in progress is capped.** At most 8 issues In Progress for the whole team. An issue In Progress either
  converges (Done with evidence, finished, or back to the backlog with the reason) or names what blocks it.

## Creating an issue

| Rule | Detail |
|---|---|
| Ask the tech lead first | Bring the proposed title, problem and scope in plain words, several at once, so a yes is enough |
| Check for a duplicate | Search with two or three key words, the backlog included. A near match is extended or commented on, not copied |
| One project per issue | Every issue belongs to exactly one project; a project stays under about 100 open issues |
| One issue is one deliverable slice | About one PR or a small group of PRs. Detail lives in the plan and the session checklist, not in more issues |
| English | Title, description and comments are English; the title has the form `[Area] what to do - main detail` and no Jira key |
| Priority by impact | Urgent: production broken or data lost. High: blocks the next work or a security risk. Medium: a useful improvement. Low: later |

The issue body follows the template Problem, Scope (with out of scope), Done when, Related. Done-when lines are
checkable on the real environment (a curl, a query, a page, a workflow run), never "code merged".

## Definition of Ready

An issue is handed to a lane, a subagent or Kiro only when it is Ready: goal, path (fix, small, feature, risky),
appetite in sessions (with a USD cap for paid runs), scope, 3 to 6 Done-when lines, the verify command, the risk
class, dependencies, docs impact and cost. The full checklist is the
[Definition of Ready template](../../templates/definition-of-ready.md). If the work outgrows its appetite, stop and
cut or split it; do not carry on.

## Keeping the free plan

Linear runs on the free plan, which caps the open issues of the workspace, and it is not upgraded.

- Closed issues are exported to `docs/linear-export/` in the session's root PR, then archived through the API.
- Never delete an issue to make room: a deleted issue and its evidence comments are gone after 30 days.
- Never make a planned issue the sub-issue of an issue that closes soon: archiving the parent archives its open
  children. Use a "related" link instead.

## Updating an issue

- Before writing to an issue, read it and check that its title matches what you are about to write. Issue numbers
  remembered from earlier in a session are not trusted.
- A new finding is a dated comment with its evidence, not a silent edit of the description.
- Work outside the scope becomes a new issue (ask first) linked as related, never added to the current one.
- When order is mandatory (a migration before the code that reads its column), link the issues as blocks and
  blocked by.

## When an issue is Done

- **Done means verified live.** Merged and green CI are not enough: the change is deployed, the rollout completed,
  and the live endpoint or page shows the result. The closing comment lists the PR, the deployed version, the live
  check and its result, the docs touched and the cost.
- **Done-when lines are frozen** once the issue is In Progress. New scope found on the way becomes a new issue.
  Wording may be clarified; meaning may not change.
- **Done with scope.** An issue may close with only part of its scope delivered when the delivered part is verified
  live and every remaining part has its own follow-up issue or a written trigger (a condition or a date). Otherwise
  it stays open.
- **Commits and PRs reference, never close.** The body carries a `Refs` line with the issue keys. No issue key in a
  title, no closing keyword (Linear would close the issue on merge). After each merge, deploy or migration of an issue
  that is still open, check that Linear did not close it automatically and reopen it if it did.
- Missing evidence keeps the issue In Review with what is missing written down.

## Related

- [Session rules](sessions.md) and [stakeholder communication rules](stakeholder-communication.md)
- [Engineering handbook, Definition of Ready and Done](../../engineering-handbook.md#64-definition-of-ready-and-done)
