# AA-Ecosys DB Schema Reference (live dump)

**Verified:** 2026-10-15 (S237) — live `information_schema` dump of the shared RDS (`aa-cis/dev/rds`, acc2 `005097885195`, us-west-1). Latest migration applied: **bk-010** (latest CIS numeric: 233; TripPlanner: tp-010; Booking: bk-010).

> This file is generated from a real DB dump, not hand-maintained. It is the **single source of truth** for table/column names across both CIS and TripPlanner (same RDS, separate schemas). Kiro and Claude Code should read THIS before introspecting columns. Regenerate after any migration: re-run the dump script (`.tmp-session/s209_schema_dump.py` pattern, S3-mediated ECS exec) and `s209_gen_schema_md.py`.

**Totals:** 15 non-empty schemas, 172 tables/views, 175 FKs, 13 enums. Empty schemas (exist, 0 objects): acp_gold_output, acp_silver_s3, acp_silver_s4.

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

### `acp_contract.atom_embedding` (table, ~6744 rows)
```
atom_id text NN
view text NN
embedding vector NN
created_at timestamp with time zone NN
```

### `acp_contract.atom_matches` (table, ~9526 rows)
```
id bigint NN
query text NN
kind text NN
atom_id text NN
distance double precision NN
matched_by text NN
matched_at timestamp with time zone NN
```

### `acp_contract.atom_ranking` (table, ~108198 rows)
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
version integer NN
superseded_at timestamp with time zone
```

### `acp_contract.atom_segment` (table, ~11306 rows)
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

### `acp_contract.atom_segment_alias` (table, ~149 rows)
```
segment_id_old text NN
segment_id_canonical text NN
merged_at timestamp with time zone NN
```

### `acp_contract.atom_segment_member` (table, ~25072 rows)
```
segment_id text NN
atom_id text NN
is_alias boolean NN
```

### `acp_contract.atomize_day_fingerprint` (table, ~10062 rows)
```
tenant_tour_version_id uuid NN
day_number integer NN
fingerprint_hash text NN
atomized_at timestamp with time zone NN
```

### `acp_contract.hub` (table, ~59 rows)
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

### `acp_contract.route` (table, ~8058 rows)
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

### `acp_contract.search_demand` (table, ~5089 rows)
```
keyword text NN
market text NN
search_volume integer
people_also_ask jsonb NN
retrieved_on timestamp with time zone NN
serp_domains jsonb
```

### `acp_contract.segment_research_log` (table, ~1337 rows)
```
canonical_place text NN
market text NN
researched_at timestamp with time zone NN
```

### `acp_contract.tour_atoms` (table, ~32019 rows)
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

## `acp_shared` (21 objects)

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

### `acp_shared.angle_gate_option` (table, ~33 rows)
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

### `acp_shared.angle_gate_request` (table, ~15 rows)
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

### `acp_shared.atom_place_card` (table, ~291 rows)
```
atom_id text NN
card_id uuid
resolved_at timestamp with time zone NN
miss_reason text
```

### `acp_shared.audit_log` (table, ~930 rows)
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

### `acp_shared.content_piece` (table, ~188 rows)
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
writer_input jsonb
```

### `acp_shared.content_piece_label` (table)
```
piece_id uuid NN
labelled_by text NN
label text NN
defects jsonb NN
minutes_to_fix smallint
reason text
content_sha256 text
labelled_at timestamp with time zone NN
```

### `acp_shared.debate_brand_fit_cache` (table, ~237 rows)
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
country text
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

### `acp_shared.place_card` (table, ~111 rows)
```
card_id uuid NN
place_key text NN
display_name text NN
locality text
region text
country text NN
naming_note text
facts jsonb NN
status text NN
cost_usd numeric NN
verified_by text
verified_at timestamp with time zone
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
destination_id uuid
```

### `acp_shared.place_card_alias` (table, ~361 rows)
```
alias_norm text NN
country_norm text NN
card_id uuid NN
source text NN
created_at timestamp with time zone NN
```

### `acp_shared.place_card_miss` (table)
```
place_norm text NN
country_norm text NN
reason text NN
attempts integer NN
rule_version integer NN
prompt_sha text NN
model text
last_tried_at timestamp with time zone NN
retry_after timestamp with time zone NN
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
idempotency_key text
requested_at timestamp with time zone
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

### `acp_shared.subject` (table, ~105 rows)
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

## `booking` (34 objects)

### `booking.audit_logs` (table, ~2 rows)
```
id uuid NN
actor_type text NN
actor_id uuid
action text NN
entity_type text NN
entity_id uuid
before jsonb
after jsonb
created_at timestamp with time zone NN
actor_ref text
entity_label text
summary text
```

### `booking.countries` (table)
```
iso2 character NN
name text NN
active boolean NN
```

### `booking.customer_otps` (table)
```
id uuid NN
customer_id uuid NN
otp_hash text NN
channel text NN
expires_at timestamp with time zone NN
used_at timestamp with time zone
attempts smallint NN
created_at timestamp with time zone NN
```

### `booking.customer_sessions` (table)
```
id uuid NN
customer_id uuid NN
refresh_token_hash text NN
expires_at timestamp with time zone NN
revoked_at timestamp with time zone
created_at timestamp with time zone NN
```

### `booking.customers` (table, ~1 rows)
```
id uuid NN
name text
email text
phone text
address text
gender text
marital_status text
profession text
profile_media_id uuid
is_blocked boolean NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
verified boolean NN
source text NN
needs_merge_review boolean NN
merge_candidate_id uuid
external_ref text
contact_consent boolean NN
contact_consent_at timestamp with time zone
code text NN
```

### `booking.fx_rates` (table)
```
id uuid NN
currency character NN
rate_per_usd numeric NN
buffer_pct numeric NN
as_of date NN
source text NN
created_by text
created_at timestamp with time zone NN
```

### `booking.hotel_room_types` (table)
```
id uuid NN
hotel_id uuid NN
name text NN
max_occupancy smallint
bed_types _text NN
internal_notes text
status text NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `booking.hotels` (table)
```
id uuid NN
code text NN
supplier_id uuid NN
name text NN
hotel_style text
star_rating smallint
address text
destination_id uuid
country_code character
latitude numeric
longitude numeric
check_in_time time without time zone
check_out_time time without time zone
amenities _text NN
links jsonb NN
internal_notes text
status text NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `booking.inbox_cursor` (table, ~1 rows)
```
source text NN
contract text NN
safe_id bigint NN
updated_at timestamp with time zone NN
```

### `booking.inbox_events` (table)
```
id uuid NN
source text NN
contract text NN
idempotency_key text NN
payload jsonb NN
received_at timestamp with time zone NN
processed_at timestamp with time zone
error text
status text NN
contract_version text
source_position bigint
```

### `booking.job` (table, ~1095 rows)
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
idempotency_key text
result jsonb
error text
created_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
started_at timestamp with time zone
finished_at timestamp with time zone
```

### `booking.media_files` (table)
```
id uuid NN
s3_bucket text NN
s3_key text NN
content_type text NN
bytes bigint
width integer
height integer
sha256 text
uploaded_by uuid
created_at timestamp with time zone NN
deleted_at timestamp with time zone
```

### `booking.notification_reads` (table)
```
notification_id uuid NN
cis_user_id text NN
read_at timestamp with time zone NN
```

### `booking.notifications` (table, ~1 rows)
```
id uuid NN
recipient_type text NN
recipient_id uuid
type text NN
title text NN
message text
entity_type text
entity_id uuid
data jsonb NN
read_at timestamp with time zone
created_at timestamp with time zone NN
recipient_ref text
```

### `booking.policy_approvals` (table)
```
id uuid NN
entity_type text NN
pricing_rule_id uuid
fx_rate_id uuid
approved_by text NN
approved_at timestamp with time zone NN
note text
```

### `booking.pricing_rules` (table)
```
id uuid NN
channel text NN
target_margin numeric NN
floor_margin numeric NN
peak_uplift_pts numeric NN
card_fee_pct numeric NN
valid_from date NN
note text
created_by text
created_at timestamp with time zone NN
```

### `booking.services` (table)
```
id uuid NN
code text NN
supplier_id uuid NN
service_type text NN
title text NN
unit text NN
destination_id uuid
country_code character
source_system text
source_id text
max_group_size smallint
duration_minutes integer
inclusions _text NN
internal_notes text
status text NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `booking.settings` (table)
```
key text NN
value jsonb NN
description text
updated_at timestamp with time zone NN
```

### `booking.staff_assignments` (table)
```
id uuid NN
trip_case_id uuid NN
staff_user_id text NN
role text NN
assigned_by text
assigned_at timestamp with time zone NN
unassigned_at timestamp with time zone
```

### `booking.staff_users` (table)
```
cis_user_id text NN
email text
name text
role text NN
active boolean NN
cis_role text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
last_seen_at timestamp with time zone
preferences jsonb NN
```

### `booking.supplier_contracts` (table)
```
id uuid NN
supplier_id uuid NN
title text NN
reference text
valid_from date NN
valid_to date
currency character NN
payment_terms text
cancellation_policy text
notes text
status text NN
created_by text NN
updated_by text
published_by text
published_at timestamp with time zone
expired_by text
expired_at timestamp with time zone
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `booking.supplier_rates` (table)
```
id uuid NN
supplier_contract_id uuid NN
hotel_room_type_id uuid
service_id uuid
season text
valid_from date NN
valid_to date
unit text NN
meal_plan text
pax_min smallint
pax_max smallint
net_amount numeric NN
currency character NN
notes text
created_by text NN
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `booking.suppliers` (table)
```
id uuid NN
code text NN
company_name text NN
categories _text NN
website text
internal_notes text
contact_name text
contact_title text
contact_email text
contact_phone text
address text
region text
postal_code text
destination_id uuid
country_code character
status text NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `booking.trip_case_countries` (table)
```
trip_case_id uuid NN
country_code character NN
position smallint NN
created_at timestamp with time zone NN
```

### `booking.trip_case_legs` (table)
```
id uuid NN
trip_case_id uuid NN
position smallint NN
source_tour_id text NN
day_from smallint NN
day_to smallint NN
created_at timestamp with time zone NN
```

### `booking.trip_case_status_history` (table, ~1 rows)
```
id uuid NN
trip_case_id uuid NN
from_status text
to_status text NN
changed_by text
note text
changed_at timestamp with time zone NN
seq bigint NN
```

### `booking.trip_case_status_transitions` (table)
```
from_status text NN
to_status text NN
```

### `booking.trip_case_version_itinerary` (table, ~4 rows)
```
id uuid NN
trip_case_version_id uuid NN
position smallint NN
title text NN
day_from smallint NN
day_to smallint NN
source_tour_id text
notes text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
hotel_room_type_id uuid
service_id uuid
```

### `booking.trip_case_versions` (table)
```
id uuid NN
trip_case_id uuid NN
version_number smallint NN
notes text
total_price numeric
currency character
is_sent_to_customer boolean NN
sent_at timestamp with time zone
is_approved boolean NN
approved_at timestamp with time zone
created_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
title text
valid_until date
channel text
fx_rate_locked numeric
fx_as_of date
sent_by text
approved_by text
approval_note text
updated_by text
deleted_at timestamp with time zone
```

### `booking.trip_cases` (table, ~1 rows)
```
id uuid NN
code text NN
customer_id uuid NN
status text NN
trip_style text
start_date date
end_date date
pax smallint
currency character
source_system text NN
source_id text
idempotency_key text
inbox_event_id uuid
inquiry_snapshot jsonb
created_by uuid
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
notes text
pax_adults smallint
pax_children smallint
```

### `booking.trip_plans` (table)
```
id uuid NN
source_system text NN
source_id text NN
sellable boolean NN
trip_style text
default_channel text
price_hint_amount numeric
price_hint_currency character
price_hint_basis text
commercial_notes text
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `booking.v_customer_summary` (VIEW)
```
id uuid
code text
name text
email text
phone text
address text
verified boolean
is_blocked boolean
needs_merge_review boolean
merge_candidate_id uuid
source text
contact_consent boolean
contact_consent_at timestamp with time zone
created_at timestamp with time zone
updated_at timestamp with time zone
case_count bigint
open_case_count bigint
last_activity_at timestamp with time zone
status text
```

### `booking.v_schema_versions` (VIEW)
```
version character varying
description text
applied_at timestamp with time zone
```

### `booking.version_item_costs` (table, ~4 rows)
```
id uuid NN
version_item_id uuid NN
net_amount numeric NN
net_currency character NN
supplier_note text
entered_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
supplier_rate_id uuid
```

## `catalog` (14 objects)

### `catalog._tour_day_text` (VIEW)
```
source_system text
source_id text
tour_id uuid
tour_country text
day_number integer
title text
body text
```

### `catalog.v_destination` (VIEW)
```
source_system text
source_id text
destination_id uuid
name text
country text
lat double precision
lng double precision
cover_photo_path text
cover_image_url text
photo_count bigint
created_at timestamp with time zone
updated_at timestamp with time zone
geo_status text
located_by text
precision text
```

### `catalog.v_destination_photo` (VIEW)
```
destination_id uuid
photo_id uuid
path text
place_label text
tour_id uuid
width integer
height integer
position bigint
updated_at timestamp with time zone
```

### `catalog.v_graph_edge` (VIEW)
```
from_destination_id uuid
to_destination_id uuid
tour_count integer
source_ids _text
tour_ids _uuid
km double precision
build_id uuid
```

### `catalog.v_graph_node` (VIEW)
```
destination_id uuid
name text
country text
lat double precision
lng double precision
located_by text
precision text
source_ids _text
tour_ids _uuid
stop_count integer
activities _text
intensity_min text
intensity_max text
season_months _int4
build_id uuid
built_at timestamp with time zone
```

### `catalog.v_tour` (VIEW)
```
source_system text
source_id text
tour_id uuid
source_version smallint
sku text
slug text
title character varying
subtitle character varying
summary text
description text
highlights jsonb
country text
duration_raw text
duration_days integer
activities jsonb
inclusions text
exclusions text
best_time_to_go character varying
group_size text
lifecycle_stage text
itinerary_text text
cover_photo_path text
photo_count bigint
published_at timestamp with time zone
updated_at timestamp with time zone
content_hash text
```

### `catalog.v_tour_component` (VIEW)
```
source_system text
source_id text
tour_id uuid
built_from_tour_id uuid
is_stale boolean
component_id uuid
day_index integer
destination_id uuid
name text
country text
activity text
intensity_level text
season_months _int4
duration_hint text
text_extract text
place_card_id uuid
embedding vector
```

### `catalog.v_tour_day` (VIEW)
```
source_system text
source_id text
tour_id uuid
day_number integer
title text
body text
places _text
```

### `catalog.v_tour_day_route` (VIEW)
```
source_system text
source_id text
tour_id uuid
built_from_tour_id uuid
is_stale boolean
day_index integer
title text
start_place text
end_place text
overnight_place text
overnight_destination_id uuid
places _text
extracted_by text
is_transit_day boolean
```

### `catalog.v_tour_junction` (VIEW)
```
destination_a uuid
destination_b uuid
km double precision
cross_border boolean
build_id uuid
```

### `catalog.v_tour_leg` (VIEW)
```
source_system text
source_id text
tour_id uuid
day_from integer
day_to integer
days integer
start_destination_id uuid
end_destination_id uuid
destination_ids _uuid
countries _text
activities _text
build_id uuid
```

### `catalog.v_tour_photo` (VIEW)
```
source_system text
source_id text
tour_id uuid
photo_id uuid
path text
place_label text
destination_id uuid
width integer
height integer
position bigint
updated_at timestamp with time zone
```

### `catalog.v_tour_place` (VIEW)
```
source_system text
source_id text
tour_id uuid
day_number smallint
position bigint
place_name text
place_card_id uuid
place_display_name text
locality text
region text
country text
destination_id uuid
destination_name text
lat double precision
lng double precision
activity_types _text
atom_count bigint
located_by text
precision text
```

### `catalog.v_tour_stop` (VIEW)
```
source_system text
source_id text
tour_id uuid
day_index integer
destination_id uuid
country text
source text
build_id uuid
```

## `geo` (12 objects)

### `geo.geocode_call` (table)
```
id bigint NN
called_at timestamp with time zone NN
provider text NN
requests integer NN
cost_usd numeric NN
job_id uuid
```

### `geo.graph_build` (table)
```
build_id uuid NN
params jsonb NN
stats jsonb NN
is_current boolean NN
built_at timestamp with time zone NN
job_id uuid
```

### `geo.graph_edge` (table, ~209 rows)
```
build_id uuid NN
from_destination_id uuid NN
to_destination_id uuid NN
tour_count integer NN
source_ids _text NN
km numeric
```

### `geo.graph_node` (table, ~143 rows)
```
build_id uuid NN
destination_id uuid NN
name text NN
country text
lat double precision NN
lng double precision NN
source_ids _text NN
stop_count integer NN
activities _text NN
intensity_min text
intensity_max text
season_months _int4 NN
```

### `geo.place_name` (table, ~573 rows)
```
name_norm text NN
country_norm text NN
locality_norm text NN
display_name text NN
country text NN
locality text
tour_name text
destination_id uuid
place_card_id uuid
status text NN
tries integer NN
last_error text
next_retry_at timestamp with time zone NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `geo.place_outlier` (table)
```
destination_id uuid NN
source_id text NN
day_index integer NN
km numeric NN
observed_at timestamp with time zone NN
```

### `geo.tour_build` (table, ~27 rows)
```
source_id text NN
tour_id uuid NN
country text
days_hash text
components_hash text
rule_version integer NN
status text NN
counts jsonb NN
cost_usd numeric NN
built_at timestamp with time zone
job_id uuid
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```

### `geo.tour_day` (table, ~392 rows)
```
source_id text NN
day_index integer NN
tour_id uuid NN
title text
start_place text
end_place text
overnight_place text
anchor_place text
anchor_norm text
anchor_country_norm text
anchor_locality_norm text NN
overnight_destination_id uuid
places _text NN
extracted_by text NN
is_transit_day boolean NN
created_at timestamp with time zone NN
```

### `geo.tour_junction` (table, ~2854 rows)
```
build_id uuid NN
destination_a uuid NN
destination_b uuid NN
km numeric NN
cross_border boolean NN
```

### `geo.tour_leg` (table, ~1971 rows)
```
build_id uuid NN
source_id text NN
day_from integer NN
day_to integer NN
days integer NN
start_destination_id uuid NN
end_destination_id uuid NN
destination_ids _uuid NN
countries _text NN
activities _text NN
```

### `geo.tour_place` (table, ~967 rows)
```
component_id uuid NN
source_id text NN
tour_id uuid NN
day_index integer NN
name text NN
name_norm text NN
country text NN
country_norm text NN
locality_norm text NN
destination_id uuid
place_card_id uuid
activity text NN
intensity_level text NN
season_months _int4 NN
duration_hint text NN
text_extract text NN
text_hash text NN
atom_ids _text NN
created_at timestamp with time zone NN
embedding vector
```

### `geo.tour_stop` (table, ~407 rows)
```
build_id uuid NN
source_id text NN
day_index integer NN
destination_id uuid NN
country text
source text NN
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

### `gold_aa_internal.published_tours` (table, ~886 rows)
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

### `gold_aa_internal.tenant_tour_versions` (table, ~39 rows)
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

## `shared` (44 objects)

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

### `shared.cost_explorer_snapshot` (table, ~6923 rows)
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

### `shared.decision_cache_hits_daily` (table, ~190 rows)
```
day date NN
stage text NN
question_key text NN
mode text NN
zone text NN
hits bigint NN
updated_at timestamp with time zone NN
```

### `shared.decision_log` (table, ~280310 rows)
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

### `shared.destinations` (table, ~1469 rows)
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
geo_status text NN
confidence real
geocoder_place_id text
geo_checked_at timestamp with time zone
name_norm text
locality_norm text NN
duplicate_of uuid
geo_precision text
geocoder_provider text
geocoded_at timestamp with time zone
geocoder_meta jsonb
review_reason text
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

### `shared.dfs_call_log` (table, ~2545 rows)
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

### `shared.jev_credit_topup` (table)
```
id bigint NN
topped_up_on date NN
amount_usd numeric NN
note text
created_by text
created_at timestamp with time zone NN
```

### `shared.jev_tenant_allowlist` (table)
```
tenant_id uuid NN
reason text NN
added_at timestamp with time zone NN
added_by text NN
```

### `shared.job` (table, ~2533 rows)
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

### `shared.job_worker` (table, ~148 rows)
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

### `shared.llm_call_daily` (table)
```
day date NN
app text NN
tenant_id uuid
stage text NN
role text NN
model text NN
provider text
account text
is_shadow boolean NN
calls bigint NN
fallback_calls bigint NN
tokens_in bigint NN
tokens_out bigint NN
cost_usd numeric NN
updated_at timestamp with time zone NN
```

### `shared.llm_call_log` (table, ~252375 rows)
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

### `shared.llm_shadow_log` (table, ~5554 rows)
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

### `shared.notifications` (table, ~12 rows)
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

### `shared.pipeline_jobs` (table, ~523 rows)
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

### `shared.rerun_wave` (table)
```
id uuid NN
name text NN
country text
expected_tour_ids _uuid NN
status text NN
notes text
created_by text
created_at timestamp with time zone NN
closed_at timestamp with time zone
last_checked_at timestamp with time zone
last_check jsonb
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

### `shared.tenant_api_usage` (table, ~121332 rows)
```
id uuid NN
tenant_id uuid
endpoint character varying NN
method character varying NN
status_code integer NN
response_ms integer
called_at timestamp with time zone NN
actor_type character varying NN
admin_user_id uuid
```

### `shared.tenant_api_usage_monthly` (table)
```
month date NN
tenant_id uuid
actor_type text NN
calls bigint NN
ok_calls bigint NN
rate_limited_calls bigint NN
server_error_calls bigint NN
response_ms_sum bigint NN
response_ms_count bigint NN
updated_at timestamp with time zone NN
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
default_cta text
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
daily_publish_limit integer
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

### `silver_aa_internal.generated_content` (table, ~1423 rows)
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

### `silver_aa_internal.quality_scores` (table, ~1432 rows)
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

### `silver_aa_internal.review_queue` (table, ~229 rows)
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

### `silver_aa_internal.seo_context` (table, ~898 rows)
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

## `tripplanner` (16 objects)

### `tripplanner.customers` (table)
```
id uuid NN
name text NN
phone text
email text
created_at timestamp with time zone NN
contact_consent boolean NN
contact_consent_at timestamp with time zone
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

### `tripplanner.llm_spend_daily` (table)
```
day date NN
stage text NN
cost_usd numeric NN
calls integer NN
unpriced_calls integer NN
updated_at timestamp with time zone NN
```

### `tripplanner.narration_cache` (table)
```
itinerary_hash text NN
mode text NN
narration text NN
source text NN
days integer NN
created_at timestamp with time zone NN
hits integer NN
last_hit_at timestamp with time zone
```

### `tripplanner.outbox` (table)
```
id bigint NN
event text NN
schema_version integer NN
idempotency_key text NN
aggregate_id uuid NN
payload jsonb NN
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

### `tripplanner.v_inquiry_outbox` (VIEW)
```
id bigint
schema_version integer
idempotency_key text
trip_id uuid
payload jsonb
created_at timestamp with time zone
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
- `shared.admin_role`: admin,reviewer,content
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
acp_shared.atom_place_card.atom_id -> acp_contract.tour_atoms.atom_id
acp_shared.atom_place_card.card_id -> acp_shared.place_card.card_id
acp_shared.content_piece.angle_gate_option_id -> acp_shared.angle_gate_option.option_id
acp_shared.content_piece.angle_gate_request_id -> acp_shared.angle_gate_request.request_id
acp_shared.content_piece.job_id -> shared.job.id
acp_shared.content_piece.tenant_id -> shared.tenants.tenant_id
acp_shared.content_piece_label.piece_id -> acp_shared.content_piece.piece_id
acp_shared.debate_brand_fit_cache.tenant_id -> shared.tenants.tenant_id
acp_shared.facts.tenant_id -> shared.tenants.tenant_id
acp_shared.place_card.destination_id -> shared.destinations.id
acp_shared.place_card_alias.card_id -> acp_shared.place_card.card_id
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
booking.customer_otps.customer_id -> booking.customers.id
booking.customer_sessions.customer_id -> booking.customers.id
booking.customers.merge_candidate_id -> booking.customers.id
booking.customers.profile_media_id -> booking.media_files.id
booking.fx_rates.created_by -> booking.staff_users.cis_user_id
booking.hotel_room_types.created_by -> booking.staff_users.cis_user_id
booking.hotel_room_types.hotel_id -> booking.hotels.id
booking.hotel_room_types.updated_by -> booking.staff_users.cis_user_id
booking.hotels.country_code -> booking.countries.iso2
booking.hotels.created_by -> booking.staff_users.cis_user_id
booking.hotels.supplier_id -> booking.suppliers.id
booking.hotels.updated_by -> booking.staff_users.cis_user_id
booking.notification_reads.cis_user_id -> booking.staff_users.cis_user_id
booking.notification_reads.notification_id -> booking.notifications.id
booking.policy_approvals.fx_rate_id -> booking.fx_rates.id
booking.policy_approvals.pricing_rule_id -> booking.pricing_rules.id
booking.pricing_rules.created_by -> booking.staff_users.cis_user_id
booking.services.country_code -> booking.countries.iso2
booking.services.created_by -> booking.staff_users.cis_user_id
booking.services.supplier_id -> booking.suppliers.id
booking.services.updated_by -> booking.staff_users.cis_user_id
booking.staff_assignments.assigned_by -> booking.staff_users.cis_user_id
booking.staff_assignments.staff_user_id -> booking.staff_users.cis_user_id
booking.staff_assignments.trip_case_id -> booking.trip_cases.id
booking.supplier_contracts.created_by -> booking.staff_users.cis_user_id
booking.supplier_contracts.expired_by -> booking.staff_users.cis_user_id
booking.supplier_contracts.published_by -> booking.staff_users.cis_user_id
booking.supplier_contracts.supplier_id -> booking.suppliers.id
booking.supplier_contracts.updated_by -> booking.staff_users.cis_user_id
booking.supplier_rates.created_by -> booking.staff_users.cis_user_id
booking.supplier_rates.hotel_room_type_id -> booking.hotel_room_types.id
booking.supplier_rates.service_id -> booking.services.id
booking.supplier_rates.supplier_contract_id -> booking.supplier_contracts.id
booking.supplier_rates.updated_by -> booking.staff_users.cis_user_id
booking.suppliers.country_code -> booking.countries.iso2
booking.suppliers.created_by -> booking.staff_users.cis_user_id
booking.suppliers.updated_by -> booking.staff_users.cis_user_id
booking.trip_case_countries.country_code -> booking.countries.iso2
booking.trip_case_countries.trip_case_id -> booking.trip_cases.id
booking.trip_case_legs.trip_case_id -> booking.trip_cases.id
booking.trip_case_status_history.changed_by -> booking.staff_users.cis_user_id
booking.trip_case_status_history.trip_case_id -> booking.trip_cases.id
booking.trip_case_version_itinerary.hotel_room_type_id -> booking.hotel_room_types.id
booking.trip_case_version_itinerary.service_id -> booking.services.id
booking.trip_case_version_itinerary.trip_case_version_id -> booking.trip_case_versions.id
booking.trip_case_versions.approved_by -> booking.staff_users.cis_user_id
booking.trip_case_versions.created_by -> booking.staff_users.cis_user_id
booking.trip_case_versions.sent_by -> booking.staff_users.cis_user_id
booking.trip_case_versions.trip_case_id -> booking.trip_cases.id
booking.trip_case_versions.updated_by -> booking.staff_users.cis_user_id
booking.trip_cases.customer_id -> booking.customers.id
booking.trip_cases.inbox_event_id -> booking.inbox_events.id
booking.trip_plans.created_by -> booking.staff_users.cis_user_id
booking.trip_plans.updated_by -> booking.staff_users.cis_user_id
booking.version_item_costs.entered_by -> booking.staff_users.cis_user_id
booking.version_item_costs.supplier_rate_id -> booking.supplier_rates.id
booking.version_item_costs.version_item_id -> booking.trip_case_version_itinerary.id
geo.graph_edge.build_id -> geo.graph_build.build_id
geo.graph_edge.from_destination_id -> shared.destinations.id
geo.graph_edge.to_destination_id -> shared.destinations.id
geo.graph_node.build_id -> geo.graph_build.build_id
geo.graph_node.destination_id -> shared.destinations.id
geo.place_name.destination_id -> shared.destinations.id
geo.place_name.place_card_id -> acp_shared.place_card.card_id
geo.place_outlier.destination_id -> shared.destinations.id
geo.tour_day.overnight_destination_id -> shared.destinations.id
geo.tour_junction.build_id -> geo.graph_build.build_id
geo.tour_junction.destination_a -> shared.destinations.id
geo.tour_junction.destination_b -> shared.destinations.id
geo.tour_leg.build_id -> geo.graph_build.build_id
geo.tour_leg.end_destination_id -> shared.destinations.id
geo.tour_leg.start_destination_id -> shared.destinations.id
geo.tour_place.destination_id -> shared.destinations.id
geo.tour_place.place_card_id -> acp_shared.place_card.card_id
geo.tour_stop.build_id -> geo.graph_build.build_id
geo.tour_stop.destination_id -> shared.destinations.id
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
shared.destinations.duplicate_of -> shared.destinations.id
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
| bk-010 | 2026-10-15 06:10:43.263554+00:00 | AA-823 wave 2b: hotels (HTL- code, supplier, style, stars, place, geo, check-in/out, amenities, links, active/inactive), hotel_room_types, services (SVC- code, activity/transfer/guide/entrance/meal, unit, place, CIS source ref), supplier_rates under draft-only contracts (fixed once published), version items reference a room type or service, cost lines name their rate, no customer-facing columns (Q17) |
| 233 | 2026-10-15 05:51:59.990701+00:00 | AA-825: sargable v_tenant_monthly_usage + (tenant_id, called_at) index, retention indexes, ledger autovacuum, shared.llm_call_daily + shared.tenant_api_usage_monthly rollups |
| 229 | 2026-10-15 05:10:15.575344+00:00 | AA-817: tenant-pool RLS template (TO aa_app_user, NULLIF app.tenant_id, WITH CHECK) on tenant_tour_versions, angle_gate_request, content_piece, publish_log, facts (platform rows read-only); drop drift policies; SELECT/INSERT/UPDATE on tenant_tour_versions to aa_app_user; no default privileges to aa_app_user. ENABLE without FORCE (owner exempt) |
| 231 | 2026-10-15 04:29:28.914998+00:00 | AA-791: acp_shared.content_piece_label — human label per T9 piece and labeller (as_is/light/heavy/reject, defects, minutes, reason, content sha256) |
| bk-009 | 2026-10-15 04:28:06.478539+00:00 | AA-679: trip_plans (commercial-only row per CIS catalog tour, keyed on source_system + source_id: sellable, trip style, channel, price hint, notes) |
| bk-008 | 2026-10-15 01:27:29.530670+00:00 | AA-822 wave 2a: suppliers (SUP- code, categories, contact, address, destination_id, country_code, active/inactive, no delete) + supplier_contracts (validity, currency, payment terms, cancellation policy, draft/published/expired, maker-checker publish, published lock), countries MN |
| 230 | 2026-10-15 00:37:26.367349+00:00 | AA-819: shared.tenants.daily_publish_limit — nullable per-tenant override of the daily publish limit (NULL = code default 20/UTC day) |
| bk-007 | 2026-10-15 00:29:57.154774+00:00 | AA-810: policy_approvals (maker-checker for pricing_rules / fx_rates, append-only), seed rules approved as seed:bk-004, existing rows back-filled |
| 228 | 2026-10-15 00:25:32.714676+00:00 | AA-712: catalog place/graph views over geo — v_tour_component, v_tour_day_route, v_tour_stop, v_tour_leg, v_graph_node, v_graph_edge, v_tour_junction; v_tour_place (destination by pipeline link) and v_destination + located_by/precision (appended); owner catalog_owner, SELECT to aa_app_user, tripplanner, booking |
| 226 | 2026-10-14 14:52:31.570475+00:00 | AA-712: schema geo (place pipeline: tour_build, tour_day, tour_place, place_name, place_outlier, geocode_call, graph builds), shared.destinations key (name_norm, country, locality_norm) + geo columns, place_card.destination_id, stages a3_place_days/locate/embed, geocoder budgets |
| 227 | 2026-10-14 12:39:11.961719+00:00 | AA-801: llm_model_catalog sonnet-5, opus-5-5 supports_temperature = false (Bedrock: temperature is deprecated for this model) |
| bk-006 | 2026-10-14 12:09:22.414869+00:00 | AA-810: version_item_cost_lock also refuses cost writes on SENT versions (was approved only) |
| bk-005 | 2026-10-14 12:06:06.424963+00:00 | AA-681 W1: transitions proposal_sent->confirmed, confirmed->cancelled, cancelled->new_inquiry, pax split, countries + trip_case_countries, customers.code (CUS-), v_customer_summary, version title/valid_until/channel/FX lock/sent+approved by/soft delete + sent lock (no hard delete), notifications.recipient_ref + notification_reads, staff preferences, settings, audit entity_label/summary |
| bk-004 | 2026-10-14 12:02:49.399633+00:00 | AA-810: pricing_rules (ADR 0005 seed 30/20, 25/18, 15/10, append-only), fx_rates (dated, append-only), version_item_costs (FK bk-003 trip_case_version_itinerary, approval lock) |
| 225 | 2026-10-14 10:31:12.547644+00:00 | AA-679: schema catalog (CIS read model) — v_tour, v_tour_day, v_tour_place, v_tour_photo, v_destination, v_destination_photo owned by catalog_owner (NOLOGIN, AA-master RLS read policy); SELECT to aa_app_user, tripplanner, booking |
