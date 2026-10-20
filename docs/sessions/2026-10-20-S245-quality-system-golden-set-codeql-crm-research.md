# S245 — 20/10/2026: golden set + baseline, Hệ thống chất lượng v1, CodeQL về 0, alert recipients, CRM research

**Tác nhân:** Claude Code (Ultracode, nhiều workflow, nhiều agent). Phiên rất dài, có một lần compact context và một lần đổi tài khoản Claude (admin@ → nghieppham@adventure.asia).

## Trạng thái cuối phiên

- **ECS:**
  - api `aa-cis-dev-api:730` và worker `aa-cis-dev-worker:287`: rollout COMPLETED sau CIS #885 (merge da07b7db), `/health` 200.
  - Task một lần chạy baseline AA-729 (task def api:729) đã thoát, mã 0.
- **CodeQL AA-CIS-App:** 0 cảnh báo mở (đầu phiên 31).
- **Repo:** mọi repo con ở `main`, cây sạch. Repo gốc ở `master`: PR #121–#142 đã merge; PR đóng phiên mở riêng.
- **Linear:**
  - Đã đóng: AA-860, AA-895, AA-846, AA-887, AA-805, AA-680, AA-878, AA-907, AA-913, AA-914, AA-826, AA-893, AA-800, AA-865, AA-888, AA-875, AA-849, AA-787, AA-912.
  - Mới: AA-912, AA-913, AA-914, AA-915..AA-923 (Writing Memory), AA-924 (từ AA-787), AA-925 (Q-2), AA-926 (Q-1), AA-927 (log chi phí LLM).
- **Chi phí trả phí trong phiên** (ước, theo `llm_call_log` và DFS): khoảng $8.
  - Các lượt trước compact: blog r7 $0,70, T2 khoảng $0,38, r8 $1,20, SERP top-up $0,02.
  - AA-729: trial $0,13 và baseline $5,41.

## Quyết định của Nghiệp (trong phiên)

**Viết tự học và Hệ thống chất lượng**
- **Writing Memory:** duyệt D1–D16 và các câu cắt chi phí E1–E4. Đã tạo issue AA-915..923.
- **Định hướng dài hạn** (đã lưu memory `systematic-quality-direction`): xây hệ thống viết và chấm có tính hệ thống — chặn lỗi lặp lại, không để sửa chỗ này sinh lỗi chỗ khác, có huấn luyện để tự học — thay vì vá lỗi lặt vặt.
- **Hệ thống chất lượng v1** (`docs/audits/2026-10-20-S245-quality-system/`): duyệt D1–D11.
  - D3 = b: trần chung $40/tháng, $10/lần chạy. Anh hỏi thêm cách tiết kiệm; đã ghi 4 cách vào AA-919.
  - D6 = a, kèm ghi chú "làm sao tốt hơn cho chất lượng". Trả lời: phủ theo lớp lỗi và chọn mẫu theo chỗ bất đồng; đã ghi vào AA-919.
  - D7 = b: panel agent gán bộ audit verifier thay anh.
  - D9 = a: chỉ 2 issue mới (Q-2, Q-1).
  - D10 = a: AA-779 dừng vá luật, dựng bộ câu có nhãn giữ/bỏ rồi sửa một lần theo số.
  - D11 = a: giữ các loop writer–judge, nối 3 loop học đang hở, thêm repair contract.
- **AA-729:** duyệt toàn bộ 82 nhãn panel (68 chốt + 14 mẫu tranh chấp, cả 14 theo đề xuất). Duyệt baseline có phí, trần $15.

**Issue lẻ**
- **AA-787:** đồng ý đổi Done-when thành "31 → 26 gate". Phần gộp F15 và gate từ vựng chuyển sang AA-924.
- **AA-849:** Nghiệp tự bật required check `Migrations (lint, PG 15 replay)` trên TripPlanner `main`.
- **AA-875:** Nghiệp tạo site TasteWP mới (needlesspoint) và mật khẩu ứng dụng "AA portal e2e"; secret do agent lưu.
- **Cảnh báo:** gửi tới nghieppham@adventure.asia; danh sách người nhận quản lý ở trang admin (AA-913), không hard-code.

**Linear**
- Không nâng gói. Làm B + C + D: archive qua API, xuất issue ra repo, ít issue cỡ "giao được".
- Chuyển "Recently deleted" sang Archive; khôi phục mọi issue chưa xong.

**CRM đại lý**
- Tách thành app riêng tích hợp vào portal, không là module trong CIS. Tách hẳn admin CIS khỏi portal tenant.
- Hai trang duyệt CRM để Nghiệp và chị Thư xem sau. Form câu hỏi cho chị Thư viết theo kiểu khảo sát trung tính.
- Chị Thư comment PR-19 (20/10) nhờ dùng REA bóc tách Tern và TravelJoy. Nghiệp chốt: **không đăng trả lời Jira**, phải tự phân tích và thiết kế kỹ trước.

**Artifact và phiên**
- Mọi artifact có quyết định phải có nút chọn và nút duyệt. Tắt theo dõi artifact.
- Phiên quá dài: dừng ở đây.

## Kết quả chính (bằng chứng)

**AA-729 — golden set + baseline**
- Harness CIS #883. #884: gói gửi panel mang nguồn đầy đủ, vì đoạn trích 2.500 ký tự che nguồn ở 76/82 mẫu.
- Panel 3 giám khảo + kiểm chứng nguồn đầy đủ. Fixture `docs/eval/aa729/fixture-1.1.0.json` có 100/100 mẫu có nhãn.
- Baseline (`docs/audits/2026-10-20-S245-aa729-baseline/`):
  - Score-only: $0,22. Regenerate: $5,19.
  - Lệch giữa judge/gate và nhãn: 43,6%.
  - **S1 lọt 26/44 bài lỗi; T9 chặn oan 12 bài tốt.**
  - Injection: chặn 10/10.
  - Jev S1 khớp nhãn 12,5%.
  - Lời gọi LLM không có dòng log: 116/216 và 188/815 → AA-927.
- AA-729 vẫn In Progress: còn chờ lần thay đổi đầu tiên trích số trước/sau.

**AA-912 — CodeQL backlog** (CIS #885, deploy da07b7db)
- 13 regex viết lại chạy tuyến tính. Mỗi regex có fuzz so với bản cũ và test giới hạn thời gian.
  - Tệ nhất: regex hashtag, khoảng 100 ký tự treo hàng giờ → 0,1 ms.
- Một định nghĩa citation tag dùng chung (`services/acp_shared/citation_tags.py`).
- 5 chỗ lộ stack trace: trả thân lỗi chung + ref id.
- 17 cảnh báo đóng có số đo: 12 báo nhầm, 5 chỉ trong test.
- Sửa thêm test AA-913 phụ thuộc đồng hồ: đỏ ở mọi nhánh từ 12:55 UTC.

**AA-875 — safe_http** (CIS #880)
- Ca chặn: 422 + log `safe_http_blocked`.
- Ca dương tính trên tenant terra-family: kết nối 200 → test 200 → đăng bài 200 (bài trên site trả 200) → gỡ bài (`trashed`, link 404) → ngắt kết nối.

**AA-913 — người nhận cảnh báo do admin quản lý**
- CIS #872–#874 (mig 251, router + UI, gợi ý "Did you mean"); Infra #237. Nghiệp đã xác nhận qua mail.

**AA-914 / AA-800 / AA-865 / AA-780 / AA-787**
- AA-914: route guard (#879).
- AA-800: signature words (#875).
- AA-865: r8, 0/28 lỗi từ retry; F9 gộp 6,2%.
- AA-780: sàn 120 từ (#881). Baseline: 15/15 bài LinkedIn ≥ 152 từ, nhưng chưa có nhãn panel r5.
- AA-787: bỏ 4 gate, 31 → 26 (#878).

**AA-779 — FAQ dùng câu hỏi thật** (#877, #882 đã merge)
- Nhánh `fix/real-questions-scope-variants`: 4 commit, đến 1a7a73b3, khoảng 500 test, **không đẩy lên**.
- 3 vòng sửa + review đối kháng không hội tụ: mỗi vòng lại sinh "giữ nhầm" mới (Karakoram, Mongolian beef, Kobe, Lake Victoria…).
- Theo D10: dừng vá luật.

**Hệ thống chất lượng v1**
- Thiết kế bản 2 qua 2 vòng phản biện, 32 điểm. §13 nói về các loop writer–judge.
- Trang duyệt: <https://claude.ai/artifact/9mmgckVoU9BHQ3dG6woEuG>.

**CRM**
- v2 / v2.1 / v2.2 (#127, #129, #133); spec song ngữ; form câu hỏi chị Thư.
- Bóc tách Tern và TravelJoy chỉ từ nguồn công khai, vì điều khoản cả hai cấm dịch ngược và scrape (`docs/audits/2026-10-20-S245-crm-tern-traveljoy/`):
  - lõi spec ngang hai đối thủ;
  - 11 lợi thế của AA, 10 khoảng trống;
  - 16 đề xuất. Trang duyệt: <https://claude.ai/artifact/5srRKGxXrdiADV6u13niAH>, Nghiệp **chưa bấm**.

**Linear (công cụ và quy trình)**
- `tools/linear/linear_export.py`: xuất issue ra `docs/linear-export/` và archive qua API.
- Quy tắc steering mới: 1 issue = 1 lát giao được.

**Hạ tầng và tài liệu**
- Docs lint (AA-888) và generated docs (#139). Contract hash guard (#241).
- Alarm catalog + Terraform outputs (AA-893, Infra #244).
- Secret mới `aa-ecosys/ops/linear-api-key`.

## Còn lại / việc phiên sau (S246)

**Thứ tự đề xuất**
1. **AA-925 (Q-2)**, làm trước theo D9: repair contract, sửa fitter AA-740, bộ đếm `degraded[]`, oracle số ngày S1 (chạy trên khoảng 900 tour), corpus Q0. Đây là thay đổi đầu tiên trích số trước/sau trên fixture 1.1.0, nên đóng được AA-729.
2. **AA-779 theo D10:**
   - dựng bộ khoảng 150–200 câu PAA thật có nhãn giữ/bỏ, cộng các câu bẫy reviewer đã tìm (`.tmp-session/aa779-review.json`, `.tmp-session/aa779-fix-r2.json`);
   - panel gắn nhãn, Nghiệp duyệt;
   - đo 3 phương án: `main`, nhánh luật, bộ phân loại LLM nhỏ.
3. **AA-926 (Q-1):** taxonomy, registry, thresholds, lint.
4. **AA-927:** lời gọi LLM thiếu log.
5. **AA-780:** panel gắn nhãn 15 bài LinkedIn đã viết lại (run dab254c4), đóng hoặc chỉnh.
6. **AA-845:** nhãn panel 100 claim, chọn trần reject (kết hợp số Jev 12,5% của golden set), điều tra 402.
7. **CRM (AA-821):** sau khi Nghiệp duyệt 16 đề xuất, làm thiết kế bản kế tiếp (luồng màn hình và wireframe theo mẫu dễ dùng của Tern và TravelJoy, mô hình dữ liệu, chi phí, chia issue). Nghiệp duyệt bản đó rồi mới soạn bảng hỏi trung tính cho chị Thư. **Không trả lời Jira PR-19 trước khi xong.**

**Chờ Nghiệp**
- Bấm duyệt 16 đề xuất CRM: <https://claude.ai/artifact/5srRKGxXrdiADV6u13niAH>.
- Thu hồi mật khẩu ứng dụng "AA portal e2e" trên site TasteWP test khi không cần nữa (mật khẩu đã hiện trong transcript).
- Hai trang CRM v2.1/v2.2 và form câu hỏi chị Thư: Nghiệp và chị Thư xem khi rảnh.

**Không làm trong phiên (ghi lại)**
- Nháp Jira báo cáo tuần PR-20: không soạn, vì Nghiệp dừng phiên và không muốn đăng gì cho chị Thư lúc này.
- Tracker artifact Q4LvqJyX… thuộc tài khoản Claude cũ nên không cập nhật được. `plan.json` vẫn cập nhật trong repo; khi cần thì xuất bản lại dưới tài khoản mới.

## Lưu ý kỹ thuật cho phiên sau

- **ECS exec:** stdout bị cắt ở khoảng 1 KB. Kết quả lớn ghi ra S3 bronze `scripts/out/...`, rồi tải về.
- **Lượt chạy trả phí dài:** chạy trong ECS task một lần (`run-task` với command override, network giống service api) để exec hay deploy không cắt ngang. Mẫu lệnh: `.tmp-session/aa729run/` (overrides tạo bằng script, presigned URL cho tgz và fixture).
- **Harness AA-729:** không nằm trong image. Đóng gói từ `origin/main:scripts/aa729` thành `s3://…/scripts/aa729.tgz`. Fixture ở `s3://…/scripts/out/aa729/fixture-1.1.0.json`.
- **Đổi tài khoản Claude:** artifact của tài khoản cũ đọc được qua link `?sk=` mà Nghiệp share trong team, nhưng không ghi được.
- **Thử biến thể mật khẩu bị auto mode chặn** (bị coi là dò thông tin đăng nhập): xin chính xác giá trị từ Nghiệp.
- **Repo gốc không có required check:** chờ Docs lint xanh rồi mới `gh pr merge` (#141 merge đỏ, đã sửa bằng #142).
- **CodeQL:** giữ regex cũ trong test để chứng minh tương đương sẽ sinh cảnh báo mới trên PR → đóng với lý do "used in tests".
