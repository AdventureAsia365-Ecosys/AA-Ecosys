# AA-842: OpenTelemetry gen_ai tracing for every LLM call (Bedrock + OpenAI)

Read-only investigation, session S257, 2026-10-29. Agent: Claude Code (lane AA-842). Report for the tech lead.
This file replaces the S238 draft (2026-10-15) of the same name. Since then the gateway changed a lot: acc1 left the
ecosystem (AA-998, ADR 0001a), acc2-native Claude attempts were switched off (AA-843), JSON logs with job and request
context shipped (AA-871), Sentry turned on, and the S1 writer moved to a Converse key. Every number below was
re-measured on the current code and live state.

**Sources (snapshots used for every file:line)**
- AA-CIS-App `origin/main` `92934598` (2026-10-29 02:27 UTC). The live image is `dev-3994a1a8` (api task def `:906`,
  worker `:472`, from `aws ecs describe-services`). `git diff --stat 3994a1a8 origin/main -- shared/llm_client
  shared/log_config.py shared/sentry_init.py shared/jobs/worker.py requirements.txt` is empty, so the cited code is
  what runs live.
- AA-TripPlanner-Web `origin/main` `c961e12`. AA-CIS-Infra `origin/main` `daaa477`.
- Database: not queried by this lane (no ECS exec). Columns and row counts come from
  `docs/architecture/db-schema-reference.md` (root repo, "Verified: 2026-10-29 00:06 UTC").
- AWS: read-only describe, list and Logs Insights calls on acc2 (profile `aa365-admin`, us-west-1).
- Web: PyPI JSON API, the downloaded wheels of `anthropic` 2.3.0 and `sentry-sdk` 2.73.0 (read, not run), AWS and
  vendor pricing pages.
- Not done: no paid LLM call, no spike, no code, dependency, Terraform, ECS or Lambda change.

---

## 1. Summary and recommendation

**Is LLM tracing there today? No.**
- No Python file in CIS or the TripPlanner backend imports `opentelemetry` (`rg` count 0, Appendix V13).
- X-Ray has 0 traces in the last 6 hours. The `aws/spans` log group does not exist, so Transaction Search is off.
- No ECS service has a collector sidecar (each task definition has one container). No Lambda has a layer, and all
  8 Lambdas run `tracing: PassThrough`.
- Infra Terraform has 0 matches for X-Ray, ADOT or OTel. The `modules/langfuse/*.tf` files are 0 bytes.
- **What did change since S238:** the CIS api and worker now write one JSON log line per event, with `job_id`,
  `job_kind` and `request_id` bound through `structlog.contextvars` (AA-871, `shared/log_config.py:1-17`). Sentry is
  on (the DSN secret has a value since 2026-10-17, and 0 "Sentry DSN not found" lines in 7 days) with
  `traces_sample_rate=0.1` (`shared/sentry_init.py:273`). Sentry gives API request transactions and error events. It
  gives **no LLM spans for Bedrock**: its boto3 integration only makes generic `http.client` spans
  (`sentry_sdk/integrations/boto3/_instrumentation.py:181`), and the worker starts no Sentry transaction, so worker
  LLM calls produce no Sentry spans at all.

**Who calls LLMs.**
- CIS: 41 registered call sites (the AA-927 registry, `tests/unit/test_aa927_llm_call_site_registry.py`), all
  through one gateway, `shared/llm_client/`. The gateway makes 8 kinds of wire calls (section 2.1).
- TripPlanner backend: 2 callers (`tp_compose`, `tp_search_embed`) through `backend/shared/llm_gateway.py`.
- Jev (TypeSafe) is a separate HTTP decision API: 18 `decide()` call lines in 13 files (Appendix V8).

**Does the anthropic SDK help? Only a little.**
- Neither repo depends on `anthropic` (it is absent from both requirements files). Every Claude call is raw boto3
  (`invoke_model`, `invoke_model_with_response_stream`, `converse`, `converse_stream`).
- The current `anthropic` release, 2.3.0 (2026-10-23), does support the `open_telemetry` client option, also on
  `AnthropicBedrock` (`anthropic/lib/bedrock/_client.py:154`, provider name `aws.bedrock` at `:95`). Options:
  `traces.enabled`, `content_mode` (`metadata_only` by default), `max_content_bytes` (750,000 by default),
  `propagation`, `conversation_id`, with the `ANTHROPIC_OPEN_TELEMETRY*` environment variables
  (`anthropic/_types.py:118-213`). OTel support first shipped in v1.14.0 (2026-10-14, release notes "add native
  support for OpenTelemetry tracing").
- **But the live S1 writer does not use the Anthropic Messages API any more.** `s1_generate` routes to `sonnet-5-5`,
  a catalog key with `api_style=converse` (route kept on permanently since S250, root `docs/backlog/README.md:427`).
  Converse is an AWS API. The Anthropic SDK cannot make Converse calls, so its tracing would not cover the A1
  writer stage, nor any GPT judge or validator on Bedrock.

**Recommendation: Option B.** One gen_ai wrapper span per logical call at the gateway, in `LLMClient.generate`
(`client.py:327`). One child span per attempt in `_call_key_logged` (`client.py:413`). This is the one function that
the route loop (`:444`), single-key calls (`:362`) and the shadow (`:501`) all go through. Add the same wrapper in
`embed()` (`embed.py:124`), in `_call_jev` (`decide.py:244`, so the Jev canary that bypasses `decide()` is also
covered), and in TripPlanner `generate_text` / `embed_texts`.

What only the gateway knows, and the reason to prefer B:
- business context: stage, role, job id and kind, tenant, eval run
- route position, and why an attempt failed
- billed-but-unusable replies (AA-927)
- the shadow call

Optional later: the `opentelemetry-instrumentation-botocore` child layer (Option C1) for per-request Bedrock wire
spans. Decide after the pilot whether its noise is worth it.

**The fallback reason is still logged as text only, and since AA-998 there is no account fallback.** Logs Insights,
`/ecs/aa-cis-dev`, last 7 days (Appendix V15–V17):
- 25–26/10, 18 hours: acc3 returned `ServiceUnavailableException` to legacy Haiku calls **139 times**. 138 were
  saved by the then-existing acc1 tier (`t2_5b_satellite_used`, acc1) and 1 failed there too
  (`t2_5b_satellite_failed_trying_t3`).
- Today that acc1 tier is gone (`client.py:300-303`). The same burst would make those calls raise, and the route's
  next model or the job retry takes over.
- Neither database table records why. `llm_call_log` has `account`, `fallback_used` and `provider`, but no reason
  column, and no row is written for an attempt that failed without a bill. The `error_type` exists only in the log
  line `satellite_invoke_failed` (`bedrock_satellite.py:292`). A B span with an `error.type` attribute per attempt
  makes this queryable.
- AA-843 worked: the 7-day counts of `t1_failed_trying_t2` and `t2_failed_trying_t2_5a` are 0, against 954 and 1,428
  in the S238 week.

**Pins needed (none exist today).** OTel is not in `requirements.txt`. `fastapi==0.161.1` (`requirements.txt:28`)
hard-requires `opentelemetry-api>=1.44.0` (PyPI `requires_dist`), so the image has the API package, but not the SDK
or an exporter. (Inferred: `chromadb`, which used to pull in the SDK, was dropped. An image probe would confirm it.)
The pin set depends on the backend (section 5):
- **X-Ray without a collector, through ADOT:** `aws-opentelemetry-distro==0.21.0` (2026-10-01) pins
  `opentelemetry-api==1.44.0`, `opentelemetry-exporter-otlp-proto-http==1.44.0` and `opentelemetry-distro==0.65b0`
  (PyPI). This is compatible with fastapi's `>=1.44.0`.
- **Any other OTLP backend (Langfuse, Grafana, a collector):** `opentelemetry-api==1.45.1`,
  `opentelemetry-sdk==1.45.1`, `opentelemetry-exporter-otlp-proto-http==1.45.1`,
  `opentelemetry-semantic-conventions==0.66b1` (all 2026-10-06). For C1, add
  `opentelemetry-instrumentation-botocore==0.66b1`.
- Do **not** add `anthropic` for this work. If a later ADR moves the Messages API calls onto the SDK, pin
  `anthropic[bedrock]==2.3.0` exactly (it brings `httpx2>=2,<3` and `opentelemetry-api>=1.1,<2`).

**Backend: X-Ray through Transaction Search** costs under about $2 a month at Dev volume and keeps content in AWS.
Langfuse Cloud (Core) is about $30–80 a month and gives the best LLM UI, but sends data outside AWS. The choice goes
in an ADR (section 5).

---

## 2. Call-site table

### 2.1 Wire calls (where bytes leave the process)

| file:line | function | client / API | sync / async | streaming | path |
|---|---|---|---|---|---|
| CIS `shared/llm_client/client.py:621` | `_call_bedrock` (acc2-native T1/T2) | boto3 `invoke_model_with_response_stream` | sync | always | gateway; **off by default** (`LLM_LEGACY_ACC2_NATIVE`, `:47-55`; the worker task def has no such variable) |
| CIS `bedrock_satellite.py:261` | `invoke_claude` (acc3 legacy haiku/sonnet) | boto3 `invoke_model`, Anthropic body | sync | no | gateway (T1.5a / T2.5a, `client.py:540`, `:562`) |
| CIS `bedrock_satellite.py:165` | `_invoke_streaming` | boto3 `invoke_model_with_response_stream` | sync | when a stream sink is bound and the request has no `json_schema` (`client.py:697`) | gateway |
| CIS `client.py:807` (via `_converse_with_param_downgrades`, `:221`), `:834` (schema retry) | `_call_bedrock_converse` | boto3 `converse` (acc3 session, `:787`) | sync | no | gateway, catalog keys |
| CIS `client.py:846` | `_call_bedrock_converse` | boto3 `converse_stream` | sync | when a sink is bound and no schema (`:786`) | gateway, catalog keys |
| CIS `client.py:936` | `_call_openai` | `openai.OpenAI().chat.completions.create` (client at `:323`) | sync | no | gateway; only for an enabled catalog row with provider `openai` (`:932`, `:62-70`) |
| CIS `shared/llm_client/embed.py:96` | `_call` | boto3 `invoke_model` (Cohere Embed v4; acc2 client `:57`, acc3 `:77`) | sync | n/a | `embed()` |
| CIS `shared/llm_client/decide.py:251` | `_call_jev` | `httpx.AsyncClient.post` to TypeSafe `/v1/systemone` (`:45`) | async | no | `decide()`, plus the canary at `api/routers/admin_llm_ops.py:1218` |
| CIS `shared/llm_client/bedrock_batch.py:176` | `submit_batch_job` | boto3 `create_model_invocation_job` | sync | n/a | offline Batch; never run (AA-624, registry `EXCLUDED` entry for `s1_batch.py`) |
| TP `backend/shared/llm_gateway.py:244` | `_text_call` (`anthropic_native`) | boto3 `invoke_model` | sync | no | TP gateway |
| TP `llm_gateway.py:253` | `_text_call` (`converse`) | boto3 `converse` | sync | no | TP gateway |
| TP `llm_gateway.py:405` | `embed_texts` | boto3 `invoke_model` (Cohere) | sync | n/a | TP gateway |

No line in either repo imports `anthropic`. CIS has exactly 2 `openai` lines, both in `client.py` (`:10`, `:323`),
and TripPlanner has 0 (Appendix V1, TP1).

### 2.2 Logical callers (CIS)

The list is the AA-927 registry (`LOGGED_CALL_SITES`, 41 entries; `EXCLUDED`, 5 entries). The guard test fails when a
new call site appears. Line numbers are the gateway call inside each function (Appendix V3–V5). The stage is the
literal, or the constant it resolves to. The role and default route come from `SAFE_DEFAULTS` in
`shared/llm_client/role_config.py:76-176`. That is the code fallback, not the live route; see 2.3 for how to read
live routes.

**Streaming.** Calls stream only while a job binds a sink: `s1_rewrite_job.py:91`, `t2_rewrite_job.py:440`,
`t9_write_job.py:47`, `acp_shared/writing_progress.py:246`.

**Event loop.** Most sync callers run inside `asyncio.to_thread` or the LangGraph executor. The marked ones block an
event loop.

| file:line | function (sync/async) | stage → role (code default route) | notes |
|---|---|---|---|
| `services/content_generation/graph.py:614` | `generate_node` (sync) | `s1_generate` / `t2_generate` → writer (haiku). **Live `s1_generate` = `sonnet-5-5` (Converse)**, per the backlog | streams under the S1/T2 sink |
| `content_generation/s1_writer_v2_live.py:70` | `_call` (sync) | `s1_generate` → writer; up to 3 calls per draft (`:15`) | live: worker env `S1_WRITER_V2` is set (task def `:472`) |
| `content_generation/itinerary_utils.py:125` | `nudge_itinerary_day` (sync) | `s1_/t2_itinerary_nudge` → writer (haiku) | |
| `content_generation/flag_fix_node.py:639`, `:284` | `flag_fix_node`, `_rerepair_meta` (sync) | `s1_/t2_flag_fix` → writer (haiku) | |
| `content_generation/grounding.py:439` | `repair` (sync) | `s1_flag_fix` by default (`:422`) → writer | |
| `content_generation/source_facts.py:246` | `extract_day_facts` (sync) | `s1_source_facts` → validate (gpt-6-luna → …) | |
| `content_generation/brand_audit_node.py:663` | `brand_audit_node` (sync) | `s1_/t2_brand_audit` → judge (gpt-5.6-luna → gpt-6-luna → gpt-6-luna-openai) | shadow possible |
| `shared/llm_client/judge.py:54` (`call_judge`), `:61` (`invoke_judge`) | sync | the one judge client (AA-765); callers below | |
| `content_generation/brand_fit.py:723` (`_judge`), `:628`, `:663`, `:545` | sync | `s1_judge` / `t2_judge` / `t7_debate_judge` → judge | **T7 runs on the event loop**: `acp_shared/debate.py:264` calls `score_candidate_fit` directly inside async `apply_debate` |
| `content_generation/judge_node.py:335`, `:348` | `judge_node` (sync) | `s1_judge` / `t2_judge` (+ `s1_judge_tiebreak`, `:194`) | writes the judge rows |
| `acp_content_writing/quality_gates.py:1189` | `_gate_brand_voice` (sync) | `t10_judge` → judge | via `invoke_judge` |
| `acp_content_writing/generate.py:59`, `:67` | `_generate_full` (sync) | `t9_write` → writer (sonnet) | streams under the T9 sink |
| `acp_content_writing/generate.py:351` | `repair_sentences_detailed` (sync) | `t9_write` by default (`:333`) | |
| `acp_content_writing/generate.py:425`, `:508` | `fit_seo_fields`, `write_faq` (sync) | `t9_repair` (`:393`) → writer (haiku → sonnet) | |
| `acp_content_writing/faq_filter.py:273` | `llm_filter_questions` (sync) | `t9_faq_filter` → validate (haiku) | |
| `acp_content_writing/faq_answer_fit.py:193` | `_fit_call` (sync) | `t9_faq_answer_fit` → validate (sonnet) | |
| `acp_angle_gate/generate.py:141` | `_generate_once` (async, `to_thread`) | `t8_angle_gen` → writer (sonnet) | |
| `acp_contract/a3_atomize.py:145` | `_ask_atoms` (async, `to_thread`) | `a3_atomize` → validate (gpt-6-luna → haiku) | |
| `acp_shared/place_cards.py:856`, `:877` | `draft_card`, `check_card` (sync) | `a3_place_card` (gpt-6-luna), `a3_place_card_check` (haiku) → validate | |
| `services/places/llm.py:29` | `_generate_sync` | `a3_place_days`, `a3_place_locate` → validate | |
| `services/jobs/place_dedupe_job.py:50` | `_generate_sync` | `a3_place_dedupe` (gpt-6-luna), `a3_place_dedupe_check` (haiku) → validate | |
| `acp_contract/segment_research.py:492`, `segment_research_batch.py:191` | async, `to_thread` | **no stage**: `model_tier="haiku"` (`segment_research.py:483`, `segment_research_batch.py:190`); logged as `a3_search_demand`, which has no route | no route, no shadow |
| `services/supply_content/writer.py:171` | `draft_content` (sync) | `supply_content_writer` → writer (sonnet-5-5) | |
| `services/writing_memory/drafter.py:108`, `eval_judge.py:325` | `_generate_sync` | `writing_memory_mine`, `writing_memory_eval` → judge | eval runs set `bind_eval_stage` (`call_log.py:100`) |
| `shared/llm_client/column_mapper.py:79` | `detect_column_mapping` (sync) | `a0_column_map` → writer (haiku) | logs its own row (`:105`, `:111`) |
| `acp_shared/content_embedding.py:122`, `places/llm.py:58` | sync / async | `f10_embed`, `a3_place_embed` → embed (cohere-embed-v4) | `embed()` |
| 18 Jev lines in 13 files, for example `ingestion/jev_gates.py`, `grounding.py`, `atom_ranking.py` (4), `judge_node.py` (2) | async (`decide_sync` in graph nodes) | `a0_ingest`, `a1_seo`, `s1_grounding`, `a3_*`, `t7_*`, … (provider `typesafe`) | `decide()` writes `decision_log` + `llm_call_log` (`decide.py:706-755`) |
| `api/routers/admin_llm_ops.py:1218` | `check_jev_canary` (async) | none | **calls `_call_jev` directly, bypassing `decide()`**; no `llm_call_log` row |
| scripts: `aa645/s1_screen.py:341`, `aa645/brandfit_measure.py:242`, `aa790/t9_writer_repanel.py:212`, `aa856_global_profile_probe.py:171` | sync | `adhoc_*` stages | the probe calls `embed_mod._call` directly (no route) |

**TripPlanner backend**

| file:line | function | stage → role | notes |
|---|---|---|---|
| `backend/assembly/agent.py:88` | `_run` (sync generator) | `tp_compose` → writer; built-in route Sonnet 4.6 on acc3 (`llm_gateway.py:103-110`) | **sync inside an async handler**: `assembly/handler.py:583` calls `narrate_fn(missing)` without `to_thread` |
| `backend/browse/search.py:134` | `_query_vector` (async) | `tp_search_embed` → embed (Cohere: acc2 first, then acc3) | sync boto3 on the event loop; 0 cost on cache hits (`llm_gateway.py:430-440`) |

`s1_atom_writer`, `t10_claims`, `tp_extract` and `tp_component_embed` have a code default but no caller found
(`rg` over each stage name, Appendix V6).

### 2.3 Gateway, bypasses, fallback, live routes

**Choke points (one per call type).**

| Call type | Entry → per-attempt function |
|---|---|
| Text, CIS | `LLMClient.generate` (`client.py:327`) → `_generate` (`:338`) → `_call_route` (`:428`) or a single key → **`_call_key_logged` (`:413`)** → `_call_key` (`:373`) → legacy chain (`:511`) / catalog Converse (`:751`) / OpenAI (`:898`) |
| Embeddings, CIS | `embed()` (`embed.py:124`) → `_call` (`:92`) |
| Jev, CIS | `decide()` / `decide_sync()` (`decide.py:758`, `:793`) → `_decide` (`:582`) → `_call_jev` (`:244`) |
| TripPlanner | `generate_text` / `embed_texts` (`llm_gateway.py:265`, `:388`) |

**Bypasses.**
- Guard 1, `tests/unit/test_aa685_no_raw_model_calls.py`. It fails on any raw Bedrock method, `*.completions.create`
  or `invoke_claude` / `get_satellite_client` outside `shared/llm_client/` (lines 12-17, 40-44). `ALLOWED` is empty
  (line 21). It scans only `services`, `api` and `shared` (line 12), and does not look for httpx calls.
- Guard 2, the AA-927 registry (section 2.2). It scans `scripts/` too.
- Real bypasses today:
  - the Jev canary (`admin_llm_ops.py:1218`)
  - the embed probe script (`aa856_global_profile_probe.py:171`)
  - the stage-less `segment_research*` calls. They go through the gateway but carry no stage, so they get no route
    and no stage attribute.
- 0 raw Bedrock or OpenAI calls outside `shared/llm_client/` (V2).

**Logging happens after the call, mostly at the caller.**
- 65 `record_*` call lines in 32 non-test files (V10).
- Three writers sit inside the gateway:
  - `decide()` (`decide.py:755`)
  - the shadow thread (`client.py:505` → `shadow.py:43`)
  - the AA-927 billed-unusable rows (`client.py:276-296`, written on a background thread)
- So a span opened in `generate()` sees the response, but not the `quality_signal` or the role that the caller adds
  later. Those stay in `llm_call_log`.

**Fallback, as the code does it now (AA-998).**

| Route type | Where | Order | Fallback reason recorded |
|---|---|---|---|
| Legacy keys `haiku` / `sonnet` (`catalog.py:26`) | `_legacy_chain` (`client.py:511-589`) | acc2-native T1/T2, only if `LLM_LEGACY_ACC2_NATIVE` (off) → acc3 Sonnet (T1.5a) → acc3 Haiku (T2.5a) → GPT-4.1 only if its catalog row is re-enabled (`:577`; live: retired, S235) | Log lines only: `t1_5a_satellite_failed_trying_t2` (`:548`), `t2_5a_satellite_failed_trying_t3` (`:570`), `satellite_invoke_failed` with `error_type` (`bedrock_satellite.py:292`). In the DB: `fallback_used = tier == "sonnet"` (`:564`), i.e. True when a Sonnet stage dropped to Haiku |
| Catalog keys (Converse, OpenAI) | `_call_route` (`client.py:428-472`) | model → model; each model on one account (`catalog.py:69-78`, acc3 before acc2) | `llm_route_attempt_failed` (`:447`, with error text), `llm_route_skip` (`:440`), `llm_openai_fallback_used` (`:463`). In the DB: `fallback_used=True` when position > 0 (`:456`). Billed-unusable attempts get their own row (`:424`) |
| Embeddings | `embed()` (`embed.py:124-157`) | model → model (`cohere-embed-v4` acc2 → `cohere-embed-v4-acc3`, migration 240) | log `llm_embed_success` with account |
| TripPlanner | `generate_text` (`llm_gateway.py:265-297`) | model × account (`SUPPORTED_ACCOUNTS = ("acc3", "acc2")`, `:176`) | **each failed attempt gets its own `llm_call_log` row** with `stop_reason='error'` and the error (`:226-229`, `record()` `:528`) |
| Shadow | `_start_shadow` (`client.py:474-509`) | daemon thread; job and tenant carried over explicitly (`:480-493`) | `llm_shadow_log` + `llm_call_log` under the same stage |

The account route is now acc3 or NULL: a CHECK since migration 295 (`api/migrations/295_llm_acc3_only.sql`), and any
other stored value is ignored with `llm_account_route_ignored` (`client.py:346-349`).

**Live routes: how to read them (this lane did not query).** `shared.llm_role_config` has ~36 rows (schema
reference). Columns: `stage, role, provider, model_id, account_route, is_active, fallback_model_ids,
shadow_model_id, shadow_sample_pct`. `cis_app` can SELECT it. The gateway reads it per stage with a 20 s cache
(`role_config.py:29`, `:198-208`). Three read-only ways to see it:
1. The admin UI, Settings > Models, or `GET /admin/llm-config` and `GET /admin/llm-catalog`
   (`api/routers/admin_llm_ops.py:216`, `:375`), called through the admin BFF `/api/admin/...` (it adds the admin
   secret).
2. An S3-mediated ECS exec script on the api task with the container `DATABASE_URL` (`cis_app`, `ssl="require"`):
   `SELECT stage, role, model_id, fallback_model_ids, shadow_model_id, shadow_sample_pct, account_route FROM
   shared.llm_role_config WHERE is_active ORDER BY stage;`, plus `SELECT model_key, provider, api_style,
   bedrock_profile_ids ? 'acc3' AS on_acc3, enabled, blocked_reason FROM shared.llm_model_catalog ORDER BY
   model_key;`. This is a live step for the orchestrator.
3. The routes in code (`SAFE_DEFAULTS`, `role_config.py:76-176`) are only the fallback when the DB read fails.

Known live deviation from the code defaults, from session records rather than a query: `s1_generate` =
`sonnet-5-5` (root `docs/backlog/README.md:427`, S250). The code default is `haiku` (`role_config.py:77`).

**Catalog keys in code and migrations:**
- Legacy: `haiku`, `sonnet`, `gpt-4.1`
- Claude on Converse: `haiku-5-5`, `sonnet-5`, `sonnet-5-5`, `opus-5-5`
- GPT on Bedrock Converse: `gpt-5.6-luna`, `gpt-6-luna`, `gpt-6-astra`
- OpenAI platform: `gpt-6-luna-openai`
- Embeddings: `cohere-embed-v4`, `cohere-embed-v4-acc3`
- Jev: `jev-latest`

---

## 3. Current observability

### 3.1 Apps

| Item | State | Evidence |
|---|---|---|
| OpenTelemetry in code | none | V13: 0 matches in CIS and TP backend |
| OTel packages | `opentelemetry-api` comes through `fastapi==0.161.1` (requires `>=1.44.0`); no SDK, no exporter (inferred) | `requirements.txt:28`; PyPI `requires_dist` of fastapi 0.161.1. The local `.venv` is stale (fastapi 0.110.1, chromadb 0.4.24) and is not evidence for the image |
| Logs (CIS) | **JSON, one object per line**, fields `service` (`cis-api` / `cis-worker`), `git_sha`, `request_id`, `tenant_id`, `job_id`, `job_kind` | `shared/log_config.py:1-17`, `:136-197`; binds at `shared/jobs/worker.py:220`, `api/middleware/request_id.py:92`, `api/middleware/rate_limit.py:96` |
| LLM log events | `llm_success` (per wire call, with tokens, cost, stop_reason), `llm_route_used`, `llm_route_attempt_failed`, `satellite_invoke_failed`, `llm_embed_success`, `converse_schema_retry` | `client.py:659`, `:715`, `:884`, `:969`, `:465`; V15 counts |
| Sentry (CIS) | **on**: errors, plus 10% transactions and profiles; FastAPI integrations on the api; auto-enabling integrations include openai, anthropic, boto3, httpx, langgraph | `shared/sentry_init.py:250-277`; sentry-sdk 2.73.0 `integrations/__init__.py:68-97`; the secret has an `AWSCURRENT` version since 2026-10-17; V17 has 0 "DSN not found" lines. The pin is `sentry-sdk[fastapi]>=1.40.0` (`requirements.txt:45`), so the installed version is not pinned |
| Sentry LLM coverage | OpenAI calls only, and only inside a sampled API transaction; Bedrock calls only as `http.client` spans; worker jobs have no transaction (`start_transaction` count 0) | `boto3/_instrumentation.py:181`; `rg "start_transaction\|start_span" --type py` → 0 |
| Langfuse | dead code: `services/acp_shared/tracer.py` (v2 API, langfuse pinned to version 2.26.0 at `requirements.txt:46`); no keys in the task defs | V14 |
| LLM data today | **in the database**: `shared.llm_call_log` (~383,796 rows, 202.7 MB), `shared.llm_shadow_log` (~5,554), Jev `shared.decision_log`, plus the Redis live-progress channel (`stream_sink`, ADR 0004) | schema reference §`shared.llm_call_log` |
| TripPlanner backend | JSON logs with `request_id` (structlog contextvars) and Sentry for errors only, no tracing | `backend/shared/observability.py:1-25`; `structlog==25.5.0`, `sentry-sdk==2.70.0` (`backend/requirements.txt:8-9`) |

### 3.2 Infra (`infra/AA-CIS-Infra/accounts/aa365`, live root)

- `observability.tf` (563 lines):
  - SNS alerts (`:53`)
  - RDS CPU and ECS task-count alarms (`:75`, `:102`)
  - ACP alarms (`:153`, `:201`, `:222`)
  - budgets (`:258`, `:336`)
  - CloudTrail (`:387-503`)
  - the `log_write_failed` metric filters and alarms for `llm_call_log`, `decision_log`, `llm_shadow_log` and
    `dfs_call_log` (`:523-560`)
  - **No tracing.**
- `observability_ecosys.tf` (761 lines): log retention (`:87`, `:96`) and app alarms (NAT, Booking, CIS 5xx and p95,
  TripPlanner Lambda errors and throttles, RDS). No tracing.
- `rg -i "xray|x-ray|tracing_config|aws-otel|\badot\b|opentelemetry|\botel\b|otel-collector|AWSXRay"` over
  tf/json/yml/tfvars → **0** (V18). No X-Ray IAM permission is granted in Terraform.
- `modules/langfuse/{main,outputs,variables}.tf`: 0 bytes each.

### 3.3 ECS, Lambda, X-Ray (live, read-only)

- **ECS: one container per task, no sidecar.**
  - `aa-cis-dev-api:906` (container `api`), `aa-cis-dev-worker:472` (`worker`), `aa-booking-dev-api:84`,
    `aa-crm-dev-api:76`.
  - Environment names matching OTEL / SENTRY / LANGFUSE / LLM_ / XRAY: CIS api none; CIS worker `S1_WRITER_V2`,
    `T9_FAQ_LLM_FILTER`; Booking `SENTRY_REQUIRED` plus the secret `SENTRY_DSN`.
  - Terraform: one element per `container_definitions` (`modules/ecs/main.tf:569`, `:786`; `booking.tf:349`;
    `crm_app.tf:389`; `crm_web.tf:253`; `crm_portal.tf:235`).
- **Lambda.** All 8 functions (`aa-tripplanner-dev-assembly`, `-browse`, `aa-cis-dev-dfs-balance-check`,
  `aa-cis-dev-rds-snapshot-expiry`, 4 identity triggers) have `Layers: null`, `TracingConfig: PassThrough` and
  `LogFormat: Text`.
- **X-Ray.**
  - `get-trace-segment-destination` → `XRay` / `ACTIVE`, the default. Transaction Search is off, and no `aws/spans`
    log group exists.
  - `get-trace-summaries` over 6 hours → 0.
  - `get-indexing-rules` → Default, `DesiredSamplingPercentage: 0.0`.

### 3.4 Business context at call time

| Context | Source today | Reachable from a span in `generate()` | Change needed |
|---|---|---|---|
| `stage` | `LLMRequest.stage` (`models.py:22`) | direct | none (stage-less `segment_research*` calls: give them a stage) |
| role, route position, model, account, fallback, tokens, cost, stop_reason, `provider_requests` | `StageConfig` (`client.py:360`), `_call_route` position (`:435`), `LLMResponse` (`models.py:32-61`) | yes | none |
| `job_id` | ContextVar `call_log.py:44` (`current_job_id()` `:47`), bound per job at `shared/jobs/worker.py:241`; copied into `to_thread` workers; the shadow thread re-binds it (`client.py:480-493`) | `current_job_id()` | none |
| `job_kind` | `structlog.contextvars` (`worker.py:220`) | `structlog.contextvars.get_contextvars()["job_kind"]` | none (or a call_log ContextVar for cleanliness) |
| `tenant_id` | ContextVar `call_log.py:67` (`current_tenant_id()` `:70`), from the payload (`worker.py:241`); API `/v1/*`: structlog only (`rate_limit.py:96`) | jobs: yes; API: only the structlog var | small, if API calls must carry it |
| eval run | ContextVar `call_log.py:91` (`eval_label()`) | yes | none |
| `request_id` (API) | structlog contextvars (`request_id.py:92`) | yes | none |
| `tour_id` | payload only: `s1_rewrite_job.py:53`, `a3_atomize_job.py:105`; T2 uses `published_tour_id` (`t2_rewrite_job.py:9`) | no | bind next to `job_id` at `worker.py:241` (a `job_subject()` helper like `job_tenant_id()`) |
| `wave` | not at call time. `shared.rerun_wave` is joined afterwards on `job.payload->>'tour_id'` and a time window (`services/waves/report.py:42-52`) | no | add `wave_id` to the enqueue payload, or join on `job_id` in the backend afterwards |
| `conversation_id` candidate | `job_id`: one tour rewrite or one T9 piece per job | `gen_ai.conversation.id = job_id` | none |

**Two context traps for span parenting:**
- `threading.Thread` does not copy contextvars (comment `client.py:476`), so the shadow span must be linked to the
  primary span explicitly.
- T7 judge calls run on the event loop (`debate.py:264`), so the exporter must be a `BatchSpanProcessor`.

**TripPlanner.**
- Available: `stage`, role, model, account, position and `failed` on each `Call` (`llm_gateway.py:86-102`), and
  `request_id` (structlog).
- Trip and session ids are deliberately never logged (AA-827, `observability.py:16`). Spans must follow the same rule.

---

## 4. Options compared

Common to every option:
- A bootstrap module that registers one `TracerProvider` per process (CIS api, CIS worker, each TP Lambda) with a
  pinned exporter and a `BatchSpanProcessor`.
- A kill switch.
- Infra to receive spans (section 5). Infra hours are listed separately.

All hours are **rough engineering estimates, not verified** by a task breakdown in an issue.

### A. Anthropic SDK tracing, plus manual spans for everything else

**What it means here.**
- Add `anthropic[bedrock]==2.3.0` and move the Messages API transports onto `AnthropicBedrock`: `_call_bedrock`
  (`client.py:591`), `invoke_claude` / `_invoke_streaming` (`bedrock_satellite.py:161-297`), and TP `_text_call`
  (`anthropic_native` branch).
- Pass the acc3 assumed-role credentials (`bedrock_satellite.py:115`) as `aws_access_key` / `aws_secret_key` /
  `aws_session_token` (`anthropic/lib/bedrock/_client.py:141-146`).
- Converse calls (every catalog key: `sonnet-5-5` for the live S1 writer, the GPT judges and validators), OpenAI,
  Cohere and Jev would all still need manual spans.

**Files to change:** `client.py` (983 lines), `bedrock_satellite.py` (297), `requirements.txt`, TP
`llm_gateway.py` (591) and `backend/requirements.txt` (the Lambda zip grows by `httpx2` and the SDK), manual spans in
`client.py` / `embed.py` / `decide.py`, and streaming-parity tests against `stream_sink`.

**Effort:** about 40–56 h.

**Risks:**
- It rewrites the transport of every legacy writer stage only to gain tracing.
- It covers neither the live S1 writer (Converse) nor any judge.
- Its default `max_content_bytes` (750,000) is above the X-Ray 200 KB span limit (section 5), so content mode must
  lower it.
- Two span schemas end up in one trace: the SDK's own gen_ai attributes beside manual ones.
- No job, stage or fallback context unless set per request (`conversation_id` via `with_options`).

**Kill switch:** `ANTHROPIC_OPEN_TELEMETRY=false`, or `open_telemetry=False` on the client (`_types.py:209-213`).

### B. One gen_ai wrapper span at the gateway for both vendors (recommended)

**Span shape.**
- Logical span: `CLIENT` kind, named `chat {model}` / `embeddings {model}`, opened in `LLMClient.generate`
  (`client.py:327`) next to `stream_sink.emit_call_start`.
- Attempt spans: one child per attempt in `_call_key_logged` (`client.py:413`), the function that every route
  attempt, single-key call and shadow call goes through. Inside the legacy chain, the T1.5a → T2.5a tiers
  (`:538-571`) become span events with `error.type`.
- Shadow span: started in `_run_shadow` (`:488`) with a **link** to the primary span (a plain thread has no parent
  context).
- The same wrapper in `embed()` (`embed.py:124`) and in `_call_jev` (`decide.py:244`). Putting it in `_call_jev`
  rather than `decide()` also covers the canary bypass. TripPlanner: `generate_text` and `embed_texts`
  (`llm_gateway.py:265`, `:388`).

**Attributes.**
- Standard gen_ai: `gen_ai.operation.name`, `gen_ai.provider.name` (`aws.bedrock` / `openai`, matching what the
  Anthropic SDK emits), `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.input_tokens` /
  `output_tokens`, `gen_ai.conversation.id` = job id.
- AA-specific: `aa.stage`, `aa.role`, `aa.job_id`, `aa.job_kind`, `aa.tenant_id`, `aa.eval_run`, `aa.account`,
  `aa.route_position`, `aa.fallback_used`, `aa.cost_usd`, `aa.stop_reason`, `aa.provider_requests`,
  `aa.billed_unusable`, `aa.shadow`.
- Per attempt: `error.type` and the error text truncated to 1 KB. This is the structured fallback reason that does
  not exist today.
- Content is **off**. A `content` mode, for one debug job only, caps text at 100 KB per span.

**Files to change:**
- new `shared/observability/tracing.py` (bootstrap, kill switch, attribute helpers)
- `shared/llm_client/client.py`, `embed.py`, `decide.py`
- `shared/jobs/worker.py:241` (optional tour ContextVar) and `call_log.py`
- `api/main.py:98` and `worker/__main__.py:18` (bootstrap next to `configure_for_process`)
- `requirements.txt` (explicit pins)
- TP `backend/shared/llm_gateway.py`, `backend/shared/observability.py`, `backend/requirements.txt`
- unit tests with `InMemorySpanExporter` (35 existing gateway test files match `llm|gateway|satellite|decide|embed|shadow|judge`)

**Effort:**

| Work | Hours |
|---|---|
| Bootstrap and kill switch (both CIS processes) | 2–3 |
| Text gateway spans: `generate`, `_call_key_logged`, legacy tiers, billed-unusable, shadow link | 6–8 |
| Embed and Jev (`_call_jev`, canary included) | 2–3 |
| Unit tests | 4–5 |
| TripPlanner gateway and Lambda bootstrap | 3–4 |
| Optional tour/subject ContextVar | 1–2 |
| **Code total** | **about 18–25** |
| Infra PR: worker task-role IAM, env flags, Transaction Search (if X-Ray) | 3–4 |

**Risks:**
- We own the attribute schema. Mitigation: follow the semconv gen_ai span spec, pin
  `opentelemetry-semantic-conventions`, and keep `aa.*` for our own keys.
- `BatchSpanProcessor` only, because T7 judges run on the event loop.
- The span must close on every raise path (`_call_route` re-raises the `RouteUnusableReply`, `:468-472`).
- `quality_signal` and role overrides written later by callers stay in `llm_call_log`. Reconcile by `job_id`.

**Kill switch:**
- `AA_LLM_TRACING=off` (default off): the bootstrap registers no provider, so every span is a no-op.
- Plus the spec variable `OTEL_SDK_DISABLED=true` (verify against the pinned SDK in the pilot).
- A task-def env change, with no code change.

### C. Contrib or vendor auto-instrumentation

- **C1, `opentelemetry-instrumentation-botocore==0.66b1`** (Beta):
  - Gives gen_ai spans for `Converse`, `ConverseStream` and Claude `InvokeModel*` with no client change.
  - Does **not** cover Cohere `InvokeModel` (plain AWS span), Batch, or Jev.
  - Not verified: whether it detects the model family from the `global.` inference-profile IDs/ARNs the code sends
    (`bedrock_satellite.py:76-84`, `client.py:756`). It also traces every boto3 call (S3, Secrets Manager, STS),
    which adds noise.
  - Effort 3–5 h. Kill: `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=botocore`.
- **C2, `opentelemetry-instrumentation-openai-v2==2.4b0`** (2026-05-01):
  - Covers `chat.completions.create`. This is the rare path: only `gpt-6-luna-openai` as the last judge fallback.
  - `openai` is unpinned (`requirements.txt:6`, `>=1.16.2`; PyPI latest is 3.41.0). Compatibility with openai 3.x
    is not verified.
  - Effort 1–2 h.
- **C3, Sentry AI monitoring** (already installed):
  - Its OpenAI and Anthropic integrations make gen_ai spans automatically, but there is no Anthropic SDK here, and
    Bedrock gets only HTTP spans.
  - The worker would need a Sentry transaction per job, plus manual `gen_ai.*` spans, which is Option B written
    against the Sentry API instead of OTel. It is tied to one vendor, and the Sentry plan's span quota is not known.
  - Effort about B's, minus the exporter work.

### Verdict

| | A | B | C1 botocore | B + C1 |
|---|---|---|---|---|
| Claude, legacy `haiku`/`sonnet` (Messages API) | yes, after a rewrite | yes | yes (profile-ID detection not verified) | yes |
| Claude on Converse (`sonnet-5-5`: live S1 writer) | **no** | yes | yes | yes |
| GPT on Bedrock Converse (judges, validators) | no (manual) | yes | yes | yes |
| OpenAI last resort | manual | yes | no (needs C2) | yes |
| Cohere embeddings / Jev | manual | yes | plain AWS / no | yes |
| Business context (stage, job, tenant, position) | manual | **yes** | no | **yes** |
| Structured fallback reason | partial | **yes** | per wire call | **yes** |
| Client code changes | large | small | none | small |
| Code effort (rough) | 40–56 h | 18–25 h | 3–5 h | 21–30 h |

Start with **B**. Add C1 only if the pilot shows a need for Bedrock wire timing below the attempt span.

---

## 5. Backend options (trade-offs; the choice belongs in an ADR)

**Dev volume used for cost.**
- `llm_call_log` grew from ~252k rows (S238, 2026-10-15) to ~383.8k (2026-10-29 dump): about 131k rows in 14 days,
  Jev rows included, during wave weeks.
- Logs Insights, 7 days, worker: `llm_success` 29,352 and `llm_embed_success` 1,145 (V15). Daily `llm_success` +
  `llm_route_used` swings from 289 (23/10) to 32,593 (26/10) (V16b), so volume is bursty.
- Planning figure for a wave month: ≤ 300k logical calls. Metadata-only spans at about 2.5 spans per call and
  ~1.5 KB each come to about 4 KB per call, so **about 1.2 GB a month**. Content mode on writer calls adds about
  30 KB per call.

| Backend | How | Monthly cost at Dev volume | Pros | Cons |
|---|---|---|---|---|
| **ADOT → X-Ray / CloudWatch Transaction Search** | OTLP/HTTP to `https://xray.us-west-1.amazonaws.com/v1/traces` with SigV4. HTTP only, no gRPC. Limits: 5 MB per request, 10,000 spans per request, **200 KB per span**, 16 KB per resource+scope (AWS OTLP endpoint doc). In-process ADOT distro exporter, no sidecar. Enable Transaction Search (spans land in `aws/spans`); IAM `AWSXrayWriteOnlyPolicy` on the worker/api task roles; ADOT layer for Lambdas | Span ingest $0.35/GB → about **$0.40–2** (1.2 GB metadata; ~5 GB with content). 1% indexing included; extra indexing $0.75 per million spans. Free tier: 100 GB for 3 months. Logs storage about $0.03/GB-month. Rates come from the CloudWatch pricing page's examples; us-west-1 rates not verified | Stays in acc2: no new vendor, no secret, tenant content never leaves AWS (consistent with S235 "Bedrock first"); joins CloudWatch alarms and the JSON logs by `job_id` | Weak LLM-specific UI (no prompt/cost views). Whether the CloudWatch GenAI dashboard shows spans from a plain ECS app is not verified. Set the sampler explicitly and keep `OTEL_AWS_APPLICATION_SIGNALS_ENABLED=false` |
| **Langfuse Cloud** | OTLP/HTTP `/api/public/otel/v1/traces`, Basic auth | Hobby is free up to 50k units, which is too small for a wave month. **Core $29 + $8 per 100k units** above 100k: about $29 in a quiet month, **about $60–80** in a wave month (~300k calls × ~2.5 units). US, EU or Japan region | LLM-native UI: sessions (`job_id`), cost and latency per stage, prompt view | **Data leaves AWS** (conflicts with the S235 rationale once content mode is on); a new vendor and secret; the pinned `langfuse==2.26.0` is not OTel-based (dead code anyway); Langfuse v3+ needs its own SDK pins |
| **Langfuse self-hosted** | Same OTLP endpoint; new infra (web + worker + Postgres + ClickHouse + Redis + S3) | No license cost. Infra estimated at **$60–150/month** on ECS Fargate ARM + RDS/ClickHouse (not verified) | Data stays in acc2 | Largest ops load; the old module is empty and the stack was removed in AA-23 |
| **Grafana Cloud (Tempo)** | OTLP gateway, Basic auth in `OTEL_EXPORTER_OTLP_HEADERS` | Free tier 50 GB/month and 14-day retention → **$0** at this volume; Pro $19/month for 30-day retention | Good trace UI (TraceQL) | Data leaves AWS; no LLM views; a new vendor |
| **Sentry** (already on) | Sentry SDK spans or its OTel integration | Depends on the current Sentry plan's span quota (not checked) | Already wired, with release and job tags | Vendor-specific API; Bedrock not auto-covered; data leaves AWS |

Not proposed: the Anthropic server-side telemetry destination. It applies to the Claude API, not to Bedrock (S238
finding, not re-checked).

**Independent of the backend:**
- Keep `llm_call_log` as the source of truth for cost and audit. Traces are for latency, fallback and debugging.
- Keep the exporter behind the env flag.

---

## 6. Pilot plan

**Scope.**
- One stage family: the S1 rewrite. That is job kind `s1_rewrite` (`services/jobs/s1_rewrite_job.py:40`,
  `concurrency=6`, `max_attempts=1`, `:43`), with the writer v2 flag on the worker.
- Its LLM stages:
  - `s1_generate`: `sonnet-5-5` Converse on acc3, streaming under the sink at `:91`, up to 3 calls per draft
  - `s1_source_facts`: gpt-6-luna → …
  - `s1_flag_fix`, `s1_itinerary_nudge`: legacy haiku on acc3
  - `s1_judge` / `s1_brand_audit`: GPT judge route, with a possible shadow
  - Jev `s1_grounding`
- One pilot therefore exercises Converse streaming, the legacy acc3 chain, the judge route and Jev.
- "metadata_only in prod" means Dev here (there is no prod stack); content stays off.

**Steps** (each a separate issue/PR; none done here):
1. ADR: the backend (section 5) and the attribute schema (gen_ai + `aa.*`).
2. CIS PR: build B behind `AA_LLM_TRACING` (default off). Pin the OTel set that matches the backend. Use
   `BatchSpanProcessor` and a parent-based ratio sampler (1.0 on the pilot worker only). Content off. Unit tests with
   `InMemorySpanExporter`.
3. Infra PR + apply: IAM write on the worker task role, the env flag (Terraform), and for X-Ray, enabling
   Transaction Search. No sidecar.
4. Turn the flag on for **`aa-cis-dev-worker` only**. Run **one small wave of 3 tours** (`/admin/waves`, the
   `aa-wave-rerun` 3-tour rung) in one country. Expected LLM cost about $0.05 per tour (S254 job `209d9e60`:
   $0.0514), so about **$0.15–0.30**. Tracing cost: under $0.01.
5. Optional: content mode for one job, with `max_content_bytes ≤ 100 KB`, then off.

**Success criteria:**
- Every pilot `llm_call_log` row (`job_id IN pilot`) has exactly one logical span with the same `stage`, `model`,
  `account` and token counts. Shadow rows (`quality_signal->>'shadow'`) match a shadow span.
- Every `satellite_invoke_failed`, `llm_route_attempt_failed` and `converse_schema_retry` log line of those jobs
  has a matching attempt span with `error.type` (join on `job_id`).
- The S1 job p95 duration regresses by less than 2% against the last `s1_rewrite` jobs (`shared.job` timings).
- 0 exporter errors in `/ecs/aa-cis-dev`, 0 spans rejected for size, and no prompt or output text in spans while
  content is off.

**Rollback:** set `AA_LLM_TRACING=off` on the worker task and roll the service. The code is a no-op without a
provider. Revert the infra PR if needed.

---

## 7. Open questions

1. **Backend:** X-Ray Transaction Search (in AWS, cheapest, weak LLM UI) or Langfuse (best UI; Cloud sends data out,
   self-host costs ops)? Proposed answer: X-Ray for the pilot; revisit Langfuse self-host only if the UI gap hurts.
2. **Spike** before the PR? One paid call with `ConsoleSpanExporter` to see real spans:
   - (a) B's wrapper around one `converse` call
   - (b) `BotocoreInstrumentor` on the same call, to check the profile-ID model detection
   Cost: a few cents. Proposed: run (b) inside the pilot instead of a separate spike.
3. With no account fallback since AA-998, should the legacy Haiku tier fall back to a **model** on acc3 (for example
   `haiku-5-5` via Converse), so that a 25–26/10-style acc3 Haiku outage (139 failures in 18 h) degrades instead of
   failing? This is a routing question, not tracing; it needs its own issue.
4. Should `wave_id` go into the job payload at enqueue, so spans carry it live (today it is derived afterwards,
   `waves/report.py:42-52`)?
5. Should the two guards also catch httpx LLM calls (the Jev canary) and stage-less `LLMRequest`s
   (`segment_research*`), so every call is guaranteed a span with a stage?
6. Should the API process be traced, or only the worker and Lambdas? API LLM calls are rare (admin repairs, the
   canary).
7. Pin OTel explicitly now? `opentelemetry-api` floats in through fastapi, and a fastapi bump can move it.
8. Fix the TripPlanner sync-in-async calls (`handler.py:583`, `search.py:134`) first? Otherwise spans show
   event-loop blocking as LLM latency.

---

## Appendix: Verify

All searches: ripgrep 14.1.1 on `git archive origin/main` snapshots, excluding `tests/**` unless stated.

### Call sites, CIS (`92934598`)
| # | Command | Result |
|---|---|---|
| V1 | `rg -n --type py -g '!tests/**' -e '^\s*(import\|from)\s+(anthropic\|openai)\b' -e 'AnthropicBedrock\|AsyncAnthropic\|OpenAI\(\|AsyncOpenAI' .` | **2** (`client.py:10`, `:323`) |
| V2 | `rg -n --type py -g '!tests/**' -e '\.(invoke_model\|invoke_model_with_response_stream\|converse\|converse_stream\|create_model_invocation_job)\(' -e 'chat\.completions\.create\|responses\.create\|messages\.create\|messages\.stream\|embeddings\.create' .` | **8** lines, all in `shared/llm_client/` except a docstring at `services/acp_shared/tracer.py:100`; plus `rt.converse` / `rt.converse_stream` passed as callables at `client.py:807`, `:846` |
| V3 | `rg -n --type py -g '!tests/**' -g '!shared/llm_client/client.py' -e '\.generate\(' .` | **38** lines (call sites plus docstrings; the call sites are listed in 2.2) |
| V4 | AST read of `tests/unit/test_aa927_llm_call_site_registry.py` | `LOGGED_CALL_SITES` **41**, `EXCLUDED` **5** |
| V5 | `rg -n --type py -g '!tests/**' -e '\.generate\b[^(]' -e 'call_judge\(\|invoke_judge\('` | callables passed to `to_thread`: `acp_angle_gate/generate.py:141`, `segment_research.py:492`, `segment_research_batch.py:191`, `a3_atomize.py:145` |
| V6 | `rg -n "s1_atom_writer\|t10_claims\|tp_extract\|tp_component_embed" --type py -g '!tests/**'` | only route/default definitions, no caller |
| V7 | `rg -n --type py -g '!tests/**' -g '!shared/llm_client/**' -e 'from shared\.llm_client\.embed import\|llm_client import embed' .` | **4** (`places/llm.py:58`, `content_embedding.py:42`, 2 scripts) |
| V8 | `rg -n --type py -g '!tests/**' -g '!shared/llm_client/decide.py' -e 'await decide\(\|decide_sync\(\|decide_mod\.(decide\|_call_jev)\(\|_call_jev\(' . \| wc -l` | **18** (13 files) + canary `admin_llm_ops.py:1218` |
| V9 | `rg -n --type py -g '!tests/**' 'stream_sink\.bind\(' services api worker` | 4 (`writing_progress.py:246`, `s1_rewrite_job.py:91`, `t9_write_job.py:47`, `t2_rewrite_job.py:440`) |
| V10 | `rg -n --type py -g '!tests/**' -g '!shared/llm_client/call_log.py' -e '\brecord_call(s)?(_sync\|_with_pool)?\(\|record_(billed_failure\|unusable)(_sync)?\(' . \| wc -l` | **65** lines in **32** files |
| V11 | `rg -n --type py -g '!tests/**' "bound_contextvars\|bind_contextvars" .` | 3 (`worker.py:220`, `request_id.py:92`, `rate_limit.py:96`) |
| V12 | `rg -n --type py -e '\.(invoke_model\|…\|converse_stream)\(\|completions\.create\|get_satellite_client\|invoke_claude' scripts worker docker` | 0 raw calls (the probe goes through `embed_mod._call`) |

### Call sites, TripPlanner (`c961e12`)
| # | Command | Result |
|---|---|---|
| TP1 | `rg -n --type py -g '!tests/**' -e '^\s*(import\|from)\s+(anthropic\|openai)\b' -e '\.(invoke_model\|invoke_model_with_response_stream\|converse\|converse_stream)\(' -e 'completions\.create\|messages\.create\|embeddings\.create' backend` | **3** wire calls (`llm_gateway.py:244`, `:253`, `:405`), 0 imports |
| TP2 | `rg -n --type py -g '!tests/**' -e 'generate_text\(\|embed_texts\(\|load_route\(' backend` | 4 (`search.py:119`, `:134`, `handler.py:506`, `agent.py:88`) |

### Observability
| # | Command | Result |
|---|---|---|
| V13 | `rg -n --type py "opentelemetry\|\bOTEL_\|\botel\b"` over CIS and TP `backend` (excluding `tests/**`) | 0 imports or uses |
| V14 | `rg -n "start_transaction\|start_span\|sentry_sdk.trace" --type py -g '!tests/**'` (CIS) | 0 |
| V15 | `aws logs start-query --log-group-name /ecs/aa-cis-dev` over 7 days (1792639807–1793244607): `filter event in [...] \| stats count(*) by event, service` | worker: `llm_success` 29,352; `llm_route_used` 26,535; `t2_5a_satellite_used` 8,597; `llm_embed_success` 1,145; `t1_5a_satellite_used` 477; `satellite_invoke_failed` 140; `converse_schema_retry` 10; `llm_route_attempt_failed` 1; `t1_failed_trying_t2`, `t2_failed_trying_t2_5a`, `llm_openai_fallback_used`: absent (0). Only JSON lines have `event`, so these are lower bounds |
| V16 | same group: `filter event like /satellite\|_5b_\|acc1\|fallback\|failed_trying\|route_attempt\|openai/ \| stats count(*) by event, error_type, account` | `satellite_invoke_failed` `ServiceUnavailableException` acc3 **139**, acc1 1; `t2_5a_satellite_failed_trying_t2_5b` 139; `t2_5b_satellite_used` (acc1) 138; `t2_5b_satellite_failed_trying_t3` 1. Hourly view: 2026-10-25 17:00 UTC → 2026-10-26 12:00 UTC (49 + 58 + 26 in the peak hours) |
| V16b | same group: `filter event in ["llm_route_used","llm_success"] \| stats count(*) as n by bin(1d)` | 22/10 403, 23/10 289, 24/10 10,640, 25/10 9,546, 26/10 32,593, 27/10 1,660, 28/10 750, 29/10 (partial) 6 |
| V17 | `filter @message like /sentry/ or @message like /Sentry/ \| stats count(*) by event, service` (7 days) | 12 lines, none "Sentry DSN not found" |
| V18 | Infra: `rg -n -i "xray\|x-ray\|tracing_config\|aws-otel\|\badot\b\|opentelemetry\|\botel\b\|otel-collector\|AWSXRay" -g '*.tf' -g '*.json' -g '*.yml' -g '*.yaml' -g '*.tfvars' -g '!dist/**' .` | 0 |
| V19 | `aws ecs describe-services` + `describe-task-definition` (api, worker, booking, crm) | 1 container each; env and secret names as in 3.3 |
| V20 | `aws lambda list-functions --query "Functions[].{n:FunctionName,layers:Layers[].Arn,tracing:TracingConfig.Mode}"` | 8 functions, `layers: None`, `PassThrough`, `Text` |
| V21 | `aws xray get-trace-segment-destination`, `get-trace-summaries` (6 h), `get-indexing-rules`, `aws logs describe-log-groups --log-group-name-prefix aws/spans` | `XRay`/`ACTIVE`; 0 traces; Default 0.0%; no group |
| V22 | `aws secretsmanager list-secrets` filtered on sentry/langfuse/otel/grafana; `list-secret-version-ids --secret-id aa-cis/dev/sentry-dsn-api` | 5 Sentry secrets (CIS, Booking, TripPlanner, CRM, CRM portal), no Langfuse/OTel/Grafana; CIS DSN `AWSCURRENT` since 2026-10-17 |

### Dependency pins

**AA-CIS-App `requirements.txt`** (no lock file; `Dockerfile:2` `FROM python:3.12-slim`, `:17` `pip install -r
requirements.txt`):
```
2:boto3==1.43.49
3:botocore==1.43.49
6:openai>=1.16.2                  (unpinned; PyPI latest 3.41.0, 2026-10-28)
10:langgraph==1.2.16             (no opentelemetry in requires_dist)
28:fastapi==0.161.1              (requires opentelemetry-api>=1.44.0; sdk/exporter only in extras)
31:httpx>=0.27.0
45:sentry-sdk[fastapi]>=1.40.0   (unpinned; PyPI latest 2.73.0)
46:langfuse==2.26.0              (no opentelemetry in requires_dist)
51:structlog==24.1.0
anthropic: absent
opentelemetry-*: absent (only opentelemetry-api, transitively via fastapi; inferred, not probed in the image)
```

**AA-TripPlanner-Web `backend/requirements.txt`:**
```
2:asyncpg==0.30.0
4:boto3==1.35.36
6:httpx==0.27.2
8:structlog==25.5.0
9:sentry-sdk==2.70.0
anthropic / openai / opentelemetry-*: absent
```

**anthropic** (PyPI + wheel 2.3.0): releases 1.14.0 (2026-10-14, first with OTel) … 1.17.0 (2026-10-20), 2.0.0
(2026-10-21, "BREAKING: new API version 2026-10-21"), 2.3.0 (2026-10-23). `requires_dist` includes
`httpx2<3,>=2.0.0`, `opentelemetry-api<2,>=1.1.0`; extra `bedrock`: `boto3>=1.28.57`, `botocore>=1.31.57`;
`requires_python >=3.10`. Option docs: `anthropic/_types.py:118-213`; Bedrock client option:
`anthropic/lib/bedrock/_client.py:154`; provider name: `:95`.

**OTel on PyPI (2026-10-29):**
- `opentelemetry-api` / `-sdk` / `-exporter-otlp-proto-http` 1.45.1 (2026-10-06)
- `opentelemetry-semantic-conventions` 0.66b1
- `opentelemetry-instrumentation-botocore` 0.66b1 (requires `opentelemetry-propagator-aws-xray~=1.0`)
- `opentelemetry-instrumentation-httpx` 0.66b1
- `opentelemetry-instrumentation-openai-v2` 2.4b0 (2026-05-01)
- `aws-opentelemetry-distro` 0.21.0 (2026-10-01; pins `opentelemetry-api==1.44.0`, `opentelemetry-distro==0.65b0`,
  `opentelemetry-exporter-otlp-proto-http==1.44.0`)

### Spike
Not run. No paid call was made (open question 2).
