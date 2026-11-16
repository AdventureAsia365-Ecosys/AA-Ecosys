---
name: project-ship
description: From pull request to Done - the checks before merge, who may merge in which phase, the deploy gate (no deploy while a job table has work), migrations as expand or contract with their order, deploy, verify live, and the evidence that moves an issue to Done. Use before merging a PR, deploying, applying a migration or infrastructure change, rolling back, or setting an issue to Done.
---

# project-ship

Template: `docs/templates/release-checklist.md`. Parameters (in `AGENTS.md`): the repo list, the merge command, the
deploy commands, the health URLs per service, the migration apply command.

## 1. Definition of Done

Merged + CI green + deployed (rollout completed) + **verified live** (the health URL returns the new commit SHA and
the changed endpoint answers with the expected shape). A merged PR alone is not Done.

## 2. Before merge

- Every check green, not only the required ones; the PR title is `<type>: <description>`; the body has the
  `Refs <KEY>-<n>` line and no closing keyword.
- Risky classes (auth or permissions, migration or schema, CI, workflow or secrets, data deletion) had an independent
  agent review through its lens (correctness; security and data), with one fix pass.
- The branch is not stacked on another PR's branch (a stacked branch keeps the other PR's commits after it merges).

## 3. Who merges

| Phase | Merges |
|---|---|
| Dev (no production yet) | The orchestrator, when CI is green, including risky classes after their review |
| From the first production or paying customer | The tech lead approves infrastructure, IAM, migrations, auth and data deletion first; other PRs as in Dev |

Subagents never merge or push (the guardrail hook refuses it). Ship a wave of PRs with one command that runs the
independent PRs in parallel and only the migration chains in order; no hand-written loops of merges.

## 4. Migrations

- **Expand** (new table, new nullable column, new index): ships before the code that uses it, in its own PR.
- **Contract** (alter or drop an existing object, add a constraint or policy, insert config rows): only after no
  running code needs the old shape.
- Chain: migration PR merged, applied by CI to Dev, then the code PR. The code PR is branched from main, never from the
  migration branch.
- Destructive files: DRY RUN, then the tech lead's yes, then apply.
- No apply while a job table has queued or running work.

## 5. Deploy

- The deploy gate refuses while a job table has queued or running work or a batch run is open
  (`project-batch-run`); only the tech lead overrides it, with a written reason.
- Deploy from CI, never from a laptop. Wait one sensible interval (CI 3 to 5 minutes, containers 2 to 5) and check
  once; do not poll in a tight loop.
- Infrastructure applies run from main, never from a lane worktree or a feature branch.

## 6. Verify live, then Done

```bash
curl -s <health-url>          # expect the merged commit SHA
curl -s <health-url>/ready    # expect ready
curl -s <changed-endpoint>    # expect the documented shape
```

Write the evidence (command, status, the part of the answer that proves it) on the issue, then set it Done by hand.

## 7. Rollback

Roll back to the previous image or release with the project's rollback command; record an incident
(`docs/templates/incident-record.md`) when users were affected; write the lesson.
