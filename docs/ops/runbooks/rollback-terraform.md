---
id: OPS-02-terraform
title: Roll back a Terraform change
description: Undo an AA-CIS-Infra change on acc2 by a revert PR and a fresh apply from main, with the special cases for bootstrap roles, the state file and deleted resources.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-infra]
last_reviewed: 2026-10-19
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-01, OPS-04, OPS-02-cis, AA-866, AA-869, AA-892]
---

# Roll back a Terraform change

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> Revert-and-apply is the normal Infra flow and runs every week, but no rollback has been run as a drill. The
> state-file restore (step 6) has never been run.

## When to use

- Trigger: a `terraform-apply.yml` run on acc2 (root `accounts/aa365`) broke something: an alarm fires, a service
  loses access (AccessDenied in the logs), a route or DNS name stops answering.
- Not for: app code (use the app rollback runbooks) or DB migrations ([DB Migrate](db-migrate.md)).

## Facts that shape this runbook

- Apply runs only by dispatch from `main` (AA-866): `terraform-apply.yml` has `if: github.ref == 'refs/heads/main'`
  and the apply role trusts only `refs/heads/main`. It applies the **whole** `accounts/aa365` root, so every other
  change merged on `main` goes out with your revert.
- **Bootstrap roles** (`aa-cis-infra-tf-apply`, `aa-cis-dev-app-deploy`, the plan role and their inline policies) cannot
  be changed by the CI apply role. A change to them is applied by hand with MFA, targeted, from merged `main`.
- The LLM satellite roots (`accounts/acc1-bedrock`, `accounts/acc3-bedrock`) are applied locally with their own
  profiles (see the [account map](../../onboarding.md#account-map)); no workflow applies them.
- State: S3 bucket `aa-cis-tfstate-005097885195`, key `dev/terraform.tfstate`, **versioning on** (206 versions on
  19/10/2026), DynamoDB lock table `aa-cis-tfstate-lock-005097885195`.
- Safety nets for deleted data: RDS `deletion_protection` on; Secrets Manager deletes keep a 30-day recovery window
  (`restore-secret`); the bronze, state and Lambda-artifact buckets are versioned.
- Cost: 0 USD (one apply run).

## Preconditions

- No other Infra PR is being applied (one Infra merge at a time, each followed at once by its apply).
- Read the plan of the revert PR before merging it: a revert of a `removed` or `import` block is not a clean undo.

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the account map.

## Steps

1. Find the apply that broke it and what it changed.

   ```bash
   gh run list -R AdventureAsia365-Ecosys/AA-CIS-Infra --workflow terraform-apply.yml -L 5
   gh run view <run-id> -R AdventureAsia365-Ecosys/AA-CIS-Infra --log | grep -E "will be|must be|Apply complete"
   ```

   Expected: the resource lines of the bad apply and the PR merged just before it.
   Rollback: none - read-only.

2. Open a revert PR on AA-CIS-Infra (`git revert <merge-sha>` on a `fix/` branch, body `Refs AA-xxx`). Read the
   `terraform-plan.yml` comment on the PR.
   Expected: the plan shows only the inverse of step 1.
   Verify: no `destroy` of a stateful resource (RDS, secret, bucket, Cognito pool). If there is one, stop and ask
   Nghiệp.
   Rollback: close the PR.

3. Merge the revert PR, then apply from `main`.

   ```bash
   gh workflow run terraform-apply.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main # WRITE
   gh run watch -R AdventureAsia365-Ecosys/AA-CIS-Infra $(gh run list -R AdventureAsia365-Ecosys/AA-CIS-Infra --workflow terraform-apply.yml -L 1 --json databaseId --jq '.[0].databaseId')
   ```

   Expected: `Apply complete!` with the counts from the plan.
   Verify: "Verify the result" below.
   Rollback: revert the revert and apply again.

4. IAM change that failed with AccessDenied right after it was created: run the apply a second time (IAM is
   eventually consistent, S241).

5. Bootstrap role change (the apply role cannot write it): apply by hand with MFA, targeted, from a clean checkout of
   merged `main`.

   ```bash
   export $(aws configure export-credentials --profile aa365-admin --format env | xargs) && unset AWS_PROFILE
   terraform -chdir=accounts/aa365 plan -target=<resource-address> -out=/tmp/rb.tfplan
   terraform -chdir=accounts/aa365 apply /tmp/rb.tfplan # WRITE
   ```

   Expected: the plan touches only the target.
   Rollback: the same with the previous commit checked out.

6. Last resort - the state file is corrupt (init or plan fails to decode it, not just a warning). Do this only with
   Nghiệp, with no apply running. List the versions and copy the last good one back as the current object:

   ```bash
   aws s3api list-object-versions --bucket aa-cis-tfstate-005097885195 --prefix dev/terraform.tfstate --profile aa365-admin --region us-west-1 --query "Versions[:5].[VersionId,LastModified,IsLatest]" --output table
   aws s3api copy-object --bucket aa-cis-tfstate-005097885195 --key dev/terraform.tfstate --copy-source "aa-cis-tfstate-005097885195/dev/terraform.tfstate?versionId=<good-version-id>" --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: a new current version equal to the good one. The lock table may hold a digest of the old state; if
   init then reports a checksum mismatch, update the digest item as the error message says.
   Verify: `terraform plan` from `main` shows only the drift you expect.
   Rollback: copy the version that was current before step 6 back the same way.
   Note: the AWS provider 6 upgrade (S242) prints "Failed to decode resource from state" for leftover v5
   attributes. That is a warning, not corruption; the pre-upgrade state version is kept as the way back.

## Verify the result

- The resource that broke works again: the alarm is `OK`, the service log has no new AccessDenied, the route answers.
- `terraform plan` on `main` (the next PR's plan or a dispatch of `terraform-plan.yml`) shows no changes.

## Roll back or abort

- Every step that writes is a normal apply; undo it with another revert and apply.
- Abort before step 6 unless the state file itself is broken.

## Escalation

- [Incident response](../incident-response.md). A change that removes access to data or secrets is SEV1.

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-19 | dev-acc2, read-only facts (state versioning, lock table) | Claude Code | `docs/audits/2026-10-19-S243-ops-runbooks/readonly-checks.md` | read-only only |
