# AA-Ecosys DB Schema Reference (live dump)

**Verified:** 2026-10-03 (S209) — live `information_schema` dump of the shared RDS (`aa-cis/dev/rds`, acc2 `005097885195`, us-west-1). Latest migration: **203**.

> This file is generated from a real DB dump, not hand-maintained. It is the **single source of truth** for table/column names across both CIS and TripPlanner (same RDS, separate schemas). Kiro and Claude Code should read THIS before introspecting columns. Regenerate after any migration: re-run the dump script (`.tmp-session/s209_schema_dump.py` pattern) and `s209_gen_schema_md.py`.

**Totals:** 12 non-empty schemas, 100 tables/views, 95 FKs, 13 enums. Empty schemas (exist, 0 objects): acp_gold_output, acp_silver_s3, acp_silver_s4.

## Conventions
- Column format: `name type` — `NN` suffix = NOT NULL. `_enum` / udt types shown by their udt name. `rows` = approximate (`pg_class.reltuples`), not exact.
- `raw_tours` PK is `tour_id` (NOT `id`). `quality_scores` has `evaluated_at` (NOT `created_at`). `published_tours`/`seo_context` have NO `country` — always JOIN `raw_tours`.

## Schema ownership
- `silver_aa_internal`, `gold_aa_internal` — CIS S1 pipeline (raw → generated → published).
- `acp_shared`, `acp_contract`, `acp_deliver` — ACPv2 T-series + atom pipeline. `acp_contract.tour_atoms` + view `v_active_tour_atoms` (mig 203, gates on `published_tours.master_status`).
- `shared` — cross-cutting: tenants, plans, jobs (`job`, `pipeline_jobs`, `pipeline_runs`), LLM gateway (`llm_call_log`, `llm_shadow_log`, `llm_role_config`, `llm_model_catalog`), `destinations` (TripPlanner golden record, CIS-write-only per ADR 0002).
- `tripplanner` — TripPlanner-owned (itinerary_components, customers, sessions, trip_events, trip_drafts, ...).

## `acp_contract` (18 objects)

### `acp_contract.atom_decompose_jobs` (table, ~0 rows)
```
job_id text NN
tour_ids jsonb NN
status text NN
input_s3_uri text NN
output_s3_uri text
submitted_at timestamp with time zone NN
completed_at timestamp with time zone
error_message text
atoms_created integer
job_arn text
succeeded_count integer
failed_count integer
```

### `acp_contract.atom_embedding` (table, ~510 rows)
```
atom_id text NN
view text NN
embedding vector NN
created_at timestamp with time zone NN
```

### `acp_contract.atom_matches` (table, ~827 rows)
```
id bigint NN
query text NN
kind text NN
atom_id text NN
distance double precision NN
matched_by text NN
matched_at timestamp with time zone NN
```

### `acp_contract.atom_ranking` (table, ~10860 rows)
```
tour_id uuid NN
segment_id text NN
demand_rank integer
recurrence_rank integer
questions_rank integer
said_rank integer
total_rank integer
demand_market text
demand_volume integer
recurrence integer NN
questions integer NN
said integer NN
excluded_reason text
computed_at timestamp with time zone NN
market text NN
```

### `acp_contract.atom_segment` (table, ~1625 rows)
```
segment_id text NN
canonical_place text NN
canonical_action text NN
created_at timestamp with time zone NN
questions_count integer
questions_computed_at timestamp with time zone
contested real
contested_computed_at timestamp with time zone
```

### `acp_contract.atom_segment_alias` (table, ~51 rows)
```
segment_id_old text NN
segment_id_canonical text NN
merged_at timestamp with time zone NN
```

### `acp_contract.atom_segment_member` (table, ~2108 rows)
```
segment_id text NN
atom_id text NN
is_alias boolean NN
```

### `acp_contract.atomize_day_fingerprint` (table, ~568 rows)
```
tenant_tour_version_id uuid NN
day_number integer NN
fingerprint_hash text NN
atomized_at timestamp with time zone NN
```

### `acp_contract.hub` (table, ~23 rows)
```
hub_id uuid NN
hub_name text NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `acp_contract.question_embedding` (table, ~847 rows)
```
question_hash text NN
question_text text NN
embedding vector NN
created_at timestamp with time zone NN
```

### `acp_contract.route` (table, ~167 rows)
```
route_id text NN
tour_id uuid NN
hub_id uuid
hub_name text NN
ordered_segment_ids jsonb NN
first_day smallint NN
last_day smallint NN
created_at timestamp with time zone NN
version integer NN
superseded_at timestamp with time zone
```

### `acp_contract.route_pick` (table)
```
route_pick_id uuid NN
tenant_id uuid NN
hub_name text NN
route_snapshot jsonb NN
selected_at timestamp with time zone NN
selected_by text
```

### `acp_contract.s1_from_atom_runs` (table)
```
id uuid NN
tour_id uuid NN
prompt_version text NN
model_tier text NN
model_used text
status text NN
retries smallint
atoms_available integer
atoms_used_count integer
citation_count integer
word_count integer
words_per_citation numeric
density_pass boolean
closed_world_pass boolean
input_tokens integer
output_tokens integer
error_message text
created_at timestamp with time zone NN
```

### `acp_contract.search_demand` (table, ~4470 rows)
```
keyword text NN
market text NN
search_volume integer
people_also_ask jsonb NN
retrieved_on timestamp with time zone NN
serp_domains jsonb
```

### `acp_contract.segment_research_log` (table, ~1068 rows)
```
canonical_place text NN
market text NN
researched_at timestamp with time zone NN
```

### `acp_contract.tour_atoms` (table, ~2165 rows)
```
atom_id text NN
tour_id uuid NN
owner_scope text NN
text text NN
activity_type text
emotional_hook text
visual_potential smallint NN
persona_fit jsonb NN
season_note text
distinctiveness text NN
media jsonb NN
starred boolean NN
deleted boolean NN
usage_log jsonb NN
cooldown_until jsonb NN
human_seam_notes jsonb NN
weight numeric NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
source_hash text
is_empty_marker boolean NN
itinerary_day smallint
place text
action text
evidence text
```

### `acp_contract.v_active_tour_atoms` (VIEW)
```
atom_id text
tour_id uuid
owner_scope text
text text
activity_type text
emotional_hook text
visual_potential smallint
persona_fit jsonb
season_note text
distinctiveness text
media jsonb
starred boolean
deleted boolean
usage_log jsonb
cooldown_until jsonb
human_seam_notes jsonb
weight numeric
created_at timestamp with time zone
updated_at timestamp with time zone
source_hash text
is_empty_marker boolean
itinerary_day smallint
place text
action text
evidence text
```

### `acp_contract.v_trip_registry` (VIEW)
```
id uuid
sku text
name character varying
aa_name character varying
duration_raw text
period text
price_raw text
destination text
itinerary_source text
itinerary_brand text
aa_summary text
aa_highlights jsonb
seo_title character varying
seo_meta character varying
seo_keywords_used jsonb
quality_score numeric
content_embedding vector
trip_url text
url_alive boolean
inclusions text
exclusions text
tenant_id uuid
lifecycle_stage tour_lifecycle_stage_enum
```

## `acp_deliver` (1 objects)

### `acp_deliver.tenant_tour_pages` (table, ~0 rows)
```
tenant_id text NN
tour_id uuid NN
url text NN
published_at timestamp with time zone
url_alive boolean
last_checked_at timestamp with time zone
```

## `acp_shared` (17 objects)

### `acp_shared.acp_output_rules` (table)
```
rule_id uuid NN
tenant_id character varying
stage smallint
rule_type character varying NN
pattern character varying NN
action_value text
error_message character varying
source_type character varying NN
source_hitl_id uuid
run_count integer
is_active boolean
created_at timestamp with time zone
confidence_score numeric
```

### `acp_shared.acp_quota_ledger` (table)
```
ledger_id uuid NN
tenant_id uuid NN
s2_runs_limit integer NN
s3_runs_limit integer NN
s4_blogs_limit integer NN
s2_runs_used integer NN
s3_runs_used integer NN
s4_blogs_used integer NN
reset_at timestamp with time zone NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `acp_shared.angle_gate_option` (table, ~0 rows)
```
option_id uuid NN
request_id uuid NN
idx smallint NN
name text NN
why_it_works text NN
formula_fit text NN
best_final_style text NN
recommended boolean NN
chosen boolean NN
answers jsonb
violations jsonb
```

### `acp_shared.angle_gate_request` (table, ~0 rows)
```
request_id uuid NN
tenant_id uuid NN
atom_id text NN
trip_id uuid
channel text
goal text
status text NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
cta text
dfs_paa_snapshot jsonb
subject_id uuid
route_segment_ids jsonb
```

### `acp_shared.audit_log` (table, ~0 rows)
```
id uuid NN
tenant_id character varying
actor character varying
action character varying
resource_type character varying
resource_id text
details jsonb
created_at timestamp with time zone
actor_type audit_actor_type
```

### `acp_shared.competitor_index_cache` (table)
```
tenant_id uuid NN
country character varying NN
phrases jsonb NN
competitors jsonb NN
fetched_at timestamp with time zone NN
```

### `acp_shared.content_piece` (table, ~1 rows)
```
piece_id uuid NN
tenant_id uuid NN
angle_gate_request_id uuid NN
attempt_number smallint NN
content_text text NN
status text NN
held_reason text
gate_ledger jsonb NN
repair_log jsonb NN
created_at timestamp with time zone NN
angle_gate_option_id uuid
channel text
content_summary text
content_embedding vector
seo_title text
meta_description text
slug text
route_hub_name text
route_segment_count smallint
flags jsonb
discarded_attempts jsonb NN
job_id uuid
```

### `acp_shared.debate_brand_fit_cache` (table)
```
id uuid NN
tenant_id uuid NN
segment_id text
route_id text
brand_version integer NN
judge_score real NN
brand_fit_score real NN
cross_brand_distinct real NN
mission_present boolean NN
feedback text
computed_at timestamp with time zone NN
```

### `acp_shared.facts` (table)
```
fact_id text NN
scope text NN
tenant_id uuid
title text NN
body text NN
stated_on date
provenance text NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `acp_shared.marketplace_portfolios` (table)
```
portfolio_id uuid NN
tour_ids _uuid NN
filters_used jsonb
atom_snapshot jsonb
status text NN
created_at timestamp with time zone NN
finalized_at timestamp with time zone
```

### `acp_shared.publish_log` (table)
```
publish_id uuid NN
piece_id uuid NN
tenant_id uuid NN
channel text NN
status text NN
external_id text
external_url text
published_at timestamp with time zone
unpublished_at timestamp with time zone
unpublished_by text
last_error text
created_at timestamp with time zone NN
```

### `acp_shared.quarter_plan` (table, ~6 rows)
```
plan_id uuid NN
tenant_id uuid NN
year integer NN
quarter smallint NN
current_version_id uuid
created_at timestamp with time zone NN
year_plan_id uuid
```

### `acp_shared.quarter_plan_version` (table, ~0 rows)
```
version_id uuid NN
plan_id uuid NN
version_no integer NN
payload jsonb NN
source character varying NN
approval_status character varying NN
approved_by character varying
approved_at timestamp with time zone
created_at timestamp with time zone NN
```

### `acp_shared.subject` (table, ~0 rows)
```
subject_id uuid NN
tenant_id uuid NN
segment_id text
route_id text
channel text NN
state text NN
cleared_bar_reason jsonb NN
score numeric
created_at timestamp with time zone NN
```

### `acp_shared.tenant_atom_state` (table, ~0 rows)
```
tenant_id uuid NN
tour_id uuid NN
assigned_angle text
starred boolean NN
cooldown_until timestamp with time zone
usage_log jsonb NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `acp_shared.tenant_config` (table)
```
tenant_id uuid NN
markets _text NN
channels _text NN
updated_at timestamp with time zone NN
```

### `acp_shared.year_plan` (table)
```
year_plan_id uuid NN
tenant_id uuid NN
year integer NN
created_at timestamp with time zone NN
```

## `acp_silver_s2` (1 objects)

### `acp_silver_s2.competitor_inputs` (table)
```
id uuid NN
tenant_id uuid NN
country character varying NN
url text NN
label character varying
is_active boolean NN
added_by uuid
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

## `gold_aa_internal` (4 objects)

### `gold_aa_internal.content_exports` (table)
```
id uuid NN
tenant_id uuid NN
export_id uuid NN
format export_format_enum NN
filter_params jsonb
field_mapping jsonb
s3_path character varying
signed_url text
total_tours integer
file_size_kb integer
status character varying NN
expires_at timestamp with time zone
created_at timestamp with time zone NN
completed_at timestamp with time zone
```

### `gold_aa_internal.published_tours` (table, ~42 rows)
```
id uuid NN
tour_id uuid NN
generated_content_id uuid NN
tenant_id uuid NN
aa_name character varying NN
aa_subtitle character varying
aa_summary text
aa_description text
aa_highlights jsonb
aa_itineraries text
mobile_card_text character varying
seo_title character varying
seo_meta character varying
seo_keywords_used jsonb
og_tags jsonb
quality_score numeric
quality_score_id uuid
s3_gold_path character varying
approved_by character varying
published_at timestamp with time zone NN
content_embedding vector
master_status master_status_enum NN
deleted_at timestamp with time zone
deleted_by text
```

### `gold_aa_internal.tenant_tour_versions` (table, ~3 rows)
```
id uuid NN
tenant_id uuid NN
published_tour_id uuid NN
version_number integer NN
parent_version_id uuid
rewritten_content jsonb NN
status text NN
quality_score numeric
edit_source text NN
rewrite_language text NN
seo_mode text NN
edited_at timestamp with time zone
edited_by_user text
created_at timestamp with time zone NN
qa_status text NN
qa_repair_count smallint NN
qa_checked_at timestamp with time zone
qa_auto_passed boolean NN
job_id uuid
```

### `gold_aa_internal.webhook_deliveries` (table)
```
id uuid NN
tenant_id uuid NN
tour_id uuid NN
webhook_url character varying NN
event_type character varying NN
delivery_id uuid NN
payload_s3_path character varying
hmac_secret_ref character varying
status webhook_status_enum NN
http_status smallint
attempt_count smallint NN
last_error text
created_at timestamp with time zone NN
next_retry_at timestamp with time zone
delivered_at timestamp with time zone
```

## `public` (1 objects)

### `public.checkpoint_migrations` (table)
```
v integer NN
```

## `shared` (39 objects)

### `shared.acp_runs` (table)
```
id uuid NN
batch_id uuid NN
country text
tenant_id uuid NN
manifest_s3_key text
tour_count integer NN
quality_score_avg numeric
status text NN
created_at timestamp with time zone NN
completed_at timestamp with time zone
```

### `shared.admin_users` (table)
```
id uuid NN
username character varying NN
password_hash character varying NN
role admin_role NN
is_active boolean NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `shared.cost_explorer_snapshot` (table, ~2066 rows)
```
id uuid NN
account_id text NN
service text NN
period_start date NN
period_end date NN
amount_usd numeric NN
unit text NN
raw jsonb
fetched_at timestamp with time zone NN
```

### `shared.decision_log` (table, ~163427 rows)
```
id bigint NN
created_at timestamp with time zone NN
stage text NN
question_key text NN
subject_key text NN
tenant_id uuid
job_id uuid
mode text NN
zone text NN
probability numeric
choice text
probabilities jsonb
threshold_version integer
model text
latency_ms integer
cost_usd numeric
error text
outcome text
question_hash text
cached boolean NN
```

### `shared.decision_question` (table, ~5 rows)
```
question_key text NN
stage text NN
kind text NN
instructions text NN
criteria jsonb
mode text NN
accept_floor numeric
reject_ceiling numeric
threshold_version integer NN
calibration_ref text
notes text
updated_at timestamp with time zone NN
updated_by text NN
question_hash text
```

### `shared.destinations` (table, ~1178 rows)
```
id uuid NN
name text NN
country text NN
lat double precision NN
lng double precision NN
cover_image_url text
created_at timestamp with time zone NN
located_by text
located_at timestamp with time zone
```

### `shared.dfs_balance_snapshot` (table)
```
id uuid NN
balance_usd numeric NN
currency text
below_threshold boolean NN
threshold_usd numeric
raw jsonb
fetched_at timestamp with time zone NN
```

### `shared.dfs_call_log` (table, ~1537 rows)
```
id uuid NN
tenant_id uuid
tour_id uuid
endpoint text NN
keyword text
location_code integer
cost_usd numeric
cache_hit boolean NN
fetched_live boolean NN
keyword_count integer
meta jsonb
created_at timestamp with time zone NN
```

### `shared.jev_tenant_allowlist` (table)
```
tenant_id uuid NN
reason text NN
added_at timestamp with time zone NN
added_by text NN
```

### `shared.job` (table, ~126 rows)
```
id uuid NN
kind text NN
payload jsonb NN
status text NN
attempt integer NN
max_attempts integer NN
run_after timestamp with time zone NN
locked_by text
locked_until timestamp with time zone
cancel_requested boolean NN
idempotency_key text
progress jsonb NN
result jsonb
cost_usd numeric NN
error text
parent_job_id uuid
created_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
started_at timestamp with time zone
finished_at timestamp with time zone
```

### `shared.job_worker` (table, ~71 rows)
```
worker_id text NN
host text NN
started_at timestamp with time zone NN
last_seen_at timestamp with time zone NN
stopped_at timestamp with time zone
max_parallel integer NN
caps jsonb NN
running_jobs integer NN
reaped_requeued integer NN
reaped_failed integer NN
last_reap_at timestamp with time zone
last_reaped jsonb
task_revision integer
```

### `shared.llm_call_log` (table, ~48880 rows)
```
id uuid NN
tenant_id uuid
stage text NN
role text NN
model text NN
tokens_in integer
tokens_out integer
cost_usd numeric
quality_signal jsonb NN
content_piece_id uuid
angle_gate_request_id uuid
created_at timestamp with time zone NN
stop_reason text
account text
fallback_used boolean
provider text
job_id uuid
```

### `shared.llm_model_catalog` (table)
```
model_key text NN
label text NN
vendor text NN
provider text NN
api_style text NN
bedrock_profile_ids jsonb NN
wire_model text
callable_via _text NN
supports_temperature boolean NN
max_output_tokens integer
price_in_per_mtok numeric
price_out_per_mtok numeric
price_cache_read_per_mtok numeric
price_cache_write_per_mtok numeric
price_source text
enabled boolean NN
blocked_reason text
notes text
updated_at timestamp with time zone NN
updated_by text NN
```

### `shared.llm_role_config` (table)
```
stage text NN
role text NN
provider text NN
model_id text NN
account_route text
is_active boolean NN
updated_at timestamp with time zone NN
updated_by text NN
fallback_model_ids _text NN
shadow_model_id text
shadow_sample_pct integer NN
```

### `shared.llm_shadow_log` (table, ~348 rows)
```
id bigint NN
created_at timestamp with time zone NN
stage text NN
primary_model text NN
shadow_model text NN
primary_output text
shadow_output text
shadow_error text
primary_cost_usd numeric
shadow_cost_usd numeric
shadow_latency_ms integer
request_sha256 text
```

### `shared.membership_plans` (table)
```
id uuid NN
plan_name text NN
tours_quota_monthly integer NN
api_calls_quota_monthly integer NN
price_usd_monthly numeric NN
overage_rate_usd_per_tour numeric NN
overage_rate_usd_per_1k_calls numeric NN
is_active boolean NN
created_at timestamp with time zone NN
```

### `shared.notifications` (table, ~0 rows)
```
id bigint NN
tenant_id uuid NN
actor_type character varying NN
event_type character varying NN
entity_type character varying
entity_id character varying
payload jsonb NN
target_roles _text NN
is_read boolean NN
dispatched_at timestamp with time zone NN
created_at timestamp with time zone NN
```

### `shared.pipeline_jobs` (table, ~260 rows)
```
id uuid NN
job_type text NN
status text NN
request jsonb NN
tenant text
result_version_id uuid
pipeline_run_id uuid
error text
heartbeat_at timestamp with time zone
created_at timestamp with time zone NN
started_at timestamp with time zone
finished_at timestamp with time zone
current_stage text
```

### `shared.pipeline_lessons` (table)
```
id integer NN
batch character varying
country character varying
stage character varying NN
field character varying
pattern text NN
why_it_matters text
what_to_do text NN
example_before text
example_after text
is_active boolean
version integer
created_at timestamp with time zone
```

### `shared.pipeline_runs` (table, ~46 rows)
```
id uuid NN
tenant_id uuid NN
batch_id uuid NN
batch_name character varying
s3_source_path character varying
status character varying NN
tours_total integer NN
tours_passed integer NN
tours_hitl integer NN
tours_failed integer NN
cost_usd numeric
tokens_input bigint
tokens_output bigint
tokens_cached bigint
langfuse_trace_url character varying
started_at timestamp with time zone NN
completed_at timestamp with time zone
error_message text
llm_provider text
llm_model text
step_name text
ingest_details jsonb
```

### `shared.place_photo` (table, ~3232 rows)
```
id uuid NN
drive_file_id text NN
drive_root_id text NN
folder_path text NN
country text NN
tour_folder text
file_name text NN
place_label text
tour_id uuid
destination_id uuid
match_source text NN
status text NN
s3_key_large text
s3_key_small text
width integer
height integer
bytes bigint
sha256 text
credit text
drive_modified_at timestamp with time zone
error text
synced_at timestamp with time zone
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
s3_key_original text
```

### `shared.prompt_eval_runs` (table)
```
id uuid NN
pipeline text NN
prompt_version text NN
tour_count integer NN
avg_quality_score numeric
avg_words_per_citation numeric
gate_pass_count integer
gate_fail_count integer
cost_usd numeric
regression_detected boolean NN
baseline_prompt_version text
baseline_avg_quality_score numeric
details jsonb
triggered_by text NN
created_at timestamp with time zone NN
```

### `shared.schema_versions` (table, ~160 rows)
```
version character varying NN
description text
applied_at timestamp with time zone NN
```

### `shared.spend_budget` (table)
```
provider text NN
scope text NN
per_run_usd numeric
per_day_usd numeric
hard_stop boolean NN
alert_pct integer NN
updated_at timestamp with time zone NN
updated_by text
```

### `shared.tenant_api_usage` (table, ~19299 rows)
```
id uuid NN
tenant_id uuid
endpoint character varying NN
method character varying NN
status_code integer NN
response_ms integer
called_at timestamp with time zone
actor_type character varying NN
admin_user_id uuid
```

### `shared.tenant_brand_rule_versions` (table)
```
version_id uuid NN
tenant_id uuid NN
snapshot jsonb NN
source_docx_s3_key text
source_type text NN
created_by character varying
created_at timestamp with time zone NN
```

### `shared.tenant_brand_rules` (table, ~1 rows)
```
id uuid NN
tenant_id uuid NN
system_prompt text
style_guide text
forbidden_words jsonb
custom_validators jsonb
version integer NN
is_active boolean NN
updated_at timestamp with time zone NN
created_at timestamp with time zone
brand_type text
core_idea text
customer_segment text
customer_mindset text
voice_examples jsonb
source_docx_s3_key text
rewrite_language text
target_markets _text
brand_name text NN
good_examples text
```

### `shared.tenant_brand_rules_deleted_aa404` (table)
```
id uuid NN
tenant_id uuid NN
system_prompt text
style_guide text
forbidden_words jsonb
custom_validators jsonb
version integer NN
is_active boolean NN
updated_at timestamp with time zone NN
created_at timestamp with time zone
brand_type text
core_idea text
customer_segment text
customer_mindset text
voice_examples jsonb
source_docx_s3_key text
rewrite_language text
target_markets _text
brand_name text NN
good_examples text
deleted_at timestamp with time zone NN
```

### `shared.tenant_export_config` (table)
```
id uuid NN
tenant_id uuid NN
webhook_url character varying
export_format export_format_enum NN
field_mapping jsonb
auth_header character varying
is_active boolean NN
created_at timestamp with time zone NN
```

### `shared.tenant_integrations` (table)
```
id uuid NN
tenant_id uuid NN
integration_type text NN
config jsonb NN
secret_key text
connected_at timestamp with time zone
last_verified_at timestamp with time zone
last_verify_error text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `shared.tenant_rewrite_usage` (table)
```
tenant_id uuid NN
year_month text NN
rewrite_count integer NN
updated_at timestamp with time zone NN
```

### `shared.tenant_seo_config` (table)
```
id uuid NN
tenant_id uuid NN
seo_provider seo_provider_enum NN
custom_keywords jsonb
target_market jsonb
overrides jsonb
updated_at timestamp with time zone NN
```

### `shared.tenants` (table, ~4 rows)
```
tenant_id uuid NN
name character varying NN
slug character varying NN
plan_tier plan_tier_enum NN
api_key_hash character varying
rate_limit_rpm integer NN
is_active boolean NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
plan_id uuid
last_brand_brief_s3_key text
cancelled_at timestamp with time zone
cancellation_reason text
country text
is_canary boolean
skip_hitl boolean
posts_per_week integer NN
```

### `shared.unmapped_market_requests` (table)
```
id uuid NN
tenant_id uuid NN
country_code text NN
requested_at timestamp with time zone NN
first_seen_at timestamp with time zone NN
resolved_at timestamp with time zone
```

### `shared.v_batch_stats` (VIEW)
```
batch_id uuid
total bigint
passed bigint
hitl bigint
failed bigint
```

### `shared.v_destination_photos` (VIEW)
```
destination_id uuid
photo_id uuid
path text
place_label text
tour_id uuid
width integer
height integer
match_source text
updated_at timestamp with time zone
position bigint
```

### `shared.v_pipeline_summary` (VIEW)
```
tour_id uuid
tenant_id uuid
batch_id uuid
src_name character varying
country text
pipeline_status pipeline_status_enum
ingest_at timestamp with time zone
latest_content_id uuid
content_version smallint
content_status content_status_enum
score_overall numeric
failure_codes jsonb
published_at timestamp with time zone
```

### `shared.v_tenant_monthly_usage` (VIEW)
```
tenant_id uuid
tenant_name character varying
plan_tier plan_tier_enum
slug character varying
tours_quota_monthly integer
api_calls_quota_monthly integer
price_usd_monthly numeric
overage_rate_usd_per_tour numeric
billing_month timestamp with time zone
tours_rewritten bigint
api_calls_used numeric
quota_tours_pct numeric
quota_calls_pct numeric
tours_overage bigint
overage_usd numeric
llm_cost_usd numeric
```

### `shared.v_tour_photos` (VIEW)
```
tour_id uuid
photo_id uuid
path text
place_label text
destination_id uuid
width integer
height integer
match_source text
updated_at timestamp with time zone
position bigint
```

## `silver_aa_internal` (7 objects)

### `silver_aa_internal.generated_content` (table, ~110 rows)
```
id uuid NN
tour_id uuid NN
tenant_id uuid NN
version_num smallint NN
aa_name character varying
aa_subtitle character varying
aa_summary text
aa_description text
aa_highlights jsonb
aa_itineraries text
mobile_card_text character varying
seo_title character varying
seo_meta character varying
seo_keywords_used jsonb
og_tags jsonb
model_editorial character varying
model_schema character varying
prompt_version character varying
brand_rules_version integer
status content_status_enum NN
retry_count smallint NN
created_at timestamp with time zone NN
metadata jsonb NN
fix_pass_applied boolean
fix_pass_fields jsonb
requested_tier text
fallback_used boolean NN
human_edited boolean NN
reviewed_by_legacy character varying
edited_at timestamp with time zone
edit_diff jsonb NN
revalidate_passed boolean
reviewed_by uuid
satellite_used boolean NN
satellite_account text
```

### `silver_aa_internal.quality_scores` (table, ~109 rows)
```
id uuid NN
generated_content_id uuid NN
tour_id uuid NN
tenant_id uuid NN
score_overall numeric NN
score_brand numeric
score_seo numeric
score_structure numeric
score_quality numeric
failure_codes jsonb
issues jsonb
passed_count smallint NN
failed_count smallint NN
validator_fn_version character varying
langfuse_trace_id character varying
evaluated_at timestamp with time zone NN
brand_audit_status text
brand_audit_codes jsonb
brand_audit_issues jsonb
brand_audit_fields jsonb
lessons_extracted jsonb
```

### `silver_aa_internal.raw_sources` (table, ~34 rows)
```
id uuid NN
tenant_id uuid NN
batch_id uuid NN
filename character varying NN
s3_path character varying NN
file_size_kb integer
row_count integer
parsed_at timestamp with time zone NN
parse_errors jsonb
file_hash character varying
```

### `silver_aa_internal.raw_tours` (table, ~987 rows)
```
tour_id uuid NN
tenant_id uuid NN
batch_id uuid NN
source_id uuid
tour_id_external text
sku text
provider character varying
src_name character varying NN
src_subtitle character varying
src_summary text
src_description text
src_highlights jsonb
src_itineraries text
country text
duration text
group_size text
period text
price_raw text
inclusions text
exclusions text
links jsonb
activities jsonb
feature text
best_time_to_go character varying
pipeline_status pipeline_status_enum NN
ingest_at timestamp with time zone NN
review_status character varying NN
reviewed_by uuid
reviewed_at timestamp with time zone
review_notes text
source_group_id uuid
source_version smallint NN
source_status source_status_enum NN
deleted_at timestamp with time zone
deleted_by text
lifecycle_stage tour_lifecycle_stage_enum NN
country_raw_unresolved text
```

### `silver_aa_internal.review_queue` (table, ~0 rows)
```
id uuid NN
tour_id uuid NN
generated_content_id uuid
tenant_id uuid NN
failure_summary text
score_overall numeric
step_fn_task_token text
step_fn_execution_arn character varying
review_status review_status_enum NN
reviewer_notes text
reviewed_by character varying
reviewed_at timestamp with time zone
created_at timestamp with time zone NN
tenant_tour_version_id uuid
escalate_detail jsonb
```

### `silver_aa_internal.seo_context` (table, ~78 rows)
```
id uuid NN
tour_id uuid NN
tenant_id uuid NN
keyword_search character varying
provider seo_provider_enum NN
keyword_ideas jsonb
demographics jsonb
trends jsonb
top_keywords jsonb
cache_key character varying
fetched_at timestamp with time zone NN
expires_at timestamp with time zone
people_also_ask jsonb
related_keywords jsonb
```

### `silver_aa_internal.upload_staging` (table)
```
id uuid NN
batch_id uuid NN
tenant_id uuid NN
parsed_payload jsonb NN
matched_tour_id uuid
matched_source_group_id uuid
decision staging_decision_enum NN
decided_by text
decided_at timestamp with time zone
created_at timestamp with time zone NN
```

## `tripplanner` (12 objects)

### `tripplanner.customers` (table)
```
id uuid NN
name text NN
phone text
email text
created_at timestamp with time zone NN
```

### `tripplanner.itinerary_components` (table, ~3972 rows)
```
id uuid NN
source_tour_id text NN
source_day_index integer NN
destination_id uuid NN
name text NN
activity text NN
intensity_level text NN
season_months _int4 NN
duration_hint text NN
text_extract text NN
embedding vector
created_at timestamp with time zone NN
```

### `tripplanner.sessions` (table)
```
id uuid NN
guest_token text NN
customer_id uuid
created_at timestamp with time zone NN
expires_at timestamp with time zone
```

### `tripplanner.tour_day` (table, ~650 rows)
```
source_tour_id text NN
day_index integer NN
title text NN
start_place text
end_place text
overnight_place text
overnight_destination_id uuid
places _text NN
extracted_by text NN
source_hash text NN
extracted_at timestamp with time zone NN
```

### `tripplanner.tour_graph_build` (table)
```
id uuid NN
built_at timestamp with time zone NN
params jsonb NN
stats jsonb NN
```

### `tripplanner.tour_graph_edge` (table, ~379 rows)
```
from_destination_id uuid NN
to_destination_id uuid NN
tour_count integer NN
tour_ids _text NN
km double precision NN
```

### `tripplanner.tour_graph_node` (table, ~299 rows)
```
destination_id uuid NN
name text NN
country text NN
lat double precision NN
lng double precision NN
tour_ids _text NN
stop_count integer NN
activities _text NN
intensity_min text
intensity_max text
season_months _int4 NN
```

### `tripplanner.tour_junction` (table, ~3496 rows)
```
destination_a uuid NN
destination_b uuid NN
km double precision NN
cross_border boolean NN
```

### `tripplanner.tour_leg` (table, ~3871 rows)
```
source_tour_id text NN
day_from integer NN
day_to integer NN
days integer NN
start_destination_id uuid NN
end_destination_id uuid NN
destination_ids _uuid NN
countries _text NN
activities _text NN
```

### `tripplanner.tour_stop` (table, ~622 rows)
```
source_tour_id text NN
day_index integer NN
destination_id uuid NN
country text NN
source text NN
```

### `tripplanner.trip_drafts` (table, ~21 rows)
```
id uuid NN
session_id uuid NN
status text NN
itinerary jsonb NN
date_start date
date_end date
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `tripplanner.trip_events` (table, ~51 rows)
```
id bigint NN
trip_id uuid NN
session_id uuid NN
event_type text NN
payload jsonb NN
created_at timestamp with time zone NN
```

## Enums

- `acp_shared.audit_actor_type`: hitl_reviewer,tenant_admin,tenant_reviewer
- `gold_aa_internal.master_status_enum`: active,inactive,trashed
- `public.content_status_enum`: draft,passed,hitl,approved,rejected,published
- `public.export_format_enum`: json,csv,xml
- `public.pipeline_status_enum`: ingested,seo_pending,seo_done,gen_pending,gen_done,validating,hitl_required,hitl_approved,hitl_rejected,published,failed
- `public.plan_tier_enum`: internal,starter,growth,business,enterprise
- `public.review_status_enum`: pending,approved,rejected,skipped,superseded,dismissed
- `public.seo_provider_enum`: dataforseo,custom,disabled
- `public.webhook_status_enum`: pending,delivered,failed,retrying
- `shared.admin_role`: admin,reviewer
- `silver_aa_internal.source_status_enum`: active,superseded,trashed
- `silver_aa_internal.staging_decision_enum`: pending,bypass,replace,update,keep_both
- `silver_aa_internal.tour_lifecycle_stage_enum`: active,phasing_out,retired

## Foreign keys

Format: `child.col` → `parent.col`
```
acp_contract.atom_embedding.atom_id -> acp_contract.tour_atoms.atom_id
acp_contract.atom_matches.atom_id -> acp_contract.tour_atoms.atom_id
acp_contract.atom_ranking.segment_id -> acp_contract.atom_segment.segment_id
acp_contract.atom_ranking.tour_id -> silver_aa_internal.raw_tours.tour_id
acp_contract.atom_segment_alias.segment_id_canonical -> acp_contract.atom_segment.segment_id
acp_contract.atom_segment_alias.segment_id_old -> acp_contract.atom_segment.segment_id
acp_contract.atom_segment_member.atom_id -> acp_contract.tour_atoms.atom_id
acp_contract.atom_segment_member.segment_id -> acp_contract.atom_segment.segment_id
acp_contract.route.hub_id -> acp_contract.hub.hub_id
acp_contract.route.tour_id -> silver_aa_internal.raw_tours.tour_id
acp_contract.route_pick.tenant_id -> shared.tenants.tenant_id
acp_contract.s1_from_atom_runs.tour_id -> silver_aa_internal.raw_tours.tour_id
acp_contract.tour_atoms.tour_id -> silver_aa_internal.raw_tours.tour_id
acp_shared.acp_quota_ledger.tenant_id -> shared.tenants.tenant_id
acp_shared.angle_gate_option.request_id -> acp_shared.angle_gate_request.request_id
acp_shared.angle_gate_request.subject_id -> acp_shared.subject.subject_id
acp_shared.angle_gate_request.tenant_id -> shared.tenants.tenant_id
acp_shared.competitor_index_cache.tenant_id -> shared.tenants.tenant_id
acp_shared.content_piece.angle_gate_option_id -> acp_shared.angle_gate_option.option_id
acp_shared.content_piece.angle_gate_request_id -> acp_shared.angle_gate_request.request_id
acp_shared.content_piece.job_id -> shared.job.id
acp_shared.content_piece.tenant_id -> shared.tenants.tenant_id
acp_shared.debate_brand_fit_cache.tenant_id -> shared.tenants.tenant_id
acp_shared.facts.tenant_id -> shared.tenants.tenant_id
acp_shared.publish_log.piece_id -> acp_shared.content_piece.piece_id
acp_shared.publish_log.tenant_id -> shared.tenants.tenant_id
acp_shared.quarter_plan.current_version_id -> acp_shared.quarter_plan_version.version_id
acp_shared.quarter_plan.year_plan_id -> acp_shared.year_plan.year_plan_id
acp_shared.quarter_plan_version.plan_id -> acp_shared.quarter_plan.plan_id
acp_shared.subject.route_id -> acp_contract.route.route_id
acp_shared.subject.segment_id -> acp_contract.atom_segment.segment_id
acp_shared.subject.tenant_id -> shared.tenants.tenant_id
acp_shared.tenant_atom_state.tenant_id -> shared.tenants.tenant_id
acp_shared.tenant_atom_state.tour_id -> silver_aa_internal.raw_tours.tour_id
acp_shared.tenant_config.tenant_id -> shared.tenants.tenant_id
acp_shared.year_plan.tenant_id -> shared.tenants.tenant_id
acp_silver_s2.competitor_inputs.tenant_id -> shared.tenants.tenant_id
gold_aa_internal.content_exports.tenant_id -> shared.tenants.tenant_id
gold_aa_internal.published_tours.generated_content_id -> silver_aa_internal.generated_content.id
gold_aa_internal.published_tours.tenant_id -> shared.tenants.tenant_id
gold_aa_internal.published_tours.tour_id -> silver_aa_internal.raw_tours.tour_id
gold_aa_internal.tenant_tour_versions.job_id -> shared.job.id
gold_aa_internal.tenant_tour_versions.parent_version_id -> gold_aa_internal.tenant_tour_versions.id
gold_aa_internal.tenant_tour_versions.published_tour_id -> gold_aa_internal.published_tours.id
gold_aa_internal.tenant_tour_versions.tenant_id -> shared.tenants.tenant_id
gold_aa_internal.webhook_deliveries.tenant_id -> shared.tenants.tenant_id
gold_aa_internal.webhook_deliveries.tour_id -> silver_aa_internal.raw_tours.tour_id
shared.acp_runs.batch_id -> shared.pipeline_runs.batch_id
shared.jev_tenant_allowlist.tenant_id -> shared.tenants.tenant_id
shared.job.parent_job_id -> shared.job.id
shared.llm_call_log.tenant_id -> shared.tenants.tenant_id
shared.pipeline_runs.tenant_id -> shared.tenants.tenant_id
shared.place_photo.destination_id -> shared.destinations.id
shared.place_photo.tour_id -> silver_aa_internal.raw_tours.tour_id
shared.tenant_api_usage.admin_user_id -> shared.admin_users.id
shared.tenant_api_usage.tenant_id -> shared.tenants.tenant_id
shared.tenant_brand_rule_versions.tenant_id -> shared.tenants.tenant_id
shared.tenant_brand_rules.tenant_id -> shared.tenants.tenant_id
shared.tenant_export_config.tenant_id -> shared.tenants.tenant_id
shared.tenant_integrations.tenant_id -> shared.tenants.tenant_id
shared.tenant_rewrite_usage.tenant_id -> shared.tenants.tenant_id
shared.tenant_seo_config.tenant_id -> shared.tenants.tenant_id
shared.tenants.plan_id -> shared.membership_plans.id
silver_aa_internal.generated_content.reviewed_by -> shared.admin_users.id
silver_aa_internal.generated_content.tenant_id -> shared.tenants.tenant_id
silver_aa_internal.generated_content.tour_id -> silver_aa_internal.raw_tours.tour_id
silver_aa_internal.quality_scores.generated_content_id -> silver_aa_internal.generated_content.id
silver_aa_internal.quality_scores.tenant_id -> shared.tenants.tenant_id
silver_aa_internal.quality_scores.tour_id -> silver_aa_internal.raw_tours.tour_id
silver_aa_internal.raw_sources.batch_id -> shared.pipeline_runs.batch_id
silver_aa_internal.raw_sources.tenant_id -> shared.tenants.tenant_id
silver_aa_internal.raw_tours.batch_id -> shared.pipeline_runs.batch_id
silver_aa_internal.raw_tours.reviewed_by -> shared.admin_users.id
silver_aa_internal.raw_tours.source_id -> silver_aa_internal.raw_sources.id
silver_aa_internal.raw_tours.tenant_id -> shared.tenants.tenant_id
silver_aa_internal.review_queue.generated_content_id -> silver_aa_internal.generated_content.id
silver_aa_internal.review_queue.tenant_id -> shared.tenants.tenant_id
silver_aa_internal.review_queue.tenant_tour_version_id -> gold_aa_internal.tenant_tour_versions.id
silver_aa_internal.review_queue.tour_id -> silver_aa_internal.raw_tours.tour_id
silver_aa_internal.seo_context.tenant_id -> shared.tenants.tenant_id
silver_aa_internal.seo_context.tour_id -> silver_aa_internal.raw_tours.tour_id
silver_aa_internal.upload_staging.matched_tour_id -> silver_aa_internal.raw_tours.tour_id
tripplanner.itinerary_components.destination_id -> shared.destinations.id
tripplanner.sessions.customer_id -> tripplanner.customers.id
tripplanner.tour_day.overnight_destination_id -> shared.destinations.id
tripplanner.tour_graph_edge.from_destination_id -> shared.destinations.id
tripplanner.tour_graph_edge.to_destination_id -> shared.destinations.id
tripplanner.tour_graph_node.destination_id -> shared.destinations.id
tripplanner.tour_junction.destination_a -> shared.destinations.id
tripplanner.tour_junction.destination_b -> shared.destinations.id
tripplanner.tour_leg.end_destination_id -> shared.destinations.id
tripplanner.tour_leg.start_destination_id -> shared.destinations.id
tripplanner.tour_stop.destination_id -> shared.destinations.id
tripplanner.trip_drafts.session_id -> tripplanner.sessions.id
tripplanner.trip_events.session_id -> tripplanner.sessions.id
```

## Latest migrations

| version | applied_at | description |
|---|---|---|
| 203 | 2026-10-02 10:44:03.636578+00:00 | AA-713: v_active_tour_atoms — atom reads follow published_tours.master_status |
| 202 | 2026-10-01 09:37:08.637520+00:00 | AA-708: shared.place_photo.s3_key_original (keep the original file) |
| 201 | 2026-10-01 06:55:35.081142+00:00 | ADR 0002: tripplanner role read-only on shared.destinations; SELECT on photo views |
| 200 | 2026-10-01 06:47:17.204480+00:00 | AA-708: shared.v_tour_photos / v_destination_photos (photo read contract) |
| 199 | 2026-10-01 06:30:45.363534+00:00 | AA-711: shared.job_worker.task_revision (old task stops claiming after a deploy) |
| 198 | 2026-10-01 05:36:34.725949+00:00 | AA-708: shared.place_photo (Drive photo sync, tour/destination matching) |
| 197 | 2026-10-01 04:33:42.739593+00:00 | AA-653: chk_raw_tours_country adds Pakistan and Philippines (20 values) |
| 196 | 2026-10-01 02:19:36.662918+00:00 | AA-706: a1_keyword_about_tour Jev question (shadow) |
| 195 | 2026-10-01 00:12:53.351452+00:00 | AA-702: v_trip_registry excludes superseded sources (active only) |
| 194 | 2026-09-30 11:00:52.390383+00:00 | AA-701: T10 gate Jev questions (shadow, observe only) |
| 193 | 2026-09-30 10:56:26.303479+00:00 | AA-700: T-series Jev questions t7_topic_fits_brand, t8_angle_answers, t9_fact_relevant (shadow) |
| 192 | 2026-09-30 10:19:35.059279+00:00 | AA-695: Segment same-place Jev question a3_same_place (shadow) |
| 191 | 2026-09-30 10:10:55.212093+00:00 | AA-692: A1 judge tie-break Jev question a1_brand_fit (shadow) |
| 190 | 2026-09-30 07:41:26.382204+00:00 | AA-694: reword a3_activity_type to the transit rule's meaning (logistics vs experience) |
| 189 | 2026-09-30 07:12:26.252416+00:00 | AA-694: A3 segment activity-type Jev question (shadow) |
