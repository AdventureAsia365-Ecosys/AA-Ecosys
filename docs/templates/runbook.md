---
id: OPS-00-replace-me
title: <Verb> <object>
description: <One sentence - when an operator opens this runbook.>
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [replace-me]
last_reviewed: 2026-10-19
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: []
---

# <Verb> <object>

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> Remove this banner, set `status: active` and fill `last_tested`, `tested_where` and `tested_evidence` after the
> first real run (Dev acc2, drill, incident or DRY RUN). See [STYLE](../STYLE.md#runbooks-and-tested).

## When to use

- Trigger: <alarm name / symptom / request>.
- Not for: <cases that use another runbook - link it>.

## Preconditions

- Access: <profile, role, Cognito group>. Start every session with the identity check below.
- State: `shared.job` has no queued or running job of a kind this touches (deploy gate), unless SEV1 and Nghiệp decides.
- Cost: <0 USD / estimate per run>.

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../onboarding.md#account-map).

## Steps

1. <Action.>

   ```bash
   <one-line command with --profile and --region>
   ```

   Expected: <output or state>.
   Verify: <one-line check>.
   Rollback: <how to undo this step, or "none - read-only">.

2. <Action that changes state.>

   ```bash
   <one-line command> # WRITE
   ```

   Expected: <output>.
   Verify: <check>.
   Rollback: <undo command or "abort and go to Escalation">.

## Verify the result

- <Live check: curl 200 + shape, rollout COMPLETED, alarm back to OK.>

## Roll back or abort

- <Whole-procedure rollback, or the point after which there is no rollback.>

## Escalation

- Severity per [incident response](../ops/incident-response.md). Tell Ms. Thư when <rule>.

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| <YYYY-MM-DD> | <dev-acc2 / drill / incident / dry-run> | <name> | `docs/audits/<date>-S<nnn>-<slug>/` or Linear comment | <pass / fail + note> |
