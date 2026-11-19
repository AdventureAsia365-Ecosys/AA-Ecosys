---
id: spec-AA-<n>
issue: AA-<n>
title: <short name of the bug>
status: draft
owner_repo: <repo>
kind: bugfix
approved_at:
---

# <Short name of the bug>

## Current behaviour

<What happens, where, how to reproduce, the evidence (log line, request, screenshot).>

## Expected behaviour

<!-- The fix. The first test listed must fail before the fix and pass after it. -->

- R1.1 WHEN <the trigger that shows the bug> THE SYSTEM SHALL <the correct response>.
  Verify: tests/unit/test_<module>.py (fails before the fix); live: <the reproduction now gives the correct result>

## Unchanged behaviour

<!-- What must keep working; a regression test for each. -->

- R2.1 WHEN <a nearby case that works today> THE SYSTEM SHALL <keep its current response>.
  Verify: tests/unit/test_<module>.py

## Root cause

<One paragraph once known; the lesson line it adds to skill/aa-lessons/lessons.md, if any.>
