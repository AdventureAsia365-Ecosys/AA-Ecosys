# AA-Ecosys DB Schema Reference (live dump)

<!-- schema-fingerprint: 633249db8e106c706624480272407ae639dbe7f94d35d35560149363e56d2eb7 -->

**Verified:** 2026-10-29 20:51 UTC — live catalog dump of the shared RDS (`aa-cis-dev-db`, `aa-cis/dev/rds`, acc2, us-west-1, PostgreSQL 15.17). Latest migration per owner: CIS **305**, TripPlanner **tp-021**, Booking **bk-035**, CRM **crm-023** (361 versions registered).

> **Generated file — do not edit by hand** (data standards DM-3.1). It is the single source of truth for table/column names, owners, grants and RLS across CIS, TripPlanner and Booking (one RDS, one schema per owner; ownership rules: `docs/database/schema-ownership.md`). Read it before introspecting columns. AA-CIS-Infra `.github/workflows/db-schema-dump.yml` regenerates it after every DB Migrate apply and every night (`db/schema_dump.py` in a one-off ECS task, then `db/gen_schema_reference.py`) and opens a PR here when the structure changed.
> Source: AA-CIS-Infra DB Schema Dump (after DB Migrate apply of booking/035_ops_inquiry_inbox_view.sql (run 40952342685)), https://github.com/AdventureAsia365-Ecosys/AA-CIS-Infra/actions/runs/40952555118

**ERD:** [one Mermaid diagram per schema](erd/README.md) (keys and foreign keys), generated from the same dump by AA-CIS-Infra `db/gen_erd.py` (AA-894).

**Totals:** 13 schemas (1 empty: retired), 333 tables/views, 923 indexes, 450 FKs, 166 RLS policy(ies), 134 functions, 13 enums. Database size 1.5 GB, max_connections 181. RLS catalogue guard: 2 unallowlisted violation(s) (see *RLS catalogue guard (X2)*). DM-6.1 tags: 204 tagged column(s), 38 untagged candidate(s).

## Conventions
- Column format: `name type` — `NN` suffix = NOT NULL. Types are `format_type()` output (`character varying(64)`, `text[]`, `vector(1024)`, enums schema-qualified). A ` · pii:<class>` / ` · conf:<class>` suffix is the column's data standards DM-6.1 tag (its comment starts with it), `(also …)` = further tags named in the same comment; see *Personal and confidential data tags (DM-6.1)*.
- `~N rows` = `pg_class.reltuples` estimate, sizes = `pg_total_relation_size`, both as of the Verified line (a PR is opened only when the structure changes, so these lag between structural changes). Run exact counts before any drop decision.
- Under each object: owner and RLS state (`RLS on` = ENABLE, `+ FORCE` = FORCE ROW LEVEL SECURITY; the owner is exempt unless FORCE), indexes, CHECK constraints, grants to roles other than the owner (`*` = WITH GRANT OPTION), column-level grants, RLS policies and triggers. Usage counters are in *Table activity* at the end.
- `raw_tours` PK is `tour_id` (NOT `id`). `quality_scores` has `evaluated_at` (NOT `created_at`). `published_tours`/`seo_context` have NO `country` — always JOIN `raw_tours`.

## Schemas

| schema | owner | objects | size | grants (USAGE / CREATE) |
|---|---|---|---|---|
| `acp_contract` | cis_owner | 15 | 310.5 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE |
| `acp_deliver` | cis_owner | 1 | 40 kB | aa_app_user: USAGE; cis_app: USAGE |
| `acp_shared` | cis_owner | 19 | 28.1 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE |
| `booking` | bk_owner | 75 | 8.4 MB | booking: USAGE; cis_app: USAGE |
| `catalog` | cis_owner | 25 |  | aa_app_user: USAGE; booking: USAGE; catalog_owner: USAGE; tripplanner: USAGE |
| `crm` | crm_owner | 85 | 20.4 MB | crm_ai_reader: USAGE; crm_app: USAGE; crm_eraser: USAGE; crm_insights: USAGE; crm_support_reader: USAGE |
| `geo` | cis_owner | 18 | 369.6 MB | catalog_owner: USAGE; cis_app: USAGE |
| `gold_aa_internal` | cis_owner | 9 | 7.8 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE |
| `public` | pg_database_owner | 1 | 24 kB | PUBLIC: USAGE |
| `retired` | cis_owner | 0 |  |  |
| `shared` | cis_owner | 63 | 746 MB | aa_app_user: USAGE; bk_owner: USAGE; catalog_owner: USAGE; cis_app: USAGE; crm_owner: USAGE; tp_owner: USAGE; tripplanner: USAGE |
| `silver_aa_internal` | cis_owner | 7 | 29.3 MB | aa_app_user: USAGE; catalog_owner: USAGE; cis_app: USAGE |
| `tripplanner` | tp_owner | 15 | 1 MB | booking: USAGE; cis_app: USAGE; tripplanner: USAGE |

## `acp_contract` (15 objects)

### `acp_contract.atom_embedding` (table, ~10674 rows, 175.2 MB)
```
atom_id text NN
view text NN
embedding vector(1536) NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `atom_embedding_pkey` PRIMARY KEY: UNIQUE btree (atom_id, view)
- index `idx_atom_embedding_vector`: ivfflat (embedding vector_cosine_ops) WITH (lists='10')
- check `atom_embedding_view_check`: `CHECK ((view = ANY (ARRAY['place'::text, 'place_action'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_matches` (table, ~15152 rows, 4.4 MB)
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
- check `atom_matches_kind_check`: `CHECK ((kind = 'question'::text))`
- check `atom_matches_matched_by_check`: `CHECK ((matched_by = ANY (ARRAY['vector'::text, 'tokens'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_ranking` (table, ~97368 rows, 66.6 MB)
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
- check `atom_ranking_excluded_reason_check`: `CHECK ((excluded_reason = ANY (ARRAY['transit'::text, 'unnamed_place'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_segment` (table, ~11613 rows, 3.9 MB)
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

### `acp_contract.atom_segment_alias` (table, ~1012 rows, 352 kB)
```
segment_id_old text NN
segment_id_canonical text NN
merged_at timestamp with time zone NN
```
- owner `cis_owner`
- index `atom_segment_alias_pkey` PRIMARY KEY: UNIQUE btree (segment_id_old)
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.atom_segment_member` (table, ~17510 rows, 7.8 MB)
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

### `acp_contract.atomize_day_fingerprint` (table, ~16159 rows, 2.9 MB)
```
tenant_tour_version_id uuid NN
day_number integer NN
fingerprint_hash text NN
atomized_at timestamp with time zone NN
```
- owner `cis_owner`
- index `atomize_day_fingerprint_pkey` PRIMARY KEY: UNIQUE btree (tenant_tour_version_id, day_number)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.hub` (table, ~87 rows, 152 kB)
```
hub_id uuid NN
hub_name text NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `hub_pkey` PRIMARY KEY: UNIQUE btree (hub_id)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.question_embedding` (table, ~1006 rows, 8.4 MB)
```
question_hash text NN
question_text text NN
embedding vector(1536) NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `question_embedding_pkey` PRIMARY KEY: UNIQUE btree (question_hash)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_contract.route` (table, ~11546 rows, 6.8 MB)
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

### `acp_contract.tour_atoms` (table, ~54494 rows, 31.8 MB)
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
- check `tour_atoms_visual_potential_check`: `CHECK (((visual_potential >= 1) AND (visual_potential <= 3)))`
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

## `acp_shared` (19 objects)

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
- check `acp_output_rules_rule_type_check`: `CHECK (((rule_type)::text = ANY (ARRAY[('block'::character varying)::text, ('replace'::character varying)::text, ('truncate'::character varying)::text, ('flag'::character varying)::text, ('score_gate'::character varying)::text])))`
- check `acp_output_rules_source_type_check`: `CHECK (((source_type)::text = ANY (ARRAY[('system'::character varying)::text, ('hitl_rejection'::character varying)::text, ('manual'::character varying)::text])))`
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
- check `angle_gate_option_idx_check`: `CHECK (((idx >= 0) AND (idx <= 2)))`
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
- check `angle_gate_request_status_check`: `CHECK ((status = ANY (ARRAY['pending_goal'::text, 'pending_choice'::text, 'approved'::text, 'reusable'::text])))`
- grant `aa_app_user`: INSERT, SELECT, UPDATE
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `angle_gate_request_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `acp_shared.atom_place_card` (table, ~26154 rows, 3.8 MB)
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

### `acp_shared.audit_log` (table, ~3100 rows, 2.2 MB)
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
- check `audit_log_http_method_chk`: `CHECK (((http_method IS NULL) OR (http_method = ANY (ARRAY['POST'::text, 'PUT'::text, 'PATCH'::text, 'DELETE'::text]))))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `audit_log_chain`: BEFORE INSERT ON acp_shared.audit_log FOR EACH ROW EXECUTE FUNCTION acp_shared.audit_log_chain()
- trigger `audit_log_no_delete`: BEFORE DELETE ON acp_shared.audit_log FOR EACH ROW EXECUTE FUNCTION acp_shared.audit_log_append_only()
- trigger `audit_log_no_truncate`: BEFORE TRUNCATE ON acp_shared.audit_log FOR EACH STATEMENT EXECUTE FUNCTION acp_shared.audit_log_append_only()
- trigger `audit_log_no_update`: BEFORE UPDATE ON acp_shared.audit_log FOR EACH ROW EXECUTE FUNCTION acp_shared.audit_log_append_only()

### `acp_shared.content_piece` (table, ~343 rows, 11.9 MB)
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
- check `content_piece_status_check`: `CHECK ((status = ANY (ARRAY['processing'::text, 'approved'::text, 'held'::text, 'failed'::text])))`
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
- check `content_piece_label_defects_check`: `CHECK ((jsonb_typeof(defects) = 'object'::text))`
- check `content_piece_label_label_check`: `CHECK ((label = ANY (ARRAY['as_is'::text, 'light'::text, 'heavy'::text, 'reject'::text])))`
- check `content_piece_label_labelled_by_check`: `CHECK ((length(btrim(labelled_by)) > 0))`
- check `content_piece_label_minutes_to_fix_check`: `CHECK (((minutes_to_fix IS NULL) OR ((minutes_to_fix >= 0) AND (minutes_to_fix <= 600))))`
- check `content_piece_label_reason_check`: `CHECK (((reason IS NULL) OR (length(reason) <= 4000)))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `acp_shared.debate_brand_fit_cache` (table, ~357 rows, 504 kB)
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
- check `debate_brand_fit_cache_check`: `CHECK (((segment_id IS NOT NULL) <> (route_id IS NOT NULL)))`
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
kind text NN
valid_until date
updated_by text
```
- owner `cis_owner` · RLS on
- index `facts_pkey` PRIMARY KEY: UNIQUE btree (fact_id)
- index `idx_facts_scope`: btree (scope)
- index `idx_facts_tenant`: btree (tenant_id) WHERE (scope = 'tenant'::text)
- check `facts_kind_check`: `CHECK ((kind = ANY (ARRAY['price'::text, 'season'::text, 'visa_entry'::text, 'transfer_time'::text, 'booking_terms'::text, 'other'::text])))`
- check `facts_scope_check`: `CHECK ((scope = ANY (ARRAY['platform'::text, 'tenant'::text])))`
- check `facts_scope_tenant_ck`: `CHECK ((((scope = 'platform'::text) AND (tenant_id IS NULL)) OR ((scope = 'tenant'::text) AND (tenant_id IS NOT NULL))))`
- check `facts_valid_until_ck`: `CHECK (((valid_until IS NULL) OR (stated_on IS NULL) OR (valid_until >= stated_on)))`
- grant `aa_app_user`: DELETE, INSERT, SELECT, UPDATE
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `facts_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `facts_platform_read` (PERMISSIVE SELECT TO aa_app_user): USING `(scope = 'platform'::text)`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))` WITH CHECK `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))`

### `acp_shared.place_card` (table, ~4785 rows, 4.5 MB)
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
- check `place_card_status_check`: `CHECK ((status = ANY (ARRAY['auto_checked'::text, 'verified'::text, 'rejected'::text])))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: SELECT (card_id, status)

### `acp_shared.place_card_alias` (table, ~18503 rows, 3.2 MB)
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

### `acp_shared.place_card_miss` (table, ~1331 rows, 528 kB)
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
- check `place_card_miss_reason_check`: `CHECK ((reason = ANY (ARRAY['no_name'::text, 'identity_rejected'::text, 'error'::text])))`
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
- check `publish_log_status_check`: `CHECK ((status = ANY (ARRAY['requested'::text, 'published'::text, 'unpublished'::text, 'failed'::text])))`
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
- check `quarter_plan_quarter_check`: `CHECK (((quarter >= 1) AND (quarter <= 4)))`
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
- check `quarter_plan_version_approval_status_check`: `CHECK (((approval_status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[])))`
- check `quarter_plan_version_source_check`: `CHECK (((source)::text = ANY ((ARRAY['standard'::character varying, 'override'::character varying])::text[])))`
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

### `acp_shared.subject` (table, ~435 rows, 624 kB)
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
- check `subject_check`: `CHECK ((((segment_id IS NOT NULL) AND (route_id IS NULL)) OR ((segment_id IS NULL) AND (route_id IS NOT NULL))))`
- check `subject_state_check`: `CHECK ((state = ANY (ARRAY['proposed'::text, 'picked'::text, 'used'::text, 'cut'::text])))`
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- column grant `aa_app_user`: UPDATE (state)
- policy `subject_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `acp_shared.tenant_config` (table, 32 kB)
```
tenant_id uuid NN
markets text[] NN
channels text[] NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `tenant_config_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- check `tenant_config_channels_not_empty`: `CHECK ((array_length(channels, 1) > 0))`
- check `tenant_config_channels_valid`: `CHECK ((channels <@ ARRAY['blog'::text, 'linkedin'::text, 'facebook'::text, 'instagram'::text, 'tiktok'::text, 'email'::text, 'landing_page'::text, 'ads'::text]))`
- check `tenant_config_markets_not_empty`: `CHECK ((array_length(markets, 1) > 0))`
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

## `booking` (75 objects)

### `booking.audit_logs` (table, ~167 rows, 280 kB)
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
- check `audit_logs_actor_type_chk`: `CHECK ((actor_type = ANY (ARRAY['staff'::text, 'customer'::text, 'system'::text])))`
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
- check `b2b_cancellations_amounts_chk`: `CHECK (((total_b2b_price >= (0)::numeric) AND (fee_amount >= (0)::numeric) AND (refundable_amount >= (0)::numeric) AND ((fee_amount + refundable_amount) = total_b2b_price)))`
- check `b2b_cancellations_client_chk`: `CHECK ((m2m_client_id ~ '^[A-Za-z0-9]{1,128}$'::text))`
- check `b2b_cancellations_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `b2b_cancellations_fee_pct_chk`: `CHECK (((fee_pct >= (0)::numeric) AND (fee_pct <= (100)::numeric)))`
- check `b2b_cancellations_key_chk`: `CHECK (((length(idempotency_key) >= 8) AND (length(idempotency_key) <= 200)))`
- check `b2b_cancellations_reason_chk`: `CHECK ((reason_code = ANY (ARRAY['client_cancelled'::text, 'agency_cancelled'::text, 'departure_cancelled'::text, 'other'::text])))`
- grant `booking`: INSERT, SELECT
- trigger `b2b_cancellations_outbox`: AFTER INSERT ON booking.b2b_cancellations FOR EACH ROW EXECUTE FUNCTION booking.b2b_cancellations_outbox()

### `booking.b2b_hold_lines` (table, ~12 rows, 80 kB)
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
- check `b2b_hold_lines_answer_chk`: `CHECK ((((answered_by IS NULL) OR (answered_at IS NOT NULL)) AND ((answered_at IS NULL) OR (status = ANY (ARRAY['confirmed'::text, 'declined'::text, 'cancelled'::text])))))`
- check `b2b_hold_lines_decline_chk`: `CHECK ((((status = 'declined'::text) = (decline_code IS NOT NULL)) AND ((decline_code IS NULL) OR (decline_code = ANY (ARRAY['sold_out'::text, 'supplier_unavailable'::text, 'minimum_not_met'::text, 'other'::text])))))`
- check `b2b_hold_lines_held_as_chk`: `CHECK ((held_as = ANY (ARRAY['available'::text, 'on_request'::text])))`
- check `b2b_hold_lines_no_chk`: `CHECK (((line_no >= 1) AND (line_no <= 200)))`
- check `b2b_hold_lines_ref_chk`: `CHECK (((length(line_ref) >= 1) AND (length(line_ref) <= 64)))`
- check `b2b_hold_lines_seats_chk`: `CHECK (((seats >= 0) AND (seats <= 120)))`
- check `b2b_hold_lines_status_chk`: `CHECK ((status = ANY (ARRAY['available'::text, 'on_request'::text, 'confirmed'::text, 'declined'::text, 'cancelled'::text])))`
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
- check `b2b_holds_client_chk`: `CHECK ((m2m_client_id ~ '^[A-Za-z0-9]{1,128}$'::text))`
- check `b2b_holds_confirmed_chk`: `CHECK (((status = 'confirmed'::text) = ((confirmed_at IS NOT NULL) AND (trip_case_id IS NOT NULL))))`
- check `b2b_holds_deposit_chk`: `CHECK (((deposit_ref IS NULL) OR ((length(deposit_ref) >= 1) AND (length(deposit_ref) <= 64))))`
- check `b2b_holds_expired_chk`: `CHECK (((status = 'expired'::text) = (expired_at IS NOT NULL)))`
- check `b2b_holds_expiry_chk`: `CHECK ((expires_at > created_at))`
- check `b2b_holds_extend_chk`: `CHECK ((((extended_count = 0) = (extended_at IS NULL)) AND ((extended_at IS NULL) = (extend_reason IS NULL)) AND ((extended_at IS NULL) = (extend_idempotency_key IS NULL)) AND ((extend_reason IS NULL) OR (extend_reason = ANY (ARRAY['payment_claimed'::text, 'client_recheck'::text]))) AND ((extend_idempotency_key IS NULL) OR ((length(extend_idempotency_key) >= 8) AND (length(extend_idempotency_key) <= 200)))))`
- check `b2b_holds_extended_chk`: `CHECK (((extended_count >= 0) AND (extended_count <= 1)))`
- check `b2b_holds_key_chk`: `CHECK (((length(idempotency_key) >= 8) AND (length(idempotency_key) <= 200)))`
- check `b2b_holds_proposal_chk`: `CHECK ((((length(proposal_ref) >= 1) AND (length(proposal_ref) <= 64)) AND (proposal_version >= 1)))`
- check `b2b_holds_released_chk`: `CHECK (((status = 'released'::text) = (released_at IS NOT NULL)))`
- check `b2b_holds_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'confirmed'::text, 'expired'::text, 'released'::text])))`
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
- check `b2b_partners_client_chk`: `CHECK ((m2m_client_id ~ '^[A-Za-z0-9]{1,128}$'::text))`
- check `b2b_partners_currency_chk`: `CHECK ((billing_currency ~ '^[A-Z]{3}$'::text))`
- check `b2b_partners_name_chk`: `CHECK (((length(btrim(agency_name)) >= 1) AND (length(btrim(agency_name)) <= 200)))`
- check `b2b_partners_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'suspended'::text])))`
- check `b2b_partners_terms_chk`: `CHECK (((credit_terms_ref IS NULL) OR ((length(btrim(credit_terms_ref)) >= 1) AND (length(btrim(credit_terms_ref)) <= 120))))`
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `b2b_partners_set_updated_at`: BEFORE UPDATE ON booking.b2b_partners FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.b2b_quote_lines` (table, 80 kB)
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
- check `b2b_quote_lines_availability_chk`: `CHECK ((availability = ANY (ARRAY['available'::text, 'on_request'::text, 'sold_out'::text])))`
- check `b2b_quote_lines_component_chk`: `CHECK (((length(component_id) >= 1) AND (length(component_id) <= 64)))`
- check `b2b_quote_lines_kind_chk`: `CHECK ((component_kind = ANY (ARRAY['trip_plan'::text, 'hotel_room'::text, 'transfer'::text, 'guide'::text, 'activity'::text, 'entrance'::text, 'meal'::text])))`
- check `b2b_quote_lines_nights_chk`: `CHECK (((nights IS NULL) OR ((nights >= 1) AND (nights <= 60))))`
- check `b2b_quote_lines_no_chk`: `CHECK (((line_no >= 1) AND (line_no <= 200)))`
- check `b2b_quote_lines_pax_chk`: `CHECK ((((pax_adult >= 1) AND (pax_adult <= 60)) AND ((pax_child >= 0) AND (pax_child <= 60)) AND ((pax_infant >= 0) AND (pax_infant <= 20))))`
- check `b2b_quote_lines_price_chk`: `CHECK (((b2b_price >= (0)::numeric) AND (net_cost_usd >= (0)::numeric)))`
- check `b2b_quote_lines_ref_chk`: `CHECK (((length(line_ref) >= 1) AND (length(line_ref) <= 64)))`
- check `b2b_quote_lines_rooms_chk`: `CHECK (((jsonb_typeof(rooms) = 'array'::text) AND (jsonb_array_length(rooms) <= 30)))`
- check `b2b_quote_lines_unit_chk`: `CHECK ((unit = ANY (ARRAY['per_person'::text, 'per_group'::text, 'per_room_night'::text, 'per_line'::text])))`
- grant `booking`: INSERT, SELECT

### `booking.b2b_quotes` (table, 96 kB)
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
- check `b2b_quotes_client_chk`: `CHECK ((m2m_client_id ~ '^[A-Za-z0-9]{1,128}$'::text))`
- check `b2b_quotes_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `b2b_quotes_fx_chk`: `CHECK (((fx_rate_per_usd > (0)::numeric) AND (fx_buffer_pct >= (0)::numeric) AND (fx_buffer_pct < (1)::numeric) AND ((length(fx_source) >= 1) AND (length(fx_source) <= 64))))`
- check `b2b_quotes_hash_chk`: `CHECK ((price_hash ~ '^[a-f0-9]{64}$'::text))`
- check `b2b_quotes_margin_chk`: `CHECK (((margin_applied >= (0)::numeric) AND (margin_applied < (1)::numeric) AND (card_fee_pct >= (0)::numeric) AND (card_fee_pct < (1)::numeric)))`
- check `b2b_quotes_proposal_chk`: `CHECK ((((length(proposal_ref) >= 1) AND (length(proposal_ref) <= 64)) AND (proposal_version >= 1)))`
- check `b2b_quotes_rounding_chk`: `CHECK (((length(rounding) >= 1) AND (length(rounding) <= 64)))`
- check `b2b_quotes_total_chk`: `CHECK ((total_b2b_price >= (0)::numeric))`
- check `b2b_quotes_valid_chk`: `CHECK ((valid_until > created_at))`
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
- check `cancellation_policies_channel_chk`: `CHECK ((channel = 'b2b'::text))`
- check `cancellation_policies_note_chk`: `CHECK (((note IS NULL) OR (length(note) <= 500)))`
- check `cancellation_policies_tiers_chk`: `CHECK (((jsonb_typeof(tiers) = 'array'::text) AND ((jsonb_array_length(tiers) >= 1) AND (jsonb_array_length(tiers) <= 20)) AND jsonb_path_exists(tiers, '$[*]?(@."min_days" == 0)'::jsonpath) AND (NOT jsonb_path_exists(tiers, '$[*]?(!(((((((exists (@."min_days") && @."min_days".type() == "number") && @."min_days" >= 0) && @."min_days" <= 730) && exists (@."fee_pct")) && @."fee_pct".type() == "number") && @."fee_pct" >= 0) && @."fee_pct" <= 100))'::jsonpath))))`
- check `cancellation_policies_title_chk`: `CHECK (((length(btrim(title)) >= 1) AND (length(btrim(title)) <= 120)))`
- grant `booking`: INSERT, SELECT

### `booking.countries` (table, 32 kB)
```
iso2 character(2) NN
name text NN
active boolean NN
```
- owner `bk_owner`
- index `countries_pkey` PRIMARY KEY: UNIQUE btree (iso2)
- check `countries_iso2_chk`: `CHECK ((iso2 ~ '^[A-Z]{2}$'::text))`
- grant `booking`: SELECT

### `booking.country_profiles` (table, 24 kB)
```
country_code character(2) NN
id uuid NN
status text NN
area text
internal_notes text · conf:commercial
status_reason text · conf:commercial
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `country_profiles_id_uq`: UNIQUE btree (id)
- index `country_profiles_pkey` PRIMARY KEY: UNIQUE btree (country_code)
- check `country_profiles_area_chk`: `CHECK (((area IS NULL) OR ((length(btrim(area)) >= 1) AND (length(btrim(area)) <= 60))))`
- check `country_profiles_notes_chk`: `CHECK (((internal_notes IS NULL) OR (length(internal_notes) <= 5000)))`
- check `country_profiles_reason_chk`: `CHECK (((status_reason IS NULL) OR (length(status_reason) <= 500)))`
- check `country_profiles_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (area, internal_notes, status, status_reason, updated_at, updated_by)
- trigger `country_profiles_set_updated_at`: BEFORE UPDATE ON booking.country_profiles FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.customer_identities` (table, 24 kB)
```
iss text NN · pii:online_id
sub text NN · pii:online_id
customer_id uuid NN
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `customer_identities_customer_idx`: btree (customer_id)
- index `customer_identities_pkey` PRIMARY KEY: UNIQUE btree (iss, sub)
- check `customer_identities_shape_chk`: `CHECK (((iss ~~ 'https://%'::text) AND (length(iss) <= 300) AND ((length(sub) >= 1) AND (length(sub) <= 128))))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (customer_id)

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
- check `customer_otps_attempts_chk`: `CHECK ((attempts >= 0))`
- check `customer_otps_channel_chk`: `CHECK ((channel = ANY (ARRAY['email'::text, 'sms'::text])))`
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
- check `customers_contact_chk`: `CHECK (((email IS NOT NULL) OR (phone IS NOT NULL)))`
- check `customers_source_chk`: `CHECK ((source = ANY (ARRAY['manual'::text, 'otp'::text, 'tripplanner_lead'::text, 'traveller_signin'::text])))`
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
- check `departure_incidents_cleared_chk`: `CHECK ((((cleared_at IS NULL) = (cleared_by IS NULL)) AND ((cleared_at IS NULL) OR (cleared_at >= flagged_at))))`
- check `departure_incidents_code_chk`: `CHECK ((incident_code = ANY (ARRAY['weather'::text, 'road'::text, 'health'::text, 'political'::text, 'supplier'::text, 'other'::text])))`
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
- check `departures_capacity_chk`: `CHECK (((capacity >= 0) AND (capacity <= 1000)))`
- check `departures_status_chk`: `CHECK ((status = ANY (ARRAY['scheduled'::text, 'guaranteed'::text, 'cancelled'::text])))`
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `departures_outbox`: AFTER UPDATE OF status ON booking.departures FOR EACH ROW EXECUTE FUNCTION booking.departures_outbox()
- trigger `departures_set_updated_at`: BEFORE UPDATE ON booking.departures FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.destination_profiles` (table, 16 kB)
```
destination_id uuid NN
status text NN
internal_notes text · conf:commercial
status_reason text · conf:commercial
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `destination_profiles_pkey` PRIMARY KEY: UNIQUE btree (destination_id)
- check `destination_profiles_notes_chk`: `CHECK (((internal_notes IS NULL) OR (length(internal_notes) <= 5000)))`
- check `destination_profiles_reason_chk`: `CHECK (((status_reason IS NULL) OR (length(status_reason) <= 500)))`
- check `destination_profiles_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (internal_notes, status, status_reason, updated_at, updated_by)
- trigger `destination_profiles_set_updated_at`: BEFORE UPDATE ON booking.destination_profiles FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.entity_media` (table, 64 kB)
```
id uuid NN
entity_type text NN
entity_id uuid NN
s3_bucket text NN
s3_key text NN
content_type text NN
bytes integer NN
width integer
height integer
sha256 text NN
usage_rights boolean NN
status text NN
uploaded_by text NN
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `entity_media_entity_idx`: btree (entity_type, entity_id, created_at)
- index `entity_media_entity_sha_uq`: UNIQUE btree (entity_type, entity_id, sha256) WHERE (status = 'active'::text)
- index `entity_media_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `entity_media_bucket_chk`: `CHECK ((s3_bucket ~ '^aa-booking-[a-z0-9]+-supply-media-[0-9]{12}$'::text))`
- check `entity_media_bytes_chk`: `CHECK (((bytes >= 1) AND (bytes <= 10485760)))`
- check `entity_media_content_type_chk`: `CHECK ((content_type = ANY (ARRAY['image/jpeg'::text, 'image/png'::text, 'image/webp'::text])))`
- check `entity_media_entity_type_chk`: `CHECK ((entity_type = ANY (ARRAY['hotel'::text, 'service'::text])))`
- check `entity_media_key_chk`: `CHECK ((s3_key = ((((((('supply-media/'::text || entity_type) || '/'::text) || (entity_id)::text) || '/'::text) || (id)::text) || '.'::text) ||
CASE content_type
    WHEN 'image/jpeg'::text THEN 'jpg'::text
    WHEN 'image/png'::text THEN 'png'::text
    ELSE 'webp'::text
END)))`
- check `entity_media_sha256_chk`: `CHECK ((sha256 ~ '^[0-9a-f]{64}$'::text))`
- check `entity_media_size_chk`: `CHECK ((((width IS NULL) OR ((width >= 1) AND (width <= 20000))) AND ((height IS NULL) OR ((height >= 1) AND (height <= 20000)))))`
- check `entity_media_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'removed'::text])))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (status, updated_at, updated_by, usage_rights)
- trigger `entity_media_guard`: BEFORE UPDATE ON booking.entity_media FOR EACH ROW EXECUTE FUNCTION booking.entity_media_guard()
- trigger `entity_media_set_updated_at`: BEFORE UPDATE ON booking.entity_media FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()
- trigger `entity_media_supply_bump`: AFTER INSERT OR UPDATE ON booking.entity_media FOR EACH ROW EXECUTE FUNCTION booking.entity_media_supply_bump()

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
- check `fx_rates_buffer_chk`: `CHECK (((buffer_pct >= (0)::numeric) AND (buffer_pct < (1)::numeric)))`
- check `fx_rates_currency_chk`: `CHECK (((currency ~ '^[A-Z]{3}$'::text) AND (currency <> 'USD'::bpchar)))`
- check `fx_rates_rate_chk`: `CHECK ((rate_per_usd > (0)::numeric))`
- check `fx_rates_source_chk`: `CHECK ((length(btrim(source)) > 0))`
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
- check `hotel_room_types_beds_chk`: `CHECK ((cardinality(bed_types) <= 10))`
- check `hotel_room_types_name_chk`: `CHECK (((length(btrim(name)) >= 1) AND (length(btrim(name)) <= 120)))`
- check `hotel_room_types_occupancy_chk`: `CHECK (((max_occupancy IS NULL) OR ((max_occupancy >= 1) AND (max_occupancy <= 20))))`
- check `hotel_room_types_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))`
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `hotel_room_types_set_updated_at`: BEFORE UPDATE ON booking.hotel_room_types FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()
- trigger `hotel_room_types_supply_bump`: AFTER INSERT OR UPDATE ON booking.hotel_room_types FOR EACH ROW EXECUTE FUNCTION booking.hotel_room_types_supply_bump()

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
supply_version bigint NN
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
- check `hotels_amenities_chk`: `CHECK ((cardinality(amenities) <= 50))`
- check `hotels_geo_chk`: `CHECK ((((latitude IS NULL) = (longitude IS NULL)) AND ((latitude IS NULL) OR ((latitude >= ('-90'::integer)::numeric) AND (latitude <= (90)::numeric))) AND ((longitude IS NULL) OR ((longitude >= ('-180'::integer)::numeric) AND (longitude <= (180)::numeric)))))`
- check `hotels_links_chk`: `CHECK (((jsonb_typeof(links) = 'array'::text) AND (jsonb_array_length(links) <= 10)))`
- check `hotels_name_chk`: `CHECK (((length(btrim(name)) >= 1) AND (length(btrim(name)) <= 200)))`
- check `hotels_star_chk`: `CHECK (((star_rating IS NULL) OR ((star_rating >= 1) AND (star_rating <= 5))))`
- check `hotels_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))`
- check `hotels_style_chk`: `CHECK (((hotel_style IS NULL) OR ((length(hotel_style) >= 1) AND (length(hotel_style) <= 60))))`
- check `hotels_supply_version_chk`: `CHECK ((supply_version >= 1))`
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `hotels_set_updated_at`: BEFORE UPDATE ON booking.hotels FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()
- trigger `hotels_supply_outbox`: AFTER INSERT OR UPDATE ON booking.hotels FOR EACH ROW EXECUTE FUNCTION booking.supply_outbox()
- trigger `hotels_supply_version`: BEFORE INSERT OR UPDATE ON booking.hotels FOR EACH ROW EXECUTE FUNCTION booking.hotels_supply_version()

### `booking.inbox_cursor` (table, ~2 rows, 64 kB)
```
source text NN
contract text NN
safe_id bigint NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `inbox_cursor_pk` PRIMARY KEY: UNIQUE btree (source, contract)
- check `inbox_cursor_safe_id_chk`: `CHECK ((safe_id >= 0))`
- check `inbox_cursor_source_chk`: `CHECK ((source = ANY (ARRAY['tripplanner'::text, 'cis'::text])))`
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `inbox_cursor_set_updated_at`: BEFORE UPDATE ON booking.inbox_cursor FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.inbox_events` (table, ~5 rows, 144 kB)
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
- check `inbox_events_source_chk`: `CHECK ((source = ANY (ARRAY['tripplanner'::text, 'cis'::text])))`
- check `inbox_events_status_chk`: `CHECK ((status = ANY (ARRAY['received'::text, 'processed'::text, 'parked'::text, 'failed'::text])))`
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.invoice_items` (table, 88 kB)
```
id uuid NN
invoice_id uuid NN
position smallint NN
kind text NN
description text NN · pii:free_text
quantity numeric(10,2) NN
unit_price numeric(16,2) NN
amount numeric(16,2) NN
reason text · pii:free_text
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `invoice_items_created_by_idx`: btree (created_by) WHERE (created_by IS NOT NULL)
- index `invoice_items_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `invoice_items_position_uq`: UNIQUE btree (invoice_id, "position")
- index `invoice_items_updated_by_idx`: btree (updated_by) WHERE (updated_by IS NOT NULL)
- index `invoice_items_version_total_uq`: UNIQUE btree (invoice_id) WHERE (kind = 'version_total'::text)
- check `invoice_items_amount_chk`: `CHECK ((amount = round((quantity * unit_price), 2)))`
- check `invoice_items_description_chk`: `CHECK (((length(description) >= 1) AND (length(description) <= 500)))`
- check `invoice_items_kind_chk`: `CHECK ((kind = ANY (ARRAY['version_total'::text, 'adjustment'::text])))`
- check `invoice_items_position_chk`: `CHECK ((("position" >= 1) AND ("position" <= 200)))`
- check `invoice_items_quantity_chk`: `CHECK (((quantity > (0)::numeric) AND (quantity <= (9999)::numeric)))`
- check `invoice_items_reason_chk`: `CHECK ((((kind = 'adjustment'::text) = (reason IS NOT NULL)) AND ((reason IS NULL) OR ((length(reason) >= 1) AND (length(reason) <= 500)))))`
- check `invoice_items_version_total_chk`: `CHECK (((kind <> 'version_total'::text) OR ((quantity = (1)::numeric) AND (unit_price >= (0)::numeric))))`
- grant `booking`: DELETE, INSERT, SELECT
- column grant `booking`: UPDATE (amount, description, position, quantity, reason, unit_price, updated_at, updated_by)
- trigger `invoice_items_guard`: BEFORE INSERT OR DELETE OR UPDATE ON booking.invoice_items FOR EACH ROW EXECUTE FUNCTION booking.invoice_items_guard()
- trigger `invoice_items_set_updated_at`: BEFORE UPDATE ON booking.invoice_items FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()
- trigger `invoice_items_settle`: AFTER INSERT OR DELETE OR UPDATE ON booking.invoice_items FOR EACH ROW EXECUTE FUNCTION booking.invoice_items_settle()

### `booking.invoices` (table, 184 kB)
```
id uuid NN
invoice_number text NN
trip_case_id uuid NN
version_id uuid NN
bill_to_kind text NN
customer_id uuid
bill_to_name text · pii:name
bill_to_email text · pii:contact
bill_to_address text · pii:address
document_type text NN
currency character(3) NN
total_amount numeric(16,2) NN
status text NN
amending boolean NN
issued_at timestamp with time zone
sent_by text
notes text · pii:free_text
terms text · pii:free_text
cancelled_at timestamp with time zone
cancelled_by text
cancel_reason text · pii:free_text
idempotency_key text NN
request_sha256 text NN
deleted_at timestamp with time zone
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `invoices_cancelled_by_idx`: btree (cancelled_by) WHERE (cancelled_by IS NOT NULL)
- index `invoices_created_by_idx`: btree (created_by) WHERE (created_by IS NOT NULL)
- index `invoices_customer_idx`: btree (customer_id) WHERE (customer_id IS NOT NULL)
- index `invoices_idempotency_uq`: UNIQUE btree (trip_case_id, idempotency_key)
- index `invoices_live_per_case_uq`: UNIQUE btree (trip_case_id) WHERE ((status <> 'cancelled'::text) AND (deleted_at IS NULL))
- index `invoices_number_uq`: UNIQUE btree (invoice_number)
- index `invoices_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `invoices_sent_by_idx`: btree (sent_by) WHERE (sent_by IS NOT NULL)
- index `invoices_status_idx`: btree (status, issued_at DESC) WHERE (deleted_at IS NULL)
- index `invoices_updated_by_idx`: btree (updated_by) WHERE (updated_by IS NOT NULL)
- index `invoices_version_idx`: btree (version_id)
- check `invoices_amending_chk`: `CHECK (((NOT amending) OR (status = ANY (ARRAY['sent'::text, 'partially_paid'::text, 'paid'::text]))))`
- check `invoices_bill_to_chk`: `CHECK ((((bill_to_name IS NULL) OR ((length(bill_to_name) >= 1) AND (length(bill_to_name) <= 200))) AND ((bill_to_email IS NULL) OR ((length(bill_to_email) >= 3) AND (length(bill_to_email) <= 320))) AND ((bill_to_address IS NULL) OR ((length(bill_to_address) >= 1) AND (length(bill_to_address) <= 500)))))`
- check `invoices_bill_to_kind_chk`: `CHECK ((bill_to_kind = 'customer'::text))`
- check `invoices_cancel_chk`: `CHECK ((((status = 'cancelled'::text) = ((cancelled_at IS NOT NULL) AND (cancel_reason IS NOT NULL))) AND ((cancel_reason IS NULL) OR ((length(cancel_reason) >= 1) AND (length(cancel_reason) <= 500)))))`
- check `invoices_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `invoices_customer_chk`: `CHECK (((bill_to_kind <> 'customer'::text) OR (customer_id IS NOT NULL)))`
- check `invoices_deleted_chk`: `CHECK (((deleted_at IS NULL) OR (status = 'draft'::text)))`
- check `invoices_document_type_chk`: `CHECK ((document_type = 'proforma'::text))`
- check `invoices_idempotency_chk`: `CHECK ((((length(idempotency_key) >= 8) AND (length(idempotency_key) <= 200)) AND (request_sha256 ~ '^[0-9a-f]{64}$'::text)))`
- check `invoices_number_chk`: `CHECK ((invoice_number ~ '^INV-[0-9]{6,}$'::text))`
- check `invoices_sent_chk`: `CHECK ((((status = 'draft'::text) = (issued_at IS NULL)) AND ((status = 'draft'::text) OR ((bill_to_name IS NOT NULL) AND (sent_by IS NOT NULL)))))`
- check `invoices_status_chk`: `CHECK ((status = ANY (ARRAY['draft'::text, 'sent'::text, 'partially_paid'::text, 'paid'::text, 'cancelled'::text])))`
- check `invoices_text_chk`: `CHECK ((((notes IS NULL) OR ((length(notes) >= 1) AND (length(notes) <= 2000))) AND ((terms IS NULL) OR ((length(terms) >= 1) AND (length(terms) <= 2000)))))`
- check `invoices_total_chk`: `CHECK (((total_amount >= (0)::numeric) AND ((status = ANY (ARRAY['draft'::text, 'cancelled'::text])) OR (total_amount > (0)::numeric))))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (amending, bill_to_address, bill_to_email, bill_to_name, cancel_reason, cancelled_at, cancelled_by, deleted_at, issued_at, notes, sent_by, status, terms, total_amount, updated_at, updated_by)
- trigger `invoices_check_transition`: BEFORE UPDATE OF status ON booking.invoices FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.ops_check_transition('invoice')
- trigger `invoices_guard`: BEFORE INSERT OR UPDATE ON booking.invoices FOR EACH ROW EXECUTE FUNCTION booking.invoices_guard()
- trigger `invoices_set_updated_at`: BEFORE UPDATE ON booking.invoices FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.job` (table, ~6914 rows, 3.5 MB)
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
- check `job_attempts_chk`: `CHECK (((attempt >= 0) AND (max_attempts >= 1)))`
- check `job_kind_chk`: `CHECK ((kind ~ '^bk_[a-z0-9_]+$'::text))`
- check `job_lease_chk`: `CHECK (((status <> 'running'::text) OR ((locked_by IS NOT NULL) AND (locked_until IS NOT NULL))))`
- check `job_status_chk`: `CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text, 'cancelled'::text])))`
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
- check `media_files_bytes_chk`: `CHECK (((bytes IS NULL) OR (bytes >= 0)))`
- check `media_files_dims_chk`: `CHECK ((((width IS NULL) OR (width > 0)) AND ((height IS NULL) OR (height > 0))))`
- check `media_files_sha256_chk`: `CHECK (((sha256 IS NULL) OR (sha256 ~ '^[0-9a-f]{64}$'::text)))`
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

### `booking.notifications` (table, ~22 rows, 112 kB)
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
- index `notifications_reminder_uq`: UNIQUE btree (recipient_type, type, entity_id, ((data ->> 'reminder_key'::text))) WHERE (data ? 'reminder_key'::text)
- index `notifications_staff_feed_idx`: btree (recipient_ref, created_at DESC) WHERE (recipient_type = 'staff'::text)
- index `notifications_unread_idx`: btree (recipient_type, recipient_id, created_at DESC) WHERE (read_at IS NULL)
- check `notifications_customer_recipient_chk`: `CHECK (((recipient_type <> 'customer'::text) OR (recipient_id IS NOT NULL)))`
- check `notifications_recipient_type_chk`: `CHECK ((recipient_type = ANY (ARRAY['customer'::text, 'staff'::text])))`
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.ops_files` (table, 128 kB)
```
id uuid NN
kind text NN
entity_type text NN
entity_id uuid NN
trip_case_id uuid
s3_bucket text NN
s3_key text NN · pii:payment (also pii:name)
content_type text NN
bytes integer NN
sha256 text NN
file_name text NN · pii:free_text
status text NN
removed_reason text · pii:free_text
removed_at timestamp with time zone
uploaded_by text
removed_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `ops_files_entity_idx`: btree (entity_type, entity_id, created_at)
- index `ops_files_entity_sha_uq`: UNIQUE btree (entity_type, entity_id, sha256) WHERE (status = 'active'::text)
- index `ops_files_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `ops_files_removed_by_idx`: btree (removed_by) WHERE (removed_by IS NOT NULL)
- index `ops_files_removed_idx`: btree (removed_at) WHERE (status = 'removed'::text)
- index `ops_files_trip_case_idx`: btree (trip_case_id) WHERE (trip_case_id IS NOT NULL)
- index `ops_files_uploaded_by_idx`: btree (uploaded_by) WHERE (uploaded_by IS NOT NULL)
- check `ops_files_bucket_chk`: `CHECK ((s3_bucket ~ '^aa-booking-[a-z0-9]+-ops-docs-[0-9]{12}$'::text))`
- check `ops_files_bytes_chk`: `CHECK (((bytes >= 1) AND (bytes <= 10485760)))`
- check `ops_files_content_type_chk`: `CHECK ((content_type = ANY (ARRAY['application/pdf'::text, 'image/jpeg'::text, 'image/png'::text, 'image/webp'::text])))`
- check `ops_files_entity_type_chk`: `CHECK ((entity_type = ANY (ARRAY['payment'::text, 'supplier_booking'::text, 'supplier_bill'::text, 'supplier_payout'::text])))`
- check `ops_files_key_chk`: `CHECK ((s3_key = ((((('ops-docs/'::text || kind) || '/'::text) || (id)::text) || '.'::text) ||
CASE content_type
    WHEN 'application/pdf'::text THEN 'pdf'::text
    WHEN 'image/jpeg'::text THEN 'jpg'::text
    WHEN 'image/png'::text THEN 'png'::text
    ELSE 'webp'::text
END)))`
- check `ops_files_kind_chk`: `CHECK ((kind = ANY (ARRAY['payment_evidence'::text, 'supplier_voucher'::text, 'supplier_confirmation'::text, 'supplier_bill'::text, 'payout_evidence'::text])))`
- check `ops_files_kind_entity_chk`: `CHECK ((((kind = 'payment_evidence'::text) AND (entity_type = 'payment'::text)) OR ((kind = ANY (ARRAY['supplier_voucher'::text, 'supplier_confirmation'::text])) AND (entity_type = 'supplier_booking'::text)) OR ((kind = 'supplier_bill'::text) AND (entity_type = 'supplier_bill'::text)) OR ((kind = 'payout_evidence'::text) AND (entity_type = 'supplier_payout'::text))))`
- check `ops_files_name_chk`: `CHECK (((length(file_name) >= 1) AND (length(file_name) <= 200)))`
- check `ops_files_removed_chk`: `CHECK ((((status = 'removed'::text) = ((removed_at IS NOT NULL) AND (removed_reason IS NOT NULL))) AND ((removed_reason IS NULL) OR ((length(removed_reason) >= 1) AND (length(removed_reason) <= 500)))))`
- check `ops_files_sha256_chk`: `CHECK ((sha256 ~ '^[0-9a-f]{64}$'::text))`
- check `ops_files_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'removed'::text])))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (removed_at, removed_by, removed_reason, status, updated_at)
- trigger `ops_files_guard`: BEFORE INSERT OR UPDATE ON booking.ops_files FOR EACH ROW EXECUTE FUNCTION booking.ops_files_guard()
- trigger `ops_files_set_updated_at`: BEFORE UPDATE ON booking.ops_files FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.ops_transitions` (table, 32 kB)
```
entity text NN
from_status text NN
to_status text NN
```
- owner `bk_owner`
- index `ops_transitions_pk` PRIMARY KEY: UNIQUE btree (entity, from_status, to_status)
- check `ops_transitions_distinct_chk`: `CHECK ((from_status <> to_status))`
- check `ops_transitions_entity_chk`: `CHECK ((entity = ANY (ARRAY['supplier_booking'::text, 'invoice'::text, 'supplier_bill'::text])))`
- grant `booking`: SELECT

### `booking.outbox` (table, ~1 rows, 112 kB)
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
entity_type text
entity_id uuid
supply_version bigint
```
- owner `bk_owner`
- index `outbox_event_id_uq`: UNIQUE btree (event_id)
- index `outbox_feed_seq_uq`: UNIQUE btree (feed_seq)
- index `outbox_partner_feed_idx`: btree (partner_id, feed_seq) WHERE (feed_seq IS NOT NULL)
- index `outbox_pending_idx`: btree (id) WHERE (feed_seq IS NULL)
- index `outbox_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `outbox_supply_feed_idx`: btree (feed_seq) WHERE (stream = 'supply'::text)
- check `outbox_b2b_partner_chk`: `CHECK (((stream <> 'b2b'::text) OR (partner_id IS NOT NULL)))`
- check `outbox_booking_chk`: `CHECK (((event_type <> 'booking.cancelled'::text) OR (booking_id IS NOT NULL)))`
- check `outbox_decline_chk`: `CHECK ((((event_type = 'line.declined'::text) = (decline_code IS NOT NULL)) AND ((decline_code IS NULL) OR (decline_code = ANY (ARRAY['sold_out'::text, 'supplier_unavailable'::text, 'minimum_not_met'::text, 'other'::text])))))`
- check `outbox_departure_chk`: `CHECK (((event_type !~~ 'departure.%'::text) OR (departure_id IS NOT NULL)))`
- check `outbox_event_type_chk`: `CHECK ((event_type = ANY (ARRAY['hold.expired'::text, 'hold.extended'::text, 'line.confirmed'::text, 'line.declined'::text, 'booking.cancelled'::text, 'departure.guaranteed'::text, 'departure.cancelled'::text, 'departure.incident'::text, 'departure.incident_cleared'::text, 'supply.upsert'::text, 'supply.deactivate'::text])))`
- check `outbox_hold_chk`: `CHECK (((event_type = ANY (ARRAY['hold.expired'::text, 'hold.extended'::text, 'line.confirmed'::text, 'line.declined'::text, 'booking.cancelled'::text])) = (hold_id IS NOT NULL)))`
- check `outbox_incident_chk`: `CHECK ((((event_type = ANY (ARRAY['departure.incident'::text, 'departure.incident_cleared'::text])) = (incident_code IS NOT NULL)) AND ((incident_code IS NULL) OR (incident_code = ANY (ARRAY['weather'::text, 'road'::text, 'health'::text, 'political'::text, 'supplier'::text, 'other'::text])))))`
- check `outbox_line_chk`: `CHECK ((((event_type = ANY (ARRAY['line.confirmed'::text, 'line.declined'::text])) = (line_ref IS NOT NULL)) AND ((line_ref IS NULL) OR ((length(line_ref) >= 1) AND (length(line_ref) <= 64)))))`
- check `outbox_sequenced_chk`: `CHECK (((feed_seq IS NULL) = (sequenced_at IS NULL)))`
- check `outbox_stream_chk`: `CHECK ((stream = ANY (ARRAY['b2b'::text, 'supply'::text])))`
- check `outbox_supply_chk`: `CHECK ((((stream = 'supply'::text) AND (event_type = ANY (ARRAY['supply.upsert'::text, 'supply.deactivate'::text])) AND COALESCE(((entity_type = ANY (ARRAY['hotel'::text, 'service'::text])) AND (supply_version >= 1)), false) AND (entity_id IS NOT NULL) AND (num_nonnulls(partner_id, hold_id, booking_id, line_ref, departure_id, incident_code, decline_code) = 0)) OR ((stream <> 'supply'::text) AND (event_type <> ALL (ARRAY['supply.upsert'::text, 'supply.deactivate'::text])) AND (entity_type IS NULL) AND (entity_id IS NULL) AND (supply_version IS NULL))))`
- grant `booking`: SELECT
- column grant `booking`: INSERT (booking_id, decline_code, departure_id, entity_id, entity_type, event_type, hold_id, incident_code, line_ref, partner_id, stream, supply_version)
- column grant `booking`: UPDATE (feed_seq, sequenced_at)

### `booking.payment_schedule` (table, 88 kB)
```
id uuid NN
invoice_id uuid NN
seq smallint NN
kind text NN
amount numeric(16,2) NN
due_date date NN
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `payment_schedule_created_by_idx`: btree (created_by) WHERE (created_by IS NOT NULL)
- index `payment_schedule_due_idx`: btree (due_date)
- index `payment_schedule_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `payment_schedule_seq_uq`: UNIQUE btree (invoice_id, seq)
- index `payment_schedule_updated_by_idx`: btree (updated_by) WHERE (updated_by IS NOT NULL)
- check `payment_schedule_amount_chk`: `CHECK ((amount > (0)::numeric))`
- check `payment_schedule_kind_chk`: `CHECK ((kind = ANY (ARRAY['deposit'::text, 'second'::text, 'final'::text, 'other'::text])))`
- check `payment_schedule_seq_chk`: `CHECK (((seq >= 1) AND (seq <= 10)))`
- grant `booking`: DELETE, INSERT, SELECT
- column grant `booking`: UPDATE (amount, due_date, kind, seq, updated_at, updated_by)
- trigger `payment_schedule_guard`: BEFORE INSERT OR DELETE OR UPDATE ON booking.payment_schedule FOR EACH ROW EXECUTE FUNCTION booking.payment_schedule_guard()
- trigger `payment_schedule_set_updated_at`: BEFORE UPDATE ON booking.payment_schedule FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.payments` (table, 200 kB)
```
id uuid NN
ref text NN
invoice_id uuid NN
kind text NN
amount numeric(16,2) NN
currency character(3) NN
method text NN
received_on date NN
reference text · pii:payment
note text · pii:free_text
received_amount numeric(16,2)
received_currency character(3)
evidence_file_id uuid
idempotency_key text NN
request_sha256 text NN
recorded_by text NN
recorded_at timestamp with time zone NN
verified_by text
verified_at timestamp with time zone
voided_by text
voided_at timestamp with time zone
void_reason text · pii:free_text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `payments_awaiting_idx`: btree (recorded_at) WHERE ((verified_at IS NULL) AND (voided_at IS NULL))
- index `payments_evidence_idx`: btree (evidence_file_id) WHERE (evidence_file_id IS NOT NULL)
- index `payments_idempotency_uq`: UNIQUE btree (invoice_id, idempotency_key)
- index `payments_invoice_idx`: btree (invoice_id, recorded_at)
- index `payments_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `payments_received_on_idx`: btree (received_on)
- index `payments_recorded_by_idx`: btree (recorded_by)
- index `payments_ref_uq`: UNIQUE btree (ref)
- index `payments_reference_idx`: btree (method, reference) WHERE ((voided_at IS NULL) AND (reference IS NOT NULL))
- index `payments_updated_by_idx`: btree (updated_by) WHERE (updated_by IS NOT NULL)
- index `payments_verified_by_idx`: btree (verified_by) WHERE (verified_by IS NOT NULL)
- index `payments_voided_by_idx`: btree (voided_by) WHERE (voided_by IS NOT NULL)
- check `payments_amount_chk`: `CHECK ((amount > (0)::numeric))`
- check `payments_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `payments_idempotency_chk`: `CHECK ((((length(idempotency_key) >= 8) AND (length(idempotency_key) <= 200)) AND (request_sha256 ~ '^[0-9a-f]{64}$'::text)))`
- check `payments_kind_chk`: `CHECK ((kind = ANY (ARRAY['receipt'::text, 'refund'::text])))`
- check `payments_maker_checker_chk`: `CHECK (((verified_by IS NULL) OR (verified_by <> recorded_by)))`
- check `payments_method_chk`: `CHECK ((method = ANY (ARRAY['bank_transfer'::text, 'card_offline'::text, 'cash'::text, 'other'::text])))`
- check `payments_received_chk`: `CHECK ((((received_amount IS NULL) = (received_currency IS NULL)) AND ((received_amount IS NULL) OR (received_amount > (0)::numeric)) AND ((received_currency IS NULL) OR (received_currency ~ '^[A-Z]{3}$'::text))))`
- check `payments_received_on_chk`: `CHECK ((received_on >= '2020-01-01'::date))`
- check `payments_ref_chk`: `CHECK ((ref ~ '^PMT-[0-9]{6,}$'::text))`
- check `payments_text_chk`: `CHECK ((((reference IS NULL) OR ((length(reference) >= 1) AND (length(reference) <= 100))) AND ((note IS NULL) OR ((length(note) >= 1) AND (length(note) <= 2000)))))`
- check `payments_verified_chk`: `CHECK (((verified_by IS NULL) = (verified_at IS NULL)))`
- check `payments_void_chk`: `CHECK ((((voided_at IS NULL) = (void_reason IS NULL)) AND ((voided_at IS NULL) = (voided_by IS NULL)) AND ((void_reason IS NULL) OR ((length(void_reason) >= 1) AND (length(void_reason) <= 500)))))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (evidence_file_id, note, reference, updated_at, updated_by, verified_at, verified_by, void_reason, voided_at, voided_by)
- trigger `payments_guard`: BEFORE INSERT OR UPDATE ON booking.payments FOR EACH ROW EXECUTE FUNCTION booking.payments_guard()
- trigger `payments_set_updated_at`: BEFORE UPDATE ON booking.payments FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()
- trigger `payments_settle`: AFTER INSERT OR UPDATE ON booking.payments FOR EACH ROW EXECUTE FUNCTION booking.payments_settle()

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
- check `policy_approvals_approved_by_chk`: `CHECK ((length(btrim(approved_by)) > 0))`
- check `policy_approvals_entity_chk`: `CHECK ((((entity_type = 'pricing_rule'::text) AND (pricing_rule_id IS NOT NULL) AND (fx_rate_id IS NULL) AND (cancellation_policy_id IS NULL)) OR ((entity_type = 'fx_rate'::text) AND (fx_rate_id IS NOT NULL) AND (pricing_rule_id IS NULL) AND (cancellation_policy_id IS NULL)) OR ((entity_type = 'cancellation_policy'::text) AND (cancellation_policy_id IS NOT NULL) AND (pricing_rule_id IS NULL) AND (fx_rate_id IS NULL))))`
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
- check `pricing_rules_channel_chk`: `CHECK ((channel = ANY (ARRAY['b2c_tailor_made'::text, 'fixed_departure'::text, 'b2b'::text])))`
- check `pricing_rules_divisor_chk`: `CHECK ((((target_margin + peak_uplift_pts) + card_fee_pct) < (1)::numeric))`
- check `pricing_rules_ratios_chk`: `CHECK (((target_margin >= (0)::numeric) AND (target_margin < (1)::numeric) AND (floor_margin >= (0)::numeric) AND (floor_margin <= target_margin) AND (peak_uplift_pts >= (0)::numeric) AND (peak_uplift_pts < (1)::numeric) AND (card_fee_pct >= (0)::numeric) AND (card_fee_pct < (1)::numeric)))`
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
supply_version bigint NN
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
- check `services_duration_chk`: `CHECK (((duration_minutes IS NULL) OR ((duration_minutes >= 1) AND (duration_minutes <= 43200))))`
- check `services_group_chk`: `CHECK (((max_group_size IS NULL) OR ((max_group_size >= 1) AND (max_group_size <= 999))))`
- check `services_inclusions_chk`: `CHECK ((cardinality(inclusions) <= 50))`
- check `services_source_chk`: `CHECK ((((source_system IS NULL) AND (source_id IS NULL)) OR ((source_system = 'cis'::text) AND (source_id IS NOT NULL) AND ((length(source_id) >= 1) AND (length(source_id) <= 120)))))`
- check `services_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))`
- check `services_supply_version_chk`: `CHECK ((supply_version >= 1))`
- check `services_title_chk`: `CHECK (((length(btrim(title)) >= 1) AND (length(btrim(title)) <= 200)))`
- check `services_type_chk`: `CHECK ((service_type = ANY (ARRAY['activity'::text, 'transfer'::text, 'guide'::text, 'entrance'::text, 'meal'::text])))`
- check `services_unit_chk`: `CHECK ((unit = ANY (ARRAY['person'::text, 'group'::text, 'vehicle'::text, 'day'::text])))`
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `services_set_updated_at`: BEFORE UPDATE ON booking.services FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()
- trigger `services_supply_outbox`: AFTER INSERT OR UPDATE ON booking.services FOR EACH ROW EXECUTE FUNCTION booking.supply_outbox()
- trigger `services_supply_version`: BEFORE INSERT OR UPDATE ON booking.services FOR EACH ROW EXECUTE FUNCTION booking.services_supply_version()

### `booking.settings` (table, 32 kB)
```
key text NN
value jsonb NN
description text
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `settings_pkey` PRIMARY KEY: UNIQUE btree (key)
- check `settings_key_chk`: `CHECK ((key ~ '^[a-z][a-z0-9_]{0,62}$'::text))`
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
- check `staff_assignments_period_chk`: `CHECK (((unassigned_at IS NULL) OR (unassigned_at >= assigned_at)))`
- check `staff_assignments_role_chk`: `CHECK ((role = ANY (ARRAY['sales'::text, 'contracting'::text, 'ops'::text, 'guide'::text])))`
- grant `booking`: DELETE, INSERT, SELECT, UPDATE

### `booking.staff_users` (table, ~8 rows, 64 kB)
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
- check `staff_users_cognito_key_chk`: `CHECK ((("left"(cis_user_id, 4) <> 'cog:'::text) OR ((cognito_sub IS NOT NULL) AND (cognito_sub = substr(cis_user_id, 5)))))`
- check `staff_users_cognito_pair_chk`: `CHECK ((((cognito_iss IS NULL) AND (cognito_sub IS NULL)) OR ((cognito_iss IS NOT NULL) AND (cognito_sub IS NOT NULL) AND (cognito_iss ~~ 'https://%'::text) AND ((length(cognito_sub) >= 1) AND (length(cognito_sub) <= 128)))))`
- check `staff_users_id_chk`: `CHECK (((length(cis_user_id) >= 1) AND (length(cis_user_id) <= 128)))`
- check `staff_users_role_chk`: `CHECK ((role = ANY (ARRAY['admin'::text, 'sales'::text, 'contracting'::text, 'content_creator'::text])))`
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `staff_users_set_updated_at`: BEFORE UPDATE ON booking.staff_users FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.supplier_bill_items` (table, 64 kB)
```
bill_id uuid NN
supplier_booking_id uuid NN
amount numeric(16,2) NN · conf:commercial
created_by text
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `supplier_bill_items_booking_idx`: btree (supplier_booking_id)
- index `supplier_bill_items_created_by_idx`: btree (created_by) WHERE (created_by IS NOT NULL)
- index `supplier_bill_items_pk` PRIMARY KEY: UNIQUE btree (bill_id, supplier_booking_id)
- check `supplier_bill_items_amount_chk`: `CHECK ((amount > (0)::numeric))`
- grant `booking`: DELETE, INSERT, SELECT
- trigger `supplier_bill_items_guard`: BEFORE INSERT OR DELETE OR UPDATE ON booking.supplier_bill_items FOR EACH ROW EXECUTE FUNCTION booking.supplier_bill_items_guard()

### `booking.supplier_bills` (table, 208 kB)
```
id uuid NN
code text NN
supplier_id uuid NN
trip_case_id uuid
bill_number text NN · conf:commercial
currency character(3) NN
amount numeric(16,2) NN · conf:commercial
issue_date date NN
due_date date NN
document_file_id uuid
status text NN
notes text · pii:free_text (also conf:commercial)
idempotency_key text NN
request_sha256 text NN
created_by text NN
facts_edited_by text NN
approved_by text
approved_at timestamp with time zone
paid_at timestamp with time zone
cancelled_by text
cancelled_at timestamp with time zone
cancel_reason text · pii:free_text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `supplier_bills_approved_by_idx`: btree (approved_by) WHERE (approved_by IS NOT NULL)
- index `supplier_bills_cancelled_by_idx`: btree (cancelled_by) WHERE (cancelled_by IS NOT NULL)
- index `supplier_bills_code_uq`: UNIQUE btree (code)
- index `supplier_bills_created_by_idx`: btree (created_by)
- index `supplier_bills_document_idx`: btree (document_file_id) WHERE (document_file_id IS NOT NULL)
- index `supplier_bills_facts_edited_by_idx`: btree (facts_edited_by)
- index `supplier_bills_idempotency_uq`: UNIQUE btree (idempotency_key)
- index `supplier_bills_number_uq`: UNIQUE btree (supplier_id, lower(bill_number)) WHERE (status <> 'cancelled'::text)
- index `supplier_bills_open_idx`: btree (due_date) WHERE (status = ANY (ARRAY['received'::text, 'approved'::text]))
- index `supplier_bills_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `supplier_bills_supplier_idx`: btree (supplier_id, due_date)
- index `supplier_bills_trip_case_idx`: btree (trip_case_id) WHERE (trip_case_id IS NOT NULL)
- index `supplier_bills_updated_by_idx`: btree (updated_by) WHERE (updated_by IS NOT NULL)
- check `supplier_bills_amount_chk`: `CHECK ((amount > (0)::numeric))`
- check `supplier_bills_approved_chk`: `CHECK ((((approved_by IS NULL) = (approved_at IS NULL)) AND ((status <> 'received'::text) OR (approved_at IS NULL)) AND ((status <> ALL (ARRAY['approved'::text, 'paid'::text])) OR (approved_at IS NOT NULL))))`
- check `supplier_bills_cancel_chk`: `CHECK ((((status = 'cancelled'::text) = ((cancelled_at IS NOT NULL) AND (cancel_reason IS NOT NULL) AND (cancelled_by IS NOT NULL))) AND ((cancel_reason IS NULL) OR ((length(cancel_reason) >= 1) AND (length(cancel_reason) <= 500)))))`
- check `supplier_bills_code_chk`: `CHECK ((code ~ '^BIL-[0-9]{6,}$'::text))`
- check `supplier_bills_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `supplier_bills_dates_chk`: `CHECK (((issue_date >= '2020-01-01'::date) AND (due_date >= issue_date)))`
- check `supplier_bills_idempotency_chk`: `CHECK ((((length(idempotency_key) >= 8) AND (length(idempotency_key) <= 200)) AND (request_sha256 ~ '^[0-9a-f]{64}$'::text)))`
- check `supplier_bills_maker_checker_chk`: `CHECK (((approved_by IS NULL) OR ((approved_by <> created_by) AND (approved_by <> facts_edited_by))))`
- check `supplier_bills_notes_chk`: `CHECK (((notes IS NULL) OR ((length(notes) >= 1) AND (length(notes) <= 2000))))`
- check `supplier_bills_number_chk`: `CHECK (((length(bill_number) >= 1) AND (length(bill_number) <= 100)))`
- check `supplier_bills_paid_chk`: `CHECK (((status = 'paid'::text) = (paid_at IS NOT NULL)))`
- check `supplier_bills_status_chk`: `CHECK ((status = ANY (ARRAY['received'::text, 'approved'::text, 'paid'::text, 'cancelled'::text])))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (amount, approved_at, approved_by, bill_number, cancel_reason, cancelled_at, cancelled_by, currency, document_file_id, due_date, facts_edited_by, issue_date, notes, paid_at, status, supplier_id, trip_case_id, updated_at, updated_by)
- trigger `supplier_bills_check_transition`: BEFORE UPDATE OF status ON booking.supplier_bills FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.ops_check_transition('supplier_bill')
- trigger `supplier_bills_guard`: BEFORE INSERT OR UPDATE ON booking.supplier_bills FOR EACH ROW EXECUTE FUNCTION booking.supplier_bills_guard()
- trigger `supplier_bills_set_updated_at`: BEFORE UPDATE ON booking.supplier_bills FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.supplier_bookings` (table, 240 kB)
```
id uuid NN
code text NN
trip_case_id uuid NN
version_item_id uuid
supplier_id uuid NN
hotel_room_type_id uuid
service_id uuid
item_description text NN
service_date date
nights smallint
pax smallint
net_amount numeric(16,2) · conf:commercial
net_currency character(3)
status text NN
requested_at timestamp with time zone
requested_by text
confirmed_at timestamp with time zone
confirmed_by text
confirmation_ref text
declined_at timestamp with time zone
decline_code text
cancelled_at timestamp with time zone
cancel_reason text · pii:free_text
voucher_file_id uuid
b2b_hold_id uuid
b2b_line_ref text
notes text · pii:free_text (also conf:commercial)
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `supplier_bookings_b2b_line_idx`: btree (b2b_hold_id, b2b_line_ref) WHERE (b2b_hold_id IS NOT NULL)
- index `supplier_bookings_case_idx`: btree (trip_case_id, created_at)
- index `supplier_bookings_code_uq`: UNIQUE btree (code)
- index `supplier_bookings_confirmed_by_idx`: btree (confirmed_by) WHERE (confirmed_by IS NOT NULL)
- index `supplier_bookings_created_by_idx`: btree (created_by) WHERE (created_by IS NOT NULL)
- index `supplier_bookings_item_idx`: btree (version_item_id) WHERE (version_item_id IS NOT NULL)
- index `supplier_bookings_item_live_uq`: UNIQUE btree (version_item_id) WHERE ((status = ANY (ARRAY['pending'::text, 'requested'::text, 'confirmed'::text])) AND (version_item_id IS NOT NULL))
- index `supplier_bookings_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `supplier_bookings_requested_by_idx`: btree (requested_by) WHERE (requested_by IS NOT NULL)
- index `supplier_bookings_room_type_idx`: btree (hotel_room_type_id) WHERE (hotel_room_type_id IS NOT NULL)
- index `supplier_bookings_service_idx`: btree (service_id) WHERE (service_id IS NOT NULL)
- index `supplier_bookings_supplier_idx`: btree (supplier_id, service_date DESC)
- index `supplier_bookings_updated_by_idx`: btree (updated_by) WHERE (updated_by IS NOT NULL)
- index `supplier_bookings_voucher_idx`: btree (voucher_file_id) WHERE (voucher_file_id IS NOT NULL)
- index `supplier_bookings_waiting_idx`: btree (requested_at) WHERE (status = 'requested'::text)
- check `supplier_bookings_b2b_pair_chk`: `CHECK (((b2b_hold_id IS NULL) = (b2b_line_ref IS NULL)))`
- check `supplier_bookings_cancel_chk`: `CHECK ((((status = 'cancelled'::text) = ((cancel_reason IS NOT NULL) AND (cancelled_at IS NOT NULL))) AND ((cancel_reason IS NULL) OR ((length(cancel_reason) >= 1) AND (length(cancel_reason) <= 500)))))`
- check `supplier_bookings_code_chk`: `CHECK ((code ~ '^SB-[0-9]{6,}$'::text))`
- check `supplier_bookings_confirmed_chk`: `CHECK (((status <> 'confirmed'::text) OR ((confirmation_ref IS NOT NULL) AND (confirmed_at IS NOT NULL))))`
- check `supplier_bookings_decline_chk`: `CHECK ((((status = 'declined'::text) = ((decline_code IS NOT NULL) AND (declined_at IS NOT NULL))) AND ((decline_code IS NULL) OR (decline_code = ANY (ARRAY['sold_out'::text, 'supplier_unavailable'::text, 'minimum_not_met'::text, 'other'::text])))))`
- check `supplier_bookings_description_chk`: `CHECK (((length(item_description) >= 1) AND (length(item_description) <= 500)))`
- check `supplier_bookings_net_chk`: `CHECK ((((net_amount IS NULL) = (net_currency IS NULL)) AND ((net_amount IS NULL) OR (net_amount >= (0)::numeric)) AND ((net_currency IS NULL) OR (net_currency ~ '^[A-Z]{3}$'::text))))`
- check `supplier_bookings_nights_chk`: `CHECK (((nights IS NULL) OR ((nights >= 0) AND (nights <= 60))))`
- check `supplier_bookings_notes_chk`: `CHECK (((notes IS NULL) OR ((length(notes) >= 1) AND (length(notes) <= 2000))))`
- check `supplier_bookings_pax_chk`: `CHECK (((pax IS NULL) OR ((pax >= 1) AND (pax <= 120))))`
- check `supplier_bookings_ref_chk`: `CHECK (((confirmation_ref IS NULL) OR ((length(confirmation_ref) >= 1) AND (length(confirmation_ref) <= 100))))`
- check `supplier_bookings_requested_chk`: `CHECK (((status = 'pending'::text) OR (status = 'cancelled'::text) OR (requested_at IS NOT NULL)))`
- check `supplier_bookings_status_chk`: `CHECK ((status = ANY (ARRAY['pending'::text, 'requested'::text, 'confirmed'::text, 'declined'::text, 'cancelled'::text])))`
- check `supplier_bookings_supply_chk`: `CHECK ((num_nonnulls(hotel_room_type_id, service_id) <= 1))`
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `supplier_bookings_check_transition`: BEFORE UPDATE OF status ON booking.supplier_bookings FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.ops_check_transition('supplier_booking')
- trigger `supplier_bookings_guard`: BEFORE INSERT OR UPDATE ON booking.supplier_bookings FOR EACH ROW EXECUTE FUNCTION booking.supplier_bookings_guard()
- trigger `supplier_bookings_set_updated_at`: BEFORE UPDATE ON booking.supplier_bookings FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

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
- check `supplier_contracts_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `supplier_contracts_expired_chk`: `CHECK (((status = 'expired'::text) = ((expired_by IS NOT NULL) AND (expired_at IS NOT NULL))))`
- check `supplier_contracts_maker_checker_chk`: `CHECK (((published_by IS NULL) OR (published_by <> COALESCE(updated_by, created_by))))`
- check `supplier_contracts_published_chk`: `CHECK ((((status = 'draft'::text) AND (published_by IS NULL) AND (published_at IS NULL)) OR ((status = ANY (ARRAY['published'::text, 'expired'::text])) AND (published_by IS NOT NULL) AND (published_at IS NOT NULL))))`
- check `supplier_contracts_status_chk`: `CHECK ((status = ANY (ARRAY['draft'::text, 'published'::text, 'expired'::text])))`
- check `supplier_contracts_title_chk`: `CHECK (((length(btrim(title)) >= 1) AND (length(btrim(title)) <= 200)))`
- check `supplier_contracts_validity_chk`: `CHECK (((valid_to IS NULL) OR (valid_to >= valid_from)))`
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `supplier_contracts_lock`: BEFORE UPDATE ON booking.supplier_contracts FOR EACH ROW EXECUTE FUNCTION booking.supplier_contract_lock()
- trigger `supplier_contracts_rates_fit`: BEFORE UPDATE OF currency, valid_from, valid_to ON booking.supplier_contracts FOR EACH ROW EXECUTE FUNCTION booking.supplier_contract_rates_fit()
- trigger `supplier_contracts_set_updated_at`: BEFORE UPDATE ON booking.supplier_contracts FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.supplier_payouts` (table, 168 kB)
```
id uuid NN
code text NN
bill_id uuid NN
amount numeric(16,2) NN · conf:commercial
currency character(3) NN
method text NN
paid_on date NN
reference text · conf:commercial
note text · pii:free_text
evidence_file_id uuid
idempotency_key text NN
request_sha256 text NN
recorded_by text NN
recorded_at timestamp with time zone NN
voided_by text
voided_at timestamp with time zone
void_reason text · pii:free_text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `supplier_payouts_bill_idx`: btree (bill_id, recorded_at)
- index `supplier_payouts_code_uq`: UNIQUE btree (code)
- index `supplier_payouts_evidence_idx`: btree (evidence_file_id) WHERE (evidence_file_id IS NOT NULL)
- index `supplier_payouts_idempotency_uq`: UNIQUE btree (bill_id, idempotency_key)
- index `supplier_payouts_paid_on_idx`: btree (paid_on)
- index `supplier_payouts_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `supplier_payouts_recorded_by_idx`: btree (recorded_by)
- index `supplier_payouts_reference_idx`: btree (method, reference) WHERE ((voided_at IS NULL) AND (reference IS NOT NULL))
- index `supplier_payouts_updated_by_idx`: btree (updated_by) WHERE (updated_by IS NOT NULL)
- index `supplier_payouts_voided_by_idx`: btree (voided_by) WHERE (voided_by IS NOT NULL)
- check `supplier_payouts_amount_chk`: `CHECK ((amount > (0)::numeric))`
- check `supplier_payouts_code_chk`: `CHECK ((code ~ '^SPO-[0-9]{6,}$'::text))`
- check `supplier_payouts_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `supplier_payouts_idempotency_chk`: `CHECK ((((length(idempotency_key) >= 8) AND (length(idempotency_key) <= 200)) AND (request_sha256 ~ '^[0-9a-f]{64}$'::text)))`
- check `supplier_payouts_method_chk`: `CHECK ((method = ANY (ARRAY['bank_transfer'::text, 'card_offline'::text, 'cash'::text, 'other'::text])))`
- check `supplier_payouts_paid_on_chk`: `CHECK ((paid_on >= '2020-01-01'::date))`
- check `supplier_payouts_text_chk`: `CHECK ((((reference IS NULL) OR ((length(reference) >= 1) AND (length(reference) <= 100))) AND ((note IS NULL) OR ((length(note) >= 1) AND (length(note) <= 2000)))))`
- check `supplier_payouts_void_chk`: `CHECK ((((voided_at IS NULL) = (void_reason IS NULL)) AND ((voided_at IS NULL) = (voided_by IS NULL)) AND ((void_reason IS NULL) OR ((length(void_reason) >= 1) AND (length(void_reason) <= 500)))))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (evidence_file_id, updated_at, updated_by, void_reason, voided_at, voided_by)
- trigger `supplier_payouts_guard`: BEFORE INSERT OR UPDATE ON booking.supplier_payouts FOR EACH ROW EXECUTE FUNCTION booking.supplier_payouts_guard()
- trigger `supplier_payouts_set_updated_at`: BEFORE UPDATE ON booking.supplier_payouts FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()
- trigger `supplier_payouts_settle`: AFTER INSERT OR UPDATE ON booking.supplier_payouts FOR EACH ROW EXECUTE FUNCTION booking.supplier_payouts_settle()

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
- check `supplier_rates_amount_chk`: `CHECK ((net_amount >= (0)::numeric))`
- check `supplier_rates_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `supplier_rates_meal_plan_chk`: `CHECK (((meal_plan IS NULL) OR ((hotel_room_type_id IS NOT NULL) AND (meal_plan = ANY (ARRAY['RO'::text, 'BB'::text, 'HB'::text, 'FB'::text, 'AI'::text])))))`
- check `supplier_rates_pax_chk`: `CHECK ((((pax_min IS NULL) OR ((pax_min >= 1) AND (pax_min <= 999))) AND ((pax_max IS NULL) OR ((pax_max >= 1) AND (pax_max <= 999))) AND ((pax_min IS NULL) OR (pax_max IS NULL) OR (pax_max >= pax_min))))`
- check `supplier_rates_season_chk`: `CHECK (((season IS NULL) OR ((length(season) >= 1) AND (length(season) <= 80))))`
- check `supplier_rates_target_chk`: `CHECK ((num_nonnulls(hotel_room_type_id, service_id) = 1))`
- check `supplier_rates_unit_chk`: `CHECK (((unit = ANY (ARRAY['room_night'::text, 'person'::text, 'group'::text, 'vehicle'::text, 'day'::text])) AND ((hotel_room_type_id IS NOT NULL) = (unit = 'room_night'::text))))`
- check `supplier_rates_validity_chk`: `CHECK (((valid_to IS NULL) OR (valid_to >= valid_from)))`
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
- check `suppliers_categories_chk`: `CHECK ((((cardinality(categories) >= 1) AND (cardinality(categories) <= 6)) AND (categories <@ ARRAY['hotel'::text, 'transport'::text, 'guide'::text, 'entrance'::text, 'activity'::text, 'meal'::text])))`
- check `suppliers_email_chk`: `CHECK (((contact_email IS NULL) OR (contact_email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'::text)))`
- check `suppliers_name_chk`: `CHECK (((length(btrim(company_name)) >= 1) AND (length(btrim(company_name)) <= 200)))`
- check `suppliers_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))`
- check `suppliers_website_chk`: `CHECK (((website IS NULL) OR (website ~* '^https?://[^\s]+$'::text)))`
- grant `booking`: INSERT, SELECT, UPDATE
- trigger `suppliers_set_updated_at`: BEFORE UPDATE ON booking.suppliers FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

### `booking.trip_case_checks` (table, 128 kB)
```
id uuid NN
trip_case_id uuid NN
code text NN
title text NN · pii:free_text
status text NN
due_date date
assignee_ref text
done_by text
done_at timestamp with time zone
note text · pii:free_text
emergency_contact_name text · pii:emergency_contact (also pii:name)
emergency_contact_phone text · pii:emergency_contact (also pii:contact)
cleared_at timestamp with time zone
created_by text
updated_by text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `bk_owner`
- index `trip_case_checks_assignee_idx`: btree (assignee_ref) WHERE (assignee_ref IS NOT NULL)
- index `trip_case_checks_case_idx`: btree (trip_case_id, created_at)
- index `trip_case_checks_created_by_idx`: btree (created_by) WHERE (created_by IS NOT NULL)
- index `trip_case_checks_done_by_idx`: btree (done_by) WHERE (done_by IS NOT NULL)
- index `trip_case_checks_open_due_idx`: btree (due_date) WHERE (status = 'open'::text)
- index `trip_case_checks_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_case_checks_standard_uq`: UNIQUE btree (trip_case_id, code) WHERE (code <> 'custom'::text)
- index `trip_case_checks_uncleared_idx`: btree (trip_case_id) WHERE (cleared_at IS NULL)
- index `trip_case_checks_updated_by_idx`: btree (updated_by) WHERE (updated_by IS NOT NULL)
- check `trip_case_checks_cleared_chk`: `CHECK (((cleared_at IS NULL) OR ((emergency_contact_name IS NULL) AND (emergency_contact_phone IS NULL) AND (note IS NULL))))`
- check `trip_case_checks_code_chk`: `CHECK ((code = ANY (ARRAY['pre_trip_recheck'::text, 'emergency_contact'::text, 'insurance'::text, 'custom'::text])))`
- check `trip_case_checks_contact_name_chk`: `CHECK (((emergency_contact_name IS NULL) OR ((length(emergency_contact_name) >= 1) AND (length(emergency_contact_name) <= 200))))`
- check `trip_case_checks_contact_phone_chk`: `CHECK (((emergency_contact_phone IS NULL) OR (emergency_contact_phone ~ '^\+?[0-9][0-9 ().-]{3,38}[0-9]$'::text)))`
- check `trip_case_checks_contact_row_chk`: `CHECK (((code = 'emergency_contact'::text) OR ((emergency_contact_name IS NULL) AND (emergency_contact_phone IS NULL))))`
- check `trip_case_checks_done_chk`: `CHECK ((((status = 'done'::text) = (done_at IS NOT NULL)) AND ((done_by IS NULL) OR (status = 'done'::text))))`
- check `trip_case_checks_note_chk`: `CHECK (((note IS NULL) OR ((length(note) >= 1) AND (length(note) <= 2000))))`
- check `trip_case_checks_status_chk`: `CHECK ((status = ANY (ARRAY['open'::text, 'done'::text, 'not_applicable'::text])))`
- check `trip_case_checks_title_chk`: `CHECK (((length(title) >= 1) AND (length(title) <= 200)))`
- grant `booking`: INSERT, SELECT
- column grant `booking`: UPDATE (assignee_ref, cleared_at, done_at, done_by, due_date, emergency_contact_name, emergency_contact_phone, note, status, title, updated_at, updated_by)
- trigger `trip_case_checks_guard`: BEFORE INSERT OR UPDATE ON booking.trip_case_checks FOR EACH ROW EXECUTE FUNCTION booking.trip_case_checks_guard()
- trigger `trip_case_checks_set_updated_at`: BEFORE UPDATE ON booking.trip_case_checks FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

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
- check `trip_case_countries_position_chk`: `CHECK (("position" >= 1))`
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
- check `trip_case_legs_position_chk`: `CHECK (("position" >= 1))`
- check `trip_case_legs_tour_key_chk`: `CHECK ((((source_system IS NULL) AND (source_id IS NULL)) OR COALESCE(((source_system = 'cis'::text) AND ((length(btrim(source_id)) >= 1) AND (length(btrim(source_id)) <= 128))), false)))`
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
- check `trip_case_status_history_from_chk`: `CHECK (((from_status IS NULL) OR (from_status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text]))))`
- check `trip_case_status_history_to_chk`: `CHECK ((to_status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text])))`
- grant `booking`: INSERT, SELECT

### `booking.trip_case_status_transitions` (table, 32 kB)
```
from_status text NN
to_status text NN
```
- owner `bk_owner`
- index `trip_case_status_transitions_pk` PRIMARY KEY: UNIQUE btree (from_status, to_status)
- check `trip_case_status_transitions_distinct_chk`: `CHECK ((from_status <> to_status))`
- check `trip_case_status_transitions_from_chk`: `CHECK ((from_status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text])))`
- check `trip_case_status_transitions_to_chk`: `CHECK ((to_status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text])))`
- grant `booking`: SELECT

### `booking.trip_case_version_itinerary` (table, ~25 rows, 96 kB)
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
- index `trip_case_version_itinerary_source_tour_idx`: btree (source_tour_id) WHERE (source_tour_id IS NOT NULL)
- check `trip_case_version_itinerary_days_chk`: `CHECK (((day_from >= 1) AND (day_to >= day_from)))`
- check `trip_case_version_itinerary_position_chk`: `CHECK (("position" >= 1))`
- check `trip_case_version_itinerary_supply_chk`: `CHECK ((num_nonnulls(hotel_room_type_id, service_id) <= 1))`
- check `trip_case_version_itinerary_title_chk`: `CHECK (((length(title) >= 1) AND (length(title) <= 500)))`
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
- check `trip_case_versions_approved_chk`: `CHECK (((NOT is_approved) OR (approved_at IS NOT NULL)))`
- check `trip_case_versions_channel_chk`: `CHECK (((channel IS NULL) OR (channel = ANY (ARRAY['b2c_tailor_made'::text, 'fixed_departure'::text, 'b2b'::text]))))`
- check `trip_case_versions_currency_chk`: `CHECK (((currency IS NULL) OR (currency ~ '^[A-Z]{3}$'::text)))`
- check `trip_case_versions_deleted_chk`: `CHECK (((deleted_at IS NULL) OR ((NOT is_sent_to_customer) AND (NOT is_approved))))`
- check `trip_case_versions_fx_chk`: `CHECK (((fx_rate_locked IS NULL) OR (fx_rate_locked > (0)::numeric)))`
- check `trip_case_versions_number_chk`: `CHECK ((version_number >= 1))`
- check `trip_case_versions_price_chk`: `CHECK (((total_price IS NULL) OR (total_price >= (0)::numeric)))`
- check `trip_case_versions_sent_chk`: `CHECK (((NOT is_sent_to_customer) OR (sent_at IS NOT NULL)))`
- check `trip_case_versions_title_chk`: `CHECK (((title IS NULL) OR ((length(title) >= 1) AND (length(title) <= 200))))`
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
- check `trip_cases_channel_chk`: `CHECK ((((channel = 'b2c'::text) AND (customer_id IS NOT NULL) AND (party_tenant_id IS NULL)) OR ((channel = 'b2b'::text) AND (customer_id IS NULL) AND (party_tenant_id IS NOT NULL))))`
- check `trip_cases_currency_chk`: `CHECK (((currency IS NULL) OR (currency ~ '^[A-Z]{3}$'::text)))`
- check `trip_cases_dates_chk`: `CHECK (((start_date IS NULL) OR (end_date IS NULL) OR (start_date <= end_date)))`
- check `trip_cases_pax_chk`: `CHECK (((pax IS NULL) OR (pax > 0)))`
- check `trip_cases_pax_split_chk`: `CHECK ((((pax_adults IS NULL) OR (pax_adults >= 1)) AND ((pax_children IS NULL) OR ((pax_children >= 0) AND (pax_adults IS NOT NULL))) AND ((pax_adults IS NULL) OR (pax = (pax_adults + COALESCE((pax_children)::integer, 0))))))`
- check `trip_cases_source_system_chk`: `CHECK ((source_system = ANY (ARRAY['cis'::text, 'tripplanner'::text, 'manual'::text, 'crm'::text])))`
- check `trip_cases_status_chk`: `CHECK ((status = ANY (ARRAY['new_inquiry'::text, 'discovery'::text, 'building'::text, 'proposal_sent'::text, 'confirmed'::text, 'supplier_confirming'::text, 'invoice_sent'::text, 'payment_pending'::text, 'paid'::text, 'pre_departure'::text, 'on_trip'::text, 'completed'::text, 'cancelled'::text])))`
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `trip_cases_check_transition`: BEFORE UPDATE OF status ON booking.trip_cases FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.trip_case_check_transition()
- trigger `trip_cases_post_sale_guard`: BEFORE UPDATE OF status ON booking.trip_cases FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.trip_cases_post_sale_guard()
- trigger `trip_cases_record_status_insert`: AFTER INSERT ON booking.trip_cases FOR EACH ROW EXECUTE FUNCTION booking.trip_case_record_status()
- trigger `trip_cases_record_status_update`: AFTER UPDATE OF status ON booking.trip_cases FOR EACH ROW WHEN ((old.status IS DISTINCT FROM new.status)) EXECUTE FUNCTION booking.trip_case_record_status()
- trigger `trip_cases_seed_checks`: AFTER INSERT OR UPDATE OF status, start_date ON booking.trip_cases FOR EACH ROW EXECUTE FUNCTION booking.trip_case_seed_checks()
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
- check `trip_plan_components_day_chk`: `CHECK (((day_no >= 1) AND (day_no <= 366)))`
- check `trip_plan_components_target_chk`: `CHECK ((num_nonnulls(hotel_room_type_id, service_id) = 1))`
- grant `booking`: DELETE, INSERT, SELECT

### `booking.trip_plan_prices` (table, 32 kB)
```
id uuid NN
trip_plan_id uuid NN
position smallint NN
channel text NN
season text
peak boolean NN
valid_from date NN
valid_to date NN
pax_min smallint NN
pax_max smallint
currency character(3) NN
amount numeric(12,2) NN · conf:commercial
net_amount numeric(12,2) · conf:commercial
net_currency character(3) · conf:commercial
effective_margin numeric(12,4) · conf:commercial
priced_on date
overridden boolean NN
created_by text
created_at timestamp with time zone NN
```
- owner `bk_owner`
- index `trip_plan_prices_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_plan_prices_plan_idx`: btree (trip_plan_id, channel, currency, valid_from)
- index `trip_plan_prices_position_uq`: UNIQUE btree (trip_plan_id, "position")
- check `trip_plan_prices_amount_chk`: `CHECK ((amount > (0)::numeric))`
- check `trip_plan_prices_channel_chk`: `CHECK ((channel = ANY (ARRAY['b2c_tailor_made'::text, 'fixed_departure'::text, 'b2b'::text])))`
- check `trip_plan_prices_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `trip_plan_prices_net_chk`: `CHECK ((((net_amount IS NULL) AND (net_currency IS NULL) AND (effective_margin IS NULL) AND (priced_on IS NULL)) OR ((net_amount IS NOT NULL) AND (net_currency IS NOT NULL) AND (priced_on IS NOT NULL) AND (net_amount >= (0)::numeric) AND (net_currency ~ '^[A-Z]{3}$'::text))))`
- check `trip_plan_prices_override_chk`: `CHECK (((NOT overridden) OR (net_amount IS NOT NULL)))`
- check `trip_plan_prices_pax_chk`: `CHECK ((((pax_min >= 1) AND (pax_min <= 999)) AND ((pax_max IS NULL) OR (((pax_max >= 1) AND (pax_max <= 999)) AND (pax_max >= pax_min)))))`
- check `trip_plan_prices_position_chk`: `CHECK ((("position" >= 1) AND ("position" <= 200)))`
- check `trip_plan_prices_season_chk`: `CHECK (((season IS NULL) OR ((length(btrim(season)) >= 1) AND (length(btrim(season)) <= 80))))`
- check `trip_plan_prices_validity_chk`: `CHECK ((valid_to >= valid_from))`
- grant `booking`: DELETE, INSERT, SELECT

### `booking.trip_plans` (table, ~2 rows, 72 kB)
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
supplier_id uuid · conf:commercial
```
- owner `bk_owner`
- index `trip_plans_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `trip_plans_sellable_idx`: btree (source_id) WHERE sellable
- index `trip_plans_source_uq`: UNIQUE btree (source_system, source_id)
- index `trip_plans_supplier_idx`: btree (supplier_id) WHERE (supplier_id IS NOT NULL)
- check `trip_plans_channel_chk`: `CHECK (((default_channel IS NULL) OR (default_channel = ANY (ARRAY['b2c_tailor_made'::text, 'fixed_departure'::text, 'b2b'::text]))))`
- check `trip_plans_notes_chk`: `CHECK (((commercial_notes IS NULL) OR (length(commercial_notes) <= 5000)))`
- check `trip_plans_price_hint_chk`: `CHECK ((((price_hint_amount IS NULL) AND (price_hint_currency IS NULL) AND (price_hint_basis IS NULL)) OR ((price_hint_amount IS NOT NULL) AND (price_hint_currency IS NOT NULL) AND (price_hint_basis IS NOT NULL) AND (price_hint_amount > (0)::numeric) AND (price_hint_currency ~ '^[A-Z]{3}$'::text) AND (price_hint_basis = ANY (ARRAY['per_person'::text, 'per_group'::text])))))`
- check `trip_plans_source_id_chk`: `CHECK (((length(btrim(source_id)) >= 1) AND (length(btrim(source_id)) <= 128)))`
- check `trip_plans_source_system_chk`: `CHECK ((source_system = 'cis'::text))`
- check `trip_plans_trip_style_chk`: `CHECK (((trip_style IS NULL) OR ((length(btrim(trip_style)) >= 1) AND (length(btrim(trip_style)) <= 60))))`
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

### `booking.v_invoice_balance` (VIEW)
```
invoice_id uuid
invoice_number text
trip_case_id uuid
status text
is_deleted boolean
currency character(3)
total_amount numeric(16,2)
verified_received numeric(16,2)
verified_refunded numeric(16,2)
net_paid numeric(16,2)
unverified_amount numeric(16,2)
unverified_count integer
balance numeric
next_due_date date
overdue_amount numeric(16,2)
oldest_overdue_date date
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

### `booking.v_ops_data_totals` (VIEW)
```
metric text
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

### `booking.v_ops_inquiry_inbox` (VIEW)
```
source text
idempotency_key text
status text
received_at timestamp with time zone
processed_at timestamp with time zone
has_trip_case boolean
```
- owner `bk_owner`
- grant `booking`: SELECT
- grant `cis_app`: SELECT

### `booking.v_ops_trip_plan_keys` (VIEW)
```
source_system text
source_id text
sellable boolean
```
- owner `bk_owner`
- grant `booking`: SELECT
- grant `cis_app`: SELECT

### `booking.v_payment_schedule_status` (VIEW)
```
schedule_id uuid
invoice_id uuid
seq smallint
kind text
amount numeric(16,2)
due_date date
covered_amount numeric(16,2)
remaining_amount numeric(16,2)
state text
days_overdue integer
```
- owner `bk_owner`
- grant `booking`: SELECT

### `booking.v_schema_versions` (VIEW)
```
version character varying(20)
description text
applied_at timestamp with time zone
```
- owner `bk_owner`
- grant `booking`: SELECT

### `booking.v_supplier_bill_balance` (VIEW)
```
bill_id uuid
supplier_id uuid
status text
currency character(3)
amount numeric(16,2)
paid_amount numeric(16,2)
live_payouts bigint
balance numeric(16,2)
line_count bigint
lines_amount numeric(16,2)
due_date date
overdue boolean
```
- owner `bk_owner`
- grant `booking`: SELECT

### `booking.v_supply_hotels` (VIEW)
```
id uuid
supply_version bigint
name text
hotel_style text
star_rating smallint
address text
destination_id uuid
country_code text
lat double precision
lng double precision
check_in_time time without time zone
check_out_time time without time zone
amenities text[]
room_types jsonb
status text
media jsonb
```
- owner `bk_owner`
- grant `booking`: SELECT
- grant `cis_app`: SELECT

### `booking.v_supply_media` (VIEW)
```
media_id uuid
entity_type text
entity_id uuid
usage_rights boolean
s3_bucket text
s3_key text
sha256 text
content_type text
```
- owner `bk_owner`
- grant `booking`: SELECT
- grant `cis_app`: SELECT

### `booking.v_supply_outbox` (VIEW)
```
event_id uuid
event_type text
entity_type text
entity_id uuid
supply_version bigint
occurred_at timestamp with time zone
feed_seq bigint
```
- owner `bk_owner`
- grant `booking`: SELECT
- grant `cis_app`: SELECT

### `booking.v_supply_services` (VIEW)
```
id uuid
supply_version bigint
service_type text
working_title text
unit text
destination_id uuid
country_code text
duration_minutes integer
max_group_size smallint
inclusions text[]
status text
media jsonb
```
- owner `bk_owner`
- grant `booking`: SELECT
- grant `cis_app`: SELECT

### `booking.v_trip_case_supply_state` (VIEW)
```
trip_case_id uuid
items_to_book integer
items_booked integer
live integer
confirmed integer
waiting integer
declined integer
state text
```
- owner `bk_owner`
- grant `booking`: SELECT

### `booking.v_trip_check_board` (VIEW)
```
trip_case_id uuid
trip_case_code text
channel text
case_status text
start_date date
end_date date
checks_total integer
checks_open integer
checks_done integer
checks_not_applicable integer
checks_overdue integer
next_due_date date
supply_state text
suppliers_confirmed boolean
payment_verified boolean
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
- check `version_item_costs_amount_chk`: `CHECK ((net_amount >= (0)::numeric))`
- check `version_item_costs_currency_chk`: `CHECK ((net_currency ~ '^[A-Z]{3}$'::text))`
- grant `booking`: DELETE, INSERT, SELECT, UPDATE
- trigger `version_item_costs_lock`: BEFORE INSERT OR DELETE OR UPDATE ON booking.version_item_costs FOR EACH ROW EXECUTE FUNCTION booking.version_item_cost_lock()
- trigger `version_item_costs_set_updated_at`: BEFORE UPDATE ON booking.version_item_costs FOR EACH ROW EXECUTE FUNCTION booking.set_updated_at()

## `catalog` (25 objects)

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

### `catalog.v_component_redirect` (VIEW)
```
component_id uuid
new_component_id uuid
```
- owner `catalog_owner`
- grant `tripplanner`: SELECT

### `catalog.v_country` (VIEW)
```
iso2 character(2)
iso3 character(3)
numeric_code character(3)
name text
iso_name text
```
- owner `catalog_owner`
- grant `booking`: SELECT
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
country_iso2 character(2)
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

### `catalog.v_supply_content` (VIEW)
```
source_system text
source_id text
entity_type text
content_status text
content_version integer
description text
highlights text[]
good_to_know text[]
photo_urls text[]
edit_url text
published_at timestamp with time zone
```
- owner `catalog_owner`
- grant `booking`: SELECT

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

### `catalog.v_tour_place_name` (VIEW)
```
source_system text
source_id text
tour_id uuid
day_number smallint
position bigint
place_name text
```
- owner `catalog_owner`
- grant `booking`: SELECT

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

## `crm` (85 objects)

### `crm.aa_catalog_state` (table, ~1 rows, 64 kB)
```
singleton boolean NN
list_cursor text
pass_started_at timestamp with time zone
last_full_pass_at timestamp with time zone
failures integer NN
last_error_class text
last_error_at timestamp with time zone
last_ok_at timestamp with time zone
```
- owner `crm_owner`
- index `aa_catalog_state_pkey` PRIMARY KEY: UNIQUE btree (singleton)
- check `aa_catalog_state_one_chk`: `CHECK (singleton)`
- check `aa_catalog_state_values_chk`: `CHECK ((((list_cursor IS NULL) OR ((char_length(list_cursor) >= 1) AND (char_length(list_cursor) <= 200))) AND (failures >= 0) AND (COALESCE(last_error_class, 'x'::text) ~ '^[a-z][a-z0-9_]{0,59}$'::text)))`
- grant `crm_app`: SELECT, UPDATE

### `crm.aa_catalog_tour` (table, ~892 rows, 6.4 MB)
```
source_system text NN
source_id text NN
title text NN
country_code character(2)
duration_days integer
content_hash text
etag text
served_state text NN
reason text
body jsonb
fetched_at timestamp with time zone
checked_at timestamp with time zone NN
state_changed_at timestamp with time zone NN
```
- owner `crm_owner`
- index `aa_catalog_tour_pkey` PRIMARY KEY: UNIQUE btree (source_system, source_id)
- index `aa_catalog_tour_served_idx`: btree (served_state, country_code, title)
- check `aa_catalog_tour_values_chk`: `CHECK (((source_system = 'cis'::text) AND ((char_length(source_id) >= 1) AND (char_length(source_id) <= 128)) AND (source_id !~ '[[:cntrl:]]'::text) AND ((char_length(title) >= 1) AND (char_length(title) <= 300)) AND (COALESCE(country_code, 'VN'::bpchar) ~ '^[A-Z]{2}$'::text) AND ((duration_days IS NULL) OR ((duration_days >= 1) AND (duration_days <= 366))) AND ((content_hash IS NULL) OR (char_length(content_hash) <= 100)) AND ((etag IS NULL) OR (char_length(etag) <= 100)) AND (served_state = ANY (ARRAY['served'::text, 'paused'::text, 'retired'::text])) AND (COALESCE(reason, 'x'::text) ~ '^[a-z][a-z_]{0,63}$'::text) AND ((body IS NULL) OR (jsonb_typeof(body) = 'object'::text))))`
- grant `crm_app`: INSERT, SELECT, UPDATE

### `crm.aa_content` (table, ~23 rows, 248 kB)
```
content_id uuid NN
kind text NN
locale text NN
group_key text
version integer NN
title text NN
body_markdown text NN
applies_to jsonb NN
content_hash text NN
published_at timestamp with time zone NN
listed boolean NN
fetched_at timestamp with time zone NN
checked_at timestamp with time zone NN
```
- owner `crm_owner`
- index `aa_content_kind_idx`: btree (kind, locale, group_key) WHERE listed
- index `aa_content_pkey` PRIMARY KEY: UNIQUE btree (content_id)
- check `aa_content_values_chk`: `CHECK (((kind = ANY (ARRAY['prep_pack'::text, 'starter_template'::text, 'campaign_block'::text])) AND (locale = ANY (ARRAY['en'::text, 'vi'::text])) AND ((group_key IS NULL) OR (group_key ~ '^[a-z0-9][a-z0-9-]{1,79}$'::text)) AND (version >= 1) AND ((char_length(title) >= 1) AND (char_length(title) <= 300)) AND (title !~ '[[:cntrl:]]'::text) AND (octet_length(body_markdown) <= 200000) AND (jsonb_typeof(applies_to) = 'object'::text) AND ((char_length(content_hash) >= 1) AND (char_length(content_hash) <= 100))))`
- grant `crm_app`: INSERT, SELECT, UPDATE

### `crm.aa_request` (table, ~19 rows, 112 kB)
```
aa_request_id uuid NN
tenant_id uuid NN
trip_id uuid NN
booking_line_id uuid NN
kind text NN
status text NN
tour_source_id text
component_id text
component_kind text
departure_id text
service_date date
nights smallint
pax_adult smallint
pax_child smallint
pax_infant smallint
rooms jsonb
currency character(3)
sell_amount numeric(14,2)
attempts integer NN
next_attempt_at timestamp with time zone NN
lease_until timestamp with time zone
last_error_class text
result_code text
finished_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `aa_request_due_idx`: btree (tenant_id, next_attempt_at) WHERE (status = 'pending'::text)
- index `aa_request_line_idx`: btree (tenant_id, booking_line_id)
- index `aa_request_live_uq`: UNIQUE btree (tenant_id, booking_line_id, kind) WHERE ((status = 'pending'::text) AND (deleted_at IS NULL))
- index `aa_request_pkey` PRIMARY KEY: UNIQUE btree (aa_request_id)
- index `aa_request_tenant_id_uq`: UNIQUE btree (tenant_id, aa_request_id)
- index `aa_request_trip_idx`: btree (tenant_id, trip_id)
- check `aa_request_finished_chk`: `CHECK (((status = 'pending'::text) = (finished_at IS NULL)))`
- check `aa_request_kind_chk`: `CHECK ((kind = ANY (ARRAY['quote'::text, 'requote'::text, 'hold'::text, 'confirm'::text, 'release'::text, 'refresh'::text])))`
- check `aa_request_params_chk`: `CHECK ((((kind = 'quote'::text) AND (num_nulls(tour_source_id, component_id, component_kind, service_date, pax_adult, pax_child, pax_infant, currency) = 0)) OR ((kind <> 'quote'::text) AND (num_nonnulls(tour_source_id, component_id, component_kind, departure_id, service_date, nights, pax_adult, pax_child, pax_infant, rooms, currency) = 0) AND ((kind = 'requote'::text) OR (sell_amount IS NULL)))))`
- check `aa_request_status_chk`: `CHECK ((status = ANY (ARRAY['pending'::text, 'done'::text, 'failed'::text, 'cancelled'::text])))`
- check `aa_request_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `aa_request_values_chk`: `CHECK ((((tour_source_id IS NULL) OR (((char_length(tour_source_id) >= 1) AND (char_length(tour_source_id) <= 128)) AND (tour_source_id !~ '[[:cntrl:]]'::text))) AND (COALESCE(component_id, 'x'::text) ~ '^[A-Za-z0-9:_.-]{1,64}$'::text) AND ((component_kind IS NULL) OR (component_kind = ANY (ARRAY['trip_plan'::text, 'hotel_room'::text, 'transfer'::text, 'guide'::text, 'activity'::text, 'entrance'::text, 'meal'::text]))) AND (COALESCE(departure_id, 'x'::text) ~ '^[A-Za-z0-9:_.-]{1,64}$'::text) AND ((nights IS NULL) OR ((nights >= 1) AND (nights <= 60))) AND ((pax_adult IS NULL) OR ((pax_adult >= 1) AND (pax_adult <= 60))) AND ((pax_child IS NULL) OR ((pax_child >= 0) AND (pax_child <= 60))) AND ((pax_infant IS NULL) OR ((pax_infant >= 0) AND (pax_infant <= 20))) AND ((rooms IS NULL) OR ((jsonb_typeof(rooms) = 'array'::text) AND ((jsonb_array_length(rooms) >= 1) AND (jsonb_array_length(rooms) <= 30)))) AND (COALESCE(currency, 'USD'::bpchar) ~ '^[A-Z]{3}$'::text) AND ((sell_amount IS NULL) OR (sell_amount >= (0)::numeric)) AND (attempts >= 0) AND (COALESCE(last_error_class, 'x'::text) ~ '^[a-z][a-z0-9_]{0,59}$'::text) AND (COALESCE(result_code, 'x'::text) ~ '^[a-z][a-z_]{0,39}$'::text)))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `aa_request_hold_guard`: BEFORE DELETE OR UPDATE ON crm.aa_request FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `aa_request_set_updated_at`: BEFORE UPDATE ON crm.aa_request FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `aa_request_status_transition`: BEFORE UPDATE OF status ON crm.aa_request FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.agency_supplier` (table, 80 kB)
```
agency_supplier_id uuid NN
tenant_id uuid NN
kind text NN
name text NN
category text NN
contact_name_enc bytea · pii:name
contact_email_enc bytea · pii:contact
default_commission_pct numeric(5,2) · conf:commercial
confirmation_unique boolean NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `agency_supplier_aa_uq`: UNIQUE btree (tenant_id) WHERE (kind = 'aa'::text)
- index `agency_supplier_pkey` PRIMARY KEY: UNIQUE btree (agency_supplier_id)
- index `agency_supplier_tenant_id_uq`: UNIQUE btree (tenant_id, agency_supplier_id)
- index `agency_supplier_tenant_idx`: btree (tenant_id, name) WHERE (deleted_at IS NULL)
- check `agency_supplier_category_chk`: `CHECK ((category = ANY (ARRAY['accommodation'::text, 'transport'::text, 'activity'::text, 'guide'::text, 'restaurant'::text, 'flight'::text, 'insurance'::text, 'visa'::text, 'dmc'::text, 'other'::text])))`
- check `agency_supplier_commission_chk`: `CHECK (((default_commission_pct IS NULL) OR ((default_commission_pct >= (0)::numeric) AND (default_commission_pct <= (100)::numeric))))`
- check `agency_supplier_contact_chk`: `CHECK (((COALESCE(octet_length(contact_name_enc), 30) >= 30) AND (COALESCE(octet_length(contact_email_enc), 30) >= 30) AND ((kind = 'own'::text) OR ((contact_name_enc IS NULL) AND (contact_email_enc IS NULL)))))`
- check `agency_supplier_kind_chk`: `CHECK ((kind = ANY (ARRAY['aa'::text, 'own'::text])))`
- check `agency_supplier_name_chk`: `CHECK ((((char_length(btrim(name)) >= 1) AND (char_length(btrim(name)) <= 120)) AND (name !~ '[[:cntrl:]]'::text)))`
- check `agency_supplier_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `agency_supplier_guard`: BEFORE INSERT OR UPDATE ON crm.agency_supplier FOR EACH ROW EXECUTE FUNCTION crm.guard_agency_supplier()
- trigger `agency_supplier_hold_guard`: BEFORE DELETE OR UPDATE ON crm.agency_supplier FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change()
- trigger `agency_supplier_set_updated_at`: BEFORE UPDATE ON crm.agency_supplier FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.agreement_doc` (table, ~18 rows, 80 kB)
```
doc_id uuid NN
tenant_id uuid NN
kind text NN
version_label text NN
body_text text NN
body_sha256 bytea NN
status text NN
published_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `agreement_doc_one_published_uq`: UNIQUE btree (tenant_id, kind) WHERE ((status = 'published'::text) AND (deleted_at IS NULL))
- index `agreement_doc_pkey` PRIMARY KEY: UNIQUE btree (doc_id)
- index `agreement_doc_tenant_id_uq`: UNIQUE btree (tenant_id, doc_id)
- index `agreement_doc_version_uq`: UNIQUE btree (tenant_id, kind, version_label)
- check `agreement_doc_body_chk`: `CHECK ((((char_length(body_text) >= 1) AND (char_length(body_text) <= 100000)) AND (octet_length(body_sha256) = 32)))`
- check `agreement_doc_kind_chk`: `CHECK ((kind = ANY (ARRAY['booking_terms'::text, 'waiver'::text])))`
- check `agreement_doc_label_chk`: `CHECK ((((char_length(version_label) >= 1) AND (char_length(version_label) <= 40)) AND (version_label !~ '[[:cntrl:]]'::text)))`
- check `agreement_doc_published_chk`: `CHECK (((status = 'draft'::text) = (published_at IS NULL)))`
- check `agreement_doc_status_chk`: `CHECK ((status = ANY (ARRAY['draft'::text, 'published'::text, 'retired'::text])))`
- check `agreement_doc_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `agreement_doc_hold_guard`: BEFORE DELETE OR UPDATE ON crm.agreement_doc FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change()
- trigger `agreement_doc_sealed`: BEFORE UPDATE ON crm.agreement_doc FOR EACH ROW EXECUTE FUNCTION crm.guard_sealed_row('draft', 'kind', 'version_label', 'body_text', 'published_at', 'tenant_id')
- trigger `agreement_doc_set_updated_at`: BEFORE UPDATE ON crm.agreement_doc FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `agreement_doc_sha256`: BEFORE INSERT OR UPDATE ON crm.agreement_doc FOR EACH ROW EXECUTE FUNCTION crm.set_agreement_doc_sha256()
- trigger `agreement_doc_status_transition`: BEFORE UPDATE OF status ON crm.agreement_doc FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

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
- check `audit_event_action_chk`: `CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_actor_kind_chk`: `CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))`
- check `audit_event_actor_ref_chk`: `CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))`
- check `audit_event_fields_chk`: `CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))`
- check `audit_event_object_id_chk`: `CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))`
- check `audit_event_object_ids_chk`: `CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))`
- check `audit_event_object_kind_chk`: `CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_outcome_chk`: `CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))`
- check `audit_event_reason_chk`: `CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))`
- check `audit_event_request_id_chk`: `CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))`
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_event_append_only`: BEFORE DELETE OR UPDATE ON crm.audit_event FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `audit_event_check_at`: BEFORE INSERT ON crm.audit_event FOR EACH ROW EXECUTE FUNCTION crm.audit_event_check_at()
- trigger `audit_event_no_truncate`: BEFORE TRUNCATE ON crm.audit_event FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.audit_event_legacy` (table, ~2806 rows, 1.7 MB)
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
- check `audit_event_action_chk`: `CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_actor_kind_chk`: `CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))`
- check `audit_event_actor_ref_chk`: `CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))`
- check `audit_event_fields_chk`: `CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))`
- check `audit_event_object_id_chk`: `CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))`
- check `audit_event_object_ids_chk`: `CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))`
- check `audit_event_object_kind_chk`: `CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_outcome_chk`: `CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))`
- check `audit_event_reason_chk`: `CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))`
- check `audit_event_request_id_chk`: `CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))`
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
- check `audit_event_action_chk`: `CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_actor_kind_chk`: `CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))`
- check `audit_event_actor_ref_chk`: `CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))`
- check `audit_event_fields_chk`: `CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))`
- check `audit_event_object_id_chk`: `CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))`
- check `audit_event_object_ids_chk`: `CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))`
- check `audit_event_object_kind_chk`: `CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_outcome_chk`: `CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))`
- check `audit_event_reason_chk`: `CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))`
- check `audit_event_request_id_chk`: `CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))`
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
- check `audit_event_action_chk`: `CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_actor_kind_chk`: `CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))`
- check `audit_event_actor_ref_chk`: `CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))`
- check `audit_event_fields_chk`: `CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))`
- check `audit_event_object_id_chk`: `CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))`
- check `audit_event_object_ids_chk`: `CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))`
- check `audit_event_object_kind_chk`: `CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_outcome_chk`: `CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))`
- check `audit_event_reason_chk`: `CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))`
- check `audit_event_request_id_chk`: `CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))`
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
- check `audit_event_action_chk`: `CHECK ((action ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_actor_kind_chk`: `CHECK ((actor_kind = ANY (ARRAY['user'::text, 'traveler'::text, 'ai_agent'::text, 'aa_ops'::text, 'aa_staff'::text, 'support'::text, 'breakglass'::text, 'system'::text])))`
- check `audit_event_actor_ref_chk`: `CHECK ((actor_ref ~ '^[A-Za-z0-9:_-]{1,80}$'::text))`
- check `audit_event_fields_chk`: `CHECK (((cardinality(fields) <= 32) AND (array_to_string(fields, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{0,62}(,|$))*$'::text)))`
- check `audit_event_object_id_chk`: `CHECK (((object_id IS NULL) OR (object_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)))`
- check `audit_event_object_ids_chk`: `CHECK (((cardinality(object_ids) <= 200) AND (array_to_string(object_ids, ','::text, '!'::text) ~ '^([A-Za-z0-9:_-]{1,80}(,|$))*$'::text)))`
- check `audit_event_object_kind_chk`: `CHECK ((object_kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `audit_event_outcome_chk`: `CHECK ((outcome = ANY (ARRAY['allowed'::text, 'denied'::text])))`
- check `audit_event_reason_chk`: `CHECK (((reason IS NULL) OR (reason ~ '^[a-z][a-z0-9_]{0,63}$'::text)))`
- check `audit_event_request_id_chk`: `CHECK (((request_id IS NULL) OR (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'::text)))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_event_append_only`: BEFORE DELETE OR UPDATE ON crm.audit_event_p202701 FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `audit_event_check_at`: BEFORE INSERT ON crm.audit_event_p202701 FOR EACH ROW EXECUTE FUNCTION crm.audit_event_check_at()
- trigger `audit_event_no_truncate`: BEFORE TRUNCATE ON crm.audit_event_p202701 FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.audit_export_manifest` (table, ~426 rows, 376 kB)
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
- check `audit_export_manifest_count_chk`: `CHECK ((event_count >= 0))`
- check `audit_export_manifest_format_chk`: `CHECK ((format_version = 1))`
- check `audit_export_manifest_hashes_chk`: `CHECK (((content_sha256 ~ '^[0-9a-f]{64}$'::text) AND (prev_manifest_sha256 ~ '^[0-9a-f]{64}$'::text) AND (manifest_sha256 ~ '^[0-9a-f]{64}$'::text) AND (object_sha256 ~ '^[0-9a-f]{64}$'::text)))`
- check `audit_export_manifest_key_chk`: `CHECK (((object_key ~~ (('audit/v1/tenants/'::text || (tenant_id)::text) || '/%'::text)) AND (object_key ~ '^audit/v1/tenants/[0-9a-f-]{36}/[0-9]{4}/[0-9]{2}/[0-9]{2}/[0-9]{4}Z-[0-9]{10}\.jsonl$'::text)))`
- check `audit_export_manifest_period_chk`: `CHECK (((period_end > period_start) AND (period_start = (date_trunc('hour'::text, (period_start AT TIME ZONE 'UTC'::text)) AT TIME ZONE 'UTC'::text)) AND (period_end = (date_trunc('hour'::text, (period_end AT TIME ZONE 'UTC'::text)) AT TIME ZONE 'UTC'::text))))`
- check `audit_export_manifest_seq_chk`: `CHECK ((seq >= 1))`
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_export_manifest_append_only`: BEFORE DELETE OR UPDATE ON crm.audit_export_manifest FOR EACH ROW EXECUTE FUNCTION crm.reject_append_only_change()
- trigger `audit_export_manifest_chain`: BEFORE INSERT ON crm.audit_export_manifest FOR EACH ROW EXECUTE FUNCTION crm.audit_manifest_chain()
- trigger `audit_export_manifest_no_truncate`: BEFORE TRUNCATE ON crm.audit_export_manifest FOR EACH STATEMENT EXECUTE FUNCTION crm.reject_append_only_change()

### `crm.audit_export_tenant` (table, ~4 rows, 56 kB)
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
- check `audit_export_tenant_hour_chk`: `CHECK (((exported_until = (date_trunc('hour'::text, (exported_until AT TIME ZONE 'UTC'::text)) AT TIME ZONE 'UTC'::text)) AND ((verified_until IS NULL) OR (verified_until = (date_trunc('hour'::text, (verified_until AT TIME ZONE 'UTC'::text)) AT TIME ZONE 'UTC'::text)))))`
- check `audit_export_tenant_seq_chk`: `CHECK ((last_seq >= 0))`
- check `audit_export_tenant_verified_chk`: `CHECK (((verified_until IS NULL) OR (verified_until <= exported_until)))`
- grant `crm_app`: SELECT
- column grant `crm_app`: INSERT (tenant_id)
- column grant `crm_app`: INSERT, UPDATE (exported_until)
- column grant `crm_app`: UPDATE (last_seq)
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `audit_export_tenant_set_updated_at`: BEFORE UPDATE ON crm.audit_export_tenant FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.booking_feed_state` (table, ~1 rows, 48 kB)
```
booking_feed_state_id uuid NN
tenant_id uuid NN
feed_cursor text
failures integer NN
last_error_class text
last_error_at timestamp with time zone
last_ok_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `booking_feed_state_pkey` PRIMARY KEY: UNIQUE btree (booking_feed_state_id)
- index `booking_feed_state_tenant_uq`: UNIQUE btree (tenant_id)
- check `booking_feed_state_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `booking_feed_state_values_chk`: `CHECK ((((feed_cursor IS NULL) OR ((char_length(feed_cursor) >= 1) AND (char_length(feed_cursor) <= 200))) AND (failures >= 0) AND (COALESCE(last_error_class, 'x'::text) ~ '^[a-z][a-z0-9_]{0,59}$'::text)))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `booking_feed_state_set_updated_at`: BEFORE UPDATE ON crm.booking_feed_state FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.booking_line` (table, 136 kB)
```
booking_line_id uuid NN
tenant_id uuid NN
trip_id uuid NN
supplier_kind text NN
agency_supplier_id uuid NN
bk_hold_id text
bk_booking_id text
departure_id text
status text NN
aa_sub_status text
title text NN
confirmation_no text
conf_unique_key text
service_from date
service_to date
collect text NN
confirm_class text
visible_to_travelers boolean NN
confirmed_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
aa_tour_source_id text
aa_component_id text
aa_component_kind text
aa_currency character(3)
aa_pax jsonb
bk_quote_id text
aa_price_hash text
aa_quote_version integer
quote_valid_until timestamp with time zone
hold_expires_at timestamp with time zone
from_price numeric(14,2)
below_from_price boolean
aa_decline_code text
aa_result_code text
```
- owner `crm_owner` · RLS on + FORCE
- index `booking_line_booking_idx`: btree (tenant_id, bk_booking_id) WHERE (bk_booking_id IS NOT NULL)
- index `booking_line_conf_uq`: UNIQUE btree (tenant_id, agency_supplier_id, conf_unique_key)
- index `booking_line_hold_idx`: btree (tenant_id, bk_hold_id) WHERE (bk_hold_id IS NOT NULL)
- index `booking_line_pkey` PRIMARY KEY: UNIQUE btree (booking_line_id)
- index `booking_line_status_idx`: btree (tenant_id, status, service_from) WHERE (deleted_at IS NULL)
- index `booking_line_supplier_idx`: btree (tenant_id, agency_supplier_id)
- index `booking_line_tenant_id_uq`: UNIQUE btree (tenant_id, booking_line_id)
- index `booking_line_trip_idx`: btree (tenant_id, trip_id)
- check `booking_line_aa_chk`: `CHECK ((((supplier_kind = 'aa'::text) OR ((aa_sub_status IS NULL) AND (bk_hold_id IS NULL) AND (bk_booking_id IS NULL) AND (num_nonnulls(aa_tour_source_id, aa_component_id, aa_component_kind, aa_currency, aa_pax, bk_quote_id, aa_price_hash, aa_quote_version, quote_valid_until, hold_expires_at, from_price, below_from_price, aa_decline_code, aa_result_code) = 0))) AND ((aa_sub_status IS NULL) OR (aa_sub_status = ANY (ARRAY['pending'::text, 'quoted'::text, 'sold_out'::text, 'held'::text, 'on_request'::text, 'declined'::text, 'expired'::text, 'released'::text, 'not_served'::text, 'failed'::text])))))`
- check `booking_line_aa_values_chk`: `CHECK ((((aa_tour_source_id IS NULL) OR (((char_length(aa_tour_source_id) >= 1) AND (char_length(aa_tour_source_id) <= 128)) AND (aa_tour_source_id !~ '[[:cntrl:]]'::text))) AND (COALESCE(aa_component_id, 'x'::text) ~ '^[A-Za-z0-9:_.-]{1,64}$'::text) AND ((aa_component_kind IS NULL) OR (aa_component_kind = ANY (ARRAY['trip_plan'::text, 'hotel_room'::text, 'transfer'::text, 'guide'::text, 'activity'::text, 'entrance'::text, 'meal'::text]))) AND (COALESCE(aa_currency, 'USD'::bpchar) ~ '^[A-Z]{3}$'::text) AND ((aa_pax IS NULL) OR (jsonb_typeof(aa_pax) = 'object'::text)) AND (COALESCE(bk_quote_id, 'x'::text) ~ '^[A-Za-z0-9:_.-]{1,64}$'::text) AND (COALESCE(aa_price_hash, repeat('0'::text, 64)) ~ '^[a-f0-9]{64}$'::text) AND ((aa_quote_version IS NULL) OR (aa_quote_version >= 1)) AND ((from_price IS NULL) OR (from_price >= (0)::numeric)) AND ((aa_decline_code IS NULL) OR (aa_decline_code = ANY (ARRAY['sold_out'::text, 'supplier_unavailable'::text, 'minimum_not_met'::text, 'other'::text]))) AND (COALESCE(aa_result_code, 'x'::text) ~ '^[a-z][a-z_]{0,39}$'::text)))`
- check `booking_line_cancelled_hidden_chk`: `CHECK (((status <> 'cancelled'::text) OR (NOT visible_to_travelers)))`
- check `booking_line_collect_chk`: `CHECK ((collect = ANY (ARRAY['agency'::text, 'on_arrival'::text])))`
- check `booking_line_confirm_class_chk`: `CHECK (((confirm_class IS NULL) OR (confirm_class = ANY (ARRAY['confirmed'::text, 'aa_on_request'::text, 'agency_booking'::text]))))`
- check `booking_line_confirmation_chk`: `CHECK (((confirmation_no IS NULL) OR (((char_length(btrim(confirmation_no)) >= 1) AND (char_length(btrim(confirmation_no)) <= 80)) AND (confirmation_no !~ '[[:cntrl:]]'::text))))`
- check `booking_line_confirmed_at_chk`: `CHECK (((status <> 'confirmed'::text) OR (confirmed_at IS NOT NULL)))`
- check `booking_line_dates_chk`: `CHECK (((service_to IS NULL) OR (service_from IS NULL) OR (service_to >= service_from)))`
- check `booking_line_refs_chk`: `CHECK (((COALESCE(bk_hold_id, 'x'::text) ~ '^[A-Za-z0-9:_.-]{1,80}$'::text) AND (COALESCE(bk_booking_id, 'x'::text) ~ '^[A-Za-z0-9:_.-]{1,80}$'::text) AND (COALESCE(departure_id, 'x'::text) ~ '^[A-Za-z0-9:_.-]{1,80}$'::text)))`
- check `booking_line_status_chk`: `CHECK ((status = ANY (ARRAY['planning'::text, 'confirmed'::text, 'cancelled'::text])))`
- check `booking_line_supplier_kind_chk`: `CHECK ((supplier_kind = ANY (ARRAY['aa'::text, 'agency'::text])))`
- check `booking_line_title_chk`: `CHECK ((((char_length(btrim(title)) >= 1) AND (char_length(btrim(title)) <= 200)) AND (title !~ '[[:cntrl:]]'::text)))`
- check `booking_line_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `booking_line_guard`: BEFORE INSERT OR DELETE OR UPDATE ON crm.booking_line FOR EACH ROW EXECUTE FUNCTION crm.guard_booking_line()
- trigger `booking_line_hold_guard`: BEFORE DELETE OR UPDATE ON crm.booking_line FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `booking_line_set_updated_at`: BEFORE UPDATE ON crm.booking_line FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `booking_line_status_transition`: BEFORE UPDATE OF status ON crm.booking_line FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.booking_line_money` (table, 80 kB)
```
booking_line_money_id uuid NN
tenant_id uuid NN
booking_line_id uuid NN
kind text NN
amount numeric(14,2) NN
currency character(3) NN
base_currency character(3)
amount_base numeric(14,2)
fx_rate numeric(20,10)
fx_rate_date date
fx_source text
fx_basis text
stale_days smallint
supersedes_id uuid
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `booking_line_money_line_idx`: btree (tenant_id, booking_line_id, kind)
- index `booking_line_money_pkey` PRIMARY KEY: UNIQUE btree (booking_line_money_id)
- index `booking_line_money_successor_uq`: UNIQUE btree (tenant_id, supersedes_id)
- index `booking_line_money_tenant_id_uq`: UNIQUE btree (tenant_id, booking_line_money_id)
- check `booking_line_money_amount_chk`: `CHECK (((amount >= (0)::numeric) AND (currency ~ '^[A-Z]{3}$'::text)))`
- check `booking_line_money_fx_chk`: `CHECK (((num_nulls(base_currency, amount_base, fx_rate, fx_rate_date, fx_source, fx_basis, stale_days) = ANY (ARRAY[0, 7])) AND ((base_currency IS NULL) OR ((base_currency ~ '^[A-Z]{3}$'::text) AND (fx_rate > (0)::numeric) AND (amount_base = round((amount * fx_rate), 2)) AND ((base_currency <> currency) OR (fx_rate = (1)::numeric)) AND (fx_source = ANY (ARRAY['aa_quote_lock'::text, 'platform_daily'::text, 'manual'::text])) AND (fx_basis = ANY (ARRAY['booking_date'::text, 'receipt_date'::text, 'quote_lock'::text])) AND ((stale_days >= 0) AND (stale_days <= 366))))))`
- check `booking_line_money_kind_chk`: `CHECK ((kind = ANY (ARRAY['cost'::text, 'sell'::text, 'commission_expected'::text])))`
- check `booking_line_money_supersedes_chk`: `CHECK (((supersedes_id IS NULL) OR (supersedes_id <> booking_line_money_id)))`
- grant `crm_app`: SELECT
- policy `booking_line_money_margin_roles` (RESTRICTIVE SELECT TO crm_app): USING `((COALESCE(current_setting('app.member_role'::text, true), ''::text) = ANY (ARRAY['owner'::text, 'agent'::text])) OR ((COALESCE(current_setting('app.member_role'::text, true), ''::text) = ''::text) AND (COALESCE(current_setting('app.actor'::text, true), ''::text) ~ '^(job|seed):'::text)))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `booking_line_money_append_only`: BEFORE DELETE OR UPDATE ON crm.booking_line_money FOR EACH ROW EXECUTE FUNCTION crm.ledger_append_only()
- trigger `booking_line_money_chain`: BEFORE INSERT ON crm.booking_line_money FOR EACH ROW EXECUTE FUNCTION crm.booking_line_money_chain()
- trigger `booking_line_money_no_truncate`: BEFORE TRUNCATE ON crm.booking_line_money FOR EACH STATEMENT EXECUTE FUNCTION crm.ledger_append_only()

### `crm.channel_account` (table, 80 kB)
```
channel_account_id uuid NN
tenant_id uuid NN
member_id uuid
kind text NN
address_enc bytea NN · pii:contact
address_bidx bytea NN
credential_id uuid
status text NN
last_token_check_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `channel_account_credential_idx`: btree (tenant_id, credential_id) WHERE (credential_id IS NOT NULL)
- index `channel_account_member_uq`: UNIQUE btree (tenant_id, member_id) NULLS NOT DISTINCT
- index `channel_account_pkey` PRIMARY KEY: UNIQUE btree (channel_account_id)
- index `channel_account_tenant_id_uq`: UNIQUE btree (tenant_id, channel_account_id)
- check `channel_account_address_chk`: `CHECK (((octet_length(address_enc) >= 30) AND (octet_length(address_bidx) = 16)))`
- check `channel_account_connected_chk`: `CHECK (((status <> 'connected'::text) OR (credential_id IS NOT NULL)))`
- check `channel_account_kind_chk`: `CHECK ((kind = ANY (ARRAY['gmail'::text, 'microsoft'::text, 'smtp'::text])))`
- check `channel_account_status_chk`: `CHECK ((status = ANY (ARRAY['connected'::text, 'needs_attention'::text, 'disconnected'::text])))`
- check `channel_account_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `channel_account_guard`: BEFORE INSERT OR UPDATE OF credential_id, member_id, kind ON crm.channel_account FOR EACH ROW EXECUTE FUNCTION crm.guard_channel_account()
- trigger `channel_account_set_updated_at`: BEFORE UPDATE ON crm.channel_account FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `channel_account_status_transition`: BEFORE UPDATE OF status ON crm.channel_account FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.client_link` (table, ~53 rows, 168 kB)
```
link_id uuid NN
tenant_id uuid NN
trip_id uuid NN
traveler_id uuid
purpose text NN
token_hash bytea NN · conf:credential
status text NN
expires_at timestamp with time zone NN
first_opened_at timestamp with time zone
submitted_at timestamp with time zone
revoked_at timestamp with time zone
reissued_from uuid
dispatch_id uuid
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `client_link_dispatch_idx`: btree (tenant_id, dispatch_id) WHERE (dispatch_id IS NOT NULL)
- index `client_link_pkey` PRIMARY KEY: UNIQUE btree (link_id)
- index `client_link_subject_uq`: UNIQUE btree (tenant_id, link_id, trip_id, traveler_id)
- index `client_link_tenant_id_uq`: UNIQUE btree (tenant_id, link_id)
- index `client_link_token_uq`: UNIQUE btree (token_hash)
- index `client_link_traveler_idx`: btree (traveler_id) WHERE (traveler_id IS NOT NULL)
- index `client_link_trip_idx`: btree (tenant_id, trip_id)
- check `client_link_dates_chk`: `CHECK ((((status <> 'opened'::text) OR (first_opened_at IS NOT NULL)) AND ((status <> 'submitted'::text) OR (submitted_at IS NOT NULL)) AND ((status = 'revoked'::text) = (revoked_at IS NOT NULL)) AND ((reissued_from IS NULL) OR (reissued_from <> link_id))))`
- check `client_link_expiry_chk`: `CHECK (((expires_at > created_at) AND (expires_at <= (created_at + '30 days'::interval))))`
- check `client_link_purpose_chk`: `CHECK (((purpose = ANY (ARRAY['stage2_form'::text, 'proposal'::text, 'portal'::text])) AND (traveler_id IS NOT NULL)))`
- check `client_link_status_chk`: `CHECK ((status = ANY (ARRAY['sent'::text, 'opened'::text, 'submitted'::text, 'expired'::text, 'revoked'::text])))`
- check `client_link_token_chk`: `CHECK ((octet_length(token_hash) = 32))`
- check `client_link_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `client_link_token_lookup` (PERMISSIVE SELECT TO crm_app): USING `((token_hash = decode(NULLIF(current_setting('app.client_link_hash'::text, true), ''::text), 'hex'::text)) AND (status = ANY (ARRAY['sent'::text, 'opened'::text, 'submitted'::text])) AND (expires_at > now()) AND (deleted_at IS NULL))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `client_link_hold_guard`: BEFORE DELETE OR UPDATE ON crm.client_link FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id')
- trigger `client_link_set_updated_at`: BEFORE UPDATE ON crm.client_link FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `client_link_status_transition`: BEFORE UPDATE OF status ON crm.client_link FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.consent` (table, ~106 rows, 96 kB)
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
- check `consent_notice_chk`: `CHECK (((notice_version IS NULL) OR (notice_version ~ '^[a-z0-9_.-]{1,40}$'::text)))`
- check `consent_purpose_chk`: `CHECK ((purpose = ANY (ARRAY['contact'::text, 'marketing'::text, 'health_data'::text, 'ops_release'::text, 'ai_processing'::text, 'terms'::text])))`
- check `consent_source_chk`: `CHECK ((source = ANY (ARRAY['form'::text, 'portal'::text, 'agent_recorded'::text, 'import'::text])))`
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `consent_append_only`: BEFORE DELETE OR UPDATE ON crm.consent FOR EACH ROW EXECUTE FUNCTION crm.erasable_append_only()
- trigger `consent_no_truncate`: BEFORE TRUNCATE ON crm.consent FOR EACH STATEMENT EXECUTE FUNCTION crm.erasable_append_only()

### `crm.conversation` (table, 96 kB)
```
conversation_id uuid NN
tenant_id uuid NN
traveler_id uuid
trip_id uuid
channel text NN
external_thread_ref_hash bytea
last_message_at timestamp with time zone NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `conversation_pkey` PRIMARY KEY: UNIQUE btree (conversation_id)
- index `conversation_tenant_id_uq`: UNIQUE btree (tenant_id, conversation_id)
- index `conversation_traveler_idx`: btree (traveler_id) WHERE (traveler_id IS NOT NULL)
- index `conversation_trip_idx`: btree (tenant_id, trip_id, last_message_at DESC) WHERE (trip_id IS NOT NULL)
- index `conversation_unmatched_idx`: btree (tenant_id, last_message_at DESC) WHERE ((traveler_id IS NULL) AND (trip_id IS NULL) AND (deleted_at IS NULL))
- check `conversation_channel_chk`: `CHECK ((channel = ANY (ARRAY['email'::text, 'whatsapp'::text, 'sms'::text, 'messenger'::text, 'ig'::text])))`
- check `conversation_thread_ref_chk`: `CHECK ((COALESCE(octet_length(external_thread_ref_hash), 32) = 32))`
- check `conversation_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `conversation_hold_guard`: BEFORE DELETE OR UPDATE ON crm.conversation FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id')
- trigger `conversation_set_updated_at`: BEFORE UPDATE ON crm.conversation FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.dispatch_attempt` (table, 64 kB)
```
attempt_id uuid NN
tenant_id uuid NN
dispatch_id uuid NN
job_attempt smallint NN
started_at timestamp with time zone NN
decided_at timestamp with time zone
outcome text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `dispatch_attempt_dispatch_idx`: btree (tenant_id, dispatch_id)
- index `dispatch_attempt_open_uq`: UNIQUE btree (dispatch_id) WHERE (decided_at IS NULL)
- index `dispatch_attempt_pkey` PRIMARY KEY: UNIQUE btree (attempt_id)
- check `dispatch_attempt_job_attempt_chk`: `CHECK (((job_attempt >= 1) AND (job_attempt <= 100)))`
- check `dispatch_attempt_outcome_chk`: `CHECK ((((decided_at IS NULL) = (outcome IS NULL)) AND ((outcome IS NULL) OR (outcome = ANY (ARRAY['sent'::text, 'held_reconnect'::text, 'no_message'::text, 'send_failed'::text, 'retry'::text, 'not_sent'::text, 'send_uncertain'::text]))) AND ((decided_at IS NULL) OR (decided_at >= started_at))))`
- check `dispatch_attempt_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT
- column grant `crm_app`: UPDATE (decided_at, outcome)
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `dispatch_attempt_decided_once`: BEFORE UPDATE ON crm.dispatch_attempt FOR EACH ROW EXECUTE FUNCTION crm.guard_dispatch_attempt()
- trigger `dispatch_attempt_set_updated_at`: BEFORE UPDATE ON crm.dispatch_attempt FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.dispatch_queue` (table, ~52 rows, 144 kB)
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
message_id uuid
```
- owner `crm_owner` · RLS on + FORCE
- index `dispatch_queue_due_idx`: btree (tenant_id, not_before) WHERE (status = 'queued'::text)
- index `dispatch_queue_message_idx`: btree (tenant_id, message_id) WHERE (message_id IS NOT NULL)
- index `dispatch_queue_pkey` PRIMARY KEY: UNIQUE btree (dispatch_id)
- index `dispatch_queue_tenant_id_uq`: UNIQUE btree (tenant_id, dispatch_id)
- index `dispatch_queue_traveler_idx`: btree (traveler_id)
- check `dispatch_queue_attempts_chk`: `CHECK (((attempts >= 0) AND (attempts <= 100)))`
- check `dispatch_queue_channel_chk`: `CHECK ((channel = ANY (ARRAY['email'::text, 'sms'::text, 'whatsapp'::text])))`
- check `dispatch_queue_gate_chk`: `CHECK ((((status = 'queued'::text) = (gate_result IS NULL)) AND ((gate_result IS NULL) OR (gate_result = ANY (ARRAY['sent'::text, 'archived'::text, 'traveler_trashed'::text, 'trip_trashed'::text, 'no_consent'::text, 'no_sender'::text, 'undone'::text, 'held_reconnect'::text, 'send_failed'::text, 'no_message'::text, 'send_uncertain'::text]))) AND ((status = 'queued'::text) = (decided_at IS NULL))))`
- check `dispatch_queue_origin_chk`: `CHECK ((origin = ANY (ARRAY['user_action'::text, 'workflow'::text, 'system'::text])))`
- check `dispatch_queue_purpose_chk`: `CHECK ((purpose = ANY (ARRAY['transactional'::text, 'marketing'::text])))`
- check `dispatch_queue_status_chk`: `CHECK ((status = ANY (ARRAY['queued'::text, 'held'::text, 'sent'::text, 'dropped'::text, 'cancelled'::text])))`
- check `dispatch_queue_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `dispatch_queue_hold_guard`: BEFORE DELETE OR UPDATE ON crm.dispatch_queue FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id')
- trigger `dispatch_queue_set_updated_at`: BEFORE UPDATE ON crm.dispatch_queue FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `dispatch_queue_status_transition`: BEFORE UPDATE OF status ON crm.dispatch_queue FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.document` (table, 72 kB)
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
- check `document_content_type_chk`: `CHECK ((content_type = ANY (ARRAY['application/pdf'::text, 'image/jpeg'::text, 'image/png'::text, 'image/webp'::text, 'image/heic'::text])))`
- check `document_filename_chk`: `CHECK ((octet_length(filename_enc) >= 30))`
- check `document_kind_chk`: `CHECK ((kind = ANY (ARRAY['passport_scan'::text, 'waiver_pdf'::text, 'terms_pdf'::text, 'ticket'::text, 'voucher'::text, 'invoice_pdf'::text, 'supplier_confirmation'::text, 'other'::text])))`
- check `document_s3_key_chk`: `CHECK ((s3_key = ((('tenants/'::text || (tenant_id)::text) || '/documents/'::text) || (document_id)::text)))`
- check `document_sha256_chk`: `CHECK ((octet_length(sha256) = 32))`
- check `document_size_chk`: `CHECK (((size_bytes >= 1) AND (size_bytes <= 10485760)))`
- check `document_subject_chk`: `CHECK (((trip_id IS NOT NULL) OR (traveler_id IS NOT NULL)))`
- check `document_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `document_uploader_chk`: `CHECK ((uploaded_by_kind = ANY (ARRAY['member'::text, 'traveler'::text, 'aa_booking'::text, 'mail'::text])))`
- check `document_write_only_chk`: `CHECK ((((kind <> 'passport_scan'::text) OR write_only) AND (NOT (write_only AND visible_to_travelers))))`
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
- check `erasure_request_actor_chk`: `CHECK (((requested_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text) AND ((confirmed_by IS NULL) OR (confirmed_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text))))`
- check `erasure_request_counts_chk`: `CHECK (((jsonb_typeof(dry_run_counts) = 'object'::text) AND (octet_length((dry_run_counts)::text) <= 4096) AND (jsonb_typeof(receipt) = 'object'::text) AND (octet_length((receipt)::text) <= 8192)))`
- check `erasure_request_done_chk`: `CHECK (((status = 'erased'::text) = (executed_at IS NOT NULL)))`
- check `erasure_request_export_chk`: `CHECK ((((export_object_key IS NULL) = (export_sha256 IS NULL)) AND ((export_object_key IS NULL) = (export_expires_at IS NULL)) AND ((export_object_key IS NULL) OR (export_object_key ~ '^exports/tenants/[0-9a-f-]{36}/[0-9a-f-]{36}\.jsonl\.enc$'::text)) AND ((export_sha256 IS NULL) OR (export_sha256 ~ '^[0-9a-f]{64}$'::text)) AND (NOT (export_waived AND (export_object_key IS NOT NULL)))))`
- check `erasure_request_failure_chk`: `CHECK (((failure_class IS NULL) OR (failure_class ~ '^[A-Za-z][A-Za-z0-9_]{0,63}$'::text)))`
- check `erasure_request_purpose_chk`: `CHECK (((purpose = ANY (ARRAY['offboard'::text, 'export_only'::text])) AND ((purpose = 'offboard'::text) OR (scope = 'tenant'::text))))`
- check `erasure_request_scope_chk`: `CHECK (((scope = ANY (ARRAY['traveler'::text, 'tenant'::text])) AND ((scope <> 'tenant'::text) OR (subject_id = tenant_id))))`
- check `erasure_request_status_chk`: `CHECK ((status = ANY (ARRAY['requested'::text, 'export_ready'::text, 'erasing'::text, 'erased'::text, 'cancelled'::text, 'failed'::text])))`
- check `erasure_request_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
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
- check `form_definition_schema_chk`: `CHECK (((jsonb_typeof(schema) = 'object'::text) AND (octet_length((schema)::text) <= 65536)))`
- check `form_definition_schema_key_chk`: `CHECK ((schema_key ~ '^[a-z][a-z0-9_.]{0,39}$'::text))`
- check `form_definition_stage_chk`: `CHECK ((stage = ANY (ARRAY['s1'::text, 's2'::text, 's3'::text])))`
- check `form_definition_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `form_definition_version_chk`: `CHECK (((version >= 1) AND (version <= 100000)))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `form_definition_set_updated_at`: BEFORE UPDATE ON crm.form_definition FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.form_submission` (table, ~90 rows, 248 kB)
```
submission_id uuid NN
tenant_id uuid NN
intake_form_id uuid
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
client_link_id uuid
```
- owner `crm_owner` · RLS on + FORCE
- index `form_submission_client_link_idx`: btree (tenant_id, client_link_id) WHERE (client_link_id IS NOT NULL)
- index `form_submission_idempotency_uq`: UNIQUE btree (tenant_id, idempotency_key)
- index `form_submission_pkey` PRIMARY KEY: UNIQUE btree (submission_id)
- index `form_submission_redact_idx`: btree (redact_after) WHERE (payload_redacted_at IS NULL)
- index `form_submission_tenant_id_uq`: UNIQUE btree (tenant_id, submission_id)
- index `form_submission_trip_idx`: btree (trip_id) WHERE (trip_id IS NOT NULL)
- check `form_submission_dropped_chk`: `CHECK (((hidden_answers_dropped >= 0) AND (hidden_answers_dropped <= 1000)))`
- check `form_submission_failure_chk`: `CHECK (((failure_class IS NULL) OR (failure_class ~ '^[A-Za-z][A-Za-z0-9_]{0,63}$'::text)))`
- check `form_submission_idempotency_chk`: `CHECK ((idempotency_key ~ '^[A-Za-z0-9:_-]{8,80}$'::text))`
- check `form_submission_outcome_chk`: `CHECK ((((status = 'processed'::text) = (outcome IS NOT NULL)) AND ((outcome IS NULL) OR (outcome = ANY (ARRAY['created'::text, 'attached'::text, 'applied'::text])))))`
- check `form_submission_payload_chk`: `CHECK ((((payload_enc IS NOT NULL) AND (octet_length(payload_enc) >= 30)) OR (payload_redacted_at IS NOT NULL)))`
- check `form_submission_schema_key_chk`: `CHECK ((schema_key ~ '^[a-z][a-z0-9_.]{0,39}$'::text))`
- check `form_submission_source_chk`: `CHECK ((((stage <> 's1'::text) OR (intake_form_id IS NOT NULL)) AND ((client_link_id IS NULL) OR ((stage <> 's1'::text) AND (trip_id IS NOT NULL) AND (traveler_id IS NOT NULL)))))`
- check `form_submission_stage_chk`: `CHECK ((stage = ANY (ARRAY['s1'::text, 's2'::text, 's3'::text])))`
- check `form_submission_status_chk`: `CHECK ((status = ANY (ARRAY['received'::text, 'processed'::text, 'failed'::text])))`
- check `form_submission_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `form_submission_hold_guard`: BEFORE DELETE OR UPDATE ON crm.form_submission FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id', 'payload_enc')
- trigger `form_submission_set_updated_at`: BEFORE UPDATE ON crm.form_submission FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `form_submission_status_transition`: BEFORE UPDATE OF status ON crm.form_submission FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.fx_rate_override` (table, 24 kB)
```
fx_rate_override_id uuid NN
tenant_id uuid NN
rate_date date NN
base character(3) NN
quote character(3) NN
rate numeric(20,10) NN
set_by uuid NN
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `fx_rate_override_pair_idx`: btree (tenant_id, base, quote, rate_date DESC, created_at DESC)
- index `fx_rate_override_pkey` PRIMARY KEY: UNIQUE btree (fx_rate_override_id)
- check `fx_rate_override_pair_chk`: `CHECK (((base ~ '^[A-Z]{3}$'::text) AND (quote ~ '^[A-Z]{3}$'::text) AND (base <> quote)))`
- check `fx_rate_override_rate_chk`: `CHECK ((rate > (0)::numeric))`
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `fx_rate_override_append_only`: BEFORE DELETE OR UPDATE ON crm.fx_rate_override FOR EACH ROW EXECUTE FUNCTION crm.ledger_append_only()
- trigger `fx_rate_override_no_truncate`: BEFORE TRUNCATE ON crm.fx_rate_override FOR EACH STATEMENT EXECUTE FUNCTION crm.ledger_append_only()

### `crm.fx_rate_platform` (table, ~126 rows, 80 kB)
```
rate_date date NN
base character(3) NN
quote character(3) NN
source text NN
rate numeric(20,10) NN
fetched_at timestamp with time zone NN
```
- owner `crm_owner`
- index `fx_rate_platform_pair_idx`: btree (base, quote, rate_date DESC)
- index `fx_rate_platform_pkey` PRIMARY KEY: UNIQUE btree (rate_date, base, quote, source)
- check `fx_rate_platform_pair_chk`: `CHECK (((base ~ '^[A-Z]{3}$'::text) AND (quote ~ '^[A-Z]{3}$'::text) AND (base <> quote)))`
- check `fx_rate_platform_rate_chk`: `CHECK ((rate > (0)::numeric))`
- check `fx_rate_platform_source_chk`: `CHECK ((source = ANY (ARRAY['ecb'::text, 'exchangerate_api'::text, 'fawazahmed0'::text, 'sbv'::text, 'booking_b2b'::text, 'manual_aa'::text, 'synthetic'::text])))`
- grant `crm_app`: INSERT, SELECT

### `crm.inbox_events` (table, 48 kB)
```
id uuid NN
tenant_id uuid NN
source text NN
contract text NN
idempotency_key text NN
event_type text
outcome text NN
reason_code text NN
received_at timestamp with time zone NN
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `inbox_events_key_uq`: UNIQUE btree (tenant_id, source, contract, idempotency_key)
- index `inbox_events_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `inbox_events_values_chk`: `CHECK (((source = 'booking'::text) AND (contract = 'booking.b2b.v1'::text) AND (idempotency_key ~ '^[A-Za-z0-9:_.-]{1,64}$'::text) AND (COALESCE(event_type, 'x'::text) ~ '^[a-z][a-z_.]{0,39}$'::text) AND (outcome = ANY (ARRAY['applied'::text, 'ignored'::text, 'rejected'::text])) AND (reason_code ~ '^[a-z][a-z_]{0,39}$'::text)))`
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `inbox_events_append_only`: BEFORE DELETE OR UPDATE ON crm.inbox_events FOR EACH ROW EXECUTE FUNCTION crm.ledger_append_only()
- trigger `inbox_events_no_truncate`: BEFORE TRUNCATE ON crm.inbox_events FOR EACH STATEMENT EXECUTE FUNCTION crm.ledger_append_only()

### `crm.ingest_address` (table, 64 kB)
```
ingest_address_id uuid NN
tenant_id uuid NN
local_part text NN
active boolean NN
forwarding_confirmation_enc bytea · conf:credential
forwarding_code_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `ingest_address_active_uq`: UNIQUE btree (tenant_id) WHERE (active AND (deleted_at IS NULL))
- index `ingest_address_local_part_uq`: UNIQUE btree (local_part)
- index `ingest_address_pkey` PRIMARY KEY: UNIQUE btree (ingest_address_id)
- check `ingest_address_code_chk`: `CHECK (((COALESCE(octet_length(forwarding_confirmation_enc), 30) >= 30) AND ((forwarding_confirmation_enc IS NULL) = (forwarding_code_at IS NULL))))`
- check `ingest_address_local_part_chk`: `CHECK ((local_part ~ '^[a-z0-9][a-z0-9-]{6,62}[a-z0-9]$'::text))`
- check `ingest_address_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `ingest_address_lookup` (PERMISSIVE SELECT TO crm_app): USING `((local_part = NULLIF(current_setting('app.ingest_local_part'::text, true), ''::text)) AND active AND (deleted_at IS NULL))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `ingest_address_set_updated_at`: BEFORE UPDATE ON crm.ingest_address FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

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
- check `intake_form_honeypot_chk`: `CHECK ((honeypot_field ~ '^[a-z][a-z_]{2,30}$'::text))`
- check `intake_form_label_chk`: `CHECK ((((length(btrim(label)) >= 1) AND (length(btrim(label)) <= 80)) AND (label = btrim(label))))`
- check `intake_form_lead_source_chk`: `CHECK ((lead_source ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `intake_form_origins_chk`: `CHECK (((cardinality(allowed_origins) <= 10) AND (array_to_string(allowed_origins, ' '::text, '!'::text) ~ '^(https://[a-z0-9.-]+(:[0-9]{1,5})?( |$))*$'::text)))`
- check `intake_form_privacy_url_chk`: `CHECK (((privacy_notice_url IS NULL) OR ((privacy_notice_url ~ '^https://[^\s]+$'::text) AND (length(privacy_notice_url) <= 500))))`
- check `intake_form_public_key_chk`: `CHECK ((public_key ~ '^[A-Za-z0-9_-]{20,64}$'::text))`
- check `intake_form_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'disabled'::text])))`
- check `intake_form_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `intake_form_public_lookup` (PERMISSIVE SELECT TO crm_app): USING `((status = 'active'::text) AND (deleted_at IS NULL) AND (public_key = NULLIF(current_setting('app.intake_key'::text, true), ''::text)))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `intake_form_set_updated_at`: BEFORE UPDATE ON crm.intake_form FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `intake_form_status_transition`: BEFORE UPDATE OF status ON crm.intake_form FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.integration_credential` (table, 80 kB)
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
member_id uuid
```
- owner `crm_owner` · RLS on + FORCE
- index `integration_credential_member_idx`: btree (tenant_id, member_id) WHERE (member_id IS NOT NULL)
- index `integration_credential_pkey` PRIMARY KEY: UNIQUE btree (integration_credential_id)
- index `integration_credential_provider_member_uq`: UNIQUE btree (tenant_id, provider, member_id) NULLS NOT DISTINCT
- index `integration_credential_tenant_id_uq`: UNIQUE btree (tenant_id, integration_credential_id)
- check `integration_credential_account_ref_chk`: `CHECK (((account_ref IS NULL) OR ((length(account_ref) >= 1) AND (length(account_ref) <= 320))))`
- check `integration_credential_failure_chk`: `CHECK (((failure_class IS NULL) OR (failure_class = ANY (ARRAY['auth_revoked'::text, 'permission_missing'::text, 'vendor_rejected'::text, 'rate_limited'::text, 'unreachable'::text]))))`
- check `integration_credential_failure_state_chk`: `CHECK (((failure_class IS NULL) OR (status = ANY (ARRAY['needs_attention'::text, 'disconnected'::text]))))`
- check `integration_credential_provider_chk`: `CHECK ((provider = ANY (ARRAY['twilio'::text, 'stripe_key'::text, 'stripe_webhook_secret'::text, 'google'::text, 'microsoft'::text, 'smtp'::text, 'esign'::text])))`
- check `integration_credential_secret_chk`: `CHECK (((octet_length(secret_enc) >= 30) AND (octet_length(secret_enc) <= 16384)))`
- check `integration_credential_status_chk`: `CHECK ((status = ANY (ARRAY['not_set_up'::text, 'connected'::text, 'needs_attention'::text, 'disconnected'::text])))`
- check `integration_credential_test_result_chk`: `CHECK (((last_test_result IS NULL) OR (last_test_result = ANY (ARRAY['ok'::text, 'failed'::text]))))`
- check `integration_credential_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `integration_credential_set_updated_at`: BEFORE UPDATE ON crm.integration_credential FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `integration_credential_status_transition`: BEFORE UPDATE OF status ON crm.integration_credential FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.job` (table, ~7988 rows, 5.9 MB)
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
- check `job_attempts_chk`: `CHECK (((attempt >= 0) AND (max_attempts >= 1)))`
- check `job_kind_chk`: `CHECK ((kind ~ '^crm_[a-z0-9_]+$'::text))`
- check `job_lease_chk`: `CHECK (((status <> 'running'::text) OR ((locked_by IS NOT NULL) AND (locked_until IS NOT NULL))))`
- check `job_status_chk`: `CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text, 'cancelled'::text])))`
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
- check `legal_hold_actor_chk`: `CHECK (((placed_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text) AND ((released_by IS NULL) OR (released_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text))))`
- check `legal_hold_never_trashed_chk`: `CHECK (((deleted_at IS NULL) AND (deleted_by IS NULL) AND (purge_after IS NULL)))`
- check `legal_hold_reason_chk`: `CHECK ((reason_code = ANY (ARRAY['litigation'::text, 'regulator_request'::text, 'dispute'::text, 'insurance_claim'::text, 'other'::text])))`
- check `legal_hold_release_chk`: `CHECK ((((status = 'released'::text) = (released_at IS NOT NULL)) AND ((released_at IS NULL) = (released_by IS NULL))))`
- check `legal_hold_scope_chk`: `CHECK (((scope = ANY (ARRAY['tenant'::text, 'trip'::text, 'traveler'::text])) AND ((scope = 'tenant'::text) = (subject_id IS NULL))))`
- check `legal_hold_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'released'::text])))`
- check `legal_hold_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `legal_hold_guard`: BEFORE UPDATE ON crm.legal_hold FOR EACH ROW EXECUTE FUNCTION crm.guard_legal_hold()
- trigger `legal_hold_set_updated_at`: BEFORE UPDATE ON crm.legal_hold FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `legal_hold_status_transition`: BEFORE UPDATE OF status ON crm.legal_hold FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.lifecycle_run` (table, 48 kB)
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
- check `lifecycle_run_counts_chk`: `CHECK (((jsonb_typeof(counts) = 'object'::text) AND (octet_length((counts)::text) <= 4096) AND (NOT jsonb_path_exists(counts, '$.*?(@.type() != "number")'::jsonpath))))`
- check `lifecycle_run_kind_chk`: `CHECK ((kind ~ '^crm_[a-z0-9_]{1,40}$'::text))`
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
- check `llm_call_cost_chk`: `CHECK ((cost_usd_est >= (0)::numeric))`
- check `llm_call_error_chk`: `CHECK (((error_class IS NULL) OR (error_class ~ '^[A-Za-z][A-Za-z0-9_]{0,63}$'::text)))`
- check `llm_call_model_chk`: `CHECK ((model ~ '^[A-Za-z0-9._:/-]{1,120}$'::text))`
- check `llm_call_outcome_chk`: `CHECK ((outcome = ANY (ARRAY['ok'::text, 'refused'::text, 'error'::text])))`
- check `llm_call_provider_chk`: `CHECK ((provider ~ '^[a-z][a-z0-9_]{0,30}$'::text))`
- check `llm_call_receipt_chk`: `CHECK (((jsonb_typeof(scrub_receipt) = 'object'::text) AND (octet_length((scrub_receipt)::text) <= 2048)))`
- check `llm_call_receipt_keys_chk`: `CHECK ((((scrub_receipt - ARRAY['scrubber'::text, 'detector'::text, 'entities'::text, 'counts'::text, 'passes'::text, 'known_persons'::text]) = '{}'::jsonb) AND ((NOT (scrub_receipt ? 'scrubber'::text)) OR ((jsonb_typeof((scrub_receipt -> 'scrubber'::text)) = 'string'::text) AND ((scrub_receipt ->> 'scrubber'::text) ~ '^[a-z0-9][a-z0-9.-]{0,19}$'::text))) AND ((NOT (scrub_receipt ? 'detector'::text)) OR ((jsonb_typeof((scrub_receipt -> 'detector'::text)) = 'string'::text) AND ((scrub_receipt ->> 'detector'::text) ~ '^[a-z0-9][a-z0-9_.-]{0,39}$'::text))) AND ((NOT (scrub_receipt ? 'entities'::text)) OR (jsonb_typeof((scrub_receipt -> 'entities'::text)) = 'number'::text)) AND ((NOT (scrub_receipt ? 'known_persons'::text)) OR (jsonb_typeof((scrub_receipt -> 'known_persons'::text)) = 'number'::text)) AND ((NOT (scrub_receipt ? 'counts'::text)) OR ((jsonb_typeof((scrub_receipt -> 'counts'::text)) = 'object'::text) AND (NOT jsonb_path_exists((scrub_receipt -> 'counts'::text), 'strict $.keyvalue()?(!(@."key" like_regex "^[A-Z][A-Z_]{1,23}$") || @."value".type() != "number")'::jsonpath)))) AND ((NOT (scrub_receipt ? 'passes'::text)) OR ((jsonb_typeof((scrub_receipt -> 'passes'::text)) = 'object'::text) AND (((scrub_receipt -> 'passes'::text) - ARRAY['known'::text, 'regex'::text, 'detector'::text]) = '{}'::jsonb) AND (NOT jsonb_path_exists((scrub_receipt -> 'passes'::text), 'strict $.keyvalue()?(@."value".type() != "number")'::jsonpath))))))`
- check `llm_call_refusal_chk`: `CHECK ((((outcome = 'refused'::text) = (refusal_code IS NOT NULL)) AND ((refusal_code IS NULL) OR (refusal_code ~ '^[a-z][a-z0-9_]{0,39}$'::text))))`
- check `llm_call_role_chk`: `CHECK ((role = ANY (ARRAY['writer'::text, 'judge'::text, 'validate'::text])))`
- check `llm_call_stage_chk`: `CHECK ((stage ~ '^crm_[a-z0-9_]{1,40}$'::text))`
- check `llm_call_tokens_chk`: `CHECK (((input_tokens >= 0) AND (output_tokens >= 0) AND (latency_ms >= 0)))`
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
- check `llm_usage_daily_counts_chk`: `CHECK (((calls >= 0) AND (failed_calls >= 0) AND (failed_calls <= calls) AND (input_tokens >= 0) AND (output_tokens >= 0) AND (cost_usd >= (0)::numeric)))`
- check `llm_usage_daily_model_chk`: `CHECK ((model ~ '^[A-Za-z0-9._:/-]{1,120}$'::text))`
- check `llm_usage_daily_stage_chk`: `CHECK ((stage ~ '^crm_[a-z0-9_]{1,40}$'::text))`
- grant `crm_app`: INSERT, SELECT, UPDATE

### `crm.mail_import` (table, 32 kB)
```
mail_import_id uuid NN
tenant_id uuid NN
member_id uuid NN
source_kind text NN
size_bytes bigint NN
status text NN
total_count integer NN
imported_count integer NN
duplicate_count integer NN
skipped_count integer NN
failed_count integer NN
error_code text
finished_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `mail_import_pkey` PRIMARY KEY: UNIQUE btree (mail_import_id)
- check `mail_import_counts_chk`: `CHECK (((total_count >= 0) AND (imported_count >= 0) AND (duplicate_count >= 0) AND (skipped_count >= 0) AND (failed_count >= 0)))`
- check `mail_import_error_chk`: `CHECK ((((error_code IS NULL) OR (error_code ~ '^[a-z][a-z0-9_]{1,40}$'::text)) AND ((error_code IS NULL) OR (status = 'failed'::text))))`
- check `mail_import_finished_chk`: `CHECK (((status = ANY (ARRAY['done'::text, 'failed'::text])) = (finished_at IS NOT NULL)))`
- check `mail_import_size_chk`: `CHECK (((size_bytes >= 1) AND (size_bytes <= 26214400)))`
- check `mail_import_source_chk`: `CHECK ((source_kind = ANY (ARRAY['mbox'::text, 'csv'::text])))`
- check `mail_import_status_chk`: `CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'done'::text, 'failed'::text])))`
- check `mail_import_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `mail_import_set_updated_at`: BEFORE UPDATE ON crm.mail_import FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `mail_import_status_transition`: BEFORE UPDATE OF status ON crm.mail_import FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.meeting_slot` (table, 96 kB)
```
slot_id uuid NN
tenant_id uuid NN
trip_id uuid
traveler_id uuid
starts_at timestamp with time zone NN
duration_min smallint NN
status text NN
source text NN
form_submission_id uuid
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `meeting_slot_live_start_uq`: UNIQUE btree (tenant_id, starts_at) WHERE ((status = ANY (ARRAY['requested'::text, 'confirmed'::text])) AND (deleted_at IS NULL))
- index `meeting_slot_pkey` PRIMARY KEY: UNIQUE btree (slot_id)
- index `meeting_slot_submission_idx`: btree (tenant_id, form_submission_id) WHERE (form_submission_id IS NOT NULL)
- index `meeting_slot_traveler_idx`: btree (traveler_id) WHERE (traveler_id IS NOT NULL)
- index `meeting_slot_trip_idx`: btree (tenant_id, trip_id) WHERE (trip_id IS NOT NULL)
- check `meeting_slot_duration_chk`: `CHECK (((duration_min >= 10) AND (duration_min <= 240)))`
- check `meeting_slot_source_chk`: `CHECK (((source = ANY (ARRAY['form'::text, 'agent'::text])) AND ((source = 'form'::text) = (form_submission_id IS NOT NULL))))`
- check `meeting_slot_status_chk`: `CHECK ((status = ANY (ARRAY['requested'::text, 'confirmed'::text, 'cancelled'::text, 'done'::text])))`
- check `meeting_slot_subject_chk`: `CHECK (((trip_id IS NOT NULL) OR (traveler_id IS NOT NULL)))`
- check `meeting_slot_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `meeting_slot_hold_guard`: BEFORE DELETE OR UPDATE ON crm.meeting_slot FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id')
- trigger `meeting_slot_set_updated_at`: BEFORE UPDATE ON crm.meeting_slot FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `meeting_slot_status_transition`: BEFORE UPDATE OF status ON crm.meeting_slot FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

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
- check `member_iss_chk`: `CHECK ((cognito_iss ~ '^https://[^/]+/[^/]+$'::text))`
- check `member_role_chk`: `CHECK ((role = ANY (ARRAY['owner'::text, 'agent'::text, 'assistant'::text])))`
- check `member_status_chk`: `CHECK ((status = ANY (ARRAY['invited'::text, 'active'::text, 'disabled'::text])))`
- check `member_sub_chk`: `CHECK (((length(cognito_sub) >= 1) AND (length(cognito_sub) <= 128)))`
- check `member_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
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
- check `member_invitation_accept_chk`: `CHECK (((status = 'accepted'::text) = ((accepted_at IS NOT NULL) AND (member_id IS NOT NULL))))`
- check `member_invitation_bidx_chk`: `CHECK (((octet_length(email_bidx) >= 8) AND (octet_length(email_bidx) <= 64)))`
- check `member_invitation_claim_chk`: `CHECK ((((status = 'pending'::text) AND (cognito_sub IS NULL) AND (claimed_at IS NULL)) OR ((status = ANY (ARRAY['claimed'::text, 'accepted'::text])) AND (cognito_sub IS NOT NULL) AND (claimed_at IS NOT NULL)) OR (status = ANY (ARRAY['revoked'::text, 'expired'::text]))))`
- check `member_invitation_expiry_chk`: `CHECK (((expires_at > created_at) AND (expires_at <= (created_at + '30 days'::interval))))`
- check `member_invitation_identity_chk`: `CHECK ((((cognito_iss IS NULL) = (cognito_sub IS NULL)) AND ((cognito_iss IS NULL) OR ((cognito_iss ~ '^https://[^/]+/[^/]+$'::text) AND ((length(cognito_sub) >= 1) AND (length(cognito_sub) <= 128))))))`
- check `member_invitation_role_chk`: `CHECK ((role = ANY (ARRAY['owner'::text, 'agent'::text, 'assistant'::text])))`
- check `member_invitation_status_chk`: `CHECK ((status = ANY (ARRAY['pending'::text, 'claimed'::text, 'accepted'::text, 'revoked'::text, 'expired'::text])))`
- check `member_invitation_token_chk`: `CHECK ((octet_length(token_hash) = 32))`
- check `member_invitation_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `invitation_token_lookup` (PERMISSIVE SELECT TO crm_app): USING `(token_hash = decode(NULLIF(current_setting('app.invite_token_hash'::text, true), ''::text), 'hex'::text))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `member_invitation_guard_write`: BEFORE INSERT OR UPDATE ON crm.member_invitation FOR EACH ROW EXECUTE FUNCTION crm.guard_invitation_write()
- trigger `member_invitation_set_updated_at`: BEFORE UPDATE ON crm.member_invitation FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `member_invitation_status_transition`: BEFORE UPDATE OF status ON crm.member_invitation FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.membership_feed_state` (table, ~1 rows, 64 kB)
```
singleton boolean NN
feed_cursor text
last_ok_at timestamp with time zone
last_error_class text
last_error_at timestamp with time zone
failures integer NN
updated_at timestamp with time zone NN
```
- owner `crm_owner`
- index `membership_feed_state_pkey` PRIMARY KEY: UNIQUE btree (singleton)
- check `membership_feed_state_cursor_chk`: `CHECK (((feed_cursor IS NULL) OR (feed_cursor ~ '^[!-~]{1,200}$'::text)))`
- check `membership_feed_state_error_chk`: `CHECK ((((last_error_class IS NULL) = (last_error_at IS NULL)) AND ((last_error_class IS NULL) OR (last_error_class ~ '^[a-z][a-z0-9_]{0,39}$'::text))))`
- check `membership_feed_state_failures_chk`: `CHECK (((failures >= 0) AND (failures <= 1000000)))`
- check `membership_feed_state_singleton_chk`: `CHECK (singleton)`
- grant `crm_app`: SELECT, UPDATE
- trigger `membership_feed_state_set_updated_at`: BEFORE UPDATE ON crm.membership_feed_state FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.membership_inbox` (table, 48 kB)
```
event_id uuid NN
tenant_id uuid NN
event_type text
outcome text NN
reason_code text NN
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `membership_inbox_pkey` PRIMARY KEY: UNIQUE btree (event_id)
- index `membership_inbox_tenant_idx`: btree (tenant_id, created_at DESC)
- check `membership_inbox_outcome_chk`: `CHECK ((outcome = ANY (ARRAY['applied'::text, 'ignored'::text, 'rejected'::text])))`
- check `membership_inbox_reason_chk`: `CHECK ((reason_code ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `membership_inbox_type_chk`: `CHECK (COALESCE((event_type = ANY (ARRAY['tenant.created'::text, 'tenant.locked'::text, 'tenant.unlocked'::text, 'tenant.deleted'::text, 'membership.invited'::text, 'membership.activated'::text, 'membership.role_changed'::text, 'membership.removed'::text])), (outcome = 'rejected'::text)))`
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `membership_inbox_append_only`: BEFORE DELETE OR UPDATE ON crm.membership_inbox FOR EACH ROW EXECUTE FUNCTION crm.membership_inbox_append_only()
- trigger `membership_inbox_no_truncate`: BEFORE TRUNCATE ON crm.membership_inbox FOR EACH STATEMENT EXECUTE FUNCTION crm.membership_inbox_append_only()

### `crm.message` (table, 224 kB)
```
message_id uuid NN
tenant_id uuid NN
conversation_id uuid NN
direction text NN
channel text NN
status text NN
sender_kind text
channel_account_id uuid
author_member_id uuid
subject_enc bytea · pii:free_text
body_enc bytea · pii:free_text
body_html_enc bytea · pii:free_text
from_enc bytea · pii:contact
from_bidx bytea
to_enc bytea · pii:contact
attachments uuid[] NN
attachment_notes text[] NN
rfc_message_id_hash bytea
rfc_message_id_enc bytea · pii:contact
in_reply_to_hash bytea
references_hashes bytea[] NN
external_id text
match_method text
failure_code text
imported boolean NN
occurred_at timestamp with time zone NN
sent_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `message_conversation_idx`: btree (tenant_id, conversation_id, occurred_at)
- index `message_external_id_uq`: UNIQUE btree (tenant_id, channel, external_id)
- index `message_from_idx`: btree (tenant_id, from_bidx) WHERE (from_bidx IS NOT NULL)
- index `message_held_idx`: btree (tenant_id, channel_account_id) WHERE (status = 'held_reconnect'::text)
- index `message_pkey` PRIMARY KEY: UNIQUE btree (message_id)
- index `message_rfc_id_uq`: UNIQUE btree (tenant_id, rfc_message_id_hash)
- index `message_tenant_id_uq`: UNIQUE btree (tenant_id, message_id)
- check `message_attachments_chk`: `CHECK (((cardinality(attachments) <= 50) AND (array_position(attachments, NULL::uuid) IS NULL) AND (cardinality(attachment_notes) <= 50) AND (array_to_string(attachment_notes, ','::text) ~ '^([a-z][a-z0-9_]{1,40}(,[a-z][a-z0-9_]{1,40})*)?$'::text)))`
- check `message_bidx_chk`: `CHECK ((COALESCE(octet_length(from_bidx), 16) = 16))`
- check `message_channel_chk`: `CHECK ((channel = ANY (ARRAY['email'::text, 'whatsapp'::text, 'sms'::text])))`
- check `message_direction_chk`: `CHECK ((direction = ANY (ARRAY['in'::text, 'out'::text])))`
- check `message_enc_chk`: `CHECK (((COALESCE(octet_length(subject_enc), 30) >= 30) AND (COALESCE(octet_length(body_enc), 30) >= 30) AND (COALESCE(octet_length(body_html_enc), 30) >= 30) AND (COALESCE(octet_length(from_enc), 30) >= 30) AND (COALESCE(octet_length(to_enc), 30) >= 30) AND (COALESCE(octet_length(rfc_message_id_enc), 30) >= 30)))`
- check `message_external_id_chk`: `CHECK (((external_id IS NULL) OR (((char_length(external_id) >= 1) AND (char_length(external_id) <= 200)) AND (external_id !~ '[[:cntrl:][:space:]]'::text))))`
- check `message_failure_chk`: `CHECK (((failure_code IS NULL) OR ((failure_code ~ '^[a-z][a-z0-9_]{1,40}$'::text) AND (status = ANY (ARRAY['held_reconnect'::text, 'failed'::text])))))`
- check `message_hash_chk`: `CHECK (((COALESCE(octet_length(rfc_message_id_hash), 32) = 32) AND (COALESCE(octet_length(in_reply_to_hash), 32) = 32) AND (cardinality(references_hashes) <= 100) AND (array_position(references_hashes, NULL::bytea) IS NULL)))`
- check `message_match_chk`: `CHECK (((match_method IS NULL) OR (match_method = ANY (ARRAY['reply_header'::text, 'trip_token'::text, 'sender'::text, 'manual'::text, 'unmatched'::text, 'compose'::text]))))`
- check `message_sender_kind_chk`: `CHECK ((((direction = 'in'::text) AND (sender_kind IS NULL)) OR ((direction = 'out'::text) AND (sender_kind IS NOT NULL) AND (sender_kind = ANY (ARRAY['agency_mailbox'::text, 'system'::text])))))`
- check `message_sent_chk`: `CHECK (((status = 'sent'::text) = (sent_at IS NOT NULL)))`
- check `message_status_chk`: `CHECK (((status = ANY (ARRAY['received'::text, 'draft_autosaved'::text, 'queued'::text, 'held_reconnect'::text, 'sent'::text, 'failed'::text])) AND ((direction = 'in'::text) = (status = 'received'::text))))`
- check `message_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `message_guard`: BEFORE DELETE OR UPDATE ON crm.message FOR EACH ROW EXECUTE FUNCTION crm.guard_message()
- trigger `message_set_updated_at`: BEFORE UPDATE ON crm.message FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `message_status_transition`: BEFORE UPDATE OF status ON crm.message FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.message_template` (table, 80 kB)
```
message_template_id uuid NN
tenant_id uuid NN
locale text NN
title text NN
body_enc bytea NN · pii:free_text
source text NN
aa_group_key text
aa_content_id uuid
aa_version integer
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `message_template_aa_uq`: UNIQUE btree (tenant_id, aa_group_key, locale) WHERE (aa_group_key IS NOT NULL)
- index `message_template_pkey` PRIMARY KEY: UNIQUE btree (message_template_id)
- index `message_template_tenant_id_uq`: UNIQUE btree (tenant_id, message_template_id)
- index `message_template_tenant_idx`: btree (tenant_id, locale, title) WHERE (deleted_at IS NULL)
- check `message_template_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `message_template_values_chk`: `CHECK (((locale = ANY (ARRAY['en'::text, 'vi'::text])) AND ((char_length(btrim(title)) >= 1) AND (char_length(btrim(title)) <= 120)) AND (title !~ '[[:cntrl:]]'::text) AND ((octet_length(body_enc) >= 30) AND (octet_length(body_enc) <= 65536)) AND (source = ANY (ARRAY['agency'::text, 'aa_starter'::text])) AND
CASE source
    WHEN 'aa_starter'::text THEN ((aa_group_key ~ '^[a-z0-9][a-z0-9-]{1,79}$'::text) AND (aa_content_id IS NOT NULL) AND (aa_version >= 1))
    ELSE (num_nonnulls(aa_group_key, aa_content_id, aa_version) = 0)
END))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `message_template_set_updated_at`: BEFORE UPDATE ON crm.message_template FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.metric_event` (table, 96 kB)
```
metric_event_id uuid NN
tenant_id uuid NN
trip_id uuid NN
proposal_id uuid
name text NN
detail jsonb NN
bell_member_id uuid
seen_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `metric_event_bell_idx`: btree (tenant_id, bell_member_id, created_at DESC) WHERE ((bell_member_id IS NOT NULL) AND (seen_at IS NULL))
- index `metric_event_pkey` PRIMARY KEY: UNIQUE btree (metric_event_id)
- index `metric_event_proposal_idx`: btree (tenant_id, proposal_id, name) WHERE (proposal_id IS NOT NULL)
- index `metric_event_tenant_id_uq`: UNIQUE btree (tenant_id, metric_event_id)
- index `metric_event_trip_idx`: btree (tenant_id, trip_id, created_at)
- check `metric_event_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `metric_event_values_chk`: `CHECK (((name ~ '^[a-z][a-z0-9_]{0,30}\.[a-z][a-z0-9_]{0,30}$'::text) AND (jsonb_typeof(detail) = 'object'::text) AND (octet_length((detail)::text) <= 4000) AND ((seen_at IS NULL) OR (bell_member_id IS NOT NULL))))`
- grant `crm_app`: INSERT, SELECT
- column grant `crm_app`: UPDATE (seen_at)
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `metric_event_hold_guard`: BEFORE DELETE OR UPDATE ON crm.metric_event FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `metric_event_sealed`: BEFORE UPDATE ON crm.metric_event FOR EACH ROW EXECUTE FUNCTION crm.guard_metric_event()
- trigger `metric_event_set_updated_at`: BEFORE UPDATE ON crm.metric_event FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

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
- check `note_body_chk`: `CHECK ((octet_length(body_enc) >= 30))`
- check `note_kind_chk`: `CHECK ((kind = ANY (ARRAY['internal'::text, 'call_log'::text, 'stage2_free_text'::text, 'inquiry_message'::text])))`
- check `note_subject_chk`: `CHECK (((trip_id IS NOT NULL) OR (traveler_id IS NOT NULL)))`
- check `note_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `note_hold_guard`: BEFORE DELETE OR UPDATE ON crm.note FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id', 'body_enc', 'kind')
- trigger `note_set_updated_at`: BEFORE UPDATE ON crm.note FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.option` (table, 160 kB)
```
option_id uuid NN
tenant_id uuid NN
proposal_id uuid NN
trip_id uuid NN
option_block_id uuid NN
sort_order smallint NN
source text NN
title text NN
tier text
agency_supplier_id uuid
sell_amount numeric(14,2) NN
net_amount numeric(14,2) · conf:commercial
pay_on_arrival boolean NN
choose_later_allowed boolean NN
availability text NN
availability_checked_at timestamp with time zone
aa_tour_source_id text
aa_component_id text
aa_component_kind text
aa_departure_id text
aa_nights smallint
aa_quote_id text
aa_quote_valid_until timestamp with time zone
aa_from_price numeric(14,2)
below_from_price boolean
source_option_id uuid
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `option_block_idx`: btree (tenant_id, option_block_id, sort_order)
- index `option_block_uq`: UNIQUE btree (tenant_id, option_block_id, option_id)
- index `option_pkey` PRIMARY KEY: UNIQUE btree (option_id)
- index `option_proposal_uq`: UNIQUE btree (tenant_id, proposal_id, option_id)
- index `option_supplier_idx`: btree (tenant_id, agency_supplier_id) WHERE (agency_supplier_id IS NOT NULL)
- index `option_tenant_id_uq`: UNIQUE btree (tenant_id, option_id)
- index `option_trip_idx`: btree (tenant_id, trip_id)
- check `option_source_chk`: `CHECK ((((source = 'aa'::text) AND (agency_supplier_id IS NULL) AND (NOT choose_later_allowed) AND (availability = ANY (ARRAY['instant'::text, 'on_request'::text, 'sold_out'::text])) AND (aa_tour_source_id IS NOT NULL) AND ((char_length(aa_tour_source_id) >= 1) AND (char_length(aa_tour_source_id) <= 128)) AND (aa_tour_source_id !~ '[[:cntrl:]]'::text) AND (aa_component_id ~ '^[A-Za-z0-9:_.-]{1,64}$'::text) AND (aa_component_kind = ANY (ARRAY['trip_plan'::text, 'hotel_room'::text, 'transfer'::text, 'guide'::text, 'activity'::text, 'entrance'::text, 'meal'::text])) AND (COALESCE(aa_departure_id, 'x'::text) ~ '^[A-Za-z0-9:_.-]{1,64}$'::text) AND ((aa_component_kind <> 'hotel_room'::text) OR (aa_nights IS NOT NULL)) AND (COALESCE(aa_quote_id, 'x'::text) ~ '^[A-Za-z0-9:_.-]{1,64}$'::text)) OR ((source = 'agency'::text) AND (availability = 'agency'::text) AND (num_nonnulls(aa_tour_source_id, aa_component_id, aa_component_kind, aa_departure_id, aa_nights, aa_quote_id, aa_quote_valid_until, aa_from_price, below_from_price) = 0))))`
- check `option_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `option_values_chk`: `CHECK ((((sort_order >= 0) AND (sort_order <= 99)) AND (source = ANY (ARRAY['aa'::text, 'agency'::text])) AND ((char_length(title) >= 1) AND (char_length(title) <= 200)) AND (title !~ '[[:cntrl:]]'::text) AND ((tier IS NULL) OR (tier = ANY (ARRAY['budget'::text, 'comfort'::text, 'premium'::text, 'luxury'::text]))) AND (sell_amount >= (0)::numeric) AND ((net_amount IS NULL) OR (net_amount >= (0)::numeric)) AND (availability = ANY (ARRAY['instant'::text, 'on_request'::text, 'sold_out'::text, 'agency'::text])) AND ((aa_from_price IS NULL) OR (aa_from_price >= (0)::numeric)) AND ((aa_nights IS NULL) OR ((aa_nights >= 1) AND (aa_nights <= 60)))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `option_draft_only`: BEFORE INSERT OR DELETE OR UPDATE ON crm.option FOR EACH ROW EXECUTE FUNCTION crm.guard_proposal_draft()
- trigger `option_hold_guard`: BEFORE DELETE OR UPDATE ON crm.option FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `option_set_updated_at`: BEFORE UPDATE ON crm.option FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.option_block` (table, ~42 rows, 128 kB)
```
option_block_id uuid NN
tenant_id uuid NN
proposal_id uuid NN
trip_id uuid NN
proposal_day_id uuid NN
sort_order smallint NN
title text NN
type text NN
client_may_swap boolean NN
default_option_id uuid
default_pinned boolean NN
source_block_id uuid
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `option_block_day_idx`: btree (tenant_id, proposal_day_id, sort_order)
- index `option_block_pkey` PRIMARY KEY: UNIQUE btree (option_block_id)
- index `option_block_proposal_uq`: UNIQUE btree (tenant_id, proposal_id, option_block_id)
- index `option_block_tenant_id_uq`: UNIQUE btree (tenant_id, option_block_id)
- index `option_block_trip_idx`: btree (tenant_id, trip_id)
- check `option_block_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `option_block_values_chk`: `CHECK ((((sort_order >= 0) AND (sort_order <= 99)) AND ((char_length(title) >= 1) AND (char_length(title) <= 120)) AND (title !~ '[[:cntrl:]]'::text) AND (type = ANY (ARRAY['lodging'::text, 'activity'::text, 'transport'::text, 'meal'::text, 'guide'::text, 'other'::text]))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `option_block_draft_only`: BEFORE INSERT OR DELETE OR UPDATE ON crm.option_block FOR EACH ROW EXECUTE FUNCTION crm.guard_proposal_draft()
- trigger `option_block_hold_guard`: BEFORE DELETE OR UPDATE ON crm.option_block FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `option_block_set_updated_at`: BEFORE UPDATE ON crm.option_block FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.option_rule` (table, 96 kB)
```
option_rule_id uuid NN
tenant_id uuid NN
proposal_id uuid NN
trip_id uuid NN
kind text NN
option_id uuid NN
target_option_id uuid NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `option_rule_pkey` PRIMARY KEY: UNIQUE btree (option_rule_id)
- index `option_rule_target_idx`: btree (tenant_id, target_option_id)
- index `option_rule_tenant_id_uq`: UNIQUE btree (tenant_id, option_rule_id)
- index `option_rule_trip_idx`: btree (tenant_id, trip_id)
- index `option_rule_uq`: UNIQUE btree (tenant_id, proposal_id, kind, option_id, target_option_id)
- check `option_rule_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `option_rule_values_chk`: `CHECK (((kind = ANY (ARRAY['requires'::text, 'excludes'::text])) AND (option_id <> target_option_id)))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `option_rule_draft_only`: BEFORE INSERT OR DELETE OR UPDATE ON crm.option_rule FOR EACH ROW EXECUTE FUNCTION crm.guard_proposal_draft()
- trigger `option_rule_hold_guard`: BEFORE DELETE OR UPDATE ON crm.option_rule FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `option_rule_set_updated_at`: BEFORE UPDATE ON crm.option_rule FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.otp_challenge` (table, 104 kB)
```
otp_id uuid NN
tenant_id uuid NN
access_id uuid NN
trip_id uuid NN
traveler_id uuid NN
purpose text NN
code_hash bytea NN · conf:credential
attempts smallint NN
status text NN
expires_at timestamp with time zone NN
verified_at timestamp with time zone
session_hash bytea · conf:credential
session_expires_at timestamp with time zone
consumed_at timestamp with time zone
message_id uuid
code_enc bytea · conf:credential
delivery text NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `otp_challenge_access_idx`: btree (tenant_id, access_id, created_at DESC)
- index `otp_challenge_created_idx`: btree (tenant_id, created_at)
- index `otp_challenge_message_idx`: btree (tenant_id, message_id) WHERE (message_id IS NOT NULL)
- index `otp_challenge_pkey` PRIMARY KEY: UNIQUE btree (otp_id)
- index `otp_challenge_session_uq`: UNIQUE btree (session_hash)
- index `otp_challenge_tenant_id_uq`: UNIQUE btree (tenant_id, otp_id)
- check `otp_challenge_attempts_chk`: `CHECK (((attempts >= 0) AND (attempts <= 5)))`
- check `otp_challenge_code_enc_chk`: `CHECK (((code_enc IS NULL) OR ((status = 'pending'::text) AND (octet_length(code_enc) >= 30))))`
- check `otp_challenge_delivery_chk`: `CHECK ((delivery = ANY (ARRAY['mailbox'::text, 'dev_echo'::text])))`
- check `otp_challenge_expiry_chk`: `CHECK (((expires_at > created_at) AND (expires_at <= (created_at + '00:10:00'::interval))))`
- check `otp_challenge_hash_chk`: `CHECK (((octet_length(code_hash) = 32) AND (COALESCE(octet_length(session_hash), 32) = 32)))`
- check `otp_challenge_purpose_chk`: `CHECK ((purpose = ANY (ARRAY['sign_in'::text, 'sign'::text])))`
- check `otp_challenge_session_chk`: `CHECK ((((session_hash IS NULL) = (session_expires_at IS NULL)) AND ((session_hash IS NULL) OR ((purpose = 'sign_in'::text) AND (verified_at IS NOT NULL) AND (session_expires_at <= (verified_at + '12:00:00'::interval)))) AND ((consumed_at IS NULL) OR ((purpose = 'sign'::text) AND (verified_at IS NOT NULL)))))`
- check `otp_challenge_status_chk`: `CHECK ((status = ANY (ARRAY['pending'::text, 'verified'::text, 'failed'::text, 'expired'::text])))`
- check `otp_challenge_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `otp_challenge_verified_chk`: `CHECK ((((status = 'verified'::text) OR ((status = 'expired'::text) AND (verified_at IS NOT NULL))) = (verified_at IS NOT NULL)))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `otp_challenge_set_updated_at`: BEFORE UPDATE ON crm.otp_challenge FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `otp_challenge_status_transition`: BEFORE UPDATE OF status ON crm.otp_challenge FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

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
- check `owner_recovery_actor_chk`: `CHECK (((requested_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text) AND ((decided_by IS NULL) OR (decided_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text))))`
- check `owner_recovery_decided_chk`: `CHECK ((((status = 'pending'::text) = (decided_at IS NULL)) AND ((decided_at IS NULL) = (decided_by IS NULL))))`
- check `owner_recovery_reason_chk`: `CHECK ((reason = ANY (ARRAY['owner_left'::text, 'owner_unreachable'::text, 'no_owner'::text])))`
- check `owner_recovery_request_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `owner_recovery_status_chk`: `CHECK ((status = ANY (ARRAY['pending'::text, 'cancelled'::text, 'completed'::text])))`
- check `owner_recovery_wait_chk`: `CHECK ((eligible_at >= (created_at + '14 days'::interval)))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `owner_recovery_guard`: BEFORE INSERT OR UPDATE ON crm.owner_recovery_request FOR EACH ROW EXECUTE FUNCTION crm.guard_owner_recovery()
- trigger `owner_recovery_set_updated_at`: BEFORE UPDATE ON crm.owner_recovery_request FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `owner_recovery_status_transition`: BEFORE UPDATE OF status ON crm.owner_recovery_request FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.payment` (table, 80 kB)
```
payment_id uuid NN
tenant_id uuid NN
trip_id uuid NN
schedule_id uuid NN
amount numeric(14,2) NN
currency character(3) NN
method text NN
received_on date NN
created_at timestamp with time zone NN
created_by text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `payment_pkey` PRIMARY KEY: UNIQUE btree (payment_id)
- index `payment_schedule_once_uq`: UNIQUE btree (tenant_id, schedule_id)
- index `payment_tenant_id_uq`: UNIQUE btree (tenant_id, payment_id)
- index `payment_trip_idx`: btree (tenant_id, trip_id)
- check `payment_amount_chk`: `CHECK ((amount > (0)::numeric))`
- check `payment_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `payment_method_chk`: `CHECK ((method = ANY (ARRAY['bank_transfer'::text, 'cash'::text, 'card_offline'::text, 'other'::text])))`
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `payment_append_only`: BEFORE DELETE OR UPDATE ON crm.payment FOR EACH ROW EXECUTE FUNCTION crm.ledger_append_only()
- trigger `payment_no_truncate`: BEFORE TRUNCATE ON crm.payment FOR EACH STATEMENT EXECUTE FUNCTION crm.ledger_append_only()

### `crm.payment_schedule` (table, 96 kB)
```
schedule_id uuid NN
tenant_id uuid NN
trip_id uuid NN
proposal_id uuid NN
kind text NN
amount numeric(14,2) NN
currency character(3) NN
due_on date NN
status text NN
paid_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `payment_schedule_live_uq`: UNIQUE btree (tenant_id, proposal_id, kind) WHERE ((status <> 'void'::text) AND (deleted_at IS NULL))
- index `payment_schedule_pkey` PRIMARY KEY: UNIQUE btree (schedule_id)
- index `payment_schedule_tenant_id_uq`: UNIQUE btree (tenant_id, schedule_id)
- index `payment_schedule_trip_idx`: btree (tenant_id, trip_id)
- index `payment_schedule_trip_uq`: UNIQUE btree (tenant_id, schedule_id, trip_id)
- check `payment_schedule_amount_chk`: `CHECK ((amount > (0)::numeric))`
- check `payment_schedule_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `payment_schedule_deposit_void_chk`: `CHECK (((kind <> 'deposit'::text) OR (status <> 'void'::text)))`
- check `payment_schedule_kind_chk`: `CHECK ((kind = ANY (ARRAY['deposit'::text, 'balance'::text])))`
- check `payment_schedule_paid_chk`: `CHECK (((status = 'paid'::text) = (paid_at IS NOT NULL)))`
- check `payment_schedule_status_chk`: `CHECK ((status = ANY (ARRAY['due'::text, 'paid'::text, 'void'::text])))`
- check `payment_schedule_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `payment_schedule_hold_guard`: BEFORE DELETE OR UPDATE ON crm.payment_schedule FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `payment_schedule_sealed`: BEFORE UPDATE ON crm.payment_schedule FOR EACH ROW EXECUTE FUNCTION crm.guard_sealed_row('due', 'trip_id', 'proposal_id', 'kind', 'amount', 'currency', 'due_on', 'paid_at', 'tenant_id')
- trigger `payment_schedule_set_updated_at`: BEFORE UPDATE ON crm.payment_schedule FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `payment_schedule_status_transition`: BEFORE UPDATE OF status ON crm.payment_schedule FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

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
- check `placeholder_map_count_chk`: `CHECK (((placeholder_count >= 1) AND (placeholder_count <= 500)))`
- check `placeholder_map_enc_chk`: `CHECK (((octet_length(map_enc) >= 30) AND (octet_length(map_enc) <= 65536)))`
- check `placeholder_map_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `placeholder_map_ttl_chk`: `CHECK (((expires_at > created_at) AND (expires_at <= (created_at + '24:00:00'::interval))))`
- check `placeholder_map_version_chk`: `CHECK ((scrubber_version ~ '^[a-z0-9][a-z0-9.-]{0,19}$'::text))`
- grant `crm_app`: DELETE, INSERT, SELECT
- policy `placeholder_map_expired_purge` (PERMISSIVE DELETE TO crm_app): USING `((current_setting('app.purge_scope'::text, true) = 'placeholder_map'::text) AND (expires_at < now()))`
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `placeholder_map_set_updated_at`: BEFORE UPDATE ON crm.placeholder_map FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.prep_pack_selection` (table, 48 kB)
```
prep_pack_selection_id uuid NN
tenant_id uuid NN
trip_id uuid NN
proposal_id uuid NN
group_key text NN
locale text NN
content_id uuid NN
content_version integer NN
title text NN
body_markdown text NN
applies_to jsonb NN
content_hash text NN
sort_order smallint NN
source_selection_id uuid
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `prep_pack_selection_pack_uq`: UNIQUE btree (tenant_id, proposal_id, group_key, locale)
- index `prep_pack_selection_pkey` PRIMARY KEY: UNIQUE btree (prep_pack_selection_id)
- index `prep_pack_selection_proposal_idx`: btree (tenant_id, proposal_id, sort_order)
- index `prep_pack_selection_tenant_id_uq`: UNIQUE btree (tenant_id, prep_pack_selection_id)
- index `prep_pack_selection_trip_idx`: btree (tenant_id, trip_id)
- check `prep_pack_selection_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `prep_pack_selection_values_chk`: `CHECK (((group_key ~ '^[a-z0-9][a-z0-9-]{1,79}$'::text) AND (locale = ANY (ARRAY['en'::text, 'vi'::text])) AND (content_version >= 1) AND ((char_length(title) >= 1) AND (char_length(title) <= 300)) AND (title !~ '[[:cntrl:]]'::text) AND (octet_length(body_markdown) <= 200000) AND (jsonb_typeof(applies_to) = 'object'::text) AND ((char_length(content_hash) >= 1) AND (char_length(content_hash) <= 100)) AND ((sort_order >= 0) AND (sort_order <= 99))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `prep_pack_selection_draft_only`: BEFORE INSERT OR DELETE OR UPDATE ON crm.prep_pack_selection FOR EACH ROW EXECUTE FUNCTION crm.guard_proposal_draft()
- trigger `prep_pack_selection_hold_guard`: BEFORE DELETE OR UPDATE ON crm.prep_pack_selection FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `prep_pack_selection_set_updated_at`: BEFORE UPDATE ON crm.prep_pack_selection FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

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
- check `profile_history_ids_chk`: `CHECK ((((aa_departure_id IS NULL) OR (aa_departure_id ~ '^[A-Za-z0-9:_-]{1,80}$'::text)) AND ((aa_product_key IS NULL) OR (aa_product_key ~ '^[A-Za-z0-9:_./-]{1,120}$'::text))))`
- check `profile_history_month_chk`: `CHECK ((year_month = (date_trunc('month'::text, (year_month)::timestamp with time zone))::date))`
- check `profile_history_stage_chk`: `CHECK ((stage_reached = ANY (ARRAY['inquiry'::text, 'qualifying'::text, 'proposal'::text, 'booked'::text, 'pre_departure'::text, 'travelling'::text, 'completed'::text, 'lost'::text, 'cancelled'::text])))`
- check `profile_history_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `profile_history_set_updated_at`: BEFORE UPDATE ON crm.profile_history FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.proposal` (table, ~20 rows, 232 kB)
```
proposal_id uuid NN
tenant_id uuid NN
trip_id uuid NN
version integer NN
status text NN
body_enc bytea NN · pii:free_text
currency character(3) NN
total_amount numeric(14,2) NN
deposit_amount numeric(14,2) NN
balance_due_on date
terms_doc_id uuid
price_hash bytea
link_id uuid
sent_at timestamp with time zone
accepted_at timestamp with time zone
accepted_name_enc bytea · pii:name
accepted_name_erased_at timestamp with time zone
accepted_price_hash bytea
accepted_terms_doc_id uuid
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
kind text NN
price_visibility text NN
room_config jsonb
deposit_pct numeric(5,2)
starts_on date
edit_seq integer NN
selection_seq integer NN
based_on_proposal_id uuid
based_on_selection_seq integer
published_at timestamp with time zone
view_count integer NN
first_viewed_at timestamp with time zone
last_viewed_at timestamp with time zone
nudged_at timestamp with time zone
hold_set_ref text
hold_id text
hold_quote_id text
hold_expires_at timestamp with time zone
hold_selection_sha256 bytea
hold_placed_at timestamp with time zone
hold_count smallint NN
recheck_day date
recheck_count_day smallint NN
hold_attempt smallint NN
hold_pending_key text
hold_pending_at timestamp with time zone
hold_pending_quote_id text
hold_pending_price_hash text
hold_pending_selection_sha256 bytea
hold_release_id text
accepted_selection_sha256 bytea
accepted_total_amount numeric(14,2)
accepted_deposit_amount numeric(14,2)
accepted_hold_id text
```
- owner `crm_owner` · RLS on + FORCE
- index `proposal_based_on_idx`: btree (tenant_id, based_on_proposal_id) WHERE (based_on_proposal_id IS NOT NULL)
- index `proposal_hold_set_uq`: UNIQUE btree (tenant_id, hold_set_ref) WHERE (hold_set_ref IS NOT NULL)
- index `proposal_link_idx`: btree (tenant_id, link_id) WHERE (link_id IS NOT NULL)
- index `proposal_nudge_idx`: btree (tenant_id, first_viewed_at) WHERE ((status = 'sent'::text) AND (nudged_at IS NULL) AND (first_viewed_at IS NOT NULL) AND (deleted_at IS NULL))
- index `proposal_one_accepted_uq`: UNIQUE btree (tenant_id, trip_id) WHERE ((status = 'accepted'::text) AND (deleted_at IS NULL))
- index `proposal_one_published_uq`: UNIQUE btree (tenant_id, trip_id) WHERE ((status = 'published'::text) AND (deleted_at IS NULL))
- index `proposal_one_sent_uq`: UNIQUE btree (tenant_id, trip_id) WHERE ((status = 'sent'::text) AND (deleted_at IS NULL))
- index `proposal_pkey` PRIMARY KEY: UNIQUE btree (proposal_id)
- index `proposal_tenant_id_uq`: UNIQUE btree (tenant_id, proposal_id)
- index `proposal_trip_uq`: UNIQUE btree (tenant_id, proposal_id, trip_id)
- index `proposal_version_uq`: UNIQUE btree (tenant_id, trip_id, version)
- check `proposal_accepted_chk`: `CHECK ((((status = 'accepted'::text) = (accepted_at IS NOT NULL)) AND ((accepted_at IS NULL) = ((accepted_name_enc IS NULL) AND (accepted_name_erased_at IS NULL))) AND ((accepted_name_enc IS NULL) OR (accepted_name_erased_at IS NULL)) AND ((accepted_at IS NULL) = (accepted_price_hash IS NULL)) AND ((accepted_price_hash IS NULL) OR (accepted_price_hash = price_hash)) AND ((accepted_terms_doc_id IS NULL) OR (accepted_terms_doc_id = terms_doc_id)) AND ((accepted_at IS NULL) OR (terms_doc_id IS NULL) OR (accepted_terms_doc_id IS NOT NULL))))`
- check `proposal_accepted_choice_chk`: `CHECK (((COALESCE(octet_length(accepted_selection_sha256), 32) = 32) AND
CASE
    WHEN ((kind = 'builder'::text) AND (accepted_at IS NOT NULL)) THEN ((accepted_selection_sha256 IS NOT NULL) AND (accepted_total_amount > (0)::numeric) AND (accepted_deposit_amount > (0)::numeric) AND (accepted_deposit_amount <= accepted_total_amount))
    ELSE (num_nonnulls(accepted_selection_sha256, accepted_total_amount, accepted_deposit_amount, accepted_hold_id) = 0)
END))`
- check `proposal_amounts_chk`: `CHECK ((((kind = 'builder'::text) AND (published_at IS NULL) AND (total_amount >= (0)::numeric) AND (deposit_amount >= (0)::numeric) AND (deposit_amount <= total_amount)) OR ((total_amount > (0)::numeric) AND (deposit_amount > (0)::numeric) AND (deposit_amount <= total_amount) AND ((balance_due_on IS NULL) = (deposit_amount = total_amount)))))`
- check `proposal_currency_chk`: `CHECK ((currency ~ '^[A-Z]{3}$'::text))`
- check `proposal_enc_chk`: `CHECK (((octet_length(body_enc) >= 30) AND (COALESCE(octet_length(accepted_name_enc), 30) >= 30)))`
- check `proposal_hash_chk`: `CHECK (((COALESCE(octet_length(price_hash), 32) = 32) AND (COALESCE(octet_length(accepted_price_hash), 32) = 32)))`
- check `proposal_hold_chk`: `CHECK ((((hold_set_ref IS NULL) OR (hold_set_ref = ('crm-proposal:'::text || (proposal_id)::text))) AND ((hold_id IS NULL) OR (hold_id ~ '^[A-Za-z0-9:_.-]{1,64}$'::text)) AND ((hold_quote_id IS NULL) OR (hold_quote_id ~ '^[A-Za-z0-9:_.-]{1,64}$'::text)) AND ((accepted_hold_id IS NULL) OR (accepted_hold_id ~ '^[A-Za-z0-9:_.-]{1,64}$'::text)) AND ((hold_release_id IS NULL) OR (hold_release_id ~ '^[A-Za-z0-9:_.-]{1,64}$'::text)) AND ((hold_release_id IS NULL) OR (hold_id IS NULL)) AND (num_nonnulls(hold_id, hold_quote_id, hold_expires_at, hold_selection_sha256, hold_placed_at) = ANY (ARRAY[0, 5])) AND ((hold_id IS NULL) OR ((hold_set_ref IS NOT NULL) AND (hold_count >= 1))) AND (COALESCE(octet_length(hold_selection_sha256), 32) = 32) AND ((hold_count >= 0) AND (hold_count <= 1000)) AND ((recheck_count_day >= 0) AND (recheck_count_day <= 3)) AND ((recheck_count_day = 0) OR (recheck_day IS NOT NULL)) AND ((kind = 'builder'::text) OR ((hold_set_ref IS NULL) AND (hold_id IS NULL) AND (hold_count = 0) AND (recheck_day IS NULL) AND (recheck_count_day = 0) AND (hold_release_id IS NULL)))))`
- check `proposal_hold_pending_chk`: `CHECK ((((hold_attempt >= 0) AND (hold_attempt <= 10000)) AND ((hold_pending_key IS NULL) OR (hold_pending_key ~ '^crm-proposal:[0-9a-f-]{36}:v[0-9]{1,5}:a[0-9]{1,5}$'::text)) AND ((hold_pending_key IS NULL) = (hold_pending_at IS NULL)) AND ((hold_pending_key IS NULL) OR (hold_attempt >= 1)) AND (num_nonnulls(hold_pending_quote_id, hold_pending_price_hash, hold_pending_selection_sha256) = ANY (ARRAY[0, 3])) AND ((hold_pending_quote_id IS NULL) OR (hold_pending_key IS NOT NULL)) AND ((hold_pending_quote_id IS NULL) OR (hold_pending_quote_id ~ '^[A-Za-z0-9:_.-]{1,64}$'::text)) AND ((hold_pending_price_hash IS NULL) OR (hold_pending_price_hash ~ '^[a-f0-9]{64}$'::text)) AND (COALESCE(octet_length(hold_pending_selection_sha256), 32) = 32) AND ((kind = 'builder'::text) OR ((hold_attempt = 0) AND (hold_pending_key IS NULL)))))`
- check `proposal_kind_chk`: `CHECK (((kind = ANY (ARRAY['text'::text, 'builder'::text])) AND (price_visibility = ANY (ARRAY['total_with_deltas'::text, 'total_only'::text])) AND (edit_seq >= 1) AND (selection_seq >= 0) AND (COALESCE(based_on_selection_seq, 0) >= 0) AND ((room_config IS NULL) OR ((jsonb_typeof(room_config) = 'array'::text) AND ((jsonb_array_length(room_config) >= 1) AND (jsonb_array_length(room_config) <= 20)))) AND ((deposit_pct IS NULL) OR ((deposit_pct >= (1)::numeric) AND (deposit_pct <= (100)::numeric))) AND ((kind = 'builder'::text) OR ((room_config IS NULL) AND (deposit_pct IS NULL) AND (starts_on IS NULL) AND (based_on_proposal_id IS NULL) AND (based_on_selection_seq IS NULL) AND (published_at IS NULL) AND (selection_seq = 0))) AND ((kind = 'text'::text) OR (deposit_pct IS NOT NULL))))`
- check `proposal_sent_chk`: `CHECK ((
CASE
    WHEN (status = 'draft'::text) THEN ((price_hash IS NULL) AND (sent_at IS NULL) AND (published_at IS NULL))
    WHEN (status = 'published'::text) THEN ((kind = 'builder'::text) AND (price_hash IS NOT NULL) AND (published_at IS NOT NULL) AND (sent_at IS NULL))
    WHEN (status = 'withdrawn'::text) THEN ((price_hash IS NULL) = ((sent_at IS NULL) AND (published_at IS NULL)))
    ELSE ((price_hash IS NOT NULL) AND ((sent_at IS NOT NULL) OR ((status = 'superseded'::text) AND (published_at IS NOT NULL))))
END AND ((kind = 'text'::text) OR (status = ANY (ARRAY['draft'::text, 'withdrawn'::text])) OR (published_at IS NOT NULL))))`
- check `proposal_status_chk`: `CHECK ((status = ANY (ARRAY['draft'::text, 'published'::text, 'sent'::text, 'accepted'::text, 'superseded'::text, 'withdrawn'::text])))`
- check `proposal_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `proposal_version_chk`: `CHECK (((version >= 1) AND (version <= 999)))`
- check `proposal_viewed_chk`: `CHECK (((view_count >= 0) AND ((first_viewed_at IS NULL) = (view_count = 0)) AND ((last_viewed_at IS NULL) = (first_viewed_at IS NULL)) AND ((last_viewed_at IS NULL) OR (last_viewed_at >= first_viewed_at)) AND ((nudged_at IS NULL) OR (first_viewed_at IS NOT NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `proposal_acceptance_sealed`: BEFORE UPDATE ON crm.proposal FOR EACH ROW EXECUTE FUNCTION crm.guard_sealed_row('sent', 'accepted_at', 'accepted_name_enc', 'accepted_name_erased_at', 'accepted_price_hash', 'accepted_terms_doc_id', 'accepted_selection_sha256', 'accepted_total_amount', 'accepted_deposit_amount', 'accepted_hold_id')
- trigger `proposal_hold_guard`: BEFORE DELETE OR UPDATE ON crm.proposal FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `proposal_sealed`: BEFORE UPDATE ON crm.proposal FOR EACH ROW EXECUTE FUNCTION crm.guard_sealed_row('draft', 'trip_id', 'version', 'body_enc', 'currency', 'total_amount', 'deposit_amount', 'balance_due_on', 'terms_doc_id', 'price_hash', 'tenant_id', 'kind', 'price_visibility', 'room_config', 'deposit_pct', 'starts_on', 'published_at')
- trigger `proposal_sent_once`: BEFORE UPDATE ON crm.proposal FOR EACH ROW EXECUTE FUNCTION crm.guard_set_once('sent_at')
- trigger `proposal_set_updated_at`: BEFORE UPDATE ON crm.proposal FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `proposal_status_transition`: BEFORE UPDATE OF status ON crm.proposal FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.proposal_day` (table, ~54 rows, 136 kB)
```
proposal_day_id uuid NN
tenant_id uuid NN
proposal_id uuid NN
trip_id uuid NN
day_no smallint NN
title text
place text
tz text NN
notes_enc bytea · pii:free_text
source_day_id uuid
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `proposal_day_no_uq`: UNIQUE btree (tenant_id, proposal_id, day_no)
- index `proposal_day_pkey` PRIMARY KEY: UNIQUE btree (proposal_day_id)
- index `proposal_day_proposal_uq`: UNIQUE btree (tenant_id, proposal_id, proposal_day_id)
- index `proposal_day_tenant_id_uq`: UNIQUE btree (tenant_id, proposal_day_id)
- index `proposal_day_trip_idx`: btree (tenant_id, trip_id)
- check `proposal_day_no_chk`: `CHECK (((day_no >= 0) AND (day_no <= 90)))`
- check `proposal_day_text_chk`: `CHECK ((((title IS NULL) OR (((char_length(title) >= 1) AND (char_length(title) <= 120)) AND (title !~ '[[:cntrl:]]'::text))) AND ((place IS NULL) OR (((char_length(place) >= 1) AND (char_length(place) <= 120)) AND (place !~ '[[:cntrl:]]'::text))) AND (COALESCE(octet_length(notes_enc), 30) >= 30)))`
- check `proposal_day_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `proposal_day_tz_chk`: `CHECK (((tz = 'UTC'::text) OR (tz ~ '^[A-Z][A-Za-z_]+(/[A-Za-z0-9_+-]+){1,2}$'::text)))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `proposal_day_draft_only`: BEFORE INSERT OR DELETE OR UPDATE ON crm.proposal_day FOR EACH ROW EXECUTE FUNCTION crm.guard_proposal_draft()
- trigger `proposal_day_hold_guard`: BEFORE DELETE OR UPDATE ON crm.proposal_day FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `proposal_day_set_updated_at`: BEFORE UPDATE ON crm.proposal_day FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.saved_reply` (table, 24 kB)
```
saved_reply_id uuid NN
tenant_id uuid NN
member_id uuid
locale text NN
title text NN
body_enc bytea NN · pii:free_text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `saved_reply_pkey` PRIMARY KEY: UNIQUE btree (saved_reply_id)
- index `saved_reply_tenant_idx`: btree (tenant_id, member_id, title) WHERE (deleted_at IS NULL)
- check `saved_reply_body_chk`: `CHECK (((octet_length(body_enc) >= 30) AND (octet_length(body_enc) <= 65536)))`
- check `saved_reply_locale_chk`: `CHECK ((locale = ANY (ARRAY['en'::text, 'vi'::text])))`
- check `saved_reply_title_chk`: `CHECK ((((char_length(btrim(title)) >= 1) AND (char_length(btrim(title)) <= 80)) AND (title !~ '[[:cntrl:]]'::text)))`
- check `saved_reply_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `saved_reply_set_updated_at`: BEFORE UPDATE ON crm.saved_reply FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.selection` (table, 96 kB)
```
selection_id uuid NN
tenant_id uuid NN
proposal_id uuid NN
trip_id uuid NN
option_block_id uuid NN
option_id uuid NN
chosen_by text NN
choose_later boolean NN
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `selection_block_uq`: UNIQUE btree (tenant_id, proposal_id, option_block_id)
- index `selection_option_idx`: btree (tenant_id, option_block_id, option_id)
- index `selection_pkey` PRIMARY KEY: UNIQUE btree (selection_id)
- index `selection_tenant_id_uq`: UNIQUE btree (tenant_id, selection_id)
- index `selection_trip_idx`: btree (tenant_id, trip_id)
- check `selection_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `selection_values_chk`: `CHECK ((chosen_by = ANY (ARRAY['client'::text, 'agent'::text, 'carried'::text])))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `selection_hold_guard`: BEFORE DELETE OR UPDATE ON crm.selection FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id')
- trigger `selection_open_version`: BEFORE INSERT OR UPDATE ON crm.selection FOR EACH ROW EXECUTE FUNCTION crm.guard_selection()
- trigger `selection_set_updated_at`: BEFORE UPDATE ON crm.selection FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.signature_request` (table, 88 kB)
```
request_id uuid NN
tenant_id uuid NN
trip_id uuid NN
traveler_id uuid NN
access_id uuid NN
doc_id uuid NN
status text NN
doc_sha256 bytea
signed_at timestamp with time zone
signed_name_enc bytea · pii:name
otp_id uuid
code_delivery text
evidence_record bytea
evidence_sha256 bytea
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `signature_request_access_idx`: btree (tenant_id, access_id)
- index `signature_request_live_uq`: UNIQUE btree (tenant_id, trip_id, traveler_id, doc_id) WHERE ((status <> 'void'::text) AND (deleted_at IS NULL))
- index `signature_request_otp_idx`: btree (tenant_id, otp_id) WHERE (otp_id IS NOT NULL)
- index `signature_request_pkey` PRIMARY KEY: UNIQUE btree (request_id)
- index `signature_request_tenant_id_uq`: UNIQUE btree (tenant_id, request_id)
- check `signature_request_code_delivery_chk`: `CHECK ((code_delivery = ANY (ARRAY['mailbox'::text, 'dev_echo'::text])))`
- check `signature_request_evidence_chk`: `CHECK (((evidence_record IS NULL) OR (((octet_length(evidence_record) >= 2) AND (octet_length(evidence_record) <= 4096)) AND (sha256(evidence_record) = evidence_sha256))))`
- check `signature_request_hash_chk`: `CHECK (((COALESCE(octet_length(doc_sha256), 32) = 32) AND (COALESCE(octet_length(evidence_sha256), 32) = 32) AND (COALESCE(octet_length(signed_name_enc), 30) >= 30)))`
- check `signature_request_signed_chk`: `CHECK ((((status = 'signed'::text) = (signed_at IS NOT NULL)) AND ((signed_at IS NULL) = (signed_name_enc IS NULL)) AND ((signed_at IS NULL) = (doc_sha256 IS NULL)) AND ((signed_at IS NULL) = (evidence_sha256 IS NULL)) AND ((signed_at IS NULL) = (evidence_record IS NULL)) AND ((signed_at IS NULL) = (code_delivery IS NULL)) AND ((signed_at IS NOT NULL) OR (otp_id IS NULL))))`
- check `signature_request_status_chk`: `CHECK ((status = ANY (ARRAY['pending'::text, 'signed'::text, 'void'::text])))`
- check `signature_request_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `signature_request_hold_guard`: BEFORE DELETE OR UPDATE ON crm.signature_request FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id')
- trigger `signature_request_sealed`: BEFORE UPDATE ON crm.signature_request FOR EACH ROW EXECUTE FUNCTION crm.guard_sealed_row('pending', 'trip_id', 'traveler_id', 'access_id', 'doc_id', 'doc_sha256', 'signed_at', 'signed_name_enc', 'code_delivery', 'evidence_record', 'evidence_sha256', 'tenant_id')
- trigger `signature_request_set_updated_at`: BEFORE UPDATE ON crm.signature_request FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `signature_request_status_transition`: BEFORE UPDATE OF status ON crm.signature_request FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.status_transition` (table, ~121 rows, 64 kB)
```
table_name text NN
from_status text NN
to_status text NN
```
- owner `crm_owner`
- index `status_transition_pkey` PRIMARY KEY: UNIQUE btree (table_name, from_status, to_status)
- check `status_transition_names_chk`: `CHECK (((table_name ~ '^[a-z][a-z0-9_]*$'::text) AND (from_status ~ '^[a-z][a-z0-9_]*$'::text) AND (to_status ~ '^[a-z][a-z0-9_]*$'::text) AND (from_status <> to_status)))`
- grant `crm_app`: SELECT

### `crm.studio_invitation` (table, 96 kB)
```
studio_invitation_id uuid NN
cis_tenant_id uuid NN
cis_invitation_id uuid NN
email_enc bytea NN
token_hash bytea NN
locale text NN
status text NN
issued_at timestamp with time zone NN
expires_at timestamp with time zone NN
cognito_iss text
cognito_sub text · pii:online_id
claimed_at timestamp with time zone
accepted_at timestamp with time zone
activated_at timestamp with time zone
activation_attempts integer NN
activation_error text
invited_by text NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `crm_owner` · RLS on + FORCE
- index `studio_invitation_cis_invitation_uq`: UNIQUE btree (cis_invitation_id)
- index `studio_invitation_due_idx`: btree (accepted_at) WHERE (status = 'accepted'::text)
- index `studio_invitation_pkey` PRIMARY KEY: UNIQUE btree (studio_invitation_id)
- index `studio_invitation_tenant_idx`: btree (cis_tenant_id, created_at DESC)
- index `studio_invitation_token_uq`: UNIQUE btree (token_hash)
- check `studio_invitation_accept_chk`: `CHECK (((status = ANY (ARRAY['accepted'::text, 'activated'::text])) = (accepted_at IS NOT NULL)))`
- check `studio_invitation_activate_chk`: `CHECK (((status = 'activated'::text) = (activated_at IS NOT NULL)))`
- check `studio_invitation_actor_chk`: `CHECK (((char_length(invited_by) >= 1) AND (char_length(invited_by) <= 100)))`
- check `studio_invitation_attempts_chk`: `CHECK (((activation_attempts >= 0) AND (activation_attempts <= 1000)))`
- check `studio_invitation_claim_chk`: `CHECK ((((status = 'pending'::text) AND (cognito_sub IS NULL) AND (claimed_at IS NULL)) OR ((status = ANY (ARRAY['claimed'::text, 'accepted'::text, 'activated'::text])) AND (cognito_sub IS NOT NULL) AND (claimed_at IS NOT NULL)) OR (status = ANY (ARRAY['expired'::text, 'revoked'::text]))))`
- check `studio_invitation_email_chk`: `CHECK (((octet_length(email_enc) >= 32) AND (octet_length(email_enc) <= 1100)))`
- check `studio_invitation_error_chk`: `CHECK (((activation_error IS NULL) OR (activation_error ~ '^[a-z][a-z0-9_]{0,39}$'::text)))`
- check `studio_invitation_expiry_chk`: `CHECK (((expires_at > issued_at) AND (expires_at <= (issued_at + '30 days'::interval))))`
- check `studio_invitation_identity_chk`: `CHECK ((((cognito_iss IS NULL) = (cognito_sub IS NULL)) AND ((cognito_iss IS NULL) OR ((cognito_iss ~ '^https://[^/]+/[^/]+$'::text) AND ((length(cognito_sub) >= 1) AND (length(cognito_sub) <= 128))))))`
- check `studio_invitation_locale_chk`: `CHECK ((locale = ANY (ARRAY['en'::text, 'vi'::text])))`
- check `studio_invitation_status_chk`: `CHECK ((status = ANY (ARRAY['pending'::text, 'claimed'::text, 'accepted'::text, 'activated'::text, 'expired'::text, 'revoked'::text])))`
- check `studio_invitation_token_chk`: `CHECK ((octet_length(token_hash) = 32))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `studio_invitation_platform` (PERMISSIVE ALL TO crm_app, crm_owner): USING `((COALESCE(current_setting('app.actor'::text, true), ''::text) ~~ 'platform:%'::text) OR (COALESCE(current_setting('app.actor'::text, true), ''::text) = 'job:crm_studio_activation'::text))` WITH CHECK `((COALESCE(current_setting('app.actor'::text, true), ''::text) ~~ 'platform:%'::text) OR (COALESCE(current_setting('app.actor'::text, true), ''::text) = 'job:crm_studio_activation'::text))`
- policy `studio_invitation_token_lookup` (PERMISSIVE SELECT TO crm_app): USING `(token_hash = decode(NULLIF(current_setting('app.invite_token_hash'::text, true), ''::text), 'hex'::text))`
- policy `studio_invitation_token_update` (PERMISSIVE UPDATE TO crm_app): USING `(token_hash = decode(NULLIF(current_setting('app.invite_token_hash'::text, true), ''::text), 'hex'::text))` WITH CHECK `(token_hash = decode(NULLIF(current_setting('app.invite_token_hash'::text, true), ''::text), 'hex'::text))`
- trigger `studio_invitation_guard`: BEFORE INSERT OR UPDATE ON crm.studio_invitation FOR EACH ROW EXECUTE FUNCTION crm.guard_studio_invitation_write()
- trigger `studio_invitation_set_updated_at`: BEFORE UPDATE ON crm.studio_invitation FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `studio_invitation_status_transition`: BEFORE UPDATE OF status ON crm.studio_invitation FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

### `crm.task` (table, ~91 rows, 144 kB)
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
priority text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `task_open_idx`: btree (tenant_id, assignee_member_id, due_at) WHERE ((status = 'open'::text) AND (deleted_at IS NULL))
- index `task_open_kind_uq`: UNIQUE btree (trip_id, kind) WHERE ((status = 'open'::text) AND (deleted_at IS NULL) AND (trip_id IS NOT NULL))
- index `task_pkey` PRIMARY KEY: UNIQUE btree (task_id)
- index `task_trip_idx`: btree (trip_id) WHERE (trip_id IS NOT NULL)
- check `task_anchor_chk`: `CHECK (((due_anchor IS NULL) OR (due_anchor = ANY (ARRAY['departure'::text, 'return'::text, 'created'::text, 'stage_entered'::text, 'hold_expiry'::text, 'deposit_paid'::text, 'ops_handoff'::text]))))`
- check `task_done_chk`: `CHECK ((((status = 'open'::text) = (done_at IS NULL)) AND ((done_at IS NULL) = (done_by IS NULL))))`
- check `task_kind_chk`: `CHECK ((kind ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `task_offset_chk`: `CHECK (((due_offset_days IS NULL) OR ((due_offset_days >= '-365'::integer) AND (due_offset_days <= 365))))`
- check `task_priority_chk`: `CHECK ((priority = ANY (ARRAY['normal'::text, 'urgent'::text])))`
- check `task_status_chk`: `CHECK ((status = ANY (ARRAY['open'::text, 'done'::text, 'skipped'::text])))`
- check `task_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
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
lock_source text
```
- owner `crm_owner` · RLS on + FORCE
- index `tenant_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- check `tenant_default_locale_chk`: `CHECK ((default_locale = ANY (ARRAY['en-AU'::text, 'en-GB'::text, 'en-US'::text, 'vi-VN'::text])))`
- check `tenant_display_name_chk`: `CHECK ((((length(btrim(display_name)) >= 1) AND (length(btrim(display_name)) <= 120)) AND (display_name = btrim(display_name))))`
- check `tenant_lock_source_chk`: `CHECK (((lock_source IS NULL) OR ((lock_source = ANY (ARRAY['aa_ops'::text, 'cis_tenant'::text, 'cis_membership'::text])) AND (status = 'locked'::text))))`
- check `tenant_status_chk`: `CHECK ((status = ANY (ARRAY['active'::text, 'locked'::text, 'offboarding'::text, 'offboarded'::text])))`
- check `tenant_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- policy `tenant_member_lookup` (PERMISSIVE SELECT TO crm_app): USING `((deleted_at IS NULL) AND (EXISTS ( SELECT 1
   FROM crm.member m
  WHERE ((m.tenant_id = tenant.tenant_id) AND (m.status = 'active'::text) AND (m.deleted_at IS NULL) AND (m.cognito_iss = NULLIF(current_setting('app.caller_iss'::text, true), ''::text)) AND (m.cognito_sub = NULLIF(current_setting('app.caller_sub'::text, true), ''::text))))))`
- trigger `tenant_audit_register`: AFTER INSERT ON crm.tenant FOR EACH ROW EXECUTE FUNCTION crm.audit_register_tenant()
- trigger `tenant_set_updated_at`: BEFORE UPDATE ON crm.tenant FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `tenant_status_transition`: BEFORE UPDATE OF status ON crm.tenant FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()
- trigger `tenant_sync_lock_source`: BEFORE INSERT OR UPDATE OF status, lock_source ON crm.tenant FOR EACH ROW EXECUTE FUNCTION crm.sync_tenant_lock_source()

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
- check `tenant_entitlement_features_chk`: `CHECK ((allowed_features <@ ARRAY['ai_assist'::text, 'whatsapp_sms'::text, 'stripe_connect'::text, 'campaigns'::text, 'custom_domain'::text, 'insights_export'::text]))`
- check `tenant_entitlement_limit_chk`: `CHECK (((member_limit >= 1) AND (member_limit <= 500)))`
- check `tenant_entitlement_plan_chk`: `CHECK ((plan = ANY (ARRAY['free'::text, 'core'::text, 'pro'::text])))`
- check `tenant_entitlement_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
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
- check `tenant_key_context_chk`: `CHECK ((encryption_context = jsonb_build_object('tenant_id', (tenant_id)::text, 'purpose', purpose)))`
- check `tenant_key_destroyed_chk`: `CHECK ((((destroyed_at IS NULL) = (wrapped_dek IS NOT NULL)) AND ((destroyed_at IS NULL) OR (retired_at IS NOT NULL))))`
- check `tenant_key_kek_id_chk`: `CHECK (((length(kek_id) >= 1) AND (length(kek_id) <= 2048)))`
- check `tenant_key_kek_provider_chk`: `CHECK ((kek_provider = ANY (ARRAY['kms'::text, 'local'::text])))`
- check `tenant_key_purpose_chk`: `CHECK ((purpose = ANY (ARRAY['vault'::text, 'docs'::text, 'integration'::text, 'scrub'::text, 'ops_release'::text, 'export'::text, 'mail'::text])))`
- check `tenant_key_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `tenant_key_version_chk`: `CHECK (((key_version >= 1) AND (key_version <= 65535)))`
- check `tenant_key_wrapped_chk`: `CHECK (((wrapped_dek IS NULL) OR ((octet_length(wrapped_dek) >= 32) AND (octet_length(wrapped_dek) <= 4096))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `tenant_key_guard`: BEFORE DELETE OR UPDATE ON crm.tenant_key FOR EACH ROW EXECUTE FUNCTION crm.tenant_key_guard()
- trigger `tenant_key_set_updated_at`: BEFORE UPDATE ON crm.tenant_key FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.tenant_settings` (table, 32 kB)
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
timezone text NN
stage2_auto_send boolean NN
call_slot_rules jsonb NN
base_currency character(3) NN
booking_validation_level text NN
fx_mode text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `tenant_settings_pkey` PRIMARY KEY: UNIQUE btree (tenant_id)
- check `tenant_settings_auto_archive_chk`: `CHECK (((auto_archive_months >= 12) AND (auto_archive_months <= 120)))`
- check `tenant_settings_base_currency_chk`: `CHECK ((base_currency ~ '^[A-Z]{3}$'::text))`
- check `tenant_settings_budget_chk`: `CHECK (((ai_budget_usd >= (0)::numeric) AND (ai_budget_usd <= (10000)::numeric)))`
- check `tenant_settings_call_slot_rules_chk`: `CHECK (crm.call_slot_rules_ok(call_slot_rules))`
- check `tenant_settings_fx_mode_chk`: `CHECK ((fx_mode = ANY (ARRAY['automatic'::text, 'manual'::text])))`
- check `tenant_settings_refund_threshold_chk`: `CHECK (((refund_owner_threshold_base >= (0)::numeric) AND (refund_owner_threshold_base <= (10000000)::numeric)))`
- check `tenant_settings_timezone_chk`: `CHECK (((length(timezone) <= 64) AND (timezone ~ '^(UTC|[A-Z][A-Za-z_]+(/[A-Za-z0-9_+-]+){1,2})$'::text)))`
- check `tenant_settings_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `tenant_settings_trash_days_chk`: `CHECK (((trash_days >= 1) AND (trash_days <= 30)))`
- check `tenant_settings_validation_level_chk`: `CHECK ((booking_validation_level = ANY (ARRAY['off'::text, 'basic'::text, 'strict'::text])))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `tenant_settings_set_updated_at`: BEFORE UPDATE ON crm.tenant_settings FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.traveler` (table, ~51 rows, 200 kB)
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
- check `traveler_archive_chk`: `CHECK ((((archive_reason IS NULL) OR (archived_at IS NOT NULL)) AND ((archive_reason IS NULL) OR (archive_reason ~ '^[a-z][a-z0-9_]{0,39}$'::text))))`
- check `traveler_archive_reason_chk`: `CHECK ((((archived_at IS NULL) = (archive_reason IS NULL)) AND ((archived_at IS NULL) = (archived_by IS NULL)) AND ((archive_reason IS NULL) OR (archive_reason = ANY (ARRAY['agent'::text, 'client_request'::text, 'auto_inactive'::text, 'duplicate'::text, 'other'::text]))) AND ((archived_by IS NULL) OR (archived_by ~ '^[A-Za-z0-9:_-]{1,80}$'::text))))`
- check `traveler_bidx_chk`: `CHECK (((COALESCE(octet_length(email_bidx), 16) = 16) AND (COALESCE(octet_length(phone_bidx), 16) = 16) AND (COALESCE(octet_length(name_bidx), 8) = 8) AND (array_position(name_token_bidx, NULL::bytea) IS NULL) AND (COALESCE(cardinality(name_token_bidx), 0) <= 16)))`
- check `traveler_bidx_pairs_chk`: `CHECK ((((email_bidx IS NULL) = (email_enc IS NULL)) AND ((phone_bidx IS NULL) = (phone_enc IS NULL))))`
- check `traveler_channel_chk`: `CHECK (((preferred_channel IS NULL) OR (preferred_channel = ANY (ARRAY['email'::text, 'phone'::text, 'sms'::text, 'whatsapp'::text]))))`
- check `traveler_enc_chk`: `CHECK (((octet_length(display_name_enc) >= 30) AND (COALESCE(octet_length(given_name_enc), 30) >= 30) AND (COALESCE(octet_length(family_name_enc), 30) >= 30) AND (COALESCE(octet_length(email_enc), 30) >= 30) AND (COALESCE(octet_length(phone_enc), 30) >= 30) AND (COALESCE(octet_length(dob_enc), 30) >= 30) AND (COALESCE(octet_length(nationality_enc), 30) >= 30) AND (COALESCE(octet_length(passport_no_enc), 30) >= 30) AND (COALESCE(octet_length(passport_expiry_enc), 30) >= 30) AND (COALESCE(octet_length(passport_country_enc), 30) >= 30) AND (COALESCE(octet_length(emergency_contact_enc), 30) >= 30) AND (COALESCE(octet_length(profile_token_enc), 30) >= 30)))`
- check `traveler_lead_source_chk`: `CHECK (((lead_source IS NULL) OR (lead_source ~ '^[a-z][a-z0-9_]{0,39}$'::text)))`
- check `traveler_referrer_chk`: `CHECK ((referrer_traveler_id IS DISTINCT FROM traveler_id))`
- check `traveler_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `traveler_hold_guard`: BEFORE DELETE OR UPDATE ON crm.traveler FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('referrer_traveler_id', 'profile_token_enc')
- trigger `traveler_set_updated_at`: BEFORE UPDATE ON crm.traveler FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.traveler_access` (table, 112 kB)
```
access_id uuid NN
tenant_id uuid NN
trip_id uuid NN
traveler_id uuid NN
role text NN
link_id uuid
status text NN
last_sign_in_at timestamp with time zone
stage3_submitted_at timestamp with time zone
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
deleted_at timestamp with time zone
deleted_by text
purge_after timestamp with time zone
```
- owner `crm_owner` · RLS on + FORCE
- index `traveler_access_link_idx`: btree (tenant_id, link_id) WHERE (link_id IS NOT NULL)
- index `traveler_access_live_uq`: UNIQUE btree (tenant_id, trip_id, traveler_id) WHERE ((status <> 'revoked'::text) AND (deleted_at IS NULL))
- index `traveler_access_pkey` PRIMARY KEY: UNIQUE btree (access_id)
- index `traveler_access_subject_uq`: UNIQUE btree (tenant_id, access_id, trip_id, traveler_id)
- index `traveler_access_tenant_id_uq`: UNIQUE btree (tenant_id, access_id)
- index `traveler_access_traveler_idx`: btree (traveler_id)
- check `traveler_access_role_chk`: `CHECK ((role = ANY (ARRAY['lead'::text, 'companion'::text])))`
- check `traveler_access_sign_in_chk`: `CHECK (((status <> 'active'::text) OR (last_sign_in_at IS NOT NULL)))`
- check `traveler_access_status_chk`: `CHECK ((status = ANY (ARRAY['invited'::text, 'active'::text, 'revoked'::text])))`
- check `traveler_access_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `traveler_access_hold_guard`: BEFORE DELETE OR UPDATE ON crm.traveler_access FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_id')
- trigger `traveler_access_set_updated_at`: BEFORE UPDATE ON crm.traveler_access FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `traveler_access_stage3_guard`: BEFORE INSERT OR UPDATE ON crm.traveler_access FOR EACH ROW EXECUTE FUNCTION crm.guard_traveler_access()
- trigger `traveler_access_status_transition`: BEFORE UPDATE OF status ON crm.traveler_access FOR EACH ROW EXECUTE FUNCTION crm.enforce_status_transition()

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
- check `traveler_health_enc_chk`: `CHECK ((octet_length(health_flags_enc) >= 30))`
- check `traveler_health_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `traveler_health_consent`: BEFORE INSERT OR UPDATE OF consent_id, traveler_id ON crm.traveler_health FOR EACH ROW EXECUTE FUNCTION crm.traveler_health_consent()
- trigger `traveler_health_hold_guard`: BEFORE DELETE OR UPDATE ON crm.traveler_health FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('traveler_id')
- trigger `traveler_health_set_updated_at`: BEFORE UPDATE ON crm.traveler_health FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.traveler_profile` (table, ~56 rows, 80 kB)
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
- check `traveler_profile_bands_chk`: `CHECK ((((residence_country IS NULL) OR (residence_country ~ '^[A-Z]{2}$'::text)) AND ((fitness_band IS NULL) OR (fitness_band = ANY (ARRAY['up_to_2h'::text, '2_4h'::text, '4_6h'::text, 'over_6h'::text]))) AND ((trek_experience IS NULL) OR (trek_experience = ANY (ARRAY['none'::text, 'some'::text, 'experienced'::text]))) AND ((accommodation_tier IS NULL) OR (accommodation_tier = ANY (ARRAY['budget'::text, 'comfort'::text, 'premium'::text, 'luxury'::text]))) AND ((occasion IS NULL) OR (occasion = ANY (ARRAY['none'::text, 'honeymoon'::text, 'anniversary'::text, 'birthday'::text, 'family_reunion'::text, 'graduation'::text, 'retirement'::text, 'other'::text]))) AND ((budget_flex IS NULL) OR (budget_flex = ANY (ARRAY['fixed'::text, 'some'::text, 'flexible'::text]))) AND ((decision_maker IS NULL) OR (decision_maker = ANY (ARRAY['self'::text, 'partner'::text, 'family'::text, 'group'::text, 'company'::text]))) AND ((booking_timeline IS NULL) OR (booking_timeline = ANY (ARRAY['ready_now'::text, 'within_month'::text, 'within_3_months'::text, 'later'::text, 'just_looking'::text])))))`
- check `traveler_profile_budget_chk`: `CHECK (((budget_band IS NULL) OR (budget_band = ANY (ARRAY['under_1000'::text, '1000_2000'::text, '2000_3500'::text, '3500_5000'::text, 'over_5000'::text, 'not_sure'::text]))))`
- check `traveler_profile_codes_chk`: `CHECK (((cardinality(interests) <= 20) AND (array_to_string(interests, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{1,39}(,|$))*$'::text) AND (cardinality(must_do_codes) <= 20) AND (array_to_string(must_do_codes, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{1,39}(,|$))*$'::text) AND (cardinality(must_avoid_codes) <= 20) AND (array_to_string(must_avoid_codes, ','::text, '!'::text) ~ '^([a-z][a-z0-9_]{1,39}(,|$))*$'::text) AND (dietary_flags <@ ARRAY['vegetarian'::text, 'vegan'::text, 'halal'::text, 'kosher'::text, 'gluten_free'::text, 'lactose_free'::text, 'nut_allergy'::text, 'shellfish_allergy'::text, 'other_allergy'::text]) AND (array_position(dietary_flags, NULL::text) IS NULL) AND (mobility_flags <@ ARRAY['limited_walking'::text, 'wheelchair'::text, 'no_stairs'::text, 'no_long_drives'::text, 'other'::text]) AND (array_position(mobility_flags, NULL::text) IS NULL)))`
- check `traveler_profile_group_chk`: `CHECK (((group_pref IS NULL) OR (group_pref = ANY (ARRAY['private'::text, 'small_group'::text]))))`
- check `traveler_profile_pace_chk`: `CHECK (((pace IS NULL) OR (pace = ANY (ARRAY['relaxed'::text, 'balanced'::text, 'adventure'::text]))))`
- check `traveler_profile_repeat_chk`: `CHECK (((repeat_count >= 0) AND (repeat_count <= 10000)))`
- check `traveler_profile_s2_chk`: `CHECK (((stage2_completeness >= 0) AND (stage2_completeness <= 100)))`
- check `traveler_profile_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
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
- check `traveler_relation_kind_chk`: `CHECK ((kind = ANY (ARRAY['spouse'::text, 'partner'::text, 'parent'::text, 'child'::text, 'sibling'::text, 'friend'::text, 'referrer'::text, 'referred'::text])))`
- check `traveler_relation_self_chk`: `CHECK ((from_traveler_id <> to_traveler_id))`
- check `traveler_relation_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `traveler_relation_fixed`: BEFORE UPDATE ON crm.traveler_relation FOR EACH ROW EXECUTE FUNCTION crm.traveler_relation_pair()
- trigger `traveler_relation_hold_guard`: BEFORE DELETE OR UPDATE ON crm.traveler_relation FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('from_traveler_id', 'to_traveler_id', 'kind')
- trigger `traveler_relation_mirror`: AFTER INSERT OR DELETE OR UPDATE OF deleted_at ON crm.traveler_relation FOR EACH ROW EXECUTE FUNCTION crm.traveler_relation_mirror()
- trigger `traveler_relation_set_updated_at`: BEFORE UPDATE ON crm.traveler_relation FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.trip` (table, ~57 rows, 176 kB)
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
intake_completeness jsonb NN
cancel_reason_code text
last_activity_at timestamp with time zone NN
mail_token text NN
```
- owner `crm_owner` · RLS on + FORCE
- index `trip_board_idx`: btree (tenant_id, stage, last_inquiry_at DESC) WHERE (deleted_at IS NULL)
- index `trip_date_rule_idx`: btree (tenant_id, stage, start_date) WHERE ((deleted_at IS NULL) AND (stage = ANY (ARRAY['booked'::text, 'pre_departure'::text, 'travelling'::text])))
- index `trip_mail_token_uq`: UNIQUE btree (tenant_id, mail_token)
- index `trip_owner_idx`: btree (owner_member_id) WHERE (owner_member_id IS NOT NULL)
- index `trip_pkey` PRIMARY KEY: UNIQUE btree (trip_id)
- index `trip_quiet_idx`: btree (tenant_id, stage, last_activity_at) WHERE (deleted_at IS NULL)
- index `trip_tenant_id_uq`: UNIQUE btree (tenant_id, trip_id)
- check `trip_budget_chk`: `CHECK (((budget_band IS NULL) OR (budget_band = ANY (ARRAY['under_1000'::text, '1000_2000'::text, '2000_3500'::text, '3500_5000'::text, 'over_5000'::text, 'not_sure'::text]))))`
- check `trip_cancel_reason_chk`: `CHECK ((((stage = 'cancelled'::text) = (cancel_reason_code IS NOT NULL)) AND ((cancel_reason_code IS NULL) OR (cancel_reason_code = ANY (ARRAY['client_request'::text, 'client_illness'::text, 'travel_advisory'::text, 'force_majeure'::text, 'supplier_failure'::text, 'aa_cancelled'::text, 'payment_not_received'::text, 'duplicate'::text, 'other'::text])))))`
- check `trip_dates_chk`: `CHECK ((((start_date IS NULL) OR (end_date IS NULL) OR (end_date >= start_date)) AND ((month IS NULL) OR (month = (date_trunc('month'::text, (month)::timestamp with time zone))::date))))`
- check `trip_destinations_chk`: `CHECK (((cardinality(destinations) <= 12) AND (array_to_string(destinations, ','::text, '!'::text) ~ '^([a-z][a-z_]{1,39}(,|$))*$'::text)))`
- check `trip_flex_chk`: `CHECK (((date_flex_days >= 0) AND (date_flex_days <= 60)))`
- check `trip_intake_completeness_chk`: `CHECK (crm.completeness_ok(intake_completeness))`
- check `trip_lead_source_chk`: `CHECK (((lead_source IS NULL) OR (lead_source ~ '^[a-z][a-z0-9_]{0,39}$'::text)))`
- check `trip_lost_reason_chk`: `CHECK ((((stage = 'lost'::text) = (lost_reason_code IS NOT NULL)) AND ((lost_reason_code IS NULL) OR (lost_reason_code = ANY (ARRAY['price'::text, 'price_aa_tour'::text, 'aa_sold_out'::text, 'aa_on_request_declined'::text, 'dates_changed'::text, 'went_elsewhere'::text, 'no_response'::text, 'postponed'::text, 'other'::text])))))`
- check `trip_mail_token_chk`: `CHECK ((mail_token ~ '^[a-z0-9]{8,16}$'::text))`
- check `trip_nights_chk`: `CHECK (((nights IS NULL) OR ((nights >= 1) AND (nights <= 90))))`
- check `trip_party_chk`: `CHECK ((((party_adults >= 1) AND (party_adults <= 50)) AND (cardinality(party_child_ages) <= 20) AND ((cardinality(party_child_ages) = 0) OR ((0 <= ALL (party_child_ages)) AND (17 >= ALL (party_child_ages))))))`
- check `trip_party_type_chk`: `CHECK (((party_type IS NULL) OR (party_type = ANY (ARRAY['solo'::text, 'couple'::text, 'family'::text, 'friends'::text, 'group'::text]))))`
- check `trip_stage_chk`: `CHECK ((stage = ANY (ARRAY['inquiry'::text, 'qualifying'::text, 'proposal'::text, 'booked'::text, 'pre_departure'::text, 'travelling'::text, 'completed'::text, 'lost'::text, 'cancelled'::text])))`
- check `trip_style_chk`: `CHECK (((trip_style IS NULL) OR (trip_style = ANY (ARRAY['relaxed'::text, 'balanced'::text, 'adventure'::text]))))`
- check `trip_title_chk`: `CHECK (((length(btrim(title)) >= 1) AND (length(btrim(title)) <= 120)))`
- check `trip_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- check `trip_waiting_on_chk`: `CHECK ((waiting_on = ANY (ARRAY['agency'::text, 'client'::text, 'aa'::text, 'supplier'::text, 'none'::text])))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `trip_hold_guard`: BEFORE DELETE OR UPDATE ON crm.trip FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change()
- trigger `trip_set_updated_at`: BEFORE UPDATE ON crm.trip FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()
- trigger `trip_stage_transition`: BEFORE UPDATE OF stage ON crm.trip FOR EACH ROW EXECUTE FUNCTION crm.enforce_stage_transition()

### `crm.trip_commitment` (table, 64 kB)
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
- check `trip_commitment_kind_status_chk`: `CHECK ((((kind = 'aa_line'::text) AND (line_status = ANY (ARRAY['requested'::text, 'held'::text, 'confirmed'::text, 'released'::text, 'expired'::text, 'cancelled'::text, 'declined'::text]))) OR ((kind = 'invoice'::text) AND (line_status = ANY (ARRAY['draft'::text, 'open'::text, 'payment_claimed'::text, 'paid'::text, 'paid_unfulfillable'::text, 'void'::text, 'expired'::text]))) OR ((kind = 'payment'::text) AND (line_status = ANY (ARRAY['pending'::text, 'succeeded'::text, 'failed'::text, 'refunded'::text]))) OR ((kind = 'signature'::text) AND (line_status = ANY (ARRAY['pending'::text, 'signed'::text, 'declined'::text, 'expired'::text]))) OR ((kind = 'commission'::text) AND (line_status = ANY (ARRAY['expected'::text, 'claimed'::text, 'received'::text, 'cancelled'::text])))))`
- check `trip_commitment_source_chk`: `CHECK ((source_ref ~ '^[A-Za-z0-9:_.-]{1,80}$'::text))`
- check `trip_commitment_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `trip_commitment_set_updated_at`: BEFORE UPDATE ON crm.trip_commitment FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.trip_party` (table, ~51 rows, 96 kB)
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
- check `trip_party_age_band_chk`: `CHECK (((age_band_at_departure IS NULL) OR (age_band_at_departure ~ '^[a-z0-9_]{1,20}$'::text)))`
- check `trip_party_age_band_list_chk`: `CHECK (((age_band_at_departure IS NULL) OR (age_band_at_departure = ANY (ARRAY['under_2'::text, '2_11'::text, '12_17'::text, '18_24'::text, '25_34'::text, '35_44'::text, '45_54'::text, '55_64'::text, '65_74'::text, '75_plus'::text]))))`
- check `trip_party_role_chk`: `CHECK ((role = ANY (ARRAY['lead'::text, 'companion'::text])))`
- check `trip_party_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
- grant `crm_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `trip_party_hold_guard`: BEFORE DELETE OR UPDATE ON crm.trip_party FOR EACH ROW EXECUTE FUNCTION crm.guard_held_change('trip_id', 'traveler_token')
- trigger `trip_party_set_updated_at`: BEFORE UPDATE ON crm.trip_party FOR EACH ROW EXECUTE FUNCTION crm.set_updated_at()

### `crm.trip_stage_history` (table, ~161 rows, 168 kB)
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
override_reason_code text
undo_of uuid
batch_id uuid
```
- owner `crm_owner` · RLS on + FORCE
- index `trip_stage_history_batch_idx`: btree (tenant_id, batch_id) WHERE (batch_id IS NOT NULL)
- index `trip_stage_history_pkey` PRIMARY KEY: UNIQUE btree (history_id)
- index `trip_stage_history_tenant_id_uq`: UNIQUE btree (tenant_id, history_id)
- index `trip_stage_history_trip_idx`: btree (trip_id, at)
- check `trip_stage_history_override_chk`: `CHECK (((override = (override_reason_code IS NOT NULL)) AND ((override_reason_code IS NULL) OR (override_reason_code = ANY (ARRAY['client_in_hurry'::text, 'repeat_client'::text, 'info_by_phone'::text, 'manual_booking'::text, 'manual_stage3'::text, 'other'::text])))))`
- check `trip_stage_history_reason_chk`: `CHECK ((reason_code ~ '^[a-z][a-z0-9_]{0,39}$'::text))`
- check `trip_stage_history_stage_chk`: `CHECK (((to_stage ~ '^[a-z_]{3,20}$'::text) AND ((from_stage IS NULL) OR (from_stage ~ '^[a-z_]{3,20}$'::text))))`
- check `trip_stage_history_undo_chk`: `CHECK (((undo_of IS NULL) OR ((reason_code = 'undo'::text) AND (undo_of <> history_id) AND (override_reason_code IS NULL))))`
- grant `crm_app`: INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO crm_ai_reader, crm_app, crm_eraser, crm_insights, crm_owner, crm_support_reader): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)` WITH CHECK `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `trip_stage_history_append_only`: BEFORE DELETE OR UPDATE ON crm.trip_stage_history FOR EACH ROW EXECUTE FUNCTION crm.erasable_append_only()
- trigger `trip_stage_history_no_truncate`: BEFORE TRUNCATE ON crm.trip_stage_history FOR EACH STATEMENT EXECUTE FUNCTION crm.erasable_append_only()
- trigger `trip_stage_history_pin_insert`: BEFORE INSERT ON crm.trip_stage_history FOR EACH ROW EXECUTE FUNCTION crm.pin_stage_history_insert()

### `crm.trip_traveler` (table, ~45 rows, 112 kB)
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
- check `trip_traveler_portal_chk`: `CHECK ((portal_access = ANY (ARRAY['lead'::text, 'companion'::text, 'none'::text])))`
- check `trip_traveler_role_chk`: `CHECK ((role = ANY (ARRAY['lead'::text, 'companion'::text])))`
- check `trip_traveler_trash_chk`: `CHECK ((((deleted_at IS NULL) = (deleted_by IS NULL)) AND ((deleted_at IS NULL) = (purge_after IS NULL))))`
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

### `crm.v_booking_line_money_current` (VIEW)
```
booking_line_money_id uuid
tenant_id uuid
booking_line_id uuid
kind text
amount numeric(14,2)
currency character(3)
base_currency character(3)
amount_base numeric(14,2)
fx_rate numeric(20,10)
fx_rate_date date
fx_source text
fx_basis text
stale_days smallint
supersedes_id uuid
created_at timestamp with time zone
created_by text
```
- owner `crm_owner`
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

## `geo` (18 objects)

### `geo.component_redirect` (table, 64 kB)
```
old_id uuid NN
new_id uuid NN
source_id text NN
rule text NN
created_at timestamp with time zone NN
```
- owner `cis_owner`
- index `component_redirect_new_idx`: btree (new_id)
- index `component_redirect_pkey` PRIMARY KEY: UNIQUE btree (old_id)
- index `component_redirect_source_idx`: btree (source_id)
- check `component_redirect_not_self_chk`: `CHECK ((old_id <> new_id))`
- check `component_redirect_rule_chk`: `CHECK ((rule = ANY (ARRAY['destination'::text, 'card'::text, 'spelling'::text, 'link_name'::text])))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.geocode_call` (table, ~49 rows, 80 kB)
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
- check `geocode_call_credits_chk`: `CHECK (((credits IS NULL) OR (credits >= 0)))`
- check `geocode_call_endpoint_chk`: `CHECK ((endpoint = ANY (ARRAY['search'::text, 'place_details'::text, 'overpass'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.graph_build` (table, ~3 rows, 104 kB)
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

### `geo.graph_edge` (table, ~8469 rows, 3.4 MB)
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

### `geo.graph_node` (table, ~5415 rows, 3.3 MB)
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
- check `place_dedupe_country_apply_chk`: `CHECK (((mode <> 'apply'::text) OR (approved_diff_hash IS NOT NULL)))`
- check `place_dedupe_country_mode_chk`: `CHECK ((mode = ANY (ARRAY['dry_run'::text, 'apply'::text])))`
- check `place_dedupe_country_norm_chk`: `CHECK (((country = lower(btrim(country))) AND (country <> ''::text)))`
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
- check `place_merge_decided_by_chk`: `CHECK ((decided_by = ANY (ARRAY['provider_id'::text, 'osm_id'::text, 'place_card'::text, 'line_overlap'::text, 'rule'::text, 'llm'::text, 'admin'::text])))`
- check `place_merge_not_self_chk`: `CHECK ((merged_id <> keeper_id))`
- check `place_merge_undo_chk`: `CHECK ((((undone_at IS NULL) = (undone_by IS NULL)) AND ((undone_at IS NULL) OR (undo_reason IS NOT NULL))))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.place_name` (table, ~9545 rows, 2.9 MB)
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
- check `place_name_status_check`: `CHECK ((status = ANY (ARRAY['pending'::text, 'resolved'::text, 'unknown'::text, 'suspect'::text])))`
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
- check `place_pair_verdict_cost_chk`: `CHECK ((cost_usd >= (0)::numeric))`
- check `place_pair_verdict_order_chk`: `CHECK ((lo_id < hi_id))`
- check `place_pair_verdict_pin_chk`: `CHECK (((source = 'model'::text) = (input_hash <> '*'::text)))`
- check `place_pair_verdict_source_chk`: `CHECK ((source = ANY (ARRAY['model'::text, 'undo'::text, 'admin'::text, 'recheck'::text])))`
- check `place_pair_verdict_verdict_chk`: `CHECK ((verdict = ANY (ARRAY['same'::text, 'different'::text, 'unsure'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.place_shape` (table, ~284 rows, 1.4 MB)
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
- check `place_shape_bbox_chk`: `CHECK ((((min_lat >= ('-90'::integer)::double precision) AND (min_lat <= (90)::double precision)) AND ((max_lat >= ('-90'::integer)::double precision) AND (max_lat <= (90)::double precision)) AND (min_lat <= max_lat) AND ((min_lng >= ('-180'::integer)::double precision) AND (min_lng <= (180)::double precision)) AND ((max_lng >= ('-180'::integer)::double precision) AND (max_lng <= (180)::double precision)) AND (min_lng <= max_lng)))`
- check `place_shape_drawn_chk`: `CHECK (((status = ANY (ARRAY['ok'::text, 'approximate'::text, 'manual'::text])) = ((geom IS NOT NULL) AND (geom_mid IS NOT NULL) AND (geom_lo IS NOT NULL) AND (source IS NOT NULL) AND (length_km IS NOT NULL))))`
- check `place_shape_geom_chk`: `CHECK (((geom IS NULL) OR (((geom ->> 'type'::text) = ANY (ARRAY['LineString'::text, 'MultiLineString'::text])) AND ((geo.line_vertex_count(geom) >= 2) AND (geo.line_vertex_count(geom) <= 2000)))))`
- check `place_shape_geom_lo_chk`: `CHECK (((geom_lo IS NULL) OR (((geom_lo ->> 'type'::text) = ANY (ARRAY['LineString'::text, 'MultiLineString'::text])) AND ((geo.line_vertex_count(geom_lo) >= 2) AND (geo.line_vertex_count(geom_lo) <= 60)))))`
- check `place_shape_geom_mid_chk`: `CHECK (((geom_mid IS NULL) OR (((geom_mid ->> 'type'::text) = ANY (ARRAY['LineString'::text, 'MultiLineString'::text])) AND ((geo.line_vertex_count(geom_mid) >= 2) AND (geo.line_vertex_count(geom_mid) <= 300)) AND (octet_length((geom_mid)::text) <= 12288))))`
- check `place_shape_kind_chk`: `CHECK ((kind = ANY (ARRAY['line'::text, 'area'::text])))`
- check `place_shape_length_chk`: `CHECK (((length_km IS NULL) OR (length_km >= (0)::numeric)))`
- check `place_shape_osm_chk`: `CHECK ((((osm_type IS NULL) = (osm_id IS NULL)) AND ((osm_type IS NULL) OR (osm_type = ANY (ARRAY['node'::text, 'way'::text, 'relation'::text])))))`
- check `place_shape_source_chk`: `CHECK (((source IS NULL) OR (source = ANY (ARRAY['geoapify_details'::text, 'overpass'::text, 'anchors'::text, 'manual'::text]))))`
- check `place_shape_status_chk`: `CHECK ((status = ANY (ARRAY['pending'::text, 'ok'::text, 'approximate'::text, 'not_found'::text, 'failed'::text, 'manual'::text])))`
- check `place_shape_status_source_chk`: `CHECK ((((status = 'approximate'::text) = (NOT (source IS DISTINCT FROM 'anchors'::text))) AND ((status = 'manual'::text) = (NOT (source IS DISTINCT FROM 'manual'::text)))))`
- check `place_shape_tries_chk`: `CHECK ((tries >= 0))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_build` (table, ~892 rows, 1.1 MB)
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
- check `tour_build_status_check`: `CHECK ((status = ANY (ARRAY['pending'::text, 'ok'::text, 'partial'::text, 'failed'::text, 'retired'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_day` (table, ~6996 rows, 2.8 MB)
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
- check `tour_day_extracted_by_check`: `CHECK ((extracted_by = ANY (ARRAY['rule'::text, 'llm'::text, 'rule+llm'::text])))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_junction` (table, ~228082 rows, 60.1 MB)
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

### `geo.tour_leg` (table, ~96906 rows, 68.4 MB)
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

### `geo.tour_place` (table, ~13500 rows, 216.1 MB)
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
- check `tour_place_activity_check`: `CHECK ((activity = ANY (ARRAY['trekking'::text, 'cultural_heritage'::text, 'wildlife_nature'::text, 'water_activities'::text, 'culinary'::text, 'wellness_relaxation'::text, 'adventure_sport'::text, 'local_immersion'::text])))`
- check `tour_place_duration_hint_check`: `CHECK ((duration_hint = ANY (ARRAY['half_day'::text, 'full_day'::text, 'overnight'::text, 'multi_night'::text])))`
- check `tour_place_intensity_level_check`: `CHECK ((intensity_level = ANY (ARRAY['leisurely'::text, 'moderate'::text, 'active'::text, 'strenuous'::text])))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_segment` (table, ~1230 rows, 1.8 MB)
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
- check `tour_segment_basis_chk`: `CHECK ((basis = ANY (ARRAY['day_anchors'::text, 'anchor_window'::text, 'feature'::text])))`
- check `tour_segment_feature_chk`: `CHECK ((((basis = 'feature'::text) = (segment IS NULL)) AND ((segment IS NULL) = (segment_km IS NULL))))`
- check `tour_segment_km_chk`: `CHECK (((segment_km IS NULL) OR (segment_km >= (0)::numeric)))`
- check `tour_segment_segment_chk`: `CHECK (((segment IS NULL) OR (((segment ->> 'type'::text) = 'LineString'::text) AND ((geo.line_vertex_count(segment) >= 2) AND (geo.line_vertex_count(segment) <= 300)))))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `geo.tour_stop` (table, ~19521 rows, 8 MB)
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
- check `tour_stop_source_check`: `CHECK ((source = ANY (ARRAY['overnight'::text, 'component'::text])))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

## `gold_aa_internal` (9 objects)

### `gold_aa_internal.aa_content_item` (table, ~28 rows, 48 kB)
```
content_id uuid NN
kind text NN
locale text NN
group_key text NN
retired_at timestamp with time zone
retired_by text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `aa_content_item_group_locale_key`: UNIQUE btree (group_key, locale)
- index `aa_content_item_pkey` PRIMARY KEY: UNIQUE btree (content_id)
- check `aa_content_item_actor_check`: `CHECK ((((char_length(created_by) >= 1) AND (char_length(created_by) <= 64)) AND ((retired_by IS NULL) OR ((char_length(retired_by) >= 1) AND (char_length(retired_by) <= 64)))))`
- check `aa_content_item_group_key_check`: `CHECK ((group_key ~ '^[a-z0-9][a-z0-9-]{1,79}$'::text))`
- check `aa_content_item_kind_check`: `CHECK ((kind = ANY (ARRAY['prep_pack'::text, 'starter_template'::text, 'campaign_block'::text])))`
- check `aa_content_item_locale_check`: `CHECK ((locale = ANY (ARRAY['en'::text, 'vi'::text])))`
- check `aa_content_item_retired_check`: `CHECK (((retired_at IS NULL) = (retired_by IS NULL)))`
- grant `cis_app`: INSERT, SELECT, UPDATE
- trigger `aa_content_item_guard`: BEFORE UPDATE ON gold_aa_internal.aa_content_item FOR EACH ROW EXECUTE FUNCTION gold_aa_internal.aa_content_item_guard()

### `gold_aa_internal.aa_content_version` (table, ~28 rows, 144 kB)
```
content_id uuid NN
version integer NN
status text NN
title text NN
body_markdown text NN
applies_to jsonb NN
content_hash text
published_at timestamp with time zone
published_by text
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `aa_content_version_one_draft_idx`: UNIQUE btree (content_id) WHERE (status = 'draft'::text)
- index `aa_content_version_pkey` PRIMARY KEY: UNIQUE btree (content_id, version)
- index `aa_content_version_published_idx`: btree (content_id, version DESC) WHERE (status = 'published'::text)
- check `aa_content_version_actor_check`: `CHECK ((((char_length(created_by) >= 1) AND (char_length(created_by) <= 64)) AND ((published_by IS NULL) OR ((char_length(published_by) >= 1) AND (char_length(published_by) <= 64)))))`
- check `aa_content_version_applies_to_check`: `CHECK (((jsonb_typeof(applies_to) = 'object'::text) AND (((applies_to - 'country_codes'::text) - 'tours'::text) = '{}'::jsonb)))`
- check `aa_content_version_body_check`: `CHECK ((char_length(body_markdown) <= 20000))`
- check `aa_content_version_hash_check`: `CHECK (((content_hash IS NULL) OR (content_hash ~ '^sha256:[0-9a-f]{64}$'::text)))`
- check `aa_content_version_published_check`: `CHECK (
CASE status
    WHEN 'draft'::text THEN ((content_hash IS NULL) AND (published_at IS NULL) AND (published_by IS NULL))
    ELSE ((content_hash IS NOT NULL) AND (published_at IS NOT NULL) AND (published_by IS NOT NULL))
END)`
- check `aa_content_version_status_check`: `CHECK ((status = ANY (ARRAY['draft'::text, 'published'::text])))`
- check `aa_content_version_title_check`: `CHECK (((char_length(title) >= 1) AND (char_length(title) <= 300)))`
- check `aa_content_version_version_check`: `CHECK ((version >= 1))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `aa_content_version_guard`: BEFORE INSERT OR DELETE OR UPDATE ON gold_aa_internal.aa_content_version FOR EACH ROW EXECUTE FUNCTION gold_aa_internal.aa_content_version_guard()

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
- check `published_tours_master_status_reason_check`: `CHECK (((master_status_reason IS NULL) OR (master_status_reason = ANY (ARRAY['staff_deactivated'::text, 'staff_trashed'::text, 'source_deleted'::text, 'superseded'::text]))))`
- grant `aa_app_user`: SELECT
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `aa_app_user_aa_master_read` (PERMISSIVE SELECT TO aa_app_user): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `catalog_owner_aa_master_read` (PERMISSIVE SELECT TO catalog_owner): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `published_tours_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `published_tours_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `gold_aa_internal.tenant_tour_versions` (table, ~53 rows, 680 kB)
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
generation_meta jsonb
judge_breakdown jsonb
```
- owner `cis_owner` · RLS on
- index `idx_ttv_created`: btree (tenant_id, created_at DESC)
- index `idx_ttv_published_tour`: btree (published_tour_id)
- index `idx_ttv_status`: btree (tenant_id, status)
- index `idx_ttv_tenant_id`: btree (tenant_id)
- index `tenant_tour_versions_job_idx`: btree (job_id) WHERE (job_id IS NOT NULL)
- index `tenant_tour_versions_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `tenant_tour_versions_tenant_id_published_tour_id_version_nu_key`: UNIQUE btree (tenant_id, published_tour_id, version_number)
- check `tenant_tour_versions_edit_source_check`: `CHECK ((edit_source = ANY (ARRAY['ai_generated'::text, 'tenant_edit'::text, 're_rewrite'::text])))`
- check `tenant_tour_versions_qa_status_check`: `CHECK ((qa_status = ANY (ARRAY['pending'::text, 'passed'::text, 'failed'::text, 'escalated'::text])))`
- check `tenant_tour_versions_status_check`: `CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, 'needs_review'::text, 'ai_generated'::text, 'failed'::text])))`
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
- check `tour_lifecycle_event_event_check`: `CHECK ((event = ANY (ARRAY['retired'::text, 'paused'::text, 'restored'::text, 'superseded'::text])))`
- check `tour_lifecycle_event_reason_check`: `CHECK ((reason = ANY (ARRAY['source_deleted'::text, 'master_trashed'::text, 'superseded_orphan'::text, 'master_inactive'::text, 'superseded_pending'::text, 'replaced'::text, 'restore'::text, 'publish'::text, 'activate'::text, 'set_active'::text])))`
- check `tour_lifecycle_event_source_system_check`: `CHECK ((source_system = 'cis'::text))`
- check `tour_lifecycle_event_successor_check`: `CHECK (((event = 'superseded'::text) = (replaced_by_tour_id IS NOT NULL)))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: INSERT, SELECT
- trigger `tour_lifecycle_event_append_only`: BEFORE DELETE OR UPDATE ON gold_aa_internal.tour_lifecycle_event FOR EACH ROW EXECUTE FUNCTION gold_aa_internal.tour_lifecycle_event_append_only()

### `gold_aa_internal.v_aa_content_published` (VIEW)
```
content_id uuid
kind text
locale text
group_key text
version integer
title text
body_markdown text
applies_to jsonb
published_at timestamp with time zone
content_hash text
retired_at timestamp with time zone
```
- owner `cis_owner`
- grant `cis_app`: SELECT

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

## `shared` (63 objects)

### `shared.admin_users` (table, ~11 rows, 80 kB)
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
- check `admin_users_cognito_pair_chk`: `CHECK ((((cognito_iss IS NULL) AND (cognito_sub IS NULL)) OR ((cognito_iss IS NOT NULL) AND (cognito_sub IS NOT NULL) AND (cognito_iss ~~ 'https://%'::text) AND ((length(cognito_sub) >= 1) AND (length(cognito_sub) <= 128)))))`
- check `admin_users_email_chk`: `CHECK (((email IS NULL) OR ((email = lower(email)) AND (email ~ '^[^@[:space:]]+@adventure[.]asia$'::text)) OR ((email = 'e2e@e2e-mail.lumiguides.it.com'::text) AND (role = 'reviewer'::shared.admin_role) AND (NOT is_owner) AND (password_hash IS NULL)) OR ((email = 'e2e-cis-admin@e2e-mail.lumiguides.it.com'::text) AND (role = 'admin'::shared.admin_role) AND (NOT is_owner) AND (password_hash IS NULL))))`
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
- check `alert_recipient_email_chk`: `CHECK (((email = lower(email)) AND (length(email) <= 254) AND (email ~ '^[^@[:space:],;<>"]+@[^@[:space:],;<>"]+\.[^@[:space:],;<>"]+$'::text)))`
- check `alert_recipient_note_chk`: `CHECK (((note IS NULL) OR (length(note) <= 80)))`
- check `alert_recipient_removed_chk`: `CHECK ((((status = 'removed'::text) = (removed_at IS NOT NULL)) AND ((status = 'removed'::text) = (removed_reason IS NOT NULL)) AND ((removed_reason IS NULL) OR (removed_reason = ANY (ARRAY['admin'::text, 'unsubscribed'::text, 'expired'::text])))))`
- check `alert_recipient_seen_chk`: `CHECK (((last_seen_state IS NULL) OR (last_seen_state = ANY (ARRAY['confirmed'::text, 'pending'::text, 'missing'::text]))))`
- check `alert_recipient_status_chk`: `CHECK ((status = ANY (ARRAY['pending'::text, 'confirmed'::text, 'removed'::text])))`
- grant `cis_app`: INSERT, SELECT, UPDATE

### `shared.cost_explorer_app_snapshot` (table, ~10118 rows, 2.4 MB)
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

### `shared.cost_explorer_snapshot` (table, ~2766 rows, 2 MB)
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

### `shared.countries` (table, ~249 rows, 128 kB)
```
iso2 character(2) NN
iso3 character(3) NN
numeric_code character(3) NN
name text NN
iso_name text NN
aliases text[] NN
```
- owner `cis_owner`
- index `countries_iso3_key`: UNIQUE btree (iso3)
- index `countries_name_key`: UNIQUE btree (name)
- index `countries_numeric_code_key`: UNIQUE btree (numeric_code)
- index `countries_pkey` PRIMARY KEY: UNIQUE btree (iso2)
- check `countries_aliases_check`: `CHECK (((aliases)::text = lower((aliases)::text)))`
- check `countries_iso2_check`: `CHECK ((iso2 ~ '^[A-Z]{2}$'::text))`
- check `countries_iso3_check`: `CHECK ((iso3 ~ '^[A-Z]{3}$'::text))`
- check `countries_names_check`: `CHECK (((length(btrim(name)) > 0) AND (length(btrim(iso_name)) > 0)))`
- check `countries_numeric_code_check`: `CHECK ((numeric_code ~ '^[0-9]{3}$'::text))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: SELECT

### `shared.decision_cache_hits_daily` (table, ~290 rows, 128 kB)
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

### `shared.decision_log` (table, ~427684 rows, 443.7 MB)
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
- check `decision_log_mode_check`: `CHECK ((mode = ANY (ARRAY['off'::text, 'shadow'::text, 'enforce'::text])))`
- check `decision_log_zone_check`: `CHECK ((zone = ANY (ARRAY['accept'::text, 'grey'::text, 'reject'::text, 'error'::text, 'skipped'::text])))`
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
- check `decision_question_accept_floor_check`: `CHECK (((accept_floor IS NULL) OR ((accept_floor >= (0)::numeric) AND (accept_floor <= (1)::numeric))))`
- check `decision_question_enforce_needs_calibration`: `CHECK (((mode <> 'enforce'::text) OR ((calibration_ref IS NOT NULL) AND ((accept_floor IS NOT NULL) OR (reject_ceiling IS NOT NULL)))))`
- check `decision_question_floors_ordered`: `CHECK (((accept_floor IS NULL) OR (reject_ceiling IS NULL) OR (reject_ceiling < accept_floor)))`
- check `decision_question_kind_check`: `CHECK ((kind = ANY (ARRAY['noul'::text, 'choice'::text, 'score'::text])))`
- check `decision_question_mode_check`: `CHECK ((mode = ANY (ARRAY['off'::text, 'shadow'::text, 'enforce'::text])))`
- check `decision_question_reject_ceiling_check`: `CHECK (((reject_ceiling IS NULL) OR ((reject_ceiling >= (0)::numeric) AND (reject_ceiling <= (1)::numeric))))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.destinations` (table, ~8200 rows, 6.5 MB)
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
country_iso2 character(2)
```
- owner `cis_owner`
- index `destinations_country_iso2_idx`: btree (country_iso2)
- index `destinations_lower_name_uidx`: UNIQUE btree (lower(name))
- index `destinations_name_country_uidx`: UNIQUE btree (name_norm, lower(btrim(country)), locality_norm) WHERE ((duplicate_of IS NULL) AND (name_norm IS NOT NULL))
- index `destinations_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `destinations_geo_precision_check`: `CHECK (((geo_precision IS NULL) OR (geo_precision = ANY (ARRAY['point'::text, 'area'::text, 'line'::text]))))`
- check `destinations_geo_status_check`: `CHECK ((geo_status = ANY (ARRAY['ok'::text, 'suspect'::text, 'manual'::text])))`
- check `destinations_located_by_check`: `CHECK ((located_by = ANY (ARRAY['mapbox'::text, 'llm'::text, 'geoapify'::text, 'manual'::text])))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `destinations_country_iso2`: BEFORE INSERT OR UPDATE OF country ON shared.destinations FOR EACH ROW EXECUTE FUNCTION shared.set_country_iso2()

### `shared.dfs_balance_snapshot` (table, 352 kB)
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

### `shared.dfs_call_log` (table, ~2626 rows, 1 MB)
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
job_id uuid
```
- owner `cis_owner`
- index `dfs_call_log_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `idx_dfs_call_log_created`: btree (created_at DESC)
- index `idx_dfs_call_log_endpoint`: btree (endpoint, created_at DESC)
- index `idx_dfs_call_log_job`: btree (job_id) WHERE (job_id IS NOT NULL)
- index `idx_dfs_call_log_live`: btree (fetched_live) WHERE fetched_live
- index `idx_dfs_call_log_tenant_created`: btree (tenant_id, created_at DESC)
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.eval_golden_item` (table, ~200 rows, 2.6 MB)
```
item_id uuid NN
set_id uuid NN
sample_id text NN
writer text NN
channel text
scope text NN
tenant_id uuid
split text NN
trap boolean NN
kind text NN
tiers text[] NN
country text
days integer
input jsonb NN · pii:free_text
control_output jsonb · pii:free_text
post_edit boolean NN
pipeline_verdict jsonb · pii:free_text
label jsonb NN · pii:free_text
label_verdict text NN
label_source text NN
injection_spec jsonb
refs jsonb NN
input_sha256 text NN
pick_reason text
created_at timestamp with time zone NN
```
- owner `cis_owner` · RLS on + FORCE
- index `eval_golden_item_pkey` PRIMARY KEY: UNIQUE btree (item_id)
- index `eval_golden_item_sample_key`: UNIQUE btree (set_id, sample_id)
- index `eval_golden_item_set_writer_split_idx`: btree (set_id, writer, split)
- index `eval_golden_item_tenant_idx`: btree (tenant_id) WHERE (scope = 'tenant'::text)
- check `eval_golden_item_channel_check`: `CHECK ((((writer = ANY (ARRAY['a1'::text, 't2'::text])) AND (channel IS NULL)) OR ((writer = 't9_blog'::text) AND (channel = 'blog'::text)) OR ((writer = 't9_social'::text) AND (channel IS NOT NULL) AND (channel <> 'blog'::text) AND (channel ~ '^[a-z_]{1,32}$'::text))))`
- check `eval_golden_item_days_check`: `CHECK ((((days IS NULL) OR ((days >= 1) AND (days <= 60))) AND (COALESCE(char_length(country), 0) <= 60)))`
- check `eval_golden_item_json_check`: `CHECK (((jsonb_typeof(input) = 'object'::text) AND (jsonb_typeof(label) = 'object'::text) AND (jsonb_typeof(refs) = 'object'::text) AND ((control_output IS NULL) OR (jsonb_typeof(control_output) = 'object'::text)) AND ((pipeline_verdict IS NULL) OR (jsonb_typeof(pipeline_verdict) = 'object'::text)) AND ((injection_spec IS NULL) OR (jsonb_typeof(injection_spec) = 'object'::text))))`
- check `eval_golden_item_kind_check`: `CHECK ((kind = ANY (ARRAY['real'::text, 'synthetic'::text])))`
- check `eval_golden_item_label_check`: `CHECK (((label_verdict = ANY (ARRAY['pass'::text, 'fail'::text])) AND (label_source = ANY (ARRAY['agent_panel'::text, 'synthetic'::text, 'admin_edit'::text, 'tenant_edit'::text, 'human_label'::text]))))`
- check `eval_golden_item_sample_check`: `CHECK ((sample_id ~ '^[a-z0-9-]{1,40}$'::text))`
- check `eval_golden_item_scope_check`: `CHECK ((scope = ANY (ARRAY['platform'::text, 'tenant'::text])))`
- check `eval_golden_item_scope_tenant_ck`: `CHECK ((((scope = 'platform'::text) AND (tenant_id IS NULL)) OR ((scope = 'tenant'::text) AND (tenant_id IS NOT NULL))))`
- check `eval_golden_item_sha_check`: `CHECK ((input_sha256 ~ '^[0-9a-f]{64}$'::text))`
- check `eval_golden_item_size_check`: `CHECK (((pg_column_size(input) <= 262144) AND (COALESCE(pg_column_size(control_output), 0) <= 131072) AND (COALESCE(pg_column_size(pipeline_verdict), 0) <= 16384) AND (pg_column_size(label) <= 32768) AND (COALESCE(pg_column_size(injection_spec), 0) <= 8192) AND (pg_column_size(refs) <= 4096) AND (COALESCE(char_length(pick_reason), 0) <= 80)))`
- check `eval_golden_item_split_check`: `CHECK ((split = ANY (ARRAY['tune'::text, 'holdout'::text, 'trap'::text])))`
- check `eval_golden_item_tiers_check`: `CHECK (((tiers <@ ARRAY['cycle_bike'::text, 'trek_hike'::text, 'water'::text, 'wildlife'::text, 'culinary'::text, 'long_9d'::text, 'long_18d'::text, 'poor_raw'::text, 'known_failure'::text, 'held'::text, 'fact_dense'::text, 'prompt_injection'::text, 'post_edit'::text]) AND (cardinality(tiers) <= 13) AND (('post_edit'::text = ANY (tiers)) = post_edit)))`
- check `eval_golden_item_trap_check`: `CHECK (((trap = (split = 'trap'::text)) AND (trap = (injection_spec IS NOT NULL))))`
- check `eval_golden_item_writer_check`: `CHECK ((writer = ANY (ARRAY['a1'::text, 't2'::text, 't9_blog'::text, 't9_social'::text])))`
- check `eval_golden_item_writer_scope_check`: `CHECK (((writer = 'a1'::text) = (scope = 'platform'::text)))`
- grant `cis_app`: DELETE, INSERT, SELECT
- policy `eval_golden_item_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `eval_golden_item_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))` WITH CHECK `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))`

### `shared.eval_golden_set` (table, 112 kB)
```
set_id uuid NN
name text NN
version text NN
status text NN
source_uri text NN
source_sha256 text NN
seed integer NN
holdout_pct numeric(4,3) NN
tier_rules jsonb NN
shared_inputs jsonb NN
meta jsonb NN
label_history jsonb NN · pii:online_id
item_count integer NN
imported_by text NN
created_at timestamp with time zone NN
superseded_at timestamp with time zone
```
- owner `cis_owner`
- index `eval_golden_set_name_version_key`: UNIQUE btree (name, version)
- index `eval_golden_set_one_active`: UNIQUE btree (name) WHERE (status = 'active'::text)
- index `eval_golden_set_pkey` PRIMARY KEY: UNIQUE btree (set_id)
- check `eval_golden_set_count_check`: `CHECK (((item_count >= 0) AND ((char_length(imported_by) >= 1) AND (char_length(imported_by) <= 128))))`
- check `eval_golden_set_holdout_check`: `CHECK (((holdout_pct > (0)::numeric) AND (holdout_pct < (1)::numeric)))`
- check `eval_golden_set_json_check`: `CHECK (((jsonb_typeof(tier_rules) = 'object'::text) AND (jsonb_typeof(shared_inputs) = 'object'::text) AND (jsonb_typeof(meta) = 'object'::text) AND (jsonb_typeof(label_history) = 'array'::text) AND (pg_column_size(tier_rules) <= 16384) AND (pg_column_size(shared_inputs) <= 131072) AND (pg_column_size(meta) <= 16384) AND (pg_column_size(label_history) <= 16384)))`
- check `eval_golden_set_name_check`: `CHECK ((name ~ '^[a-z0-9_]{1,40}$'::text))`
- check `eval_golden_set_platform_inputs_check`: `CHECK ((NOT jsonb_path_exists(shared_inputs, '$."brand_rules".keyvalue()?(!(@."key" starts with "s1:"))'::jsonpath)))`
- check `eval_golden_set_sha_check`: `CHECK ((source_sha256 ~ '^[0-9a-f]{64}$'::text))`
- check `eval_golden_set_source_uri_check`: `CHECK ((((char_length(source_uri) >= 1) AND (char_length(source_uri) <= 300)) AND (source_uri !~ '[0-9]{12}'::text) AND (source_uri !~* '^(arn:|s3://)'::text)))`
- check `eval_golden_set_status_check`: `CHECK ((status = ANY (ARRAY['active'::text, 'superseded'::text])))`
- check `eval_golden_set_superseded_check`: `CHECK (((status = 'superseded'::text) = (superseded_at IS NOT NULL)))`
- check `eval_golden_set_version_check`: `CHECK ((version ~ '^[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}$'::text))`
- grant `cis_app`: INSERT, SELECT, UPDATE

### `shared.eval_item_result` (table, ~326 rows, 472 kB)
```
result_id uuid NN
run_id uuid NN
item_id uuid NN
writer text NN
scope text NN
tenant_id uuid
arm text NN
mode text NN
phase text NN
scored_result_id uuid
output jsonb · pii:free_text
output_sha256 text
verdict text NN
score numeric
failure_codes text[] NN
hard_stop boolean NN
judge_model text
judge_version text
cost_usd numeric(10,6) NN
details jsonb NN
created_at timestamp with time zone NN
```
- owner `cis_owner` · RLS on + FORCE
- index `eval_item_result_item_idx`: btree (item_id)
- index `eval_item_result_key`: UNIQUE btree (run_id, item_id, arm, mode)
- index `eval_item_result_pkey` PRIMARY KEY: UNIQUE btree (result_id)
- index `eval_item_result_scored_idx`: btree (scored_result_id) WHERE (scored_result_id IS NOT NULL)
- index `eval_item_result_tenant_idx`: btree (tenant_id) WHERE (scope = 'tenant'::text)
- check `eval_item_result_arm_check`: `CHECK ((arm = ANY (ARRAY['control'::text, 'candidate'::text])))`
- check `eval_item_result_mode_check`: `CHECK ((mode = ANY (ARRAY['score_only'::text, 'regenerate'::text, 'rejudge'::text])))`
- check `eval_item_result_output_check`: `CHECK ((((output IS NULL) OR ((mode = 'regenerate'::text) AND (jsonb_typeof(output) = 'object'::text) AND (pg_column_size(output) <= 131072))) AND ((output IS NULL) = (output_sha256 IS NULL)) AND ((output_sha256 IS NULL) OR (output_sha256 ~ '^[0-9a-f]{64}$'::text))))`
- check `eval_item_result_phase_check`: `CHECK ((phase = ANY (ARRAY['probe'::text, 'tune'::text, 'holdout'::text])))`
- check `eval_item_result_rejudge_check`: `CHECK ((((mode = 'rejudge'::text) = (scored_result_id IS NOT NULL)) AND (scored_result_id IS DISTINCT FROM result_id)))`
- check `eval_item_result_scope_check`: `CHECK ((scope = ANY (ARRAY['platform'::text, 'tenant'::text])))`
- check `eval_item_result_scope_tenant_ck`: `CHECK ((((scope = 'platform'::text) AND (tenant_id IS NULL)) OR ((scope = 'tenant'::text) AND (tenant_id IS NOT NULL))))`
- check `eval_item_result_size_check`: `CHECK (((cardinality(failure_codes) <= 50) AND (COALESCE(char_length(judge_model), 0) <= 128) AND (COALESCE(char_length(judge_version), 0) <= 128) AND (cost_usd >= (0)::numeric) AND (jsonb_typeof(details) = 'object'::text) AND (pg_column_size(details) <= 16384)))`
- check `eval_item_result_verdict_check`: `CHECK ((verdict = ANY (ARRAY['pass'::text, 'fail'::text, 'error'::text, 'skipped'::text])))`
- check `eval_item_result_writer_check`: `CHECK ((writer = ANY (ARRAY['a1'::text, 't2'::text, 't9_blog'::text, 't9_social'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT
- policy `eval_item_result_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `eval_item_result_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))` WITH CHECK `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))`
- trigger `eval_item_result_guard`: BEFORE INSERT OR UPDATE ON shared.eval_item_result FOR EACH ROW EXECUTE FUNCTION shared.eval_item_result_guard()

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
- check `jev_credit_topup_amount_usd_check`: `CHECK ((amount_usd > (0)::numeric))`
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

### `shared.job` (table, ~7790 rows, 22.8 MB)
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
- check `job_attempts_chk`: `CHECK (((attempt >= 0) AND (max_attempts >= 1)))`
- check `job_kind_chk`: `CHECK ((kind ~ '^(?!bk_|tp_)[a-z][a-z0-9_]*$'::text))`
- check `job_lease_chk`: `CHECK (((status <> 'running'::text) OR ((locked_by IS NOT NULL) AND (locked_until IS NOT NULL))))`
- check `job_status_check`: `CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text, 'stopped_budget'::text, 'cancelled'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `job_set_updated_at`: BEFORE UPDATE ON shared.job FOR EACH ROW EXECUTE FUNCTION shared.job_set_updated_at()

### `shared.job_worker` (table, ~181 rows, 424 kB)
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

### `shared.kpi_daily` (table, 24 kB)
```
kpi_id text NN
day date NN
scope text NN
kpi_version smallint NN
value numeric NN
unit text NN
source text NN
data_as_of timestamp with time zone
computed_at timestamp with time zone NN
job_id uuid
```
- owner `cis_owner`
- index `kpi_daily_day_idx`: btree (day DESC)
- index `kpi_daily_pkey` PRIMARY KEY: UNIQUE btree (kpi_id, day, scope)
- check `kpi_daily_kpi_id_check`: `CHECK (((kpi_id ~ '^K-[A-Z0-9]+(-[A-Z0-9]+)*$'::text) AND (char_length(kpi_id) <= 64)))`
- check `kpi_daily_scope_check`: `CHECK (((scope = 'all'::text) OR ((scope ~ '^(app|provider):[A-Za-z0-9_.-]+$'::text) AND (char_length(scope) <= 96))))`
- check `kpi_daily_source_check`: `CHECK (((char_length(source) >= 1) AND (char_length(source) <= 200)))`
- check `kpi_daily_unit_check`: `CHECK ((unit = ANY (ARRAY['count'::text, 'ratio'::text, 'usd'::text, 'seconds'::text, 'hours'::text, 'days'::text, 'score'::text, 'status'::text, 'text'::text])))`
- check `kpi_daily_version_check`: `CHECK ((kpi_version >= 1))`
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

### `shared.llm_call_log` (table, ~383796 rows, 202.8 MB)
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
- check `llm_call_log_role_check`: `CHECK ((role = ANY (ARRAY['writer'::text, 'judge'::text, 'validate'::text, 'embed'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- grant `tripplanner`: INSERT

### `shared.llm_model_catalog` (table, 64 kB)
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
capabilities jsonb NN
```
- owner `cis_owner`
- index `llm_model_catalog_pkey` PRIMARY KEY: UNIQUE btree (model_key)
- check `llm_model_catalog_api_style_check`: `CHECK ((api_style = ANY (ARRAY['anthropic_native'::text, 'converse'::text, 'openai_chat'::text, 'embed'::text, 'decide'::text, 'anthropic_messages'::text, 'openai_responses'::text])))`
- check `llm_model_catalog_capabilities_check`: `CHECK ((jsonb_typeof(capabilities) = 'object'::text))`
- check `llm_model_catalog_enabled_needs_price`: `CHECK (((NOT enabled) OR ((price_in_per_mtok IS NOT NULL) AND (price_out_per_mtok IS NOT NULL))))`
- check `llm_model_catalog_max_output_tokens_check`: `CHECK (((max_output_tokens IS NULL) OR (max_output_tokens > 0)))`
- check `llm_model_catalog_provider_check`: `CHECK ((provider = ANY (ARRAY['bedrock'::text, 'openai'::text, 'typesafe'::text, 'anthropic'::text, 'azure_openai'::text, 'mock'::text])))`
- check `llm_model_catalog_vendor_check`: `CHECK ((vendor = ANY (ARRAY['anthropic'::text, 'openai'::text, 'cohere'::text, 'typesafe'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- grant `tripplanner`: SELECT

### `shared.llm_model_deployment` (table, 48 kB)
```
model_key text NN
connection_key text NN
wire_id text NN
priority smallint NN
enabled boolean NN
price_in_override numeric(10,4)
price_out_override numeric(10,4)
price_cache_read_override numeric(10,4)
price_cache_write_override numeric(10,4)
price_cache_write_1h_override numeric(10,4)
batch_capable boolean NN
request_defaults jsonb NN
origin text NN
notes text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
updated_by text NN
```
- owner `cis_owner`
- index `llm_model_deployment_connection_idx`: btree (connection_key)
- index `llm_model_deployment_pkey` PRIMARY KEY: UNIQUE btree (model_key, connection_key)
- check `llm_model_deployment_origin_check`: `CHECK ((origin = ANY (ARRAY['legacy_constant'::text, 'bedrock_profile'::text, 'openai_wire'::text, 'seed'::text, 'admin'::text])))`
- check `llm_model_deployment_price_check`: `CHECK ((((price_in_override IS NULL) OR (price_in_override >= (0)::numeric)) AND ((price_out_override IS NULL) OR (price_out_override >= (0)::numeric)) AND ((price_cache_read_override IS NULL) OR (price_cache_read_override >= (0)::numeric)) AND ((price_cache_write_override IS NULL) OR (price_cache_write_override >= (0)::numeric)) AND ((price_cache_write_1h_override IS NULL) OR (price_cache_write_1h_override >= (0)::numeric))))`
- check `llm_model_deployment_priority_check`: `CHECK (((priority >= 0) AND (priority <= 1000)))`
- check `llm_model_deployment_request_defaults_check`: `CHECK ((jsonb_typeof(request_defaults) = 'object'::text))`
- check `llm_model_deployment_wire_id_check`: `CHECK (((length(wire_id) >= 1) AND (length(wire_id) <= 200)))`
- grant `cis_app`: SELECT

### `shared.llm_provider_connection` (table, 32 kB)
```
connection_key text NN
kind text NN
auth_mode text NN
label text NN
account_id text
account_id_env text
region text
role_name text
external_id text
secret_name text
credential_env text
base_url text
data_scope text NN
timeout_s integer
max_retries integer
max_concurrency integer
rpm_limit integer
monthly_budget_usd numeric(10,2)
enabled boolean NN
notes text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
updated_by text NN
```
- owner `cis_owner`
- index `llm_provider_connection_pkey` PRIMARY KEY: UNIQUE btree (connection_key)
- check `llm_provider_connection_account_id_check`: `CHECK (((account_id IS NULL) OR (account_id ~ '^[0-9]{12}$'::text)))`
- check `llm_provider_connection_account_id_env_check`: `CHECK (((account_id_env IS NULL) OR (account_id_env = 'BEDROCK_ACCT_PRIMARY'::text)))`
- check `llm_provider_connection_assume_role_check`: `CHECK (((auth_mode <> 'assume_role'::text) OR (NOT enabled) OR ((role_name IS NOT NULL) AND (external_id IS NOT NULL) AND (region IS NOT NULL) AND ((account_id IS NOT NULL) OR (account_id_env IS NOT NULL)))))`
- check `llm_provider_connection_auth_mode_check`: `CHECK ((((kind = 'bedrock'::text) AND (auth_mode = ANY (ARRAY['assume_role'::text, 'task_role'::text, 'bedrock_api_key'::text]))) OR ((kind = ANY (ARRAY['anthropic'::text, 'openai'::text, 'azure_openai'::text])) AND (auth_mode = 'api_key'::text)) OR ((kind = 'mock'::text) AND (auth_mode = 'none'::text))))`
- check `llm_provider_connection_base_url_check`: `CHECK (((base_url IS NULL) OR ((kind <> ALL (ARRAY['bedrock'::text, 'mock'::text])) AND (base_url ~ '^https://[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+(/[A-Za-z0-9._~-]+)*/?$'::text))))`
- check `llm_provider_connection_budget_check`: `CHECK (((monthly_budget_usd IS NULL) OR (monthly_budget_usd >= (0)::numeric)))`
- check `llm_provider_connection_concurrency_check`: `CHECK (((max_concurrency IS NULL) OR ((max_concurrency >= 1) AND (max_concurrency <= 1000))))`
- check `llm_provider_connection_credential_env_check`: `CHECK (((credential_env IS NULL) OR (credential_env = 'OPENAI_API_KEY'::text)))`
- check `llm_provider_connection_data_scope_check`: `CHECK ((data_scope = ANY (ARRAY['aws_only'::text, 'vendor_direct'::text])))`
- check `llm_provider_connection_key_check`: `CHECK ((connection_key ~ '^[a-z0-9][a-z0-9-]{1,62}$'::text))`
- check `llm_provider_connection_key_source_check`: `CHECK (((auth_mode <> ALL (ARRAY['api_key'::text, 'bedrock_api_key'::text])) OR (NOT enabled) OR (secret_name IS NOT NULL) OR (credential_env IS NOT NULL)))`
- check `llm_provider_connection_kind_check`: `CHECK ((kind = ANY (ARRAY['bedrock'::text, 'anthropic'::text, 'openai'::text, 'azure_openai'::text, 'mock'::text])))`
- check `llm_provider_connection_region_check`: `CHECK (((region IS NULL) OR (region ~ '^[a-z]{2}(-[a-z]+)+-[0-9]$'::text)))`
- check `llm_provider_connection_retries_check`: `CHECK (((max_retries IS NULL) OR ((max_retries >= 0) AND (max_retries <= 5))))`
- check `llm_provider_connection_role_name_check`: `CHECK (((role_name IS NULL) OR (role_name ~ '^[A-Za-z0-9+=,.@_-]{1,64}$'::text)))`
- check `llm_provider_connection_rpm_check`: `CHECK (((rpm_limit IS NULL) OR ((rpm_limit >= 1) AND (rpm_limit <= 100000))))`
- check `llm_provider_connection_secret_name_check`: `CHECK (((secret_name IS NULL) OR (secret_name ~ '^aa-llm/[a-z0-9-]+/[a-z0-9][a-z0-9-]*$'::text)))`
- check `llm_provider_connection_task_role_check`: `CHECK (((auth_mode <> 'task_role'::text) OR ((region IS NOT NULL) AND (role_name IS NULL) AND (external_id IS NULL) AND (secret_name IS NULL) AND (credential_env IS NULL))))`
- check `llm_provider_connection_timeout_check`: `CHECK (((timeout_s IS NULL) OR ((timeout_s >= 1) AND (timeout_s <= 900))))`
- grant `cis_app`: SELECT

### `shared.llm_role_config` (table, ~36 rows, 32 kB)
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
- check `llm_role_config_account_route_check`: `CHECK (((account_route IS NULL) OR (account_route = 'acc3'::text)))`
- check `llm_role_config_provider_check`: `CHECK ((provider = ANY (ARRAY['claude'::text, 'openai'::text, 'cohere'::text])))`
- check `llm_role_config_role_check`: `CHECK ((role = ANY (ARRAY['writer'::text, 'judge'::text, 'validate'::text, 'embed'::text])))`
- check `llm_role_config_shadow_sample_pct_check`: `CHECK (((shadow_sample_pct >= 0) AND (shadow_sample_pct <= 100)))`
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

### `shared.notifications` (table, ~39 rows, 104 kB)
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

### `shared.place_photo` (table, ~3232 rows, 4.2 MB)
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
s3_key_medium text
destination_match_source text
```
- owner `cis_owner`
- index `place_photo_country_status_idx`: btree (country, status)
- index `place_photo_destination_idx`: btree (destination_id) WHERE (destination_id IS NOT NULL)
- index `place_photo_drive_file_id_key`: UNIQUE btree (drive_file_id)
- index `place_photo_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `place_photo_sha256_matched_idx`: btree (sha256, created_at, id) WHERE ((status = 'matched'::text) AND (s3_key_large IS NOT NULL) AND (sha256 IS NOT NULL))
- index `place_photo_tour_idx`: btree (tour_id) WHERE (tour_id IS NOT NULL)
- check `place_photo_destination_match_source_check`: `CHECK ((destination_match_source = ANY (ARRAY['auto'::text, 'manual'::text])))`
- check `place_photo_match_source_check`: `CHECK ((match_source = ANY (ARRAY['auto'::text, 'manual'::text])))`
- check `place_photo_status_check`: `CHECK ((status = ANY (ARRAY['matched'::text, 'unmatched'::text, 'rejected'::text, 'error'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.prompt_eval_runs` (table, 136 kB)
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
run_kind text NN
writer text
release_id uuid
golden_set_id uuid
tiers text[] NN
stop_reason text
verdict text
cost_cap_usd numeric(10,4)
judge_kappa numeric(4,3)
judge_counts boolean
fingerprint jsonb NN
finished_at timestamp with time zone
```
- owner `cis_owner`
- index `idx_prompt_eval_runs_pipeline_created`: btree (pipeline, created_at DESC)
- index `prompt_eval_runs_golden_set_idx`: btree (golden_set_id) WHERE (golden_set_id IS NOT NULL)
- index `prompt_eval_runs_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `prompt_eval_runs_wm_writer_idx`: btree (writer, run_kind, created_at DESC) WHERE (pipeline = 'writing_memory'::text)
- check `prompt_eval_runs_finished_check`: `CHECK (((finished_at IS NULL) OR ((stop_reason IS NOT NULL) AND (verdict IS NOT NULL))))`
- check `prompt_eval_runs_legacy_kind_check`: `CHECK (((pipeline = 'writing_memory'::text) OR ((run_kind = 'regression'::text) AND (writer IS NULL))))`
- check `prompt_eval_runs_pipeline_check`: `CHECK ((pipeline = ANY (ARRAY['s1_old'::text, 's1_from_atom'::text, 'writing_memory'::text])))`
- check `prompt_eval_runs_run_kind_check`: `CHECK ((run_kind = ANY (ARRAY['regression'::text, 'baseline_import'::text, 'r0_replay'::text, 'r1'::text, 'r2'::text, 'reverify'::text, 'probe'::text, 'shadow'::text])))`
- check `prompt_eval_runs_values_check`: `CHECK ((((stop_reason IS NULL) OR (stop_reason = ANY (ARRAY['completed'::text, 'hard_stop'::text, 'futility'::text, 'budget_cap'::text, 'probe_fail'::text, 'error'::text]))) AND ((verdict IS NULL) OR (verdict = ANY (ARRAY['pass'::text, 'fail'::text, 'baseline'::text, 'informative'::text, 'invalid'::text]))) AND (tour_count >= 0) AND ((cost_usd IS NULL) OR (cost_usd >= (0)::numeric)) AND ((cost_cap_usd IS NULL) OR (cost_cap_usd >= (0)::numeric)) AND ((judge_kappa IS NULL) OR ((judge_kappa >= ('-1'::integer)::numeric) AND (judge_kappa <= (1)::numeric))) AND ((judge_counts IS NOT TRUE) OR (judge_kappa >= 0.6)) AND (tiers <@ ARRAY['cycle_bike'::text, 'trek_hike'::text, 'water'::text, 'wildlife'::text, 'culinary'::text, 'long_9d'::text, 'long_18d'::text, 'poor_raw'::text, 'known_failure'::text, 'held'::text, 'fact_dense'::text, 'prompt_injection'::text, 'post_edit'::text]) AND (jsonb_typeof(fingerprint) = 'object'::text)))`
- check `prompt_eval_runs_wm_shape_check`: `CHECK (((pipeline <> 'writing_memory'::text) OR ((writer IS NOT NULL) AND (run_kind <> 'regression'::text) AND (cost_usd IS NOT NULL) AND (jsonb_typeof(details) = 'object'::text))))`
- check `prompt_eval_runs_writer_check`: `CHECK (((writer IS NULL) OR (writer = ANY (ARRAY['a1'::text, 't2'::text, 't9_blog'::text, 't9_social'::text]))))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `prompt_eval_runs_freeze`: BEFORE UPDATE ON shared.prompt_eval_runs FOR EACH ROW EXECUTE FUNCTION shared.prompt_eval_runs_freeze()

### `shared.report_run` (table, 40 kB)
```
id uuid NN
report_id text NN
period_start date NN
period_end date NN
status text NN
trigger text NN
triggered_by text
job_id uuid
started_at timestamp with time zone
finished_at timestamp with time zone
summary text
output jsonb
output_markdown text
s3_key text
error text
approved_by text
approved_at timestamp with time zone
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `report_run_job_idx`: btree (job_id) WHERE (job_id IS NOT NULL)
- index `report_run_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `report_run_report_created_idx`: btree (report_id, created_at DESC)
- index `report_run_schedule_uq`: UNIQUE btree (report_id, period_start, period_end) WHERE (trigger = 'schedule'::text)
- check `report_run_approval_check`: `CHECK (((approved_by IS NULL) = (approved_at IS NULL)))`
- check `report_run_period_check`: `CHECK ((period_end >= period_start))`
- check `report_run_report_id_check`: `CHECK ((report_id ~ '^[A-Z]{2,4}-[0-9]{2}$'::text))`
- check `report_run_status_check`: `CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text, 'draft'::text, 'approved'::text, 'posted'::text])))`
- check `report_run_text_check`: `CHECK (((COALESCE(char_length(triggered_by), 0) <= 128) AND (COALESCE(char_length(summary), 0) <= 1000) AND (COALESCE(char_length(error), 0) <= 4000) AND (COALESCE(char_length(s3_key), 0) <= 1024) AND (COALESCE(char_length(approved_by), 0) <= 128)))`
- check `report_run_trigger_check`: `CHECK ((trigger = ANY (ARRAY['schedule'::text, 'manual'::text, 'on_demand'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.rerun_wave` (table, ~25 rows, 216 kB)
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
- check `rerun_wave_expected_tour_ids_check`: `CHECK ((cardinality(expected_tour_ids) > 0))`
- check `rerun_wave_status_check`: `CHECK ((status = ANY (ARRAY['open'::text, 'complete'::text, 'incomplete'::text, 'closed'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.schema_versions` (table, ~301 rows, 120 kB)
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
- check `spend_budget_alert_pct_check`: `CHECK (((alert_pct >= 1) AND (alert_pct <= 100)))`
- check `spend_budget_per_day_usd_check`: `CHECK (((per_day_usd IS NULL) OR (per_day_usd >= (0)::numeric)))`
- check `spend_budget_per_run_usd_check`: `CHECK (((per_run_usd IS NULL) OR (per_run_usd >= (0)::numeric)))`
- check `spend_budget_provider_check`: `CHECK ((provider = ANY (ARRAY['dfs'::text, 'bedrock'::text, 'openai'::text, 'jev'::text, 'geocoder'::text, 'anthropic'::text, 'azure_openai'::text])))`
- check `spend_budget_scope_check`: `CHECK (((scope = 'global'::text) OR (scope ~~ 'job:%'::text)))`
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
- check `staff_app_grant_app_chk`: `CHECK ((app = 'booking'::text))`
- check `staff_app_grant_role_chk`: `CHECK ((role = ANY (ARRAY['admin'::text, 'sales'::text, 'contracting'::text, 'content_creator'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE

### `shared.supply_content_version` (table, 80 kB)
```
id uuid NN
entity_id uuid NN
content_version integer NN
supply_version bigint NN
origin text NN
description text NN
highlights text[] NN
good_to_know text[] NN
photos jsonb NN
status text NN
based_on_version_id uuid
llm_job_id uuid
created_by text NN
created_at timestamp with time zone NN
reviewed_by text
reviewed_at timestamp with time zone
review_note text
```
- owner `cis_owner`
- index `supply_content_version_entity_id_key`: UNIQUE btree (entity_id, id)
- index `supply_content_version_number_key`: UNIQUE btree (entity_id, content_version)
- index `supply_content_version_one_approved`: UNIQUE btree (entity_id) WHERE (status = 'approved'::text)
- index `supply_content_version_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `supply_content_version_numbers_check`: `CHECK (((content_version >= 1) AND (supply_version >= 1)))`
- check `supply_content_version_origin_check`: `CHECK ((origin = ANY (ARRAY['llm'::text, 'human'::text])))`
- check `supply_content_version_photos_check`: `CHECK ((jsonb_typeof(photos) = 'array'::text))`
- check `supply_content_version_review_check`: `CHECK (((status <> ALL (ARRAY['approved'::text, 'rejected'::text])) OR ((reviewed_by IS NOT NULL) AND (reviewed_at IS NOT NULL))))`
- check `supply_content_version_status_check`: `CHECK ((status = ANY (ARRAY['draft'::text, 'approved'::text, 'rejected'::text, 'superseded'::text])))`
- check `supply_content_version_text_check`: `CHECK (((length(btrim(description)) > 0) AND (cardinality(highlights) <= 5) AND (cardinality(good_to_know) <= 3)))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: INSERT, SELECT, UPDATE
- trigger `supply_content_version_guard`: BEFORE DELETE OR UPDATE ON shared.supply_content_version FOR EACH ROW EXECUTE FUNCTION shared.supply_content_version_guard()

### `shared.supply_entity` (table, 64 kB)
```
id uuid NN
source_system text NN
source_id text NN
entity_type text NN
service_type text
title text NN
country_code text
facts jsonb NN
applied_supply_version bigint NN
active boolean NN
content_status text NN
published_version_id uuid
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `supply_entity_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `supply_entity_source_key`: UNIQUE btree (source_system, source_id)
- index `supply_entity_status_idx`: btree (content_status, updated_at DESC)
- check `supply_entity_content_status_check`: `CHECK ((content_status = ANY (ARRAY['draft'::text, 'in_review'::text, 'published'::text, 'stale'::text, 'unpublished'::text])))`
- check `supply_entity_entity_type_check`: `CHECK ((entity_type = ANY (ARRAY['hotel'::text, 'service'::text])))`
- check `supply_entity_facts_check`: `CHECK ((jsonb_typeof(facts) = 'object'::text))`
- check `supply_entity_inactive_check`: `CHECK ((active OR (content_status = 'unpublished'::text)))`
- check `supply_entity_published_check`: `CHECK (((content_status <> 'published'::text) OR (published_version_id IS NOT NULL)))`
- check `supply_entity_service_type_check`: `CHECK (((entity_type = 'service'::text) OR (service_type IS NULL)))`
- check `supply_entity_source_id_check`: `CHECK ((source_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'::text))`
- check `supply_entity_source_system_check`: `CHECK ((source_system = 'booking'::text))`
- check `supply_entity_version_check`: `CHECK ((applied_supply_version >= 1))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: INSERT, SELECT, UPDATE

### `shared.supply_event_inbox` (table, 80 kB)
```
id bigint NN
source text NN
contract text NN
idempotency_key uuid NN
source_id text NN
event_type text NN
supply_version bigint NN
facts_supply_version bigint
feed_seq bigint NN
outcome text NN
received_at timestamp with time zone NN
```
- owner `cis_owner`
- index `supply_event_inbox_key`: UNIQUE btree (source, contract, idempotency_key)
- index `supply_event_inbox_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `supply_event_inbox_received_idx`: btree (received_at)
- index `supply_event_inbox_source_idx`: btree (source_id, received_at DESC)
- check `supply_event_inbox_contract_check`: `CHECK ((contract = ANY (ARRAY['supply.hotel.v1'::text, 'supply.service.v1'::text])))`
- check `supply_event_inbox_event_type_check`: `CHECK ((event_type = ANY (ARRAY['supply.upsert'::text, 'supply.deactivate'::text])))`
- check `supply_event_inbox_outcome_check`: `CHECK ((outcome = ANY (ARRAY['applied'::text, 'skipped_older'::text, 'missing'::text])))`
- check `supply_event_inbox_outcome_version_check`: `CHECK (((outcome = 'missing'::text) = (facts_supply_version IS NULL)))`
- check `supply_event_inbox_source_check`: `CHECK ((source = 'booking'::text))`
- grant `cis_app`: INSERT, SELECT

### `shared.supply_feed_cursor` (table, ~1 rows, 64 kB)
```
consumer text NN
last_feed_seq bigint NN
last_pull_at timestamp with time zone
last_success_at timestamp with time zone
last_error text
last_error_at timestamp with time zone
```
- owner `cis_owner`
- index `supply_feed_cursor_pkey` PRIMARY KEY: UNIQUE btree (consumer)
- check `supply_feed_cursor_consumer_check`: `CHECK ((consumer ~ '^[a-z][a-z0-9_]{1,62}$'::text))`
- check `supply_feed_cursor_seq_check`: `CHECK ((last_feed_seq >= 0))`
- grant `cis_app`: INSERT, SELECT, UPDATE

### `shared.supply_media` (table, 48 kB)
```
booking_media_id uuid NN
entity_id uuid NN
usage_rights boolean NN
active boolean NN
sha256 text NN
content_type text NN
width integer
height integer
cis_key_1600 text
cis_key_600 text
url_1600 text
url_600 text
copied_sha256 text
copied_at timestamp with time zone
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `supply_media_entity_idx`: btree (entity_id)
- index `supply_media_pkey` PRIMARY KEY: UNIQUE btree (booking_media_id)
- check `supply_media_content_type_check`: `CHECK ((content_type = ANY (ARRAY['image/jpeg'::text, 'image/png'::text, 'image/webp'::text])))`
- check `supply_media_copy_check`: `CHECK ((((cis_key_1600 IS NULL) AND (cis_key_600 IS NULL) AND (copied_sha256 IS NULL) AND (copied_at IS NULL) AND (url_1600 IS NULL) AND (url_600 IS NULL)) OR ((cis_key_1600 ~~ 'photos/supply/%'::text) AND (cis_key_600 ~~ 'photos/supply/%'::text) AND (copied_sha256 ~ '^[0-9a-f]{64}$'::text) AND (copied_at IS NOT NULL))))`
- check `supply_media_sha256_check`: `CHECK ((sha256 ~ '^[0-9a-f]{64}$'::text))`
- check `supply_media_url_check`: `CHECK ((((url_1600 IS NULL) OR (url_1600 ~~ 'https://%'::text)) AND ((url_600 IS NULL) OR (url_600 ~~ 'https://%'::text))))`
- grant `catalog_owner`: SELECT
- grant `cis_app`: INSERT, SELECT, UPDATE

### `shared.tenant_api_usage` (table, ~157306 rows, 39 MB)
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
- check `chk_tenant_api_usage_actor`: `CHECK (((((actor_type)::text = 'tenant'::text) AND (tenant_id IS NOT NULL) AND (admin_user_id IS NULL)) OR (((actor_type)::text = 'admin'::text) AND (tenant_id IS NULL) AND (admin_user_id IS NOT NULL)) OR (((actor_type)::text = 'admin'::text) AND (tenant_id IS NULL) AND (admin_user_id IS NULL))))`
- check `tenant_api_usage_actor_type_check`: `CHECK (((actor_type)::text = ANY ((ARRAY['tenant'::character varying, 'admin'::character varying])::text[])))`
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
- check `tenant_api_usage_monthly_first_day`: `CHECK ((EXTRACT(day FROM month) = (1)::numeric))`
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

### `shared.tenant_members` (table, 64 kB)
```
membership_id uuid NN
tenant_id uuid NN
cognito_iss text · pii:online_id
cognito_sub text · pii:online_id
content_studio_role text NN
status text NN
invitation_id uuid
created_at timestamp with time zone NN
created_by text NN
updated_at timestamp with time zone NN
removed_at timestamp with time zone
removed_by text
```
- owner `cis_owner`
- index `tenant_members_identity_idx`: btree (cognito_iss, cognito_sub) WHERE (cognito_iss IS NOT NULL)
- index `tenant_members_live_identity_key`: UNIQUE btree (tenant_id, cognito_iss, cognito_sub) WHERE (status <> 'removed'::text)
- index `tenant_members_pkey` PRIMARY KEY: UNIQUE btree (membership_id)
- check `tenant_members_actor_check`: `CHECK ((((char_length(created_by) >= 1) AND (char_length(created_by) <= 64)) AND ((removed_by IS NULL) OR ((char_length(removed_by) >= 1) AND (char_length(removed_by) <= 64)))))`
- check `tenant_members_identity_check`: `CHECK ((((cognito_iss IS NULL) = (cognito_sub IS NULL)) AND ((status <> 'invited'::text) OR (cognito_iss IS NULL)) AND ((status <> 'active'::text) OR (cognito_iss IS NOT NULL))))`
- check `tenant_members_identity_shape_check`: `CHECK (((cognito_iss IS NULL) OR ((cognito_iss ~~ 'https://%'::text) AND (char_length(cognito_iss) <= 300) AND ((char_length(cognito_sub) >= 1) AND (char_length(cognito_sub) <= 128)))))`
- check `tenant_members_invitation_check`: `CHECK (((status <> 'invited'::text) OR (invitation_id IS NOT NULL)))`
- check `tenant_members_removed_check`: `CHECK ((((status = 'removed'::text) = (removed_at IS NOT NULL)) AND ((removed_at IS NULL) = (removed_by IS NULL))))`
- check `tenant_members_role_check`: `CHECK ((content_studio_role = ANY (ARRAY['owner'::text, 'editor'::text, 'viewer'::text])))`
- check `tenant_members_status_check`: `CHECK ((status = ANY (ARRAY['invited'::text, 'active'::text, 'removed'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `tenant_members_feed`: AFTER INSERT OR UPDATE ON shared.tenant_members FOR EACH ROW EXECUTE FUNCTION shared.tenant_membership_emit_member()
- trigger `tenant_members_guard`: BEFORE INSERT OR DELETE OR UPDATE ON shared.tenant_members FOR EACH ROW EXECUTE FUNCTION shared.tenant_members_guard()

### `shared.tenant_membership_event` (table, 64 kB)
```
seq bigint NN
event_id uuid NN
txid xid8 NN
type text NN
tenant_id uuid NN
membership jsonb · pii:online_id
occurred_at timestamp with time zone NN
```
- owner `cis_owner`
- index `tenant_membership_event_event_id_key`: UNIQUE btree (event_id)
- index `tenant_membership_event_feed_idx`: btree (txid, seq)
- index `tenant_membership_event_pkey` PRIMARY KEY: UNIQUE btree (seq)
- check `tenant_membership_event_membership_check`: `CHECK ((((type ~~ 'membership.%'::text) = (membership IS NOT NULL)) AND ((membership IS NULL) OR (jsonb_typeof(membership) = 'object'::text))))`
- check `tenant_membership_event_type_check`: `CHECK ((type = ANY (ARRAY['tenant.created'::text, 'tenant.locked'::text, 'tenant.unlocked'::text, 'tenant.deleted'::text, 'membership.invited'::text, 'membership.activated'::text, 'membership.role_changed'::text, 'membership.removed'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT
- trigger `tenant_membership_event_guard`: BEFORE INSERT OR DELETE OR UPDATE ON shared.tenant_membership_event FOR EACH ROW EXECUTE FUNCTION shared.tenant_membership_event_guard()
- trigger `tenant_membership_event_no_truncate`: BEFORE TRUNCATE ON shared.tenant_membership_event FOR EACH STATEMENT EXECUTE FUNCTION shared.tenant_membership_event_guard()

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
- check `tenants_daily_publish_limit_positive`: `CHECK (((daily_publish_limit IS NULL) OR (daily_publish_limit >= 1)))`
- check `tenants_posts_per_week_range`: `CHECK (((posts_per_week >= 1) AND (posts_per_week <= 14)))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- trigger `tenants_membership_feed_ins`: AFTER INSERT ON shared.tenants FOR EACH ROW EXECUTE FUNCTION shared.tenant_membership_emit_tenant()
- trigger `tenants_membership_feed_upd`: AFTER UPDATE OF is_active, cancelled_at ON shared.tenants FOR EACH ROW WHEN (((old.is_active IS DISTINCT FROM new.is_active) OR (old.cancelled_at IS DISTINCT FROM new.cancelled_at))) EXECUTE FUNCTION shared.tenant_membership_emit_tenant()

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

### `shared.v_country_unmapped` (VIEW)
```
source text
country text
row_count bigint
```
- owner `cis_owner`
- grant `cis_app`: SELECT

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

### `shared.writing_memory_release` (table, ~9 rows, 160 kB)
```
release_id uuid NN
writer text NN
scope text NN
tenant_id uuid
release_no integer NN
train_kind text NN
content_class text NN
rule_ids uuid[] NN
items_sha256 text NN
status text NN
r0_run_id uuid
eval_run_id uuid
shadow_run_id uuid
previous_release_id uuid
train_month date
emergency_reason text
emergency_ref uuid
reverify boolean NN
reverify_reasons text[] NN
reverify_at timestamp with time zone
reverify_run_id uuid
reverify_approved_by text
reverify_approved_at timestamp with time zone
fingerprint jsonb NN
approved_by text
approved_at timestamp with time zone
approval_ref text
activated_at timestamp with time zone
retired_at timestamp with time zone
retired_reason text · pii:free_text
rejected_by text
rejected_reason text · pii:free_text
notes text · pii:free_text
created_by text NN
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner` · RLS on + FORCE
- index `writing_memory_release_number_uq`: UNIQUE btree (writer, scope, COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), release_no)
- index `writing_memory_release_one_active`: UNIQUE btree (writer, scope, COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid)) WHERE (status = 'active'::text)
- index `writing_memory_release_pkey` PRIMARY KEY: UNIQUE btree (release_id)
- index `writing_memory_release_tenant_idx`: btree (tenant_id, status) WHERE (scope = 'tenant'::text)
- index `writing_memory_release_train_slot`: UNIQUE btree (writer, scope, COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), train_month) WHERE ((train_kind = 'regular'::text) AND (train_month IS NOT NULL))
- index `writing_memory_release_writer_status_idx`: btree (writer, status)
- check `writing_memory_release_approval_check`: `CHECK ((((status <> ALL (ARRAY['approved'::text, 'active'::text, 'retired'::text])) OR ((approved_by IS NOT NULL) AND (approved_at IS NOT NULL))) AND ((status <> ALL (ARRAY['active'::text, 'retired'::text])) OR (activated_at IS NOT NULL)) AND ((status <> 'retired'::text) OR ((retired_at IS NOT NULL) AND (retired_reason IS NOT NULL))) AND ((status <> 'rejected'::text) OR ((rejected_by IS NOT NULL) AND (rejected_reason IS NOT NULL)))))`
- check `writing_memory_release_class_check`: `CHECK ((((content_class = 'empty'::text) = (train_kind = 'baseline'::text)) AND ((content_class = 'lexicon_only'::text) = (train_kind = 'lexicon'::text)) AND ((content_class = 'empty'::text) = (cardinality(rule_ids) = 0)) AND ((release_no <> 0) OR (content_class = 'empty'::text)) AND (release_no >= 0)))`
- check `writing_memory_release_emergency_check`: `CHECK ((((train_kind = 'emergency'::text) = (emergency_reason IS NOT NULL)) AND ((emergency_reason IS NULL) = (emergency_ref IS NULL)) AND ((emergency_reason IS NULL) OR (emergency_reason = ANY (ARRAY['hard_stop_1'::text, 'hard_stop_2'::text, 'hard_stop_3'::text])))))`
- check `writing_memory_release_evidence_check`: `CHECK (((status <> ALL (ARRAY['active'::text, 'retired'::text])) OR ((content_class = 'empty'::text) AND (r0_run_id IS NOT NULL) AND (eval_run_id IS NOT NULL)) OR ((content_class = 'lexicon_only'::text) AND (r0_run_id IS NOT NULL)) OR ((content_class = ANY (ARRAY['repair_hint_only'::text, 'rules'::text])) AND (eval_run_id IS NOT NULL) AND (shadow_run_id IS NOT NULL))))`
- check `writing_memory_release_kind_check`: `CHECK (((train_kind = ANY (ARRAY['baseline'::text, 'regular'::text, 'emergency'::text, 'lexicon'::text])) AND (content_class = ANY (ARRAY['empty'::text, 'lexicon_only'::text, 'repair_hint_only'::text, 'rules'::text]))))`
- check `writing_memory_release_reverify_check`: `CHECK (((reverify = (reverify_at IS NOT NULL)) AND (reverify OR (cardinality(reverify_reasons) = 0)) AND (reverify_reasons <@ ARRAY['golden_set'::text, 'model_route'::text, 'gate_taxonomy'::text, 'prompt_version_mismatch'::text]) AND ((reverify_run_id IS NULL) OR ((reverify_approved_by IS NOT NULL) AND (reverify_approved_at IS NOT NULL)))))`
- check `writing_memory_release_scope_check`: `CHECK ((scope = ANY (ARRAY['platform'::text, 'tenant'::text])))`
- check `writing_memory_release_scope_tenant_ck`: `CHECK ((((scope = 'platform'::text) AND (tenant_id IS NULL)) OR ((scope = 'tenant'::text) AND (tenant_id IS NOT NULL))))`
- check `writing_memory_release_size_check`: `CHECK (((cardinality(rule_ids) <= 40) AND (items_sha256 ~ '^[0-9a-f]{64}$'::text) AND (jsonb_typeof(fingerprint) = 'object'::text) AND (pg_column_size(fingerprint) <= 8192) AND (COALESCE(char_length(approved_by), 0) <= 128) AND (COALESCE(char_length(approval_ref), 0) <= 300) AND (COALESCE(char_length(retired_reason), 0) <= 500) AND (COALESCE(char_length(rejected_by), 0) <= 128) AND (COALESCE(char_length(rejected_reason), 0) <= 500) AND (COALESCE(char_length(notes), 0) <= 1000) AND (COALESCE(char_length(reverify_approved_by), 0) <= 128) AND ((char_length(created_by) >= 1) AND (char_length(created_by) <= 128)) AND (cardinality(reverify_reasons) <= 4)))`
- check `writing_memory_release_status_check`: `CHECK ((status = ANY (ARRAY['draft'::text, 'evaluated'::text, 'approved'::text, 'active'::text, 'retired'::text, 'rejected'::text])))`
- check `writing_memory_release_train_check`: `CHECK ((((train_month IS NULL) OR ((train_kind = 'regular'::text) AND (EXTRACT(day FROM train_month) = (1)::numeric))) AND ((train_kind <> 'regular'::text) OR (status <> ALL (ARRAY['active'::text, 'retired'::text])) OR (train_month IS NOT NULL))))`
- check `writing_memory_release_writer_check`: `CHECK ((writer = ANY (ARRAY['a1'::text, 't2'::text, 't9_blog'::text, 't9_social'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))` WITH CHECK `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))`
- policy `writing_memory_release_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `writing_memory_release_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- trigger `writing_memory_release_guard`: BEFORE INSERT OR UPDATE ON shared.writing_memory_release FOR EACH ROW EXECUTE FUNCTION shared.writing_memory_release_guard()

### `shared.writing_memory_shadow` (table, 80 kB)
```
shadow_id uuid NN
release_id uuid NN
run_id uuid NN
writer text NN
channel text
scope text NN
tenant_id uuid
probe boolean NN
input_source text NN
input_id uuid NN
input_sha256 text NN
prompt_sha256 text
output jsonb · pii:free_text
output_sha256 text
control_ref jsonb
isolation jsonb NN
qa_artefacts text[] NN
verdict text NN
cost_usd numeric(10,6) NN
created_at timestamp with time zone NN
```
- owner `cis_owner` · RLS on + FORCE
- index `writing_memory_shadow_input_key`: UNIQUE btree (run_id, input_source, input_id)
- index `writing_memory_shadow_pkey` PRIMARY KEY: UNIQUE btree (shadow_id)
- index `writing_memory_shadow_release_idx`: btree (release_id)
- index `writing_memory_shadow_tenant_idx`: btree (tenant_id) WHERE (scope = 'tenant'::text)
- check `writing_memory_shadow_channel_check`: `CHECK ((((writer = ANY (ARRAY['a1'::text, 't2'::text])) AND (channel IS NULL)) OR ((writer = 't9_blog'::text) AND (channel = 'blog'::text)) OR ((writer = 't9_social'::text) AND (channel IS NOT NULL) AND (channel <> 'blog'::text) AND (channel ~ '^[a-z_]{1,32}$'::text))))`
- check `writing_memory_shadow_output_check`: `CHECK ((((output IS NULL) OR ((jsonb_typeof(output) = 'object'::text) AND (pg_column_size(output) <= 131072))) AND ((output IS NULL) = (output_sha256 IS NULL)) AND ((output_sha256 IS NULL) OR (output_sha256 ~ '^[0-9a-f]{64}$'::text)) AND (input_sha256 ~ '^[0-9a-f]{64}$'::text) AND ((prompt_sha256 IS NULL) OR (prompt_sha256 ~ '^[0-9a-f]{64}$'::text))))`
- check `writing_memory_shadow_scope_check`: `CHECK ((scope = ANY (ARRAY['platform'::text, 'tenant'::text])))`
- check `writing_memory_shadow_scope_tenant_ck`: `CHECK ((((scope = 'platform'::text) AND (tenant_id IS NULL)) OR ((scope = 'tenant'::text) AND (tenant_id IS NOT NULL))))`
- check `writing_memory_shadow_size_check`: `CHECK (((jsonb_typeof(isolation) = 'object'::text) AND (pg_column_size(isolation) <= 8192) AND ((control_ref IS NULL) OR ((jsonb_typeof(control_ref) = 'object'::text) AND (pg_column_size(control_ref) <= 4096))) AND (cardinality(qa_artefacts) <= 50) AND (cost_usd >= (0)::numeric)))`
- check `writing_memory_shadow_source_check`: `CHECK ((input_source = ANY (ARRAY['content_piece'::text, 'tenant_tour_version'::text, 'generated_content'::text])))`
- check `writing_memory_shadow_verdict_check`: `CHECK ((verdict = ANY (ARRAY['pass'::text, 'fail'::text, 'error'::text])))`
- check `writing_memory_shadow_writer_check`: `CHECK ((writer = ANY (ARRAY['a1'::text, 't2'::text, 't9_blog'::text, 't9_social'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))` WITH CHECK `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))`
- policy `writing_memory_shadow_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `writing_memory_shadow_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`

### `shared.writing_memory_writer` (table, 32 kB)
```
writer text NN
memory_enabled boolean NN
train_closed_month date
updated_by text
updated_at timestamp with time zone NN
```
- owner `cis_owner`
- index `writing_memory_writer_pkey` PRIMARY KEY: UNIQUE btree (writer)
- check `writing_memory_writer_actor_check`: `CHECK ((((NOT memory_enabled) OR (updated_by IS NOT NULL)) AND (COALESCE(char_length(updated_by), 0) <= 128) AND ((train_closed_month IS NULL) OR (EXTRACT(day FROM train_closed_month) = (1)::numeric))))`
- check `writing_memory_writer_writer_check`: `CHECK ((writer = ANY (ARRAY['a1'::text, 't2'::text, 't9_blog'::text, 't9_social'::text])))`
- grant `cis_app`: SELECT, UPDATE
- trigger `writing_memory_writer_guard`: BEFORE UPDATE ON shared.writing_memory_writer FOR EACH ROW EXECUTE FUNCTION shared.writing_memory_writer_guard()

### `shared.writing_rule` (table, 128 kB)
```
rule_id uuid NN
kind text NN
scope text NN
tenant_id uuid
writer text NN
applies_to text[] NN
reason_code text
gate_class text
cluster_key text NN
rule_text text NN · pii:free_text
replacement text · pii:free_text
match_phrases text[] NN · pii:free_text
token_estimate integer
status text NN
signal_ids uuid[] NN
support_signals integer NN
support_pieces integer NN
support_tenants integer NN
support_reviewers integer NN
lint jsonb NN
drafted_by text
mine_job_id uuid
expires_at timestamp with time zone NN
approved_by text
approved_at timestamp with time zone
rejected_by text
rejected_reason text
created_at timestamp with time zone NN
updated_at timestamp with time zone NN
```
- owner `cis_owner` · RLS on + FORCE
- index `writing_rule_open_cluster_uq`: UNIQUE btree (writer, scope, COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), cluster_key) WHERE (status = ANY (ARRAY['candidate'::text, 'approved'::text, 'active'::text]))
- index `writing_rule_pkey` PRIMARY KEY: UNIQUE btree (rule_id)
- index `writing_rule_tenant_status_idx`: btree (tenant_id, status) WHERE (scope = 'tenant'::text)
- index `writing_rule_writer_status_idx`: btree (writer, status)
- check `writing_rule_approval_check`: `CHECK (((status <> ALL (ARRAY['approved'::text, 'active'::text])) OR ((approved_by IS NOT NULL) AND (approved_at IS NOT NULL))))`
- check `writing_rule_kind_check`: `CHECK ((kind = ANY (ARRAY['lexicon'::text, 'writer_instruction'::text, 'repair_hint'::text, 'preference_summary'::text])))`
- check `writing_rule_lint_check`: `CHECK ((jsonb_typeof(lint) = 'object'::text))`
- check `writing_rule_reason_code_check`: `CHECK (((reason_code IS NULL) OR (reason_code = ANY (ARRAY['fact_not_in_source'::text, 'optional_as_included'::text, 'wrong_place_or_time'::text, 'voice_off_brand'::text, 'ai_phrasing'::text, 'format_channel'::text, 'repair_residue'::text, 'style_only'::text]))))`
- check `writing_rule_replacement_check`: `CHECK (((replacement IS NULL) OR (kind = 'lexicon'::text)))`
- check `writing_rule_scope_check`: `CHECK ((scope = ANY (ARRAY['platform'::text, 'tenant'::text])))`
- check `writing_rule_scope_tenant_ck`: `CHECK ((((scope = 'platform'::text) AND (tenant_id IS NULL)) OR ((scope = 'tenant'::text) AND (tenant_id IS NOT NULL))))`
- check `writing_rule_size_check`: `CHECK (((char_length(rule_text) <= 1000) AND (COALESCE(char_length(replacement), 0) <= 200) AND ((char_length(cluster_key) >= 1) AND (char_length(cluster_key) <= 200)) AND (COALESCE(char_length(gate_class), 0) <= 128) AND (cardinality(applies_to) <= 8) AND (cardinality(match_phrases) <= 5) AND (char_length(array_to_string(match_phrases, ''::text)) <= 400) AND (cardinality(signal_ids) <= 500) AND (COALESCE(char_length(drafted_by), 0) <= 128) AND (COALESCE(char_length(approved_by), 0) <= 128) AND (COALESCE(char_length(rejected_by), 0) <= 128) AND (COALESCE(char_length(rejected_reason), 0) <= 500)))`
- check `writing_rule_status_check`: `CHECK ((status = ANY (ARRAY['candidate'::text, 'rejected'::text, 'approved'::text, 'active'::text, 'expired'::text])))`
- check `writing_rule_summary_scope_check`: `CHECK (((kind <> 'preference_summary'::text) OR (scope = 'tenant'::text)))`
- check `writing_rule_support_check`: `CHECK (((support_signals >= 0) AND (support_pieces >= 0) AND (support_tenants >= 0) AND (support_reviewers >= 0) AND ((scope = 'tenant'::text) OR (support_tenants = 0) OR (support_tenants >= 3)) AND ((scope = 'platform'::text) OR (support_tenants <= 1))))`
- check `writing_rule_words_check`: `CHECK (((char_length(btrim(rule_text)) > 0) AND
CASE
    WHEN (kind = 'preference_summary'::text) THEN ((array_length(regexp_split_to_array(btrim(rule_text), '\s+'::text), 1) <= 125) AND (char_length(regexp_replace(regexp_replace(btrim(rule_text), '[.!?]+'::text, '.'::text, 'g'::text), '[^.]'::text, ''::text, 'g'::text)) <= 5))
    ELSE (array_length(regexp_split_to_array(btrim(rule_text), '\s+'::text), 1) <= 25)
END))`
- check `writing_rule_writer_check`: `CHECK ((writer = ANY (ARRAY['a1'::text, 't2'::text, 't9_blog'::text, 't9_social'::text])))`
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))` WITH CHECK `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))`
- policy `writing_rule_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `writing_rule_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- trigger `writing_rule_token_cap`: AFTER INSERT OR UPDATE ON shared.writing_rule FOR EACH ROW EXECUTE FUNCTION shared.writing_rule_token_cap()

### `shared.writing_signal` (table, ~580 rows, 2.1 MB)
```
signal_id uuid NN
writer text NN
channel text
scope text NN
tenant_id uuid
field text
locator jsonb
before_text text · pii:free_text
after_text text · pii:free_text
before_sha256 text
after_sha256 text
gate text
problem text · pii:free_text
reason_code text
action text NN
actor_type text NN
actor_id text
fact_status text NN
exemplar_pref text
audit_log_id uuid
source_table text NN
source_id text NN
created_at timestamp with time zone NN
```
- owner `cis_owner` · RLS on + FORCE
- index `writing_signal_pkey` PRIMARY KEY: UNIQUE btree (signal_id)
- index `writing_signal_source_idx`: btree (source_table, source_id)
- index `writing_signal_tenant_created_idx`: btree (tenant_id, created_at DESC) WHERE (scope = 'tenant'::text)
- index `writing_signal_writer_created_idx`: btree (writer, created_at DESC)
- check `writing_signal_action_check`: `CHECK ((action = ANY (ARRAY['field_edit'::text, 'sentence_cut'::text, 'sentence_rewrite'::text, 'sentence_manual'::text, 'tenant_edit'::text, 'reject'::text, 'dismiss'::text, 'regenerate'::text])))`
- check `writing_signal_actor_type_check`: `CHECK ((actor_type = ANY (ARRAY['admin'::text, 'tenant'::text, 'system'::text])))`
- check `writing_signal_exemplar_pref_check`: `CHECK (((exemplar_pref IS NULL) OR (exemplar_pref = ANY (ARRAY['use'::text, 'never'::text]))))`
- check `writing_signal_fact_status_check`: `CHECK ((fact_status = ANY (ARRAY['pending'::text, 'grey'::text, 'pass'::text, 'fail'::text])))`
- check `writing_signal_locator_check`: `CHECK (((locator IS NULL) OR (jsonb_typeof(locator) = 'object'::text)))`
- check `writing_signal_reason_code_check`: `CHECK (((reason_code IS NULL) OR (reason_code = ANY (ARRAY['fact_not_in_source'::text, 'optional_as_included'::text, 'wrong_place_or_time'::text, 'voice_off_brand'::text, 'ai_phrasing'::text, 'format_channel'::text, 'repair_residue'::text, 'style_only'::text]))))`
- check `writing_signal_scope_check`: `CHECK ((scope = ANY (ARRAY['platform'::text, 'tenant'::text])))`
- check `writing_signal_scope_tenant_ck`: `CHECK ((((scope = 'platform'::text) AND (tenant_id IS NULL)) OR ((scope = 'tenant'::text) AND (tenant_id IS NOT NULL))))`
- check `writing_signal_sha256_check`: `CHECK ((((before_text IS NULL) OR (before_sha256 IS NOT NULL)) AND ((after_text IS NULL) OR (after_sha256 IS NOT NULL)) AND ((before_sha256 IS NULL) OR (before_sha256 ~ '^[0-9a-f]{64}$'::text)) AND ((after_sha256 IS NULL) OR (after_sha256 ~ '^[0-9a-f]{64}$'::text))))`
- check `writing_signal_size_check`: `CHECK (((COALESCE(char_length(before_text), 0) <= 200000) AND (COALESCE(char_length(after_text), 0) <= 200000) AND (COALESCE(char_length(field), 0) <= 200) AND (COALESCE(char_length(channel), 0) <= 64) AND (COALESCE(char_length(gate), 0) <= 128) AND (COALESCE(char_length(actor_id), 0) <= 128) AND (COALESCE(char_length(problem), 0) <= 2000)))`
- check `writing_signal_source_check`: `CHECK ((((char_length(source_table) >= 1) AND (char_length(source_table) <= 128)) AND ((char_length(source_id) >= 1) AND (char_length(source_id) <= 128))))`
- check `writing_signal_writer_check`: `CHECK ((writer = ANY (ARRAY['a1'::text, 't2'::text, 't9_blog'::text, 't9_social'::text])))`
- grant `aa_app_user`: INSERT, SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `tenant_isolation` (PERMISSIVE ALL TO aa_app_user): USING `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))` WITH CHECK `((scope = 'tenant'::text) AND (tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid))`
- policy `writing_signal_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `writing_signal_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`

## `silver_aa_internal` (7 objects)

### `silver_aa_internal.generated_content` (table, ~2296 rows, 18.8 MB)
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
- check `generated_content_satellite_account_valid`: `CHECK (((satellite_account IS NULL) OR (satellite_account = ANY (ARRAY['acc1'::text, 'acc3'::text]))))`
- grant `aa_app_user`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `generated_content_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `generated_content_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`

### `silver_aa_internal.quality_scores` (table, ~2272 rows, 2.4 MB)
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

### `silver_aa_internal.raw_tours` (table, ~987 rows, 6.5 MB)
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
country_iso2 character(2)
```
- owner `cis_owner` · RLS on + FORCE
- index `idx_aa_internal_raw_tours_batch`: btree (batch_id)
- index `idx_aa_internal_raw_tours_country`: btree (country)
- index `idx_aa_internal_raw_tours_status`: btree (pipeline_status)
- index `idx_raw_tours_country_raw_unresolved`: btree (country_raw_unresolved) WHERE (country_raw_unresolved IS NOT NULL)
- index `idx_raw_tours_review_status`: btree (review_status)
- index `raw_tours_country_iso2_idx`: btree (country_iso2)
- index `raw_tours_pkey` PRIMARY KEY: UNIQUE btree (tour_id)
- index `raw_tours_source_key_idx`: btree (source_key)
- index `uq_raw_tours_active_per_group`: UNIQUE btree (source_group_id) WHERE (source_status = 'active'::silver_aa_internal.source_status_enum)
- check `raw_tours_country_iso2_set`: `CHECK (((country IS NULL) = (country_iso2 IS NULL)))`
- check `raw_tours_review_status_check`: `CHECK (((review_status)::text = ANY (ARRAY[('pending_review'::character varying)::text, ('reviewed'::character varying)::text, ('approved'::character varying)::text, ('rejected'::character varying)::text])))`
- grant `aa_app_user`: SELECT
- grant `catalog_owner`: SELECT
- grant `cis_app`: DELETE, INSERT, SELECT, UPDATE
- policy `aa_app_user_aa_master_read` (PERMISSIVE SELECT TO aa_app_user): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `catalog_owner_aa_master_read` (PERMISSIVE SELECT TO catalog_owner): USING `(tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)`
- policy `raw_tours_cis_app_all` (PERMISSIVE ALL TO cis_app): USING `true` WITH CHECK `true`
- policy `raw_tours_cis_owner_all` (PERMISSIVE ALL TO cis_owner): USING `true` WITH CHECK `true`
- policy `tenant_isolation` (PERMISSIVE ALL TO public): USING `(tenant_id = (NULLIF(current_setting('app.tenant_id'::text, true), ''::text))::uuid)`
- trigger `raw_tours_country_iso2`: BEFORE INSERT OR UPDATE OF country ON silver_aa_internal.raw_tours FOR EACH ROW EXECUTE FUNCTION shared.set_country_iso2()

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

### `silver_aa_internal.seo_context` (table, ~918 rows, 1.3 MB)
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

## `tripplanner` (15 objects)

### `tripplanner.component_id_map` (table, ~750 rows, 136 kB)
```
old_id uuid NN
new_id uuid NN
matched_by text NN
created_at timestamp with time zone NN
```
- owner `tp_owner`
- index `component_id_map_pkey` PRIMARY KEY: UNIQUE btree (old_id)
- check `component_id_map_matched_by_check`: `CHECK ((matched_by = ANY (ARRAY['name'::text, 'destination'::text])))`
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

### `tripplanner.job` (table, 120 kB)
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
- owner `tp_owner`
- index `job_finished_idx`: btree (finished_at, id) WHERE (finished_at IS NOT NULL)
- index `job_idempotency_key_uq`: UNIQUE btree (idempotency_key) WHERE (idempotency_key IS NOT NULL)
- index `job_kind_created_idx`: btree (kind, created_at DESC)
- index `job_parent_idx`: btree (parent_job_id) WHERE (parent_job_id IS NOT NULL)
- index `job_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `job_queued_due_idx`: btree (run_after, created_at) WHERE (status = 'queued'::text)
- index `job_running_idx`: btree (kind, locked_until) WHERE (status = 'running'::text)
- check `job_attempts_chk`: `CHECK (((attempt >= 0) AND (max_attempts >= 1)))`
- check `job_kind_chk`: `CHECK ((kind ~ '^tp_[a-z0-9_]+$'::text))`
- check `job_lease_chk`: `CHECK (((status <> 'running'::text) OR ((locked_by IS NOT NULL) AND (locked_until IS NOT NULL))))`
- check `job_status_chk`: `CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text, 'cancelled'::text])))`
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE
- trigger `job_set_updated_at`: BEFORE UPDATE ON tripplanner.job FOR EACH ROW EXECUTE FUNCTION tripplanner.job_set_updated_at()

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
- check `narration_cache_mode_chk`: `CHECK ((mode = ANY (ARRAY['compose'::text, 'renarrate'::text])))`
- check `narration_cache_source_chk`: `CHECK ((source = ANY (ARRAY['llm'::text, 'mixed'::text])))`
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.outbox` (table, ~7 rows, 112 kB)
```
id bigint NN
event text NN
schema_version integer NN
idempotency_key text NN
aggregate_id uuid NN
payload jsonb NN · pii:contact (also pii:name, pii:free_text, pii:travel)
created_at timestamp with time zone NN
redacted_at timestamp with time zone
```
- owner `tp_owner`
- index `outbox_event_id_idx`: btree (event, id)
- index `outbox_idempotency_key_key`: UNIQUE btree (idempotency_key)
- index `outbox_pkey` PRIMARY KEY: UNIQUE btree (id)
- index `outbox_redact_due_idx`: btree (created_at, id) WHERE (redacted_at IS NULL)
- check `outbox_event_chk`: `CHECK ((event = 'inquiry.submitted'::text))`
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.sessions` (table, ~102 rows, 96 kB)
```
id uuid NN
guest_token text · conf:credential
customer_id uuid
created_at timestamp with time zone NN
expires_at timestamp with time zone
guest_token_hash bytea · conf:credential
account_id uuid
```
- owner `tp_owner`
- index `sessions_account_idx`: btree (account_id) WHERE (account_id IS NOT NULL)
- index `sessions_guest_token_key`: UNIQUE btree (guest_token)
- index `sessions_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `sessions_guest_token_hash_len_chk`: `CHECK (((guest_token_hash IS NULL) OR (octet_length(guest_token_hash) = 32)))`
- check `sessions_guest_token_retired_chk`: `CHECK ((guest_token IS NULL))`
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.traveller_accounts` (table, 48 kB)
```
id uuid NN
iss text NN · pii:online_id
sub text NN · pii:online_id
created_at timestamp with time zone NN
last_sign_in_at timestamp with time zone
```
- owner `tp_owner`
- index `traveller_accounts_iss_sub_key`: UNIQUE btree (iss, sub)
- index `traveller_accounts_pkey` PRIMARY KEY: UNIQUE btree (id)
- check `traveller_accounts_iss_chk`: `CHECK (((iss ~ '^https://'::text) AND (length(iss) <= 300)))`
- check `traveller_accounts_sub_chk`: `CHECK (((length(sub) >= 1) AND (length(sub) <= 128)))`
- grant `tripplanner`: INSERT, SELECT, UPDATE

### `tripplanner.trip_drafts` (table, ~98 rows, 144 kB)
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
- check `trip_drafts_status_chk`: `CHECK ((status = ANY (ARRAY['draft'::text, 'sent'::text])))`
- grant `tripplanner`: DELETE, INSERT, SELECT, UPDATE

### `tripplanner.trip_events` (table, ~416 rows, 192 kB)
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
- check `trip_events_type_chk`: `CHECK ((event_type = ANY (ARRAY['add_component'::text, 'remove_component'::text, 'reorder'::text, 'sent'::text, 'add_day'::text, 'remove_day'::text])))`
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

### `tripplanner.v_ops_component_id_map` (VIEW)
```
old_id text
new_id text
```
- owner `tp_owner`
- grant `cis_app`: SELECT
- grant `tripplanner`: SELECT

### `tripplanner.v_ops_data_totals` (VIEW)
```
metric text
n bigint
```
- owner `tp_owner`
- grant `cis_app`: SELECT
- grant `tripplanner`: SELECT

### `tripplanner.v_ops_pin_components` (VIEW)
```
component_id text
trips bigint
```
- owner `tp_owner`
- grant `cis_app`: SELECT
- grant `tripplanner`: SELECT

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
| `cis_owner` | acp_shared | functions | `cis_app` | EXECUTE |
| `cis_owner` | acp_shared | tables | `cis_app` | DELETE,INSERT,SELECT,UPDATE |
| `cis_owner` | acp_shared | sequences | `cis_app` | SELECT,UPDATE,USAGE |
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
| `booking.entity_media_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.entity_media_supply_bump()` | trigger | plpgsql | `bk_owner` | no |
| `booking.hotel_room_types_supply_bump()` | trigger | plpgsql | `bk_owner` | no |
| `booking.hotels_supply_version()` | trigger | plpgsql | `bk_owner` | no |
| `booking.invoice_items_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.invoice_items_settle()` | trigger | plpgsql | `bk_owner` | no |
| `booking.invoice_money_state(p_invoice uuid, p_total numeric)` | text | sql | `bk_owner` | no |
| `booking.invoice_net_paid(p_invoice uuid)` | numeric | sql | `bk_owner` | no |
| `booking.invoice_settle(p_invoice uuid)` | text | plpgsql | `bk_owner` | no |
| `booking.invoices_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.ops_check_transition()` | trigger | plpgsql | `bk_owner` | no |
| `booking.ops_files_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.outbox_departure_event(p_departure uuid, p_type text, p_incident text)` | void | sql | `bk_owner` | no |
| `booking.payment_schedule_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.payments_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.payments_settle()` | trigger | plpgsql | `bk_owner` | no |
| `booking.policy_approval_maker_checker()` | trigger | plpgsql | `bk_owner` | no |
| `booking.services_supply_version()` | trigger | plpgsql | `bk_owner` | no |
| `booking.set_updated_at()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_bill_items_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_bill_paid(p_bill uuid)` | numeric | sql | `bk_owner` | no |
| `booking.supplier_bill_settle(p_bill uuid)` | text | plpgsql | `bk_owner` | no |
| `booking.supplier_bills_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_bookings_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_contract_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_contract_rates_fit()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_payouts_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_payouts_settle()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supplier_rate_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.supply_outbox()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_check_transition()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_checks_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_record_status()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_seed_checks()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_version_item_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_version_item_sent_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_version_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_case_version_sent_lock()` | trigger | plpgsql | `bk_owner` | no |
| `booking.trip_cases_post_sale_guard()` | trigger | plpgsql | `bk_owner` | no |
| `booking.version_item_cost_lock()` | trigger | plpgsql | `bk_owner` | no |
| `crm.aa_line_request(p_trip uuid, p_source_id text, p_component_id text, p_component_kind text, p_departure_id text, p_service_date date, p_nights integer, p_adult integer, p_child integer, p_infant integer, p_rooms jsonb, p_currency text, p_sell numeric)` | uuid | plpgsql | `crm_owner` | **yes** |
| `crm.audit_drop_expired_partitions(p_dry_run boolean)` | TABLE(partition_name text, range_end timestamp with time zone, action text) | plpgsql | `crm_owner` | **yes** |
| `crm.audit_ensure_partitions()` | integer | plpgsql | `crm_owner` | **yes** |
| `crm.audit_event_check_at()` | trigger | plpgsql | `crm_owner` | no |
| `crm.audit_export_agencies()` | TABLE(tenant_id uuid, exported_until timestamp with time zone, verified_until timestamp with time zone, last_seq bigint, registered_at timestamp with time zone) | sql | `crm_owner` | **yes** |
| `crm.audit_manifest_chain()` | trigger | plpgsql | `crm_owner` | no |
| `crm.audit_mark_verified(p_until timestamp with time zone)` | boolean | plpgsql | `crm_owner` | **yes** |
| `crm.audit_partition_bounds()` | TABLE(partition_name text, range_start timestamp with time zone, range_end timestamp with time zone) | sql | `crm_owner` | no |
| `crm.audit_register_tenant()` | trigger | plpgsql | `crm_owner` | no |
| `crm.booking_line_aa_money(p_line uuid, p_kind text, p_amount numeric, p_currency text, p_rate_per_usd numeric, p_rate_date date)` | uuid | plpgsql | `crm_owner` | **yes** |
| `crm.booking_line_confirm(p_line uuid)` | jsonb | plpgsql | `crm_owner` | **yes** |
| `crm.booking_line_confirm_check(p_line uuid)` | text[] | plpgsql | `crm_owner` | **yes** |
| `crm.booking_line_money_chain()` | trigger | plpgsql | `crm_owner` | no |
| `crm.booking_line_money_put(p_line uuid, p_kind text, p_amount numeric, p_currency text)` | uuid | plpgsql | `crm_owner` | **yes** |
| `crm.booking_line_money_write(p_line uuid, p_kind text, p_amount numeric, p_currency text, p_status text, p_confirmed_at timestamp with time zone)` | uuid | plpgsql | `crm_owner` | no |
| `crm.call_slot_rules_ok(p jsonb)` | boolean | plpgsql | `crm_owner` | no |
| `crm.completeness_ok(p jsonb)` | boolean | plpgsql | `crm_owner` | no |
| `crm.enforce_stage_transition()` | trigger | plpgsql | `crm_owner` | no |
| `crm.enforce_status_transition()` | trigger | plpgsql | `crm_owner` | no |
| `crm.ensure_aa_supplier()` | uuid | plpgsql | `crm_owner` | **yes** |
| `crm.erasable_append_only()` | trigger | plpgsql | `crm_owner` | no |
| `crm.erase_held(p_scope text, p_subject uuid, p_token uuid)` | boolean | plpgsql | `crm_owner` | no |
| `crm.erase_rows(p_table text, p_where text, p_subject uuid, p_token uuid, p_dry_run boolean, p_set text)` | bigint | plpgsql | `crm_owner` | no |
| `crm.erase_subject(p_scope text, p_subject uuid, p_profile_token uuid, p_dry_run boolean)` | jsonb | plpgsql | `crm_owner` | **yes** |
| `crm.fx_resolve(p_from text, p_to text, p_date date)` | TABLE(rate numeric, rate_date date, fx_source text, stale_days integer) | plpgsql | `crm_owner` | no |
| `crm.guard_agency_supplier()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_booking_line()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_channel_account()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_dispatch_attempt()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_erasure_request_owner_confirm()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_held_change()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_invitation_write()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_legal_hold()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_member_write()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_message()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_metric_event()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_owner_recovery()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_platform_write()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_proposal_draft()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_sealed_row()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_selection()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_set_once()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_studio_invitation_write()` | trigger | plpgsql | `crm_owner` | no |
| `crm.guard_traveler_access()` | trigger | plpgsql | `crm_owner` | no |
| `crm.hold_row(p_trip uuid, p_traveler uuid)` | boolean | sql | `crm_owner` | no |
| `crm.hold_traveler(p_traveler uuid)` | boolean | sql | `crm_owner` | no |
| `crm.hold_trip(p_trip uuid)` | boolean | sql | `crm_owner` | no |
| `crm.job_set_updated_at()` | trigger | plpgsql | `crm_owner` | no |
| `crm.ledger_append_only()` | trigger | plpgsql | `crm_owner` | no |
| `crm.legal_hold_blocks(p_scope text, p_subject uuid)` | boolean | sql | `crm_owner` | no |
| `crm.lifecycle_purge_expired(p_dry_run boolean)` | jsonb | plpgsql | `crm_owner` | **yes** |
| `crm.membership_inbox_append_only()` | trigger | plpgsql | `crm_owner` | no |
| `crm.pin_stage_history_insert()` | trigger | plpgsql | `crm_owner` | no |
| `crm.portal_unlocked(p_trip uuid)` | boolean | sql | `crm_owner` | no |
| `crm.reject_append_only_change()` | trigger | plpgsql | `crm_owner` | no |
| `crm.relation_inverse(kind text)` | text | sql | `crm_owner` | no |
| `crm.set_agreement_doc_sha256()` | trigger | plpgsql | `crm_owner` | no |
| `crm.set_updated_at()` | trigger | plpgsql | `crm_owner` | no |
| `crm.sync_tenant_lock_source()` | trigger | plpgsql | `crm_owner` | no |
| `crm.tenant_key_guard()` | trigger | plpgsql | `crm_owner` | no |
| `crm.traveler_health_consent()` | trigger | plpgsql | `crm_owner` | no |
| `crm.traveler_relation_mirror()` | trigger | plpgsql | `crm_owner` | no |
| `crm.traveler_relation_pair()` | trigger | plpgsql | `crm_owner` | no |
| `crm.trip_delete_blockers(p_trip uuid)` | text[] | sql | `crm_owner` | no |
| `geo.line_vertex_count(g jsonb)` | integer | sql | `cis_owner` | no |
| `geo.name_norm(p text)` | text | sql | `cis_owner` | no |
| `gold_aa_internal.aa_content_item_guard()` | trigger | plpgsql | `cis_owner` | no |
| `gold_aa_internal.aa_content_version_guard()` | trigger | plpgsql | `cis_owner` | no |
| `gold_aa_internal.tour_lifecycle_event_append_only()` | trigger | plpgsql | `cis_owner` | no |
| `shared.country_iso2(p_country text)` | character | sql | `cis_owner` | no |
| `shared.create_tenant_schemas(p_slug character varying)` | void | plpgsql | `cis_owner` | no |
| `shared.eval_item_result_guard()` | trigger | plpgsql | `cis_owner` | no |
| `shared.job_set_updated_at()` | trigger | plpgsql | `cis_owner` | no |
| `shared.prompt_eval_runs_freeze()` | trigger | plpgsql | `cis_owner` | no |
| `shared.schema_versions_key_guard()` | trigger | plpgsql | `cis_owner` | no |
| `shared.set_country_iso2()` | trigger | plpgsql | `cis_owner` | no |
| `shared.supply_content_version_guard()` | trigger | plpgsql | `cis_owner` | no |
| `shared.tenant_members_guard()` | trigger | plpgsql | `cis_owner` | no |
| `shared.tenant_membership_emit_member()` | trigger | plpgsql | `cis_owner` | no |
| `shared.tenant_membership_emit_tenant()` | trigger | plpgsql | `cis_owner` | no |
| `shared.tenant_membership_event_guard()` | trigger | plpgsql | `cis_owner` | no |
| `shared.writing_memory_release_guard()` | trigger | plpgsql | `cis_owner` | no |
| `shared.writing_memory_writer_guard()` | trigger | plpgsql | `cis_owner` | no |
| `shared.writing_rule_token_cap()` | trigger | plpgsql | `cis_owner` | no |
| `tripplanner.job_set_updated_at()` | trigger | plpgsql | `tp_owner` | no |

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
booking.country_profiles.country_code -> booking.countries.iso2
booking.country_profiles.updated_by -> booking.staff_users.cis_user_id
booking.customer_identities.customer_id -> booking.customers.id
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
booking.destination_profiles.updated_by -> booking.staff_users.cis_user_id
booking.entity_media.updated_by -> booking.staff_users.cis_user_id
booking.entity_media.uploaded_by -> booking.staff_users.cis_user_id
booking.fx_rates.created_by -> booking.staff_users.cis_user_id
booking.hotel_room_types.created_by -> booking.staff_users.cis_user_id
booking.hotel_room_types.hotel_id -> booking.hotels.id
booking.hotel_room_types.updated_by -> booking.staff_users.cis_user_id
booking.hotels.country_code -> booking.countries.iso2
booking.hotels.created_by -> booking.staff_users.cis_user_id
booking.hotels.supplier_id -> booking.suppliers.id
booking.hotels.updated_by -> booking.staff_users.cis_user_id
booking.invoice_items.created_by -> booking.staff_users.cis_user_id
booking.invoice_items.invoice_id -> booking.invoices.id
booking.invoice_items.updated_by -> booking.staff_users.cis_user_id
booking.invoices.cancelled_by -> booking.staff_users.cis_user_id
booking.invoices.created_by -> booking.staff_users.cis_user_id
booking.invoices.customer_id -> booking.customers.id
booking.invoices.sent_by -> booking.staff_users.cis_user_id
booking.invoices.trip_case_id -> booking.trip_cases.id
booking.invoices.updated_by -> booking.staff_users.cis_user_id
booking.invoices.version_id -> booking.trip_case_versions.id
booking.job.parent_job_id -> booking.job.id
booking.notification_reads.cis_user_id -> booking.staff_users.cis_user_id
booking.notification_reads.notification_id -> booking.notifications.id
booking.ops_files.removed_by -> booking.staff_users.cis_user_id
booking.ops_files.trip_case_id -> booking.trip_cases.id
booking.ops_files.uploaded_by -> booking.staff_users.cis_user_id
booking.payment_schedule.created_by -> booking.staff_users.cis_user_id
booking.payment_schedule.invoice_id -> booking.invoices.id
booking.payment_schedule.updated_by -> booking.staff_users.cis_user_id
booking.payments.evidence_file_id -> booking.ops_files.id
booking.payments.invoice_id -> booking.invoices.id
booking.payments.recorded_by -> booking.staff_users.cis_user_id
booking.payments.updated_by -> booking.staff_users.cis_user_id
booking.payments.verified_by -> booking.staff_users.cis_user_id
booking.payments.voided_by -> booking.staff_users.cis_user_id
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
booking.supplier_bill_items.bill_id -> booking.supplier_bills.id
booking.supplier_bill_items.created_by -> booking.staff_users.cis_user_id
booking.supplier_bill_items.supplier_booking_id -> booking.supplier_bookings.id
booking.supplier_bills.approved_by -> booking.staff_users.cis_user_id
booking.supplier_bills.cancelled_by -> booking.staff_users.cis_user_id
booking.supplier_bills.created_by -> booking.staff_users.cis_user_id
booking.supplier_bills.document_file_id -> booking.ops_files.id
booking.supplier_bills.facts_edited_by -> booking.staff_users.cis_user_id
booking.supplier_bills.supplier_id -> booking.suppliers.id
booking.supplier_bills.trip_case_id -> booking.trip_cases.id
booking.supplier_bills.updated_by -> booking.staff_users.cis_user_id
booking.supplier_bookings.(b2b_hold_id,b2b_line_ref) -> booking.b2b_hold_lines.(hold_id,line_ref)
booking.supplier_bookings.confirmed_by -> booking.staff_users.cis_user_id
booking.supplier_bookings.created_by -> booking.staff_users.cis_user_id
booking.supplier_bookings.hotel_room_type_id -> booking.hotel_room_types.id
booking.supplier_bookings.requested_by -> booking.staff_users.cis_user_id
booking.supplier_bookings.service_id -> booking.services.id
booking.supplier_bookings.supplier_id -> booking.suppliers.id
booking.supplier_bookings.trip_case_id -> booking.trip_cases.id
booking.supplier_bookings.updated_by -> booking.staff_users.cis_user_id
booking.supplier_bookings.version_item_id -> booking.trip_case_version_itinerary.id
booking.supplier_bookings.voucher_file_id -> booking.ops_files.id
booking.supplier_contracts.created_by -> booking.staff_users.cis_user_id
booking.supplier_contracts.expired_by -> booking.staff_users.cis_user_id
booking.supplier_contracts.published_by -> booking.staff_users.cis_user_id
booking.supplier_contracts.supplier_id -> booking.suppliers.id
booking.supplier_contracts.updated_by -> booking.staff_users.cis_user_id
booking.supplier_payouts.bill_id -> booking.supplier_bills.id
booking.supplier_payouts.evidence_file_id -> booking.ops_files.id
booking.supplier_payouts.recorded_by -> booking.staff_users.cis_user_id
booking.supplier_payouts.updated_by -> booking.staff_users.cis_user_id
booking.supplier_payouts.voided_by -> booking.staff_users.cis_user_id
booking.supplier_rates.created_by -> booking.staff_users.cis_user_id
booking.supplier_rates.hotel_room_type_id -> booking.hotel_room_types.id
booking.supplier_rates.service_id -> booking.services.id
booking.supplier_rates.supplier_contract_id -> booking.supplier_contracts.id
booking.supplier_rates.updated_by -> booking.staff_users.cis_user_id
booking.suppliers.country_code -> booking.countries.iso2
booking.suppliers.created_by -> booking.staff_users.cis_user_id
booking.suppliers.updated_by -> booking.staff_users.cis_user_id
booking.trip_case_checks.assignee_ref -> booking.staff_users.cis_user_id
booking.trip_case_checks.created_by -> booking.staff_users.cis_user_id
booking.trip_case_checks.done_by -> booking.staff_users.cis_user_id
booking.trip_case_checks.trip_case_id -> booking.trip_cases.id
booking.trip_case_checks.updated_by -> booking.staff_users.cis_user_id
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
booking.trip_plan_prices.created_by -> booking.staff_users.cis_user_id
booking.trip_plan_prices.trip_plan_id -> booking.trip_plans.id
booking.trip_plans.created_by -> booking.staff_users.cis_user_id
booking.trip_plans.supplier_id -> booking.suppliers.id
booking.trip_plans.updated_by -> booking.staff_users.cis_user_id
booking.version_item_costs.entered_by -> booking.staff_users.cis_user_id
booking.version_item_costs.supplier_rate_id -> booking.supplier_rates.id
booking.version_item_costs.version_item_id -> booking.trip_case_version_itinerary.id
crm.aa_request.tenant_id -> crm.tenant.tenant_id
crm.aa_request.(tenant_id,booking_line_id) -> crm.booking_line.(tenant_id,booking_line_id)
crm.aa_request.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.agency_supplier.tenant_id -> crm.tenant.tenant_id
crm.agreement_doc.tenant_id -> crm.tenant.tenant_id
crm.audit_event.tenant_id -> crm.tenant.tenant_id
crm.audit_event_legacy.tenant_id -> crm.tenant.tenant_id
crm.audit_event_p202611.tenant_id -> crm.tenant.tenant_id
crm.audit_event_p202612.tenant_id -> crm.tenant.tenant_id
crm.audit_event_p202701.tenant_id -> crm.tenant.tenant_id
crm.audit_export_tenant.tenant_id -> crm.tenant.tenant_id
crm.booking_feed_state.tenant_id -> crm.tenant.tenant_id
crm.booking_line.tenant_id -> crm.tenant.tenant_id
crm.booking_line.(tenant_id,agency_supplier_id) -> crm.agency_supplier.(tenant_id,agency_supplier_id)
crm.booking_line.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.booking_line_money.tenant_id -> crm.tenant.tenant_id
crm.booking_line_money.(tenant_id,booking_line_id) -> crm.booking_line.(tenant_id,booking_line_id)
crm.booking_line_money.(tenant_id,supersedes_id) -> crm.booking_line_money.(tenant_id,booking_line_money_id)
crm.channel_account.tenant_id -> crm.tenant.tenant_id
crm.channel_account.(tenant_id,credential_id) -> crm.integration_credential.(tenant_id,integration_credential_id)
crm.channel_account.(tenant_id,member_id) -> crm.member.(tenant_id,member_id)
crm.client_link.tenant_id -> crm.tenant.tenant_id
crm.client_link.(tenant_id,dispatch_id) -> crm.dispatch_queue.(tenant_id,dispatch_id)
crm.client_link.(tenant_id,reissued_from) -> crm.client_link.(tenant_id,link_id)
crm.client_link.(tenant_id,traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.client_link.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.consent.submission_id -> crm.form_submission.submission_id
crm.consent.tenant_id -> crm.tenant.tenant_id
crm.consent.traveler_id -> crm.traveler.traveler_id
crm.conversation.tenant_id -> crm.tenant.tenant_id
crm.conversation.(tenant_id,traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.conversation.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.dispatch_attempt.tenant_id -> crm.tenant.tenant_id
crm.dispatch_attempt.(tenant_id,dispatch_id) -> crm.dispatch_queue.(tenant_id,dispatch_id)
crm.dispatch_queue.tenant_id -> crm.tenant.tenant_id
crm.dispatch_queue.(tenant_id,message_id) -> crm.message.(tenant_id,message_id)
crm.dispatch_queue.(tenant_id,traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.dispatch_queue.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.document.tenant_id -> crm.tenant.tenant_id
crm.document.(tenant_id,traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.document.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.erasure_request.tenant_id -> crm.tenant.tenant_id
crm.form_definition.tenant_id -> crm.tenant.tenant_id
crm.form_submission.intake_form_id -> crm.intake_form.intake_form_id
crm.form_submission.tenant_id -> crm.tenant.tenant_id
crm.form_submission.(tenant_id,client_link_id,trip_id,traveler_id) -> crm.client_link.(tenant_id,link_id,trip_id,traveler_id)
crm.form_submission.traveler_id -> crm.traveler.traveler_id
crm.form_submission.trip_id -> crm.trip.trip_id
crm.fx_rate_override.tenant_id -> crm.tenant.tenant_id
crm.fx_rate_override.(tenant_id,set_by) -> crm.member.(tenant_id,member_id)
crm.inbox_events.tenant_id -> crm.tenant.tenant_id
crm.ingest_address.tenant_id -> crm.tenant.tenant_id
crm.intake_form.default_owner_member_id -> crm.member.member_id
crm.intake_form.form_definition_id -> crm.form_definition.form_definition_id
crm.intake_form.tenant_id -> crm.tenant.tenant_id
crm.integration_credential.tenant_id -> crm.tenant.tenant_id
crm.integration_credential.(tenant_id,member_id) -> crm.member.(tenant_id,member_id)
crm.job.parent_job_id -> crm.job.id
crm.legal_hold.tenant_id -> crm.tenant.tenant_id
crm.lifecycle_run.tenant_id -> crm.tenant.tenant_id
crm.llm_call.tenant_id -> crm.tenant.tenant_id
crm.mail_import.tenant_id -> crm.tenant.tenant_id
crm.mail_import.(tenant_id,member_id) -> crm.member.(tenant_id,member_id)
crm.meeting_slot.tenant_id -> crm.tenant.tenant_id
crm.meeting_slot.(tenant_id,form_submission_id) -> crm.form_submission.(tenant_id,submission_id)
crm.meeting_slot.(tenant_id,traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.meeting_slot.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.member.tenant_id -> crm.tenant.tenant_id
crm.member_invitation.tenant_id -> crm.tenant.tenant_id
crm.member_invitation.(tenant_id,member_id) -> crm.member.(tenant_id,member_id)
crm.message.tenant_id -> crm.tenant.tenant_id
crm.message.(tenant_id,author_member_id) -> crm.member.(tenant_id,member_id)
crm.message.(tenant_id,channel_account_id) -> crm.channel_account.(tenant_id,channel_account_id)
crm.message.(tenant_id,conversation_id) -> crm.conversation.(tenant_id,conversation_id)
crm.message_template.tenant_id -> crm.tenant.tenant_id
crm.metric_event.tenant_id -> crm.tenant.tenant_id
crm.metric_event.(tenant_id,bell_member_id) -> crm.member.(tenant_id,member_id)
crm.metric_event.(tenant_id,proposal_id,trip_id) -> crm.proposal.(tenant_id,proposal_id,trip_id)
crm.metric_event.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.note.tenant_id -> crm.tenant.tenant_id
crm.note.traveler_id -> crm.traveler.traveler_id
crm.note.trip_id -> crm.trip.trip_id
crm.option.tenant_id -> crm.tenant.tenant_id
crm.option.(tenant_id,agency_supplier_id) -> crm.agency_supplier.(tenant_id,agency_supplier_id)
crm.option.(tenant_id,proposal_id,option_block_id) -> crm.option_block.(tenant_id,proposal_id,option_block_id)
crm.option.(tenant_id,proposal_id,trip_id) -> crm.proposal.(tenant_id,proposal_id,trip_id)
crm.option_block.tenant_id -> crm.tenant.tenant_id
crm.option_block.(tenant_id,option_block_id,default_option_id) -> crm.option.(tenant_id,option_block_id,option_id)
crm.option_block.(tenant_id,proposal_id,proposal_day_id) -> crm.proposal_day.(tenant_id,proposal_id,proposal_day_id)
crm.option_block.(tenant_id,proposal_id,trip_id) -> crm.proposal.(tenant_id,proposal_id,trip_id)
crm.option_rule.tenant_id -> crm.tenant.tenant_id
crm.option_rule.(tenant_id,proposal_id,option_id) -> crm.option.(tenant_id,proposal_id,option_id)
crm.option_rule.(tenant_id,proposal_id,target_option_id) -> crm.option.(tenant_id,proposal_id,option_id)
crm.option_rule.(tenant_id,proposal_id,trip_id) -> crm.proposal.(tenant_id,proposal_id,trip_id)
crm.otp_challenge.tenant_id -> crm.tenant.tenant_id
crm.otp_challenge.(tenant_id,access_id,trip_id,traveler_id) -> crm.traveler_access.(tenant_id,access_id,trip_id,traveler_id)
crm.otp_challenge.(tenant_id,message_id) -> crm.message.(tenant_id,message_id)
crm.owner_recovery_request.tenant_id -> crm.tenant.tenant_id
crm.owner_recovery_request.(tenant_id,candidate_member_id) -> crm.member.(tenant_id,member_id)
crm.payment.tenant_id -> crm.tenant.tenant_id
crm.payment.(tenant_id,schedule_id,trip_id) -> crm.payment_schedule.(tenant_id,schedule_id,trip_id)
crm.payment_schedule.tenant_id -> crm.tenant.tenant_id
crm.payment_schedule.(tenant_id,proposal_id,trip_id) -> crm.proposal.(tenant_id,proposal_id,trip_id)
crm.placeholder_map.tenant_id -> crm.tenant.tenant_id
crm.placeholder_map.(tenant_id,llm_call_id) -> crm.llm_call.(tenant_id,llm_call_id)
crm.prep_pack_selection.tenant_id -> crm.tenant.tenant_id
crm.prep_pack_selection.(tenant_id,proposal_id,trip_id) -> crm.proposal.(tenant_id,proposal_id,trip_id)
crm.profile_history.tenant_id -> crm.tenant.tenant_id
crm.profile_history.(tenant_id,traveler_token) -> crm.traveler_profile.(tenant_id,traveler_token)
crm.proposal.tenant_id -> crm.tenant.tenant_id
crm.proposal.(tenant_id,accepted_terms_doc_id) -> crm.agreement_doc.(tenant_id,doc_id)
crm.proposal.(tenant_id,based_on_proposal_id) -> crm.proposal.(tenant_id,proposal_id)
crm.proposal.(tenant_id,link_id) -> crm.client_link.(tenant_id,link_id)
crm.proposal.(tenant_id,terms_doc_id) -> crm.agreement_doc.(tenant_id,doc_id)
crm.proposal.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.proposal_day.tenant_id -> crm.tenant.tenant_id
crm.proposal_day.(tenant_id,proposal_id,trip_id) -> crm.proposal.(tenant_id,proposal_id,trip_id)
crm.saved_reply.tenant_id -> crm.tenant.tenant_id
crm.saved_reply.(tenant_id,member_id) -> crm.member.(tenant_id,member_id)
crm.selection.tenant_id -> crm.tenant.tenant_id
crm.selection.(tenant_id,option_block_id,option_id) -> crm.option.(tenant_id,option_block_id,option_id)
crm.selection.(tenant_id,proposal_id,option_block_id) -> crm.option_block.(tenant_id,proposal_id,option_block_id)
crm.selection.(tenant_id,proposal_id,trip_id) -> crm.proposal.(tenant_id,proposal_id,trip_id)
crm.signature_request.tenant_id -> crm.tenant.tenant_id
crm.signature_request.(tenant_id,access_id,trip_id,traveler_id) -> crm.traveler_access.(tenant_id,access_id,trip_id,traveler_id)
crm.signature_request.(tenant_id,doc_id) -> crm.agreement_doc.(tenant_id,doc_id)
crm.signature_request.(tenant_id,otp_id) -> crm.otp_challenge.(tenant_id,otp_id)
crm.task.assignee_member_id -> crm.member.member_id
crm.task.tenant_id -> crm.tenant.tenant_id
crm.task.trip_id -> crm.trip.trip_id
crm.tenant_entitlement.tenant_id -> crm.tenant.tenant_id
crm.tenant_key.tenant_id -> crm.tenant.tenant_id
crm.tenant_settings.tenant_id -> crm.tenant.tenant_id
crm.traveler.owner_member_id -> crm.member.member_id
crm.traveler.referrer_traveler_id -> crm.traveler.traveler_id
crm.traveler.tenant_id -> crm.tenant.tenant_id
crm.traveler_access.tenant_id -> crm.tenant.tenant_id
crm.traveler_access.(tenant_id,link_id) -> crm.client_link.(tenant_id,link_id)
crm.traveler_access.(tenant_id,traveler_id) -> crm.traveler.(tenant_id,traveler_id)
crm.traveler_access.(tenant_id,trip_id) -> crm.trip.(tenant_id,trip_id)
crm.traveler_access.(trip_id,traveler_id) -> crm.trip_traveler.(trip_id,traveler_id)
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
crm.trip_stage_history.(tenant_id,undo_of) -> crm.trip_stage_history.(tenant_id,history_id)
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
gold_aa_internal.aa_content_version.content_id -> gold_aa_internal.aa_content_item.content_id
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
shared.destinations.country_iso2 -> shared.countries.iso2
shared.destinations.duplicate_of -> shared.destinations.id
shared.eval_golden_item.set_id -> shared.eval_golden_set.set_id
shared.eval_item_result.item_id -> shared.eval_golden_item.item_id
shared.eval_item_result.run_id -> shared.prompt_eval_runs.id
shared.eval_item_result.scored_result_id -> shared.eval_item_result.result_id
shared.jev_tenant_allowlist.tenant_id -> shared.tenants.tenant_id
shared.job.parent_job_id -> shared.job.id
shared.llm_call_log.tenant_id -> shared.tenants.tenant_id
shared.llm_model_deployment.connection_key -> shared.llm_provider_connection.connection_key
shared.llm_model_deployment.model_key -> shared.llm_model_catalog.model_key
shared.pipeline_runs.tenant_id -> shared.tenants.tenant_id
shared.place_photo.destination_id -> shared.destinations.id
shared.place_photo.tour_id -> silver_aa_internal.raw_tours.tour_id
shared.prompt_eval_runs.golden_set_id -> shared.eval_golden_set.set_id
shared.staff_app_grant.admin_user_id -> shared.admin_users.id
shared.supply_content_version.entity_id -> shared.supply_entity.id
shared.supply_entity.(id,published_version_id) -> shared.supply_content_version.(entity_id,id)
shared.supply_media.entity_id -> shared.supply_entity.id
shared.tenant_api_usage.admin_user_id -> shared.admin_users.id
shared.tenant_api_usage.tenant_id -> shared.tenants.tenant_id
shared.tenant_brand_rules.tenant_id -> shared.tenants.tenant_id
shared.tenant_export_config.tenant_id -> shared.tenants.tenant_id
shared.tenant_integrations.tenant_id -> shared.tenants.tenant_id
shared.tenant_members.tenant_id -> shared.tenants.tenant_id
shared.tenant_rewrite_usage.tenant_id -> shared.tenants.tenant_id
shared.tenant_seo_config.tenant_id -> shared.tenants.tenant_id
shared.tenants.plan_id -> shared.membership_plans.id
shared.writing_memory_release.eval_run_id -> shared.prompt_eval_runs.id
shared.writing_memory_release.previous_release_id -> shared.writing_memory_release.release_id
shared.writing_memory_release.r0_run_id -> shared.prompt_eval_runs.id
shared.writing_memory_release.reverify_run_id -> shared.prompt_eval_runs.id
shared.writing_memory_release.shadow_run_id -> shared.prompt_eval_runs.id
shared.writing_memory_shadow.release_id -> shared.writing_memory_release.release_id
shared.writing_memory_shadow.run_id -> shared.prompt_eval_runs.id
silver_aa_internal.generated_content.reviewed_by -> shared.admin_users.id
silver_aa_internal.generated_content.tenant_id -> shared.tenants.tenant_id
silver_aa_internal.generated_content.tour_id -> silver_aa_internal.raw_tours.tour_id
silver_aa_internal.quality_scores.generated_content_id -> silver_aa_internal.generated_content.id
silver_aa_internal.quality_scores.tenant_id -> shared.tenants.tenant_id
silver_aa_internal.quality_scores.tour_id -> silver_aa_internal.raw_tours.tour_id
silver_aa_internal.raw_sources.batch_id -> shared.pipeline_runs.batch_id
silver_aa_internal.raw_sources.tenant_id -> shared.tenants.tenant_id
silver_aa_internal.raw_tours.batch_id -> shared.pipeline_runs.batch_id
silver_aa_internal.raw_tours.country -> shared.countries.name
silver_aa_internal.raw_tours.country_iso2 -> shared.countries.iso2
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
tripplanner.job.parent_job_id -> tripplanner.job.id
tripplanner.sessions.account_id -> tripplanner.traveller_accounts.id
tripplanner.sessions.customer_id -> tripplanner.customers.id
tripplanner.trip_drafts.session_id -> tripplanner.sessions.id
tripplanner.trip_events.session_id -> tripplanner.sessions.id
```

## Table activity

`pg_stat_user_tables` counters since the last stats reset (never), as of the Verified line. Use them with the 14-day rule of the Dead Table Registry, not alone.

| table | ~rows | size | seq scans | idx scans | ins / upd / del | dead tuples | last autovacuum |
|---|---|---|---|---|---|---|---|
| `acp_contract.atom_embedding` | 10674 | 175.2 MB | 465 | 112200 | 8456 / 0 / 0 | 0 | 2026-10-24 20:45 |
| `acp_contract.atom_matches` | 15152 | 4.4 MB | 17 | 44809 | 9412 / 29537 / 0 | 351 | 2026-10-24 12:48 |
| `acp_contract.atom_ranking` | 97368 | 66.6 MB | 37841 | 12213 | 13508382 / 13419564 / 13443522 | 0 | 2026-10-27 18:20 |
| `acp_contract.atom_segment` | 11613 | 3.9 MB | 5914 | 16083175 | 21485 / 160547 / 12892 | 260 | 2026-10-27 09:31 |
| `acp_contract.atom_segment_alias` | 1012 | 352 kB | 19167 | 222173 | 2261 / 231871 / 1489 | 128 | 2026-10-25 07:52 |
| `acp_contract.atom_segment_member` | 17510 | 7.8 MB | 9636 | 1650327 | 55894 / 471 / 43204 | 1257 | 2026-10-27 05:42 |
| `acp_contract.atomize_day_fingerprint` | 16159 | 2.9 MB | 20 | 16388 | 13159 / 53 / 0 | 3 | 2026-10-25 06:38 |
| `acp_contract.hub` | 87 | 152 kB | 1966 | 12115 | 75 / 2327 / 774 | 53 | 2026-10-27 08:31 |
| `acp_contract.question_embedding` | 1006 | 8.4 MB | 108 | 129 | 99 / 0 / 0 | 0 |  |
| `acp_contract.route` | 11546 | 6.8 MB | 1477 | 8562636 | 11199 / 10249 / 0 | 298 | 2026-10-27 07:15 |
| `acp_contract.search_demand` | 5089 | 1.7 MB | 4136 | 1898 | 509 / 289 / 0 | 237 |  |
| `acp_contract.segment_research_log` | 1337 | 568 kB | 5427 | 14657 | 219 / 0 / 0 | 0 |  |
| `acp_contract.tour_atoms` | 54494 | 31.8 MB | 22022 | 17558573 | 43293 / 36142 / 0 | 4816 | 2026-10-25 06:54 |
| `acp_deliver.tenant_tour_pages` | 0 | 40 kB | 7041 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.acp_output_rules` |  | 48 kB | 45 | 0 | 0 / 0 / 0 | 0 |  |
| `acp_shared.acp_quota_ledger` |  | 56 kB | 9 | 15 | 6 / 0 / 1 | 1 |  |
| `acp_shared.angle_gate_option` | 57 | 296 kB | 2649 | 68443 | 69 / 72 / 0 | 20 | 2026-10-16 03:32 |
| `acp_shared.angle_gate_request` | 21 | 128 kB | 18750 | 18947 | 25 / 76 / 0 | 18 | 2026-10-16 08:36 |
| `acp_shared.atom_place_card` | 26154 | 3.8 MB | 19357 | 3299076 | 26577 / 31 / 0 | 4 | 2026-10-26 13:34 |
| `acp_shared.audit_log` | 3100 | 2.2 MB | 586 | 7408 | 3209 / 0 / 0 | 15 | 2026-10-26 13:26 |
| `acp_shared.content_piece` | 343 | 11.9 MB | 17323 | 89022 | 349 / 719 / 0 | 60 | 2026-10-25 12:12 |
| `acp_shared.content_piece_label` |  | 48 kB | 23 | 25622 | 1 / 0 / 0 | 0 |  |
| `acp_shared.debate_brand_fit_cache` | 357 | 504 kB | 928 | 3198 | 925 / 0 / 563 | 24 | 2026-10-25 07:05 |
| `acp_shared.facts` |  | 64 kB | 67 | 5677 | 2 / 4 / 2 | 6 |  |
| `acp_shared.place_card` | 4785 | 4.5 MB | 23983 | 4253850 | 4803 / 4145 / 18 | 498 | 2026-10-27 07:33 |
| `acp_shared.place_card_alias` | 18503 | 3.2 MB | 1419 | 83865 | 18877 / 20 / 0 | 2 | 2026-10-26 15:22 |
| `acp_shared.place_card_miss` | 1331 | 528 kB | 1107 | 20103 | 1369 / 0 / 1 | 0 | 2026-10-26 15:04 |
| `acp_shared.publish_log` |  | 96 kB | 65 | 11568 | 7 / 14 / 0 | 11 |  |
| `acp_shared.quarter_plan` | 6 | 88 kB | 1636 | 52 | 0 / 0 / 0 | 0 |  |
| `acp_shared.quarter_plan_version` | 0 | 112 kB | 1609 | 52 | 0 / 0 / 0 | 0 |  |
| `acp_shared.subject` | 435 | 624 kB | 14008 | 6600 | 1001 / 1187 / 566 | 0 | 2026-10-28 07:35 |
| `acp_shared.tenant_config` |  | 32 kB | 15 | 573 | 1 / 0 / 1 | 1 |  |
| `acp_shared.year_plan` |  | 40 kB | 19 | 1592 | 0 / 0 / 0 | 0 |  |
| `booking.audit_logs` | 167 | 280 kB | 131 | 222 | 222 / 0 / 0 | 29 |  |
| `booking.b2b_cancellations` |  | 80 kB | 11 | 4 | 2 / 0 / 0 | 0 |  |
| `booking.b2b_hold_lines` | 12 | 80 kB | 198 | 316 | 22 / 5 / 0 | 5 |  |
| `booking.b2b_holds` | 2 | 128 kB | 20020 | 452 | 22 / 23 / 0 | 22 |  |
| `booking.b2b_partners` |  | 64 kB | 17 | 6433 | 3 / 0 / 0 | 1 |  |
| `booking.b2b_quote_lines` |  | 80 kB | 6 | 53 | 40 / 0 / 0 | 0 |  |
| `booking.b2b_quotes` |  | 96 kB | 10 | 96 | 40 / 0 / 0 | 0 |  |
| `booking.cancellation_policies` |  | 48 kB | 9 | 17 | 1 / 0 / 0 | 0 |  |
| `booking.countries` |  | 32 kB | 265 | 323 | 21 / 0 / 0 | 0 |  |
| `booking.country_profiles` |  | 24 kB | 24 | 12 | 0 / 0 / 0 | 0 |  |
| `booking.customer_identities` |  | 24 kB | 9 | 1 | 0 / 0 / 0 | 0 |  |
| `booking.customer_otps` |  | 24 kB | 10 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.customer_sessions` |  | 32 kB | 11 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.customers` | 1 | 104 kB | 4490 | 4 | 17 / 0 / 0 | 4 |  |
| `booking.departure_incidents` |  | 32 kB | 9 | 28 | 0 / 0 / 0 | 0 |  |
| `booking.departures` |  | 64 kB | 16 | 164 | 5 / 0 / 0 | 0 |  |
| `booking.destination_profiles` |  | 16 kB | 53 | 3 | 0 / 0 / 0 | 0 |  |
| `booking.entity_media` |  | 64 kB | 44 | 474 | 2 / 2 / 0 | 2 |  |
| `booking.fx_rates` |  | 48 kB | 111 | 17 | 3 / 0 / 0 | 0 |  |
| `booking.hotel_room_types` |  | 48 kB | 52 | 1191 | 5 / 0 / 0 | 1 |  |
| `booking.hotels` |  | 136 kB | 201 | 287 | 5 / 11 / 0 | 12 |  |
| `booking.inbox_cursor` | 2 | 64 kB | 49205 | 15502 | 2 / 15402 / 0 | 0 | 2026-10-29 20:51 |
| `booking.inbox_events` | 5 | 144 kB | 18786 | 72 | 17 / 22 / 0 | 22 |  |
| `booking.invoice_items` |  | 88 kB | 11 | 67 | 4 / 0 / 0 | 2 |  |
| `booking.invoices` |  | 184 kB | 21 | 673 | 4 / 14 / 0 | 16 |  |
| `booking.job` | 6914 | 3.5 MB | 18493 | 1521010 | 15464 / 30989 / 8550 | 183 | 2026-10-29 19:21 |
| `booking.media_files` |  | 24 kB | 10 | 0 | 0 / 0 / 0 | 0 |  |
| `booking.notification_reads` |  | 24 kB | 10 | 12157 | 0 / 0 / 0 | 0 |  |
| `booking.notifications` | 22 | 112 kB | 1398 | 48 | 29 / 0 / 0 | 3 |  |
| `booking.ops_files` |  | 128 kB | 13 | 37 | 1 / 1 / 0 | 1 |  |
| `booking.ops_transitions` |  | 32 kB | 4 | 53 | 20 / 0 / 0 | 0 |  |
| `booking.outbox` | 1 | 112 kB | 31215 | 3127 | 20 / 17 / 0 | 20 |  |
| `booking.payment_schedule` |  | 88 kB | 15 | 140 | 6 / 0 / 0 | 3 |  |
| `booking.payments` |  | 200 kB | 20 | 514 | 8 / 8 / 0 | 13 |  |
| `booking.policy_approvals` | 6 | 80 kB | 221 | 53 | 8 / 0 / 0 | 0 |  |
| `booking.pricing_rules` |  | 48 kB | 104 | 84 | 4 / 0 / 0 | 0 |  |
| `booking.services` |  | 152 kB | 200 | 268 | 5 / 1 / 0 | 2 |  |
| `booking.settings` |  | 32 kB | 22 | 482 | 20 / 0 / 0 | 0 |  |
| `booking.staff_assignments` |  | 64 kB | 89 | 4270 | 1 / 0 / 0 | 0 |  |
| `booking.staff_users` | 8 | 64 kB | 3289 | 4674 | 15 / 54 / 0 | 19 |  |
| `booking.supplier_bill_items` |  | 64 kB | 9 | 7 | 2 / 0 / 0 | 2 |  |
| `booking.supplier_bills` |  | 208 kB | 23 | 37 | 1 / 3 / 0 | 4 |  |
| `booking.supplier_bookings` |  | 240 kB | 21 | 543 | 9 / 12 / 0 | 19 |  |
| `booking.supplier_contracts` |  | 64 kB | 11 | 828 | 3 / 7 / 0 | 7 |  |
| `booking.supplier_payouts` |  | 168 kB | 17 | 17 | 3 / 1 / 0 | 4 |  |
| `booking.supplier_rates` |  | 80 kB | 31 | 1130 | 5 / 0 / 0 | 0 |  |
| `booking.suppliers` |  | 144 kB | 330 | 362 | 7 / 1 / 0 | 4 |  |
| `booking.trip_case_checks` |  | 128 kB | 17 | 215 | 40 / 2 / 0 | 20 |  |
| `booking.trip_case_countries` |  | 40 kB | 10 | 1014 | 3 / 0 / 0 | 0 |  |
| `booking.trip_case_legs` | 8 | 64 kB | 1424 | 117 | 14 / 8 / 0 | 8 |  |
| `booking.trip_case_status_history` | 1 | 64 kB | 221 | 0 | 51 / 0 / 0 | 17 |  |
| `booking.trip_case_status_transitions` |  | 32 kB | 6 | 145 | 34 / 0 / 0 | 0 |  |
| `booking.trip_case_version_itinerary` | 25 | 96 kB | 711 | 31 | 27 / 4 / 0 | 6 |  |
| `booking.trip_case_versions` |  | 80 kB | 56 | 1937 | 14 / 14 / 0 | 17 |  |
| `booking.trip_cases` | 10 | 176 kB | 4810 | 41 | 24 / 27 / 0 | 33 |  |
| `booking.trip_plan_components` |  | 48 kB | 26 | 85 | 2 / 0 / 0 | 0 |  |
| `booking.trip_plan_prices` |  | 32 kB | 10 | 142 | 0 / 0 / 0 | 0 |  |
| `booking.trip_plans` | 2 | 72 kB | 666 | 33739 | 2 / 2 / 0 | 2 |  |
| `booking.version_item_costs` | 4 | 64 kB | 83 | 19 | 14 / 0 / 1 | 3 |  |
| `crm.aa_catalog_state` | 1 | 64 kB | 1014 | 1 | 1 / 856 / 0 | 12 | 2026-10-29 19:00 |
| `crm.aa_catalog_tour` | 892 | 6.4 MB | 952 | 35639 | 892 / 36730 / 0 | 0 | 2026-10-29 20:00 |
| `crm.aa_content` | 23 | 248 kB | 250 | 328 | 23 / 1357 / 0 | 44 | 2026-10-29 17:00 |
| `crm.aa_request` | 19 | 112 kB | 23782 | 16486 | 24 / 42 / 0 | 25 |  |
| `crm.agency_supplier` |  | 80 kB | 10 | 1109 | 17 / 12 / 0 | 12 |  |
| `crm.agreement_doc` | 18 | 80 kB | 402 | 477 | 22 / 42 / 0 | 42 |  |
| `crm.audit_event` |  | 0 B | 0 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.audit_event_legacy` | 2806 | 1.7 MB | 31 | 928 | 2827 / 0 / 0 | 0 | 2026-10-29 17:09 |
| `crm.audit_event_p202611` |  | 32 kB | 15 | 12 | 0 / 0 / 0 | 0 |  |
| `crm.audit_event_p202612` |  | 32 kB | 15 | 12 | 0 / 0 / 0 | 0 |  |
| `crm.audit_event_p202701` |  | 32 kB | 15 | 12 | 0 / 0 / 0 | 0 |  |
| `crm.audit_export_manifest` | 426 | 376 kB | 24 | 938 | 466 / 0 / 0 | 0 |  |
| `crm.audit_export_tenant` | 4 | 56 kB | 10828 | 539 | 4 / 487 / 0 | 20 | 2026-10-29 16:16 |
| `crm.booking_feed_state` | 1 | 48 kB | 28118 | 815 | 1 / 6144 / 0 | 37 |  |
| `crm.booking_line` |  | 136 kB | 16 | 1271 | 7 / 19 / 0 | 13 |  |
| `crm.booking_line_money` |  | 80 kB | 10 | 886 | 18 / 0 / 0 | 0 |  |
| `crm.channel_account` |  | 80 kB | 10 | 775 | 1 / 10 / 0 | 10 |  |
| `crm.client_link` | 53 | 168 kB | 777 | 306 | 54 / 162 / 0 | 1 | 2026-10-29 17:10 |
| `crm.consent` | 106 | 96 kB | 67 | 20 | 116 / 0 / 0 | 0 |  |
| `crm.conversation` |  | 96 kB | 11 | 451 | 8 / 16 / 0 | 16 |  |
| `crm.dispatch_attempt` |  | 64 kB | 9 | 8 | 4 / 4 / 0 | 4 |  |
| `crm.dispatch_queue` | 52 | 144 kB | 207 | 63 | 59 / 63 / 0 | 10 | 2026-10-26 13:02 |
| `crm.document` |  | 72 kB | 37 | 366 | 1 / 0 / 0 | 0 |  |
| `crm.erasure_request` |  | 24 kB | 14 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.form_definition` |  | 48 kB | 8 | 107 | 3 / 0 / 0 | 0 |  |
| `crm.form_submission` | 90 | 248 kB | 1523 | 3255 | 91 / 58 / 0 | 1 | 2026-10-29 17:10 |
| `crm.fx_rate_override` |  | 24 kB | 8 | 12 | 0 / 0 / 0 | 0 |  |
| `crm.fx_rate_platform` | 126 | 80 kB | 8 | 126 | 126 / 0 / 0 | 0 |  |
| `crm.inbox_events` |  | 48 kB | 8 | 2 | 1 / 0 / 0 | 0 |  |
| `crm.ingest_address` |  | 64 kB | 9 | 54 | 1 / 0 / 0 | 0 |  |
| `crm.intake_form` |  | 48 kB | 123 | 452 | 3 / 0 / 0 | 0 |  |
| `crm.integration_credential` |  | 80 kB | 11 | 114 | 2 / 11 / 1 | 12 |  |
| `crm.job` | 7988 | 5.9 MB | 9597 | 930982 | 33033 / 66060 / 25000 | 144 | 2026-10-29 20:40 |
| `crm.legal_hold` |  | 24 kB | 8 | 1244 | 0 / 0 / 0 | 0 |  |
| `crm.lifecycle_run` |  | 48 kB | 8 | 0 | 21 / 0 / 0 | 0 |  |
| `crm.llm_call` |  | 32 kB | 10 | 47 | 0 / 0 / 0 | 0 |  |
| `crm.llm_usage_daily` |  | 16 kB | 7 | 2 | 0 / 0 / 0 | 0 |  |
| `crm.mail_import` |  | 32 kB | 10 | 37 | 4 / 18 / 0 | 18 |  |
| `crm.meeting_slot` |  | 96 kB | 11 | 92 | 11 / 8 / 0 | 8 |  |
| `crm.member` | 6 | 80 kB | 71310 | 288 | 13 / 1 / 0 | 1 |  |
| `crm.member_invitation` |  | 80 kB | 10 | 296 | 3 / 4 / 0 | 5 |  |
| `crm.membership_feed_state` | 1 | 64 kB | 33670 | 1 | 1 / 16323 / 0 | 3 | 2026-10-29 20:49 |
| `crm.membership_inbox` |  | 48 kB | 8 | 31 | 6 / 0 / 0 | 0 |  |
| `crm.message` |  | 224 kB | 13 | 1621 | 18 / 12 / 2 | 14 |  |
| `crm.message_template` |  | 80 kB | 10 | 16 | 4 / 0 / 0 | 0 |  |
| `crm.metric_event` |  | 96 kB | 11 | 165 | 15 / 0 / 0 | 0 |  |
| `crm.note` |  | 48 kB | 29 | 357 | 19 / 0 / 0 | 0 |  |
| `crm.option` |  | 160 kB | 13 | 449 | 43 / 3 / 0 | 1 |  |
| `crm.option_block` | 42 | 128 kB | 195 | 256 | 68 / 26 / 0 | 0 |  |
| `crm.option_rule` |  | 96 kB | 11 | 368 | 5 / 0 / 0 | 5 |  |
| `crm.otp_challenge` |  | 104 kB | 12 | 807 | 7 / 7 / 7 | 14 |  |
| `crm.owner_recovery_request` |  | 24 kB | 8 | 739 | 0 / 0 / 0 | 0 |  |
| `crm.payment` |  | 80 kB | 10 | 316 | 8 / 0 / 0 | 0 |  |
| `crm.payment_schedule` |  | 96 kB | 11 | 1132 | 20 / 8 / 0 | 8 |  |
| `crm.placeholder_map` |  | 32 kB | 143 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.prep_pack_selection` |  | 48 kB | 11 | 20 | 0 / 0 / 0 | 0 |  |
| `crm.profile_history` |  | 24 kB | 8 | 0 | 0 / 0 / 0 | 0 |  |
| `crm.proposal` | 20 | 232 kB | 2029 | 108 | 20 / 143 / 0 | 1 | 2026-10-29 17:13 |
| `crm.proposal_day` | 54 | 136 kB | 193 | 260 | 86 / 0 / 0 | 0 |  |
| `crm.saved_reply` |  | 24 kB | 8 | 313 | 0 / 0 / 0 | 0 |  |
| `crm.selection` |  | 96 kB | 11 | 172 | 2 / 0 / 0 | 0 |  |
| `crm.signature_request` |  | 88 kB | 11 | 360 | 8 / 0 / 0 | 0 |  |
| `crm.status_transition` | 121 | 64 kB | 560 | 161 | 136 / 0 / 0 | 0 |  |
| `crm.studio_invitation` |  | 96 kB | 11 | 13 | 2 / 4 / 0 | 4 |  |
| `crm.task` | 91 | 144 kB | 4202 | 492 | 115 / 90 / 0 | 30 | 2026-10-26 03:58 |
| `crm.tenant` |  | 32 kB | 27 | 67387 | 4 / 0 / 0 | 0 |  |
| `crm.tenant_entitlement` |  | 16 kB | 7 | 24 | 0 / 0 / 0 | 0 |  |
| `crm.tenant_key` |  | 64 kB | 9 | 135 | 4 / 0 / 0 | 0 |  |
| `crm.tenant_settings` |  | 32 kB | 15 | 1237 | 1 / 18 / 0 | 5 |  |
| `crm.traveler` | 51 | 200 kB | 7227 | 462 | 58 / 0 / 0 | 0 |  |
| `crm.traveler_access` |  | 112 kB | 12 | 441 | 8 / 14 / 0 | 14 |  |
| `crm.traveler_health` |  | 24 kB | 8 | 15 | 0 / 0 / 0 | 0 |  |
| `crm.traveler_profile` | 56 | 80 kB | 1252 | 2 | 58 / 179 / 0 | 4 |  |
| `crm.traveler_relation` |  | 40 kB | 31 | 15 | 0 / 0 / 0 | 0 |  |
| `crm.trip` | 57 | 176 kB | 7171 | 1694 | 58 / 478 / 0 | 38 | 2026-10-26 10:23 |
| `crm.trip_commitment` |  | 64 kB | 9 | 45 | 14 / 6 / 0 | 6 |  |
| `crm.trip_party` | 51 | 96 kB | 28 | 0 | 58 / 0 / 0 | 0 |  |
| `crm.trip_stage_history` | 161 | 168 kB | 550 | 408 | 193 / 0 / 0 | 0 |  |
| `crm.trip_traveler` | 45 | 112 kB | 3991 | 6824 | 58 / 8 / 0 | 2 |  |
| `geo.component_redirect` |  | 64 kB | 181 | 18615 | 27 / 0 / 1 | 1 |  |
| `geo.geocode_call` | 49 | 80 kB | 276 | 935 | 90 / 3 / 0 | 0 |  |
| `geo.graph_build` | 3 | 104 kB | 4594772 | 2391094 | 74 / 147 / 71 | 12 | 2026-10-28 03:11 |
| `geo.graph_edge` | 8469 | 3.4 MB | 93 | 7 | 113183 / 0 / 104714 | 0 | 2026-10-29 01:00 |
| `geo.graph_node` | 5415 | 3.3 MB | 123 | 60 | 71622 / 0 / 66207 | 0 | 2026-10-29 01:00 |
| `geo.place_dedupe_country` |  | 16 kB | 62 | 0 | 0 / 0 / 0 | 0 |  |
| `geo.place_merge` |  | 40 kB | 13 | 600 | 0 / 0 / 0 | 0 |  |
| `geo.place_name` | 9545 | 2.9 MB | 971 | 53639 | 9577 / 14300 / 0 | 685 | 2026-10-28 01:29 |
| `geo.place_outlier` |  | 16 kB | 131 | 2030 | 0 / 0 / 0 | 0 |  |
| `geo.place_pair_verdict` |  | 24 kB | 597 | 0 | 0 / 0 / 0 | 0 |  |
| `geo.place_shape` | 284 | 1.4 MB | 3827 | 8617 | 288 / 381 / 0 | 27 | 2026-10-28 03:05 |
| `geo.tour_build` | 892 | 1.1 MB | 623 | 12553 | 892 / 1964 / 0 | 1 | 2026-10-28 07:23 |
| `geo.tour_day` | 6996 | 2.8 MB | 431 | 46807 | 15676 / 2294 / 8680 | 677 | 2026-10-27 17:38 |
| `geo.tour_junction` | 228082 | 60.1 MB | 1259 | 1 | 2149566 / 0 / 1921484 | 0 | 2026-10-29 01:00 |
| `geo.tour_leg` | 96906 | 68.4 MB | 2763 | 4 | 1273289 / 0 / 1176383 | 0 | 2026-10-29 01:00 |
| `geo.tour_place` | 13500 | 216.1 MB | 6124 | 4596704 | 30349 / 8079 / 16839 | 836 | 2026-10-28 00:30 |
| `geo.tour_segment` | 1230 | 1.8 MB | 205207 | 2755460 | 13208 / 0 / 11978 | 0 | 2026-10-29 01:00 |
| `geo.tour_stop` | 19521 | 8 MB | 5731 | 4953 | 259020 / 0 / 239499 | 0 | 2026-10-29 01:00 |
| `gold_aa_internal.aa_content_item` | 28 | 48 kB | 224 | 563 | 29 / 29 / 0 | 30 |  |
| `gold_aa_internal.aa_content_version` | 28 | 144 kB | 180 | 2089 | 32 / 29 / 0 | 32 |  |
| `gold_aa_internal.content_exports` |  | 24 kB | 3264 | 0 | 0 / 0 / 0 | 0 |  |
| `gold_aa_internal.published_tours` | 892 | 6.8 MB | 69818 | 20518551 | 497 / 2259 / 0 | 131 | 2026-10-25 07:36 |
| `gold_aa_internal.tenant_tour_versions` | 53 | 680 kB | 42473 | 8259 | 63 / 133 / 0 | 36 | 2026-10-15 14:24 |
| `gold_aa_internal.tour_lifecycle_event` |  | 80 kB | 18637 | 738824 | 12 / 0 / 0 | 2 |  |
| `gold_aa_internal.webhook_deliveries` |  | 24 kB | 3269 | 0 | 0 / 0 / 0 | 0 |  |
| `public.checkpoint_migrations` |  | 24 kB | 8 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.admin_users` | 11 | 80 kB | 23583 | 75345 | 9 / 894 / 4 | 17 |  |
| `shared.alert_recipient` | 2 | 64 kB | 8838 | 154 | 2 / 2957 / 0 | 6 |  |
| `shared.cost_explorer_app_snapshot` | 10118 | 2.4 MB | 134 | 38 | 10118 / 0 / 0 | 0 | 2026-10-27 03:58 |
| `shared.cost_explorer_snapshot` | 2766 | 2 MB | 580 | 16 | 9536 / 0 / 8951 | 0 | 2026-10-27 21:00 |
| `shared.countries` | 249 | 128 kB | 7891 | 15619 | 249 / 7 / 0 | 6 |  |
| `shared.decision_cache_hits_daily` | 290 | 128 kB | 668 | 24936 | 293 / 24641 / 0 | 45 | 2026-10-27 17:44 |
| `shared.decision_log` | 427684 | 443.7 MB | 618 | 1147080 | 425301 / 6 / 695728 | 3 | 2026-10-25 08:41 |
| `shared.decision_question` | 5 | 72 kB | 15787 | 670 | 1 / 20 / 0 | 3 |  |
| `shared.destinations` | 8200 | 6.5 MB | 68461 | 28731407 | 7017 / 7043 / 0 | 773 | 2026-10-29 00:46 |
| `shared.dfs_balance_snapshot` |  | 352 kB | 5 | 1720 | 26 / 0 / 0 | 0 |  |
| `shared.dfs_call_log` | 2626 | 1 MB | 2070 | 8174 | 707 / 0 / 0 | 0 |  |
| `shared.eval_golden_item` | 200 | 2.6 MB | 946 | 872 | 203 / 0 / 0 | 3 |  |
| `shared.eval_golden_set` |  | 112 kB | 18 | 818 | 5 / 1 / 0 | 4 |  |
| `shared.eval_item_result` | 326 | 472 kB | 227 | 645 | 382 / 0 / 0 | 1 |  |
| `shared.jev_credit_topup` |  | 48 kB | 540 | 3 | 2 / 0 / 0 | 0 |  |
| `shared.jev_tenant_allowlist` |  | 32 kB | 13258 | 4732 | 4 / 0 / 7 | 7 |  |
| `shared.job` | 7790 | 22.8 MB | 19429 | 2216280 | 7176 / 67450 / 0 | 113 | 2026-10-29 00:53 |
| `shared.job_worker` | 181 | 424 kB | 114407 | 487143 | 499 / 132307 / 379 | 68 | 2026-10-29 20:34 |
| `shared.kpi_daily` |  | 24 kB | 2 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.llm_call_daily` |  | 48 kB | 1724 | 618 | 5 / 0 / 0 | 0 |  |
| `shared.llm_call_log` | 383796 | 202.8 MB | 10610 | 26395552 | 270231 / 0 / 200 | 200 | 2026-10-26 07:05 |
| `shared.llm_model_catalog` |  | 64 kB | 2406 | 198 | 3 / 12 / 0 | 3 |  |
| `shared.llm_model_deployment` |  | 48 kB | 3 | 21 | 15 / 0 / 0 | 0 |  |
| `shared.llm_provider_connection` |  | 32 kB | 3 | 20 | 5 / 0 / 0 | 0 |  |
| `shared.llm_role_config` | 36 | 32 kB | 6890 | 11673 | 20 / 26 / 6 | 18 |  |
| `shared.llm_shadow_log` | 5554 | 11.9 MB | 10 | 16 | 3029 / 0 / 0 | 0 | 2026-10-08 07:37 |
| `shared.membership_plans` |  | 48 kB | 5866 | 6698 | 0 / 0 / 0 | 0 |  |
| `shared.notifications` | 39 | 104 kB | 28479 | 392 | 30 / 29 / 0 | 32 |  |
| `shared.pipeline_jobs` | 523 | 480 kB | 28 | 22 | 0 / 0 / 0 | 0 |  |
| `shared.pipeline_lessons` |  | 24 kB | 9 | 1960 | 0 / 0 / 0 | 0 |  |
| `shared.pipeline_runs` | 46 | 208 kB | 9515 | 7781 | 0 / 1679 / 0 | 20 |  |
| `shared.place_photo` | 3232 | 4.2 MB | 23893 | 17747471 | 0 / 31007 / 0 | 326 | 2026-10-29 07:44 |
| `shared.prompt_eval_runs` |  | 136 kB | 43 | 1080 | 42 / 13 / 0 | 17 |  |
| `shared.report_run` |  | 40 kB | 4 | 0 | 0 / 0 / 0 | 0 |  |
| `shared.rerun_wave` | 25 | 216 kB | 441 | 1112 | 25 / 130 / 0 | 10 | 2026-10-25 08:19 |
| `shared.schema_versions` | 301 | 120 kB | 4733 | 1191 | 182 / 0 / 0 | 7 |  |
| `shared.spend_budget` |  | 32 kB | 1432 | 2222 | 8 / 0 / 0 | 0 |  |
| `shared.staff_app_grant` |  | 32 kB | 179 | 86 | 2 / 0 / 1 | 1 |  |
| `shared.supply_content_version` |  | 80 kB | 68 | 527 | 8 / 7 / 0 | 7 |  |
| `shared.supply_entity` |  | 64 kB | 490 | 181 | 4 / 16 / 0 | 16 |  |
| `shared.supply_event_inbox` |  | 80 kB | 66 | 76 | 15 / 0 / 0 | 0 |  |
| `shared.supply_feed_cursor` | 1 | 64 kB | 3212 | 1679 | 1 / 1580 / 0 | 49 | 2026-10-29 17:00 |
| `shared.supply_media` |  | 48 kB | 65 | 185 | 2 / 8 / 0 | 8 |  |
| `shared.tenant_api_usage` | 157306 | 39 MB | 9 | 39560 | 117567 / 0 / 200 | 206 | 2026-10-26 12:11 |
| `shared.tenant_api_usage_monthly` |  | 48 kB | 17 | 198 | 3 / 0 / 0 | 0 |  |
| `shared.tenant_brand_rules` | 27 | 232 kB | 28587 | 5682 | 25 / 56 / 1 | 13 | 2026-10-22 09:12 |
| `shared.tenant_export_config` |  | 48 kB | 18 | 9 | 0 / 0 / 0 | 0 |  |
| `shared.tenant_integrations` |  | 64 kB | 36 | 4509 | 14 / 11 / 14 | 8 |  |
| `shared.tenant_members` |  | 64 kB | 22 | 154 | 6 / 7 / 0 | 10 |  |
| `shared.tenant_membership_event` |  | 64 kB | 25 | 16329 | 17 / 0 / 0 | 10 |  |
| `shared.tenant_rewrite_usage` | 6 | 64 kB | 697 | 159 | 4 / 58 / 0 | 11 | 2026-10-20 03:09 |
| `shared.tenant_seo_config` |  | 48 kB | 17 | 2821 | 4 / 11 / 0 | 11 |  |
| `shared.tenants` | 4 | 80 kB | 251621 | 3314 | 7 / 34 / 1 | 16 |  |
| `shared.unmapped_market_requests` |  | 32 kB | 10 | 412 | 0 / 0 / 0 | 0 |  |
| `shared.writing_memory_release` | 9 | 160 kB | 824 | 128 | 22 / 91 / 1 | 39 | 2026-10-27 00:28 |
| `shared.writing_memory_shadow` |  | 80 kB | 10 | 1 | 3 / 0 / 0 | 0 |  |
| `shared.writing_memory_writer` |  | 32 kB | 21 | 73 | 4 / 8 / 0 | 8 |  |
| `shared.writing_rule` |  | 128 kB | 64 | 110 | 26 / 16 / 0 | 40 |  |
| `shared.writing_signal` | 580 | 2.1 MB | 1684 | 1667 | 600 / 586 / 0 | 25 | 2026-10-25 12:12 |
| `silver_aa_internal.generated_content` | 2296 | 18.8 MB | 5424 | 786989 | 1806 / 851 / 0 | 91 | 2026-10-25 04:35 |
| `silver_aa_internal.quality_scores` | 2272 | 2.4 MB | 667823 | 2691 | 1811 / 1773 / 7 | 207 | 2026-10-24 12:26 |
| `silver_aa_internal.raw_sources` | 34 | 96 kB | 1237 | 2344 | 0 / 0 / 0 | 0 |  |
| `silver_aa_internal.raw_tours` | 987 | 6.5 MB | 69066 | 33323218 | 0 / 2645 / 0 | 70 | 2026-10-25 07:44 |
| `silver_aa_internal.review_queue` | 229 | 176 kB | 70443 | 37908 | 178 / 109 / 0 | 66 | 2026-10-08 03:05 |
| `silver_aa_internal.seo_context` | 918 | 1.3 MB | 3649 | 716680 | 506 / 75 / 0 | 86 |  |
| `silver_aa_internal.upload_staging` |  | 104 kB | 23 | 0 | 0 / 0 / 0 | 0 |  |
| `tripplanner.component_id_map` | 750 | 136 kB | 183 | 1345 | 756 / 0 / 0 | 0 |  |
| `tripplanner.customers` |  | 64 kB | 28 | 25 | 7 / 7 / 1 | 8 |  |
| `tripplanner.job` |  | 120 kB | 17 | 36 | 5 / 10 / 0 | 10 |  |
| `tripplanner.llm_spend_daily` | 8 | 64 kB | 935 | 1638 | 8 / 1502 / 0 | 50 | 2026-10-16 09:06 |
| `tripplanner.narration_cache` |  | 48 kB | 15 | 12 | 1 / 1 / 0 | 1 |  |
| `tripplanner.outbox` | 7 | 112 kB | 1221 | 29676 | 8 / 0 / 3 | 1 |  |
| `tripplanner.sessions` | 102 | 96 kB | 966 | 604 | 81 / 43 / 3 | 38 |  |
| `tripplanner.traveller_accounts` |  | 48 kB | 12 | 23 | 3 / 1 / 0 | 1 |  |
| `tripplanner.trip_drafts` | 98 | 144 kB | 479 | 820 | 79 / 284 / 1 | 21 |  |
| `tripplanner.trip_events` | 416 | 192 kB | 964 | 805 | 363 / 0 / 6 | 5 |  |

## Unused indexes

Non-PK, non-unique indexes with 0 scans since the stats reset. A drop candidate only after 30 days at 0 (standards C5.2d), through expand/contract.

- `acp_shared.idx_output_rules_active` on `acp_output_rules` (16 kB)
- `acp_shared.idx_angle_gate_request_status` on `angle_gate_request` (16 kB)
- `acp_shared.idx_angle_gate_request_subject` on `angle_gate_request` (16 kB)
- `acp_shared.idx_angle_gate_request_tenant` on `angle_gate_request` (16 kB)
- `acp_shared.idx_content_piece_embedding` on `content_piece` (2.6 MB)
- `acp_shared.idx_content_piece_label_label` on `content_piece_label` (16 kB)
- `acp_shared.idx_quarter_plan_year_plan_id` on `quarter_plan` (16 kB)
- `acp_shared.idx_quarter_plan_version_approval_status` on `quarter_plan_version` (16 kB)
- `booking.b2b_cancellations_partner_idx` on `b2b_cancellations` (16 kB)
- `booking.b2b_hold_lines_on_request_idx` on `b2b_hold_lines` (16 kB)
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
- `booking.hotels_updated_idx` on `hotels` (16 kB)
- `booking.inbox_events_pending_idx` on `inbox_events` (16 kB)
- `booking.inbox_events_redact_due_idx` on `inbox_events` (16 kB)
- `booking.inbox_events_status_idx` on `inbox_events` (16 kB)
- `booking.invoice_items_created_by_idx` on `invoice_items` (16 kB)
- `booking.invoice_items_updated_by_idx` on `invoice_items` (8 kB)
- `booking.invoices_cancelled_by_idx` on `invoices` (8 kB)
- `booking.invoices_created_by_idx` on `invoices` (16 kB)
- `booking.invoices_customer_idx` on `invoices` (16 kB)
- `booking.invoices_sent_by_idx` on `invoices` (16 kB)
- `booking.invoices_updated_by_idx` on `invoices` (16 kB)
- `booking.invoices_version_idx` on `invoices` (16 kB)
- `booking.notifications_staff_feed_idx` on `notifications` (16 kB)
- `booking.notifications_unread_idx` on `notifications` (16 kB)
- `booking.ops_files_entity_idx` on `ops_files` (16 kB)
- `booking.ops_files_removed_by_idx` on `ops_files` (16 kB)
- `booking.ops_files_removed_idx` on `ops_files` (16 kB)
- `booking.ops_files_trip_case_idx` on `ops_files` (16 kB)
- `booking.ops_files_uploaded_by_idx` on `ops_files` (16 kB)
- `booking.outbox_supply_feed_idx` on `outbox` (16 kB)
- `booking.payment_schedule_created_by_idx` on `payment_schedule` (16 kB)
- `booking.payment_schedule_due_idx` on `payment_schedule` (16 kB)
- `booking.payment_schedule_updated_by_idx` on `payment_schedule` (8 kB)
- `booking.payments_awaiting_idx` on `payments` (16 kB)
- `booking.payments_evidence_idx` on `payments` (8 kB)
- `booking.payments_recorded_by_idx` on `payments` (16 kB)
- `booking.payments_reference_idx` on `payments` (16 kB)
- `booking.payments_updated_by_idx` on `payments` (16 kB)
- `booking.payments_verified_by_idx` on `payments` (16 kB)
- `booking.payments_voided_by_idx` on `payments` (16 kB)
- `booking.services_country_idx` on `services` (16 kB)
- `booking.services_type_idx` on `services` (16 kB)
- `booking.services_updated_idx` on `services` (16 kB)
- `booking.staff_users_active_idx` on `staff_users` (16 kB)
- `booking.supplier_bill_items_created_by_idx` on `supplier_bill_items` (16 kB)
- `booking.supplier_bills_approved_by_idx` on `supplier_bills` (16 kB)
- `booking.supplier_bills_cancelled_by_idx` on `supplier_bills` (8 kB)
- `booking.supplier_bills_created_by_idx` on `supplier_bills` (16 kB)
- `booking.supplier_bills_document_idx` on `supplier_bills` (8 kB)
- `booking.supplier_bills_facts_edited_by_idx` on `supplier_bills` (16 kB)
- `booking.supplier_bills_supplier_idx` on `supplier_bills` (16 kB)
- `booking.supplier_bills_trip_case_idx` on `supplier_bills` (16 kB)
- `booking.supplier_bills_updated_by_idx` on `supplier_bills` (16 kB)
- `booking.supplier_bookings_b2b_line_idx` on `supplier_bookings` (8 kB)
- `booking.supplier_bookings_confirmed_by_idx` on `supplier_bookings` (16 kB)
- `booking.supplier_bookings_created_by_idx` on `supplier_bookings` (16 kB)
- `booking.supplier_bookings_requested_by_idx` on `supplier_bookings` (16 kB)
- `booking.supplier_bookings_room_type_idx` on `supplier_bookings` (16 kB)
- `booking.supplier_bookings_service_idx` on `supplier_bookings` (16 kB)
- `booking.supplier_bookings_supplier_idx` on `supplier_bookings` (16 kB)
- `booking.supplier_bookings_updated_by_idx` on `supplier_bookings` (16 kB)
- `booking.supplier_bookings_voucher_idx` on `supplier_bookings` (8 kB)
- `booking.supplier_payouts_evidence_idx` on `supplier_payouts` (8 kB)
- `booking.supplier_payouts_recorded_by_idx` on `supplier_payouts` (16 kB)
- `booking.supplier_payouts_reference_idx` on `supplier_payouts` (16 kB)
- `booking.supplier_payouts_updated_by_idx` on `supplier_payouts` (16 kB)
- `booking.supplier_payouts_voided_by_idx` on `supplier_payouts` (16 kB)
- `booking.suppliers_categories_idx` on `suppliers` (24 kB)
- `booking.suppliers_country_idx` on `suppliers` (16 kB)
- `booking.suppliers_updated_idx` on `suppliers` (16 kB)
- `booking.trip_case_checks_assignee_idx` on `trip_case_checks` (8 kB)
- `booking.trip_case_checks_created_by_idx` on `trip_case_checks` (8 kB)
- `booking.trip_case_checks_done_by_idx` on `trip_case_checks` (8 kB)
- `booking.trip_case_checks_updated_by_idx` on `trip_case_checks` (8 kB)
- `booking.trip_case_countries_country_idx` on `trip_case_countries` (16 kB)
- `booking.trip_case_legs_tour_key_idx` on `trip_case_legs` (16 kB)
- `booking.trip_case_status_history_case_idx` on `trip_case_status_history` (16 kB)
- `booking.trip_case_status_history_case_seq_idx` on `trip_case_status_history` (16 kB)
- `booking.trip_case_version_itinerary_room_type_idx` on `trip_case_version_itinerary` (16 kB)
- `booking.trip_case_version_itinerary_service_idx` on `trip_case_version_itinerary` (16 kB)
- `booking.trip_case_version_itinerary_source_tour_idx` on `trip_case_version_itinerary` (16 kB)
- `booking.trip_cases_customer_idx` on `trip_cases` (16 kB)
- `booking.trip_cases_party_idx` on `trip_cases` (16 kB)
- `booking.trip_cases_source_idx` on `trip_cases` (16 kB)
- `booking.trip_plans_supplier_idx` on `trip_plans` (8 kB)
- `booking.version_item_costs_rate_idx` on `version_item_costs` (16 kB)
- `crm.aa_request_trip_idx` on `aa_request` (16 kB)
- `crm.audit_event_object_idx` on `audit_event` (0 B)
- `crm.audit_event_tenant_at_idx` on `audit_event` (0 B)
- `crm.booking_line_booking_idx` on `booking_line` (8 kB)
- `crm.booking_line_hold_idx` on `booking_line` (16 kB)
- `crm.client_link_dispatch_idx` on `client_link` (16 kB)
- `crm.conversation_traveler_idx` on `conversation` (16 kB)
- `crm.dispatch_attempt_dispatch_idx` on `dispatch_attempt` (16 kB)
- `crm.dispatch_queue_due_idx` on `dispatch_queue` (16 kB)
- `crm.dispatch_queue_message_idx` on `dispatch_queue` (16 kB)
- `crm.form_submission_client_link_idx` on `form_submission` (16 kB)
- `crm.fx_rate_platform_pair_idx` on `fx_rate_platform` (16 kB)
- `crm.integration_credential_member_idx` on `integration_credential` (16 kB)
- `crm.lifecycle_run_tenant_idx` on `lifecycle_run` (16 kB)
- `crm.llm_call_tenant_at_idx` on `llm_call` (8 kB)
- `crm.meeting_slot_submission_idx` on `meeting_slot` (16 kB)
- `crm.meeting_slot_traveler_idx` on `meeting_slot` (16 kB)
- `crm.message_from_idx` on `message` (16 kB)
- `crm.metric_event_trip_idx` on `metric_event` (16 kB)
- `crm.option_block_idx` on `option` (16 kB)
- `crm.option_supplier_idx` on `option` (8 kB)
- `crm.option_block_day_idx` on `option_block` (16 kB)
- `crm.option_rule_target_idx` on `option_rule` (16 kB)
- `crm.option_rule_trip_idx` on `option_rule` (16 kB)
- `crm.otp_challenge_access_idx` on `otp_challenge` (16 kB)
- `crm.placeholder_map_expires_idx` on `placeholder_map` (8 kB)
- `crm.prep_pack_selection_trip_idx` on `prep_pack_selection` (8 kB)
- `crm.profile_history_token_idx` on `profile_history` (8 kB)
- `crm.proposal_based_on_idx` on `proposal` (16 kB)
- `crm.proposal_link_idx` on `proposal` (16 kB)
- `crm.proposal_nudge_idx` on `proposal` (16 kB)
- `crm.selection_option_idx` on `selection` (16 kB)
- `crm.signature_request_access_idx` on `signature_request` (16 kB)
- `crm.studio_invitation_tenant_idx` on `studio_invitation` (16 kB)
- `crm.task_open_idx` on `task` (16 kB)
- `crm.traveler_archived_idx` on `traveler` (8 kB)
- `crm.traveler_name_bidx_idx` on `traveler` (16 kB)
- `crm.traveler_name_token_bidx_idx` on `traveler` (24 kB)
- `crm.traveler_owner_member_idx` on `traveler` (8 kB)
- `crm.traveler_phone_bidx_idx` on `traveler` (8 kB)
- `crm.traveler_referrer_idx` on `traveler` (8 kB)
- `crm.traveler_access_link_idx` on `traveler_access` (16 kB)
- `crm.traveler_relation_to_idx` on `traveler_relation` (8 kB)
- `crm.trip_date_rule_idx` on `trip` (16 kB)
- `crm.trip_owner_idx` on `trip` (16 kB)
- `crm.trip_quiet_idx` on `trip` (16 kB)
- `crm.trip_party_token_idx` on `trip_party` (16 kB)
- `crm.trip_stage_history_batch_idx` on `trip_stage_history` (8 kB)
- `geo.component_redirect_new_idx` on `component_redirect` (16 kB)
- `geo.component_redirect_source_idx` on `component_redirect` (16 kB)
- `geo.place_merge_country_idx` on `place_merge` (8 kB)
- `geo.place_merge_keeper_idx` on `place_merge` (8 kB)
- `geo.place_pair_verdict_hi_idx` on `place_pair_verdict` (8 kB)
- `geo.place_shape_osm_idx` on `place_shape` (16 kB)
- `geo.tour_leg_countries_gin` on `tour_leg` (1.1 MB)
- `geo.tour_place_unlinked_idx` on `tour_place` (272 kB)
- `gold_aa_internal.idx_pt_embedding` on `published_tours` (168 kB)
- `gold_aa_internal.idx_ttv_status` on `tenant_tour_versions` (16 kB)
- `gold_aa_internal.idx_ttv_tenant_id` on `tenant_tour_versions` (16 kB)
- `gold_aa_internal.tenant_tour_versions_job_idx` on `tenant_tour_versions` (16 kB)
- `gold_aa_internal.tour_lifecycle_event_tour_idx` on `tour_lifecycle_event` (16 kB)
- `gold_aa_internal.idx_aa_internal_webhook_status` on `webhook_deliveries` (8 kB)
- `shared.idx_dfs_call_log_job` on `dfs_call_log` (8 kB)
- `shared.idx_dfs_call_log_live` on `dfs_call_log` (32 kB)
- `shared.eval_golden_item_tenant_idx` on `eval_golden_item` (16 kB)
- `shared.eval_item_result_scored_idx` on `eval_item_result` (16 kB)
- `shared.eval_item_result_tenant_idx` on `eval_item_result` (16 kB)
- `shared.kpi_daily_day_idx` on `kpi_daily` (8 kB)
- `shared.idx_llm_call_log_model_created` on `llm_call_log` (26.9 MB)
- `shared.idx_notif_tenant_unread` on `notifications` (16 kB)
- `shared.ix_pipeline_jobs_created` on `pipeline_jobs` (40 kB)
- `shared.idx_pipeline_runs_status` on `pipeline_runs` (16 kB)
- `shared.idx_prompt_eval_runs_pipeline_created` on `prompt_eval_runs` (16 kB)
- `shared.report_run_job_idx` on `report_run` (8 kB)
- `shared.report_run_report_created_idx` on `report_run` (8 kB)
- `shared.writing_memory_release_tenant_idx` on `writing_memory_release` (16 kB)
- `shared.writing_memory_shadow_tenant_idx` on `writing_memory_shadow` (16 kB)
- `shared.writing_rule_tenant_status_idx` on `writing_rule` (16 kB)
- `tripplanner.job_finished_idx` on `job` (16 kB)
- `tripplanner.job_parent_idx` on `job` (8 kB)
- `tripplanner.narration_cache_created_at_idx` on `narration_cache` (16 kB)
- `tripplanner.outbox_redact_due_idx` on `outbox` (16 kB)
- `tripplanner.sessions_account_idx` on `sessions` (16 kB)

## Soft-key orphans (DM-4.2)

Cross-app keys that have no FK (data standards DM-2.3) and how many rows point at nothing in the target, as of the Verified line (counts lag between structural changes, like `~rows`). `not_applicable` = the key columns or the target do not exist yet; `no_privilege` = the dump role cannot read one side. Orphan rate = orphans / rows with a key.

| key | status | rows | without key | orphans | orphan rate |
|---|---|---|---|---|---|
| booking.trip_case_legs.(source_system, source_id) -> catalog.v_tour | ok | 14 | 0 | 0 | 0.00% |

## Personal and confidential data tags (DM-6.1)

Column comments that start with `pii:<class>` (personal data) or `conf:<class>` (`commercial`, `credential`), data standards DM-6.1; `also` = further tags named later in the same comment. Owners tag a column in the migration that creates it. Input of the RoPA (AA-Ecosys `docs/legal/register.md` section (a), `tools/data/gen_pii_inventory.py`) and the erasure runbook (DM-6.7).

**204 tagged column(s)**, 38 untagged candidate(s) in booking, crm, tripplanner, 0 finding(s).

| schema | tag | columns | named as also |
|---|---|---|---|
| `booking` | `conf:commercial` | 45 | 2 |
| `booking` | `conf:credential` | 2 | 0 |
| `booking` | `pii:address` | 3 | 0 |
| `booking` | `pii:contact` | 10 | 3 |
| `booking` | `pii:emergency_contact` | 2 | 0 |
| `booking` | `pii:free_text` | 30 | 2 |
| `booking` | `pii:name` | 5 | 8 |
| `booking` | `pii:online_id` | 5 | 0 |
| `booking` | `pii:payment` | 2 | 0 |
| `booking` | `pii:profile` | 6 | 0 |
| `booking` | `pii:travel` | 7 | 0 |
| `crm` | `conf:commercial` | 2 | 0 |
| `crm` | `conf:credential` | 7 | 0 |
| `crm` | `pii:contact` | 11 | 0 |
| `crm` | `pii:emergency_contact` | 1 | 0 |
| `crm` | `pii:free_text` | 10 | 0 |
| `crm` | `pii:government_id` | 5 | 0 |
| `crm` | `pii:health` | 1 | 0 |
| `crm` | `pii:name` | 8 | 0 |
| `crm` | `pii:online_id` | 1 | 0 |
| `crm` | `pii:profile` | 1 | 0 |
| `crm` | `pii:travel` | 1 | 0 |
| `shared` | `conf:credential` | 1 | 0 |
| `shared` | `pii:contact` | 2 | 0 |
| `shared` | `pii:free_text` | 15 | 0 |
| `shared` | `pii:name` | 1 | 0 |
| `shared` | `pii:online_id` | 7 | 0 |
| `tripplanner` | `conf:credential` | 2 | 0 |
| `tripplanner` | `pii:contact` | 4 | 0 |
| `tripplanner` | `pii:free_text` | 1 | 3 |
| `tripplanner` | `pii:name` | 1 | 2 |
| `tripplanner` | `pii:online_id` | 2 | 0 |
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
| `booking` | `country_profiles` | `internal_notes` | `conf:commercial` |  |
| `booking` | `country_profiles` | `status_reason` | `conf:commercial` |  |
| `booking` | `customer_identities` | `iss` | `pii:online_id` |  |
| `booking` | `customer_identities` | `sub` | `pii:online_id` |  |
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
| `booking` | `destination_profiles` | `internal_notes` | `conf:commercial` |  |
| `booking` | `destination_profiles` | `status_reason` | `conf:commercial` |  |
| `booking` | `hotel_room_types` | `internal_notes` | `conf:commercial` |  |
| `booking` | `hotels` | `internal_notes` | `conf:commercial` |  |
| `booking` | `inbox_events` | `payload` | `pii:contact` | `pii:name`, `pii:free_text` |
| `booking` | `inbox_events` | `error` | `pii:free_text` |  |
| `booking` | `invoice_items` | `description` | `pii:free_text` |  |
| `booking` | `invoice_items` | `reason` | `pii:free_text` |  |
| `booking` | `invoices` | `bill_to_name` | `pii:name` |  |
| `booking` | `invoices` | `bill_to_email` | `pii:contact` |  |
| `booking` | `invoices` | `bill_to_address` | `pii:address` |  |
| `booking` | `invoices` | `notes` | `pii:free_text` |  |
| `booking` | `invoices` | `terms` | `pii:free_text` |  |
| `booking` | `invoices` | `cancel_reason` | `pii:free_text` |  |
| `booking` | `media_files` | `s3_key` | `pii:profile` |  |
| `booking` | `notifications` | `title` | `pii:free_text` |  |
| `booking` | `notifications` | `message` | `pii:free_text` | `pii:name` |
| `booking` | `notifications` | `data` | `pii:contact` |  |
| `booking` | `ops_files` | `s3_key` | `pii:payment` | `pii:name` |
| `booking` | `ops_files` | `file_name` | `pii:free_text` |  |
| `booking` | `ops_files` | `removed_reason` | `pii:free_text` |  |
| `booking` | `payments` | `reference` | `pii:payment` |  |
| `booking` | `payments` | `note` | `pii:free_text` |  |
| `booking` | `payments` | `void_reason` | `pii:free_text` |  |
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
| `booking` | `supplier_bill_items` | `amount` | `conf:commercial` |  |
| `booking` | `supplier_bills` | `bill_number` | `conf:commercial` |  |
| `booking` | `supplier_bills` | `amount` | `conf:commercial` |  |
| `booking` | `supplier_bills` | `notes` | `pii:free_text` | `conf:commercial` |
| `booking` | `supplier_bills` | `cancel_reason` | `pii:free_text` |  |
| `booking` | `supplier_bookings` | `net_amount` | `conf:commercial` |  |
| `booking` | `supplier_bookings` | `cancel_reason` | `pii:free_text` |  |
| `booking` | `supplier_bookings` | `notes` | `pii:free_text` | `conf:commercial` |
| `booking` | `supplier_contracts` | `payment_terms` | `conf:commercial` |  |
| `booking` | `supplier_contracts` | `cancellation_policy` | `conf:commercial` |  |
| `booking` | `supplier_contracts` | `notes` | `conf:commercial` |  |
| `booking` | `supplier_payouts` | `amount` | `conf:commercial` |  |
| `booking` | `supplier_payouts` | `reference` | `conf:commercial` |  |
| `booking` | `supplier_payouts` | `note` | `pii:free_text` |  |
| `booking` | `supplier_payouts` | `void_reason` | `pii:free_text` |  |
| `booking` | `supplier_rates` | `net_amount` | `conf:commercial` |  |
| `booking` | `supplier_rates` | `notes` | `conf:commercial` |  |
| `booking` | `suppliers` | `internal_notes` | `conf:commercial` |  |
| `booking` | `suppliers` | `contact_name` | `pii:name` |  |
| `booking` | `suppliers` | `contact_title` | `pii:profile` |  |
| `booking` | `suppliers` | `contact_email` | `pii:contact` |  |
| `booking` | `suppliers` | `contact_phone` | `pii:contact` |  |
| `booking` | `trip_case_checks` | `title` | `pii:free_text` |  |
| `booking` | `trip_case_checks` | `note` | `pii:free_text` |  |
| `booking` | `trip_case_checks` | `emergency_contact_name` | `pii:emergency_contact` | `pii:name` |
| `booking` | `trip_case_checks` | `emergency_contact_phone` | `pii:emergency_contact` | `pii:contact` |
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
| `booking` | `trip_plan_prices` | `amount` | `conf:commercial` |  |
| `booking` | `trip_plan_prices` | `net_amount` | `conf:commercial` |  |
| `booking` | `trip_plan_prices` | `net_currency` | `conf:commercial` |  |
| `booking` | `trip_plan_prices` | `effective_margin` | `conf:commercial` |  |
| `booking` | `trip_plans` | `default_channel` | `conf:commercial` |  |
| `booking` | `trip_plans` | `price_hint_amount` | `conf:commercial` |  |
| `booking` | `trip_plans` | `price_hint_currency` | `conf:commercial` |  |
| `booking` | `trip_plans` | `price_hint_basis` | `conf:commercial` |  |
| `booking` | `trip_plans` | `commercial_notes` | `conf:commercial` |  |
| `booking` | `trip_plans` | `supplier_id` | `conf:commercial` |  |
| `booking` | `v_customer_summary` | `name` | `pii:name` |  |
| `booking` | `v_customer_summary` | `email` | `pii:contact` |  |
| `booking` | `v_customer_summary` | `phone` | `pii:contact` |  |
| `booking` | `v_customer_summary` | `address` | `pii:address` |  |
| `booking` | `version_item_costs` | `net_amount` | `conf:commercial` |  |
| `booking` | `version_item_costs` | `supplier_note` | `conf:commercial` |  |
| `crm` | `agency_supplier` | `contact_name_enc` | `pii:name` |  |
| `crm` | `agency_supplier` | `contact_email_enc` | `pii:contact` |  |
| `crm` | `agency_supplier` | `default_commission_pct` | `conf:commercial` |  |
| `crm` | `channel_account` | `address_enc` | `pii:contact` |  |
| `crm` | `client_link` | `token_hash` | `conf:credential` |  |
| `crm` | `document` | `filename_enc` | `pii:free_text` |  |
| `crm` | `form_submission` | `payload_enc` | `pii:contact` |  |
| `crm` | `ingest_address` | `forwarding_confirmation_enc` | `conf:credential` |  |
| `crm` | `integration_credential` | `account_ref` | `pii:contact` |  |
| `crm` | `integration_credential` | `secret_enc` | `conf:credential` |  |
| `crm` | `message` | `subject_enc` | `pii:free_text` |  |
| `crm` | `message` | `body_enc` | `pii:free_text` |  |
| `crm` | `message` | `body_html_enc` | `pii:free_text` |  |
| `crm` | `message` | `from_enc` | `pii:contact` |  |
| `crm` | `message` | `to_enc` | `pii:contact` |  |
| `crm` | `message` | `rfc_message_id_enc` | `pii:contact` |  |
| `crm` | `message_template` | `body_enc` | `pii:free_text` |  |
| `crm` | `note` | `body_enc` | `pii:free_text` |  |
| `crm` | `option` | `net_amount` | `conf:commercial` |  |
| `crm` | `otp_challenge` | `code_hash` | `conf:credential` |  |
| `crm` | `otp_challenge` | `session_hash` | `conf:credential` |  |
| `crm` | `otp_challenge` | `code_enc` | `conf:credential` |  |
| `crm` | `placeholder_map` | `map_enc` | `pii:free_text` |  |
| `crm` | `proposal` | `body_enc` | `pii:free_text` |  |
| `crm` | `proposal` | `accepted_name_enc` | `pii:name` |  |
| `crm` | `proposal_day` | `notes_enc` | `pii:free_text` |  |
| `crm` | `saved_reply` | `body_enc` | `pii:free_text` |  |
| `crm` | `signature_request` | `signed_name_enc` | `pii:name` |  |
| `crm` | `studio_invitation` | `cognito_sub` | `pii:online_id` |  |
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
| `shared` | `eval_golden_item` | `input` | `pii:free_text` |  |
| `shared` | `eval_golden_item` | `control_output` | `pii:free_text` |  |
| `shared` | `eval_golden_item` | `pipeline_verdict` | `pii:free_text` |  |
| `shared` | `eval_golden_item` | `label` | `pii:free_text` |  |
| `shared` | `eval_golden_set` | `label_history` | `pii:online_id` |  |
| `shared` | `eval_item_result` | `output` | `pii:free_text` |  |
| `shared` | `tenant_members` | `cognito_iss` | `pii:online_id` |  |
| `shared` | `tenant_members` | `cognito_sub` | `pii:online_id` |  |
| `shared` | `tenant_membership_event` | `membership` | `pii:online_id` |  |
| `shared` | `writing_memory_release` | `retired_reason` | `pii:free_text` |  |
| `shared` | `writing_memory_release` | `rejected_reason` | `pii:free_text` |  |
| `shared` | `writing_memory_release` | `notes` | `pii:free_text` |  |
| `shared` | `writing_memory_shadow` | `output` | `pii:free_text` |  |
| `shared` | `writing_rule` | `rule_text` | `pii:free_text` |  |
| `shared` | `writing_rule` | `replacement` | `pii:free_text` |  |
| `shared` | `writing_rule` | `match_phrases` | `pii:free_text` |  |
| `shared` | `writing_signal` | `before_text` | `pii:free_text` |  |
| `shared` | `writing_signal` | `after_text` | `pii:free_text` |  |
| `shared` | `writing_signal` | `problem` | `pii:free_text` |  |
| `tripplanner` | `customers` | `name` | `pii:name` |  |
| `tripplanner` | `customers` | `phone` | `pii:contact` |  |
| `tripplanner` | `customers` | `email` | `pii:contact` |  |
| `tripplanner` | `outbox` | `payload` | `pii:contact` | `pii:name`, `pii:free_text`, `pii:travel` |
| `tripplanner` | `sessions` | `guest_token` | `conf:credential` |  |
| `tripplanner` | `sessions` | `guest_token_hash` | `conf:credential` |  |
| `tripplanner` | `traveller_accounts` | `iss` | `pii:online_id` |  |
| `tripplanner` | `traveller_accounts` | `sub` | `pii:online_id` |  |
| `tripplanner` | `trip_drafts` | `itinerary` | `pii:travel` | `pii:free_text` |
| `tripplanner` | `trip_drafts` | `date_start` | `pii:travel` |  |
| `tripplanner` | `trip_drafts` | `date_end` | `pii:travel` |  |
| `tripplanner` | `trip_events` | `payload` | `pii:free_text` | `pii:travel` |
| `tripplanner` | `v_inquiry_outbox` | `payload` | `pii:contact` | `pii:name`, `pii:free_text`, `pii:travel` |

### Tag findings

- none

### Untagged candidates

Columns of `booking`, `crm`, `tripplanner` without a tag whose name contains one of the tokens `address`, `data`, `email`, `iss`, `itinerary`, `label`, `message`, `name`, `note`, `notes`, `payload`, `phone`, `snapshot`, `sub`, `summary`, `title` (whole snake_case tokens) and that are not on the allowlist (AA-CIS-Infra `db/gen_schema_reference.py` `PII_ALLOWLIST`). Tag them in an owner migration or allowlist them with a reason.

- `crm.aa_catalog_tour.title`
- `crm.aa_content.title`
- `crm.agency_supplier.name`
- `crm.agreement_doc.version_label`
- `crm.booking_line.aa_sub_status`
- `crm.booking_line.title`
- `crm.channel_account.address_bidx`
- `crm.conversation.last_message_at`
- `crm.dispatch_queue.message_ref`
- `crm.dispatch_queue.message_id`
- `crm.form_submission.payload_redacted_at`
- `crm.ingest_address.ingest_address_id`
- `crm.intake_form.label`
- `crm.job.payload`
- `crm.member.cognito_iss`
- `crm.member.cognito_sub`
- `crm.member_invitation.email_enc`
- `crm.member_invitation.email_bidx`
- `crm.member_invitation.cognito_iss`
- `crm.member_invitation.cognito_sub`
- `crm.message.message_id`
- `crm.message.attachment_notes`
- `crm.message.rfc_message_id_hash`
- `crm.message_template.message_template_id`
- `crm.message_template.title`
- `crm.metric_event.name`
- `crm.note.note_id`
- `crm.option.title`
- `crm.option_block.title`
- `crm.otp_challenge.message_id`
- `crm.prep_pack_selection.title`
- `crm.proposal.accepted_name_erased_at`
- `crm.proposal_day.title`
- `crm.saved_reply.title`
- `crm.status_transition.table_name`
- `crm.studio_invitation.email_enc`
- `crm.studio_invitation.cognito_iss`
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
| `booking.v_supply_hotels.name` | a hotel (business) name (bk-023 contract view of hotels.name) |
| `booking.v_supply_hotels.address` | a hotel (business) address (bk-023 contract view of hotels.address) |
| `booking.v_supply_services.working_title` | internal working title of a supplier service (bk-023 contract view of services.title), no customer data |
| `tripplanner.job.payload` | job payloads carry flags and counts only (DM-6.3; tp-021, the retention kind's trigger / dry_run / max_rows) |
| `tripplanner.narration_cache.itinerary_hash` | hash of a catalog itinerary (cache key), no identity |

## RLS catalogue guard (X2)

Rules in AA-CIS-Infra `db/rls_catalogue_rules.py` (byte copy of AA-CIS-App `tests/integration/rls_catalogue_rules.py`, which CIS CI runs on the replayed migrations). A violation is a finding that is not on the allowlist; each allowlist entry carries a one-line reason. Fix the object or allowlist it in the CIS file, then copy it here.

**2 unallowlisted violation(s)**, 98 allowlisted finding(s), 17 stale allowlist entry(ies).

| rule | meaning | violations | allowlisted |
|---|---|---|---|
| a | tenant_id table without RLS + an app.tenant_id policy | 1 | 21 |
| b | policy TO PUBLIC | 0 | 8 |
| c | policy reads app.current_tenant | 0 | 0 |
| d | current_setting('app.tenant_id') outside NULLIF | 0 | 0 |
| e | foreign key across owners | 0 | 0 |
| p | grant to PUBLIC | 0 | 1 |
| g | grant to another owner's role | 1 | 67 |
| t | unconditional (true) policy | 0 | 1 |

### Violations

- [a] `booking.b2b_partners`: RLS off
- [g] `booking.v_ops_inquiry_inbox:cis_app`: booking object to cis role: SELECT

### Allowlist entries in use

| rule | entry | findings | reason |
|---|---|---|---|
| a | `acp_shared.acp_output_rules` | 1 | RLS on with the X1 cis_app parity policy only (CIS 244); no tenant-pool grant |
| a | `acp_shared.acp_quota_ledger` | 1 | tenant quota ledger; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.audit_log` | 1 | tenant action audit log; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.debate_brand_fit_cache` | 1 | pipeline cache keyed by tenant; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `acp_shared.tenant_config` | 1 | tenant settings, admin + pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.decision_log` | 1 | Jev decision audit; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.dfs_call_log` | 1 | DataForSEO cost log; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.jev_tenant_allowlist` | 1 | Jev rollout switch per tenant (admin-managed); platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.llm_call_daily` | 1 | cost log roll-up; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.llm_call_log` | 1 | cost log of every app; tenant_id is attribution; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_api_usage` | 1 | API metering written by the middleware; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_api_usage_monthly` | 1 | API metering roll-up; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_export_config` | 1 | tenant export settings, admin + pipeline only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_members` | 1 | CIS membership directory (AA-978, 276), served over HTTP only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
| a | `shared.tenant_membership_event` | 1 | tenant.membership.v1 feed (AA-978, 276), HTTP only; platform table, cis_app only (no tenant-pool grant); tenant_id is filtered in code |
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
| g | `booking.v_ops_data_totals:cis_app` | 1 | contract: CIS data coverage page, counts only (bk-025) |
| g | `booking.v_ops_funnel_daily:cis_app` | 1 | contract: CIS ops dashboard (bk-017) |
| g | `booking.v_ops_trip_plan_keys:cis_app` | 1 | contract: CIS data coverage page, plan catalog keys only (bk-025) |
| g | `booking.v_supply_hotels:cis_app` | 1 | contract: supply.hotel.v1 facts for the CIS content consumer (bk-023) |
| g | `booking.v_supply_media:cis_app` | 1 | contract: supplier photo ids, rights and keys for CIS copies (bk-023) |
| g | `booking.v_supply_outbox:cis_app` | 1 | contract: the supply feed CIS pulls (bk-023) |
| g | `booking.v_supply_services:cis_app` | 1 | contract: supply.service.v1 facts for the CIS content consumer (bk-023) |
| g | `booking:cis_app` | 1 | contract: schema USAGE for the CIS ops views (bk-017) |
| g | `catalog.*:booking` | 19 | contract: catalog.* views for Booking (CIS 225, 228) |
| g | `catalog.*:tripplanner` | 20 | contract: catalog.* views for TripPlanner (CIS 225, 228) |
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
| g | `tripplanner.v_ops_component_id_map:cis_app` | 1 | contract: CIS data coverage page, id-map edges (tp-020) |
| g | `tripplanner.v_ops_data_totals:cis_app` | 1 | contract: CIS data coverage page, totals only (tp-020) |
| g | `tripplanner.v_ops_pin_components:cis_app` | 1 | contract: CIS data coverage page, pinned component ids (tp-020) |
| g | `tripplanner.v_ops_traffic_daily:cis_app` | 1 | contract: CIS ops dashboard (tp-015) |
| g | `tripplanner:booking` | 1 | contract: schema USAGE for the inquiry outbox (tp-009) |
| g | `tripplanner:cis_app` | 1 | contract: schema USAGE for the CIS ops view (tp-015) |
| p | `public` | 1 | PostgreSQL default USAGE on the public schema (extensions); no app object lives there |
| t | `acp_contract.tour_atoms:catalog_owner_read` | 1 | catalog_owner views read every atom as before (CIS 266); D9 = 0 guarded |

Stale entries (matched nothing on this database; remove them from the CIS file): [a] `retired.acp_runs`, [a] `retired.route_pick`, [a] `retired.tenant_atom_state`, [a] `retired.tenant_brand_rule_versions`, [a] `retired.tenant_brand_rules_deleted_aa404`, [e] `tripplanner.*->shared.destinations`, [g] `acp_contract.tour_atoms.*:tripplanner`, [g] `acp_contract.v_active_tour_atoms.*:tripplanner`, [g] `acp_contract:tripplanner`, [g] `gold_aa_internal.published_tours:tripplanner`, [g] `gold_aa_internal:tripplanner`, [g] `shared.destinations:tripplanner`, [g] `shared.v_destination_photos:tripplanner`, [g] `shared.v_tour_photos:tripplanner`, [g] `silver_aa_internal.raw_tours.country:tripplanner`, [g] `silver_aa_internal.raw_tours.tour_id:tripplanner`, [g] `silver_aa_internal:tripplanner`.

## Schema drift against a replay of all migrations (AA-853)

<!-- drift-fingerprint: b9ed63e476d023c60e1714281acd1cdeafd27aba6f75150b774a83b777d28486 -->

**Drift verdict: open** (4 open finding(s), 1 failed replay file(s); 5 finding(s) carry an owner decision and do not count as open)

AA-CIS-Infra `db/replay_migrations.py` replayed every applied migration (live `shared.schema_versions` order) into a scratch PostgreSQL 15.16 (Debian 15.16-1.pgdg12+1) and `db/schema_drift.py` compared its catalog with the live dump above. Replay: 385 files, 379 ok, 5 partly (legacy files, psql semantics), 1 failed; 19 legacy files without a registry row replayed in number order, 1 registered versions without a file.

**Unmanaged** (on Dev, no migration creates it): **5** finding(s), 41 object(s) with their children; **4 without an owner decision**. **Missing** (a migration creates it, not on Dev): 4. **Changed**: 0. Findings explained by a failed replay file (it changes the object with DDL): 4; **not explained by the replay** (drift on Dev to decide): 5, of them unmanaged 1. Privilege differences (informational): 21. Owner decisions live in AA-CIS-Infra `db/schema_drift_decisions.json`; `drift.json` in the workflow artifact has every finding. Report only: a finding fails nothing, and findings a replay gap explains do not move the drift fingerprint.

Replay gaps (6: files that failed or ran partly; their objects show up as unmanaged until the history is fixed or a baseline file covers them):

| file | key | status | first error |
|---|---|---|---|
| `cis/001_initial_schema.sql` | v1.0 | partial | 19 statement(s) failed; first: line 34: InvalidTextRepresentationError 22P02 invalid input value for enum ops.pipeline_status_enum: "pendin… |
| `cis/004_tenant_rls.sql` | - | partial | 18 statement(s) failed; first: line 51: UndefinedFunctionError 42883 operator does not exist: uuid = text HINT:  No operator matches the gi… |
| `cis/005_tenant_config.sql` | - | partial | 11 statement(s) failed; first: line 57: UndefinedObjectError 42704 role "app_user" does not exist |
| `cis/006_export_webhook.sql` | - | partial | 6 statement(s) failed; first: line 60: UndefinedFunctionError 42883 operator does not exist: uuid = text HINT:  No operator matches the giv… |
| `cis/007_seed_test_tenants.sql` | - | partial | 7 statement(s) failed; first: line 34: NotNullViolationError 23502 null value in column "slug" of relation "tenants" violates not-null cons… |
| `tripplanner/021_job_table_outbox_redaction.sql` | tp-021 | failed | RaiseError P0001 tp-021: role tripplanner cannot UPDATE tripplanner.outbox.redacted_at |

### Unmanaged (5)

| object | owner | detail | replay gap | decision |
|---|---|---|---|---|
| `relation public.checkpoint_migrations` | - | +2 child object(s) table | - | keep (AA-853) |
| `function tripplanner.job_set_updated_at()` | tripplanner |  | `tripplanner/021_job_table_outbox_redaction.sql` | **open** |
| `relation tripplanner.job` | tripplanner | +34 child object(s) table | `tripplanner/021_job_table_outbox_redaction.sql` | **open** |
| `column tripplanner.outbox.redacted_at` | tripplanner |  | `tripplanner/021_job_table_outbox_redaction.sql` | **open** |
| `index tripplanner.outbox outbox_redact_due_idx` | tripplanner |  | `tripplanner/021_job_table_outbox_redaction.sql` | **open** |

### Missing (4)

| object | owner | detail | replay gap | decision |
|---|---|---|---|---|
| `schema bronze` | - |  | - | keep-dropped (AA-853) |
| `schema gold` | - | +26 child object(s) | - | keep-dropped (AA-853) |
| `schema ops` | - | +10 child object(s) | - | keep-dropped (AA-853) |
| `schema silver` | - | +12 child object(s) | - | keep-dropped (AA-853) |

## Connections at dump time

Client sessions per `application_name` (`(empty)` = a pool without `application_name`, standards C1.1a).

| application_name | role | state | sessions |
|---|---|---|---|
| booking-api | booking | idle | 1 |
| cis-api | cis_app | idle | 1 |
| cis-worker | cis_app | idle | 1 |
| crm-api | crm_app | idle | 1 |

## Latest migrations

| version | applied_at | description |
|---|---|---|
| bk-035 | 2026-10-29 20:49:44.896805+00:00 | AA-1003: inquiry inbox key contract view booking.v_ops_inquiry_inbox, SELECT to cis_app |
| 305 | 2026-10-29 17:37:52.522293+00:00 | AA-1003: shared.kpi_daily + shared.report_run (report core R1) |
| 304 | 2026-10-29 17:20:54.894722+00:00 | AA-1002: llm_provider_connection + llm_model_deployment (backfilled), catalog capabilities, provider / api_style / spend_budget CHECKs widened |
| bk-034 | 2026-10-29 16:57:03.372025+00:00 | AA-993: index trip_case_version_itinerary.source_tour_id (lifecycle affected cases) |
| 303 | 2026-10-29 07:17:11.115750+00:00 | AA-671: shared.place_photo.destination_match_source (who set the destination) |
| tp-021 | 2026-10-29 06:20:06.090685+00:00 | AA-861: tripplanner.job (ADR 0003a template) + outbox.redacted_at and its redaction index |
| 302 | 2026-10-29 06:13:05.038763+00:00 | AA-814: acp_shared.facts kind / valid_until / updated_by (Facts Entry API); DELETE to aa_app_user (own tenant facts under tenant_isolation) |
| 301 | 2026-10-29 00:05:17.821219+00:00 | AA-995: shared.place_photo.s3_key_medium (960 w WebP rendition for mobile heroes) |
| 300 | 2026-10-28 17:38:43.953045+00:00 | AA-795: tenant_tour_versions.judge_breakdown (T2 judge verdict + brand-claim check, admin-only) |
| 298 | 2026-10-28 17:18:34.893308+00:00 | AA-996: catalog.v_tour_place_name (booking) — the places of a tour day by name only, row for row v_tour_place's names without the card / destination / segment lookups |
| 297 | 2026-10-28 15:22:15.671018+00:00 | AA-920 WM-25: tenant_tour_versions.generation_meta (T2 writing-memory stamp, admin-only) |
| bk-033 | 2026-10-28 14:38:26.944894+00:00 | AA-996: widen trip_plan_prices.effective_margin to NUMERIC(12, 4) (bk-032 restored to its applied bytes) |
| 299 | 2026-10-28 12:59:04.542905+00:00 | AA-850: drop the four empty legacy ACP v1 schemas acp_gold_output, acp_silver_s2, acp_silver_s3, acp_silver_s4 |
| 295 | 2026-10-28 12:44:58.009693+00:00 | AA-998: llm_model_catalog drops the acc1 profiles; llm_role_config.account_route acc3 only |
| 296 | 2026-10-28 11:41:26.867258+00:00 | AA-850 wave 1 (DM-3.9 step 2): drop the 8 tables and 2 views quarantined in retired by 294 (14-day wait waived by Nghiệp, S255) |
| 294 | 2026-10-28 10:26:50.006498+00:00 | AA-850 wave 1 (DM-3.9): quarantine 8 dead CIS tables and 2 dead views in schema retired (no grants); drop after >= 14 days |
| 293 | 2026-10-28 07:58:33.647075+00:00 | AA-665 C2: dfs_call_log.job_id + partial index (DataForSEO spend by job) |
| crm-023 | 2026-10-28 07:05:57.161539+00:00 | AA-993 G4b: the crm_dispatch send marker (crm.dispatch_attempt, committed before the provider call; at most one open per dispatch row; closed once, CRM38), dispatch_queue gate code send_uncertain, erase_subject + dispatch_attempt |
| bk-032 | 2026-10-28 04:26:30.456448+00:00 | AA-996: trip_plans.supplier_id and trip_plan_prices (per-person price list per channel, season / validity, pax band and currency, replaced as a set and audited) |
| 292 | 2026-10-28 03:29:05.759552+00:00 | AA-919 (WM-19 / WM-21 review): release guard requires the r2 eval run and the shadow run to name the release (no code-train, seeded-fault or other release's run as evidence) |
