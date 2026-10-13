# Next session (S235): multi-lane agent team pilot — approved by Nghiệp 13/10/2026

Design and constraints: `10-agent-team-design.md`. This file records **what Nghiệp approved** and the concrete
lane plan for S235. Language for the session: Vietnamese with Nghiệp; English for code/PR/Linear.

## Decisions (Nghiệp, end of S234)
1. Commit format: subject `feat|fix|chore|refactor|docs: …`, body `Refs AA-xxx`. Never `[AA-xx]`, never `Fixes/Closes`
   (`~/.claude/CLAUDE.md` updated in S234).
2. "CIS first" relaxed: CIS stays primary; parallel lanes are allowed in the same session.
3. Guardrails: project hook `.claude/hooks/subagent-guardrails.sh` blocks subagents (hook input has `agent_id`) from
   push / merge / PR create / workflow run / secrets / terraform / ECS-RDS-Secrets writes / destructive git. The
   orchestrator (no `agent_id`) merges; `.claude/settings.json` allows `gh pr merge` in auto mode. Verified live in S234.
4. Lane A/B issue list pre-approved (AA-773 … AA-784). STS refreshed by Nghiệp at session start.
5. **Booking: build it** — new repo, CI, infra, DB role and `bk-001` from scratch — **after a document review** at
   the start of the session (PRD, ERD v2 `docs/AAA/erd-v2/booking.dbml`, Figma screens, `inquiry.submitted.v1`,
   ADR 0001 decisions 5–7, `docs/database/schema-ownership.md`).
6. Add an **ecosystem architect** agent that reviews the whole architecture (CIS, TripPlanner, Booking, Infra, shared
   RDS, contracts, jobs, auth) before lanes start and again before the merge train.

## Team (orchestrator = main session)
| Role | Kind | Responsibility |
|---|---|---|
| Orchestrator / integrator | main session | Gate 0–1 with Nghiệp, assigns lanes, owns merge train + deploy + Linear/Notion/log + shared files (`CONTEXT.md`, lessons, schema reference, sessions README) |
| Ecosystem architect | workflow agent (Opus, high effort), read-only | Gate 0.5: architecture review of all repos + ADRs → risks, contract gaps, Booking stack proposal (ADR draft), lane boundaries; Gate 3.5: review of cross-repo diffs before merge |
| Implementer × lane | workflow agents in worktrees | code + tests + local commit, structured JSON result; no push/merge (hook) |
| Reviewer | workflow agent, only for risky PRs | migrations, auth, data deletion, hot files (`services/acp_content_writing/*`) |
| QA / UI verify | agent | `aa-ui-verify` on previews; Booking: smoke on its first deploy |
| Scribe | agent (draft only) | session log / Linear comment drafts; orchestrator posts |

## Lanes for S235
| Lane | Repo | Issues | Merge path |
|---|---|---|---|
| A — CIS backend (serial on hot files) | AA-CIS-App | AA-776 (XS bug), AA-773, AA-774, AA-775, AA-778, AA-780 → checkpoint r5 (≈$1.15, one paid window) | orchestrator train, one PR at a time, no merge while `shared.job` busy |
| B — CIS portal (parallel) | AA-CIS-App `frontend/` | small admin items (e.g. Place cards per-country progress for AA-784, Content Quality polish) | frontend-only PRs merge any time |
| C — Booking bootstrap (parallel, after doc review + architect) | new `AA-Booking` repo + AA-CIS-Infra | repo scaffold + CI + branch protection; Infra (ECR, ECS service, OIDC, DB role `booking`, API route); `bk-001` from ERD v2; health endpoint | Infra PR + DB Migrate need Nghiệp's approval (batched); repo creation is orchestrator-only |
| D — docs (parallel) | AA-Ecosys | Booking stack ADR, stale-doc fixes, ecosystem diagram update | root PR, orchestrator merges |

TripPlanner is not a lane in S235 (pilot 2 if S235 meets the criteria).

## Session protocol
1. Gate 0 (15′): STS, ECS/RDS, `shared.job`, `git worktree list`, open-issue counts per Linear project.
2. Gate 0.5: architect review (read-only) → findings + Booking ADR draft.
3. Gate 1: ONE batched approval message to Nghiệp (issues per lane with Done-when, Booking ADR, Infra plan, paid window).
4. Build: lanes in parallel, ≤4 agents in flight, every brief states commit format, file scope and bans.
5. Review/QA: ≤2 loops then escalate. Architect pass over cross-repo diffs.
6. Merge train: CIS backend serial (update-branch → CI → Deploy Dev → live verify); frontend any time; Infra/root
   batched for Nghiệp; long adhoc scripts as one-off ECS tasks only.
7. Done per `aa-ship`; journal at `.tmp-session/team/S235/journal.md`.

## Success criteria (written to the S235 log)
- ≥6 issues Done (baseline 3–5), Booking repo + CI green + `bk-001` applied on Dev (or a written blocker).
- 0 rebases caused by shared files; 0 false Done; Nghiệp approvals ≤5 batches.
- Orchestrator context not compacted (or recovered from the journal); LLM spend ≤$10 recorded.
