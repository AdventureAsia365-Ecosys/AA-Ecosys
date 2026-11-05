> **CHƯA ĐĂNG — chuyển sang S269** (tech lead 05/11: gom sang phiên sau, rút gọn). Bản rút gọn dưới đây là bản để đăng;
> bản dài phía sau chỉ giữ làm bằng chứng nội bộ. Đăng cùng nháp S269 sau một lần duyệt; PR-20 kỳ 4 soạn từ 09/11.

# Bản rút gọn (để đăng ở S269)

**PR-23 (app đại lý)** — ảnh: `aa1029-from-price-drawer-desktop-light.png`, `aa1036-vi-tours-mobile-dark.png`

@thule App đại lý (Dev, 04–05/11): (1) Content studio có tiếng Việt, đổi ở "Language and dates", mặc định tiếng Anh;
(2) Marketplace hiện giá "From $X per person" từ Booking (đã kiểm trên tour thử, giá mô phỏng); (3) trang Account › Add-ons
để đại lý xin thêm CRM hoặc Trip planner, AA duyệt trong Tenant 360 (chưa thử trọn vòng).

**PR-22 (admin CIS)** — không ảnh

@thule Admin CIS (Dev, 04–05/11): nhân viên AA "xem như đối tác" chỉ xem, có ghi lại (đã kiểm); trang Assignments giao đối
tác cho nhân viên; AI gateway đổi thứ tự model có xem trước và hoàn tác, cảnh báo khi model dự phòng trả lời (đã kiểm);
Usage explorer xem chi phí AI theo app/đối tác/bước, tổng khớp sổ ghi (đã kiểm). Thêm Tenant 360, Catalogue settings,
Place cards (chưa kiểm giao diện).

**PR-26 (CRM)** — không ảnh

@thule CRM (Dev, 04–05/11): rà soát bảo mật 3 vòng trước khi có dữ liệu khách thật, các chặn chính đã thử thật; cảnh báo
khi CRM lỗi hoặc chậm; banner khi AA tạm dừng AI. Tiếp theo: thử tải 50 đại lý mô phỏng.

---

> **CHƯA ĐĂNG.** Nháp Jira S268 (04–05/11/2026), soạn 05/11 ~09:00 +07 (Claude Code, phiên S268). Chưa đăng, chưa sửa
> comment nào, chưa đổi trạng thái issue nào. Tech lead duyệt một lần, rồi đăng theo skill `aa-jira-update`
> (`contentFormat: html`, bảng markdown đổi sang bảng HTML và để ngoài gạch đầu dòng, ảnh upload từng file rồi nhúng bằng
> `inlineFileId` đúng thứ tự).

# S268 — nháp Jira cho chị Thư

Mention khi đăng: `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`
(thay chữ `@thule` ở đầu mỗi nháp). Xưng "em" như bản S267 đã duyệt.

## Đã rà trên Jira (chỉ đọc, 05/11 ~09:00 +07)

- JQL `project in (PR, KAN, CON) AND updated >= "2026-11-04 21:00"` → 0 issue. Không có gì mới sau đợt đăng S267
  (04/11 ~20:20–20:35 +07), không có comment mới của chị Thư.
- Comment mới nhất mỗi epic (đợt S267): PR-20 #10608, PR-22 #10615, PR-23 #10611 + #10612, PR-24 #10614, PR-25 #10610,
  PR-26 #10613. Nháp dưới đây nối tiếp các comment đó, không lặp lại nội dung đã đăng (gói, một app cho đại lý, gỡ đăng
  nhập bằng API key, vai trò nhân viên lát 1, Writing Lab, Spend, giá "from" trên TripPlanner, chuỗi giá Booking).
- JQL `project in (PR, KAN, CON) AND statusCategory != Done`: 125 issue (2 trang). Ngoài các epic PR, toàn bộ là việc nội
  dung/marketing KAN/CON (KAN-86, KAN-89… việc riêng của chị Thư). Không issue KAN/CON nào khớp việc S268 → không soạn.
- **PR-20 kỳ 4 (03–09/11) chưa đến hạn**: một kỳ mỗi tuần lịch, kỳ 4 soạn từ thứ Hai 09/11 (memory
  `platform-report-weekly`). Hôm nay thứ Năm 05/11 → không soạn. Các mục S268 dưới đây sẽ được link từ kỳ 4.

## Danh sách

| # | Issue | Một dòng | Ảnh |
|---|---|---|---|
| 1 | PR-23 | App cho đại lý: Content studio tiếng Việt (mặc định tiếng Anh), giá "From $X per person" trong Marketplace, trang Add-ons để đại lý xin thêm CRM / Trip planner | 2 |
| 2 | PR-22 | Admin CIS: "xem như đối tác" chỉ xem có ghi lại, trang Assignments, Writing Lab thêm Releases + Metrics, Tenant 360 / Catalogue settings / Place cards; AI gateway: đổi thứ tự model có xem trước + hoàn tác, truy vết, cảnh báo khi model dự phòng trả lời, Usage explorer | 0 |
| 3 | PR-26 | CRM: rà soát bảo mật trước khi đại lý thí điểm dùng dữ liệu khách thật, các chặn đã thử thật; cảnh báo lỗi/chậm; banner khi AA tạm dừng AI; thử tải 50 đại lý chạy tiếp | 0 |

Không soạn: PR-20 (chưa đến kỳ), PR-24, PR-25, PR-27, KAN/CON — lý do ở cuối file.

## Kiểm trước khi đăng (ô tech lead chốt)

- [ ] **#1 ảnh 1** chụp tour thử Okinawa (giá 235 USD là dữ liệu mô phỏng, cùng tour đã nêu ở PR-24/PR-25 ngày 04/11). Ảnh
  có dòng "Your advisor confirms the final price." — câu viết cho khách du lịch, có thể cần đổi lời cho đại lý (follow-up đã
  ghi ở Linear). Giữ ảnh hay không là tech lead quyết.
- [ ] **#1 ảnh tiếng Việt:** chọn trang Kho tour trên điện thoại (nền tối). KHÔNG dùng ảnh Tổng quan tiếng Việt
  (`aa1036-vi-dashboard-*`) vì thẻ hạn mức vẫn hiện dòng "Lượt gọi API 0 / 20.000" trong khi đối tác không còn dùng API key
  — dễ gây hỏi. Nếu tech lead muốn khoe trang Tổng quan, thêm `aa1036-vi-dashboard-desktop-light.png` làm ảnh 3 và ghi nhận
  dòng đó là việc dọn tiếp.
- [ ] **#1 Add-ons:** chỉ kiểm thật phần trang hiện CRM và Trip planner. Đường gửi yêu cầu → AA duyệt/từ chối trong
  Tenant 360 chưa chạy trọn vòng trên Dev (chỉ đọc danh sách yêu cầu phía admin, 200). Nháp đã ghi rõ "chưa thử thật".
- [ ] **#2 phần AI gateway:** đây là công cụ vận hành của AA. Theo luật S258 (không đưa quyết định kỹ thuật lên Jira), nháp
  chỉ nêu cái chủ doanh nghiệp nhìn thấy được (xem chi phí AI, cảnh báo khi nội dung do model dự phòng viết), không nêu kiến
  trúc. Tech lead thấy thừa thì bỏ cả đoạn "AI gateway".
- [ ] **#2 câu "trên Dev mọi bước AI đang chạy bằng model dự phòng":** nêu trung tính, không nhắc nhà cung cấp hay sự cố. Bỏ
  nếu tech lead chưa muốn nêu.
- [ ] **#2 không có ảnh:** các trang admin S268 (AI gateway, Usage explorer, Assignments, Xem như đối tác, Tenant 360) cần
  quyền admin / ai_ops; người dùng E2E chụp tự động chỉ có vai trò content nên không chụp được. Hai ảnh
  `cis-*-redirected.png` chỉ chứng minh trang bị chặn với vai trò content → không đính. Nếu tech lead muốn ảnh, chụp bằng
  tài khoản admin thật, che account ID trên mọi trang AI gateway trước khi đính.
- [ ] **#3 PR-26:** rà soát bảo mật là điều kiện trước khi đại lý thí điểm đưa dữ liệu khách thật vào CRM — nêu như tiến độ
  sản phẩm, không nêu chi tiết kỹ thuật. Bỏ chi phí cảnh báo (~0,30 USD/tháng) khỏi Jira (luật 7). Tech lead coi là việc kỹ
  thuật thì rút còn 2 dòng (banner AI + thử tải chạy tiếp).
- [ ] Không có link artifact nào cho chị Thư trong phiên này (trang chiến lược video / post kit là việc nội bộ, đã dừng
  05/11 → không đưa).

---

## 1. PR-23 — Portal tenant / app cho đại lý (04–05/11)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** cả ba thay đổi là thứ đại lý nhìn thấy trong app (Content studio). Comment 04/11 (#10611) ghi "Giao
diện tiếng Việt cho Content studio làm tiếp"; nay đã lên Dev. Giá "from" đã báo ở TripPlanner (PR-24) và Booking (PR-25),
nay hiện thêm trong Marketplace của đại lý.

**Nội dung (sẵn để đăng):**

@thule Cập nhật app cho đại lý (Content studio) ngày 04–05/11 (Dev, đại lý thử Atlas & Hearth):

| Phần | Đã thử trên Dev | Chưa thử |
|---|---|---|
| Content studio tiếng Việt | đạt (05/11): đổi sang tiếng Việt ở "Language and dates", các trang Tổng quan, Kho tour, Nhận diện thương hiệu hiện tiếng Việt, đổi lại tiếng Anh được; mở app mặc định tiếng Anh | — |
| Giá "From $X per person" trong Marketplace | đạt (05/11): thẻ tour và ngăn chi tiết của tour thử hiện "From $235 per person" | tour có bảng giá nhà cung cấp thật (chưa nhập) |
| Đại lý xin thêm CRM hoặc Trip planner | trang Account › Add-ons hiện CRM và Trip planner (05/11) | gửi yêu cầu → AA duyệt hoặc từ chối: đã có trong hệ thống, chưa thử thật trọn vòng |

- **Tiếng Việt:** toàn bộ giao diện Content studio có bản tiếng Việt, đổi bằng một công tắc ngôn ngữ trong "Language and
  dates"; app mở mặc định bằng tiếng Anh. Phần chữ do đại lý nhập (ví dụ hồ sơ thương hiệu) và nội dung tour giữ nguyên ngôn
  ngữ gốc.
- **Giá "from" trong Marketplace:** thẻ tour và ngăn chi tiết tour hiện giá bán lẻ gợi ý lấy từ Booking, cùng cách ghi với trang
  tour TripPlanner, ví dụ "From $235 per person — Suggested price for 2 travellers". Tour chưa có bảng giá nhà cung cấp thì
  không hiện giá. Đã kiểm 05/11 trên **tour thử** Okinawa from Naha (nhà cung cấp và giá là **dữ liệu mô phỏng**, như comment
  ngày 04/11 trên PR-25); các tour khác chưa có giá vì chưa nhập bảng giá thật.
- **Xin thêm CRM / Trip planner:** trong Account › Add-ons, đại lý thấy các phần mua thêm (CRM, Trip planner) và gửi yêu cầu
  ngay trong app. AA nhận thông báo (chuông) và duyệt hoặc từ chối ở trang Tenant 360 của đối tác trong admin CIS; duyệt thì
  gói của đại lý đổi theo. Đã kiểm trang Add-ons trên Dev; đường gửi yêu cầu và duyệt chưa thử thật trọn vòng, sẽ thử cùng
  đại lý thí điểm hoặc tài khoản thử có quyền ghi.

Ảnh theo thứ tự: (1) Marketplace với tour thử: thẻ tour và ngăn chi tiết đều hiện "From $235 per person" (dữ liệu mô phỏng);
(2) Kho tour bằng tiếng Việt trên điện thoại, nền tối.

**Ảnh:**

| # | Tên khi upload | File | Che/cắt |
|---|---|---|---|
| 1 | studio-gia-from-marketplace.png | `docs/audits/2026-11-04-S268-live-verify/screens/aa1029-from-price-drawer-desktop-light.png` | không cần (đại lý thử, tour thử, không email, không account ID) |
| 2 | studio-tieng-viet-kho-tour.png | `docs/audits/2026-11-04-S268-live-verify/screens/aa1036-vi-tours-mobile-dark.png` | không cần |

(Dự phòng, chỉ khi tech lead muốn: `aa1036-vi-dashboard-desktop-light.png` — xem ô kiểm về dòng "Lượt gọi API".)

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Studio EN/VI, mặc định EN | Partner #215 `bda36d1`; UI Smoke (portal) run 41945555534 trên `fa8a82b` (05/11 01:01Z), 67/67 pass, test "Vietnamese through 'Language and dates': dashboard, Marketplace, Brand Identity, then back to English"; ảnh `aa1036-vi-*` |
| Thẻ + ngăn chi tiết "From $235 per person" | Partner #214 `0b20abf`, CIS #1299 `3568851c`, Booking #181 (bk-040 áp 14:56Z 04/11); cùng run 41945555534 test "the priced tour shows 'From $235 per person' on the card and in the drawer"; ảnh `aa1029-from-price-*`; Linear AA-1029 comment 04/11 17:07Z (`booking.v_from_prices` 2 dòng) |
| Tour thử, dữ liệu mô phỏng | `docs/audits/2026-11-04-S267-live-verify/aa1029/README.md` (`SYNTHETIC S267`) |
| Trang Add-ons hiện CRM + Trip planner | Partner #219 `0ce28ce`; run 41945555534 test "Account › Add-ons lists the CRM and the Trip planner" |
| Yêu cầu add-on → staff duyệt/từ chối ở Tenant 360, chuông | CIS #1310 (374, contract) + #1312 `44345fd9`; root #541; phía admin chỉ kiểm `GET /admin/tenants/<canary>/addon-requests` 200 (`.tmp-session/S268/live/aa1036_check.py`, không lưu output) → ghi "chưa thử thật trọn vòng" |

**Chưa kiểm:** gửi một yêu cầu add-on thật và duyệt/từ chối; người dùng mới được mời vào thẳng Content (test đã thêm ở
Partner #219 nhưng không nằm trong lượt smoke 67 test); Deploy Web Dev trên `0ce28ce` đỏ ở bước smoke (deploy + verify
xanh), lượt UI Smoke sau đó trên `fa8a82b` xanh.

---

## 2. PR-22 — CIS admin (04–05/11)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** comment 04/11 (#10615) ghi "Làm tiếp: trang giao đối tác cho nhân viên trên giao diện, chế độ 'xem như
đối tác' (chỉ xem, có giới hạn thời gian, có ghi lại)" — nay đã lên Dev. Thêm các trang admin mới và phần AI gateway mà chủ
doanh nghiệp dùng để xem chi phí AI và chất lượng.

**Nội dung (sẵn để đăng):**

@thule Cập nhật trang quản trị CIS ngày 04–05/11 (Dev):

- **Xem như đối tác (chỉ xem):** nhân viên AA mở được app của một đối tác đúng như đối tác thấy, để hỗ trợ, nhưng chỉ được
  xem: mọi thao tác ghi bị chặn, phiên có giới hạn thời gian, có dòng báo đang ở chế độ xem, và mọi lượt mở đều được ghi lại.
  Đã kiểm 04/11 trên đối tác thử: xem danh sách thành viên được; đánh dấu đã đọc, mở lịch đăng và trang thanh toán đều bị chặn;
  kết thúc phiên thì không xem tiếp được; nhật ký ghi đủ 7 bước. Lần kiểm chạy trên hệ thống đang chạy, chưa chụp giao diện.
- **Trang Assignments:** giao đối tác cho từng nhân viên chăm sóc (người chăm sóc đối tác chỉ thấy đối tác được giao, như
  comment ngày 04/11). Đã kiểm 04/11: danh sách 10 đối tác thử và người phụ trách đọc được; chưa chụp giao diện.
- **Trang mới đã lên Dev, chưa kiểm trên giao diện:** Tenant 360 (một trang cho mỗi đối tác: gói, thành viên, yêu cầu mua
  thêm), Catalogue settings, Place cards. Writing Lab thêm hai phần Releases và Metrics (đã kiểm dữ liệu 05/11).
- **AI gateway (nơi AA điều khiển các model AI):**
  - Admin đổi được thứ tự model và nhà cung cấp cho từng bước viết, có xem trước kết quả, mỗi lần đổi thành một phiên bản và
    hoàn tác bằng một nút, không cần sửa code hay triển khai lại. Đã kiểm 04/11: áp một thiết lập sẵn rồi hoàn tác, cấu hình
    trở về đúng như trước.
  - Mỗi lượt gọi AI có truy vết: model nào được thử, model nào trả lời, mất bao lâu, tốn bao nhiêu.
  - Khi một model dự phòng phải trả lời thay, AA nhận cảnh báo (chuông và email). Đã kiểm 04/11: cảnh báo chuông và email
    được gửi.
  - Nội dung do model dự phòng viết được đánh dấu để kiểm lại (đã có trong hệ thống, chưa kiểm trên giao diện).
  - **Usage explorer** (AI & spend): xem chi phí AI và dữ liệu theo app, đối tác, bước viết, nhà cung cấp; lọc, nhóm, sắp xếp,
    xuất CSV, lưu bộ lọc, bấm vào một ô để xem từng lượt gọi. Đã kiểm 05/11: tổng theo giờ khớp đúng sổ ghi từng lượt gọi
    trong 7 ngày; nhân viên hỗ trợ không mở được trang này.
  - Trên Dev hiện mọi bước AI đang trả lời bằng model dự phòng, vì tài khoản AI trên AWS chưa cho dùng các model mới nhất;
    nội dung vẫn được viết bình thường và cảnh báo ở trên cho thấy rõ việc này.
- **Dữ liệu cá nhân:** cấu hình AI nay ghi rõ bước nào xử lý dữ liệu cá nhân; các bước đó chỉ được chạy trên AWS của mình
  tại Mỹ (theo bảng ngày 04/11 trên PR-20). Hiện chưa bước AI nào được đánh dấu xử lý dữ liệu cá nhân nên quy tắc chưa có
  lượt chạy thật.

**Ảnh:** không (các trang này cần tài khoản admin; lượt chụp tự động dùng tài khoản chỉ có vai trò nội dung).

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Xem như đối tác: 201 read_only, members 200, read-all / slate / billing 403 `view_as_read_only`, end → 401 `view_as_ended`, 7 dòng audit, phiên có `ended_at` | `.tmp-session/S268/live/aa1035_viewas.out` (20/20 PASS, 04/11 ~17:06Z); Linear AA-1035 comment 04/11 17:07Z; CIS #1303 `e86bd3c0`, #1308 `b59c0aea` |
| Dòng báo đang ở chế độ xem (banner) | CIS #1303 (UI); chưa chụp → câu "chưa chụp giao diện" |
| Assignments: 10 đối tác, scope all, 4 nhân viên | aa1035_viewas.out (`/admin/tenant-assignments` 200, tenants=10; `/staff` 200) |
| Tenant 360 / Catalogue settings / Place cards | CIS #1311 `25142dae` (deploy Dev xanh 05/11 00:12Z); không có kiểm live → "chưa kiểm trên giao diện" |
| Writing Lab Releases + Metrics | `.tmp-session/S268/live/aa1039.out` (05/11 ~00:36Z: releases 200, metrics 200) |
| Đổi thứ tự / preset / phiên bản / hoàn tác khớp snapshot | Linear AA-1042 comment 04/11 17:06Z (14/15 PASS; FAIL = 2 route chết chờ 336, không nêu); CIS #1300/#1302 |
| Truy vết từng lượt (pos, status, latency, cost) | AA-1042 comment (trace 11/11 PASS); `.tmp-session/S268/live/aa1042_trace2.out`; CIS #1301 |
| Cảnh báo chuông + email khi fallback | AA-1042 comment: `llm_route_watch` raised `route_fb.a3_place_card_check` (bell + e-mail sent) |
| Đánh dấu nội dung do model dự phòng viết | CIS #1301 "fallback quality guard"; ledger có `quality_signal.route_trace` — mark trên giao diện chưa kiểm |
| Usage explorer 14/14, rollup = ledger 7 ngày, support/viewer 403 | Linear AA-1045 comment 04/11 18:11Z; `.tmp-session/S268/live/aa1045_explorer.out`, `aa1045_rollup.out`; CIS #1306 `c6a31393` |
| Dev: mọi stage đang ở rung dự phòng | AA-1042 comment "Open (a)"; S268 lessons-pending dòng AI gateway |
| pii_class: 40 stage, tất cả `content` | aa1039.out (`/admin/llm-config` 200, classes=['content']); CIS #1309 (373) + #1311 |

**Chưa kiểm:** mọi trang S268 trên giao diện admin (cần phiên admin/ai_ops); CRM daily totals trong explorer (`crm=unavailable`
khi kiểm trong container); "primary trở lại" (không chứng minh được khi model chính còn bị từ chối); vai trò support thật.
Không đưa: số tiền trong lần đối soát (chi phí vào báo cáo kỳ 4), tên model/nhà cung cấp, migration.

---

## 3. PR-26 — CRM cho đại lý (04–05/11)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** rà soát bảo mật CRM là điều kiện trước khi đại lý thí điểm đưa dữ liệu khách thật vào CRM (mốc thí điểm
đã nêu ở PR-20 ngày 04/11). Banner khi AA tạm dừng AI là phần còn thiếu đã ghi ở comment #10613 ("trang Cài đặt → AI của đại lý
chưa báo việc AA đang tạm dừng").

**Nội dung (sẵn để đăng):**

@thule Cập nhật CRM cho đại lý ngày 04–05/11 (Dev):

- **Rà soát bảo mật trước khi có dữ liệu khách thật:** CRM được rà ba vòng độc lập và đã sửa các điểm tìm thấy: giới hạn
  kích thước yêu cầu, chia tài nguyên công bằng giữa các đại lý (một đại lý dùng nhiều không làm chậm đại lý khác), hàng
  đợi việc nền công bằng theo đại lý, và che thông tin nhạy cảm trong nhật ký. Đã thử thật trên Dev 05/11: yêu cầu quá lớn bị
  từ chối; yêu cầu chưa đăng nhập bị chặn trước khi hệ thống đọc dữ liệu gửi lên; tin nhắn giả danh nhà cung cấp SMS bị từ
  chối. Phần chia tài nguyên công bằng chưa thử dưới tải (xem dòng cuối).
- **Theo dõi chất lượng dịch vụ:** AA nhận cảnh báo khi CRM trả lỗi nhiều hoặc chậm bất thường.
- **Banner khi AA tạm dừng AI:** khi AA tắt AI cho cả CRM, đại lý thấy dòng báo ngay trong app thay vì chỉ thấy khi bấm viết
  nháp. Đã có trong hệ thống, chưa thử thật trên giao diện.
- **Tiếp theo:** thử tải với 50 đại lý mô phỏng (chỉ đọc, có hai đại lý dùng dồn dập) để kiểm phần chia tài nguyên; đang dựng
  dữ liệu thử.

**Ảnh:** không.

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| 3 vòng review, các điểm đã sửa | Linear AA-969 comment 04/11 18:52Z; root #539 (`docs/audits/2026-11-04-S268-crm-security-review/`); Partner #218 `e333af53`, crm-api :129 COMPLETED |
| 2 MiB → 413 `body_too_large`; 100 KB chưa đăng nhập → 401 trước khi đọc body; Twilio hook không ký → 403 `invalid_signature` | AA-969 comment "Live (curl)" |
| Cảnh báo lỗi / chậm | Infra #675, Terraform Apply sau duyệt 05/11 ~02:00 (6 add / 1 change / 0 destroy: 2 alarm 5xx rate + p95 latency, 4 query) — checklist S268 dòng AA-969 |
| Banner AI tạm dừng | Partner #219 `0ce28ce` (deploy Dev xanh); không có test smoke/ảnh → "chưa thử thật trên giao diện" |
| Thử tải 50 đại lý chưa chạy, đang seed | AA-969 comment "Pending (b)"; `.tmp-session/S268/live/lt_seed_*.out`; seed hết thời gian chờ ~01:58Z, đọc lại sau |

**Chưa kiểm:** chia tài nguyên công bằng dưới tải; banner trên giao diện; bảo vệ riêng cho đại lý thí điểm (ADR 0019 d16, chưa
làm — không nêu).

---

## Không soạn (và vì sao)

- **PR-20 kỳ 4 (03–09/11):** chưa đến hạn, soạn từ thứ Hai 09/11 (một báo cáo mỗi tuần lịch). Kỳ 4 gom S265–S268 + chi phí
  AWS tháng 10 như đã hẹn ở #10603.
- **PR-24 TripPlanner, PR-25 Booking:** S268 không có thay đổi người dùng thấy (Booking chỉ mở quyền đọc giá cho app đại lý —
  đã nêu trong #1 PR-23).
- **PR-27 Nền tảng:** migration (xoá hẳn cột khoá API cũ, bảng yêu cầu add-on), quy tắc RLS, Terraform cảnh báo, ADR view-as,
  sửa test smoke — việc kỹ thuật của tech lead (memory `jira-no-tech-decisions`).
- **Kế hoạch video (series sản phẩm, UAT) và việc dừng đăng kênh cá nhân:** việc nội bộ của tech lead; series sản phẩm sẽ báo
  khi có video đầu tiên làm xong.
- **KAN/CON:** không có việc liên quan S268.
