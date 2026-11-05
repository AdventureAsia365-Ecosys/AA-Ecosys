# DRAFT: KAN-20 comment (not posted)

Status: **DRAFT, not posted.** Written in S269 (05/11/2026) for the tech lead to review; it is posted on KAN-20 only
after his yes (skill `aa-jira-update`). Language: Vietnamese, for the business owner. When posted, the mention below
becomes the HTML mention node of the business owner's Jira account, and the table becomes an HTML table.
Source of every fact: [`README.md`](README.md) in this folder (public sources, accessed 05/11/2026).
Before posting: replace the link with the merged path on `master`, and re-check that no line claims more than what
runs on Dev on the posting day (the R4 items below are planned, not built). Status check on 05/11/2026: agency tiers
(Linear AA-1030) Todo, agency invoices, deposit and credit (AA-1037) Backlog, per-agency trip planner R5 (ADR 0019);
re-check each status in Linear on the posting day and keep the wording "đã lên kế hoạch" until work has started.

---

@thule Dạ chị,

Em đã so sánh xong hệ thống B2B của Asian Trails với phần B2B mình đang làm cho đại lý. Nguồn chỉ lấy từ trang công
khai của Asian Trails, Lemax (phần mềm back office họ dùng) và báo ngành, có ghi ngày truy cập.

**Asian Trails có gì (theo nguồn công khai):**

- **eConnect:** cổng đặt chỗ cho đại lý, miễn phí đăng ký, đặt thời gian thực khách sạn, tour, đưa đón, tour nhiều
  ngày và vé máy bay. Hơn 20.000 khách sạn và hơn 5.000 tour, hoạt động, đưa đón. Làm cùng công ty 11Infotech, chạy
  từ cuối 2022.
- **API** cho OTA và hãng lữ hành, kết nối thẳng hoặc qua các sàn trung gian (TravelgateX, Juniper, theo Asian Trails
  tự công bố; Juniper có ghi Asian Trails là khách hàng, TravelgateX chưa thấy xác nhận).
- **Cloud Tariff:** trang bảng giá và thông tin điểm đến, đại lý đăng nhập để xem. Điều khoản của họ có nhắc giá hợp
  đồng riêng theo sản lượng và tiền tệ thoả thuận riêng với từng đối tác; bảng giá có khác theo từng đại lý hay không
  thì nguồn công khai không nói.
- **Back office Lemax** (thắng thầu 2018, chạy từ 2019 theo case study của chính Lemax; không rõ nay còn dùng): theo
  case study đó có tự xác nhận, tự xuất hoá đơn, tự làm lịch trình.
- **Điều khoản:** giá net, không hoa hồng, không công bố hạng đại lý; trả đủ trước 30 ngày nếu không có hạn mức công
  nợ; quá hạn thì có thể dừng công nợ.

**Mình so với họ:**

| Hạng mục | Asian Trails | Mình |
|---|---|---|
| Đặt chỗ, giữ chỗ, xác nhận, huỷ có phí | Có | Đã có trên môi trường thử nghiệm |
| Giá cho đại lý | Giá net, không công bố hạng; có giá hợp đồng riêng theo sản lượng | Giá theo mùa từ giá nhà cung cấp, giá bán lẻ gợi ý = net + 25%, đã chạy thử; ba hạng đại lý 0/3/6%: đã lên kế hoạch (đợt Booking cho đại lý) |
| Hoá đơn, đặt cọc, công nợ | Có | Đã lên kế hoạch: hoá đơn tiền tour và phí phần mềm, cọc 30%, phần còn lại trước 30 ngày |
| Nội dung tour cho đại lý đăng | Kho ảnh, không cho đăng lại nội dung | Thế mạnh của mình: tour viết lại, bản riêng cho từng đại lý, đăng WordPress/Facebook |
| CRM cho đại lý | Không thấy công bố | Có trên môi trường thử nghiệm |
| Trang lên kế hoạch chuyến đi riêng cho từng đại lý | Không thấy công bố | Đợt sau |
| Khách sạn bán sỉ, vé máy bay, sàn trung gian | Có | Không làm: mình chỉ bán tour mình vận hành |

**Em sẽ bổ sung vào đợt làm phần Booking cho đại lý:**

1. Hiện chính sách phí huỷ ngay lúc báo giá, để đại lý biết phí trước khi đặt.
2. Phiếu xác nhận đặt chỗ cho đại lý đặt qua "Book with AA" (không có tên khách).
3. Bảng giá riêng từng đại lý theo hạng (tải về được), tương tự Cloud Tariff của họ.
4. Tự nhắc hoá đơn quá hạn và tạm dừng giữ chỗ mới khi quá hạn công nợ.
5. File xuất hoá đơn và thanh toán theo kỳ cho kế toán.

**Để chị cân nhắc (không gấp):** điều khoản của Asian Trails có mục "giá đăng sai": nếu giá sai lớn thì họ được sửa,
đại lý được huỷ miễn phí nếu không xác nhận lại trong 7 ngày. Em đề xuất mình thêm một mục tương tự vào điều khoản đại
lý; câu chữ chị và luật sư quyết.

Bản so sánh đầy đủ, có nguồn từng dòng: <link to docs/research/2026-11-05-asian-trails-b2b-benchmark/README.md on master>
