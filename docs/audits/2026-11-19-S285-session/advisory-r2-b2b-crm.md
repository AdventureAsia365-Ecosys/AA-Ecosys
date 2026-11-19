# Tư vấn vòng 2: giá trên trang đại lý, dịch vụ riêng của đại lý, dữ liệu Dev, lịch còn chỗ, gói ăn

Phiên S285, 19/11/2026. Trả lời ghi chú của tech lead trên trang quyết định cho các mục **B2, B10, T18, T19, T7, T9**.
Xây tiếp trên `advisory-crm-agency-extras.md`, `advisory-optional-activities.md`, `advisory-supply-coverage-critic.md`
(cùng thư mục). Chỉ đọc code và schema, không chạy gì trên Dev. Tên bảng/cột lấy từ
`docs/architecture/db-schema-reference.md` (bản dump 18/11/2026).

Từ dùng chung trong cả bài:

- **B2B** = bán cho doanh nghiệp (AA bán cho đại lý). **B2C** = bán thẳng cho khách lẻ.
- **DMC** (destination management company) = công ty lữ hành tại điểm đến, lo xe, khách sạn, hướng dẫn viên. Nhà cung
  cấp của AA là các DMC.
- **Giá net** = giá vốn nhà cung cấp tính cho AA. **Giá B2B** = giá AA bán cho đại lý (net cộng lợi nhuận của AA).
- **Markup** = phần trăm cộng thêm lên giá vốn để ra giá bán.
- **RRP** (recommended retail price) = giá bán lẻ gợi ý. Ở AA: RRP = giá B2B + 25 % (ADR 0019 b15).
- **Merchant of record** = bên đứng tên bán và thu tiền của khách. Ở AA đó là đại lý (ADR 0019 b5).

---

## B2. Trang TripPlanner của đại lý có hiện giá hoạt động tuỳ chọn không

### Câu hỏi của tech lead

"Đại lý không được chỉnh giá. Nếu không hiện giá thì khách lấy gì mà chọn? Nếu hiện giá theo tỉ lệ quy định như tour thì
sao? Thị trường làm thế nào? Giá đại lý sau khi nhân hệ số đã làm tròn chưa? Hiện giá lẻ thì trông rất buồn cười."

### 1. Sự thật trong code hôm nay

**a) Đại lý CÓ tự đặt giá, nhưng chỉ trong CRM.** Có ba lớp:

| Lớp | Đại lý làm gì | Bằng chứng |
|---|---|---|
| Markup mặc định theo loại sản phẩm | Chủ đại lý đặt % cho từng loại: tour, phòng khách sạn, xe, hướng dẫn viên, **hoạt động**, vé, bữa ăn. Từ 0 tới mức trần AA đặt (tối đa 300 %). | `apps/AA-Partner/api/app/proposals/retail.py:1-20, 82-114`; cột `crm.tenant_settings.retail_markup_pct` (crm-046) |
| Quy tắc giá bán lẻ | Cộng hoặc trừ % theo mùa, theo cỡ nhóm, đặt sớm, đặt sát ngày, từ −90 % tới +300 %. Có thể chỉ áp cho loại "activity". | bảng `crm.retail_price_rule` (crm-048), `apps/AA-Partner/api/migrations/048_crm_retail_pricing.sql` mục 5; `api/app/proposals/pricing.py:330-346` |
| Gõ tay giá bán từng dòng | Đại lý sửa giá bán trong báo giá. Bán dưới giá "from" của AA chỉ bị **cảnh báo, không bị chặn**. | `docs/adr/0005a-b2b-resale-warn-and-vnd.md:46`; cờ `below_from_price` |

Vậy câu "đại lý không được chỉnh giá" chỉ đúng **trên trang TripPlanner**. Hôm nay trang của đại lý **không hiện giá
nào cả, kể cả giá tour** (`apps/AA-TripPlanner-Web/CONTEXT.md:830`, ADR 0019 b5 "no AA price"). Giá chỉ xuất hiện khi đại
lý gửi báo giá từ CRM.

**b) Làm tròn: đúng là đang ra số lẻ.**

- Gợi ý giá trong CRM (markup, quy tắc, RRP × số khách) chỉ làm tròn **lên tới cent** (0,01 USD):
  `retail.py:133-136`, `pricing.py:346`.
- Giá B2B từng dòng Booking gửi sang cũng chỉ làm tròn tới cent; riêng VND làm tròn lên 1.000 đ
  (`apps/AA-Booking/backend/app/b2b/quotes.py:116-131`).
- Chỉ **RRP và bảng giá ma trận** của Booking được làm tròn lên theo bước của từng tiền tệ (tham số
  `rounding_increment_by_currency`, USD bước 5): `apps/AA-Booking/backend/app/pricing/engine.py:175-191`.

Ví dụ một hoạt động chèo kayak (số minh hoạ):

| Bước | Phép tính | Kết quả hôm nay |
|---|---|---|
| Giá net nhà cung cấp | | 30,00 USD/khách |
| Giá B2B AA (lợi nhuận mục tiêu 15 %, ADR 0005a) | 30 ÷ 0,85 | 35,30 USD |
| Đại lý được chiết khấu hạng 3 % (giảm trên số chưa làm tròn) | 35,294… × 0,97 | 34,24 USD |
| Đại lý đặt markup hoạt động 20 % | 34,24 × 1,20 | **41,09 USD** (số lẻ) |
| Thêm quy tắc mùa cao điểm +10 % (áp lên giá đã cộng markup, `builder.py:700-702`) | 41,09 × 1,10 | **45,20 USD** (số lẻ) |
| RRP của AA (đã làm tròn bước 5) | 35,294… × 1,25 = 44,12 | 45,00 USD |

Với tour, ví dụ giá B2B 1.043,48 USD/khách, markup 18 % ra **1.231,31 USD**. Đúng như tech lead lo: trông không chuyên
nghiệp.

### 2. Thị trường làm thế nào

Có hai mô hình bán lại. Khách lúc nào cũng thấy **một** giá, và đó là giá của người bán, không phải giá vốn.

- **Mô hình hoa hồng (commission).** Nhà cung cấp đặt giá bán lẻ; người bán lại bán đúng giá đó và ăn hoa hồng.
  - Viator, GetYourGuide làm kiểu này: nhà cung cấp nhập giá bán lẻ, sàn giữ phần hoa hồng. Khách thấy giá ngay trên
    trang hoạt động.
  - Rezdy, Bókun có cả giá bán lẻ gợi ý lẫn giá net cho người bán lại. Đa số đại lý trên đó bán đúng giá gợi ý.
    (Khá chắc về cơ chế, không chắc về tỉ lệ "đa số".)
- **Mô hình giá net (net rate).** Nhà cung cấp chỉ cho giá net; người bán lại tự cộng markup.
  - Đây là cách DMC bán cho đại lý (ví dụ Asian Trails gửi bảng giá tham quan theo điểm đến; hệ Tourplan, Lemax tính giá
    bán = net × markup của đại lý).
  - Trên web của đại lý, họ hiện **giá của chính họ**, thường là "từ X/khách", và **luôn số tròn**.
- **Trang tour may đo** (tailor-made, ví dụ Audley Travel): tour có "from £X per person"; hoạt động thêm thường không có
  giá riêng, ghi "chuyên viên sẽ báo giá". (Khá chắc, chưa kiểm lại trang của họ gần đây.)

AA đang theo **mô hình giá net** (ADR 0019 b15: một giá B2B, đại lý tự đặt giá bán, RRP chỉ là gợi ý). Vì thế giá trên
trang đại lý phải là giá của đại lý. Hiện giá AA (RRP) dưới thương hiệu đại lý là sai mô hình: số đó có thể khác số đại lý
báo sau.

### 3. Ba phương án

| | A. Không hiện giá | B. Hiện RRP của AA | **C. Hiện giá "từ" tính bằng luật giá của chính đại lý** |
|---|---|---|---|
| Khách thấy | "Giá có trong báo giá" | "Từ 45 USD/khách" | "Từ 42 USD/khách" (theo markup đại lý, làm tròn) |
| Ưu | Đơn giản; khớp hôm nay (tour cũng không có giá) | Dễ làm | Khách có số để chọn; số trên web = số gợi ý trong báo giá đầu tiên; giữ đúng b5 (giá của đại lý, không phải giá AA) |
| Nhược | Khách khó chọn (đúng ý tech lead) | Lệch với báo giá nếu đại lý có markup khác; đi ngược mô hình giá net | Cần nối luật giá CRM sang TripPlanner; cần thêm bước làm tròn |

### 4. Thiết kế gợi ý cho phương án C

1. **Một hàm tính giá duy nhất** cho cả gợi ý trong CRM và giá trên trang:
   `giá hiển thị = làm_tròn_lên(giá B2B "từ" × (1 + markup hoạt động của đại lý))`.
   Đại lý chưa đặt markup cho loại đó thì dùng RRP của AA (B2B × 1,25). Lưu ý: hôm nay CRM chỉ có RRP dự phòng cho
   **tour** (`retail.py:135`, `kind == "trip_plan"`); hoạt động chưa có markup thì không có gợi ý nào, nên phải thêm RRP
   cho hoạt động (Booking tính, như `v_from_prices` của tour). Quy tắc theo ngày (mùa, đặt sớm) chỉ áp khi
   khách đã chọn ngày; chưa có ngày thì hiện mức thấp nhất, chữ "từ". Quy tắc áp **sau** markup (nhân tiếp lên giá đã
   cộng markup, như code hôm nay), rồi mới làm tròn một lần ở cuối.
2. **Bước làm tròn do đại lý chọn**, theo từng tiền tệ, luôn làm tròn **lên** (không bao giờ làm mất lãi của đại lý):
   - USD: 1 (mặc định), 5 hoặc 10.
   - VND: 10.000 đ (mặc định), 50.000 đ hoặc 100.000 đ.
   - Áp cho **mọi** giá gợi ý trong CRM (tour, hoạt động, khách sạn), không chỉ trang web. Làm tròn **giá mỗi khách**
     trước, rồi mới nhân số khách, để tổng không lẻ.
   - Mặc định là một giá trị đổi được trong Settings của đại lý; trần và danh sách bước là cài đặt nền tảng sửa được trên
     trang admin, không viết cứng.
   - Ví dụ trên: 41,09 → **42 USD** (bước 1) hoặc **45 USD** (bước 5). VND: giá B2B 865.000 đ × 1,20 = 1.038.000 đ → **1.040.000 đ** (bước
     10.000).
3. **Công tắc "Hiện giá trên trang của tôi"** trong Settings của đại lý. Mặc định bật. Đại lý muốn giữ kiểu "liên hệ báo
   giá" thì tắt.
4. **Áp luôn cho giá tour** trên trang đại lý. Nếu hoạt động có giá mà tour không có giá thì khách càng khó hiểu.
5. **Không bao giờ lộ** giá B2B, markup hay tên nhà cung cấp ra trang. TripPlanner chỉ nhận con số cuối cùng.
   - Cách nối: CRM giữ luật giá, nên CRM nên tạo một view theo đại lý chỉ có số đã tính, rồi grant SELECT cho role
     `tripplanner` (giống cách CIS làm với `catalog.v_tenant_tour_v1`). Đây mới là phác thảo; tech lead chốt khi thiết kế.
6. **Ghi rõ trên trang**: "Giá tham khảo, giá cuối cùng theo báo giá của [tên đại lý]". Giá được chốt lúc báo giá, không
   chốt lúc hiển thị (như thị trường).
7. **Sửa ADR 0019 b5**: đổi "no AA price" thành "chỉ giá của đại lý, không bao giờ giá AA".

### Đề xuất cuối

Chọn **C**: trang đại lý hiện "từ X/khách" cho cả tour lẫn hoạt động. Số đó tính từ giá B2B của AA nhân markup của chính
đại lý (chưa có markup thì dùng RRP). Thêm bước làm tròn lên theo tiền tệ do đại lý chọn (mặc định USD 1, VND 10.000), áp
cho mọi giá gợi ý trong CRM. Có công tắc để đại lý tắt hiện giá. Không lộ giá B2B ra trang.

---

## B10. Bảo hiểm du lịch và phí dịch vụ của đại lý

### Câu hỏi của tech lead

"Thị trường B2B làm phần này thế nào?"

### Đường ranh giữa DMC và đại lý trên thị trường

| Thứ | Ai bán | Ai chịu trách nhiệm với khách | Tiền đi đâu |
|---|---|---|---|
| Tour trên mặt đất (xe, khách sạn, hướng dẫn viên, vé, ăn, hoạt động) | DMC/nhà bán buôn (ở đây là AA) bán cho đại lý theo giá net | Đại lý chịu với khách; DMC chịu với đại lý theo hợp đồng | Khách trả đại lý; đại lý trả DMC giá net |
| Vé máy bay | Đại lý tự xuất vé qua **GDS** (hệ đặt chỗ toàn cầu như Amadeus, Sabre), cổng hãng bay hoặc đại lý vé cấp trên (consolidator) | Hãng bay chịu chuyến bay; đại lý chịu việc đặt đúng, xuất đúng hạn | Tiền vé trả về hãng; đại lý giữ phí hoặc hoa hồng |
| Visa | Đại lý làm hộ hồ sơ | Đại sứ quán quyết; đại lý chỉ chịu việc nộp đúng, đủ, đúng hạn | Phí visa là tiền **chi hộ**, chuyển nguyên cho cơ quan cấp; đại lý thu thêm phí dịch vụ |
| Bảo hiểm du lịch | Đại lý bán thay hãng bảo hiểm | Hãng bảo hiểm chịu bồi thường | Phí bảo hiểm về hãng; đại lý nhận hoa hồng |
| Phí dịch vụ của đại lý | Đại lý | Đại lý | Doanh thu của đại lý |

Ba điểm thị trường làm giống nhau:

1. **DMC không đụng vé máy bay, visa, bảo hiểm** của khách lẻ. Có DMC bán thêm vé nội địa, nhưng đó là dịch vụ riêng có
   hợp đồng riêng. Với AA, luật đã chốt: những thứ này là của đại lý.
2. **Bảo hiểm luôn là một dòng riêng, có giá riêng, khách được quyền từ chối.** Ở Anh, EU có luật về bán kèm bảo hiểm.
   Ở nhiều nước, người bán bảo hiểm phải là đại lý bảo hiểm có đăng ký. (Khá chắc cho Anh/EU; **chưa chắc cho Việt Nam**,
   cần luật sư bên business owner xác nhận. Đây là việc kinh doanh, không phải việc kỹ thuật.)
3. **Phí dịch vụ của đại lý** thường là một dòng riêng ("service fee", "booking fee") hoặc gộp vào giá tour. Cả hai đều
   phổ biến.

### Đề xuất cuối

Giữ như đề xuất: bảo hiểm và phí dịch vụ là dịch vụ riêng của đại lý, nhập tay, không tích hợp, không gửi sang AA. Thêm
một câu trong điều khoản đối tác: đại lý tự đảm bảo mình được phép bán bảo hiểm ở nước của mình. CRM không kiểm giấy phép
này.

---

## T18. Dịch vụ riêng của đại lý trong CRM: rạch ròi thế nào khi bán B2B

### Câu hỏi của tech lead

"Tư vấn thêm để rõ ràng hơn: khi bán kiểu B2B thì nên rạch ròi thế nào?"

### Ba chỗ phải tách bạch

**1) Trách nhiệm.**

- AA chịu trách nhiệm với đại lý về phần tour (dòng `aa`).
- Đại lý chịu trách nhiệm với khách về **toàn bộ** chuyến đi, vì đại lý là bên tổ chức (b12) và đứng tên bán (b5).
- Riêng dòng của đại lý (vé máy bay, visa, bảo hiểm, phí): AA không liên quan.
- Ví dụ thực tế:
  - Khách trượt visa, hủy tour 10 ngày trước khởi hành → phí hủy tour của AA vẫn tính cho đại lý. Đại lý tự xử lý với
    khách.
  - Hãng bay đổi giờ, khách đến trễ → đại lý báo AA đổi giờ đón. Dữ liệu này đi qua `crm.traveler_flight`.
- Ở thị trường EU/Anh: ai **ghép** vé máy bay với tour thành một gói thì thành bên tổ chức gói, chịu trách nhiệm cả gói
  (Package Travel Directive; ở Anh thêm bảo hiểm ATOL cho gói có vé máy bay). Đây là chuyện của đại lý, không phải của AA.
  (Chắc về nguyên tắc; chi tiết từng nước để luật sư.)

**2) Tiền và hoá đơn.**

- **AA → đại lý:** hoá đơn B2B chỉ gồm các dòng AA, theo giá B2B. Không bao giờ có vé máy bay hay visa (đã đúng trong
  code: đồng bộ Booking chỉ lấy dòng `aa`, `apps/AA-Partner/api/app/booking/sync.py:126,190,207`).
- **Đại lý → khách:** một hoá đơn, nhưng chia hai nhóm:
  - "Tour (Adventure Asia)": giá bán của đại lý cho phần tour.
  - "Dịch vụ do [tên đại lý] cung cấp": từng dòng có giá.
- Gộp hay tách giá:
  - **Vé máy bay và phí đại lý:** cho phép gộp vào giá trọn gói. Đại lý hay muốn giấu giá vé để khách không so giá.
  - **Phí visa và bảo hiểm:** luôn để dòng riêng. Phí visa là tiền chi hộ; bảo hiểm khách phải thấy giá và có quyền từ
    chối.

Ví dụ một cặp đôi, tour 8 ngày:

| Dòng | Giá vốn của đại lý | Giá bán cho khách | Ghi chú |
|---|---|---|---|
| Tour AA (2 khách) | 2.000 USD (hoá đơn AA) | 2.500 USD | Markup 25 % của đại lý |
| Vé máy bay HAN–SGN (2 vé) | 240 USD | 270 USD | Gộp được vào giá gói |
| Phí e-visa (2 người) | 50 USD | 50 USD | Chi hộ, luôn tách riêng |
| Bảo hiểm (2 người) | 60 USD | 72 USD | Luôn tách riêng, khách được từ chối |
| Phí dịch vụ đại lý | 0 | 50 USD | Gộp được |
| **Tổng khách trả đại lý** | | **2.942 USD** | AA chỉ thu 2.000 USD từ đại lý |

**3) Dữ liệu trong CRM: mỗi dòng của đại lý cần gì.**

| Loại (`category`) | Nhà cung cấp (có thể để trống = "Đại lý tự làm") | Hạn cần theo dõi (`due_at`) | Giấy tờ gắn vào dòng |
|---|---|---|---|
| `flight` | Hãng bay hoặc đại lý vé cấp trên | Hạn xuất vé (TTL, ticketing time limit: quá hạn thì chỗ giữ bị hủy) | E-ticket, PNR (mã đặt chỗ) |
| `visa` | Đại sứ quán, dịch vụ visa, hoặc để trống | Hạn nộp hồ sơ | Thư mời, visa đã cấp |
| `insurance` | Hãng bảo hiểm | Trước ngày khởi hành (tốt nhất ngay khi khách đặt cọc) | Giấy chứng nhận bảo hiểm |
| `fee` | Để trống | Không cần | Không cần |

Thị trường: Tourplan và Lemax coi mỗi dịch vụ là một "service line" có loại, giá vốn, giá bán, trạng thái, voucher. CRM
cho đại lý (TravelJoy, Tern, Travefy) cho nhập tay vé máy bay và gắn e-ticket. Vì vậy thiết kế trong
`advisory-crm-agency-extras.md` đi đúng hướng.

### Đề xuất cuối

Giữ đề xuất, chỉnh hai chỗ:

- **Quy tắc gộp giá:** chỉ cho gộp vé máy bay và phí đại lý vào giá tour. Phí visa và bảo hiểm luôn là dòng riêng.
- **Câu miễn trừ** in sẵn dưới nhóm "Dịch vụ do [đại lý] cung cấp" trên báo giá và hoá đơn.

Phần còn lại giữ như cũ.

---

## T19. Khoảng 63 dòng nhà cung cấp riêng của đại lý trên Dev: ngưng dùng hay xoá hẳn

### Câu hỏi của tech lead

"Tư vấn thêm: để lại hay xoá hẳn?"

### Sự thật cần biết trước

1. **Con số 63 là cả bảng**, không phải chỉ các dòng thuộc loại bị chặn.
   - `crm.agency_supplier` có khoảng 63 dòng (`db-schema-reference.md:5383`), gồm cả dòng "Adventure Asia" dựng sẵn mỗi
     đại lý (kind `aa`).
   - Số dòng thật thuộc loại bị chặn (accommodation, transport, activity, guide, restaurant, dmc) **chưa đếm**. Phải đếm
     trước khi viết migration.
2. **Bảng không có cột "đang dùng/ngưng dùng".** Chỉ có thùng rác:
   - `deleted_at`, `deleted_by`, `purge_after` = xoá mềm, khôi phục được trong hạn.
   - CRM đã có luật: nhà cung cấp còn dòng booking đang sống thì không cho vào thùng rác (409 `supplier_in_use`,
     `apps/AA-Partner/CONTEXT.md:998`).
3. **Xoá hẳn sẽ đụng khoá ngoại (FK, liên kết giữa các bảng):**
   - Khoá ngoại từ `crm.option` và `crm.booking_line` **chặn** việc xoá: báo giá và dòng booking của các trip demo sẽ làm
     DELETE lỗi.
   - Khoá ngoại từ `crm.supplier_bill`, `crm.departure_cost`, `crm.aa_invoice_cache`, `crm.agency_service` có
     **ON DELETE CASCADE**: xoá nhà cung cấp là **lặng lẽ xoá luôn** hoá đơn nhà cung cấp và chi phí của trip.
   - Nguồn: `apps/AA-Partner/api/migrations/014…:221`, `019…:316`, `051…:138,252,296`, `052…:74`.
4. **Khoảng 16 file test** của AA-Partner đang tạo nhà cung cấp loại `accommodation`, `restaurant`, `dmc`… (ví dụ
   `api/tests/integration/test_ledger_api.py`, `test_crm014_schema.py`). Đổi luật CHECK (ràng buộc giá trị trong DB) thì
   phải sửa các file này trong cùng PR, nếu không CI đỏ.
5. **Quy trình DRY RUN** (`skill/aa-cis-schema/references/destructive-ops.md`): mọi DELETE vĩnh viễn phải đếm trước, chụp
   snapshot, chạy thử trong transaction và chờ tech lead đồng ý mới COMMIT. Đổi nhãn và xoá mềm thì không thuộc diện này.

### So sánh

| | Xoá hẳn | **Đổi nhãn + cho vào thùng rác** |
|---|---|---|
| Dữ liệu sạch | Sạch nhất | Sạch với người dùng: danh bạ không còn hiện các dòng đó |
| Lịch sử, trip demo, video UAT | Mất hoặc vỡ: hoá đơn, chi phí bị cascade xoá; báo giá cũ lỗi | Giữ nguyên |
| Làm được trong 1 migration | Không: vướng FK chặn, phải xoá trip demo trước | Có |
| Quy trình DRY RUN + duyệt | Bắt buộc (mất thêm một vòng) | Không bắt buộc; vẫn đếm trước |
| Lùi lại được | Chỉ bằng snapshot RDS | Khôi phục từ thùng rác |

Dev không có đại lý thật, nên "giữ lịch sử" không vì pháp lý. Lý do chính là **rẻ và an toàn hơn**: không làm vỡ dữ liệu
demo, không cần vòng DRY RUN, và đi đúng cơ chế xoá mềm sẵn có của CRM.

### Cách làm trong migration CRM

1. **Đếm trước** (chỉ đọc): theo `kind`, `category`, và số dòng có báo giá, dòng booking, hoá đơn, chi phí tham chiếu tới.
   Ghi số vào PR.
2. `UPDATE` các dòng `kind='own'` thuộc loại bị chặn sang `category='other'`. `other` vẫn được phép trong danh bạ, theo
   phản biện mục 6. Mọi FK vẫn nguyên.
3. Dòng **không** còn dòng booking sống nào tham chiếu: cho vào thùng rác (đặt `deleted_at`, `deleted_by =
   'migration:crm-NNN'`, `purge_after`). Dòng còn được tham chiếu giữ lại với nhãn `other`, chỉ để đọc lịch sử.
4. Sau đó mới thu hẹp CHECK `agency_supplier_category_chk`.
5. Sửa fixture test cùng PR.
6. Lưu ý dòng đang bị legal hold (giữ dữ liệu theo yêu cầu pháp lý): trigger `crm.guard_held_change` sẽ chặn UPDATE. Bước
   đếm phải đếm luôn các dòng này; trên Dev nhiều khả năng bằng 0.

### Đề xuất cuối

**Không xoá hẳn.** Trong cùng migration CRM: đếm trước, đổi các dòng `own` thuộc loại bị chặn sang `other`, cho các dòng
không còn được dùng vào thùng rác, giữ lại các dòng còn được tham chiếu, rồi mới thu hẹp CHECK. Sửa fixture test cùng PR.
"Ngưng dùng" ở đây chính là thùng rác sẵn có; không thêm cột trạng thái mới.

---

## T7. Lịch còn chỗ của hoạt động tuỳ chọn: thương mại làm thế nào

### Câu hỏi của tech lead

"Trong thương mại làm sao nhỉ?"

### Năm cách bán chỗ phổ biến

| Cách | Nghĩa là | Ví dụ | Ai hay dùng |
|---|---|---|---|
| **Free sale** (bán tự do) | Nhà cung cấp cho phép người bán xác nhận ngay mà không cần hỏi, thường kèm giới hạn ("tối đa 8 khách/booking") cho tới khi nhà cung cấp báo dừng | Vé múa rối nước, tour xe đạp quanh Hội An: nhận ngay ≤ 8 khách | Hợp đồng DMC với khách sạn và hoạt động đông chỗ |
| **On request** (theo yêu cầu) | Mỗi booking gửi hỏi nhà cung cấp, chờ xác nhận (thường 24–48 giờ) | Lớp nấu ăn nhỏ ở Hội An, 2 lớp/ngày | Nhà cung cấp nhỏ, không có hệ thống |
| **Allotment** (số chỗ giữ sẵn) | Nhà cung cấp giữ sẵn X chỗ mỗi ngày cho người bán. Qua **hạn trả chỗ** (release, ví dụ 7 ngày trước) mà chưa bán thì chỗ trả về nhà cung cấp | Du thuyền Hạ Long giữ 4 cabin/đêm cho AA, trả chỗ trước 14 ngày | Khách sạn, du thuyền, show có ít ghế |
| **Lịch chỗ trực tuyến** (live availability) | Nhà cung cấp quản lý số chỗ theo từng giờ khởi hành trên phần mềm; người bán đọc qua API và xác nhận ngay | Tour 9:00 còn 6 chỗ | Bókun, Rezdy, FareHarbor; Viator và GetYourGuide nhận lịch này qua API |
| **Stop sale** (dừng bán) | Nhà cung cấp đóng một ngày hay một khoảng ngày | Bão, ngày lễ, thuyền bảo dưỡng | Mọi mô hình |

Hai luật đi kèm mọi cách trên:

- **Cut-off** (hạn chót đặt): phải đặt trước giờ bắt đầu ít nhất bao lâu. Ví dụ 24 giờ, hoặc "trước 17:00 hôm trước".
- **Ngày hoạt động và giờ khởi hành**: ví dụ chỉ chạy thứ 3, 5, 7, khởi hành 8:00. Thường kèm **số khách tối thiểu**
  (ví dụ tối thiểu 2 khách mới chạy).

Thị trường: Viator và GetYourGuide ưu tiên hiển thị hoạt động **xác nhận ngay**. (Khá chắc; chính sách xếp hạng chi tiết
thì không chắc.) DMC bán cho đại lý thì phần lớn hoạt động là on request hoặc free sale theo hợp đồng. Allotment chỉ dùng
cho thứ ít chỗ.

### AA hôm nay

- Tour có lịch khởi hành (`tp:`) đã có đủ: số chỗ, tự xác nhận, hạn chót bán, allotment theo đại lý
  (`booking.departure_allotments`, mô tả trong `apps/AA-Booking/backend/app/b2b/quotes.py:19-25`).
- Dịch vụ lẻ (`sv:`), trong đó có hoạt động, **luôn** là on request.
- Bảng giá nhà cung cấp gửi AA thường không có số chỗ theo ngày, nên làm allotment cho hoạt động bây giờ là làm thứ không
  có dữ liệu để nhập.

### Đề xuất cuối

Giữ hướng của đề xuất, thêm một cờ rẻ. Bản đầu gồm:

- Mặc định on request.
- Cut-off theo giờ.
- Ngày hoạt động trong tuần và giờ khởi hành.
- Số khách tối thiểu.
- Stop sale: dùng **bảng restriction/allotment chung** của T12 (lát L5 trong `advisory-r2-plan.md`), khoá theo thành
  phần `sv:`. Lịch mùa sẵn có hôm nay gắn với tour (trip plan), không gắn với từng dịch vụ, nên không dùng lại được
  cho hoạt động lẻ.
- **"Free sale tới N khách/booking"**: một dòng kiểu `free_sale` (kèm N) trong cùng bảng chung đó, giống cách B8 làm
  cho phòng khách sạn. Khi nhà cung cấp đồng ý bằng hợp đồng, engine trả `available` thay vì `on_request`, AA xác nhận
  ngay không cần hỏi. Không thêm cột riêng trên add-on, để hoạt động và khách sạn dùng một mô hình.

Làm allotment theo ngày (kiểu `allotment` trong cùng bảng) khi có nhà cung cấp gửi số chỗ.

---

## T9. Gói ăn mặc định của tour: RO / BB / HB / FB / AI là gì

### Câu hỏi của tech lead

"Chưa hiểu các thuật ngữ viết tắt."

### Nghĩa từng chữ

Đây là "board basis" (gói ăn kèm phòng khách sạn). Booking lưu ở cột `booking.supplier_rates.meal_plan`, chỉ cho giá phòng
khách sạn (`db-schema-reference.md:3366`, `apps/AA-Booking/backend/app/supply/rates.py:35`).

| Mã | Viết đầy đủ | Nghĩa | Ví dụ giá (minh hoạ, phòng đôi/đêm) |
|---|---|---|---|
| **RO** | Room Only | Chỉ phòng, không ăn | 70 USD |
| **BB** | Bed & Breakfast | Phòng kèm bữa sáng | 80 USD |
| **HB** | Half Board | Nửa suất: bữa sáng + một bữa chính (thường là tối) | 80 + 2 × 15 = 110 USD |
| **FB** | Full Board | Trọn suất: sáng, trưa, tối | 80 + 2 × 30 = 140 USD |
| **AI** | All Inclusive | Trọn gói: 3 bữa + đồ uống, đồ ăn nhẹ trong khu nghỉ dưỡng | 200 USD |

Lịch trình tour hay ghi bữa theo ngày bằng **B / L / D** (Breakfast sáng, Lunch trưa, Dinner tối). Ví dụ "Ngày 3: B, L"
nghĩa là ngày 3 có bữa sáng và bữa trưa.

### Vì sao BB là mặc định

1. **Khách sạn thành phố ở Đông Nam Á gần như luôn báo giá BB.** Bảng giá DMC gửi AA phần lớn là BB.
2. **Bữa trưa, bữa tối của tour thường ăn ở nhà hàng địa phương** trên đường đi. Đó là dịch vụ ăn uống riêng của tour
   (`service_type='meal'`), không phải bữa của khách sạn. Lấy HB hay FB ở khách sạn sẽ trói khách vào nhà hàng khách sạn,
   và dễ **tính tiền hai lần** cùng một bữa tối.
3. **HB/FB/AI chỉ hợp ở nơi không có chỗ ăn bên ngoài**: homestay Sapa, lodge miền Tây, khu nghỉ dưỡng biển (Phú Quốc,
   đảo Thái Lan). Du thuyền Hạ Long ngủ đêm vốn đã gồm bữa theo kiểu trọn suất.

### Đề xuất cuối

Giữ đề xuất: BB mặc định; tour hoặc báo giá được chọn HB/FB (AI cho khu nghỉ dưỡng). Thêm một kiểm tra nhỏ khi làm: nếu
một đêm lấy HB/FB mà ngày đó tour đã có bữa tối ở nhà hàng (dịch vụ `meal`) thì cảnh báo trùng bữa.

---

## Tóm tắt quyết định

| Mục | Giữ hay đổi | Một câu |
|---|---|---|
| B2 | **Đổi** | Hiện giá "từ" của chính đại lý (markup đại lý, không có thì RRP), làm tròn lên theo bước đại lý chọn, áp cho cả tour; có công tắc tắt |
| B10 | Giữ | Bảo hiểm và phí là dịch vụ riêng của đại lý; thêm câu "đại lý tự đảm bảo được phép bán bảo hiểm" vào điều khoản |
| T18 | **Chỉnh nhỏ** | Chỉ cho gộp vé máy bay và phí đại lý vào giá tour; visa và bảo hiểm luôn dòng riêng; in câu miễn trừ |
| T19 | **Chỉnh** | Không xoá hẳn: đổi sang `other`, cho vào thùng rác dòng không dùng, đếm trước; 63 là cả bảng, chưa phải số bị chặn |
| T7 | **Chỉnh nhỏ** | "Free sale tới N khách" và stop sale là dòng trong bảng restriction/allotment chung của T12 (L5); allotment để sau |
| T9 | Giữ | BB mặc định; cảnh báo trùng bữa khi chọn HB/FB |

Chi phí: không có dịch vụ AWS mới, không gọi LLM. Các phần có migration (B2 làm tròn + view giá, T19; T7 nằm trong
migration chung của lát L5 bên Booking) là thay đổi schema, cần agent review trước khi merge theo luật dev phase.
