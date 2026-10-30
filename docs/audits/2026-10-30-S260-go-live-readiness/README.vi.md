# Sẵn sàng go-live: mọi ứng dụng (30/10/2026)

<!-- Bản tiếng Việt của README.md (báo cáo OPS-17). Bản tiếng Anh là bản gốc: sửa bản đó trước. -->

Phạm vi: CIS (nội dung và danh mục tour), Booking, TripPlanner, Partner (CRM và cổng đối tác). Lập ngày 30/10/2026
(S260) bởi tech lead (agent soạn). Hạn quyết định: chưa có, vì chưa đặt ngày go-live.

## 1. Tóm tắt

**Chưa sẵn sàng, đúng như dự kiến:** chưa có môi trường production. ADR 0012 (chấp nhận 29/10/2026) đã chốt mô hình
môi trường và cổng go-live; phần xây dựng (khoảng 3–4 tuần) chỉ bắt đầu khi business owner đặt ngày go-live. ADR 0018
(đề xuất 30/10/2026) sẽ đưa prod sang một tài khoản AWS riêng và cần được chấp nhận hoặc bác trước.
Trong 12 mục bắt buộc của cổng nền tảng và các báo cáo liên quan, chưa mục nào xong (ADR 0012 đã chấp nhận, ADR 0018
còn mở); theo từng ứng dụng, 3 trên 14 mục bắt buộc đã xong (các endpoint health). Không có mục nào bị bên thứ ba
chặn; mục 3 (rà soát tài khoản quản lý) phụ thuộc ADR 0018. Việc cần business owner quyết: **một ngày (hoặc khoảng
thời gian) go-live, và lần prod đầu cần những ứng dụng nào.**

## 2. Cách đọc

- Mục bắt buộc chặn go-live; mục nên có có thể dời, kèm người phụ trách và ngày.
- "Xong" nghĩa là có link bằng chứng; khẳng định không có bằng chứng tính là còn mở.
- Mục 1–8 là cổng go-live của ADR 0012 (quyết định 11), mục 9–12 là các cổng báo cáo liên quan của OPS-17.

## 3. Bảng điểm

| Mảng | Mục bắt buộc | Xong có bằng chứng | Bị chặn | Trạng thái |
|---|---|---|---|---|
| Cổng nền tảng (ADR 0012 quyết định 11) | 8 | 0 | 0 | mở |
| Cổng báo cáo liên quan (OPS-08, OPS-03, SEC-05, SEC-10, DEV-04, SEC-03, FI-06) | 4 | 0 | 0 | mở |
| CIS | 3 | 1 | 0 | mở |
| Booking | 4 | 1 | 0 | mở |
| TripPlanner | 4 | 0 | 0 | mở |
| Partner (CRM, cổng đối tác) | 3 | 1 | 0 | mở |

## 4. Danh sách kiểm

### Cổng nền tảng

| # | Mục | Bắt buộc / nên có | Trạng thái | Bằng chứng | Vai trò phụ trách | Hạn |
|---|---|---|---|---|---|---|
| 1 | Mô hình môi trường được chấp nhận (ADR 0012); ADR 0018 được chấp nhận hoặc bác | bắt buộc | ADR 0012 xong; ADR 0018 mở | [ADR 0012](../../adr/0012-environment-model.md); [ADR 0018](../../adr/0018-lean-aws-account-model.md) đang đề xuất | tech lead | trước khi xây |
| 2 | Kế hoạch Terraform prod được rà soát với một con số chi phí hằng tháng đã đối chiếu, duyệt trước khi apply (D-19) | bắt buộc | mở | — | tech lead | tuần xây 2 |
| 3 | Agent chuyển sang role chỉ cho Dev; ghi nhận rà soát tài khoản quản lý (ADR 0012 quyết định 4.4, 4.5) | bắt buộc | mở | — | tech lead | trước khi xây |
| 4 | Quyết định lại ADR 0014 quyết định 4 cho các repo private | bắt buộc | mở | — | tech lead | trước khi xây |
| 5 | Diễn tập khôi phục trên prod đạt, có ghi RTO (DM-9.3, OPS-03) | bắt buộc | mở | [diễn tập](../../ops/drills/README.md) | tech lead | tuần xây 3 |
| 6 | Cảnh báo có đường gọi trực và kênh báo thứ hai đã thử; hai SLO cho mỗi API công khai | bắt buộc | mở | OPS-13 đo 3 mục tiêu của CIS, chỉ trên Dev | tech lead | tuần xây 3 |
| 7 | Đổi secret (D-02, D-03); bản PDF break-glass của các runbook chính | bắt buộc | mở | [break-glass](../../ops/runbooks/break-glass.md) | tech lead | tuần go-live |
| 8 | Đóng mọi kiểm soát mà [baseline bảo mật](../../security/baseline.md) ghi "before prod"; chạy job seed nội dung và đối chiếu số với Dev | bắt buộc | mở | baseline: GuardDuty, Access Analyzer, S3 BPA, Redis AUTH/TLS còn thiếu | tech lead | tuần go-live |

### Cổng báo cáo liên quan

| # | Mục | Bắt buộc / nên có | Trạng thái | Bằng chứng | Vai trò phụ trách | Hạn |
|---|---|---|---|---|---|---|
| 9 | Duyệt ngân sách prod (FI-06) và rà soát năng lực / bộ SLO (OPS-08) | bắt buộc | mở | FI-06 và OPS-08 sinh hằng tháng trên Dev (engine báo cáo CIS) | business owner, tech lead | tuần xây 1 |
| 10 | Rà soát quyền truy cập của quý (SEC-05); cảnh báo bảo mật quá hạn = 0 (SEC-03) | bắt buộc | mở | SEC-03 bản nháp sinh hằng tháng từ 11/2026 (số của CIS; số GitHub điền tay) | tech lead | tuần xây 3 |
| 11 | Sẵn sàng pháp lý: trả lời đủ 12 chủ đề (SEC-10) | bắt buộc | mở | [sẵn sàng pháp lý 30/10/2026](../2026-10-30-S260-legal-readiness/README.vi.md): mở 12/12 | business owner | trước go-live |
| 12 | Ký UAT cho từng ứng dụng (DEV-04, AA-855: video sau khi xong phần kỹ thuật) | bắt buộc | mở | — | business owner | tuần go-live |

### Theo ứng dụng

| Ứng dụng | Mục | Bắt buộc / nên có | Trạng thái | Bằng chứng | Vai trò phụ trách |
|---|---|---|---|---|---|
| CIS | Endpoint health và readiness trả lời | bắt buộc | xong | bản tin OPS-12 hằng ngày kiểm `/health` + `/health/ready` | tech lead |
| CIS | Image prod được nâng theo digest từ Dev (ADR 0012 quyết định 7) | bắt buộc | mở | chưa có workflow Deploy Prod | tech lead |
| CIS | Engine báo cáo và snapshot KPI hằng ngày đang chạy | nên có | xong | /admin/reports (EX-04, EX-06, OPS-12 hằng ngày) | tech lead |
| CIS | Trang admin trên project Vercel prod, gói Pro (D-18) | bắt buộc | mở | đang dùng Hobby | tech lead |
| Booking | Endpoint health và readiness trả lời | bắt buộc | xong | bản tin OPS-12 hằng ngày | tech lead |
| Booking | Thanh toán chỉ bật trên prod (điều kiện kích hoạt của ADR 0012 quyết định 11) | bắt buộc | mở | đang làm lát hoá đơn / thanh toán (AA-952) | tech lead |
| Booking | Trang admin Booking trên project Vercel prod, gói Pro | bắt buộc | mở | đang dùng Hobby | tech lead |
| Booking | Rà soát quyền nhân viên cho prod (SEC-05) | bắt buộc | mở | — | tech lead |
| TripPlanner | Endpoint health (hiện chưa có: trạng thái chỉ dựa vào lưu lượng Lambda) | bắt buộc | mở | OPS-12 ghi TripPlanner "chưa có endpoint health" | tech lead |
| TripPlanner | Trang quyền riêng tư và điều khoản bản chính thức (bỏ nhãn "Draft - pending legal review") | bắt buộc | mở | SEC-10 chủ đề 2 | business owner |
| TripPlanner | Project Vercel prod, gói Pro trước khi thu tiền (D-18) | bắt buộc | mở | đang dùng Hobby | tech lead |
| TripPlanner | Business đặt trần chi phí LLM mỗi ngày (TP-01 K-TP-LLMCAP đang dùng mặc định 5 USD) | bắt buộc | mở | TP-01 hằng tuần từ 02/11/2026 | business owner |
| Partner | Endpoint health và readiness trả lời | bắt buộc | xong | bản tin OPS-12 hằng ngày | tech lead |
| Partner | CRM Go-real: dữ liệu đại lý thật chỉ trên prod (AA-980) | bắt buộc | mở | — | tech lead |
| Partner | Điều khoản cổng đối tác có AI Schedule được chấp nhận (SEC-10 chủ đề 12, cần trả lời trước 11/11/2026) | bắt buộc | mở | SEC-10 | business owner |
| Partner | Tài khoản nhà cung cấp của từng đại lý (đại lý tự mang) được ghi lại | nên có | mở | — | tech lead |

## 7. Điểm chặn

| Điểm chặn | Ảnh hưởng | Kế hoạch | Vai trò phụ trách | Ngày |
|---|---|---|---|---|
| Chưa có ngày go-live | Chưa thể bắt đầu 3–4 tuần xây dựng | Business owner đặt ngày hoặc khoảng thời gian | business owner | — |
| ADR 0018 chưa quyết | Nơi đặt prod (acc2 hay tài khoản riêng) đổi root Terraform và mục 3 | Tech lead chấp nhận hoặc bác ADR 0018 | tech lead | trước khi xây |

## 8. Quyết định và ký duyệt

| Quyết định | Phương án | Đề xuất | Người quyết (vai trò) | Ngày | Kết quả |
|---|---|---|---|---|---|
| Ngày go-live | (A) đặt một ngày cách ít nhất 4 tuần; (B) đặt một khoảng thời gian và chọn các ứng dụng đầu tiên | B: một khoảng thời gian cùng các ứng dụng đầu tiên (nhiều khả năng TripPlanner + Booking) | business owner | — | mở |

## Nguồn

ADR 0012 (29/10/2026), ADR 0018 (30/10/2026), `docs/ops/README.md` mục "Prod", `docs/security/baseline.md`, registry báo
cáo `docs/reports/catalog.yaml` (các cổng liên quan của OPS-17), bản tin OPS-12 ngày 30/10/2026, báo cáo sẵn sàng pháp
lý cùng ngày.
