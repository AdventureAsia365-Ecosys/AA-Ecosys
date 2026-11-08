---
id: OPS-03-gameday
title: Rollback game day plan
description: The 0 USD drill that rolls Booking API, CRM API, the TripPlanner web (ECS) and one TripPlanner Lambda back and forward once each, timed, and proves the terraform-apply job-idle gate; with the evidence to capture.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [aa-booking-api, aa-crm-api, aa-tripplanner, tripplanner-lambda, aa-cis-infra]
last_reviewed: 2026-11-02
review_every_days: 90
related: [OPS-03-drills, OPS-02-ecs, OPS-02-booking, OPS-02-vercel, OPS-02-tp-lambda, OPS-10-deploy-gate, AA-1023]
---

# Rollback game day plan

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> This is the plan of the first run (AA-1023). After the run, its results go into the [drill index](README.md) and the
> runbooks' tested logs.

One sitting on Dev, about 60-90 minutes, **0 USD** (no new resource; a few Fargate task-minutes inside the existing
cluster). Each drill goes back to an earlier build and forward again, and is timed. CIS api + worker were drilled in
S241 and are not repeated.

| # | Target | Runbook | Back to | Forward to |
|---|---|---|---|---|
| D1 | ECS `aa-booking-dev-api` | [rollback-ecs](../runbooks/rollback-ecs.md) | `--previous` (newest older real build) | the revision running before D1 |
| D2 | ECS `aa-crm-dev-api` | [rollback-ecs](../runbooks/rollback-ecs.md) | `--previous` | the revision running before D2 |
| D3 | ECS `aa-tripplanner-dev-web` (was Vercel `aa-tripplanner`, retired with AA-1038, S272; before that `aa-booking-admin`, AA-911) | [rollback-ecs](../runbooks/rollback-ecs.md) | `--previous` | the revision running before D3 |
| D4 | Lambda `aa-tripplanner-dev-browse` | [rollback-tp-lambda](../runbooks/rollback-tp-lambda.md) path B | the previous `browse.zip` object version | the newest `browse.zip` object version |
| D5 | AA-CIS-Infra `terraform-apply.yml` job-idle gate | [deploy-gate override](../runbooks/deploy-gate-override.md) (gates table) | red while one seeded `noop_sleep` row is busy | green after the row is cleared |

## Before you start

- Who: the orchestrating agent or the tech lead. Agent lanes are refused every write below by the subagent hooks
  (`.claude/hooks/subagent-guardrails.sh` refuses `ecs_rollback.sh`, `ecsx.sh`, `gh workflow run`,
  `aws lambda update-*` and the Vercel CLI rollback/promote; `subagent-mcp-guardrails.sh` the Vercel MCP writes).
- No rerun wave open, no Deploy Dev or Migration Apply run in progress on any repo, no `data_erasure` job running.
  D5 makes `shared.job` busy for a few minutes: a Migration Apply contract file due in that window is deferred to the
  next hourly run (no harm), so do D5 last.
- Evidence folder: `docs/audits/<date>-S<nnn>-rollback-game-day/` with one text file per drill
  (`d1-booking.txt` ... `d5-idle-gate.txt`) and a `README.md` with the results table below. Paste command output as
  printed; never paste a secret, a presigned URL or a token. Account IDs are fine in this repo.
- Time every write with `date -u +%FT%TZ` before and after; the helper also prints the seconds to stable.

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map).

## D1 and D2: Booking API and CRM API (ECS)

Run for `<service>` = `aa-booking-dev-api`, then `aa-crm-dev-api`.

1. Baseline: `bash tools/ops/ecs_rollback.sh <service> --list` and the health line (`/booking/health`, `/crm/health`).
   Note `<current-revision>` and its SHA.
2. Dry run: `bash tools/ops/ecs_rollback.sh <service> --previous`. Note the target revision, SHA and the configuration
   line. Booking on 2026-11-02 showed `env only in running: ALERTS_TOPIC_ARN` for every older build (the alert topic
   came later): accepted for the drill, the old build just publishes no alert for those minutes.
3. Back: `bash tools/ops/ecs_rollback.sh <service> --previous --apply` (Booking: add `--allow-config-diff` when step 2
   showed only the difference above). Expected `DONE: ... in <n> s`. Then readiness:
   `curl -s https://api-booking.lumiguides.it.com/booking/health/ready` or
   `curl -s https://partner-dev.lumiguides.it.com/crm/health/ready`: 200, `"db":"ok"`.
4. Forward: `bash tools/ops/ecs_rollback.sh <service> --to <current-revision> --apply`. Expected `DONE`, health on the
   baseline SHA, readiness 200.
5. CRM only: the CRM web reads the API; open `https://portal.lumiguides.it.com/healthz` after step 4 (200, `git_sha`
   unchanged).

Pass: both directions end `COMPLETED` with the expected SHA on health and readiness 200; the RTO (seconds from the
update to a healthy SHA) is written down.

## D3: TripPlanner web `aa-tripplanner-dev-web` (ECS)

The TripPlanner frontend left Vercel (AA-1038, S272; the Booking admin before it, AA-911): no Vercel project is left, so
D3 is the D1 procedure on the TripPlanner web service. Its health is `https://tripplanner.lumiguides.it.com/api/health`
(through CloudFront; field `git_sha`).

1. Baseline, dry run, back and forward exactly as D1 steps 1 to 4 with `<service>` = `aa-tripplanner-dev-web` (no
   readiness endpoint: the health answer is the check).
2. After forward: the home page answers 200 and `/plan` loaded as a document answers the WAF Challenge (202 with
   `x-amzn-waf-action: challenge`), as in the Deploy Web Dev verify.

Pass: both directions end `COMPLETED` with the expected SHA on health; the RTO is written down.

## D4: TripPlanner Lambda `aa-tripplanner-dev-browse`

The HTTP API calls the function unqualified (`$LATEST`; no alias exists, AA-703), so the drill is path B of the runbook
on one function.

1. Baseline: the running code hash and the zip versions.

   ```bash
   aws lambda get-function-configuration --function-name aa-tripplanner-dev-browse --profile aa365-admin --region us-west-1 --query "[CodeSha256,LastModified]" --output text
   aws s3api list-object-versions --bucket aa-tripplanner-dev-lambda-artifacts-005097885195 --prefix browse.zip --profile aa365-admin --region us-west-1 --query "Versions[:3].[VersionId,LastModified,IsLatest]" --output text
   ```

   Note `<newest-version-id>` (`True`) and `<previous-version-id>` (the next row). Its metadata `code-sha256` is the
   hash to expect:

   ```bash
   aws s3api head-object --bucket aa-tripplanner-dev-lambda-artifacts-005097885195 --key browse.zip --version-id <previous-version-id> --profile aa365-admin --region us-west-1 --query "Metadata" --output json
   ```

2. Back:

   ```bash
   aws lambda update-function-code --function-name aa-tripplanner-dev-browse --s3-bucket aa-tripplanner-dev-lambda-artifacts-005097885195 --s3-key browse.zip --s3-object-version <previous-version-id> --publish --profile aa365-admin --region us-west-1 --query "[Version,CodeSha256]" --output text # WRITE
   aws lambda wait function-updated --function-name aa-tripplanner-dev-browse --profile aa365-admin --region us-west-1
   curl -s -o /dev/null -w "%{http_code}\n" "https://tripplanner.lumiguides.it.com/api/browse?resource=countries"
   ```

   Expected: a new version whose `CodeSha256` equals the previous zip's `code-sha256`; the browse call 200.
3. Forward: the same `update-function-code` line with `<newest-version-id>`, then the wait and the curl. Expected:
   `CodeSha256` equal to the baseline hash of step 1, browse 200.
4. Alarm check (both alarms `OK` within 10 minutes):

   ```bash
   aws cloudwatch describe-alarms --alarm-names aa-tripplanner-dev-browse-errors aa-tripplanner-dev-assembly-errors --profile aa365-admin --region us-west-1 --query "MetricAlarms[].[AlarmName,StateValue]" --output text
   ```

Pass: both moves publish the expected hash and browse answers 200 after each.

## D5: the terraform-apply job-idle gate

Needs the AA-CIS-Infra job-idle gate merged on `main` (AA-1023). Every dispatch below uses `idle_gate_check=true`,
which runs only the gate: no plan, no apply.

1. Baseline (idle): dispatch, expect green and `job-idle gate: pass` in the summary.

   ```bash
   gh workflow run terraform-apply.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f idle_gate_check=true
   ```

   A red baseline means real jobs are busy: read the `MIGRATE busy:` lines, wait, and retry before seeding.
2. Seed one busy row (CIS api container, `cis_app`; kind `noop_sleep`, tag `aa1023-gameday`). The row ends by itself
   only when the CIS worker runs `noop_sleep`, i.e. `JOB_TEST_KINDS=1` is set on it; that is off on Dev by default,
   so expect the row to stay `queued` and to block DB Migrate apply, Migration Apply and the terraform-apply gate
   until step 5 clears it. Step 5 is mandatory, never optional:

   ```bash
   tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=seed
   ```

   Expected: `SEEDED id=<uuid> kind=noop_sleep status=queued seconds=900`, then after about 15 s either
   `UNCLAIMED ...` (normal Dev config: the row NEVER ends by itself) or `CLAIMED ...` (the worker runs the test kind:
   it ends after 900 s). Paste the line into `d5-idle-gate.txt` either way.
3. Dispatch the same `gh workflow run` line. Expected: red at "Job-idle gate", summary `job-idle gate: refused`, a line
   `MIGRATE busy: shared.job running=1 ...` (or `queued=1` when the worker does not claim the test kind).
4. Override wiring (optional): dispatch with `-f override_busy_jobs="AA-1023 game day: override wiring check"`.
   Expected: green with `::warning::job-idle gate OVERRIDDEN`.
5. Clear (mandatory, also when step 3 or 4 failed): `tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=clear`,
   then `tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=status` until `OPEN_COUNT 0` (a queued row is cancelled
   at once; a running row ends at its next progress write, within 5 s). Paste the `OPEN_COUNT 0` line into
   `d5-idle-gate.txt`: the game day is not over without it.
6. Dispatch again. Expected: green, `job-idle gate: pass`.

Pass: red with the seeded row, green before and after it, and `ACTION=status` printing `OPEN_COUNT 0` at the end.

## Results table (copy into the evidence README)

| Drill | Back: from -> to (SHA / deployment / hash) | Back: seconds | Forward: seconds | Health / check after each | Result |
|---|---|---|---|---|---|
| D1 Booking API | | | | | |
| D2 CRM API | | | | | |
| D3 ECS `aa-tripplanner-dev-web` | | | | | |
| D4 Lambda browse | | | | | |
| D5 job-idle gate | idle -> seeded -> cleared (`OPEN_COUNT 0`) | - | - | green / red / green | |

## After the run

- Add a row per drill to the [drill index](README.md) and move the runbooks out of "Not drilled yet".
- In each runbook's front-matter set `last_tested`, `tested_where: drill`, `tested_evidence` (the audit folder), add a
  tested-log row, and set `status: active` for the ones that passed both ways
  ([rollback-ecs](../runbooks/rollback-ecs.md), [rollback-booking](../runbooks/rollback-booking.md),
  [rollback-tp-lambda](../runbooks/rollback-tp-lambda.md)).
- Update the [operations index](../README.md) runbook table.

## Roll back or abort

- Any drill that does not come back healthy: run its forward step at once (it is the way back), then stop the game
  day and open an incident if the forward step fails ([incident response](../incident-response.md)).
- D5: whatever happened, run `ACTION=clear` and then `ACTION=status` until it prints `OPEN_COUNT 0` before you stop.
  A seeded row left behind does NOT end by itself on the normal Dev config (`JOB_TEST_KINDS` off: nothing claims
  `noop_sleep`); it stays queued, due now, and blocks DB Migrate apply, Migration Apply contract files and the
  terraform-apply job-idle gate until it is cleared. It ends by itself after `SLEEP_SECONDS` only when the worker runs
  with `JOB_TEST_KINDS=1`. The CIS deploy gate is not affected (`noop_sleep` is not `deploy_blocking`).
