# Sẵn sàng pháp lý: quyền riêng tư, điều khoản, DPA và điều khoản AI (30/10/2026)

<!-- Bản tiếng Việt của README.md (báo cáo SEC-10). Bản tiếng Anh là bản gốc: sửa bản đó trước. Các mục pháp lý là
đề xuất: có mời luật sư hay không là quyết định của business owner. -->

Phạm vi: 12 chủ đề của [bộ hồ sơ sẵn sàng pháp lý](../../legal/readiness-packet.vi.md), bốn trang công khai bản nháp,
DPA với nhà cung cấp, điều khoản AI cho đối tác. Lập ngày 30/10/2026 (S260) bởi tech lead (agent soạn).
Hạn quyết định: **11/11/2026** cho chủ đề 12 (chính sách sử dụng của nhà cung cấp AI có hiệu lực từ 12/11/2026); các
chủ đề còn lại trước khi có dữ liệu cá nhân thật đầu tiên hoặc đối tác trả tiền đầu tiên.

## 1. Tóm tắt

**Chưa sẵn sàng; không có gì gấp ngoài chủ đề 12.** Bộ hồ sơ đưa cho mỗi chủ đề một thực tế, các phương án và một đề
xuất; chưa có câu trả lời nào được ghi lại (nhật ký quyết định ở mục (c) của [sổ đăng ký](../../legal/register.md) còn
trống), nên cả 12 chủ đề đều còn mở. Bốn trang công khai đang ở dạng nháp. Chưa ký DPA với nhà cung cấp nào. Hệ thống
không giữ dữ liệu thật của khách hay đối tác (chỉ có Dev), nên các mục mở chặn go-live chứ không chặn công việc hiện tại.

| KPI | Giá trị | Mục tiêu |
|---|---|---|
| K-LEGAL-OPEN, chủ đề chưa có câu trả lời được chấp nhận | 12/12 | 0 trước go-live |
| K-LEGAL-TBC, điểm "[to be confirmed]" trên bốn trang công khai (bảng A.0 của bộ hồ sơ) | 20 | 0 trước go-live |
| K-LEGAL-TBC, dấu "[to be confirmed]" trong sổ đăng ký | 31 | 0 trước go-live |
| K-VEND-DPA, nhà cung cấp xử lý dữ liệu cá nhân đã ký DPA | 0/8 | 100 % trước go-live prod |

## 2. Cách đọc

- Một chủ đề chỉ tính là đã trả lời khi quyết định của business owner là một dòng trong nhật ký quyết định của sổ đăng
  ký.
- Các con số được đọc từ các file trong repo ngày 30/10/2026; mỗi dòng ghi rõ file nguồn.

## 6. Các chủ đề pháp lý

| # | Chủ đề | Thực tế hiện tại (ngắn) | Đề xuất (theo bộ hồ sơ) | Đã quyết? |
|---|---|---|---|---|
| 1 | Pháp nhân kiểm soát dữ liệu | Cả hai thông báo quyền riêng tư ghi "[to be confirmed]" | Công ty vận hành adventure.asia, tên đầy đủ và địa chỉ | chưa |
| 2 | Nội dung quyền riêng tư, cookie và điều khoản | Bốn trang nháp đang online, gắn nhãn "Draft - pending legal review" | Business owner đọc Phụ lục A, trả lời các điểm kinh doanh, rồi quyết có mời luật sư | chưa |
| 3 | Ghi nhận đồng ý | Một mục đích (liên hệ về chuyến đi); đã thử 20/10/2026, 0 lệch | Giữ một mục đích; chỉ thêm ô marketing (không tick sẵn) khi có hoạt động marketing | chưa |
| 4 | DPA và nhà cung cấp dịch vụ | Đã có mẫu DPA; chưa ký DPA với nhà cung cấp nào | Dùng mẫu; liệt kê đủ nhà cung cấp | chưa |
| 5 | Hồ sơ hoạt động xử lý | Đã có sổ đăng ký tạm | Dùng sổ đăng ký tạm ngay | chưa |
| 6 | Yêu cầu truy cập và xoá dữ liệu | Quy trình thủ công và runbook | Thủ công bây giờ, job đã kiểm thử trước khi có dữ liệu thật | chưa |
| 7 | Dữ liệu lưu ở Mỹ | Hạ tầng ở us-west-1 | Giữ hạ tầng ở Mỹ, chuẩn bị tài liệu chuyển dữ liệu | chưa |
| 8 | Mức dịch vụ | Chưa cam kết gì | Chỉ cam kết thời gian phản hồi cho tới khi có production | chưa |
| 9 | Địa chỉ hỗ trợ | Chưa thiết lập | `support@` về một hộp thư chung | chưa |
| 10 | Trang trạng thái | Chưa có | Chưa cần cho tới đối tác trả tiền đầu tiên | chưa |
| 11 | Gói Vercel | Hobby (phi thương mại) cho ba ứng dụng web | Lên Pro trước khi thu tiền đối tác đầu tiên (D-18) | chưa |
| 12 | Điều khoản sử dụng AI | AI Schedule ở bản nháp v0.2; tóm tắt ngắn trong điều khoản cổng đối tác | A hoặc C: chấp nhận Schedule ngay; cần trả lời trước 11/11/2026 | chưa |

## Các trang công khai bản nháp

| Trang | Tình trạng | Điểm còn mở (bảng A.0 của bộ hồ sơ) |
|---|---|---|
| TripPlanner `/privacy` | Draft - pending legal review | pháp nhân, cơ sở pháp lý, danh sách nhà cung cấp, chuyển dữ liệu, thời hạn lưu, thời gian trả lời yêu cầu, độ tuổi tối thiểu |
| TripPlanner `/terms` | Draft - pending legal review | pháp nhân vận hành, điều kiện đặt chỗ, giới hạn trách nhiệm, luật áp dụng |
| Cổng đối tác `/privacy` | Draft - pending legal review | pháp nhân, cơ sở pháp lý, danh sách nhà cung cấp AI, chuyển dữ liệu, thời hạn lưu, thời gian trả lời yêu cầu, DPA với đối tác |
| Cổng đối tác `/terms` | Draft - pending legal review | pháp nhân, quan hệ với hợp đồng đối tác, duyệt tóm tắt AI, thời hạn báo trước và chấm dứt, quyền sở hữu nội dung, phí, mức dịch vụ, luật áp dụng |

## DPA với nhà cung cấp và AI không lưu dữ liệu

Theo sổ đăng ký, mục (b) "Sub-processors": chưa ký hay kiểm tra DPA với nhà cung cấp nào. Nhà cung cấp xử lý dữ liệu
cá nhân (có hoặc có thể có): AWS (acc2), đơn vị bán lại của acc2, Amazon SES, Amazon SNS, Amazon Cognito, Vercel,
Mapbox (chỉ IP), máy chủ mail của adventure.asia. Nhà cung cấp AI: Bedrock trên tài khoản LLM (theo tài liệu AWS không
có câu hỏi lưu dữ liệu, cần luật sư xác nhận), OpenAI API (chỉ dùng khi bất đắc dĩ; log chống lạm dụng giữ tới 30 ngày
nếu chưa được duyệt chế độ không lưu), Jev (DM-6.4: cần DPA hoặc thoả thuận không lưu trước khi gửi nội dung của đối
tác).

## Điều khoản AI cho đối tác

[Bản nháp điều khoản sử dụng AI](../../legal/tenant-terms-ai-clause-draft.md): Schedule ở bản nháp v0.2, điều khoản cổng
đối tác §3 có phần tóm tắt dưới nhãn nháp, 14 câu hỏi cho luật sư ở §6. Chưa có đối tác thật hay trả tiền, nên chưa phải
gửi thông báo; mỗi đối tác chấp nhận Schedule khi tham gia. CRM cho đại lý chưa gọi nhà cung cấp AI.

## 7. Điểm chặn

| Điểm chặn | Ảnh hưởng | Kế hoạch | Vai trò phụ trách | Ngày |
|---|---|---|---|---|
| Chủ đề 12 chưa trả lời | Phần tóm tắt trên cổng đối tác vẫn là nháp khi chính sách có hiệu lực 12/11/2026 | Business owner chọn A hoặc C | business owner | 11/11/2026 |

## 8. Quyết định và ký duyệt

| Quyết định | Phương án | Đề xuất | Người quyết (vai trò) | Ngày | Kết quả |
|---|---|---|---|---|---|
| Chủ đề 12, điều khoản sử dụng AI | A chấp nhận ngay; B luật sư xem trước; C chấp nhận ngay, luật sư xem trước đối tác trả tiền đầu tiên | A hoặc C (chưa có đối tác, chấp nhận ngay không tốn gì) | business owner | trước 11/11/2026 | mở |
| Chủ đề 1–11 | theo bộ hồ sơ | các đề xuất của bộ hồ sơ | business owner | trước go-live | mở |

## Thay đổi từ lần rà soát trước

Lần rà soát đầu tiên.

## Nguồn

`docs/legal/readiness-packet.md` (rà soát lần cuối 28/10/2026), `docs/legal/register.md` mục (b) và (c),
`docs/legal/tenant-terms-ai-clause-draft.md`, đọc ngày 30/10/2026.
