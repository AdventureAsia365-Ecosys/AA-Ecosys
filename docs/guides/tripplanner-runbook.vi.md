---
id: GUIDE-12-tripplanner
title: Runbook TripPlanner
description: Cách khách du lịch dùng TripPlanner ở dạng khách vãng lai hoặc đã đăng nhập (lên kế hoạch chuyến đi, gửi cho tư vấn viên, My trips và thanh toán), tài khoản khách du lịch được tạo thế nào, nhân sự làm gì với các yêu cầu, và xem ở đâu khi có gì đó sai.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [tripplanner-web, tripplanner-lambda]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-booking, GUIDE-04, OPS-04, AA-1020]
lang: vi
translation_of: docs/guides/tripplanner-runbook.md
---

# Runbook TripPlanner

Thuộc bộ [truy cập và vận hành các ứng dụng](app-access-and-operations.vi.md). Đây là bản tiếng Việt của
[tripplanner-runbook.md](tripplanner-runbook.md).

## 1. Ai dùng

TripPlanner là website công khai nơi khách du lịch khám phá các điểm đến và tour của Adventure Asia, dựng chuyến đi trên
bản đồ và gửi nó cho một tư vấn viên Adventure Asia. Khách du lịch dùng ở dạng **khách vãng lai** (không có tài khoản)
hoặc **đã đăng nhập** (để xem chuyến đi trên mọi thiết bị và các yêu cầu thanh toán của những chuyến đi họ gửi khi đã
đăng nhập). Nhân sự Adventure Asia không đăng nhập ở đây: các chuyến đi gửi cho tư vấn viên sẽ tới
[Booking admin](booking-admin-runbook.vi.md).

## 2. Địa chỉ

| Trang | Địa chỉ Dev |
|---|---|
| Trang chủ | `https://tripplanner.lumiguides.it.com` |
| Bản đồ lên kế hoạch | `https://tripplanner.lumiguides.it.com/plan` |
| Điểm đến | `https://tripplanner.lumiguides.it.com/destinations` |
| Đăng nhập | `https://tripplanner.lumiguides.it.com/sign-in` |
| My trips | `https://tripplanner.lumiguides.it.com/trips` |

## 3. Lấy tài khoản

Không ai tạo tài khoản khách du lịch bằng tay. Khách du lịch tự tạo tài khoản ở lần đầu đăng nhập bằng mã gửi qua
e-mail. Khách chỉ lên kế hoạch và gửi chuyến đi thì không cần tài khoản.

## 4. Đăng nhập và đăng xuất

1. Chọn **Sign in** trên thanh đầu trang (hoặc **Sign in or create an account**).
2. Nhập một địa chỉ e-mail và chọn **Email me a code**.
3. Nhập mã trong e-mail. Một địa chỉ mới nhận một mã để xác nhận địa chỉ, rồi thêm một mã nữa để đăng nhập ("Your
   email is confirmed. We sent one more code to sign you in.").
4. Bạn vào **My trips**. Các chuyến đi đã lên kế hoạch trên trình duyệt này khi còn là khách vãng lai được thêm vào tài
   khoản của bạn. Chuyến đi bạn đã gửi ở dạng khách vãng lai vẫn nhận yêu cầu thanh toán qua e-mail từ tư vấn viên,
   không hiện trong **Payments**.
5. Để đăng xuất, chọn **Sign out**. Trên máy tính dùng chung, luôn đăng xuất.

Không có mật khẩu. Mã đã hết hạn hoặc nhập sai sẽ hiện thông báo; hãy xin mã mới.

## 5. Khách vãng lai và khách du lịch đã đăng nhập

| | Khách vãng lai | Đã đăng nhập |
|---|---|---|
| Khám phá điểm đến và tour, lên kế hoạch trên bản đồ | Có | Có |
| Gửi chuyến đi cho tư vấn viên | Có (tên, e-mail và số điện thoại trong biểu mẫu) | Có (e-mail được điền sẵn) |
| Tìm lại chuyến đi | Chỉ trên cùng trình duyệt | **My trips**, trên mọi thiết bị |
| Xem yêu cầu thanh toán từ Adventure Asia | Không: tư vấn viên gửi qua e-mail | **Payments** trong **My trips**, chỉ với chuyến đi gửi khi đã đăng nhập (chuyến đi gửi ở dạng khách vãng lai vẫn qua e-mail, kể cả sau khi đăng nhập) |

## 6. Sử dụng hằng ngày (khách du lịch)

### Lên kế hoạch chuyến đi

1. Ở trang chủ, điền **Where to**, **How long** và **Travellers**, rồi **Plan a trip**. Hoặc mở một trang điểm đến hay
   trang tour và chọn **Customise this trip** hoặc **Ask an advisor**.
2. Trên bản đồ lên kế hoạch, bấm vào một điểm đánh dấu và **+ Add to trip**. Chuyển qua lại giữa **Map** và **List of
   tours**.
3. Dùng **Reorder & send** để kéo các ngày theo thứ tự. Có thể thêm ngày phụ và ngày tự do.

### Gửi cho tư vấn viên

1. Mở bảng chuyến đi và điền **Full name**, **Email** và **Phone**.
2. Đánh dấu "An Adventure Asia advisor may contact me about this trip." và chọn **Send to an advisor**.
3. Trang báo "Sent to an advisor. They'll be in touch shortly." Yêu cầu tới Booking admin dưới dạng một yêu cầu mới.

### Theo dõi chuyến đi và thanh toán (đã đăng nhập)

1. Mở **My trips**. Mỗi chuyến đi hiện trạng thái (Draft hoặc Sent to an advisor), các điểm dừng và số ngày. **Open**
   mở lại nó trên bản đồ.
2. Trong **Payments**, xem lịch thanh toán, các khoản đã nhận và **How to pay** khi còn nợ tiền. Không có nút thanh
   toán: hướng dẫn thanh toán do tư vấn viên gửi.
3. **Payments** chỉ liệt kê các chuyến đi gửi khi đã đăng nhập. Chuyến đi gửi ở dạng khách vãng lai không bao giờ hiện
   yêu cầu thanh toán ở đây, kể cả khi bạn đăng nhập sau đó và nó được thêm vào **My trips**: tư vấn viên gửi các yêu
   cầu đó qua e-mail.

## 7. Nhân sự làm gì

- Các chuyến đi mới gửi cho tư vấn viên hiện trong Booking admin › **Trip Cases** (tab **Inquiries**), và nhân sự nhận
  một e-mail "new inquiry". Làm theo [runbook Booking admin](booking-admin-runbook.vi.md).
- Trang tour và trang điểm đến được dựng từ Master Content của CIS. Một tour mà Adventure Asia ngừng bán sẽ biến mất
  khỏi danh sách trong vài phút và trang của nó báo "gone".
- Trang **Apps** của CIS admin có một thẻ TripPlanner với chi phí AI hôm nay so với trần ngày. Khi không đọc được chi
  phí, TripPlanner ngừng gọi AI và trả bản đơn giản không có chữ do AI viết.

## 8. Khi có gì đó sai

| Khách du lịch hoặc nhân sự thấy | Sau đó |
|---|---|
| "We could not send the email" hoặc không có mã | Kiểm địa chỉ và thư mục spam; chờ vài phút ("Too many attempts") |
| Một thông báo nói trình duyệt không giữ cookie của bản đồ lên kế hoạch | Cho phép cookie với trang này; không có cookie thì không lưu được thay đổi của chuyến đi |
| **Send to an advisor** lỗi | Thử lại; nếu vẫn lỗi, ghi lại thời điểm và báo kỹ sư trực |
| Một chuyến đi đã gửi không có trong Booking | Kỹ sư trực kiểm báo cáo bàn giao yêu cầu (CIS admin › **Reports**) |
| **We could not load your payments** | Chọn **Try again**; nếu vẫn vậy, báo kỹ sư trực |
| Một trang tour báo "not found" | Tour có thể đang tạm dừng hoặc không còn bán; kiểm trong CIS admin › **Master Content** |

Trong giai đoạn dev, tech lead là kỹ sư trực. Rollback dành cho kỹ sư:
[rollback TripPlanner Lambda](../ops/runbooks/rollback-tp-lambda.md) và, với web app trên ECS, [rollback ECS](../ops/runbooks/rollback-ecs.md) (service `aa-tripplanner-dev-web`; project Vercel đã gỡ, AA-1038).

## 9. Lưu ý giai đoạn Dev

- Trang web là bản **xem trước**: công cụ tìm kiếm được yêu cầu không lập chỉ mục, và chân trang ghi "Preview site".
- **Terms** và **Privacy** là bản nháp đang chờ review pháp lý.
- Phần chữ AI trong bản đồ lên kế hoạch (lời dẫn lộ trình) cần một model chat. Tài khoản model chính từ chối lời gọi từ
  29/10/2026, nên phần chữ đó có thể thiếu trên Dev; lên kế hoạch, bản đồ và gửi đi vẫn hoạt động.
- Dữ liệu trên Dev là dữ liệu thử; chưa mời khách du lịch thật.

## Nguồn (cho người bảo trì)

Đọc từ AA-TripPlanner-Web `main` ngày 01/11/2026: các thư mục route `frontend/app`,
`frontend/components/SignInForm.tsx`, `TripPanel.tsx`, `MyTrips.tsx`, `MyPayments.tsx`, `site/HomeSearch.tsx`, và
`CONTEXT.md` (các mục "Pages", "Guest identity", "Traveller sign-in in the BFF", "My Payments", "Contracts with other
apps"). Quyết định: ADR gốc 0006 (Phase 4, đăng nhập khách du lịch). Giữ trang này khớp với
[tripplanner-runbook.md](tripplanner-runbook.md).
