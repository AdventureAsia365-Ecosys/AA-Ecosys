---
id: OPS-02-tp-lambda
title: Roll back the TripPlanner Lambdas
description: Return aa-tripplanner-dev-browse and aa-tripplanner-dev-assembly to the previous code, by a revert on main or by hand from the versioned artifacts bucket.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [tripplanner-lambda]
last_reviewed: 2026-10-28
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-02-vercel, OPS-04, AA-703, AA-869, AA-892]
---

# Roll back the TripPlanner Lambdas

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> Only the read-only steps were run (2026-10-19, facts re-checked 2026-10-28). A Lambda alias `live` would make this
> a one-line switch. It is planned (U-54, with AA-703) and does not exist yet.

## When to use

- Trigger: after a `deploy-lambdas.yml` run, the TripPlanner map or trip pages fail, or
  `aa-tripplanner-dev-browse-errors` / `aa-tripplanner-dev-assembly-errors` fires.
- Not for: the TripPlanner frontend ([rollback-vercel](rollback-vercel.md)) or a bad `tp-NNN` migration
  ([DB Migrate](db-migrate.md): forward only).

## Facts that shape this runbook (read 2026-10-28)

- The HTTP API invokes both functions **unqualified**, so traffic always goes to `$LATEST`. There is no alias.
- `deploy-lambdas.yml` runs only after the full CI passed on the commit (AA-879). Every deploy runs
  `update-function-code --publish`, so each deploy leaves a numbered version with its `CodeSha256`. Both functions
  are deployed together and get the same version number.
- The artifacts bucket `aa-tripplanner-dev-lambda-artifacts-005097885195` is **versioned**; each deploy overwrites
  `browse.zip` and `assembly.zip`, and the older objects stay as previous versions.
- Since AA-993 each uploaded zip carries object metadata `git-sha`, `app-version` and `code-sha256` (the same form as
  the function's `CodeSha256`). The deploy's `verify` job (`post-deploy-verify.yml`, app `lambdas`) compares the
  running code with it.
- The zips are about 45 MB, close to the 50 MB direct-upload limit, so the hand path uses S3, not `--zip-file`.
- Configuration (environment, role, VPC, layers) is **not** rolled back by a code rollback. Example: since AA-878
  (S243) the code reads the edge API key from Secrets Manager and the plaintext variable is gone; code from before
  that change would fail closed. Check that the target code works with today's configuration.
- The GitHub deploy role trusts only `refs/heads/main`, so a dispatch from another branch is refused.
- Cost: 0 USD.

## Preconditions

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map).

## Steps

Path A (preferred, a few minutes): revert the bad PR on AA-TripPlanner-Web `main`. A change under `backend/**`
triggers `deploy-lambdas.yml`, which publishes the reverted code. Then go to "Verify the result".

Path B (by hand, when CI is slow or broken):

1. Find the last good code hash. List the recent published versions:

   ```bash
   aws lambda list-versions-by-function --function-name aa-tripplanner-dev-browse --profile aa365-admin --region us-west-1 --query "Versions[-4:].[Version,LastModified,CodeSha256]" --output table
   ```

   Expected: the newest version is the bad deploy; note the `CodeSha256` of the one before it.
   Verify: its `LastModified` is before the bad merge.
   Rollback: none - read-only.

2. Find the matching S3 object version of each zip (same time as that Lambda version):

   ```bash
   aws s3api list-object-versions --bucket aa-tripplanner-dev-lambda-artifacts-005097885195 --prefix browse.zip --profile aa365-admin --region us-west-1 --query "Versions[:4].[VersionId,LastModified,IsLatest]" --output table
   ```

   Run it again with `--prefix assembly.zip`. Confirm a candidate version by its metadata:

   ```bash
   aws s3api head-object --bucket aa-tripplanner-dev-lambda-artifacts-005097885195 --key browse.zip --version-id <browse-version-id> --profile aa365-admin --region us-west-1 --query "Metadata" --output json
   ```

   Expected: the second row (not `IsLatest`) is the previous deploy; its `code-sha256` equals the hash from step 1
   and its `git-sha` is the commit before the bad merge.
   Rollback: none - read-only.

3. Point each function at the previous zip and publish.

   ```bash
   aws lambda update-function-code --function-name aa-tripplanner-dev-browse --s3-bucket aa-tripplanner-dev-lambda-artifacts-005097885195 --s3-key browse.zip --s3-object-version <browse-version-id> --publish --profile aa365-admin --region us-west-1 --query "[Version,CodeSha256]" --output text # WRITE
   aws lambda update-function-code --function-name aa-tripplanner-dev-assembly --s3-bucket aa-tripplanner-dev-lambda-artifacts-005097885195 --s3-key assembly.zip --s3-object-version <assembly-version-id> --publish --profile aa365-admin --region us-west-1 --query "[Version,CodeSha256]" --output text # WRITE
   aws lambda wait function-updated --function-name aa-tripplanner-dev-browse --profile aa365-admin --region us-west-1
   aws lambda wait function-updated --function-name aa-tripplanner-dev-assembly --profile aa365-admin --region us-west-1
   ```

   Expected: a new version number whose `CodeSha256` equals the hash from step 1.
   Verify: a different hash means the wrong object version; repeat with the right one.
   Rollback: the same commands with the newest object version (the bad code).

4. Revert the bad PR on `main` anyway, so the next deploy does not bring the bad code back.

## Verify the result

```bash
curl -s -o /dev/null -w "%{http_code}\n" "https://tripplanner.lumiguides.it.com/api/browse?resource=countries"
aws cloudwatch describe-alarms --alarm-names aa-tripplanner-dev-browse-errors aa-tripplanner-dev-assembly-errors --profile aa365-admin --region us-west-1 --query "MetricAlarms[].[AlarmName,StateValue]" --output text
```

Expected: 200 (the response lists countries with `component_count`); both alarms `OK` within 10 minutes.

For a full check after Path A (or after step 4 of Path B has deployed), dispatch the verify workflow from `main`.
`<deploy-commit-sha>` is the full commit SHA of the last `deploy-lambdas.yml` run, that is the revert commit.

```bash
gh workflow run post-deploy-verify.yml --repo AdventureAsia365-Ecosys/AA-TripPlanner-Web --ref main -f app=lambdas -f expected_sha=<deploy-commit-sha>
```

Expected: the run is green (both functions `Active`, `CodeSha256` equal to the newest zip in the bucket, browse and
assembly rows answer).
Note: the workflow reads the **newest** zip object, not an older version. Right after Path B step 3 the newest zip is
still the bad one, so the run fails until step 4 deploys the revert. Use the curl and alarm checks above meanwhile.

## Roll back or abort

- Path B is undone by step 3 with the newest object version.
- Abort when the previous code needs configuration that no longer exists: fix forward.

## Escalation

- [Incident response](../incident-response.md). TripPlanner is the public front door: a full outage is SEV1.

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-19 | dev-acc2, read-only facts and steps 1-2 | Claude Code | `docs/audits/2026-10-19-S243-ops-runbooks/readonly-checks.md` | read-only only; write steps untested |
