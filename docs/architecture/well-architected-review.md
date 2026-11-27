---
id: ARCH-11
title: Well-Architected review (S295 baseline)
description: The first full AWS Well-Architected self-review of the ecosystem (6 pillars plus the SaaS and Generative AI lenses), its scorecard, where each risk is tracked and when the next review is due.
type: explanation
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-27
review_every_days: 365
related: [ARCH-01, ARCH-08, docs/audits/2026-11-27-S295-well-architected/README.md]
---

# Well-Architected review (S295 baseline)

> **Status:** self-review recorded on 2026-11-27 (S295). It is not a review by AWS or a partner. The same answers are
> recorded in the AWS Well-Architected Tool (workload "AA Ecosystem (Dev)", lenses: AWS Well-Architected Framework,
> Generative AI Lens, SaaS Lens; milestone "S295 baseline 2026-11-27"). The full per-pillar files are in the private
> ISMS evidence store; this page is the public-safe summary.

## What was reviewed

- Every best-practice question of the six pillars (OPS01–11, SEC01–11, REL01–13, PERF01–05, COST01–11, SUS01–06), plus
  the SaaS Lens and the Generative AI Lens where they apply.
- Evidence: the code in the repositories and read-only calls to AWS. Each pillar had one reviewer and one adversarial
  check.
- Environment: Dev, which also hosts the B2B pilot. Dev is lean on purpose (single-AZ database, one NAT instance, one
  task per service). Multi-AZ, a NAT gateway and cross-account backup are production decisions.

## Scorecard

HRI = high-risk issue, MRI = medium-risk issue.

| Pillar | HRI | MRI | Summary |
|---|---|---|---|
| Operational Excellence | 2 | 8 | Delivery is strong (CI/CD, IaC, nightly drift check, docs-as-code). Risks: one alert channel, one operator. |
| Security | 5 | 14 | Strong technical base. Risks: admin identity, broad permissions, thin detection, recovery if an admin role is compromised. |
| Reliability | 1 | 10 | Software handles failure well. Risk: backups are not separated from admin permissions. |
| Performance Efficiency | 0 | 6 | Database SLOs and weekly query reviews. Gaps: edge caching for the CRM, no load test yet. |
| Cost Optimization | 0 | 4 | Good FinOps for the team size. Gaps: cost allocation after the billing transfer, vendor-side AI spend limits. |
| Sustainability | 0 | 4 | Graviton, Fargate, log retention. Gaps: long data retention, no sustainability metrics. |
| **Total** | **8** | **46** | Nothing blocks the pilot technically. All 8 HRIs can be fixed before real pilot data, almost at no cost. |

The high risks are about people and permissions, not about the application architecture.

## Where each risk is tracked

| Area | Issue |
|---|---|
| Second alert channel, second key-holder, runbook drill, security tabletop | AA-1110 |
| Admin MFA, E2E identities | AA-1111, AA-1054, AA-1158 |
| Terraform state lock-down, narrower permissions, vendor AI spend limits | AA-1182 |
| Cost allocation and anomaly detection after 01/12, SCP/RCP | AA-1004 |
| Backups separated from admin permissions, GuardDuty, one-off Security Hub / Inspector / Macie scans | AA-873 |
| Zero-cost sweep: edge, egress, EBS default encryption, IAM policy validation in CI, AWS Health events, NAT patching, CRM edge cache | AA-1185 |
| Go-live gate: database maintenance window, pilot AI budget share, internal RTO/RPO, load test | AA-1117 |
| Automatic rollback of API deploys when the post-deploy smoke check fails | AA-1193 |
| LLM failover drill and Bedrock quota register | AA-1194 |
| Source of inter-AZ traffic | AA-1195 |

## Next review

- Yearly, next on 2026-11-27 + 1 year (27/11/2027), or before production if production comes first.
- Compare against the "S295 baseline" milestone in the Well-Architected Tool. The date is on the ops calendar (AA-1184).
