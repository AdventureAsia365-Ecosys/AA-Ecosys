# PR-29: hoạt động tuỳ chọn có tính tiền theo địa điểm và ngày

# Hoạt động tuỳ chọn theo địa điểm (optional add-ons): tư vấn thiết kế

## 1) Trả lời ngắn

- Phần cung ứng đã có gần đủ trong AA-Booking. Mỗi `booking.services` loại `activity` bắt buộc có nhà cung cấp AA (`supplier_id NOT NULL`), có gắn địa điểm (`destination_id`), có giá net theo hợp đồng do người thứ hai duyệt, và engine báo giá đã tính được dòng `sv:`.
- Còn thiếu lớp "add-on tuỳ chọn theo địa điểm". Hiện cách duy nhất gắn service vào tour là `trip_plan_components`, nhưng mọi component ở đó đều bị cộng vào giá tour, nên thành bắt buộc.
- Khuyến nghị: Booking sở hữu một danh mục add-on riêng, gắn với nhiều địa điểm, có luật bán (cut-off, ngày hoạt động, số khách tối thiểu, giá trẻ em). CIS viết nội dung cho khách. TripPlanner chỉ đọc qua view. CRM chỉ báo giá qua `booking.b2b.v1`. Đại lý không có đường nào để ghi vào danh mục.
- Công sức khoảng 18–22 ngày công, chia 5 phiên. Chi phí gần 0 USD (dùng RDS/ECS sẵn có; LLM viết mô tả chỉ vài cent mỗi hoạt động, nằm trong cap hiện tại).

## 2) Hiện trạng (trích file)

| Đã có | Bằng chứng |
|---|---|
| Service `activity`, đơn vị person/group/vehicle/day, một `destination_id` | `docs/architecture/db-schema-reference.md:2937-2978` |
| Mỗi service có đúng một nhà cung cấp AA | `db-schema-reference.md:2940`, `:3376-3412` |
| Giá net theo hợp đồng, maker-checker publish | `db-schema-reference.md:3208-3239`, `:3338-3370`; `apps/AA-Booking/CONTEXT.md:1690-1693` |
| Dòng `sv:` báo giá riêng; trẻ em tính bằng giá người lớn | `apps/AA-Booking/backend/app/b2b/components.py:6-7,17-18`; `CONTEXT.md:1334-1337` |
| Dòng `sv:` luôn là `on_request` (cut-off và allotment chỉ áp cho `tp:`) | `apps/AA-Booking/backend/app/b2b/quotes.py:19-21` |
| Component bị cộng vào giá tour | `components.py:8`; `CONTEXT.md:893-899` |
| Ghép ngày với địa điểm: `v_tour_day_route`, `v_tour_place` | `db-schema-reference.md:4919-4940`, `:5010-5040` |
| CIS viết mô tả/ảnh, nhưng `v_supply_content` không có title, không có locale và chỉ grant cho booking | `db-schema-reference.md:4681-4699`; `apps/AA-CIS-App/CONTEXT.md:2384-2410` |
| Import Excel chỉ đặt giá cho mã SVC- có sẵn, không tạo được service mới | `apps/AA-Booking/backend/app/supply/rate_sheet.py:1-25,50-56` |
| `content_creator` không đọc/ghi được supply | `apps/AA-Booking/backend/app/auth/staff.py:116-119` |
| "Activities here" của TripPlanner lấy từ nội dung tour: không nhà cung cấp, không giá | `apps/AA-TripPlanner-Web/backend/assembly/activities.py:1-27` |
| Lead không có trường add-on | `docs/contracts/lead.submitted.v1.openapi.yaml:226-267` |
| CRM: đại lý vẫn tự gõ được option trong block `activity` | `apps/AA-Partner/api/app/proposals/builder.py:1349-1366`; `rules.py:27` |
| Luật ADR: CRM chỉ được thêm ancillary ngoài AA | `docs/adr/0019-b2b-only-ecosystem-model.md:310` (b6), `:309` (b5: đại lý là merchant of record) |

Chưa kiểm live: trên Dev có bao nhiêu service `activity` và bao nhiêu là dữ liệu thật. Cần đếm trong DB trước khi nói "đã phủ".

## 3) Chuẩn thị trường làm thế nào

- **DMC / hệ tour operator** (Tourplan, Lemax; Asian Trails bán "tariffs per destination for … excursions" — `docs/research/2026-11-05-asian-trails-b2b-benchmark/README.md:82`): excursion là một sản phẩm riêng, gắn với destination, không nằm trong giá package. Agent thêm nó như dòng "optional" trong booking.
- **Hệ supplier activity** (Bókun, Rezdy, FareHarbor, phía supplier của Viator/GYG): mỗi sản phẩm có:
  - loại giá adult/child/infant kèm tuổi;
  - số khách tối thiểu/tối đa;
  - giờ cut-off;
  - ngày hoạt động trong tuần, giờ khởi hành;
  - lịch còn chỗ hoặc on-request;
  - chính sách huỷ riêng từng sản phẩm (ví dụ huỷ miễn phí trước 24 giờ);
  - điểm đón;
  - ngôn ngữ hướng dẫn;
  - nội dung đa ngôn ngữ.
- **Nguyên tắc chung:**
  - Chỉ hiện sản phẩm có giá đang hiệu lực vào đúng ngày đi.
  - Danh mục do nhà điều hành quản lý; reseller (đại lý) chỉ đặt markup.
  - Giá chốt lại lúc báo giá, không chốt lúc hiển thị.

## 4) Phương án

| | A. Cờ `is_addon` trên `booking.services` | **B. Danh mục add-on riêng trong Booking** | C. CIS sở hữu danh sách add-on |
|---|---|---|---|
| Cách làm | Thêm cột cờ; add-on = service active tại `destination_id` | Bảng `addon_offers` + `addon_offer_places` trỏ tới service; luật bán nằm trên offer | CIS giữ danh sách và nội dung, map sang service của Booking |
| Ưu | Nhanh (~1 tuần) | Đúng chuẩn DMC; nhiều địa điểm; có publish và audit riêng; không đụng giá tour | Gần đội content |
| Nhược | Chỉ một địa điểm; trộn sự thật cung ứng với luật bán; khó thêm cut-off/ngày hoạt động | Thêm 2 bảng + 1 màn hình | Trái ADR 0004a (dữ liệu thương mại do Booking sở hữu); hai nguồn sự thật |
| Chọn | Không | **Có** | Không |

## 5) Khuyến nghị và thiết kế (phương án B)

**Ai sở hữu gì**

- **Booking:** add-on, địa điểm, luật bán, giá.
- **CIS:** tiêu đề và mô tả cho khách, ảnh, bản dịch.
- **TripPlanner và CRM:** chỉ đọc.

**Dữ liệu** (expand trước; không bỏ cột cũ)

- `booking.addon_offers` (bk-NNN):
  - `id`, `service_id` (FK), `status` draft|published|retired, `sort_order`, `featured`;
  - `min_pax`, `cutoff_hours`, `operating_weekdays smallint[]`, `start_times text[]`;
  - `child_age_max`, `infant_age_max`, `cancellation_terms` (văn bản cho khách, ví dụ "free cancel ≥24h");
  - `created_by`, `published_by` với CHECK publisher ≠ người sửa cuối (giống contract);
  - trigger outbox + `supply_version` như services (`db-schema-reference.md:2985-2987`).
- `booking.addon_offer_places`:
  - `offer_id`, `destination_id` (soft key, API kiểm qua `catalog.v_destination`), `role` operates|pickup;
  - giải quyết giới hạn "một nơi" của services.
- `booking.supplier_rates` thêm `pax_type` adult|child|infant, mặc định adult.
  - Engine sẽ tính trẻ em theo giá child nếu có, không có thì lấy giá adult (giữ hành vi cũ).
- View `booking.v_place_addons`, grant cho `tripplanner` (cùng kiểu `v_from_prices`, bk-039):
  - cột: `component_id 'sv:…'`, `destination_id`, unit, duration, min_pax, cut-off, weekdays, `from_rrp_usd`;
  - không net, không tên nhà cung cấp;
  - **luật lọc:** offer published, service active, supplier active, có contract published và rate đang hiệu lực, không bị stop-sale của season calendar.
- CIS (migration CIS):
  - `shared.supply_content_version` thêm `customer_title`, `locale` (mặc định 'en');
  - `catalog.v_supply_content` thêm 2 cột đó, và grant bản chỉ chứa nội dung published cho `tripplanner`.

**Màn hình cho nhân viên AA**

- Booking `/add-ons`:
  - danh sách lọc theo nước/địa điểm/nhà cung cấp; nút chọn service, gắn nhiều địa điểm;
  - trường luật bán; badge "thiếu giá / thiếu nội dung / thiếu ảnh có quyền";
  - Publish (người thứ hai bấm); xem trước theo một tour mẫu ("Ngày 3 HCMC sẽ hiện…").
- CIS `/admin/supply-content`: sửa tiêu đề và mô tả cho khách, bản dịch (đã có luồng review).

**Import Excel**

- Template mới "Activity catalogue", mỗi dòng một hoạt động:
  - mã nhà cung cấp, tiêu đề, địa điểm, unit, thời lượng, bao gồm;
  - min pax, cut-off, ngày hoạt động;
  - net adult/child, mùa, hiệu lực.
- Mở rộng `rate_sheet.py` để **tạo** service + offer ở trạng thái draft và một contract draft.
- Có bước xem trước diff, rồi publish theo maker-checker.

**Luồng tới khách**

1. TripPlanner, mỗi thẻ ngày: lấy địa điểm của ngày từ `v_tour_place.destination_id` + `v_tour_day_route.overnight_destination_id`, nơi ngủ đêm xếp trước. Hiện "Hoạt động thêm" từ `v_place_addons` + nội dung CIS.
2. Mục "Activities here" hiện tại đổi nhãn thành "Trong tour có" (chỉ là nội dung, không bán).
3. Khách tick chọn → `lead.submitted.v1` minor: `day_plan[].addons[]` = các id `sv:`, không kèm giá (giữ luật "không giá trong lead").
4. CRM: `booking.b2b.v1` minor `GET /add-ons?destination_id=&date=&pax=`. Builder có drawer "AA add-on" để báo giá dòng `sv:` bằng engine sẵn có.
5. Sau đó đi tiếp luồng cũ: hold → booking → supplier booking → voucher (`CONTEXT.md:1137-1140,1309-1313`).

**Quyền**

- `supply.addon.write` mới cho `content_creator` + `contracting` + `admin`: tạo/sửa offer, gắn địa điểm, sắp thứ tự.
- `supply.read` mở cho `content_creator` nhưng ẩn net.
- Giá và hợp đồng vẫn chỉ `contracting`/`admin`.
- Publish offer phải là người thứ hai.

**Chặn đại lý**

- `add_agency_option` từ chối mọi block/category ngoài b6 (flight|insurance|visa|transfer|fee).
- `booking.b2b.v1` không có endpoint ghi add-on.

**Audit:** outbox + `supply_version` + ai publish, lúc nào. Dòng báo giá vẫn append-only như hiện tại.

## 6) Lộ trình theo phiên (mỗi bước giao được)

| Phiên | Giao | Ngày công |
|---|---|---|
| 1 | Migration Booking (offers, places, `pax_type`), API staff, quyền, màn hình `/add-ons`, maker-checker | 5 |
| 2 | Import Excel tạo service + offer + rate draft, xem trước diff; engine tính giá child | 4 |
| 3 | CIS `customer_title` + `locale`, grant view; `v_place_addons` + luật lọc | 3 |
| 4 | `b2b.v1` minor `/add-ons`, drawer trong CRM, chặn option đại lý ngoài b6 | 4 |
| 5 | TripPlanner hiển thị theo ngày, đổi nhãn "Activities here", lead minor, CRM nhận add-on từ lead | 4 |
| Sau | Lịch còn chỗ/allotment theo ngày cho service (khi nhà cung cấp cho số chỗ) | 3 |

Chi phí: 0 USD hạ tầng mới; LLM viết mô tả dùng gateway hiện có (giới hạn 20 bản nháp/ngày).

## 7) Câu cần chốt (kèm đề xuất)

1. **Ai nhập danh sách?**
   - Đề xuất: content AA tạo/sửa offer và nội dung; contracting nhập giá và hợp đồng; người thứ hai publish.
   - (business owner)
2. **Trang TripPlanner của đại lý có hiện giá add-on không?**
   - Đề xuất: không hiện giá (b5), ghi "đại lý báo giá"; trang của AA hiện "From …/khách".
   - (business owner)
3. **Ghép add-on theo nơi ngủ hay theo mọi nơi đi qua trong ngày?**
   - Đề xuất: cả hai, nơi ngủ xếp trước.
   - (tech lead)
4. **Lịch còn chỗ?**
   - Đề xuất: v1 dùng on_request + cut-off + ngày hoạt động; làm allotment khi nhà cung cấp cung cấp số chỗ.
   - (tech lead)
5. **Hoạt động chưa có giá hiệu lực thì sao?**
   - Đề xuất: ẩn hẳn, không hiện "liên hệ".
   - (business owner)
6. **Giá trẻ em khi nhà cung cấp không ghi riêng?**
   - Đề xuất: tính bằng giá người lớn, và hiện chú thích tuổi.
   - (business owner)
7. **Dữ liệu Dev:**
   - Đề xuất: đếm service `activity` thật/giả trước phiên 1, xoá dữ liệu giả theo quy trình DRY RUN.
   - (tech lead)
