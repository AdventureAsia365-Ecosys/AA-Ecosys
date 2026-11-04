> **ĐÃ ĐĂNG 04/11 (~20:30 +07), 7 comment, 11 ảnh.** Sửa theo tech lead: bỏ 2 câu ở PR-20, xưng "em", viết lại đoạn luật sư, "dữ liệu giả" → "dữ liệu mô phỏng".
> Trước đó: Nháp Jira gộp S265 + S266 + S267 (03–04/11/2026), soạn trong S267. Chưa đăng, chưa sửa
> comment nào, chưa đổi trạng thái issue nào. Tech lead duyệt một lần, rồi đăng theo skill `aa-jira-update`
> (`contentFormat: html`, bảng markdown đổi sang bảng HTML, ảnh upload từng file rồi nhúng bằng `inlineFileId` đúng thứ tự).

# S265 + S266 + S267 — nháp Jira cho chị Thư

Soạn 04/11/2026 (Claude Code, phiên S267; phần S267 gộp vào lúc ~18:00 +07). Mention khi đăng:
`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>` (thay chữ `@thule`
ở đầu mỗi nháp).

## Đã rà trên Jira (chỉ đọc, 04/11)

- JQL `project in (PR, KAN, CON) AND updated >= "2026-11-02"`: chỉ PR-20, PR-22…PR-26, cập nhật cuối 02/11 21:21–21:23
  (đợt đăng nháp S264). Không có gì mới sau đó, không có comment mới của chị Thư.
- Comment mới nhất mỗi epic: PR-20 #10607 (kỳ 3 cập nhật 02/11), PR-22 #10606, PR-23 #10604, PR-24 #10600, PR-25 #10599,
  PR-26 #10605, PR-27 #10532 (29/10). Câu hỏi điều khoản AI A/B/C (PR-23 #10508 ngày 25/10, nhắc lại ở #10601) vẫn chưa có
  trả lời.
- JQL `project in (PR, KAN, CON) AND statusCategory != Done`: hơn 100 issue (trang đầu 100, còn trang sau), phần lớn là việc
  nội dung/marketing của KAN/CON (vd. KAN-86, KAN-89 là việc riêng của chị Thư). Không issue KAN/CON nào khớp việc S265–S266
  → không soạn.
- **PR-20 kỳ 4 (03–09/11) chưa đến hạn (thứ Hai 09/11) → không soạn ở đây.** Báo cáo chi phí AWS chính thức tháng 10 (đã
  hứa ở #10603 "sẽ có trong kỳ 4") để vào kỳ 4.
- Rà lại lúc gộp S267 (~18:00 +07, chỉ đọc): JQL `project in (PR, KAN, CON) AND updated >= "2026-11-03"` → 0 issue (không có
  gì mới, không có comment mới của chị Thư). Epic PR chưa Done: PR-20, PR-22…PR-27 (cập nhật cuối 29/10–02/11), không đổi.
  Comment mới nhất PR-24 vẫn là #10600 (02/11) → nội dung S267 không trùng với gì đã đăng.
- Rà lần cuối lúc chốt phiên (04/11 ~20:00 +07): JQL `project in (PR, KAN, CON) AND updated >= "2026-11-04 11:00"` → 0 issue.
  Phần route LLM theo họ model (366–368, sweep) là việc kỹ thuật → không đưa lên Jira (luật S258).

## Danh sách

| # | Issue | Một dòng | Ảnh |
|---|---|---|---|
| 1 | PR-20 | Hướng sản phẩm chỉ B2B sau buổi họp 02/11 + 18 con số/quy tắc khởi điểm thuộc phần chủ doanh nghiệp, đổi được, chờ chị xem (comment riêng, không phải báo cáo kỳ 4); thêm 1 dòng tiến độ 04/11 | 0 |
| 2 | PR-23 (A) | Content studio: nhãn "AI-assisted", dấu AI máy đọc được, giữ bài có link đặt tour ngoài AA, AI kèm gói dừng đúng khi hết mức; **S267:** trang Plans & add-ons đã chụp kiểm, Content studio + CRM thành một app cho đại lý (Content là trang chủ, một đăng nhập có MFA, app cũ đã gỡ, đăng nhập bằng API key đã gỡ) | 3 |
| 3 | PR-23 (B) | Điều khoản AI: Phụ lục AI v1.0 lên Content studio / CRM / TripPlanner; chuyện nhờ luật sư là phương án để chị quyết; **S267:** link điều khoản đổi sang địa chỉ mới | 0 |
| 4 | PR-26 | CRM: bản nháp AI chạy với model thật, AA tạm dừng AI cả CRM; **S267:** số chỗ và tính năng CRM theo gói đặt ở admin CIS đã thử thật (CRM Core 10 chỗ + AI drafts, SMS/WhatsApp bị từ chối) | 3 |
| 5 | PR-24 | TripPlanner: nút gửi tư vấn viên thành thông báo demo (B2B), tắt AI → tìm theo từ khoá, dấu AI máy đọc được, điều khoản; **S267:** trang tour hiện giá "From $235 per person" lấy từ Booking (tour thử, dữ liệu mô phỏng) | 1 |
| 6 | PR-25 | Booking: tắt phần khách lẻ, danh sách đối tác lấy từ CIS; **S267:** bảng giá nhà cung cấp + quy tắc lợi nhuận tự ra giá bán lẻ gợi ý "from" | 0 |
| 7 | PR-22 | Admin CIS: thanh bên 7 nhóm theo mô hình B2B, bỏ số liệu khách lẻ, trang Compliance; **S267:** 6 vai trò nhân viên mới (người chăm sóc đối tác chỉ thấy đối tác được giao), Writing Lab theo từng bước viết, một trang Spend có tab By app | 4 |

Không soạn PR-27 (việc kỹ thuật của tech lead), PR-20 kỳ 4 (chưa đến hạn). Lý do chi tiết ở cuối file. PR-23 giữ hai comment
(A tiến độ, B trả lời câu hỏi A/B/C về điều khoản) như bản S265–S266; tech lead muốn gộp làm một thì dán B nối sau A.

## Kiểm trước khi đăng (ô tech lead chốt)

- [ ] **#1 PR-20:** 18 dòng trong bảng là lựa chọn tech lead đã bấm theo khuyến nghị trên trang quyết định (03/11, 21/21
  theo khuyến nghị, có ghi chú ở 7 mục). Phần đó thuộc quyền chủ doanh nghiệp nên nháp trình bày là "số khởi điểm, chị xem
  và đổi". Tech lead xác nhận được trình bày như vậy.
- [ ] **#1 link trang quyết định** (https://claude.ai/artifact/S9JUSxTAdsULth39qHXQJN): trang có cả phần quyết định kỹ thuật
  (TL) và ghi chú riêng của tech lead. Chỉ đưa link nếu tech lead muốn và đã mở chia sẻ cho tài khoản chị Thư; không thì bỏ
  dòng "Chi tiết từng mục".
- [ ] **#1 vị trí:** đăng làm comment riêng trên PR-20 (hướng chung cho mọi app). Nếu tech lead muốn để cạnh phần quản lý
  đối tác thì chuyển sang PR-23 (các comment app khác vẫn trỏ "xem comment ngày 04/11 trên PR-20" — sửa chữ trỏ theo).
- [ ] **#1 dòng pháp nhân Úc:** lấy từ ghi chú của tech lead trên trang quyết định (hướng tới đại lý nước ngoài → pháp nhân
  có thể là AA ở Úc). Bỏ dòng nếu tech lead chưa muốn nêu với chị Thư.
- [ ] **#4 PR-26 ảnh 2** chụp 03/11 lúc CRM còn chế độ thử (có dòng "TEST MODE"); câu chú thích đã ghi rõ. Bỏ ảnh nếu thấy
  gây nhầm.
- [ ] **#7 PR-22 ảnh 1** là bản **đã cắt** chỉ còn thanh bên (`.tmp-session/S267/jira-img/`). Bản gốc
  `02-sidebar-all-groups-open-1440-light.png` có bảng chi phí theo app tháng 10/11 → không đính bản gốc (chi phí để báo
  cáo kỳ 4).
- [ ] Không đính ảnh nào trong `.tmp-session/S266/private-shots/` (trang Routing có account ID AWS).
- [ ] Tên epic PR-24 vẫn là "TripPlanner — Lên lịch trình trên bản đồ (khách B2C)". Đổi tên hay không là việc của tech lead /
  chị Thư; agent không sửa.

Ô mới cho phần S267:

- [ ] **#4 PR-26 ảnh 3** là bản **đã cắt** (`.tmp-session/S267/jira-img/cis-goi-cua-doi-tac-cat.png`) từ
  `aa1028/03-atlas-subscription-1440-light.png`: bản gốc có dải số trên cùng (chi phí AI của đối tác thử) và dòng quyền
  "Content API keys: On" (chụp trước khi gỡ API key, dễ gây nhầm) → không đính bản gốc.
- [ ] **#2 PR-23 A ảnh 2** (trang Plans & add-ons) hiện giá gói Content 299 / 799 / 1.499 USD — cùng số với bảng PR-20. Không
  dùng ảnh ngăn chi tiết gói `crm.core` (`02-plan-crm-core-drawer`) vì có mã nội bộ (tên migration, mã quyết định).
- [ ] **#7 PR-22 ảnh 3–4** là bản **đã cắt**: Writing Lab (`cis-writing-lab-cat.png`) bỏ phần dưới có mã bộ mẫu nội bộ; Spend
  (`cis-spend-tab-cat.png`) chỉ còn tiêu đề + 4 tab. Bản gốc `spend-apps-*` có **account ID AWS** và bảng chi phí theo app
  tháng 11 → tuyệt đối không đính bản gốc. Ảnh Spend nhỏ, bỏ được nếu thấy thừa.
- [ ] **#5/#6 giá "From $235"** là tour thử, nhà cung cấp, khách sạn và giá đều là dữ liệu mô phỏng (đã ghi rõ trong nháp). Trang
  TripPlanner Dev công khai đang hiện giá giả đó trên tour thử. Tech lead xác nhận được nêu như vậy.
- [ ] **#7 PR-22 vai trò nhân viên:** 6 tên vai trò nêu bằng lời thường; kiểm cô lập chạy trên hệ thống đang chạy (gọi đúng các
  route thật), chưa thử bằng tài khoản nhân viên đăng nhập thật — đã ghi rõ trong nháp. Nếu tech lead coi phân quyền là phần
  nền tảng (PR-27) thì bỏ đoạn này khỏi PR-22.
- [ ] **#2 PR-23 A "đăng nhập bằng API key đã gỡ":** nêu theo lời sản phẩm (đối tác chỉ đăng nhập bằng tài khoản đối tác). Nếu
  chị Thư chưa từng biết đến API key thì có thể bỏ câu này.

---

## 1. PR-20 — Hướng sản phẩm chỉ B2B (comment riêng, không phải báo cáo kỳ 4)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** PR-20 là epic báo cáo nền tảng chung cho mọi app; mô hình chỉ B2B (chốt ở buổi họp 02/11) đổi cả 4 app.
Các lựa chọn thuộc phần chủ doanh nghiệp (giá, hợp đồng, pháp lý) đang được dùng làm số khởi điểm để dựng hệ thống, nên chị
cần thấy và đổi nếu muốn. Không nêu quyết định hạ tầng/kiến trúc (việc của tech lead).

**Nội dung (sẵn để đăng):**

@thule Sau buổi họp 02/11, hệ thống được sắp lại theo mô hình chỉ phục vụ đại lý (B2B). Tiến độ
từng app ở comment ngày 04/11 trên các epic PR-22 đến PR-26.

**Hướng sản phẩm**

- Adventure Asia chỉ bán cho đại lý đối tác; không bán trực tiếp cho khách du lịch và không giữ dữ liệu khách lẻ của riêng
  mình.
- Mỗi đại lý dùng gói nền **Content** (viết lại tour, bài mạng xã hội, đăng bài). **CRM** và **TripPlanner** là phần mua thêm.
- **Booking** thành hệ thống của AA để làm việc với đại lý: giá net, giữ chỗ, xác nhận, quyết toán. Phần khách lẻ đã tắt trên
  Dev ngày 03/11.
- **TripPlanner** sẽ thành sản phẩm đại lý gắn lên website của mình, mang thương hiệu đại lý; yêu cầu của khách đi vào CRM
  của đại lý. Trang TripPlanner hiện tại của AA thành bản demo.
- Mọi tour đại lý bán phải là tour đang bán của Adventure Asia; trong CRM, đại lý chỉ được thêm dịch vụ bổ trợ (vé máy bay,
  bảo hiểm, visa, đưa đón, phí).
- Đã xong trên Dev: tắt các đường bán lẻ (03/11); gói và quyền theo gói, AI kèm gói dừng khi hết mức, Content studio và CRM
  thành một app cho đại lý, giá bán lẻ gợi ý tự tính từ bảng giá nhà cung cấp (04/11; chi tiết ở các epic). Đang làm: vai trò
  nhân viên AA (phần còn lại), phần Booking cho đại lý. Mốc kế tiếp: một đại lý thí điểm dùng Content và CRM, có thư thí điểm
  và thoả thuận xử lý dữ liệu. Chưa có ngày.

**Các số và quy tắc khởi điểm (thuộc phần chị quyết)**

| Mục | Đang dùng |
|---|---|
| Câu cam kết với đại lý | "Adventure Asia chỉ bán cho đại lý đối tác; không bán trực tiếp cho khách du lịch và không dùng dữ liệu khách của đại lý để tiếp thị." Luật sư rà cùng bộ hợp đồng mẫu sau |
| Giá gói Content | Starter 299, Growth 799, Business 1.499 USD/tháng; Enterprise "liên hệ", giá theo hợp đồng, không thấp hơn Business; dùng thử 14 ngày; xem lại sau 3 đại lý đầu tiên |
| AI kèm gói | Starter 15, Growth 40, Business 80 USD/tháng; hết mức thì AI tạm dừng tới tháng sau, báo đại lý và người phụ trách, chưa thu thêm tiền |
| CRM | Tính theo người dùng, thấp hơn mức của Tern (ví dụ 25–35 USD/người/tháng); chưa đặt giá trên hệ thống |
| TripPlanner | Thuê bao theo site: gói cơ bản (trang AA lưu trữ hoặc nhúng vào website đại lý), gói cao (tên miền riêng + API cho đại lý tự làm giao diện); chưa đặt giá |
| Dòng "Powered by Adventure Asia" trên TripPlanner của đại lý | Tuỳ chọn, mặc định tắt; có thể bật ở gói thấp (chỉ đổi cấu hình) |
| Ai thu tiền khách | Đại lý thu tiền khách; Adventure Asia xuất hoá đơn cho đại lý theo giá B2B |
| Giá bán cho đại lý | Một giá net mỗi tour theo mùa; 3 hạng đại lý giảm 0 / 3 / 6 %; giá bán lẻ gợi ý = giá net + 25 % |
| Đại lý trả tiền tour | Đại lý mới cọc 30 % khi xác nhận, phần còn lại trước ngày khởi hành 30 ngày (đặt sát ngày thì trả đủ); công nợ chỉ mở sau khoảng 6 tháng thanh toán tốt, hạn mức ghi trong hợp đồng; USD |
| Thuế, hoá đơn | Gửi ghi chú câu hỏi thuế xuyên biên giới cho kế toán trước hoá đơn đầu tiên cho đại lý nước ngoài; hợp đồng ghi "giá chưa gồm thuế"; tách hoá đơn phí phần mềm và hoá đơn quyết toán tour; giai đoạn đầu lập hoá đơn tay. Hoá đơn VAT ở Việt Nam vẫn phát hành trên phần mềm hoá đơn điện tử kế toán đang dùng |
| Đại lý bán tour không phải của AA | Cảnh báo trước, sau 7 ngày không sửa thì tạm ngưng; số ngày đổi được |
| Kiểm tra đại lý khi đăng ký | Giấy đăng ký kinh doanh; giấy phép lữ hành nếu nước của đại lý yêu cầu; tra tay danh sách trừng phạt công khai miễn phí; người phụ trách đại lý duyệt, chị duyệt trường hợp đặc biệt |
| Chăm sóc đại lý | Mỗi đại lý có một người phụ trách có tên; chăm sóc sát cho gói Business/Enterprise; các gói khác qua hàng đợi chung khi số đại lý tăng |
| Dữ liệu khách | Đại lý là bên kiểm soát dữ liệu, Adventure Asia là bên xử lý; đại lý tự hiện thông báo cookie trên site của họ. Lưu trên máy chủ ở Mỹ kèm hợp đồng chuẩn về chuyển dữ liệu; lưu ở EU chỉ khi hợp đồng yêu cầu và có tính phí; Trung Quốc đại lục chỉ dùng gói Content |
| Đại lý ở EU (luật du lịch trọn gói) | Đại lý vẫn là bên tổ chức; Adventure Asia cung cấp gói thông tin về tour và nhà cung cấp |
| Cam kết dịch vụ | Chốt ngày dùng thật khi có đại lý thí điểm đồng ý dùng CRM với khách thật; 99,5 % thời gian hoạt động cho Business/Enterprise; phản hồi hỗ trợ trong 1 ngày làm việc (4 giờ cho gói cao); chưa làm SOC 2/ISO, làm khi đại lý lớn hoặc đại lý EU đầu tiên yêu cầu; kiểm thử xâm nhập trước ngày dùng thật |
| Tài khoản AI trực tiếp (Anthropic) | Đứng tên pháp nhân Adventure Asia, chị là chủ thanh toán; trần 150 USD/tháng, chỉ nâng khi chị đồng ý |
| Pháp nhân ký hợp đồng với đại lý | Hướng đang nghiêng về pháp nhân Adventure Asia ở Úc, vì khách hàng mục tiêu là đại lý nước ngoài; chị xác nhận. Nếu chọn Úc, có vài câu cho kế toán/luật sư Úc (đăng ký GST, dịch vụ cho đại lý nước ngoài có được miễn GST, luật quyền riêng tư Úc); có hỏi và hỏi lúc nào là chị quyết, chỉ cần trước đại lý thí điểm đầu tiên |

Điều khoản AI cho đại lý: xem comment ngày 04/11 trên PR-23.

Gói và mức AI kèm gói đã lưu trên hệ thống Dev, đổi trên trang Plans & add-ons của admin CIS, không cần sửa code (ảnh ở
comment ngày 04/11 trên PR-23). Quy tắc "giá bán lẻ gợi ý = giá net + 25 %" đã chạy trên một tour thử (xem PR-25). Các số về
đặt cọc, thuế sẽ đổi được trên trang quản trị khi làm xong phần Booking cho đại lý.

Chi tiết từng mục (lý do, các phương án khác): https://claude.ai/artifact/S9JUSxTAdsULth39qHXQJN

**Ảnh:** không.

**Câu → bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Mô hình chỉ B2B chốt ở buổi họp 02/11; Content gói nền, CRM + TripPlanner mua thêm, Booking B2B, TripPlanner white-label | log S265 "Quyết định ~10:30"; ADR 0019 Accepted (root #486, `2bf0be09`); `docs/audits/2026-11-03-S265-ecosystem-restructure/README.md` §0 |
| Đường bán lẻ tắt trên Dev 03/11 | Linear AA-1034 comment 03/11 08:20Z (TP #218 410 `b2b_only`; Booking #170 bk-036 INSERT 42501, #171 B2C intake tắt; CIS #1271) |
| 18 dòng bảng | `docs/audits/2026-11-03-S265-ecosystem-restructure/approvals.json` (BO-1…BO-21, 21/21 theo khuyến nghị, "approved_by: tech lead") + `decisions.json`; ghi chú tech lead ở BO-4, BO-7 (7 ngày), BO-8, BO-10 (pháp nhân Úc), BO-14, BO-15/16/17 (đổi sau được); giải đáp `clarifications.md` §2 (BO-4, BO-8, BO-10, BO-14) |
| Dùng thử 14 ngày, 299/799/1.499 USD/tháng | `decisions.json` BO-2 `why_vi`; README §3 dòng "Content" |
| Gói + AI kèm gói lưu trên Dev, đổi không cần code | Linear AA-1028 lát 1 (mig 353–355: content 299/799/1.499, AI 15/40/80; `/tenant/v1` account 200 `ai.budget_usd_monthly="40.00"`) và lát 3 (trang Plans & add-ons `/admin/tenants/plans`, CIS #1285) |
| Số Booking đổi được sau khi làm phần Booking cho đại lý | `clarifications.md` §2 "BO-15, BO-16, BO-17" (sau R4) |
| Đã xong 04/11: gói/quyền theo gói, một app, giá gợi ý | `docs/audits/2026-11-04-S267-live-verify/aa1028/`, `aa1036/`, `aa1029/` README; Linear AA-1036 comment 04/11 08:00Z + 10:27Z |
| RRP = giá net + 25 % chạy trên tour thử | `aa1029/README.md` ("net 150 per person → b2b 185 → RRP 235 (b2b x 1.25)") |

**Chưa kiểm:** các dòng BO là lựa chọn trên giấy, chưa có gì "chạy được" để kiểm, trừ gói + AI kèm gói và quy tắc RRP +25 %
(đã có trên Dev). Trang Plans & add-ons đã chụp kiểm 04/11 (S267).

---

## 2. PR-23 — Portal tenant — comment A (Content studio, 03–04/11)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** việc đối tác nhìn thấy trong Content studio và phần AA quản lý đối tác (gói, AI kèm gói); từ 04/11
Content studio là một phần của app chung cho đại lý.

**Nội dung (sẵn để đăng):**

@thule Cập nhật Content studio và quản lý đối tác ngày 03–04/11 (Dev, đối tác thử):

| Phần | Đã thử trên Dev | Chưa thử |
|---|---|---|
| Nhãn "AI-assisted" trên bài do AI viết | đạt (03/11): 6/6 bài trong My Content có nhãn, ngăn chi tiết bài cũng có | danh sách Published (đối tác thử chưa có bài đã đăng) |
| Dấu "có AI hỗ trợ" máy đọc được trong file xuất và bài WordPress | đạt khi kiểm phần xuất bài trên Dev (03/11) | đăng thật lên WordPress: site WordPress thử đã hết hạn, chờ site mới |
| Giữ bài có link đặt tour ngoài Adventure Asia | đạt (03/11), lần kiểm không lưu gì | Content studio chưa hiện lý do "cần sửa" trong danh sách đăng (làm tiếp) |
| AI kèm gói dừng khi hết mức tháng | đạt (04/11) | — |
| Gói và phần mua thêm trong admin CIS | đạt (04/11): trang Plans & add-ons và tab Subscription chụp kiểm; gán gói CRM cho đối tác thử, CRM theo đúng gói (xem PR-26) | — |
| Một app cho đại lý: Content studio chạy trong app web của đại lý | đạt (04/11): mở địa chỉ là vào Content; đăng nhập bằng tài khoản đối tác có MFA; app Content studio riêng cũ đã gỡ; đăng nhập bằng API key bị từ chối | một người dùng mới được mời vào thẳng Content và chỉ thấy CRM khi gói có CRM; giao diện tiếng Việt của Content studio (làm tiếp) |
| Khi AA ngừng bán một tour | đã có trong hệ thống | chưa thử thật: cần một bài thử đang đăng trên site WordPress mới |

- **Nhãn AI:** trang My Content có dòng nhắc "This content was generated with AI. Review it before publishing; you are
  responsible for what you publish." và mỗi bài do AI viết có nhãn "AI-assisted". Khi xuất file hoặc đăng lên WordPress, bài
  mang thêm một dấu ẩn để công cụ tìm kiếm và các nền tảng biết đây là nội dung có AI hỗ trợ (theo yêu cầu minh bạch nội
  dung AI của EU); người đọc không thấy khác. Facebook không có chỗ gắn dấu này cho bài chữ nên bài Facebook giữ nguyên.
- **Chỉ bán tour của Adventure Asia:** trước khi đăng, hệ thống kiểm link trong bài: link đặt/bán tour chỉ được trỏ tới trang
  tour của Adventure Asia hoặc TripPlanner của đối tác; bài chỉ nói về thương hiệu, không kêu gọi đặt tour, vẫn đăng bình
  thường. Bài vi phạm bị giữ lại kèm lý do để đối tác sửa, và hiện cho AA ở trang kiểm nội dung đối tác. Đã thử 03/11 trên
  một bài thử của đối tác Atlas & Hearth: thêm link "Book this tour" sang Viator thì bài bị giữ, báo "cần sửa"; lần thử chạy ở
  chế độ không lưu, bài thử giữ nguyên.
- **AI kèm gói:** mỗi đối tác có mức AI theo tháng lấy từ gói (xem comment ngày 04/11 trên PR-20). Đã thử 04/11 lúc 08:14 trên
  một đối tác thử: đặt tạm mức 0,01 USD, chạy 24 lượt AI rẻ (tổng khoảng 0,01 USD); tới 80 % hệ thống xếp email cảnh báo cho
  AA, quá 100 % thì từ chối lượt tiếp theo, không phát sinh thêm tiền. Sau đó trả mức về như cũ.
- **Gói và phần mua thêm:** admin CIS có trang Plans & add-ons: gói Content (Starter, Growth, Business, Enterprise), phần mua
  thêm CRM (CRM Core, CRM Pro) và TripPlanner (Hosted, Pro); mỗi gói ghi giá, tính năng, số đối tác đang dùng và phiên bản;
  sửa một gói thì áp cho mọi đối tác đang dùng và được ghi lại. Trang từng đối tác có tab Subscription (gán gói, thêm phần mua
  thêm, mở hoặc tắt riêng từng quyền). Quyền của đối tác (số bài, kênh đăng, mức AI, số chỗ CRM…) lấy từ gói; CRM và Booking tự
  cập nhật theo. Đã kiểm 04/11: hai trang chạy đúng trên máy tính và điện thoại, sáng và tối; gán CRM Core cho đối tác thử
  Atlas & Hearth thì CRM của đối tác đó theo đúng gói (chi tiết ở comment ngày 04/11 trên PR-26). Gói thử được tạo và gán bằng
  đúng phần xử lý mà nút Save gọi, không bấm Save trên giao diện (tài khoản kiểm của em trên admin chỉ có quyền xem).
- **Một app cho đại lý:** từ 04/11, Content studio chạy bên trong app web của đại lý, cùng địa chỉ portal.lumiguides.it.com.
  Mở địa chỉ là vào thẳng Content (trang chủ). Đại lý đăng nhập một lần bằng tài khoản đối tác (có MFA) cho cả Content và CRM.
  Nhóm "Apps" ở thanh bên hiện các phần đại lý có hoặc có thể mua thêm (ví dụ "Trip planner: request add-on"). App Content
  studio riêng cũ đã gỡ. Đối tác không còn đăng nhập bằng API key: trang API trong studio đã bỏ, cách đăng nhập cũ nay trả lời
  "đã gỡ" và chỉ đường sang tài khoản đối tác. Đã kiểm 04/11: mở địa chỉ chuyển vào Content; trang Content và các trang điều
  khoản mở được; đại lý thử Harbour Lights đăng nhập bằng tài khoản đối tác + MFA; đăng nhập bằng API key bị từ chối. Chưa thử:
  một người dùng mới được mời vào thẳng Content và chỉ thấy CRM khi gói có CRM; link Content trong nhóm "Apps" (đại lý thử
  Harbour Lights chưa có quyền Content nên ảnh chỉ thấy dòng TripPlanner). Giao diện tiếng Việt cho Content studio làm tiếp.
- **Khi AA ngừng bán một tour:** đối tác đang có bài về tour đó nhận thông báo (chuông và email); trang WordPress của bài chuyển
  về nháp sau 7 ngày; bài Facebook được đánh dấu để đối tác xử lý; Booking không nhận giữ chỗ mới. Khi tour bán lại, đối tác
  nhận email "back on sale". Phần này đã có trong hệ thống, chưa thử thật vì chưa có bài thử nào đang đăng (site WordPress thử
  hết hạn).

Ảnh theo thứ tự: (1) trang My Content với nhãn "AI-assisted" trên từng bài; (2) trang Plans & add-ons trong admin CIS;
(3) trang chủ app đại lý (đại lý thử Harbour Lights) với nhóm "Apps" ở thanh bên.

**Ảnh:**

| # | Tên khi upload | File | Che/cắt |
|---|---|---|---|
| 1 | studio-nhan-ai-assisted.png | `docs/audits/2026-11-03-S266-live-verify/aa1040-ai-marking/02-studio-my-content-1440-light.png` | không cần (đối tác thử Atlas & Hearth, không account ID, không email) |
| 2 | cis-goi-va-phan-mua-them.png | `docs/audits/2026-11-04-S267-live-verify/aa1028/01-plans-1440-light.png` | không cần (không account ID, không email; giá gói = bảng PR-20) |
| 3 | app-dai-ly-trang-chu.png | `docs/audits/2026-11-04-S267-live-verify/aa1036/crm-home-apps-1440-light.png` | không cần (đại lý thử, số 0, không email, không account ID) |

**Câu → bằng chứng (nội bộ):**

| Câu | Bằng chứng |
|---|---|
| Nhãn AI 6/6, ngăn chi tiết, Published trống | `docs/audits/2026-11-03-S266-live-verify/results.json` verdicts AA-1040; Linear AA-1040 comment 03/11 12:04Z |
| Dấu máy đọc được ở xuất/WordPress, Facebook không gắn | Linear AA-1040 (CIS #1274: `data-ai-*`, `<meta name="ai-*">`, `X-AI-*`; "Facebook text posts … left unchanged") |
| Đăng WordPress thật chưa thử, site hết hạn | Linear AA-1040 "Blocked"; log S266 "Còn mở" |
| Gate link ngoài AA: Viator → giữ, 409 `content_needs_change`, rollback | Linear AA-1039 comment 04/11 00:12Z (piece dbf45319, Atlas & Hearth); `.tmp-session/S266/aa1039/RUN.md` §2 |
| Thương hiệu không CTA vẫn đăng; link tới trang AA hoặc TripPlanner đối tác | Linear AA-1039 plan review (d21) |
| Portal chưa hiện `needs_change` | Linear AA-1039 follow-ups |
| AI kèm gói fail-closed 04/11 01:14Z, 0,01 USD, 24 lượt, 80 % email được xếp hàng (chưa kiểm hộp thư nhận), refused | Linear AA-1028 comment 04/11 01:15Z |
| Plans & add-ons, Subscription, CRM/Booking tự cập nhật | Linear AA-1028 lát 2 (crm_entitlement_pull, bk_tenant_pull live) + lát 3 (CIS #1285) |
| Ngừng bán tour: chuông + email, WP về nháp sau 7 ngày, Facebook flag, Booking chặn giữ chỗ, "back on sale" | Linear AA-1039 plan review (d20) + slice 2 (job `tour_retirement_fanout`, `tour_notice_email`, `retired_page_draft`); retire→restore "Not verified live yet" |
| Plans & add-ons (5 gói Content, CRM Core/Pro, TripPlanner Hosted/Pro), 1440+390 sáng/tối; Subscription Atlas | `docs/audits/2026-11-04-S267-live-verify/aa1028/` (11 ảnh, README "Screenshots") |
| Gói thử tạo/gán qua code của route admin, không bấm Save (phiên admin E2E chỉ đọc) | aa1028 README "Not tested live" ý 2 |
| Một app: `/` 307 → `/portal/dashboard`, `/api/healthz` `studio: merged`, `/terms` 308 → `/legal/partner-terms`, `/tenant-login` 308, trang studio 200 | Linear AA-1036 comment 04/11 08:00Z (Infra #650, Partner #211, `crm_edge_live_check.py --agency-direct` PASS) |
| Đăng nhập partner pool + MFA, `crm_entitled: true`, nhóm Apps chỉ "Trip planner: request add-on" | `aa1036/README.md` (kiểm 04/11 trước cut-over, trên app web đã gộp) |
| App studio cũ đã gỡ | Linear AA-1036 comment 04/11 10:27Z (Partner #212, Infra #659 apply, `aa-crm-dev-portal` INACTIVE; edge check PASS sau destroy) |
| Đăng nhập bằng API key → 410, trang API/key card bỏ | Linear AA-1036 comment 04/11 10:27Z (CIS #1292 `ee253a6e` live `POST /auth/tenant-login` → 410; Partner #213) |
| Chưa thử: người được mời vào Content, CRM chỉ khi có gói; studio i18n | Linear AA-1036 10:27Z "Left" |

**Chưa kiểm:** danh sách Published có nhãn; đăng thật lên WordPress có dấu; ngừng bán → báo → bán lại; bấm Save trên trang
Plans/Subscription bằng tài khoản có quyền ghi; người dùng mới được mời vào thẳng Content; link Content trong nhóm Apps; đối
tác viewer còn thấy nút Edit/Export trong ngăn bài (follow-up nội bộ, không đưa).

---

## 3. PR-23 — Portal tenant — comment B (Điều khoản AI)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** câu hỏi A/B/C về điều khoản AI hỏi ở đây (25/10, nhắc 02/11). Phần 1 của việc điều khoản AI đã lên Dev;
việc nhờ luật sư là quyết định của chị, trình bày như một phương án, không hạn chót.

**Nội dung (sẵn để đăng):**

@thule Điều khoản AI cho đối tác (tiếp câu hỏi A/B/C ngày 25/10):

- Đã soạn **Phụ lục AI v1.0** đi kèm hợp đồng đối tác. Nội dung chính: đối tác tuân thủ chính sách sử dụng của các nhà cung cấp
  AI (chính sách mới của Anthropic có hiệu lực từ 12/11/2026); không dùng AI cho đánh giá giả, nhân vật bịa, mạng tài khoản
  giả, quảng cáo không ghi rõ, spam; đối tác xem lại mọi bài và bản nháp AI trước khi đăng hoặc gửi, và chịu trách nhiệm về nội
  dung mình đăng; AI không tư vấn riêng cho một khách về bảo hiểm, visa, tài chính nếu chưa có người có chuyên môn của đối tác
  kiểm; AA lưu nhật ký dùng AI (không lưu nội dung), có thể giữ bài vi phạm và tạm dừng AI của tài khoản vi phạm; AI kèm gói có
  mức theo tháng, hết mức thì tạm dừng tới tháng sau, không thu thêm.
- **Đã lên Dev:** Điều khoản §3 và Quyền riêng tư §5 của Content studio tóm tắt phụ lục (bản nháp v0.4, kiểm trên trang đang
  chạy 03/11; từ 04/11 trang ở địa chỉ mới, link cũ tự chuyển): https://portal.lumiguides.it.com/legal/partner-terms và
  https://portal.lumiguides.it.com/legal/privacy. Điều khoản TripPlanner ghi rõ AI viết lời dẫn là Claude (qua Amazon
  Bedrock) và có link chính sách của Anthropic (bản nháp v0.2, kiểm 03/11). Điều khoản CRM thêm link chính sách các nhà cung cấp
  và quy tắc bảo hiểm/visa/tài chính, cả bản tiếng Anh và tiếng Việt (đã lên Dev, chưa mở kiểm trên giao diện).
- Hiện chưa có đối tác thật nên không cần báo ai trước 12/11. Phụ lục sẽ đi kèm thư mời đại lý thí điểm đầu tiên; đoạn về AI
  trong thư đã soạn sẵn, chỉ còn mức AI kèm gói của đại lý thí điểm để chị điền.
- **Tư vấn pháp lý:** các trang điều khoản hiện vẫn là bản nháp (có dòng "Draft — pending legal review"). Trước khi có
  đối tác trả tiền đầu tiên, mình nên có luật sư xem qua phụ lục AI và điều khoản đối tác; em đã chuẩn bị sẵn các điểm cần
  hỏi để khi chị sắp xếp được thì gửi luôn.

**Ảnh:** không (ảnh trang Điều khoản §3 đã đính ở comment 02/11; nội dung chữ nay dài hơn, không chụp lại).

**Câu → bằng chứng (nội bộ):**

| Câu | Bằng chứng |
|---|---|
| Phụ lục AI v1.0, các điểm chính | `docs/legal/tenant-ai-schedule.md` (root #492, `06da7f3a`) §3, §5 thư thí điểm |
| Anthropic hiệu lực 12/11/2026 | tenant-ai-schedule §1 (đọc trang live 03/11) |
| Portal /terms v0.4, /privacy §5, TP /terms v0.2 live 03/11 | Linear AA-820 comment 03/11 10:43Z (Partner #204, TP #219) |
| Địa chỉ mới `/legal/partner-terms`, `/legal/privacy` 200; `/terms` 308 → `/legal/partner-terms` (04/11) | `docs/audits/2026-11-04-S267-live-verify/aa1036/README.md` + ảnh `legal-legal-*`; Linear AA-1036 comment 04/11 08:00Z |
| CRM terms EN + VI, chưa kiểm live | Linear AA-820 (Partner #204) — phần kiểm live chỉ nêu portal và TP |
| Chưa có đối tác thật, phụ lục đi kèm thư thí điểm, mức AI chị điền | tenant-ai-schedule §5 + drafting note |
| Hướng C đang dùng | ADR 0019 b20; `approvals.json` BO-20 "Duyệt bản nháp ngay; luật sư rà trước đại lý trả tiền đầu tiên" |
| Danh sách câu hỏi cho luật sư | tenant-ai-schedule §7 (Q1 attribution, Q4 binding, Q9 liability, Q10 governing law, …) |

**Chưa kiểm:** điều khoản CRM trên giao diện; chính sách OpenAI chưa đọc lại được (trang trả 403 ngày 03/11, ghi trong
tenant-ai-schedule §1) — không nêu trong comment.

---

## 4. PR-26 — CRM cho đại lý (03–04/11)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** comment 02/11 (#10605) ghi "Ô nháp AI: chưa thử thật". Nay đã thử với model thật; thêm công tắc AI của AA
cho cả CRM; số chỗ và tính năng CRM theo gói đã thử thật ngày 04/11.

**Nội dung (sẵn để đăng):**

@thule Cập nhật CRM cho đại lý ngày 03–04/11 (Dev, đại lý thử "Lữ hành Sen Vàng" và "Atlas & Hearth", dữ liệu mô phỏng):

| Phần | Đã thử trên Dev | Chưa thử |
|---|---|---|
| Bản nháp AI trả lời khách trên trang chuyến | đạt với model thật: 1 bản nháp trong khoảng 2 giây, khoảng 0,0001 USD | — |
| AA tạm dừng AI cho cả CRM | đạt: đại lý nhận câu báo, không gọi AI, 0 USD | trang Cài đặt → AI của đại lý chưa báo việc AA đang tạm dừng (làm tiếp) |
| Số chỗ và tính năng CRM theo gói đặt ở admin CIS | đạt (04/11): gói CRM Core → 10 chỗ, có bản nháp AI, SMS/WhatsApp bị từ chối; đổi gói thì CRM đổi theo trong vài phút | thử bằng một người dùng của đại lý đăng nhập thật và bấm gửi SMS/WhatsApp |

- **Bản nháp AI:** trên trang chuyến, đại lý dán tin nhắn của khách và bấm "Write draft". Thông tin cá nhân của khách được thay
  bằng ký hiệu (ví dụ `<PERSON_1>`) trước khi gửi cho AI; dưới bản nháp có dòng "AI can make mistakes. Check prices, dates, visa
  and safety information before you send or publish this."; đại lý chép và dùng, hoặc bỏ kèm góp ý. Đã thử 03/11 lúc 17:38 với
  đúng 1 lần bấm, dùng model tạm trên AWS trong lúc tài khoản AI chính còn bị chặn; chi phí khoảng 0,0001 USD (gồm bước che
  thông tin cá nhân). Bản nháp được bỏ sau khi xem, công tắc AI của đại lý trả về tắt như cũ.
- **AA tạm dừng AI cho cả CRM:** trong admin CIS (AI providers), AA tắt được AI cho cả app CRM. Đã thử 03/11: em tắt AI của CRM,
  đại lý thử bấm viết nháp thì nhận câu "AI drafts are paused by AA for now. Write this reply by hand.", không gọi AI, không
  tốn tiền; sau đó bật lại.
- **Số chỗ và tính năng theo gói:** số người dùng (chỗ) và tính năng CRM của mỗi đại lý (bản nháp AI, WhatsApp/SMS…) nay lấy
  theo gói đặt ở admin CIS; CRM tự cập nhật, và kiểm quyền ngay lúc đại lý dùng tính năng. Hai gói CRM có sẵn: **CRM Core**
  (10 chỗ, bản nháp AI) và **CRM Pro** (10 chỗ, thêm WhatsApp/SMS, thanh toán thẻ, chiến dịch, tên miền riêng, xuất báo cáo);
  cả hai chưa có giá (xem PR-20). Đã thử 04/11 trên đại lý thử Atlas & Hearth:
  - gán CRM Core → CRM của đại lý thành 10 chỗ, bản nháp AI được phép, gửi SMS/WhatsApp bị từ chối với câu "SMS and WhatsApp
    is not on this agency's plan";
  - tạo một gói thử có SMS/WhatsApp, 3 chỗ, gán cho đại lý → CRM đổi theo (3 chỗ, SMS/WhatsApp được phép);
  - gán lại CRM Core và gỡ gói thử → CRM về 10 chỗ, SMS/WhatsApp lại bị từ chối.

  Atlas & Hearth giữ CRM Core sau lần thử. Đại lý thử Sen Vàng (chưa có hồ sơ trong CIS) giữ nguyên như cũ. Lần thử kiểm quyền
  ngay trong CRM đang chạy, chưa thử bằng một người dùng của đại lý đăng nhập thật rồi bấm gửi (đại lý thử chưa có tài khoản
  người dùng riêng).
- **Một app cho đại lý:** từ 04/11 Content studio và CRM là một app: một địa chỉ, một lần đăng nhập, phần nào mở theo gói (chi
  tiết ở comment ngày 04/11 trên PR-23).
- **Tiếp theo:** theo mô hình mới, CRM là phần mua thêm tính theo người dùng (comment ngày 04/11 trên PR-20). Các phần CRM mới
  (thẻ khách, tìm kiếm, chiến dịch) làm tiếp trên app chung.

Ảnh theo thứ tự: (1) bản nháp AI trên trang chuyến, thông tin cá nhân đã thay bằng ký hiệu; (2) câu báo khi AA tạm dừng AI cho
cả CRM (chụp lúc CRM còn ở chế độ thử); (3) tab Subscription của đại lý thử Atlas & Hearth trong admin CIS: gói Content Growth
và CRM Core.

**Ảnh:**

| # | Tên khi upload | File | Che/cắt |
|---|---|---|---|
| 1 | crm-ban-nhap-ai.png | `docs/audits/2026-11-03-S266-live-verify/f4-draft/06-draft-result-1440.png` | không cần (dữ liệu mô phỏng, không email, không account ID) |
| 2 | crm-aa-tam-dung-ai.png | `docs/audits/2026-11-03-S265-live-verify/h1c-appoff/03-drawer-refused-1440.png` | không cần (tên "Anna" là tin nhắn bịa) |
| 3 | crm-goi-cua-dai-ly.png | `.tmp-session/S267/jira-img/cis-goi-cua-doi-tac-cat.png` | **đã cắt** từ `docs/audits/2026-11-04-S267-live-verify/aa1028/03-atlas-subscription-1440-light.png` (bỏ dải số chi phí AI và dòng "Content API keys") |

**Câu → bằng chứng (nội bộ):**

| Câu | Bằng chứng |
|---|---|
| 1 bản nháp, model thật, 1841 ms, 1 lần bấm, `<PERSON_1>`, AiNotice, discard + feedback, công tắc trả về tắt | `docs/audits/2026-11-03-S266-live-verify/f4-draft/data/crm-f4-results.json` (drafted_at 10:38:24Z, draftMs 1841, draftPostsSent 1, provider bedrock); ảnh 1 |
| ~0,0001 USD (Guardrail + Nova Lite 0,000034) | log S266 "Chi phí phiên"; checklist S266 dòng F4 |
| Model tạm trên AWS vì tài khoản AI chính bị chặn | Partner #205 (Nova Lite acc2, crm-042); ADR 0009 d14 (root #494, Dev only) |
| AA tắt AI cả CRM → `app_disabled`, câu báo, 0 USD, bật lại | `docs/audits/2026-11-03-S265-live-verify/h1c-appoff/README.md`; Linear AA-1025 comment 03/11 06:06Z |
| Settings → AI chưa báo tạm dừng | h1c-appoff README "Observations"; AA-1025 follow-up |
| Quyền theo gói, Sen Vàng giữ nguyên, WhatsApp/SMS kiểm lúc gửi | Linear AA-1028 lát 2 (Partner #209; Atlas projected `allowed_features=[]`, Sen Vàng `['ai_assist']`) |
| CRM W6–W8 tạm dừng tới gộp app → nay gộp xong | Linear AA-1034 "CRM W6–W8 … paused"; AA-1036 comment 04/11 08:00Z + 10:27Z |
| CRM Core: 10 chỗ, `[ai_assist]`; `whatsapp_sms` → 403 `feature_not_allowed` "SMS and WhatsApp is not on this agency's plan" | `docs/audits/2026-11-04-S267-live-verify/aa1028/README.md` bước 2–4 (job `a7bf8afa…`, projected 01:40Z) |
| Gói thử 3 chỗ + SMS → CRM theo; gán lại Core, retire → 10 chỗ, `[ai_assist]` | aa1028 README bước 5–10 (01:46Z, 02:16Z) |
| CRM Pro gồm WhatsApp/SMS, stripe, campaigns, custom domain, insights export; 10 chỗ; cả hai chưa có giá | CIS `api/migrations/355_tenant_plans_seed_and_entitlement_view.sql` dòng 130–193; ảnh Plans "No price" |
| "vài phút": pull mỗi 2 phút | aa1028 README bước 3 |
| Chưa thử bằng user đại lý đăng nhập (cần secret E2E mới ~0,40 USD/tháng) | aa1028 README "Not tested live" ý 1 |

**Chưa kiểm:** 403 qua HTTP khi một người dùng đại lý đã đăng nhập bấm gửi SMS/WhatsApp (chỉ kiểm hàm chặn quyền trong
container CRM đang chạy; ánh xạ sang 403 có unit test); gói CRM Pro chưa gán thử cho đại lý nào (lần thử dùng gói thử riêng).

---

## 5. PR-24 — TripPlanner (03–04/11)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** thay đổi khách nhìn thấy trên TripPlanner theo mô hình B2B, công tắc AI đã thử thật, dấu AI và điều khoản;
04/11 trang tour hiện giá "from" lấy từ Booking.

**Nội dung (sẵn để đăng):**

@thule Cập nhật TripPlanner ngày 03–04/11 (tiếp theo cập nhật 02/11):

- **Theo mô hình chỉ B2B:** nút "Send to an advisor" không còn gửi chuyến đi cho AA; trang hiện thông báo đây là bản demo,
  Adventure Asia làm việc với đại lý nên không nhận chuyến từ đây. Đã kiểm 03/11: yêu cầu gửi bị từ chối kèm câu "This planner
  is a demo: Adventure Asia works with travel agencies, so trips are not sent to an advisor here.", không tạo hồ sơ khách nào;
  chưa chụp màn hình thông báo trên trang. TripPlanner cho đại lý (gắn lên website đại lý, mang thương hiệu đại lý, yêu cầu của
  khách vào CRM của đại lý) làm ở giai đoạn sau, xem comment ngày 04/11 trên PR-20.
- **AA tắt AI của TripPlanner:** đã thử 03/11: tắt AI thì tìm kiếm chuyển sang tìm theo từ khoá, có dòng thông báo nhẹ, không tốn
  tiền; bật lại thì tìm kiếm như cũ. (Trường hợp vượt trần 5 USD/ngày vẫn chưa thử thật.)
- **Dấu AI máy đọc được:** các đoạn chữ do AI hỗ trợ viết trên trang tour (mô tả, lịch trình từng ngày) mang thêm một dấu ẩn để
  công cụ tìm kiếm và nền tảng biết đây là nội dung có AI hỗ trợ; dữ liệu tour TripPlanner gửi ra cũng mang dấu này. Khách
  không thấy khác. Đã kiểm 03/11 trên một trang tour Bhutan: 9 đoạn có dấu.
- **Điều khoản:** mục "Use of AI" nay ghi rõ AI viết lời dẫn chuyến đi là Claude (qua Amazon Bedrock) và có link chính sách sử dụng
  của Anthropic (bản nháp v0.2, kiểm trên trang đang chạy 03/11).
- **Giá "from" trên trang tour (04/11):** ô "Make it yours" trên trang tour nay hiện giá bán lẻ gợi ý, ví dụ "From $235 per
  person — Suggested price for 2 travellers. Your advisor confirms the final price.". Giá lấy thẳng từ Booking (tính từ bảng giá
  nhà cung cấp, xem comment ngày 04/11 trên PR-25), kèm hạn hiệu lực; công cụ tìm kiếm cũng đọc được giá này. Đã kiểm 04/11
  trên một **tour thử** (Okinawa from Naha, 5 ngày): nhà cung cấp, khách sạn và giá đều là **dữ liệu mô phỏng** dựng để kiểm. Tour
  khác hiện chưa có bảng giá nhà cung cấp; nhập bảng giá thật là bước tiếp theo.

Ảnh theo thứ tự: (1) trang tour thử với giá "From $235 per person" (dữ liệu mô phỏng).

**Ảnh:**

| # | Tên khi upload | File | Che/cắt |
|---|---|---|---|
| 1 | tripplanner-gia-from.png | `docs/audits/2026-11-04-S267-live-verify/aa1029/tp-tour-from-price-1440-light.png` | không cần (trang công khai, không account ID, không email) |

(Dấu AI không nhìn thấy trên trang; thông báo demo chưa chụp.)

**Câu → bằng chứng (nội bộ):**

| Câu | Bằng chứng |
|---|---|
| Send to an advisor → 410 `b2b_only` + câu demo, không tạo case | Linear AA-1034 (TP #218, `537b0fd5`); câu chữ `AA-TripPlanner-Web` `backend/assembly/handler.py` `B2B_ONLY_DETAIL`; demo notice `frontend/lib/advisorDemo.ts` |
| Tắt AI → `ranking=keyword` + `ai_paused`, 0 USD, bật lại semantic | Linear AA-1025 comment 03/11 04:54Z (H1b) |
| Vượt trần chưa thử | PR-24 #10600; AA-1025 "Not proven live: TripPlanner spend bell" |
| 9 đoạn `data-ai-generated=true` trên trang tour | `docs/audits/2026-11-03-S266-live-verify/results.json` "AA-1040 TripPlanner machine mark: PASS (9 elements)"; ảnh `05-tp-tour-day-by-day-*` (tour Bhutan) |
| Dữ liệu tour gửi ra mang dấu | TP #223; checklist S266 "browse catalog-tours có `ai` (892 tour)" |
| Điều khoản v0.2, Claude qua Bedrock, link Anthropic | Linear AA-820 comment 03/11 10:43Z (TP #219 `dcbd2cfd`) |
| "From $235 per person — Suggested price for 2 travellers", schema.org Offer 235.00 USD, priceValidUntil 2027-02-01; tour thử, dữ liệu `SYNTHETIC S267` | `docs/audits/2026-11-04-S267-live-verify/aa1029/README.md` (TP #224 `cf6faf9a`); ảnh `tp-tour-from-price-*` |
| Tour khác chưa có bảng giá nhà cung cấp | aa1029 README: seed chỉ cho 1 tour E2E (6 rates, 1 rule); không có import bảng giá thật trong S267 |

**Chưa kiểm:** tour không có bảng giá hiển thị thế nào (không chụp); thông báo demo trên giao diện (chỉ kiểm câu trả lời của hệ thống); chuông báo chi tiêu AI TripPlanner (chưa có chi
tiêu thật); vượt trần 5 USD/ngày.

---

## 6. PR-25 — Booking (03–04/11)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** Booking đổi vai theo mô hình B2B: tắt khách lẻ, hồ sơ đối tác lấy từ CIS. Các câu chờ chị (thuế, % đặt cọc)
nay có số khởi điểm trong comment PR-20. 04/11: chuỗi giá tour (bảng giá nhà cung cấp → giá net → giá bán lẻ gợi ý) chạy thật
trên một tour thử.

**Nội dung (sẵn để đăng):**

@thule Cập nhật Booking ngày 03–04/11 (Dev):

- **Tắt phần khách lẻ:** Booking không nhận yêu cầu của khách lẻ từ TripPlanner nữa và không tạo hồ sơ khách lẻ mới. Đã kiểm 03/11:
  việc kéo yêu cầu khách lẻ đã dừng (4 lượt đang chờ được huỷ), thử ghi một hồ sơ khách lẻ mới thì bị từ chối. Dữ liệu cũ giữ
  nguyên để tra cứu và xoá theo quy định.
- **Danh sách đối tác lấy từ CIS:** mỗi đối tác trong admin CIS tự có hồ sơ đối tác trong Booking, trạng thái theo CIS. Lần chạy
  đầu tối 03/11: 10 đối tác thử được tạo (5 đang hoạt động, 5 đã ngừng hợp tác); 2 đại lý chỉ có trong Booking (gồm Lữ hành Sen
  Vàng) giữ nguyên, không bị đổi.
- **Nhãn AI trên nội dung tour lấy từ CIS:** Booking đã sẵn nhãn "AI-assisted" cho phần mô tả tour do AI hỗ trợ viết. Chưa có nội
  dung nào mang dấu (dấu được ghi khi nội dung CIS được đăng lại), nên chưa thử trên giao diện.
- **Thuế, % đặt cọc:** đã có số khởi điểm trong comment ngày 04/11 trên PR-20 (cọc 30 %, phần còn lại trước khởi hành 30 ngày,
  hợp đồng ghi giá chưa gồm thuế…). Các số này sẽ sửa được trên trang khi làm xong phần Booking cho đại lý.
- **Giá tour tự tính từ bảng giá nhà cung cấp (04/11):** Booking nay giữ bảng giá của nhà cung cấp (khách sạn, hướng dẫn viên,
  xe đưa đón… theo mùa) và quy tắc lợi nhuận cho đại lý. Từ đó Booking tự tính chi phí tour, giá net cho đại lý và giá bán lẻ
  gợi ý "from" (giá net + 25 %, theo bảng trong comment ngày 04/11 trên PR-20), có lưu lịch sử giá, rồi đưa giá bán lẻ gợi ý lên
  trang tour TripPlanner. Đã thử 04/11 trên một **tour thử** với nhà cung cấp, khách sạn và giá đều là **dữ liệu mô phỏng**: 6 dòng
  giá + 1 quy tắc → hệ thống tự tính, không cần thao tác tay:

  | Bước | Mỗi khách (2 khách, mùa thấp) |
  |---|---|
  | Chi phí từ bảng giá nhà cung cấp | 150 USD |
  | Giá net cho đại lý | 185 USD |
  | Giá bán lẻ gợi ý "from" (giá net + 25 %, làm tròn) | 235 USD, hiệu lực tới 01/02/2027 |

  Giá 235 USD hiện đúng trên trang tour TripPlanner (ảnh ở comment ngày 04/11 trên PR-24). Nhập bảng giá từ file đã có trong
  hệ thống, chưa thử với bảng giá thật của nhà cung cấp; màn hình Booking cho phần giá chưa chụp kiểm.

**Ảnh:** không (giá xem ở ảnh trang tour trên PR-24; màn hình Booking chưa chụp).

**Câu → bằng chứng (nội bộ):**

| Câu | Bằng chứng |
|---|---|
| Tắt intake B2C, 4 lượt huỷ, INSERT bị từ chối, giữ SELECT/UPDATE/DELETE | `.tmp-session/S265/r0_bk_probe.out` (bk_inquiry_pull cancelled 4, INSERT refused 42501); Linear AA-1034 (Booking #170 bk-036, #171) |
| 10 tạo, 5 active / 5 suspended (offboarded), 2 chỉ có trong Booking giữ nguyên, Sen Vàng active | Linear AA-1028 lát 2 (`bk_tenant_pull` 15:44Z: created=10, awaiting_cis=2) |
| Nhãn AI Booking, chưa có dữ liệu | Booking #176; checklist S266 "v_supply_content có 3 cột ai_* (NULL tới khi publish)" |
| Chuỗi giá: catalog bridge, cost sheet từ rates, RRP, import bảng giá, lịch sử giá | Booking #179 (bk-039) + #180 `3ef1434b`; CIS #1291 (365); TP #224 |
| Seed giả 6 rates + rule b2b RRP 25 %; worker `bk_price_recompute` tự chạy 08:41Z; `v_from_prices` 235.00 USD, 2 khách, Low, rrp, 2026-11-04..2027-02-01; net 150 → b2b 185 → RRP 235 | `docs/audits/2026-11-04-S267-live-verify/aa1029/README.md` (seed run-script 41801245083 sau DRY RUN 41800519848) |
| Import bảng giá chưa thử thật; Booking admin chưa chụp (phiên staff của agent chỉ đọc / bị từ chối) | aa1029 README "Not done here" |

**Chưa kiểm:** giao diện Booking (không chụp trong S265–S267); nhãn AI trên giao diện; nhập bảng giá từ file; phần giá trên
portal đối tác (đọc giá "from" ở chợ tour của Content studio — làm tiếp).

---

## 7. PR-22 — CIS nội dung & pipeline (admin, 03–04/11)

**Trạng thái:** chưa đăng — chờ duyệt.

**Vì sao issue này:** admin CIS đổi bố cục theo mô hình B2B (comment 02/11 #10606 báo 10 nhóm; nay 7 nhóm), bỏ số liệu khách lẻ,
thêm trang kiểm nội dung đối tác; 04/11 thêm vai trò nhân viên AA, Writing Lab theo từng bước viết và một trang Spend.

**Nội dung (sẵn để đăng):**

@thule Cập nhật trang quản trị CIS ngày 03–04/11 (Dev):

- **Thanh bên sắp lại thành 7 nhóm theo mô hình B2B** (thay cho 10 nhóm báo ngày 02/11): Home; Tenants (danh sách đối tác, đại
  lý CRM, xoá dữ liệu); AA Catalogue (kho tour của AA: tải lên, viết lại, duyệt, Master, địa điểm, ảnh…); Tenant content QA
  (kiểm nội dung của đối tác); AI & spend; Writing Lab; Platform. Các link cũ tự chuyển sang chỗ mới. Đã kiểm 03/11: đủ 7 nhóm,
  3 link cũ chuyển đúng, máy tính và điện thoại, sáng và tối, không lỗi.
- **Tenants → Directory:** danh sách đối tác với gói và trạng thái (Dev: 11 đối tác thử, 6 đang hoạt động, 5 đã ngừng).
- **Bỏ số liệu khách lẻ:** trang Overview không còn thẻ khách TripPlanner và phễu khách lẻ của Booking; các báo cáo dựa trên khách
  lẻ đã gỡ hoặc chuyển thành số lịch sử. Đã chạy lại 5/5 báo cáo còn dùng ngày 03/11, không báo đỏ sai.
- **Tenant content QA → Compliance:** nơi AA xem các bài của đối tác bị giữ (link đặt tour ngoài Adventure Asia, tour đã ngừng bán)
  kèm lý do. Hiện 0 mục.
- **Vai trò nhân viên AA (04/11):** thêm 6 vai trò cho nhân viên trên admin: phụ trách nội dung, kiểm nội dung đối tác, chăm sóc
  đối tác (customer success), hỗ trợ (support), kế toán (finance), vận hành AI. Mỗi vai trò chỉ mở đúng phần việc của mình (ví
  dụ: hỗ trợ không xem số tiền và mức sử dụng của đối tác). Người chăm sóc đối tác chỉ thấy các đối tác được giao cho mình. Đã
  kiểm 04/11 trên hệ thống đang chạy: một nhân viên được giao Atlas & Hearth xem được thành viên của Atlas & Hearth, mở một đối
  tác khác thì bị từ chối ("Tenant outside your scope"), danh sách đối tác chỉ hiện Atlas & Hearth; hỗ trợ mở trang sử dụng bị
  từ chối; admin xem được mọi đối tác. Phép giao thử đã gỡ sau khi kiểm. Chưa thử bằng tài khoản nhân viên đăng nhập thật. Làm
  tiếp: trang giao đối tác cho nhân viên trên giao diện, chế độ "xem như đối tác" (chỉ xem, có giới hạn thời gian, có ghi lại).
- **Writing Lab theo từng bước viết (04/11):** mỗi bước viết có một trang riêng: A1 (viết lại tour AA), T2 (viết lại cho đối tác),
  T9 bài blog, T9 bài mạng xã hội. Mỗi trang có 5 phần: bộ bài mẫu dùng để chấm, nhãn chấm, các thử nghiệm, các phiên bản
  hướng dẫn viết (prompt) và cổng đánh giá (một thay đổi phải qua đánh giá trước khi chạy thật). Trang chỉ để xem, không đổi gì
  ở bộ viết. Đã kiểm 04/11: cả 4 bước đủ 5 phần; số bài mẫu 55 / 20 / 23 / 36, số phiên bản prompt 6 / 5 / 8 / 8. Cổng đánh giá
  của cả 4 bước đang báo "cần kiểm lại" vì đầu vào đã đổi từ lần duyệt trước; bản đang chạy vẫn phục vụ bình thường.
- **Một trang Spend (04/11):** thay cho 3 trang chi phí cũ, gồm các tab Overview, AI & data spend, AWS bill và By app (chi phí từng
  app trong tháng). Link cũ tự chuyển sang tab tương ứng. Đã kiểm 04/11: 5 link cũ (chi phí và Writing Lab) chuyển đúng, không lỗi. Số chi phí tháng 10
  sẽ có trong báo cáo kỳ 4.

Ảnh theo thứ tự: (1) thanh bên 7 nhóm, (2) trang Tenants → Directory, (3) Writing Lab, bước T9 bài mạng xã hội, phần bộ bài
mẫu, (4) trang Spend với 4 tab.

**Ảnh:**

| # | Tên khi upload | File | Che/cắt |
|---|---|---|---|
| 1 | cis-thanh-ben-7-nhom.png | `.tmp-session/S267/jira-img/cis-admin-thanh-ben-7-nhom.png` | **đã cắt** từ `docs/audits/2026-11-03-S266-live-verify/aa1039-admin-ia/02-sidebar-all-groups-open-1440-light.png` (bản gốc có bảng chi phí theo app → không dùng) |
| 2 | cis-danh-sach-doi-tac.png | `docs/audits/2026-11-03-S266-live-verify/aa1039-admin-ia/05-tenants-directory-1440-light.png` | không cần (đối tác thử, không account ID, không email) |
| 3 | cis-writing-lab.png | `.tmp-session/S267/jira-img/cis-writing-lab-cat.png` | **đã cắt** từ `docs/audits/2026-11-04-S267-live-verify/aa1039/lab-t9-social-tab-samples-1440-light.png` (bỏ dòng mã bộ mẫu nội bộ và bảng mẫu) |
| 4 | cis-spend.png | `.tmp-session/S267/jira-img/cis-spend-tab-cat.png` | **đã cắt** từ `aa1039/spend-apps-1440-light.png` — chỉ tiêu đề + 4 tab; bản gốc có **account ID AWS** và số chi phí → không dùng |

**Câu → bằng chứng (nội bộ):**

| Câu | Bằng chứng |
|---|---|
| 7 nhóm (tên + mục), redirect 307 ×3, 1440/390, sáng/tối, 0 lỗi console/4xx | `docs/audits/2026-11-03-S266-live-verify/results.json` (navGroups, redirects, verdicts AA-1039 PASS); Linear AA-1039 lát 1 (CIS #1277) |
| Directory 11 dòng, 6 active / 5 offboarded | results.json `tenantsRows: 11`; ảnh 2 |
| Overview không còn thẻ B2C | Linear AA-1034 (CIS #1271), ảnh `docs/audits/2026-11-03-S265-live-verify/r0-overview/` |
| 5/5 báo cáo, 0 đỏ sai, TP-03 gỡ, KPI B2C lịch sử | log S266 bảng (AA-1003, root #493, CIS #1272); checklist S266 dòng AA-1003 |
| Compliance 0 mục | Linear AA-1039 lát 2 "Compliance listing: 0 open flags" |
| 6 vai trò (content lead, tenant QA, customer success, support, finance, AI ops); support không xem tiền/usage | Linear AA-1035 comment 04/11 08:00Z (CIS #1289/#1290, Infra #651, mig 362–364); `.tmp-session/S267/r2-final.json` (support: `tenant.book.account.read` không có, money null) |
| Kiểm cô lập ~08:00Z (15:00 +07): assigned → members 200, Terra Family 403 "Tenant outside your scope", directory chỉ `atlas-hearth`; support → usage 403; viewer → members 403; admin 200; gỡ assignment | Linear AA-1035 comment 04/11 08:00Z "Live isolation check (in the api container, real routes)" |
| Làm tiếp: view-as, trang Assignments | AA-1035 "Left (slice 2)" |
| Writing Lab 4 bước × 5 phần `ready`, mẫu 55/20/23/36, prompt 6/5/8/8, gate `reverify` | `docs/audits/2026-11-04-S267-live-verify/aa1039/README.md` (CIS #1286, #1287; ô KPI sửa ở #1288) |
| Spend: 4 tab, 5 redirect, 0 lỗi console | aa1039 README "UI" |

**Chưa kiểm:** ngừng bán tour → thông báo → bán lại (xem PR-23 A); vai trò nhân viên bằng tài khoản đăng nhập thật (chỉ kiểm qua
route thật trong container); vai trò kế toán trên Booking (đã lên Dev, không thử, không nêu). Không đưa: trang Docs/kiến trúc,
gom chi phí, AI gateway (việc kỹ thuật / kỳ 4).

---

## Không soạn (và vì sao)

- **PR-20 kỳ 4 (03–09/11):** chưa đến hạn (thứ Hai 09/11). Báo cáo chi phí AWS chính thức tháng 10 (482,77 USD mức dùng / khoảng
  246,70 USD thực trả) vào kỳ 4 như đã ghi ở #10603.
- **PR-27 Nền tảng:** đổi tên môi trường triển khai, diễn tập, chặn chi phí AI theo app, bảo vệ môi trường prod, dựng khung prod
  nhẹ, tài liệu kiến trúc, cách chạy frontend trên AWS và chi phí Dev, Fargate/WAF — việc kỹ thuật của tech lead (memory
  `jira-no-tech-decisions`).
- **Trao đổi với Sunny Cloud / IDS / eCloudvalley:** việc của tech lead với nhà cung cấp, chưa có trả lời văn bản; không đưa Jira.
- **Artifact giải thích TripPlanner cho tenant** (`docs/audits/2026-11-03-S266-tripplanner-tenant-addons/`): viết cho tech lead,
  không phải cho chị Thư.
- **KAN/CON:** không có việc liên quan S265–S267.
- **S267 không đưa Jira:** định tuyến LLM theo họ model + chuỗi dự phòng, bảng khả dụng model, việc với tài khoản AI trên AWS,
  quyền IAM, dời stack TripPlanner trong Terraform, khoá API key ở tầng hạ tầng, xoá secret — quyết định/việc kỹ thuật của tech
  lead (memory `jira-no-tech-decisions`). Vai trò kế toán trên Booking: đã lên Dev nhưng chưa thử thật → không nêu.

## Kết quả đăng

Đăng 04/11 ~20:20–20:35 +07 sau khi tech lead duyệt ("ok sửa rồi đăng đi, kèm ảnh"), đúng bản đã sửa ở trên.

| # | Issue | Comment | Ảnh |
|---|---|---|---|
| 1 | PR-20 | [10608](https://adventure-asia.atlassian.net/browse/PR-20?focusedCommentId=10608) | 0 |
| 2 | PR-23 A | [10611](https://adventure-asia.atlassian.net/browse/PR-23?focusedCommentId=10611) | 3 |
| 3 | PR-23 B | [10612](https://adventure-asia.atlassian.net/browse/PR-23?focusedCommentId=10612) | 0 |
| 4 | PR-26 | [10613](https://adventure-asia.atlassian.net/browse/PR-26?focusedCommentId=10613) | 3 |
| 5 | PR-24 | [10614](https://adventure-asia.atlassian.net/browse/PR-24?focusedCommentId=10614) | 1 |
| 6 | PR-25 | [10610](https://adventure-asia.atlassian.net/browse/PR-25?focusedCommentId=10610) | 0 |
| 7 | PR-22 | [10615](https://adventure-asia.atlassian.net/browse/PR-22?focusedCommentId=10615) | 4 |

Ghi chú: lần đầu PR-25 bị 400 `INVALID_INPUT` (bảng nằm trong gạch đầu dòng) → đưa bảng ra ngoài danh sách. Upload ảnh timeout
khi VPN bật (IP ra NL); tech lead tắt VPN rồi upload được. Không đổi trạng thái issue Jira nào.
