# Generic agent skills (new-project kit)

The generic skills of the new-project kit (design: `docs/research/new-project-playbook/` section 5.5). They hold the
procedures a project run by one tech lead and several AI agents needs, with no project names. The kit's template repo
copies this folder byte for byte into a generated project's `.claude/skills/`.

| Skill | Use it for |
|---|---|
| [`project-rules`](project-rules/SKILL.md) | Hard rules, tolerances, ADR rules, the lane brief template |
| [`project-session`](project-session/SKILL.md) | Start, during and close of a working session |
| [`project-ship`](project-ship/SKILL.md) | From PR to Done: checks, merge, deploy gate, verify live |
| [`project-lessons`](project-lessons/SKILL.md) | The lesson log and turning lessons into guards |
| [`project-issue`](project-issue/SKILL.md) | Tracker issues: ready, in progress, done with evidence |
| [`project-business-update`](project-business-update/SKILL.md) | Progress updates for the business owner, drafted then approved |
| [`project-ui-verify`](project-ui-verify/SKILL.md) | Checking a UI change before calling it done |
| [`project-batch-run`](project-batch-run/SKILL.md) | Paid or long batch runs in a ladder with stop conditions |
| [`project-uat`](project-uat/SKILL.md) | UAT scripts and recordings for business sign-off |

## Rules for these files

- English, at most about 150 lines per `SKILL.md`; details go into `references/` and load on demand.
- No project names, paths outside the generated layout, account IDs or people. Values a project sets (tracker, issue
  key prefix, repos, health URLs, deploy commands) are read from the **Project parameters** section of the project's
  `AGENTS.md`; a skill names the parameter, never a value.
- A rule changes here first, then in the project overlays (handbook-first, playbook principle 3).

## Overlays

A project keeps its own skills on top: they point at the generic skill for the procedure and add only what is
project-specific (accounts, service names, people, channels).

<!-- kit:skip -->
AA's overlay is the `skill/aa-*` and `skill/ai-nghiep` folders, mapped in `docs/playbook/aa-profile.md`. The text
between the kit markers in this repo is left out of the template copy (`tools/project-kit/kit_transform.py`).
<!-- /kit:skip -->
