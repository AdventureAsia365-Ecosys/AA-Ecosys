---
id: SEC-06-aa839-erasure-drill
title: "AA-839 real tenant erasure drill on Dev (S248)"
description: "Drill xoá thật một tenant tổng hợp trên Dev (DRY RUN, duyệt, apply, kiểm lại) kèm bằng chứng CSV."
type: report
status: active
owner: nghiep
audience: [engineer, cto, agent]
applies_to: [aa-cis-api, ecosystem]
last_reviewed: 2026-10-23
review_every_days: 180
related: [AA-839]
---

# AA-839 — real tenant erasure drill on Dev (S248, 23/10/2026)

Synthetic tenant `AA-839 drill` (`aa839-drill-1`, `f641b3f0-5761-494d-97b1-65340e83d450`), created and offboarded
through the admin API earlier the same day. Runbook: [`docs/legal/dsar-erasure-runbook.md`](../../legal/dsar-erasure-runbook.md).

| Step | Who | Evidence |
|---|---|---|
| Flags ON (`erasure_drill = true`: apply on, retention 0 days) | Claude Code | AA-CIS-Infra #321, terraform-apply run 39942353951, CIS Deploy Dev run 39942579454 (api :791 / worker :350); `/admin/job-runner/erasure` → apply_enabled true, retention 0 |
| Manual RDS snapshot `tenant-erase-20261023-pre` (20 GB) | Claude Code | created 11:01 UTC, status available before the apply |
| DRY RUN `d4fb89f5` — delete 4 · keep 3, no blockers, 30 checks passed, 0 unregistered tables; fingerprint v2 `843a2ce0…` | Nghiệp (admin page, Cognito) | admin page `/admin/data-erasure` |
| Apply `382ad9b3` — fingerprint prefix, snapshot id, approver Nghiệp, confirmation naming the tenant | Nghiệp (Cognito session) | status succeeded, `delete 4 · VERIFIED` |
| Verification DRY RUN `4c01c2f1` — tenant state GONE; every table 0; keep 4 (`acp_shared.audit_log`, append-only, the apply adds its own audit row) | Nghiệp | [`verify-dry-run-4c01c2f1.csv`](verify-dry-run-4c01c2f1.csv) (exported from the page) |
| Outside the DB: S3 `raw-inbox/<tenant>/` and `brand-identity/<tenant>/` 0 objects; Secrets Manager `acp/cms/<tenant>` and `acp/social/<tenant>` do not exist | Claude Code | read-only checks after the apply |
| Flags OFF (`erasure_drill = false`) | Claude Code | AA-CIS-Infra #322, terraform-apply, CIS Deploy Dev; `/admin/job-runner/erasure` → apply_enabled false, retention 30 |
| Snapshot deleted | Claude Code | `tenant-erase-20261023-pre` deleted after the verification |

Window with apply enabled: about 25 minutes. The other offboarded Dev tenants (two seed tenants, `test-1`, the S235
throwaway) were not touched: no DRY RUN was run for them.

Code shipped for the drill: AA-CIS-App #946 (job), #960 (admin page), #961 (fingerprint v2 binds the subject);
AA-CIS-Infra #320 (flags), #321 / #322 (drill on / off); root #208 (runbook).
