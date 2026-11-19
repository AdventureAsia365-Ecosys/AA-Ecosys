# Tư vấn vòng 3: T13, vai trò và quyền trong AA-Booking (bản chốt)

Phiên S285, 19/11/2026. Tác nhân: Claude Code. Dựa trên đề xuất T13 (`advisory-r2-booking-ops.md` mục T13), lát L7
(`advisory-r2-plan.md:63`) và ba bản review (code, kiểm soát, vận hành). Mọi điểm dưới đây đã đối chiếu lại với code:
AA-Booking `4b77735` (phần `backend/app` và `frontend/lib` giống `origin/main` `a6a421c`), AA-CIS-App `43d288c5d`,
AA-CIS-Infra bản checkout hiện tại. Đường dẫn tính từ `apps/AA-Booking/` nếu không ghi khác.

Từ viết tắt (giải thích một lần):

- **NCC**: nhà cung cấp (DMC, khách sạn, nhà xe...). **STK**: số tài khoản ngân hàng.
- **Maker-checker**: người làm và người duyệt phải là hai người khác nhau.
- **Net**: giá AA trả cho NCC. **PO** (purchase order): đơn đặt dịch vụ gửi NCC.
- **BE** = backend (FastAPI), **FE** = frontend (Next.js).
- **CHECK**: ràng buộc trong DB, DB tự từ chối dữ liệu sai dù code có lỗi.
- **Group Cognito**: nhóm người dùng trong pool đăng nhập nhân viên (WORKFORCE); vai trò Booking lấy từ group `booking-*`.
- **KMS**: dịch vụ khoá mã hoá của AWS. **BEC** (business email compromise): email giả, ví dụ "NCC báo đổi STK".
- **SP&ĐH**: vai trò "Sản phẩm & điều hành" (mã trong code vẫn là `contracting`).

---

## 1. Kết luận

**Giữ 4 vai trò, có chỉnh.** Quản trị (`admin`), Bán hàng (`sales`), Sản phẩm & điều hành (`contracting`), Kế toán
(`finance`). Không thêm `ops`. Stop-sale thuộc SP&ĐH + Quản trị. Kế toán trả tiền NCC.

Sáu chỗ phải chỉnh so với đề xuất vòng 2:

1. **Kế toán cần thêm quyền đọc**, không chỉ `bill.read` + `payout.write`. Nếu chỉ thêm hai quyền đó, Kế toán vẫn không
   mở được trang hoá đơn NCC (FE chặn ở `frontend/lib/rbac.ts:84`), tab chi phí theo đoàn (cần `pricing.read`,
   `backend/app/finance/departure_costs.py:128`) và hồ sơ NCC. Kế toán đã thấy lợi nhuận thực tế (`profit.read`, tức
   doanh thu trừ net), nên giấu net với Kế toán không còn tác dụng gì.
2. **Người ghi khoản trả phải khác người duyệt hoá đơn.** Hôm nay code chỉ chặn người nhập và người sửa số tiền
   (`backend/app/ops/supplier_bills.py:958-962`, trigger DB `migrations/030_supplier_bills_payouts.sql:536`). Một admin
   vừa duyệt vừa trả được.
3. **Hợp đồng: cấm công bố với mọi người đã viết điều khoản hoặc giá, không chỉ người sửa cuối.** `maker()` chỉ lấy
   `updated_by or created_by` (`backend/app/suppliers/service.py:496-498`). Người khác sửa một ô ghi chú là người nhập
   giá tự công bố được giá của chính mình.
4. **NCC mới phải có người thứ hai kích hoạt.** Hôm nay NCC mới vào thẳng trạng thái `active` (DB mặc định,
   `migrations/008_suppliers_contracts.sql:61`), không ai duyệt. Kéo bước "Chờ duyệt → Đang hợp tác" của T17 lên đợt 1.
5. **Stop-sale duyệt lệch:** bật thì có hiệu lực ngay, gỡ thì cần người thứ hai. Hôm nay khoảng stop-sale chỉ có
   hiệu lực khi đã duyệt (`backend/app/pricing/seasons.py:157` lọc `status = 'approved'`), nên trong lúc chờ duyệt, tour
   vẫn bán xác nhận ngay.
6. **Câu "chỉ sửa `staff.py`, không migration" của L7 là sai.** Phần quyền và nhãn không cần migration nhưng phải sửa
   FE, CIS và tài liệu. Các mục 3, 4 và phần STK (T17) cần migration `bk-`. Ẩn `content_creator` làm hai bước: ẩn ngay,
   xoá hẳn sau khi đếm được 0 người.

`profit.read` = Quản trị + Kế toán đang ghi "proposed default, to confirm with the business owner"
(`backend/app/auth/staff.py:169-171`). T13 chốt luôn: giữ như vậy.

---

## 2. Ma trận vai trò và quyền (bản chốt)

Ký hiệu trong ô:

- **Có**: tự làm, không cần ai duyệt.
- **Đọc**: chỉ xem.
- **Làm, chờ duyệt**: làm được, nhưng chỉ có hiệu lực khi người thứ hai duyệt.
- **Duyệt**: là người thứ hai; không bao giờ duyệt việc của chính mình.
- **Không**: không thấy, không làm.
- Chữ **(mới)** = khác hôm nay.

### 2.1 Nhà cung cấp

| Việc | Quản trị | Bán hàng | SP&ĐH | Kế toán |
|---|---|---|---|---|
| Xem NCC, khách sạn, dịch vụ (kèm giá net) | Có | Đọc | Có | Đọc (mới) |
| Tạo, sửa hồ sơ NCC (trừ STK và số điện thoại kế toán NCC) | Có | Không | Có | Không |
| Kích hoạt NCC mới (Chờ duyệt → Đang hợp tác) | Làm, chờ duyệt / Duyệt | Không | Làm, chờ duyệt / Duyệt | Không |
| Tạm ngưng, ngừng hợp tác | Có | Không | Có | Không |

### 2.2 Tài khoản ngân hàng của NCC (T17, phần cần khoá KMS)

| Việc | Quản trị | Bán hàng | SP&ĐH | Kế toán |
|---|---|---|---|---|
| Xem STK đầy đủ | Có | Đọc số đã che (4 số cuối) | Đọc số đã che | Có |
| Nhập STK đầu tiên, đổi STK | Làm, chờ duyệt | Không | Không (chuyển thư NCC cho Kế toán) | Làm, chờ duyệt |
| Duyệt STK, kèm gọi lại xác nhận | Duyệt | Không | Không | Duyệt |
| Đổi số điện thoại người liên hệ kế toán của NCC | Làm, chờ duyệt | Không | Không | Làm, chờ duyệt |

SP&ĐH không nhập STK, vì nếu được thì một người có thể tạo NCC, nhập STK, đặt dịch vụ và nhập hoá đơn cho chính NCC đó.

### 2.3 Hợp đồng và giá

| Việc | Quản trị | Bán hàng | SP&ĐH | Kế toán |
|---|---|---|---|---|
| Xem net, biên lợi nhuận, tỷ giá (`pricing.read`) | Có | Đọc | Có | Đọc (mới) |
| Nhập hợp đồng nháp, giá NCC, bảng giá, quy tắc giá | Làm, chờ duyệt | Không | Làm, chờ duyệt | Không |
| Công bố hợp đồng, duyệt bảng giá, quy tắc giá | Duyệt (khác **mọi** người đã viết, mới) | Không | Duyệt (như bên trái) | Không |
| Lịch mùa, sự kiện lễ | Làm, chờ duyệt / Duyệt | Đọc | Làm, chờ duyệt / Duyệt | Đọc (mới) |
| Tham số giá trên trang Policy | Làm, chờ duyệt / Duyệt mọi nhóm | Đọc | Làm, chờ duyệt / Duyệt nhóm giá | Làm, chờ duyệt / Duyệt nhóm tỷ giá, thuế, phụ thu, thanh toán |

### 2.4 Stop-sale

| Việc | Quản trị | Bán hàng | SP&ĐH | Kế toán |
|---|---|---|---|---|
| Xem stop-sale | Có | Đọc | Có | Đọc (mới) |
| Bật stop-sale | Có: hiệu lực ngay, người thứ hai xem lại sau (mới) | Không | Có: như bên trái (mới) | Không |
| Gỡ stop-sale đã có hiệu lực | Làm, chờ duyệt / Duyệt | Không | Làm, chờ duyệt / Duyệt | Không |

### 2.5 Đặt dịch vụ, voucher, PO

| Việc | Quản trị | Bán hàng | SP&ĐH | Kế toán |
|---|---|---|---|---|
| Xem đặt dịch vụ, voucher, PO, kiểm chuyến | Có | Có | Có | Đọc (mới) |
| Tạo, gửi, sửa net dòng, xác nhận với NCC | Có | Có | Có | Không |
| Gán người phụ trách một đoàn khởi hành | Có | Có | Có | Không |

Quy ước vận hành: người được gán phụ trách đoàn là chủ việc đặt dịch vụ của đoàn đó, để Bán hàng và SP&ĐH không làm
trùng.

### 2.6 Báo giá và đặt chỗ của đại lý

| Việc | Quản trị | Bán hàng | SP&ĐH | Kế toán |
|---|---|---|---|---|
| Xem hồ sơ chuyến | Có | Có | Đọc | Đọc (mới) |
| Tạo hồ sơ, báo giá, đặt thay đại lý, huỷ / bớt khách | Có | Có | Không | Không |
| Báo giá dưới biên sàn, giảm phí huỷ | Làm, chờ duyệt / Duyệt | Làm, chờ duyệt | Duyệt | Không |
| Desk B2B (dòng on-request, sự cố đoàn) | Có | Có | Có | Không |
| Đối tác B2B được gọi API | Có | Không | Không | Không |

### 2.7 Hoá đơn NCC và trả tiền

| Việc | Quản trị | Bán hàng | SP&ĐH | Kế toán |
|---|---|---|---|---|
| Xem hoá đơn NCC, khoản đã trả, giấy báo chuyển khoản | Có | Đọc | Có | Đọc (mới) |
| Nhập hoá đơn NCC, khớp với đặt dịch vụ | Làm, chờ duyệt | Không | Làm, chờ duyệt | Không |
| Duyệt hoá đơn NCC | Duyệt | Không | Duyệt | Không |
| Ghi khoản trả, huỷ khoản trả, tải giấy báo | Có (khác người nhập, người sửa số tiền, người duyệt, mới) | Không | Không | Có (như bên trái, mới) |
| Hoá đơn AA gửi đại lý, ghi tiền đại lý trả | Có | Không | Không | Có |
| Duyệt khoản đại lý trả | Duyệt | Không | Không | Duyệt |

Kế toán **không** nhập và không duyệt hoá đơn NCC. Vòng tiền tách ba người: SP&ĐH nhập → người thứ hai duyệt → Kế toán
trả. Bán hàng vẫn giữ `bill.read` (họ đặt dịch vụ nên cần thấy NCC đã đòi gì); khi khoản trả lưu STK lúc trả (mục 3),
STK đó hiện số đã che với Bán hàng và SP&ĐH.

### 2.8 Người dùng và cài đặt

| Việc | Quản trị | Bán hàng | SP&ĐH | Kế toán |
|---|---|---|---|---|
| Cấp, đổi vai trò Booking (trên trang Staff của CIS) | Có (mỗi lần cấp vai trò có quyền tiền thì báo mọi admin khác, mới) | Không | Không | Không |
| Khoá / mở tài khoản Booking (kèm lý do) | Có | Không | Không | Không |
| Nhật ký audit | Có | Không | Không | Không (nhận tóm tắt tuần, mới) |
| Điều khoản đối tác | Duyệt | Không | Không | Không |
| Trạng thái quốc gia, xoá dữ liệu theo hạn | Có | Không | Không | Không |

### 2.9 Báo cáo

| Việc | Quản trị | Bán hàng | SP&ĐH | Kế toán |
|---|---|---|---|---|
| Lợi nhuận thực tế theo hồ sơ, đoàn, đại lý | Có | Không | Không | Có (chốt) |
| Chi phí theo đoàn khởi hành, tab PO | Có | Đọc | Có | Đọc (mới) |
| Catalog tour (chỉ đọc, nội dung viết ở CIS) | Có | Đọc | Đọc | Đọc (mới, sửa lỗi 403 hôm nay) |
| Trang chủ riêng | Có | Có | Có | Có: hoá đơn NCC sắp đến hạn, khoản đại lý chờ duyệt (mới) |

Quyền trong code của Kế toán sau T13: giữ 10 quyền hiện có, thêm `bill.read`, `payout.write`, `pricing.read`,
`supply.read`, `ops.read`, `trip_case.read`, `catalog.read`; về sau thêm `supplier_bank.read/write/approve` (L7c).
Kế toán **không** có `bill.write`, `bill.approve`, `ops.write`, `supply.write`, `staff.admin`.

`content_creator` không còn trong ma trận (ẩn ngay, xoá hẳn sau, mục 4).

---

## 3. Luật kiểm soát

### 3.1 Bộ luật (giữ nguyên 4 vai trò)

- **L-1. Không tự duyệt.** Người duyệt khác **mọi** người đã tạo hoặc sửa đối tượng, áp dụng cả cho admin, có CHECK
  trong DB giữ. Hôm nay đã đúng với hoá đơn NCC (`030:138`), mùa (`055:155`), khoản đại lý trả, điều khoản đối tác.
  Thiếu ở hợp đồng (chỉ người sửa cuối) và kích hoạt NCC (không ai duyệt).
- **L-2. Ba khoá cho một vòng tiền NCC.**
  - (a) Kích hoạt NCC và duyệt STK do người thứ hai làm.
  - (b) Duyệt hoá đơn do người thứ hai làm (đã có).
  - (c) Người ghi khoản trả khác người nhập (đã có), khác người sửa số tiền (đã có) và **khác người duyệt hoá đơn**.
    Luật (c) chặn hẳn khi còn một người khác đang hoạt động có quyền trả tiền (admin hoặc finance). Nếu không còn ai,
    hệ thống cho ghi nhưng bắt ghi lý do và gắn cờ `same_approver_payer` trong audit; cờ này hiện trong tóm tắt tuần.
  - Ngoài hệ thống: Booking **không chuyển tiền**, khoản trả chỉ là bản ghi. Tiền thật đi ở internet banking doanh
    nghiệp: Kế toán lập lệnh, business owner duyệt lệnh. Đây là khoá mạnh nhất với đội nhỏ.
- **L-3. Ngân hàng (T17), chống email giả đổi STK.**
  - Nhập hoặc đổi STK: người thứ hai duyệt.
  - Người duyệt gọi lại số đã lưu ít nhất 30 ngày hoặc số in trên hợp đồng đã ký, không gọi số vừa đổi; ghi "đã gọi
    ai, số nào, lúc nào".
  - Đổi số điện thoại người liên hệ kế toán của NCC cũng là thay đổi nhạy cảm, theo luật như đổi STK.
  - Khoá trả tiền 24 giờ sau khi STK được duyệt, **kể cả STK đầu tiên** của NCC mới.
  - Mỗi khoản trả lưu STK đang hiệu lực lúc ghi, để đối chiếu với lệnh ở ngân hàng.
  - Số ngày, số giờ là tham số trên trang Policy, không ghi cứng.
- **L-4. Cờ đỏ trên màn duyệt** (chỉ cảnh báo, không chặn; ngưỡng chỉnh trên trang Policy):
  - Cùng một người tạo NCC, đặt dịch vụ và nhập hoá đơn.
  - NCC mới dưới 30 ngày; STK đổi dưới 30 ngày.
  - Hoá đơn lệch giá net đã đặt quá ngưỡng (hôm nay duyệt hoá đơn chỉ kiểm tổng dòng bằng số tiền,
    `supplier_bills.py:846-851`); vượt ngưỡng thì bắt ghi lý do.
- **L-5. Không có nút vượt rào.** Admin không có nút bỏ qua maker-checker. Không có công tắc "chế độ một người".
- **L-6. Audit và nhân viên.**
  - Audit giữ chỉ-thêm (app không có quyền UPDATE/DELETE, `migrations/001_*.sql:31`).
  - Tóm tắt tuần (sự kiện tiền, cờ đỏ, cờ `same_approver_payer`, thay đổi nhân viên và vai trò) gửi business owner và
    Kế toán.
  - Tạo tài khoản nhân viên hoặc cấp vai trò có quyền tiền (admin, contracting, finance) thì báo ngay cho mọi admin
    khác. Lý do: owner tự tạo được tài khoản thứ hai và gán `booking-admin` (guard CIS chỉ chặn tự hạ quyền, tự khoá),
    trong khi maker-checker kiểm theo tài khoản, không theo người thật.
  - Rà quyền hằng quý (lịch DM-8.10 đã có).
- **L-7. Hạ tầng.** Người giữ DB master hoặc dùng DB Migrate `run-script` ghi thẳng được vào bảng tiền. Quy ước: không
  dùng `run-script` cho bảng tiền; khi có prod, tech lead duyệt từng lần chạy (đã có trong luật merge giai đoạn prod).

### 3.2 Khi chỉ có 1 hoặc 2 người

| Đội | Ai làm gì | Ghi chú |
|---|---|---|
| 4 người: owner (Quản trị), SP&ĐH, Bán hàng, Kế toán | Đủ L-1 đến L-6 | Chuẩn |
| 3 người: owner, SP&ĐH, Kế toán | Việc bán hàng do owner hoặc SP&ĐH làm | Đủ luật |
| 2 người: owner + 1 SP&ĐH; Kế toán thuê ngoài không đăng nhập | SP&ĐH làm, owner duyệt. Owner nhập giá thì SP&ĐH duyệt (SP&ĐH có quyền duyệt giá, mùa, hoá đơn). Owner vừa duyệt hoá đơn vừa ghi khoản trả: L-2c chỉ gắn cờ, chấp nhận được vì SP&ĐH không có quyền trả và lệnh ở ngân hàng vẫn do owner duyệt | STK: owner nhập thì không ai duyệt được (SP&ĐH không có quyền ngân hàng) → tech lead (tài khoản admin riêng, người thật khác) duyệt |
| 1 người, hoặc người thứ hai vắng lâu | Tech lead đăng nhập bằng tài khoản admin của chính mình làm người thứ hai, từ xa | Tech lead là người thật khác, nên không phải "một người hai tài khoản" |

**Nút "duyệt một mình" (break-glass)**: chưa làm trong L7. Lý do: mỗi bảng có maker-checker đều có CHECK trong DB, nên
nút này phải sửa CHECK của từng bảng (hoá đơn, hợp đồng, mùa, STK...). Dev chưa có người dùng thật và luôn có tech lead
làm người thứ hai. Làm trước prod đầu tiên **nếu** lúc đó có giai đoạn chỉ một người duyệt được. Khi làm: chỉ admin, lý
do ≥ 20 ký tự, trần số tiền trên trang Policy, audit gắn cờ `break_glass`, email ngay cho owner + tech lead, người thứ
hai rà lại khi quay về.

**Người nghỉ phép**: không cho một người giữ 2 vai trò. Admin đổi vai trò tạm trên trang Staff của CIS (có ghi audit
`staff.role_synced`, `staff.py:351-356`), đổi lại khi người kia về.

---

## 4. Thay đổi code và dữ liệu cho L7

Chia L7 thành ba lát để PR nhỏ và phần rủi ro được review riêng. Lát a không có migration; lát b và c có migration
`bk-` nên cho agent review trước khi merge (luật merge giai đoạn dev).

### L7a. Ma trận 4 vai trò, nhãn, Kế toán trả tiền (không migration)

**AA-Booking, BE**

- `backend/app/auth/staff.py`
  - `PERMISSIONS`: thêm `finance` vào `bill.read` (:154), `payout.write` (:157), `pricing.read` (:112), `supply.read`
    (:116), `ops.read` (:142), `trip_case.read` (:103), `catalog.read` (:119).
  - Sửa chú thích quyền (:32-36, :151-153, :169-171 chốt `profit.read`).
  - Bỏ `"content": "content_creator"` khỏi `ROLE_FROM_CIS` (:74). Cầu nối đã tắt (`identity_config.py:58`), dòng này chỉ
    còn dùng trong test.
  - Giữ nguyên `content_creator` trong `STAFF_ROLES` và `BOOKING_GROUP_ROLES` ở lát này.
- `backend/app/ops/supplier_bills.py`
  - Luật L-2c: trong hàm ghi khoản trả (:958-962) và cờ `actions.pay` (:190-192) thêm điều kiện khác `approved_by`; nếu
    không còn người khác có `payout.write` đang hoạt động thì cho ghi kèm lý do và gắn cờ `same_approver_payer` vào
    audit.
  - Sửa chữ "an admin records the payout" (:16, :30, :959) thành "finance or an admin".
- `backend/app/ops/lifecycle.py:600`: câu nhắc hoá đơn sắp đến hạn, bỏ "an admin".
- `backend/app/pricing/seasons.py:157`: khoảng `stop_sale` đang chờ duyệt cũng có hiệu lực
  (`r.status = 'approved' OR (r.kind = 'stop_sale' AND r.status = 'pending')`). Bị từ chối hoặc rút thì hết hiệu lực;
  gỡ một stop-sale đã duyệt vẫn qua yêu cầu kết thúc có người thứ hai (đã có, CHECK `055:159-164`). Không cần
  migration. Sửa docstring `backend/app/pricing/seasons_admin.py:9-11`.
- `backend/app/auth/e2e_staff.py`: thêm test khẳng định route ghi khoản trả không nằm trong danh sách cho phép của ba
  tài khoản E2E nhóm `booking-finance` (:249-253).
- Test phải sửa: `backend/tests/unit/test_aa682_billing.py:197-198`, `backend/tests/unit/test_aa682_supplier_bills.py:188`.
  Test mới: Kế toán ghi được khoản trả; người duyệt không ghi được khi còn người khác; stop-sale chờ duyệt đã đẩy báo
  giá sang `on_request` (`backend/app/b2b/quotes.py:237-240`).

**AA-Booking, FE**

- `frontend/lib/rbac.ts`
  - `ROLE_LABEL.contracting` = "Product & operations" (:17).
  - Thêm `F` vào `/billing` (:84), `/suppliers` và `/suppliers/*` (:58-59), `/hotels`, `/services`, `/services/*`
    (:60-62), `/cases` và `/cases/*` (:46-47), `/pricing/seasons`, `/pricing/holiday-events` (:76-77).
  - Không thêm `F` vào trang sửa: `/suppliers/new`, `/suppliers/:id/edit`, `/suppliers/rate-sheets/*`, `/cases/new`.
- `frontend/app/(staff)/page.tsx`: thêm trang chủ Kế toán (hoá đơn NCC sắp đến hạn, khoản đại lý chờ duyệt). Chú ý:
  `canCases` (:60) sẽ thành đúng với Kế toán sau khi thêm `/cases`, nên phải rẽ nhánh theo vai trò, không theo
  `canCases`. `CatalogDashboard` (:478-489) không còn ai dùng sau khi ẩn `content_creator`.
- `frontend/app/(staff)/billing/page.tsx:4,17` và `billing/_parts/BillDrawer.tsx:7,211,305`: bỏ "an admin".
- `frontend/app/(staff)/staff/_parts/useStaffActions.tsx:24-25`: mô tả vai trò mới; bỏ dòng `content_creator`.
- `frontend/app/(staff)/pricing/calculator/page.tsx:22` và `frontend/app/(staff)/cases/[code]/proposals/[n]/page.tsx:136`:
  đổi `me.role === "admin" || me.role === "contracting"` thành `useCan("pricing.write")`.
- Chữ "Contracting adds..." ở trạng thái trống: `app/(staff)/services/_parts/ServicesView.tsx`,
  `app/(staff)/hotels/_parts/HotelsView.tsx`, `app/(staff)/suppliers/_parts/SuppliersListView.tsx`,
  `app/(staff)/suppliers/_parts/SupplierDetailView.tsx`, `app/(staff)/catalog/trip-plans/_parts/DeparturesPanel.tsx`.
- Kiểm trang hồ sơ chuyến khi Kế toán mở mà không có `customer.read`: trang phải ẩn phần khách, không lỗi.

**AA-Booking, tài liệu (cùng PR)**: `CONTEXT.md:555-582` (bảng quyền), `docs/ui-spec.md` (các dòng vai trò :25, :197,
:203, :338). Root: ADR `docs/adr/0006-ecosystem-identity.md:115` và `docs/adr/0006a-identity-phase1-amendments.md:65`
thêm ghi chú "S285 T13".

**AA-CIS-App (PR riêng)**

- `api/services/staff_directory.py`
  - `BOOKING_ROLES` (:118) bỏ `content_creator`.
  - Thêm `RETIRED_BOOKING_GROUPS = ("booking-content_creator",)` và cộng vào `BOOKING_GROUPS` (:235), giống
    `RETIRED_CIS_GROUPS` (:116, :234). Nếu không, nút Sync (:771) sẽ thôi gỡ group cũ, và Booking vẫn cho người còn
    group cũ đăng nhập.
- `api/routers/admin_platform.py:82`: `BookingRole` bỏ `content_creator` (API trả 400 khi cấp mới).
- `frontend/app/admin/platform/staff/StaffManage.tsx:64`: bỏ `content_creator`.
- `frontend/app/admin/platform/staff/messages.ts:11,15`: nhãn "Product & operations" / "Sản phẩm & điều hành"; sửa
  câu mẫu `pricing_team` (:228, :332) cho khớp tên mới.
- Luật L-6 phần thông báo: khi cấp `booking-admin`, `booking-contracting`, `booking-finance` thì gửi thông báo cho mọi
  admin khác (có thể đưa vào L7b nếu PR CIS này cần gọn).

**AA-CIS-Infra**: không đổi ở lát này. Giữ group `booking-content_creator` (`accounts/aa365/identity.tf:158`); có thể đổi
chữ mô tả `booking-contracting` (:156), không bắt buộc.

### L7b. Luật kiểm soát có migration (bk mới)

- Migration `bk-`:
  - `booking.supplier_contracts`: thêm cột danh sách người đã viết điều khoản hoặc giá của bản nháp; điền sẵn từ
    `created_by` / `updated_by`; CHECK mới "người công bố không nằm trong danh sách" thay CHECK người sửa cuối (`008`).
  - `booking.suppliers`: thêm trạng thái `pending` vào `suppliers_status_chk` (`008:74`); NCC tạo mới mặc định `pending`;
    cột người kích hoạt + CHECK khác người tạo. NCC đang có giữ `active`.
- Code: `backend/app/suppliers/service.py` (`maker()` :496-498 → kiểm cả danh sách; `create_supplier` → `pending`;
  `set_status` :410 → kích hoạt từ `pending` phải khác người tạo), `backend/app/supply/rates.py:260-262` (người ghi giá
  được thêm vào danh sách, không đè).
- Cờ đỏ L-4 trên màn duyệt hoá đơn NCC (`supplier_bills.py` hàm `approve` :834 + `BillDrawer.tsx`); ngưỡng là tham số
  mới trên trang Policy (thêm dòng tham số theo cách AA-1096 đã làm).
- Tóm tắt tuần L-6: một job tuần trên bảng `booking.job`, gửi email cho owner và Kế toán.

### L7c. Tài khoản ngân hàng NCC (T17, chờ duyệt khoá KMS ~1 USD/tháng)

- Migration `bk-`: bảng STK của NCC (mã hoá bằng khoá KMS mới), trạng thái chờ duyệt / đã duyệt, người nhập, người
  duyệt, ghi chú gọi lại, thời điểm hết khoá 24 giờ; `supplier_payouts` thêm STK lúc trả (đã che với người không có
  `supplier_bank.read`).
- Quyền mới trong `staff.py`: `supplier_bank.read` = admin, finance (Bán hàng và SP&ĐH thấy số đã che);
  `supplier_bank.write` = admin, finance; `supplier_bank.approve` = admin, finance, khác người nhập.
- Ghi khoản trả bị chặn khi NCC chưa có STK đã duyệt hoặc còn trong 24 giờ khoá.
- Infra: khoá KMS và quyền cho task role Booking (AA-CIS-Infra), chỉ khi tech lead đã duyệt chi phí.

### Chuyển người dùng và dữ liệu đang có

1. **Đếm người còn `content_creator`** ở 3 nơi trước khi deploy L7a:
   - Booking: `GET /booking/staff` bằng tài khoản admin, lọc `role = content_creator` (hoặc DB Migrate `run-script`).
   - CIS: `shared.staff_app_grant` với `app = 'booking'` và `role = 'content_creator'` (ECS exec bằng `DATABASE_URL`).
   - Cognito: thành viên group `booking-content_creator` (lệnh `list-users-in-group`, một dòng).
2. **Ai còn**: xoá grant trên trang Staff của CIS, bấm Sync để gỡ group (sau khi L7a CIS có `RETIRED_BOOKING_GROUPS`);
   dòng `booking.staff_users` đặt `active = false` kèm lý do.
3. **Kế toán**: không phải chuyển gì. Quyền mới có hiệu lực từ request tiếp theo. Ba tài khoản E2E nhóm
   `booking-finance` nhận thêm quyền đọc; ghi vẫn bị chặn theo danh sách route cho phép.
4. **SP&ĐH**: không đổi gì ngoài nhãn; mã `contracting` và group giữ nguyên.
5. **Dữ liệu L7b**: NCC đang có giữ `active`; hợp đồng nháp đang có được điền danh sách người viết từ `created_by` /
   `updated_by`.
6. **Xoá hẳn `content_creator`** (lát sau, khi đếm được 0 ở cả 3 nơi qua ít nhất một lần Sync):
   - Booking: bỏ khỏi `STAFF_ROLES` (:72), `BOOKING_GROUP_ROLES` (:83), `catalog.read` (:119); FE `lib/rbac.ts:11,18`,
     `catalog/trip-plans/_parts/shared.tsx:15`, `e2e/layout/fixtures.ts:111`; khoảng 25 file test đang dùng
     `content_creator` làm "vai trò bị từ chối" đổi sang vai trò khác.
   - Thu hẹp CHECK `staff_users_role_chk` (Booking, migration `bk-` mới thay `038:39`) và `staff_app_grant_role_chk`
     (CIS, migration mới thay 363).
   - Infra: xoá group ở `accounts/aa365/identity.tf:158` và sửa
     `accounts/aa365/lambda_src/identity_triggers_tests/test_workforce.py`.
   - Đây là thay đổi quyền + migration: cho agent review trước khi merge.

---

## 5. Khi nào tách thêm vai trò

| Tách ra | Khi nào | Cách làm |
|---|---|---|
| `ops` (đặt chỗ) tách khỏi SP&ĐH | Có từ 2 người đặt chỗ toàn thời gian, **hoặc** khoảng 200 đặt dịch vụ mỗi tháng, **hoặc** tuyển người đặt chỗ không được sửa giá | Vai trò mới: `ops.*`, `b2b_desk.*`, đọc NCC; không có `supply.write`, `pricing.write`, `bill.approve` |
| `net.read` tách khỏi `pricing.read` | Tuyển Bán hàng cấp dưới, bán thời gian, hoặc cộng tác viên bán hàng | Bán hàng mới chỉ thấy giá bán + % biên lợi nhuận; khoảng 22 file đang kiểm `pricing.read` |
| `viewer` (chỉ xem) | Có kiểm toán, nhà đầu tư hay đối tác cần xem mà không sửa | Chỉ các quyền `.read`, không thấy STK |
| Kế toán đọc audit phần tiền | Khi có hơn một admin, hoặc khi tóm tắt tuần không còn đủ | Quyền mới `audit.read_finance`, lọc sự kiện tiền |
| Nút "duyệt một mình" | Trước prod đầu tiên, nếu có giai đoạn chỉ một người duyệt được | Như mục 3.2 |
| Một người giữ 2 vai trò | Chỉ khi có người vừa bán vừa nhập giá mà không nên làm admin, và đổi vai trò tạm không đủ | Phải sửa cả Booking (trả về tập vai trò) và trang Staff của CIS |

Con số "200 đặt dịch vụ mỗi tháng" là ước lượng, không phải chuẩn ngành. Ở các công ty lữ hành dưới 10 người, gộp sản
phẩm với điều hành là phổ biến; Tourplan và Lemax phân quyền theo chức năng (chưa kiểm họ có maker-checker cho STK).
