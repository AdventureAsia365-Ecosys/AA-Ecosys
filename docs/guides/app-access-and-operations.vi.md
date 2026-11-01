---
id: GUIDE-12
title: Truy cập và vận hành các ứng dụng
description: Mục lục các runbook theo ứng dụng - với mỗi ứng dụng, ai dùng, địa chỉ Dev, cách đăng nhập và ai quản lý tài khoản; bắt đầu từ đây để vào một ứng dụng hoặc vận hành nó hằng ngày.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer, devops]
applies_to: [ecosystem]
last_reviewed: 2026-11-01
review_every_days: 90
related: [CAT-00, GUIDE-04, GUIDE-01, GUIDE-05, OPS-04, AA-1020]
lang: vi
translation_of: docs/guides/app-access-and-operations.md
---

# Truy cập và vận hành các ứng dụng

Trang này là điểm vào của các runbook ứng dụng: mỗi ứng dụng một trang, nói rõ **cách vào** và **cách vận hành hằng
ngày**. Các trang được viết cho chủ doanh nghiệp, nhân sự Adventure Asia và những người ở đại lý đối tác hướng dẫn
đồng nghiệp của mình. Đây là bản tiếng Việt của [app-access-and-operations.md](app-access-and-operations.md).

Mỗi ứng dụng làm gì cho công ty có trong [hướng dẫn cho CEO](ceo.vi.md). Quyền truy cập dành cho kỹ sư (AWS, GitHub,
Vercel) nằm ở [onboarding](../onboarding.md); trang này chỉ nói về bản thân các ứng dụng.

## Các ứng dụng

| Ứng dụng | Người dùng | Địa chỉ Dev | Cách đăng nhập | Ai quản lý tài khoản | Runbook |
|---|---|---|---|---|---|
| **CIS admin** (hệ thống nội dung) | Nhân sự Adventure Asia và chủ doanh nghiệp | `https://aa-cis.lumiguides.it.com` | E-mail công ty và mã dùng một lần (đăng nhập nhân sự) | Một chủ nền tảng thêm tài khoản ở trang **Staff** (hiện là tech lead) | [Runbook CIS admin](cis-admin-runbook.vi.md) |
| **Content studio** (cổng tenant) | Thương hiệu đối tác mua nội dung (thành viên tenant: owner, editor, viewer) | `https://portal.lumiguides.it.com/portal/dashboard` | E-mail, mật khẩu và ứng dụng xác thực (đăng nhập đối tác) | Nhân sự Adventure Asia tạo tenant và gửi lời mời; owner của tenant quản lý việc dùng hằng ngày | [Runbook Content studio](content-studio-runbook.vi.md) |
| **CRM cho đại lý** (AA Partner) | Đại lý đối tác (owner, agent, assistant); khách du lịch của họ qua đường link; nhân sự hỗ trợ và điều hành mặt đất của Adventure Asia | `https://portal.lumiguides.it.com` (ứng dụng đại lý), `https://go-dev.lumiguides.it.com` (trang cho khách du lịch), `/staff` trên host đại lý (console nhân sự AA) | Đại lý: e-mail, mật khẩu và ứng dụng xác thực. Nhân sự AA: e-mail công ty và mã dùng một lần | Adventure Asia tạo đại lý và mời owner đầu tiên; owner của đại lý mời các thành viên | [Runbook CRM](crm-runbook.vi.md) |
| **Booking admin** | Nhân sự kinh doanh, hợp đồng và nội dung của Adventure Asia | `https://booking.lumiguides.it.com` | E-mail công ty và mã dùng một lần (cùng tài khoản nhân sự với CIS) | Một chủ nền tảng đặt vai trò Booking ở trang **Staff** của CIS | [Runbook Booking admin](booking-admin-runbook.vi.md) |
| **TripPlanner** | Khách du lịch, ở dạng khách vãng lai hoặc đã đăng nhập | `https://tripplanner.lumiguides.it.com` | Không cần để lên kế hoạch chuyến đi; e-mail và mã dùng một lần cho My trips | Khách du lịch tự tạo tài khoản ở lần đăng nhập đầu tiên | [Runbook TripPlanner](tripplanner-runbook.vi.md) |

Trong CIS admin, có hai khu vực có runbook riêng vì chủ doanh nghiệp xem thường xuyên:
[nhà cung cấp AI và báo cáo](ai-providers-and-reports-runbook.vi.md) (chi phí AI và dữ liệu, tình trạng các model, sổ
đăng ký báo cáo).

## Ba kiểu đăng nhập

| Kiểu đăng nhập | Ai | Cần gì | Mã hoặc mật khẩu đến từ đâu |
|---|---|---|---|
| **Đăng nhập nhân sự** | Nhân sự Adventure Asia trong CIS admin, Booking admin và console nhân sự của CRM | Một địa chỉ `@adventure.asia` do chủ nền tảng thêm vào | Mã dùng một lần gửi tới e-mail của bạn; trang đăng nhập là `staff-auth.lumiguides.it.com` có logo Adventure Asia. Không có mật khẩu |
| **Đăng nhập đối tác** | Người ở đại lý đối tác và tenant (CRM và Content studio dùng chung một tài khoản và một host) | Một e-mail mời | Bạn tự chọn mật khẩu ở lần đăng nhập đầu và cài ứng dụng xác thực; luôn bắt buộc đăng nhập hai bước |
| **Đăng nhập khách du lịch** | Khách du lịch trên TripPlanner | Bất kỳ địa chỉ e-mail nào | Mã dùng một lần gửi tới e-mail; tài khoản được tạo ở lần đăng nhập đầu. Khách của đại lý đối tác không bao giờ đăng nhập: họ dùng đường link đại lý gửi |

Không bao giờ chia sẻ mã dùng một lần, mật khẩu hay mã của ứng dụng xác thực với bất kỳ ai, kể cả tech lead.

## Khi có gì đó sai

1. Xem dấu hiệu sức khoẻ của chính ứng dụng trước (mỗi runbook có nêu: chuông thông báo, trang **Apps**, trang
   **Jobs**, trang health của CRM).
2. E-mail cảnh báo được gửi tới những người ở CIS admin **Platform › Alert recipients**, khi ALARM và lần nữa khi OK.
3. Lỗi thông thường: tạo một issue Jira trong các project bạn vẫn dùng. Lỗi khẩn (một ứng dụng sập, dữ liệu sai đang
   hiển thị, một đối tác phàn nàn): nhắn ngay cho kỹ sư trực. Trong giai đoạn dev, tech lead là kỹ sư trực cho mọi
   ứng dụng.
4. Luôn gửi kèm địa chỉ trang, thời điểm, ảnh chụp màn hình, điều bạn mong đợi và điều bạn thấy.

Cách xử lý sự cố và ai được báo: [ứng phó sự cố](../ops/incident-response.md).

## Giai đoạn Dev hiện nay

- **Dev là môi trường duy nhất.** Chỉ chứa dữ liệu thử: đại lý giả lập, khách du lịch và tenant được tạo ra, không có
  khách hàng thật. Dữ liệu có thể bị đặt lại.
- **Các lời gọi model bị hạn chế.** Tài khoản model chat chính từ chối lời gọi từ 29/10/2026, nên việc viết và kiểm
  tra bằng AI cần model chat sẽ phải chờ hoặc lỗi trên Dev cho tới khi có lại đường gọi model
  ([postmortem](../ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md)). Embedding cho tìm kiếm vẫn chạy. CRM
  dùng một bộ thay thế dựng sẵn thay cho model thật, và SMS, WhatsApp của CRM dùng nhà cung cấp sandbox.
- **Địa chỉ sẽ đổi khi go-live.** Các host `lumiguides.it.com` là host Dev. Địa chỉ production được chốt khi có ngày
  go-live.
- Các runbook này được viết từ mã nguồn và kiểm trên Dev bằng cách mở từng địa chỉ ngày 01/11/2026. Việc nhân sự đi
  thử từng bước vẫn chưa làm; hãy báo lại mọi bước không khớp với màn hình.
