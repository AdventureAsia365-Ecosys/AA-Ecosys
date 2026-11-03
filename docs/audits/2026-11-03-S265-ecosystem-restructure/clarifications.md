---
id: ARCH-s265-restructure-clarifications
title: "Giải thích và thiết kế lại sau khi tech lead duyệt 44 quyết định (S265)"
description: "Trả lời từng ghi chú của tech lead trên trang quyết định S265, thiết kế lại cho 4 lựa chọn khác khuyến nghị (TL-6 merge_now, TL-9 all_in_booking, TL-16 all_on_dev, TL-23 move_tp_to_ecs), bảng vai trò và ma trận quyền nhân viên AA, bảng chi phí hosting TripPlanner, kế hoạch lên prod và lộ trình R0..R8 đã đổi."
type: report
status: draft
owner: nghiep
audience: [owner, cto, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-03
review_every_days: 30
related: [ARCH-s265-ecosystem-restructure, AA-1028, AA-1004, AA-969, AA-1029, AA-1030, AA-1007, AA-1008, AA-820]
---

# Giải thích và thiết kế lại sau khi duyệt 44 quyết định (S265, 03/11/2026)

> Phụ lục của [`README.md`](README.md). Nguồn lựa chọn: [`approvals.json`](approvals.json) (40 theo khuyến nghị, 4 chọn khác).
> Viết tiếng Việt cho tech lead. Tên bảng, route, contract giữ tiếng Anh. Tên bảng/cột lấy từ
> `docs/architecture/db-schema-reference.md` (dump 02/11: CIS 346, bk-035, crm-040, tp-023). Tên ghi "(mới)" là đề xuất, chưa có trong DB.
> Không sửa code, không ghi AWS, không gọi LLM trả phí khi soạn bản này. Giá truy cập ngày 03/11/2026.

## 0. Tóm tắt

1. **Master** là nơi duy nhất được sửa một loại dữ liệu. Tài khoản tenant: CIS `shared`. Tiền với agency: Booking. Khách cuối: CRM của tenant.
2. **TL-6 `merge_now`:** gộp `portal/` vào `web/` trong R3. Chỉ còn một cách đăng nhập (partner pool + MFA). Bỏ hẳn đăng nhập bằng API key của tenant. Mất khoảng 3 phiên.
3. **TL-9 `all_in_booking`:** cả hoá đơn phần mềm lẫn hoá đơn quyết toán tour đều do Booking lập, ở bảng mới `booking.agency_invoice`. Màn Booking tạm thời vẫn là app riêng, nối sang AA Admin bằng app switcher.
4. **TL-16 `all_on_dev`:** pilot chạy cả chuỗi Content → TripPlanner → CRM → Booking trên Dev với dữ liệu thật. Đây là ngoại lệ có thời hạn và có điều kiện. Kế hoạch lên prod có 6 pha, khoảng 8–10 phiên.
5. **TL-23 `move_tp_to_ecs`:** chạy được, khoảng 16 USD/tháng trên Dev (Spot + WAF) và 28 USD on-demand. Cần hai "đồng ý" riêng: một cho Fargate, một cho WAF.
6. Lộ trình R0–R8 dài thêm khoảng 7–9 phiên, tức khoảng 32–39 phiên tổng (chưa tính 8–10 phiên của kế hoạch prod ở mục 5). Chỗ dài thêm nằm ở R3 (6–7 phiên), R4 (3–4), R5 (4–6).

---

## 1. Bốn lựa chọn khác khuyến nghị

### TL-6: gộp `portal/` vào `web/` ngay, một cách đăng nhập, không dùng key

**Trả lời.** Làm được, và ghi chú của anh đúng với hiện trạng. Trên Dev, không ai còn đăng nhập bằng API key: `PORTAL_API_KEY_SIGNIN` đã tắt từ S256, và `/tenant-login` trả 308. Nhưng code và dữ liệu key vẫn còn ở nhiều chỗ:

| Chỗ còn key | File | Xử lý |
|---|---|---|
| Trang và BFF `/tenant-login` | `AA-Partner/portal/app/tenant-login/`, `portal/app/api/auth/tenant-login/route.ts` | Xoá cùng lúc gộp |
| E2E bằng key | `e2e/smoke-portal/auth.setup.ts` (`E2E_TENANT_API_KEY`) | Chuyển sang E2E partner identity |
| CIS `POST /auth/tenant-login` (đổi key lấy JWT 24 giờ), **hai handler** | `AA-CIS-App/api/main.py:385` (không đánh dấu deprecated) và `api/routers/auth.py:163` (`deprecated=True`) | Xoá cả hai. Trước khi xoá, đọc `audit_log` 30 ngày để chắc không còn ai gọi (chưa kiểm log) |
| `verify_tenant_api_key` (`X-API-Key`) | định nghĩa ở `api/routers/auth.py:267` | Không route nào dùng nó làm dependency, xoá |
| Lambda authorizer | `api/lambda_authorizer/handler.py` | Code chết từ AA-750, xoá |
| Cấp, xoay, khôi phục key; thẻ API key | `api/routers/admin.py`, `GET /v1/account/api-key`, trang Integrations | Xoá. Bước 1 của quy trình tạo tenant mất theo |
| Cột `shared.tenants.api_key_hash` | migration CIS | Set NULL, rồi drop theo DRY RUN. Offboarding đang dùng dấu `REVOKED_`, đổi sang dùng `account_status` |

**Thiết kế lại.**

- Một app Next.js `web/` chạy trên host `portal.`. Studio chuyển vào `web/app/(studio)/portal/**` và giữ nguyên URL `/portal/*`.
- Hai file `proxy.ts` gộp thành một, kiểm theo thứ tự: host → `/staff*` → `/c/*` → `/portal*` → CRM.
- Phía server vẫn đổi token partner lấy JWT tenant (≤ 15 phút) ở CIS `/auth/tenant-session`, vì `/v1/*` chỉ nhận JWT của CIS. Nhưng việc đổi giờ chạy trong cùng một app, nên bỏ được các bản byte-copy `portal/lib/session.ts` và `seal.ts`.
- Chỉ còn một bản kit (`web/app/_kit/core`), và bỏ target `portal` trong `kit-sync.sh`.

**Hệ quả cần biết.** `X-API-Key` trên `/v1/*` thực ra không còn chạy: `verify_tenant_api_key` có trong code nhưng không route nào gọi. Đường máy duy nhất của agency vào `/v1/*` hôm nay là JWT 24 giờ lấy từ `POST /auth/tenant-login`. Xoá endpoint này (TL-6) nghĩa là **mọi truy cập bằng máy của agency vào `/v1/*` dừng hẳn tới R8**. Trên Dev chưa có agency nào dùng đường này; `audit_log` 30 ngày sẽ xác nhận trước khi xoá.

**Khác "không dùng key gì nữa".** Token M2M giữa các app của AA vẫn giữ: AA-Partner API gọi `booking.b2b.v1` và CIS `tenant.membership.v1` bằng client-credentials của pool `aa-m2m`. Đó là máy của AA gọi máy của AA, không phải key của tenant hay của người. API cho hệ thống riêng của agency (gói cao, BO-4) chỉ làm ở R8, khi có tenant trả tiền yêu cầu. Lúc đó dùng credential có scope và xoay được, và cần anh đồng ý riêng vì có thể phát sinh phí. Theo trang [Cognito pricing](https://aws.amazon.com/cognito/pricing/): không tính phí theo số app client; M2M tính 0,00225 USD mỗi token request thành công (ví dụ us-east-1), không có free tier.

**Công và tiền.**

- Khoảng 3 phiên:
  - Phiên 1: chuyển code, gộp proxy, CSP và `/healthz`; đưa `/terms` và `/privacy` vào `/legal/*` (308 từ đường cũ).
  - Phiên 2: CI/deploy. Bỏ Portal Build và `deploy-portal-dev.yml`. Bên Infra: bỏ các rule ALB của portal, rồi xoá service `aa-crm-dev-portal`, task def, target group, ECR và log group.
  - Phiên 3: xoá phần key và chạy migration CIS. Sửa ADR 0010a và CONTEXT.md của hai repo.
- Tiết kiệm: một task 0,25 vCPU / 0,5 GB ARM. `aa-crm-dev-portal` hôm nay đã chạy `FARGATE_SPOT` (`crm_portal.tf`, comment ghi khoảng 2,2 USD trên Spot), nên **tiết kiệm thật hôm nay chỉ khoảng 2,2–2,5 USD/tháng**. Con số 8,3 USD chỉ đúng nếu sau này chuyển sang on-demand (prod). Nếu app gộp cần 1 GB thì mất lại khoảng 0,5 USD trên Spot (1,5 USD on-demand).
- Lợi ích lớn hơn tiền: bớt một image, một pipeline và một quyền đọc secret `crm/<env>/web`.
- Rủi ro chính: preflight của Tailwind 4 (portal dùng) có thể làm lệch CSS của các trang CRM. Cách tránh: tắt preflight, rồi chụp ảnh so sánh trước và sau theo aa-ui-verify.

### TL-9: mọi hoá đơn trong Booking, và câu hỏi "gộp Booking về trang admin"

**Trả lời.** "Gộp" có hai nghĩa:

- **Dữ liệu và backend:** hoá đơn nằm trong schema `booking.*`. Việc này chọn xong với `all_in_booking`.
- **Màn hình:** nhân viên làm việc ở một chỗ. Đây là việc làm sau.

Backend Booking không gộp được vào CIS. Giá net (`booking.supplier_rates.net_amount`) không được ra khỏi Booking.

**Thiết kế lại (thay cho `manual_split`).**

- Bảng `booking.invoices` không dùng lại được, vì `invoices_bill_to_kind_chk` chỉ cho `'customer'` và `trip_case_id` là NOT NULL. Bảng này đóng băng cùng phần B2C.
- Migration bk mới gồm các bảng (mới):
  - `booking.agency_invoice`: `party_tenant_id`, `invoice_kind` ∈ `saas` | `settlement`, kỳ, tiền tệ, thuế, trạng thái, `e_invoice_no`, bản chụp thông tin bên nhận.
  - `booking.agency_invoice_line`: có CHECK bắt mọi dòng cùng loại với hoá đơn, nên phí phần mềm và tiền tour không bao giờ chung một hoá đơn (BO-17).
  - `booking.agency_payment`: maker-checker, người ghi khác người duyệt, bắt buộc có chứng từ.
  - `booking.invoice_sequence`: số không nhảy, mỗi loại một dãy, ví dụ `AAS-2026-000001` cho phí phần mềm và `AAT-2026-000001` cho tour.
  - `booking.billing_entity` và `booking.tax_rule`.
- Thông tin pháp lý của bên nhận hoá đơn (tên pháp nhân, mã số thuế, e-mail billing) nằm trên `shared.tenants`, vì CIS là master của tài khoản. Booking chụp lại vào hoá đơn lúc phát hành. Mọi tenant, kể cả tenant chỉ dùng Content, có một dòng projection `booking.b2b_partners`. Cột `m2m_client_id` là client của AA-Partner chứ không phải của từng tenant, nên dòng này tạo được cho mọi tenant. "Book with AA" (TL-17) cũng cần dòng này.
- Job tạo bản nháp: `bk_saas_invoice_draft` (đầu kỳ, đọc gói từ `tenant.entitlements.v1`) và `bk_settlement_draft`.
- Chiều ngược lại: Booking công bố view (mới) `booking.v_tenant_billing_status` (`paid_through`, `overdue_amount`). Job CIS `tenant_billing_tick` đọc view này rồi đổi trạng thái subscription. CIS vẫn là nơi duy nhất ghi trạng thái tài khoản.
- Vai trò `finance` cho Booking cần ba thay đổi ở ba repo:
  - **Migration CIS** (không phải bk): thêm `'finance'` vào `staff_app_grant_role_chk`. Ràng buộc này nằm trên `shared.staff_app_grant`, owner `cis_owner` (`db-schema-reference.md`), và `schema-ownership.md` giao bảng này cho CIS. Booking không được migrate nó.
  - **Infra:** thêm Cognito group `booking-finance` trong `identity.tf` (đề xuất precedence 75, nằm giữa `booking-content_creator` 70 và `crm-platform-admin` 80).
  - **Booking:** đọc vai trò từ `cognito:groups` hoặc bridge token như các vai trò Booking khác, rồi gác route hoá đơn/thanh toán bằng vai trò này.
- Màn hình:
  - Bây giờ: thêm nhóm "Trade" trong nav AA Admin, mở sang Booking admin bằng app switcher (cùng đăng nhập WORKFORCE). Tenant 360 có tab Billing chỉ đọc kèm nút "Open in Booking".
  - Gộp hẳn màn Booking vào `AA-CIS-App/frontend` để ở R8, khi đã bỏ màn B2C. Lúc đó Booking chỉ còn khoảng 6 nhóm trang.
- Công: R4 tăng khoảng 2 phiên (từ 1–2 lên 3–4). Không có dịch vụ AWS mới.

### TL-16: pilot cả chuỗi trên Dev với dữ liệu thật

**Trả lời.** Pilot là một agency thật (design partner) dùng sản phẩm cho việc thật trong 4–8 tuần, đổi lại họ góp ý. Pilot chạy đúng cả chuỗi anh nói:

1. Nhận lời mời và đăng nhập.
2. Khai thương hiệu, nối WordPress/Facebook của chính agency.
3. Viết lại tour AA và đăng bài.
4. Mở planner mang thương hiệu agency.
5. Nhận lead vào CRM, báo giá, lập hoá đơn cho khách.
6. Đặt tour với AA qua Agency desk.

**Thiết kế lại.** Lựa chọn này đi ngược ADR 0018 d2 và data standard C7.1a ("Dev chỉ có dữ liệu thử"). Vì vậy cần ghi một ngoại lệ có thời hạn vào ADR 0019 d16 và C7.1a:

- Chỉ 1 tenant, `kind='agency'`, có dấu pilot (feature key hoặc cột, chốt trong migration R1).
- Kéo dài tối đa 8 tuần, hoặc tới khi có `aa-prod`.
- Thư pilot ghi "môi trường thử, không SLA" kèm DPA. Câu chữ do business owner quyết.

Điều kiện kỹ thuật trước khi có PII thật:

1. AA-969 (security review CRM) xong.
2. Hook chặn agent và DB Migrate `run-script` đọc dòng PII của tenant pilot. Script chỉ in số đếm. Lý do: log CI của repo Infra là public.
3. Mọi job dọn dẹp, E2E và wave bỏ qua tenant pilot. Không chạy PITR cả instance khi chưa báo agency trước, vì PITR khôi phục cả DB của 4 app chứ không khôi phục riêng một tenant được.
4. Mỗi đêm export riêng tenant pilot bằng `crm.export_job` để có thể khôi phục từng tenant.
5. Tuỳ chọn: nâng backup RDS từ 7 lên 14 ngày (`modules/rds/main.tf` đang `backup_retention_period = 7`), ước tính dưới 1 USD/tháng. Cơ sở: backup miễn phí tới bằng tổng dung lượng DB đã cấp trong region ([RDS FAQ](https://aws.amazon.com/rds/faqs/)); phần vượt tính 0,095 USD/GB-tháng ở us-west-1 (AWS Price List API, `USW1-RDS:ChargedBackupUsage`). Với DB 20 GB, thêm 7 ngày backup tăng dần thường vượt vài GB, tức vài chục cent tới khoảng 1 USD. Đây là khoản trả phí nên cần anh đồng ý riêng.

Kế hoạch lên prod ở mục 5.

### TL-23: chuyển TripPlanner sang ECS

**Trả lời.** Làm theo đúng mẫu `aa-crm-dev-portal`: Fargate ARM sau CloudFront → VPC origin → ALB dùng chung. Hai Lambda `browse`/`assembly` giữ nguyên. Bảng chi phí ở mục 4.

- Pilot rẻ hơn Vercel Pro một chút: khoảng 16 USD trên Spot so với 20 USD.
- Khi lên khoảng 50 tenant thì ECS đắt hơn (khoảng 85–100 USD so với 20–40 USD), chủ yếu vì CloudFront tính theo GB và theo request.
- Lợi ích:
  - Mặt tiền cho tenant nằm hẳn trên AWS.
  - Bớt một bên xử lý dữ liệu (sub-processor) phải kê trong DPA.
  - Secret và log ở một chỗ.
  - Tên miền riêng dùng chứng chỉ ACM miễn phí.

**Thiết kế lại.**

- Một task 0.5 vCPU / 1 GB ARM. Dev chạy Spot. Chuyển sang on-demand khi có tenant trả tiền đầu tiên.
- Dùng một distribution CloudFront mới, tái dùng VPC origin và wildcard cert sẵn có.
- Mất Vercel BotID. Thay bằng web ACL phạm vi CLOUDFRONT: một rule rate theo IP, cộng rule Challenge trên `/api/browse/search` và `/api/trip/narrate`.
- Mất preview theo từng PR. Visual test chạy bằng `next start` trong CI.
- `vercel-cdn-cache-control` đổi sang `s-maxage`. `/photo-cdn` thành một behavior CloudFront.
- Công: khoảng 1–2 phiên, cộng vào R5 (Dockerfile standalone, `tripplanner_web.tf`, workflow deploy, CloudFront + WAF).
- Cần hai "đồng ý": Fargate (8,3–16,6 USD) và WAF (khoảng 7,4 USD; khoảng 14 USD khi tăng trưởng).
- Còn mở: CIS admin và Booking admin vẫn trên Vercel cùng team. Chưa xác nhận được gói qua API; README ghi Hobby. Hai đường: chuyển nốt hai app đó sang ECS, hoặc mua Pro 1 seat. Đây là một quyết định nhỏ, chốt sau.

---

## 2. Trả lời các ghi chú

### TL-1: "master" là gì, đặt ở đâu

Master (system of record) là nơi duy nhất được quyền sửa một loại thông tin. Nơi khác chỉ giữ bản chép tự cập nhật theo master.

Ví dụ: hôm nay agency "Lotus Travel" nằm ở 3 bản ghi, `shared.tenants`, `crm.tenant` và `booking.b2b_partners`, mỗi bản có trạng thái riêng. Staff khoá Lotus ở CIS thì Booking vẫn `active`, nên Lotus vẫn giữ chỗ tour được.

| Loại thông tin | Master | Bản chép |
|---|---|---|
| Tài khoản, trạng thái, gói, add-on, người của tenant, thông tin bên nhận hoá đơn | CIS `shared` | `crm.tenant`, `booking.b2b_partners` |
| Tiền với agency: hoá đơn, thanh toán, công nợ, hạng giá | Booking | View `booking.v_tenant_billing_status` cho CIS đọc |
| Khách cuối | `crm.traveler` của tenant | Không có |

Giữ `cis_shared` khớp cả TL-6 (đăng nhập đi qua CIS `/auth/tenant-session`) lẫn TL-9 (Booking là master về tiền).

### TL-3: vai trò làm gì

Xem mục 3 (bảng vai trò và ma trận quyền).

### TL-7: một lời mời, một đăng nhập, add-on mở theo gói

Anh hiểu đúng. **Lời mời là cho người, còn gói là cho tenant.**

1. Staff tạo tenant (một thao tác), rồi mời owner ở Tenant 360.
2. Owner nhận mail `/join`, tạo tài khoản partner pool + MFA, rồi vào thẳng Content.
3. Owner mời đồng nghiệp ở Account › Team: một form gồm e-mail + vai trò Content. Ô vai trò CRM chỉ hiện khi tenant có `crm.core`.
4. Bật CRM:
   - Owner bấm "Request CRM", account manager duyệt.
   - CIS ghi entitlement, và CRM tự tạo `crm.tenant`.
   - Owner bấm "Kích hoạt CRM" một lần. Thao tác này giữ ADR 0006b d4: sự kiện của CIS không tự cấp vai trò CRM.
   - Sau đó owner gán vai trò CRM cho người đã có trong Team, không cần mời lại.
5. TripPlanner mở theo entitlement `tp.*` và dùng vai trò Content.

Kết quả: mỗi người có 1 tài khoản và 1 lần đăng nhập. Dữ liệu vai trò vẫn ở 2 bảng, `shared.tenant_members.content_studio_role` và `crm.member.role`, mỗi app giữ bảng của mình.

### TL-8: lấy gì từ Booking cho CRM, CRM còn thiếu gì

| Việc | Đề xuất |
|---|---|
| Thanh toán tay có maker-checker, bắt chứng từ, chặn trùng số tham chiếu (Booking `payments_maker_checker_chk`) | Port sang `crm.payment`, tuỳ chọn theo tenant |
| Ba check trước khởi hành (`pre_trip_recheck`, `emergency_contact`, `insurance`) | Port dạng dữ liệu: mẫu workflow seed sẵn task |
| Cảnh báo "chưa trả đủ" ở stage `pre_departure` | Lát nhỏ |
| Khách trả thẻ online | **Ưu tiên 1:** Stripe Connect trên tài khoản của chính agency (BYO). AA không cầm tiền. Hôm nay `stripe` trả 409 `provider_not_available`. Cần kiểm điều khoản Connect trước |
| Lịch trình nhiều ảnh, xuất PDF | **Ưu tiên 2:** kéo ảnh và atom CIS vào proposal. Đây là lợi thế riêng vì Content là gói nền |
| PWA mang thương hiệu tenant | Khi có brand token runtime |
| Chia hoa hồng cho từng advisor, xuất CSV kế toán | Làm sau |

Đối chiếu thị trường: Tern, TravelJoy, Safari Portal. Nguồn ở mục 8.

### TL-10: bốn cách giao TripPlanner, một repo cho nhiều tenant

| Cách | Khách thấy | Agency phải làm | Khi nào |
|---|---|---|---|
| (a) Path `/{slug}` + nút launcher | `planner.<miền AA>/acme/plan` | Dán một link | Bản đầu (R5) |
| (d) Subdomain / tên miền riêng | `plan.acme.com` | Thêm 1 CNAME | Khi có tenant trả tiền (ACM miễn phí trên ECS) |
| (b) iframe nhúng | Planner nằm trong trang của agency | Dán `<iframe>` | Sau (d). Cần mở `frame-ancestors` theo tenant |
| (c) API headless | Giao diện agency tự làm | Có lập trình viên | Cuối cùng, theo yêu cầu (xem TL-6) |

Một repo phục vụ nhiều tenant theo cách sau:

1. `proxy.ts` đọc slug (sau này đọc Host) rồi tra view (mới) `catalog.v_tenant_tripplanner_v1`. View trả về theme, locale, entitlement, đích gửi lead và origin được phép.
2. Theme của tenant ghi đè biến `--aa-*` của kit. Vẫn một kit duy nhất.
3. BFF ký `tenant_id` gửi sang Lambda. Bảng `tripplanner.*` có `tenant_id NOT NULL` + FORCE RLS.
4. Danh mục tour lấy từ view (mới) `catalog.v_tenant_tour_v1`: chỉ tour AA còn live.

Khác biệt giữa các tenant là dữ liệu, không phải code.

**An toàn nhất** là (a): cookie first-party, không cho nhúng. **Tốt cho SEO của agency** là (c) và (d).

### TL-11: khách xem lại và đặt tour thế nào khi AA không giữ dữ liệu khách

1. Khách lên kế hoạch dưới dạng khách ẩn danh. Cookie `guest_token_hash` không chứa tên hay e-mail.
2. Bấm "Request this trip" và nhập tên, e-mail. Dữ liệu đi qua `lead.submitted.v1` vào CRM của tenant, hoặc qua webhook/e-mail tới hệ thống của tenant. Bản ở TripPlanner chỉ giữ tới khi giao xong.
3. Khách quay lại bằng link client portal `/c/t/<token>` do agency gửi. Ở đó khách xem proposal, chấp nhận, ký, đặt cọc qua Stripe của agency.
4. Agency đặt dịch vụ của AA qua `booking.b2b.v1`. API này chỉ mang số khách theo nhóm tuổi, không mang tên.
5. Khi đi tour, AA cần danh sách tên. Danh sách lấy từ `crm.ops_release`, niêm phong theo khoá của agency và xoá sau khi tour kết thúc + 90 ngày.

Tóm lại: dữ liệu khách nằm trong CRM của tenant (tenant là controller). AA chỉ vận hành hệ thống (processor) và chỉ thấy đúng phần tối thiểu để chạy tour.

Còn thiếu: tenant không có CRM mà đặt qua "Book with AA" (TL-17) thì chưa có đường gửi danh sách khách. Việc này đưa vào R4.

### TL-19: AI notice là gì

- **Phần người đọc thấy (EU AI Act Art. 50(1)):** đã làm xong. Component kit `AiNotice` đã merge ở CIS #1235, Partner #185 và TripPlanner #210. Nó hiện một dòng chữ nhỏ dưới nội dung do AI tạo.
- **Còn lại là phần máy đọc (Art. 50(2)):** một nhãn ẩn mà phần mềm khác đọc được. Cụ thể là `ai_generated`, `model`, `generated_at` trong JSON `/v1/*` và trong file export CIS, cộng một thẻ `<meta>` trên trang WordPress đã đăng. Thêm badge "AI-assisted" trong Content studio.
- Hạn **02/12/2026**. Hạn này lấy từ nguồn thứ cấp về thoả thuận AI Omnibus, luật sư nên kiểm. Công khoảng 1 phiên, 0 USD.

### TL-20: báo tenant qua đâu

Báo qua cả hai kênh.

- **Trong portal:** đã có. `services/tour_lifecycle/service.py` ghi `tour.discontinued` vào `shared.notifications` và hiện ở chuông.
- **E-mail qua SES (thêm):**
  - Gửi ngay khi tour `retired` mà tenant còn trang hoặc bài đang live. Các trường hợp còn lại gom vào digest hằng ngày.
  - Gửi cho owner và thành viên content.
  - Nội dung: tên tour, ngày ngừng, những gì hệ thống đã tự làm, ngày trang WordPress chuyển về draft, danh sách bài Facebook họ nên tự sửa, tour thay thế nếu có.
  - Tour `restored` có thư báo bán lại. Tour `paused` không báo.
  - Viết theo lời nội dung, không có chữ "flag/QA".

### TL-21: AA subject gate là gì

Gate là một bước kiểm bằng luật, không gọi AI nên miễn phí. Nó chạy lúc tạo bài và trước khi đăng, và kiểm hai điều:

1. Bài có gắn ít nhất một tour AA còn live hoặc một place AA không. Bài thương hiệu không có lời mời mua (ví dụ "Giới thiệu đội ngũ") thì được qua.
2. Mọi link "Book now" có trỏ tới trang tour AA hoặc site TripPlanner của tenant không.

Ví dụ: bài "Top 5 Mekong" có link sang `congtykhac.com/mekong-tour` sẽ bị giữ ở Tenant QA › Compliance. Tenant chỉ thấy: "Bài này dẫn tới một tour không có trong danh mục Adventure Asia; đổi link để đăng."

Mục đích: hợp đồng (BO-6, BO-7) chỉ cho bán tour AA. Không có gate thì nền tảng và tiền AI của AA bị dùng để quảng cáo tour của đối thủ.

### TL-22: làm sẵn thêm ngôn ngữ

Làm được sau R5. Công không nằm ở dịch mà ở việc duy trì bản dịch.

| Việc | Công |
|---|---|
| Đưa chữ cứng của Content studio vào catalogue. Studio chưa có i18n, khoảng 11,6k dòng TSX. Làm cùng đợt gộp TL-6 | 2–3 phiên, trong R3 |
| Mở kit từ `"en" \| "vi"` sang N ngôn ngữ | khoảng 1 phiên |
| Mỗi ngôn ngữ thêm (dịch máy qua gateway + test đủ key) | khoảng 0,5 phiên + vài USD token (cần đồng ý riêng) |
| Người bản ngữ duyệt, và dịch mọi chuỗi mới | Kéo dài mãi |

Thứ tự đề xuất: Đức, Pháp, rồi Tây Ban Nha, rồi Nhật, Hàn. Tốt nhất là theo ngôn ngữ của 3–5 agency tiềm năng đầu tiên.

Lưu ý: ngôn ngữ giao diện khác ngôn ngữ nội dung bài viết. Nội dung bài viết là pipeline riêng, tính phí theo tour.

### BO-4: "chỉ nhúng hoặc API, AA không lưu gì" có đúng không

Đúng một phần. Nhúng hay API thì AA vẫn phải chạy planner, catalogue, AI và bản đồ. Điều AA tránh được là giữ PII khách lâu dài.

| Cách giao | AA lưu gì |
|---|---|
| Trang hosted / nhúng | Kế hoạch ẩn danh có hạn xoá (đề xuất 30 ngày); lead chỉ giữ tới khi giao |
| API không trạng thái | Gần như không lưu gì, chỉ log gọi API |
| Lead vào CRM add-on | PII trong `crm.traveler`. Tenant là controller, AA là processor |

Vẫn phải quản các chỗ sau:

- IP trong log CloudFront/ALB: đặt thời hạn giữ log.
- Chat tự do có thể chứa PII: phải qua scrubber trước khi gọi model.
- Sentry: không ghi PII.

Muốn "AA không giữ gì" tuyệt đối thì phải chọn API không trạng thái + chỉ webhook. Đây là quyết định sản phẩm và pháp lý của business owner, có thể bán thành một gói riêng.

### BO-7: 7 ngày điều chỉnh sau

- Hôm nay chưa có chỗ nào lưu con số này.
- Trong R1: lưu dòng `policy.notice_days = 7` trong `shared.plan_feature` (mới). Ghi đè theo tenant bằng `shared.tenant_entitlement_override` (mới). Mỗi lần đổi ghi vào `shared.tenant_account_event` (mới). Cả ba bảng chưa có trong dump live, chúng thuộc migration R1.
- Mỗi thông báo lưu `due_at` lúc gửi. Nhờ vậy, đổi số ngày sau này không làm ngắn hạn của các thông báo đã gửi.
- Lên prod thì đổi số trên trang Plans, không cần deploy.

### BO-8: cân nhắc phương án 3 (bật ở gói thấp)

- Kỹ thuật như nhau cho cả ba phương án: một cờ gắn với entitlement `tp.branding`. Nên xây cờ ngay trong R5, mặc định tắt. Khi chốt bảng giá BO-4 thì chỉ đổi cấu hình.
- Nếu bật ở gói thấp: chữ nhỏ ở footer, `rel="nofollow"`, không đặt trong khung chat AI.
- Được: có lý do để agency nâng gói.
- Mất: gói thấp không còn white-label trọn vẹn.
- Business owner quyết.

### BO-10: pháp nhân Úc

Ghi nhận. Không phải dựng lại gì về kỹ thuật, chỉ là cấu hình: `billing_entity`, tên pháp nhân trên DPA và hoá đơn, `contract_version`.

Câu hỏi cho luật sư và kế toán Úc:

1. AA Úc đã có ABN và đăng ký GST chưa?
2. Dịch vụ cung cấp cho agency nước ngoài có được GST-free không ([ATO](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/gst-cross-border-transactions-between-businesses))?
3. Doanh nghiệp có thuộc diện miễn của Privacy Act (≤ 3 triệu AUD) không? Cải cách Tranche 2 có thể bỏ miễn trừ này.
4. Kỹ sư ở Việt Nam truy cập dữ liệu thì cần hợp đồng nội bộ gì? (APP 8, [OAIC](https://www.oaic.gov.au/privacy/australian-privacy-principles-guidelines/chapter-8-app-8-cross-border-disclosure-of-personal-information/); Nghị định 356/2025)
5. Tenant EU vẫn cần SCC + TIA, và câu hỏi đại diện EU theo Art. 27 còn áp dụng không?

### BO-14: hệ thống mình có tự làm được không

Phần lớn tự làm được trong Booking, 0 USD:

- tạo hoá đơn định kỳ;
- PDF;
- gửi e-mail;
- nhắc nợ;
- tự chuyển past_due → suspend qua CIS.

Phần không tự làm được là **hoá đơn VAT hợp pháp ở Việt Nam**. Theo Nghị định 70/2025, hoá đơn này phải đi qua phần mềm hoá đơn điện tử nối với cơ quan thuế ([PwC](https://www.pwc.com/vn/vn/publications/2025/250416-changes-to-invoicing-regulations.pdf)).

Giai đoạn đầu, kế toán phát hành trên phần mềm AA đang dùng rồi dán số vào `e_invoice_no`. Khi số hoá đơn mỗi tháng nhiều, nối API của chính nhà cung cấp đó (ví dụ [MISA meInvoice](https://doc.meinvoice.vn/about)), khoảng 1 phiên.

Stripe không mở cho pháp nhân Việt Nam ([Stripe global](https://stripe.com/global)). Stripe Billing chỉ cân nhắc nếu AA Úc xuất hoá đơn. Phí 0,7% doanh thu ([pricing](https://stripe.com/billing/pricing)), và cần một "đồng ý" riêng.

### BO-15, BO-16, BO-17: điều chỉnh sau được

| Tham số | Hôm nay | Sau R4 |
|---|---|---|
| Biên B2B, tỷ giá, giá net theo mùa, phí huỷ | `booking.pricing_rules`, `fx_rates`, `supplier_rates`, `cancellation_policies`, có maker-checker | Giữ nguyên, đổi trên trang |
| Ba hạng 0/3/6% | Chưa có (AA-1030) | (mới) `booking.partner_tier` |
| Cọc 30%, số dư trước 30 ngày, công nợ, hạn mức | Chỉ áp cho B2C; `credit_terms_ref` là chữ tự do | (mới) `booking.partner_terms`, khoá trên hold lúc confirm |
| RRP = net + 25% | Chưa có (AA-1029) | Cột (mới) `rrp_markup_pct` trên `pricing_rules` kênh `b2b` |
| Giữ chỗ 48h và các thời hạn ops | `booking.settings`, trang chỉ đọc | Trang Settings sửa được, có maker-checker |
| Thuế, mẫu hoá đơn (BO-17) | Chưa có | (mới) `booking.tax_rule` + `billing_entity`; chữ chân hoá đơn là dữ liệu theo `tax_rule` |

Sau R4, business owner đổi số trên trang, người thứ hai duyệt, không phải sửa code. Phần còn cứng trong code (B2B không cộng phụ phí mùa cao điểm, bước làm tròn) được ghi rõ trong CONTEXT.md của Booking.

### BO-19: "theo thiết kế"

Ghi nhận, không có gì thay đổi. Trần 150 USD/tháng và mức AI kèm gói được lưu thành dữ liệu theo feature key `ai.budget_usd_monthly` (TL-2), nên đổi số không cần code.

---

## 3. Vai trò nhân viên AA và ma trận quyền (TL-3, TL-4, TL-5, BO-13)

Mỗi người giữ một vai trò CIS, vì code hiện tại lấy "nhóm cao nhất thắng" (`GROUP_ROLES`, `shared.admin_users.role`). Vai trò được thiết kế lồng nhau: `content_lead` chứa quyền của `content` và `tenant_qa`, còn `customer_success` chứa quyền của `support`.

| Vai trò | Ai (team nhỏ) | Việc hằng ngày | Không được |
|---|---|---|---|
| `admin` | Tech lead, business owner (`is_owner`) | Cấu hình, sự cố, giao tenant, quản lý nhân viên | Không giới hạn; mọi thao tác nhạy cảm đều ghi audit |
| `content_lead` | 1 người phụ trách nội dung | Wave, review queue, master content, atom/ảnh, SEO | Xem danh bạ tenant, tiền, AI spend |
| `content` (gộp `reviewer`) | 1–3 writer | Upload, S1 rewrite, sửa và duyệt bản viết | Ngừng/xoá tour master, sửa atom, xem tenant |
| `tenant_qa` | Kiêm bởi content_lead | Xem bài tenant bị held, gắn nhãn, sửa place card, Content Trace | Tenant 360, view-as, tiền |
| `customer_success` | Account manager, 5–25 tenant | Sức khoẻ tenant của mình, trial, gợi ý add-on, lời mời, ghi chú | Tenant của người khác, hoá đơn, offboard |
| `support` | Kiêm bởi CSM, sau này tier 1 | Gửi lại lời mời, reset MFA, view-as chỉ đọc | Đổi gói, billing, PII khách khi chưa có `support_grant` |
| `finance` | Kế toán part-time | Phát hành hoá đơn trong Booking, ghi thanh toán, tạm ngưng vì nợ | Nội dung tenant, thành viên, view-as |
| `ai_ops` | Tech lead hoặc 1 kỹ sư | Routing model, ngân sách AI, Writing Lab | Danh bạ, Tenant 360, billing |
| `viewer` | E2E, Preview | Smoke test | Mọi thao tác ghi |

**Ma trận** (W = đọc và ghi, R = chỉ đọc, – = không):

| Khu vực | admin | content_lead | content | tenant_qa | customer_success | support | finance | ai_ops |
|---|---|---|---|---|---|---|---|---|
| Tenants directory | W | – | – | – | R (của mình) | R (của mình + pool) | R (cột billing) | – |
| Tenant 360 | W | – | – | – | W (của mình, trừ billing) | R + thao tác thành viên | R (tab Billing) | – |
| Gói / hoá đơn (Booking) | W | – | – | – | R (gói, add-on) | – | W | – |
| AA Catalogue | W | W | R + W bản viết | R | – | – | – | R |
| Tenant QA | W | W | – | W | R (của mình) | – | – | R |
| AI & spend | W | – | – | – | R (tenant mình) | – | R (số tiền) | W |
| Writing Lab | W | R | – | R | – | – | – | W |
| Nhân viên | W (cần owner) | – | – | – | – | – | – | – |
| View-as (chỉ đọc, ≤ 60 phút) | R | – | – | – | R (của mình) | R (của mình + pool) | – | – |

**"Mỗi manager chỉ thấy tenant của mình":**

- Bảng (mới) `shared.staff_tenant_assignment` ghi quan hệ `owner`, `backup` hoặc `support`, mỗi tenant đúng một `owner`.
- Mọi route `{tenant_id}` qua dependency `require_tenant_scope`. Ai gọi thẳng API vào tenant không thuộc mình cũng nhận 403.
- Có CI test bắt mọi route đó phải dùng dependency, và probe kiểm: CSM A gọi tenant của CSM B phải nhận 403.
- Tenant gói nhỏ hoặc chưa có người phụ trách nằm trong view "Pool" mà mọi `support` đều thấy.

**Phải sửa trong code (R2):**

- `tenant.read` hôm nay gác ba thứ: danh bạ, text của tenant và kho atom. Tách thành `tenant.read`, `tenant_content.read` và `catalog.read`.
- "GET không có entry trong POLICY thì mở cho mọi vai trò": với 8 vai trò, mọi GET có `{tenant_id}` phải có entry.
- `PATCH /admin/tenants/{tenant_id}` kiểm theo trường: `finance` chỉ sửa trường billing.
- Cognito group mới có precedence trong khoảng 10–39 (Booking bắt đầu từ 40). `cis-reviewer` giữ làm alias một release.

**Cần anh chọn:** Writing Lab có text tenant. Đề xuất cho `ai_ops` quyền `tenant_content.read`, chỉ dùng trong Lab, có ghi log. Cách còn lại là che text tenant với `ai_ops`.

**Vai trò phía tenant** (sửa theo TL-6: owner không còn "xoay API key"):

| Vai trò | Content (`content_studio_role`) | CRM (`crm.member.role`) | Gói, thành viên |
|---|---|---|---|
| owner | `owner` | `owner` | Nâng/hạ gói, mời, xoá, đổi vai trò, cấp `support_grant` cho AA |
| agent | `editor` | `agent` (thấy margin) | Không |
| assistant | `viewer` | `assistant` (không thấy tiền, RLS crm-014) | Không |
| admin (để sau) | Như owner trừ billing | Phải thêm giá trị vào `member_role_chk` | Mời, trừ owner |

---

## 4. Chi phí hosting TripPlanner (TL-23)

Giả định:

- Pilot: 3 tenant, khoảng 5 nghìn lượt/tháng, 15 GB, 0,5 triệu request.
- Tăng trưởng: khoảng 50 tenant, 100 nghìn lượt, 300 GB, 10 triệu request.
- Fargate ARM us-west-1: 0,03725 USD/vCPU-giờ, 0,00409 USD/GB-giờ (AWS Price List API).
- CloudFront Asia: 0,12 USD/GB. Tính trường hợp xấu nhất: không còn free tier vì free tier tính theo payer.
- Fargate Spot không có bảng giá cố định. Trang [Fargate pricing](https://aws.amazon.com/fargate/pricing/) chỉ ghi "up to a 70% discount", và giá Spot thay đổi theo thời gian. Các số Spot dưới đây giả định giảm khoảng 70%: 16,6 × 0,3 ≈ 5 USD (0.5 vCPU/1 GB) và 8,3 × 0,3 ≈ 2,5 USD (0.25/0.5). Đây là ước tính, không phải giá niêm yết.
- WAF phạm vi CLOUDFRONT ([WAF pricing](https://aws.amazon.com/waf/pricing/) và AWS Price List API): web ACL 5 USD + 2 rule × 1 USD + 0,60 USD mỗi triệu request + Challenge 0,40 USD mỗi triệu challenge response (`ChallengeServed`; tính cả khi người dùng không làm challenge). Pilot (0,5 triệu request, khoảng 0,1 triệu challenge): 5 + 2 + 0,30 + 0,04 ≈ **7,4 USD**. Tăng trưởng (10 triệu request, khoảng 2 triệu challenge): 5 + 2 + 6 + 0,8 ≈ **14 USD**. Chỉ dùng Challenge (im lặng), không dùng CAPTCHA (0,40 USD mỗi nghìn lần).
- Web ACL hôm nay (`identity.tf`, `modules/waf`) đều là `REGIONAL`, nên web ACL CLOUDFRONT là tài nguyên mới, có phí mới.

| Phương án | Pilot USD/tháng | Tăng trưởng USD/tháng | Ghi chú |
|---|---|---|---|
| Vercel Pro (1 seat) | 20 | 20–40 | Gồm 1 TB, 10 triệu request, BotID Basic miễn phí. Tenant-facing trên nhà cung cấp ngoài AWS |
| **ECS Fargate Spot + CloudFront WAF (chọn cho Dev)** | **~16** | — | 0.5 vCPU/1 GB, Spot khoảng 5 (ước tính, giảm ~70%); CloudFront khoảng 2,4; WAF khoảng 7,4; phụ khoảng 1 |
| ECS Fargate on-demand + WAF (prod) | ~28 | ~85–100 (2 task) | Pilot: compute 16,6 + CloudFront 2,4 + WAF 7,4 + phụ 1. Tăng trưởng: compute 33 + CloudFront 300 GB × 0,12 = 36 + request khoảng 10–12 + WAF khoảng 14. Phần lớn chênh lệch là CloudFront và WAF, không nhỏ. Không WAF thì pilot khoảng 20 |
| ECS không WAF (Spot / on-demand) | ~9 / ~20 | — | Không khuyến nghị cho mặt tiền công khai |
| Amplify Hosting | ~26 | ~90+ | Dịch vụ mới, không có VPC origin, Next 16 chưa kiểm. Không khuyến nghị |
| S3 + CloudFront static | — | — | Không khả thi: BFF, cookie HttpOnly, ISR và SSR theo tenant cần server |
| OpenNext trên Lambda | ~0–5 | thấp | Adapter không chính thức, thêm S3/SQS/DynamoDB. Vận hành nặng |

Nguồn: [Fargate](https://aws.amazon.com/fargate/pricing/), [WAF](https://aws.amazon.com/waf/pricing/), [CloudFront](https://aws.amazon.com/cloudfront/pricing/), [CloudFront flat-rate (VPC origin chỉ từ gói Business 200 USD)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/flat-rate-pricing-plan.html), [Amplify](https://aws.amazon.com/amplify/pricing/), [Vercel](https://vercel.com/pricing). Tất cả truy cập 03/11/2026.

Lưu ý: comment trong `crm_portal.tf` ghi khoảng 7,2 USD cho task 0.25/0.5. Theo giá us-west-1 thì đúng là khoảng 8,3 USD.

---

## 5. Kế hoạch lên prod (TL-16, ADR 0018 + ADR 0012 d9–d11)

| Pha | Việc | Phiên |
|---|---|---|
| P0 (0 USD, làm sớm, lane song song) | Tách `modules/environment` bằng `moved` block (plan Dev không đổi); workflow Deploy Prod; DB Migrate `environment=prod` | 2 |
| P1 | Business owner chốt ngày go-live (BO-18); tech lead đồng ý một con số chi phí tháng đã đối chiếu | — |
| P2 | Tạo account `aa-prod`, OU Prod + 3 SCP, Identity Center (agent không có role prod), quota, state bucket, OIDC | 1 |
| P3 | `accounts/prod`: VPC 2 AZ (1 NAT), RDS Multi-AZ `db.t4g.medium` + CMK, ECS (api 2 task, TripPlanner on-demand), ALB, API GW, WAF, Cognito prod, SES production access, ACM | 2 |
| P4 Dữ liệu | Seed content theo allow-list. Chuyển tenant pilot bằng export/import theo tenant, giữ ID, so số đếm, rồi xoá bản Dev theo erasure (DRY RUN trước) | 2 |
| P5 Gate (ADR 0012 d11) | Diễn tập restore có ghi RTO; cảnh báo + kênh thứ hai; 2 SLO mỗi API; xoay secret; đóng mục "before prod" của AA-873; AA-969; kiểm thử xâm nhập (BO-18) | 2 |
| P6 Cut-over | Khoá ghi tenant trên Dev, export/import, đổi host. Người dùng agency đăng ký lại vì Cognito không chuyển pool được, và nối lại WordPress/Facebook vì credential mã hoá bằng khoá Dev. Theo dõi 7 ngày, báo cáo chi phí 7 ngày | 1 |

- Tổng khoảng 8–10 phiên, tức 3–4 tuần lịch.
- RPO ≤ 15 phút (mất instance) và ≤ 24 giờ (mất region). RTO ≤ 1 giờ và ≤ 4 giờ. PITR 14 ngày, backup sao sang us-west-2, diễn tập mỗi quý.
- Chi phí (S258): 410–580 USD/tháng giá niêm yết, 280–410 USD/tháng có tiết kiệm. Cộng 0–110 USD/tháng dịch vụ bảo mật, mỗi khoản cần đồng ý riêng.
- Kế hoạch test pilot đi theo 6 bước ở TL-16. Mỗi bước có tiêu chí qua và bằng chứng: ảnh và số đếm, không có PII trong báo cáo.

---

## 6. Lộ trình thay đổi

| Pha | Trước | Sau khi duyệt | Vì |
|---|---|---|---|
| R0 | ADR 0019, flag tắt B2C | Thêm: ADR 0019 ghi 4 lựa chọn khác; ghi chú ngoại lệ C7.1a; kiểm `audit_log` xem còn ai gọi `/auth/tenant-login` | TL-6, TL-16 |
| R1 | Control plane | Thêm: trường bên nhận hoá đơn trên `shared.tenants`; dấu pilot; `policy.notice_days`; `bk_tenant_pull` tạo `b2b_partners` cho **mọi** tenant; view billing hai chiều | TL-9, TL-16, BO-7 |
| R2 | Vai trò + scope (S270–S271) | Giữ nội dung. Thêm `finance` cho Booking: migration **CIS** trên `shared.staff_app_grant` (`staff_app_grant_role_chk`), group `booking-finance` trong Infra `identity.tf`, Booking map vai trò. Chạy lane song song với R3 (khoảng S269–S271). Phải xong trước khi CRM pilot có PII thật, cùng AA-969 | TL-9, TL-16 |
| R3 | Portal shell, 2 phiên | **Khoảng 6–7 phiên công**: gộp `portal/` vào `web/` và xoá đường key (3), i18n studio (2–3, lane song song), phần portal shell cũ còn lại sau khi gộp (khoảng 1: Content là home, app switcher, "Request add-on"). Chạy 2 lane nên chiếm slot S268–S272. i18n không chặn mốc pilot 1 | TL-6, TL-22 |
| R4 | Booking chỉ B2B, 1–2 phiên | **Khoảng 3–4 phiên**: `agency_invoice` (saas + settlement), payment, sequence, tax_rule, billing_entity, partner_tier/terms, Settings sửa được, đường danh sách khách cho "Book with AA"; nav "Trade" trong AA Admin | TL-9, BO-14..17, TL-11 |
| R5 | TripPlanner tenancy, 3–4 phiên, cần Vercel Pro | **Khoảng 4–6 phiên**: thêm chuyển sang ECS (Dockerfile, Terraform, deploy, CloudFront WAF, bỏ BotID), cờ `tp.branding`. Không cần Vercel Pro cho TripPlanner | TL-23, BO-8 |
| Pilot | ~S270, chỉ Content | Pilot cả chuỗi theo hai mốc: Content + CRM sau R1 + R3 + R2 + AA-969 (khoảng S272); TripPlanner vào sau R5 (khoảng S277). Tối đa 8 tuần hoặc tới `aa-prod` | TL-16 |
| Prod | Khi có ngày go-live | P0 làm sớm (lane song song, 0 USD); P2–P6 khi BO-18 chốt ngày, trước tenant trả tiền đầu tiên | TL-16 |
| R6 | Admin IA + Lab | Thêm e-mail SES (thư ngay + digest) cho tour ngừng. SES đã dùng trên acc2 (`ses.tf`), nên chỉ thêm phí gửi: 0,10 USD mỗi 1.000 thư ([SES pricing](https://aws.amazon.com/ses/pricing/)), vài cent mỗi tháng ở quy mô pilot | TL-20 |
| Hạn cố định | AI notice | Còn phần metadata máy đọc, trước 02/12/2026 | TL-19 |
| R7 | TripPlanner UX | Preview bằng `next start` trong CI thay cho preview Vercel | TL-23 |
| R8 | Có "gộp portal vào web", "subdomain (Vercel Pro)" | Bỏ "gộp portal" (đã lên R3). Subdomain/tên miền riêng dùng ACM trên CloudFront. Thêm: gộp màn Booking vào AA Admin; API máy cho agency khi có yêu cầu; ngôn ngữ thêm sau R5 | TL-6, TL-9, TL-23, TL-22 |

Tổng R0–R8 khoảng 32–39 phiên, trước đây là 25–30 (R3 +4–5, R4 +2, R5 +1–2). Kế hoạch prod (8–10 phiên, mục 5) tính riêng.

**Slot mới (thay bảng 11.1 của README):**

| Slot | Việc |
|---|---|
| S265 | R0; khép gateway In Review; AA-820 |
| S266–S268 | R1 (AA-1028) |
| S268–S272 | R3: gộp + xoá key S268–S270; i18n studio lane song song S269–S272 (+AA-1007, AA-1008) |
| S269–S271 | R2 + `finance` (lane song song), AA-969 |
| ~S272 | **Pilot mốc 1:** Content + CRM (sau R1, R3 phần gộp, R2, AA-969) |
| S271–S274 | R4 (+AA-1029, AA-1030) |
| S272–S277 | R5 (gồm chuyển sang ECS) |
| ~S277 | **Pilot mốc 2:** TripPlanner |
| S277–S280 | R7 |
| Lane song song | R6 (+e-mail SES); TL-19 trước 02/12/2026; P0 của kế hoạch prod |

---

## 7. Còn cần anh chốt

1. `ai_ops` có được đọc text tenant trong Writing Lab không (mục 3)?
2. CIS admin và Booking admin trên Vercel: mua Pro 1 seat, hay chuyển sang ECS theo mẫu TripPlanner?
3. Hai "đồng ý" cho TL-23: Fargate (8,3–16,6 USD/tháng) và CloudFront WAF (khoảng 7,4 USD/tháng ở pilot, khoảng 14 USD khi tăng trưởng). Tuỳ chọn thêm: backup RDS 14 ngày (dưới 1 USD/tháng).
4. "Không dùng key": xác nhận M2M giữa các app AA được giữ, và API máy cho agency để R8.

## 8. Nguồn ngoài (truy cập 03/11/2026)

- AWS: [Fargate](https://aws.amazon.com/fargate/pricing/) · [WAF](https://aws.amazon.com/waf/pricing/) · [WAF CAPTCHA và Challenge](https://docs.aws.amazon.com/waf/latest/developerguide/waf-captcha-and-challenge.html) · [CloudFront](https://aws.amazon.com/cloudfront/pricing/) · [CloudFront flat-rate](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/flat-rate-pricing-plan.html) · [Amplify](https://aws.amazon.com/amplify/pricing/) · [Cognito](https://aws.amazon.com/cognito/pricing/) · [SES](https://aws.amazon.com/ses/pricing/) · [RDS FAQ (backup miễn phí)](https://aws.amazon.com/rds/faqs/) · AWS Price List API (`get-products`: AmazonECS, AmazonRDS, awswaf; us-west-1 / Global)
- [Vercel](https://vercel.com/pricing)
- Stripe: [Stripe Billing](https://stripe.com/billing/pricing) · [Stripe global](https://stripe.com/global)
- Hoá đơn điện tử Việt Nam: [PwC Nghị định 70/2025](https://www.pwc.com/vn/vn/publications/2025/250416-changes-to-invoicing-regulations.pdf) · [EY](https://www.ey.com/vi_vn/technical/tax/tax-and-law-updates/tin-nhanh-ve-thue-thang-4-nam-2025-nhung-thay-doi-ve-hoa-don-chung-tu-ap-dung-tu-ngay-1-thang-6-nam-2025) · [MISA meInvoice API](https://doc.meinvoice.vn/about)
- Úc: [ATO GST cross-border](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/gst-cross-border-transactions-between-businesses) · [OAIC APP 8](https://www.oaic.gov.au/privacy/australian-privacy-principles-guidelines/chapter-8-app-8-cross-border-disclosure-of-personal-information/)
- EU AI Act: [Matheson AI Omnibus](https://www.matheson.com/insights/eu-legislators-reach-agreement-on-ai-digital-omnibus-regulation/) · [techUK](https://www.techuk.org/insights/news/eu-ai-omnibus-deal-reached-more-clarity-on-ai-act-obligations)
- Sản phẩm thị trường: [Tern](https://tern.travel/agencies) · [Safari Portal](https://www.safariportal.app/features) · [TravelJoy review](https://saascrmreview.com/?p=17427)
