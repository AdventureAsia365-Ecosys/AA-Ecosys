# Task <task-id> — <AA-xxx> <one-line title>

## Goal
<1–3 sentences: what must be true when done, and why.>

## Repo / branch
<absolute repo path> on `<feat|fix|chore>/<aa-xxx>-<slug>` (already checked out by Claude Code).

## Read first
- `<repo>/CONTEXT.md`
- `/home/nghiep/projects/AA-Ecosys/skill/aa-lessons/lessons.md` — section(s): <…>
- <file:line pointers that matter>

## Scope
- <change 1>
- <change 2>

## Out of scope
- <what must not be touched / decided>

## Files in scope
- `<path/or/glob relative to the repo>`
- `<tests/unit/test_xxx.py>`

## Constraints
- No schema change unless listed above. No new dependency. Match the surrounding code style and comment density.
- Commit on this branch only, message format `<type>: <description>` + blank line + `Refs AA-xxx`. Do not push.

## Test commands
- `python3 -m pytest -q tests/unit -p no:cacheprovider`
- `python3 -m flake8 <changed .py files>`

Iterate (fix → re-run the commands above) until both are green before reporting. If you cannot get them green, stop and report why.

## Done when
- <measurable condition 1>
- <measurable condition 2>

## Report
Write `/home/nghiep/projects/AA-Ecosys/.tmp-session/kiro/<task-id>/result.md` with sections:
`## Summary`, `## Files changed`, `## Commands run`, `## Test results` (verbatim pass/fail lines),
`## Decisions not in the brief`, `## Open questions / risks`.
