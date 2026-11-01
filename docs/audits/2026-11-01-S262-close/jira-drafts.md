> **Trạng thái: CHƯA ĐĂNG — dời sang S263 theo quyết định của Nghiệp (01/11/2026).** Ảnh đã cắt/che nằm ở `.tmp-session/S262/jira-img/` (không đưa vào repo public); S263 đăng từ đó.

# S262 — nháp Jira (gồm nháp S261 chuyển sang), chờ Nghiệp duyệt

Soạn 01/11/2026 ~04:30 +07 (Claude Code, phiên S262). **Chưa đăng gì, chưa sửa, chưa đổi trạng thái issue nào.**
Đăng theo skill `aa-jira-update`: `contentFormat: html`, mention thật
`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`, bảng markdown đổi
sang bảng HTML khi đăng, ảnh upload từng file (`uploadAttachmentToJiraIssue`) rồi nhúng bằng `inlineFileId` đúng thứ tự.

## Đã rà trên Jira (đọc, 01/11 ~04:15 +07)

- `project in (PR, KAN, CON) AND statusCategory != Done`: 99+ issue. Có cập nhật gần đây chỉ các epic PR-22…PR-27 (comment
  cuối 29–30/10). PR-28 (báo cáo kỳ 2) không có gì mới. Các issue KAN/CON là việc nội dung/marketing của chị Thư và đội,
  không liên quan việc phiên này → không soạn.
- Comment mới nhất mỗi epic (để không lặp): PR-26 #10564 (30/10: hoá đơn/hoàn tiền, ký điện tử, xuất/xoá dữ liệu chạy
  thử, lịch, "Chưa thử: … xoá thật dữ liệu một khách … cảnh báo sự cố từ Adventure Asia"); PR-25 #10563 (30/10: lưới khách
  sạn, menu dòng, giao diện thống nhất); PR-24 #10565 (30/10: video giới thiệu, tốc độ trang điểm đến); PR-23 #10533
  (29/10: Facts, CTA, nhãn giá), câu hỏi điều khoản AI A/B/C ở #10508 (25/10) **chưa có trả lời**; PR-22 #10566 (30/10:
  ảnh bìa, định vị 78,4 %, AI viết nội dung tạm dừng); PR-27 #10532 (29/10).

## Danh sách nháp

| # | Issue | Nội dung | Ảnh |
|---|---|---|---|
| 1 | PR-26 (comment A) | CRM: 7 phần ship 31/10 (S261) | 7 |
| 2 | PR-26 (comment B) | CRM: 6 phần ship 31/10–01/11 (S262) | 10 |
| 3 | PR-25 | Booking: đề xuất báo khi CIS có nội dung mới hơn | 2 |
| 4 | PR-24 | TripPlanner: chống bot, giới hạn AI, trang Dev không lập chỉ mục | 1 |
| 5 | PR-23 | Portal: trần chi phí AI theo đối tác; điều khoản AI (đề xuất, chờ chị chọn) | 1 |
| 6 | PR-20 | Báo cáo nền tảng kỳ 3 (27/10–02/11) — **chỉ đăng từ thứ Hai 02/11** | 0 |
| 7 | PR-22 | Định vị địa điểm: kết quả cuối 01/11, pin không chắc chắn đã ẩn | 0 |

Không soạn: PR-27 (lý do ở cuối file). PR-22 soạn bổ sung ở mục 7 (01/11, sau audit cuối).

## Kiểm trước khi đăng (ô Nghiệp chốt)

- [ ] **PR-26 B, AA-957 (hoa hồng + huỷ chuyến):** đang có 2 lane chỉnh giao diện/chức năng sau phần kiểm live
  (critic thấy nhiều lỗi UI). Nếu lane merge trước khi đăng thì ảnh vẫn đúng chức năng, nhưng giao diện có thể khác chút.
- [ ] **Ảnh trang khách ngoại tuyến** đã che địa chỉ Gmail cá nhân của Nghiệp (email liên hệ của đại lý thử). Dùng bản đã
  che `.tmp-session/S262/jira-img/crm-trang-khach-ngoai-tuyen.png`, không dùng bản gốc trong `docs/audits`.
- [ ] Ảnh AA-971, báo cáo, onboarding là ảnh cả trang rất dài → dùng bản đã cắt trong `.tmp-session/S262/jira-img/`.
- [ ] **PR-20 kỳ 3:** đăng từ 02/11 (một tuần một báo cáo). Tạo story mới "Báo cáo nền tảng kỳ 3 (27/10–02/11/2026)" dưới
  PR-20 **chỉ khi Nghiệp nói tạo**; không thì đăng làm comment trên PR-20.
- [ ] Dòng "kiểm soát chi phí AI" trong PR-20, mục ngân sách AI ở PR-23 và mục "Trần chi phí AI theo ngày" (5 USD/ngày) ở
  PR-24: nếu Nghiệp coi là việc kỹ thuật / chi phí nội bộ thì bỏ (memory `jira-no-tech-decisions`, skill luật 7); đã viết
  theo kết quả sản phẩm, không nói kiến trúc.
- [ ] (Rà S262) **Ảnh PR-23 `08b-tenant-budget-editor`** để lộ số chi phí nội bộ của đối tác thử (LLM cost 14,82 USD, Plan
  revenue 799 USD, LLM margin 784,18 USD) sau lớp mờ → cắt chỉ lấy khung "AI budget" bên phải trước khi đăng (luật 7).
- [ ] (Rà S262) **Ảnh PR-26 B số 5 (`B2-01-cancel-dialog-dry-run`)** có chữ sai thì ("You cancelled this trip…" trước khi
  bấm), dòng "—, paid 540.00 USD", tên khách thử chứa "AA961" và khoá thô `stage3_due_t21`; **ảnh số 6 (`B2-06`)** hiện cả
  "CANCELLED" lẫn "CONFIRMED BY AA" và mã thô `cancelled_by_agency`. Chờ lane chỉnh giao diện huỷ chuyến merge rồi chụp lại,
  hoặc đăng kèm (đã ghi "đang sửa tiếp" trong nội dung).
- [ ] (Rà S262) Ảnh PR-25 có tên khách thử "ZZ S239 test Customer AA-679" (chứa mã Linear trong dữ liệu thử). Chấp nhận
  hoặc cắt phần tiêu đề hồ sơ.

---

## 1. PR-26 — CRM cho đại lý — comment A (việc ship 31/10, S261)

**Vì sao issue này:** PR-26 là epic CRM; mọi cập nhật CRM trước đều đăng ở đây (#10510, #10519, #10564). Comment 30/10 có
mục "Chưa thử: … xoá thật dữ liệu một khách … cảnh báo sự cố từ Adventure Asia trên trang chuyến" → hai việc này nay đã
thử. Nháp S261 chuyển sang (`docs/audits/2026-10-31-S261-close/jira-drafts.md`).

**Nội dung (sẵn để đăng):**

@thule Cập nhật CRM cho đại lý ngày 31/10 (Dev, đại lý thử "Lữ hành Sen Vàng", dữ liệu giả, tiếp theo cập nhật 30/10):

| Phần | Đã thử trên Dev | Chưa thử |
|---|---|---|
| Trang riêng cho từng khách trong chuyến | 16/16 bước đạt | gửi mã đăng nhập qua email thật |
| Bắt đầu dùng + nhập dữ liệu khách | nhập 3 dòng, nhập lại cùng file: 0 bản trùng | file Excel rất lớn |
| Báo cáo cho đại lý | 14 phần của trang hiện đủ, xuất CSV | ô thống kê chung của AA khi có đủ đại lý |
| Thư: câu trả lời mẫu, ghi chú nội bộ, nháp tự lưu | đạt | Microsoft 365, SMTP |
| Ký điện tử: các bước chặt hơn | đạt cả 3 phần | bản PDF có chữ ký số |
| Cảnh báo sự cố từ Adventure Asia | bật → thấy → gỡ, đạt | bấm báo sự cố từ giao diện Booking |
| Xoá thật dữ liệu một khách | đạt, có biên nhận | khách có giấy tờ đã ký cần giữ lại |

- **Trang riêng cho từng khách:** mỗi người trong chuyến có link riêng; mở link thì hỏi "Bạn là ai?", mỗi người thấy trang
  của mình (chuyến bay, giấy tờ được chia sẻ, quét hộ chiếu, mời bạn đồng hành). Thử với 3 người (khách chính, một người lớn
  có email, một trẻ không có email): link của trẻ gửi mã về địa chỉ của khách chính; giấy tờ chưa chia sẻ không hiện; giấy
  tờ của đại lý khác không mở được.
- **Bắt đầu dùng và nhập dữ liệu:** trang "bắt đầu" có danh sách việc cần làm (kết nối hộp thư, mời đội, gắn form hỏi
  khách). Nhập khách từ CSV có chạy thử trước: file thiếu cột tên bị từ chối và không nhập gì; file 3 dòng có 2 dòng trùng
  email → tạo 2 khách, nhận ra 1 trùng; nhập lại cùng file → 0 khách mới. Có trang gộp khách trùng và trang Kết nối.
- **Báo cáo:** phễu khách (yêu cầu → báo giá → đặt → hoàn tất), doanh thu và lãi, tiền còn phải thu, theo từng người trong
  đội, xuất CSV. Số tiền còn phải thu khớp đúng các hoá đơn đang mở (1.080 USD trên dữ liệu thử). Tài khoản trợ lý không thấy
  phần lãi; đại lý khác không thấy dữ liệu của Sen Vàng. Phần thống kê chung của AA (gộp ẩn danh theo quý) chỉ công bố ô có
  từ 10 khách và 3 đại lý trở lên; trên Dev mới có 4 đại lý thử nên mọi ô đều được giấu, như thiết kế.
- **Thư cho khách:** lưu câu trả lời mẫu và chèn vào thư; ghi chú nội bộ trên chuyến (khách không thấy); thư đang soạn tự
  lưu sau 3 giây, tải lại trang vẫn còn; bỏ nháp thì mất hẳn.
- **Ký điện tử:** nhập mã đã hết hạn thì bị từ chối; khi đại lý đổi điều khoản đặt tour sau khi khách đã chấp nhận, hệ
  thống không cho ghi nhận tiền cọc cho tới khi khách đọc và chấp nhận lại bản mới; khách ký waiver và ký "không mua bảo
  hiểm du lịch", cả hai bản đều được niêm phong.
- **Cảnh báo sự cố từ Adventure Asia:** khi AA ghi nhận sự cố trên một ngày khởi hành, chuyến của đại lý hiện băng cảnh báo,
  có một việc khẩn cho người phụ trách, và trang "Travelling now" báo số sự cố. Gỡ sự cố thì băng chuyển sang "đã xử lý".
  Trên Dev, sự cố được tạo bằng kịch bản kiểm phía Booking (tài khoản nhân viên thử của Booking chỉ có quyền xem), chưa
  bấm từ giao diện Booking. Chỉ đúng một đại lý có khách trên ngày khởi hành đó nhận cảnh báo.
- **Xoá dữ liệu theo yêu cầu của khách (lần này xoá thật):** trên một khách thử không có chuyến, bước kiểm tra báo sẽ xoá
  2 bản ghi; xoá thật → có biên nhận (số bản ghi đã xoá, bản sao lưu tự hết hạn ngày 30/11, các nơi ngoài AA mà đại lý cần
  tự xoá); kiểm lại thì khách không còn. File xuất dữ liệu cũ của khách đó bị huỷ theo. Trên Dev, việc xoá thật chỉ bật tạm
  cho lần thử này rồi tắt lại.

Ảnh theo thứ tự: (1) "Bạn là ai?" trên trang khách (điện thoại), (2) trang bắt đầu dùng, (3) báo cáo của chủ đại lý,
(4) thư nháp được khôi phục sau khi tải lại trang (điện thoại), (5) bản ký waiver và "không mua bảo hiểm" trên trang
chuyến, (6) băng cảnh báo sự cố trên chuyến, (7) biên nhận xoá dữ liệu.

**Ảnh (đúng thứ tự, tên file khi upload):**

| # | Tên khi upload | File |
|---|---|---|
| 1 | crm-trang-khach-ban-la-ai.png | `docs/audits/2026-10-31-S261-evidence/AA-953/02-portal-picker-who-are-you-390-light.png` |
| 2 | crm-bat-dau-dung.png | `.tmp-session/S262/jira-img/crm-bat-dau-onboarding-1440.png` (cắt từ `AA-962/01-onboarding-1440-light.png`) |
| 3 | crm-bao-cao.png | `.tmp-session/S262/jira-img/crm-bao-cao-chu-dai-ly-1440.png` (cắt từ `AA-966/01-reports-owner-light-1440.png`) |
| 4 | crm-thu-nhap-khoi-phuc.png | `docs/audits/2026-10-31-S261-evidence/AA-945/04b-after-reload-draft-restored-390.png` |
| 5 | crm-ky-waiver-bao-hiem.png | `.tmp-session/S262/jira-img/crm-ky-waiver-bao-hiem.png` (cắt từ `AA-955/07b-agreements-panel-element-1440.png`) |
| 6 | — | no screenshot — no live incident now |
| 7 | crm-bien-nhan-xoa-du-lieu.png | `docs/audits/2026-10-31-S261-evidence/AA-967/06-erasure-done-receipt-element-1440.png` |

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Trang từng khách 16/16 (README bảng 17 dòng: 1–16 PASS, 17 = console), link trẻ gửi mã về khách chính, giấy tờ đại lý khác 404 | `docs/audits/2026-10-31-S261-evidence/AA-953/README.md` (bảng kết quả, "Not tested": mail thật); Partner #145 |
| Nhập CSV: thiếu cột 422, 3 dòng → 2 tạo + 1 trùng, nhập lại 0 | `AA-962/README.md` dòng 5–8; chưa thử: xlsx lớn (dòng 9) |
| Báo cáo 14 phần, 1.080 USD, trợ lý không thấy lãi, đại lý khác cách ly, ô insight giấu (4 đại lý) | `AA-966/README.md` dòng 2–4, mục assistant/second agency |
| Câu trả lời mẫu, ghi chú, nháp tự lưu 3 s, khôi phục sau tải lại | `AA-945/README.md` bước 1–6; chưa thử M365/SMTP |
| Mã hết hạn từ chối, chấp nhận lại điều khoản (409 → 200), waiver + từ chối bảo hiểm niêm phong | `AA-955/README.md`; chưa thử PAdES, đường "có bảo hiểm" |
| Sự cố: banner, task khẩn, Travelling, gỡ → "Cleared", đúng 1 đại lý; flag từ UI Booking bị 403 (E2E chỉ xem), tạo bằng run-script | `AA-961/README.md` mục "Finished by the orchestrator" (run 41177461668 / 41177912654) |
| Xoá thật: dry run 2 bản ghi, receipt, backup 30/11, `subject_gone`, export huỷ, cờ dry-run bật lại | `AA-967/README.md` mục cuối; log S261 dòng AA-967 (Infra #547 → #548) |

---

## 2. PR-26 — CRM cho đại lý — comment B (việc ship 31/10–01/11, S262)

**Vì sao issue này:** cùng epic CRM; phần hoá đơn S261 chỉ báo "một phần" (còn link hết hạn, tiền đến muộn, nhắc nợ) nay
đã thử xong; thêm 5 phần mới ship trong S262.

**Nội dung (sẵn để đăng):**

@thule Cập nhật CRM cho đại lý ngày 01/11 (Dev, đại lý thử "Lữ hành Sen Vàng", dữ liệu giả, tiếp theo cập nhật trên):

| Phần | Đã thử trên Dev | Chưa thử |
|---|---|---|
| Thanh toán: link hết hạn, tiền đến muộn, nhắc nợ | đạt cả 3 | thanh toán thẻ qua cổng thanh toán thật |
| Hoa hồng từ nhà cung cấp | đạt (dự kiến → đã đòi → đã nhận, xoá sổ) | hoa hồng quá hạn; hoa hồng khi huỷ chuyến |
| Huỷ chuyến một thao tác | đạt cả chuyến có và không có dịch vụ AA | khi hệ thống Booking đang ngừng; chuyến có hoá đơn chưa trả |
| Bàn giao thông tin khách cho đội điều hành của AA | đạt phía đại lý | màn hình cho nhân viên AA |
| Trang khách dùng được khi mất mạng | đạt trên trình duyệt máy tính | trên điện thoại thật |
| Cho AA hỗ trợ xem dữ liệu (có thời hạn) | đạt phía đại lý | màn hình cho nhân viên AA |
| Trợ lý AI soạn trả lời | trang cài đặt đạt, chế độ thử | model AI thật |

- **Thanh toán, phần còn lại (31/10):**
  - Link thanh toán hết hạn khi chỗ giữ của AA hết hạn: trang của khách không còn thông tin chuyển khoản và báo "link đã
    hết hạn, hỏi đại lý link mới"; đại lý thấy lời nhắc báo giá lại trước khi khách trả. (Trên dữ liệu thử, hạn giữ chỗ
    được dời sớm để không phải chờ 48 giờ.)
  - Tiền cọc đến muộn sau khi chỗ đã nhả: khách chấp nhận lại điều khoản → đại lý ghi đủ 540 USD → Booking giữ chỗ lại →
    hoá đơn chuyển "Đã trả".
  - Nhắc nợ: hoá đơn quá hạn tự sinh thông báo trên chuông và một việc "hoá đơn quá hạn" cho người phụ trách chuyến (chạy
    tự động lúc 0 giờ ngày 01/11, kiểm lại lúc 01:12).
- **Hoa hồng (trang Commissions mới):** khi đại lý xác nhận một dịch vụ của nhà cung cấp riêng có hoa hồng, CRM tự ghi
  khoản hoa hồng dự kiến, hạn nhận = ngày kết thúc dịch vụ + số ngày đã đặt cho nhà cung cấp (mặc định 30). Đã thử: 3 dịch
  vụ → 3 khoản, hạn 25/11 (10 ngày sau dịch vụ); đánh dấu đã đòi kèm số chứng từ; ghi đã nhận 46 EUR → quy ra 50 USD theo
  tỷ giá ngày tiền về; xoá sổ khoản 15 USD với lý do "quá nhỏ"; tổng theo từng chuyến đúng. Tài khoản trợ lý không vào được
  trang này và không thấy hoa hồng trên chuyến.
- **Huỷ chuyến bằng một thao tác:** bảng xác nhận liệt kê trước mọi việc sẽ xảy ra (tin nhắn đang chờ gửi bị huỷ, việc
  đang mở được đóng, link của khách ngừng hoạt động, dịch vụ AA bị huỷ kèm phí, khoản cần hoàn, thông tin đã gửi đội điều
  hành AA được rút lại), phải gõ CANCEL để xác nhận.
  - Chuyến không có dịch vụ AA: huỷ ngay, đại lý chỉnh số tiền hoàn (thử 500/540 USD), yêu cầu hoàn tiền chờ duyệt, hoá đơn
    đã trả được giữ nguyên.
  - Chuyến có tour của AA: bảng hiện phí huỷ do Booking tính (118,91 USD = 75 %, huỷ trước 13 ngày); sau khi xác nhận, chuyến
    chờ AA xác nhận huỷ rồi mới chuyển "Đã huỷ" (lần thử Booking trả lời sau khoảng 1,3 giây); phí huỷ hiện trên tab
    Bookings; khoản đã trả mà không có hoá đơn sinh việc "hoàn tiền thủ công".
  - Chưa thử: huỷ khi Booking đang ngừng (chuyến phải ở trạng thái "chờ AA xác nhận"); huỷ chuyến có hoá đơn chưa trả. Đang
    sửa tiếp: chuyến đã huỷ vẫn còn hiện khoản thu còn lại (nút tạo hoá đơn, ghi đã trả) và một số chữ trên giao diện.
- **Bàn giao cho đội điều hành của AA:** khi AA xác nhận tour trên một chuyến, đội điều hành AA nhận đúng phần tối thiểu để
  chạy tour (tên, nhóm tuổi, ăn uống, đi lại, chuyến bay, lựa chọn bảo hiểm); không có số điện thoại, email, hộ chiếu hay
  ghi chú. Trang chuyến có khung "AA ground operations": còn thiếu gì, mỗi lần AA mở xem đều ghi lại, ngày tự xoá (90 ngày
  sau chuyến), nút rút lại. Thiếu thông tin trước 21 ngày khởi hành thì nhắc người phụ trách (đã chạy thật trên chuyến thử);
  huỷ chuyến thì thông tin tự rút. Phía AA mới có phần hệ thống; màn hình cho nhân viên điều hành AA làm tiếp.
- **Trang khách dùng được khi mất mạng:** khách cài trang chuyến lên máy như một ứng dụng; khi mất mạng vẫn mở được bản lưu
  (lịch trình và liên hệ đại lý); giấy tờ, ký và thanh toán chỉ mở khi có mạng; đăng xuất là xoá bản lưu trên máy. Đã chạy
  trong bộ kiểm tự động trên Dev (trình duyệt máy tính); chuyến thử không có lịch trình theo ngày nên ảnh chỉ thấy phần liên
  hệ. Chưa thử cài trên điện thoại thật.
- **Cho AA hỗ trợ xem dữ liệu:** chủ đại lý cho phép nhân viên hỗ trợ AA xem dữ liệu (chỉ xem) trong 1–7 ngày; suốt thời
  gian đó có băng báo trên mọi trang, kèm link nhật ký truy cập; bấm "End now" là dừng ngay. Đã thử: cấp 1 ngày → băng hiện
  → dừng. Có thêm quyền khẩn cấp (15–60 phút, phải ghi lý do, không thấy tên khách, chủ đại lý nhận email, AA nhận cảnh
  báo): đã có trong hệ thống, chưa thử thật vì màn hình cho nhân viên AA chưa xong.
- **Trợ lý AI soạn trả lời (Cài đặt → AI assistant):** chủ đại lý bật/tắt, đặt ngân sách AI hằng tháng (trong mức của
  gói), xem đã dùng bao nhiêu; dùng hết 100 % thì AI dừng tới tháng sau, không tính thêm tiền. Thông tin cá nhân (tên, email,
  số điện thoại, hộ chiếu) được thay bằng mã trước khi tới AI. Trên Dev đang ở chế độ thử: bản nháp do model thử trả về,
  chưa gọi model AI thật, không tốn tiền.

Ảnh theo thứ tự: (1) trang khách khi link thanh toán đã hết hạn, (2) hoá đơn cọc đã trả sau khi tiền đến muộn, (3) việc
"Follow up an overdue invoice" trên trang chuyến, (4) trang Commissions sau khi nhận 46 EUR, (5) bảng xác nhận huỷ chuyến có tour AA,
(6) phí huỷ của AA trên tab Bookings, (7) khung "AA ground operations" trên trang chuyến, (8) trang khách khi mất mạng,
(9) băng "AA support" sau khi chủ đại lý cho phép, (10) Cài đặt → AI assistant.

**Ảnh (đúng thứ tự):**

| # | Tên khi upload | File |
|---|---|---|
| 1 | crm-link-thanh-toan-het-han.png | `docs/audits/2026-10-31-S262-evidence/AA-952/20c-client-pay-box-expired-1440.png` |
| 2 | crm-coc-den-muon-da-tra.png | `.tmp-session/S262/jira-img/crm-coc-den-muon-da-tra.png` (từ `AA-952/22-invoices-card-after-late-money-1440.png`) |
| 3 | crm-hoa-don-qua-han.png | `.tmp-session/S262/jira-img/crm-hoa-don-qua-han-r2.png` (chụp lại khung Tasks của chuyến A `87f9e5ee`, 01/11; thay `AA-952/10-trip-A-overdue-task-1440.png`) |
| 4 | crm-hoa-hong-da-nhan.png | `.tmp-session/S262/jira-img/crm-hoa-hong-da-nhan-r3.png` (chụp lại 01/11 trên giao diện sau #169, khung trang Commissions, lọc Received) |
| 5 | crm-huy-chuyen-xac-nhan.png | `.tmp-session/S262/jira-img/crm-huy-chuyen-xac-nhan-r3.png` (chụp lại 01/11 trên giao diện sau #169, bảng xác nhận trước khi bấm) |
| 6 | crm-phi-huy-aa.png | `.tmp-session/S262/jira-img/crm-phi-huy-aa-r3.png` (chụp lại 01/11 trên giao diện sau #169, bảng Bookings sau khi huỷ) |
| 7 | crm-ban-giao-dieu-hanh-aa.png | `docs/audits/2026-10-31-S262-evidence/AA-956/02-ops-panel-after-copy-fix-1440-light.png` |
| 8 | crm-trang-khach-ngoai-tuyen.png | `.tmp-session/S262/jira-img/crm-trang-khach-ngoai-tuyen.png` (**đã che email cá nhân**) |
| 9 | crm-ho-tro-aa-da-cap.png | `.tmp-session/S262/jira-img/crm-ho-tro-aa-da-cap-1440.png` (cắt từ `AA-971/40-support-access-granted-1440.png`) |
| 10 | crm-cai-dat-ai.png | `docs/audits/2026-10-31-S262-evidence/AA-964/30-settings-ai-1440-light.png` |

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Link hết hạn: không có thông tin chuyển khoản, 410 `pay_link_expired` ×2, đại lý thấy "re-quote"; hạn giữ chỗ dời sớm trên dữ liệu thử | checklist S262 18:51 + 20:00; ảnh `AA-952/20*`; spec S261 `expired.spec.ts` |
| Tiền đến muộn: reaccept 200 → cọc 201 `rehold_pending` → Booking reheld → paid | checklist S262 20:00; ảnh `22-…` |
| Nhắc nợ: chuông + task `invoice_overdue`; chuông `last_at` 17:00:04Z (00:00 +07 01/11), kiểm 18:12Z (01:12 +07) | checklist S262 01:13; `.tmp-session/S262/aa952_rem2.log`; ảnh `10-…` (`10b` hiện "No tasks" → không dùng) |
| Hoa hồng A1–A4: 3 dòng, hạn 25/11 (+10 ngày), claim SV-INV-957-001, nhận 46 EUR = 50 USD tỷ giá 28/10, xoá sổ 15 USD too_small, tổng theo trip, trợ lý 403 | `.tmp-session/S262/aa957_live.json` (A1…A4 PASS) |
| Huỷ B1: dry run, hoàn 500/540, refund proposed, hoá đơn giữ paid | `aa957_live.json` B1 |
| Huỷ B2: phí 118,91 USD 75 %/13 ngày, pending → done 1,3 s, phí trên tab Bookings, `cancel_refund_review`, ops release rút | `aa957_live.json` B2-*; badge "pending" chưa thấy trên UI (BLOCKED), Booking-down chưa thử (critic) |
| Bàn giao ops: dữ liệu tối thiểu, không phone/email/hộ chiếu, đếm lượt mở, tự xoá 90 ngày, T-21 nhắc thật, rút khi huỷ | Partner #160 body; checklist S262 01:12 (alarm T-21 bắn thật), 01:25; ảnh `AA-956/02-*`; màn hình nhân viên AA = AA-1019 chưa xong |
| Trang ngoại tuyến: E2E 41230648205 bước 6b PASS, CDP installability rỗng, SW scope `/c/t`; đăng xuất xoá cache | checklist S262 01:50, 02:00; Partner #161 body; ảnh `AA-954/lifecycle-06b-offline.png` |
| Hỗ trợ AA: cấp 1 ngày → banner + thẻ → thu hồi; break-glass chưa chạy live phía nhân viên | checklist S262 00:00; Partner #157 body; ảnh `AA-971/40-*` |
| AI assistant: settings 200, chế độ thử (stub), trần 2 USD, 100 % dừng | checklist S262 23:08; Partner #153 body; ảnh `AA-964/30-*` |

---

## 3. PR-25 — Booking

**Vì sao issue này:** epic Booking; phần mới là đề xuất trong Booking theo kịp nội dung CIS sau lần viết lại. Comment cuối
#10563 (30/10) không nói phần này.

**Nội dung (sẵn để đăng):**

@thule Cập nhật Booking ngày 31/10 (tiếp theo cập nhật 30/10):

- **Đề xuất báo khi CIS có nội dung tour mới hơn:** khi một tour đã được viết lại trong CIS sau lúc nhân viên dựng đề xuất,
  trình soạn đề xuất hiện khung "CIS has newer text for this tour" (số mục khác và ngày CIS cập nhật), từng mục có dòng
  "CIS now: …" với tên mới. Nút "Refresh from CIS" chép tên mới vào bản nháp; chỉ khi bấm Save mới lưu. Trang xem trước
  cũng báo và chỉ đường quay lại trình soạn.
- Đã kiểm trên Dev 31/10 với hồ sơ chuyến thử TC-000008 (tour Bhutan, 2 phiên bản đề xuất): mỗi phiên bản báo 6/7 mục có
  tên mới; bấm Refresh → "6 title(s) copied from CIS. Save to keep them.", không ghi gì vào hệ thống; tải lại trang khi chưa
  Save thì đề xuất giữ nguyên như cũ. Không bấm Save trong lần kiểm này. Đề xuất đến từ CRM của đại lý hiện tên tour đầy đủ.

Ảnh theo thứ tự: (1) trình soạn đề xuất với khung báo và các dòng "CIS now", (2) sau khi bấm Refresh (chưa lưu).

**Ảnh:**

| # | Tên khi upload | File |
|---|---|---|
| 1 | booking-cis-co-noi-dung-moi.png | `.tmp-session/S262/jira-img/booking-cis-co-noi-dung-moi.png` (từ `AA-1013/tc8-v2-builder-1440-light.png`) |
| 2 | booking-sau-refresh-chua-luu.png | `.tmp-session/S262/jira-img/booking-sau-refresh-chua-luu.png` (từ `AA-1013/tc8-v2-builder-after-refresh-unsaved-1440-light.png`) |

**Câu → bằng chứng:** `.tmp-session/S262/aa1013/run-log.txt` + `check.json` (16:16–16:18Z 31/10: TC-000008 V1/V2 changed=6
of 7, notice text, refresh toast, `writesDuringRefresh: []`, `apiUnchanged: true`, reload notice back; TC-000026 tour line);
Booking #163 merged 16fbed68; checklist S262 23:35.

---

## 4. PR-24 — TripPlanner

**Vì sao issue này:** epic TripPlanner; ba thay đổi khách nhìn thấy hoặc ảnh hưởng chi phí AI, kèm dòng ghi chú SEO cho
trang Dev (quyết định TL-24 ghi "báo business owner một dòng").

**Nội dung (sẵn để đăng):**

@thule Cập nhật TripPlanner ngày 31/10 (tiếp theo cập nhật 30/10):

- **Chặn bot ở phần tìm kiếm và lời dẫn từng ngày:** hai phần có thể gọi AI chỉ chạy cho trình duyệt thật (dùng gói kiểm
  bot miễn phí của Vercel). Đã kiểm 31/10: trình duyệt thật tìm kiếm bình thường; gọi tự động từ dòng lệnh hoặc trình
  duyệt chạy ngầm bị từ chối. Các trang khác (danh sách nước, tour) không bị ảnh hưởng.
- **Giới hạn dùng AI cho mỗi khách:** tìm kiếm tối đa 30 lượt mỗi phút cho mỗi địa chỉ mạng, lời dẫn từng ngày tối đa 10
  lượt mỗi giờ cho mỗi phiên (khách đăng nhập được gấp đôi); chỉ đếm lượt thật sự gọi AI. Vượt giới hạn thì trang hiện một
  dòng nhắc thử lại sau. Đã thử 31/10: 35 lượt tìm kiếm trong một phút → 30 lượt trả kết quả, 5 lượt bị từ chối đúng giới
  hạn. Lời dẫn: cả 892 tour đều có nội dung ngày của Adventure Asia nên trang dùng thẳng nội dung đó, không gọi AI và không
  bị tính vào giới hạn.
- **Trần chi phí AI theo ngày** cho TripPlanner: 5 USD/ngày, cảnh báo khi tới 80 %. Khi AI không chạy được (vượt trần hoặc
  nhà cung cấp lỗi), tìm kiếm chuyển sang tìm theo từ khoá và lời dẫn dùng nội dung có sẵn, có một dòng thông báo nhẹ. Phần
  này đã có trong hệ thống, chưa thử thật trường hợp vượt trần.
- **Trang TripPlanner bản Dev** (aa-tripplanner.vercel.app) giờ báo công cụ tìm kiếm không lập chỉ mục và có dòng "Preview
  site" ở cuối trang, để khách không nhầm là trang chính thức. Như vậy trang Dev không được tính điểm SEO; trang chính thức
  sau go-live mới được lập chỉ mục. Đã kiểm trên trang đang chạy 01/11.

Ảnh: (1) tìm kiếm trên trình duyệt thật sau khi bật chặn bot.

**Ảnh:**

| # | Tên khi upload | File |
|---|---|---|
| 1 | tripplanner-tim-kiem-trinh-duyet-that.png | `docs/audits/2026-10-31-S262-evidence/AA-1015/headed-search-200-1440.png` |

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Chặn bot: curl search 403 `bot_check_failed`, countries 200, headless 403, headed Chromium 200; BotID Basic miễn phí | checklist S262 22:35; TP #201 body |
| 30/phút/IP, 10/giờ/phiên, đăng nhập gấp đôi; burst 35 → 30×200 + 5×429 | TP #199 body; checklist S262 21:25 |
| 892 tour có nội dung ngày AA → không gọi model | checklist S262 22:55; `.tmp-session/S262/aa1015-narrate/` |
| Trần 5 USD/ngày, 80 % cảnh báo; degrade khi AI không chạy | Terraform Apply run 41204275322 (`TP_DAILY_SPEND_CAP_USD=5.0`); TP #199, #198 body; vượt trần chưa thử live |
| Dev noindex + "Preview site" | curl 01/11 ~04:25 +07: `x-robots-tag: noindex, nofollow`, footer "Preview site: a test version …"; TP #200 |

---

## 5. PR-23 — Portal tenant

**Vì sao issue này:** câu hỏi điều khoản AI (A/B/C) đăng ở đây ngày 25/10 (#10508) chưa có trả lời; có thay đổi mới ở
trang điều khoản. Thêm trần chi phí AI theo đối tác (AA quản lý chi phí của tenant). Viết dạng đề xuất nhẹ nhàng, có nhờ
luật sư hay không là chị quyết (memory `tech-focus-business-to-thu`).

**Nội dung (sẵn để đăng):**

@thule Cập nhật Portal ngày 31/10 (tiếp theo cập nhật 29/10):

- **Trần chi phí AI cho từng đối tác:** trong admin CIS (Tenants → Cost), AA đặt ngân sách AI hằng tháng cho một đối tác,
  mức báo và mức phải duyệt. Đối tác không thấy phần này. Đã thử trên Dev với một đối tác thử: đặt trần thấp → lượt viết
  kế tiếp của đối tác dừng chờ AA duyệt, không tốn tiền, admin nhận thông báo trên chuông; sau đó trả trần về như cũ.
- **Trang điều khoản và quyền riêng tư của portal đã ghi rõ các nhà cung cấp AI** (bản nháp v0.3, 31/10): Claude của
  Anthropic (qua Amazon Bedrock) viết nội dung; các model của OpenAI (qua Amazon Bedrock) xem lại, chấm điểm và kiểm tra;
  khi Amazon Bedrock không dùng được thì có thể gọi thẳng Anthropic hoặc OpenAI, có trần chi tiêu; có thêm link tới chính
  sách sử dụng của OpenAI. Trang vẫn ghi "Draft — pending legal review": https://portal.lumiguides.it.com/terms

**Điều khoản sử dụng AI cho đối tác (nhắc lại câu hỏi ngày 25/10, khi tiện chị xem):** chính sách sử dụng mới của
Anthropic có hiệu lực từ 12/11/2026. Hiện chưa có đối tác thật nên chưa cần thông báo cho ai; mỗi đối tác chấp nhận điều
khoản khi bắt đầu dùng.

- **A.** Dùng điều khoản như bản nháp.
- **B.** Nhờ luật sư xem trước; trong lúc chờ, trang vẫn để bản nháp.
- **C.** Dùng ngay như A, nhờ luật sư xem trước khi có đối tác trả tiền đầu tiên.

Đề xuất: A hoặc C. Thêm một điểm mới: CRM cho đại lý đã có trợ lý AI soạn trả lời (đang ở chế độ thử, chưa gọi model
thật). Đề xuất đưa cùng điều khoản này vào điều khoản của đại lý trước khi bật model AI thật cho CRM, theo cùng lựa chọn
A/B/C của chị. Có nhờ luật sư hay không là chị quyết.

Ảnh: (1) chỉnh trần chi phí AI của một đối tác thử trong admin.

**Ảnh:**

| # | Tên khi upload | File |
|---|---|---|
| 1 | portal-tran-chi-phi-ai-doi-tac.png | `.tmp-session/S262/jira-img/portal-tran-chi-phi-ai-doi-tac.png` (cắt khung "AI budget" từ `AA-804-c4/08b-tenant-budget-editor-1440-light.png`) |

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Ngân sách AI theo tenant (staff only), tenant không thấy | ảnh `08b-…` (chữ "Staff only: the tenant never sees it"); `AA-804-c4/findings.md` dòng "Tenant 360 › Cost: PASS" |
| Thử: lượt T-stage của tenant thử dừng chờ duyệt 0 USD + chuông `spend_budget_alert`, dòng ngân sách tạm đã xoá | checklist S262 01:00 (AA-1016 Done-with-scope) |
| Trang terms v0.3 nêu nhà cung cấp + link OpenAI | curl 01/11 ~04:25 +07 `portal.lumiguides.it.com/terms`: "Draft v0.3", "OpenAI models, also through Amazon Bedrock …", "OpenAI Usage Policies"; Partner #151; root #401 (`docs/legal/readiness-packet*.md`, `tenant-terms-ai-clause-draft.md`) |
| Hiệu lực 12/11/2026 | `docs/legal/tenant-terms-ai-clause-draft.md`; đọc lại chính sách lần cuối 24/10 (chưa đọc lại trong S262 → không nói "đã kiểm lại") |
| Điều khoản phải vào điều khoản đại lý trước khi bật Claude cho CRM | `tenant-terms-ai-clause-draft.md` bảng §(c) "Gate … before any Claude-backed provider is switched on for a CRM agency" |
| Chưa có trả lời A/B/C | `listJiraIssueComments PR-23` 01/11: không có comment của chị Thư sau #10508 |

---

## 6. PR-20 — Báo cáo nền tảng kỳ 3 (27/10–02/11/2026) — đăng từ thứ Hai 02/11

**Vì sao issue này:** báo cáo tuần (memory `platform-report-weekly`); kỳ 2 là PR-28. Bản đầu kỳ 3 soạn ở S253 không đăng
(một tuần một báo cáo). Kỳ 3 kết thúc 02/11. **Tạo story mới dưới PR-20 chỉ khi Nghiệp nói tạo**; không thì đăng làm
comment trên PR-20. Bảng chỉ lấy số đã báo trên các epic 27–30/10 và các nháp ở trên.

**Nội dung (mô tả story / comment):**

@thule Báo cáo nền tảng kỳ 3 (27/10–02/11/2026). Mọi số đo trên Dev với dữ liệu thử, còn thay đổi. Chi tiết ở comment trên
từng epic.

| App | Đã xong trong kỳ | Tiếp theo |
|---|---|---|
| CIS (PR-22) | Thẻ địa điểm đạt ngưỡng chất lượng (dữ kiện sai 2,0 %); ảnh bìa tour cho đại lý 302 → 444/892 tour; tọa độ địa điểm chỉ lấy từ dịch vụ bản đồ, tỷ lệ đúng 75,4 % → 78,4 % (kiểm giữa chừng 30/10); trang Cost Operations và Docs trong admin; kiểm câu khẳng định thương hiệu trong bản viết lại của đối tác | Chốt số định vị địa điểm sau đợt chạy cuối; bật lại AI viết nội dung khi có lại |
| Portal (PR-23) | Portal chạy trên máy chủ AA, một bản, đăng nhập 2 lớp (bỏ khoá API); Marketplace có bộ lọc và ảnh bìa; trang Facts của đối tác; trần chi phí AI theo đối tác; trang điều khoản ghi rõ nhà cung cấp AI | Điều khoản AI cho đối tác (chờ chị chọn A/B/C) |
| TripPlanner (PR-24) | Video giới thiệu EN + VI; trang chủ và trang tour 1,5–1,6 giây trên điện thoại, trang điểm đến dưới 2,5 giây; chặn bot và giới hạn AI cho mỗi khách; trang Dev không lập chỉ mục | — |
| Booking (PR-25) | Phủ các màn hình theo Figma; danh sách trip plan nhanh khoảng 4 lần; tải chứng từ; lưới khách sạn; đề xuất báo khi CIS có nội dung mới hơn | — |
| CRM (PR-26) | Hoá đơn, thanh toán, hoàn tiền, nhắc nợ; ký điện tử; xuất và xoá dữ liệu khách; lịch; trang riêng cho từng khách (dùng được khi mất mạng); nhập dữ liệu; báo cáo; cảnh báo sự cố từ AA; hoa hồng; huỷ chuyến một thao tác; bàn giao cho đội điều hành AA; cho AA hỗ trợ xem dữ liệu; trợ lý AI (chế độ thử) | Màn hình cho nhân viên AA (hỗ trợ, điều hành); chỉnh giao diện huỷ chuyến và hoa hồng; Microsoft 365 |
| Nền tảng (PR-27) | Cảnh báo bảo mật thử bằng thay đổi thật (12/12 lần có cảnh báo); kiểm soát chi phí AI: mọi lượt gọi AI trả phí được ghi chi phí, có trần theo nhà cung cấp, đối tác và đại lý, xem trong admin | Báo cáo chi phí AWS tháng 8–10 theo từng app |

**Nghiệm thu (UAT):** đã có bộ 27 kịch bản nghiệm thu cho các app. Chạy thử 31/10 trên Dev ở chế độ chỉ đọc: 23 kịch bản,
đạt cả 23 sau khi sửa 4 kịch bản viết sai (lỗi ở kịch bản, không phải ở sản phẩm); 4 kịch bản có ghi dữ liệu chưa chạy.
Quay xong video mẫu đầu tiên (TripPlanner, lời đọc EN + VI); vòng quay chính thức làm khi giao diện ổn định và AI viết nội
dung có lại.

**Chi phí:** báo cáo chi phí AWS tháng 8, 9, 10 theo từng app đang làm (tháng 10 vừa chốt), sẽ có trong kỳ 4.

**Rủi ro:** AI viết nội dung vẫn tạm dừng (kiểm tối 31/10: tài khoản AI vẫn bị chặn), nên chưa có nội dung mới do AI viết;
các phần đã ship không phụ thuộc AI vẫn chạy. Định vị địa điểm chưa đạt mục tiêu 90 %. Hệ thống vẫn ở môi trường thử
nghiệm với dữ liệu thử.

**Ảnh:** không (ảnh ở comment từng epic).

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| CIS: 2,0 %, 302 → 444/892, 75,4 → 78,4 %, Cost Operations, Docs, câu khẳng định thương hiệu | Jira PR-22 #10513 (27/10), #10515 (28/10), #10521 (29/10), #10566 (30/10) |
| Portal: máy chủ AA, khoá API tắt, Marketplace, Facts | Jira PR-23 #10509 (27/10), #10516 (28/10), #10528, #10533 (29/10); trần AI + terms: nháp §5 |
| TripPlanner: video, 1,54/1,57 s, điểm đến < 2,5 s | Jira PR-24 #10526 (29/10), #10565 (30/10); chặn bot/giới hạn/noindex: nháp §4 |
| Booking: Figma, nhanh ~4 lần, chứng từ, lưới khách sạn | Jira PR-25 #10518 (28/10), #10527 (29/10), #10563 (30/10); nháp §3 |
| CRM | Jira PR-26 #10564 (30/10); nháp §1, §2 |
| Nền tảng: 12/12 cảnh báo (4+6+1+1) | Jira PR-27 #10529 (29/10) |
| Kiểm soát chi phí AI | AA-642/AA-804/AA-1016/AA-1017/AA-1018 Done(-with-scope) trong checklist S262; ảnh `AA-804-c4/` (không đăng). Dòng tuỳ Nghiệp bỏ |
| UAT 27 kịch bản, 23 chỉ đọc, 19 + 4 sửa, 4 ghi chưa chạy, video TP-02 EN + VI | `docs/audits/2026-10-31-S262-uat-dry-run/run-1-results.md`, `run-2-rerun-4-results.md`, `record-TP-02-result.json`; checklist S262 00:05–00:20, 02:40 (root #415, #416) |
| Chi phí AWS T8–T10 chưa xong | checklist S262 mục 18 (AA-896) chưa tick |
| AI vẫn bị chặn tối 31/10 | checklist S262 "Ràng buộc" + 00:55 (chuông `llm_circuit_open` acc3); Jira PR-22 #10566 đã báo tạm dừng |
| Định vị < 90 % | `docs/audits/2026-10-31-S261-aa997-report/README.md` (78,8 % ±4,0 sau chuỗi v2, FAIL); audit cuối 01/11 chưa chạy |

---

## 7. PR-22 — CIS nội dung & pipeline: định vị địa điểm trên bản đồ (kết quả cuối 01/11)

**Vì sao issue này:** epic CIS; comment #10566 (30/10) đã báo định vị 78,4 % và hẹn báo lại sau đợt kiểm cuối. Đợt kiểm
lại dữ liệu cũ đã chạy xong 01/11 và pin không chắc chắn đã được ẩn (tech lead đã duyệt), nên báo kết quả. Theo quyết
định của tech lead: báo business owner con số phủ bản đồ. Không đưa phần kỹ thuật (luật nhận, nhà cung cấp, chi phí chi tiết).

**Vị trí đăng:** comment trên PR-22 (mention bằng mention node, bảng đổi sang HTML khi đăng).

**Nội dung (sẵn để đăng):**

@thule Cập nhật định vị địa điểm trên bản đồ ngày 01/11 (tiếp theo cập nhật 30/10):

- **Địa điểm mới:** từ nay toạ độ chỉ lấy từ dịch vụ tra bản đồ, không để AI tự đoán toạ độ, nên các địa điểm mới không
  còn bị ghim theo toạ độ AI đoán.
- **Dữ liệu cũ:** đợt kiểm lại toàn bộ địa điểm cũ đã chạy xong sáng 01/11, trên gói miễn phí.
- **Ẩn pin không chắc chắn:** khoảng 2.500 địa điểm mà dịch vụ tra bản đồ không xác nhận được vị trí đã được ẩn pin thay vì
  hiện một điểm có thể sai; địa điểm không bị xoá và pin tự hiện lại khi được xác nhận.

| Chỉ số (đo 01/11, trên mẫu 600 địa điểm đã chấm tay) | Số |
|---|---|
| Pin khách nhìn thấy trên bản đồ đặt đúng chỗ | ≈ 88 % |
| Tỉ lệ địa điểm vẫn còn hiện pin | ≈ 51 % |
| Toàn bộ dữ liệu cũ, tính cả pin đã ẩn (30/10 báo 78,4 %) | ≈ 80 % |

- **Sau này:** nếu thấy việc thiếu pin làm ảnh hưởng trải nghiệm khách, bên kỹ thuật sẽ xem xét bổ sung cách định vị
  thêm (có thể tốn phí) để hiện lại nhiều pin hơn. Hiện chưa cần làm gì thêm.

**Ảnh:** không có.

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Địa điểm mới chỉ lấy toạ độ từ dịch vụ tra bản đồ | báo cáo `docs/audits/2026-10-31-S261-aa997-report/README.md` §4.6 (guard "Toạ độ chỉ từ geocoder", CIS #1092) |
| Đợt kiểm lại xong 01/11, miễn phí | dòng `JOB` `b1e780e8` `ok`, `remaining 0`, xong 01/11 00:30Z; `J chain_sums` `cost_usd 0.0` (`.tmp-session/S262/aa997/audit-out.txt`) |
| Khoảng 2.500 địa điểm ẩn pin | báo cáo hide `f54cdf77`: 2.517 dòng (1.187 đang gắn tour); confirm `4919a61f`: `hidden 2517`, `changed_since_report 0` (`hide-report-out.txt`, `hide-confirm-out.txt`) |
| Không xoá, tự hiện lại khi xác nhận | báo cáo AA-997 §4.7 (ẩn = đổi trạng thái, có unhide; "Tự hiện khi geocoder xác nhận", CIS #1178) |
| ≈ 88 % pin đúng, ≈ 51 % còn pin | `audit-after-hide.txt` 01:22Z: `served_now` 88,0 % ±4,5, `coverage` 50,8 % |
| ≈ 80 % toàn bộ dữ liệu cũ | `audit-after-hide.txt` 01:22Z: `GATE flag-strat 79,6 %` ±4,0 (S260 30/10: 78,4 %) |
| Bổ sung cách định vị có thể tốn phí chỉ khi cần | quyết định TL-25, `docs/audits/2026-10-31-S262-tl-decisions/README.md` |

**Kiểm trước khi đăng:**

- [ ] Số "khách nhìn thấy" đo trên tập địa điểm đang gắn tour (kể cả tour chưa live), không phải từ màn hình app. Chưa chụp
  ảnh bản đồ trên app sau khi ẩn; nếu Nghiệp muốn kèm ảnh thì chụp trước khi đăng.
- [ ] Dòng "≈ 80 %" có thể bỏ nếu Nghiệp thấy hai số đầu là đủ (giữ để nối với số 78,4 % đã báo 30/10).

---

## Không soạn (và vì sao)

- **PR-22 (CIS):** đã soạn ở mục 7 sau audit cuối 01/11. Trạng thái AI tạm dừng vẫn để ở mục Rủi ro của PR-20.
- **PR-27 (Nền tảng):** cổng AI v2, ADR 0018, AWS Organizations/SCP/Identity Center, alarm CloudWatch, vá IAM, đường
  Anthropic/OpenAI API dự phòng, probe hằng ngày, các quyết định TL: việc kỹ thuật của tech lead (memory
  `jira-no-tech-decisions`) → không comment. Chỉ một dòng kết quả "kiểm soát chi phí AI" trong PR-20 (tuỳ Nghiệp bỏ).
- **Video review CRM (AA-1014), video UAT TP-02:** chưa có link Drive đã kiểm → chưa đưa link. Khi có link thì thêm vào
  comment PR-26 / PR-20.
- **Trang báo cáo cho business owner (BO-1, 4, 5, 6, 7, 8, 9, 13 của review kiến trúc S261):** chưa làm trong S262 → không có
  link. Không có trang/artifact nào khác làm cho chị Thư trong phiên này.
- **KAN-20, KAN-90, các issue KAN/CON khác:** không có việc mới liên quan.
- **Dọn dữ liệu, CI, freshness relink, schema, lỗi đã tự xử lý trong phiên:** nội bộ, không đưa (skill luật 7).

## Kết quả đăng

Chưa đăng (chờ Nghiệp duyệt). Sau khi đăng: ghi comment id / link từng issue vào đây và vào log phiên.
