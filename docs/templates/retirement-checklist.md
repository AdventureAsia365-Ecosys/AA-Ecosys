---
id: TPL-01-retirement-checklist
title: Retirement checklist
description: How to shut down a product, app, feature or environment cleanly, with nothing left running, stored or billed.
type: template
status: draft
owner: nghiep
audience: [owner, engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01]
---

# Retirement checklist

New-project playbook, phase 9 Retire, gate G8. Copy the list into the retirement issue. The business owner is
accountable; the tech lead runs it. Gate G8 passes only when the cloud bill and the inventory show nothing left. AA cases
it is built from: the removal of an account from the ecosystem (ADR 0001a), tour retirement propagation (ADR 0015) and
the dead table registry.

## 1. Decide

- [ ] Retirement ADR: what is retired, why, the date, what replaces it, who is affected.
- [ ] Business owner's yes recorded, with the notice period.

## 2. Tell

- [ ] Notice to users and tenants at least 30 days ahead (or the contract's period), with the export path.
- [ ] Contract consumers told; the last major contract version served in parallel for at least 30 days.
- [ ] Vendors told; subscriptions and contracts end dates set.

## 3. Data

- [ ] Data export given to whoever owns it, in an open format, with a checksum.
- [ ] Each data class kept or erased per its retention rule (legal holds and accounting records kept as required).
- [ ] Erasure done with the dry-run procedure: exact counts shown, snapshot taken, approval recorded, re-verified.
- [ ] Tables and schemas moved to quarantine first, dropped after the waiting period; registry rows updated.

## 4. Traffic

- [ ] Routes return a tombstone (HTTP 410 with a short message) or redirect to the replacement.
- [ ] DNS records, certificates and load balancer rules removed after the tombstone period.
- [ ] Scheduled jobs, queues and webhooks stopped and deleted; third-party callbacks unregistered.

## 5. Infrastructure

- [ ] Infrastructure-as-code destroy plan reviewed (every resource listed), then applied from CI.
- [ ] Resources outside IaC found by tag and by the inventory, and removed.
- [ ] Secrets deleted (and rotated first if they were shared); IAM roles, identity clients and CI credentials removed.
- [ ] Container images, buckets, snapshots and log groups deleted or set to expire, per retention.
- [ ] Budgets and alarms of the retired part removed after the final bill.

## 6. Prove zero

- [ ] Inventory and tag search show no resource left.
- [ ] One full billing day later, the cost by tag and by service shows 0 USD for the retired part.

## 7. Close

- [ ] Docs set to `deprecated` or `archived` with a pointer to the replacement; the catalog updated.
- [ ] Agent instructions, skills and hooks no longer mention it.
- [ ] A final lesson entry: what to do differently next time.
