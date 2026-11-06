# S271 — Audit + đánh giá thiết kế 4 workflow viết / chấm / thử (06/11/2026)

Tác nhân: Claude Code (Ultracode). Chỉ đọc code + dữ liệu live tổng hợp, **0 USD**, không gọi model.

## Phạm vi và cách làm

- 4 workflow: **T9 blog** (+ kênh social/LinkedIn dùng chung gate), **S1** viết lại tour catalogue, **T2** viết tour cho đại lý, **Writing Lab** (bộ nhãn, R0/R1/R2, judge eval, release, writing-memory).
- Bước 1 — 3 audit song song (`data/aa900-judge-rootcause.json`, `data/blog-pipeline-audit.json`, `data/tour-pipeline-audit.json`): bản đồ stage, lịch sử sửa từ 01/09, ma trận mâu thuẫn chính sách, số liệu ledger 30–60 ngày, ngân sách token/route, lưới hồi quy; mỗi audit có tổng hợp + 2 phản biện.
- Bước 2 — đánh giá thiết kế (`data/design-review.json`): mỗi workflow phê bình graph hiện tại theo 11 nguyên tắc → 3 bản thiết kế lại độc lập (EVOLVE / FACTS-FIRST / EVAL-FIRST) → hội đồng chấm chọn + ghép → kiến trúc sư gom một kiến trúc chung → 2 phản biện.
- UUID trong file data đã rút gọn 8 ký tự; không có account ID, ARN hay khoá.

## Kết luận theo workflow

| Workflow | Kết luận | Bản thắng |
|---|---|---|
| blog | RESTRUCTURE, not keep and not rebuild. | EVAL-FIRST is the spine: instruments, labels and measured gate modes come before any change to behaviour |
| s1 | RESTRUCTURE, not rebuild. | Proposal 1 (EVOLVE) is the backbone |
| t2 | RESTRUCTURE. Do not polish it, and do not rebuild from zero. The current graph is not sound, for three VERIFIED reasons: | EVOLVE is the backbone, with grafts from FACTS-FIRST and EVAL-FIRST |
| eval | RESTRUCTURE, not rebuild. The plumbing is sound and stays as it is: | Proposal 1 (EVOLVE) is the spine: it turns on dormant machinery and puts the $0-refusal guards first |

## Tóm tắt cho tech lead

Kết luận chung: cả bốn workflow (S1 viết lại tour gốc, T2 viết lại tour cho đại lý, T9 blog/social, Writing Lab đo chất lượng) đều nên TÁI CẤU TRÚC tại chỗ, không viết lại từ đầu. Phần viết và nhiều mảnh code đang tốt, giữ lại: writer v2, sửa từng câu có dẫn nguồn, các bước code cố định, gateway và ledger, cổng phát hành của Writing Lab.

Vì sao sửa mãi không dứt: cả bốn workflow cùng một gốc lỗi.
- Luật viết bị chép ở nhiều nơi, mỗi nơi một kiểu.
- Mỗi bước nhìn một phiên bản "nguồn" khác nhau.
- Thứ đang quyết định giữ bài là judge LLM chưa hiệu chỉnh, hoặc một điểm số không bao giờ trượt.
- Nhiều lối ra bỏ qua bước kiểm.
- Thay route, effort, cờ env đều không qua bước đo nào.

Kiến trúc chung đề xuất, mỗi phần chỉ làm một lần, dùng cho cả bốn workflow:
1. Gateway: tự thử lại đúng model khi bị cắt ở trần token, đánh dấu mọi lần rơi xuống model dự phòng (cả judge), ghim một model duy nhất cho judge được phép giữ bài, lưu nguyên câu trả lời thô để phát lại.
2. Một file chính sách viết duy nhất. Prompt, rubric, luật regex và bảng định tuyến đều sinh ra từ file này, CI chặn khi có chỗ chép tay.
3. Một bảng sự thật (FactSheet) dựng bằng code từ dữ liệu gốc. Writer, bộ kiểm, bước sửa và judge eval cùng đọc một bản.
4. Code giữ các ô cố định: dòng bữa ăn, số ngày, meta, slug, CTA, FAQ. LLM chỉ viết phần văn.
5. Một bộ kiểm bằng code chạy trước, rồi đến một model kiểm câu đã ghim. Cổng chỉ được giữ bài khi có số đo precision đạt chuẩn, chưa đo thì chỉ cảnh báo.
6. Một lối ra duy nhất cho mọi đường. Văn bản lưu phải đúng là văn bản đã qua kiểm.
7. Bộ chạy lại nhiều tầng (miễn phí, rồi vài cent, rồi trả phí), không bao giờ dùng lại verdict cũ. Fingerprint bắt mọi thay đổi route, effort, prompt.

Thứ tự làm:
- W0: chặn lãng phí và làm lộ sự thật. Miễn phí, kèm smoke khoảng 0,75 USD.
- W1: file chính sách, FactSheet, lối ra duy nhất ở chế độ chỉ báo cáo. Miễn phí.
- W2: gán nhãn theo từng câu và hiệu chỉnh judge. Dưới 2 USD, cộng 2-3 giờ anh duyệt nhãn.
- W3: nối lại luồng cho T9, S1, T2. Đo bằng chạy lại miễn phí, smoke khoảng 1 USD.
- W4: đưa model kiểm câu đã hiệu chỉnh vào chạy thật. Dưới 0,5 USD.
- W5: thử writer trả phí, mẫu nhỏ. Tổng tối đa khoảng 33 USD, mỗi lần chạy anh đồng ý riêng.
- W6: dọn code thừa và bắt buộc kiểm soát thay đổi.

Anh cần quyết, mỗi câu đã có đề xuất trên trang bấm chọn:
- phạm vi bối cảnh địa danh;
- brief không phải là nguồn;
- câu suy ngẫm tính là giọng văn;
- một dải độ dài meta 140-155;
- với nội dung của đại lý, code cắt câu hứa hẹn sai trước khi giao, chưa chặn publish;
- ghim gpt-6-luna-openai làm judge duy nhất;
- tour cưỡi voi ở T2 giữ nguyên văn;
- bỏ judge S1 khỏi luồng chạy thật;
- thời gian anh duyệt nhãn;
- trần chi phí cho các lần chạy trả phí.

Cần một ADR gốc mới số 0020 (kiến trúc chất lượng chung), một bản sửa ADR 0009 về gateway, và vài ADR trong CIS cho từng workflow.

## Bổ sung từ phản biện (đã đưa vào kế hoạch)

- W0: widen the route migration to every route with a verifier-family or nova-lite rung: t8_angle_gen, t9_repair, t9_faq_filter, t9_faq_answer_fit, t10_claims, t10_adjudicate, writing_memory_mine/eval. Add a CI lint that derives this from the live route snapshot instead of a hand list.
- W0: delete or gate the S1 Bedrock Batch path (/s1-batch/submit, bedrock_batch.py) and the legacy v1_pipeline approve endpoint. Point the revalidate job at final_contract (REPORT mode first).
- W0/decision page: add a decision row on the data rule for the pinned vendor_direct instrument. Option A: accept vendor primary for the verify role with allowed_scopes and an ADR 0009 amendment. Option B: pin an acc2 non-Claude model instead. Update the S235 test accordingly.
- Fix S0 wording: anchored=false lines can never be the sole support that clears a claim. A claim supported only by unanchored lines is 'unsupported' (warn or enforce per class).
- Add a Publish/Export contract stage after final_contract. Make slug, title and meta single-sourced from the stored gated fields: remove the angle_name title fallback and make blog_slug keep the gated slug, adding the key as a suffix only at a word boundary. Add a post-assert on the WordPress/Facebook payload, with its sha recorded in publish_log.
- Add channel profiles for every channel the slate can produce. At minimum, Facebook gets its own channel_spec, shape asserts, a cut-vs-hold decision and labels, because it is auto-published. The rest are declared export-only with warn-only gates. Split t9_social metrics and Writing Lab samples per channel.
- Add a decision and a design for human edits. Tenant edits are tenant-owned (BYO): contract_check + claim engine run in REPORT mode, the result is shown as a non-blocking notice, the status is re-derived (a held piece whose residual finding is gone becomes approved), and a new enforce-class promise sets content_compliance_flag. Admin sentence apply goes through final_contract. Scope invariant 4 to system-written text.
- Give FactSheet lines a provenance/trust field: source_raw, human_verified, tenant_asserted, llm_derived (atom/place card/day map), external (DFS). Rule: tenant_asserted lines may support claims only about the tenant (price, terms), with valid_until enforced at compose time.
- Add a source-change fan-out ($0): when raw_tours, Facts Entries, place-card facts, atoms or the Master change, re-run contract_check/claim-cache on dependent Master/T2/T9 objects by fs_sha. Results become a review row or a tenant notice. Sequence W6 re-atomize with an AA-990 carry-over (re-point open requests to the new atoms by quote match) before the atoms are replaced.
- W1 input measurements: add A0 column-map accuracy (log the LLM map plus a human confirm on the upload-staging decide when llm_used), a place-card fact error rate, place_days/locate accuracy on route tours, and angle_name/title leakage. Add the evidence-author family to the family check: the instrument may not verify against llm_derived lines written by its own family, or those lines count as unanchored.
- Writing memory: define tenant-release gating. Tenant releases are constraint-only (cut/ban/lexicon); exemplars must pass R0b contract replay on that tenant's last N objects plus the platform R1 record; no per-tenant R2. Re-verify existing exemplars and rules under the new policy_sha (W1) and retire failures. Decide where repair_hint rules plug into the route-table repair operators. Add a fact_filter row to thresholds.yaml.
- Change control: extend config_fp and the lint to runtime surfaces. Include the route-control version id, catalog wire_model/deployment rows, brand pack / house style / SEO config / Facts snapshot shas. UI edits of llm-config, route, switch and catalog on gated stages require an eval run id or a break-glass reason in the audited body, and they are frozen during waves. The instrument id hashes the wire_model, deployment and the provider-returned model id.
- Define the pause and resume semantics: a verifier refused by the tenant budget or a stage switch gives 'unverified' (never pass), the job resumes from the stored best candidate, and final_contract runs on resume. A Jev outage in S1 gives DEGRADED (no publish).
- W5 caps: budget for paid regeneration of arm A controls (or re-baseline A as part of W3 smokes), since config_fp changes invalidate the stored finals.
- ADR 0020: add an explicit scope section naming supply_content_writer, TripPlanner narration, CRM AI and aa_content as in or out. Recommended: supply_content_writer becomes a 5th lightweight profile (policy compile + contract_check of numbers/services vs supply facts, warn-only, with human review kept). Add locale (en-US/en-GB) as a policy dimension.
- F1 Add the missing policy questions to the W1 decision page before freezing writing_policy v1: rarity/uniqueness/superlative/era claims, suitability/safety claims (for children, swimming, pace), and scene staging around a sourced moment. Each gets a proposed answer and twin fixtures. Then re-derive the fixture-1.3.0 item labels with verdict_rule and list every label that flips, before any W2 work.
- F2 Rewrite the promotion bars in terms of the metric they measure: precision LB on flagged count, recall on n_pos. Publish a sample-size table per row (P 0.90 / LB 0.80 needs about 47 flagged). Pool rows by class across writer profiles where the detector is profile-independent, and size CL-1 from that table instead of '60 claims'. If the label budget cannot reach the bar, say up front which classes stay warn-only through W5.
- F3 Make Decision 7 'instrument = base model with calibrated twin connections'. Ask R1 to pick among at least 2 candidates (gpt-6-luna family twins, plus one acc2 non-Claude model if one exists). Record the served model id per call. Pin max_completion_tokens >= 8192 (migration 382). Record effort as 'provider_default' with a probe, and add a CI check that fails if the provider later accepts an effort field we do not send. State the data-scope exception explicitly in ADR 0009's amendment.
- F4 W0: remove gpt-6-luna-openai from ALL writer routes (t8_angle_gen, t9_repair, s1_generate, s1_flag_fix, s1_itinerary_nudge, t2_flag_fix, t2_itinerary_nudge, plus t9_write and t2_generate) with queue_retry. Remove nova-lite from writing_memory_mine/eval as well. Freeze writing-memory mining until R1 exists. Record the shared family of a3_* evidence producers and the instrument in the ADR, and measure it in W2.
- F5 Drop the W0 'attempt 3 = code truth_cut'. In W0, attempt 3 becomes $0 'stop and label' (no paid call, no deletion). truth_cut is allowed only for classes with a passing measurement record, at clause level first (recite the FactSheet line or drop the clause), and as a sentence delete only when the sentence holds no sourced span. Tenant-authored spans are never cut.
- F6 Resolve the number conflict in policy: numeric novelty is enforce only inside trip-attribute frames, built by code from the FactSheet day lines and the PROMISE_FRAME tripwires, and warn elsewhere. Add the 1937/1992/0.4% F9 examples and the F1 '12'/'900' examples as twin fixtures.
- F7 Measure the tripwires (TRIP_RE, CONCRETE_TRIP_RE, PROMISE_FRAME_RE) in W2 like every other detector. They can promote a claim to blocking in C3 but are missing from the W2 detector list. Until measured, a tripwire may only send a sentence to C2 and never decide a hold by itself.
- F8 Reorder T9: before W2 R1, create calibration material for entailment mode. Option one is a cheap code alignment of each CL-1 sentence to FactSheet line ids, with the alignment checked by the panel. Option two is a 3-5 piece paid tagged-writer sample under its own small cap. Calibrate entailment and extraction as separate instrument ids. W4 flips only the mode and classes that passed. Add post-asserts '0 [F:]/[R:] tokens in stored and delivered text' and 'tag coverage >= X% of sentences the code fact detector marks factual'.
- F9 Compile the writer-prompt policy sections in W1 too, but only the contradiction-resolving lines (CTA, meta band, background, meals). Prove them with a 3-piece smoke per writer (about $0.50) rather than waiting for W5. Otherwise change the W1 proof from '0 of 16' to '0 of the code-vs-code contradictions' and list the writer-vs-code ones as open until W5.
- F10 Add an A3 input check to W1/W2: precision of a3_place_card_check and a3_atomize on about 30 sampled atoms and cards, labelled by the same panel, and the share of the T9 FactSheet that rests on unanchored atoms. Unanchored atoms are never sole support for a PASS (the plan's wording 'never sole support for a hold' is inverted).
- F11 Define the stable finding key (class + sorted evidence_ids + normalized claim span hash) and test it across splice_checked edits, before the stop rule ships.
- F12 Before W5, add a $0 power check from R1 vote variance and stored SWC: the minimum detectable dSWC at the planned n. Set a fixed absolute non-inferiority margin in the pre-registration, not one derived from A' noise. Budget arm A at full writer cost (config_fp will not match), and update the W5 caps on the decision page.
- F13 Add a review-capacity decision for A1: who reviews REVIEW rows, the weekly throughput, what happens to the 891 active pending_review Masters (keep active with a flag, or demote the ones whose W1 REPORT-mode final_contract fails), and whether T2/T9 may consume a flagged Master.
- F14 Label protocol: the 20% audit is a random sample of panel-AGREED items with the panel error rate reported; disputes go to the tech lead. Budget the adjudication from the observed 0.351 panel-vs-final agreement, not 60 claims. Labels with panel-only provenance never count as release evidence.
- F15 Observability: store all failing gates per attempt (not only the first held_reason), and split 'judge unavailable / treated as fail' and TEXT_INTEGRITY out of F9, so the baseline frozen in W0 is not inflated by infrastructure failures.

## Quyết định cần tech lead chốt

Trang bấm chọn: https://claude.ai/artifact/YZzbttV86QkzHssvsfkAbd (đã chốt A cả 16). Danh sách gốc ở `data/design-review.json` → `arch.decisions`, cộng 4 câu phản biện thêm (hiếm/lâu đời, phù hợp/an toàn, dựng cảnh, luật dữ liệu cho judge ghim trên OpenAI API).

## Mục tiêu chất lượng đo được

- Policy: 1 source file; policy_sha identical in 100% of rendered prompts, rubrics and route rows; 0 hand restatements (lint); 0 of the 16 listed T9 contradictions remain; 1 meta band and 1 title band in code
- Gate honesty: 0 classes in enforce/hold mode without a passing measurement record. Deterministic detectors: P >= 0.90, Wilson-95 LB >= 0.75, n_pos >= 15, labeller agreement >= 0.7. LLM instruments: P >= 0.90, LB >= 0.80, n_pos >= 20, test-retest >= 0.95, hard-subset recall 10/10 (today 20/20 thresholds calibrated:false)
- Exit integrity: 100% of save/publish/END paths pass final_contract (topology test); stored text sha == gated text sha on 100% of objects; post-gate edits = 0
- Contract cleanliness in stored text: 0 violations of CTA x1, FAQ 0 or 3-4, title/meta in band, slug at a word boundary, day count = source, meal/overnight lines byte-equal to the fact sheet, forbidden words 0
- Fidelity: 0 unsupported trip activity/service/time/view claims in delivered text, by the verifier and in a human read of 10 pieces per writer change; S1 serious-error rate no worse than the v2 baseline of 0.0015 per sentence; day loss 0
- Claim instrument: over-strict flags cleared >= 85% (today 25-26/46); <= 2 leaks per exempt type (V2a: 19); 0 hold verdicts from a non-pinned rung; degraded share < 5% while the pin is reachable
- Eval instrument: item kappa >= 0.6, recall_pass and recall_fail >= 0.75, mutant recall >= 0.90 with clean originals unchanged, GATE within 0.1 of CAL; R2 paired == planned on every run (today 0/15); writer $ spent after a failed calibration = $0 (today $2.37); null run (B == A) non_inferior
- First-pass yield (no enforce-class violation at the first write): T9 blog >= 30% floor, 50% target (today 4/187); T2 median writer calls 1, max 2
- Bounded cost and requests: T9 median <= 5 and worst <= 8 requests per blog (today worst about 38, INFERRED), $/delivered blog <= $0.25; S1 worst <= 12 requests, $/tour <= $0.065 (today about $0.075); T2 worst <= 8 requests (today about 96), $/version median <= $0.10, hard cap $0.25; elephant policy_hold $0 LLM
- Routing transparency: 0 silent model downgrades (today 3/3 Sonnet 5.5 empty cuts fell to 4.6 unmarked); 100% of calls stamped with answered model, rung and effort; 0 writer/judge same-family pairs in production; writer cut waste < 5% of writer spend (today $0.98 of $2.71)
- Replayability: 100% of new-object LLM calls have a cassette with the raw reply; R0 rerun diff = 0; 0 cassette misses counted as a pass; FactSheet verify_pointers bad == 0 and every excluded fact has a reason
- Change control: config_fp moves on any route/effort/params/mode/policy/prompt/memory change (unit test); 100% of gated PRs and migrations carry a matching-tier eval token or break-glass reason; 0 writing-memory activations without replay; reruns of the same candidate + fingerprint without a recorded change = 0
- Ground truth: CL-1 >= 60 tech-lead-adjudicated claims + 10 pieces with a frozen 30% held-out split; L2 40-60 S1 v2 tours; t2@2 >= 12 pairs (>= 4 pass, >= 4 fail) + about 150 sentence labels; 0 internal label contradictions; 0 stub labels; >= 20 mutants per writer
- Review queue (S1/T2): 100% of review rows carry a typed reason code; S1 review rate excluding POLICY_HOLD no higher than today; no item older than 7 days without an owner alert
- Measurement: all metrics per workflow and per channel (blog vs LinkedIn), with every failing class per attempt; unanchored-atom share and master_drift rate reported each run

## Lộ trình (wave)

### W0 Stop waste and make the truth visible (shared foundations, no output change except declared interim diffs)

- Gateway: the gateway becomes the single owner of the same-model truncation retry (empty or cut reply at max_tokens retried once at 2x on the same model, retry_reason recorded). token_budget becomes a ceiling calculator. Add a CI lint: every ceiling >= token_floor(model, effort).
- Gateway: degraded marks for judge, validate and decide roles too (extend _note_fallback_write, client.py:864-873). Bind family_rule.trace_models per call in the S1, T2 and T9 jobs. A same-family pair, rung > 0 or nova-lite on an instrument gives degraded.
- Routes (one migration with a '-- break-glass: remove uncalibrated rungs' header): t9_write = sonnet-5-5 -> sonnet-4-6; gpt-6-luna-openai off the t2_generate chain (degrade_mode queue_retry); nova-lite off t10_judge, t2_judge and the eval route. The acc3 rungs known to refuse go behind the existing refusal circuit.
- Cassette recorder in record-only mode: raw replies, request and prompt shas, answered model, rung, effort, linked to the ledger id and the owning object. Needs a CIS table, so an Infra migration with independent agent review.
- Interim T9 F9 (declared diff): hold only on a quoted, unsupported trip activity/service/time/view with why_not_in_source; every other class warns. Attempt 3 becomes a code truth_cut with no paid call.
- Interim T2: the judge becomes report-only for status (status from validate + T3 hard codes); T3 full-graph rounds, Jev tie-break, median-of-3, the revalidate judge and the nudge are turned off; the hitl exit is closed; t2_dashes moves before the final check; the master quality_score fallback is dropped; elephant policy_hold v0 (master verbatim, 0 LLM, review row).
- Interim eval: R2 controls are paired on (sample_id, input_sha256); R2 is refused at $0 when calibration is missing or paired < planned; the judge is pinned (model_key + connection in judge_version, mixed judge = invalid); the cost estimate comes from the ledger; after() keeps the verdict of a finished run; prompt_version_mismatch is computed in reverify.
- Widen config_fp (releases.py:446) to every route row on each path, stage_model_params, mode flags, rendered prompt shas, writing-memory items and L0 sha; stamp answered_model and fallback_used on every write. Writing-memory L0 becomes warn-only.
- Funnel SQL + nightly watchdog (per workflow and channel, every failing class per attempt, rung share, $ per delivered object), frozen as the baseline.

- **Proof:** Free. Unit tests red on base, green on the branch:
- an empty cut is retried on the same model;
- a judge rung > 0 is marked degraded;
- a same-family pair is marked;
- a migration-381-style effort change moves config_fp;
- an R2 with no calibration makes 0 writer calls;
- two golden versions pair all planned items;
- the T2 hitl path reaches the checks;
- 'elephant riding' in an itinerary gives policy_hold with 0 LLM calls.
A container dry run of R2 gives paired == planned (today 0/15). Then a 3-object smoke per workflow on synthetic audit tenants (about $0.75 total): every call has a cassette and an answered model at the pinned rung, with 0 silent model swaps.
- **Cost:** $0 code; about $0.75 smoke

### W1 One policy, one FactSheet, one exit (free; the tech lead clicks the decision page first)

- Decision page: place background, brief, reflection, hypotheticals, meta/title band, truth_cut for tenant content, pinned instrument, elephant default for T2, label budget, paid caps, s1_judge off the live path. writing_policy.yaml v1 is frozen from the answers.
- writing_policy.yaml + compiler + lint. The eval rubric, LABEL_RUBRIC, RulesConfig and route rows switch at once. Writer-prompt fragments stay byte-equal until W5, which avoids an unmeasured writer change. The eval judge loses its 16000/9000 truncation and reads evidence_view.
- Contradiction fixture suite generated from the policy examples: about 10 fire/no-fire twins per topic (background, timing, rarity, CTA, FAQ topic, numbers incl. word numbers, scope, meta band, slug boundary, meals, day count). It runs through every fixer, gate and apply_rules.
- FactSheet module with a tour builder and a route builder, as a parity refactor. render() is byte-equal to today's grounding_text_from. The deterministic budget order with recorded exclusions is a declared diff. Then persistence (a CIS table + fs_id on generated_content, content_piece.writer_input and tenant_tour_versions; risky migration with agent review). The T2 _PT_SQL gains the raw inclusions/exclusions/itineraries/highlights/price/agency fields.
- final_contract in REPORT mode wired to ALL exits of S1 (done, hitl, revalidation, resumed, promote, server approve), T2 and T9, with the topology test. In T9 the post-loop edits fold into the normalizer, with a stored sha == gated sha assert.
- Input measurements: share of unanchored atoms, pointer failures, excluded facts per object, and the master_drift census over about 892 Masters.

- **Proof:** Free CI and replay:
- 1 policy_sha across all artefacts; 0 hand restatements; the 16 listed T9 contradictions -> 0; 1 meta band in code;
- contradiction suite 100% as the policy expects;
- verify_pointers == 0 on all 943 active sources;
- render parity 100% before the budget diff;
- the REPORT-mode final_contract over stored v2 Masters lists Japan 12->4 and Rajasthan 15->10 in its publish-flip list;
- the master_drift blocking rate is reported (if it is above 15%, tune the provenance rules before W3).
- **Cost:** $0

### W2 Ground truth at claim level and instrument calibration (free labels, then cents)

- shared.eval_claim_label table + the 'golden_claim' disagreement source. Revoke the t9b-002 stub. Strata and hash splits. The private Dev DB is the master copy, with a manifest in the root repo.
- CL-1 (T9 blog + social): seed from the S232 127 claims, a stratified sample of the S234 565 V2 flags and the 18 golden blogs. 3-lens agent panel. The tech lead adjudicates about 60 claims and 10 pieces. 30% frozen held-out split.
- L2 (S1 v2): 40-60 stored v2 tours, stratified (length > 10 days, meal-heavy, no day markers, elephant, Optional-heavy). Sentence and field labels from a 2-pass panel; the tech lead approves.
- t2@2: >= 12 pairs (>= 4 pass, >= 4 fail) + about 150 sentence labels.
- Mutation suites per writer (about 50 clean texts x 8 classes) and code-injected MUTANTS strata.
- Deterministic detectors measured on the labels (meal/clock regex, elephant, day codes, novel numbers, Optional, meta band, T3 lexicon, F1/F12/F17/F18); thresholds.yaml rows filled in, gate modes derived.
- R1 (judge-only, 3 votes, pinned): the claim engine on gpt-6-luna-openai@openai-direct, plus one acc2 non-Claude model if available; the production F9 config, the S1 judge, the T2 voice assessor and Jev a1_claim_supported on T2 pairs. Every LLM gate with no passing record becomes warn-only.

- **Proof:** Free for labels; R1 under $2 in total (the S234 V2a measure was $0.1055 per 76 calls).
- Label sets have 0 internal contradictions; per-class agreement is recorded.
- Mutation recall >= 0.95 on structural/number/inclusion/meal classes and >= 0.8 on names/service words; false findings <= 5% of clean sentences.
- An instrument passes only at P >= 0.90, LB >= 0.80, n_pos >= 20, test-retest >= 0.95, hard-subset recall 10/10, over-strict cleared >= 0.85 (today 25-26/46), <= 2 leaks per exempt type.
- The eval instrument also needs kappa >= 0.6 and recall_pass/fail >= 0.75.
- If no instrument passes after 2 frozen DEV-only policy-text revisions: stop and add human labels. No paid R2.
- **Cost:** $0 + <= $2 judge-only; about 2-3 h of tech-lead adjudication over 1-2 weeks

### W3 Rewire the control planes in place (free replay; declared diffs only)

- T9: route_table as a 0-diff pure refactor of the ~9 routing sets, then the declared diffs: stop rule, generalised truth_cut, stable-key regression guard, verdict cache (F9PassMemory removed); seo_builder + word-boundary slug (the 2 SEO-fit calls removed); FAQ answerable set in the plan with faq_filter rank-only (t9_faq_answer_fit removed after checking the live flag value); pre-spend duplicate and angle tripwire checks.
- S1: contract_check + class router replace validate scoring and should_retry; source_gate on; final_contract switched to enforce for the codes that passed W2; rule 7 -> code fact lines (byte-identical prompt otherwise); meta candidates -> fit -> template; local_fix replaces flag_fix and _rerepair_meta; grounding units widened to name, trip_type and seo fields with FS slices; no Jev waiver of deterministic findings; s1_judge off the live path (Writing Lab sampler); typed review queue; approve/edit/promote through final_contract; blanket truth stamp removed; build_graph_from_generated refused for A1.
- T2: the linear orchestrator behind the T2 profile row (bundle -> policy_route -> compose_slots -> one write -> normalize -> verify -> route -> local repair / field regen -> select_best -> voice report -> final_contract -> save), with VersionBudget and resume-from-best, and compiled writer/repair prompts.
- Eval: R0b PieceStore seam (production input builder, dry store) for T9, then the S1 and T2 dry stores; R0a cassette re-score in CI.

- **Proof:** Free full-chain replay over fixture-1.2.0 (15 blog + 15 LinkedIn), the 18 golden blogs, about 892 stored S1 v2 Masters, L2, and stored T2 versions (mostly sonnet-4-6 + v1).
- 0 undeclared diffs; 0 cassette misses counted as a pass.
- stored sha == gated sha on 100%.
- Post-assert sweep: 0 violations.
- F4_seo, F6 and F16 holds = 0 by construction.
- 0 PUBLISH pages carrying an enforced code; the elephant deadlock test passes.
- Scripted fake-LLM path tests (clean, repair, regen, budget out, judge error, writer fallback, policy_hold) all reach final_contract; writer calls <= 2 including a simulated job retry.
- Repair replay with recorded bad outputs (forbidden word written back, day dropped, number added) is reverted 100%.
Then 3-tour/3-piece smokes per workflow on the pinned route (about $1 total): abort on any off-pin answer, slot break or cut.
- **Cost:** $0 replay + about $1 smokes

### W4 Promote the calibrated claim instrument (cents shadow, then live)

- Claim engine in shadow beside the interim T9 F9 and the T2 shadow verifier, on cassettes of recent objects and audit-tenant writes. The tech lead labels about 30 disagreements, which go into CL-1 / t2@2.
- Flip T9 holds and T2 status to the claim engine for enforce-mode classes only. Retire the old F9 judge prompt and route row. LinkedIn unsupported_trip_promise -> cut (route row change).
- S1: Q-promise (a1_promise_unsupported) is promoted only if its record passes; otherwise it stays shadow.

- **Proof:** Cents: shadow < $0.30, mostly from the cache.
- The new instrument is right in >= 80% of the sampled disagreements with F9.
- 100% of held/needs_review classes are enforce-mode classes in thresholds.yaml.
- Degraded share < 5% while the pin is reachable.
- 0 hold verdicts from a non-pinned rung.
- **Cost:** < $0.50

### W5 Paid writer proof (small, after an explicit yes per item, under the decision-page caps)

- Eval null run first: t9_blog release 0 (B == A) on GATE, 12 items. It must come out non_inferior with paired == n, 0 mixed judges and 0 HS1. A false regression blocks every B.
- T9 writer contract: compiled policy section incl. F17/F18, tagged prose, 3+3 header, FAQ keyed to q_ids. 3-piece smoke, then a fixed 12-15 blog sample with arms A (stored finals at matching config_fp, $0 where possible) / B / A' (noise on 6-8 items), full loop.
- S1: 3 tours (sub-day, meal-coded multi-day, elephant), then 25 held-out golden + 25 stratified tours (Japan, Rajasthan, source contradictions, Optional-heavy). Current vs new graph on the same pinned route and effort; blind 2-pass panel at $0 with pre-registered criteria.
- T2: 20 synthetic-tenant tours (>= 2 elephant, >= 3 thin-source). v2 effort high vs medium; control = stored v1 re-scored by the verifier at $0; blind pairwise voice preference on 10 tours.
- A 5-pair human preference check on any winning B (anti-bland), before the profile/route flip is recorded with its eval_run_id.

- **Proof:** Pre-registered per workflow (see quality_targets).
- T9: first-pass yield >= 30% (target 50%); median requests <= 5; 0 contract violations; 0 unsupported trip promises in a human read of 10 pieces; writer cut rate < 2%; $/delivered blog <= $0.25.
- S1: serious-error rate no worse than the v2 baseline (0.0015 per sentence; bootstrap upper bound of the difference <= +0.003); day loss 0/50.
- T2: enforce findings 0 after repair and <= 25% of the v1 control; writer calls <= 2; $/version median <= $0.10.
Any failure keeps the current writer prompt on the restructured graph, and the run is stored as evidence.
- **Cost:** Recommended caps: eval null run <= $5, T9 <= $15, S1 <= $8, T2 <= $5; total <= $33 (the card pays OpenAI/Anthropic direct; acc3 credit cannot serve Claude 5.x)

### W6 Lineage, cleanup and permanent change control (free, then ongoing)

- A3 atoms from FactSheet entries, each with a quote that must be a substring of raw_tours. a3_atom_in_text stays warn. The T2 grounding baseline = FactSheet (Master is the style reference only).
- Delete the dormant or replaced code and routes: T9 seed_align tier 2, t10_adjudicate, brief_grounding, reader_checklist and the separate t10_claims stage (unless promoted with a number); S1 flag_fix and s1_brand_audit LLM; the T2 v1 branches in graph.py, T2 flag_fix, revise_block and t2_judge_tiebreak; drop their routes by migration.
- The migration/CI lint ('-- eval:' or '-- break-glass:' per tier) becomes required in CIS and Infra; paths.yaml required; runtime route and memory edits are frozen during waves.
- Writing memory as policy-overlay proposals: activation needs R0b + R1, plus R2 when it changes a writer prompt.
- Monthly: relabel 10 new objects per workflow from the review queue and the disagreement queue, and re-read gate precision.

- **Proof:** Free:
- replay shows 0 diffs after the deletions;
- a grep shows 0 live paths for deleted stages;
- a seeded-regression PR (meta band widened in policy; LLM fact line re-enabled) fails CI and its revert passes;
- a synthetic route migration with no eval header fails the lint;
- the watchdog returns 0 alerts on a clean week and fires on a seeded off-pin row;
- run_write_background is <= 300 lines (from about 750).
Then the S1 wave ladder (3 -> <= 50, per aa-wave-rerun) with the route pinned and a cost per stage report.
- **Cost:** $0; atom re-run about $0.05 per 3 tours

## ADR cần viết

- Root ADR 0020 (new): 'One writing-quality architecture: policy registry, FactSheet, measured gates, single exit contract'. Root level because reversing it touches CIS (all writers, Writing Lab), AA-CIS-Infra (cassette, FactSheet and claim-label tables, migration lint) and the root data standards. It covers: writing_policy.yaml as the single policy source; gate mode derived only from measurement records with the two promotion bars; verifiers vs assessors (assessors report-only); final_contract as the only exit; tenant content truth_cut while held stays a label; the shared claim engine used by both production and eval. Implements root ADR 0001 and cites ADR 0009.
- Root ADR 0009 amendment (gateway): the gateway is the single owner of the same-model truncation retry; degraded marks for every role; per-call family check in production; pinned single-rung 'instrument' routes (a miss = unverified, no fallback verdict); the cassette recorder and its retention; no writer route may contain the verifier's family. Amends decision 12 (family rule) and CIS ADR 0005 decision 4 wording.
- Root data-standards change (DM-10.x / DM-11.x): config_fp contents and stamping; the migration header rule '-- eval: <run_id>' or '-- break-glass: <reason>' on llm_role_config / stage_model_params / gated prompt changes; cassette and claim-label storage only in the private Dev DB (public-repo rule).
- CIS ADR (new): 'Writing Lab evaluation ladder'. R0a/R0b/R0c/R1/R2 tiers, pairing on (sample_id, input_sha256), refusal at $0 before writer spend, A/A'/B with a null run first, claim-level ground truth with DEV/CAL/GATE hash splits, measurement of production LLM gates by R1. Amends CIS ADR 0010 (governed writing memory): L0 is warn-only and activation is gated by R0b + R1 (+ R2 for writer prompts).
- CIS ADR (new): 'S1 control plane'. Persisted FactSheet, contract_check routing instead of quality_score, local source-aware repair replacing flag_fix / _rerepair_meta, source_gate, s1_judge off the live path, typed review queue with POLICY_HOLD, A3 atoms from the FactSheet.
- CIS ADR (new): 'T2 as its own linear orchestrator'. Raw-row SourceBundle with master as voice base and master_drift marks, code-composed slots, one writer call, VersionBudget with resume-from-best, the elephant policy_hold default, one versioned T2 profile row replacing the env flags.
- CIS ADR amendments for T9: CIS ADR 0011 (the t9 FAQ question filter becomes rank-only inside the code-decided answerable set; t9_faq_answer_fit removed) and CIS ADR 0009 (F17 offered moments: F17/F18 become claim-engine rules that fire only when the cited lines lack the item).

## Kiến trúc đích (English, from the architect)

# Target architecture: one writing-quality system for S1, T2, T9 and the Writing Lab

Status: proposal for the tech lead, S271, 06/11/2026. It is based on four design reviews (blog, S1, T2, eval) and spot checks at CIS f7d310db.
Verdict for all four workflows: **RESTRUCTURE in place**. This means no parallel v2 graph, except T2: T2 is a set of `is_tenant_rewrite` branches inside the A1 graph and gets its own small linear orchestrator.
What is reused unchanged:
- the gateway and ledger
- writer v2 (S1)
- the T8 angle contract with Jev rank and human pick
- choose_keyword
- sentence-level, source-cited repair with splice_checked / repair_contract
- the deterministic finalizers
- the degraded registry
- the release evidence gate
- Q0 CI
- tenants always receive content

## 1. Why fixes loop (common root cause, VERIFIED in all four reviews)

1. **Policy has no single source.** It is restated in ~10 places per workflow, with 4+ meta bands. Each fix lands in one copy and contradicts another.
2. **Facts have no single source.** Writer, gates, repair and eval judge each see a different, silently cut version of the source. In T2 that source is lossy master prose with "Inclusions: None".
3. **The deciding signals are unmeasured.**
   - T9: an uncalibrated, unpinned F9 judge decides 34/99 holds and is answered by its 3rd rung.
   - T2: a source-blind brand judge drives status and retries.
   - S1: a saturated score (avg 9.99) cannot fail.
   - Writing Lab: the eval judge has kappa -0.07..0.32 on 1 human label.
4. **Repair is global or source-blind, and the detector that fired is not re-run.** One example is S1 flag_fix and revalidate (graph.py:1397-1398).
5. **Exits do not share one contract.** S1/T2 hitl goes straight to END, and T9 edits text after the last gate.
6. **Behaviour changes outside eval.** Routes, effort, env flags and writing memory all change it, and no replay is fake-proof: replays reuse stored F9 verdicts.

Every new failure therefore became one more gate or one more fixer.

## 2. Layers

```
L8 Change control   config_fp | migration lint (-- eval / -- break-glass) | eval tiers | writing-memory gating
L7 Record + replay  cassettes | manifests | findings vectors | R0a/R0b/R0c | R1 | R2 (A/A'/B, null run) | mutation suites
L6 Exit             final_contract (read-only, the one exit) -> status + typed review queue
L5 Route + repair   route_table (from policy) | repair operators | budget | stop rule | truth_cut
L4 Verify           contract_check (code) -> claim engine C2 (pinned instrument / Jev for A1) -> C3 code confirm -> C4 2nd vote
L3 Compose          slot composers (fact lines, day skeleton, inclusions, seo_fields, slug, CTA, FAQ plan) + one ordered normalizer
L2 Evidence         FactSheet (one schema, tour + route builders, persisted, fs_sha) + evidence_view renderer
L1 Policy           writing_policy.yaml -> compiler (prompts, rubrics, RulesConfig, route rows) | thresholds.yaml measurement records -> gate modes
L0 Gateway          one LLMClient + ledger | pinned instrument routes | same-model truncation retry | role-wide fallback marks | per-call family check | cassette
```

**Data flow.** raw source -> FactSheet (persisted, fs_sha) -> content plan / slots (code) -> ONE writer call, narrative only, through the gateway -> compose + normalize (code) -> contract_check + claim engine (same FactSheet) -> route table -> local repair on flagged spans -> re-verify changed units -> final_contract -> save. The tenant always receives the text; for T2/T9 the reader is protected by truth_cut of residual enforce-class promises. Last comes the record: cassette, findings vector and config_fp.

**Two kinds of judge.**
- **Verifiers** (claim engine, Jev a1_claim_supported) may hold, but only with a passing measurement record and a pinned instrument.
- **Assessors** (S1 brand_fit, T2 voice, T9 F9_brand_style / F15) are report-only. They never route, retry, select or hold until kappa >= 0.6 on labelled pairs, and they live in the Writing Lab.

## 3. Key cross-cutting rules (resolving conflicts between the four picks)

| Topic | Blog pick | S1 pick | T2 pick | Eval pick | Resolution |
|---|---|---|---|---|---|
| Policy file | writing_policy.yaml | services/quality/writing_policy.yaml | policy rows | services/quality/policy.yaml | **one file `services/quality/writing_policy.yaml`**; taxonomy.yaml keeps class ids/definitions rendered from it |
| Calibration record | measurements.yaml | thresholds.yaml fields | taxonomy blocks | eval_judge_calibration table | **thresholds.yaml rows** for gate modes (already has the calibrated fields, 20/20 false VERIFIED); `shared.eval_judge_calibration` DB rows for instrument runs, referenced by run_id. No third file. |
| Promotion bar | P>=0.90, LB>=0.80, n>=20 | P>=0.90, LB>=0.75, n>=15 | P>=0.90, n>=15, agreement>=0.7 | claim precision>=0.70 + kappa | **Deterministic detector: P>=0.90, Wilson-95 LB>=0.75, n_pos>=15, labeller agreement>=0.7. LLM instrument (hold-capable): P>=0.90, LB>=0.80, n_pos>=20, test-retest>=0.95, hard-subset recall 10/10. Definitional classes: Q0 red-on-base proof. Eval R2 instrument: kappa>=0.6, recall_pass/fail>=0.75, mutant recall>=0.90, GATE within 0.1 of CAL.** |
| Fact source | FactPack from grounding_text_from + s1 anchoring | persisted FS from s1_facts | SourceBundle raw + master_drift | FactSheet wrapping both | **one FactSheet schema and module, two builders, one persisted row**; T2 adds BASE + master_drift; eval uses evidence_view() |
| Writer output | prose + [F:]/[R:] tags + 3/3 header | W unchanged, code appends fact lines | narrative slots JSON + 3 meta candidates | n/a | **One principle: code owns constrained slots, the LLM writes narrative only, bounded fields come as candidates.** The shape stays per workflow (tagged prose for T9, W prose for S1, slots for T2), to keep voice risk low. |
| Claim verifier | pinned t10_verify entailment on cited lines + V2a for untagged | Jev a1_claim_supported + Q-promise shadow | code verify + LLM t2_verify shadow | E1-E4 extractor + code confirm | **One claim engine module (C1-C4).** One pinned non-Claude instrument for T9/T2/eval. Jev stays C2 for A1 only (already calibrated on A1, keep-Jev rule). |
| Eval judge vs production verifier | n/a | n/a | n/a | same engine | Same engine and instrument (narrow non-Claude pool). Independence comes from claim-level human/adjudicated labels and the C4 second vote, never from the instrument agreeing with itself. INFERRED risk, accepted; recorded in the ADR. |
| Truncation retry owner | gateway | gateway | gateway | n/a | **gateway**; token_budget becomes a ceiling calculator only |
| Loop bounds | 2 repair rounds | 2 drafts, 1 repair round | writer<=2, repair<=3 | n/a | per-profile numbers in policy: writer<=2 (2nd only for structural regen), repair rounds S1=1 / T2=2 / T9=2, round 2 only on strict shrink, budget persisted across job retry |
| Product consequence | truth_cut, held = label | review queue (A1 is not tenant-facing) | needs_review shown as ready | n/a | A1: review queue blocks publish of the Master. T2/T9: tenant receives, residual enforce-class promises are truth_cut by code, held/needs_review = label only (decision D6). |

## 4. Final graph per workflow

Legend: [C] code $0, [L] LLM through the gateway (pinned/stamped), [J] Jev, [H] human. Every node writes findings + hashes to the record.

### 4.1 S1 platform tour rewrite (A1 Master)
```
ENTRY admin rewrite | wave | resumed   (batch-seed v1 entry build_graph_from_generated refused for A1)
[C] N0 FactSheet(tour builder) persisted; reuse if source_hash unchanged; verify_pointers == 0
[C] N1 source_gate: DAY_COUNT_VS_DURATION on SOURCE (independent of day_parse), empty itinerary, SOURCE_DAY_CONTRADICTION,
       elephant wording over all fields -> SOURCE_HOLD (enforce only after precision read) | POLICY_HOLD flag | ok      ($0 writer spend on hold)
[C/J] N2 seo_prefetch (unchanged)
[L] N3 writer v2 W (pinned route/effort/release; literals from policy; rule 7 -> "do not write a fact line";
       empty cut -> same model 2x; fallback writer = DEGRADED)
[C] N4 compose: per-day verbatim fact lines, Optional label, forbidden strip, title fit
[L] N5 meta candidates (sees FS) -> [C] band pick | fit | template(FS)   (meta never blocks; <=1 retry)
[C] N6 contract_check -> classes REGENERATE | LOCAL | POLICY_HOLD | REPORT  (quality_score = report column only)
    REGENERATE and drafts<2 -> N3 with code-built feedback; exhausted -> N9
[C+J] N7 grounding: units incl. name/trip_type/seo_title/seo_meta, unit source = FS slice; fail-closed novel numbers;
       Jev a1_claim_supported pinned version; no Jev waiver of deterministic findings; Q-promise shadow
[C->L] N8 local_fix (replaces flag_fix + _rerepair_meta): deterministic edits -> 1 grounding.repair call on enforce-flagged
       sentences with FS quotes -> code delete only for deterministic findings if field keeps >=1 sentence;
       repair_contract after each edit; re-run N6+N7 on changed units; no 2nd round
[C] N9 final_contract (ALL exits: done, hitl, drafts exhausted, resumed, human edit, server approve, promote)
    -> PUBLISH | POLICY_HOLD | REVIEW(codes) | SOURCE_HOLD | DEGRADED
PUBLISH -> Master (fs_id, contract result, config_fp) ; else typed review queue (reason codes, owner, 7-day age alert)
[H] A2 approve re-runs N9 server side; override needs a reason code; POLICY_HOLD approved as policy_keep (exempt from
    human_edit_gate); sentence labels only for reviewer-marked sentences (blanket truth stamp removed)
[L/C] N10 A3 atomize from FS entries with a quote that is a substring of raw_tours (code-enforced); T2 baseline = FS
OFF LIVE PATH: s1_judge -> Writing Lab sampled pinned assessor (~20 tours/week); s1_brand_audit LLM, s1_source_facts,
    itinerary nudge deleted
```

### 4.2 T2 tenant tour rewrite (own linear orchestrator in services/quality + jobs, behind a profile row, then the default)
```
job wrapper (KEEP) + VersionBudget persisted {writer<=2, repair<=3 calls/2 rounds, verifier<=2, voice<=1, usd<=0.25}; retry resumes best candidate
T1 [C] SourceBundle = FactSheet(raw row incl. inclusions/exclusions/src_itineraries/src_highlights/price_raw/agency) + BASE master prose
       (voice only) + master_drift 'do not carry' (human-edited master = source, provenance=human) + brand pack + cached SEO + policy_sha
       + frozen writing-memory release id; policy_mode via elephant detector on raw+master
T2 [C] policy_hold -> master verbatim + deterministic brand fields, 0 LLM (D8) -> T6 -> T7 -> T10
T3 [C] compose_slots: day skeleton, Overnight/Meals lines, at-a-glance, inclusion/exclusion lists, slug, keyword set (immutable)
T4 [L] t2_generate ONE call, sonnet-5-5, ceiling from token_budget, effort pinned; narrative slots + 3 title + 3 meta candidates;
       writer chain has no OpenAI rung (queue_retry)
T5 [C] merge   T6 [C] normalizer (forbidden + tenant layers, dashes, seo_fields pick/fit, integrity) before EVERY verify
T7 [C] contract_check(t2 profile) incl. run_checks, T3 lexicon, meal/clock outside slots, slot equality, isolation, brand_claims(report)
T7b [L] claim engine on residual promise class (activity/view/time/service): SHADOW until the T2 measurement record passes;
       Jev a1_claim_supported accept-only clear: SHADOW until recalibrated on T2 pairs
T8 [C] route_table: enforce span findings -> 1 haiku t2_repair call over all flagged spans + fact lines -> enforce_spans/fields +
       slot equality -> T6 -> T7 (max 2 rounds, strict shrink); struct.* -> 1 field-scoped regen; budget out -> truth_cut of residual
       enforce-class sentences (code) -> T9
T9 [C] select_best key (enforce_hard==0, enforce_count, inherited_master, warn_count, repairs_used)
T9b [L] voice assessor, pinned non-Claude, report-only (enters key only at kappa>=0.6 on t2@2)
T10 [C] final_contract -> status ai_generated iff 0 enforce findings, mode normal, no fallback writer, no 'unverified' enforced class;
       else needs_review (tenant sees ready); review queue reason codes; record bundle_sha, prompt shas, raw replies of ALL candidates
REMOVED: nudge, whole-field flag_fix, revise_block, Jev tie-break, median-of-3, revalidate judge, min(validate, judge), apply_a1_hold on T2,
       hitl bypass, T3 full-graph rounds, master quality_score fallback, ~10 env flags (-> one versioned T2 profile row)
Worst case 8 requests (today ~96, x2 on job retry)
```

### 4.3 T9 blog + social (in-place restructure of run_write_background)
```
T7 slate (kept) -> T8 angle + contract + Jev rank + [H] pick (kept)
[C] PRE-SPEND: subject/angle near-duplicate vs all tenants (F10 embedding+threshold, ~$0.001); angle tripwires vs FactSheet
    (brief = instruction, never support)
S0 [C] FactSheet(route builder): grows grounding_text_from + number_source_lines; per-tour s1_facts anchoring; atoms with no
    raw overlap = anchored=false (framing only, never sole support for a hold); deterministic budget order S,F,T,L > P > O with recorded
    exclusions (support_excluded = warn)
S1 [C] content plan: sections = moments with line ids; keyword = choose_keyword; FAQ = answerable set (q -> line ids) or section dropped
    by rule (<3); t9_faq_filter may only rank inside the set; CTA literal, bands, floors from policy
S2 [L] t9_write sonnet-5-5 -> sonnet-4-6 only (gpt-6-luna-openai removed); prompt policy section compiled (F17/F18 included, retired F3
    removed); output = header {title x3, meta x3} + prose with [F:id]/[R:id] on factual sentences + FAQ answers keyed to q_ids
S3 [C] compose + one normalizer (merges 12 fixers, SEO fit, FAQ regen, real_first_faq, stock/authenticity cuts, tag parsing);
    post-asserts CTA x1, FAQ 0|3-4 citing lines, title/meta in band, slug at word boundary, length >= floor (warn)
S4 [C] contract_check(t9 profile) -> [L] claim engine on unsettled sentences only (cited entailment; one narrow "activity/service/
    time/view of THIS trip?" for voice/place_bg; extraction for untagged legacy) -> [C] confirm; cache replaces F9PassMemory;
    non-pinned rung / nova-lite / same family = degraded (cannot approve or hold); F9_brand_style / F15 warn -> Writing Lab
S5 [C] route_table: recite | cut | repair_sentence (haiku, +-2 neighbours + cited lines -> splice_checked) | regenerate_section |
    rewrite (only invalid reply / F0 / extreme length, max 1); max 2 rounds on strict shrink; then truth_cut -> post-asserts
S6 [C] final_contract: stored text sha == gated text sha (no post-loop edits); status approved | held(ALL classes) | degraded;
    tenant 'ready' kept; publish gate kept (subject 409, unserved tour, content_compliance_flag)
S7 record: cassette, pack, plan, per-sentence verdict table, config_fp
SOCIAL/LinkedIn: same S0, no FAQ, F14 shape asserts, unsupported_trip_promise -> cut before repair; metrics per channel
REMOVED: F9PassMemory, AA-528 attempt revert (-> stable-key guard), 2 SEO-fit calls, _enforce_faq_contract regen, t9_faq_answer_fit,
    post-loop edits, ~9 routing sets, dormant seed_align t2 / t10_adjudicate / brief_grounding / reader_checklist (unless promoted with a number)
Median <=5 requests, worst <=8 (today worst ~38, INFERRED)
```

### 4.4 Writing Lab evaluation (the test half)
```
POLICY (same file) -> [C] verdict_rule(confirmed claims, struct findings) -> pass/fail + severity-weighted count (SWC)
EVIDENCE evidence_view(FactSheet, labelled output fields); over cap -> item excluded (never cut); same sha for writer, panel, judge
GROUND TRUTH shared.eval_claim_label; strata HARD/REPRESENTATIVE/MUTANTS/TRAPS; splits DEV/CAL/GATE by hash(sample_id); t9b-002 stub revoked
INSTRUMENT = claim engine E1 contract_check -> E2 pinned extraction (no verdict field) -> E3 confirm -> E4 2nd vote on unconfirmed blocking
LADDER R0a cassette rescore | R0b deterministic replay (production builder, PieceStore seam) | R0c lexicon | R1 judge-only calibration
    (writes measurement record; also measures production F9 / S1 judge / T2 voice: no record -> warn-only) |
    R2-dev (cap $3, informative) | R2-gate: $0 refusals (calibrated id, paired==planned on (sample_id,input_sha256), ledger estimate,
    pre-registered decision, no same-fingerprint rerun, 6-item drift check) -> arms A (stored finals at matching config_fp, $0) / A' / B;
    full loop dry run; HS1 = new CONFIRMED trip-promise/checkable claim absent in A and A'; decision non_inferior/improve on dSWC vs 2*SE(A'-A)
KEEP release evidence gate (API 409 + CIS 287), release 0 no-op, rollback, post-activation check, KPI soft stops, disagreement queue
```

## 5. How write / judge / test fit together
- **Write**: the generator only writes narrative inside a plan whose facts, slots and bounded fields are fixed by code. The writer's prompt is compiled from the same policy that the gates enforce. First-pass yield becomes the main writer metric, instead of repair volume.
- **Judge**:
  - Deterministic contract_check first.
  - Then one pinned claim instrument that sees exactly the FactSheet the writer saw, with code confirmation of every quote.
  - Hold power comes only from a measurement record.
  - Assessors (voice/brand) report only.
- **Test**:
  - Every change runs the cheapest tier that can falsify it, before anything paid: R0 free, then R1 cents, then R2 paid with a null run first.
  - Replay never trusts stored LLM verdicts.
  - config_fp makes every route, effort, prompt, policy or memory change visible, and the lint makes it gated.

## 6. Invariants (enforced by tests/lints)
1. One policy_sha across all rendered artefacts; 0 hand restatements (lint).
2. Every consumer reads the FactSheet by fs_sha. evidence_view parity: no silent truncation.
3. No gate in enforce mode without a passing measurement record (lint).
4. Every path to save/publish/END passes final_contract (topology test). Stored sha == gated sha.
5. A hold-capable verdict comes only from the pinned instrument rung. Any other rung is degraded.
6. No writer route contains the verifier's model family. A per-call family check runs in production.
7. Replay: a cassette miss = needs rejudge, never a pass.
8. config_fp moves on any route/effort/params/mode/policy/prompt/memory change (unit test). Gated migrations carry an eval or break-glass header.

