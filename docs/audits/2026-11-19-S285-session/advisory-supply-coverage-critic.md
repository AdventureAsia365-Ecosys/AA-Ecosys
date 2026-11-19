# Phản biện: nguồn cung trọn gói và dịch vụ riêng của đại lý

# Phản biện 2 bản tư vấn: nguồn cung Booking và dịch vụ riêng của đại lý

## Lỗi và cách sửa

1. **Mục A của bản Booking không chạy được như đang viết.** Bản tư vấn ghi "chưa kiểm unique". Thực tế đã có index `supplier_bookings_item_live_uq`, là UNIQUE trên `version_item_id` khi trạng thái là pending/requested/confirmed (`docs/architecture/db-schema-reference.md:3174`). Vì vậy mỗi dòng `tp:` chỉ được có 1 đặt dịch vụ đang sống, không tách ra N cái được.
   - **Sửa:** thêm cột `version_component_id`, FK tới bảng snapshot, và chuyển ràng buộc unique sang cột này. Đây là migration bk-NNN nên cần review trước khi merge.
2. **Câu "mỗi loại đã có bảng, màn hình" nói quá.** Xe, hướng dẫn viên, vé, ăn uống, hoạt động dùng chung một bảng `booking.services` và chỉ phân biệt bằng `service_type` (`db-schema-reference.md:2977`). Riêng ăn uống chưa có thực thể nhà hàng.
   - **Sửa:** viết lại thành "khách sạn có bảng riêng, 5 loại còn lại chung bảng `services`".
3. **Mục G của bản Booking ghi "chưa kiểm aa_request", trong khi bản CRM đã có bằng chứng.** Các query đồng bộ lọc `supplier_kind = 'aa'` (`apps/AA-Partner/api/app/booking/sync.py:126,190,207`). Riêng chỗ INSERT `aa_request` (`sync.py:183`) thì không có ràng buộc DB nào kiểm loại dòng.
   - **Sửa:** test guard thuộc AA-Partner, không thuộc Booking. Bỏ câu này khỏi bản Booking.
4. **Mâu thuẫn với phản biện sáng nay.** Bản phản biện sáng (`advisory-content-activities-hotels-critic.md:7`) coi `booking.trip_plans` là chỗ gắn tour với nhà cung cấp. Câu 1 của bản Booking lại đề xuất hạ `trip_plans.supplier_id` xuống "đầu mối vận hành".
   - **Sửa:** ghi rõ là theo luật (a), nhà cung cấp gắn theo từng thành phần (`trip_plan_components`). Soft key `raw_tours.provider` bên CIS chỉ để hiển thị. Cập nhật phản biện sáng cho khớp.
5. **Trạng thái "operable" (mục B) còn thiếu.**
   - Số đêm cần khách sạn là số ngày − 1, không phải số ngày.
   - Cần tính cả stop-sale và allotment theo bảng restriction chung mà phản biện sáng đề xuất (`critic.md:31`).
6. **CRM đang có lối lách qua `other`.** Block type đang có `other` (`apps/AA-Partner/api/app/proposals/rules.py:27`), và bản CRM giữ `other` trong `agency_supplier`. Đại lý vẫn có thể bán khách sạn dưới nhãn `other`.
   - **Sửa:** `category` của dòng agency là danh sách đóng, không có `other`. `add_agency_option` chỉ nhận block `extras`. `other` chỉ còn ở danh bạ nhà cung cấp.
7. **Transfer cần chốt mặc định là chặn, không để treo "chờ chốt".** Business owner đã kể "xe đi lại" là một thành phần của tour. Booking đã có `service_type = 'transfer'`, nên xe đón sân bay trước hoặc sau tour AA bán được dưới dạng `sv:`.
   - Bỏ `transfer` khỏi `agency_service_category_chk` (`db-schema-reference.md:5348`).
   - Bỏ các cách tính số lượng kiểu khách sạn `per_room`, `per_night`, `per_person_night` khỏi `agency_service`.
   - `advisory-optional-activities.md:123` (danh sách b6 có transfer) đã cũ, cần sửa theo.
8. **Đã kiểm thêm phần tích hợp ngoài.** Grep AA-Partner tìm amadeus, sabre, travelport, duffel, gds: 0 file. Câu "3 file GDS" trong bản Booking không áp cho CRM.

## Danh sách luật cuối (để sửa ADR 0019 b6)

**Chặn với đại lý.** Phải là thành phần AA `rt:`, `sv:` hoặc `tp:`, có nhà cung cấp AA:
- Khách sạn, kể cả đêm trước hoặc sau tour.
- Xe và đưa đón, cả trong tour lẫn sân bay.
- Hướng dẫn viên.
- Vé tham quan.
- Ăn uống, nhà hàng.
- Hoạt động.
- DMC, tour trọn gói.
- Mọi thứ trên khi ghi dưới nhãn `other`.

**Cho phép làm dòng riêng của đại lý (nhập tay):**
- `flight`: vé máy bay, PNR, e-ticket.
- `visa`: hồ sơ, thư mời, phí visa.
- `insurance`: bảo hiểm du lịch.
- `fee`: phí dịch vụ của đại lý.

**Điều kiện cho các dòng riêng này:**
- Không gọi API ngoài.
- Không bao giờ đồng bộ sang Booking hoặc ops release.
- Không ghi vào schema `booking`.
- Đại lý chịu trách nhiệm (b5).
- PDF tách thành nhóm riêng.

**Business owner còn cần chốt:**
- `insurance` và `fee`. Luật (b) chỉ nêu vé máy bay và visa làm ví dụ. Đề xuất: giữ.
- Transfer. Đề xuất: chặn.

**Phân công app:** Booking làm A–F (bk-NNN). AA-Partner làm phần CRM (crm-NNN). CIS không đổi.
