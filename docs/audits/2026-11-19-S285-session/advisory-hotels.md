# PR-30: dữ liệu khách sạn so với PRD AAA/Quanskill và chuẩn thị trường

# PR30 Khách sạn: so với PRD AAA/Quanskill và chuẩn thị trường DMC

## 1) Trả lời ngắn

- **So với PRD cũ: đã làm đúng, và làm nhiều hơn PRD.** PRD chỉ có một bảng `hotels` mỏng, gồm name, country, destination, supplier, links, media và desc. PRD không có loại phòng, giá, mùa hay hợp đồng. Lịch trình trong PRD ghi khách sạn bằng một ô chữ tự do. AA-Booking giữ mọi phần tử của PRD, chỉ khác hai chỗ: mô tả chuyển sang CIS, ảnh chuyển sang `entity_media`. Ngoài ra Booking đã có thêm loại phòng, hợp đồng nhà cung cấp có maker-checker, giá net, import Excel bảng giá, lịch mùa có stop-sale và cost sheet.
- **So với chuẩn thị trường (Tourplan, Lemax, Hotelbeds contracting): còn thiếu phần "hợp đồng khách sạn có cấu trúc".** Cụ thể là property master, phụ thu, chính sách trẻ em và giường phụ, allotment với release days, chọn giá theo meal plan, điều khoản huỷ dạng bậc, và vòng đời hợp đồng theo năm.
- **Khuyến nghị:** mở rộng dần ngay trong schema `booking` theo kiểu expand/contract, không mua hệ thống ngoài. Tổng khoảng 20–23 engineer-day, 0 USD.
- **Ngoài phạm vi khách sạn có một điểm trái luật (a):** CRM vẫn cho đại lý tự tạo nhà cung cấp loại `accommodation`, `activity` và `dmc`.

## 2) Hiện trạng (trích file)

**PRD gốc**
- `docs/AAA/Adventure Asia PRD and Technical Spec Doc [Final].pdf`, §5.4 (trang 10): bảng hotels có id, name, country_id, destination_id, supplier_id, links, media, desc.
- §5.7 và §5.10: cột `hotel` là varchar.
- RBAC: Content Creator chỉ quản lý activity.
- ERD v2 thêm `hotel_style`, `status`, `deleted_at` (`docs/AAA/erd-v2/booking.dbml:227-240`).
- Figma không có màn nhập giá và không có loại phòng (`docs/audits/2026-10-14-S236-design-review/booking-ui-spec/07-activities-hotels.md:253, 328-332`).

**Hiện tại trong Booking**
- `booking.hotels` (`docs/architecture/db-schema-reference.md:2065-2110`):
  - Có code, stars, geo, giờ check-in/out, amenities, `supply_version`.
  - Khoá duy nhất `(supplier_id, lower(name), destination_id)`, nên mỗi khách sạn bị gắn cứng với một nhà cung cấp.
  - UI khoá ô Supplier sau khi tạo (`apps/AA-Booking/frontend/app/(staff)/hotels/_parts/HotelFormDrawer.tsx:111-185`).
- `hotel_room_types` chỉ có `max_occupancy` và `bed_types` (`db-schema-reference.md:2040-2063`).
- `supplier_rates` có season (chữ tự do), meal_plan, pax band và net. Không có cột phụ thu, giường phụ, trẻ em, allotment hay min-stay (`db-schema-reference.md:3338-3374`).
- ADR 0005 d2 lại yêu cầu "single supplement, extra bed" (`docs/adr/0005-pricing-and-supplier-rates.md:44-48`).
- Template Excel chỉ có 10 cột (`apps/AA-Booking/backend/app/supply/rate_sheet.py:63-74`). Import chỉ định giá cho khách sạn đã có sẵn, không nhập được thông tin khách sạn (`apps/AA-Booking/CONTEXT.md:2206`).
- Rate in force chọn **net thấp nhất** và không nhận tham số meal_plan (`apps/AA-Booking/backend/app/supply/rates.py:58, 100-150`). Vì vậy giá BB rẻ hơn sẽ âm thầm thắng giá HB.
- Single supplement được suy ra từ dòng giá pax=1 (`apps/AA-Booking/backend/app/catalog/cost_sheet.py:341-370`). Giá trẻ em chỉ là % ở phía giá bán (`CONTEXT.md:1334-1340`).
- Pricing chỉ đọc lịch mùa của trip plan (`apps/AA-Booking/backend/app/pricing/seasons.py:20-22, 215`). Lịch mùa gắn với hợp đồng nhà cung cấp có tồn tại nhưng pricing không đọc.
- Allotment chỉ có cho ghế đại lý trên departure (`db-schema-reference.md:1699-1734`).
- Điều khoản huỷ và thanh toán là chữ tự do trên hợp đồng (`db-schema-reference.md:3208-3244`).

**Nội dung khách sạn**
- Theo ADR 0004a (`docs/adr/0004a-supply-content-ownership.md:33-57`): Booking giữ facts, CIS viết và duyệt mô tả và ảnh tại `/admin/supply-content`.
- CIS ghi mỗi lần sửa thành một version mới, có publish/reject (`apps/AA-CIS-App/services/supply_content/review.py:1-13`).

**Điểm trái luật (a)**
- `crm.agency_supplier` cho phép category `accommodation` (`db-schema-reference.md:5383+`), và `crm.option` cho phép source `agency`.

## 3) Chuẩn thị trường làm thế nào

Các hệ thống DMC (Tourplan, Lemax, Hotelbeds/RateHawk contracting, phía supplier của Asian Trails) đều tách hai lớp:

1. **Static content (property master).** Mỗi khách sạn thật là một dòng duy nhất, có mã GIATA hoặc mã channel. Một khách sạn liên kết với nhiều nhà cung cấp (mua trực tiếp, mua qua DMC). Loại phòng có standard/max occupancy, số người lớn và trẻ em tối đa, giường phụ, cũi, diện tích, hướng nhìn. Ảnh, mô tả và tiện ích do đội content quản lý.
2. **Contract / rates.** Gồm:
   - Hợp đồng theo năm, có version và quan hệ supersede.
   - Rate plan theo mùa × loại phòng × meal plan × occupancy.
   - Phụ thu: single supplement, extra bed, gala bắt buộc 24/12 và 31/12.
   - Chính sách trẻ em theo dải tuổi (ở chung phòng hoặc giường phụ).
   - Hạn chế: min-stay, CTA/CTD.
   - Inventory: allotment, free sale hoặc on request, kèm release days và stop-sale theo ngày.
   - Điều khoản huỷ và thanh toán dạng bậc (số ngày, %).
   - Loại giá: net hoặc commissionable.
   - Nhập và xuất Excel theo kiểu round trip, có diff trước khi duyệt.
   - Giá tính **theo từng đêm**, để một kỳ lưu trú có thể nằm vắt qua hai mùa.

## 4) Phương án

| | A. Vá cột tối thiểu | B. Property master + hợp đồng có cấu trúc (mở rộng dần) | C. Mua hệ thống / feed ngoài |
|---|---|---|---|
| Nội dung | Thêm các cột phụ thu và trẻ em vào `supplier_rates`, sửa meal_plan | Tách khách sạn khỏi nhà cung cấp; thêm các bảng phụ thu, trẻ em, allotment, điều khoản bậc, vòng đời hợp đồng | Dùng Tourplan/Lemax, mua licence GIATA hoặc channel manager |
| Ưu | Nhanh (~5 ngày) | Đúng chuẩn DMC, giữ đúng ownership ADR 0004a/0005, 0 USD | Tính năng đầy đủ ngay |
| Nhược | Khách sạn trùng vẫn tồn tại, không có allotment, sẽ phải làm lại | ~20–23 ngày, cần một đợt gộp dữ liệu | Trả phí, phá kiến trúc hiện có, dữ liệu nằm ngoài DB AA |
| Chọn | Không | **Có** | Không (chỉ giữ cột mã ngoài để sau này nối) |

## 5) Khuyến nghị và thiết kế (phương án B)

**Ai sở hữu dữ liệu.** Mọi dữ liệu khách sạn và giá nằm trong schema `booking`, migration `bk-NNN`, áp qua DB Migrate. Nội dung hiển thị cho khách vẫn ở CIS. TripPlanner không đổi. CRM chỉ đọc.

**Dữ liệu (expand trước, contract sau)**
- `hotels`:
  - Thêm `giata_id`, `external_codes jsonb`.
  - Bảng mới `hotel_supplier_links` gồm hotel_id, supplier_id, supplier_hotel_code, is_preferred.
  - Bước contract: `hotels.supplier_id` cho phép NULL, đổi khoá duy nhất thành `(lower(name), destination_id)` sau khi gộp trùng.
- `hotel_room_types`: thêm `std_occupancy`, `max_adults`, `max_children`, `extra_bed_max`, `cot_allowed`, `size_m2`, `view`, `category_code`.
- `supplier_rates`: thêm `rate_basis` (per_room|per_person), `single_supplement`, `extra_bed_adult`, `extra_bed_child`, `min_stay`, `rate_kind` (net|commissionable), `commission_pct`.
- Bảng mới:
  - `hotel_child_policies`: contract, hotel, age_from/to, sharing|extra_bed, amount hoặc pct.
  - `supplier_rate_supplements`: contract, hotel, kind gala|compulsory|surcharge, ngày, giá người lớn/trẻ em, mandatory.
  - `hotel_allotments`: contract, room_type, khoảng ngày, rooms, release_days, inventory_type allotment|free_sale|on_request.
  - `hotel_restrictions`: stop_sale|cta|ctd theo hotel hoặc room type và ngày.
- `supplier_contracts`: thêm `supersedes_contract_id`, `cancellation_tiers jsonb`, `payment_tiers jsonb`, `document_file_id`.
- `trip_plan_components` và `trip_case_version_itinerary`: thêm `meal_plan`.
- Giữ các trigger `supply_version` và audit columns hiện có.

**Màn hình** (Booking staff admin, trang `/hotels` và `/suppliers`)
- Drawer khách sạn chia tab: Facts, Room types, Suppliers & codes, Contracts, Calendar.
- Lưới giá theo mùa × phòng × meal plan.
- Tab phụ thu và trẻ em.
- Lịch allotment và stop-sale, có nút stop-sale nhanh cho ops.
- Màn "Gộp khách sạn trùng".
- Import Excel cho cả facts và giá: chạy thử, hiện diff, tạo draft. Có thêm Export để sửa rồi nhập lại.
- Nút "Copy sang năm sau".
- Diff dòng giá trước khi publish.
- Mô tả và ảnh vẫn sửa ở CIS `/admin/supply-content`.

**Luồng giá**
1. Cost sheet chọn room type, meal plan và số đêm.
2. Với từng đêm: tìm `rate_in_force(meal_plan, ngày)`, cộng phụ thu theo ngày, tính trẻ em theo tuổi, cộng single supplement tường minh.
3. Hết allotment, quá release days hoặc gặp stop-sale thì dòng thành `on_request`, giống cơ chế `seasons.py:14-15`.
4. Khi tạo `supplier_bookings`, trừ allotment. Ops xác nhận với nhà cung cấp.

**Hiển thị**
- Khách du lịch: TripPlanner chỉ thấy giá từ (`v_from_prices`) và nội dung CIS, không bán phòng lẻ (`apps/AA-TripPlanner-Web/.kiro/steering/product.md:44`).
- Đại lý: thấy component phòng của AA (`rt:`) cùng nội dung CIS trong B2B/CRM. Đại lý chỉ dùng, không sửa.

**Quyền**
- `supply.write` (facts, giá, allotment): contracting, admin.
- Publish hợp đồng: người thứ hai (maker-checker có sẵn).
- Stop-sale: contracting và ops.
- sales: chỉ đọc.
- Nội dung khách sạn: vai trò content trong CIS.
- Mọi lần import ghi log kèm diff.

## 6) Lộ trình theo phiên (mỗi bước là 1 PR giao được)

| # | Bước | Ngày |
|---|---|---|
| 1 | Meal plan thành khoá chọn giá; single supplement và extra bed tường minh; template Excel thêm cột | 3–4 |
| 2 | Property master, `hotel_supplier_links`, mã GIATA/external, màn gộp trùng | 3–4 |
| 3 | Chính sách trẻ em và phụ thu/gala vào cost sheet | 3 |
| 4 | Allotment, release, stop-sale và CTA/CTD; quote ra on_request | 4–5 |
| 5 | Vòng đời hợp đồng: supersede, diff, copy năm, điều khoản huỷ dạng bậc | 3 |
| 6 | Import/export Excel facts và room types (round trip) | 3 |
| R | Chặn `crm.agency_supplier` các loại catalogue (nếu được chốt) | 1 |

Tổng: khoảng 20–23 engineer-day. Chi phí 0 USD vì không dùng dịch vụ AWS mới. GIATA và channel manager là dịch vụ trả phí, nên chưa mua.

## 7) Câu cần chốt

1. **Một khách sạn có thể mua qua nhiều nhà cung cấp không?** Đề xuất: có, dùng property master (bước 2).
2. **Meal plan mặc định của tour là gì?** Đề xuất: BB, tour hoặc quote được chọn HB/FB.
3. **Nhà cung cấp của AA có cấp allotment thật không?** Đề xuất: hỗ trợ đủ ba kiểu, mặc định on_request.
4. **Có mua GIATA không?** Đề xuất: chưa, chỉ giữ cột mã để nối sau.
5. **Hợp đồng net hay commissionable?** Đề xuất: hỗ trợ cả hai qua `rate_kind`.
6. **Ai nhập gì?** Đề xuất: contracting nhập facts và giá ở Booking; nhân viên content viết mô tả và ảnh ở CIS.
7. **Luật (a) với CRM:** đại lý có được giữ nhà cung cấp riêng không? Đề xuất: bỏ hẳn `accommodation`, `activity`, `dmc` khỏi `crm.agency_supplier` và chặn `crm.option` source `agency` cho các loại catalogue. Business owner chốt.

**Chưa kiểm trong lần này:** số dòng live của các bảng khách sạn và giá, việc đã có bảng giá thật nào được import hay chưa, và `docs/contracts/supply.hotel.v1.json`.
