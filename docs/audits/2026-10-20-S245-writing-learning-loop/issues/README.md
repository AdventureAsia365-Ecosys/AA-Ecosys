# Writing Memory v1 — detailed issue plan (S245)

34 detailed tasks (WM-01..WM-34) behind the grouped Linear issues (rule D: one Linear issue per deliverable slice). Approved: D1–D16 and the cost cuts E1–E4 (20/10/2026). Generated from `writing-memory-issues.json`.

## Group 1: Freeze the ungated lessons loop and record ADR 0009 (governed writing memory)

### WM-01 — [Writing memory] Freeze the ungated shared.pipeline_lessons loop behind a flag

Priority 2 · blocked by — · phase P0

## Problem
The AA-132 lessons loop is broken and unsafe if anyone "fixes" it. The writer inserts with `stage = "audit"` (`services/content_generation/flag_fix_node.py:735`, via `loop.run_until_complete` at :685), but both readers only select `stage IN ('S1_rewrite','S1_editor')` (`services/content_generation/s1_batch.py:110-112`, `api/routers/admin_pipeline.py:562-565`) and append `what_to_do` to the shared S1 system prompt (`admin_pipeline.py:582-583`). The table has no `tenant_id` (schema reference 20/10/2026) and T2 runs the same graph, so a stage "fix" would let T2 (tenant) failures steer the global S1 prompt and park tenant-derived `pattern`/`example_before` text in a global table. No eval gate, rows default to active. Source: S245 writing-learning-loop audit §1.2 (D3 approved).

## Scope
1. Read-only count first: rows by `stage` and `is_active` (ECS exec with `DATABASE_URL`); record in the issue.
2. One flag (default OFF) guarding both reads (`s1_batch.py:108-122`, `admin_pipeline.py:560-583`) and the write path (`flag_fix_node.py:655-760`).
3. If any active `S1_rewrite`/`S1_editor` rows exist today, list them: switching the read off changes the S1 prompt, so note the prompt hash before/after (`prompt_version_of`, `services/content_generation/batch_prompt.py:240`).
4. Lesson line in `skill/aa-lessons/lessons.md` (stage mismatch + global table).
Out of scope: dropping the table (WM-34).

## Done when
- Exact row counts per stage recorded in a comment.
- On Dev after deploy: no new `pipeline_lessons` insert and no read (pg_stat_user_tables n_tup_ins / idx_scan unchanged across one S1 rewrite and one T2 rewrite).
- Unit test: with the flag off, the S1 system prompt contains no "LESSONS FROM PREVIOUS BATCHES" block.
- Deployed and verified per aa-ship.

## Risk / cost
Risk class: LLM prompt change (only if active S1 rows exist). Cost $0.

## Related
AA-132 (origin), AA-763 (shared S1/T2 graph). Audit: docs/audits/2026-10-20-S245-writing-learning-loop/README.md §1.2, §11.

### WM-02 — [ADR] CIS app ADR 0009: governed writing memory (rules + pinned exemplars, release-gated, no fine-tuning)

Priority 3 · blocked by — · phase P0

## Problem
The writing-memory design (S245) was approved (D1-D16, E1-E4) but none of its invariants are recorded where the code lives. `apps/AA-CIS-App/docs/adr/` stops at 0008 (checked on origin/main). Without an ADR, later sessions can re-open settled points (auto-activation, fine-tuning, vendor split, budgets).

## Scope
1. `apps/AA-CIS-App/docs/adr/0009-*.md` (app series; cites ecosystem ADR 0009 placeholder, AI platform / AA-804, a different series).
2. Record as dated invariants: nothing auto-activates, every release needs one human click (D6a); no fine-tuning in v1 (D2); rules are constraint-only; fact gates (F1/F17/F9_cta_fact, Jev) rank above every learned item; drafter/judge is non-Anthropic on the existing judge route while writers are Anthropic (app ADR 0006 §5); monthly release train, L0 lexicon any time, rollback any time (E1); shadow 20 targeted, T2/Facebook 50, repair_hint-only ≤10 (E2); S1 rules only, T2/T9 two pinned examples per release, no kNN (E3); learning-loop LLM spend ≤ $25/month and ≤ $10 per R2 release run, full baseline/reverify runs approved separately (E4); tenant text only in deletable tables, `audit_log` keeps ids/hashes (D16 exception for legacy rows).
3. Supersedes AA-132 lessons and AA-99/N8 output rules; update `CONTEXT.md` (ownership of the new tables).

## Done when
- ADR merged, listed in `docs/adr/README.md` of the app, `CONTEXT.md` updated in the same PR.
- Docs lint (AA-888) green.

## Risk / cost
Risk class: none (docs). Cost $0.

## Related
Audit README §5, §13; cost-cuts README §7 + K4 (root repo, branch docs/s245-crm-v2-cost-paa).

## Group 2: Capture writing signals: before/after text, reason codes, every T9 attempt

### WM-03 — [Writing memory] Migration shared.writing_signal (RLS + FORCE, deletable) and the record_writer_feedback helper

Priority 2 · blocked by — · phase P0

## Problem
Human corrections are either lost or stored where they cannot be deleted. `acp_shared.audit_log` is append-only with a hash chain and `audit_log_no_delete/no_update/no_truncate` triggers (schema reference 20/10/2026), so before/after text written there can never be removed at tenant offboarding. The loop needs one normalised, deletable signal store before any capture work starts.

## Scope
1. Migration (next free CIS number; 251 is the latest on origin/main): `shared.writing_signal` with writer (`a1`,`t2`,`t9_blog`,`t9_social`), channel, `scope` (`platform`|`tenant`) + `tenant_id uuid NULL` with a CHECK tying them, field/paragraph locator, before/after text, gate, `reason_code`, actor type (admin/tenant/system), `fact_status` (`pending`,`grey`,`pass`,`fail`), `audit_log_id uuid NULL` (audit_log.id is uuid), source table + id, created_at.
2. RLS on + FORCE. Policies: `cis_app` (code must still filter `WHERE tenant_id = $1`, because CIS `cis_app` policies are `USING true`) and `aa_app_user` tenant_isolation with WITH CHECK, because the tenant T9 edit runs on the tenant pool (`services/acp_content_writing/service.py:2222-2230`).
3. Helper `record_writer_feedback(conn, ...)`: inserts in the caller's transaction, never calls an LLM; returns the signal id; `audit_log.details` gets only signal id + sha256 + reason chip, never text.
4. `delete_writing_signals_for_tenant(tenant_id)` with a DRY RUN mode (destructive-ops procedure).
5. Register the store in the AI Use Register (AA-804).

## Done when
- Migration applied on Dev through DB Migrate; schema reference PR merged.
- Tests run as `cis_app` and as `aa_app_user`: tenant A cannot read or insert tenant B rows on the tenant pool; `scope='platform'` rows must have `tenant_id IS NULL`.
- DRY RUN + real delete test for one synthetic tenant removes only its rows.
- Agent review on the PR (migration + RLS).

## Risk / cost
Risk class: migration + RLS. Cost $0.

## Related
AA-804 (AI Use Register), AA-859 (tenant pool). Audit §5.2 graft 7-8, §5.3.

### WM-04 — [Writing memory] Capture before/after text on tenant T9 My Content edits

Priority 2 · blocked by WM-03 · phase P0

## Problem
A tenant edit of a T9 piece overwrites the AI text: `_PIECE_EDIT_SQL` updates `content_text` and returns only the new text (`services/acp_content_writing/service.py:2222-2230`), and the audit row stores only `{"content_length": ...}` (`service.py:2237-2242`). The strongest "learn from human edits" signal is lost.

## Scope
1. In the same transaction (tenant pool, RLS), read the current `content_text` (`SELECT ... FOR UPDATE` or a CTE) before the UPDATE.
2. Call `record_writer_feedback` with before/after, `actor='tenant'`, writer from the piece channel, `fact_status='pending'`.
3. Audit row keeps `content_length` and adds signal id + sha256 only.
4. Tenant response unchanged (no new fields in the tenant projection).
Out of scope: any tenant-facing UI (D7a).

## Done when
- One tenant edit on Dev (synthetic tenant) produces one `writing_signal` row with both texts (query output in a comment) and an audit row without text.
- Tenant PATCH response shape unchanged (contract test).
- Deployed and verified per aa-ship.

## Risk / cost
Risk class: none beyond tenant-pool write path. Cost $0.

## Related
AA-569 (tenant edit), AA-613 (tenant-safe projection).

### WM-05 — [Writing memory] Capture per-field before/after on admin A1 generated_content edits

Priority 2 · blocked by WM-03 · phase P0

## Problem
`PATCH /tours/{tour_id}/generated/{content_id}` (`api/routers/admin_pipeline.py:3760-3815`) overwrites fields and stores only `edit_diff = {"fields": [...], "reviewer_handle": ...}`; the AI version is lost, so A1 corrections cannot feed platform rules.

## Scope
1. Read the edited fields' current values in the same connection before the UPDATE.
2. One `writing_signal` row per changed field: `writer='a1'`, `scope='platform'`, `tenant_id NULL` (A1 is platform content; do not copy `generated_content.tenant_id`).
3. Keep `edit_diff` as is; add the signal ids.

## Done when
- One admin field edit on Dev yields N signal rows (one per field) with before/after and `scope='platform'`.
- Existing human_edited / revalidate_passed behaviour unchanged (existing tests green).
- Deployed and verified per aa-ship.

## Risk / cost
Risk class: none. Cost $0.

## Related
AA-234, AA-232 (current edit audit).

### WM-06 — [Writing memory] Reason codes on admin actions (API) and fact_not_in_source to Jev record_outcome(truth=False)

Priority 3 · blocked by WM-03 · phase P0

## Problem
Approve/reject/dismiss and sentence edits carry no reason, so the loop cannot tell a factual fix from a style fix (S218: 196 review rows, 0 decisions with reasons). Jev outcomes are almost empty because only approvals record truth (AA-845).

## Scope
1. Optional `reason_code` (enum: `fact_not_in_source`, `optional_as_included`, `wrong_place_or_time`, `voice_off_brand`, `ai_phrasing`, `format_channel`, `repair_residue`, `style_only`) on: sentence apply T9 (`api/routers/admin_content_quality.py:500`) and T2 (`:1169`), review-queue reject (`api/routers/admin_pipeline.py:2724`) and dismiss (`:2757`), and the A1 review "Regenerate" action.
2. Each call writes a `writing_signal` row (sentence before/after already known for sentence apply).
3. `fact_not_in_source` calls `record_outcome(..., truth=False)` (`shared/llm_client/decide.py:471`) for the matching Jev question.
4. Default chip suggested from the flagged gate (returned by the existing GET used by the drawer).

## Done when
- API tests: each route accepts and stores the code; unknown codes rejected (422).
- On Dev, one `fact_not_in_source` apply creates a `decision_log` outcome with truth=false (query in a comment).
- Deployed and verified per aa-ship.

## Risk / cost
Risk class: none. Cost $0.

## Related
AA-845 (Jev outcome loop), AA-802 (T2 sentence edit), AA-791.

### WM-07 — [Admin UI] One-click reason chips in the Content Quality drawers and the A1 review actions

Priority 3 · blocked by WM-06 · phase P0

## Problem
WM-06 adds reason codes to the API, but they only become data if an admin can set one with one click when applying a sentence or acting on an A1 review item.

## Scope
1. Chip row (UI kit `app/_kit`) in `frontend/app/admin/content-quality` sentence actions for T9 pieces and the T2 `TourVersionDrawer`, preselected from the flagged gate; one click to confirm.
2. Chips on A1 review Reject / Dismiss / Regenerate.
3. "Use as example" / "Never use as example" toggles stored on the signal (consumed by WM-27).
Out of scope: tenant portal (nothing changes there, D7a).

## Done when
- aa-ui-verify screenshots on a Vercel preview: chip preselected, one click saves, value visible on reload.
- Share of admin sentence actions with a reason ≥ 80% over the first 20 actions (query).

## Risk / cost
Risk class: none. Cost $0.

## Related
WM-06.

### WM-08 — [Writing memory] Persist every T9 attempt's text and stamp writer_prompt_version in writer_input

Priority 3 · blocked by — · phase P0

## Problem
Per-attempt gate ledgers are kept (`repair_log`, AA-791), but only one discarded attempt's text survives: `discarded_attempts=[discarded_attempt] if discarded_attempt else []` (`services/acp_content_writing/service.py:1907`). Replay ($0) and edit-pair metrics need every attempt's text, and T9 pieces carry no prompt version.

## Scope
1. Keep the text of every attempt in `content_piece.discarded_attempts` (bounded: attempts ≤ 3), each tagged with its attempt number and ledger index.
2. Add `writer_prompt_version` (sha256[:8] of the exact system prompt, same function as `prompt_version_of` in `services/content_generation/batch_prompt.py:240`) to `writer_input_snapshot` (`service.py:1940`).
3. Admin-only: confirm the tenant projection never returns either field.
Out of scope: T2 stamping (needs `generation_meta`, WM-25).

## Done when
- A new 3-attempt T9 piece on Dev stores 2 discarded texts + final, and `writer_input.writer_prompt_version` (query).
- Tenant projection test still hides `discarded_attempts` / `writer_input`.
- Deployed and verified per aa-ship.

## Risk / cost
Risk class: none. Cost $0 (storage only).

## Related
AA-791, AA-769 (writer_input).

## Group 3: Rule store and the mining job (scoped rules, fact filter, cheaper drafter)

### WM-09 — [Writing memory] Migration shared.writing_rule: scoped rules with kinds, token caps, reason-code keys and expiry

Priority 3 · blocked by WM-03 · phase P1

## Problem
There is no governed store for learned rules: the old `shared.pipeline_lessons` has no scope or tenant and `acp_shared.acp_output_rules` is dead (AA-603). Rules need a scope, a kind, provenance and caps before any mining runs.

## Scope
1. Migration: `shared.writing_rule` with `kind` (`lexicon`,`writer_instruction`,`repair_hint`,`preference_summary`), `scope`/`tenant_id` CHECK as in `writing_signal`, writer, `applies_to` channels, `reason_code` + gate alias map key (survives AA-787 gate renames), text, replacement (lexicon), `status` (`candidate`,`rejected`,`approved`,`active`,`expired`), provenance (signal ids), support counts, `expires_at` (60 days), approved_by/at.
2. Token caps enforced at write: platform rules for a writer ≤ 400 tokens total, tenant rules ≤ 250 tokens total, one rule ≤ 25 words.
3. RLS on + FORCE; code-level `WHERE tenant_id = $1` for tenant scope.

## Done when
- Migration applied on Dev via DB Migrate; schema reference PR merged.
- Tests (as `cis_app`): a tenant rule never resolves for another tenant; a platform rule with `tenant_id` set is rejected; cap overflow rejected.
- Agent review on the PR.

## Risk / cost
Risk class: migration. Cost $0.

## Related
AA-603 (N8 removal), AA-787 (gate rename).

### WM-10 — [Writing memory] One-time backfill of writing_signal from existing edits, ledgers and lessons

Priority 3 · blocked by WM-03 · phase P1

## Problem
About half of the learning material already exists but is scattered: admin sentence edits in `audit_log` (`content_piece.admin_sentence_*`, `tenant_tour_version.admin_sentence_*`, `services/acp_shared/audit_log.py:68-75`), T2 tenant edits as parent/child versions (`edit_source='tenant_edit'`, `parent_version_id`), T9 `repair_log`/`discarded_attempts`, and `quality_scores.lessons_extracted`.

## Scope
1. Idempotent backfill job (`shared.job` kind) reading those sources into `writing_signal` with source table + id.
2. Cast `audit_log.tenant_id` (varchar(50)) to uuid; A1 rows → `scope='platform'`, no tenant_id.
3. Text from `audit_log` is copied into `writing_signal`; the legacy `audit_log` copy stays (D16 retention exception, AI Use Register note).

## Done when
- Counts per source and per tenant recorded in a comment; re-running inserts 0 rows.
- Spot check of 5 rows per source against the original.

## Risk / cost
Risk class: none (insert only). Cost $0.

## Related
AA-802, AA-791, D16.

### WM-11 — [Writing memory] Async fact filter on signals (new_specifics, Jev for grey cases, quarantine of added claims)

Priority 3 · blocked by WM-03 · phase P1

## Problem
A human edit can add a promise the source lacks (e.g. tenant writes "lunch included"). Learning from such edits would teach writers to invent facts. The filter must run outside the request path.

## Scope
1. Job kind that takes `fact_status='pending'` signals and runs `new_specifics(original, replacement, ...)` (`services/acp_content_writing/sentence_repair.py:418`) on before→after against the stored source/writer_input.
2. No new specific → `pass`; new specific not in source → `fail` (`adds_unsourced_claim`, quarantined, never mined); ambiguous → `grey`, needs admin confirmation until AA-803 is calibrated.
3. `reason_code='fact_not_in_source'` signals are always `fail` for learning.

## Done when
- Unit tests with fixtures: "lunch" → "lunch included" fails; pure style edits pass.
- On Dev, the backfilled signals have no `pending` rows after one run; counts per status in a comment.

## Risk / cost
Risk class: none. Cost $0 (Jev only for grey cases if enabled; otherwise admin confirmation).

## Related
AA-803, AA-845. Audit §5.2 graft 7.

### WM-12 — [Writing memory] writing_memory_mine job: SQL clustering, thresholds, judge-route drafter on masked text, constraint-only lint, PREDICT check, budget guard

Priority 3 · blocked by WM-09, WM-10, WM-11 · phase P1

## Problem
Signals do not turn into rules by themselves. The miner must stay cheap, tenant-safe and unable to propose rules that add facts.

## Scope
1. Trigger: only when ≥ 10 new `pass` signals since the last run, at most 2 runs per month, plus one run before the monthly release close; manual run from admin.
2. Clustering and thresholds in SQL ($0): tenant rule ≥ 2 edits on ≥ 2 pieces of that tenant; platform rule with tenant evidence needs ≥ 3 distinct tenants; "≥ 2 reviewers" and "gate repeat ≥ 5% in 30 days" only for A1 signals (D9). Only clusters over threshold go to the LLM.
3. Drafter: new stage `writing_memory_mine` seeded in `shared.llm_role_config` with `role='judge'`, the current judge route (gpt-5.6-luna → gpt-6-luna → gpt-6-luna-openai last, per migration 224) and `shadow_sample_pct = 0`; ≤ 50 calls per run; input is entity-masked text only, never raw multi-tenant text.
4. Lint: constraint-only (rejects "include/mention X"), lexicon replacements checked with `new_specifics`, 5-gram overlap block against all tenant corpora + brand names + forbidden words, PREDICT check (rule explains ≥ 2 held-out edits in its cluster).
5. Budget guard helper shared by mine/eval/shadow stages: sums `shared.llm_call_log.cost_usd` for these stages in the calendar month; refuses a run that would exceed $25/month (E4).

## Done when
- One run on Dev ≤ $1 (llm_call_log, stage `writing_memory_mine`) produces candidates with provenance.
- Tests: lint rejects "include X"; a tenant-A-only cluster never yields a platform rule; platform rule from tenant evidence needs 3 tenants; budget guard blocks a run when the month total is over cap.
- Deployed and verified per aa-ship.

## Risk / cost
Risk class: LLM + cost. Paid: ≤ $1 per run (GPT-5.6 Luna Global CRIS $0.20/$1.20 per 1M, AWS model card, accessed 20/10/2026).

## Related
D9, D10, E4; app ADR 0006 §5.

### WM-13 — [Writing memory] Agreement check, then move the rule drafter to gpt-6-luna first

Priority 3 · blocked by WM-12 · phase P1

## Problem
GPT-6 Luna costs $0.10/$0.50 per 1M tokens vs GPT-5.6 Luna $0.20/$1.20 on Global CRIS (AWS model cards, accessed 20/10/2026; geo/US +10%). It already serves `a3_atomize`, `s1_source_facts`, `t10_claims`. Swapping the drafter halves mining cost, but only if rule quality holds (approved cut, cost-cuts §2 #6).

## Scope
1. One-time check: the same 20 clusters drafted by both models (stage `adhoc_wm13`, logged).
2. Compare lint + PREDICT pass rate (gpt-6-luna may be at most 10 points lower) and Cohen's κ of accept/reject between the two drafters' outputs, reported with the numbers.
3. If it passes: reorder the `writing_memory_mine` route to gpt-6-luna → gpt-5.6-luna → gpt-6-luna-openai; if not, keep the current route and record why.
Out of scope: reasoning-effort tuning (client does not send it on Converse today).

## Done when
- Report in a comment: pass rates, κ, cost (≤ $0.8).
- `llm_role_config` shows the chosen route on Dev.

## Risk / cost
Risk class: LLM + cost. Paid one-time ≈ $0.25-0.8.

## Related
WM-12, D10.

### WM-14 — [Admin UI] /admin/writing-memory: Signals and Candidates tabs

Priority 3 · blocked by WM-10, WM-12 · phase P1

## Problem
Signals and candidate rules need a place where the admin can see clusters, provenance and lint results and act on candidates.

## Scope
1. New page `/admin/writing-memory` (UI kit), tab Signals: clusters by writer, channel, tenant; counts, trend, before/after samples, fact status.
2. Tab Candidates: draft rules with provenance links, support, scope, lint result, fact verdict; actions edit / reject (with reason) / send to R0.
3. Admin-only routes; staff_authz POLICY entries for every non-GET route.

## Done when
- aa-ui-verify screenshots on a preview with backfilled data.
- staff_authz policy test green (every new non-GET route has a policy).

## Risk / cost
Risk class: auth (new admin routes). Cost $0.

## Related
Audit §7.

## Group 4: R0 replay engine ($0) and the L0 lexicon fast path

### WM-15 — [Eval] R0 replay engine ($0) and candidate filter with k equal to the mining threshold

Priority 3 · blocked by WM-09, WM-10 · phase P1b

## Problem
Every rule must be proven on stored text before any paid evaluation. R0 also filters out candidates whose target cluster no longer recurs, which avoids paying R2 for them (approved cut #3a, corrected: k must equal the mining threshold, not a fixed 3, or Dev would starve).

## Scope
1. R0: deterministic replay of a rule over stored text + `gate_ledger` + `repair_log` + `writing_signal` (counterfactual pattern from `s245_f9_counterfactual.py`): how often the rule would fire, which past failures it would have prevented.
2. Candidate filter: a candidate enters R2 only if its cluster recurred ≥ k times in 30 days, k read from the same config as the mining threshold.
3. Per-rule R0 results stored on the rule; candidates that fail stay visible and are reconsidered next month.

## Done when
- R0 reproduces the current observed gate numbers on stored data before any rule is applied (sanity check).
- Unit test: k follows the mining threshold config.
- R0 result for 3 real candidates in a comment, $0 in llm_call_log.

## Risk / cost
Risk class: none. Cost $0.

## Related
AA-865 (counterfactual method).

### WM-16 — [Writing memory] L0 lexicon fast path into the tenant vocabulary layers, applied before the gates

Priority 3 · blocked by WM-15 · phase P1b

## Problem
The quickest visible win ("the AI no longer writes X") is a vocabulary rule, which is deterministic and can be proven with R0 alone (D11). It must never bypass the fact gates.

## Scope
1. `lexicon` rules (ban in v1; a replacement only if `new_specifics` finds no new number, place, time, price or service) feed the AA-800 layers (`services/acp_shared/signature_vocabulary.py`, T9 words line `services/acp_content_writing/prompts.py:344-347`, T9 gate in `quality_gates.py:366`).
2. Applied before the gates (prompt + gate), never as a post-gate text substitution.
3. Activation per rule: R0 + one admin click (no R2, no shadow); rollback one click; tenant scope respected.
4. First target: T9 social.

## Done when
- One L0 rule active for T9 social on Dev; R0 shows the target phrase drops with 0 new hard-stop hits.
- Test: a replacement that adds a number/place/time/price/service is rejected.
- Rollback drill: next piece no longer gets the rule (writer_input shows it).

## Risk / cost
Risk class: LLM prompt change. Cost $0.

## Related
AA-800 (PR #869), AA-787 (lexicon gate).

## Group 5: Eval and release gate: golden set, R2 runner, targeted shadow, Releases tab

### WM-17 — [Eval] First-class golden set tables and widened prompt_eval_runs

Priority 3 · blocked by — · phase P2

## Problem
`shared.prompt_eval_runs` is S1-only with results in a `details` jsonb (schema reference 20/10/2026) and has 0 inserts. The AA-729 golden set needs real tables with tune/holdout split, tiers, traps and tenant to drive release gates.

## Scope
1. Migration: `eval_golden_set`, `eval_golden_item` (tier, tune/holdout 30%, trap flag, tenant, writer, channel), `eval_item_result` (per item per release, judge model + version).
2. Widen `prompt_eval_runs` (writer, release id, cost, stop reason).
3. Import the AA-729 set (A1 50, T2 10, blog 15, LinkedIn 15) from DB/S3 bronze; repository tests use fake fixtures only (public repo).

## Done when
- Tables on Dev with the AA-729 items loaded; counts per tier in a comment.
- No real tenant text in the repo (grep in CI).

## Risk / cost
Risk class: migration. Cost $0.

## Related
Blocked by AA-729 (golden set). AA-783 (anchor labels).

### WM-18 — [Eval] Release tables with activate-requires-eval CHECK, API double check, monthly train, reverify state and rollback pointer

Priority 3 · blocked by WM-09, WM-17 · phase P2

## Problem
Rules and examples must reach writers only as versioned, approved releases that can be rolled back without a deploy, and the gate must hold even if the API has a bug.

## Scope
1. Migration: `writing_memory_release` (writer, scope, items, status `draft`→`evaluated`→`approved`→`active`→`retired`, `reverify`, approver, eval/shadow refs) and `writing_memory_shadow` (shadow outputs, tenant-scoped, deletable).
2. DB CHECK: `active` requires eval refs and a shadow ref, except lexicon-only releases (R0 only); the API checks the same.
3. One active pointer per writer (+ tenant); rollback = move the pointer.
4. Monthly train: one regular release per writer per month; an emergency release only to clear a hard stop; L0 lexicon and rollback are never blocked by the train.
5. `reverify` when the golden set, a model route or the gate taxonomy (AA-787) changes: release keeps running, flagged, re-run needs approval.

## Done when
- DB and API both refuse to activate a release without eval/shadow (tests).
- Rollback drill on Dev: next job uses the previous release (writer_input/metadata stamp).
- Agent review on the PR.

## Risk / cost
Risk class: migration. Cost $0.

## Related
Absorbs part of AA-900 (manual eval gate).

### WM-19 — [Eval] R2 runner: affected tiers only, fail-only early stop, stored controls re-judged, $10 per release cap

Priority 3 · blocked by WM-15, WM-18 · phase P2

## Problem
R2 is the main paid gate. Approved cuts: run only affected tiers; stop early only when failing; never regenerate the control arm; but re-judge stored controls with the current judge so judge drift cannot fake a win (K2 correction).

## Scope
1. Sequence: 3-item probe → tune (70%) of the affected tiers → holdout (30%) only if tune passes. Stop on hard stop 1 (new B-class/C1) or futility; never stop early on success.
2. Controls: stored outputs of the active release (release 0 = AA-729 baseline), re-scored by the current judge; regenerate only in `reverify`.
3. Stage `memory_eval` seeded with `shadow_sample_pct = 0`.
4. Judge counts toward hard/soft stops only if κ ≥ 0.6 against Nghiệp's anchor labels (AA-783); otherwise informative only.
5. Isolation probe (tenant A n-grams in tenant B output, F10 ≥ 0.92) and QA-artefact grep in outputs.
6. Caps: ≤ $10 per release run and the $25/month guard (WM-12 helper); a full-set baseline/reverify run is a separate approval.
7. Release touching S1 or T2 always runs the "fact-dense" and "≥ 9 days" tiers.

## Done when
- One R2 run on Dev ≤ $10 with per-item results stored; a seeded failing candidate stops at tune.
- Tests: controls are never regenerated outside reverify; cap enforced.

## Risk / cost
Risk class: LLM + cost. Paid ≤ $10 per release run (Haiku 4.5 $1/$5, Sonnet 4.6 $3/$15 per 1M, list price; Bedrock table did not render, treated as estimate).

## Related
AA-729, AA-783, AA-865 (pooling rule).

### WM-20 — [Eval] Release 0: byte-identical prompt replay for all four writers before memory is enabled

Priority 2 · blocked by WM-18 · phase P2

## Problem
The insertion path itself must not change any article. Before `memory_enabled` is switched on for a writer, an empty release through the new path must produce exactly today's prompt.

## Scope
1. Release 0 (empty memory) per writer (A1, T2, T9 blog, T9 social).
2. Replay stored inputs through the new insertion path and compare system + user prompts byte for byte with the current builders (`prompt_version_of` hash for S1).
3. Record AA-729 baseline numbers as release 0's eval.

## Done when
- 0 byte differences on ≥ 20 stored inputs per writer (CI test with fake fixtures + Dev replay report, $0).
- Release 0 rows exist and are active for each writer.

## Risk / cost
Risk class: none. Cost $0.

## Related
AA-729 (baseline numbers).

### WM-21 — [Eval] Targeted shadow replay: 20 inputs (A1, blog, LinkedIn), 50 for T2 and Facebook, ≤ 10 for repair_hint-only

Priority 3 · blocked by WM-18, WM-19 · phase P2

## Problem
Shadow is the pre-activation check for hard stops 2 (tenant leak) and 3 (QA traces). The approved cut (E2) reduces it to targeted inputs, with the K2 corrections: T2 and Facebook keep 50 (holdout T2 is only 3 items, no Facebook tier), repair_hint-only releases still get a small shadow, and tenant releases get a cross-tenant probe.

## Scope
1. Input selection: most recent real inputs of the affected writer where the target gate/cluster fired, excluding golden items: 20 for A1, T9 blog, LinkedIn; 50 for T2 and Facebook; ≤ 10 for repair_hint-only releases; none for lexicon-only.
2. Tenant release: inputs of that tenant + 1-2 inputs of another tenant as isolation probe.
3. Outputs into `writing_memory_shadow` (never visible to tenants); stage `memory_shadow`, `shadow_sample_pct = 0`; budget guard applies.
4. Same isolation probe + QA-artefact grep as R2.

## Done when
- Unit tests for the size rules per writer/kind.
- One shadow run on Dev with cost in llm_call_log (expected ~$1-2 for 20 inputs, ~$5 for 50 T2).

## Risk / cost
Risk class: LLM + cost. Paid ~$1-7 per release.

## Related
E2 (cost-cuts K4).

### WM-22 — [Admin UI] Releases tab: report, one-click approve, activate, rollback, kill switch, monthly close and the prompt register

Priority 3 · blocked by WM-18, WM-19, WM-21 · phase P2

## Problem
Nghiệp approves one release per writer per month with one click (D6a, D15). The prompt register and manual eval gate of AA-900 should live here, not on a separate page (graft 11).

## Scope
1. Tab Releases: draft → eval report (R0/R1/R2, paired stats, isolation probe, cost) → shadow side by side → Approve → Activate / Roll back; per-writer kill switch; "close monthly train" button.
2. Prompt register view: current system prompt hash per writer + active release.
3. Admin-only routes with staff_authz POLICY entries.

## Done when
- aa-ui-verify on a preview: approve + activate + rollback round trip on a test release.
- AA-900 updated to point here (comment), its prompt-register scope closed by this issue.

## Risk / cost
Risk class: auth (new admin routes). Cost $0.

## Related
AA-900 (Data Platform project).

## Group 6: Inject approved rules into the four writers with a post-activation check

### WM-23 — [Writers] A1/S1: HOUSE RULES block replaces the lessons append (rules only, no examples), repair_hint only on the flagged code

Priority 3 · blocked by WM-01, WM-20 · phase P3

## Problem
A1 should learn platform rules without examples (E3): A1 is neutral catalogue content and its failures are mostly facts, forbidden words and structure. Today lessons are appended to the system prompt (`api/routers/admin_pipeline.py:582-583`, `services/content_generation/s1_batch.py:108-122`).

## Scope
1. HOUSE RULES block (active A1 release, platform scope, ≤ 400 tokens) at the end of the A1 system prompt in both paths (sync + batch materialisation), replacing the frozen lessons append.
2. Flag_fix (`services/content_generation/flag_fix_node.py:560-568`) receives only the `repair_hint` of the flagged code (~60 tokens), not the HOUSE RULES block.
3. Stamp `release_id` + `rule_ids` in `generated_content.metadata`.
4. A1 rules apply to T2 only if a T2 release includes them (shared graph, `stage_for`).

## Done when
- Release 0 replay still byte-identical (WM-20); release 1 for A1 passes R2 with 0 new B-class/C1 on the fact-dense and ≥ 9 days tiers.
- Cost per tour ≤ +1% measured in llm_call_log (expected +$0.0005).
- Deployed and verified per aa-ship.

## Risk / cost
Risk class: LLM prompt change. Paid: covered by WM-19 runs.

## Related
E3.

### WM-24 — [Writers] T9: platform rules after SYSTEM_PROMPT, tenant rules after the brand block, repair hints only when a gate fires

Priority 3 · blocked by WM-20 · phase P3

## Problem
T9 writes with a static `SYSTEM_PROMPT` (`services/acp_content_writing/prompts.py:184`, sent at `generate.py:201` and `:264`); the tenant brand block sits in the user prompt after CHANNEL and GOAL lines (`prompts.py:334-347`). Placement decides cost: the satellite marks the whole system block for caching, the user prompt is a plain string.

## Scope
1. Platform rules appended right after `SYSTEM_PROMPT` in the system block (shared cache across tenants).
2. Tenant rules (≤ 250 tokens) and pinned examples (WM-27) in the user prompt after the brand block and the AA-800 words line, before the content seed.
3. `repair_hint` added through `_repair_feedback` (`services/acp_content_writing/service.py:1031`) only when its gate failed; `applies_to` filters social vs blog.
4. Examples only on the first write, not on `rewrite_with_feedback`.
5. Stamp release id + rule ids in `writer_input`.

## Done when
- Release 1 for T9 social or blog passes R2 + shadow; 0 tenant leak, 0 QA traces.
- Cost per piece ≤ +7% (expected +2-4% blog, +4-7% LinkedIn) in llm_call_log.
- Two read-only cache checks run (CloudWatch query in cost-cuts §2 #7) and results posted.

## Risk / cost
Risk class: LLM prompt change. Cost covered by WM-19/21.

## Related
AA-800, AA-768.

### WM-25 — [Writers] T2: generation_meta migration with tenant projection denylist and regex in the same PR, then release injection

Priority 2 · blocked by WM-20 · phase P3

## Problem
`gold_aa_internal.tenant_tour_versions` has no metadata column (only `rewritten_content` jsonb). The tenant read uses `SELECT ttv.*` (`api/routers/v1_tours.py:820`) filtered by a denylist (`api/routers/_tenant_projection.py:19`) and a key regex (`:16`, `needs_review|quality|score|qa_|judge|llm_cost|jev_cost`) that would not catch `generation_meta`, `rule_ids` or `release`. Adding the column without closing this would leak QA state to tenants (hard stop 3).

## Scope
1. Migration: `generation_meta jsonb NULL` on `tenant_tour_versions`.
2. Same PR: add `generation_meta` to `TENANT_HIDDEN_VERSION_FIELDS`; extend the regex with `generation_meta|rule_ids|release|memory`; key-walk test on every tenant tour-version read.
3. Inject the active T2 release at the end of the T2 system prompt (`build_t2_system_prompt`, `services/content_generation/batch_prompt.py:114-136`): rules + 2 pinned examples when WM-27 lands.
4. Stamp release id + rule ids in `generation_meta`.

## Done when
- Key-walk test: no tenant response contains `generation_meta`, `rule_ids`, `release` or `memory` keys.
- One T2 rewrite on Dev stamps `generation_meta` (query) and the tenant GET does not show it (curl).
- Agent review on the PR (migration + tenant projection).

## Risk / cost
Risk class: migration + tenant data exposure. Cost $0.

## Related
AA-792, AA-613. Audit §7.

### WM-26 — [Writers] Post-activation check on every new piece (isolation probe + QA-artefact grep) with automatic rollback

Priority 2 · blocked by WM-18, WM-24 · phase P3

## Problem
Shadow is smaller after the approved cuts (20 inputs catch a 5% violation rate with 64% probability instead of 92%), so the safety net after activation must be real: every piece written by an active release is checked and a violation rolls the release back.

## Scope
1. After each A1/T2/T9 write under a non-zero release: isolation probe (tenant A n-grams in tenant B text, F10 ≥ 0.92) and QA-artefact grep (gate codes, citation tags, rule text, `generation_meta`/`rule_ids`/`release` keys).
2. Violation → move the writer's pointer to the previous release, mark the piece, alert (existing ops alert job).

## Done when
- Drill on Dev with a seeded violation: release rolled back automatically, next piece uses the previous release (stamp).
- Check adds no LLM call (llm_call_log unchanged).

## Risk / cost
Risk class: none. Cost $0.

## Related
Audit §8.2 (hard stops 2-3).

## Group 7: Pinned example sets and tenant preference summaries

### WM-27 — [Writing memory] Pinned exemplar sets per release (2 per tenant x writer x channel, entity-masked), no kNN or ivfflat

Priority 3 · blocked by WM-18, WM-24 · phase P4

## Problem
Voice examples help T2/T9 sound like the tenant. The approved design (E3, D12) replaces per-call kNN (k=3, ivfflat, embeddings) with two pinned, entity-masked examples chosen and approved inside the release: the release sees exactly what will run, and no runtime retrieval can pick a wrong paragraph.

## Scope
1. Migration `shared.writing_exemplar` (tenant scope, entity-masked text `[PLACE]`, `[N]`..., source signal, status), RLS on + FORCE, code-level `WHERE tenant_id = $1`.
2. Candidates from approved/edited pieces with `fact_status='pass'` and "use as example" (WM-07); never items marked "never use".
3. At release build: pick 2 per tenant x writer x channel; fall back to platform examples when a tenant has < 2. A1 gets none (E3).
4. Label in prompt: "voice only, reuse no fact".

## Done when
- Test as `cis_app`: release of tenant A contains only tenant A exemplar ids; resolving for tenant B returns 0 rows of A.
- R2 paired result for ≥ 1 tenant writer shows lower edit distance, 0 carried-over facts (n-gram check).
- Agent review on the PR (migration + tenant data).

## Risk / cost
Risk class: migration + tenant data. Cost $0 (no embeddings).

## Related
D12. Needs Ms. Thư before real tenants: consent / terms wording for using a tenant's own edits as its voice examples (Dev uses synthetic tenants).

### WM-28 — [Writing memory] Tenant preference summaries (CIPHER, ≤ 5 sentences) gated like rules

Priority 3 · blocked by WM-12, WM-19 · phase P4

## Problem
With few edits per tenant (Dev: ~48 T2 versions, ~251 T9 pieces), a short preference summary learns voice faster than examples. A summary can still encode an unsourced promise ("always mention free hotel pickup"), so it must pass the same gates as a rule.

## Scope
1. `preference_summary` rule kind: ≤ 5 sentences from that tenant's `pass` signals only, drafted on the judge route.
2. Same constraint-only lint, `adds_unsourced_claim` quarantine, R0-R2, shadow and one-click approval.
3. Inserted with the tenant rules (≤ 250 tokens shared cap).

## Done when
- Test: a summary containing an unsourced promise is quarantined.
- One approved summary for a synthetic tenant on Dev with R2 results.

## Risk / cost
Risk class: LLM. Paid: within the $25/month guard.

## Related
Audit §5.2 graft 9.

### WM-29 — [Admin UI] Exemplars tab: pinned sets per tenant, writer and channel, pin/unpin with reason

Priority 4 · blocked by WM-27 · phase P4

## Problem
Admins need to see and adjust which two examples a release will pin before approving it.

## Scope
1. Tab Exemplars on `/admin/writing-memory`: pool per tenant x writer x channel, masked text, source link, pin/unpin with reason, "never use".
2. Tenant 360 card "Voice memory" (active tenant rules, exemplar count, latest release).

## Done when
- aa-ui-verify on a preview; pin change shows in the next draft release.

## Risk / cost
Risk class: auth (admin routes). Cost $0.

## Related
WM-27.

## Group 8: Weekly KPIs, soft-stop rollback and the disagreement queue

### WM-30 — [Writing memory] Weekly KPI job with soft-stop rollback and 60-day rule expiry

Priority 3 · blocked by WM-26 · phase P5

## Problem
Hard stops are checked per piece (WM-26); soft stops (re-flag > 8%, light-edit share drop, minutes_to_fix +20%, tenant edit rate up, cost/piece +20%) and hard stop 1 on the golden set need a scheduled job, and rules must expire so the prompt does not grow forever.

## Scope
1. Weekly job: KPIs per writer and tenant (repeat-error rate, edit-pair replay hit rate, re-flag with Wilson 95%, capture completeness ≥ 80% reasons, candidate funnel, cost/piece, learning-loop spend vs $25).
2. Soft stop → rollback unless Nghiệp records a reason to keep.
3. Expire rules after 60 days unless re-confirmed by fresh signals.
4. Project stop rule: after P3, two releases without improvement → stop at P3 (report flags it).

## Done when
- Two automated weekly reports stored; one rule expired by the job (row).
- Trend written to `docs/audits/` once.

## Risk / cost
Risk class: none. Cost: golden-set part within caps.

## Related
Audit §8.

### WM-31 — [Admin UI] Metrics tab and weekly disagreement queue (5-10 items)

Priority 4 · blocked by WM-30 · phase P5

## Problem
The KPIs and the judge/human disagreement queue (≤ 30 min/week for Nghiệp, D15) need a screen.

## Scope
1. Tab Metrics: KPIs per writer/tenant, clean-pairs counter per writer (keeps the fine-tune door visible; no export path).
2. Disagreement queue: 5-10 items/week where judge and human labels disagree, one-click resolution.

## Done when
- aa-ui-verify on a preview with the WM-30 data.

## Risk / cost
Risk class: none. Cost $0.

## Related
D15.

## Group 9: Labels for T2/A1, offboarding deletion, retire the old lesson paths

### WM-32 — [Labels] Extend piece labels to T2 versions and A1 tours

Priority 4 · blocked by — · phase P5

## Problem
`acp_shared.content_piece_label` has primary key `(piece_id, labelled_by)` and only covers T9 pieces (1 insert so far); T2 and A1 cannot be labelled, so `minutes_to_fix` and light-edit share exist only for T9.

## Scope
1. Migration: a subject type (`t9_piece`, `t2_version`, `a1_content`) + subject id, or a sibling table with the same CHECKs (label, defects, minutes_to_fix ≤ 600).
2. `PieceLabel.tsx` drawer reused for T2 versions and A1 tour detail.

## Done when
- One label of each type on Dev; existing T9 labels unchanged.

## Risk / cost
Risk class: migration. Cost $0.

## Related
AA-791, AA-783.

### WM-33 — [Data] Offboarding deletion of learned tenant data (signals, tenant rules and summaries, exemplars, shadow outputs)

Priority 3 · blocked by WM-27, WM-28 · phase P5

## Problem
All learned tenant text must be deletable when a tenant leaves (data rule, graft 8). Legacy before/after text already in `audit_log` cannot be deleted (append-only triggers) and is a recorded retention exception (D16).

## Scope
1. One offboarding function covering `writing_signal`, tenant-scope `writing_rule` (incl. preference summaries), `writing_exemplar`, `writing_memory_shadow`, and tenant releases; DRY RUN first (destructive-ops procedure).
2. AI Use Register entry updated with the stores and the D16 exception.

## Done when
- DRY RUN + real run for a synthetic tenant: counts before/after, other tenants untouched.
- Agent review on the PR (data deletion).

## Risk / cost
Risk class: delete. Cost $0.

## Related
AA-804. Needs Ms. Thư: wording of the retention exception in tenant terms (with AA-820).

### WM-34 — [Data] DRY-RUN retirement of pipeline_lessons, acp_output_rules, /v1/rules and the dead rule adapter code

Priority 4 · blocked by WM-01, WM-23 · phase P5

## Problem
Two dead learning paths remain: `shared.pipeline_lessons` (frozen by WM-01, replaced by WM-23) and the N8 output rules (`acp_shared.acp_output_rules`, `/v1/rules` with a PATCH policy at `api/core/staff_authz.py:305` and the prefix at `:338`, `acp_post_processor.py`, `services/acp_produce/rule_adapter.py` used only by `tests/unit/test_aa363_rule_adapter.py`).

## Scope
1. DRY RUN listing rows, readers, grants; then drop tables (CIS migration), remove the route + staff_authz entries, delete the modules and their test.
2. Dead Table Registry updated.

## Done when
- DRY RUN evidence in a comment; after deploy `/v1/rules` returns 404 and staff_authz tests are green.
- Schema reference PR shows the tables gone.

## Risk / cost
Risk class: delete + migration. Cost $0.

## Related
AA-603, AA-850 (Dead Table Registry).

