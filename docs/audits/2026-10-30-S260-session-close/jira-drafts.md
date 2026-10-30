---
id: OPS-08-s260-jira-drafts
title: "S260 Jira drafts (S258 + S259 carried over + S260)"
description: "Nháp comment Jira cuối phiên S260 (gộp nháp S258/S259 chưa đăng), chờ tech lead duyệt trước khi đăng."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-30
review_every_days: 30
related: [AA-952, AA-994, AA-997, AA-955, AA-967, AA-961, AA-855]
---

# S260 — nháp Jira (chờ duyệt, CHƯA đăng)

Soạn 30/10/2026 ~20:30 +07, cập nhật ~22:30 (PR-26 thêm ký điện tử, dữ liệu, lịch theo bằng chứng mục 5, 6, 8; PR-24 thêm sửa bản đồ). Gộp nháp S258 + S259 (tech lead bảo gom sang S260) với việc S260: mỗi issue Jira đúng
**một** nháp. Đã đọc comment mới nhất của PR-22…PR-26 trên Jira (connector Atlassian chạy được, 30/10 ~20:20) để không
lặp: comment gần nhất là PR-22/PR-24/PR-23 ngày 29/10 15:27, PR-25 ngày 29/10 09:31, PR-26 ngày 28/10 20:43.

Quy ước khi đăng: `@thule` → mention node (`contentFormat: html`,
`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`); bảng markdown →
bảng HTML; ảnh upload bằng `uploadAttachmentToJiraIssue` rồi nhúng qua `inlineFileId` theo đúng thứ tự ghi trong
comment. Không mã Linear, đứng tên Nghiệp, không "ạ".

Bỏ trong lượt này: PR-27 (hạ tầng, việc kỹ thuật tech lead tự quyết — memory `jira-no-tech-decisions`); PR-20 báo cáo
tuần (chưa tới hạn, xem cuối file).

---

## 1. PR-25 — Booking — Hệ thống đặt tour (trip case, báo giá, thanh toán)

**Vì sao:** nháp S259 (lưới khách sạn, menu dòng hoá đơn/thanh toán, ô nhập liệu theo bộ giao diện chung) chưa đăng;
S260 thêm nút/tab/menu theo bộ giao diện chung, đã kiểm trên bản Dev. Comment gần nhất trên Jira (29/10 09:31) chưa nói
các phần này.

**Nháp (dán nguyên văn):**

> @thule Cập nhật Booking ngày 30/10 (tiếp theo cập nhật 29/10):
>
> - **Khách sạn** mở dạng lưới ảnh: mỗi khách sạn có ảnh đầu tiên của nhà cung cấp (hoặc ô "No photo"), số ảnh, địa
>   điểm, hạng sao, nhà cung cấp, số loại phòng và giá đang áp dụng, trạng thái; có nút chuyển sang dạng bảng như cũ.
> - **Hoá đơn và Thanh toán**: mỗi dòng có menu thao tác (xem hoá đơn, mở hồ sơ chuyến, huỷ hoá đơn khi được phép; với
>   thanh toán: xem, tải chứng từ, huỷ khi được phép), không cần mở trang chi tiết trước.
> - **Giao diện thống nhất với các app khác:** toàn bộ ô nhập liệu, nút, tab và menu trong Booking dùng chung một bộ
>   giao diện (cùng kiểu, cùng trạng thái lỗi, cùng viền nổi khi chọn bằng bàn phím). Đã kiểm trên bản Dev 30/10: tab
>   của hồ sơ chuyến chuyển được bằng phím mũi tên; menu "Change status" đóng bằng phím Esc; trong trình soạn đề xuất,
>   từng ngày thu gọn / mở lại được; chế độ sáng / tối đổi đúng. Trên điện thoại, dải tab cuộn ngang gọn trong khung,
>   trang không bị tràn.
>
> Ảnh theo thứ tự: (1) lưới khách sạn, (2) bảng hoá đơn có menu dòng, (3) hồ sơ chuyến với nút "Change status" và dải
> tab trên bản Dev. Ảnh 1–2 chụp từ bản chạy thử giao diện với dữ liệu mẫu; ảnh 3 chụp trên bản Dev.

**Ảnh đính kèm (theo thứ tự):**

1. `docs/audits/2026-10-30-S260-session-close/evidence/booking-khach-san-luoi-anh.png` (dữ liệu mẫu, 1440 px)
2. `docs/audits/2026-10-30-S260-session-close/evidence/booking-hoa-don-menu-dong.png` (dữ liệu mẫu, 1440 px)
3. `docs/audits/2026-10-30-S260-session-close/evidence/booking-ho-so-chuyen-tab.png` (bản Dev, cắt từ
   `2026-10-30-S260-evidence/02-case-tabs-1440-light.png`: bỏ phần tên khách thử vì tên đó chứa mã issue nội bộ)

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Lưới ảnh khách sạn, menu dòng hoá đơn / thanh toán | Booking #156 `45de036`, Deploy Dev xanh; bộ test bố cục 281/281 (S259). Ảnh dữ liệu mẫu; chưa chụp lại trên Dev với dữ liệu thật |
| Ô nhập liệu theo bộ giao diện chung | S259 (cùng đợt #156) |
| Nút / tab / menu theo bộ giao diện chung | Booking #158 `048c4981` merged + deploy; bộ test bố cục 282/282 |
| Tab đổi bằng phím mũi tên, Esc đóng menu, thu gọn ngày, sáng/tối, 390 px không tràn | `2026-10-30-S260-evidence/README.md` mục 2 — PASS live 30/10 17:40–18:20 (ảnh `02-*`) |

Không nói: lưu thay đổi tuỳ chọn thông báo (phiên E2E Booking chỉ đọc, ghi trả 403 đúng thiết kế, chưa thử lưu thật).
Ảnh live `02-builder-*` / `02-case-tabs-*` nguyên khổ có tên khách thử chứa mã issue nội bộ → không đính.

---

## 2. PR-26 — CRM cho đại lý — quản lý khách của travel agency (sản phẩm hoàn chỉnh)

**Vì sao:** S260 ship và thử trên Dev: hoá đơn + thanh toán + hoàn tiền (trọn vòng qua giao diện), ký điện tử hợp đồng
+ waiver (trọn vòng qua cổng khách), xuất / xoá dữ liệu theo yêu cầu (xoá chỉ chạy thử), lịch đại lý + link lịch + trang
khách đang đi; gộp nháp S258/S259 chưa đăng (vòng đời chuyến tới Hoàn tất, trợ lý không thấy lãi, sản phẩm AA trọn vòng
tới khi Booking xác nhận). Comment gần nhất trên Jira (28/10) chỉ nói gửi email an toàn.

**Nháp (dán nguyên văn):**

> @thule Cập nhật CRM cho đại lý (Dev, 30/10/2026, đại lý thử, dữ liệu giả):
>
> **Hoá đơn, thanh toán và hoàn tiền: đã thử trọn vòng trên Dev qua giao diện**, với khoản cọc 540 USD của một chuyến
> đã được khách chấp nhận đề xuất:
>
> - Cài đặt → Thanh toán: đại lý ghi cách khách trả tiền (ví dụ chuyển khoản vào tài khoản của đại lý) và thiết lập hoá
>   đơn (tiền tố số, thuế, số ngày phải trả).
> - Từ khoản cọc đến hạn: tạo hoá đơn nháp → phát hành, hệ thống cấp số liên tục **INV-000001**; bản in hoá đơn mở ở
>   tab mới.
> - Khách trả hai lần (200 rồi 340 USD): hoá đơn chuyển **Đã trả**, khoản cọc trong lịch thanh toán chuyển đã trả, chuyến
>   tự chuyển sang **Đã đặt**.
> - Hoàn 50 USD: chủ đại lý gửi yêu cầu, một thành viên khác của đại lý duyệt rồi ghi đã hoàn; hoá đơn hiện "đã hoàn 50
>   USD".
> - Trang **Payments** liệt kê hoá đơn theo trạng thái (chưa trả, nháp, đã trả, đã huỷ) và các yêu cầu hoàn tiền đang
>   chờ.
> - Hệ thống không cho đánh dấu "đã trả" thẳng trên khoản đã có hoá đơn phát hành, và nhắc ghi tiền vào hoá đơn (hoặc
>   huỷ hoá đơn trước).
>
> **Ký điện tử điều khoản đặt tour và waiver: đã thử trọn vòng trên Dev qua cổng của khách (30/10)**, trên một chuyến
> 2 khách, trong đó có một trẻ 10 tuổi:
>
> - Mỗi khách có một link riêng vào cổng chuyến, đọc điều khoản đặt tour và waiver ngay trên cổng, rồi ký bằng mã xác
>   nhận.
> - Trẻ vị thành niên không tự ký được: cổng báo khách chính sẽ ký thay. Khách chính ký bản của mình, rồi ký thay cho trẻ
>   với tư cách người giám hộ.
> - Nhập sai mã thì bị từ chối và báo số lần thử còn lại. Nếu nội dung tài liệu đã đổi so với bản khách đang đọc thì
>   không ký được.
> - Mỗi bản ký được niêm phong. Trên trang chuyến, đại lý thấy "mọi khách đã ký", ai ký cho ai và nhật ký ký; mở bản đã
>   niêm phong (phải ghi lý do) thì hệ thống kiểm lại và báo niêm phong hợp lệ.
> - Khi ký, hệ thống cũng ghi nhận khách đã chấp nhận điều khoản đặt tour.
>
> **Xuất dữ liệu và xoá dữ liệu theo yêu cầu của khách: đã thử trên Dev (Cài đặt → Dữ liệu, 30/10); phần xoá chỉ chạy
> thử, không xoá thật:**
>
> - Đại lý ghi nhận yêu cầu của khách (xin bản sao dữ liệu, hoặc xin xoá); hệ thống tự đặt hạn trả lời 30 ngày.
> - Xuất dữ liệu của một khách: sau vài giây có file ZIP (41 bản ghi, dạng JSON và CSV, kèm mã kiểm tra). File tải bằng
>   link dùng một lần; mở lại link đã dùng thì bị từ chối. File tải về khớp mã kiểm tra.
> - Xoá dữ liệu: bước kiểm tra cho biết sẽ xoá bao nhiêu bản ghi (lần thử: 7 bản ghi) và chờ đại lý xác nhận thêm một
>   lần. Khách còn chuyến chưa kết thúc thì hệ thống từ chối xoá.
>
> **Lịch của đại lý và khách đang đi (Dev, 30/10):**
>
> - **Lịch** theo tháng gom ngày khởi hành, ngày về, hạn thanh toán, hạn ký, việc cần làm và cuộc gọi; xem chuyến của
>   mình hoặc cả đại lý. Đã kiểm với dữ liệu thử tháng 10–11: lịch hiện đúng các mục (ví dụ hạn ký 8/11, hạn trả phần
>   còn lại 9/11 và 19/11, khởi hành 29/11). Giờ của từng việc đã được chỉnh để hiện theo giờ địa phương của đại lý
>   (bản chỉnh lên Dev tối 30/10, chưa chụp lại; ảnh 10 chụp trước bản chỉnh nên giờ trong ảnh còn lệch).
> - **Link lịch riêng** để đưa lịch CRM vào Google Calendar, Outlook hoặc lịch Apple: chủ đại lý tạo link; link chỉ có
>   ngày và mã chuyến, không có tên khách hay số tiền; bấm dừng link thì link ngừng hoạt động ngay. Đã kiểm link trả về
>   đúng định dạng lịch chuẩn; chưa thử đăng ký link trên một ứng dụng lịch thật.
> - **Trang "Travelling now"** (khách đang đi hôm nay / 7 / 14 ngày tới, theo vùng): đã có trong hệ thống, nhưng trên
>   Dev chưa có chuyến nào trong 14 ngày tới nên trang chỉ hiện trạng thái trống. Phần dữ liệu phía sau đã kiểm riêng:
>   chuyến khởi hành 29/11 xếp đúng vùng Việt Nam, 3 khách; danh sách không hiện tên hay số liên lạc; mở tên quá 5 khách
>   một lần phải ghi lý do, và mỗi lần mở đều được ghi lại.
>
> **Kiểm thử trọn vòng khác trên Dev (30/10):**
>
> - Một chuyến chạy trọn từ Yêu cầu → Báo giá → Đặt cọc → Đã đặt → Đang đi → **Hoàn tất**, có dịch vụ của nhà cung cấp
>   riêng của đại lý.
> - Tài khoản trợ lý của đại lý đọc 7 trang có tiền: **không thấy lãi / giá net / hoa hồng**; chủ đại lý vẫn thấy đủ.
> - **Sản phẩm Adventure Asia trong đề xuất, trọn vòng:** báo giá theo giá Booking thật → giữ chỗ → khách chấp nhận →
>   hệ thống tự tạo dòng dịch vụ AA với giá vốn đã khoá → khách đặt cọc (540 USD) → chuyến chuyển **Đã đặt** →
>   **Booking xác nhận đặt chỗ** cho cả bộ dịch vụ. Giữ chỗ hết hạn thì hệ thống từ chối và mời báo giá lại.
> - Tài khoản quản trị nội bộ của AA không vào được cổng của đại lý.
>
> Chưa thử: hoá đơn phí dịch vụ hoặc dòng nhập tay, huỷ hoá đơn, từ chối hoàn tiền, hoàn tiền vượt ngưỡng cần duyệt
> thêm; gửi mã ký qua email thật (trên Dev mã lấy từ chế độ thử) và câu hỏi bảo hiểm khi ký; xoá thật dữ liệu một khách,
> xuất toàn bộ dữ liệu đại lý; cảnh báo sự cố từ Adventure Asia trên trang chuyến (chưa thấy trên Dev vì chưa có sự cố
> nào).
>
> Ảnh theo thứ tự: (1) hoá đơn cọc vừa phát hành, (2) bản in hoá đơn, (3) hoá đơn sau khi trả đủ và hoàn 50 USD, (4)
> trang Payments lọc "Đã trả", (5) cổng của khách sau khi ký cho mình và ký thay cho trẻ, (6) trang chuyến "mọi khách đã
> ký", (7) bản ký đã niêm phong với dòng "niêm phong hợp lệ", (8) file xuất dữ liệu của một khách đã sẵn sàng, (9) bước
> kiểm tra trước khi xoá dữ liệu một khách, (10) lịch tháng 11 của đại lý.

**Ảnh đính kèm (theo thứ tự):**

1. `docs/audits/2026-10-30-S260-session-close/evidence/crm-hoa-don-da-phat-hanh.png` (= `04c-invoice-issued-1440.png`)
2. `docs/audits/2026-10-30-S260-session-close/evidence/crm-ban-in-hoa-don.png` (= `04e-invoice-document-open.png`)
3. `docs/audits/2026-10-30-S260-session-close/evidence/crm-da-tra-va-hoan-tien.png` (= `04j-refund-executed-1440.png`)
4. `docs/audits/2026-10-30-S260-session-close/evidence/crm-trang-payments.png` (= `04k-payments-paid-filter-1440.png`)
5. `docs/audits/2026-10-30-S260-evidence/05f-portal-lead-all-signed-1440.png` → đăng tên `crm-cong-khach-da-ky.png`
6. `docs/audits/2026-10-30-S260-evidence/05g-agreements-signed-1440.png` → `crm-moi-khach-da-ky.png`
7. `docs/audits/2026-10-30-S260-evidence/05h-sealed-envelope-1-1440.png` → `crm-ban-ky-niem-phong.png`
8. `docs/audits/2026-10-30-S260-evidence/06d-export-ready-1440.png` → `crm-xuat-du-lieu-khach.png`
9. `docs/audits/2026-10-30-S260-evidence/06h-erasure-dry-run-1440.png` → `crm-kiem-tra-truoc-khi-xoa.png`
10. `docs/audits/2026-10-30-S260-evidence/08c-calendar-nov-agency-1440-light.png` → `crm-lich-thang-11.png`

Ảnh 5–10 đã xem lại 30/10: không có mã issue nội bộ, không có account ID; tên khách là tên thử ("E2E … Proof",
"E2E S260 Minor") và mã định danh nội bộ của khách thử (ảnh 7) — chấp nhận được như ảnh 3. Ảnh 10 chụp lúc 22:0x, trước
bản chỉnh giờ trên lịch, nên giờ của các việc ngày 1/11 hiện theo giờ UTC (ví dụ "04:37 am"); muốn sạch thì bỏ ảnh 10
hoặc chụp lại sau bản chỉnh.

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Cài đặt thanh toán + hoá đơn | README S260 mục 4: `PUT settings/payment-methods/manual` 200; ảnh `04-settings-payments-*` |
| Nháp → phát hành INV-000001, bản in | `POST trips/{id}/invoices` 201, `issue` 200 số INV-000001; `GET invoices/{id}/document` 200 (ảnh `04c`, `04e`) |
| Trả 200 + 340 → Đã trả, lịch cọc đã trả, chuyến Đã đặt | `POST invoices/{id}/payments` 201 ×2; `due → paid`, `proposal → booked` (ảnh `04f`, `04g`) |
| Hoàn 50: chủ yêu cầu, thành viên khác duyệt, ghi đã hoàn | refund-requests 201 `proposed` → approve 200 (agent) → execute 200 `executed` (ảnh `04h`–`04j`) |
| Trang Payments | `GET invoices?status=paid` 200, refund-requests executed 1 dòng (ảnh `04k-*`) |
| Chặn "đã trả" thẳng trên khoản có hoá đơn | `POST schedule/{id}/mark-paid` 409 `invoice_issued_for_row` + thông báo trên UI (ảnh `04d`) |
| Code đã ship | Partner #130 + #131 (hoá đơn), #132 `8525a211` (thanh toán), crm-024 applied; `/crm/health/ready` crm-024 lúc chạy |
| Vòng đời → Hoàn tất, nhà cung cấp riêng, trợ lý không thấy lãi, quản trị không vào cổng | proof S258 (`2026-10-30-S258-session-close/evidence/20261029T170848Z-cm2-lifecycle.json`, …) |
| Sản phẩm AA trọn vòng tới Booking xác nhận; giữ chỗ hết hạn bị từ chối | S259 `20261030T043644Z-cm3-confirm.json` 16/16 PASS (Booking #155, Partner #128); S258 `20261029T171322Z-cm3-hold-expired.json` |
| Ký điện tử: link riêng mỗi khách, đọc + ký bằng mã | README S260 mục 5: `portal-access` 201 ×2; code 202 + session 200; ký 200 `signed` (ảnh `05c`, `05e`) — Partner #136 `021d68e6`, crm-025; chạy trên `7e9d8db0` (#138 chứa #136) |
| Trẻ không tự ký; khách chính ký thay với tư cách giám hộ | `sign` của trẻ 403 `guardian_signs` (ảnh `05b`); khách chính ký `signer_role: guardian` 200 (ảnh `05f`) |
| Sai mã bị từ chối + báo lần thử còn lại; tài liệu đổi thì không ký được | 422 `code_invalid` `attempts_left: 4` (ảnh `05d`); hash sửa → 409 `document_changed` (`data/05-esign-portal.json`) |
| Niêm phong, "mọi khách đã ký", nhật ký, mở bản niêm phong phải có lý do, báo hợp lệ | `GET agreements` 200 `all_signed: true` (ảnh `05g`); mở không lý do 422 `reason_required`; mở có lý do 200 ×2 `seal.verified: true` (ảnh `05h-1`, `05h-2`) |
| Ghi nhận chấp nhận điều khoản khi ký | 2 terms acceptances `source: envelope` (mục 5, dòng agreements) |
| Ghi yêu cầu, hạn 30 ngày | README mục 6: `POST data/requests` 201, nhận 30/10 hạn 29/11 (ảnh `06b`) — Partner #138 `7e9d8db0`, crm-026 |
| ZIP một khách 41 bản ghi JSON + CSV, mã kiểm tra, link dùng một lần, file khớp | export `ready 24/24` trong 5 s, 41 dòng (ảnh `06d`); tải 200, lần hai 403 `link_invalid`; SHA-256 bytes = checksum (ảnh `06e`, data `06-portability.json`) |
| Bước kiểm tra xoá: 7 bản ghi, chờ xác nhận; khách còn chuyến bị từ chối; không xoá thật | dry run 200 (ảnh `06h`); khách đang có chuyến 409 `traveler_on_trip` (ảnh `06f`); "Erase this client now" không bấm, khách vẫn 200 (ảnh `06g`) |
| Lịch tháng: các loại mục, của mình / cả đại lý, ví dụ ngày | README mục 8c: `GET calendar` 200, số mục UI = API tháng 10 + 11 (ảnh `08c-*`): hạn ký 8/11, payment_due 9/11 ×2 + 19/11, departure 29/11 — Partner #140 `3718242a`, crm-027 |
| Giờ theo giờ địa phương của đại lý (chỉnh tối 30/10) | phát hiện F4 (giờ UTC) → Partner #142 `3a116512` merged + deploy (theo orchestrator). **Chưa chụp lại / chưa kiểm live sau bản sửa** — câu viết "chỉnh lại", không viết "đã kiểm" |
| Link lịch: chỉ ngày + mã chuyến, không tên / số tiền, dừng là ngừng ngay; đúng định dạng chuẩn; chưa thử app lịch thật | mục 8d: feed 201; fetch 200 `text/calendar`, 62 VEVENT, không tên / số tiền / email / phone; revoke 200 → fetch 404 `feed_not_found` (ảnh `08d-*`); không thử subscribe trên Google / Outlook / Apple |
| Trang Travelling now chỉ trạng thái trống; dữ liệu phía sau: VN 3 khách, không tên / liên lạc; >5 khách cần lý do; mỗi lần mở ghi lại | mục 8a: ảnh `08a-*` trống; `duty/travelling?days=31` 200 VN `traveller_count 3`, không key tên / liên lạc; reveal 1 khách 200 + audit event `reveal`; 6 khách không lý do 422 `reason_required` (kiểm qua API, không qua giao diện — câu viết "kiểm riêng") |
| Cảnh báo sự cố chưa thấy | mục 8b: `incidents: []` mọi câu trả lời; trang chuyến không có banner (ảnh `08b`) — đưa vào dòng "Chưa thử" |

Không đưa vào (cố ý):

- Câu báo khi từ chối xoá khách ("huỷ hoặc xoá chuyến trước", nhưng huỷ chuyến chưa đủ — phát hiện F2): việc kỹ thuật,
  tự xử lý (Partner #141). Nháp chỉ viết "khách còn chuyến chưa kết thúc thì hệ thống từ chối xoá".
- Các quan sát nhỏ: nhật ký ký chưa hiện lần mở bản niêm phong, dòng "signing code refused (code_invalid)" còn mã thô,
  "1 signatures pending" sai số ít — việc kỹ thuật.
- Lỗi hiển thị nhỏ trên trang chuyến (hydration #418) và câu hỏi hạn hoá đơn cọc = ngày trong lịch thanh toán: việc
  kỹ thuật, tự xử lý.
- Ảnh `04j` có chú thích dữ liệu thử dạng "E2E-S260-…" (mã phiên, không phải mã issue) — chấp nhận được; nếu tech lead
  muốn sạch hơn thì bỏ ảnh 3.

---

## 3. PR-24 — TripPlanner — Lên lịch trình trên bản đồ (khách B2C)

**Vì sao:** video giới thiệu TripPlanner làm cho chị Thư (S260, link Drive qua Jira theo memory `thu-links-via-jira`);
nháp S258 về tốc độ trang điểm đến chưa đăng (comment 29/10 15:27 còn báo Bhutan ~3,9 giây, chưa có số sau sửa).

**Nháp (dán nguyên văn):**

> @thule Cập nhật TripPlanner ngày 30/10 (tiếp theo cập nhật 29/10):
>
> **Video giới thiệu TripPlanner**, bản tiếng Anh (3 phút 57 giây) và tiếng Việt (4 phút 14 giây), có phụ đề:
>
> - Quay trên trang TripPlanner đang chạy, với tour thật trong kho của Adventure Asia: trang chủ và ô tìm chuyến, trang
>   một nước (Bhutan), trang tour (lịch trình từng ngày, bản đồ lộ trình, bao gồm / không bao gồm), nút "Customise this
>   trip", trình lên lịch trên bản đồ (lọc hoạt động, gợi ý điểm đến tiếp theo, thêm đêm, ngày tự do, đổi thứ tự ngày),
>   gửi chuyến cho tư vấn viên, và bản trên điện thoại.
> - Phần cuối nói giá trị cho Adventure Asia: mỗi chuyến khách gửi đến đội tư vấn thành một yêu cầu mới kèm sẵn lịch
>   trình; tour luôn khớp với kho tour của công ty.
> - Form gửi tư vấn trong video chỉ điền dữ liệu mẫu và dừng trước khi gửi; video không dùng phần AI.
> - Tải gói video: <LINK DRIVE> (gồm 2 video MP4, giọng đọc MP3, phụ đề SRT/VTT, lời đọc theo thời gian; mở bằng
>   trình phát video bất kỳ trên máy tính hoặc điện thoại).
>
> **Trang điểm đến đạt mục tiêu tốc độ trên điện thoại** (dưới 2,5 giây; đo trên bản đang chạy, Lighthouse điện thoại,
> trung vị 5 lần, 30/10):
>
> | Trang | Trước | Sau |
> |---|---|---|
> | Danh sách điểm đến | 2,46 giây | 1,38 giây |
> | Trang một nước (Bhutan) | 3,95 giây | 2,49 giây |
>
> Trang Bhutan còn dao động 1,7–2,8 giây giữa các lần đo. Cách làm: ảnh nằm dưới màn hình đầu chỉ tải khi khách cuộn
> tới; ảnh đầu trang dùng đúng kích cỡ.
>
> **Trình lên lịch trên bản đồ:** đã sửa để khi khách chọn một nước, bản đồ di chuyển tới nước đó. Bản sửa đã lên trang
> đang chạy và qua kiểm thử tự động; chưa kiểm lại bằng tay trên trình duyệt.

**Ảnh đính kèm:** không (video gửi qua link Drive; số tốc độ ở dạng bảng).

**Placeholder:** `<LINK DRIVE>` giữ nguyên trong bản lưu này. Gói `TripPlanner-intro_20261030.zip` (73 MB) đã ở thư
mục Google Drive AdventureAsia; link chia sẻ chỉ nằm trong tin nhắn cuối phiên, thay vào nháp lúc đăng. Link Drive
không ghi vào repo (repo gốc public tới tháng 11).

link: see session message

Ghi chú cho tech lead: đoạn "Trình lên lịch trên bản đồ" chỉ có bằng chứng test, chưa kiểm live; video giới thiệu quay
trước bản sửa. Muốn chặt hơn thì bỏ đoạn đó, báo ở lần sau khi đã kiểm trên trình duyệt.

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Video EN 3:57, VI 4:14, phụ đề, nội dung 23 cảnh | `.tmp-session/S260/uat/out/intro/storyboard.md` (EN 3:56.9, VI 4:13.9; 23 cảnh), checklist S260: 23 cảnh PASS; zip 14 file (README, 2 MP4, 2 MP3, SRT/VTT, script) |
| Quay trên trang đang chạy, tour thật, form không gửi, không AI | storyboard (đoạn đầu): production `aa-tripplanner.vercel.app`, 1440×900 + 390×844, form không submit, không gọi AI trả phí |
| Giọng đọc chạy trên máy, không tốn phí | README trong zip: Kokoro (EN), VieNeu-TTS v3 Turbo giọng nữ miền Nam (VI), Apache-2.0 |
| Tốc độ 2,46 → 1,38 và 3,95 → 2,49 | `2026-10-30-S258-session-close/evidence/lighthouse-prod-after.txt` (5 lần, 30/10 ~00:35, sau TripPlanner #188); dải Bhutan [2.78, 2.49, 1.82, 1.74, 2.78] |
| Bản đồ planner di chuyển tới nước được chọn; đã lên trang; test tự động; chưa kiểm tay | TripPlanner #197 (lỗi thật: bản đồ chưa sẵn sàng khi chọn nước) merged + deploy theo orchestrator; kiểm bằng test, **không** có bằng chứng live — câu viết rõ "chưa kiểm lại bằng tay" |

Không đưa vào: chi tiết kỹ thuật của lỗi bản đồ planner;
mã ẩn điểm nghi sai trên trang khách (đã merge, chưa bật — xem PR-22).

---

## 4. PR-22 — CIS — Nội dung & pipeline (Master content, đăng bài, ảnh)

**Vì sao:** nháp S258 về ảnh bìa (302 → 444 / 892 tour) chưa đăng; cập nhật tiến độ định vị lại địa điểm (comment
29/10 báo 77,7 %, kiểm giữa chừng 30/10 có số mới) và trạng thái AI viết nội dung (vẫn tạm dừng).

**Nháp (dán nguyên văn):**

> @thule Cập nhật CIS ngày 30/10 (tiếp theo cập nhật 29/10):
>
> - **Ảnh bìa tour cho đại lý:** ghép ảnh với điểm đến tốt hơn, thêm 326 ảnh được gắn đúng điểm đến (tổng 1.919 ảnh),
>   336 điểm đến có ảnh bìa. Tour trong Marketplace có ảnh bìa: **302 → 444 / 892 tour**. 448 tour còn thiếu chủ yếu
>   thuộc India (215), Japan (79), Laos (45), Philippines (44), Thailand (43): các nước này chưa có thư mục ảnh nguồn,
>   cần bổ sung ảnh chứ không phải sửa code.
> - **Định vị lại địa điểm (vẫn đang chạy, dự kiến xong 31/10):** kiểm mẫu giữa chừng chiều 30/10, tỷ lệ địa điểm đúng
>   78,4 % (trước đợt chạy 75,4 %), dự kiến khoảng 80 % khi chạy xong, vẫn dưới mục tiêu 90 %. Trang khách đã có sẵn
>   cách ẩn những điểm bị nghi sai, nhưng chưa bật: sẽ kiểm lại số sau khi đợt chạy xong rồi mới quyết.
> - **AI viết nội dung vẫn tạm dừng:** kiểm lại ngày 30/10, mọi model sinh văn bản vẫn bị chặn. Đã gửi yêu cầu gỡ chặn
>   tới AWS; AWS báo cần 3–5 ngày làm việc. Trong lúc chờ, hệ thống báo trạng thái này trên trang quản trị và dừng các
>   việc AI ngay thay vì thử lại.

**Ảnh đính kèm:** không (không có ảnh chụp cho các mục này; số liệu từ đợt chạy và kiểm mẫu).

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| 326 ảnh, tổng 1.919, 336 điểm đến, 302 → 444 / 892, 448 còn thiếu theo nước | S258 apply (log S258, nháp `2026-10-30-S258-session-close/jira-drafts.md`) — số 29–30/10, không đo lại trong S260 |
| 78,4 % (trước 75,4 %), dự kiến ~80 %, mục tiêu 90 % | checklist S260 mục 11: audit giữa chừng 15:25 +07 (08:25Z), flag-strat; chuỗi relocate còn 1 job queued tới 31/10 |
| Đã có cách ẩn, chưa bật | CIS #1185 / #1178, Booking #160, TripPlanner #195 merged + deploy (api :929 / worker :495); báo cáo hide_flagged chạy live 2.017 dòng, confirm trả 409 đúng (chuỗi còn mở) — chưa ẩn dòng nào |
| AI vẫn bị chặn | probe 30/10 15:14 và 15:30: mọi model sinh văn bản FAIL; case AWS mở 16:30, AWS báo 3–5 ngày làm việc |

Ghi chú cho tech lead (chọn trước khi đăng):

- Câu "Đã gửi yêu cầu gỡ chặn tới AWS; AWS báo cần 3–5 ngày làm việc" chỉ nói mốc thời gian, không nói tài khoản /
  reseller / chi phí. Muốn gọn hơn thì bỏ câu đó, giữ "AI viết nội dung vẫn tạm dừng".
- Bỏ dòng "tài khoản OpenAI dự phòng đã hết credit" của nháp S259 (dính chi phí / nhà cung cấp — để tech lead xử lý
  ngoài Jira). Muốn giữ thì thêm lại.
- Không báo: Writing memory (mẫu viết ghim, KPI tuần, hàng bất đồng, nhãn chấm tay — đã merge, chưa thử thật được vì AI
  đang dừng); bộ nút giao diện chung trong admin CIS (nội bộ, không đổi tính năng); 6 báo cáo vận hành mới và cổng LLM
  (ngân sách / phạm vi dữ liệu / chi phí) — việc kỹ thuật, memory `jira-no-tech-decisions`.

---

## Không soạn nháp (và lý do)

| Issue | Lý do |
|---|---|
| PR-20 / báo cáo tuần | Kỳ 2 (PR-28, 20–26/10) tạo 25/10. Kỳ 3 (27/10–02/11) chỉ soạn khi đủ một tuần (từ 02/11, memory `platform-report-weekly`) |
| PR-27 Nền tảng | Việc kỹ thuật (tài khoản AWS, LLM gateway, báo cáo vận hành, CI), tech lead tự quyết |
| PR-23 Portal tenant | S260 không có tính năng portal mới ship (chỉ đồng bộ bộ giao diện, không đổi gì thấy được). Video UAT Portal là nội bộ, không gửi |
| PR-19 (story CRM), PR-12 (story Booking), PR-11 (Visual map planner) | Tiến độ CRM / Booking / TripPlanner đi vào epic PR-26 / PR-25 / PR-24 như các lần trước |
| PR-13, PR-15, PR-16, PR-9, PR-7, PR-1, PR-14, PR-17, PR-18 | Không có việc S260 ship liên quan |
| KAN-*, CON-* | Việc marketing / nội dung của đội chị Thư; S260 không có việc liên quan (KAN-90 chi phí DataForSEO đã báo ở PR-22 ngày 29/10) |
| Kế hoạch video UAT | Nội bộ, không gửi (theo yêu cầu) |

## Placeholder còn mở

- `<LINK DRIVE>` ở PR-24 (gói video giới thiệu TripPlanner): gói đã lên thư mục Drive; link nằm trong tin nhắn cuối
  phiên S260 (link: see session message), không ghi vào repo vì repo gốc còn public tới tháng 11. Thay vào nháp lúc
  đăng.
- PR-26: dòng ký điện tử đã điền theo proof live PASS (bằng chứng mục 5), không còn placeholder.

## Kết quả đăng

**Chưa đăng.** Chờ tech lead duyệt nguyên văn trong tin nhắn cuối phiên S260. Sau khi đăng: ghi comment id / link vào
đây và vào log phiên.
