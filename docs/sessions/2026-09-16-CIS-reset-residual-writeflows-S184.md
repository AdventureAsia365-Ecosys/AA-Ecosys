# Session Log — S184 (AA-Ecosys dev)

- **Ngày:** 2026-09-16
- **Agent:** Kiro
- **Chủ đề:** Tiếp S183 — reset residual DB + cost=0, fix bug S0/S1 tours-ready, dịch i18n admin, điều tra sâu 2 luồng viết → epic redesign. G4 hoãn.
- **Trạng thái:** 5/6 việc phiên xong. G4+ hoãn có chủ đích.

## 1. Trạng thái
Đầu phiên đọc memory S183 + log + Linear, tiếp chuỗi CIS reset (AA-594). Nghiệp chốt góc "reset từ đầu": giữ SỐ THẬT (793 raw = 788 active + 5 superseded Sri Lanka), reset COST về 0. Cuối phiên: DB reset residual + cost=0 xong; 2 PR (#387/#388) auto-merge; 4 issue mới + 1 epic; AA-495 cancelled.

## 2. Thay đổi CODEBASE (apps/AA-CIS-App)
### PR #387 — AA-604 (branch pqnghiep1354/aa-604-s0-tours-ready-itinerary-floor)
- admin_pipeline.py: S0 get_tours_ready thêm itinerary floor (deleted_at IS NULL + src_itineraries non-empty) khớp S1; dry_run preview thêm block empty_itinerary.
- services/ingestion/handler.py: process_file skip empty-itinerary khỏi new_records, ghi ingest_details.
- frontend/app/admin/upload/page.tsx: badge đỏ "No Itinerary".
- tests test_aa488/490/343: thêm src_itineraries vào fixtures (CI Unit Tests fail lần 1 do empty-itinerary skip làm rớt fixtures dedup). 11 test pass local.
### PR #388 — i18n (branch pqnghiep1354/s184-admin-i18n-vi-to-en)
- llm-usage/page.tsx (12) + settings/page.tsx (12): dịch tiếng Việt UI → Anh. All checks pass.

## 3. Thay đổi DB (acc2 aa_cis_dev, qua bastion tunnel — verified transaction)
- Reset residual: DELETE llm_call_log(741), tenant_api_usage(18241), notifications(39), acp_shared.audit_log(127), prompt_eval_runs(3), acp_contract.atom_decompose_jobs(87), pipeline_jobs(46), + 1 orphan pipeline_run (giữ 37 = provenance upload; raw_tours.batch_id NOT NULL FK trỏ pipeline_runs nên KHÔNG xóa hết được — phương án B). GIỮ config: llm_role_config/admin_users/schema_versions/membership_plans.
- Cost=0: UPDATE pipeline_runs SET cost_usd=0 (37 rows, $3.9998→$0). View v_tenant_monthly_usage tự recompute 0.
- Trash 30 tour empty-itinerary: source_status=trashed, deleted_at=now (Japan 23 POI, India 4, Laos/Nepal/Thailand 3). raw_tours not-deleted=763, S1-ready=763.
- Bastion i-006e9b5bc05c6861f VẪN CHẠY (~$0.25/ngày) — terminate AA-602 khi xong audit. RDS snapshot G0 giữ.

## 4. Verify
- Reset residual: COMMIT, post-verify 6 bảng+pipeline_jobs=0, pipeline_runs=37, raw_tours=793.
- Cost: BEFORE $3.9998 → UPDATE 37 → AFTER $0.0000, guard raw=793.
- Trash: BEFORE 30 → not-deleted=763, s1-ready=763.
- Code: py_compile OK, tsc exit 0, pytest 3 file (11 test) pass local.

## 5. Linear
- AA-604 (In Progress): S0/S1 fix + trash 30 tour. PR #387.
- AA-605 (Backlog): UIUX đồng bộ adventure.asia (design pass).
- AA-606 (Backlog, sub AA-607): Bedrock Batch S1 — xin IAM Batch acc3 + re-architect submit/poll.
- AA-607 (Backlog, EPIC): redesign 2 luồng viết admin+tenant.
- AA-495: CANCELED (trùng AA-594).
- PR #388 (i18n): all checks pass.

## 6. Điều tra 2 luồng viết (bằng chứng code → AA-607)
### Luồng 1 — S1 (generate→validate→judge→[retry≤3/hitl]→brand_audit→flag_fix→revalidate)
- Writer=haiku/acc3 (generate/flag_fix/nudge). Judge=gpt-4.1 OpenAI API NGOÀI (chủ đích khác vendor, không phải Bedrock thiếu GPT).
- Gate _is_publishable: score≥7 AND audit≠manual_check AND không(flagged chưa fix). quality_score=min(validate,judge). MAX_RETRIES=3→review_queue.
- A1 admin: judge brand-fit client-cụ-thể SKIP (brand row default trống brand-diff). NHƯNG brand_audit AA generic (AA_BRAND_IDENTITY_PROMPT) VẪN chạy đầy đủ — rubric CHẶT (~40 forbidden words, rule từng field, manual_check cứng cho elephant/fabricated). Đây là cái Nghiệp muốn NỚI (dễ fail review queue khi rerun 700 tour).
- T2 tenant = BUG: fetch brand tenant KHÔNG lấy core_idea/customer_mindset/voice_examples → judge skip cả cho tenant thật (đáng lẽ phải chấm).
- atom_writer (viết tour TỪ atom): ĐÃ BỎ — route /v1/s1-from-atom mount nhưng 0 caller (chỉ eval). Gỡ hẳn.
- Curation VÔ NGHĨA: chỉ deleted ảnh hưởng segment; star no-op; mọi atom không xóa đều vào segment.
- DFS cache key seo:<seed>:<location_code>, seed chứa country → nước khác không collision.
### Tenant T2 dùng chung build_graph; T7-T11 social = stack riêng (acp_angle_gate+acp_content_writing+acp_produce), AA không gate content tenant.

## 7. CÒN LẠI — việc đầu phiên sau (S185)
1. Chốt thiết kế AA-607 từng sub với Nghiệp: rubric A1 (NỚI brand_audit, xem #9) vs T2, haiku↔sonnet, judge model, curation (bỏ star/làm thật), gỡ s1-from-atom, tenant sync → rồi build.
2. AA-606 Bedrock Batch: xin IAM Batch acc3 (Terraform AA-CIS-Infra) + S3 in/out + re-architect. Xác nhận quota min-records.
3. AA-604: kiểm PR #387 merge chưa (đã fix test, chờ CI xanh).
4. G4 (AA-599): rerun S1 CHỈ SAU khi AA-607 chốt + AA-606 sẵn.
5. Bastion: terminate (AA-602) nếu nghỉ lâu; giữ nếu làm AA-606/G4 sớm.

## 8. Lưu ý kỹ thuật (Kiro/WSL — QUAN TRỌNG)
- Terminal interactive-zsh: nhiễu hiển thị (double-char) + LUÔN exit -1 GIẢ nhưng lệnh CÓ chạy. Lệnh 1 dòng ngắn; psql -c/-f ghi ra .txt; read_file path WORKSPACE-RELATIVE (absolute bị double //wsl.../home/.../home/...).
- fs_write file MỚI shell KHÔNG thấy (layer khác) — LÀM LOG/SCRIPT CẦN SHELL ĐỌC PHẢI dùng shell printf/redirect. (Lỗi phiên này: log S184 tạo bằng fs_write ban đầu KHÔNG vào docs/sessions thật — phải viết lại bằng shell printf.)
- SSM tunnel port 15432 (local pg16 chiếm 5432), idle ~20 phút.
- pytest: .venv/bin/python -m pytest (shebang venv stale) + env JWT_SECRET/DATABASE_URL/OPENAI_API_KEY.
- CI AA-CIS-App 5 job, merge gh pr merge --auto --squash; CHẠY pytest local trước khi push.

## 9. Phát hiện quan trọng
1. Số UI "sai" (788/763/20/$4) là DỮ LIỆU THẬT đọc cột chưa reset (source_status/src_itineraries/cost_usd), không phải cache. Xử đúng bản chất: giữ số thật, zero cost.
2. pipeline_runs KHÔNG phải residual thuần — raw_tours.batch_id NOT NULL FK trỏ vào (34/38 là provenance upload). Chỉ xóa 1 orphan.
3. 30 tour S0-ready nhưng S1=763: parser không phân biệt tour/POI + không validate itinerary. Fix ở boundary.
4. A1 lo ngại review-queue: judge brand-fit ĐÃ skip nhưng brand_audit AA generic vẫn CHẶT → Nghiệp muốn nới. 3 hướng ghi ở AA-607: (H1) tách rubric A1 nhẹ chỉ structural/grounding; (H2) đổi manual_check→flagged cho lỗi brand-voice, chỉ chặn product-truth; (H3) đo batch nhỏ 20-50 tour trước rồi mới quyết. Đề xuất H3 trước rồi H1/H2.
5. AA-495 = trùng AA-594 → cancel.
