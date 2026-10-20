# Measurement design for a writing learning loop: CIS (A1/S1) and tenant portal (T2, T9/T11)

Research date 20/10/2026. Read-only: no DB queries, no LLM calls, no writes. Code read at AA-CIS-App `origin/main`
5486a0ee. Schema from `docs/architecture/db-schema-reference.md` (dump 2026-10-20 01:02 UTC).

Two inputs read from other worktrees: the AA-865 audit (merged as root PR #125, now at
`docs/audits/2026-10-20-S245-f9-pooled/README.md`) and the AA-729 memo (unmerged, branch
`docs/tenant-crm-research-and-m2a-memos`, `docs/audits/2026-10-20-S245-m2a-decisions/README.md`).

## 0. Bottom line

1. **The metrics that grade the writer already exist; the labels that would let it learn do not.** S1 review queue:
   196 rows since 01/10 and 0 human decisions (S218). S1 approvals: `approved_versions = 0` because reviewers press
   Regenerate (S228 Part 6). Tenant T9 edits overwrite text and log only length. Admin S1 field edits log field names only.
2. **Three tiers of measurement:** $0 offline replay on frozen inputs (AA-865 pattern); judge-only re-score of frozen
   outputs; capped paid generate-and-score on the AA-729 golden set (~$8.6–10.4 for 100 samples). Live Dev traffic is
   too small to A/B (natural T9 traffic after r7 was one retry); live use is shadow and a guarded canary only.
3. **One rule overrides the rest:** a learned rule that adds even one real B-class fault (a promise the source lacks) on
   the golden fact subset is rolled back — the logic AA-865 used to reject fix (b) over case #13 (overnight → lunch stop).

## 1. Inventory

| Signal | Where | Covers | Status |
|---|---|---|---|
| Per-gate runs/fails/blocking fails by channel | `GET /admin/content-quality/stats` (admin_content_quality.py:777-816), from `gate_ledger` | T9 | Live; counts use `gate_ledger`, never `held_reason` (S232) |
| Per-tenant outcomes + LLM cost per piece | same route, `cost_usd` from `llm_call_log` by `job_id` | T9 | Live |
| Re-flag rate | AA-865 §4, §7; `s245_f9_pool.py`, `s245_f9_counterfactual.py` | T9 | Ad hoc. 8/75 = 10.7% [5.5, 19.7]; fix (a) 5/75 = 6.7% [2.9, 14.7]; target ≤ 8% |
| Failure classes C1/C2/C3 | AA-865 §5 | T9 | C1 real new fault; C2 F9 re-judging a passed sentence; C3 quote spanning two sentences |
| F9 brand voice judge, prompt `f9_v1.1` | quality_gates.py:180-188, ledger :1220 | T9 | Only the judge has a version stamp |
| Brand-fit judge | `brand_fit.py`; `debate_brand_fit_cache` | T2, Slate | Live; temp 0.1, seed 42; Luna median-of-repeats (AA-714) |
| `quality_scores` | ~1432 rows | S1/A1 | 0 Masters < 7; 94% reach Master alone; ~$0.114 per Master (S218) |
| T2 version QA | `tenant_tour_versions` (~48) | T2 | Tenant edits create a child via `parent_version_id` (v1_tours.py:1067-1076, 1085-1140) |
| Human label per T9 piece | `content_piece_label`, mig 231; `PieceLabel.tsx` | T9 | Built (AA-791); AA-783 waits on labelling |
| Admin sentence edits | `audit_log` `content_piece.admin_sentence_*`, `tenant_tour_version.admin_sentence_*` | T9, T2 | Live, append-only, hash-chained; best edit-pair source |
| Jev decisions + outcomes | `decision_log` (~331k), `decision_question` (CHECK: calibration before enforce), `record_outcome()` decide.py:456-480 | A1 | No sentence-level truth source yet |
| Model shadow | `llm_role_config.shadow_model_id/shadow_sample_pct` → `llm_shadow_log` (~5.5k) | Any | Model-level only; no prompt/rule variant shadow |
| Prompt regression harness | `services/eval/regression.py` → `prompt_eval_runs` | S1 only | CHECK allows only `s1_old`/`s1_from_atom` |
| S1 prompt version | `generated_content.metadata.prompt_version` (sha256[:8]; batch_prompt.py:234-237) | S1 | Opaque hash |
| Cost | `llm_call_log` | All | S1 $0.048–0.06/tour; T9 blog $0.094–0.104; LinkedIn ~$0.057; T2 $0.38 before AA-792 (now unknown) |
| Panel rounds | S234 r1–r4, S235 r5 | T9 | "Light edit or better" 55% → 70% (target ≥ 60%); $1.03 per 20 pieces |

Legacy learning in code (unmeasured): `shared.pipeline_lessons` (live, ungated prompt mutation; no A/B, no rollback, no
attribution); `acp_shared.acp_output_rules` (legacy, no caller on T2/T9).

## 2. Capture gaps

| # | Gap | Fix |
|---|---|---|
| G1 | Tenant T9 edit overwrites `content_text`, logs `{content_length}` only (service.py ~2175-2193) | Store before/after admin-side, tenant-scoped |
| G2 | Admin S1 field edit logs `{fields, reviewer_handle}` only (admin_pipeline.py:3794-3812) | Keep before/after per field |
| G3 | S1 review queue yields no decisions; reviewers regenerate | Count regenerate as implicit reject; add reason chips |
| G4 | Only one discarded T9 attempt kept | Persist every attempt's text + ledger |
| G5 | No T9/T2 writer prompt version stamp | Stamp `writer_prompt_version` + `rule_set_version` in `writer_input` / T2 / `llm_call_log.quality_signal` |
| G6 | No experiment/variant flag | `experiment_id` / `variant` in `quality_signal` (no migration) |
| G7 | `pipeline_lessons` mutates S1 prompts ungated | Freeze, or route through §5 |

## 3. Metric set

- **Primary quality:** light-edit-or-better share (labels or AI-panel majority; target ≥ 60%, last 70%); `minutes_to_fix`
  median/p90; implicit human edit rate (T2 `tenant_edit` share; T9 edit events after G1; S1 regenerates after G3); edit
  distance.
- **Fidelity guardrail (zero tolerance):** B-class faults per 100 on golden fact subset; C1 count; online proxy F1 /
  F17 / F9_cta_fact blocking-fail rate.
- **Loop health:** re-flag rate (n ≥ 60, Wilson 95%, ≤ 8%); gate approval/precision vs labels (S234 r4 55% / 73%);
  judge stability (20 texts × 3 re-judges ≈ $0.30).
- **Brand:** F9 `brand_fit` pass rate, `brand_fit_score`, T2 `quality_score`, per tenant; `cross_brand_distinct`; F10
  similarity ≥ 0.92 stays 0.
- **Cost:** `cost_usd` per piece by stage; repair spend share.

## 4. Golden sets

Basis: AA-729 option (a): 100 samples (50 S1, 10 T2, 15 T9 blog, 15 T9 LinkedIn, 10 prompt-injection); regenerate+score
and score-only modes; labels from review results, Ms. Thư feedback, audit conclusions, AI panel where unlabelled with
Nghiệp checking disagreements; versioned fixture, no PII; `stage="adhoc_aa729"`; ~$8.6–10.4/run, cap $15; decision
pending ("a / có / có"), slotted S247.

Additions for the learning loop: (1) strata per writer/channel (fact-dense vs thin, tours ≥ 9 days, OFFERED/optional
items, named-place background) with known traps (Tsaatan access, "near Mörön", AA-865 #13); (2) edit-pair subset from
`audit_log` sentence actions and T2 parent/child diffs, kept in their tenant partition; (3) ~30 synthetic fault-injection
pieces at $0; (4) ~30% holdout never used to write or tune a rule; (5) refresh trigger: bump the fixture version on
catalog / tenant mix / brand pack change and compare only on the same version.

Label source for sentence fidelity: AA-845 option (c) — ~100 grey-zone sentences labelled by an agent panel now, then a
per-sentence "unsupported" reviewer action. 100/100 gives a Wilson lower bound of ~96%.

## 5. Rollout: offline → shadow → canary → enforce

| Stage | What runs | Cost | Pass bar |
|---|---|---|---|
| R0 deterministic replay | Code-expressible rules replayed on stored ledgers/texts (`s245_f9_counterfactual.py`); current rule must reproduce observed numbers first | $0 | Rate improves on pooled set; 0 C1 waved through; unit pairs pass |
| R1 judge-only | Re-score frozen golden outputs + panel-labelled pieces | ~$1–2 | Precision/recall not worse; κ reported |
| R2 golden regenerate | Trial 3, then affected layer or full 100 | ≤ $15 | Paired before/after on same fixture version |
| R3 shadow | New "variant shadow" (today only model shadow exists) | sample % × unit cost | Same metrics on shadow pairs |
| R4 canary | Fraction of real pieces, stamped `variant`; Jev reuses `decision_question.mode` shadow → enforce | normal | Stop/rollback below |
| R5 enforce + monitor | Default on; old variant as a flag (AA-544, D-12) | — | Weekly review |

Paid runs: trial ~3 then ≤ ~50; no paid run while a backend PR is unmerged or jobs queued; waves need idle job tables
(DM-11.4). Dev traffic is synthetic (A&H, Terra, Trail Pulse, WildKind); R4 on Dev is effectively a fifth golden run.

## 6. Statistics and stop/rollback

Paired comparisons on the same fixture items (McNemar binary, Wilcoxon minutes/scores); pool across rounds; Wilson 95%.

Hard stops: (1) ≥ 1 new B-class or C1 on golden fact subset; online, variant's Wilson lower bound for F1/F17/F9_cta_fact
blocking-fail rate above baseline point estimate. (2) Any tenant-A-derived text in tenant-B output (n-gram vs tenant edit
corpus, F10 ≥ 0.92). (3) Any QA artefact in tenant-visible text.

Soft stops: re-flag > 8% pooled or +3 pts; light-edit-or-better −10 pts or < 60%; median `minutes_to_fix` +20% or tenant
edit rate up; cost per piece +20%; F9 test-retest drops.

Promotion: primary metric improves (or holds while cost falls), no stop, holds on holdout; recorded in
`prompt_eval_runs` (or successor once the CHECK covers T2/T9).

## 7. Per-tenant isolation

- Learned tenant rules only in tenant-scoped versioned stores (`tenant_brand_rules`, `tenant_brand_rule_versions`;
  `source_type` CHECK allows only `manual`/`docx_parse` → `learned` needs a migration).
- Promotion to platform only when the same defect shows up across ≥ N distinct tenants (proposed N ≥ 3, author's
  number), rewritten generically, through R0–R2.
- Report every metric per tenant and pooled.
- Edit-pair fixtures carry `tenant_id`; scored only against the same tenant.
- `audit_log.details` holds raw tenant text → mining runs admin-side, outputs aggregates or generic rules only.

## 8. The human side

- Reviewer capacity: no documented number. S235 AI-first audit: "review capacity is a budget", example 30 min/week per
  reviewer. AA-783 pack: 2–3 h for 40 pieces (~5 min/blog, ~2 min/LinkedIn), not done yet. Memory
  `claude-audits-quality`: Claude Code labels with a panel, Nghiệp checks disagreements; Ms. Thư's team not assigned
  homework. One reviewer account (`trang`) now inactive. Ms. Thư's team's weekly minutes: unknown. Proposed default:
  ≤ 30 min/week for Nghiệp on disagreements; 0 required from Ms. Thư.
- Cheap capture: reason chips on the Content Quality drawer (`fact_not_in_source`, `optional_as_included`,
  `wrong_place_or_time`, `voice_off_brand`, `ai_phrasing`, `format_channel`, `repair_residue`, `style_only`) into
  `audit_log.details` (no migration), pre-selected from the gate; `fact_not_in_source` wired to
  `record_outcome(question_key="a1_claim_supported", truth=False)` (AA-845 a). Same chips on S1 Regenerate and field
  edit (+ fix G2). Tenant portal: no chips by default (tenant sees content only); implicit capture via T2 diff and G1.
  Optional product-worded "What should we change next time?" is a product decision; never shows gate codes or scores.
- Extend `PieceLabel.tsx` to T2 versions and S1 tours. Queue only panel disagreements or verdict-changing candidates;
  5–10 per week, stratified.

## 9. Unknowns

Live counts (`content_piece_label`, `pipeline_lessons`, `acp_output_rules`, audit_log sentence actions, T2
`tenant_edit` share); current T2 unit cost; whether `grounding.py:523` `record_outcome` writes rows. Pending decisions:
AA-729, AA-845 (c), tenant feedback prompt, freezing `pipeline_lessons`, Ms. Thư team minutes.
