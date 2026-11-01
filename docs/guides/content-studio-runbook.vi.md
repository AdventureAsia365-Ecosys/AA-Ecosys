---
id: GUIDE-12-content-studio
title: Runbook Content studio
description: Cách một thương hiệu đối tác (tenant) vào Content studio, các vai trò owner, editor và viewer làm được gì, các luồng hằng ngày từ chọn tour tới đăng nội dung, và làm gì khi có gì đó sai.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-crm-portal, aa-cis-api]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-crm, GUIDE-12-cis-admin, GUIDE-04, AA-1020]
lang: vi
translation_of: docs/guides/content-studio-runbook.md
---

# Runbook Content studio

Thuộc bộ [truy cập và vận hành các ứng dụng](app-access-and-operations.vi.md). Đây là bản tiếng Việt của
[content-studio-runbook.md](content-studio-runbook.md).

## 1. Ai dùng

Content studio (cổng tenant) là nơi một thương hiệu đối tác mua nội dung từ Adventure Asia chọn tour, viết lại tour
theo giọng thương hiệu của mình, viết bài mạng xã hội và bài viết, rồi đăng lên website hoặc Facebook Page của mình.
Người dùng là thành viên của một **tenant**. Nhân sự Adventure Asia thiết lập tenant từ CIS admin; họ không làm việc
bên trong studio.

Studio dùng chung một host, một tài khoản và một lần đăng xuất với [CRM cho đại lý](crm-runbook.vi.md): một đại lý có
cả hai thì mở studio từ menu CRM (**Open Content studio**), và studio có đường link quay lại (**Open CRM**).

## 2. Địa chỉ

| Trang | Địa chỉ Dev |
|---|---|
| Content studio | `https://portal.lumiguides.it.com/portal/dashboard` |
| Đăng nhập | Bắt đầu từ địa chỉ trên; trang đăng nhập đối tác tự mở |

## 3. Lấy tài khoản

1. **Adventure Asia tạo tenant.** Một admin mở CIS admin › **Tenants**, chọn **New Tenant**, điền biểu mẫu và bấm
   **Create Tenant**.
2. **Adventure Asia mời thành viên đầu tiên.** Lời mời ghi địa chỉ e-mail và vai trò trong studio (owner, editor hoặc
   viewer). CIS admin chưa có nút cho việc này: hãy nhờ kỹ sư trực, người sẽ gửi lời mời qua tuyến mời dành cho nhân
   sự. CIS giữ vai trò; CRM gửi e-mail.
3. **Thành viên mở e-mail** "Your invitation to AA Partner" và chọn **Open invitation**.
4. Trang hiện địa chỉ để đăng nhập và một **mật khẩu dùng một lần**, chỉ hiện một lần. Giữ trang mở, chọn **Continue
   to sign in**, đăng nhập bằng mật khẩu đó, rồi tự chọn mật khẩu của mình.
5. Cài một **ứng dụng xác thực** trên điện thoại (Google Authenticator, Microsoft Authenticator, 1Password hoặc tương
   tự) và nhập mã của nó. Luôn bắt buộc đăng nhập hai bước.
6. Chọn **Accept invitation**. Trang báo **Your Content studio access is ready**; chọn **Open the Content studio**.

Nếu địa chỉ đó đã có tài khoản AA Partner (ví dụ từ CRM), người đó đăng nhập bằng tài khoản ấy và chỉ cần chấp nhận.
Nếu mất mật khẩu dùng một lần trước lần đăng nhập đầu, cần một lời mời mới.

## 4. Đăng nhập và đăng xuất

1. Mở `https://portal.lumiguides.it.com/portal/dashboard`.
2. Trên trang đăng nhập, nhập địa chỉ e-mail, mật khẩu và mã từ ứng dụng xác thực.
3. Nếu tài khoản của bạn thuộc nhiều studio, chọn một ở trang **Choose a Content studio**.
4. Để đăng xuất, mở **Account settings** và đăng xuất. Thao tác này cũng đăng xuất bạn khỏi CRM trên cùng host.

Trang báo **No Content studio access** nghĩa là tài khoản chưa là thành viên studio nào: hãy đăng nhập bằng địa chỉ
đã nhận lời mời, hoặc xin Adventure Asia một lời mời.

## 5. Vai trò

| Vai trò | Làm được gì |
|---|---|
| **owner** | Mọi thứ trong studio, gồm **Integrations**, khoá **API** và các trang tài khoản |
| **editor** | Chọn tour và viết, sửa, đăng nội dung; không đổi được **Integrations**, tài khoản hay webhook |
| **viewer** | Chỉ đọc |

Vai trò do Adventure Asia (CIS) đặt; trang **Members** liệt kê các thành viên của tenant và vai trò của họ.

## 6. Menu

- **Overview**: **Dashboard** (mức sử dụng và hạn mức trong một màn hình).
- **Tours**: **Marketplace** (mọi tour bạn chọn được, và các tour bạn đã chọn), **My Tours** (các bản bạn đã viết
  lại).
- **Brand**: **Brand Identity** (giọng văn, sắc thái, lời kêu gọi hành động, quy tắc), **Facts** (giá, mùa, visa, đưa
  đón và điều khoản mà bộ viết của bạn được trích dẫn).
- **Create**: **Social Posts**, **Articles**.
- **Content**: **My Content** (mọi thứ đã viết, sẵn sàng để duyệt và đăng).
- **Account**: **Billing**, **Activity**, **Account settings**, **Members**, **API**, **Integrations**.

Trên điện thoại, thanh dưới cùng có Dashboard, Tours, Create và Content; **More** mở phần còn lại. Bấm ⌘K (Ctrl+K)
để tìm bất kỳ trang nào.

## 7. Việc hằng ngày

### Thiết lập thương hiệu một lần

1. Mở **Brand Identity** và điền giọng văn, sắc thái, lời kêu gọi hành động và quy tắc.
2. Mở **Facts** và thêm các dữ kiện mà bài viết của bạn được dùng (giá, mùa, điều khoản), mỗi dữ kiện kèm nguồn.

### Chọn và viết lại tour

1. Mở **Marketplace**. Lọc theo tên, nước hoặc độ dài; tour mới có dấu "New" trong 14 ngày.
2. Mở một tour và chọn **Rewrite this tour** (hoặc chọn nhiều tour). Ghi chú hạn mức cho biết kỳ này còn bao nhiêu lượt
   viết lại.
3. Bản viết lại hiện ở **My Tours** và ở mục **In my catalog** của Marketplace.

### Viết và đăng nội dung

1. Mở **Create › Social Posts** hoặc **Create › Articles**, chọn một tour hoặc một góc viết rồi chọn **Write**.
2. Duyệt bài trong **My Content**. **Write again** yêu cầu một phiên bản mới.
3. Kết nối các kênh một lần trong **Integrations** (**Connect WordPress**, **Connect your Facebook Page**) và chạy bài
   kiểm tra kênh.
4. Mở **Publish** từ **My Content** và đăng bài. Bài hiện trạng thái **Published**.

### Theo dõi tài khoản

- **Billing**: gói của bạn, đồng hồ lượt viết lại (đã dùng, hạn mức, ngày đặt lại) và phần vượt hạn mức tới nay.
- **Activity**: mọi việc đã xảy ra, có bộ lọc và xuất CSV.
- **API**: khoá API đã che cho hệ thống của bạn. Xin khoá mới bằng e-mail gửi Adventure Asia.

## 8. Khi có gì đó sai

| Bạn thấy | Sau đó |
|---|---|
| Trang tải lại hoặc yêu cầu đăng nhập lại | Phiên của bạn đã hết; đăng nhập lại |
| **Content studio unavailable** | Studio chưa kiểm được quyền của bạn; thử lại sau một phút |
| Viết lại hoặc viết bài bị lỗi | Xem **Billing** (đã hết hạn mức?); sau đó báo Adventure Asia kèm trang, thời điểm và ảnh chụp màn hình |
| Đăng bài bị lỗi | Chạy bài kiểm tra kênh trong **Integrations**; kết nối lại kênh nếu kiểm tra lỗi |
| Mất điện thoại hoặc ứng dụng xác thực | Báo Adventure Asia; kỹ sư trực đặt lại bước thứ hai |

Thương hiệu đối tác liên hệ người phụ trách của họ ở Adventure Asia. Bên trong Adventure Asia, kỹ sư trực (trong giai
đoạn dev là tech lead) xem **Tenants** và **Content Trace** trong CIS admin và theo quy tắc
[ứng phó sự cố](../ops/incident-response.md).

## 9. Lưu ý giai đoạn Dev

- Trên Dev chỉ có tenant giả lập để thử.
- Viết bằng AI (viết lại tour, bài mạng xã hội, bài viết) cần một model chat. Tài khoản model chính từ chối lời gọi từ
  29/10/2026, nên việc viết sẽ lỗi hoặc chờ trên Dev cho tới khi có lại đường gọi model.
- **Billing** chưa có hoá đơn (trạng thái trống). **Terms** và **Privacy** là bản nháp đang chờ review pháp lý.
- Đăng nhập bằng khoá API của tenant đã tắt với người dùng; khoá API chỉ dành cho máy.

## Nguồn (cho người bảo trì)

Đọc từ AA-Partner `main` ngày 01/11/2026: `portal/app/_kit/local/portalNav.tsx` (menu), `portal/app/portal-access/*`,
`web/lib/i18n.ts` (các chuỗi `join.*`), `CONTEXT.md` ("Tenant portal", "Content studio invitations"); AA-CIS-App
`CONTEXT.md` ("Tenant membership directory": vai trò studio) và `frontend/app/admin/tenants/messages.ts`. Quyết định:
ADR gốc 0010 và 0010a. Giữ trang này khớp với [content-studio-runbook.md](content-studio-runbook.md).
