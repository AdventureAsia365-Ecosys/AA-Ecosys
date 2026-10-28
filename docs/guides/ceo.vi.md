---
id: GUIDE-04
title: Hướng dẫn cho CEO
description: Hướng dẫn cho chủ doanh nghiệp (CEO) - bốn ứng dụng làm gì cho công ty, đăng nhập ở đâu, xem gì, đọc chi phí thế nào, quyết định nào thuộc về chủ doanh nghiệp và cách báo lỗi.
type: tutorial
status: draft
owner: nghiep
audience: [owner]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
related: [CAT-00, GUIDE-03, OPS-04, FIN-01, FIN-02, AA-897, AA-855]
lang: vi
translation_of: docs/guides/ceo.md
---

# Hướng dẫn cho CEO

Cách cả hệ thống được xây, vận hành và tính chi phí: [engineering handbook](../engineering-handbook.md). Đây là bản
tiếng Việt của [ceo.md](ceo.md).

## 1. Dành cho ai

Tài liệu này dành cho chủ doanh nghiệp, CEO của Adventure Asia, và không cần kiến thức kỹ thuật. Đọc xong, bạn sẽ
biết mỗi ứng dụng làm gì cho công ty, đăng nhập ở đâu, nên xem trang nào, đọc chi phí hằng tháng thế nào và những
quyết định nào đang chờ bạn. Tech lead cập nhật trang này; bản PDF được đặt trên Google Drive.

## 2. Bốn ứng dụng

| Ứng dụng | Làm gì cho công ty | Ai dùng |
|---|---|---|
| **CIS** (hệ thống nội dung) | Biến file tour của mình thành nội dung tour sạch, đã kiểm tra; giữ danh mục tour; viết nội dung cho thương hiệu đối tác (tenant). | Nhân viên Adventure Asia (trang quản trị) |
| **TripPlanner** | Trang web để khách du lịch xem điểm đến, ghép chuyến đi và gửi yêu cầu cho tư vấn viên. | Khách du lịch |
| **Booking** | Nơi nhân viên xử lý từng yêu cầu của khách: hồ sơ khách, hồ sơ chuyến đi, đề xuất, giá, nhà cung cấp. | Nhân viên kinh doanh và hợp đồng của Adventure Asia |
| **Partner** (ứng dụng cho đại lý) | Ứng dụng mình cung cấp cho đại lý du lịch đối tác: một CRM để họ quản lý khách của mình, có sẵn tour của mình bên trong. Từ 25/10/2026 ứng dụng này cũng chứa cổng tenant (Content studio), nơi đối tác quản lý nội dung thương hiệu. | Đại lý đối tác |

Bốn ứng dụng dùng chung một tài khoản AWS và một cơ sở dữ liệu, mỗi phần có một chủ rõ ràng. Chỉ CIS được tạo hoặc
sửa nội dung tour; các ứng dụng còn lại chỉ đọc.

## 3. Đăng nhập ở đâu

| Trang | Địa chỉ | Cách đăng nhập |
|---|---|---|
| **Trang quản trị CIS** (trang chính của bạn) | `https://aa-cis.lumiguides.it.com` | Bấm **Sign in with company email**, nhập địa chỉ email công ty của bạn, rồi nhập mã dùng một lần gửi vào hộp thư. Trang nhập mã là `staff-auth.lumiguides.it.com`, có logo Adventure Asia. |
| Trang quản trị Booking | `https://booking.lumiguides.it.com` | Cùng cách nhập mã qua email công ty, chỉ khi bạn có vai trò Booking. Cần vai trò này thì báo tech lead. |
| Ứng dụng Partner và cổng tenant | `https://portal.lumiguides.it.com` | Chỉ dành cho **đại lý đối tác**, đăng nhập riêng. Nhân viên không dùng. |
| TripPlanner | `https://tripplanner.lumiguides.it.com` | Trang công khai cho khách (bản Dev). Không cần đăng nhập để ghép chuyến đi. |

Vai trò của bạn trên CIS là **admin**: bạn xem được mọi trang. Việc đổi quyền người khác (trang Staff) chỉ dành cho
các tài khoản owner của CIS: tech lead và một tài khoản khẩn cấp luôn khoá sẵn.

> [!NOTE]
> Ngày 18/10/2026 bên mình đã đề nghị Google xem lại cảnh báo "trang nguy hiểm" bị gắn nhầm cho `lumiguides.it.com`.
> Nếu trình duyệt hiện trang cảnh báo màu đỏ, hãy báo tech lead; đừng bấm bỏ qua trên máy dùng chung.

## 4. Bạn xem và làm được gì

Trang quản trị có hai khu ở menu bên trái.

**Platform** (toàn công ty):

- **Overview** - một màn hình tóm tắt tình trạng hệ thống; **Data coverage** - số đếm trực tiếp của tour, từ lúc tải
  lên tới TripPlanner, Booking và CRM.
- **People & access** - **Staff** (ai có quyền vào và với vai trò gì), **Audit log** (ai làm gì, lúc nào; nhật ký
  cho thấy nếu một dòng bị sửa về sau), **Alert recipients** (ai nhận email cảnh báo và email ngân sách).
- **Apps** - từng ứng dụng có chạy không, đang chạy phiên bản nào, lúc này cập nhật có an toàn không.
- **Tenants** và **Agencies (CRM)** - thương hiệu đối tác và đại lý đối tác.
- **Jobs** (việc chạy nền đang làm) và **Data erasure** (xoá dữ liệu của một người hay một đối tác khi có yêu cầu).
- **AI & spend** - **Cost Operations**, **Cost per app** (mục 5) và **Jev Decisions** (các lần kiểm tra nội dung tự động).
- **Developer** - API Docs, Data model và **Docs**, nơi chứa tài liệu của công ty, kể cả hướng dẫn này.

**CIS Content** (công việc tour): Upload, Rewrite, Review Queue, Master Content; Photos, Places, AA content (CRM),
Supply (Booking); Social Content, SEO Intelligence; Content Trace, A4 Quality, Content Quality, Writing memory.

Bạn xem mọi trang đều an toàn. Các nút làm thay đổi dữ liệu (duyệt, tạo lại, lấy số mới từ AWS) sẽ chạy thật; khi
chưa chắc, hãy hỏi tech lead trước.

## 5. Đọc chi phí

- **Cost per app** (Platform → AI & spend): chọn tháng. Bốn ô hiện tổng, hoá đơn AWS, chi phí mô hình AI và chi phí
  AWS "chưa gắn nhãn" (chưa gán cho ứng dụng nào). Bảng chia tiền theo ứng dụng: CIS, Booking, TripPlanner và
  Partner CRM, cộng thêm "shared" (cơ sở dữ liệu và mạng mà mọi ứng dụng dùng chung) và "identity" (đăng nhập của
  nhân viên).
- **Cost Operations**: nền tảng chi bao nhiêu cho mô hình AI, DataForSEO, Jev và hoá đơn AWS, so với ngân sách; số
  mình tự ghi đặt cạnh hoá đơn thật.
- Nút **Refresh from AWS** hỏi Amazon số mới, tốn khoảng 0,04 USD mỗi lần bấm. Trang đã tự cập nhật khoảng một lần
  mỗi ngày, nên hiếm khi cần bấm.
- **Ngân sách có cảnh báo email** trên tài khoản AWS chính, gửi tới danh sách người nhận cảnh báo: tổng 300 USD/tháng
  (nâng từ 250 ngày 28/10/2026), chia CIS 90, shared 120, Partner CRM 35, Booking 25, đăng nhập nhân viên 10,
  TripPlanner 10.
- **Báo cáo chi phí và năng lực hằng tháng**: từ tháng 11/2026, trong phiên làm việc đầu mỗi tháng, tech lead gửi bạn
  một bản tóm tắt ngắn: tổng theo ứng dụng, năm khoản lớn nhất, chênh lệch so với tháng trước kèm lý do, và con số
  "chi phí cho mỗi tour được xuất bản".
- **Dịch vụ trả phí mới**: không bật thứ gì tốn tiền mà chưa báo giá và chưa được duyệt.

## 6. Những quyết định cần bạn

| Chủ đề | Bên mình đưa bạn | Hiện nay |
|---|---|---|
| Pháp lý và điều khoản | Đề xuất bình tĩnh, có các phương án; có cần luật sư hay không là bạn quyết | Điều khoản tenant về nội dung do AI viết, cần trả lời trước 11/11/2026 |
| Giá và ưu đãi | Đề xuất quy tắc giá và biên lợi nhuận cho Booking | Bộ tính giá Booking đã xong; quy tắc kinh doanh do bạn quyết |
| Tenant (đối tác) | Ai được làm tenant, gói nào, khi nào | Chưa có tenant trả tiền |
| Các lần chạy AI lớn | Mọi đợt chạy AI vượt mức thử nhỏ (khoảng 50 tour) | Hỏi từng lần, kèm giá |
| Ngày chạy thật | Khi nào Dev thành dịch vụ thật (prod), kèm checklist và chi phí | Chưa chốt ngày |
| Nhà cung cấp | Công cụ trả phí mới hoặc nâng gói, ví dụ Vercel Pro khi có tenant trả tiền đầu tiên | Hiện dùng gói miễn phí |
| Yêu cầu về dữ liệu khách | Khách muốn xem hoặc xoá dữ liệu của mình; có luật sư nếu cần | Làm từng bước theo quy trình xoá dữ liệu; chỉ phần CIS có nút bấm |
| Sự cố liên quan dữ liệu cá nhân | Có thông báo cho người bị ảnh hưởng không, và thông báo thế nào | Chỉ khi xảy ra |

## 7. Báo lỗi

1. **Yêu cầu và lỗi thông thường**: tạo hoặc bình luận trên Jira trong các project bạn đang dùng (PR, KAN, CON).
   Tech lead trả lời ở đó sau khi kiểm tra; câu trả lời được duyệt trước khi đăng.
2. **Gấp** (ứng dụng ngừng chạy, hiện sai dữ liệu, đối tác phàn nàn): nhắn tech lead qua Zalo.
3. Gửi kèm: địa chỉ trang, ảnh chụp màn hình, thời điểm, bạn mong đợi gì và thực tế thấy gì.

Nếu có sự cố nghiêm trọng (sản phẩm ngừng với mọi người, dữ liệu bị lộ hoặc mất), tech lead báo bạn trong vòng
30 phút và cập nhật cho tới khi xử lý xong.

## 8. Dev và prod hiện nay

- **Dev** là môi trường duy nhất hiện nay, dùng để xây và thử. Dev chỉ chứa **dữ liệu thử**: không có khách thật.
  Giao diện có thể đổi nhanh và dữ liệu thử có thể bị làm mới.
- **Prod** (môi trường thật) sẽ là dịch vụ thật cho khách và đối tác, dùng một cơ sở dữ liệu riêng trên cùng tài khoản
  AWS. Prod bắt đầu khi bạn chốt ngày chạy thật. Trước ngày đó bên mình hoàn tất một checklist: thay mới khoá bảo
  mật, thử sao lưu và khôi phục, có cảnh báo và mục tiêu phản hồi.
- Nghiệm thu (UAT) sẽ được quay thành video ngắn cho mọi ứng dụng khi phần kỹ thuật xong.

## 9. Giữ an toàn tài khoản

- Bạn đăng nhập bằng mã dùng một lần gửi vào email công ty. Không có mật khẩu phải nhớ.
- **Không bao giờ đưa mã** cho bất kỳ ai, kể cả tech lead. Không ai trong nhóm sẽ hỏi mã của bạn.
- Nhận được mã mà bạn không yêu cầu nghĩa là có người gõ địa chỉ email của bạn: bỏ qua và báo tech lead.
- Đăng xuất khi dùng máy tính chung hoặc máy công cộng.
- Mất quyền vào email? Báo tech lead; một tài khoản owner của CIS có thể tạm khoá và mở lại quyền CIS cho bạn.
- Nhật ký bảo mật (đăng nhập, truy cập mạng) được giữ 365 ngày; nhật ký ứng dụng giữ 30 ngày.

## 10. Mười lăm thuật ngữ chính

| Thuật ngữ | Tiếng Việt | Nghĩa |
|---|---|---|
| Tenant | Tenant (đối tác dùng nền tảng) | Thương hiệu đối tác dùng nền tảng nội dung của mình. |
| Tenant portal | Cổng tenant | Khu vực web riêng của đối tác. |
| Admin console | Trang quản trị | Trang web nội bộ của CIS cho nhân viên. |
| Master Content | Nội dung gốc | Bản tour đã kiểm tra, dùng chung cho mọi tenant. |
| Atom | Atom (mẩu nội dung) | Một mẩu nội dung tour nhỏ, dùng lại được. |
| Trip case | Hồ sơ chuyến đi | Một yêu cầu của khách được xử lý trong Booking. |
| Proposal | Đề xuất | Phương án nhân viên gửi cho khách. |
| Dev | Môi trường Dev | Môi trường xây và thử, chỉ có dữ liệu thử. |
| Prod | Môi trường thật | Dịch vụ chạy thật sau này. |
| Deploy | Triển khai | Đưa phiên bản mới lên máy chủ. |
| Release | Phát hành | Người dùng bắt đầu thấy tính năng. |
| Incident | Sự cố | Lỗi làm ảnh hưởng người dùng. |
| Budget alert | Cảnh báo ngân sách | Email khi chi phí gần chạm mức tháng. |
| Personal data (PII) | Dữ liệu cá nhân | Dữ liệu nhận diện được một người. |
| UAT | Nghiệm thu | Kiểm tra chấp nhận của phía kinh doanh trước khi chạy thật. |

Bảng thuật ngữ đầy đủ: [bảng thuật ngữ](../glossary.vi.md).

## Nguồn (cho người duy trì trang)

Giữ trang này khớp với: ADR 0006a về đăng nhập nhân viên; menu trang quản trị CIS (`AA-CIS-App`
`frontend/app/_kit/adminNav.tsx`, đọc ngày 28/10/2026); Cost per app AA-884 (`api/core/app_registry.py`,
`api/services/platform_cost.py`), báo cáo hằng tháng AA-896 cùng AA-838; ngân sách trong Infra
`accounts/aa365/variables.tf` và `observability.tf` (đọc trực tiếp ngày 28/10/2026); pháp lý AA-820, AA-886; Dev chỉ
có dữ liệu thử D-01; prod ADR 0001 / C7.2a / D-17 / AA-880; gói Vercel D-18; yêu cầu dữ liệu D-11 và
[quy trình yêu cầu và xoá dữ liệu](../legal/dsar-erasure-runbook.md); thời gian giữ log D-09 / AA-872; trách nhiệm khi
có sự cố: [xử lý sự cố](../ops/incident-response.md); video UAT AA-855; đề nghị Google xem lại cảnh báo AA-816. Bản
tiếng Anh [ceo.md](ceo.md) là bản gốc; sửa bản đó trước rồi cập nhật trang này.
