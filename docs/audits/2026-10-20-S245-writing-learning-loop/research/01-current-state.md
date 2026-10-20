# What CIS already has for a writing-learning loop (tour + social), as of 20/10/2026

Scope: read-only. Read `apps/AA-CIS-App` at `origin/main` 5486a0ee, `docs/architecture/db-schema-reference.md`
(verified 2026-10-20 01:02 UTC; row counts are `reltuples` estimates, and "ins" means inserts from the *Table activity*
section) and Linear (accessed 20/10/2026). No DB query. Where a number is not in the dump, it says "unknown".

## TL;DR

1. **There is already a "learn from mistakes" mechanism for A1/S1, and it does not work.** `shared.pipeline_lessons`
   is written as `stage='audit'` but read as `stage IN ('S1_rewrite','S1_editor')`. The write call also most likely
   fails silently. The dump shows 0 inserts and 1,956 index scans (reads only).
2. **The "N8 Deliver & Learn" flywheel was removed (AA-603).** The "every mistake becomes a permanent rule" module was
   `h3_rule_extractor.py`, which turned HITL rejections into `acp_output_rules` rows. It now exists only in old
   worktrees. `acp_output_rules` and `/v1/rules` are still live, but no live writer calls `apply_output_rules()`.
   `rule_adapter.py` is imported nowhere.
3. **The best human signal today is the admin sentence edits.** T9 pieces and T2 versions edited from the Content
   Quality page are saved in `acp_shared.audit_log` with before/after text, gate, problem, the model's suggestion and
   the mode (cut / accepted rewrite / own text). How many rows there are is unknown.
4. **Three places where a human edits but the original or the reason is lost:**
   - A1 admin field edit: `generated_content.edit_diff` holds only field names, and the text is overwritten.
   - Tenant edit on My Content (T9): the audit row holds only `content_length`, and `content_text` is overwritten.
   - Every approve/reject (A1 Review Queue, T2 tenant): no reason is stored.
5. **Labels and eval are mostly still planned.** `content_piece_label` has 1 insert. The 40-piece label pack exists but
   is not labelled (AA-783). The golden set (AA-729) is Backlog. `decision_log.outcome` is "still empty in practice"
   (AA-845). `prompt_eval_runs` has 0 inserts.

## 1. Writers

| Writer | Code | Output table | Before/after kept |
|---|---|---|---|
| **A1/S1 Master rewrite** (LangGraph: validate → judge → brand_audit → grounding → flag_fix → revalidate) | `services/content_generation/graph.py`, `flag_fix_node.py`, `grounding.py`, `brand_audit_node.py`, batch `s1_batch.py` | `silver_aa_internal.generated_content` (~1,423), `quality_scores` (~1,432) | Regenerate makes a new `version_num` (UNIQUE `tour_id, version_num`), so versions can be diffed. A human edit overwrites in place (§4). |
| **T2 tenant tour rewrite** (tenant voice, AA-792) + T3 QA | `services/jobs/t2_rewrite_job.py` (brand pack incl. `voice_examples` / `good_examples` at L98–99), `services/acp_produce/tenant_pipeline.py` | `gold_aa_internal.tenant_tour_versions` (~48; `qa_status`, `qa_repair_count`, `edit_source ∈ ai_generated / tenant_edit / re_rewrite`, `parent_version_id`) | Yes for tenant edits: each edit is a new row linked by `parent_version_id`. |
| **T8 angles** (3 options, one recommended) | `services/acp_angle_gate/service.py` | `acp_shared.angle_gate_request` (~21), `angle_gate_option` (~57; `recommended`, `chosen`) | n/a |
| **T9 blog / social pieces** (3 attempts; attempt 3 is a sentence repair only) | `services/acp_content_writing/service.py`, `quality_gates.py`, `sentence_repair.py`, `hygiene.py`, `trip_facts.py`, `text_integrity.py` | `acp_shared.content_piece` (~251; 258 ins). Columns `gate_ledger`, `repair_log[]` (AA-791), `discarded_attempts` (reverted attempt's full text + ledger, service.py L1733–1736, L1816–1819), `writer_input`, `flags` | Writer-side yes, through `discarded_attempts`. A tenant edit overwrites in place. |
| **T11 publish** | publish router + `publish_log` | `acp_shared.publish_log` (4 ins) | n/a |

Brand input shared by T2/T8/T9: `render_brand_block()` in `services/acp_shared/brand_pack.py` L107. It passes the style
guide, `forbidden_words` and `good_examples` as voice-only few-shot (L135–137).

## 2. Quality gates and repair loops

- **A1.** `validate_node` codes, plus `brand_audit_node` (GPT-4.1 strict schema) returning `failure_codes`, `issues`,
  5 binary scores and **`lessons_extracted[]`** `{pattern, failure_code, field, example_before, severity}`
  (brand_audit_node.py ~L150–190), stored in `quality_scores` (`brand_audit_status/codes/issues/fields`,
  `lessons_extracted`). Grounding repairs one sentence at a time against the source; Jev `a1_claim_supported` runs per
  sentence (grounding.py ~L456–496). `flag_fix_node` repairs only flagged fields. Scores below 7.0, or `manual_check`,
  go to `silver_aa_internal.review_queue` (~229).
- **T10 gate codes.** F0_complete, F1_grounding, F2_banned_patterns, F2_brand_forbidden, F3_structural_variance,
  F4_extreme_length, F4_seo_surface, F5_atom_density, F6_cta_present, F7_faq_*, F8_framework, F9_brand_style,
  F9_brand_voice, F9_cta_fact, F9_sticky_pass*, F10_cannibalization_cross_tenant, F11_brand_name, F12_scope,
  F13_autofix / final_pass / hygiene / leak / repeat, F14_first_line, F14_social_shape, F15_voice, F15_voice_warn,
  F16_faq, F17_trip_fact, F18_rarity, F19_authenticity. Descriptions: CONTEXT.md L1187–1266.
- **Repair / retry.** Up to 3 attempts; a full rewrite is told every blocking failure (`_repair_feedback`); a
  regression guard reverts a worse attempt; on the last attempt remaining truth failures are cut in code;
  `splice_checked` reverts repairs that leave a new repeat or orphaned pronoun; `new_specifics` refuses a repair that
  adds a number, time or pace word.
- **F9 sticky pass (AA-777, PR #761 merged).** Within one write job, a sentence F9 has passed stays passed while
  unchanged (CONTEXT.md L1249). AA-865 In Progress; PR #868 (OPEN) carries the pass through delete-only repairs.
- **Signature vocabulary (AA-800, In Progress).** Commit 56c67538 on `feat/tenant-signature-vocabulary` = PR #869,
  OPEN. Adds `services/acp_shared/signature_vocabulary.py`: `PLATFORM_TRUTH` (blocked for every tenant); AA style
  `STOCK_SUPERLATIVES` (cap 1 per piece for tenants) and `POSITIONING` words a tenant can declare; the tenant's own
  `forbidden_words` always win. Also a source-evidence rule for service-level claims.
- **Brand rules.** `shared.tenant_brand_rules` (`system_prompt`, `style_guide`, `forbidden_words`,
  `custom_validators`, `voice_examples`, `good_examples`, `version`, `is_active`; ~1 row by estimate, true count
  unknown, `shared.tenants` ~4). `tenant_brand_rule_versions` (0 ins). `debate_brand_fit_cache` (~375; `judge_score`,
  `brand_fit_score`, `feedback`).
- **Jev.** `shared.decision_question` (~5; `mode`, `accept_floor`, `reject_ceiling`, `threshold_version`,
  `calibration_ref`). `shared.decision_log` (~331,400; `outcome` jsonb for later human truth).

## 3. Existing "learn" mechanisms

| Mechanism | Tables | Data | Status |
|---|---|---|---|
| **A1 lessons loop (AA-132)**. Write: `flag_fix_node._write_lessons_safe` → `write_lessons_log` (L653–656, L677–757). Read: "LESSONS FROM PREVIOUS BATCHES" appended to the system prompt in `admin_pipeline.py` L560–583 and `s1_batch.py` L109–121 | `shared.pipeline_lessons` (`stage`, `field`, `pattern`, `why_it_matters`, `what_to_do`, `example_before`, `example_after`, `is_active`, `version`) | 24 kB, **0 ins, 1,956 index scans**. `quality_scores.lessons_extracted` holds raw LLM lessons per score (non-empty count unknown) | **Broken.** (a) writes `stage='audit'`, reader filters `S1_rewrite`/`S1_editor`. (b) `asyncio.get_event_loop().run_until_complete` from a graph run in `run_in_executor` (admin_pipeline.py L1086–1090) most likely raises and is swallowed (`lessons_writeback_failed`). (c) `what_to_do` is a template. (d) No human approval, no tenant scoping; T2/T9 never read it. |
| **N8 flywheel / H-3 rule extractor** | `acp_shared.acp_output_rules` (`tenant_id`, `stage`, `rule_type ∈ block/replace/truncate/flag/score_gate`, `pattern`, `source_type ∈ system/hitl_rejection/manual`, `source_hitl_id`, `confidence_score`, `run_count`) | 48 kB, 0 ins (seeded by mig 020) | **Dead.** Removed with N7/N8 (AA-603, CONTEXT.md L383). `api/services/acp_post_processor.py` called only from tests. `/v1/rules` mounted at `api/main.py` L245. |
| **Jev outcome loop (AA-756, PR #630)** | `decision_log.outcome` ({truth, source, ref, at}) via `shared/llm_client/decide.py` `record_outcome` L471 | Callers: review approve stamps truth=True per sentence (admin_pipeline.py L2669, L2688; grounding.py L501), admin atom delete (admin_atoms.py L534) | Per AA-845 "still empty in practice"; `/admin/decisions/outcomes/summary` returns 0. `record_rejected_outcome` never built. |
| **Prompt regression eval (AA-289)** | `shared.prompt_eval_runs` (pipeline ∈ `s1_old`, `s1_from_atom`) via `services/eval/regression.py` | 0 ins | Manual only. Fixture `CIS_Golden_Tours_20_v1.xlsx` in S3, not in repo. |
| Agent lessons (`skill/aa-lessons/lessons.md`) | file | n/a | For developer agents, not the runtime writer. |

## 4. Every place a human edit or decision is recorded

| Signal | Endpoint / code | Where saved | Before/after? | Reason? | Volume |
|---|---|---|---|---|---|
| Admin field edit of an A1 version | `PATCH /admin/tours/{tour_id}/generated/{content_id}` (admin_pipeline.py L3762–3819) | `generated_content`: `human_edited`, `reviewed_by`, `edited_at`, `edit_diff`, `revalidate_passed` (mig 072) | **No.** `edit_diff = {fields, reviewer_handle}`, text overwritten | No | Unknown |
| A1 Review Queue approve | `POST /v1/review-queue/{id}/approve` (v1_pipeline.py ~L470) | `review_queue.review_status/reviewed_at`; Jev truth=True per sentence | n/a | No | ~229 rows total |
| A1 Review Queue reject / dismiss / supersede | v1_pipeline.py L580; admin_pipeline.py ~L2724–2785 | `review_status` only | n/a | **No** (`reviewer_notes` only by an AA-716 script, admin.py L1831) | Unknown |
| Admin sentence apply, T9 piece | `POST /admin/content-quality/pieces/{id}/sentences/apply` (admin_content_quality.py L500–600) | `content_text` overwritten + `audit_log` `content_piece.admin_sentence_{cut,rewritten,edited}` | **Yes**: before, after, offsets, gate, problem, suggestion, suggestion_model, mode, lengths, published/exported, warnings (L586–593) | Indirect | audit_log ~1,324 rows across all actions |
| Admin sentence apply, T2 version (AA-802) | `POST /admin/content-quality/tour-versions/{id}/sentences/apply` (L1145–1225) | `rewritten_content` in place + `audit_log` `tenant_tour_version.admin_sentence_*` | **Yes**: sentence, section and whole content | Indirect | Unknown |
| Admin piece label (AA-791) | `POST /admin/content-quality/pieces/{id}/label` (L733–775) | `content_piece_label` (`label`, `defects`, `minutes_to_fix`, `reason`, `content_sha256`) | Hash only | **Yes** | **1 ins** |
| Tenant edit on My Content (T9) | `PATCH /v1/content-writing/pieces/{id}`; `update_piece_content_text`, service.py L2175–2220 | `content_text` overwritten + `audit_log` `content_piece.edited` | **No** (`{content_length}`) | No | Unknown |
| Tenant T2 inline edit | `PATCH /v1/tours/versions/{id}` action=edit (v1_tours.py L1084; insert ~L1066) | New `tenant_tour_versions` row, `edit_source='tenant_edit'`, `parent_version_id`, `edited_by_user` | **Yes** by diffing against parent | No | Of ~48; count in Tenant 360 (`admin_tenant360.py` L129–135) |
| Tenant T2 approve / reject | same endpoint | `status` UPDATE; no audit row with the flag on (~L1046) | n/a | No | Unknown |
| Angle pick (T8) | `angle_gate_option.chosen` vs `recommended` | same row | n/a; options keep `why_it_works`, `formula_fit`, `violations` | No | ~57 / ~21 |
| Slate subject pick / cut | `slate.py` L869–899; audit `slate.subject_picked` | `acp_shared.subject.state`, `cleared_bar_reason`, `score` | n/a | No | ~342 |
| Publish / unpublish / export | publish router; audit `content_piece.published/unpublished/exported` | `publish_log`, audit_log | Text as published | No | 4 ins |
| Admin regenerate angles | `POST /admin/content-quality/requests/{id}/regenerate-angles` | Clone + audit keeps old angles | Old angles | No | Unknown |
| Admin brand edits | `tenant.brand_updated` audit | audit_log | Yes | No | Unknown |

Tenant-isolation gaps:
- `audit_log`, `review_queue`, `content_piece_label`, `decision_log`, `tenant_brand_rule_versions` are cis_app-only,
  `tenant_id` filtered in code (dump L4456–4483).
- `content_piece` and `tenant_tour_versions` have RLS `tenant_isolation` for `aa_app_user`.
- Any learned per-tenant rule store needs the same RLS. A platform rule store must hold no tenant text
  (`acp_output_rules.tenant_id` is nullable today and RLS covers cis_app only).

## 5. Golden set and eval work

| Issue | Status (20/10/2026) | What exists |
|---|---|---|
| AA-729 golden set ~100 samples + scoring script (`stage="adhoc_aa729"`) | Backlog (S247) | Nothing committed; older 20-tour S1 fixture in S3 only |
| AA-787 gate consolidation (27 → ~18) | Backlog (S247) | S234 report 12 evidence |
| AA-783 40 pieces labelled by Nghiệp vs 4-lens AI panel | Backlog (S251) | `docs/audits/2026-10-13-S234-t-series-rounds/label-pack/` (xlsx + HUONG-DAN-CHAM.md); no labels yet |
| AA-791 per-attempt ledger + Label action + 30-piece fault set | **Done** | `repair_log[].gate_ledger`, `content_piece_label` (mig 231), `tests/unit/aa791_t9_fault_set.py` |
| AA-845 Jev A-axis ground truth (`record_rejected_outcome`) | Backlog (S247/S252) | Approve-side only; AA-803 shares labels |
| AA-865 F9 re-flag rate pooled n ≥ 60 | In Progress | PR #868 open |
| AA-800 signature vocabulary | In Progress | PR #869 open |

## 6. Reusable vs missing (evidence only)

- **Ready to mine:** `audit_log` admin_sentence_* rows; `discarded_attempts` + `repair_log`; T2 parent/child diffs;
  `angle_gate_option.chosen` vs `recommended`; `quality_scores.lessons_extracted` + `brand_audit_codes`;
  `decision_log` per-sentence Jev verdicts.
- **Missing capture:** before-text on A1 admin edit and T9 tenant edit; reason on every reject / cut / dismiss;
  rejected outcome for Jev; human labels beyond 1.
- **Injection point to repair or reuse:** "LESSONS FROM PREVIOUS BATCHES" (A1 only). T2/T9 have no lesson injection;
  their per-tenant levers are brand pack fields (`forbidden_words`, `good_examples`, `style_guide`), extended by AA-800
  once PR #869 merges.
