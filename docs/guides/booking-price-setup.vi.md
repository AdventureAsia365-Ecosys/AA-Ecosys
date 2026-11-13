---
id: GUIDE-12-booking-pricing
title: Thiết lập giá trong Booking
description: Cách nhóm chăm sóc khách hàng nhập giá tour - quyền truy cập, Thiết lập giá, khách sạn và dịch vụ từ lịch trình CIS, file Excel với DRY RUN, phiên bản giá, mùa, giá tạm và giá tham khảo CIS, và kiểm một tour đã mở bán.
type: how-to
status: draft
owner: nghiep
audience: [staff, owner]
applies_to: [aa-booking-admin, aa-booking-api, aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-13
review_every_days: 90
related: [GUIDE-12, GUIDE-12-booking, GUIDE-12-cis-admin, AA-1091]
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

## 4. Nhiều tour một lúc: file Excel

### Tải và điền file

1. Trên **Price setup**, lọc các tour cần làm, rồi bấm **Download workbook** (Tải file Excel; điền sẵn các tour đó,
   tối đa 300). Với tour mới, mở **Import workbook** (Nhập file Excel) và chọn **Blank workbook** (File trống).
2. Điền các sheet. Giữ cột **Tour key**; **Title** và **Country** chỉ để đọc. Ngày viết dạng `YYYY-MM-DD`.

| Sheet | Cột | Quy tắc |
|---|---|---|
| **Tours** | Tour key, Sellable | `yes` hoặc `no`; để trống thì giữ nguyên. Tour mở bán cần có khách sạn và dịch vụ |
| **Components** | Tour key, Day, Hotel code + Room type, hoặc Service code | Mỗi dòng một mục. Tour có trong sheet này nhận đúng các mục này (các mục khác bị bỏ) |
| **Prices** | Tour key, Channel, Season, Peak, Valid from, Valid to, Pax min, Pax max, Currency, Price per person, Child price, Infant price, Single supplement | Xem bên dưới |
| **Departures** | Tour key, Start date, Capacity, Min to operate, Sales cutoff days, Decision days before, Auto confirm, Status | Chỉ ngày mới, sau hôm nay; ngày tour đã có thì bỏ qua. Status là `scheduled` (mặc định) hoặc `guaranteed` |

Sheet **Prices**, mỗi dòng một nhóm số khách và một khoảng ngày:

- **Channel**: `b2b` (mặc định) là giá mỗi khách dành cho đại lý; biểu giá đại lý và giá **From** trên TripPlanner
  chỉ đọc các dòng này. `fixed_departure` là giá một chỗ trên một chuyến khởi hành theo lịch cố định (đi ghép đoàn),
  tính theo quy tắc giá của kênh khởi hành cố định. **Currency**: để trống = USD; bước **Check** báo mọi đơn vị tiền
  không phải tiền bán.
- **Pax min** / **Pax max** (pax = số khách): số khách của nhóm, ví dụ 2–2, 3–4, 11 và để trống (để trống = không
  giới hạn trên). Các dòng cùng kênh và cùng đơn vị tiền không được chồng nhau về ngày và số khách.
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

Thời hạn báo giá, số khách được báo giá theo yêu cầu và các quy tắc kinh doanh khác nằm ở **Supply › Pricing
policy**. Đổi chúng cũng cần người thứ hai; xem [runbook Booking admin](booking-admin-runbook.vi.md).

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

Trong giai đoạn dev, tech lead là kỹ sư trực: tạo issue Jira cho vấn đề thường, nhắn trực tiếp khi gấp. Gửi kèm địa
chỉ trang, mã tour, thời điểm và ảnh chụp màn hình.

## Nguồn (cho người bảo trì)

Đọc từ AA-Booking `main` ngày 13/11/2026: `frontend/ui/local/nav.tsx`, các trang `(staff)/pricing` và `messages.ts`
của chúng (workbench, versions, seasons), `suppliers/_parts/RateSheetDrawer.tsx`,
`backend/app/catalog/price_import.py` (cột, kiểm tra và các dòng Read me của file Excel), `CONTEXT.md` ("Tour price
chain", "Agency price tiers"), `docs/implementation-notes/AA-1091*.md`; AA-CIS-App `frontend/lib/adminIa.ts`,
`frontend/app/admin/reference-prices/messages.ts`, `frontend/app/admin/platform/staff/messages.ts`,
`docs/implementation-notes/AA-1091-cis.md`. Quyết định: ADR gốc 0005, 0005b và 0019. Giữ trang này khớp với
[booking-price-setup.md](booking-price-setup.md).
