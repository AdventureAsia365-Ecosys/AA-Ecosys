> **ĐÃ ĐĂNG 02/11 ~21:40 (+07)** sau khi tech lead duyệt ("ok đăng"), nguyên văn như dưới, ảnh nhúng đúng thứ tự.
> Không đổi trạng thái issue nào.

# S264 — nháp Jira cho chị Thư

Soạn 02/11/2026 ~21:20 (+07), Claude Code, phiên S264. Mention khi đăng:
`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>` (thay chữ `@thule`
ở đầu mỗi nháp).

## Đã rà trên Jira (chỉ đọc, 02/11 ~21:15)

- JQL `project in (PR, KAN, CON) AND updated >= "2026-11-02"`: chỉ PR-20, PR-22…PR-26, cập nhật cuối 06:40–06:42 (đợt
  đăng nháp S263 sáng nay). Không có comment mới của chị Thư sau đó. KAN/CON: không có việc mới liên quan → không soạn.
- Không soạn PR-24 (TripPlanner: việc phiên này là phần kỹ thuật của cổng AI, khách không thấy khác) và PR-25 (Booking:
  thanh bên gom nhóm đã lên Dev nhưng agent chưa có tài khoản Booking để chụp ảnh kiểm). PR-27 không soạn (việc kỹ thuật
  của tech lead).

## Danh sách

| # | Issue | Một dòng | Ảnh |
|---|---|---|---|
| 1 | PR-23 Portal | AI viết bài cho đối tác chạy lại (đường dự phòng OpenAI), điều khoản ghi rõ, thanh bên gom nhóm, tab Thành viên phía AA | 3 |
| 2 | PR-26 CRM | Danh sách việc + tự động hoá kiểm thật; link điều khoản CRM đúng trang; thanh bên; ô nháp AI (chưa thử) | 5 |
| 3 | PR-22 CIS | Thanh bên gom nhóm, trang tải file trên điện thoại, cảnh báo nhà cung cấp và trần AI chung | 2 |
| 4 | PR-20 | Báo cáo kỳ 3 đã cập nhật phần 02/11 sau buổi họp (cùng link) | 0 |

## Kiểm trước khi đăng (ô tech lead chốt)

- [ ] Ảnh trang Nhà cung cấp AI / Budgets / Members có dòng: **không đính** (có account ID / mã nhân viên, nằm ở thư mục riêng).
- [ ] Ảnh 2 (PR-23) là trang Members của tenant "Adventure Asia Internal" (trống) — đính hay bỏ tuỳ tech lead.
- [ ] Câu "AI viết chạy lại" (PR-23 §1): bằng chứng là một lượt gọi bước viết lúc 18:33 (dòng sổ AI, model OpenAI trả bài),
  **chưa** thử bấm viết từ giao diện Content studio. Nếu tech lead muốn, thử một bài trong studio Atlas & Hearth trước khi đăng.

---

## 1. PR-23 — Portal tenant

**Vì sao issue này:** việc người dùng nhìn thấy trong Content studio: viết bài chạy lại, điều khoản, thanh bên; và phía AA
quản lý thành viên của đối tác.

**Nội dung (sẵn để đăng):**

@thule Cập nhật Content studio ngày 02/11 (Dev, dữ liệu thử):

| Phần | Đã thử trên Dev | Chưa thử |
|---|---|---|
| AI viết bài cho đối tác | chạy lại từ 18:33 qua đường dự phòng cuối (OpenAI, có trần chi phí); bài thử viết xong | viết từ giao diện studio |
| Điều khoản §3 và Quyền riêng tư §5 | ghi rõ đường dự phòng này | — |
| Thanh bên trái gom nhóm | thu gọn được, nhớ trạng thái sau khi tải lại, máy tính + điện thoại | — |
| AA quản lý thành viên của đối tác (CIS admin) | xem danh sách thành viên | mời người mới qua giao diện |

- **AI viết bài chạy lại:** từ 29/10 tài khoản AI chính bị AWS chặn nên đối tác không viết bài mới được. Từ 18:33 ngày 02/11,
  khi đường chính bị từ chối, bước viết tự chuyển sang đường dự phòng cuối là OpenAI (gọi thẳng, có trần chi tiêu). Bài thử
  đầu tiên viết xong ("At dawn, Hoi An's lantern-lit lanes…"). Khi tài khoản AI chính mở lại, hệ thống tự dùng lại đường chính.
- **Điều khoản:** Điều khoản §3 và Quyền riêng tư §5 của studio ghi rõ khi nào bài được viết qua đường dự phòng này (bản
  nháp, vẫn chờ chị chọn phương án A/B/C và luật sư như câu hỏi trước).
- **Thanh bên:** các mục gom theo nhóm (Tours, Content, Publish…), bấm để thu gọn, mở lại trang vẫn giữ như lúc rời đi.
- **Thành viên:** trong CIS admin, mỗi đối tác có tab Thành viên: ai có quyền vào Content studio, vai trò, ngày mời. AA mời
  được người mới kèm quyền studio. Đã kiểm phần xem; chưa mời người mới qua giao diện.

Ảnh theo thứ tự: (1) Điều khoản §3 có đường dự phòng, (2) tab Thành viên trong CIS admin, (3) thanh bên studio gom nhóm.

**Ảnh:**

| # | Tên khi upload | File |
|---|---|---|
| 1 | studio-dieu-khoan-du-phong.png | `docs/audits/2026-11-02-S264-live-verify/05-studio-terms-fallback-1440-light.png` |
| 2 | cis-thanh-vien-doi-tac.png | `docs/audits/2026-11-02-S264-live-verify/05-cis-tenant-members-1440-light.png` |
| 3 | studio-thanh-ben.png | `docs/audits/2026-11-02-S264-live-verify/05-studio-sidebar-1440-light.png` |

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Viết chạy lại 18:33 qua OpenAI | migration 344 áp 11:30Z (`/health/ready` 344); lượt `t9_write` 11:33Z: đường chính từ chối → GPT-6 Luna (OpenAI) trả bài (checklist S264) |
| Điều khoản §3, Quyền riêng tư §5 | live-verify §5 dòng 5, ảnh `05-studio-terms-fallback-*`, `05-studio-privacy-fallback-*` |
| Thanh bên | live-verify §5 dòng 1d (6 nhóm, mở lại vẫn giữ, 390 px) |
| Tab Thành viên | live-verify §5 dòng 2 (danh sách PASS); mời qua giao diện chưa thử |

---

## 2. PR-26 — CRM cho đại lý

**Vì sao issue này:** danh sách việc và tự động hoá là hạng mục trong kế hoạch CRM, nay kiểm thật xong; sửa link điều khoản.

**Nội dung (sẵn để đăng):**

@thule Cập nhật CRM cho đại lý ngày 02/11 (Dev, đại lý thử "Lữ hành Sen Vàng", dữ liệu giả):

| Phần | Đã thử trên Dev | Chưa thử |
|---|---|---|
| Danh sách việc (Tasks) | tạo việc → hiện trong danh sách → đánh dấu xong | — |
| Tự động hoá quy trình (Automations) | cài mẫu "Visa and documents task list", áp vào chuyến: đạt 4/4 tình huống | mẫu chạy theo mốc giờ (T-48 h, T-21 ngày), mẫu chúc mừng sinh nhật |
| Link "Điều khoản" trong CRM | mở đúng trang điều khoản CRM, mục AI | — |
| Thanh bên trái gom nhóm | thu gọn được, nhớ trạng thái, máy tính + điện thoại | — |
| Ô nháp AI trên trang chuyến | đã lên Dev | chưa thử (cần bật AI cho một đại lý thử) |

- **Danh sách việc:** trang Tasks có việc của tôi / của nhóm / đã xong, có bản tóm tắt buổi sáng. Đã thử tạo một việc, đánh
  dấu xong, việc chuyển sang mục Đã xong.
- **Tự động hoá quy trình:** đại lý chọn mẫu trong thư viện của AA (10 mẫu) và áp vào chuyến. Đã thử với mẫu "Visa and
  documents task list" (3 việc, hạn trước ngày đi 60 / 45 / 30 ngày):
  - chuyến có ngày đi: tạo 3 việc với đúng hạn;
  - chuyến chưa có ngày: 3 việc nằm ở mục "Waiting for dates" cho tới khi có ngày;
  - áp lại lần nữa: không tạo việc trùng;
  - huỷ chuyến: quy trình đang chạy dừng ngay, các việc mở của chuyến chuyển sang bỏ qua.
- **Điều khoản:** link "Terms of use" ở chân trang và ở Cài đặt → AI nay mở đúng trang điều khoản của CRM (trước đó mở nhầm
  điều khoản của Content studio).
- **Ô nháp AI trên trang chuyến:** đã lên Dev, chỉ đại lý có quyền dùng AI theo gói mới thấy, dưới bản nháp có dòng nhắc "AI
  có thể sai". Chưa thử thật.

Ảnh theo thứ tự: (1) trang Tasks, (2) quy trình chạy xong trên chuyến có ngày đi, (3) việc chờ ngày của chuyến chưa có
ngày, (4) huỷ chuyến dừng quy trình, (5) trang điều khoản CRM mục AI.

**Ảnh:**

| # | Tên khi upload | File |
|---|---|---|
| 1 | crm-danh-sach-viec.png | `docs/audits/2026-11-02-S264-live-verify/03-crm-tasks-1440-light.png` |
| 2 | crm-quy-trinh-chuyen-co-ngay.png | `docs/audits/2026-11-02-S264-live-verify/03-wf-2a-trip-dated-run-1440-light.png` |
| 3 | crm-viec-cho-ngay.png | `docs/audits/2026-11-02-S264-live-verify/03-wf-2d-tasks-waiting-for-dates-1440-light.png` |
| 4 | crm-huy-chuyen-dung-quy-trinh.png | `docs/audits/2026-11-02-S264-live-verify/03-wf-4-cancelled-run-stopped-1440-light.png` |
| 5 | crm-dieu-khoan-ai.png | `docs/audits/2026-11-02-S264-live-verify/05-crm-legal-terms-ai-1440-light.png` |

**Câu → bằng chứng:** live-verify §3 (Tasks), §3b (bảng thời gian 00:58–01:06Z: dated / undated / idempotent / cancel
STOPPED), §5 dòng 4 (terms), §5 dòng 1c (thanh bên). Ô nháp AI: Partner #194 (ship), chưa có ảnh.

---

## 3. PR-22 — CIS

**Vì sao issue này:** thay đổi trang quản trị CIS mà nhân viên AA thấy.

**Nội dung (sẵn để đăng):**

@thule Cập nhật trang quản trị CIS ngày 02/11 (Dev):

- **Thanh bên trái gom 10 nhóm**, chỉ nhóm đang dùng mở sẵn; bấm để thu gọn, mở lại trang vẫn giữ. Chế độ thu nhỏ chỉ còn
  biểu tượng. Đã kiểm trên máy tính và điện thoại, sáng và tối.
- **Trang tải file (Upload) dùng được trên điện thoại:** các bước không còn tràn ra ngoài màn hình.
- **Nhà cung cấp AI:** thêm trần chi tiêu AI chung cho cả app (báo ở 80 %), công tắc bật/tắt AI theo từng app, và cảnh báo khi
  nhà cung cấp dữ liệu có vấn đề (Jev lỗi liên tục, số dư DataForSEO thấp, credit AI sắp hết). Đã thử thật: chuông trong admin
  và email cảnh báo đều tới (các email cảnh báo tối 02/11 khoảng 18:15–18:38 là email thử của lần kiểm này).

Ảnh theo thứ tự: (1) thanh bên gom nhóm, (2) trang Upload trên điện thoại.

**Ảnh:**

| # | Tên khi upload | File |
|---|---|---|
| 1 | cis-thanh-ben.png | `docs/audits/2026-11-02-S264-live-verify/05-cis-sidebar-1440-light.png` |
| 2 | cis-upload-dien-thoai.png | `docs/audits/2026-11-02-S264-live-verify/05-cis-upload-390-light.png` |

**Câu → bằng chứng:** live-verify §5 dòng 1a, 6, 3a; checklist S264 "B3 live PASS 11:15Z", "B4 live PASS 11:38Z", "B5 live
PASS 11:18Z". Ảnh trang AI có account ID → không đính.

---

## 4. PR-20 — báo cáo kỳ 3 (bổ sung)

**Nội dung (sẵn để đăng):**

@thule Báo cáo kỳ 3 đã cập nhật thêm phần làm ngày 02/11 sau buổi họp (cùng link như sáng nay):
https://claude.ai/artifact/5QtvFweK4LHaMwF3HfXDok

Điểm mới: AI viết bài cho đối tác chạy lại qua đường dự phòng; CRM có danh sách việc và tự động hoá quy trình đã kiểm thật;
thanh bên của CIS, CRM và Content studio gom nhóm; diễn tập quay lại bản cũ đạt 5/5 bài, không tốn phí. Hệ thống kiểm lại lúc
21:10, mọi app trả lời bình thường.

**Bằng chứng:** `state-snapshot.md` (cùng thư mục), game day `docs/audits/2026-11-02-S264-rollback-game-day/`.

---

## Kết quả đăng

| Issue | Comment | Ảnh |
|---|---|---|
| PR-23 | https://adventure-asia.atlassian.net/browse/PR-23?focusedCommentId=10604 | 3 |
| PR-26 | https://adventure-asia.atlassian.net/browse/PR-26?focusedCommentId=10605 | 5 |
| PR-22 | https://adventure-asia.atlassian.net/browse/PR-22?focusedCommentId=10606 | 2 |
| PR-20 | https://adventure-asia.atlassian.net/browse/PR-20?focusedCommentId=10607 | 0 |
