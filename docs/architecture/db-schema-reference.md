# AA-Ecosys DB Schema Reference (live dump)

<!-- schema-fingerprint: 2548fe15ca13b076173c1c0cd6f6e2cd36d41e8b929b241ba4bf3ec2e48e6aca -->

**Verified:** 2026-10-24 10:33 UTC — live catalog dump of the shared RDS (`aa-cis-dev-db`, `aa-cis/dev/rds`, acc2, us-west-1, PostgreSQL 15.17). Latest migration per owner: CIS **274**, TripPlanner **tp-018**, Booking **bk-022** (302 versions registered).

> **Generated file — do not edit by hand** (data standards DM-3.1). It is the single source of truth for table/column names, owners, grants and RLS across CIS, TripPlanner and Booking (one RDS, one schema per owner; ownership rules: `docs/database/schema-ownership.md`). Read it before introspecting columns. AA-CIS-Infra `.github/workflows/db-schema-dump.yml` regenerates it after every DB Migrate apply and every night (`db/schema_dump.py` in a one-off ECS task, then `db/gen_schema_reference.py`) and opens a PR here when the structure changed.
> Source: AA-CIS-Infra DB Schema Dump (after DB Migrate apply of crm/011_crm_l1_console.sql (run 40086257081)), https://github.com/AdventureAsia365-Ecosys/AA-CIS-Infra/actions/runs/40086353427

**ERD:** [one Mermaid diagram per schema](erd/README.md) (keys and foreign keys), generated from the same dump by AA-CIS-Infra `db/gen_erd.py` (AA-894).

**Totals:** 16 schemas (4 empty: acp_gold_output, acp_silver_s2, acp_silver_s3, acp_silver_s4), 242 tables/views, 574 indexes, 277 FKs, 110 RLS policy(ies), 63 functions, 13 enums. Database size 981.2 MB, max_connections 181. RLS catalogue guard: 1 unallowlisted violation(s) (see *RLS catalogue guard (X2)*). DM-6.1 tags: 119 tagged column(s), 13 untagged candidate(s).

## Conventions
- Column format: `name type` — `NN` suffix = NOT NULL. Types are `format_type()` output (`character varying(64)`, `text[]`, `vector(1024)`, enums schema-qualified). A ` · pii:<class>` / ` · conf:<class>` suffix is the column's data standards DM-6.1 tag (its comment starts with it), `(also …)` = further tags named in the same comment; see *Personal and confidential data tags (DM-6.1)*.
- `~N rows` = `pg_class.reltuples` estimate, sizes = `pg_total_relation_size`, both as of the Verified line (a PR is opened only when the structure changes, so these lag between structural changes). Run exact counts before any drop decision.
- Under each object: owner and RLS state (`RLS on` = ENABLE, `+ FORCE` = FORCE ROW LEVEL SECURITY; the owner is exempt unless FORCE), indexes, CHECK constraints, grants to roles other than the owner (`*` = WITH GRANT OPTION), column-level grants, RLS policies and triggers. Usage counters are in *Table activity* at the end.
- `raw_tours` PK is `tour_id` (NOT `id`). `quality_scores` has `evaluated_at` (NOT `created_at`). `published_tours`/`seo_context` have NO `country` — always JOIN `raw_tours`.

## Schemas

| schema | owner | objects | size | grants (USAGE / CREATE) |
|---|---|---|---|---|
| `acp_contract` | cis_owner | 18 | 247.4 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE |
| `acp_deliver` | cis_owner | 1 | 40 kB | aa_app_user: USAGE; cis_app: USAGE |
| `acp_gold_output` | cis_owner | 0 |  | cis_app: USAGE |
| `acp_shared` | cis_owner | 21 | 14.8 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE |
| `acp_silver_s2` | cis_owner | 0 |  | cis_app: USAGE |
| `acp_silver_s3` | cis_owner | 0 |  | cis_app: USAGE |
| `acp_silver_s4` | cis_owner | 0 |  | cis_app: USAGE |
| `booking` | bk_owner | 47 | 6.5 MB | booking: USAGE; cis_app: USAGE |
| `catalog` | cis_owner | 21 |  | aa_app_user: USAGE; booking: USAGE; catalog_owner: USAGE; tripplanner: USAGE |
| `crm` | crm_owner | 46 | 2.8 MB | crm_ai_reader: USAGE; crm_app: USAGE; crm_eraser: USAGE; crm_insights: USAGE; crm_support_reader: USAGE |
| `geo` | cis_owner | 17 | 63.5 MB | catalog_owner: USAGE; cis_app: USAGE |
| `gold_aa_internal` | cis_owner | 6 | 7.5 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE |
| `public` | pg_database_owner | 1 | 24 kB | PUBLIC: USAGE |
| `shared` | cis_owner | 47 | 596.5 MB | aa_app_user: USAGE; bk_owner: USAGE; catalog_owner: USAGE; cis_app: USAGE; crm_owner: USAGE; tp_owner: USAGE; tripplanner: USAGE |
| `silver_aa_internal` | cis_owner | 7 | 24 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE |
| `tripplanner` | tp_owner | 10 | 792 kB | booking: USAGE; cis_app: USAGE; tripplanner: USAGE |

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

### `acp_contract.atom_embedding` (table, ~7728 rows, 126.6 MB)
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

### `acp_contract.atom_matches` (table, ~10947 rows, 3.4 MB)
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

### `acp_contract.atom_ranking` (table, ~105606 rows, 67.1 MB)
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

### `acp_contract.atom_segment` (table, ~13606 rows, 3.8 MB)
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
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_segment_alias` (table, ~438 rows, 352 kB)
```
segment_id_old text NN
segment_id_canonical text NN
merged_at timestamp with time zone NN
```
- owner `cis_owner`
- index `atom_segment_alias_pkey` PRIMARY KEY: UNIQUE btree (segment_id_old)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_segment_member` (table, ~26280 rows, 5.5 MB)
```
segment_id text NN
atom_id text NN
is_alias boolean NN
```
- owner `cis_owner`
- index `atom_segment_member_pkey` PRIMARY KEY: UNIQUE btree (segment_id, atom_id)
- index `idx_atom_segment_member_atom`: btree (atom_id)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atomize_day_fingerprint` (table, ~10617 rows, 2.1 MB)
```
tenant_tour_version_id uuid NN
day_number integer NN
fingerprint_hash text NN
atomized_at timestamp with time zone NN
```
- owner `cis_owner`
- index `atomize_day_fingerprint_pkey` PRIMARY KEY: UNIQUE btree (tenant_tour_version_id, day_number)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.hub` (table, ~64 rows, 152 kB)
```
hub_id uuid NN
hub_name text NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `hub_pkey` PRIMARY KEY: UNIQUE btree (hub_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.question_embedding` (table, ~847 rows, 8.2 MB)
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
- grant `aa_app_user`: SELECT
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

### `acp_contract.tour_atoms` (table, ~35737 rows, 22.1 MB)
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
- owner `cis_owner` · RLS on
- index `idx_tour_atoms_tour_id`: btree (tour_id) WHERE (NOT deleted)
- index `tour_atoms_pkey` PRIMARY KEY: UNIQUE btree (atom_id)
- check `tour_atoms_visual_potential_check`: CHECK (((visual_potential >= 1) AND (visual_potential <= 3)))
- grant `aa_app_user`: SELECT
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `atoms_platform_read` (PERMISSIVE SELECT TO aa_app_user): USING `(owner_scope = 'platform'::text)`
- policy `catalog_owner_read` (PERMISSIVE SELECT TO catalog_owner): USING `true`
- policy `tenant_isolation` (PERMISSIVE SELECT TO aa_app_user): USING `(owner_scope = NULLIF(current_setting('app.tenant_id'::text, true), ''::text))`
- policy `tour_atoms_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`

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
- owner `cis_owner` · RLS on
- index `tenant_tour_pages_pkey` PRIMARY KEY: UNIQUE btree (tenant_id, tour_id)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `aa_app_user_aa_master_read` (PERMISSIVE SELECT TO aa_app_user): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::text)`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = NULLIF(current_setting('app.tenant_id'::text, true), ''::text))` WITH CHECK `(tenant_id = NULLIF(current_setting('app.tenant_id'::text, true), ''::text))`
- policy `tenant_tour_pages_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`

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

### `acp_shared.angle_gate_option` (table, ~57 rows, 296 kB)
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
- grant `aa_app_user`: SELECT
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.audit_log` (table, ~1728 rows, 1.3 MB)
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

### `acp_shared.content_piece` (table, ~317 rows, 10.7 MB)
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

### `acp_shared.debate_brand_fit_cache` (table, ~414 rows, 504 kB)
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

### `acp_shared.place_card` (table, ~112 rows, 344 kB)
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
- column grant `aa_app_user`: SELECT (card_id, status)

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
- grant `aa_app_user`: SELECT
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
- owner `cis_owner` · RLS on
- index `idx_quarter_plan_year_plan_id`: btree (year_plan_id) WHERE (year_plan_id IS NOT NULL)
- index `quarter_plan_pkey` PRIMARY KEY: UNIQUE btree (plan_id)
- index `quarter_plan_tenant_id_year_quarter_key`: UNIQUE btree (tenant_id, year, quarter)
- check `quarter_plan_quarter_check`: CHECK (((quarter >= 1) AND (quarter <= 4)))
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: INSERT (quarter, tenant_id, year)
- column grant `aa_app_user`: INSERT, UPDATE (year_plan_id)
- column grant `aa_app_user`: UPDATE (current_version_id)
- policy `quarter_plan_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

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
- owner `cis_owner` · RLS on
- index `idx_quarter_plan_version_approval_status`: btree (approval_status)
- index `idx_quarter_plan_version_plan_id`: btree (plan_id)
- index `quarter_plan_version_pkey` PRIMARY KEY: UNIQUE btree (version_id)
- index `quarter_plan_version_plan_id_version_no_key`: UNIQUE btree (plan_id, version_no)
- check `quarter_plan_version_approval_status_check`: CHECK (((approval_status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[])))
- check `quarter_plan_version_source_check`: CHECK (((source)::text = ANY ((ARRAY['standard'::character varying, 'override'::character varying])::text[])))
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: INSERT (payload, plan_id, source, version_no)
- column grant `aa_app_user`: INSERT, UPDATE (approval_status)
- column grant `aa_app_user`: UPDATE (approved_at, approved_by)
- policy `quarter_plan_version_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(EXISTS ( SELECT 1
   FROM acp_shared.quarter_plan qp
  WHERE ((qp.plan_id = quarter_plan_version.plan_id) AND (qp.tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))))` WITH CHECK `(EXISTS ( SELECT 1
   FROM acp_shared.quarter_plan qp
  WHERE ((qp.plan_id = quarter_plan_version.plan_id) AND (qp.tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))))`

### `acp_shared.subject` (table, ~409 rows, 600 kB)
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
- owner `cis_owner` · RLS on
- index `idx_subject_tenant_channel_score`: btree (tenant_id, channel, score)
- index `idx_subject_unique_route`: UNIQUE btree (tenant_id, channel, route_id) WHERE (route_id IS NOT NULL)
- index `idx_subject_unique_segment`: UNIQUE btree (tenant_id, channel, segment_id) WHERE (segment_id IS NOT NULL)
- index `subject_pkey` PRIMARY KEY: UNIQUE btree (subject_id)
- check `subject_check`: CHECK ((((segment_id IS NOT NULL) AND (route_id IS NULL)) OR ((segment_id IS NULL) AND (route_id IS NOT NULL))))
- check `subject_state_check`: CHECK ((state = ANY (ARRAY['proposed'::text, 'picked'::text, 'used'::text, 'cut'::text])))
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: UPDATE (state)
- policy `subject_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

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
- owner `cis_owner` · RLS on
- index `year_plan_pkey` PRIMARY KEY: UNIQUE btree (year_plan_id)
- index `year_plan_tenant_id_year_key`: UNIQUE btree (tenant_id, year)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: INSERT (tenant_id, year)
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- policy `year_plan_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`

## `booking` (47 objects)

### `booking.audit_logs` (table, ~108 rows, 184 kB)
```
id uuid NN
actor_type text NN
actor_id uuid
action text NN
entity_type text NN
entity_id uuid
before jsonb · pii:free_text (also pii:name, pii:contact)
after jsonb · pii:free_text (also pii:name, pii:contact)
created_at timestamp with time zone NN
actor_ref text
entity_label text · pii:free_text (also pii:name)
summary text · pii:free_text (also pii:name)
```
- owner `bk_owner`
- index `audit_logs_actor_ref_idx`: btree (actor_ref, created_at DESC) WHERE (actor_ref IS NOT NULL)
- index `audit_logs_created_idx`: btree (created_at DESC)
- index `audit_logs_entity_idx`: btree (entity_type, entity_id, created_at DESC)
- index `audit_logs_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `audit_logs_actor_type_chk`: CHECK ((actor_type = ANY (ARRAY['staff'::text, 'customer'::text, 'system'::text])))
- grant `booking`: INSERT, SELECT

### `booking.b2b_cancellations` (table, 80 kB)
```
id uuid NN
hold_id uuid NN
trip_case_id uuid NN
partner_id uuid NN
m2m_client_id text NN
policy_id uuid NN
reason_code text NN
idempotency_key text NN
departure_date date NN
days_before_departure integer NN
fee_pct numeric(5,2) NN
currency character(3) NN
total_b2b_price numeric(14,2) NN
fee_amount numeric(14,2) NN
refundable_amount numeric(14,2) NN
cancelled_at timestamp with time zone NN
```
- owner `bk_owner`
- index `b2b_cancellations_hold_uq`: UNIQUE btree (hold_id)
- index `b2b_cancellations_partner_idx`: btree (partner_id, cancelled_at DESC)
- index `b2b_cancellations_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `b2b_cancellations_trip_case_uq`: UNIQUE btree (trip_case_id)
- check `b2b_cancellations_amounts_chk`: CHECK (((total_b2b_price >= (0)::numeric) AND (fee_amount >= (0)::numeric) AND (refundable_amount >= (0)::numeric) AND ((fee_amount + refundable_amount) = total_b2b_price)))
- check `b2b_cancellations_client_chk`: CHECK ((m2m_client_id ~ '^[A-Za-z0-9]{1,128}$'::text))
- check `b2b_cancellations_currency_chk`: CHECK ((currency ~ '^[A-Z]{3}$'::text))
- check `b2b_cancellations_fee_pct_chk`: CHECK (((fee_pct >= (0)::numeric) AND (fee_pct <= (100)::numeric)))
- check `b2b_cancellations_key_chk`: CHECK (((length(idempotency_key) >= 8) AND (length(idempotency_key) <= 200)))
- check `b2b_cancellations_reason_chk`: CHECK ((reason_code = ANY (ARRAY['client_cancelled'::text, 'agency_cancelled'::text, 'departure_cancelled'::text, 'other'::text])))
- grant `booking`: INSERT, SELECT
- trigger `b2b_cancellations_outbox`: AFTER INSERT ON booking.b2b_cancellations FOR EACH ROW EXECUTE FUNCTION booking.b2b_cancellations_outbox()

### `booking.b2b_hold_lines` (table, ~12 rows, 72 kB)
```
hold_id uuid NN
line_no smallint NN
line_ref text NN
departure_id uuid
seats smallint NN
held_as text NN
status text NN
updated_at timestamp with time zone NN
answer_due_at timestamp with time zone
answered_at timestamp with time zone
answered_by text
decline_code text
```
- owner `bk_owner`
- index `b2b_hold_lines_departure_idx`: btree (departure_id) WHERE (departure_id IS NOT NULL)
- index `b2b_hold_lines_on_request_idx`: btree (answer_due_at) WHERE (status = 'on_request'::text)
- index `b2b_hold_lines_pkey` PRIMARY KEY: UNIQUE btree (hold_id, line_no)
- index `b2b_hold_lines_ref_uq`: UNIQUE btree (hold_id, line_ref)
- check `b2b_hold_lines_answer_chk`: CHECK ((((answered_by IS NULL) OR (answered_at IS NOT NULL)) AND ((answered_at IS NULL) OR (status = ANY (ARRAY['confirmed'::text, 'declined'::text, 'cancelled'::text])))))
- check `b2b_hold_lines_decline_chk`: CHECK ((((status = 'declined'::text) = (decline_code IS NOT NULL)) AND ((decline_code IS NULL) OR (decline_code = ANY (ARRAY['sold_out'::text, 'supplier_unavailable'::text, 'minimum_not_met'::text, 'other'::text])))))
- check `b2b_hold_lines_held_as_chk`: CHECK ((held_as = ANY (ARRAY['available'::text, 'on_request'::text])))
- check `b2b_hold_lines_no_chk`: CHECK (((line_no >= 1) AND (line_no <= 200)))
- check `b2b_hold_lines_ref_chk`: CHECK (((length(line_ref) >= 1) AND (length(line_ref) <= 64)))
- check `b2b_hold_lines_seats_chk`: CHECK (((seats >= 0) AND (seats <= 120)))
- check `b2b_hold_lines_status_chk`: CHECK ((status = ANY (ARRAY['available'::text, 'on_request'::text, 'confirmed'::text, 'declined'::text, 'cancelled'::text])))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `b2b_hold_lines_outbox`: AFTER UPDATE OF status ON booking.b2b_hold_lines FOR EACH ROW EXECUTE FUNCTION booking.b2b_hold_lines_outbox()
- trigger `b2b_hold_lines_set_updated_at`: BEFORE UPDATE ON booking.b2b_hold_lines FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.b2b_holds` (table, ~2 rows, 128 kB)
```
id uuid NN
partner_id uuid NN
m2m_client_id text NN
quote_id uuid NN
proposal_ref text NN
proposal_version integer NN
idempotency_key text NN
status text NN
expires_at timestamp with time zone NN
extended_count smallint NN
trip_case_id uuid
deposit_ref text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
confirmed_at timestamp with time zone
released_at timestamp with time zone
expired_at timestamp with time zone
extended_at timestamp with time zone
extend_reason text
extend_idempotency_key text
cancellation_policy_id uuid
```
- owner `bk_owner`
- index `b2b_holds_due_idx`: btree (expires_at) WHERE (status = 'active'::text)
- index `b2b_holds_idempotency_uq`: UNIQUE btree (partner_id, idempotency_key)
- index `b2b_holds_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `b2b_holds_proposal_day_idx`: btree (partner_id, proposal_ref, created_at)
- index `b2b_holds_proposal_uq`: UNIQUE btree (partner_id, proposal_ref, proposal_version) WHERE (status = ANY (ARRAY['active'::text, 'confirmed'::text]))
- index `b2b_holds_quote_idx`: btree (quote_id)
- index `b2b_holds_trip_case_uq`: UNIQUE btree (trip_case_id) WHERE (trip_case_id IS NOT NULL)
- check `b2b_holds_client_chk`: CHECK ((m2m_client_id ~ '^[A-Za-z0-9]{1,128}$'::text))
- check `b2b_holds_confirmed_chk`: CHECK (((status = 'confirmed'::text) = ((confirmed_at IS NOT NULL) AND (trip_case_id IS NOT NULL))))
- check `b2b_holds_deposit_chk`: CHECK (((deposit_ref IS NULL) OR ((length(deposit_ref) >= 1) AND (length(deposit_ref) <= 64))))
- check `b2b_holds_expired_chk`: CHECK (((status = 'expired'::text) = (expired_at IS NOT NULL)))
- check `b2b_holds_expiry_chk`: CHECK ((expires_at > created_at))
- check `b2b_holds_extend_chk`: CHECK ((((extended_count = 0) = (extended_at IS NULL)) AND ((extended_at IS NULL) = (extend_reason IS NULL)) AND ((extended_at IS NULL) = (extend_idempotency_key IS NULL)) AND ((extend_reason IS NULL) OR (extend_reason = ANY (ARRAY['payment_claimed'::text, 'client_recheck'::text]))) AND ((extend_idempotency_key IS NULL) OR ((length(extend_idempotency_key) >= 8) AND (length(extend_idempotency_key) <= 200)))))
- check `b2b_holds_extended_chk`: CHECK (((extended_count >= 0) AND (extended_count <= 1)))
- check `b2b_holds_key_chk`: CHECK (((length(idempotency_key) >= 8) AND (length(idempotency_key) <= 200)))
- check `b2b_holds_proposal_chk`: CHECK ((((length(proposal_ref) >= 1) AND (length(proposal_ref) <= 64)) AND (proposal_version >= 1)))
- check `b2b_holds_released_chk`: CHECK (((status = 'released'::text) = (released_at IS NOT NULL)))
- check `b2b_holds_status_chk`: CHECK ((status = ANY (ARRAY['active'::text, 'confirmed'::text, 'expired'::text, 'released'::text])))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `b2b_holds_outbox`: AFTER UPDATE OF status, extended_count ON booking.b2b_holds FOR EACH ROW EXECUTE FUNCTION booking.b2b_holds_outbox()
- trigger `b2b_holds_set_updated_at`: BEFORE UPDATE ON booking.b2b_holds FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.b2b_partners` (table, 64 kB)
```
id uuid NN
tenant_id uuid NN
agency_name text NN · conf:commercial
status text NN
billing_currency character(3) NN
credit_terms_ref text · conf:commercial
m2m_client_id text NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `b2b_partners_client_idx`: btree (m2m_client_id)
- index `b2b_partners_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `b2b_partners_tenant_uq`: UNIQUE btree (tenant_id)
- check `b2b_partners_client_chk`: CHECK ((m2m_client_id ~ '^[A-Za-z0-9]{1,128}$'::text))
- check `b2b_partners_currency_chk`: CHECK ((billing_currency ~ '^[A-Z]{3}$'::text))
- check `b2b_partners_name_chk`: CHECK (((length(btrim(agency_name)) >= 1) AND (length(btrim(agency_name)) <= 200)))
- check `b2b_partners_status_chk`: CHECK ((status = ANY (ARRAY['active'::text, 'suspended'::text])))
- check `b2b_partners_terms_chk`: CHECK (((credit_terms_ref IS NULL) OR ((length(btrim(credit_terms_ref)) >= 1) AND (length(btrim(credit_terms_ref)) <= 120))))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `b2b_partners_set_updated_at`: BEFORE UPDATE ON booking.b2b_partners FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.b2b_quote_lines` (table, 48 kB)
```
quote_id uuid NN
line_no smallint NN
line_ref text NN
component_id text NN
component_kind text NN
service_date date NN
nights smallint
pax_adult smallint NN
pax_child smallint NN
pax_infant smallint NN
rooms jsonb NN
unit text NN
availability text NN
b2b_price numeric(14,2) NN
net_cost_usd numeric(16,4) NN · conf:commercial
supplier_rate_ids uuid[] NN · conf:commercial
departure_id uuid
```
- owner `bk_owner`
- index `b2b_quote_lines_pkey` PRIMARY KEY: UNIQUE btree (quote_id, line_no)
- index `b2b_quote_lines_ref_uq`: UNIQUE btree (quote_id, line_ref)
- check `b2b_quote_lines_availability_chk`: CHECK ((availability = ANY (ARRAY['available'::text, 'on_request'::text, 'sold_out'::text])))
- check `b2b_quote_lines_component_chk`: CHECK (((length(component_id) >= 1) AND (length(component_id) <= 64)))
- check `b2b_quote_lines_kind_chk`: CHECK ((component_kind = ANY (ARRAY['trip_plan'::text, 'hotel_room'::text, 'transfer'::text, 'guide'::text, 'activity'::text, 'entrance'::text, 'meal'::text])))
- check `b2b_quote_lines_nights_chk`: CHECK (((nights IS NULL) OR ((nights >= 1) AND (nights <= 60))))
- check `b2b_quote_lines_no_chk`: CHECK (((line_no >= 1) AND (line_no <= 200)))
- check `b2b_quote_lines_pax_chk`: CHECK ((((pax_adult >= 1) AND (pax_adult <= 60)) AND ((pax_child >= 0) AND (pax_child <= 60)) AND ((pax_infant >= 0) AND (pax_infant <= 20))))
- check `b2b_quote_lines_price_chk`: CHECK (((b2b_price >= (0)::numeric) AND (net_cost_usd >= (0)::numeric)))
- check `b2b_quote_lines_ref_chk`: CHECK (((length(line_ref) >= 1) AND (length(line_ref) <= 64)))
- check `b2b_quote_lines_rooms_chk`: CHECK (((jsonb_typeof(rooms) = 'array'::text) AND (jsonb_array_length(rooms) <= 30)))
- check `b2b_quote_lines_unit_chk`: CHECK ((unit = ANY (ARRAY['per_person'::text, 'per_group'::text, 'per_room_night'::text, 'per_line'::text])))
- grant `booking`: INSERT, SELECT

### `booking.b2b_quotes` (table, 64 kB)
```
id uuid NN
partner_id uuid NN
m2m_client_id text NN
proposal_ref text NN
proposal_version integer NN
currency character(3) NN
fx_rate_per_usd numeric(18,8) NN
fx_buffer_pct numeric(5,4) NN
fx_as_of date NN
fx_source text NN
pricing_rule_valid_from date NN
margin_applied numeric(5,4) NN · conf:commercial
card_fee_pct numeric(5,4) NN · conf:commercial
rounding text NN
priced_on date NN
total_b2b_price numeric(14,2) NN
price_hash character(64) NN
valid_until timestamp with time zone NN
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `b2b_quotes_partner_idx`: btree (partner_id, created_at DESC)
- index `b2b_quotes_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `b2b_quotes_proposal_idx`: btree (partner_id, proposal_ref, proposal_version)
- check `b2b_quotes_client_chk`: CHECK ((m2m_client_id ~ '^[A-Za-z0-9]{1,128}$'::text))
- check `b2b_quotes_currency_chk`: CHECK ((currency ~ '^[A-Z]{3}$'::text))
- check `b2b_quotes_fx_chk`: CHECK (((fx_rate_per_usd > (0)::numeric) AND (fx_buffer_pct >= (0)::numeric) AND (fx_buffer_pct < (1)::numeric) AND ((length(fx_source) >= 1) AND (length(fx_source) <= 64))))
- check `b2b_quotes_hash_chk`: CHECK ((price_hash ~ '^[a-f0-9]{64}$'::text))
- check `b2b_quotes_margin_chk`: CHECK (((margin_applied >= (0)::numeric) AND (margin_applied < (1)::numeric) AND (card_fee_pct >= (0)::numeric) AND (card_fee_pct < (1)::numeric)))
- check `b2b_quotes_proposal_chk`: CHECK ((((length(proposal_ref) >= 1) AND (length(proposal_ref) <= 64)) AND (proposal_version >= 1)))
- check `b2b_quotes_rounding_chk`: CHECK (((length(rounding) >= 1) AND (length(rounding) <= 64)))
- check `b2b_quotes_total_chk`: CHECK ((total_b2b_price >= (0)::numeric))
- check `b2b_quotes_valid_chk`: CHECK ((valid_until > created_at))
- grant `booking`: INSERT, SELECT

### `booking.cancellation_policies` (table, 48 kB)
```
id uuid NN
channel text NN
trip_plan_id uuid
valid_from date NN
title text NN · conf:commercial
tiers jsonb NN
note text · conf:commercial
created_by text
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `cancellation_policies_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `cancellation_policies_scope_uq`: UNIQUE btree (channel, trip_plan_id, valid_from) NULLS NOT DISTINCT
- check `cancellation_policies_channel_chk`: CHECK ((channel = 'b2b'::text))
- check `cancellation_policies_note_chk`: CHECK (((note IS NULL) OR (length(note) <= 500)))
- check `cancellation_policies_tiers_chk`: CHECK (((jsonb_typeof(tiers) = 'array'::text) AND ((jsonb_array_length(tiers) >= 1) AND (jsonb_array_length(tiers) <= 20)) AND jsonb_path_exists(tiers, '$[*]?(@."min_days" == 0)'::jsonpath) AND (NOT jsonb_path_exists(tiers, '$[*]?(!(((((((exists (@."min_days") && @."min_days".type() == "number") && @."min_days" >= 0) && @."min_days" <= 730) && exists (@."fee_pct")) && @."fee_pct".type() == "number") && @."fee_pct" >= 0) && @."fee_pct" <= 100))'::jsonpath))))
- check `cancellation_policies_title_chk`: CHECK (((length(btrim(title)) >= 1) AND (length(btrim(title)) <= 120)))
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
otp_hash text NN · conf:credential
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
refresh_token_hash text NN · conf:credential
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
name text · pii:name
email text · pii:contact
phone text · pii:contact
address text · pii:address
gender text · pii:profile
marital_status text · pii:profile
profession text · pii:profile
profile_media_id uuid · pii:profile
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

### `booking.departure_incidents` (table, 32 kB)
```
id uuid NN
departure_id uuid NN
incident_code text NN
flagged_by text NN
flagged_at timestamp with time zone NN
cleared_by text
cleared_at timestamp with time zone
```
- owner `bk_owner`
- index `departure_incidents_departure_idx`: btree (departure_id, flagged_at DESC)
- index `departure_incidents_open_uq`: UNIQUE btree (departure_id) WHERE (cleared_at IS NULL)
- index `departure_incidents_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `departure_incidents_cleared_chk`: CHECK ((((cleared_at IS NULL) = (cleared_by IS NULL)) AND ((cleared_at IS NULL) OR (cleared_at >= flagged_at))))
- check `departure_incidents_code_chk`: CHECK ((incident_code = ANY (ARRAY['weather'::text, 'road'::text, 'health'::text, 'political'::text, 'supplier'::text, 'other'::text])))
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (cleared_at, cleared_by)
- trigger `departure_incidents_outbox`: AFTER INSERT OR UPDATE OF cleared_at ON booking.departure_incidents FOR EACH ROW EXECUTE FUNCTION booking.departure_incidents_outbox()

### `booking.departures` (table, 64 kB)
```
id uuid NN
trip_plan_id uuid NN
start_date date NN
capacity integer NN
status text NN
auto_confirm boolean NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `departures_date_idx`: btree (start_date)
- index `departures_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `departures_plan_date_uq`: UNIQUE btree (trip_plan_id, start_date)
- check `departures_capacity_chk`: CHECK (((capacity >= 0) AND (capacity <= 1000)))
- check `departures_status_chk`: CHECK ((status = ANY (ARRAY['scheduled'::text, 'guaranteed'::text, 'cancelled'::text])))
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `departures_outbox`: AFTER UPDATE OF status ON booking.departures FOR EACH ROW EXECUTE FUNCTION booking.departures_outbox()
- trigger `departures_set_updated_at`: BEFORE UPDATE ON booking.departures FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

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
internal_notes text · conf:commercial
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
internal_notes text · conf:commercial
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

### `booking.inbox_cursor` (table, ~2 rows, 64 kB)
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

### `booking.inbox_events` (table, ~5 rows, 136 kB)
```
id uuid NN
source text NN
contract text NN
idempotency_key text NN
payload jsonb NN · pii:contact (also pii:name, pii:free_text)
received_at timestamp with time zone NN
processed_at timestamp with time zone
error text · pii:free_text
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

### `booking.job` (table, ~6899 rows, 3.5 MB)
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
s3_key text NN · pii:profile
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

### `booking.notifications` (table, ~1 rows, 96 kB)
```
id uuid NN
recipient_type text NN
recipient_id uuid
type text NN
title text NN · pii:free_text
message text · pii:free_text (also pii:name)
entity_type text
entity_id uuid
data jsonb NN · pii:contact
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

### `booking.outbox` (table, 96 kB)
```
id bigint NN
event_id uuid NN
stream text NN
event_type text NN
partner_id uuid
hold_id uuid
booking_id uuid
line_ref text
departure_id uuid
incident_code text
decline_code text
occurred_at timestamp with time zone NN
feed_seq bigint
sequenced_at timestamp with time zone
```
- owner `bk_owner`
- index `outbox_event_id_uq`: UNIQUE btree (event_id)
- index `outbox_feed_seq_uq`: UNIQUE btree (feed_seq)
- index `outbox_partner_feed_idx`: btree (partner_id, feed_seq) WHERE (feed_seq IS NOT NULL)
- index `outbox_pending_idx`: btree (id) WHERE (feed_seq IS NULL)
- index `outbox_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `outbox_b2b_partner_chk`: CHECK (((stream <> 'b2b'::text) OR (partner_id IS NOT NULL)))
- check `outbox_booking_chk`: CHECK (((event_type <> 'booking.cancelled'::text) OR (booking_id IS NOT NULL)))
- check `outbox_decline_chk`: CHECK ((((event_type = 'line.declined'::text) = (decline_code IS NOT NULL)) AND ((decline_code IS NULL) OR (decline_code = ANY (ARRAY['sold_out'::text, 'supplier_unavailable'::text, 'minimum_not_met'::text, 'other'::text])))))
- check `outbox_departure_chk`: CHECK (((event_type !~~ 'departure.%'::text) OR (departure_id IS NOT NULL)))
- check `outbox_event_type_chk`: CHECK ((event_type = ANY (ARRAY['hold.expired'::text, 'hold.extended'::text, 'line.confirmed'::text, 'line.declined'::text, 'booking.cancelled'::text, 'departure.guaranteed'::text, 'departure.cancelled'::text, 'departure.incident'::text, 'departure.incident_cleared'::text])))
- check `outbox_hold_chk`: CHECK (((event_type = ANY (ARRAY['hold.expired'::text, 'hold.extended'::text, 'line.confirmed'::text, 'line.declined'::text, 'booking.cancelled'::text])) = (hold_id IS NOT NULL)))
- check `outbox_incident_chk`: CHECK ((((event_type = ANY (ARRAY['departure.incident'::text, 'departure.incident_cleared'::text])) = (incident_code IS NOT NULL)) AND ((incident_code IS NULL) OR (incident_code = ANY (ARRAY['weather'::text, 'road'::text, 'health'::text, 'political'::text, 'supplier'::text, 'other'::text])))))
- check `outbox_line_chk`: CHECK ((((event_type = ANY (ARRAY['line.confirmed'::text, 'line.declined'::text])) = (line_ref IS NOT NULL)) AND ((line_ref IS NULL) OR ((length(line_ref) >= 1) AND (length(line_ref) <= 64)))))
- check `outbox_sequenced_chk`: CHECK (((feed_seq IS NULL) = (sequenced_at IS NULL)))
- check `outbox_stream_chk`: CHECK ((stream = 'b2b'::text))
- grant `booking`: SELECT
- column grant `booking`: INSERT (booking_id, decline_code, departure_id, event_type, hold_id, incident_code, line_ref, partner_id, stream)
- column grant `booking`: UPDATE (feed_seq, sequenced_at)

### `booking.policy_approvals` (table, ~6 rows, 80 kB)
```
id uuid NN
entity_type text NN
pricing_rule_id uuid
fx_rate_id uuid
approved_by text NN
approved_at timestamp with time zone NN
note text · conf:commercial
cancellation_policy_id uuid
```
- owner `bk_owner`
- index `policy_approvals_cancellation_policy_uq`: UNIQUE btree (cancellation_policy_id)
- index `policy_approvals_fx_rate_uq`: UNIQUE btree (fx_rate_id)
- index `policy_approvals_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `policy_approvals_pricing_rule_uq`: UNIQUE btree (pricing_rule_id)
- check `policy_approvals_approved_by_chk`: CHECK ((length(btrim(approved_by)) > 0))
- check `policy_approvals_entity_chk`: CHECK ((((entity_type = 'pricing_rule'::text) AND (pricing_rule_id IS NOT NULL) AND (fx_rate_id IS NULL) AND (cancellation_policy_id IS NULL)) OR ((entity_type = 'fx_rate'::text) AND (fx_rate_id IS NOT NULL) AND (pricing_rule_id IS NULL) AND (cancellation_policy_id IS NULL)) OR ((entity_type = 'cancellation_policy'::text) AND (cancellation_policy_id IS NOT NULL) AND (pricing_rule_id IS NULL) AND (fx_rate_id IS NULL))))
- grant `booking`: INSERT, SELECT
- trigger `policy_approvals_cancellation_maker_checker`: BEFORE INSERT ON booking.policy_approvals FOR EACH ROW EXECUTE FUNCTION booking.cancellation_policy_maker_checker()
- trigger `policy_approvals_maker_checker`: BEFORE INSERT ON booking.policy_approvals FOR EACH ROW EXECUTE FUNCTION booking.policy_approval_maker_checker()

### `booking.pricing_rules` (table, 48 kB)
```
id uuid NN
channel text NN
target_margin numeric(5,4) NN · conf:commercial
floor_margin numeric(5,4) NN · conf:commercial
peak_uplift_pts numeric(5,4) NN · conf:commercial
card_fee_pct numeric(5,4) NN · conf:commercial
valid_from date NN
note text · conf:commercial
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
internal_notes text · conf:commercial
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
cis_user_id text NN · pii:online_id
email text · pii:contact
name text · pii:name
role text NN
active boolean NN
cis_role text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
last_seen_at timestamp with time zone
preferences jsonb NN
cognito_iss text · pii:online_id
cognito_sub text · pii:online_id
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
payment_terms text · conf:commercial
cancellation_policy text · conf:commercial
notes text · conf:commercial
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
net_amount numeric(16,2) NN · conf:commercial
currency character(3) NN
notes text · conf:commercial
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
internal_notes text · conf:commercial
contact_name text · pii:name
contact_title text · pii:profile
contact_email text · pii:contact
contact_phone text · pii:contact
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
note text · pii:free_text
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
notes text · pii:free_text
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
notes text · pii:free_text
total_price numeric(12,2)
currency character(3)
is_sent_to_customer boolean NN
sent_at timestamp with time zone
is_approved boolean NN
approved_at timestamp with time zone
created_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
title text · pii:free_text
valid_until date
channel text
fx_rate_locked numeric(18,8)
fx_as_of date
sent_by text
approved_by text
approval_note text · pii:free_text
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

### `booking.trip_cases` (table, ~10 rows, 176 kB)
```
id uuid NN
code text NN
customer_id uuid
status text NN
trip_style text · pii:travel
start_date date · pii:travel
end_date date · pii:travel
pax smallint · pii:travel
currency character(3)
source_system text NN
source_id text
idempotency_key text
inbox_event_id uuid
inquiry_snapshot jsonb · pii:travel (also pii:free_text)
created_by uuid
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
notes text · pii:free_text
pax_adults smallint · pii:travel
pax_children smallint · pii:travel
channel text NN
party_tenant_id uuid
```
- owner `bk_owner`
- index `trip_cases_code_uq`: UNIQUE btree (code)
- index `trip_cases_customer_idx`: btree (customer_id, created_at DESC)
- index `trip_cases_idempotency_key_uq`: UNIQUE btree (idempotency_key)
- index `trip_cases_party_idx`: btree (party_tenant_id, created_at DESC) WHERE (party_tenant_id IS NOT NULL)
- index `trip_cases_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_cases_source_idx`: btree (source_system, source_id)
- index `trip_cases_status_idx`: btree (status, created_at DESC) WHERE (deleted_at IS NULL)
- index `trip_cases_updated_idx`: btree (updated_at DESC) WHERE (deleted_at IS NULL)
- check `trip_cases_channel_chk`: CHECK ((((channel = 'b2c'::text) AND (customer_id IS NOT NULL) AND (party_tenant_id IS NULL)) OR ((channel = 'b2b'::text) AND (customer_id IS NULL) AND (party_tenant_id IS NOT NULL))))
- check `trip_cases_currency_chk`: CHECK (((currency IS NULL) OR (currency ~ '^[A-Z]{3}$'::text)))
- check `trip_cases_dates_chk`: CHECK (((start_date IS NULL) OR (end_date IS NULL) OR (start_date <= end_date)))
- check `trip_cases_pax_chk`: CHECK (((pax IS NULL) OR (pax > 0)))
- check `trip_cases_pax_split_chk`: CHECK ((((pax_adults IS NULL) OR (pax_adults >= 1)) AND ((pax_children IS NULL) OR ((pax_children >= 0) AND (pax_adults IS NOT NULL))) AND ((pax_adults IS NULL) OR (pax = (pax_adults + COALESCE((pax_children)::integer, 0))))))
- check `trip_cases_source_system_chk`: CHECK ((source_system = ANY (ARRAY['cis'::text, 'tripplanner'::text, 'manual'::text, 'crm'::text])))
- check `trip_cases_status_chk`: CHECK ((status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text])))
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `trip_cases_check_transition`: BEFORE UPDATE OF status ON booking.trip_cases FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.trip_case_check_transition()
- trigger `trip_cases_record_status_insert`: AFTER INSERT ON booking.trip_cases FOR EACH ROW EXECUTE FUNCTION booking.trip_case_record_status()
- trigger `trip_cases_record_status_update`: AFTER UPDATE OF status ON booking.trip_cases FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.trip_case_record_status()
- trigger `trip_cases_set_updated_at`: BEFORE UPDATE ON booking.trip_cases FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.trip_plan_components` (table, 48 kB)
```
id uuid NN
trip_plan_id uuid NN
day_no smallint NN
hotel_room_type_id uuid
service_id uuid
created_by text
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `trip_plan_components_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_plan_components_uq`: UNIQUE btree (trip_plan_id, day_no, COALESCE(hotel_room_type_id, service_id))
- check `trip_plan_components_day_chk`: CHECK (((day_no >= 1) AND (day_no <= 366)))
- check `trip_plan_components_target_chk`: CHECK ((num_nonnulls(hotel_room_type_id, service_id) = 1))
- grant `booking`: DELETE, INSERT, SELECT

### `booking.trip_plans` (table, 64 kB)
```
id uuid NN
source_system text NN
source_id text NN
sellable boolean NN
trip_style text
default_channel text · conf:commercial
price_hint_amount numeric(12,2) · conf:commercial
price_hint_currency character(3) · conf:commercial
price_hint_basis text · conf:commercial
commercial_notes text · conf:commercial
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
name text · pii:name
email text · pii:contact
phone text · pii:contact
address text · pii:address
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
net_amount numeric(16,2) NN · conf:commercial
net_currency character(3) NN
supplier_note text · conf:commercial
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

## `catalog` (21 objects)

### `catalog._live_stop` (VIEW)
```
source_id text
tour_id uuid
day_index integer
destination_id uuid
country text
source text
build_id uuid
```
- owner `catalog_owner`

### `catalog._live_tour` (VIEW)
```
tour_id uuid
source_id text
source_version smallint
sku text
country text
duration text
inclusions text
exclusions text
activities jsonb
best_time_to_go character varying(500)
group_size text
lifecycle_stage silver_aa_internal.tour_lifecycle_stage_enum
aa_name character varying(500)
aa_subtitle character varying(500)
aa_summary text
aa_description text
aa_highlights jsonb
aa_itineraries text
published_at timestamp with time zone
master_updated_at timestamp with time zone
```
- owner `catalog_owner`

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

### `catalog.v_component_embedding` (VIEW)
```
component_id uuid
source_id text
destination_id uuid
activity text
intensity_level text
season_months integer[]
embedding vector(1536)
```
- owner `catalog_owner`
- grant `tripplanner`: SELECT

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
shape_kind text
shape_status text
shape_source text
length_km double precision
min_lat double precision
min_lng double precision
max_lat double precision
max_lng double precision
shape_lo jsonb
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

### `catalog.v_destination_redirect` (VIEW)
```
destination_id uuid
keeper_id uuid
```
- owner `catalog_owner`
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

### `catalog.v_destination_shape` (VIEW)
```
destination_id uuid
shape_status text
shape_mid jsonb
shape_lo jsonb
```
- owner `catalog_owner`
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
precision text
segment jsonb
segment_basis text
segment_from_destination_id uuid
segment_to_destination_id uuid
segment_km double precision
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

### `catalog.v_tour_lifecycle_outbox` (VIEW)
```
event_id bigint
source_system text
source_id text
tour_id uuid
event text
reason text
replaced_by_tour_id uuid
occurred_at timestamp with time zone
idempotency_key text
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
segment jsonb
segment_basis text
segment_from_destination_id uuid
segment_to_destination_id uuid
segment_km double precision
```
- owner `catalog_owner`
- grant `aa_app_user`: SELECT
- grant `booking`: SELECT
- grant `tripplanner`: SELECT

### `catalog.v_tour_retired` (VIEW)
```
source_system text
source_id text
tour_id uuid
state text
reason text
changed_at timestamp with time zone
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

## `crm` (46 objects)

### `crm.audit_event` (partitioned table, 0 B)
```
event_id uuid NN
tenant_id uuid NN
at timestamp with time zone NN
actor_kind text NN
actor_ref text NN
action text NN
outcome text NN
object_kind text NN
object_id text
fields text[] NN
reason text
request_id text
created_at timestamp with time zone NN
created_by text NN
object_ids text[] NN
```
- owner `crm_owner` · RLS on + FORCE
- index `audit_event_object_idx`: btree (tenant_id, object_kind, object_id)
- index `audit_event_pkey` PRIMARY KEY: UNIQUE btree (event_id, at)
- index `audit_event_tenant_at_idx`: btree (tenant_id, at DESC)
- check `audit_event_action_chk`: CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_actor_kind_chk`: CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))
- check `audit_event_actor_ref_chk`: CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))
- check `audit_event_fields_chk`: CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))
- check `audit_event_object_id_chk`: CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))
- check `audit_event_object_ids_chk`: CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))
- check `audit_event_object_kind_chk`: CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_outcome_chk`: CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))
- check `audit_event_reason_chk`: CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))
- check `audit_event_request_id_chk`: CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_event_append_only`: BEFORE DELETE OR UPDATE ON crm.audit_event FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `audit_event_check_at`: BEFORE INSERT ON crm.audit_event FOR EACH ROW EXECUTE FUNCTION crm.audit_event_check_at()
- trigger `audit_event_no_truncate`: BEFORE TRUNCATE ON crm.audit_event FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.audit_event_legacy` (table, ~114 rows, 136 kB)
```
event_id uuid NN
tenant_id uuid NN
at timestamp with time zone NN
actor_kind text NN
actor_ref text NN
action text NN
outcome text NN
object_kind text NN
object_id text
fields text[] NN
reason text
request_id text
created_at timestamp with time zone NN
created_by text NN
object_ids text[] NN
```
- owner `crm_owner` · RLS on + FORCE · partition
- index `audit_event_legacy_object_idx`: btree (tenant_id, object_kind, object_id)
- index `audit_event_legacy_pkey` PRIMARY KEY: UNIQUE btree (event_id, at)
- index `audit_event_legacy_tenant_at_idx`: btree (tenant_id, at DESC)
- check `audit_event_action_chk`: CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_actor_kind_chk`: CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))
- check `audit_event_actor_ref_chk`: CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))
- check `audit_event_fields_chk`: CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))
- check `audit_event_object_id_chk`: CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))
- check `audit_event_object_ids_chk`: CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))
- check `audit_event_object_kind_chk`: CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_outcome_chk`: CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))
- check `audit_event_reason_chk`: CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))
- check `audit_event_request_id_chk`: CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_event_append_only`: BEFORE DELETE OR UPDATE ON crm.audit_event_legacy FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `audit_event_check_at`: BEFORE INSERT ON crm.audit_event_legacy FOR EACH ROW EXECUTE FUNCTION crm.audit_event_check_at()
- trigger `audit_event_no_truncate`: BEFORE TRUNCATE ON crm.audit_event_legacy FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.audit_event_p202611` (table, 32 kB)
```
event_id uuid NN
tenant_id uuid NN
at timestamp with time zone NN
actor_kind text NN
actor_ref text NN
action text NN
outcome text NN
object_kind text NN
object_id text
fields text[] NN
reason text
request_id text
created_at timestamp with time zone NN
created_by text NN
object_ids text[] NN
```
- owner `crm_owner` · RLS on + FORCE · partition
- index `audit_event_p202611_pkey` PRIMARY KEY: UNIQUE btree (event_id, at)
- index `audit_event_p202611_tenant_id_at_idx`: btree (tenant_id, at DESC)
- index `audit_event_p202611_tenant_id_object_kind_object_id_idx`: btree (tenant_id, object_kind, object_id)
- check `audit_event_action_chk`: CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_actor_kind_chk`: CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))
- check `audit_event_actor_ref_chk`: CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))
- check `audit_event_fields_chk`: CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))
- check `audit_event_object_id_chk`: CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))
- check `audit_event_object_ids_chk`: CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))
- check `audit_event_object_kind_chk`: CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_outcome_chk`: CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))
- check `audit_event_reason_chk`: CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))
- check `audit_event_request_id_chk`: CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_event_append_only`: BEFORE DELETE OR UPDATE ON crm.audit_event_p202611 FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `audit_event_check_at`: BEFORE INSERT ON crm.audit_event_p202611 FOR EACH ROW EXECUTE FUNCTION crm.audit_event_check_at()
- trigger `audit_event_no_truncate`: BEFORE TRUNCATE ON crm.audit_event_p202611 FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.audit_event_p202612` (table, 32 kB)
```
event_id uuid NN
tenant_id uuid NN
at timestamp with time zone NN
actor_kind text NN
actor_ref text NN
action text NN
outcome text NN
object_kind text NN
object_id text
fields text[] NN
reason text
request_id text
created_at timestamp with time zone NN
created_by text NN
object_ids text[] NN
```
- owner `crm_owner` · RLS on + FORCE · partition
- index `audit_event_p202612_pkey` PRIMARY KEY: UNIQUE btree (event_id, at)
- index `audit_event_p202612_tenant_id_at_idx`: btree (tenant_id, at DESC)
- index `audit_event_p202612_tenant_id_object_kind_object_id_idx`: btree (tenant_id, object_kind, object_id)
- check `audit_event_action_chk`: CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_actor_kind_chk`: CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))
- check `audit_event_actor_ref_chk`: CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))
- check `audit_event_fields_chk`: CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))
- check `audit_event_object_id_chk`: CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))
- check `audit_event_object_ids_chk`: CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))
- check `audit_event_object_kind_chk`: CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_outcome_chk`: CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))
- check `audit_event_reason_chk`: CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))
- check `audit_event_request_id_chk`: CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_event_append_only`: BEFORE DELETE OR UPDATE ON crm.audit_event_p202612 FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `audit_event_check_at`: BEFORE INSERT ON crm.audit_event_p202612 FOR EACH ROW EXECUTE FUNCTION crm.audit_event_check_at()
- trigger `audit_event_no_truncate`: BEFORE TRUNCATE ON crm.audit_event_p202612 FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.audit_event_p202701` (table, 32 kB)
```
event_id uuid NN
tenant_id uuid NN
at timestamp with time zone NN
actor_kind text NN
actor_ref text NN
action text NN
outcome text NN
object_kind text NN
object_id text
fields text[] NN
reason text
request_id text
created_at timestamp with time zone NN
created_by text NN
object_ids text[] NN
```
- owner `crm_owner` · RLS on + FORCE · partition
- index `audit_event_p202701_pkey` PRIMARY KEY: UNIQUE btree (event_id, at)
- index `audit_event_p202701_tenant_id_at_idx`: btree (tenant_id, at DESC)
- index `audit_event_p202701_tenant_id_object_kind_object_id_idx`: btree (tenant_id, object_kind, object_id)
- check `audit_event_action_chk`: CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_actor_kind_chk`: CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))
- check `audit_event_actor_ref_chk`: CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))
- check `audit_event_fields_chk`: CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))
- check `audit_event_object_id_chk`: CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))
- check `audit_event_object_ids_chk`: CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))
- check `audit_event_object_kind_chk`: CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `audit_event_outcome_chk`: CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))
- check `audit_event_reason_chk`: CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))
- check `audit_event_request_id_chk`: CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_event_append_only`: BEFORE DELETE OR UPDATE ON crm.audit_event_p202701 FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `audit_event_check_at`: BEFORE INSERT ON crm.audit_event_p202701 FOR EACH ROW EXECUTE FUNCTION crm.audit_event_check_at()
- trigger `audit_event_no_truncate`: BEFORE TRUNCATE ON crm.audit_event_p202701 FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.audit_export_manifest` (table, 64 kB)
```
manifest_id uuid NN
tenant_id uuid NN
seq bigint NN
period_start timestamp with time zone NN
period_end timestamp with time zone NN
event_count integer NN
content_sha256 text NN
prev_manifest_sha256 text NN
manifest_sha256 text NN
object_key text NN
object_sha256 text NN
format_version smallint NN
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `audit_export_manifest_period_uq`: UNIQUE btree (tenant_id, period_start)
- index `audit_export_manifest_pkey` PRIMARY KEY: UNIQUE btree (manifest_id)
- index `audit_export_manifest_seq_uq`: UNIQUE btree (tenant_id, seq)
- check `audit_export_manifest_count_chk`: CHECK ((event_count >= 0))
- check `audit_export_manifest_format_chk`: CHECK ((format_version = 1))
- check `audit_export_manifest_hashes_chk`: CHECK (((content_sha256 ~ '^[0-9a-f]{64}$'::text) AND (prev_manifest_sha256 ~ '^[0-9a-f]{64}$'::text) AND (manifest_sha256 ~ '^[0-9a-f]{64}$'::text) AND (object_sha256 ~ '^[0-9a-f]{64}$'::text)))
- check `audit_export_manifest_key_chk`: CHECK (((object_key ~~ (('audit/v1/tenants/'::text || (tenant_id)::text) || '/%'::text)) AND (object_key ~ '^audit/v1/tenants/[0-9a-f-]{36}/[0-9]{4}/[0-9]{2}/[0-9]{2}/[0-9]{4}Z-[0-9]{10}\.jsonl$'::text)))
- check `audit_export_manifest_period_chk`: CHECK (((period_end > period_start) AND (period_start = (date_trunc('hour'::text, (period_start AT TIME ZONE 'UTC'::text)) AT TIME ZONE 'UTC'::text)) AND (period_end = (date_trunc('hour'::text, (period_end AT TIME ZONE 'UTC'::text)) AT TIME ZONE 'UTC'::text))))
- check `audit_export_manifest_seq_chk`: CHECK ((seq >= 1))
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_export_manifest_append_only`: BEFORE DELETE OR UPDATE ON crm.audit_export_manifest FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `audit_export_manifest_chain`: BEFORE INSERT ON crm.audit_export_manifest FOR EACH ROW EXECUTE FUNCTION crm.audit_manifest_chain()
- trigger `audit_export_manifest_no_truncate`: BEFORE TRUNCATE ON crm.audit_export_manifest FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.audit_export_tenant` (table, 24 kB)
```
tenant_id uuid NN
exported_until timestamp with time zone NN
verified_until timestamp with time zone
last_seq bigint NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `crm_owner` · RLS on
- index `audit_export_tenant_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- check `audit_export_tenant_hour_chk`: CHECK (((exported_until = (date_trunc('hour'::text, (exported_until AT TIME ZONE 'UTC'::text)) AT TIME ZONE 'UTC'::text)) AND ((verified_until IS NULL) OR (verified_until = (date_trunc('hour'::text, (verified_until AT TIME ZONE 'UTC'::text)) AT TIME ZONE 'UTC'::text)))))
- check `audit_export_tenant_seq_chk`: CHECK ((last_seq >= 0))
- check `audit_export_tenant_verified_chk`: CHECK (((verified_until IS NULL) OR (verified_until <= exported_until)))
- grant `crm_app`: SELECT
- column grant `crm_app`: INSERT (tenant_id)
- column grant `crm_app`: INSERT, UPDATE (exported_until)
- column grant `crm_app`: UPDATE (last_seq)
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_export_tenant_set_updated_at`: BEFORE UPDATE ON crm.audit_export_tenant FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.consent` (table, 48 kB)
```
consent_id uuid NN
tenant_id uuid NN
traveler_id uuid NN
purpose text NN
value boolean NN
at timestamp with time zone NN
source text NN
submission_id uuid
notice_version text
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `consent_pkey` PRIMARY KEY: UNIQUE btree (consent_id)
- index `consent_traveler_idx`: btree (traveler_id, purpose, at DESC)
- check `consent_notice_chk`: CHECK (((notice_version IS NULL) OR (notice_version ~ '^[a-z0-9_.-]{1,40}$'::text)))
- check `consent_purpose_chk`: CHECK ((purpose = ANY (ARRAY['contact'::text, 'marketing'::text, 'health_data'::text, 'ops_release'::text, 'ai_processing'::text, 'terms'::text])))
- check `consent_source_chk`: CHECK ((source = ANY (ARRAY['form'::text, 'portal'::text, 'agent_recorded'::text, 'import'::text])))
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `consent_append_only`: BEFORE DELETE OR UPDATE ON crm.consent FOR EACH ROW EXECUTE FUNCTION crm.erasable_append_only()
- trigger `consent_no_truncate`: BEFORE TRUNCATE ON crm.consent FOR EACH STATEMENT EXECUTE FUNCTION crm.erasable_append_only()

### `crm.dispatch_queue` (table, 32 kB)
```
dispatch_id uuid NN
tenant_id uuid NN
traveler_id uuid NN
trip_id uuid
channel text NN
purpose text NN
origin text NN
message_ref uuid
not_before timestamp with time zone NN
status text NN
gate_result text
attempts smallint NN
decided_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `dispatch_queue_due_idx`: btree (tenant_id, not_before) WHERE (status = 'queued'::text)
- index `dispatch_queue_pkey` PRIMARY KEY: UNIQUE btree (dispatch_id)
- index `dispatch_queue_traveler_idx`: btree (traveler_id)
- check `dispatch_queue_attempts_chk`: CHECK (((attempts >= 0) AND (attempts <= 100)))
- check `dispatch_queue_channel_chk`: CHECK ((channel = ANY (ARRAY['email'::text, 'sms'::text, 'whatsapp'::text])))
- check `dispatch_queue_gate_chk`: CHECK ((((status = 'queued'::text) = (gate_result IS NULL)) AND ((gate_result IS NULL) OR (gate_result = ANY (ARRAY['sent'::text, 'archived'::text, 'traveler_trashed'::text, 'trip_trashed'::text, 'no_consent'::text, 'no_sender'::text, 'undone'::text]))) AND ((status = 'queued'::text) = (decided_at IS NULL))))
- check `dispatch_queue_origin_chk`: CHECK ((origin = ANY (ARRAY['user_action'::text, 'workflow'::text, 'system'::text])))
- check `dispatch_queue_purpose_chk`: CHECK ((purpose = ANY (ARRAY['transactional'::text, 'marketing'::text])))
- check `dispatch_queue_status_chk`: CHECK ((status = ANY (ARRAY['queued'::text, 'held'::text, 'sent'::text, 'dropped'::text, 'cancelled'::text])))
- check `dispatch_queue_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `dispatch_queue_hold_guard`: BEFORE DELETE OR UPDATE ON crm.dispatch_queue FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id')
- trigger `dispatch_queue_set_updated_at`: BEFORE UPDATE ON crm.dispatch_queue FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `dispatch_queue_status_transition`: BEFORE UPDATE OF status ON crm.dispatch_queue FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.document` (table, 40 kB)
```
document_id uuid NN
tenant_id uuid NN
trip_id uuid
traveler_id uuid
kind text NN
s3_key text NN
sha256 bytea NN
size_bytes bigint NN
content_type text NN
filename_enc bytea NN · pii:free_text
visible_to_travelers boolean NN
write_only boolean NN
uploaded_by_kind text NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `document_pkey` PRIMARY KEY: UNIQUE btree (document_id)
- index `document_s3_key_uq`: UNIQUE btree (s3_key)
- index `document_traveler_idx`: btree (traveler_id) WHERE (traveler_id IS NOT NULL)
- index `document_trip_idx`: btree (trip_id) WHERE (trip_id IS NOT NULL)
- check `document_content_type_chk`: CHECK ((content_type = ANY (ARRAY['application/pdf'::text, 'image/jpeg'::text, 'image/png'::text, 'image/webp'::text, 'image/heic'::text])))
- check `document_filename_chk`: CHECK ((octet_length(filename_enc) >= 30))
- check `document_kind_chk`: CHECK ((kind = ANY (ARRAY['passport_scan'::text, 'waiver_pdf'::text, 'terms_pdf'::text, 'ticket'::text, 'voucher'::text, 'invoice_pdf'::text, 'supplier_confirmation'::text, 'other'::text])))
- check `document_s3_key_chk`: CHECK ((s3_key = ((('tenants/'::text || (tenant_id)::text) || '/documents/'::text) || (document_id)::text)))
- check `document_sha256_chk`: CHECK ((octet_length(sha256) = 32))
- check `document_size_chk`: CHECK (((size_bytes >= 1) AND (size_bytes <= 10485760)))
- check `document_subject_chk`: CHECK (((trip_id IS NOT NULL) OR (traveler_id IS NOT NULL)))
- check `document_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- check `document_uploader_chk`: CHECK ((uploaded_by_kind = ANY (ARRAY['member'::text, 'traveler'::text, 'aa_booking'::text])))
- check `document_write_only_chk`: CHECK ((((kind <> 'passport_scan'::text) OR write_only) AND (NOT (write_only AND visible_to_travelers))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `document_hold_guard`: BEFORE DELETE OR UPDATE ON crm.document FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id', 's3_key', 'sha256', 'filename_enc')
- trigger `document_set_updated_at`: BEFORE UPDATE ON crm.document FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.erasure_request` (table, 24 kB)
```
request_id uuid NN
tenant_id uuid NN
scope text NN
subject_id uuid NN
status text NN
requested_by text NN
confirmed_by text
dry_run_counts jsonb NN
export_waived boolean NN
export_object_key text
export_sha256 text
export_expires_at timestamp with time zone
export_downloaded_at timestamp with time zone
executed_at timestamp with time zone
keys_destroyed_at timestamp with time zone
backup_purge_by date
receipt jsonb NN
failure_class text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
purpose text NN
owner_accepted_at timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `erasure_request_open_tenant_uq`: UNIQUE btree (tenant_id) WHERE ((scope = 'tenant'::text) AND (status = ANY (ARRAY['requested'::text, 'export_ready'::text, 'erasing'::text, 'failed'::text])))
- index `erasure_request_pkey` PRIMARY KEY: UNIQUE btree (request_id)
- check `erasure_request_actor_chk`: CHECK (((requested_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text) AND ((confirmed_by IS NULL) OR (confirmed_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text))))
- check `erasure_request_counts_chk`: CHECK (((jsonb_typeof(dry_run_counts) = 'object'::text) AND (octet_length((dry_run_counts)::text) <= 4096) AND (jsonb_typeof(receipt) = 'object'::text) AND (octet_length((receipt)::text) <= 8192)))
- check `erasure_request_done_chk`: CHECK (((status = 'erased'::text) = (executed_at IS NOT NULL)))
- check `erasure_request_export_chk`: CHECK ((((export_object_key IS NULL) = (export_sha256 IS NULL)) AND ((export_object_key IS NULL) = (export_expires_at IS NULL)) AND ((export_object_key IS NULL) OR (export_object_key ~ '^exports/tenants/[0-9a-f-]{36}/[0-9a-f-]{36}\.jsonl\.enc$'::text)) AND ((export_sha256 IS NULL) OR (export_sha256 ~ '^[0-9a-f]{64}$'::text)) AND (NOT (export_waived AND (export_object_key IS NOT NULL)))))
- check `erasure_request_failure_chk`: CHECK (((failure_class IS NULL) OR (failure_class ~ '^[A-Za-z][A-Za-z0-9_]{0,63}$'::text)))
- check `erasure_request_purpose_chk`: CHECK (((purpose = ANY (ARRAY['offboard'::text, 'export_only'::text])) AND ((purpose = 'offboard'::text) OR (scope = 'tenant'::text))))
- check `erasure_request_scope_chk`: CHECK (((scope = ANY (ARRAY['traveler'::text, 'tenant'::text])) AND ((scope <> 'tenant'::text) OR (subject_id = tenant_id))))
- check `erasure_request_status_chk`: CHECK ((status = ANY (ARRAY['requested'::text, 'export_ready'::text, 'erasing'::text, 'erased'::text, 'cancelled'::text, 'failed'::text])))
- check `erasure_request_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `erasure_request_owner_confirm`: BEFORE INSERT OR UPDATE ON crm.erasure_request FOR EACH ROW EXECUTE FUNCTION crm.guard_erasure_request_owner_confirm()
- trigger `erasure_request_set_updated_at`: BEFORE UPDATE ON crm.erasure_request FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `erasure_request_status_transition`: BEFORE UPDATE OF status ON crm.erasure_request FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.form_definition` (table, 48 kB)
```
form_definition_id uuid NN
tenant_id uuid NN
stage text NN
version integer NN
schema_key text NN
schema jsonb NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `form_definition_pkey` PRIMARY KEY: UNIQUE btree (form_definition_id)
- index `form_definition_version_uq`: UNIQUE btree (tenant_id, stage, version)
- check `form_definition_schema_chk`: CHECK (((jsonb_typeof(schema) = 'object'::text) AND (octet_length((schema)::text) <= 65536)))
- check `form_definition_schema_key_chk`: CHECK ((schema_key ~ '^[a-z][a-z0-9_.]{0,39}$'::text))
- check `form_definition_stage_chk`: CHECK ((stage = ANY (ARRAY['s1'::text, 's2'::text, 's3'::text])))
- check `form_definition_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- check `form_definition_version_chk`: CHECK (((version >= 1) AND (version <= 100000)))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `form_definition_set_updated_at`: BEFORE UPDATE ON crm.form_definition FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.form_submission` (table, 112 kB)
```
submission_id uuid NN
tenant_id uuid NN
intake_form_id uuid NN
stage text NN
schema_key text NN
payload_enc bytea · pii:contact
idempotency_key text NN
hidden_answers_dropped integer NN
status text NN
outcome text
failure_class text
trip_id uuid
traveler_id uuid
processed_at timestamp with time zone
redact_after timestamp with time zone NN
payload_redacted_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `form_submission_idempotency_uq`: UNIQUE btree (tenant_id, idempotency_key)
- index `form_submission_pkey` PRIMARY KEY: UNIQUE btree (submission_id)
- index `form_submission_redact_idx`: btree (redact_after) WHERE (payload_redacted_at IS NULL)
- index `form_submission_trip_idx`: btree (trip_id) WHERE (trip_id IS NOT NULL)
- check `form_submission_dropped_chk`: CHECK (((hidden_answers_dropped >= 0) AND (hidden_answers_dropped <= 1000)))
- check `form_submission_failure_chk`: CHECK (((failure_class IS NULL) OR (failure_class ~ '^[A-Za-z][A-Za-z0-9_]{0,63}$'::text)))
- check `form_submission_idempotency_chk`: CHECK ((idempotency_key ~ '^[A-Za-z0-9:_-]{8,80}$'::text))
- check `form_submission_outcome_chk`: CHECK ((((status = 'processed'::text) = (outcome IS NOT NULL)) AND ((outcome IS NULL) OR (outcome = ANY (ARRAY['created'::text, 'attached'::text])))))
- check `form_submission_payload_chk`: CHECK ((((payload_enc IS NOT NULL) AND (octet_length(payload_enc) >= 30)) OR (payload_redacted_at IS NOT NULL)))
- check `form_submission_schema_key_chk`: CHECK ((schema_key ~ '^[a-z][a-z0-9_.]{0,39}$'::text))
- check `form_submission_stage_chk`: CHECK ((stage = ANY (ARRAY['s1'::text, 's2'::text, 's3'::text])))
- check `form_submission_status_chk`: CHECK ((status = ANY (ARRAY['received'::text, 'processed'::text, 'failed'::text])))
- check `form_submission_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `form_submission_hold_guard`: BEFORE DELETE OR UPDATE ON crm.form_submission FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id', 'payload_enc')
- trigger `form_submission_set_updated_at`: BEFORE UPDATE ON crm.form_submission FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `form_submission_status_transition`: BEFORE UPDATE OF status ON crm.form_submission FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.intake_form` (table, 48 kB)
```
intake_form_id uuid NN
tenant_id uuid NN
public_key text NN
label text NN
form_definition_id uuid NN
allowed_origins text[] NN
honeypot_field text NN
default_owner_member_id uuid
lead_source text NN
privacy_notice_url text
status text NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `intake_form_pkey` PRIMARY KEY: UNIQUE btree (intake_form_id)
- index `intake_form_public_key_uq`: UNIQUE btree (public_key)
- check `intake_form_honeypot_chk`: CHECK ((honeypot_field ~ '^[a-z][a-z_]{2,30}$'::text))
- check `intake_form_label_chk`: CHECK ((((length(btrim(label)) >= 1) AND (length(btrim(label)) <= 80)) AND (label = btrim(label))))
- check `intake_form_lead_source_chk`: CHECK ((lead_source ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `intake_form_origins_chk`: CHECK (((cardinality(allowed_origins) <= 10) AND (array_to_string(allowed_origins, ' '::text, '!'::text) ~ '^(https://[a-z0-9.-]+(:[0-9]{1,5})?( |$))*$'::text)))
- check `intake_form_privacy_url_chk`: CHECK (((privacy_notice_url IS NULL) OR ((privacy_notice_url ~ '^https://[^\s]+$'::text) AND (length(privacy_notice_url) <= 500))))
- check `intake_form_public_key_chk`: CHECK ((public_key ~ '^[A-Za-z0-9_-]{20,64}$'::text))
- check `intake_form_status_chk`: CHECK ((status = ANY (ARRAY['active'::text, 'disabled'::text])))
- check `intake_form_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `intake_form_public_lookup` (PERMISSIVE SELECT TO crm_app): USING `((status = 'active'::text) AND (deleted_at IS NULL) AND (public_key = NULLIF(current_setting('app.intake_key'::text, true), ''::text)))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `intake_form_set_updated_at`: BEFORE UPDATE ON crm.intake_form FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `intake_form_status_transition`: BEFORE UPDATE OF status ON crm.intake_form FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.integration_credential` (table, 24 kB)
```
integration_credential_id uuid NN
tenant_id uuid NN
provider text NN
account_ref text · pii:contact
secret_enc bytea NN · conf:credential
status text NN
failure_class text
last_checked_at timestamp with time zone
last_ok_at timestamp with time zone
last_test_at timestamp with time zone
last_test_result text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `integration_credential_pkey` PRIMARY KEY: UNIQUE btree (integration_credential_id)
- index `integration_credential_provider_uq`: UNIQUE btree (tenant_id, provider)
- check `integration_credential_account_ref_chk`: CHECK (((account_ref IS NULL) OR ((length(account_ref) >= 1) AND (length(account_ref) <= 320))))
- check `integration_credential_failure_chk`: CHECK (((failure_class IS NULL) OR (failure_class = ANY (ARRAY['auth_revoked'::text, 'permission_missing'::text, 'vendor_rejected'::text, 'rate_limited'::text, 'unreachable'::text]))))
- check `integration_credential_failure_state_chk`: CHECK (((failure_class IS NULL) OR (status = ANY (ARRAY['needs_attention'::text, 'disconnected'::text]))))
- check `integration_credential_provider_chk`: CHECK ((provider = ANY (ARRAY['twilio'::text, 'stripe_key'::text, 'stripe_webhook_secret'::text, 'google'::text, 'microsoft'::text, 'smtp'::text, 'esign'::text])))
- check `integration_credential_secret_chk`: CHECK (((octet_length(secret_enc) >= 30) AND (octet_length(secret_enc) <= 16384)))
- check `integration_credential_status_chk`: CHECK ((status = ANY (ARRAY['not_set_up'::text, 'connected'::text, 'needs_attention'::text, 'disconnected'::text])))
- check `integration_credential_test_result_chk`: CHECK (((last_test_result IS NULL) OR (last_test_result = ANY (ARRAY['ok'::text, 'failed'::text]))))
- check `integration_credential_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `integration_credential_set_updated_at`: BEFORE UPDATE ON crm.integration_credential FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `integration_credential_status_transition`: BEFORE UPDATE OF status ON crm.integration_credential FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.job` (table, ~1852 rows, 968 kB)
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
- owner `crm_owner`
- index `job_finished_idx`: btree (finished_at, id) WHERE (finished_at IS NOT NULL)
- index `job_idempotency_key_uq`: UNIQUE btree (idempotency_key) WHERE (idempotency_key IS NOT NULL)
- index `job_kind_created_idx`: btree (kind, created_at DESC)
- index `job_parent_idx`: btree (parent_job_id) WHERE (parent_job_id IS NOT NULL)
- index `job_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `job_queued_due_idx`: btree (run_after, created_at) WHERE (status = 'queued'::text)
- index `job_running_idx`: btree (kind, locked_until) WHERE (status = 'running'::text)
- check `job_attempts_chk`: CHECK (((attempt >= 0) AND (max_attempts >= 1)))
- check `job_kind_chk`: CHECK ((kind ~ '^crm_[a-z0-9_]+$'::text))
- check `job_lease_chk`: CHECK (((status <> 'running'::text) OR ((locked_by IS NOT NULL) AND (locked_until IS NOT NULL))))
- check `job_status_chk`: CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text, 'cancelled'::text])))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `job_set_updated_at`: BEFORE UPDATE ON crm.job FOR EACH ROW EXECUTE FUNCTION crm.job_set_updated_at()

### `crm.legal_hold` (table, 24 kB)
```
hold_id uuid NN
tenant_id uuid NN
scope text NN
subject_id uuid
reason_code text NN
status text NN
placed_by text NN
released_at timestamp with time zone
released_by text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `legal_hold_active_uq`: UNIQUE btree (tenant_id, scope, COALESCE(subject_id, '00000000-0000-0000-0000-000000000000'::uuid)) WHERE (status = 'active'::text)
- index `legal_hold_pkey` PRIMARY KEY: UNIQUE btree (hold_id)
- check `legal_hold_actor_chk`: CHECK (((placed_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text) AND ((released_by IS NULL) OR (released_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text))))
- check `legal_hold_never_trashed_chk`: CHECK (((deleted_at IS NULL) AND (deleted_by IS NULL) AND (purge_after IS NULL)))
- check `legal_hold_reason_chk`: CHECK ((reason_code = ANY (ARRAY['litigation'::text, 'regulator_request'::text, 'dispute'::text, 'insurance_claim'::text, 'other'::text])))
- check `legal_hold_release_chk`: CHECK ((((status = 'released'::text) = (released_at IS NOT NULL)) AND ((released_at IS NULL) = (released_by IS NULL))))
- check `legal_hold_scope_chk`: CHECK (((scope = ANY (ARRAY['tenant'::text, 'trip'::text, 'traveler'::text])) AND ((scope = 'tenant'::text) = (subject_id IS NULL))))
- check `legal_hold_status_chk`: CHECK ((status = ANY (ARRAY['active'::text, 'released'::text])))
- check `legal_hold_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `legal_hold_guard`: BEFORE UPDATE ON crm.legal_hold FOR EACH ROW EXECUTE FUNCTION crm.guard_legal_hold()
- trigger `legal_hold_set_updated_at`: BEFORE UPDATE ON crm.legal_hold FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `legal_hold_status_transition`: BEFORE UPDATE OF status ON crm.legal_hold FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.lifecycle_run` (table, 24 kB)
```
run_id uuid NN
tenant_id uuid NN
kind text NN
dry_run boolean NN
counts jsonb NN
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `lifecycle_run_pkey` PRIMARY KEY: UNIQUE btree (run_id)
- index `lifecycle_run_tenant_idx`: btree (tenant_id, created_at DESC)
- check `lifecycle_run_counts_chk`: CHECK (((jsonb_typeof(counts) = 'object'::text) AND (octet_length((counts)::text) <= 4096) AND (NOT jsonb_path_exists(counts, '$.*?(@.type() != "number")'::jsonpath))))
- check `lifecycle_run_kind_chk`: CHECK ((kind ~ '^crm_[a-z0-9_]{1,40}$'::text))
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `lifecycle_run_append_only`: BEFORE DELETE OR UPDATE ON crm.lifecycle_run FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `lifecycle_run_no_truncate`: BEFORE TRUNCATE ON crm.lifecycle_run FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.llm_call` (table, 32 kB)
```
llm_call_id uuid NN
tenant_id uuid NN
at timestamp with time zone NN
stage text NN
role text NN
provider text NN
model text NN
input_tokens integer NN
output_tokens integer NN
cost_usd_est numeric(12,6) NN
latency_ms integer NN
outcome text NN
refusal_code text
error_class text
scrub_receipt jsonb NN
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `llm_call_pkey` PRIMARY KEY: UNIQUE btree (llm_call_id)
- index `llm_call_tenant_at_idx`: btree (tenant_id, at DESC)
- index `llm_call_tenant_id_uq`: UNIQUE btree (tenant_id, llm_call_id)
- check `llm_call_cost_chk`: CHECK ((cost_usd_est >= (0)::numeric))
- check `llm_call_error_chk`: CHECK (((error_class IS NULL) OR (error_class ~ '^[A-Za-z][A-Za-z0-9_]{0,63}$'::text)))
- check `llm_call_model_chk`: CHECK ((model ~ '^[A-Za-z0-9._:/-]{1,120}$'::text))
- check `llm_call_outcome_chk`: CHECK ((outcome = ANY (ARRAY['ok'::text, 'refused'::text, 'error'::text])))
- check `llm_call_provider_chk`: CHECK ((provider ~ '^[a-z][a-z0-9_]{0,30}$'::text))
- check `llm_call_receipt_chk`: CHECK (((jsonb_typeof(scrub_receipt) = 'object'::text) AND (octet_length((scrub_receipt)::text) <= 2048)))
- check `llm_call_receipt_keys_chk`: CHECK ((((scrub_receipt - ARRAY['scrubber'::text, 'detector'::text, 'entities'::text, 'counts'::text, 'passes'::text, 'known_persons'::text]) = '{}'::jsonb) AND ((NOT (scrub_receipt ? 'scrubber'::text)) OR ((jsonb_typeof((scrub_receipt -> 'scrubber'::text)) = 'string'::text) AND ((scrub_receipt ->> 'scrubber'::text) ~ '^[a-z0-9][a-z0-9.-]{0,19}$'::text))) AND ((NOT (scrub_receipt ? 'detector'::text)) OR ((jsonb_typeof((scrub_receipt -> 'detector'::text)) = 'string'::text) AND ((scrub_receipt ->> 'detector'::text) ~ '^[a-z0-9][a-z0-9_.-]{0,39}$'::text))) AND ((NOT (scrub_receipt ? 'entities'::text)) OR (jsonb_typeof((scrub_receipt -> 'entities'::text)) = 'number'::text)) AND ((NOT (scrub_receipt ? 'known_persons'::text)) OR (jsonb_typeof((scrub_receipt -> 'known_persons'::text)) = 'number'::text)) AND ((NOT (scrub_receipt ? 'counts'::text)) OR ((jsonb_typeof((scrub_receipt -> 'counts'::text)) = 'object'::text) AND (NOT jsonb_path_exists((scrub_receipt -> 'counts'::text), 'strict $.keyvalue()?(!(@."key" like_regex "^[A-Z][A-Z_]{1,23}$") || @."value".type() != "number")'::jsonpath)))) AND ((NOT (scrub_receipt ? 'passes'::text)) OR ((jsonb_typeof((scrub_receipt -> 'passes'::text)) = 'object'::text) AND (((scrub_receipt -> 'passes'::text) - ARRAY['known'::text, 'regex'::text, 'detector'::text]) = '{}'::jsonb) AND (NOT jsonb_path_exists((scrub_receipt -> 'passes'::text), 'strict $.keyvalue()?(@."value".type() != "number")'::jsonpath))))))
- check `llm_call_refusal_chk`: CHECK ((((outcome = 'refused'::text) = (refusal_code IS NOT NULL)) AND ((refusal_code IS NULL) OR (refusal_code ~ '^[a-z][a-z0-9_]{0,39}$'::text))))
- check `llm_call_role_chk`: CHECK ((role = ANY (ARRAY['writer'::text, 'judge'::text, 'validate'::text])))
- check `llm_call_stage_chk`: CHECK ((stage ~ '^crm_[a-z0-9_]{1,40}$'::text))
- check `llm_call_tokens_chk`: CHECK (((input_tokens >= 0) AND (output_tokens >= 0) AND (latency_ms >= 0)))
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `llm_call_append_only`: BEFORE DELETE OR UPDATE ON crm.llm_call FOR EACH ROW EXECUTE FUNCTION crm.erasable_append_only()
- trigger `llm_call_no_truncate`: BEFORE TRUNCATE ON crm.llm_call FOR EACH STATEMENT EXECUTE FUNCTION crm.erasable_append_only()

### `crm.llm_usage_daily` (table, 16 kB)
```
day date NN
stage text NN
model text NN
calls integer NN
failed_calls integer NN
input_tokens bigint NN
output_tokens bigint NN
cost_usd numeric(14,6) NN
updated_at timestamp with time zone NN
```
- owner `crm_owner`
- index `llm_usage_daily_pkey` PRIMARY KEY: UNIQUE btree (day, stage, model)
- check `llm_usage_daily_counts_chk`: CHECK (((calls >= 0) AND (failed_calls >= 0) AND (failed_calls <= calls) AND (input_tokens >= 0) AND (output_tokens >= 0) AND (cost_usd >= (0)::numeric)))
- check `llm_usage_daily_model_chk`: CHECK ((model ~ '^[A-Za-z0-9._:/-]{1,120}$'::text))
- check `llm_usage_daily_stage_chk`: CHECK ((stage ~ '^crm_[a-z0-9_]{1,40}$'::text))
- grant `crm_app`: INSERT, SELECT, UPDATE

### `crm.member` (table, ~6 rows, 80 kB)
```
member_id uuid NN
tenant_id uuid NN
cognito_iss text NN
cognito_sub text NN
role text NN
status text NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `member_identity_idx`: btree (cognito_iss, cognito_sub) WHERE (deleted_at IS NULL)
- index `member_identity_uq`: UNIQUE btree (tenant_id, cognito_iss, cognito_sub)
- index `member_pkey` PRIMARY KEY: UNIQUE btree (member_id)
- index `member_tenant_member_uq`: UNIQUE btree (tenant_id, member_id)
- check `member_iss_chk`: CHECK ((cognito_iss ~ '^https://[^/]+/[^/]+$'::text))
- check `member_role_chk`: CHECK ((role = ANY (ARRAY['owner'::text, 'agent'::text, 'assistant'::text])))
- check `member_status_chk`: CHECK ((status = ANY (ARRAY['invited'::text, 'active'::text, 'disabled'::text])))
- check `member_sub_chk`: CHECK (((length(cognito_sub) >= 1) AND (length(cognito_sub) <= 128)))
- check `member_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `member_self_lookup` (PERMISSIVE SELECT TO crm_app): USING `((deleted_at IS NULL) AND (cognito_iss = NULLIF(current_setting('app.caller_iss'::text, true), ''::text)) AND (cognito_sub = NULLIF(current_setting('app.caller_sub'::text, true), ''::text)))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `member_guard_write`: BEFORE INSERT OR DELETE OR UPDATE ON crm.member FOR EACH ROW EXECUTE FUNCTION crm.guard_member_write()
- trigger `member_set_updated_at`: BEFORE UPDATE ON crm.member FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `member_status_transition`: BEFORE UPDATE OF status ON crm.member FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.member_invitation` (table, 80 kB)
```
invitation_id uuid NN
tenant_id uuid NN
role text NN
email_enc bytea NN
email_bidx bytea NN
token_hash bytea NN
status text NN
expires_at timestamp with time zone NN
cognito_iss text
cognito_sub text
claimed_at timestamp with time zone
accepted_at timestamp with time zone
member_id uuid
invited_by text NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `member_invitation_live_email_uq`: UNIQUE btree (tenant_id, email_bidx) WHERE ((status = ANY (ARRAY['pending'::text, 'claimed'::text])) AND (deleted_at IS NULL))
- index `member_invitation_pkey` PRIMARY KEY: UNIQUE btree (invitation_id)
- index `member_invitation_tenant_status_idx`: btree (tenant_id, status, created_at DESC)
- index `member_invitation_token_uq`: UNIQUE btree (token_hash)
- check `member_invitation_accept_chk`: CHECK (((status = 'accepted'::text) = ((accepted_at IS NOT NULL) AND (member_id IS NOT NULL))))
- check `member_invitation_bidx_chk`: CHECK (((octet_length(email_bidx) >= 8) AND (octet_length(email_bidx) <= 64)))
- check `member_invitation_claim_chk`: CHECK ((((status = 'pending'::text) AND (cognito_sub IS NULL) AND (claimed_at IS NULL)) OR ((status = ANY (ARRAY['claimed'::text, 'accepted'::text])) AND (cognito_sub IS NOT NULL) AND (claimed_at IS NOT NULL)) OR (status = ANY (ARRAY['revoked'::text, 'expired'::text]))))
- check `member_invitation_expiry_chk`: CHECK (((expires_at > created_at) AND (expires_at <= (created_at + '30 days'::interval))))
- check `member_invitation_identity_chk`: CHECK ((((cognito_iss IS NULL) = (cognito_sub IS NULL)) AND ((cognito_iss IS NULL) OR ((cognito_iss ~ '^https://[^/]+/[^/]+$'::text) AND ((length(cognito_sub) >= 1) AND (length(cognito_sub) <= 128))))))
- check `member_invitation_role_chk`: CHECK ((role = ANY (ARRAY['owner'::text, 'agent'::text, 'assistant'::text])))
- check `member_invitation_status_chk`: CHECK ((status = ANY (ARRAY['pending'::text, 'claimed'::text, 'accepted'::text, 'revoked'::text, 'expired'::text])))
- check `member_invitation_token_chk`: CHECK ((octet_length(token_hash) = 32))
- check `member_invitation_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `invitation_token_lookup` (PERMISSIVE SELECT TO crm_app): USING `(token_hash = decode(NULLIF(current_setting('app.invite_token_hash'::text, true), ''::text), 'hex'::text))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `member_invitation_guard_write`: BEFORE INSERT OR UPDATE ON crm.member_invitation FOR EACH ROW EXECUTE FUNCTION crm.guard_invitation_write()
- trigger `member_invitation_set_updated_at`: BEFORE UPDATE ON crm.member_invitation FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `member_invitation_status_transition`: BEFORE UPDATE OF status ON crm.member_invitation FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.note` (table, 48 kB)
```
note_id uuid NN
tenant_id uuid NN
trip_id uuid
traveler_id uuid
kind text NN
body_enc bytea NN · pii:free_text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `note_pkey` PRIMARY KEY: UNIQUE btree (note_id)
- index `note_trip_idx`: btree (trip_id, created_at) WHERE (trip_id IS NOT NULL)
- check `note_body_chk`: CHECK ((octet_length(body_enc) >= 30))
- check `note_kind_chk`: CHECK ((kind = ANY (ARRAY['internal'::text, 'call_log'::text, 'stage2_free_text'::text, 'inquiry_message'::text])))
- check `note_subject_chk`: CHECK (((trip_id IS NOT NULL) OR (traveler_id IS NOT NULL)))
- check `note_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `note_hold_guard`: BEFORE DELETE OR UPDATE ON crm.note FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id', 'body_enc', 'kind')
- trigger `note_set_updated_at`: BEFORE UPDATE ON crm.note FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.owner_recovery_request` (table, 24 kB)
```
request_id uuid NN
tenant_id uuid NN
candidate_member_id uuid NN
reason text NN
status text NN
eligible_at timestamp with time zone NN
requested_by text NN
decided_at timestamp with time zone
decided_by text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `owner_recovery_one_pending_uq`: UNIQUE btree (tenant_id) WHERE ((status = 'pending'::text) AND (deleted_at IS NULL))
- index `owner_recovery_request_pkey` PRIMARY KEY: UNIQUE btree (request_id)
- check `owner_recovery_actor_chk`: CHECK (((requested_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text) AND ((decided_by IS NULL) OR (decided_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text))))
- check `owner_recovery_decided_chk`: CHECK ((((status = 'pending'::text) = (decided_at IS NULL)) AND ((decided_at IS NULL) = (decided_by IS NULL))))
- check `owner_recovery_reason_chk`: CHECK ((reason = ANY (ARRAY['owner_left'::text, 'owner_unreachable'::text, 'no_owner'::text])))
- check `owner_recovery_request_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- check `owner_recovery_status_chk`: CHECK ((status = ANY (ARRAY['pending'::text, 'cancelled'::text, 'completed'::text])))
- check `owner_recovery_wait_chk`: CHECK ((eligible_at >= (created_at + '14 days'::interval)))
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `owner_recovery_guard`: BEFORE INSERT OR UPDATE ON crm.owner_recovery_request FOR EACH ROW EXECUTE FUNCTION crm.guard_owner_recovery()
- trigger `owner_recovery_set_updated_at`: BEFORE UPDATE ON crm.owner_recovery_request FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `owner_recovery_status_transition`: BEFORE UPDATE OF status ON crm.owner_recovery_request FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.placeholder_map` (table, 32 kB)
```
placeholder_map_id uuid NN
tenant_id uuid NN
llm_call_id uuid NN
ai_draft_id uuid
map_enc bytea NN · pii:free_text
placeholder_count integer NN
scrubber_version text NN
expires_at timestamp with time zone NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `placeholder_map_call_uq`: UNIQUE btree (llm_call_id)
- index `placeholder_map_expires_idx`: btree (expires_at)
- index `placeholder_map_pkey` PRIMARY KEY: UNIQUE btree (placeholder_map_id)
- check `placeholder_map_count_chk`: CHECK (((placeholder_count >= 1) AND (placeholder_count <= 500)))
- check `placeholder_map_enc_chk`: CHECK (((octet_length(map_enc) >= 30) AND (octet_length(map_enc) <= 65536)))
- check `placeholder_map_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- check `placeholder_map_ttl_chk`: CHECK (((expires_at > created_at) AND (expires_at <= (created_at + '24:00:00'::interval))))
- check `placeholder_map_version_chk`: CHECK ((scrubber_version ~ '^[a-z0-9][a-z0-9.-]{0,19}$'::text))
- grant `crm_app`: DELETE, INSERT, SELECT
- policy `placeholder_map_expired_purge` (PERMISSIVE DELETE TO crm_app): USING `((current_setting('app.purge_scope'::text, true) = 'placeholder_map'::text) AND (expires_at < now()))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `placeholder_map_set_updated_at`: BEFORE UPDATE ON crm.placeholder_map FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.profile_history` (table, 24 kB)
```
history_id uuid NN
tenant_id uuid NN
traveler_token uuid NN
aa_departure_id text
aa_product_key text
stage_reached text NN
year_month date NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `profile_history_pkey` PRIMARY KEY: UNIQUE btree (history_id)
- index `profile_history_token_idx`: btree (traveler_token, year_month DESC)
- check `profile_history_ids_chk`: CHECK ((((aa_departure_id IS NULL) OR (aa_departure_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)) AND ((aa_product_key IS NULL) OR (aa_product_key ~ '^[A-Za-z0-9:_./-]{1,120}$'::text))))
- check `profile_history_month_chk`: CHECK ((year_month = (date_trunc('month'::text, (year_month)::timestamp with time zone))::date))
- check `profile_history_stage_chk`: CHECK ((stage_reached = ANY (ARRAY['inquiry'::text, 'qualifying'::text, 'proposal'::text, 'booked'::text, 'pre_departure'::text, 'travelling'::text, 'completed'::text, 'lost'::text, 'cancelled'::text])))
- check `profile_history_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `profile_history_set_updated_at`: BEFORE UPDATE ON crm.profile_history FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.status_transition` (table, ~57 rows, 32 kB)
```
table_name text NN
from_status text NN
to_status text NN
```
- owner `crm_owner`
- index `status_transition_pkey` PRIMARY KEY: UNIQUE btree (table_name, from_status, to_status)
- check `status_transition_names_chk`: CHECK (((table_name ~ '^[a-z][a-z0-9_]*$'::text) AND (from_status ~ '^[a-z][a-z0-9_]*$'::text) AND (to_status ~ '^[a-z][a-z0-9_]*$'::text) AND (from_status <> to_status)))
- grant `crm_app`: SELECT

### `crm.task` (table, 80 kB)
```
task_id uuid NN
tenant_id uuid NN
trip_id uuid
kind text NN
assignee_member_id uuid
status text NN
due_anchor text
due_offset_days smallint
due_at timestamp with time zone
due_overridden boolean NN
done_at timestamp with time zone
done_by text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `task_open_idx`: btree (tenant_id, assignee_member_id, due_at) WHERE ((status = 'open'::text) AND (deleted_at IS NULL))
- index `task_open_kind_uq`: UNIQUE btree (trip_id, kind) WHERE ((status = 'open'::text) AND (deleted_at IS NULL) AND (trip_id IS NOT NULL))
- index `task_pkey` PRIMARY KEY: UNIQUE btree (task_id)
- index `task_trip_idx`: btree (trip_id) WHERE (trip_id IS NOT NULL)
- check `task_anchor_chk`: CHECK (((due_anchor IS NULL) OR (due_anchor = ANY (ARRAY['departure'::text, 'return'::text, 'created'::text, 'stage_entered'::text, 'hold_expiry'::text, 'deposit_paid'::text, 'ops_handoff'::text]))))
- check `task_done_chk`: CHECK ((((status = 'open'::text) = (done_at IS NULL)) AND ((done_at IS NULL) = (done_by IS NULL))))
- check `task_kind_chk`: CHECK ((kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `task_offset_chk`: CHECK (((due_offset_days IS NULL) OR ((due_offset_days >= '-365'::integer) AND (due_offset_days <= 365))))
- check `task_status_chk`: CHECK ((status = ANY (ARRAY['open'::text, 'done'::text, 'skipped'::text])))
- check `task_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `task_hold_guard`: BEFORE DELETE OR UPDATE ON crm.task FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `task_set_updated_at`: BEFORE UPDATE ON crm.task FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `task_status_transition`: BEFORE UPDATE OF status ON crm.task FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.tenant` (table, 32 kB)
```
tenant_id uuid NN
status text NN
is_synthetic boolean NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
display_name text NN
default_locale text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `tenant_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- check `tenant_default_locale_chk`: CHECK ((default_locale = ANY (ARRAY['en-AU'::text, 'en-GB'::text, 'en-US'::text, 'vi-VN'::text])))
- check `tenant_display_name_chk`: CHECK ((((length(btrim(display_name)) >= 1) AND (length(btrim(display_name)) <= 120)) AND (display_name = btrim(display_name))))
- check `tenant_status_chk`: CHECK ((status = ANY (ARRAY['active'::text, 'locked'::text, 'offboarding'::text, 'offboarded'::text])))
- check `tenant_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- policy `tenant_member_lookup` (PERMISSIVE SELECT TO crm_app): USING `((deleted_at IS NULL) AND (EXISTS ( SELECT 1
   FROM crm.member m
  WHERE ((m.tenant_id = tenant.tenant_id) AND (m.status = 'active'::text) AND (m.deleted_at IS NULL) AND (m.cognito_iss = NULLIF(current_setting('app.caller_iss'::text, true), ''::text)) AND (m.cognito_sub = NULLIF(current_setting('app.caller_sub'::text, true), ''::text))))))`
- trigger `tenant_audit_register`: AFTER INSERT ON crm.tenant FOR EACH ROW EXECUTE FUNCTION crm.audit_register_tenant()
- trigger `tenant_set_updated_at`: BEFORE UPDATE ON crm.tenant FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `tenant_status_transition`: BEFORE UPDATE OF status ON crm.tenant FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.tenant_entitlement` (table, 16 kB)
```
tenant_id uuid NN
plan text NN
member_limit integer NN
allowed_features text[] NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
insights_opt_out boolean NN
```
- owner `crm_owner` · RLS on + FORCE
- index `tenant_entitlement_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- check `tenant_entitlement_features_chk`: CHECK ((allowed_features <@ ARRAY['ai_assist'::text, 'whatsapp_sms'::text, 'stripe_connect'::text, 'campaigns'::text, 'custom_domain'::text, 'insights_export'::text]))
- check `tenant_entitlement_limit_chk`: CHECK (((member_limit >= 1) AND (member_limit <= 500)))
- check `tenant_entitlement_plan_chk`: CHECK ((plan = ANY (ARRAY['free'::text, 'core'::text, 'pro'::text])))
- check `tenant_entitlement_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `tenant_entitlement_platform_only`: BEFORE INSERT OR UPDATE ON crm.tenant_entitlement FOR EACH ROW EXECUTE FUNCTION crm.guard_platform_write()
- trigger `tenant_entitlement_set_updated_at`: BEFORE UPDATE ON crm.tenant_entitlement FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.tenant_key` (table, 64 kB)
```
tenant_key_id uuid NN
tenant_id uuid NN
purpose text NN
key_version integer NN
kek_provider text NN
kek_id text NN
wrapped_dek bytea · conf:credential
encryption_context jsonb NN
rewrapped_at timestamp with time zone
retired_at timestamp with time zone
destroyed_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `tenant_key_current_uq`: UNIQUE btree (tenant_id, purpose) WHERE (retired_at IS NULL)
- index `tenant_key_pkey` PRIMARY KEY: UNIQUE btree (tenant_key_id)
- index `tenant_key_version_uq`: UNIQUE btree (tenant_id, purpose, key_version)
- check `tenant_key_context_chk`: CHECK ((encryption_context = jsonb_build_object('tenant_id', (tenant_id)::text, 'purpose', purpose)))
- check `tenant_key_destroyed_chk`: CHECK ((((destroyed_at IS NULL) = (wrapped_dek IS NOT NULL)) AND ((destroyed_at IS NULL) OR (retired_at IS NOT NULL))))
- check `tenant_key_kek_id_chk`: CHECK (((length(kek_id) >= 1) AND (length(kek_id) <= 2048)))
- check `tenant_key_kek_provider_chk`: CHECK ((kek_provider = ANY (ARRAY['kms'::text, 'local'::text])))
- check `tenant_key_purpose_chk`: CHECK ((purpose = ANY (ARRAY['vault'::text, 'docs'::text, 'integration'::text, 'scrub'::text, 'ops_release'::text, 'export'::text, 'mail'::text])))
- check `tenant_key_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- check `tenant_key_version_chk`: CHECK (((key_version >= 1) AND (key_version <= 65535)))
- check `tenant_key_wrapped_chk`: CHECK (((wrapped_dek IS NULL) OR ((octet_length(wrapped_dek) >= 32) AND (octet_length(wrapped_dek) <= 4096))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `tenant_key_guard`: BEFORE DELETE OR UPDATE ON crm.tenant_key FOR EACH ROW EXECUTE FUNCTION crm.tenant_key_guard()
- trigger `tenant_key_set_updated_at`: BEFORE UPDATE ON crm.tenant_key FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.tenant_settings` (table, 16 kB)
```
tenant_id uuid NN
ai_enabled boolean NN
ai_budget_usd numeric(10,2) NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
refund_owner_threshold_base numeric(12,2) NN
trash_days smallint NN
auto_archive_months smallint NN
```
- owner `crm_owner` · RLS on + FORCE
- index `tenant_settings_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- check `tenant_settings_auto_archive_chk`: CHECK (((auto_archive_months >= 12) AND (auto_archive_months <= 120)))
- check `tenant_settings_budget_chk`: CHECK (((ai_budget_usd >= (0)::numeric) AND (ai_budget_usd <= (10000)::numeric)))
- check `tenant_settings_refund_threshold_chk`: CHECK (((refund_owner_threshold_base >= (0)::numeric) AND (refund_owner_threshold_base <= (10000000)::numeric)))
- check `tenant_settings_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- check `tenant_settings_trash_days_chk`: CHECK (((trash_days >= 1) AND (trash_days <= 30)))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `tenant_settings_set_updated_at`: BEFORE UPDATE ON crm.tenant_settings FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.traveler` (table, ~8 rows, 136 kB)
```
traveler_id uuid NN
tenant_id uuid NN
given_name_enc bytea · pii:name
family_name_enc bytea · pii:name
display_name_enc bytea NN · pii:name
email_enc bytea · pii:contact
phone_enc bytea · pii:contact
preferred_channel text
email_bidx bytea · pii:contact
phone_bidx bytea · pii:contact
name_bidx bytea · pii:name
name_token_bidx bytea[] NN · pii:name
dob_enc bytea · pii:government_id
nationality_enc bytea · pii:government_id
passport_no_enc bytea · pii:government_id
passport_expiry_enc bytea · pii:government_id
passport_country_enc bytea · pii:government_id
emergency_contact_enc bytea · pii:emergency_contact
profile_token_enc bytea · pii:profile
owner_member_id uuid
lead_source text
referrer_traveler_id uuid
archived_at timestamp with time zone
archive_reason text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
archived_by text
```
- owner `crm_owner` · RLS on + FORCE
- index `traveler_archived_idx`: btree (tenant_id, archived_at) WHERE ((archived_at IS NOT NULL) AND (deleted_at IS NULL))
- index `traveler_email_bidx_idx`: btree (tenant_id, email_bidx) WHERE ((email_bidx IS NOT NULL) AND (deleted_at IS NULL))
- index `traveler_name_bidx_idx`: btree (tenant_id, name_bidx) WHERE ((name_bidx IS NOT NULL) AND (deleted_at IS NULL))
- index `traveler_name_token_bidx_idx`: gin (name_token_bidx)
- index `traveler_owner_member_idx`: btree (owner_member_id) WHERE (owner_member_id IS NOT NULL)
- index `traveler_phone_bidx_idx`: btree (tenant_id, phone_bidx) WHERE ((phone_bidx IS NOT NULL) AND (deleted_at IS NULL))
- index `traveler_pkey` PRIMARY KEY: UNIQUE btree (traveler_id)
- index `traveler_referrer_idx`: btree (referrer_traveler_id) WHERE (referrer_traveler_id IS NOT NULL)
- index `traveler_tenant_id_uq`: UNIQUE btree (tenant_id, traveler_id)
- check `traveler_archive_chk`: CHECK ((((archive_reason IS NULL) OR (archived_at IS NOT NULL)) AND ((archive_reason IS NULL) OR (archive_reason ~ '^[a-z][a-z0-9_]{0,39}$'::text))))
- check `traveler_archive_reason_chk`: CHECK ((((archived_at IS NULL) = (archive_reason IS NULL)) AND ((archived_at IS NULL) = (archived_by IS NULL)) AND ((archive_reason IS NULL) OR (archive_reason = ANY (ARRAY['agent'::text, 'client_request'::text, 'auto_inactive'::text, 'duplicate'::text, 'other'::text]))) AND ((archived_by IS NULL) OR (archived_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text))))
- check `traveler_bidx_chk`: CHECK (((COALESCE(octet_length(email_bidx), 16) = 16) AND (COALESCE(octet_length(phone_bidx), 16) = 16) AND (COALESCE(octet_length(name_bidx), 8) = 8) AND (array_position(name_token_bidx, NULL::bytea) IS NULL) AND (COALESCE(cardinality(name_token_bidx), 0) <= 16)))
- check `traveler_bidx_pairs_chk`: CHECK ((((email_bidx IS NULL) = (email_enc IS NULL)) AND ((phone_bidx IS NULL) = (phone_enc IS NULL))))
- check `traveler_channel_chk`: CHECK (((preferred_channel IS NULL) OR (preferred_channel = ANY (ARRAY['email'::text, 'phone'::text, 'sms'::text, 'whatsapp'::text]))))
- check `traveler_enc_chk`: CHECK (((octet_length(display_name_enc) >= 30) AND (COALESCE(octet_length(given_name_enc), 30) >= 30) AND (COALESCE(octet_length(family_name_enc), 30) >= 30) AND (COALESCE(octet_length(email_enc), 30) >= 30) AND (COALESCE(octet_length(phone_enc), 30) >= 30) AND (COALESCE(octet_length(dob_enc), 30) >= 30) AND (COALESCE(octet_length(nationality_enc), 30) >= 30) AND (COALESCE(octet_length(passport_no_enc), 30) >= 30) AND (COALESCE(octet_length(passport_expiry_enc), 30) >= 30) AND (COALESCE(octet_length(passport_country_enc), 30) >= 30) AND (COALESCE(octet_length(emergency_contact_enc), 30) >= 30) AND (COALESCE(octet_length(profile_token_enc), 30) >= 30)))
- check `traveler_lead_source_chk`: CHECK (((lead_source IS NULL) OR (lead_source ~ '^[a-z][a-z0-9_]{0,39}$'::text)))
- check `traveler_referrer_chk`: CHECK ((referrer_traveler_id IS DISTINCT FROM traveler_id))
- check `traveler_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `traveler_hold_guard`: BEFORE DELETE OR UPDATE ON crm.traveler FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('referrer_traveler_id', 'profile_token_enc')
- trigger `traveler_set_updated_at`: BEFORE UPDATE ON crm.traveler FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.traveler_health` (table, 24 kB)
```
health_id uuid NN
tenant_id uuid NN
traveler_id uuid NN
health_flags_enc bytea NN · pii:health
consent_id uuid NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `traveler_health_pkey` PRIMARY KEY: UNIQUE btree (health_id)
- index `traveler_health_traveler_uq`: UNIQUE btree (traveler_id) WHERE (deleted_at IS NULL)
- check `traveler_health_enc_chk`: CHECK ((octet_length(health_flags_enc) >= 30))
- check `traveler_health_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `traveler_health_consent`: BEFORE INSERT OR UPDATE OF consent_id, traveler_id ON crm.traveler_health FOR EACH ROW EXECUTE FUNCTION crm.traveler_health_consent()
- trigger `traveler_health_hold_guard`: BEFORE DELETE OR UPDATE ON crm.traveler_health FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('traveler_id')
- trigger `traveler_health_set_updated_at`: BEFORE UPDATE ON crm.traveler_health FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.traveler_profile` (table, ~2 rows, 48 kB)
```
traveler_token uuid NN
tenant_id uuid NN
budget_band text
pace text
group_pref text
repeat_count integer NN
stage2_completeness smallint NN
marketing_ok boolean NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
residence_country text
fitness_band text
trek_experience text
altitude_ok boolean
accommodation_tier text
interests text[] NN
must_do_codes text[] NN
must_avoid_codes text[] NN
occasion text
dietary_flags text[] NN
mobility_flags text[] NN
budget_flex text
decision_maker text
booking_timeline text
competing_quotes boolean
```
- owner `crm_owner` · RLS on + FORCE
- index `traveler_profile_pkey` PRIMARY KEY: UNIQUE btree (traveler_token)
- index `traveler_profile_tenant_token_uq`: UNIQUE btree (tenant_id, traveler_token)
- check `traveler_profile_bands_chk`: CHECK ((((residence_country IS NULL) OR (residence_country ~ '^[A-Z]{2}$'::text)) AND ((fitness_band IS NULL) OR (fitness_band = ANY (ARRAY['up_to_2h'::text, '2_4h'::text, '4_6h'::text, 'over_6h'::text]))) AND ((trek_experience IS NULL) OR (trek_experience = ANY (ARRAY['none'::text, 'some'::text, 'experienced'::text]))) AND ((accommodation_tier IS NULL) OR (accommodation_tier = ANY (ARRAY['budget'::text, 'comfort'::text, 'premium'::text, 'luxury'::text]))) AND ((occasion IS NULL) OR (occasion = ANY (ARRAY['none'::text, 'honeymoon'::text, 'anniversary'::text, 'birthday'::text, 'family_reunion'::text, 'graduation'::text, 'retirement'::text, 'other'::text]))) AND ((budget_flex IS NULL) OR (budget_flex = ANY (ARRAY['fixed'::text, 'some'::text, 'flexible'::text]))) AND ((decision_maker IS NULL) OR (decision_maker = ANY (ARRAY['self'::text, 'partner'::text, 'family'::text, 'group'::text, 'company'::text]))) AND ((booking_timeline IS NULL) OR (booking_timeline = ANY (ARRAY['ready_now'::text, 'within_month'::text, 'within_3_months'::text, 'later'::text, 'just_looking'::text])))))
- check `traveler_profile_budget_chk`: CHECK (((budget_band IS NULL) OR (budget_band = ANY (ARRAY['under_1000'::text, '1000_2000'::text, '2000_3500'::text, '3500_5000'::text, 'over_5000'::text, 'not_sure'::text]))))
- check `traveler_profile_codes_chk`: CHECK (((cardinality(interests) <= 20) AND (array_to_string(interests, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{1,39}(,|$))*$'::text) AND (cardinality(must_do_codes) <= 20) AND (array_to_string(must_do_codes, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{1,39}(,|$))*$'::text) AND (cardinality(must_avoid_codes) <= 20) AND (array_to_string(must_avoid_codes, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{1,39}(,|$))*$'::text) AND (dietary_flags <@ ARRAY['vegetarian'::text, 'vegan'::text, 'halal'::text, 'kosher'::text, 'gluten_free'::text, 'lactose_free'::text, 'nut_allergy'::text, 'shellfish_allergy'::text, 'other_allergy'::text]) AND (array_position(dietary_flags, NULL::text) IS NULL) AND (mobility_flags <@ ARRAY['limited_walking'::text, 'wheelchair'::text, 'no_stairs'::text, 'no_long_drives'::text, 'other'::text]) AND (array_position(mobility_flags, NULL::text) IS NULL)))
- check `traveler_profile_group_chk`: CHECK (((group_pref IS NULL) OR (group_pref = ANY (ARRAY['private'::text, 'small_group'::text]))))
- check `traveler_profile_pace_chk`: CHECK (((pace IS NULL) OR (pace = ANY (ARRAY['relaxed'::text, 'balanced'::text, 'adventure'::text]))))
- check `traveler_profile_repeat_chk`: CHECK (((repeat_count >= 0) AND (repeat_count <= 10000)))
- check `traveler_profile_s2_chk`: CHECK (((stage2_completeness >= 0) AND (stage2_completeness <= 100)))
- check `traveler_profile_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `traveler_profile_set_updated_at`: BEFORE UPDATE ON crm.traveler_profile FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.traveler_relation` (table, 40 kB)
```
relation_id uuid NN
tenant_id uuid NN
from_traveler_id uuid NN
to_traveler_id uuid NN
kind text NN
inverse_id uuid
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `traveler_relation_one_referrer_uq`: UNIQUE btree (from_traveler_id) WHERE ((kind = 'referrer'::text) AND (deleted_at IS NULL))
- index `traveler_relation_pair_uq`: UNIQUE btree (from_traveler_id, to_traveler_id) WHERE (deleted_at IS NULL)
- index `traveler_relation_pkey` PRIMARY KEY: UNIQUE btree (relation_id)
- index `traveler_relation_to_idx`: btree (to_traveler_id)
- check `traveler_relation_kind_chk`: CHECK ((kind = ANY (ARRAY['spouse'::text, 'partner'::text, 'parent'::text, 'child'::text, 'sibling'::text, 'friend'::text, 'referrer'::text, 'referred'::text])))
- check `traveler_relation_self_chk`: CHECK ((from_traveler_id <> to_traveler_id))
- check `traveler_relation_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `traveler_relation_fixed`: BEFORE UPDATE ON crm.traveler_relation FOR EACH ROW EXECUTE FUNCTION crm.traveler_relation_pair()
- trigger `traveler_relation_hold_guard`: BEFORE DELETE OR UPDATE ON crm.traveler_relation FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('from_traveler_id', 'to_traveler_id', 'kind')
- trigger `traveler_relation_mirror`: AFTER INSERT OR DELETE OR UPDATE OF deleted_at ON crm.traveler_relation FOR EACH ROW EXECUTE FUNCTION crm.traveler_relation_mirror()
- trigger `traveler_relation_set_updated_at`: BEFORE UPDATE ON crm.traveler_relation FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.trip` (table, ~2 rows, 72 kB)
```
trip_id uuid NN
tenant_id uuid NN
title text NN · pii:travel
stage text NN
stage_entered_at timestamp with time zone NN
waiting_on text NN
start_date date
end_date date
month date
date_flex_days smallint NN
nights smallint
destinations text[] NN
party_adults smallint NN
party_child_ages smallint[] NN
party_type text
budget_band text
trip_style text
owner_member_id uuid
intake_form_id uuid
lead_source text
lost_reason_code text
last_inquiry_at timestamp with time zone NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `trip_board_idx`: btree (tenant_id, stage, last_inquiry_at DESC) WHERE (deleted_at IS NULL)
- index `trip_owner_idx`: btree (owner_member_id) WHERE (owner_member_id IS NOT NULL)
- index `trip_pkey` PRIMARY KEY: UNIQUE btree (trip_id)
- index `trip_tenant_id_uq`: UNIQUE btree (tenant_id, trip_id)
- check `trip_budget_chk`: CHECK (((budget_band IS NULL) OR (budget_band = ANY (ARRAY['under_1000'::text, '1000_2000'::text, '2000_3500'::text, '3500_5000'::text, 'over_5000'::text, 'not_sure'::text]))))
- check `trip_dates_chk`: CHECK ((((start_date IS NULL) OR (end_date IS NULL) OR (end_date >= start_date)) AND ((month IS NULL) OR (month = (date_trunc('month'::text, (month)::timestamp with time zone))::date))))
- check `trip_destinations_chk`: CHECK (((cardinality(destinations) <= 12) AND (array_to_string(destinations, ','::text, '!'::text) ~ '^([a-z][a-z_]{1,39}(,|$))*$'::text)))
- check `trip_flex_chk`: CHECK (((date_flex_days >= 0) AND (date_flex_days <= 60)))
- check `trip_lead_source_chk`: CHECK (((lead_source IS NULL) OR (lead_source ~ '^[a-z][a-z0-9_]{0,39}$'::text)))
- check `trip_lost_reason_chk`: CHECK ((((stage = 'lost'::text) = (lost_reason_code IS NOT NULL)) AND ((lost_reason_code IS NULL) OR (lost_reason_code = ANY (ARRAY['price'::text, 'price_aa_tour'::text, 'aa_sold_out'::text, 'aa_on_request_declined'::text, 'dates_changed'::text, 'went_elsewhere'::text, 'no_response'::text, 'postponed'::text, 'other'::text])))))
- check `trip_nights_chk`: CHECK (((nights IS NULL) OR ((nights >= 1) AND (nights <= 90))))
- check `trip_party_chk`: CHECK ((((party_adults >= 1) AND (party_adults <= 50)) AND (cardinality(party_child_ages) <= 20) AND ((cardinality(party_child_ages) = 0) OR ((0 <= ALL (party_child_ages)) AND (17 >= ALL (party_child_ages))))))
- check `trip_party_type_chk`: CHECK (((party_type IS NULL) OR (party_type = ANY (ARRAY['solo'::text, 'couple'::text, 'family'::text, 'friends'::text, 'group'::text]))))
- check `trip_stage_chk`: CHECK ((stage = ANY (ARRAY['inquiry'::text, 'qualifying'::text, 'proposal'::text, 'booked'::text, 'pre_departure'::text, 'travelling'::text, 'completed'::text, 'lost'::text, 'cancelled'::text])))
- check `trip_style_chk`: CHECK (((trip_style IS NULL) OR (trip_style = ANY (ARRAY['relaxed'::text, 'balanced'::text, 'adventure'::text]))))
- check `trip_title_chk`: CHECK (((length(btrim(title)) >= 1) AND (length(btrim(title)) <= 120)))
- check `trip_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- check `trip_waiting_on_chk`: CHECK ((waiting_on = ANY (ARRAY['agency'::text, 'client'::text, 'aa'::text, 'supplier'::text, 'none'::text])))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `trip_hold_guard`: BEFORE DELETE OR UPDATE ON crm.trip FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change()
- trigger `trip_set_updated_at`: BEFORE UPDATE ON crm.trip FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `trip_stage_transition`: BEFORE UPDATE OF stage ON crm.trip FOR EACH ROW EXECUTE FUNCTION crm.enforce_stage_transition()

### `crm.trip_commitment` (table, 32 kB)
```
commitment_id uuid NN
tenant_id uuid NN
trip_id uuid NN
kind text NN
line_status text NN
source_ref text NN
checked_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `trip_commitment_pkey` PRIMARY KEY: UNIQUE btree (commitment_id)
- index `trip_commitment_source_uq`: UNIQUE btree (tenant_id, kind, source_ref)
- index `trip_commitment_trip_idx`: btree (trip_id)
- check `trip_commitment_kind_status_chk`: CHECK ((((kind = 'aa_line'::text) AND (line_status = ANY (ARRAY['requested'::text, 'held'::text, 'confirmed'::text, 'released'::text, 'expired'::text, 'cancelled'::text, 'declined'::text]))) OR ((kind = 'invoice'::text) AND (line_status = ANY (ARRAY['draft'::text, 'open'::text, 'payment_claimed'::text, 'paid'::text, 'paid_unfulfillable'::text, 'void'::text, 'expired'::text]))) OR ((kind = 'payment'::text) AND (line_status = ANY (ARRAY['pending'::text, 'succeeded'::text, 'failed'::text, 'refunded'::text]))) OR ((kind = 'signature'::text) AND (line_status = ANY (ARRAY['pending'::text, 'signed'::text, 'declined'::text, 'expired'::text]))) OR ((kind = 'commission'::text) AND (line_status = ANY (ARRAY['expected'::text, 'claimed'::text, 'received'::text, 'cancelled'::text])))))
- check `trip_commitment_source_chk`: CHECK ((source_ref ~ '^[A-Za-z0-9:_.-]{1,80}$'::text))
- check `trip_commitment_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `trip_commitment_set_updated_at`: BEFORE UPDATE ON crm.trip_commitment FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.trip_party` (table, ~2 rows, 64 kB)
```
trip_party_id uuid NN
tenant_id uuid NN
trip_id uuid NN
traveler_token uuid NN
role text NN
age_band_at_departure text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `trip_party_pkey` PRIMARY KEY: UNIQUE btree (trip_party_id)
- index `trip_party_token_idx`: btree (traveler_token)
- index `trip_party_uq`: UNIQUE btree (trip_id, traveler_token)
- check `trip_party_age_band_chk`: CHECK (((age_band_at_departure IS NULL) OR (age_band_at_departure ~ '^[a-z0-9_]{1,20}$'::text)))
- check `trip_party_age_band_list_chk`: CHECK (((age_band_at_departure IS NULL) OR (age_band_at_departure = ANY (ARRAY['under_2'::text, '2_11'::text, '12_17'::text, '18_24'::text, '25_34'::text, '35_44'::text, '45_54'::text, '55_64'::text, '65_74'::text, '75_plus'::text]))))
- check `trip_party_role_chk`: CHECK ((role = ANY (ARRAY['lead'::text, 'companion'::text])))
- check `trip_party_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `trip_party_hold_guard`: BEFORE DELETE OR UPDATE ON crm.trip_party FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_token')
- trigger `trip_party_set_updated_at`: BEFORE UPDATE ON crm.trip_party FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.trip_stage_history` (table, 48 kB)
```
history_id uuid NN
tenant_id uuid NN
trip_id uuid NN
from_stage text
to_stage text NN
reason_code text NN
override boolean NN
at timestamp with time zone NN
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `trip_stage_history_pkey` PRIMARY KEY: UNIQUE btree (history_id)
- index `trip_stage_history_trip_idx`: btree (trip_id, at)
- check `trip_stage_history_reason_chk`: CHECK ((reason_code ~ '^[a-z][a-z0-9_]{0,39}$'::text))
- check `trip_stage_history_stage_chk`: CHECK (((to_stage ~ '^[a-z_]{3,20}$'::text) AND ((from_stage IS NULL) OR (from_stage ~ '^[a-z_]{3,20}$'::text))))
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `trip_stage_history_append_only`: BEFORE DELETE OR UPDATE ON crm.trip_stage_history FOR EACH ROW EXECUTE FUNCTION crm.erasable_append_only()
- trigger `trip_stage_history_no_truncate`: BEFORE TRUNCATE ON crm.trip_stage_history FOR EACH STATEMENT EXECUTE FUNCTION crm.erasable_append_only()

### `crm.trip_traveler` (table, 80 kB)
```
trip_traveler_id uuid NN
tenant_id uuid NN
trip_id uuid NN
traveler_id uuid NN
role text NN
portal_access text NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `trip_traveler_one_lead_uq`: UNIQUE btree (trip_id) WHERE ((role = 'lead'::text) AND (deleted_at IS NULL))
- index `trip_traveler_pkey` PRIMARY KEY: UNIQUE btree (trip_traveler_id)
- index `trip_traveler_traveler_idx`: btree (traveler_id)
- index `trip_traveler_uq`: UNIQUE btree (trip_id, traveler_id)
- check `trip_traveler_portal_chk`: CHECK ((portal_access = ANY (ARRAY['lead'::text, 'companion'::text, 'none'::text])))
- check `trip_traveler_role_chk`: CHECK ((role = ANY (ARRAY['lead'::text, 'companion'::text])))
- check `trip_traveler_trash_chk`: CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `trip_traveler_hold_guard`: BEFORE DELETE OR UPDATE ON crm.trip_traveler FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id')
- trigger `trip_traveler_set_updated_at`: BEFORE UPDATE ON crm.trip_traveler FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.v_ai_traveler_profile` (VIEW)
```
traveler_token uuid
residence_country text
budget_band text
pace text
group_pref text
fitness_band text
trek_experience text
altitude_ok boolean
accommodation_tier text
interests text[]
must_do_codes text[]
must_avoid_codes text[]
occasion text
dietary_flags text[]
mobility_flags text[]
budget_flex text
decision_maker text
booking_timeline text
competing_quotes boolean
repeat_count integer
stage2_completeness smallint
```
- owner `crm_owner`
- grant `crm_ai_reader`: SELECT
- grant `crm_app`: SELECT

### `crm.v_ai_trip_context` (VIEW)
```
trip_id uuid
stage text
waiting_on text
month date
start_date date
end_date date
nights smallint
date_flex_days smallint
destinations text[]
party_adults smallint
party_child_ages smallint[]
party_type text
budget_band text
trip_style text
```
- owner `crm_owner`
- grant `crm_ai_reader`: SELECT
- grant `crm_app`: SELECT

### `crm.v_ai_trip_party` (VIEW)
```
trip_id uuid
traveler_token uuid
role text
age_band_at_departure text
```
- owner `crm_owner`
- grant `crm_ai_reader`: SELECT
- grant `crm_app`: SELECT

### `crm.v_insight_fact` (VIEW)
```
tenant_id uuid
month date
destination text
budget_band text
age_band text
party_size integer
stage_reached text
lost_reason_code text
```
- owner `crm_owner`
- grant `crm_app`: SELECT
- grant `crm_insights`: SELECT

### `crm.v_schema_versions` (VIEW)
```
version character varying(20)
applied_at timestamp with time zone
```
- owner `crm_owner`
- grant `crm_app`: SELECT

## `geo` (17 objects)

### `geo.geocode_call` (table, 48 kB)
```
id bigint NN
called_at timestamp with time zone NN
provider text NN
requests integer NN
cost_usd numeric(10,6) NN
job_id uuid
endpoint text NN
credits integer
```
- owner `cis_owner`
- index `geocode_call_called_at_idx`: btree (called_at)
- index `geocode_call_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `geocode_call_credits_chk`: CHECK (((credits IS NULL) OR (credits >= 0)))
- check `geocode_call_endpoint_chk`: CHECK ((endpoint = ANY (ARRAY['search'::text, 'place_details'::text, 'overpass'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.graph_build` (table, ~2 rows, 96 kB)
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

### `geo.graph_edge` (table, ~1779 rows, 776 kB)
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

### `geo.graph_node` (table, ~1341 rows, 824 kB)
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

### `geo.place_dedupe_country` (table, 16 kB)
```
country text NN
mode text NN
approved_diff_hash text
approved_diff jsonb NN
rule_version text NN
updated_by text NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `place_dedupe_country_pkey` PRIMARY KEY: UNIQUE btree (country)
- check `place_dedupe_country_apply_chk`: CHECK (((mode <> 'apply'::text) OR (approved_diff_hash IS NOT NULL)))
- check `place_dedupe_country_mode_chk`: CHECK ((mode = ANY (ARRAY['dry_run'::text, 'apply'::text])))
- check `place_dedupe_country_norm_chk`: CHECK (((country = lower(btrim(country))) AND (country <> ''::text)))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.place_merge` (table, 40 kB)
```
id uuid NN
merged_id uuid NN
keeper_id uuid NN
country text NN
decided_by text NN
rule_version text NN
score numeric(6,3)
features jsonb NN
verdict jsonb
repointed jsonb NN
prior jsonb NN
job_id uuid
created_at timestamp with time zone NN
created_by text NN
undone_at timestamp with time zone
undone_by text
undo_reason text
```
- owner `cis_owner`
- index `place_merge_active_uidx`: UNIQUE btree (merged_id) WHERE (undone_at IS NULL)
- index `place_merge_country_idx`: btree (country, created_at DESC)
- index `place_merge_keeper_idx`: btree (keeper_id)
- index `place_merge_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `place_merge_decided_by_chk`: CHECK ((decided_by = ANY (ARRAY['provider_id'::text, 'osm_id'::text, 'place_card'::text, 'line_overlap'::text, 'rule'::text, 'llm'::text, 'admin'::text])))
- check `place_merge_not_self_chk`: CHECK ((merged_id <> keeper_id))
- check `place_merge_undo_chk`: CHECK ((((undone_at IS NULL) = (undone_by IS NULL)) AND ((undone_at IS NULL) OR (undo_reason IS NOT NULL))))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.place_name` (table, ~1719 rows, 576 kB)
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

### `geo.place_pair_verdict` (table, 24 kB)
```
lo_id uuid NN
hi_id uuid NN
input_hash text NN
verdict text NN
source text NN
answers jsonb NN
models jsonb NN
rule_version text NN
prompt_sha text
cost_usd numeric(10,6) NN
job_id uuid
created_at timestamp with time zone NN
created_by text NN
```
- owner `cis_owner`
- index `place_pair_verdict_hi_idx`: btree (hi_id)
- index `place_pair_verdict_pkey` PRIMARY KEY: UNIQUE btree (lo_id, hi_id, input_hash)
- check `place_pair_verdict_cost_chk`: CHECK ((cost_usd >= (0)::numeric))
- check `place_pair_verdict_order_chk`: CHECK ((lo_id < hi_id))
- check `place_pair_verdict_pin_chk`: CHECK (((source = 'model'::text) = (input_hash <> '*'::text)))
- check `place_pair_verdict_source_chk`: CHECK ((source = ANY (ARRAY['model'::text, 'undo'::text, 'admin'::text, 'recheck'::text])))
- check `place_pair_verdict_verdict_chk`: CHECK ((verdict = ANY (ARRAY['same'::text, 'different'::text, 'unsure'::text])))
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.place_shape` (table, ~39 rows, 488 kB)
```
destination_id uuid NN
kind text NN
status text NN
source text
geom jsonb
geom_mid jsonb
geom_lo jsonb
min_lat double precision NN
min_lng double precision NN
max_lat double precision NN
max_lng double precision NN
length_km numeric(8,1)
osm_type text
osm_id bigint
tries integer NN
next_retry_at timestamp with time zone NN
last_error text
fetched_at timestamp with time zone
meta jsonb NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `place_shape_due_idx`: btree (status, next_retry_at)
- index `place_shape_osm_idx`: btree (osm_type, osm_id) WHERE (osm_id IS NOT NULL)
- index `place_shape_pkey` PRIMARY KEY: UNIQUE btree (destination_id)
- check `place_shape_bbox_chk`: CHECK ((((min_lat >= ('-90'::integer)::double precision) AND (min_lat <= (90)::double precision)) AND ((max_lat >= ('-90'::integer)::double precision) AND (max_lat <= (90)::double precision)) AND (min_lat <= max_lat) AND ((min_lng >= ('-180'::integer)::double precision) AND (min_lng <= (180)::double precision)) AND ((max_lng >= ('-180'::integer)::double precision) AND (max_lng <= (180)::double precision)) AND (min_lng <= max_lng)))
- check `place_shape_drawn_chk`: CHECK (((status = ANY (ARRAY['ok'::text, 'approximate'::text, 'manual'::text])) = ((geom IS NOT NULL) AND (geom_mid IS NOT NULL) AND (geom_lo IS NOT NULL) AND (source IS NOT NULL) AND (length_km IS NOT NULL))))
- check `place_shape_geom_chk`: CHECK (((geom IS NULL) OR (((geom ->> 'type'::text) = ANY (ARRAY['LineString'::text, 'MultiLineString'::text])) AND ((geo.line_vertex_count(geom) >= 2) AND (geo.line_vertex_count(geom) <= 2000)))))
- check `place_shape_geom_lo_chk`: CHECK (((geom_lo IS NULL) OR (((geom_lo ->> 'type'::text) = ANY (ARRAY['LineString'::text, 'MultiLineString'::text])) AND ((geo.line_vertex_count(geom_lo) >= 2) AND (geo.line_vertex_count(geom_lo) <= 60)))))
- check `place_shape_geom_mid_chk`: CHECK (((geom_mid IS NULL) OR (((geom_mid ->> 'type'::text) = ANY (ARRAY['LineString'::text, 'MultiLineString'::text])) AND ((geo.line_vertex_count(geom_mid) >= 2) AND (geo.line_vertex_count(geom_mid) <= 300)) AND (octet_length((geom_mid)::text) <= 12288))))
- check `place_shape_kind_chk`: CHECK ((kind = ANY (ARRAY['line'::text, 'area'::text])))
- check `place_shape_length_chk`: CHECK (((length_km IS NULL) OR (length_km >= (0)::numeric)))
- check `place_shape_osm_chk`: CHECK ((((osm_type IS NULL) = (osm_id IS NULL)) AND ((osm_type IS NULL) OR (osm_type = ANY (ARRAY['node'::text, 'way'::text, 'relation'::text])))))
- check `place_shape_source_chk`: CHECK (((source IS NULL) OR (source = ANY (ARRAY['geoapify_details'::text, 'overpass'::text, 'anchors'::text, 'manual'::text]))))
- check `place_shape_status_chk`: CHECK ((status = ANY (ARRAY['pending'::text, 'ok'::text, 'approximate'::text, 'not_found'::text, 'failed'::text, 'manual'::text])))
- check `place_shape_status_source_chk`: CHECK ((((status = 'approximate'::text) = (NOT (source IS DISTINCT FROM 'anchors'::text))) AND ((status = 'manual'::text) = (NOT (source IS DISTINCT FROM 'manual'::text)))))
- check `place_shape_tries_chk`: CHECK ((tries >= 0))
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_build` (table, ~110 rows, 184 kB)
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

### `geo.tour_day` (table, ~1084 rows, 536 kB)
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

### `geo.tour_junction` (table, ~22662 rows, 6 MB)
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

### `geo.tour_leg` (table, ~16041 rows, 11.7 MB)
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

### `geo.tour_place` (table, ~2473 rows, 40.5 MB)
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

### `geo.tour_segment` (table, ~192 rows, 480 kB)
```
build_id uuid NN
source_id text NN
day_index integer NN
destination_id uuid NN
segment jsonb
basis text NN
from_destination_id uuid
to_destination_id uuid
segment_km numeric(8,1)
```
- owner `cis_owner`
- index `tour_segment_destination_idx`: btree (destination_id)
- index `tour_segment_pkey` PRIMARY KEY: UNIQUE btree (build_id, source_id, day_index, destination_id)
- check `tour_segment_basis_chk`: CHECK ((basis = ANY (ARRAY['day_anchors'::text, 'anchor_window'::text, 'feature'::text])))
- check `tour_segment_feature_chk`: CHECK ((((basis = 'feature'::text) = (segment IS NULL)) AND ((segment IS NULL) = (segment_km IS NULL))))
- check `tour_segment_km_chk`: CHECK (((segment_km IS NULL) OR (segment_km >= (0)::numeric)))
- check `tour_segment_segment_chk`: CHECK (((segment IS NULL) OR (((segment ->> 'type'::text) = 'LineString'::text) AND ((geo.line_vertex_count(segment) >= 2) AND (geo.line_vertex_count(segment) <= 300)))))
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_stop` (table, ~3081 rows, 1.3 MB)
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

## `gold_aa_internal` (6 objects)

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

### `gold_aa_internal.published_tours` (table, ~892 rows, 6.8 MB)
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
master_status_reason text
updated_at timestamp with time zone NN
```
- owner `cis_owner` · RLS on + FORCE
- index `idx_aa_internal_published_at`: btree (published_at DESC)
- index `idx_pt_embedding`: ivfflat (content_embedding vector_cosine_ops) WITH (lists='10')
- index `idx_published_tours_quality_score_id`: btree (quality_score_id)
- index `published_tours_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `published_tours_tour_id_key`: UNIQUE btree (tour_id)
- check `published_tours_master_status_reason_check`: CHECK (((master_status_reason IS NULL) OR (master_status_reason = ANY (ARRAY['staff_deactivated'::text, 'staff_trashed'::text, 'source_deleted'::text, 'superseded'::text]))))
- grant `aa_app_user`: SELECT
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `aa_app_user_aa_master_read` (PERMISSIVE SELECT TO aa_app_user): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `catalog_owner_aa_master_read` (PERMISSIVE SELECT TO catalog_owner): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `published_tours_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `published_tours_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `gold_aa_internal.tenant_tour_versions` (table, ~53 rows, 648 kB)
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

### `gold_aa_internal.tour_lifecycle_event` (table, 80 kB)
```
id bigint NN
source_system text NN
source_id text NN
tour_id uuid NN
event text NN
reason text NN
replaced_by_tour_id uuid
action text NN
actor text
details jsonb NN
occurred_at timestamp with time zone NN
idempotency_key text NN
```
- owner `cis_owner`
- index `tour_lifecycle_event_idempotency_key_key`: UNIQUE btree (idempotency_key)
- index `tour_lifecycle_event_key_idx`: btree (source_id, occurred_at DESC, id DESC)
- index `tour_lifecycle_event_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `tour_lifecycle_event_tour_idx`: btree (tour_id)
- check `tour_lifecycle_event_event_check`: CHECK ((event = ANY (ARRAY['retired'::text, 'paused'::text, 'restored'::text, 'superseded'::text])))
- check `tour_lifecycle_event_reason_check`: CHECK ((reason = ANY (ARRAY['source_deleted'::text, 'master_trashed'::text, 'superseded_orphan'::text, 'master_inactive'::text, 'superseded_pending'::text, 'replaced'::text, 'restore'::text, 'publish'::text, 'activate'::text, 'set_active'::text])))
- check `tour_lifecycle_event_source_system_check`: CHECK ((source_system = 'cis'::text))
- check `tour_lifecycle_event_successor_check`: CHECK (((event = 'superseded'::text) = (replaced_by_tour_id IS NOT NULL)))
- grant `catalog_owner`: SELECT
- grant `cis_app`: INSERT, SELECT
- trigger `tour_lifecycle_event_append_only`: BEFORE DELETE OR UPDATE ON gold_aa_internal.tour_lifecycle_event FOR EACH ROW EXECUTE FUNCTION gold_aa_internal.tour_lifecycle_event_append_only()

### `gold_aa_internal.v_tour_liveness` (VIEW)
```
source_system text
source_id text
tour_id uuid
state text
reason text
changed_at timestamp with time zone
```
- owner `cis_owner`
- grant `aa_app_user`: SELECT
- grant `catalog_owner`: SELECT
- grant `cis_app`: SELECT

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
username character varying(100) NN · pii:online_id
password_hash character varying(255) · conf:credential
role shared.admin_role NN
is_active boolean NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
email text · pii:contact
display_name text · pii:name
cognito_iss text · pii:online_id
cognito_sub text · pii:online_id
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

### `shared.alert_recipient` (table, ~2 rows, 64 kB)
```
id uuid NN
email text NN · pii:contact
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

### `shared.cost_explorer_app_snapshot` (table, ~5358 rows, 1.4 MB)
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

### `shared.cost_explorer_snapshot` (table, ~1678 rows, 2 MB)
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

### `shared.decision_cache_hits_daily` (table, ~261 rows, 128 kB)
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

### `shared.decision_log` (table, ~387843 rows, 379.4 MB)
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

### `shared.destinations` (table, ~1927 rows, 1.1 MB)
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
- check `destinations_geo_precision_check`: CHECK (((geo_precision IS NULL) OR (geo_precision = ANY (ARRAY['point'::text, 'area'::text, 'line'::text]))))
- check `destinations_geo_status_check`: CHECK ((geo_status = ANY (ARRAY['ok'::text, 'suspect'::text, 'manual'::text])))
- check `destinations_located_by_check`: CHECK ((located_by = ANY (ARRAY['mapbox'::text, 'llm'::text, 'geoapify'::text, 'manual'::text])))
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.dfs_balance_snapshot` (table, 320 kB)
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

### `shared.job` (table, ~3207 rows, 12.5 MB)
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

### `shared.job_worker` (table, ~150 rows, 312 kB)
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

### `shared.llm_call_log` (table, ~284344 rows, 145.8 MB)
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
- owner `cis_owner` · RLS on
- index `idx_notif_event_type`: btree (event_type, created_at DESC)
- index `idx_notif_tenant_unread`: btree (tenant_id, created_at DESC) WHERE (is_read = false)
- index `notifications_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: UPDATE (is_read)
- policy `notifications_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `notifications_tenant_audience` (RESTRICTIVE ALL TO aa_app_user): USING `(target_roles @> ARRAY['tenant'::text])` WITH CHECK `(target_roles @> ARRAY['tenant'::text])`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

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

### `shared.rerun_wave` (table, 80 kB)
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

### `shared.schema_versions` (table, ~301 rows, 104 kB)
```
version character varying(20) NN
description text
applied_at timestamp with time zone NN
```
- owner `cis_owner`
- index `schema_versions_pkey` PRIMARY KEY: UNIQUE btree (version)
- grant `bk_owner`: INSERT, SELECT
- grant `cis_app`: SELECT
- grant `crm_owner`: INSERT, SELECT
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

### `shared.tenant_api_usage` (table, ~148083 rows, 35.8 MB)
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

### `shared.tenant_brand_rules` (table, ~27 rows, 232 kB)
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
- owner `cis_owner` · RLS on
- index `idx_brand_rules_tenant_brand`: btree (tenant_id, brand_name)
- index `tenant_brand_rules_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `uq_tenant_brand_name_version`: UNIQUE btree (tenant_id, brand_name, version)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: INSERT (brand_name, brand_type, core_idea, customer_mindset, customer_segment, default_cta, forbidden_words, good_examples, style_guide, system_prompt, target_markets, tenant_id, updated_at, version, voice_examples)
- column grant `aa_app_user`: INSERT, UPDATE (is_active)
- policy `tenant_brand_rules_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

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
- owner `cis_owner` · RLS on
- index `tenant_seo_config_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `tenant_seo_config_tenant_id_key`: UNIQUE btree (tenant_id)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: INSERT (tenant_id)
- column grant `aa_app_user`: INSERT, UPDATE (target_market)
- column grant `aa_app_user`: UPDATE (updated_at)
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- policy `tenant_seo_config_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`

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

## `silver_aa_internal` (7 objects)

### `silver_aa_internal.generated_content` (table, ~1516 rows, 15.4 MB)
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

### `silver_aa_internal.quality_scores` (table, ~1550 rows, 2 MB)
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

### `silver_aa_internal.raw_tours` (table, ~987 rows, 5 MB)
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
source_key text
```
- owner `cis_owner` · RLS on + FORCE
- index `idx_aa_internal_raw_tours_batch`: btree (batch_id)
- index `idx_aa_internal_raw_tours_country`: btree (country)
- index `idx_aa_internal_raw_tours_status`: btree (pipeline_status)
- index `idx_raw_tours_country_raw_unresolved`: btree (country_raw_unresolved) WHERE (country_raw_unresolved IS NOT NULL)
- index `idx_raw_tours_review_status`: btree (review_status)
- index `raw_tours_pkey` PRIMARY KEY: UNIQUE btree (tour_id)
- index `raw_tours_source_key_idx`: btree (source_key)
- index `uq_raw_tours_active_per_group`: UNIQUE btree (source_group_id) WHERE (source_status = 'active'::silver_aa_internal.source_status_enum)
- check `chk_raw_tours_country`: CHECK (((country IS NULL) OR (country = ANY (ARRAY['Bhutan'::text, 'Cambodia'::text, 'China'::text, 'India'::text, 'Indonesia'::text, 'Japan'::text, 'Kyrgyzstan'::text, 'Laos'::text, 'Malaysia'::text, 'Mongolia'::text, 'Myanmar'::text, 'Nepal'::text, 'Pakistan'::text, 'Philippines'::text, 'South Korea'::text, 'Sri Lanka'::text, 'Taiwan'::text, 'Thailand'::text, 'Uzbekistan'::text, 'Vietnam'::text]))))
- check `raw_tours_review_status_check`: CHECK (((review_status)::text = ANY (ARRAY[('pending_review'::character varying)::text, ('reviewed'::character varying)::text, ('approved'::character varying)::text, ('rejected'::character varying)::text])))
- grant `aa_app_user`: SELECT
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
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

## `tripplanner` (10 objects)

### `tripplanner.component_id_map` (table, ~750 rows, 136 kB)
```
old_id uuid NN
new_id uuid NN
matched_by text NN
created_at timestamp with time zone NN
```
- owner `tp_owner`
- index `component_id_map_pkey` PRIMARY KEY: UNIQUE btree (old_id)
- check `component_id_map_matched_by_check`: CHECK ((matched_by = ANY (ARRAY['name'::text, 'destination'::text])))
- grant `tripplanner`: INSERT, SELECT

### `tripplanner.customers` (table, 64 kB)
```
id uuid NN
name text NN · pii:name
phone text · pii:contact
email text · pii:contact
created_at timestamp with time zone NN
contact_consent boolean NN
contact_consent_at timestamp with time zone
```
- owner `tp_owner`
- index `customers_email_key`: UNIQUE btree (email)
- index `customers_phone_key`: UNIQUE btree (phone)
- index `customers_pkey` PRIMARY KEY: UNIQUE btree (id)
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.llm_spend_daily` (table, ~8 rows, 64 kB)
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
payload jsonb NN · pii:contact (also pii:name, pii:free_text, pii:travel)
created_at timestamp with time zone NN
```
- owner `tp_owner`
- index `outbox_event_id_idx`: btree (event, id)
- index `outbox_idempotency_key_key`: UNIQUE btree (idempotency_key)
- index `outbox_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `outbox_event_chk`: CHECK ((event = 'inquiry.submitted'::text))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.sessions` (table, ~93 rows, 80 kB)
```
id uuid NN
guest_token text · conf:credential
customer_id uuid
created_at timestamp with time zone NN
expires_at timestamp with time zone
guest_token_hash bytea · conf:credential
```
- owner `tp_owner`
- index `sessions_guest_token_key`: UNIQUE btree (guest_token)
- index `sessions_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `sessions_guest_token_hash_len_chk`: CHECK (((guest_token_hash IS NULL) OR (octet_length(guest_token_hash) = 32)))
- check `sessions_guest_token_retired_chk`: CHECK ((guest_token IS NULL))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.trip_drafts` (table, ~98 rows, 120 kB)
```
id uuid NN
session_id uuid NN
status text NN
itinerary jsonb NN · pii:travel (also pii:free_text)
date_start date · pii:travel
date_end date · pii:travel
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `tp_owner`
- index `trip_drafts_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_drafts_session_idx`: btree (session_id)
- check `trip_drafts_status_chk`: CHECK ((status = ANY (ARRAY['draft'::text, 'sent'::text])))
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.trip_events` (table, ~416 rows, 184 kB)
```
id bigint NN
trip_id uuid NN
session_id uuid NN
event_type text NN
payload jsonb NN · pii:free_text (also pii:travel)
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
payload jsonb · pii:contact (also pii:name, pii:free_text, pii:travel)
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
| `aa_cis_admin` | yes | no | no | none |  | bk_owner, cis_app, cis_owner, crm_owner, rds_superuser, tp_owner |
| `bk_owner` | no | no | no | none |  |  |
| `booking` | yes | no | no | 15 |  |  |
| `catalog_owner` | no | no | no | none |  |  |
| `cis_app` | yes | no | no | 90 |  |  |
| `cis_owner` | no | no | no | none |  |  |
| `crm_ai_reader` | no | no | no | none |  |  |
| `crm_app` | yes | no | no | 6 |  | crm_ai_reader, crm_eraser, crm_insights, crm_support_reader |
| `crm_eraser` | no | no | no | none |  |  |
| `crm_insights` | no | no | no | none |  |  |
| `crm_owner` | no | no | no | none |  |  |
| `crm_support_reader` | no | no | no | none |  |  |
| `db_migrator` | yes | no | no | 5 |  | bk_owner, catalog_owner, cis_app, cis_owner, crm_owner, pg_read_all_stats, tp_owner |
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
| `crm_owner` | (all) | functions | `crm_owner` | EXECUTE |
| `crm_owner` | crm | tables | `crm_app` | DELETE,INSERT,SELECT,UPDATE |
| `crm_owner` | crm | sequences | `crm_app` | SELECT,USAGE |
| `tp_owner` | tripplanner | tables | `tripplanner` | DELETE,INSERT,SELECT,UPDATE |
| `tp_owner` | tripplanner | sequences | `tripplanner` | SELECT,USAGE |

## Functions

Extension-owned functions are left out. `SECURITY DEFINER` functions run with the owner's rights.

| function | returns | language | owner | security definer |
|---|---|---|---|---|
| `acp_shared.audit_log_append_only()` | trigger | plpgsql | `cis_owner` | no |
| `acp_shared.audit_log_chain()` | trigger | plpgsql | `cis_owner` | no |
| `booking.b2b_answer_due(start_at timestamp with time zone, business_days integer, tz text)` | timestamp with time zone | plpgsql | `bk_owner` | no |
| `booking.b2b_cancellations_outbox()` | trigger | plpgsql | `bk_owner` | no |
| `booking.b2b_hold_lines_outbox()` | trigger | plpgsql | `bk_owner` | no |
| `booking.b2b_holds_outbox()` | trigger | plpgsql | `bk_owner` | no |
| `booking.cancellation_policy_maker_checker()` | trigger | plpgsql | `bk_owner` | no |
| `booking.departure_incidents_outbox()` | trigger | plpgsql | `bk_owner` | no |
| `booking.departures_outbox()` | trigger | plpgsql | `bk_owner` | no |
| `booking.outbox_departure_event(p_departure uuid, p_type text, p_incident text)` | void | sql | `bk_owner` | no |
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
| `crm.audit_drop_expired_partitions(p_dry_run boolean)` | TABLE(partition_name text, range_end timestamp with time zone, action text) | plpgsql | `crm_owner` | **yes** |
| `crm.audit_ensure_partitions()` | integer | plpgsql | `crm_owner` | **yes** |
| `crm.audit_event_check_at()` | trigger | plpgsql | `crm_owner` | no |
| `crm.audit_export_agencies()` | TABLE(tenant_id uuid, exported_until timestamp with time zone, verified_until timestamp with time zone, last_seq bigint, registered_at timestamp with time zone) | sql | `crm_owner` | **yes** |
| `crm.audit_manifest_chain()` | trigger | plpgsql | `crm_owner` | no |
| `crm.audit_mark_verified(p_until timestamp with time zone)` | boolean | plpgsql | `crm_owner` | **yes** |
| `crm.audit_partition_bounds()` | TABLE(partition_name text, range_start timestamp with time zone, range_end timestamp with time zone) | sql | `crm_owner` | no |
| `crm.audit_register_tenant()` | trigger | plpgsql | `crm_owner` | no |
| `crm.enforce_stage_transition()` | trigger | plpgsql | `crm_owner` | no |
| `crm.enforce_status_transition()` | trigger | plpgsql | `crm_owner` | no |
| `crm.erasable_append_only()` | trigger | plpgsql | `crm_owner` | no |
| `crm.erase_held(p_scope text, p_subject uuid, p_token uuid)` | boolean | plpgsql | `crm_owner` | no |
| `crm.erase_rows(p_table text, p_where text, p_subject uuid, p_token uuid, p_dry_run boolean, p_set text)` | bigint | plpgsql | `crm_owner` | no |
| `crm.erase_subject(p_scope text, p_subject uuid, p_profile_token uuid, p_dry_run boolean)` | jsonb | plpgsql | `crm_owner` | **yes** |
| `crm.guard_erasure_request_owner_confirm()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_held_change()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_invitation_write()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_legal_hold()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_member_write()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_owner_recovery()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_platform_write()` | trigger | plpgsql | `crm_owner` | no |
| `crm.hold_row(p_trip uuid, p_traveler uuid)` | boolean | sql | `crm_owner` | no |
| `crm.hold_traveler(p_traveler uuid)` | boolean | sql | `crm_owner` | no |
| `crm.hold_trip(p_trip uuid)` | boolean | sql | `crm_owner` | no |
| `crm.job_set_updated_at()` | trigger | plpgsql | `crm_owner` | no |
| `crm.legal_hold_blocks(p_scope text, p_subject uuid)` | boolean | sql | `crm_owner` | no |
| `crm.lifecycle_purge_expired(p_dry_run boolean)` | jsonb | plpgsql | `crm_owner` | **yes** |
| `crm.reject_append_only_change()` | trigger | plpgsql | `crm_owner` | no |
| `crm.relation_inverse(kind text)` | text | sql | `crm_owner` | no |
| `crm.set_updated_at()` | trigger | plpgsql | `crm_owner` | no |
| `crm.tenant_key_guard()` | trigger | plpgsql | `crm_owner` | no |
| `crm.traveler_health_consent()` | trigger | plpgsql | `crm_owner` | no |
| `crm.traveler_relation_mirror()` | trigger | plpgsql | `crm_owner` | no |
| `crm.traveler_relation_pair()` | trigger | plpgsql | `crm_owner` | no |
| `crm.trip_delete_blockers(p_trip uuid)` | text[] | sql | `crm_owner` | no |
| `geo.line_vertex_count(g jsonb)` | integer | sql | `cis_owner` | no |
| `geo.name_norm(p text)` | text | sql | `cis_owner` | no |
| `gold_aa_internal.tour_lifecycle_event_append_only()` | trigger | plpgsql | `cis_owner` | no |
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
booking.b2b_cancellations.hold_id -> booking.b2b_holds.id
booking.b2b_cancellations.partner_id -> booking.b2b_partners.id
booking.b2b_cancellations.policy_id -> booking.cancellation_policies.id
booking.b2b_cancellations.trip_case_id -> booking.trip_cases.id
booking.b2b_hold_lines.answered_by -> booking.staff_users.cis_user_id
booking.b2b_hold_lines.departure_id -> booking.departures.id
booking.b2b_hold_lines.hold_id -> booking.b2b_holds.id
booking.b2b_holds.cancellation_policy_id -> booking.cancellation_policies.id
booking.b2b_holds.partner_id -> booking.b2b_partners.id
booking.b2b_holds.quote_id -> booking.b2b_quotes.id
booking.b2b_holds.trip_case_id -> booking.trip_cases.id
booking.b2b_partners.created_by -> booking.staff_users.cis_user_id
booking.b2b_partners.updated_by -> booking.staff_users.cis_user_id
booking.b2b_quote_lines.departure_id -> booking.departures.id
booking.b2b_quote_lines.quote_id -> booking.b2b_quotes.id
booking.b2b_quotes.partner_id -> booking.b2b_partners.id
booking.cancellation_policies.created_by -> booking.staff_users.cis_user_id
booking.cancellation_policies.trip_plan_id -> booking.trip_plans.id
booking.customer_otps.customer_id -> booking.customers.id
booking.customer_sessions.customer_id -> booking.customers.id
booking.customers.merge_candidate_id -> booking.customers.id
booking.customers.profile_media_id -> booking.media_files.id
booking.departure_incidents.cleared_by -> booking.staff_users.cis_user_id
booking.departure_incidents.departure_id -> booking.departures.id
booking.departure_incidents.flagged_by -> booking.staff_users.cis_user_id
booking.departures.created_by -> booking.staff_users.cis_user_id
booking.departures.trip_plan_id -> booking.trip_plans.id
booking.departures.updated_by -> booking.staff_users.cis_user_id
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
booking.policy_approvals.cancellation_policy_id -> booking.cancellation_policies.id
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
booking.trip_plan_components.created_by -> booking.staff_users.cis_user_id
booking.trip_plan_components.hotel_room_type_id -> booking.hotel_room_types.id
booking.trip_plan_components.service_id -> booking.services.id
booking.trip_plan_components.trip_plan_id -> booking.trip_plans.id
booking.trip_plans.created_by -> booking.staff_users.cis_user_id
booking.trip_plans.updated_by -> booking.staff_users.cis_user_id
booking.version_item_costs.entered_by -> booking.staff_users.cis_user_id
booking.version_item_costs.supplier_rate_id -> booking.supplier_rates.id
booking.version_item_costs.version_item_id -> booking.trip_case_version_itinerary.id
crm.audit_event.tenant_id -> crm.tenant.tenant_id
crm.audit_event_legacy.tenant_id -> crm.tenant.tenant_id
crm.audit_event_p202611.tenant_id -> crm.tenant.tenant_id
crm.audit_event_p202612.tenant_id -> crm.tenant.tenant_id
crm.audit_event_p202701.tenant_id -> crm.tenant.tenant_id
crm.audit_export_tenant.tenant_id -> crm.tenant.tenant_id
crm.consent.submission_id -> crm.form_submission.submission_id
crm.consent.tenant_id -> crm.tenant.tenant_id
crm.consent.traveler_id -> crm.traveler.traveler_id
crm.dispatch_queue.tenant_id -> crm.tenant.tenant_id
crm.dispatch_queue.(tenant_id,traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.dispatch_queue.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.document.tenant_id -> crm.tenant.tenant_id
crm.document.(tenant_id,traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.document.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.erasure_request.tenant_id -> crm.tenant.tenant_id
crm.form_definition.tenant_id -> crm.tenant.tenant_id
crm.form_submission.intake_form_id -> crm.intake_form.intake_form_id
crm.form_submission.tenant_id -> crm.tenant.tenant_id
crm.form_submission.traveler_id -> crm.traveler.traveler_id
crm.form_submission.trip_id -> crm.trip.trip_id
crm.intake_form.default_owner_member_id -> crm.member.member_id
crm.intake_form.form_definition_id -> crm.form_definition.form_definition_id
crm.intake_form.tenant_id -> crm.tenant.tenant_id
crm.integration_credential.tenant_id -> crm.tenant.tenant_id
crm.job.parent_job_id -> crm.job.id
crm.legal_hold.tenant_id -> crm.tenant.tenant_id
crm.lifecycle_run.tenant_id -> crm.tenant.tenant_id
crm.llm_call.tenant_id -> crm.tenant.tenant_id
crm.member.tenant_id -> crm.tenant.tenant_id
crm.member_invitation.tenant_id -> crm.tenant.tenant_id
crm.member_invitation.(tenant_id,member_id) -> crm.member.(tenant_id,member_id)
crm.note.tenant_id -> crm.tenant.tenant_id
crm.note.traveler_id -> crm.traveler.traveler_id
crm.note.trip_id -> crm.trip.trip_id
crm.owner_recovery_request.tenant_id -> crm.tenant.tenant_id
crm.owner_recovery_request.(tenant_id,candidate_member_id) -> crm.member.(tenant_id,member_id)
crm.placeholder_map.tenant_id -> crm.tenant.tenant_id
crm.placeholder_map.(tenant_id,llm_call_id) -> crm.llm_call.(tenant_id,llm_call_id)
crm.profile_history.tenant_id -> crm.tenant.tenant_id
crm.profile_history.(tenant_id,traveler_token) -> crm.traveler_profile.(tenant_id,traveler_token)
crm.task.assignee_member_id -> crm.member.member_id
crm.task.tenant_id -> crm.tenant.tenant_id
crm.task.trip_id -> crm.trip.trip_id
crm.tenant_entitlement.tenant_id -> crm.tenant.tenant_id
crm.tenant_key.tenant_id -> crm.tenant.tenant_id
crm.tenant_settings.tenant_id -> crm.tenant.tenant_id
crm.traveler.owner_member_id -> crm.member.member_id
crm.traveler.referrer_traveler_id -> crm.traveler.traveler_id
crm.traveler.tenant_id -> crm.tenant.tenant_id
crm.traveler_health.consent_id -> crm.consent.consent_id
crm.traveler_health.tenant_id -> crm.tenant.tenant_id
crm.traveler_health.(tenant_id,traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.traveler_profile.tenant_id -> crm.tenant.tenant_id
crm.traveler_relation.inverse_id -> crm.traveler_relation.relation_id
crm.traveler_relation.tenant_id -> crm.tenant.tenant_id
crm.traveler_relation.(tenant_id,from_traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.traveler_relation.(tenant_id,to_traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.trip.intake_form_id -> crm.intake_form.intake_form_id
crm.trip.owner_member_id -> crm.member.member_id
crm.trip.tenant_id -> crm.tenant.tenant_id
crm.trip_commitment.tenant_id -> crm.tenant.tenant_id
crm.trip_commitment.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.trip_party.tenant_id -> crm.tenant.tenant_id
crm.trip_party.traveler_token -> crm.traveler_profile.traveler_token
crm.trip_party.trip_id -> crm.trip.trip_id
crm.trip_stage_history.tenant_id -> crm.tenant.tenant_id
crm.trip_stage_history.trip_id -> crm.trip.trip_id
crm.trip_traveler.tenant_id -> crm.tenant.tenant_id
crm.trip_traveler.traveler_id -> crm.traveler.traveler_id
crm.trip_traveler.trip_id -> crm.trip.trip_id
geo.graph_edge.build_id -> geo.graph_build.build_id
geo.graph_edge.from_destination_id -> shared.destinations.id
geo.graph_edge.to_destination_id -> shared.destinations.id
geo.graph_node.build_id -> geo.graph_build.build_id
geo.graph_node.destination_id -> shared.destinations.id
geo.place_merge.keeper_id -> shared.destinations.id
geo.place_merge.merged_id -> shared.destinations.id
geo.place_name.destination_id -> shared.destinations.id
geo.place_name.place_card_id -> acp_shared.place_card.card_id
geo.place_outlier.destination_id -> shared.destinations.id
geo.place_pair_verdict.hi_id -> shared.destinations.id
geo.place_pair_verdict.lo_id -> shared.destinations.id
geo.place_shape.destination_id -> shared.destinations.id
geo.tour_day.overnight_destination_id -> shared.destinations.id
geo.tour_junction.build_id -> geo.graph_build.build_id
geo.tour_junction.destination_a -> shared.destinations.id
geo.tour_junction.destination_b -> shared.destinations.id
geo.tour_leg.build_id -> geo.graph_build.build_id
geo.tour_leg.end_destination_id -> shared.destinations.id
geo.tour_leg.start_destination_id -> shared.destinations.id
geo.tour_place.destination_id -> shared.destinations.id
geo.tour_place.place_card_id -> acp_shared.place_card.card_id
geo.tour_segment.build_id -> geo.graph_build.build_id
geo.tour_segment.destination_id -> shared.destinations.id
geo.tour_segment.from_destination_id -> shared.destinations.id
geo.tour_segment.to_destination_id -> shared.destinations.id
geo.tour_stop.build_id -> geo.graph_build.build_id
geo.tour_stop.destination_id -> shared.destinations.id
gold_aa_internal.content_exports.tenant_id -> shared.tenants.tenant_id
gold_aa_internal.published_tours.generated_content_id -> silver_aa_internal.generated_content.id
gold_aa_internal.published_tours.quality_score_id -> silver_aa_internal.quality_scores.id
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
tripplanner.sessions.customer_id -> tripplanner.customers.id
tripplanner.trip_drafts.session_id -> tripplanner.sessions.id
tripplanner.trip_events.session_id -> tripplanner.sessions.id
```

## Table activity

`pg_stat_user_tables` counters since the last stats reset (never), as of the Verified line. Use them with the 14-day rule of the Dead Table Registry, not alone.

| table | ~rows | size | seq scans | idx scans | ins / upd / del | dead tuples | last autovacuum |
|---|---|---|---|---|---|---|---|
| `acp_contract.atom_decompose_jobs` | 0 | 104 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_contract.atom_embedding` | 7728 | 126.6 MB | 421 | 71846 | 5330 / 0 / 0 | 0 | 2026-10-10 13:30 |
| `acp_contract.atom_matches` | 10947 | 3.4 MB | 10 | 34456 | 5200 / 24963 / 0 | 864 | 2026-10-08 14:00 |
| `acp_contract.atom_ranking` | 105606 | 67.1 MB | 29341 | 10015 | 6366311 / 6269255 / 6293213 | 0 | 2026-10-24 10:26 |
| `acp_contract.atom_segment` | 13606 | 3.8 MB | 3824 | 7551255 | 15740 / 131892 / 5045 | 974 | 2026-10-16 08:22 |
| `acp_contract.atom_segment_alias` | 438 | 352 kB | 9068 | 213333 | 1690 / 231643 / 1475 | 12 | 2026-10-24 09:04 |
| `acp_contract.atom_segment_member` | 26280 | 5.5 MB | 7228 | 956990 | 40588 / 471 / 18969 | 1 | 2026-10-24 10:13 |
| `acp_contract.atomize_day_fingerprint` | 10617 | 2.1 MB | 13 | 8735 | 7601 / 43 / 0 | 4 | 2026-10-10 07:13 |
| `acp_contract.hub` | 64 | 152 kB | 1634 | 9863 | 52 / 1031 / 774 | 0 | 2026-10-24 10:26 |
| `acp_contract.question_embedding` | 847 | 8.2 MB | 45 | 97 | 77 / 0 / 0 | 0 |  |
| `acp_contract.route` | 9063 | 5.6 MB | 676 | 8544664 | 8667 / 7654 / 0 | 247 | 2026-10-16 08:25 |
| `acp_contract.route_pick` |  | 48 kB | 4 | 9 | 0 / 0 / 0 | 0 |  |
| `acp_contract.s1_from_atom_runs` |  | 64 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_contract.search_demand` | 5089 | 1.7 MB | 3194 | 1548 | 509 / 289 / 0 | 237 |  |
| `acp_contract.segment_research_log` | 1337 | 568 kB | 4803 | 14657 | 219 / 0 / 0 | 0 |  |
| `acp_contract.tour_atoms` | 35737 | 22.1 MB | 11606 | 16118037 | 24098 / 16830 / 0 | 60 | 2026-10-24 10:18 |
| `acp_deliver.tenant_tour_pages` | 0 | 40 kB | 2069 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.acp_output_rules` |  | 48 kB | 39 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.acp_quota_ledger` |  | 56 kB | 3 | 15 | 6 / 0 / 1 | 1 |  |
| `acp_shared.angle_gate_option` | 57 | 296 kB | 2544 | 45610 | 69 / 72 / 0 | 20 | 2026-10-16 03:32 |
| `acp_shared.angle_gate_request` | 21 | 128 kB | 10542 | 13905 | 25 / 65 / 0 | 13 | 2026-10-16 08:36 |
| `acp_shared.atom_place_card` | 291 | 120 kB | 14341 | 403678 | 298 / 28 / 0 | 27 |  |
| `acp_shared.audit_log` | 1728 | 1.3 MB | 424 | 4831 | 1824 / 0 / 0 | 0 | 2026-10-16 12:16 |
| `acp_shared.content_piece` | 317 | 10.7 MB | 16074 | 82994 | 324 / 647 / 0 | 81 | 2026-10-20 10:43 |
| `acp_shared.content_piece_label` |  | 48 kB | 14 | 20398 | 1 / 0 / 0 | 0 |  |
| `acp_shared.debate_brand_fit_cache` | 414 | 504 kB | 179 | 2294 | 662 / 0 / 275 | 27 | 2026-10-24 09:02 |
| `acp_shared.facts` |  | 64 kB | 57 | 3593 | 0 / 2 / 0 | 2 |  |
| `acp_shared.marketplace_portfolios` |  | 32 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.place_card` | 112 | 344 kB | 7070 | 502672 | 128 / 123 / 18 | 22 | 2026-10-14 10:18 |
| `acp_shared.place_card_alias` | 361 | 136 kB | 249 | 614 | 409 / 20 / 0 | 20 |  |
| `acp_shared.place_card_miss` |  | 32 kB | 6 | 103 | 3 / 0 / 0 | 0 |  |
| `acp_shared.publish_log` |  | 96 kB | 56 | 6512 | 7 / 14 / 0 | 11 |  |
| `acp_shared.quarter_plan` | 6 | 88 kB | 643 | 52 | 0 / 0 / 0 | 0 |  |
| `acp_shared.quarter_plan_version` | 0 | 112 kB | 619 | 52 | 0 / 0 / 0 | 0 |  |
| `acp_shared.subject` | 409 | 600 kB | 5860 | 4226 | 674 / 766 / 265 | 81 | 2026-10-22 10:44 |
| `acp_shared.tenant_atom_state` | 0 | 80 kB | 21 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.tenant_config` |  | 32 kB | 9 | 356 | 1 / 0 / 1 | 1 |  |
| `acp_shared.year_plan` |  | 40 kB | 13 | 608 | 0 / 0 / 0 | 0 |  |
| `booking.audit_logs` | 108 | 184 kB | 98 | 0 | 114 / 0 / 0 | 0 |  |
| `booking.b2b_cancellations` |  | 80 kB | 5 | 4 | 2 / 0 / 0 | 0 |  |
| `booking.b2b_hold_lines` | 12 | 72 kB | 112 | 292 | 13 / 5 / 0 | 5 |  |
| `booking.b2b_holds` | 2 | 128 kB | 3779 | 452 | 13 / 16 / 0 | 16 |  |
| `booking.b2b_partners` |  | 64 kB | 4 | 158 | 2 / 0 / 0 | 1 |  |
| `booking.b2b_quote_lines` |  | 48 kB | 3 | 20 | 20 / 0 / 0 | 0 |  |
| `booking.b2b_quotes` |  | 64 kB | 4 | 58 | 20 / 0 / 0 | 0 |  |
| `booking.cancellation_policies` |  | 48 kB | 3 | 17 | 1 / 0 / 0 | 0 |  |
| `booking.countries` |  | 32 kB | 92 | 141 | 17 / 0 / 0 | 0 |  |
| `booking.customer_otps` |  | 24 kB | 4 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.customer_sessions` |  | 32 kB | 5 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.customers` | 1 | 104 kB | 2607 | 4 | 10 / 0 / 0 | 0 |  |
| `booking.departure_incidents` |  | 32 kB | 3 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.departures` |  | 64 kB | 7 | 121 | 5 / 0 / 0 | 0 |  |
| `booking.fx_rates` |  | 48 kB | 89 | 17 | 3 / 0 / 0 | 0 |  |
| `booking.hotel_room_types` |  | 48 kB | 19 | 214 | 3 / 0 / 0 | 0 |  |
| `booking.hotels` |  | 136 kB | 50 | 92 | 2 / 0 / 0 | 0 |  |
| `booking.inbox_cursor` | 2 | 64 kB | 22513 | 10179 | 2 / 10079 / 0 | 32 | 2026-10-24 09:46 |
| `booking.inbox_events` | 5 | 136 kB | 2615 | 70 | 15 / 15 / 0 | 15 |  |
| `booking.job` | 6899 | 3.5 MB | 18284 | 940453 | 10112 / 20221 / 3213 | 170 | 2026-10-24 09:11 |
| `booking.media_files` |  | 24 kB | 4 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.notification_reads` |  | 24 kB | 4 | 2926 | 0 / 0 / 0 | 0 |  |
| `booking.notifications` | 1 | 96 kB | 701 | 0 | 22 / 0 / 0 | 0 |  |
| `booking.outbox` |  | 96 kB | 5 | 2072 | 1 / 1 / 0 | 1 |  |
| `booking.policy_approvals` | 6 | 80 kB | 160 | 53 | 8 / 0 / 0 | 0 |  |
| `booking.pricing_rules` |  | 48 kB | 82 | 60 | 4 / 0 / 0 | 0 |  |
| `booking.services` |  | 152 kB | 47 | 112 | 2 / 0 / 0 | 0 |  |
| `booking.settings` |  | 32 kB | 11 | 71 | 8 / 0 / 0 | 0 |  |
| `booking.staff_assignments` |  | 64 kB | 41 | 2200 | 1 / 0 / 0 | 0 |  |
| `booking.staff_users` | 3 | 64 kB | 319 | 4488 | 6 / 34 / 0 | 34 |  |
| `booking.supplier_contracts` |  | 64 kB | 5 | 381 | 3 / 7 / 0 | 7 |  |
| `booking.supplier_rates` |  | 80 kB | 11 | 229 | 5 / 0 / 0 | 0 |  |
| `booking.suppliers` |  | 144 kB | 129 | 126 | 2 / 1 / 0 | 1 |  |
| `booking.trip_case_countries` |  | 40 kB | 4 | 583 | 3 / 0 / 0 | 0 |  |
| `booking.trip_case_legs` | 8 | 64 kB | 725 | 117 | 14 / 8 / 0 | 8 |  |
| `booking.trip_case_status_history` | 1 | 64 kB | 106 | 0 | 18 / 0 / 0 | 0 |  |
| `booking.trip_case_status_transitions` |  | 32 kB | 3 | 53 | 12 / 0 / 0 | 0 |  |
| `booking.trip_case_version_itinerary` | 4 | 80 kB | 317 | 31 | 23 / 4 / 0 | 4 |  |
| `booking.trip_case_versions` |  | 80 kB | 30 | 908 | 8 / 12 / 0 | 12 |  |
| `booking.trip_cases` | 10 | 176 kB | 1314 | 17 | 13 / 5 / 0 | 5 |  |
| `booking.trip_plan_components` |  | 48 kB | 8 | 42 | 2 / 0 / 0 | 0 |  |
| `booking.trip_plans` |  | 64 kB | 375 | 13823 | 2 / 1 / 0 | 1 |  |
| `booking.version_item_costs` | 4 | 64 kB | 51 | 19 | 10 / 0 / 1 | 1 |  |
| `crm.audit_event` |  | 0 B | 0 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.audit_event_legacy` | 114 | 136 kB | 12 | 11 | 126 / 0 / 0 | 0 |  |
| `crm.audit_event_p202611` |  | 32 kB | 3 | 2 | 0 / 0 / 0 | 0 |  |
| `crm.audit_event_p202612` |  | 32 kB | 3 | 2 | 0 / 0 / 0 | 0 |  |
| `crm.audit_event_p202701` |  | 32 kB | 3 | 2 | 0 / 0 / 0 | 0 |  |
| `crm.audit_export_manifest` |  | 64 kB | 3 | 28 | 14 / 0 / 0 | 0 |  |
| `crm.audit_export_tenant` |  | 24 kB | 1 | 143 | 3 / 14 / 0 | 14 |  |
| `crm.consent` |  | 48 kB | 2 | 6 | 18 / 0 / 0 | 0 |  |
| `crm.dispatch_queue` |  | 32 kB | 3 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.document` |  | 40 kB | 4 | 24 | 0 / 0 / 0 | 0 |  |
| `crm.erasure_request` |  | 24 kB | 3 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.form_definition` |  | 48 kB | 2 | 27 | 3 / 0 / 0 | 0 |  |
| `crm.form_submission` |  | 112 kB | 5 | 145 | 9 / 9 / 0 | 9 |  |
| `crm.intake_form` |  | 48 kB | 20 | 54 | 3 / 0 / 0 | 0 |  |
| `crm.integration_credential` |  | 24 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.job` | 1852 | 968 kB | 8977 | 130166 | 1877 / 3752 / 0 | 10 | 2026-10-24 10:28 |
| `crm.legal_hold` |  | 24 kB | 2 | 3 | 0 / 0 / 0 | 0 |  |
| `crm.lifecycle_run` |  | 24 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.llm_call` |  | 32 kB | 4 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.llm_usage_daily` |  | 16 kB | 1 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.member` | 6 | 80 kB | 821 | 288 | 13 / 1 / 0 | 1 |  |
| `crm.member_invitation` |  | 80 kB | 4 | 288 | 3 / 4 / 0 | 5 |  |
| `crm.note` |  | 48 kB | 2 | 22 | 9 / 0 / 0 | 0 |  |
| `crm.owner_recovery_request` |  | 24 kB | 2 | 37 | 0 / 0 / 0 | 0 |  |
| `crm.placeholder_map` |  | 32 kB | 7 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.profile_history` |  | 24 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.status_transition` | 57 | 32 kB | 5 | 82 | 57 / 0 / 0 | 0 |  |
| `crm.task` |  | 80 kB | 4 | 109 | 9 / 0 / 0 | 0 |  |
| `crm.tenant` |  | 32 kB | 6 | 798 | 3 / 0 / 0 | 0 |  |
| `crm.tenant_entitlement` |  | 16 kB | 1 | 14 | 0 / 0 / 0 | 0 |  |
| `crm.tenant_key` |  | 64 kB | 3 | 20 | 1 / 0 / 0 | 0 |  |
| `crm.tenant_settings` |  | 16 kB | 4 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.traveler` | 8 | 136 kB | 175 | 13 | 9 / 0 / 0 | 0 |  |
| `crm.traveler_health` |  | 24 kB | 2 | 6 | 0 / 0 / 0 | 0 |  |
| `crm.traveler_profile` | 2 | 48 kB | 17 | 2 | 9 / 0 / 0 | 0 |  |
| `crm.traveler_relation` |  | 40 kB | 4 | 6 | 0 / 0 / 0 | 0 |  |
| `crm.trip` | 2 | 72 kB | 240 | 34 | 9 / 14 / 0 | 14 |  |
| `crm.trip_commitment` |  | 32 kB | 3 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.trip_party` | 2 | 64 kB | 10 | 0 | 9 / 0 / 0 | 0 |  |
| `crm.trip_stage_history` |  | 48 kB | 2 | 22 | 23 / 0 / 0 | 0 |  |
| `crm.trip_traveler` |  | 80 kB | 4 | 184 | 9 / 0 / 0 | 0 |  |
| `geo.geocode_call` |  | 48 kB | 14 | 641 | 11 / 3 / 0 | 3 |  |
| `geo.graph_build` | 2 | 96 kB | 711337 | 123573 | 14 / 27 / 11 | 38 |  |
| `geo.graph_edge` | 1779 | 776 kB | 28 | 7 | 5022 / 0 / 3243 | 0 | 2026-10-24 03:33 |
| `geo.graph_node` | 1341 | 824 kB | 60 | 44 | 3671 / 0 / 2330 | 0 | 2026-10-24 03:33 |
| `geo.place_dedupe_country` |  | 16 kB | 9 | 0 | 0 / 0 / 0 | 0 |  |
| `geo.place_merge` |  | 40 kB | 7 | 67 | 0 / 0 / 0 | 0 |  |
| `geo.place_name` | 1719 | 576 kB | 472 | 3609 | 1729 / 1553 / 0 | 175 | 2026-10-23 14:43 |
| `geo.place_outlier` |  | 16 kB | 32 | 133 | 0 / 0 / 0 | 0 |  |
| `geo.place_pair_verdict` |  | 24 kB | 69 | 0 | 0 / 0 / 0 | 0 |  |
| `geo.place_shape` | 39 | 488 kB | 1845 | 6046 | 39 / 39 / 0 | 39 |  |
| `geo.tour_build` | 110 | 184 kB | 429 | 417 | 123 / 123 / 0 | 44 |  |
| `geo.tour_day` | 1084 | 536 kB | 124 | 410 | 1098 / 247 / 0 | 112 | 2026-10-15 00:02 |
| `geo.tour_junction` | 22662 | 6 MB | 1192 | 1 | 65828 / 0 / 43166 | 0 | 2026-10-24 03:33 |
| `geo.tour_leg` | 16041 | 11.7 MB | 2691 | 2 | 45277 / 0 / 29236 | 0 | 2026-10-24 03:33 |
| `geo.tour_place` | 2473 | 40.5 MB | 3863 | 1370480 | 2480 / 1084 / 0 | 170 | 2026-10-22 03:18 |
| `geo.tour_segment` | 192 | 480 kB | 205145 | 374621 | 662 / 0 / 470 | 64 | 2026-10-24 02:21 |
| `geo.tour_stop` | 3081 | 1.3 MB | 5605 | 3067 | 8984 / 0 / 5903 | 0 | 2026-10-24 03:33 |
| `gold_aa_internal.content_exports` |  | 24 kB | 1935 | 0 | 0 / 0 / 0 | 0 |  |
| `gold_aa_internal.published_tours` | 892 | 6.8 MB | 49320 | 16610838 | 497 / 1536 / 0 | 110 | 2026-10-23 11:33 |
| `gold_aa_internal.tenant_tour_versions` | 53 | 648 kB | 27733 | 4343 | 55 / 116 / 0 | 19 | 2026-10-15 14:24 |
| `gold_aa_internal.tour_lifecycle_event` |  | 80 kB | 2527 | 33104 | 10 / 0 / 0 | 2 |  |
| `gold_aa_internal.webhook_deliveries` |  | 24 kB | 1940 | 0 | 0 / 0 / 0 | 0 |  |
| `public.checkpoint_migrations` |  | 24 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.acp_runs` |  | 40 kB | 11 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.admin_users` | 10 | 80 kB | 12715 | 75345 | 8 / 332 / 4 | 14 |  |
| `shared.alert_recipient` | 2 | 64 kB | 3774 | 154 | 2 / 1271 / 0 | 24 |  |
| `shared.cost_explorer_app_snapshot` | 5358 | 1.4 MB | 97 | 8 | 5358 / 0 / 0 | 0 | 2026-10-24 02:43 |
| `shared.cost_explorer_snapshot` | 1678 | 2 MB | 506 | 10 | 7572 / 0 / 8075 | 0 | 2026-10-23 21:00 |
| `shared.decision_cache_hits_daily` | 261 | 128 kB | 662 | 10232 | 261 / 9969 / 0 | 16 | 2026-10-24 10:26 |
| `shared.decision_log` | 387843 | 379.4 MB | 503 | 748155 | 310886 / 4 / 695728 | 0 | 2026-10-24 10:24 |
| `shared.decision_question` | 5 | 72 kB | 9731 | 670 | 1 / 20 / 0 | 3 |  |
| `shared.destinations` | 1927 | 1.1 MB | 55936 | 6899867 | 786 / 1401 / 0 | 145 | 2026-10-14 14:52 |
| `shared.dfs_balance_snapshot` |  | 320 kB | 2 | 1509 | 20 / 0 / 0 | 0 |  |
| `shared.dfs_call_log` | 2545 | 1 MB | 2048 | 7411 | 701 / 0 / 0 | 0 |  |
| `shared.jev_credit_topup` |  | 48 kB | 198 | 3 | 2 / 0 / 0 | 0 |  |
| `shared.jev_tenant_allowlist` |  | 32 kB | 7723 | 4732 | 4 / 0 / 7 | 7 |  |
| `shared.job` | 3207 | 12.5 MB | 16509 | 1050605 | 2590 / 28253 / 0 | 96 | 2026-10-24 10:03 |
| `shared.job_worker` | 150 | 312 kB | 112642 | 332166 | 355 / 98145 / 266 | 49 | 2026-10-24 10:21 |
| `shared.llm_call_daily` |  | 48 kB | 990 | 354 | 5 / 0 / 0 | 0 |  |
| `shared.llm_call_log` | 284344 | 145.8 MB | 9159 | 23648286 | 169688 / 0 / 200 | 200 | 2026-10-24 09:26 |
| `shared.llm_model_catalog` |  | 32 kB | 1735 | 98 | 3 / 5 / 0 | 2 |  |
| `shared.llm_role_config` |  | 32 kB | 1107 | 7540 | 17 / 24 / 6 | 12 |  |
| `shared.llm_shadow_log` | 5554 | 11.9 MB | 10 | 10 | 3001 / 0 / 0 | 0 | 2026-10-08 07:37 |
| `shared.membership_plans` |  | 48 kB | 3434 | 3615 | 0 / 0 / 0 | 0 |  |
| `shared.notifications` | 12 | 104 kB | 18904 | 0 | 27 / 23 / 0 | 25 |  |
| `shared.pipeline_jobs` | 523 | 480 kB | 11 | 22 | 0 / 0 / 0 | 0 |  |
| `shared.pipeline_lessons` |  | 24 kB | 3 | 1960 | 0 / 0 / 0 | 0 |  |
| `shared.pipeline_runs` | 46 | 208 kB | 6704 | 6046 | 0 / 946 / 0 | 36 |  |
| `shared.place_photo` | 3232 | 2.6 MB | 12325 | 3532110 | 0 / 9696 / 0 | 173 | 2026-10-21 05:52 |
| `shared.prompt_eval_runs` |  | 48 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.rerun_wave` |  | 80 kB | 6 | 353 | 6 / 20 / 0 | 11 |  |
| `shared.schema_versions` | 301 | 104 kB | 1504 | 673 | 123 / 0 / 0 | 7 |  |
| `shared.spend_budget` |  | 32 kB | 1160 | 201 | 6 / 0 / 0 | 0 |  |
| `shared.staff_app_grant` |  | 32 kB | 166 | 85 | 2 / 0 / 1 | 1 |  |
| `shared.tenant_api_usage` | 148083 | 35.8 MB | 9 | 27965 | 106454 / 0 / 200 | 206 | 2026-10-22 01:37 |
| `shared.tenant_api_usage_monthly` |  | 48 kB | 11 | 47 | 3 / 0 / 0 | 0 |  |
| `shared.tenant_brand_rule_versions` |  | 64 kB | 3 | 33 | 0 / 0 / 0 | 0 |  |
| `shared.tenant_brand_rules` | 27 | 232 kB | 25465 | 1192 | 25 / 56 / 1 | 13 | 2026-10-22 09:12 |
| `shared.tenant_brand_rules_deleted_aa404` |  | 96 kB | 3 | 8 | 0 / 0 / 0 | 0 |  |
| `shared.tenant_export_config` |  | 48 kB | 3 | 9 | 0 / 0 / 0 | 0 |  |
| `shared.tenant_integrations` |  | 64 kB | 30 | 2271 | 14 / 11 / 14 | 8 |  |
| `shared.tenant_rewrite_usage` | 6 | 64 kB | 125 | 151 | 4 / 50 / 0 | 3 | 2026-10-20 03:09 |
| `shared.tenant_seo_config` |  | 48 kB | 11 | 1541 | 4 / 11 / 0 | 11 |  |
| `shared.tenants` | 4 | 80 kB | 240989 | 3202 | 6 / 28 / 1 | 9 |  |
| `shared.unmapped_market_requests` |  | 32 kB | 4 | 409 | 0 / 0 / 0 | 0 |  |
| `silver_aa_internal.generated_content` | 1516 | 15.4 MB | 3592 | 658205 | 1085 / 512 / 0 | 106 | 2026-10-08 02:59 |
| `silver_aa_internal.quality_scores` | 1550 | 2 MB | 568023 | 1251 | 1092 / 1054 / 7 | 189 | 2026-10-10 10:07 |
| `silver_aa_internal.raw_sources` | 34 | 96 kB | 1073 | 2038 | 0 / 0 / 0 | 0 |  |
| `silver_aa_internal.raw_tours` | 987 | 5 MB | 40748 | 22324612 | 0 / 937 / 0 | 87 | 2026-10-10 09:43 |
| `silver_aa_internal.review_queue` | 229 | 176 kB | 58693 | 26290 | 178 / 109 / 0 | 66 | 2026-10-08 03:05 |
| `silver_aa_internal.seo_context` | 898 | 1.2 MB | 2284 | 709024 | 506 / 0 / 0 | 12 |  |
| `silver_aa_internal.upload_staging` |  | 104 kB | 11 | 0 | 0 / 0 / 0 | 0 |  |
| `tripplanner.component_id_map` | 750 | 136 kB | 81 | 1299 | 750 / 0 / 0 | 0 |  |
| `tripplanner.customers` |  | 64 kB | 18 | 25 | 7 / 7 / 1 | 8 |  |
| `tripplanner.llm_spend_daily` | 8 | 64 kB | 928 | 1637 | 8 / 1502 / 0 | 50 | 2026-10-16 09:06 |
| `tripplanner.narration_cache` |  | 48 kB | 5 | 12 | 1 / 1 / 0 | 1 |  |
| `tripplanner.outbox` |  | 96 kB | 15 | 20191 | 8 / 0 / 3 | 1 |  |
| `tripplanner.sessions` | 93 | 80 kB | 761 | 386 | 77 / 42 / 3 | 37 |  |
| `tripplanner.trip_drafts` | 98 | 120 kB | 380 | 466 | 75 / 260 / 1 | 14 |  |
| `tripplanner.trip_events` | 416 | 184 kB | 910 | 654 | 335 / 0 / 6 | 5 |  |

## Unused indexes

Non-PK, non-unique indexes with 0 scans since the stats reset. A drop candidate only after 30 days at 0 (standards C5.2d), through expand/contract.

- `acp_contract.idx_atom_decompose_jobs_status` on `atom_decompose_jobs` (16 kB)
- `acp_contract.idx_s1_from_atom_runs_prompt_version` on `s1_from_atom_runs` (16 kB)
- `acp_contract.idx_s1_from_atom_runs_tour_id` on `s1_from_atom_runs` (16 kB)
- `acp_shared.idx_output_rules_active` on `acp_output_rules` (16 kB)
- `acp_shared.idx_angle_gate_request_status` on `angle_gate_request` (16 kB)
- `acp_shared.idx_angle_gate_request_subject` on `angle_gate_request` (16 kB)
- `acp_shared.idx_angle_gate_request_tenant` on `angle_gate_request` (16 kB)
- `acp_shared.idx_content_piece_embedding` on `content_piece` (2.3 MB)
- `acp_shared.idx_content_piece_label_label` on `content_piece_label` (16 kB)
- `acp_shared.idx_quarter_plan_year_plan_id` on `quarter_plan` (16 kB)
- `acp_shared.idx_quarter_plan_version_approval_status` on `quarter_plan_version` (16 kB)
- `acp_shared.idx_tenant_atom_state_tenant` on `tenant_atom_state` (16 kB)
- `booking.audit_logs_actor_ref_idx` on `audit_logs` (16 kB)
- `booking.audit_logs_created_idx` on `audit_logs` (16 kB)
- `booking.audit_logs_entity_idx` on `audit_logs` (16 kB)
- `booking.b2b_cancellations_partner_idx` on `b2b_cancellations` (16 kB)
- `booking.b2b_hold_lines_on_request_idx` on `b2b_hold_lines` (8 kB)
- `booking.b2b_holds_proposal_day_idx` on `b2b_holds` (16 kB)
- `booking.b2b_holds_quote_idx` on `b2b_holds` (16 kB)
- `booking.b2b_partners_client_idx` on `b2b_partners` (16 kB)
- `booking.b2b_quotes_partner_idx` on `b2b_quotes` (16 kB)
- `booking.customer_otps_customer_idx` on `customer_otps` (8 kB)
- `booking.customer_sessions_customer_idx` on `customer_sessions` (8 kB)
- `booking.customers_merge_review_idx` on `customers` (16 kB)
- `booking.customers_phone_lookup_idx` on `customers` (8 kB)
- `booking.departure_incidents_departure_idx` on `departure_incidents` (8 kB)
- `booking.hotels_country_idx` on `hotels` (16 kB)
- `booking.hotels_destination_idx` on `hotels` (8 kB)
- `booking.hotels_updated_idx` on `hotels` (16 kB)
- `booking.inbox_events_pending_idx` on `inbox_events` (16 kB)
- `booking.inbox_events_redact_due_idx` on `inbox_events` (16 kB)
- `booking.inbox_events_status_idx` on `inbox_events` (16 kB)
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
- `booking.trip_cases_party_idx` on `trip_cases` (16 kB)
- `booking.trip_cases_source_idx` on `trip_cases` (16 kB)
- `booking.version_item_costs_rate_idx` on `version_item_costs` (16 kB)
- `crm.audit_event_object_idx` on `audit_event` (0 B)
- `crm.audit_event_tenant_at_idx` on `audit_event` (0 B)
- `crm.audit_event_p202611_tenant_id_object_kind_object_id_idx` on `audit_event_p202611` (8 kB)
- `crm.audit_event_p202612_tenant_id_object_kind_object_id_idx` on `audit_event_p202612` (8 kB)
- `crm.audit_event_p202701_tenant_id_object_kind_object_id_idx` on `audit_event_p202701` (8 kB)
- `crm.dispatch_queue_due_idx` on `dispatch_queue` (8 kB)
- `crm.dispatch_queue_traveler_idx` on `dispatch_queue` (8 kB)
- `crm.form_submission_redact_idx` on `form_submission` (16 kB)
- `crm.job_parent_idx` on `job` (8 kB)
- `crm.lifecycle_run_tenant_idx` on `lifecycle_run` (8 kB)
- `crm.llm_call_tenant_at_idx` on `llm_call` (8 kB)
- `crm.placeholder_map_expires_idx` on `placeholder_map` (8 kB)
- `crm.profile_history_token_idx` on `profile_history` (8 kB)
- `crm.task_open_idx` on `task` (16 kB)
- `crm.traveler_archived_idx` on `traveler` (8 kB)
- `crm.traveler_name_bidx_idx` on `traveler` (16 kB)
- `crm.traveler_name_token_bidx_idx` on `traveler` (24 kB)
- `crm.traveler_owner_member_idx` on `traveler` (8 kB)
- `crm.traveler_phone_bidx_idx` on `traveler` (8 kB)
- `crm.traveler_referrer_idx` on `traveler` (8 kB)
- `crm.traveler_relation_to_idx` on `traveler_relation` (8 kB)
- `crm.trip_owner_idx` on `trip` (8 kB)
- `crm.trip_commitment_trip_idx` on `trip_commitment` (8 kB)
- `crm.trip_party_token_idx` on `trip_party` (16 kB)
- `geo.place_merge_country_idx` on `place_merge` (8 kB)
- `geo.place_merge_keeper_idx` on `place_merge` (8 kB)
- `geo.place_pair_verdict_hi_idx` on `place_pair_verdict` (8 kB)
- `geo.place_shape_osm_idx` on `place_shape` (16 kB)
- `geo.tour_leg_countries_gin` on `tour_leg` (192 kB)
- `geo.tour_place_unlinked_idx` on `tour_place` (72 kB)
- `gold_aa_internal.idx_pt_embedding` on `published_tours` (168 kB)
- `gold_aa_internal.idx_ttv_status` on `tenant_tour_versions` (16 kB)
- `gold_aa_internal.idx_ttv_tenant_id` on `tenant_tour_versions` (16 kB)
- `gold_aa_internal.tenant_tour_versions_job_idx` on `tenant_tour_versions` (16 kB)
- `gold_aa_internal.tour_lifecycle_event_tour_idx` on `tour_lifecycle_event` (16 kB)
- `gold_aa_internal.idx_aa_internal_webhook_status` on `webhook_deliveries` (8 kB)
- `shared.idx_acp_runs_country` on `acp_runs` (8 kB)
- `shared.idx_acp_runs_status` on `acp_runs` (8 kB)
- `shared.cost_explorer_app_snapshot_fetched_idx` on `cost_explorer_app_snapshot` (88 kB)
- `shared.idx_dfs_call_log_live` on `dfs_call_log` (32 kB)
- `shared.idx_llm_call_log_account` on `llm_call_log` (528 kB)
- `shared.idx_llm_call_log_model_created` on `llm_call_log` (19.9 MB)
- `shared.idx_notif_event_type` on `notifications` (16 kB)
- `shared.idx_notif_tenant_unread` on `notifications` (16 kB)
- `shared.ix_pipeline_jobs_created` on `pipeline_jobs` (40 kB)
- `shared.idx_pipeline_runs_status` on `pipeline_runs` (16 kB)
- `shared.idx_prompt_eval_runs_pipeline_created` on `prompt_eval_runs` (16 kB)
- `silver_aa_internal.idx_generated_content_metadata_gin` on `generated_content` (1.5 MB)
- `tripplanner.narration_cache_created_at_idx` on `narration_cache` (16 kB)

## Soft-key orphans (DM-4.2)

Cross-app keys that have no FK (data standards DM-2.3) and how many rows point at nothing in the target, as of the Verified line (counts lag between structural changes, like `~rows`). `not_applicable` = the key columns or the target do not exist yet; `no_privilege` = the dump role cannot read one side. Orphan rate = orphans / rows with a key.

| key | status | rows | without key | orphans | orphan rate |
|---|---|---|---|---|---|
| booking.trip_case_legs.(source_system, source_id) -> catalog.v_tour | ok | 14 | 0 | 0 | 0.00% |

## Personal and confidential data tags (DM-6.1)

Column comments that start with `pii:<class>` (personal data) or `conf:<class>` (`commercial`, `credential`), data standards DM-6.1; `also` = further tags named later in the same comment. Owners tag a column in the migration that creates it. Input of the RoPA (AA-Ecosys `docs/legal/register.md` section (a), `tools/data/gen_pii_inventory.py`) and the erasure runbook (DM-6.7).

**119 tagged column(s)**, 13 untagged candidate(s) in booking, crm, tripplanner, 0 finding(s).

| schema | tag | columns | named as also |
|---|---|---|---|
| `booking` | `conf:commercial` | 30 | 0 |
| `booking` | `conf:credential` | 2 | 0 |
| `booking` | `pii:address` | 2 | 0 |
| `booking` | `pii:contact` | 9 | 2 |
| `booking` | `pii:free_text` | 13 | 2 |
| `booking` | `pii:name` | 4 | 6 |
| `booking` | `pii:online_id` | 3 | 0 |
| `booking` | `pii:profile` | 6 | 0 |
| `booking` | `pii:travel` | 7 | 0 |
| `crm` | `conf:credential` | 2 | 0 |
| `crm` | `pii:contact` | 6 | 0 |
| `crm` | `pii:emergency_contact` | 1 | 0 |
| `crm` | `pii:free_text` | 3 | 0 |
| `crm` | `pii:government_id` | 5 | 0 |
| `crm` | `pii:health` | 1 | 0 |
| `crm` | `pii:name` | 5 | 0 |
| `crm` | `pii:profile` | 1 | 0 |
| `crm` | `pii:travel` | 1 | 0 |
| `shared` | `conf:credential` | 1 | 0 |
| `shared` | `pii:contact` | 2 | 0 |
| `shared` | `pii:name` | 1 | 0 |
| `shared` | `pii:online_id` | 3 | 0 |
| `tripplanner` | `conf:credential` | 2 | 0 |
| `tripplanner` | `pii:contact` | 4 | 0 |
| `tripplanner` | `pii:free_text` | 1 | 3 |
| `tripplanner` | `pii:name` | 1 | 2 |
| `tripplanner` | `pii:travel` | 3 | 3 |

### Tagged columns

| schema | relation | column | tag | also |
|---|---|---|---|---|
| `booking` | `audit_logs` | `before` | `pii:free_text` | `pii:name`, `pii:contact` |
| `booking` | `audit_logs` | `after` | `pii:free_text` | `pii:name`, `pii:contact` |
| `booking` | `audit_logs` | `entity_label` | `pii:free_text` | `pii:name` |
| `booking` | `audit_logs` | `summary` | `pii:free_text` | `pii:name` |
| `booking` | `b2b_partners` | `agency_name` | `conf:commercial` |  |
| `booking` | `b2b_partners` | `credit_terms_ref` | `conf:commercial` |  |
| `booking` | `b2b_quote_lines` | `net_cost_usd` | `conf:commercial` |  |
| `booking` | `b2b_quote_lines` | `supplier_rate_ids` | `conf:commercial` |  |
| `booking` | `b2b_quotes` | `margin_applied` | `conf:commercial` |  |
| `booking` | `b2b_quotes` | `card_fee_pct` | `conf:commercial` |  |
| `booking` | `cancellation_policies` | `title` | `conf:commercial` |  |
| `booking` | `cancellation_policies` | `note` | `conf:commercial` |  |
| `booking` | `customer_otps` | `otp_hash` | `conf:credential` |  |
| `booking` | `customer_sessions` | `refresh_token_hash` | `conf:credential` |  |
| `booking` | `customers` | `name` | `pii:name` |  |
| `booking` | `customers` | `email` | `pii:contact` |  |
| `booking` | `customers` | `phone` | `pii:contact` |  |
| `booking` | `customers` | `address` | `pii:address` |  |
| `booking` | `customers` | `gender` | `pii:profile` |  |
| `booking` | `customers` | `marital_status` | `pii:profile` |  |
| `booking` | `customers` | `profession` | `pii:profile` |  |
| `booking` | `customers` | `profile_media_id` | `pii:profile` |  |
| `booking` | `hotel_room_types` | `internal_notes` | `conf:commercial` |  |
| `booking` | `hotels` | `internal_notes` | `conf:commercial` |  |
| `booking` | `inbox_events` | `payload` | `pii:contact` | `pii:name`, `pii:free_text` |
| `booking` | `inbox_events` | `error` | `pii:free_text` |  |
| `booking` | `media_files` | `s3_key` | `pii:profile` |  |
| `booking` | `notifications` | `title` | `pii:free_text` |  |
| `booking` | `notifications` | `message` | `pii:free_text` | `pii:name` |
| `booking` | `notifications` | `data` | `pii:contact` |  |
| `booking` | `policy_approvals` | `note` | `conf:commercial` |  |
| `booking` | `pricing_rules` | `target_margin` | `conf:commercial` |  |
| `booking` | `pricing_rules` | `floor_margin` | `conf:commercial` |  |
| `booking` | `pricing_rules` | `peak_uplift_pts` | `conf:commercial` |  |
| `booking` | `pricing_rules` | `card_fee_pct` | `conf:commercial` |  |
| `booking` | `pricing_rules` | `note` | `conf:commercial` |  |
| `booking` | `services` | `internal_notes` | `conf:commercial` |  |
| `booking` | `staff_users` | `cis_user_id` | `pii:online_id` |  |
| `booking` | `staff_users` | `email` | `pii:contact` |  |
| `booking` | `staff_users` | `name` | `pii:name` |  |
| `booking` | `staff_users` | `cognito_iss` | `pii:online_id` |  |
| `booking` | `staff_users` | `cognito_sub` | `pii:online_id` |  |
| `booking` | `supplier_contracts` | `payment_terms` | `conf:commercial` |  |
| `booking` | `supplier_contracts` | `cancellation_policy` | `conf:commercial` |  |
| `booking` | `supplier_contracts` | `notes` | `conf:commercial` |  |
| `booking` | `supplier_rates` | `net_amount` | `conf:commercial` |  |
| `booking` | `supplier_rates` | `notes` | `conf:commercial` |  |
| `booking` | `suppliers` | `internal_notes` | `conf:commercial` |  |
| `booking` | `suppliers` | `contact_name` | `pii:name` |  |
| `booking` | `suppliers` | `contact_title` | `pii:profile` |  |
| `booking` | `suppliers` | `contact_email` | `pii:contact` |  |
| `booking` | `suppliers` | `contact_phone` | `pii:contact` |  |
| `booking` | `trip_case_status_history` | `note` | `pii:free_text` |  |
| `booking` | `trip_case_version_itinerary` | `notes` | `pii:free_text` |  |
| `booking` | `trip_case_versions` | `notes` | `pii:free_text` |  |
| `booking` | `trip_case_versions` | `title` | `pii:free_text` |  |
| `booking` | `trip_case_versions` | `approval_note` | `pii:free_text` |  |
| `booking` | `trip_cases` | `trip_style` | `pii:travel` |  |
| `booking` | `trip_cases` | `start_date` | `pii:travel` |  |
| `booking` | `trip_cases` | `end_date` | `pii:travel` |  |
| `booking` | `trip_cases` | `pax` | `pii:travel` |  |
| `booking` | `trip_cases` | `inquiry_snapshot` | `pii:travel` | `pii:free_text` |
| `booking` | `trip_cases` | `notes` | `pii:free_text` |  |
| `booking` | `trip_cases` | `pax_adults` | `pii:travel` |  |
| `booking` | `trip_cases` | `pax_children` | `pii:travel` |  |
| `booking` | `trip_plans` | `default_channel` | `conf:commercial` |  |
| `booking` | `trip_plans` | `price_hint_amount` | `conf:commercial` |  |
| `booking` | `trip_plans` | `price_hint_currency` | `conf:commercial` |  |
| `booking` | `trip_plans` | `price_hint_basis` | `conf:commercial` |  |
| `booking` | `trip_plans` | `commercial_notes` | `conf:commercial` |  |
| `booking` | `v_customer_summary` | `name` | `pii:name` |  |
| `booking` | `v_customer_summary` | `email` | `pii:contact` |  |
| `booking` | `v_customer_summary` | `phone` | `pii:contact` |  |
| `booking` | `v_customer_summary` | `address` | `pii:address` |  |
| `booking` | `version_item_costs` | `net_amount` | `conf:commercial` |  |
| `booking` | `version_item_costs` | `supplier_note` | `conf:commercial` |  |
| `crm` | `document` | `filename_enc` | `pii:free_text` |  |
| `crm` | `form_submission` | `payload_enc` | `pii:contact` |  |
| `crm` | `integration_credential` | `account_ref` | `pii:contact` |  |
| `crm` | `integration_credential` | `secret_enc` | `conf:credential` |  |
| `crm` | `note` | `body_enc` | `pii:free_text` |  |
| `crm` | `placeholder_map` | `map_enc` | `pii:free_text` |  |
| `crm` | `tenant_key` | `wrapped_dek` | `conf:credential` |  |
| `crm` | `traveler` | `given_name_enc` | `pii:name` |  |
| `crm` | `traveler` | `family_name_enc` | `pii:name` |  |
| `crm` | `traveler` | `display_name_enc` | `pii:name` |  |
| `crm` | `traveler` | `email_enc` | `pii:contact` |  |
| `crm` | `traveler` | `phone_enc` | `pii:contact` |  |
| `crm` | `traveler` | `email_bidx` | `pii:contact` |  |
| `crm` | `traveler` | `phone_bidx` | `pii:contact` |  |
| `crm` | `traveler` | `name_bidx` | `pii:name` |  |
| `crm` | `traveler` | `name_token_bidx` | `pii:name` |  |
| `crm` | `traveler` | `dob_enc` | `pii:government_id` |  |
| `crm` | `traveler` | `nationality_enc` | `pii:government_id` |  |
| `crm` | `traveler` | `passport_no_enc` | `pii:government_id` |  |
| `crm` | `traveler` | `passport_expiry_enc` | `pii:government_id` |  |
| `crm` | `traveler` | `passport_country_enc` | `pii:government_id` |  |
| `crm` | `traveler` | `emergency_contact_enc` | `pii:emergency_contact` |  |
| `crm` | `traveler` | `profile_token_enc` | `pii:profile` |  |
| `crm` | `traveler_health` | `health_flags_enc` | `pii:health` |  |
| `crm` | `trip` | `title` | `pii:travel` |  |
| `shared` | `admin_users` | `username` | `pii:online_id` |  |
| `shared` | `admin_users` | `password_hash` | `conf:credential` |  |
| `shared` | `admin_users` | `email` | `pii:contact` |  |
| `shared` | `admin_users` | `display_name` | `pii:name` |  |
| `shared` | `admin_users` | `cognito_iss` | `pii:online_id` |  |
| `shared` | `admin_users` | `cognito_sub` | `pii:online_id` |  |
| `shared` | `alert_recipient` | `email` | `pii:contact` |  |
| `tripplanner` | `customers` | `name` | `pii:name` |  |
| `tripplanner` | `customers` | `phone` | `pii:contact` |  |
| `tripplanner` | `customers` | `email` | `pii:contact` |  |
| `tripplanner` | `outbox` | `payload` | `pii:contact` | `pii:name`, `pii:free_text`, `pii:travel` |
| `tripplanner` | `sessions` | `guest_token` | `conf:credential` |  |
| `tripplanner` | `sessions` | `guest_token_hash` | `conf:credential` |  |
| `tripplanner` | `trip_drafts` | `itinerary` | `pii:travel` | `pii:free_text` |
| `tripplanner` | `trip_drafts` | `date_start` | `pii:travel` |  |
| `tripplanner` | `trip_drafts` | `date_end` | `pii:travel` |  |
| `tripplanner` | `trip_events` | `payload` | `pii:free_text` | `pii:travel` |
| `tripplanner` | `v_inquiry_outbox` | `payload` | `pii:contact` | `pii:name`, `pii:free_text`, `pii:travel` |

### Tag findings

- none

### Untagged candidates

Columns of `booking`, `crm`, `tripplanner` without a tag whose name contains one of the tokens `address`, `data`, `email`, `iss`, `itinerary`, `label`, `message`, `name`, `note`, `notes`, `payload`, `phone`, `snapshot`, `sub`, `summary`, `title` (whole snake_case tokens) and that are not on the allowlist (AA-CIS-Infra `db/gen_schema_reference.py` `PII_ALLOWLIST`). Tag them in an owner migration or allowlist them with a reason.

- `crm.dispatch_queue.message_ref`
- `crm.form_submission.payload_redacted_at`
- `crm.intake_form.label`
- `crm.job.payload`
- `crm.member.cognito_iss`
- `crm.member.cognito_sub`
- `crm.member_invitation.email_enc`
- `crm.member_invitation.email_bidx`
- `crm.member_invitation.cognito_iss`
- `crm.member_invitation.cognito_sub`
- `crm.note.note_id`
- `crm.status_transition.table_name`
- `crm.tenant.display_name`

| allowlisted column | reason |
|---|---|
| `booking.countries.name` | reference data: country name |
| `booking.hotel_room_types.name` | a room type name |
| `booking.hotels.name` | a hotel (business) name |
| `booking.hotels.address` | a hotel (business) address |
| `booking.job.payload` | job payloads carry ids only (DM-6.3; the intake enqueues {inbox_event_id}, staff_email the notification id) |
| `booking.services.title` | internal working title of a supplier service (bk-010), no customer data |
| `booking.supplier_contracts.title` | a contract title, no customer data |
| `booking.suppliers.company_name` | a supplier company name; the contact person is suppliers.contact_name |
| `booking.suppliers.address` | a supplier business address (AA-877 decision: a sole-trader guide's business address is covered by the supplier-contacts RoPA activity, not tagged) |
| `booking.trip_case_version_itinerary.title` | itinerary item title (tour, hotel or service name) |
| `tripplanner.narration_cache.itinerary_hash` | hash of a catalog itinerary (cache key), no identity |

## RLS catalogue guard (X2)

Rules in AA-CIS-Infra `db/rls_catalogue_rules.py` (byte copy of AA-CIS-App `tests/integration/rls_catalogue_rules.py`, which CIS CI runs on the replayed migrations). A violation is a finding that is not on the allowlist; each allowlist entry carries a one-line reason. Fix the object or allowlist it in the CIS file, then copy it here.

**1 unallowlisted violation(s)**, 87 allowlisted finding(s), 12 stale allowlist entry(ies).

| rule | meaning | violations | allowlisted |
|---|---|---|---|
| a | tenant_id table without RLS + an app.tenant_id policy | 1 | 24 |
| b | policy TO PUBLIC | 0 | 8 |
| c | policy reads app.current_tenant | 0 | 0 |
| d | current_setting('app.tenant_id') outside NULLIF | 0 | 0 |
| e | foreign key across owners | 0 | 0 |
| p | grant to PUBLIC | 0 | 1 |
| g | grant to another owner's role | 0 | 53 |
| t | unconditional (true) policy | 0 | 1 |

### Violations

- [a] `booking.b2b_partners`: RLS off

### Allowlist entries in use

| rule | entry | findings | reason |
|---|---|---|---|
| a | `acp_contract.route_pick` | 1 | tenant route picks written by the T-pipeline jobs; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.acp_output_rules` | 1 | RLS on with the X1 cis_app parity policy only (CIS 244); no tenant-pool grant |
| a | `acp_shared.acp_quota_ledger` | 1 | tenant quota ledger; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.audit_log` | 1 | tenant action audit log; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.debate_brand_fit_cache` | 1 | pipeline cache keyed by tenant; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.tenant_atom_state` | 1 | per-tenant atom state, pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.tenant_config` | 1 | tenant settings, admin + pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.acp_runs` | 1 | legacy ACP v1 run table (pre-AA-751); platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.decision_log` | 1 | Jev decision audit; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.dfs_call_log` | 1 | DataForSEO cost log; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.jev_tenant_allowlist` | 1 | Jev rollout switch per tenant (admin-managed); platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.llm_call_daily` | 1 | cost log roll-up; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.llm_call_log` | 1 | cost log of every app; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_api_usage` | 1 | API metering written by the middleware; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_api_usage_monthly` | 1 | API metering roll-up; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_brand_rule_versions` | 1 | history of tenant brand rules; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_brand_rules_deleted_aa404` | 1 | AA-404 backup copy of deleted brand rules; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_export_config` | 1 | tenant export settings, admin + pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_rewrite_usage` | 1 | rewrite quota counter; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
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
| g | `booking.v_ops_case_status:cis_app` | 1 | contract: CIS ops dashboard (bk-017) |
| g | `booking.v_ops_funnel_daily:cis_app` | 1 | contract: CIS ops dashboard (bk-017) |
| g | `booking:cis_app` | 1 | contract: schema USAGE for the CIS ops views (bk-017) |
| g | `catalog.*:booking` | 16 | contract: catalog.* views for Booking (CIS 225, 228) |
| g | `catalog.*:tripplanner` | 18 | contract: catalog.* views for TripPlanner (CIS 225, 228) |
| g | `catalog:booking` | 1 | contract: catalog schema USAGE for Booking (CIS 225, 228) |
| g | `catalog:tripplanner` | 1 | contract: catalog schema USAGE for TripPlanner (CIS 225, 228) |
| g | `shared.llm_call_log:tripplanner` | 1 | contract: standing INSERT exception for TripPlanner cost logging (CIS 173) |
| g | `shared.llm_model_catalog:tripplanner` | 1 | CIS 173; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `shared.llm_role_config:tripplanner` | 1 | CIS 173; grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `shared.schema_versions:bk_owner` | 1 | contract: bk- keys only, key guard (CIS 243) |
| g | `shared.schema_versions:crm_owner` | 1 | contract: crm- keys only, key guard (CIS 269) |
| g | `shared.schema_versions:tp_owner` | 1 | contract: tp- keys only, key guard (CIS 243) |
| g | `shared:bk_owner` | 1 | contract: Booking owner role registers bk- keys (CIS 243) |
| g | `shared:crm_owner` | 1 | contract: partner CRM owner role registers crm- keys (CIS 269) |
| g | `shared:tp_owner` | 1 | contract: TripPlanner owner role registers tp- keys (CIS 243) |
| g | `shared:tripplanner` | 1 | schema USAGE for the Model Gateway tables below (CIS 173); grandfathered TripPlanner read (owners.yaml consumer_grants), removed by X4 |
| g | `tripplanner.v_inquiry_outbox:booking` | 1 | contract: Booking inquiry intake (tp-009) |
| g | `tripplanner.v_ops_traffic_daily:cis_app` | 1 | contract: CIS ops dashboard (tp-015) |
| g | `tripplanner:booking` | 1 | contract: schema USAGE for the inquiry outbox (tp-009) |
| g | `tripplanner:cis_app` | 1 | contract: schema USAGE for the CIS ops view (tp-015) |
| p | `public` | 1 | PostgreSQL default USAGE on the public schema (extensions); no app object lives there |
| t | `acp_contract.tour_atoms:catalog_owner_read` | 1 | catalog_owner views read every atom as before (CIS 266); D9 = 0 guarded |

Stale entries (matched nothing on this database; remove them from the CIS file): [e] `tripplanner.*->shared.destinations`, [g] `acp_contract.tour_atoms.*:tripplanner`, [g] `acp_contract.v_active_tour_atoms.*:tripplanner`, [g] `acp_contract:tripplanner`, [g] `gold_aa_internal.published_tours:tripplanner`, [g] `gold_aa_internal:tripplanner`, [g] `shared.destinations:tripplanner`, [g] `shared.v_destination_photos:tripplanner`, [g] `shared.v_tour_photos:tripplanner`, [g] `silver_aa_internal.raw_tours.country:tripplanner`, [g] `silver_aa_internal.raw_tours.tour_id:tripplanner`, [g] `silver_aa_internal:tripplanner`.

## Connections at dump time

Client sessions per `application_name` (`(empty)` = a pool without `application_name`, standards C1.1a).

| application_name | role | state | sessions |
|---|---|---|---|
| aa-tripplanner-dev-browse | tripplanner | idle | 2 |
| booking-api | booking | idle | 1 |
| cis-api | cis_app | idle | 1 |
| cis-worker | cis_app | idle | 1 |
| crm-api | crm_app | idle | 1 |
| db-isolation-probe | cis_app | active | 1 |
| db-isolation-probe | db_migrator | idle | 1 |

## Latest migrations

| version | applied_at | description |
|---|---|---|
| crm-011 | 2026-10-24 10:32:24.305342+00:00 | AA-941: L1 console (insights opt-out, AA-raised data requests) |
| crm-010 | 2026-10-24 08:35:46.600908+00:00 | AA-942: data lifecycle (agency offboarding states, trash days, archive columns, legal_hold, trip_commitment, dispatch_queue, erasure_request, lifecycle_run, erase_subject, lifecycle_purge_expired) |
| crm-009 | 2026-10-24 06:56:54.321270+00:00 | AA-938: F3 scrubber: crm.placeholder_map (scrub DEK, 24 h, purge policy), value-free llm_call receipt |
| crm-008 | 2026-10-24 06:49:42.396963+00:00 | AA-939: F4 roles (membership write guard, last owner, invitations, owner recovery, entitlements, refund threshold) |
| crm-007 | 2026-10-24 06:39:39.304637+00:00 | AA-940: audit_event monthly partitions (crm-003 table attached as the first), partition maker + verified drop, audit_export_tenant registry, audit_export_manifest hash chain |
| crm-006 | 2026-10-24 05:24:13.544067+00:00 | AA-937: F1/F2 complete: relations (+inverse), health codes, documents, full F2 profile + history, age band list, list_view ids, F2 views + reader grants |
| crm-005 | 2026-10-24 03:39:17.916619+00:00 | AA-936: intake forms + submissions, consent, F2 profile, trip + stage history, party links, task, note, llm_call + usage rollup |
| crm-004 | 2026-10-24 02:21:28.296870+00:00 | AA-935: agency display name + default locale, caller-scoped membership lookup policies |
| crm-003 | 2026-10-23 18:10:19.861587+00:00 | AA-934: crm vault (tenant_key DEK store, integration_credential, traveler vault columns, append-only audit_event) |
| bk-022 | 2026-10-23 17:42:33.217758+00:00 | AA-975 (CRM-B3): shared outbox (+ feed_seq sequence, event triggers on holds, hold lines, cancellations, departures, incidents), departure_incidents, hold-line on-request desk columns, b2b_answer_due(), settings b2b_on_request_answer_business_days, b2b_ops_timezone |
| 274 | 2026-10-23 13:42:43.623090+00:00 | AA-986 L3/L4: shared.notifications under RLS (tenant reads its own tenant-facing rows); catalog.v_tour_retired + catalog.v_tour_lifecycle_outbox (contract catalog.tour.v1.3) |
| 273 | 2026-10-23 11:33:49.681667+00:00 | AA-645 d06: published_tours.updated_at (a rewrite keeps published_at, records updated_at); catalog._live_tour.master_updated_at, v_tour.updated_at follows it; same v_tour columns and rows |
| 272 | 2026-10-23 11:26:22.910760+00:00 | AA-986 L2: tour lifecycle record, Master status reason, v_tour_liveness |
| 271 | 2026-10-23 09:53:47.851498+00:00 | AA-986 L1: v_active_tour_atoms requires a live source version (the catalog._live_tour rule) |
| bk-021 | 2026-10-23 06:09:34.643635+00:00 | AA-974 (CRM-B2b): cancellation_policies (+ approvals, seed default B2B policy), b2b_cancellations, b2b_holds extend columns + cancellation_policy_id + re-hold index, settings b2b_hold_extend_hours, b2b_rehold_limit_per_day |
| tp-018 | 2026-10-23 05:26:50.574824+00:00 | AA-712 X4: drop the frozen place tables (itinerary_components, tour_day, tour_stop, tour_graph_*, tour_leg, tour_junction) |
| 270 | 2026-10-23 04:45:12.440314+00:00 | AA-712 X4: tripplanner keeps only the catalog views and the Model Gateway grants of CIS |
| crm-002 | 2026-10-23 03:10:52.562403+00:00 | AA-933: crm tenancy base (tenant, member, status transitions, base table template, readiness view) |
| crm-001 | 2026-10-23 03:07:15.770984+00:00 | AA-932: crm schema privileges (crm_app DML defaults, no PUBLIC EXECUTE) + crm.job (ADR 0003a template, kinds crm_*) |
| 269 | 2026-10-23 02:52:22.790021+00:00 | AA-932: crm_owner USAGE on shared + SELECT, INSERT on shared.schema_versions; key guard: crm_owner registers crm- keys only |
