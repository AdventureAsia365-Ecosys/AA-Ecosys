# AA-712 — CIS-side map (read-only survey, S236)

Scope: what already exists in AA-CIS-App that the "place pipeline moves to CIS" work (AA-712, ADR 0002
consequence 1) must plug into or can reuse. Local checkout of AA-CIS-App is `main` @ f5f13331 (#719);
`origin/main` is 1a10c1c7 (#724) — migration 225 (#723) was read from git (`git show 2d5fec2f:...`), it is
not in the working tree yet. Schema facts from `docs/architecture/db-schema-reference.md` (verified S235,
latest migration 224 — **does not yet list `catalog.*`**, regenerate after 225).

---

## 1. Durable job runner (ADR 0003) — where AA-712 job kinds land

| Piece | File | Facts |
|---|---|---|
| Queue SQL | `shared/jobs/queue.py` | `enqueue(pool, kind, payload, idempotency_key=, max_attempts=, parent_job_id=, created_by=, run_after=)` → `(job_id, created)`; `ON CONFLICT (idempotency_key) DO NOTHING` returns the existing job. `claim()` = `pg_advisory_xact_lock(650_001)` + `FOR UPDATE SKIP LOCKED`, per-kind running cap checked inside the claim (global across workers). Backoff `30s * 2^(attempt-1)`, cap 900 s. Lease 90 s, heartbeat 20 s, reaper every 30 s. Graceful release does not count an attempt (`MAX_RELEASES=3`). |
| Registry | `shared/jobs/registry.py` | `@job_kind(name, concurrency=1, max_attempts=3, on_terminal=None, expected_seconds=600)`. Handler `async def run(ctx: JobContext) -> dict`; `ctx.payload`, `ctx.pool`, `ctx.progress(**fields)`, `ctx.add_cost(usd)` (non-LLM spend, e.g. Mapbox if billed), `ctx.set_result()`. `NonRetryable` = fail at once; `BudgetExceeded` → `stopped_budget`. `registry.enqueue()` applies the kind's `max_attempts`. |
| Worker | `shared/jobs/worker.py`, ECS service `aa-cis-dev-worker` (`python -m shared.jobs.worker`) | `JOB_WORKER_MAX_PARALLEL` default 8; `caps()` = every registered kind's concurrency. Binds `call_log.bind_job(job_id)` so every `llm_call_log` row the job causes carries `job_id` (job cost = `job.cost_usd` + sum of those rows). AA-711: old task stops claiming once a newer task revision is live. API runs with `JOB_WORKER_IN_API=false`. |
| Kind registration | `services/jobs/__init__.py` | Import-to-register: a new `services/jobs/<x>_job.py` must be added here or the worker never claims it. |
| Existing caps | `services/jobs/*` | s1_rewrite 6, t2_rewrite/t8_angles/t9_write 4, revalidate/t7_slate 2, **a3_atomize 1**, recompute 1, photo_sync 1, **place_cards_build 1**, segment_research 1, s1_seo_prefetch 1, s1_batch_ingest 1. Rule (S217): `s1_rewrite` cap + `a3_atomize` cap < slot budget (8). A new place-pipeline kind at cap 1–2 fits. |
| Admin observability | `api/routers/admin_job_runner.py` → `/admin/job-runner/{jobs,summary,deploy-gate,workers,jobs/{id},jobs/{id}/llm-calls,jobs/{id}/cancel,jobs/{id}/retry}`; FE `/admin/jobs` | `expected_seconds` flags (never stops) a long job; `progress.{step,done,total}` convention for long kinds (a3_atomize since AA-688). `queue.domain_links()` adds per-kind links on the job detail — extend it for the new kind (tour_id in payload). **`/deploy-gate`**: CI refuses a backend deploy while jobs are queued/running → a long country-wide extraction blocks deploys; keep jobs per tour. |

### How A3 atomize enqueues follow-ups (the hook point for AA-712)
- Publish: `services/export/handler.py::process_export()` upserts `gold_aa_internal.published_tours`
  (`ON CONFLICT (tour_id)`), sets `raw_tours.pipeline_status='published'`, then
  `enqueue_a3_atomize(conn, tour_id, version_id=generated_content.id, ...)` with
  `idempotency_key = "a3_atomize:<version_id>"` (best-effort, publish never fails on enqueue).
- `services/jobs/a3_atomize_job.py` runs `_run_a3_atomize_background()` **in its own thread + event loop**
  (Cohere pacing `time.sleep` starved /health in S201). Inside: `run_a3_atomize()` → `run_stages(["segment"],
  RecomputeScope(tour_id))` → `enqueue_recompute(scope="platform", segment_ids, debounce_s=WAVE_DEBOUNCE_S)`
  (`services/jobs/recompute_job.py`: one queued platform job absorbs a wave, `run_after` slides, capped by MAX_WAIT_S).
- **Nothing enqueues place cards or a place/geo pipeline after atomize today.** Place cards are built by
  (a) admin "Build place cards" on Content Quality (`place_cards_build`, one tour, `MAX_PLACES=40`) and
  (b) T8 on demand for its one request atom (`build_card_for_atom`). T9 only reads cards.
- Natural AA-712 hook: at the end of `_run_a3_atomize_background` (next to `enqueue_recompute`), enqueue
  a per-tour place job with idempotency key `"<kind>:<version_id>"` (same dedupe as atomize). Note the
  atomize job uses `max_attempts=2` and `reraise=True`; follow-up enqueue should be best-effort like recompute.
- Other enqueue sites to know: `api/routers/admin_atoms.py:636` (admin re-atomize, `dedupe=False`),
  `admin.py:52` + `admin_atoms.py:488` (recompute after status change/atom delete), `admin_photos.py:239` (photo_sync).

---

## 2. Place card pipeline — already resolves atoms → places (biggest reuse)

`services/acp_shared/place_cards.py` (1117 lines, AA-772, migrations 220/221/222, AA-809 dedupe in #719):
- Input: atom ids from `acp_contract.v_active_tour_atoms` (`place IS NOT NULL`, not deleted, not empty marker).
- Free filters before any call: `card_skip_reason()` (unnamed places via `ranking_reference.names_somewhere`,
  logistics: hotels/camps/airports/border gates on stay/transit/food atoms), `is_generic_name()`.
- Grouping: `atom_group_key()` = (`place_norm`, tour country) → one draft per distinct place; generic names
  are one group per atom, matched only by `pick_local_card()` (locality named in the itinerary sentence).
- Reuse with no call: `find_existing_cards()` (place_key / alias / core name), `find_local_cards()`,
  negative cache `acp_shared.place_card_miss` (`MISS_RETRY`: no_name 30 d, identity_rejected 14 d, error 1 d;
  invalidated by `RULE_VERSION` / `PROMPT_SHA`).
- Paid: `draft_card()` stage `a3_place_card` (validate, GPT-5.6 Luna acc3 → sonnet) returns
  display_name, locality, region, country, naming_note, aliases, 4–6 facts; `check_card()` stage
  `a3_place_card_check` (validate, Haiku acc3 → sonnet). Logged via `record_call_with_pool` (`_log`).
- Persist: `acp_shared.place_card` (card_id, place_key, display_name, locality, region, country, naming_note,
  facts jsonb, status verified/rejected/…, cost_usd), `atom_place_card` (atom_id → card_id | miss_reason),
  `place_card_alias` (alias_norm, country_norm → card_id). `place_key` = core name | country (generic: core |
  locality | country). `find_card_for_draft()` resolves a checked draft against existing cards (AA-809).
- Admin: verify / reject / merge duplicates (`merge_cards`, `duplicate_clusters`) on Content Quality.
- Entry points: `ensure_place_cards(atom_ids, pool, force=, max_places=)` (returns counters),
  `build_card_for_group`, `build_card_for_atom`.

**What a place card does NOT have:** no lat/lng, no `destination_id`, no geocode. Identity is text only.

### Compare with TripPlanner extraction (frozen, `AA-TripPlanner-Web/backend/extraction/`)
| TP step | TP file | CIS equivalent / reuse |
|---|---|---|
| Read active atoms | `components.py` ATOMS_SQL on `v_active_tour_atoms` | same view as `place_cards_build` |
| Skip lodging/transit "places" | `tour_days.anchor_place`, `deterministic.categorize_atom` | `card_skip_reason()` (similar intent, different rules — unify on one) |
| Group by place | per tour, `dict.fromkeys(names)` | `atom_group_key` (place_norm + country), cross-tour |
| Name → `shared.destinations` link | `geocode._lookup_cached` = `lower(name)` exact, **global** (unique index on lower(name), no country) | none in CIS; `catalog.v_tour_place` (225) joins destinations on `lower(name) IN (card.display_name, atom place) AND lower(country)` |
| Coordinates | `locate.py`: one `tp_extract` call per 40 names → [lat,lng,country] or null, Mapbox proximity confirm within 25 km, else keep LLM point; reject non-AA countries | **missing in CIS** — must port (Mapbox token `MAPBOX_GEOCODING_TOKEN` in TP env/config → CIS secret per ADR 0002) |
| Activity / intensity / season / duration_hint | `deterministic.categorize_atom` (no model) | atoms already carry `activity_type`; no CIS equivalent of intensity/season |
| Embedding | `tp_component_embed`, 96/batch | CIS gateway `shared.llm_client.embed.embed(stage, texts)` (Cohere v4 on acc2, catalog `api_style='embed'`) |
| Day skeleton (start/end/overnight) | `tour_days.py` rules + `tp_extract` over `published_tours.aa_itineraries`, grounded per day, sha256 skip | `catalog._tour_day_text` (225) parses the same canonical "Day N —" text in SQL (Python twin `itinerary_utils.parse_canonical_itinerary_days`); no overnight/start/end extraction in CIS |
| Tour graph (stops, legs, edges, junctions) | `tour_graph.py` `rebuild()` (pure builders + `persist_graph`) | none in CIS; pure functions port as-is |

**Recommended reuse shape:** place card = the identity layer (one per real place, admin-curated, deduped);
add geo resolution **per card** (card → destination), not per atom name. Then itinerary_components /
tour_stop rows derive from `atom_place_card` + card → destination. Gaps to decide:
1. Link column: `place_card.destination_id` (CIS migration) vs a `card_destination` table; today 225
   links by name equality at read time (fragile, no FK).
2. `shared.destinations` uniqueness is `lower(name)` global (per TP geocode.py docstring) while place_key is
   per country — same name in two countries collides. Needs a CIS migration (name+country key) before CIS
   becomes the writer.
3. Skipped places: cards skip hotels/logistics, but TP's `tour_day.overnight_destination_id` needs the
   overnight town (not the hotel) → overnight anchor extraction must be kept separately.
4. Cost: place cards cap 40 places/job and only draft unseen places; geocode should be likewise once per
   card (cached on the destination row), never per tour.

---

## 3. Model Gateway (stage registration + cost logging)

- All calls via `shared/llm_client/` (`LLMClient.generate(LLMRequest(stage=...))`, embeddings via
  `embed.embed(stage, texts)`). `tests/unit/test_aa685_no_raw_model_calls.py` fails on raw Bedrock/OpenAI
  calls outside the gateway.
- Stage route = row in `shared.llm_role_config` (stage PK, role writer|judge|validate, provider, model_id,
  account_route, fallback_model_ids[], shadow_model_id, shadow_sample_pct), 20 s cache; fallback
  `SAFE_DEFAULTS` dict in `shared/llm_client/role_config.py` (e.g. lines 120–122 for `a3_place_card*`).
- **New stage = CIS migration** `INSERT INTO shared.llm_role_config ... ON CONFLICT (stage) DO NOTHING`
  (pattern: migration 221 §4) + a `SAFE_DEFAULTS` entry + `shared.schema_versions` row. Model change =
  `UPDATE` migration with evidence + rollback in the header (pattern: 222). S235 rule (224): Bedrock first;
  an OpenAI-API model only as LAST fallback. Place-card style stages are `validate` (ADR 0008: reference
  data, any vendor).
- TripPlanner's own stages (`tp_compose`, `tp_search_embed`, `tp_extract`, `tp_component_embed`) were
  registered by CIS migrations 172/173 (TP has SELECT on role_config/catalog, INSERT on llm_call_log).
  AA-712 should register CIS-side keys (e.g. `a3_place_locate`, `a3_place_embed`) rather than reuse `tp_*`.
- Cost logging: `record_call_with_pool(pool, stage=, role=, model=, tokens_in=, tokens_out=, cost_usd=,
  quality_signal=, tenant_id=, account=, fallback_used=, provider=)` (`call_log.py:158`) /
  `record_call_sync`. Inside a job the row gets `job_id` automatically. Non-LLM paid calls (Mapbox) →
  `ctx.add_cost()`; consider a `spend_budget` row `job:<kind>` (`shared/cost_guard.py`, AA-649) if Mapbox is paid.

---

## 4. Secrets Manager pattern

`shared/secrets.py`: `_fetch_secret_sdk(arn_or_name)` (boto3, region `AWS_DEFAULT_REGION` default us-west-1)
+ 1 h in-memory TTL cache `_get_cached(key, fn)`. Per-secret getter with env override first:
`get_database_url()` (`SECRET_DB_ARN` → else `DATABASE_URL`), `get_dataforseo_creds()`
(`SECRET_DATAFORSEO_ARN`, JSON login/password), `get_typesafe_api_key()` (`TYPESAFE_API_KEY` env, else
secret id from `SECRET_TYPESAFE_ID`, default `aa-cis/dev/typesafe`; bare or JSON `api_key`). Photos read
`aa-cis/dev/gdrive-photo-reader` via `services/photos/drive.load_credentials()`.
→ Mapbox: add `get_mapbox_token()` same shape (`MAPBOX_TOKEN` env, else `SECRET_MAPBOX_ID` default
`aa-cis/dev/mapbox`); secret created in acc2 + task-role read grant in AA-CIS-Infra (worker task role).
Underscore env names: per user rule, Nghiệp edits them by hand.

---

## 5. Tour identity: publish / re-upload / trash vs `published_tours`

- `gold_aa_internal.published_tours` keyed by `tour_id` (upsert `ON CONFLICT (tour_id)` in
  `shared/repository/published_catalog_repository.py`; no `updated_at`, `published_at=NOW()` on each publish).
  `master_status` enum active | inactive | trashed (+ `deleted_at`).
- **Re-upload** (`api/routers/admin_pipeline.py` ~1726, staging decision replace/update): old
  `raw_tours` rows of the `source_group_id` → `source_status='superseded'`; INSERT a **new `tour_id`**
  with `source_version+1`, same `source_group_id`. The new tour runs S1 → review → publish → its own
  `published_tours` row and atoms. The old `published_tours` row is NOT changed by the re-upload itself.
  `keep_both` inserts the new one as superseded. `set-active` endpoint flips which version is active.
- **Trash source** (`admin.py` ~1650, AA-716): `raw_tours.source_status='trashed'` + cascade
  `published_tours.master_status='inactive'` (only if active), dismiss pending review, then
  `_recompute_after_status_change` → `recompute` job. Restore reverses (inactive → active).
- **Master status change** (`admin.py` ~1545) / **trash master** (`/admin/master/{id}/trash` →
  `master_status='trashed'`, `deleted_at`) → AA-713 recompute job.
- Consequence for AA-712: keying place outputs by `tour_id` (as TP does: `source_tour_id`) orphans them on
  re-upload; the stable key is `source_group_id` (catalog `source_id`). Liveness = `v_active_tour_atoms`
  rule (master active, not deleted) + `raw_tours.source_status='active'`. A trash/status change should also
  enqueue the place job (or the readers filter through catalog views, which already hide dead tours).
  There is no outbox yet (`catalog.tour.published|updated|trashed` is the next AA-679 slice) — consumers
  poll `catalog.v_tour.content_hash`.

---

## 6. Catalog views — migration 225 (AA-679, merged #723, origin/main)

Schema `catalog`, views owned by NOLOGIN `catalog_owner` (no BYPASSRLS; RLS policy
`catalog_owner_aa_master_read` on published_tours/raw_tours = AA master tenant
`00000000-0000-0000-0000-000000000001`), `security_barrier`, granted SELECT to `aa_app_user`, `tripplanner`,
`booking`. Also fixes `tenant_isolation` to `NULLIF(current_setting('app.tenant_id', true), '')::uuid`.
- `catalog.v_tour`: `source_system='cis'`, `source_id = COALESCE(source_group_id, tour_id)`, tour_id,
  source_version, slug, title/summary/…, itinerary_text, cover_photo_path, photo_count, `content_hash`
  (md5 of content; the change signal), updated_at (informative only).
- `catalog._tour_day_text` (internal, not granted): parses "Day N — Title\nBody".
- `catalog.v_tour_day`: day_number, title, body, places[] (from v_tour_place).
- **`catalog.v_tour_place`**: per tour/day, from active atoms + `atom_place_card` + `place_card`
  (rejected excluded): place_name, place_card_id, display_name, locality, region, country,
  **destination_id/name/lat/lng by name+country match to `shared.destinations`**, activity_types[],
  atom_count, `position` = first mention in day text. → This is already the read contract AA-712 should
  fill: once CIS links cards to destinations by id, swap the name-match LATERAL for the FK (needs the
  "catalog_owner dance" for any later view change — see 225 header).
- `catalog.v_tour_photo`, `v_destination`, `v_destination_photo` (wrap `shared.v_*_photos`).
- Contract JSON: `AA-Ecosys/docs/contracts/catalog.tour.v1.json`; add columns freely, rename/remove = v2.
- `catalog_owner` has SELECT only on: published_tours, raw_tours, tour_atoms, place_card, atom_place_card,
  destinations, v_tour_photos, v_destination_photos. A new table used by a catalog view must be granted
  to it in the migration.

---

## 7. Photo matching (AA-708)

- Job `photo_sync` (`services/jobs/photo_sync_job.py`, cap 1): Drive (CON PHOTOS folders, API key secret
  `aa-cis/dev/gdrive-photo-reader`) → S3 `photos/<country>/<file id>-{1600,600}.webp` → `shared.place_photo`
  (tour_id, destination_id, place_label, match_source auto/manual, status matched/unmatched/…).
- Matching (`services/photos/match.py`, pure): `match_tour(folder, tours)` (title ratio ≥ 0.85 / token share)
  and `match_destination(label, destinations)` (exact or longest whole-word name inside the label).
- **Destination candidates come from TripPlanner tables**: `services/photos/sync.py::itinerary_places()`
  (line ~95) reads `tripplanner.itinerary_components UNION tripplanner.tour_stop` JOIN `shared.destinations`
  — only places on that tour's own itinerary. `match_destinations` is off by default; `fill_destination_covers()`
  writes `shared.destinations.cover_image_url` (only empty or self-set). This is the direct consumer AA-712
  must re-point to the CIS-owned place output (e.g. `catalog.v_tour_place.destination_id` or the new table).
- Views (migration 200): `shared.v_tour_photos` / `shared.v_destination_photos` (status matched, s3 present,
  position 1 = cover; manual first). Keyed by **tour_id** → photos of a re-uploaded tour need re-matching
  (same identity issue as §5). Admin page `/admin/photos` (`api/routers/admin_photos.py`: summary, folders,
  tour-coverage, destinations picker, sync enqueue, manual assign).

---

## 8. Constraints that bind AA-712 (from CONTEXT.md / ADRs)

- ADR 0002: only CIS writes `shared.destinations`, itinerary places, tour graph; TP `SELECT` only (CIS 201);
  TP writers frozen until CIS ships; Mapbox key moves to CIS secrets; place pipeline = CIS job kinds run
  after A3 atomize per rerun wave; observable on an admin page.
- ADR 0003: no in-request work; enqueue with idempotency key; stage registry pattern (`services/recompute/`:
  `run(ctx, scope)` declaring reads/writes/`write_strategy`); readers never see a partial set — use a
  versioned swap / current pointer (the `route.superseded_at` model) if components are rebuilt per tour
  (TP's DELETE+INSERT in one transaction is acceptable per tour, not platform-wide).
- Schema ownership: new tables in a CIS schema (e.g. `acp_shared.*` or `shared.*`), migration in
  `api/migrations/` + byte-identical copy in `AA-CIS-Infra/db/migrations/cis/`, applied by DB Migrate before
  the code merges. `tripplanner.*` tables are TP-owned — CIS must not migrate them; the TP-read contract
  should be a catalog view, and TP's `itinerary_components` (with embeddings, used by search) becomes a TP
  derived cache rebuilt from the view, or is replaced.
- Paid-run rule: trial ~3 tours, then ≤ ~50; never the whole catalog unasked.
- Deploy gate: CI blocks backend deploys while `shared.job` has queued/running jobs.
