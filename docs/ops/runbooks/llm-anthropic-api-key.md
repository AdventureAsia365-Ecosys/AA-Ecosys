---
id: APP-06-anthropic-key
title: Plug in and probe the Anthropic API key
description: How the tech lead stores the Anthropic API key, switches the anthropic-direct LLM connection on with the one audited admin PATCH, runs the adhoc_aa1002 probe through LLMClient and switches the connection off again (LLM gateway slice S2).
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, aa-cis-dev-db]
last_reviewed: 2026-10-30
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [APP-06, OPS-05-ecs-exec, SEC-02-rotation, OPS-04-llm-cost-spike, AA-1002]
---

# Plug in and probe the Anthropic API key

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.

Source of truth: AA-CIS-App `shared/llm_client/adapters/anthropic_messages.py`, `shared/llm_client/vendor_route.py`,
`api/services/llm_connections.py` (`set_enabled`), migration `api/migrations/306_llm_anthropic_deployments.sql` and
`docs/implementation-notes/AA-1002.md` (slice S2). The probe script is
[`tools/llm/aa1002_anthropic_probe.py`](../../../tools/llm/aa1002_anthropic_probe.py) in this repo.

## What this does and does not do

LLM gateway slice S2 adds a second way to call Anthropic models: the Anthropic Messages API on the connection
`anthropic-direct` (kind `anthropic`, data scope `vendor_direct`). Migration 306 seeds one `anthropic-direct`
deployment per Anthropic catalog model at priority 100, behind acc3 (priority 10), and leaves the connection off.

- Switching the connection on moves **no stage route**: every Anthropic API deployment sits behind acc3. Only a
  probe that pins the deployment (`model_tier = "haiku-5-5@anthropic-direct"`) reaches the API.
- Making the API the first way in for a model is a separate decision (see
  [Making the API primary for a model](#making-the-api-primary-for-a-model)).

> [!IMPORTANT]
> **Switch the connection off again after the probe.** Keep `anthropic-direct` off until slice S5 (data scopes) and
> slice S10 (the provider-wide daily cap for `anthropic` in `cost_guard`) have landed. Until S10, Anthropic API spend
> is logged in `shared.llm_call_log` (provider `anthropic`) but no provider-wide daily cap counts it: `cost_guard`
> sums only `bedrock%` and `openai`. A job's own run budget and a kind-scoped daily cap still count it.

## Before you start

- The CIS migration 306 is applied on Dev (`shared.schema_versions` has `306`) and the CIS code PR "Anthropic
  Messages API adapter behind the connection registry" is deployed (api and worker on the same image SHA).
- You have the Anthropic API key in a file, never on a command line. Recommended on the Anthropic side: a dedicated
  workspace for this key with a monthly spend limit.
- Cost of the whole procedure: under $0.001 (one Haiku 5.5 call), plus about $0.40 a month for the secret.

## 1. Confirm the account

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account of the [account map](../../onboarding.md#account-map). Abort on any other account.

## 2. Check the deploy before the key exists ($0, no key)

1. Read the connection listing. The admin secret comes from Secrets Manager; it never goes into the shell history.

   ```bash
   ADMIN_SECRET=$(aws secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --query SecretString --output text --profile aa365-admin --region us-west-1)
   curl -s https://api-cis.lumiguides.it.com/admin/llm-connections -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" | python3 -m json.tool | head -80
   ```

   Expected: HTTP 200, `"routing_uses_registry": true`; `anthropic-direct` has `"enabled": false`,
   `"secret_name": "aa-llm/dev/anthropic-direct"`, `"policy_problems": []` and its deployments at priority 100. No
   `sk-` string anywhere in the body.

2. Check that the switch refuses what it must refuse:

   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" -X PATCH https://api-cis.lumiguides.it.com/admin/llm-connections/acc3 -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" -H "content-type: application/json" -d '{"enabled": false}'
   curl -s -X PATCH https://api-cis.lumiguides.it.com/admin/llm-connections/anthropic-direct -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" -H "content-type: application/json" -d '{"enabled": true}'
   ```

   Expected: `422` for `acc3` (the gateway reads no Bedrock flag before slice S3). For `anthropic-direct` before the
   secret exists: `422` with `secret unreadable (ResourceNotFoundException)`, and nothing is written (no audit row).

Verify: no `anthropic` row appears in `shared.llm_call_log` after the deploy (read-only, as `cis_app`, through
[ECS exec](ecs-exec-s3-mediated.md)):

```sql
SELECT provider, account, count(*) FROM shared.llm_call_log WHERE created_at > now() - interval '1 hour' GROUP BY 1, 2 ORDER BY 1, 2;
```

Abort: if the listing shows `"enabled": true` for `anthropic-direct` or a policy problem, stop and fix the row
first.

## 3. Store the key

Create the secret from a file, then delete the file. The secret holds the bare key or the JSON `{"api_key": "<key>"}`.

```bash
aws secretsmanager create-secret --name aa-llm/dev/anthropic-direct --secret-string file:///home/nghiep/projects/AA-Ecosys/.tmp-session/anthropic-key.txt --profile aa365-admin --region us-west-1  # WRITE
shred -u /home/nghiep/projects/AA-Ecosys/.tmp-session/anthropic-key.txt
```

- The name must start with `aa-llm/` (a table CHECK and the gateway both refuse anything else).
- The CIS task role already has `secretsmanager:GetSecretValue` on this name: no IAM change.
- The Secrets Manager console works too (plaintext, the bare key).

Verify: `aws secretsmanager describe-secret --secret-id aa-llm/dev/anthropic-direct --profile aa365-admin --region us-west-1 --query Name --output text`
prints the name. Never run `get-secret-value` on it.

Rollback: `aws secretsmanager delete-secret --secret-id aa-llm/dev/anthropic-direct --profile aa365-admin --region us-west-1  # WRITE`
(30-day recovery window).

## 4. Switch the connection on (one audited PATCH)

```bash
curl -s -X PATCH https://api-cis.lumiguides.it.com/admin/llm-connections/anthropic-direct -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" -H "x-admin-user-id: tech-lead" -H "content-type: application/json" -d '{"enabled": true}'  # WRITE
```

Expected: `{"connection_key":"anthropic-direct","kind":"anthropic","enabled":true,"changed":true,"updated_by":"admin:tech-lead"}`.
The switch reads the secret before it writes and refuses (`422`) when it cannot. The api process uses the new state
at once; the worker within 5 minutes (registry cache).

Verify the audit row:

```sql
SELECT actor, action, resource_id, details, created_at FROM acp_shared.audit_log WHERE action = 'llm_connection_changed' ORDER BY created_at DESC LIMIT 1;
```

Expected: actor `admin:tech-lead`, `details` with `before.enabled = false`, `after.enabled = true`, the secret NAME
(never the key).

Rollback: the same PATCH with `{"enabled": false}` (step 6).

## 5. Probe the key

Run the probe in the CIS worker container with [`tools/ecs/ecsx.sh`](../../../tools/ecs/ecsx.sh) (it returns the
whole output; the manual S3-mediated steps are in the [ECS exec runbook](ecs-exec-s3-mediated.md)). Run it on the
api service instead (`ECSX_SERVICE=aa-cis-dev-api`) if you do not want to wait up to 5 minutes for the worker cache.

```bash
ECSX_SERVICE=aa-cis-dev-worker tools/ecs/ecsx.sh tools/llm/aa1002_anthropic_probe.py PROBE_MODEL=haiku-5-5
```

Expected output (one JSON line):

```json
{"ok": true, "content": "OK", "model_used": "anthropic-api-haiku-5-5", "provider": "anthropic", "provider_model": "claude-haiku-5-5", "tokens_in": 30, "tokens_out": 3, "cost_usd": 0.00001, "stop_reason": "end_turn"}
```

Token counts and cost vary a little; `provider_model` is the model the API says answered.

Verify the cost row (`stage = 'adhoc_aa1002'`, role `validate`):

```sql
SELECT model, provider, account, tokens_in, tokens_out, cost_usd, stop_reason, quality_signal, created_at FROM shared.llm_call_log WHERE stage = 'adhoc_aa1002' ORDER BY created_at DESC LIMIT 3;
```

Expected: model `haiku-5-5`, provider `anthropic`, account NULL (slice S2 does not record the connection there;
the probe puts it and `provider_model` into `quality_signal`).

If the probe prints `{"ok": false, ...}`, read `llm_error_class`:

| `llm_error_class` / error | Meaning | Action |
|---|---|---|
| `access_denied` | 401 or 403: wrong or revoked key, or no permission in the workspace | Check the key, update the secret (`put-secret-value` from a file), re-run. A 401 drops the cached key, so the next call reads the new value |
| `quota_exhausted` | No credit, or the workspace spend limit is reached | Add credit or raise the limit on the Anthropic side |
| `throttled` | 429 rate limit or 529 overloaded | Wait a minute and re-run |
| `secret unreadable (...)` | Secret name or task role | Check step 3; the name must be exactly `aa-llm/dev/anthropic-direct` |
| `connection ... is missing or disabled` | The worker still has the old registry | Wait 5 minutes or run on the api service |

## 6. Switch the connection off again

```bash
curl -s -X PATCH https://api-cis.lumiguides.it.com/admin/llm-connections/anthropic-direct -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" -H "x-admin-user-id: tech-lead" -H "content-type: application/json" -d '{"enabled": false}'  # WRITE
unset ADMIN_SECRET
```

Expected: `"enabled": false, "changed": true` and a second `llm_connection_changed` audit row. Keep it off until S5
and S10 (see the warning at the top). The secret can stay: a disabled connection never reads it.

Record the run: set `last_tested`, `tested_where: dev-acc2` and `tested_evidence` (the probe output and the
`llm_call_log` row, saved under `docs/audits/<date>-S<nnn>-<slug>/`) in this page's front-matter.

## Making the API primary for a model

Not part of this procedure. It needs a tech lead decision on three points:

1. **Data scope**: `anthropic-direct` is `vendor_direct`. A tenant (T-series) stage on such a model sends tenant
   content outside AWS. Nothing enforces data scopes before slice S5.
2. **Budget**: no provider-wide daily cap for `anthropic` before slice S10.
3. **Mechanism**: lower that model's `anthropic-direct` deployment priority below 10 (acc3) with a CIS migration or
   DB Migrate `mode=run-script` (`cis_app` cannot write deployments). Revert: priority back to 100, or switch the
   connection off (every model returns to Bedrock within 5 minutes). Legacy keys `haiku` / `sonnet` cannot use the
   API before slice S3.

> [!CAUTION]
> Slice S3 (spread a route over every deployment) turns the seeded `anthropic-direct` deployments into same-model
> fallbacks automatically, tenant models included. S5 data scopes must land before or with S3; otherwise tenant
> content leaves AWS whenever acc3 fails.

## Rotate the key

Update the secret from a file (`aws secretsmanager put-secret-value --secret-id aa-llm/dev/anthropic-direct --secret-string file://<path> --profile aa365-admin --region us-west-1  # WRITE`),
delete the file, then re-run step 5 with the connection on. A cached key lives up to the credential cache TTL; a 401
drops it at once. See also the [secret rotation runbook](secret-rotation.md).
