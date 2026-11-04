---
id: ARCH-01-ai-gateway
title: AI gateway (as built)
description: How every paid AI and data call of the ecosystem is configured, routed, guarded, metered and observed today (root ADR 0009, gateway v2), with a live / planned table checked on 2026-11-01 and refreshed on 2026-11-03.
type: explanation
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem, aa-cis-api, aa-cis-worker, tripplanner-lambda, aa-crm-api]
last_reviewed: 2026-11-04
review_every_days: 30
related: [ARCH-01, ARCH-01-diagrams, APP-06-ai-register, APP-06-routes, ARCH-08, docs/adr/0009-ai-platform-and-provider-gateway.md, AA-642, AA-804, AA-1002, AA-1016, AA-1017, AA-1018, AA-1042]
---

# AI gateway (as built)

> **Status:** as built on 2026-11-01 (S263), refreshed on 2026-11-03 (S265). Applied on Dev on 2026-11-03, read from
> each API's `/health/ready`: CIS every migration through 346 except the held contract file 336, TripPlanner tp-023 and
> CRM crm-040. Live facts of 2026-11-01: ECS task definitions, the Secrets Manager secret names (names only), the
> Bedrock guardrail list. The live checks of the S264 slices (340, 342, 343, 345) are in the S264 session log. The
> decisions behind this page are in [ADR 0009](../adr/0009-ai-platform-and-provider-gateway.md); this page says what
> of them runs today. The full stage list is the [AI Use Register](ai-use-register.md); the current routes are in
> [`generated/llm-routes.md`](../generated/llm-routes.md) (snapshot of 2026-11-02T11:35Z: 40 stages, 20 models).

## 1. What the gateway is

One gateway handles every paid AI and data call of the ecosystem. It is not a service in the call path: it is a
library plus a control plane.

- **The control plane lives in CIS.** Its tables in schema `shared` hold the provider registry, the routes per stage,
  the data scopes, the budgets, the circuit state and the ledger. The CIS admin page **AI providers**
  (`/admin/ai-gateway`) shows and edits what may be edited.
- **The call path runs inside each app.** CIS calls it as `shared/llm_client/`. TripPlanner and the CRM vendor the
  pure core `aa_llm` (standard library only) as a byte copy and keep their own adapters.
- **Every attempt writes one ledger row**, including refused and failed attempts at 0 USD. The ledger is the source of
  truth for cost, latency and outcome.

| Caller | How it calls | Config it reads | Ledger it writes |
|---|---|---|---|
| CIS (api + `shared.job` worker) | `LLMClient.generate(stage=…)`, `embed(stage, texts)`, plus the Jev, DataForSEO and Geoapify clients that read their registry rows | `shared.*` registry tables directly | `shared.llm_call_log` (ledger v2, `app = 'cis'`), plus the domain ledgers `decision_log`, `dfs_call_log`, `geo.geocode_call` |
| TripPlanner (browse, assembly, jobs Lambdas) | `backend/shared/llm_gateway.py` on the vendored core `backend/aa_llm/` | `catalog.v_llm_gateway_config_v1`, `catalog.v_llm_app_spend_today_v1` (CIS 323), `catalog.v_llm_app_profile_v1` (CIS 347) | `shared.llm_call_log` (INSERT only, `app = 'tripplanner'`) |
| AA-Partner CRM (api + `crm.job` worker) | the CRM gateway on the vendored core `app/aa_llm/` | its own control plane in schema `crm` (root ADR 0008a §6) | `crm.llm_call` (ledger v2 shape, `app = 'crm'`, crm-032); CIS sees it only through `crm.ops.v1` |
| AA-Booking | no AI call today | — | — (any future AI goes through CIS jobs or the shared core, ADR 0009 decision 13) |

## 2. Diagram

Solid lines are live on Dev; dashed lines are built but switched off, or planned.

```mermaid
flowchart LR
  subgraph Apps[Callers]
    CIS[CIS api + worker]
    TP[TripPlanner Lambdas]
    CRM[AA-Partner CRM]
    BK[AA-Booking: no AI]
  end
  subgraph Core[Gateway code]
    LLMC[CIS shared/llm_client]
    CORE[aa_llm core: errors, pricing, ledger row, budget rules]
  end
  subgraph CP[CIS control plane, schema shared]
    REG[Registry v2: kinds, connections, deployments, families, stage x model params]
    RT[Routes per stage: chain, data scopes, deadline, shadow]
    POL[Guards: connection, app, job, tenant budgets; circuit; limiter]
    LED[Ledger v2: llm_call_log + domain ledgers]
    VIEWS[catalog contract views 323]
  end
  subgraph Prov[Providers and failure domains]
    B3[Bedrock acc3: main chat account]
    B2E[Bedrock acc2: embeddings]
    B2C[Bedrock acc2: Nova Lite, Llama 4 Scout and Maverick as judge and validate fallbacks]
    GR[Bedrock Guardrails acc2: CRM scrub]
    OA[OpenAI API: last rung of judge and writer routes]
    AN[Anthropic API: no key]
    JEV[Jev decisions]
    DFS[DataForSEO]
    GEO[Geoapify]
  end
  OBS[AI providers page, probe, bell + ops e-mail, nightly reconcile]
  CIS --> LLMC
  TP --> CORE
  CRM --> CORE
  BK -.-> LLMC
  LLMC --> REG & RT & POL
  CORE --> VIEWS
  VIEWS --> RT
  LLMC --> B3 & B2E & B2C & OA & JEV & DFS & GEO
  LLMC -.-> AN
  TP --> B3 & B2E
  CRM --> GR
  CRM -.-> B3
  LLMC --> LED
  TP --> LED
  LED --> OBS
  POL --> OBS
```

The AWS-icon deployment views of each app are in the [architecture diagrams](diagrams/README.md).

## 3. Registry v2

Migrations 304, 306, 307, 320 and 322 (AA-1002, AA-1017).

- **Provider kinds:** `bedrock`, `anthropic`, `openai`, `azure_openai`, `mock` (LLM kinds) and `typesafe` (Jev),
  `dataforseo`, `geoapify`, `bedrock_guardrails` (provider kinds). The LLM dispatch never sees a provider kind.
- **Connection** (`shared.llm_provider_connection`): one way in (an account and region, or an API endpoint and a
  secret name). It carries timeouts, retries, limits (`max_concurrency`, `rpm_limit`, `daily_credit_limit`), a
  monthly budget, `data_scope` (`aws_only` or `vendor_direct`), `failure_domain`, `served_roles`, `access_state`,
  `last_probe_at`, `balance_source` and `low_balance_usd`.
- **Secret guard per kind:** LLM kinds accept only secret names under `aa-llm/<env>/`, provider kinds only
  `aa-cis/<env>/<kind>`, and each kind has a host allow-list. Both are code constants and CHECK constraints.
- **Deployment** (`shared.llm_model_deployment`): a catalog model on a connection, with wire id, priority,
  `api_style`, price overrides and request defaults.
- **Model family** (`shared.llm_model_family`): the maker (Anthropic, OpenAI, Amazon, Meta, Moonshot, Cohere, Jev).
  Catalog rows carry `family` and `capabilities` read as data (prompt cache, forced tool choice, cache minimum,
  default effort).
- **Stage × model parameters** (`shared.stage_model_params`): max tokens, minimum output tokens, temperature, effort
  and reasoning mode. Precedence: call site, then the row, then the protocol default. With no row a request is
  unchanged. TripPlanner reads the row through the `stage_params` column of `catalog.v_llm_gateway_config_v1` (CIS
  350, AA-1027 E4) and applies temperature (when the catalog says the model takes one); its call sites always set max
  tokens, which wins. It sends no effort or reasoning field: every TripPlanner call goes to Bedrock, and, as in CIS
  (effort only on the Anthropic Messages API), the field is added on Bedrock only after a probe shows it is accepted.
- **Edits:** secret names, base URLs and catalog prices change only by migration (322 revoked the runtime role's
  UPDATE on them). The admin may switch a connection on or off and edit limits, budgets and notes; each change is
  audited. Migration 324 proved "add a model = one migration PR": five acc2 chat models with one enabled acc2
  deployment each and no route. Migrations 331–333 and 339 then made three of them route fallbacks (§8).

## 4. Routing

- **Route per stage** (`shared.llm_role_config`): a primary model, ordered fallbacks, an optional shadow at a sample
  rate, `allowed_scopes` (migration-only, AA-1002 S5), `route_deadline_s` (320; set by role in 334: writer 1200 s,
  judge 900 s, validate 600 s, embed 120 s) and the stage kill switch with its declared degrade mode (326).
- **Order of attempts:** set by the **order mode** (`shared.llm_route_settings.order_mode`, CIS 370; the env var
  `LLM_ROUTE_AWS_FIRST` is only the start-up default while that row cannot be read):
  - `model_first` (the default, tech lead S267, ADR 0009 decision 5 amendment): every deployment of a model, in its
    **provider order** (`shared.llm_model_deployment.priority`, lowest first), then the next model of the route;
  - `aws_first`: every AWS deployment of every model of the route, then the vendor API deployments.
  Open circuits, connections over budget and switched-off rows are skipped; after the last rung, or after six attempts
  in all (`errors.MAX_CHAIN_ATTEMPTS`), a typed error. A route lists every model it may use; nothing falls back
  silently across families.
- **Legacy keys:** since migration 327 no route names `haiku` or `sonnet`: every stage moved to the Converse keys of
  the same tier (`haiku-5-5`, `sonnet-5-5`). The catalog rows stay; a caller that still passes a legacy key reaches
  acc3 through the legacy chain, inside the breaker since AA-1018 part 2, and logs `llm_deprecated_path_used`
  (proposed removal 2026-12-31). The aliases of 307 stay off.
- **Data scopes** (CIS ADR 0012): a stage's content may use only connections whose `data_scope` its
  `allowed_scopes` lists. The Anthropic and OpenAI API connections are `vendor_direct`. The A-series writers (327) and
  the six tenant writers (344) allow `{aws_only, vendor_direct}` with the OpenAI API model `gpt-6-luna-openai` as the
  last fallback, so they leave AWS only when every AWS path is blocked; the TripPlanner, segment research and CRM
  stages stay `aws_only`.

### 4.1 Route control (admin, no deploy)

The admin page AI providers › **Route control** (`/admin/ai-gateway?tab=controls`, AA-1042, CIS 370) changes routing
without a deploy. The gateway picks a change up within about 20 seconds (each process re-reads the settings row every
20 s and drops its route caches when the version number moves).

- **What it edits:** the order mode, the chain of every stage (primary and fallbacks, drag and drop) and the provider
  order of every model with more than one deployment.
- **Presets:** "Prefer Anthropic API for Claude (sponsored)" puts the Anthropic API deployment of every Claude model
  first and sets the order mode to `model_first`; "Prefer AWS" puts the AWS deployments of every model first. Presets
  never change a chain.
- **Preview before saving:** the server walks every active stage with the proposed config (the same $0 resolver as
  `scripts/llm_ops/route_chain_check.py`, no model call) and returns the model and provider that would serve first,
  next to the one in force.
- **Rules on every save, preview, preset and revert (server side):** a selectable model for the stage (family rule,
  catalog, data scopes); a model reached only through a vendor API stays at the end of a chain or right behind the same
  model on AWS; a judge never of the writers' family; the two sides of a check pair on different makers; at most six
  attempts per request; every active stage keeps a model that would be called now. A rule the live config already
  breaks is a warning, not an error. A writer or judge chain change needs an eval run or a break-glass reason (the
  break glass raises an admin bell).
- **Versions:** every route change, the Routing tab's own edits included, is a row of
  `shared.llm_route_config_version` with who, when, the action (save, preset, revert, baseline, external), a note, the
  snapshot (order mode, chains, priorities) and the diff. A change made outside the admin (a migration) is recorded as
  an `external` version before the next admin change. Revert restores an earlier snapshot as a new version, audited
  in `acp_shared.audit_log`. Shadows, the stage switch, data scopes and caps keep their own controls and are not part
  of a version.
- **On every call:** each CIS ledger row carries `route_config_version`, the version in force when it was written
  (a BEFORE INSERT trigger; TripPlanner rows stay NULL). Within the 20 s after a change a row may name the new version
  for a call routed by the previous one.
- **Who:** reads need `spend.read`; preview and every write need `ai.admin` (admin and ai_ops). A reader sees the
  routes, presets and versions with no control.

## 5. Guards

| Guard | Where | Rule |
|---|---|---|
| Connection budget | `connection_budget.py`, policy `shared.llm_connection_cost_policy` (317) | Month-to-date ledger spend of the connection; alert at 80 %, hard stop at 100 % of `monthly_budget_usd` by default |
| App budget | TripPlanner: the `default_daily_budget_usd` of its app profile (CIS 347 `catalog.v_llm_app_profile_v1`, every `tp_*` stage) when set, else `TP_DAILY_SPEND_CAP_USD` (5 USD on Dev, online stages); spend through `catalog.v_llm_app_spend_today_v1`; CIS ops check `llm_spend_alert.tripplanner.near/cap` (bell + e-mail). CRM: `crm.llm_app_profile` (crm-041, every agency together, written by the CIS admin over crm.ops.v1 1.10); CRM ops checks `llm_app_spend_near` / `llm_app_spend_cap` (e-mail on the platform alerts topic, no CIS bell: CIS does not read the CRM ledger) | Fails closed when the spend cannot be read |
| Job and stage budget | `shared.spend_budget`, `cost_guard.RunBudget` | Jev and DataForSEO caps seeded by 318 |
| App profile | `shared.llm_app_profile` (345), `app_profile.py` (AA-1025 H1a, ADR 0009 decision 4) | One row per app: AI on / off, bulk paused, default daily budget, degrade mode. AI off for `cis`: every CIS AI call (chat, embed, connection test, Jev) is refused before it is sent, a 0 USD `refused` / `disabled` row; jobs wait for the re-queue. No row or unreadable = AI on. TripPlanner (H1b) reads its row through `catalog.v_llm_app_profile_v1` (CIS 347, 20 s cache): AI off = a 0 USD refused row, basic narration and keyword search. The CRM (H1c) keeps its copy in `crm.llm_app_profile` (crm-041), written by the CIS admin over crm.ops.v1 1.10 before the CIS row: AI off = `app_disabled` at 0 USD, "reply by hand" |
| Tenant budget | `shared.tenant_ai_budget` (321), `tenant_budget.py` (AA-1016) | Bell + ops e-mail at `alert_pct`; with `hard_stop`, T-stage jobs stop `stopped_budget` at `approval_pct` and wait for staff approval, then the bulk re-queue. No row = no budget. The CRM keeps its own hard per-agency monthly budget, alerts at 75 / 90 / 100 % (crm-032), capped by `AI_BUDGET_MAX_USD` |
| Circuit breaker | `breaker.py`, `shared.llm_provider_health` (309) | One circuit per deployment, shared across tasks; a connection-level circuit derived from it trips on account-wide signals (one `credential` or `quota_exhausted`, or `access_denied` on two models) |
| Limiter | per process | `max_concurrency` and `rpm_limit` of the connection |
| Capacity (TPM, lines, backpressure) | `shared.llm_capacity_limit` (348), `shared.rerun_wave` pause columns (349), `capacity.py` (AA-1025 H2, capacity S12) | A call is `prod`, `bulk` (waves, catalogue backfills) or `dev` (ad-hoc, eval, probes). Its tokens (prompt / 4 + `max_tokens`) are reserved on the TPM limit of the connection and of the model, per process; a call that does not fit waits (prod 65 s, bulk 180 s), bulk holds at most `bulk_pct` and waits while prod waits. A `prod_guard` circuit open: the worker postpones LLM job claims and pauses the open waves (one bell each) until it closes; the app profile's bulk pause does the same for bulk. No row = no limit, no hold |
| PII scrub | CRM F3 scrubber (crm-009): known values, regex, then Bedrock Guardrails | Fails closed; the guardrail call is a ledger row with role `guard` |

A provider spend-limit refusal (Anthropic tier cap, OpenAI `insufficient_quota`, Jev 402, DataForSEO 401/402) is the
error class `quota_exhausted`: the connection stops and the call is never retried as throttling.

## 6. Ledger v2 and observation

- **One row per attempt** (319, AA-804): app, stage, provider kind, connection, deployment wire id, model, family,
  tenant, job, request id, attempt number, status (`ok`, `refused`, `error`, `truncated`, `billed_unusable`),
  error class, latency, tokens (in, out, cache read, cache write, reasoning), units, cost, pricing mode,
  `prompt_hash` (sha256 of the system prompt), `prompt_version`, `is_shadow`, `is_experiment`. No prompt or completion
  text is stored (DM-6.4). Bedrock Batch records and Jev calls (role `decide` since AA-1025 D3) write rows too.
- **Read federated** (ADR 0009 decision 8 as amended in S264, DM-10.4): DataForSEO and Geoapify keep their domain
  ledgers (`shared.dfs_call_log`, `geo.geocode_call`) with the contract's status, latency, app and stage (CIS 319 /
  346); Jev's per-question verdicts stay in `shared.decision_log`. The Calls tab, the trace and Providers read every
  ledger side by side; nothing is copied into one table.
- **CIS admin, AI providers** (`/admin/ai-gateway`): tabs Providers (connections, Jev credit, availability),
  Routing, Route control (order mode, presets, chains, provider order, versions; §4.1), Models & trials (families,
  shadow report, the read-only Experiments section), Budgets (every cap layer, tenant budgets), Calls (ledger search)
  and Guide; the **Trace drawer** shows every attempt of a job or tour in time
  order. **Cost Operations** (`/admin/cost-ops`) holds the money view, with the "AI & data spend" tab built from the
  ledger.
- **Daily probe:** job kind `llm_connection_probe`, one small Test call per enabled text deployment (at most 30), daily
  from 05:00 UTC. It is **on** on Dev (`LLM_DAILY_PROBE=on` on the CIS api and worker, Infra #574). Each probe writes
  `access_state` and `last_probe_at`.
- **Alerts:** when a connection circuit opens, one admin bell and one ops e-mail (`llm_circuit_open`, provider text
  masked of ARNs and account IDs); budget alerts use the same bell and e-mail.
- **Route trace** (AA-1042): every row of one gateway request carries the same `quality_signal.route_trace` (the
  answered row also `route_position`; no ledger column). AI gateway › **Trace** shows, per stage, the share of
  answered requests per rung (primary = the first model on its first provider; any later model or provider =
  fallback), the requests with every attempt (reason, error class, latency, cost; a Calls row links to it) and the
  content a fallback model wrote. `POST /admin/ai-gateway/route-trace/test` sends 1-6 tiny real requests on one stage,
  optionally refusing its first model for those requests only (no breaker or circuit change): the live check.
- **Route alerts** (AA-1042): job kind `llm_route_watch` on `shared.job` every 15 minutes, queued by the api's ops
  sampler, and a daily digest from 01:00 UTC; bell + at most one e-mail per alert and UTC day: fallback share above
  the stage's threshold, the last model of a route reached, the first model back after a fallback alert, fallback
  answers costing more than the primary would have (24 h). Thresholds per stage (or `*` defaults) in
  `shared.llm_route_policy` (CIS 371), edited on the Trace tab; defaults 20 % of at least 5 requests, 1 USD.
- **Quality guard** (AA-1042): content whose writer was answered by a fallback model is marked in QA (degraded entry
  `fallback_writer`, admin only); with the stage's `hold_fallback_writes` on, A1 / T2 output is held for review
  (`DEGRADED_DETECTOR`) and a T9 piece gets the admin-only held label (the tenant still receives it). Off by default.
- **Re-queue:** `POST /admin/job-runner/jobs/retry-llm-denied` re-queues failed jobs refused with
  `llm_access_denied` (or held with `tenant_ai_budget_approval`) once their connection answers again; dry run by
  default, at most 50 per apply.
- **Nightly reconcile:** job kind `llm_cost_reconcile` compares logged cost with the provider's figure per connection
  and day (Bedrock from the stored Cost Explorer snapshot).
- **Failure-domain invariant:** report-only on Dev (`invariant.py`, in `/admin/llm-availability` and the OPS-12
  digest): every stage class should have an enabled, funded deployment in another failure domain, or a declared
  degrade mode.

## 7. Shared core `aa_llm`

- Canonical source: AA-CIS-App `shared/aa_llm/` (AA-642 S8): error classes, pricing (`quote` with the catalog passed
  in), the ledger v2 row and its INSERT, the budget decision, and the 323 contract SELECTs. Standard library only, so a
  byte copy runs in every app.
- Copies: TripPlanner `backend/aa_llm/` and AA-Partner `app/aa_llm/`, each pinned by a lock file with the manifest
  hash. Nobody edits a copy: a change merges in CIS, then the **Llm Core Sync** bot opens the consumer PRs
  (root wrapper `tools/llm-core/llm-core-sync.sh`). A parity test in CIS pins `shared/llm_client` and the core to the
  same results.

## 8. Live and planned

Checked on 2026-11-01 and refreshed on 2026-11-03 (the `/health/ready` reads, the route snapshot of 2026-11-02 and the
S264 live checks), unless the row says otherwise.

| Item | State | Evidence or next step |
|---|---|---|
| Ledger v2 (319), registry v2 (320, 322), tenant budget and prompt register tables (321), contract views (323, routing facts and circuit state appended by 341), acc2 candidates (324) | **Live** on Dev | CIS `/health/ready` `schema_version` 346 on 2026-11-03 |
| Circuit breaker, connection circuit, alerts, route deadlines, re-queue | **Live**; every route has a deadline by role (334) | AA-1002 S4, AA-1018, AA-1024 |
| Stage kill switch and degrade mode (326), central LLM budgets in `shared.spend_budget` (340) | **Live** | 340: the `llm/app:cis` cap alerts only (S264 live check) |
| Shared circuit of Jev, DataForSEO and Geoapify (342); credit ledger and low-credit alert of the direct APIs (342, 343) | **Live** | S264 live checks (bell + e-mail, circuit closed after 60 s) |
| Daily probe of every enabled connection | **Live**, on | `LLM_DAILY_PROBE=on` in the CIS api and worker task definitions |
| acc3 Bedrock (main chat account) | **Refusing** since 2026-10-29 (Error 002, every model); the connection circuit and the probe show it | Provider case open; [postmortem](../ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md) |
| acc2 Bedrock embeddings (Cohere Embed v4) | **Live** | Used by CIS and TripPlanner search |
| acc2 Bedrock candidate chat models (Nova Lite, Nova 2 Lite, Llama 4 Maverick, Llama 4 Scout, Kimi K3) | **Fallbacks of judge and validate routes, never of a writer:** Nova Lite on the platform (331) and tenant (332) judge / validate stages and before the OpenAI hop of the judge routes (333); Llama 4 Scout for the place card check; Llama 4 Maverick for `a3_place_dedupe` (339). Nova 2 Lite and Kimi K3 are on no route | Format checked per stage by the contract smoke (CIS job `llm_contract_smoke`) before each change; judge calibration and A/B of the ladder (ADR 0009 decision 12, AA-900) skipped by the S263 amendment of decision 14, so a brand audit `pass` answered on acc2 is held as `manual_check` (`BRAND_AUDIT_UNCALIBRATED_JUDGE`) |
| OpenAI API (`openai-direct`) | Key present (`aa-cis/dev/openai-key`); **last rung** of most judge routes, `a3_place_dedupe`, the A-series writers (327) and the six tenant writers (344); monthly budget 10 USD, alert at 80 %, hard stop (327) | While acc3 refuses, tenant writing runs on it (a live `t9_write` answered through it on 2026-11-02); balance from the credit ledger (343) |
| Anthropic API (`anthropic-direct`) | **Not live:** no `aa-llm/` secret exists; deployments seeded behind acc3 (306) with the connection off | The tech lead creates the key with a workspace spend limit; then the secret is stored and the connection switched on (runbook [llm-anthropic-api-key](../ops/runbooks/llm-anthropic-api-key.md)) |
| Jev, DataForSEO, Geoapify as registry rows (322) with ledger rows | **Live** | Settings come from their rows, else env, else the old constants |
| Bedrock Guardrails | **Live for the CRM scrub** (guardrail `aa-crm-dev-scrub`); the CIS registry row is seeded off | — |
| TripPlanner on the shared core and the 323 views | **Live**; since AA-1027 E5 it reads the views only and fails closed (no table fallback) | CIS 351 revokes the grandfathered SELECT on `shared.llm_role_config` / `llm_model_catalog`; tp-024 drops `tripplanner.llm_spend_daily` |
| CRM gateway v2 (crm-032 ledger, vendored core) | **Live, stub provider:** no `CRM_LLM_*` variable is set on Dev, so CRM AI drafting runs the deterministic stub | Real provider needs `CRM_LLM_PROVIDER` and the role, Bedrock only (root ADR 0008a) |
| Tenant AI budget (Content studio) | **Live** (code and table); a tenant without a row has no budget | Amounts come from the business owner's plan prices |
| App profile (345) and the geocode ledger columns (346) | **Live** in CIS (AA-1025 D3 / H1a, S264); TripPlanner and the CRM read their row later (H1b / H1c) | S264 live check: AI off for `cis`, one connection test refused at 0 USD, AI back on; all four apps `ai_enabled = true` at the close |
| Capacity S12: TPM limiter, request lines, claim backpressure, wave pause (348, 349) | **Built** (AA-1025 H2, S265); no limit row and no prod guard are seeded, so Dev behaves as before | Live drill at 0 USD: `scripts/aa1025_h2_tpm_drill.py` in CIS (a low TPM row on a drill model key: request N+1 waits about 60 s, no error); the tech lead sets real rows from the Service Quotas numbers |
| Retire the dead routes `s1_atom_writer`, `tp_extract`, `tp_component_embed` (336) | **Held** (contract file; its 30-day guard allows it from 2026-11-10) | Applied by hand with DB Migrate, then `DB_AUTO_APPLY_CONTRACT` back on |
| App profile in TripPlanner and the CRM, TripPlanner spend bell (CIS 347, crm-041) | **Built** (AA-1025 H1b / H1c, S265); live once 347 / crm-041 are applied and the three code PRs are deployed | Live check: AI off for `tripplanner` (a search answers the keyword ranking, a 0 USD refused row) and for `crm` (an AI draft answers `app_disabled`); a TripPlanner budget at or under today's spend rings `llm_spend_alert.tripplanner.cap`; a CRM budget at or under today's CRM spend mails `llm_app_spend_cap` within one sampler tick |
| Prompt register | Table live; until a migration registers versions, `prompt_version` is NULL | A migration inserts the first versions (`scripts/prompt_registry_check.py --sql`) |
| Stage × model parameters | Table live, no rows at its release (AA-1017) | Filled when a trial needs it |
| Legacy keys and aliases (`LLM_LEGACY_ALIASES`) | No route names a legacy key (327); aliases **off** | Legacy paths proposed for removal 2026-12-31 |
| Warm independent path per stage class (decision 5 invariant) | A-series and tenant writers: met through the OpenAI API last rung (327, 344). TripPlanner `tp_compose` and segment research: acc3 only, covered by their declared degrade modes (TripPlanner `basic_narration`, 326; segment research `queue_retry`, 335) | A Claude warm path still needs the Anthropic key |
| Route control: order mode in the DB, provider order, presets, preview, versions with revert, route version on the ledger (CIS 370) | **Built** (AA-1042, S268); live once 370 is applied and the code PR deployed | Live check: Route control tab shows version 1 (baseline); a preview of "Prefer AWS" lists the provider-order diff; `llm_call_log.route_config_version` is set on new CIS rows. The retired `gpt-4.1` deployment is switched off by 370 (the daily probe stops calling it) |
| Monthly failover drill | **Not scheduled** | Starts once both direct APIs are funded |
| Second region for eval connections | Not decided | ADR 0009 "Not decided here" |
| HTTP gateway service | Deferred | Reconsidered when three apps call it in production (decision 13) |

## 9. Where to change what

| Change | How |
|---|---|
| A new model on a known provider kind | One migration PR in CIS: catalog row with price and family, a deployment, no route (the 324 pattern), then the qualification ladder |
| A route, a provider order or the order mode | Admin AI providers › Route control (previewed, checked by the server, versioned, revertible; §4.1) or Routing for one stage; a writer route needs the tech lead's yes |
| Undo a route change | Admin AI providers › Route control › Versions › Revert (a new version; the history keeps every step) |
| A secret name, base URL, price or data scope | Migration only |
| A budget or limit | Admin AI providers › Budgets or the connection drawer (audited) |
| The shared core | CIS `shared/aa_llm/`, then the Llm Core Sync PRs in TripPlanner and AA-Partner |
| A new provider kind | An adapter in code plus a migration (ADR 0009 decision 9) |

## 10. Sources

- Decisions: [ADR 0009](../adr/0009-ai-platform-and-provider-gateway.md), CIS ADR 0005, 0006, 0008 and 0012, root
  ADR 0008a §5–6 (CRM).
- Implementation notes in AA-CIS-App `docs/implementation-notes/`: `AA-1002.md` (slices S1–S10), `AA-804-ledger-v2.md`,
  `AA-1017.md`, `AA-1017-w4a-mig324.md`, `AA-1018.md`, `AA-642-s8.md`.
- Repo context: AA-CIS-App, AA-TripPlanner-Web and AA-Partner `CONTEXT.md` (sections on the AI gateway).
- Column names: [`db-schema-reference.md`](db-schema-reference.md).
