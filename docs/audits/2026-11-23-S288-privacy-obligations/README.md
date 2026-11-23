# Nghĩa vụ dữ liệu cá nhân trên trang Compliance readiness (S288)

> **Con trỏ công khai.** Repo đang public: kết luận áp dụng từng luật, danh sách nghĩa vụ và control riêng tư nằm ở bản
> riêng tư (register v2 + ghi chú nguồn, lưu trong kho riêng tư acc2), không chép vào đây. Đây là mức sẵn sàng, không
> phải tư vấn pháp lý; mọi kết luận đều gắn cờ cần luật sư xác nhận.

_23/11/2026 (S288). Quyết định tech lead lúc chốt S287 (Q14 đổi): đưa luật bảo vệ dữ liệu cá nhân Việt Nam và GDPR vào
ngay, cùng các luật khác sau khi kiểm tra áp dụng theo thị trường và ngưỡng._

## Đã làm

- **Cấu trúc** (CIS 471): bảng `compliance.framework` (chuẩn hoặc luật, có tính % hay không), `compliance.applicability`
  (ma trận thị trường x nhóm dữ liệu x luật, mỗi kết luận có nguồn chính thức; luật Việt Nam áp cho dữ liệu khách du
  lịch của mọi thị trường vì AA là tổ chức Việt Nam, Điều 1 khoản 2 điểm a Luật 91), thêm cờ luật sư, vai trò bên kiểm soát /
  bên xử lý, link văn bản và link tài liệu cho từng nghĩa vụ. Luật là danh sách kiểm đạt / chưa đạt / chưa kiểm, không
  phải phần trăm.
- **Bằng chứng tự động:** collector gốc thêm 6 kiểm tra tài liệu pháp lý (`docs/legal/`: RoPA, DPA và 4 phụ lục, danh
  sách bên xử lý phụ, hồ sơ chuyển dữ liệu ra nước ngoài, runbook yêu cầu của chủ thể dữ liệu, trang ghi nhận đồng ý; chấm
  theo chu kỳ rà soát riêng của từng trang) và ngày diễn tập xóa thật gần nhất; API CIS tự thu lượt chạy job dọn dữ liệu
  (`cis_db`) và số đếm từ CRM (`crm_ops`, crm.ops.v1 1.18: tin marketing gửi cho người chưa đồng ý, quyết định đồng ý
  mới nhất) khi admin bấm Làm mới bằng chứng.
- **Trang:** tab Nghĩa vụ trên Platform › Compliance readiness, có ma trận áp dụng và danh sách kiểm theo từng luật.
- **Đọc trung thực (review vòng 3):** trang pháp lý còn ở trạng thái `draft` thì kiểm tra tài liệu của nó **không đạt**
  (hôm nay mọi trang `docs/legal` đều là bản nháp, nên các nghĩa vụ dựa trên DPA, hồ sơ chuyển dữ liệu và RoPA ghi chưa
  đạt cho tới khi tài liệu được thông qua); 0 tin marketing trong cửa sổ là chưa có bằng chứng (không ghi đạt); tin bị giữ
  `send_uncertain` (có thể đã gửi) được tính là đã gửi; mỗi luật hiện ngày có hiệu lực và, nếu muộn hơn, ngày bắt đầu
  áp dụng (GDPR: hiệu lực 24/05/2016, áp dụng 25/05/2018).

## Nguồn đã đọc (23/11/2026)

Việt Nam, đọc trên **Công báo** (congbao.chinhphu.vn, bản chính thức): Luật 91/2025/QH15 (Công báo số 971 + 972, đọc
toàn văn; mọi số điều trong danh sách kiểm đã đối chiếu lại trên văn bản này), Nghị định 356/2025/NĐ-CP (Công báo số
18, đã mở và đọc: các mẫu hồ sơ, Cổng thông tin quốc gia, danh mục dịch vụ xử lý dữ liệu cá nhân ở Điều 21), Luật An
ninh mạng 116/2025/QH15 (hiệu lực 01/07/2026, thay Luật 24/2018), Luật Dữ liệu 60/2024/QH15. Vòng review đầu chỉ dựa
trên tài liệu giới thiệu của Ngân hàng Nhà nước / Sở Tư pháp Đắk Lắk và một bản dịch không chính thức; các link đó đã
được thay, và bộ nạp register giờ chỉ nhận cơ sở dữ liệu văn bản pháp luật và Công báo cho nguồn Việt Nam.
Ngoài Việt Nam: GDPR và Chỉ thị ePrivacy (EUR-Lex), UK GDPR, DPA 2018, PECR (legislation.gov.uk), Privacy Act 1988 và
Spam Act 2003 của Úc (legislation.gov.au, OAIC), CCPA (văn bản luật trên leginfo.legislature.ca.gov, Civ. Code 1798.100 trở đi; ngưỡng điều chỉnh 2025 trên cppa.ca.gov), VCDPA (law.lis.virginia.gov),
CAN-SPAM (uscode.house.gov), PCI DSS v4.0.1.

## Việc cho luật sư (đã gắn cờ trong dữ liệu)

Phạm vi miễn 5 năm cho doanh nghiệp nhỏ theo Điều 38 Luật 91 khi có dịch vụ CRM (Điều 21 khoản 1 Nghị định 356 liệt
kê dịch vụ vận hành phần mềm xử lý dữ liệu thay bên kiểm soát); Điều 29 Luật 91 (mạng xã hội, dịch vụ truyền thông trực
tuyến) có áp cho trang của AA không; lưu trữ dữ liệu trong nước theo luật
an ninh mạng mới; nghĩa vụ đại diện tại EU / UK và phí ICO; câu hỏi "kinh doanh tại Úc" theo Privacy Act.
