# AA-784 — Spot check 20 thẻ địa điểm (bản build thật, GPT-6 Luna × Haiku 4.5)

Ngày: 27/10/2026 (S252). Tác nhân: Claude Code.

## Mục đích

AA-784 chỉ Done khi có spot check mù trên thẻ đã build thật.
Ở đây kiểm 20 thẻ do cặp đang chạy tạo ra: GPT-6 Luna viết, Haiku 4.5 kiểm.
Câu hỏi: thẻ có đúng chỗ không, sự kiện có đúng không, có lọt chi tiết tour không.

Lưu ý: `../history.md` ghi Done-when là 30 thẻ, ≥27 đúng danh tính.
Lần này kiểm 20 thẻ theo yêu cầu workflow. Tỷ lệ tương đương là ≥90% đúng danh tính.

## Cách làm

- Chọn mẫu cố định theo md5, nên chạy lại vẫn ra cùng 20 thẻ. Mỗi nước tối đa 2 thẻ.
- `packet.json` chứa mỗi thẻ: tên, locality, region, country, các fact, và câu itinerary gốc.
  Không có tên model hay route, nên người gán nhãn không biết thẻ do ai viết.
- 2 người gán nhãn (agent có tra web) làm độc lập, mỗi fact phải có URL và câu trích.
- Chỗ hai người lệch nhau thì một người thứ ba phân xử. Có 3 thẻ phải phân xử: C04, C07, C18.
- Kết quả cuối (`final`) và nhãn gốc của A, B nằm trong `labels.json`.

## Số liệu so với cổng

Cổng lấy đúng từ `../design.md` §7. Khoảng tin cậy là Wilson 95%.

| Chỉ số | Kết quả | Wilson 95% | Cổng (§7) | Đạt? |
|---|---|---|---|---|
| FK: fact sai / fact giữ lại | 3/83 = 3,6% | 1,2% – 10,1% | ≤ 3% | **Không** (vượt 0,6 điểm, tức 1 fact) |
| UK: fact không kiểm được | 0/83 = 0% | 0% – 4,4% | không có cổng | — |
| LK: lọt chi tiết tour | 0/83 = 0% | 0% – 4,4% | ≤ 2% | Đạt |
| WI: sai danh tính | 0/20 (C07 "chưa rõ") | 0% – 16,1% | ≤ 1 thẻ, 0 sai nước | Đạt |
| Sai nước | 0/20 | — | 0 | Đạt |
| Sai locality hoặc region | 7/20 = 35% | 18,1% – 56,7% | không có cổng (chỉ báo cáo, §6) | — |
| Đúng danh tính (yes) | 19/20 = 95% | 76,4% – 99,1% | ≥ 90% (27/30) | Đạt |

Ghi chú:
- Workflow ghi LK ≤ 3%. `design.md` §7 ghi LK ≤ 2%. Bảng dùng số của `design.md`.
- Ngưỡng 3% nằm trong khoảng tin cậy của FK. Mẫu 83 fact quá nhỏ để khẳng định tỷ lệ thật trên 3%.
  Nhưng luật §7 xét theo số đo được, nên FK tính là không đạt.

## Thẻ có lỗi

Fact sai (3):
- **C02 Pleiku**, fact 0 "Pleiku is a city … and the province's capital": lỗi thời. Từ 1/7/2025 Pleiku không còn là thành phố, thủ phủ Gia Lai là Quy Nhơn. https://en.wikipedia.org/wiki/Pleiku_(city)
- **C18 Nuwara Eliya Post Office**, fact 1 "continues to serve as a post office": hiện sai. Tòa nhà đang trùng tu, bưu cục tạm chuyển sang Thư viện. https://www.sundaytimes.lk/260614/news/nuwara-eliyas-132-year-old-iconic-post-office-undergoes-rs-200-mn-restoration-645472.html
- **C20 Zenkov Cathedral**, fact 2 "designed by architect Andrei Zenkov": sai người thiết kế. Kiến trúc sư là Borisoglebsky, Zenkov sửa thiết kế và giám sát thi công. Năm 1904–1907 đúng. https://archaeology.kz/en/heritages/voznesensk-kafedraly-sobory

Sai locality / region (7):
- **C04 Thado Koshi**: locality "Lukla" sai (làng riêng dưới Lukla), region "Khumbu" là tên vùng trek. Nên là Khumbu Pasanglhamu Rural Municipality / Koshi Province. https://natureexcursion.com/blog/lukla-to-everest-base-camp-trek
- **C08 Old Goa**: locality "Goa Velha" là làng khác, cách vài dặm. Nên là Old Goa (hoặc Tiswadi). `naming_note` cũng sai cùng lý do. https://en.wikipedia.org/wiki/Old_Goa
- **C11 Bulgan Province**: region "Northern Mongolia" không phải đơn vị hành chính. Nên để null (hoặc Khangai). https://en.wikipedia.org/wiki/Bulgan_Province
- **C13 Barafu Camp**: locality "Moshi" sai, trại nằm trong vườn quốc gia, cách Moshi ~40 km. Nên để null. https://en.wikipedia.org/wiki/Kilimanjaro_National_Park
- **C14 Malé**: region "North Malé Atoll" chỉ là địa lý. Về hành chính Malé City là đơn vị riêng. Nên là Malé City (hoặc null). https://en.wikipedia.org/wiki/Malé
- **C15 Thien Mu Pagoda**: region "Central Vietnam" là vùng địa lý. Nên là Huế. https://en.wikipedia.org/wiki/Thi%C3%AAn_M%E1%BB%A5_Temple
- **C17 Kuaishan Giant Trees Trail**: đặt nhầm bên ranh giới. Nên là Tai'an Township / Miaoli County (độ tin cậy vừa). https://recreation.forest.gov.tw/Forest/RA?typ_id=0200004

Danh tính chưa rõ (1):
- **C07 China–Nepal Friendship Bridge**: thông tin thẻ đúng cho cầu Kodari–Zhangmu. Nhưng câu tour không nói cửa khẩu nào. Tour Tây Tạng hiện nay hay đi Rasuwagadhi–Kerung, nơi cũng có "Friendship Bridge". https://en.wikipedia.org/wiki/Sino-Nepal_Friendship_Bridge

9 thẻ sạch: C01, C03, C05, C06, C09, C10, C12, C16, C19.

## Kết luận

- WI: **đạt** (0 sai danh tính, 0 sai nước). LK: **đạt** (0 lọt). FK: **không đạt** (3,6% > 3%, hơn ngưỡng 1 fact).
- Spot check AA-784 chưa đạt trọn vẹn. Danh tính tốt, nhưng fact và locality/region cần sửa trước khi đóng.

Xử lý từng thẻ:
- C02, C18, C20: đánh dấu fact đó là rejected và bỏ khỏi thẻ (hoặc viết lại theo nguồn ở trên). Giữ thẻ.
- C04, C08, C11, C13, C14, C15, C17: sửa locality/region như trên. C08 sửa luôn `naming_note`. Giữ fact.
- C07: đưa vào hàng chờ review danh tính. Chưa gắn thẻ này vào tour Lhasa–Kailash cho tới khi biết cửa khẩu.

Sửa cho cả hệ, không vá từng thẻ:
- 4/7 lỗi region là tên vùng địa lý ("Northern Mongolia", "Central Vietnam", "Khumbu", "North Malé Atoll").
  Cần luật: region là đơn vị hành chính cấp 1 hoặc null. Thêm vào prompt và validator, có test hồi quy.
- 2 lỗi locality là gán thị trấn gần nhất cho điểm ở xa (Lukla, Moshi). Luật: điểm trong vườn/núi thì locality null.
- 2/3 fact sai là thông tin đã cũ (cải cách hành chính 2025, trùng tu 2026). Checker cần nghi ngờ câu hiện tại về thủ phủ, tình trạng hoạt động.
