# AA-825 — Booking retention live proof on Dev (S251, 25/10/2026)

Shipped: AA-Booking #91 (`8d00c76d`, fail-closed override gate, succeeded jobs archived before delete) deployed as
`aa-booking-dev-api:58` (rollout COMPLETED, `/booking/health` git_sha `8d00c76d`); AA-CIS-Infra #386 (`6a168e19`) applied by
Terraform Apply run 40178214300 (IAM `aa-booking-dev-ecs-task-retention-archive`: PutObject on bronze `archive/booking/*`
only; Booking task env `RETENTION_OVERRIDE_ENABLED=true` on Dev only). Calls made in the Booking container with the same
functions the staff route uses (`_check_override`, `enqueue_manual`, audit row with actor `system:s251-aa825-evidence`),
because the E2E Booking staff user is read-only.

| Step | Result |
|---|---|
| `GET` status | `override_allowed: true`, scheduled mode `dry_run`, no approved live run |
| Override with `older_than` 2026-10-19 (today − 6 d) | refused: "older_than 2026-10-19 is too recent: at most 2026-10-18" |
| DRY RUN `bk_retention_job`, older_than 2026-10-18 (job 739311bf) | succeeded: candidates succeeded 14, failed 3; affected 0 |
| DRY RUN `bk_retention_inbox_redact` (job ee90256c) | succeeded: candidates payload_pii 5; affected 0 |
| LIVE `bk_retention_job`, max_rows 17 (job 22de9734) | succeeded, mode live, affected_total 17 |
| LIVE `bk_retention_inbox_redact`, max_rows 5 (job 3a171b92) | succeeded, mode live, affected_total 5 |
| Verify (Booking role, read) | `booking.inbox_events` past cutoff not redacted: 0; `booking.job` rows past cutoff: 0 |
| S3 archive | `archive/booking/job/2026/10/22de9734-…-succeeded-b00001.jsonl.gz` (2,578 B) and `…-failed-b00001.jsonl.gz` (462 B), written before the delete |

CIS side of AA-825 (rollups, sargable usage view, CIS TTL kinds): evidence in the S239 Linear comment (16/10).
