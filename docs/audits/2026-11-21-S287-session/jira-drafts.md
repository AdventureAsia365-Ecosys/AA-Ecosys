# S287 — Jira drafts

Status: **chưa đăng — chờ duyệt.** Drafts only. Nothing posted, no status changed, no Jira issue created. The tech
lead approves (or edits), then the orchestrator posts.

Read before drafting (21/11 ~17:30 +07):

- Open issues `project in (PR, KAN, CON) AND statusCategory != Done AND updated >= -10d`: PR-20, PR-22..PR-27 (app
  epics), PR-29 "Optional activity add in" and PR-30 "Khach san" (both raised by the business owner 18/11, Backlog,
  planned in the master plan for S289), KAN-94 (AA staff weekly report, not a target). No newer comment than the S286
  posts on any target epic.
- Newest comments read on each epic: PR-22 10681 (20/11), PR-23 10683 (20/11), PR-24 10680 (19/11), PR-25 10682 (20/11),
  PR-26 10678 (19/11), PR-27 10663 (16/11), PR-20 10661 (kỳ 5, 15/11 20:01). None covers: agency services on the trip /
  deadline task / invoice group (PR-26 10678 only covered "agency lines limited to 4 kinds"), custom staff roles, the
  Roles & permissions page, the Compliance readiness page, or the HTML clean-up before publishing (PR-23 10683 was the
  AI disclosure line, a different change).
- Linear read: AA-1147 (Done 07:02Z), AA-1155 (In Review; S287 comment 04:58Z + live files), AA-1167 (Done 08:32Z),
  AA-1170 (comment 08:33Z), AA-788 (In Progress, not shipped), AA-1171 (In Review, no comment, not merged).

When posting: `contentFormat: html`; `@thule` as the mention node
`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`; markdown tables →
HTML tables, never inside a list item (PR-24 400 on 19/11); screenshots uploaded and embedded in the listed order.
Screenshot paths are relative to `docs/audits/2026-11-21-S287-session/`.

Target choice (app → epic, skill aa-jira-update): CRM → PR-26; agency content published to WordPress → PR-23 (follows
the 20/11 AI disclosure post there); staff roles across CIS + Booking and the Compliance page → PR-27 (Nền tảng: đăng
nhập, bảo mật, dùng chung các app); weekly report kỳ 6 → comment on PR-20 (same form as kỳ 5, comment 10661).

---

## J1 — PR-26 (CRM cho đại lý): agency services follow the trip, from the accepted proposal to the invoice

Why: shipped 21/11 (Partner #374 + #375, crm-083/084), live check 5/5 PASS on the synthetic agency Sen Vàng with 10
screenshots; the last PR-26 comment (19/11) only said agency lines are limited to 4 kinds. This is the next visible
step of the same flow.

Text:

@thule Cập nhật CRM đại lý ngày 21/11 (Dev, đại lý thử Sen Vàng, dữ liệu thử): dịch vụ đại lý tự lo (vé máy bay, visa, bảo hiểm, phí) giờ đi theo chuyến từ báo giá tới hoá đơn.

1. **Sau khi khách chấp nhận báo giá:** tab Bookings của chuyến tự có một dòng cho mỗi dịch vụ đại lý tự lo, ghi "Handled by the agency", trạng thái đang lên kế hoạch, ẩn với khách, tiền do đại lý thu. Các dòng này không gửi sang Booking của AA (kiểm bằng test tự động). Đã thử 21/11: khách chấp nhận qua link một báo giá có vé máy bay và e-visa, tab Bookings có đúng 2 dòng.
2. **Hạn chót trên từng dòng:** nút "Deadline and supplier" để đặt hạn xuất vé hoặc nộp visa, và xoá hạn khi cần. Đã thử 21/11: đặt hạn 23/11 cho vé máy bay, xoá, rồi đặt lại; mỗi lần lưu đều đúng.
3. **Việc nhắc tự động:** khi hạn chót còn trong 3 ngày, CRM tự mở một việc khẩn "Issue the flight ticket before its time limit" cho người phụ trách chuyến, hạn đúng ngày hạn chót. Đã thử 21/11: việc xuất hiện ở lượt kiểm hằng giờ lúc 14:00; dòng visa không đặt hạn nên không có việc.
4. **Trang báo giá của khách và hoá đơn:** có mục "Services provided by <tên đại lý>" liệt kê từng dịch vụ kèm giá, và câu miễn trừ: các dịch vụ này do đại lý sắp xếp, cung cấp và chịu trách nhiệm; điều kiện vé, visa, bảo hiểm theo hãng bay, cơ quan cấp và công ty bảo hiểm. Trên hoá đơn đặt cọc các dịch vụ này chỉ được liệt kê, không cộng vào số tiền cọc. Đã thử 21/11 trên trang báo giá và một hoá đơn đặt cọc bản nháp (không phát hành, không thu tiền).
5. **Cài đặt:** số ngày nhắc trước (mặc định 3) và câu miễn trừ (tiếng Anh và tiếng Việt) xem ở CIS › Platform › Settings, tab CRM. Lần thử hiện câu tiếng Anh; bản tiếng Việt có trong cài đặt, chưa xem trên trang của một đại lý dùng tiếng Việt.

Lưu ý: trên trang báo giá của khách, thẻ vé máy bay và visa đang ghi "Included" trong khi mục dịch vụ của đại lý ngay bên dưới ghi giá (270 và 50 USD). Tổng 320 USD vẫn đúng; chữ trên thẻ sẽ được chỉnh cho khỏi hiểu nhầm.

Ảnh theo thứ tự: (1) tab Bookings với 2 dòng đại lý tự lo, (2) việc nhắc xuất vé trên trang chuyến, (3) trang báo giá của khách với mục dịch vụ của đại lý, (4) hoá đơn đặt cọc bản nháp.

(End of comment text.)

Screenshots (upload names without diacritics):
1. `live/aa1147/01a-bookings-two-agency-lines-light.png` → `crm-bookings-dong-dai-ly.png`
2. `live/aa1147/03-trip-task-agency-flight-due-light.png` → `crm-viec-nhac-xuat-ve.png`
3. `live/aa1147/04a-client-page-agency-services-light.png` → `trang-bao-gia-dich-vu-dai-ly.png`
4. `live/aa1147/04c-invoice-printable-agency-services-light.png` → `hoa-don-dat-coc-nhap.png`

Image notes: no issue ID or e-mail on any of the four. Image 3 shows the test terms label "(e2e-mwbxw5ae)" near the
bottom; image 4 shows the invented prospect "E2E v11470zbai Agency Extras" and "E2E test agency" in the bank-transfer
line. Both are synthetic test names. If the tech lead prefers, drop image 4 and change the caption to (1)–(3).
Not attached: `05a..05c` CIS settings (text says it), `04b`/`01b` dark duplicates, `02` (the deadline state also shows in 3).

| Claim | Evidence |
|---|---|
| Accept → exactly 2 planning agency lines, "Handled by the agency", hidden from travellers, collect by the agency | `live/aa1147/evidence.md` §1 (06:27Z+, lines API 200, panel text); image 1 |
| Not sent to Booking | CI test `test_no_agency_line_is_ever_sent_to_booking` (Linear AA-1147 Done comment); stated as "kiểm bằng test tự động" |
| Deadline set 23/11 → clear → set again, each saved | `evidence.md` §2 table (PATCH 200 ×3, GET read-back) |
| Urgent task at the hourly tick 07:00 UTC (= 14:00 +07), due = line deadline, owner = trip owner; none for visa | `evidence.md` §3 (task created 07:00:20Z, priority urgent); image 2 |
| Client page + printable deposit invoice: "Services provided by …", priced rows, disclaimer; not summed into the deposit | `evidence.md` §4 (invoice lines `included`, total 96.00 = the one charge); images 3, 4 |
| Within 3 days → `crm.agency_lines.due_lead_days` = 3; disclaimer en + vi on CIS Settings › CRM | `evidence.md` §5; `05a`–`05c` |
| Draft invoice not issued, nothing paid, 0 USD | `evidence.md` header + "Left on Dev" |
| "Included" vs priced group | `evidence.md` §4 observation; Linear AA-1147 "Minor UX note" |

Not claimed on purpose: the Vietnamese disclaimer on a Vietnamese-language agency page (not run); per-agency override
of the two settings (exists, read only in the run); supplier choice on an agency line (the button is "Deadline and
supplier"; only the deadline was exercised). The "sẽ được chỉnh" line commits to a small follow-up that has no issue
yet (Linear calls it "candidate for a small follow-up"): keep it, or cut the "Lưu ý" paragraph and image 3 if the tech
lead does not want to promise it.

---

## J2 — PR-23 (Portal tenant / Content studio): AI posts are cleaned of unsafe HTML before they reach the agency's site

Why: shipped 21/11 (CIS #1634 `350353eb`, migration 467), run live end to end on the test WordPress site through the CIS
publish route; it changes what is published on every agency's website. PR-23's last comment (20/11) was the AI
disclosure line, not this.

Text:

@thule Bài viết AI đăng lên kênh của đại lý giờ được làm sạch mã HTML trước khi đăng (21/11, Dev):

- Trước khi gửi bài lên WordPress, hệ thống chỉ giữ định dạng thường (tiêu đề, đoạn văn, chữ đậm, liên kết, danh sách) và bỏ mọi mã có thể chạy trên website của đại lý: đoạn mã script, khung nhúng (iframe), mã gắn vào thao tác bấm hay rê chuột, liên kết dạng "javascript:". Chữ hiển thị vẫn giữ nguyên.
- Mục đích: nếu nội dung AI viết hoặc phần đại lý tự sửa có lẫn mã lạ, website của đại lý và người đọc không bị ảnh hưởng. Đây là một trong các biện pháp an toàn cho ứng dụng dùng AI theo khuyến nghị OWASP.
- Đã thử 21/11 trên site WordPress thử: đăng một bài có cài sẵn script, iframe, mã bấm chuột và 2 liên kết "javascript:" xen với định dạng thường. Đọc lại bài trên site: không còn mã nào trong số đó; tiêu đề, chữ đậm, liên kết thường và danh sách còn nguyên. Bản xuất từ hệ thống trước khi đăng đã sạch và giống hệt bài trên WordPress, nghĩa là hệ thống tự làm sạch, không dựa vào bộ lọc của WordPress. Gỡ bài xong, bài viết của đại lý thử trở lại nội dung ban đầu và về trạng thái sẵn sàng đăng.
- Bản xuất HTML và bản xuất văn bản dùng cùng bộ lọc (đã thử 21/11). Bài Facebook dùng bản văn bản đã lọc; lần này chưa đăng thử lên Facebook. Tiêu đề và mô tả SEO trên WordPress cũng qua bộ lọc, chưa thử với mã lạ.
- Không tốn tiền AI: dùng một bài đã viết sẵn của đại lý thử.

(End of comment text. No image by default — see below.)

Screenshot option: `live/aa1167/aa1167-01-wordpress-post-sanitized.png` → `wordpress-bai-da-lam-sach.png` shows the
cleaned test block on the test WordPress site, outlined in red. Every test line carries a marker such as
"(aa1167-h2)", which is an internal issue number in lowercase (S286 dropped images that showed issue IDs). Default: post
without the image. If the tech lead wants it, add the line "Ảnh: (1) khối chữ thử trên site WordPress thử sau khi đăng
(khoanh đỏ); chữ trong ngoặc là nhãn của bài thử."

| Claim | Evidence |
|---|---|
| Allow-list keeps h2/h3, strong, links, lists; drops script (with content), iframe (with src), on* attributes, `javascript:` hrefs; text kept | `live/aa1167/evidence.md` Results 2–4 + Notes; HTML excerpt |
| Published through the CIS route to the test WP site; public read-back clean; live page runs nothing | Results 1, 2, 4 (POST 200, WP post 4; `window.aa1167` undefined) |
| CIS cleaned it, not WordPress (export before publish = `content.rendered`) | "Who removed the markup: CIS, not WordPress" |
| Taken down; original text back; piece ready | Results 6, 8 (DELETE 200 → 401; same sha256; publish log 0 published) |
| HTML + text export use the same filter | Results 7 + fragment / document / plain-text exports |
| Facebook / WP title-meta not run | `evidence.md` Notes "Not checked in this run"; Linear AA-1167 "Not tested" |
| OWASP framing | AA-1167 scope; root #930 AI use register rows LLM01, LLM05 |
| 0 USD for this check | `evidence.md` header ("Cost: 0 USD. There was no model call.") |

Left out on purpose: the prompt-injection trap run (9 invented traps, 8/9 held in both fence modes, 0.81 USD, fence left
off, the T9 case moved to a new issue). It is a quality measure with an open weakness and an internal setting decision;
skill rule 7. If the tech lead wants one line: "Đã thử 9 tình huống dữ liệu đầu vào có cài câu lệnh lạ cho AI viết
bài: 8/9 AI không làm theo; tình huống còn lại (bài blog) đang được sửa."

---

## J3 — PR-27 (Nền tảng): custom staff roles in CIS and Booking; Compliance readiness page

Why: both shipped and checked live 21/11. Custom roles: CIS #1624 + #1627/#1628 (role editor, presets as data), Booking
#294; live read-only pass 2/2 and maker pass with the test account holding the two custom roles. Compliance: CIS #1633
(+ #1629, #1631, root #929, Infra #963), daily collector running, page checked live with 6 screenshots. Both are
cross-app / platform features visible to the business owner (who may hold roles, and who answers partners' security
questions). Not an infrastructure decision: the comment states what the pages show, no architecture.

Text:

@thule Cập nhật nền tảng ngày 21/11 (Dev):

1. **Vai trò nhân viên tự tạo cho CIS và Booking:**
   - Ngoài các vai trò có sẵn, chủ nền tảng tạo được vai trò riêng: sao chép một vai trò có sẵn rồi chọn quyền. Ở Booking, các quyền duyệt (duyệt giá, kích hoạt nhà cung cấp, công bố hợp đồng, dừng bán, chi trả) luôn ở lại các vai trò có sẵn; vai trò tự tạo không nhận được.
   - Trang mới **CIS › Platform › Roles & permissions** (chỉ đọc): mọi vai trò của 4 app (CIS, Booking, CRM, TripPlanner) và quyền của từng vai trò, kèm bảng tick quyền theo từng vai trò CIS. Booking có trang **Roles**: vai trò tự tạo và vai trò có sẵn; người không phải chủ nền tảng chỉ xem, có dòng ghi chỉ chủ nền tảng (CIS › Platform › Staff) mới tạo hoặc sửa vai trò.
   - Hai vai trò tự tạo đang dùng trên Dev: CIS "Content" (18 quyền, dựa trên Content Lead, xem được thông tin đại lý, không sửa cài đặt nội dung) và Booking "Product, ops & accounting" (24 quyền, dựa trên Product & operations, không có quyền duyệt).
   - Đã thử 21/11 bằng một tài khoản thử mang 2 vai trò này. Ở CIS: đăng nhập vào thẳng My work, mở được danh sách đại lý; trang Staff và SEO Intelligence không mở được (quay về My work). Ở Booking: xem được nhà cung cấp, hoá đơn nhà cung cấp, hoá đơn đại lý; 13 thao tác duyệt và chi (duyệt quy tắc giá, tỷ giá, chính sách huỷ, chiết khấu đại lý, bảng giá đại lý, điều chỉnh giá B2B, allotment, dừng bán, chi trả, sửa hợp đồng, kích hoạt nhà cung cấp…) đều bị từ chối.
   - Đã thử 21/11 bằng tài khoản chủ nền tảng trên trang CIS › Platform › Staff: tạo một vai trò mới rồi ngừng dùng nó, sửa tên một mẫu phân quyền (preset) rồi trả lại tên cũ; nhật ký ghi lại trước và sau mỗi thay đổi. Chưa làm: đánh dấu chủ doanh nghiệp trên trang Staff.
2. **Trang Compliance readiness (CIS › Platform › Compliance readiness):**
   - Đo mức sẵn sàng theo 6 bộ chuẩn: ISO/IEC 27001, SOC 2, ISO/IEC 42001 (quản lý hệ thống AI), OWASP Top 10, OWASP Top 10 cho ứng dụng LLM, và nghĩa vụ của bên triển khai trong Đạo luật AI của EU. Trang ghi rõ: điểm sẵn sàng trên môi trường Dev, **không phải chứng nhận**.
   - 48 biện pháp kiểm soát của AA gắn với 253 yêu cầu của 6 bộ chuẩn. Mỗi ngày hệ thống tự thu bằng chứng (ví dụ kết quả quét lỗ hổng, các kiểm tra tự động định kỳ); chỉ bằng chứng còn hạn và đạt mới được tính.
   - Số đo 21/11 lúc 15:29: 8 biện pháp đạt, 1 chưa đạt (1 trong 39 kiểm tra tự động định kỳ chưa xanh), 39 chưa có bằng chứng vì là việc làm tay (chính sách, quy trình, rà soát) chưa nộp bằng chứng. Vì vậy điểm hiện thấp hơn bản tự đánh giá:

| Bộ chuẩn | Số yêu cầu | Điểm đã có bằng chứng (chặt) | Tính cả phần đạt một phần | Bản tự đánh giá |
|---|---|---|---|---|
| ISO/IEC 27001:2022 | 123 | 2,4 % | 9,3 % | 45,8 % |
| SOC 2 | 33 | 0 % | 16,7 % | 44,0 % |
| ISO/IEC 42001:2023 | 70 | 1,4 % | 5,0 % | 46,9 % |
| OWASP Top 10 (2021) | 10 | 0 % | 20,0 % | 64,8 % |
| OWASP Top 10 cho LLM (2025) | 10 | 0 % | 0 % | 66,7 % |
| Đạo luật AI của EU (bên triển khai) | 7 | 0 % | 0 % | — |

   Điểm sẽ tăng khi các việc làm tay có bằng chứng.
   - Đã kiểm 21/11 bằng tài khoản quản trị thử (chỉ đọc): trang tổng quan, danh sách 48 biện pháp, chi tiết một biện pháp kèm các kiểm tra và lịch sử; trên máy tính và điện thoại, nền sáng và tối, không lỗi.
   - Đã thử bằng tài khoản chủ nền tảng: rút thời hạn của bằng chứng còn 1 giờ thì cả 10 bằng chứng chuyển sang hết hạn, số biện pháp đạt từ 8 về 0 và mọi bộ chuẩn về 0 %; sau đó đặt lại 72 giờ. Nút "Refresh evidence" có chạy nhưng chưa báo kết quả trên màn hình, sẽ bổ sung.

Ảnh theo thứ tự: (1) trang Roles & permissions trong CIS, (2) trang Roles trong Booking, (3) trang Compliance readiness.

(End of comment text.)

Posting note: the table must be a top-level HTML table between the item 2 list and the "Điểm sẽ tăng…" paragraph (not
inside the list item), as in PR-25 10682. Split item 2 into: list (3 bullets) → table → paragraph → list (1 bullet).

Screenshots (upload names without diacritics):
1. `live/aa1155/cis-platform-roles-1440-light.png` → `cis-roles-permissions.png` (1440×4479, full page; fine to crop
   to the top ~1,300 px: CIS roles + the start of the matrix)
2. `live/aa1155/booking-roles-1440-light.png` → `booking-roles.png`
3. `live/aa1170/aa1170-01-overview-1440-light.png` → `compliance-readiness.png`

No issue ID, e-mail or account ID on these (page scans in `cis-readonly.json` `page.forbidden` and aa1170 Result 9; the
account chip is masked). Not attached: `booking-maker-suppliers-1440-light.png`, `cis-maker-my-work-1440-light.png`
(test account views, not needed), the 390 / dark duplicates, the controls drawer shots (control ids `AAC-…` would need
explaining).

| Claim | Evidence |
|---|---|
| Custom role = copy of a built-in + chosen capabilities; Booking approvals stay with built-in roles | Booking `/roles` page text (image 2); `booking-readonly.json` (0 approve-class, `assignable` flags); AA-1155 S287 comment |
| Roles & permissions page: 4 apps, CIS matrix, read-only | `live/aa1155/evidence.md` R5.4; image 1 |
| Booking Roles: non-owner line, no New / Edit / Archive | `evidence.md` R4.2 |
| CIS "Content" 18 caps, based on content_lead, has tenant.read, no content.settings.write | `cis-readonly.json` `roles_api.content_role`; `cis-maker.json` (18, `has_tenant_read` true, `has_content_settings_write` false) |
| Booking "Product, ops & accounting" 24 caps, no approvals | `booking-readonly.json`; `booking-maker.json` `staff_me` (24 = seed) |
| Maker: CIS lands on My work; /admin/tenants opens; Staff + SEO Intelligence go back to My work | `cis-maker.json` `pages_landed` |
| Maker: Booking reads 200; 13 approve / pay / contract / activate writes → 403 forbidden | `booking-maker.json` `reads`, `approve_probes` (13 × 403) |
| Owner created + archived a custom role, renamed a preset and restored it; business-owner marker not set | tech lead's 12 screenshots in chat 21/11 (#4), staff audit before/after read by the agent; checklist S287 |
| Validity 1 h → 10 results STALE, met 8 → 0, frameworks 0 %; reset to 72 h; Refresh shows no feedback | tech lead's screenshots 4–5 (#3); setting `cis.compliance.validity_hours.root_daily` v2 = 72 approved |
| Compliance: 6 frameworks, 253 req, 48 controls, banner "not a certification" | `live/aa1170/evidence.md` Results 1, 8; image 3 |
| Daily collection, only fresh passing evidence counts | Results 3–4 (`root_daily`, 10 rows), page header text (image 3) |
| 8 met / 1 gap / 39 no evidence; 1 fail = 38/39 scheduled guards | Results 1, 5 + "One check needs attention" |
| Framework table (strict / weighted / reference) | "Evidenced % per framework" table (08:29 UTC = 15:29 +07), rounded to one decimal as on the page |
| Overview, controls, detail; 1440 / 390, light / dark, no errors | Results 5, 6, 7, 10; Notes "Console and network" |

Not claimed on purpose: a CIS content write refused by the role (the CIS write probe answered `e2e_read_only`, i.e.
refused because the test account is read-only, not because of the role); a non-administrator 403 on the compliance
routes.
---

## J4 — PR-20 báo cáo tuần kỳ 6 (17–23/11) — post Sunday 22/11

Why: weekly report (memory `platform-report-weekly`); kỳ 5 was comment 10661 on PR-20 (15/11 20:01), so kỳ 6 is due
Sunday 22/11. Drafted now from everything posted on the epics after kỳ 5 (16–20/11) plus J1–J3. Numbers were read
live on 21/11 18:14 +07 (see the evidence note below). If J1–J3 are not approved, drop their parts here.

Text:

@thule Báo cáo nền tảng kỳ 6 (17–23/11/2026). Mọi số đo trên Dev với dữ liệu thử, còn thay đổi; số đo ngày 21/11 lúc 18:15. Chi tiết và ảnh ở các comment trong tuần trên PR-22 đến PR-27 (gồm cả các cập nhật tối 16/11, sau kỳ 5).

**Tóm tắt tuần**

- Phân quyền nhân viên: trang "My work" ở CIS và Booking, 3 vai trò mẫu trên trang Staff, Booking tách người nhập và người duyệt, và nay có vai trò tự tạo cho CIS và Booking.
- CRM: dịch vụ đại lý tự lo đi theo chuyến từ báo giá tới việc nhắc hạn và hoá đơn; tạo đại lý có gói CRM bằng một lần bấm.
- Nội dung cho đại lý: bài AI ghi rõ có AI hỗ trợ (Đạo luật AI của EU, Điều 50) và được làm sạch mã HTML trước khi đăng; đại lý sửa câu chữ nhưng không đổi được dữ kiện tour của AA.
- TripPlanner chỉ mang thương hiệu đại lý; yêu cầu của khách tới đại lý theo cả 3 cách (CRM, e-mail, webhook).
- Chạy thử có trả phí trên bộ mẫu cố định cho 3 bộ viết (19/11): tour AA giảm mạnh lỗi so với nguồn; bài blog của đại lý còn thấp ở tỷ lệ đạt ngay lần đầu.

| App | Đã xong trong kỳ | Tiếp theo |
|---|---|---|
| CIS (PR-22) | Dữ liệu nhu cầu tìm kiếm đủ 5.877 địa điểm ở 6 thị trường; câu hỏi "People also ask" có ở 99,4 % tour đã xuất bản (839/844); tab Research trong SEO Intelligence (16/11). Ba báo cáo đối tác chạy thật; trang Reports có tình trạng của 65 báo cáo; nội dung của đại lý được che e-mail, số điện thoại, số thẻ, số giấy tờ, mã OTP trước khi gửi cho AI (17/11). Trang Docs mở cho mọi nhân viên: tìm toàn văn, mục lục, lịch sử thay đổi, góp ý (18/11). Admin dùng được trên điện thoại: 12/12 chỗ không còn kéo ngang (19/11). My work cho nhân viên nội dung (4/4 ô khớp số); sửa tour AA có phiên bản, cổng duyệt và khoá; 3 vai trò mẫu trên trang Staff; đăng nhập CIS xong vào thẳng Booking (20/11) | Trang soạn tour AA bằng tay, gắn nhà cung cấp, có xem trước và duyệt thay đổi; xem trang với quyền của vai trò thấp hơn (chỉ đọc, có ghi lại); nâng tỷ lệ bài blog đạt ngay lần đầu |
| App cho đại lý, Content studio (PR-23) | Đại lý sửa bài tour nhưng không đổi được số ngày, địa điểm, con số, phần bao gồm; mục Facts chỉ còn điều khoản đặt tour của đại lý; thông báo hết hạn mức AI kèm ngày làm mới; thẻ "Hoá đơn tháng này" (19/11). Dòng công khai "có AI hỗ trợ" cuối bài WordPress và Facebook, trong bản xuất văn bản và CSV (20/11). Làm sạch mã HTML trước khi đăng: đã thử trên site WordPress thử, chưa thử Facebook (21/11) | Bước kiểm bài mới: bài thiếu độ dài hoặc lệch phạm vi tour được sửa một lần thay vì bị giữ, chạy thử trên mẫu nhỏ trước khi bật; bộ viết bài blog không làm theo câu lệnh lạ nằm trong dữ kiện đầu vào |
| TripPlanner (PR-24) | Trang của đại lý chỉ mang thương hiệu đại lý (0 chỗ còn chữ "Adventure Asia" trên đại lý thử), mỗi đại lý có trang Điều khoản và Quyền riêng tư riêng, bỏ đăng nhập khách lẻ (17/11). Yêu cầu của khách tới đại lý qua CRM, e-mail, webhook (thử cả 3 cách); trợ lý lên lịch tạm dừng khi hết số phiên AI của gói (18/11). Trang "Trip planner" trong app của đại lý: địa chỉ, nơi nhận khách, màu và ngôn ngữ, số phiên AI tháng này, danh sách yêu cầu; đại lý được báo khi hết phiên AI (19/11) | Phần chữ trên planner theo ngôn ngữ đại lý chọn (hiện vẫn tiếng Anh); yêu cầu của khách vẫn được nhận khi đại lý chưa có CRM |
| Booking (PR-25) | Hoá đơn phần mềm hằng tháng có dòng giảm giá riêng cho từng gói (17/11) và dòng "Extra seats" khi vượt 3 chỗ CRM (18/11). Trang quản trị Booking có tiếng Việt, kiểm 10 trang (19/11). Kế toán chỉ xem, không duyệt hay chi; tách người nhập và người duyệt (hợp đồng, dừng bán, giá, allotment, khách sạn và dịch vụ); hợp đồng nhà cung cấp tính giá trẻ em, ngày dừng bán, phí huỷ theo bậc; dải My work trên trang chủ (20/11). Vai trò tự tạo "Product, ops & accounting": xem được, 13/13 thao tác duyệt và chi bị từ chối (21/11, chi tiết PR-27) | Quy tắc duyệt cho đội 3 người (chủ doanh nghiệp tự duyệt có đánh dấu, người chi khác người duyệt, kiểm soát thông tin chuyển khoản nhà cung cấp); tour đã bán tách thành từng dịch vụ đặt với nhà cung cấp; hoạt động tuỳ chọn (PR-29) và khách sạn qua DMC (PR-30) bắt đầu sau đó |
| CRM (PR-26) | Ô tìm kiếm chung Ctrl K, chiến dịch e-mail chỉ gửi cho khách đã đồng ý, xem trước tính năng mới, gói CRM 19 / 29 USD mỗi người dùng thử 14 ngày (16/11). Tạo đại lý có gói CRM bằng một lần bấm, tính năng khoá theo gói (17/11). Đại lý chỉ tự thêm 4 loại dịch vụ, tên dịch vụ AA không sửa được; báo hết ngân sách AI; nhật ký truy cập bằng câu thường, thêm tiếng Việt (19/11). Dịch vụ đại lý tự lo đi theo chuyến: dòng trong tab Bookings, hạn chót, việc nhắc tự động, mục riêng có câu miễn trừ trên trang báo giá và hoá đơn (21/11, thử 5/5 đạt) | Sửa chữ "Included" trên thẻ dịch vụ đại lý ở trang báo giá của khách; hoạt động tuỳ chọn theo ngày cho khách và đại lý |
| Nền tảng (PR-27) | Bảng giá gói chỉnh trong admin, các app đọc cùng bảng giá; trang Delivery; theo dõi lỗi đủ 5 phần còn thiếu (16/11). Vai trò nhân viên tự tạo cho CIS và Booking, trang Roles & permissions; trang Compliance readiness đo mức sẵn sàng theo 6 bộ chuẩn, ghi rõ không phải chứng nhận (21/11) | Chuyển người phụ trách nội dung và vận hành sang vai trò tự tạo; nộp bằng chứng cho các biện pháp làm tay để điểm sẵn sàng phản ánh đúng |

**Kế hoạch kỳ 5 (17–23/11), kết quả:**

| Việc | Kết quả |
|---|---|
| Đo xong độ chính xác của bước tự kiểm dữ kiện trong bài | Chưa xong, chuyển sang tuần tới |
| Chạy thử có trả phí trên bộ mẫu nhỏ cố định cho các bộ viết, có trần chi phí | Xong 19/11. Viết lại tour AA: số lỗi so với nguồn giảm từ 11,16 xuống 0,76 mỗi tour (25 tour), 56 % tour đạt ngay lần đầu. Tour cho đại lý: 8,3 xuống 7,7 lỗi mỗi tour (20 tour), không kém bản cũ nhưng sát ngưỡng. Bài blog cho đại lý: 4,67 xuống 3,50 lỗi mỗi bài, nhưng chỉ 8 % bài đạt ngay lần đầu, dưới mục tiêu 30 %; đây là việc chính tuần tới. Cả lượt đo trong trần chi phí đã đặt |
| Báo cáo: kiểm lần tự chạy đầu của hai báo cáo tuần (16/11); thêm báo cáo vận hành CRM | Ba báo cáo đối tác (tăng trưởng và rời bỏ, phễu tiếp nhận đại lý, sử dụng trợ lý AI trong CRM) chạy thật 17/11. Lần tự chạy 16/11 của hai báo cáo tuần: chưa kiểm |
| TripPlanner trên tên miền riêng: phần hạ tầng còn lại | Chưa làm trong kỳ, chuyển sang tuần tới |
| Diễn tập Content studio và TripPlanner khi đại lý hết ngân sách AI | Đã thử trên giao diện 18–19/11 (thông báo hết hạn mức, trợ lý tạm dừng, chuông báo cho đại lý), không tốn tiền AI. Chưa quay video |
| Từ 19/11, chuẩn bị bước kiểm bài mới (sửa một lần thay vì giữ) | Đang làm; chưa chạy thử trên mẫu nhỏ |
| CRM phần mua thêm | Tìm kiếm và chiến dịch e-mail đã có (16/11). Kết nối Microsoft 365 và lịch: chưa làm |

**Nội dung tour** (đo 21/11, so với kỳ 5 đo 15/11):

| Bước | Kỳ 5 | Kỳ 6 |
|---|---|---|
| Tour thô đang bán (14 nước) | 917 | 917 |
| Tour Master đang phục vụ | 844 (92 %); 48 tour có cưỡi voi tạm rút, chờ duyệt | 844 (92 %); 48 tour vẫn chờ duyệt |
| Có tuyến để gợi ý trên bản đồ | 650 | 650 |
| Tour đã viết lại cho đại lý thử | 38 tour, 138 bản, 10 đại lý thử | 56 tour, 164 bản, 10 đại lý thử |
| Bài viết cho đại lý thử | 469 bài; 11 bài từng đăng | 469 bài; 11 bài từng đăng |

**Chi phí AI và dữ liệu tìm kiếm** (theo sổ ghi từng lượt gọi; số Dev, chưa ổn định):

| Tháng | AI (USD) | DataForSEO (USD) |
|---|---|---|
| 10 | 269,34 | 19,30 |
| 11 (tới 21/11) | 49,31 | 11,19 |

- Số chi phí AI trên mọi trang quản trị đã đối chiếu lại với sổ ghi từng lượt gọi: 26/26 khớp (20/11).

**Kế hoạch tuần tới (24–30/11):**

| Việc | Cuối tuần muốn có |
|---|---|
| Chất lượng bài blog cho đại lý: tìm lý do bài không đạt ngay lần đầu, sửa, đo lại một lần có trần chi phí | Tỷ lệ đạt ngay lần đầu tiến về mục tiêu 30 % |
| Bước kiểm bài mới (bài ngắn, lệch phạm vi được sửa một lần thay vì giữ): chạy thử trên mẫu nhỏ | Có số đo trước/sau, rồi mới bật |
| Booking: quy tắc duyệt cho đội 3 người, kiểm soát thông tin chuyển khoản nhà cung cấp; tour đã bán tách thành từng dịch vụ đặt với nhà cung cấp | Nhân viên đặt dịch vụ nhà cung cấp theo từng thành phần của tour |
| CIS: trang soạn tour AA bằng tay gắn nhà cung cấp; xem trang với quyền thấp hơn | Nhân viên nội dung tự sửa tour có duyệt |
| Hoạt động tuỳ chọn (PR-29), khách sạn qua DMC (PR-30): bắt đầu ở Booking và CIS | Phần dữ liệu và trang nhập đầu tiên |

Mốc ngày: từ 28/11 xoá hẳn dữ liệu khách lẻ cũ trong Booking; đầu tháng 12 đối chiếu chi phí tháng 11 với hoá đơn.

**Rủi ro:**

- Tài khoản AWS dự kiến cho AI vẫn bị AWS chặn 7 model. AI viết nội dung chạy qua đường thay thế, không gián đoạn.
- Bài blog của đại lý: lỗi đã giảm nhưng mới 8 % bài đạt ngay lần đầu; đại lý vẫn nhận bài, bài chưa đạt được sửa hoặc giữ để kiểm.
- Giá thật còn ít: đo 21/11, 2/892 tour đủ điều kiện bán và 3 ngày khởi hành mở. Pilot thật cần giá nhà cung cấp và ngày khởi hành thật của các tour ưu tiên.
- Còn chưa thử thật: đăng bài đã làm sạch mã lên Facebook; VNPay bằng tài khoản thật của đại lý; PDF ký số với chứng thư thật.

(End of comment text.)

Images: none (as kỳ 5).

| Claim | Evidence |
|---|---|
| CIS 16–20/11 items | PR-22 comments 10664 (16/11), 10668 (17/11), 10671 (18/11), 10679 (19/11), 10681 (20/11) |
| Content studio items | PR-23 10675 (19/11), 10683 (20/11); J2 |
| TripPlanner items | PR-24 10667 (17/11), 10669 (18/11), 10680 (19/11) |
| Booking items | PR-25 10665 (17/11), 10670 (18/11), 10677 (19/11), 10682 (20/11); J3 (`booking-maker.json`) |
| CRM items | PR-26 10662 (16/11), 10666 (17/11), 10678 (19/11); J1 |
| Platform items | PR-27 10663 (16/11); J3 |
| Writer proofs 19/11 (S1 11,16 → 0,76 on 25, first pass 0,56; T2 8,3 → 7,7 on 20, near margin; T9 4,67 → 3,50, first pass 0,08 < 0,30; within caps) | `docs/sessions/2026-11-19-S285-…md` "AA-1051 (W5 proofs)"; reports in `docs/audits/2026-11-19-S285-session/aa1051/` |
| AI month to 20/11 = 46,75 USD; 26/26 reconciliation | `docs/sessions/2026-11-20-S286-…md` line 57 (AA-1127) |
| acc for AI still blocks 7 models | S287 checklist "Trạng thái đầu phiên" (21/11) |
| 28/11 Booking deletion; early-December reconciliation | kỳ 5 (10661) dates; Booking #200 waiting ≥ 28/11 (S287 checklist) |
| Next-week items | `docs/backlog/tracker/plan.json` slots S288–S290 (AA-1158, AA-1149, AA-1148, AA-1157, AA-1169, AA-1172, AA-788, AA-1151, AA-1153, AA-1160) |

Numbers read 21/11 11:14 UTC (18:14 +07) in the CIS container, read-only: `.tmp-session/S287/ops/pr20_costs.out`
(`shared.llm_call_log` November 151.158 calls 49,31 USD; `shared.dfs_call_log` November 396 calls 11,19 USD, October
19,30) and `pr20_funnel.out` (live_active_source 917, master active 844 / inactive 48 policy_hold, tours_with_route 650,
s09_t2 tours 56 / rows 164 / tenants 10, piece_totals 469, publish_totals pieces 11, trip_plans_sellable 2 / 892,
departures_open 3). Items written "chưa kiểm" / "chưa làm" were not checked or not done in the period.

---

## Left out on purpose

- **WAF rate limit on the CRM hosts (Infra #954/#956, alarm #961), image scanning and SBOM gate (CIS/Partner Node bumps,
  WordPress 7.1.5 on the test site, scan run green 8/8), repo history rewrite and size clean-up, branch protection,
  CodeQL, vulnerability triage and SEC-03**: infrastructure and engineering process, tech lead's call (memory
  `jira-no-tech-decisions`). The Compliance page in J3 is the only security item, as a page the business owner can open.
- **Alerts catalogue P0 (Platform › Alerts)**: shipped 21/11 evening (CIS #1636 deploy `1be86655`); ops-internal
  monitoring for the tech lead, not a product feature for the business owner. Not in Jira.
- **AA-788 new review step**: code in review, pilot not run; appears only as "đang làm" in the kỳ 6 plan table.
- **The 17 compliance-tracking decisions and the 10 alerting decisions**: tech lead's decisions, no draft.
- **Trap run cost and fence setting**: see J2 "Left out on purpose".

## Posted

Tech lead approved all four drafts on 21/11 (evening); PR-20 held for the Monday-morning session.

| Draft | Issue | Comment | Images |
|---|---|---|---|
| J1 | PR-26 | 10684 (21/11) | 4 inline |
| J2 | PR-23 | 10685 (21/11) | none |
| J3 | PR-27 | 10686 (21/11) | 3 inline |
| J4 | PR-20 | not posted yet: held for the Monday 23/11 morning session (tech lead) | none |
