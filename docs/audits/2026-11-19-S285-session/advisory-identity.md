# Tên người trong hệ sinh thái: thiết kế chung thay cho bản vá riêng CRM

## 1) Trả lời ngắn

Không nên làm một "kho hồ sơ người dùng" trung tâm. Cũng không nên nhân rộng cách lấy phần e-mail trước "@" ra làm tên. **Khuyến nghị:** mỗi app giữ một cột `display_name` trên bản ghi người của chính nó. Phần dùng chung chỉ gồm **một chuẩn dữ liệu**, **một component `PersonLabel` trong kit** và **thuộc tính Cognito `name` chuẩn, chỉ ghi một lần lúc tạo tài khoản**. Đây cũng là nguyên tắc nên dùng cho câu hỏi về gateway: gom luật và code về một chỗ, không gom dữ liệu hay runtime về một service mà mọi trang phải gọi tới. Chi phí AWS 0 USD/tháng, khoảng 6–8 ngày công.

## 2) Hiện trạng (đã kiểm)

- **Thành viên đại lý không có tên ở bất cứ đâu.** `crm.member` chỉ có `(cognito_iss, cognito_sub)`, role và status (`docs/architecture/db-schema-reference.md:7501-7515`). `shared.tenant_members` cũng không có tên hay e-mail (`:14124-14138`). Data standard đã duyệt ở S283 giữ nguyên như vậy (`docs/architecture/data-standards/02-data-management.md:309`).
- **Staff:** chỉ CIS có `shared.admin_users.display_name`, nhưng không có đường sửa sau khi tạo (`apps/AA-CIS-App/api/services/staff_directory.py:560-562`; route PATCH duy nhất là `/staff/{id}/roles`, `api/routers/admin_platform.py:244`). Booking tự lấy phần e-mail trước "@" làm tên vì access token không mang tên (`apps/AA-Booking/backend/app/auth/staff.py:363-368`).
- **Cognito `name`** là thuộc tính chuẩn, client được phép ghi (`infra/AA-CIS-Infra/accounts/aa365/identity_partner.tf:199-200`), nhưng chưa ai ghi. Cả hai lệnh AdminCreateUser chỉ truyền `email` (`apps/AA-Partner/api/app/members/directory.py:159-165`, `staff_directory.py:426`). Pre-token trigger của WORKFORCE chỉ thêm `email` vào access token (`lambda_src/identity_triggers/workforce.py:283`). Partner pool ở tier ESSENTIALS và không có trigger nào (`identity_partner.tf:99`).
- **Bản vá S285 (AA-1129, chưa merge):** mỗi lần gọi GET /members, API giải mã e-mail lời mời của mọi thành viên qua vault và ghi một audit event. Ghi chú của AA-1129 tự nhận cần migration crm và đổi guard crm-008 (`docs/implementation-notes/AA-1129-l2-pr2.md:8-14`).
- **Content studio** hiện "Member ab12·cd34·ef56". `member_ref` = `sha256(iss|sub)[:12]` (`apps/AA-CIS-App/services/tenant_membership/writer.py:66-69`), nên CRM tính lại được giá trị này.
- **Khách du lịch** có hai kiểu tên: một chuỗi `name` tự do trong lead (`docs/contracts/lead.submitted.v1.openapi.yaml:172-182`), và bộ given/family/display trong `crm.traveler` (`db-schema-reference.md:9797-9831`).

## 3) Các phương án

| Phương án | Cách làm | Lợi | Hại | Công sức/chi phí |
|---|---|---|---|---|
| **A. Giữ fallback e-mail** | Merge S285, gom fallback vào kit | Nhanh, không cần migration hay ADR | "lan.nguyen" không phải tên thật và người dùng không sửa được. Giải mã PII trên mọi request. Lặp ở 2–3 app | 1,5–3 ngày, 0 USD |
| **B. Mỗi app giữ tên + chuẩn chung + Cognito `name` ghi một lần** (khuyến nghị) | Cột `display_name` ở app chủ; WORKFORCE token mang `name`; `PersonLabel` trong kit | Không thêm runtime dependency, không đổi IAM, giữ mọi ranh giới đã duyệt | Người ở 2 đại lý nhập tên 2 lần (có điền sẵn). Đổi tên staff không tự sang Booking | 6–8 ngày, 0 USD |
| **B′. Như B, thêm Lambda "name-writer" + trigger cho partner pool** | Lambda có quyền `AdminUpdateUserAttributes`, đồng bộ một tên cho mọi app | Một tên chung, người dùng tự sửa | Mở lại đúng API mà ADR 0006 cấm (`docs/adr/0006-ecosystem-identity.md:129-137`), chỉ chặn bằng code. Trigger mới làm đăng nhập partner phụ thuộc Lambda | 11–14 ngày, dưới 1 USD |
| **C. Profile service trung tâm ở CIS** | `person_profile` + contract `identity.profile.v1` | Một nơi cho mọi trường hồ sơ | Đảo ngược ADR 0010a:46, dòng S283 ở :309 và DM-6.8. Sập một chỗ là mất tên ở mọi app. Xoá dữ liệu phải tính theo nhiều controller | 12–25 ngày |

**Hai bản đề xuất mâu thuẫn ở đâu, ai đúng:**

- **Phương án B′.** Bản đề xuất này nói trigger "fail open" là an toàn. Thực tế code chỉ bắt được exception của chính nó; Lambda bị timeout hay throttle thì đăng nhập vẫn hỏng. Nó cũng đưa quyền `AdminUpdateUserAttributes` (API đổi được cả e-mail) vào, chỉ giới hạn bằng code. Với vài người dùng Dev, cái giá đó chưa đáng. Bản đề xuất kia đúng ở điểm này.
- **Cột `name_source` + quyền sửa tên trong Booking.** Thừa với số staff hiện tại. Booking chỉ cần lấy lại tên từ claim mỗi lần đăng nhập.

## 4) Khuyến nghị và lý do

Chọn **B, bản gọn**:

- **Ranh giới:** CIS không giữ tên người của đại lý. Tên thành viên đại lý nằm trong schema `crm`, nơi đại lý là controller (ADR 0008a). ADR 0019 d7 và ADR 0006 quyết định 1 và 9 giữ nguyên.
- **Ổn định:** trigger WORKFORCE chỉ đọc `userAttributes` có sẵn trong event, không gọi DB hay mạng, nên đăng nhập không thể hỏng vì tên. Partner pool vẫn không có trigger.
- **Bỏ được gốc của bản vá:** không còn giải mã e-mail chỉ để dựng nhãn tên.
- **Một luật chung:** cái gì cũng đi qua `PersonLabel`, không có biến thể riêng cho từng trang.

## 5) Lộ trình (không làm gãy Dev)

**Làm ngay trong phiên này:**

0. **Root PR, chỉ tài liệu.** Thêm mục "Person names" vào data standard:
   - Mỗi bản ghi người có `display_name` (pii:name, 1–120 ký tự), do người nhập, sửa được, thuộc app chủ của bản ghi.
   - Không bao giờ lấy e-mail làm tên. Event, job, log và prompt chỉ mang id.
   - Thêm ADR 0006 amendment: `name` là seed ghi một lần, không đổi IAM.
   - Ghi chú retention: cột mới của `crm.member` theo dòng `:360` (DM-7.1).
1. **Merge AA-1129** như bản tạm, đánh dấu TEMP để gỡ ở bước 5.
2. **Kit:** thêm `PersonLabel(name, kind, ref, seq)` vào `frontend/app/_kit/core` của CIS rồi sync. Thứ tự hiển thị: tên → "Agent 2" → "Former member"; không bao giờ hiện e-mail, UUID hay sub. Thay các hàm nhãn tự viết ở `apps/AA-Partner/web/lib/pipeline.ts:566-570`, `web/lib/team.ts:51-54` và `web/lib/studio/members.ts:50-55`.

**Phiên sau:**

3. **CIS:**
   - Owner sửa được `display_name` (PATCH, có audit).
   - Truyền `name` khi gọi AdminCreateUser.
   - Thêm `name` vào access token trong `workforce.py:283`, chỉ khi người dùng có thuộc tính này. Thiếu thì token giống hệt hôm nay.
   - Tech lead điền `name` một lần cho vài staff hiện có, theo thủ tục có ghi log.
4. **Booking:**
   - Lấy tên từ claim lúc đăng nhập; phần e-mail trước "@" chỉ còn là fallback cuối.
   - Audit mới lưu id, tên đọc lúc hiển thị.
   - Sửa "Recorded by" đang hiện raw sub và UUID của B2B (S283 B3).
5. **CRM:**
   - Migration crm-NNN (thứ tự MIG-4): thêm `crm.member.display_name` (nullable, pii:name, CHECK độ dài).
   - Guard crm-008 cho phép thành viên tự sửa đúng cột này của chính mình, có test CRM01/02 và review độc lập.
   - Màn hình nhận lời mời hỏi "Your name", điền sẵn từ ID token; truyền `name` khi claim tài khoản.
   - GET /members trả thẳng `display_name`. Gỡ phần giải mã của S285.
6. **Studio:** CRM ánh xạ `member_ref` sang tên của `crm.member` cùng tenant. CIS không đổi. Pin công thức fingerprint vào `tenant.membership.v1`.

**Để sau:**

7. **Guard:**
   - Lint bắt mọi cột pii:name mới phải trỏ tới một dòng retention.
   - Test `PersonLabel` không bao giờ trả về e-mail hay UUID.
   - Test danh sách thành viên không gọi vault.
8. **Khách du lịch, chỉ tài liệu:**
   - Đầu vào là một chuỗi `name` tự do, lưu nguyên vào `display_name_enc`.
   - Given/family chỉ do người nhập, dùng cho giấy tờ; không tự tách.
   - `booking.customers` bị xoá cùng AA-1046.

## 6) Khi nào xem lại

- **Hồ sơ cần thêm trường ở ≥2 app** (avatar, múi giờ, chức danh) hoặc **support AA cần tìm người xuyên đại lý** (khoảng 50+ đại lý): xem lại C, dạng directory chỉ đọc.
- **Người dùng than phiền phải nhập tên theo từng đại lý**, hoặc phổ biến chuyện một người ở ≥3 đại lý: xem lại B′.
- **Đại lý đòi SSO/SCIM:** lấy `name` từ IdP của họ.
- **AWS cho phép IAM giới hạn tới từng thuộc tính:** dùng Cognito `name` làm nguồn đồng bộ.
- **Trước prod đầu tiên:** kiểm đã điền `name` trong pool prod, và không còn tên nằm trong text tự do của `booking.audit_logs`.
- **Một yêu cầu xoá dữ liệu tìm thấy tên ngoài bảng chủ:** thêm guard, không dọn một lần.

## 7) Quyết định cần tech lead chốt

1. Chọn B bản gọn, không làm C và B′? **Đề xuất: Có.**
2. `crm.member.display_name` để plain text gắn pii:name, như `admin_users.display_name`, thay vì mã hoá qua vault? **Đề xuất: Plain**, vì đây là nhãn công việc và bị xoá cứng khi đại lý offboard.
3. Cho thành viên tự sửa đúng tên của mình (đổi guard crm-008, chỉ cột này)? **Đề xuất: Có.**
4. Cognito `name` là seed ghi một lần, không đồng bộ, không thêm quyền IAM? **Đề xuất: Có.**
5. Merge AA-1129 làm bản tạm? **Đề xuất: Có**, đánh dấu TEMP và gỡ ở bước 5.
6. Đổi tên staff (hiếm) làm bằng thủ tục console có ghi log, như thủ tục đổi e-mail staff trong ADR 0006? **Đề xuất: Có.**
