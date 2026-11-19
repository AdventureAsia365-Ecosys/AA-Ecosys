# Audit kế hoạch S286–S292: phân quyền gọn trước, rồi trang làm việc cho Trang

Phiên S285, 19/11/2026. Tác nhân: Claude Code. Chỉ đọc, chưa sửa plan.json, Linear hay code.

Nguồn: `docs/backlog/tracker/plan.json` (bản local, có thay đổi chưa commit), `docs/backlog/README.md`, Linear (đọc lúc ~11:30Z),
code trên origin/main: CIS `1b3e07c09`, Booking `e329c9e`, Partner `fbe5ff71`, TripPlanner `6e4eab7`, Infra `f031107e`.
Quyết định: trang quyết định truy cập (`.tmp-session/S285/decisions3`, 27 yes, A8 no), trang vai trò gọn
(`.tmp-session/S285/decisions5`), `permmap/lean.json`. Bản nháp issue tiếng Anh: `plan-audit-issue-drafts.md`.
Thay đổi lịch dạng máy đọc: `plan-audit-plan-changes.json`.

Chưa kiểm live: Trang đã có tài khoản WORKFORCE chưa; ai đang giữ `content_creator` và `booking-contracting`; lần đầu
một người không phải admin mở Booking có phải đăng nhập lại không.

---

## 1. Tóm tắt

1. **Tiến độ:** M-SUP đã xong L1 (AA-1144). L5 (AA-1145) và L3 phần 1 (AA-1146) đã merge, chỉ còn verify live. Đang có 10 issue mở dở, vượt trần 8.
2. **Phần Content, Trang làm được ngay hôm nay** với vai trò CIS `content_lead` có sẵn (giao tay trên trang Staff). Phần Booking thì **không nên** giao tạm `contracting`: vai trò này có quyền duyệt hoá đơn, giá, mùa giá và dừng bán, trái với luật "Trang không duyệt gì".
3. **Booking cho Trang (sản phẩm, vận hành, hoá đơn NCC, hoá đơn đại lý)** đến khi có vai trò tuỳ chỉnh: cuối S287, chậm nhất S288. Trang không bao giờ tự ghi chi trả cho NCC; việc này do business owner làm. Nhập tài khoản ngân hàng NCC thì đến S289.
4. **Phân quyền gọn xong hẳn** (vai trò tuỳ chỉnh, xem như vai trò thấp hơn, owner tự duyệt có cờ, luật duyệt, tài khoản ngân hàng) khoảng S289, tức 23/11. **M-SUP** xong khoảng S290 (24/11), chậm khoảng 1 phiên so với lịch cũ và dùng hết phiên dự phòng.
5. Cần tech lead chốt **3 việc trước khi S286 bắt đầu**: Trang chưa vào Booking cho tới khi có vai trò tuỳ chỉnh (Q1); cách Booking biết một người giữ vai trò tuỳ chỉnh nào (Q2); danh sách quyền của Trang trong Booking (Q3). Danh sách đầy đủ ở mục 6.

---

## 2. Lịch mới S286–S292

Giả định khoảng 1 phiên mỗi ngày: S286 = 20/11 … S292 = 26/11. Mỗi phiên tối đa 3 lane nặng.

**Luật áp migration:** DB Migrate `apply` chỉ chạy khi **cả ba** bảng job `shared.job`, `booking.job` và `crm.job` đều rảnh
(DM-11.4). Lịch cũ chỉ nhắc `booking.job`, như vậy là sai. Trong mỗi phiên: áp migration trước, chạy LLM trả phí sau.

Cách đọc bảng: "đóng" là issue đã build xong, chỉ còn verify live, bằng chứng rồi chuyển Done.

| Phiên | Issue | Vì sao |
|---|---|---|
| **S285 (còn lại hôm nay)** | Bước 0 kiểm live (chỉ đọc) + bước tay: mời Trang vào WORKFORCE, đặt mật khẩu, TOTP, giao **CIS `content_lead`, chưa giao Booking** | Trang bắt đầu Content ngay. Kiểm live rẻ, không cần chờ S286. |
| **S286 (20/11)** | Đóng trước: AA-1145, AA-1146 (phần 1), AA-1134, AA-1127, AA-1051 (cho đợt chạy T2 xong) | Đóng trước để đưa số issue mở dở từ 10 về khoảng 6 rồi mới mở lane mới (luật In Progress phải hội tụ). |
| | **AA-1150** (thu hẹp: bước 1) | Ưu tiên 1 của tech lead. Gồm preset trên trang Staff, bỏ `content_creator`, cho finance quyền đọc, tách quyền làm và quyền duyệt, chứng minh một lần đăng nhập. Không có migration. |
| | **NEW-W1** My work trong CIS (dải Content) | Ưu tiên 2. Trang có một trang việc cần làm cho phần Content. Không có migration, không đụng file của AA-1150. |
| | **NEW-R1** (khởi động) | Viết và apply PR Infra (nhóm `booking-custom`, `cis-custom`, người dùng E2E). Viết PR migration CIS + bk-. Chỉ apply khi AA-1051 đã chạy xong và cả 3 bảng job rảnh; nếu không kịp thì sang S287. |
| **S287 (21/11)** | **NEW-R1** (xong) | Chuỗi: apply migration → PR schema-reference merge → deploy code → bước tay giao vai trò tuỳ chỉnh cho Trang. Cuối phiên Trang vào được Booking. |
| | **NEW-W2** (bắt đầu) | Ô việc ngay trên dashboard Booking, lọc theo `me.permissions`. Không có migration. |
| | AA-1147 L2 | Đã sẵn sàng từ khi AA-1144 xong. |
| | AA-1137 | Đóng sau khi có T7/T8. |
| | AA-788 pilot 20 mẩu (≤5 USD) | Chạy **sau** khi áp migration xong, để không chặn DB Migrate. |
| | AA-1139 (đóng nếu lane l19 xong) | Đóng. |
| **S288 (22/11)** | **NEW-R3** phần 1: luật duyệt cho 3 người, owner tự duyệt có cờ, kiểm soát thông tin chuyển khoản trên hoá đơn đại lý, chặn bật "đang bán" khi giá chưa duyệt | Bịt các đường gian lận trước khi Trang làm nhiều trong Booking. Có migration bk-. |
| | **NEW-R2** View-as xuống dưới (CIS + Booking) | Cần marker owner từ NEW-R1. Booking dùng cookie ký ngắn hạn cộng audit sẵn có, không thêm bảng. |
| | **NEW-W2** (xong phần lọc) | Bộ lọc mới (hoá đơn đến hạn 7 ngày, hợp đồng sắp hết hạn, đặt dịch vụ NCC qua mọi hồ sơ), link qua lại My work, thông báo theo quyền. |
| | AA-1149 L6 | Migration bk- thứ hai trong phiên, áp sau NEW-R3. |
| | AA-1148 L4 (bắt đầu) | Phần editor chạy song song được. Phần `staff_authz.py` (`photos.upload`) chỉ làm sau khi NEW-R2 merge, vì đụng cùng file. |
| **S289 (23/11)** | **NEW-R3** phần 2: hồ sơ NCC đầy đủ + tài khoản ngân hàng NCC mã hoá KMS, khoá chi trả 24 giờ | A1 đã duyệt khoảng 1 USD/tháng. Cần phần 1 xong trước. |
| | **NEW-W2** (dải "Đang chờ người khác" / "Chờ tôi duyệt") | Đọc dữ liệu chờ duyệt do NEW-R3 tạo ra. |
| | AA-1148 (tiếp), AA-1151 L8, AA-1153 L10 phần 1 | Chuỗi bk-: NEW-R3 p2 → AA-1151 → AA-1153 p1. Nếu bảng job bận thì AA-1153 p1 dời sang S290. |
| | AA-1136 (đóng sau 1 tuần log) | Đóng. |
| | Bước tay chốt cuối: giao vai trò thật cho 3 người | Xem mục 3.4. |
| **S290 (24/11)** | AA-1152 L9, AA-1153 phần 2, AA-1148 (xong), dự phòng sửa review, AA-1140 | Đóng M-SUP. Hết dự phòng sau phiên này. |
| **S291 (25/11)** | AA-1154 A0, AA-1141, AA-1119, AA-1103 (gộp AA-1121) | Sau M-SUP. |
| **S292 (26/11)** | AA-1154 A1, AA-1142, AA-1118, AA-1050 (chỉ khi có khoảng 30 nhãn bất đồng) | Sau M-SUP. |

**Chờ ngày hoặc chờ người ngoài (chưa xếp phiên):**
- AA-1004: hạn 20/11, nhưng chờ phụ lục TrueIDC, hoá đơn 25–28/11 và lời mời vào org ngày 01/12. Nên đổi hạn, không để nó hiện quá hạn.
- AA-1110 (≥01/12), AA-1111 (TOTP tech lead, WAF #935), AA-1122 (≥02/12), AA-873 (≥01/12), AA-1061 (từ 28/11 23:50Z).
- AA-980, AA-1054, AA-1117: chờ ngày go-live.
- AA-1011 (app Entra), AA-948 (đồng ý chi phí Mapbox), AA-881 (05/2027).
- AA-790, AA-920, AA-921, AA-1000: chỉ còn chờ mở băng TL-11. Đường LLM đã có từ S278.
- AA-704, AA-782, AA-842, AA-855: đang đỗ.

**Số migration (đếm lại):**
- Booking 6–7 cái: NEW-R1, NEW-R3 p1, AA-1149, NEW-R3 p2, AA-1151, AA-1153 p1 (và p2 nếu cần). Lịch cũ ghi "bảy" nhưng liệt kê tám.
- NEW-W2 không cần migration vì đọc bảng của chính Booking.
- CIS: **một** migration cho mọi thay đổi vai trò (NEW-R1), cộng một cái của AA-1148 nếu cần.
- Số NNN lấy lúc viết, không cố định ở đây.

---

## 3. Phân quyền

### 3.1 Mô hình đích

Có 3 vai trò cho người. Mỗi người một tài khoản WORKFORCE, đăng nhập một lần là vào được mọi app mình cần. Claude Code
không có vai trò nào. Ma trận không có dòng agent; người dùng E2E không hiện như một vai trò.

| Vai trò | Người | CIS | Booking | CRM staff | Duyệt |
|---|---|---|---|---|---|
| Administrator | tech lead | `admin` + `is_owner` | `admin` | `platform_admin` | Duyệt việc của người khác. **Không bao giờ tự duyệt việc mình làm.** |
| Business owner | chị Thư | `admin` + `is_owner` + **marker `business_owner`** (đúng 1 người, lưu ở server) | admin + tự duyệt có cờ | chỉ đọc | Tự duyệt được: NCC, hợp đồng/giá/mùa, hoá đơn NCC, tài khoản ngân hàng NCC, tín dụng/giảm giá/hoàn tiền cho đại lý. Mỗi lần ghi cờ `owner_self_approved`. **Ghi chi trả NCC** (chị là người duyệt chuyển khoản thật trên internet banking). |
| Content + Sản phẩm, vận hành & kế toán | Trang | Vai trò "Content" = `content_lead` **bỏ** `content.settings.write`, **thêm** `tenant.read` (từ NEW-R1). Trước đó dùng tạm `content_lead`. | **Một vai trò tuỳ chỉnh**, danh sách cho phép viết rõ (mục 3.3). Chỉ làm, không duyệt. | không | Không duyệt gì. |

Các luật cứng (nằm trong code và DB, không phụ thuộc ô tick trong vai trò):
- Người làm khác người duyệt. Người chi trả khác người duyệt, trừ trường hợp business owner có cờ.
- Không ai tự hạ quyền chính mình. Không xoá được owner cuối cùng.
- **Quyền loại duyệt** (`*.approve`, `supplier.activate`, `contract.publish`, `stop_sale.approve`, `payout.write`, `payment.verify`, `billing_config.write`, `staff.admin`) **chỉ nằm ở vai trò dựng sẵn** (admin, business_owner). Code từ chối nếu một vai trò tuỳ chỉnh chứa các quyền này. Luật này thay cho "cảnh báo tổ hợp rủi ro", vì cảnh báo chỉ là lời khuyên.
- Chữ "owner" có hai nghĩa, phải tách rõ:
  - `is_owner` (CIS) là cờ được sửa vai trò. Cả tech lead và chị Thư đều có.
  - `business_owner` là marker được tự duyệt, chỉ đúng 1 người. DB chỉ chấp nhận `owner_self_approved = true` khi dòng của người duyệt có marker này, không bao giờ lấy từ field trong request.
- View-as: chỉ xem xuống dưới, chỉ đọc, có log, không đổi phiên đăng nhập. "Xuống dưới" nghĩa là quyền **đọc** của vai trò đích là tập con quyền đọc của người xem. Chặn mọi request không phải GET trước khi route chạy. Dòng log bắt đầu ghi đủ danh sách quyền của vai trò đích.
- CRM: các nhóm hiện có đã đáp ứng ma trận. Chỉ hiện ở dạng đọc, không làm editor. TripPlanner không có vai trò staff.

### 3.2 Code hôm nay có gì (đã đọc trên origin/main)

**CIS**
- `api/core/staff_authz.py` có 9 vai trò, quyền khai báo theo kiểu "cấm nếu không cho".
- `content.publish` và công tắc duyệt 2 người (CIS 458, đang tắt trên Dev) đã có. D5 đã xong: `content_lead` mất `reference_price.write`.
- `staff_directory.py` là nơi duy nhất ghi nhóm WORKFORCE. Mỗi người 1 vai trò CIS và 1 vai trò Booking (`shared.staff_app_grant`). Đã có preset `platform_owner` và `pricing_team`.
- View-as hiện chỉ có cho tenant (`shared.staff_view_as_session`, `tenant_id` NOT NULL).

**Booking**
- `backend/app/auth/staff.py` có 5 vai trò, `PERMISSIONS` là dict trong code.
- Vai trò lấy từ nhóm `booking-*` **đầu tiên** trong token, nên mỗi người chỉ có 1 vai trò.
- Đã kiểm: `contracting` có `bill.approve`, `b2b_desk.approve`, `stop_sale.write`, `supply.write` (hôm nay dùng cả để kích hoạt NCC và publish hợp đồng). Finance có `billing_config.write`, tức là sửa được `payment_instructions` (thông tin chuyển khoản AA in trên hoá đơn gửi đại lý), mà không có ai duyệt.
- Có khoảng 10 CHECK người làm khác người duyệt. R6 dừng bán đã xong (bk-060).

**Infra**
- `identity.tf` có 16 nhóm staff.
- Trigger pre-token **bỏ mọi nhóm không có trong `STAFF_GROUPS`**. Vì vậy phải apply nhóm mới trước khi xếp người vào nhóm đó.

### 3.3 Danh sách quyền Booking của Trang (đề xuất, cần chốt ở Q3)

Viết thành danh sách cho phép, có unit test khẳng định vai trò này không chứa quyền loại duyệt.

- **Sản phẩm và vận hành:** `supply.read/write` (sau khi tách: tạo/sửa NCC và hợp đồng nháp, **không** kích hoạt, **không** publish), `pricing.read/write` (tạo nháp, không duyệt), `trip_plan.write`, `stop_sale.write` (chỉ đặt, không gỡ hay duyệt), `catalog.read`, `ops.read/write`, `b2b_desk.read/write`, `staff.directory`.
- **Kế toán:** `bill.read/write` (nhập hoá đơn NCC), `billing.read/write`, `agency_billing.*` (lập, phát hành hoá đơn đại lý, ghi tiền nhận), `profit.read`.
- **Báo giá, đặt chỗ cho đại lý (cần chốt):** `b2b_desk.book`, `trip_case.read/write`, `customer.read/write`. Không có `customer.admin`, `trip_case.assign`, `version.write`.
- **Không bao giờ có:** `payout.write`, `billing_config.write`, `payment.verify`, `agency_payment.approve`, mọi `*.approve`, `supplier.activate`, `contract.publish`, `stop_sale.approve`, `staff.admin`.
- **Tài khoản ngân hàng NCC:** `supplier_bank.write` (chỉ nhập) thêm vào **sau khi** NEW-R3 phần 2 có owner duyệt, gọi lại xác nhận và khoá 24 giờ.

### 3.4 Các lát xây theo thứ tự

"Rủi ro" nghĩa là đụng auth, quyền, migration hoặc tiền. Mỗi PR rủi ro cần một agent review độc lập trước khi merge.

| # | Lát | Repo / migration | Phiên | Rủi ro |
|---|---|---|---|---|
| 0 | Kiểm live (chỉ đọc). (a) Vai trò và `is_owner` của từng dòng staff. (b) Trang có tài khoản chưa. (c) Ai giữ `content_creator`. (d) Ai giữ `booking-contracting`, kể cả người dùng E2E pricing checker A10e-2 và preset "Pricing team". | Cognito `list-users-in-group`, CIS `staff_app_grant`, Booking `staff_users` qua DB Migrate run-script | S285 | không |
| 1 | **AA-1150 bước 1.** CIS: preset "Administrator", "Business owner", "Content + Product & operations"; vai trò khác ẩn sau "Show all roles"; bỏ `content_creator` khỏi `BOOKING_ROLES` và thêm danh sách nhóm đã nghỉ để Sync gỡ; nhãn "Product & operations". Booking: finance có quyền đọc (L7a); tách `supplier.activate`, `contract.publish`, `stop_sale.approve` khỏi quyền ghi. Built-in `contracting` **giữ** các quyền duyệt để E2E pricing không vỡ. Chứng minh một lần đăng nhập. | CIS + Booking, không có migration | S286 | trung bình |
| 2 | **NEW-R1 vai trò tuỳ chỉnh.** Thứ tự bắt buộc: (1) PR Infra: nhóm `booking-custom`, `cis-custom`, 1 người dùng E2E "maker" giữ vai trò tuỳ chỉnh, người dùng E2E `content_lead` (A10f), test trigger; apply với MFA. (2) **Một** migration CIS + một migration bk-, apply khi cả 3 bảng job rảnh. (3) PR schema-reference merge. (4) Deploy code Booking + CIS. (5) Bước tay đổi vai trò. Vai trò dựng sẵn **vẫn nằm trong code**; bảng chỉ chứa vai trò tuỳ chỉnh; chỉ người giữ `booking-custom`/`cis-custom` bị "fail closed". Editor có ở Booking; CIS chỉ seed bảng, chưa làm editor UI. Có trang ma trận đọc, sinh từ bảng. Sửa P13 (route trần chi phí AI phải có phiên Cognito thật và audit trước/sau). | Infra → CIS mig + bk- mig → code | S286–S287 | cao |
| 3 | **NEW-R2 View-as xuống dưới** ở CIS (mở rộng bảng phiên view-as; nếu kịp thì gộp vào migration CIS của NEW-R1) và Booking (cookie ký ngắn hạn + audit sẵn có, không thêm bảng). | CIS + Booking | S288 | cao |
| 4 | **NEW-R3 phần 1 luật duyệt.** R5: NCC mới ở trạng thái `pending` và cần `activated_by`. R4: danh sách người viết hợp đồng + CHECK. R3: người chi trả khác người duyệt hoá đơn. Cột `owner_self_approved` cùng CHECK nới, chỉ khi người duyệt có marker `business_owner`. Maker-checker cho `payment_instructions`/`is_default` của pháp nhân lập hoá đơn. Không bật được `sellable` khi tour chưa có phiên bản giá đã duyệt (kiểm readiness trước). Bộ lọc audit đã lưu `owner_self_approved = true` hiện trên dashboard của owner, **không** làm job digest hằng tuần. | bk- | S288 | cao |
| 5 | **NEW-R3 phần 2.** Hồ sơ NCC đầy đủ. Tài khoản ngân hàng NCC mã hoá bằng khoá KMS riêng. Mọi thay đổi chờ owner duyệt kèm ghi chú gọi lại xác nhận. Khoá chi trả 24 giờ. | Infra KMS → bk- | S289 | cao (tiền, ~1 USD/tháng) |
| 6 | Bước tay chốt cuối (link trang Staff, giá trị chính xác) | — | S289 | không |

**Cách Booking biết một người giữ vai trò tuỳ chỉnh nào** (nhóm `booking-custom` chỉ nói "có tuỳ chỉnh", không nói vai trò nào). Đề xuất **phương án A**:
- CIS xuất một contract view chỉ chứa khoá: `shared.v_staff_booking_grant(cognito_sub, booking_role_code, is_owner, is_business_owner)`.
- Chỉ role `booking` được SELECT. Ghi vào owners.yaml `consumer_grants` và isolation probe.
- Booking đọc view này khi token có `booking-custom`, hoặc khi cần biết marker owner (lúc duyệt, lúc view-as). Cache 60 giây, fail closed.
- Như vậy không cần nhóm Cognito `booking-business_owner`.
- Phải ghi bổ sung vào ADR 0006, vì đây là thay đổi với luật "danh bạ CIS là nguồn sự thật".

**Phương án B:** router `/staff` của chính Booking ghi `booking.staff_users.custom_role`, và trang Staff của CIS deep-link sang đó.

**Đường lùi, chỉ khi Q2 bị trễ:** thêm vai trò dựng sẵn `ops_finance` theo mẫu đã làm với finance (CIS 363 + bk-038 + một nhóm). Mặc định không làm, vì tech lead đã duyệt vai trò tuỳ chỉnh ngay.

### 3.5 Rủi ro chính

- **Khoá nhầm admin.** Đã giảm bằng cách giữ vai trò dựng sẵn trong code. Done-when có bước: thu quyền đọc bảng vai trò trong test, admin vẫn đăng nhập và mở `/staff` được.
- **Xung đột file CIS.**
  - AA-1150 và phần CIS của NEW-R1 cùng sửa `staff_directory.py` và `StaffManage.tsx`, nên NEW-R1 chạy sau khi PR CIS của AA-1150 merge (cùng lane, hoặc rebase).
  - NEW-R1 → NEW-R2 → phần authz của AA-1148 chạy tuần tự, không để song song.
  - AA-1150 và NEW-W1 không đụng cùng file.
- **E2E không đủ để chứng minh.** Phiên E2E admin của Booking chỉ đọc. Vì vậy cần thêm người dùng E2E "maker" (vai trò tuỳ chỉnh) và E2E `content_lead`. Nếu không thêm được thì chứng minh bằng test tích hợp API trong CI và ghi rõ trong Done-when.
- **Đường gian lận còn mở cho tới S289:** tạo NCC → đặt dịch vụ → nhập hoá đơn. Những gì đang chặn: owner kích hoạt NCC (S288), Trang không có quyền chi trả, chưa có tài khoản ngân hàng cho tới khi có khoá (S289).

---

## 4. Trang làm việc của Trang

### 4.1 Hiện có gì

**CIS với `content_lead` vào được:** Review Queue (trang đích hiện nay), upload Excel và S1, Master content, nội dung khách sạn/hoạt động, AA content, ảnh (đồng bộ Drive), place cards, facts, giữ text tenant, atoms, SEO, giá tham chiếu (chỉ đọc).

**CIS còn thiếu với vai trò này:**
- `/admin/places` (chỉ admin).
- `/admin/jobs` (chỉ admin). Wave chưa có trang.
- `/admin/tenants` (thiếu `tenant.read`).
- Chưa có upload hay crop ảnh (thuộc AA-1148).
- `content_lead` rộng hơn dòng CIS trong ma trận gọn: nó có `content.settings.write` (gate, brand, SEO). Tạm chấp nhận ở S286. NEW-R1 sẽ bỏ quyền này khỏi vai trò "Content". Cần kiểm "gates" gồm những gì trước khi chốt.

**Booking:** `contracting` phủ khoảng nửa việc (NCC, hợp đồng, giá, dừng bán, B2B desk, đặt dịch vụ NCC, hoá đơn NCC). `finance` phủ nửa kia (hoá đơn đại lý, lợi nhuận). Mỗi người chỉ có 1 vai trò, nên không ghép được.

**Đăng nhập:** đã một lần (Cognito WORKFORCE SSO). Nhưng có hai app, hai menu, hai host. CIS chỉ deep-link sang Booking qua nhóm "Trade", mà `content_lead` không thấy nhóm này.

### 4.2 Thiếu gì

| # | Thiếu | Hệ quả |
|---|---|---|
| W1 | Booking chỉ cho 1 vai trò mỗi người | Chặn việc làm Content và Booking cùng lúc. Lát 2 (NEW-R1) giải quyết. |
| W2 | Không có danh sách việc cần làm ở đâu cả | Trang phải tự nhớ khoảng 15 trang. |
| W3 | Booking không có list cho vài ô việc | Không có: hoá đơn đến hạn 7 ngày, hợp đồng sắp hết hạn, đặt dịch vụ NCC qua mọi hồ sơ. |
| W4 | Thông báo Booking gửi theo vai trò dựng sẵn | Người giữ vai trò tuỳ chỉnh không nhận thông báo. |
| W5 | Không thấy việc đang chờ người duyệt | Trang không biết việc nào đang chờ owner. Owner không có hộp duyệt. |
| W6 | Từ CIS không có link thẳng sang việc Booking | Chỉ có link chung "Booking admin". |

### 4.3 Trang mới: "My work", hai nửa nối nhau

Bản đọc ban đầu đề xuất một trang CIS đọc Booking qua contract view chéo app (`booking.v_ops_work_queue`). Cách đó cần
thêm grant Infra, isolation probe, contract doc và 2 migration bk-, tức khoảng 1,5–2 phiên cho đúng 1 người dùng. Đề xuất
gọn hơn:

- **CIS `/admin/my-work`** (NEW-W1, S286).
  - Dải Content, mỗi ô gồm số lượng, tuổi của mục cũ nhất và 1 link mở đúng trang đã lọc.
  - Các ô: Review Queue, nội dung NCC còn nháp hoặc thiếu mô tả, AA content nháp, place cards cần xem, giữ text tenant. Khi AA-1148 xong thì thêm: bản nháp của tôi, bị trả lại, tour chưa đủ 100%, tour thiếu ảnh bìa.
  - Là trang đích cho các vai trò content. Admin vẫn vào `/admin/overview`.
  - Hiện theo quyền, không bao giờ theo tên người.
  - Có nút làm mới, không polling. Mặc định tiếng Anh. Dùng UI kit.
  - Có link "Booking: My work".
- **Booking dashboard `app/(staff)/page.tsx`, dải "My work"** (NEW-W2, S287–S289).
  - Đọc bảng của chính Booking, không cần contract chéo app, không cần migration.
  - Ô hiện theo `me.permissions`: đặt dịch vụ NCC cần gửi / đang chờ NCC trả lời, dòng B2B on-request, trip check đến hạn, tour chưa sẵn giá, hợp đồng hết hạn trong 30 ngày (số ngày chỉnh được trong Policy), dừng bán chờ xem, hoá đơn NCC cần nhập / đến hạn 7 ngày / đã duyệt chưa trả, hoá đơn đại lý quá hạn, tiền nhận chờ duyệt.
  - Dải "Đang chờ người khác" (cho người làm) và "Chờ tôi duyệt" (cho owner, đây chính là hộp duyệt) có từ S289.
  - Có link "CIS: My work".
- **Contract view chéo app** chỉ làm khi Trang thấy việc chuyển giữa hai app thật sự vướng (Q8).

### 4.4 Các lát

| Lát | Nội dung | Phiên |
|---|---|---|
| Hôm nay | Bước tay: tài khoản + CIS `content_lead`. Trang làm Content ngay. | S285 |
| W1 | `/admin/my-work` dải Content + trang đích + link sang Booking | S286 |
| W2a | Dải My work trên dashboard Booking (lọc theo quyền) + link về CIS | S287 |
| W2b | Bộ lọc mới (`/billing?due=7d`, "đã duyệt chưa trả", hợp đồng sắp hết hạn, list đặt dịch vụ NCC) + thông báo theo quyền | S288 |
| W2c | "Đang chờ người khác" / "Chờ tôi duyệt" + kiểm bằng view-as | S289 |

Từ S287, khi Trang có vai trò tuỳ chỉnh: buổi sáng mở CIS My work rồi bấm sang Booking My work, cả hai bằng một lần đăng
nhập. AA-1149 làm ô "đặt dịch vụ NCC cần gửi" có ý nghĩa thật. Trước đó ô này chỉ đếm các đặt chỗ làm tay.

---

## 5. Sửa issue cũ

**AA-1150: thu hẹp thành "bước 1"**
- Tiêu đề mới: `[CIS + Booking] Lean staff roles step 1: three people-role presets, finance reads, make/approve capability split, one sign-in`.
- Giữ: preset trên trang Staff, bỏ `content_creator` (danh sách nhóm đã nghỉ), nhãn "Product & operations", L7a (finance đọc `bill`, `pricing`, `supply`, `ops`, `trip_case`, `catalog`; luật trang thêm `F`), tách `supplier.activate` / `contract.publish` / `stop_sale.approve`.
- Built-in `contracting` giữ quyền duyệt để E2E pricing checker và preset "Pricing team" không vỡ.
- Bỏ khỏi Done-when: "sales sees a masked account".
- Bỏ "need" khoá KMS (A1 đã yes).
- Bỏ `payout.write` cho finance (chỉ admin; owner ghi chi trả).
- Thêm vào Done-when:
  - Một người dùng E2E không phải admin đăng nhập một lần, mở được CIS `/admin` và Booking staff mà không bị hỏi đăng nhập lần hai. Lặp lại bằng tài khoản thật của Trang.
  - E2E pricing xanh.
- Chuyển ra ngoài: vai trò tuỳ chỉnh → NEW-R1; view-as → NEW-R2; luật duyệt, owner tự duyệt, hồ sơ NCC, tài khoản ngân hàng → NEW-R3.
- Phiên S287 → **S286**.
- Linear đang để Todo; plan.json còn để Backlog và còn ghi "ma trận 4 vai trò". Sửa cả tiêu chí M-SUP thành "Booking: 3 vai trò người + vai trò tuỳ chỉnh".

**Các issue khác**

| Issue | Sửa |
|---|---|
| AA-1145 | Bỏ ", lean staff roles" khỏi tiêu đề. Verify live R6 rồi Done ở S286. |
| AA-1146 | plan.json: In Review. Đóng phần 1 (D1, D5, CIS 457/458) có bằng chứng. Phần 2 (trang Tour editor) chuyển vào AA-1148. Xoá "need" về trần T2 (A2 đã yes). |
| AA-1148 | Bỏ M0 "Content desk" vì NEW-W1 thay. Bỏ "Content staff work only in CIS" (L1 đã đổi). Giữ "`content_creator` ẩn khỏi Booking". Thêm AA-1146 phần 2. Thêm `photos.upload`, làm sau NEW-R2. Phiên S288–S290. |
| AA-1147 / 1149 / 1151 / 1153 / 1152 | Chuyển phiên: S287 / S288 / S289 / S289 (p1) + S290 (p2) / S290. |
| AA-1140, AA-1154, AA-1141, AA-1142 | S290, S291 (kéo sang sau S292), S291, S292. |
| AA-1121 | Đóng vì trùng, comment trỏ sang AA-1103. Không xoá. AA-1103 nhận phạm vi của nó. |
| AA-1004, 1103, 1122, 1050, 1011, 1117 | Đổi hạn hoặc phiên đã qua (S281–S283) theo cổng thật. |
| AA-790 / 920 / 921 / 1000 | Cổng chỉ còn "mở băng TL-11". |

**plan.json và README** (đồng bộ trong root PR lúc đóng S286)
- plan.json dùng field `session`, không phải `slot`. Bản đọc B nói "slot của AA-1146–1152 là null" là **sai**: AA-1147/1148/1149 = S286, AA-1150/1151/1153 = S287, AA-1152 = S288.
- plan.json local có thay đổi chưa commit (+224/−44). Sửa trên bản local này, đừng dựng lại từ origin, rồi publish lại tracker Q4Lv….
- Đánh Done: AA-1143, 1126, 1144, 1130, 1138, 1128, 1129, 1135.
- Trạng thái: AA-1145, 1146, 1136, 1137 → In Review; AA-1150 → Todo.
- Xoá `needs: "cần xếp slot"` ở AA-1127, 1134, 1136, 1137, 1139, 1122, 1061. Xoá "need" release-please ở AA-1119.
- Đóng milestone M-OD, M-P2, M-R7. Sửa tham chiếu M1b tới AA-1026/AA-998.
- Thêm milestone **M-ROLES** ("Lean permissions + My work", S286–S289).
- Cập nhật `source` và `synced_at`.
- README: thêm dòng S285–S292 ở §3; dựng lại bảng "Open issues by slot" từ Linear; bỏ 18 mục A9 đã duyệt bỏ (C1–C18) ở §2 và ở `waiting`.

**Hồ sơ quyết định**
- Ghi câu trả lời của tech lead vào `decisions5/data.json`: L1 = Trang làm cả Booking (sản phẩm, vận hành, kế toán); L5 = làm vai trò tuỳ chỉnh ngay.
- Thêm ghi chú "đã thay bằng L4" ở `advisory-r3-t13-roles.md` §3.2 (R7).

**Số issue Linear mới: 5** (NEW-R1, R2, R3, W1, W2), giảm từ 9 trong bản nháp đầu. 45 + 5 vẫn xa trần 250. Phải kiểm
project đích còn dưới 100 issue chưa lưu trữ.

---

## 6. Việc cần tech lead quyết

"Trước S286" nghĩa là phải chốt trước khi mở lane S286.

| # | Câu hỏi | Đề xuất | Khi nào cần |
|---|---|---|---|
| Q1 | Trang có vào Booking bằng `contracting` tạm không? | **Không.** S285–S286 chỉ làm Content. Booking bắt đầu bằng vai trò tuỳ chỉnh (S287). Nếu buộc phải sớm hơn: chỉ sau khi AA-1150 tách quyền, tech lead chấp nhận bằng văn bản rằng Trang còn quyền duyệt hoá đơn/giá/mùa/B2B trong 1 phiên, và kiểm audit lúc chuyển vai trò. | Trước S286 |
| Q2 | Booking biết vai trò tuỳ chỉnh và marker business_owner bằng cách nào? | **Phương án A**: contract view CIS `shared.v_staff_booking_grant`, bổ sung ADR 0006. B: Booking tự lưu `custom_role` ở `/staff` của nó. | Trước S286 |
| Q3 | Danh sách quyền Booking của Trang | Như mục 3.3. Cần chốt riêng: có cho báo giá/đặt chỗ đại lý không (`b2b_desk.book`, `trip_case.read/write`, `customer.read/write`)? Đề xuất **có**. | Trước S286 (seed NEW-R1) |
| Q4 | Ai ghi chi trả NCC? | **Business owner** (chị duyệt chuyển khoản thật), có cờ `same_approver_payer`. Tech lead làm dự phòng. Trang không bao giờ ghi. | Trước S288 |
| Q5 | Phạm vi owner tự duyệt | NCC, hợp đồng/giá/mùa, hoá đơn NCC, tài khoản ngân hàng NCC, tín dụng/giảm giá/hoàn tiền đại lý, thông tin chuyển khoản trên hoá đơn đại lý. **Không** gồm luật Pricing › Policy và gỡ dừng bán. | Trước S288 |
| Q6 | "Xem xuống dưới" là gì? | Quyền đọc của vai trò đích là tập con quyền đọc của người xem. Chỉ GET. Log đủ quyền của vai trò đích. | Trước S288 |
| Q7 | Vai trò CIS "Content" của Trang | `content_lead` bỏ `content.settings.write`, thêm `tenant.read`. `reference_price.write` chỉ admin giữ. Kiểm "gates" gồm gì trước khi chốt. | S287 |
| Q8 | My work: hai nửa nối nhau, hay một trang CIS đọc Booking qua contract view? | **Hai nửa** (rẻ hơn khoảng 1 phiên). Chỉ làm view chéo app khi Trang báo thật sự vướng. | Trước S286 |
| Q9 | Bật `sellable` cần giá đã duyệt? | **Có**: phải có phiên bản giá đã duyệt hoặc tour đã sẵn giá. Kiểm readiness hiện có trước khi viết code. | S288 |
| Q10 | Trang nhập tài khoản ngân hàng NCC sau S289? | **Có**: chỉ nhập, chờ owner duyệt + gọi lại xác nhận + khoá 24 giờ. | S289 |
| Q11 | Vai trò tuỳ chỉnh cho CRM | Không làm editor. Hiện 3 nhóm CRM ở dạng đọc trên ma trận. | S287 |
| Q12 | Tạo 5 issue Linear mới + gộp AA-1121 vào AA-1103 + milestone M-ROLES | **Có.** | Trước S286 |

Gợi ý: gom Q1–Q12 vào một trang quyết định bấm chọn (lưu DB) như các trang S285, mỗi câu có sẵn đề xuất. Trong lúc chờ
NEW-R1 có trang ma trận thật, có thể publish ma trận `permmap/lean.json` thành trang đọc ngay ở S286, không tốn code.

**Tiền:** không có chi phí mới. Khoá KMS khoảng 1 USD/tháng (A1), AA-788 ≤5 USD, AA-1051 T2 ≤4,8 USD đều đã duyệt.
Các lát phân quyền và My work không dùng dịch vụ AWS mới nào, không có lượt chạy trả phí.
