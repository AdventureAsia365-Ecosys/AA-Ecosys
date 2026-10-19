# AA-842: LLM observability through OpenTelemetry (gen_ai)

Read-only investigation, S238, 2026-10-15. Local file only: AA-CIS-App ignores `docs/` (`.gitignore:41`), so this file is not committed.

**Sources**
- Code: `git archive origin/main` snapshots. AA-CIS-App is `d224c4d3`, AA-TripPlanner-Web is `082380a`, AA-CIS-Infra is `ccd0f89`. Every file:line in this report refers to these snapshots.
- Live image: **newer than the code snapshot.** `origin/main` moved to `ef0930b9` (committed 2026-10-15 21:14 +07), and live now runs `aa-cis-dev-api:625` / `aa-cis-dev-worker:182`, image `aa-cis-dev-api:dev-ef0930b938975462…`, both registered at 21:16 +07 (`aws ecs describe-services` + `describe-task-definition`). The LLM gateway is unchanged: `git diff --stat d224c4d3 origin/main -- shared/llm_client` is empty, so the conclusions hold for live.
- Line moves on current `main` (`ef0930b9`): `itinerary_utils.py` `client.generate` is at `:123` (snapshot `:122`), and `t2_rewrite_job.py` `stream_sink.bind` is at `:362` (snapshot `:355`). Other cited lines were re-checked where this report was corrected; the rest are still snapshot `d224c4d3` lines. Infra `origin/main` is now `8bd4659`: `modules/ecs/main.tf` `container_definitions` are at `:293` and `:490` (snapshot `ccd0f89`: `:276`, `:465`), and `accounts/aa365/observability.tf` lines after `:290` shift by +4.
- Database: SELECT-only reads of `shared.llm_role_config` (30 rows) and `shared.llm_model_catalog` (11 rows) through `.tmp-session/s237/exec_s3out.sh`. The outputs are `.tmp-session/s238/aa842_routes.json` and `.tmp-session/s238/aa842_s2_probe_out.json` (the image package probe). The 7-day CloudWatch counts are in `.tmp-session/s238/aa842_cw_counts.json`.
- AWS: read-only describe and list calls on acc2 (`005097885195`).
- What was not done: no paid LLM call, no spike, no code change, no dependency change, no Terraform, and no ECS or Lambda config change.

---

## 1. Summary and recommendation

**Is it already there? No.**
- No LLM trace is emitted anywhere today.
- No Python code imports `opentelemetry` (`rg` count 0).
- X-Ray has 0 traces in the last 6 hours.
- No ECS service has a collector sidecar, and no Lambda has a layer.
- Sentry is wired in code but its DSN secret is missing on acc2, so it is off.
- Langfuse is dead code: `AcpTracer` has 0 importers and its Terraform module files are empty.

**Can we do it? Yes, but not the way the idea assumed.**
- **Neither repo uses the `anthropic` SDK.** All Claude calls go through raw boto3: `invoke_model`, `invoke_model_with_response_stream`, `converse` and `converse_stream`.
- So the SDK's built-in OTel tracing (Option A) would mean adding a new dependency and rewriting the Bedrock transport onto `AnthropicBedrock`.
- The SDK's OTel support only shipped in `anthropic` v1.14.0, published 2026-10-14, the day before this investigation.

**Recommendation: Option B, with Option C's botocore instrumentor as an optional child layer.**

Option B puts one gen_ai wrapper span at the gateway choke points, which already exist:
- `LLMClient.generate`, `client.py:122`
- `embed()`, `embed.py:122`
- `decide()`, `decide.py:672`
- TripPlanner `generate_text` and `embed_texts`, `llm_gateway.py:235` and `:267`

At the gateway, the span carries what no vendor SDK can know:
- `stage`, `role`, `job_id`, `tenant_id`
- the position in the fallback route
- the account (acc2, acc3 or acc1)

It also records each failed attempt as a span event. Today the reason for a failed attempt lands only in structlog text, never in the database.

`opentelemetry-instrumentation-botocore` (Option C) can optionally add per-attempt Bedrock wire spans underneath, with no change to the client code.

**Pin these explicitly.** Today OTel arrives only as a transitive, unpinned dependency, and the gen_ai conventions are still `Development` status. **The pin set depends on the backend** (section 5):
- **Collector-less X-Ray through ADOT** (`aws-opentelemetry-distro==0.21.0`): PyPI requires `opentelemetry-api==1.44.0`, `opentelemetry-sdk==1.44.0`, `opentelemetry-exporter-otlp-proto-http==1.44.0` and `opentelemetry-instrumentation-botocore==0.65b0`. That is compatible with `chromadb==0.4.24` (`opentelemetry-api/sdk >=1.2.0`) and `fastapi` 0.143.2 (`opentelemetry-api>=1.44.0`). The installed 0.66b1 contrib packages (`instrumentation`, `-asgi`, `-fastapi`) would have to move to the matching 0.65b0 line; a resolver run is not verified. Plain `opentelemetry-exporter-otlp-proto-http` has no SigV4 auth, so X-Ray OTLP needs the ADOT exporter or a collector.
- **Non-ADOT OTLP backend** (Langfuse, Grafana) **or a sidecar collector**: `opentelemetry-api==1.45.1`, `opentelemetry-sdk==1.45.1`, `opentelemetry-exporter-otlp-proto-http==1.45.1`, `opentelemetry-semantic-conventions==0.66b1`, and, if the C layer is used, `opentelemetry-instrumentation-botocore==0.66b1`.
- If TripPlanner Lambdas are instrumented: a pinned ADOT layer version.

Do **not** add `anthropic` for this work. If a later ADR moves Bedrock onto the SDK, pin `anthropic[bedrock]==1.14.0` exactly.

**Side finding: every legacy writer call wastes one round-trip.** It makes one guaranteed-failing acc2-native attempt (`ValidationException … not available for channel program accounts`) before reaching acc3. Logs Insights on `/ecs/aa-cis-dev`, last 7 days (`filter @message like /t2_failed_trying_t2_5a|t2_5a_satellite_used|t1_failed_trying_t2|t1_5a_satellite_used|llm_route_attempt_failed|llm_openai_fallback_used/ | parse … | stats count(*) by ev`; output `.tmp-session/s238/aa842_cw_counts.json`):
- `t2_failed_trying_t2_5a` = 1,428 (1,424 worker, 2 api, 2 other streams), and `t2_5a_satellite_used` = 1,427
- `t1_failed_trying_t2` = 954, and `t1_5a_satellite_used` = 954
- `llm_route_attempt_failed` = 32 (worker, 2026-10-12 10:10 to 2026-10-13 02:14 UTC); `llm_openai_fallback_used` = 0

That is about **2,382 wasted acc2 attempts in 7 days**. The B span would make this visible per call. Fixing it is a separate issue.

---

## 2. Call sites

### 2.1 Physical wire calls (where bytes leave the process)

| file:line | function | client / API | sync/async | stream | via gateway |
|---|---|---|---|---|---|
| CIS `shared/llm_client/client.py:360` | `_call_bedrock` (acc2-native legacy tier) | boto3 `invoke_model_with_response_stream` | sync | always | inside |
| CIS `client.py:522`, `:542` (schema retry) | `_call_bedrock_converse` | boto3 `converse` (satellite session) | sync | no | inside |
| CIS `client.py:550` | `_call_bedrock_converse` | boto3 `converse_stream` | sync | only with a bound stream sink and no `json_schema` (`:516`) | inside |
| CIS `client.py:632` | `_call_openai` | `openai.OpenAI().chat.completions.create` (client built at `:118`) | sync | no | inside |
| CIS `shared/llm_client/bedrock_satellite.py:326` | `invoke_claude` (acc3/acc1) | boto3 `invoke_model` (`anthropic_version` body) | sync | no | inside |
| CIS `bedrock_satellite.py:228` | `_invoke_streaming` | boto3 `invoke_model_with_response_stream` | sync | only when `on_delta` is set | inside |
| CIS `shared/llm_client/embed.py:94` | `_call` | boto3 `invoke_model` (Cohere Embed v4) | sync | n/a | inside `embed()` |
| CIS `shared/llm_client/decide.py:250` | `_call_jev` | `httpx.AsyncClient.post` to `api.typesafe.ai/v1/systemone` (`:45`) | async | no | inside `decide()` |
| CIS `shared/llm_client/bedrock_batch.py:171` | `submit_batch_job` | boto3 `create_model_invocation_job` (Batch API, offline; caller `s1_batch.py:208`) | sync | n/a | separate path |
| TP `backend/shared/llm_gateway.py:214` | `_text_call` (`anthropic_native`) | boto3 `invoke_model` | sync | no | inside |
| TP `llm_gateway.py:223` | `_text_call` (`converse`) | boto3 `converse` | sync | no | inside |
| TP `llm_gateway.py:280` | `embed_texts` | boto3 `invoke_model` (Cohere) | sync | n/a | inside |

No line in either repo imports `anthropic`, `AnthropicBedrock` or `AsyncAnthropic`. The `"anthropic_version": "bedrock-2023-05-31"` hits are request bodies, for example `client.py:349`, `bedrock_satellite.py:296` and TP `llm_gateway.py:212`.

### 2.2 Logical callers

**Stages and roles.**
- Stage and role come from the live `shared.llm_role_config`.
- "Path" means the branch `LLMClient` actually takes for that live route (section 2.3).

**Streaming.** Calls stream only under `stream_sink.bind`, which wraps them at:
- `services/jobs/s1_rewrite_job.py:75`
- `t2_rewrite_job.py:355`
- `t9_write_job.py:47`
- `acp_shared/writing_progress.py:235`

| file:line | function (sync/async) | stage → role | path / client actually used | via gateway |
|---|---|---|---|---|
| `services/content_generation/graph.py:463` | `generate_node` (sync) | `s1_generate` / `t2_generate` → writer | legacy: acc2 stream (fails) → `invoke_claude` acc3 → acc1 | yes |
| `content_generation/itinerary_utils.py:122` | `nudge_itinerary_day` (sync) | `s1_/t2_itinerary_nudge` → writer | legacy haiku | yes |
| `content_generation/flag_fix_node.py:568`, `:274` | `flag_fix_node`, `_rerepair_meta` (sync) | `s1_/t2_flag_fix` → writer | legacy haiku | yes |
| `content_generation/grounding.py:406` | `repair` (sync) | `s1_/t2_flag_fix` → writer | legacy haiku | yes |
| `content_generation/source_facts.py:245` | `extract_day_facts` (sync) | `s1_source_facts` → validate | catalog: gpt-6-luna `converse` acc3 → haiku legacy | yes |
| `content_generation/brand_fit.py:647` | `_judge` (sync) | `s1_judge` / `t2_judge` / `t7_debate_judge` → judge | gpt-5.6-luna → gpt-6-luna (`converse` acc3) → gpt-6-luna-openai (OpenAI API); 10% shadow. Called **on the event loop** from `acp_shared/debate.py:263` | yes |
| `content_generation/brand_audit_node.py:365` | `brand_audit_node` (sync) | `s1_/t2_brand_audit` → judge | gpt-5.6-luna → gpt-6-luna; 10% shadow | yes |
| `acp_produce/judge_client.py:26` | `invoke_judge` (sync) | `t10_judge` → judge | judge route including the OpenAI last step | yes |
| `acp_content_writing/generate.py:61`, `:69` | `_generate_full` (sync, run through `to_thread`) | `t9_write` → writer | legacy sonnet | yes |
| `acp_content_writing/generate.py:336` | `repair_sentences_detailed` (sync) | `t9_write` by default → writer | legacy | yes |
| `generate.py:410`, `:473` | `fit_seo_fields`, `write_faq` (sync) | `t9_repair` → writer | legacy haiku → sonnet | yes |
| `acp_angle_gate/generate.py:130` | `_generate_once` (async, `to_thread`) | `t8_angle_gen` → writer | legacy sonnet | yes |
| `acp_contract/a3_atomize.py:178`, `:349` | per-tour / per-day (async, `to_thread`) | `a3_atomize` → validate | gpt-6-luna `converse` → haiku | yes |
| `acp_shared/place_cards.py:398`, `:413` | `draft_card`, `check_card` (sync) | `a3_place_card`, `a3_place_card_check` → validate | gpt-5.6-luna → sonnet; haiku → sonnet | yes |
| `services/places/llm.py:29` | `_generate_sync` | `a3_place_days` (20% shadow), `a3_place_locate` → validate | legacy sonnet | yes |
| `shared/llm_client/column_mapper.py:79` | `detect_column_mapping` (sync) | `a0_column_map` → writer | legacy haiku | yes |
| `acp_contract/segment_research.py:492`, `segment_research_batch.py:191` | async, `to_thread` | **no stage**: `model_tier="haiku"` (`:483`, `:190`); logged as `a3_search_demand`, which is not in `llm_role_config` | legacy haiku, no route, no shadow | yes (no stage) |
| `acp_shared/content_embedding.py:122`, `places/llm.py:65` | sync / async | `f10_embed`, `a3_place_embed` → embed | `embed()` → Cohere acc2 | yes |
| 21 Jev sites (S7c), for example `ingestion/jev_gates.py:98`, `grounding.py:272`, `atom_ranking.py:253`, `judge_node.py:174` | async (`decide_sync` in graph nodes) | `a0_ingest`, `a1_seo`, `a3_*`, `s1_grounding`, `t7_debate`, `t9_facts`, `t10_gates`, … → validate (provider `typesafe`) | `decide()` → `_call_jev` | yes |
| `api/routers/admin_llm_ops.py:1087` | `check_jev_canary` (async) | none | **calls `_call_jev` directly and bypasses `decide()`**; writes no `llm_call_log` row (`:1076-1112`) | **no** |
| TP `backend/assembly/agent.py:88` | `_run` (sync generator) | `tp_compose` → writer | `llm_gateway.generate_text`; sync inside an async handler (`assembly/handler.py:385`) | yes |
| TP `backend/browse/search.py:133` | in `async search` | `tp_search_embed` → embed | `llm_gateway.embed_texts`; sync boto3 on the event loop | yes |

Some stages have a route but no code caller on `origin/main`: `s1_atom_writer`, `t10_claims`, `tp_extract` and `tp_component_embed`.

### 2.3 Gateway, bypasses, fallback

**Choke points.**

| Call type | Entry point |
|---|---|
| Text | `LLMClient.generate` (`client.py:122-131`) → `_generate` (`:133-162`) |
| Embeddings | `embed()` (`embed.py:122-155`) |
| Jev | `decide()` / `decide_sync()` (`decide.py:672-704`) |
| TripPlanner | `generate_text` / `embed_texts` (`llm_gateway.py:235-299`) |

**Logging is not at the choke points.**
- `record_call*` (`call_log.py:119`, `:158`, `:192`) is called by the callers after the call returns: 31 non-test lines across 21 files (Verify V10).
- Three writers sit inside `shared/llm_client/` and write their own row:
  - `decide()` (`decide.py:669`; `:665` only builds the kwargs)
  - the shadow daemon thread: `client.py:232` calls `record_shadow_sync`, which writes a second `llm_call_log` row through `shadow.py:51` `record_call(…, quality_signal={"shadow": True, "shadow_of": …})` under the **same stage**, with `job_id` / `tenant_id` re-bound at `client.py:220`
  - `column_mapper.py:116` (`_log_call` → `record_call_sync`, stage `a0_column_map`)
- Consequence: a span opened in `generate()` will not see `quality_signal` or the `role` that the caller attaches later, and shadow calls produce `llm_call_log` rows that share the primary call's stage and job_id.

**Guard test.** `tests/unit/test_aa685_no_raw_model_calls.py`:
- It scans `services/`, `api/` and `shared/` minus `shared/llm_client/` (lines 12-13, 50-55), and `ALLOWED` is empty (line 21).
- It flags the boto3 runtime methods (line 14), `*.completions.create` (lines 41-43), and `invoke_claude` / `get_satellite_client` (lines 17, 28-37).
- It does **not** catch:
  - httpx calls, so the Jev canary bypass passes
  - `responses.create`, `messages.create` and `embeddings.create`
  - anything under `scripts/` or `worker/` (V12 found 0 raw calls there today)
  - stage-less `LLMClient` calls

**Fallback is not "acc3 → acc1 → OpenAI" for every stage.** Code:

| Route type | Where | Order | Notes |
|---|---|---|---|
| Legacy keys `haiku` / `sonnet` (`catalog.py:26`); every writer stage | `_legacy_chain` (`client.py:238-329`) | acc2-native `_call_bedrock` (always fails: `ValidationException … not available for channel program accounts`) → `primary_acct` (`account_route`, default acc3, `:142-143`) → the other satellite | Sonnet drops to the Haiku chain. A T3 GPT-4.1 OpenAI step exists (`client.py:313-329`, `_call_openai(request, model="gpt-4.1")` at `:322`) but is disabled by the catalog gate (`openai_platform_allowed("gpt-4.1")` at `:317`; live row `gpt-4.1` `enabled=false`, `blocked_reason` "S235: retired…"). Re-enabling that row re-activates it. Profiles are hard-coded (`pricing.py:29-30`, `bedrock_satellite.py:135-143`), not taken from the catalog |
| Catalog keys (judges, GPT validators) | `_call_route` (`client.py:171-200`) | model → model | Each model picks one account (`catalog.py:64-72`). No acc3 → acc1 retry inside a model, and the Luna/Astra rows are acc3-only. OpenAI is reached only through `api_style=openai_chat` (`:478-479`), gated by `openai_platform_allowed` (`:41-49`, `:628`). `fallback_used=True` only when position > 0 (`:188-189`). Shadow runs in a daemon thread (`:202-236`) → `shared.llm_shadow_log` |
| Embeddings | `embed.py:132-155` | model → model | one account per model |
| TripPlanner | `llm_gateway.py:159-161` | model × account (`preferred, acc3, acc1, acc2`) | no shadow (`:147-150`) |

**Live routes** (`shared.llm_role_config`, all `is_active`):
- **Writers:** Claude on acc3. haiku for `s1_generate`, `s1_flag_fix`, `s1_itinerary_nudge`, `t2_flag_fix`, `t2_itinerary_nudge` and `a0_column_map`. sonnet for `t2_generate`, `t9_write`, `t8_angle_gen`, `tp_compose`, `s1_atom_writer` and `tp_extract`. `t9_repair` is haiku → sonnet.
- **Judges:** `s1_judge`, `t2_judge`, `t10_judge` and `t7_debate_judge` run gpt-5.6-luna → gpt-6-luna → gpt-6-luna-openai, with a gpt-6-luna shadow at 10%. `s1_/t2_brand_audit` run gpt-5.6-luna → gpt-6-luna.
- **Validators:**
  - `a3_atomize`, `s1_source_facts`: gpt-6-luna → haiku
  - `t10_claims`: gpt-6-luna → gpt-5.6-luna
  - `a3_place_card`: gpt-5.6-luna → sonnet
  - `a3_place_card_check`: haiku → sonnet
  - `a3_place_days`: sonnet, with a gpt-5.6-luna shadow at 20%
  - `a3_place_locate`: sonnet
- **Embed:** cohere-embed-v4.

**Live catalog.**
All 11 rows (`.tmp-session/s238/aa842_routes.json`, key `catalog`):
- gpt-5.6-luna, gpt-6-luna and gpt-6-astra are `provider=bedrock`, `api_style=converse`, acc3-only. **GPT judges run on Bedrock Converse, not on the OpenAI API.**
- **Claude on Converse:** `opus-5-5` (`global.anthropic.claude-opus-5-5`) and `sonnet-5` (`global.anthropic.claude-sonnet-5`) are enabled, `provider=bedrock`, `api_style=converse`, acc3-only. No live route uses them today (0 of 30 `llm_role_config` rows reference them), but any stage switched to them in admin Settings would call Claude through Converse.
- Legacy `haiku` and `sonnet` are `api_style=anthropic_native` with acc1/acc2/acc3 profiles.
- Only `gpt-6-luna-openai` (enabled) uses the OpenAI platform. `gpt-4.1` is disabled ("S235: retired…").
- The other two rows are `cohere-embed-v4` (`embed`, acc2) and `jev-latest` (`typesafe`, `decide`).

**Is the fallback reason logged?**

| Where | What is recorded |
|---|---|
| CIS database | Outcome only: `llm_call_log.account`, `fallback_used`, `provider`. There is no reason column, and a failed attempt gets no row |
| CIS, acc3 → acc1 failover | Recorded as `fallback_used=False` at `client.py:273` (T1.5b, sonnet tier) and at `:305` (T2.5b) when the tier is haiku; visible only as `account='acc1'`. For comparison, `:262` is the normal acc3 path (T1.5a), and `:294` / `:305` set `fallback_used = tier == "sonnet"`, which is True when a Sonnet stage drops to Haiku. 30-day rows: `s1_generate` acc1 n=3, `s1_flag_fix` n=1, `s1_itinerary_nudge` n=5 |
| CIS structlog (CloudWatch) | The reason exists only here: `t1_failed_trying_t2`, `t2_failed_trying_t2_5a`, `satellite_access_denied` / `satellite_invoke_failed` (`bedrock_satellite.py:351-357`, with `error_type`), `llm_route_attempt_failed` (`client.py:184`), `llm_openai_fallback_used` (`:195`, with an `errors` list). 7-day counts: `llm_route_attempt_failed`=32, `llm_openai_fallback_used`=0 (section 1). The CloudWatch metric is a TODO (`bedrock_satellite.py:55`, `:359`) |
| TripPlanner database | Each failed attempt gets its own row with `stop_reason='error'`, `quality_signal.error` and `failed=true` (`llm_gateway.py:196-199`, `:302-316`). 30-day `tp_*` error rows: 0 |

**30-day `llm_call_log` shape.**
- `provider=openai` judge rows exist only up to 2026-10-01: `s1_judge` 156+354, `t10_judge` 7+8, `s1_brand_audit` 9+19.
- `fallback_used=True`: `s1_flag_fix` 3, `t10_judge` 1, `a3_place_card_check` 1.
- The largest stage is Jev `s1_grounding`, n=75,644.

---

## 3. Current observability

### 3.1 Apps

| Item | State | Evidence |
|---|---|---|
| OpenTelemetry (Python code) | none | `rg -n --type py "opentelemetry\|\bOTEL_\|\botel\b"` over CIS + TP backend → 0 |
| OTel packages in the image | **present transitively, unpinned**: api / sdk / exporter-otlp-proto-grpc 1.45.1; instrumentation / -asgi / -fastapi 0.66b1; semantic-conventions 0.66b1 | ECS exec `importlib.metadata` probe. They come from `chromadb==0.4.24` (requirements:23, which needs otel api/sdk/otlp-grpc/instrumentation-fastapi) and from `fastapi` 0.143.2 (needs `opentelemetry-api>=1.44.0`) |
| X-Ray SDK | none | `rg -i "xray\|x-ray\|aws_xray\|X-Amzn-Trace\|_X_AMZN_TRACE_ID"` → 0 in both repos; `aws-xray-sdk` not installed |
| Sentry (CIS backend) | wired but **off live** | `api/core/sentry.py:19` (secret `aa-cis/dev/sentry-dsn-api`), `:50-63` init with `traces_sample_rate=0.1`; `api/main.py:67`, `:239`. `secretsmanager list-secrets` for `aa-cis/dev/sentry` → `[]`. `"Sentry DSN not found"` over 3 days → 76 events on api streams, 7 on worker streams |
| Langfuse | **dead** | `services/acp_shared/tracer.py:87-131` (`AcpTracer`, v2 API, langfuse 2.26.0 pinned at requirements:38); importers: only its own test; no `LANGFUSE_*` variables in the task definitions |
| structlog | used everywhere, **never configured** | No `structlog.configure`, `merge_contextvars` or `JSONRenderer`. Output is the default console renderer. The worker's `logger.bind(job_id=…)` (`worker.py:185`) is local, so `llm_route_used` lines carry no job_id |
| Correlation / trace propagation | none | Searching for `x-request-id`, `traceparent`, `x-amzn-trace-id` and correlation IDs finds 2 hits: the Sentry tag (`sentry_context.py:7`) and a comment (`graph.py:440`). `api/middleware/` holds only `rate_limit.py` and `sentry_context.py` |
| LLM observability today | **in the database, not in traces** | `shared.llm_call_log` (~252k rows), `shared.llm_shadow_log`, the Jev `decision_log`, and the Redis live-progress side channel `stream_sink` (ADR 0004) |
| TripPlanner backend | stdlib `logging` and `print` (`llm_gateway.py:318`); 0 ContextVars; no Sentry, OTel or X-Ray | `rg "ContextVar\|contextvars"` → 0; LLM rows go to `llm_call_log` with `APP="tripplanner"` (`:43`) |

### 3.2 Infra (`accounts/aa365`, the live root)

**`observability.tf`** has no tracing. It contains:
- an SNS alert topic (`:45`)
- RDS CPU and ECS task-count alarms (`:62`, `:88`)
- three ACP N7 alarms (`:139`, `:187`, `:208`)
- budgets (`:241`, `:291`)
- CloudTrail (`:340-433`)
- a `log_write_failed` metric filter and alarm for `llm_call_log`, `decision_log`, `llm_shadow_log` and `dfs_call_log` (locals `:465-472`, filter `:474`, alarm `:489`; on `8bd4659`: `:469-476`, `:478`, `:493`)

**`observability_ecosys.tf`** contains log retention for TripPlanner and API Gateway, plus 11 alarms (NAT, Booking, TripPlanner Lambda, RDS).

**`diagnostics.tf`** is temporary AA-272 work: VPC flow logs, an ALB access-log bucket, and the API Gateway CloudWatch role.

**`modules/monitoring`** holds one dashboard, `aa-cis-dev-pipeline`, with ECS, RDS and ALB widgets.

**X-Ray, ADOT and OTel in Terraform:** `rg -i "xray|x-ray|tracing_config|aws-otel|\badot\b|opentelemetry|\botel\b|otel-collector|AWSXRay"` over tf, json, yml and tfvars → **0**. No X-Ray IAM permission is granted in Terraform. Live IAM was not checked.

**Langfuse module:** `modules/langfuse/{main,outputs,variables}.tf` are 0-byte files. Other references are commented out ("AA-23: removed") or point to acc1 ARNs in the old `envs/dev` scaffold. Live acc2 has no `langfuse` secret (`list-secrets` → `[]`).

### 3.3 ECS and Lambda (live)

**ECS: no sidecar.**
- `aa-cis-dev-api:622`, `aa-cis-dev-worker:179` and `aa-booking-dev-api:17` each have **one container**. Re-checked on the current live revisions `aa-cis-dev-api:625` and `aa-cis-dev-worker:182`: still one container, and 0 `OTEL`/`LANGFUSE`/`SENTRY` names in `environment` or `secrets` with `awslogs` and no `OTEL_*`, `LANGFUSE_*` or `SENTRY_*` variables.
- Terraform agrees: every `container_definitions` list has a single element (`modules/ecs/main.tf:276`, `:465` in `ccd0f89`, `:293`, `:490` in `8bd4659`; `booking.tf:273`).

**Lambda: no layers.**
- `aa-tripplanner-dev-browse`, `aa-tripplanner-dev-assembly` and `aa-cis-dev-dfs-balance-check` all show `layers: null`, `tracing: PassThrough` and `LogFormat: Text`.
- Terraform has no `layers` or `tracing_config` (`rg` → 0).

**X-Ray account state.**
- `get-trace-segment-destination` → `XRay`/`ACTIVE`, which is the default. Transaction Search is not enabled, and the `aws/spans` log group does not exist.
- `get-trace-summaries` over 6 hours → 0.
- API Gateway `4ylo382khg/dev` has `tracingEnabled: false`.

### 3.4 Business context at call time (CIS)

| Context | Source | Reach from a span in `generate()` | Signature change |
|---|---|---|---|
| `stage` | `LLMRequest.stage` (`models.py:24`); set in 22 of 24 non-test `LLMRequest(` constructions (missing: `segment_research.py:481`, `segment_research_batch.py:189`) | direct | none |
| `job_id` | ContextVar `call_log.py:41`, `current_job_id()` `:44`. Bound at `worker.py:196`. The `call_log.py:37-41` comment says it is copied across `to_thread` and the LangGraph executor. The shadow thread re-binds it (`client.py:208-221`) | `current_job_id()` | none |
| `tenant_id` | ContextVar `call_log.py:64`, `resolve_tenant()` `:87-89`; the worker derives it from the payload (`worker.py:56-66`) | `resolve_tenant(None)` | none for jobs; **API-process calls have no binding** (the only bind sites are `worker.py:196` and `client.py:220`) |
| model / provider / account / fallback / tokens / cost / stop_reason | `LLMResponse` (`models.py:33-58`); chain position is known in `_call_route` | after the response returns | none |
| job kind / attempt | `Job.kind`, `.attempt` (`queue.py:27-37`); only on the worker's local logger | needs a ContextVar | small: `worker.py:196` and `call_log.py` |
| `tour_id` | **not in a ContextVar**: `s1_rewrite` `payload["tour_id"]` (`s1_rewrite_job.py:44-45`), `a3_atomize` (`a3_atomize_job.py:60-61`); `t2_rewrite` uses `published_tour_id` (`t2_rewrite_job.py:322-324`) | add `bind_tour()` at `worker.py:196`, same pattern as `job_tenant_id()` | small: worker and call_log only |
| `batch_id` | `TourRunRequest.batch_id` (`admin_pipeline.py:345`), in the S1 payload | same worker-bind approach | small |
| `wave` | **not available at call time**: `shared.rerun_wave` has no FK from jobs; the wave is derived afterwards (`services/waves/report.py:42-47`, `:97-103`); `wave_id` appears only in `admin_waves.py` and `waves/report.py` | join on job_id in the backend, or add `wave_id` to the enqueue payload | yes, if it is needed live |
| `conversation_id` candidate | `job_id`: one tour rewrite or one T9 piece per job, already propagated. Finer-grained: `piece_id` / `request_id` (payload keys, `t9_write_job.py:9` docstring and `:72`) | `current_job_id()` | none |

---

## 4. Options compared

Common pieces for every option:
- A small bootstrap module that registers a `TracerProvider` once per process (api, worker, each Lambda), using a pinned exporter.
- An env kill switch.
- Infra work to receive the spans (section 5). The infra work is not counted in the hours below.

### A. Anthropic SDK tracing only, plus manual spans for OpenAI

**What it means here.** Add `anthropic[bedrock]==1.14.0`. It brings `httpx2>=2,<3` and `opentelemetry-api>=1.1,<2` as hard dependencies and requires Python >= 3.10 (pyproject lines 12, 13, 22, 45). Then move these transports off boto3 onto `AnthropicBedrock`:
- `_call_bedrock`
- `invoke_claude` / `_invoke_streaming`
- TripPlanner `_text_call` (`anthropic_native`)

Cross-account satellite credentials (acc3/acc1 role assumption) must be passed into the SDK client. GPT on Bedrock Converse is **not covered**, because the SDK only speaks the Anthropic Messages API. A only covers the `anthropic_native` legacy keys (`haiku`, `sonnet`). Claude through the catalog Converse keys (`opus-5-5`, `sonnet-5`, section 2.3) would still need B or C spans. Converse, OpenAI, Cohere embeddings and Jev would all need manual spans.

**Files to change:**
- `shared/llm_client/client.py`, `bedrock_satellite.py`, `requirements.txt`
- TripPlanner `backend/shared/llm_gateway.py`, `backend/requirements.txt` (adding httpx2 and the SDK grows the Lambda zip)
- manual spans in `client.py` (`_call_bedrock_converse`, `_call_openai`), `embed.py`, `decide.py`
- tests for streaming parity with `stream_sink`

**Effort:** about 32–48 hours. **Rough engineering estimate, not verified** by a task breakdown. The transport rewrite (`client.py` 670 lines, `bedrock_satellite.py` 362, TP `llm_gateway.py` 365 on current `main`), streaming re-implementation, satellite credentials and regression tests on every writer stage take most of it.

**Risks:**
- The SDK OTel feature is 1 day old and in beta; the span schema can change.
- It rewrites the transport of every writer stage only to gain tracing.
- In content mode, non-streaming `messages.create` spans carry `gen_ai.output.messages` (v1.14.0 `lib/_tracing/_api_call.py:144-150`, `set_message_content`). Only streamed calls (`create(stream=True)`) need the `messages.stream()` helper to get output content. This matters because writer stages stream under `stream_sink.bind`.
- It still carries no job, stage or fallback context unless `conversation_id` and attributes are added by hand.
- Two semconv versions end up in one trace: Anthropic follows `e57c543b` (2026-09-24), while openai-v2 defaults to v1.30.0.
- After the upgrade, spans emit automatically whenever *any* global provider is registered.

**Fast kill switch:** `ANTHROPIC_OPEN_TELEMETRY=false` (verified at `_tracing.py:109` in v1.14.0), or `open_telemetry=False` on the client.

### B. One gen_ai wrapper span at the gateway for both vendors (recommended)

**What it means here.**

*Span structure.*
- One `CLIENT` span per logical call, named `chat {model}` / `embeddings {model}` per semconv `gen_ai-spans.md:54`.
- It is opened in `LLMClient.generate()` (`client.py:122`), next to the existing `stream_sink.emit_call_start/end`.
- One child span (or span event) per attempt, in `_call_route` (`:171-200`) and `_legacy_chain` (`:238-329`).

*Attributes on the logical span.*
- Standard gen_ai: `gen_ai.operation.name`, `gen_ai.provider.name` (`aws.bedrock` / `openai`), `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.input_tokens/output_tokens`.
- AA-specific: `aa.stage`, `aa.job_id`, `aa.tenant_id`, `aa.account`, `aa.route_position`, `aa.fallback_used`, `aa.cost_usd`, `aa.stop_reason`.

*Attributes on each attempt.*
- `error.type` plus the truncated error. This gives a structured fallback reason, which does not exist today.

*Other entry points.*
- The same wrapper goes in `embed()` (`embed.py:122`) and `decide()` (`decide.py:672`) for Jev.
- In TripPlanner it goes in `generate_text` / `embed_texts` (`llm_gateway.py:235`, `:267`).
- Content (prompts and outputs) is **off by default**. It is turned on only through an env flag and truncated below 200 KB (the X-Ray span limit).

**Files to change:**
- new `shared/observability/tracing.py` (bootstrap and kill switch)
- `shared/llm_client/client.py`, `embed.py`, `decide.py`
- optionally `call_log.py` and `worker.py:196` for kind and tour ContextVars
- `api/main.py` and the worker entrypoint (bootstrap)
- `requirements.txt` (explicit OTel pins)
- TripPlanner `backend/shared/llm_gateway.py`, `backend/requirements.txt`
- unit tests with `InMemorySpanExporter`

**Effort:** rough engineering estimate, **not verified**. Per-task breakdown (file sizes are `wc -l` on current `main`; 12 existing unit test files under `tests/unit/` match `llm|gateway|satellite|decide|embed|shadow`):

| Work | Files / functions | Hours |
|---|---|---|
| Bootstrap and kill switch | new `shared/observability/tracing.py`; `api/main.py`; worker entrypoint | 2–3 |
| Text gateway spans | `client.py` (670 lines): `generate` (`:122`), `_call_route` (`:171-200`), `_legacy_chain` (`:238-329`), `_start_shadow` / `_run_shadow` (`:202-236`) | 4–5 |
| Embed and Jev spans | `embed.py` (155): `embed()`; `decide.py` (704): `decide()` | 1–2 |
| Unit tests | `InMemorySpanExporter` tests for the above | 3–4 |
| TripPlanner | `backend/shared/llm_gateway.py` (365): `generate_text`, `embed_texts`; Lambda bootstrap | 3–4 |
| Optional tour/kind ContextVars | `call_log.py` (209), `worker.py:196` | 2 |
| **Total** | | **about 15–20** |

**Risks:**
- We own the attribute schema. Mitigation: follow semconv `gen_ai-spans.md` and pin `opentelemetry-semantic-conventions==0.66b1`.
- `brand_fit._judge` runs on the event loop (`debate.py:263`). The span itself is cheap, but a `BatchSpanProcessor` is required, never `SimpleSpanProcessor`, so export does not block.
- The shadow daemon thread (`client.py:202-236`) must get its own span linked to the parent, not a child that outlives it.
- `quality_signal` and `role` stay in `llm_call_log`, because they are attached after the call.

**Fast kill switch:** `OTEL_SDK_DISABLED=true` is general OTel spec, not verified against this SDK version here. Also add an explicit `AA_LLM_TRACING=off` flag checked by the bootstrap, so that no provider is registered and every span is a no-op. Removing the env vars disables tracing without a code change.

### C. Auto-instrument botocore / openai-v2 / httpx (contrib)

**What it means here.**
- `opentelemetry-instrumentation-botocore==0.66b1` (Beta) emits gen_ai spans for `Converse`, `ConverseStream`, `InvokeModel` and `InvokeModelWithResponseStream`. For `InvokeModel` / `InvokeModelWithResponseStream`, the PyPI description limits gen_ai tracing to Amazon Titan, Amazon Nova and Anthropic Claude.
- So C gives gen_ai spans for the **Converse, ConverseStream and Claude InvokeModel** calls of section 2.1, with no client code change. It does **not** cover:
  - Cohere Embed v4 through `InvokeModel` (CIS `embed.py:94`, TP `llm_gateway.py:280`): only a generic AWS SDK span
  - `create_model_invocation_job` (`bedrock_batch.py:171`): not a gen_ai operation
  - Jev (`httpx`, `decide.py:250`): only an HTTP span
- The code passes inference-profile IDs/ARNs as `modelId` (`bedrock_satellite.py:138-143`). Whether the instrumentor detects the Claude model family from those is **not verified**; check it in the spike.
- `opentelemetry-instrumentation-openai-v2==2.4b0` covers `chat.completions.create`. The wheel only declares `openai>=1.26.0` (extra `instruments`); the live image has openai 3.31.0, and `requirements.txt:6` is unpinned `>=1.16.2`. Compatibility with the openai 3.x client layout is **not verified**; check it in the spike.
- `opentelemetry-instrumentation-httpx==0.66b1` would give plain HTTP spans for Jev.

**Files to change:**
- `requirements.txt` (pins)
- bootstrap in `api/main.py` and the worker entrypoint (`BotocoreInstrumentor().instrument()`)
- for TripPlanner Lambdas, alternatively the ADOT layer plus `AWS_LAMBDA_EXEC_WRAPPER=/opt/otel-instrument`

**Effort:** about 4–6 hours of code, plus infra. Rough engineering estimate, **not verified**: pins in `requirements.txt`, one `instrument()` call per entrypoint, and a smoke test.

**Risks:**
- **No business context.** Spans have no stage, job, tenant or route position. "Which stage burned the fallback" stays unanswerable.
- The botocore instrumentor traces *all* boto3 calls (S3, Secrets Manager, Bedrock), which adds noise and cost. Per-service filtering is not verified.
- The semconv versions differ between packages.
- Every package is Beta.
- ADOT 0.21.0 pins `opentelemetry-sdk==1.44.0` and `opentelemetry-instrumentation-botocore==0.65b0`, so the C layer under ADOT is `0.65b0`, not `0.66b1` (section 1). It also conflicts with langfuse 5.x (`>=1.45.0`) if Langfuse v5 is ever chosen.

**Fast kill switch:** `OTEL_SDK_DISABLED=true`, or `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=botocore,openai`. On Lambda, remove the layer and `AWS_LAMBDA_EXEC_WRAPPER`.

### Verdict

| | A | B | C | B + C (botocore only) |
|---|---|---|---|---|
| Covers Claude on Bedrock | legacy `haiku`/`sonnet` only, after a rewrite; not Claude on Converse keys (`opus-5-5`, `sonnet-5`) | yes | yes (Converse + Claude InvokeModel; ARN detection not verified) | yes |
| Covers Cohere embeddings / Jev | manual | yes | plain AWS / HTTP spans only | yes |
| Covers GPT on Bedrock Converse | no | yes | yes | yes |
| Covers the OpenAI fallback | manual | yes | yes | yes |
| Business context (stage, job, tenant, fallback position) | manual | **yes** | no | **yes** |
| Structured fallback reason | partial (`resend_count` is SDK-level only) | **yes** | per wire call only | **yes** |
| Client code changes | large | small | none | small |
| Effort (code), rough estimate, not verified | 32–48 h | 15–20 h | 4–6 h | 17–23 h |

Start with **B**. Add the botocore layer from C only if the per-attempt wire spans justify the noise; decide that after the pilot. **A only becomes interesting** if a separate ADR moves Bedrock onto the Anthropic SDK for other reasons.

---

## 5. Backend options (trade-offs only; the choice belongs in an ADR)

**ADOT → X-Ray / CloudWatch (Transaction Search)**
- **Setup:** OTLP/HTTP to `https://xray.us-west-1.amazonaws.com/v1/traces` with SigV4. HTTP only, no gRPC.
  - Collector-less ADOT Python needs version >= 0.10.0 and `botocore`. The current `aws-opentelemetry-distro==0.21.0` pins `opentelemetry-api/sdk==1.44.0` and `opentelemetry-instrumentation-botocore==0.65b0` (PyPI), so this route uses the 1.44.0 pin set from section 1, not 1.45.1.
  - Plain `opentelemetry-exporter-otlp-proto-http` has no SigV4 auth; without the ADOT distro exporter, a collector is needed.
  - Alternatively, run an `ecs-cwagent` sidecar plus an ADOT auto-instrumentation init container, which changes the task definition.
  - Lambda needs the ADOT layer.
- **Prerequisite:** Transaction Search, which is **not enabled** on acc2 today. Spans land in the `aws/spans` log group.
- **IAM:** `AWSXrayWriteOnlyPolicy` or `CloudWatchAgentServerPolicy`.
- **Limits:**
  - single span 200 KB (rejected above that)
  - 5 MB per request
  - 16 KB per resource and scope
- **Pros:**
  - stays in acc2, no new vendor, and tenant content never leaves AWS (consistent with S235 "Bedrock-only")
  - IAM-auth, no secrets
  - joins the existing CloudWatch alarms
- **Cons:**
  - weak LLM-specific UI. The CloudWatch "GenAI observability / Model Invocation" dashboard works for Bedrock inference, but whether it shows spans from a non-AgentCore ECS app is **not verified**.
  - the default sampler is 100%, so `parentbased_traceidratio` must be set
  - keep `OTEL_AWS_APPLICATION_SIGNALS_ENABLED=false` to avoid double cost
  - cost from the us-east-1 example: $0.35/GB span ingest, 1% indexed included. us-west-1 rates are not verified.

**Langfuse (cloud or self-hosted)**
- **Setup:** OTLP/HTTP at `/api/public/otel/v1/traces` with Basic auth (pk:sk). No gRPC. Self-hosted needs v3.22.0 or later.
- **Pros:** an LLM-native UI (sessions, cost, prompts); `session.id` maps naturally to `job_id`.
- **Cons:**
  - Cloud sends tenant prompts and outputs outside AWS when content mode is on, which conflicts with the S235 rationale.
  - Self-hosting needs new infra; the old module is empty and the stack was removed in AA-23.
  - Its attribute mapping lists `gen_ai.prompt` / `gen_ai.completion`. Whether it maps the newer `gen_ai.input.messages` / `output.messages` is **not verified**.
  - Our pinned `langfuse==2.26.0` is not OTel-based. Langfuse 5.0.1 needs `opentelemetry-sdk>=1.45.0` and Python >= 3.11, so it cannot share an environment with ADOT 0.21.0 (`sdk==1.44.0`).

**Grafana Cloud (Tempo)**
- **Setup:** OTLP gateway (`otlp-gateway-prod-<region>.grafana.net/otlp`) with Basic auth in `OTEL_EXPORTER_OTLP_HEADERS`. In Python, the header must be written `Basic%20…`.
- **Pros:** a general trace UI with TraceQL; listed as an Anthropic OTel partner.
- **Cons:**
  - a new vendor and secret
  - data leaves AWS
  - free-tier trace limits are not stated on the page read
  - no LLM-specific views
- **Not proposed:** Anthropic server-side destination (`/opentelemetry/api`). It supports only the Claude API and Claude Platform on AWS, **not Bedrock**.

**Independent of the backend:**
- Keep the exporter behind an env switch.
- Keep `llm_call_log` as the cost and audit source of truth. Traces are for latency, fallback and debugging, not billing.

---

## 6. Pilot plan

**Scope check.**
- "S1 rewrite" is a **job kind**, `s1_rewrite`, not an `llm_role_config` stage. Evidence:
  - `services/jobs/s1_rewrite_job.py:32` (`KIND = "s1_rewrite"`)
  - `:35` (`concurrency=6`)
  - enqueued at `api/routers/admin_pipeline.py:1183`
- Its LLM stages are real and routed:
  - `s1_generate` (writer, haiku, acc3, legacy chain, streaming under `stream_sink.bind` at `:75`)
  - `s1_source_facts` (gpt-6-luna → haiku)
  - `s1_flag_fix` and `s1_itinerary_nudge` (haiku)
  - `s1_judge` (gpt-5.6-luna → gpt-6-luna → gpt-6-luna-openai)
  - `s1_brand_audit`
  - Jev `s1_grounding`
- One pilot therefore exercises both vendors' Bedrock paths, the legacy acc2 → acc3 chain, the catalog route, streaming and Jev.
- "metadata_only in prod" means **Dev** in practice: acc2 has no prod stack yet. The content mode default stays `metadata_only` anyway.

**Steps (each needs Nghiệp's approval and a separate issue or PR; none was done here):**
1. ADR: the backend choice (section 5) and the attribute schema for B (gen_ai plus `aa.*`).
2. Build B in CIS behind `AA_LLM_TRACING`, default **off**. Pin the OTel packages. Use `BatchSpanProcessor`, a ratio sampler (1.0 for the pilot worker only), and no content capture.
3. Prepare infra in AA-CIS-Infra through PR and apply, per the chosen backend. For X-Ray that means enabling Transaction Search and IAM write on the worker task role. No sidecar is needed for collector-less OTLP.
4. Turn the flag on for the **worker only** (`aa-cis-dev-worker`). Run **one small wave** of 3 tours, following the `aa-wave-rerun` pilot convention, of `s1_rewrite` in one country. Paid run: at most 3 tours, as the memory rule requires.
5. Content mode: enable it only for one debugging job, with `max_content_bytes` below 200 KB, and turn it off afterwards.

**Success criteria:**
- Every `llm_call_log` row of the pilot jobs (`job_id IN pilot`) has exactly one matching logical span with the same `stage`, `model`, `account` and token counts. Reconcile by job_id. Shadow rows (`quality_signal->>'shadow' = 'true'`, written by `shadow.py:51` under the same stage and job_id; `s1_judge` / `s1_brand_audit` shadow at 10%) must match a shadow span, or be excluded from the count.
- The legacy acc2 failed attempt shows as an attempt with `error.type`, and the acc3 success as the final attempt.
- Fallback reasons are queryable without CloudWatch log text.
- Worker job p95 duration does not regress more than 2% against the previous `s1_rewrite` jobs (`shared.job` timings).
- No span is rejected for size, and no exporter errors appear in `/ecs/aa-cis-dev`.
- No prompt or output text appears in spans while content mode is off.

**Rollback:**
- Set `AA_LLM_TRACING=off` (or `OTEL_SDK_DISABLED=true`) on the worker task, then redeploy.
- The code path is a no-op without a provider.
- Revert the infra PR if needed.

---

## 7. Open questions

1. **Spike (needs Nghiệp's approval):** one paid Bedrock call with `ConsoleSpanExporter`, to look at a real span. Because no code uses the Anthropic SDK, there are two variants:
   - (a) an `AnthropicBedrock` + `anthropic==1.14.0` scratch venv, which produces an `anthropic.messages.create` span
   - (b) `BotocoreInstrumentor` on the existing `invoke_model` path, which shows what C/B+C would produce

   **Not run.** Approve (a), (b), or both?
2. Backend: X-Ray/Transaction Search (stays in AWS) or Langfuse (LLM UI, data leaves AWS or needs self-hosting)? Decide in an ADR.
3. Should B also fix the "acc3 → acc1 recorded as `fallback_used=False`" semantics (`client.py:273` for sonnet tier, `:305` when tier=haiku), or only expose it as `aa.account` / `aa.route_position`?
4. Should the guaranteed-failing acc2-native first attempt for legacy writers (about 2,382 wasted acc2 attempts in 7 days: 1,428 `t2_failed_trying_t2_5a` + 954 `t1_failed_trying_t2`) be removed? That is a separate issue; it is not tracing work.
5. Should `wave_id` be put into the job payload at enqueue, so spans carry it live? Today it is derivable only afterwards (`waves/report.py:42-47`).
6. Should the guard test (`test_aa685_no_raw_model_calls.py`) be extended to catch httpx LLM calls (the Jev canary bypass at `admin_llm_ops.py:1087`) and stage-less `LLMRequest`s, so every call is guaranteed a span?
7. Should the API process (no ContextVar binding for job or tenant) be traced at all, or only the worker and Lambdas?
8. Should OTel be pinned explicitly even before any tracing work? Today it floats transitively through chromadb and fastapi, and a fastapi bump can change it.
9. Should the TripPlanner assembly sync-in-async call (`handler.py:385`) be fixed before tracing? Otherwise spans will show event-loop blocking as LLM latency.

---

## Appendix: Verify

All searches ran with ripgrep 14.1.1 in the `origin/main` snapshots, with `!tests/**` excluded unless stated.

### Call-site searches (CIS)
| # | Command | Hits |
|---|---|---|
| V1 | `rg -n --type py -e '^\s*(import\|from)\s+(anthropic\|openai\|typesafe\|jev)\b' -e 'AnthropicBedrock\|AsyncAnthropic\|OpenAI\(\|AsyncOpenAI' AA-CIS-App` | **2** (`client.py:10`, `client.py:118`) |
| V2 | `rg -n --type py -e '\.(invoke_model\|invoke_model_with_response_stream\|converse\|converse_stream)\(' -e 'chat\.completions\.create\|responses\.create\|messages\.create\|messages\.stream\|embeddings\.create' -e "client\(\s*['\"]bedrock-runtime" AA-CIS-App` | **10** (9 real; `acp_shared/tracer.py:100` is a docstring) |
| V3 | `rg -n --type py -e '\.generate\(' . \| rg -v shared/llm_client/client.py` | **24** (17 real calls) |
| V4 | `rg -n --type py 'LLMClient\(\)' .` | **24** |
| V5 | `rg -n --type py -e '\.generate\b[^(]' -e 'llm(_client)?\.generate' .` (generate passed as a callable to `to_thread`) | 6 real |
| V6 | `rg -n --type py -g '!shared/llm_client/**' -e 'invoke_claude\(\|get_satellite_client\(\|bedrock_batch\|create_model_invocation_job' .` | **14** (0 direct `invoke_claude` / `get_satellite_client`) |
| V7 | `rg -n --type py -e 'llm_client\.decide import\|llm_client import decide' .` | **19** importers |
| V8 | `rg -n --type py -g '!shared/llm_client/decide.py' -e 'await decide\(\|decide_sync\(\|decide_mod\.(decide\|_call_jev)\(\|_call_jev\(' .` | **22** (21 Jev) |
| V9 | `rg -n --type py -e 'llm_client\.embed import\|\bembed\(\s*["a-z_]' .` | **2** importers |
| V10 | `rg -n --type py -g '!shared/llm_client/call_log.py' -g '!tests/**' -e 'record_call(_sync\|_with_pool)?\(' .` | **31** lines in 21 files. Without the test exclusion: 48. The variant `rg -n "record_call(_sync\|_with_pool)?\(" --type py -g '!tests/**' . \| grep -v "def record_call"` gives 38, which adds 7 lines inside `call_log.py`. One of the 31 is `shared/dfs_client/call_log.py`, a different (DataForSEO) logger |
| V11 | `rg -n --type py -e 'to_thread\(\|run_in_executor\(' . \| rg -i 'graph\|generate\|judge\|llm\|embed\|card\|...'` | **31** |
| V12 | the V2 patterns plus `invoke_claude\|LLMClient\(\)\|api\.typesafe\|bedrock-runtime` over `scripts worker docker infrastructure *.py` | **0** |
| — | `git -C apps/AA-CIS-App grep -n -E "^\s*(import anthropic\|from anthropic)" origin/main -- '*.py' \| wc -l` | **0** |

### Call-site searches (TripPlanner backend)
| # | Command | Hits |
|---|---|---|
| TP1 | `rg -n --type py -e '^\s*(import\|from)\s+(anthropic\|openai)\b' -e 'AnthropicBedrock\|OpenAI\(' -e '\.(invoke_model\|…\|converse_stream)\(' -e 'completions\.create\|responses\.create\|messages\.create\|embeddings\.create' -e bedrock-runtime -e typesafe .` | **5** (3 real calls) |
| TP2 | `rg -n --type py -e 'generate_text\(\|embed_texts\(\|load_route\(\|llm_gateway\.record\(\|…' .` | **9** |
| — | `git -C apps/AA-TripPlanner-Web grep -n -E "^\s*(import anthropic\|from anthropic)" origin/main -- '*.py' \| wc -l` | **0** |

### Observability searches
| Command | Result |
|---|---|
| `rg -n --type py "^\s*(import\|from)\s+(anthropic\|openai\|langfuse\|sentry_sdk\|structlog\|opentelemetry\|aws_xray_sdk)" AA-CIS-App AA-TripPlanner-Web/backend` | 148, all structlog except openai ×1, sentry_sdk ×4, langfuse ×1 |
| `rg -n --type py "opentelemetry\|\bOTEL_\|\botel\b" AA-CIS-App AA-TripPlanner-Web/backend` | 0 |
| `rg -n -i -g '!*.md' -g '!tests/**' "xray\|x-ray\|aws_xray\|X-Amzn-Trace\|_X_AMZN_TRACE_ID"` | 0 per repo |
| Infra: `rg -n -i "xray\|x-ray\|tracing_config\|aws-otel\|\badot\b\|opentelemetry\|\botel\b\|otel-collector\|AWSXRay" -g '*.tf' -g '*.json' -g '*.yml' -g '*.yaml' -g '*.tfvars' -g '!dist/**' .` | 0 |
| `aws logs start-query --log-group-name /ecs/aa-cis-dev` (7 days, 1791470155–1792074955): `filter @message like /t2_failed_trying_t2_5a\|t2_5a_satellite_used\|t1_failed_trying_t2\|t1_5a_satellite_used\|llm_route_attempt_failed\|llm_openai_fallback_used/ \| parse @message /(?<ev>…)/ \| stats count(*) as n by ev` | `t2_failed_trying_t2_5a` 1428, `t2_5a_satellite_used` 1427, `t1_failed_trying_t2` 954, `t1_5a_satellite_used` 954, `llm_route_attempt_failed` 32, `llm_openai_fallback_used` absent (0). Split by stream prefix: `.tmp-session/s238/aa842_cw_counts_by_stream.json` |
| `aws xray get-trace-summaries` (6 hours) | 0 traces |
| `aws xray get-trace-segment-destination` | `XRay` / `ACTIVE` |
| `aws secretsmanager list-secrets --filters Key=name,Values=aa-cis/dev/sentry` | `[]` |
| `aws secretsmanager list-secrets` filtered on `langfuse` | `[]` |
| `aws lambda get-function-configuration` (browse, assembly) | `layers: null`, `tracing: PassThrough` |

### Dependency pin lines

**AA-CIS-App `requirements.txt`** (origin/main `d224c4d3`; no lock file; `Dockerfile:2` `FROM python:3.12-slim`, `:16-17` `pip install -r requirements.txt`):
```
2:boto3==1.43.49
3:botocore==1.43.49
6:openai>=1.16.2          (installed live: 3.31.0)
10:langgraph==1.1.8
23:chromadb==0.4.24        (pulls opentelemetry-api/sdk/otlp-grpc/instrumentation-fastapi)
26:fastapi>=0.110.1        (installed 0.143.2; requires opentelemetry-api>=1.44.0)
28:httpx>=0.27.0           (installed 0.28.1)
37:sentry-sdk[fastapi]>=1.40.0   (installed 2.72.0)
38:langfuse==2.26.0
43:structlog==24.1.0
anthropic: absent (not installed)
opentelemetry-*: absent from requirements; installed transitively: api/sdk/exporter-otlp-proto-grpc 1.45.1, instrumentation(-asgi,-fastapi) 0.66b1, semantic-conventions 0.66b1
```
`tests/integration/requirements-integration.txt:11-12`: `boto3==1.35.99` / `botocore==1.35.99`. This affects tests only.

**AA-TripPlanner-Web `backend/requirements.txt`** (origin/main `082380a`; the Lambda zip is built from the runtime block, `package_lambdas.sh:36-44`):
```
2  asyncpg==0.30.0
3  pydantic==2.9.2
4  boto3==1.35.36
5  pgvector==0.3.6
6  httpx==0.27.2
anthropic / openai / opentelemetry-*: absent
```

**anthropic v1.14.0 `pyproject.toml`** (first release with OTel; `gh release view v1.14.0 -R anthropics/anthropic-sdk-python`):
```
12: "httpx2>=2.0.0, <3"
13: "opentelemetry-api>=1.1.0, <2"
22: requires-python = ">= 3.10"
45: bedrock = ["boto3 >=1.28.57, <2", "botocore >=1.31.57, <2"]
```

### Spike
**Not run.** No `ConsoleSpanExporter` output is available. The spike needs Nghiệp's approval (open question 1).
