# Linear export

Closed Linear issues (Done / Canceled), plus every archived or trashed issue, with their comments, exported by `tools/linear/linear_export.py` before they are archived (Linear Free plan, S245). Generated — do not edit by hand; re-run the script.

| Issue | Title | State | Closed | Project |
|---|---|---|---|---|
| [AA-677](aa-booking-aaa-foundation/AA-677.md) | [AAA] ERD v2 — re-evaluate the Quanskill ERD and redesign it for the ecosystem (schema booking.* on acc2 RDS) | Done | 2026-10-11 | AA-Booking (AAA) — Foundation |
| [AA-176](acpv2-admin-tenant-split-a-t/AA-176.md) | [DEPLOY-01] Immutable image tags + ECS/Lambda safe rollout (rollback-first) | Done | 2026-09-04 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-177](acpv2-admin-tenant-split-a-t/AA-177.md) | [SEC-01] Container + Lambda image scanning + SBOM in CI (Trivy + syft) | Done | 2026-09-04 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-264](acpv2-admin-tenant-split-a-t/AA-264.md) | [ACP-Portal][SECURITY] Hardening — httpOnly cookie + Next.js middleware guard (từ AA-261) | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-279](acpv2-admin-tenant-split-a-t/AA-279.md) | [SEC-PIPELINE] Prompt injection surface — S0 brand brief .docx + S2 competitor content feed LLM prompts unsanitized | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-282](acpv2-admin-tenant-split-a-t/AA-282.md) | [OPS] schema_versions gap đợt 2 — migrations 043–050 không có trong log (AA-102 chỉ fix 027/029–034) | Done | 2026-09-04 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-310](acpv2-admin-tenant-split-a-t/AA-310.md) | [Infra] AA-295 Direction 3 — nới ECS stopTimeout để khớp với graceful shutdown drain (25s) đã merge | Done | 2026-09-24 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-318](acpv2-admin-tenant-split-a-t/AA-318.md) | [Gap thiết kế — chưa chốt] Không log nội dung prompt thật gửi LLM — chỉ log prompt_len, chặn khả năng verify bug liên quan nội dung prompt | Done | 2026-09-04 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-324](acpv2-admin-tenant-split-a-t/AA-324.md) | [COST/PERF] Prompt caching thật sự vô hiệu trên production — mọi call S1-old đi qua acc1 satellite, cache_control chỉ hoạt động trên acc2 Bedrock trực tiếp | Done | 2026-09-04 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-331](acpv2-admin-tenant-split-a-t/AA-331.md) | [ACPv2-N6] Ô reactive 10% → đổi thành buffer chạy lại slot HELD (Q5=C) | Done | 2026-09-03 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-332](acpv2-admin-tenant-split-a-t/AA-332.md) | [ACPv2-N7] Tầng 4 chống cannibalization — dedup pgvector cross-tenant cosine >0.92 trước publish (Q6=B) | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-342](acpv2-admin-tenant-split-a-t/AA-342.md) | [Platform] Rà soát ngược: cơ chế ghi trạng thái đã đánh Done nhưng chưa từng persist thật (ADR-2026-037) | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-344](acpv2-admin-tenant-split-a-t/AA-344.md) | Upload History: surface rows_landed/rows_dropped (not just parsed count) on /admin/upload | Done | 2026-09-04 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-348](acpv2-admin-tenant-split-a-t/AA-348.md) | [CIS-S1] Lệch version hằng số BEDROCK_SONNET (4-5) vs model thật gọi qua satellite (4-6) | Done | 2026-09-05 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-383](acpv2-admin-tenant-split-a-t/AA-383.md) | [acp-brand-brief-parser Lambda] INSERT branch thiếu brand_name — cùng lỗi NOT NULL đã fix ở create_tenant() (AA-309), Lambda chưa được vá | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-395](acpv2-admin-tenant-split-a-t/AA-395.md) | [ACPv2-N8][ADR-2026-030] Landing page engine — tự host trang giới thiệu tour per-tenant, ghi acp_deliver.tenant_tour_pages (quyết định 13/07 chưa từng lên issue) | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-406](acpv2-admin-tenant-split-a-t/AA-406.md) | [ACPv2][N7][Chờ Ms. Thư] F2 atom density (§1.6.1, CONTEXT.md) — chưa build trong ACPv2, cần xác nhận có còn cần thiết hay đã cố ý bỏ vĩnh viễn | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-428](acpv2-admin-tenant-split-a-t/AA-428.md) | [Bug] CatalogTab.tsx gọi /api/tenant/v1/quota không tồn tại — lỗi nuốt câm lặng | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-434](acpv2-admin-tenant-split-a-t/AA-434.md) | [STEP0] Audit theo dõi usage LLM theo tenant + T-stage — đã có chưa, liên quan AA-118/AA-258/AA-255 | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-435](acpv2-admin-tenant-split-a-t/AA-435.md) | [SECURITY] Admin login JWT lộ qua JSON body + cookie không httpOnly — cùng họ AA-427, chưa vá | Done | 2026-09-03 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-462](acpv2-admin-tenant-split-a-t/AA-462.md) | [T11] Mở rộng Publish sang 6 kênh còn lại (facebook/tiktok/instagram/linkedin/email/ads) — hiện chỉ blog-only | Done | 2026-09-04 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-463](acpv2-admin-tenant-split-a-t/AA-463.md) | [INVESTIGATE] 4 mục hypothesis còn treo từ audit AA-438/439 — brand_audit strict, published_tours count lệch, seo_context null, DFS batch-cost | Done | 2026-09-21 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-464](acpv2-admin-tenant-split-a-t/AA-464.md) | [A4] Nối dây suggest_ramp_transition() — gợi ý chuyển Trust Ramp state, admin vẫn duyệt tay | Done | 2026-09-05 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-465](acpv2-admin-tenant-split-a-t/AA-465.md) | [URGENT][PATCH TẠM] Tăng API Gateway integration timeout /v1/* — /goal (30.3s) và /write (57.2s) đã vượt trần 29s thật | Done | 2026-08-27 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-466](acpv2-admin-tenant-split-a-t/AA-466.md) | [ARCH] Chuyển /goal, /write sang pattern async (202+poll) — thay patch timeout tạm AA-465 | Done | 2026-08-26 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-467](acpv2-admin-tenant-split-a-t/AA-467.md) | [CLEANUP] Dọn dẹp kiến trúc: worktree rác + điều tra archive AA-ACP-App/Core + rà soát trang admin N0-N8 cũ | Done | 2026-08-26 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-468](acpv2-admin-tenant-split-a-t/AA-468.md) | [ADMIN] Dọn trang N0-N8 cũ + bỏ bắt buộc tạo plan/chọn tour khi tạo tenant mới | Done | 2026-08-26 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-469](acpv2-admin-tenant-split-a-t/AA-469.md) | [REDESIGN] T-series: tách T4/T5 độc lập, T7 sửa được + xem lịch sử, fix 28/71 tour, xác nhận T8-T11, A4 feedback loop | Done | 2026-08-30 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-470](acpv2-admin-tenant-split-a-t/AA-470.md) | [FIX] /goal: client.generate() thiếu asyncio.to_thread() — block event loop ECS khi chờ Bedrock | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-471](acpv2-admin-tenant-split-a-t/AA-471.md) | [AUDIT] tenant test-n1-flow thiếu default brand_rules row — fallback rubric generic, cần xác nhận có tenant khác cùng thiếu | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-474](acpv2-admin-tenant-split-a-t/AA-474.md) | [INVESTIGATE] channels trong tenant_config nên là input tenant chọn hay kết quả tính — Planning tab admin đang là nguồn ghi duy nhất, không xoá được | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-476](acpv2-admin-tenant-split-a-t/AA-476.md) | [DASHBOARD] 6 mục audit AA-438 còn treo — #3 double-fire ingestion (P1), #1/#2/#11 sai số hiển thị (P3), #4/#6 đã đóng | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-478](acpv2-admin-tenant-split-a-t/AA-478.md) | [INVESTIGATE] 9 mục còn mơ hồ từ ACP v2/Phase 2 — vấn đề gốc còn thật, cơ chế đề xuất đã lỗi thời, cần xác nhận lại cho T-series | Done | 2026-09-05 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-479](acpv2-admin-tenant-split-a-t/AA-479.md) | [AUDIT] Dump toàn bộ schema DB thật, xác nhận lại phạm vi migration 121, viết lại skill aa-cis-schema từ đầu | Done | 2026-08-27 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-480](acpv2-admin-tenant-split-a-t/AA-480.md) | [SKILL] Bổ sung FK Reference đầy đủ (81 quan hệ) vào skill aa-cis-schema — chuẩn bị sẵn sàng dựng ERD | Done | 2026-08-28 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-481](acpv2-admin-tenant-split-a-t/AA-481.md) | [DB] Dọn 6 bảng chết bổ sung phát hiện ở AA-479 — acp_cms_publish_queue, idempotency_keys, lessons_registry, 3 bảng LangGraph checkpoint mồ côi | Done | 2026-08-27 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-493](acpv2-admin-tenant-split-a-t/AA-493.md) | [shared/llm_client] stop_reason/finish_reason bị vứt đi im lặng — không phân biệt được LLM viết xong vs bị cắt cụt max_tokens | Done | 2026-09-04 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-494](acpv2-admin-tenant-split-a-t/AA-494.md) | [REDESIGN] Atom/Angle/Piece reuse model — schema hiện tại là "1 request = dùng 1 lần", cần chuyển sang N:N tái sử dụng | Done | 2026-09-03 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-497](acpv2-admin-tenant-split-a-t/AA-497.md) | [AA-494 Decision 3] Build: status mới sau approved + API chọn lại angle | Done | 2026-09-03 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-498](acpv2-admin-tenant-split-a-t/AA-498.md) | [AA-494 Decision 4] Build: lịch sử piece cũ đưa vào prompt sinh angle | Done | 2026-09-03 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-499](acpv2-admin-tenant-split-a-t/AA-499.md) | [AA-494 Decision 5] Build: pgvector embedding cho within/cross-tenant reuse | Done | 2026-09-03 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-500](acpv2-admin-tenant-split-a-t/AA-500.md) | [AA-494 Decision 6] Build: fix fetch_trips() tenant filter + xác nhận connector RunwayMap↔atom planning | Done | 2026-09-01 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-501](acpv2-admin-tenant-split-a-t/AA-501.md) | [T9-T11] UI xem bài viết đã chấm — góc AA (trạng thái/điểm/retry/lỗi qua A4) + góc Tenant (nội dung + đầy đủ ngữ cảnh atom/goal/angle/DFS-PAA) | Done | 2026-08-30 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-504](acpv2-admin-tenant-split-a-t/AA-504.md) | [Blog channel] Thiết kế cơ chế multi-atom/pillar content cho Blog — 4 hướng phân tích, chờ quyết định content-strategy với Ms. Thư | Done | 2026-09-01 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-505](acpv2-admin-tenant-split-a-t/AA-505.md) | [LLM Cost Tracking] Persist per-call usage (tenant/T-stage/model/tokens/cost) — build, tách từ AA-434 audit | Done | 2026-09-03 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-506](acpv2-admin-tenant-split-a-t/AA-506.md) | [SECURITY][Urgent] JWT_SECRET hardcoded fallback đang sống trên production — bất kỳ ai đọc code đều giả mạo được JWT cho mọi tenant | Done | 2026-09-01 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-516](acpv2-admin-tenant-split-a-t/AA-516.md) | [CLEANUP] Dead code layer N4-N6 (fetch_trips/runway_map/plan_quarter/allocate_month) — không route nào gọi tới | Done | 2026-09-03 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-518](acpv2-admin-tenant-split-a-t/AA-518.md) | [LLM Ops] Model selection qua UI admin (writer: Claude/Palmyra X5, judge: GPT-5.6) — STEP0 Bedrock 3-account trước, liên kết AA-495 cho brand identity A1 | Done | 2026-09-03 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-520](acpv2-admin-tenant-split-a-t/AA-520.md) | [AUDIT] Rà soát backlog sau AA-507 — issue nào premise đã lỗi thời do kiến trúc Segment/Route/Slate mới | Done | 2026-09-05 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-521](acpv2-admin-tenant-split-a-t/AA-521.md) | [SECURITY] Admin logout() không clear được cis_admin_token httpOnly — session sống tới hết hạn 24h | Done | 2026-09-04 | ACPv2 — Admin/Tenant Split (A/T) |
| [AA-594](cis-core-pipeline-llm-platform/AA-594.md) | [EPIC] CIS Data Reset & Pipeline Rerun — giữ raw_tours, reset dẫn xuất, chạy lại S1/atom/social, verify UI | Done | 2026-10-12 | CIS Core — Pipeline, LLM & Platform |
| [AA-634](cis-core-pipeline-llm-platform/AA-634.md) | [RESEARCH] TypeSafe AI "Jev" (System One Model) — khảo sát toàn diện A/T-series + TripPlanner + AAA cho quyết định có cấu trúc | Done | 2026-10-15 | CIS Core — Pipeline, LLM & Platform |
| [AA-645](cis-core-pipeline-llm-platform/AA-645.md) | [EVAL] Claude Sonnet 5 for writer stages (t2_generate, t8_angle_gen, t9_write, s1_atom_writer) vs Sonnet 4.5/4.6 on Bedrock | Done | 2026-10-25 | CIS Core — Pipeline, LLM & Platform |
| [AA-688](cis-core-pipeline-llm-platform/AA-688.md) | [Perf] Batch Cohere embeddings in PAA question landing (a3_atomize takes 2h+ at 1 text per 3.5 s) | Done | 2026-09-29 | CIS Core — Pipeline, LLM & Platform |
| [AA-690](cis-core-pipeline-llm-platform/AA-690.md) | [A0 + Jev] Ingest gates — is it a tour, near-duplicates, country, usable itinerary | Done | 2026-10-11 | CIS Core — Pipeline, LLM & Platform |
| [AA-691](cis-core-pipeline-llm-platform/AA-691.md) | [A1 + Jev] Grounding check for master content — S1 output must be supported by the raw source | Done | 2026-09-30 | CIS Core — Pipeline, LLM & Platform |
| [AA-692](cis-core-pipeline-llm-platform/AA-692.md) | [A1/A2 + Jev] Brand audit prefilter, judge tie-break, generic soft codes, meal/time regex, Review Queue order | Done | 2026-10-11 | CIS Core — Pipeline, LLM & Platform |
| [AA-693](cis-core-pipeline-llm-platform/AA-693.md) | [A3 research + Jev] Keyword-belongs gate before buying DFS volume + idea filter before storing | Done | 2026-09-30 | CIS Core — Pipeline, LLM & Platform |
| [AA-694](cis-core-pipeline-llm-platform/AA-694.md) | [A3 atoms/Score + Jev] Atom grounding, activity type, PAA landing (transit rule, country scope, belongs), demand ownership | Done | 2026-10-11 | CIS Core — Pipeline, LLM & Platform |
| [AA-695](cis-core-pipeline-llm-platform/AA-695.md) | [A3 Segment + Jev] Measure borderline Segment merges, then decide on a stored "same real-world place?" verdict | Done | 2026-10-11 | CIS Core — Pipeline, LLM & Platform |
| [AA-696](cis-core-pipeline-llm-platform/AA-696.md) | [T-series + Jev] Jev for allow-listed test tenants — T0 brief, T3 grounding, T7 Debate, T8 angles, T9 facts, T10 gates | Canceled | 2026-10-15 | CIS Core — Pipeline, LLM & Platform |
| [AA-698](cis-core-pipeline-llm-platform/AA-698.md) | [A1 judge] GPT-5.6 Luna scores default-brand master rewrites ~3.0 (cross_brand_distinct) → every A1 tour goes to HITL; blocks the rerun | Done | 2026-09-30 | CIS Core — Pipeline, LLM & Platform |
| [AA-699](cis-core-pipeline-llm-platform/AA-699.md) | [T-series + Jev] T0 brief sections, T2 judge, T3 grounding — reuse A1 questions where identical | Canceled | 2026-10-15 | CIS Core — Pipeline, LLM & Platform |
| [AA-700](cis-core-pipeline-llm-platform/AA-700.md) | [T-series + Jev] T7 Debate prefilter, T8 angle answers question, T9 fact relevance (shadow) | Done | 2026-09-30 | CIS Core — Pipeline, LLM & Platform |
| [AA-701](cis-core-pipeline-llm-platform/AA-701.md) | [T-series + Jev] T10 gates — F8 rubric, F9 split, cannibalization, promises_an_option, FAQ dedup (shadow) | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-706](cis-core-pipeline-llm-platform/AA-706.md) | [A1 + Jev] S1 keyword ideas — ask Jev "is this keyword about this tour?" (shadow first, then enforce) | Done | 2026-10-01 | CIS Core — Pipeline, LLM & Platform |
| [AA-707](cis-core-pipeline-llm-platform/AA-707.md) | [T2] Tenant rewrite uses keywords + PAA for the tenant's own market (research cache), not the admin's US keywords | Done | 2026-10-01 | CIS Core — Pipeline, LLM & Platform |
| [AA-712](cis-core-pipeline-llm-platform/AA-712.md) | [ADR 0002] Move the place pipeline (itinerary places, geocoding, tour graph) from the TripPlanner into CIS | Done | 2026-10-23 | CIS Core — Pipeline, LLM & Platform |
| [AA-713](cis-core-pipeline-llm-platform/AA-713.md) | [A3] Atoms follow the tour's Master Content status — inactive/trashed tours leave segments, ranking and tenant slates | Done | 2026-10-03 | CIS Core — Pipeline, LLM & Platform |
| [AA-714](cis-core-pipeline-llm-platform/AA-714.md) | [LLM] Judges on GPT Luna instead of GPT-4.1 — A/B gpt-6-luna vs gpt-5.6-luna, fix the mixed s1_judge routing | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-716](cis-core-pipeline-llm-platform/AA-716.md) | [A3] Raw-tour discontinuation cascade — trashing a source tour must inactivate its Master, drop its atoms, and warn the tenant | Done | 2026-10-07 | CIS Core — Pipeline, LLM & Platform |
| [AA-717](cis-core-pipeline-llm-platform/AA-717.md) | [Review Queue UI] REASONS column shows “—” for tours failed only on low quality / brand_audit manual_check | Done | 2026-10-03 | CIS Core — Pipeline, LLM & Platform |
| [AA-719](cis-core-pipeline-llm-platform/AA-719.md) | [Review Queue UI] Bulk regenerate + non-blocking regenerate (UI freezes, no multi-select) | Done | 2026-10-05 | CIS Core — Pipeline, LLM & Platform |
| [AA-720](cis-core-pipeline-llm-platform/AA-720.md) | [Jev] Credit monitoring — 402 billing_error alert + circuit breaker + daily canary (TypeSafe has no balance API) | Done | 2026-10-05 | CIS Core — Pipeline, LLM & Platform |
| [AA-727](cis-core-pipeline-llm-platform/AA-727.md) | [Ops] Rerun wave as an object — expected_set, terminal states, auto-generated 4-column report + Jev coverage % | Done | 2026-10-11 | CIS Core — Pipeline, LLM & Platform |
| [AA-728](cis-core-pipeline-llm-platform/AA-728.md) | [Review Queue] failure_class + retryable per row; hide Regenerate for non-retryable failures | Done | 2026-10-09 | CIS Core — Pipeline, LLM & Platform |
| [AA-729](cis-core-pipeline-llm-platform/AA-729.md) | [Eval] Golden set (~100 samples from existing data) + scoring script for audit rounds | Done | 2026-10-21 | CIS Core — Pipeline, LLM & Platform |
| [AA-736](cis-core-pipeline-llm-platform/AA-736.md) | [S1 pipeline] Hard failure codes must block Master; one-shot haiku→sonnet upgrade, else route to review queue | Done | 2026-10-07 | CIS Core — Pipeline, LLM & Platform |
| [AA-737](cis-core-pipeline-llm-platform/AA-737.md) | [Jobs] Raise s1_rewrite worker throughput for waves (concurrency / worker scale) — CPU is idle at ~20% | Done | 2026-10-08 | CIS Core — Pipeline, LLM & Platform |
| [AA-738](cis-core-pipeline-llm-platform/AA-738.md) | [S1 pipeline] Deterministic forbidden-word strip on body + tighter writer prompt (stop paying for Sonnet twice) | Done | 2026-10-08 | CIS Core — Pipeline, LLM & Platform |
| [AA-739](cis-core-pipeline-llm-platform/AA-739.md) | [Review Queue UX] A high score + hard-code block reads as contradictory — lead with the block reason, not the score | Done | 2026-10-08 | CIS Core — Pipeline, LLM & Platform |
| [AA-740](cis-core-pipeline-llm-platform/AA-740.md) | [S1 pipeline] Deterministic seo_meta / seo_title length fit after the last LLM repair — length codes block Master with no repair path | Done | 2026-10-08 | CIS Core — Pipeline, LLM & Platform |
| [AA-742](cis-core-pipeline-llm-platform/AA-742.md) | [Jev] decision_log growth — stop writing a full row per cache hit; A3 ranking re-asks every segment on each recompute | Done | 2026-10-09 | CIS Core — Pipeline, LLM & Platform |
| [AA-743](cis-core-pipeline-llm-platform/AA-743.md) | [A3] Incremental recompute — scoped Score/Route on tour removal + one debounced recompute per wave | Done | 2026-10-09 | CIS Core — Pipeline, LLM & Platform |
| [AA-744](cis-core-pipeline-llm-platform/AA-744.md) | [Data] Deterministic backfill — 927 atoms with brand forbidden words + 32 legacy Masters with short seo_meta | Done | 2026-10-09 | CIS Core — Pipeline, LLM & Platform |
| [AA-745](cis-core-pipeline-llm-platform/AA-745.md) | [Review] Clear the 51 tours pending review after the rerun — route by cause | Done | 2026-10-11 | CIS Core — Pipeline, LLM & Platform |
| [AA-746](cis-core-pipeline-llm-platform/AA-746.md) | [S0] Batch completion — treat trashed/superseded/in-review tours as settled; 10 batches stuck in "ingesting" | Done | 2026-10-09 | CIS Core — Pipeline, LLM & Platform |
| [AA-747](cis-core-pipeline-llm-platform/AA-747.md) | [S1 pipeline] Trim LLM calls per tour — seo_meta out of flag_fix, cap itinerary nudges, S1 starts while SEO prefetch is still running | Done | 2026-10-10 | CIS Core — Pipeline, LLM & Platform |
| [AA-748](cis-core-pipeline-llm-platform/AA-748.md) | [S1 writer] Feed the writer structured source facts (days, places, numbers) instead of raw source text | Done | 2026-10-10 | CIS Core — Pipeline, LLM & Platform |
| [AA-749](cis-core-pipeline-llm-platform/AA-749.md) | [A3] Platform atom distinctiveness is always MED — score it per country or hide it | Done | 2026-10-09 | CIS Core — Pipeline, LLM & Platform |
| [AA-753](cis-core-pipeline-llm-platform/AA-753.md) | [Cleanup] Remove dead N7 LLM stages (n7_draft/adapt/faq/repair/gap_research/judge) + orphaned services/acp_produce/gates.py | Done | 2026-10-10 | CIS Core — Pipeline, LLM & Platform |
| [AA-754](cis-core-pipeline-llm-platform/AA-754.md) | [Cleanup] Remove atom distinctiveness end to end (T5 scoring, planning weights, portal, admin API) — concept dropped in the source repo | Done | 2026-10-10 | CIS Core — Pipeline, LLM & Platform |
| [AA-756](cis-core-pipeline-llm-platform/AA-756.md) | [Jev] System-wide effectiveness audit + recalibration — thresholds, grey zones, questions to add or retire | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-757](cis-core-pipeline-llm-platform/AA-757.md) | [A3 atomize] Move t5_atomize from Haiku to GPT-6 Luna — offline A/B on existing atoms (≥100 labelled pairs) | Done | 2026-10-10 | CIS Core — Pipeline, LLM & Platform |
| [AA-758](cis-core-pipeline-llm-platform/AA-758.md) | [A3/Route] Hub assignment broken — routes collapse onto 14 hub_ids, 862-on-one, 405 orphan hubs | Done | 2026-10-11 | CIS Core — Pipeline, LLM & Platform |
| [AA-763](cis-core-pipeline-llm-platform/AA-763.md) | [T-series/Gateway] Separate T-series stage keys (t2_judge, t2_brand_audit, t7_debate_judge…) — split T cost and routing from A1 (G4) | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-764](cis-core-pipeline-llm-platform/AA-764.md) | [T-series/Jobs] Move T7 slate + T8 angles + T9 fact-select onto the worker — end LLM calls inside HTTP requests (ADR 0003) (G5) | Done | 2026-10-12 | CIS Core — Pipeline, LLM & Platform |
| [AA-765](cis-core-pipeline-llm-platform/AA-765.md) | [Gateway] Consolidate judge clients, move T11 dispatch into services/acp_publish, clean stale model docstrings (G6) | Done | 2026-10-28 | CIS Core — Pipeline, LLM & Platform |
| [AA-768](cis-core-pipeline-llm-platform/AA-768.md) | [T9 writer] Source fidelity — the writer invents numeric facts; 5/5 pilot pieces held by F1_grounding / F9 | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-770](cis-core-pipeline-llm-platform/AA-770.md) | [T2/T9] Tenant always receives the content — no held/blocked state, scores or gate codes on the tenant side | Done | 2026-10-13 | CIS Core — Pipeline, LLM & Platform |
| [AA-771](cis-core-pipeline-llm-platform/AA-771.md) | [T8/T9/T10] Tenant brand pack everywhere — compile the tenant rubric from T0 fields, feed it to T8 + T9, remove hard-coded "Adventure Asia / AA / premium" from T-series prompts | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-772](cis-core-pipeline-llm-platform/AA-772.md) | [Place cards] Verified per-place fact cards (region, era, visit length, practical/safety notes, display name) as citable source for T2/T9 | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-773](cis-core-pipeline-llm-platform/AA-773.md) | [T9 seed] Offered vs included status on every moment — "Status: OFFERED, NOT INCLUDED" line + writer rule | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-774](cis-core-pipeline-llm-platform/AA-774.md) | [Place cards] Keep "visiting/practical" card facts out of the writer seed; drafter writes only what/history/setting/naming | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-775](cis-core-pipeline-llm-platform/AA-775.md) | [Brand pack] Fence the style guide as "never a source" + F17 pace_promise finding | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-776](cis-core-pipeline-llm-platform/AA-776.md) | [T9 repair] Bug — an F4-only ledger triggers a full Sonnet rewrite instead of the SEO-fields repair | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-777](cis-core-pipeline-llm-platform/AA-777.md) | [T10 F9] Judge consistency — sticky pass for unchanged sentences, cut truth faults at attempt 3, A/B the F9 judge model | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-778](cis-core-pipeline-llm-platform/AA-778.md) | [T9 voice] Em-dash — deterministic autofix, strip em-dashes from our prompts, then a residue guard | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-779](cis-core-pipeline-llm-platform/AA-779.md) | [T9 FAQ] Questions from People Also Ask first; every answer names its question's subject | Done | 2026-10-22 | CIS Core — Pipeline, LLM & Platform |
| [AA-780](cis-core-pipeline-llm-platform/AA-780.md) | [LinkedIn] 120-word floor (blocking on attempt 1), Trail Pulse voice, broetry + new stock lines | Done | 2026-10-22 | CIS Core — Pipeline, LLM & Platform |
| [AA-783](cis-core-pipeline-llm-platform/AA-783.md) | [Eval] Human calibration of the T9 commercial panel — 40 pieces labelled by Nghiệp with explicit criteria vs the 4-lens AI panel | Done | 2026-10-23 | CIS Core — Pipeline, LLM & Platform |
| [AA-784](cis-core-pipeline-llm-platform/AA-784.md) | [Place cards] Platform-wide build — ~7–9.7k distinct places, staged by country, after the fact-kind fix (≈$15–25) | Done | 2026-10-27 | CIS Core — Pipeline, LLM & Platform |
| [AA-785](cis-core-pipeline-llm-platform/AA-785.md) | [T10 F1] Year-format tolerance — accept "YYYY–YY" / "YYYYs" when the seed has the year (warn until fixed) | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-786](cis-core-pipeline-llm-platform/AA-786.md) | [T10 F9] F9_cta_fact v1.1 — strip citation tags, quote-the-sentence fallback, title/meta input, LinkedIn repair-not-hold | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-787](cis-core-pipeline-llm-platform/AA-787.md) | [T10 gates] Drop F8_framework, promises_an_option, F3, F5; merge F7→F16 | Done | 2026-10-20 | CIS Core — Pipeline, LLM & Platform |
| [AA-791](cis-core-pipeline-llm-platform/AA-791.md) | [Gate eval data] Persist the gate ledger of every attempt + "Label" action on Content Quality + 30-piece fault-injection set | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-792](cis-core-pipeline-llm-platform/AA-792.md) | [T2] Tenant-voice writer prompt — T2 writes in the tenant's brand, not A1's neutral voice; judge gates on brand fit only | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-793](cis-core-pipeline-llm-platform/AA-793.md) | [T2] Best draft wins + targeted repair + background-fact allowance in grounding | Done | 2026-10-15 | CIS Core — Pipeline, LLM & Platform |
| [AA-794](cis-core-pipeline-llm-platform/AA-794.md) | [T2] SEO meta cut mid-sentence + wrong-country suffix | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-795](cis-core-pipeline-llm-platform/AA-795.md) | [T2] Persist the judge breakdown per version + brand-claim fidelity check | Done | 2026-10-28 | CIS Core — Pipeline, LLM & Platform |
| [AA-799](cis-core-pipeline-llm-platform/AA-799.md) | [Security] /v1/pipeline — /run has no auth; review-queue approve/reject accept any tenant JWT | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-800](cis-core-pipeline-llm-platform/AA-800.md) | [Brand pack] Tenant signature vocabulary — split the forbidden list into platform-truth vs AA-style; tenants may use their own brand words | Done | 2026-10-20 | CIS Core — Pipeline, LLM & Platform |
| [AA-801](cis-core-pipeline-llm-platform/AA-801.md) | [T2 judge] Stabilise the brand_fit / mission verdict — repeated calls on the same draft swing 4–8 | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-803](cis-core-pipeline-llm-platform/AA-803.md) | [Jev] Evaluate every Jev question on live data; keep the ones with real effect, switch off the rest | Done | 2026-10-22 | CIS Core — Pipeline, LLM & Platform |
| [AA-806](cis-core-pipeline-llm-platform/AA-806.md) | [Infra] Split the CIS CI role (app-deploy vs terraform) + permissions boundary; enable WAF enforce after the count window | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-807](cis-core-pipeline-llm-platform/AA-807.md) | [Data] Phase 1 foundation — per-app DB owner roles, migration ownership + byte-copy CI checks, nightly schema-drift job, Dead Table Registry, shared.countries ISO | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-808](cis-core-pipeline-llm-platform/AA-808.md) | [Place cards] Drafter must not append traveller clauses to background facts | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-809](cis-core-pipeline-llm-platform/AA-809.md) | [Place cards] Post-draft dedup: a drafted card that names an existing card must link to it, not insert a duplicate | Done | 2026-10-14 | CIS Core — Pipeline, LLM & Platform |
| [AA-811](cis-core-pipeline-llm-platform/AA-811.md) | [Platform] Transactional email channel (SES on acc2) — shared sender for Booking quotes/OTP and TripPlanner advisor notifications | Done | 2026-10-15 | CIS Core — Pipeline, LLM & Platform |
| [AA-817](cis-core-pipeline-llm-platform/AA-817.md) | [Security] CIS API runtime role aa_cis_admin is not filtered by RLS — tenant isolation relies on app code only | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-840](cis-core-pipeline-llm-platform/AA-840.md) | [T7 Slate] Normal planning never proposes Facebook (or other non-LinkedIn social) pieces — shared seen_places + LinkedIn first; tenant channels do not filter the Slate | Done | 2026-10-15 | CIS Core — Pipeline, LLM & Platform |
| [AA-843](cis-core-pipeline-llm-platform/AA-843.md) | [LLM gateway] Legacy writer chain wastes one guaranteed-failing acc2-native call per request (~2,382 in 7 days) — start at the satellite, keep acc2 only if it ever works | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-845](cis-core-pipeline-llm-platform/AA-845.md) | [Jev] A-axis ground-truth loop + a1_claim_supported reject ceiling + 402 investigation | Done | 2026-10-22 | CIS Core — Pipeline, LLM & Platform |
| [AA-854](cis-core-pipeline-llm-platform/AA-854.md) | Identity Phase 0: apply Cognito pools (Infra #105), break-glass account, first staff email-code login on Dev | Done | 2026-10-18 | CIS Core — Pipeline, LLM & Platform |
| [AA-862](cis-core-pipeline-llm-platform/AA-862.md) | [LLM] Cohere Embed v4 throughput: fall back to the acc3 and acc1 satellites before keyword search, then re-request the acc2 quota | Done | 2026-10-16 | CIS Core — Pipeline, LLM & Platform |
| [AA-865](cis-core-pipeline-llm-platform/AA-865.md) | [T10 F9] Pooled F9_cta_fact re-flag rate after sentence repair (AA-777 residual) | Done | 2026-10-20 | CIS Core — Pipeline, LLM & Platform |
| [AA-905](cis-core-pipeline-llm-platform/AA-905.md) | [Data] Geo graph backfill for the 8 countries without one (paid place-pipeline run, needs a quote) | Done | 2026-10-27 | CIS Core — Pipeline, LLM & Platform |
| [AA-914](cis-core-pipeline-llm-platform/AA-914.md) | Route assembly puts Segments from another country into a tour's route | Done | 2026-10-20 | CIS Core — Pipeline, LLM & Platform |
| [AA-915](cis-core-pipeline-llm-platform/AA-915.md) | [Writing memory] Freeze the ungated lessons loop and record app ADR 0010 (governed writing memory) | Done | 2026-10-21 | CIS Core — Pipeline, LLM & Platform |
| [AA-916](cis-core-pipeline-llm-platform/AA-916.md) | [Writing memory] Capture writing signals: before/after text, reason codes, every T9 attempt | Done | 2026-10-26 | CIS Core — Pipeline, LLM & Platform |
| [AA-917](cis-core-pipeline-llm-platform/AA-917.md) | [Writing memory] Rule store and the mining job (scoped rules, fact filter, cheaper drafter) | Done | 2026-10-26 | CIS Core — Pipeline, LLM & Platform |
| [AA-918](cis-core-pipeline-llm-platform/AA-918.md) | [Writing memory] R0 replay engine ($0) and the L0 lexicon fast path | Done | 2026-10-26 | CIS Core — Pipeline, LLM & Platform |
| [AA-924](cis-core-pipeline-llm-platform/AA-924.md) | [T10 gates] Severity per violation in the gate ledger, then merge F15_voice_warn→F15 and F2 variants + stock list → one lexicon gate | Done | 2026-10-26 | CIS Core — Pipeline, LLM & Platform |
| [AA-925](cis-core-pipeline-llm-platform/AA-925.md) | [Quality] Q-2: repair contract, degraded counters, S1 day-count oracle and Q0 corpus | Done | 2026-10-21 | CIS Core — Pipeline, LLM & Platform |
| [AA-926](cis-core-pipeline-llm-platform/AA-926.md) | [Quality] Q-1: error taxonomy, gate registry, single thresholds file and lint | Done | 2026-10-25 | CIS Core — Pipeline, LLM & Platform |
| [AA-927](cis-core-pipeline-llm-platform/AA-927.md) | [Cost] LLM calls with no llm_call_log row (AA-729 eval runs: 116/216 and 188/815) | Done | 2026-10-21 | CIS Core — Pipeline, LLM & Platform |
| [AA-982](cis-core-pipeline-llm-platform/AA-982.md) | T9 writer input drops place_paa questions already rejected by Jev A3 | Done | 2026-10-23 | CIS Core — Pipeline, LLM & Platform |
| [AA-983](cis-core-pipeline-llm-platform/AA-983.md) | Revalidation sets published_tours.quality_score_id to NULL instead of the new accepted score | Done | 2026-10-23 | CIS Core — Pipeline, LLM & Platform |
| [AA-984](cis-core-pipeline-llm-platform/AA-984.md) | T9 blog holds: F9 claims on heading lines are unrepairable; over-long rewrites held at attempt 2 | Done | 2026-10-23 | CIS Core — Pipeline, LLM & Platform |
| [AA-985](cis-core-pipeline-llm-platform/AA-985.md) | T9 F17 temporal-role false positives + systematic gate-error calibration | Done | 2026-10-23 | CIS Core — Pipeline, LLM & Platform |
| [AA-986](cis-core-pipeline-llm-platform/AA-986.md) | Tour retirement propagation: a tour deleted at S0/A0 hides every derivative, tenant keeps T2 with a warning | Done | 2026-10-23 | CIS Core — Pipeline, LLM & Platform |
| [AA-988](cis-core-pipeline-llm-platform/AA-988.md) | [S1 propagation] Segments, routes and ranking follow the S1 v2 atoms (segment match, orphan cleanup, routes for every tour) | Done | 2026-10-27 | CIS Core — Pipeline, LLM & Platform |
| [AA-989](cis-core-pipeline-llm-platform/AA-989.md) | [S1 propagation] Places and embeddings follow the S1 v2 atoms (geo.tour_place re-sync, atom embeddings, content_embedding decision) | Done | 2026-10-27 | CIS Core — Pipeline, LLM & Platform |
| [AA-992](cis-core-pipeline-llm-platform/AA-992.md) | [Admin] Data coverage page: one live numbers table from raw uploads to TripPlanner, Booking and CRM | Done | 2026-10-26 | CIS Core — Pipeline, LLM & Platform |
| [AA-588](cis-data-reset-pipeline-rerun-audit/AA-588.md) | [INFRA][G5] Gỡ OIDC trust org cũ (AdventureAsia365-CIS) sau khi ổn định | Done | 2026-09-21 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-595](cis-data-reset-pipeline-rerun-audit/AA-595.md) | [G0] Dựng bastion EC2 + SSM tunnel + BACKUP toàn bộ (chặn mọi việc sau) | Done | 2026-09-16 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-596](cis-data-reset-pipeline-rerun-audit/AA-596.md) | [G1] Điều tra hiện trạng DB (read-only) — đếm row mọi bảng/schema, xác nhận ranh giới raw vs dẫn xuất | Done | 2026-09-16 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-597](cis-data-reset-pipeline-rerun-audit/AA-597.md) | [G2] Chốt danh sách bảng xóa + thứ tự + script DELETE (Nghiệp DUYỆT trước khi chạy) | Done | 2026-09-16 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-598](cis-data-reset-pipeline-rerun-audit/AA-598.md) | [G3] Reset dữ liệu dẫn xuất (chạy sau backup + duyệt G2) | Done | 2026-09-16 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-599](cis-data-reset-pipeline-rerun-audit/AA-599.md) | [G4] Chạy lại S1 → master content, verify S1 hoạt động + UI | Done | 2026-10-09 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-600](cis-data-reset-pipeline-rerun-audit/AA-600.md) | [G5] Atomize + segment/score/route + social content admin, verify (+ rebuild TripPlanner extraction) | Done | 2026-10-09 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-601](cis-data-reset-pipeline-rerun-audit/AA-601.md) | [G6] Audit UI admin — verify mọi trang hiển thị đúng, dữ liệu thật (không mock) sau rerun | Done | 2026-10-09 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-602](cis-data-reset-pipeline-rerun-audit/AA-602.md) | [CLEANUP] Terminate bastion EC2 + revert SG sau khi audit xong | Done | 2026-09-17 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-603](cis-data-reset-pipeline-rerun-audit/AA-603.md) | [CLEANUP] DROP cụm bảng N7/N8 dead sau khi gỡ code reader + deploy | Done | 2026-09-21 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-604](cis-data-reset-pipeline-rerun-audit/AA-604.md) | [BUG] S0 "Tours Ready" đếm 793 nhưng 30 tour thiếu itinerary không viết được (S1=763) — lọc + cảnh báo ngay khi upload | Done | 2026-09-17 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-605](cis-data-reset-pipeline-rerun-audit/AA-605.md) | [UIUX] Đồng bộ phong cách admin portal với trang chính adventure.asia (điều tra kỹ + design pass) | Done | 2026-09-24 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-606](cis-data-reset-pipeline-rerun-audit/AA-606.md) | [BUILD] Bedrock Batch Inference cho S1 rewrite (~100 tour/lần) — xin IAM Batch trên acc3 + re-architect submit/poll/ingest | Done | 2026-09-17 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-607](cis-data-reset-pipeline-rerun-audit/AA-607.md) | [EPIC] Đánh giá lại &amp; redesign 2 luồng viết (admin S1 + social content) — đồng bộ cả tenant | Done | 2026-09-23 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-608](cis-data-reset-pipeline-rerun-audit/AA-608.md) | [S1][Rubric/Gate+Model] H3 đo batch 20-50 tour → H2 nới gate + quyết haiku↔sonnet | Done | 2026-09-17 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-609](cis-data-reset-pipeline-rerun-audit/AA-609.md) | [Curation] Gỡ "star" no-op (dead) khỏi UI + backend | Done | 2026-09-17 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-610](cis-data-reset-pipeline-rerun-audit/AA-610.md) | [Enhancement] Nâng cấp score ranking atom/segment theo rank-sum 4 chiều (mô hình Ms.Thư) | Done | 2026-09-21 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-611](cis-data-reset-pipeline-rerun-audit/AA-611.md) | [Cleanup] Gỡ hẳn s1-from-atom (route + s1_from_atom.py + eval) | Done | 2026-09-17 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-612](cis-data-reset-pipeline-rerun-audit/AA-612.md) | [Tenant sync] Fix bug T2 brand fetch (làm luôn) + điều tra T7-T11 đối chiếu Ms.Thư | Done | 2026-09-19 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-613](cis-data-reset-pipeline-rerun-audit/AA-613.md) | [Social tenant][Sub1-BE] Gate severity + metrics table + dọn leak /pieces + held→approved cho tenant + fix blog publish MD→HTML + export/publish audit | Done | 2026-09-19 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-614](cis-data-reset-pipeline-rerun-audit/AA-614.md) | [Social tenant][Sub2-FE tenant] My Content phẳng (ẩn gate/held) + khóa copy màn hình (chừa ô edit) + publish/export rõ | Done | 2026-09-19 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-615](cis-data-reset-pipeline-rerun-audit/AA-615.md) | [Social tenant][Sub3-FE admin] Monitor telemetry gate/severity/retry/publish theo tenant/kênh (mở rộng run-health/platform-stats) | Done | 2026-09-19 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-625](cis-data-reset-pipeline-rerun-audit/AA-625.md) | [DFS][COST] Nâng TTL cache SEO 24h → 7 ngày (giảm chi phí DataForSEO khi rerun) | Done | 2026-09-19 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-626](cis-data-reset-pipeline-rerun-audit/AA-626.md) | [UI] Review Queue làm lại (bảng + expand + dismiss version fail) + Master Content thêm cột version/link dismiss | Done | 2026-09-19 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-627](cis-data-reset-pipeline-rerun-audit/AA-627.md) | [DFS][Ops] Cảnh báo số dư DataForSEO thấp (đọc balance 1 lần/ngày, alert dưới ngưỡng) — OpenAI để platform tự quản | Done | 2026-09-19 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-629](cis-data-reset-pipeline-rerun-audit/AA-629.md) | [BUG] Tenant market ngoài 6 whitelist bị silent-fallback về US (đọc nhầm dữ liệu, không lỗi) | Done | 2026-09-22 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-630](cis-data-reset-pipeline-rerun-audit/AA-630.md) | [TECH DEBT] questions_count cache (AA-610) never invalidated when search_demand/PAA data changes | Done | 2026-09-22 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-631](cis-data-reset-pipeline-rerun-audit/AA-631.md) | [Enhancement] Debate stage for Slate — contested metric + brand-fit filter before tenant sees candidates | Done | 2026-09-22 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-632](cis-data-reset-pipeline-rerun-audit/AA-632.md) | [Debate follow-up] Extend "not already on slate" place de-dup across Channels | Done | 2026-09-23 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-633](cis-data-reset-pipeline-rerun-audit/AA-633.md) | [Pre-G4] Sweep admin UI for dead-route calls before rerun (found via Trust Ramp 404) | Done | 2026-09-23 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-636](cis-data-reset-pipeline-rerun-audit/AA-636.md) | [Tenant Portal] Trust fixes: real quota reset date, working bell/search, hide internal cost & jargon, page headers | Done | 2026-09-25 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-637](cis-data-reset-pipeline-rerun-audit/AA-637.md) | [Tenant Portal] Live writing progress: stream steps + text while a tour / social post is being written | Done | 2026-09-25 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-638](cis-data-reset-pipeline-rerun-audit/AA-638.md) | [Tenant Portal] Product polish: onboarding checklist, skeleton loading, notifications, ⌘K palette, usage chart | Done | 2026-09-25 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-639](cis-data-reset-pipeline-rerun-audit/AA-639.md) | [T2 pipeline] Tour rewrite needs 3+ full revisions before passing checks — find why the first draft fails | Done | 2026-09-25 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-640](cis-data-reset-pipeline-rerun-audit/AA-640.md) | [Billing] One source for plan tour quota (membership_plans); over-quota rewrites allowed + billed as overage | Done | 2026-09-25 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-641](cis-data-reset-pipeline-rerun-audit/AA-641.md) | [T2 pipeline] Stop flag_fix from creating new hard failures: deterministic seo_meta fit + forbidden-word guard | Done | 2026-10-07 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-724](cis-data-reset-pipeline-rerun-audit/AA-724.md) | [S1 writer] Cycle/bike tours fail brand-fit — writer emits hype/persona tone + forbidden words, regenerate can't fix | Done | 2026-10-07 | CIS Data Reset & Pipeline Rerun (Audit) |
| [AA-160](cis-portal-admin-tenant-ui/AA-160.md) | Notification Layer Phase 2 — EventBridge + SQS + Dispatch Lambda | Canceled | 2026-10-12 | CIS Portal — Admin & Tenant UI |
| [AA-662](cis-portal-admin-tenant-ui/AA-662.md) | [UI kit] Shared admin/portal components — DataTable (filter, sort, columns, pagination, saved views, CSV), Drawer, Modal, PageHeader, empty/loading/error states | Done | 2026-10-05 | CIS Portal — Admin & Tenant UI |
| [AA-663](cis-portal-admin-tenant-ui/AA-663.md) | [Admin] Information architecture consolidation — one Dashboard, remove duplicates and legacy routes, Brand Identity + system config into Settings, drop the "ADMIN" tag | Done | 2026-09-29 | CIS Portal — Admin & Tenant UI |
| [AA-664](cis-portal-admin-tenant-ui/AA-664.md) | [Admin] Overview dashboard — whole-system view (pipeline A0→A3, intelligence, tenants, jobs, cost vs budget, alerts) | Done | 2026-10-05 | CIS Portal — Admin & Tenant UI |
| [AA-665](cis-portal-admin-tenant-ui/AA-665.md) | [Admin] Cost Operations — rename External Spend; budgets, DFS/Jev/LLM/AWS spend, research triggers audit, alerts | Done | 2026-10-28 | CIS Portal — Admin & Tenant UI |
| [AA-666](cis-portal-admin-tenant-ui/AA-666.md) | [Admin] Tenant 360 — full tenant management page (profile, brand, content, channels, usage/billing, quality, audit, settings) | Done | 2026-10-05 | CIS Portal — Admin & Tenant UI |
| [AA-667](cis-portal-admin-tenant-ui/AA-667.md) | [Admin] S1 Rewrite page — live streaming while writing (reuse LiveWriter / ADR 0004) + job-based progress | Done | 2026-10-05 | CIS Portal — Admin & Tenant UI |
| [AA-668](cis-portal-admin-tenant-ui/AA-668.md) | [Portal] Writer panel — segment/topic opens a right-side panel: Goal → Angle → auto-write with live streaming (social + tour rewrite); CTA from brand defaults | Done | 2026-10-16 | CIS Portal — Admin & Tenant UI |
| [AA-669](cis-portal-admin-tenant-ui/AA-669.md) | [Portal] My Content as a DataTable — columns, filters, sort, bulk export/publish | Done | 2026-10-25 | CIS Portal — Admin & Tenant UI |
| [AA-670](cis-portal-admin-tenant-ui/AA-670.md) | [Portal] Information architecture + page-by-page UI audit (fix inconsistent states, e.g. finished tour still shows "Writing…") | Duplicate | 2026-10-12 | CIS Portal — Admin & Tenant UI |
| [AA-671](cis-portal-admin-tenant-ui/AA-671.md) | [Portal] Marketplace redesign — catalog grid with filters, detail drawer, clear add-to-catalog state | Done | 2026-10-29 | CIS Portal — Admin & Tenant UI |
| [AA-672](cis-portal-admin-tenant-ui/AA-672.md) | [Portal] Account pages — Billing, Activity log, Team & Settings, Integrations (commercial-grade) | Duplicate | 2026-10-12 | CIS Portal — Admin & Tenant UI |
| [AA-687](cis-portal-admin-tenant-ui/AA-687.md) | [Admin] Jobs observability — job detail with LLM calls and cost split, worker health, progress/ETA, links from domain pages | Done | 2026-09-29 | CIS Portal — Admin & Tenant UI |
| [AA-705](cis-portal-admin-tenant-ui/AA-705.md) | [Admin UI v2] SEO Intelligence page — demand by market, keyword table, PAA coverage, gaps, spend | Done | 2026-10-05 | CIS Portal — Admin & Tenant UI |
| [AA-718](cis-portal-admin-tenant-ui/AA-718.md) | [Admin UI] Master Content page — fix 5 data/UX bugs + redesign for a professional, commercial-grade catalog view | Done | 2026-10-05 | CIS Portal — Admin & Tenant UI |
| [AA-721](cis-portal-admin-tenant-ui/AA-721.md) | [Admin UI v2] Jobs page rebuild — kit + react-query, worker-ECS-aware (per-kind, concurrency, workers) | Done | 2026-10-09 | CIS Portal — Admin & Tenant UI |
| [AA-722](cis-portal-admin-tenant-ui/AA-722.md) | [Admin UI v2] Retire / de-dupe the old Dashboard page after Overview + SEO Intelligence | Done | 2026-10-09 | CIS Portal — Admin & Tenant UI |
| [AA-726](cis-portal-admin-tenant-ui/AA-726.md) | [T11] Idempotent publish — unique key per (piece, channel, revision), store remote_post_id, read-before-retry; WordPress app password in Secrets Manager | Done | 2026-10-11 | CIS Portal — Admin & Tenant UI |
| [AA-732](cis-portal-admin-tenant-ui/AA-732.md) | [CI][UI] Playwright smoke on Vercel preview for key admin/portal pages + ESLint rule enforcing the kit | Done | 2026-10-09 | CIS Portal — Admin & Tenant UI |
| [AA-752](cis-portal-admin-tenant-ui/AA-752.md) | [Admin UI v2] Admin shell redesign — collapsible sidebar, logo → Overview, topbar with real ⌘K search, mobile bottom nav | Done | 2026-10-09 | CIS Portal — Admin & Tenant UI |
| [AA-759](cis-portal-admin-tenant-ui/AA-759.md) | [Portal] PortalShell on the kit — grouped nav, real ⌘K, mobile bottom bar, theme, route renames (no T-number slugs) | Done | 2026-10-22 | CIS Portal — Admin & Tenant UI |
| [AA-760](cis-portal-admin-tenant-ui/AA-760.md) | [Portal] Page-by-page audit + state fixes — statuses from the job, never inferred from rows ("Writing…" bug) | Done | 2026-10-22 | CIS Portal — Admin & Tenant UI |
| [AA-761](cis-portal-admin-tenant-ui/AA-761.md) | [Portal] Account pages with real data — Billing usage/overage, Activity timeline, Integrations (WordPress health, API key view) | Done | 2026-10-25 | CIS Portal — Admin & Tenant UI |
| [AA-766](cis-portal-admin-tenant-ui/AA-766.md) | [Admin] Tenant 360 panel — Cost, Quality and Markets tabs (margin vs plan, per-gate pass/held, research coverage) (G9) | Done | 2026-10-14 | CIS Portal — Admin & Tenant UI |
| [AA-769](cis-portal-admin-tenant-ui/AA-769.md) | [Admin] Content Quality tab on /admin/atom-curation — every tenant's T2 tours and T9 pieces with gate results, held reasons, flagged sentences, writer inputs and per-gate stats | Done | 2026-10-13 | CIS Portal — Admin & Tenant UI |
| [AA-796](cis-portal-admin-tenant-ui/AA-796.md) | [Portal] AA-770 compliance for T2 — tenant status no longer derives from the score; remove quality fields from tenant APIs | Done | 2026-10-14 | CIS Portal — Admin & Tenant UI |
| [AA-797](cis-portal-admin-tenant-ui/AA-797.md) | [Admin tenants] Bugs — status toggle does nothing, plan_id never set, offboard not wired, no audit, /usage 500 | Done | 2026-10-14 | CIS Portal — Admin & Tenant UI |
| [AA-798](cis-portal-admin-tenant-ui/AA-798.md) | [Billing] Replace the fabricated llm_cost_usd view column and the starter defaults with real llm_call_log cost | Done | 2026-10-14 | CIS Portal — Admin & Tenant UI |
| [AA-802](cis-portal-admin-tenant-ui/AA-802.md) | [T2/T9] Silent correction — a held piece repaired by admin/AI updates the tenant's unpublished copy (version history, no flags shown) | Done | 2026-10-16 | CIS Portal — Admin & Tenant UI |
| [AA-813](cis-portal-admin-tenant-ui/AA-813.md) | [Portal] Tenant user accounts — invite users, roles (owner/editor/viewer), API key rotation; replace the one-shared-key login | Done | 2026-10-24 | CIS Portal — Admin & Tenant UI |
| [AA-815](cis-portal-admin-tenant-ui/AA-815.md) | [Portal] Facebook connect UI + tenant self-unpublish — wire existing /v1/integrations/facebook* and DELETE /v1/publish-log/{id} | Done | 2026-10-15 | CIS Portal — Admin & Tenant UI |
| [AA-819](cis-portal-admin-tenant-ui/AA-819.md) | [AUP 2026-11] Tenant AI notice at review/publish, T9 guard against reviews/testimonials/first-person-customer copy, per-tenant daily publish limit | Done | 2026-10-16 | CIS Portal — Admin & Tenant UI |
| [AA-821](cis-portal-admin-tenant-ui/AA-821.md) | [Research] Tenant CRM — customer/lead management for tenants (Ms. Thư's idea, S236); research + design before any build | Done | 2026-10-21 | CIS Portal — Admin & Tenant UI |
| [AA-831](cis-portal-admin-tenant-ui/AA-831.md) | [Portal] Facebook Page connect: tenant connection guide (promised on PR-7) + correct connect-card help text (3 permissions, Live-mode app, long-lived token) | Done | 2026-10-16 | CIS Portal — Admin & Tenant UI |
| [AA-834](cis-portal-admin-tenant-ui/AA-834.md) | [CI][UI] Fix flaky AA-752 smoke test "(b) collapse toggles the rail and survives reload" — click lands before hydration | Done | 2026-10-17 | CIS Portal — Admin & Tenant UI |
| [AA-836](cis-portal-admin-tenant-ui/AA-836.md) | [Portal] Tenant portal layout defects at 390 px + My Catalog source-fetch 404 + raw markdown previews (S237 UI verify D2/D3/D4/D6) | Done | 2026-10-17 | CIS Portal — Admin & Tenant UI |
| [AA-857](cis-portal-admin-tenant-ui/AA-857.md) | [Slate/A3] Tenant picks a Subject but the post is about another place (even another country): mixed-country Segments + representative atom by atom_id | Done | 2026-10-16 | CIS Portal — Admin & Tenant UI |
| [AA-858](cis-portal-admin-tenant-ui/AA-858.md) | [Admin] Ops overview: extend /admin/overview with TripPlanner traffic, Booking funnel, per-app health and per-app cost (business view for Ms. Thư) | Done | 2026-10-19 | CIS Portal — Admin & Tenant UI |
| [AA-863](cis-portal-admin-tenant-ui/AA-863.md) | [Admin] Show the Slate seed place and country next to each Subject and T9 piece | Done | 2026-10-17 | CIS Portal — Admin & Tenant UI |
| [AA-882](cis-portal-admin-tenant-ui/AA-882.md) | [Admin] Server-side staff authorization: capability map, require_perm, route-policy CI | Done | 2026-10-17 | CIS Portal — Admin & Tenant UI |
| [AA-883](cis-portal-admin-tenant-ui/AA-883.md) | [Admin] AA Console nav (Platform / CIS Content) + read-only Staff page + links to all apps | Done | 2026-10-17 | CIS Portal — Admin & Tenant UI |
| [AA-884](cis-portal-admin-tenant-ui/AA-884.md) | [Admin] Apps page (health/version/links), staff action audit view, cost per app | Done | 2026-10-19 | CIS Portal — Admin & Tenant UI |
| [AA-885](cis-portal-admin-tenant-ui/AA-885.md) | [Portal] Split the tenant portal into its own app and domain | Done | 2026-10-19 | CIS Portal — Admin & Tenant UI |
| [AA-898](cis-portal-admin-tenant-ui/AA-898.md) | [Admin] Docs reader page in the CIS admin — S3 sync, manifest, /admin/docs | Done | 2026-10-28 | CIS Portal — Admin & Tenant UI |
| [AA-751](data-platform-schema-ops-scale/AA-751.md) | [Jobs] X6 per-owner job tables (ADR 0003a): DDL template + comparison test, booking.job parity, Booking deploy guard, DB Migrate idle check, backlog-age alarms, acp_runs readers | Done | 2026-10-17 | Data Platform — Schema, Ops & Scale |
| [AA-824](data-platform-schema-ops-scale/AA-824.md) | [Data/Ops] RDS guardrails + connection budget — storage autoscaling, parameter group, pg_stat_statements, log export, alarms, CONNECTION LIMIT per role, Lambda reserved concurrency | Done | 2026-10-15 | Data Platform — Schema, Ops & Scale |
| [AA-825](data-platform-schema-ops-scale/AA-825.md) | [Data] Retention + rollups for log tables — llm_call_log 180 d + daily rollup, tenant_api_usage 90 d + monthly, job TTL, sargable usage view, S3 Parquet archive | Done | 2026-10-25 | Data Platform — Schema, Ops & Scale |
| [AA-826](data-platform-schema-ops-scale/AA-826.md) | [Data/ADR] New-app integration playbook (ADR 0008) — owners.yaml registry, role bootstrap template, consumer contract hash guard | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-827](data-platform-schema-ops-scale/AA-827.md) | [Security] TripPlanner guest_token is the session id in plaintext — issue a separate random token, store only its hash | Done | 2026-10-16 | Data Platform — Schema, Ops & Scale |
| [AA-828](data-platform-schema-ops-scale/AA-828.md) | [Data/Ops] Per-app cost allocation tags + budgets for the data platform (RDS, S3 archive, Proxy later) | Done | 2026-10-16 | Data Platform — Schema, Ops & Scale |
| [AA-829](data-platform-schema-ops-scale/AA-829.md) | [Data/DR] Restore drill on Dev + private DSN CNAME + secure the real-data dumps in docs/backups/2026-09-16 | Done | 2026-10-24 | Data Platform — Schema, Ops & Scale |
| [AA-832](data-platform-schema-ops-scale/AA-832.md) | [Data/Ops] Remaining C4.1 RDS alarms — read/write latency, disk queue, XID wraparound, per-role connections vs CONNECTION LIMIT | Done | 2026-10-16 | Data Platform — Schema, Ops & Scale |
| [AA-833](data-platform-schema-ops-scale/AA-833.md) | [Data/Ops] TripPlanner Lambda throttle alarms: stop paging on single 5-minute blips + cut the home-page prefetch fan-out (root cause fixed by CIS migration 235) | Done | 2026-10-16 | Data Platform — Schema, Ops & Scale |
| [AA-838](data-platform-schema-ops-scale/AA-838.md) | [Data/Ops] Wire the capacity review (monthly), pg_stat_statements check (weekly) and access review (quarterly) into the session ritual; run the first capacity review | Done | 2026-10-28 | Data Platform — Schema, Ops & Scale |
| [AA-839](data-platform-schema-ops-scale/AA-839.md) | [Data/Privacy] Erasure runbook + DRY RUN job for a traveller/customer and an offboarded tenant (roadmap L3, DM-6.7) — parked until ADR 0006 Phase 4 / before prod | Done | 2026-10-23 | Data Platform — Schema, Ops & Scale |
| [AA-841](data-platform-schema-ops-scale/AA-841.md) | [Security] Plaintext credentials tracked in AA-CIS-Infra envs/dev/terraform.tfvars (old acc1 RDS DSN with password, DataForSEO login/password) — remove from git, rotate what is still live | Done | 2026-10-16 | Data Platform — Schema, Ops & Scale |
| [AA-846](data-platform-schema-ops-scale/AA-846.md) | [Infra] Clean full-root Terraform plan for accounts/aa365: hidden drifts, Terraform version pin, apply guard | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-847](data-platform-schema-ops-scale/AA-847.md) | [Places] L4 catalog read model fast enough for PLACES_SOURCE=cis + flip + content-validity report | Done | 2026-10-22 | Data Platform — Schema, Ops & Scale |
| [AA-848](data-platform-schema-ops-scale/AA-848.md) | [Security] X2 catalogue-wide RLS CI guard (rules a-e; f after AA-826) | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-849](data-platform-schema-ops-scale/AA-849.md) | [Data/CI] TripPlanner migration replay CI: replay tp migrations twice, assert tp-NNN keys + tripplanner grants | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-850](data-platform-schema-ops-scale/AA-850.md) | [Data] Dead Table Registry + wave-1 quarantine (acp_gold_output, acp_silver_s2-s4, confirmed legacy tables) | Done | 2026-10-28 | Data Platform — Schema, Ops & Scale |
| [AA-851](data-platform-schema-ops-scale/AA-851.md) | [Data] shared.countries (ISO-3166) + v_countries / v_destinations catalog contract views | Done | 2026-10-25 | Data Platform — Schema, Ops & Scale |
| [AA-852](data-platform-schema-ops-scale/AA-852.md) | [Data] Per-app DB owner roles + db_migrator task def (bk_owner / tp_owner, tripplanner role in a migration, revoke legacy grants 179/180) | Done | 2026-10-19 | Data Platform — Schema, Ops & Scale |
| [AA-853](data-platform-schema-ops-scale/AA-853.md) | [Data/CI] Schema drift diff against a replayed DB + migration ownership lint (nightly: 0 unmanaged objects) | Done | 2026-10-25 | Data Platform — Schema, Ops & Scale |
| [AA-859](data-platform-schema-ops-scale/AA-859.md) | [Security] Tenant pool wave 2: move tenant write and planning routes to aa_app_user, RLS on the tables they touch | Done | 2026-10-22 | Data Platform — Schema, Ops & Scale |
| [AA-860](data-platform-schema-ops-scale/AA-860.md) | [Security] X1: split the CIS runtime role (cis_owner owns tables, cis_app serves requests without the RLS bypass) | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-866](data-platform-schema-ops-scale/AA-866.md) | [Security] Restrict deploy/apply/migrate OIDC trust to main (env policy, ref guard, IAM) | Done | 2026-10-17 | Data Platform — Schema, Ops & Scale |
| [AA-867](data-platform-schema-ops-scale/AA-867.md) | [Security] Free GitHub security features, org 2FA, force-push and branch-deletion block | Done | 2026-10-17 | Data Platform — Schema, Ops & Scale |
| [AA-868](data-platform-schema-ops-scale/AA-868.md) | [CI] CIS CI/deploy hardening: blocking pip-audit, deploy concurrency, fail-closed guard | Done | 2026-10-17 | Data Platform — Schema, Ops & Scale |
| [AA-869](data-platform-schema-ops-scale/AA-869.md) | [Ops] App rollback readiness: immutable CIS ECR, task-def + Vercel rollback, incident page | Done | 2026-10-17 | Data Platform — Schema, Ops & Scale |
| [AA-870](data-platform-schema-ops-scale/AA-870.md) | [Observability] CIS error visibility: Sentry, API GW 5xx/latency alarms, uptime checks | Done | 2026-10-17 | Data Platform — Schema, Ops & Scale |
| [AA-871](data-platform-schema-ops-scale/AA-871.md) | [Observability] JSON logs with request ids + Sentry for Booking and TripPlanner | Done | 2026-10-22 | Data Platform — Schema, Ops & Scale |
| [AA-872](data-platform-schema-ops-scale/AA-872.md) | chore: alarm OK e-mails back on + log retention 365 d security / 30 d app | Done | 2026-10-17 | Data Platform — Schema, Ops & Scale |
| [AA-874](data-platform-schema-ops-scale/AA-874.md) | [Security] Redis AUTH/TLS/at-rest encryption + tenant-flag read-failure alarm | Done | 2026-10-25 | Data Platform — Schema, Ops & Scale |
| [AA-875](data-platform-schema-ops-scale/AA-875.md) | [Security] SSRF-safe outbound HTTP client (safe_http) for tenant-supplied URLs | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-876](data-platform-schema-ops-scale/AA-876.md) | [Security] API edge hardening: login rate limit, throttle/WAF, Booking docs, CORS, headers | Done | 2026-10-21 | Data Platform — Schema, Ops & Scale |
| [AA-877](data-platform-schema-ops-scale/AA-877.md) | [Data] Tag Booking and TripPlanner PII columns (pii:<class>, DM-6.1) | Done | 2026-10-21 | Data Platform — Schema, Ops & Scale |
| [AA-878](data-platform-schema-ops-scale/AA-878.md) | [Security] Secrets register, orphaned-secret cleanup, read-only E2E account | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-879](data-platform-schema-ops-scale/AA-879.md) | [CI] CI gate parity across CIS, Booking and TripPlanner | Done | 2026-10-22 | Data Platform — Schema, Ops & Scale |
| [AA-887](data-platform-schema-ops-scale/AA-887.md) | [Docs] Adopt the documentation standard — catalog, front-matter schema, templates, glossary, DoR | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-888](data-platform-schema-ops-scale/AA-888.md) | [CI] Docs lint and ADR indexes in every repo — front-matter, links, resource-ID and multi-line CLI checks | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-889](data-platform-schema-ops-scale/AA-889.md) | [Docs] Remove stale docs and agent-instruction drift — CIS runbook v1, root README, steering, stray root files | Done | 2026-10-19 | Data Platform — Schema, Ops & Scale |
| [AA-890](data-platform-schema-ops-scale/AA-890.md) | [CI] PR template, PR title lint and squash-only settings in all repos — plus Infra .bak cleanup | Done | 2026-10-19 | Data Platform — Schema, Ops & Scale |
| [AA-891](data-platform-schema-ops-scale/AA-891.md) | [Release] Version traceability — release-please, CHANGELOG and first tags per app | Done | 2026-10-22 | Data Platform — Schema, Ops & Scale |
| [AA-892](data-platform-schema-ops-scale/AA-892.md) | [Ops] Operations index and runbooks — rollback per component, DB ops index, flag register, incident playbooks | Done | 2026-10-19 | Data Platform — Schema, Ops & Scale |
| [AA-893](data-platform-schema-ops-scale/AA-893.md) | [Infra] Alarm catalog with runbook links and core Terraform outputs — generated inventory, network, IAM tables | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-894](data-platform-schema-ops-scale/AA-894.md) | [Docs/Data] ERD + PRD as code — generated ERD per schema, design ERD + drift check, PRD front matter, /admin/data-model, env-config register | Done | 2026-10-22 | Data Platform — Schema, Ops & Scale |
| [AA-895](data-platform-schema-ops-scale/AA-895.md) | [Security] Security baseline and vulnerability management policy — Dependabot for Booking and TripPlanner | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-897](data-platform-schema-ops-scale/AA-897.md) | [Docs] Engineer onboarding guide and agent instruction index | Done | 2026-10-19 | Data Platform — Schema, Ops & Scale |
| [AA-899](data-platform-schema-ops-scale/AA-899.md) | [API] OpenAPI export and breaking-change check for CIS and Booking | Done | 2026-10-24 | Data Platform — Schema, Ops & Scale |
| [AA-901](data-platform-schema-ops-scale/AA-901.md) | [Security] GitHub App for agents and release-please, ADR 0010/0011, CODEOWNERS (U-25) | Done | 2026-10-22 | Data Platform — Schema, Ops & Scale |
| [AA-902](data-platform-schema-ops-scale/AA-902.md) | [Security] Scrub AWS account IDs and ARNs from tracked files in the public repos | Done | 2026-10-19 | Data Platform — Schema, Ops & Scale |
| [AA-903](data-platform-schema-ops-scale/AA-903.md) | [CI] Skip the "Vercel deploy" job for Dependabot PRs (Booking, TripPlanner, CIS) | Done | 2026-10-21 | Data Platform — Schema, Ops & Scale |
| [AA-907](data-platform-schema-ops-scale/AA-907.md) | [CIS] Bump langchain / langgraph and drop chromadb before the pip-audit ignores expire (30/11, 31/12) | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-912](data-platform-schema-ops-scale/AA-912.md) | Triage CodeQL backlog (CIS) | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-913](data-platform-schema-ops-scale/AA-913.md) | Alert recipients managed from the CIS admin page (no hard-coded e-mail) | Done | 2026-10-20 | Data Platform — Schema, Ops & Scale |
| [AA-981](data-platform-schema-ops-scale/AA-981.md) | Secret scanning guard for public repos: push protection, full-history gitleaks, tfvars password rule | Done | 2026-10-23 | Data Platform — Schema, Ops & Scale |
| [AA-991](data-platform-schema-ops-scale/AA-991.md) | [S1 propagation] Downstream freshness probe + proof that automatic sync works (atom → segment/route/ranking/geo/place/tenant) | Done | 2026-10-27 | Data Platform — Schema, Ops & Scale |
| [AA-650](ecosystem-foundation-cost-guard-jobs-docs/AA-650.md) | [P1] Durable job runner — Postgres queue + worker ECS service (replaces in-process asyncio tasks and the Bedrock Batch dependency) | Done | 2026-09-28 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-651](ecosystem-foundation-cost-guard-jobs-docs/AA-651.md) | [P1][INFRA] Worker ECS service for the job runner (AA-CIS-Infra) | Done | 2026-10-05 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-652](ecosystem-foundation-cost-guard-jobs-docs/AA-652.md) | [P1] Move T2 rewrite, T9 write, research and A3 atomize onto jobs; job-based status in the portal (fixes stuck "Writing…") | Done | 2026-09-28 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-653](ecosystem-foundation-cost-guard-jobs-docs/AA-653.md) | [P2] A/T flow sync audit + clean-rerun runbook (Bhutan pilot wave, Jev in shadow) | Done | 2026-10-08 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-654](ecosystem-foundation-cost-guard-jobs-docs/AA-654.md) | [DOCS] English README + complete CONTEXT.md for every repo; translate root docs; refresh App .claude/CLAUDE.md | Done | 2026-10-11 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-656](ecosystem-foundation-cost-guard-jobs-docs/AA-656.md) | [SEC] Staff auth hardening — real JWT for the content role, BFF proxy coverage, single role model across CIS and AA-Booking | Done | 2026-10-11 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-684](ecosystem-foundation-cost-guard-jobs-docs/AA-684.md) | [DB] Schema ownership map + migration cleanup across repos (shared RDS) | Done | 2026-10-11 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-702](ecosystem-foundation-cost-guard-jobs-docs/AA-702.md) | [Admin UI audit] Fix broken notifications list + inconsistent counts/costs before the platform rerun | Done | 2026-09-30 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-711](ecosystem-foundation-cost-guard-jobs-docs/AA-711.md) | [BUG][Jobs] Draining ECS task keeps claiming jobs after a deploy — runs them on the old code | Done | 2026-10-01 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-723](ecosystem-foundation-cost-guard-jobs-docs/AA-723.md) | [P1] Move ALL remaining in-process API background tasks onto the worker (shared.job) — S1 rewrite, revalidate, recompute; survive deploys + show on Jobs | Done | 2026-10-06 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-725](ecosystem-foundation-cost-guard-jobs-docs/AA-725.md) | [CI] Deploy guard on shared.job + post-deploy live smoke verify + api/worker same image SHA | Done | 2026-10-07 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-730](ecosystem-foundation-cost-guard-jobs-docs/AA-730.md) | [SEC] Narrow IAM role for agent sessions (Kiro / Claude Code); prod migrations only via workflow | Done | 2026-10-11 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-733](ecosystem-foundation-cost-guard-jobs-docs/AA-733.md) | [Docs][Skills] Restructure AA skills — slim SKILL.md + references, delete superseded content, 6 workflow skills, one source in repo skill/ | Done | 2026-10-07 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-734](ecosystem-foundation-cost-guard-jobs-docs/AA-734.md) | [Jobs] atom_ranking versioned-swap so recompute never dips the live count (ADR 0003 nac 2) | Done | 2026-10-06 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-735](ecosystem-foundation-cost-guard-jobs-docs/AA-735.md) | [Jobs] Job-model modularization follow-ups (ADR 0003 nac 3-6) | Done | 2026-10-09 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-750](ecosystem-foundation-cost-guard-jobs-docs/AA-750.md) | [Infra] Audit the 7 CIS Lambdas with 0 invocations in 30 days — confirm still needed vs obsolete, then retire the obsolete ones safely | Done | 2026-10-11 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-755](ecosystem-foundation-cost-guard-jobs-docs/AA-755.md) | [Jobs] Jobs page redesign — server-side pagination, sort and filters on every column, sticky header/toolbar, tabs | Done | 2026-10-10 | Ecosystem Foundation — Cost Guard, Jobs, Docs |
| [AA-1](no-project/AA-1.md) | Get familiar with Linear | Done | 2026-05-13 | — |
| [AA-101](no-project/AA-101.md) | [M6] Master Content — Golden Tours 20 import + 3-config rewrite + Quality Showcase Dashboard for Ms. Thu | Done | 2026-05-22 | — |
| [AA-102](no-project/AA-102.md) | [OPS] Fix schema_versions gap — record migrations 027/029-034 in shared.schema_versions | Done | 2026-05-21 | — |
| [AA-104](no-project/AA-104.md) | [HRN-01] S1 State Bridge Guard — Write-before-Trigger | Done | 2026-06-03 | — |
| [AA-118](no-project/AA-118.md) | [HRN-13] Cost Tracking End-to-End (acp_runs.total_llm_cost_usd) | Done | 2026-06-02 | — |
| [AA-141](no-project/AA-141.md) | [OBS-02] Run-Health single-pane dashboard + SLO/alerting | Done | 2026-06-03 | — |
| [AA-143](no-project/AA-143.md) | [OBS-04] Synthetic canary E2E run (regression detection) | Done | 2026-06-03 | — |
| [AA-145](no-project/AA-145.md) | [FEAT-01] S4.2 v1→v2 — 9-goal strategist upgrade | Done | 2026-06-04 | — |
| [AA-146](no-project/AA-146.md) | [WAVE 0] Observability + Validation Backbone (do first) | Done | 2026-06-05 | — |
| [AA-147](no-project/AA-147.md) | [WAVE 1] Rebuild S2 — Market + Competitor Research | Done | 2026-06-04 | — |
| [AA-148](no-project/AA-148.md) | [WAVE 2] Rebuild S3 — Campaign Planning | Done | 2026-06-03 | — |
| [AA-149](no-project/AA-149.md) | [WAVE 3] Rebuild S4.1 — Blog Engine | Done | 2026-06-04 | — |
| [AA-150](no-project/AA-150.md) | [WAVE 4] Rebuild S4.2 → v2 — Social Media Engine | Done | 2026-06-06 | — |
| [AA-17](no-project/AA-17.md) | Get 6 decisions from Ms. Thư — D-01 to D-06 (schema + image + CIS) | Canceled | 2026-08-21 | — |
| [AA-170](no-project/AA-170.md) | [EPIC] CIS Admin UI — Complete pipeline view S2→S4.2 + remove B2B tenant portal | Done | 2026-06-06 | — |
| [AA-174](no-project/AA-174.md) | [INVESTIGATION] ACP E2E attempt → discovered S1→S4.2 pipeline is not orchestrated | Done | 2026-06-11 | — |
| [AA-178](no-project/AA-178.md) | [LEARN-DVA] DynamoDB deep-dive — single-table, GSI/LSI, streams (cert-only) | Canceled | 2026-08-21 | — |
| [AA-18](no-project/AA-18.md) | Migrate geographic content — areas, countries, destinations, users from legacy MySQL | Canceled | 2026-08-21 | — |
| [AA-181](no-project/AA-181.md) | [INFRA] ACP tenant-auth contract inconsistent across 3 layers (API GW / FastAPI / JWT) | Done | 2026-06-11 | — |
| [AA-182](no-project/AA-182.md) | [CIS] Verify aa-cis-dev-pipeline SM works → migrate CIS to SM or retire it (currently ECS-direct) | Canceled | 2026-09-04 | — |
| [AA-186](no-project/AA-186.md) | [ACP-ORCH-5] Gate-as-event-boundary wiring (Gate 1/2/3) + HITL request + resume | Done | 2026-06-15 | — |
| [AA-19](no-project/AA-19.md) | CIS → AAA sync — implement content pipeline to trip_plans (Option A: scheduled pull) | Canceled | 2026-08-21 | — |
| [AA-193](no-project/AA-193.md) | S1 Content Quality: DataForSEO keyword sourcing + brand differentiation + day-title/meta fixes | Done | 2026-06-22 | — |
| [AA-194](no-project/AA-194.md) | [AA-193·F5] SEO title/meta cut-off — canonical 60/155 + word-boundary trim across 4 layers | Done | 2026-06-16 | — |
| [AA-195](no-project/AA-195.md) | [AA-193·F3] Itinerary: strip fabricated meals + clock-times (prevent in prompt, catch in audit) | Done | 2026-06-16 | — |
| [AA-196](no-project/AA-196.md) | [AA-193·F4] Day-by-day titles must name place/activity (string format + validator, no schema change) | Done | 2026-06-16 | — |
| [AA-197](no-project/AA-197.md) | [AA-193·F2] DataForSEO rebuild — seed location+activity, buyer-market location_code, PAA+related+ideas | Done | 2026-06-16 | — |
| [AA-198](no-project/AA-198.md) | [AA-193·F1] Brand differentiation — wire brand_identity_id + fix fallback + admin brand-picker preview | Done | 2026-06-16 | — |
| [AA-2](no-project/AA-2.md) | Set up your teams | Done | 2026-05-13 | — |
| [AA-202](no-project/AA-202.md) | [AA-193·F1-followup] Brand differentiation still weak — rewrite 4 brand prompts (đậm) + code contrast | Done | 2026-06-17 | — |
| [AA-203](no-project/AA-203.md) | [UI] Hiển thị DataForSEO keyword_ideas trên admin S1 (bảng keyword + volume + competition + cpc) | Done | 2026-06-18 | — |
| [AA-204](no-project/AA-204.md) | [AA-193·F5-over-band] SEO meta over-length cụt câu vào gold — repair-to-band over-length + observability | Done | 2026-06-17 | — |
| [AA-206](no-project/AA-206.md) | [AA-193·F1] S1 Two-Model Generate–Judge: Bedrock viết + GPT-4.1 chấm brand-fit + tăng cường diff_block (gộp AA-207) | Done | 2026-06-17 | — |
| [AA-216](no-project/AA-216.md) | [AA-193·gate] Empty/missing-field generation lọt gate 7.0 vào gold — validate sub-score trung bình bị bucket trống kéo cao | Done | 2026-06-20 | — |
| [AA-217](no-project/AA-217.md) | [AA-193·generate] Haiku retry=1 malformed-JSON empty-gen + cost-accounting leak — deterministic json-repair salvage | Done | 2026-06-20 | — |
| [AA-218](no-project/AA-218.md) | [AA-193·DFS] Persist PAA + related_keywords vào seo_context (migration + handler + endpoint) | Done | 2026-06-22 | — |
| [AA-219](no-project/AA-219.md) | [AA-193·UI] VersionCompare: surface judge + quality + audit + failure_codes + revalidate + full DFS per version | Done | 2026-06-22 | — |
| [AA-220](no-project/AA-220.md) | [AA-193·export] Multi-version compare export (XLSX/CSV) + single-version full DOCX | Done | 2026-06-23 | — |
| [AA-222](no-project/AA-222.md) | _execute_run_tour crashes on not-publishable runs: INSERT status="pending" invalid for content_status_enum | Done | 2026-06-22 | — |
| [AA-226](no-project/AA-226.md) | [AA-193·F5] SEO meta lọt dưới floor 140 sau fix_pass (Trail Pulse/Sonnet = 132) | Done | 2026-06-23 | — |
| [AA-24](no-project/AA-24.md) | [Admin] Dashboard, SEO & Cost — tất cả metrics/data dùng giá trị thực từ DB, không hardcode | Done | 2026-05-13 | — |
| [AA-246](no-project/AA-246.md) | AWS Account Migration: 867490540162 (management acc) → 005097885195 (độc lập, TrueIDC fund) + build hạ tầng mới | Done | 2026-07-15 | — |
| [AA-25](no-project/AA-25.md) | [Admin] Tenants — fix "Failed to load" + thêm detail view (tours, SEO, keywords, cost) | Done | 2026-05-12 | — |
| [AA-254](no-project/AA-254.md) | [CIS-OBS] Ops diagnosis panel — rule-based failure triage, extend Health tab | Canceled | 2026-09-23 | — |
| [AA-255](no-project/AA-255.md) | [COMMAND-CENTER] Unified Admin Dashboard — Infra + LLM Ops + Cost (real-time, 1 trang) | Canceled | 2026-09-23 | — |
| [AA-256](no-project/AA-256.md) | [COMMAND-CENTER 1/4] AWS Cost Explorer integration — cost breakdown thật theo service/ngày | Canceled | 2026-09-23 | — |
| [AA-257](no-project/AA-257.md) | [COMMAND-CENTER 2/4] Live infra state endpoint — ECS/RDS/NAT/Redis health | Done | 2026-09-04 | — |
| [AA-26](no-project/AA-26.md) | [CIS] Upload pipeline + DB audit — verify end-to-end, schema alignment, fix src_itineraries REQUIRED | Done | 2026-05-12 | — |
| [AA-261](no-project/AA-261.md) | [ACP-Portal][SECURITY] STEP 0 audit — sessionStorage-only auth, 0 server-side middleware | Done | 2026-07-06 | — |
| [AA-263](no-project/AA-263.md) | [CIS][S1] Tách node editor độc lập khỏi validate_node trong S1 graph (từ ADR-2026-020) | Canceled | 2026-09-04 | — |
| [AA-265](no-project/AA-265.md) | [Track B][Terraform] Account-2 root config riêng — reuse modules, scope WAF/APIGW/SF/EventBridge | Done | 2026-07-15 | — |
| [AA-266](no-project/AA-266.md) | [URGENT] RDS password drift account 1 — TF_VAR_DB_PASSWORD (GitHub secret) lệch khỏi giá trị thật, block merge develop | Done | 2026-07-07 | — |
| [AA-27](no-project/AA-27.md) | [Admin] Catalog — filter bar, bỏ char limit, fix format Highlights/Inclusions/Exclusions, SEO keywords, Audit panel | Done | 2026-05-13 | — |
| [AA-277](no-project/AA-277.md) | Trunk-based CI/CD migration — remove develop branch (ADR-2026-023) | Done | 2026-07-09 | — |
| [AA-28](no-project/AA-28.md) | [Admin+Tenant] Catalog — multi-select tours để export CSV/Excel | Done | 2026-05-13 | — |
| [AA-29](no-project/AA-29.md) | [Tenant] My Catalog — fix Itinerary format xuống dòng per day + bỏ char limit AI rewrite | Done | 2026-05-13 | — |
| [AA-3](no-project/AA-3.md) | Connect your tools | Done | 2026-05-13 | — |
| [AA-30](no-project/AA-30.md) | [Admin] Catalog — fix Highlights format: JSON array string → bullet list xuống dòng | Done | 2026-05-15 | — |
| [AA-31](no-project/AA-31.md) | [Admin] Catalog — SEO section: hiển thị keywords nguồn DFS (KEYWORD_SEARCH, PAA, RELATED, IDEAS) | Done | 2026-05-15 | — |
| [AA-311](no-project/AA-311.md) | [Bug] Upload S0 báo "Commit failed (500)" sai — data đã lưu DB đúng, lỗi thật là StartExecution AccessDenied gọi thừa sau khi INSERT xong | Done | 2026-07-20 | — |
| [AA-312](no-project/AA-312.md) | [Bug][Frontend?] Upload S0 Commit — 4/14 file "0 tours saved" vì request chưa từng tới backend (không phải lỗi mất dữ liệu) | Done | 2026-07-20 | — |
| [AA-313](no-project/AA-313.md) | [Bug] country_resolver.py thiếu/sai alias — PAKISTAN không có trong COUNTRY_MASTER, SRI-LANDKA (typo toàn công ty) không match Sri Lanka | Done | 2026-07-20 | — |
| [AA-32](no-project/AA-32.md) | [Admin] Catalog — thêm Audit/Validation status panel (AUDIT_STATUS, FAILURE_CODES, ISSUES, FIELDS_UPDATED) | Done | 2026-05-15 | — |
| [AA-33](no-project/AA-33.md) | [Admin] Catalog — Inclusions/Exclusions: render xuống dòng per item thay vì inline text | Done | 2026-05-15 | — |
| [AA-338](no-project/AA-338.md) | [ACPv2-Model] 3 dữ kiện chưa giải quyết từ AA-335 — Nova Batch, Nova Lite caching, giá Cohere Embed v4 | Canceled | 2026-09-04 | — |
| [AA-34](no-project/AA-34.md) | [Admin] Catalog — multi-select tours để export CSV/Excel | Done | 2026-05-15 | — |
| [AA-341](no-project/AA-341.md) | [CIS-S1] Gom nợ kỹ thuật S1 cũ — 2 gap code + persist stop_reason + max_tokens override (làm 1 lượt, không làm lẻ) | Canceled | 2026-09-04 | — |
| [AA-35](no-project/AA-35.md) | [Tenant] My Catalog — Itinerary: giữ format xuống dòng per day (không collapse thành paragraph) | Done | 2026-05-15 | — |
| [AA-36](no-project/AA-36.md) | [Tenant] My Catalog — bỏ giới hạn chữ cho tất cả fields AI rewrite | Done | 2026-05-15 | — |
| [AA-37](no-project/AA-37.md) | [Tenant] My Catalog — multi-select tours để export CSV/Excel | Done | 2026-05-15 | — |
| [AA-4](no-project/AA-4.md) | Import your data | Done | 2026-05-13 | — |
| [AA-40](no-project/AA-40.md) | [ACP-CORE] EventBridge bus + S3 buckets + API GW routes — Terraform | Done | 2026-05-13 | — |
| [AA-407](no-project/AA-407.md) | [ACPv2][N7][Chờ Ms. Thư] F10 AI-detector trend logger — chưa build, signal-only không chặn gate, cần bàn giá trị trước khi đầu tư | Canceled | 2026-09-04 | — |
| [AA-41](no-project/AA-41.md) | [ACP-CORE] DB schema migration — 5 new schemas + RLS + pgvector | Done | 2026-05-12 | — |
| [AA-43](no-project/AA-43.md) | [ACP-S2] Market & Competitor Research Agent — FastAPI + DataForSEO + Apify + LLM | Done | 2026-05-20 | — |
| [AA-44](no-project/AA-44.md) | [ACP-S0] Input Manager — XLSX upload + Data Quality Review Page + Manual S1 Gate | Done | 2026-05-19 | — |
| [AA-447](no-project/AA-447.md) | [A/T-SYNC-AUDIT] Rà soát đồng bộ BE+FE+hạ tầng cho từng T-stage/A-stage — tránh build lệch tầng | Canceled | 2026-09-03 | — |
| [AA-45](no-project/AA-45.md) | [ACP-S3] Content & Campaign Planner — Lambda + LLM + Content Calendar + Ads + TikTok | Done | 2026-05-20 | — |
| [AA-46](no-project/AA-46.md) | [ACP-S4] Blog Engine — Draft + Self-Critique + SEO + HITL + CMS Publish | Done | 2026-05-21 | — |
| [AA-47](no-project/AA-47.md) | [ACP-UAT] Full E2E pipeline test — 1 country, all stages, all HITL gates | Done | 2026-05-22 | — |
| [AA-472](no-project/AA-472.md) | [TENANT ONBOARDING] Bỏ ràng buộc bắt buộc portfolio_id khi tạo tenant — Hướng B | Done | 2026-08-26 | — |
| [AA-473](no-project/AA-473.md) | [ADMIN] Chuyển atomize (N0-N2) + curation (N3) Master Content sang tenant tự làm, xoá /admin/atomize + /admin/curation | Done | 2026-08-27 | — |
| [AA-475](no-project/AA-475.md) | [ADMIN] Xoá hẳn /admin/atomize + /admin/curation + toàn bộ 2551 atom owner_scope='platform' | Done | 2026-08-27 | — |
| [AA-477](no-project/AA-477.md) | [INVESTIGATE] Cụm 14 bảng ACPv1 (gốc acp_runs) + 6 router + 2 Lambda — 0 row/0 invocation nhưng chưa xác nhận độc lập với A/T-series | Done | 2026-08-27 | — |
| [AA-48](no-project/AA-48.md) | [INFRA] Setup Claude Code + Chat Workflow — CLAUDE.md + Hooks + Skills + Subagents | Done | 2026-05-11 | — |
| [AA-482](no-project/AA-482.md) | [BUILD] Landing page engine — tự host trang giới thiệu tour per-tenant (ADR-2026-030, tách từ AA-395) | Done | 2026-09-04 | — |
| [AA-483](no-project/AA-483.md) | [INVESTIGATE] Race condition nghi vấn ở process_export() — batch completion check thiếu lock, có thể tái diễn | Done | 2026-09-03 | — |
| [AA-484](no-project/AA-484.md) | [BUILD] Cannibalization gate T10 — ưu tiên case tenant thiếu tenant_brand_rules | Done | 2026-09-03 | — |
| [AA-485](no-project/AA-485.md) | [BUILD] Buffer HELD retry — tự động re-queue content_piece bị T10 reject | Done | 2026-09-03 | — |
| [AA-486](no-project/AA-486.md) | [BUILD] LLM cost tracking theo tenant + stage — thiết kế mới, không tái dùng cost_utils.py đã chết | Canceled | 2026-09-04 | — |
| [AA-487](no-project/AA-487.md) | [BUILD] Sanitize brand brief input (S0) trước khi build system_prompt — prompt injection surface | Done | 2026-09-03 | — |
| [AA-488](no-project/AA-488.md) | [BUILD] 2 gap dedup nhỏ từ AA-476 STEP0 — dedup trong-file + lệch logic dry_run/Commit | Done | 2026-08-28 | — |
| [AA-489](no-project/AA-489.md) | [BUILD] Rewrite quota/tháng theo tenant — chưa từng được enforce, cần thiết kế mới | Done | 2026-09-04 | — |
| [AA-49](no-project/AA-49.md) | [ACP-HARNESS] Harness Engineering Layer — Isolated Evaluator + Output Rules + Mistake→Rule Pipeline | Done | 2026-05-21 | — |
| [AA-490](no-project/AA-490.md) | [FOLLOW-UP AA-488] dry_run preview chưa có in-file dedup — trùng dòng chỉ phát hiện sau khi Commit | Done | 2026-09-04 | — |
| [AA-491](no-project/AA-491.md) | [FOLLOW-UP] Gỡ --ignore cho test_h3_rule_extractor.py + test_run_health.py sau khi sửa 7 test fail sẵn | Done | 2026-09-04 | — |
| [AA-492](no-project/AA-492.md) | [CLEANUP] services/export/handler.py — dọn nhánh ACP-S1 EventBridge chết (0 consumer từ đầu, không ảnh hưởng A/T) | Done | 2026-09-05 | — |
| [AA-495](no-project/AA-495.md) | [RESET] Xóa sạch dữ liệu A/T-series, giữ >700 tour thô — chạy E2E A0-T11 với dữ liệu sạch, 2 phase | Canceled | 2026-09-16 | — |
| [AA-496](no-project/AA-496.md) | /api/admin/billing trả 401 trên mọi trang /portal/* — layout.tsx gọi endpoint admin từ tenant portal | Done | 2026-09-04 | — |
| [AA-502](no-project/AA-502.md) | [T7 planning] Làm rõ UX chọn tour để tính plan + giải thích cơ chế "Finalize this quarter" | Canceled | 2026-08-31 | — |
| [AA-503](no-project/AA-503.md) | [/portal] Audit toàn bộ trang tenant-facing — đảm bảo chỉ dùng tiếng Anh, không lẫn tiếng Việt | Canceled | 2026-09-05 | — |
| [AA-507](no-project/AA-507.md) | [EPIC][REDESIGN T5-T11] Segment/Route/Slate — rebuild theo aa-social-media reference (Ms. Thư) | Done | 2026-09-03 | — |
| [AA-508](no-project/AA-508.md) | [T5] Atom identity content-hash + cache theo ngày + partial commit | Done | 2026-09-01 | — |
| [AA-509](no-project/AA-509.md) | [Segment] Lớp mới — group atom cùng moment thật, schema + thuật toán matching | Done | 2026-09-03 | — |
| [AA-510](no-project/AA-510.md) | [Route/Hub] Lớp mới, chỉ phục vụ Blog — schema + phát hiện hành trình | Done | 2026-09-01 | — |
| [AA-511](no-project/AA-511.md) | [T7] Slate — thay Weekly Slots, schema Subject + service + router + frontend | Done | 2026-09-02 | — |
| [AA-512](no-project/AA-512.md) | [T8] Bỏ bước chọn Channel, angle ranking bằng số đo được | Done | 2026-09-03 | — |
| [AA-513](no-project/AA-513.md) | [T9] Route-aware write — nhiều Segment trong 1 bài Blog, mở rộng provenance tag | Done | 2026-09-02 | — |
| [AA-514](no-project/AA-514.md) | [T10] Bổ sung gate "promises an option" + SEO surface + structural variance route-aware | Done | 2026-09-02 | — |
| [AA-515](no-project/AA-515.md) | [Ranking/Atom Score] Stage xếp hạng atom — điều kiện tiên quyết cho AA-510 (Route/Hub) | Done | 2026-09-01 | — |
| [AA-517](no-project/AA-517.md) | [INFRA] Điều tra chi phí RDS + Secrets Manager lạc trên acc 1 (867490540162) — nghi setup nhầm acc, kiểm tra luôn GPT-4.1 key rotation | Done | 2026-09-02 | — |
| [AA-519](no-project/AA-519.md) | [T5-T11] UI polish + route/hub metadata thread-through (từ audit AA-507) | Done | 2026-09-03 | — |
| [AA-522](no-project/AA-522.md) | [URGENT][T7-T9] Luồng viết mới từ Slate không lưu bài vào Review — luồng cũ Atom/Goal/Angle/Channel song song vẫn còn sống, gây nhầm lẫn | Done | 2026-09-05 | — |
| [AA-523](no-project/AA-523.md) | [T5-T7][UI GAP] Thiếu UI truy vết Tour→Atom hóa→Slate — không rõ Segment/Hub/Picked từ đâu ra, chọn theo logic nào | Canceled | 2026-09-05 | — |
| [AA-524](no-project/AA-524.md) | [T5-T11][UI POLISH] Layout hẹp, header mất khi cuộn, còn sót tiếng Việt — rà lại thiết kế toàn portal | Done | 2026-09-11 | — |
| [AA-525](no-project/AA-525.md) | [INVESTIGATE][ARCH DECISION] Đọc kỹ repo aa-social-media, đối chiếu AA-507 — build tiếp hay đập bỏ xây lại T5-T11 theo pattern gốc? | Done | 2026-09-05 | — |
| [AA-526](no-project/AA-526.md) | [ARCH][T5] Di dời Atomize sang A-series (trigger tại A3) — gỡ bỏ hoàn toàn khỏi luồng tenant, không lộ atom ra tenant | Done | 2026-09-05 | — |
| [AA-527](no-project/AA-527.md) | [ARCH][ADMIN] Xây trang admin Atom Curation mới — thay thế vai trò T6, AA duyệt atom nào gắn tour nào | Done | 2026-09-05 | — |
| [AA-528](no-project/AA-528.md) | [T9][BUG] Viết lại toàn bộ khi sửa Gate gây hồi quy — 56% piece kẹt held, cần gate-regression-guard | Done | 2026-09-06 | — |
| [AA-529](no-project/AA-529.md) | [T9][GAP] Thiếu tầng Facts Entry — claim giá/mùa/visa không có nguồn trích, kẹt held vĩnh viễn | Done | 2026-09-05 | — |
| [AA-530](no-project/AA-530.md) | [DESIGN][UI] Thiết kế trang tổng thể luồng T5-T11 — phân cấp, show toàn bộ thành phần từ dữ liệu output — CHƯA CODE | Canceled | 2026-09-05 | — |
| [AA-531](no-project/AA-531.md) | [T9][BUG] Blog bị gate chặn oan vì dùng chung ngưỡng độ dài với 7 kênh ngắn — trần chỉ bằng nửa chuẩn | Done | 2026-09-05 | — |
| [AA-532](no-project/AA-532.md) | [T7][BUG] route_detection.py xoá-toàn-bộ-rồi-insert-lại vi phạm FK subject.route_id — chuyển sang versioning | Done | 2026-09-05 | — |
| [AA-533](no-project/AA-533.md) | [INVESTIGATE][PRE-EPIC] Đọc repo aa-social-media — Atom→Segment→Route/Hub→Slate→Write: bước nào dùng chung, bước nào phải riêng theo tenant | Done | 2026-09-05 | — |
| [AA-534](no-project/AA-534.md) | [INVESTIGATE][PRE-EPIC] Đọc code S1 rewrite + Atomize/Segment/Score/Slate hiện tại của AA-CIS — so sánh với kiến trúc Ms. Thư | Done | 2026-09-05 | — |
| [AA-535](no-project/AA-535.md) | [S1][BRAND] SYSTEM_PROMPT hardcode giọng "Adventure Asia" — viết lại trung tính cho Master Content chung | Done | 2026-09-05 | — |
| [AA-536](no-project/AA-536.md) | [INVESTIGATE][PRE-EPIC] Bảng map file-by-file đầy đủ Ms. Thư ↔ AA-CIS + xác nhận DFS multi-market và Facts Entry | Done | 2026-09-06 | — |
| [AA-537](no-project/AA-537.md) | [INVESTIGATE] Xác nhận AA-528 và AA-463 còn phù hợp hay đã lỗi thời so với luồng hiện tại | Done | 2026-09-06 | — |
| [AA-538](no-project/AA-538.md) | [DFS][COST] Batch hoá fetch_keyword_ideas() — hiện vẫn gọi 1 keyword/request trong vòng lặp Segment research | Canceled | 2026-09-19 | — |
| [AA-539](no-project/AA-539.md) | [PROCESS] Cài đặt bộ skill Matt Pocock (domain-modeling, grill-with-docs, improve-codebase-architecture) — xây CONTEXT.md/glossary chính thức trước epic UI Admin/Tenant | Done | 2026-09-06 | — |
| [AA-540](no-project/AA-540.md) | [INVESTIGATE][PRE-EPIC] Resolve Open Question 1 — bảng đầy đủ Admin/Tenant + cơ chế cross-tenant cho toàn luồng T5-T11 | Done | 2026-09-06 | — |
| [AA-541](no-project/AA-541.md) | [INVESTIGATE] Xác nhận input thật của Segment (atom gốc hay atom đã rewrite) và lý do kỹ thuật thật cho quyết định per-tenant | Done | 2026-09-06 | — |
| [AA-542](no-project/AA-542.md) | [PROCESS][URGENT] Sửa CONTEXT.md + ADR-0001 tại repo — Segment/Score/Route/Hub per-tenant là NỢ KỸ THUẬT cần sửa, không phải thiết kế đúng | Done | 2026-09-06 | — |
| [AA-543](no-project/AA-543.md) | [INVESTIGATE][ARCH] Điều tra thật để thiết kế Segment/Score/Route/Hub platform-wide (mở rộng kiểm tra ranh giới Slate T7) — KHÔNG CODE | Done | 2026-09-07 | — |
| [AA-544](no-project/AA-544.md) | [SECURITY][GAP] seo_context RLS không có hiệu lực thật — schema nói per-tenant, runtime bypass hoàn toàn (aa_cis_admin superuser + GUC never set) | Done | 2026-09-10 | — |
| [AA-545](no-project/AA-545.md) | [ARCH][SPEC] Redesign Segment/Score/Route/Hub thành platform-wide — 1 PR/1 migration duy nhất | Done | 2026-09-06 | — |
| [AA-546](no-project/AA-546.md) | [INVESTIGATE][UI] Điều tra hiện trạng + nhu cầu UI Admin giám sát Segment/Score/Route/Hub platform-wide — KHÔNG CODE | Done | 2026-09-07 | — |
| [AA-547](no-project/AA-547.md) | [INVESTIGATE][UI] Điều tra lại AA-469 — trạng thái thật UI T-series (T5 tách, T7 edit, T8/T11 evidence gap) — KHÔNG CODE | Done | 2026-09-07 | — |
| [AA-548](no-project/AA-548.md) | [UI][BUG] atom-curation: bỏ cột Tenant vô nghĩa, thêm cột Market, sửa rowKey trùng (hậu quả AA-545) | Done | 2026-09-06 | — |
| [AA-549](no-project/AA-549.md) | [CLEANUP] Xóa 2 route mồ côi "xem lịch sử quarter-plan" (T7 cũ, đã thay bởi Slate/AA-519) | Done | 2026-09-06 | — |
| [AA-550](no-project/AA-550.md) | [AUDIT][UI] Audit lại UI thật /admin/atom-curation bằng ảnh chụp — đối chiếu mâu thuẫn với báo cáo Done AA-546/548 | Done | 2026-09-07 | — |
| [AA-551](no-project/AA-551.md) | [BUILD][UI] Tách /admin/atom-curation (platform-wide 01-05) + /admin/tenant-activity mới (06-08) — kèm API mới, filter/header, sticky, i18n, điều tra bug 401 | Done | 2026-09-07 | — |
| [AA-552](no-project/AA-552.md) | [INVESTIGATE][UI] Giải thích + điều tra 8 nhóm vấn đề UX/nội dung trên /admin/atom-curation + /admin/tenant-activity (review sau AA-551) — KHÔNG CODE | Done | 2026-09-07 | — |
| [AA-553](no-project/AA-553.md) | [INVESTIGATE][UI] Đánh giá trùng lặp Cross-Tenant Oversight vs Tenants/Tenant Activity + di chuyển & đổi tên "Atom Curation" trong sidebar | Done | 2026-09-07 | — |
| [AA-554](no-project/AA-554.md) | [BUILD][UI] Social Content rename + sticky Tours + multi-select star + Segment/Score/Route link+legend + Hub/Slate decisions + i18n cleanup (tổng hợp AA-552/553) | Done | 2026-09-07 | — |
| [AA-555](no-project/AA-555.md) | [INVESTIGATE][UI-TENANT] Rà soát hiện trạng UI phía Tenant sau AA-526/AA-519 — Browse Pool (T4), Slate (T7), Write/My Catalog (T9), Review (T10), Publish (T11) | Done | 2026-09-07 | — |
| [AA-556](no-project/AA-556.md) | [BUILD][UI] Tenant-facing "Cut" button for Slate proposals | Done | 2026-09-10 | — |
| [AA-557](no-project/AA-557.md) | [BUILD][UI] Sửa lỗi sticky header còn sót + table/sort/filter cho Segment/Score/Route/Hub/Slate + Tenant page cleanup (feedback trực tiếp Nghiệp 07/09) | Done | 2026-09-09 | — |
| [AA-558](no-project/AA-558.md) | [INVESTIGATE] Gộp 06 Write/Gate + 07 Review + 08 Publish thành "theo dõi 1 bài viết đầy đủ" + bỏ Cross-Tenant Oversight + điều tra API Usage/Rate Limit/Activity Log thật vs mock | Done | 2026-09-07 | — |
| [AA-559](no-project/AA-559.md) | [BUILD][BACKEND] Ghi log hoạt động ngữ nghĩa của Tenant (login/pick Slate/write/rewrite) — mở khóa AA-557 mục 21 | Done | 2026-09-09 | — |
| [AA-560](no-project/AA-560.md) | [BUILD][UI] Trang "07" (Review Log + Trust Ramp + gate aggregate) thay Cross-Tenant Oversight + Force unpublish chuyển vào Content Trace (06) | Done | 2026-09-09 | — |
| [AA-561](no-project/AA-561.md) | [FIX+INVESTIGATE][UI] Sửa dứt điểm A/B report-sai + điều tra Segment đa-tour + Slate dễ hiểu + xây lineage thật cho 06-08 (Nghiệp tự chụp ảnh phát hiện AA-557 sai) | Done | 2026-09-07 | — |
| [AA-562](no-project/AA-562.md) | [BUILD][UI] Đổi tên "06-08 · Tenant Activity" → "Content Trace" (tên đúng bản chất theo dõi vòng đời bài viết) | Done | 2026-09-09 | — |
| [AA-563](no-project/AA-563.md) | [EPIC][INVESTIGATE] Điều tra toàn diện cơ chế trigger Atomize→Segment→Score→Route/Hub→Slate + thiết kế lại Slate đúng bản chất per-tenant (dùng grill-with-docs) | Done | 2026-09-08 | — |
| [AA-564](no-project/AA-564.md) | [BUILD] Triển khai thiết kế AA-563: sửa bug sticky/star/stats, Slate Admin theo Tenant, Atomize backfill, gộp Slate+Write inline (Tenant Portal), đồng bộ layout My Catalog | Done | 2026-09-09 | — |
| [AA-565](no-project/AA-565.md) | [BUILD][UI] T4 My Catalog (Tenant Portal): đồng bộ layout với Admin Master Content — wireframe trước, giữ panel biên tập riêng | Done | 2026-09-08 | — |
| [AA-566](no-project/AA-566.md) | [BUILD][UI] Sửa bug đếm sai My Catalog + audit sticky header toàn hệ thống + nâng cấp UX My Catalog/Browse Pool/bỏ Rewrite Config | Done | 2026-09-09 | — |
| [AA-567](no-project/AA-567.md) | [URGENT][BUG] pick_subject() không bao giờ hoạt động cho atom platform-wide — chặn toàn bộ pipeline Slate→Write cho gần như mọi tenant | Done | 2026-09-09 | — |
| [AA-568](no-project/AA-568.md) | [BUILD][UI] Gộp 3 trang con Write/Review/Publish thành 1 trang "06 - Content Trace" — lineage chi tiết per-bài-viết, lọc theo tenant | Done | 2026-09-09 | — |
| [AA-569](no-project/AA-569.md) | [INVESTIGATE] Trạng thái thật của trang tenant xem/edit/save/xuất bài viết sau khi viết xong | Done | 2026-09-11 | — |
| [AA-570](no-project/AA-570.md) | [INVESTIGATE] Có nên lưu snapshot nội dung mỗi lần retry (content diff thật) không? | Done | 2026-09-11 | — |
| [AA-571](no-project/AA-571.md) | Data quality: normalize raw_tours.country (SRI-LANDKA, OKINAWA, possibly more) | Done | 2026-09-11 | — |
| [AA-572](no-project/AA-572.md) | [FIX][UI] Content Trace (AA-568) — English labels, tenant stats header, sortable columns, expandable content, lineage line breaks, sticky header | Done | 2026-09-09 | — |
| [AA-573](no-project/AA-573.md) | [BUG] Login stuck on "Connecting..." indefinitely despite backend 200 + real redirect (manual refresh required) | Done | 2026-09-09 | — |
| [AA-574](no-project/AA-574.md) | [INVESTIGATE][BUG] Login screen flashes and reloads to empty form — no POST fired, no console error (distinct from AA-573) | Canceled | 2026-09-09 | — |
| [AA-575](no-project/AA-575.md) | [FIX][UI] Content Trace — sub-nav 01-06 disappears when navigating in, sort missing on most columns | Done | 2026-09-09 | — |
| [AA-576](no-project/AA-576.md) | [FIX][UI] Tenant portal — dịch nốt tiếng Việt còn sót, dọn /portal/t8-angle-gate nếu dead code, đề xuất đổi tên sidebar | Done | 2026-09-10 | — |
| [AA-577](no-project/AA-577.md) | [SECURITY] Swagger UI (/docs) công khai ở production — yêu cầu X-Admin-Secret trước khi xem | Done | 2026-09-11 | — |
| [AA-578](no-project/AA-578.md) | [RISK NOTE] 3 route (tours/my-versions/billing) sẽ vỡ nếu bật RLS thật cho published_tours/raw_tours trong tương lai | Done | 2026-09-11 | — |
| [AA-579](no-project/AA-579.md) | [BUG][INVESTIGATE] GET /v1/tours và POST /v1/exports có thể đang trả rỗng cho mọi tenant thật — không liên quan RLS | Done | 2026-09-10 | — |
| [AA-58](no-project/AA-58.md) | [ACP-CONTRACT] acpcore package + OpenAPI codegen + ACPError standard + SSE /stream endpoint | Done | 2026-05-18 | — |
| [AA-580](no-project/AA-580.md) | [BUG] /catalog (staff) 401 từ AA-232 hotfix — dùng thật gần đây, cần khôi phục Bearer hoặc chuyển sang admin_atoms.py | Done | 2026-09-10 | — |
| [AA-581](no-project/AA-581.md) | [BUG] CONTENT_PASSWORD rỗng trên Vercel Production — login role content trả 503 | Done | 2026-09-10 | — |
| [AA-582](no-project/AA-582.md) | [INVESTIGATE] GET /v1/tours/{tour_id} và .../full (nhánh JWT-tenant) luôn 404 — xác nhận caller thật trước khi quyết hướng xử lý | Done | 2026-09-11 | — |
| [AA-583](no-project/AA-583.md) | [INVESTIGATE] API Gateway routing gap — /docs/redoc/openapi.json không đồng bộ trên domain chính, khả năng liên quan AA-432 | Done | 2026-09-11 | — |
| [AA-584](no-project/AA-584.md) | [UI] My Catalog Tours (t4-pool) — panel chi tiết tour hẹp hơn Browse Tours (t1-rewrite), mở rộng cho khớp | Done | 2026-09-11 | — |
| [AA-585](no-project/AA-585.md) | [SECURITY][INVESTIGATE] GET /tours + /tours/{tour_id} — route legacy không auth, xác nhận có sống qua đường ALB bypass (giống AA-577) không | Done | 2026-09-11 | — |
| [AA-586](no-project/AA-586.md) | [BUG] Ô search chung trên topbar tự điều hướng sang t1-rewrite khi focus, làm mất trang đang xem | Done | 2026-09-11 | — |
| [AA-587](no-project/AA-587.md) | [DOCS] AA-CIS-Infra CLAUDE.md ghi sai account/profile — root Terraform cũ trỏ state bucket đã bị xóa | Done | 2026-09-11 | — |
| [AA-59](no-project/AA-59.md) | [ACP-SECURITY] Secrets Manager + audit_log + WAF ACP rules + git-secrets + pip-audit CI | Done | 2026-05-20 | — |
| [AA-61](no-project/AA-61.md) | [ACP-RELIABILITY] DLQ + checkpoint janitor + S3 mirror + cost caps + stage retry API | Done | 2026-05-18 | — |
| [AA-616](no-project/AA-616.md) | [EPIC] Giám sát chi phí LLM/DFS + tối ưu model/batch từng stage | Done | 2026-10-09 | — |
| [AA-617](no-project/AA-617.md) | [Sub A][BE] LLM instrumentation — thêm account/fallback/provider vào llm_call_log + thread satellite_account | Done | 2026-09-18 | — |
| [AA-618](no-project/AA-618.md) | [Sub B][BE] DFS/DataForSEO usage logging — bảng dfs_call_log (cost/cache_hit/live) tại điểm gọi | Done | 2026-09-18 | — |
| [AA-619](no-project/AA-619.md) | [Sub C][MEASURE] A/B atomize Haiku vs Sonnet → hạ t5_atomize xuống Haiku (lever tiết kiệm lớn nhất) | Done | 2026-09-18 | — |
| [AA-62](no-project/AA-62.md) | [ACP-QUALITY] Factual grounding + semantic internal linking + granular Gate 3 + image sourcing | Done | 2026-05-21 | — |
| [AA-620](no-project/AA-620.md) | [Sub G][BE] Tách stage t2_generate (config UI) + Sonnet cho T2 tenant (A1 giữ Haiku) + thread tenant_id qua S1 graph | Done | 2026-09-18 | — |
| [AA-621](no-project/AA-621.md) | [Sub D][BE] Batch atomize — mở rộng Bedrock Batch (AA-606) sang t5_atomize | Canceled | 2026-10-12 | — |
| [AA-622](no-project/AA-622.md) | [Sub E][FE+BE] UI admin "External Spend" thống nhất — LLM theo account/model/stage/fallback + DFS + reconcile Cost Explorer | Done | 2026-09-18 | — |
| [AA-623](no-project/AA-623.md) | [Sub F][BE+INFRA] AWS Cost Explorer reconcile — đối chiếu hóa đơn Bedrock/AWS thật với cost tính từ token | Done | 2026-09-23 | — |
| [AA-624](no-project/AA-624.md) | [BLOCKER] Bedrock Batch chưa enable trên acc3 (AWS case 178979743800653) + DFS hết tiền — chặn AA-621/606/G4/G5 | Canceled | 2026-10-12 | — |
| [AA-63](no-project/AA-63.md) | [ACP-PRODUCT] Brand brief reuse + admin onboarding + GDPR off-boarding + run comparison | Done | 2026-05-21 | — |
| [AA-635](no-project/AA-635.md) | [BE] llm_call_log under-reports Bedrock spend vs AWS bill (acc1 ~99% missing, acc3 ~20%) | Done | 2026-09-24 | — |
| [AA-643](no-project/AA-643.md) | [EVAL] Jev (TypeSafe) offline eval on real CIS data — F8, T3 grounding, A3 keyword/PAA gates | Duplicate | 2026-09-29 | — |
| [AA-644](no-project/AA-644.md) | [EVAL] GPT-4.1 → GPT-5.6 Luna on Bedrock acc3 for judges (s1_judge, brand audit, Debate, T10 F8/F9) — A/B then staged switch | Duplicate | 2026-10-10 | — |
| [AA-646](no-project/AA-646.md) | [P0][BUG] DFS research runs platform-wide after every tenant rewrite — scope it and make it admin-triggered | Done | 2026-09-28 | — |
| [AA-647](no-project/AA-647.md) | [P0][BUG] DFS failures poison the search_demand cache (NULL stored as fresh, places marked researched for 182 days) + repair 25/09 data | Done | 2026-09-28 | — |
| [AA-648](no-project/AA-648.md) | [P0] DFS batching is ineffective (~4.5 keywords per paid task) — two-phase research with real bulk tasks + Standard queue mode | Done | 2026-09-28 | — |
| [AA-649](no-project/AA-649.md) | [P0] Cost guard — DB-configured budgets for DFS / LLM / Jev per run and per day, hard stop, pre-run estimate | Done | 2026-09-28 | — |
| [AA-65](no-project/AA-65.md) | T-05: AWS DB Setup — DEV RDS 19-table schema migration | Canceled | 2026-08-21 | — |
| [AA-657](no-project/AA-657.md) | [INFRA] acc3 invoker IAM — allow Sonnet 5, Opus 5.5, GPT-5.6 Luna, GPT-6 Astra (inference profiles + foundation ARNs) | Done | 2026-09-28 | — |
| [AA-658](no-project/AA-658.md) | [Gateway P0] Bedrock Converse provider + model catalog table (single source for admin dropdowns and pricing) | Done | 2026-09-28 | — |
| [AA-659](no-project/AA-659.md) | [Gateway P1] Stage routing for every call site + acc3-first fallback chain + shadow model | Done | 2026-09-28 | — |
| [AA-66](no-project/AA-66.md) | T-06: Admin Portal scaffold — Laravel 12 + OTP auth + 8 CRUD modules | Canceled | 2026-08-21 | — |
| [AA-660](no-project/AA-660.md) | [Gateway P2] Jev `decide()` seam + shared.decision_log + cost logging (shadow mode first) | Done | 2026-09-29 | — |
| [AA-661](no-project/AA-661.md) | [RESEARCH] Jev confidence thresholds — when may Jev block content? Calibration study + 3-zone policy | Done | 2026-09-29 | — |
| [AA-67](no-project/AA-67.md) | T-09: CIS→AAA sync job (6h) + Mobile API contract (Sanctum) | Canceled | 2026-08-21 | — |
| [AA-68](no-project/AA-68.md) | T-10: Trip Case lifecycle — versioning, HITL approval, wishlist-to-trip | Canceled | 2026-08-21 | — |
| [AA-685](no-project/AA-685.md) | [Gateway P1b] Move the 5 unlogged model call sites + TripPlanner behind the gateway (cost log for every call) | Done | 2026-09-28 | — |
| [AA-686](no-project/AA-686.md) | [Gateway P1c] Admin UI — edit stage routes (fallback chain, shadow model + sample %), catalog view, shadow A/B report | Done | 2026-10-09 | — |
| [AA-69](no-project/AA-69.md) | T-12: Payments & invoices — Stripe/Xendit integration | Canceled | 2026-08-21 | — |
| [AA-7](no-project/AA-7.md) | Legacy image migration → S3 + CloudFront CDN | Canceled | 2026-08-21 | — |
| [AA-70](no-project/AA-70.md) | T-14: Flutter app integration + full UAT (Ms. Thu sign-off) | Canceled | 2026-08-21 | — |
| [AA-715](no-project/AA-715.md) | [OPS] GitHub Actions "Ops" workflow — AWS status/logs/read queries/migrations/scripts from cloud Claude sessions | Canceled | 2026-10-03 | — |
| [AA-73](no-project/AA-73.md) | Setup ADR tracking: viết 7 ADR backfill từ các quyết định đã đưa ra | Canceled | 2026-08-21 | — |
| [AA-75](no-project/AA-75.md) | Cert: DVA-C02 prep — Q3 2026 (aligned P4-S5/S6 + ACP) | Canceled | 2026-08-21 | — |
| [AA-86](no-project/AA-86.md) | [ACP-v1.2] Audit S1 quality scoring — why 10.0 score but tenant rejects tours | Done | 2026-05-19 | — |
| [AA-87](no-project/AA-87.md) | [ACP-v1.2] Fix S1 brand injection — system_prompt not applied to LLM rewrite call | Done | 2026-05-19 | — |
| [AA-88](no-project/AA-88.md) | [ACP-v1.2] Competitor URL management — table + UI for B2B tenant self-input | Done | 2026-05-19 | — |
| [AA-89](no-project/AA-89.md) | [ACP-v1.2] B2B self-approval dashboard — S2/S3/S4 tenant-side review flow | Done | 2026-05-21 | — |
| [AA-90](no-project/AA-90.md) | [ACP-S1] Configured Rewrite Engine — Multi-select + run_config + Tour Content Versioning | Done | 2026-05-20 | — |
| [AA-92](no-project/AA-92.md) | [AA-ACP-App] Brand & Design Alignment — Adventure Asia design system | Done | 2026-05-21 | — |
| [AA-93](no-project/AA-93.md) | [ACP-S4.2] Social Media Content Engine — Dual-mode, 8 channels, 11 formulas, Bedrock configurable | Done | 2026-05-21 | — |
| [AA-94](no-project/AA-94.md) | [Learning] DVA Gap: DynamoDB fundamentals — exam prep | Canceled | 2026-08-21 | — |
| [AA-95](no-project/AA-95.md) | [Learning] AIOps Gap: Vector databases — pgvector + Bedrock embeddings | Canceled | 2026-08-21 | — |
| [AA-96](no-project/AA-96.md) | [Learning] DOP Gap: Prometheus + Grafana — open-source observability | Canceled | 2026-08-21 | — |
| [AA-928](partner-crm-aa-partner/AA-928.md) | [CRM W0] CRM-01a ADRs + contracts + spec errata | Done | 2026-10-22 | Partner CRM — AA-Partner |
| [AA-929](partner-crm-aa-partner/AA-929.md) | [CRM W0] CRM-01b Data-standards bump | Done | 2026-10-22 | Partner CRM — AA-Partner |
| [AA-930](partner-crm-aa-partner/AA-930.md) | [CRM W0] CRM-02 Readiness checks (read-only) | Done | 2026-10-22 | Partner CRM — AA-Partner |
| [AA-931](partner-crm-aa-partner/AA-931.md) | [CRM W0] CRM-03 Infra bootstrap + CloudFront VPC-origin spike | Done | 2026-10-22 | Partner CRM — AA-Partner |
| [AA-932](partner-crm-aa-partner/AA-932.md) | [CRM W1] CRM-04 Infra + DB owner `crm` | Done | 2026-10-23 | Partner CRM — AA-Partner |
| [AA-933](partner-crm-aa-partner/AA-933.md) | [CRM W1] CRM-05 AA-Partner repo, API, job runner | Done | 2026-10-23 | Partner CRM — AA-Partner |
| [AA-934](partner-crm-aa-partner/AA-934.md) | [CRM W1] CRM-06 KeyProvider and field encryption | Done | 2026-10-23 | Partner CRM — AA-Partner |
| [AA-935](partner-crm-aa-partner/AA-935.md) | [CRM W1] CRM-07 Web skeleton + synthetic agencies | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-936](partner-crm-aa-partner/AA-936.md) | [CRM W1] CRM-08 Slice 1: intake → Inquiry → board | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-937](partner-crm-aa-partner/AA-937.md) | [CRM W2] CRM-09 F1/F2 complete | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-938](partner-crm-aa-partner/AA-938.md) | [CRM W2] CRM-10 F3 scrubber | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-939](partner-crm-aa-partner/AA-939.md) | [CRM W2] CRM-11 F4 roles, partner pool, MFA, permission matrix | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-940](partner-crm-aa-partner/AA-940.md) | [CRM W2] CRM-12 F5 audit | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-941](partner-crm-aa-partner/AA-941.md) | [CRM W2] CRM-13a AA admin L1 console | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-942](partner-crm-aa-partner/AA-942.md) | [CRM W2] CRM-14 Data lifecycle rules | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-943](partner-crm-aa-partner/AA-943.md) | [CRM W3] CRM-15 Modules 1 + 2 complete | Done | 2026-10-25 | Partner CRM — AA-Partner |
| [AA-944](partner-crm-aa-partner/AA-944.md) | [CRM W3] CRM-16 Agency-line ledger + suppliers | Done | 2026-10-25 | Partner CRM — AA-Partner |
| [AA-946](partner-crm-aa-partner/AA-946.md) | [CRM W3] CRM-18 Thin full lifecycle | Done | 2026-10-25 | Partner CRM — AA-Partner |
| [AA-947](partner-crm-aa-partner/AA-947.md) | [CRM W4] CRM-19 B2B client + AA lines | Done | 2026-10-25 | Partner CRM — AA-Partner |
| [AA-949](partner-crm-aa-partner/AA-949.md) | [CRM W4] CRM-21a Proposal model + day-list builder | Done | 2026-10-26 | Partner CRM — AA-Partner |
| [AA-950](partner-crm-aa-partner/AA-950.md) | [CRM W4] CRM-21b Client proposal + accept + hold | Done | 2026-10-26 | Partner CRM — AA-Partner |
| [AA-951](partner-crm-aa-partner/AA-951.md) | [CRM W4] CRM-22 Module 4 + "Before you go" | Done | 2026-10-27 | Partner CRM — AA-Partner |
| [AA-972](partner-crm-aa-partner/AA-972.md) | [CRM LB] CRM-B1 M2M + B2B quote | Done | 2026-10-23 | Partner CRM — AA-Partner |
| [AA-973](partner-crm-aa-partner/AA-973.md) | [CRM LB] CRM-B2 Departures, capacity, holds | Done | 2026-10-23 | Partner CRM — AA-Partner |
| [AA-974](partner-crm-aa-partner/AA-974.md) | [CRM LB] CRM-B2b Booking commercial rules (new, Fix C2, A3, A8) | Done | 2026-10-23 | Partner CRM — AA-Partner |
| [AA-975](partner-crm-aa-partner/AA-975.md) | [CRM LB] CRM-B3 Event feed + on-request desk + incident flag | Done | 2026-10-23 | Partner CRM — AA-Partner |
| [AA-976](partner-crm-aa-partner/AA-976.md) | [CRM LB] CRM-B4 CIS catalog over HTTP | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-977](partner-crm-aa-partner/AA-977.md) | [CRM LB] CRM-B5 AA-authored content in CIS (new, Fix C1) | Done | 2026-10-25 | Partner CRM — AA-Partner |
| [AA-978](partner-crm-aa-partner/AA-978.md) | [CRM LP] CRM-P1 Membership feed + tenant API | Done | 2026-10-24 | Partner CRM — AA-Partner |
| [AA-979](partner-crm-aa-partner/AA-979.md) | [CRM LP] CRM-P2 Move `portal/` into AA-Partner | Done | 2026-10-29 | Partner CRM — AA-Partner |
| [AA-589](tripplanner-aa-booking/AA-589.md) | [EPIC] TripPlanner — Ms.Thư tasks (data cleanup, upload raw, auto-edit, arrival/departure map, suggest next) | Done | 2026-09-16 | TripPlanner & AA-Booking |
| [AA-590](tripplanner-aa-booking/AA-590.md) | [#5][MAP] Suggest next place theo itinerary — kết hợp taste-similarity + geography | Done | 2026-09-16 | TripPlanner & AA-Booking |
| [AA-591](tripplanner-aa-booking/AA-591.md) | [#4][MAP] Arrival/departure trên bản đồ — vẽ gateway airport + flight arc fly-in/fly-out | Done | 2026-09-16 | TripPlanner & AA-Booking |
| [AA-592](tripplanner-aa-booking/AA-592.md) | [UI] Hover tên nước trong picker → highlight polygon nước trên map (preview) | Done | 2026-09-16 | TripPlanner & AA-Booking |
| [AA-593](tripplanner-aa-booking/AA-593.md) | [UI] Xác nhận ActivityIcon đủ 8 activity (nợ 'icon 6+2') | Done | 2026-09-16 | TripPlanner & AA-Booking |
| [AA-673](tripplanner-aa-booking/AA-673.md) | [TripPlanner] Tour Graph read model — destinations, within-tour day adjacency, cross-tour junctions (from CIS published tours) | Done | 2026-09-29 | TripPlanner & AA-Booking |
| [AA-674](tripplanner-aa-booking/AA-674.md) | [TripPlanner] Multi-tour trip composition + route-constrained "suggest next" + filters (country, activity, intensity, duration) | Done | 2026-09-29 | TripPlanner & AA-Booking |
| [AA-675](tripplanner-aa-booking/AA-675.md) | [TripPlanner] Re-extraction job — rebuild itinerary_components + Tour Graph after each CIS rerun wave (Jev classification in shadow) | Canceled | 2026-10-19 | TripPlanner & AA-Booking |
| [AA-676](tripplanner-aa-booking/AA-676.md) | [TripPlanner → AA-Booking] Hand-off: submitted trip draft becomes a Trip Case (New Inquiry) with V1 pre-filled from the leg chain | Done | 2026-10-11 | TripPlanner & AA-Booking |
| [AA-678](tripplanner-aa-booking/AA-678.md) | [AAA] Architecture + repo bootstrap on acc2 — AA-Booking repo (FastAPI + Next.js), ECS service, CI/OIDC, Terraform in AA-CIS-Infra | Done | 2026-10-16 | TripPlanner & AA-Booking |
| [AA-679](tripplanner-aa-booking/AA-679.md) | [AAA] Catalog read in Booking: sellable trip plans over the live CIS catalog (catalog.v_tour) + "Use for trip case" | Done | 2026-10-16 | TripPlanner & AA-Booking |
| [AA-680](tripplanner-aa-booking/AA-680.md) | [AAA] Identity — customer OTP auth (shared with TripPlanner) + staff RBAC (admin / sales / content_creator) | Done | 2026-10-20 | TripPlanner & AA-Booking |
| [AA-681](tripplanner-aa-booking/AA-681.md) | [AAA] Trip Case workflow MVP — inquiry → versions (V1..Vn) → approved → confirmed order; staff assignment; customer "My Trips" | Done | 2026-10-16 | TripPlanner & AA-Booking |
| [AA-682](tripplanner-aa-booking/AA-682.md) | [AAA] Operations MVP — supplier bookings, trip checks, invoices + payment schedule, supplier bills | Done | 2026-10-28 | TripPlanner & AA-Booking |
| [AA-683](tripplanner-aa-booking/AA-683.md) | [AAA] Figma review → UI spec aligned with the ecosystem design system (staff admin + customer app) | Done | 2026-10-16 | TripPlanner & AA-Booking |
| [AA-689](tripplanner-aa-booking/AA-689.md) | [EPIC] TripPlanner — Trip.com-style planner on AA data (Jira PR-11) | Canceled | 2026-10-19 | TripPlanner & AA-Booking |
| [AA-708](tripplanner-aa-booking/AA-708.md) | [Photos] Sync AA marketing photos from Google Drive (Jira CON PHOTOS) to S3 and match them to places/tours | Done | 2026-10-16 | TripPlanner & AA-Booking |
| [AA-709](tripplanner-aa-booking/AA-709.md) | [AAA] Research: load supplier price and AA selling price for raw tours | Done | 2026-10-15 | TripPlanner & AA-Booking |
| [AA-731](tripplanner-aa-booking/AA-731.md) | [TripPlanner] Harness fixes before real customers — idempotent Send-to-advisor, read v_active_tour_atoms, rerun after waves, renarrate grounding | Done | 2026-10-11 | TripPlanner & AA-Booking |
| [AA-805](tripplanner-aa-booking/AA-805.md) | [TripPlanner] AI Phase 0 — narration spend caps + cache + session ownership + "AI-assisted" label; search fixes; contract version 1.1 | Done | 2026-10-20 | TripPlanner & AA-Booking |
| [AA-810](tripplanner-aa-booking/AA-810.md) | [AAA] Minimal pricing engine (ADR 0005 first cut) — pricing_rules, dated fx_rates, manual net per version item, deterministic sell-price engine | Done | 2026-10-15 | TripPlanner & AA-Booking |
| [AA-812](tripplanner-aa-booking/AA-812.md) | [TripPlanner] Tour detail pages + destination pages (SSR, SEO) — trip.com-style PDP with itinerary, inclusions, photos, "from" price and "Customise with an advisor" | Done | 2026-10-15 | TripPlanner & AA-Booking |
| [AA-818](tripplanner-aa-booking/AA-818.md) | [Infra] Custom domains for TripPlanner and AA-Booking on lumiguides.it.com — frontends + APIs off vercel.app / execute-api | Done | 2026-10-16 | TripPlanner & AA-Booking |
| [AA-822](tripplanner-aa-booking/AA-822.md) | [AAA] Wave 2a — suppliers + supplier contracts (bk-008): API + staff admin /suppliers list, form, detail | Done | 2026-10-16 | TripPlanner & AA-Booking |
| [AA-823](tripplanner-aa-booking/AA-823.md) | [AAA] Wave 2b — hotels + services supply records per ADR 0004a (bk-010): API + staff admin /hotels and /services | Done | 2026-10-16 | TripPlanner & AA-Booking |
| [AA-830](tripplanner-aa-booking/AA-830.md) | [TripPlanner → AA-Booking] Tour key fix (X3): inquiry.submitted v1.2 with source_system + source_id per leg, trip_case_legs key columns, backfill, contracts registry | Done | 2026-10-15 | TripPlanner & AA-Booking |
| [AA-835](tripplanner-aa-booking/AA-835.md) | [AAA/CIS] ADR 0004a supply content — supply.hotel.v1 / supply.service.v1 contracts, Booking supply outbox + v_supply_* views, CIS content consumer with review, read-back view to Booking, entity_media usage rights | Done | 2026-10-25 | TripPlanner & AA-Booking |
| [AA-837](tripplanner-aa-booking/AA-837.md) | [TripPlanner] /plan UI leftovers: 7 WCAG AA contrast violations, Customise 404 logged as console error, "1 DAYS" label | Done | 2026-10-23 | TripPlanner & AA-Booking |
| [AA-844](tripplanner-aa-booking/AA-844.md) | [Photos] CloudFront in front of S3 photos/ + daily scheduled photo_sync (PR-11 promise) | Done | 2026-10-21 | TripPlanner & AA-Booking |
| [AA-856](tripplanner-aa-booking/AA-856.md) | [TripPlanner] Search fails under load: Cohere Embed V4 quota is 20 requests/min on acc2 — cache query embeddings, keyword fallback, raise the quota | Done | 2026-10-16 | TripPlanner & AA-Booking |
| [AA-886](tripplanner-aa-booking/AA-886.md) | [Legal] /privacy and /terms pages + legal readiness proposal packet for Ms. Thư | Done | 2026-10-22 | TripPlanner & AA-Booking |
| [AA-904](tripplanner-aa-booking/AA-904.md) | [TripPlanner] Planned Next.js 14 → 15 upgrade (replaces Dependabot PR #104) | Done | 2026-10-19 | TripPlanner & AA-Booking |
| [AA-906](tripplanner-aa-booking/AA-906.md) | [TripPlanner] Next.js 15 → 16 upgrade (match CIS/Booking; React Compiler lint refactor) | Done | 2026-10-23 | TripPlanner & AA-Booking |
| [AA-908](tripplanner-aa-booking/AA-908.md) | [Identity] Traveller sign-in on Cognito EXTERNAL, TripPlanner guest linking and My Trips (customer half split from AA-680) | Done | 2026-10-25 | TripPlanner & AA-Booking |
| [AA-909](tripplanner-aa-booking/AA-909.md) | [TripPlanner] Check the guest token on the read GETs (trip, suggestions, coverage, activities) | Done | 2026-10-22 | TripPlanner & AA-Booking |
| [AA-910](tripplanner-aa-booking/AA-910.md) | [Booking] Staff admin at 1440 px (table overflow, FX column wrap, 1 px scrollbar) + audit rows for room type / rate and superseded V1 | Done | 2026-10-24 | TripPlanner & AA-Booking |
| [AA-987](tripplanner-aa-booking/AA-987.md) | TripPlanner drops a retired tour at once: CIS lifecycle event triggers a TripPlanner cache purge | Done | 2026-10-24 | TripPlanner & AA-Booking |
| [AA-995](tripplanner-aa-booking/AA-995.md) | [TripPlanner] Polished customer-facing design with motion, in the adventure.asia brand | Done | 2026-10-29 | TripPlanner & AA-Booking |
| [AA-996](tripplanner-aa-booking/AA-996.md) | [AAA] Booking covers every Figma screen: CIS content read-only with Edit in CIS, soft-delete dialogs, Sign-in & security, Destinations/Countries | Done | 2026-10-28 | TripPlanner & AA-Booking |
