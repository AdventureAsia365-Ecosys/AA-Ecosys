---
name: project-rules
description: Hard rules for an agent working on this project - tolerances (what to do without asking), escalation by decision page, cost, secrets, settings and verification rules, where an ADR goes, and the brief template for a lane or a second agent. Use at the start of any task that no other skill covers, before an architecture decision or an ADR, before any paid or destructive step, and when writing a brief for another agent.
---

# project-rules

The rules every agent follows on this project. The full reasoning is in `docs/playbook/principles.md` and
`docs/playbook/agents.md`; the project's own values are in the **Project parameters** section of `AGENTS.md`.

## 1. Tolerances: act inside them, escalate only on a forecast breach

| Area | Act without asking while | Escalate when |
|---|---|---|
| Time | the session holds 3 to 5 issues and at most 8 are In Progress; each issue stays within its appetite | an issue will pass its appetite |
| Cost | no new paid item; paid runs follow the ladder (3, then at most 50, then the rest) | a new paid service, plan or run is needed: quote the monthly cost first and wait for an explicit yes to that item |
| Scope | work stays inside the issue's Done-when | new scope appears: open a linked issue instead |
| Quality | every check is green and Done is verified live | a check must be skipped or weakened |
| Risk | the change is not in a risky class, or an independent agent review passed | a destructive step (delete, drop, rewrite history): DRY RUN first, then the tech lead's yes |
| Benefits | the work follows the agreed direction | a business, legal or commercial question: options with a recommendation for the business owner |

Two sides of one rule: **decide, don't ask** (carry an approved direction through, do the doable steps yourself) and
**no agent-made gates** (never invent a cap, a slot or a "needs clarification" the tolerances do not require).

## 2. Escalation: one decision page

When a human must decide, bring one page, not a string of questions: plain-words context per question, two to five
options plus "Other", the proposed answer marked with one line of why, who answers (tech lead or business owner), and
answers saved where the agent can read them back.

## 3. Hard rules

- **Verify live before claiming.** Never state a deploy, key, access, credit or rotation status from memory or old
  notes: check it now, or say it was not checked.
- **Secrets:** names only in docs, code, logs and commits; values live in the secret store. A leaked value is rotated,
  even after a force-push.
- **No static cloud keys** in CI or on a profile CI uses: CI reaches the cloud through OIDC.
- **Thresholds are settings.** Every threshold, limit, cap, quota, budget, retry limit or retention window is an
  admin-editable setting (seeded default, audited), never a code literal or an environment variable alone. Deploy
  configuration (endpoints, secret references, per-environment switches) stays in the environment.
- **Paid calls are logged.** Every call to a paid model or API writes a ledger row with its cost, also a failed call.
- **Tests never reach the cloud or a paid API**: hide the cloud config and mock paid calls.
- **One worktree per lane**, created from the latest main under `.tmp-session/wt/`; never edit the main checkout.
- **Subagents** code, test and commit locally; only the orchestrator pushes, merges, deploys or writes cloud
  resources (the guardrail hook enforces it).
- **Commit and PR format:** `<type>: <description>`; the body names issues on one `Refs <KEY>-<n>` line; never a
  closing keyword (`Fixes`, `Closes`) that would close the issue before it is verified live.
- **Language:** product text, code, PRs and tracker items in the project's primary language; a translated page is a
  sibling file `<name>.<lang>.md`.
- **Roles, not names**, in project docs: "tech lead", "business owner".

## 4. ADRs

Write an ADR for a decision that is hard to reverse. Ask: "if we reversed this, which repos would change?" Two or more
repos: the root repo's `docs/adr/`; one repo: that repo's `docs/adr/`. Use `docs/templates/adr.md` (full or
MADR-minimal shape). A superseded ADR gets a status line pointing to its successor; it is not rewritten.

## 5. Brief for a lane or a second agent

```text
Task: <issue key and title>. Repo and base: <repo>, a worktree from origin/main under .tmp-session/wt/.
Read first: CONTEXT.md, the lessons of the area, the issue, <named docs>.
Do: <scope>. Done when: <checkable lines>.
Must not: push, merge, deploy, apply, write secrets or cloud resources, call paid APIs.
Tests: <targeted test command>, the repo's pre-push checks, a secret scan of the new commits.
Return: branches and commits, tests run with results, PR title and body, live steps for the orchestrator, lessons.
```
