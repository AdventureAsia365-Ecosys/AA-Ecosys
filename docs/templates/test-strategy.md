---
id: ARCH-00-test-strategy-replace-me
title: Test strategy - <project or repo>
description: <One sentence - what is tested at which layer, what blocks a merge and what runs after deploy.>
type: explanation
status: draft
owner: replace-me
audience: [engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 180
related: []
---

# Test strategy - <project or repo>

<!-- New-project playbook, phase 5 Test, gate G5. One page that says what to test where, so no one argues it per PR.
"Every check green, not only the required ones" is the gate. Delete this comment. -->

## 1. Layers

| Layer | What it proves | Tool | Runs | Blocks merge? |
|---|---|---|---|---|
| Unit | Pure logic: rules, parsers, calculations | <pytest, vitest> | every PR | yes |
| Integration | Code against a real database or service in a container | <pytest + Postgres service> | every PR | yes |
| Contract | Produced and consumed shapes match the published contract and its samples | <JSON Schema, OpenAPI diff> | every PR touching a contract | yes |
| UI smoke | Main pages render, no console error, key action works | <Playwright> | every PR touching the web app | yes |
| Visual and signed-in E2E | Layout at desktop and phone width, light and dark; real sign-in flow | <Playwright> | before release | yes for the release |
| Isolation probe | One tenant cannot read or write another's data | <probe script> | every tenancy change; nightly | yes |
| AI eval regression | Quality of LLM outputs on a fixed set does not drop | <eval runner, golden set> | prompt, model or route change | yes |
| Post-deploy verify | Live endpoint returns the right shape and the new commit | <smoke script> | after every deploy | the change is not Done until green |

## 2. Rules

- A bug fix starts with a failing test that reproduces it (the `fix` path).
- A test that needs a paid call uses a recorded response, never a live paid call in CI.
- Test data is invented; never a copy of real customer data.
- Flaky tests are fixed or quarantined with an issue within one session; they are never retried until green.
- Coverage and code-health limits only move up (ratchets); a PR may not lower them.

## 3. What is not tested, and why

<Areas left to manual UAT or monitoring, with the reason and the risk owner.>

## 4. UAT

Business-visible features get a UAT report (`uat-report.md`) signed off by the business owner or the role that uses
the feature.
