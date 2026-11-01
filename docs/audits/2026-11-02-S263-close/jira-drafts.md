> **CHƯA ĐĂNG.** Nháp Jira S263 (gộp 7 nháp S262 chưa đăng + việc S263 01–02/11). Chưa đăng, chưa sửa, chưa đổi trạng
> thái issue nào. Chờ tech lead duyệt một lần, rồi đăng theo skill `aa-jira-update` (`contentFormat: html`, bảng markdown
> đổi sang bảng HTML, ảnh upload từng file rồi nhúng bằng `inlineFileId` đúng thứ tự).

# S263 — nháp Jira cho chị Thư

Soạn 02/11/2026 (Claude Code, phiên S263). Mention khi đăng:
`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>` (thay chữ `@thule`
ở đầu mỗi nháp).

## Đã rà trên Jira (chỉ đọc, 02/11)

- JQL `project in (PR, KAN, CON) AND updated >= "2026-10-31"`: **0 issue**. JQL `project = PR AND updated >= -5d`: chỉ các
  epic PR-22…PR-27, cập nhật cuối 29–30/10. → Không nháp S262 nào đã được đăng; không có comment mới của chị Thư (câu hỏi
  điều khoản AI A/B/C ở PR-23 #10508 vẫn chưa có trả lời). Comment mới nhất mỗi epic như ghi trong nháp S262
  (PR-26 #10564, PR-25 #10563, PR-24 #10565, PR-23 #10533, PR-22 #10566, PR-27 #10532; PR-28 kỳ 2 không có gì mới).
- KAN/CON: không có việc mới liên quan → không soạn.

## Danh sách (epic → nội dung)

| # | Epic | Một dòng | Ảnh |
|---|---|---|---|
| 1 | PR-26 CRM (A) | Việc ship 31/10: trang riêng từng khách, nhập dữ liệu, báo cáo, thư, ký điện tử, cảnh báo sự cố, xoá dữ liệu thật (nháp S262 §1, giữ nguyên) | 6–7 |
| 2 | PR-26 CRM (B) | Việc ship 31/10–01/11: thanh toán còn lại, hoa hồng, huỷ chuyến, bàn giao điều hành, ngoại tuyến, hỗ trợ AA, trợ lý AI (nháp S262 §2, giữ nguyên) | 10 |
| 3 | PR-26 CRM (C, mới) | 01–02/11: AA tạo đại lý từ admin CIS; mời chủ đại lý (mật khẩu một lần, đổi mật khẩu, đăng nhập 2 bước) tech lead thử trọn vòng; xoá đại lý thử; WhatsApp + SMS (sandbox); thông báo AI + mục AI trong điều khoản CRM | 2 |
| 4 | PR-25 Booking | Đề xuất báo khi CIS có nội dung mới hơn (nháp S262 §3, giữ nguyên) | 2 |
| 5 | PR-24 TripPlanner | Chống bot, giới hạn AI, trang Dev không lập chỉ mục (S262) + thông báo AI trên trang tour/chân trang và mục "Use of AI" trong điều khoản (S263, kiểm live 02/11) | 3 |
| 6 | PR-23 Portal | Trần chi phí AI theo đối tác; điều khoản AI (nhắc A/B/C), cập nhật: CRM nay đã có mục AI trong điều khoản | 1 |
| 7 | PR-22 CIS | Định vị địa điểm kết quả cuối 01/11 (S262) + AI chạy tiếp bằng model dự phòng có trần chi tiêu, trang nhà cung cấp AI có lỗi/độ trễ và công tắc bật/tắt (S263) | 0 |
| 8 | PR-20 báo cáo kỳ 3 | 27/10–02/11 gồm S263, kèm link trang báo cáo cho buổi họp 14:00 02/11 | 0 |

Không soạn PR-27 (việc kỹ thuật của tech lead: gia cố bảo mật, giảm cảnh báo, cổng AI, quy trình ship, tài liệu kiến
trúc, runbook). Chỉ một dòng kết quả trong PR-20 (tuỳ tech lead bỏ).

## Kiểm trước khi đăng (ô tech lead chốt)

- [ ] Giữ toàn bộ các ô "Kiểm trước khi đăng" của nháp S262 (`docs/audits/2026-11-01-S262-close/jira-drafts.md` dòng
  35–54: ảnh đã che email, ảnh đã cắt, ảnh PR-23 chỉ khung "AI budget", ảnh huỷ chuyến bản r3, ảnh Booking có tên khách thử).
- [ ] **Không đính ảnh trang Providers** (`.tmp-session/S263/evidence-private/`): có account ID AWS.
- [x] **Đã sửa 02/11 (Partner #190, kiểm live: /terms và /privacy có "Amazon Nova", "Meta Llama"). Lệch phát hiện khi soạn (nội bộ, không đăng):** trang điều khoản portal (kiểm 02/11) chỉ liệt kê Claude (qua
  Bedrock), OpenAI (qua Bedrock) và API Anthropic/OpenAI dự phòng; **không nhắc Amazon Nova / Meta Llama**, trong khi
  migration 331/332/333 đã đặt các model này làm dự phòng cho bước kiểm tra/chấm điểm, kể cả bước của đối tác (332). Nên
  sửa terms portal (và CRM nếu liệt kê nhà cung cấp) trước khi đăng PR-23, hoặc ít nhất trước khi có đối tác thật.
- [ ] PR-20: đăng làm comment trên PR-20, hoặc tạo story "Báo cáo nền tảng kỳ 3 (27/10–02/11/2026)" dưới PR-20 **chỉ khi
  tech lead nói tạo**. Đăng trước hay sau buổi họp 14:00 là tech lead chọn; trang báo cáo đã chia sẻ trong tổ chức
  (checklist S263 "Báo cáo v2 … chia sẻ cho tổ chức") — mở thử bằng tài khoản chị Thư nếu chưa chắc.
- [x] PR-26 C: "rút lại lời mời" đã thử live (tech lead, 01/11: hộp thoại Withdraw → mời lại → mật khẩu một lần hiện → vào CRM).

---

## 1. PR-26 — CRM cho đại lý — comment A (ship 31/10)

**Giữ nguyên văn** nháp S262 §1 (`docs/audits/2026-11-01-S262-close/jira-drafts.md` dòng 58–129): nội dung, bảng, 7 dòng
ảnh và bảng câu → bằng chứng. Không có số nào cần làm mới (đều là kết quả thử ngày 31/10).

Thay đổi duy nhất: ảnh số 6 (băng cảnh báo sự cố) nay **có** file đã cắt `.tmp-session/S262/jira-img/crm-canh-bao-su-co.png`
(chụp 31/10, chỉ có băng "AA reported an incident on a departure in this trip"). Đính kèm làm ảnh 6, giữ câu chú thích
"(6) băng cảnh báo sự cố trên chuyến"; nếu không đính thì bỏ "(6)" và đánh lại số ảnh.

**Bằng chứng:** như nháp S262 §1. **Chưa kiểm:** như nháp S262 §1 (mail thật, Excel lớn, M365/SMTP, PDF chữ ký số, bấm sự
cố từ giao diện Booking).

---

## 2. PR-26 — CRM cho đại lý — comment B (ship 31/10–01/11)

**Giữ nguyên văn** nháp S262 §2 (dòng 133–226), 10 ảnh bản r2/r3 như bảng ảnh trong đó.

**Bằng chứng:** như nháp S262 §2. **Chưa kiểm:** huỷ khi Booking ngừng, huỷ chuyến có hoá đơn chưa trả, màn hình nhân
viên AA (hỗ trợ/điều hành), cài trang khách lên điện thoại thật, model AI thật cho trợ lý. Câu "Đang sửa tiếp: chuyến đã
huỷ vẫn còn hiện khoản thu còn lại…" chưa kiểm lại trong S263 — giữ nguyên.

---

## 3. PR-26 — CRM cho đại lý — comment C (mới, 01–02/11)

**Vì sao issue này:** cùng epic CRM; các việc S263 người dùng nhìn thấy: AA tạo đại lý, mời chủ đại lý, nhắn tin
WhatsApp/SMS, thông báo AI.

**Nội dung (sẵn để đăng):**

@thule Cập nhật CRM cho đại lý ngày 01–02/11 (Dev, dữ liệu giả, tiếp theo hai cập nhật trên):

| Phần | Đã thử trên Dev | Chưa thử |
|---|---|---|
| AA tạo đại lý mới từ trang quản trị CIS | đạt (tạo đại lý thử "test nghiep") | — |
| Mời chủ đại lý và đăng nhập lần đầu | đạt trọn vòng, tôi tự thử | — |
| AA xoá đại lý thử, rút lại lời mời chủ đại lý | đạt, tài khoản đăng nhập chưa dùng được dọn theo | — |
| Nhắn tin WhatsApp và SMS | đạt 7/7 bước với tài khoản thử (không gửi tin thật) | gửi tới điện thoại thật bằng tài khoản Twilio thật |
| Thông báo "AI có thể sai" và mục AI trong điều khoản | đã đưa lên Dev | kiểm trên giao diện |

- **AA tạo đại lý mới:** trong admin CIS (Platform → Agencies), người có quyền quản lý nền tảng bấm "Create agency", nhập
  tên đại lý, email chủ đại lý và mã yêu cầu hỗ trợ. Đại lý mới có ngay gói mặc định (10 chỗ, ngân sách AI 2 USD/tháng trên
  Dev). Đã thử: tạo đại lý thử "test nghiep", đại lý hiện trong danh sách và mở được.
- **Mời chủ đại lý:** chủ đại lý nhận email mời, mở link một lần thì thấy mật khẩu dùng một lần, đăng nhập rồi đặt mật
  khẩu riêng, bật đăng nhập 2 bước, chấp nhận lời mời và vào CRM với vai trò Owner. Tôi đã tự thử trọn vòng ngày 01/11,
  gồm cả đăng xuất rồi đăng nhập lại bằng mã 2 bước.
- **AA dọn đại lý thử:** AA xoá được một đại lý thử chưa có dữ liệu; tài khoản đăng nhập đã mời mà chưa từng dùng được xoá
  theo, và mỗi ngày hệ thống tự dọn các tài khoản như vậy. Đã thử trên đại lý thử "test nghiep 2": xoá xong, không còn tài
  khoản nào sót. AA cũng rút lại được lời mời chủ đại lý chưa nhận rồi mời lại: tôi đã thử trên "test nghiep" ngày 01/11, lời mời mới mở ra đúng mật khẩu một lần.
- **Nhắn tin WhatsApp và SMS (Cài đặt → SMS and WhatsApp):** đại lý kết nối tài khoản Twilio của chính mình; Twilio (và
  Meta với WhatsApp) tính phí thẳng cho đại lý, AA không thu phí phần này. Trên trang chuyến có khung WhatsApp/SMS: gửi tin,
  có 10 giây để huỷ trước khi gửi, thấy trạng thái đã nhận / đã đọc; tin khách trả lời hiện ngay trên chuyến. Ngoài 24 giờ
  kể từ tin cuối của khách, WhatsApp chỉ cho gửi mẫu tin đã được duyệt. Tin từ số chưa biết vào Hộp thư để gắn vào khách.
  Đã thử 7/7 bước bằng tài khoản thử (sandbox, không gửi tin thật, không tốn tiền): kết nối, lấy mẫu tin, gửi tin thử, nhận
  tin trả lời, từ chối tin giả mạo, trạng thái đã đọc, giao diện máy tính và điện thoại. Chưa thử với tài khoản Twilio
  thật gửi tới điện thoại thật.
- **Thông báo AI:** dưới mỗi bản nháp do AI soạn có dòng nhắc "AI can make mistakes. Check prices, dates, visa and safety
  information before you send or publish this."; trang Cài đặt → AI có thêm quy tắc này; điều khoản sử dụng CRM có thêm mục
  về nội dung do AI tạo (bản nháp, chờ luật sư như điều khoản portal). Trang chuyến khách xem cũng có dòng thông báo cho
  khách. Đã đưa lên Dev ngày 01/11, chưa kiểm trên giao diện.

Ảnh theo thứ tự: (1) trạng thái kết nối WhatsApp/SMS với tài khoản thử, (2) khung WhatsApp trên trang chuyến với tin đã đọc.

**Ảnh:**

| # | Tên khi upload | File |
|---|---|---|
| 1 | crm-whatsapp-sms-ket-noi.png | `.tmp-session/S263/jira-img/crm-whatsapp-sms-ket-noi.png` (cắt khung Status từ `aa958-live/settings-channels-desktop-light.png`; bản đầy đủ có link hook riêng của đại lý → không dùng) |
| 2 | crm-whatsapp-tren-chuyen.png | `.tmp-session/S263/jira-img/crm-whatsapp-tren-chuyen.png` (= `aa958-live/06d-trip-whatsapp-read-badge-desktop-light.png`, số điện thoại giả) |

**Bằng chứng (nội bộ, không đăng):**

| Câu | Bằng chứng |
|---|---|
| Tạo đại lý từ admin CIS, "test nghiep", 0/10 chỗ, AI 2 USD, gói free | Linear AA-1031 comment 01/11 14:13Z (Done evidence); checklist S263 dòng 144 |
| Mời chủ đại lý trọn vòng do tech lead thử | checklist S263 "CRM invite end to end PASSED by Nghiệp (re-invite → one-time password shown → change pw → MFA → accept → CRM Owner → sign-out → sign-in with MFA)"; Partner #186, #187 |
| Xoá đại lý thử + dọn tài khoản chưa dùng, dọn hằng ngày | `.tmp-session/S263/tmpjt2v84lz.md` (tech lead xoá "test nghiep 2"); checklist dòng 180: dry run would_delete 1 → apply deleted 1 → list-users = 0; Partner #189 (td :117) |
| WhatsApp/SMS 7/7, sandbox $0, BYO Twilio, 24 h, undo 10 s, READ, Inbox | Linear AA-958 comment 01/11 09:21Z; `.tmp-session/S263/aa958-live/findings.md`, `run-log.txt` |
| Thông báo AI + mục AI trong điều khoản CRM | Partner #185 (90e8c4b, `web/app/(crm)/terms`, `AiSettingsView`, `trip/[tourId]`), deploy cùng #186 (CRM api+web e5d5d517) |

**Chưa kiểm:** WhatsApp/SMS với Twilio thật và điện thoại thật; 409 cần mẫu tin khi cửa
sổ 24 h đóng, 409 thiếu đồng ý marketing (chỉ test tự động); thông báo AI + điều khoản CRM chưa có ảnh trên giao diện
(trang sau đăng nhập; `crm.lumiguides.it.com` không phân giải từ máy này lúc soạn). **Không đưa vào:** công cụ tự động hoá
và trang Tasks/Automations (AA-959, Partner #183 đã merge, crm-038 áp, **chưa kiểm live**) — báo ở phiên sau khi đã thử.
Việc nhỏ còn lại (phụ đề Hộp thư, nút copy link hook trên điện thoại, gợi ý ô "Ticket reference") không đưa.

---

## 4. PR-25 — Booking

**Giữ nguyên văn** nháp S262 §3 (dòng 230–258), 2 ảnh. S263 không có thay đổi Booking người dùng nhìn thấy (chỉ đồng bộ
bộ giao diện và giảm cảnh báo — nội bộ).

**Bằng chứng:** như nháp S262 §3. **Chưa kiểm:** bấm Save sau Refresh (lần kiểm không lưu).

---

## 5. PR-24 — TripPlanner (gộp S262 + S263)

**Vì sao issue này:** epic TripPlanner; ba thay đổi S262 (chống bot, giới hạn AI, trang Dev không lập chỉ mục) và thông
báo AI + điều khoản S263, đã kiểm trên trang đang chạy 02/11.

**Nội dung (sẵn để đăng):**

@thule Cập nhật TripPlanner ngày 31/10–02/11 (tiếp theo cập nhật 30/10):

- **Chặn bot ở phần tìm kiếm và lời dẫn từng ngày:** hai phần có thể gọi AI chỉ chạy cho trình duyệt thật (dùng gói kiểm
  bot miễn phí của Vercel). Đã kiểm 31/10: trình duyệt thật tìm kiếm bình thường; gọi tự động từ dòng lệnh hoặc trình
  duyệt chạy ngầm bị từ chối. Các trang khác (danh sách nước, tour) không bị ảnh hưởng.
- **Giới hạn dùng AI cho mỗi khách:** tìm kiếm tối đa 30 lượt mỗi phút cho mỗi địa chỉ mạng, lời dẫn từng ngày tối đa 10
  lượt mỗi giờ cho mỗi phiên (khách đăng nhập được gấp đôi); chỉ đếm lượt thật sự gọi AI. Vượt giới hạn thì trang hiện một
  dòng nhắc thử lại sau. Đã thử 31/10: 35 lượt tìm kiếm trong một phút → 30 lượt trả kết quả, 5 lượt bị từ chối đúng giới
  hạn. Lời dẫn: cả 892 tour đều có nội dung ngày của Adventure Asia nên trang dùng thẳng nội dung đó, không gọi AI và không
  bị tính vào giới hạn.
- **Trần chi phí AI theo ngày** cho TripPlanner: 5 USD/ngày, cảnh báo khi tới 80 %. Khi AI không chạy được (vượt trần hoặc
  nhà cung cấp lỗi), tìm kiếm chuyển sang tìm theo từ khoá và lời dẫn dùng nội dung có sẵn, có một dòng thông báo nhẹ. Phần
  này đã có trong hệ thống, chưa thử thật trường hợp vượt trần.
- **Trang TripPlanner bản Dev** (aa-tripplanner.vercel.app) giờ báo công cụ tìm kiếm không lập chỉ mục và có dòng "Preview
  site" ở cuối trang, để khách không nhầm là trang chính thức. Như vậy trang Dev không được tính điểm SEO; trang chính thức
  sau go-live mới được lập chỉ mục. Đã kiểm trên trang đang chạy 01/11.
- **Thông báo nội dung có dùng AI:** trang tour và cuối mọi trang có dòng "Some descriptions are written with the help of
  AI and may contain mistakes. Prices, itineraries and visa conditions are confirmed in your official quote.", kèm link
  "Use of AI".
- **Điều khoản có mục "Use of AI"** (https://aa-tripplanner.vercel.app/terms, mục 3): AI giúp viết mô tả tour, lịch trình
  từng ngày và lời dẫn chuyến đi; nội dung do AI viết có thể sai, chỉ để tham khảo, không dùng cho quyết định về đi lại,
  visa, sức khoẻ hay an toàn; giá, lịch trình và điều kiện visa chỉ ràng buộc theo báo giá chính thức và điều kiện đặt tour.
  Điều khoản vẫn là bản nháp, chờ luật sư xem như điều khoản portal. Đã kiểm hai phần này trên trang đang chạy 02/11.

Ảnh theo thứ tự: (1) tìm kiếm trên trình duyệt thật sau khi bật chặn bot, (2) dòng thông báo AI trên trang tour,
(3) mục "Use of AI" trong điều khoản.

**Ảnh:**

| # | Tên khi upload | File |
|---|---|---|
| 1 | tripplanner-tim-kiem-trinh-duyet-that.png | `docs/audits/2026-10-31-S262-evidence/AA-1015/headed-search-200-1440.png` |
| 2 | tripplanner-thong-bao-ai-trang-tour.png | `.tmp-session/S263/jira-img/tripplanner-thong-bao-ai-trang-tour.png` (chụp 02/11, tour Wheels around Taipei, 1440) |
| 3 | tripplanner-dieu-khoan-ai.png | `.tmp-session/S263/jira-img/tripplanner-dieu-khoan-ai.png` (chụp 02/11, /terms mục 3) |

**Bằng chứng (nội bộ):**

| Câu | Bằng chứng |
|---|---|
| Chặn bot, giới hạn, 892 tour, trần 5 USD, noindex | bảng bằng chứng nháp S262 §4 (dòng 296–302) |
| Thông báo AI trên trang tour + chân trang + link "Use of AI" | curl + Playwright 02/11: `/`, `/terms`, `/tours/wheels-around-taipei-…-74f84466` đều 200 và có câu "Some descriptions are written with the help of AI…"; ảnh 2; TP #210 (AA-1033) |
| Mục 3 "Use of AI" trong /terms | Playwright 02/11, heading "3. Use of AI" (1 heading), ảnh 3 |

**Chưa kiểm:** vượt trần 5 USD/ngày; thông báo AI trên trang lập kế hoạch (/plan) và giao diện điện thoại/tối (chỉ chụp
desktop sáng); lời dẫn khi AI không chạy (cần guest token, checklist S263 L4 còn ⏳).

---

## 6. PR-23 — Portal tenant

**Vì sao issue này:** câu hỏi điều khoản AI A/B/C (#10508, 25/10) chưa có trả lời; nháp S262 §5 thêm trần chi phí AI theo
đối tác. Làm mới một câu: CRM nay đã có mục AI trong điều khoản (S263).

**Nội dung (sẵn để đăng):** nguyên văn nháp S262 §5 (dòng 314–334), **trừ câu cuối đoạn "Đề xuất"** thay bằng:

> Đề xuất: A hoặc C. Thêm một điểm mới: CRM cho đại lý và TripPlanner nay cũng có mục "nội dung do AI tạo" trong điều
> khoản (bản nháp, cùng tinh thần với điều khoản portal: AI có thể sai, đại lý/khách cần kiểm lại, giá và điều kiện chỉ
> ràng buộc theo báo giá chính thức). Đề xuất áp cùng lựa chọn A/B/C của chị cho cả ba bản. Có nhờ luật sư hay không là
> chị quyết.

Ảnh: như nháp S262 §5 (`portal-tran-chi-phi-ai-doi-tac.png`, đã cắt chỉ khung "AI budget").

**Bằng chứng:** bảng nháp S262 §5; điều khoản TP mục 3 (Playwright 02/11, ảnh PR-24 số 3); điều khoản CRM: Partner #185.
Không có comment mới trên PR-23 (JQL 02/11: không issue PR nào cập nhật sau 30/10).

**Chưa kiểm:** điều khoản CRM trên giao diện. Danh sách nhà cung cấp trong terms/privacy portal đã khớp cấu hình AI (sửa và kiểm live 02/11, Partner #190).

---

## 7. PR-22 — CIS nội dung & pipeline (gộp S262 + S263)

**Vì sao issue này:** epic CIS; #10566 (30/10) đã báo định vị 78,4 % và "AI viết nội dung tạm dừng". Nay có kết quả định
vị cuối 01/11 (S262) và đường AI dự phòng + trang nhà cung cấp AI (S263).

**Nội dung (sẵn để đăng):**

@thule Cập nhật CIS ngày 01–02/11 (tiếp theo cập nhật 30/10):

**1. Định vị địa điểm trên bản đồ (kết quả cuối 01/11)**

- **Địa điểm mới:** từ nay toạ độ chỉ lấy từ dịch vụ tra bản đồ, không để AI tự đoán toạ độ, nên các địa điểm mới không
  còn bị ghim theo toạ độ AI đoán.
- **Dữ liệu cũ:** đợt kiểm lại toàn bộ địa điểm cũ đã chạy xong sáng 01/11, trên gói miễn phí.
- **Ẩn pin không chắc chắn:** khoảng 2.500 địa điểm mà dịch vụ tra bản đồ không xác nhận được vị trí đã được ẩn pin thay vì
  hiện một điểm có thể sai; địa điểm không bị xoá và pin tự hiện lại khi được xác nhận.

| Chỉ số (đo 01/11, trên mẫu 600 địa điểm đã chấm tay) | Số |
|---|---|
| Pin khách nhìn thấy trên bản đồ đặt đúng chỗ | ≈ 88 % |
| Tỉ lệ địa điểm vẫn còn hiện pin | ≈ 51 % |
| Toàn bộ dữ liệu cũ, tính cả pin đã ẩn (30/10 báo 78,4 %) | ≈ 80 % |

- **Sau này:** nếu thấy việc thiếu pin làm ảnh hưởng trải nghiệm khách, bên kỹ thuật sẽ xem xét bổ sung cách định vị
  thêm (có thể tốn phí) để hiện lại nhiều pin hơn. Hiện chưa cần làm gì thêm.

**2. AI chạy tiếp khi tài khoản AI chính bị chặn**

- Tài khoản AI chính vẫn bị AWS chặn từ 29/10 (AWS hẹn xử lý trong khoảng 05–06/11). Từ 01/11, mỗi bước dùng AI trong CIS
  có thêm model dự phòng: khi model chính không gọi được, hệ thống tự chuyển sang model dự phòng; mỗi đường dự phòng có trần
  chi tiêu theo tháng, tới trần thì dừng, không phát sinh thêm tiền.
- Đã thử bằng một lượt kiểm nhỏ trên Dev: 19/20 bước kiểm tra và chấm điểm chạy được trên model dự phòng, tổng chi phí
  khoảng 0,004 USD. Bước còn lại (gộp địa điểm trùng) đang chọn model dự phòng phù hợp.
- Chưa chạy lại AI viết nội dung cho tour thật (chưa mở lượt chạy trả phí), nên phần viết lại nội dung vẫn chờ.

**3. Trang nhà cung cấp AI trong admin (menu "AI providers", tab Providers)**

- Mỗi nhà cung cấp AI và dữ liệu có thêm số lượt gọi, tỉ lệ lỗi và thời gian trả lời trong 24 giờ / 7 ngày, công tắc
  bật/tắt từng nhà cung cấp (tắt thì hệ thống không gửi gì tới nhà cung cấp đó), và thêm các dòng AI của CRM và bản đồ.
  Đã kiểm trên bản đang chạy 01/11, máy tính và điện thoại; thử tắt rồi bật lại một nhà cung cấp: khi tắt, không có lượt
  gọi nào được gửi đi.
- Các màn hình duyệt nội dung do AI viết trong admin có dòng nhắc "AI có thể sai, kiểm lại giá, ngày, visa và thông tin an
  toàn trước khi gửi hoặc đăng" (đã đưa lên Dev 01/11).

Ảnh: không đính (ảnh trang nhà cung cấp có thông tin tài khoản nội bộ).

**Bằng chứng (nội bộ):**

| Câu | Bằng chứng |
|---|---|
| Định vị (toàn bộ mục 1) | bảng bằng chứng nháp S262 §7 (dòng 439–447) |
| Chặn từ 29/10, AWS hẹn 05–06/11 | trang báo cáo S263 (`report/data.json` vendor + incidents_vi) |
| Model dự phòng mỗi bước, trần theo tháng, dừng ở trần | Linear AA-1026 (mig 327 writers → OpenAI API, trần 10 USD/tháng, 80 %, hard stop; mig 331/332/333 dự phòng acc2 cho judge/validate) |
| 19/20 bước, ≈ 0,004 USD | AA-1026: smoke #1 11/12 ≈ 0,0017 USD, smoke #2 19/20 ≈ 0,0025 USD (cộng ≈ 0,004); a3_place_dedupe còn mở |
| Trang Providers: 24 h/7 d, lỗi %, p50/p95, công tắc, dòng CRM AI + Mapbox; desktop + mobile; tắt Jev → "nothing was sent" | Linear AA-1025 comment 01/11 17:57Z; ảnh `.tmp-session/S263/evidence-private/` (có account ID, không đăng) |
| Thông báo AI ở màn hình duyệt CIS | CIS #1235 (8a2def27), deploy sau đó (9fcd1b8f); AA-1033 In Review |

**Chưa kiểm:** viết lại nội dung tour thật bằng đường dự phòng (không chạy trả phí); phần viết cho đối tác (Content studio)
có chạy được qua dự phòng hay không — không kiểm, nên bản đăng không nói; thông báo AI trong admin CIS chưa có ảnh; nút
Switch/Re-queue còn bấm được với vai trò chỉ xem (việc nhỏ, không đưa). Nếu tech lead thấy mục 2–3 là việc kỹ thuật, bỏ cả
hai và chỉ đăng mục 1 (memory `jira-no-tech-decisions`); mục 2 viết theo kết quả cho chủ doanh nghiệp, không nói kiến trúc.

---

## 8. PR-20 — Báo cáo nền tảng kỳ 3 (27/10–02/11/2026)

**Vì sao issue này:** báo cáo tuần; kỳ 2 là PR-28 (26/10), đã đủ một tuần. Gồm cả S263. Trang báo cáo chi tiết là tài liệu
buổi họp 14:00 ngày 02/11.

**Nội dung (sẵn để đăng):**

@thule Báo cáo nền tảng kỳ 3 (27/10–02/11/2026). Mọi số đo trên Dev với dữ liệu thử, còn thay đổi. Chi tiết ở comment trên
từng epic.

Tài liệu cho buổi họp 14:00 ngày 02/11 (mức hoàn thành từng app, tính năng, chi phí theo tháng, nhà cung cấp AWS, việc cần
chị quyết): (link trang báo cáo riêng, chỉ trong comment Jira)

| App | Mức hoàn thành (ước tính) | Đã xong trong kỳ | Tiếp theo |
|---|---|---|---|
| CIS (PR-22) | 78 % | Thẻ địa điểm đạt ngưỡng chất lượng (dữ kiện sai 2,0 %); ảnh bìa tour cho đại lý 302 → 444/892 tour; định vị địa điểm: ≈ 88 % pin khách thấy đặt đúng chỗ, ≈ 80 % trên toàn dữ liệu cũ, pin không chắc chắn đã ẩn; trang Cost Operations và Docs; AI có model dự phòng khi tài khoản AI chính bị chặn; trang nhà cung cấp AI có lỗi, độ trễ, công tắc bật/tắt | Bật lại AI viết nội dung khi tài khoản AI chính có lại hoặc khi được duyệt chạy qua đường dự phòng |
| Portal (PR-23) | 80 % | Portal chạy trên máy chủ AA, một bản, đăng nhập 2 lớp; Marketplace có bộ lọc và ảnh bìa; trang Facts của đối tác; trần chi phí AI theo đối tác | Điều khoản AI cho đối tác (chờ chị chọn A/B/C) |
| TripPlanner (PR-24) | 80 % | Video giới thiệu EN + VI; trang chủ và trang tour 1,5–1,6 giây trên điện thoại, trang điểm đến dưới 2,5 giây; chặn bot và giới hạn AI cho mỗi khách; trang Dev không lập chỉ mục; thông báo AI trên trang tour và mục "Use of AI" trong điều khoản | — |
| Booking (PR-25) | 78 % | Phủ các màn hình theo Figma; danh sách trip plan nhanh khoảng 4 lần; tải chứng từ; lưới khách sạn; đề xuất báo khi CIS có nội dung mới hơn | Chờ chị chốt thuế, % đặt cọc, cách đánh dấu đã thanh toán |
| CRM (PR-26) | 84 % | Hoá đơn, thanh toán, hoàn tiền, nhắc nợ; ký điện tử; xuất và xoá dữ liệu khách; lịch; trang riêng cho từng khách (dùng được khi mất mạng); nhập dữ liệu; báo cáo; cảnh báo sự cố từ AA; hoa hồng; huỷ chuyến một thao tác; bàn giao cho đội điều hành AA; cho AA hỗ trợ xem dữ liệu; trợ lý AI (chế độ thử); AA tạo đại lý và mời chủ đại lý từ admin; nhắn tin WhatsApp và SMS bằng tài khoản của đại lý (đã thử bằng tài khoản thử) | Tự động hoá việc theo chuyến; màn hình cho nhân viên AA (hỗ trợ, điều hành); Microsoft 365 |
| Nền tảng (PR-27) | 64 % | Gia cố bảo mật không tốn phí; số cảnh báo tự động giảm 101 → 27 để bớt email và chi phí; hướng dẫn vào và chạy từng app (EN + VI) | Báo cáo chi phí AWS chính thức tháng 8–10 (từ 03/11) |

**Nghiệm thu (UAT):** đã có bộ 27 kịch bản nghiệm thu cho các app. Chạy thử 31/10 trên Dev ở chế độ chỉ đọc: 23 kịch bản,
đạt cả 23 sau khi sửa 4 kịch bản viết sai (lỗi ở kịch bản, không phải ở sản phẩm); 4 kịch bản có ghi dữ liệu chưa chạy.
Vòng quay chính thức làm khi giao diện ổn định và AI viết nội dung có lại.

**Chi phí:** số chi phí Dev theo tháng và theo app nằm trong trang báo cáo ở trên (số Dev, chưa ổn định). Báo cáo chính
thức tháng 8–10 có từ 03/11, sẽ có trong kỳ 4.

**Rủi ro:** tài khoản AI chính vẫn bị AWS chặn từ 29/10 (AWS hẹn xử lý khoảng 05–06/11). Các bước kiểm tra và chấm điểm đã
có model dự phòng; AI viết nội dung cho tour chưa chạy lại. Các phần không dùng AI vẫn chạy bình thường. Định vị địa điểm
chưa đạt mục tiêu 90 %. Hệ thống vẫn ở môi trường thử nghiệm với dữ liệu thử; chưa có ngày go-live.

**Cần chị quyết** (chi tiết trong trang báo cáo): điều khoản AI A/B/C (PR-23) và việc nhờ luật sư; chọn đại lý AWS và
chuyển thanh toán; con số cho gói dịch vụ và hạng đại lý; thuế, % đặt cọc cho Booking.

**Ảnh:** không (ảnh ở comment từng epic).

**Bằng chứng (nội bộ):**

| Câu | Bằng chứng |
|---|---|
| Link trang báo cáo, nội dung (%, chi phí, nhà cung cấp, cần quyết) | checklist S263 ("Báo cáo cho chị Thư … % theo app: CIS 78, Content studio 80, TP 80, Booking 78, CRM 84, Nền tảng 64"; v2 chi phí; v3 Phân quyền; chia sẻ cho tổ chức); `.tmp-session/S263/report/data.json` |
| Các dòng CIS/Portal/TP/Booking/CRM của S262 | bảng bằng chứng nháp S262 §6 (dòng 392–404) |
| CIS: dự phòng AI, trang nhà cung cấp | nháp §7 trên (AA-1025, AA-1026) |
| TP: thông báo AI + "Use of AI" | nháp §5 trên (Playwright 02/11) |
| CRM: tạo đại lý, mời chủ đại lý, WhatsApp/SMS | nháp §3 trên (AA-1031, AA-958, checklist S263) |
| Nền tảng: gia cố $0, 101 → 27 cảnh báo, runbook 7 trang EN + VI | AA-1022 Done; checklist S263 (Infra #586 apply: 27 alarm OK); root #435 |
| AWS hẹn 05–06/11 | `report/data.json` vendor.summary_vi |
| Cần chị quyết | `report/data.json` period.owner_asks_vi |
| UAT | nháp S262 §6 |

**Chưa kiểm:** "Mức hoàn thành" là ước tính trong trang báo cáo (cách tính ở đó), chốt khoảng 17:15 01/11, chưa tính phần
cuối S263 (AA-958/1031 Done sau giờ đó đã nằm trong CRM 84 % hay chưa — xem `percent_method_vi`); nếu tech lead không muốn
đưa % lên Jira thì bỏ cột này. Dòng Nền tảng tuỳ tech lead bỏ (việc kỹ thuật). Trang báo cáo có mục bảo mật/nhà cung cấp
nội bộ hơn mức Jira thường đăng — đó là tài liệu riêng cho buổi họp; Jira chỉ đưa link.

---

## Không soạn (và vì sao)

- **PR-27:** gia cố bảo mật, giảm cảnh báo, mail phiên quản trị, cổng AI (kiểm tra tuyến, luật chọn model, migration),
  quy trình ship nhanh hơn, tài liệu kiến trúc 6 repo, phát hiện phiên quản trị từ hệ thống của đại lý AWS — việc kỹ thuật
  của tech lead (memory `jira-no-tech-decisions`); phần nào chủ doanh nghiệp cần đã nằm trong trang báo cáo.
- **CRM tự động hoá (AA-959):** đã merge, chưa kiểm live → báo khi đã thử.
- **Giao diện admin CIS dùng chung bộ giao diện (AA-1006):** việc nội bộ cho nhân viên, lỗi tìm thấy đã sửa nhưng chưa chụp
  lại → không đưa.
- **Gói dịch vụ / chuỗi giá / hạng đại lý (AA-1028…1030):** chưa ship; câu hỏi số liệu đã ở mục "Cần chị quyết" của PR-20.
- **KAN/CON:** không có việc mới liên quan.

## Kết quả đăng

Đăng 02/11/2026 (~06:50 +07) bởi phiên điều phối sau khi tech lead duyệt ("duyệt hết, bỏ dòng Nền tảng"). Subagent bị hook
chặn ghi Jira nên điều phối tự đăng. 25 ảnh tải một lượt, nhúng theo đúng thứ tự.

| # | Issue | Comment id | Ảnh |
|---|---|---|---|
| 1 | PR-26 (A) | 10596 | 7 |
| 2 | PR-26 (B) | 10597 | 10 |
| 3 | PR-26 (C) | 10598 | 2 |
| 4 | PR-25 | 10599 | 2 |
| 5 | PR-24 | 10600 | 3 |
| 6 | PR-23 | 10601 | 1 |
| 7 | PR-22 | 10602 | 0 |
| 8 | PR-20 | 10603 | 0 |

Khác bản duyệt (chỉ sửa cho đúng sự thật, không thêm nội dung): PR-20 bỏ dòng Nền tảng (tech lead); PR-26 B ghi rõ phí huỷ
lần thử (118,91 USD/75 %/13 ngày) khác ảnh chụp lại (79,27 USD/50 %/21 ngày); PR-26 B câu che thông tin cá nhân nói đúng
mức "những thông tin CRM biết và phát hiện được"; PR-26 C hộp Create agency không có email chủ (mời ở bước Invite first
owner); PR-22 bỏ câu nội bộ về ảnh, bước gộp địa điểm trùng "đã có model dự phòng đạt bài kiểm 02/11".
