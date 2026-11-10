# S275 — bộ đáp án CL-1 đủ và duyệt trong Writing Lab, Jev lọc trước, bật 2 công tắc W3, AA-741 phase 2, nghiên cứu app Odoo

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). 10/11/2026 ~06:30 → ~16:30 +07.
- MFA làm mới một lần, lúc 09:58, sau khi phiên cũ hết hạn; hạn mới 21:49.
- Tech lead duyệt trên điện thoại qua các trang artifact: trang quyết định, trang duyệt câu, trang Odoo.

Snapshot: `docs/audits/2026-11-10-S275-session/state-snapshot.md`.

## Danh sách đầu phiên (tech lead "Ok" 06:50)
1. Đóng AA-1056, AA-1055, AA-1058, AA-820.
2. AA-1024 D8 sau 19:00.
3. AA-1050, AA-1049, AA-1051.
4. Hội tụ AA-741, AA-1038, AA-1046, AA-1004.
5. AA-1039 (phương án A, đưa bài trở lại bằng một nút).
6. Điều tra lỗi a3_demand.

## Quyết định của tech lead
- **Trang quyết định S275 (16 câu):** 15/16 theo đề xuất. Ghi chú thêm:
  - W4: "chưa hiểu".
  - Brand: "sao không làm test luôn".
- **W4:** tính cổng 80% theo object, không theo câu. Công tắc enforce giữ OFF. Chỉ bật từng class sau khi W2 đo class đó đạt.
- **W3:**
  - Thử T2 linear 5 tour và SEO builder 3 bài; đạt thì bật cả hai.
  - `stable_keys` sửa trước, vẫn OFF.
  - FAQ filter giữ on.
- **W5:** dời tới khi W2 có R1 đạt và W4 xong.
- **Duyệt câu:**
  - "Làm giao diện cho 55" câu W4. 104 câu W2 khó hiểu → làm trang duyệt tiếng Việt.
  - "Đồng ý mọi đề xuất". Nút "đồng ý tất cả" không bấm được trong khung artifact → sửa thành bấm hai lần ngay trong trang.
  - "Đã duyệt" đợt 1 (200 câu) và đợt cuối (190 câu) của CL-1 1.1.0.
- **Nhãn đã duyệt phải xem lại và sửa được:** làm Writing Lab gồm hàng duyệt, trình duyệt bộ nhãn và sửa nhãn kiểu chỉ thêm (append-only) → AA-1063.
- **Guide có ảnh, "làm đầy đủ":** PNG/WebP ≤ 300 KB trong bundle docs → AA-1064. Dung lượng gần như không tốn tiền.
- **Jev lọc trước:**
  - "Sao không dùng Jev huấn luyện luôn" → thêm 2 tenant demo vào allowlist Jev, chạy shadow trên câu đã có đáp án.
  - Đạt thì lọc trước 372 câu còn lại.
- **App Odoo của chị Thư (`mdv_tour_travel` 19.0, OPL-1):**
  - Mở issue nghiên cứu.
  - Tech lead sửa trục so sánh: so với CRM đại lý (B2C), cộng thêm phần nâng cấp Booking.
  - "Không chép code, lấy tính năng rồi build".
  - Làm trang xem được trên điện thoại.
  - "Đồng ý làm tất cả": tạo issue và phân vào master plan. Câu hỏi cho chị Thư → nháp Jira/Zalo riêng, có đề xuất.
- **Chốt phiên "Cách 1":** chờ AA-741 C2/C3 và lane AA-1066 xong rồi mới đóng.

## Thay đổi codebase (đã merge)

**CIS**
- **#1416:** Jev giữ một client keep-alive cho mỗi event loop. Lượt bị circuit từ chối được tính là từ chối, không tính là lỗi (sửa a3_demand).
- **#1417 AA-1039:** đưa bài trở lại, mỗi trang WordPress một nút bấm, thay cho việc tự đăng lại.
- **#1418 AA-1049:** guard T9 `stable_keys` fail closed khi có finding mới có thể giữ bài; F14 tính theo class vi phạm.
- **#1419 AA-1063 (mig 394):**
  - Writing Lab: hàng duyệt câu bằng lời thường, đề xuất của panel agent, trình duyệt bộ nhãn.
  - Sửa nhãn kiểu chỉ thêm (`eval_claim_proposal`, `eval_claim_relabel`).
- **#1420 AA-1064:** trình đọc docs và tab Guide hiện ảnh PNG/WebP.

**Partner**
- **#256 AA-1039:** danh sách "Put back online" trong Content studio và nút trên chuông thông báo.
- **#257 AA-1062:** trang pháp lý bản nháp v0.6, bỏ câu "OpenAI viết khi bất đắc dĩ".
- **#258 (crm-048, contract) + #259 AA-1066:**
  - Giá theo loại khách; quy tắc giá theo mùa, theo đoàn, đặt sớm.
  - Giảm giá trên mức giới hạn cần chủ đại lý duyệt.
  - Settings > Pricing.

**Booking**
- **#210 AA-820:** docs về ranh giới AI trỏ tới AI Schedule của tenant.

**Infra**
- #751: copy CIS 394.
- **#752:** biến nullable `t2_orchestrator` / `t9_seo_builder`, chỉ trên worker. Terraform Apply Dev run 42771211378.

**Root**
- #657: gateway_status đếm lượt circuit từ chối riêng với lỗi.
- #658: cờ put-back trong flag register.
- #659: pháp lý v0.6.
- #660: bundle docs phát hành ảnh PNG/WebP; docs lint kiểm mọi link ảnh.
- #661: retention cho CIS 394.
- #662: schema-ref tự sinh.
- #663: retention cho crm-048.

## Việc dữ liệu / vận hành trên Dev (có trả tiền đều theo trần)

**AA-1056**
- recompute bbbc63ce xong 00:08:55Z, 69′ sau sự kiện, trong cửa sổ 2 h.
- metric late=4, max 266.724 s.

**AA-1055**
- Tỉ lệ dữ liệu tìm kiếm cũ ở DE/FR/NL giảm từ 99% xuống 8,4%.
- re-atomize a679995c: 4/4 địa điểm vào phạm vi. Preview chọn 2 (0,36 USD, chưa mua).

**AA-1058**
- S1 + T9 + recompute đủ `tour_id` / `content_piece_id` / `job_id` / `prompt_version`. 0,125 USD.
- Wave mở bởi script bằng chứng bị sót, làm Deploy Dev CIS bị chặn; đã đóng wave (có bài học).

**a3_demand**
- Một lượt recompute lúc 18:07Z dồn hơn 240 call/phút → 20 ConnectTimeout mở circuit → 4.997 lượt bị từ chối.
- Lần sau 4.745/4.745 subject được trả lời. Không mất dữ liệu. Sửa trong #1416.

**W2 / AA-1048 + AA-1063 (bộ đáp án CL-1)**
- CL-1 1.0.0 đủ 150/150: tech lead 84, panel đồng thuận 66. Audit 17, 0 câu lật.
- CL-1 1.1.0: 868 câu (tech lead 572, panel 296). Audit 74, 0 câu lật. Hàng duyệt: 0 mở / 390 đã giải quyết.
- R1: không class nào đạt n_pos ≥ 20 (tối đa 9) → không chạy lượt trả tiền. Cần thêm vi phạm, hoặc đổi thanh đo của ADR 0020.

**Jev (AA-1063)**
- Shadow `a1_claim_supported` trên 576 câu đã có đáp án: 0,085 USD.
  - p ≥ 0,90 trên held-out: 340/342, 2 câu sai đều thuộc `fact.misbinding`.
  - Luật kết hợp (p ≥ 0,90 + panel đa số ok + không lens non-ok misbinding): 341/341.
- Lọc 372 câu còn lại: 0,038 USD, 182 câu tự "Đúng" (labeller `prefilter:jev090+panel`, không vào bản ghi quyết định R1).

**W4 / AA-1050**
- Panel 3 lens không tốn tiền trên 201 câu.
- Theo object: T9 8/9 (88,9%), tất cả 14/16 (87,5%) — đạt.
- Theo câu: độ chính xác ~18% → công tắc giữ OFF.
- 55 mục đã qua tech lead duyệt.

**W3 / AA-1049**
- Thử T2 linear 5 tour: 5/5 (0,166 USD). SEO builder 3/3 bài approved (~0,21 USD).
- Replay miễn phí: 0 khác biệt chưa khai báo.
- Bật trên worker :648: `T2_ORCHESTRATOR=linear`, `T9_SEO_BUILDER=on`.

**AA-741 phase 2 (đường thật, không `trial_flags`)**
- Phạm vi: 4 tenant audit × 12 tour, 48/48 cặp.
- T2: 39 `ai_generated`, 9 `needs_review`.
- Blog trong phase 2: 28 bài — 7 duyệt, 20 giữ, 1 lỗi. Lý do giữ chính: F4_extreme_length 13; F17_trip_fact 7; F13_repeat 4; F9 2. Không có `F4_seo_surface`.
- Chi phí: 6,77 / 13,44 USD — 0,078 USD mỗi bản T2, 0,137 USD mỗi bài blog.
- Bằng chứng: `docs/audits/2026-11-10-S275-session/aa741-phase2/`.

**AA-1039**
- Drill trên test-wp bị chặn: container test-wp được tạo lại nên post 6 đã mất.
- Không có khoá sạch và không có bài nào đăng được. Cần một bài mới (~0,11 USD) → S276.

## Nghiên cứu app Odoo (AA-1065)
- Báo cáo: `docs/research/2026-11-10-odoo-tour-travel-plugin-comparison.md`.
  - 53 tính năng: CRM đại lý 35 (9 có / 16 một phần / 10 chưa), Booking 18 (12 một phần / 6 chưa).
  - Có ERD mermaid, kế hoạch build và 10 câu hỏi.
- Zip plugin để ở `docs/plugin/`, có trong `.gitignore` và `.git/info/exclude`. Không chép code (OPL-1).
- 10 issue AA-1066…1075 phân vào milestone **M-OD** (S276–S280). AA-1066 kéo lên làm ngay trong S275.
- Nháp câu hỏi cho chị Thư: Zalo (`.tmp-session/S275/thu-odoo-questions.txt`) và Jira nháp 6 (form khảo sát).

## Hội tụ Linear
- Done: AA-1056, AA-1058, AA-1064, AA-1062, **AA-1066** (Playwright live 8/8 bước, chủ đại lý + nhân viên; bằng chứng
  `docs/audits/2026-11-10-S275-session/aa1066-live/`).
- Done-with-scope: AA-1055, AA-820, AA-1046 (+ AA-1061 bk-045 từ 28/11).
- AA-1004 → Backlog, hạn 20/11, kèm nháp Zalo cho TrueIDC.
- In Review (chờ việc còn lại):
  - AA-1063: duyệt một đợt trong Lab; luật Jev thành code.
  - AA-1050: chờ W2 theo class.
  - AA-1038: test teal + Playwright.
  - AA-1024: D8.
  - AA-1065: đóng khi root PR có báo cáo merge.

## Jira (tech lead duyệt, đã đăng 10/11)
- 3 nháp S274 + 6 nháp S275 → 8 comment. Nháp DataForSEO đăng ở **PR-22**, không phải KAN-90 (tech lead sửa đích).
  - PR-22: 10629, 10630, 10631.
  - PR-25: 10632.
  - PR-23: 10633.
  - PR-13: 10634.
  - PR-26: 10635 (kèm 1 ảnh) và 10636.
- Chi tiết: `docs/audits/2026-11-10-S275-session/jira-drafts.md`. Câu hỏi cho chị Thư nằm trong bảng chọn ở PR-26 (10636).

## Trạng thái cuối phiên (từ snapshot)
- CIS: api :1081, worker :648, admin :17, `5cc016cd`, schema 394.
- Booking: api :112 `76140cdf`, bk-044.
- CRM: api :147, web :122 `451e5011`, crm-048.
- TripPlanner: web :6.
- Mọi service COMPLETED. `shared.job` 0, wave 0. PR mở: chỉ release + Booking #200 (draft).
- Cố ý để BẬT: trên worker, `T2_ORCHESTRATOR=linear` và `T9_SEO_BUILDER=on`. 2 tenant demo trong allowlist Jev.
- Dữ liệu thử để lại trên Dev: quy tắc giá mùa "+10%" và trip `ca9513f1` của đại lý thử Sen Vàng.
- Chi tiêu gateway tháng này: 26,18 USD.

## Việc đầu phiên sau (S276)
1. **AA-1024 D8:** migration 336 + `DB_AUTO_APPLY_CONTRACT` (đã qua 12:00Z 10/11).
2. **AA-1063:**
   - đưa 341 câu tranh chấp t2@2 vào hàng duyệt (hiện 0 queue item), rồi tech lead duyệt một đợt trong Writing Lab;
   - viết luật lọc trước bằng Jev thành code;
   - gỡ 2 tenant demo khỏi allowlist Jev.
3. **AA-741 phase 3:** báo cáo theo cơ chế. Bắt đầu từ 9 bài chỉ bị giữ vì F4_extreme_length, `t2_flag_fix` max_tokens 4,
   và tour không có chủ đề blog.
4. **AA-1039:** drill trên test-wp (cần một bài mới, ~0,11 USD).
5. **AA-1038:** test teal + Playwright.
6. **AA-1048 R1:** cần thêm vi phạm.
7. **M-OD:** AA-1067 (lịch trả tiền, phí huỷ) theo slot S276.
8. **Gateway:** xem `t7_debate_judge` access_denied 119/24 h có nên tính là refusal.
9. **acc3:** apply tag Terraform (cần tắt auto mode). TrueIDC: gửi tin Zalo trước 20/11 (`.tmp-session/S275/trueidc-zalo.txt`).
