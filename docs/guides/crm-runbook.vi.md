---
id: GUIDE-12-crm
title: Runbook CRM
description: Cách đại lý đối tác và nhân sự Adventure Asia vào CRM cho đại lý (AA Partner), các vai trò owner, agent và assistant làm được gì, các luồng hằng ngày từ yêu cầu tới thanh toán, console nhân sự AA và trang admin Agencies (CRM), và làm gì khi có gì đó sai.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-crm-web, aa-crm-api, aa-cis-frontend]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-content-studio, GUIDE-12-cis-admin, GUIDE-04, OPS-04, AA-1020]
lang: vi
translation_of: docs/guides/crm-runbook.md
---

# Runbook CRM

Thuộc bộ [truy cập và vận hành các ứng dụng](app-access-and-operations.vi.md). Đây là bản tiếng Việt của
[crm-runbook.md](crm-runbook.md).

## 1. Ai dùng

CRM cho đại lý (người dùng thấy tên **AA Partner**) là ứng dụng Adventure Asia cấp cho các đại lý du lịch đối tác để
quản lý khách hàng của chính họ, có sẵn tour Adventure Asia bên trong. Bốn nhóm sử dụng:

| Nhóm | Ở đâu | Để làm gì |
|---|---|---|
| **Đội ngũ đại lý**: owner, agent, assistant | Ứng dụng đại lý | Yêu cầu, khách hàng, báo giá, thanh toán, đặt chỗ, đội ngũ và cài đặt |
| **Khách du lịch của đại lý** | Các trang mở từ đường link đại lý gửi | Biểu mẫu yêu cầu, báo giá, cổng khách du lịch. Họ không bao giờ có tài khoản |
| **Bộ phận hỗ trợ và điều hành mặt đất của Adventure Asia** | Console nhân sự AA (`/staff`) | Đọc dữ liệu của một đại lý khi owner cho phép; xem những gì khách du lịch chia sẻ cho các tour Adventure Asia đã xác nhận |
| **Admin của Adventure Asia** | CIS admin › **Agencies (CRM)** | Tạo đại lý, mời owner đầu tiên, khoá và mở khoá, mức sử dụng |

Đại lý sở hữu dữ liệu khách hàng của mình; Adventure Asia chỉ xử lý dữ liệu đó. Vì vậy nhân sự Adventure Asia chỉ
thấy số liệu sử dụng, không bao giờ thấy chuyến đi hay doanh thu, trừ khi owner cho phép truy cập hỗ trợ.

## 2. Địa chỉ

| Trang | Địa chỉ Dev |
|---|---|
| Ứng dụng đại lý (CRM, và Content studio trên cùng host) | `https://portal.lumiguides.it.com` |
| Trang cho khách du lịch (biểu mẫu, báo giá, cổng khách du lịch) | `https://go-dev.lumiguides.it.com/c/...` (chỉ qua đường link đại lý gửi; mở host trần không thấy gì) |
| Console nhân sự AA | `https://portal.lumiguides.it.com/staff` |
| Trang health của CRM | `https://portal.lumiguides.it.com/health` |
| Trang admin Agencies (CRM) | `https://aa-cis.lumiguides.it.com/admin/platform/agencies` |

Host cũ `partner-dev.lumiguides.it.com` chuyển tiếp sang `portal.lumiguides.it.com`.

## 3. Lấy tài khoản

### Một đại lý mới (Adventure Asia)

1. Một admin Adventure Asia thuộc nhóm nhân sự CRM platform-admin mở CIS admin › **Agencies (CRM)**.
2. **Create agency**: chọn nguồn đại lý (**For a CIS tenant**, hoặc **New synthetic agency (test)**), rồi **Agency
   name**, **Default language and region** và ticket hỗ trợ hoặc Jira mà đại lý thuộc về (ví dụ `SUP-1024`; ticket được
   ghi vào nhật ký truy cập của đại lý). Chưa có thành viên nào được tạo.
3. Mở ngăn chi tiết của đại lý và chọn **Invite first owner** với địa chỉ e-mail của owner. Địa chỉ không bao giờ được
   lưu dạng đọc được hay hiện lại.

Một đại lý mới bắt đầu với gói miễn phí 10 chỗ.

### Tham gia một đại lý (mọi thành viên)

1. Mở e-mail "Your invitation to AA Partner" và chọn **Open invitation**.
2. Trang hiện địa chỉ để đăng nhập và một **mật khẩu dùng một lần**, chỉ hiện một lần. Giữ trang mở và chọn **Continue
   to sign in**.
3. Đăng nhập bằng mật khẩu dùng một lần, rồi tự chọn mật khẩu của mình.
4. Cài một **ứng dụng xác thực** trên điện thoại và nhập mã của nó. Luôn bắt buộc đăng nhập hai bước.
5. Chọn **Accept invitation**, rồi **Go to AA Partner**.

Nếu mất mật khẩu dùng một lần trước lần đăng nhập đầu, hãy xin owner một lời mời mới.

### Owner mời đội ngũ

1. **Settings › Team & roles › Team, roles and plan**.
2. **Invite someone**: địa chỉ e-mail và vai trò (owner, agent hoặc assistant), rồi **Send invitation**.
3. Lời mời hiện trạng thái **Invited** cho tới khi người đó chấp nhận. Owner đổi vai trò hoặc gỡ một thành viên tại
   đây; chuyến đi và khách hàng đang mở của thành viên bị gỡ chuyển vào hàng đợi giao lại trên cùng trang.

### Console nhân sự Adventure Asia

Console dùng kiểu đăng nhập nhân sự (e-mail công ty và mã dùng một lần). Tech lead thêm tài khoản nhân sự của bạn vào
nhóm **điều hành mặt đất**, nhóm **hỗ trợ đại lý**, hoặc cả hai. Không có nhóm nào thì console đăng xuất bạn kèm một
thông báo.

## 4. Đăng nhập và đăng xuất

### Đội ngũ đại lý

1. Mở `https://portal.lumiguides.it.com` và chọn **Sign in**.
2. Nhập e-mail, mật khẩu và mã từ ứng dụng xác thực.
3. Nếu bạn thuộc nhiều đại lý, chọn một. Một đại lý bị khoá hiện "This agency is locked by AA".
4. Để đăng xuất, chọn **Sign out** trong menu. Thao tác này cũng đăng xuất bạn khỏi Content studio.

### Nhân sự Adventure Asia

Mở `https://portal.lumiguides.it.com/staff` và chọn **Sign in with your AA staff
account**. Đăng xuất khỏi console (**Sign out of the staff console**) không ảnh hưởng phiên đại lý nào.

### Khách du lịch

Khách du lịch mở đường link đại lý gửi. Cổng khách du lịch hỏi một mã gửi tới e-mail của họ.

## 5. Vai trò

| Vai trò | Làm được gì |
|---|---|
| **Owner** | Mọi thứ: đội ngũ và gói, cài đặt thanh toán, nhập dữ liệu, dữ liệu và quyền riêng tư, nhật ký truy cập, cho phép hỗ trợ AA, danh sách việc bắt đầu |
| **Agent** | Việc bán hàng trên chuyến đi và khách hàng, báo giá, thanh toán và đặt chỗ; thấy biên lợi nhuận và **Commissions**; không có cài đặt đội ngũ hay cài đặt của owner |
| **Assistant** | Việc hằng ngày của đội, không có **Commissions**, **Marketing** hay bất kỳ số biên lợi nhuận, giá net hoặc hoa hồng nào |

Ẩn một mục menu chỉ để tiện: máy chủ kiểm vai trò ở mọi thao tác.

Nhóm nhân sự AA: **hỗ trợ đại lý** chỉ được đọc một đại lý khi owner của đại lý đó cho phép hỗ trợ; **điều hành mặt
đất** đọc các ops release và có thể mở truy cập khẩn cấp; nhóm **CRM platform-admin** thực hiện thay đổi trên
**Agencies (CRM)**. Mỗi lần nhân sự xem một trang được ghi vào nhật ký truy cập của đại lý, owner đọc được.

## 6. Menu (ứng dụng đại lý)

- **Home**: việc cần bạn xử lý, danh sách việc bắt đầu, 12 tháng qua.
- **CRM**: **Pipeline**, **Clients**, **Inbox**, **Tasks**, **Travelling now**, **Calendar**.
- **Money**: **Payments**, **Bookings**, **Commissions**.
- **Grow**: **Reports**, **Marketing**, **Suppliers**, **Library**, **Automations**.
- **Content studio**: **Open Content studio** (khi đại lý cũng là tenant).
- **Settings** và **Help & what's new**.

Ứng dụng mở bằng tiếng Anh. Đổi ngôn ngữ và định dạng ngày ở **Settings › Language and dates**.

## 7. Việc hằng ngày

### Ngày đầu tiên (owner)

1. Mở **Home** và danh sách **Get started**. Ba bước là bắt buộc; các bước khác có thể để sau (**Later**).
2. Đọc và chấp nhận **Shared responsibility** (một lần, chỉ owner).
3. **Settings › Getting started › Connections and privacy**: kết nối hộp thư riêng, thanh toán thẻ hoặc chuyển khoản,
   SMS và WhatsApp. Đây là tài khoản của chính đại lý bạn; Adventure Asia không cung cấp chúng.
4. **Settings › Getting started › Import clients** (owner): tải lên một file CSV hoặc Excel. Một lần chạy thử cho thấy
   kết quả trước khi lưu bất cứ thứ gì.

### Nhận yêu cầu

1. **Settings › Inquiry forms › Inquiry forms and embed code**, rồi **New form**.
2. **Copy** mã nhúng vào website của bạn, hoặc chia sẻ đường link biểu mẫu.
3. Mỗi yêu cầu hiện trên **Pipeline** ở cột **Inquiry**. Yêu cầu lặp lại từ cùng một người được gộp vào chuyến đi đang
   mở.

### Xử lý một chuyến đi từ yêu cầu tới đặt chỗ

1. Trên **Pipeline**, mở thẻ chuyến đi. Chuyển nó qua **Qualifying**, **Proposal**, **Booked**, **Pre-departure**,
   **Travelling**, **Completed** (hoặc **Lost** / **Cancelled**).
2. Dựng báo giá trong chuyến đi: các ngày, tour Adventure Asia (giá thực và giữ chỗ) và nhà cung cấp riêng của bạn.
3. **Send to the client**. Khách mở đường link báo giá, chọn phương án và chấp nhận. Muốn đổi sau khi đã gửi thì cần
   **New version**.
4. Khi khách thanh toán: **Record payment**. Các dòng tour Adventure Asia được xác nhận sau khi có tiền cọc.
5. **Send portal link** cấp cho khách du lịch cổng của họ: giấy tờ, chuyến bay, thoả thuận cần ký, và lịch trình
   chuyến đi, xem được cả khi không có mạng trên điện thoại.

### Khách hàng

1. **Clients** chỉ liệt kê tên. **New client** thêm một khách bằng tay.
2. Thông tin liên lạc, giấy tờ tuỳ thân và thông tin sức khoẻ chỉ mở khi bấm **Reveal**, kèm lý do. Mỗi lần mở được ghi
   vào nhật ký truy cập.

### Tiền và theo dõi

- **Payments** và **Bookings**: đã trả, còn nợ và đã đặt. **Commissions** (owner và agent).
- **Travelling now** và **Calendar**: ai đang đi hôm nay và việc sắp tới; lịch có thể đồng bộ sang Google, Outlook hoặc
  Apple Calendar qua một đường link riêng.
- **Reports**: số liệu riêng của đại lý.

### Cho phép bộ phận hỗ trợ Adventure Asia (owner)

1. **Settings › Data and privacy › AA support access**.
2. **Allow AA support** trong 1 tới 7 ngày, chỉ đọc. Việc hiện tên vẫn tắt trừ khi bạn bật.
3. Một dải màu hổ phách hiện trên mọi trang khi đang cho phép hỗ trợ. **End now** dừng ngay lập tức.

Dải màu đỏ nghĩa là **truy cập khẩn cấp**: Adventure Asia mở nó mà không cần bạn cho phép, vì lý do bảo mật, dữ liệu
hoặc pháp lý, trong tối đa 60 phút. Owner nhận một e-mail và dải này tự đóng.

### Rời đi hoặc xoá dữ liệu (owner)

**Settings › Data and privacy** chứa các quy tắc dữ liệu, thùng rác, lưu giữ pháp lý, xoá dữ liệu khách hàng, xuất dữ
liệu đại lý và rời AA Partner. Một yêu cầu do Adventure Asia nêu ra hiện ở đây với **Confirm** hoặc **Decline**.

### Nhân sự Adventure Asia

- **Agencies (CRM)** trong CIS admin: danh sách kèm mức sử dụng (chỗ, thành viên hoạt động, dung lượng, chi phí AI, job
  lỗi); **Lock** / **Unlock**; chạy lại một job lỗi; mở khôi phục owner khi một đại lý mất owner duy nhất (hoàn tất sau
  14 ngày, và mọi thành viên đều thấy và huỷ được).
- **Console nhân sự › Ops releases**: thông tin khách du lịch mà đại lý chia sẻ cho các tour Adventure Asia đã xác
  nhận, mức tối thiểu đội mặt đất cần, bị xoá 90 ngày sau ngày về.
- **Console nhân sự › Support access**: các đại lý đang cho phép hỗ trợ; bắt đầu một phiên kèm ticket (mỗi lúc một
  nhân sự; phiên kết thúc khi owner thu hồi quyền hoặc sau 8 giờ). Nhân sự điều hành mặt đất có thể mở truy cập khẩn
  cấp kèm lý do, ticket và 15 tới 60 phút; ở đó không bao giờ hiện tên.

## 8. Khi có gì đó sai

| Bạn thấy | Sau đó |
|---|---|
| Một trang báo dịch vụ CRM không trả lời | Mở trang health của CRM; thử lại sau một phút |
| "This agency is locked by AA" | Owner liên hệ Adventure Asia; một admin mở khoá ở **Agencies (CRM)** |
| Mất điện thoại hoặc ứng dụng xác thực | Owner báo Adventure Asia; nếu owner duy nhất bị khoá ngoài, một admin mở khôi phục owner |
| Lời mời không tới | Xem thư mục spam; owner gửi một lời mời mới |
| Console nhân sự báo tài khoản của bạn không có quyền | Nhờ tech lead thêm bạn vào nhóm hỗ trợ hoặc điều hành mặt đất |
| Job lỗi ở **Agencies (CRM)** hoặc ở CIS admin › **Apps** (CRM jobs) | Chạy lại từ ngăn chi tiết của đại lý; nếu lại lỗi, báo kỹ sư trực |

Đại lý liên hệ người phụ trách của họ ở Adventure Asia. Bên trong Adventure Asia, kỹ sư trực (trong giai đoạn dev là
tech lead) theo [ứng phó sự cố](../ops/incident-response.md); runbook khoá mã hoá của CRM là
[CRM keys](../ops/runbooks/crm-keys.md).

## 9. Lưu ý giai đoạn Dev

- Dev chỉ nhận **đại lý giả lập**; không tạo được đại lý thật trên Dev. Mọi khách du lịch đều được tạo ra.
- Soạn nháp bằng AI chạy một bộ thay thế dựng sẵn, không phải model thật, nên nội dung chỉ là chữ giữ chỗ.
- SMS và WhatsApp dùng một nhà cung cấp sandbox không gửi gì. Thanh toán thẻ qua Stripe chưa được xây; thanh toán được
  ghi bằng tay.
- `portal.lumiguides.it.com` và host cho khách du lịch `go-dev.lumiguides.it.com` là địa chỉ Dev; tên host production
  có khi go-live.

## Nguồn (cho người bảo trì)

Đọc từ AA-Partner `main` ngày 01/11/2026: `web/lib/nav.ts` (menu và vai trò thấy gì), `web/lib/i18n.ts` và
`web/lib/i18nStaff.ts` (nhãn), `web/app/(crm)/settings/page.tsx`, `CONTEXT.md` (các mục "Web", "Tenant portal",
"F4 roles and team", "L1 console", "AA support access L2 + break-glass L3", "AA staff console", "Domain terms");
AA-CIS-App `frontend/app/admin/platform/agencies/messages.ts`. Quyết định: ADR gốc 0010, 0006b, 0008a. Giữ trang này
khớp với [crm-runbook.md](crm-runbook.md).
