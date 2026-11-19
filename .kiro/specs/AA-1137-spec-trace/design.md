# Design - specs and trace

Spec: [requirements](requirements.md). Advisory: `docs/audits/2026-11-18-S284-hooks-spec-advisory/README.md` section 5.

## Decisions

### D1 Specs live in the repo that owns the work

Hard to reverse: no (a folder move)

`.kiro/specs/AA-<n>-<slug>/` in the owner repo, so Kiro finds it with `#spec` and Claude reads it as a file; work
across repos keeps its spec in the root repo and every task names its `repo:`. Archive: `.kiro/specs/_archive/`.

### D2 The session list approves the requirements

Hard to reverse: no (a skill rule)

Approving the session issue list approves the requirements of their specs (status approved, approved_at set by the
orchestrator). The tech lead approves only design decisions flagged `Hard to reverse: yes` (boundaries, grants, data
deletion, ADR-level) on the session decision page, recorded as an `Approved:` line. Tasks are not approved.

### D3 The PR check blocks only issues that have a spec

Hard to reverse: no (a workflow)

`spec-trace.yml` reads the issue keys of the PR text (merge queue: the commit messages) and the specs the PR changes.
No spec found: pass. It runs on `pull_request`, `merge_group` and `workflow_call` (app repos call it next wave), with
`contents: read` and no secret. It is not a required check in the root repo.

### D4 Task claims live in the session scratch folder

Hard to reverse: no (a hook state file)

`lane_start_guard.py` records the tasks a lane takes in `.tmp-session/spec-claims.json` (gitignored), keyed by spec
id, with the session and lane key. A claim of another session is stale and ignored; a relaunch of the same lane
passes.

## CONTEXT.md impact

None: no app boundary changes. The working rules page `docs/guides/working-rules/planning-and-issues.md` gains a
Specs section.

## Docs impact

- `docs/guides/working-rules/planning-and-issues.md` (+ `.vi.md`): spec kinds, approval, Done when = R ids + spec path.
- `docs/guides/working-rules/sessions.md` (+ `.vi.md`): the session list approves the specs.

## Test strategy

- R1, R2, R4.1, R4.2: unit tests on fixture specs in temporary folders (`tools/spec/test_trace_check.py`), plus this
  spec and the three templates as passing fixtures.
- R3.1, R3.2: hook self-tests (`.claude/hooks/test_lane_start_guard.py`).
- R3.3: the lane workflow run against a scripted `agent()` (`tools/workflows/test_lane.cjs`).
- R4.3, R4.4: workflow lint and docs lint tests; the live run of this spec's root PR.
