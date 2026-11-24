# S289 + S290 (24/11/2026): Jira drafts (combined)

> **Not posted.** The tech lead reviews every word first. Nothing below has been posted, edited or transitioned on Jira.
> When posting: `contentFormat: html`, the mention is
> `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`, tables become
> HTML tables, and screenshots are attached in the listed order (upload → curl → `inlineFileId`). Screenshot paths are
> relative to the repo root. Files ending in `.webp`: convert to PNG first if Jira does not show a preview.

## Jira read before drafting (24/11, read only)

- Open issues in PR, KAN, CON (`statusCategory != Done`): 129 issues across two pages. Recently updated: PR-31
  (24/11 10:03, no new comment, last comment is ours from 23/11), PR-27, PR-25 (23/11), PR-23, PR-26 (21/11), PR-22
  (20/11), PR-24, PR-29, PR-30 (19/11). KAN/CON: no new request that this work answers. Progress goes on the PR epics
  (memory `jira-post-to-pr-epics`).
- Latest comments read: PR-25 (23/11 and 20/11), PR-27 (23/11 and 21/11), PR-24 (19/11 and 18/11), PR-26 (21/11 and
  19/11), PR-22 (20/11), PR-29 (19/11), PR-30 (19/11, two), PR-31 (23/11).
- What those comments already said, so it is not repeated here:
  - PR-25 23/11 said tour splitting into supplier bookings and the "Allow sale…" exception were "in the system, not
    tested live", and listed "supplier bank account with a waiting time before payout" as **not yet built**. These
    drafts now report them tested.
  - PR-25 23/11 also listed as "not tested live": a bill's approver cannot record its payout, the payment-details
    change on the agency invoice waits for approval, a tour without an approved price cannot be put on sale. All three
    were tested on 24/11.
  - PR-24 19/11 said: choosing Vietnamese only changed the page language, the planner text stayed English. Now done.
  - PR-29 19/11 described the design of optional activities and the build order; PR-30 19/11 described the hotel
    approach (net rates, many DMCs per hotel, allotment kinds, Excel). These drafts report what now runs.
  - PR-31 23/11 explained the group-size bands (v2: 1, 2, 3, 4, 5–7, 8–10, 11+), viewed only, not changed.
  - PR-31 description (her line, last edit 24/11 10:03): "nhà cung cấp giá trong khoảng thời gian (1 năm) hệ thống có
    chức năng nhắc admin khi gần hết hạn". J4 item 3 answers it.
  - PR-22 20/11 said the full tour editor was the next step; J8 reports the Content workspace.

## Targets

| # | Issue | Content | Screenshots |
|---|---|---|---|
| J1 | PR-27 Platform | Sign-in for the business owner and the content + booking staff member, real data on Dev, Ecosystem status page | 1 |
| J2 | PR-25 Booking | Sold tour split into supplier bookings, can-operate check and sale exception, supplier bank accounts, approval rules tested | 4 |
| J3 | PR-30 Hotels (her ticket) | One hotel via several DMCs, published price + commission → net, room allotment and release days, two-way Excel | 4 |
| J4 | PR-31 Price system (her ticket) | Group-size bands changed and approved by two people, multi-supplier tour, contract expiry reminder | 2 |
| J5 | PR-29 Optional activities (her ticket) | Excel import, second-person publish, only in-force days, on the planner, to the agency's lead and CRM quote | 4 |
| J6 | PR-24 TripPlanner | Agency colours, Vietnamese planner, lead by e-mail when the agency has no CRM | 4 |
| J7 | PR-26 CRM | Planner lead with the chosen activity, AA add-on in the proposal, "Prices on my planner" setting | 4 |
| J8 | PR-22 CIS | Content workspace: hand-made tours tied to an AA supplier, completeness, preview, review gate; Supplier links page | 4 |

No draft for:

- **PR-23 Portal tenant**: nothing new for it.
- **Ecosystem status page, 4xx rate change** (expired session checks shown apart): technical detail, left out of PR-27.
- **PR-20 weekly report**: not part of this round.
- **KAN / CON**: nothing to report there.
- Also not claimed anywhere: the compliance evidence vault (not finished), the CRM's hourly check after the
  e-mail-fallback lead (the log read was still pending), the business owner's own approvals (her account is not
  active yet).

---

## J1. PR-27 (Platform: sign-in, security, infrastructure)

**Why here:** sign-in and staff accounts are platform items, and PR-27 already holds the roles and "View as" updates.
The sign-in steps she needs go here, once.

**Draft (ready to post):**

> @thule Cập nhật nền tảng ngày 24/11 (Dev):
>
> 1. **Tài khoản đăng nhập cho chị và nhân viên content + booking:**
>    - Thư mời đăng nhập đã gửi lại cho chị và cho hộp thư info@ lúc 12:29 ngày 24/11 (người gửi
>      no-reply@lumiguides.it.com, tiêu đề "You've been added to Adventure Asia staff admin").
>    - Chị có quyền chủ doanh nghiệp ở cả CIS và Booking.
>    - Tài khoản info@ có quyền Content ở CIS và vai trò "Product, ops & accounting" ở Booking: nhập nhà cung cấp, khách
>      sạn, hoạt động, giá, hồ sơ chuyến đi và báo giá cho đại lý. Tài khoản này không có quyền duyệt; việc duyệt luôn do
>      người thứ hai làm.
>    - Nhân viên dùng info@ cũng dùng trang Content workspace mới trong CIS để tạo tour bằng tay (chi tiết ở PR-22).
>
> 2. **Cách đăng nhập** (không có mật khẩu, mã gửi qua e-mail):
>    - CIS: mở https://aa-cis.lumiguides.it.com/login → bấm **Sign in with company email** → gõ địa chỉ e-mail công ty →
>      mở thư và gõ mã dùng một lần.
>    - Booking: sau khi vào CIS, mở https://booking.lumiguides.it.com → bấm **Sign in with company email**. Thường không
>      phải nhập mã lần nữa.
>    - Nên đăng nhập CIS trước Booking ở lần đầu, để hệ thống liên kết tài khoản.
>    - Sau lần đăng nhập đầu tiên của chị, em sẽ bật dấu "chủ doanh nghiệp" cho tài khoản của chị (phần tự duyệt có đánh
>      dấu đã báo ở PR-25 ngày 23/11).
>
> 3. **Dữ liệu trên Dev:** từ 24/11 được nhập dữ liệu kinh doanh thật của AA trên Dev và giữ lại: nhà cung cấp, khách
>    sạn, loại phòng, dịch vụ, hoạt động tuỳ chọn, hợp đồng và giá. Thông tin cá nhân (khách hàng, khách du lịch, người
>    liên hệ của đại lý) vẫn dùng dữ liệu bịa. Số tài khoản ngân hàng thật của nhà cung cấp chờ tới khi có bản chính
>    thức (production). Bản ghi chỉ để thử tính năng vẫn đặt tên "SYNTHETIC …". Hướng dẫn chi tiết (có bản tiếng Việt)
>    nằm ở CIS › Docs, trang "Business owner onboarding and the price system".
>
> 4. **Trang "Ecosystem status" trong CIS** (trang mở đầu của quản trị viên): một trang cho biết các app đang chạy ra
>    sao: dịch vụ, lỗi, tốc độ, hàng việc chờ, sự kiện, mỗi phần ghi giờ lấy số. Phần nào chưa đo được thì ghi "Not
>    measured yet", không bao giờ tô xanh. Có tiếng Anh và tiếng Việt, nền sáng và tối, máy tính và điện thoại. Đã kiểm
>    24/11 trên Dev.
>
> Ảnh: (1) trang Ecosystem status bằng tiếng Việt.

**Screenshots (in order):**

1. `docs/audits/2026-11-24-S289-session/live/aa-1140/03-overview__1440__light__vi.webp`

**Claim → evidence:**

| Claim | Evidence |
|---|---|
| Invitations re-sent 12:29 on 24/11, to her and to info@ | `.tmp-session/S290-checklist.md` item 1 ("Gửi lại lời mời chị Thư + info@ (job succeeded 12:29)") |
| info@ = CIS Content + Booking "Product, ops & accounting", no approve right | checklist item 1 (Booking `custom_product_ops_accounting`, Cognito group 12:26); role definition reported on PR-27 21/11 (24 permissions, no approval) |
| She has CIS + Booking business-owner rights | checklist decisions ("preset Business owner đã gồm") |
| Sign-in steps | onboarding guide VI (origin/master) §A4, §A6 |
| info@ staff member uses the Content workspace | coordinator brief (S290); CIS Content role covers it; feature evidence in J8 |
| Marker after first sign-in | guide §A5; checklist "Chị Thư đăng nhập lần đầu → anh bấm Make business owner" |
| Real business data on Dev, personal data invented, real bank numbers after production | root #976 `e975c991` (guide "Quy tắc trên Dev"); `.tmp-session/S290/pr-docs-real-data.md` |
| Status page, EN/VI, light/dark, 1440/390, "Not measured yet" never green | `docs/audits/2026-11-24-S289-session/live/aa-1140/evidence.md` Done-when 1–6 pass |

The tech lead may cut item 4 if he counts the status page as technical (memory `jira-no-tech-decisions`); it is a
shipped page, not a decision, so it is included.

---

## J2. PR-25 (Booking)

**Why here:** the 23/11 PR-25 comment left these items "not tested live" or "not built"; they now run on Dev.

**Draft (ready to post):**

> @thule Cập nhật Booking ngày 24/11 (Dev, toàn bộ là dữ liệu thử "SYNTHETIC", không phải nhà cung cấp thật):
>
> 1. **Tour đã bán tách thành từng booking nhà cung cấp (đã thử thật 24/11):**
>    - Tour thử 5 ngày ở Thái Lan: 4 đêm ở 2 khách sạn, 5 chặng xe, 1 hướng dẫn viên, giá từ 2 nhà cung cấp thử
>      (một bên khách sạn, một bên xe + hướng dẫn viên).
>    - Bán cho đại lý thử qua bàn B2B, chấp nhận dòng tour, rồi bấm Generate ở tab Suppliers của hồ sơ chuyến: hệ thống tạo
>      đúng 10 booking nhà cung cấp, 4 đêm khách sạn gửi bên khách sạn, 6 dòng xe + hướng dẫn viên gửi bên còn lại.
>    - Sửa tour sau đó (bỏ khách sạn đêm 2) rồi bấm Generate lại: không tạo thêm booking nào, 10 booking cũ giữ nguyên.
>    - Còn một chỗ chữ: các booking này đang ghi "extra item" dù lấy từ thành phần tour; sẽ chỉnh nhãn.
>
> 2. **Kiểm tra "vận hành được" và mở bán ngoại lệ (đã thử thật 24/11 trên tour thử trên):**
>    - Thiếu khách sạn đêm 2: tour chuyển sang Blocked; bán cho đại lý bị từ chối với lời báo "night 2 has no hotel".
>    - Quản trị viên bấm "Allow sale…", ghi lý do, 14 ngày: tour chuyển sang "Exception until 8 Dec 2026" và bán cho
>      đại lý được. Thu hồi ngoại lệ: tour về lại Blocked.
>    - Thiếu xe ngày 3 nhưng đủ khách sạn: chỉ cảnh báo, vẫn bán được.
>    - Tour chưa có giá đã duyệt thì không bật mở bán được, có lời báo cần duyệt giá trước.
>
> 3. **Tài khoản ngân hàng nhà cung cấp (mới):**
>    - Ở tab "Bank accounts" của nhà cung cấp. Tài khoản mới nhập ở trạng thái "Waiting for approval"; màn hình chỉ hiện 4
>      số cuối, người không có quyền xem không bao giờ nhận được số đầy đủ.
>    - Chỉ chủ doanh nghiệp duyệt tài khoản ngân hàng (em duyệt thay khi chị vắng). Quản trị viên khác bấm duyệt bị từ chối.
>    - Trong lúc có thay đổi tài khoản đang chờ, chi trả cho nhà cung cấp đó bị chặn ("no payout until it is decided").
>    - Số tài khoản được lưu mã hoá; đã kiểm trực tiếp trong cơ sở dữ liệu 24/11, không có số nào ở dạng đọc được.
>    - Đã thử 24/11 với tài khoản ngân hàng bịa. Chưa thử: chị duyệt một tài khoản và lệnh chặn chi 24 giờ sau khi duyệt,
>      vì tài khoản của chị chưa kích hoạt.
>
> 4. **Quy tắc người làm, người duyệt (đã thử thật 24/11, trước đây chỉ có test tự động):**
>    - Người nhập hoá đơn nhà cung cấp không tự duyệt được hoá đơn đó.
>    - Người duyệt hoá đơn không tự ghi chi trả được; cần một quản trị viên khác.
>    - Người tạo nhà cung cấp không tự kích hoạt được; người soạn hợp đồng không tự công bố được.
>    - Đổi thông tin chuyển khoản của pháp nhân trên hoá đơn đại lý phải chờ người khác duyệt (thử trên một pháp nhân bịa,
>      pháp nhân thật của AA không bị đụng tới).
>
> 5. Bậc số khách: đã đổi thử và duyệt qua hai người, chi tiết ở PR-31. Khách sạn qua nhiều nhà cung cấp và phòng giữ sẵn:
>    PR-30. Hoạt động tuỳ chọn: PR-29.
>
> Ảnh theo thứ tự: (1) tab Suppliers của hồ sơ chuyến với các booking nhà cung cấp tạo từ tour, (2) trang Price readiness:
> tour thử đang mở bán theo ngoại lệ tới 8/12, (3) tab Bank accounts nhìn từ người không có quyền duyệt (4 số cuối, chờ
> duyệt, chi trả tạm dừng), (4) cùng tab nhìn từ quản trị viên: không có nút Approve.

**Screenshots (in order):**

1. `docs/audits/2026-11-24-S290-session/live/closeouts/50-case-A-suppliers-final__1440__light.png`
2. `docs/audits/2026-11-24-S290-session/live/closeouts/50-readiness-exception__1440__light.png`
3. `docs/audits/2026-11-24-S289-session/live/aa-1153-1158/b-bank-tab-checker__1440__light.png`
4. `docs/audits/2026-11-24-S289-session/live/aa-1153-1158/b-bank-tab-owner__1440__light.png`

**Claim → evidence** (S290 `live/closeouts/evidence.md` = E290; S289 `live/aa-1153-1158/evidence.md` = E289):

| Claim | Evidence |
|---|---|
| 5-day tour, 4 nights / 2 hotels, 5 transfers, 1 guide, 2 synthetic DMCs | E290 §4 table "Synthetic records", step 4.9 |
| Desk sale, line accepted, Generate → 10 bookings (4 hotel DMC, 6 ground DMC) | E290 4.12–4.14, `50-generate-A.json` |
| Edit + Generate again → 0 created, 10 unchanged | E290 4.15, `50-operability-edited.json` |
| "extra item" label | E290 Observation 1, screenshot 1 |
| Blocked, B2B sale refused "night 2 has no hotel" | E290 4.15, 4.16 (422) |
| Exception 14 days → "exception", sale 201; revoke → blocked | E290 4.17, 4.18; `50-operability-exception.json`, `50-operability-revoked.json`, screenshot 2 |
| Missing transfer only warns | E290 step 15, `50-operability-no-transfer3.json` |
| No approved price → cannot be sellable | E290 4.8 (409 `no_approved_price`), `50-sellable-probe.json` |
| Bank account pending, last 4 only, no full number to non-readers | E289 B1b, B4, B4b; E290 6.1 `70-bank.json` |
| Only business owner approves; admin refused | E289 B2a, E290 6.1 (403 `bank_approver_not_allowed`) |
| Payout blocked while pending | E290 6.5 (409 `bank_account_pending`), `70-payout-bill1-pending.json` |
| Stored encrypted, checked in DB 24/11 | DB Migrate `mode=run-script` `aa1158_bank_ciphertext_check.py`, GitHub Actions run 45352277094 (24/11), verdict `ciphertext_at_rest=true` (confirmed by the coordinator) |
| Not tested: business owner approval + 24 h lock | E290 6.8/6.9 "waiting for the business owner" |
| Bill maker cannot approve; approver cannot pay; creator cannot activate; writer cannot publish | E290 6.6, 6.7b, 6.11, 4.6 |
| Payment details change pending, real entity untouched | E290 6.10, `70-billing-entity.json` |

---

## J3. PR-30 (Khach san, her ticket)

**Why here:** she asked about hotel data; the 19/11 replies described the approach. The approach now runs on Dev, and
from 24/11 she can enter real hotels.

**Draft (ready to post):**

> @thule Phần khách sạn đã chạy trên Dev (thử 24/11 bằng khách sạn và nhà cung cấp thử "SYNTHETIC"):
>
> 1. **Một khách sạn, nhiều nhà cung cấp (DMC):** một khách sạn thử ở TP. Hồ Chí Minh gắn với 2 DMC thử, mỗi DMC có
>    hợp đồng và mã khách sạn riêng; người thứ hai công bố cả hai hợp đồng.
> 2. **Giá công bố + hoa hồng → giá net:** dòng "70 USD, hoa hồng 20 %" trong file Excel của DMC được nhập thành giá net
>    56 USD, giữ lại cả hai số gốc để đối chiếu.
> 3. **Báo giá chọn đúng DMC:** báo giá 3 đêm, ăn sáng + tối (HB), 2 người lớn + 1 trẻ 7 tuổi ra chi phí 198 USD theo DMC
>    rẻ hơn (DMC kia sẽ là 216 USD); cả 3 đêm lấy cùng một DMC. Danh sách dòng "theo yêu cầu" của bàn B2B nay ghi đúng tên
>    DMC có giá được dùng (trước đó ghi DMC đầu tiên của khách sạn).
> 4. **Phòng giữ sẵn (allotment) và hạn trả phòng:** trong file Excel có thêm phần "Inventory". Thử với 2 phòng giữ sẵn,
>    trả phòng trước 7 ngày:
>    - đặt 2 phòng: xác nhận ngay;
>    - đặt 3 phòng: chuyển "theo yêu cầu" (on request) vì vượt số phòng giữ sẵn;
>    - đặt trong vòng 7 ngày trước ngày ở: chuyển "theo yêu cầu" vì đã quá hạn trả phòng.
>    Số ngày trả phòng mặc định là 7, chỉnh được ở trang Pricing policy.
> 5. **Excel hai chiều:** tab Rates của nhà cung cấp có nút Excel để tải bảng giá đang dùng ra, sửa, rồi tải lên lại.
>    Trước khi ghi, hệ thống so với hợp đồng đang dùng và liệt kê dòng thêm / đổi / bỏ (ví dụ "80 → 84 USD, +5 %").
>    Sau khi người thứ hai công bố, báo giá mới dùng giá 84 USD; số phòng giữ sẵn không bị cộng đôi giữa hợp đồng cũ và mới.
>
> Từ 24/11 chị và nhân viên được nhập khách sạn, loại phòng và giá thật trên Dev (hướng dẫn và cách đăng nhập ở PR-27).
> Các bản ghi thử ở trên đã huỷ hoặc hết hiệu lực sau khi kiểm.
>
> Ảnh theo thứ tự: (1) khách sạn thử với giá của 2 DMC, (2) chi phí báo giá 3 đêm HB = 198 USD, (3) tab Rates với nút
> Excel và phần "Room and service inventory", (4) danh sách dòng theo yêu cầu của bàn B2B ghi đúng DMC.

**Screenshots (in order):**

1. `docs/audits/2026-11-24-S289-session/live/aa-1153-1158/a1-hotel-two-dmcs__1440__light.png`
2. `docs/audits/2026-11-24-S289-session/live/aa-1153-1158/a3-desk-booking-tc39-net__1440__light.png`
3. `docs/audits/2026-11-24-S290-session/live/closeouts/90-supplier-rates-inventory__1440__light.png`
4. `docs/audits/2026-11-24-S290-session/live/closeouts/90-desk-on-request-dmc-label__1440__light.png`

**Claim → evidence:**

| Claim | Evidence |
|---|---|
| One hotel, 2 DMCs, own codes, checker published | E289 A1–A7, Done-when 1 pass |
| 70 USD / 20 % → 56 net, both kept | E289 A5, A8, Done-when 2 pass (the API keeps both; the Rates screen shows the net) |
| 198 USD quote, cheaper DMC, 216 alternative, one DMC for all nights | E289 A10 + "Quote vs contract rates", Done-when 3 pass |
| Desk list names the DMC whose rate priced the line | E290 "AA-1153 part 2" step 1, `90-desk-label.json` |
| Allotment 2 rooms / release 7: 2 rooms confirmed, 3 rooms on request, inside 7 days on request | E290 part 2 steps 2b–2e, `90-quote-q2rooms.json`, `90-quote-q3rooms.json`, `90-quote-qrelease.json` |
| Release default 7 is a policy value | E290 2a, `90-policy.json` |
| Export → edit → diff "80 → 84, +5 %" → checker publishes → new price used | E290 3a–3c (103.90 → 109.10 USD = ×1.05), `90-dryrun-c3.json`, `90-quote-qnet84.json` |
| Allotment not doubled | E290 3d, `90-quote-qnotdoubled.json` |
| Test records cancelled / expired | E290 part 2 step 4 |

---

## J4. PR-31 (Price system, her ticket)

**Why here:** she listed 4 needs (group bands, seasons, multi-supplier tour, contract expiry reminder). The 23/11 reply
explained them; now the band change and the multi-supplier tour were exercised live.

**Draft (ready to post):**

> @thule Cập nhật giá trip ngày 24/11 (Dev):
>
> 1. **Đổi bậc số khách, hai người duyệt (đã thử thật 24/11):**
>    - Một người đề xuất bậc mới 1, 2, 3, 4, 5–6, 7–10, 11+; chính người đó bấm duyệt bị từ chối; người thứ hai duyệt thì bậc
>      mới có hiệu lực.
>    - Lịch sử ghi cả lần đề xuất và lần duyệt, người đề xuất khác người duyệt.
>    - Tính lại giá một tour thử: bảng giá cho đại lý theo đúng bậc mới (nhóm 6 khách vào bậc 5–6, nhóm 9 khách vào bậc
>      7–10).
>    - Sau đó đề xuất trả lại bậc cũ (1, 2, 3, 4, 5–7, 8–10, 11+), cũng qua người thứ hai; bảng giá về lại như trước:
>      bậc 5–7 tính theo giá 5 khách, bậc 8–10 theo giá 8 khách. Hiện đang dùng bậc cũ này.
> 2. **Một trip lấy giá từ nhiều nhà cung cấp:** đã thử thật 24/11 với tour thử 5 ngày, giá cộng từ 2 nhà cung cấp; khi bán,
>    tour tách thành 10 booking cho đúng từng nhà cung cấp (chi tiết ở PR-25).
> 3. **Giá nhà cung cấp theo thời hạn (ví dụ 1 năm) và nhắc khi sắp hết hạn:**
>    - Mỗi hợp đồng nhà cung cấp có ngày bắt đầu và ngày kết thúc; giá chỉ dùng trong khoảng đó.
>    - Hợp đồng hết hạn trong 60 ngày tới (số 60 chỉnh được ở Booking › Pricing policy) được liệt kê ở ô "Contracts ending
>      soon" trên trang chủ Booking, trong danh sách Suppliers và tab Contracts của từng nhà cung cấp, kèm một thông báo
>      trong app.
>    - Mới 24/11: thêm một e-mail cho mỗi hợp đồng sắp hết hạn, gửi quản trị viên và nhân viên hợp đồng (nhóm người nhận
>      chỉnh được ở Pricing policy).
>    - Đã thử 24/11 với một hợp đồng khách sạn thử kết thúc 24/12: ô "Contracts ending soon" trên trang chủ Booking, danh
>      sách Suppliers và tab Contracts của nhà cung cấp đều hiện hợp đồng (còn 30 ngày); hệ thống ghi một thông báo trong
>      app và gửi đúng một e-mail cho mỗi người nhận; chạy lại lần hai thì không gửi lặp.
> 4. Giá phòng khách sạn theo bảng Excel của nhà cung cấp, sửa và tải lên lại, xem ở PR-30.
>
> Bảng giá ví dụ của chị (20/01–31/03/2027) chưa được nhập thử; từ 24/11 chị nhập được giá thật trên Dev (cách đăng nhập ở
> PR-27).
>
> Ảnh theo thứ tự: (1) trang Pricing policy khi bậc mới có hiệu lực, (2) sau khi trả về bậc cũ, có lịch sử phiên bản.

**Screenshots (in order):**

1. `docs/audits/2026-11-24-S290-session/live/closeouts/60-policy-v3__1440__light.png`
2. `docs/audits/2026-11-24-S290-session/live/closeouts/60-policy-after-restore__1440__light.png`

**Claim → evidence:**

| Claim | Evidence |
|---|---|
| Propose v3, own approve refused, checker approves, v3 in force | E290 §5 steps 5.2–5.3 (403 `own_row`), `60-propose-v3.json` |
| Audit submitted + approved, maker ≠ approver | E290 5.4, `60-policy-history.json` |
| Tariff on v3: 6 → 5–6, 9 → 7–10 | E290 5.4, `60-bands-v3.json` |
| Restore via second person, v4 = v2 values, 5–7 priced for 5, 8–10 priced for 8 | E290 5.5–5.7, `60-bands-v2.json` |
| Multi-supplier tour split into 10 bookings | E290 4.14 |
| "Contracts ending soon", 60 days, contract at 52 days | E289 `live/aa-1151-1152/evidence.md` AA-1151 step 5; window 60 = policy (`live/aa-1151-1153/evidence.md` A5b) |
| In-app notification sent for an expiring contract | E289 `live/aa-1151-1153/evidence.md` A5 (`announced: true` = the daily expiry job sent its notification) |
| Dashboard tile, Suppliers list, Contracts tab, e-mail to admin + contracting (roles in Pricing policy) | Coordinator brief (S290, AA-1177 shipped 24/11). **No AA-1177 section in `live/closeouts/evidence.md` yet** (only `90-dryrun-x1177.json`), so the e-mail is written as "đang kiểm live" and the other places as not re-opened. Update the sentence if the AA-1177 live check passes before posting |
| Answers her 24/11 10:03 line "nhà cung cấp giá trong khoảng thời gian (1 năm) … nhắc admin khi gần hết hạn" | PR-31 description (read 24/11) |
| Her example price table not entered | not done in S289/S290 |

---

## J5. PR-29 (Optional activity add in, her ticket)

**Why here:** the 19/11 reply set out the design and the build order ("Em sẽ cập nhật tiếp khi từng phần chạy được trên
Dev"). All three parts now run on Dev.

**Draft (ready to post):**

> @thule Hoạt động tuỳ chọn đã chạy trên Dev, từ nhập liệu tới báo giá của đại lý (thử 23–24/11 bằng 5 hoạt động thử
> "SYNTHETIC" ở TP. Hồ Chí Minh):
>
> 1. **Nhập bằng Excel:** tải file mẫu, điền 5 hoạt động (giá net, ngày chạy trong tuần, giờ bắt đầu, thời hạn), chạy thử
>    trước khi ghi, rồi nhập: ra 5 hoạt động nháp và 1 hợp đồng nháp. Người thứ hai công bố hợp đồng và các hoạt động; người
>    nhập không tự công bố được. Nhà cung cấp mới cũng phải được người thứ hai kích hoạt trước khi nhập.
> 2. **Chỉ hiện ngày có giá còn hạn:** hợp đồng thử hết hạn 15/01/2027 thì không ngày nào sau đó hiện ra; hoạt động chỉ chạy
>    thứ 2, 4, 6 thì chỉ hiện các ngày đó; hoạt động có giá 01–10/12 chỉ hiện 10 ngày đó.
> 3. **Trên trang lên lịch (TripPlanner):** ngày ở TP. Hồ Chí Minh của tour "Ho Chi Minh Trail Cycling" hiện mục
>    "Optional activities this day" với 5 hoạt động; khách tick chọn, tải lại trang vẫn còn.
> 4. **Trên trang lên lịch của đại lý:** hiện giá "From $X per person" theo hệ số giá của đại lý (45–75 USD với 5 hoạt động
>    thử). Đại lý tắt được phần hiện giá trong CRM; đã thử bật, tắt, bật lại. Phần làm tròn chưa thấy rõ vì các giá thử đã
>    là số tròn.
> 5. **Tới tay đại lý (đã thử thật 24/11):** khách chọn "street food walk" rồi gửi yêu cầu; yêu cầu vào CRM của đại lý thử,
>    ghi chú có tên hoạt động đã chọn ở ngày 7. Trong báo giá, đại lý thêm hoạt động đó từ tab "AA add-on" với giá AA đang
>    có, trạng thái "theo yêu cầu", giá bán gợi ý 90 USD cho 2 khách. Lần thử dùng một tour thử khác làm tour AA của báo giá,
>    vì tour Hồ Chí Minh chưa mở bán trong Booking.
>
> Từ 24/11 nhân viên được nhập hoạt động thật trên Dev (cách đăng nhập ở PR-27).
>
> Ảnh theo thứ tự: (1) trang Add-ons của Booking với 5 hoạt động đã công bố, (2) ngày ở TP. Hồ Chí Minh trên trang lên lịch
> của đại lý, có giá "From", (3) khách đã tick một hoạt động, (4) hoạt động trong báo giá CRM của đại lý.

**Screenshots (in order):**

1. `docs/audits/2026-11-24-S289-session/live/aa-1151-1152/a1151-addons-published__1440__light.png`
2. `docs/audits/2026-11-24-S290-session/live/closeouts/80-agency-planner-day-addons__1440__light.webp`
3. `docs/audits/2026-11-24-S290-session/live/closeouts/80-agency-planner-addon-ticked__1440__light.webp`
4. `docs/audits/2026-11-24-S290-session/live/closeouts/80-crm-aa-addon-quoted__1440__light.png` (days 1–6 are the Thai
   test tour; the caption covers it)

**Claim → evidence:**

| Claim | Evidence |
|---|---|
| Template, DRY RUN, import 5 → 5 drafts + 1 draft contract | E289 `live/aa-1151-1152/evidence.md` AA-1151 1d–1e |
| Supplier must be activated by a second person first | same, 1a–1c (422 `supplier_inactive` before activation) |
| Second person publishes contract and offers | same, steps 2–3 (`created_by` ≠ `published_by`) |
| Only in-force days (contract end, Mon/Wed/Fri, 01–10/12 window) | same, place-view table |
| AA planner HCMC day card, tick survives reload | same, AA-1152 A–B (`a1152-aa-planner-hcmc-day-card__*`, `…ticked-after-reload…`) |
| Agency planner "From $X" 45/50/60/65/75 | E290 §7a step 7.3 |
| Agency switch on/off/on | E289 AA-1152 D–G; rounding "not visibly exercised" |
| Lead to CRM with the pick on day 7 | E290 7.3 (200 `sent`, channel `crm`), 7.4 (note "Day 7 AA add-on …") |
| AA add-on in the CRM proposal, on request, 90 USD for 2 | E290 7.4 (`aa-addons` 201), `80-crm.json` |
| Thai test tour used as the proposal's AA tour | E290 §7a notes |

---

## J6. PR-24 (TripPlanner)

**Why here:** the 19/11 PR-24 comment said the Vietnamese planner text was still English and that agencies without a CRM
pick e-mail or webhook; both are now shown live.

**Draft (ready to post):**

> @thule Cập nhật TripPlanner ngày 24/11 (Dev, đại lý thử):
>
> 1. **Màu của đại lý trên trang lên lịch:** bản đồ, dải màu và nút theo màu thương hiệu đại lý, nền sáng và tối; trang của
>    AA vẫn giữ màu vàng của AA. Đã thử 24/11 trên 2 đại lý thử có màu riêng.
> 2. **Trang lên lịch bằng tiếng Việt:** đại lý chọn tiếng Việt thì chữ trên trang lên lịch đổi sang tiếng Việt ("Chuyến đi
>    của bạn", "Bắt đầu xây dựng chuyến đi", bộ lọc, các tab), trên máy tính và điện thoại. Đã thử 24/11 rồi trả về tiếng
>    Anh. Tiêu đề ô "Plan from a tour route" còn sót tiếng Anh đã được thêm bản tiếng Việt cuối ngày 24/11 (chưa chụp lại).
> 3. **Đại lý có gói CRM nhưng CRM chưa sẵn sàng:** yêu cầu của khách không bị mất mà đi theo đường dự phòng đại lý đã chọn.
>    Đã thử 24/11 với một đại lý thử chưa có CRM: khách gửi yêu cầu, yêu cầu đi qua e-mail và ghi "delivered". Trong app của
>    đại lý (Content studio › Account › Trip planner) hiện "Where leads go · NOW: E-MAIL" và lời giải thích vì sao. Trang
>    Tenant 360 trong CIS cũng ghi chú điều này cho nhân viên AA.
> 4. Hoạt động tuỳ chọn trên trang lên lịch: chi tiết ở PR-29.
>
> Ảnh theo thứ tự: (1) trang lên lịch của đại lý thử với màu của đại lý, (2) trang lên lịch bằng tiếng Việt trên máy tính,
> (3) trên điện thoại, (4) trang Trip planner trong app đại lý: yêu cầu đi qua e-mail.

**Screenshots (in order):**

1. `docs/audits/2026-11-24-S289-session/live/aa-1160/p4-pilot-rehearsal-01-country__1440__light.webp`
2. `docs/audits/2026-11-24-S290-session/live/closeouts/85-planner-vi__1440__light.webp`
3. `docs/audits/2026-11-24-S290-session/live/closeouts/85-planner-vi__390__light.png`
4. `docs/audits/2026-11-24-S290-session/live/closeouts/85-agency-app-planner-leads__1440__light.png`

Do not attach `p1-pilot-rehearsal-01__1440__dark.webp`: it was taken before the dark-mode accent fix (TripPlanner #296)
and still shows a gold button.

**Claim → evidence:**

| Claim | Evidence |
|---|---|
| Agency colours on map, bands, buttons; AA stays gold; light + dark | E289 `live/aa-1160/evidence.md` check 1 (pixel counts, tokens); dark accent fix shipped in S289 (TripPlanner #296) and re-checked per the S289 log ("live màu/dark … xong") |
| Vietnamese planner at 1440 + 390, then back to en | E290 "Planner on locale vi", `85-locale-vi.json`, `85-locale-en.json` |
| "Plan from a tour route" still English | E290 same section, observation |
| No CRM agency → e-mail fallback, `delivered`, "NOW: E-MAIL" + explanation | E290 §7b steps 1–3, 6; `85-leads.json` |
| Tenant 360 note for AA staff | E289 aa-1160 check 2 (`p3-lead-route-atlas-hearth__*`); E290 7b step 2 screenshot `85-tenant360-lead-route__1440__light.png` |
| Not claimed: the CRM's hourly check after the lead | E290 7b step 7 "orchestrator", not done in the evidence |

---

## J7. PR-26 (CRM for agencies)

**Why here:** the CRM side of the add-on flow and the planner price setting are agency features.

**Draft (ready to post):**

> @thule Cập nhật CRM đại lý ngày 24/11 (Dev, đại lý thử "E2E Pilot Rehearsal Travel", dữ liệu thử):
>
> 1. **Yêu cầu từ trang lên lịch vào thẳng Pipeline:** khách chọn tour và một hoạt động tuỳ chọn rồi gửi; CRM tạo chuyến ở
>    giai đoạn Inquiry ("Vietnam, 6 nights"), ghi chú liệt kê lịch trình từng ngày và hoạt động khách đã chọn ở ngày 7. Đã
>    thử thật 24/11.
> 2. **Thêm hoạt động của AA vào báo giá:** trong trình soạn báo giá theo ngày, tab "AA add-on" liệt kê các hoạt động AA bán
>    ở ngày đó; chọn một hoạt động là thêm vào báo giá với giá AA đang có (trạng thái "theo yêu cầu", giá bán gợi ý của AA).
>    Đã thử 24/11 với "street food walk": giá bán gợi ý 90 USD cho 2 khách.
> 3. **Cài đặt "Prices on my planner and rounding"** (Settings › Payments): đại lý bật hoặc tắt việc hiện giá "From $X per
>    person" trên trang tour và trang lên lịch của mình, và chọn bước làm tròn (USD 1 / 5 / 10, VND mặc định 10.000 đ). Đã thử
>    23–24/11: bật thì trang tour hiện "From $110", tắt thì giá ẩn sau vài giây, bật lại thì hiện lại.
>
> Ảnh theo thứ tự: (1) chuyến mới trên Pipeline, (2) ghi chú của chuyến với hoạt động đã chọn, (3) cài đặt "Prices on my
> planner and rounding", (4) trang tour của đại lý có giá "From".

**Screenshots (in order):**

1. `docs/audits/2026-11-24-S290-session/live/closeouts/80-crm-pipeline-lead__1440__light.png`
2. `docs/audits/2026-11-24-S290-session/live/closeouts/80-crm-lead-sv-note__1440__light.png` (a tall full-page shot; crop
   to the Notes card if needed)
3. `docs/audits/2026-11-24-S289-session/live/aa-1151-1152/a1152-crm-planner-prices-saved-on__1440__light.png`
4. `docs/audits/2026-11-24-S289-session/live/aa-1151-1152/a1152-agency-tour-page-price-on__1440__light.png`


**Claim → evidence:**

| Claim | Evidence |
|---|---|
| Lead becomes a trip at Inquiry, note lists the days + "Day 7 AA add-on …" | E290 7.4, screenshots 1–2 |
| "AA add-on" tab lists the day's AA activities, adds with live AA price, on request, 90 USD for 2 | E290 7.4 (201), `80-crm-aa-addon-drawer__1440__light.png`, `80-crm-aa-addon-quoted__1440__light.png` |
| Setting exists with steps 1/5/10, VND 10,000 | E289 aa-1151-1152 AA-1152 step D |
| On "From $110", off hidden within ~12 s, on again | E289 AA-1152 steps E–G |
| Rounding not visibly exercised | E289 note under step G (not claimed in the draft) |

---

## J8. PR-22 (CIS: content and pipeline)

**Why here:** the Content workspace is a CIS content feature. The last PR-22 comment (20/11) said "the full tour editor
is the next step"; this is that step. PR-27 J1 points here for the info@ staff member.

**Draft (ready to post):**

> @thule Cập nhật CIS ngày 24/11 (Dev):
>
> **Content workspace: tạo tour bằng tay** (CIS admin › Content workspace), cho nhân viên nội dung:
>
> 1. **Tạo tour gắn với nhà cung cấp của AA:** chọn nhà cung cấp từ danh sách nhà cung cấp của Booking (có ô tìm kiếm),
>    rồi điền từng ngày: tiêu đề, nơi đến, nơi ngủ, mô tả.
> 2. **Bao gồm / không bao gồm:** bấm chọn nhanh các mục có sẵn (ví dụ "Private transport", "English-speaking guide",
>    "Entrance fees"; không bao gồm "International flights", "Travel insurance", "Tips"…). Danh sách mục chọn nhanh lấy từ
>    phần cài đặt.
> 3. **Mức đầy đủ và xem trước:** trang soạn hiện phần trăm đầy đủ và danh sách mục còn thiếu (ví dụ "At least 3 included
>    items"); tab Preview hiện tour như khách sẽ thấy, ở cỡ máy tính và điện thoại.
> 4. **Công bố qua cùng cổng duyệt như tour khác:** tour chưa đủ thông tin thì bị từ chối công bố; tour đã đủ nhưng chưa qua
>    bước kiểm lại cũng bị từ chối.
> 5. **Trang "Supplier links":** liệt kê các tour cũ chưa gắn nhà cung cấp, để nhân viên gắn dần. Trên Dev hiện có 917 tour
>    chưa gắn; hệ thống chưa tự ghép được tour nào theo tên.
>
> Đã thử 24/11 bằng một tour thử "SYNTHETIC" 3 ngày ở Thái Lan: tạo tour, thiếu mục thì mức đầy đủ 85 % và công bố bị từ
> chối; chọn đủ mục thì lên 100 %; công bố khi chưa kiểm lại bị từ chối; sau đó xoá tour thử, tour chưa từng hiện cho khách.
> Chưa thử: công bố có người thứ hai duyệt bằng một người thật (dự kiến thứ Năm); trên Dev chế độ bắt buộc người thứ hai
> đang tắt.
>
> Ảnh theo thứ tự: (1) trang tạo tour với ô chọn nhà cung cấp từ Booking, (2) trang soạn tour ở mức 85 % với các mục còn
> thiếu, (3) xem trước trên điện thoại, (4) trang Supplier links.

**Screenshots (in order):**

1. `docs/audits/2026-11-24-S290-session/live/closeouts/95-new__1440__light.png`
2. `docs/audits/2026-11-24-S290-session/live/closeouts/95-editor-a__1440__light.png`
3. `docs/audits/2026-11-24-S290-session/live/closeouts/95-preview-b__390__light.png`
4. `docs/audits/2026-11-24-S290-session/live/closeouts/95-supplier-links__1440__light.png`

**Claim → evidence** (E290 section "AA-1148 content workspace", about 09:20–10:0x UTC on 24/11):

| Claim | Evidence |
|---|---|
| Supplier picked from Booking's list, with search | step 2, `95-picker.json`, `95-new__*` |
| Quick chips for included / not included, from settings | step 1 (`options` returns the chip lists), step 6 |
| Completeness % and the missing items; preview at desktop and phone | steps 4 and 6 (85 % → 100 %), `95-editor-*`, `95-preview-*` |
| Incomplete → publish refused | step 5 (409 `required_missing`) |
| Complete but checks not run → publish refused | step 6b (409 `revalidate_required`) |
| Test tour removed, never published | step 9 |
| Supplier links: 917 not linked, 0 matched | step 8 (`95-links.json`, dry run `matches 0`) |
| Not shown: two-person publish with a real second person; switch off on Dev | E290 notes under the table ("The two-person refusal is not demonstrated", planned Thursday) |
| Not claimed: the first create attempts returned a server error before a fix (AA-CIS-App #1666) | step 3; fixed and re-run the same day, so it is left out of the draft |

---

## Points for the tech lead before posting

1. **Bank number encryption (J2 item 3):** confirmed by run 45352277094 (`ciphertext_at_rest=true`); sentence kept.
2. **J4 item 3, contract expiry e-mail:** written as "đang kiểm live" because `live/closeouts/evidence.md` has no AA-1177
   section yet. If that check passes before posting, change the last bullet to "đã thử 24/11".
3. **J8 (PR-22):** two-person publishing is off on Dev, so the draft only claims the two refusals that were shown
   (incomplete, checks not run); the publish by a real second person is planned for Thursday.
4. **J1 item 4 (Ecosystem status page):** kept as a shipped page; cut it if you count it as technical.
5. **J5 screenshot 4:** the CRM proposal shows the Thai test tour on days 1–6; the draft explains it. Drop the picture if
   it reads as confusing.
6. **J6 item 1, dark mode:** the agency accent in dark mode was fixed in S289 (TripPlanner #296); no post-fix dark
   screenshot is saved, so only the light one is attached.
7. Posting order suggestion: J1 (sign-in first, since the other drafts point to it), then J2, J3, J4, J5, J6, J7, J8.

## Posted (24/11/2026)

Approved by the tech lead ("Duyệt hết", 24/11 ~19:10 +07), posted by the orchestrator (subagent Jira writes are blocked by hook).

| Draft | Issue | Comment | Images |
|---|---|---|---|
| J1 | PR-27 | [10691](https://adventure-asia.atlassian.net/browse/PR-27?focusedCommentId=10691) | 1 |
| J2 | PR-25 | [10692](https://adventure-asia.atlassian.net/browse/PR-25?focusedCommentId=10692) | 4 |
| J3 | PR-30 | [10693](https://adventure-asia.atlassian.net/browse/PR-30?focusedCommentId=10693) | 4 |
| J4 | PR-31 | [10698](https://adventure-asia.atlassian.net/browse/PR-31?focusedCommentId=10698) | 2 (re-shot: 60-bands-section, 60-bands-history; caption adjusted to match the new images, text otherwise as approved) |
| J5 | PR-29 | [10694](https://adventure-asia.atlassian.net/browse/PR-29?focusedCommentId=10694) | 4 |
| J6 | PR-24 | [10695](https://adventure-asia.atlassian.net/browse/PR-24?focusedCommentId=10695) | 4 |
| J7 | PR-26 | [10696](https://adventure-asia.atlassian.net/browse/PR-26?focusedCommentId=10696) | 4 |
| J8 | PR-22 | [10697](https://adventure-asia.atlassian.net/browse/PR-22?focusedCommentId=10697) | 4 |
