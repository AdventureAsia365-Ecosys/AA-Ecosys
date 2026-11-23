# Nghĩa vụ dữ liệu cá nhân trên trang Compliance readiness (S288)

> **Con trỏ công khai.** Repo đang public: kết luận áp dụng từng luật, danh sách nghĩa vụ và control riêng tư nằm ở bản
> riêng tư (register v2 + ghi chú nguồn, lưu trong kho riêng tư acc2), không chép vào đây. Đây là mức sẵn sàng, không
> phải tư vấn pháp lý; mọi kết luận đều gắn cờ cần luật sư xác nhận.

_23/11/2026 (S288). Quyết định tech lead lúc chốt S287 (Q14 đổi): đưa luật bảo vệ dữ liệu cá nhân Việt Nam và GDPR vào
ngay, cùng các luật khác sau khi kiểm tra áp dụng theo thị trường và ngưỡng._

## Đã làm

- **Cấu trúc** (CIS 471): bảng `compliance.framework` (chuẩn hoặc luật, có tính % hay không), `compliance.applicability`
  (ma trận thị trường x nhóm dữ liệu x luật, mỗi kết luận có nguồn chính thức), thêm cờ luật sư, vai trò bên kiểm soát /
  bên xử lý, link văn bản và link tài liệu cho từng nghĩa vụ. Luật là danh sách kiểm đạt / chưa đạt / chưa kiểm, không
  phải phần trăm.
- **Bằng chứng tự động:** collector gốc thêm 6 kiểm tra tài liệu pháp lý (`docs/legal/`: RoPA, DPA và 4 phụ lục, danh
  sách bên xử lý phụ, hồ sơ chuyển dữ liệu ra nước ngoài, runbook yêu cầu của chủ thể dữ liệu, trang ghi nhận đồng ý; chấm
  theo chu kỳ rà soát riêng của từng trang) và ngày diễn tập xóa thật gần nhất; API CIS tự thu lượt chạy job dọn dữ liệu
  (`cis_db`) và số đếm từ CRM (`crm_ops`, crm.ops.v1 1.18: tin marketing gửi cho người chưa đồng ý, quyết định đồng ý
  mới nhất) khi admin bấm Làm mới bằng chứng.
- **Trang:** tab Nghĩa vụ trên Platform › Compliance readiness, có ma trận áp dụng và danh sách kiểm theo từng luật.

## Nguồn chính thức đã đọc (23/11/2026)

Luật 91/2025/QH15 (giới thiệu của Ngân hàng Nhà nước và bản dịch toàn văn), Nghị định 356/2025/NĐ-CP (cơ sở dữ liệu
văn bản của Bộ Tư pháp), Luật An ninh mạng 116/2025/QH15 (hiệu lực 01/07/2026, thay Luật 24/2018), Luật Dữ liệu
60/2024/QH15, GDPR và Chỉ thị ePrivacy (EUR-Lex), UK GDPR, DPA 2018, PECR (legislation.gov.uk), Privacy Act 1988 và
Spam Act 2003 của Úc (legislation.gov.au, OAIC), CCPA (cppa.ca.gov, ngưỡng điều chỉnh 2025), VCDPA (law.lis.virginia.gov),
CAN-SPAM (uscode.house.gov), PCI DSS v4.0.1.

## Việc cho luật sư (đã gắn cờ trong dữ liệu)

Phạm vi miễn 5 năm cho doanh nghiệp nhỏ theo Điều 38 Luật 91 khi có dịch vụ CRM; lưu trữ dữ liệu trong nước theo luật
an ninh mạng mới; nghĩa vụ đại diện tại EU / UK và phí ICO; câu hỏi "kinh doanh tại Úc" theo Privacy Act.
