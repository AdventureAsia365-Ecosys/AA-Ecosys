---
id: APP-06-ai-register
title: "AI Use Register"
description: "Every AI and paid-data stage of the ecosystem with its owner role, provider, data scope, budget, kill switch, eval and human gate, and the OWASP LLM Top 10 (2025) map of existing controls and gaps, and the machine-readable marking of AI output (EU AI Act Art. 50). v1.13."
type: reference
status: draft
owner: nghiep
audience: [engineer, cto, cio, agent]
applies_to: [ecosystem, aa-cis-api, aa-cis-worker, tripplanner-lambda, aa-crm-api, aa-booking-api, aa-booking-admin]
last_reviewed: 2026-11-10
review_every_days: 30
related: [ARCH-01-ai-gateway, APP-06-routes, APP-06-eval, APP-06-prompts, ARCH-08, docs/adr/0009-ai-platform-and-provider-gateway.md, AA-804, AA-820, AA-1040]
---

# AI Use Register (v1.13)

One row per place where the ecosystem calls an AI model or a paid data provider. It answers, for each stage: what it
is for, who owns the decision to change it, which provider and model family serve it today, which data may leave AWS,
whether tenant data is in the prompt, what caps its spend, how it is switched off, how a change is evaluated, and
which human checks the output before anyone relies on it.

- **Why it exists:** [ADR 0009](../adr/0009-ai-platform-and-provider-gateway.md) (AI platform and provider gateway,
  decisions 1–9, 13 and 14 accepted 31/10/2026) and the S261 architecture review item TL-15. The tenant terms and the
  partner-portal privacy notice take their provider list from this page (AA-820).
- **v1 (2026-11-01):** adds what the S262 gateway build made live ([AI gateway (as built)](ai-gateway.md)): ledger v2
  for CIS, TripPlanner and the CRM, the Jev and DataForSEO caps (CIS 318), the tenant AI budget (321), the per-kind
  registry rows of Jev, DataForSEO, Geoapify and Guardrails (322), the TripPlanner contract views (323), the acc2
  candidate models (324), the probe and Bedrock Batch ledger rows, and the gateway's circuit, route deadline and
  re-queue as switches. The model column still comes from the 29/10 route snapshot: no route changed since (320–324
  add no route row), and the [generated route table](../generated/llm-routes.md) (`APP-06-routes`) wins when they
  differ. Its model catalog half predates 324 (the five acc2 candidates are missing there until the snapshot is
  recaptured, a backlog follow-up). v0 was written by hand from the code on `main` on 31/10/2026.
- **v1.1 (2026-11-02):** adds the acc2 Bedrock fallback of the judge and validate stages (CIS migrations 331–333,
  [section below](#acc2-bedrock-fallback-for-judge-and-validate-stages-cis-331333)). For the stages listed there, that
  section wins over the "Provider / family today" column of their rows, which still shows the 29/10 snapshot.
- **v1.2 (2026-11-02, S264):** the six tenant writer stages may fall back to the OpenAI API as their last rung (CIS
  migration 344, tech lead decision S264, ADR 0009 decision 5 amendment): their rows below and the tenant-terms
  provider list.
- **v1.3 (2026-11-03, S265):** `a3_place_dedupe` gets the acc2 Llama 4 Maverick rung before the OpenAI API hop (CIS
  339; its row and the acc2 section below).
- **v1.5 (2026-11-03, S266):** the [machine-readable marking](#machine-readable-marking-eu-ai-act-art-50) of AI
  output per surface and per publish channel (AA-1040, EU AI Act Art. 50, ADR 0019 d19). Includes the catalog Master
  text row and the coverage limits. No route change.
- **v1.6 (2026-11-03, S266):** the two marking gaps of v1.5 are closed (AA-1040): the catalog tour JSON other apps
  read (catalog.http.v1 1.3 `Tour.ai`, the TripPlanner browse Lambda) and the Booking supply text (CIS 358, Booking
  `content.ai` and the "AI-assisted" badge). No route change.
- **v1.7 (2026-11-04, S267):** family fallback chains (CIS migration 366, tech lead request S267): every active route
  is an ordered chain by model family. Claude Sonnet 4.6 and Claude Haiku 4.5 come back as Converse catalog rows
  (`sonnet-4-6`, `haiku-4-5`, acc3 only) right behind their 5.5 siblings; a writer then steps one Claude tier; the
  acc2 rung stays where it was; the OpenAI API stays last and only on `vendor_direct` stages. The gateway now tries a
  `vendor_direct` route on AWS first across ALL its models (every AWS deployment of every model, then the vendor
  APIs), so a same-family degrade no longer has to be dropped. `tp_compose`, `segment_research` and
  `segment_research_batch` get their first fallback. Judges, `a3_place_card`, `t10_claims` and the embed stages are
  unchanged. Rows below, and the new `segment_research*` row.
- **v1.8 (2026-11-04, S267, tech lead decisions; replaces the order described in v1.7):** **AWS preferred, not AWS
  only** (ADR 0009 decision 5 amendment S267, replacing T-3): CIS migration 366 gives EVERY active text stage
  (writer, judge, validate) `allowed_scopes = {aws_only, vendor_direct}`, tenant content, TripPlanner and the validate
  and brand-audit stages included; only the embedding stages (and switched-off routes) stay `aws_only`. The gateway
  runs every route **model first**: each model on acc3, then the same model on its vendor API (Claude 5.x on the
  Anthropic API; GPT-6 Luna on the OpenAI API through its twin row `gpt-6-luna-openai`), before the next model; any
  other model reached only outside AWS is the last rung. Chains (CIS 366): large writers Sonnet 5.5 → Sonnet 4.6 →
  Haiku 4.5 → OpenAI API (`tp_compose` too); small writers Haiku 5.5 → Haiku 4.5 → Sonnet 4.6 → OpenAI API
  (`segment_research*` too); a Claude validate stage keeps one 5.x tier (the six attempts per request); every GPT
  route (the judges, the two brand audits, `a3_atomize`, `s1_source_facts`, `a3_place_card`, `a3_place_dedupe`,
  `t10_claims`, `t10_adjudicate`) runs GPT-6 Luna on acc3, then on the OpenAI API, before its next model (fix pass 2
  of the S267 review: while acc3 refuses GPT these stages answer on GPT-6 Luna through the OpenAI API, not on acc2).
  **One Anthropic API key** for every product (`anthropic-direct`, 150 USD a month, alert 80 %, hard stop) and acc3
  capped at 100 USD a month (alert 80 %), both CIS 366; the split by product is ours (ledger per stage, the admin
  Spend > By app page, CIS `llm_route_chains.product_of`). The hard stops are enforced by the CIS gateway only (see
  "Budget source" below). **So the
  Anthropic API and the OpenAI API are now reachable by tenant content (writers, judges and the validate stages),
  TripPlanner and, once its own gateway follows, the CRM**: see "Providers" below and its follow-up for the business
  owner. Not applied yet: TripPlanner's gateway calls Bedrock only and skips the vendor deployments of `tp_compose`,
  has no connection hard stop, and reads the acc3 connection circuit from a view that still uses the old rule (see
  the `tp_compose` row); the CRM keeps its own Bedrock-only gateway until its own change (root ADR 0008a §5–6).
- **v1.11 (2026-11-06, S271, AA-820):** records the provider order that route control has set since 2026-11-05
  (S269, AA-1042; [AI gateway](ai-gateway.md) §4.1): **version 6, preset `prefer_anthropic_api`**, puts the
  Anthropic API deployment of every Claude model (`haiku-5-5`, `sonnet-5`, `sonnet-5-5`, `opus-5-5`, `haiku-4-5`,
  `sonnet-4-6`, `opus-4-6`, `opus-4-5`) first and acc3 second; GPT models keep acc3 first and their OpenAI API twin
  second. acc3 still refused its seven main models (Claude 5.x, GPT-6, GPT-5.6) at the S270 close, and since CIS
  #1332 a rung whose circuit is open after a refusal is deferred without a call, so on Dev today **the Anthropic API
  answers the Claude rungs of every CIS stage and the OpenAI API answers the GPT judges, audits, checks and
  extraction stages**. The chains (CIS 366 / 376) are unchanged; the rows below name each Claude model's providers
  in the route-control order. The tech lead set it as temporary: the preset Prefer AWS puts AWS first again (a
  revert to versions 3-5 is refused by `attempt_cap`). TripPlanner and the CRM are unchanged: Bedrock only. The
  provider list for the tenant terms and the [DPA Annex 3](../legal/dpa-annex-3-subprocessors.md) follow.
- **v1.12 (2026-11-06, S271, AA-820):** the Content studio pages of AA-Partner (`/legal/partner-terms` §3,
  `/legal/privacy` §5–§6, EN and VI) moved to Draft v0.5 and follow the provider list below: Claude models write and
  may also check, on the Anthropic API first and Amazon Bedrock second; OpenAI models and Amazon Nova / Meta Llama
  review and check; an OpenAI model may write as a last resort. AA may change the order without notice; adding or
  replacing a provider follows the DPA notice ([DPA](../legal/dpa.md) 6.2). No route change.
- **v1.13 (2026-11-09, S274, AA-820; records a route change made on 2026-11-06):** CIS migration 383 (AA-900, S271
  wave W0, tech lead decision D7; applied on Dev on 2026-11-06 as route control version 7) removed GPT-6 Luna on the
  OpenAI API (`gpt-6-luna-openai`) from all 13 writer routes and Amazon Nova Lite (`nova-lite`) from the 10 judge and
  instrument rows (every judge row, the two brand audits and `t10_adjudicate` included, and the validate instrument
  `t10_claims`); the other validate rows (`t9_faq_filter`, `t9_faq_answer_fit`, the `a3_*` rows, `s1_source_facts`)
  keep any Nova Lite rung on purpose. A writer whose Claude rungs all fail now stops with `queue_retry`; a judge
  whose GPT rungs all fail returns no verdict. **For the stages it names, migration 383 wins over the "Provider /
  family today" column of the rows below**, which still show the post-376 chains ("GPT-6 Luna (OpenAI API) last
  resort", "→ Nova Lite (acc2)"). The provider list for the tenant terms is corrected below: an OpenAI model no
  longer writes. Also new since 2026-11-06 (CIS 385): the CIS gateway keeps the raw reply of each provider attempt in
  `shared.llm_cassette` (prompt hash only, no text for a `pii` stage, DM-7.1 30 days proposed), so "no prompt or output
  text" holds for the ledger, not for every store; [DPA Annex 1](../legal/dpa-annex-1-processing.md) §3 and
  [Annex 2](../legal/dpa-annex-2-security.md) M-20 say so.
- **Who updates it:** the PR that adds, removes or re-routes a stage, adds a provider, or changes a stage's data
  scope, budget or human gate updates its row. A new provider also updates the tenant terms list (AA-820).

## How to read the columns

| Column | Meaning |
|---|---|
| Owner role | Who decides a change. **Tech lead**: writer stages and anything tenant-facing (a route switch on a main writer stage needs the tech lead's yes, ADR 0009 decision 12). **Engineer on duty**: extraction, validate and embed stages, which an engineer may re-route after the eval in the [eval runbook](https://github.com/AdventureAsia365-Ecosys/AA-CIS-App/blob/main/docs/llm/eval-runbook.md) and report after the fact. Roles, never names. |
| Provider / family today | Primary model, then fallbacks, from the route table. For a model with two deployments, the order in brackets is the provider order of route control (v1.11). "Bedrock (acc3)" = Amazon Bedrock in the LLM account; "OpenAI API" = the OpenAI platform API outside AWS; "acc2" = Bedrock in the infrastructure account. Families: Anthropic (Claude Sonnet 4.6 / 5.5, Haiku 4.5), OpenAI (GPT-5.6 Luna, GPT-6 Luna), Cohere (Embed v4). |
| Data scope | From `shared.llm_role_config.allowed_scopes` (CIS migration 311, `shared/llm_client/data_scope.py`): `aws_only` = the stage's content may only go to connections inside AWS; `vendor_direct` = it may also reach a vendor API outside AWS. Every CIS stage whose route names a model reachable only outside AWS (`gpt-6-luna-openai`) is `vendor_direct`; every other stage was `aws_only` until CIS 366. Since CIS migration 327 (AA-1026, tech lead T-3 in S263) that includes the five A-series writers (`a0_column_map`, `s1_generate`, `s1_flag_fix`, `s1_itinerary_nudge`, `supply_content_writer`), and since CIS migration 344 (tech lead, S264) the six tenant writers (`t2_generate`, `t2_flag_fix`, `t2_itinerary_nudge`, `t8_angle_gen`, `t9_write`, `t9_repair`): every AWS deployment of the route first, then the Anthropic API once its key is in, GPT-6 Luna on the OpenAI API last. CIS 327 moved every route off the legacy keys `haiku` / `sonnet` (Haiku 4.5 / Sonnet 4.6) to `haiku-5-5` / `sonnet-5-5` (T-4). **Since CIS 366 (S267, AWS preferred, not AWS only) every active text stage is `vendor_direct`** (embedding stages stay `aws_only`) and the gateway runs each route model first: a model on acc3, then the same model on its vendor API (Claude 5.x on the Anthropic API, GPT-6 Luna on the OpenAI API through its twin row `gpt-6-luna-openai`), then the next model; any other model reached only outside AWS is last (this replaces the "AWS first across all its models" order of v1.7). |
| Tenant data | Yes when the prompt carries a tenant's brand settings, briefs or tenant-written text. Traveller input is noted separately. |
| Budget source | What stops spend today. **Connection** = `shared.llm_provider_connection.monthly_budget_usd` (since CIS 366: acc3 100 USD, the one Anthropic API key `anthropic-direct` 150 USD, and since 327 the OpenAI API 10 USD a month, each alert 80 %, hard stop). The hard stop is enforced by the **CIS gateway only**: it sums `shared.llm_call_log` per connection, so TripPlanner's acc3 calls count toward the cap but are not stopped by it (TripPlanner's gateway has no per-connection budget check; its stop is its daily app cap), and the CRM's calls (ledger `crm.llm_call`) are neither counted nor stopped. No cap spans every product: on acc3 the AWS budget only e-mails; for the Anthropic API key, the vendor-side spend limit (150 USD) set when the key is created. Follow-ups: TripPlanner and CRM, see ADR 0009 decision 5 amendment S267. **Job cap** = a `shared.spend_budget` row (provider × `job:<kind>`) that the job loads with `shared/cost_guard.py` before each call. **Tenant budget** = a `shared.tenant_ai_budget` row (CIS 321, AA-1016): alert, then staff approval for T-stages; a tenant without a row has none. "Connection only" means no per-stage or per-job cap exists yet (ADR 0009 decision 6 closes this). |
| Kill switch | What turns the stage off without a deploy of new code. Since v1 the gateway also stops a connection by itself (connection circuit, AA-1018), ends a slow route at its `route_deadline_s` (none set yet), and holds refused jobs for the bulk re-queue. There is still **no per-stage switch in the gateway**: `is_active = false` on a route row makes the code fall back to its built-in default route (`SAFE_DEFAULTS`), it does not stop calls. The switches that exist are the connection `enabled` flag (all stages on that connection), a hard-stop budget row, and the feature flags named per row. |
| Golden set / eval | How a prompt or route change is measured ([eval runbook](https://github.com/AdventureAsia365-Ecosys/AA-CIS-App/blob/main/docs/llm/eval-runbook.md)): **R2** = a run on the frozen AA-729 golden set (`shared.eval_golden_set`) for writers `a1`, `t2`, `t9_blog`, `t9_social`; **Q2** = judge re-score; otherwise the baseline named in the CIS prompt register. |
| Human gate | Who checks the output before it is published, served or relied on. |

## Register

### CIS: A-series (platform content, AA's own catalog)

| Stage | App | Purpose | Owner role | Provider / family today | Data scope | Tenant data | Budget source | Kill switch | Golden set / eval | Human gate |
|---|---|---|---|---|---|---|---|---|---|---|
| `a0_column_map` | CIS | Map unknown Excel columns of a supplier import to tour fields | Engineer on duty | Haiku 5.5 → Haiku 4.5 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | No | Connection only | Connection `enabled` | Prompt register baseline | Import is reviewed in the A-series pipeline (A1/A2) before anything is served |
| `s1_generate` | CIS | A1 rewrite of a catalog tour (the Master writer) | Tech lead | Sonnet 5.5 → Sonnet 4.6 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | No | Connection only (wave runs carry their own cost report) | Connection `enabled` | R2 `a1` | A2 review before the Master is served (review queue) |
| `s1_judge` | CIS | Score an S1 draft against the rubric | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3, then the OpenAI API: its twin, CIS 366) → Nova Lite (acc2) / OpenAI, Amazon | vendor_direct | No | Connection only | Connection `enabled` | Q2; judge not calibrated yet (kappa 0.562 on 13 pairs, candidate only, S261 review TL-10) | A2 review |
| `s1_brand_audit` | CIS | Brand and fact audit of an S1 draft | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3, then the OpenAI API: its twin, CIS 366) → Nova Lite (acc2) / OpenAI, Amazon | vendor_direct (CIS 366) | No | Connection only | Connection `enabled` | Q2 | A2 review |
| `s1_flag_fix` | CIS | Repair the sentences the checks flagged | Tech lead | Haiku 5.5 → Haiku 4.5 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | No | Connection only | Connection `enabled` | R2 `a1` (part of the graph) | A2 review |
| `s1_itinerary_nudge` | CIS | Fix itinerary structure in an S1 draft | Tech lead | Haiku 5.5 → Haiku 4.5 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | No | Connection only | Connection `enabled` | R2 `a1` (part of the graph) | A2 review |
| `s1_source_facts` | CIS | Extract per-day source facts for the writer | Engineer on duty | GPT-6 Luna (acc3, then the OpenAI API: its twin) → Haiku 5.5 (the Anthropic API, then acc3) → Nova Lite (acc2) (CIS 376) / OpenAI, Anthropic, Amazon | vendor_direct (CIS 366) | No | Connection only | Flag `S1_STRUCTURED_FACTS` (env or tenant flag, default off) | Prompt register baseline | A2 review |
| `s1_grounding` (Jev) | CIS | Ask Jev whether each sentence is supported by the source (`a1_claim_supported`) | Tech lead | Jev (TypeSafe), decision API outside AWS | Jev connection (outside AWS) | No | Jev day cap 5 USD, hard stop before each ask (CIS 318, AA-642 S0); a stop leaves the stage on its own rule | Question mode off / shadow / enforce (`decision_question`, CIS ADR 0007); Jev failing never blocks | Jev verdicts act only when enforced and calibrated (CIS ADR 0007) | A2 review; unsupported claims go to manual check |
| Other Jev `decide` questions | CIS | Typed yes/no questions in debate, claim rules, trip facts, atom ranking, segment matching, tenant pipeline (`shared.decision_log`) | Engineer on duty | Jev (TypeSafe) | Jev connection; tenant questions only for allowlisted tenants | Some (tenant pipeline, allowlisted tenants only) | None before the call today | Per-question mode (off / shadow / enforce) | Per question (CIS ADR 0007) | As the calling stage |
| `s1_atom_writer` | CIS | Route kept for atom writing; **no caller found on `main`** | Engineer on duty | Sonnet 5.5 → Haiku 5.5, Bedrock (acc3) / Anthropic | aws_only | No | Connection only | Connection `enabled` | None | None (not called) |
| `a3_atomize` | CIS | Cut a Master tour into atoms (A3) | Engineer on duty | GPT-6 Luna (acc3, then the OpenAI API: its twin) → Haiku 5.5 (the Anthropic API, then acc3) → Nova Lite (acc2) (CIS 376) / OpenAI, Anthropic, Amazon | vendor_direct (CIS 366) | No | Connection only | Connection `enabled` | Offline A/B of S224 (prompt register) | None per item; atoms are curated in the admin atom pages |
| `a3_place_days` | CIS | Day skeleton of places for a tour | Engineer on duty | Haiku 5.5 → Haiku 4.5 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) → Nova Lite (acc2) / Anthropic, Amazon | vendor_direct (CIS 366) | No | Job cap `bedrock` × `job:place_extract` (per day of that kind) | Connection `enabled`; budget hard stop | S246 place model trial | None per item |
| `a3_place_locate` | CIS | Name and locate places from tour text | Engineer on duty | Sonnet 5.5 → Sonnet 4.6 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) → Nova Lite (acc2) / Anthropic, Amazon | vendor_direct (CIS 366) | No | Job cap `bedrock` (place geocode job) | Connection `enabled`; budget hard stop | S247 trial | None per item; flagged pins can be hidden (AA-997) |
| `a3_place_card` | CIS | Draft a place card from web-sourced facts | Engineer on duty | GPT-6 Luna (acc3, then the OpenAI API: its twin, CIS 366) → GPT-5.6 Luna (acc3) → Nova Lite (acc2) / OpenAI, Amazon | vendor_direct (CIS 366) | No | Connection only | Connection `enabled` | AA-784 blind eval (S252) | Two-model check (`a3_place_card_check`, another maker) |
| `a3_place_card_check` | CIS | Fact-check the place card draft | Engineer on duty | Haiku 5.5 → Haiku 4.5 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) → Llama 4 Scout (acc2) / Anthropic, Meta | vendor_direct (CIS 366) | No | Connection only | Connection `enabled` | AA-784 blind eval | None per item |
| `a3_place_dedupe` | CIS | Decide whether two places are the same | Engineer on duty | GPT-6 Luna (acc3, then the OpenAI API: its twin, CIS 366) → GPT-5.6 Luna (acc3) → Llama 4 Maverick (Bedrock acc2, CIS 339) / OpenAI, Meta | vendor_direct | No | Job cap `bedrock` × `job:place_dedupe` | Connection `enabled`; budget hard stop | S234 identity A/B | Two-model check (`a3_place_dedupe_check`) |
| `a3_place_dedupe_check` | CIS | Second opinion on a merge | Engineer on duty | Haiku 5.5 → Haiku 4.5 (each on the Anthropic API, then acc3: route control v6) → Nova Lite (acc2) / Anthropic, Amazon | vendor_direct (CIS 366) | No | Job cap (as above) | Connection `enabled` | S234 identity A/B | None per item |
| `segment_research`, `segment_research_batch` | CIS | Demand research: phrase search keywords for a segment (job `segment_research`, one keyword step per call; the batch proposer) | Engineer on duty | Haiku 5.5 → Haiku 4.5 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort (CIS 335, chain CIS 366 / 376) | vendor_direct (CIS 366) | No | Connection only | Stage switch (`is_active`); degrade mode `queue_retry` (the job is re-queued) | None | None per item; segments are curated in the admin atom pages |
| `a3_place_embed`, `f10_embed` | CIS | Embeddings of places and content for search and similarity | Engineer on duty | Cohere Embed v4, Bedrock acc2 → acc3 / Cohere | aws_only | No | Connection only | Connection `enabled` | None (deterministic use) | Not applicable |
| `supply_content_writer` | CIS (for Booking) | Customer description and highlights of a Booking hotel or service, from staff-entered facts treated as untrusted data | Tech lead | Sonnet 5.5 → Sonnet 4.6 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | No | Job cap `bedrock` × `job:supply_content_draft` (per day of that kind) + `SUPPLY_CONTENT_MAX_DRAFTS_PER_DAY` | Flag `SUPPLY_CONTENT_LLM=off` | None | Booking staff review each draft before Booking shows it |
| `writing_memory_mine`, `writing_memory_eval` | CIS | Draft writing-memory rules from edits; eval judge of the R2 runner | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3, then the OpenAI API: its twin, CIS 366) → Nova Lite (acc2) / OpenAI, Amazon | vendor_direct | Possible: writing memory has tenant-scoped rows (CIS ADR 0010) | Job cap `bedrock` × `writing_memory_mine`; eval runs: 25 USD a month over every writing-memory stage (`MONTH_CAP_USD`) | Per-writer memory switch and release activation (CIS ADR 0010) | R2 itself | Release activation by staff (CIS ADR 0010) |
| DataForSEO (`data`) | CIS | Keyword volumes, SERP and question research for tours and segments | Engineer on duty | DataForSEO API, outside AWS | Keywords and place names only | No | Job cap `dfs` (a global day cap, seeded 10 USD/day, plus per-job rows: segment research, S1 SEO prefetch, question top-up) | Budget hard stop | Not applicable | Not applicable |
| Geocoder (`data`) | CIS | Geocode and shape places (`services/places/geocoder.py`) | Engineer on duty | Geoapify, outside AWS (`geo.geocode_call`, ledger v2 row; registry row since CIS 322) | Place names only | No | Job cap `geocoder` (place geocode, relocate, shape jobs) | `PLACE_SHAPES_ENABLED` (shape job, default off); budget hard stop | AA-997 accuracy audit | Flagged pins hidden (AA-997) |
| `s1_generate` (Bedrock Batch) | CIS | The same A1 rewrite sent as a Bedrock Batch job (`s1_batch`); each record writes a ledger row at the batch price | Tech lead | Haiku 4.5, Bedrock Batch (acc3) / Anthropic; **blocked**: AWS has not enabled Batch Inference on acc3 (AA-624) | aws_only | No | Connection only | Connection `enabled`; no batch is submitted while AA-624 is open | R2 `a1` | A2 review |
| acc2 chat models (Nova Lite, Nova 2 Lite, Llama 4 Maverick, Llama 4 Scout, Kimi K3) | CIS | Catalogued with one acc2 deployment each (CIS 324). **Since CIS 331–333 (S263) Nova Lite and Llama 4 Scout are routed** as the acc2 fallback of judge and validate stages, and since CIS 339 (S264) Llama 4 Maverick on `a3_place_dedupe` (section below); Nova 2 Lite and Kimi K3 are on no route | Tech lead | Bedrock (acc2) / Amazon, Meta, Moonshot | aws_only | Nova Lite: yes, on the tenant judge / validate stages of 332–333 | Connection only | Connection `enabled`; the admin route PATCH | Contract smoke per stage before routing (`llm_contract_smoke`, AA-1026); the rest of the ladder (calibration, A/B, shadow) skipped knowingly for these fallbacks | An acc2 judge pass that would publish (`s1_brand_audit`, `t2_brand_audit`) is held for a human check (`BRAND_AUDIT_UNCALIBRATED_JUDGE`) |
| `adhoc_conn_test` (daily probe, Test connection) | CIS | One small call per enabled text deployment (`llm_connection_probe`, daily 05:00 UTC, at most 30) or one admin Test; writes `access_state` and `last_probe_at` | Engineer on duty | Every enabled connection | The connection's own scope; the prompt is a fixed test text | No | Connection only (under 1 USD a month on Dev, ADR 0009 decision 7) | `LLM_DAILY_PROBE` (on, Dev) | Not applicable | Not applicable |

### CIS: T-series (tenant content, Content studio)

T-series writer stages were `aws_only` until S264. Since CIS migration 344 (tech lead decision S264, 02/11/2026: acc3
refuses every model since 29/10 and the Anthropic API has no key, so tenants could not write at all) the six tenant
writer stages are `vendor_direct`: Claude on Bedrock (acc3) first, then the same Claude model on the Anthropic API
once its key is in, then GPT-6 Luna on the OpenAI API as the **last** rung, only when every AWS path failed (ADR 0009
decision 5 amendment, the rule of the A-series writers in CIS 327). Since CIS migration 366 (S267, tech lead: AWS
preferred, not AWS only; model first) each tenant writer has its Claude family chain again (Sonnet 5.5 → Sonnet 4.6 →
Haiku 4.5, or Haiku 5.5 → Haiku 4.5 → Sonnet 4.6), run model first: the 5.x primary on acc3, then the same model on
the Anthropic API, then the 4.x rows on acc3, GPT-6 Luna on the OpenAI API last. Every other active T-stage (the
brand audit, the FAQ filter / answer fit, the claim extraction) is `vendor_direct` too since 366, so tenant content
may reach the Anthropic API or the OpenAI API from every T-stage. Since CIS migration 383 (route control version 7,
2026-11-06, v1.13) the writers no longer have the GPT-6 Luna rung: only Claude writes, and a writer whose Claude rungs
all fail waits (`queue_retry`). The tenant terms name this (Draft v0.6, 2026-11-10: "Adventure Asia calls Claude
through the Anthropic API first and through Amazon Bedrock (Amazon Web Services) second", and "Only Claude models write
it: if no Claude model is available, the writing step waits and is tried again later"; Draft v0.5 still said an OpenAI
model "may write it as a last resort"). The other T-stage writers' rules are unchanged. The judge stages below are
`vendor_direct`; since CIS 366 (model first) their route runs GPT-6 Luna on acc3, then the same model on the OpenAI API
(its twin row), before the acc2 Nova Lite hop, so tenant content reaches the OpenAI API as soon as acc3 refuses or
fails GPT-6 Luna (from 333 to 366 it went there only after the acc2 hop). The tenant terms stated this as "may be used
as a fallback" until their Draft v0.5 (2026-11-06), which names the direct APIs as providers; the AA-820 follow-up
below covers the wider use. **Since route control version 6 (2026-11-05, v1.11)
the Anthropic API is the first provider of every Claude model, not a fallback**, and while acc3 refuses, the OpenAI
API answers the judge stages: on Dev today tenant content goes to the two direct APIs on almost every T-stage call.

| Stage | App | Purpose | Owner role | Provider / family today | Data scope | Tenant data | Budget source | Kill switch | Golden set / eval | Human gate |
|---|---|---|---|---|---|---|---|---|---|---|
| `t2_generate` | CIS | T2: rewrite a catalog tour in the tenant's brand voice | Tech lead | Sonnet 5.5 → Sonnet 4.6 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | Yes (brand settings) | Connection + tenant budget | Connection `enabled` | R2 `t2` | Tenant reviews and exports; AI notice at review, publish and export |
| `t2_judge`, `t2_brand_audit` | CIS | Score and audit a T2 rewrite | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3, then the OpenAI API: its twin, CIS 366) → Nova Lite (acc2); 10 % shadow on GPT-6 Luna / OpenAI, Amazon | vendor_direct (`t2_brand_audit` since CIS 366) | Yes | Connection + tenant budget | Connection `enabled`; brand claim check `T2_BRAND_CLAIM_CHECK=off` | Q2 | Tenant review |
| `t2_flag_fix`, `t2_itinerary_nudge` | CIS | Repair flagged T2 sentences and itinerary structure | Tech lead | Haiku 5.5 → Haiku 4.5 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | Yes | Connection + tenant budget | Connection `enabled` | R2 `t2` (part of the graph) | Tenant review |
| `t7_debate_judge` | CIS | Brand-fit call of the T7 debate | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3, then the OpenAI API: its twin, CIS 366) → Nova Lite (acc2) / OpenAI, Amazon; 10 % shadow | vendor_direct | Yes | Connection + tenant budget | Connection `enabled` | Q2 | Tenant review |
| `t8_angle_gen` | CIS | Propose content angles for a tenant brief | Tech lead | Sonnet 5.5 → Sonnet 4.6 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | Yes | Connection + tenant budget | Connection `enabled` | Prompt register baseline | Tenant picks the angle |
| `t9_write` | CIS | T9: blog and social pieces about a tour | Tech lead | Sonnet 5.5 → Sonnet 4.6 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | Yes | Connection + tenant budget | Connection `enabled` | R2 `t9_blog`, `t9_social` | Authenticity check (no reviews, testimonials, first-person customers, independence claims); tenant reviews and presses publish (T10/T11) |
| `t9_repair` | CIS | Sentence repair, SEO fit and the admin sentence suggest | Tech lead | Haiku 5.5 → Haiku 4.5 (each on the Anthropic API, then acc3: route control v6; chain CIS 376) / Anthropic; GPT-6 Luna (OpenAI API) last resort | vendor_direct | Yes | Connection + tenant budget | Connection `enabled` | Prompt register baseline | Tenant review |
| `t9_faq_filter`, `t9_faq_answer_fit` | CIS | Filter real search questions for the blog FAQ; check each answer fits | Engineer on duty | Haiku 5.5 → Haiku 4.5 / Sonnet 5.5 → Sonnet 4.6 (each model on the Anthropic API, then acc3: route control v6; chain CIS 376) → Nova Lite (acc2) / Anthropic, Amazon | vendor_direct (CIS 366) | Yes | Connection + tenant budget | Flag `T9_FAQ_LLM_FILTER` (default off) | S247 trial | Tenant review |
| `t10_judge` | CIS | T10 gate: score a T9 piece | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3, then the OpenAI API: its twin, CIS 366) → Nova Lite (acc2) / OpenAI, Amazon | vendor_direct | Yes | Connection + tenant budget | Connection `enabled` | Q2 | Tenant review |
| `t10_adjudicate` | CIS | T10 tier-2 adjudicator of the writer's sentences | Tech lead | GPT-6 Luna (acc3, then the OpenAI API: its twin, CIS 366) → GPT-5.6 Luna (acc3) → Nova Lite (acc2) / OpenAI, Amazon | vendor_direct | Yes | Connection + tenant budget | `T10_ADJ_MODE` (default off) | None yet | Tenant review |
| `t10_claims` | CIS | F9 v2 claim extraction; **not wired into the gates** (no caller on `main`) | Engineer on duty | GPT-6 Luna (acc3, then the OpenAI API: its twin, CIS 366) → GPT-5.6 Luna (acc3) → Nova Lite (acc2) / OpenAI, Amazon | vendor_direct (CIS 366) | Yes (when wired) | Connection + tenant budget | Connection `enabled` | Replay before wiring | Not applicable yet |

### acc2 Bedrock fallback for judge and validate stages (CIS 331–333)

Root [ADR 0009](../adr/0009-ai-platform-and-provider-gateway.md) decision 14, amended by the tech lead on 01/11/2026
(S263, AA-1026): judge and validate stages may fall back to chat models on Bedrock in the infrastructure account
(acc2), a second failure domain next to the LLM account (acc3), which refuses every model since 29/10. Rule **AWS
first, vendor APIs last**: every AWS deployment of a route is tried before a vendor API outside AWS (the OpenAI API
today, the Anthropic API once its key is in). Writer stages keep Anthropic models; acc2 cannot run Claude. Each pick is
the cheapest acc2 model that passed the stage's contract smoke (its own prompt and parser on the acc2 deployment), and
is not from the writers' family (Anthropic), per decision 12. acc2 is `aws_only`, so no data scope changed.

| Migration | Stages | acc2 model (maker) | Position in the route |
|---|---|---|---|
| 331 (platform) | `s1_brand_audit`, `s1_source_facts`, `a3_atomize`, `a3_place_card`, `a3_place_days`, `a3_place_locate`, `a3_place_dedupe_check` | Nova Lite (Amazon) | Last fallback |
| 331 (platform) | `a3_place_card_check` | Llama 4 Scout (Meta): another maker than the draft stage's Nova Lite, so the two-model check keeps two makers | Last fallback |
| 332 (tenant) | `t2_brand_audit`, `t10_claims`, `t9_faq_answer_fit`, `t9_faq_filter` | Nova Lite (Amazon) | Last fallback |
| 333 (platform and tenant) | `s1_judge`, `t2_judge`, `t7_debate_judge`, `t10_judge`, `t10_adjudicate`, `writing_memory_eval`, `writing_memory_mine` | Nova Lite (Amazon) | Before the OpenAI API hop (333); last since CIS 366, where the OpenAI API hop (GPT-6 Luna's twin) moved right behind GPT-6 Luna |
| 339 (platform) | `a3_place_dedupe` | Llama 4 Maverick (Meta): another maker than its check stage's Nova Lite; asked for the object in the prompt (CIS 337) | Before the OpenAI API hop (339); last since CIS 366 (the twin right behind GPT-6 Luna) |

- **`a3_place_dedupe` (closed by CIS 339, S264):** it needed an acc2 model of another maker than its check stage's
  Nova Lite that also returns a structured verdict; Llama 4 Scout and Maverick refuse a forced tool choice on Bedrock,
  so CIS 337 asks Llama 4 models for the object in the prompt, and the Maverick rung went in after its contract smoke
  passed (one call, 779 ms, 0.00021 USD).
- **Human gate:** an acc2 pass of a brand audit that would publish is held as a manual check
  (`BRAND_AUDIT_UNCALIBRATED_JUDGE`), so an uncalibrated judge never publishes on its own.
- **Rollback:** a new forward migration (remove the acc2 key from the routes), or the admin route PATCH per stage.
- **Since CIS 366 (S267):** the "AWS first, vendor APIs last" rule of this section is replaced by model first (ADR 0009
  decision 5 amendment S267). On the GPT routes GPT-6 Luna's OpenAI API twin now comes right behind GPT-6 Luna, so
  while acc3 refuses GPT these stages answer on GPT-6 Luna through the OpenAI API (10 USD a month cap) and reach the
  acc2 pick only after that, or once that cap is hit.

### TripPlanner (travellers, no sign-in needed)

| Stage | App | Purpose | Owner role | Provider / family today | Data scope | Tenant data | Budget source | Kill switch | Golden set / eval | Human gate |
|---|---|---|---|---|---|---|---|---|---|---|
| `tp_compose` | TripPlanner | Narrate and re-narrate a traveller's trip | Tech lead | Sonnet 5.5 → Sonnet 4.6 → Haiku 4.5, Bedrock (acc3) / Anthropic (CIS 366; CIS 376 dropped the OpenAI API rung its gateway never calls). **TripPlanner's gateway calls Bedrock only today**: it skips Sonnet 5.5 on the Anthropic API until it gains vendor adapters. It may also skip the new acc3 rungs: it reads the acc3 connection circuit from `catalog.v_llm_gateway_config_v1`, which still counts single-model refusals that the CIS breaker no longer counts, so after a CIS request that last probed two refused acc3 models acc3 stays tripped for TripPlanner until the next CIS answer on acc3 (follow-up: a CIS view migration with the new rule) | vendor_direct since CIS 366 (TripPlanner reads its route through `catalog.v_llm_gateway_config_v1`, CIS 323) | No; **traveller free text** can be in the prompt (no automated scrub yet, ADR 0009 "Not decided here") | `TP_DAILY_SPEND_CAP_USD` (5 USD/day over the online stages, set by Infra), read through `catalog.v_llm_app_spend_today_v1` (no fallback since AA-1027 E5); fails closed when the spend cannot be read (AA-642 S0); per-visitor limits in `tripplanner.ai_rate_counter` (tp-023, AA-1015). Its acc3 calls count toward the acc3 100 USD connection cap but are not stopped by it (follow-up) | Over the cap the site serves basic narration (degrade mode) | None | AI label on the site and on AI narration; an Adventure Asia advisor reviews every itinerary before booking |
| `tp_search_embed` | TripPlanner | Embed the traveller's search text | Engineer on duty | Cohere Embed v4, Bedrock acc2 → acc3 / Cohere | aws_only | No; traveller search text | Same daily cap | Same degrade mode | None | Not applicable |
| `tp_extract`, `tp_component_embed` | TripPlanner | Routes kept for the old place extraction and embedding; **no caller found on `main`** (the place pipeline moved to CIS `a3_*`, AA-712) | Engineer on duty | Sonnet 5.5 / Cohere Embed v4 | aws_only | No | Logged only (offline stages are outside the daily cap) | Connection `enabled` | None | None (not called) |

### AA-Partner CRM and AA-Booking

| Stage | App | Purpose | Owner role | Provider / family today | Data scope | Tenant data | Budget source | Kill switch | Golden set / eval | Human gate |
|---|---|---|---|---|---|---|---|---|---|---|
| `crm_*` (gateway v2) | CRM | Reply drafts for agencies (card CRM-33a); the CRM gateway runs on the vendored `aa_llm` core and writes `crm.llm_call` in the ledger v2 shape (crm-032). **Dev runs Amazon Nova Lite** on acc2 (AA-Partner crm-042, AA-CIS-Infra `crm_llm.tf`, `CRM_LLM_PROVIDER=bedrock`, read live 05/11/2026), the interim path of root ADR 0009 decision 14 amendment (Dev only) | Tech lead | Nova Lite (Amazon), Bedrock acc2, `us.` cross-region profile (US regions only); the crm-037 Claude entries kept, switched off. Bedrock only, never OpenAI or Jev (root ADR 0008a §5–6). The S267 decision (AWS preferred, not AWS only; one Anthropic key) covers the CRM too; it applies when the CRM's own gateway change amends ADR 0008a §5–6, with the scrub kept before any call | Bedrock only (until that change) | Yes: the agency's own client data, scrubbed first (F3: known values, regex, Bedrock Guardrails in acc2 detect mode) | Per agency `crm.tenant_settings.ai_budget_usd` (default 2 USD a month), alerts at 75 / 90 / 100 % (crm-032), refused at 100 % | `ai_enabled` per agency (default false) | None yet | Every draft is shown to an agency member, who sends it by hand |
| `crm_scrub` (`guard`) | CRM | Pass 3 of the F3 PII scrubber: Bedrock Guardrails detect personal data before any CRM model call; each call is a `crm.llm_call` row with role `guard` | Tech lead | Bedrock Guardrails (acc2), guardrail `aa-crm-dev-scrub` | Bedrock only | Yes: the agency's client text, before it reaches a model | Per agency AI budget | `ai_enabled`; a failed scrub fails closed | EN/VI scrub corpus gate (`Scrub corpus` workflow) | Not applicable |
| None | Booking | Booking makes no AI calls. Hotel and service text is drafted by CIS (`supply_content_writer`) | — | — | — | — | — | — | — | High-risk advice rule in Booking `CONTEXT.md` (AA-820): no AI advice on insurance, financing, claims or visas without qualified staff review and AI disclosure |

### Providers, for the tenant terms (AA-820)

What the tenant terms and the partner-portal privacy notice name, derived from the rows above. Since S266 the tenant
terms summarise the [AI Schedule v1.0](../legal/tenant-ai-schedule.md) (AA-820): the Content studio `/terms` §3 and the
CRM `/legal/terms` §1 (AA-Partner) take its version and the three policy links from one list, and the Trip Planner
`/terms` §3 names the narration model (`tp_compose`). Every direct API path below runs on an account held in the AA
company's name (ADR 0019 b19); tenants never hold a provider key.

- **Anthropic (Claude)**: every writer stage, and checks too: the FAQ filter / answer-fit stages and the Claude
  fallbacks of the audit and extraction stages (terms wording, Draft v0.5: Claude models "write it and may also check
  it"). Since 2026-11-05 (route control version 6, v1.11) each Claude model is
  called on the **direct Anthropic API first** and on Amazon Bedrock (acc3) second; while acc3 refuses, the Anthropic
  API serves every Claude call of the Content studio.
- **OpenAI models**: judge, audit and extraction stages that score or check drafts, on Amazon Bedrock (acc3) first and
  on the **direct OpenAI API** (GPT-6 Luna's twin) right after; while acc3 refuses, the OpenAI API serves them.
- **Cohere (Embed v4), through Amazon Bedrock**: search embeddings of catalog content.
- **Direct Anthropic API and direct OpenAI API**: paths outside AWS with a monthly cap (ADR 0009 decisions 5 and 14;
  ONE Anthropic API key for every product, 150 USD a month; the OpenAI API 10 USD a month). Until v1.10 this list
  called them fallback paths; since route control version 6 the Anthropic API is the first path of Claude, and
  while acc3 refuses the OpenAI API answers the judges, so the terms must name both as providers that receive
  tenant content, not as fallbacks only. **Since CIS 366
  (S267, AWS preferred, not AWS only) every active text stage may reach them**: tenant content (writers, judges, the
  brand audit, the FAQ checks and the claim extraction), TripPlanner narration (`tp_compose`, once TripPlanner's
  gateway can call them) and, after its own change, the CRM. A Claude model goes to the Anthropic API first (route
  control version 6; before it, only when its AWS deployment refused or failed); GPT-6 Luna goes to the OpenAI API (its twin row) when its acc3
  deployment refuses or fails, before the next model of a judge or GPT validate route. Until CIS 383 (2026-11-06)
  GPT-6 Luna on the OpenAI API was also the last rung of the writer routes; since then **no OpenAI model writes**
  (v1.13). Terms wording: for the Anthropic API and the OpenAI API scoring and checking, providers that receive the
  content (v1.11), not "a fallback"; since the portal pages' Draft v0.6 (2026-11-10) they say "Only Claude models write
  it", and the Draft v0.5 sentence "an OpenAI model ... may write it as a last resort" is gone (an AA-Partner guard
  test checks every sentence about writing on both pages, EN and VI, against the writer providers of this list).
- **Follow-up for the business owner (AA-820):** the tenant terms, the AI Schedule and the DPA must name the Anthropic
  API (Anthropic, PBC, direct) and the OpenAI API (OpenAI, direct) as providers that may receive tenant content and
  TripPlanner traveller text, not only as writing fallbacks of the T-series writers (since CIS 366 the tenant judges
  and the claim extraction send tenant content to the OpenAI API as soon as acc3 refuses GPT-6 Luna, not only as a
  last resort). Until they do, decision 10's "only makers named in the terms" is not met for the T-stages and
  `tp_compose` that 366 opened. *S269:* the DPA draft v0.2 names both direct APIs as sub-processors for the Content
  studio stages ([DPA Annex 3](../legal/dpa-annex-3-subprocessors.md) §1.2), and the pilot contract set incorporates
  the AI Schedule; both wait for the tech lead's read and counsel. *S271:* DPA draft v0.3 Annex 3 names the
  Anthropic API as the first path of Claude and the OpenAI API as the path that answers the judges while acc3
  refuses; the AI Schedule's clause .1 already names both paths and its facts table follows. The Content studio pages
  of AA-Partner (`/legal/partner-terms` §3, `/legal/privacy` §5–§6, EN and VI, Draft v0.5) name both direct APIs as
  providers that may process the content, Claude on the Anthropic API first; AA may change the order without notice,
  and adding or replacing a provider follows the DPA notice ([DPA](../legal/dpa.md) 6.2); the readiness packet's copy of those pages (Annex A) follows. The CRM and Trip Planner terms are unchanged
  (both gateways call Bedrock only).
- **Jev (TypeSafe)**: yes/no decision checks; for tenant content only for allowlisted tenants.
- **DataForSEO, Geoapify**: keywords and place names only, never tenant text.
- **Amazon (Nova) and Meta (Llama) models on Bedrock (acc2)**: fallback for validate stages when acc3 refuses (CIS
  331–333, AWS first, vendor APIs last); since CIS 383 (2026-11-06) no longer for the judge routes, `t10_adjudicate`
  or `t10_claims`. On tenant stages only Amazon Nova Lite is routed, and only behind the two FAQ checks (flag
  `T9_FAQ_LLM_FILTER`, default off); Meta Llama 4
  Scout and Llama 4 Maverick serve one platform stage each (`a3_place_card_check`, `a3_place_dedupe`). Terms wording
  (Draft v0.5): "other models on Amazon Bedrock (Amazon Nova, Meta Llama) may also review and check it" (until v0.4:
  "may be used as a fallback"). The other acc2 models (Nova 2 Lite, Moonshot Kimi K3) are on no route and stay out of the tenant terms until one
  passes its contract smoke and is routed.

## Machine-readable marking (EU AI Act Art. 50)

Root ADR 0019 d19 (deadline 02/12/2026, AA-1040). Two duties: a person is told when they read or use AI output
(Art. 50(1), the visible notice), and AI-generated text carries a mark that software can read (Art. 50(2)). The
notice is the kit `AiNotice` (AA-CIS-App `frontend/app/_kit/core/`, one wording file for every app): variants
`staff`, `publisher`, `traveller`, `narration`, and the short "AI-assisted" badge (`form="badge"`). The tenant AI
Schedule [●].4 ([tenant-ai-schedule.md](../legal/tenant-ai-schedule.md)) relies on this section; the tenant still adds
any label a Channel or law requires to what it publishes ([●].4(b)).

| Surface | What AI wrote | Stored mark | Delivered mark | Visible notice |
|---|---|---|---|---|
| Content studio piece (T9) | Blog and social pieces (`t9_write`) | `acp_shared.content_piece.writer_input -> 'ai_provenance'`: `ai_generated`, `generator`, writer `model` (from the `t9_write` ledger row), `generated_at`; `human_edited_at` after a tenant edit. A piece older than AA-1040 still reads as AI-generated (`generated_at` = `created_at`, model unknown) | `piece.ai` in `/v1/content-writing/pieces/*`; HTML export: `<meta name="ai-*">` in the `<head>` (document) or after the `<article>` (fragment), `data-ai-*` on the `<article>`; every download: `X-AI-Generated` / `X-AI-Generator` / `X-AI-Model` headers | `publisher` line at review, publish and export; "AI-assisted" badge on each My Content, Published and publish row and in the piece drawer |
| Catalog Master text (A-series) | Tour name, subtitle, summary, description, highlights and day-by-day text of every Master tour (`s1_generate` and its repair stages) | None per row: every `gold_aa_internal.published_tours` `aa_*` text is S1 writer output by construction; the writer models and a staff edit before approval are on `silver_aa_internal.generated_content` (admin only) | `ai: {ai_generated, generator: "Adventure Asia catalog writer", generated_at, model: null, human_edited: null}` in the tenant tour reads (`/v1/tours/pool`, `/v1/tours/{id}`, `/v1/tours/{id}/full`), `generated_at` = the last Master publish (`updated_at`, else `published_at`); TripPlanner tour pages: `data-ai-generated="true" data-ai-source="catalog" data-ai-generated-at` on the summary, highlights and each itinerary day block (never page-wide: prices, photos and facts on the same page are not AI output). The same `ai` object in the catalog tour JSON other apps read: `Tour.ai` of catalog.http.v1 1.3 (the partner CRM, CIS `services/catalog_http`, inside the hashed body so the ETag moves with a Master publish) and every tour card and tour detail of the TripPlanner browse Lambda (`backend/browse/catalog.py` `catalog_ai_mark`; the tour page's `data-ai-generated-at` takes its `generated_at`). There `generated_at` is `catalog.v_tour.text_updated_at` (CIS 359), the Master row's `updated_at`, so it equals the tenant reads' value; a photo change does not move it. Until 359 is applied both readers fall back to `v_tour.updated_at` (the later of the text publish and the photo updates, an upper bound). **Not marked yet:** Marketplace rows (tour name only) | AI label (AA-819) on the tour text and the `traveller` line under the itinerary (AA-1033); `publisher` line in the Content studio catalog tab |
| Booking supply text | Hotel and service descriptions and highlights (`supply_content_writer`), reviewed and published by AA staff in CIS `/admin/supply-content`; shown read-only in the Booking admin and on proposal items | `shared.supply_content_version.origin` (`llm` = the writer's draft, `human` = a staff edit) and its `based_on_version_id` chain (a staff edit of a draft stays AI-assisted; a text written from scratch is not AI), `created_at` of the draft; served to Booking as `ai_generated`, `ai_generated_at`, `ai_human_edited` on `catalog.v_supply_content` (CIS 358, NULL while not published) | `content.ai` on the Booking hotel and service detail and `supply.ai` on proposal items: `{ai_generated, generator: "Adventure Asia supply content writer", model: null, generated_at, human_edited}`; `data-ai-generated` / `data-ai-source="cis-supply-content"` / `data-ai-generated-at` / `data-ai-human-edited` on each text block in the Booking admin (never page-wide) | "AI-assisted" badge (kit `AiNotice form="badge"`, staff sentence as its tooltip) next to the text in the hotel / service CIS panel, the service form, the proposal builder and the proposal preview; CIS admin labels each version "Written by model" |
| Content studio tour version (T2) | Tour rewrites (`t2_generate`) | `gold_aa_internal.tenant_tour_versions.edit_source` (`ai_generated`, `re_rewrite`; `tenant_edit` = a person's edit) and `generation_meta` (admin only) | `ai` in every tenant version read (`/v1/tours/my-versions`, `/v1/tours/versions/{id}`); DOCX download: core properties keywords `ai-generated` and comments (generator, generated-at, human-edited) | `publisher` line in the catalog tab, drawer and rewrite panel |
| WordPress post (T11 blog) | The published T9 piece | As the piece | Post body: `<article data-ai-generated="true" data-ai-generator data-ai-model data-ai-generated-at data-ai-human-edited>` (kept by WordPress for every role) and, after it, `<meta name="ai-generated">`, `ai-generator`, `ai-model`, `ai-generated-at`, `ai-human-edited`, `digital-source-type` (IPTC `trainedAlgorithmicMedia`), kept only when the connected WordPress user may post unfiltered HTML (administrators, editors) | The tenant's own site; Schedule [●].4(b) |
| Facebook Page post (T11) | The published T9 piece | As the piece | **None on the platform**: the Graph API Page feed has no AI label for a text post; the text is not changed | Schedule [●].4(b): the tenant labels it if Facebook's rules or the law require |
| CRM AI draft | Reply and follow-up drafts (`crm_draft_reply`) | `crm.ai_draft` (every row is model output; the model is on the ledger row `llm_call_id`) | `ai: {ai_generated, generator, generated_at}` in the draft answer; `data-ai-generated` / `data-ai-generated-at` on the draft text in the CRM web | `staff` line under the draft. A message a member writes from it is their own (a person reviews and sends) |
| Trip Planner narration | Day text on request (`tp_compose`, source `llm` / `mixed`) or AA itinerary text written earlier (`master`) | The narrate answer's `source` | `data-ai-generated="true"` and `data-ai-source` on the narration block | `narration` line for `llm` / `mixed`, `traveller` line otherwise; the per-source AI label (AA-819) |

**Coverage limits** (03/11/2026, v1.6): the table lists every surface that shows AI text to a tenant, a staff member or the public today, each with a stored and a delivered mark. The two v1.5 gaps are closed (AA-1040): the catalog tour JSON (catalog.http.v1 1.3 and the TripPlanner browse Lambda) and the Booking supply text (CIS 358). Still without a per-row mark: Marketplace rows, which show the tour name only. Where the model is not known at the read (catalog tours, Booking supply text), `model` is null and the writer model stays on the CIS ledger (admin only). A surface added later gets its row here first (ADR 0019 d19, deadline 02/12/2026).

**Publish channels and platform AI labels** (checked 03/11/2026; only blog and Facebook are built, the others answer
"not yet supported"). Verify against the platform's own reference when a channel is built:

| Channel | Platform label through the API | What AA sends |
|---|---|---|
| WordPress (blog) | No AI field in the REST API; unregistered post meta is ignored | The HTML mark above |
| Facebook Page feed (text) | None documented for a text post. Meta's "AI info" label comes from image and video metadata (C2PA / IPTC) or the uploader's own disclosure in the app; a `video_labels` parameter for video is reported by third parties only | Nothing extra; the mark stays in the piece |
| Instagram, LinkedIn, e-mail, ads | Not built | — |
| TikTok | Not built; third-party guides name a boolean `is_aigc` on the Content Posting API (video `post_info`), not confirmed against TikTok's reference | — |

The meta names are plain and self-describing; no single web standard marks AI text yet, so this table is their
definition. C2PA Content Credentials would apply to images and video, which no stage generates today.

## OWASP Top 10 for LLM Applications (2025): controls and gaps

Controls are cited only where they exist in code or configuration on `main` (01/11/2026). Gaps name the ADR 0009
decision or issue that closes them, or say "none planned".

| Risk | Existing controls | Gaps |
|---|---|---|
| **LLM01 Prompt injection** | Source text and staff input are passed as quoted, untrusted data (for example `services/supply_content/writer.py`); the AA-729 golden set carries 10 synthetic injection samples with canary tokens (`scripts/aa729/injection.py`) for S1 and T9; outputs are text only, never executed or used to call tools. | No injection check runs per call; TripPlanner traveller free text reaches `tp_compose` unscrubbed; tenant brand settings are free text. Proposed in ADR 0009 "Not decided here" (PII and scrub step for `free_text` stages). |
| **LLM02 Sensitive information disclosure** | Data standards DM-6.4 (no personal data in prompts); no prompt or completion text in `shared.llm_call_log` (ADR 0009 decision 8); per-stage data scopes `aws_only` / `vendor_direct` enforced by the gateway (`data_scope.py`, `test_aa1002_s5_data_scope.py`); the CRM scrubs personal data before any call and seals the placeholder map (`api/app/privacy/`). | DM-6.4 is review-only in CIS and TripPlanner (no automated scrub); the per-maker and per-geography scope (ADR 0009 decision 10) is still Proposed. |
| **LLM03 Supply chain** | Models only from the catalog `shared.llm_model_catalog`; CI guard `test_aa685_no_raw_model_calls.py` forbids a model SDK or HTTP call outside the gateway; secrets in Secrets Manager with a name-prefix CHECK; gitleaks on every repo. | The qualification ladder for a new model or provider (ADR 0009 decision 12) is still Proposed; the CI guard does not cover Jev, DataForSEO and the geocoder yet (ADR 0009 decision 1). |
| **LLM04 Data and model poisoning** | No model is trained or fine-tuned. Writing memory changes prompts only through a staff-activated release with a kill switch (CIS ADR 0010); the golden set is frozen and hashed (`shared.eval_golden_set.source_sha256`). | Supplier source text is trusted as tour facts; grounding catches unsupported claims but not a false source. None planned beyond A2 review. |
| **LLM05 Improper output handling** | Quality gates and validators before content is served (A2 review, T10 gate); the T9 authenticity check (`services/acp_content_writing/authenticity.py`); structured output with an enforced schema where a stage asks for it (for example `supply_content_writer` on Sonnet 5.5 through Converse); output is rendered as text by the frontends. | Some stages still parse free text from legacy model keys (21 stages, step-0 audit Q1); a truncated reply as an error class is decided (ADR 0009 decision 5) but not verified here. |
| **LLM06 Excessive agency** | No product stage has tools or actions: models return text, and code decides. Publishing happens only on a tenant's own publish action; CRM drafts are sent by a person. | Development agents run with an admin role (S261 review TL-8, deferred until before prod). |
| **LLM07 System prompt leakage** | Prompts live in the public CIS repo, so they hold no secrets by construction (gitleaks scans every commit); the injection samples check for prompt leaks. | None needed while prompts stay secret-free. |
| **LLM08 Vector and embedding weaknesses** | Embeddings cover catalog and place content and traveller search text only, never tenant data; one model (Cohere Embed v4, 1536 dimensions) for every embed stage. | No registry of embedding spaces and no re-embed procedure (S261 review TL-14, deferred). |
| **LLM09 Misinformation** | Jev grounding plus the numeric check on S1 sentences; judge and audit stages; two-model place card and dedupe checks; flagged map pins hidden (AA-997); AI labels on TripPlanner and the portal notice at review, publish and export; human review before serving (A2, tenant, advisor). | Judges are not calibrated (kappa 0.562 on 13 pairs); a judge becomes a gate only after at least 30 human-labelled pairs with at least 8 per class (S261 review TL-10, labelling deferred). |
| **LLM10 Unbounded consumption** | Connection monthly budgets; job caps with hard stop (`shared/cost_guard.py`, `shared.spend_budget`); TripPlanner daily cap with a degrade mode; CRM per-agency budget; writing-memory eval cap 25 USD a month; AWS budgets and cost anomaly alerts per account (AA-896). | Most writer stages still have only the connection budget (no per-stage cap); the tenant budget has no amounts until the business owner sets plan prices; route deadlines are unset. Closed in S262: Jev pre-call cap (318), TripPlanner fail-closed and per-visitor limits (tp-023), tenant budget (321), connection circuit and re-queue (AA-1018). |

## Change log

| Version | Date | Change |
|---|---|---|
| v1.13 | 09/11/2026 (S274, AA-820) | Records CIS 383 (route control version 7, applied 06/11): no OpenAI writer rung, no Nova Lite judge or instrument rung (the other validate rows keep theirs); 383 wins over the row chains it names; provider list for the tenant terms corrected; CIS 385 reply store noted. No new route change. |
| v1.12 | 06/11/2026 (S271, AA-820) | The AA-Partner Content studio terms and privacy pages moved to Draft v0.5 (EN and VI): Claude models write and may also check, the direct Anthropic API and OpenAI API are providers that may process the content (not a fallback), Amazon Nova / Meta Llama may also review and check, an OpenAI model may write as a last resort; AA may change the order without notice, adding or replacing a provider follows the DPA notice (6.2). Closes the v1.11 open item. Terms-wording notes of the provider list and the T-stage narrative follow. No route change. |
| v1.11 | 06/11/2026 (S271, AA-820) | Route control version 6 written down (S269, AA-1042): the Anthropic API first for every Claude model, acc3 second; the OpenAI API answers the GPT judges, audits and checks while acc3 refuses (deferred refused rungs, CIS #1332). Rows name each Claude model's providers in that order; provider list for the tenant terms no longer calls the direct APIs fallbacks only; open item: the AA-Partner Content studio terms and privacy pages. No route change. |
| v1.10 | 05/11/2026 (S269, AA-1042) | CIS 376: every Claude model of the Anthropic API key is in the gateway catalog with an Anthropic API deployment behind AWS (Fable 5.1 / 5, Opus 5 / 4.8 / 4.7 API only; Opus 4.6 / 4.5 switched on; Sonnet 4.6 / Haiku 4.5 now on acc3 and the API). The 18 rows whose chains changed to keep six attempts per request: each drops its lowest Claude rung (tp_compose its OpenAI API rung). No stage routes Sonnet 5, Opus or Fable. |
| v1.9 | 05/11/2026 (S269, AA-820) | CRM row corrected: Dev drafts run on Amazon Nova Lite on acc2 through a `us.` profile since AA-1027 F4 (AA-Partner crm-042, AA-CIS-Infra `crm_llm.tf`, root ADR 0009 decision 14 amendment), not the stub; the DPA draft v0.2 cross-reference in the provider list. No route change. |
| v1.8 | 04/11/2026 (S267, AA-1026) | Tech lead decisions S267: AWS preferred, not AWS only (every active text stage `vendor_direct`, CIS 366); model first (the same model on its vendor API before the next model; GPT-6 Luna's OpenAI API twin right behind it on every GPT route); one Anthropic API key (150 USD a month) and acc3 capped at 100 USD a month, hard stops enforced by the CIS gateway only (TripPlanner counted, not stopped; CRM outside); provider list for tenant terms widened (AA-820 follow-up); TripPlanner view gap noted. |
| v1.7 | 04/11/2026 (S267, AA-1026) | Family fallback chains (CIS 366): Claude Sonnet 4.6 / Haiku 4.5 Converse rows behind their 5.5 siblings; first fallbacks for `tp_compose` and `segment_research*`. Order superseded by v1.8. |
| v1.6 | 03/11/2026 (S266, AA-1040) | Marking gaps closed: catalog tour JSON (`Tour.ai` in catalog.http.v1 1.3, TripPlanner browse Lambda cards and detail; `generated_at` from `v_tour.text_updated_at`, CIS 359) and the Booking supply text row (CIS 358 view columns, Booking `content.ai` / `supply.ai`, "AI-assisted" badge). Coverage limits rewritten. No route change. |
| v1.5 | 03/11/2026 (S266, AA-1040) | Machine-readable marking (EU AI Act Art. 50): per-surface stored and delivered marks, notices, publish-channel AI labels. The AI Schedule facts table points here. No route change. |
| v1.4 | 03/11/2026 (S266, AA-820) | Tenant-terms note: the AI Schedule v1.0 and where each app page summarises it; direct API accounts in the AA company name (ADR 0019 b19). No route change. |
| v1.3 | 03/11/2026 (S265, AA-1020) | `a3_place_dedupe`: Llama 4 Maverick (acc2) before the OpenAI API hop (CIS 339, live since S264); the acc2 models row, section and tenant-terms note follow. |
| v1.2 | 02/11/2026 (S264) | Tenant writer stages (`t2_generate`, `t2_flag_fix`, `t2_itinerary_nudge`, `t8_angle_gen`, `t9_write`, `t9_repair`) `vendor_direct` with GPT-6 Luna on the OpenAI API as the last rung (CIS 344, tech lead S264; ADR 0009 decision 5 amendment); tenant-terms provider list: an OpenAI model may write as a last resort. |
| v1.1 | 02/11/2026 (S263 close) | acc2 Bedrock fallback for judge and validate stages (CIS 331–333; Nova Lite, Llama 4 Scout on `a3_place_card_check`; AWS first, vendor APIs last); `a3_place_dedupe` open; tenant-terms provider list; the A-series writer scope note now cites CIS 327 (was 335 by mistake). |
| v1 | 01/11/2026 (S263, AA-1020) | Gateway v2 as built: ledger v2 for CIS, TripPlanner and the CRM; Jev and DataForSEO caps (318); tenant budget (321); provider registry rows (322); TripPlanner contract views (323); acc2 candidate models (324); Bedrock Batch, probe and CRM guard rows; circuit, deadline and re-queue as switches; LLM10 gaps updated. Routes unchanged since the 29/10 snapshot. |
| v0 | 31/10/2026 (S262) | First version: 37 routed stages of the 29/10 route snapshot, `t10_adjudicate` (CIS migration 309), Jev, DataForSEO, the geocoder, the CRM stub; OWASP LLM Top 10 (2025) map. Draft until the tech lead has read it. |
