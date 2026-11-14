---
id: GUIDE-14-retire
title: "Phase 9: Retire"
description: Shut a product, app or feature down cleanly and stop paying for it - the retirement steps, gate G8 and common mistakes.
type: how-to
status: draft
owner: nghiep
audience: [owner, cto, engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-operate, TPL-01-retirement-checklist]
---

# Phase 9: Retire

**Goal:** shut a product, app or feature down cleanly and stop paying for it. **Accountable:** the business owner; the
tech lead runs it. **Follows:** UK GDS retirement phase; the retention and erasure rules of the project's privacy
register.

## Steps

The full list, to copy into the retirement issue, is the [retirement checklist](../templates/retirement-checklist.md).
In short:

1. **Decide:** a retirement ADR (what, why, when, what replaces it, who is affected) and the business owner's yes.
2. **Tell:** users, tenants, contract consumers and vendors, at least 30 days ahead; the last major contract version is
   served in parallel for at least 30 days.
3. **Data:** export to its owner; keep or erase each class per its retention; erase through a dry run with exact counts,
   a snapshot and an approval; quarantine before drop.
4. **Traffic:** tombstones (HTTP 410) or redirects; then DNS, certificates and routing rules removed; jobs, queues and
   webhooks stopped.
5. **Infrastructure:** IaC destroy plan reviewed and applied from CI; resources outside IaC found by tag; secrets,
   roles and identity clients removed; images, buckets, snapshots and logs deleted or set to expire.
6. **Prove zero:** inventory and tag search empty; one full billing day later, 0 USD for the retired part.
7. **Close:** docs deprecated or archived, agent instructions cleaned, a final lesson entry.

## Gate G8: retirement complete

| # | Question |
|---|---|
| 1 | Does the inventory show no resource of the retired part? |
| 2 | Does the bill, one full billing day after the destroy, show 0 USD for it? |
| 3 | Was every data class kept or erased per its retention, with evidence? |
| 4 | Were users and consumers told, and did the notice period pass? |
| 5 | Are secrets, roles and credentials of the retired part deleted? |
| 6 | Are docs and agent instructions free of live references to it? |

## Common mistakes

- Deleting the app but not its scheduled jobs, alarms, DNS records or secrets.
- Dropping tables without an export or a quarantine period.
- Stopping at "destroyed" without checking the bill.
- Forgetting the agent instructions, which keep telling agents to call a dead service.
