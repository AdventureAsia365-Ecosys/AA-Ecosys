# ADR 0009 — AI platform and provider gateway: one gateway for every paid AI and data provider, every app and stage

- **Status:** Proposed (31/10/2026, S261). Uses the number reserved for AA-804 ("AI platform and governance").
- **Scope:** every paid AI or data API called by AA-CIS-App, AA-TripPlanner-Web, AA-Partner (CRM) and AA-Booking (when
  it needs one), on every environment; the AA-CIS-Infra roots that hold their roles, secrets and alarms.
- **Implements:** root ADR 0001 decision 2 ("Single Model Gateway") and decision 4 (cost guard).
- **Amends (on acceptance):** CIS ADR 0006 §5 and CIS ADR 0008 (the writer/judge rule becomes family-based, decision
  12); CIS ADR 0012 (data scopes gain model maker, inference geography and per-provider tenant rules, decision 10);
  root ADR 0001a decisions 1–2 (acc2 may serve chat models for eval, judge and validate stages, decision 14); the S258
  blueprint text "add a connection in ≤30 min, no deploy" (decision 11).
- **Respects, unchanged:** root ADR 0008a §5–6 (the CRM keeps its own gateway, control plane and ledger); CIS ADR 0005
  (catalog, no silent cross-vendor fallback); CIS ADR 0007 (Jev verdicts may act only when enforced and calibrated);
  root ADR 0018 (the LLM account `aa-ai`, invoker role per environment).
- **Design and evidence:** `docs/audits/2026-10-31-S261-ai-gateway-design-v2/README.md` (tech lead summary);
  `docs/audits/2026-10-31-S261-llm-gateway-design-gap/` (gap table, weaknesses D1–D11, critic),
  `docs/audits/2026-10-31-S261-llm-gateway-readiness/`, `docs/audits/2026-10-31-S261-llm-capacity-plan/`, the S261
  paid-provider inventory (code read only), and the approved
  [S258 blueprint](../audits/2026-10-29-S258-aws-org-blueprint/README.md) section "AI / LLM Gateway".
- **Related Linear:** AA-804 (this ADR, ledger v2, AI Use Register), AA-642 (gateway build, shared core S8),
  AA-900 (qualification and evaluation), AA-1002 (S0–S10 as built), AA-820 (tenant AI terms), AA-842 (traces, on
  hold), AA-1004 (organization and SCP).

## Context

The tech lead defined the target on 31/10/2026: the gateway is where every LLM use in the ecosystem is called,
managed, routed, monitored and traced, for all sources and model families, with settings per app and per stage; and
it covers Jev and DataForSEO as well.

What exists (CIS code at `1b6e9448`, S261 audits):

- CIS has a working LLM gateway: a connection → deployment → logical-model registry, stage routes with ordered
  fallbacks and a shadow, data scopes per stage (CIS ADR 0012), a circuit breaker, connection budgets and a nightly
  reconcile against the provider bill. These parts are kept.
- **29/10 outage.** Error 002 blocked every model and region on acc3, the only chat account. `anthropic-direct` was
  disabled with no key and `openai-direct` had no credit, so only about two stages could fail over and every writing
  stage stopped (postmortem `docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md`). Loss of access was
  found by a paid eval run, and refused calls left no ledger row.
- **Providers outside the gateway.** Jev (`decide.py`), DataForSEO (`DataForSEOClient`) and Geoapify
  (`geocoder.py`) each have their own client, configuration (env, Secrets Manager, code constants) and ledger.
  TripPlanner runs a copy of the gateway that reads two of the five registry tables and has no breaker. The CRM
  gateway is a stub. Bedrock Batch and Bedrock Guardrails have no cost row.
- **Five ledgers, five shapes:** `shared.llm_call_log`, `shared.decision_log`, `shared.dfs_call_log`,
  `geo.geocode_call`, `crm.llm_call`. No common record carries app, stage, provider, tenant, job, latency and outcome.
- **Uneven budgets.** `cost_guard` checks only where a caller loads a `RunBudget`: Jev has no pre-call budget, the
  DataForSEO `process_seo` path is unbudgeted, the TripPlanner daily cap fails open, and acc2 chat rows log
  `account=NULL` so they escape the connection budget.
- **Model identity is one field.** `vendor` means maker, host and path at once, under a closed CHECK; `capabilities`
  is never read; request parameters live in call sites; a per-call `model_tier` skips the route.
- **No qualification procedure** for a new model family, and the writer/judge rule checks vendor identity on one side.

## Decisions

### 1. One gateway for every paid AI and data provider

- Every paid call from any app goes through the gateway: LLM generation (all sources and families), embeddings,
  batch inference, Jev decisions, DataForSEO and Geoapify data calls, and Bedrock Guardrails.
- Out of the call path: Mapbox (called from the traveller's browser) is registered for monitoring and usage alerts
  only; free sources (Google Drive, Overpass, FX feeds) are registered as `free` so the registry shows where data
  goes; tenant-owned channels (Facebook, WordPress, agency mail) are not AA spend and stay outside.
- A CI guard in each app forbids a provider SDK or HTTP client outside the gateway adapters (extends CIS
  `test_aa685_no_raw_model_calls.py` to Jev, DataForSEO and Geoapify). Dead clients are deleted, starting with
  CIS `services/acp_produce/dataforseo.py`.

### 2. Registry: provider kind → connection → deployment → logical model or operation

- **Provider kinds:** `bedrock`, `anthropic`, `openai`, `azure_openai`, `typesafe` (Jev), `dataforseo`, `geoapify`,
  `bedrock_guardrails`, `mock`. A new kind needs an adapter (decision 9); a new connection of a known kind does not.
- **Connection** (one way in: account × region, or API endpoint × key): kind, account / region / endpoint, secret
  name (prefix and host allow-list), timeouts and retries, limits (RPM, concurrency, daily credits), data scope,
  monthly budget, balance source, `failure_domain` (the payer and organization that can block it), the roles it may
  serve (writer, judge, validate, embed, decide, data), and lifecycle state.
- **Deployment:** model or operation × connection, with wire id, priority, `api_style`, price overrides, batch
  capability and request defaults.
- Jev, DataForSEO and Geoapify become connections; their thresholds (Jev low credit, DataForSEO balance alert,
  Geoapify daily credits) move from code and env into connection data.

### 3. Model families and capabilities are data

- The logical model gets a `family` (the maker: Anthropic, OpenAI, Amazon, Meta, Moonshot, Cohere, …) from a family
  table; the closed `vendor` CHECK is dropped. The host comes from the connection kind, the path from the deployment.
- Effective capabilities = catalog values + per-deployment override: reasoning mode and control, structured output,
  prompt caching, minimum and maximum output tokens. Behaviour keyed on model-name substrings is removed.
- Lifecycle is data: `access_state`, `last_probe_at`, `eol_date`. Price records are structured (region, inference
  profile, effective date) and change only by migration.

### 4. Profiles per app and per stage, including parameters

- A stage profile = route + parameters + data scopes + budget + kill switch, keyed by app.
- Parameters live in a stage × model table with a fixed precedence: call-site hard limits → stage × model →
  protocol defaults. Every adapter translates them, the Bedrock Converse adapter included.
- An app profile holds the app-wide switches: AI on/off, bulk paused, default budgets, and the degrade mode the app
  shows when AI is unavailable.
- CRM profiles stay in schema `crm` (root ADR 0008a §6) with the same shape.

### 5. Routing with failure domains and a warm independent path

- One dispatch pipeline: route → deployment plan → shared middleware (scope, budget, limiter, breaker, attribution,
  ledger, response contract) → adapter. The legacy chain, the vendor path and the direct OpenAI path are removed,
  each by a dated slice in AA-642. `model_tier` is accepted only in an eval or probe context.
- Order: same model on the next deployment by priority → skip open circuits → next model in the route → typed error.
  One deadline per route; the gateway owns retries (SDK retries off, at most six attempts per chain). No shadow as a
  fallback, no hidden provider-side fallback, no silent cross-family fallback for writer stages.
- **Invariant:** every production stage class has at least one enabled, funded deployment in another failure domain
  that its scopes allow, or a declared degrade mode. CI checks it on the route data; the availability card shows it.
  The independent path is kept warm by the health probes (decision 7).
- `stop_reason = max_tokens` is the error class `truncated`, never a success.

### 6. Budgets at every layer, enforced by the gateway

- Budgets are no longer opt-in per caller. Layers: connection (monthly), app (daily), stage or job kind (per run),
  tenant (monthly, the CRM `ai_budget_usd` pattern extended to Content studio tenants), eval and ad-hoc scopes.
- Every kind gives a pre-call estimate: tokens × price for LLMs, the catalog price per Jev decision, the DataForSEO
  estimate table, Geoapify credits.
- When a budget counter cannot be read, the call fails closed (this removes the TripPlanner fail-open).
- A provider spend-limit refusal (Anthropic workspace limit, OpenAI `insufficient_quota`, Jev 402, DataForSEO
  401/402) is `quota_exhausted`: the connection stops, it is never retried as throttling.

### 7. Health probes, access state and balances

- A scheduled probe per connection × enabled deployment, using the cheapest call or a free endpoint where one exists
  (the DataForSEO balance API). It updates `access_state` and the health table, so loss of access is found before
  real work fails.
- Balance per provider: the real balance API where it exists, otherwise ledger spend against recorded top-ups (Jev)
  or counted credits (Geoapify).
- A connection-level circuit opens all deployments of a blocked account at once. An instant alert fires when a
  production circuit opens or a balance falls under its threshold. Jobs that failed with access denied can be
  re-queued from the admin; job backoff gets jitter. A failover drill runs monthly on Dev.
- A probe that costs money is enabled only after its monthly cost has been stated and the tech lead has said yes.

### 8. One ledger contract and a trace view

- Every external call, including refused and failed attempts (cost 0), writes one row under one column contract:
  app, stage, provider kind, connection, deployment, model or operation, family, tenant, job, request id, attempt,
  outcome, error class, latency, units (tokens in / out / cache / reasoning, credits, tasks), cost and an estimate
  flag, prompt version.
- The shared ledger is `shared.llm_call_log` extended to this contract (ledger v2) for CIS and TripPlanner.
  `decision_log`, `dfs_call_log` and `geo.geocode_call` stay as domain detail, linked to the ledger row by call id.
  `crm.llm_call` follows the same contract with `app = 'crm'` and reaches CIS only through `crm.ops.v1`.
- The CIS admin gets a "paid providers" page (health, balance, spend per app / stage / tenant, latency p50/p95,
  error rate) and a per-job / per-tour trace of calls in time order.
- No prompt or completion text is stored by default (DM-6.4). Prompt capture, if ever needed, is opt-in for
  platform-only `aws_only` stages, in acc2 S3 with a 30-day TTL.

### 9. Adapters per provider kind

- Seams: `generate`, `embed`, `batch`, `decide` (Jev typed questions; `decision_question` off / shadow / enforce
  modes stay), `data` (DataForSEO endpoints, Geoapify geocode and place details) and `guard` (Bedrock ApplyGuardrail).
- Chat adapters: Bedrock Converse, Anthropic Messages, OpenAI Chat / Responses, Azure OpenAI. Each adapter maps
  provider errors to the shared classes, reports units and cost, applies the stage parameters, and never retries on
  its own.

### 10. Data scopes: maker, geography and tenant rules per provider

- CIS ADR 0012 scopes stay and gain, per stage, the allowed model makers and the allowed inference geography
  (in-region, `us.`, `global.`), and per provider a data class (what may be sent: keywords, place names, platform tour
  text, tenant text, scrubbed traveller text).
- The Jev tenant allowlist becomes the general per-provider tenant rule; a tenant stage with no tenant fails closed.
- Tenant and TripPlanner stages use only makers named in the AI register and the tenant terms (AA-820), and no
  `global.` profile until the terms cover it. DM-6.4 and the CRM scrub order (root ADR 0008a §5) are unchanged.
- A scope change happens only by migration.

### 11. Configuration by migration, toggles in the admin

- Connections, deployments, families, prices and scopes are added by a PR and DB Migrate ("plug and play" = one PR
  plus DB Migrate, no code change for a known kind). The admin may only enable or disable, set priority, limits,
  budgets and shadow share, and run Test. Every admin change is audited.

### 12. Qualification ladder for new models and providers; family-based writer/judge rule

- Ladder: disabled and priced row → access probe → contract smoke (under 0.10 USD) → judge calibration → A/B against
  a frozen control → targeted shadow → route switch with a one-edit rollback. Bars: no new hard-fact class,
  deterministic fidelity no worse than the control, cost per tour and p95 latency reported. Every paid step needs the
  tech lead's yes.
- Tours are written in English; quality criteria are English only.
- Writer stages stay on Anthropic models (S1 on Sonnet 5.5) until the ladder shows non-inferiority and an amendment
  of this decision is accepted. The judge's family must differ from the writer's and from both A/B arms, checked at
  call time, in the eval runner and in the harness (amends CIS ADR 0006 §5 and CIS ADR 0008).

### 13. One shared core for all apps

- The gateway core is a vendored library with the CIS control plane (blueprint option a). TripPlanner vendors it and
  reads configuration through a CIS contract (snapshot or endpoint), not by SELECT on registry tables.
- The CRM vendors the code only and keeps its own control plane and ledger in `crm`; it stays Bedrock-only, never
  OpenAI or Jev (root ADR 0008a §5–6, not amended).
- Booking has no AI today; when it needs AI, it goes through CIS jobs (AA-835) or the shared core.
- An HTTP gateway service is reconsidered when three or more apps call it in production or central keys are needed.

### 14. Accounts and failure domains

- acc3 (`aa-ai`) stays the main Bedrock chat account. acc2 may serve chat models for eval, judge and validate stages
  as a second failure domain (different payer), not for main writer or tenant stages until decision 10 and AA-820
  are done. This amends root ADR 0001a decisions 1–2. `account_route` is replaced by the connection's role list.
- The Anthropic API is the warm independent path for Claude stages, funded within its workspace spend limit.
- Each app calls Bedrock through its own invoker role so AWS cost allocation shows the caller (root ADR 0018).

## Consequences

- **Positive:**
  - one place to see and cap every paid AI and data spend, per app, stage and tenant;
  - an account-wide block no longer stops all writing, and it is found by a probe, not by a paid run;
  - new families and providers become data plus a qualification run, not code spread over call sites;
  - one trace per job covers about 80% of what a Langfuse trace gives here, at no infrastructure cost.
- **Negative / cost:**
  - a wider registry and a ledger migration for several schemas; Jev, DataForSEO and Geoapify callers must move;
  - the warm path and paid probes add a small monthly spend, stated and approved before they are enabled;
  - the CRM keeps a second ledger in step with the shared contract;
  - no new AWS resource is created by this ADR (DM-10.7: 0 USD); any later one states its monthly cost first.

## Alternatives considered

- **LiteLLM proxy.** Rejected: a new service and database in the call path; it does not cover Jev, DataForSEO or
  Geoapify; it duplicates our budgets, scopes and reconciled ledger.
- **Langfuse Cloud.** Rejected: prompts and outputs would leave AWS outside CIS ADR 0012, incompatible with the CRM
  (root ADR 0008a) and DM-6.4.
- **Langfuse self-hosted.** Deferred: about 60–150 USD a month, ClickHouse on Fargate, more connections on the shared
  RDS; paid observability is on hold. Reopen with real prod traffic, through the AA-842 OTel exporter, with the ledger
  staying the source of truth for cost.
- **HTTP gateway service now.** Deferred: an extra hop, deploy and availability risk for one main caller today; the
  vendored core keeps the option (decision 13).
- **Keep per-vendor clients and ledgers.** Rejected: it is the source of the uneven budgets and the missing traces.

## Follow-ups

- AA-804: this ADR; ledger v2 columns; AI Use Register lists makers, stages, owners, budgets and kill switches.
- First slice, 0 USD, no route change: acc2 attribution, Anthropic spend-limit class, DataForSEO `process_seo`
  budget, Jev pre-call budget, TripPlanner fail-closed, delete the dead DataForSEO client.
- AA-642: dispatch pipeline and removal dates, legacy aliases, shared core (S8). AA-900: ladder and judge calibration.
  New issues for reliability and model families only with the tech lead's OK.
- On acceptance: pointer lines in CIS ADR 0006, 0008, 0012 (CIS PR) and root ADR 0001a; status here and in the index.
