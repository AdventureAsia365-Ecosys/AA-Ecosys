---
id: SEC-05-index
title: Security docs index
description: Index of the security pages and of the access-review records kept in docs/audits; start here for any security question.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-20
review_every_days: 90
related: [SEC-01, SEC-02, SEC-03, SEC-05, SEC-06, SEC-07]
---

# Security docs index

Security pages live only in this private repo (SEC-06, D-25). They are not synced to the admin docs page
unless Nghiệp decides who may read them there (N-3).

| ID | Page | What it answers |
|---|---|---|
| SEC-01 | [Security baseline](baseline.md) | Which controls exist, their live status, evidence and open issue |
| SEC-02 | `secrets-register.md` / `.yaml` (AA-878) | Every secret: owner, readers, rotation class |
| SEC-03 | [Vulnerability management](vulnerability-management.md) | Fix times, exceptions, monthly triage, open alerts |
| SEC-04 | [Compliance and privacy register](../legal/register.md) (draft, AA-886), with the [retention log](../legal/retention-log.md), [DPA template](../legal/dpa-template.md), [DSAR and erasure runbook](../legal/dsar-erasure-runbook.md), [readiness packet](../legal/readiness-packet.md) and [consent check](../legal/consent-capture-query.md) | Processing activities, sub-processors, retention runs, data-subject requests |
| SEC-06 | [Where a page may live](../STYLE.md#where-a-page-may-live-sec-06) | What may go into the public app repos |
| SEC-07 | [GitHub Apps for agents and bots](github-apps.md) (draft, AA-901) | How the `aa-agent` and `aa-ci-bot` Apps are created, installed, keyed, rotated and stopped |

## Access reviews (SEC-05)

Quarterly, in the first session of each quarter (DM-8.10). Each review is a dated folder
`docs/audits/<date>-S<nnn>-access-review/` with its evidence; this page only lists them.

| Quarter | Record | Notes |
|---|---|---|
| 2026-Q4 | [2026-10-20-S245-access-review](../audits/2026-10-20-S245-access-review/README.md) | First review (AA-878), 20/10/2026: 15 findings (F-1…F-15), 2 questions for Nghiệp. Next: first session of 2027-Q1 (cadence AA-838) |
