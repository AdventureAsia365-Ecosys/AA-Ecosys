# Tư vấn vòng 2: khách sạn khi nhà cung cấp (DMC) giữ quan hệ với khách sạn — T10, T11, T8, T12, B7, B8

Phiên S285, 19/11/2026. Chỉ đọc code, không sửa gì. Xây tiếp trên `advisory-hotels.md` và
`advisory-content-activities-hotels-critic.md` cùng thư mục.

Từ viết tắt dùng trong bài (giải thích một lần ở đây, các mục dưới dùng lại):

- **DMC** = destination management company, công ty lữ hành tại điểm đến. Ở đây là nhà cung cấp của AA: họ lo trọn
  xe, vé, khách sạn, hướng dẫn viên, bữa ăn, hoạt động ở một nước.
- **Contracting** = nhóm nhập hợp đồng và giá trong AA-Booking (vai trò `contracting` trong Booking).
- **Facts** = sự thật về khách sạn: tên, địa chỉ, toạ độ, số sao, giờ nhận/trả phòng, tiện ích, loại phòng.
- **Meal plan** = gói bữa ăn kèm phòng: RO (room only, chỉ phòng), BB (bed & breakfast, phòng kèm bữa sáng),
  HB (half board, kèm 2 bữa), FB (full board, kèm 3 bữa), AI (all inclusive, trọn gói ăn uống).
- **Maker-checker** = người nhập và người duyệt phải là hai người khác nhau (Booking đã có cho hợp đồng).
- **Dry run** = chạy thử: kiểm tra file, báo lỗi, không ghi gì vào DB.
- **Stop-sale** = ngừng bán một khách sạn/loại phòng trong một khoảng ngày.
- **Trigger** = đoạn lệnh trong DB tự chạy mỗi khi một dòng được thêm/sửa, dùng để chặn dữ liệu sai.
- **Property master** = danh bạ khách sạn gốc: mỗi khách sạn thật một dòng, nhiều hợp đồng của nhiều DMC gắn vào.

---

## 0) Sự thật mới làm thay đổi điều gì

Business owner chốt (19/11): AA **không** có hợp đồng trực tiếp với khách sạn. Chuỗi thật là:

```
Khách sạn ──(hợp đồng DMC–khách sạn: AA không thấy)──▶ DMC (nhà cung cấp của AA)
DMC ──(hợp đồng AA–DMC: booking.supplier_contracts)──▶ AA ──(giá bán B2B)──▶ đại lý
```

Hệ quả cho hệ thống (kiểm trong code hôm nay):

1. **Mọi giá khách sạn trong Booking là giá DMC báo cho AA**, không phải giá khách sạn. Bảng `booking.supplier_rates`
   đã đúng như vậy: mỗi dòng giá nằm dưới một `supplier_contracts` của một `suppliers` (`db-schema-reference.md:3208-3375`).
2. **Sự thật về khách sạn mà AA có = điều DMC nói + website khách sạn.** AA không tự kiểm được. Vì vậy cần ghi
   *nguồn* và *ngày xác nhận lần cuối* cho từng khách sạn (hôm nay chưa có cột này: `booking.hotels`,
   `db-schema-reference.md:2065-2088`).
3. **Đặt phòng đi tới DMC, không tới khách sạn.** Đúng với code: `supplier_bookings` lấy nhà cung cấp là
   `coalesce(h.supplier_id, sv.supplier_id)` (`apps/AA-Booking/backend/app/ops/supplier_bookings.py:122`), tức DMC đang
   gắn với khách sạn. `confirmation_ref` là mã xác nhận của DMC.
4. **Điều khoản huỷ, thanh toán là của DMC với AA** (DMC thường lấy điều khoản của khách sạn rồi cộng thêm vài ngày
   đệm). Hôm nay là chữ tự do trên `supplier_contracts.cancellation_policy`.
5. **Allotment (số phòng giữ sẵn) nếu có là cam kết của DMC dành cho AA**, cắt ra từ phần DMC giữ với khách sạn.
   AA không bao giờ thấy tồn phòng thật của khách sạn.
6. **Quyền dùng ảnh** đi qua DMC hoặc bộ ảnh báo chí của khách sạn, không qua hợp đồng của AA. Booking đã có cờ
   `entity_media.usage_rights` (mặc định false), CIS chỉ công bố ảnh có cờ này (ADR 0004a quyết định 2).

Phần dưới trả lời từng mục theo đúng sự thật này.

---

## T10 — Mã khách sạn chuẩn ngành (GIATA) → làm tốt hơn với hệ thống hiện tại

**Câu hỏi của tech lead:** hệ thống đang nhập khách sạn bằng tay từ bảng của nhà cung cấp AA, AA chưa nối hệ thống
khách sạn nào. Vậy làm sao cho tốt hơn với cái đang có?

**GIATA** là một công ty bán "mã khách sạn chung": mỗi khách sạn thật trên thế giới có một mã, các hệ thống khác nhau
dùng mã đó để biết hai dòng là cùng một khách sạn. Phải trả phí. Với AA hôm nay (vài DMC, vài trăm khách sạn, nhập tay)
thì chưa đáng tiền: lợi ích của GIATA chỉ lớn khi nối nhiều nguồn tự động.

### Hiện trạng (code)

- Khách sạn tạo từng cái trong drawer Booking. Khoá trùng là `(supplier_id, lower(name), destination_id)`
  (`db-schema-reference.md:2096`): cùng DMC, cùng tên, cùng nơi thì báo trùng; khác một dấu cách hay chữ "Hotel" là lọt.
- Import bảng giá (`apps/AA-Booking/backend/app/supply/rate_sheet.py:63-74`) có 10 cột, đã có dry run, báo lỗi theo
  sheet/dòng/cột, không ghi gì khi còn lỗi, tạo hợp đồng nháp rồi người thứ hai duyệt. Đây là nền tốt.
- Nhưng import **chỉ định giá cho khách sạn đã có**; không nhập được facts hay loại phòng
  (`apps/AA-Booking/CONTEXT.md:2206`). Khớp theo `Hotel code` + tên loại phòng.
- Mùa (`season`) là chữ tự do tới 80 ký tự; không có bảng mùa theo hợp đồng.
- Hợp đồng có `valid_to` nhưng chưa thấy job nào nhắc sắp hết hạn hay nhắc xác nhận lại (tìm trong CONTEXT.md không có).
- DB chưa có extension so khớp chữ gần đúng (`pg_trgm`); chỉ có `pg_stat_statements`, `plpgsql`, `vector`
  (`db-schema-reference.md:15799-15804`).

### Thị trường làm thế nào

- Hệ thống tour operator/DMC như **Tourplan**, **Lemax** có "danh bạ sản phẩm" nội bộ: mỗi khách sạn một dòng, nhiều
  nhà cung cấp/hợp đồng gắn vào (chắc chắn ở mức khái niệm; chi tiết màn hình từng hệ thống tôi không chắc).
- Bên bán buôn lớn (**Hotelbeds**, **WebBeds**) mua mã GIATA hoặc tự làm "mapping" để gộp cùng một khách sạn từ nhiều
  nguồn. Đó là quy mô hàng trăm nghìn khách sạn, không phải quy mô AA.
- DMC và tour operator nhỏ ở châu Á phần lớn vẫn làm bằng Excel: mỗi năm nhận bảng giá ("tariff") của đối tác, nhập
  vào hệ thống bằng file mẫu. Điểm khác biệt giữa làm tốt và làm ẩu là có **kiểm tra** và **nhắc định kỳ** hay không.

### Cách làm tốt hơn, không tốn phí (5 phần)

**1. Danh bạ khách sạn nội bộ + chống trùng (property master).**
Mỗi khách sạn thật là một dòng `booking.hotels`, dùng chung cho mọi DMC (chi tiết ở T8). Khi tạo tay hoặc import,
hệ thống tìm ứng viên trùng bằng ba tín hiệu:

- Tên chuẩn hoá: chữ thường, bỏ dấu, bỏ các từ chung ("hotel", "resort", "& spa", "boutique"), bỏ dấu câu.
- Cùng `destination_id` (nơi CIS) hoặc cùng thành phố.
- Khoảng cách theo toạ độ (công thức haversine trong SQL, không cần PostGIS).

Quy tắc ví dụ:

| Tình huống | Kết quả |
|---|---|
| Tên giống ≥ 85 % **và** cách nhau < 300 m | Chặn, gợi ý "dùng khách sạn có sẵn HTL-000123" |
| Tên giống 60–85 % **hoặc** cùng nơi và cách < 1 km | Cảnh báo, người nhập bấm "khác khách sạn" kèm lý do |
| Còn lại | Tạo mới |

Ví dụ: "La Siesta Classic Ma May" và "La Siesta Classic Hotel – Ma May", cùng Hoàn Kiếm, cách 20 m → chuẩn hoá đều thành
"la siesta classic ma may" → chặn. So khớp chữ làm trong Python trước (thư viện chuẩn `difflib`); khi danh bạ lớn mới
bật `pg_trgm` (extension miễn phí của PostgreSQL, cần một migration của Booking). Thêm một màn "Gộp khách sạn trùng"
cho dữ liệu cũ.

Giữ cột `external_codes jsonb` (mã của DMC cho khách sạn đó, mã GIATA để trống) để sau này nối nếu cần.

**2. Mẫu nhập (template) cho facts và loại phòng.**
Thêm hai sheet vào file mẫu: `Hotels` (Hotel code — trống nghĩa là tạo mới, Tên, Nơi, Địa chỉ, Vĩ độ, Kinh độ, Sao,
Giờ nhận, Giờ trả, Tiện ích, Nguồn, Ngày xác nhận) và `Room types` (Khách sạn, Tên loại phòng, Số người chuẩn, Tối đa
người lớn, Tối đa trẻ em, Giường phụ, Kiểu giường). Đi qua cùng dry run: báo lỗi, báo ứng viên trùng, rồi mới ghi.
Có nút Export để xuất ra đúng mẫu, sửa, nhập lại (round trip).

**3. Importer bảng giá DMC có kiểm tra chặt hơn.** Giữ khung hiện có (dry run, lỗi theo ô, nháp, maker-checker), thêm:

- Cột mới: Single supplement (phụ thu phòng đơn), Extra bed adult/child (giường phụ), Min stay (ở tối thiểu bao nhiêu
  đêm), và hai cột tuỳ chọn "Giá công bố" + "% hoa hồng" (xem B7).
- Khớp khách sạn theo **mã của DMC** (`supplier_hotel_code`) trước, rồi mới tới tên; tên loại phòng của DMC lưu thành
  "tên gọi khác" (alias) của loại phòng AA để lần sau tự khớp.
- Kiểm tra nghiệp vụ, mỗi lỗi một dòng dễ đọc:

| Kiểm tra | Ví dụ bị bắt |
|---|---|
| Mùa hở hoặc chồng nhau | Low 01/05–30/09, High 01/10–31/03 → hở 01/04–30/04 |
| Meal plan ngược | Deluxe BB 60 USD nhưng HB 55 USD (HB phải ≥ BB) |
| Phòng đơn rẻ bất thường | Single 30 USD trong khi Double 60 USD và không có phụ thu |
| Nhảy giá so với năm trước | 2026 là 50 USD, 2027 là 80 USD (+60 %) → cảnh báo, không chặn |
| Tiền tệ khác hợp đồng | Hợp đồng USD, dòng ghi VND |
| Loại phòng lạ | "Premier Lake View" chưa có → gợi ý 3 loại gần nhất hoặc tạo mới |

- Màn diff trước khi duyệt: dòng nào thêm, đổi, mất so với hợp đồng năm trước.
- Bảng của DMC thường có bố cục riêng. Bản 1: contracting chép sang mẫu của AA. Bản 2: lưu "bản đồ cột" riêng cho từng
  DMC (cột C của DMC A = Net) để lần sau nhập thẳng file gốc. Không cần LLM.

**4. Bảng mùa và giá theo từng đêm.** Thay chữ tự do `season` bằng bảng mùa gắn với hợp đồng (tên mùa + các khoảng
ngày). Dòng giá trỏ tới mùa. Giá tính **từng đêm**, nên một kỳ ở vắt qua hai mùa vẫn đúng. Ví dụ: ở 3 đêm 29/09–02/10,
Low (tới 30/09) 45 USD, High (từ 01/10) 60 USD → 45 + 45 + 60 = 150 USD, không phải 3 × 45 = 135 như khi lấy giá
ngày đầu. Hôm nay báo giá B2B cho đại lý **đã** tính từng đêm (`b2b/components.py:227-235`, mỗi đêm một lần tra giá).
Chỗ còn lấy giá ngày đầu nhân số đêm là giá mặc định khi nhân viên thêm phòng vào phiên bản chuyến
(`trip_cases/versions.py:285-293`: `rate_in_force` ngày bắt đầu, rồi `default_cost` × số đêm); phần này cần sửa theo.

**5. Nhắc xác nhận lại định kỳ.** Thêm cột `facts_confirmed_at`, `facts_confirmed_by`, `facts_source`
(`dmc_sheet` / `hotel_website` / `site_visit`) cho khách sạn. Một job hằng ngày trong bảng job của Booking
(`booking.job`) gom ba danh sách lên trang chủ Booking và gửi e-mail cho contracting (Booking đã gửi e-mail nội bộ qua
SES cho inquiry mới):

- Hợp đồng DMC hết hạn trong 60 / 30 / 7 ngày mà chưa có hợp đồng kế tiếp.
- Khách sạn chưa xác nhận lại quá 180 ngày (ngưỡng sửa được trên trang admin, đúng luật "ngưỡng không hard-code").
- Khách sạn còn trong tour bán được nhưng không có giá cho ngày khởi hành sắp tới.

Kèm nút "Copy hợp đồng sang năm sau" (tạo nháp năm mới từ năm cũ, contracting chỉ sửa số).

**Công sức ước tính:** phần 1 khoảng 3 ngày (gộp với T8), phần 2 khoảng 2 ngày, phần 3 khoảng 3 ngày, phần 4 khoảng
2–3 ngày, phần 5 khoảng 1–2 ngày. Tổng khoảng 11–13 ngày công (engineer-day), 0 USD (không dịch vụ AWS mới; SES, dịch vụ
gửi e-mail của AWS, đã có). Con số này chỉ để so độ lớn; lịch thật theo phiên là lát L10 trong `advisory-r2-plan.md`.
Job nhắc hợp đồng hết hạn làm một lần cho mọi hợp đồng nhà cung cấp (lát L8); phần 5 ở đây chỉ thêm nhắc xác nhận lại
khách sạn.

### Đề xuất cuối (T10)

Không mua GIATA. Giữ cột `external_codes` (mã DMC, chỗ trống cho GIATA). Làm cho việc nhập tay an toàn hơn theo thứ
tự: (1) danh bạ khách sạn + chống trùng theo tên chuẩn hoá, nơi, toạ độ; (2) mẫu Excel cho facts và loại phòng;
(3) mở rộng importer bảng giá DMC với kiểm tra nghiệp vụ, khớp theo mã DMC, diff trước duyệt; (4) bảng mùa và giá
từng đêm; (5) job nhắc hết hạn hợp đồng và xác nhận lại khách sạn, ngưỡng sửa được trong admin.

---

## T11 — Ai nhập phần nào, có sợ lệch không, và DMC giữ khách sạn thì đổi gì

**Câu hỏi của tech lead:** chưa hiểu; như vậy có thể sai lệch, thiếu đồng bộ; và khách sạn hiện do nhà cung cấp quản
lý chứ không phải AA.

### Giải thích bằng lời thường

Một khách sạn có ba loại thông tin, mỗi loại có **đúng một nơi được sửa**:

| Thông tin | Ai nhập | Nhập ở đâu (bảng) | Ai đọc, bằng cách nào |
|---|---|---|---|
| Facts: tên, địa chỉ, toạ độ, sao, giờ nhận/trả, tiện ích, loại phòng | Contracting, theo bảng DMC + website khách sạn | Booking `booking.hotels`, `booking.hotel_room_types` | CIS đọc qua view `booking.v_supply_hotels` (chỉ facts, không giá) |
| Giá và điều khoản: giá net, mùa, meal plan, phụ thu, trẻ em, huỷ, allotment | Contracting, theo hợp đồng AA–DMC | Booking `supplier_contracts`, `supplier_rates` | Chỉ Booking. CIS, TripPlanner, khách **không bao giờ** thấy |
| Lời văn cho khách: mô tả, điểm nổi bật, lưu ý, bộ ảnh công bố | Nhân viên content (AI viết nháp, người duyệt) | CIS `shared.supply_content_version` | Booking đọc qua view `catalog.v_supply_content` (chỉ bản đã duyệt) |
| Ảnh gốc từ DMC/khách sạn | Contracting tải lên, đánh dấu được phép dùng | Booking `entity_media` (`usage_rights`) | CIS chép ảnh có cờ cho phép, làm bản WebP |

Nguồn: ADR 0004a (`docs/adr/0004a-supply-content-ownership.md`), Booking `CONTEXT.md:1825-1845`, CIS
`CONTEXT.md:2384-2410`.

### Đồng bộ chạy thế nào (đã có trong code, không phải đề xuất)

**Một mã khách sạn duy nhất:** id của dòng `booking.hotels` (uuid). CIS lưu nó ở `shared.supply_entity.source_id`
(khoá duy nhất `(source_system, source_id)`, `db-schema-reference.md:13708-13727`). Không có mã thứ hai.

Ví dụ một lần thay đổi: DMC báo khách sạn X thêm loại phòng "Deluxe Lake View".

1. Contracting thêm loại phòng trong Booking. Trigger tăng `supply_version` của khách sạn từ 7 lên 8 và ghi một dòng
   outbox ("hộp thư đi" trong DB, cùng giao dịch với thay đổi, nên không bao giờ mất).
2. CIS kéo outbox mỗi nhịp của sampler, đọc facts **hiện tại** từ view, chỉ áp nếu version 8 mới hơn version CIS đang
   giữ (7). Bản tin cũ tới muộn bị bỏ qua.
3. Lời văn đã công bố chuyển thành `stale` (cũ): **không còn hiển thị** cho tới khi có bản mới được duyệt, nên khách
   không đọc lời văn sai.
4. Job CIS viết nháp mới từ facts version 8; người duyệt xem, sửa, công bố.
5. Booking đọc lại bản đã công bố qua `catalog.v_supply_content` để đưa vào báo giá.

**Một điểm cần nói thật:** CIS có giữ một **bản chụp chỉ-đọc** của facts trong `shared.supply_entity.facts` (kèm
`applied_supply_version`), để AI viết dựa vào. Đây không phải bản thứ hai để sửa: CIS không có màn sửa facts, màn CIS
hiện facts chỉ-đọc với nút "Edit in Booking", và mỗi version mới từ Booking ghi đè bản chụp. Luật "CIS đọc, không sửa"
vẫn đúng.

### Chỗ nào vẫn có thể lệch, và cách chặn

| Rủi ro lệch | Ví dụ | Cách chặn |
|---|---|---|
| Thế giới thật đổi mà DMC không báo | Khách sạn đóng cửa sửa chữa 3 tháng, đổi tên | Cột "xác nhận lần cuối" + job nhắc 180 ngày (T10 phần 5); hợp đồng năm mới bắt xác nhận lại |
| Cùng một khách sạn nhập hai lần | DMC A và DMC B đều bán "La Siesta", thành hai dòng, hai mô tả | Danh bạ khách sạn + chống trùng (T8, T10) |
| Khoảng trống sau khi đổi | Facts đổi, lời văn `stale`, báo giá thiếu mô tả vài ngày | Thẻ "đang chờ duyệt lại" trên trang CIS `/admin/supply-content/status`; cảnh báo khi quá N ngày |
| Lời văn tour (CIS) nêu tên khách sạn cụ thể | Lịch trình viết "nghỉ tại khách sạn ABC" nhưng tour trong Booking đã đổi sang khách sạn DEF | Lời văn tour nên ghi hạng + nơi ("khách sạn 4 sao ở phố cổ Hội An hoặc tương đương"); tên cụ thể lấy từ thành phần tour trong Booking |
| Ảnh không có quyền | Ảnh lấy từ website khách sạn, DMC không có quyền chia sẻ | Chỉ bật `usage_rights` khi DMC xác nhận bằng văn bản hoặc ảnh từ bộ ảnh báo chí của khách sạn |

### DMC giữ khách sạn thì đổi gì

- **Facts trong Booking là "điều DMC nói với AA"**, không phải sự thật AA tự kiểm. Mỗi khách sạn cần ghi nguồn
  (`dmc_sheet`, `hotel_website`, `site_visit`) và ngày xác nhận. Trên màn hiện chữ nhỏ: "Theo DMC X, xác nhận
  12/11/2026".
- **Contracting không đàm phán với khách sạn**, chỉ ghi lại offer của DMC. Hợp đồng AA ký là với DMC; khách sạn là một
  thành phần DMC cung cấp.
- **Đặt phòng gửi cho DMC**; DMC hỏi khách sạn rồi trả về hai mã: mã của DMC (`supplier_bookings.confirmation_ref` đã
  có) và mã xác nhận của khách sạn (nên thêm một cột tuỳ chọn `hotel_confirmation_ref` để in lên voucher, vì khách
  check-in bằng mã của khách sạn).
- **Voucher** ghi tên khách sạn và dòng "đặt qua DMC X".
- **Nếu một khách sạn được nhiều DMC cung cấp** (T8), facts vẫn một dòng; giá và điều khoản là của từng DMC.

### Đề xuất cuối (T11)

Giữ phân công, nói rõ hơn: contracting nhập facts và giá ở Booking **theo bảng của DMC**, ghi nguồn và ngày xác nhận;
nhân viên content viết mô tả và chọn ảnh ở CIS; một mã khách sạn chung (id Booking); CIS chỉ đọc facts qua view/outbox,
giữ bản chụp chỉ-đọc, không bao giờ sửa; facts sai thì sửa ở Booking. Thêm: cột nguồn + ngày xác nhận, job nhắc xác
nhận lại, cột mã xác nhận của khách sạn trên đặt phòng, và luật lời văn tour không ghi cứng tên khách sạn.

---

## T8 — Một khách sạn mua qua nhiều nhà cung cấp → vẫn đúng, còn quan trọng hơn

### Kiểm lại với sự thật mới

Khi AA không có hợp đồng với khách sạn, **cùng một khách sạn rất dễ đến từ hai DMC**. Ví dụ ở Hà Nội: DMC A báo
"La Siesta Classic, Deluxe, BB" 55 USD/đêm; DMC B báo cùng phòng 52 USD/đêm. Hôm nay khoá trùng có `supplier_id`
(`db-schema-reference.md:2096`) và UI khoá ô nhà cung cấp sau khi tạo, nên phải tạo **hai dòng khách sạn**. Hệ quả:

- CIS viết **hai** mô tả, chép **hai** bộ ảnh cho cùng một khách sạn (tốn tiền LLM, khách thấy trùng).
- Gợi ý thành phần tour (`component_suggest.py`) thấy hai ứng viên giống hệt nhau.
- Đổi DMC cho một tour nghĩa là đổi khách sạn, mất liên kết lời văn đã duyệt.

### Thị trường

Gộp "cùng một khách sạn từ nhiều nguồn" chính là việc GIATA và bộ phận mapping của Hotelbeds/WebBeds làm (chắc chắn).
Tourplan/Lemax cho một sản phẩm có nhiều nhà cung cấp (chắc ở mức khái niệm, không chắc tên màn hình).

### Những chỗ code phải đổi theo (bổ sung vào đề xuất gốc)

- Bảng nối `hotel_supplier_links` (khách sạn, DMC, mã của DMC cho khách sạn, ưu tiên). `hotels.supplier_id` thành
  nullable rồi bỏ ở bước contract; khoá trùng mới `(tên chuẩn hoá, destination_id)`.
- Trigger `supplier_rate_guard` hôm nay đòi khách sạn **cùng nhà cung cấp** với hợp đồng; phải đổi thành "khách sạn có
  liên kết với DMC của hợp đồng".
- Đặt phòng (`supplier_bookings.py:122`) lấy nhà cung cấp từ `hotels.supplier_id`; phải đổi thành **nhà cung cấp của
  hợp đồng chứa dòng giá đã dùng** (giá của DMC nào thì đặt với DMC đó).
- Chọn giá: khi hai DMC cùng có giá, ưu tiên DMC đánh dấu "ưu tiên", rồi tới giá thấp hơn **cùng meal plan**.
- Tên loại phòng mỗi DMC gọi khác ("Deluxe" và "Deluxe City View"): lưu alias như T10 phần 3.

### Đề xuất cuối (T8)

Giữ nguyên: có, thêm property master (một khách sạn, nhiều hợp đồng của nhiều DMC). Làm cùng bước chống trùng của T10.
Các chỗ phải đổi theo: guard giá, nhà cung cấp của đặt phòng lấy từ hợp đồng, alias loại phòng.

---

## T12 — Gộp mô hình chung cho khách sạn và hoạt động → vẫn đúng

### Kiểm lại với sự thật mới

- **Điều khoản huỷ theo bậc trên hợp đồng:** vẫn đúng, chỉ cần hiểu là điều khoản **DMC áp cho AA**. Ví dụ hợp đồng
  AA–DMC A: huỷ trước 30 ngày mất 0 %, 15–29 ngày mất 50 %, dưới 15 ngày mất 100 %. Khách sạn có thể cho DMC 21 ngày,
  DMC cộng đệm thành 30 ngày; AA chỉ cần biết con số DMC đưa. Offer (giá riêng cho một dịp) được ghi đè.
- **Giá trẻ em:** dịch vụ tính theo người dùng `pax_type` (người lớn/trẻ em/em bé); phòng dùng chính sách trẻ em và
  giường phụ. Với khách sạn, chính sách này là **DMC chuyển lại** từ khách sạn, nên lưu theo (hợp đồng, khách sạn):
  hai DMC có thể báo giá trẻ em khác nhau cho cùng một khách sạn. Ví dụ: trẻ 0–5 ở chung miễn phí, 6–11 giường phụ
  20 USD/đêm kèm bữa sáng.
- **Bảng restriction/allotment chung theo thành phần** (`rt:` = loại phòng, `sv:` = dịch vụ): vẫn đúng. Stop-sale
  của khách sạn đến từ thông báo của DMC; nên ghi thêm "nguồn: e-mail DMC ngày …".

Không có phần nào trong T12 giả định AA ký trực tiếp với khách sạn, nên không cần đổi.

### Đề xuất cuối (T12)

Giữ nguyên đề xuất. Ghi rõ trong thiết kế: điều khoản huỷ và chính sách trẻ em là của DMC với AA, lưu theo hợp đồng
(và khách sạn); stop-sale ghi nguồn thông báo của DMC.

---

## B7 — Giá net hay giá có hoa hồng → sửa lại: hợp đồng là AA với DMC

### Trả lời câu "hợp đồng giữa ai với ai"

Bản trước ghi "hợp đồng giữa AA và khách sạn". Với sự thật mới, câu đó **sai**. Hợp đồng là **giữa AA và nhà cung cấp
(DMC)**, và giá phòng là giá DMC báo cho AA. Khách sạn ký với DMC, AA không thấy hợp đồng đó. Mục này cũng không liên
quan đại lý (giá AA bán cho đại lý là chuyện khác, ở pricing B2B).

Hai kiểu giá, ví dụ cùng một phòng:

- **Giá net** (giá vốn ròng): DMC báo "Deluxe BB 50 USD/đêm". AA trả 50, tự cộng lời khi bán.
- **Giá có hoa hồng** (commissionable): DMC báo "giá công bố 70 USD, hoa hồng cho AA 20 %". AA thực trả
  70 × (1 − 20 %) = 56 USD.

### Thị trường

DMC bán cho tour operator nước ngoài gần như luôn dùng **giá net** (bảng "net rates, non-commissionable") — đây là cách
phổ biến trong inbound châu Á, tôi khá chắc. Giá có hoa hồng hay gặp khi đại lý làm việc trực tiếp với khách sạn hoặc
qua kênh giá công bố (GDS, một số OTA), tức trường hợp AA không có.

### Đổi gì so với đề xuất cũ

Đề xuất cũ "hỗ trợ cả hai trong cùng hợp đồng (trường loại giá)" kéo theo một luồng tính hoa hồng riêng mà AA gần như
không dùng. Gọn hơn: **luôn lưu giá net** (`supplier_rates.net_amount` đã có, mọi chỗ tính giá vốn dùng nó). Nếu một
DMC gửi bảng kiểu "giá công bố + %", importer nhận hai cột tuỳ chọn và **tự quy ra net**, lưu lại hai số gốc để đối
chiếu. Không cần thêm logic ở cost sheet hay engine.

### Đề xuất cuối (B7)

Hợp đồng là AA ↔ nhà cung cấp (DMC), không phải AA ↔ khách sạn. Lưu và tính mọi giá theo net. Importer có hai cột tuỳ
chọn "Giá công bố" và "% hoa hồng": nếu có thì tự quy ra net (70 USD, 20 % → 56 USD) và giữ hai số gốc để đối chiếu.
Không làm luồng hoa hồng riêng.

---

## B8 — Nhà cung cấp có cấp allotment không → giữ ý, nói rõ allotment là của DMC

### Giải thích

**Allotment** = số phòng giữ sẵn. Với sự thật mới, đó là số phòng **DMC cam kết giữ cho AA** (DMC thường có allotment
lớn hơn với khách sạn rồi chia lại một phần, hoặc không chia). AA không thấy tồn phòng thật của khách sạn. Ba kiểu,
nhìn từ phía AA:

| Kiểu | Nghĩa | Ví dụ |
|---|---|---|
| Allotment | DMC giữ cố định N phòng/đêm cho AA; tới **release days** (hạn trả phòng) mà AA chưa bán thì phòng về lại DMC | 5 phòng Deluxe mỗi đêm từ 01/10 đến 31/12, release 21 ngày: đặt cho đêm 20/11 phải xong trước 30/10 |
| Free sale | DMC cho AA bán và xác nhận ngay, không hỏi lại, trừ ngày có stop-sale | DMC cho bán tự do mọi đêm trừ 24/12 và 31/12 |
| On request | Mỗi lần đặt, AA hỏi DMC, DMC hỏi khách sạn, trả lời sau 24–48 giờ | Mặc định khi chưa có thoả thuận |

Với chuỗi AA → DMC → khách sạn, on request là kiểu chắc chắn có; free sale và allotment chỉ có khi DMC đồng ý trên hợp
đồng. Tôi không có số liệu chắc chắn về tỉ lệ DMC châu Á cho tour operator free sale hay allotment, nên không đoán.

### Hiện trạng

Allotment hôm nay chỉ có cho ghế đại lý trên ngày khởi hành tour (`db-schema-reference.md:1699-1734`); dòng dịch vụ
`sv:` luôn on request (`apps/AA-Booking/backend/app/b2b/quotes.py:19-21`). Chưa có gì cho phòng.

### Đề xuất cuối (B8)

Giữ ý cũ, sửa cách hiểu: trong bảng restriction/allotment chung của T12, mỗi dòng ghi kiểu kho (`allotment` /
`free_sale` / `on_request`) theo **(hợp đồng AA–DMC, loại phòng, khoảng ngày)**, kèm số phòng và release days khi là
allotment. Báo giá hiện "xác nhận ngay" chỉ khi là free sale hoặc allotment còn phòng và chưa quá release days; còn lại
là on request. Đặt phòng được DMC xác nhận thì trừ allotment. Mặc định on request cho tới khi một hợp đồng DMC ghi rõ
free sale hoặc allotment. Khi gia hạn hợp đồng với DMC, contracting hỏi thêm DMC có cho free sale/allotment không.

---

## Tóm tắt thay đổi so với vòng 1

| Mục | Vòng 1 | Vòng 2 |
|---|---|---|
| T10 | Chưa mua GIATA, giữ một cột mã | Giữ, cộng 5 phần làm tốt nhập tay: chống trùng, mẫu facts, importer giá có kiểm tra, bảng mùa, nhắc xác nhận lại |
| T11 | Contracting ở Booking, content ở CIS | Giữ, cộng: nguồn + ngày xác nhận theo DMC, giải thích đồng bộ, mã xác nhận khách sạn, luật lời văn tour |
| T8 | Property master | Giữ; thêm các chỗ code phải đổi (guard giá, nhà cung cấp đặt phòng lấy từ hợp đồng, alias loại phòng) |
| T12 | Mô hình chung | Giữ; ghi rõ điều khoản và chính sách trẻ em là của DMC |
| B7 | Hỗ trợ cả net và hoa hồng | **Sửa**: hợp đồng AA–DMC, lưu net; importer quy giá có hoa hồng ra net |
| B8 | Đủ 3 kiểu, mặc định on request | Giữ; allotment là cam kết của DMC cho AA, theo hợp đồng AA–DMC |

**Chưa kiểm trong lần này:** số khách sạn và dòng giá thật trên Dev (không chạy query); có bảng giá DMC thật nào đã
import chưa; bố cục thật của bảng giá các DMC hiện có (cần một mẫu để thiết kế bản đồ cột).
