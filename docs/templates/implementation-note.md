# <ISSUE-KEY> — <issue title>

<!-- Implementation note template (new-project playbook, phase 4 Build). Store it at
docs/implementation-notes/<ISSUE-KEY>.md in the repo the change lands in, write it WHILE working, not after.
Implementation notes are journals: no front-matter, no translation. On the feature and risky paths, the Plan section
comes first and the diff should touch only the files it names; when the plan changes, update the Plan in the same
commit. Delete this comment. -->

## Plan

- **Path:** <fix | small | feature | risky> (from the Definition of Ready).
- **Files:** <paths that will change>.
- **Order:** <1. migration, 2. reader, 3. UI, ...>.
- **Risks:** <what could break, and the check that would catch it>.
- **Proof:** <the test, the live check or the screenshot that shows it works>.

## Decisions

- <A choice the issue did not specify, the options, and why this one.>

## Changed

- <What was built differently from the original requirement, and why.>

## Tradeoffs

- <What was weighed: speed against safety, cost against coverage.>

## Should know

- <Anything the reviewer needs before reading the diff: a live step left for the orchestrator, a follow-up issue,
  a setting to flip.>
