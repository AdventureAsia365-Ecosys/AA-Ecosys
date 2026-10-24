# S249 restore drill (AA-829): PITR copy, single-schema restore, repoint of `db.dev.internal`

Session S249, 23–24/10/2026, Claude Code (orchestrator), Dev acc2. Approved by Nghiệp at the end of S248 (card e03
"full") and again in S249 ("làm luôn"). Runbooks: [restore-rds-pitr](../../ops/runbooks/restore-rds-pitr.md),
[restore-schema](../../ops/runbooks/restore-schema.md). Scripts: AA-CIS-Infra #330 (`db/scripts/s249_drill_*.py`).

## Timeline (UTC)

| Time | Step | Evidence |
|---|---|---|
| 23/10 16:27:17 | Rehearsal table `drill_s249.restore_rehearsal` complete: 100 synthetic rows (T1) | DB Migrate run-script 39986778838 |
| 23/10 16:29:17 | Simulated damage: 40 rows deleted, 60 left (T2) | same run |
| 23/10 16:35:47 | PITR restore started, `--restore-time 2026-10-23T16:28:15Z` (between T1 and T2), `db.t4g.micro` | `aws rds restore-db-instance-to-point-in-time` |
| 23/10 16:57:07 | Copy `aa-cis-dev-db-drill-20261023` available — **RTO 21 min 20 s** (target < 1 h) | `aws rds wait db-instance-available` |
| 23/10 16:59 | Compare live vs copy (read-only): **164/164 tables**, migration heads equal (274, 273, 272, 271, bk-021); differences only in tables written after the restore point: `crm.job` +30, `shared.tenant_api_usage` +97, `booking.job` −1 (retention), rehearsal 60 vs 100 | run-script 39991070753, [compare-run-39991070753.txt](compare-run-39991070753.txt) |
| 24/10 02:5x | **Single-schema restore (option A)**: 40 missing rows copied from the copy in one transaction, count re-checked: `inserted=40 live_now=100 equals_copy=true` | run-script 40056219169 |
| 24/10 02:5x | Rehearsal schema dropped | run-script 40056368676 |
| 24/10 03:13:14→03:13:55 | **Repoint** `db.dev.internal` → copy: local MFA `terraform apply -target=aws_route53_record.db -var db_dns_target_override=<copy>`: 0 add, 1 change, 0 destroy | terraform output |
| 24/10 03:14:16→03:17:25 | Force new deployment of `aa-cis-dev-api`, `aa-cis-dev-worker`, `aa-booking-dev-api`, `aa-crm-dev-api`; all stable | `aws ecs wait services-stable` |
| 24/10 03:17 | Verified on the copy: CIS api, worker and CRM report `server_ip 10.2.21.185`, `pg_postmaster_start_time` 23/10 16:45 (the copy; live is 10.2.21.174, started 15/10); CIS `/health/ready` ok (274); **Booking and CRM `/health/ready` = not_ready** (`missing bk-022`, `missing crm-003, crm-004`) because the copy predates those migrations — readiness correctly refuses a restore older than the code's schema; TripPlanner browse 200 | ECS exec + curl |
| 24/10 03:18:34→03:19:15 | Repoint back (apply without the override): 1 change | terraform output |
| 24/10 03:19→03:22:49 | Same 4 services redeployed, stable; back on live (`10.2.21.174`); `/health/ready` ok for CIS (274), Booking (bk-022), CRM (crm-004) | ECS exec + curl |
| 24/10 03:2x | `terraform plan -target=aws_route53_record.db` → **No changes** (state = AWS) | terraform output |
| 24/10 03:25:33 | Copy deleted (`--skip-final-snapshot --delete-automated-backups`); only `aa-cis-dev-db` left | `aws rds describe-db-instances` |

Job tables idle before each write step (`shared.job`, `booking.job`, `crm.job`, `shared.rerun_wave`). Writes made to
Dev while the name pointed at the copy (03:14–03:19) were lost on the way back, as accepted (Dev has no users).
Cost: one `db.t4g.micro` for about 10.8 h plus storage, well under 1 USD.

## Findings

1. **PITR restore** works and is well within the < 1 h RTO (21 min 20 s; S241: ~22 min).
2. **Single-schema restore option A** (reviewed run-script, read from the copy, write to live in one transaction with
   a count guard) works end to end; the runbook is no longer UNTESTED.
3. **`db.dev.internal` cut-over** works in about 40 s of Terraform plus about 3 min of redeploys; the apps follow the
   name, no DSN secret changes.
4. **Readiness protects an old restore**: services whose required schema is newer than the restored copy report
   `not_ready` instead of serving with a missing migration. A real cut-over to an older copy needs the migrations
   re-applied (DB Migrate) before the services become ready — added to the runbook.
5. The auto-mode safety classifier blocked the DNS repoint and the schema-restore write until Nghiệp turned auto mode
   off; plan for that in future drills.
