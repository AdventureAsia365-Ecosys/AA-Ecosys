# S288 (23/11/2026) — Jira drafts, session close

Status: **POSTED 23/11 ~22:55 +07** after the tech lead's in-session approval ("kiểm xong hết đi, rồi có sửa gì thì đăng"), with the final live results of the E2E owner run folded in (`live/e2e-owner/evidence-final.md`). Nothing was
written to Jira, Linear or GitHub while preparing these drafts (read-only).

Sources read: `.tmp-session/S288-checklist.md`; Linear comments on AA-1149, AA-1157, AA-1158, AA-1172, AA-1174,
AA-1175, AA-1176; live evidence `docs/audits/2026-11-23-S288-session/live/*`; runbook
`docs/guides/business-owner-onboarding-and-pricing.vi.md`; artifact "Bắt đầu với hệ thống giá"; the latest Jira
comments on PR-20 (10687), PR-25 (10682), PR-27 (10686); PR-31 (created 23/11 12:46 by the business owner, description
still empty, 0 comments); open items `project in (PR, KAN, CON) AND statusCategory != Done` (52 issues, read
23/11 ~17:20 +07).

Live state re-read while drafting (23/11 ~17:20 +07): Booking `/booking/health/ready` = `bk-066`, `git_sha` 79a8b389
(= merge of Booking #307, AA-1175 code); Deploy Dev + Deploy Admin Dev green on 79a8b389. CIS #1647 (phone layout of
the matrix) merged 07:52 UTC, Deploy Admin Dev green on b8d040cb. CIS #1648/#1649 (AA-1176, E2E owner) still OPEN.

## Before posting (orchestrator)

1. **Artifact is current.** https://claude.ai/artifact/DaUxxoojMm4RzpswhdQB2J is at version 2 (bands shipped:
   1, 2, 3, 4, 5–7, 8–10, 11+) and shared with the whole organization. The PR-31 draft keeps the link; no update needed.
2. **Bands live screenshot (optional, makes the PR-25 #3 / PR-31 claim stronger).** No one opened Booking ›
   Pricing policy ("Group size bands") after the AA-1175 deploy. The read-only E2E Booking admin (A10a) can open it
   without writing. With a screenshot, replace "chưa mở thử trang Pricing policy trên màn hình" by "đã mở thử 23/11:
   trang hiện bậc 1, 2, 3, 4, 5–7, 8–10, 11+ kèm hướng dẫn" and attach it.
3. **Compliance counts.** The obligations counts (0 met / 31 not met, 6 partly / 29 not checked) are from verify
   round 2 at ~14:30 +07. The cis_db collector ran later (~16:10: retention_runs_recent pass, retention_live_enabled
   fail), which may move some retention items. Re-read `GET /api/admin/platform/compliance/obligations` before
   posting, or keep the "đo lúc 14:30" time stamp as written.
4. **Blur the synthetic supplier name in PR-25 images 1 and 2.** Both show "SYNTHETIC aa1158-mwsw2ml1 custom", an
   internal issue ID (skill rule 4, memory `no-issue-ids-in-ui`). Blur or crop the name in a copy before upload (or
   replace image 2 by a crop of the banner and badge only). E-mail and account chip are already masked.
5. Images: upload per the skill (uploadAttachmentToJiraIssue → curl → inline ids). Files are listed under each draft.

## Summary of targets

| Jira | Post? | Why |
|---|---|---|
| PR-25 Booking | **Yes** | Approval rules part 1, supplier booking per sold tour component + can-operate check, group-size bands shipped today (Dev) |
| PR-27 Platform | **Yes** | View as a lower role (CIS + Booking) and the Obligations tab on Compliance readiness are user-visible admin features shipped today. Follows the 21/11 comment (roles, Compliance readiness; it said Refresh "chưa báo kết quả… sẽ bổ sung", now done) |
| PR-31 Price system | **Yes (reply on her task)** | Her own task from today: what the system already does for her example, the band change, the short guide link |
| PR-22 CIS | No | Only shipped CIS items are the AI-writer fact guard (ships **off**, switching it on is the tech lead's call: technical, not user-visible) and a small Settings label fix. Nothing user-visible for the business owner |
| PR-23 Content studio | No | PR-20 kỳ 6 listed "bộ viết bài blog không làm theo câu lệnh lạ nằm trong dữ kiện đầu vào" as next for PR-23. The guard exists but is off, so no change reaches agencies yet. Post when the tech lead turns it on |
| PR-26 / PR-24 | No | Nothing shipped for CRM or TripPlanner users today (the CRM privacy-evidence endpoint only feeds the PR-27 page) |
| E2E owner admin (AA-1176) | No | Test identity for agent live checks: technical, tech lead's decision (memory `jira-no-tech-decisions`); PRs still open |

---

## 1. PR-25 — Booking

- **Issue:** PR-25 "Booking — Hệ thống đặt tour (trip case, báo giá, thanh toán)" (epic, In Progress).
- **Why:** PR-20 kỳ 6 listed "quy tắc duyệt cho đội 3 người" and "tour đã bán tách thành từng dịch vụ đặt với nhà cung
  cấp" as next for Booking; part 1 of the first and the second shipped today. Last PR-25 comment 10682 (20/11) covers
  accounting rights, maker/checker split, contract terms and My work: no overlap.
- **Where:** new comment on PR-25, `contentFormat: html`.

### Text (HTML, ready to post)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật Booking ngày 23/11 (Dev):</p>
<ol>
<li><p><strong>Quy tắc duyệt cho đội 3 người (phần 1):</strong></p>
<ul>
<li><p>Nhà cung cấp mới luôn ở trạng thái "Pending approval"; trang chi tiết ghi rõ cần người thứ hai kích hoạt trước khi thêm hợp đồng. Đã thử 23/11 bằng tài khoản thử vai trò "Product, ops &amp; accounting": tạo một nhà cung cấp giả lập → chờ duyệt, trang không có nút kích hoạt cho người này, gửi yêu cầu kích hoạt bị từ chối; sau đó đã ngưng nhà cung cấp thử. Việc người tạo có quyền kích hoạt vẫn không tự kích hoạt được nhà cung cấp của mình: có test tự động, chưa thử thật.</p></li>
<li><p>Chủ doanh nghiệp được tự duyệt một số việc của chính mình: kích hoạt nhà cung cấp, công bố hợp đồng, duyệt phiên bản giá, mùa và ngày lễ, thông tin chuyển khoản trên hoá đơn đại lý, hoá đơn nhà cung cấp và chi trả. Mỗi lần tự duyệt đều được đánh dấu và liệt kê ở tab "Business-owner self-approvals" trong Audit log. Trang chủ có thêm các ô "Business-owner self-approvals", "Suppliers to activate" và "Billing changes to approve". Hai công tắc cho phép tự duyệt nằm ở mục "Staff sign-in" của trang Pricing policy, đang bật (đã kiểm qua hệ thống, chưa mở trên màn hình).</p></li>
<li><p>Đã mở thử 23/11: tab tự duyệt và các ô trên trang chủ hiện đúng, chưa có dòng nào. Việc chủ doanh nghiệp tự duyệt đã có trong hệ thống, chưa thử thật vì Dev chưa có tài khoản chủ doanh nghiệp.</p></li>
<li><p>Đã có trong hệ thống, có test tự động, chưa thử thật trên màn hình vì cần tài khoản người duyệt và chủ doanh nghiệp làm trên dữ liệu giả lập: em (tech lead) không tự duyệt được nhà cung cấp, hợp đồng hay hoá đơn của chính mình; người duyệt hoá đơn không tự ghi chi trả (trừ chủ doanh nghiệp, có đánh dấu); đổi thông tin chuyển khoản trên hoá đơn đại lý phải chờ duyệt, trong lúc chờ hoá đơn vẫn in thông tin cũ (nút "Change payment details" đã có ở tab Settings của Agency billing); tour chưa có giá đã duyệt thì không mở bán được.</p></li>
<li><p>Chưa có trong đợt này: tài khoản ngân hàng nhà cung cấp có thời gian chờ trước khi chi sau một lần đổi; chủ doanh nghiệp tự duyệt mức giảm theo hạng đại lý, thẻ giá và miễn phí huỷ (các việc này vẫn cần người thứ hai).</p></li>
</ul></li>
<li><p><strong>Tour đã bán tách thành từng booking nhà cung cấp, và kiểm tra "vận hành được":</strong></p>
<ul>
<li><p>Tab Suppliers của hồ sơ chuyến có thẻ "Tour components". Khi tour bán cho đại lý đã xác nhận, bấm Generate thì mỗi đêm khách sạn, mỗi chặng xe và hướng dẫn viên thành một booking nhà cung cấp riêng, lấy theo tour tại lúc bán; sửa tour sau đó không làm đổi các booking đã tạo. Đã có trong hệ thống, chưa thử thật vì từ lúc lên Dev chưa có tour nào được bán. 3 hồ sơ bán trước 23/11 hiện dòng "Sold before tours were split: add by hand" (đã thấy trên Dev).</p></li>
<li><p>Trang Price readiness có cột "Can operate" và bộ lọc theo Ready, Warnings, Blocked, Exception. Thiếu khách sạn một đêm thì tour bị chặn bán cho đại lý; thiếu xe giữa hai nơi chỉ cảnh báo. Đã thấy 23/11: một tour bị chặn với lý do "night 2 has no hotel". Hôm nay cả 892 tour trên Dev đều ở Blocked: 890 tour chưa có thành phần, 2 tour đã có giá còn thiếu đêm khách sạn. Đây là đúng với dữ liệu Dev, chưa có nguồn cung thật. Chưa thử: báo giá đại lý bị từ chối cho tour bị chặn, và trường hợp chỉ cảnh báo (Dev chưa có tour nào thiếu xe giữa hai nơi).</p></li>
<li><p>Quản trị viên mở bán ngoại lệ bằng nút "Allow sale…": chọn quy tắc, ghi lý do ít nhất 20 ký tự, thời hạn mặc định 14 ngày, tối đa 30 ngày (hai mức này chỉnh được trong chính sách giá); chuyến bán theo ngoại lệ được gắn việc kiểm tra chuyến. Đã mở thử khung này 23/11, không bấm lưu; mở khoá bán thật chưa thử vì Dev chưa có tour giả lập để thử (2 tour đã có giá là tour thật của catalogue nên không dùng để thử).</p></li>
</ul></li>
<li><p><strong>Bậc số khách cho giá tour</strong> nay chỉnh được ở trang Pricing policy, mục "Group size bands"; đang dùng từ 23/11: 1, 2, 3, 4, 5–7, 8–10, 11+. Đổi bậc cần người thứ hai duyệt (kể cả chủ doanh nghiệp). Đã mở thử 23/11 (chỉ xem, không sửa): trang hiện đúng các bậc đang dùng, phiên bản v2 từ 23/11 và lịch sử phiên bản. Chi tiết và đối chiếu với ví dụ giá ở PR-31.</p></li>
</ol>
<p>Ảnh theo thứ tự: (1) danh sách nhà cung cấp lọc "Pending approval", (2) nhà cung cấp chờ duyệt nhìn từ người tạo, (3) trang chủ Booking với các ô duyệt mới, (4) trang Price readiness lọc "Can operate = Blocked", (5) khung "Allow sale…", (6) mục "Group size bands" trên trang Pricing policy.</p>
```

### Images (in order)

1. `live/aa-1158/suppliers-pending-1440-light.png`
2. `live/aa-1158/supplier-detail-pending-creator-1440-light.png`
3. `live/aa-1158/home-my-work-1440-light.png`
4. `live/aa-1149/aa1149-readiness-blocked__1440__light.png`
5. `live/aa-1149/aa1149-sell-exception-drawer__1440__light.png`

(Paths relative to `docs/audits/2026-11-23-S288-session/`. The AA-1158 shots mask e-mail addresses and the account
chip per its evidence file; images 1 and 2 still show the synthetic supplier name with an internal ID: blur it first
("Before posting" 4).)

### Claim → evidence

| Claim | Evidence | Live? |
|---|---|---|
| Every new supplier starts "Pending approval", with the banner | `live/aa-1158/evidence.md` Done-when 2a (custom maker POST → 201 `pending`; UI banner text; shots `suppliers-pending-*`, `supplier-detail-pending-*`); hand step H1 (owner's new supplier also starts "Pending approval") | Yes, UI + API, 23/11 ~13:30 |
| Test role sees no Activate button; its activate request is refused | Shot `supplier-detail-pending-creator-1440-light` (only "Edit profile"); same file 2b + `results.json` `custom_activate_own`: API `POST /suppliers/{id}/activate` → 403 `forbidden` (role holds no `supplier.activate`; nothing was clicked) | Yes (API refusal via a role without the right) |
| A creator who holds the activate right still cannot activate its own supplier | Same file 2b: `maker_checker` branch, CI only (`test_aa1158_approval_rules_api.py`) | Stated as not tried (CI) |
| Synthetic supplier deactivated afterwards | Same file, "Writes made" (3 synthetic suppliers withdrawn, `inactive`) | Yes |
| Business-owner self-approval list of actions | Artifact section 5 table; Linear AA-1158 scope note (part 1 tables); runbook C0 | Code/scope, not live |
| Self-approvals tab + My work tiles show, 0 rows | `live/aa-1158/evidence.md` Done-when 9; shots `audit-log-self-approvals-*`, `home-my-work-*` | Yes |
| Two switches in the "Staff sign-in" section of Pricing policy, on | Same file "Other checks": `GET /pricing/policy` both `true`, version 1; section name from runbook (`.vi.md` "Pricing policy › Staff sign-in") | Yes (API); page not opened |
| Self-approval not tried (no owner account) | Same file 2c, 3, H1 | Stated as not tried |
| Tech lead own approval refused; payout rule; payment-details pending; sellable needs approved price | Same file 4, 5, 6, 7: NOT CHECKED live, CI tests named; read side of 6 PASS (`agency-billing-settings-*`) | Stated as not tried (CI) |
| Part 2 items not in this round | Linear AA-1158 comment 23/11 03:06 (part 2 S289 list); artifact section 8 | Scope |
| "Tour components" card, Generate per component; edits do not change sold bookings | `live/aa-1149/evidence.md` 1a/1b not checked; Linear AA-1149 comment | Stated as not tried |
| 3 cases sold before 23/11 show "Sold before tours were split: add by hand" | `live/aa-1149/evidence.md` 1a read-only evidence; shot `aa1149-case-sold-before-split__*` | Yes |
| "Can operate" column + filter on Price readiness; one tour blocked "night 2 has no hotel" | Same file 2a ("Price readiness shows the 'Can operate' column"); shots `aa1149-readiness*` | Yes |
| 892 blocked: 890 no components, 2 priced missing nights | Same file "Price readiness, can-operate" | Yes (API, 23/11 ~14:30) |
| Quote refusal and warning-only case not tried | Same file 2a (quote refusal not checked), 2c | Stated |
| "Allow sale…" drawer: reason ≥ 20, 14/30 days from policy, trip check note; not submitted | Same file 2b; shot `aa1149-sell-exception-drawer__*` | Yes (opened, not submitted) |
| Bands editable on Pricing policy ("Group size bands"), value 1, 2, 3, 4, 5–7, 8–10, 11+ from 23/11, second-person approval incl. business owner | Linear AA-1175 comment 23/11 10:50 ("never business-owner self-approval"); Booking #306/#307 merged; label `label_price_pax_bands: "Group size bands"` in Booking `frontend/app/(staff)/pricing/policy/_parts/messages.ts` (origin/main); `/booking/health/ready` = bk-066, `git_sha` 79a8b389 = #307 merge | Deploy yes; **UI not opened** (see "Before posting" 2) |

---

## 2. PR-27 — Nền tảng

- **Issue:** PR-27 "Nền tảng — Đăng nhập, bảo mật, hạ tầng (dùng chung các app)" (epic, In Progress).
- **Why:** both features are admin pages the business owner will see; they continue the 21/11 comment 10686 (roles,
  Compliance readiness). PR-20 kỳ 6 listed "xem trang với quyền thấp hơn" as next for CIS. No infrastructure or tooling
  decision is reported (memory `jira-no-tech-decisions`).
- **Where:** new comment on PR-27, `contentFormat: html`.

### Text (HTML, ready to post)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật nền tảng ngày 23/11 (Dev):</p>
<ol>
<li><p><strong>Xem hệ thống với quyền của một vai trò thấp hơn (CIS và Booking):</strong></p>
<ul>
<li><p>Chủ nền tảng chọn một vai trò (ví dụ "Content" ở CIS, "Product, ops &amp; accounting" ở Booking) để thấy đúng các trang và menu của vai trò đó. Trong lúc xem chỉ được đọc, mọi thay đổi bị từ chối; đầu trang có dải báo đang xem với vai trò nào, số phút còn lại và nút Back. Nhật ký ghi lúc bắt đầu, lúc kết thúc và danh sách quyền của vai trò được xem. Chỉ chủ nền tảng mới bắt đầu được, và không xem được vai trò có quyền đọc rộng hơn mình.</p></li>
<li><p>Chỗ dùng: CIS › Platform › Roles &amp; permissions (nút "View as" trên từng vai trò) và Booking › Roles (khung "View as a role").</p></li>
<li><p>Đã thử thật 23/11 bằng tài khoản chủ nền tảng thử (chỉ có trên Dev). Booking, xem với vai trò "Product, ops &amp; accounting": dải báo hiện đúng, một thao tác thay đổi bị từ chối, nút Back đưa về quyền của mình. CIS, xem với vai trò "Content": phía hệ thống chạy đúng (thay đổi bị từ chối, các trang quản trị bị chặn), nhưng dải báo và menu theo vai trò chưa hiện. Lỗi này đã sửa trong ngày; kiểm lại 23/11 lúc 22:37: dải báo hiện vai trò đang xem, chế độ chỉ đọc, số phút còn lại và nút Back, menu chỉ còn các mục của vai trò Content, bấm Back trả lại đầy đủ quyền. Tài khoản quản trị chỉ đọc không thấy nút "View as" ở cả hai app.</p></li>
</ul></li>
<li><p><strong>Compliance readiness có thêm tab Obligations (nghĩa vụ theo luật):</strong></p>
<ul>
<li><p>Bảng "Applicability by market": luật nào áp dụng ở thị trường nào, 29 ô (23 áp dụng, 4 chưa tới ngưỡng, 2 không áp dụng). Mỗi ô có link nguồn chính thức (Công báo Chính phủ, EUR-Lex, văn bản luật của Anh, Úc, Mỹ), ngày đánh giá 23/11 và dấu "cần luật sư xác nhận".</p></li>
<li><p>Danh sách việc cho từng luật áp dụng: Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 cùng Nghị định 356/2025/NĐ-CP (hiệu lực 01/01/2026, 15 mục), GDPR (15), UK GDPR (9), Đạo luật AI của EU (7), CAN-SPAM (5), ePrivacy của EU (3), PECR của Anh (3), Spam Act của Úc (3). Tổng 60 mục, mỗi mục có trạng thái và bằng chứng; 53 mục có link văn bản gốc và tài liệu tương ứng của AA.</p></li>
<li><p>Trang ghi rõ "Readiness, not legal advice": đây là mức sẵn sàng, không phải tư vấn pháp lý; mục có dấu luật sư cần luật sư xác nhận.</p></li>
<li><p>Số đo 23/11 lúc 14:30: 0 mục đạt, 31 chưa đạt (6 trong đó đạt một phần), 29 chưa kiểm. Các mục dựa vào tài liệu pháp lý (sổ hoạt động xử lý dữ liệu, thoả thuận xử lý dữ liệu, danh sách bên xử lý phụ, hồ sơ chuyển dữ liệu ra nước ngoài, quy trình trả lời yêu cầu của chủ thể dữ liệu, ghi nhận sự đồng ý) đang ở "chưa đạt" vì các trang đó vẫn là bản nháp; trang được thông qua thì mục tương ứng tự cập nhật ở lần thu bằng chứng sau. Lần diễn tập xoá dữ liệu gần nhất (31/10) đã được tính là bằng chứng còn hạn.</p></li>
<li><p>Số biện pháp kiểm soát của AA tăng từ 48 lên 61 (thêm nhóm quyền riêng tư), gắn với 306 yêu cầu.</p></li>
<li><p>Nút "Refresh evidence" nay báo kết quả ngay trên trang. Đã làm mới thành công 23/11 lúc 22:01: đọc 17 kết quả, cả nguồn dữ liệu CIS và CRM đều có lần kiểm mới. Với tài khoản chỉ đọc, hệ thống từ chối và báo lỗi ngay trên trang.</p></li>
<li><p>Đã kiểm 23/11 trên máy tính: cả ba tab Overview, Controls, Obligations hiện đủ, không lỗi (nền sáng; tab Obligations cả nền tối).</p></li>
</ul></li>
</ol>
<p>Ảnh: (1) tab Obligations với bảng áp dụng theo thị trường, (2) Booking đang xem với vai trò "Product, ops &amp; accounting" (dải báo ở đầu trang), (3) CIS đang xem với vai trò Content sau khi sửa (dải báo và menu theo vai trò).</p>
```

### Images (in order)

1. `live/aa-1174/r2-compliance-obligations-desktop-light.png` (468 KB)

Dropped: `live/aa-1174/r2-compliance-refresh-refused-desktop-light.png` shows the internal code `e2e_read_only` twice
and the chip "E2E CIS admin"; it only proves the error path, which the text already states.

No phone shot: the round-2 phone shots were taken before CIS #1647 (matrix scrolled the whole page sideways) and the
fix was not re-checked live, so the draft makes no phone claim.

### Claim → evidence

| Claim | Evidence | Live? |
|---|---|---|
| View-as feature description (read only, banner, minutes, Back, audit start/end with capability list, owner only, no wider role) | Linear AA-1157 comment; `live/aa-1157/evidence.md` sections 2–3 (CI tests named for owner rule, write refusal, wider target) | Description; not live for the owner path |
| Where: CIS Roles & permissions "View as", Booking Roles "View as a role" | `live/aa-1157/evidence.md` H1, H3 (UI labels from code) | Not opened as owner |
| Non-owner read-only test admin: no View as control in both apps | Same file checks c2, d3 (0 controls, shots), c, d2 (`can_view_as: false`) | Yes, 23/11 06:20–06:30 UTC |
| Owner-only start, no wider role, writes refused during view-as: CI only | Same file "What these checks do and do not prove": the live 403s (b, d) are the generic `e2e_read_only` refusal before the owner check, so they prove nothing about the owner rule; CI tests `test_aa1157_staff_view_as.py`, `test_aa1157_view_as.py` | Stated as not tried (CI) |
| Owner path not tried | Same file Done-when table, hand steps H0–H6 | Stated |
| Matrix 29 rows (23/4/2), official source each, assessed 23/11, counsel flag | `live/aa-1174/evidence.md` round 2, Done-when 1 | Yes (API + page), 23/11 07:24–07:32 UTC |
| 8 law checklists with item counts; VN Law 91/2025/QH15 + Decree 356/2025/ND-CP in force 01/01/2026 | Same, Done-when 2 | Yes |
| 60 items, 53 with official source + document link | Same, Done-when 2 | Yes |
| "Readiness, not legal advice" text | Same, Done-when 5 | Yes |
| 0 met / 31 not met (6 partly) / 29 not checked at ~14:30 | Same, Done-when 3 | Yes, **re-read before posting** (cis_db collected after) |
| Legal pages are drafts → those items not met; adopting a page updates on the next collection | Same, D1; Linear AA-1174 comment 09:05 (tech lead decision D1: keep draft) | Yes (collector run 45130504907) |
| Erasure drill 31/10 counted | Round 1 F4 + round 2 Done-when 3 (`last_erasure_drill` pass, 23 days, limit 180) | Yes |
| Controls 48 → 61, 306 requirements | Round 2 "Register v2 loaded" (306 / 61 / 465 / 14 / 60); 48 from PR-27 comment 10686 (21/11) | Yes |
| Refresh shows result; read-only gets error toast, no crash; success not tried | Round 2 "Refresh feedback" (403 `e2e_read_only`, toast, shot kept locally, not attached) | Yes (refused path only) |
| Three tabs render on desktop, no errors: all three in light, Obligations also in dark | Round 2 Done-when (shots `r2-compliance-overview-desktop-light`, `r2-compliance-controls-desktop-light`, `r2-compliance-obligations-desktop-{light,dark}`; console only the expected 403) | Yes |

---

## 3. PR-31 — Price system (reply on the business owner's task)

- **Issue:** PR-31 "Price system" (Task, Backlog, created 23/11 12:46 by the business owner, assigned to the tech
  lead; description empty in Jira, 0 comments). Her example was read from the image she shared (recorded in Linear
  AA-1175 "Problem").
- **Why:** her own request from today. The reply says what the system already does for her example, what changed
  today (the bands), and gives the short guide page. No question to her; no status change (skill rule 2).
- **Where:** new comment on PR-31, `contentFormat: html`. Do not change the status.
- **Link:** the artifact is the tech lead's page, version 2 (bands shipped), shared with the whole organization
  ("Before posting" 1).

### Text (HTML, ready to post)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Về giá trip theo số khách (Dev, 23/11):</p>
<p>Đối chiếu với ví dụ giá của chị (giá mỗi khách ở phòng đôi, hiệu lực 20/01–31/03/2027: 2 khách 2.190 USD, 4 khách 1.770 USD, 5–7 khách 1.745 USD, 8 khách 1.550 USD):</p>
<table>
<thead><tr><th><p>Yêu cầu</p></th><th><p>Hệ thống</p></th></tr></thead>
<tbody>
<tr><td><p>Giá mỗi khách theo phòng đôi</p></td><td><p>Đã có, kèm phụ thu phòng đơn, giá trẻ em và em bé</p></td></tr>
<tr><td><p>Thời hạn giá 20/01–31/03/2027</p></td><td><p>Đã có: mỗi phiên bản giá có ngày bắt đầu và kết thúc</p></td></tr>
<tr><td><p>Mùa cao điểm, thấp điểm, ngày lễ</p></td><td><p>Đã có: lịch mùa và ngày lễ trong Booking</p></td></tr>
<tr><td><p>Một trip lấy giá từ nhiều nhà cung cấp</p></td><td><p>Đã có: giá tour cộng từ khách sạn, xe, hướng dẫn viên của nhiều nhà cung cấp; khi bán, mỗi thành phần thành một booking nhà cung cấp riêng (mới 23/11, chi tiết ở PR-25)</p></td></tr>
<tr><td><p>Bậc số khách</p></td><td><p>Mới 23/11: chỉnh được ở Booking › Pricing policy, mục "Group size bands"</p></td></tr>
</tbody>
</table>
<p>Các mục "Đã có" là tính năng đã làm trước; giá trẻ em đã thử 20/11, các mục khác chưa thử lại hôm nay.</p>
<ul>
<li><p><strong>Nhập bảng giá như ví dụ:</strong> trong Booking, tạo phiên bản giá (giá nhập tay) cho tour, mỗi dòng một bậc số khách (Pax min – Pax max, ví dụ 5–7), có ngày hiệu lực. Giá nhập tay đặt được bậc tuỳ ý. Sau khi duyệt, giá nhập tay được ưu tiên hơn giá tính tự động trong bảng giá; báo giá tức thì cho đại lý vẫn tính từ các thành phần tour. Theo quy tắc duyệt mới, chủ doanh nghiệp tự duyệt được phiên bản giá, có đánh dấu trong nhật ký (đã có trong hệ thống, chưa thử thật vì Dev chưa có tài khoản chủ doanh nghiệp). Chưa nhập thử đúng bảng giá này trên Dev.</p></li>
<li><p><strong>Bậc số khách cho giá tính tự động:</strong> trước đây cố định trong hệ thống (1, 2, 3–4, 5–6, 7–10, 11+); nay là một tham số ở trang Pricing policy, mục "Group size bands", đang dùng từ 23/11: <strong>1, 2, 3, 4, 5–7, 8–10, 11+</strong>. Có bậc 3 riêng vì các bậc phải liền nhau từ 1 khách: nếu gộp 3–4 thì nhóm 4 người sẽ phải trả theo giá của nhóm 3 người, cao hơn. Bậc 11+ tính theo giá của 11 khách (số khách nhỏ nhất của bậc), giống mọi bậc khác, để không đoàn nào bị tính thấp hơn chi phí thật. Đổi bậc cần người thứ hai duyệt (kể cả chủ doanh nghiệp), có lịch sử thay đổi và hướng dẫn tiếng Anh, tiếng Việt ngay trên trang.</p></li>
<li><p><strong>Bảng giá cho đại lý</strong> ghi một giá cho mỗi bậc, tính theo số khách nhỏ nhất của bậc đó. Báo giá tức thì cho đại lý tính theo đúng số khách thật từ các thành phần tour, nên có thể thấp hơn giá của bậc; nhóm từ 9 khách trở lên báo giá theo yêu cầu (mức 9 chỉnh được). Dòng 8–10 và 11+ vẫn có trong bảng giá để tham khảo; đoàn từ 9 khách nhân viên báo giá theo yêu cầu.</p></li>
<li><p><strong>Ở lần tính giá lại đầu tiên:</strong> nhóm 1, 2, 3, 5, 6 và 11+ không đổi; nhóm 4 có dòng giá riêng, rẻ hơn trước; nhóm 7 nay theo giá của 5 khách (tăng); nhóm 8–10 theo giá của 8 khách (giảm).</p></li>
<li><p>Đã lên Dev 23/11, có test tự động; đã mở thử trang Pricing policy 23/11 (chỉ xem, không sửa): mục "Group size bands" hiện đúng các bậc trên, phiên bản v2 từ 23/11, có lịch sử phiên bản (ảnh kèm).</p></li>
</ul>
<p>Trang tóm tắt "Bắt đầu với hệ thống giá" (chuẩn bị cho buổi đầu, đăng nhập, giá chảy thế nào, ai duyệt, nên thử gì): <a href="https://claude.ai/artifact/DaUxxoojMm4RzpswhdQB2J">https://claude.ai/artifact/DaUxxoojMm4RzpswhdQB2J</a></p>
<p>Hướng dẫn chi tiết (bản nháp, sẽ dùng trong buổi đầu cùng em) nằm trong CIS admin › Docs, trang "Business owner onboarding and the price system", có bản tiếng Việt; chị mở được sau khi có tài khoản.</p>
<p>Ảnh: mục "Group size bands" trên trang Pricing policy của Booking.</p>
```

No images (optional: the Pricing policy screenshot from "Before posting" 2, then drop the "chưa mở thử" line).

### Claim → evidence

| Claim | Evidence | Live? |
|---|---|---|
| Her example numbers and validity | Linear AA-1175 "Problem" (read from her image); artifact section 4 | Source |
| Per person twin share, single supplement, child/infant prices | Artifact section 4; runbook GUIDE-12-owner-pricing part C; PR-25 comment 10682 (child price 50 % tried 20/11) | Code + earlier live (child price) |
| Price versions have validity dates; seasons/holidays calendar | Artifact section 4; runbook part C | Code/runbook, not re-tried today |
| Note under the table: "Đã có" = existing features; child price tried 20/11, others not re-tried today | PR-25 comment 10682 (20/11) | Stated |
| Multi-supplier tour price; one supplier booking per component on sale | Artifact section 4; `live/aa-1149/evidence.md` (shipped, Generate not tried live) | Partly (see PR-25) |
| Hand price versions accept any Pax min / Pax max and win over computed rows in the price list | Linear AA-1175 "Problem"; Booking #307 PR body ("Hand prices keep any Pax min / Pax max and still win over the computed rows they cover") | Code; **"chưa nhập thử" stated** |
| Agency instant quote is still priced from tour components (not from hand price versions) | Booking #307 body ("The B2B quote … prices the real party from the plan's components and never reads the bands"); module docstring `backend/app/b2b/quotes.py` (every line through the pricing rule; no hand price versions) | Code |
| Business owner may self-approve price versions (flagged); not tried | Linear AA-1158 part 1 scope (price list versions); artifact section 5; `live/aa-1158/evidence.md` 2c, 3, H1 (no owner account on Dev) | Code; stated as not tried |
| Old bands 1, 2, 3–4, 5–6, 7–10, 11+; new 1, 2, 3, 4, 5–7, 8–10, 11+ from 23/11; setting "Group size bands" on Pricing policy | Linear AA-1175 description + comment; Booking #306 body (v1 / v2); label in Booking `pricing/policy/_parts/messages.ts` (EN "Group size bands", VI "Bậc cỡ đoàn") | Deploy yes (bk-066 live) |
| Why band 3; 11+ priced for 11 (smallest count of the band, like every band, so no party is underpriced) | Linear AA-1175 comment ("Band choice": "priced for 11 so it never undercuts 8–10") | Design note |
| Second-person approval incl. business owner, history, EN/VI guide | Linear AA-1175 comment ("never business-owner self-approval"); Booking #307 body; integration test "maker cannot self-approve, audit rows" | CI; UI not opened |
| Agency tariff one price per band (smallest group); instant quote from components, can be lower; ≥ 9 on request; 8–10 and 11+ rows kept for reference | Booking #307 body "Agency tariff vs agency quote"; integration test (4 → 120, 6 → 180 below 5–7 row, 9 → on_request) | CI (real POST in integration test) |
| First recompute effect (4 cheaper own row, 7 up, 8–10 down; others unchanged) | Booking #307 body "Price effect at the first recompute after deploy" | Design/CI |
| Deployed 23/11, not opened on screen | `/booking/health` `git_sha` 79a8b389 = #307 merge; Deploy Dev + Deploy Admin Dev green; no live UI evidence file | Yes (deploy) |
| Artifact link | Artifact version 2 (bands shipped), owned by the tech lead, shared with the whole organization | — |
| Detailed guide in CIS admin › Docs, draft, VI version, opens once she has an account | root #953 merged (`docs/guides/business-owner-onboarding-and-pricing.md`, id GUIDE-12-owner-pricing, EN title "Business owner onboarding and the price system", + `.vi.md`); page status `draft`, banner "CHƯA CHẠY THỬ"; Part A: the tech lead creates her CIS and Booking accounts | Docs |

---

## Not drafted, with reason

- **PR-22 CIS:** the fact guard for AI writers ships off (switch on = tech lead decision, technical); Settings
  "SCHEDULED" label fix is minor. Nothing user-visible for the business owner.
- **PR-23 Content studio:** the blog-writer guard against planted instructions exists but is off; post on PR-23 when it
  is switched on (it was listed as "next" in PR-20 kỳ 6).
- **E2E owner admin (AA-1176):** technical test identity; Jira gets nothing (memory `jira-no-tech-decisions`).
- **Release-please / dependabot merges, repo GC:** technical, already in PR-20 kỳ 6 where relevant.

## Posting log

| Issue | Comment | Images | Posted |
|---|---|---|---|
| PR-25 | [10688](https://adventure-asia.atlassian.net/browse/PR-25?focusedCommentId=10688) | 6 (images 1–2 with the synthetic supplier code masked; 6 = Group size bands, final run) | 23/11 ~22:52 +07 |
| PR-27 | [10689](https://adventure-asia.atlassian.net/browse/PR-27?focusedCommentId=10689) | 3 (3 = CIS view-as banner after CIS #1651) | 23/11 ~22:54 +07 (first try hit a connector error; checked, not posted, retried once) |
| PR-31 | [10690](https://adventure-asia.atlassian.net/browse/PR-31?focusedCommentId=10690) | 1 (Group size bands) | 23/11 ~22:55 +07 |

Changes from the drafts above after the final run: PR-27 CIS banner sentence (fixed and re-checked 22:37); PR-25 item 3 and PR-31 last bullet "đã mở thử trang Pricing policy (chỉ xem)"; PR-25 sale exception reason "Dev chưa có tour giả lập"; extra images.
