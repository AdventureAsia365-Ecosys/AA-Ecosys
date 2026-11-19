# Phản biện chung: content, hoạt động tuỳ chọn, khách sạn

## Phản biện 3 bản tư vấn (kiến trúc sư trưởng, chỉ đọc)

### Content editing
- **Hai câu không có cơ sở trong code.** Câu "chọn nhà cung cấp AA từ view nhà cung cấp của Booking" và câu đổi `raw_tours.provider` thành ID nhà cung cấp đều chưa có chỗ dựa. `booking.suppliers` chỉ grant cho `booking` (`docs/architecture/db-schema-reference.md:3376-3413`). `provider` hiện là varchar tự do (`db-schema-reference.md:14979`).
  - **Sửa:** Booking viết migration bk-NNN tạo view thư mục nhà cung cấp (id, tên, status, không có giá net) và grant cho `cis_app`.
  - Tour gắn nhà cung cấp qua `booking.trip_plans` (`trip_plan.write`, `apps/AA-Booking/backend/app/auth/staff.py:118-119`). CIS chỉ giữ soft key, không có FK sang schema khác.
- **Câu 3 (T2 và Facts Entries của đại lý) trái luật (a).** Đề xuất "giữ quyền sửa giọng văn T2" phải để business owner chốt, không nên coi là mặc định.
  - **Sửa:** chỉ đổi phần trình bày (logo, giọng) ở tầng tenant, không bao giờ chảy ngược về catalogue.
  - Facts Entries chỉ giữ markup và điều khoản bán. Mọi sự thật sản phẩm (giá, lịch trình) do AA cấp.
- **Chưa thống nhất vai trò.** Nhân viên content là `content` ở CIS nhưng là `content_creator` ở Booking (`staff.py:72`). Cần ghi rõ một người giữ cả hai nhóm Cognito.

### Hoạt động tuỳ chọn
- **Đúng hướng.** `services.supplier_id` NOT NULL; `destination_id` là soft key tới `catalog.v_destination` (`apps/AA-Booking/CONTEXT.md:1665`). Cùng không gian khoá với `v_tour_place` và `v_tour_day_route`, nên ghép ngày với địa điểm là khả thi.
- **Chặn đại lý chưa đủ.** Phương án dựa vào ADR 0019 b6 (`docs/adr/0019-b2b-only-ecosystem-model.md:310`), nhưng b6 vẫn cho đại lý thêm transfer, flight, visa của riêng họ. Điều này trái luật (a) theo nghĩa đen. Hiện `add_agency_option` không kiểm loại block (`apps/AA-Partner/api/app/proposals/builder.py:1352-1370`).
  - **Sửa:** sửa ADR 0019 b6 theo quyết định 19/11 (b6 ghi "business owner may revisit"). Business owner chốt danh sách ngoại lệ, nếu có.
- **Grant `v_supply_content` cho `tripplanner`:** do CIS sở hữu (`catalog_owner`), nên migration CIS là đúng.

### Khách sạn
- **Vai trò "ops" không tồn tại.** Booking chỉ có admin, sales, contracting, content_creator, finance (`staff.py:72`). **Sửa:** giao stop-sale cho contracting, hoặc tạo vai trò mới có quyết định rõ.
- **Bước R chặn quá ít.** Bước này chỉ bỏ accommodation, activity, dmc. Nhưng `crm.agency_supplier` còn transport, guide, restaurant, other (`db-schema-reference.md:5407`, khoảng 63 dòng). Cần chung một luật với phần hoạt động (xem ý dưới).

### Mâu thuẫn giữa các bản
1. **Giá trẻ em có hai mô hình.** Phần hoạt động thêm `supplier_rates.pax_type`. Phần khách sạn thêm `extra_bed_child` và `hotel_child_policies`.
   - **Sửa:** `pax_type` dùng cho dịch vụ tính theo người. Bảng chính sách trẻ em dùng cho phòng. Engine áp một thứ tự ưu tiên duy nhất.
2. **Điều khoản huỷ có hai dạng.** Phần hoạt động dùng `cancellation_terms` dạng text trên offer. Phần khách sạn dùng `cancellation_tiers` jsonb trên hợp đồng.
   - **Sửa:** dùng bậc có cấu trúc trên hợp đồng; offer chỉ được ghi đè.
3. **Stop-sale có hai bảng.** `hotel_restrictions` chỉ cho khách sạn, còn hoạt động dùng lịch mùa.
   - **Sửa:** một bảng restriction và allotment chung, khoá theo component (`rt:` hoặc `sv:`).
4. **Chặn đại lý có hai cách.** Một bên bỏ category khỏi `agency_supplier`, một bên giới hạn block theo b6.
   - **Sửa:** gộp thành một PR CRM với một danh sách duy nhất, đi kèm bản sửa ADR 0019.

### Bức tranh thống nhất
- **Booking là nguồn cung duy nhất.** Gồm nhà cung cấp AA, hợp đồng và giá (maker-checker), service `activity` kèm `addon_offers`, khách sạn và loại phòng, restriction và allotment. Mọi thứ bán được đều có `supplier_id` của AA.
- **CIS sở hữu nội dung.** Gồm tour (raw, phiên bản AI viết, Master, atom) qua Tour editor có phiên bản, và mô tả, ảnh của khách sạn, hoạt động qua `/admin/supply-content`. Nhân viên content AA là người sửa.
- **Địa điểm** dùng chung `catalog.v_destination` (CIS) làm soft key.
- **TripPlanner chỉ đọc view:** `v_tour_place`, `v_place_addons`, `v_from_prices`, `v_supply_content`.
- **CRM và đại lý** chỉ báo giá qua `booking.b2b.v1` bằng component `rt:`, `sv:`, `tp:`. Đại lý không ghi gì vào catalogue, chỉ đặt markup.
- **Mỗi app chỉ migrate schema của mình.** View cho app khác do app chủ tạo và grant.

**Chưa kiểm:** số dòng thật của service `activity` và khách sạn trên Dev; phạm vi của Facts Entries.
