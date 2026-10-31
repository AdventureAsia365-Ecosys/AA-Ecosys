---
id: APP-06-ai-register
title: "AI Use Register"
description: "Every AI and paid-data stage of the ecosystem with its owner role, provider, data scope, budget, kill switch, eval and human gate, and the OWASP LLM Top 10 (2025) map of existing controls and gaps. v0."
type: reference
status: draft
owner: nghiep
audience: [engineer, cto, cio, agent]
applies_to: [ecosystem, aa-cis-api, aa-cis-worker, tripplanner-lambda, aa-crm-api]
last_reviewed: 2026-10-31
review_every_days: 30
related: [APP-06-routes, APP-06-eval, APP-06-prompts, ARCH-08, docs/adr/0009-ai-platform-and-provider-gateway.md, AA-804, AA-820]
---

# AI Use Register (v0)

One row per place where the ecosystem calls an AI model or a paid data provider. It answers, for each stage: what it
is for, who owns the decision to change it, which provider and model family serve it today, which data may leave AWS,
whether tenant data is in the prompt, what caps its spend, how it is switched off, how a change is evaluated, and
which human checks the output before anyone relies on it.

- **Why it exists:** [ADR 0009](../adr/0009-ai-platform-and-provider-gateway.md) (AI platform and provider gateway,
  decisions 1–9, 13 and 14 accepted 31/10/2026) and the S261 architecture review item TL-15. The tenant terms and the
  partner-portal privacy notice take their provider list from this page (AA-820).
- **v0 limits:** written by hand from the code on `main` (31/10/2026) and the route snapshot of 29/10/2026. Routes
  change by configuration, so the [generated route table](../generated/llm-routes.md) (`APP-06-routes`, from
  `shared.llm_role_config` and `shared.llm_model_catalog`) wins for the model of a stage. v1 adds what ADR 0009
  builds: one stage profile per app with its own budget and kill switch (decisions 4 and 6), ledger v2 columns
  (decision 8) and the CRM stages read from `crm.ops.v1`.
- **Who updates it:** the PR that adds, removes or re-routes a stage, adds a provider, or changes a stage's data
  scope, budget or human gate updates its row. A new provider also updates the tenant terms list (AA-820).

## How to read the columns

| Column | Meaning |
|---|---|
| Owner role | Who decides a change. **Tech lead**: writer stages and anything tenant-facing (a route switch on a main writer stage needs the tech lead's yes, ADR 0009 decision 12). **Engineer on duty**: extraction, validate and embed stages, which an engineer may re-route after the eval in the [eval runbook](https://github.com/AdventureAsia365-Ecosys/AA-CIS-App/blob/main/docs/llm/eval-runbook.md) and report after the fact. Roles, never names. |
| Provider / family today | Primary model, then fallbacks, from the route table. "Bedrock (acc3)" = Amazon Bedrock in the LLM account; "OpenAI API" = the OpenAI platform API outside AWS; "acc2" = Bedrock in the infrastructure account. Families: Anthropic (Claude Sonnet 4.6 / 5.5, Haiku 4.5), OpenAI (GPT-5.6 Luna, GPT-6 Luna), Cohere (Embed v4). |
| Data scope | From `shared.llm_role_config.allowed_scopes` (CIS migration 311, `shared/llm_client/data_scope.py`): `aws_only` = the stage's content may only go to connections inside AWS; `vendor_direct` = it may also reach a vendor API outside AWS. Every CIS stage whose route names a model reachable only outside AWS (`gpt-6-luna-openai`) is `vendor_direct`; every other stage is `aws_only`. |
| Tenant data | Yes when the prompt carries a tenant's brand settings, briefs or tenant-written text. Traveller input is noted separately. |
| Budget source | What stops spend today. **Connection** = `shared.llm_provider_connection.monthly_budget_usd` (every CIS and TripPlanner call). **Job cap** = a `shared.spend_budget` row (provider × `job:<kind>`) that the job loads with `shared/cost_guard.py` before each call. "Connection only" means no per-stage or per-job cap exists yet (ADR 0009 decision 6 closes this). |
| Kill switch | What turns the stage off without a deploy of new code. Today there is **no per-stage switch in the gateway**: `is_active = false` on a route row makes the code fall back to its built-in default route (`SAFE_DEFAULTS`), it does not stop calls. The switches that exist are the connection `enabled` flag (all stages on that connection), a hard-stop budget row, and the feature flags named per row. |
| Golden set / eval | How a prompt or route change is measured ([eval runbook](https://github.com/AdventureAsia365-Ecosys/AA-CIS-App/blob/main/docs/llm/eval-runbook.md)): **R2** = a run on the frozen AA-729 golden set (`shared.eval_golden_set`) for writers `a1`, `t2`, `t9_blog`, `t9_social`; **Q2** = judge re-score; otherwise the baseline named in the CIS prompt register. |
| Human gate | Who checks the output before it is published, served or relied on. |

## Register

### CIS: A-series (platform content, AA's own catalog)

| Stage | App | Purpose | Owner role | Provider / family today | Data scope | Tenant data | Budget source | Kill switch | Golden set / eval | Human gate |
|---|---|---|---|---|---|---|---|---|---|---|
| `a0_column_map` | CIS | Map unknown Excel columns of a supplier import to tour fields | Engineer on duty | Haiku 4.5, Bedrock (acc3) / Anthropic | aws_only | No | Connection only | Connection `enabled` | Prompt register baseline | Import is reviewed in the A-series pipeline (A1/A2) before anything is served |
| `s1_generate` | CIS | A1 rewrite of a catalog tour (the Master writer) | Tech lead | Sonnet 5.5, Bedrock (acc3) / Anthropic; no fallback in the route | aws_only | No | Connection only (wave runs carry their own cost report) | Connection `enabled` | R2 `a1` | A2 review before the Master is served (review queue) |
| `s1_judge` | CIS | Score an S1 draft against the rubric | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3) → GPT-6 Luna (OpenAI API) / OpenAI | vendor_direct | No | Connection only | Connection `enabled` | Q2; judge not calibrated yet (kappa 0.562 on 13 pairs, candidate only, S261 review TL-10) | A2 review |
| `s1_brand_audit` | CIS | Brand and fact audit of an S1 draft | Tech lead | GPT-5.6 Luna → GPT-6 Luna, Bedrock (acc3) / OpenAI | vendor_direct | No | Connection only | Connection `enabled` | Q2 | A2 review |
| `s1_flag_fix` | CIS | Repair the sentences the checks flagged | Tech lead | Haiku 4.5, Bedrock (acc3) / Anthropic | aws_only | No | Connection only | Connection `enabled` | R2 `a1` (part of the graph) | A2 review |
| `s1_itinerary_nudge` | CIS | Fix itinerary structure in an S1 draft | Tech lead | Haiku 4.5, Bedrock (acc3) / Anthropic | aws_only | No | Connection only | Connection `enabled` | R2 `a1` (part of the graph) | A2 review |
| `s1_source_facts` | CIS | Extract per-day source facts for the writer | Engineer on duty | GPT-6 Luna → Haiku 4.5, Bedrock (acc3) / OpenAI, Anthropic | aws_only | No | Connection only | Flag `S1_STRUCTURED_FACTS` (env or tenant flag, default off) | Prompt register baseline | A2 review |
| `s1_grounding` (Jev) | CIS | Ask Jev whether each sentence is supported by the source (`a1_claim_supported`) | Tech lead | Jev (TypeSafe), decision API outside AWS | Jev connection (outside AWS) | No | None before the call today (Jev has no pre-call budget; ADR 0009 first slice adds one) | Question mode off / shadow / enforce (`decision_question`, CIS ADR 0007); Jev failing never blocks | Jev verdicts act only when enforced and calibrated (CIS ADR 0007) | A2 review; unsupported claims go to manual check |
| Other Jev `decide` questions | CIS | Typed yes/no questions in debate, claim rules, trip facts, atom ranking, segment matching, tenant pipeline (`shared.decision_log`) | Engineer on duty | Jev (TypeSafe) | Jev connection; tenant questions only for allowlisted tenants | Some (tenant pipeline, allowlisted tenants only) | None before the call today | Per-question mode (off / shadow / enforce) | Per question (CIS ADR 0007) | As the calling stage |
| `s1_atom_writer` | CIS | Route kept for atom writing; **no caller found on `main`** | Engineer on duty | Sonnet 4.6, Bedrock (acc3) / Anthropic | aws_only | No | Connection only | Connection `enabled` | None | None (not called) |
| `a3_atomize` | CIS | Cut a Master tour into atoms (A3) | Engineer on duty | GPT-6 Luna → Haiku 4.5, Bedrock (acc3) / OpenAI, Anthropic | aws_only | No | Connection only | Connection `enabled` | Offline A/B of S224 (prompt register) | None per item; atoms are curated in the admin atom pages |
| `a3_place_days` | CIS | Day skeleton of places for a tour | Engineer on duty | Haiku 4.5 → Sonnet 4.6, Bedrock (acc3) / Anthropic | aws_only | No | Job cap `bedrock` × `job:place_extract` (per day of that kind) | Connection `enabled`; budget hard stop | S246 place model trial | None per item |
| `a3_place_locate` | CIS | Name and locate places from tour text | Engineer on duty | Sonnet 4.6 → Haiku 4.5, Bedrock (acc3) / Anthropic | aws_only | No | Job cap `bedrock` (place geocode job) | Connection `enabled`; budget hard stop | S247 trial | None per item; flagged pins can be hidden (AA-997) |
| `a3_place_card` | CIS | Draft a place card from web-sourced facts | Engineer on duty | GPT-6 Luna → GPT-5.6 Luna, Bedrock (acc3) / OpenAI | aws_only | No | Connection only | Connection `enabled` | AA-784 blind eval (S252) | Two-model check (`a3_place_card_check`, another maker) |
| `a3_place_card_check` | CIS | Fact-check the place card draft | Engineer on duty | Haiku 4.5 → Sonnet 4.6, Bedrock (acc3) / Anthropic | aws_only | No | Connection only | Connection `enabled` | AA-784 blind eval | None per item |
| `a3_place_dedupe` | CIS | Decide whether two places are the same | Engineer on duty | GPT-6 Luna (Bedrock acc3) → GPT-6 Luna (OpenAI API) / OpenAI | vendor_direct | No | Job cap `bedrock` × `job:place_dedupe` | Connection `enabled`; budget hard stop | S234 identity A/B | Two-model check (`a3_place_dedupe_check`) |
| `a3_place_dedupe_check` | CIS | Second opinion on a merge | Engineer on duty | Haiku 4.5, Bedrock (acc3) / Anthropic | aws_only | No | Job cap (as above) | Connection `enabled` | S234 identity A/B | None per item |
| `a3_place_embed`, `f10_embed` | CIS | Embeddings of places and content for search and similarity | Engineer on duty | Cohere Embed v4, Bedrock acc2 → acc3 / Cohere | aws_only | No | Connection only | Connection `enabled` | None (deterministic use) | Not applicable |
| `supply_content_writer` | CIS (for Booking) | Customer description and highlights of a Booking hotel or service, from staff-entered facts treated as untrusted data | Tech lead | Sonnet 5.5 → Sonnet 4.6, Bedrock (acc3) / Anthropic | aws_only | No | Job cap `bedrock` × `job:supply_content_draft` (per day of that kind) + `SUPPLY_CONTENT_MAX_DRAFTS_PER_DAY` | Flag `SUPPLY_CONTENT_LLM=off` | None | Booking staff review each draft before Booking shows it |
| `writing_memory_mine`, `writing_memory_eval` | CIS | Draft writing-memory rules from edits; eval judge of the R2 runner | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3) → GPT-6 Luna (OpenAI API) / OpenAI | vendor_direct | Possible: writing memory has tenant-scoped rows (CIS ADR 0010) | Job cap `bedrock` × `writing_memory_mine`; eval runs: 25 USD a month over every writing-memory stage (`MONTH_CAP_USD`) | Per-writer memory switch and release activation (CIS ADR 0010) | R2 itself | Release activation by staff (CIS ADR 0010) |
| DataForSEO (`data`) | CIS | Keyword volumes, SERP and question research for tours and segments | Engineer on duty | DataForSEO API, outside AWS | Keywords and place names only | No | Job cap `dfs` (a global day cap, seeded 10 USD/day, plus per-job rows: segment research, S1 SEO prefetch, question top-up) | Budget hard stop | Not applicable | Not applicable |
| Geocoder (`data`) | CIS | Geocode and shape places (`services/places/geocoder.py`) | Engineer on duty | External geocoder, outside AWS (`geo.geocode_call`) | Place names only | No | Job cap `geocoder` (place geocode, relocate, shape jobs) | `PLACE_SHAPES_ENABLED` (shape job, default off); budget hard stop | AA-997 accuracy audit | Flagged pins hidden (AA-997) |

### CIS: T-series (tenant content, Content studio)

T-series stages are `aws_only` for writers until the tenant terms cover more (AA-820, ADR 0009 decision 5). The
judge stages below are `vendor_direct` because their route ends at the OpenAI API, so tenant content can reach the
OpenAI API when both Bedrock judge models fail. The tenant terms state this as "may be used as a fallback".

| Stage | App | Purpose | Owner role | Provider / family today | Data scope | Tenant data | Budget source | Kill switch | Golden set / eval | Human gate |
|---|---|---|---|---|---|---|---|---|---|---|
| `t2_generate` | CIS | T2: rewrite a catalog tour in the tenant's brand voice | Tech lead | Sonnet 4.6, Bedrock (acc3) / Anthropic | aws_only | Yes (brand settings) | Connection only (tenant budget: AA-1016, not built) | Connection `enabled` | R2 `t2` | Tenant reviews and exports; AI notice at review, publish and export |
| `t2_judge`, `t2_brand_audit` | CIS | Score and audit a T2 rewrite | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3) → GPT-6 Luna (OpenAI API, `t2_judge` only); 10 % shadow on GPT-6 Luna / OpenAI | vendor_direct | Yes | Connection only | Connection `enabled`; brand claim check `T2_BRAND_CLAIM_CHECK=off` | Q2 | Tenant review |
| `t2_flag_fix`, `t2_itinerary_nudge` | CIS | Repair flagged T2 sentences and itinerary structure | Tech lead | Haiku 4.5, Bedrock (acc3) / Anthropic | aws_only | Yes | Connection only | Connection `enabled` | R2 `t2` (part of the graph) | Tenant review |
| `t7_debate_judge` | CIS | Brand-fit call of the T7 debate | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3) → GPT-6 Luna (OpenAI API); 10 % shadow | vendor_direct | Yes | Connection only | Connection `enabled` | Q2 | Tenant review |
| `t8_angle_gen` | CIS | Propose content angles for a tenant brief | Tech lead | Sonnet 4.6, Bedrock (acc3) / Anthropic | aws_only | Yes | Connection only | Connection `enabled` | Prompt register baseline | Tenant picks the angle |
| `t9_write` | CIS | T9: blog and social pieces about a tour | Tech lead | Sonnet 4.6, Bedrock (acc3) / Anthropic | aws_only | Yes | Connection only | Connection `enabled` | R2 `t9_blog`, `t9_social` | Authenticity check (no reviews, testimonials, first-person customers, independence claims); tenant reviews and presses publish (T10/T11) |
| `t9_repair` | CIS | Sentence repair, SEO fit and the admin sentence suggest | Tech lead | Haiku 4.5 → Sonnet 4.6, Bedrock (acc3) / Anthropic | aws_only | Yes | Connection only | Connection `enabled` | Prompt register baseline | Tenant review |
| `t9_faq_filter`, `t9_faq_answer_fit` | CIS | Filter real search questions for the blog FAQ; check each answer fits | Engineer on duty | Haiku 4.5 / Sonnet 4.6, Bedrock (acc3) / Anthropic | aws_only | Yes | Connection only | Flag `T9_FAQ_LLM_FILTER` (default off) | S247 trial | Tenant review |
| `t10_judge` | CIS | T10 gate: score a T9 piece | Tech lead | GPT-5.6 Luna → GPT-6 Luna (Bedrock acc3) → GPT-6 Luna (OpenAI API) / OpenAI | vendor_direct | Yes | Connection only | Connection `enabled` | Q2 | Tenant review |
| `t10_adjudicate` | CIS | T10 tier-2 adjudicator of the writer's sentences | Tech lead | GPT-6 Luna → GPT-5.6 Luna (Bedrock acc3) → GPT-6 Luna (OpenAI API) / OpenAI | vendor_direct | Yes | Connection only | `T10_ADJ_MODE` (default off) | None yet | Tenant review |
| `t10_claims` | CIS | F9 v2 claim extraction; **not wired into the gates** (no caller on `main`) | Engineer on duty | GPT-6 Luna → GPT-5.6 Luna, Bedrock (acc3) / OpenAI | aws_only | Yes (when wired) | Connection only | Connection `enabled` | Replay before wiring | Not applicable yet |

### TripPlanner (travellers, no sign-in needed)

| Stage | App | Purpose | Owner role | Provider / family today | Data scope | Tenant data | Budget source | Kill switch | Golden set / eval | Human gate |
|---|---|---|---|---|---|---|---|---|---|---|
| `tp_compose` | TripPlanner | Narrate and re-narrate a traveller's trip | Tech lead | Sonnet 4.6, Bedrock (acc3) / Anthropic; no fallback | aws_only (TripPlanner reads only the routes) | No; **traveller free text** can be in the prompt (no automated scrub yet, ADR 0009 "Not decided here") | `TP_DAILY_SPEND_CAP_USD` (default 5 USD/day over the online stages, `tripplanner.llm_spend_daily`); it fails open when the counter cannot be read until the S262 fail-closed fix ships | Over the cap the site serves basic narration (degrade mode) | None | AI label on the site and on AI narration; an Adventure Asia advisor reviews every itinerary before booking |
| `tp_search_embed` | TripPlanner | Embed the traveller's search text | Engineer on duty | Cohere Embed v4, Bedrock acc2 → acc3 / Cohere | aws_only | No; traveller search text | Same daily cap | Same degrade mode | None | Not applicable |
| `tp_extract`, `tp_component_embed` | TripPlanner | Routes kept for the old place extraction and embedding; **no caller found on `main`** (the place pipeline moved to CIS `a3_*`, AA-712) | Engineer on duty | Sonnet 4.6 / Cohere Embed v4 | aws_only | No | Logged only (offline stages are outside the daily cap) | Connection `enabled` | None | None (not called) |

### AA-Partner CRM and AA-Booking

| Stage | App | Purpose | Owner role | Provider / family today | Data scope | Tenant data | Budget source | Kill switch | Golden set / eval | Human gate |
|---|---|---|---|---|---|---|---|---|---|---|
| `crm_*` (gateway stub) | CRM | Reply drafts for agencies (card CRM-33a); **only a stub provider today, no real model is called** | Tech lead | Stub (no network). Planned: Bedrock only, never OpenAI or Jev (root ADR 0008a §5–6) | Bedrock only | Yes: the agency's own client data, scrubbed first (F3: known values, regex, Bedrock Guardrails in acc2 detect mode) | Per agency `crm.tenant_settings.ai_budget_usd` (default 2 USD a month), refused at 100 % | `ai_enabled` per agency (default false) | None yet | Every draft is shown to an agency member, who sends it by hand |
| None | Booking | Booking makes no AI calls. Hotel and service text is drafted by CIS (`supply_content_writer`) | — | — | — | — | — | — | — | High-risk advice rule in Booking `CONTEXT.md` (AA-820): no AI advice on insurance, financing, claims or visas without qualified staff review and AI disclosure |

### Providers, for the tenant terms (AA-820)

What the tenant terms and the partner-portal privacy notice name, derived from the rows above:

- **Anthropic (Claude), through Amazon Bedrock**: every writer stage.
- **OpenAI models, through Amazon Bedrock**: judge, audit and extraction stages that score or check drafts.
- **Cohere (Embed v4), through Amazon Bedrock**: search embeddings of catalog content.
- **Direct Anthropic API and direct OpenAI API**: warm fallback paths outside AWS with a monthly cap (ADR 0009
  decisions 5 and 14). In the 29/10 route snapshot only judge and dedupe routes end at the OpenAI API, and no route
  names an Anthropic API model yet (the writer warm path is approved, its routing is a later gateway step). Terms wording: "may be used as a fallback".
- **Jev (TypeSafe)**: yes/no decision checks; for tenant content only for allowlisted tenants.
- **DataForSEO, the geocoder**: keywords and place names only, never tenant text.

## OWASP Top 10 for LLM Applications (2025): controls and gaps

Controls are cited only where they exist in code or configuration on `main` (31/10/2026). Gaps name the ADR 0009
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
| **LLM10 Unbounded consumption** | Connection monthly budgets; job caps with hard stop (`shared/cost_guard.py`, `shared.spend_budget`); TripPlanner daily cap with a degrade mode; CRM per-agency budget; writing-memory eval cap 25 USD a month; AWS budgets and cost anomaly alerts per account (AA-896). | Budgets are opt-in per caller (most writer stages have only the connection budget); Jev has no pre-call budget; the TripPlanner cap fails open; no Content studio tenant budget (AA-1016). ADR 0009 decision 6 and its first slice close these. |

## Change log

| Version | Date | Change |
|---|---|---|
| v0 | 31/10/2026 (S262) | First version: 37 routed stages of the 29/10 route snapshot, `t10_adjudicate` (CIS migration 309), Jev, DataForSEO, the geocoder, the CRM stub; OWASP LLM Top 10 (2025) map. Draft until the tech lead has read it. |
