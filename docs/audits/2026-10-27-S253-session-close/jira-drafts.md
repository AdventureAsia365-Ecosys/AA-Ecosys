# S253 — draft Jira cho chị Thư (gồm việc dồn từ S252)

Trạng thái: **NHÁP, CHƯA ĐĂNG.** Chờ Nghiệp duyệt một lần (skill `aa-jira-update`, memory `batch-drafts-at-session-end`).
Soạn 27/10/2026. Nguồn: log S252, `docs/audits/2026-10-27-S252-session-close/state-snapshot.md`, các thư mục audit S252/S253,
checklist `.tmp-session/S253-checklist.md`, comment Linear ngày 26–27/10 (đọc lại khi soạn).

Đã đọc comment Jira gần nhất trên PR-22…PR-28 (mới nhất đều 25/10 tối). Không nhắc lại những gì đã đăng 25/10:
CRM đề xuất → chấp nhận → cọc → dòng tour AA (báo giá, giữ chỗ, trả chỗ) đã báo trên PR-26 ngày 25/10, nên bỏ khỏi draft.

Cách đăng (khi Nghiệp duyệt): `contentFormat: html`; `@thule` đổi thành
`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`; bảng markdown đổi sang
`<table>`; ảnh upload bằng `uploadAttachmentToJiraIssue` rồi nhúng qua `inlineFileId` theo đúng thứ tự (tên file tiếng
Việt không dấu như cột "Tên khi upload"). Không mở đầu "Dạ chị", không "ạ" (memory `jira-draft-tone`).

## Lưu ý cho Nghiệp trước khi duyệt

1. **Báo cáo tuần kỳ 3 chưa có story.** PR-20 hiện chỉ có kỳ 1 (PR-21) và kỳ 2 (PR-28). Skill cấm tự tạo issue Jira, nên
   mục 7 cần Nghiệp nói "tạo" (story con của PR-20, tiêu đề như dưới). Nếu không muốn tạo: đăng nội dung đó làm comment
   trên PR-20.
2. **Cập nhật tối 27/10:** Sri Lanka "Day 12–15" và thẻ địa điểm vòng 3 đã ship, đã đưa vào PR-24 và PR-22. Thêm
   các mục mới: PR-25 hoá đơn và thanh toán; PR-24 trang chủ mới; PR-27 deploy không chờ job và màu nút admin.
3. **Ảnh nằm trong `.tmp-session/` (gitignored)**: còn trên máy, không lên repo. Ảnh Gmail (PR-26) có địa chỉ Gmail cá
   nhân của Nghiệp — ổn trên Jira, đừng chép vào repo gốc (đang public).
4. **Thiếu ảnh:** chưa có ảnh "sau khi sửa" cho bản đồ một điểm (TripPlanner); không có ảnh cho phần dọn dữ liệu và thẻ
   địa điểm (việc dữ liệu, không có màn hình riêng). Ảnh nhập lịch sử thư có thanh menu bên trái bị đè giữa trang (lỗi
   chụp toàn trang, không phải lỗi giao diện) — có thể chụp lại.
5. **Chi phí trong báo cáo tuần:** 54,93 USD tính từ 00:00 UTC 25/10; khung này có thể trùng phần cuối lần viết lại đã
   báo ở kỳ 2 (59,34 USD). Nếu muốn tránh trùng, bỏ dòng tổng và chỉ giữ các khoản có tên.

---

## 1. PR-23 — Portal tenant

**Vì sao issue này:** việc chuyển portal về máy chủ AA và đăng nhập một lần là phần "Gộp với portal hiện tại" đã báo trong
thiết kế (PR-19, 21/10) và đã nhắc trong cập nhật portal 25/10 ("công cụ nội dung đã chuyển về cùng ứng dụng với CRM ở
phía sau"). Đây là bước người dùng thấy được.

**Nội dung đăng:**

> @thule Cập nhật portal cho đại lý (Dev, 27/10/2026):
>
> - **Portal chạy trên máy chủ của AA:** địa chỉ giữ nguyên portal.lumiguides.it.com; giờ một nơi phục vụ cả công cụ nội
>   dung (Content studio) lẫn CRM. Địa chỉ cũ trên Vercel tự chuyển sang địa chỉ này.
> - **Đăng nhập một lần:** đại lý đăng nhập bằng tài khoản riêng và ứng dụng xác thực trên điện thoại (mã 6 số) là vào
>   được cả studio lẫn CRM, không cần khoá API như trước.
> - **Đã thử trọn vòng trên Dev** với một người dùng thử, vai "chỉ xem", ở tenant thử: thư mời tới hộp thư → người được
>   mời tự đặt mật khẩu và cài ứng dụng xác thực → studio mở ra → vai "chỉ xem" không sửa được gì → đăng xuất ở studio là
>   thoát luôn cả CRM. Chủ đại lý thử đăng nhập vào CRM qua địa chỉ mới: đạt.
> - Khi thử, phát hiện nút đăng xuất của studio chưa thoát hẳn (lần vào sau tự đăng nhập lại); đã sửa và kiểm lại trên bản
>   đang chạy.
> - **Diễn tập quay lại bản cũ:** chuyển về Vercel mất 3 phút 28 giây, chuyển lại máy chủ AA mất 3 phút 11 giây; sau mỗi
>   lần, bộ kiểm giao diện tự động đạt 59/59.
>
> Bước tiếp: từ 03/11 tắt cách đăng nhập cũ bằng khoá API và gỡ bản portal trên Vercel.
>
> Ảnh: (1) thư mời, (2) studio mở sau khi nhận lời mời, (3) trang chính của studio, (4) nội dung trên điện thoại nền tối,
> (5) trang đã đăng xuất.

**Ảnh đính kèm (theo thứ tự):**

| # | File | Tên khi upload |
|---|---|---|
| 1 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa979-cutover/shots/p2-01-join-invite-1440-light.png` | `1-thu-moi.png` |
| 2 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa979-cutover/shots/p2-02-join-studio-activated-1440-light.png` | `2-studio-sau-khi-nhan-loi-moi.png` |
| 3 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa979-cutover/shots/p2-03-studio-dashboard-1440-light.png` | `3-trang-chinh-studio.png` |
| 4 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa979-cutover/shots/p2-04-studio-content-390-dark.png` | `4-noi-dung-dien-thoai-nen-toi.png` |
| 5 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa979-cutover/shots/p2-05-signed-out-1440-light.png` | `5-da-dang-xuat.png` |

**Câu → bằng chứng:** cutover, 301, smoke 59/59, diễn tập 3′28″/3′11″, lỗi CSP đăng xuất: `docs/audits/2026-10-27-S253-aa979-cutover/README.md`;
luồng mời → MFA → studio → viewer → đăng xuất: cùng file mục §2.4b/§3/§6a + `phase2-run.json`; đăng nhập chủ đại lý: §2.4;
dọn từ 03/11: mục "Còn lại" §4.5.

---

## 2. PR-26 — CRM cho đại lý

**Vì sao issue này:** comment 25/10 trên PR-26 ghi "Chưa thử: kết nối Gmail / Microsoft 365". Gmail nay đã thử trọn vòng;
nhập lịch sử thư là tính năng mới.

**Nội dung đăng:**

> @thule Cập nhật CRM cho đại lý (Dev, 26/10/2026):
>
> **Gửi thư bằng Gmail của đại lý: đã thử trọn vòng trên Dev** với một hộp Gmail thử, một đại lý thử và một khách thử:
> - Kết nối Gmail trong Cài đặt → "Gửi thư thử" nằm trong thư mục Đã gửi của Gmail.
> - Thư gửi khách từ trang chuyến đi ra bằng địa chỉ Gmail của đại lý; bấm huỷ ngay sau khi gửi thì thư không đi.
> - Khách trả lời → thư hiện đúng trên chuyến, kể cả khi khách chỉ bấm "Trả lời" bình thường.
> - Thư gửi tới một địa chỉ nhận không tồn tại bị bỏ, không lẫn vào hộp thư của đại lý.
> - Gmail bị ngắt kết nối → thư mới được giữ lại, Cài đặt báo đỏ; kết nối lại thì thư đang giữ tự gửi đi.
>
> **Nhập lịch sử thư cũ** (file .mbox xuất từ Google Takeout hoặc Thunderbird, hoặc file CSV), đã thử trên Dev:
> - File thử 2 thư: nhập đủ 2; nhập lại cùng file không tạo bản trùng.
> - File 12 MB, 621 thư: chạy xong trong khoảng 8 giây (thư đã có trong CRM được bỏ qua).
> - File trên 25 MB bị từ chối, có thông báo rõ.
>
> Đăng nhập CRM giờ dùng chung với công cụ nội dung (xem cập nhật Portal, PR-23).
>
> Chưa thử: Microsoft 365 (cần đăng ký ứng dụng Microsoft cho AA), kết nối bằng SMTP, hộp thư chung của đại lý.
>
> Ảnh: (1) Cài đặt hộp thư sau khi gửi thư thử, (2) thư gửi và thư khách trả lời trên trang chuyến, (3) thư được giữ khi
> Gmail mất kết nối, (4) nhập lịch sử thư.

**Ảnh đính kèm (theo thứ tự):**

| # | File | Tên khi upload |
|---|---|---|
| 1 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/aa945/3-test-sent.png` | `1-gmail-gui-thu-thu.png` |
| 2 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/aa945/evidence/06-r2-header-reply-on-trip.png` | `2-thu-tren-trang-chuyen.png` |
| 3 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/aa945/evidence/10-settings-held-count.png` | `3-thu-duoc-giu-khi-mat-ket-noi.png` |
| 4 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/aa945/import/import-1440-light.png` | `4-nhap-lich-su-thu.png` |

**Câu → bằng chứng:** Gmail send-as live + "Send a test" → Sent: log S252 mục "Đã làm sớm hơn" + `.tmp-session/s252/aa945/test-result.txt`;
gửi A, huỷ B, R1 theo mã chuyến, R2 theo header trả lời, U bị bỏ, giữ thư khi ngắt / gửi lại khi nối lại:
`.tmp-session/s252/aa945/evidence/notes.txt` (26/10, lượt 2 lúc 13:36–13:43Z: R2 `reply_header` trên chuyến); nhập lịch sử 2/2,
2 trùng, 621 thư (1 mới, 620 đã có), 25 MB bị chặn: `.tmp-session/s252/aa945/import/results.json` (thời gian 14:34:19 → 14:34:27Z);
M365 chưa mở: ảnh Cài đặt "Not available yet on this server", checklist S253 "AA-945 M365 bị chặn".

---

## 3. PR-25 — Booking

**Vì sao issue này:** đặt dịch vụ với nhà cung cấp là phần đầu của vận hành sau bán (đặt nhà cung cấp, kiểm trước chuyến,
hoá đơn, thanh toán) — chưa báo trên Jira.

**Nội dung đăng:**

> @thule Cập nhật Booking (Dev, 26–27/10/2026): phần đầu của vận hành sau bán đã chạy trên Dev.
>
> - **Đặt dịch vụ với nhà cung cấp:** từ phiên bản đề xuất đã duyệt, Booking tạo sẵn booking với nhà cung cấp cho từng
>   phòng và dịch vụ; nhân viên gửi yêu cầu, ghi xác nhận (mã xác nhận, voucher), từ chối hoặc huỷ. Hồ sơ chuyến tự
>   chuyển sang bước "Supplier confirming"; khi mọi booking đã xác nhận thì hiện nhãn "Confirmed & Booked".
> - **Đã kiểm trên Dev với một hồ sơ chuyến thử:** tạo đúng 2 booking (2 đêm phòng, 1 dịch vụ kayak), xác nhận cả 2 →
>   nhãn "Confirmed & Booked", trạng thái chuyển đúng. Hệ thống từ chối các bước sai (xác nhận khi chưa gửi yêu cầu, đặt
>   trùng một dịch vụ). Màn hình tab Nhà cung cấp kiểm trên máy tính và điện thoại: không lỗi.
> - Chưa thử: xác nhận dòng "on-request" của đại lý ngay từ tab Nhà cung cấp (chưa có giữ chỗ on-request thử); thao tác
>   bằng tay của nhân viên trên giao diện (lần kiểm này ghi dữ liệu bằng kịch bản kiểm, giao diện kiểm ở chế độ xem).
>
> - **Kiểm tra trước chuyến đi (27/10):** khi hồ sơ chuyến được xác nhận, Booking tự tạo 3 việc cần kiểm: kiểm lại các
>   booking, liên hệ khẩn cấp (khách lẻ; khách đại lý thì không áp dụng), bảo hiểm du lịch. Nhân viên có thể thêm việc
>   riêng. Trang "Trip Checks" gom mọi việc của các chuyến đã bán, việc quá hạn tô đỏ; mỗi hồ sơ chuyến có tab Checks.
> - **Trạng thái chuyến tự đi theo ngày đi:** mỗi ngày hệ thống tự chuyển hồ sơ sang "Pre-departure", "On trip",
>   "Completed" theo ngày khởi hành / kết thúc. Đã kiểm trên Dev bằng hồ sơ thử: chuyển đúng tới "Completed"; lần chạy
>   thật đầu tiên trên toàn bộ hồ sơ chuyển 1 hồ sơ, không hồ sơ nào bị chặn. Màn hình kiểm trên máy tính và điện thoại.
>
> - **Hoá đơn và thanh toán (27/10):** từ phiên bản đề xuất đã duyệt, nhân viên tạo yêu cầu thanh toán (proforma) với lịch
>   thanh toán (ví dụ cọc 30%, còn lại 70%), gửi cho khách, sửa bổ sung khi cần, nhắc khách. Tiền nhận được ghi tay kèm
>   chứng từ; một người ghi, một người khác (admin) duyệt thì tiền mới được tính. Hồ sơ chuyến tự chuyển "Invoice sent" →
>   "Payment pending" → "Paid". Trang "Payments & Invoices" có số còn phải thu, quá hạn, đã nhận trong tháng.
> - **Đã kiểm trên Dev với hồ sơ thử:** gửi yêu cầu 30/70 → cọc được người thứ hai duyệt → trả nốt → "Paid"; huỷ một khoản đã
>   duyệt → quay về "Payment pending". Hệ thống từ chối: tự duyệt khoản mình ghi, duyệt khi thiếu chứng từ, ghi trùng một
>   khoản, sửa tay trạng thái "đã trả". Khoản quá hạn sinh nhắc nhở đúng một lần. Màn hình kiểm trên máy tính và điện thoại.
>
> Bước tiếp: hoá đơn của nhà cung cấp và chi trả, rồi trang "Thanh toán của tôi" cho khách trong TripPlanner.
>
> Ảnh: (1) tab Nhà cung cấp của hồ sơ chuyến, (2) cùng tab trên điện thoại nền tối, (3) trang Trip Checks, (4) tab Checks của một hồ sơ chuyến, (5) trang Payments & Invoices, (6) chi tiết một yêu cầu thanh toán.

**Ảnh đính kèm:**

| # | File | Tên khi upload |
|---|---|---|
| 1 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/aa682/shots/aa682-case-suppliers-1440-light.png` | `1-tab-nha-cung-cap.png` |
| 2 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/aa682/shots/aa682-case-suppliers-390-dark.png` | `2-tab-nha-cung-cap-dien-thoai.png` |
| 3 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa682-s2/trip-checks-1440.png` | `3-trip-checks.png` |
| 4 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa682-s2/case-TC-000019-checks-1440.png` | `4-tab-checks.png` |
| 5 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa682-s3/billing-1440.png` | `5-payments-invoices.png` |
| 6 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa682-s3/billing-invoices-INV-000003-1440.png` | `6-chi-tiet-yeu-cau-thanh-toan.png` |

**Câu → bằng chứng:** comment Linear AA-682 26/10 15:54Z (run-script dry run + apply: 2 booking, từ chối edge sai 23514,
trùng 23505, auto-advance `supplier_confirming`, supply `booked` 2/2; API 200; ảnh 1440 light / 390 dark, 0 lỗi; phần B2B
bỏ qua vì không có dòng on_request); S2 và S3: comment Linear AA-682 27/10 (run-script S2 go-live af5c3b5d; S3 #443/#444 verdict ok, 23514/23505); thiết kế các slice: `docs/audits/2026-10-26-S252-aa682-ops-mvp-design/design.md` §2.

---

## 4. PR-24 — TripPlanner

**Vì sao issue này:** kiểm TripPlanner sau lần viết lại toàn bộ nội dung (đã hứa ở "Bước tiếp" trên PR-22 ngày 25/10) và
các sửa lỗi khách thấy được.

**Nội dung đăng:**

> @thule Cập nhật TripPlanner (Dev, 26–27/10/2026):
>
> - **Kiểm lại sau lần viết lại nội dung:** 43 tour ở 14 nước, mỗi nước một nhóm tour: mọi trang tour mở được, 0 lỗi, nội
>   dung mới hiện đủ 43/43, số ngày trên trang khớp 42/43 (tour Việt Nam ghi 14 ngày nhưng nội dung chỉ có 12 ngày; đây là
>   lỗi nội dung, đang xem).
> - **Bản đồ tour chỉ có một địa điểm** trước đây không hiện ảnh; đã sửa, kiểm lại 2 trang lỗi trong mẫu: bản đồ đã hiện.
> - **Điểm dừng khách đã lưu đi theo địa điểm mới** khi địa điểm được dựng lại hay đổi tên; điểm dừng không còn địa điểm
>   tương ứng thì hiện "không còn" thay vì lỗi.
> - **Pakistan và Philippines** (18 và 44 tour) chưa có bản đồ vì hai nước thiếu trong danh sách nước của bản đồ. Đã thêm;
>   việc định vị địa điểm đang tự chạy (hết hạn mức miễn phí trong ngày thì tự chạy tiếp ngày sau). Chưa kiểm lại bản đồ
>   của hai nước sau khi định vị xong.
> - **Số ngày của tour:** sửa lỗi đọc file Excel làm mất ngày (dòng bắt đầu bằng dấu ngoặc kép). 3 tour bị mất ngày đã viết
>   lại; tour Sri Lanka có ngày dạng "Day 12–15" đã hiện đủ 16/16 ngày.
>
> - **Tuyến trong trang lập lịch trình:** tuyến chỉ được đưa ra khi gắn được địa điểm cho ít nhất một nửa số ngày; nếu không,
>   trang hiện danh sách ngày của tour. Kiểm lại 137 tour từng bị gắn cờ: không tour nào còn tuyến thiếu ngày.
> - **Trang chủ mới (27/10):** ảnh lớn đầu trang, ô tìm chuyến (số ngày, số khách), hàng tour nổi bật, lưới điểm đến, dải ảnh
>   chạy ngang như trang adventure.asia (có nút dừng; người dùng tắt hiệu ứng chuyển động thì dải ảnh đứng yên), dải mời
>   trao đổi với tư vấn viên, chân trang mới. Kiểm trên máy tính và điện thoại, nền sáng và tối: không lỗi, không tràn ngang.
>   Ảnh trùng nhau trong dải ảnh (cùng một ảnh lưu ở nhiều tour) đã được gộp ở phía nội dung.
>
> Ảnh: (1) trang tour Lào có bản đồ và lịch trình từng ngày, (2) trang tour Bhutan trên điện thoại, (3) trang chủ mới trên máy tính, (4) trang chủ trên điện thoại nền tối.

**Ảnh đính kèm:**

| # | File | Tên khi upload |
|---|---|---|
| 1 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-26-S252-aa990-parity/shots/laos-1440.png` | `1-trang-tour-lao.png` |
| 2 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-26-S252-aa990-parity/shots/bhutan-390.jpg` | `2-trang-tour-bhutan-dien-thoai.jpg` |
| 3 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa995-golden-hour/shots/home-light-1440-fold.png` | `3-trang-chu-moi.png` |
| 4 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa995-golden-hour/shots/home-dark-390-fold.png` | `4-trang-chu-dien-thoai.png` |

**Câu → bằng chứng:** 43 tour / 14 nước / 0 lỗi / 43 v2 / 42/43 ngày, Vietnam 12/14, F2 12/32, F3 PK/PH:
`docs/audits/2026-10-26-S252-aa990-parity/README.md`; sửa bản đồ một điểm live (200 `image/png`) và điểm dừng theo
redirect: comment Linear AA-990 26/10 (TripPlanner #158, #154); PK/PH vào danh sách nước + tự chạy tiếp sau hạn mức:
comment Linear AA-990 27/10 02:47Z; sửa đọc ngày + 3 Master viết lại + còn 1 Sri Lanka: comment Linear AA-990 27/10 05:04Z
và checklist S253 mục 5 (Sri Lanka đang chờ CI).

---

## 5. PR-22 — CIS nội dung & pipeline

**Vì sao issue này:** tiếp nối "Bước tiếp" của comment 25/10 trên PR-22 (các phần dùng lại nội dung tour phải đi theo nội
dung mới); thẻ địa điểm và bộ nhớ viết là phần của pipeline nội dung CIS.

**Nội dung đăng:**

> @thule Cập nhật nội dung CIS (26–27/10/2026):
>
> **1. Các phần dùng lại nội dung tour đã theo kịp nội dung mới** (tiếp theo cập nhật 25/10)
> - Dọn 10.495 liên kết cũ còn trỏ vào nội dung trước lần viết lại (có bản sao lưu cơ sở dữ liệu trước khi xoá); kiểm
>   lại còn 0.
> - Tìm và sửa một lỗi ghép: 227 hoạt động trong 157 tour (ví dụ "đi dạo trong Hutong") bị rơi khỏi lớp "khoảnh khắc"
>   dùng chung (lớp ghép các hoạt động giống nhau giữa các tour, dùng để gợi ý tuyến và xếp hạng). Đã sửa gốc và ghép
>   lại: còn 0. Cùng lỗi này làm 104 hoạt động bị ghép nhầm chỗ (ví dụ "ăn tối ở Negombo" nằm chung với "ăn sáng ở khách
>   sạn"); đã gỡ và xếp lại đủ 104/104.
> - Phép kiểm độ mới chạy mỗi đêm nay ở chế độ chặn: còn liên kết cũ quá 24 giờ là báo đỏ. Lần chạy 27/10: xanh.
> - Kết quả: 892/892 tour đang bán có dữ liệu địa điểm dựng từ nội dung mới; 883/892 tour có xếp hạng (9 tour còn lại
>   không có địa điểm đặt tên nào để xếp hạng).
>
> **2. Thẻ địa điểm: đạt ngưỡng chất lượng (27/10)** — thẻ giới thiệu ngắn cho từng địa điểm trong tour.
> - Luật mới: vùng phải là đơn vị hành chính cấp tỉnh/bang; điểm hẻo lánh không gán thị trấn gần nhất; bỏ các câu khẳng
>   định "hiện tại" không kiểm được (ví dụ "toà nhà vẫn là bưu điện").
> - 10 thẻ bị đánh dấu ở lần kiểm trước đã dựng lại: 9 đã đúng, 1 còn lệch ranh giới huyện; thêm 1 thẻ được giữ lại chờ
>   người xem lại.
> - Kiểm mù thẻ mới (2 lượt kiểm độc lập, tra nguồn web cho từng dữ kiện, 1 lượt phân xử chỗ lệch):
>
>   | | Lần 1 (26/10) | Lần 2 (27/10) | Lần 3 (27/10) | Ngưỡng |
>   |---|---|---|---|---|
>   | Dữ kiện sai | 3/83 = 3,6% | 3/79 = 3,8% | **1/51 = 2,0%** | ≤ 3%: **đạt** |
>   | Lọt chi tiết tour | 0 | 0 | 0 | ≤ 2%: đạt |
>   | Sai địa điểm | 0 | 0 | 0 | ≤ 1 thẻ: đạt |
>   | Sai nước | 0 | 0 | 0 | 0: đạt |
>   | Thẻ sai thị trấn/vùng | 7/20 | 6/20 | 3/14 | theo dõi |
>
> - Ở lần 2, 3 dữ kiện sai đều là con số lệch nhẹ: năm mất 1938 (đúng 1939), độ cao "khoảng 3.480 m" (đúng 3.458 m), năm thành lập
>   1870 (đúng 1872). Không còn câu "hiện tại" sai. Lỗi thị trấn/vùng giờ là bỏ trống quá tay (công viên, hang trong thành
>   phố mất thị trấn; Almaty, Huế mất vùng).
> - Vòng 3 (luật mới: giữ thị trấn cho công viên, hang, tượng đài trong thành phố; điền vùng cho thành phố trực thuộc trung
>   ương; kiểm từng con số chính xác) đạt cả 4 ngưỡng. Còn theo dõi: 6 thẻ cho địa điểm nằm trên biên giới hai nước (DMZ,
>   Gobi, dãy Kanchenjunga…) chưa áp được luật mới, sẽ xử lý riêng.
>
> **3. Bộ nhớ viết (Writing memory): bản phát hành đầu tiên**
> - Hệ thống gom các chỗ người duyệt sửa và các lỗi kiểm lặp lại thành quy tắc cho các bộ viết AI. Quy tắc chỉ tới bộ viết
>   qua một "bản phát hành" đã chạy kiểm lại và được duyệt; quay về bản trước được.
> - Ngày 27/10 bật bản phát hành đầu tiên (bản gốc, chưa thêm quy tắc nào) cho 4 bộ viết: nội dung Master, tour viết lại
>   của tenant, blog, bài mạng xã hội. Kiểm lại 21–25 bài mỗi bộ: 0 khác biệt chữ so với trước. Diễn tập quay về bản trước
>   trên một tenant thử: đạt.
> - Trang Writing memory trong admin có thêm tab Guide giải thích cách hoạt động.
> - Tự động gom quy tắc đang tắt; quy tắc đầu tiên sẽ qua kiểm lại và duyệt trước khi áp dụng.
>
> Ảnh: (1) trang Writing memory (có tab Guide), (2) cùng trang trên điện thoại nền tối.

**Ảnh đính kèm:**

| # | File | Tên khi upload |
|---|---|---|
| 1 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/admin-shots/wm-guide/wm-guide-1440-light.png` | `1-writing-memory.png` |
| 2 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/admin-shots/wm-guide/wm-guide-390-dark.png` | `2-writing-memory-dien-thoai.png` |

**Câu → bằng chứng:**
- 10.495 → 0, snapshot trước khi xoá, probe enforce xanh, `ENFORCE=True`, 892/892 nguồn: comment Linear AA-991 27/10 05:52Z.
- 227 atom / 157 tour → 0, ví dụ Hutong, 883/892 xếp hạng, 9 tour không segment: comment Linear AA-988 27/10 07:24Z
  (probe run xanh 40466598280); 104 dòng ghép nhầm → 104/104, ví dụ Negombo: comment AA-988 27/10 07:28Z.
- Thẻ địa điểm: `docs/audits/2026-10-27-S253-aa784-spotcheck-r2/README.md` + comment Linear AA-784 27/10 07:43Z (9/10, C17, C07,
  vòng 3); vòng 3: `docs/audits/2026-10-27-S253-aa784-spotcheck-r3/README.md` + comment Linear AA-784 27/10 10:00Z (FK 1/51, Done).
- Writing memory: `docs/audits/2026-10-26-S252-wm20-release0/README.md` mục "Update 27/10" (T2 21 / T9 25 / A1 25 input, 0 diff,
  active 4 writer, memory on, drill terra-family pass); tab Guide: log S252 (CIS #1054/#1055); mining tắt: ảnh 1 ("automatic
  mining is off").

---

## 6. PR-27 — Nền tảng

**Vì sao issue này:** trang Data coverage là công cụ dùng chung cho mọi app (CIS, TripPlanner, Booking, CRM).

**Nội dung đăng:**

> @thule Cập nhật nền tảng (Dev, 26–27/10/2026):
>
> - **Trang "Data coverage" trong admin CIS:** một trang số liệu cho cả hệ thống, đi theo dữ liệu từ file Excel tour và
>   file thương hiệu → nội dung Master → các phần dùng lại → tenant, TripPlanner, Booking, CRM, và chỉ ra chỗ nào thiếu
>   dữ liệu.
> - Lần đo 26/10: 892 tour đang bán, 17 chỗ thiếu cần xem, 1 nguồn chưa đo được. Có nút làm mới và xuất CSV.
> - Đã mở bằng phiên admin thật trên máy tính và điện thoại, nền sáng và tối: 0 lỗi. Lỗi nút đầu trang tràn khỏi màn hình
>   điện thoại đã sửa chung cho mọi trang admin.
> - Kiểm độ mới dữ liệu mỗi đêm nay chặn khi còn liên kết cũ (xem cập nhật CIS, PR-22). Đăng nhập một lần có xác thực 2
>   lớp cho đại lý: xem cập nhật Portal (PR-23).
> - **Cập nhật hệ thống không phải chờ việc nền chạy xong (27/10):** trước đây mỗi lần cập nhật CIS phải đợi mọi việc nền
>   (viết lại, dựng dữ liệu) xong, có khi vài giờ. Giờ việc đang chạy được làm nốt trong tối đa 100 giây; việc dài hơn được
>   trả về hàng đợi và máy mới chạy tiếp, không mất, không chạy trùng. Đã thử trên Dev bằng 3 lần cập nhật trong lúc có việc
>   đang chạy: việc ngắn được làm xong ngay; việc dài 30 phút được trả về hàng đợi rồi chạy tiếp và hoàn tất đúng một lần. Booking và CRM cũng dừng gọn trong dưới 1 giây.
> - **Một bộ giao diện chung cho các app:** các thành phần giao diện của admin CIS gom về một bộ dùng chung, có kiểm tự động
>   để các app khác chép đúng. Bốn màu ở nền sáng được chỉnh cho dễ đọc hơn (chữ trên nút vàng đổi từ trắng sang nâu đậm).
>
> Ảnh: (1) trang Data coverage, (2) trên điện thoại nền tối, (3) admin CIS sau khi chỉnh màu.

**Ảnh đính kèm:**

| # | File | Tên khi upload |
|---|---|---|
| 1 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/admin-shots/aa992/aa992-data-coverage-1440-light.png` | `1-data-coverage.png` |
| 2 | `/home/nghiep/projects/AA-Ecosys/.tmp-session/s252/admin-shots/aa992/aa992-data-coverage-390-dark.png` | `2-data-coverage-dien-thoai.png` |
| 3 | `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-27-S253-aa994-s1b/prod-review-light-1440.png` | `3-admin-cis-mau-moi.png` |

**Câu → bằng chứng:** comment Linear AA-992 26/10 15:55Z (892 tour, 17 gap, 1 not available, Refresh + Export CSV, 0 lỗi
console / API, ảnh 1440/390 light/dark, `PageHeader` sửa cho mọi trang CIS #1040); phạm vi trang:
`docs/audits/2026-10-26-S252-data-coverage/README.md`; cập nhật không chờ việc nền: comment Linear AA-993 27/10 15:00Z (job 1800 s nhả lúc deploy, succeeded attempt 1); màu: comment Linear AA-994 27/10 15:00Z (Nghiệp duyệt H6).

---

## 7. PR-20 — Báo cáo nền tảng kỳ 3 (27/10–02/11/2026)

**Vì sao issue này:** báo cáo tuần theo lệ từ S245 là một story con của PR-20 mỗi kỳ. Kỳ 3 **chưa có story**: cần Nghiệp
đồng ý tạo story "Báo cáo nền tảng kỳ 3 (27/10–02/11/2026)" dưới PR-20 với mô tả bên dưới (như PR-28 kỳ 2). Nếu không tạo:
đăng nguyên văn làm comment trên PR-20. Đây là bản đầu kỳ (số liệu 27/10), gồm cả việc xong 25–26/10 sau khi đăng báo cáo
kỳ 2; cuối kỳ có thể bổ sung.

**Nội dung (mô tả story mới):**

> @thule Báo cáo nền tảng kỳ 3 (27/10–02/11/2026), bản đầu kỳ, số liệu 27/10/2026. Gồm cả việc xong 25–26/10 sau báo cáo
> kỳ 2. Chi tiết ở comment mới trên từng epic.
>
> | App | Đã xong | Tiếp theo |
> |---|---|---|
> | CIS (PR-22) | Dọn 10.495 liên kết cũ; sửa lỗi ghép, 227 hoạt động → 0 bị rơi; kiểm độ mới mỗi đêm chuyển sang chặn, đang xanh; bộ nhớ viết bật bản phát hành đầu tiên cho 4 bộ viết; thẻ địa điểm đạt ngưỡng (dữ kiện sai 2,0%) | Thẻ cho địa điểm trên biên giới hai nước |
> | Portal (PR-23) | Portal chạy trên máy chủ AA, cùng địa chỉ; đăng nhập một lần có xác thực 2 lớp; luồng mời thử trọn vòng; diễn tập quay lại khoảng 3 phút | Từ 03/11 tắt đăng nhập bằng khoá API, gỡ bản Vercel |
> | TripPlanner (PR-24) | Kiểm 43 tour / 14 nước sau lần viết lại: 0 lỗi; sửa bản đồ một địa điểm; điểm dừng đã lưu đi theo địa điểm mới; tuyến lập lịch trình đủ ngày; trang chủ mới | Bản đồ Pakistan / Philippines sau khi định vị xong; các trang còn lại theo giao diện mới |
> | Booking (PR-25) | Đặt dịch vụ với nhà cung cấp; kiểm tra trước chuyến; trạng thái tự theo ngày đi; hoá đơn và thanh toán ghi tay (hai người ghi/duyệt) | Hoá đơn nhà cung cấp và chi trả; "Thanh toán của tôi" cho khách |
> | CRM (PR-26) | Gửi thư bằng Gmail của đại lý thử trọn vòng; nhập lịch sử thư | Microsoft 365 |
> | Nền tảng (PR-27) | Trang Data coverage cho cả hệ thống; cập nhật hệ thống không phải chờ việc nền; bộ giao diện chung bước đầu | Rà soát chi phí theo app đầu tháng 11 |
>
> **Chi phí:** chi phí AI đo từ 0 giờ 25/10 (UTC) tới sáng 27/10: 54,93 USD, trong đó dựng dữ liệu địa điểm 4,31 USD và
> thẻ địa điểm cho 892 tour 12,65 USD. Các lần dựng lại và sửa dữ liệu ngày 27/10 khoảng 0,20 USD.
>
> **Rủi ro:** không có sự cố ảnh hưởng người dùng; hệ thống vẫn ở môi trường thử nghiệm với dữ liệu thử.

**Ảnh:** không (ảnh nằm ở comment từng epic).

**Câu → bằng chứng:** các dòng bảng lấy từ mục 1–6 ở trên; 54,93 USD: `docs/audits/2026-10-27-S252-session-close/state-snapshot.md`
(`shared.llm_call_log` từ 25/10 00:00Z); 4,31 / 12,65: log S252 mục Chi phí; dưới 0,20 USD ngày 27/10: dựng lại 10 thẻ $0,048
(Linear AA-784), 20 thẻ ≈ $0,10, 20 thẻ vòng 3 $0,045 (job 8da054d1) (`docs/audits/2026-10-27-S253-aa784-spotcheck-r2/README.md`), recompute ≈ $0,009 (Linear AA-988);
"rà soát chi phí đầu tháng 11": hứa trong PR-28.

---

## Kết quả đăng

Nghiệp duyệt 27/10 tối; đăng cùng ngày (`contentFormat: html`, mention thật, ảnh nhúng đúng thứ tự):

| Issue | Comment id | Ảnh |
|---|---|---|
| PR-23 | 10509 | 5 |
| PR-26 | 10510 | 4 |
| PR-25 | 10511 | 6 |
| PR-24 | 10512 | 4 |
| PR-22 | 10513 | 2 |
| PR-27 | 10514 | 3 |

**§7 PR-20 (báo cáo kỳ 3): không đăng.** Nghiệp: báo cáo kỳ một tuần một lần; kỳ 2 mới tạo thứ Hai, nên kỳ 3 làm vào tuần sau.
PR-27: câu "3 lần cập nhật…" đã sửa cho đúng bằng chứng trước khi đăng (job 300 s / 900 s / 1800 s).
