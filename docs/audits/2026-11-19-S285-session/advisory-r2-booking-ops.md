# Tư vấn vòng 2: vai trò, tách tour, thuộc tính dịch vụ, hồ sơ nhà cung cấp (T13, T15, T16, T17, B12, B13)

Phiên S285, 19/11/2026. Viết cho tech lead, trả lời ghi chú của anh trên trang quyết định (`decisions2`).
Dựa trên: `advisory-booking-supply-coverage.md`, `advisory-supply-coverage-critic.md`, `apps/AA-Booking/CONTEXT.md`,
code `apps/AA-Booking/backend/app/...` và `docs/architecture/db-schema-reference.md` (dump 18/11, Booking bk-059).
Chỉ đọc, không đổi code. Chi phí hạ tầng của mọi đề xuất: 0 USD (không dịch vụ AWS mới, không gọi LLM).

Luật nền (business owner, 19/11): mọi dữ liệu sản phẩm thuộc AA và nhà cung cấp của AA; đại lý chỉ dùng app. Một tour
của nhà cung cấp AA gồm xe, vé, khách sạn, hướng dẫn viên, ăn uống, hoạt động. Khách sạn nhập tay từ bảng giá của nhà
cung cấp; quan hệ với khách sạn do DMC giữ.

**Từ ngữ dùng trong bài** (giải thích một lần):

- **DMC** = destination management company, công ty lữ hành địa phương lo toàn bộ dịch vụ mặt đất (xe, khách sạn,
  hướng dẫn viên...) ở một nước.
- **Nhà cung cấp (supplier)** = bên AA trả tiền để có dịch vụ: DMC, nhà xe, nhà hàng, hướng dẫn viên tự do.
- **Thành phần tour (component)** = một dịch vụ cụ thể trong một ngày của tour, ví dụ "đêm 2 khách sạn X" hay
  "xe ngày 3 Hà Nội đi Hạ Long". Bảng `booking.trip_plan_components`.
- **Đặt dịch vụ với nhà cung cấp (supplier booking, mã `SB-000123`)** = một yêu cầu AA gửi nhà cung cấp, có trạng thái
  chờ gửi → đã gửi → đã xác nhận / từ chối / huỷ. Bảng `booking.supplier_bookings`.
- **Voucher** = phiếu dịch vụ, giấy khách hoặc hướng dẫn viên đưa cho khách sạn, nhà xe để nhận dịch vụ.
- **PO** = purchase order, đơn đặt hàng gom nhiều đặt dịch vụ của cùng một nhà cung cấp trong một tháng.
- **Maker-checker** = người tạo và người duyệt phải là hai người khác nhau (chống sai sót và gian lận).
- **Stop-sale** = tạm ngừng bán một khoảng ngày (ví dụ khách sạn kín phòng dịp Tết).
- **Snapshot** = bản chụp: chép dữ liệu ra một bảng riêng tại một thời điểm, sau đó không đổi theo bản gốc nữa.
- **CHECK** = ràng buộc trong DB, chỉ cho một cột nhận các giá trị hợp lệ (ví dụ số chỗ chỉ có ở dịch vụ xe).
- **Audit** = nhật ký ghi lại ai đổi gì, lúc nào, lý do.

---

## T13. Vai trò trong Booking: gọn cho một startup

### Ghi chú của tech lead

"Các vai trò có vẻ nhiều với một startup." Đúng. Đề xuất cũ thêm vai trò thứ sáu `ops`. Bản này đề xuất ngược lại: bớt
xuống còn 4 vai trò, không thêm `ops` lúc này.

### Hôm nay đang có gì (đã đọc code)

- Booking có 5 vai trò: `admin`, `sales`, `contracting`, `content_creator`, `finance`
  (`backend/app/auth/staff.py:72`).
- **Mỗi người chỉ có 1 vai trò trong Booking**: lấy nhóm `booking-*` đầu tiên theo thứ tự ưu tiên
  (`staff.py:351-356`). Trang Staff của CIS cũng ghi "one role per app" (`AA-CIS-App/api/services/staff_directory.py:138`).
- `content_creator` trong Booking chỉ được **xem catalog** (`catalog.read`), không làm gì khác. Đội nội dung làm việc
  ở CIS, không cần vào Booking.
- Việc "ops" (đặt dịch vụ, voucher, PO) hiện đã mở cho `admin`, `sales`, `contracting` (`ops.read` / `ops.write`,
  `staff.py:142-143`). Code ghi rõ "no separate ops role yet, design D16".
- Stop-sale hiện là một khoảng trong lịch mùa của tour; quyền `season.write` / `season.approve` = `admin`,
  `contracting` (`staff.py:189-190`).
- Trả tiền cho nhà cung cấp (`payout.write`) hiện chỉ `admin` (`staff.py:157`). `finance` không đọc được hoá đơn nhà
  cung cấp (`bill.read` không có `finance`).

### Bộ vai trò gọn đề xuất (4 vai trò)

| Vai trò (tên hiển thị) | Mã giữ nguyên | Người làm thực tế | Làm được gì |
|---|---|---|---|
| Quản trị | `admin` | Business owner, tech lead dự phòng | Mọi thứ; người duyệt cuối khi thiếu người thứ hai |
| Bán hàng | `sales` | Người nói chuyện với đại lý / khách | Hồ sơ khách, báo giá, đặt thay đại lý, hoá đơn khách, xem giá và nhà cung cấp, đặt dịch vụ |
| Sản phẩm & điều hành | `contracting` | Người nhập giá DMC, dựng tour, đặt dịch vụ | Nhà cung cấp, hợp đồng, giá, thành phần tour, mùa, stop-sale, đặt dịch vụ, voucher, PO, nhập hoá đơn nhà cung cấp |
| Kế toán | `finance` | Kế toán (có thể thuê ngoài) | Hoá đơn đại lý, ghi nhận tiền về, lợi nhuận, **trả tiền nhà cung cấp** |

Thay đổi so với hôm nay (đều nhỏ, chỉ sửa ma trận trong `staff.py` và nhãn, không cần migration):

1. **Không thêm `ops`.** Đặt dịch vụ vẫn do `sales` và `contracting` làm như hiện tại.
2. **Đổi tên hiển thị** `contracting` thành "Sản phẩm & điều hành" (mã giữ nguyên, khỏi đổi nhóm Cognito).
3. **Ẩn `content_creator`** khỏi danh sách chọn vai trò Booking trên trang Staff CIS. Ai cần xem catalog thì đã có ở
   CIS. Chưa kiểm trên Dev có ai đang giữ vai trò này không; nếu có, chuyển họ sang không có quyền Booking.
4. **Stop-sale** = `contracting` + `admin` (đúng như hiện tại), duyệt hai người như mùa.
5. **Kế toán trả tiền nhà cung cấp**: thêm `finance` vào `bill.read` và `payout.write`. Người nhập và duyệt hoá đơn
   nhà cung cấp vẫn là `contracting` (họ biết dịch vụ có thật hay không). Như vậy tách tự nhiên: người đặt dịch vụ
   không tự trả tiền.

### Maker-checker với đội nhỏ: cần tối thiểu mấy người

Ví dụ một đội 4 người: chị chủ (admin), Lan (Sản phẩm & điều hành), Minh (Bán hàng), Hà (Kế toán thuê ngoài).

- Lan nhập file Excel giá của DMC "Bắc Việt" → hợp đồng nháp. Người công bố phải khác Lan: chị chủ (admin) bấm
  công bố. Mỗi lần đổi giá như vậy chỉ mất 1 phút của chị chủ.
- Minh báo giá cho đại lý thấp hơn biên lợi nhuận sàn → cần Lan hoặc chị chủ duyệt (`b2b_desk.approve`).
- Lan nhập hoá đơn 12.500.000 VND của DMC → chị chủ duyệt hoá đơn → Hà chuyển khoản. Ba người, không ai tự
  làm trọn một vòng tiền.

Kết luận: 4 vai trò, 3 đến 4 người là chạy được toàn bộ quy trình hai người duyệt. Khi chỉ có 1 người
"Sản phẩm & điều hành", admin là người duyệt thứ hai.

### Khi nào mới tách thêm vai trò

| Tách ra | Khi nào |
|---|---|
| `ops` (điều hành / đặt chỗ) tách khỏi "Sản phẩm & điều hành" | Có từ 2 người làm đặt chỗ toàn thời gian, hoặc khoảng trên 200 đặt dịch vụ mỗi tháng, hoặc tuyển nhân viên mới mà không muốn họ sửa giá |
| `viewer` (chỉ xem) | Khi có kiểm toán, nhà đầu tư hay đối tác cần xem mà không được sửa |
| Cho một người giữ 2 vai trò cùng lúc | Khi xảy ra trường hợp một người vừa bán vừa nhập giá mà không nên làm admin. Việc này phải sửa cả Booking (`booking_role` trả về tập vai trò) và trang Staff CIS, nên chỉ làm khi thật cần |

### Thị trường làm thế nào

Tourplan và Lemax không cố định danh sách vai trò; họ cho tạo nhóm người dùng và tick quyền theo từng chức năng.
Ở các công ty lữ hành nhỏ, cách chia phổ biến là 4 khối: bán hàng, sản phẩm/hợp đồng, điều hành (reservations), kế
toán; công ty dưới 10 người thường gộp sản phẩm với điều hành. (Con số "200 đặt dịch vụ/tháng" là ước lượng của tôi,
không phải chuẩn ngành.)

### Đề xuất cuối (T13)

4 vai trò: Quản trị, Bán hàng, Sản phẩm & điều hành (mã `contracting`), Kế toán. Không thêm `ops`. Ẩn
`content_creator` khỏi Booking. Stop-sale = Sản phẩm & điều hành + Quản trị. Kế toán được xem hoá đơn nhà cung cấp và
trả tiền. Tách `ops` khi có từ 2 người đặt chỗ toàn thời gian hoặc khoảng 200 đặt dịch vụ mỗi tháng.

---

## T15. Tách tour đã bán thành từng đặt dịch vụ với nhà cung cấp

### Ghi chú của tech lead

"Chưa hiểu rõ." Dưới đây là một ví dụ đi trọn từ lúc đại lý đặt tới màn hình điều hành.

### Ví dụ: đại lý đặt tour Hà Nội – Hạ Long 5 ngày

Đại lý "Sunrise Travel" đặt tour "Hà Nội – Hạ Long 5 ngày" cho 4 người lớn, khởi hành 10/03/2027.
Trong Booking, tour này đã có 12 thành phần (bảng `trip_plan_components`):

| Ngày | Thành phần | Nhà cung cấp | Giá net (giá AA trả) |
|---|---|---|---|
| 1 | Xe đón sân bay Nội Bài, xe 7 chỗ | DMC Bắc Việt | 600.000 VND/xe |
| 1 | Khách sạn Hà Nội, phòng đôi | DMC Bắc Việt | 1.200.000 VND/phòng/đêm × 2 phòng |
| 2 | Xe Hà Nội → Hạ Long | DMC Bắc Việt | 2.200.000 VND/xe |
| 2 | Du thuyền Hạ Long 1 đêm, cabin đôi | Công ty du thuyền Hạ Long | 3.000.000 VND/cabin × 2 |
| 2 | Ăn trưa trên tàu | Công ty du thuyền Hạ Long | 250.000 VND/người |
| 3 | Xe Hạ Long → Hà Nội | DMC Bắc Việt | 2.200.000 VND/xe |
| 3 | Khách sạn Hà Nội | DMC Bắc Việt | 1.200.000 × 2 phòng |
| 4 | Hướng dẫn viên tiếng Anh cả ngày | DMC Bắc Việt | 800.000 VND/ngày |
| 4 | Vé Văn Miếu | DMC Bắc Việt | 30.000 VND/người |
| 4 | Ăn trưa nhà hàng | Nhà hàng Phố Cổ | 300.000 VND/người |
| 4 | Khách sạn Hà Nội | DMC Bắc Việt | 1.200.000 × 2 phòng |
| 5 | Xe tiễn sân bay | DMC Bắc Việt | 600.000 VND/xe |

**Lúc báo giá**, Booking đã cộng đúng 12 dòng này để ra giá cho đại lý (`app/b2b/components.py:244-262`: một dòng `tp:`
bằng tổng các thành phần, mỗi thành phần lấy giá đang hiệu lực đúng ngày đó).

### Hôm nay chuyện gì xảy ra sau khi đại lý xác nhận

1. Booking tạo hồ sơ chuyến (trip case) và một phiên bản (version) có **đúng 1 dòng**: "Hà Nội – Hạ Long 5 ngày",
   không có khách sạn hay dịch vụ nào gắn vào (`app/b2b/holds.py:888-904`: `hotel_room_type_id` và `service_id`
   đều NULL với dòng `tp:`). Chi phí cũng gộp thành một con số.
2. Điều hành mở tab Suppliers, bấm Generate. Câu lệnh chọn dòng cần đặt bỏ qua mọi dòng không có khách sạn hay dịch
   vụ (`app/ops/supplier_bookings.py`, `ITEMS_SQL`, điều kiện `hotel_room_type_id IS NOT NULL OR service_id IS NOT
   NULL`). Kết quả: **0 đặt dịch vụ**.
3. Điều hành phải tự mở tour, nhìn 12 thành phần, tạo tay 12 đặt dịch vụ, tự tính ngày (10/03 + số ngày − 1), tự gõ
   số khách và giá. Dễ quên một xe, gõ sai ngày.
4. Kể cả muốn gắn 12 đặt dịch vụ đó vào dòng tour cũng không được: DB có index duy nhất
   `supplier_bookings_item_live_uq` (`db-schema-reference.md:3174`), mỗi dòng phiên bản chỉ được 1 đặt dịch vụ còn
   sống.

### Sau khi sửa: màn hình điều hành sẽ hiện gì

Lúc đại lý xác nhận (cùng lúc `holds.py` tạo phiên bản), Booking chép 12 thành phần đã dùng để báo giá vào một bảng
snapshot. Bấm Generate thì ra 12 đặt dịch vụ, mỗi cái đủ ngày, số khách, giá:

```
Chuyến TC-000245 · Sunrise Travel · 4 khách · 10/03 – 14/03/2027        12 cần đặt · 0 đã gửi · 0 đã xác nhận

Nhà cung cấp: DMC Bắc Việt (9 mục)                                       [Gửi PO cho DMC Bắc Việt]
  SB-000301  10/03  Xe đón sân bay, 7 chỗ, 1 xe           600.000     Chờ gửi
  SB-000302  10/03  KS Hà Nội, phòng đôi × 2, 1 đêm     2.400.000     Chờ gửi
  SB-000303  11/03  Xe Hà Nội → Hạ Long, 1 xe          2.200.000     Chờ gửi
  ...
Nhà cung cấp: Công ty du thuyền Hạ Long (2 mục)
  SB-000310  11/03  Du thuyền, cabin đôi × 2            6.000.000     Chờ gửi
  SB-000311  11/03  Ăn trưa trên tàu × 4                1.000.000     Chờ gửi
Nhà cung cấp: Nhà hàng Phố Cổ (1 mục)
  SB-000312  13/03  Ăn trưa × 4                         1.200.000     Chờ gửi
```

Từ đó điều hành làm như với một chuyến bình thường: gửi yêu cầu, nhập số xác nhận, in voucher, gom PO theo nhà
cung cấp, đối chiếu hoá đơn. Không phải gõ tay dòng nào.

### Snapshot là gì và vì sao cần

Snapshot là bảng mới (ví dụ `booking.trip_case_version_components`) lưu **đúng những gì đã bán**: dòng tour nào,
ngày thứ mấy, khách sạn/dịch vụ nào, số lượng, giá nào (mã giá `supplier_rate_id`), giá net.

Vì sao không đọc thẳng bảng thành phần của tour lúc Generate:

- Khi sửa thành phần, code **xoá hết rồi chèn lại** (`app/b2b/plan_components.py:131-138`). Ví dụ 15/12 Lan đổi
  khách sạn Hà Nội từ "Hotel A" sang "Hotel B" cho các đoàn sau. Nếu đọc thẳng bảng tour, đoàn Sunrise đã bán từ
  20/11 với Hotel A sẽ bị đặt nhầm sang Hotel B, sai với giá và chương trình đã gửi đại lý.
- Giá đại lý đã trả được tính từ các giá cụ thể. Snapshot giữ mã giá đó, nên sau này so hoá đơn nhà cung cấp với giá
  đã bán là so đúng.

Snapshot nên lấy **từ chính phép tính báo giá** (hàm `price_lines` đã có danh sách giá dùng cho từng thành phần, đang
lưu trong `supplier_rate_ids` của dòng giữ chỗ), không tính lại lần hai. Như vậy giá trên đặt dịch vụ luôn khớp giá
đã báo đại lý.

Thay đổi DB (một migration `bk-NNN`, review trước khi merge vì đổi ràng buộc):

- tạo bảng snapshot;
- thêm cột `version_component_id` vào `supplier_bookings`;
- chuyển index duy nhất từ `version_item_id` sang `version_component_id` (mỗi thành phần đã bán chỉ có 1 đặt dịch vụ
  còn sống).

### Thị trường làm thế nào

Tourplan và Lemax đều coi tour trọn gói là một bộ dịch vụ; khi xác nhận bán, hệ thống sinh ra từng dòng dịch vụ để
gửi nhà cung cấp và in voucher. Tên gọi và chi tiết màn hình của từng hãng tôi chưa kiểm trên bản demo.

### Đề xuất cuối (T15)

Giữ đề xuất. Snapshot tạo lúc đại lý xác nhận, lấy từ chính phép tính báo giá. Generate tách mỗi thành phần thành một
đặt dịch vụ, nhóm theo nhà cung cấp. Đổi index duy nhất sang từng thành phần (bk-NNN, review trước). Sửa tour sau đó
không ảnh hưởng chuyến đã bán.

---

## T16. Thuộc tính riêng cho xe, hướng dẫn viên, ăn uống; số xe

### Ghi chú của tech lead

"Cách nhập ra sao; số xe nên là tuỳ chọn, khách muốn nhiều xe thì sao; làm tròn rất rủi ro." Đồng ý: **không làm
tròn âm thầm**. Hệ thống chỉ gợi ý, người quyết định, và mọi chỗ lệch đều có cảnh báo.

### Hôm nay

- Bảng `booking.services` dùng chung cho xe, hướng dẫn viên, vé, ăn uống, hoạt động. Chỉ có `service_type`, `unit`,
  `max_group_size`, `duration_minutes`, `inclusions` (`db-schema-reference.md:2937-2958`). Không có loại xe, số chỗ,
  tuyến, ngôn ngữ, loại bữa.
- Giá xe theo đơn vị `vehicle` hiện luôn tính **× 1 xe**, bất kể bao nhiêu khách (`app/b2b/components.py:118-123`).
  Nếu giá xe không ghi khoảng số khách (`pax_max` trống), đoàn 30 khách vẫn được tính giá 1 xe 16 chỗ. Đây là rủi ro
  tính thiếu chi phí đang có thật, không chỉ là chuyện tương lai.
- Thành phần tour chưa có số lượng.

### Nhân viên nhập thế nào

Nhập trên form dịch vụ của nhà cung cấp (Nhà cung cấp → Dịch vụ → Thêm). Form đổi theo loại dịch vụ:

**Xe (transfer):**

| Trường | Ví dụ | Ghi chú |
|---|---|---|
| Loại xe | Xe 16 chỗ (van) | Danh sách cố định: sedan 4 chỗ, SUV 7 chỗ, van 16 chỗ, minibus 29 chỗ, coach 45 chỗ, thuyền, khác |
| Số khách tối đa mỗi xe | 12 | Số khách thật ngồi thoải mái kèm hành lý, **không phải số ghế đăng ký**. Xe 16 chỗ thường chở 10–12 khách có vali |
| Điểm đi / điểm đến | Hà Nội → Hạ Long | Chọn từ danh sách địa điểm (destination) có sẵn |
| Kiểu dịch vụ | Riêng (private) / Ghép (SIC) | SIC = seat-in-coach, xe ghép nhiều đoàn, giá theo người |
| Thời gian | 150 phút | Đã có cột `duration_minutes` |

**Hướng dẫn viên (guide):** ngôn ngữ (chọn nhiều: Anh, Pháp, Đức...), loại (theo tuyến suốt tour / tại điểm), nửa
ngày hay cả ngày.

**Ăn uống (meal):** loại bữa (sáng, trưa, tối, set menu), tên thực đơn, có món chay không. Nhà hàng chính là nhà cung
cấp nhóm `meal`, không cần bảng nhà hàng riêng lúc này.

Mỗi thuộc tính là một cột riêng có CHECK theo loại dịch vụ (ví dụ chỉ xe mới có số chỗ), không dùng JSON, để lọc và
kiểm được.

### Giá theo xe hay theo người

Bảng giá DMC thường có ba kiểu. Booking nên nhận cả ba, vì đơn vị giá đã có sẵn (`person`, `group`, `vehicle`,
`day`) và khoảng số khách (`pax_min`, `pax_max`) cũng đã có:

| Kiểu | Ví dụ trên bảng giá DMC | Cách nhập trong Booking | Số lượng khi bán |
|---|---|---|---|
| Theo xe | Xe 16 chỗ Hà Nội – Hạ Long: 2.200.000 VND/xe | Đơn vị `vehicle`, gắn dịch vụ xe 16 chỗ | Số xe (xem dưới) |
| Theo người theo bậc số khách | 2–3 khách: 900.000/người; 4–6: 550.000/người; 7–12: 350.000/người | Đơn vị `person`, mỗi bậc một dòng giá với `pax_min`/`pax_max` | Số khách; DMC tự chọn xe |
| Theo người, xe ghép | Shuttle Hà Nội – Hạ Long: 350.000/người | Đơn vị `person`, dịch vụ kiểu SIC | Số khách |

Kiểu thứ hai rất phổ biến ở bảng giá DMC Đông Nam Á (tôi khá chắc, nhưng chưa đối chiếu bảng giá thật của nhà cung
cấp AA): DMC đã tính sẵn loại xe theo số khách, AA không cần đếm xe.

### Số xe: gợi ý, cho sửa, có cảnh báo

1. **Gợi ý**: số xe gợi ý = số khách chia số khách tối đa mỗi xe, làm tròn lên. Ví dụ 18 khách, xe 12 khách/xe →
   gợi ý 2 xe. Chỉ là con số hiện sẵn trong ô, không tự ghi.
2. **Ô số lượng sửa được** ở ba chỗ:
   - Thành phần tour: "số lượng mặc định" (để trống = dùng gợi ý). Ví dụ tour "Private luxury" luôn 1 xe cho mỗi 2 khách.
   - Báo giá của nhân viên bán (đặt thay đại lý): sửa số xe trước khi gửi giá.
   - Snapshot / đặt dịch vụ: điều hành sửa trước khi gửi nhà cung cấp.
3. **Cảnh báo, không làm tròn âm thầm**:
   - Số xe × số khách mỗi xe **nhỏ hơn** số khách → cảnh báo đỏ "Thiếu chỗ: 18 khách, 1 xe 12 chỗ". Không cho gửi nhà
     cung cấp cho tới khi sửa hoặc ghi lý do (ví dụ "2 khách đi riêng xe khác").
   - Số xe **lớn hơn** gợi ý → cảnh báo vàng "Nhiều hơn gợi ý (3 so với 2). Khách yêu cầu?" và bắt ghi lý do. Màn hình
     hiện ngay chi phí tăng: 1 xe × 2.200.000 = +2.200.000 VND.
   - Đổi số xe **sau khi đã báo giá đại lý**: hiện chênh lệch chi phí và hỏi "Tính thêm cho đại lý" (tạo dòng phụ thu)
     hay "AA chịu" (biên lợi nhuận giảm, hiện số mới). Mọi lần đổi ghi audit: ai, lúc nào, từ mấy lên mấy, lý do.
4. **Ví dụ khách muốn nhiều xe**: đoàn 6 khách, 2 gia đình, muốn đi 2 xe riêng. Gợi ý 1 xe 7 chỗ. Nhân viên bán sửa
   thành 2, ghi "2 gia đình đi riêng", giá tăng 2.200.000 VND và được tính vào báo giá. Hôm nay CRM của đại lý chưa có ô
   chọn số xe; tạm thời đại lý ghi yêu cầu, nhân viên bán sửa khi đặt thay. Ô số xe trong CRM làm sau, khi có đại lý
   thật hỏi.

Khi giá xe nhập theo bậc số khách (kiểu thứ hai), không có số xe để gợi ý; số lượng = 1 bậc giá, và khách muốn thêm xe
thì nhân viên bán thêm một dòng xe riêng (`sv:`).

Sửa luôn rủi ro tính thiếu hiện tại: giá đơn vị `vehicle` mà dịch vụ có số khách tối đa mỗi xe thì phép tính báo giá
nhân với số xe gợi ý (hoặc số đã sửa), không còn luôn × 1.

### File Excel nhập thế nào

Hôm nay file Excel chỉ **định giá** cho khách sạn, dịch vụ đã có sẵn (khớp bằng mã `SVC-000123`); dữ liệu dịch vụ phải
nhập ở form (`app/supply/rate_sheet.py:1-25`, ADR 0004a). Một bảng giá DMC có thể có 40 tuyến × 4 loại xe = 160 dịch
vụ, nhập form từng cái thì quá chậm. Đề xuất:

- Thêm sheet **Services** (tuỳ chọn) vào cùng file mẫu. Cột: Service code (trống = tạo mới), Type, Title, Vehicle type,
  Max pax per vehicle, From, To, Private/SIC, Languages, Meal kind, Menu, Unit.
- Xử lý theo thứ tự: sheet Services trước (tạo/sửa dịch vụ, cùng kiểm tra như form), rồi các sheet giá Transport,
  Guide, Meal dùng mã vừa tạo. Chạy thử (dry run) báo lỗi theo từng ô, không ghi gì khi còn lỗi, như hiện nay.
- Sheet giá Transport giữ cột Pax min / Pax max (đã có) để nhập kiểu giá theo bậc số khách.
- Người nhập file là người tạo (maker); dịch vụ mới ở trạng thái nháp cho tới khi người thứ hai công bố hợp đồng.

### Thị trường làm thế nào

Bókun chọn xe theo sức chứa và tách vé theo loại khách. Tourplan cho mỗi sản phẩm của nhà cung cấp có loại và thuộc
tính theo loại, giá theo bậc số khách. Cả hai đều cho nhân viên sửa số lượng trên từng dòng dịch vụ của booking. Chi
tiết cảnh báo thiếu chỗ là thiết kế của tôi, không chắc hãng nào làm đúng như vậy.

### Đề xuất cuối (T16)

Thêm cột theo loại dịch vụ (CHECK, không JSON): xe có loại xe, số khách tối đa mỗi xe, điểm đi/đến, riêng/ghép; hướng
dẫn viên có ngôn ngữ; ăn uống có loại bữa, thực đơn. Số lượng là ô sửa được (thành phần tour, báo giá, đặt dịch vụ)
với giá trị gợi ý; thiếu chỗ thì chặn gửi, nhiều hơn gợi ý thì cảnh báo và bắt ghi lý do, hiện chi phí tăng. Nhận
cả giá theo xe, theo người theo bậc số khách, và xe ghép. File Excel thêm sheet Services xử lý trước sheet giá.

---

## T17. Hồ sơ nhà cung cấp chuyên nghiệp, đầy đủ

### Ghi chú của tech lead

"Tư vấn thêm để quản lý nhà cung cấp chuyên nghiệp, chi tiết và đầy đủ thông tin hơn."

### Hôm nay

Bảng `booking.suppliers` có: mã, tên công ty, nhóm (hotel/transport/...), website, địa chỉ, 1 người liên hệ (tên,
chức danh, email, điện thoại), trạng thái `active`/`inactive` (`db-schema-reference.md:3376-3413`). Hợp đồng có điều
khoản thanh toán và huỷ dạng chữ tự do. Hạn thanh toán hoá đơn nhà cung cấp (`supplier_bills.due_date`) nhập tay. PO
gửi tới email của người liên hệ duy nhất (`app/finance/supplier_orders.py:58`).

### Hồ sơ đầy đủ: 9 phần, chia "cần ngay" và "để sau"

**1. Pháp nhân (cần ngay)**

- Tên pháp lý (đúng trên hoá đơn) và tên giao dịch. Ví dụ "Công ty TNHH Lữ hành Bắc Việt" / "Bac Viet Travel".
- Mã số thuế (MST), nước đăng ký, địa chỉ đăng ký.
- Loại pháp nhân: DMC, nhà xe, công ty du thuyền, hướng dẫn viên tự do, nhà hàng, điểm tham quan. Không có "khách
  sạn" như một nhà cung cấp trực tiếp: theo luật 19/11, AA mua phòng qua DMC, quan hệ với khách sạn do DMC giữ. Cột
  `categories` hiện có (hotel, transport, guide...) vẫn giữ, nghĩa là "nhà cung cấp này bán những loại dịch vụ nào"
  (một DMC bán phòng thì có `hotel`).
- Có xuất được hoá đơn VAT (hoá đơn giá trị gia tăng) không. Ảnh hưởng chi phí thuế của AA.

**2. Người liên hệ theo vai trò (cần ngay)**

Nhiều người, mỗi người một hoặc nhiều vai trò:

| Vai trò | Dùng vào việc gì |
|---|---|
| Đặt chỗ (reservations) | Nhận PO và yêu cầu đặt dịch vụ |
| Kế toán (accounts) | Nhận thông báo thanh toán, gửi hoá đơn |
| Khẩn cấp 24/7 (emergency) | In trên voucher, hướng dẫn viên gọi khi có sự cố |
| Hợp đồng / kinh doanh (contracting) | Đàm phán giá, gửi bảng giá mới |

Mỗi người: tên, email, điện thoại, Zalo/WhatsApp, ngôn ngữ, một người "chính" cho mỗi vai trò.

**3. Tài khoản ngân hàng (cần ngay, bảo vệ chặt)**

- Tên người thụ hưởng, ngân hàng, chi nhánh, số tài khoản, SWIFT (mã ngân hàng quốc tế), loại tiền.
- Số tài khoản mã hoá; màn hình chỉ hiện 4 số cuối; chỉ Kế toán và Quản trị xem đủ.
- Đổi tài khoản: người thứ hai duyệt, **và** phải gọi lại số điện thoại đã lưu từ trước để xác nhận (ghi "đã gọi lại
  lúc ..., người nghe ..."). Lý do: kiểu lừa đảo phổ biến nhất với công ty du lịch là email giả "chúng tôi đổi số tài
  khoản" (BEC = business email compromise, giả mạo email doanh nghiệp).
- Tài khoản mới đổi bị khoá trả tiền 24 giờ (số giờ là tham số chỉnh được trên trang Policy, theo luật "mọi ngưỡng
  chỉnh được trên admin").

**4. Điều khoản thanh toán có cấu trúc trên hợp đồng (cần ngay)**

- Đặt cọc: % và lúc nào (ví dụ 30 % khi nhà cung cấp xác nhận).
- Phần còn lại: "X ngày trước ngày dịch vụ" hoặc "Y ngày sau ngày hoá đơn".
- Hình thức: chuyển khoản / tiền mặt cho hướng dẫn viên; loại tiền.
- Hạn hoá đơn tự tính: hoá đơn ngày 10/03, điều khoản "15 ngày sau hoá đơn" → hạn 25/03. Kế toán vẫn sửa được, có
  ghi lý do.
- Giữ ô chữ tự do cũ làm "ghi chú điều khoản" cho trường hợp đặc biệt.

**5. Vòng đời trạng thái và danh sách đen (cần ngay, phần nhỏ)**

```
Nháp (thiếu hồ sơ) → Chờ duyệt → Đang hợp tác → Tạm ngưng → Ngừng hợp tác
                                     │
                                     └→ Danh sách đen (blacklist)
```

- **Nháp**: đang nhập, chưa đặt dịch vụ được.
- **Chờ duyệt → Đang hợp tác**: người thứ hai kiểm hồ sơ đủ (MST, người liên hệ đặt chỗ, tài khoản ngân hàng, giấy
  phép bắt buộc).
- **Tạm ngưng**: không đặt mới, chuyến đã đặt vẫn chạy. Ví dụ nhà xe đang bị phạt, chờ đăng kiểm.
- **Danh sách đen**: như tạm ngưng nhưng bắt buộc ghi lý do, chỉ Quản trị bật/tắt, mọi tour dùng nhà cung cấp này bị
  đánh dấu "không vận hành được" (nối với B13), và báo cho điều hành các chuyến sắp chạy còn dùng họ.
- Hôm nay chỉ có `active`/`inactive`; bước đầu chỉ cần thêm "Tạm ngưng" và "Danh sách đen" kèm lý do. "Nháp / Chờ
  duyệt" làm sau.

**6. Giấy tờ có hạn (cần ngay cho giấy bắt buộc, phần còn lại sau)**

| Loại nhà cung cấp | Giấy tờ thường cần |
|---|---|
| DMC | Giấy phép kinh doanh, giấy phép lữ hành quốc tế |
| Nhà xe | Giấy phép kinh doanh vận tải, đăng kiểm từng xe, bảo hiểm hành khách |
| Hướng dẫn viên | Thẻ hướng dẫn viên |
| Nhà hàng | Giấy chứng nhận an toàn thực phẩm |
| Mọi loại | Hợp đồng đã ký (file PDF) |

Mỗi giấy: loại, số, ngày cấp, **ngày hết hạn**, file. Nhắc trước 30 ngày (tham số chỉnh được). Giấy bắt buộc hết hạn →
cảnh báo trên màn hình đặt dịch vụ; sau đó có thể chặn đặt mới. File lưu cùng chỗ với tài liệu điều hành hiện có
(`booking.ops_files`). Danh sách giấy cụ thể theo nước là việc business owner xác nhận; bảng trên là ví dụ Việt Nam,
tôi chưa đối chiếu luật từng nước.

**7. Bảo hiểm (để sau)**

Bảo hiểm trách nhiệm (khi khách bị thương do dịch vụ), bảo hiểm hành khách trên xe: số hợp đồng, mức bảo hiểm, hạn.
Lưu như một loại giấy tờ ở phần 6, không cần bảng riêng.

**8. Đánh giá và hiệu suất (để sau, phần tự tính làm sớm được)**

Tự tính từ dữ liệu đặt dịch vụ đã có, không cần nhập tay:

- Tỉ lệ xác nhận: 46/50 yêu cầu được xác nhận = 92 %.
- Thời gian xác nhận trung bình: từ `requested_at` tới `confirmed_at`, ví dụ 5 giờ.
- Số lần từ chối theo lý do (`decline_code`: hết chỗ, không phục vụ được...).
- Hoá đơn lệch so với giá đã đặt.

Phần nhập tay sau mỗi chuyến: điểm 1–5 từ hướng dẫn viên/khách, ghi chú khiếu nại. Làm khi có chuyến thật.

**9. Hạn mức và công nợ (để sau)**

Số tiền AA đang nợ nhà cung cấp, đã quá hạn bao nhiêu. Phần lớn đã có trong hoá đơn và chi trả nhà cung cấp; chỉ thiếu
màn hình tổng hợp theo nhà cung cấp.

### Thứ tự làm

| Đợt | Nội dung | Ước lượng |
|---|---|---|
| 1 | Pháp nhân + MST, người liên hệ theo vai trò (PO gửi người "đặt chỗ"), điều khoản thanh toán có cấu trúc + hạn hoá đơn tự tính, trạng thái Tạm ngưng / Danh sách đen | 2–2,5 ngày công |
| 1 | Tài khoản ngân hàng mã hoá, maker-checker + gọi lại xác nhận, khoá trả tiền 24 giờ | 1–1,5 ngày công |
| 2 | Giấy tờ có hạn + nhắc hạn, hiệu suất tự tính | 1,5–2 ngày công |
| 3 | Nháp/Chờ duyệt hồ sơ, điểm đánh giá tay, công nợ theo nhà cung cấp | khi có nhà cung cấp và chuyến thật |

Một điểm cần biết: mỗi khách sạn hôm nay thuộc đúng một nhà cung cấp (`hotels.supplier_id` bắt buộc). Nếu hai DMC cùng
chào giá một khách sạn thì phải có hai dòng khách sạn. Vì DMC giữ quan hệ khách sạn nên trường hợp này dễ xảy ra; việc
tách "khách sạn gốc" (property master) khỏi "hợp đồng theo DMC" đã được chọn ở T8 (`advisory-r2-hotels.md`, lát L10
trong `advisory-r2-plan.md`), không làm trong T17.

### Thị trường làm thế nào

Tourplan và Lemax đều có hồ sơ nhà cung cấp với nhiều người liên hệ, thông tin thanh toán, hợp đồng và tài liệu đính
kèm; Lemax có quản lý giấy tờ và trạng thái hợp tác. Mức chi tiết cụ thể (ví dụ có khoá trả tiền sau khi đổi tài khoản
hay không) tôi chưa kiểm trên sản phẩm của họ; phần chống lừa đảo đổi tài khoản là thực hành chung của kế toán, không
riêng ngành du lịch.

### Đề xuất cuối (T17)

Hồ sơ 9 phần. Làm ngay: pháp nhân + MST, người liên hệ theo vai trò, tài khoản ngân hàng (mã hoá, chỉ Kế toán/Quản trị
xem, đổi phải hai người + gọi lại xác nhận + khoá trả tiền 24 giờ), điều khoản thanh toán có cấu trúc để hạn hoá đơn
tự tính, trạng thái Tạm ngưng và Danh sách đen có lý do. Làm sau: giấy tờ có hạn và nhắc hạn, bảo hiểm, hiệu suất,
công nợ.

---

## B12. Có tour nào AA mua trọn gói một giá từ một DMC không

### Ghi chú của tech lead

"Giải thích rõ hơn."

### Hai cách mua một tour từ DMC

Cùng tour Hà Nội – Hạ Long 5 ngày, 4 khách, DMC Bắc Việt có thể chào giá theo hai cách:

**Cách 1 – bóc tách (build-up):** DMC gửi bảng giá từng món: khách sạn 1.200.000/phòng/đêm, xe Hà Nội – Hạ Long
2.200.000/xe, hướng dẫn viên 800.000/ngày, vé Văn Miếu 30.000/người... AA tự cộng ra giá tour.

**Cách 2 – trọn gói (package / lump sum):** DMC chỉ nói "tour 5 ngày, 4 khách: 4.500.000 VND/người, đã gồm tất cả".
AA không biết bên trong mỗi món bao nhiêu.

### Vì sao đề xuất chỉ dùng cách 1

| Tình huống | Cách 1 (bóc tách) | Cách 2 (trọn gói) |
|---|---|---|
| Khách bỏ 1 đêm khách sạn | Bớt đúng 1.200.000 × 2 phòng | Phải hỏi lại DMC |
| Có 1 trẻ em 8 tuổi | Tính giá trẻ em từng món | Không biết giảm bao nhiêu |
| Đoàn từ 4 lên 9 khách | Tự đổi xe, tự tính lại | Phải xin giá mới |
| Đổi khách sạn hạng cao hơn | Thay 1 thành phần | Phải xin giá mới |
| Đối chiếu hoá đơn | So từng dòng | Chỉ so tổng |
| Đặt dịch vụ, voucher (T15) | Mỗi món một đặt dịch vụ | Một đặt dịch vụ cho cả tour, không có voucher từng khách sạn |

Booking hôm nay đã chạy theo cách 1: giá tour = tổng các thành phần (`app/b2b/components.py:8`), tour không có thành
phần thì không báo giá được (`components.py:258-259`, lỗi "the trip plan has no bookable components").

### "Mỗi thành phần một nhà cung cấp" không có nghĩa là nhiều công ty

Theo luật của business owner, DMC giữ quan hệ với khách sạn, nhà xe. Nên trong thực tế **9/12 thành phần** của ví dụ
T15 có cùng một nhà cung cấp là DMC Bắc Việt; chỉ du thuyền và nhà hàng là công ty khác. Luật chỉ đòi mỗi thành phần
phải **ghi rõ** nhà cung cấp nào, không đòi phải là các công ty khác nhau.

### Cột `trip_plans.supplier_id` dùng làm gì

Cột này hôm nay chỉ để hiển thị; tính giá, điều hành, tài chính không đọc (`app/catalog/trip_plans.py`). Đề xuất đổi
tên hiển thị thành **"Đầu mối vận hành"** (DMC chính lo tour đó ở nước sở tại) và cho nó hai việc nhỏ có ích:

- Khi thêm thành phần cho tour, danh sách chọn khách sạn/dịch vụ lọc sẵn theo đầu mối này (vẫn chọn được nhà cung cấp
  khác).
- In số khẩn cấp 24/7 của đầu mối (người liên hệ vai trò "khẩn cấp", T17) lên voucher và lịch trình gửi đại lý.

Nó **không** thay nhà cung cấp của từng thành phần, và không dùng để tính giá.

### Nếu một DMC chỉ chào giá trọn gói

Nhân viên Sản phẩm & điều hành xin DMC bảng bóc tách (hầu hết DMC có sẵn, vì chính họ cũng cộng từ từng món). Nếu DMC
nhất quyết không bóc tách, chưa nên đưa tour đó lên bán cho đại lý. Khi gặp trường hợp thật nhiều lần mới xem xét thêm
một loại dịch vụ "trọn gói" (giá theo người theo bậc số khách, một đặt dịch vụ cho cả tour). Hôm nay không làm.

### Thị trường làm thế nào

Tourplan và Lemax đều hỗ trợ cả tour dựng từ từng dịch vụ lẫn sản phẩm "package" một giá; các công ty lữ hành đón
khách quốc tế (inbound) thường dùng cách dựng từ dịch vụ cho tour tự thiết kế và chỉ dùng giá trọn gói cho tour ghép
khởi hành cố định mua lại. Tỉ lệ dùng mỗi cách tôi không có số liệu.

### Đề xuất cuối (B12)

Không mua trọn gói một giá. Mỗi tour phải có đủ thành phần theo ngày, mỗi thành phần ghi một nhà cung cấp AA (thường cùng
là DMC chính). `trip_plans.supplier_id` đổi tên hiển thị "Đầu mối vận hành": lọc sẵn khi chọn thành phần và in số khẩn
cấp lên voucher, không dùng để tính giá. DMC chỉ chào trọn gói thì xin bảng bóc tách; chưa có thì chưa bán cho đại lý.

---

## B13. Tour chưa đủ nhà cung cấp cho mọi thành phần

### Ghi chú của tech lead

"Tư vấn thêm": kiểm thế nào, và nút cho bán ngoại lệ của Quản trị trông ra sao.

### Hôm nay kiểm gì

- Báo giá đại lý từ chối nếu tour không có thành phần nào, hoặc một thành phần không có giá đúng ngày
  (`components.py:258-259`, `:272-274`).
- Trang Pricing → Price readiness cho mỗi tour một trạng thái: `priced`, `hand_priced`, `no_components`,
  `inactive_component`, `no_rule`, `missing_rates`, `missing_fx` (`app/catalog/price_readiness.py:11-24`).
- **Không ai kiểm cấu trúc**: tour 5 ngày chỉ có khách sạn 2 đêm vẫn báo giá và bán được, vì 2 thành phần đó đều có
  giá. Hai đêm còn lại khách không có chỗ ngủ, và AA chỉ phát hiện khi điều hành đặt dịch vụ.

### Kiểm tra "đủ để vận hành" chạy thế nào

Mỗi tour được kiểm theo các luật dưới. Luật **chặn** làm tour không bán được cho đại lý; luật **cảnh báo** chỉ hiện để
nhân viên xem.

| Mã | Luật | Mức | Ví dụ lỗi |
|---|---|---|---|
| N1 | Mỗi đêm (số ngày − 1 đêm) có ít nhất một khách sạn/du thuyền | Chặn | Tour 5 ngày = 4 đêm; thiếu đêm 2 và 4 |
| N2 | Mỗi thành phần có giá đã công bố, còn hiệu lực trên các ngày đang bán (365 ngày tới, hoặc từng ngày khởi hành cố định) | Chặn | "Xe ngày 2: hết giá từ 01/04/2027" |
| N3 | Nhà cung cấp của mọi thành phần đang hợp tác (không tạm ngưng, không danh sách đen) | Chặn | "Nhà hàng Phố Cổ: tạm ngưng" |
| N4 | Ngày đổi điểm (hôm trước ngủ Hà Nội, hôm sau ngủ Hạ Long) có xe | Cảnh báo | "Ngày 2 đổi điểm nhưng không có xe" |
| N5 | Tour ghi "có hướng dẫn viên" mà có ngày không có hướng dẫn viên | Cảnh báo | "Ngày 3 thiếu hướng dẫn viên" |
| N6 | Giấy tờ bắt buộc của nhà cung cấp hết hạn (khi có T17 phần 6) | Cảnh báo, sau này chặn | "Nhà xe X: đăng kiểm hết hạn 01/02" |

Ngày nào cần xe, cần hướng dẫn viên thì không suy chắc chắn được (ngày tự do ở Hà Nội không cần xe), nên N4, N5 chỉ
cảnh báo.

**Ngoại lệ có chủ đích cho đêm không cần khách sạn**: ví dụ tour Sapa có đêm 3 ngủ trên tàu đêm Hà Nội – Lào Cai. Nhân
viên Sản phẩm & điều hành đánh dấu "đêm 3: không cần khách sạn (tàu đêm)" trên tour. Đây là dữ liệu của tour, không
phải ngoại lệ của Quản trị.

### Kết quả hiện ở đâu

- Trang Price readiness thêm cột **"Vận hành được"**: Đủ / Có cảnh báo / Chưa đủ, kèm danh sách lý do. Ví dụ:
  "Chưa đủ: thiếu khách sạn đêm 2, 4; xe ngày 2 hết giá từ 01/04/2027".
- Danh sách sản phẩm gửi CRM: tour "Chưa đủ" không có trong danh sách bán (như tour không `sellable`).
- Báo giá đại lý gửi tour "Chưa đủ": từ chối với lý do `not_operable` và tên luật vi phạm.
- Nhân viên bán đặt thay đại lý: thấy cùng lý do, không có nút đặt.
- Bán lẻ (B2C) và khởi hành cố định: lúc này chỉ cảnh báo, không chặn (luật quyết định chỉ nói B2B).

### Nút "Cho bán ngoại lệ" của Quản trị

Trên ngăn kéo thông tin thương mại của tour (chỉ Quản trị thấy), khi tour "Chưa đủ":

```
Tour HN-HL-5D · Chưa đủ để vận hành
  ✗ N1 Thiếu khách sạn đêm 4
  ✓ N2 Giá còn hiệu lực

[Cho bán ngoại lệ]
  Bỏ qua luật:     [x] N1  (chỉ các luật đang lỗi)
  Lý do (≥ 20 ký tự): "Đêm 4 DMC Bắc Việt giữ phòng tay, hợp đồng ký tuần sau"
  Hết hạn:         05/12/2026   (mặc định 14 ngày, tối đa 30)
                                                  [Huỷ]  [Xác nhận]
```

Quy tắc:

- Chỉ bỏ qua đúng những luật đang lỗi, không bỏ qua "tất cả".
- Bắt buộc lý do và ngày hết hạn. Số ngày mặc định và tối đa là tham số chỉnh được trên trang Pricing → Policy (luật
  "mọi ngưỡng chỉnh được"), không viết cứng.
- Hết hạn thì tour tự quay về "Chưa đủ". Nếu trong thời gian ngoại lệ xuất hiện lỗi **mới** (ví dụ thêm một thành phần
  hết giá) thì ngoại lệ không che lỗi mới đó.
- Ghi audit (ai, lúc nào, luật nào, lý do). Trang Price readiness hiện huy hiệu "Ngoại lệ tới 05/12".
- Chuyến bán trong thời gian ngoại lệ được gắn cờ "bán ngoại lệ"; Generate (T15) tạo thêm một việc cho điều hành:
  "Đêm 4 chưa có khách sạn trong hệ thống: đặt tay và nhập vào chuyến".
- Lưu ở một bảng nhỏ mới (ví dụ `booking.trip_plan_operable_overrides`: tour, các luật bỏ qua, lý do, hết hạn, người
  tạo, người thu hồi). Một migration `bk-NNN`, có thể gộp chung với migration của T15.

### Thị trường làm thế nào

Hệ thống bán tour B2B thường không cho đặt một sản phẩm thiếu giá hay thiếu tồn kho; với tour tự dựng, Tourplan và
Lemax dựa vào việc nhân viên dựng đủ dịch vụ, và tôi không chắc họ có luật tự kiểm "mỗi đêm một khách sạn" như trên.
Luật N1–N6 là thiết kế cho AA, dựa trên lỗi thật có thể xảy ra hôm nay.

### Đề xuất cuối (B13)

Thêm kiểm tra "Vận hành được" cho mỗi tour: chặn bán cho đại lý khi thiếu khách sạn một đêm (trừ đêm đánh dấu không
cần khách sạn), thiếu giá còn hạn, hoặc nhà cung cấp tạm ngưng / danh sách đen; cảnh báo khi ngày đổi điểm không có xe
hay thiếu hướng dẫn viên. Quản trị cho bán ngoại lệ: chọn đúng luật bỏ qua, lý do từ 20 ký tự, hết hạn mặc định 14
ngày tối đa 30 (tham số chỉnh được), có audit, chuyến bán trong ngoại lệ có việc cho điều hành.

---

## Tóm tắt thứ tự làm (cập nhật lộ trình bản trước)

Bảng dưới chỉ để so độ lớn. Lịch thật theo phiên nằm ở `advisory-r2-plan.md`: T13 + T17 thuộc lát L7, T15 + T16 + B12
+ B13 thuộc lát L6.

| Đợt | Việc | Ngày công (ước lượng) |
|---|---|---|
| 1 | T15 snapshot + tách tour + đổi index (bk-NNN, review trước merge) | 2–2,5 |
| 1 | B13 kiểm "Vận hành được" + ngoại lệ (gộp migration với T15) | 1,5 |
| 1 | T13 ma trận 4 vai trò (chỉ code + nhãn, không migration) | 0,5 |
| 2 | T16 thuộc tính dịch vụ + số lượng gợi ý/sửa được + sửa tính giá xe + sheet Services | 3–3,5 |
| 2 | B12 đổi tên "Đầu mối vận hành" + lọc khi chọn thành phần | 0,5 |
| 3 | T17 đợt 1 (pháp nhân, liên hệ, ngân hàng, điều khoản, trạng thái) | 3–4 |
| 4 | T17 đợt 2 (giấy tờ có hạn, hiệu suất) | 1,5–2 |

**Chưa kiểm:** số nhà cung cấp, dịch vụ xe và tour có thành phần thật trên Dev; có ai đang giữ vai trò
`content_creator` trong Booking; bảng giá thật của DMC AA đang dùng kiểu giá xe nào (theo xe hay theo bậc số khách).
