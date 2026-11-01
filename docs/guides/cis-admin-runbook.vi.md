---
id: GUIDE-12-cis-admin
title: Runbook CIS admin
description: Cách nhân sự Adventure Asia vào console CIS admin, mỗi vai trò nhân sự làm được gì, các luồng nội dung hằng ngày từ upload tới Master Content, quản lý nhân sự, tenant và đại lý, và xem ở đâu khi có gì đó sai.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-ai-reports, GUIDE-04, GUIDE-01, OPS-04, AA-1020]
lang: vi
translation_of: docs/guides/cis-admin-runbook.md
---

# Runbook CIS admin

Thuộc bộ [truy cập và vận hành các ứng dụng](app-access-and-operations.vi.md). Đây là bản tiếng Việt của
[cis-admin-runbook.md](cis-admin-runbook.md).

## 1. Ai dùng

Console CIS admin là website nhân sự của hệ thống nội dung. Nhân sự Adventure Asia dùng nó để đưa file tour vào, viết
lại và duyệt tour, giữ danh mục tour (Master Content), và chăm sóc tenant, đại lý đối tác, job và chi phí. Chủ doanh
nghiệp dùng nó để xem toàn bộ nền tảng. Đại lý đối tác không bao giờ dùng trang này.

## 2. Địa chỉ

| Trang | Địa chỉ Dev |
|---|---|
| Console admin | `https://aa-cis.lumiguides.it.com` (mở trang đăng nhập) |
| Trang đăng nhập nhân sự | `https://staff-auth.lumiguides.it.com` (bạn tới đây từ console; không lưu bookmark trang này) |
| Health của API, cho kỹ sư | `https://api-cis.lumiguides.it.com/health` |

## 3. Lấy tài khoản

1. Xin quyền từ một chủ nền tảng (hiện là tech lead), kèm địa chỉ `@adventure.asia` và công việc bạn làm.
2. Chủ nền tảng mở **Platform › People & access › Staff**, chọn **Add staff**, nhập tên và e-mail công việc của bạn,
   chọn **CIS role** và, nếu bạn cũng làm việc trong Booking, chọn **Booking role**.
3. Bạn nhận được e-mail mời. Nếu sau vài phút chưa thấy, chủ nền tảng bấm **Resend invite** trên dòng của bạn.

Chỉ một chủ nền tảng đã đăng nhập bằng e-mail công ty mới thêm được tài khoản, đổi vai trò hoặc vô hiệu hoá tài khoản.
Khi nghỉ việc: chủ nền tảng vô hiệu hoá dòng đó (không bao giờ xoá, để giữ lịch sử).

## 4. Đăng nhập và đăng xuất

1. Mở `https://aa-cis.lumiguides.it.com`.
2. Chọn **Sign in with company email**.
3. Trên trang đăng nhập Adventure Asia, nhập địa chỉ e-mail công việc.
4. Nhập mã dùng một lần trong e-mail. Bạn vào trang đầu tiên mà vai trò của bạn được mở.
5. Để đăng xuất, mở menu tài khoản (chữ cái đầu tên bạn, góc trên bên phải) và chọn **Sign out**. Lần đăng nhập sau
   sẽ hỏi mã mới.

Phiên tự gia hạn khi bạn đang làm việc và kết thúc sau khoảng 12 giờ. Không có mật khẩu.

## 5. Vai trò

| Vai trò | Làm được gì |
|---|---|
| **admin** | Mọi trang, gồm phần Platform (con người, ứng dụng, tenant, đại lý, job, AI và chi phí, báo cáo, tài liệu) và các trang chất lượng đầu ra của tenant. Chủ doanh nghiệp có vai trò này |
| **reviewer** | Việc nội dung: **Upload (S0)**, **Rewrite (S1)**, **Review Queue**, **Master Content**, **AA content (CRM)**, **Supply (Booking)**, **Facts** (chỉ đọc), **Settings** |
| **content** | Các trang nội dung giống reviewer |
| **viewer** | Chỉ đọc, dùng cho các bài kiểm tra tự động; không giao cho người thật |
| **Cờ owner** | Một admin có cờ owner thì quản lý thêm tài khoản nhân sự. Hiện có: tech lead và một tài khoản khẩn cấp bị khoá |

Một số nút cần nhiều quyền hơn bản thân trang: ví dụ sửa **Facts**, publish **AA content (CRM)** và mọi thiết lập
tenant chỉ dành cho admin. Máy chủ kiểm lại vai trò ở mỗi thay đổi.

## 6. Menu

Menu bên trái có hai phần.

- **Platform**: Overview (**Overview**, **Data coverage**, **Reports**); People & access (**Staff**, **Audit log**,
  **Alert recipients**); **Apps**; Tenants (**Tenants**, **Agencies (CRM)**); Jobs (**Jobs**, **Data erasure**);
  AI & spend (**AI providers**, **Cost Operations**, **Cost per app**, **Jev Decisions**); Developer (**API Docs**,
  **Data model**, **Docs**).
- **CIS Content**: Pipeline (**Upload (S0)**, **Rewrite (S1)**, **Review Queue**, **Master Content**); Assets
  (**Photos**, **Places**, **AA content (CRM)**, **Facts**, **Supply (Booking)**); Intelligence (**Social Content**,
  **SEO Intelligence**); Tenant output (**Content Trace**, **A4 Quality**, **Content Quality**, **Writing memory**).

**Settings** nằm ở cuối menu. Giao diện mở bằng tiếng Anh; đổi ngôn ngữ ở thanh trên cùng.

## 7. Việc hằng ngày

### Đưa tour mới vào

1. Mở **Upload (S0)**.
2. Làm theo các bước trên trang: **Select Files** (file Excel tour), **Upload to S3**, **Parse & Review**, **Commit**,
   rồi **Dup Review** cho các tour trông giống tour đã có trong danh mục.
3. Tour mới hiện ở **Tours Ready for Rewrite**. **Trash** bỏ một tour nguồn sai; **Show Trashed** cho phép khôi phục.

### Viết lại tour

1. Mở **Rewrite (S1)**, lọc theo nước hoặc file, và chọn tour.
2. Kiểm **Brand Identity** và **SEO Mode** (Standard, Aggressive hoặc Minimal). Model được đặt ở
   **AI providers › Routing**, không phải ở đây.
3. Chạy và theo dõi từng tour qua Generating content, Validating & scoring, Brand audit và Final check.

> [!WARNING]
> Viết lại tour gọi model AI có trả phí. Bắt đầu với khoảng ba tour, sau đó tối đa khoảng năm mươi. Lượt chạy lớn hơn
> cần chủ doanh nghiệp duyệt kèm giá trước.

### Duyệt và publish

1. Mở **Review Queue** và giữ bộ lọc **Pending**.
2. Mở một tour và đọc bản mới so với bản nguồn. Sửa chữ ngay tại chỗ rồi bấm **Save edits**; trang sẽ yêu cầu kiểm
   lại trước khi duyệt.
3. Chọn **Approve** để publish vào Master Content, **Reject** để không đưa vào, hoặc **Regenerate** để viết lại lần
   nữa (một lời gọi có trả phí).

### Đọc và xuất Master Content

1. Mở **Master Content** và tìm tour.
2. Dùng **+ Add Panel** để so các phiên bản cạnh nhau, **Export Comparison XLSX** hoặc **Export this version as
   DOCX** để chia sẻ một bản.

### Quản lý nhân sự (chỉ chủ nền tảng)

1. **Staff**: thêm, đổi vai trò, vô hiệu hoá hoặc đăng xuất một người. **Open in Booking** mở cùng người đó trong
   Booking admin.
2. **Audit log**: ai đã đổi gì và khi nào.
3. **Alert recipients**: ai nhận e-mail cảnh báo và ngân sách.

### Tenant và đại lý đối tác

1. **Tenants**: **New Tenant**, rồi **Create Tenant**, tạo một thương hiệu đối tác cho Content studio. Mở một tenant
   để xem các tab (Tours, Pipeline, Activity, API Usage, Brand, Social Content, Usage & Billing, Cost, Quality,
   Markets, Audit, Settings). Mời thành viên tenant chưa có nút: xem
   [runbook Content studio](content-studio-runbook.vi.md), mục 3.
2. **Agencies (CRM)**: các đại lý đối tác của CRM. **Create agency**, **Invite first owner**, **Lock** và **Unlock**
   cần nhóm nhân sự CRM platform-admin và một mã ticket; các admin khác xem được danh sách và mức sử dụng. Chi tiết:
   [runbook CRM](crm-runbook.vi.md), mục 3.

### Một người yêu cầu xoá dữ liệu của họ

1. Mở **Data erasure**. Chạy DRY RUN trước và đọc những gì sẽ bị xoá.
2. Chỉ apply sau khi đã kiểm, theo [runbook yêu cầu dữ liệu và xoá dữ liệu](../legal/dsar-erasure-runbook.md). Chỉ
   phần CIS có nút; các ứng dụng khác làm tay theo runbook đó.

### Theo dõi nền tảng

- **Overview**: một màn hình cho trạng thái hệ thống. **Data coverage**: số tour đếm từ lúc upload tới TripPlanner,
  Booking và CRM.
- **Apps**: từng ứng dụng có chạy không, đang chạy commit nào (**Same commit** hay **Mismatch**), và **Deploy gate**
  (**Safe to deploy** hay **Deploy waits**).
- **Jobs**: việc chạy nền, đang chờ, đang chạy và lỗi, mỗi job có một ngăn chi tiết.
- Chi phí và báo cáo: xem [runbook nhà cung cấp AI và báo cáo](ai-providers-and-reports-runbook.vi.md).

## 8. Khi có gì đó sai

| Bạn thấy | Xem ở | Sau đó |
|---|---|---|
| Chấm đỏ trên chuông (thanh trên cùng) | Danh sách chuông: các thông báo mới nhất | Mở trang mà thông báo nêu |
| Một trang báo lỗi hoặc trống | **Apps**: CIS có chạy không, commit của API và worker có giống nhau không? | Chụp màn hình và gửi kèm thời điểm |
| Viết lại hoặc duyệt không tiến triển | **Jobs** (job lỗi) và **AI providers** (một nhà cung cấp không OK) | Nếu một nhà cung cấp từ chối lời gọi, báo kỹ sư trực; các job bị từ chối được đưa lại vào hàng đợi khi nhà cung cấp trả lời lại |
| Mã đăng nhập không tới hoặc trang mã từ chối bạn | Thư mục spam; chờ hai phút rồi xin mã mới | Vẫn lỗi: kỹ sư trực làm theo [playbook đăng nhập nhân sự](../ops/playbooks/cognito-login.md) |
| Một e-mail cảnh báo | Tên cảnh báo trong tiêu đề | Chuyển cho kỹ sư trực nếu nó vẫn ở trạng thái ALARM |

Trong giai đoạn dev, tech lead là kỹ sư trực. Lỗi thông thường gửi qua Jira; lỗi khẩn nhắn trực tiếp.

## 9. Lưu ý giai đoạn Dev

- Chỉ có dữ liệu thử. Tour, tenant và đại lý trên Dev là để thử nghiệm.
- Tài khoản model chính từ chối model chat từ 29/10/2026, nên **Rewrite (S1)**, **Regenerate** và các bước kiểm tra
  bằng AI sẽ lỗi hoặc chờ cho tới khi có lại đường gọi model. Các job bị từ chối được đưa lại vào hàng đợi từ
  **AI providers** khi nhà cung cấp trả lời lại.
- Địa chỉ `aa-cis-preview.lumiguides.it.com` là bản sao thử của console dành cho kỹ sư, chỉ đọc với nhân sự.

## Nguồn (cho người bảo trì)

Đọc từ AA-CIS-App `main` ngày 01/11/2026: `frontend/app/_kit/adminNav.tsx` (menu), `frontend/lib/rbac.ts` (vai trò),
`frontend/app/login/page.tsx`, các file `messages.ts` của `admin/platform/staff`, `upload`, `s1-rewrite`, `review`,
`master-content`, `platform/apps`, `tenants`, `platform/agencies`, `_kit/Topbar.tsx` (chuông), và `CONTEXT.md`
("Staff roles and permissions"). Thiết kế đăng nhập: ADR gốc 0006 và 0006a. Giữ trang này khớp với
[cis-admin-runbook.md](cis-admin-runbook.md).
