---
id: spec-AA-1137
issue: AA-1137
title: Specs and trace - requirement, task, lane trace, PR check
status: in-progress
owner_repo: AA-Ecosys
kind: feature
approved_at: 2026-11-19 (S285 session list)
---

# Specs and trace

## Problem

Work runs from a Linear issue (Problem / Scope / Done when) plus implementation notes. There is no requirement list
with ids, no task list linked to the requirements, and no way to follow an issue from its acceptance criteria to the
tests, the PR and the live evidence without reading chat logs. Kiro's spec flow (requirements, design, tasks) gives
that trace; this spec adopts its file format and adds a checker, lane arguments and a PR check.

## Requirements

### R1 Spec format and approval

- R1.1 THE SYSTEM SHALL provide feature, bugfix and quick spec templates under `skill/aa-linear-issue/templates/spec/`
  that the trace checker accepts once their placeholders are filled.
  Verify: tools/spec/test_trace_check.py
- R1.2 WHEN an agent plans the issues of a session THE SYSTEM SHALL state in the issue and session skills and the
  working rules which issue needs which spec kind and how a spec is approved.
  Verify: live: skill/aa-linear-issue/SKILL.md section "Spec" and docs/guides/working-rules/planning-and-issues.md section "Specs" state the rule

### R2 Trace checker

- R2.1 WHEN a task names no requirement, or a requirement the spec does not define, THE SYSTEM SHALL report an error.
  Verify: tools/spec/test_trace_check.py
- R2.2 WHEN a requirement has no Verify line naming a test or a live step THE SYSTEM SHALL report an error.
  Verify: tools/spec/test_trace_check.py
- R2.3 WHEN a spec that was implemented at the base revision changes, other than its status moving to archived,
  THE SYSTEM SHALL report the change as frozen.
  Verify: tools/spec/test_trace_check.py
- R2.4 WHEN a spec file holds an account ID or another resource ID THE SYSTEM SHALL report an error.
  Verify: tools/spec/test_trace_check.py

### R3 Lanes

- R3.1 WHEN a lane is launched with a spec and tasks THE SYSTEM SHALL refuse the launch unless the spec is approved
  or in progress, every task exists and is open, and no other lane of the session holds one of them.
  Verify: .claude/hooks/test_lane_start_guard.py
- R3.2 WHEN a lane is launched without a spec THE SYSTEM SHALL apply only the gates it applied before.
  Verify: .claude/hooks/test_lane_start_guard.py
- R3.3 WHEN a lane has a spec THE SYSTEM SHALL require a trace entry per task in the lane output and add the
  reviewer lens "spec".
  Verify: tools/workflows/test_lane.cjs

### R4 Pull request check

- R4.1 WHEN a pull request names an issue that has a spec, or changes a spec, THE SYSTEM SHALL check that spec and
  fail the Spec trace check on an error.
  Verify: tools/spec/test_trace_check.py; live: the Spec trace run of the root PR of this spec checks spec-AA-1137 and is green
- R4.2 WHEN a pull request names no issue with a spec and changes no spec THE SYSTEM SHALL pass the Spec trace check.
  Verify: tools/spec/test_trace_check.py; live: the Spec trace run of a root PR without a spec passes with "No spec"
- R4.3 THE SYSTEM SHALL run the Spec trace workflow on pull_request and merge_group (never pull_request_target),
  with read-only contents permission, no secret and every action pinned by full commit SHA.
  Verify: test: .github/scripts/workflow_lint.py; tools/spec/test_trace_check.py
- R4.4 THE SYSTEM SHALL check every Markdown file under `.kiro/specs/` for literal resource IDs in the docs lint, as
  an error.
  Verify: tools/docs/test_docs_tools.py

### R5 Application repos

- R5.1 WHEN a pull request of an application repo names an issue that has a spec THE SYSTEM SHALL run the root Spec
  trace workflow for it.
  Verify: live: a Spec trace run on a pull request of each application repo
- R5.2 THE SYSTEM SHALL keep only issue specs under `.kiro/specs/`; a spec without an issue moves to
  `.kiro/specs/_archive/`.
  Verify: live: the TripPlanner repo lists no spec folder outside `.kiro/specs/_archive/`
