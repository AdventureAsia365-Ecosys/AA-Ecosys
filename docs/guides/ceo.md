---
id: GUIDE-04
title: CEO guide (English and Tiếng Việt)
description: Bilingual guide for Ms. Thư - what the three apps do for the business, where to sign in, what to look at, how to read cost, which decisions are hers and how to report a problem.
type: tutorial
status: draft
owner: nghiep
audience: [owner]
applies_to: [ecosystem]
last_reviewed: 2026-10-23
review_every_days: 90
related: [CAT-00, GUIDE-03, OPS-04, FIN-01, FIN-02, AA-897, AA-855]
---

# CEO guide (English and Tiếng Việt)

How the whole delivery system works / Cách cả hệ thống được xây, vận hành và tính chi phí: [engineering handbook](../engineering-handbook.md).

Each section is written in English first, then the same content in Vietnamese.
Mỗi mục viết tiếng Anh trước, sau đó là cùng nội dung bằng tiếng Việt.

## 1. Who this is for / Dành cho ai

This guide is for Ms. Thư, CEO of Adventure Asia. It needs no technical background. After reading it you will know
what each app does for the business, where to sign in, which pages to look at, how to read the monthly cost and
which decisions wait for you. Nghiệp keeps this page up to date; a PDF copy is placed on Google Drive.

### Tiếng Việt

Tài liệu này dành cho chị Thư, CEO của Adventure Asia, không cần kiến thức kỹ thuật. Đọc xong chị sẽ biết mỗi ứng
dụng làm gì cho công ty, đăng nhập ở đâu, nên xem trang nào, đọc chi phí hằng tháng thế nào và những quyết định nào
cần chị. Nghiệp cập nhật trang này; bản PDF được đặt trên Google Drive.

## 2. The three apps / Ba ứng dụng

| App | What it does for the business | Who uses it |
|---|---|---|
| **CIS** (Content system) | Turns our tour files into clean, checked tour content, keeps the tour catalog, and writes content for partner brands (tenants). | Adventure Asia staff (admin console), partners (tenant portal) |
| **TripPlanner** | The website where a traveller explores places, builds a trip and sends a request to an advisor. | Travellers |
| **Booking** | Where staff handle each traveller request: customer, trip case, proposal, price, suppliers. | Adventure Asia sales and contracting staff |

The three apps share one AWS account and one database, with a clear owner for each part. Only CIS creates or
changes tour content; the other two read it.

### Tiếng Việt

| Ứng dụng | Làm gì cho công ty | Ai dùng |
|---|---|---|
| **CIS** (hệ thống nội dung) | Biến file tour của mình thành nội dung tour sạch, đã kiểm tra; giữ danh mục tour; viết nội dung cho thương hiệu đối tác (tenant). | Nhân viên Adventure Asia (trang quản trị), đối tác (cổng tenant) |
| **TripPlanner** | Trang web để khách du lịch xem điểm đến, ghép chuyến đi và gửi yêu cầu cho tư vấn viên. | Khách du lịch |
| **Booking** | Nơi nhân viên xử lý từng yêu cầu của khách: hồ sơ khách, hồ sơ chuyến đi, đề xuất, giá, nhà cung cấp. | Nhân viên kinh doanh và hợp đồng của Adventure Asia |

Ba ứng dụng dùng chung một tài khoản AWS và một cơ sở dữ liệu, mỗi phần có một chủ rõ ràng. Chỉ CIS được tạo hoặc
sửa nội dung tour; hai ứng dụng còn lại chỉ đọc.

## 3. Where to sign in / Đăng nhập ở đâu

| Page | Address | How you sign in |
|---|---|---|
| **CIS admin console** (your main page) | `https://aa-cis.lumiguides.it.com` | Click **Sign in with company email**, type `thu@adventure.asia`, then type the one-time code sent to your inbox. The code page is `staff-auth.lumiguides.it.com` with the Adventure Asia logo. |
| Booking admin | `https://booking.lumiguides.it.com` | Same company e-mail code, only if you have a Booking role. Today your account has no Booking role; ask Nghiệp if you want one. |
| Tenant portal | `https://portal.lumiguides.it.com` | For **partners** only, with their own login. Staff do not use it. |
| TripPlanner | `https://tripplanner.lumiguides.it.com` | Public traveller site (Dev version). No sign-in. |

Your CIS role is **admin**: you can see every page. Changing who has access (the Staff page) is reserved for owners:
Nghiệp and one locked emergency account.

> [!NOTE]
> On 18/10/2026 we asked Google to review a false "dangerous site" warning on `lumiguides.it.com`. If your browser
> shows a red warning page before the review ends, tell Nghiệp; do not click through on a shared computer.

### Tiếng Việt

| Trang | Địa chỉ | Cách đăng nhập |
|---|---|---|
| **Trang quản trị CIS** (trang chính của chị) | `https://aa-cis.lumiguides.it.com` | Bấm **Sign in with company email**, nhập `thu@adventure.asia`, rồi nhập mã dùng một lần gửi vào hộp thư. Trang nhập mã là `staff-auth.lumiguides.it.com`, có logo Adventure Asia. |
| Trang quản trị Booking | `https://booking.lumiguides.it.com` | Cùng cách nhập mã qua email công ty, chỉ khi chị có vai trò Booking. Hiện tài khoản của chị chưa có vai trò Booking; chị cần thì báo Nghiệp. |
| Cổng tenant | `https://portal.lumiguides.it.com` | Chỉ dành cho **đối tác**, đăng nhập riêng. Nhân viên không dùng. |
| TripPlanner | `https://tripplanner.lumiguides.it.com` | Trang công khai cho khách (bản Dev). Không cần đăng nhập. |

Vai trò của chị trên CIS là **admin**: chị xem được mọi trang. Việc đổi quyền người khác (trang Staff) chỉ dành cho
owner: Nghiệp và một tài khoản khẩn cấp luôn khoá sẵn.

> [!NOTE]
> Ngày 18/10/2026 bên mình đã đề nghị Google xem lại cảnh báo "trang nguy hiểm" bị gắn nhầm cho `lumiguides.it.com`.
> Nếu trình duyệt hiện trang cảnh báo màu đỏ trước khi Google xem xong, chị báo Nghiệp; đừng bấm bỏ qua trên máy dùng chung.

## 4. What you can see and do / Chị xem và làm được gì

The console has two areas in the left menu.

**Platform** (the whole company):

- **Overview** - one screen with the state of the system. A clearer operations overview is being designed and will be
  shown to you first.
- **Staff** - who has access and with which role. **Audit log** - who did what and when; the log shows if a
  record was changed afterwards.
- **Apps** - is each app up, which version runs, is it safe to update now.
- **Tenants**, **Jobs** (background work in progress).
- **External Spend** and **Cost per app** - money (section 5). **Jev Decisions** - automatic content checks.

**CIS Content** (the tour work): Upload, Rewrite, Review Queue, Master Content, Photos, Social Content, SEO
Intelligence, Content Trace, A4 Quality, Content Quality.

You can look at everything safely. Buttons that change data (approve, regenerate, refresh from AWS) do real work;
when unsure, ask Nghiệp first.

### Tiếng Việt

Trang quản trị có hai khu ở menu bên trái.

**Platform** (toàn công ty):

- **Overview** - một màn hình tóm tắt tình trạng hệ thống. Một bản tổng quan vận hành rõ hơn đang được thiết kế và sẽ
  đưa chị xem trước.
- **Staff** - ai có quyền vào và với vai trò gì. **Audit log** - ai làm gì, lúc nào; nhật ký cho thấy nếu một dòng
  bị sửa về sau.
- **Apps** - từng ứng dụng có chạy không, đang chạy phiên bản nào, lúc này cập nhật có an toàn không.
- **Tenants**, **Jobs** (việc chạy nền đang làm).
- **External Spend** và **Cost per app** - chi phí (mục 5). **Jev Decisions** - các lần kiểm tra nội dung tự động.

**CIS Content** (công việc tour): Upload, Rewrite, Review Queue, Master Content, Photos, Social Content, SEO
Intelligence, Content Trace, A4 Quality, Content Quality.

Chị xem mọi trang đều an toàn. Các nút làm thay đổi dữ liệu (duyệt, tạo lại, lấy số mới từ AWS) sẽ chạy thật; khi
chưa chắc, chị hỏi Nghiệp trước.

## 5. Reading the cost / Đọc chi phí

- **Cost per app** (Platform → AI & spend): pick a month. Four boxes show the total, the AWS bill, AI model spend and
  "untagged" AWS cost (not yet assigned to an app). The table splits the money by app: CIS, Booking, TripPlanner and
  "shared" (the database and network all apps use).
- **External Spend**: AI and data-provider spend, our own estimate next to the real bill.
- **Refresh from AWS** asks Amazon for new numbers and costs about 0.04 USD per click. The page already refreshes by
  itself about once a day, so the button is rarely needed.
- **Budgets with e-mail alerts** (to Nghiệp) on the main AWS account: 250 USD per month in total, split CIS 90,
  shared 100, Booking 25, TripPlanner 10, CRM 25.
- **Monthly cost and capacity report**: from November 2026, in the first working session of each month, Nghiệp sends
  you a short Vietnamese summary: total by app, the five biggest items, change from last month with reasons, and a
  "cost per published tour" figure.
- **New paid services**: nothing new that costs money is switched on without a price quote and approval first.

### Tiếng Việt

- **Cost per app** (Platform → AI & spend): chọn tháng. Bốn ô hiện tổng, hoá đơn AWS, chi phí mô hình AI và chi phí
  AWS "chưa gắn nhãn" (chưa gán cho ứng dụng nào). Bảng chia tiền theo ứng dụng: CIS, Booking, TripPlanner và "shared"
  (cơ sở dữ liệu và mạng mà mọi ứng dụng dùng chung).
- **External Spend**: chi phí AI và nhà cung cấp dữ liệu, số mình tự ước tính đặt cạnh hoá đơn thật.
- Nút **Refresh from AWS** hỏi Amazon số mới, tốn khoảng 0,04 USD mỗi lần bấm. Trang đã tự cập nhật khoảng một lần
  mỗi ngày, nên hiếm khi cần bấm.
- **Ngân sách có cảnh báo email** (gửi Nghiệp) trên tài khoản AWS chính: tổng 250 USD/tháng, chia CIS 90, shared 100,
  Booking 25, TripPlanner 10, CRM 25.
- **Báo cáo chi phí và năng lực hằng tháng**: từ tháng 11/2026, trong phiên làm việc đầu mỗi tháng, Nghiệp gửi chị một
  bản tóm tắt tiếng Việt: tổng theo ứng dụng, năm khoản lớn nhất, chênh lệch so với tháng trước kèm lý do, và con số
  "chi phí cho mỗi tour được xuất bản".
- **Dịch vụ trả phí mới**: không bật thứ gì tốn tiền mà chưa báo giá và chưa được duyệt.

## 6. Decisions that need you / Những quyết định cần chị

| Topic | What we bring you | Today |
|---|---|---|
| Legal and terms | A calm proposal with options; whether a lawyer is needed is your call | Tenant terms clause on AI-written content, answer wanted by 11/11/2026 |
| Pricing and offers | Pricing rules and margins proposed for Booking | Booking pricing engine is built; business rules are yours |
| Tenants (partners) | Who becomes a tenant, which plan, when | No paying tenant yet |
| Large paid runs | Any AI batch beyond a small trial (about 50 tours) | Asked case by case with a price |
| Go-live date | When Dev becomes a real service (prod), with a checklist and cost | Not dated yet |
| Vendors | New paid tools or plan upgrades, e.g. Vercel Pro when the first paying tenant arrives | Free plans today |
| Customer data requests | A traveller asks to see or delete their data; with the lawyer if needed | Handled by hand, step by step, until a button exists |
| Incidents with personal data | Whether and how to notify people | Only if it happens |

### Tiếng Việt

| Chủ đề | Bên mình đưa chị | Hiện nay |
|---|---|---|
| Pháp lý và điều khoản | Đề xuất bình tĩnh, có các phương án; có cần luật sư hay không là chị quyết | Điều khoản tenant về nội dung do AI viết, cần chị trả lời trước 11/11/2026 |
| Giá và ưu đãi | Đề xuất quy tắc giá và biên lợi nhuận cho Booking | Bộ tính giá Booking đã xong; quy tắc kinh doanh do chị quyết |
| Tenant (đối tác) | Ai được làm tenant, gói nào, khi nào | Chưa có tenant trả tiền |
| Các lần chạy AI lớn | Mọi đợt chạy AI vượt mức thử nhỏ (khoảng 50 tour) | Hỏi từng lần, kèm giá |
| Ngày chạy thật | Khi nào Dev thành dịch vụ thật (prod), kèm checklist và chi phí | Chưa chốt ngày |
| Nhà cung cấp | Công cụ trả phí mới hoặc nâng gói, ví dụ Vercel Pro khi có tenant trả tiền đầu tiên | Hiện dùng gói miễn phí |
| Yêu cầu về dữ liệu khách | Khách muốn xem hoặc xoá dữ liệu của mình; có luật sư nếu cần | Làm tay từng bước cho tới khi có nút tự động |
| Sự cố liên quan dữ liệu cá nhân | Có thông báo cho người bị ảnh hưởng không, và thông báo thế nào | Chỉ khi xảy ra |

## 7. Reporting a problem / Báo lỗi

1. **Normal requests and bugs**: create or comment on a Jira issue in the projects you already use (PR, KAN, CON).
   Nghiệp answers there after checking; replies are reviewed before they are posted.
2. **Urgent** (something is down, wrong data is visible, a partner complains): message Nghiệp on Zalo.
3. Include: the page address, a screenshot, the time, what you expected and what you saw.

If something serious happens (a product is down for everyone, data is exposed or lost), Nghiệp tells you within
30 minutes and keeps you updated until it is fixed.

### Tiếng Việt

1. **Yêu cầu và lỗi thông thường**: tạo hoặc bình luận trên Jira trong các project chị đang dùng (PR, KAN, CON).
   Nghiệp trả lời ở đó sau khi kiểm tra; câu trả lời được duyệt trước khi đăng.
2. **Gấp** (ứng dụng ngừng chạy, hiện sai dữ liệu, đối tác phàn nàn): nhắn Nghiệp qua Zalo.
3. Gửi kèm: địa chỉ trang, ảnh chụp màn hình, thời điểm, chị mong đợi gì và thực tế thấy gì.

Nếu có sự cố nghiêm trọng (sản phẩm ngừng với mọi người, dữ liệu bị lộ hoặc mất), Nghiệp báo chị trong vòng
30 phút và cập nhật cho tới khi xử lý xong.

## 8. Dev and prod today / Dev và prod hiện nay

- **Dev** is the only environment today. It is for building and testing. It holds **test data only**: no real
  customers. Pages can change quickly, and test records can be reset.
- **Prod** (production) will be the real service for travellers and partners. It will use a separate database on the
  same AWS account. It starts when you set a go-live date. Before that date we finish a checklist: security keys
  renewed, backups and restore tested, alerts and response targets in place.
- Acceptance testing will be recorded as short videos for all apps once the technical work is done.

### Tiếng Việt

- **Dev** là môi trường duy nhất hiện nay, dùng để xây và thử. Dev chỉ chứa **dữ liệu thử**: không có khách thật.
  Giao diện có thể đổi nhanh và dữ liệu thử có thể bị làm mới.
- **Prod** (môi trường thật) sẽ là dịch vụ thật cho khách và đối tác, dùng một cơ sở dữ liệu riêng trên cùng tài khoản
  AWS. Prod bắt đầu khi chị chốt ngày chạy thật. Trước ngày đó bên mình hoàn tất một checklist: thay mới khoá bảo
  mật, thử sao lưu và khôi phục, có cảnh báo và mục tiêu phản hồi.
- Nghiệm thu (UAT) sẽ được quay thành video ngắn cho mọi ứng dụng khi phần kỹ thuật xong.

## 9. Keeping your account safe / Giữ an toàn tài khoản

- You sign in with a one-time code sent to your company e-mail. There is no password to remember.
- **Never share a code** with anyone, including Nghiệp. Nobody from our team will ever ask for it.
- A code you did not request means someone typed your address: ignore it and tell Nghiệp.
- Sign out on shared or public computers.
- Lost access to your e-mail? Tell Nghiệp; an owner can disable and restore your CIS access.
- Security logs (sign-in and network records) are kept for 365 days; app logs for 30 days.

### Tiếng Việt

- Chị đăng nhập bằng mã dùng một lần gửi vào email công ty. Không có mật khẩu phải nhớ.
- **Không bao giờ đưa mã** cho bất kỳ ai, kể cả Nghiệp. Không ai trong nhóm sẽ hỏi mã của chị.
- Nhận được mã mà chị không yêu cầu nghĩa là có người gõ địa chỉ email của chị: bỏ qua và báo Nghiệp.
- Đăng xuất khi dùng máy tính chung hoặc máy công cộng.
- Mất quyền vào email? Báo Nghiệp; owner có thể tạm khoá và mở lại quyền CIS cho chị.
- Nhật ký bảo mật (đăng nhập, truy cập mạng) được giữ 365 ngày; nhật ký ứng dụng giữ 30 ngày.

## 10. Fifteen key terms / Mười lăm thuật ngữ chính

| English | Tiếng Việt | Meaning / Nghĩa |
|---|---|---|
| Tenant | Tenant (đối tác dùng nền tảng) | A partner brand that uses our content platform. / Thương hiệu đối tác dùng nền tảng nội dung của mình. |
| Tenant portal | Cổng tenant | The partner's own website area. / Khu vực web riêng của đối tác. |
| Admin console | Trang quản trị | The staff website for CIS. / Trang web nội bộ của CIS cho nhân viên. |
| Master Content | Nội dung gốc | Our checked version of each tour, shared by all tenants. / Bản tour đã kiểm tra, dùng chung cho mọi tenant. |
| Atom | Atom (mẩu nội dung) | A small reusable piece of tour content. / Một mẩu nội dung tour nhỏ, dùng lại được. |
| Trip case | Hồ sơ chuyến đi | One traveller request handled in Booking. / Một yêu cầu của khách được xử lý trong Booking. |
| Proposal | Đề xuất | The offer staff send to a traveller. / Phương án nhân viên gửi cho khách. |
| Dev | Môi trường Dev | Build-and-test environment, test data only. / Môi trường xây và thử, chỉ có dữ liệu thử. |
| Prod | Môi trường thật | The future live service. / Dịch vụ chạy thật sau này. |
| Deploy | Triển khai | Putting a new version on a server. / Đưa phiên bản mới lên máy chủ. |
| Release | Phát hành | Users start seeing a feature. / Người dùng bắt đầu thấy tính năng. |
| Incident | Sự cố | Something broken that affects users. / Lỗi làm ảnh hưởng người dùng. |
| Budget alert | Cảnh báo ngân sách | E-mail when spend nears the monthly limit. / Email khi chi phí gần chạm mức tháng. |
| Personal data (PII) | Dữ liệu cá nhân | Data that identifies a person. / Dữ liệu nhận diện được một người. |
| UAT | Nghiệm thu | Business acceptance test before go-live. / Kiểm tra chấp nhận của phía kinh doanh trước khi chạy thật. |

The full glossary with more terms: [glossary](../glossary.md). / Bảng thuật ngữ đầy đủ: [glossary](../glossary.md).

## Sources (for maintainers)

Keep this page in step with: staff sign-in ADR 0006a; CIS admin navigation (`AA-CIS-App` `frontend/app/_kit/adminNav.tsx`,
AA-883, AA-884); ops overview AA-858; cost per app AA-884, monthly report AA-896 with AA-838; budgets in Infra
`observability.tf` (read live 2026-10-19); legal AA-820, AA-886; Dev test data only D-01; prod ADR 0001 / C7.2a /
D-17 / AA-880; Vercel plan D-18; data requests D-11; log retention D-09 / AA-872; incident duties
[incident response](../ops/incident-response.md); UAT videos AA-855; Safe Browsing review AA-816. The bilingual
format is an exception to the language convention, pending N-7.
