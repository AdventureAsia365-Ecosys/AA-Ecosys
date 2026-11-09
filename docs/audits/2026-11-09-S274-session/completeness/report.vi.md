# CIS đầy đủ cho tenant: phễu từ tour thô tới tenant, trước và sau S274 (09–10/11/2026)

Người đọc: tech lead. Số đo bằng `catalog_completeness.py` (chỉ đọc, role `cis_app`) hai lần:

- `run1-before.out`: 09/11, trước khi lấp dữ liệu.
- `run2-after.out`: 10/11 khoảng 05:35 +07, sau research US/UK/AU, recompute và lấp place card.

Tầng tour thô lấy từ bức tranh hệ thống S273. Phiên này không nạp file Excel mới, nên tầng đó không đổi.

## 1. Phễu tổng (toàn catalogue)

| Tầng | Trước | Sau | Ghi chú |
|---|---|---|---|
| Dòng khai báo trong 46 file Excel | 1.063 | 1.063 | S273 |
| Tour thô trong DB | 987 | 987 | S273 |
| Tour thô chưa xoá | 943 | 943 | 26 bị thay thế, 44 trong thùng rác |
| **Tour thô đang sống** | **917** | **917** | 14 nước |
| Master đang hoạt động | 892 (97,3%) | 892 | 25 tour chờ duyệt S1, xem mục 3 |
| Master có atom | 892 (100%) | 892 | 25.989 atom, trung vị 26 / tour; 22 tour dưới 5 atom (tour ngắn) |
| Atom có place card hoạt động | 17.598 | **17.789** | Các atom còn lại không có card là do luật: 5.432 không tên, 1.859 không tên riêng, 894 điểm hậu cần |
| Atom chờ AI viết card (needs_draft / identity / error) | 215 | **0** | Đã lấp hết, 57 tour, khoảng 0,44 USD |
| Tour có card cho mọi atom đủ điều kiện | 208 | **220** | 660 tour còn lại "partial" do atom bị luật loại, không phải thiếu dữ liệu |
| Master có ít nhất 1 điểm ghim bản đồ | — (chưa đo) | 878 | 14 Master không có điểm ghim nào (JP 10, LA/LK/MN/TW 1); 5 không có thành phần geo nào (JP 4, LK 1) |
| Segment sống (đơn vị xếp hạng) | 10.527 | 10.527 | 9.167 xếp hạng được, 1.360 bị loại toàn bộ (transit / không tên) |
| Master có ranking | 883 (99,0%) | 883 | 9 Master không có Segment: mọi atom bị luật loại (đã xem từng tour) |
| **Dòng ranking có demand, US** | 3.090 / 14.055 (22%) | **12.376 (88%)** | |
| **Dòng ranking có demand, UK** | 2.237 (16%) | **12.384 (88%)** | |
| **Dòng ranking có demand, AU** | 2.059 (15%) | **12.378 (88%)** | |
| Dòng ranking có demand, DE / FR / NL | khoảng 710 (5%) | khoảng 710 (5%) | Chưa chạy đợt R2, xem mục 4 |
| Tour có demand ở US | 635 / 883 | **867 / 883** | UK 540 → 866, AU 539 → 867 |
| **Segment qua thanh Blog, US** | 391 | **1.593** | Thanh: ≥1.000 lượt tìm và ≥3 câu hỏi |
| Segment qua thanh Blog, UK | 221 | **1.257** | |
| Segment qua thanh Blog, AU | 190 | **1.060** | |
| Master có route | 699 (78,4% số đã xếp hạng) | 699 | 177 không có route: 160 tour 1 ngày, 16 ngày không liền nhau, 7 mọi Segment bị loại, 1 tour 1 địa điểm |
| Tour có route mang demand (US / UK / AU) | 560 / 490 / 489 | **699 / 699 / 699** | |

## 2. Search demand: research theo từng thị trường (Standard queue, mỗi nước một trần riêng)

| | US | UK | AU |
|---|---|---|---|
| Địa điểm trong phạm vi | 6.134 | 6.134 | 6.134 |
| Chưa research bao giờ (trước → sau) | 3.433 → 0 | 3.553 → 0 | 3.553 → 0 |
| Địa điểm có demand trong ranking (trước → sau) | 1.033 → 4.949 | 757 → 4.955 | 711 → 4.950 |
| Đã research nhưng không ai tìm | 1.185 | 1.179 | 1.184 |
| Từ khoá có volume (trước → sau) | 6.549 → 10.292 | 3.254 → 7.033 | 3.168 → 6.953 |
| Từ khoá ≥ 1.000 lượt / tháng | 1.300 → 2.070 | 447 → 907 | 354 → 714 |
| SERP có câu hỏi PAA | 1.606 → 3.375 | — | — |
| Chi DataForSEO lần chạy cuối | 1,62 USD (volume + 1.837 SERP) | 0,48 USD | 0,48 USD |

Chất lượng giữ nguyên khi chuyển sang hàng đợi Standard rẻ hơn:

- Volume giống bản live ở 47/50 từ khoá thử.
- SERP có ≥3 câu PAA: 63,6% (bản live 65%). Có related search: 83,4% (live 86%).
- Jev giữ 92,3% (US) và 91,4% (UK, AU) số từ khoá đề xuất.
- Panel kiểm 86 từ khoá được giữ: 93% đúng.

Giá Standard queue: 0,06 USD mỗi task 1.000 từ khoá (live 0,09) và 0,0006 USD mỗi SERP (live 0,002).

Tổng chi DFS trong 24 giờ của phiên là 7,16 USD. Con số này gồm lần R1 đầu bị lỗi định tuyến LLM; dữ liệu đã mua lần đó được giữ và dùng lại. Kế hoạch S273 ước khoảng 60 USD chỉ cho US.

## 3. Phần còn thiếu, theo cách xử lý

**Cần người (không máy nào làm thay được):**

- 25 tour thô sống chưa có Master đang nằm trong hàng duyệt S1 (IN 18, LK 4, PH 2, NP 1): 12 tour qua cổng sạch, chỉ chờ bấm duyệt; 13 tour bị cổng chặn, cần sửa rồi duyệt.
- 730/892 tour chưa có ảnh bìa, 731 tour dưới 3 ảnh: đội nội dung bổ sung ảnh vào Drive, sau đó `photo_sync` chạy.
- 281 tour không có giá tham chiếu trong file nguồn: chủ doanh nghiệp cung cấp giá.
- Booking chỉ có 2/892 trip plan bán được: thiếu giá nhà cung cấp và ngày khởi hành. Đây là quyết định thương mại.

**Cố ý, không phải thiếu dữ liệu:**

- Atom transit / không tên / điểm hậu cần không có card, Segment hay ghim bản đồ (luật ADR 0019 / 0020).
- 160 tour 1 ngày không có route. Luật route cần ít nhất 2 ngày liền nhau. Thử luật "tính Segment ở mọi ngày" chỉ thêm 3 tour (CN 1, LK 2), nên không đổi luật.
- 9 Master không có Segment: mọi atom là transit hoặc không tên. Bước catch-up đúng khi không chọn tour nào.
- 1.067 Segment mồ côi được giữ vì còn alias (segment_gc ở chế độ apply, 0 dòng xoá được).
- `mobile_card_text` (892) và `content_embedding` (892) trên `published_tours` là cột cũ không app nào đọc (data coverage đã ghi "dead column"). `sku` (886) là cột tuỳ chọn của file nguồn. Ba metric này trong runner không phải lỗ hổng.

**Đã sửa trong phiên:**

- 1.471 tên địa điểm "unknown" (962 thành phần tour sống không có toạ độ). Phân loại:
  - 310 tên đúng là không phải địa điểm.
  - 1.117 tên model không biết: tên chung chung như "a Buddhist temple", hoặc quá hiếm.
  - 44 tên do lỗi: polygon quốc gia Natural Earth 1:10m không có đảo nhỏ (Koh Tao, Phi Phi, Similan, Lakshadweep). Sửa ở CIS #1413; sau deploy sẽ đưa 44 tên lại hàng chờ geocode.
- Metric "880 Master thiếu geo" của lần đo đầu là sai định nghĩa: nó đếm Master có *một* atom ngoài geo, mà luật components đã cố ý bỏ các atom đó. Metric đúng (thêm trong runner): 5 Master không có thành phần geo, 14 Master không có điểm ghim.

## 4. Thị trường

| Nhóm | Thị trường | Trạng thái |
|---|---|---|
| 1 | US, UK, AU | Xong (mục 2) |
| 2 | DE, FR, NL (đã có trong bản đồ thị trường, dùng chung code) | Đợt R2, ước 0,48 USD mỗi nước, chạy từng nước một sau khi deploy xong. Tenant dùng: trail-pulse, wildkind-travel và 2 tenant audit |
| 3 | Mã tenant khai nhưng chưa có trong bản đồ: AE, HK, SA, SG, CA, NZ | Làm sau: cần PR thêm thị trường vào `DFS_LOCATION_MAP` + `MARKET_RANK`, rồi research. Hiện các tenant này rơi về thị trường đã khai khác |

## 5. Tenant thật / demo đang hoạt động (sau)

| Tenant | Thị trường | Tour T2 | Có demand ở ít nhất 1 thị trường | Có route | Ứng viên Blog qua thanh (trước → sau) |
|---|---|---|---|---|---|
| aa1037-ledger-lane | US | 14 | 14 | 12 | 30 → 40 |
| atlas-hearth | US, UK | 9 | 8 | 7 | 7 → 35 |
| terra-family | UK, AU | 6 | 6 | 6 | 16 → 16 |
| trail-pulse | 6 thị trường | 5 | 5 | 3 | 6 → 12 |
| wildkind-travel | 6 thị trường | 3 | 3 | 3 | 5 → 7 |

Tổng 9 tenant (gồm 4 tenant audit), quy tắc Slate mới: Blog qua thanh 75 → 141, "không có dữ liệu" 310 → 113 (`slate_bar_compare`).
