---
id: OPS-08-s261-llm-gateway-readiness
title: "LLM gateway: per-stage routing, model readiness per source, observability vs Langfuse, test-first plan (S261)"
description: "Nghiên cứu chỉ đọc code: gateway chọn model cho từng stage thế nào, model nào sẵn sàng theo acc2/acc3/API trực tiếp, quan sát so với Langfuse, và kế hoạch kiểm thử model acc2 không đổi route."
type: report
status: active
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1002, AA-642, AA-842]
---

# LLM gateway: định tuyến theo stage, model sẵn sàng, quan sát (S261, 31/10/2026)

Tác nhân: Claude Code (workflow 6 agent, chỉ đọc code: CIS `1b6e9448`, TripPlanner `02dd9f1`, Partner `d29e29e`).
Tech lead chốt S261: **chưa chuyển route nào, kiểm thử trước.** Bản tóm tắt tiếng Việt cho tech lead nằm trong
tin nhắn phiên; dưới đây là nguyên văn các phần nghiên cứu (tiếng Anh).

## Năm điều chính (kiểm chéo)

**1. Parts of his question not fully answered**
- **Is the gateway ready, yes or no.** No output answers this in one line. The answer is no. Every text stage fails today. Only Cohere Embed on acc2 works. acc3 is blocked, openai-direct has no credit (429), and anthropic-direct is disabled with no key. The outputs also don't say what fixes each source: topping up OpenAI credit, creating the `aa-llm/dev/anthropic-direct` secret plus `vendor_direct` scopes, or a migration for acc2.
- **Which model families are feasible.** The research covers only Nova, Llama 4, Kimi K3, GLM and Grok. These are not assessed:
  - other acc2 Bedrock families: Mistral, DeepSeek, Qwen, Cohere Command, AI21;
  - direct-API sources other than Anthropic and OpenAI, such as Gemini;
  - price, latency or quality for any candidate. No prices are in the repo, so no cost comparison is possible yet.
- **What a stage can customise beyond model choice.** Not stated. The facts from the outputs: temperature, max tokens and prompts are set by each call site in code, and `role_config` has no per-stage parameters. `request_defaults` is per deployment and is ignored by Converse.
- **Live state is not verified.** Routes come from the 30/10 snapshot, the `LLM_*` env values were not checked against the live task definition, and "acc2 provider works" for Nova, Llama and Kimi rests on the 31/10 access matrix, not a gateway call.
- **Monitoring of the other apps.** Covered (TripPlanner and CRM). There is no plan for a single view across the three apps beyond the AA-804 `app` column.

**2. Unsupported claims or contradictions**
- **acc2 cost attribution (the most important conflict).**
  - INVENTORY: "Pricing and logging work... `llm_call_log` records `provider=bedrock`, `account=acc2`."
  - ROUTING and PLAN: "acc2 Converse replies carry neither `satellite_account` nor `connection_key`... acc2 chat rows get `account=NULL`" (`client.py:1370-1378` / `:1375`).
  - PLAN adds that the Test button logs `account=connection_key`, so only real `generate()` calls are affected.
  - Treat the bug as real until a unit test settles it. Also check which account today's Cohere embed rows log.
- **Scope of "acc3 Claude only".**
  - ROUTING: "all 20 live stages (18 CIS + 2 TripPlanner) have only acc3 Claude behind them."
  - INVENTORY: "16 CIS + 2 TP stages" use `haiku`/`sonnet` as primary. Many other stages use GPT on Bedrock on acc3 (gpt-5.6-luna, gpt-6-luna), with gpt-6-luna-openai as last fallback through openai-direct.
  - So "only acc3 Claude" holds only for the legacy-key stages, and the count of 18 vs 16 is unresolved.
- **Enable state of the new rows.**
  - ROUTING §13: migration adds catalog `enabled=false` and deployment `enabled=false`.
  - PLAN PR-3: catalog `enabled=false` and deployment enabled.
  - Both say the Test button works on rows that are switched off. Pick one.
- **What the gateway writes itself.**
  - ROUTING: "the gateway writes only billed-but-unusable rows."
  - OBSERVABILITY: it also writes shadow cost rows (`shadow.py:42-50`). Minor.
- **A second CHECK may need widening.** APPS says `provider_check` (schema ref L8147) must also be widened. No other output mentions it, so verify before writing PR-3.
- **TripPlanner IAM line ranges differ** (L64-74 and L330-337 vs 331-336). Cosmetic.

**3. The five facts he must hear**
1. **Nothing generates text today.** Every stage's primary and most fallbacks sit on acc3 (Claude and GPT-on-Bedrock), which is blocked. openai-direct has no credit and anthropic-direct is off. Only embeddings work, through Cohere on acc2.
2. **The routing mechanism exists and can be set per stage.**
   - Each stage has one row in `shared.llm_role_config`: a primary model, ordered fallbacks and an optional shadow. These are editable in Admin › Settings › Models.
   - Each model is tried on its deployments in priority order, filtered by data scope, circuit breaker and connection budget.
   - Two gaps: the legacy `haiku`/`sonnet` keys bypass all of this and go to a hard-coded acc3 chain, and several code paths pin `model_tier`.
3. **Nova, Llama and Kimi are not in the gateway yet.**
   - Adding them needs a migration to widen the vendor CHECK, plus catalog and deployment rows.
   - Writer stages are locked to Anthropic models by an admin rule, and changing that needs an ADR.
   - TripPlanner needs a Terraform IAM change. The CRM gateway is still a stub.
4. **Testing first is possible without changing any route.** Add the rows switched off, then use the Test button, ad-hoc `model_tier` calls and `judge_compare --account acc2`. Shadow cannot be used while the primaries are blocked. Before any paid call, fix two things:
   - acc2 account attribution, otherwise test spend is invisible to the budget;
   - Kimi reasoning and the `max_tokens` floor, otherwise its calls return empty and are billed as unusable.
5. **Observability is not Langfuse-level.**
   - Cost tracking is strong: per call, reconciled against the provider bill, with budgets, breaker health and a daily digest.
   - Missing: latency, a trace or span tree, prompt and output capture, rows for refused calls (in CIS), and a per-job view in the UI.
   - The Langfuse code in the repo is dead.
   - Recommendation: build it in-house (one migration plus gateway code, about 2–3 days, $0 infrastructure). Self-hosted Langfuse comes later (about $60–150 a month), and Langfuse Cloud is ruled out by ADR 0012 and the CRM policy.

## Kế hoạch kiểm thử không đổi route

# Test-first plan: qualify the acc2 non-Claude models without changing any route (S261, 31/10)

Code read at CIS `1b6e9448`. I made no edits, AWS calls, DB calls or LLM calls. Paths are relative to `apps/AA-CIS-App` unless a path says otherwise.

## 0. Which test paths work while acc3 is blocked

| Path | Works today? | Why |
|---|---|---|
| Admin › Connections › **Test** (`api/services/llm_connections.py:398-460`) | **Yes**, once the rows exist | It works on a switched-off deployment. `probe` takes the model object directly. It logs one `adhoc_conn_test` row with `account=connection_key` (`:449-452`). It caps output at 32 tokens (`:369`), so **Kimi K3 will report "unusable"**. That result is expected and proves the reasoning issue. |
| Ad-hoc `LLMClient.generate(model_tier=<key>, stage='adhoc_<issue>')` | **Yes**, once the catalog row is enabled | One model, no route, no fallback, no shadow. Two conditions: `_call_catalog_model` refuses a disabled catalog row (`shared/llm_client/client.py:1087`), and `deployment_plan` keeps only enabled deployments. |
| `scripts/aa919/judge_compare.py` (judge vs golden labels, kappa per model) | **Needs a one-line change** | Hard-coded `ACCOUNT = "acc3"` (`:51`) and `account_for(ACCOUNT) != ACCOUNT` (`:71`). Everything else fits: it uses the `model_tier` override (`services/writing_memory/eval_judge.py:336-352`), runs as DRY RUN by default, has a `--max-usd` cap and a hard $5 limit (`:54`), and logs to `adhoc_aa919`. |
| `scripts/aa729/score.py` (S1/T2/T9 graph, score-only or regenerate) | **No, as is** | `evalpatch` keeps routing ("the real stage still picks the model"), so the S1 judges run on the acc3 routes. S1 score-only also pins `state["model_tier"]="haiku"` (`score.py:246`), which goes to the legacy acc3 chain. It needs an in-process per-stage model override. |
| R2 runner (`services/writing_memory/r2.py`) | **No** | Its judge is the `writing_memory_eval` route (gpt-5.6-luna on acc3). The A1 writer uses `model_tier=None` (`eval_writers.py:133`). |
| Shadow | **No** | It runs only after the primary succeeds (`client.py:619-621`), and every primary is on acc3. Writer shadows must also be Anthropic models (`api/routers/admin_llm_ops.py:386-410`). |

**Route guard for every step:** take a snapshot of `shared.llm_role_config` (stage, model_id, fallback_model_ids, shadow_model_id) before and after. The two must be identical. Do not change any `LLM_*` env value (`LLM_LEGACY_ALIASES` stays off). No stage names the new keys, and neither do `SAFE_DEFAULTS` (`shared/llm_client/role_config.py:82-188`) or the aliases (migration 307).

## 1. Code and data changes: small PRs, $0, the agent can do them now

1. **PR-1: fix account attribution in the gateway (CIS).** `client.py:1375` returns `satellite_account=None if native else account`. Every acc2 Converse reply therefore logs `account=NULL`. Any test spend would then be invisible to the acc2 budget (`connection_budget.py`), per-connection cost and reconcile, because spend is summed by `llm_call_log.account` in `shared/cost_guard.py:327-333`.
   - Fix: set `account`/`connection_key` = `acc2` for task-role deployments and keep `provider="bedrock"`.
   - Unit test: an acc2 Converse response carries `account='acc2'`.
   - This must merge before any paid call.
2. **PR-2: reasoning control and tool-choice handling on Converse (CIS).**
   - **Reasoning:** Converse never sends `additionalModelRequestFields` (`client.py:1256-1258`) and ignores `deployment.request_defaults`. Pass an allow-listed `request_defaults.additional_model_request_fields` from the deployment. Take Kimi K3's exact reasoning parameter from the Bedrock model docs; do not guess it.
   - **Token floor:** add a minimum `max_tokens` for reasoning models, stored in the catalog `capabilities` jsonb (the column exists from migration 304 but no code reads it). Without it, Kimi's reasoning eats the judge's `MAX_TOKENS=1200` (`eval_judge.py:51`) and returns "empty content" (`client.py:1342`), which is billed as unusable.
   - **Tool choice:** add "does not support" / "doesn't support" to `_tool_choice_rejected` (`client.py:364-369`). A Llama or Kimi rejection worded that way would otherwise fail instead of falling back to `auto`.
   - Unit tests: a reasoning-only reply, and a rejection message in each wording.
3. **PR-3: catalog and deployment rows, as a CIS migration through DB Migrate.**
   - This is a contract change: it alters an existing CHECK. It needs reviewer sign-off and idle job tables, and the `bot/db-schema-reference` PR must be merged afterwards.
   - Widen `llm_model_catalog_vendor_check` (today anthropic/openai/cohere/typesafe, `docs/architecture/db-schema-reference.md:8021`) to add `amazon`, `meta` and `moonshot`.
   - Insert 4 catalog rows with **`enabled=false`**: `provider='bedrock'`, `api_style='converse'`, `callable_via={llm_client}`, `bedrock_profile_ids={"acc2": <wire>}`, a real `max_output_tokens`, `supports_temperature` set from the smoke test, prices, and `price_source`.
   - Insert 4 `llm_model_deployment` rows on `acc2`, **enabled**, with `wire_id` equal to `bedrock_profile_ids.acc2`. The CI guard `tests/integration/test_aa1002_deployment_wire_drift.py` checks this.
   - **Wire IDs:**
     - Nova 2 Lite and Nova Pro: `us.` profiles.
     - Llama 4 Maverick: needs the `us.` inference profile; there is no on-demand ID (`docs/audits/2026-10-31-S261-aws-bedrock-org-access/model-access-matrix-2026-10-31.md`).
     - Kimi K3: the wire ID is in no repo. Read it with a read-only `aws bedrock list-inference-profiles` / `list-foundation-models` on acc2.
   - **Kill switch:** the catalog `enabled` flag, which an admin can toggle in the UI (`shared/llm_client/catalog.py:204`; it is cached for 5 minutes). It is on only during a test window. A deployment of a disabled catalog model is never called, and no route names it.
   - **Prices:** none are in the repo. Take them from the AWS Bedrock price list for the profile and region that will be called. Enabling a row requires a price (CHECK in migration 169).
4. **PR-4: the eval harnesses (CIS `scripts/`, not in the image, $0).**
   - `judge_compare.py`: add `--account acc2` in place of the constant at `:51` and `:71`. Also record each call's latency (harness wall time) in `quality_signal.latency_ms`, because `llm_call_log` has no latency column.
   - `scripts/aa729/evalpatch.py`: add `--stage-model s1_judge=<key>,s1_generate=<key>,…` as an in-process patch that sets `LLMRequest.model_tier` for the listed stages. It must also remap the pinned `haiku`/`sonnet` tiers (`score.py:231, 246`); otherwise flag-fix, grounding repair and revalidate go to acc3. Add the same latency capture.
5. **Acc2 connection limits (data, in the Connections tab, $0).** Set `rpm_limit` and `max_concurrency`, plus `monthly_budget_usd` as **alert only, no hard stop**. A hard stop on acc2 would also stop Cohere Embed (`f10_embed`, `a3_place_embed`, `tp_*_embed`). Read the current acc2 embed spend first.

## 2. Test sequence (paid steps need the tech lead's approval)

**Step A: smoke test.** 4 models × 3 small calls, under the paid-run "trial" rule.
- The calls:
  - the Test button;
  - one call with `json_schema` (the forced tool path);
  - one call at `temperature=0`.
- Pass criteria:
  - a usable reply on each call;
  - the schema parses;
  - an `llm_call_log` row with `account='acc2'`.
- Kimi K3 is retested after PR-2.

**Step B: qualify the judges first.** No writer calls; it re-judges frozen outputs.
- **Tool:** `judge_compare.py` with `--account acc2`. It takes at most 3 models per run, so use two runs: {nova-2-lite, nova-pro, kimi-k3}, then {llama4-maverick}.
- **Writer order:** `t9_social` first (13 labelled pairs, 8 pass / 5 fail in S256), then `a1`, `t2` and `t9_blog`. The DRY RUN prints each writer's pair counts at $0.
- **Gate (existing, unchanged):** kappa ≥ 0.6 on ≥ 10 pairs with ≥ 3 of each label (`services/writing_memory/config.py:59-60`, `eval_checks.py:268-272`).
- **Also report:**
  - recall per label (fail recall matters most);
  - kappa per stratum;
  - JSON validity (rows marked `billed_unusable` ÷ calls);
  - latency p50/p95;
  - cost per pair;
  - agreement with the earlier gpt-5.6-luna runs (kappa 0.316 on `t9_social`, AA-919 notes S256/S257).
- **Proposed extra gates (tech lead to confirm):**
  - 0 unparseable replies after PR-2;
  - repeat agreement ≥ 90% when one model is run twice at `temperature=0`. This checks for the instability AA-339 saw: Nova Pro flipped 17/29 when the order was swapped (`docs/AA339_compare_llm/README.md:75-90`).
- **Pipeline judges** (`s1_judge`, `t2_judge`, `brand_audit`): use `aa729/score.py --mode score-only --strata s1,t2` with `--stage-model`. That is the 50 S1 + 10 T2 frozen outputs; trial 3, then all. Score the agreement of the publish-gate verdict with the golden labels, using the same kappa rule.
- **Validate stages** (`a3_place_*`, `t9_faq_*`, `s1_source_facts`): no labelled set exists. Each stage needs a replay harness against verdicts already stored in app tables. Design it per stage later; it is not in this round.

**Step C: writer A/B.** Only after a judge passes Step B, because the writer is scored by the qualified judge.
- **Tool:** `aa729/score.py --mode regenerate --strata s1` with `--stage-model s1_generate=<candidate>` (plus flag_fix, itinerary_nudge and grounding repair set to the candidate), and the judges set to the qualified acc2 judge.
- **Control:** the frozen fixture outputs, re-judged by the same judge in score-only mode.
- **Candidates:** Kimi K3 and Nova Pro. I would leave Llama 4 Maverick out (AA-339: 0/29 wins against Haiku and Sonnet) unless the tech lead wants it.
- **Judge vendor:** the judge must be a different vendor from the writer (ADR 0010 decision 5). If Kimi writes, Nova judges, and the other way round.
- **Size:** `--limit 3`, then ≤ 50. The S1 stratum is exactly 50 tours.
- **Metrics:**
  - publish-gate pass rate compared with the control;
  - new hard fact classes (unsourced claims, per the writer source-fidelity rule);
  - grounding violations;
  - QA artefacts;
  - brand forbidden words;
  - schema pass;
  - length;
  - latency p50/p95;
  - cost per tour (sum of `adhoc_aa729` rows grouped by `quality_signal.aa729_run`).
- **Pass:** the R2 `non_inferior` definition (new failures − fixed ≤ 0 and new ≤ noise_k, `r2.py` header) with **zero new hard fact classes**.
- Even a passing writer cannot be routed until the admin vendor rule changes (`admin_llm_ops.py:180-183`), and that needs an ADR.
- **Vietnamese:** the golden set is en-US only (`scripts/aa729/select_samples.py:178, 398`), so this round has no Vietnamese quality gate. A Vietnamese set would be a separate small labelled set. TripPlanner is out of scope anyway: its Lambda IAM allows only the Cohere models (`infra/AA-CIS-Infra/accounts/aa365/tripplanner.tf:331-336`).

## 3. How to estimate cost (no figures until prices are in the catalog)

- **Formula:** `calls × (input tokens × price_in + output tokens × price_out) / 1e6`, using the catalog row prices from PR-3.
- **Estimators that already exist:**
  - `judge_compare` DRY RUN: input = characters ÷ 3, expected output 700 tokens, worst case 1,200 (`:55-56`).
  - `score.py --estimate`.
- **Kimi K3:** estimate with output at the raised `max_tokens` floor, because reasoning tokens are billed.
- **After each run:** reconcile against `llm_call_log` (stage `adhoc_aa919` / `adhoc_aa729`, `account='acc2'`, which needs PR-1) and against the S10 Cost Explorer reconcile for acc2.
- **Hard caps already in place:**
  - `judge_compare`: $5 per run;
  - `score.py`: `--max-cost-usd`, default $15 (`scripts/aa729/common.py:33`);
  - R2: $10 per run, $25 per month (`config.py:40, 56`).

## 4. Who decides what

| Item | Cost | Who |
|---|---|---|
| PR-1 (attribution), PR-2 (reasoning and tool choice), PR-4 (harnesses) | $0 | Agent now. PR-1 and PR-2 touch the gateway, so they get an independent review. |
| PR-3 migration (vendor CHECK, rows switched off), plus the read-only lookup of the Kimi wire ID | $0 | Agent now, as a risky PR with a reviewer. DB Migrate runs with job tables idle. |
| Acc2 connection limits and budget alert (data) | $0 | Agent now. Alert only, so embeddings are never stopped. |
| Route snapshot before and after | $0 | Agent now |
| Step A smoke (about 12 small calls) | tiny, estimated from catalog prices | Tech lead approves (first paid call on acc2 for chat) |
| Step B judge comparison (`judge_compare` and score-only) | estimate printed before the run | Tech lead approves the per-run cap |
| Step C writer A/B (3, then ≤ 50 tours) | estimate printed before the run | Tech lead approves each stage of the trial, per the paid-run rule |
| Any route switch, the writer vendor rule, the ADR | — | Tech lead. Not part of this plan. |

## Định tuyến

# How the CIS LLM gateway picks a model today (S261, 31/10)

Code read: CIS `1b6e9448`, TripPlanner `02dd9f1`, Partner `d29e29e`, Infra working tree, and the schema dump (`docs/architecture/db-schema-reference.md`, verified 30/10). Paths below are relative to `apps/AA-CIS-App` unless a path says otherwise. I made no edits, no AWS calls, no DB calls and no LLM calls.

## Short answers
- **Routing.** Each stage has one row in `shared.llm_role_config`: a primary model, an ordered fallback list, and an optional shadow. A catalog model is tried on each of its deployments, ordered by `priority`, after filtering by data scope, circuit breaker and connection budget. This happens before the route moves on to its next model. The legacy keys `haiku`/`sonnet` skip all of this today. They run a hard-coded acc3 chain because `LLM_LEGACY_ALIASES` is off by default. So **all 20 live stages (18 CIS + 2 TripPlanner) have only acc3 Claude behind them.**
- **Mixing sources (acc3 → acc2 → anthropic-direct).** Yes, but only within these rules:
  - acc3 → anthropic-direct works only for the *same Claude catalog key* (deployment priority 10 then 100), and only on stages whose `allowed_scopes` include `vendor_direct`.
  - acc2 → Nova or another model works only as *another route position*, because Claude is not on acc2.
  - Legacy keys can never reach anthropic-direct.
- **Adding Nova, Llama 4 or Kimi K3 by data only: no.** The catalog `vendor` CHECK only allows anthropic, openai, cohere and typesafe, so a migration is needed. The admin UI also forbids non-Anthropic writers (the writer/judge vendor rule). The Converse adapter can call these models without code changes. Several fixes are still needed: cost attribution on acc2, reasoning controls, and caching for Nova.
- **Observability.** It is per-call cost accounting, not Langfuse-style tracing. There are no prompts or replies, no spans and no latency column, except prompts and outputs stored in the shadow log.

## 1. What happens on a call
`LLMClient.generate` → `_generate` (`shared/llm_client/client.py:572-584`) reads the stage row and binds the stage's `allowed_scopes`. Then `_generate_with` (`client.py:586-622`) runs:
1. **`account_route` is ignored.** Only acc3 is allowed. Any other stored value is logged and dropped (`client.py:589-592`; DB CHECK `account_route IN (acc3, NULL)`).
2. **Chain.**
   - If the request sets `model_tier`, the chain is `[model_tier]` alone: no route, no shadow.
   - Otherwise it is `[model_id, *fallback_model_ids]`.
   - Otherwise `DEFAULT_MODEL_TIER` (env, default haiku) (`client.py:596-601`).
3. **One model in the chain.** It is called directly. An account-level failure raises `LLMAccessDenied` at once (`client.py:604-613`).
4. **Several models.** `_call_route` (`client.py:745-791`):
   - A catalog key that is missing or disabled is skipped. It does not count as an attempt.
   - **Any** exception from a model moves on to the next model.
   - After a fallback succeeds, `fallback_used=True` is set.
5. **Per key** (`_call_key`, `client.py:624-632`).
   - Catalog keys go to `_call_catalog_model`: it refuses a disabled row (`client.py:1087`), builds `deployment_plan` (`client.py:1095-1098`), then runs `_call_plan` (`client.py:1126-1164`). The plan tries each deployment through `breaker.guarded`. An unusable reply is raised at once (the route moves on) and the remaining deployments are not tried.
   - Legacy keys go to `_legacy_call` (`client.py:634-640`). A `json_schema` request gets the schema added to the prompt (`client.py:700-728`).
6. **Dispatch** (`client.py:1191-1217`), by connection kind:
   - `anthropic` → Messages adapter.
   - `openai` / `azure_openai` → Chat adapter.
   - `bedrock` + `converse` → Converse. A task-role connection (acc2) uses `native_runtime` (`client.py:1201-1205`).
   - `anthropic_native` → InvokeModel body.
7. **Shadow** (`client.py:619-621`) runs only after the **primary has succeeded**, only when the request has no `model_tier`, only for `shadow_sample_pct`% of calls, and never inside an eval run.

## 2. Stage config (`shared/llm_client/role_config.py`)
- **Fields.** `StageConfig` (`role_config.py:55-68`): `stage, role, provider, model_id, account_route, fallback_model_ids, shadow_model_id, shadow_sample_pct, allowed_scopes`.
- **Reads.**
  - Only rows with `is_active` are read (`role_config.py:263`).
  - The cache lasts 20 s per process (`role_config.py:32`).
  - On a DB error the code falls back to `SAFE_DEFAULTS` (`role_config.py:82-188`). These still name luna/catalog keys for the judges, so they differ from today's live legacy-only routes.
- **`role`** (writer, judge, validate, embed) only drives the admin vendor rule and the `llm_call_log.role` column. **`provider`** (claude, openai, cohere) is display only.
- **`allowed_scopes`** (`aws_only` and/or `vendor_direct`) can only be set by migration (`api/routers/admin_llm_ops.py:253-260`). `cis_app` has no column grant for it (schema ref line 8152).

## 3. Catalog, deployment, connection
- **Catalog** (`shared/llm_client/catalog.py`): one logical model.
  - Holds api_style, `bedrock_profile_ids`, `supports_temperature`, `max_output_tokens`, prices, and `enabled` (the model switch). Cached 5 min.
  - CHECKs: an enabled row needs prices (schema ref line 8017-8021); `vendor ∈ {anthropic, openai, cohere, typesafe}` (line 8021).
  - The `capabilities` jsonb column exists (migration 304) but **no code reads it** (no hits in `shared/llm_client`).
  - `LEGACY_KEYS = {haiku, sonnet, gpt-4.1}` (`catalog.py:28`).
- **Deployment** (`shared/llm_client/deployments.py`): one model on one connection.
  - Holds `wire_id`, `priority` (lowest first, ties broken by `connection_key`, `deployments.py:147`), `enabled`, price overrides, and `request_defaults`. `request_defaults` is used only by the Anthropic and OpenAI adapters, never by Converse.
  - `cis_app` has SELECT only (schema ref 8053), so every change is a migration.
- **Connection** (`shared/llm_client/connections.py`): kind, `auth_mode`, `data_scope`, limits, budget, secret name.
  - The seeds are in `api/migrations/304_llm_connection_deployment.sql:285-303`: `acc3` (assume_role, enabled), `acc2` (task_role, enabled), `openai-direct` (enabled), `anthropic-direct` (disabled), `bedrock-llm-org` (disabled).
- **`deployment_plan`** (`shared/llm_client/vendor_route.py:213-289`):
  1. **Callable rows only.** Callable means there is an adapter for the api_style (`vendor_route.py:135-140`). An `anthropic` connection refuses legacy and non-Anthropic models. `openai` serves only `provider='openai'` rows (`vendor_route.py:194-210`).
  2. **Returns None vs `[]`.** If the registry does not describe the model, it returns `None` and the old path runs. That old path refuses Converse on acc2 (`client.py:1118-1120`). If rows exist but none can be used now, it returns `[]` and the model fails (`vendor_route.py:234-238, 255-256`).
  3. **Enabled filter.** Only an enabled deployment on an enabled connection is kept.
  4. **Scope filter** (`vendor_route.py:261-269`). If the stage has no policy (`allowed_scopes` NULL), a `vendor_direct` row is kept only when it is the first row.
  5. **Circuit, then budget.** A deployment behind an open circuit is skipped and named in `circuit_skips`; one on a connection over its hard budget is skipped and named in `budget_skips` (`vendor_route.py:274-284`).

## 4. Legacy keys and aliases
- **Today (`LLM_LEGACY_ALIASES` off)**, `_legacy_chain` runs (`client.py:833-910`): `sonnet` = acc3 Sonnet → acc3 Haiku; `haiku` = acc3 Haiku. acc2-native is off (`LLM_LEGACY_ACC2_NATIVE`). The last resort, gpt-4.1, is retired (`client.py:912-930`).
- **This chain has no breaker and no limiter.** Only `connection_budget.check` runs.
- **With aliases on** (an ECS env change in Infra), `shared.llm_model_alias` decides the steps. Migration 307 (lines 77-81) maps `haiku→[haiku]` and `sonnet→[sonnet, haiku]`. Those targets are the legacy catalog rows, so they still run acc3 only.
- **Legacy keys never reach anthropic-direct.** `_callable` refuses them (`vendor_route.py:201-202`), and migration 306 seeded anthropic-direct rows only for Claude catalog keys, at priority 100.
- None of the 7 `LLM_*` / `DEFAULT_MODEL_TIER` switches is set in Infra Terraform, so code defaults apply. I did not check this against the live task definition.

## 5. Breaker, limiter, health (S4: `shared/llm_client/breaker.py`)
- **Circuits.** One circuit per (connection, model), stored in `shared.llm_provider_health` (snapshot re-read every 10 s). Open rules (`breaker.py:100-106`):

| Error class | Opens after | First open period | Cap |
|---|---|---|---|
| access_denied | 1 failure | 300 s | 1800 s |
| quota_exhausted | 1 failure | 300 s | 1800 s |
| credential | 1 failure | 120 s | 900 s |
| throttled | 3 in a row | 30 s | 300 s |
| other | 5 in a row | 60 s | 600 s |

- **Half-open.** After the open period, exactly one probe call is allowed. If it fails, the next open period doubles, up to the cap.
- **Request errors are not counted** (`breaker.py:368-394`). These are `ValidationException`, 400/413 and content-filter errors. Side effect: acc2's Claude refusal ("not available for channel program accounts") is a `ValidationException`, so it never opens a circuit. It also classifies as `other`, not `LLMAccessDenied`.
- **Limiter.** Per connection and per process: `max_concurrency` and `rpm_limit`, with a 30 s wait (`breaker.py:113, 528-536`). After that it raises `LimiterSaturated` (class throttled), not counted by the breaker.
- **Switch.** `LLM_CIRCUIT_BREAKER=off` turns the breaker off.

## 6. Budgets
- **Monthly per connection (S10).** `monthly_budget_usd` with an alert at `alert_pct` (default 80%) and a hard stop (`shared/llm_client/connection_budget.py:1-22`, cache 60 s). If every model is skipped for budget, the call raises `ConnectionBudgetExceeded` and the job ends as stopped_budget (`client.py:246-252`). The seed rows have NULL budgets. Spend is summed from `llm_call_log.account` (`shared/cost_guard.py:327-333`).
- **Daily caps** (`shared.spend_budget`, `shared/cost_guard.py`). These are **not in the gateway**. A job opts in with `load_run_budget(...)` and calls `.check()` itself. About 10 job files do this (segment_research, place_*, supply_content_draft, writing_memory …). S1/T2/T8/T9/A3 are not covered.

## 7. Which errors fall back and which stop
- **Inside a route:** every exception moves to the next model (`client.py:764-774`), including access denied and open circuits.
- **Inside a plan:** failing deployments move to the next deployment, except an `UnusableReply` (billed but unusable: schema mismatch, empty, refusal), which skips the model's remaining deployments.
- **Converse retries in place** (one free retry each): a rejected temperature, a rejected forced tool choice (switched to `auto`), a rejected cachePoint. A schema mismatch gets one billed retry (`client.py:1297-1318`).
- **Final error** (`client.py:241-261, 786-791`):
  - `LLMAccessDenied` when every attempt failed with access_denied or quota_exhausted. The job runner then fails the job at once with no retries (`shared/llm_client/errors.py:142-158`).
  - `RouteUnusableReply` when every attempt was billed but unusable.
  - The budget error when everything was skipped for budget.
  - Otherwise a `RuntimeError` classed throttled or other, which the job retries.

## 8. Shadow A/B
- **Mechanics.** One shadow model per stage, run in a daemon thread. It writes an `llm_call_log` cost row plus `llm_shadow_log` (primary and shadow outputs up to 16k characters, cost, latency, request hash) (`shared/llm_client/shadow.py`; `client.py:793-831`).
- **Admin rules** (`admin_llm_ops.py:386-410`): the shadow must differ from the primary, must be "available" for the stage's role, and must not be a model reached only outside AWS.
- **Two limits today:**
  - No shadow ever fires while the primary fails, which is every acc3 route.
  - On writer stages the shadow must be an Anthropic model, so Nova or Kimi cannot be shadowed there.

## 9. Code that forces a model (`model_tier`)
These calls bypass the stage route and the shadow:
- Hard-coded `"haiku"` with no stage: `services/acp_contract/segment_research.py:483` and `services/acp_contract/segment_research_batch.py:190`.
- `services/eval/regression.py:170`.
- The AA-237 Sonnet upgrade: `api/routers/admin_pipeline.py:1076`.
- Batch defaults to `"haiku"`: `api/routers/admin_pipeline.py:1261, 1505`. The S1 Bedrock batch runs on acc3 only.
- Request-supplied tiers: S1 page / `jobs_repo`, `s1_batch`, judge.

## 10. What an admin can change, and where
**UI only: Admin → Settings → "Models" tab** (`ai.admin`; `frontend/app/admin/settings/{ModelsTab,StageRouteEditor,CatalogTab,ConnectionsTab,ShadowReportTab,LlmAvailabilityCard}.tsx`):
- **Stage primary model** (`PATCH /admin/llm-config/{stage}`).
- **Fallbacks and shadow** (`PATCH /admin/llm-config/{stage}/route`). Choices are limited to catalog rows that are enabled, have `llm_client` in `callable_via`, pass the vendor rule, and are reachable within the stage's scopes (`admin_llm_ops.py:160-192`). Writer stages must use Anthropic models and judge stages must not (`admin_llm_ops.py:180-183`). A model reached only through a vendor API may only be the last fallback (`admin_llm_ops.py:313-314, 389-390`).
- **Catalog:** price in/out, `price_source`, `enabled` (`catalog.py:204`).
- **Connections:** `enabled`, `secret_name`, `base_url`, `timeout_s`, `max_retries`, `max_concurrency`, `rpm_limit`, `monthly_budget_usd`, `notes`, budget alert %, hard stop, usage key (`admin_llm_ops.py:1211-1229`), plus a **Test** button and **Reconcile**.

**Migration or DB Migrate run-script:**
- New catalog rows, any catalog column other than price/enabled, and the vendor CHECK.
- Every deployment change (add, priority, enabled, wire_id, `request_defaults`).
- Alias rows.
- `allowed_scopes`.
- New stages, or a stage's role/provider.
- New connections, and connection identity or `data_scope`.

**Terraform / ECS env:** the `LLM_*` switches; IAM for TripPlanner. The secret `aa-llm/dev/anthropic-direct` is created separately.

**Code:** see section 12.

## 11. Mixing sources in one stage
- **Same model:** deployments in priority order. Only Claude catalog keys have both acc3 (priority 10) and anthropic-direct (priority 100) rows.
  - The stage needs `vendor_direct` in its `allowed_scopes`. That is a migration; only 10 judge-type stages have it (`role_config.py:193-196`).
  - When acc3 returns Error 002, its circuit opens and calls go straight to anthropic-direct.
- **Across models:** route order, for example `[sonnet-5-5, nova-pro]`.
- **The order is always model-first:** all deployments of model 1, then model 2. You cannot interleave `sonnet@acc3 → nova@acc2 → sonnet@anthropic-direct`.
- **Writer stages that are `aws_only` cannot use anthropic-direct at all.**

## 12. Adding Nova, Llama 4 or Kimi K3
**Data part (migration):**
- Widen `llm_model_catalog_vendor_check` (add amazon, meta, moonshot).
- Insert a catalog row: `provider='bedrock'`, `api_style='converse'`, `callable_via={llm_client}`, prices, `max_output_tokens`, and `supports_temperature` (false for Kimi if it rejects temperature).
- Insert an acc2 deployment row.
- Write `bedrock_profile_ids.acc2` with the same value as the deployment's `wire_id` (two copies). `tests/integration/test_aa1002_deployment_wire_drift.py` enforces this.

The acc2 task role already allows `bedrock:InvokeModel` on `*` (`infra/AA-CIS-Infra/modules/ecs/main.tf:247-263`).

**What already works without code:**
- Converse on acc2 (`client.py:1201-1205`).
- Reasoning blocks are ignored when reading text, both normal and streamed (`client.py:1320, 1328-1332`).
- If a model rejects a forced tool, the call falls back to `auto` + parsing JSON from text. This only triggers if the error text matches `_tool_choice_rejected` (`client.py:364-369`); not verified for Llama or Kimi.
- `acc2` is an `aws_only` connection, so `aws_only` stages may use it.
- Judge and validate stages accept non-Anthropic vendors.

**Needs code:**
1. **Bug: acc2 Converse replies carry neither `satellite_account` nor `connection_key`** (`client.py:1370-1378`). Call sites log `account=resp.satellite_account`, so acc2 chat rows get `account=NULL`. The acc2 monthly budget and per-connection cost tracking would not see that spend.
2. **No reasoning controls on Converse.** `additionalModelRequestFields` is never sent and `request_defaults` is ignored (`client.py:1256-1258`). Kimi's reasoning can use up `maxTokens`, giving an empty reply that is billed as unusable.
3. **The cachePoint is sent only for `anthropic.` profiles** (`client.py:418-425`), so Nova runs without caching. This costs money but does not break anything.
4. **Non-Anthropic writers** need the vendor rule changed (`admin_llm_ops.py:180-183`) plus an ADR decision.
5. **TripPlanner.** Its gateway would call a Converse catalog row on acc2 (`backend/shared/llm_gateway.py:176, 252-262`), but the TripPlanner Lambda IAM on acc2 only allows the embedding models (`infra/AA-CIS-Infra/accounts/aa365/tripplanner.tf:331-336`).
6. **CRM** is still a stub (`apps/AA-Partner/api/app/llm/gateway.py:106-127`).

## 13. Testing first without switching any stage
1. **Migration adds the rows switched off** (catalog `enabled=false`, deployment `enabled=false`). Nothing routes to them.
2. **Admin Connections → Test on acc2 with the model key.** This works on a switched-off row (`api/services/llm_connections.py:398-460`). It makes one call of a few tokens, writes an `adhoc_conn_test` log row and an audit row, and updates the circuit.
3. **For an A/B on real tours:** enable the catalog row and the deployment. No stage names the model, so production does not change. Then run an adhoc script with `LLMClient.generate(model_tier='<key>', stage='adhoc_<issue>', json_schema=…)`. This follows the paid-run steps (3 tours, then ≤50) and is logged in `llm_call_log`.
   - The writing-memory R2 eval cannot do this. It uses the stage route (`services/writing_memory/eval_writers.py`, `model_tier=None`).
   - The shadow cannot do it either, because the primary is blocked.
4. **Fix the account-attribution bug in section 12 first**, so that test spend is tracked under acc2.

## 14. Observability compared with Langfuse
**What exists:**
- `shared.llm_call_log` (schema ref line 7891). One row per call with stage, role, model, provider, account, tokens, cache split, cost, `pricing_mode`, `fallback_used`, `stop_reason`, `job_id`, `tenant_id`, and `quality_signal`.
- Shadow log; breaker health; connection costs and nightly reconcile.
- Admin endpoints and pages: `/admin/llm-usage/tree`, `/admin/job-runner/jobs/{id}/llm-calls`, `/admin/llm-shadow/report`, `/admin/llm-availability`, and the cost-ops forecast and daily spend.

**What is missing compared with Langfuse:**
- Success rows are written **by each call site**, not by the gateway. The gateway writes only billed-but-unusable rows (`shared/llm_client/call_log.py` header; `client.py:509-529`), so coverage depends on every call site doing it.
- No latency column. No prompt or reply stored outside the shadow log. No trace or span tree. No prompt versioning. No per-stage quality dashboard beyond `quality_signal`.
- `services/acp_shared/tracer.py` (Langfuse) is dead code with 0 callers.
- Paid tracing tools (Langfuse/LangSmith/OTel) are deferred until go-live (`docs/audits/2026-10-31-S261-architecture-review/README.md:853`).

**Not yet built in AA-1002:** S7 (batch), S8 (shared `aa_llm` core for TripPlanner/CRM), S11 (move legacy keys to 5.5 models behind an eval), and S12 (capacity controls, including an immediate alert when a circuit opens).

## Kiểm kê model theo nguồn

## LLM gateway inventory and readiness (CIS migrations up to 317, code at CIS `1b6e9448`)

**Answer first:** today the gateway's data does not include Amazon Nova, Meta Llama or Moonshot Kimi. The only deployment that works end to end is Cohere Embed v4 on acc2. Making the four acc2 models callable is **not data-only**. It needs one hand-applied migration, because the catalog's `vendor` CHECK blocks the new rows. The code path for acc2 Converse already exists. For safe use, a few small code fixes are advisable, mainly for Kimi K3.

### 1. What the gateway knows (14 catalog rows, 5 connections)

Connections are seeded at `304_llm_connection_deployment.sql:286-305`:
- **acc3:** Bedrock, assume_role, enabled. Live: blocked with Error 002.
- **acc2:** Bedrock, task_role, enabled.
- **openai-direct:** api_key, enabled, key from env `OPENAI_API_KEY`. Live: 429, out of credit.
- **anthropic-direct:** disabled, no secret.
- **bedrock-llm-org:** disabled, no account ID or ExternalId, and no deployments.

Deployments are backfilled at `304:311-352`, plus Anthropic API rows at `306:68-79`. Stage routes come from `shared/llm_client/role_config.py:76-190` and the live snapshot `docs/audits/2026-10-30-S260-evidence/data/03-llm-config-scopes.json`, which has primary model only.

| Model key | Family / vendor | Deployments (connection, priority, enabled) | Catalog enabled | Stages that route it |
|---|---|---|---|---|
| `haiku` | Claude Haiku 4.5, anthropic, `anthropic_native` | acc3 p10 on; acc2 p20 **off** (`304:316-323`) | yes | Primary: s1/t2_flag_fix, s1/t2_itinerary_nudge, t9_repair, t9_faq_filter, a0_column_map, a3_place_card_check, a3_place_days, a3_place_dedupe_check. Fallback: s1_source_facts, a3_atomize, a3_place_locate. Alias: haiku→haiku, sonnet pos 2→haiku (`307`) |
| `sonnet` | Claude Sonnet 4.6, `anthropic_native` | acc3 p10 on; acc2 p20 off | yes | Primary: s1_atom_writer, t2_generate, t8_angle_gen, t9_write, t9_faq_answer_fit, a3_place_locate, **tp_compose, tp_extract**. Fallback: supply_content_writer, a3_place_days, a3_place_card_check, t9_repair |
| `sonnet-5` | Claude 5, converse | acc3 p10; anthropic-direct p100 | yes | none |
| `haiku-5-5` | Claude 5.5 (`259:88-112`) | acc3 p10; anthropic-direct p100 | yes | none |
| `sonnet-5-5` | Claude 5.5 | acc3 p10; anthropic-direct p100 | yes | s1_generate, supply_content_writer |
| `opus-5-5` | Claude 5.5 | acc3 p10; anthropic-direct p100 | yes | none (eval only) |
| `gpt-5.6-luna` | GPT on Bedrock (vendor openai) | acc3 p10 | yes | 8 judge stages (s1/t2 judge + brand_audit, t7_debate_judge, t10_judge, writing_memory_mine/eval); fallback of a3_place_card, t10_claims, t10_adjudicate |
| `gpt-6-luna` | GPT on Bedrock | acc3 p10 (enabled by `286:64`) | yes | s1_source_facts, a3_atomize, a3_place_card, t10_claims, t10_adjudicate, a3_place_dedupe; judge fallback |
| `gpt-6-astra` | GPT on Bedrock | acc3 p10 | yes | none |
| `gpt-6-luna-openai` | GPT, OpenAI API | openai-direct p10 (vendor_direct) | yes | Last fallback for judge stages, t10_adjudicate, a3_place_dedupe |
| `gpt-4.1` | GPT, OpenAI API | openai-direct p10 | **no**, retired (`224:56`) | none |
| `cohere-embed-v4` | Cohere embed | **acc2 p20 on**, `global.cohere.embed-v4:0` (`238`) | yes | f10_embed, a3_place_embed, tp_search_embed, tp_component_embed |
| `cohere-embed-v4-acc3` | Cohere embed | acc3 p10 (`240:90`) | yes | Fallback of the 4 embed routes |
| `jev-latest` | Typesafe Jev, `decide` | none (outside the registry) | — | Jev path only |

On the "18 CIS + 2 TP legacy-key" figure: the 30/10 snapshot shows **16 CIS + 2 TP stages** with `haiku`/`sonnet` as their primary. A few more name those keys only as a fallback, which may explain 18.

- **Legacy keys:** they only go through deployments when `LLM_LEGACY_ALIASES=on`. It is off by default (`client.py:46-56`), so these stages run the hard-coded acc3 chain.
- **Hard-coded tiers:** some call sites pin `model_tier="haiku"` or `"sonnet"` and ignore stage routes entirely: `services/acp_contract/segment_research.py:483`, `segment_research_batch.py:190`, `services/eval/regression.py:170`, `api/routers/admin_pipeline.py:1076`.

### 2. Which families are in the catalog

- **Claude 4.x:** yes (haiku, sonnet).
- **Claude 5.x:** yes (4 rows).
- **GPT on Bedrock:** yes (3 rows).
- **GPT on the OpenAI API:** yes (one live row; gpt-4.1 is retired).
- **Cohere Embed v4:** yes (2 rows).
- **Typesafe Jev:** yes.
- **Amazon Nova, Meta Llama, Moonshot Kimi, GLM, Grok:** **no**. The live `llm_model_catalog_vendor_check` only allows `anthropic`, `openai`, `cohere` and `typesafe` (`169:25`; `docs/architecture/db-schema-reference.md:8021`).

### 3. Readiness matrix (code and migrations combined with the live facts of 31/10)

| Family | acc3 Bedrock | acc2 Bedrock | anthropic-direct | openai-direct | bedrock-llm-org |
|---|---|---|---|---|---|
| Claude 4.x | blocked at provider (deployment on) | deployment disabled, and blocked at provider (channel program) | not in catalog for this path (306 skips `anthropic_native`) | — | no deployment, connection disabled |
| Claude 5.x | blocked at provider | in catalog, no deployment (and blocked at provider) | deployment on, **connection disabled** (no key) | — | no deployment |
| GPT on Bedrock | blocked at provider | in catalog, no deployment (and "not available" at provider) | — | not allowed by design: an OpenAI connection serves only `provider='openai'` rows (`vendor_route.py:203`) | — |
| GPT, OpenAI API | — | — | — | deployment on, **blocked at provider** (429, no credit) | — |
| Amazon Nova | not in catalog (also blocked) | **not in catalog**; provider works | — | — | — |
| Meta Llama 4 | not in catalog | **not in catalog**; provider works | — | — | — |
| Moonshot Kimi K3 | not in catalog | **not in catalog**; provider works | — | — | — |
| Cohere Embed v4 | blocked at provider | **works today** | — | — | — |
| GLM, Grok | not in catalog | not in catalog, and blocked at provider | — | — | — |

Net effect: every text stage currently fails. Only embeddings work.

### 4. What makes acc2 Nova 2 Lite, Nova Pro, Llama 4 Maverick and Kimi K3 callable

**The code path already exists.** A `converse` catalog row on a `task_role` Bedrock connection is dispatched to `native_runtime(conn)`:
- `client.py:1191-1205` dispatches it.
- `vendor_route.py:135-140` and `:194-200` mark Bedrock `converse` as callable under assume_role or task_role.
- `LLM_DEPLOYMENT_ROUTING` is on by default (`client.py:89`).
- The ECS task role allows `bedrock:InvokeModel` and `InvokeModelWithResponseStream` on `*` (`infra/AA-CIS-Infra/modules/ecs/main.tf:261`).
- The acc2 connection is `aws_only`, which fits every `{aws_only}` stage.
- Pricing and logging work: priced from the catalog row (`pricing.py:193`); `llm_call_log` records `provider=bedrock`, `account=acc2`.

**Rows needed (one migration, applied by hand through DB Migrate with the job tables idle; it counts as a contract change because it alters an existing CHECK):**

1. **Widen the vendor CHECK.** Drop and recreate `llm_model_catalog_vendor_check` with `amazon`, `meta` and `moonshot` added, plus any future vendors.
2. **Add 4 rows to `shared.llm_model_catalog`.** Each needs `provider='bedrock'`, `api_style='converse'`, `callable_via='{llm_client}'`, `bedrock_profile_ids={"acc2": <wire id>}`, prices for input and output, `enabled`, and a real `max_output_tokens` cap. The CHECK at `169:44` refuses `enabled` without prices.
   - `nova-2-lite`: `us.amazon.nova-2-lite-v1:0` (or `global.`)
   - `nova-pro`: `us.amazon.nova-pro-v1:0`
   - `llama4-maverick`: `us.meta.llama4-maverick-17b-instruct-v1:0` (used in the AA-339 bake-off, `apps/AA-CIS-App/docs/AA339_compare_llm/README.md:7`)
   - `kimi-k3`: the wire ID is **not in any repo**. Look it up with `aws bedrock list-foundation-models` or `list-inference-profiles` on acc2.
3. **Add 4 rows to `shared.llm_model_deployment`.** Each is `(model_key, 'acc2', wire_id = the acc2 profile, priority 10 or 20, enabled, origin 'seed')`. The admin cannot do this: cis_app has only SELECT on this table (`db-schema-reference.md:8053`). The wire ID must equal `bedrock_profile_ids.acc2`, or the CI drift guard `tests/integration/test_aa1002_deployment_wire_drift.py` fails.
4. **No new connection and no grant changes.**

**After the migration, route changes are data-only.** They go through Settings > Models (`PATCH /admin/llm-config/{stage}` and `/route`), subject to `admin_llm_ops.py:176-183`:
- `validate` stages may use any vendor.
- `judge` stages may use any non-Anthropic model, so Nova, Llama and Kimi are allowed.
- **`writer` stages refuse any non-Anthropic model.** A writer A/B therefore has to go through an eval or harness using a `model_tier` override (`_call_catalog_model` has no vendor rule), not through a route or shadow on the stage.

**Gaps to fix or check before routing real stages:**
- **Kimi K3 (reasoning model).** The output token limit comes only from the call site; the catalog row can only lower it (`client.py:1232-1234`). The Converse path ignores `deployment.request_defaults` (only the Anthropic adapter reads it), so a reasoning budget cannot be set as data. If reasoning uses all the tokens, the call fails as "returned empty content" (`client.py:1342`) and the billed attempt is logged as unusable. The admin connection test uses `TEST_MAX_TOKENS = 32` (`api/services/llm_connections.py:370`), so a Kimi test will report a failure.
- **Structured output.** The gateway forces the tool choice by default. If a model rejects that, the switch to `auto` only triggers on certain error wording: "not supported", "unsupported", "not allowed", "thinking" or "deprecated" (`client.py:364-369`). A rejection worded differently, for example "doesn't support", would fail instead of retrying. Run one live smoke test with a JSON schema per model, or add those models to `_NO_FORCED_TOOL_CHOICE_MARKERS` (`client.py:351`).
- **Fallback path.** Without the registry, or with `LLM_DEPLOYMENT_ROUTING=off`, an acc2 `converse` model raises "no satellite account" (`client.py:1119`). That is acceptable as a fail-closed rollback.
- **Limits on acc2.** The acc2 connection has `rpm_limit`, `max_concurrency` and `monthly_budget_usd` all NULL (304 seed), so no limiter or budget applies until they are set in the Connections tab (data).
- **Legacy-key stages.** The 16 + 2 stages on `haiku`/`sonnet` only move if each stage's `model_id` is changed. The admin refuses this for writer-role stages: a0_column_map, s1/t2_flag_fix, s1/t2_itinerary_nudge, s1_atom_writer, t2_generate, t8_angle_gen, t9_write, t9_repair. Validate-role stages can move (a3_place_*, t9_faq_*). Repointing aliases (`LLM_LEGACY_ALIASES`) would get around the writer/judge vendor rule; I would not recommend it.
- **TripPlanner.** Its gateway reads `bedrock_profile_ids` and already calls `converse` on acc2 (`apps/AA-TripPlanner-Web/backend/shared/llm_gateway.py:176`, `:237-262`). However, the Lambda role only allows the Cohere ARNs (`infra/AA-CIS-Infra/accounts/aa365/tripplanner.tf:331-336`), so moving tp_compose or tp_extract would also need a Terraform IAM change.
- **AA-Partner (CRM).** The CRM gateway is still a stub (`apps/AA-Partner/api/app/llm/gateway.py:1-28`, `StubProvider`), so none of this applies to it before gateway slice S8.

### 5. Quality evidence already in the repo

From the AA-339 bake-off (31/07/2026, acc2), `apps/AA-CIS-App/docs/AA339_compare_llm/README.md:75-90`:
- Llama 4 Scout and Maverick lost to Claude Haiku and Sonnet on every tour (0/29 wins).
- As a judge, Nova Pro flipped its verdict on 17/29 tours when the answer order was swapped (position bias).

This supports testing first: run Nova and Kimi as judge/validate candidates through the eval or shadow log before any route switch, rather than switching routes straight away.

## Quan sát và theo dõi (so với Langfuse)

# LLM observability today compared with Langfuse (S261, read-only)

**Short answer:** It's partly true. The gateway already tracks cost, usage, budgets, availability and offline evals in-house, and in some areas it does more than Langfuse (it reconciles its cost against the provider's bill and enforces budgets on the call path). It is not Langfuse-like in five ways:
- It keeps no per-call latency.
- It has no trace or span tree.
- It keeps no prompt or completion text per call.
- In CIS, a refused or unbilled attempt leaves no row in the ledger.
- No UI shows "this job's calls".

The tracing part was already studied in AA-842 (`docs/audits/2026-10-29-S257-aa842-otel/README.md`). That audit found no OTel anywhere, 0 X-Ray traces, and the old Langfuse code is dead (`:29-38`, `:269-273`).

## 1. What exists today

### 1.1 The CIS ledger: `shared.llm_call_log`
About 383,796 rows, 202.8 MB (`docs/architecture/db-schema-reference.md:7891-7927`).

- **Columns:** `id, tenant_id, stage, role (writer|judge|validate|embed), model, tokens_in, tokens_out, cost_usd, quality_signal jsonb, content_piece_id, angle_gate_request_id, created_at, stop_reason, account, fallback_used, provider, job_id, cache_read_tokens, cache_write_tokens, pricing_mode`.
- **Columns it does not have:**
  - latency
  - outcome or error class
  - provider request id
  - prompt version
  - attempt or position in the route
  - deployment id
  - parent call or trace id
  - an `app` column (the app is in `quality_signal.app`; AA-804 adds the column)
  - any prompt or completion text
- **Who writes the row:** the call site, not the gateway (`shared/llm_client/call_log.py:33-54`, `record_call*` at `:290-372`).
  - The gateway writes only two kinds of row itself: billed-but-unusable attempts (`client.py:509-529`, `quality_signal.gateway_attempt=true`) and shadow cost rows (`shadow.py:42-50`).
  - CI guards keep call sites honest: `tests/unit/test_aa685_no_raw_model_calls.py`, `test_aa927_llm_call_site_registry.py`, `test_aa927_one_row_per_call.py`, `test_aa1002_s6_billed_fields.py`.
- **Context:** `job_id` and `tenant_id` are carried by contextvars (`call_log.py:113-149`).
- **Eval runs are relabelled:** `bind_eval_stage` writes eval rows under the eval stage, with the real stage and run id kept in `quality_signal` (`call_log.py:160-192`).
- **Refused calls leave no row in CIS.** Only billed calls get one, so an Error-002 refusal is visible only in `shared.job.error` and `shared.llm_provider_health` (`api/services/llm_availability.py:8-16`).
- **Latency and provider request ids go only to the JSON logs** (`client.py:1059-1062`, `:1440-1444`). Those live in CloudWatch `/ecs/aa-cis-dev`, which keeps app logs for 30 days (`infra/.../modules/ecs/main.tf:516`). The log lines carry `request_id`, `job_id` and `job_kind` (`shared/log_config.py:1-17`).
- **Retention:** raw rows 180 days, archived to S3, then rolled up into `shared.llm_call_daily` (`services/retention/policy.py:54-59`; rollup schema `:7865-7889`).

### 1.2 Other LLM tables
- **`shared.llm_shadow_log`** (`schema:8154-8171`) stores the primary and shadow outputs (up to 16,000 characters each), the shadow's latency, both costs and a `request_sha256` of the prompt (`shadow.py:22, 32-33, 53-59`). Problems:
  - It has no `tenant_id`.
  - It has no retention job: `policy.py` has no spec for it, while DM-7 proposes 180 days (`02-data-management.md:251`).
  - A shadow runs only after the primary call succeeds (`client.py:618-621`), so a stage whose primary is on acc3 cannot shadow today.
- **`shared.llm_provider_health`** (`schema:8105-8127`) keeps one row per connection × model: `last_ok_at`, `last_error_class` (access_denied, quota_exhausted, throttled, credential, other), consecutive failures, circuit state. It holds the latest state only, no history.
- **`shared.llm_cost_reconcile`** and **`llm_connection_cost_policy`** (S10, migration 317) compare what the ledger logged each day against the provider's own figure, read from:
  - stored Cost Explorer data for Bedrock
  - the Anthropic cost report
  - the OpenAI costs API

  Status is ok, mismatch, not_configured and so on. A mismatch rings the admin bell once per 24 h (`services/llm_cost/reconcile.py:1-38`).
- **`shared.spend_budget`** and `shared/cost_guard.py` check limits before each paid call (per run, per day, hard stop). `connection_budget.py:1-22` adds a monthly cap per connection on the call path.
- **`shared.decision_log`** (Jev) has `latency_ms`, `error`, `job_id` and a human `outcome` label.

### 1.3 Admin UI (CIS)
- **`/admin/cost-ops`** has tabs Overview (with month-end forecast), LLM, DataForSEO, AWS bill, Jev and Budgets (`frontend/app/admin/cost-ops/page.tsx:2-7, 507-508`).
  - The LLM tab shows a tenant → model → stage tree: calls, cost, tokens, fallback count, ok-rate, truncated count (`admin_llm_ops.py:752`, SQL just above).
  - A drill-down lists flat calls, filterable by piece, tenant, stage, account or fallback (`:773-846`). It has **no `job_id` filter** and does not return job, cache or `pricing_mode` columns (`:818`).
- **Settings › LLM Models** has sub-tabs Stages, Catalog, Shadow and Connections (`ModelsTab.tsx:344-347`).
  - The availability card reads real outcomes and makes no probe call (`admin_llm_ops.py:1193`).
  - The Connections tab has health, budgets, a costs view, a reconcile action and a Test-connection button (`:1203-1356`).
  - The shadow report covers agreement, score delta, cost, p50/p95 shadow latency and repeat variance (`:481-659`).
- **Tenant 360** shows cost per tenant (`admin_tenant360.py:94-106`). The wave report shows cost per wave by `job_id` (`services/waves/report.py:104`).

### 1.4 Reports and alarms
- **OPS-12 daily digest (AA-1003)** (`services/reports/digest.py:1-31`) includes:
  - an LLM availability section (blocked, degraded, unknown)
  - K-LLM-COST-DAY compared with the 14-day median
  - K-LLM-FALLBACK-24H (`kpis.py:115-134`)
- **Weekly money KPIs:** K-LLM-APP, TENANT, SHADOW, FALLBACK, ADHOC and RECON (`money.py:845-856`).
- **No LLM latency KPI exists for CIS.** The only one is K-CRM04-LATENCY-P95 (`registry/kpis.yaml:914`).
- **CloudWatch alarms** fire when a `llm_call_log`, `decision_log`, `llm_shadow_log` or `dfs_call_log` write finally fails (`infra/.../accounts/aa365/observability.tf:505-557`).
- **No Bedrock cost alarm, on purpose** (AA-828, `:133-143`). The in-app ledger and budgets cover it instead, and AWS Budgets apply per account and per App tag.
- **No instant alert when a circuit opens.** It is planned in S12 (capacity plan `README.md:582`).
- **Sentry** is on for the api and worker with 10% traces and PII scrubbing (`shared/sentry_init.py:6-11, 265-274`). It gives no LLM spans: Bedrock calls appear only as generic HTTP spans and the worker starts no transaction (AA-842 `:35-38`).

### 1.5 Evals and datasets (in-house)
- **Golden sets:** `shared.eval_golden_set` and `eval_golden_item` (334 items, labelled, with splits and traps).
- **Results:** `shared.eval_item_result` stores verdict, score, failure codes, judge model and version, and cost.
- **Prompt eval runs:** `shared.prompt_eval_runs` stores `prompt_version`, the baseline version, `regression_detected`, a cost cap and judge kappa (`services/eval/regression.py:177-294`).
- **Writing-memory releases and shadows** keep `prompt_sha256` and the output.
- **Human labels:** `acp_shared.content_piece_label` and `content_label` (label, defects, minutes to fix), and `decision_log.outcome`.
- **Prompt versioning:** prompts live in code. The version is the first 8 characters of the system prompt's sha256 (`services/content_generation/batch_prompt.py:247-249`). It is written to some `quality_signal`s (`graph.py:644`, `quality_gates.py:716`) but is not a column.

### 1.6 TripPlanner and CRM
- **TripPlanner** (`backend/shared/llm_gateway.py`) INSERTs into `shared.llm_call_log` (`:528-545`). Differences from CIS:
  - It **logs failed attempts** with `stop_reason='error'` and `quality_signal.failed` (`:26-27`), which CIS does not do.
  - It writes no `job_id`, cache tokens or `pricing_mode`.
  - It never runs a shadow (`:30-31`).
  - It has a daily cap in `tripplanner.llm_spend_daily`.
  - The code has 4 stages: tp_compose, tp_search_embed, tp_extract and tp_component_embed.
  - Its other logs are JSON with `request_id`, and Sentry catches errors only.
- **CRM** (`AA-Partner/api/app/llm/gateway.py:1-29`) has its own ledger, `crm.llm_call` (`schema:4757`), under RLS and append-only.
  - Columns: `latency_ms`, `outcome` (ok, refused, error), `refusal_code`, `error_class`, `scrub_receipt` (counts only). It stores no prompt and no output.
  - Its rollup `crm.llm_usage_daily` is read by the CIS cost page.
  - Calls go in this order: PII scrub (Bedrock Guardrails) → budget → `ai_enabled`.
  - **The provider is still the stub** (`:277`). No real model call exists yet.

### 1.7 Data rules that bind any tracing tool
- **DM-6.4** (`02-data-management.md:226`): no identifying PII in prompts, and none in `llm_call_log`, its `quality_signal`, `llm_shadow_log` or app logs. It is enforced by review only, and no automated PII check is planned (`README.md:168`).
- **DM-10.4** (`:371`): every paid call goes through the gateway into the ledger with `job_id`; ad-hoc scripts use `stage=adhoc_<issue>`. The weekly report tracks it as K-LLM-ADHOC.
- **ADR 0012** (`apps/AA-CIS-App/docs/adr/0012-*.md:22-35`): `data_scope` (`aws_only` or `vendor_direct`) controls only which model connection a stage may use. **A trace exporter to a SaaS backend would be a new way for content to leave AWS that this policy does not cover.**
- **CRM:** never anything except Bedrock, scrubbed text only (ADR 0008a).

## 2. Feature by feature against Langfuse

| Langfuse feature | Status | Where it is, or what is missing |
|---|---|---|
| Trace per job or tour with nested spans | **Partial** | `job_id`, `content_piece_id` and `tenant_id` group calls. There is no span tree: attempts, fallbacks and retries appear only in log lines (`llm_route_attempt_failed`, `client.py:765`), kept 30 days. No job → calls view in the UI. |
| Generation records (model, tokens, cost) | **Have** | `llm_call_log`, including cache tokens and `pricing_mode`. Stronger than Langfuse, which estimates cost while ours is reconciled with the provider (S10). |
| Prompt and completion capture | **Missing** (by design) | Not stored per call. Only the shadow log keeps outputs, plus eval tables and the content tables themselves. |
| Prompt management and versioning | **Partial** | Prompts live in code with a sha256 version. Some stages log `prompt_version`; `prompt_eval_runs` holds versions and baselines. No registry, playground or label-based rollout. |
| Evals and scores on traces | **Partial** | Judge and validate results go into `quality_signal`, and the UI shows ok-rate per stage. Offline evals are strong (golden sets, R2 runner, regression detection, judge kappa), but scores are not attached to individual generation rows. |
| Datasets and experiments | **Have (in-house)** | `eval_golden_set`/`item`, `eval_item_result`, writing-memory releases and shadows, plus the shadow A/B report. |
| User feedback / annotation | **Partial** | `content_piece_label`, `decision_log.outcome` and review queues. Not linked to individual LLM calls. |
| Cost per trace | **Have** (SQL) / **partial** (UI) | Per job (wave report), per piece (calls filter), per tenant (Tenant 360). No per-job UI. |
| Latency percentiles | **Missing** for CIS and TripPlanner | No latency column. Only the shadow p95, Jev's `decision_log.latency_ms` and CRM's `latency_ms` exist. |
| Session / user view | **Partial** | `tenant_id`, `job_id` and `request_id` (in logs). No session object for TripPlanner B2C. |
| Error and refusal tracking | **Partial** | `provider_health` keeps only the latest state; `shared.job.error`; billed-unusable rows. CIS writes no row for an unbilled refusal (TripPlanner and CRM do). |
| Alerts, budgets, availability | **Have**, beyond Langfuse | Budgets per run, day and connection; reconcile bell; digest; write-failure alarms; circuit breaker. Missing: instant alert when a circuit opens (S12). |
| PII masking | **Have** for CRM / **policy only** for CIS | CRM scrubs before the call; Sentry redacts. CIS prompts follow DM-6.4 by review only. |
| Self-host vs cloud | n/a | Everything is in-house on acc2 RDS. Leftover Langfuse dead code: `langfuse==2.26.0` (`requirements.txt:50`), `services/acp_shared/tracer.py`, an empty `infra/.../modules/langfuse/*.tf` (0 bytes), and the columns `shared.pipeline_runs.langfuse_trace_url` and `silver_aa_internal.quality_scores.langfuse_trace_id`. |

## 3. What this means for testing the acc2 models before switching
- **Shadow can't help today.** It runs only after the primary call succeeds (`client.py:618-621`), and the primaries are on acc3, which is blocked.
- **Usable now:**
  - The Connections "Test connection" button (`POST /admin/llm-connections/{key}/test`, logged as an `adhoc_*` row).
  - The eval harness: golden set, R2 runner and `bind_eval_stage`. Its rows go under the eval stage with a cost cap, and `eval_item_result` gives verdicts and scores per item.
  - Ad-hoc scripts through `LLMClient.generate()` with `stage=adhoc_<issue>`.
- **The current tools can't show latency per model**, which matters for Kimi K3 (a reasoning model). The trial would read latency from log lines (`llm_success`) or need the latency column below.

## 4. Recommendation

**Build in-house, $0 extra infrastructure (one CIS migration plus gateway code, roughly 2–3 days):**
1. **Make the gateway write one ledger row per attempt** (billed or not), with new columns:
   - `latency_ms`
   - `outcome` (ok, refused, error, unusable)
   - `error_class` (reuse `errors.classify`)
   - `attempt` (route position)
   - `connection_key` / deployment
   - `provider_request_id`
   - `prompt_version` (the 8-character hash)
   - `app`, which is AA-804

   Refused and failed attempts get cost 0. This matches what TripPlanner and CRM already do and lets `llm_availability` stop parsing `shared.job.error`. Keep the call-site `quality_signal` row through an id link, or as the second half of a two-phase write.
2. **Add a job trace view:** a `job_id` filter on `/admin/llm-usage/calls`, and an "LLM calls" panel on the job and wave detail. It would show each call's stage, model, account, attempt, latency, tokens, cost and outcome in time order, read through the existing `llm_call_log_job_idx`. This covers about 80% of what a Langfuse trace gives here.
3. **Add latency p50/p95 per stage and model** to the Cost Ops LLM tab, and a K-LLM-LATENCY-P95 line in the OPS-12 digest. Pull the S12 instant circuit-open alert forward.
4. **Fix the shadow log:** add a retention spec (180 d) and a `tenant_id` column so erasure and DM-7 apply to it.
5. **Remove the dead Langfuse code:** the pin, `tracer.py`, the empty module, and the two legacy columns (each by its owner's migration).
6. **Optional, later:** opt-in prompt/completion capture for platform-only, `aws_only` stages, stored in acc2 S3 with a TTL of 30 days or less. Never for CRM or tenant PII.

**Langfuse:**
- **Cloud: no.** Prompts and outputs would leave AWS outside ADR 0012's control, it is incompatible with CRM (ADR 0008a and DM-6.4), and it would be a new vendor and new spend.
- **Self-hosted: not now.**
  - It needs a web and a worker service, Postgres, ClickHouse, Redis and S3. ClickHouse needs persistent disk, which is awkward on Fargate.
  - AA-842 estimates **$60–150/month**, plus operations work.
  - It would add connections to the shared RDS, which is already near its limit (about 132 of 135 per the data standards v1.3 note). That last point is my inference.
  - It falls under the "paid observability on hold" decision (GuardDuty and the OTel spike are off).
- **When to reopen it:** prod with real traffic, several engineers debugging prompts, or a need for a prompt playground or annotation queues. If it is adopted then, use the AA-842 design: an OTel exporter behind a flag, metadata only by default, self-hosted in acc2, with `llm_call_log` staying the source of truth for cost.

## Các app khác (TripPlanner, CRM, Booking)

## Other apps and the shared LLM gateway (S261, read-only)

Nothing was edited, no AWS calls were made and no paid LLM was called. Repo root is `/home/nghiep/projects/AA-Ecosys`.

**Summary:**
- **TripPlanner** has its own copy of the gateway. It reads two of the CIS gateway tables, but none of what AA-1002 S1–S10 added.
- **The CRM gateway** is a stub. It has a working PII scrubber, budget check and on/off switch, but no real model provider exists and its task role cannot invoke any model.
- **Booking** makes no LLM calls.
- **Unifying the three apps** is planned as gateway slice S8, which has not started.

Two blockers apply to every app, CIS included. Today no catalog row can describe Nova, Llama or Kimi, and the admin page will not let any writer stage pick a model that is not Anthropic.

### 1. TripPlanner — `apps/AA-TripPlanner-Web/backend/shared/llm_gateway.py`

**How it picks a model**
- `load_route` (L130-171) reads `shared.llm_role_config` (the stage's main model, fallback list and `account_route`) and `shared.llm_model_catalog` (`vendor`, `api_style`, `bedrock_profile_ids`, prices, `enabled`). The SQL is at L137-147. Routes are cached for 60 s (L59).
- If either table cannot be read, it falls back to routes written in the code (L105-114): `tp_compose` uses Sonnet 4.6 on acc3, `tp_search_embed` uses Cohere Embed v4 on acc2.
- `generate_text` (L265-297) tries each enabled model in order, and for each model each account in `_accounts` (L179-181): the preferred `account_route` first, then `SUPPORTED_ACCOUNTS = ("acc3", "acc2")` (L176), but only accounts that have a profile in `bedrock_profile_ids`.
- acc2 is called with the Lambda's own role (`_runtime`, L202-205). acc3 is reached by assuming its role (L188-199).
- Supported `api_style` values (`_text_call` L237-262): `anthropic_native` (InvokeModel) and `converse` only. `anthropic_messages` and `openai_*` raise "not supported" (L262).
- **Shadow runs are skipped.** A configured shadow model is only noted in the log (L161-165).

**What it does not read.** It never reads `llm_model_deployment`, `llm_provider_connection`, `llm_model_alias`, `llm_provider_health`, `llm_connection_cost_policy` or `allowed_scopes`. The live grants (`docs/architecture/db-schema-reference.md` L7990-8153) back this up: `tripplanner` has SELECT on catalog and role_config, INSERT on `llm_call_log`, and nothing else. So the S3 deployment spread, S4 circuit breaker and rate limiter, S5 data scopes and S10 per-connection budgets do not apply to TripPlanner calls. The S3 notes already say this "until S8" (AA-1002.md L296, L373).

**Stages and callers**
- `tp_compose`: `assembly/agent.py:18`, called at `assembly/handler.py:506`. Route = legacy key `sonnet` on acc3 (CIS migration 172 L47).
- `tp_search_embed`: `browse/search.py:50`, L119-144.
- `tp_extract` and `tp_component_embed` have no callers.

**Can it use the acc2 or direct paths today?**

| Path | Usable today? | Why |
|---|---|---|
| acc2 Nova, Llama 4, Kimi K3 | No | Three blockers, below |
| anthropic-direct | No | No adapter, no secret access, `account_route` limited to acc3 |
| openai-direct | No | No OpenAI path in the code at all |

The code itself would work: a `converse` catalog row with an `acc2` profile goes through `_text_call` (L252-261), and Kimi's reasoning blocks have no `text` key so they are dropped. But three things block it:
1. **Catalog CHECK (all apps).** `llm_model_catalog_vendor_check` only allows anthropic, openai, cohere and typesafe (schema ref L8021). An amazon, meta or moonshot row needs a CIS migration first. No migration mentions Nova, Llama or Kimi yet.
2. **Admin rule (also CIS).** `admin_llm_ops.py:182`: a `writer` stage must use an Anthropic model. `tp_compose` is a writer, so the admin page will not offer Nova or Kimi for it.
3. **IAM.** The TripPlanner Lambda role may only call InvokeModel on the Cohere ARNs (`infra/AA-CIS-Infra/accounts/aa365/tripplanner.tf` L64-74, L330-337). A Nova call on acc2 would get AccessDenied, so Terraform needs a new grant.

Two smaller points:
- `compose` uses `max_tokens: 1200` (`agent.py:55`). A reasoning model like Kimi may spend that on thinking, return empty text, and count as a failure.
- The converse call sends no temperature setting and no cache point.

**Logging**
- `record()` (L528-546) writes one `shared.llm_call_log` row per attempt, failed attempts included (AA-805), with `quality_signal.app='tripplanner'` and `provider` set to `bedrock-native` or `bedrock-satellite` (L100-102).
- It does not fill `cache_read_tokens`, `cache_write_tokens`, `pricing_mode` or `job_id`, although it does use cache tokens when computing cost.
- A missing catalog price is logged as cost NULL.
- There is a daily spend cap on the customer-facing stages: `tripplanner.llm_spend_daily` against `TP_DAILY_SPEND_CAP_USD` (5 USD by default), L549-591. If the counter cannot be read, the cap is not enforced and calls go through (L588-590).
- Logs go to CloudWatch as JSON, PII redacted (`shared/observability.py:151`). No prompts or outputs are stored and there is no trace or span ID.

**Behaviour with acc3 blocked.** Days that have AA's own master text still work. Any day that needs the model makes the narration fail, and the API answers 502 `narration_failed` (`handler.py:305-313`). It falls back to plain "Day N: names" text only when the budget is exhausted (L575-579), not when the provider fails.

### 2. AA-Partner CRM — `apps/AA-Partner/api/app/llm/gateway.py`

**Order of checks** (each one stops the call on failure):
1. Scrub (L159-169).
2. Budget, under an advisory lock per agency (L171-178; `ai_budget_usd` defaults to 2 USD a month).
3. `ai_enabled`, which defaults to false (L179-180).
4. Seal the placeholder map before paying for the call (L182-190).
5. Call the provider (L192-199).
6. Log one `crm.llm_call` row (no text) plus the `crm.llm_usage_daily` rollup and an audit event (L216-273).
7. Store the map (L203-213).

Every result that is not `ok` returns `manual_reply_needed`.

**The PII scrubber is real.** `privacy/scrubber.py` (version `f3-3`) runs three passes: known values → regex → Bedrock Guardrails `ApplyGuardrail` on acc2 (`privacy/guardrails.py`; `infra/.../crm_scrub.tf` L62-69, L126). It fails closed.

**The provider is a stub.** Only `StubScrubber` and `StubProvider` exist (L106-125) and `stub_gateway()` (L276). The "Bedrock" provider in the tests is a fake (`tests/unit/test_llm_gateway.py:67,91`). No production code instantiates `LlmGateway`; its only importer is `ops/console.py:41`, which uses the constants. With the stub scrubber, a real provider is refused (L168). The `Provider` protocol takes only `prompt` (L99-103): no system prompt, no max tokens, no route, no fallback chain, one model per gateway.

**IAM.** The CRM task role has only `bedrock:ApplyGuardrail`, no InvokeModel (`crm_scrub.tf`; nothing in `crm_app.tf`).

**Policy.** ADR 0008a §5 (`docs/adr/0008a-crm-separate-app-exceptions.md` L107-125) sets these rules:
- Bedrock only; OpenAI and Jev are never used for CRM stages.
- No `shared.*` grants, so it writes no `shared.llm_call_log` row.
- Stage settings live in the `crm` schema.
- The planned path is acc3 through a CRM-only role.
- §6 (L129-137): ADR 0009 may share the gateway *code* but not the database control plane.

So Nova or Kimi on acc2 fits the "Bedrock only" rule, but anthropic-direct would need an ADR amendment.

**Observability.** CIS sees CRM usage only as a daily total per stage and model, through `GET /crm/ops/v1/llm/usage` (`llm/usage.py`; CIS `api/services/platform_cost.py:242-345`, `platform_apps.py:270`).

**CRM-33a (AA-964)** is scheduled for S264 (`docs/backlog/README.md:239`). It needs AA-958 and an LLM path, and has no Linear export yet. The 75/90 % budget alerts and `ai_draft` arrive with it (`docs/implementation-notes/AA-936.md:94`, `AA-938.md:21`).

### 3. AA-Booking

Booking makes **no LLM calls**. Its runtime dependencies have no Bedrock or Anthropic SDK (`backend/requirements.txt`), and its code has no Bedrock, Anthropic or OpenAI reference; the only hits are gitleaks secret-scanning rules. `CONTEXT.md:1304-1312` says "Today Booking makes no AI calls" and sets the high-risk AI boundary (AA-820) for future features. AI drafting for Booking supply is planned as a CIS consumer job (AA-835; `docs/implementation-notes/AA-975.md:77-79`), so it would go through the CIS gateway.

### 4. Plan to unify — AA-1002 slice S8, under epic AA-642

- **Blueprint S8** (`docs/audits/2026-10-29-S258-aws-org-blueprint/blueprint.json`, `ai_gateway.build_slices`): split out an `aa_llm` core package in CIS plus a sync script, and vendor it into the other apps.
  - TripPlanner replaces `llm_gateway.py`, reads its config through a CIS contract, and drops `SUPPORTED_ACCOUNTS` and the account env vars.
  - The CRM gets a real adapter behind `Provider` and keeps the scrub → budget → ai_enabled order.
  - Effort 3–4 days, no CIS migration, medium risk.
  - CIS stops writing `bedrock_profile_ids` only after TripPlanner has moved.
- **Status.** S1–S6, S9 and S10 are live or merged. S7 and S8 have not started (backlog row 0ad, `docs/backlog/README.md:169`). AA-642 is "later, last in the L1 order" (L253). CIS ADR 0012 L9: "TripPlanner keeps its own gateway until slice S8". Neither AA-642 nor AA-1002 is in `docs/linear-export` (both are open).

### Per app: router, reachable sources, logging, gap to one gateway

| App | Router | Sources reachable today | Logging | Gap to "one gateway" |
|---|---|---|---|---|
| CIS | `shared/llm_client`: deployments, aliases, scopes, breaker, budgets | acc3 (blocked), acc2 embed, anthropic-direct (off, no key), openai-direct (key, out of credit) | `shared.llm_call_log` + shadow log + health + reconcile | Vendor CHECK and writer=Anthropic rule block Nova, Llama and Kimi |
| TripPlanner | Own copy: role_config + catalog, accounts acc3 then acc2 | acc3 (blocked → 502 on model days), acc2 Cohere only | `shared.llm_call_log` without cache, pricing or job columns; daily cap | Ignores deployments, connections, scopes, breaker; no Anthropic-messages or OpenAI adapter; IAM limited to Cohere; no grants on the new tables. Needs S8 or a stopgap catalog row plus IAM |
| CRM | Stub `LlmGateway`, one provider, no routing | None (stub; role has ApplyGuardrail only) | Own `crm.llm_call` (latency, scrub receipt, no text) → CIS through ops API | Needs a Bedrock provider adapter (AA-964), an InvokeModel grant, a route or fallback concept in the `crm` schema; ADR 0008a forbids `shared.*` reads and non-Bedrock providers |
| Booking | None | None | None | Nothing to unify; future AI goes through CIS jobs |

**Against a Langfuse-style view:**
- Every app stores metadata only: no prompts, outputs or trace and span tree.
- `shared.llm_call_log` has no latency column (only the CRM records latency) and no `app` column (app is in `quality_signal->>'app'`).
- The CRM ledger is separate by ADR, and CIS sees it only as daily totals.

**Before testing an acc2 model in TripPlanner** (TripPlanner itself has no shadow mode, so a test means pointing one stage at it):
1. A CIS migration to widen `vendor_check` and `provider_check` (schema ref L8021 and L8147).
2. Catalog rows with prices: `enabled_needs_price` refuses an enabled row without them.
3. Relax the writer=Anthropic rule for `tp_compose`, or test on a non-writer stage.
4. Add InvokeModel ARNs for those models to `tripplanner.tf`.
5. A larger `max_tokens` for reasoning models.
