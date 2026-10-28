---
id: OPS-04-crm-keys
title: Handle a CRM KMS key alarm
description: What to do when aa-crm-dev-kms-key-admin, aa-crm-dev-kms-foreign-use or aa-crm-dev-kms-decrypt-anomaly fires, or the nightly CRM key-policy diff is red - a change to, a use by a foreign principal of, or a Decrypt spike on the partner CRM's data, ingest or seal key.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-partner, kms, aa-cis-dev-db]
last_reviewed: 2026-10-28
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-04, OPS-10, SEC-02-rotation, docs/adr/0010-aa-partner-app.md, docs/adr/0008a-crm-separate-app-exceptions.md, AA-932, AA-934]
---

# Handle a CRM KMS key alarm

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> The alarms have never fired. The rule patterns were checked with `test-event-pattern` only (AA-932, S248).

## Why it matters

The partner CRM (AA-Partner) keeps every agency's travellers encrypted under per-tenant data keys, which are wrapped
by three KMS keys (design v3 §4.1, AA-932):

- `alias/crm-dev/data` - wraps the per-tenant data keys (context `{tenant_id, purpose}`) and the documents' SSE-KMS layer;
- `alias/crm-dev/ingest` - raw inbound mail (kept at most 1 day) and the audit export;
- `alias/crm-dev/seal` - the platform seal on signed agreements (asymmetric, signing only).

Only the CRM task role `aa-crm-dev-ecs-task-role` may use them; every other principal is denied by the key policy.
One narrow exception: the CRM break-glass role `aa-crm-dev-breakglass` (CRM-13b; not created yet) may `Decrypt` with
the **data** key only, and only the envelope keys whose context `tenant_id` equals its session tag `tenant_id`, so one
agency per session (statement `CrmBreakGlassOneAgency`, design v3 §5.5 L3). It cannot encrypt, and has no use of the
ingest or seal key. Every break-glass call fires `aa-crm-dev-kms-foreign-use`. The agency is the data controller and AA the processor (ADR 0008a): a key policy
changed without a plan, or a decrypt by an AA admin, is a processor incident the agency must hear about.

## The alarms and checks (AA-CIS-Infra `accounts/aa365/crm_data.tf`, `crm_storage.tf`)

| Rule | Fires on | Expected sources |
|---|---|---|
| `aa-crm-dev-kms-key-admin` | `PutKeyPolicy`, `CreateGrant`, `ScheduleKeyDeletion`, `DisableKey`, rotation off, alias move or delete, key material, `CancelKeyDeletion`, `EnableKey`, `TagResource`, `UntagResource` on any of the three keys | a planned local MFA Terraform apply that changes a key policy (the CI apply role cannot); a planned apply that changes the keys' tags (CI may tag; it may not remove `App`) |
| `aa-crm-dev-kms-foreign-use` | a crypto call (`Decrypt`, `Encrypt`, `GenerateDataKey*`, `ReEncrypt`, `Sign`), allowed **or denied**, by any principal other than the task role or an AWS service | a ticketed CRM break-glass session; nothing else |
| `aa-crm-dev-kms-decrypt-anomaly` (CloudWatch alarm, `crm_storage.tf`) | `Decrypt` calls on the three keys (any principal, metric `AA/Crm/Kms` `DecryptCalls`, 5-minute sums) above the anomaly band in 2 of 3 periods | a DEK cache miss storm after a deploy or restart, a bulk export or erasure run, a load test; until the model has about two weeks of data it stays `INSUFFICIENT_DATA` |
| **CRM Key Policy Diff** (nightly GitHub workflow in AA-CIS-Infra, `crm-key-policy-diff.yml`) | the live key policy of a key differs from the policy in the Terraform state (red run, GitHub failure e-mail; the summary names the key and the statement Sids) | a policy change outside Terraform (never planned), or a local MFA apply whose state upload failed |

E-mail: the alerts topic, text starting `[aa-crm]`, with the event, key, principal, source IP and error code (the
anomaly alarm uses the standard CloudWatch alarm e-mail).

## Steps

1. Was it planned? Check the session log and open PRs for an AA-CIS-Infra change to `crm_data.tf` applied locally at
   that time, or a break-glass ticket. Planned: note the alarm in the session log and stop.
   Rollback: none - read-only.

2. Read the event in CloudTrail (the e-mail time ± 15 minutes; `kms.amazonaws.com` events stay 90 days).

   ```bash
   aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=kms.amazonaws.com --start-time $(date -u -d '-2 hour' +%FT%TZ) --profile aa365-admin --region us-west-1 --query "Events[].[EventTime,EventName,Username,Resources[0].ResourceName]" --output table
   ```

   Expected: the event of the e-mail, with the principal. A `Username` that is not a known admin session or the CRM task
   role is an incident (SEV2 per [incident response](../incident-response.md)).

3. Compare the live key policy with Terraform (any difference = the policy was changed outside a reviewed apply).

   ```bash
   aws kms get-key-policy --key-id alias/crm-dev/data --policy-name default --profile aa365-admin --region us-west-1 --query Policy --output text
   ```

   Then run a read-only `terraform plan` of `accounts/aa365` with `-target=aws_kms_key.crm_data` (same for `crm_ingest`,
   `crm_seal`): "No changes" means the live policy is the reviewed one.
   Rollback: none - read-only.

4. If a key is scheduled for deletion and that was not planned: cancel at once (the window is 30 days, but every
   agency's data becomes unreadable when it ends).

   ```bash
   aws kms cancel-key-deletion --key-id alias/crm-dev/data --profile aa365-admin --region us-west-1
   ```

   Then `aws kms enable-key` (a cancelled deletion leaves the key disabled) and re-apply Terraform locally with MFA.
   Rollback: schedule the deletion again only through a reviewed Terraform change.

   If the tag `App = crm` was removed or changed (`UntagResource` / `TagResource` event): put it back with a local MFA
   `terraform apply -target=aws_kms_key.<key>` from `main`. Until then the CI boundary deny on CRM keys
   (`DenyCrmKeyUseAndPolicyEdits`, keyed on that tag) does not cover the key, so pause CI applies of `accounts/aa365`.

5. If the policy was changed: restore it with a local MFA `terraform apply -target=aws_kms_key.<key>` from `main`
   (the reviewed policy). This fires `aa-crm-dev-kms-key-admin` once more: expected.

6. If a foreign principal decrypted (not only attempted): treat it as a personal-data incident. Record which tenants'
   data keys could have been unwrapped (CloudTrail `requestParameters.encryptionContext.tenant_id`), keep the evidence
   in `docs/audits/<date>-S<nnn>-crm-key-incident/`, and bring the tech lead the agency notification draft (the agency is
   the controller; DPA wording, ADR 0010 decision 9).

## Decrypt-rate anomaly

1. Read who decrypted, from the alarm's log group (CloudTrail events copied by EventBridge, kept 365 days):

   ```bash
   aws logs filter-log-events --log-group-name /aws/events/aa-crm-dev-kms-decrypt --start-time $(date -u -d '-2 hour' +%s000) --profile aa365-admin --region us-west-1 --query "events[].message" --output text
   ```

   Expected: `detail.userIdentity` of almost every event is the CRM task role. Count by
   `detail.requestParameters.encryptionContext.tenant_id` and `purpose`.
2. Task role only, one tenant and purpose `export` or `docs`: a bulk export or documents batch; match it with the
   CRM job table (`crm.job`) and note it in the session log. Many tenants at once right after a deploy: the DEK cache
   was cold; note it. Anything else, or a principal that is not the task role (`aa-crm-dev-kms-foreign-use` fires
   too): steps 2 to 6 above.
   Rollback: none - read-only.

## Nightly key-policy diff is red

The AA-CIS-Infra workflow **CRM Key Policy Diff** compares each key's live policy with the Terraform state every night
(read-only plan role). Red = a key policy changed outside Terraform, or the check could not read a key.

1. Open the run summary: it names the key (`data`, `ingest`, `seal`) and the statement Sids that differ, or the error.
   An `ERROR ... GetKeyPolicy failed: AccessDeniedException` means the plan role lost read access: someone changed
   the key policy's `IamAdministration` statement, so treat it like a drift.
2. Drift: steps 2, 3 and 5 above (CloudTrail `PutKeyPolicy` event, compare, restore the reviewed policy with a local
   MFA apply from `main`). The `aa-crm-dev-kms-key-admin` alarm should have fired at the time of the change; if it did
   not, check the rule (`crm_kms_alarm_check.py` below).
3. Re-run the workflow (`workflow_dispatch`): expected green, every key "live policy = Terraform state".

## Verify the alarms without touching a key

After any change to the rules (read-only, EventBridge evaluates sample events against the live patterns):

```bash
python3 tools/terraform/crm_kms_alarm_check.py --profile aa365-admin --region us-west-1 --env dev
```

Run it from the AA-CIS-Infra checkout. Expected: every line `ok`, `0 failed`.

## Cost

KMS: 3 keys x 1 USD/month (+1 USD/month per symmetric key for each of its first two yearly rotations). The two rules
and the e-mails: 0 USD. Decrypt-rate anomaly alarm about 0.60 USD/month (anomaly-detection alarm 0.30 + metric-filter
metric 0.30; log ingestion negligible). The nightly diff: 0 USD.
