---
name: project-session
description: The working-session ritual for an orchestrator agent - start (read state, check live, propose issues in plan order), during (live checklist, lanes, lessons at root-cause time) and close (snapshot live state, lessons, business drafts approved, then the log and the plan; every repo back on a clean main). Use when a session starts or ends, when the user names a session number, or when work begins without context.
---

# project-session

Template: `docs/templates/session-checklist.md`. Parameters (in `AGENTS.md`): the tracker, the plan file, the
live-check commands, the session log folder (default `docs/sessions/`).

## 1. Start

1. Read the newest session log, the backlog (`docs/backlog/README.md`) and the plan file.
2. Check live state with the project's live-check commands: cloud identity, deployed version per service (the commit
   SHA from `/health`), job tables idle or busy, open PRs. Say "not checked" for anything you could not check.
3. Look at review dates that fall due (weekly metrics, monthly cost and capacity, quarterly access review) and add the
   due ones to the list.
4. Propose 3 to 5 issues (more in a long session) **in plan order**; say why any issue is skipped or pulled ahead.
   For each one write one to three plain lines: what it is, what will be done, how it will be verified.
5. Wait for the tech lead to confirm the list, then work through it without asking again (`project-rules` section 1).

## 2. During

- Keep a live checklist in `.tmp-session/S<nnn>-checklist.md`; tick each step as it ends.
- One worktree per lane; lanes return a structured result (`project-rules` section 5). The orchestrator pushes, opens
  PRs, merges, deploys and runs the live steps (`project-ship`).
- Write a lesson the moment a root cause is found (`project-lessons`); lanes report theirs in their result.
- Park steps only a human can do (MFA, a browser approval, a paid yes) in one list, keep working, and do them when the
  human is back.
- A side bug gets one fix and a follow-up issue, not a new lane.
- Do not offer to stop while doable work remains on the checklist.

## 3. Close (in this order)

1. **Converge the tracker:** each issue Done only with its verified-live evidence; unfinished ones keep a note of
   what is left.
2. **Snapshot live state** into the session folder: deployed version per service, `/health` and `/health/ready`,
   the newest migration per owner, job tables, open PRs.
3. **Lessons:** move the pending lessons into `docs/lessons.md` with their Guard field.
4. **Business drafts:** draft every update for the business owner (`project-business-update`), get them approved,
   then post.
5. **Then write:** the session log (numbers from the snapshot and the posted drafts), the backlog and the plan file.
6. **Clean:** every repo back on main with a clean tree; remove finished worktrees; the session's own PR merged.

## 4. Numbering

Sessions are numbered `S<n>` in one sequence; the log file is `docs/sessions/YYYY-MM-DD-<topic>.md` and the index
`docs/sessions/README.md` lists it. Name the acting agent in each log.
