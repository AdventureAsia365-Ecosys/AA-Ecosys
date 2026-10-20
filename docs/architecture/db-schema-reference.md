# AA-Ecosys DB Schema Reference (live dump)

<!-- schema-fingerprint: 800bbb433405e7b15d683b80177a2a4b5d8b21da36d69e459c5b78bd63fa71fb -->

**Verified:** 2026-10-20 05:28 UTC — live catalog dump of the shared RDS (`aa-cis-dev-db`, `aa-cis/dev/rds`, acc2 `005097885195`, us-west-1, PostgreSQL 15.17). Latest migration per owner: CIS **251**, TripPlanner **tp-015**, Booking **bk-017** (260 versions registered).

> **Generated file — do not edit by hand** (data standards DM-3.1). It is the single source of truth for table/column names, owners, grants and RLS across CIS, TripPlanner and Booking (one RDS, one schema per owner; ownership rules: `docs/database/schema-ownership.md`). Read it before introspecting columns. AA-CIS-Infra `.github/workflows/db-schema-dump.yml` regenerates it after every DB Migrate apply and every night (`db/schema_dump.py` in a one-off ECS task, then `db/gen_schema_reference.py`) and opens a PR here when the structure changed.
> Source: AA-CIS-Infra DB Schema Dump (after DB Migrate apply of cis/251_alert_recipient.sql (run 39374915493)), https://github.com/AdventureAsia365-Ecosys/AA-CIS-Infra/actions/runs/39375039192

**Totals:** 15 schemas (4 empty: acp_gold_output, acp_silver_s2, acp_silver_s3, acp_silver_s4), 178 tables/views, 417 indexes, 177 FKs, 45 RLS policy(ies), 18 functions, 13 enums. Database size 938.5 MB, max_connections 181. RLS catalogue guard: 0 unallowlisted violation(s) (see *RLS catalogue guard (X2)*).

## Conventions
- Column format: `name type` — `NN` suffix = NOT NULL. Types are `format_type()` output (`character varying(64)`, `text[]`, `vector(1024)`, enums schema-qualified).
- `~N rows` = `pg_class.reltuples` estimate, sizes = `pg_total_relation_size`, both as of the Verified line (a PR is opened only when the structure changes, so these lag between structural changes). Run exact counts before any drop decision.
- Under each object: owner and RLS state (`RLS on` = ENABLE, `+ FORCE` = FORCE ROW LEVEL SECURITY; the owner is exempt unless FORCE), indexes, CHECK constraints, grants to roles other than the owner (`*` = WITH GRANT OPTION), column-level grants, RLS policies and triggers. Usage counters are in *Table activity* at the end.
- `raw_tours` PK is `tour_id` (NOT `id`). `quality_scores` has `evaluated_at` (NOT `created_at`). `published_tours`/`seo_context` have NO `country` — always JOIN `raw_tours`.

## Schemas

| schema | owner | objects | size | grants (USAGE / CREATE) |
|---|---|---|---|---|
| `acp_contract` | cis_owner | 18 | 236.4 MB | catalog_owner: USAGE; cis_app: USAGE; tripplanner: USAGE |
| `acp_deliver` | cis_owner | 1 | 40 kB | aa_app_user: USAGE; cis_app: USAGE |
| `acp_gold_output` | cis_owner | 0 |  | cis_app: USAGE |
| `acp_shared` | cis_owner | 21 | 12 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE |
| `acp_silver_s2` | cis_owner | 0 |  | cis_app: USAGE |
| `acp_silver_s3` | cis_owner | 0 |  | cis_app: USAGE |
| `acp_silver_s4` | cis_owner | 0 |  | cis_app: USAGE |
| `booking` | bk_owner | 36 | 4.9 MB | booking: USAGE; cis_app: USAGE |
| `catalog` | cis_owner | 14 |  | aa_app_user: USAGE; booking: USAGE; catalog_owner: USAGE; tripplanner: USAGE |
| `geo` | cis_owner | 12 | 18.7 MB | catalog_owner: USAGE; cis_app: USAGE |
| `gold_aa_internal` | cis_owner | 4 | 5.9 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE; tripplanner: USAGE |
| `public` | pg_database_owner | 1 | 24 kB | PUBLIC: USAGE |
| `shared` | cis_owner | 47 | 559.7 MB | aa_app_user: USAGE; bk_owner: USAGE; catalog_owner: USAGE; cis_app: USAGE; tp_owner: USAGE; tripplanner: USAGE |
| `silver_aa_internal` | cis_owner | 7 | 23.5 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE; tripplanner: USAGE |
| `tripplanner` | tp_owner | 17 | 62.3 MB | booking: USAGE; cis_app: USAGE; tripplanner: USAGE |

## `acp_contract` (18 objects)

### `acp_contract.atom_decompose_jobs` (table, ~0 rows, 104 kB)
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
- owner `cis_owner`
- index `atom_decompose_jobs_pkey` PRIMARY KEY: UNIQUE btree (job_id)
- index `idx_atom_decompose_jobs_status`: btree (status) WHERE (status = ANY (ARRAY['submitted'::text, 'in_progress'::text]))
- check `atom_decompose_jobs_status_check`: CHECK ((status = ANY (ARRAY['submitted'::text, 'in_progress'::text, 'completed'::text, 'failed'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_embedding` (table, ~7298 rows, 118.4 MB)
```
atom_id text NN
view text NN
embedding vector(1536) NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `atom_embedding_pkey` PRIMARY KEY: UNIQUE btree (atom_id, view)
- index `idx_atom_embedding_vector`: ivfflat (embedding vector_cosine_ops) WITH (lists='10')
- check `atom_embedding_view_check`: CHECK ((view = ANY (ARRAY['place'::text, 'place_action'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_matches` (table, ~10119 rows, 3.3 MB)
```
id bigint NN
query text NN
kind text NN
atom_id text NN
distance double precision NN
matched_by text NN
matched_at timestamp with time zone NN
```
- owner `cis_owner`
- index `atom_matches_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `atom_matches_query_atom_id_key`: UNIQUE btree (query, atom_id)
- index `idx_atom_matches_atom`: btree (atom_id)
- check `atom_matches_kind_check`: CHECK ((kind = 'question'::text))
- check `atom_matches_matched_by_check`: CHECK ((matched_by = ANY (ARRAY['vector'::text, 'tokens'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_ranking` (table, ~107748 rows, 67.1 MB)
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
- owner `cis_owner`
- index `atom_ranking_pkey` PRIMARY KEY: UNIQUE btree (market, tour_id, segment_id, version)
- index `idx_atom_ranking_current_identity`: UNIQUE btree (market, tour_id, segment_id) WHERE (superseded_at IS NULL)
- index `idx_atom_ranking_market_total_rank_current`: btree (market, total_rank) WHERE ((superseded_at IS NULL) AND (excluded_reason IS NULL))
- index `idx_atom_ranking_market_tour_current`: btree (market, tour_id) WHERE (superseded_at IS NULL)
- check `atom_ranking_excluded_reason_check`: CHECK ((excluded_reason = ANY (ARRAY['transit'::text, 'unnamed_place'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_segment` (table, ~12496 rows, 3.8 MB)
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
- owner `cis_owner`
- index `atom_segment_pkey` PRIMARY KEY: UNIQUE btree (segment_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_segment_alias` (table, ~410 rows, 352 kB)
```
segment_id_old text NN
segment_id_canonical text NN
merged_at timestamp with time zone NN
```
- owner `cis_owner`
- index `atom_segment_alias_pkey` PRIMARY KEY: UNIQUE btree (segment_id_old)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_segment_member` (table, ~23987 rows, 5.4 MB)
```
segment_id text NN
atom_id text NN
is_alias boolean NN
```
- owner `cis_owner`
- index `atom_segment_member_pkey` PRIMARY KEY: UNIQUE btree (segment_id, atom_id)
- index `idx_atom_segment_member_atom`: btree (atom_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atomize_day_fingerprint` (table, ~10062 rows, 1.9 MB)
```
tenant_tour_version_id uuid NN
day_number integer NN
fingerprint_hash text NN
atomized_at timestamp with time zone NN
```
- owner `cis_owner`
- index `atomize_day_fingerprint_pkey` PRIMARY KEY: UNIQUE btree (tenant_tour_version_id, day_number)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.hub` (table, ~59 rows, 152 kB)
```
hub_id uuid NN
hub_name text NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `hub_pkey` PRIMARY KEY: UNIQUE btree (hub_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.question_embedding` (table, ~847 rows, 8.1 MB)
```
question_hash text NN
question_text text NN
embedding vector(1536) NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `question_embedding_pkey` PRIMARY KEY: UNIQUE btree (question_hash)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.route` (table, ~9063 rows, 5.6 MB)
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
- owner `cis_owner`
- index `idx_route_current`: btree (tour_id) WHERE (superseded_at IS NULL)
- index `idx_route_current_identity`: UNIQUE btree (tour_id, first_day, last_day) WHERE (superseded_at IS NULL)
- index `idx_route_hub`: btree (hub_id) WHERE (hub_id IS NOT NULL)
- index `idx_route_tour`: btree (tour_id)
- index `route_pkey` PRIMARY KEY: UNIQUE btree (route_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.route_pick` (table, 48 kB)
```
route_pick_id uuid NN
tenant_id uuid NN
hub_name text NN
route_snapshot jsonb NN
selected_at timestamp with time zone NN
selected_by text
```
- owner `cis_owner`
- index `idx_route_pick_tenant`: btree (tenant_id, selected_at DESC)
- index `subject_pkey` PRIMARY KEY: UNIQUE btree (route_pick_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.s1_from_atom_runs` (table, 64 kB)
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
- owner `cis_owner`
- index `idx_s1_from_atom_runs_prompt_version`: btree (prompt_version)
- index `idx_s1_from_atom_runs_tour_id`: btree (tour_id)
- index `s1_from_atom_runs_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `s1_from_atom_runs_status_check`: CHECK ((status = ANY (ARRAY['passed'::text, 'gate_failed'::text, 'error'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.search_demand` (table, ~5089 rows, 1.7 MB)
```
keyword text NN
market text NN
search_volume integer
people_also_ask jsonb NN
retrieved_on timestamp with time zone NN
serp_domains jsonb
```
- owner `cis_owner`
- index `search_demand_pkey` PRIMARY KEY: UNIQUE btree (keyword, market)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.segment_research_log` (table, ~1337 rows, 568 kB)
```
canonical_place text NN
market text NN
researched_at timestamp with time zone NN
```
- owner `cis_owner`
- index `segment_research_log_pkey` PRIMARY KEY: UNIQUE btree (canonical_place, market)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.tour_atoms` (table, ~32019 rows, 19.8 MB)
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
- owner `cis_owner`
- index `idx_tour_atoms_tour_id`: btree (tour_id) WHERE (NOT deleted)
- index `tour_atoms_pkey` PRIMARY KEY: UNIQUE btree (atom_id)
- check `tour_atoms_visual_potential_check`: CHECK (((visual_potential >= 1) AND (visual_potential <= 3)))
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `tripplanner`: SELECT (action, activity_type, atom_id, deleted, is_empty_marker, itinerary_day, owner_scope, place, season_note, text, tour_id)

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
- owner `cis_owner`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `tripplanner`: SELECT (action, activity_type, atom_id, deleted, is_empty_marker, itinerary_day, owner_scope, place, season_note, text, tour_id)

### `acp_contract.v_trip_registry` (VIEW)
```
id uuid
sku text
name character varying(500)
aa_name character varying(500)
duration_raw text
period text
price_raw text
destination text
itinerary_source text
itinerary_brand text
aa_summary text
aa_highlights jsonb
seo_title character varying(70)
seo_meta character varying(170)
seo_keywords_used jsonb
quality_score numeric(5,2)
content_embedding vector(1536)
trip_url text
url_alive boolean
inclusions text
exclusions text
tenant_id uuid
lifecycle_stage silver_aa_internal.tour_lifecycle_stage_enum
```
- owner `cis_owner`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

## `acp_deliver` (1 objects)

### `acp_deliver.tenant_tour_pages` (table, ~0 rows, 40 kB)
```
tenant_id text NN
tour_id uuid NN
url text NN
published_at timestamp with time zone
url_alive boolean
last_checked_at timestamp with time zone
```
- owner `cis_owner`
- index `tenant_tour_pages_pkey` PRIMARY KEY: UNIQUE btree (tenant_id, tour_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

## `acp_shared` (21 objects)

### `acp_shared.acp_output_rules` (table, 48 kB)
```
rule_id uuid NN
tenant_id character varying(50)
stage smallint
rule_type character varying(20) NN
pattern character varying(500) NN
action_value text
error_message character varying(500)
source_type character varying(20) NN
source_hitl_id uuid
run_count integer
is_active boolean
created_at timestamp with time zone
confidence_score numeric(5,4)
```
- owner `cis_owner` · RLS on
- index `acp_output_rules_pkey` PRIMARY KEY: UNIQUE btree (rule_id)
- index `idx_output_rules_active`: btree (is_active) WHERE (is_active = true)
- check `acp_output_rules_rule_type_check`: CHECK (((rule_type)::text = ANY (ARRAY[('block'::character varying)::text, ('replace'::character varying)::text, ('truncate'::character varying)::text, ('flag'::character varying)::text, ('score_gate'::character varying)::text])))
- check `acp_output_rules_source_type_check`: CHECK (((source_type)::text = ANY (ARRAY[('system'::character varying)::text, ('hitl_rejection'::character varying)::text, ('manual'::character varying)::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `acp_output_rules_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`

### `acp_shared.acp_quota_ledger` (table, 56 kB)
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
- owner `cis_owner`
- index `acp_quota_ledger_pkey` PRIMARY KEY: UNIQUE btree (ledger_id)
- index `acp_quota_ledger_tenant_id_key`: UNIQUE btree (tenant_id)
- index `idx_quota_tenant`: btree (tenant_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.angle_gate_option` (table, ~57 rows, 264 kB)
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
- owner `cis_owner` · RLS on
- index `angle_gate_option_pkey` PRIMARY KEY: UNIQUE btree (option_id)
- index `angle_gate_option_request_id_idx_key`: UNIQUE btree (request_id, idx)
- index `idx_angle_gate_option_request`: btree (request_id)
- check `angle_gate_option_idx_check`: CHECK (((idx >= 0) AND (idx <= 2)))
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: UPDATE (chosen)
- policy `angle_gate_option_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(EXISTS ( SELECT 1
   FROM acp_shared.angle_gate_request r
  WHERE ((r.request_id = angle_gate_option.request_id) AND (r.tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))))` WITH CHECK `(EXISTS ( SELECT 1
   FROM acp_shared.angle_gate_request r
  WHERE ((r.request_id = angle_gate_option.request_id) AND (r.tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))))`

### `acp_shared.angle_gate_request` (table, ~21 rows, 128 kB)
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
- owner `cis_owner` · RLS on
- index `angle_gate_request_pkey` PRIMARY KEY: UNIQUE btree (request_id)
- index `idx_angle_gate_request_status`: btree (status)
- index `idx_angle_gate_request_subject`: btree (subject_id) WHERE (subject_id IS NOT NULL)
- index `idx_angle_gate_request_tenant`: btree (tenant_id, created_at DESC)
- check `angle_gate_request_status_check`: CHECK ((status = ANY (ARRAY['pending_goal'::text, 'pending_choice'::text, 'approved'::text, 'reusable'::text])))
- grant `aa_app_user`: INSERT, SELECT, UPDATE
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `angle_gate_request_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `acp_shared.atom_place_card` (table, ~291 rows, 120 kB)
```
atom_id text NN
card_id uuid
resolved_at timestamp with time zone NN
miss_reason text
```
- owner `cis_owner`
- index `atom_place_card_pkey` PRIMARY KEY: UNIQUE btree (atom_id)
- index `idx_atom_place_card_card`: btree (card_id)
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.audit_log` (table, ~1353 rows, 1.1 MB)
```
id uuid NN
tenant_id character varying(50)
actor character varying(64)
action character varying(64)
resource_type character varying(32)
resource_id text
details jsonb
created_at timestamp with time zone
actor_type acp_shared.audit_actor_type
http_method text
route text
status smallint
chain_seq bigint
prev_hash text
row_hash text
```
- owner `cis_owner`
- index `audit_log_chain_seq_key`: UNIQUE btree (chain_seq) WHERE (chain_seq IS NOT NULL)
- index `audit_log_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `idx_audit_log_action`: btree (action, created_at DESC)
- index `idx_audit_log_actor_type`: btree (actor_type)
- index `idx_audit_log_tenant`: btree (tenant_id, created_at DESC)
- check `audit_log_http_method_chk`: CHECK (((http_method IS NULL) OR (http_method = ANY (ARRAY['POST'::text, 'PUT'::text, 'PATCH'::text, 'DELETE'::text]))))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `audit_log_chain`: BEFORE INSERT ON acp_shared.audit_log FOR EACH ROW EXECUTE FUNCTION acp_shared.audit_log_chain()
- trigger `audit_log_no_delete`: BEFORE DELETE ON acp_shared.audit_log FOR EACH ROW EXECUTE FUNCTION acp_shared.audit_log_append_only()
- trigger `audit_log_no_truncate`: BEFORE TRUNCATE ON acp_shared.audit_log FOR EACH STATEMENT EXECUTE FUNCTION acp_shared.audit_log_append_only()
- trigger `audit_log_no_update`: BEFORE UPDATE ON acp_shared.audit_log FOR EACH ROW EXECUTE FUNCTION acp_shared.audit_log_append_only()

### `acp_shared.content_piece` (table, ~251 rows, 8.4 MB)
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
content_embedding vector(1536)
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
- owner `cis_owner` · RLS on
- index `content_piece_job_idx`: btree (job_id) WHERE (job_id IS NOT NULL)
- index `content_piece_pkey` PRIMARY KEY: UNIQUE btree (piece_id)
- index `idx_content_piece_embedding`: ivfflat (content_embedding vector_cosine_ops) WITH (lists='10')
- index `idx_content_piece_held`: btree (tenant_id, status) WHERE (status = 'held'::text)
- index `idx_content_piece_request`: btree (angle_gate_request_id, attempt_number DESC)
- index `idx_content_piece_tenant`: btree (tenant_id, created_at DESC)
- check `content_piece_status_check`: CHECK ((status = ANY (ARRAY['processing'::text, 'approved'::text, 'held'::text, 'failed'::text])))
- grant `aa_app_user`: INSERT, SELECT, UPDATE
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `content_piece_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `acp_shared.content_piece_label` (table, 48 kB)
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
- owner `cis_owner`
- index `content_piece_label_pkey` PRIMARY KEY: UNIQUE btree (piece_id, labelled_by)
- index `idx_content_piece_label_label`: btree (label, labelled_at DESC)
- check `content_piece_label_defects_check`: CHECK ((jsonb_typeof(defects) = 'object'::text))
- check `content_piece_label_label_check`: CHECK ((label = ANY (ARRAY['as_is'::text, 'light'::text, 'heavy'::text, 'reject'::text])))
- check `content_piece_label_labelled_by_check`: CHECK ((length(btrim(labelled_by)) > 0))
- check `content_piece_label_minutes_to_fix_check`: CHECK (((minutes_to_fix IS NULL) OR ((minutes_to_fix >= 0) AND (minutes_to_fix <= 600))))
- check `content_piece_label_reason_check`: CHECK (((reason IS NULL) OR (length(reason) <= 4000)))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.debate_brand_fit_cache` (table, ~375 rows, 344 kB)
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
- owner `cis_owner`
- index `debate_brand_fit_cache_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `idx_debate_brand_fit_route`: UNIQUE btree (tenant_id, route_id, brand_version) WHERE (route_id IS NOT NULL)
- index `idx_debate_brand_fit_segment`: UNIQUE btree (tenant_id, segment_id, brand_version) WHERE (segment_id IS NOT NULL)
- check `debate_brand_fit_cache_check`: CHECK (((segment_id IS NOT NULL) <> (route_id IS NOT NULL)))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.facts` (table, 64 kB)
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
- owner `cis_owner` · RLS on
- index `facts_pkey` PRIMARY KEY: UNIQUE btree (fact_id)
- index `idx_facts_scope`: btree (scope)
- index `idx_facts_tenant`: btree (tenant_id) WHERE (scope = 'tenant'::text)
- check `facts_scope_check`: CHECK ((scope = ANY (ARRAY['platform'::text, 'tenant'::text])))
- check `facts_scope_tenant_ck`: CHECK ((((scope = 'platform'::text) AND (tenant_id IS NULL)) OR ((scope = 'tenant'::text) AND (tenant_id IS NOT NULL))))
- grant `aa_app_user`: INSERT, SELECT, UPDATE
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `facts_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `facts_platform_read` (PERMISSIVE SELECT TO aa_app_user): USING `(scope = 'platform'::text)`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))` WITH CHECK `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))`

### `acp_shared.marketplace_portfolios` (table, 32 kB)
```
portfolio_id uuid NN
tour_ids uuid[] NN
filters_used jsonb
atom_snapshot jsonb
status text NN
created_at timestamp with time zone NN
finalized_at timestamp with time zone
```
- owner `cis_owner`
- index `marketplace_portfolios_pkey` PRIMARY KEY: UNIQUE btree (portfolio_id)
- check `marketplace_portfolios_status_check`: CHECK ((status = ANY (ARRAY['draft'::text, 'finalized'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.place_card` (table, ~111 rows, 344 kB)
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
cost_usd numeric(10,6) NN
verified_by text
verified_at timestamp with time zone
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
destination_id uuid
```
- owner `cis_owner`
- index `place_card_pkey` PRIMARY KEY: UNIQUE btree (card_id)
- index `place_card_place_key_key`: UNIQUE btree (place_key)
- check `place_card_status_check`: CHECK ((status = ANY (ARRAY['auto_checked'::text, 'verified'::text, 'rejected'::text])))
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.place_card_alias` (table, ~361 rows, 136 kB)
```
alias_norm text NN
country_norm text NN
card_id uuid NN
source text NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `idx_place_card_alias_card`: btree (card_id)
- index `place_card_alias_pkey` PRIMARY KEY: UNIQUE btree (alias_norm, country_norm)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.place_card_miss` (table, 32 kB)
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
- owner `cis_owner`
- index `place_card_miss_pkey` PRIMARY KEY: UNIQUE btree (place_norm, country_norm)
- check `place_card_miss_reason_check`: CHECK ((reason = ANY (ARRAY['no_name'::text, 'identity_rejected'::text, 'error'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.publish_log` (table, 96 kB)
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
- owner `cis_owner` · RLS on
- index `idx_publish_log_piece`: btree (piece_id)
- index `idx_publish_log_published`: btree (tenant_id, status) WHERE (status = 'published'::text)
- index `idx_publish_log_tenant`: btree (tenant_id, created_at DESC)
- index `publish_log_pkey` PRIMARY KEY: UNIQUE btree (publish_id)
- index `uq_publish_log_active_key`: UNIQUE btree (idempotency_key) WHERE ((idempotency_key IS NOT NULL) AND (status = ANY (ARRAY['requested'::text, 'published'::text])))
- check `publish_log_status_check`: CHECK ((status = ANY (ARRAY['requested'::text, 'published'::text, 'unpublished'::text, 'failed'::text])))
- grant `aa_app_user`: INSERT, SELECT, UPDATE
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `publish_log_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `acp_shared.quarter_plan` (table, ~6 rows, 88 kB)
```
plan_id uuid NN
tenant_id uuid NN
year integer NN
quarter smallint NN
current_version_id uuid
created_at timestamp with time zone NN
year_plan_id uuid
```
- owner `cis_owner`
- index `idx_quarter_plan_year_plan_id`: btree (year_plan_id) WHERE (year_plan_id IS NOT NULL)
- index `quarter_plan_pkey` PRIMARY KEY: UNIQUE btree (plan_id)
- index `quarter_plan_tenant_id_year_quarter_key`: UNIQUE btree (tenant_id, year, quarter)
- check `quarter_plan_quarter_check`: CHECK (((quarter >= 1) AND (quarter <= 4)))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.quarter_plan_version` (table, ~0 rows, 112 kB)
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
- owner `cis_owner`
- index `idx_quarter_plan_version_approval_status`: btree (approval_status)
- index `idx_quarter_plan_version_plan_id`: btree (plan_id)
- index `quarter_plan_version_pkey` PRIMARY KEY: UNIQUE btree (version_id)
- index `quarter_plan_version_plan_id_version_no_key`: UNIQUE btree (plan_id, version_no)
- check `quarter_plan_version_approval_status_check`: CHECK (((approval_status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[])))
- check `quarter_plan_version_source_check`: CHECK (((source)::text = ANY ((ARRAY['standard'::character varying, 'override'::character varying])::text[])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.subject` (table, ~342 rows, 560 kB)
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
- owner `cis_owner`
- index `idx_subject_tenant_channel_score`: btree (tenant_id, channel, score)
- index `idx_subject_unique_route`: UNIQUE btree (tenant_id, channel, route_id) WHERE (route_id IS NOT NULL)
- index `idx_subject_unique_segment`: UNIQUE btree (tenant_id, channel, segment_id) WHERE (segment_id IS NOT NULL)
- index `subject_pkey` PRIMARY KEY: UNIQUE btree (subject_id)
- check `subject_check`: CHECK ((((segment_id IS NOT NULL) AND (route_id IS NULL)) OR ((segment_id IS NULL) AND (route_id IS NOT NULL))))
- check `subject_state_check`: CHECK ((state = ANY (ARRAY['proposed'::text, 'picked'::text, 'used'::text, 'cut'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.tenant_atom_state` (table, ~0 rows, 80 kB)
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
- owner `cis_owner`
- index `idx_tenant_atom_state_tenant`: btree (tenant_id)
- index `tenant_atom_state_pkey` PRIMARY KEY: UNIQUE btree (tenant_id, tour_id)
- check `tenant_atom_state_assigned_angle_check`: CHECK ((assigned_angle = ANY (ARRAY['culinary_people'::text, 'physical_terrain'::text, 'culture_craft'::text, 'nature_wildlife'::text, 'luxury_leisure'::text, 'family_group'::text, 'wellness_spiritual'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.tenant_config` (table, 32 kB)
```
tenant_id uuid NN
markets text[] NN
channels text[] NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `tenant_config_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- check `tenant_config_channels_not_empty`: CHECK ((array_length(channels, 1) > 0))
- check `tenant_config_channels_valid`: CHECK ((channels <@ ARRAY['blog'::text, 'linkedin'::text, 'facebook'::text, 'instagram'::text, 'tiktok'::text, 'email'::text, 'landing_page'::text, 'ads'::text]))
- check `tenant_config_markets_not_empty`: CHECK ((array_length(markets, 1) > 0))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.year_plan` (table, 40 kB)
```
year_plan_id uuid NN
tenant_id uuid NN
year integer NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `year_plan_pkey` PRIMARY KEY: UNIQUE btree (year_plan_id)
- index `year_plan_tenant_id_year_key`: UNIQUE btree (tenant_id, year)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

## `booking` (36 objects)

### `booking.audit_logs` (table, ~54 rows, 160 kB)
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
- owner `bk_owner`
- index `audit_logs_actor_ref_idx`: btree (actor_ref, created_at DESC) WHERE (actor_ref IS NOT NULL)
- index `audit_logs_created_idx`: btree (created_at DESC)
- index `audit_logs_entity_idx`: btree (entity_type, entity_id, created_at DESC)
- index `audit_logs_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `audit_logs_actor_type_chk`: CHECK ((actor_type = ANY (ARRAY['staff'::text, 'customer'::text, 'system'::text])))
- grant `booking`: INSERT, SELECT

### `booking.countries` (table, 32 kB)
```
iso2 character(2) NN
name text NN
active boolean NN
```
- owner `bk_owner`
- index `countries_pkey` PRIMARY KEY: UNIQUE btree (iso2)
- check `countries_iso2_chk`: CHECK ((iso2 ~ '^[A-Z]{2}$'::text))
- grant `booking`: SELECT

### `booking.customer_otps` (table, 24 kB)
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
- owner `bk_owner`
- index `customer_otps_customer_idx`: btree (customer_id, created_at DESC)
- index `customer_otps_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `customer_otps_attempts_chk`: CHECK ((attempts >= 0))
- check `customer_otps_channel_chk`: CHECK ((channel = ANY (ARRAY['email'::text, 'sms'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.customer_sessions` (table, 32 kB)
```
id uuid NN
customer_id uuid NN
refresh_token_hash text NN
expires_at timestamp with time zone NN
revoked_at timestamp with time zone
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `customer_sessions_customer_idx`: btree (customer_id)
- index `customer_sessions_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `customer_sessions_token_uq`: UNIQUE btree (refresh_token_hash)
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.customers` (table, ~1 rows, 104 kB)
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
- owner `bk_owner`
- index `customers_code_uq`: UNIQUE btree (code)
- index `customers_email_lookup_idx`: btree (lower(email)) WHERE ((email IS NOT NULL) AND (deleted_at IS NULL))
- index `customers_email_verified_uq`: UNIQUE btree (lower(email)) WHERE ((email IS NOT NULL) AND (deleted_at IS NULL) AND verified)
- index `customers_merge_review_idx`: btree (created_at DESC) WHERE (needs_merge_review AND (deleted_at IS NULL))
- index `customers_phone_lookup_idx`: btree (phone) WHERE ((phone IS NOT NULL) AND (deleted_at IS NULL))
- index `customers_phone_verified_uq`: UNIQUE btree (phone) WHERE ((phone IS NOT NULL) AND (deleted_at IS NULL) AND verified)
- index `customers_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `customers_contact_chk`: CHECK (((email IS NOT NULL) OR (phone IS NOT NULL)))
- check `customers_source_chk`: CHECK ((source = ANY (ARRAY['manual'::text, 'otp'::text, 'tripplanner_lead'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `customers_set_updated_at`: BEFORE UPDATE ON booking.customers FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.fx_rates` (table, 48 kB)
```
id uuid NN
currency character(3) NN
rate_per_usd numeric(18,8) NN
buffer_pct numeric(5,4) NN
as_of date NN
source text NN
created_by text
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `fx_rates_currency_as_of_uq`: UNIQUE btree (currency, as_of)
- index `fx_rates_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `fx_rates_buffer_chk`: CHECK (((buffer_pct >= (0)::numeric) AND (buffer_pct < (1)::numeric)))
- check `fx_rates_currency_chk`: CHECK (((currency ~ '^[A-Z]{3}$'::text) AND (currency <> 'USD'::bpchar)))
- check `fx_rates_rate_chk`: CHECK ((rate_per_usd > (0)::numeric))
- check `fx_rates_source_chk`: CHECK ((length(btrim(source)) > 0))
- grant `booking`: INSERT, SELECT

### `booking.hotel_room_types` (table, 48 kB)
```
id uuid NN
hotel_id uuid NN
name text NN
max_occupancy smallint
bed_types text[] NN
internal_notes text
status text NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `hotel_room_types_name_uq`: UNIQUE btree (hotel_id, lower(btrim(name)))
- index `hotel_room_types_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `hotel_room_types_beds_chk`: CHECK ((cardinality(bed_types) <= 10))
- check `hotel_room_types_name_chk`: CHECK (((length(btrim(name)) >= 1) AND (length(btrim(name)) <= 120)))
- check `hotel_room_types_occupancy_chk`: CHECK (((max_occupancy IS NULL) OR ((max_occupancy >= 1) AND (max_occupancy <= 20))))
- check `hotel_room_types_status_chk`: CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `hotel_room_types_set_updated_at`: BEFORE UPDATE ON booking.hotel_room_types FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.hotels` (table, 136 kB)
```
id uuid NN
code text NN
supplier_id uuid NN
name text NN
hotel_style text
star_rating smallint
address text
destination_id uuid
country_code character(2)
latitude numeric(9,6)
longitude numeric(9,6)
check_in_time time without time zone
check_out_time time without time zone
amenities text[] NN
links jsonb NN
internal_notes text
status text NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `hotels_code_uq`: UNIQUE btree (code)
- index `hotels_country_idx`: btree (country_code)
- index `hotels_destination_idx`: btree (destination_id) WHERE (destination_id IS NOT NULL)
- index `hotels_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `hotels_status_idx`: btree (status)
- index `hotels_supplier_idx`: btree (supplier_id)
- index `hotels_supplier_name_place_uq`: UNIQUE btree (supplier_id, lower(btrim(name)), COALESCE((destination_id)::text, '-'::text))
- index `hotels_updated_idx`: btree (updated_at DESC)
- check `hotels_amenities_chk`: CHECK ((cardinality(amenities) <= 50))
- check `hotels_geo_chk`: CHECK ((((latitude IS NULL) = (longitude IS NULL)) AND ((latitude IS NULL) OR ((latitude >= ('-90'::integer)::numeric) AND (latitude <= (90)::numeric))) AND ((longitude IS NULL) OR ((longitude >= ('-180'::integer)::numeric) AND (longitude <= (180)::numeric)))))
- check `hotels_links_chk`: CHECK (((jsonb_typeof(links) = 'array'::text) AND (jsonb_array_length(links) <= 10)))
- check `hotels_name_chk`: CHECK (((length(btrim(name)) >= 1) AND (length(btrim(name)) <= 200)))
- check `hotels_star_chk`: CHECK (((star_rating IS NULL) OR ((star_rating >= 1) AND (star_rating <= 5))))
- check `hotels_status_chk`: CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))
- check `hotels_style_chk`: CHECK (((hotel_style IS NULL) OR ((length(hotel_style) >= 1) AND (length(hotel_style) <= 60))))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `hotels_set_updated_at`: BEFORE UPDATE ON booking.hotels FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.inbox_cursor` (table, ~1 rows, 64 kB)
```
source text NN
contract text NN
safe_id bigint NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `inbox_cursor_pk` PRIMARY KEY: UNIQUE btree (source, contract)
- check `inbox_cursor_safe_id_chk`: CHECK ((safe_id >= 0))
- check `inbox_cursor_source_chk`: CHECK ((source = ANY (ARRAY['tripplanner'::text, 'cis'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `inbox_cursor_set_updated_at`: BEFORE UPDATE ON booking.inbox_cursor FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.inbox_events` (table, ~5 rows, 128 kB)
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
redacted_at timestamp with time zone
```
- owner `bk_owner`
- index `inbox_events_key_uq`: UNIQUE btree (source, contract, idempotency_key)
- index `inbox_events_pending_idx`: btree (received_at) WHERE (processed_at IS NULL)
- index `inbox_events_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `inbox_events_redact_due_idx`: btree (received_at, id) WHERE (redacted_at IS NULL)
- index `inbox_events_status_idx`: btree (status, received_at DESC)
- check `inbox_events_source_chk`: CHECK ((source = ANY (ARRAY['tripplanner'::text, 'cis'::text])))
- check `inbox_events_status_chk`: CHECK ((status = ANY (ARRAY['received'::text, 'processed'::text, 'parked'::text, 'failed'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.job` (table, ~5869 rows, 2.8 MB)
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
cancel_requested boolean NN
progress jsonb NN
cost_usd numeric(12,6) NN
parent_job_id uuid
```
- owner `bk_owner`
- index `job_active_pull_uq`: UNIQUE btree (kind) WHERE ((kind = 'bk_inquiry_pull'::text) AND (status = ANY (ARRAY['queued'::text, 'running'::text])))
- index `job_finished_idx`: btree (finished_at, id) WHERE (finished_at IS NOT NULL)
- index `job_idempotency_key_uq`: UNIQUE btree (idempotency_key) WHERE (idempotency_key IS NOT NULL)
- index `job_kind_created_idx`: btree (kind, created_at DESC)
- index `job_parent_idx`: btree (parent_job_id) WHERE (parent_job_id IS NOT NULL)
- index `job_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `job_queued_due_idx`: btree (run_after, created_at) WHERE (status = 'queued'::text)
- index `job_running_idx`: btree (kind, locked_until) WHERE (status = 'running'::text)
- check `job_attempts_chk`: CHECK (((attempt >= 0) AND (max_attempts >= 1)))
- check `job_kind_chk`: CHECK ((kind ~ '^bk_[a-z0-9_]+$'::text))
- check `job_lease_chk`: CHECK (((status <> 'running'::text) OR ((locked_by IS NOT NULL) AND (locked_until IS NOT NULL))))
- check `job_status_chk`: CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text, 'cancelled'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `job_set_updated_at`: BEFORE UPDATE ON booking.job FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.media_files` (table, 24 kB)
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
- owner `bk_owner`
- index `media_files_object_uq`: UNIQUE btree (s3_bucket, s3_key)
- index `media_files_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `media_files_bytes_chk`: CHECK (((bytes IS NULL) OR (bytes >= 0)))
- check `media_files_dims_chk`: CHECK ((((width IS NULL) OR (width > 0)) AND ((height IS NULL) OR (height > 0))))
- check `media_files_sha256_chk`: CHECK (((sha256 IS NULL) OR (sha256 ~ '^[0-9a-f]{64}$'::text)))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.notification_reads` (table, 24 kB)
```
notification_id uuid NN
cis_user_id text NN
read_at timestamp with time zone NN
```
- owner `bk_owner`
- index `notification_reads_pk` PRIMARY KEY: UNIQUE btree (notification_id, cis_user_id)
- index `notification_reads_staff_idx`: btree (cis_user_id, read_at DESC)
- grant `booking`: DELETE, INSERT, SELECT

### `booking.notifications` (table, ~1 rows, 64 kB)
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
- owner `bk_owner`
- index `notifications_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `notifications_staff_feed_idx`: btree (recipient_ref, created_at DESC) WHERE (recipient_type = 'staff'::text)
- index `notifications_unread_idx`: btree (recipient_type, recipient_id, created_at DESC) WHERE (read_at IS NULL)
- check `notifications_customer_recipient_chk`: CHECK (((recipient_type <> 'customer'::text) OR (recipient_id IS NOT NULL)))
- check `notifications_recipient_type_chk`: CHECK ((recipient_type = ANY (ARRAY['customer'::text, 'staff'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.policy_approvals` (table, 64 kB)
```
id uuid NN
entity_type text NN
pricing_rule_id uuid
fx_rate_id uuid
approved_by text NN
approved_at timestamp with time zone NN
note text
```
- owner `bk_owner`
- index `policy_approvals_fx_rate_uq`: UNIQUE btree (fx_rate_id)
- index `policy_approvals_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `policy_approvals_pricing_rule_uq`: UNIQUE btree (pricing_rule_id)
- check `policy_approvals_approved_by_chk`: CHECK ((length(btrim(approved_by)) > 0))
- check `policy_approvals_entity_chk`: CHECK ((((entity_type = 'pricing_rule'::text) AND (pricing_rule_id IS NOT NULL) AND (fx_rate_id IS NULL)) OR ((entity_type = 'fx_rate'::text) AND (fx_rate_id IS NOT NULL) AND (pricing_rule_id IS NULL))))
- grant `booking`: INSERT, SELECT
- trigger `policy_approvals_maker_checker`: BEFORE INSERT ON booking.policy_approvals FOR EACH ROW EXECUTE FUNCTION booking.policy_approval_maker_checker()

### `booking.pricing_rules` (table, 48 kB)
```
id uuid NN
channel text NN
target_margin numeric(5,4) NN
floor_margin numeric(5,4) NN
peak_uplift_pts numeric(5,4) NN
card_fee_pct numeric(5,4) NN
valid_from date NN
note text
created_by text
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `pricing_rules_channel_valid_from_uq`: UNIQUE btree (channel, valid_from)
- index `pricing_rules_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `pricing_rules_channel_chk`: CHECK ((channel = ANY (ARRAY['b2c_tailor_made'::text, 'fixed_departure'::text, 'b2b'::text])))
- check `pricing_rules_divisor_chk`: CHECK ((((target_margin + peak_uplift_pts) + card_fee_pct) < (1)::numeric))
- check `pricing_rules_ratios_chk`: CHECK (((target_margin >= (0)::numeric) AND (target_margin < (1)::numeric) AND (floor_margin >= (0)::numeric) AND (floor_margin <= target_margin) AND (peak_uplift_pts >= (0)::numeric) AND (peak_uplift_pts < (1)::numeric) AND (card_fee_pct >= (0)::numeric) AND (card_fee_pct < (1)::numeric)))
- grant `booking`: INSERT, SELECT

### `booking.services` (table, 152 kB)
```
id uuid NN
code text NN
supplier_id uuid NN
service_type text NN
title text NN
unit text NN
destination_id uuid
country_code character(2)
source_system text
source_id text
max_group_size smallint
duration_minutes integer
inclusions text[] NN
internal_notes text
status text NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `services_code_uq`: UNIQUE btree (code)
- index `services_country_idx`: btree (country_code)
- index `services_destination_idx`: btree (destination_id) WHERE (destination_id IS NOT NULL)
- index `services_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `services_status_idx`: btree (status)
- index `services_supplier_idx`: btree (supplier_id)
- index `services_supplier_title_place_uq`: UNIQUE btree (supplier_id, service_type, lower(btrim(title)), COALESCE((destination_id)::text, '-'::text))
- index `services_type_idx`: btree (service_type)
- index `services_updated_idx`: btree (updated_at DESC)
- check `services_duration_chk`: CHECK (((duration_minutes IS NULL) OR ((duration_minutes >= 1) AND (duration_minutes <= 43200))))
- check `services_group_chk`: CHECK (((max_group_size IS NULL) OR ((max_group_size >= 1) AND (max_group_size <= 999))))
- check `services_inclusions_chk`: CHECK ((cardinality(inclusions) <= 50))
- check `services_source_chk`: CHECK ((((source_system IS NULL) AND (source_id IS NULL)) OR ((source_system = 'cis'::text) AND (source_id IS NOT NULL) AND ((length(source_id) >= 1) AND (length(source_id) <= 120)))))
- check `services_status_chk`: CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))
- check `services_title_chk`: CHECK (((length(btrim(title)) >= 1) AND (length(btrim(title)) <= 200)))
- check `services_type_chk`: CHECK ((service_type = ANY (ARRAY['activity'::text, 'transfer'::text, 'guide'::text, 'entrance'::text, 'meal'::text])))
- check `services_unit_chk`: CHECK ((unit = ANY (ARRAY['person'::text, 'group'::text, 'vehicle'::text, 'day'::text])))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `services_set_updated_at`: BEFORE UPDATE ON booking.services FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.settings` (table, 32 kB)
```
key text NN
value jsonb NN
description text
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `settings_pkey` PRIMARY KEY: UNIQUE btree (key)
- check `settings_key_chk`: CHECK ((key ~ '^[a-z][a-z0-9_]{0,62}$'::text))
- grant `booking`: SELECT

### `booking.staff_assignments` (table, 64 kB)
```
id uuid NN
trip_case_id uuid NN
staff_user_id text NN
role text NN
assigned_by text
assigned_at timestamp with time zone NN
unassigned_at timestamp with time zone
```
- owner `bk_owner`
- index `staff_assignments_open_uq`: UNIQUE btree (trip_case_id, role) WHERE (unassigned_at IS NULL)
- index `staff_assignments_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `staff_assignments_staff_open_idx`: btree (staff_user_id, assigned_at DESC) WHERE (unassigned_at IS NULL)
- check `staff_assignments_period_chk`: CHECK (((unassigned_at IS NULL) OR (unassigned_at >= assigned_at)))
- check `staff_assignments_role_chk`: CHECK ((role = ANY (ARRAY['sales'::text, 'contracting'::text, 'ops'::text, 'guide'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.staff_users` (table, ~3 rows, 64 kB)
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
cognito_iss text
cognito_sub text
```
- owner `bk_owner`
- index `staff_users_active_idx`: btree (active, role)
- index `staff_users_cognito_identity_key`: UNIQUE btree (cognito_iss, cognito_sub)
- index `staff_users_pkey` PRIMARY KEY: UNIQUE btree (cis_user_id)
- check `staff_users_cognito_key_chk`: CHECK ((("left"(cis_user_id, 4) <> 'cog:'::text) OR ((cognito_sub IS NOT NULL) AND (cognito_sub = substr(cis_user_id, 5)))))
- check `staff_users_cognito_pair_chk`: CHECK ((((cognito_iss IS NULL) AND (cognito_sub IS NULL)) OR ((cognito_iss IS NOT NULL) AND (cognito_sub IS NOT NULL) AND (cognito_iss ~~ 'https://%'::text) AND ((length(cognito_sub) >= 1) AND (length(cognito_sub) <= 128)))))
- check `staff_users_id_chk`: CHECK (((length(cis_user_id) >= 1) AND (length(cis_user_id) <= 128)))
- check `staff_users_role_chk`: CHECK ((role = ANY (ARRAY['admin'::text, 'sales'::text, 'contracting'::text, 'content_creator'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `staff_users_set_updated_at`: BEFORE UPDATE ON booking.staff_users FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.supplier_contracts` (table, 64 kB)
```
id uuid NN
supplier_id uuid NN
title text NN
reference text
valid_from date NN
valid_to date
currency character(3) NN
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
- owner `bk_owner`
- index `supplier_contracts_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `supplier_contracts_published_idx`: btree (supplier_id, valid_to) WHERE (status = 'published'::text)
- index `supplier_contracts_supplier_idx`: btree (supplier_id, valid_from DESC)
- check `supplier_contracts_currency_chk`: CHECK ((currency ~ '^[A-Z]{3}$'::text))
- check `supplier_contracts_expired_chk`: CHECK (((status = 'expired'::text) = ((expired_by IS NOT NULL) AND (expired_at IS NOT NULL))))
- check `supplier_contracts_maker_checker_chk`: CHECK (((published_by IS NULL) OR (published_by <> COALESCE(updated_by, created_by))))
- check `supplier_contracts_published_chk`: CHECK ((((status = 'draft'::text) AND (published_by IS NULL) AND (published_at IS NULL)) OR ((status = ANY (ARRAY['published'::text, 'expired'::text])) AND (published_by IS NOT NULL) AND (published_at IS NOT NULL))))
- check `supplier_contracts_status_chk`: CHECK ((status = ANY (ARRAY['draft'::text, 'published'::text, 'expired'::text])))
- check `supplier_contracts_title_chk`: CHECK (((length(btrim(title)) >= 1) AND (length(btrim(title)) <= 200)))
- check `supplier_contracts_validity_chk`: CHECK (((valid_to IS NULL) OR (valid_to >= valid_from)))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `supplier_contracts_lock`: BEFORE UPDATE ON booking.supplier_contracts FOR EACH ROW EXECUTE FUNCTION booking.supplier_contract_lock()
- trigger `supplier_contracts_rates_fit`: BEFORE UPDATE OF currency, valid_from, valid_to ON booking.supplier_contracts FOR EACH ROW EXECUTE FUNCTION booking.supplier_contract_rates_fit()
- trigger `supplier_contracts_set_updated_at`: BEFORE UPDATE ON booking.supplier_contracts FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.supplier_rates` (table, 80 kB)
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
net_amount numeric(16,2) NN
currency character(3) NN
notes text
created_by text NN
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `supplier_rates_contract_idx`: btree (supplier_contract_id)
- index `supplier_rates_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `supplier_rates_room_type_idx`: btree (hotel_room_type_id, valid_from DESC) WHERE (hotel_room_type_id IS NOT NULL)
- index `supplier_rates_service_idx`: btree (service_id, valid_from DESC) WHERE (service_id IS NOT NULL)
- check `supplier_rates_amount_chk`: CHECK ((net_amount >= (0)::numeric))
- check `supplier_rates_currency_chk`: CHECK ((currency ~ '^[A-Z]{3}$'::text))
- check `supplier_rates_meal_plan_chk`: CHECK (((meal_plan IS NULL) OR ((hotel_room_type_id IS NOT NULL) AND (meal_plan = ANY (ARRAY['RO'::text, 'BB'::text, 'HB'::text, 'FB'::text, 'AI'::text])))))
- check `supplier_rates_pax_chk`: CHECK ((((pax_min IS NULL) OR ((pax_min >= 1) AND (pax_min <= 999))) AND ((pax_max IS NULL) OR ((pax_max >= 1) AND (pax_max <= 999))) AND ((pax_min IS NULL) OR (pax_max IS NULL) OR (pax_max >= pax_min))))
- check `supplier_rates_season_chk`: CHECK (((season IS NULL) OR ((length(season) >= 1) AND (length(season) <= 80))))
- check `supplier_rates_target_chk`: CHECK ((num_nonnulls(hotel_room_type_id, service_id) = 1))
- check `supplier_rates_unit_chk`: CHECK (((unit = ANY (ARRAY['room_night'::text, 'person'::text, 'group'::text, 'vehicle'::text, 'day'::text])) AND ((hotel_room_type_id IS NOT NULL) = (unit = 'room_night'::text))))
- check `supplier_rates_validity_chk`: CHECK (((valid_to IS NULL) OR (valid_to >= valid_from)))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `supplier_rates_guard`: BEFORE INSERT OR DELETE OR UPDATE ON booking.supplier_rates FOR EACH ROW EXECUTE FUNCTION booking.supplier_rate_guard()
- trigger `supplier_rates_set_updated_at`: BEFORE UPDATE ON booking.supplier_rates FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.suppliers` (table, 144 kB)
```
id uuid NN
code text NN
company_name text NN
categories text[] NN
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
country_code character(2)
status text NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `suppliers_categories_idx`: gin (categories)
- index `suppliers_code_uq`: UNIQUE btree (code)
- index `suppliers_country_idx`: btree (country_code)
- index `suppliers_destination_idx`: btree (destination_id) WHERE (destination_id IS NOT NULL)
- index `suppliers_name_country_uq`: UNIQUE btree (lower(btrim(company_name)), COALESCE(country_code, '--'::bpchar))
- index `suppliers_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `suppliers_status_idx`: btree (status)
- index `suppliers_updated_idx`: btree (updated_at DESC)
- check `suppliers_categories_chk`: CHECK ((((cardinality(categories) >= 1) AND (cardinality(categories) <= 6)) AND (categories <@ ARRAY['hotel'::text, 'transport'::text, 'guide'::text, 'entrance'::text, 'activity'::text, 'meal'::text])))
- check `suppliers_email_chk`: CHECK (((contact_email IS NULL) OR (contact_email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'::text)))
- check `suppliers_name_chk`: CHECK (((length(btrim(company_name)) >= 1) AND (length(btrim(company_name)) <= 200)))
- check `suppliers_status_chk`: CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))
- check `suppliers_website_chk`: CHECK (((website IS NULL) OR (website ~* '^https?://[^\s]+$'::text)))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `suppliers_set_updated_at`: BEFORE UPDATE ON booking.suppliers FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.trip_case_countries` (table, 40 kB)
```
trip_case_id uuid NN
country_code character(2) NN
position smallint NN
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `trip_case_countries_country_idx`: btree (country_code)
- index `trip_case_countries_pk` PRIMARY KEY: UNIQUE btree (trip_case_id, country_code)
- check `trip_case_countries_position_chk`: CHECK (("position" >= 1))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.trip_case_legs` (table, ~8 rows, 64 kB)
```
id uuid NN
trip_case_id uuid NN
position smallint NN
source_tour_id text NN
day_from smallint NN
day_to smallint NN
created_at timestamp with time zone NN
source_system text
source_id text
```
- owner `bk_owner`
- index `trip_case_legs_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_case_legs_position_uq`: UNIQUE btree (trip_case_id, "position")
- index `trip_case_legs_tour_key_idx`: btree (source_system, source_id)
- check `trip_case_legs_position_chk`: CHECK (("position" >= 1))
- check `trip_case_legs_tour_key_chk`: CHECK ((((source_system IS NULL) AND (source_id IS NULL)) OR COALESCE(((source_system = 'cis'::text) AND ((length(btrim(source_id)) >= 1) AND (length(btrim(source_id)) <= 128))), false)))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.trip_case_status_history` (table, ~1 rows, 64 kB)
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
- owner `bk_owner`
- index `trip_case_status_history_case_idx`: btree (trip_case_id, changed_at)
- index `trip_case_status_history_case_seq_idx`: btree (trip_case_id, seq)
- index `trip_case_status_history_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `trip_case_status_history_from_chk`: CHECK (((from_status IS NULL) OR (from_status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text]))))
- check `trip_case_status_history_to_chk`: CHECK ((to_status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text])))
- grant `booking`: INSERT, SELECT

### `booking.trip_case_status_transitions` (table, 32 kB)
```
from_status text NN
to_status text NN
```
- owner `bk_owner`
- index `trip_case_status_transitions_pk` PRIMARY KEY: UNIQUE btree (from_status, to_status)
- check `trip_case_status_transitions_distinct_chk`: CHECK ((from_status <> to_status))
- check `trip_case_status_transitions_from_chk`: CHECK ((from_status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text])))
- check `trip_case_status_transitions_to_chk`: CHECK ((to_status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text])))
- grant `booking`: SELECT

### `booking.trip_case_version_itinerary` (table, ~4 rows, 80 kB)
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
- owner `bk_owner`
- index `trip_case_version_itinerary_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_case_version_itinerary_position_uq`: UNIQUE btree (trip_case_version_id, "position")
- index `trip_case_version_itinerary_room_type_idx`: btree (hotel_room_type_id) WHERE (hotel_room_type_id IS NOT NULL)
- index `trip_case_version_itinerary_service_idx`: btree (service_id) WHERE (service_id IS NOT NULL)
- check `trip_case_version_itinerary_days_chk`: CHECK (((day_from >= 1) AND (day_to >= day_from)))
- check `trip_case_version_itinerary_position_chk`: CHECK (("position" >= 1))
- check `trip_case_version_itinerary_supply_chk`: CHECK ((num_nonnulls(hotel_room_type_id, service_id) <= 1))
- check `trip_case_version_itinerary_title_chk`: CHECK (((length(title) >= 1) AND (length(title) <= 500)))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `trip_case_version_itinerary_lock`: BEFORE INSERT OR DELETE OR UPDATE ON booking.trip_case_version_itinerary FOR EACH ROW EXECUTE FUNCTION booking.trip_case_version_item_lock()
- trigger `trip_case_version_itinerary_sent_lock`: BEFORE INSERT OR DELETE OR UPDATE ON booking.trip_case_version_itinerary FOR EACH ROW EXECUTE FUNCTION booking.trip_case_version_item_sent_lock()
- trigger `trip_case_version_itinerary_set_updated_at`: BEFORE UPDATE ON booking.trip_case_version_itinerary FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.trip_case_versions` (table, 80 kB)
```
id uuid NN
trip_case_id uuid NN
version_number smallint NN
notes text
total_price numeric(12,2)
currency character(3)
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
fx_rate_locked numeric(18,8)
fx_as_of date
sent_by text
approved_by text
approval_note text
updated_by text
deleted_at timestamp with time zone
```
- owner `bk_owner`
- index `trip_case_versions_approved_uq`: UNIQUE btree (trip_case_id) WHERE is_approved
- index `trip_case_versions_number_uq`: UNIQUE btree (trip_case_id, version_number)
- index `trip_case_versions_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_case_versions_updated_idx`: btree (updated_at DESC) WHERE (deleted_at IS NULL)
- check `trip_case_versions_approved_chk`: CHECK (((NOT is_approved) OR (approved_at IS NOT NULL)))
- check `trip_case_versions_channel_chk`: CHECK (((channel IS NULL) OR (channel = ANY (ARRAY['b2c_tailor_made'::text, 'fixed_departure'::text, 'b2b'::text]))))
- check `trip_case_versions_currency_chk`: CHECK (((currency IS NULL) OR (currency ~ '^[A-Z]{3}$'::text)))
- check `trip_case_versions_deleted_chk`: CHECK (((deleted_at IS NULL) OR ((NOT is_sent_to_customer) AND (NOT is_approved))))
- check `trip_case_versions_fx_chk`: CHECK (((fx_rate_locked IS NULL) OR (fx_rate_locked > (0)::numeric)))
- check `trip_case_versions_number_chk`: CHECK ((version_number >= 1))
- check `trip_case_versions_price_chk`: CHECK (((total_price IS NULL) OR (total_price >= (0)::numeric)))
- check `trip_case_versions_sent_chk`: CHECK (((NOT is_sent_to_customer) OR (sent_at IS NOT NULL)))
- check `trip_case_versions_title_chk`: CHECK (((title IS NULL) OR ((length(title) >= 1) AND (length(title) <= 200))))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `trip_case_versions_lock`: BEFORE DELETE OR UPDATE ON booking.trip_case_versions FOR EACH ROW EXECUTE FUNCTION booking.trip_case_version_lock()
- trigger `trip_case_versions_sent_lock`: BEFORE DELETE OR UPDATE ON booking.trip_case_versions FOR EACH ROW EXECUTE FUNCTION booking.trip_case_version_sent_lock()
- trigger `trip_case_versions_set_updated_at`: BEFORE UPDATE ON booking.trip_case_versions FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.trip_cases` (table, ~1 rows, 160 kB)
```
id uuid NN
code text NN
customer_id uuid NN
status text NN
trip_style text
start_date date
end_date date
pax smallint
currency character(3)
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
- owner `bk_owner`
- index `trip_cases_code_uq`: UNIQUE btree (code)
- index `trip_cases_customer_idx`: btree (customer_id, created_at DESC)
- index `trip_cases_idempotency_key_uq`: UNIQUE btree (idempotency_key)
- index `trip_cases_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_cases_source_idx`: btree (source_system, source_id)
- index `trip_cases_status_idx`: btree (status, created_at DESC) WHERE (deleted_at IS NULL)
- index `trip_cases_updated_idx`: btree (updated_at DESC) WHERE (deleted_at IS NULL)
- check `trip_cases_currency_chk`: CHECK (((currency IS NULL) OR (currency ~ '^[A-Z]{3}$'::text)))
- check `trip_cases_dates_chk`: CHECK (((start_date IS NULL) OR (end_date IS NULL) OR (start_date <= end_date)))
- check `trip_cases_pax_chk`: CHECK (((pax IS NULL) OR (pax > 0)))
- check `trip_cases_pax_split_chk`: CHECK ((((pax_adults IS NULL) OR (pax_adults >= 1)) AND ((pax_children IS NULL) OR ((pax_children >= 0) AND (pax_adults IS NOT NULL))) AND ((pax_adults IS NULL) OR (pax = (pax_adults + COALESCE((pax_children)::integer, 0))))))
- check `trip_cases_source_system_chk`: CHECK ((source_system = ANY (ARRAY['cis'::text, 'tripplanner'::text, 'manual'::text])))
- check `trip_cases_status_chk`: CHECK ((status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `trip_cases_check_transition`: BEFORE UPDATE OF status ON booking.trip_cases FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.trip_case_check_transition()
- trigger `trip_cases_record_status_insert`: AFTER INSERT ON booking.trip_cases FOR EACH ROW EXECUTE FUNCTION booking.trip_case_record_status()
- trigger `trip_cases_record_status_update`: AFTER UPDATE OF status ON booking.trip_cases FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.trip_case_record_status()
- trigger `trip_cases_set_updated_at`: BEFORE UPDATE ON booking.trip_cases FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.trip_plans` (table, 64 kB)
```
id uuid NN
source_system text NN
source_id text NN
sellable boolean NN
trip_style text
default_channel text
price_hint_amount numeric(12,2)
price_hint_currency character(3)
price_hint_basis text
commercial_notes text
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `trip_plans_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_plans_sellable_idx`: btree (source_id) WHERE sellable
- index `trip_plans_source_uq`: UNIQUE btree (source_system, source_id)
- check `trip_plans_channel_chk`: CHECK (((default_channel IS NULL) OR (default_channel = ANY (ARRAY['b2c_tailor_made'::text, 'fixed_departure'::text, 'b2b'::text]))))
- check `trip_plans_notes_chk`: CHECK (((commercial_notes IS NULL) OR (length(commercial_notes) <= 5000)))
- check `trip_plans_price_hint_chk`: CHECK ((((price_hint_amount IS NULL) AND (price_hint_currency IS NULL) AND (price_hint_basis IS NULL)) OR ((price_hint_amount IS NOT NULL) AND (price_hint_currency IS NOT NULL) AND (price_hint_basis IS NOT NULL) AND (price_hint_amount > (0)::numeric) AND (price_hint_currency ~ '^[A-Z]{3}$'::text) AND (price_hint_basis = ANY (ARRAY['per_person'::text, 'per_group'::text])))))
- check `trip_plans_source_id_chk`: CHECK (((length(btrim(source_id)) >= 1) AND (length(btrim(source_id)) <= 128)))
- check `trip_plans_source_system_chk`: CHECK ((source_system = 'cis'::text))
- check `trip_plans_trip_style_chk`: CHECK (((trip_style IS NULL) OR ((length(btrim(trip_style)) >= 1) AND (length(btrim(trip_style)) <= 60))))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `trip_plans_set_updated_at`: BEFORE UPDATE ON booking.trip_plans FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

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
- owner `bk_owner`
- grant `booking`: SELECT

### `booking.v_ops_case_status` (VIEW)
```
status text
n bigint
```
- owner `bk_owner`
- grant `booking`: SELECT
- grant `cis_app`: SELECT

### `booking.v_ops_funnel_daily` (VIEW)
```
day date
metric text
source_system text
n bigint
```
- owner `bk_owner`
- grant `booking`: SELECT
- grant `cis_app`: SELECT

### `booking.v_schema_versions` (VIEW)
```
version character varying(20)
description text
applied_at timestamp with time zone
```
- owner `bk_owner`
- grant `booking`: SELECT

### `booking.version_item_costs` (table, ~4 rows, 64 kB)
```
id uuid NN
version_item_id uuid NN
net_amount numeric(16,2) NN
net_currency character(3) NN
supplier_note text
entered_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
supplier_rate_id uuid
```
- owner `bk_owner`
- index `version_item_costs_item_idx`: btree (version_item_id)
- index `version_item_costs_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `version_item_costs_rate_idx`: btree (supplier_rate_id) WHERE (supplier_rate_id IS NOT NULL)
- check `version_item_costs_amount_chk`: CHECK ((net_amount >= (0)::numeric))
- check `version_item_costs_currency_chk`: CHECK ((net_currency ~ '^[A-Z]{3}$'::text))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `version_item_costs_lock`: BEFORE INSERT OR DELETE OR UPDATE ON booking.version_item_costs FOR EACH ROW EXECUTE FUNCTION booking.version_item_cost_lock()
- trigger `version_item_costs_set_updated_at`: BEFORE UPDATE ON booking.version_item_costs FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

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
- owner `catalog_owner`

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
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

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
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

### `catalog.v_graph_edge` (VIEW)
```
from_destination_id uuid
to_destination_id uuid
tour_count integer
source_ids text[]
tour_ids uuid[]
km double precision
build_id uuid
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

### `catalog.v_graph_node` (VIEW)
```
destination_id uuid
name text
country text
lat double precision
lng double precision
located_by text
precision text
source_ids text[]
tour_ids uuid[]
stop_count integer
activities text[]
intensity_min text
intensity_max text
season_months integer[]
build_id uuid
built_at timestamp with time zone
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

### `catalog.v_tour` (VIEW)
```
source_system text
source_id text
tour_id uuid
source_version smallint
sku text
slug text
title character varying(500)
subtitle character varying(500)
summary text
description text
highlights jsonb
country text
duration_raw text
duration_days integer
activities jsonb
inclusions text
exclusions text
best_time_to_go character varying(500)
group_size text
lifecycle_stage text
itinerary_text text
cover_photo_path text
photo_count bigint
published_at timestamp with time zone
updated_at timestamp with time zone
content_hash text
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

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
season_months integer[]
duration_hint text
text_extract text
place_card_id uuid
embedding vector(1536)
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

### `catalog.v_tour_day` (VIEW)
```
source_system text
source_id text
tour_id uuid
day_number integer
title text
body text
places text[]
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

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
places text[]
extracted_by text
is_transit_day boolean
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

### `catalog.v_tour_junction` (VIEW)
```
destination_a uuid
destination_b uuid
km double precision
cross_border boolean
build_id uuid
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

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
destination_ids uuid[]
countries text[]
activities text[]
build_id uuid
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

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
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

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
activity_types text[]
atom_count bigint
located_by text
precision text
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

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
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

## `geo` (12 objects)

### `geo.geocode_call` (table, 48 kB)
```
id bigint NN
called_at timestamp with time zone NN
provider text NN
requests integer NN
cost_usd numeric(10,6) NN
job_id uuid
```
- owner `cis_owner`
- index `geocode_call_called_at_idx`: btree (called_at)
- index `geocode_call_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.graph_build` (table, 48 kB)
```
build_id uuid NN
params jsonb NN
stats jsonb NN
is_current boolean NN
built_at timestamp with time zone NN
job_id uuid
```
- owner `cis_owner`
- index `graph_build_one_current_uq`: UNIQUE btree (is_current) WHERE is_current
- index `graph_build_pkey` PRIMARY KEY: UNIQUE btree (build_id)
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.graph_edge` (table, ~209 rows, 112 kB)
```
build_id uuid NN
from_destination_id uuid NN
to_destination_id uuid NN
tour_count integer NN
source_ids text[] NN
km numeric(8,1)
```
- owner `cis_owner`
- index `graph_edge_pkey` PRIMARY KEY: UNIQUE btree (build_id, from_destination_id, to_destination_id)
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.graph_node` (table, ~143 rows, 96 kB)
```
build_id uuid NN
destination_id uuid NN
name text NN
country text
lat double precision NN
lng double precision NN
source_ids text[] NN
stop_count integer NN
activities text[] NN
intensity_min text
intensity_max text
season_months integer[] NN
```
- owner `cis_owner`
- index `graph_node_pkey` PRIMARY KEY: UNIQUE btree (build_id, destination_id)
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.place_name` (table, ~573 rows, 248 kB)
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
- owner `cis_owner`
- index `place_name_due_idx`: btree (next_retry_at) WHERE (status = 'pending'::text)
- index `place_name_pkey` PRIMARY KEY: UNIQUE btree (name_norm, country_norm, locality_norm)
- check `place_name_status_check`: CHECK ((status = ANY (ARRAY['pending'::text, 'resolved'::text, 'unknown'::text, 'suspect'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.place_outlier` (table, 16 kB)
```
destination_id uuid NN
source_id text NN
day_index integer NN
km numeric(8,1) NN
observed_at timestamp with time zone NN
```
- owner `cis_owner`
- index `place_outlier_pkey` PRIMARY KEY: UNIQUE btree (destination_id, source_id, day_index)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_build` (table, ~27 rows, 88 kB)
```
source_id text NN
tour_id uuid NN
country text
days_hash text
components_hash text
rule_version integer NN
status text NN
counts jsonb NN
cost_usd numeric(10,6) NN
built_at timestamp with time zone
job_id uuid
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `tour_build_pkey` PRIMARY KEY: UNIQUE btree (source_id)
- check `tour_build_status_check`: CHECK ((status = ANY (ARRAY['pending'::text, 'ok'::text, 'partial'::text, 'failed'::text, 'retired'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_day` (table, ~392 rows, 264 kB)
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
places text[] NN
extracted_by text NN
is_transit_day boolean NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `tour_day_pkey` PRIMARY KEY: UNIQUE btree (source_id, day_index)
- index `tour_day_unlinked_anchor_idx`: btree (anchor_norm, anchor_country_norm, anchor_locality_norm) WHERE ((overnight_destination_id IS NULL) AND (anchor_norm IS NOT NULL))
- check `tour_day_extracted_by_check`: CHECK ((extracted_by = ANY (ARRAY['rule'::text, 'llm'::text, 'rule+llm'::text])))
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_junction` (table, ~2854 rows, 560 kB)
```
build_id uuid NN
destination_a uuid NN
destination_b uuid NN
km numeric(8,1) NN
cross_border boolean NN
```
- owner `cis_owner`
- index `tour_junction_pkey` PRIMARY KEY: UNIQUE btree (build_id, destination_a, destination_b)
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_leg` (table, ~1971 rows, 1.1 MB)
```
build_id uuid NN
source_id text NN
day_from integer NN
day_to integer NN
days integer NN
start_destination_id uuid NN
end_destination_id uuid NN
destination_ids uuid[] NN
countries text[] NN
activities text[] NN
```
- owner `cis_owner`
- index `tour_leg_countries_gin`: gin (countries)
- index `tour_leg_pkey` PRIMARY KEY: UNIQUE btree (build_id, source_id, day_from, day_to)
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_place` (table, ~967 rows, 16 MB)
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
season_months integer[] NN
duration_hint text NN
text_extract text NN
text_hash text NN
atom_ids text[] NN
created_at timestamp with time zone NN
embedding vector(1536)
```
- owner `cis_owner`
- index `tour_place_destination_idx`: btree (destination_id)
- index `tour_place_embedding_hnsw`: hnsw (embedding vector_cosine_ops)
- index `tour_place_pkey` PRIMARY KEY: UNIQUE btree (component_id)
- index `tour_place_source_idx`: btree (source_id, day_index)
- index `tour_place_unlinked_idx`: btree (name_norm, country_norm, locality_norm) WHERE (destination_id IS NULL)
- check `tour_place_activity_check`: CHECK ((activity = ANY (ARRAY['trekking'::text, 'cultural_heritage'::text, 'wildlife_nature'::text, 'water_activities'::text, 'culinary'::text, 'wellness_relaxation'::text, 'adventure_sport'::text, 'local_immersion'::text])))
- check `tour_place_duration_hint_check`: CHECK ((duration_hint = ANY (ARRAY['half_day'::text, 'full_day'::text, 'overnight'::text, 'multi_night'::text])))
- check `tour_place_intensity_level_check`: CHECK ((intensity_level = ANY (ARRAY['leisurely'::text, 'moderate'::text, 'active'::text, 'strenuous'::text])))
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_stop` (table, ~407 rows, 168 kB)
```
build_id uuid NN
source_id text NN
day_index integer NN
destination_id uuid NN
country text
source text NN
```
- owner `cis_owner`
- index `tour_stop_pkey` PRIMARY KEY: UNIQUE btree (build_id, source_id, day_index)
- check `tour_stop_source_check`: CHECK ((source = ANY (ARRAY['overnight'::text, 'component'::text])))
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

## `gold_aa_internal` (4 objects)

### `gold_aa_internal.content_exports` (table, 24 kB)
```
id uuid NN
tenant_id uuid NN
export_id uuid NN
format export_format_enum NN
filter_params jsonb
field_mapping jsonb
s3_path character varying(500)
signed_url text
total_tours integer
file_size_kb integer
status character varying(50) NN
expires_at timestamp with time zone
created_at timestamp with time zone NN
completed_at timestamp with time zone
```
- owner `cis_owner` · RLS on + FORCE
- index `content_exports_export_id_key`: UNIQUE btree (export_id)
- index `content_exports_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `content_exports_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `content_exports_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `gold_aa_internal.published_tours` (table, ~886 rows, 5.3 MB)
```
id uuid NN
tour_id uuid NN
generated_content_id uuid NN
tenant_id uuid NN
aa_name character varying(500) NN
aa_subtitle character varying(500)
aa_summary text
aa_description text
aa_highlights jsonb
aa_itineraries text
mobile_card_text character varying(80)
seo_title character varying(70)
seo_meta character varying(170)
seo_keywords_used jsonb
og_tags jsonb
quality_score numeric(5,2)
quality_score_id uuid
s3_gold_path character varying(500)
approved_by character varying(200)
published_at timestamp with time zone NN
content_embedding vector(1536)
master_status gold_aa_internal.master_status_enum NN
deleted_at timestamp with time zone
deleted_by text
```
- owner `cis_owner` · RLS on + FORCE
- index `idx_aa_internal_published_at`: btree (published_at DESC)
- index `idx_pt_embedding`: ivfflat (content_embedding vector_cosine_ops) WITH (lists='10')
- index `published_tours_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `published_tours_tour_id_key`: UNIQUE btree (tour_id)
- grant `aa_app_user`: SELECT
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- grant `tripplanner`: SELECT
- policy `aa_app_user_aa_master_read` (PERMISSIVE SELECT TO aa_app_user): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `catalog_owner_aa_master_read` (PERMISSIVE SELECT TO catalog_owner): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `published_tours_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `published_tours_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `gold_aa_internal.tenant_tour_versions` (table, ~48 rows, 616 kB)
```
id uuid NN
tenant_id uuid NN
published_tour_id uuid NN
version_number integer NN
parent_version_id uuid
rewritten_content jsonb NN
status text NN
quality_score numeric(4,2)
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
- owner `cis_owner` · RLS on
- index `idx_ttv_created`: btree (tenant_id, created_at DESC)
- index `idx_ttv_published_tour`: btree (published_tour_id)
- index `idx_ttv_status`: btree (tenant_id, status)
- index `idx_ttv_tenant_id`: btree (tenant_id)
- index `tenant_tour_versions_job_idx`: btree (job_id) WHERE (job_id IS NOT NULL)
- index `tenant_tour_versions_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `tenant_tour_versions_tenant_id_published_tour_id_version_nu_key`: UNIQUE btree (tenant_id, published_tour_id, version_number)
- check `tenant_tour_versions_edit_source_check`: CHECK ((edit_source = ANY (ARRAY['ai_generated'::text, 'tenant_edit'::text, 're_rewrite'::text])))
- check `tenant_tour_versions_qa_status_check`: CHECK ((qa_status = ANY (ARRAY['pending'::text, 'passed'::text, 'failed'::text, 'escalated'::text])))
- check `tenant_tour_versions_status_check`: CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, 'needs_review'::text, 'ai_generated'::text, 'failed'::text])))
- grant `aa_app_user`: INSERT, SELECT, UPDATE
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- policy `tenant_tour_versions_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`

### `gold_aa_internal.webhook_deliveries` (table, 24 kB)
```
id uuid NN
tenant_id uuid NN
tour_id uuid NN
webhook_url character varying(500) NN
event_type character varying(100) NN
delivery_id uuid NN
payload_s3_path character varying(500)
hmac_secret_ref character varying(200)
status webhook_status_enum NN
http_status smallint
attempt_count smallint NN
last_error text
created_at timestamp with time zone NN
next_retry_at timestamp with time zone
delivered_at timestamp with time zone
```
- owner `cis_owner` · RLS on + FORCE
- index `idx_aa_internal_webhook_status`: btree (status)
- index `webhook_deliveries_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- policy `webhook_deliveries_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `webhook_deliveries_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`

## `public` (1 objects)

### `public.checkpoint_migrations` (table, 24 kB)
```
v integer NN
```
- owner `aa_cis_admin`
- index `checkpoint_migrations_pkey` PRIMARY KEY: UNIQUE btree (v)

## `shared` (47 objects)

### `shared.acp_runs` (table, 40 kB)
```
id uuid NN
batch_id uuid NN
country text
tenant_id uuid NN
manifest_s3_key text
tour_count integer NN
quality_score_avg numeric(5,2)
status text NN
created_at timestamp with time zone NN
completed_at timestamp with time zone
```
- owner `cis_owner`
- index `acp_runs_batch_id_key`: UNIQUE btree (batch_id)
- index `acp_runs_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `idx_acp_runs_country`: btree (country)
- index `idx_acp_runs_status`: btree (status)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.admin_users` (table, ~10 rows, 80 kB)
```
id uuid NN
username character varying(100) NN
password_hash character varying(255)
role shared.admin_role NN
is_active boolean NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
email text
display_name text
cognito_iss text
cognito_sub text
last_login_at timestamp with time zone
is_owner boolean NN
```
- owner `cis_owner`
- index `admin_users_cognito_identity_key`: UNIQUE btree (cognito_iss, cognito_sub)
- index `admin_users_email_lower_key`: UNIQUE btree (lower(email))
- index `admin_users_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `admin_users_username_key`: UNIQUE btree (username)
- check `admin_users_cognito_pair_chk`: CHECK ((((cognito_iss IS NULL) AND (cognito_sub IS NULL)) OR ((cognito_iss IS NOT NULL) AND (cognito_sub IS NOT NULL) AND (cognito_iss ~~ 'https://%'::text) AND ((length(cognito_sub) >= 1) AND (length(cognito_sub) <= 128)))))
- check `admin_users_email_chk`: CHECK (((email IS NULL) OR ((email = lower(email)) AND (email ~ '^[^@[:space:]]+@adventure[.]asia$'::text)) OR ((email = 'e2e@e2e-mail.lumiguides.it.com'::text) AND (role = 'reviewer'::shared.admin_role) AND (NOT is_owner) AND (password_hash IS NULL))))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.alert_recipient` (table, 32 kB)
```
id uuid NN
email text NN
note text
status text NN
removed_reason text
subscription_arn text
created_at timestamp with time zone NN
created_by text NN
confirmed_at timestamp with time zone
removed_at timestamp with time zone
removed_by text
last_confirmation_sent_at timestamp with time zone
last_seen_state text
last_reconciled_at timestamp with time zone
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `alert_recipient_active_email_uq`: UNIQUE btree (email) WHERE (status <> 'removed'::text)
- index `alert_recipient_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `alert_recipient_status_idx`: btree (status, created_at DESC)
- check `alert_recipient_email_chk`: CHECK (((email = lower(email)) AND (length(email) <= 254) AND (email ~ '^[^@[:space:],;<>"]+@[^@[:space:],;<>"]+\.[^@[:space:],;<>"]+$'::text)))
- check `alert_recipient_note_chk`: CHECK (((note IS NULL) OR (length(note) <= 80)))
- check `alert_recipient_removed_chk`: CHECK ((((status = 'removed'::text) = (removed_at IS NOT NULL)) AND ((status = 'removed'::text) = (removed_reason IS NOT NULL)) AND ((removed_reason IS NULL) OR (removed_reason = ANY (ARRAY['admin'::text, 'unsubscribed'::text, 'expired'::text])))))
- check `alert_recipient_seen_chk`: CHECK (((last_seen_state IS NULL) OR (last_seen_state = ANY (ARRAY['confirmed'::text, 'pending'::text, 'missing'::text]))))
- check `alert_recipient_status_chk`: CHECK ((status = ANY (ARRAY['pending'::text, 'confirmed'::text, 'removed'::text])))
- grant `cis_app`: INSERT, SELECT, UPDATE

### `shared.cost_explorer_app_snapshot` (table, ~2448 rows, 696 kB)
```
id uuid NN
account_id text NN
app_tag text NN
service text NN
period_start date NN
period_end date NN
amount_usd numeric(14,4) NN
unit text NN
fetched_at timestamp with time zone NN
```
- owner `cis_owner`
- index `cost_explorer_app_snapshot_fetched_idx`: btree (fetched_at DESC)
- index `cost_explorer_app_snapshot_period_idx`: btree (period_start, app_tag, service, fetched_at DESC)
- index `cost_explorer_app_snapshot_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.cost_explorer_snapshot` (table, ~2163 rows, 2.5 MB)
```
id uuid NN
account_id text NN
service text NN
period_start date NN
period_end date NN
amount_usd numeric(14,4) NN
unit text NN
raw jsonb
fetched_at timestamp with time zone NN
```
- owner `cis_owner`
- index `cost_explorer_snapshot_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `idx_cost_explorer_account_period`: btree (account_id, period_start DESC)
- index `idx_cost_explorer_fetched`: btree (fetched_at DESC)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.decision_cache_hits_daily` (table, ~217 rows, 104 kB)
```
day date NN
stage text NN
question_key text NN
mode text NN
zone text NN
hits bigint NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `decision_cache_hits_daily_pkey` PRIMARY KEY: UNIQUE btree (day, stage, question_key, mode, zone)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.decision_log` (table, ~331400 rows, 360.7 MB)
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
probability numeric(6,5)
choice text
probabilities jsonb
threshold_version integer
model text
latency_ms integer
cost_usd numeric(12,8)
error text
outcome text
question_hash text
cached boolean NN
```
- owner `cis_owner`
- index `decision_log_cache_idx`: btree (subject_key, question_key, created_at DESC)
- index `decision_log_created_id_idx`: btree (created_at, id)
- index `decision_log_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `decision_log_question_created_cov_idx`: btree (question_key, created_at DESC) INCLUDE (zone, mode, cached, cost_usd, latency_ms, probability)
- index `decision_log_stage_created_cov_idx`: btree (stage, created_at DESC) INCLUDE (question_key, zone, mode, cached, cost_usd, latency_ms)
- index `decision_log_subject_idx`: btree (subject_key)
- check `decision_log_mode_check`: CHECK ((mode = ANY (ARRAY['off'::text, 'shadow'::text, 'enforce'::text])))
- check `decision_log_zone_check`: CHECK ((zone = ANY (ARRAY['accept'::text, 'grey'::text, 'reject'::text, 'error'::text, 'skipped'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.decision_question` (table, ~5 rows, 72 kB)
```
question_key text NN
stage text NN
kind text NN
instructions text NN
criteria jsonb
mode text NN
accept_floor numeric(5,4)
reject_ceiling numeric(5,4)
threshold_version integer NN
calibration_ref text
notes text
updated_at timestamp with time zone NN
updated_by text NN
question_hash text
```
- owner `cis_owner`
- index `decision_question_pkey` PRIMARY KEY: UNIQUE btree (question_key)
- check `decision_question_accept_floor_check`: CHECK (((accept_floor IS NULL) OR ((accept_floor >= (0)::numeric) AND (accept_floor <= (1)::numeric))))
- check `decision_question_enforce_needs_calibration`: CHECK (((mode <> 'enforce'::text) OR ((calibration_ref IS NOT NULL) AND ((accept_floor IS NOT NULL) OR (reject_ceiling IS NOT NULL)))))
- check `decision_question_floors_ordered`: CHECK (((accept_floor IS NULL) OR (reject_ceiling IS NULL) OR (reject_ceiling < accept_floor)))
- check `decision_question_kind_check`: CHECK ((kind = ANY (ARRAY['noul'::text, 'choice'::text, 'score'::text])))
- check `decision_question_mode_check`: CHECK ((mode = ANY (ARRAY['off'::text, 'shadow'::text, 'enforce'::text])))
- check `decision_question_reject_ceiling_check`: CHECK (((reject_ceiling IS NULL) OR ((reject_ceiling >= (0)::numeric) AND (reject_ceiling <= (1)::numeric))))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.destinations` (table, ~1469 rows, 752 kB)
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
- owner `cis_owner`
- index `destinations_lower_name_uidx`: UNIQUE btree (lower(name))
- index `destinations_name_country_uidx`: UNIQUE btree (name_norm, lower(btrim(country)), locality_norm) WHERE ((duplicate_of IS NULL) AND (name_norm IS NOT NULL))
- index `destinations_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `destinations_geo_precision_check`: CHECK (((geo_precision IS NULL) OR (geo_precision = ANY (ARRAY['point'::text, 'area'::text]))))
- check `destinations_geo_status_check`: CHECK ((geo_status = ANY (ARRAY['ok'::text, 'suspect'::text, 'manual'::text])))
- check `destinations_located_by_check`: CHECK ((located_by = ANY (ARRAY['mapbox'::text, 'llm'::text, 'geoapify'::text, 'manual'::text])))
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- grant `tripplanner`: SELECT

### `shared.dfs_balance_snapshot` (table, 288 kB)
```
id uuid NN
balance_usd numeric(14,4) NN
currency text
below_threshold boolean NN
threshold_usd numeric(14,4)
raw jsonb
fetched_at timestamp with time zone NN
```
- owner `cis_owner`
- index `dfs_balance_snapshot_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `idx_dfs_balance_fetched`: btree (fetched_at DESC)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.dfs_call_log` (table, ~2545 rows, 1 MB)
```
id uuid NN
tenant_id uuid
tour_id uuid
endpoint text NN
keyword text
location_code integer
cost_usd numeric(12,6)
cache_hit boolean NN
fetched_live boolean NN
keyword_count integer
meta jsonb
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `dfs_call_log_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `idx_dfs_call_log_created`: btree (created_at DESC)
- index `idx_dfs_call_log_endpoint`: btree (endpoint, created_at DESC)
- index `idx_dfs_call_log_live`: btree (fetched_live) WHERE fetched_live
- index `idx_dfs_call_log_tenant_created`: btree (tenant_id, created_at DESC)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.jev_credit_topup` (table, 48 kB)
```
id bigint NN
topped_up_on date NN
amount_usd numeric(10,2) NN
note text
created_by text
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `idx_jev_credit_topup_date`: btree (topped_up_on DESC)
- index `jev_credit_topup_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `jev_credit_topup_amount_usd_check`: CHECK ((amount_usd > (0)::numeric))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.jev_tenant_allowlist` (table, 32 kB)
```
tenant_id uuid NN
reason text NN
added_at timestamp with time zone NN
added_by text NN
```
- owner `cis_owner`
- index `jev_tenant_allowlist_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.job` (table, ~2735 rows, 10.8 MB)
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
cost_usd numeric(12,6) NN
error text
parent_job_id uuid
created_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
started_at timestamp with time zone
finished_at timestamp with time zone
```
- owner `cis_owner`
- index `job_finished_idx`: btree (finished_at, id) WHERE (finished_at IS NOT NULL)
- index `job_idempotency_key_uq`: UNIQUE btree (idempotency_key) WHERE (idempotency_key IS NOT NULL)
- index `job_kind_created_idx`: btree (kind, created_at DESC)
- index `job_parent_idx`: btree (parent_job_id) WHERE (parent_job_id IS NOT NULL)
- index `job_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `job_queued_due_idx`: btree (run_after, created_at) WHERE (status = 'queued'::text)
- index `job_running_idx`: btree (kind, locked_until) WHERE (status = 'running'::text)
- check `job_attempts_chk`: CHECK (((attempt >= 0) AND (max_attempts >= 1)))
- check `job_kind_chk`: CHECK ((kind ~ '^(?!bk_|tp_)[a-z][a-z0-9_]*$'::text))
- check `job_lease_chk`: CHECK (((status <> 'running'::text) OR ((locked_by IS NOT NULL) AND (locked_until IS NOT NULL))))
- check `job_status_check`: CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text, 'stopped_budget'::text, 'cancelled'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `job_set_updated_at`: BEFORE UPDATE ON shared.job FOR EACH ROW EXECUTE FUNCTION shared.job_set_updated_at()

### `shared.job_worker` (table, ~170 rows, 248 kB)
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
git_sha text
```
- owner `cis_owner`
- index `job_worker_last_seen_idx`: btree (last_seen_at DESC)
- index `job_worker_pkey` PRIMARY KEY: UNIQUE btree (worker_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.llm_call_daily` (table, 48 kB)
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
- owner `cis_owner`
- index `llm_call_daily_key`: UNIQUE btree (day, app, tenant_id, stage, role, model, provider, account, is_shadow) NULLS NOT DISTINCT
- index `llm_call_daily_tenant_day_idx`: btree (tenant_id, day)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.llm_call_log` (table, ~257439 rows, 132.7 MB)
```
id uuid NN
tenant_id uuid
stage text NN
role text NN
model text NN
tokens_in integer
tokens_out integer
cost_usd numeric(10,6)
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
- owner `cis_owner`
- index `idx_llm_call_log_account`: btree (account) WHERE (account IS NOT NULL)
- index `idx_llm_call_log_model_created`: btree (model, created_at DESC)
- index `idx_llm_call_log_piece`: btree (content_piece_id) WHERE (content_piece_id IS NOT NULL)
- index `idx_llm_call_log_stage_created`: btree (stage, created_at DESC)
- index `idx_llm_call_log_tenant_created`: btree (tenant_id, created_at DESC)
- index `llm_call_log_created_id_idx`: btree (created_at, id)
- index `llm_call_log_job_idx`: btree (job_id) WHERE (job_id IS NOT NULL)
- index `llm_call_log_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `llm_call_log_role_check`: CHECK ((role = ANY (ARRAY['writer'::text, 'judge'::text, 'validate'::text, 'embed'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- grant `tripplanner`: INSERT

### `shared.llm_model_catalog` (table, 32 kB)
```
model_key text NN
label text NN
vendor text NN
provider text NN
api_style text NN
bedrock_profile_ids jsonb NN
wire_model text
callable_via text[] NN
supports_temperature boolean NN
max_output_tokens integer
price_in_per_mtok numeric(10,4)
price_out_per_mtok numeric(10,4)
price_cache_read_per_mtok numeric(10,4)
price_cache_write_per_mtok numeric(10,4)
price_source text
enabled boolean NN
blocked_reason text
notes text
updated_at timestamp with time zone NN
updated_by text NN
```
- owner `cis_owner`
- index `llm_model_catalog_pkey` PRIMARY KEY: UNIQUE btree (model_key)
- check `llm_model_catalog_api_style_check`: CHECK ((api_style = ANY (ARRAY['anthropic_native'::text, 'converse'::text, 'openai_chat'::text, 'embed'::text, 'decide'::text])))
- check `llm_model_catalog_enabled_needs_price`: CHECK (((NOT enabled) OR ((price_in_per_mtok IS NOT NULL) AND (price_out_per_mtok IS NOT NULL))))
- check `llm_model_catalog_max_output_tokens_check`: CHECK (((max_output_tokens IS NULL) OR (max_output_tokens > 0)))
- check `llm_model_catalog_provider_check`: CHECK ((provider = ANY (ARRAY['bedrock'::text, 'openai'::text, 'typesafe'::text])))
- check `llm_model_catalog_vendor_check`: CHECK ((vendor = ANY (ARRAY['anthropic'::text, 'openai'::text, 'cohere'::text, 'typesafe'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- grant `tripplanner`: SELECT

### `shared.llm_role_config` (table, 32 kB)
```
stage text NN
role text NN
provider text NN
model_id text NN
account_route text
is_active boolean NN
updated_at timestamp with time zone NN
updated_by text NN
fallback_model_ids text[] NN
shadow_model_id text
shadow_sample_pct integer NN
```
- owner `cis_owner`
- index `llm_role_config_pkey` PRIMARY KEY: UNIQUE btree (stage)
- check `llm_role_config_account_route_check`: CHECK (((account_route = ANY (ARRAY['acc1'::text, 'acc3'::text])) OR (account_route IS NULL)))
- check `llm_role_config_provider_check`: CHECK ((provider = ANY (ARRAY['claude'::text, 'openai'::text, 'cohere'::text])))
- check `llm_role_config_role_check`: CHECK ((role = ANY (ARRAY['writer'::text, 'judge'::text, 'validate'::text, 'embed'::text])))
- check `llm_role_config_shadow_sample_pct_check`: CHECK (((shadow_sample_pct >= 0) AND (shadow_sample_pct <= 100)))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- grant `tripplanner`: SELECT

### `shared.llm_shadow_log` (table, ~5554 rows, 11.9 MB)
```
id bigint NN
created_at timestamp with time zone NN
stage text NN
primary_model text NN
shadow_model text NN
primary_output text
shadow_output text
shadow_error text
primary_cost_usd numeric(12,6)
shadow_cost_usd numeric(12,6)
shadow_latency_ms integer
request_sha256 text
```
- owner `cis_owner`
- index `llm_shadow_log_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `llm_shadow_log_stage_time`: btree (stage, created_at DESC)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.membership_plans` (table, 48 kB)
```
id uuid NN
plan_name text NN
tours_quota_monthly integer NN
api_calls_quota_monthly integer NN
price_usd_monthly numeric(10,2) NN
overage_rate_usd_per_tour numeric(8,4) NN
overage_rate_usd_per_1k_calls numeric(8,4) NN
is_active boolean NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `membership_plans_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `membership_plans_plan_name_key`: UNIQUE btree (plan_name)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.notifications` (table, ~12 rows, 104 kB)
```
id bigint NN
tenant_id uuid NN
actor_type character varying(50) NN
event_type character varying(100) NN
entity_type character varying(50)
entity_id character varying(100)
payload jsonb NN
target_roles text[] NN
is_read boolean NN
dispatched_at timestamp with time zone NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `idx_notif_event_type`: btree (event_type, created_at DESC)
- index `idx_notif_tenant_unread`: btree (tenant_id, created_at DESC) WHERE (is_read = false)
- index `notifications_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.pipeline_jobs` (table, ~523 rows, 480 kB)
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
- owner `cis_owner`
- index `ix_pipeline_jobs_created`: btree (created_at DESC)
- index `ix_pipeline_jobs_status`: btree (status)
- index `pipeline_jobs_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.pipeline_lessons` (table, 24 kB)
```
id integer NN
batch character varying(100)
country character varying(100)
stage character varying(30) NN
field character varying(50)
pattern text NN
why_it_matters text
what_to_do text NN
example_before text
example_after text
is_active boolean
version integer
created_at timestamp with time zone
```
- owner `cis_owner`
- index `idx_pipeline_lessons_stage`: btree (stage) WHERE (is_active = true)
- index `pipeline_lessons_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.pipeline_runs` (table, ~46 rows, 208 kB)
```
id uuid NN
tenant_id uuid NN
batch_id uuid NN
batch_name character varying(255)
s3_source_path character varying(500)
status character varying(50) NN
tours_total integer NN
tours_passed integer NN
tours_hitl integer NN
tours_failed integer NN
cost_usd numeric(10,4)
tokens_input bigint
tokens_output bigint
tokens_cached bigint
langfuse_trace_url character varying(500)
started_at timestamp with time zone NN
completed_at timestamp with time zone
error_message text
llm_provider text
llm_model text
step_name text
ingest_details jsonb
```
- owner `cis_owner` · RLS on + FORCE
- index `idx_pipeline_runs_batch`: btree (batch_id)
- index `idx_pipeline_runs_status`: btree (status)
- index `idx_pipeline_runs_tenant`: btree (tenant_id)
- index `pipeline_runs_batch_id_key`: UNIQUE btree (batch_id)
- index `pipeline_runs_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `aa_app_user`: INSERT, SELECT, UPDATE
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `pipeline_runs_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `pipeline_runs_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `shared.place_photo` (table, ~3232 rows, 2.6 MB)
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
- owner `cis_owner`
- index `place_photo_country_status_idx`: btree (country, status)
- index `place_photo_destination_idx`: btree (destination_id) WHERE (destination_id IS NOT NULL)
- index `place_photo_drive_file_id_key`: UNIQUE btree (drive_file_id)
- index `place_photo_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `place_photo_tour_idx`: btree (tour_id) WHERE (tour_id IS NOT NULL)
- check `place_photo_match_source_check`: CHECK ((match_source = ANY (ARRAY['auto'::text, 'manual'::text])))
- check `place_photo_status_check`: CHECK ((status = ANY (ARRAY['matched'::text, 'unmatched'::text, 'rejected'::text, 'error'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.prompt_eval_runs` (table, 48 kB)
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
- owner `cis_owner`
- index `idx_prompt_eval_runs_pipeline_created`: btree (pipeline, created_at DESC)
- index `prompt_eval_runs_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `prompt_eval_runs_pipeline_check`: CHECK ((pipeline = ANY (ARRAY['s1_old'::text, 's1_from_atom'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.rerun_wave` (table, 48 kB)
```
id uuid NN
name text NN
country text
expected_tour_ids uuid[] NN
status text NN
notes text
created_by text
created_at timestamp with time zone NN
closed_at timestamp with time zone
last_checked_at timestamp with time zone
last_check jsonb
```
- owner `cis_owner`
- index `idx_rerun_wave_open`: btree (created_at DESC) WHERE (status = 'open'::text)
- index `rerun_wave_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `rerun_wave_expected_tour_ids_check`: CHECK ((cardinality(expected_tour_ids) > 0))
- check `rerun_wave_status_check`: CHECK ((status = ANY (ARRAY['open'::text, 'complete'::text, 'incomplete'::text, 'closed'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.schema_versions` (table, ~239 rows, 96 kB)
```
version character varying(20) NN
description text
applied_at timestamp with time zone NN
```
- owner `cis_owner`
- index `schema_versions_pkey` PRIMARY KEY: UNIQUE btree (version)
- grant `bk_owner`: INSERT, SELECT
- grant `cis_app`: SELECT
- grant `tp_owner`: INSERT, SELECT
- trigger `schema_versions_key_guard`: BEFORE INSERT ON shared.schema_versions FOR EACH ROW EXECUTE FUNCTION shared.schema_versions_key_guard()

### `shared.spend_budget` (table, 32 kB)
```
provider text NN
scope text NN
per_run_usd numeric(10,2)
per_day_usd numeric(10,2)
hard_stop boolean NN
alert_pct integer NN
updated_at timestamp with time zone NN
updated_by text
```
- owner `cis_owner`
- index `spend_budget_pkey` PRIMARY KEY: UNIQUE btree (provider, scope)
- check `spend_budget_alert_pct_check`: CHECK (((alert_pct >= 1) AND (alert_pct <= 100)))
- check `spend_budget_per_day_usd_check`: CHECK (((per_day_usd IS NULL) OR (per_day_usd >= (0)::numeric)))
- check `spend_budget_per_run_usd_check`: CHECK (((per_run_usd IS NULL) OR (per_run_usd >= (0)::numeric)))
- check `spend_budget_provider_check`: CHECK ((provider = ANY (ARRAY['dfs'::text, 'bedrock'::text, 'openai'::text, 'jev'::text, 'geocoder'::text])))
- check `spend_budget_scope_check`: CHECK (((scope = 'global'::text) OR (scope ~~ 'job:%'::text)))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.staff_app_grant` (table, 32 kB)
```
admin_user_id uuid NN
app text NN
role text NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `staff_app_grant_pkey` PRIMARY KEY: UNIQUE btree (admin_user_id, app)
- check `staff_app_grant_app_chk`: CHECK ((app = 'booking'::text))
- check `staff_app_grant_role_chk`: CHECK ((role = ANY (ARRAY['admin'::text, 'sales'::text, 'contracting'::text, 'content_creator'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.tenant_api_usage` (table, ~136572 rows, 33.3 MB)
```
id uuid NN
tenant_id uuid
endpoint character varying(100) NN
method character varying(10) NN
status_code integer NN
response_ms integer
called_at timestamp with time zone NN
actor_type character varying(10) NN
admin_user_id uuid
```
- owner `cis_owner`
- index `idx_tenant_api_usage_actor_type`: btree (actor_type)
- index `idx_tenant_api_usage_admin_user_id`: btree (admin_user_id)
- index `idx_tenant_api_usage_called_at`: btree (called_at)
- index `idx_tenant_api_usage_tenant_id`: btree (tenant_id)
- index `tenant_api_usage_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `tenant_api_usage_tenant_called_idx`: btree (tenant_id, called_at)
- check `chk_tenant_api_usage_actor`: CHECK (((((actor_type)::text = 'tenant'::text) AND (tenant_id IS NOT NULL) AND (admin_user_id IS NULL)) OR (((actor_type)::text = 'admin'::text) AND (tenant_id IS NULL) AND (admin_user_id IS NOT NULL)) OR (((actor_type)::text = 'admin'::text) AND (tenant_id IS NULL) AND (admin_user_id IS NULL))))
- check `tenant_api_usage_actor_type_check`: CHECK (((actor_type)::text = ANY ((ARRAY['tenant'::character varying, 'admin'::character varying])::text[])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.tenant_api_usage_monthly` (table, 48 kB)
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
- owner `cis_owner`
- index `tenant_api_usage_monthly_key`: UNIQUE btree (month, tenant_id, actor_type) NULLS NOT DISTINCT
- index `tenant_api_usage_monthly_tenant_idx`: btree (tenant_id, month)
- check `tenant_api_usage_monthly_first_day`: CHECK ((EXTRACT(day FROM month) = (1)::numeric))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.tenant_brand_rule_versions` (table, 64 kB)
```
version_id uuid NN
tenant_id uuid NN
snapshot jsonb NN
source_docx_s3_key text
source_type text NN
created_by character varying(50)
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `idx_brand_rule_versions_tenant`: btree (tenant_id, created_at DESC)
- index `tenant_brand_rule_versions_pkey` PRIMARY KEY: UNIQUE btree (version_id)
- check `tenant_brand_rule_versions_source_type_check`: CHECK ((source_type = ANY (ARRAY['manual'::text, 'docx_parse'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.tenant_brand_rules` (table, ~1 rows, 184 kB)
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
target_markets text[]
brand_name text NN
good_examples text
default_cta text
```
- owner `cis_owner`
- index `idx_brand_rules_tenant_brand`: btree (tenant_id, brand_name)
- index `tenant_brand_rules_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `uq_tenant_brand_name_version`: UNIQUE btree (tenant_id, brand_name, version)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.tenant_brand_rules_deleted_aa404` (table, 96 kB)
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
target_markets text[]
brand_name text NN
good_examples text
deleted_at timestamp with time zone NN
```
- owner `cis_owner`
- index `tenant_brand_rules_deleted_aa404_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `tenant_brand_rules_deleted_aa404_tenant_id_brand_name_idx`: btree (tenant_id, brand_name)
- index `tenant_brand_rules_deleted_aa4_tenant_id_brand_name_version_key`: UNIQUE btree (tenant_id, brand_name, version)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.tenant_export_config` (table, 48 kB)
```
id uuid NN
tenant_id uuid NN
webhook_url character varying(500)
export_format export_format_enum NN
field_mapping jsonb
auth_header character varying(500)
is_active boolean NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `tenant_export_config_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `tenant_export_config_tenant_id_key`: UNIQUE btree (tenant_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.tenant_integrations` (table, 64 kB)
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
- owner `cis_owner` · RLS on
- index `idx_tenant_integrations_tenant`: btree (tenant_id)
- index `tenant_integrations_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `tenant_integrations_tenant_id_integration_type_key`: UNIQUE btree (tenant_id, integration_type)
- grant `aa_app_user`: DELETE, SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: INSERT (connected_at, integration_type, tenant_id)
- column grant `aa_app_user`: INSERT, UPDATE (config, secret_key)
- column grant `aa_app_user`: UPDATE (last_verified_at, last_verify_error, updated_at)
- policy `tenant_integrations_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `shared.tenant_rewrite_usage` (table, ~6 rows, 64 kB)
```
tenant_id uuid NN
year_month text NN
rewrite_count integer NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `tenant_rewrite_usage_pkey` PRIMARY KEY: UNIQUE btree (tenant_id, year_month)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.tenant_seo_config` (table, 48 kB)
```
id uuid NN
tenant_id uuid NN
seo_provider seo_provider_enum NN
custom_keywords jsonb
target_market jsonb
overrides jsonb
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `tenant_seo_config_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `tenant_seo_config_tenant_id_key`: UNIQUE btree (tenant_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.tenants` (table, ~4 rows, 80 kB)
```
tenant_id uuid NN
name character varying(255) NN
slug character varying(100) NN
plan_tier plan_tier_enum NN
api_key_hash character varying(255)
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
- owner `cis_owner`
- index `tenants_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- index `tenants_slug_key`: UNIQUE btree (slug)
- check `tenants_daily_publish_limit_positive`: CHECK (((daily_publish_limit IS NULL) OR (daily_publish_limit >= 1)))
- check `tenants_posts_per_week_range`: CHECK (((posts_per_week >= 1) AND (posts_per_week <= 14)))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.unmapped_market_requests` (table, 32 kB)
```
id uuid NN
tenant_id uuid NN
country_code text NN
requested_at timestamp with time zone NN
first_seen_at timestamp with time zone NN
resolved_at timestamp with time zone
```
- owner `cis_owner`
- index `idx_unmapped_market_unresolved`: btree (country_code) WHERE (resolved_at IS NULL)
- index `unmapped_market_requests_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `unmapped_market_requests_tenant_id_country_code_key`: UNIQUE btree (tenant_id, country_code)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.v_batch_stats` (VIEW)
```
batch_id uuid
total bigint
passed bigint
hitl bigint
failed bigint
```
- owner `cis_owner`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

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
- owner `cis_owner`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- grant `tripplanner`: SELECT

### `shared.v_pipeline_summary` (VIEW)
```
tour_id uuid
tenant_id uuid
batch_id uuid
src_name character varying(500)
country text
pipeline_status pipeline_status_enum
ingest_at timestamp with time zone
latest_content_id uuid
content_version smallint
content_status content_status_enum
score_overall numeric(5,2)
failure_codes jsonb
published_at timestamp with time zone
```
- owner `cis_owner`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.v_tenant_monthly_usage` (VIEW)
```
tenant_id uuid
tenant_name character varying(255)
plan_tier plan_tier_enum
slug character varying(100)
tours_quota_monthly integer
api_calls_quota_monthly integer
price_usd_monthly numeric(10,2)
overage_rate_usd_per_tour numeric(8,4)
billing_month timestamp with time zone
tours_rewritten bigint
api_calls_used numeric
quota_tours_pct numeric
quota_calls_pct numeric
tours_overage bigint
overage_usd numeric
llm_cost_usd numeric
```
- owner `cis_owner`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

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
- owner `cis_owner`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- grant `tripplanner`: SELECT

## `silver_aa_internal` (7 objects)

### `silver_aa_internal.generated_content` (table, ~1423 rows, 14.8 MB)
```
id uuid NN
tour_id uuid NN
tenant_id uuid NN
version_num smallint NN
aa_name character varying(500)
aa_subtitle character varying(500)
aa_summary text
aa_description text
aa_highlights jsonb
aa_itineraries text
mobile_card_text character varying(80)
seo_title character varying(70)
seo_meta character varying(170)
seo_keywords_used jsonb
og_tags jsonb
model_editorial character varying(100)
model_schema character varying(100)
prompt_version character varying(50)
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
reviewed_by_legacy character varying(128)
edited_at timestamp with time zone
edit_diff jsonb NN
revalidate_passed boolean
reviewed_by uuid
satellite_used boolean NN
satellite_account text
```
- owner `cis_owner` · RLS on + FORCE
- index `generated_content_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `generated_content_tour_id_version_num_key`: UNIQUE btree (tour_id, version_num)
- index `idx_aa_internal_gen_content_status`: btree (status)
- index `idx_aa_internal_gen_content_tour`: btree (tour_id)
- index `idx_generated_content_metadata_gin`: gin (metadata jsonb_path_ops)
- check `generated_content_satellite_account_valid`: CHECK (((satellite_account IS NULL) OR (satellite_account = ANY (ARRAY['acc1'::text, 'acc3'::text]))))
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `generated_content_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `generated_content_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `silver_aa_internal.quality_scores` (table, ~1432 rows, 2 MB)
```
id uuid NN
generated_content_id uuid NN
tour_id uuid NN
tenant_id uuid NN
score_overall numeric(5,2) NN
score_brand numeric(5,2)
score_seo numeric(5,2)
score_structure numeric(5,2)
score_quality numeric(5,2)
failure_codes jsonb
issues jsonb
passed_count smallint NN
failed_count smallint NN
validator_fn_version character varying(50)
langfuse_trace_id character varying(200)
evaluated_at timestamp with time zone NN
brand_audit_status text
brand_audit_codes jsonb
brand_audit_issues jsonb
brand_audit_fields jsonb
lessons_extracted jsonb
```
- owner `cis_owner` · RLS on + FORCE
- index `quality_scores_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `quality_scores_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `quality_scores_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `silver_aa_internal.raw_sources` (table, ~34 rows, 96 kB)
```
id uuid NN
tenant_id uuid NN
batch_id uuid NN
filename character varying(500) NN
s3_path character varying(500) NN
file_size_kb integer
row_count integer
parsed_at timestamp with time zone NN
parse_errors jsonb
file_hash character varying(64)
```
- owner `cis_owner`
- index `idx_aa_internal_raw_sources_batch`: btree (batch_id)
- index `idx_raw_sources_file_hash`: UNIQUE btree (file_hash) WHERE (file_hash IS NOT NULL)
- index `raw_sources_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `silver_aa_internal.raw_tours` (table, ~987 rows, 5.1 MB)
```
tour_id uuid NN
tenant_id uuid NN
batch_id uuid NN
source_id uuid
tour_id_external text
sku text
provider character varying(255)
src_name character varying(500) NN
src_subtitle character varying(500)
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
best_time_to_go character varying(500)
pipeline_status pipeline_status_enum NN
ingest_at timestamp with time zone NN
review_status character varying(20) NN
reviewed_by uuid
reviewed_at timestamp with time zone
review_notes text
source_group_id uuid
source_version smallint NN
source_status silver_aa_internal.source_status_enum NN
deleted_at timestamp with time zone
deleted_by text
lifecycle_stage silver_aa_internal.tour_lifecycle_stage_enum NN
country_raw_unresolved text
```
- owner `cis_owner` · RLS on + FORCE
- index `idx_aa_internal_raw_tours_batch`: btree (batch_id)
- index `idx_aa_internal_raw_tours_country`: btree (country)
- index `idx_aa_internal_raw_tours_status`: btree (pipeline_status)
- index `idx_raw_tours_country_raw_unresolved`: btree (country_raw_unresolved) WHERE (country_raw_unresolved IS NOT NULL)
- index `idx_raw_tours_review_status`: btree (review_status)
- index `raw_tours_pkey` PRIMARY KEY: UNIQUE btree (tour_id)
- index `uq_raw_tours_active_per_group`: UNIQUE btree (source_group_id) WHERE (source_status = 'active'::silver_aa_internal.source_status_enum)
- check `chk_raw_tours_country`: CHECK (((country IS NULL) OR (country = ANY (ARRAY['Bhutan'::text, 'Cambodia'::text, 'China'::text, 'India'::text, 'Indonesia'::text, 'Japan'::text, 'Kyrgyzstan'::text, 'Laos'::text, 'Malaysia'::text, 'Mongolia'::text, 'Myanmar'::text, 'Nepal'::text, 'Pakistan'::text, 'Philippines'::text, 'South Korea'::text, 'Sri Lanka'::text, 'Taiwan'::text, 'Thailand'::text, 'Uzbekistan'::text, 'Vietnam'::text]))))
- check `raw_tours_review_status_check`: CHECK (((review_status)::text = ANY (ARRAY[('pending_review'::character varying)::text, ('reviewed'::character varying)::text, ('approved'::character varying)::text, ('rejected'::character varying)::text])))
- grant `aa_app_user`: SELECT
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `tripplanner`: SELECT (country, tour_id)
- policy `aa_app_user_aa_master_read` (PERMISSIVE SELECT TO aa_app_user): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `catalog_owner_aa_master_read` (PERMISSIVE SELECT TO catalog_owner): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `raw_tours_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `raw_tours_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `silver_aa_internal.review_queue` (table, ~229 rows, 176 kB)
```
id uuid NN
tour_id uuid NN
generated_content_id uuid
tenant_id uuid NN
failure_summary text
score_overall numeric(5,2)
step_fn_task_token text
step_fn_execution_arn character varying(500)
review_status review_status_enum NN
reviewer_notes text
reviewed_by character varying(200)
reviewed_at timestamp with time zone
created_at timestamp with time zone NN
tenant_tour_version_id uuid
escalate_detail jsonb
```
- owner `cis_owner`
- index `idx_aa_internal_review_status`: btree (review_status)
- index `review_queue_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `silver_aa_internal.seo_context` (table, ~898 rows, 1.2 MB)
```
id uuid NN
tour_id uuid NN
tenant_id uuid NN
keyword_search character varying(500)
provider seo_provider_enum NN
keyword_ideas jsonb
demographics jsonb
trends jsonb
top_keywords jsonb
cache_key character varying(500)
fetched_at timestamp with time zone NN
expires_at timestamp with time zone
people_also_ask jsonb
related_keywords jsonb
```
- owner `cis_owner` · RLS on + FORCE
- index `seo_context_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `seo_context_tour_id_key`: UNIQUE btree (tour_id)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `aa_app_user_aa_master_read` (PERMISSIVE SELECT TO aa_app_user): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `seo_context_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `seo_context_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `silver_aa_internal.upload_staging` (table, 104 kB)
```
id uuid NN
batch_id uuid NN
tenant_id uuid NN
parsed_payload jsonb NN
matched_tour_id uuid
matched_source_group_id uuid
decision silver_aa_internal.staging_decision_enum NN
decided_by text
decided_at timestamp with time zone
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `upload_staging_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

## `tripplanner` (17 objects)

### `tripplanner.customers` (table, 64 kB)
```
id uuid NN
name text NN
phone text
email text
created_at timestamp with time zone NN
contact_consent boolean NN
contact_consent_at timestamp with time zone
```
- owner `tp_owner`
- index `customers_email_key`: UNIQUE btree (email)
- index `customers_phone_key`: UNIQUE btree (phone)
- index `customers_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.itinerary_components` (table, ~3972 rows, 56.6 MB)
```
id uuid NN
source_tour_id text NN
source_day_index integer NN
destination_id uuid NN
name text NN
activity text NN
intensity_level text NN
season_months integer[] NN
duration_hint text NN
text_extract text NN
embedding vector(1536)
created_at timestamp with time zone NN
```
- owner `tp_owner`
- index `itinerary_components_activity_idx`: btree (activity)
- index `itinerary_components_destination_idx`: btree (destination_id)
- index `itinerary_components_embedding_idx`: hnsw (embedding vector_cosine_ops)
- index `itinerary_components_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `itinerary_components_season_idx`: gin (season_months)
- check `itinerary_components_activity_chk`: CHECK ((activity = ANY (ARRAY['trekking'::text, 'cultural_heritage'::text, 'wildlife_nature'::text, 'water_activities'::text, 'culinary'::text, 'wellness_relaxation'::text, 'adventure_sport'::text, 'local_immersion'::text])))
- check `itinerary_components_duration_chk`: CHECK ((duration_hint = ANY (ARRAY['half_day'::text, 'full_day'::text, 'overnight'::text, 'multi_night'::text])))
- check `itinerary_components_intensity_chk`: CHECK ((intensity_level = ANY (ARRAY['leisurely'::text, 'moderate'::text, 'active'::text, 'strenuous'::text])))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.llm_spend_daily` (table, ~3 rows, 64 kB)
```
day date NN
stage text NN
cost_usd numeric NN
calls integer NN
unpriced_calls integer NN
updated_at timestamp with time zone NN
```
- owner `tp_owner`
- index `llm_spend_daily_pkey` PRIMARY KEY: UNIQUE btree (day, stage)
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.narration_cache` (table, 48 kB)
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
- owner `tp_owner`
- index `narration_cache_created_at_idx`: btree (created_at)
- index `narration_cache_pkey` PRIMARY KEY: UNIQUE btree (itinerary_hash)
- check `narration_cache_mode_chk`: CHECK ((mode = ANY (ARRAY['compose'::text, 'renarrate'::text])))
- check `narration_cache_source_chk`: CHECK ((source = ANY (ARRAY['llm'::text, 'mixed'::text])))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.outbox` (table, 96 kB)
```
id bigint NN
event text NN
schema_version integer NN
idempotency_key text NN
aggregate_id uuid NN
payload jsonb NN
created_at timestamp with time zone NN
```
- owner `tp_owner`
- index `outbox_event_id_idx`: btree (event, id)
- index `outbox_idempotency_key_key`: UNIQUE btree (idempotency_key)
- index `outbox_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `outbox_event_chk`: CHECK ((event = 'inquiry.submitted'::text))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.sessions` (table, ~40 rows, 48 kB)
```
id uuid NN
guest_token text
customer_id uuid
created_at timestamp with time zone NN
expires_at timestamp with time zone
guest_token_hash bytea
```
- owner `tp_owner`
- index `sessions_guest_token_key`: UNIQUE btree (guest_token)
- index `sessions_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `sessions_guest_token_hash_len_chk`: CHECK (((guest_token_hash IS NULL) OR (octet_length(guest_token_hash) = 32)))
- check `sessions_guest_token_retired_chk`: CHECK ((guest_token IS NULL))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.tour_day` (table, ~650 rows, 384 kB)
```
source_tour_id text NN
day_index integer NN
title text NN
start_place text
end_place text
overnight_place text
overnight_destination_id uuid
places text[] NN
extracted_by text NN
source_hash text NN
extracted_at timestamp with time zone NN
```
- owner `tp_owner`
- index `tour_day_overnight_dest_idx`: btree (overnight_destination_id) WHERE (overnight_destination_id IS NOT NULL)
- index `tour_day_pkey` PRIMARY KEY: UNIQUE btree (source_tour_id, day_index)
- check `tour_day_day_index_check`: CHECK ((day_index >= 1))
- check `tour_day_extracted_by_check`: CHECK ((extracted_by = ANY (ARRAY['rule'::text, 'llm'::text, 'rule+llm'::text])))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.tour_graph_build` (table, 32 kB)
```
id uuid NN
built_at timestamp with time zone NN
params jsonb NN
stats jsonb NN
```
- owner `tp_owner`
- index `tour_graph_build_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.tour_graph_edge` (table, ~379 rows, 200 kB)
```
from_destination_id uuid NN
to_destination_id uuid NN
tour_count integer NN
tour_ids text[] NN
km double precision NN
```
- owner `tp_owner`
- index `tour_graph_edge_pkey` PRIMARY KEY: UNIQUE btree (from_destination_id, to_destination_id)
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.tour_graph_node` (table, ~299 rows, 240 kB)
```
destination_id uuid NN
name text NN
country text NN
lat double precision NN
lng double precision NN
tour_ids text[] NN
stop_count integer NN
activities text[] NN
intensity_min text
intensity_max text
season_months integer[] NN
```
- owner `tp_owner`
- index `tour_graph_node_country_idx`: btree (country)
- index `tour_graph_node_pkey` PRIMARY KEY: UNIQUE btree (destination_id)
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.tour_junction` (table, ~3496 rows, 864 kB)
```
destination_a uuid NN
destination_b uuid NN
km double precision NN
cross_border boolean NN
```
- owner `tp_owner`
- index `tour_junction_pkey` PRIMARY KEY: UNIQUE btree (destination_a, destination_b)
- check `tour_junction_check`: CHECK ((destination_a <> destination_b))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.tour_leg` (table, ~3871 rows, 3.1 MB)
```
source_tour_id text NN
day_from integer NN
day_to integer NN
days integer NN
start_destination_id uuid NN
end_destination_id uuid NN
destination_ids uuid[] NN
countries text[] NN
activities text[] NN
```
- owner `tp_owner`
- index `tour_leg_countries_idx`: gin (countries)
- index `tour_leg_end_idx`: btree (end_destination_id)
- index `tour_leg_pkey` PRIMARY KEY: UNIQUE btree (source_tour_id, day_from, day_to)
- index `tour_leg_start_idx`: btree (start_destination_id, days)
- check `tour_leg_check`: CHECK ((day_to > day_from))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.tour_stop` (table, ~622 rows, 320 kB)
```
source_tour_id text NN
day_index integer NN
destination_id uuid NN
country text NN
source text NN
```
- owner `tp_owner`
- index `tour_stop_destination_idx`: btree (destination_id)
- index `tour_stop_pkey` PRIMARY KEY: UNIQUE btree (source_tour_id, day_index)
- check `tour_stop_source_check`: CHECK ((source = ANY (ARRAY['overnight'::text, 'component'::text])))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.trip_drafts` (table, ~64 rows, 112 kB)
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
- owner `tp_owner`
- index `trip_drafts_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_drafts_session_idx`: btree (session_id)
- check `trip_drafts_status_chk`: CHECK ((status = ANY (ARRAY['draft'::text, 'sent'::text])))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.trip_events` (table, ~278 rows, 144 kB)
```
id bigint NN
trip_id uuid NN
session_id uuid NN
event_type text NN
payload jsonb NN
created_at timestamp with time zone NN
```
- owner `tp_owner`
- index `trip_events_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_events_trip_idx`: btree (trip_id, created_at)
- check `trip_events_type_chk`: CHECK ((event_type = ANY (ARRAY['add_component'::text, 'remove_component'::text, 'reorder'::text, 'sent'::text, 'add_day'::text, 'remove_day'::text])))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.v_inquiry_outbox` (VIEW)
```
id bigint
schema_version integer
idempotency_key text
trip_id uuid
payload jsonb
created_at timestamp with time zone
```
- owner `tp_owner`
- grant `booking`: SELECT
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.v_ops_traffic_daily` (VIEW)
```
day date
metric text
n bigint
```
- owner `tp_owner`
- grant `cis_app`: SELECT
- grant `tripplanner`: SELECT

## Roles

Roles other than `pg_*` / `rds*`. Passwords are never part of the dump.

| role | login | superuser | bypassrls | connection limit | settings | member of |
|---|---|---|---|---|---|---|
| `aa_app_user` | yes | no | no | 15 |  |  |
| `aa_cis_admin` | yes | no | no | none |  | bk_owner, cis_app, cis_owner, rds_superuser, tp_owner |
| `bk_owner` | no | no | no | none |  |  |
| `booking` | yes | no | no | 15 |  |  |
| `catalog_owner` | no | no | no | none |  |  |
| `cis_app` | yes | no | no | 90 |  |  |
| `cis_owner` | no | no | no | none |  |  |
| `db_migrator` | yes | no | no | 5 |  | bk_owner, catalog_owner, cis_app, cis_owner, pg_read_all_stats, tp_owner |
| `tp_owner` | no | no | no | none |  |  |
| `tripplanner` | yes | no | no | 30 |  |  |

## Default privileges

Grants applied automatically to objects that `role` creates later (`ALTER DEFAULT PRIVILEGES`).

| role | schema | objects | grantee | privileges |
|---|---|---|---|---|
| `bk_owner` | booking | functions | `booking` | EXECUTE |
| `bk_owner` | booking | tables | `booking` | DELETE,INSERT,SELECT,UPDATE |
| `bk_owner` | booking | sequences | `booking` | SELECT,USAGE |
| `cis_owner` | acp_contract | functions | `cis_app` | EXECUTE |
| `cis_owner` | acp_contract | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | acp_contract | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | acp_deliver | functions | `cis_app` | EXECUTE |
| `cis_owner` | acp_deliver | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | acp_deliver | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | acp_gold_output | functions | `cis_app` | EXECUTE |
| `cis_owner` | acp_gold_output | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | acp_gold_output | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | acp_shared | functions | `cis_app` | EXECUTE |
| `cis_owner` | acp_shared | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | acp_shared | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | acp_silver_s2 | functions | `cis_app` | EXECUTE |
| `cis_owner` | acp_silver_s2 | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | acp_silver_s2 | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | acp_silver_s3 | functions | `cis_app` | EXECUTE |
| `cis_owner` | acp_silver_s3 | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | acp_silver_s3 | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | acp_silver_s4 | functions | `cis_app` | EXECUTE |
| `cis_owner` | acp_silver_s4 | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | acp_silver_s4 | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | geo | functions | `cis_app` | EXECUTE |
| `cis_owner` | geo | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | geo | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | gold_aa_internal | functions | `cis_app` | EXECUTE |
| `cis_owner` | gold_aa_internal | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | gold_aa_internal | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | shared | functions | `cis_app` | EXECUTE |
| `cis_owner` | shared | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | shared | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `cis_owner` | silver_aa_internal | functions | `cis_app` | EXECUTE |
| `cis_owner` | silver_aa_internal | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | silver_aa_internal | sequences | `cis_app` | SELECT,UPDATE,USAGE |
| `tp_owner` | tripplanner | tables | `tripplanner` | DELETE,INSERT,SELECT,UPDATE |
| `tp_owner` | tripplanner | sequences | `tripplanner` | SELECT,USAGE |

## Functions

Extension-owned functions are left out. `SECURITY DEFINER` functions run with the owner's rights.

| function | returns | language | owner | security definer |
|---|---|---|---|---|
| `acp_shared.audit_log_append_only()` | trigger | plpgsql | `cis_owner` | no |
| `acp_shared.audit_log_chain()` | trigger | plpgsql | `cis_owner` | no |
| `booking.policy_approval_maker_checker()` | trigger | plpgsql | `bk_owner` | no |
| `booking.set_updated_at()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_contract_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_contract_rates_fit()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_rate_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_check_transition()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_record_status()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_version_item_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_version_item_sent_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_version_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_version_sent_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.version_item_cost_lock()` | trigger | plpgsql | `bk_owner` | no |
| `geo.name_norm(p text)` | text | sql | `cis_owner` | no |
| `shared.create_tenant_schemas(p_slug character varying)` | void | plpgsql | `cis_owner` | no |
| `shared.job_set_updated_at()` | trigger | plpgsql | `cis_owner` | no |
| `shared.schema_versions_key_guard()` | trigger | plpgsql | `cis_owner` | no |

## Extensions

- `pg_stat_statements` 1.10 (schema `public`)
- `plpgsql` 1.0 (schema `pg_catalog`)
- `vector` 0.8.1 (schema `public`)

## Enums

- `acp_shared.audit_actor_type`: 'hitl_reviewer', 'tenant_admin', 'tenant_reviewer', 'staff', 'machine'
- `gold_aa_internal.master_status_enum`: 'active', 'inactive', 'trashed'
- `public.content_status_enum`: 'draft', 'passed', 'hitl', 'approved', 'rejected', 'published'
- `public.export_format_enum`: 'json', 'csv', 'xml'
- `public.pipeline_status_enum`: 'ingested', 'seo_pending', 'seo_done', 'gen_pending', 'gen_done', 'validating', 'hitl_required', 'hitl_approved', 'hitl_rejected', 'published', 'failed'
- `public.plan_tier_enum`: 'internal', 'starter', 'growth', 'business', 'enterprise'
- `public.review_status_enum`: 'pending', 'approved', 'rejected', 'skipped', 'superseded', 'dismissed'
- `public.seo_provider_enum`: 'dataforseo', 'custom', 'disabled'
- `public.webhook_status_enum`: 'pending', 'delivered', 'failed', 'retrying'
- `shared.admin_role`: 'admin', 'reviewer', 'content', 'viewer'
- `silver_aa_internal.source_status_enum`: 'active', 'superseded', 'trashed'
- `silver_aa_internal.staging_decision_enum`: 'pending', 'bypass', 'replace', 'update', 'keep_both'
- `silver_aa_internal.tour_lifecycle_stage_enum`: 'active', 'phasing_out', 'retired'

## Foreign keys

Format: `child.col` -> `parent.col` (multi-column keys as `(a,b)`).
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
booking.job.parent_job_id -> booking.job.id
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
shared.staff_app_grant.admin_user_id -> shared.admin_users.id
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

## Table activity

`pg_stat_user_tables` counters since the last stats reset (never), as of the Verified line. Use them with the 14-day rule of the Dead Table Registry, not alone.

| table | ~rows | size | seq scans | idx scans | ins / upd / del | dead tuples | last autovacuum |
|---|---|---|---|---|---|---|---|
| `acp_contract.atom_decompose_jobs` | 0 | 104 kB | 1 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_contract.atom_embedding` | 7298 | 118.4 MB | 409 | 65987 | 4782 / 0 / 0 | 0 | 2026-10-10 13:30 |
| `acp_contract.atom_matches` | 10119 | 3.3 MB | 2 | 28882 | 4405 / 24441 / 0 | 747 | 2026-10-08 14:00 |
| `acp_contract.atom_ranking` | 107748 | 67.1 MB | 29202 | 8824 | 4544095 / 4444897 / 4468855 | 0 | 2026-10-20 00:48 |
| `acp_contract.atom_segment` | 12496 | 3.8 MB | 3536 | 5440775 | 14537 / 128590 / 5045 | 9 | 2026-10-16 08:22 |
| `acp_contract.atom_segment_alias` | 410 | 352 kB | 8767 | 213164 | 1642 / 231628 / 1471 | 85 | 2026-10-10 13:29 |
| `acp_contract.atom_segment_member` | 23987 | 5.4 MB | 6674 | 907562 | 38214 / 471 / 18800 | 2003 | 2026-10-16 08:07 |
| `acp_contract.atomize_day_fingerprint` | 10062 | 1.9 MB | 2 | 7584 | 6718 / 43 / 0 | 4 | 2026-10-10 07:13 |
| `acp_contract.hub` | 59 | 152 kB | 1406 | 9303 | 52 / 736 / 774 | 9 | 2026-10-11 23:36 |
| `acp_contract.question_embedding` | 847 | 8.1 MB | 34 | 87 | 71 / 0 / 0 | 0 |  |
| `acp_contract.route` | 9063 | 5.6 MB | 553 | 8517287 | 8417 / 7408 / 0 | 1 | 2026-10-16 08:25 |
| `acp_contract.route_pick` |  | 48 kB | 3 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_contract.s1_from_atom_runs` |  | 64 kB | 1 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_contract.search_demand` | 5089 | 1.7 MB | 2683 | 790 | 501 / 289 / 0 | 237 |  |
| `acp_contract.segment_research_log` | 1337 | 568 kB | 4226 | 14657 | 219 / 0 / 0 | 0 |  |
| `acp_contract.tour_atoms` | 32019 | 19.8 MB | 9970 | 15895352 | 20773 / 13515 / 0 | 457 | 2026-10-10 14:15 |
| `acp_deliver.tenant_tour_pages` | 0 | 40 kB | 884 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.acp_output_rules` |  | 48 kB | 30 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.acp_quota_ledger` |  | 56 kB | 2 | 5 | 5 / 0 / 0 | 0 |  |
| `acp_shared.angle_gate_option` | 57 | 264 kB | 2244 | 40587 | 60 / 60 / 0 | 9 | 2026-10-16 03:32 |
| `acp_shared.angle_gate_request` | 21 | 128 kB | 6901 | 10981 | 21 / 54 / 0 | 4 | 2026-10-16 08:36 |
| `acp_shared.atom_place_card` | 291 | 120 kB | 11550 | 144702 | 298 / 28 / 0 | 27 |  |
| `acp_shared.audit_log` | 1353 | 1.1 MB | 401 | 4159 | 1355 / 0 / 0 | 0 | 2026-10-16 12:16 |
| `acp_shared.content_piece` | 251 | 8.4 MB | 15282 | 77480 | 266 / 531 / 0 | 43 | 2026-10-16 08:01 |
| `acp_shared.content_piece_label` |  | 48 kB | 9 | 20298 | 1 / 0 / 0 | 0 |  |
| `acp_shared.debate_brand_fit_cache` | 375 | 344 kB | 61 | 1452 | 387 / 0 / 0 | 5 |  |
| `acp_shared.facts` |  | 64 kB | 47 | 1519 | 0 / 2 / 0 | 2 |  |
| `acp_shared.marketplace_portfolios` |  | 32 kB | 1 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.place_card` | 111 | 344 kB | 5893 | 215621 | 128 / 101 / 18 | 5 | 2026-10-14 10:18 |
| `acp_shared.place_card_alias` | 361 | 136 kB | 239 | 585 | 409 / 20 / 0 | 20 |  |
| `acp_shared.place_card_miss` |  | 32 kB | 5 | 103 | 3 / 0 / 0 | 0 |  |
| `acp_shared.publish_log` |  | 96 kB | 47 | 5093 | 4 / 8 / 0 | 5 |  |
| `acp_shared.quarter_plan` | 6 | 88 kB | 4 | 8 | 0 / 0 / 0 | 0 |  |
| `acp_shared.quarter_plan_version` | 0 | 112 kB | 3 | 8 | 0 / 0 / 0 | 0 |  |
| `acp_shared.subject` | 342 | 560 kB | 5705 | 2383 | 432 / 373 / 90 | 0 | 2026-10-20 01:10 |
| `acp_shared.tenant_atom_state` | 0 | 80 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.tenant_config` |  | 32 kB | 8 | 125 | 0 / 0 / 0 | 0 |  |
| `acp_shared.year_plan` |  | 40 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.audit_logs` | 54 | 160 kB | 89 | 0 | 64 / 0 / 0 | 0 |  |
| `booking.countries` |  | 32 kB | 91 | 141 | 17 / 0 / 0 | 0 |  |
| `booking.customer_otps` |  | 24 kB | 3 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.customer_sessions` |  | 32 kB | 4 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.customers` | 1 | 104 kB | 2599 | 4 | 9 / 0 / 0 | 0 |  |
| `booking.fx_rates` |  | 48 kB | 73 | 12 | 2 / 0 / 0 | 0 |  |
| `booking.hotel_room_types` |  | 48 kB | 3 | 191 | 2 / 0 / 0 | 0 |  |
| `booking.hotels` |  | 136 kB | 39 | 50 | 1 / 0 / 0 | 0 |  |
| `booking.inbox_cursor` | 1 | 64 kB | 11792 | 6045 | 1 / 5945 / 0 | 29 | 2026-10-20 04:46 |
| `booking.inbox_events` | 5 | 128 kB | 109 | 61 | 6 / 6 / 0 | 6 |  |
| `booking.job` | 5869 | 2.8 MB | 18143 | 492800 | 5968 / 11933 / 0 | 78 | 2026-10-20 04:31 |
| `booking.media_files` |  | 24 kB | 3 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.notification_reads` |  | 24 kB | 3 | 2926 | 0 / 0 / 0 | 0 |  |
| `booking.notifications` | 1 | 64 kB | 695 | 0 | 9 / 0 / 0 | 0 |  |
| `booking.policy_approvals` |  | 64 kB | 120 | 46 | 6 / 0 / 0 | 0 |  |
| `booking.pricing_rules` |  | 48 kB | 81 | 36 | 4 / 0 / 0 | 0 |  |
| `booking.services` |  | 152 kB | 26 | 79 | 1 / 0 / 0 | 0 |  |
| `booking.settings` |  | 32 kB | 10 | 4 | 2 / 0 / 0 | 0 |  |
| `booking.staff_assignments` |  | 64 kB | 40 | 2200 | 1 / 0 / 0 | 0 |  |
| `booking.staff_users` | 3 | 64 kB | 283 | 4488 | 4 / 34 / 0 | 34 |  |
| `booking.supplier_contracts` |  | 64 kB | 4 | 333 | 2 / 6 / 0 | 6 |  |
| `booking.supplier_rates` |  | 80 kB | 10 | 109 | 3 / 0 / 0 | 0 |  |
| `booking.suppliers` |  | 144 kB | 112 | 122 | 1 / 1 / 0 | 1 |  |
| `booking.trip_case_countries` |  | 40 kB | 3 | 582 | 3 / 0 / 0 | 0 |  |
| `booking.trip_case_legs` | 8 | 64 kB | 587 | 117 | 13 / 8 / 0 | 8 |  |
| `booking.trip_case_status_history` | 1 | 64 kB | 93 | 0 | 12 / 0 / 0 | 0 |  |
| `booking.trip_case_status_transitions` |  | 32 kB | 2 | 51 | 12 / 0 / 0 | 0 |  |
| `booking.trip_case_version_itinerary` | 4 | 80 kB | 68 | 31 | 20 / 4 / 0 | 4 |  |
| `booking.trip_case_versions` |  | 80 kB | 9 | 860 | 5 / 9 / 0 | 9 |  |
| `booking.trip_cases` | 1 | 160 kB | 1206 | 10 | 9 / 3 / 0 | 3 |  |
| `booking.trip_plans` |  | 64 kB | 372 | 13602 | 1 / 0 / 0 | 0 |  |
| `booking.version_item_costs` | 4 | 64 kB | 50 | 19 | 7 / 0 / 1 | 1 |  |
| `geo.geocode_call` |  | 48 kB | 6 | 432 | 3 / 0 / 0 | 0 |  |
| `geo.graph_build` |  | 48 kB | 274 | 9086 | 2 / 3 / 0 | 3 |  |
| `geo.graph_edge` | 209 | 112 kB | 8 | 4 | 209 / 0 / 0 | 0 |  |
| `geo.graph_node` | 143 | 96 kB | 9 | 3 | 143 / 0 / 0 | 0 |  |
| `geo.place_name` | 573 | 248 kB | 277 | 1224 | 573 / 517 / 0 | 36 | 2026-10-15 00:03 |
| `geo.place_outlier` |  | 16 kB | 8 | 49 | 0 / 0 / 0 | 0 |  |
| `geo.tour_build` | 27 | 88 kB | 260 | 128 | 46 / 46 / 0 | 24 |  |
| `geo.tour_day` | 392 | 264 kB | 43 | 292 | 392 / 143 / 0 | 8 | 2026-10-15 00:02 |
| `geo.tour_junction` | 2854 | 560 kB | 49 | 0 | 2854 / 0 / 0 | 0 | 2026-10-15 00:07 |
| `geo.tour_leg` | 1971 | 1.1 MB | 108 | 0 | 1971 / 0 / 0 | 0 | 2026-10-15 00:07 |
| `geo.tour_place` | 967 | 16 MB | 603 | 692699 | 967 / 496 / 0 | 62 | 2026-10-15 00:02 |
| `geo.tour_stop` | 407 | 168 kB | 476 | 9 | 407 / 0 / 0 | 0 |  |
| `gold_aa_internal.content_exports` |  | 24 kB | 636 | 0 | 0 / 0 / 0 | 0 |  |
| `gold_aa_internal.published_tours` | 886 | 5.3 MB | 33657 | 12733021 | 497 / 525 / 0 | 61 | 2026-10-10 13:12 |
| `gold_aa_internal.tenant_tour_versions` | 48 | 616 kB | 20548 | 2591 | 52 / 108 / 0 | 14 | 2026-10-15 14:24 |
| `gold_aa_internal.webhook_deliveries` |  | 24 kB | 636 | 0 | 0 / 0 / 0 | 0 |  |
| `public.checkpoint_migrations` |  | 24 kB | 1 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.acp_runs` |  | 40 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.admin_users` | 10 | 80 kB | 6869 | 75345 | 8 / 113 / 4 | 25 |  |
| `shared.alert_recipient` |  | 32 kB | 3 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.cost_explorer_app_snapshot` | 2448 | 696 kB | 85 | 5 | 2448 / 0 / 0 | 0 | 2026-10-19 03:58 |
| `shared.cost_explorer_snapshot` | 2163 | 2.5 MB | 474 | 10 | 6576 / 0 / 6594 | 146 | 2026-10-17 21:00 |
| `shared.decision_cache_hits_daily` | 217 | 104 kB | 661 | 6545 | 217 / 6326 / 0 | 12 | 2026-10-10 17:41 |
| `shared.decision_log` | 331400 | 360.7 MB | 403 | 535798 | 280318 / 0 / 695728 | 0 | 2026-10-16 08:23 |
| `shared.decision_question` | 5 | 72 kB | 8299 | 666 | 1 / 17 / 0 | 2 |  |
| `shared.destinations` | 1469 | 752 kB | 11520 | 1823931 | 334 / 1290 / 0 | 36 | 2026-10-14 14:52 |
| `shared.dfs_balance_snapshot` |  | 288 kB | 1 | 1314 | 15 / 0 / 0 | 0 |  |
| `shared.dfs_call_log` | 2545 | 1 MB | 2039 | 6855 | 688 / 0 / 0 | 0 |  |
| `shared.jev_credit_topup` |  | 48 kB | 12 | 3 | 2 / 0 / 0 | 0 |  |
| `shared.jev_tenant_allowlist` |  | 32 kB | 6397 | 4721 | 4 / 0 / 7 | 7 |  |
| `shared.job` | 2735 | 10.8 MB | 15856 | 819444 | 2124 / 22726 / 0 | 64 | 2026-10-20 02:31 |
| `shared.job_worker` | 170 | 248 kB | 111291 | 224499 | 265 / 73561 / 160 | 46 | 2026-10-20 05:19 |
| `shared.llm_call_daily` |  | 48 kB | 390 | 142 | 5 / 0 / 0 | 0 |  |
| `shared.llm_call_log` | 257439 | 132.7 MB | 8084 | 23151878 | 146020 / 0 / 200 | 200 | 2026-10-15 05:52 |
| `shared.llm_model_catalog` |  | 32 kB | 1521 | 78 | 1 / 4 / 0 | 1 |  |
| `shared.llm_role_config` |  | 32 kB | 1050 | 5725 | 13 / 16 / 6 | 18 |  |
| `shared.llm_shadow_log` | 5554 | 11.9 MB | 10 | 6 | 2973 / 0 / 0 | 0 | 2026-10-08 07:37 |
| `shared.membership_plans` |  | 48 kB | 2254 | 2306 | 0 / 0 / 0 | 0 |  |
| `shared.notifications` | 12 | 104 kB | 16653 | 0 | 11 / 13 / 0 | 13 |  |
| `shared.pipeline_jobs` | 523 | 480 kB | 2 | 22 | 0 / 0 / 0 | 0 |  |
| `shared.pipeline_lessons` |  | 24 kB | 1 | 1956 | 0 / 0 / 0 | 0 |  |
| `shared.pipeline_runs` | 46 | 208 kB | 5849 | 4536 | 0 / 840 / 0 | 24 |  |
| `shared.place_photo` | 3232 | 2.6 MB | 9934 | 2693780 | 0 / 0 / 0 | 0 |  |
| `shared.prompt_eval_runs` |  | 48 kB | 1 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.rerun_wave` |  | 48 kB | 4 | 85 | 1 / 1 / 0 | 1 |  |
| `shared.schema_versions` | 239 | 96 kB | 616 | 392 | 81 / 0 / 0 | 7 |  |
| `shared.spend_budget` |  | 32 kB | 967 | 95 | 4 / 0 / 0 | 0 |  |
| `shared.staff_app_grant` |  | 32 kB | 154 | 82 | 2 / 0 / 1 | 1 |  |
| `shared.tenant_api_usage` | 136572 | 33.3 MB | 9 | 21443 | 96948 / 0 / 200 | 206 | 2026-10-19 05:33 |
| `shared.tenant_api_usage_monthly` |  | 48 kB | 10 | 39 | 3 / 0 / 0 | 0 |  |
| `shared.tenant_brand_rule_versions` |  | 64 kB | 2 | 24 | 0 / 0 / 0 | 0 |  |
| `shared.tenant_brand_rules` | 1 | 184 kB | 22230 | 0 | 14 / 15 / 0 | 5 |  |
| `shared.tenant_brand_rules_deleted_aa404` |  | 96 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.tenant_export_config` |  | 48 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.tenant_integrations` |  | 64 kB | 28 | 894 | 10 / 10 / 10 | 20 |  |
| `shared.tenant_rewrite_usage` | 6 | 64 kB | 2 | 148 | 4 / 47 / 0 | 0 | 2026-10-20 03:09 |
| `shared.tenant_seo_config` |  | 48 kB | 3 | 756 | 4 / 1 / 0 | 1 |  |
| `shared.tenants` | 4 | 80 kB | 231674 | 3192 | 5 / 26 / 0 | 6 |  |
| `shared.unmapped_market_requests` |  | 32 kB | 3 | 400 | 0 / 0 / 0 | 0 |  |
| `silver_aa_internal.generated_content` | 1423 | 14.8 MB | 2046 | 579727 | 978 / 456 / 0 | 84 | 2026-10-08 02:59 |
| `silver_aa_internal.quality_scores` | 1432 | 2 MB | 495617 | 1015 | 984 / 947 / 6 | 123 | 2026-10-10 10:07 |
| `silver_aa_internal.raw_sources` | 34 | 96 kB | 1001 | 1926 | 0 / 0 / 0 | 0 |  |
| `silver_aa_internal.raw_tours` | 987 | 5.1 MB | 21776 | 18600409 | 0 / 821 / 0 | 82 | 2026-10-10 09:43 |
| `silver_aa_internal.review_queue` | 229 | 176 kB | 53307 | 20060 | 178 / 109 / 0 | 66 | 2026-10-08 03:05 |
| `silver_aa_internal.seo_context` | 898 | 1.2 MB | 980 | 708692 | 506 / 0 / 0 | 12 |  |
| `silver_aa_internal.upload_staging` |  | 104 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `tripplanner.customers` |  | 64 kB | 12 | 22 | 6 / 6 / 1 | 7 |  |
| `tripplanner.itinerary_components` | 3972 | 56.6 MB | 3314 | 137543 | 0 / 0 / 240 | 240 |  |
| `tripplanner.llm_spend_daily` | 3 | 64 kB | 906 | 1618 | 6 / 1485 / 0 | 35 | 2026-10-16 09:06 |
| `tripplanner.narration_cache` |  | 48 kB | 4 | 10 | 1 / 1 / 0 | 1 |  |
| `tripplanner.outbox` |  | 96 kB | 14 | 11930 | 7 / 0 / 3 | 1 |  |
| `tripplanner.sessions` | 40 | 48 kB | 333 | 233 | 42 / 41 / 3 | 38 |  |
| `tripplanner.tour_day` | 650 | 384 kB | 6 | 3 | 0 / 0 / 51 | 51 |  |
| `tripplanner.tour_graph_build` |  | 32 kB | 1 | 0 | 0 / 0 / 0 | 0 |  |
| `tripplanner.tour_graph_edge` | 379 | 200 kB | 4 | 0 | 0 / 0 / 0 | 0 |  |
| `tripplanner.tour_graph_node` | 299 | 240 kB | 38 | 66 | 0 / 0 / 0 | 0 |  |
| `tripplanner.tour_junction` | 3496 | 864 kB | 6 | 39069 | 0 / 0 / 0 | 0 |  |
| `tripplanner.tour_leg` | 3871 | 3.1 MB | 1262 | 254 | 0 / 0 / 0 | 0 |  |
| `tripplanner.tour_stop` | 622 | 320 kB | 339 | 158339 | 0 / 0 / 0 | 0 |  |
| `tripplanner.trip_drafts` | 64 | 112 kB | 122 | 222 | 41 / 179 / 1 | 13 |  |
| `tripplanner.trip_events` | 278 | 144 kB | 794 | 258 | 220 / 0 / 6 | 5 |  |

## Unused indexes

Non-PK, non-unique indexes with 0 scans since the stats reset. A drop candidate only after 30 days at 0 (standards C5.2d), through expand/contract.

- `acp_contract.idx_atom_decompose_jobs_status` on `atom_decompose_jobs` (16 kB)
- `acp_contract.idx_route_pick_tenant` on `route_pick` (16 kB)
- `acp_contract.idx_s1_from_atom_runs_prompt_version` on `s1_from_atom_runs` (16 kB)
- `acp_contract.idx_s1_from_atom_runs_tour_id` on `s1_from_atom_runs` (16 kB)
- `acp_shared.idx_output_rules_active` on `acp_output_rules` (16 kB)
- `acp_shared.idx_quota_tenant` on `acp_quota_ledger` (16 kB)
- `acp_shared.idx_angle_gate_request_status` on `angle_gate_request` (16 kB)
- `acp_shared.idx_angle_gate_request_subject` on `angle_gate_request` (16 kB)
- `acp_shared.idx_angle_gate_request_tenant` on `angle_gate_request` (16 kB)
- `acp_shared.idx_content_piece_embedding` on `content_piece` (1.9 MB)
- `acp_shared.idx_content_piece_label_label` on `content_piece_label` (16 kB)
- `acp_shared.idx_quarter_plan_year_plan_id` on `quarter_plan` (16 kB)
- `acp_shared.idx_quarter_plan_version_approval_status` on `quarter_plan_version` (16 kB)
- `acp_shared.idx_tenant_atom_state_tenant` on `tenant_atom_state` (16 kB)
- `booking.audit_logs_actor_ref_idx` on `audit_logs` (16 kB)
- `booking.audit_logs_created_idx` on `audit_logs` (16 kB)
- `booking.audit_logs_entity_idx` on `audit_logs` (16 kB)
- `booking.customer_otps_customer_idx` on `customer_otps` (8 kB)
- `booking.customer_sessions_customer_idx` on `customer_sessions` (8 kB)
- `booking.customers_merge_review_idx` on `customers` (16 kB)
- `booking.customers_phone_lookup_idx` on `customers` (8 kB)
- `booking.hotels_country_idx` on `hotels` (16 kB)
- `booking.hotels_destination_idx` on `hotels` (8 kB)
- `booking.hotels_updated_idx` on `hotels` (16 kB)
- `booking.inbox_events_pending_idx` on `inbox_events` (16 kB)
- `booking.inbox_events_redact_due_idx` on `inbox_events` (16 kB)
- `booking.inbox_events_status_idx` on `inbox_events` (16 kB)
- `booking.job_parent_idx` on `job` (8 kB)
- `booking.notifications_staff_feed_idx` on `notifications` (16 kB)
- `booking.notifications_unread_idx` on `notifications` (16 kB)
- `booking.services_country_idx` on `services` (16 kB)
- `booking.services_destination_idx` on `services` (8 kB)
- `booking.services_type_idx` on `services` (16 kB)
- `booking.services_updated_idx` on `services` (16 kB)
- `booking.staff_users_active_idx` on `staff_users` (16 kB)
- `booking.suppliers_categories_idx` on `suppliers` (24 kB)
- `booking.suppliers_country_idx` on `suppliers` (16 kB)
- `booking.suppliers_destination_idx` on `suppliers` (8 kB)
- `booking.suppliers_updated_idx` on `suppliers` (16 kB)
- `booking.trip_case_countries_country_idx` on `trip_case_countries` (16 kB)
- `booking.trip_case_legs_tour_key_idx` on `trip_case_legs` (16 kB)
- `booking.trip_case_status_history_case_idx` on `trip_case_status_history` (16 kB)
- `booking.trip_case_status_history_case_seq_idx` on `trip_case_status_history` (16 kB)
- `booking.trip_case_version_itinerary_room_type_idx` on `trip_case_version_itinerary` (16 kB)
- `booking.trip_case_version_itinerary_service_idx` on `trip_case_version_itinerary` (16 kB)
- `booking.trip_cases_customer_idx` on `trip_cases` (16 kB)
- `booking.trip_cases_source_idx` on `trip_cases` (16 kB)
- `booking.trip_cases_updated_idx` on `trip_cases` (16 kB)
- `booking.trip_plans_sellable_idx` on `trip_plans` (16 kB)
- `booking.version_item_costs_rate_idx` on `version_item_costs` (16 kB)
- `geo.tour_leg_countries_gin` on `tour_leg` (64 kB)
- `geo.tour_place_embedding_hnsw` on `tour_place` (7.4 MB)
- `geo.tour_place_unlinked_idx` on `tour_place` (56 kB)
- `gold_aa_internal.idx_pt_embedding` on `published_tours` (168 kB)
- `gold_aa_internal.idx_ttv_status` on `tenant_tour_versions` (16 kB)
- `gold_aa_internal.idx_ttv_tenant_id` on `tenant_tour_versions` (16 kB)
- `gold_aa_internal.tenant_tour_versions_job_idx` on `tenant_tour_versions` (16 kB)
- `gold_aa_internal.idx_aa_internal_webhook_status` on `webhook_deliveries` (8 kB)
- `shared.idx_acp_runs_country` on `acp_runs` (8 kB)
- `shared.idx_acp_runs_status` on `acp_runs` (8 kB)
- `shared.alert_recipient_status_idx` on `alert_recipient` (8 kB)
- `shared.cost_explorer_app_snapshot_fetched_idx` on `cost_explorer_app_snapshot` (48 kB)
- `shared.idx_dfs_call_log_endpoint` on `dfs_call_log` (208 kB)
- `shared.idx_dfs_call_log_live` on `dfs_call_log` (32 kB)
- `shared.idx_dfs_call_log_tenant_created` on `dfs_call_log` (176 kB)
- `shared.llm_call_daily_tenant_day_idx` on `llm_call_daily` (16 kB)
- `shared.idx_llm_call_log_account` on `llm_call_log` (480 kB)
- `shared.idx_llm_call_log_model_created` on `llm_call_log` (18.3 MB)
- `shared.idx_notif_event_type` on `notifications` (16 kB)
- `shared.idx_notif_tenant_unread` on `notifications` (16 kB)
- `shared.ix_pipeline_jobs_created` on `pipeline_jobs` (40 kB)
- `shared.idx_pipeline_runs_status` on `pipeline_runs` (16 kB)
- `shared.idx_prompt_eval_runs_pipeline_created` on `prompt_eval_runs` (16 kB)
- `shared.idx_brand_rules_tenant_brand` on `tenant_brand_rules` (16 kB)
- `shared.tenant_brand_rules_deleted_aa404_tenant_id_brand_name_idx` on `tenant_brand_rules_deleted_aa404` (16 kB)
- `silver_aa_internal.idx_aa_internal_gen_content_status` on `generated_content` (32 kB)
- `silver_aa_internal.idx_generated_content_metadata_gin` on `generated_content` (1.5 MB)
- `silver_aa_internal.idx_raw_tours_country_raw_unresolved` on `raw_tours` (16 kB)
- `tripplanner.itinerary_components_activity_idx` on `itinerary_components` (64 kB)
- `tripplanner.itinerary_components_embedding_idx` on `itinerary_components` (21.7 MB)
- `tripplanner.itinerary_components_season_idx` on `itinerary_components` (288 kB)
- `tripplanner.narration_cache_created_at_idx` on `narration_cache` (16 kB)
- `tripplanner.tour_day_overnight_dest_idx` on `tour_day` (40 kB)
- `tripplanner.tour_leg_countries_idx` on `tour_leg` (144 kB)

## Soft-key orphans (DM-4.2)

Cross-app keys that have no FK (data standards DM-2.3) and how many rows point at nothing in the target, as of the Verified line (counts lag between structural changes, like `~rows`). `not_applicable` = the key columns or the target do not exist yet; `no_privilege` = the dump role cannot read one side. Orphan rate = orphans / rows with a key.

| key | status | rows | without key | orphans | orphan rate |
|---|---|---|---|---|---|
| booking.trip_case_legs.(source_system, source_id) -> catalog.v_tour | ok | 13 | 0 | 0 | 0.00% |

## RLS catalogue guard (X2)

Rules in AA-CIS-Infra `db/rls_catalogue_rules.py` (byte copy of AA-CIS-App `tests/integration/rls_catalogue_rules.py`, which CIS CI runs on the replayed migrations). A violation is a finding that is not on the allowlist; each allowlist entry carries a one-line reason. Fix the object or allowlist it in the CIS file, then copy it here.

**0 unallowlisted violation(s)**, 124 allowlisted finding(s), 0 stale allowlist entry(ies).

| rule | meaning | violations | allowlisted |
|---|---|---|---|
| a | tenant_id table without RLS + an app.tenant_id policy | 0 | 31 |
| b | policy TO PUBLIC | 0 | 8 |
| c | policy reads app.current_tenant | 0 | 0 |
| d | current_setting('app.tenant_id') outside NULLIF | 0 | 0 |
| e | foreign key across owners | 0 | 10 |
| p | grant to PUBLIC | 0 | 1 |
| g | grant to another owner's role | 0 | 74 |
| t | unconditional (true) policy | 0 | 0 |

### Violations

- none

### Allowlist entries in use

| rule | entry | findings | reason |
|---|---|---|---|
| a | `acp_contract.route_pick` | 1 | tenant route picks written by the T-pipeline jobs; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_deliver.tenant_tour_pages` | 1 | tenant page registry written by the publish job; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.acp_output_rules` | 1 | RLS on with the X1 cis_app parity policy only (CIS 244); no tenant-pool grant |
| a | `acp_shared.acp_quota_ledger` | 1 | tenant quota ledger; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.audit_log` | 1 | tenant action audit log; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.debate_brand_fit_cache` | 1 | pipeline cache keyed by tenant; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.quarter_plan` | 1 | tenant content plan, pipeline + admin only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.subject` | 1 | tenant subjects, pipeline + admin only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.tenant_atom_state` | 1 | per-tenant atom state, pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.tenant_config` | 1 | tenant settings, admin + pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.year_plan` | 1 | tenant content plan, pipeline + admin only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.acp_runs` | 1 | legacy ACP v1 run table (pre-AA-751); platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.decision_log` | 1 | Jev decision audit; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.dfs_call_log` | 1 | DataForSEO cost log; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.jev_tenant_allowlist` | 1 | Jev rollout switch per tenant (admin-managed); platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.llm_call_daily` | 1 | cost log roll-up; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.llm_call_log` | 1 | cost log of every app; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.notifications` | 1 | staff notifications; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_api_usage` | 1 | API metering written by the middleware; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_api_usage_monthly` | 1 | API metering roll-up; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_brand_rule_versions` | 1 | history of tenant brand rules; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_brand_rules` | 1 | tenant brand rules, admin + pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_brand_rules_deleted_aa404` | 1 | AA-404 backup copy of deleted brand rules; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_export_config` | 1 | tenant export settings, admin + pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_rewrite_usage` | 1 | rewrite quota counter; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_seo_config` | 1 | tenant SEO settings, admin + pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenants` | 1 | the tenant registry itself (tenant_id is its key); cis_app only, no tenant-pool grant |
| a | `shared.unmapped_market_requests` | 1 | admin triage list of market requests; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `silver_aa_internal.raw_sources` | 1 | source registry, admin + pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `silver_aa_internal.review_queue` | 1 | staff review queue; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `silver_aa_internal.upload_staging` | 1 | staff upload staging; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| b | `gold_aa_internal.content_exports:tenant_isolation` | 1 | legacy tenant_isolation TO PUBLIC (004/006, pre-X1); retire in a tenant-pool review |
| b | `gold_aa_internal.published_tours:tenant_isolation` | 1 | legacy tenant_isolation TO PUBLIC (004/006, pre-X1); retire in a tenant-pool review |
| b | `gold_aa_internal.webhook_deliveries:tenant_isolation` | 1 | legacy tenant_isolation TO PUBLIC (004/006, pre-X1); retire in a tenant-pool review |
| b | `shared.pipeline_runs:tenant_isolation` | 1 | legacy tenant_isolation TO PUBLIC (004/006, pre-X1); retire in a tenant-pool review |
| b | `silver_aa_internal.generated_content:tenant_isolation` | 1 | legacy tenant_isolation TO PUBLIC (004/006, pre-X1); retire in a tenant-pool review |
| b | `silver_aa_internal.quality_scores:tenant_isolation` | 1 | legacy tenant_isolation TO PUBLIC (004/006, pre-X1); retire in a tenant-pool review |
| b | `silver_aa_internal.raw_tours:tenant_isolation` | 1 | legacy tenant_isolation TO PUBLIC (004/006, pre-X1); retire in a tenant-pool review |
| b | `silver_aa_internal.seo_context:tenant_isolation` | 1 | legacy tenant_isolation TO PUBLIC (004/006, pre-X1); retire in a tenant-pool review |
| e | `tripplanner.*->shared.destinations` | 10 | TripPlanner FKs to shared.destinations (ADR 0002), removed by X4 |
| g | `acp_contract.tour_atoms.*:tripplanner` | 11 | column grants, CIS 180; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `acp_contract.v_active_tour_atoms.*:tripplanner` | 11 | column grants, CIS 216; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `acp_contract:tripplanner` | 1 | schema USAGE for the atom columns; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `booking.v_ops_case_status:cis_app` | 1 | contract: CIS ops dashboard (bk-017) |
| g | `booking.v_ops_funnel_daily:cis_app` | 1 | contract: CIS ops dashboard (bk-017) |
| g | `booking:cis_app` | 1 | contract: schema USAGE for the CIS ops views (bk-017) |
| g | `catalog.*:booking` | 13 | contract: catalog.* views for Booking (CIS 225, 228) |
| g | `catalog.*:tripplanner` | 13 | contract: catalog.* views for TripPlanner (CIS 225, 228) |
| g | `catalog:booking` | 1 | contract: catalog schema USAGE for Booking (CIS 225, 228) |
| g | `catalog:tripplanner` | 1 | contract: catalog schema USAGE for TripPlanner (CIS 225, 228) |
| g | `gold_aa_internal.published_tours:tripplanner` | 1 | tenant RLS read; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `gold_aa_internal:tripplanner` | 1 | schema USAGE for published_tours; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `shared.destinations:tripplanner` | 1 | CIS 201; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `shared.llm_call_log:tripplanner` | 1 | contract: standing INSERT exception for TripPlanner cost logging (CIS 173) |
| g | `shared.llm_model_catalog:tripplanner` | 1 | CIS 173; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `shared.llm_role_config:tripplanner` | 1 | CIS 173; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `shared.schema_versions:bk_owner` | 1 | contract: bk- keys only, key guard (CIS 243) |
| g | `shared.schema_versions:tp_owner` | 1 | contract: tp- keys only, key guard (CIS 243) |
| g | `shared.v_destination_photos:tripplanner` | 1 | CIS 201; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `shared.v_tour_photos:tripplanner` | 1 | CIS 201; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `shared:bk_owner` | 1 | contract: Booking owner role registers bk- keys (CIS 243) |
| g | `shared:tp_owner` | 1 | contract: TripPlanner owner role registers tp- keys (CIS 243) |
| g | `shared:tripplanner` | 1 | schema USAGE for the shared.* reads below; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `silver_aa_internal.raw_tours.country:tripplanner` | 1 | CIS 179; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `silver_aa_internal.raw_tours.tour_id:tripplanner` | 1 | CIS 179; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `silver_aa_internal:tripplanner` | 1 | schema USAGE for the raw_tours columns; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `tripplanner.v_inquiry_outbox:booking` | 1 | contract: Booking inquiry intake (tp-009) |
| g | `tripplanner.v_ops_traffic_daily:cis_app` | 1 | contract: CIS ops dashboard (tp-015) |
| g | `tripplanner:booking` | 1 | contract: schema USAGE for the inquiry outbox (tp-009) |
| g | `tripplanner:cis_app` | 1 | contract: schema USAGE for the CIS ops view (tp-015) |
| p | `public` | 1 | PostgreSQL default USAGE on the public schema (extensions); no app object lives there |

## Connections at dump time

Client sessions per `application_name` (`(empty)` = a pool without `application_name`, standards C1.1a).

| application_name | role | state | sessions |
|---|---|---|---|
| booking-api | booking | idle | 1 |
| cis-api | cis_app | idle | 3 |
| cis-worker | cis_app | idle | 1 |

## Latest migrations

| version | applied_at | description |
|---|---|---|
| 251 | 2026-10-20 05:27:29.078064+00:00 | AA-913: shared.alert_recipient (alert mailboxes managed from the CIS admin page; SNS alerts topic + ops e-mail) |
| 246 | 2026-10-19 12:59:09.691401+00:00 | AA-860 (X1 S22): probe, logged in as db_migrator, ran as cis_owner (automatic SET ROLE to the live owner of schema shared) |
| 245 | 2026-10-19 12:11:10.859579+00:00 | AA-860 (X1 S21): the 12 CIS schemas and every master-owned object in the 11 runtime schemas owned by cis_owner (catalog.* views stay catalog_owner); permissive policy TO cis_owner on the 8 FORCE RLS tables; default privileges of cis_app restated FOR ROLE cis_owner, FOR ROLE aa_cis_admin rows revoked |
| rl-002 | 2026-10-19 11:19:42.351365+00:00 | AA-860 (X1 S20): role bootstrap part 2 — cis_owner NOLOGIN (CREATE on the database, granted to aa_cis_admin); db_migrator LOGIN CONNECTION LIMIT 5, NOCREATEROLE, no password, member of bk_owner, tp_owner, cis_owner, catalog_owner, cis_app and pg_read_all_stats |
| 250 | 2026-10-19 05:58:39.098615+00:00 | AA-816: admin_users_email_chk allows the E2E test mailbox address (reviewer, no owner, no password); temporary |
| 249 | 2026-10-19 04:53:38.477273+00:00 | AA-878: shared.admin_role gains viewer (read-only staff role for the E2E account) |
| 244 | 2026-10-19 04:14:29.773597+00:00 | AA-860 (X1 S16): cis_app USAGE/DML/sequences/EXECUTE (no trigger fns) in the 11 CIS schemas + default privileges FOR ROLE aa_cis_admin; registry read-only; permissive parity policy TO cis_app on the 8 ENABLE-only + 8 FORCE RLS tables |
| tp-015 | 2026-10-19 02:46:05.697131+00:00 | AA-858: ops overview contract view tripplanner.v_ops_traffic_daily, SELECT to cis_app |
| bk-017 | 2026-10-19 02:42:33.795134+00:00 | AA-858: ops overview contract views booking.v_ops_funnel_daily + v_ops_case_status, SELECT to cis_app |
| 248 | 2026-10-19 02:21:21.997260+00:00 | AA-884: acp_shared.audit_log append-only + sha256 hash chain + http_method/route/status, audit_actor_type staff/machine, shared.job_worker.git_sha, shared.cost_explorer_app_snapshot (App tag) |
| bk-016 | 2026-10-19 01:55:38.389692+00:00 | AA-680 (Phase 2): booking.staff_users cognito_iss / cognito_sub (+ pair and cog: key checks, unique identity index) |
| 247 | 2026-10-18 03:00:20.065738+00:00 | AA-816: shared.admin_users Cognito identity columns (email, display_name, cognito_iss/sub, last_login_at, is_owner), nullable password_hash, shared.staff_app_grant |
| tp-014 | 2026-10-18 01:31:05.331176+00:00 | AA-852 X1 S9: probe, ran as tp_owner (automatic SET ROLE to the live owner of schema tripplanner) |
| bk-015 | 2026-10-18 01:27:47.953040+00:00 | AA-852 (X1 S9): probe, ran as bk_owner (automatic SET ROLE to the live owner of schema booking) |
| tp-013 | 2026-10-17 12:39:45.728135+00:00 | AA-852 X1 S7: schema tripplanner + its 16 objects owned by tp_owner (was aa_cis_admin); default privileges FOR ROLE tp_owner to tripplanner, FOR ROLE aa_cis_admin rows revoked |
| bk-014 | 2026-10-17 12:36:28.913320+00:00 | AA-852 (X1 S6): booking schema, 32 tables, 2 views, 5 sequences, 12 functions owned by bk_owner, default privileges of role booking restated FOR ROLE bk_owner, FOR ROLE aa_cis_admin rows revoked |
| 243 | 2026-10-17 12:32:32.694976+00:00 | AA-852 (X1 S4): bk_owner/tp_owner USAGE on shared + SELECT, INSERT on shared.schema_versions; BEFORE INSERT key guard (registry owner members any key, bk_owner only bk- keys, tp_owner only tp- keys, others none) |
| rl-001 | 2026-10-17 12:29:17.906876+00:00 | AA-852 (X1 S3): role bootstrap — bk_owner, tp_owner NOLOGIN (granted to aa_cis_admin); cis_app LOGIN CONNECTION LIMIT 90, no password (granted to aa_cis_admin for the 244 guards); N3 limits restated from 234 (tripplanner 30, booking 15, aa_app_user 15) |
| 242 | 2026-10-16 15:43:48.481961+00:00 | AA-751 (X6): shared.job conforms to the job table template — kind/lease/attempts CHECKs, updated_at trigger, queue autovacuum |
| bk-013 | 2026-10-16 15:37:53.402363+00:00 | AA-751 (X6): booking.job template catch-up — cancel_requested, progress, cost_usd, parent_job_id (+FK, job_parent_idx), job_running_idx, job_queued_due_idx, queue autovacuum |
