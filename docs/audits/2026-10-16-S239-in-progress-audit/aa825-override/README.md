# AA-825: first live TTL runs with archive + rollup on Dev (S239, 16/10/2026)

Agent: Claude Code (orchestrator).
- Code on Dev: CIS `84bba941` (api :641 / worker :195+).
  - #764 adds the manual override.
  - #769 sets the override floor to 21 days and adds the closed-month check for tenant usage.
- The admin secret was read from Secrets Manager at run time. It was never printed or saved.
- Scripts: `.tmp-session/s239/aa825proof/aa825_override_ctx.py` (read-only context) and `aa825_override_run.py` (API calls).
- Nghiệp approved live deletes for the CIS kinds in S239.

## Why an override

The oldest `llm_call_log` row on Dev is 2026-09-17. Nothing is older than the 180 d (llm_call_log) or 90 d (tenant_api_usage) policy windows, so the policy runs find 0 candidates. A manual override takes an explicit cutoff and a mandatory small `max_rows`. It works on Dev/test only, never on a scheduled trigger, and the policy windows stay unchanged. It proves the archive-then-delete and rollup paths on real rows now.

## Runs

| Kind | Cutoff (`older_than`) | DRY RUN candidates | Live `max_rows` | Deleted | Archived | Rollup rows written | S3 object |
|---|---|---|---|---|---|---|---|
| retention_llm_call_log | 2026-09-18 | 2,676 (all on 17/09) | 200 | 200 | 200 | 5 (`shared.llm_call_daily`, day 17/09) | `archive/llm_call_log/2026/09/a309a2c4-…-raw-b00001.jsonl.gz` |
| retention_tenant_api_usage | 2026-09-17 | 260 | 200 | 200 | 200 | 3 (`shared.tenant_api_usage_monthly`, Sept) | `archive/tenant_api_usage/2026/09/0609cb2b-…-raw-b00001.jsonl.gz` |

Files: `11_dry_runs.json`, `12_live_runs.json`. The deploy gate showed `active 0` before and after each run.

## Verification

- **S3 objects** (`16_s3_listing.txt`, `17_s3_objects_check.txt`): both have metadata `rows=200`, SSE `AES256`, and 200 lines after gunzip. The format is gzipped JSONL, decided in S237 because there is no pyarrow in the image; converting to Parquet later is one Athena CTAS step.
- **llm_call_log rollup equals the raw totals before the delete** (`00_ctx_before.txt` vs `15_ctx_after.txt`):
  - raw 17/09 before: 2,676 calls, 3,874,683 in, 1,895,066 out, $26.794948;
  - raw after: 2,476 calls, $25.694670 (−200 rows, −$1.100278);
  - `llm_call_daily` for 17/09: 2,676 calls, 3,874,683 / 1,895,066 tokens, $26.794948, exactly the pre-delete totals.
- **tenant_api_usage monthly rollup** for Sept equals the pre-delete per-tenant and actor counts row for row (31 / 1,989 / 7,563 calls). Candidates below the cutoff went from 260 to 60.
- **Admin pages** (`10_pages_before.json`, `13_pages_after.json`, `14_pages_diff.json`):
  - `usage_closed_months` is the same for every tenant;
  - the all-time LLM cost of the internal AA tenant dropped by exactly $1.100278 (156.674976 → 155.574698); the 200 deleted rows were internal (`tenant_id` NULL);
  - the 30-day spend views changed by the same amount. This is expected with the 21-day floor and was noted in #769;
  - all other tenants are unchanged.
- **EXPLAIN** (`../aa825-explain/`): `v_tenant_monthly_usage` is in sargable form, the 233 numbers equal the 223 numbers for all 9 tenants, the page queries do not seq-scan the ledgers, and `called_at` is in the Index Cond.

## Also done for AA-825 in S239

- Daily schedule: Infra #150 (`../aa825-schedule/`), applied with a targeted plan (1 add, 3 change).
  - It runs at 20:30 UTC through the ops-probe Lambda, which reads the admin secret at run time.
  - The `archive/` lifecycle rule moves objects to STANDARD_IA after 90 days.
  - A manual invoke returned 200 and enqueued 5 retention jobs.
- Booking (`../aa825-booking/`): bk-012 applied through DB Migrate; the code (AA-Booking #23) is deployed.
  - DRY RUNs of `bk_retention_job` and `bk_retention_inbox_redact` succeeded, with 0 candidates: Booking data is days old.
