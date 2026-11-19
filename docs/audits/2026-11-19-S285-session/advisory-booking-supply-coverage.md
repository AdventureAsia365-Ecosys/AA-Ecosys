# Quản lý nhà cung cấp trong AA-Booking: đã đủ cho tour trọn gói chưa?

## 1. Trả lời ngắn

Gần đủ về khung, nhưng chưa vận hành trọn vẹn được một tour đã bán.

- **Đã có:** Booking có đủ 6 loại thành phần: khách sạn, xe, hướng dẫn viên, vé tham quan, ăn uống, hoạt động. Mỗi loại đã có bảng, màn hình, giá net, import Excel, đặt dịch vụ với nhà cung cấp, voucher, hoá đơn và chi trả.
- **Lỗ hổng lớn nhất:** khi đại lý đặt cả một tour (dòng `tp:`), nút Generate không tách tour ra thành từng đặt dịch vụ với nhà cung cấp. Ops phải thêm tay từng cái.
- **Còn thiếu dữ liệu chi tiết:**
  - Xe: loại xe, số chỗ, tuyến đường.
  - Hướng dẫn viên: ngôn ngữ.
  - Giá trẻ em ở phía nhà cung cấp.
  - Nhà hàng và thực đơn.
  - Phụ thu khách sạn.
  - Hồ sơ nhà cung cấp: tài khoản ngân hàng, mã số thuế, nhiều người liên hệ.

**CRM:** đại lý đang ghi tay dịch vụ riêng (vé máy bay, visa) dưới dạng bản ghi có cấu trúc kèm tài liệu. Không thấy code tích hợp GDS. Cách làm này đúng với luật (c).

## 2. Hiện trạng

| Phần | Trạng thái | Bằng chứng / thiếu gì |
|---|---|---|
| Nhóm nhà cung cấp | Có | 6 nhóm hotel/transport/guide/entrance/activity/meal (`docs/architecture/db-schema-reference.md:3404`) |
| Hồ sơ nhà cung cấp | Một phần | Chỉ 1 người liên hệ. Không có ngân hàng, mã số thuế (`db-schema-reference.md:3376-3413`) |
| Hợp đồng | Có, kèm maker-checker | `payment_terms` và `cancellation_policy` là văn bản tự do (`db-schema-reference.md:3208-3244`). Chưa upload được file hợp đồng (`apps/AA-Booking/CONTEXT.md:2207`) |
| Giá net theo đơn vị | Có | 5 đơn vị room_night/person/group/vehicle/day (`db-schema-reference.md:3367`) |
| Mùa | Một phần | Mùa chỉ là nhãn chữ cộng ngày hiệu lực. Lịch mùa của hợp đồng chưa được bảng tính giá đọc (`CONTEXT.md:1051`) |
| Giá trẻ em | Một phần | Chỉ có ở phía bán, tính bằng % giá người lớn (`apps/AA-Booking/backend/app/catalog/cost_sheet.py:579-592`). Phía nhà cung cấp chỉ có ghi chú (`frontend/app/(staff)/suppliers/_parts/RateDrawer.tsx:168`) |
| Khách sạn, hạng phòng | Có | Thiếu phụ thu, giường phụ, chính sách trẻ em, allotment (`db-schema-reference.md:2040-2110`) |
| Xe / đưa đón | Một phần | Thuộc `services.service_type='transfer'`. Không có loại xe, số chỗ mỗi xe, tuyến đi/đến (`db-schema-reference.md:2937-2978`) |
| Hướng dẫn viên | Một phần | Không có ngôn ngữ |
| Vé tham quan | Một phần | Chỉ một giá mỗi người, không tách người lớn/trẻ em |
| Ăn uống | Một phần | Không có thực thể nhà hàng hay thực đơn, chỉ có `inclusions[]` |
| Hoạt động | Có | Theo person/group |
| Import bảng giá | Có | Chỉ định giá cho khách sạn/dịch vụ đã có sẵn (`backend/app/supply/rate_sheet.py:1-25`) |
| Thành phần tour theo ngày | Có | `trip_plan_components` + bộ gợi ý (`db-schema-reference.md:3738-3753`; `CONTEXT.md:958-970`). Thiếu số lượng, ghi chú, giờ |
| Kiểm "đủ nhà cung cấp" | Một phần | Có trạng thái giá `missing_rates` (`CONTEXT.md:915-928`). Chưa kiểm mỗi đêm đã có khách sạn, mỗi ngày đã có xe |
| Đặt dịch vụ + voucher | Có cho từng dòng | Dòng tour `tp:` không được tách: `apps/AA-Booking/backend/app/b2b/holds.py:888-904` ghi room/service bằng NULL, `backend/app/ops/supplier_bookings.py:142` bỏ qua dòng đó |
| Đơn đặt hàng (PO), hoá đơn, chi trả | Có | `db-schema-reference.md:3040-3336`. Hạn thanh toán nhập tay, không suy từ hợp đồng |
| Chi phí chung của đoàn khởi hành cố định | Có | Nhập tay theo từng chuyến, không lấy từ thành phần tour (`backend/app/finance/departure_costs.py:1-25`) |
| `trip_plans.supplier_id` | Chỉ để hiển thị | Pricing, ops và finance không đọc cột này (`backend/app/catalog/trip_plans.py:632-640`) |

**CRM (để đối chiếu luật b, c):**

- `crm.agency_service` có các nhóm flight/insurance/visa/transfer/fee, giá net/bán và cách tính số lượng (`db-schema-reference.md:5322-5348`).
- `crm.agency_supplier` có nhóm flight và visa (`:5407`).
- `crm.visa_application` có checklist và mẫu (`:10456-10521`).
- `crm.traveler_flight` lưu số hiệu chuyến bay, sân bay, giờ. Người nhập là khách hoặc nhân viên đại lý (`:9895-9917`).
- `crm.document` (`:6592`).

Tất cả là nhập tay, không gọi API ngoài.

## 3. Chuẩn thị trường

- **Tourplan, Lemax:**
  - Mỗi "product" của nhà cung cấp có loại (accommodation, transfer, guide, entrance, meal), các thuộc tính theo loại và "rate type" theo loại khách (adult/child/infant), kèm mùa và phụ thu.
  - Tour trọn gói là một bộ thành phần theo ngày. Khi xác nhận bán, hệ thống tự tách ra thành từng service line, gửi nhà cung cấp, sinh voucher, rồi đối chiếu với hoá đơn.
  - Nhà cung cấp có nhiều người liên hệ theo vai trò (reservations, accounts), có ngân hàng và mã số thuế. Điều khoản thanh toán có cấu trúc (đặt cọc, số ngày trước dịch vụ).
- **Bókun:** tách vé theo loại khách và chọn xe theo sức chứa.
- **TravelJoy, Tern, Travefy, Umapped:** vé máy bay và visa là mục tự nhập trong lịch trình, kèm file đính kèm. Tích hợp GDS là tuỳ chọn, thường qua công cụ bên ngoài. CRM hiện tại đã theo đúng mẫu này.

## 4. Khuyến nghị và thiết kế

Mọi thay đổi dưới đây thuộc **AA-Booking** (schema `booking`, migration `bk-NNN`). Không tích hợp hệ thống ngoài. CRM giữ nguyên.

**A. Tách tour thành từng đặt dịch vụ (ưu tiên 1, vì luật a).**

- Khi version được duyệt và có dòng tour (`source_tour_id` có giá trị, room/service NULL), Generate đọc `trip_plan_components` của plan đó. Mỗi thành phần sinh một `supplier_bookings`:
  - `service_date` = ngày bắt đầu + `day_no` − 1.
  - `version_item_id` = dòng tour.
  - Giá chọn bằng `supply/rates.py`.
- Chụp lại (snapshot) danh sách thành phần lúc bán vào bảng mới `booking.trip_case_version_components`, gồm item_id, day_no, room/service, qty, rate_id. Như vậy sửa plan về sau không làm đổi đơn đã bán.
- **Chưa kiểm:** bảng có ràng buộc unique trên `version_item_id` hay không.
- Đoàn khởi hành cố định: thêm nút "Lấy từ thành phần tour" ở màn hình chi phí chung của chuyến.

**B. Trạng thái "operable".**

- Thêm vào danh sách readiness một trạng thái mới: mỗi đêm có một khách sạn và mỗi thành phần đều có giá đã publish và còn hiệu lực trong suốt cửa sổ bán.
- Plan chưa operable thì không bán được qua B2B. Admin được override nhưng phải ghi lý do.

**C. Thuộc tính theo loại dịch vụ** (cột nullable trên `booking.services`, có CHECK theo `service_type`, không dùng JSONB):

- Xe: `vehicle_type`, `seats_per_vehicle`, `route_from_destination_id`, `route_to_destination_id`.
- Hướng dẫn viên: `languages text[]`.
- Ăn uống: `meal_kind` (lunch/dinner/set), `menu_name`. Nhà hàng chính là nhà cung cấp nhóm meal.
- Thêm cột `qty` vào `trip_plan_components`. Với xe, số xe = ceil(pax / seats_per_vehicle), tính lúc tách tour.
- Thêm các cột tương ứng vào các sheet Transport/Guide/Meal của file import.

**D. Giá theo loại khách.**

- Thêm `supplier_rates.pax_type` adult/child/infant cộng `age_min`/`age_max` cho đơn vị person. Cách này khớp `docs/audits/2026-11-19-S285-session/advisory-optional-activities.md:79` và `advisory-content-activities-hotels-critic.md:25-33`.
- Bảng tính giá dùng giá trẻ em của nhà cung cấp nếu có, nếu không thì lấy `child_pct`.
- Phụ thu, giường phụ, allotment của khách sạn làm theo `advisory-hotels.md:69-116`.

**E. Hồ sơ nhà cung cấp.**

- `booking.supplier_contacts`: nhiều người, role reservations/accounts/emergency. PO gửi tới người liên hệ reservations.
- Thêm `tax_id` vào `suppliers`.
- `booking.supplier_bank_accounts`: số tài khoản mã hoá. Chỉ role finance/admin xem được. Đổi tài khoản phải qua maker-checker (chống gian lận đổi tài khoản).
- Điều khoản thanh toán có cấu trúc trên hợp đồng: `deposit_pct`, `balance_due_rule` (days_before_service hoặc days_after_bill), cùng mô hình hạng huỷ theo critic. Hạn thanh toán của hoá đơn lấy mặc định từ hợp đồng.

**F. Quyền.** Thêm role `ops` cho đặt dịch vụ, voucher, PO (critic `:20` ghi chưa có role này). Hợp đồng và giá giữ ở role contracting.

**G. CRM (luật b, c).**

- Giữ cách ghi tay hiện tại: `agency_service` + `agency_supplier` + `visa_application` + `traveler_flight` + `document`.
- Nguyên tắc: các dòng dịch vụ của đại lý không bao giờ được gửi vào yêu cầu gửi AA và không được ghi vào schema `booking`. Chưa kiểm luồng `aa_request`, cần một test guard cho việc này.

## 5. Lộ trình

Chi phí hạ tầng của cả lộ trình là 0 USD: không có dịch vụ AWS mới, không gọi LLM.

| Phiên | Việc giao được | Ngày công |
|---|---|---|
| 1 | A: bảng snapshot + tách tour trong Generate + test + hiển thị ở tab Suppliers | 2–2.5 |
| 1 | B: trạng thái operable + chặn bán B2B | 1 |
| 2 | C: thuộc tính theo loại dịch vụ + `qty` + số xe + cột import | 2.5–3 |
| 2 | D: `pax_type` trên giá + bảng tính giá + sheet import | 2 |
| 3 | E: contacts, `tax_id`, ngân hàng (mã hoá, maker-checker), điều khoản có cấu trúc, hạn thanh toán của hoá đơn | 3 |
| 3 | F: role `ops`; G: test guard cho CRM | 1 |
| 4 | Phụ thu khách sạn, allotment (theo advisory-hotels) | 3 |

Tổng cộng khoảng 14–15 ngày công, chia 4 phiên.

## 6. Câu cần chốt

1. **(Business owner)** Có tour nào AA mua trọn gói từ một DMC địa phương với một giá cả tour không? *Đề xuất:* không. Mỗi tour phải có đủ thành phần. Bỏ `trip_plans.supplier_id` khỏi màn hình hoặc đổi tên thành "Đầu mối vận hành", chỉ để hiển thị.
2. **(Business owner)** Tour chưa đủ nhà cung cấp cho mọi thành phần thì chặn bán hẳn hay chỉ cảnh báo? *Đề xuất:* chặn với B2B. Admin override được, phải ghi lý do.
3. **(Tech lead)** Lưu tài khoản ngân hàng của nhà cung cấp trong Booking? *Đề xuất:* có, mã hoá, chỉ finance/admin xem, đổi tài khoản phải qua maker-checker.
4. **(Tech lead)** Tách tour lúc version được duyệt, với snapshot cố định? *Đề xuất:* có. Sửa plan về sau không ảnh hưởng đơn đã bán.
5. **(Tech lead)** Giá trẻ em: dùng giá của nhà cung cấp, nếu không có thì lấy % giá bán? *Đề xuất:* có.
6. **(Tech lead)** Thêm role `ops`? *Đề xuất:* có.

**Chưa kiểm:**
- Số dòng thật trên Dev.
- Backlog/Linear đã có việc "tách tour" hay chưa.
- Luồng `aa_request` của CRM có gửi kèm dịch vụ riêng của đại lý hay không.
- Grep GDS chỉ ra 3 file. Theo tên file thì có vẻ chỉ là mã sân bay IATA, nhưng chưa đọc nội dung các file đó.
