# AA-1049 fix-up of existing Masters: system-wide propagation map

S276, 10/11/2026. Read-only research (no AWS, no ECS exec, no DB). Built from three adversarially verified layer
reviews (A3 atom layer; tenant layer T0-T11; catalog views + other apps; operations and guards).
Code baselines: CIS `5cc016cde`, Infra `788addb`, TripPlanner `c3e10fd`, Partner `451e5011`, S1 train worktree `7197e24d4`.

Path prefixes: CIS = `apps/AA-CIS-App`, Infra = `infra/AA-CIS-Infra`, TP = `apps/AA-TripPlanner-Web`,
BK = `apps/AA-Booking/backend`, CRM = `apps/AA-Partner`. Row counts are from `docs/architecture/db-schema-reference.md`
(dump estimates), never from a live query: treat them as UNCONFIRMED.

The question: after the free AA-1049 replay lists the Masters whose current text differs, we can fix each one by

- **Path A**: a $0 code fix that recomposes only the fixed fields (day count, day headings, meals/overnight lines, meta,
  slug) and keeps the narrative; or
- **Path B**: a paid S1 rewrite (A1) that creates a new version through the normal path (review queue / auto-publish).

Is re-atomization (A3) needed, and what moves across the whole system?

---

## 0. Mechanics everything depends on

| # | Fact | Evidence |
|---|---|---|
| M1 | The only automatic A3 trigger is the enqueue inside `process_export`, run on S1 auto-publish, review approve, promote and the export Lambda. Manual atomize and job-runner Retry also enqueue, never on their own. | CIS services/export/handler.py:528, 657-679; admin_pipeline.py:1067, 3266; v1_pipeline.py:669; admin_atoms.py:638-648; admin_job_runner.py:260 |
| M2 | No code writes Master text in place. The only text write is the publish upsert (`ON CONFLICT (tour_id) DO UPDATE … updated_at = NOW()`), called only by `tour_lifecycle.publish`. Other UPDATEs touch status columns or `quality_score_id`. No trigger on `published_tours`. | CIS shared/repository/published_catalog_repository.py:16-50; services/tour_lifecycle/service.py:234-648, 662-684; admin_pipeline.py:1424-1429; db-schema-reference.md:8739-8781 |
| M3 | A3 dedupe key `a3_atomize:<version_id>`; `ON CONFLICT DO NOTHING` returns the old job. The key stays spent while the job row exists (retention deletes succeeded rows after 30 d, failed after 90 d; whether retention runs live on Dev is UNCONFIRMED). | CIS services/jobs/a3_atomize_job.py:72-74; shared/jobs/queue.py:72-87; services/retention/policy.py:71-80 |
| M4 | Per-day skip: fingerprint = sha256(day title, day body, SYSTEM_PROMPT, model id), stored per (version, day). A new version has no fingerprint rows, so every day is re-read. Preamble not hashed. | CIS services/acp_shared/atom_extraction.py:274-281; services/acp_contract/a3_atomize.py:440-465 |
| M5 | **Legacy path**: if `parse_canonical_itinerary_days()` returns `{}` (text not in `Day N — Title` form) A3 atomizes the whole tour, skip key = hash of the WHOLE prompt (incl. TOUR, SUMMARY, HIGHLIGHTS), random atom ids, then soft-deletes every earlier atom. Wave flag `legacy_itinerary_path`. | a3_atomize.py:234-238, 284-373; atom_extraction.py:112-148; services/waves/quality.py:243-246 |
| M6 | Atom id = sha256(scope, tour, day, norm(place), norm(action))[:16] — not a text hash. A day renumber changes every id on shifted days. Atoms not reproduced on a re-read day are soft-deleted; orphan days (past new day count) are retired even when every day is skipped. | atom_extraction.py:159-185; a3_atomize.py:254-281, 467-478, 527-536, 565-569 |
| M7 | Ranged headings (`Day 12-15 — …`) give every covered day the block's title and body, so heading wording or range-splitting changes alter the fingerprint of every affected day. | CIS services/content_generation/itinerary_utils.py:161-176 |
| M8 | A3 chain after atomize: segment match, brand-fit cache clear (all the tour's Segments and Routes through them), debounced platform recompute (Score/Route), place-card relink, `place_extract`. Steps other than the brand-fit clear run even when all days were skipped. | handler.py:273-416 (354-403); CIS CONTEXT.md:4349-4353 |
| M9 | A3 job: `concurrency=1, max_attempts=2, expected_seconds=1800`; observed throughput ~20-30 tours/h. | a3_atomize_job.py:99; S248 memo (docs/audits/2026-10-23-S248-aa645-writer-decision/platform-impact-memo.md):12, 41, 106 |
| M10 | A3 and re-export read `silver_aa_internal.generated_content`, not `published_tours`. | handler.py ~547-552, 659-664 |
| M11 | `process_export` order: upsert → (only if lifecycle events) `notify_tripplanner` + `fan_out_to_tenants` → pipeline_status → enqueue `a3_atomize` → `source_fanout` ($0) → dismiss pending reviews. An already-served tour produces no lifecycle event. | handler.py:616-695; service.py:309-316 |
| M12 | Catalog read model is plain views read live (no matview): `catalog.v_tour` (title, itinerary_text, slug, duration_days, content_hash, text_updated_at), `_tour_day_text` → `v_tour_day`, `v_tour_place`. But `v_tour_component`, `v_tour_day_route`, stops/legs read `geo.tour_place` / `geo.tour_day`, built by `place_extract` only. | Infra db/migrations/cis/359_catalog_tour_text_updated_at.sql:121-181; 289_catalog_ranged_day_heading.sql:134-165; 256_catalog_line_places.sql:126-149, 250-275; CIS api/migrations/253_catalog_l4_read_model.sql:340-358 |
| M13 | Heading parsers that must all accept the composed format: A3 `parse_canonical_itinerary_days`, SQL `_tour_day_text` (em dash only; `Day N —` / `Days N–M —`), `v_tour.duration_days` regex, TripPlanner `^\s*Day\s*(\d{1,2})\s*[:\-–—]` (does not match a `Days 3–4` range). | itinerary_utils.py:161-176; 289…sql:136-141; 359…sql:127-135; TP backend/assembly/master_content.py:51 |

---

## 1. Layer tables

### 1A. Path A — in-place fixed-field fix (no S1 call)

Three build variants exist; only the first is recommended (see §4):

- **A-new**: write the fixed text as a NEW approved `generated_content` version and publish it via `process_export`
  (all wiring automatic).
- **A-inplace**: UPDATE `generated_content` + `published_tours` on the same version, then fire A3 / fan-out by hand.
- **A-silent**: a bare UPDATE of `published_tours` (precedent: CIS scripts/backfill_aa314_double_encoded_jsonb.py:133-137).

| Layer | What happens | Automatic? | Cost / tour | Risk |
|---|---|---|---|---|
| Master text (`published_tours.aa_*`) | A-new: upsert, `updated_at` bumped. A-inplace/A-silent: new code writes columns; `updated_at` moves only if the code sets it (M2). | A-new yes; others need new code (none exists; S276 worktree has only replay + read-only export, CIS scripts/quality/export_aa1049_s1.py:89) | $0 | A-inplace/A-silent that skip `generated_content` are reverted by the next re-export or atomize (M10). |
| Version + audit (`generated_content`, `quality_scores`) | A-new: new row, before-text kept. Staff hand path today (PATCH generated + promote) overwrites the version and logs a writer-memory `human_edit`. | A-new yes | $0 | PATCH path pollutes writer memory (admin_pipeline.py:4264-4285, 4345, 4361) and loses the before-text. |
| Catalog text views (`v_tour`, `v_tour_day`, `v_tour_place` text) | Re-parse live at next query; `content_hash` moves; slug moves only if `aa_name` moves (308 on old slug). | Yes, every variant | $0 | Composed headings outside canonical form drop day rows / change `duration_days` (M13). |
| `text_updated_at` + AI marks (AA-1040) | Follow `updated_at`. | Only if `updated_at` bumped | $0 | A-silent leaves "generated_at" older than the text (ai_marking.py:169-182; 359…sql:15, 174-180). |
| A3 atoms (`acp_contract.tour_atoms`, `v_active_tour_atoms`) | A-new: full re-read (new version, no fingerprints). A-inplace: re-read only days whose title/body changed, needs new idempotency key (M3), cancel stale queued/failed rows that carry the OLD text in payload (a3_atomize_job.py:68-69). Legacy-format tours: full churn, random ids (M5). | A-new yes; A-inplace manual enqueue; A-silent never | ≈ $0.006 full re-read; ≈ proportional to changed days otherwise. Heading rewrite on every day ≈ full re-read | A-silent: atoms describe the OLD day numbering → `v_tour_place` places attach to wrong days. Day-count change without A3 leaves atoms on days past the new count. |
| Segments, brand-fit cache, platform recompute, place-card relink | Run in the A3 chain (M8). | With A3 | Segment match ≈ $0.00003; platform recompute ≈ $0.009 per debounced run (not per tour) | Brand-fit cache cleared for all the tour's Segments → T7 debate re-asks (lazy). |
| Atom embeddings | New atom ids embedded (Cohere acc2); same id with recased text keeps OLD vector. | With A3 | < $0.001 | Minor drift on recased atoms (atom_matching.py:189-230). |
| Geo (`geo.tour_day`, `geo.tour_place`) → `v_tour_component`, `v_tour_day_route`, stops/legs, catalog.http facets | `days_hash` = sha256(RULE_VERSION ‖ aa_itineraries) changes on any byte; rules rebuild; model `a3_place_days` only when a non-last day has no findable overnight. Enqueued by A3 chain (`after_atomize`, `PLACE_PIPELINE_AUTO=on`) or `POST /admin/places/backfill` (≤50 live / ≤100 listed). | With A3 or admin backfill; A-silent never | $0 typical; model fallback rare (composed "Overnight in X" lines should reduce it — UNCONFIRMED) | Without rebuild: map stops, legs, overnight anchors, facets stay on OLD text; TripPlanner narration maps stops to wrong day (TP master_content.py:84, 177-205). Component ids (uuid5 with day_index, name) may change → saved stops show `stop_removed` (PLAUSIBLE). |
| `source_fanout` marks (`shared.source_change_mark`) | Marks each tenant's newest non-rejected T2 version and approved/held T9 pieces citing the tour's atoms. | A-new yes; others only if code calls `enqueue_safe` | $0 | Atomize soft-delete is NOT an atom fan-out source (source_fanout.py:16-18): skipping the master fan-out leaves T9 pieces on replaced atoms unflagged. |
| T2 tenant versions | Never rewritten. `master_newer` badge on every version older than `updated_at`. New DOCX/CSV export, version drawer, pool, `/full`, trip page read live Master for missing fields. | Badge only if `updated_at` bumped; live readers always | $0 (Request Rewrite = tenant quota, ≈ $0.078/version) | Every T2 version of a fixed tour shows "Master changed" at once; in-flight T2 that already read the new text is falsely marked (source_fanout.py:77, 179). |
| T7 Slate / T8 angle requests | `retarget` (default `apply`) repoints/reseeds requests on replaced atoms; rows with no unique target → 409 `atom_replaced`. | With A3 | $0 (reseed ≈ $0.02/request if tenant re-runs) | Partner wizard shows `atom_replaced` on unmatched requests (AngleGateWizard.tsx:145-150). |
| T9 pieces / T11 live posts | Never regenerated; live WordPress/Facebook posts never updated (no update adapter). | — | $0 | Delivered content keeps old day facts by design. |
| AA-hosted trip page `/v1/trip/{id}` | Reads `aa_*`, `seo_title`, `seo_meta` live. | Yes | $0 | None (only reader of composed meta). |
| TripPlanner (browse Lambda, ISR, narration) | Text after ≤30 min (CDN TTL / `revalidate = 1800`); no purge (purge only on lifecycle events). Narration cache 168 h. | Yes (text); geo-backed routes/tiles need geo rebuild | $0 (missing narration day → one model call) | Heading format must match TP parser (M13). |
| Booking | `cis_readback` flags changed day titles on draft trip-case items ("Refresh from CIS"); `trip_plan_components.day_no` not checked against new day count; frozen `inquiry_snapshot` never follows. | Yes (readback is live) | $0 | Staff prompts on every draft built from a tour whose headings changed; possible components past new day count (UNCONFIRMED count). |
| CRM catalog cache (`crm.aa_catalog_tour`) | Hourly pass on `content_hash`, ≤100 details/run → ~9 runs if ~892 tours change. Options read only served state. | Yes | $0 | ≤ ~9 h lag. |
| AA-991 Freshness Probe | `atoms_older_than_master` red after 24 h if `updated_at` bumped but no ACTIVE atom updated (meta-only fix → all days skipped → red even WITH re-atomize). `geo_tour_place_stale_rows` red until place_extract rebuilds. | Probe nightly 05:13 UTC, ENFORCE | — | Main operational trap for A-inplace. |
| AA-986 liveness gate, AA-1039 retire fan-out | Not triggered (lifecycle events only). | — | $0 | None. |

### 1B. Path B — paid S1 rewrite (new version through review / auto-publish)

| Layer | What happens | Automatic? | Cost / tour | Risk |
|---|---|---|---|---|
| S1 rewrite (A1) | New `generated_content` + `quality_scores`; judge, flag-fix, grounding. Tour in review queue keeps OLD Master until approve. | Yes | $0.0709 measured (S249: generate 0.0600, judge 0.0055, flag-fix 0.0029, grounding 0.0025); model cap $0.12 | Narrative changes too (not only fixed fields) → new review risk, source fidelity re-check; acc3/OpenAI spend is real money. |
| Review / wave states | `review_queue` entry or auto-publish; wave report states and stop flags. | Yes | $0 | `not_clearly_better` stop flag fires by construction on a fix wave over v2 Masters (quality.py:203-204, 250) — needs an agreed fix-wave rule or written tech-lead override (skill aa-wave-rerun SKILL.md:86-90). |
| Master upsert, `updated_at`, catalog views, AI marks | As A-new. | Yes | $0 | Slug 308 if name changes (S249: 50/50). |
| A3 atoms | Full re-read of every day (new version). | Yes | ≈ $0.0059 measured (gpt-6-luna 0.0052 + Jev in-text 0.0006) | Atom ids change only where day/place/action change; T8 retarget handles the rest. |
| Segments / recompute / place cards / embeddings | A3 chain. | Yes | Segment match ≈ $0.00003 measured; Segment-level Jev ≈ $0.001-0.003 (S248 est.); recompute ≈ $0.009 per debounced run; embeddings < $0.001; place cards < $0.001 | Brand-fit cache cleared per Segment. |
| Geo / place_extract | `after_atomize`, `PLACE_PIPELINE_AUTO=on`. | Yes | ≈ $0.008-0.025 per tour that has a geo build (S248 est. $1-3 for ~120 built tours); $0 when rules find every overnight | `geo_tour_place_stale_rows` red until the chain finishes. |
| `source_fanout`, T2 badge, T7/T8/T9/T11 | As A-new. | Yes | $0 platform; tenant re-runs are tenant-paid via quota | Same tenant signals as A-new. |
| TripPlanner, Booking, CRM, trip page | As A. | Yes | $0 | As A. |
| AA-991 | Red if a batch does not drain within 24 h (serial A3, 20-30 tours/h). | Probe | — | Batch ≤ ~480-720 tours per 24 h. |
| Deploy / DB Migrate guards | Blocked while the wave is open and while `shared.job` has queued A3/recompute jobs. | Yes | — | Long A3 tail blocks migrations (SKILL.md:44-45). |

---

## 2. Is re-atomization needed?

**Path A — it depends on what changed (classify every replay diff):**

| Change type | A3 needed? | Geo rebuild needed? | Cost / tour |
|---|---|---|---|
| Wording outside headings/meals/overnight; tour name; `seo_title`/`seo_meta`; summary | No (canonical tours: fingerprint excludes them). Do NOT enqueue on legacy-format tours: their skip key includes TOUR/SUMMARY/HIGHLIGHTS → full churn with random ids (M5). Do NOT bump `updated_at` without an atom touch (probe red). | No | $0 |
| Day headings, meals/overnight lines (day text) | Yes — those days are re-read (M4, M7). Normalizing headings across a tour ≈ full re-read. | Yes (`days_hash` moves) | ≈ $0.006 |
| Day count or day boundaries | Yes — new days read, orphan days retired (M6). | Yes | ≈ $0.006 |
| Any change on a legacy-format Master | Yes, full re-read with new random ids (breaks T8/T9 lineage) — or skip these tours. | Yes | ≈ $0.006 + lineage churn |

In practice, because AA-1049 composes headings and meals/overnight lines, most differing tours will be in rows 2-3, so
path A costs about one full A3 per tour (≈ $0.006) and needs `place_extract` too. The atomize cost is the same whichever A variant
is used; A-inplace only saves money when few days change.

**Path B — always, automatically.** New version id → every day re-read (≈ $0.006/tour) + the full A3 chain.

Note: if the `a3_atomize` route `model_id` changed since the last atomize, every day re-reads anyway (fingerprint
includes the model, a3_atomize.py:445, 463). Live value UNCONFIRMED.

---

## 3. Cost formula for N tours on path B

```
Cost_B(N) = N × (c_S1 + c_A3 + c_seg + c_emb)
          + N_geo × c_place
          + R × c_recompute
          + 0   (tenant layer: nothing re-runs automatically; T2/T9 re-runs are tenant clicks paid from tenant quota)

c_S1        = 0.0709 USD measured (S249 README:66-75), cap 0.12
c_A3        = 0.0059 USD measured (gpt-6-luna 0.2606 + Jev 0.0324 per 50 tours); worst case all-Haiku ≈ 0.046 (S248 memo:86)
c_seg       ≈ 0.00003 measured match + ≈ 0.001-0.003 Segment-level Jev (S248 memo:88, estimate)
c_emb       < 0.001 (S248 memo:89)
c_place     ≈ 0.008-0.025 per tour with a geo build (S248 memo:91, estimate; model only on missed overnight)
c_recompute ≈ 0.009 per debounced platform run (backlog README:470); R = number of runs, small
```

Point estimate (measured rates): **≈ 0.077 USD/tour + ≈ 0.01-0.025 per geo-built tour.**
For N = 892 (UNCONFIRMED count): ≈ 69 USD + places 3-21 USD + a few USD recompute/Segment ≈ **75-95 USD**, in line with
the S248 clean-run estimate of ~85 USD (70-160) (S248 memo:95). Worst case (S1 at cap, A3 on Haiku): ≈ 0.19 USD/tour ≈ 170 USD.
S1 runs on Sonnet (acc3 or the interim OpenAI/acc2 route) — acc3 is now billed to us (AWS Lift credit, then card).

Path A for comparison: N × c_A3 + N_geo × c_place ≈ **0.006-0.03 USD/tour** (≈ 5-27 USD for 892 tours).

---

## 4. Recommended procedure

1. **Replay (free) and classify.** For each differing Master record: change type (§2 table), canonical vs legacy
   format, day-count delta, name change (slug 308). Filter to `master_status = 'active' AND deleted_at IS NULL` with a
   live source (`published_tours` ~1,070 rows vs ~892 served). Exclude the 54 golden-fixture and 39 elephant-riding tours
   that stay on v1 by policy (docs/backlog/README.md:652).
2. **Heading-format gate before any write.** Add a test that every composed heading parses identically in
   `parse_canonical_itinerary_days`, SQL `_tour_day_text` (em dash), `v_tour.duration_days`, and TripPlanner
   `master_content.py:51` (no `Days N–M` ranges unless TP's parser is extended). Otherwise A3 falls to the legacy path
   and TripPlanner/Booking lose day rows.
3. **Route by class.**
   - Narrative/source-fidelity problems → **Path B**.
   - Fixed-field-only diffs → **Path A-new**: a dedicated code path that inserts a new approved `generated_content`
     version (edit source "code fix", actor system, not PATCH, so writer memory is not polluted) and publishes through
     `process_export`. This brings A3, geo, fan-out, marks, badges and probe consistency for free; atomize cost equals path B's A3
     (≈ 0.006/tour) with no S1 call.
   - Wording/meta-only diffs on canonical tours → Path A-new too (A3 skips nothing on a new version, so it costs ≈ 0.006),
     or, to save the A3 cost, an A-inplace write to BOTH tables WITHOUT bumping `updated_at` and without enqueue. Decide
     this deliberately: it leaves AI marks / `text_updated_at` older than the text and shows tenants nothing.
   - Legacy-format tours: Path B (or A-new after re-composing into canonical form), never A-inplace.
4. **Waves** (skill aa-wave-rerun): wave object with expected set; RDS snapshot per wave; ladder 3 → ≤50 → per country;
   batch so each wave's A3 tail drains within 24 h (≤ ~480-720 tours at 20-30/h, concurrency 1). Agree the fix-wave stop
   rule for `not_clearly_better` and the `unclassified = 0` vs stayed-old conflict before the first wave. Paid runs
   need an explicit $ cap from the tech lead (B: ~0.08-0.10/tour).
5. **Watch per wave:** wave report flags `legacy_itinerary_path`, `atoms_on_days_past_new_count` (must be 0),
   cost/tour vs model; AA-991 `atoms_older_than_master`, `geo_tour_place_stale_rows`, `place_card_links_missing`
   (stale), `tenant_versions_older_than_master` and `angle_gate_requests_on_inactive_atoms` (info); `shared.job` idle
   before any deploy or DB Migrate; spend from `tools/llm/spend_by_stage.py`.
6. **Downstream spot checks after each wave:** TripPlanner tour page after 30 min (and 308 on renamed tours); one
   Booking draft trip case on a fixed tour (`cis_readback` "changed"); CRM catalog after the hourly passes; one T8
   request on a replaced atom (repointed or 409).
7. **Tenant content rule (unchanged):** never overwrite T2/T9/T11. Tenants are informed by the `master_newer` badge and
   `source_change_mark`; they choose Request Rewrite (their quota). Delivered files and live posts never change; new
   DOCX/CSV exports pick up the live Master for fields the version lacks. Optional targeted recheck:
   `POST /admin/quality/lineage/fanout/{tour_id}/recheck` (dry run by default, admin_quality_lineage.py:83-94).

---

## 5. Open questions

1. Exact number of served Masters, and how many are legacy (non-canonical) format — needs a DB count.
2. Live `a3_atomize` `model_id` in `shared.llm_role_config`; a change since the last atomize means full re-read anyway.
3. Does `process_export` accept a code-made version (A-new) without S1 artefacts (quality_scores, judge)? Which
   `edit_source` / review status should it carry, and does it count as `human_edited`?
4. Is the AA-1040 mark allowed to say "fixed by code" (contract `catalog.http.v1` 1.3 change) or stay `model: None`?
5. Does `retention_job` run live on Dev (frees spent A3 dedupe keys after 30/90 days)?
6. What AA-1049 means by "slug": the only slug is `catalog.v_tour.slug` from `aa_name` + country + source prefix.
7. Atom id stability across an LLM re-read (how many T8 requests end in 409 `atom_replaced`).
8. Days per tour (~11 inferred from 9,800 calls / 892) and real A3 duration per tour on today's routes.
9. Today's S1 and A3 cost per tour on the current route chain (S249 rates are from 24/10, Sonnet on acc3).
10. Booking `trip_plan_components` rows with `day_no` past a tour's new day count after a day-count fix.
11. Are any tenants real (decides how much the T2 badge burst matters).
12. Whether `published_tours.content_embedding` is populated (no writer stage registered; no re-embed on either path).
