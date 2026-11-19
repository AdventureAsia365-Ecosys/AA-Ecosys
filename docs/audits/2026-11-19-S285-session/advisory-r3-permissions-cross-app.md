# Vòng 3: lỗ hổng phân quyền giữa CIS, CRM / tenant portal và TripPlanner sau các quyết định S285

_S285, 19/11/2026. Tư vấn cho tech lead. Chỉ đọc code, không sửa repo nào. Code đọc ở: AA-CIS-App `43d288c5d`,
AA-Partner `27b8c56f`, AA-TripPlanner-Web `44aa203`. Vai trò của AA-Booking (T13) đang được rà riêng nên ở đây **không
làm lại**; chỉ ghi phần CIS phải sửa theo T13._

---

## Từ viết tắt dùng trong bài

| Viết tắt | Nghĩa |
|---|---|
| **CIS** | App nội dung và danh mục tour của AA (có trang admin cho staff) |
| **CRM** | App AA-Partner: CRM cho đại lý, kèm tenant portal (Content studio) |
| **TP** | TripPlanner: trang lên lịch trình cho khách của đại lý |
| **Staff** | Nhân viên AA, đăng nhập bằng Cognito (dịch vụ đăng nhập của AWS) |
| **Đại lý / tenant** | Công ty đối tác dùng app của AA |
| **Capability** | Một quyền nhỏ trong code, ví dụ `content.write`. Mỗi vai trò là một tập capability |
| **POLICY** | Bảng trong `staff_authz.py` ghi mỗi route cần capability nào |
| **Route** | Một địa chỉ API, ví dụ `PATCH /admin/tours/{id}/raw` |
| **Master** | Bản nội dung tour đang chạy thật, khách và đại lý thấy |
| **T2** | Bản viết lại tour riêng của từng đại lý |
| **T9** | Bài viết marketing của đại lý (dùng Facts Entries làm dữ kiện) |
| **Facts Entries** | Bảng dữ kiện (giá, mùa, visa...) mà AI dùng khi viết bài |
| **Audit** | Dòng ghi lại ai làm gì, lúc nào, giá trị trước/sau |
| **E2E** | Tài khoản thử tự động (end-to-end) mà agent dùng để kiểm trên Dev |
| **Cap** | Trần tiền chi cho AI |
| **Dev / prod** | Môi trường thử / môi trường thật |

Mã issue: **AA-1144** khoá CRM (lát L1), **AA-1146** cổng phiên bản CIS (L3), **AA-1148** chỗ làm việc của content (L4,
màn content desk), **AA-1150** vai trò Booking (L7, T13). "Mới" = chưa có issue.

---

## 1. Trả lời ngắn (1 phút)

- **Có 3 lỗ hổng lớn** do quyết định hôm nay lộ ra:
  1. **Nhân viên content hiện tự xuất bản được** (Review Queue approve, promote, xuất bản mô tả khách sạn/hoạt động),
     vì vai trò `content` có quyền `review.act`. Chưa có quyền "xuất bản" riêng nên chưa thể bật "cần người thứ hai".
  2. **Nhân viên content vẫn sửa được giá và tên nhà cung cấp** dạng chữ trong tour gốc (`price_raw`, `provider`), không
     ghi giá trị cũ. Giá thì từ nay thuộc Booking.
  3. **Đại lý vẫn ghi được dữ kiện sản phẩm qua 2 đường ngoài CRM:** Facts Entries (loại `price`, `season`,
     `transfer_time`, `visa_entry`, `other`, và còn **đè** được dữ kiện của AA) và bản T2 (lưu mọi trường, không khoá
     dữ kiện). Cả hai nằm trong **code CIS**, không phải code CRM, nên AA-1144 phải sửa cả repo CIS.
- **Trần AI đã đúng chính sách:** chỉ admin được nâng hoặc bỏ trần; `ai_ops` chỉ được hạ (quyết định S279). Còn thiếu
  2 việc: các route trần AI **không bắt đăng nhập Cognito** (settings registry thì bắt), và route `budgets` không ghi
  giá trị trước/sau.
- **Màn content desk, editor, xem trước, sửa hàng loạt, upload ảnh: chưa có route nào.** Mỗi màn cần capability mới
  hoặc capability có sẵn. Bảng ở mục 4.
- **TripPlanner không có vai trò staff.** Mọi núm chỉnh nằm ở CIS. TP chỉ bị ảnh hưởng gián tiếp: trang của đại lý hiện
  bản T2, nên lỗ hổng T2 ở trên lộ ra cả trên TP.
- **11 quyết định** cần tech lead chốt (mục 7). Tất cả **0 USD** hạ tầng.

---

## 2. Bản đồ quyền hôm nay (đã kiểm trong code)

### 2.1 Vai trò staff của CIS (`apps/AA-CIS-App/api/core/staff_authz.py:163-210`)

| Vai trò | Có những quyền chính | Ghi chú liên quan tới quyết định hôm nay |
|---|---|---|
| `admin` | Tất cả, kể cả `settings.write/approve`, `spend.write`, `ai.admin` | |
| `content_lead` | Viết nội dung, `review.act`, `master.admin`, `atoms.write`, `photos.write`, `quality.write`, `wave.run`, **`reference_price.write`** | Sửa được giá tham chiếu |
| `content` | `content.read`, `content.write`, **`review.act`**, `catalog.read`, `reference_price.read` | Tự duyệt và xuất bản được. Không vào được trang Ảnh |
| `tenant_qa` | `quality.write` (kèm sửa Facts của AA), `a4.unpublish` | Ghi được Facts loại `price`/`season` của AA |
| `customer_success` | Sổ đại lý của mình, **`reference_price.write`** | Nhóm "Pricing team" nhập giá ở CIS |
| `support` | Đọc sổ đại lý, gửi lại lời mời | |
| `finance` | Tiền đại lý, đọc chi phí AI | |
| `ai_ops` | `ai.admin`, `spend.write` (chỉ được **hạ** trần) | Đúng quyết định S279 |
| `viewer` | Chỉ đọc (tài khoản UI smoke) | |

### 2.2 Vai trò của đại lý

- **CRM** (`apps/AA-Partner/api/app/permissions.py:48`): `owner`, `agent`, `assistant`. Nhà cung cấp riêng và dòng dịch
  vụ dùng quyền `TRIP_EDIT`, nên **cả 3 vai trò** đều tạo được.
- **Content studio** (CIS `api/middleware/tenant_role.py`): `viewer`, `editor`, `owner`. Editor và owner ghi được Facts
  Entries và sửa bản T2.

### 2.3 Staff AA trong CRM (`apps/AA-Partner/api/app/auth/identity_config.py:5-15, 82-94`)

- `/crm/ops/v1`: nhóm `cis-admin` đọc, **chỉ `crm-platform-admin` ghi** (gồm cài đặt CRM và hồ sơ AI của CRM,
  `app/routers/ops.py:549`).
- `/crm/staff/v1`: `crm-ops`, `crm-support` (vận hành, hỗ trợ). Không route nào ghi dữ liệu sản phẩm.

### 2.4 TripPlanner

Không có đăng nhập staff, không có vai trò. Trần AI theo đại lý đọc từ CIS (`backend/shared/tenant_budget.py:1-25`,
view `catalog.v_tenant_ai_budget_v1`). Không có lỗ hổng phân quyền riêng.

---

## 3. Danh sách lỗ hổng

Mức: **Cao** = sai quyết định hôm nay hoặc làm sai dữ liệu khách thấy. **TB** (trung bình) = cần sửa trong lát đang
làm. **Thấp** = dọn hoặc ghi rõ.

### P1 (Cao). Nhân viên content tự duyệt và tự xuất bản được, ở mọi môi trường

- **Sai ở đâu:**
  - `content` có `review.act` (`staff_authz.py:156`, `_CONTENT_WORK`; `:180`).
  - `review.act` mở: Review Queue approve (`:511`, `:672`), xuất bản mô tả khách sạn/hoạt động
    (`/admin/supply-content/.../publish`, `:821-823`).
  - Promote một phiên bản lên Master chỉ cần `content.write` (`:521`; handler `api/routers/admin_pipeline/versions.py:16-79`).
    Handler đã bắt phiên bản phải ở trạng thái `approved` (tốt), nhưng người approve có thể chính là người sửa.
  - Không chỗ nào kiểm "người duyệt khác người sửa".
  - Không có lẫn nhau: AA content (`/admin/aa-content/.../publish`, `:730`) lại cần `master.admin`, tức content **không**
    xuất bản được. Hai luồng cùng là "xuất bản nội dung AA" mà quyền khác nhau.
- **Rủi ro:** Lên prod, nếu bật "cần người thứ hai" thì chưa có gì để bật. Một nhân viên content sửa sai một tour, tự
  duyệt, và tour sai đi thẳng tới TripPlanner cùng mọi đại lý.
- **Đề xuất:**
  1. Thêm capability `content.publish`, dùng cho mọi route "đưa ra ngoài": Review Queue approve, promote, xuất bản
     supply content, xuất bản AA content, xuất bản hàng loạt, và route xuất bản của Tour editor mới.
  2. `content_lead` và `admin` luôn có `content.publish`. `content` chỉ có khi công tắc **tắt** (Dev).
  3. Công tắc là một setting trong Platform › Settings (`cis.content.publish_two_person`, chỉ admin đổi, có
     audit), không phải biến môi trường. Xem **D1**.
  4. Khi công tắc bật: route xuất bản từ chối nếu người bấm chính là người tạo bản nháp (403
     `same_person`). Đây là luật "maker-checker" (người làm khác người duyệt), giống settings registry
     (`api/services/settings_registry.py:457`).
  5. `content` giữ phần còn lại của `review.act` (reject, dismiss, gắn nhãn claim) để vẫn dọn được hàng chờ.
- **Thuộc:** AA-1146.

### P2 (Cao). Nhân viên content sửa được giá và nhà cung cấp dạng chữ, không có lịch sử

- **Sai ở đâu:**
  - `PATCH /admin/tours/{id}/raw` cần `content.write` (`staff_authz.py:518`). Danh sách trường được sửa gồm
    **`price_raw`** và **`provider`** (`api/routers/admin_pipeline/tour_detail.py:401-405`).
  - Handler UPDATE thẳng `raw_tours`, không ghi người sửa, không giữ giá trị cũ (`:409-447`).
  - Drawer hiện ô sửa Giá và Nhà cung cấp cho **mọi** vai trò, kể cả vai trò không có quyền ghi
    (`frontend/app/admin/_components/TourDetailPanelV2.tsx:661-681`, ô giá `:665`, ô nhà cung cấp `:667`). Người không
    có quyền bấm lưu thì bị 403.
  - `price_raw` là đầu vào của giá tham chiếu: bộ đọc giá so `price_raw_seen` và đánh dấu cần xem lại
    (`services/reference_price/store.py:6, 52-74`). Booking đọc giá tham chiếu qua view `catalog.v_tour_price_reference_v2`.
    Vậy sửa chữ giá ở CIS có thể đẩy tới gợi ý giá ở Booking.
- **Rủi ro:** Trái quyết định "contracting nhập giá ở Booking". Một lần sửa nhầm không truy được ai sửa, sửa từ giá nào.
- **Đề xuất:**
  1. Bỏ `price_raw` và `provider` khỏi `_ALLOWED_RAW_FIELDS`. Hai ô thành chỉ đọc, có chữ "Giá và nhà cung cấp nhập
     ở Booking". Giá "từ" hiện từ `booking.v_from_prices` (đã grant cho CIS).
  2. `provider` thay bằng bộ chọn nhà cung cấp AA (đọc view nhà cung cấp của Booking, T5 / L4).
  3. Mọi lần sửa tour gốc ghi một dòng lịch sử (bảng `raw_tour_revision` theo thiết kế L3) và một dòng audit có
     trước/sau.
  4. Drawer chỉ hiện ô sửa khi `can("content.write")`.
- **Thuộc:** AA-1146 (phần vá nhanh, phương án A) và AA-1148 (bộ chọn nhà cung cấp).

### P3 (TB). Giá tham chiếu vẫn nhập ở CIS, bởi content_lead và customer_success

- **Sai ở đâu:** `reference_price.write` thuộc `admin`, `content_lead`, `customer_success` (`staff_authz.py:174-177,
  188-191`; route `:595-599`). Preset "Pricing team" trên trang Staff gán `customer_success` ở CIS cùng `contracting`
  ở Booking (`api/services/staff_directory.py:131-146`).
- **Rủi ro:** Hai nơi cùng chứa "giá của tour AA": CIS (giá tham chiếu) và Booking (giá "từ", giá hợp đồng). Người dùng
  không biết nơi nào đúng. `content_lead` là người nội dung nhưng sửa được giá.
- **Đề xuất:** Bỏ `reference_price.write` khỏi `content_lead` ngay (giữ quyền đọc). Còn `customer_success` thì là quyết
  định **D5**.
- **Thuộc:** Mới (nhỏ, 1 PR CIS). Nên làm cùng AA-1150 vì cùng preset "Pricing team".

### P4 (Cao). Đại lý vẫn ghi dữ kiện sản phẩm qua Facts Entries, và đè được dữ kiện của AA

- **Sai ở đâu:**
  - Route của đại lý nằm ở **CIS**: `POST/PATCH/DELETE /v1/facts` (`apps/AA-CIS-App/api/routers/v1_facts.py:1-22`).
    Editor và owner của Content studio ghi được.
  - Loại dữ kiện cho phép: `price`, `season`, `visa_entry`, `transfer_time`, `booking_terms`, `other`
    (`services/acp_shared/facts_store.py:25`; CHECK ở CIS 302).
  - Dữ kiện riêng của đại lý **thay** dữ kiện của AA cùng chủ đề trong lúc AI viết bài (`v1_facts.py:9-12`).
- **Rủi ro:** Đại lý gõ "giá 450 USD" hoặc "mùa đẹp: tháng 7" khác dữ kiện AA, và bài T9 dùng số của đại lý. Trái
  quyết định "mọi dữ liệu sản phẩm là của AA" và B6 ("Facts Entries chỉ còn markup và điều khoản bán").
- **Đề xuất:**
  1. Đại lý chỉ còn tạo/sửa loại `booking_terms`. Markup không phải dữ kiện, nó ở luật giá của CRM.
  2. Các loại khác: dòng cũ giữ để đọc, không tạo mới, không sửa, và **thôi đè** dữ kiện AA trong lúc AI viết bài.
  3. Đếm số dòng cũ theo loại trước khi đổi (chưa kiểm, cần DB), ghi số vào PR.
  4. Content studio (`apps/AA-Partner/web/app/(studio)/portal/_components/BrandFacts.tsx`) ẩn các loại bị chặn.
  Xem **D7**.
- **Thuộc:** AA-1144. **Lưu ý:** AA-1144 đang ghi "Partner (+ root)". Phải thêm repo **CIS** vào phạm vi, vì route
  và CHECK nằm ở CIS.

### P5 (Cao). Bản T2 của đại lý lưu mọi trường, không khoá dữ kiện, không có audit

- **Sai ở đâu:**
  - `PATCH /v1/tours/versions/{id}` nhận `edited_content: Optional[dict]`, tức **bất kỳ trường nào**
    (`apps/AA-CIS-App/api/routers/v1_tours.py:1275-1278`).
  - Code lưu nguyên dict thành phiên bản mới (`:1360-1383`). Bộ kiểm "final contract" chỉ chạy ở chế độ REPORT, tức
    chỉ ghi log, không chặn (`:1377-1378`).
  - Tên người sửa lấy từ body (`body.edited_by`, `:1367`), không lấy từ token.
  - Ghi chú trong code: "No audit row" (`:1292`).
  - TripPlanner hiện bản của đại lý trên trang `/{slug}/tours/{tour}` (view `catalog.v_tenant_tour_v1`,
    `apps/AA-TripPlanner-Web/CONTEXT.md:35-37`). Vậy một sự thật bị đổi ở T2 sẽ tới tay khách.
- **Rủi ro:** Đại lý đổi "4 ngày" thành "3 ngày", bỏ "Không bao gồm: vé máy bay", hoặc sửa lịch trình. Khách đặt theo bản
  đó, còn AA vận hành theo bản Master.
- **Đề xuất:**
  1. Chia trường T2 thành hai nhóm. **Câu chữ** (tên hiển thị, mô tả, điểm nổi bật, giọng văn) thì đại lý sửa được.
     **Sự thật** (số ngày, lịch trình theo ngày, bao gồm/không bao gồm, nhà cung cấp, giá) thì không.
  2. Server so với Master: trường "sự thật" bị đổi thì từ chối (422 `fact_locked`). Xem **D8**.
  3. `edited_by` lấy từ token thành viên.
  4. Ghi một dòng audit cho mỗi lần sửa (theo mẫu `v1_facts.py`: ghi sau giao dịch, cố gắng hết sức).
- **Thuộc:** AA-1144 (chặn đại lý đổi sự thật, mục 3 của `advisory-content-editing.md`). Code nằm ở CIS, cùng lưu ý
  repo như P4. Phần tự viết lại T2 khi AA đổi sự thật (T3) vẫn thuộc AA-1146.

### P6 (TB). CRM: mọi vai trò đại lý tạo được nhà cung cấp loại khách sạn, xe, hoạt động

- **Sai ở đâu:**
  - Loại nhà cung cấp riêng còn `accommodation`, `transport`, `activity`, `guide`, `restaurant`, `dmc`
    (`apps/AA-Partner/api/app/ledger/suppliers.py:30-41`; CHECK ở crm-014).
  - Tạo/sửa nhà cung cấp chỉ cần `TRIP_EDIT`, nên cả `assistant` cũng tạo được (`app/routers/ledger.py:282-311`).
  - Danh mục dịch vụ của đại lý còn `transfer` (`app/catalogue/service.py:35`; crm-052).
  - Thêm "phương án của đại lý" vào bất kỳ block nào, kể cả block khách sạn (`app/proposals/builder.py:1349-1373`).
- **Rủi ro:** Đúng những gì L1 đã ghi. Không có thêm đường nào ngoài L1. Đã kiểm: import của đại lý chỉ có khách hàng,
  quan hệ, chuyến, ghi chú (`app/imports/spec.py:23`). Các route agency của Booking (`/b2b`) chỉ báo giá, giữ chỗ,
  đặt chỗ, huỷ; không tạo nhà cung cấp.
- **Đề xuất:** Giữ nguyên phạm vi L1. Thêm 1 dòng vào Done-when: "`assistant` không tạo được nhà cung cấp riêng" (hiện
  `TRIP_EDIT` cho phép), vì nhà cung cấp là danh bạ dùng chung của cả đại lý. Đề xuất gắn `MONEY_FIELDS_EDIT` hoặc một
  action mới `SUPPLIER_MANAGE` (owner, agent).
- **Thuộc:** AA-1144.

### P7 (TB). CRM: đại lý đổi được tên một mục AA trong báo giá

- **Sai ở đâu:** `update_option` chặn đổi giá vốn và nhà cung cấp của mục AA, nhưng **cho đổi `title`**
  (`apps/AA-Partner/api/app/proposals/builder.py:1471-1474`).
- **Rủi ro:** Mục "Khách sạn A, phòng Deluxe" (AA đặt thật) bị đổi thành "Khách sạn B". Khách nhận báo giá và voucher
  một tên, AA đặt một tên khác.
- **Đề xuất:** Xem **D9**. Khuyến nghị: tên mục AA chỉ đọc, đại lý thêm được một dòng ghi chú hiển thị.
- **Thuộc:** AA-1144.

### P8 (Thấp). CRM: đại lý gõ điểm đón và giờ đón cho dòng AA

- **Sai ở đâu:** `PUT /lines/{id}/voucher` áp cho mọi dòng đã xác nhận, kể cả dòng AA (`app/routers/travel_ops.py:259-266`;
  `app/travel_ops/vouchers.py:128-150`). Code ghi rõ điểm đón từ Booking là "a later Booking card" (`vouchers.py:10-11`).
- **Rủi ro:** Giờ đón trên voucher khác giờ AA đã chốt với nhà xe. Hiện là chỗ tạm có chủ đích. Có audit
  (`vouchers.py:150-153`).
- **Đề xuất:** Giữ tới khi Booking trả điểm đón. Khi có thì dòng AA lấy từ Booking và chỉ đọc, đại lý chỉ thêm ghi chú.
  Trong lúc chờ, voucher ghi nhỏ "Điểm đón do đại lý nhập".
- **Thuộc:** Mới (gắn với lát L6 của Booking khi sinh đặt dịch vụ theo từng thành phần).

### P9 (TB). Dữ kiện chung của AA (giá, mùa) do tenant_qa và content_lead gõ tay

- **Sai ở đâu:** Trang Quality › Facts ghi dữ kiện loại `price`, `season` cho mọi đại lý. Route cần `quality.write`
  (`staff_authz.py:587-589`). Quyền này thuộc `admin`, `content_lead`, **`tenant_qa`** (`:174-175, :182-183`).
  Docstring của router lại ghi "admin only" (`api/routers/admin_facts.py:17-18`), tức tài liệu lệch code.
- **Rủi ro:** Một giá gõ tay ở đây đi vào bài viết của mọi đại lý, trong khi giá thật nằm ở Booking. Có audit trước/sau
  (tốt).
- **Đề xuất:** Xem **D10**. Khuyến nghị: loại `price` không gõ tay nữa, mà lấy từ Booking (giá "từ"). Loại `season`
  chỉ `admin` và `content_lead` ghi. `tenant_qa` ghi các loại còn lại. Sửa docstring cho khớp.
- **Thuộc:** Mới (nhỏ). Có thể gộp vào PR CIS của AA-1144 vì cùng bảng `acp_shared.facts`.

### P10 (TB). Nhân viên content chạy được AI trả tiền, kể cả chạy hàng loạt

- **Sai ở đâu:** `content.write` mở `run-tour`, `run-tour-async`, `s1-batch/submit`, `s1/seo-prefetch`
  (`staff_authz.py:506-509`). `s1-batch/submit` gửi một lô viết lại. `seo-prefetch` có thể mua dữ liệu từ khoá.
- **Rủi ro:** Bản tư vấn content (T4.2) ghi "chạy lại AI có tốn phí: content_lead", nhưng code cho cả `content`. Trần
  chi đã chặn mức thiệt hại tối đa, nhưng người chạy không phải người được giao.
- **Đề xuất:** Xem **D3**.
- **Thuộc:** AA-1148.

### P11 (TB). Ảnh: content không có quyền, và chưa có route upload, cắt ảnh, chọn ảnh bìa

- **Sai ở đâu:** Mọi route ảnh hiện là đồng bộ từ Drive và gán ảnh, cần `photos.write` (`staff_authz.py:607-611`).
  Trang `/admin/photos` chỉ cho `admin` và `content_lead` (`frontend/lib/rbac.ts:107`). Không có route upload hay
  cắt ảnh.
- **Rủi ro:** Màn M7 (upload, cắt, chọn bìa) không chạy được với vai trò `content`. Nếu mở cả `photos.write` cho
  content thì content chạy được cả đồng bộ Drive và backfill hàng loạt.
- **Đề xuất:** Xem **D4**: thêm capability hẹp `photos.upload`.
- **Thuộc:** AA-1148.

### P12 (TB). Các màn mới chưa có route, chưa có quyền

Route-policy test (`tests/unit/test_aa882_route_policy.py`) bắt mọi route ghi mới phải có dòng POLICY. Đây là bảng quyền
đề xuất để lane viết thẳng vào spec (mục 4).

- **Thuộc:** AA-1146 (editor, khoá, xuất bản) và AA-1148 (desk, tạo tay, ảnh, hàng loạt).

### P13 (TB). Route trần AI không bắt đăng nhập Cognito, và `budgets` không có audit trước/sau

- **Sai ở đâu:**
  - Settings registry bắt người đổi phải đăng nhập Cognito thật (`api/routers/admin_settings_registry.py:20-26, 48-60`).
  - Các route trần AI thì chỉ đọc vai trò từ header `x-admin-role`:
    - `PUT/DELETE /admin/budgets` (`api/routers/admin_budgets.py:113-175`)
    - reset cầu dao chi bất thường (`api/routers/admin_ai_gateway_spend.py:42-55`)
    - trần đại lý, capacity, hồ sơ AI mỗi app (`api/routers/admin_ai_gateway.py:340, 354, 577-603, 666-701`)
  - Bất kỳ ai giữ admin secret (BFF, CI, Lambda probe) đều gửi được header `admin`, rồi nâng hoặc bỏ trần. Điều này đã
    được ghi là rủi ro còn lại tới GĐ4 (`staff_authz.py:24-31`); settings registry đã tự đóng lỗ này, còn route trần AI
    thì chưa.
  - `admin_budgets.py` không ghi dòng audit có trước/sau. Chỉ có log `spend_budget_updated` và dòng "ai gọi route nào"
    của middleware (`api/middleware/staff_audit.py:1-22`). Các route trần ở `admin_ai_gateway.py` thì có audit.
- **Rủi ro:** Không phải ai cũng giữ secret, nhưng trần AI là tiền thật. Chính sách S279 đòi "admin, có audit, có lịch
  sử".
- **Đề xuất:**
  1. Mọi route **nới** trần (nâng, xoá, reset cầu dao, bật AI cho app) gọi cùng hàm `_verified()` như settings
     registry: phải có phiên Cognito, vai trò đọc từ token.
  2. Route chỉ **hạ** trần thì máy (ví dụ job tự hạ khi cảnh báo) vẫn gọi được.
  3. `admin_budgets` ghi audit `spend_budget.set` / `spend_budget.deleted` có trước/sau, trong cùng giao dịch.
- **Thuộc:** Mới (1 PR CIS nhỏ, 0 USD).

### P14 (Thấp). Vai trò `content_creator` của Booking vẫn nằm trong danh bạ staff của CIS

- **Sai ở đâu:** `BOOKING_ROLES` còn `content_creator` (`api/services/staff_directory.py:118`). Trang Staff vẫn cho
  chọn. Preset "Pricing team" còn nhắc tới nó (`:138`). CHECK `staff_app_grant_role_chk` ở CIS 363 còn giá trị này.
- **Rủi ro:** T13 quyết định ẩn `content_creator` khỏi Booking, nhưng danh bạ ở CIS (nơi duy nhất gán vai trò Booking)
  vẫn gán được.
- **Đề xuất:** Phần CIS của AA-1150: bỏ `content_creator` khỏi danh sách chọn trên trang Staff. Đếm người đang giữ
  (chưa kiểm). Giữ giá trị trong CHECK tới khi đếm = 0, rồi mới bỏ (kiểu expand/contract).
- **Thuộc:** AA-1150 (phần CIS). Review Booking đang chạy chỉ nói tới `staff.py` của Booking, nên cần nhắc để không sót.

### P15 (Thấp). Audit của các việc nhạy cảm: có "ai gọi route nào", thiếu "đổi gì"

| Việc | Hiện có | Thiếu |
|---|---|---|
| Mọi lệnh ghi của staff | 1 dòng/route, ghi sau khi trả lời, lỗi thì chỉ log (`staff_audit.py:1-22`) | Giá trị trước/sau |
| Sửa tour gốc, sửa bản AI viết, promote | Chỉ dòng route + log | Trước/sau, lý do (P2) |
| Trần AI ở `budgets` | Dòng route + log | Trước/sau (P13) |
| Giá tham chiếu, Facts của AA, staff, settings, gateway | Dòng audit có trước/sau | Đủ |
| T2 của đại lý | **Không có gì** (`v1_tours.py:1292`) | Mọi thứ (P5) |
| Facts của đại lý | Audit sau giao dịch, cố gắng hết sức (`v1_facts.py:19-21`) | Đủ cho bây giờ |
| CRM của đại lý | `ctx.audit` mỗi lệnh, ghi cả lệnh bị từ chối (`permissions.py:16-19`) | Đủ |

**Đề xuất:** Gắn vào spec của AA-1146: mọi lệnh ghi qua Tour editor (sự thật, câu chữ, xuất bản, mở khoá, hàng loạt)
ghi audit có trước/sau **trong cùng giao dịch**, không ghi kiểu cố gắng hết sức.

### P16 (Thấp). Tài khoản E2E content (A10) ghi được thật và sẽ xuất bản được trên Dev

- **Sai ở đâu:** Tài khoản E2E content (A10) giữ vai trò `content` với đủ `content.write` và `review.act`
  (`api/services/staff_directory.py:147-154`). Tài khoản này **không** nằm trong nhóm E2E "chỉ đọc, chỉ Dev"
  (`api/core/e2e_staff.py:85-88`). Chỉ CHECK ở DB và trigger Cognito giữ nó.
- **Rủi ro:** Khi L3 bật tự xuất bản trên Dev, bài test E2E có thể đưa một tour thật lên Master trên Dev. TripPlanner Dev
  và các đại lý thử sẽ thấy tour đó.
- **Đề xuất:** Xem **D11**. Lệnh ghi của tài khoản E2E chỉ được vào **tour thử** (đánh dấu như `is_canary` của tenant).
- **Thuộc:** AA-1146.

### Đã kiểm, không có lỗ hổng

- **Trần AI của CIS:** chỉ `admin` nâng hoặc bỏ. `ai_ops` chỉ hạ được: budgets (`admin_budgets.py:124-135, 165`), trần
  đại lý (`admin_ai_gateway.py:340, 354`), hồ sơ app (`:577-603`), capacity (`:669, 701`), reset cầu dao
  (`admin_ai_gateway_spend.py:47`), kết nối (`api/services/llm_connections.py:326`). Settings registry chỉ admin
  (`staff_authz.py:600-604`). Khớp chính sách "ngưỡng chỉnh ở admin" và quyết định S279 Q1.
  Lưu ý: `ai_ops` vẫn đổi được model của từng bước (`ai.admin`). Đó là cấu hình, không phải trần, và trần vẫn chặn tiền.
- **Trần AI của CRM:** cài đặt CRM chỉ `crm-platform-admin` ghi. Owner đại lý đặt ngân sách AI của đại lý mình, không
  vượt trần của gói (`apps/AA-Partner/api/app/llm/agency_ai.py:145-146`).
- **TripPlanner:** đọc trần từ CIS. Thiếu dữ liệu thì dừng AI của đại lý đó (`backend/shared/tenant_budget.py:17-20`).
- **CIS không ghi được vào bảng của Booking:** `cis_app` không có quyền trên `booking.*`. Trang supply content chỉ đọc
  "dữ kiện Booking".
- **Booking `/b2b` cho đại lý:** chỉ báo giá, giữ chỗ, đặt, huỷ. Không có route nào tạo nhà cung cấp hay giá.

---

## 4. Route các màn mới cần, và quyền đề xuất

"Có sẵn" = capability đã có. "Mới" = phải thêm vào `staff_authz.py` (một dòng ROLE_PERMS và các dòng POLICY).

| Màn / việc | Route (đề xuất) | Capability | Ai có |
|---|---|---|---|
| Content desk M0: việc của tôi, chờ duyệt | `GET /admin/content-desk` | `content.read` (có sẵn) | Mọi vai trò có `content.read` |
| Tạo tour tay M2 | `POST /admin/tours` (bản nháp) | `content.write` (có sẵn) | content, content_lead, admin (xem D2) |
| Sửa nháp: sự thật, câu chữ | `PUT /admin/tours/{id}/draft` | `content.write` | content, content_lead, admin |
| Gửi duyệt | `POST /admin/tours/{id}/draft/submit` | `content.write` | như trên |
| Xem trước M3 | `GET /admin/tours/{id}/preview` | `content.read` | mọi vai trò đọc |
| Diff M4 | `GET /admin/tours/{id}/draft/diff` | `content.read` | mọi vai trò đọc |
| Xuất bản M5 (1 tour) | `POST /admin/tours/{id}/draft/publish` | **`content.publish` (mới)** | content_lead, admin; content khi công tắc tắt |
| Trả lại nháp | `POST /admin/tours/{id}/draft/reject` | `review.act` (có sẵn) | content, content_lead, admin |
| Mở khoá Master | `POST /admin/tours/{id}/unlock` | `master.admin` (có sẵn) | content_lead, admin |
| Chạy lại AI có phí (1 tour) | route `run-tour` sẵn có | `content.write` hoặc `ai.rerun` (D3) | xem D3 |
| Sửa hàng loạt M6: tạo nháp | `POST /admin/tours/bulk/drafts` (DRY RUN mặc định) | `content.write` | content, content_lead, admin |
| Sửa hàng loạt: xuất bản | `POST /admin/tours/bulk/publish` | `content.publish` | content_lead, admin |
| Upload, cắt, chọn ảnh bìa M7 | `POST /admin/photos/upload`, `POST /admin/photos/{id}/crop`, `PUT /admin/tours/{id}/cover` | **`photos.upload` (mới, D4)** | content, content_lead, admin |
| Đồng bộ Drive, backfill | route sẵn có | `photos.write` | content_lead, admin (giữ nguyên) |
| Chọn nhà cung cấp AA (T5) | `GET /admin/suppliers/lookup` (đọc view Booking) | `catalog.read` | content, content_lead, admin, tenant_qa |
| Công tắc "cần người thứ hai" | `POST /admin/settings/registry/cis.content.publish_two_person/proposals` | `settings.write` (có sẵn) | admin |

Quy tắc chung cho lane:

- Viewer bị chặn mọi lệnh ghi (đã có ở `READ_ONLY_ROLES`).
- Mọi lệnh ghi của editor ghi audit trước/sau trong cùng giao dịch (P15).
- Giao diện ẩn nút theo `can()`, không chỉ dựa vào 403.

---

## 5. Tài khoản E2E và tài khoản của business owner

| Tài khoản | Vai trò hôm nay (code) | Nên là | Vì sao |
|---|---|---|---|
| E2E content (A10) | `content`, ghi thật, không giới hạn môi trường trong code | `content`, chỉ ghi vào tour thử | Cần chứng minh luồng content (P16) |
| E2E admin (A10b) | `admin`, chỉ đọc, kèm danh sách lệnh ghi được phép, chỉ Dev | Giữ nguyên | Không nên mở thêm lệnh ghi xuất bản cho admin E2E |
| E2E customer_success (A10d) | `customer_success`, chỉ đọc, kèm Booking `contracting` (Dev) | Giữ nguyên. Nếu D5 bỏ `reference_price.write` thì không ảnh hưởng (nó vốn chỉ đọc) | |
| E2E content_lead (chưa có) | – | Đề xuất A10f: `content_lead`, chỉ Dev, chỉ duyệt tour thử | Để chứng minh "người thứ hai" khi bật công tắc (D11) |
| Business owner | Theo log S242: `admin` ở CIS, Booking "None". Cờ owner (`is_owner`): **chưa kiểm** | `admin` ở CIS, kèm cờ owner. Booking chờ T13 | D6 |

---

## 6. Gắn vào issue

| Issue | Thêm vào phạm vi |
|---|---|
| **AA-1144** (L1, CRM) | P4, P5 (code ở **CIS**: `v1_facts.py`, `facts_store.py`, `v1_tours.py`; thêm repo CIS), P6 (`assistant` không tạo nhà cung cấp), P7 (tên mục AA chỉ đọc), P9 nếu gộp |
| **AA-1146** (L3, CIS) | P1 (`content.publish` + công tắc + maker-checker), P2 (khoá `price_raw`/`provider`, lịch sử, drawer theo `can()`), P15 (audit trước/sau), P16 (E2E chỉ ghi tour thử) |
| **AA-1148** (L4, CIS) | P10 (chạy AI có phí), P11 (`photos.upload`), P12 (bảng quyền mục 4), bộ chọn nhà cung cấp |
| **AA-1150** (L7, Booking) | P14 (phần CIS: trang Staff, preset, CHECK), cùng preset "Pricing team" với P3 |
| **Mới** | P3 (bỏ `reference_price.write` của content_lead; phần còn lại theo D5), P8 (điểm đón từ Booking, theo L6), P9 (nếu không gộp vào AA-1144), P13 (Cognito + audit cho trần AI) |

Theo luật Linear: hỏi tech lead trước khi tạo issue mới. P3, P9, P13 nhỏ, đề xuất **gộp thành 1 issue** "CIS:
permission clean-up after S285 decisions".

---

## 7. Quyết định cần tech lead chốt

| Mã | Câu hỏi | Khuyến nghị | Vì sao | Chi phí |
|---|---|---|---|---|
| **D1** | Công tắc "cần người thứ hai" cho xuất bản nội dung: dùng chung công tắc `cis.settings.two_person_approval` hay một công tắc riêng? | **Riêng:** `cis.content.publish_two_person`, chỉ admin đổi, đổi cũng phải qua maker-checker | Cài đặt hệ thống và xuất bản nội dung lên prod vào lúc khác nhau. Gộp thì bật cái này kéo theo cái kia | 0 USD |
| **D2** | Ai được tạo tour tay? Bản tư vấn sửa nội dung ghi "content_lead, admin", còn L4 ghi "nhân viên content" | **Content tạo bản nháp. Xuất bản đi qua cổng D1** | Người làm hằng ngày là content. Cổng xuất bản đã đủ chặn sai. Chặn ngay từ lúc tạo thì chỉ thêm việc cho content_lead | 0 USD |
| **D3** | Nhân viên content có được chạy AI có phí không? | **Cho chạy lại 1 tour** (hiện trước số tiền, trong trần). **Chạy lô** (`s1-batch`, wave, `seo-prefetch`) chỉ content_lead và admin | Sửa 1 tour cần chạy lại ngay. Chạy lô thì tốn tiền theo số tour, nên để người được giao ngân sách làm | 0 USD hạ tầng; giảm rủi ro tiền LLM |
| **D4** | Mở ảnh cho content bằng cách nào? | **Capability mới `photos.upload`** (upload, cắt, chọn bìa cho tour đang sửa). Đồng bộ Drive và backfill giữ ở `photos.write` | Mở cả `photos.write` thì content chạy được việc hàng loạt trên mọi ảnh | ~0 USD (S3 có sẵn, vài MB) |
| **D5** | Giá tham chiếu ở CIS: giữ cho customer_success nhập, hay chuyển hẳn sang Booking? | **Chuyển dần.** Bỏ quyền ghi của content_lead ngay. customer_success nhập tiếp tới khi tour đó có giá trong Booking (L5/L6), rồi trang thành chỉ đọc | Quyết định hôm nay đặt giá ở Booking. Tắt ngay thì nhóm giá mất chỗ nhập trước khi Booking đủ dữ liệu | 0 USD |
| **D6** | Tài khoản business owner nên có quyền gì? | **CIS `admin` kèm cờ owner.** Booking và CRM chờ T13 | Business owner là người giữ khoá thứ hai (access register). Khi bật maker-checker ở prod thì cần một người duyệt thứ hai. Cờ owner cho phép sửa danh bạ staff khi tech lead vắng | 0 USD. Cần kiểm DB trước |
| **D7** | Facts Entries của đại lý còn loại nào? | **Chỉ `booking_terms`.** Các loại khác giữ dòng cũ để đọc, không tạo mới, thôi đè dữ kiện AA | Khớp B6 và "dữ liệu sản phẩm là của AA". Markup đã ở luật giá của CRM | 0 USD. Đại lý mất tính năng tự gõ giá/mùa |
| **D8** | T2 của đại lý: chặn hẳn việc đổi sự thật, hay chỉ cảnh báo? | **Chặn** (422 `fact_locked`), câu chữ vẫn sửa tự do | Cảnh báo thì vẫn tới tay khách qua TripPlanner và báo giá. Chặn là cách duy nhất khớp quyết định hôm nay | 0 USD |
| **D9** | Đại lý có được đổi tên một mục AA trong báo giá không? | **Không.** Tên chỉ đọc, thêm được 1 dòng ghi chú hiển thị | Tên khác thì khách và nhà cung cấp hiểu khác nhau về cùng một dịch vụ | 0 USD |
| **D10** | Dữ kiện chung loại "giá" ở trang Facts của AA: giữ gõ tay hay lấy từ Booking? | **Lấy từ Booking (giá "từ").** Loại `season` chỉ admin và content_lead. `tenant_qa` giữ các loại khác | Một nguồn giá duy nhất. Sửa luôn docstring đang ghi sai "admin only" | 0 USD |
| **D11** | Kiểm luồng "người thứ hai" bằng tài khoản E2E nào? | **Thêm A10f:** `content_lead` chỉ trên Dev, chỉ duyệt tour thử. Đánh dấu tour thử để mọi lệnh ghi của E2E chỉ vào đó | Không mở thêm lệnh ghi cho admin E2E (A10b). Agent tự chứng minh luồng 2 người mà không cần tech lead | 0 USD (Cognito, hộp mail E2E có sẵn) |

**Không cần quyết định** (là việc sửa, đã rõ hướng): P2 (khoá giá và nhà cung cấp trong CIS, theo quyết định hôm nay),
P13 (bắt Cognito và audit cho trần AI), P14 (phần CIS của T13), P15 (audit trước/sau).

---

## 8. Chưa kiểm (cần DB hoặc live, agent làm được, không cần tech lead)

- Ai đang giữ từng vai trò CIS: có ai là `content_lead` chưa, có ai là `ai_ops`, `tenant_qa` chưa
  (`shared.admin_users`). Ở prod mà chưa có `content_lead` thì admin phải xuất bản.
- Business owner có cờ `is_owner` chưa. Booking grant hiện tại là gì.
- Số Facts Entries của đại lý theo loại (P4). Số bản T2 do đại lý tự sửa có đổi trường sự thật (P5).
- Số người đang giữ `content_creator` ở Booking (P14).
- Màn hình: chưa mở trang Staff và trang Facts bằng trình duyệt. Chỉ đọc code.

---

## Đề xuất cuối

1. Chốt **D1–D11** (mặc định theo khuyến nghị).
2. Thêm vào spec trước khi mở lane:
   - **AA-1144:** P4, P5, P6, P7, kèm repo CIS.
   - **AA-1146:** P1, P2, P15, P16.
   - **AA-1148:** bảng quyền mục 4, P10, P11.
   - **AA-1150:** P14 phần CIS.
3. Một issue mới nhỏ (hỏi trước khi tạo): P3 + P9 + P13.
4. Thứ tự: P1 và P2 đi cùng L3 phần 1 (phiên 1). P4 và P5 đi cùng L1 (phiên 1, thêm một PR CIS). P13 làm lúc nào cũng
   được vì độc lập.
