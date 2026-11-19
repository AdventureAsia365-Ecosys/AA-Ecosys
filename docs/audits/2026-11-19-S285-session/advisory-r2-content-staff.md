# Tư vấn vòng 2: nhân viên content làm việc hằng ngày trên CIS và Booking (T4) + T1, T2, T3, T5

Ngày 19/11/2026 (S285). Chỉ đọc code, không sửa repo nào ngoài file này. Dựa trên 2 bản trước:
`advisory-content-editing.md` và `advisory-content-activities-hotels-critic.md` (cùng thư mục).

Đã đọc: `apps/AA-CIS-App/frontend/app/admin/*` (drawer tour, supply content, AA content, ảnh, upload, review),
`apps/AA-Booking/frontend/app/(staff)/*` (hotels, services, trip plans, ảnh nhà cung cấp),
`apps/AA-Booking/backend/app/auth/staff.py`, `apps/AA-Booking/CONTEXT.md`, `apps/AA-CIS-App/CONTEXT.md`,
`apps/AA-CIS-App/services/quality/source_fanout.py`, `api/routers/v1_tours.py`, và
`docs/architecture/db-schema-reference.md` (bản dump live 18/11, CIS 454, Booking bk-059).

## Từ viết tắt dùng trong bài

| Từ | Nghĩa ngắn |
|---|---|
| CIS | app nội dung + danh mục tour của AA (nơi nhân viên content làm việc) |
| Booking | app nhà cung cấp, hợp đồng, giá, đặt chỗ của AA |
| CRM | app của đại lý (AA-Partner), nơi đại lý làm báo giá và nội dung riêng |
| TripPlanner | trang web xem tour (đọc danh mục CIS, giá "từ" lấy từ Booking) |
| Raw (tour gốc) | dữ kiện tour nhà cung cấp gửi (bảng `silver_aa_internal.raw_tours`) |
| Master | bản tour AA đã duyệt, đang dùng (bảng `gold_aa_internal.published_tours`) |
| S1 | bước AI viết lại tour gốc thành bản câu chữ AA |
| T2 | bản viết lại riêng của từng đại lý theo giọng thương hiệu đại lý (bảng `gold_aa_internal.tenant_tour_versions`) |
| T9 | bài viết marketing của đại lý (blog, mạng xã hội) trích dẫn tour |
| LLM | mô hình AI viết chữ (Claude, GPT), gọi là tốn tiền theo lượt |
| DMC | destination management company, công ty lữ hành địa phương bán trọn tour (xe, vé, khách sạn, hướng dẫn) cho AA |
| Diff | bảng "trước / sau", tô màu chỗ khác nhau |
| Autosave | tự lưu bản nháp khi đang gõ, không cần bấm Lưu |
| Bản nháp | bản đang sửa, khách và đại lý chưa thấy |
| Xuất bản | đưa bản nháp thành bản đang dùng (Master), khách và đại lý thấy |
| View | "cửa sổ chỉ đọc" vào một bảng, chỉ lộ một số cột |
| Grant | quyền cho một app đọc view đó |
| Soft key | lưu ID của app khác mà không ràng buộc cứng trong DB (không FK) |
| FK | foreign key, khoá ràng buộc cứng giữa hai bảng |
| SEO | tối ưu để Google tìm thấy (tiêu đề, mô tả ngắn) |
| B / L / D | bữa sáng / trưa / tối (breakfast, lunch, dinner) |
| BB | bed & breakfast, phòng kèm bữa sáng |

## Tóm tắt 1 phút

| Mục | Câu trả lời ngắn | Đề xuất có đổi? |
|---|---|---|
| **T4** (chính) | Đúng là lỗ hổng lớn. Hôm nay nhân viên content **không tạo được tour tay**, sửa tour trong một ngăn kéo (drawer) **lưu thẳng vào bản thật**, không có nháp, không xem trước như khách thấy, không có "có gì thay đổi" trước khi xuất bản, **không upload hay cắt ảnh được**. Đề xuất một bộ công cụ 9 màn hình, làm trong ~6 PR, khoảng 26–33 ngày công lane, 0 USD hạ tầng mới. | Có, mở rộng |
| **T3** | Đổi dữ kiện ở CIS mà không làm mới T2 thì trang của đại lý vẫn kể lịch trình cũ, trong khi báo giá của đại lý đã theo lịch trình mới: khách thấy hai câu chuyện khác nhau. Logic đúng: tự làm mới khi **dữ kiện** đổi, **không ghi đè** bản đại lý đã tự sửa, có trần chi phí. | Có, làm rõ |
| **T5** | Đúng: bảng nhà cung cấp chỉ có ở Booking (`booking.suppliers`), CIS chỉ có chữ tự do `raw_tours.provider`. Cách tốt nhất: Booking mở **một view chỉ đọc** cho CIS (giống 4 view `v_supply_*` đã có), CIS lưu ID dạng soft key. | Có, chi tiết hơn |
| **T1** | Giữ: bản sửa tay thắng, lần import sau hiện so sánh từng trường. | Không |
| **T2** | Giữ: Dev tự xuất bản; từ prod người sửa không tự xuất bản. | Không |

---

## T4. Nhân viên content làm việc thế nào trên CIS và Booking

### T4.1 Hiện trạng: những gì có và thiếu (đã kiểm trong code)

**Những gì đã có và làm tốt (nên dùng lại, không làm lại):**

- **Supply content** (`/admin/supply-content/[id]`, `SupplyContentDetail.tsx`): mô tả và ảnh khách sạn, hoạt động.
  Có bản nháp, diff với bản đã xuất bản, danh sách "vì sao chưa xuất bản được" (`publishBlockers`), nút Xuất bản /
  Từ chối, lịch sử phiên bản. Đây là **khuôn mẫu đúng** cho cả tour.
- **AA content** (`/admin/aa-content`, `AaContentEditor.tsx`): bản nháp, xem trước, phiên bản, chống hai người ghi đè
  nhau (gửi kèm `expected_updated_at`, ai lưu sau bị báo "người khác vừa lưu, tải lại").
- **Review Queue** (`/admin/review`): sửa bản AI viết, kiểm lại tự động, rồi mới cho duyệt; có chọn nhiều tour để
  viết lại hàng loạt.
- **Booking** đã có link "Edit in CIS" trên trang trip plan và khách sạn; Booking giữ ảnh nhà cung cấp kèm công tắc
  "quyền sử dụng" (`_parts/SupplyContent.tsx`).

**Những gì thiếu (lỗ hổng, đánh số G để dẫn chiếu):**

| # | Thiếu gì | Bằng chứng trong code | Hậu quả với nhân viên |
|---|---|---|---|
| G1 | Không tạo được tour tay, chỉ qua upload Excel | `api/routers/admin_pipeline/uploads.py` (upload URL → ingest S3 → staging) | Nhà cung cấp gửi 1 tour qua email/PDF thì phải tự làm file Excel đúng mẫu |
| G2 | Sửa tour trong drawer 5 tab (Original, Rewrite, History, SEO, Published), **lưu khi click ra ngoài, ghi thẳng vào bản thật** | `TourDetailPanelV2.tsx:401, 483-517`: `PATCH /api/admin/tours/{id}/raw` | Gõ nhầm là sai luôn, không có nháp, không có lý do sửa, không ai biết ai sửa |
| G3 | Dữ kiện là **chữ tự do**: thời lượng, quốc gia, nhà cung cấp, cả lịch trình là một ô văn bản dài | `TourDetailPanelV2.tsx:661-681`; cột `duration text`, `provider varchar(255)`, `src_itineraries text` | Không kiểm được "8 ngày nhưng lịch trình có 7 ngày", không chọn địa điểm trên bản đồ |
| G4 | Không xem trước được tour trông thế nào trên TripPlanner | TripPlanner `app/tours/[slug]/page.tsx` không có chế độ xem nháp; trang cache 30 phút (`revalidate = 1800`) | Nhân viên xuất bản rồi mới biết trang xấu, sửa lại phải chờ cache |
| G5 | Không có màn "có gì thay đổi" trước khi xuất bản tour | `CompareModal.tsx` chỉ so 2–4 tour cạnh nhau, không phải bản nháp với bản đang chạy | Xuất bản mù |
| G6 | Không có danh sách "trường bắt buộc" cho tour | Supply content có `publishBlockers`, tour không có | Tour thiếu ảnh, thiếu bao gồm vẫn lên được |
| G7 | **Không upload, không cắt ảnh** cho tour | Trang Ảnh (`/admin/photos`) chỉ đồng bộ từ thư mục Google Drive; bảng `shared.place_photo` bắt buộc `drive_file_id`, không có cột alt text, điểm lấy nét hay quyền dùng | Ảnh phải bỏ vào Drive đúng thư mục rồi chờ đồng bộ |
| G8 | Nhân viên content (vai trò `content`) **không vào được trang Ảnh** | `frontend/lib/rbac.ts:107`: chỉ admin, content_lead | Người làm nội dung không quản lý ảnh của chính tour mình |
| G9 | Ảnh khách sạn / hoạt động: chỉ contracting của Booking upload; không cắt, không chọn ảnh bìa ở Booking | `SupplyContent.tsx` (upload + công tắc quyền); `staff.py`: `supply.write` = admin, contracting | Nhân viên content có ảnh đẹp từ nhà cung cấp cũng không tự đưa vào được |
| G10 | Vai trò Booking của nhân viên content (`content_creator`) chỉ có `catalog.read` | `apps/AA-Booking/backend/app/auth/staff.py:119`; không có `supply.read` | Trong Booking họ không xem được khách sạn, nhà cung cấp; thực tế không có việc gì làm ở Booking |
| G11 | Sửa hàng loạt chỉ có xuất CSV, gỡ tour, viết lại AI | `master-content/page.tsx:790-1035`, `review/page.tsx` | Đổi một mục "bao gồm" cho 20 tour phải mở 20 lần |
| G12 | Không có "bàn làm việc": việc của tôi, việc chờ duyệt, tour bị nhà cung cấp đổi | Không có trang nào gom lại | Nhân viên phải tự nhớ đang làm dở gì |
| G13 | Sửa bản AI viết ghi đè bản mới nhất, có thể không phải bản đang chạy; promote không bắt kiểm lại | Bản trước: `tour_detail.py:501-577`, `versions.py:42-56` | Bản sửa tay có thể bị wave sau ghi đè |
| G14 | Supply content sửa trong hộp thoại (Modal), không tự lưu, không xem trước như đại lý thấy | `SupplyContentDetail.tsx:529-553` (`EditModal`) | Đóng nhầm hộp thoại là mất chữ |

Kết luận: phần **duyệt và xuất bản** của khách sạn / hoạt động đã gần đủ. Phần **tour** thì thiếu gần hết: tạo,
nháp, xem trước, diff, ảnh. Đây là chỗ cần làm.

### T4.2 Ai làm gì

| Người | Ở app nào | Việc |
|---|---|---|
| **Nhân viên content** (CIS `content`) | **Chỉ CIS.** Không cần vai trò Booking (T13 ẩn `content_creator` khỏi Booking); trạng thái bán, giá "từ" hiện chỉ đọc trong CIS | Tạo tour tay, sửa dữ kiện và câu chữ, upload và cắt ảnh, viết mô tả khách sạn / hoạt động, gửi duyệt |
| **Trưởng content** (CIS `content_lead`) | CIS | Duyệt và xuất bản (từ prod), mở khoá bản đã sửa tay, chạy lại AI có tốn phí |
| **Contracting** (Booking `contracting`) | Booking | Tạo nhà cung cấp, hợp đồng, giá, khách sạn và loại phòng (nhập tay từ bảng giá của DMC), upload ảnh nhà cung cấp gửi, gắn tour với nhà cung cấp |
| **AI** | CIS (worker) | Viết nháp câu chữ từ dữ kiện; người luôn duyệt trước khi lên |

Nguyên tắc: **nhân viên content chỉ cần học một app (CIS)**. Mọi thứ họ cần từ Booking (tên nhà cung cấp, dữ kiện
khách sạn, giá "từ", trạng thái bán được) hiện trong CIS ở dạng chỉ đọc. Link "Mở trong Booking" chỉ hiện với người
có vai trò Booking (contracting, admin). Không cho content sửa giá, hợp đồng (đó là việc của contracting).

### T4.3 Một ngày làm việc (4 luồng)

**Luồng A: nhà cung cấp gửi cả file Excel nhiều tour (đã có, chỉ bổ sung).**
Upload → xem trước từng dòng (mới / đổi / trùng) → nhận → AI viết bản câu chữ → nhân viên kiểm trong editor → gửi
duyệt → xuất bản. Bổ sung: tour đã sửa tay thì lần import sau hiện màn so sánh từng trường (xem T1).

**Luồng B: nhà cung cấp gửi 1 tour qua email / PDF (mới).**
Ví dụ: DMC "Mekong Ways" gửi tour "Delta 3 ngày 2 đêm" bằng PDF. Lan (content) bấm **"+ Tạo tour"**, chọn nhà cung cấp
từ danh sách Booking, nhập 3 ngày theo thẻ, chọn địa điểm từ danh mục, tick bao gồm, upload 8 ảnh, bấm "AI viết câu
chữ" (~0,02–0,05 USD, chưa kiểm số thật của S1 cho tour 3 ngày), sửa lại, xem trước như trên TripPlanner, gửi duyệt.
Mất khoảng 20–30 phút thay vì làm file Excel.

**Luồng C: sửa tour đang bán.**
Ví dụ: nhà cung cấp báo ngày 2 đổi từ "ngủ du thuyền" sang "ngủ khách sạn Cần Thơ". Lan mở tour → tab Lịch trình →
sửa ngày 2 → hệ thống tự lưu nháp và báo "Câu chữ ngày 2 chưa khớp dữ kiện mới" → Lan sửa câu chữ ngày 2 (hoặc bấm AI
viết lại riêng ngày đó) → xem "Có gì thay đổi" → hộp "Ảnh hưởng: 4 đại lý có bản T2, 6 bài T9, 1 báo giá đang mở"
→ gửi duyệt / xuất bản.

**Luồng D: mô tả và ảnh khách sạn, hoạt động.**
Contracting thêm khách sạn mới trong Booking (tên, hạng sao, địa điểm, loại phòng, giá BB nhập tay từ bảng giá DMC)
→ CIS nhận sự kiện, AI viết nháp mô tả → Lan thấy việc mới ở bàn làm việc "Khách sạn mới chờ mô tả (3)" → mở editor
khách sạn → sửa mô tả, chọn ảnh bìa, cắt ảnh → xuất bản → Booking và CRM hiện mô tả mới.

### T4.4 Thiết kế màn hình

Chung cho mọi màn: dùng UI kit có sẵn (`_kit`), tiếng Anh mặc định, tiếng Việt khi người dùng chọn; nút hiện theo
quyền (`can()`), backend kiểm lại mọi lệnh ghi.

#### M0. Bàn làm việc Content (`/admin/content-desk`) — trang mở đầu của nhân viên content

```
┌ Bàn làm việc ─────────────────────────────────────────────────────────────┐
│ [Nháp của tôi 3] [Chờ duyệt 5] [Bị trả lại 1] [Nhà cung cấp đổi 2]        │
│ [Khách sạn / hoạt động chờ mô tả 7] [Tour thiếu ảnh 12] [Câu chữ lỗi thời 4]│
├───────────────────────────────────────────────────────────────────────────┤
│ Việc            Tour / mục               Ai     Cập nhật     [Mở]        │
│ Nháp            Delta 3N2Đ (mới)          Lan    10:42        →           │
│ Bị trả lại      Hạ Long 2N1Đ              Minh   hôm qua      → "thiếu ảnh bìa" │
│ NCC đổi (Excel) Sapa Trek 4N3Đ            —      09:15        → so sánh   │
└───────────────────────────────────────────────────────────────────────────┘
```

Mỗi ô là một bộ lọc; mỗi dòng mở thẳng đúng màn cần làm. Không chạy tự động hỏi liên tục (giữ luật không polling),
có nút Làm mới.

#### M1. Danh sách tour (`/admin/tours`)

```
┌ Tour ───────────────────────────────── [+ Tạo tour] [Nhập Excel] ───────┐
│ Tìm [_______]  Nước [VN ▾]  Nhà cung cấp [▾]  Trạng thái [▾]  Đủ? [▾]   │
├──────────────────────────────────────────────────────────────────────────┤
│ ☐ [ảnh] Delta 3N2Đ        VN  Mekong Ways   ● Nháp        ███░ 75%  Lan │
│ ☐ [ảnh] Hạ Long 2N1Đ      VN  Bay Tours     ● Đang bán    ████ 100% —   │
│ ☐ [ảnh] Sapa Trek 4N3Đ    VN  (chưa gắn)    ● Có thay đổi ███░ 83%  —   │
├──────────────────────────────────────────────────────────────────────────┤
│ Đã chọn 2: [Sửa hàng loạt] [AI viết lại (≈0,10 USD)] [Gỡ khỏi bán]       │
└──────────────────────────────────────────────────────────────────────────┘
```

- Trạng thái dễ hiểu (5 màu): **Nháp** (khách chưa thấy), **Chờ duyệt**, **Đang bán**, **Có thay đổi chưa xuất bản**,
  **Đã gỡ**.
- Cột "Đủ?" là thanh % theo danh sách bắt buộc (M2). Lọc "Chưa đủ" để biết việc cần làm.
- "(chưa gắn)" ở cột nhà cung cấp: tour cũ chưa có ID nhà cung cấp Booking (xem T5).

#### M2. Editor tour (`/admin/tours/{id}/edit` và `/admin/tours/new`) — màn chính

Bố cục 3 cột trên màn rộng; trên điện thoại thành 1 cột, xem trước là một tab.

```
┌ Delta 3N2Đ   ● Nháp – khách chưa thấy   ✓ Đã lưu nháp 10:42   [Xem trước] [Có gì thay đổi] [Gửi duyệt] ┐
├───────────────┬───────────────────────────────────────────┬──────────────────────────┤
│ MỤC           │ 2. Lịch trình từng ngày                   │ XEM TRƯỚC (TripPlanner)  │
│ ✓ 1 Cơ bản    │ ┌ Ngày 1 ─────────────── [⋮ kéo] [Nhân bản] │ [Máy tính | Điện thoại]  │
│ ! 2 Lịch trình│ │ Tiêu đề  [Sài Gòn – Mỹ Tho – Bến Tre   ] │  ┌────────────────────┐  │
│ ✓ 3 Bao gồm   │ │ Địa điểm [Mỹ Tho ×] [Bến Tre ×] [+ thêm] │  │ ảnh bìa            │  │
│ ✗ 4 Ảnh (3/5) │ │ Bữa ăn   ☐ Sáng ☑ Trưa ☐ Tối             │  │ Delta 3N2Đ         │  │
│ ✓ 5 Câu chữ   │ │ Ngủ tại  [Khách sạn Bến Tre (Booking) ▾] │  │ Ngày 1 ...         │  │
│   6 Giá (đọc) │ │ Hoạt động[Chèo xuồng (Booking) ×]        │  └────────────────────┘  │
│   7 Lịch sử   │ │ Mô tả dữ kiện [.......................]   │                          │
│               │ └──────────────────────────────────────────  │ Thiếu để gửi duyệt:     │
│ Đủ 10/12      │ ⚠ Thời lượng 3 ngày nhưng mới có 2 ngày   │ ✗ Ảnh: cần 5, có 3       │
│               │ [+ Thêm ngày]                             │ ✗ Ngày 3 chưa có địa điểm│
└───────────────┴───────────────────────────────────────────┴──────────────────────────┘
```

Các mục (cột trái có dấu ✓ đủ, ! cảnh báo, ✗ thiếu):

1. **Cơ bản (dữ kiện):** tên gốc; nước (chọn từ danh sách ISO, không gõ chữ); **nhà cung cấp AA** (chọn từ Booking,
   bắt buộc); số ngày và số đêm (2 ô số, không gõ "3D2N"); quy mô nhóm (từ – đến); kiểu tour (riêng / ghép đoàn);
   ngôn ngữ hướng dẫn; mùa đẹp; mã SKU (mã sản phẩm nội bộ, tự gợi ý).
2. **Lịch trình từng ngày (dữ kiện):** mỗi ngày một thẻ, kéo để đổi thứ tự, nhân bản ngày. Địa điểm chọn từ danh mục
   địa điểm của CIS (`catalog.v_destination`), không gõ tự do. "Ngủ tại" chọn khách sạn Booking mà nhà cung cấp đó có
   hợp đồng (khách sạn luôn mua qua DMC, T8/T11), hoặc gõ "khách sạn 3 sao hoặc tương đương". Hoạt động chọn từ dịch vụ
   `activity` của Booking (theo luật: hoạt động chỉ bán qua nhà cung cấp AA). Bữa ăn là 3 ô tick B / L / D.
   **Không thành hai nguồn sự thật:** các ô này là dữ kiện mô tả cho khách. Thành phần dùng để tính giá và đặt dịch vụ
   vẫn là `booking.trip_plan_components` do contracting giữ (T15, B12, B13 trong `advisory-r2-booking-ops.md`). Editor
   hiện cảnh báo khi hai bên lệch (ví dụ CIS ghi ngủ Cần Thơ đêm 2, Booking có khách sạn Bến Tre đêm 2). Câu chữ bán
   hàng ghi hạng + nơi, không ghi cứng tên khách sạn (T11 trong `advisory-r2-hotels.md`).
3. **Bao gồm / Không bao gồm (dữ kiện):** chip chọn nhanh từ danh sách chuẩn (xe đưa đón, vé tham quan, hướng dẫn
   tiếng Anh, bữa ăn theo lịch trình, khách sạn, nước uống), cộng dòng tự gõ. Một mục không được nằm ở cả hai bên.
4. **Ảnh:** kéo thả nhiều ảnh, cắt ảnh, chọn ảnh bìa, sắp thứ tự, alt text, quyền dùng (chi tiết ở M7).
5. **Câu chữ bán hàng (bản AA):** tên bán hàng, phụ đề, tóm tắt, điểm nổi bật, câu chữ từng ngày, tiêu đề và mô tả SEO
   (có đếm ký tự: tiêu đề ≤ 70, mô tả ≤ 170). Nút **"AI viết từ dữ kiện"** báo giá trước ("≈ 0,04 USD"); hoặc tự viết.
   Khi dữ kiện đổi, ngày nào đổi thì hiện nhãn vàng "Câu chữ chưa khớp dữ kiện mới" ngay ở ngày đó.
6. **Giá (chỉ đọc):** giá "từ" và trạng thái bán được lấy từ Booking (`booking.v_from_prices`, đã grant cho CIS), link
   "Sửa giá trong Booking". Nhân viên content không sửa giá.
7. **Lịch sử:** mọi phiên bản, ai sửa, lý do, nút "Xem diff", "Khôi phục bản này thành nháp".

**Tự lưu nháp:** lưu 1,5 giây sau khi ngừng gõ và khi rời ô. Góc trên hiện "Đang lưu…", "✓ Đã lưu nháp 10:42" hoặc
"⚠ Chưa lưu được, thử lại". Mỗi tour có **một bản nháp mở**; người thứ hai mở thấy "Lan đang sửa tour này từ 10:30,
[Xem chỉ đọc] [Vẫn sửa]". Ghi đè chéo bị chặn bằng cách AA content đang làm (`expected_updated_at`, 409 "người khác
vừa lưu"). Nháp không bao giờ lộ ra TripPlanner, CRM hay Booking.

**Hai lớp dữ liệu, nhân viên không cần biết tên kỹ thuật:** mục 1–4 là "dữ kiện" (ghi vào tour gốc, có lịch sử), mục 5
là "câu chữ" (phiên bản mới của bản AA). Một lần "Gửi duyệt" mang cả hai. Nhân viên không phải nhớ "raw", "Master".

#### M3. Xem trước như khách thấy

- Nút **Xem trước** mở toàn màn hình, 3 tab: **Trang TripPlanner**, **Thẻ tour trong CRM của đại lý**, **Đoạn tour
  trong báo giá PDF**. Chuyển Máy tính / Điện thoại.
- Cách làm đúng: **TripPlanner thêm một trang xem nháp** (`/preview/tours/[token]`) dùng đúng các component của trang
  tour thật, đọc bản nháp từ API CIS bằng một token ký sẵn, sống 15 phút, không cache, không cho Google lập chỉ mục
  (`noindex`). Như vậy xem trước giống 100% trang thật, không phải vẽ lại trong CIS.
- Ví dụ: Lan thấy trên điện thoại tên tour bị cắt "Mekong Delta Discovery with Floating Mar…" → rút tên ngay trong
  editor, khung xem trước cập nhật sau lần tự lưu.

#### M4. "Có gì thay đổi" (diff) trước khi xuất bản

```
┌ Có gì thay đổi so với bản đang bán (v7, 02/11, Minh) ───────────────────┐
│ Dữ kiện                                                                 │
│  Thời lượng      3 ngày 2 đêm  (không đổi)                              │
│  Ngày 2 · Ngủ tại  ─ Du thuyền Mekong ─   ＋ Khách sạn Cần Thơ ＋        │
│  Bao gồm         ＋ Nước uống trên xe                                    │
│ Câu chữ                                                                 │
│  Ngày 2   "...nghỉ đêm trên ~~du thuyền~~ **khách sạn ven sông**..."    │
│ Ảnh       ＋2 ảnh mới  [thumb][thumb]   −1 ảnh [thumb]   Ảnh bìa: đổi   │
├─────────────────────────────────────────────────────────────────────────┤
│ Ảnh hưởng khi xuất bản                                                  │
│  • TripPlanner cập nhật ngay (hệ thống báo trang làm mới)               │
│  • 4 đại lý có bản T2 của tour này → làm mới tự động ≈ 0,60 USD (xem T3)│
│  • 6 bài T9 trích tour này → đánh dấu "nguồn đã đổi"                    │
│  • 1 báo giá đang mở trong Booking giữ bản cũ (đã gửi khách)            │
│ Lý do sửa (bắt buộc) [NCC đổi nơi ngủ ngày 2, email 18/11]              │
│                                   [Quay lại sửa]  [Gửi duyệt / Xuất bản]│
└─────────────────────────────────────────────────────────────────────────┘
```

Diff theo **trường và theo ngày**, không phải diff cả khối văn bản. Ảnh so bằng hình nhỏ. Số đại lý, số bài T9 lấy từ
dữ liệu thật (cơ chế `source_fanout` đã có sẵn danh sách phụ thuộc).

#### M5. Xuất bản và duyệt

- Dev: người sửa tự xuất bản (T2). Prod: content bấm **Gửi duyệt**, content_lead nhận ở "Chờ duyệt" của bàn làm việc,
  thấy đúng màn M4, bấm **Xuất bản** hoặc **Trả lại** kèm lý do (chip chọn nhanh: thiếu ảnh, sai dữ kiện, câu chữ
  chưa đạt).
- Nút Xuất bản bị khoá khi còn mục ✗ trong danh sách bắt buộc, kèm dòng giải thích (giống `publishBlockers` của
  supply content).
- Sau xuất bản: toast "Đã xuất bản v8", link "Xem trang thật". Bản đã sửa tay được khoá: wave AI sau không ghi đè
  (khoá `human_lock` của bản trước).

#### M6. Sửa hàng loạt

Ví dụ: 14 tour Lào của cùng DMC cần thêm "Nước uống trên xe" vào Bao gồm.

1. Chọn 14 tour ở danh sách → **Sửa hàng loạt**.
2. Chọn thao tác (danh sách đóng, không gõ lệnh): thêm / bỏ một mục Bao gồm hoặc Không bao gồm; gắn nhà cung cấp; đổi
   mùa đẹp; thêm nhãn; AI viết lại câu chữ (báo giá trước); gỡ khỏi bán.
3. Màn xác nhận: "14 tour sẽ có bản nháp mới. 2 tour đã có nháp của người khác: bỏ qua." Xem diff của 1 tour mẫu.
4. Hệ thống tạo 14 bản nháp (không xuất bản thẳng), rồi "Xuất bản 12 tour đủ điều kiện" một lần (content_lead ở
   prod). Mỗi tour vẫn có lịch sử riêng.

Giới hạn mỗi lần (ví dụ 50 tour) là **một giá trị chỉnh được trong trang admin**, không viết cứng.

#### M7. Ảnh: upload, cắt, chọn bìa

```
┌ Ảnh (5/5 tối thiểu ✓) ───────────────── [Kéo thả ảnh vào đây] [Chọn từ thư viện] ┐
│ [★ bìa][ảnh2][ảnh3][ảnh4][ảnh5]   (kéo để đổi thứ tự)                             │
│ Ảnh đang chọn: ảnh2                                                              │
│  Khung cắt: [16:9 bìa] [4:3 thẻ] [1:1 mạng xã hội]   điểm lấy nét: (•)            │
│  Mô tả ảnh (alt) [Chợ nổi Cái Răng lúc sáng sớm      ]                           │
│  Nguồn & quyền   (•) Ảnh AA tự chụp  ( ) NCC cho phép  ( ) Ảnh mua bản quyền     │
│  Ghi công        [© Mekong Ways]                                                 │
│  ⚠ Ảnh 1200×800: nhỏ hơn mức tối thiểu cho ảnh bìa 1600×900                       │
└───────────────────────────────────────────────────────────────────────────────────┘
```

- Trình duyệt nén lại ảnh trước khi gửi (bỏ dữ liệu GPS, đổi về JPEG/WebP), giống cách Booking đã làm.
- **Cắt không phá ảnh gốc:** lưu ảnh gốc + toạ độ khung cắt + điểm lấy nét. Worker CIS sinh ảnh các cỡ khi xuất bản
  (thư viện Pillow, chạy trên worker có sẵn), 0 USD dịch vụ mới.
- **Thư viện ảnh chung:** ảnh tour, địa điểm, khách sạn, hoạt động chung một chỗ. Ảnh Drive cũ, ảnh nhà cung cấp do
  contracting upload ở Booking, và ảnh nhân viên upload ở CIS đều hiện trong thư viện, có nhãn nguồn. Ảnh chỉ được
  dùng khi quyền dùng đã xác nhận (luật đã có ở supply content).
- **Ảnh gốc của khách sạn / hoạt động do nhà cung cấp gửi vẫn vào ở Booking** (`entity_media`, cờ `usage_rights`, do
  contracting bật khi DMC xác nhận quyền, T11). Ở CIS nhân viên content chỉ chọn, cắt, sắp thứ tự, viết alt cho các ảnh
  đó. Upload ở CIS dành cho ảnh tour và địa điểm (AA tự chụp hoặc mua bản quyền), để quyền dùng ảnh nhà cung cấp chỉ có
  một chỗ ghi.
- Cần mở trang Ảnh cho vai trò `content` (G8).

#### M8. Editor khách sạn / hoạt động (nâng cấp trang supply content đang có)

Giữ trang `/admin/supply-content/[id]`, chỉ đổi phần sửa từ hộp thoại sang **cùng khung editor M2**: tự lưu nháp, cột
"Dữ kiện từ Booking" (chỉ đọc: hạng sao, loại phòng, giờ nhận/trả phòng, tiện ích), mục Ảnh dùng M7, và xem trước
"đoạn khách sạn trong báo giá" và "thẻ hoạt động trên TripPlanner". Lý do: phần duyệt / phiên bản đã chuẩn, chỉ thiếu
trải nghiệm nhập liệu (G14).

Ví dụ khách sạn: Booking có "Riverside Can Tho, 4 sao, 2 loại phòng Deluxe / Suite, BB". AI viết nháp 120 từ. Lan sửa
câu "gần chợ nổi" thành "cách chợ nổi Cái Răng 15 phút đi thuyền" (có trong ghi chú của DMC), chọn 6 ảnh, xuất bản.
Booking và CRM hiện mô tả mới ngay (view `catalog.v_supply_content` đã có).

#### M9. Nhập Excel lại khi tour đã sửa tay (gắn với T1)

```
Sapa Trek 4N3Đ — Excel mới (18/11) so với bản hiện tại (Lan sửa 12/11)
Trường          Excel mới           Hiện tại             Chọn
Thời lượng      5 ngày 4 đêm        4 ngày 3 đêm         (•) Nhận Excel ( ) Giữ
Ngày 3 mô tả    "Trek Tả Van..."    "Trek Tả Van, ..."   ( ) Nhận ( ) Giữ  ← Lan đã sửa
Bao gồm         + "Vé cáp treo"     —                    (•) Nhận  ( ) Giữ
5 trường không ai sửa tay: tự nhận theo Excel (vẫn ghi lịch sử)
                                         [Áp dụng → tạo bản nháp]
```

### T4.5 Quy tắc kiểm tra ngay khi gõ và danh sách bắt buộc

**Kiểm ngay tại ô (lời nhắc bằng câu thường, không mã lỗi):**

| Ô | Quy tắc | Ví dụ lời nhắc |
|---|---|---|
| Tên | 10–120 ký tự, không trùng tour đang bán cùng nhà cung cấp | "Tên này đã có ở tour VN-MKG-012" |
| Thời lượng / lịch trình | Số thẻ ngày = số ngày | "Thời lượng 3 ngày nhưng mới có 2 ngày" |
| Số đêm | = số ngày − 1, trừ khi tick "tour kết thúc đêm" | "3 ngày thường là 2 đêm, kiểm lại?" |
| Ngày có ngủ đêm | Phải có "Ngủ tại", trừ ngày cuối | "Ngày 2 chưa có nơi ngủ" |
| Bao gồm / Không bao gồm | Không trùng mục | "'Bữa trưa' nằm ở cả hai bên" |
| Hoạt động | Phải là dịch vụ của nhà cung cấp AA (luật 19/11) | "Hoạt động này chưa có nhà cung cấp trong Booking" |
| Câu chữ | Không dùng từ cấm (rẻ nhất, book now…), lớp từ cấm đã có ở CIS | "Không dùng 'cheapest' trong câu chữ AA" |
| SEO | Tiêu đề ≤ 70, mô tả ≤ 170 ký tự | thanh đếm đổi màu |
| Ảnh | Bìa ≥ 1600×900; mỗi ảnh có quyền dùng và alt | "Ảnh 3 chưa xác nhận quyền dùng" |

**Danh sách bắt buộc để gửi duyệt (12 mục, ví dụ ban đầu; ngưỡng chỉnh được trong admin):**
tên; nước; nhà cung cấp AA; số ngày / đêm; đủ thẻ ngày; mỗi ngày ≥ 1 địa điểm; ≥ 3 mục bao gồm; ≥ 1 mục không bao gồm;
≥ 5 ảnh có quyền; có ảnh bìa; tóm tắt; lý do sửa (khi sửa tour đang bán).

### T4.6 Dữ liệu và backend cần thêm

Mỗi app chỉ migrate schema của mình. Thêm cấu trúc mới trước, khoá cách ghi cũ sau.

| Việc | App | Ghi chú |
|---|---|---|
| Bảng bản nháp tour (một nháp mở mỗi tour, nội dung dạng JSON, người sửa, `updated_at` chống ghi đè) | CIS | Lịch trình lưu **có cấu trúc theo ngày** trong nháp; khi xuất bản vẫn ghi ra `src_itineraries` dạng chữ "Day 1: …" để pipeline S1 cũ chạy nguyên |
| Bảng lịch sử sửa tour gốc (chỉ thêm dòng) + cột `origin`, khoá `human_lock` | CIS | Như bản tư vấn trước |
| Cột ID nhà cung cấp trên tour gốc (soft key) | CIS | Xem T5 |
| `shared.place_photo`: cho phép ảnh không đến từ Drive (`drive_file_id` hiện NOT NULL), thêm nguồn, alt, điểm lấy nét, khung cắt, cơ sở quyền dùng | CIS | Hoặc bảng ảnh mới; chọn khi viết spec |
| API: tạo tour tay (đi qua cùng bước staging của Excel, nguồn `manual`, một batch riêng vì `raw_tours.batch_id` bắt buộc) | CIS | Tạo tour tay bắt buộc nhà cung cấp AA (T4 đã chọn) |
| API: token xem trước + trang `/preview/tours/[token]` | CIS + TripPlanner | Token ký, 15 phút, không cache, `noindex` |
| Báo TripPlanner làm mới trang sau **mọi** lần xuất bản | CIS | Hôm nay chỉ sự kiện vòng đời được báo ngay |
| View nhà cung cấp cho CIS | Booking | Xem T5 |
| Quyền: `content` vào trang Ảnh. Booking: không mở thêm quyền cho `content_creator`; vai trò này bị ẩn theo T13 (`advisory-r2-booking-ops.md`) | CIS, Booking | Nhỏ |

### T4.7 Thị trường làm thế nào

- **GetYourGuide, Viator (cổng cho nhà cung cấp):** tạo sản phẩm theo từng bước (thông tin, lịch trình, bao gồm, ảnh,
  giá), có thanh mức độ đầy đủ; sửa sản phẩm đang bán thì bản sửa vào hàng chờ duyệt rồi mới lên. Chắc chắn về hàng
  chờ duyệt; thanh "điểm chất lượng nội dung" của Viator thì tôi khá chắc nhưng chưa kiểm lại.
- **Bókun, Rezdy (phần mềm đặt tour cho nhà điều hành):** trang sửa sản phẩm chia mục (mô tả, ảnh, lịch trình, giá,
  lịch chạy) ở cột trái. Chắc chắn về bố cục chia mục; chi tiết từng màn chưa kiểm.
- **Tourplan, Lemax (hệ thống của DMC / tour operator):** đội product nhập sản phẩm có cấu trúc (ngày, dịch vụ, nhà
  cung cấp), câu chữ marketing là lớp riêng. Mức chung, không nhớ chi tiết màn hình.
- **Contentful, WordPress (hệ quản lý nội dung):** trạng thái Nháp / Đã đổi / Đã xuất bản, tự lưu, xem lại và so sánh
  phiên bản (WordPress "Revisions"), xem trước trước khi xuất bản. Chắc chắn.
- **Cắt ảnh có điểm lấy nét:** Contentful và Cloudinary có điểm lấy nét để cắt tự động nhiều khung. Khá chắc.

Điểm chung AA nên học: **một editor chia mục + thanh đầy đủ + nháp tự lưu + xem trước thật + duyệt trước khi lên**.

### T4.8 Lộ trình (mỗi dòng là 1 PR hoặc nhóm PR nhỏ)

| Bước | Nội dung | Ngày công lane | Chi phí |
|---|---|---|---|
| 1 | Nền: bảng nháp, lịch sử sửa, khoá; view nhà cung cấp Booking (T5); mở quyền Ảnh cho `content`; vá promote phải kiểm lại | 4–5 | 0 USD |
| 2 | Editor tour M2: khung 3 cột, mục 1–3 + 5, tự lưu, kiểm tại ô, danh sách bắt buộc; drawer cũ thành chỉ đọc + nút "Mở editor" | 7–8 | 0 USD |
| 3 | Diff M4 + xuất bản / duyệt M5 + bàn làm việc M0 + danh sách M1 | 4–5 | 0 USD |
| 4 | Ảnh M7: upload, cắt, bìa, thư viện chung | 4–5 | ~0 USD (S3 vài GB) |
| 5 | Xem trước M3 (trang preview TripPlanner) + tạo tour tay + nhập Excel lại M9 (T1) | 4–5 | 0 USD |
| 6 | Sửa hàng loạt M6 + nâng cấp editor khách sạn / hoạt động M8 | 3–5 | LLM chỉ khi bấm AI viết, trong trần Dev |
| | **Tổng** | **26–33** | **0 USD hạ tầng mới** |

Sau bước 2 nhân viên đã làm được việc thật (sửa có nháp). Bước 5 xong thì thay được Excel cho tour lẻ.
Bảng ngày công chỉ để so độ lớn; lịch thật theo phiên ở `advisory-r2-plan.md` (bước 1–3 và M9 thuộc lát L3, tạo tour
tay và view nhà cung cấp T5 thuộc lát L4).

### T4.9 Chưa kiểm

- Chi phí S1 thật cho một tour 3 ngày (số 0,02–0,05 USD ở trên là ước, cần đọc `shared.llm_call_log`).
- Số tour có `provider` khớp được với nhà cung cấp Booking.
- TripPlanner dùng CDN ảnh nào để sinh cỡ ảnh; nếu đã có bộ đổi cỡ ảnh thì bước cắt ảnh dùng lại.

### Đề xuất cuối T4

Chọn **Có**, nhưng không chỉ "cho tạo tour tay": làm **bộ công cụ content** gồm bàn làm việc, danh sách, editor tour
chia mục có tự lưu nháp và kiểm tại ô, xem trước bằng trang TripPlanner thật, màn "có gì thay đổi" kèm ảnh hưởng, duyệt
/ xuất bản, ảnh có cắt và quyền dùng, sửa hàng loạt; nâng editor khách sạn / hoạt động lên cùng khung. Nhân viên content
chỉ làm việc trong CIS, không cần vào Booking (thông tin Booking hiện chỉ đọc trong CIS). Tạo tour tay bắt buộc gắn nhà cung cấp AA và đi qua duyệt. 6 bước,
26–33 ngày công lane, 0 USD hạ tầng mới.

---

## T3. Đổi dữ kiện ở CIS thì bản T2 của đại lý có tự làm lại không

### T3.1 Giải thích đơn giản

Có 3 bản chữ của cùng một tour:

1. **Bản AA (Master):** AA viết, giọng trung tính. CRM dùng **dữ kiện** từ đây khi đại lý thêm tour AA vào báo giá
   (ngày, bao gồm, không bao gồm), và giá lấy trực tiếp từ Booking.
2. **Bản T2 của đại lý:** AI viết lại bản AA theo giọng thương hiệu của đại lý. Đại lý dùng để quảng bá: tải DOCX, đưa
   lên website, làm nguồn cho bài T9. Đại lý còn **tự sửa** được bản này (code: `v1_tours.py`, mỗi lần sửa là phiên bản
   mới với `edit_source = 'tenant_edit'`).
3. **Bài T9:** bài blog, mạng xã hội trích tour.

Hôm nay, khi nhân viên AA sửa dữ kiện, CIS chạy `source_fanout`: **chỉ đánh dấu** T2 và T9 là "nguồn đã đổi" trong
trang admin. Không viết lại gì, đại lý không được báo, trang của đại lý không đổi
(`services/quality/source_fanout.py`, đầu file ghi rõ "Nothing is regenerated").

### T3.2 Nếu KHÔNG làm lại T2: chuyện gì xảy ra

Ví dụ: tour "Hạ Long 2N1Đ". Nhà cung cấp bỏ đêm trên du thuyền, đổi thành đi trong ngày và ngủ khách sạn Hà Nội.
Nhân viên AA sửa và xuất bản.

- Báo giá đại lý gửi khách (lấy dữ kiện từ bản AA, giá từ Booking): "Ngày 1: du thuyền đi trong ngày, đêm khách sạn
  Hà Nội". Giá đã theo khách sạn.
- Trang website của đại lý (bản T2 cũ): "Ngủ đêm trên du thuyền giữa vịnh, ngắm hoàng hôn từ cabin".
- Khách đặt vì câu "ngủ trên vịnh", đến nơi không có → khiếu nại, đòi hoàn tiền, đại lý mất uy tín, AA mất đại lý.

Về giá: T2 **thường không chứa giá bán**, vì giá do Booking trả trực tiếp. Rủi ro "giá cũ" chỉ xảy ra khi câu chữ có
nhắc số tiền (ví dụ "đã gồm vé tham quan 25 USD"). Rủi ro chính là **lịch trình, bao gồm, nơi ngủ cũ**.

### T3.3 Nếu tự làm lại T2 mà không cẩn thận: chuyện gì xảy ra

- **Mất bản đại lý tự sửa:** đại lý đã thêm câu riêng ("đón khách tận khách sạn ở phố cổ"), bản mới ghi đè thì mất.
- **Tốn tiền vô ích:** một bản T2 tốn khoảng 0,12–0,27 USD (đo ở AA-800, AA-801). Sửa 50 tour × 10 đại lý / tháng là
  500 lượt ≈ 60–135 USD, kể cả khi chỉ sửa một dấu phẩy.
- **Đại lý bị bất ngờ:** chữ trên kênh của họ tự đổi mà không biết.
- **Bài đã đăng không tự đổi:** bài đã đưa lên website đại lý thì phải đăng lại, làm mới T2 không tự sửa được bài cũ.

### T3.4 Logic đúng

1. **Chỉ làm lại khi dữ kiện đổi, máy tự nhận biết.** CIS đã có cách so: dựng lại "FactSheet" (bảng dữ kiện) của tour,
   so với bảng dữ kiện mà bản T2 đã đọc. Giống nhau → không làm gì; khác → mới làm tiếp. Chỉ sửa câu chữ bản AA → không
   chạm T2 (đúng đề xuất cũ).
2. **Chỉ làm cho đại lý thật sự đang dùng tour:** có bản T2 đã duyệt, hoặc tour nằm trong báo giá / bài T9 còn hiệu lực.
   Đại lý chỉ xem qua thì không tốn tiền.
3. **Hai trường hợp:**
   - Đại lý **chưa tự sửa** bản T2: AI viết bản mới → kiểm chất lượng tự động → đạt thì thay bản đang dùng → báo đại lý
     "AA đã cập nhật tour Hạ Long: ngày 1 đổi nơi ngủ, bản của bạn đã được làm mới".
   - Đại lý **đã tự sửa**: AI viết bản mới thành **bản chờ** (không thay). Đại lý thấy banner đỏ "Lịch trình AA đã đổi,
     bản của bạn đang lỗi thời", màn so sánh 3 cột (bản của bạn / dữ kiện mới / bản AI đề xuất), một nút "Nhận bản mới"
     hoặc "Tự sửa".
4. **Có trần chi phí tháng, chỉnh trong admin** (đề xuất 10 USD/tháng ở Dev ≈ 40–80 lượt với 0,12–0,27 USD/lượt, khớp
   `advisory-r2-plan.md`; mức chính xác đặt theo chi phí thật trong `shared.llm_call_log`). Hết trần → không viết lại,
   chỉ đánh dấu lỗi thời và báo đại lý, đại lý bấm "Làm mới" khi cần.
5. **Trong lúc chờ, an toàn trước:** báo giá CRM vẫn lấy dữ kiện mới từ bản AA (như hôm nay). Bản T2 lỗi thời hiện
   cảnh báo ở Content studio của đại lý và khi xuất DOCX.
6. **Báo giá đã gửi khách giữ bản chụp cũ** (chưa kiểm cách Booking giữ bản chụp); nhân viên sales được báo để liên hệ
   lại khách nếu thay đổi quan trọng.

Ví dụ chi phí: tour Hạ Long có 6 đại lý dùng, 4 chưa tự sửa, 2 đã sửa. Một lần đổi dữ kiện → 6 lượt × ~0,15 USD
≈ 0,90 USD. 4 bản tự thay, 2 bản chờ đại lý bấm.

### T3.5 Thị trường

Mô hình "nội dung gốc, các kênh bán bản riêng" có ở Viator / GetYourGuide (nhà cung cấp sửa, kênh nhận bản mới sau
duyệt). Việc AI viết lại theo giọng từng đại lý thì tôi không biết hệ thống nào làm sẵn để so sánh; đây là cách riêng của
AA.

### Đề xuất cuối T3

Có, làm lại T2 khi **dữ kiện** đổi (máy tự so bảng dữ kiện), chỉ cho đại lý đang dùng tour, trong trần chi phí tháng
chỉnh được ở admin. Bản đại lý chưa sửa thì tự thay sau khi qua kiểm tra; bản đại lý đã sửa thì thành bản chờ, kèm
banner và màn so sánh để đại lý chọn. Hết trần thì chỉ đánh dấu lỗi thời và báo. Chỉ đổi câu chữ thì không chạy lại.

---

## T5. Nhà cung cấp của tour: từ chữ tự do sang ID nhà cung cấp Booking

### T5.1 Kiểm tra thực tế

- **Đúng, bảng nhà cung cấp chỉ có ở Booking:** `booking.suppliers` (chủ `bk_owner`), có id, code, company_name,
  categories, country_code, status, cùng thông tin liên hệ (là dữ liệu cá nhân) và ghi chú nội bộ (dữ liệu thương mại).
  Hôm nay **chỉ role `booking` được đọc**, CIS không đọc được.
- **CIS chỉ có chữ tự do:** `silver_aa_internal.raw_tours.provider varchar(255)`, đến từ cột Excel. Không có bảng nhà
  cung cấp nào ở CIS. (Trong CRM có `crm.agency_supplier`: đó là danh bạ riêng của đại lý, không phải nguồn này.)
- **Booking đã gắn tour với nhà cung cấp:** `booking.trip_plans.supplier_id` (bk-032), contracting chọn trong ngăn
  "Commercial" của trip plan. Nghĩa là thông tin "tour này mua của ai" **đã có một chỗ ở Booking**.
- **Lưu ý mới:** loại nhà cung cấp chỉ được là hotel, transport, guide, entrance, activity, meal, và tối đa 6 loại
  (CHECK `suppliers_categories_chk`, `cardinality(categories) <= 6`). **Không có loại "DMC"**, trong khi luật 19/11 nói
  tour đến từ nhà cung cấp AA gồm đủ xe, vé, khách sạn, hướng dẫn viên, bữa ăn, hoạt động. Booking nên thêm loại `dmc`
  và nới giới hạn lên 7. Đặt tên `dmc`, không đặt `tour`: AA vẫn mua tour **bóc tách từng dịch vụ**, không mua trọn gói
  một giá (B12 trong `advisory-r2-booking-ops.md`).
- **Đã có mẫu để làm theo:** Booking đã mở 4 view chỉ đọc cho CIS (`v_supply_hotels`, `v_supply_services`,
  `v_supply_media`, `v_supply_outbox`, bk-023), cộng `v_from_prices` (bk-040). Thêm một view nhà cung cấp là cùng một
  kiểu việc.

### T5.2 Ba cách cho CIS đọc nhà cung cấp

| | A. View chỉ đọc + grant (**chọn**) | B. CIS gọi API Booking | C. Chép danh sách sang CIS |
|---|---|---|---|
| Cách làm | Booking tạo `booking.v_supply_suppliers` (id, code, company_name, categories, country_code, status, updated_at; **không** liên hệ, ghi chú, giá), grant SELECT cho `cis_app` | CIS gọi `GET /booking/suppliers` bằng tài khoản máy (M2M) | Job đêm chép bảng sang CIS |
| Dữ liệu mới | Luôn mới (đọc thẳng) | Luôn mới | Trễ đến 1 ngày |
| Phụ thuộc | Chỉ DB dùng chung (đã có) | Booking API phải sống; thêm token, mạng | Thêm job, thêm bảng phải dọn |
| Công | ~0,5 ngày Booking + 0,5 ngày CIS | 2–3 ngày | 2 ngày + bảo trì |
| Hợp kiến trúc | Đúng mẫu bk-017 / bk-023 | Dùng cho đại lý ở ngoài, không cần cho app nội bộ cùng DB | Hai bản sự thật |

### T5.3 Cách làm khuyến nghị

1. **Booking (migration bk-NNN):** thêm loại `dmc` vào danh sách loại (và nới giới hạn số loại từ 6 lên 7); tạo view `booking.v_supply_suppliers` chỉ có
   các cột trên, `security_barrier`, grant SELECT cho `cis_app`. Đặt tên hợp đồng (ví dụ `supply.supplier.v1`), cột chỉ
   được thêm, không đổi.
2. **CIS (migration):** thêm cột `supplier_id uuid` (soft key, không FK sang schema khác) vào tour gốc. **Giữ `provider`**
   làm "tên gốc trong Excel" để đối chiếu.
3. **Điền dữ liệu cũ:** so `provider` (bỏ dấu, viết thường) với `company_name` cùng nước. Khớp chắc thì gán; không khớp
   thì vào danh sách "Tour chưa gắn nhà cung cấp" để content_lead chọn bằng sửa hàng loạt (M6).
4. **Màn hình:** ô "Nhà cung cấp AA" trong editor là ô tìm và chọn (chỉ nhà cung cấp `active`, ưu tiên loại `dmc`).
   Danh sách tour hiện tên lấy trực tiếp từ view, nên đổi tên ở Booking là CIS thấy ngay. Nhà cung cấp bị ngưng thì
   tour hiện nhãn "Nhà cung cấp đã ngưng".
5. **Tránh hai nguồn sự thật với `trip_plans.supplier_id`:** CIS đưa `supplier_id` vào `catalog.v_tour` (view CIS,
   Booking đã đọc). Booking dùng giá trị đó **điền sẵn** cho trip plan chưa gắn; contracting vẫn được đổi (ví dụ cùng
   chương trình do DMC khác vận hành). Khi hai giá trị khác nhau, trang trip plan hiện cảnh báo nhỏ "Khác nhà cung cấp
   ghi ở CIS". Ý nghĩa: CIS giữ "chương trình này lấy từ nhà cung cấp nào" (nguồn nội dung); Booking giữ "Đầu mối vận
   hành" (B12: DMC chính lo tour ở nước sở tại, dùng để lọc khi chọn thành phần và in số khẩn cấp lên voucher, không
   dùng tính giá). Nhà cung cấp thật của từng dịch vụ nằm ở từng thành phần tour trong Booking.

Ví dụ: Excel ghi `provider = "Mekong Ways Co., Ltd"`, Booking có `SUP-0042 Mekong Ways` ở VN → tự gán. Excel ghi
"MW travel" → không khớp → vào danh sách chờ, Lan chọn SUP-0042 cho cả 9 tour một lần.

### Đề xuất cuối T5

Có. Booking mở view chỉ đọc `booking.v_supply_suppliers` (không liên hệ, không ghi chú, không giá) cho `cis_app`, đúng
mẫu các view supply đã có, và thêm loại nhà cung cấp `dmc` (nới giới hạn số loại lên 7). CIS lưu `supplier_id` dạng soft key, giữ `provider`
làm tên gốc Excel, điền dữ liệu cũ bằng so tên + danh sách chờ. Booking dùng giá trị của CIS để điền sẵn
`trip_plans.supplier_id` và cảnh báo khi khác. Làm cùng bước nền của T4.

---

## T1. Nhà cung cấp gửi lại Excel sau khi nhân viên đã sửa: bên nào thắng

Giữ đề xuất: **bản sửa tay thắng**, lần import sau hiện màn so sánh từng trường (M9). Bổ sung 2 điểm:

- Trường **không ai sửa tay** thì tự nhận theo Excel (vẫn ghi lịch sử), để nhân viên chỉ phải quyết vài trường thật sự
  xung đột. Ví dụ: Excel mới đổi 7 trường, Lan chỉ từng sửa 1 → 6 trường tự nhận, 1 trường hỏi.
- Kết quả là **một bản nháp**, đi qua duyệt như mọi lần sửa khác, không xuất bản thẳng.

Thị trường: các hệ quản lý thông tin sản phẩm (PIM, product information management) thường có luật "nguồn nào ưu tiên
cho trường nào" khi nhập lại; tôi không chắc tên hệ cụ thể nào làm đúng màn so sánh từng trường như trên.

**Đề xuất cuối T1:** giữ nguyên, bản sửa tay thắng; trường chưa ai sửa tự nhận; trường xung đột hỏi người; kết quả là
bản nháp qua duyệt.

## T2. Có cần 2 người (người sửa không tự xuất bản) không

Giữ đề xuất: **Dev cho tự xuất bản** (một kỹ sư, chưa có khách thật). **Từ prod:** `content` sửa và gửi duyệt,
`content_lead` (hoặc admin) xuất bản. Màn duyệt chính là màn "Có gì thay đổi" (M4), nên người duyệt mất 1–2 phút mỗi
tour. Công tắc "cần người thứ hai duyệt" là giá trị chỉnh được trong admin, không viết cứng.

Thị trường: WordPress có vai trò Contributor (viết, không xuất bản được) và Editor (xuất bản); GetYourGuide / Viator
duyệt bản sửa của nhà cung cấp trước khi lên. Chắc chắn.

**Đề xuất cuối T2:** giữ nguyên. Dev tự xuất bản; từ prod người sửa không tự xuất bản, bật bằng công tắc trong admin.
