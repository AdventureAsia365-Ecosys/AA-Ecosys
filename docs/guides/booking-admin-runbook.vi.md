---
id: GUIDE-12-booking
title: Runbook Booking admin
description: Cách nhân sự kinh doanh, hợp đồng và nội dung của Adventure Asia vào Booking admin, mỗi vai trò Booking làm được gì, các luồng hằng ngày từ yêu cầu tới trip case, báo giá, đặt nhà cung cấp, hoá đơn và thanh toán, và xem ở đâu khi có gì đó sai.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-booking-admin, aa-booking-api]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-cis-admin, GUIDE-12-tripplanner, GUIDE-04, OPS-04, AA-1020]
lang: vi
translation_of: docs/guides/booking-admin-runbook.md
---

# Runbook Booking admin

Thuộc bộ [truy cập và vận hành các ứng dụng](app-access-and-operations.vi.md). Đây là bản tiếng Việt của
[booking-admin-runbook.md](booking-admin-runbook.md).

## 1. Ai dùng

Booking admin là nơi nhân sự Adventure Asia xử lý từng yêu cầu của khách du lịch: khách hàng, trip case, báo giá và giá,
việc đặt nhà cung cấp, hoá đơn và các bước kiểm trước khởi hành. Nhân sự kinh doanh, hợp đồng và nội dung dùng trang
này; chủ doanh nghiệp mở được khi có vai trò Booking. Khách du lịch không bao giờ đăng nhập ở đây: họ lên kế hoạch trên
[TripPlanner](tripplanner-runbook.vi.md), và khách du lịch đã đăng nhập khi gửi chuyến đi sẽ xem yêu cầu thanh toán
của chuyến đó ở đó.

## 2. Địa chỉ

| Trang | Địa chỉ Dev |
|---|---|
| Booking admin | `https://booking.lumiguides.it.com` (mở trang đăng nhập) |
| Health của API, cho kỹ sư | `https://api-booking.lumiguides.it.com/booking/health` |

## 3. Lấy tài khoản

Booking admin dùng **cùng tài khoản nhân sự với CIS admin**.

1. Xin quyền từ một chủ nền tảng (hiện là tech lead).
2. Chủ nền tảng mở CIS admin › **Platform › Staff**, thêm bạn hoặc mở dòng của bạn, và đặt **Booking role**: Booking
   admin, Sales, Contracting hoặc Content creator.
3. Nếu bạn là người mới, bạn nhận được e-mail mời. Vai trò Booking được đọc lại ở mỗi lần đăng nhập, nên thay đổi có
   hiệu lực từ yêu cầu tiếp theo của bạn.

Trang **Staff** của Booking hiện cùng những người đó. Vai trò chỉ đổi trong CIS; một Booking admin có thể tạm khoá hoặc
kích hoạt lại một người trong Booking.

## 4. Đăng nhập và đăng xuất

1. Mở `https://booking.lumiguides.it.com`.
2. Chọn **Sign in with company email**, nhập e-mail công việc, rồi nhập mã dùng một lần trong e-mail.
3. Đăng xuất từ menu tài khoản. Không có mật khẩu.

Một tài khoản không có vai trò Booking bị từ chối kèm thông báo; hãy xin chủ nền tảng một vai trò.

## 5. Vai trò

| Vai trò | Làm được gì |
|---|---|
| **Booking admin** | Mọi thứ, gồm **Staff**, **Audit Log**, xác minh thanh toán, đối tác B2B, và trạng thái Booking của các nước và điểm đến |
| **Sales** | Trip case, khách hàng và báo giá (đọc và ghi), giá và biên lợi nhuận (đọc), đặt nhà cung cấp và kiểm trước chuyến đi, hoá đơn và thanh toán |
| **Contracting** | Đọc trip case và khách hàng; ghi nhà cung cấp, khách sạn, dịch vụ, giá và hợp đồng, quy tắc giá và tỷ giá, dòng thương mại của một trip plan, hoá đơn nhà cung cấp; đặt nhà cung cấp và kiểm trước chuyến đi. Không xem tiền của khách hàng |
| **Content creator** | Danh mục từ CIS (trip plan, điểm đến, nước) không kèm giá |

Quy tắc hai người (maker-checker): một quy tắc giá, tỷ giá hay hợp đồng nhà cung cấp được duyệt bởi người khác với
người tạo; một khoản thanh toán được xác minh bởi một Booking admin khác với người đã ghi nhận nó; một hoá đơn nhà cung
cấp được duyệt bởi người khác với người đã nhập.

## 6. Menu

- **Overview**: **Dashboard**.
- **Sales**: **Trip Cases**, **Proposals**, **Customers**, **Pricing calculator**.
- **Operations**: **Payments & Invoices**, **Trip Checks**, **B2B desk**.
- **Supply**: **Suppliers**, **Hotels**, **Services**, **Pricing rules & FX**.
- **Catalog (from CIS)**: **Trip Plans**, **Destinations**, **Countries**.
- **Admin**: **Staff**, **Audit Log**.

**Settings** nằm ở chân menu và trong menu tài khoản; **Notifications** là chuông trên thanh trên cùng.

## 7. Việc hằng ngày

### Có một yêu cầu mới

1. Một khách du lịch gửi chuyến đi từ TripPlanner bằng **Send to an advisor**. Booking tự nhận và gửi nhân sự một
   e-mail "new inquiry".
2. Mở **Trip Cases**, tab **Inquiries** (hoặc **Unassigned**). Mở case.
3. Đặt **Sales rep** và kiểm thông tin chuyến đi và khách hàng.

Một yêu cầu qua điện thoại hoặc e-mail: **Trip Cases › New trip case** (hoặc **New lead**), hoặc bắt đầu từ một trip
plan bằng **Use for trip case**.

### Dựng và gửi báo giá

1. Trong case, tab **Proposals**, chọn **New proposal**. Thêm ngày và mục (**Add item**, **Add item on day**), hoặc
   **Start from a trip plan**.
2. Kiểm **Price**; **Pricing calculator** cho thấy giá được tính thế nào.
3. **Preview** những gì khách sẽ thấy, rồi **Send to customer**.
4. Muốn đổi sau khi đã gửi: một **New version**. Một phiên bản đã gửi hoặc đã duyệt giữ nguyên những gì khách đã thấy.
5. Khi khách đồng ý (qua e-mail, điện thoại hoặc trực tiếp), chọn **Record approval** kèm ghi chú về cách khách đã
   đồng ý. Phiên bản bị khoá và chuyến đi được xác nhận; các bước kiểm chuẩn được thêm vào.

### Đặt nhà cung cấp

1. Trong case, tab **Suppliers**, tạo các booking nhà cung cấp cho phiên bản đã duyệt.
2. Gửi yêu cầu từng booking tới nhà cung cấp và nhập mã tham chiếu của nhà cung cấp khi họ xác nhận. Một booking bị từ
   chối được thay bằng nhà cung cấp khác.
3. **Items without a live booking** liệt kê những gì còn thiếu.

### Hoá đơn và thanh toán (B2C)

1. Trong case, tab **Billing**, tạo hoá đơn từ phiên bản đã duyệt: tiền cọc và phần còn lại theo cài đặt.
2. Gửi hoá đơn. Khách du lịch chỉ thấy nó trên TripPlanner trong **My trips** khi họ đã đăng nhập lúc gửi chuyến đi.
   Với chuyến đi gửi ở dạng khách vãng lai (case hiện khách hàng là **Unverified**), hãy tự gửi yêu cầu thanh toán qua
   e-mail: nó không bao giờ hiện trong **My trips**, kể cả khi khách du lịch đăng nhập sau đó.
3. Khi tiền về: **Record payment** (ở đây hoặc trong **Payments & Invoices**).
4. Một Booking admin không phải người đã ghi nhận mở khoản thanh toán và chọn **Verify payment**. Chỉ tiền đã xác minh
   mới đánh dấu hoá đơn là đã trả.

### Trước khởi hành

1. Mở **Trip Checks** (hoặc tab **Checks** của case). Mỗi chuyến đi đã xác nhận có ba bước kiểm chuẩn (kiểm lại trước
   chuyến đi, người liên hệ khẩn cấp, bảo hiểm) cộng các bước bạn thêm bằng **Add check**.
2. Đánh dấu từng bước đã xong hoặc không áp dụng. Case tự chuyển sang chuẩn bị khởi hành, đang đi và hoàn tất khi nhà
   cung cấp đã được đặt và, với B2C, hoá đơn đã trả; một lần chuyển bị chặn sẽ tạo thông báo.

### Đặt chỗ của đại lý (B2B)

Đại lý đối tác đặt tour Adventure Asia từ CRM của họ. Các dòng cần nhà cung cấp trả lời hiện ở **B2B desk**: xác nhận
hoặc từ chối booking nhà cung cấp trên tab **Suppliers** của case, và dòng của đại lý cập nhật theo.

### Nguồn cung và giá (hợp đồng)

1. **Suppliers** › **Add supplier**, rồi **New contract** và giá; **Hotels** (loại phòng) và **Services**.
2. Mô tả khách sạn và dịch vụ là nội dung: **Edit in CIS** mở chúng trong CIS admin (**Supply (Booking)**).
3. **Pricing rules & FX**: **New rule**, **New FX rate**. Một người khác duyệt dòng đó.
4. Hoá đơn nhà cung cấp: **Enter bill** trên nhà cung cấp; một người khác duyệt; một Booking admin ghi nhận khoản chi
   trả.

## 8. Khi có gì đó sai

| Bạn thấy | Sau đó |
|---|---|
| Chuông có thông báo, ví dụ một lần chuyển trạng thái chuyến đi bị chặn | Mở thông báo; nó nêu case và lý do |
| "Too many sign-in attempts" | Chờ hết thời gian được nêu, rồi thử lại |
| Một trang không tải được dữ liệu | Kiểm `https://api-booking.lumiguides.it.com/booking/health`, hoặc CIS admin › **Apps** (dòng Booking); gửi ảnh chụp màn hình kèm thời điểm |
| Một yêu cầu từ TripPlanner không tới | Kỹ sư trực kiểm báo cáo bàn giao yêu cầu ở CIS admin › **Reports** |
| Một thông báo quyền (ví dụ "Billing needs the billing role") | Vai trò của bạn không bao gồm việc đó; hãy hỏi chủ nền tảng |

Trong giai đoạn dev, tech lead là kỹ sư trực: Jira cho lỗi thông thường, nhắn trực tiếp khi khẩn. Rollback dành cho kỹ
sư: [rollback Booking](../ops/runbooks/rollback-booking.md).

## 9. Lưu ý giai đoạn Dev

- Chỉ có dữ liệu thử: khách hàng và case trên Dev là được tạo ra.
- Không có thanh toán thẻ: thanh toán được ghi nhận và xác minh bằng tay. Hoá đơn là yêu cầu thanh toán tạm tính; hoá
  đơn VAT hợp pháp nằm ngoài Booking.
- Trang **Staff** chỉ phản chiếu CIS; đổi vai trò trong CIS.

## Nguồn (cho người bảo trì)

Đọc từ AA-Booking `main` ngày 01/11/2026: `frontend/ui/local/nav.tsx` (menu), các thư mục route `(staff)` và nhãn của
chúng, `CONTEXT.md` ("Staff authentication and permissions", "Supplier bookings", "Trip checks and the case
lifecycle", "Invoices and manual payments"); AA-CIS-App `frontend/app/admin/platform/staff/messages.ts` (vai trò
Booking). Quyết định: ADR gốc 0004, 0005, 0006 và 0006a. Giữ trang này khớp với
[booking-admin-runbook.md](booking-admin-runbook.md).
