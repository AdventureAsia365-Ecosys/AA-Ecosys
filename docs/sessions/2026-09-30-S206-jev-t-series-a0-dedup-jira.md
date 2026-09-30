# S206 — Jev T-series (shadow), A0 trùng gần giống + map cột, brand tenant test, research enforce đầu tiên, báo cáo Jira PR-13 (30/09/2026)

**Tác nhân:** Claude Code (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:407` đang rollout (PR #519), `:406` COMPLETED · **Migration mới nhất:** CIS 194

## Trạng thái
- **Jev: 23 câu hỏi** trên Dev — 13 enforce (A0/A1/A3) + 10 shadow (A1-4 + T-series). 38.658 verdict, $0.30 tổng.
- **T-series (AA-696)** tách 3 sub-issue AA-699/700/701 (Nghiệp duyệt). Nghiệp chốt: **shadow trước, hiệu chỉnh từ lần chạy lại** (tenant test chỉ có 5 rewrite / 3 piece).
- Issue: AA-696/699/700/701 In Progress (chờ dữ liệu lần chạy lại), AA-690 In Progress, **AA-693 Done**, AA-695/694/692 In Progress.
- Nghiệp chốt thứ tự: **audit UI admin → xoá dữ liệu dẫn xuất (chỉ giữ raw_tours) + chạy lại platform → hiệu chỉnh Jev từ dữ liệu mới → T-series (kiểm luồng, sửa UI, chạy test)**. UI v2 để phiên riêng.

## Thay đổi Codebase
**AA-CIS-App:**
| PR | Nội dung |
|---|---|
| #512 | **AA-699** T3: câu bị regex số bắn hỏi `a1_claim_supported` (dùng lại hiệu chỉnh A1, enforce accept 0.90) trước khi viết lại; T2 tie-break judge `a1_brand_fit` cho tenant (shadow). T0 hoãn |
| #513 | **AA-700** mig 193: `t7_topic_fits_brand` (Debate), `t8_angle_answers`, `t9_fact_relevant` — shadow, code sẵn cho enforce |
| #514 | **AA-701** mig 194: `observe_t10()` — 6 câu T10 (rubric F8, voice/CTA F9, same-piece ≥0.85 chỉ khi cả 2 tenant allow-list, offer_as_certain, faq_restates), chỉ ghi log |
| #515 | **AA-690 A0-2** trùng gần giống: cùng NCC + nước + tên ≥0.8 + itinerary ≥0.9 + cùng số ngày → bỏ qua khi Commit (`duplicate_of_existing`), không staging; biến thể chỉ ghi chú. Không Jev. Kèm nhãn FE Not a Tour / Thin Itinerary |
| #516 | Fix: tra brand chỉ tìm `brand_name='default'` → tenant đặt tên brand trên portal mất brand ở Debate/T9-T10/S1 batch. Nay ưu tiên default, không có thì dòng active mới nhất |
| #517 | **AA-693** lọc ý tưởng research có chữ lưu trú (hotel/resort/lodge/residency/boutique…) trước Jev, trừ "airport to hotel". Thử đổi câu Jev (v2) nhưng 91% < 95% → không dùng |
| #518 | **AA-690 A0-5** chuẩn hoá tên cột Excel (gạch dưới, đơn vị trong ngoặc) trước khi tra COLUMN_MAP |
| #519 | Excel đổi group size "2-10" thành ngày → khôi phục khoảng (tháng-ngày, nhỏ trước) |

**Root repo:** steering `session-workflow.md` thêm **"Quy tắc Jira — thời điểm báo cáo, tạo issue, liên kết Linear"** (dùng chung Kiro + Claude Code) + số phiên S206. Memory Claude `jira-report-when-done` trỏ về steering.

## Thay đổi Hạ tầng / dữ liệu (Dev)
- Migration 193, 194 apply tay trước merge.
- **WanderLux** brand = **Atlas & Hearth** (từ `docs/AI-gent-for automation works/brand identify for tenant trip content testing/Atlas.docx`), v2 active, dòng `default` rỗng tắt. Lưu ý: các file brief có dòng dạng `cis_…` giống API key.
- **Supersede 20 bản trùng** (Nghiệp duyệt; 16 cụm, giữ bản đã publish hoặc bản sớm nhất). Active 756 → 736. ID:
  `4bf83a2c-cec0-4127-ac82-1a26fbbd48a3, 255cb0f0-b3d3-45a6-a986-3c8e8623b776, de5eeb1e-2bde-4722-b25e-dba76f6242f1, 678118b4-f1c3-4f16-b460-c1c7d835b56b, 8699eb5a-c851-4dc4-b836-61720bd595d6, 2bb1567d-1476-498b-918b-52dd4c168b1b, fbc777d8-78e1-4f8e-8d8c-63c0807153f8, 9aa85d55-71b9-42bc-bf6a-3dc9deb14b3b, 2335b9a4-6c03-4c89-b41e-f174a9ea5406, 22bc526a-bea0-4e1a-b040-8f77e5701c6a, 5bbd1491-4491-47a4-94f2-ea623db87c2e, 4ad002ac-766c-40a1-b0c1-2e51e2888b02, b2344cea-19d3-4058-acbd-9191a7505931, c535be2e-ac0d-44d6-9a5b-5eba9e29b148, 673c7ceb-dc9c-4255-a44e-990b2beb43fe, 7f225a2c-ae33-4313-8b16-990a7ad2e1ab, 76b5076f-4d03-47be-a33c-1acd583e2c7c, 657f69e5-fdbe-4dee-8235-7df34dd47417, 8cd669e3-0074-4269-aa7b-58fc7703a9e3, a1dcfe8d-3db5-4065-8e48-b25ba4f49aa9`
- **Backfill raw_tours** từ 10 file gốc còn trên S3 (27 file cũ 404): **257 ô / 188 tour** (group_size 177, best_time_to_go 43, price_raw 11, subtitle/summary/inclusions 8, exclusions/duration 1). Chỉ điền ô trống. Còn 12 ô / 3 tour (dòng trùng tên trong file, chưa kiểm từng dòng).
- **Research enforce đầu tiên** (AA-693): Bhutan, US, 10 địa điểm, job `deaf3850`: DFS $0.19. Keyword bị loại 2/20 (đều đúng) → giữ 0.30. Ý tưởng: 214/300 bị loại.
- Xoá câu hỏi thử `a3_idea_traveller_v2` khỏi `decision_question` (log giữ lại).

## Bằng chứng verify
- AA-699 trên :400: tenant allow-list ghi `decision_log` đúng tenant; UUID lạ → 1 dòng `skipped` rồi dừng. Câu bịa "47 bridges" p=0.01 giữ; đổi đơn vị "6,250 m (20,506 feet)" p=0.73 → grey, **vẫn bị viết lại** (chưa có ca thật được bỏ qua).
- AA-700 trên :402/:404: T8 4 verdict (p TB 0.14 — angle phần lớn không thật sự trả lời câu PAA); T9 2 fact (fact Laos cho bài Bhutan p 0.03), tenant lạ → skipped. T7 (sau brand + #516): Itaewon 0.50, Han River 0.58, K-pop 0.11; Luna chấm cả 3 là 2.0.
- AA-701: 3 piece LinkedIn thật → rubric 12, voice 3, CTA 3 verdict.
- A0-2 trên :403: 3 tour thật đổi hoa/thường → duplicate; biến thể (1/3 itinerary, 30 ngày) → chỉ ghi chú.
- Unit suite 2.224 pass; 3 lỗi cũ (aa324 ×2, aa652) như main.
- Playwright chụp trang Jev Decisions (0 lỗi console): `.tmp-session/shots/jev_1_overview.png`, `jev_2_questions.png`, `jev_3_verdicts.png`.

## Jira
- **PR-13** comment 10431 (tiếng Việt): trạng thái Jev, 23 câu theo stage (câu chữ, ngưỡng, kết quả), đối chiếu 38 dòng Sheet review. **Nghiệp tự chèn 3 ảnh.**
- Chị Thư đã trả lời trong Sheet review: "Da chot" đồng ý 9/12, #6 (DPA) và #11 (thứ tự) "Cần bàn", #3–4 trống; "Hoc tu chi Thu" xác nhận đúng + góp ý phạm vi quốc gia khi nhiều nước; "Hoi chi Thu" (6 câu) chưa trả lời.

## Còn lại
1. **Audit UI admin** (Playwright, tài khoản admin) trước khi chạy lại.
2. **Runbook + xoá dữ liệu dẫn xuất (chỉ giữ raw_tours) + chạy lại platform** (AA-653/594/599/600): trình phạm vi xoá cho Nghiệp duyệt trước; dựng lại Segment từ đầu.
3. Hiệu chỉnh từ dữ liệu lần chạy lại: `a1_brand_fit`, 10 câu T-series, phía reject của `a1_claim_supported`.
4. T-series: kiểm logic toàn luồng, sửa UI (UI v2 AA-662→), chạy test tenant.
5. Lỗ hở biết trước: tên resort thương hiệu thuần (amankora, como…) vẫn qua lọc ý tưởng; T3 đổi đơn vị chưa vượt 0.90.
6. Chờ chị Thư: 6 câu "Hoi chi Thu", 2 mục "Cần bàn".

## Lưu ý kỹ thuật
- Script chạy trong container: thêm `sys.path.insert(0, "/app")` khi import code app.
- Runner mới `.tmp-session/s206_run.sh` tự chọn task có exec agent RUNNING (an toàn khi đang deploy). EOF giữa chừng: script vẫn có thể đã chạy xong — đọc kết quả S3 hoặc truy vấn lại DB trước khi chạy lại.
- `docs/` bị gitignore ở App → notes/calibration phải `git add -f`.
- Auto mode chặn tạo script ghi DB → Nghiệp tắt auto mode để duyệt từng bước.
- Tài khoản `aa-cis/dev/e2e-test-admin` đăng nhập admin báo Invalid credentials; Playwright dùng tài khoản admin Nghiệp đưa (không lưu vào file).
- Connector Atlassian không upload được ảnh → comment chữ, Nghiệp chèn ảnh tay.
- Danh sách VSCode Jira mặc định chỉ hiện issue gán cho mình; PR-13 gán chị Thư.
- Merge PR có `[AA-xxx]` vẫn tự đóng issue → đã mở lại AA-690/695/699/700/701.
