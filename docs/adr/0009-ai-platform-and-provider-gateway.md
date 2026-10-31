# ADR 0009 — AI platform and provider gateway: one gateway for every paid AI and data provider, every app and stage

- **Status:** **Accepted** for decisions 1–9, 13 and 14 and the UI section (tech lead, 31/10/2026, S261; see
  "Decision record"). **Proposed** for decisions 10, 11 and 12 (proposed answers to gap §5 items 9, 4 and 1 + 7,
  accepted one by one when their step comes). Uses the number reserved for AA-804 ("AI platform and governance").
  "Not decided here" lists what this ADR leaves open.
- **Scope:** every paid AI or data API called by AA-CIS-App, AA-TripPlanner-Web, AA-Partner (CRM) and AA-Booking (when
  it needs one), on every environment; the AA-CIS-Infra roots that hold their roles, secrets and alarms.
- **Implements:** root ADR 0001 decision 4 (cost guard).
- **Amends (each item when the decision it names is Accepted; see Status):**
  - root ADR 0001 decision 2 ("Single Model Gateway": LLM, Jev and embedding, Converse API, acc3 only): the scope widens
    to DataForSEO, Geoapify and Guardrails (decision 1), to other adapters (decision 9) and to acc2 as a second Bedrock
    failure domain (decision 14);
  - root ADR 0001a decisions 1–2 (acc2 may serve chat models for eval, judge and validate stages, decision 14);
  - root ADR 0018, the `aa-ai` row "Bedrock chat models only" and the sentence "ADR 0001a … is unchanged" (decision
    14; a note is added to ADR 0018 in the same PR, both Proposed);
  - root ADR 0008 decision 5, the grandfathered gateway-config SELECT, closed by the contract of decision 13;
  - data standards DM-10.4 (next version): one ledger contract with domain ledgers linked to it, and `role` gains
    `embed`, `decide` and `data` (decisions 2 and 8);
  - CIS ADR 0005 decision 4 (no silent cross-vendor fallback, reworded in decision 5) and decision 9 (TripPlanner and
    AA-Booking read the catalog, replaced by the contract of decision 13);
  - CIS ADR 0006 §4 (`model_tier` runs alone, limited to eval and probe, decision 5) and §5 (vendor-based writer/judge
    rule, decision 12);
  - CIS ADR 0008 decision 1 (the writer/judge rule becomes family-based, decision 12; decision 2 stays);
  - CIS ADR 0012 (data scopes gain model maker, inference geography and per-provider tenant rules, decision 10).
- **Supersedes:** the S258 blueprint text "≈30 minutes, no deploy" (:1183) and checklist A3 (:1316, "Admin ›
  Connections › Add"), decision 11; the blueprint gets a pointer line.
- **Respects, unchanged:** root ADR 0008a §5–6 (the CRM keeps its own gateway, control plane and ledger, Bedrock only);
  CIS ADR 0006 §7 (`SAFE_DEFAULTS` when the whole database cannot be read, decision 6); CIS ADR 0007 (Jev verdicts act
  only when enforced and calibrated; Jev failing never blocks, decision 6).
- **Design and evidence:** `docs/audits/2026-10-31-S261-ai-gateway-design-v2/README.md` (tech lead summary) and
  [`inventory.md`](../audits/2026-10-31-S261-ai-gateway-design-v2/inventory.md) (paid-provider inventory, code read
  only); `docs/audits/2026-10-31-S261-llm-gateway-design-gap/` (gap table, weaknesses D1–D11, §5 decisions, §6
  measurements, critic), `docs/audits/2026-10-31-S261-llm-gateway-readiness/`,
  `docs/audits/2026-10-31-S261-llm-capacity-plan/` (including the approved slice S12: bulk and prod lines, token
  limiter, backpressure in job claim; its only home today is a comment on the closed AA-1002), and the approved
  [S258 blueprint](../audits/2026-10-29-S258-aws-org-blueprint/README.md) section "AI / LLM Gateway".
- **Related Linear:** AA-804 (this ADR, ledger v2, AI Use Register), AA-642 (gateway build, shared core S8),
  AA-900 (qualification and evaluation), AA-1002 (S0–S10 as built), AA-820 (tenant AI terms), AA-842 (traces, on
  hold), AA-1004 (organization and SCP), AA-1016 (tenant AI budget), AA-1015 (TripPlanner limits), AA-964 (CRM
  gateway), AA-896 (alarms).

## Decision record (31/10/2026)

The tech lead answered the three questions of the design summary on 31/10/2026 (S261): yes to all three proposals,
with one addition: "the direct APIs are both Anthropic and OpenAI".

| Question | Answer | Effect in this ADR |
|---|---|---|
| 1. One gateway for every paid AI and data provider (LLM, Jev, DataForSEO, Geoapify, Guardrails), every app and stage | Yes | Decisions 1–4, 6, 8, 9 and 13 Accepted; new issues N1 and N2 are created (Follow-ups) |
| 2. A warm path in another failure domain is mandatory | Yes, and **both** direct APIs (Anthropic and OpenAI) are warm independent paths | Decisions 5 and 7 Accepted: the Anthropic API top-up of 50 USD with its 150 USD/month connection budget, daily probes of every connection on Dev (under 1 USD/month) and the monthly failover drill (about 0.25 USD) are approved. The OpenAI API connection is a warm path too, capped and probed; its top-up amount and monthly cap are stated and approved before any purchase (Follow-ups) |
| 3. acc2 may run chat models for judge and validate stages only; writer stages stay on Claude | Yes | Decision 14 Accepted; writers stay on Claude Sonnet 5.5 (decision 12's writer clause); every acc2 model passes the ladder before going live |

Not covered by the three answers, still Proposed: decision 10 (data scopes per maker and geography), decision 11
(configuration by migration only) and decision 12 (ladder and family-based writer/judge rule, except the writer
clause above).

## Context

The tech lead defined the target on 31/10/2026: the gateway is where every LLM use in the ecosystem is called,
managed, routed, monitored and traced, for all sources and model families, with settings per app and per stage; and
it covers Jev and DataForSEO as well.

What exists (CIS code at `1b6e9448`, S261 audits, [inventory](../audits/2026-10-31-S261-ai-gateway-design-v2/inventory.md)):

- CIS has a working LLM gateway: a connection → deployment → logical-model registry, stage routes with ordered
  fallbacks and a shadow, data scopes per stage (CIS ADR 0012), a circuit breaker, connection budgets and a nightly
  reconcile against the provider bill. These parts are kept. The approved S258 design already covers LLM for CIS,
  TripPlanner and the CRM (through slice S8, blueprint :1228, :1333) and Jev as kind `typesafe` (:1256); it does not
  cover DataForSEO or Geoapify.
- **29/10 outage.** Error 002 blocked every model and region on acc3, the only chat account. `anthropic-direct` was
  disabled with no key and `openai-direct` had no credit, so only about two stages could fail over and every writing
  stage stopped (postmortem `docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md`). Loss of access was
  found by a paid eval run, and refused calls left no ledger row.
- **Providers outside the gateway.** Jev (`decide.py`), DataForSEO (`DataForSEOClient`) and Geoapify
  (`geocoder.py`) each have their own client, configuration (env, Secrets Manager, code constants) and ledger.
  TripPlanner runs a copy of the gateway that reads two of the five registry tables and has no breaker. The CRM
  gateway is a stub. Bedrock Batch (verified by grep: no ledger write in `s1_batch.py`, `s1_batch_ingest_job.py` or
  `bedrock_batch.py`) and Bedrock Guardrails have no cost row. Azure OpenAI is a supported kind with an adapter and no
  connection.
- **Five ledgers, five shapes:** `shared.llm_call_log`, `shared.decision_log`, `shared.dfs_call_log`,
  `geo.geocode_call`, `crm.llm_call`. No common record carries app, stage, provider, tenant, job, latency and outcome.
- **Uneven budgets.** `cost_guard` checks only where a caller loads a `RunBudget`: Jev has no pre-call budget, the
  DataForSEO `process_seo` path is unbudgeted, the TripPlanner daily cap fails open, and an acc2 Converse reply logs
  `account=NULL`, so any acc2 chat spend would escape the connection budget (no stage routes chat to acc2 today).
- **acc2 model access.** acc2 cannot run Claude ("not available for channel program accounts") or GPT on Bedrock; only
  Amazon Nova, Meta Llama 4 (`us.` profiles) and Moonshot Kimi K3 answer (S261 access matrix, 31/10).
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
  CIS `services/acp_produce/dataforseo.py`. The Azure OpenAI adapter is not dead: it stays, with no connection, until a
  second GPT path outside AWS is needed and its cost approved.

### 2. Registry: provider kind → connection → deployment → logical model or operation

- **Provider kinds:** `bedrock`, `anthropic`, `openai`, `azure_openai`, `typesafe` (Jev), `dataforseo`, `geoapify`,
  `bedrock_guardrails`, `mock`. A new kind needs an adapter (decision 9); a new connection of a known kind does not.
  `shared.llm_provider_connection` then holds non-LLM providers too; the build slice renames it
  (`shared.provider_connection`, with a compatibility view) or documents the wider meaning in its table comment.
- **Connection** (one way in: account × region, or API endpoint × key): kind, account / region / endpoint, secret
  name, timeouts and retries, limits (RPM, concurrency, daily credits), data scope, monthly budget, balance source,
  `failure_domain` (the payer and organization that can block it), the roles it may serve (writer, judge, validate,
  embed, decide, data), and lifecycle state.
- **Secret guard per kind.** Each kind has its own secret-name prefix and host allow-list, held as code constants and
  enforced by a CHECK (today `aa-llm/%` for LLM kinds, blueprint :1236). Moving Jev (secret `aa-cis/dev/typesafe`),
  DataForSEO and Geoapify in must not let an editable row read another kind's secret or send it to another host
  (blueprint :1423). Only a migration changes a prefix or allow-list; a secret rename updates
  `docs/security/secrets-register.*` in the same PR.
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
  ledger, response contract) → adapter. The legacy chain, the vendor path and the legacy direct-OpenAI code path in
  `client.py` are removed, each by a dated slice in AA-642, after the "Measure first" count (Follow-ups). The OpenAI
  API itself stays: it is served as the `openai-direct` connection through the OpenAI adapter like any other
  connection. `model_tier` is accepted only in an eval or probe context (amends CIS ADR 0006 §4).
- Order: same model on the next deployment by priority → skip open circuits → next model in the route → typed error.
  One deadline per route; the gateway owns retries (SDK retries off, at most six attempts per chain). No shadow as a
  fallback and no hidden provider-side fallback. No stage falls back across families unless its route lists that model
  explicitly; writer routes list no other family (rewords CIS ADR 0005 decision 4).
- **Invariant:** every production stage class has at least one enabled, funded deployment in another failure domain
  that its scopes allow, or a declared degrade mode. The independent path is kept warm by the health probes
  (decision 7). The warm paths approved on 31/10:
  - writer stages (Claude): acc3 Claude → Anthropic API direct;
  - judge stages (GPT today): acc3 GPT → OpenAI API direct → acc2 Nova / Llama / Kimi, the last only after that model
    passes the decision 12 ladder;
  - validate stages: any enabled model in another failure domain (CIS ADR 0008 decision 2).
  - Tenant (T-series) and TripPlanner writer stages are `aws_only` until AA-820, must stay on Anthropic models
    (decision 12), and acc2 cannot run Claude (decision 14). Their only way to meet the invariant today is a declared
    degrade mode (for example: queue the job and retry later, or show the last saved text).
  - The CI check on route data is report-only on Dev and blocking for prod routes from go-live, so it never turns a
    funding question into a red build. The availability card shows the same result.
- `stop_reason = max_tokens` is the error class `truncated`, never a success.

### 6. Budgets at every layer, enforced by the gateway

- Budgets are no longer opt-in per caller. Layers: connection (monthly), app (daily), stage or job kind (per run),
  tenant (monthly), eval and ad-hoc scopes.
- Tenant layer: the CRM keeps its hard per-agency `ai_budget_usd` (root ADR 0008a). Content studio tenants follow
  AA-1016: an alert at 100% and staff approval from 150%, not a hard stop; the amounts come from the business owner's
  plan prices.
- Every kind gives a pre-call estimate: tokens × price for LLMs, the catalog price per Jev decision, the DataForSEO
  estimate table, Geoapify credits.
- When the database is readable but a budget counter cannot be read, the call fails closed (this removes the
  TripPlanner fail-open). When the whole database cannot be read, CIS ADR 0006 §7 `SAFE_DEFAULTS` still apply.
- A provider spend-limit refusal (Anthropic tier cap 429 `enforced_spend_limit_reached` and our own workspace limit
  400, both documented in S257 `anthropic-api-evaluation.md:164-169`; OpenAI `insufficient_quota`; Jev 402;
  DataForSEO 401/402) is `quota_exhausted`: the connection stops, it is never retried as throttling.
- For `decide`, a budget refusal or `quota_exhausted` is a Jev failure: the stage keeps its existing grey/error rule
  (CIS ADR 0007) and no work is blocked.

### 7. Health probes, access state and balances

- A daily warm probe of each direct API connection, Anthropic (approved capacity plan §5.3) and OpenAI (approved
  31/10). Cost: one call under 0.001 USD (blueprint checklist A4), under 0.03 USD a month per connection.
- Approved 31/10 (review B3, gap :398; design summary, question 2): a scheduled probe per connection × enabled
  deployment, daily on Dev, using the cheapest call or a free endpoint where one exists (the DataForSEO balance API).
  Cost line: under 0.001 USD per call, so under 1 USD a month on Dev while there are at most 30 enabled deployments.
  It updates `access_state` and the health table, so loss of access is found before real work fails. More than 30
  enabled deployments, or probes on prod, state the new monthly cost first.
- Balance per provider: the real balance API where it exists, otherwise ledger spend against recorded top-ups (Jev)
  or counted credits (Geoapify).
- A connection-level circuit opens all deployments of a blocked account at once. An instant alert fires when a
  production circuit opens or a balance falls under its threshold, through the existing admin bell and the operator
  e-mail job (`ops_alert_email`, AA-828): no new service, 0 USD. Jobs that failed with access denied can be re-queued
  from the admin; job backoff gets jitter.
- A failover drill runs monthly on Dev: the primary is switched off and about 3 tours run through the fallback
  (about 0.25 USD a drill at 0.0768 USD a tour, S249 wave). Approved 31/10 at that cost. Each drill covers one
  writer stage failing over to the Anthropic API and one judge stage failing over to the OpenAI API, within the
  route deadline, and reports its cost.

### 8. One ledger contract and a trace view

- Every external call, including refused and failed attempts (cost 0), writes one row under one column contract:
  app, stage, provider kind, connection, deployment, model or operation, family, tenant, job, request id, attempt,
  outcome, error class, latency, units (tokens in / out / cache / reasoning, credits, tasks), cost and an estimate
  flag, prompt version, `prompt_hash`, `is_shadow` and `is_experiment` (the columns root ADR 0008a §6 and AA-804
  promise).
- The shared ledger is `shared.llm_call_log` extended to this contract (ledger v2) for CIS and TripPlanner.
  `decision_log`, `dfs_call_log` and `geo.geocode_call` stay as domain detail, linked to the ledger row by call id.
  `crm.llm_call` follows the same contract with `app = 'crm'` and reaches CIS only through `crm.ops.v1`. This amends
  DM-10.4, which names one ledger per provider and limits `role` to writer, judge and validate.
- Refused attempts now get 0-cost rows, so the 180-day volume of `llm_call_log` grows (AA-825). Every new table
  (family, stage × model parameters, health and probe, eval run) gets its DM-7.1 retention row in the PR that creates
  it.
- The CIS admin gets a "paid providers" page (health, balance, spend per app / stage / tenant, latency p50/p95,
  error rate) and a per-job / per-tour trace of calls in time order.
- No prompt or completion text is stored (DM-6.4). Prompt capture is not decided here (see "Not decided here").

### 9. Adapters per provider kind

- Seams: `generate`, `embed`, `batch`, `decide` (Jev typed questions; `decision_question` off / shadow / enforce
  modes stay), `data` (DataForSEO endpoints, Geoapify geocode and place details) and `guard` (Bedrock ApplyGuardrail).
- Chat adapters: Bedrock Converse, Anthropic Messages, OpenAI Chat / Responses, Azure OpenAI. Each adapter maps
  provider errors to the shared classes, reports units and cost, applies the stage parameters, and never retries on
  its own.

### 10. Data scopes: maker, geography and tenant rules per provider

Proposed answer to gap §5 item 9; accepted separately.

- CIS ADR 0012 scopes stay and gain, per stage, the allowed model makers and the allowed inference geography
  (in-region, `us.`, `global.`), and per provider a data class (what may be sent: keywords, place names, platform tour
  text, tenant text, scrubbed traveller text).
- The Jev tenant allowlist becomes the general per-provider tenant rule; a tenant stage with no tenant fails closed.
- Tenant and TripPlanner stages use only makers named in the AI register and the tenant terms (AA-820), and no
  `global.` profile until the terms cover it. DM-6.4 and the CRM scrub order (root ADR 0008a §5) are unchanged.
- A scope change happens only by migration.

### 11. Configuration by migration, toggles in the admin

Proposed answer to gap §5 item 4; accepted separately. It changes the blueprint target "a new connection in about 30
minutes, no deploy" to "one PR plus DB Migrate".

- Connections, deployments, families, prices and scopes are added by a PR and DB Migrate ("plug and play" = one PR
  plus DB Migrate, no code change for a known kind). The admin may only enable or disable, set priority, limits,
  budgets and shadow share, and run Test. Every admin change is audited.

### 12. Qualification ladder for new models and providers; family-based writer/judge rule

Proposed answer to gap §5 items 1 and 7; accepted separately (it includes about 2 hours of the tech lead's labelling).

- Ladder: disabled and priced row → access probe → contract smoke (under 0.10 USD) → judge calibration (40 items
  labelled by the tech lead, about 2 hours) → A/B against a frozen control → targeted shadow → route switch with a
  one-edit rollback. Bars: no new hard-fact class, deterministic fidelity no worse than the control, cost per tour and
  p95 latency reported. Every paid step needs the tech lead's yes.
- A route switch on a main writer stage needs the tech lead's yes. On judge and validate stages the agent switches
  once the ladder passes and reports after the fact, with the same A/B, cost-per-tour and latency report.
- Tours are written in English; quality criteria are English only. Diacritic fidelity of place names inside English
  text (for example "Hạ Long") stays as a name-fidelity rule (NAME_NOT_IN_SOURCE), not a language rule.
- Writer stages stay on Anthropic models (S1 on Sonnet 5.5) until the ladder shows non-inferiority and an amendment
  of this decision is accepted. The judge's family must differ from the writer's and from both A/B arms, checked at
  call time, in the eval runner and in the harness (amends CIS ADR 0006 §5 and CIS ADR 0008 decision 1).
- What survives from CIS ADR 0008: decision 2 (a validate stage may use any enabled model) stays, and relabelling a
  writer as validate to dodge the rule stays forbidden. Blueprint table 5 (:1279, "judges never Anthropic") still
  holds in practice while writers stay Anthropic.

### 13. One shared core for all apps

- The gateway core is a vendored library with the CIS control plane (blueprint option a).
- TripPlanner vendors it and reads configuration through a versioned contract view in `catalog`
  (`catalog.v_llm_gateway_config_v1`: routes, deployments and prices for TripPlanner stages only), as ADR 0008
  decision 5 requires for new cross-app reads. For the fail-closed rule, TripPlanner reads its own spend through
  `catalog.v_llm_app_spend_today_v1` (today's spend for `app = 'tripplanner'` only); other LLM cost stays behind the
  daily rollup (ADR 0008 N4). The S8 slice then revokes the grandfathered SELECT on `shared.llm_role_config` and
  `shared.llm_model_catalog` (the gateway-config exception in ADR 0008 decision 5); the INSERT on `shared.llm_call_log`
  stays as the standing write exception.
- The CRM vendors the code only and keeps its own control plane and ledger in `crm`; it stays Bedrock-only, never
  OpenAI or Jev (root ADR 0008a §5–6, not amended).
- Booking has no AI today; when it needs AI, it goes through CIS jobs (AA-835) or the shared core.
- An HTTP gateway service is reconsidered when three or more apps call it in production or central keys are needed.

### 14. Accounts and failure domains

- acc3 (`aa-ai`) stays the main Bedrock chat account.
- acc2 (`aa-nonprod`) may serve chat models for eval, judge and validate stages as a second failure domain, never
  for main writer or tenant stages until decision 10 and AA-820 are done. This amends root ADR 0001a decisions 1–2 and
  ADR 0018's `aa-ai` row. The families acc2 can serve today are Amazon Nova, Meta Llama 4 and Moonshot Kimi K3; it
  cannot run Claude or GPT (S261 access matrix). So acc2 cannot back up today's judges (GPT Luna) as they are, and no
  acc2 chat route goes live before its model passes the decision 12 ladder, judge calibration included.
- The same role list applies to `aa-prod` connections when `aa-prod` can call Bedrock (ADR 0018): judge and validate
  stages only, after the ladder passes there.
- "Different payer" is today's fact, not a permanent one: the 01/12 Billing Transfer and the move into the AA
  organization change payer and organization for every account at once (gap :899), and leaving TrueIDC may lock AI on
  acc2 (blueprint :320). Every `failure_domain` value is re-checked at each payer or organization change in the ADR
  0018 timeline, with a probe of every connection before and after.
- `account_route` is replaced by the connection's role list.
- Accepted 31/10 (design summary, question 2): both direct APIs are warm independent paths outside AWS, each capped
  by its connection budget and health-probed daily.
  - **Anthropic API:** the warm path for Claude (writer) stages. Approved: a one-off top-up of 50 USD and the
    connection's monthly budget of 150 USD (the budget is a cap, not money paid in;
    `docs/ops/runbooks/llm-anthropic-api-key.md`).
  - **OpenAI API:** the warm path for GPT (judge) stages, ahead of acc2. Its top-up amount and monthly cap were not
    stated on 31/10; they are stated and approved by the tech lead before any purchase. Until then the connection
    shows "not funded" and the invariant for judge stages is met only by acc2 after its ladder, or not at all.
- Each app calls Bedrock through its own invoker role so AWS cost allocation shows the caller (root ADR 0018).

## UI

Accepted with decisions 1, 2 and 7–8 (31/10). All in the CIS admin nav group "AI & spend", built only from kit
components (root ADR 0016); a new kit component, if any, goes into the CIS canonical `_kit/core` and is synced.

- **New page `/admin/ai-gateway` ("AI providers")**, five tabs:
  - **Providers:** one row per connection (Bedrock acc3 and acc2, Anthropic API, OpenAI API, Azure off, Jev,
    DataForSEO, Geoapify, Guardrails; Mapbox monitor only) with health, access state, failure domain, balance, spend
    against budget, latency p50/p95, error rate, last probe and a Test button. Both direct APIs show as warm paths with
    cap, funding and probe state. Absorbs the settings Connections and Jev credit tabs and the availability card.
  - **Routing:** app × stage profiles (chain, read-only parameters and scope, budget, kill switch, shadow share) with a
    failure-domain badge; the per-stage `account_route` select is removed.
  - **Models & trials:** families and capabilities (read-only except enable), shadow A/B, ladder and calibration.
  - **Budgets:** every layer (connection, app, stage or job kind, tenant, eval) and the cap-coverage list.
  - **Calls:** ledger v2 search; a row opens the **Trace drawer** (every attempt of a job or tour in time order,
    refused attempts included), also opened from the job drawer, tour detail and decisions.
- **`/admin/cost-ops`** becomes the money view: Overview, Forecast, AWS bill, and one "AI & data spend" tab from the
  ledger (the LLM, DataForSEO and Jev tabs merged); Budgets moves to the gateway page.
- **Small edits:** decisions link to ledger and trace; overview shows a "paid providers" summary; platform cost per
  app reads the ledger `app` column; the per-run `model_tier` select leaves `/admin/s1-rewrite`; Tenant 360 gets the
  tenant AI budget (AA-1016); `/admin/settings` loses its models and Jev credit tabs.
- **Rules:** prices, secrets, base URLs and scopes are read-only in the UI (decision 11 when accepted; until then the
  UI simply does not offer them); a route save that breaks the warm-path invariant is refused on prod and reported on
  Dev; view needs `spend.read`, edit needs `ai.admin`; every admin change is audited; old deep links redirect.
- **Net:** one new page, no page deleted, five tabs moved or merged. Only CIS staff see changes; Content studio
  tenants see only the privacy and terms text (AA-820); CRM agencies get their AI settings in CRM web under AA-964;
  TripPlanner travellers may see the basic-narration fallback more often after the fail-closed fix.

## Not decided here

Each item is deferred explicitly; it is brought to the tech lead with a proposed answer when its step comes.

- **Second region (gap §5 item 8).** Proposed: allow us-west-2 for model availability on eval connections only, with
  the SCP allow-list in AA-1004; prod second region only on a trigger (capacity plan §5.2).
- **S1 quality gate freeze (gap §5 item 6).** Proposed: new fidelity rules run as measurements first and are promoted
  once the baseline rate is known.
- **PII step for TripPlanner traffic.** Decision 13 brings traveller `free_text` into the shared core; DM-6.4 is
  review-only. Proposed: reuse the CRM F3 scrub as an optional gateway step for stages flagged `free_text`, gated on
  S8 (gap :1100-1104).
- **Prompt capture.** Not decided; it needs DM-6.4 and DM-7 rows and the tech lead's yes, with its storage cost.

## Consequences

- **Positive:**
  - one place to see and cap every paid AI and data spend, per app, stage and tenant;
  - an account-wide block no longer stops all writing, and it is found by a probe, not by a paid run;
  - new families and providers become data plus a qualification run, not code spread over call sites;
  - one trace per job, built on the ledger, with no infrastructure cost.
- **Negative / cost:**
  - a wider registry and a ledger migration for several schemas; Jev, DataForSEO and Geoapify callers must move;
  - the warm paths, the probes and the monthly drill add a small monthly spend (under about 2 USD on Dev, plus any
    real traffic), approved 31/10, plus the one-off Anthropic top-up of 50 USD; the OpenAI top-up is still to be
    stated and approved;
  - the CRM keeps a second ledger in step with the shared contract;
  - this ADR creates no new AWS resource: alerts use the existing admin bell and operator e-mail, and prompt capture
    is not decided. Any later resource states its monthly cost first (DM-10.7).

## Alternatives considered

- **LiteLLM proxy.** Rejected: a new service and database in the call path; it does not cover Jev, DataForSEO or
  Geoapify; it duplicates our budgets, scopes and reconciled ledger.
- **Langfuse Cloud.** Rejected: prompts and outputs would leave AWS outside CIS ADR 0012, incompatible with the CRM
  (root ADR 0008a) and DM-6.4.
- **Langfuse self-hosted.** Deferred: infrastructure estimated at 60–150 USD a month (not verified; AA-842 audit
  `docs/audits/2026-10-29-S257-aa842-otel/README.md:487`), ClickHouse on Fargate, more connections on the shared RDS;
  paid observability is on hold. Reopen with real prod traffic, through the AA-842 OTel exporter, with the ledger
  staying the source of truth for cost.
- **HTTP gateway service now.** Deferred: an extra hop, deploy and availability risk for one main caller today; the
  vendored core keeps the option (decision 13).
- **Keep per-vendor clients and ledgers.** Rejected: it is the source of the uneven budgets and the missing traces.

## Follow-ups

- **Measure first (0 USD), before D4 and D10:** a `GROUP BY provider, stage` on `llm_call_log` and a count of the
  `model_tier` call sites in use, to see how much traffic the legacy chain, the vendor path, the direct OpenAI path
  and `account_route` still carry. The removal dates in AA-642 follow the counts.
- **Preconditions of any route or family change** (gap §6): Sonnet 5.5 baseline on the frozen S1 control; judge
  calibration on 40 human-labelled items; a cross-path canary of `s1_generate` on anthropic-direct (about 5 items);
  a contract smoke per candidate (3 calls).
- AA-804: this ADR; ledger v2 columns; the AI Use Register lists makers, stages, owners, budgets and kill switches,
  including the CRM stages fed from `crm.ops.v1` (root ADR 0008a §6); data standards DM-10.4 amendment (next version)
  and the DM-7.1 retention rows.
- First slice, 0 USD, no route change: acc2 attribution, Anthropic spend-limit class (fixture from the documented
  error body), DataForSEO `process_seo` budget, Jev pre-call budget, TripPlanner fail-closed, delete the dead
  DataForSEO client.
- AA-642: dispatch pipeline and removal dates, legacy aliases, shared core (S8), and S12 (bulk and prod lines, token
  limiter, backpressure in job claim). AA-900: ladder and judge calibration. AA-1016: Content studio tenant budget.
  Two new issues, since question 1 is yes: N1 "Reliability: warm Anthropic + OpenAI paths, probes, circuit,
  re-queue, monthly drill" (step 5) and N2 "Registry v2: provider kinds, model families, stage × model params,
  routing UI" (step 4). The full issue plan is in the design summary, section "Issue".
- State the OpenAI API top-up amount and monthly cap for the tech lead's yes before buying (decision 14).
- Fix the AA-804 Linear title, which still says "0006".
- On acceptance, pointer lines in: root ADR 0001 (header), 0001a, 0008 decision 5, 0008a §6 (its text "ADR 0009 is
  reserved and not written yet") and 0018; CIS ADR 0005, 0006, 0007, 0008 and 0012 (its header says "not written
  yet") in a CIS PR; the S258 blueprint (:1183, :1316); status here and in the index.
