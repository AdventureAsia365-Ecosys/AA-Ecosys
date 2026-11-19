---
id: spec-AA-<n>
issue: AA-<n>
title: <short name of the slice>
status: draft
owner_repo: <AA-CIS-App | AA-Booking | AA-Partner | AA-TripPlanner-Web | AA-CIS-Infra | AA-Ecosys>
kind: feature
approved_at:
supersedes:
---

# <Short name of the slice>

## Problem

<One paragraph: what happens today, where, the evidence (session, PR, numbers). Copy the Problem of the Linear issue;
the issue keeps Problem and Scope, this file keeps the criteria.>

## Requirements

<!-- EARS, one criterion per line, each followed by its Verify line (a test path, "test: ..." or "live: ...").
     WHEN <trigger> THE SYSTEM SHALL <response>. / IF <unwanted condition> THEN THE SYSTEM SHALL <response>.
     WHILE <state> THE SYSTEM SHALL <response>. / THE SYSTEM SHALL <always true>.
     A criterion changed after the work started keeps its id: "R1.2 (amended S<nnn>: <why>) WHEN ...". -->

### R1 <Group name>

- R1.1 WHEN <trigger> THE SYSTEM SHALL <response>.
  Verify: tests/unit/test_<module>.py; live: <curl / page / query and the expected result>
- R1.2 IF <unwanted condition> THEN THE SYSTEM SHALL <response>.
  Verify: tests/integration/test_<module>.py
