---
id: APP-06-anthropic-key
title: Plug in and probe the Anthropic API key
description: "One command plugs the Anthropic API key into the Dev AI gateway: it stores secret aa-llm/dev/anthropic-direct from stdin, sets the anthropic-direct connection's budget (150 USD a month, hard stop), probes one Haiku 5.5 call and only then switches the connection on."
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, aa-cis-dev-db]
last_reviewed: 2026-11-05
review_every_days: 90
last_tested: 2026-11-05
tested_where: dev-acc2
tested_evidence: "Dev, connection anthropic-direct (S269). Linear AA-1026 comment 05/11: secret created, budget 150 USD hard stop, probe haiku-5-5 ok 0.000005 USD, connection ON; AA-1042 comment: 13/13 Claude deployments probed ok after CIS 376"
related: [APP-06, APP-06-routes, OPS-05-ecs-exec, SEC-02-rotation, OPS-04-llm-cost-spike, AA-1002, AA-1004, AA-1026]
---

# Plug in and probe the Anthropic API key

Tested on Dev with the real key on 05/11/2026 (S269): see `tested_evidence` in the front-matter. The offline test
of the script stays `tools/llm/test_anthropic_key_plug_in.sh` (fake `aws` and `curl`).

Source of truth: the script [`tools/llm/anthropic_key_plug_in.sh`](../../../tools/llm/anthropic_key_plug_in.sh)
(`--help`), and in AA-CIS-App `api/services/llm_connections.py` (`update_connection`, `test_connection`),
`shared/llm_client/adapters/anthropic_messages.py`, `shared/llm_client/vendor_route.py` and migrations 306, 311, 317,
335.

## What it does

The Anthropic Messages API is a second way to the Claude models, on the connection `anthropic-direct` (kind
`anthropic`, data scope `vendor_direct`). Everything except the key is in place on Dev:

- One `anthropic-direct` deployment per Anthropic Converse catalog model (migration 306) at priority 100, behind the
  acc3 Bedrock deployment (priority 10). Per model, the gateway tries acc3 first and the API after it.
- Data scopes per stage (migration 311, decided by data, not code): only a stage whose `allowed_scopes` include
  `vendor_direct` can reach the API. Since migration 335 (AA-1026, tech lead decision T-3 in S263) those are the five
  A-series writers `s1_generate`, `s1_flag_fix`, `s1_itinerary_nudge`, `a0_column_map`, `supply_content_writer`.
  Each names one Anthropic model, then GPT-6 Luna on the OpenAI API, so the API is reached only after acc3 failed for
  the whole route (the gateway tries every deployment of a model before the next model; the admin refuses an AWS
  fallback behind a model with an API deployment on such a stage).
  T-stages (tenant content), `tp_*` (traveller text) and the CRM stay `aws_only`: they never reach the API.
- The legacy keys `haiku` / `sonnet` never ran on the API. Migration 335 moved every route off them to `haiku-5-5` /
  `sonnet-5-5` (decision T-4), which have API deployments.
- Monthly budget per connection, enforced on every call path (slice S10): `anthropic-direct` 150 USD a month, alert
  at 80 %, hard stop at 100 %. The script sets it again before anything can spend.
- The CIS task role can already read `aa-llm/dev/anthropic-direct`: no IAM change.

Approved spend (ADR 0009, S263 T-1): a one-time top-up of 50 USD on the Anthropic side, a connection cap of 150 USD a
month. The probe costs under 0.001 USD; the secret about 0.40 USD a month.

> [!CAUTION]
> Do not run the AA-CIS-Infra run-script `db/scripts/aa1002_dev_anthropic_road.py` in apply mode again. It opens
> every stage whose route reaches an Anthropic Converse model, and since migration 335 that includes the T-stages,
> against T-3. Migration 335 already opened the writers.

## Before you start

- The Anthropic Console side (tech lead, browser): a dedicated Dev workspace with a monthly spend limit, the 50 USD
  top-up, and an API key of that workspace saved to a file. Never paste the key into a chat or a command line.
- The API-key archive handed over by the business owner lives outside every repo, in the tech lead's secret folder.
  An agent uses it only after asking the tech lead, and never copies it into a repo or a session folder beyond the
  one mode-600 key file that step 2 shreds.
- The CIS migration 335 is applied on Dev (`shared.schema_versions` has `335`) and the api / worker run the same
  image (`/health` 200).
- An MFA session for `aa365-admin` that lasts the run: `aws sts get-caller-identity --profile aa365-admin`.
- Who runs it: the orchestrating session or the tech lead. Subagents are blocked by
  `.claude/hooks/subagent-guardrails.sh` (AWS write and audited admin writes).

## 1. Check ($0, no write)

```bash
tools/llm/anthropic_key_plug_in.sh --check
```

Expected:

```text
[anthropic-key] account: the CIS account (profile aa365-admin)
[anthropic-key] connection anthropic-direct: kind=anthropic secret=aa-llm/dev/anthropic-direct problems=0 enabled=False budget=150.0 hard_stop=True alert=80
[anthropic-key] secret aa-llm/dev/anthropic-direct does not exist yet
[anthropic-key] check done (no write)
```

Abort when the script stops with `ABORT:`: the line says what is wrong (MFA expired, another account, a connection
that names another secret or has a policy problem). `EXPECTED_ACCOUNT=<acc2 account ID>` adds an exact account check.

## 2. Plug in, probe, switch on (one command)

```bash
tools/llm/anthropic_key_plug_in.sh --apply < /home/nghiep/projects/AA-Ecosys/.tmp-session/anthropic-key.txt  # WRITE
shred -u /home/nghiep/projects/AA-Ecosys/.tmp-session/anthropic-key.txt
```

In this order, stopping at the first failure:

1. Reads the key from stdin and checks its shape (prefix `sk-ant-`, no spaces or extra text, not pasted twice,
   plausible length). The key is never printed and never on a command line; it touches disk only as a mode-600 file
   under `.tmp-session/`, shredded right after the Secrets Manager call.
2. Stores it: `create-secret` the first time, `put-secret-value` (a new version) afterwards.
3. One audited PATCH: `monthly_budget_usd = 150`, `budget_hard_stop = true`, `budget_alert_pct = 80`.
4. Probe: one call of `haiku-5-5` on `anthropic-direct` (at most 16 output tokens) through the admin connection test.
   The test works while the connection is still off, so a bad key never switches anything on.
5. Only when the probe answered: one audited PATCH `enabled = true`.

Expected (token counts, cost and latency vary):

```text
[anthropic-key] key read from stdin (... characters, not shown)
[anthropic-key] secret aa-llm/dev/anthropic-direct: created
[anthropic-key] budget: 150 USD a month, hard stop, alert at 80 % (changed: [...])
[anthropic-key] probe: {'model_key': 'haiku-5-5', 'wire_id': 'claude-haiku-5-5', 'ok': True, 'reply_usable': True, 'error_class': None, 'cost_usd': 1e-05, 'latency_ms': ...}
[anthropic-key] connection anthropic-direct: ON (api now; worker within 5 minutes). ...
```

The api uses the new state at once; the worker within 5 minutes (registry cache).

If the probe fails, the connection stays off and the script prints the class:

| `error_class` | Meaning | Action |
|---|---|---|
| `access_denied` / `credential` | 401 or 403: wrong or revoked key, no permission in the workspace | New key in the Console, run step 2 again (a new secret version) |
| `quota_exhausted` | No credit, or the workspace spend limit is reached | Add credit or raise the limit on the Anthropic side, run step 2 again |
| `throttled` | 429 rate limit or 529 overloaded | Wait a minute, run step 2 again |

## 3. Verify

The ledger row of the probe (read-only, as `cis_app`, through [ECS exec](ecs-exec-s3-mediated.md)):

```sql
SELECT stage, model, provider, account, tokens_in, tokens_out, cost_usd, status, created_at FROM shared.llm_call_log WHERE stage = 'adhoc_conn_test' AND account = 'anthropic-direct' ORDER BY created_at DESC LIMIT 3;
```

Expected: one row, model `haiku-5-5`, provider `anthropic`, cost under 0.001 USD. The audit rows:

```sql
SELECT actor, action, resource_id, created_at FROM acp_shared.audit_log WHERE resource_id = 'anthropic-direct' ORDER BY created_at DESC LIMIT 3;
```

Expected: the budget change, the connection test and the switch, actor `admin:tech-lead` (`AUDIT_ACTOR` sets it). No
row holds the key.

Record each run (a rotation too): update `last_tested`, `tested_where` and `tested_evidence` (the script output and
the two query results, or the Linear comment that holds them) in this page's front-matter.

## Rollback

Switch the connection off (every stage returns to its AWS deployments within 5 minutes; the writers end on the OpenAI
API again):

```bash
ADMIN_SECRET=$(aws secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --query SecretString --output text --profile aa365-admin --region us-west-1)
curl -s -X PATCH https://api-cis.lumiguides.it.com/admin/llm-connections/anthropic-direct -H "X-Admin-Secret: $ADMIN_SECRET" -H "x-admin-role: admin" -H "x-admin-user-id: tech-lead" -H "content-type: application/json" -d '{"enabled": false}'  # WRITE
unset ADMIN_SECRET
```

The Connections tab of `/admin/ai-gateway` has the same switch. The secret can stay: a disabled connection never
reads it. Remove it only when the key is retired:
`aws secretsmanager delete-secret --secret-id aa-llm/dev/anthropic-direct --profile aa365-admin --region us-west-1  # WRITE`
(30-day recovery window).

## Rotate the key

Run step 2 with the new key: it stores a new secret version, probes and leaves the connection on. A cached key lives
up to the credential cache TTL; a 401 drops it at once. Revoke the old key in the Console after the probe answered.
See also the [secret rotation runbook](secret-rotation.md).

## Making the API the first way in for a model

Not part of this procedure, and a tech lead decision per model: lower that model's `anthropic-direct` deployment
priority below 10 (acc3) with a CIS migration (`cis_app` cannot write deployments). Revert: priority back to 100, or
switch the connection off. A stage still reaches the API only when its `allowed_scopes` allow `vendor_direct`.
