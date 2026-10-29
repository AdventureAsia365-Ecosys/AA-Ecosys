---
id: OPS-05-ecs-exec
title: Query the database through ECS exec and S3
description: The canonical way for a person or agent to run a Python (asyncpg) script against the shared RDS from inside an app container (CIS through S3; Booking and CRM through range reads of /tmp), with the whole result returned.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-booking-api, aa-crm-api, aa-cis-dev-db]
last_reviewed: 2026-10-29
review_every_days: 90
last_tested: 2026-10-17
tested_where: dev-acc2
tested_evidence: docs/audits/2026-10-17-S241-restore-drill/ (drill_check.py ran through this pattern)
related: [OPS-05, OPS-05-db-migrate, skill/aa-cis-schema/references/ecs-exec.md, AA-829, AA-852, AA-860, AA-892]
---

# Query the database through ECS exec and S3

> [!TIP]
> Run `tools/ecs/ecsx.sh <script.py> [VAR=value ...]` from the root repo (S253; `--help` lists every option). It
> starts the script detached from the SSM session (`tools/ecs/ecsx_runner.py`), so a dropped session
> (`Cannot perform start session: EOF`) loses nothing. On CIS containers it writes the whole output to
> `s3://aa-cis-bronze-005097885195/scripts/out/`, prints it and removes the objects; the manual steps below show
> what it does. On Booking and CRM containers, whose task roles cannot write the bronze bucket, it uses the
> [local mode](#booking-and-crm-containers-local-mode).

This page is the canonical copy of the pattern (data standard DM-8.8). The agent quick reference in
`skill/aa-cis-schema/references/ecs-exec.md`, the global `CLAUDE.md` block and older notes point here.

## When to use

- Read or small one-off writes on **CIS-owned** schemas (DM-8.8, MIG-5): counts, checks, an ad-hoc A/B script.
- Not for:
  - structure changes: a migration in the owning repo, applied by [DB Migrate](db-migrate.md);
  - anything that needs the RDS master or another app's schema (`booking.*`, `tripplanner.*`, roles, `catalog.*`):
    a reviewed `db/scripts/<name>.py` run by DB Migrate `mode=run-script`;
  - long work (more than about 5 minutes): enqueue a job on the worker through `shared.job` instead;
  - paid LLM calls without logging: an ad-hoc LLM script goes through `LLMClient` and writes
    `shared.llm_call_log` with `stage=adhoc_<issue>`.

## Which database login the script gets (X1, AA-852 / AA-860)

| X1 step | `DATABASE_URL` in the api container | What the script can reach |
|---|---|---|
| Before S18 (until 2026-10-19) | the master DSN (secret `aa-cis/dev/rds`) | everything; treat non-CIS schemas as off limits anyway (DM-8.9) |
| From S18 | `cis_app` (secret `aa-cis/dev/rds-cis-app`) | CIS schemas incl. RLS tables; **not** `booking.*` / `tripplanner.*` (error 42501), no DDL |
| From S19 (live since 2026-10-19) | as S18, and the CIS task role is denied `GetSecretValue` on the master, `aa-cis/dev/db-migrator`, `booking/*`, `tripplanner/*` | a script that reads the master secret fails with AccessDenied |

So scripts read the container's own `DATABASE_URL`. They never fetch `aa-cis/dev/rds` themselves. S18 and S19 are
both live since 2026-10-19; step 0 shows the secret the api task definition injects.

## Preconditions

- Access: profile `aa365-admin` (MFA session), region `us-west-1`; the Session Manager plugin installed locally.
- The api service has a running task (`desiredCount` 1 or more).
- Every exec session is logged to `/ecs/aa-cis-dev/exec-sessions` (365 days, D-07). Say why in the session log.
- Cost: 0 USD (a few S3 requests).

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map).

## Steps

0. See which DB login the container uses (read-only).

   ```bash
   aws ecs describe-task-definition --task-definition aa-cis-dev-api --profile aa365-admin --region us-west-1 --query "taskDefinition.containerDefinitions[0].secrets[?name=='DATABASE_URL'].valueFrom" --output text
   ```

   Expected: a secret ARN ending in `aa-cis/dev/rds-cis-app-…` (S18 and later). `aa-cis/dev/rds-…` alone would mean
   the master, as before S18: stop and check the task definition.
   Rollback: none - read-only.

1. Write the script locally (in `.tmp-session/` or the scratchpad, never `~/`). Template:

   ```python
   import asyncio, json, os, boto3, asyncpg

   async def main():
       # application_name: data standards C1.1a (asyncpg ignores PGAPPNAME), so PI / pg_stat_activity show "cis-exec"
       conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require",
                                    server_settings={"application_name": "cis-exec"})
       rows = await conn.fetch("SELECT ...")  # always schema-qualify; CIS schemas only
       with open("/tmp/result.json", "w") as f:
           json.dump([dict(r) for r in rows], f, indent=2, default=str)
       await conn.close()
       boto3.client("s3", region_name="us-west-1").upload_file("/tmp/result.json", "aa-cis-bronze-005097885195", "scripts/result.json")

   asyncio.run(main())
   ```

   Read table and column names from `docs/architecture/db-schema-reference.md`; never guess them. To use app code,
   add `sys.path.insert(0, "/app")`.

2. Upload, presign, find the task and run it. One command per line; zsh does not split a variable that holds
   several flags, so keep flags literal.

   ```bash
   aws s3 cp /home/nghiep/projects/AA-Ecosys/.tmp-session/script.py s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1
   URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1 --expires-in 300)
   TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
   aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/s.py && python3 /tmp/s.py && echo DONE'" --profile aa365-admin --region us-west-1
   ```

   Expected: `DONE`. `execute-command` can hang for up to about 120 seconds: run it in the background and wait for
   the result object in S3.
   Rollback: a read-only script has nothing to undo. A script that writes follows the DRY RUN steps in
   `skill/aa-cis-schema/references/destructive-ops.md` (count, snapshot, SAVEPOINT, COMMIT only after the tech lead's OK).

3. Fetch the result, then delete both objects (the `scripts/` prefix has no lifecycle rule, so files stay forever).

   ```bash
   aws s3 cp s3://aa-cis-bronze-005097885195/scripts/result.json /home/nghiep/projects/AA-Ecosys/.tmp-session/result.json --profile aa365-admin --region us-west-1
   aws s3 rm s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1 # WRITE
   aws s3 rm s3://aa-cis-bronze-005097885195/scripts/result.json --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: the JSON locally, nothing left under `scripts/` from this run.
   Rollback: none needed (the bucket is versioned; a deleted object can be restored from its previous version).

## Booking and CRM containers: local mode

The local mode of `tools/ecs/ecsx.sh` (S257) keeps the output in the container and reads it back in short pieces.
It is the default for every service whose name does not start with `aa-cis-`; `ECSX_MODE=local` forces it anywhere.

```bash
ECSX_SERVICE=aa-booking-dev-api tools/ecs/ecsx.sh /home/nghiep/projects/AA-Ecosys/.tmp-session/bk_check.py LIMIT=20
ECSX_SERVICE=aa-crm-dev-api tools/ecs/ecsx.sh /home/nghiep/projects/AA-Ecosys/.tmp-session/crm_check.py
```

Both task definitions name their container `api` (`infra/AA-CIS-Infra/accounts/aa365/booking.tf`, `crm_app.tf`),
the default; `ECSX_CONTAINER` overrides it. The script reads the container's own `DATABASE_URL`: role `booking`
(schema `booking`) or `crm_app` (schema `crm`).

How it works (`tools/ecs/ecsx_local.py` on this side, `ecsx_runner.py` in the container):

1. **Ship.** The script and the runner reach `/tmp` of the container. Default (`ECSX_SHIP=auto`): they are uploaded
   to `scripts/ecsx/` of the bronze bucket, and the container fetches the presigned GET URLs with Python `urllib`
   (the Booking and CRM images have no curl; a presigned GET needs no task-role permission). If that is not
   confirmed, or with `ECSX_SHIP=inline`, they travel as base64 pieces inside the exec commands, one file per piece
   (a retried call cannot duplicate data), `ECSX_INLINE_CHUNK` characters each (default 2000). The ECS API sets no
   length limit on `--command`; the S3 mode already sends about 3 KB (two presigned URLs) per command. Either way the
   container checks both files against their sha256 before anything runs, and the S3 objects are removed at once.
2. **Start.** The runner forks into its own session and streams stdout + stderr into `/tmp/ecsx-<id>.out`. At the
   end it writes `/tmp/ecsx-<id>.done` (`rc=<n> bytes=<m>`).
3. **Read.** Short exec calls run `ecsx_runner.py read <id> <offset> <length>`. Each prints `ECSX_CHUNK` lines
   (offset, length, file size, state, CRC32, base64 of `ECSX_READ_CHUNK` bytes, default 1024). This side accepts only
   lines that continue at the expected offset with the right length and CRC, prints the bytes as they come, and asks
   again for anything the SSM terminal dropped. Output appears while the script still runs.
4. **Clean.** After the `.done` marker and the last byte, `/tmp/ecsx-<id>.*` is removed (`ECSX_KEEP=1` keeps it).
   The exit code is the script's.

Limits and recovery:

- Each exec call is cut after `ECSX_EXEC_TIMEOUT` seconds (default 60) with its whole process group.
- About 1 KB per exec call, a few seconds each: a 100 KB output takes minutes. Print a compact summary, not raw rows.
- If no result arrives within `ECSX_TIMEOUT` seconds (default 900), the run keeps going in the container and the
  tool prints a resume command: `ECSX_SERVICE=<same service> tools/ecs/ecsx.sh --resume <id> <offset>`.
- Eight reads in a row with no usable line (task replaced, runner not shipped) stop the tool with exit code 4; the
  files stay in the container until the task is replaced.
- Long work (more than about 5 minutes) still belongs in a job (`booking.job`, `crm.job`), not in exec.

## Port-forward for a GUI client (optional)

ECS exec also carries the `AWS-StartPortForwardingSessionToRemoteHost` document, so DBeaver can reach the DB through
the running api task. The remote host is the private DB name **`db.dev.internal`** (AA-829, S248): the task resolves
it inside the VPC, and it follows a restore or replacement of the instance, so this page needs no endpoint lookup.
The CNAME points at `aa-cis-dev-db`, and since the AA-829 DSN switch (2026-10-23) every DSN secret names the same
host. Fallback, only if the name does not resolve (private zone missing): the RDS
endpoint from
`aws rds describe-db-instances --db-instance-identifier aa-cis-dev-db --profile aa365-admin --region us-west-1 --query "DBInstances[0].Endpoint.Address" --output text`.

```bash
TASK_ID=$(echo $TASK_ARN | cut -d'/' -f3)
RUNTIME_ID=$(aws ecs describe-tasks --cluster aa-cis-dev-cluster --tasks $TASK_ARN --profile aa365-admin --region us-west-1 --query 'tasks[0].containers[0].runtimeId' --output text)
aws ssm start-session --target "ecs:aa-cis-dev-cluster_${TASK_ID}_${RUNTIME_ID}" --document-name AWS-StartPortForwardingSessionToRemoteHost --parameters "{\"host\":[\"db.dev.internal\"],\"portNumber\":[\"5432\"],\"localPortNumber\":[\"15432\"]}" --profile aa365-admin --region us-west-1
```

DBeaver: `localhost:15432`, database `aa_cis_dev`, the login the task uses (see step 0), SSL mode `require` (the RDS
certificate does not name `db.dev.internal` or `localhost`, so `verify-full` fails by design). Never SSH; never a public
endpoint (DM-8.8). The older tunnel note is superseded by this section and archived as
[db-access-ssm-tunnel](../../archive/2026/db-access-ssm-tunnel.md).

## Logs

- ECS: `/ecs/aa-cis-dev` (api and worker, stream prefixes `api/` and `worker/`), 30 days; `/ecs/aa-booking-dev`,
  30 days; `/ecs/aa-crm-dev` (Partner CRM api), 30 days; exec sessions `/ecs/aa-cis-dev/exec-sessions`, 365 days.
- Lambda: `/aws/lambda/<function-name>`, 30 days (identity triggers 365 days).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-17 | dev-acc2 | Claude Code | S241 restore drill compare script (`docs/audits/2026-10-17-S241-restore-drill/`) ran through steps 2-3; that script still read the master secret itself (the pre-X1 variant this page retires) | pass |
| 2026-10-19 | dev-acc2, step 0 only | Claude Code | `docs/audits/2026-10-19-S243-ops-runbooks/readonly-checks.md`: api still on the master DSN secret (X1 S18 not live) | pass |
