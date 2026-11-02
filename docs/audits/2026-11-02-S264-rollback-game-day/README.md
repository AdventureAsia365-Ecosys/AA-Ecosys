# Rollback game day (S264, 02/11/2026) — AA-1023

Plan: `docs/ops/drills/rollback-game-day.md`. Run by the orchestrating agent with the tech lead's auto mode off
(19:27–20:07 +07). Raw output: `d1-booking.txt`, `d2-crm.txt`, `d3-vercel.txt`, `d4-lambda.txt`, `d5-idle-gate.txt`.

| Drill | Back: from -> to | Back | Forward | Health / check after each | Result |
|---|---|---|---|---|---|
| D1 Booking API | :93 `967f9b2c` -> :91 `16fbed68` (skips template :92) | 150 s | ~3 min (stable 12:51:02Z) | `/booking/health` SHA as expected, ready 200 both ways | PASS |
| D2 CRM API | :120 `dca5465b` -> :119 `22d833cb` | 166 s | ~3 min (stable 12:42:14Z; MFA expired mid-drill, forward right after the new code) | `/crm/health` SHA as expected, ready 200, web `/healthz` 200 | PASS |
| D3 Vercel `aa-booking-admin` | `dpl_5Hca` `1fceb3c4` -> `dpl_HWmT` `cc2c78d1` | < 1 min | < 1 min | production alias moved both ways (deployment aliases), page 307 (login redirect) | PASS |
| D4 Lambda browse | `gFA2…` -> `WQVs…` (v106) | 11 s | 10 s (v107, `gFA2…`) | browse 200 both ways, alarms browse/assembly OK | PASS |
| D5 job-idle gate | idle -> seeded -> cleared (`OPEN_COUNT 0`) | - | - | green 41448556395 / red 41449153963 (`shared.job running=1 noop_sleep`) / green 41450256149 | PASS |

Findings:
- `tools/ops/ecs_rollback.sh --apply`: after `services-stable` the helper read the rollout once and reported
  `ERROR: rollout is IN_PROGRESS` twice (D1 and D2 forward) although ECS reached COMPLETED a few seconds later; the
  helper should poll the rollout state for up to ~2 minutes before failing. Follow-up.
- Booking builds older than :93 lack `ALERTS_TOPIC_ARN` (`--allow-config-diff` both ways; no alert for those minutes).
- The seeded `noop_sleep` row was CLAIMED (the Dev worker runs the test kind), cleared with `ACTION=clear`, `OPEN_COUNT 0`.
- Not done in this drill: the issue's environment rename `prod` -> `dev` (needs the bootstrap OIDC apply with MFA).
