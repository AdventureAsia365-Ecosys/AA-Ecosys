# S268 + S269 + S270 + KAN-20: nháp Jira gom một lượt (CHƯA ĐĂNG)

> **06/11 ~06:10 +07, tech lead: KAN-20 KHÔNG đăng** (#7 chỉ để tham khảo).
>
> **ĐÃ ĐĂNG 06/11 ~06:40 +07** (tech lead "đăng 6 jira"): PR-23 #10616 (4 ảnh), PR-17 #10617 (1 ảnh, bỏ dòng chi phí), PR-18 #10618 (1 ảnh, che dòng Reason), PR-22 #10619 (2 ảnh), PR-25 #10620 (2 ảnh), PR-26 #10621 (2 ảnh).
> PR-25: tech lead bỏ đoạn "Để chị cân nhắc" (Gold 6 % dưới sàn) và ảnh Agency tiers — **không hỏi chị Thư**. Ảnh add-on / bảng giá Gold / Tenant 360 đã cắt bỏ mã nội bộ.

> **CHƯA ĐĂNG.** Soạn 06/11/2026 ~02:40 +07 (Claude Code, phiên S270). Chưa đăng, chưa sửa comment nào, chưa đổi trạng thái
> issue nào. Tech lead duyệt một lần sáng 06/11, rồi đăng theo skill `aa-jira-update`: `contentFormat: html`, chữ `@thule`
> ở đầu mỗi nháp thay bằng
> `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`, bảng markdown đổi
> sang bảng HTML, ảnh upload từng file rồi nhúng bằng `inlineFileId` đúng thứ tự.
>
> Thay cho bản rút gọn S268 (`docs/audits/2026-11-05-S268-close/jira-drafts.md`) và nháp KAN-20
> (`docs/research/2026-11-05-asian-trails-b2b-benchmark/kan-20-jira-comment-DRAFT.md`): nội dung đã gộp và cập nhật theo
> việc kiểm thật ở S269–S270. Nháp S269 chưa từng soạn riêng (tech lead dời sang S270), nay nằm trong các mục dưới.

## Tóm tắt

| # | Issue | Phiên | Một dòng |
|---|---|---|---|
| 1 | PR-23 Portal tenant / app đại lý | S268, S269, S270 | Studio tiếng Việt; giá "From $X" trong Marketplace; xin thêm CRM / Trip planner chạy trọn vòng; người được mời vào thẳng Content; thông báo khi AA ngừng bán rồi bán lại một tour đã thử thật |
| 2 | PR-17 Tenant viết lại tour đúng giọng thương hiệu | S270 | Chạy thử trọn chuỗi nội dung cho 4 thương hiệu thử: 8/8 tour viết lại giao cho đại lý, xuất DOCX, blog + LinkedIn, không lẫn thương hiệu |
| 3 | PR-18 Quản lý tenant: tạm ngưng, ngừng hợp tác, khôi phục | S268, S270 | "Xem như đối tác" (chỉ xem, có ghi lại) đã có; quá hạn thanh toán thì tự tạm ngưng, trả xong tự mở lại |
| 4 | PR-22 CIS admin | S268, S270 | Menu admin gom nhóm, link cũ tự chuyển; nhân viên chăm sóc chỉ thấy đối tác được giao (đã thử với tài khoản thật); Tenant 360, Place cards, Usage explorer kiểm trên giao diện |
| 5 | PR-25 Booking | S269, S270 | Hạng đại lý 0/3/6 % + giá hợp đồng riêng; bảng giá theo đại lý; hoá đơn đại lý, thanh toán hai người duyệt, tạm dừng giữ chỗ khi quá hạn; **1 câu hỏi: hạ Gold xuống 5 %?** |
| 6 | PR-26 CRM cho đại lý | S268, S269, S270 | Rà soát bảo mật + thử tải 50 đại lý đạt; sao lưu đêm và diễn tập khôi phục cho đại lý thí điểm; trang "AA prices" và giá bán lẻ gợi ý theo % cộng thêm của đại lý |
| 7 | KAN-20 Asian Trails | S269, S270 | Kết quả so sánh B2B với Asian Trails, và các phần đã làm theo đó |

Không soạn: PR-20 (kỳ 4 chưa đến hạn), PR-24, PR-27, các story PR khác, KAN/CON còn lại. Lý do ở cuối file.

## Đã rà trên Jira (chỉ đọc, 06/11 ~02:30 +07)

- JQL `project in (PR, KAN, CON) AND statusCategory != Done`: **125 issue**. Sắp theo `updated`, chỉ CON-7 đổi sau đợt đăng
  S267 (05/11 09:17, không có comment, việc nội dung của chị Thư). Không có comment mới nào của chị Thư từ 04/11 20:26.
- Comment mới nhất đã đọc để không lặp: PR-20 #10608 (04/11, hướng B2B + bảng số khởi điểm), #10603 (02/11, báo cáo kỳ 3);
  PR-23 #10611 + #10612 (04/11); PR-25 #10610 (04/11); PR-26 #10613 (04/11); PR-22 #10615, PR-24 #10614 (04/11, theo nháp
  S268); PR-18 #10486 (19/10, hứa "chế độ xem hỗ trợ riêng ở bước sau"); PR-17 #10475 (15/10, bản đọc thử giọng văn);
  PR-12 #10479 (16/10); KAN-20 #10444 (01/10, so sánh sơ bộ bằng tiếng Anh, tag cả Leigh Wilson và chị Thư).
- Ghép theo chủ đề: "xem như đối tác" và tự tạm ngưng / mở lại đối tác thuộc **PR-18** (không chỉ PR-22), viết lại tour
  theo thương hiệu thuộc **PR-17** (không chỉ PR-23). Bài học S237 (sót PR-18) đã áp.
- **PR-20 kỳ 4 (03–09/11) chưa đến hạn:** kỳ 3 đăng thứ Hai 02/11 (#10603). Một báo cáo mỗi tuần lịch, kỳ 4 soạn từ thứ Hai
  09/11 (memory `platform-report-weekly`). Hôm nay thứ Sáu 06/11 → không soạn.

## Ô tech lead chốt trước khi đăng

- [ ] **Chỉ một câu hỏi cho chị Thư** (Gold 6 % dưới sàn 10 %), nằm ở #5 PR-25. Các câu khác trong ghi chú Booking (giữ 3 hạng?
  lên hạng theo gì? lãi theo kênh? giá hợp đồng là % hay giá cố định? % cộng thêm mặc định cho khách sạn/đưa đón?) **không đưa**.
  Câu "giá đăng sai" trong nháp KAN-20 cũ đã đổi thành câu báo (không hỏi).
- [ ] **#2 PR-17 chi phí:** dòng chi phí (≈ 0,19 USD/tour, ≈ 0,50 USD trọn chuỗi một đại lý) để trong ngoặc vuông, mặc định
  **bỏ** (luật 7). Không đưa nhận xét "đại lý Growth dùng hết 200 lượt ≈ 38 USD, sát trần AI 40 USD" vì đó là câu hỏi về gói;
  nếu muốn, đưa vào báo cáo kỳ 4.
- [ ] **#2 PR-17 nguồn AI:** câu "AI viết nội dung cho đại lý đã chạy lại trên Dev" không nêu tài khoản AI nào. Bảng PR-20
  ngày 04/11 ghi tài khoản Anthropic "đứng tên pháp nhân AA, chị là chủ thanh toán, trần 150 USD/tháng", còn key đang cắm (S269)
  là key được tài trợ. Nếu muốn nói rõ nguồn với chị Thư, tech lead tự thêm; nháp cố ý không nêu.
- [ ] **Ảnh có mã nội bộ phải cắt trước khi đính:** `aa1036-addon-after-desktop-light.png` (dòng "Reason: S269 live check
  (AA-1036)…" — cắt bỏ khung Approved/Reason hoặc không đính); `t360-booking-billing-desktop-light.png` (tên đại lý thử
  "Invented Ledger Lane Travel (AA-1037 check)" ở tiêu đề — cắt phần tiêu đề hoặc không đính);
  `aa1030-bk-tariff-gold-desktop-light.png` (tiêu đề "… (AA-1030 check)" — cắt hoặc không đính). Ảnh `viewas-banner` có dòng
  "Reason: S270 live check of the read-only banner" (mã phiên, không phải mã Linear) — giữ hay cắt tuỳ tech lead.
- [ ] **Ảnh CRM có banner đỏ "A mailbox is disconnected"** (đại lý thử Sen Vàng không nối hộp thư). Ảnh trang AA prices vẫn
  dùng được; ảnh builder dùng bản cắt dòng (`aa1030-crm-builder-suggested-row.png`), bản cắt này có nhãn "AA prices expired:
  refresh them" (giá thử đã quá hạn làm mới) — chú thích ảnh đã nói rõ.
- [ ] **Không đính** mọi ảnh AI gateway / Usage explorer / Spend (có account ID AWS, nằm ở thư mục bằng chứng riêng của phiên),
  và ảnh `cs-tenants-directory-*` (còn hiện nút New tenant / Offboard với vai trò chăm sóc — việc dọn giao diện đang làm).
- [ ] **KAN-20:** chủ đề do Leigh Wilson hỏi, comment trước (#10444) viết tiếng Anh và tag cả hai. Theo luật chỉ tag chị Thư,
  nháp viết tiếng Việt, chỉ tag chị Thư. Nếu tech lead muốn Leigh đọc được, cần bản tiếng Anh và chỉ định tag thêm.
- [ ] Link bản so sánh trong KAN-20 trỏ GitHub repo gốc (đang public, file đã merge ở root #545).

---

## 1. PR-23 — Portal tenant / app cho đại lý

**Vì sao:** cả bốn phần là thứ đại lý thấy trong app. Comment #10611 (04/11) ghi "chưa thử" cho người dùng mới được mời,
giao diện tiếng Việt và thông báo khi AA ngừng bán tour — nay đã thử thật. Nối tiếp bản rút gọn S268.

**Nội dung (sẵn để đăng):**

@thule Cập nhật app cho đại lý ngày 04–05/11 (Dev, đại lý thử Atlas & Hearth):

- **Content studio tiếng Việt:** đổi ở "Language and dates", mặc định tiếng Anh. Đã kiểm 05/11: các trang Tổng quan, Kho tour,
  Nhận diện thương hiệu hiện tiếng Việt, đổi lại tiếng Anh được. Nội dung tour và chữ đại lý tự nhập giữ nguyên ngôn ngữ gốc.
- **Giá "From $X per person" trong Marketplace:** thẻ tour và ngăn chi tiết hiện giá bán lẻ gợi ý lấy từ Booking, cùng cách ghi
  với trang tour TripPlanner. Đã kiểm 05/11 trên tour thử Okinawa from Naha (giá 235 USD là dữ liệu mô phỏng, như comment ngày
  04/11 trên PR-25). Tour chưa có bảng giá nhà cung cấp thì không hiện giá.
- **Xin thêm CRM hoặc Trip planner (Account › Add-ons):** đã thử trọn vòng 05/11: đại lý gửi yêu cầu Trip planner → AA nhận
  chuông và duyệt trong Tenant 360 → trang Add-ons của đại lý chuyển "ON" và gói đổi theo. Chủ đại lý chỉ dùng CRM cũng xin
  được ngay trong CRM (Settings › Add-ons): đã có trong hệ thống, chưa thử trọn vòng vì chưa có đại lý thử thuộc dạng này.
- **Người được mời vào thẳng Content:** đã thử 05/11 với lời mời qua email thật: người được mời nhận lời, vào thẳng Content, chỉ
  thấy CRM khi gói có CRM.
- **Khi AA ngừng bán một tour rồi bán lại:** đã thử thật 05/11 trên một tour chỉ dùng để thử: đại lý nhận chuông và email
  "Tour no longer served", tour ẩn trên TripPlanner; khi bán lại, đại lý nhận "Tour served again" và tour hiện lại; Booking cũng
  nhận thông báo cả hai lần. Phần chuyển bài WordPress về nháp sau 7 ngày chưa thử thật vì chưa có bài thử nào đang đăng
  (site WordPress thử hết hạn).

Ảnh theo thứ tự: (1) Marketplace, tour thử hiện "From $235 per person" (dữ liệu mô phỏng); (2) Kho tour tiếng Việt trên điện
thoại, nền tối; (3) trang Add-ons sau khi AA duyệt Trip planner; (4) chuông của đại lý với thông báo ngừng bán và bán lại tour.

**Ảnh:**

| # | Tên khi upload | File | Ghi chú |
|---|---|---|---|
| 1 | studio-gia-from-marketplace.png | `docs/audits/2026-11-04-S268-live-verify/screens/aa1029-from-price-drawer-desktop-light.png` | không cần che |
| 2 | studio-tieng-viet-kho-tour.png | `docs/audits/2026-11-04-S268-live-verify/screens/aa1036-vi-tours-mobile-dark.png` | không cần che |
| 3 | add-ons-trip-planner-da-duyet.png | `docs/audits/2026-11-05-S269-live-verify/screens/aa1036-addon-after-desktop-light.png` | **cắt** khung "Approved… Reason: … (AA-1036)" hoặc bỏ ảnh |
| 4 | chuong-ngung-ban-ban-lai-tour.png | `docs/audits/2026-11-05-S270-live-verify/aa1039/studio-bell-tour-notice-1440-light.png` | không cần che |

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Studio EN/VI, mặc định EN | Partner #215; UI Smoke run 41945555534 (67/67, 05/11 01:01Z); ảnh `aa1036-vi-*` (S268) |
| "From $235" trên thẻ + ngăn chi tiết, dữ liệu mô phỏng | Partner #214, CIS #1299, Booking #181; run 41945555534; Linear AA-1029 comment 05/11 02:03Z; `docs/audits/2026-11-04-S267-live-verify/aa1029/README.md` |
| Add-on trọn vòng (gửi → chuông → duyệt → ON) | Linear AA-1036 close-out 05/11 09:05Z ("live 1 + 15 + 4 PASS"); ảnh `docs/audits/2026-11-05-S269-live-verify/screens/aa1036-addon-*` |
| Chủ đại lý chỉ dùng CRM xin trong CRM — chưa thử trọn vòng | AA-1036: relay sống trả `addons_no_account` cho đại lý thử không có tài khoản CIS; nhánh 201 chỉ có test `test_aa1036_crm_addons.py` |
| Người được mời vào thẳng Content | AA-1036 "Invited user, live 7/7"; ảnh `aa1036-invite-join-*` |
| Ngừng bán / bán lại: chuông + email, TripPlanner 410 ↔ 308, Booking 1 + 1 | Linear AA-1039 close-out 05/11 16:11Z (12:04–12:07Z); ảnh `studio-bell-tour-notice-*` |
| WordPress về nháp chưa thử | AA-1039: chạy NO_POST; follow-up "restore does not undo a WP draft" |

---

## 2. PR-17 — Tenant viết lại tour đúng giọng thương hiệu của tenant

**Vì sao:** comment cuối (#10475, 15/10) là bản đọc thử giọng văn. S270 chạy thử trọn chuỗi nội dung đại lý trên 4 thương
hiệu thử với AI thật, sau thời gian AI viết bị chặn (rủi ro đã nêu ở PR-20 kỳ 3).

**Nội dung (sẵn để đăng):**

@thule Cập nhật viết lại tour cho đại lý ngày 05–06/11 (Dev, 4 thương hiệu thử: Atlas & Hearth, WildKind, Terra Family, Trail
Pulse):

- AI viết nội dung cho đại lý đã chạy lại trên Dev. Em chạy thử trọn chuỗi như một đại lý thật: tải hồ sơ thương hiệu (file
  Word) → chọn tour → viết lại → gợi ý chủ đề → viết bài → xuất bài.
- **Viết lại tour:** đại lý nhận đủ 8/8 tour (Atlas & Hearth 3, WildKind 3, Terra Family 1, Trail Pulse 1), xuất Word được cả 8.
  Không có từ bị cấm trong hồ sơ thương hiệu, không lẫn tên thương hiệu giữa các đại lý viết cùng một tour.
- **Bài viết:** từ gợi ý chủ đề, hệ thống viết được bài blog và bài LinkedIn theo giọng từng thương hiệu và giao cho đại lý;
  xuất dạng chữ và HTML, HTML có dấu "có AI hỗ trợ" máy đọc được (như comment ngày 04/11 trên PR-23).
- [Chi phí AI thật trên Dev: khoảng 0,19 USD mỗi tour viết lại, khoảng 0,50 USD cho trọn chuỗi một đại lý (1 tour, 2 bài).]
- Bước tiếp: chạy thêm 3 tour mỗi thương hiệu trên đủ các kênh, rồi một đợt lớn hơn.

Ảnh: trang My Tours của thương hiệu thử Atlas & Hearth với 3 tour đã viết lại, trạng thái "Ready".

**Ảnh:**

| # | Tên khi upload | File | Ghi chú |
|---|---|---|---|
| 1 | my-tours-atlas-hearth.png | `docs/audits/2026-11-05-S270-aa741-phase0/screens/b8611143-t2-my-tours-desktop-light.png` | không cần che |

(Kèm thêm được một file Word đã xuất: `docs/audits/2026-11-05-S270-aa741-phase0/exports/b8611143-t2-84e392c3.docx` — tech lead
mở xem trước khi đính.)

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| 4 tenant thử, hồ sơ .docx 4/4 | `docs/audits/2026-11-05-S270-aa741-phase0/README.md` §1; ảnh `*-t0-brand-*` |
| Đại lý nhận đủ 8/8, DOCX 8/8 | README §2 (trạng thái phía đại lý `ai_generated`, không điểm, không cờ); `exports/*.docx` |
| 0 từ cấm, 0 lẫn thương hiệu | README §2 "Tín hiệu cho Writing Lab" |
| Blog + LinkedIn giao cho đại lý, xuất text/HTML có dấu AI | README §2 (T9 `ready`, T11 200, `ai_mark=true`); `exports/b8611143-blog-*.html`, `c3182dd9-linkedin-*.txt`; rerun T8 8/8 sau CIS #1330 (README §6) |
| Chi phí | README §3 (ledger, non-shadow): T2 ≈ 0,19 USD/tour, trọn chuỗi ≈ 0,50 USD, tổng phase 0 ≈ 2,0 USD |

Không nêu (nội bộ): 3/8 bản dưới ngưỡng điểm judge (chỉ Writing Lab thấy, memory `tenant-sees-content-only`); lỗi trần token
đã sửa (CIS #1330); trường `system_prompt` không được điền khi nhập .docx (follow-up).

---

## 3. PR-18 — Quản lý tenant: tạm ngưng, ngừng hợp tác và khôi phục; tenant chỉ thấy nội dung

**Vì sao:** comment #10486 (19/10) ghi "nếu cần xem giúp tenant, mình sẽ làm một chế độ xem hỗ trợ riêng ở bước sau" — nay đã có.
Tự tạm ngưng khi quá hạn thanh toán và tự mở lại là phần tạm ngưng / khôi phục của issue này.

**Nội dung (sẵn để đăng):**

@thule Cập nhật quản lý đối tác ngày 04–05/11 (Dev, đối tác thử):

- **Xem như đối tác (chỉ xem):** từ trang đối tác trong admin CIS, nhân viên AA bấm "View as partner" để xem đúng những gì đối
  tác thấy khi cần hỗ trợ. Chỉ xem được: mọi thao tác ghi bị chặn, phiên tự hết sau 15 phút, đầu trang luôn có dòng báo "Read
  only… Every page you open is recorded", và mỗi lần mở đều được ghi lại. Đã thử 04/11 và 05/11 trên Atlas & Hearth: xem được,
  thao tác ghi bị chặn, kết thúc phiên thì không xem tiếp được, nhật ký ghi đủ từng bước.
- **Quá hạn thanh toán thì tự tạm ngưng, trả xong tự mở lại:** đã thử 05/11 trên một đại lý hư cấu: hoá đơn quá hạn 3 ngày →
  Booking ngừng nhận giữ chỗ mới, CIS tự chuyển đại lý sang tạm ngưng và báo chuông cho AA; ghi nhận thanh toán xong → Booking
  mở lại, lượt kiểm sau của CIS tự trả đại lý về hoạt động. Chưa chụp màn hình phía đại lý lúc bị tạm ngưng.

Ảnh: dòng báo "Viewing Atlas & Hearth as the partner · Read only" khi nhân viên AA xem như đối tác.

**Ảnh:**

| # | Tên khi upload | File | Ghi chú |
|---|---|---|---|
| 1 | xem-nhu-doi-tac-chi-xem.png | `docs/audits/2026-11-05-S270-live-verify/aa1035/viewas-banner-desktop-light.png` | dòng "Reason: S270 live check…" — giữ hoặc cắt (ô chốt) |

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| View-as: chặn ghi, kết thúc → không xem tiếp, nhật ký | Linear AA-1035 comment 04/11 17:07Z (20/20 PASS: 403 `view_as_read_only`, 401 `view_as_ended`, 7 dòng audit) |
| Banner, 15 phút, 4 dòng audit (05/11) | AA-1035 close-out 05/11 14:56Z; ảnh `viewas-banner-*` |
| Quá hạn → chặn giữ chỗ, CIS tạm ngưng + chuông; trả → mở lại | Linear AA-1037 close-out 05/11 16:12Z (11:37–11:54Z, `credit_hold_overdue`, `tenant_billing_tick`) |
| Chưa chụp phía đại lý khi tạm ngưng | không có ảnh trong `docs/audits/2026-11-05-S270-live-verify/` |

---

## 4. PR-22 — CIS admin

**Vì sao:** comment #10615 (04/11) ghi "làm tiếp: trang giao đối tác cho nhân viên, chế độ xem như đối tác". S268 làm xong phần
đó (view-as đưa sang PR-18), S270 kiểm thật vai trò chăm sóc đối tác và chụp các trang admin.

**Nội dung (sẵn để đăng):**

@thule Cập nhật trang quản trị CIS ngày 04–06/11 (Dev):

- **Menu admin gom nhóm:** Home, Tenants, AA Catalogue, Tenant content QA, AI & spend, Writing Lab, Platform, và nhóm Trade mở
  sang Booking. Link cũ tự chuyển sang trang mới (đã kiểm 05/11, 15/15 link).
- **Nhân viên chăm sóc chỉ thấy đối tác được giao:** trang Assignments giao đối tác cho từng nhân viên. Đã thử 05/11 bằng một tài
  khoản chăm sóc đối tác đăng nhập thật: chỉ thấy đối tác được giao; mở đối tác khác thì báo "Tenant not found… outside your tenant
  book"; trang chỉ dành cho admin thì bị chuyển ra; thao tác ghi bị chặn.
- **Tenant 360** (một trang cho mỗi đối tác: gói, thành viên, yêu cầu mua thêm, và từ 05/11 có thêm phần hoá đơn Booking, chỉ
  xem), **Place cards**, **Tenant content QA › Compliance**, **Writing Lab** (Releases, Metrics): đã kiểm và chụp trên giao diện
  05/11, máy tính và điện thoại, nền sáng và tối.
- **Chi phí AI (Usage explorer):** xem chi phí AI theo app, đối tác, bước viết, nhà cung cấp; lọc, xuất CSV, bấm một ô để xem từng
  lượt gọi. Đã kiểm trên giao diện 06/11 với tài khoản admin: tổng 7 ngày khớp đúng sổ ghi từng lượt gọi, CRM cũng hiện trong
  tổng. Khi model AI dự phòng phải trả lời thay, AA nhận cảnh báo chuông và email (đã kiểm 04/11). Ảnh các trang này có thông
  tin tài khoản nội bộ nên không đính kèm.

Ảnh theo thứ tự: (1) tài khoản chăm sóc đối tác mở một đối tác ngoài danh sách được giao: bị từ chối; (2) Tenant content QA ›
Compliance với menu admin mới.

**Ảnh:**

| # | Tên khi upload | File | Ghi chú |
|---|---|---|---|
| 1 | cham-soc-doi-tac-ngoai-danh-sach.png | `docs/audits/2026-11-05-S270-live-verify/aa1035/cs-tenant360-other-refused-desktop-light.png` | không cần che (đã soát) |
| 2 | compliance.png | `docs/audits/2026-11-05-S270-live-verify/aa1039/tenant-qa-compliance-desktop-light.png` | không cần che (đã soát) |

Không dùng: `aa1039/tenants-00000000-…-0001-*` (ảnh chụp lúc trang còn "Loading…", không thấy nội dung Tenant 360).

Chỉ nội bộ, không đính: ảnh AI gateway / Usage explorer / Spend (`aa1042-*`, `aa1045-*`, có account ID AWS, ở thư mục bằng chứng
riêng của phiên); `cs-tenants-directory-*` (nút New tenant / Offboard còn hiện với vai trò chăm sóc, API đã chặn).

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Menu nhóm + Trade, 15/15 link cũ tự chuyển | Linear AA-1039 close-out 05/11 16:11Z (`aa1039-admin-ia-redirects.spec.ts` 15/15); CIS #1326 (Trade) |
| Chăm sóc đối tác: chỉ thấy được giao, 403 nơi khác, trang admin bị chuyển, ghi bị chặn | Linear AA-1035 close-out 05/11 14:56Z (API 7/7, Playwright Cognito thật, `e2e_read_only`); 28 ảnh `docs/audits/2026-11-05-S270-live-verify/aa1035/` |
| Tenant 360 Billing chỉ xem | Linear AA-1037 close-out (CIS #1326: API 200, "Open in Booking"); ảnh `aa1037/t360-booking-billing-*` |
| Tenant 360, Place cards, Compliance, Writing Lab chụp 1440/390 sáng/tối | AA-1039 close-out (48 ảnh R6 trong `aa1039/`: `places-cards-*`, `tenant-qa-compliance-*`, `lab-t9-social-tab-*`); Tenant 360 thấy rõ ở `aa1037/t360-booking-billing-*` (ảnh R6 `tenants-…-0001-*` chụp lúc còn "Loading…") |
| Usage explorer trên giao diện, rollup = ledger 7 ngày, CRM có trong tổng | Linear AA-1045 close-out 05/11 18:13Z (1.058 dòng, 1,982953 USD hai phía; `crm.status = ok`) |
| Cảnh báo fallback chuông + email | Linear AA-1042 comment 04/11 17:06Z (`route_fb.a3_place_card_check`) |

Không nêu (việc kỹ thuật, memory `jira-no-tech-decisions`): thứ tự model / key Anthropic / catalog 13 model, route control, tab
Guide, nút "primary back" còn chờ tài khoản AI trên AWS.

---

## 5. PR-25 — Booking

**Vì sao:** comment #10610 (04/11) ghi "các số đặt cọc, thuế sẽ đổi được khi làm xong phần Booking cho đại lý" và bảng PR-20
#10608 có "3 hạng đại lý 0/3/6 %, cọc 30 %". Phần Booking cho đại lý (hạng, bảng giá, hoá đơn, công nợ) nay đã chạy trên Dev.
Câu hỏi duy nhất của đợt này nằm ở đây.

**Nội dung (sẵn để đăng):**

@thule Cập nhật Booking cho đại lý ngày 05/11 (Dev, đại lý hư cấu, giá mô phỏng):

- **Hạng đại lý:** Standard 0 %, Silver 3 %, Gold 6 % giảm trên giá cho đại lý, theo bảng ngày 04/11 trên PR-20; giá bán lẻ gợi ý
  giữ nguyên cho mọi đại lý. Một đại lý có thể có giá hợp đồng riêng thay cho hạng. Mỗi mức giảm hay giá hợp đồng mới cần một
  nhân viên nhập và một nhân viên khác duyệt. Đã thử 05/11 với hai đại lý hư cấu trên cùng một tour, cùng ngày, giá cho 2 khách:
  Silver 153,79 USD, Gold 149,03 USD; thêm giá hợp đồng 10 % cho đại lý Gold → 142,69 USD; hết hợp đồng → về lại giá Gold.
- **Bảng giá theo từng đại lý:** giá của đúng đại lý đó theo tour, mùa, số khách; tải CSV hoặc in. Nhân viên xem trong Booking,
  đại lý xem trong CRM (xem PR-26). Đã kiểm 05/11: bảng giá khớp đúng giá báo cho từng hạng; bản của đại lý không lộ giá vốn hay lãi.
- **Hoá đơn và công nợ đại lý:** hoá đơn phí phần mềm và hoá đơn quyết toán tour đánh số liên tục; ghi nhận thanh toán cần một
  người nhập và một người khác duyệt (người nhập không tự duyệt được). Quá hạn thì Booking ngừng nhận giữ chỗ mới và CIS tạm
  ngưng đại lý; trả xong thì tự mở lại (xem PR-18). Admin CIS xem được hoá đơn của đại lý ở Tenant 360 (chỉ xem, có nút mở sang
  Booking). Đã thử trọn vòng 05/11 trên một đại lý hư cấu: hoá đơn phí phần mềm 299 USD và hoá đơn cọc 300 USD được tạo tự động.
  Email nhắc nợ chưa thử thật vì đại lý hư cấu không có email kế toán.
- **Đã có trong hệ thống, chưa thử thật:** phí huỷ hiện ngay trong báo giá và giữ chỗ; phiếu xác nhận đặt chỗ cho đại lý (không có
  tên khách); file xuất hoá đơn và thanh toán theo kỳ cho kế toán.
- **Phần khách lẻ:** mọi thao tác ghi cho khách lẻ trong Booking nay đều bị từ chối (đã kiểm 05/11), dữ liệu cũ giữ để tra cứu.
- **Nhập bảng giá nhà cung cấp:** file Excel theo mẫu AA nhập được vào Booking; chạy thử trước để xem sẽ tạo bao nhiêu giá và tour
  nào sẽ có giá, rồi mới ghi thật (đã thử 05/11 trên nhà cung cấp hư cấu, không để lại dữ liệu). Báo cáo mới "tour nào đã có giá"
  (tải CSV, không có cột giá vốn hay lãi): hiện 892 tour, 2 tour có giá, 890 tour chưa gắn khách sạn và dịch vụ. Đây là phần dữ
  liệu cần nhập để mọi tour có giá; hệ thống đã sẵn sàng nhận.

**Để chị cân nhắc (một câu):** với quy tắc B2B hiện tại (lãi mục tiêu 15 %, sàn 10 %, phí thẻ 3 %), hạng Gold giảm 6 % thì AA còn
khoảng 9,8 %, dưới sàn 10 % (trang Agency tiers đang báo "Below floor", ảnh 1). Em đề xuất tạm hạ Gold xuống 5 % cho tới khi ký các
hợp đồng đại lý đầu tiên. Cách khác: giữ 6 % và chấp nhận Gold dưới sàn, hoặc nâng lãi B2B (ví dụ 17 %) để mọi hạng trên 10 %. Đổi
mức nào cũng chỉ là sửa số trên trang, không cần sửa code.

Ảnh theo thứ tự: (1) trang Agency tiers: ba hạng, lãi còn lại của AA, Gold báo "Below floor"; (2) bảng giá của đại lý hạng Gold;
(3) Tenant 360 trong admin CIS: hoá đơn Booking của đại lý, chỉ xem.

**Ảnh:**

| # | Tên khi upload | File | Ghi chú |
|---|---|---|---|
| 1 | hang-dai-ly-gold-duoi-san.png | `docs/audits/2026-11-05-S270-live-verify/screens/aa1030-bk-tiers-desktop-light.png` | không cần che (đã soát) |
| 2 | bang-gia-dai-ly-gold.png | `docs/audits/2026-11-05-S270-live-verify/screens/aa1030-bk-tariff-gold-desktop-light.png` | **cắt** tiêu đề "Tariff: Invented Heron Bay Journeys (AA-1030 check)" hoặc bỏ ảnh (dòng 2 khách = 149,03 USD khớp câu Gold) |
| 3 | tenant-360-hoa-don-booking.png | `docs/audits/2026-11-05-S270-live-verify/aa1037/t360-booking-billing-desktop-light.png` | **cắt** tiêu đề "… (AA-1037 check)" hoặc bỏ ảnh |

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Hạng 0/3/6 %, maker-checker, giá hợp đồng + end card | Booking #188 (bk-043), #190; Linear AA-1030 S269 comment 05/11 10:36Z |
| Silver 153,79 / Gold 149,03 / hợp đồng 142,69 / hết hợp đồng 149,03 | Linear AA-1030 close-out 05/11 15:46Z |
| Bảng giá = giá báo (124,21 / 120,37), CSV, bản đại lý không lộ card/net/cost/margin | AA-1030 close-out; Booking #192; ảnh `aa1030-bk-tariff-*` |
| Hoá đơn 299 + 300, đánh số, maker-checker, quá hạn → `credit_hold_overdue`, CIS tạm ngưng / mở lại | Linear AA-1037 close-out 05/11 16:12Z (AAS-2026-000001, AAT-2026-000001) |
| Tenant 360 hoá đơn chỉ xem + "Open in Booking" | AA-1037 close-out (CIS #1326); ảnh `aa1037/t360-booking-billing-*` |
| Email nhắc nợ chưa thử | AA-1037: "credit_stop reminder was skipped… no billing e-mail. That is by design." |
| Phí huỷ, phiếu xác nhận, CSV kế toán chưa thử thật | Booking #191 (G1/G2/G5) merged + deploy; không có lần kiểm chức năng sống (S269 chỉ kiểm route 401) |
| Khách lẻ: mọi thao tác ghi bị từ chối | AA-1037 close-out: Booking #194, 34/34 trả 410 `b2b_only`, 0 dòng B2C đổi |
| Nhập bảng giá Excel 19/19 (chạy thử 6 giá, ghi thật trong transaction rồi rollback); báo cáo 892 / 2 / 890; CSV không cột net/margin/cost | Linear AA-1029 close-out 05/11 19:54Z; Booking #198 (`5066f753`) |
| Gold ≈ 9,8 % dưới sàn 10 %, phương án (a)/(b)/(c), tech lead nghiêng (b) | Booking `docs/implementation-notes/AA-1030.md` "Questions for the business owner" câu 2; ảnh tiers (9,77 %) |

Không nêu: Booking ghi nhận số hoá đơn điện tử (DEV-…) nhưng nối API hoá đơn điện tử là việc sau; xoá hẳn bảng khách lẻ (DRY RUN,
chưa làm).

---

## 6. PR-26 — CRM cho đại lý

**Vì sao:** comment #10613 (04/11) ghi "trang Cài đặt → AI chưa báo việc AA đang tạm dừng (làm tiếp)"; S268–S269 làm phần chuẩn bị
cho đại lý thí điểm đưa dữ liệu khách thật vào CRM; S270 thêm giá AA và giá gợi ý trong CRM.

**Nội dung (sẵn để đăng):**

@thule Cập nhật CRM cho đại lý ngày 04–05/11 (Dev, đại lý thử, dữ liệu mô phỏng):

- **Chuẩn bị cho đại lý thí điểm dùng dữ liệu khách thật:**
  - CRM được rà soát bảo mật ba vòng độc lập, các điểm tìm thấy đã sửa; các chặn chính đã thử thật trên Dev 05/11 (yêu cầu quá
    lớn, yêu cầu chưa đăng nhập, tin nhắn giả danh nhà cung cấp SMS đều bị từ chối).
  - Thử tải 05/11 với 50 đại lý mô phỏng trong 8,5 phút: 6.482 yêu cầu, 0 lỗi; hai đại lý dùng dồn dập cùng lúc không làm chậm các
    đại lý còn lại (thời gian phản hồi của các đại lý khác vẫn dưới 0,3 giây).
  - Đại lý thí điểm có sao lưu riêng mỗi đêm; các việc dọn dữ liệu tự động bỏ qua đại lý thí điểm. Diễn tập khôi phục 05/11 trên
    đại lý thử Sen Vàng: khôi phục đủ 5.206/5.206 dòng, không sai lệch.
  - AA nhận cảnh báo khi CRM lỗi nhiều hoặc chậm bất thường.
- **Banner khi AA tạm dừng AI:** khi AA tắt AI cho cả CRM, đại lý thấy dòng báo ngay trong app. Đã có trong hệ thống, chưa thử thật
  trên giao diện.
- **Trang "AA prices":** chủ đại lý và nhân viên bán hàng xem giá AA dành cho đại lý mình theo tour, mùa, số khách (đã trừ mức giảm
  theo hạng), đổi tiền tệ, tải CSV, in; vai trò trợ lý không xem được. Đã kiểm 05/11 bằng chủ đại lý thử Sen Vàng đăng nhập thật,
  máy tính và điện thoại. Hiện chỉ đổi được những tiền tệ AA đã duyệt tỷ giá (USD, EUR…).
- **Giá bán lẻ gợi ý theo % cộng thêm của đại lý:** đại lý đặt % cộng thêm trên giá AA (Settings › Payments); khi thêm tour AA vào
  đề xuất cho khách, CRM gợi ý giá bán theo % đó, bấm "Use" để dùng. Đại lý không đặt % thì CRM gợi ý giá bán lẻ của AA. Đã thử 05/11:
  với 2 khách, cộng thêm 20 % trên giá AA 158,54 USD → gợi ý 190,25 USD; không đặt % → gợi ý 200 USD (giá bán lẻ AA 100 USD/khách).
  Cảnh báo khi giá bán thấp hơn giá công khai của AA vẫn giữ.

Ảnh theo thứ tự: (1) trang AA prices của đại lý thử Sen Vàng (dòng đỏ phía trên là do đại lý thử chưa nối hộp thư); (2) dòng tour AA
trong đề xuất với giá gợi ý "Suggested 190.25 USD · your markup on AA's price" (giá thử đã quá hạn nên có nhãn "refresh").

**Ảnh:**

| # | Tên khi upload | File | Ghi chú |
|---|---|---|---|
| 1 | crm-aa-prices.png | `docs/audits/2026-11-05-S270-live-verify/aa1030/aa1030-crm-aa-tariff-usd-1440-light.png` | không cần che (đã soát) |
| 2 | crm-gia-goi-y.png | `docs/audits/2026-11-05-S270-live-verify/screens/aa1030-crm-builder-suggested-row.png` | bản cắt dòng, không cần che |

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Rà soát 3 vòng, các chặn đã thử (413 / 401 trước khi đọc body / 403 chữ ký) | Linear AA-969 comment 04/11 18:52Z; root #539 `docs/audits/2026-11-04-S268-crm-security-review/`; Partner #218 |
| Thử tải 50 đại lý: 6.482 yêu cầu, 0 lỗi, p95 238/238/288 ms, 2 đại lý ồn | Linear AA-969 close-out 05/11 08:51Z; `docs/audits/2026-11-05-S269-aa969-loadtest/` (`k6-summary.json`) |
| Sao lưu đêm, dọn dữ liệu bỏ qua thí điểm, diễn tập 5.206/5.206 | AA-969 close-out (Partner #223/#224, CIS #1314, Booking #182); `restore-drill.json` |
| Cảnh báo lỗi / chậm | Infra #675 (Terraform Apply 05/11 ~02:00) |
| Banner AI tạm dừng — chưa thử trên giao diện | Partner #219; không có ảnh/smoke |
| AA prices: owner + agent, assistant bị từ chối, CSV, in, 390 tối, 16/17 | Linear AA-1030 close-out 05/11 15:46Z (Partner #235 `a1082a9f`); ảnh `aa1030/aa1030-crm-aa-tariff-*` |
| Chỉ tiền tệ đã duyệt tỷ giá | S270 checklist "AA-1029 follow-up live": AUD → 422 rõ ràng, VND 200 (Booking `62ac390`, CRM `8575fada`) |
| 158,54 → 190,25 (20 %); không markup → 200 | AA-1030 close-out; ảnh `aa1030-crm-builder-suggested-*`, `aa1030-crm-settings-payments-markup-*` |

Không nêu: lỗi xuất dữ liệu đại lý bắt được khi diễn tập và đã sửa (Partner #230) — lỗi đã tự xử lý (luật 7).

---

## 7. KAN-20 — look at IT solutions from Asian trails

**Vì sao:** comment #10444 (01/10) hứa "will update this ticket" khi thiết kế giá và đặt chỗ B2B. Bản so sánh làm xong ở S269, và các
phần học được từ đó đã làm ở S269–S270. Nháp cũ (S269) viết "đã lên kế hoạch" cho hạng đại lý, hoá đơn, công nợ — nay đổi theo trạng
thái thật trên Dev.

**Nội dung (sẵn để đăng):**

@thule Dạ chị,

Em đã so sánh xong hệ thống B2B của Asian Trails với phần B2B mình làm cho đại lý. Nguồn chỉ lấy từ trang công khai của Asian
Trails, Lemax (phần mềm back office họ dùng) và báo ngành, có ghi ngày truy cập.

**Asian Trails có gì (theo nguồn công khai):**

- **eConnect:** cổng đặt chỗ cho đại lý, miễn phí đăng ký, đặt thời gian thực khách sạn, tour, đưa đón, tour nhiều ngày và vé máy
  bay. Hơn 20.000 khách sạn và hơn 5.000 tour, hoạt động, đưa đón. Làm cùng công ty 11Infotech, chạy từ cuối 2022.
- **API** cho OTA và hãng lữ hành, kết nối thẳng hoặc qua các sàn trung gian (TravelgateX, Juniper, theo Asian Trails tự công bố;
  Juniper có ghi Asian Trails là khách hàng, TravelgateX chưa thấy xác nhận).
- **Cloud Tariff:** trang bảng giá và thông tin điểm đến, đại lý đăng nhập để xem. Điều khoản của họ có nhắc giá hợp đồng riêng
  theo sản lượng và tiền tệ thoả thuận riêng với từng đối tác; bảng giá có khác theo từng đại lý hay không thì nguồn công khai
  không nói.
- **Back office Lemax** (thắng thầu 2018, chạy từ 2019 theo case study của chính Lemax; không rõ nay còn dùng): theo case study đó
  có tự xác nhận, tự xuất hoá đơn, tự làm lịch trình.
- **Điều khoản:** giá net, không hoa hồng, không công bố hạng đại lý; trả đủ trước 30 ngày nếu không có hạn mức công nợ; quá hạn thì
  có thể dừng công nợ.

**Mình so với họ (trạng thái trên Dev ngày 05/11):**

| Hạng mục | Asian Trails | Mình |
|---|---|---|
| Đặt chỗ, giữ chỗ, xác nhận, huỷ có phí | Có | Có trên môi trường thử nghiệm |
| Giá cho đại lý | Giá net, không công bố hạng; có giá hợp đồng riêng theo sản lượng | Giá net theo mùa từ bảng giá nhà cung cấp, giá bán lẻ gợi ý = net + 25 %; ba hạng đại lý 0/3/6 % và giá hợp đồng riêng cho từng đại lý: đã chạy trên Dev (xem PR-25) |
| Hoá đơn, đặt cọc, công nợ | Có | Đã chạy trên Dev với đại lý hư cấu: hoá đơn phí phần mềm và hoá đơn tiền tour, thanh toán hai người duyệt, quá hạn thì dừng giữ chỗ mới (xem PR-25) |
| Nội dung tour cho đại lý đăng | Kho ảnh, không cho đăng lại nội dung | Thế mạnh của mình: tour viết lại, bản riêng cho từng đại lý, đăng WordPress/Facebook |
| CRM cho đại lý | Không thấy công bố | Có trên môi trường thử nghiệm |
| Trang lên kế hoạch chuyến đi riêng cho từng đại lý | Không thấy công bố | Đợt sau |
| Khách sạn bán sỉ, vé máy bay, sàn trung gian | Có | Không làm: mình chỉ bán tour mình vận hành |

**Đã bổ sung sau khi so sánh (Dev, 05/11):**

1. Bảng giá riêng từng đại lý theo hạng, tải CSV hoặc in, giống Cloud Tariff của họ: đã chạy; đại lý xem ngay trong CRM (xem PR-26).
2. Tạm dừng giữ chỗ mới khi quá hạn công nợ: đã thử thật. Email tự nhắc hoá đơn quá hạn: đã có, chưa thử thật.
3. Hiện chính sách phí huỷ ngay lúc báo giá: đã có trong hệ thống, chưa thử thật.
4. Phiếu xác nhận đặt chỗ cho đại lý đặt qua "Book with AA" (không có tên khách): đã có trong hệ thống, chưa thử thật.
5. File xuất hoá đơn và thanh toán theo kỳ cho kế toán: đã có trong hệ thống, chưa thử thật.
6. Mục "giá đăng sai" trong điều khoản đại lý (học từ điều khoản của Asian Trails): đã soạn bản nháp trong hệ thống, sẽ rà cùng bộ
   điều khoản đại lý.

Bản so sánh đầy đủ, có nguồn từng dòng:
https://github.com/AdventureAsia365-Ecosys/AA-Ecosys/blob/master/docs/research/2026-11-05-asian-trails-b2b-benchmark/README.md

**Ảnh:** không.

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Mọi dữ kiện về Asian Trails / Lemax | `docs/research/2026-11-05-asian-trails-b2b-benchmark/README.md` (18 nguồn, truy cập 05/11), root #545 `7ff1ecd1` |
| Hạng + giá hợp đồng chạy trên Dev | Linear AA-1030 close-out 05/11 15:46Z |
| Hoá đơn, hai người duyệt, dừng giữ chỗ | Linear AA-1037 close-out 05/11 16:12Z |
| (1) bảng giá theo đại lý + trong CRM | AA-1030 close-out (G3, Partner #235) |
| (2) dừng giữ chỗ đã thử; email nhắc chưa thử | AA-1037 close-out (`credit_hold_overdue`; reminder skipped, không email) |
| (3)(4)(5) chưa thử thật | Booking #191 G1/G2/G5, không có lần kiểm chức năng sống |
| (6) điều khoản giá đăng sai là bản nháp | Linear AA-1037 S269 comment ("G6: … a DRAFT price-error clause for the business owner") |

---

## Không soạn (và vì sao)

- **PR-20 kỳ 4 (03–09/11):** chưa đến hạn; kỳ 3 đăng 02/11, kỳ 4 soạn từ thứ Hai 09/11. Kỳ 4 gom S265–S270, chi phí AWS tháng
  8–10 (đã hẹn ở #10603), chi phí AI viết thật (PR-17) và bộ kịch bản nghiệm thu vòng 1.
- **PR-24 TripPlanner:** S268–S270 không có thay đổi khách thấy (lát 1 gắn đại lý cho TripPlanner chỉ là dữ liệu nền, chạy ở chế độ
  shadow).
- **PR-27 Nền tảng và các việc kỹ thuật:** kit giao diện + kiểm ảnh tự động thành check bắt buộc, tài khoản kiểm thử chỉ đọc, các
  migration, thứ tự model AI / key Anthropic / catalog, ghim Playwright — quyết định của tech lead (memory `jira-no-tech-decisions`).
- **Gói DPA và điều khoản đại lý thí điểm (bản cho luật sư):** chưa xong, và đợt này chỉ một câu hỏi được duyệt gửi chị Thư.
- **Các story PR khác** (PR-1, PR-7, PR-9, PR-11, PR-12, PR-13, PR-14, PR-15, PR-16, PR-19, PR-21, PR-28) và **KAN/CON còn lại**:
  không có việc S268–S270 khớp chủ đề (Booking và CRM báo trên epic PR-25 / PR-26 như đợt 04/11).
- **Thử nhập bảng giá Excel thật của nhà cung cấp (S270, dry run 19/19 rồi rollback):** chưa lưu dữ liệu, chưa có comment Linear
  làm bằng chứng → để kỳ 4 khi nhập thật.

## Ghi đăng (điền sau khi đăng)

| Issue | Comment id / link | Ghi chú |
|---|---|---|
| PR-23 | | |
| PR-17 | | |
| PR-18 | | |
| PR-22 | | |
| PR-25 | | |
| PR-26 | | |
| KAN-20 | | |
