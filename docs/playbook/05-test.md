---
id: GUIDE-14-test
title: "Phase 5: Test"
description: Prove a change works before users see it - test layers, gate G5 checklist, security checks, UAT and common mistakes.
type: how-to
status: draft
owner: nghiep
audience: [engineer, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-build, GUIDE-14-release]
---

# Phase 5: Test

**Goal:** prove the change works before users see it. **Accountable:** the tech lead; the business owner is consulted
for UAT. **Follows:** OWASP ASVS 5.0 level 1 (level 2 for auth, payment and personal data), ISO/IEC 25010:2023, the
DORA finding that AI-assisted delivery stays stable only with strong tests and fast feedback.

## Deliverables

| Deliverable | Template |
|---|---|
| Test strategy: what is tested at which layer, what blocks a merge | [Test strategy](../templates/test-strategy.md) |
| Unit and integration tests; contract samples; UI smoke | per repo |
| Visual and signed-in end-to-end checks at desktop and phone width, light and dark | per repo |
| Eval regression for AI changes (prompt, model or route) | per repo |
| Isolation probe for tenancy changes | per repo |
| Security checklist for the touched area | [Security checklist](../templates/security-checklist.md) |
| UAT report for business-visible features | [UAT report](../templates/uat-report.md) |

## Gate G5: release ready

| # | Question |
|---|---|
| 1 | Is every check green, not only the required ones, with nothing pending? |
| 2 | Did a risky class get an independent agent review, and is every finding fixed or recorded? |
| 3 | Are the ASVS level 1 items of the touched area checked (level 2 where it applies)? |
| 4 | For a `fix`: does the test that failed before the fix now pass? |
| 5 | For an AI change: is the eval regression green against the fixed set? |
| 6 | For a tenancy change: does the isolation probe pass? |
| 7 | For a visible feature: is the UI checked at both widths and both themes, with no console error? |

## Common mistakes

- Retrying a flaky test until it passes instead of fixing or quarantining it.
- Calling a paid model or API from CI instead of a recorded response.
- Copying real customer data into a test fixture.
- Merging on "required checks green" while a non-required check is red.
- UAT on a feature the business owner has never seen described.
