# S203 — Jev decision layer + thiết kế A/T v2 (29–30/09/2026)

**Tác nhân:** Claude Code (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:388` · **Migration mới nhất:** CIS 185

## Trạng thái
- Nghiệp chốt hướng: **thiết kế lại A/T (kèm Jev chặn thật) + hoàn thiện UI v2 trước, rồi chạy lại MỘT lần** toàn platform + tenant test. Jev được **enforce** (không chỉ shadow); tự gán nhãn và hiệu chỉnh, không chờ chị Thư.
- Seam Jev (`decide()`) chạy thật trên Dev. **1 câu enforce** (`a3_keyword_belongs`, ≤ 0.30). **6 câu shadow**: a3_idea_traveller, a0_row_kind, a0_itinerary_usable, a0_country, a3_question_foreign, a3_question_about_here.
- Jira **PR-13** (gán chị Thư) + Google Sheet review; thư mục Drive **AdventureAsia** cho file Excel.

## Thay đổi Codebase (AA-CIS-App, tất cả đã merge)
| PR | Nội dung |
|---|---|
| #478 | AA-648: seed ý tưởng DFS = "địa điểm + quốc gia" (trước đó seed là keyword 0-volume → DFS trả lại seed, 0 ý tưởng) |
| #479 | AA-631: Debate chấm **chủ đề** từ bằng chứng thô (`score_candidate_fit`), không dùng judge bài viết (trước đó mọi ứng viên ≤ 6.0 do trục mission) |
| #480 | AA-663: IA admin — Overview/Content/Intelligence/Tenants/Operations/Settings, Brand Identity vào Settings, xoá `(internal)` + redirect, bỏ tag ADMIN |
| #481 | AA-648: bỏ task ý tưởng khi < 5 seed |
| #482 | Tài liệu thiết kế `docs/architecture/at-series-v2-design.md` |
| #483 | AA-641: flag_fix hoàn trả trường bị thêm từ cấm + T3 cắt seo_meta bằng code; fix từ cấm rỗng của tenant |
| #484 | AA-660: seam `decide()` + migration 181 (decision_question/decision_log/allow-list/catalog jev-latest) |
| #485, #491, #492 | Trang **Jev Decisions** (Overview/Questions/Verdicts/Guide, lọc, sắp xếp, header dính, màu đậm, thống kê); Jev trong Settings + External Spend |
| #486 | AA-693: cổng Jev keyword + lọc ý tưởng (migration 182) |
| #487 | Fix deadlock pool khi gọi `decide()` song song (phát hiện live) |
| #488 | Hồ sơ hiệu chỉnh `docs/calibration/a3_keyword_belongs.md` |
| #490 | AA-690: cổng Jev A0 ingest (migration 183) |
| #493 | Glossary Jev trong `CONTEXT.md` + **ADR 0007** (Verdict được tác động khi enforce + chắc + đã hiệu chỉnh) + quyết định Q1–Q8 |
| #494 | Cache Verdict theo hash câu chữ (migration 184); UI "Answers" → "Verdicts" |
| #495 | AA-694: cổng phạm vi quốc gia cho câu hỏi PAA (migration 185, shadow) |
| #489 | Đóng (bị #491 thay) |

Root repo: PR #13 (log S202) đã merge.

## Thay đổi Hạ tầng / dữ liệu
- Secret **`aa-cis/dev/typesafe`** (acc2) — key Jev.
- Migration 181–185 apply tay trên Dev trước deploy.
- `a3_keyword_belongs` → **enforce** (reject ≤ 0.30, accept ≥ 0.95, threshold v1).
- Xoá 2 dòng cache Debate 1.0 cũ (Nghiệp duyệt câu lệnh).
- Google Drive: thư mục AdventureAsia (`1YGzKGICxNNjqQVpZ_AXxuhIaDiq0w2NB`), 2 Google Sheet.

## Bằng chứng verify
- Smoke Jev: mongar bhutan 0.96 / paro festival 0.89 / peninsula 0.12 / hot springs 0.05, ~150 ms/lời gọi.
- Hiệu chỉnh keyword: 200 cặp, 55/55 đúng ở ≤ 0.30; Nghiệp kiểm 69 dòng, sửa 2 (2,9%).
- Research thật có cổng Jev: job `ef066ad9` (10 địa điểm Bhutan, $0.19), 25 keyword được kiểm, không lỗi/treo.
- A0: 100 tour thật → 99 là tour (≥ 0.9). Đọc lại 10 file gốc: mọi dòng POI đều itinerary rỗng → luật có sẵn đã bắt; A0 giữ shadow.
- Phạm vi quốc gia: 600 cặp thật ($0.012): **~64% câu hỏi PAA đang tính cho Segment là câu về nước khác/chung chung** (lọc sơ bộ chỉ cần chung 1 từ). Luật đề xuất foreign ≥ 0.95 hoặc here ≤ 0.20: loại 133/150 câu xấu, sai 1 (99,2%) trên 200 mẫu tự gán.
- Luật transit cho landing đã có sẵn (856/3.362 Segment bị loại); còn 192 atom Haiku gắn transit mà luật bỏ sót (6% câu hỏi) → câu `a3_activity_type` sau.
- Playwright prod: nav admin 1440/400px, Jev Decisions v2 đều pass.
- Unit suite: 2138 pass; 3 lỗi cũ (aa324 ×2, aa652) cũng lỗi trên main.
- Tổng chi phí Jev cả phiên ≈ **$0.02**; DFS ≈ $0.48.

## Còn lại
1. **Nghiệp kiểm 57 dòng** hiệu chỉnh phạm vi quốc gia (Google Sheet "Jev calibration — question country scope"). < 10% sai → ghi hồ sơ + enforce 2 câu (có thể chờ chị Thư trả lời câu 2, 3 ở PR-13).
2. Chờ chị Thư điền Google Sheet PR-13 (12 quyết định, 38 câu hỏi Jev, 6 câu hỏi).
3. Bước 4: **kiểm chống bịa master content A1** (số liệu bằng code + Jev từng câu → flag_fix). Bắt buộc trước lần chạy lại.
4. Bước 5: câu hỏi landing (shadow + hiệu chỉnh cặp cùng loại). Sau đó UI v2 (AA-662→) → chạy lại (AA-653/594).
5. AA-641: verify live 3 lần Manaslu (≤ 1.3 lần viết) — làm trong smoke trước lần chạy lại.
6. Kiểm keyword bị loại sau 2 lượt research enforce đầu tiên (hạ ngưỡng về 0.15 nếu thấy loại nhầm).
7. DPA với TypeSafe: ai liên hệ (hỏi trong PR-13).

## Lưu ý kỹ thuật
- `decide()` không bao giờ raise; chỉ tác động khi enforce + accept/reject. Thứ tự: migration câu hỏi trước deploy.
- Không giữ connection qua lời gọi HTTP và không acquire 2 lần lồng nhau (đã từng deadlock).
- Cache Verdict theo (câu hỏi, hash câu chữ, subject, tenant) 180 ngày; đổi câu chữ = hiệu chỉnh lại.
- Không gộp nhiều chủ thể / 1 lần gọi (làm lệch câu đã hiệu chỉnh; lợi ích vài cent).
- Tải file lên Drive: dùng CSV textContent; base64 xlsx chép tay dễ hỏng.
- `docs/` trong App bị gitignore → `git add -f`.
- Auto mode classifier hay lỗi tạm thời; thử lại 1 lần rồi dừng báo cáo.
