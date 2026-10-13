# Agent dev team for CIS, TripPlanner and Booking in one session: corrected design after critic review

## 1. Feasibility verdict

**Short answer: partly yes, but less than the original design claims.** One orchestrator plus parallel workflow agents can run several lanes in one session. More agents will not speed up the part that limits throughput most, the CIS backend merge train. Booking cannot be built next session: there is no repo, CI, `bk-001` migration, DB role or Infra yet (`docs/ecosystem-architecture.md` §3.4 marks AA-Booking "(coming)"). Booking can only be a docs and readiness lane.

The original constraints table is mostly right. Corrections and additions from the critic:

| Constraint | Source (checked) | Effect, corrected |
|---|---|---|
| Speed of the CIS backend train | `skill/aa-lessons/lessons.md:50` (S222: strict up-to-date, BEHIND silently blocks auto-merge, parallel deploys race the ECS roll) | Each merge runs update-branch → CI again (5 required jobs, `skill/aa-ship/SKILL.md:14`) → Deploy Dev (6–7 min) → live verify. That is about 12–15 min per PR, so **4–5 per hour at most**, not the 6–8 per hour in the original design. |
| Jobs and waves freeze the train | `skill/aa-ship/SKILL.md:22-24`; memory `job-runner-in-api-process.md` (jobs now run on the `aa-cis-dev-worker` service and deploy with api) | Any paid run (`t9_write`, `place_cards_build`, …) or wave blocks **every** CIS backend merge. Recent CIS work (AA-768 rounds 1–7, S234) is a measure → fix → measure loop on the same `services/acp_content_writing/*` files. That loop is serial by nature, and parallel implementers cannot shorten it. |
| Linear cap is per shared project | `skill/aa-linear-issue/SKILL.md:13-17` | **TripPlanner and Booking share one project**, "TripPlanner & AA-Booking", with a 50-open-issue cap. The 3–4 TripPlanner plus 3–4 Booking issues in the original design all land in that one project. Count it at Gate 0. The whole workspace is also capped at 250 unarchived issues (Free plan). |
| TripPlanner merges | `apps/AA-TripPlanner-Web/CONTEXT.md:206-208`; memory `decide-dont-ask.md` (the auto-mode classifier blocks TripPlanner merges) | Nghiệp merges by hand. This is a second human-gated merge stream, not an agent lane. |
| Root PRs | `.kiro/steering/session-workflow.md` ("Repo gốc merge tay") | Contract-first means a human gate before any producer or consumer code. Each cross-repo contract adds a wait for Nghiệp. |
| Conflicting commit format | `~/.claude/CLAUDE.md` (`[AA-XX]`) vs steering and `aa-ship` (`Refs AA-xxx`; `[AA-xxx]` and `Fixes` auto-close issues) | Subagents load the global file too, so they may tag commits `[AA-XX]` and close issues by accident. Every brief must state `Refs AA-xxx` explicitly. |
| Agent concurrency | Machine has 32 CPUs (`nproc`), so the cap is min(16, 30) = 16 | Concurrency is not the binding limit. Nghiệp's attention, CI, the deploy train and the orchestrator's context are. |
| Priority rule | memory `cis-app-first.md` | Unchanged. Building three apps at once needs an explicit amendment from Nghiệp. |
| Paid runs | memory `paid-runs-subset.md` (trial of about 3, then 50 or fewer; state the cost before and after) | Paid runs and the merge train exclude each other (see the second row). Each paid run needs its own window. |
| Session size | memory `session-size-3-5-issues.md` | The 3–5 issue baseline already exists. The pilot must beat it, not 1 issue. |

A fully autonomous professional team is not possible here. Code, tests, review and QA can run in parallel. Merge, deploy, migrations, Linear issue creation and root/TripPlanner/Infra merges stay serial and human-gated.

## 2. Team roles

The original roles are kept, with these cuts:

- **Main session: Orchestrator + Integrator.** Unchanged: one STS cache, one writer each for Linear, Notion and the session log.
  - The orchestrator alone edits these shared, rebase-prone files, in one batch at the end of the session:
    - `docs/sessions/README.md`
    - `skill/aa-lessons/lessons.md`
    - each repo's `CONTEXT.md`
    - `docs/architecture/db-schema-reference.md`
    - `docs/database/schema-ownership.md`
  - Agents report lessons and contract deltas in their JSON result. They never edit these files.
- **Architect per app: dropped as a standing role.** One read-only planning agent per code lane, only when an issue has no clear Done-when. There is no Booking architect, because a readiness lane does not need one.
- **Implementer: 1 per lane.** Each runs in a git worktree under `apps/<repo>/.wt/<aa-xxx>`, with `Refs AA-xxx` stated in the brief.
  - Never more than one implementer on `services/acp_content_writing/*` at a time.
  - When "dùng kiro-cli" is on, Kiro takes backend and mechanical work (`.claude/skills/kiro-delegate/SKILL.md` §1–2, `aa-worker` bans at line 32).
- **Reviewer: only when risky**, matching `kiro-delegate` line 38 (auth, migration, CI, data deletion, hot files). Not on every PR, which would double the token cost for little gain.
- **QA / UI verify:** `aa-ui-verify` on the preview. Mandatory for frontend and TripPlanner work.
- **DB / migration agent: not in the pilot.** It drafts only and never applies.
- **Contract tester: not in the pilot.** Only `inquiry.submitted.v1.json` exists in `docs/contracts/`, so there is nothing to integrate against yet.
- **Scribe:** drafts only; the orchestrator posts.

**Native "Claude Code team" teammates vs workflow agents.** Workflow agents are one-shot: they return JSON and cannot talk to each other mid-task. A review → fix loop therefore always goes through the orchestrator, which costs its context. Do not plan a "chatting team". Plan batches of tasks with structured returns.

## 3. Session protocol

- **Gate 0 (15 min):** as in the original, plus:
  - count open issues in each of the 3 Linear projects, especially "TripPlanner & AA-Booking";
  - list `shared.job` jobs and any planned paid runs, since these decide when the train can run;
  - check stray worktrees with `git worktree list`. The original said to clean `.wt/pr1`, `pr2`, `pr4`, but that is stale: today only `main` is listed and `apps/AA-CIS-App/.wt/` is empty. The scoped skills still listed for those paths are a cached listing.
- **Gate 1 (20–30 min, not 45):** one batched approval message to Nghiệp. It covers:
  - the issues per lane, each with a Done-when;
  - the ownership map;
  - **a schedule of train windows vs paid-run windows** (they exclude each other);
  - the list of manual merges Nghiệp will need to do (root, TripPlanner, Infra).

  Do not fix wall-clock windows in advance. Use a "needs_human" queue that the orchestrator flushes to Nghiệp in batches, at most about once an hour.
- **Gate 2 — Build:** as in the original, with these changes:
  - Shared files are orchestrator-only (see section 2).
  - Each agent's brief carries the commit format, its file scope and the ban list.
  - Agents never run paid LLM calls. Any adhoc measurement goes through the orchestrator's paid window, logged to `shared.llm_call_log` with `stage="adhoc_<issue>"`.
- **Gate 3 — Review/QA:** at most 2 loops, not 3, then escalate.
- **Gate 4 — Merge train:**
  - Order as in the original.
  - Add a rule: **no CIS backend merge during a paid run or job**. Frontend-only PRs may merge at any time (`aa-ship:24`).
  - Long adhoc scripts run as one-off ECS tasks, or after the last merge.
- **Gate 5 — Done:** unchanged (`aa-ship` §3–4). Only the integrator marks Done.
- **Rollback:** unchanged.
- **Journal:** `.tmp-session/team/S<nnn>/journal.md` is kept. Results are compact JSON, and the orchestrator reads only `status`, `needs_human` and `risks`.

## 4. Session template and expected throughput

Drop the fixed 7.5h timetable. The schedule depends on three things: the job queue, the paid-run windows and when Nghiệp is available.

| Lane | Realistic PRs per session |
|---|---|
| CIS backend | 6–10, capped by the train at 4–5/h, minus paid-run windows. S234 already reached 12 App PRs in a single lane. **Parallel lanes add almost nothing here.** |
| CIS frontend (portal) | 3–5. This is the real parallel gain, because frontend-only PRs bypass the job guard. |
| TripPlanner | 2–4, limited by Nghiệp's manual merges. |
| Root docs / Booking-readiness | 2–3, merged by hand. |

- **Total output:** about 1.2–1.5x a good single-lane session, not 1.5–1.8x. The gain comes almost entirely from lanes outside the CIS backend.
- **Claude token cost:** about 2–3x, as originally estimated.
- **Nghiệp's attention:** expect 3–4 times as many approval and merge requests as a single-lane session. This is the real bottleneck.

## 5. Preparation before next session

Kept from the original: the stale-doc fixes (AAA accounts in `~/.claude/CLAUDE.md`, `ecosystem-review-2026-09.md`, the `tripplanner-to-aaa-handoff.md` path, the `docs/contracts` "not created" notes, the ADR 0001 status, the `schema-ownership.md` checkbox), the Booking stack ADR decision, the Linear pre-drafts and STS.

Changed or added:

1. **Commit format.** Nghiệp reconciles `~/.claude/CLAUDE.md` (`[AA-XX]`) with steering (`Refs AA-xxx`). It is Nghiệp's private file, so agents do not edit it. Until then, every brief states the format explicitly.
2. **Linear.** TripPlanner and Booking-readiness issues together must fit the "TripPlanner & AA-Booking" 50-open cap. Prefer extending AA-678 scope over creating new Booking issues (`aa-linear-issue`: duplicate check first).
3. **Priority rule.** Nghiệp amends `cis-app-first.md` only for the pilot ("CIS primary; one pre-agreed secondary chunk"). Otherwise the rule stands.
4. **Permissions.** As in the original (deny `terraform apply`, `gh workflow run`, `aws ecs update-service`, push to main, `gh secret`, `gh pr merge` for subagents). Use the `git-guardrails-claude-code` hook, so the rule holds even if a prompt is ignored.
5. **Skill and script.** Not written before the pilot. Write `skill/aa-team-session/SKILL.md` after the pilot, from measured data. A small workflow script for build, review and QA is enough.
6. **Cleanup.** Not needed: the worktrees are already gone.

**Risks (added to the original table):**

| Risk | Mitigation |
|---|---|
| Paid run blocks the CIS train | Separate windows; frontend lanes keep moving. |
| Rebases on shared files | Orchestrator-only edits, batched at the end. |
| Wrong commit tag auto-closes issues | Format stated in every brief. |
| "TripPlanner & AA-Booking" Linear cap | Count at Gate 0. |
| Human-gate pile-up (root, TripPlanner, Infra merges plus approvals) | Batched needs_human queue. |
| Stale skill or worktree listings mislead agents | Verify with `git worktree list`. |

## 6. Recommendation, with a minimal pilot

Do not run three apps next session. Run a **low-risk 2+1 pilot**:

- **Lane A, CIS backend (priority, serial):**
  - 2–3 issues from the "CIS Core" project.
  - One implementer at a time on hot files.
  - At most one paid window (a trial of about 3, under `paid-runs-subset`), scheduled when the train is idle.
- **Lane B, CIS frontend (parallel):**
  - 2–3 issues from the "CIS Portal" project.
  - No backend dependency, frontend-only PRs, QA through `aa-ui-verify`.
  - This proves parallelism without touching the job guard or other repos.
- **Lane C, read-only docs (parallel, no code):**
  - the stale-doc fixes, plus a draft `docs/adr/0004-booking-stack.md`;
  - one root PR, merged by Nghiệp.
- **TripPlanner: not in the pilot** (CIS-first rule, manual merge, shared Linear cap). Add it in pilot 2 if pilot 1 succeeds.
- **Limits:** at most 4 agents in flight, a session LLM budget of $10 or less, every result returned as JSON, and the journal kept.

**Success criteria, measured at the end and written to the session log:**

- Done issues reach at least 6. That is the 3–5 single-lane baseline plus the gain from Lane B.
- No merge conflicts or rebases on shared files.
- No false Done.
- Nghiệp's gate wait is recorded and his approvals stay at about 5 or fewer.
- The orchestrator context was not compacted, or the journal recovered it.
- Spend: Claude tokens and LLM dollars recorded.

**Scale-up path:**

- Pilot 2 adds the TripPlanner lane, only if pilot 1 meets the criteria above.
- Booking becomes a code lane only after all of the following, 2–3 sessions out at the earliest:
  - the stack ADR is approved;
  - the repo exists with CI and branch protection;
  - Infra is applied (ECS, ECR, OIDC, DB role `booking`);
  - `bk-001` is applied;
  - the CIS and TripPlanner grants are merged.

## Critic changes

1. **CIS train speed cut** from 6–8/h to 4–5/h: update-branch re-runs CI, then deploy and verify (lessons.md:50, aa-ship:14).
2. **New hard limit:** a paid run or job and the CIS backend train exclude each other (aa-ship:22-24, job-runner memory). The original planned paid runs "while no deploy runs" but did not see that they also block merges.
3. **Linear correction:** TripPlanner and Booking share one project with a 50-open cap (aa-linear-issue:13-17).
4. **TripPlanner merges are human-only** (CONTEXT.md:206, decide-dont-ask memory). This is a second manual stream, so TripPlanner is removed from the pilot.
5. **Commit-format conflict found:** `[AA-XX]` in the global CLAUDE.md vs `Refs AA-xxx`. Subagents would inherit the wrong format.
6. **Stale fact corrected:** the `.wt/pr1`, `pr2`, `pr4` worktrees no longer exist.
7. **Shared rebase-prone files** are now orchestrator-only, edited in one batch at the end.
8. **Roles cut back for the pilot:** standing architects, Booking architect, contract tester and DB agent are dropped; the reviewer runs only on risky PRs (kiro-delegate:38).
9. **Throughput cut** to 1.2–1.5x. The gain comes from frontend and docs lanes, not the CIS backend, and Nghiệp's attention is named as the bottleneck.
10. **Fixed clock gate windows** replaced with a batched needs_human queue.
11. **Concurrency is not the limit:** 32 CPUs give a cap of 16 agents, so in-flight agents are capped at 4 for context and attention reasons.
12. **Team skill postponed** until after the pilot, and a guardrail hook replaces prompt-only bans.
13. **Measurable success criteria** added, using the 3–5-issue single-lane baseline from memory.

Files checked:
- /home/nghiep/projects/AA-Ecosys/skill/aa-ship/SKILL.md
- /home/nghiep/projects/AA-Ecosys/skill/aa-lessons/lessons.md
- /home/nghiep/projects/AA-Ecosys/skill/aa-linear-issue/SKILL.md
- /home/nghiep/projects/AA-Ecosys/.claude/skills/kiro-delegate/SKILL.md
- /home/nghiep/projects/AA-Ecosys/.kiro/steering/session-workflow.md
- /home/nghiep/projects/AA-Ecosys/apps/AA-TripPlanner-Web/CONTEXT.md
- /home/nghiep/projects/AA-Ecosys/docs/ecosystem-architecture.md
- /home/nghiep/projects/AA-Ecosys/docs/contracts/inquiry.submitted.v1.json
- /home/nghiep/projects/AA-Ecosys/docs/adr/
- /home/nghiep/.claude/CLAUDE.md
- memories under /home/nghiep/.claude/projects/-home-nghiep-projects-AA-Ecosys/memory/: cis-app-first.md, paid-runs-subset.md, session-size-3-5-issues.md, decide-dont-ask.md, job-runner-in-api-process.md