---
id: GUIDE-12-booking-pricing
title: Thiết lập giá trong Booking
description: Cách nhóm chăm sóc khách hàng nhập giá tour - quyền truy cập, Thiết lập giá, khách sạn và dịch vụ từ lịch trình CIS, hợp đồng khách sạn bằng Excel và phòng được giữ, file Excel với DRY RUN, phiên bản giá, mùa, giá tạm và giá tham khảo CIS, và kiểm một tour đã mở bán.
type: how-to
status: draft
owner: nghiep
audience: [staff, owner]
applies_to: [aa-booking-admin, aa-booking-api, aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-23
review_every_days: 90
related: [GUIDE-12, GUIDE-12-booking, GUIDE-12-cis-admin, AA-1091, AA-1153, AA-1177]
lang: vi
translation_of: docs/guides/booking-price-setup.md
---

# Thiết lập giá trong Booking

Hướng dẫn này dành cho nhóm chăm sóc khách hàng nhập giá tour. Nó đi qua từng trang theo đúng thứ tự bạn dùng.
Đăng nhập, vai trò và các việc khác trong Booking nằm ở [runbook Booking admin](booking-admin-runbook.vi.md). Đây
là bản tiếng Việt của [booking-price-setup.md](booking-price-setup.md).

Tên nút và tên trang bên dưới là chữ tiếng Anh trên màn hình (mặc định). Trang **Price setup**, **Seasons**,
**Holiday events** và trang **Reference prices** của CIS có nút chuyển EN | VI; khi chuyển sang VI, tên tiếng Việt
được ghi trong ngoặc.

## 1. Xin quyền truy cập

1. Nhờ một chủ nền tảng (hiện là tech lead).
2. Chủ nền tảng mở CIS admin › **Platform › Staff & access**, mở dòng của bạn và chọn **Apply pricing preset** (Áp
   dụng mẫu nhập giá). Một lần lưu cấp cho bạn vai trò CIS **Customer Success** (Giá tham khảo) và Booking
   **Contracting** (giá nhà cung cấp, quy tắc giá, tour, ngày khởi hành, phiên bản giá, mùa).
3. Đăng xuất rồi đăng nhập lại ở cả hai ứng dụng.

Mẫu này chỉ thêm quyền. Nếu bạn đang giữ một vai trò khác trong một ứng dụng (ví dụ Booking **Sales** hoặc
**Finance**), nút bị tắt và nêu tên vai trò đó: mỗi ứng dụng chỉ cho một vai trò mỗi người, nên chủ nền tảng đổi
bằng tay. Booking **Sales** mở được **Price setup**, **Price readiness**, **Agency tiers**, **Pricing policy**,
**Seasons** và **Holiday events** ở chế độ chỉ xem (không mở được **Pricing rules & FX**) và không đổi được gì.

Mọi thay đổi giá cần **hai người**: bạn lập, một người thứ hai có vai trò Contracting hoặc Booking admin duyệt. Bạn
không bao giờ tự duyệt thay đổi của mình.

## 2. Đọc trang Price setup

Mở Booking › **Supply › Price setup** (Thiết lập giá). Mỗi dòng là một tour (trip plan) với bảy mục kiểm tra:
**Hotels & services**, **Supplier rates**, **Exchange rate**, **Pricing rule**, **Price**, **Sellable** và
**Departures** (không bắt buộc: tour thiết kế riêng không có ngày khởi hành). Các ô trên cùng đếm mọi tour; lọc theo
**Next step**, **Missing**, **Price status** hoặc **Country**, hoặc tìm theo tên hay mã tour.

Cột **Next step** (Bước tiếp theo) cho biết tour đang chờ gì:

| Bước tiếp theo | Việc cần làm |
|---|---|
| **Add hotels & services** (Thêm khách sạn & dịch vụ) | Mở **Hotels & services** của tour (mục 3) hoặc dùng file Excel (mục 4) |
| **Replace an inactive item** (Thay mục đã ngừng) | Một khách sạn, loại phòng hay dịch vụ đã bị tắt: thay nó trong **Hotels & services** |
| **Load supplier rates** (Nhập giá nhà cung cấp) | Một thành phần chưa có giá nhà cung cấp đã duyệt: nhập bảng giá của nhà cung cấp (mục 3, bước cuối) |
| **Approve an exchange rate** (Duyệt tỷ giá) | Một đơn vị tiền của giá chưa có tỷ giá được duyệt hôm nay: đề xuất tỷ giá trên **Pricing rules & FX**; một người thứ hai có vai trò Contracting hoặc Booking admin duyệt |
| **Approve a pricing rule** (Duyệt quy tắc giá) | Chưa có quy tắc giá đại lý đã duyệt đang áp dụng: đề xuất quy tắc trên **Pricing rules & FX**; một người thứ hai có vai trò Contracting hoặc Booking admin duyệt |
| **Recompute prices** (Tính lại giá) | Đã đủ mọi thứ nhưng giá chưa được tính: chọn các tour, bấm **Recompute prices** (mỗi lần 50 tour) |
| **Make sellable** (Mở bán) | Chọn các tour, bấm **Make sellable** |
| **Ready to sell** (Sẵn sàng bán) | Không còn gì phải làm |

Chỉ có giá nhập tay thì tour không bao giờ thành **Ready to sell**: báo giá cho đại lý tính giá tour từ khách sạn,
dịch vụ và giá nhà cung cấp của chúng.

## 3. Thêm khách sạn và dịch vụ từ lịch trình CIS

1. Trên **Price setup**, bấm vào tour hoặc liên kết **Hotels & services** của nó.
2. Với mỗi ngày, Booking gợi ý khách sạn nghỉ đêm và các dịch vụ mà lịch trình CIS nhắc tới (đưa đón, hướng dẫn
   viên, vé tham quan, hoạt động, bữa trưa hoặc tối), kèm **Why** (Vì sao) và độ khớp (khớp rõ, khá khớp, khớp yếu).
3. Với mỗi gợi ý, chọn **Accept** (Chấp nhận), chọn **Other match** (Lựa chọn khác) hoặc **Room type** (Loại
   phòng) khác, hoặc **Reject** (Từ chối). Bấm **Remove** (Bỏ) với mục sai; **Already on the tour** (Đã có trong tour)
   nghĩa là không cần làm gì.
4. Bấm **Save N hotel and service item(s)** (Lưu N khách sạn và dịch vụ). Chưa có gì thay đổi trước khi lưu; gợi ý
   đã từ chối sẽ hiện lại ở lần mở tour sau.
5. **No match** (Không tìm thấy) nghĩa là Booking chưa có khách sạn hay dịch vụ đó: dùng **Create supplier**,
   **Hotels** hoặc **Services**, rồi mở lại tour.
6. Với thành phần chưa có giá: **Supply › Suppliers**, mở nhà cung cấp, **Import rate sheet**, **Download the
   template**, điền, bấm **Check**, rồi **Import as draft**. Người thứ hai công bố hợp đồng nháp.

### Sửa hợp đồng khách sạn bằng Excel

Hợp đồng của một nhà cung cấp được tải ra và nhập lại bằng cùng một bảng giá.

1. **Supply › Suppliers**, mở nhà cung cấp (DMC), thẻ **Rates**, chọn hợp đồng, bấm **Excel**. File có hợp đồng, mọi
   giá (giá net, và **Published** + **Commission %** khi DMC đưa giá công bố), các **Seasons**, giá **Hotel children** và
   sheet **Inventory** (bên dưới). Khách sạn được ghi bằng mã riêng của DMC cho khách sạn đó.
2. Sửa file: một giá mới, một mùa mới, một allotment. Giữ nguyên tên cột.
3. **Import rate sheet**, chọn file, **Check**. Chưa có gì được ghi. Kết quả kiểm liệt kê lỗi theo sheet, dòng và cột,
   các cảnh báo nghiệp vụ (nửa trọn gói rẻ hơn phòng kèm ăn sáng, một khoảng trống giữa các mùa, giá tăng mạnh) và các
   thay đổi so với hợp đồng đã tải ra (giá thêm, đổi, bỏ).
4. **Import as draft**. Đây là một hợp đồng nháp mới; hợp đồng đã công bố vẫn giữ nguyên tới khi một người thứ hai
   công bố hợp đồng mới (và xác nhận đã xem mọi cảnh báo).

Một bảng giá có tối đa số dòng đặt trên **Supply › Pricing policy** (mục hotels, **Rate sheet: most rows in one
workbook**). Hợp đồng nhiều dòng hơn thì không tải được: hãy tách thành hai hợp đồng.

### Phòng được giữ: allotment, bán tự do, theo yêu cầu

Ở thẻ **Rates**, **Room and service inventory** liệt kê những gì DMC giữ cho AA theo hợp đồng. Khi hợp đồng còn là
bản nháp, **Add term** thêm một điều khoản (hoặc điền sheet **Inventory** của bảng giá: Hotel code, Room type hoặc
Service code, Kind, From, To, Units, Release days, Max pax, Notes).

| Loại | Ý nghĩa với một đặt phòng của đại lý |
|---|---|
| **Allotment** | DMC giữ chừng ấy phòng mỗi đêm cho AA. Khi còn phòng và đêm đó còn xa hơn số ngày nhả phòng, đặt chỗ của đại lý được xác nhận ngay. Ngoài ra: theo yêu cầu |
| **Free sale** (bán tự do) | AA xác nhận ngay không cần hỏi, tối đa **Max pax** khách mỗi đặt chỗ (để trống = không giới hạn) |
| **On request** (theo yêu cầu) | Mọi đặt chỗ đều hỏi DMC trên B2B desk. Cũng là cách xử lý khi không có điều khoản nào |

- **Release days** để trống = giá trị **Allotment: release days when the contract gives none** trên **Supply ›
  Pricing policy** (ban đầu 7 ngày). Giá trị được ghi vào điều khoản, nên đổi chính sách sau này không làm nó đổi.
- Phòng được giữ của mỗi DMC chỉ tính cho các đặt chỗ mà giá của DMC đó định giá: khi hai DMC cùng bán một khách sạn,
  DMC rẻ hơn (hoặc được ưu tiên) định giá phòng và chỉ allotment của DMC đó được dùng.
- Ví dụ: allotment 2 phòng, nhả phòng trước 7 ngày. Đại lý hỏi 2 phòng thì được xác nhận ngay; phòng thứ 3, hoặc mọi
  phòng ít hơn 7 ngày trước đêm ở, vào B2B desk ở dạng theo yêu cầu.

### Hợp đồng sắp hết hạn: nhắc việc

Một hợp đồng nhà cung cấp giữ giá trong một khoảng thời gian (thường là một năm). Trước khi hết hạn, Booking nhắc những
người gia hạn nó, cho mọi loại hợp đồng (khách sạn, vận chuyển, hướng dẫn viên, hoạt động, ...):

- **Thấy ở đâu**: ô **Contracts ending soon** trong **My work** trên dashboard (Booking admin và Contracting), danh sách
  **Contracts ending soon** ở đầu trang **Suppliers** (ô trên dashboard mở tới đây), cùng danh sách đó cho một nhà cung
  cấp ở thẻ **Contracts** của nó, và trang **Add-ons**. Mỗi dòng ghi số ngày còn lại, nhà cung cấp, loại, hợp đồng và
  ngày kết thúc, và nhắc việc đã **Notified** (thông báo trong ứng dụng) hay **E-mailed** (đã gửi e-mail).
- **Khi nào**: một hợp đồng đã xuất bản được liệt kê khi ngày kết thúc nằm trong **Contract expiring warning (days)**
  trên **Supply › Pricing policy** (ban đầu 60 ngày). Đổi giá trị này thì các danh sách đổi ngay.
- **E-mail**: mỗi ngày một lần (01:00 UTC), nhắc việc đăng một thông báo và gửi một e-mail cho mỗi hợp đồng và ngày
  kết thúc tới mọi nhân viên Booking đang hoạt động thuộc các vai trò trong **Contract expiring e-mail: staff roles**
  (ban đầu Booking admin và Contracting) có địa chỉ e-mail. Một vai trò tuỳ chỉnh được tính như vai trò dựng sẵn mà
  nó được sao chép từ đó, khi chưa lưu trữ và còn quyền xem nhà cung cấp. E-mail viết bằng tiếng Anh và tiếng Việt, có đường dẫn
  tới thẻ Contracts của nhà cung cấp. Một hợp đồng không bao giờ được gửi hai lần cho cùng một ngày kết thúc; nếu ngày
  kết thúc đổi, nó được báo lại. Danh sách vai trò để trống thì không gửi e-mail (thông báo và các danh sách vẫn còn).
- **Cần làm gì**: thoả thuận giá mới với nhà cung cấp và nhập hợp đồng tiếp theo (hoặc nhập bảng giá của nó) trước
  ngày kết thúc; một người thứ hai xuất bản. Những gì hợp đồng đã hết hạn định giá sẽ ngừng bán.

## 4. Nhiều tour một lúc: file Excel

### Tải và điền file

1. Trên **Price setup**, lọc các tour cần làm, rồi bấm **Download workbook** (Tải file Excel; điền sẵn các tour đó,
   tối đa 300). Với tour mới, mở **Import workbook** (Nhập file Excel) và chọn **Blank workbook** (File trống).
2. Điền các sheet. Giữ cột **Tour key**; **Title** và **Country** chỉ để đọc. Ngày viết dạng `YYYY-MM-DD`.

| Sheet | Cột | Quy tắc |
|---|---|---|
| **Tours** | Tour key, Sellable | `yes` hoặc `no`; để trống thì giữ nguyên. Tour mở bán cần có khách sạn và dịch vụ |
| **Components** | Tour key, Day, Hotel code + Room type, hoặc Service code, Meal plan | Mỗi dòng một mục. Tour có trong sheet này nhận đúng các mục này (các mục khác bị bỏ). **Meal plan** là gói ăn của một đêm khách sạn: `RO` chỉ phòng, `BB` phòng và ăn sáng, `HB` nửa trọn gói, `FB` trọn gói, `AI` bao trọn (ghi tên cũng được, ví dụ `Half board`). Để trống thì giữ gói ăn đêm đó đang có; đêm mới nhận `BB`. Dòng dịch vụ để trống cột này |
| **Prices** | Tour key, Channel, Season, Peak, Valid from, Valid to, Pax min, Pax max, Currency, Price per person, Child price, Infant price, Single supplement | Xem bên dưới |
| **Departures** | Tour key, Start date, Capacity, Min to operate, Sales cutoff days, Decision days before, Auto confirm, Status | Chỉ ngày mới, sau hôm nay; ngày tour đã có thì bỏ qua. Status là `scheduled` (mặc định) hoặc `guaranteed` |

Sheet **Prices**, mỗi dòng một nhóm số khách và một khoảng ngày:

- **Channel**: `b2b` (mặc định) là giá mỗi khách dành cho đại lý; biểu giá đại lý và giá **From** trên TripPlanner
  chỉ đọc các dòng này. `fixed_departure` là giá một chỗ trên một chuyến khởi hành theo lịch cố định (đi ghép đoàn),
  tính theo quy tắc giá của kênh khởi hành cố định. **Currency**: để trống = USD; bước **Check** báo mọi đơn vị tiền
  không phải tiền bán.
- **Pax min** / **Pax max** (pax = số khách): số khách của nhóm, ví dụ 2–2, 3–4, 11 và để trống (để trống = không
  giới hạn trên). Các dòng cùng kênh và cùng đơn vị tiền không được chồng nhau về ngày và số khách. Dòng nhập tay được
  dùng cỡ đoàn bất kỳ; giá tính từ chi phí dùng **Group size bands** (Bậc cỡ đoàn) ở **Supply › Pricing policy** (trang
  đầu của file Excel ghi các bậc này).
- **Valid from** / **Valid to**: ngày khởi hành; ngày cuối được tính.
- **Season** là nhãn cho người đọc. **Peak** vẫn được đọc nhưng không quyết định gì: lịch mùa của tour quyết định mùa
  và phụ thu cao điểm (mục 6).
- Tour có trong sheet này nhận một **phiên bản giá nháp** với đúng các giá nhập tay này. Giá tính từ giá nhà cung cấp
  được giữ, trừ khi một dòng giá tay phủ cùng ngày và số khách.

Sheet **Departures**, mỗi dòng một ngày khởi hành mới:

- **Capacity** (bắt buộc): số chỗ của chuyến, tối đa 1.000.
- **Min to operate**: số chỗ đã bán tối thiểu để chuyến chạy (không quá số chỗ); 0 hoặc để trống = không có mức tối
  thiểu. Khi số chỗ đã bán đạt mức này, lượt kiểm hằng ngày chuyển chuyến sang đảm bảo khởi hành.
- **Sales cutoff days**: ngừng bán trước ngày khởi hành bấy nhiêu ngày (tính cả ngày đó), tối đa 90; 0 hoặc để trống
  = bán tới ngày trước ngày khởi hành.
- **Decision days before**: kiểm mức tối thiểu bao nhiêu ngày trước ngày khởi hành (để trống = 21, tối đa 365). Nếu
  tới lúc đó bán chưa đủ chỗ, chuyến bị gắn cờ rủi ro và nhân viên quyết định trên B2B desk: vẫn chạy hay huỷ.
- **Auto confirm**: `yes` (hoặc để trống) = booking của đại lý còn chỗ được xác nhận ngay; `no` = mọi booking trên
  chuyến này chờ bộ phận điều hành xác nhận.

### Kiểm tra, rồi nhập

1. Mở **Import workbook**, chọn file ở ô **Filled workbook (.xlsx)** (File đã điền, tối đa 2 MB) và bấm **Check**
   (Kiểm tra). Đây là DRY RUN: chưa ghi gì.
2. Đọc kết quả. Mỗi lỗi nêu sheet, dòng và cột. Sửa file và bấm **Check** lại cho tới khi hết lỗi. Với mỗi tour, kết
   quả cho biết thay đổi gì và trạng thái giá **now** (hiện tại) và **after** (sau khi nhập).
3. Bấm **Import** (Nhập). Nhập lại cùng file lần nữa không thay đổi gì.
4. Mở tab **Versions** của từng tour và gửi duyệt bản nháp (mục 5). Giá mới chỉ có hiệu lực sau khi được duyệt.

## 5. Phiên bản giá: gửi duyệt và duyệt

Mỗi lần đổi giá là một **phiên bản** mới; không có gì bị ghi đè hay xoá.

1. Trên **Price setup**, mở liên kết **Price versions** (Phiên bản giá) của tour (hoặc mở tour, tab **Versions**).
2. Lần nhập file Excel đã tạo sẵn bản nháp. Để đổi giá bằng tay: **New draft from the prices in force** (Bản nháp
   mới từ giá đang áp dụng), sửa các dòng và khoảng ngày khởi hành, bấm **Save draft** (Lưu nháp).
3. Nhập **Reason for the change** (Lý do thay đổi; bắt buộc, tối đa 300 ký tự) và bấm **Submit for approval** (Gửi
   duyệt).
4. Người thứ hai mở cùng tab và đọc **Changes against the prices in force** (Thay đổi so với giá đang áp dụng): mỗi
   dòng trước và sau, thay đổi lớn được đánh dấu, dòng dưới mức lợi nhuận thấp nhất cho phép được gắn cờ, và các dòng
   giá kết thúc cùng phiên bản này. **What it touches** (Ảnh hưởng) đếm số báo giá còn hạn, chuyến khởi hành và dòng giá đại lý trong các ngày đó.
5. Người thứ hai bấm **Approve** (Duyệt) (hoặc **Reject** (Từ chối) kèm lý do). Phiên bản thành **Published** (Đã
   áp dụng) và giá của tour được cập nhật.

Sau khi duyệt:

- Báo giá mới, biểu giá đại lý và giá bán lẻ gợi ý dùng giá mới cho các ngày khởi hành mà phiên bản phủ. Các chuyến
  khởi hành sắp tới trong các ngày đó nhận giá mới.
- Báo giá còn hạn giữ giá cho tới khi hết hạn; báo giá lại sau đó dùng phiên bản mới. Booking đã xác nhận không bao
  giờ đổi giá.
- **Withdraw** (Rút lại) dừng phiên bản cho mọi việc mới; hộp thoại cho biết phiên bản cũ nào áp giá lại cho các ngày
  đó và ngày nào không báo giá được nữa. Phiên bản đã áp dụng do người thứ hai rút lại.

Thời hạn báo giá, số khách được báo giá theo yêu cầu, các bậc cỡ đoàn của giá tính tự động và các quy tắc kinh doanh
khác nằm ở **Supply › Pricing policy**. Đổi chúng cũng cần người thứ hai; xem [runbook Booking admin](booking-admin-runbook.vi.md).

## 6. Lịch mùa và ngày lễ

Mỗi điểm đến có một lịch mùa; tour dùng lịch của điểm đến ngày đầu tiên. Khi lịch chưa có khoảng nào được duyệt và
chưa đặt mùa mặc định khác (**Season of the other dates** khác Low), báo giá và biểu giá đại lý coi mọi ngày là thấp
điểm, còn giá hiện có giữ cờ cao điểm cũ: không giá nào thay đổi.

1. Mở **Supply › Seasons** (Mùa) và mở lịch.
2. **Add a range** (Thêm khoảng): **Kind** (**Season** hoặc **Stop-sale**), **Season** (Low, High, Peak,
   Festive), **First day**, **Last day**, một **Reason**, rồi bấm **Propose**. Khoảng lễ hội có thể **Follow a
   holiday event** (Theo một ngày lễ) thay cho ngày cố định (quốc gia, mã ngày lễ, số ngày trước và sau).
3. Người thứ hai bấm **Approve**. **Season of the other dates** đặt mùa cho mọi ngày không khoảng nào phủ (**Ask to
   change**, rồi chờ duyệt).
4. Ngày lễ là dữ liệu: **Supply › Holiday events** (Ngày lễ), **New holiday event** cho mỗi quốc gia và mỗi năm (ví
   dụ Tết Nguyên đán), người thứ hai duyệt.

Ngày đỉnh điểm và lễ hội nhận phụ thu cao điểm của quy tắc giá. Ngày lễ hội còn rút ngắn thời hạn báo giá. Khoảng
ngừng bán chuyển tour sang "theo yêu cầu" vào các ngày đó; nó không bao giờ đổi giá. Để tour dùng lịch khác, dùng ô
**Season calendar** (Lịch mùa) ở tab **Versions** của tour: thay đổi chờ người thứ hai duyệt.

## 7. Giá tạm từ giá tham khảo CIS

Với tour chưa có giá nhà cung cấp, bạn có thể hiện giá tham khảo CIS làm giá bán lẻ **tạm**.

1. Trên **Price setup**, chọn các tour và bấm **Show CIS price as provisional** (Dùng giá CIS làm giá tạm).
2. Trang đánh dấu chúng **Provisional: no supplier price yet** (Giá tạm: chưa có giá nhà cung cấp). **Clear
   provisional price** (Xoá giá tạm) bỏ giá này.

Giá tạm không bao giờ là giá hợp đồng. Nó không bao giờ được báo cho đại lý, không có trong biểu giá đại lý và không
hiện trên TripPlanner: các nơi đó chỉ dùng giá nhà cung cấp và giá nhập tay. Tour bị bỏ qua khi CIS chưa có số tiền
tham khảo, khi tour đã có giá nhà cung cấp, hoặc khi nhân viên đã gõ tay giá gợi ý.

Công tắc **Quote provisional CIS prices** (Báo giá theo giá tham khảo CIS; mặc định tắt) trên **Pricing policy** hiện
chỉ được lưu và chưa thay đổi điều này: giá tạm vẫn chỉ để hiển thị.

## 8. Giá tham khảo CIS

Giá tham khảo là giá mà file nguồn ghi cho một tour: số tiền, đơn vị tiền và cách tính. Nhân viên Booking so nó với
giá tính ra. Nó không bao giờ là giá bán.

Mở CIS admin › **AA Catalogue › Reference prices** (Giá tham khảo). Trạng thái: **No price** (Chưa có giá),
**Suggested** (Có gợi ý: CIS đọc được giá trong đoạn văn bản), **Not reviewed** (Chưa duyệt), **Needs review** (Cần
xem lại: có điểm nghi ngờ, hoặc đoạn văn bản nguồn đã đổi), **Confirmed** (Đã xác nhận).

- **Một tour**: nhập **Amount**, chọn **Currency** và **Basis** (**Per person**, **Per group**, **From (per
  person)**), thêm ghi chú nếu cần (không có dữ liệu cá nhân), rồi bấm **Save** (Lưu). **Accept** (Chấp nhận) xác
  nhận gợi ý đúng như nó là.
- **Nhiều tour trên màn hình**: **Read source texts** (Đọc đoạn giá gốc, một DRY RUN), rồi **Save these
  suggestions** (Lưu các gợi ý này). Lọc **Not reviewed**, chọn các dòng và bấm **Accept N selected** (Chấp nhận N
  dòng đã chọn).
- **Excel**: **Export Excel** (theo bộ lọc hiện tại), điền Amount, Currency, Basis và giữ cột **Key**. Gõ `yes` ở
  cột **Confirm** để xác nhận một giá đúng như nó là. **Import Excel**, **Check the file (DRY RUN)**, sửa mọi dòng
  lỗi, rồi **Apply import** (Áp dụng). File có một lỗi thì không lưu gì.

Giá **Per group** không cho Booking số tiền mỗi khách, nên không dùng làm giá tạm được.

## 9. Kiểm một tour đã mở bán

1. **Price setup**: bước tiếp theo của tour là **Ready to sell**, trạng thái **Priced** (Có giá) (hoặc **Priced by
   hand** (Giá nhập tay)), và mục **Sellable** đã đạt. **Supply › Price readiness** hiện cùng trạng thái cho mọi tour.
2. **Biểu giá đại lý**: **Supply › Agency tiers**, tab **Agencies**, bấm **View tariff** ở một đại lý. Tour có
   trong danh sách với giá theo mùa và nhóm số khách. Tour đang bán mà báo giá không tính được thì nằm ở danh sách
   riêng kèm lý do.
3. **TripPlanner**: trang tour hiện **From $X**, giá bán lẻ gợi ý thấp nhất mỗi khách cho 2 khách trong các giá đại
   lý còn hiệu lực. Giá tạm không bao giờ hiện ở đó.

## 10. Khi có gì đó không đúng

| Bạn thấy | Thì |
|---|---|
| **Check** liệt kê lỗi | Sửa đúng sheet, dòng, cột được nêu trong file rồi kiểm lại; chưa có gì được ghi |
| Tour cứ ở **Load supplier rates** | Một bảng giá vẫn là nháp, hoặc giá không phủ năm tới: nhờ người thứ hai công bố |
| Không thấy nút duyệt | Bạn lập phiên bản này: người thứ hai duyệt |
| Dải thông báo **No approved agency pricing rule is in force** | Không tour nào có giá từ giá nhà cung cấp; đề xuất quy tắc trên **Pricing rules & FX**; một người thứ hai có vai trò Contracting hoặc Booking admin duyệt |
| Trang từ chối một thay đổi | Vai trò của bạn không có quyền đó; hỏi chủ nền tảng |
| Phòng DMC giữ bằng allotment vẫn hiện theo yêu cầu | Đêm đó đã trong số ngày nhả phòng, allotment đã hết, hoặc một DMC khác định giá phòng (chỉ phòng được giữ của chính DMC đó được tính) |
| **Excel** báo hợp đồng có quá nhiều dòng | Tách hợp đồng, hoặc tăng **Rate sheet: most rows in one workbook** trên **Supply › Pricing policy** |
| Bạn không nhận được e-mail về một hợp đồng sắp hết hạn | Vai trò của bạn (hoặc, với vai trò tuỳ chỉnh, vai trò nó được sao chép từ đó) không nằm trong **Contract expiring e-mail: staff roles**, vai trò tuỳ chỉnh của bạn không có quyền xem nhà cung cấp, tài khoản nhân viên của bạn không có địa chỉ e-mail, hoặc bạn nhận vai trò sau khi e-mail đã gửi; danh sách trên **Suppliers** vẫn hiện hợp đồng đó |

Trong giai đoạn dev, tech lead là kỹ sư trực: tạo issue Jira cho vấn đề thường, nhắn trực tiếp khi gấp. Gửi kèm địa
chỉ trang, mã tour, thời điểm và ảnh chụp màn hình.

## Nguồn (cho người bảo trì)

Đọc từ AA-Booking `main` ngày 13/11/2026: `frontend/ui/local/nav.tsx`, các trang `(staff)/pricing` và `messages.ts`
của chúng (workbench, versions, seasons), `suppliers/_parts/RateSheetDrawer.tsx`,
`backend/app/catalog/price_import.py` (cột, kiểm tra và các dòng Read me của file Excel), `CONTEXT.md` ("Tour price
chain", "Agency price tiers"), `docs/implementation-notes/AA-1091*.md`; AA-CIS-App `frontend/lib/adminIa.ts`,
`frontend/app/admin/reference-prices/messages.ts`, `frontend/app/admin/platform/staff/messages.ts`,
`docs/implementation-notes/AA-1091-cis.md`. AA-1153 phần 2 (S290): `suppliers/_parts/InventoryTerms.tsx`,
`backend/app/supply/rate_sheet_export.py`, `rate_sheet_inventory.py`, `availability.py`, `CONTEXT.md` ("Hotel contracts
through DMCs"). AA-1177 (S290): `suppliers/_parts/ExpiringContracts.tsx`, `backend/app/supply/contract_expiry_mail.py`,
`CONTEXT.md` ("Add-on offers", e-mail hợp đồng sắp hết hạn). Quyết định: ADR gốc 0005, 0005b và 0019. Giữ trang này khớp với
[booking-price-setup.md](booking-price-setup.md).
